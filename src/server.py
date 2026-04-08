"""FastAPI server exposing the IncidentResponseEnv via HTTP."""

from __future__ import annotations

import json as _json

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from src.env import IncidentResponseEnv
from src.models import Action, Observation, Reward, State

app = FastAPI(
    title="Incident Response OpenEnv",
    description=(
        "Production Incident Response Simulator — an OpenEnv RL environment "
        "for training and evaluating LLM agents on SRE incident triage."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = IncidentResponseEnv()


@app.get("/")
def root() -> dict:
    """Root endpoint."""
    return {"status": "ok", "environment": "incident-response", "version": "1.0.0"}


@app.post("/reset", response_model=Observation)
async def reset(request: Request, task_name: str = "easy_oom_outage") -> Observation:
    """Reset environment to initial state for the given task."""
    body_bytes = await request.body()
    if body_bytes:
        try:
            body_data = _json.loads(body_bytes)
            if isinstance(body_data, dict):
                task_name = body_data.get("task_name") or task_name
        except _json.JSONDecodeError:
            pass
    try:
        return env.reset(task_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step")
def step(action: Action) -> dict:
    """Execute an action in the environment."""
    try:
        obs, reward, done, info = env.step(action)
        return {
            "observation": obs.model_dump(),
            "reward": reward.model_dump(),
            "done": done,
            "info": info,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state", response_model=State)
def get_state() -> State:
    """Returns the current full internal state (includes ground truth)."""
    try:
        return env.state()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> dict:
    """List all available tasks."""
    return {
        "tasks": IncidentResponseEnv.list_tasks(),
        "descriptions": {
            "easy_oom_outage": "Single service OOM crash. Diagnose and restart. (max 10 steps)",
            "medium_bad_deploy": "Bad deployment with cascading failures and a red herring. (max 15 steps)",
            "hard_phantom": "Intermittent latency from memory leak with multiple red herrings. (max 20 steps)",
        },
    }
