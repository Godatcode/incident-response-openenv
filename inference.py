"""
Baseline inference script for Incident Response OpenEnv.

Usage:
    HF_TOKEN=<your-token> python inference.py

Environment variables:
    HF_TOKEN    — required. API key / HuggingFace token for the LLM endpoint.
    API_BASE_URL — LLM API base URL (default: https://api.openai.com/v1)
    MODEL_NAME   — model identifier (default: gpt-4.1-mini)
    ENV_URL      — base URL of the running environment server (default: http://localhost:8000)
"""

import json
import os

import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")
ENV_NAME = "incident-response"
TASKS = ["easy_oom_outage", "medium_bad_deploy", "hard_phantom"]

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


def format_observation(obs: dict) -> str:
    """Format observation dict into readable text for the LLM."""
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
        parts.append(f"  {svc} → depends on: {dep_str}")

    parts.append("\n=== INCIDENT TIMELINE ===")
    for event in obs["incident_timeline"]:
        parts.append(f"  • {event}")

    if obs.get("last_action_result"):
        parts.append(f"\n=== LAST ACTION RESULT ===\n{obs['last_action_result']}")

    parts.append(f"\nStep {obs['step_number']}/{obs['max_steps']}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Task runner
# ---------------------------------------------------------------------------


def run_task(task_name: str) -> None:
    """Run a single task episode and print formatted output."""
    print(f"[START] task={task_name} env={ENV_NAME} model={MODEL_NAME}")

    rewards: list[float] = []
    steps = 0
    success = False
    last_error = None
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    try:
        # Reset environment
        resp = requests.post(f"{ENV_URL}/reset", params={"task_name": task_name}, timeout=30)
        resp.raise_for_status()
        obs = resp.json()

        done = False
        while not done:
            # Format observation for LLM
            obs_text = format_observation(obs)
            messages.append({"role": "user", "content": obs_text})

            # Get LLM action
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
                # Fallback: safe default action
                action = {"action_type": "check_logs", "target_service": "api-gateway"}

            # Step environment
            step_resp = requests.post(
                f"{ENV_URL}/step", json=action, timeout=30
            )
            step_resp.raise_for_status()
            result = step_resp.json()

            obs = result["observation"]
            reward_obj = result["reward"]
            reward = (
                reward_obj["value"]
                if isinstance(reward_obj, dict)
                else float(reward_obj)
            )
            done = result["done"]
            last_error = result.get("info", {}).get("last_action_error")

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

    score = max(0.0, min(1.0, sum(rewards)))
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={'true' if success else 'false'} steps={steps} score={score:.2f} rewards={rewards_str}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for task in TASKS:
        run_task(task)
