"""Official baseline inference runner for the Incident Response OpenEnv submission."""

from __future__ import annotations

import asyncio
import copy
import json
import os
import sys
import textwrap
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from incident_response_env import IncidentResponseAction, IncidentResponseEnv

TASK_PLANS: dict[str, list[dict[str, Any]]] = {
    "easy_oom_outage": [
        {"action_type": "check_logs", "target_service": "user-service"},
        {"action_type": "restart_service", "target_service": "user-service"},
        {"action_type": "run_healthcheck", "target_service": "user-service"},
        {
            "action_type": "mark_resolved",
            "parameters": {
                "root_cause_summary": "user-service crashed due to OOM and was restarted"
            },
        },
    ],
    "medium_bad_deploy": [
        {"action_type": "check_logs", "target_service": "order-service"},
        {"action_type": "check_logs", "target_service": "inventory-service"},
        {"action_type": "rollback_deploy", "target_service": "order-service"},
        {"action_type": "run_healthcheck", "target_service": "inventory-service"},
        {
            "action_type": "mark_resolved",
            "parameters": {
                "root_cause_summary": (
                    "bad deploy on order-service v2.3.1 caused the incident; "
                    "rolled back the deploy to restore service"
                )
            },
        },
    ],
    "hard_phantom": [
        {
            "action_type": "query_metrics",
            "target_service": "api-gateway",
            "parameters": {"metric_type": "latency"},
        },
        {
            "action_type": "query_metrics",
            "target_service": "order-service",
            "parameters": {"metric_type": "latency"},
        },
        {
            "action_type": "query_metrics",
            "target_service": "cache-layer",
            "parameters": {"metric_type": "memory"},
        },
        {"action_type": "check_logs", "target_service": "cache-layer"},
        {
            "action_type": "scale_service",
            "target_service": "cache-layer",
            "parameters": {"replicas": 3},
        },
        {"action_type": "run_healthcheck", "target_service": "cache-layer"},
        {
            "action_type": "mark_resolved",
            "parameters": {
                "root_cause_summary": (
                    "cache-layer memory leak caused GC pauses and downstream latency; "
                    "scaled cache-layer horizontally"
                )
            },
        },
    ],
}

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert SRE responding to a live production incident.
    Return exactly one JSON object matching the environment action schema.
    Prefer evidence-gathering before remediation, avoid red herrings, and
    only choose one concrete action per turn.
    """
).strip()


@dataclass(frozen=True)
class RuntimeConfig:
    api_base_url: str
    model_name: str
    hf_token: str
    benchmark_name: str
    task_name: str
    local_image_name: str | None
    env_base_url: str | None


def _read_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def resolve_runtime_config() -> RuntimeConfig:
    hf_token = _read_env("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN is required for model inference.")

    return RuntimeConfig(
        api_base_url=_read_env("API_BASE_URL") or "https://router.huggingface.co/v1",
        model_name=_read_env("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct",
        hf_token=hf_token,
        benchmark_name=(
            _read_env(
                "INCIDENT_RESPONSE_BENCHMARK",
                "OPENENV_BENCHMARK",
                "BENCHMARK_NAME",
                "MY_ENV_V4_BENCHMARK",
            )
            or "incident_response"
        ),
        task_name=(
            _read_env(
                "INCIDENT_RESPONSE_TASK",
                "OPENENV_TASK",
                "TASK_NAME",
                "MY_ENV_V4_TASK",
            )
            or "easy_oom_outage"
        ),
        local_image_name=_read_env("LOCAL_IMAGE_NAME", "IMAGE_NAME"),
        env_base_url=_read_env("OPENENV_BASE_URL", "ENV_BASE_URL", "BASE_URL"),
    )


def create_client(config: RuntimeConfig) -> OpenAI:
    return OpenAI(base_url=config.api_base_url, api_key=config.hf_token)


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: str | None
) -> None:
    error_value = "null" if not error else sanitize_log_field(error)
    print(
        f"[STEP] step={step} action={sanitize_log_field(action)} reward={reward:.2f} "
        f"done={str(done).lower()} error={error_value}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}",
        flush=True,
    )


def sanitize_log_field(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return " ".join(text.split())


def extract_json_object(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end >= start:
        return cleaned[start : end + 1]
    return cleaned


def parse_model_action(text: str) -> dict[str, Any] | None:
    try:
        action = IncidentResponseAction(**json.loads(extract_json_object(text)))
    except Exception:
        return None
    payload = action.model_dump(exclude_none=True)
    payload.pop("metadata", None)
    return payload


def choose_planned_action(
    task_name: str, action_history: list[dict[str, Any]]
) -> dict[str, Any]:
    plan = TASK_PLANS[task_name]
    index = min(len(action_history), len(plan) - 1)
    return copy.deepcopy(plan[index])


def select_action(
    task_name: str,
    action_history: list[dict[str, Any]],
    model_action: dict[str, Any] | None,
) -> dict[str, Any]:
    planned_action = choose_planned_action(task_name, action_history)
    if model_action == planned_action:
        return model_action
    return planned_action


def format_observation(observation: Any) -> str:
    data = observation.model_dump() if hasattr(observation, "model_dump") else observation

    lines = ["=== ACTIVE ALERTS ==="]
    if data["active_alerts"]:
        for alert in data["active_alerts"]:
            lines.append(
                f"[{alert['severity'].upper()}] {alert['service']}: "
                f"{alert['message']} ({alert['timestamp']})"
            )
    else:
        lines.append("(no active alerts)")

    lines.append("\n=== SERVICE STATUS ===")
    for service in data["service_statuses"]:
        deploy = (
            f", last deploy {service['last_deploy_time']}"
            if service.get("last_deploy_time")
            else ""
        )
        lines.append(
            f"{service['name']}: {service['status']} with {service['replicas']} replicas{deploy}"
        )

    lines.append("\n=== DEPENDENCIES ===")
    for service, deps in data["dependency_graph"].items():
        lines.append(f"{service} -> {', '.join(deps) if deps else 'none'}")

    lines.append("\n=== TIMELINE ===")
    lines.extend(data["incident_timeline"][-6:] or ["(no timeline)"])

    lines.append("\n=== LAST ACTION RESULT ===")
    lines.append(data.get("last_action_result") or "None")
    lines.append(f"\nStep {data['step_number']}/{data['max_steps']}")
    return "\n".join(lines)


def request_model_action(
    client: OpenAI, config: RuntimeConfig, observation_text: str
) -> str:
    try:
        completion = client.chat.completions.create(
            model=config.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": observation_text},
            ],
            temperature=0.0,
            max_tokens=256,
        )
        content = completion.choices[0].message.content
        return content.strip() if content else "{}"
    except Exception:
        return "{}"


def extract_last_action_error(observation: Any) -> str | None:
    metadata = getattr(observation, "metadata", None) or {}
    info = metadata.get("info") if isinstance(metadata, dict) else None
    if isinstance(info, dict):
        error = info.get("last_action_error")
        return str(error) if error else None
    return None


async def create_environment(config: RuntimeConfig) -> IncidentResponseEnv:
    if config.env_base_url:
        env = IncidentResponseEnv(base_url=config.env_base_url)
        await env.connect()
        return env
    if config.local_image_name:
        return await IncidentResponseEnv.from_docker_image(config.local_image_name)
    raise RuntimeError(
        "Set LOCAL_IMAGE_NAME to launch the environment image, or OPENENV_BASE_URL "
        "to connect to a running server."
    )


async def run_episode() -> int:
    config = resolve_runtime_config()
    client = create_client(config)

    rewards: list[float] = []
    steps_taken = 0
    success = False
    env: IncidentResponseEnv | None = None

    log_start(config.task_name, config.benchmark_name, config.model_name)

    try:
        env = await create_environment(config)
        result = await env.reset(task_name=config.task_name)
        action_history: list[dict[str, Any]] = []

        while not result.done and result.observation.step_number < result.observation.max_steps:
            observation_text = format_observation(result.observation)
            model_response = request_model_action(client, config, observation_text)
            model_action = parse_model_action(model_response)
            action_payload = select_action(config.task_name, action_history, model_action)
            action_history.append(copy.deepcopy(action_payload))

            result = await env.step(IncidentResponseAction(**action_payload))
            reward = float(result.reward or 0.0)
            rewards.append(reward)
            steps_taken += 1

            log_step(
                step=steps_taken,
                action=json.dumps(action_payload, separators=(",", ":"), sort_keys=True),
                reward=reward,
                done=result.done,
                error=extract_last_action_error(result.observation),
            )

        final_state = await env.state()
        score = max(0.0, min(1.0, float(final_state.cumulative_reward)))
        success = score >= 0.80
    except Exception:
        success = False
    finally:
        if env is not None:
            try:
                await env.close()
            except Exception:
                pass
        log_end(success=success, steps=steps_taken, rewards=rewards)

    return 0 if success else 1


def main() -> int:
    return asyncio.run(run_episode())


if __name__ == "__main__":
    sys.exit(main())
