"""OpenEnv client for the Incident Response environment."""

from __future__ import annotations

from typing import Any

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

from .models import (
    IncidentResponseAction,
    IncidentResponseObservation,
    IncidentResponseState,
)


class IncidentResponseEnv(
    EnvClient[
        IncidentResponseAction,
        IncidentResponseObservation,
        IncidentResponseState,
    ]
):
    """Typed client for the Incident Response OpenEnv server."""

    def _step_payload(self, action: IncidentResponseAction) -> dict[str, Any]:
        return action.model_dump(exclude_none=True)

    def _parse_result(
        self, payload: dict[str, Any]
    ) -> StepResult[IncidentResponseObservation]:
        observation = IncidentResponseObservation(**payload.get("observation", {}))
        reward = payload.get("reward")
        done = payload.get("done", observation.done)
        observation.reward = reward
        observation.done = done
        return StepResult(observation=observation, reward=reward, done=done)

    def _parse_state(self, payload: dict[str, Any]) -> IncidentResponseState:
        return IncidentResponseState(**payload)
