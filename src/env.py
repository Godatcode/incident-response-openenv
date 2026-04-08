"""Main IncidentResponseEnv — OpenEnv interface."""

from __future__ import annotations

from src.models import Action, Observation, Reward, State
from src.tasks.base import BaseTask
from src.tasks.easy_oom_outage import EasyOomOutageTask
from src.tasks.hard_phantom import HardPhantomTask
from src.tasks.medium_bad_deploy import MediumBadDeployTask

_TASK_REGISTRY: dict[str, type[BaseTask]] = {
    "easy_oom_outage": EasyOomOutageTask,
    "medium_bad_deploy": MediumBadDeployTask,
    "hard_phantom": HardPhantomTask,
}


class IncidentResponseEnv:
    """
    OpenEnv-compatible environment for production incident response simulation.

    Three tasks of increasing difficulty:
      - easy_oom_outage   : Single-service OOM kill. Diagnose and restart.
      - medium_bad_deploy : Bad deployment with cascading failures and a red herring.
      - hard_phantom      : Intermittent latency from memory leak with multiple red herrings.
    """

    def __init__(self) -> None:
        self._task: BaseTask | None = None
        self._current_task_name: str | None = None

    # ------------------------------------------------------------------
    # OpenEnv required interface
    # ------------------------------------------------------------------

    def reset(self, task_name: str | None = None) -> Observation:
        """
        Reset environment to initial state for given task.
        Returns initial observation.
        """
        name = task_name or "easy_oom_outage"
        if name not in _TASK_REGISTRY:
            available = list(_TASK_REGISTRY.keys())
            raise ValueError(
                f"Unknown task '{name}'. Available tasks: {available}"
            )
        self._current_task_name = name
        self._task = _TASK_REGISTRY[name]()
        return self._task.reset()

    def step(self, action: Action | dict) -> tuple[Observation, Reward, bool, dict]:
        """
        Execute action. Returns (observation, reward, done, info).
        Action can be a Pydantic Action model or a raw dict.
        """
        if self._task is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        if isinstance(action, dict):
            action = Action(**action)
        return self._task.step(action)

    def state(self) -> State:
        """Returns current full state of the environment."""
        if self._task is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return self._task.get_state()

    def close(self) -> None:
        """Cleanup."""
        self._task = None
        self._current_task_name = None

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @staticmethod
    def list_tasks() -> list[str]:
        return list(_TASK_REGISTRY.keys())
