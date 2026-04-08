"""
Baseline inference script for Incident Response OpenEnv.

Usage:
    HF_TOKEN=<your-token> python inference.py

Environment variables:
    HF_TOKEN     — HuggingFace API token (required)
    API_BASE_URL — LLM API base URL (default: https://api.openai.com/v1)
    MODEL_NAME   — model identifier (default: gpt-4.1-mini)
"""

import json
import os
import sys

from openai import OpenAI

from src.env import IncidentResponseEnv
from src.models import Action

# ---------------------------------------------------------------------------
# Configuration — read env vars exactly as the evaluator injects them
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

# Evaluator injects API_KEY for the LiteLLM proxy; use it if present,
# otherwise fall back to HF_TOKEN for standalone runs.
API_KEY = os.getenv("API_KEY") or HF_TOKEN

ENV_NAME = "incident-response"
TASKS = ["easy_oom_outage", "medium_bad_deploy", "hard_phantom"]

# Initialize OpenAI client at module level (as shown in the guidelines example).
# In the evaluator, API_KEY is always set. Guard for local dev without a key.
if API_KEY:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
else:
    client = None

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert SRE (Site Reliability Engineer) performing incident response.
You are given a production incident with alerts, service statuses, and a dependency graph.
Your goal is to diagnose the root cause and resolve the incident.

Available actions (respond with EXACTLY one JSON object per turn):
- {"action_type": "check_logs", "target_service": "<name>"}
- {"action_type": "query_metrics", "target_service": "<name>", "parameters": {"metric_type": "cpu|memory|latency|error_rate"}}
- {"action_type": "restart_service", "target_service": "<name>"}
- {"action_type": "rollback_deploy", "target_service": "<name>"}
- {"action_type": "scale_service", "target_service": "<name>", "parameters": {"replicas": <int>}}
- {"action_type": "run_healthcheck", "target_service": "<name>"}
- {"action_type": "mark_resolved", "parameters": {"root_cause_summary": "<your summary>"}}

Strategy:
1. Read alerts and service statuses carefully
2. Check logs and metrics of affected services
3. Identify root cause before taking mitigation action
4. Take the MINIMUM necessary action to resolve
5. Verify with healthcheck
6. Mark resolved with a clear root cause summary

Respond ONLY with a single JSON object. No explanation, no markdown."""


# ---------------------------------------------------------------------------
# Observation formatter
# ---------------------------------------------------------------------------


def format_observation(obs) -> str:
    """Format Observation model into readable text for the LLM."""
    # Handle both Pydantic model and dict
    if hasattr(obs, "model_dump"):
        obs = obs.model_dump()

    parts = []

    parts.append("=== ACTIVE ALERTS ===")
    for alert in obs["active_alerts"]:
        parts.append(
            f"[{alert['severity'].upper()}] {alert['service']}: "
            f"{alert['message']} (at {alert['timestamp']})"
        )
    if not obs["active_alerts"]:
        parts.append("  (no active alerts)")

    parts.append("\n=== SERVICE STATUSES ===")
    for svc in obs["service_statuses"]:
        deploy_info = (
            f" (last deploy: {svc['last_deploy_time']})"
            if svc.get("last_deploy_time")
            else ""
        )
        parts.append(
            f"  {svc['name']}: {svc['status']} "
            f"(replicas: {svc['replicas']}){deploy_info}"
        )

    parts.append("\n=== DEPENDENCY GRAPH ===")
    for svc, deps in obs["dependency_graph"].items():
        dep_str = ", ".join(deps) if deps else "none"
        parts.append(f"  {svc} -> depends on: {dep_str}")

    parts.append("\n=== INCIDENT TIMELINE ===")
    for event in obs["incident_timeline"]:
        parts.append(f"  - {event}")

    if obs.get("last_action_result"):
        parts.append(f"\n=== LAST ACTION RESULT ===\n{obs['last_action_result']}")

    parts.append(f"\nStep {obs['step_number']}/{obs['max_steps']}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Task runner
# ---------------------------------------------------------------------------


def run_task(env: IncidentResponseEnv, task_name: str) -> None:
    """Run a single task episode and print formatted output."""
    print(f"[START] task={task_name} env={ENV_NAME} model={MODEL_NAME}")

    rewards: list[float] = []
    steps = 0
    success = False
    last_error = None

    try:
        if client is None:
            raise RuntimeError("No API key provided. Set API_KEY or HF_TOKEN environment variable.")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Reset environment (direct Python call — no HTTP)
        obs = env.reset(task_name)

        done = False
        while not done:
            obs_text = format_observation(obs)
            messages.append({"role": "user", "content": obs_text})

            # LLM call through the proxy
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.0,
                max_tokens=256,
            )
            action_str = completion.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": action_str})

            # Parse action — strip markdown fences if present
            clean = action_str
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
            try:
                action = json.loads(clean)
            except json.JSONDecodeError:
                action = {"action_type": "check_logs", "target_service": "api-gateway"}

            # Step environment (direct Python call — no HTTP)
            obs, reward_obj, done, info = env.step(action)

            reward = reward_obj.value if hasattr(reward_obj, "value") else float(reward_obj)
            last_error = info.get("last_action_error") if isinstance(info, dict) else None

            steps += 1
            rewards.append(reward)

            error_str = last_error if last_error else "null"
            done_str = "true" if done else "false"
            print(
                f"[STEP] step={steps} action={action_str} "
                f"reward={reward:.2f} done={done_str} error={error_str}"
            )

        success = True

    except Exception as exc:
        last_error = str(exc)
        steps = max(steps, 1)
        if not rewards:
            rewards = [0.0]
        print(
            f"[STEP] step={steps} action=error reward=0.00 done=true error={last_error}"
        )

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={'true' if success else 'false'} steps={steps} rewards={rewards_str}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    env = IncidentResponseEnv()
    try:
        for task in TASKS:
            run_task(env, task)
    except Exception as exc:
        print(f"[END] success=false steps=0 rewards=0.00 error={exc}")
    finally:
        env.close()
    sys.exit(0)
