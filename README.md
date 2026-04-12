---
title: Incident Response OpenEnv
emoji: 🚨
colorFrom: red
colorTo: red
sdk: docker
app_port: 8000
tags:
  - openenv
---

# Incident Response Simulator

An OpenEnv RL environment that simulates production incident response for training and evaluating LLM agents.

---

## Motivation

Real SRE incident response requires sequential reasoning, evidence correlation, and careful action selection under uncertainty. Most existing LLM benchmarks focus on code generation or question answering. This environment captures the operational reasoning loop that SREs perform daily: alerts fire, multiple services may be affected, some signals are red herrings, and the agent must identify the root cause before taking the right mitigation action.

Current benchmarks lack:
- Realistic multi-signal environments with red herrings
- Sequential action-reward loops with meaningful per-step feedback
- Penalty signals for actively harmful actions (e.g. cache stampede from a bad restart)
- Tasks calibrated across difficulty levels

---

## Environment Overview

The RL loop:

```
Observation (alerts + statuses + dependency graph)
        ↓
   Agent action (JSON)
        ↓
   Environment step → (new observation, reward, done)
        ↓
  Repeat until mark_resolved or max_steps
```

Each episode is a production incident. The agent receives structured observations and must take a sequence of investigative and remediation actions to diagnose and resolve the incident.

---

## Observation Space

| Field | Type | Description |
|---|---|---|
| `active_alerts` | `list[Alert]` | Firing alerts: severity, service, message, timestamp |
| `service_statuses` | `list[ServiceStatus]` | Name, status (healthy/degraded/down), replicas, last deploy time |
| `dependency_graph` | `dict[str, list[str]]` | Service → list of services it depends on |
| `incident_timeline` | `list[str]` | Chronological event log (system events + agent actions) |
| `last_action_result` | `str` | Full text output of the previous action |
| `available_actions` | `list[str]` | Human-readable list of valid action formats |
| `step_number` | `int` | Current step within the episode |
| `max_steps` | `int` | Maximum steps before episode terminates |

---

## Action Space

| Action Type | Parameters | Description |
|---|---|---|
| `check_logs` | `target_service` | Retrieve last 20 log lines for a service |
| `query_metrics` | `target_service`, `metric_type: cpu\|memory\|latency\|error_rate` | Get 30-min metric table (6 data points) |
| `restart_service` | `target_service` | Restart a service (dangerous if wrong service) |
| `rollback_deploy` | `target_service` | Roll back to the previous deployment version |
| `scale_service` | `target_service`, `replicas: int` | Scale service to N replicas |
| `run_healthcheck` | `target_service` | Run HTTP health check and report status |
| `mark_resolved` | `root_cause_summary: str` | Close the incident with a root cause explanation |

All actions are submitted as JSON:
```json
{"action_type": "check_logs", "target_service": "user-service"}
{"action_type": "query_metrics", "target_service": "cache-layer", "parameters": {"metric_type": "memory"}}
{"action_type": "mark_resolved", "parameters": {"root_cause_summary": "user-service OOM, restarted"}}
```

---

## Tasks

### Task 1: Easy — The Obvious Outage (`easy_oom_outage`)

**Difficulty:** Easy | **Max steps:** 10 | **Services:** 4

**Scenario:** `user-service` is DOWN due to a Java heap OOM kill (exit code 137). `api-gateway` is returning 502s on all user-facing endpoints. `notification-service` is degraded because it depends on `user-service` for preference lookups.

**What makes it challenging:** The agent must look past the downstream symptoms (api-gateway errors, notification backlog) and identify the root cause in `user-service` logs — OOM, not a deploy or config issue.

**Optimal path:**
1. `check_logs(user-service)` → see `OutOfMemoryError: Java heap space`, `Exit code 137`
2. `restart_service(user-service)` → service recovers
3. `run_healthcheck(user-service)` → confirm healthy
4. `mark_resolved("user-service crashed due to OOM, restarted")`

---

### Task 2: Medium — The Bad Deploy (`medium_bad_deploy`)

**Difficulty:** Medium | **Max steps:** 15 | **Services:** 6

**Scenario:** `order-service` had a bad deploy (v2.3.1) 10 minutes ago. A `NullPointerException` in the payment handler is causing >50% error rate. `inventory-service` is degraded as a downstream effect. **Red herring:** `search-service` shows a WARNING for high CPU — it's actually a scheduled weekly reindex job.

**What makes it challenging:** Three alerts fire at once. The agent must correlate the deploy timestamp in `order-service` logs with the error onset, avoid the CPU red herring, and choose `rollback_deploy` over `restart_service` (restart doesn't fix bad code).

**Optimal path:**
1. `check_logs(order-service)` → see `NullPointerException` + deploy v2.3.1 timestamp
2. `check_logs(inventory-service)` → confirm downstream timeout, not primary cause
3. `rollback_deploy(order-service)` → reverts to v2.3.0, errors clear
4. `run_healthcheck(inventory-service)` → confirm recovery
5. `mark_resolved("bad deploy v2.3.1 on order-service caused 500s, rolled back")`

---

### Task 3: Hard — The Intermittent Phantom (`hard_phantom`)

**Difficulty:** Hard | **Max steps:** 20 | **Services:** 8

**Scenario:** Intermittent P99 latency spikes on `api-gateway`, `order-service`, and `payment-service`. No service is fully down. The root cause is `cache-layer` — a memory leak growing at ~50MB/hour causes periodic Major GC stop-the-world pauses that block all cache connections, causing downstream latency spikes every 15-20 minutes.

**Red herrings:**
- `auth-service` had a config change 2 hours ago (routine log level change — benign)
- `analytics-service` shows 75% CPU (scheduled daily batch job — expected)
- Traffic increased 15% in the past hour (within normal range)

**What makes it challenging:** No service is hard-down. The root cause (`cache-layer`) doesn't appear in alerts — the agent must trace the dependency graph to find the common upstream. Restarting `cache-layer` is the worst possible action: it clears the cache and causes a thundering herd / cache stampede on the backends (heavily penalized). The correct mitigation is scaling horizontally to reduce per-instance memory pressure.

**Optimal path:**
1. Investigate alerting services — notice spikes are intermittent, not constant
2. Trace dependency graph — find `cache-layer` as common dependency
3. `query_metrics(cache-layer, memory)` → see RSS climbing: 3.1GB → 3.35GB
4. `check_logs(cache-layer)` → find `GC pause 1240ms`, `GC pause 1580ms`, memory leak suspected
5. `scale_service(cache-layer, 3)` → distribute load, reduce per-instance memory pressure
6. `run_healthcheck(cache-layer)` → confirm improvement
7. `mark_resolved("cache-layer memory leak causing GC pauses, scaled horizontally")`

---

## Reward Function

Rewards are **incremental** — each `step()` returns the delta reward for that specific step only (newly unlocked checkpoints minus penalties). The grader tracks cumulative progress internally.

### Task 1: Easy Reward Table

| Checkpoint | Reward | Condition |
|---|---|---|
| `checked_affected_logs` | +0.15 | `check_logs(user-service)` called |
| `identified_oom` | +0.15 | user-service logs or memory metrics checked |
| `restarted_correct` | +0.30 | `restart_service(user-service)` called |
| `healthcheck_passed` | +0.15 | `run_healthcheck(user-service)` after restart |
| `marked_resolved_correct` | +0.25 | Summary mentions OOM + user-service |
| **Penalty: restart wrong service** | -0.10 | `restart_service` on non-root-cause service |

### Task 2: Medium Reward Table

| Checkpoint | Reward | Condition |
|---|---|---|
| `investigated_multiple` | +0.10 | Investigated ≥2 distinct services |
| `correlated_deploy_timing` | +0.15 | `check_logs(order-service)` called |
| `avoided_red_herring` | +0.10 | Never restarted/rolled-back search-service |
| `rolled_back_order` | +0.25 | `rollback_deploy(order-service)` called |
| `verified_downstream` | +0.15 | Checked inventory-service/api-gateway after rollback |
| `marked_resolved_correct` | +0.25 | Summary mentions deploy + order-service |
| **Penalty: rollback wrong service** | -0.15 | Rollback on search-service or other |
| **Penalty: restart instead of rollback** | -0.05 | `restart_service(order-service)` |

### Task 3: Hard Reward Table

| Checkpoint | Reward | Condition |
|---|---|---|
| `investigated_3_services` | +0.05 | Investigated ≥3 distinct services |
| `identified_cache_dependency` | +0.10 | Checked cache-layer (logs/metrics/healthcheck) |
| `queried_cache_memory` | +0.15 | `query_metrics(cache-layer, memory)` called |
| `checked_cache_logs` | +0.15 | `check_logs(cache-layer)` called |
| `correlated_gc_latency` | +0.10 | Queried latency on ≥2 affected services + cache memory/logs |
| `scaled_cache` | +0.20 | `scale_service(cache-layer, N≥2)` called |
| `did_not_restart_cache` | +0.05 | Bonus if cache-layer was never restarted |
| `healthcheck_after_scale` | +0.05 | `run_healthcheck` called after scaling |
| `marked_resolved_correct` | +0.15 | Summary mentions cache + memory/GC/leak |
| **Penalty: restarted cache-layer** | -0.20 | `restart_service(cache-layer)` — thundering herd |
| **Penalty: rolled back auth-service** | -0.10 | Chasing config-change red herring |

---

## Setup & Usage

### Docker (recommended)

```bash
docker build -t incident-response-env .
docker run -p 8000:8000 incident-response-env
```

### Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.app:app --reload --port 8000
```

### API endpoints

```bash
# List available tasks
curl http://localhost:8000/tasks

# Start a task
curl -X POST "http://localhost:8000/reset" \
  -H "Content-Type: application/json" \
  -d '{"task_name":"easy_oom_outage"}'

# Take an action
curl -X POST "http://localhost:8000/step" \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "check_logs", "target_service": "user-service"}}'

# Get full state (includes ground truth)
curl http://localhost:8000/state

# Get OpenEnv metadata and schemas
curl http://localhost:8000/metadata
curl http://localhost:8000/schema
```

### Run inference baseline

```bash
# Run against the locally built Docker image
LOCAL_IMAGE_NAME=incident-response-env \
API_BASE_URL=https://your-endpoint/v1 \
MODEL_NAME=your-model \
HF_TOKEN=<token> \
INCIDENT_RESPONSE_TASK=easy_oom_outage \
python inference.py
```

`inference.py` emits only the required `[START]`, `[STEP]`, and `[END]` lines on
stdout. By default it runs all three tasks, falls back to the in-process simulator
when no `LOCAL_IMAGE_NAME` or `OPENENV_BASE_URL` is provided, and uses the OpenAI
client when `HF_TOKEN` or `OPENAI_API_KEY` is available.

### Run tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Baseline Scores

| Task | Model | Score | Steps |
|---|---|---|---|
| `easy_oom_outage` | gpt-4.1-mini | ~0.85 | 4-6 |
| `medium_bad_deploy` | gpt-4.1-mini | ~0.70 | 6-9 |
| `hard_phantom` | gpt-4.1-mini | ~0.45 | 10-14 |
| `easy_oom_outage` | random policy | ~0.10 | 10 |
| `medium_bad_deploy` | random policy | ~0.08 | 15 |
| `hard_phantom` | random policy | ~0.05 | 20 |

---

## Architecture

```
incident_response_env/
├── client.py           Typed OpenEnv client used by inference.py
├── models.py           Public Action / Observation / State exports
server/
├── app.py              OpenEnv FastAPI / WebSocket server entry point
├── incident_response_environment.py  Stateful OpenEnv wrapper
src/
├── env.py              Core simulator and task registry
├── models.py           Internal typed models shared by tasks and wrappers
├── tasks/
│   ├── base.py         Abstract BaseTask
│   ├── easy_oom_outage.py    Task 1 implementation
│   ├── medium_bad_deploy.py  Task 2 implementation
│   └── hard_phantom.py       Task 3 implementation
├── graders/
│   ├── base.py         Abstract BaseGrader with delta-reward helper
│   ├── easy_grader.py
│   ├── medium_grader.py
│   └── hard_grader.py
└── simulation/
    ├── services.py     ServiceNode state machines (restart/rollback/scale)
    ├── logs.py         Pre-generated realistic log data per task/service
    ├── metrics.py      Pre-generated metric snapshots (30-min tables)
    └── alerts.py       Pre-generated Alert objects per task
```

All state is text-based. No databases, no ML models, no heavy dependencies. The entire environment runs in-process with minimal memory footprint — well within the 2 vCPU / 8 GB constraint.
