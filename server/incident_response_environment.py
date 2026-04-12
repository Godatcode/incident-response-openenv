"""OpenEnv server wrapper for the incident response simulator."""

from __future__ import annotations

from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import EnvironmentMetadata

from incident_response_env.models import (
    IncidentResponseAction,
    IncidentResponseObservation,
    IncidentResponseState,
)
from src.env import IncidentResponseEnv as IncidentResponseSimulator


class IncidentResponseEnvironment(
    Environment[
        IncidentResponseAction,
        IncidentResponseObservation,
        IncidentResponseState,
    ]
):
    """Stateful OpenEnv wrapper around the existing task simulator."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        super().__init__()
        self._sim = IncidentResponseSimulator()
        self._episode_id = str(uuid4())

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        task_name: str | None = None,
        **kwargs: object,
    ) -> IncidentResponseObservation:
        del seed, kwargs
        self._episode_id = episode_id or str(uuid4())
        observation = self._sim.reset(task_name=task_name)
        return IncidentResponseObservation(**observation.model_dump())

    def step(
        self,
        action: IncidentResponseAction,
        timeout_s: float | None = None,
        **kwargs: object,
    ) -> IncidentResponseObservation:
        del timeout_s, kwargs
        observation, reward, done, info = self._sim.step(action)
        payload = observation.model_dump()
        payload["reward"] = reward.value
        payload["done"] = done
        metadata = dict(payload.get("metadata", {}))
        metadata["reward_reason"] = reward.reason
        if info:
            metadata["info"] = info
        payload["metadata"] = metadata
        return IncidentResponseObservation(**payload)

    @property
    def state(self) -> IncidentResponseState:
        raw_state = self._sim.state().model_dump()
        raw_state["episode_id"] = self._episode_id
        raw_state["step_count"] = raw_state.get("step_number", 0)
        return IncidentResponseState(**raw_state)

    def close(self) -> None:
        self._sim.close()

    def get_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(
            name="incident_response",
            description=(
                "Production incident-response simulator for evaluating agents on "
                "SRE triage, diagnosis, and remediation."
            ),
            version="1.0.0",
            author="Team Name",
        )
