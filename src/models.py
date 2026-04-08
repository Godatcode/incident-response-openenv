from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    CHECK_LOGS = "check_logs"
    QUERY_METRICS = "query_metrics"
    RESTART_SERVICE = "restart_service"
    ROLLBACK_DEPLOY = "rollback_deploy"
    SCALE_SERVICE = "scale_service"
    RUN_HEALTHCHECK = "run_healthcheck"
    MARK_RESOLVED = "mark_resolved"


class Action(BaseModel):
    """Agent's action in the environment."""

    action_type: ActionType
    target_service: str = ""
    parameters: dict = Field(default_factory=dict)
    # parameters examples:
    #   query_metrics: {"metric_type": "cpu|memory|latency|error_rate"}
    #   scale_service: {"replicas": 3}
    #   mark_resolved: {"root_cause_summary": "..."}


class Alert(BaseModel):
    """A production alert."""

    alert_id: str
    severity: Literal["critical", "warning", "info"]
    service: str
    message: str
    timestamp: str


class ServiceStatus(BaseModel):
    """Current status of a service."""

    name: str
    status: Literal["healthy", "degraded", "down", "unknown"]
    last_deploy_time: str | None = None
    replicas: int = 1


class Observation(BaseModel):
    """What the agent sees after each step."""

    active_alerts: list[Alert]
    service_statuses: list[ServiceStatus]
    dependency_graph: dict[str, list[str]]  # service -> [depends_on]
    incident_timeline: list[str]  # ordered list of events so far
    last_action_result: str  # text output of the agent's last action
    available_actions: list[str]  # human-readable list of valid actions
    step_number: int
    max_steps: int


class Reward(BaseModel):
    """Reward signal."""

    value: float = Field(ge=-1.0, le=1.0)
    reason: str  # human-readable explanation


class State(BaseModel):
    """Full internal state (superset of observation — includes hidden ground truth)."""

    task_name: str
    step_number: int
    max_steps: int
    observation: Observation
    ground_truth_root_cause: str
    ground_truth_affected_services: list[str]
    ground_truth_optimal_actions: list[str]
    checkpoints_hit: list[str]
    cumulative_reward: float
    done: bool
