from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import Action, Observation, Reward, State


class BaseTask(ABC):
    """Abstract base class for all incident response tasks."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Task identifier."""
        ...

    @property
    @abstractmethod
    def max_steps(self) -> int:
        ...

    @property
    @abstractmethod
    def dependency_graph(self) -> dict[str, list[str]]:
        """service -> list of services it depends on."""
        ...

    @property
    @abstractmethod
    def ground_truth_root_cause(self) -> str:
        ...

    @property
    @abstractmethod
    def ground_truth_affected_services(self) -> list[str]:
        ...

    @property
    @abstractmethod
    def ground_truth_optimal_actions(self) -> list[str]:
        ...

    @abstractmethod
    def reset(self) -> Observation:
        """Reset task to initial state and return initial observation."""
        ...

    @abstractmethod
    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict]:
        """
        Execute an action.
        Returns (observation, reward, done, info).
        """
        ...

    @abstractmethod
    def get_state(self) -> State:
        """Return the full internal state."""
        ...

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    AVAILABLE_ACTIONS = [
        'check_logs <service>          — Retrieve recent log lines for a service',
        'query_metrics <service> <metric_type: cpu|memory|latency|error_rate>',
        'restart_service <service>     — Restart a service',
        'rollback_deploy <service>     — Roll back to previous deployment',
        'scale_service <service> <replicas: int>',
        'run_healthcheck <service>     — Run a health check on a service',
        'mark_resolved <root_cause_summary>  — Close the incident',
    ]
