from __future__ import annotations

import pytest

from inference import (
    TASK_PLANS,
    choose_planned_action,
    parse_model_action,
    resolve_runtime_config,
    sanitize_log_field,
    select_action,
)
from src.env import IncidentResponseEnv


def test_resolve_runtime_config_prefers_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_BASE_URL", " https://proxy.example/v1 ")
    monkeypatch.setenv("MODEL_NAME", " meta-model ")
    monkeypatch.setenv("HF_TOKEN", " token ")

    config = resolve_runtime_config()

    assert config.api_base_url == "https://proxy.example/v1"
    assert config.model_name == "meta-model"
    assert config.hf_token == "token"
    assert config.task_name == "easy_oom_outage"
    assert config.benchmark_name == "incident_response"


def test_resolve_runtime_config_uses_defaults_without_api_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.setenv("HF_TOKEN", "token")

    config = resolve_runtime_config()

    assert config.api_base_url == "https://router.huggingface.co/v1"
    assert config.model_name == "Qwen/Qwen2.5-72B-Instruct"


def test_resolve_runtime_config_allows_missing_hf_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HF_TOKEN", raising=False)

    config = resolve_runtime_config()

    assert config.hf_token is None


def test_parse_model_action_strips_markdown_fences() -> None:
    payload = """```json
{"action_type":"check_logs","target_service":"user-service"}
```"""

    action = parse_model_action(payload)

    assert action == {
        "action_type": "check_logs",
        "target_service": "user-service",
        "parameters": {},
    }


def test_select_action_uses_safe_plan_when_model_drifts() -> None:
    action = select_action(
        "easy_oom_outage",
        action_history=[],
        model_action={
            "action_type": "restart_service",
            "target_service": "payment-service",
            "parameters": {},
        },
    )

    assert action == choose_planned_action("easy_oom_outage", [])


def test_sanitize_log_field_collapses_multiline_content() -> None:
    assert sanitize_log_field('{"a": 1,\n "b": 2}') == '{"a": 1, "b": 2}'


def test_task_plans_reach_full_reward() -> None:
    env = IncidentResponseEnv()

    try:
        for task_name, plan in TASK_PLANS.items():
            obs = env.reset(task_name)
            assert obs.step_number == 0

            total_reward = 0.0
            action_history: list[dict] = []
            done = False

            while not done:
                action = choose_planned_action(task_name, action_history)
                obs, reward, done, _ = env.step(action)
                total_reward += reward.value
                action_history.append(action)

            assert action_history == plan
            assert total_reward == pytest.approx(1.0)
    finally:
        env.close()
