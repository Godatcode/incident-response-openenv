"""Entry point for the OpenEnv-compatible incident response server."""

from __future__ import annotations

import os

from fastapi import FastAPI
from openenv.core.env_server.http_server import create_app

from incident_response_env.models import (
    IncidentResponseAction,
    IncidentResponseObservation,
)
from server.incident_response_environment import IncidentResponseEnvironment
from src.env import IncidentResponseEnv as IncidentResponseSimulator

app: FastAPI = create_app(
    IncidentResponseEnvironment,
    IncidentResponseAction,
    IncidentResponseObservation,
    env_name="incident_response",
    max_concurrent_envs=4,
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "healthy",
        "environment": "incident_response",
        "version": "1.0.0",
    }


@app.get("/tasks")
def list_tasks() -> dict[str, object]:
    return {
        "tasks": IncidentResponseSimulator.list_tasks(),
        "descriptions": {
            "easy_oom_outage": "Single service OOM crash. Diagnose and restart.",
            "medium_bad_deploy": (
                "Bad deployment with cascading failures and a search-service red herring."
            ),
            "hard_phantom": (
                "Intermittent latency caused by cache-layer memory pressure and GC pauses."
            ),
        },
    }


def main(host: str = "0.0.0.0", port: int | None = None) -> None:
    """Start the production server."""
    import uvicorn

    resolved_port = port or int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=resolved_port)


if __name__ == "__main__":
    main()
