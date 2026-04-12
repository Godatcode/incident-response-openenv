"""Task 3: The Intermittent Phantom — cache-layer memory leak causing GC pauses."""

from __future__ import annotations

from datetime import datetime, timezone

from src.graders.hard_grader import HardGrader
from src.models import Action, ActionType, Observation, Reward, ServiceStatus, State
from src.simulation.alerts import get_alerts
from src.simulation.logs import format_logs
from src.simulation.metrics import format_metrics
from src.simulation.services import ServiceNode, build_services_hard
from src.tasks.base import BaseTask

_DEPENDENCY_GRAPH = {
    "api-gateway": ["auth-service", "user-service", "order-service", "payment-service"],
    "auth-service": [],
    "user-service": ["cache-layer"],
    "order-service": ["cache-layer", "payment-service"],
    "payment-service": ["cache-layer"],
    "notification-service": [],
    "analytics-service": [],
    "cache-layer": [],
}


class HardPhantomTask(BaseTask):
    name = "hard_phantom"
    max_steps = 20
    dependency_graph = _DEPENDENCY_GRAPH
    ground_truth_root_cause = (
        "cache-layer memory leak (~50MB/hour RSS growth) causing periodic Major GC "
        "stop-the-world pauses (180ms → 1580ms and growing). "
        "GC pauses block all cache-layer connections, causing downstream latency spikes "
        "in order-service, payment-service, and api-gateway. "
        "Mitigation: scale cache-layer to 3 replicas to reduce per-instance memory pressure."
    )
    ground_truth_affected_services = [
        "cache-layer", "order-service", "payment-service", "api-gateway"
    ]
    ground_truth_optimal_actions = [
        "investigate alerting services (api-gateway, order-service, payment-service)",
        "identify cache-layer as common dependency",
        "query_metrics(cache-layer, memory)",
        "check_logs(cache-layer)",
        "scale_service(cache-layer, 3)",
        "run_healthcheck(cache-layer)",
        "mark_resolved(cache-layer memory leak causing GC pauses)",
    ]

    def __init__(self) -> None:
        self._services: dict[str, ServiceNode] = {}
        self._alerts = []
        self._step_number = 0
        self._done = False
        self._timeline: list[str] = []
        self._action_history: list[dict] = []
        self._grader = HardGrader()
        self._checkpoints_hit: list[str] = []
        self._cumulative_reward = 0.0
        self._last_action_result = ""

    def reset(self) -> Observation:
        self._services = build_services_hard()
        self._alerts = get_alerts(self.name)
        self._step_number = 0
        self._done = False
        self._timeline = [
            "2024-01-15 11:00:00 UTC — cache-layer memory RSS at 2.1GB (baseline)",
            "2024-01-15 12:30:00 UTC — First GC pause: 180ms (minor)",
            "2024-01-15 13:00:00 UTC — Alert: auth-service config updated (log level change)",
            "2024-01-15 13:00:00 UTC — GC pause: 450ms — first downstream latency spike observed",
            "2024-01-15 13:30:00 UTC — Analytics batch job started (scheduled, unrelated)",
            "2024-01-15 14:00:00 UTC — GC pause: 820ms — api-gateway P99 spike to 1.8s",
            "2024-01-15 14:30:00 UTC — GC pause: 1240ms — payment-service timeouts",
            "2024-01-15 14:30:00 UTC — Alert: api-gateway P99 >1s intermittently",
            "2024-01-15 14:30:00 UTC — Alert: order-service P99 >1.5s intermittently",
            "2024-01-15 14:45:00 UTC — Alert: payment-service P99 >1.2s intermittently",
            "2024-01-15 14:55:00 UTC — cache-layer RSS now 3.35GB (+1.25GB in 4 hours)",
        ]
        self._action_history = []
        self._checkpoints_hit = []
        self._cumulative_reward = 0.0
        self._last_action_result = (
            "Incident opened. Multiple intermittent latency alerts. "
            "No services are fully down. Investigate pattern and root cause."
        )
        return self._build_observation()

    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict]:
        if self._done:
            obs = self._build_observation()
            return obs, Reward(value=0.0, reason="Episode already complete."), True, {}

        self._step_number += 1
        info: dict = {}
        penalty = 0.0
        result_text = ""

        target = action.target_service
        atype = action.action_type

        all_services = list(self._services.keys())
        if atype != ActionType.MARK_RESOLVED and target not in self._services:
            result_text = (
                f"Error: Service '{target}' not found. "
                f"Available services: {', '.join(all_services)}"
            )
            penalty = 0.02
            info["last_action_error"] = f"Service '{target}' not found"
            self._last_action_result = result_text
            self._action_history.append(
                {"action_type": atype.value, "target_service": target, "parameters": action.parameters}
            )
            return (
                self._build_observation(),
                Reward(value=0.0, reason=f"Invalid action: {info['last_action_error']}"),
                self._done,
                info,
            )

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if atype == ActionType.CHECK_LOGS:
            result_text = format_logs(self.name, target)
            self._timeline.append(f"{ts} — Agent checked logs for {target}")

        elif atype == ActionType.QUERY_METRICS:
            metric_type = action.parameters.get("metric_type", "cpu")
            result_text = format_metrics(self.name, target, metric_type)
            self._timeline.append(f"{ts} — Agent queried {metric_type} metrics for {target}")

        elif atype == ActionType.RESTART_SERVICE:
            svc = self._services[target]
            self._timeline.append(f"{ts} — Agent restarted {target}")
            if target == "cache-layer":
                # WRONG: restarting cache causes thundering herd
                penalty += 0.20
                svc.status = "healthy"
                svc.replicas = svc.replicas  # unchanged
                result_text = (
                    "[CRITICAL MISTAKE] cache-layer restarted — CACHE CLEARED.\n"
                    "All cached data lost. Backend services are now hammering the database "
                    "with cold-cache requests (thundering herd / cache stampede).\n"
                    "order-service: DB connection pool exhausted (500 errors)\n"
                    "payment-service: DB query latency >30s\n"
                    "api-gateway: error rate spiking to 65%\n"
                    "The situation is now WORSE than before. "
                    "Scaling cache-layer would have been the correct mitigation."
                )
                self._services["order-service"].status = "down"
                self._services["payment-service"].status = "degraded"
                self._services["api-gateway"].status = "degraded"
            elif target == "auth-service":
                penalty += 0.05
                result_text = (
                    f"[INFO] auth-service restarted. "
                    f"Note: auth-service config change was a routine log level update "
                    f"2 hours ago and was not related to the incident. "
                    f"Latency spikes continue on other services."
                )
            else:
                result_text = svc.restart()

        elif atype == ActionType.ROLLBACK_DEPLOY:
            self._timeline.append(f"{ts} — Agent rolled back deploy for {target}")
            if target == "auth-service":
                penalty += 0.10
                result_text = (
                    "[WARNING] auth-service deploy rolled back. "
                    "This was a red herring — the config change (log level) was unrelated to "
                    "the latency spikes. Latency continues on other services."
                )
            elif target == "cache-layer":
                msg, success = self._services[target].rollback()
                result_text = msg + (
                    "\n[INFO] cache-layer has no prior deploy to roll back to. "
                    "The issue is a memory leak in the running version, not a recent deploy."
                )
            else:
                msg, success = self._services[target].rollback()
                result_text = msg

        elif atype == ActionType.SCALE_SERVICE:
            replicas = action.parameters.get("replicas", 2)
            result_text = self._services[target].scale(replicas)
            self._timeline.append(f"{ts} — Agent scaled {target} to {replicas} replicas")
            if target == "cache-layer" and replicas >= 2:
                # Correct mitigation
                self._services["order-service"].status = "healthy"
                self._services["payment-service"].status = "healthy"
                self._services["api-gateway"].status = "healthy"
                self._alerts = [
                    a for a in self._alerts
                    if a.severity == "info"  # Keep info alerts, clear warnings
                ]
                result_text += (
                    "\n[SUCCESS] cache-layer load distributed across instances. "
                    f"Per-instance memory pressure reduced. GC pause intervals increasing. "
                    f"Downstream latency spikes subsiding. "
                    f"P99 latency on api-gateway/order-service/payment-service returning to normal."
                )

        elif atype == ActionType.RUN_HEALTHCHECK:
            result_text = self._services[target].healthcheck()
            self._timeline.append(f"{ts} — Agent ran healthcheck on {target}: {self._services[target].status}")

        elif atype == ActionType.MARK_RESOLVED:
            summary = action.parameters.get("root_cause_summary", "")
            result_text = self._handle_mark_resolved(summary)
            self._timeline.append(f"{ts} — Agent marked incident resolved: '{summary[:80]}'")

        self._last_action_result = result_text
        action_record = {
            "action_type": atype.value,
            "target_service": target,
            "parameters": action.parameters,
        }
        self._action_history.append(action_record)

        prev_checkpoints = list(self._checkpoints_hit)
        new_checkpoints = self._grader.evaluate_checkpoints(
            self._action_history, self._services, action_record
        )
        self._checkpoints_hit = new_checkpoints

        delta, raw_delta, newly_hit, reason = self._grader.compute_delta_reward(
            prev_checkpoints, new_checkpoints, penalty
        )
        self._cumulative_reward = min(
            1.0, max(0.0, self._cumulative_reward + raw_delta)
        )

        if atype == ActionType.MARK_RESOLVED or self._step_number >= self.max_steps:
            self._done = True

        obs = self._build_observation()
        return obs, Reward(value=delta, reason=reason), self._done, info

    def get_state(self) -> State:
        return State(
            task_name=self.name,
            step_number=self._step_number,
            max_steps=self.max_steps,
            observation=self._build_observation(),
            ground_truth_root_cause=self.ground_truth_root_cause,
            ground_truth_affected_services=self.ground_truth_affected_services,
            ground_truth_optimal_actions=self.ground_truth_optimal_actions,
            checkpoints_hit=self._checkpoints_hit,
            cumulative_reward=min(0.99, max(0.01, self._cumulative_reward)),
            done=self._done,
        )

    def _build_observation(self) -> Observation:
        svc_statuses = [
            ServiceStatus(
                name=s.name,
                status=s.status,
                last_deploy_time=s.last_deploy_time(),
                replicas=s.replicas,
            )
            for s in self._services.values()
        ]
        return Observation(
            active_alerts=list(self._alerts),
            service_statuses=svc_statuses,
            dependency_graph=self.dependency_graph,
            incident_timeline=list(self._timeline),
            last_action_result=self._last_action_result,
            available_actions=self.AVAILABLE_ACTIONS,
            step_number=self._step_number,
            max_steps=self.max_steps,
        )

    def _handle_mark_resolved(self, summary: str) -> str:
        lower = summary.lower()
        cache_mentioned = "cache" in lower or "cache-layer" in lower
        cause_mentioned = (
            "memory" in lower or "leak" in lower or "gc" in lower
            or "garbage" in lower or "pause" in lower
        )
        if cache_mentioned and cause_mentioned:
            if self._services["cache-layer"].status == "healthy":
                return (
                    "Incident marked RESOLVED. Root cause correctly identified: "
                    "cache-layer memory leak / GC pauses causing downstream latency. Incident closed."
                )
            return (
                "Incident marked resolved. Root cause correctly identified, "
                "but cache-layer has not been mitigated yet."
            )
        return (
            "Incident marked resolved. Root cause summary is incomplete — "
            "please mention cache-layer memory leak or GC pauses."
        )
