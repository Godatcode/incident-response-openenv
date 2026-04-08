"""Tests for the main IncidentResponseEnv interface."""

import pytest

from src.env import IncidentResponseEnv
from src.models import Action, ActionType, Observation, Reward, State


@pytest.fixture
def env():
    return IncidentResponseEnv()


def test_list_tasks():
    tasks = IncidentResponseEnv.list_tasks()
    assert "easy_oom_outage" in tasks
    assert "medium_bad_deploy" in tasks
    assert "hard_phantom" in tasks


def test_reset_returns_observation(env):
    obs = env.reset("easy_oom_outage")
    assert isinstance(obs, Observation)
    assert obs.step_number == 0
    assert len(obs.active_alerts) > 0
    assert len(obs.service_statuses) > 0
    assert len(obs.dependency_graph) > 0


def test_reset_unknown_task_raises(env):
    with pytest.raises(ValueError, match="Unknown task"):
        env.reset("nonexistent_task")


def test_step_before_reset_raises(env):
    with pytest.raises(RuntimeError, match="not initialized"):
        env.step(Action(action_type=ActionType.CHECK_LOGS, target_service="api-gateway"))


def test_step_returns_correct_types(env):
    env.reset("easy_oom_outage")
    obs, reward, done, info = env.step(
        Action(action_type=ActionType.CHECK_LOGS, target_service="user-service")
    )
    assert isinstance(obs, Observation)
    assert isinstance(reward, Reward)
    assert isinstance(done, bool)
    assert isinstance(info, dict)


def test_step_with_dict_action(env):
    """Action can be passed as a raw dict (for API compatibility)."""
    env.reset("easy_oom_outage")
    obs, reward, done, info = env.step(
        {"action_type": "check_logs", "target_service": "user-service"}
    )
    assert isinstance(obs, Observation)


def test_step_increments_step_number(env):
    env.reset("easy_oom_outage")
    obs, _, _, _ = env.step(
        Action(action_type=ActionType.CHECK_LOGS, target_service="user-service")
    )
    assert obs.step_number == 1


def test_state_returns_state_model(env):
    env.reset("easy_oom_outage")
    state = env.state()
    assert isinstance(state, State)
    assert state.task_name == "easy_oom_outage"
    assert state.ground_truth_root_cause != ""
    assert len(state.ground_truth_affected_services) > 0


def test_state_before_reset_raises(env):
    with pytest.raises(RuntimeError):
        env.state()


def test_invalid_service_returns_penalty(env):
    env.reset("easy_oom_outage")
    obs, reward, done, info = env.step(
        Action(action_type=ActionType.CHECK_LOGS, target_service="nonexistent-svc")
    )
    assert reward.value < 0
    assert "last_action_error" in info
    assert done is False


def test_reward_value_in_range(env):
    env.reset("easy_oom_outage")
    for _ in range(5):
        _, reward, _, _ = env.step(
            Action(action_type=ActionType.CHECK_LOGS, target_service="user-service")
        )
        assert -1.0 <= reward.value <= 1.0


def test_done_on_mark_resolved(env):
    env.reset("easy_oom_outage")
    _, _, done, _ = env.step(
        Action(
            action_type=ActionType.MARK_RESOLVED,
            parameters={"root_cause_summary": "test"},
        )
    )
    assert done is True


def test_close(env):
    env.reset("easy_oom_outage")
    env.close()
    with pytest.raises(RuntimeError):
        env.state()


def test_reset_all_tasks(env):
    for task in IncidentResponseEnv.list_tasks():
        obs = env.reset(task)
        assert isinstance(obs, Observation)
        assert obs.step_number == 0
