"""Task 1: The Obvious Outage — user-service OOM kill."""

from __future__ import annotations

import copy
from datetime import datetime, timezone

from src.graders.easy_grader import EasyGrader
from src.models import Action, ActionType, Observation, Reward, ServiceStatus, State
from src.simulation.alerts import get_alerts
from src.simulation.logs import format_logs
from src.simulation.metrics import format_metrics
from src.simulation.services import ServiceNode, build_services_easy
from src.tasks.base import BaseTask

_DEPENDENCY_GRAPH = {
    "api-gateway": ["user-service", "payment-service"],
    "user-service": [],
    "payment-service": [],
    "notification-service": ["user-service"],
}


class EasyOomOutageTask(BaseTask):
    name = "easy_oom_outage"
    max_steps = 10
    dependency_graph = _DEPENDENCY_GRAPH
    ground_truth_root_cause = (
        "user-service crashed due to Java heap OOM (OutOfMemoryError). "
        "Process killed by OOM killer (exit code 137). "
        "Resolution: restart user-service."
    )
    ground_truth_affected_services = ["user-service", "api-gateway", "notification-service"]
    ground_truth_optimal_actions = [
        "check_logs(user-service)",
        "restart_service(user-service)",
        "run_healthcheck(user-service)",
        "mark_resolved(OOM on user-service, restarted)",
    ]

    def __init__(self) -> None:
        self._services: dict[str, ServiceNode] = {}
        self._alerts = []
        self._step_number = 0
        self._done = False
        self._timeline: list[str] = []
        self._action_history: list[dict] = []
        self._grader = EasyGrader()
        self._checkpoints_hit: list[str] = []
        self._cumulative_reward = 0.0
        self._last_action_result = ""

    def reset(self) -> Observation:
        self._services = build_services_easy()
        self._alerts = get_alerts(self.name)
        self._step_number = 0
        self._done = False
        self._timeline = [
            "2024-01-15 14:44:02 UTC — INCIDENT STARTED: user-service process terminated (OOM)",
            "2024-01-15 14:44:05 UTC — Alert fired: user-service DOWN",
            "2024-01-15 14:44:25 UTC — Alert fired: api-gateway 502 errors elevated",
            "2024-01-15 14:46:00 UTC — Alert fired: notification-service degraded",
        ]
        self._action_history = []
        self._checkpoints_hit = []
        self._cumulative_reward = 0.0
        self._last_action_result = (
            "Incident opened. Investigate the alerts and resolve the issue."
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

        # Validate service exists (except for mark_resolved)
        all_services = list(self._services.keys())
        if atype != ActionType.MARK_RESOLVED and target not in self._services:
            result_text = (
                f"Error: Service '{target}' not found. "
                f"Available services: {', '.join(all_services)}"
            )
            penalty = 0.02
            info["last_action_error"] = f"Service '{target}' not found"
            reward_val = 0.0
            self._last_action_result = result_text
            self._action_history.append(
                {"action_type": atype.value, "target_service": target, "parameters": action.parameters}
            )
            return (
                self._build_observation(),
                Reward(value=reward_val, reason=f"Invalid action: {info['last_action_error']}"),
                self._done,
                info,
            )

        # --- Dispatch ---
        if atype == ActionType.CHECK_LOGS:
            result_text = format_logs(self.name, target)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            self._timeline.append(f"{ts} — Agent checked logs for {target}")

        elif atype == ActionType.QUERY_METRICS:
            metric_type = action.parameters.get("metric_type", "cpu")
            result_text = format_metrics(self.name, target, metric_type)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            self._timeline.append(f"{ts} — Agent queried {metric_type} metrics for {target}")

        elif atype == ActionType.RESTART_SERVICE:
            svc = self._services[target]
            result_text = svc.restart()
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            self._timeline.append(f"{ts} — Agent restarted {target} → {svc.status}")
            # If user-service restarted, downstream services recover
            if target == "user-service" and svc.status == "healthy":
                self._services["api-gateway"].status = "healthy"
                self._services["notification-service"].status = "healthy"
                # Remove alerts for these services
                self._alerts = [
                    a for a in self._alerts if a.service == "user-service"
                    and "DOWN" in a.message
                ]
                self._alerts = []  # All alerts clear on fix
            elif target != "user-service":
                # Penalize restarting wrong service
                penalty += 0.10
                result_text += f"\n[WARNING] {target} was not the root cause. This restart had no effect on the incident."

        elif atype == ActionType.ROLLBACK_DEPLOY:
            msg, success = self._services[target].rollback()
            result_text = msg
            if not success or target != "user-service":
                penalty += 0.05
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            self._timeline.append(f"{ts} — Agent rolled back deploy for {target}")

        elif atype == ActionType.SCALE_SERVICE:
            replicas = action.parameters.get("replicas", 2)
            result_text = self._services[target].scale(replicas)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            self._timeline.append(f"{ts} — Agent scaled {target} to {replicas} replicas")

        elif atype == ActionType.RUN_HEALTHCHECK:
            result_text = self._services[target].healthcheck()
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            self._timeline.append(f"{ts} — Agent ran healthcheck on {target}: {self._services[target].status}")

        elif atype == ActionType.MARK_RESOLVED:
            summary = action.parameters.get("root_cause_summary", "")
            result_text = self._handle_mark_resolved(summary)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            self._timeline.append(f"{ts} — Agent marked incident resolved: '{summary[:80]}'")

        self._last_action_result = result_text
        action_record = {
            "action_type": atype.value,
            "target_service": target,
            "parameters": action.parameters,
        }
        self._action_history.append(action_record)

        # Grade
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

        # Done if max steps reached or mark_resolved called
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
        if ("oom" in lower or "out of memory" in lower or "memory" in lower) and "user-service" in lower:
            return (
                "Incident marked RESOLVED. Root cause correctly identified: "
                "user-service OOM. Incident closed."
            )
        elif self._services["user-service"].status == "healthy":
            return (
                "Incident marked resolved. Service is healthy but root cause summary "
                "is incomplete. Please mention OOM and user-service."
            )
        else:
            return (
                "Incident marked resolved, but user-service is still DOWN. "
                "The underlying issue has not been fixed."
            )
