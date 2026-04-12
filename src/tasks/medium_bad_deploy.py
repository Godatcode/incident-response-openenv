"""Task 2: The Bad Deploy — order-service v2.3.1 causing 500s."""

from __future__ import annotations

from datetime import datetime, timezone

from src.graders.medium_grader import MediumGrader
from src.models import Action, ActionType, Observation, Reward, ServiceStatus, State
from src.simulation.alerts import get_alerts
from src.simulation.logs import format_logs
from src.simulation.metrics import format_metrics
from src.simulation.services import ServiceNode, build_services_medium
from src.tasks.base import BaseTask

_DEPENDENCY_GRAPH = {
    "api-gateway": ["auth-service", "order-service", "search-service"],
    "auth-service": [],
    "order-service": ["inventory-service", "cache-layer"],
    "inventory-service": [],
    "search-service": ["cache-layer"],
    "cache-layer": [],
}


class MediumBadDeployTask(BaseTask):
    name = "medium_bad_deploy"
    max_steps = 15
    dependency_graph = _DEPENDENCY_GRAPH
    ground_truth_root_cause = (
        "order-service deploy v2.3.1 introduced a NullPointerException in "
        "OrderHandler.processPayment. Rolled back to v2.3.0 to restore service. "
        "inventory-service degradation was downstream of order-service, not a separate issue. "
        "search-service CPU spike was unrelated (scheduled reindex job)."
    )
    ground_truth_affected_services = ["order-service", "inventory-service", "api-gateway"]
    ground_truth_optimal_actions = [
        "check_logs(order-service)",
        "query_metrics(order-service, error_rate)",
        "rollback_deploy(order-service)",
        "run_healthcheck(inventory-service)",
        "mark_resolved(bad deploy v2.3.1 on order-service, rolled back)",
    ]

    def __init__(self) -> None:
        self._services: dict[str, ServiceNode] = {}
        self._alerts = []
        self._step_number = 0
        self._done = False
        self._timeline: list[str] = []
        self._action_history: list[dict] = []
        self._grader = MediumGrader()
        self._checkpoints_hit: list[str] = []
        self._cumulative_reward = 0.0
        self._last_action_result = ""

    def reset(self) -> Observation:
        self._services = build_services_medium()
        self._alerts = get_alerts(self.name)
        self._step_number = 0
        self._done = False
        self._timeline = [
            "2024-01-15 14:50:00 UTC — deploy: order-service v2.3.1 rolled out",
            "2024-01-15 14:50:35 UTC — order-service error rate spiking (NullPointerException)",
            "2024-01-15 14:51:30 UTC — Alert fired: order-service error rate >50%",
            "2024-01-15 14:52:00 UTC — Alert fired: inventory-service P99 >2s",
            "2024-01-15 14:50:00 UTC — Alert fired: search-service CPU >80% (reindex job)",
        ]
        self._action_history = []
        self._checkpoints_hit = []
        self._cumulative_reward = 0.0
        self._last_action_result = (
            "Incident opened. Multiple alerts active. Investigate and resolve."
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
            result_text = svc.restart()
            self._timeline.append(f"{ts} — Agent restarted {target}")
            if target == "order-service":
                # Restart doesn't fix bad deploy — code is still broken
                svc.status = "degraded"
                result_text += (
                    "\n[WARNING] order-service restarted but errors are PERSISTING — "
                    "v2.3.1 is still deployed. The bug is in the code, not the process."
                )
                penalty += 0.05  # Penalty: restart instead of rollback
            elif target == "search-service":
                penalty += 0.15  # Penalize attacking the red herring
                result_text += (
                    "\n[WARNING] search-service was not related to the incident. "
                    "The CPU spike was from a scheduled reindex job, now aborted."
                )
            elif target == "inventory-service":
                # inventory-service restart has no lasting effect — still depends on broken order-service
                result_text += (
                    "\n[INFO] inventory-service restarted, but it will continue to "
                    "degrade because order-service (its dependency) is still broken."
                )

        elif atype == ActionType.ROLLBACK_DEPLOY:
            msg, success = self._services[target].rollback()
            result_text = msg
            self._timeline.append(f"{ts} — Agent rolled back deploy for {target}")
            if target == "order-service" and success:
                # Rollback fixes the issue — downstream recovers
                self._services["inventory-service"].status = "healthy"
                self._services["api-gateway"].status = "healthy"
                self._alerts = []
                result_text += (
                    "\n[SUCCESS] order-service v2.3.0 is stable. "
                    "inventory-service has recovered. Error rate returning to baseline."
                )
            elif target == "search-service":
                penalty += 0.15
                result_text = (
                    f"[WARNING] search-service rollback attempted. "
                    f"search-service was NOT the cause of the incident — "
                    f"its CPU was from a scheduled reindex job (normal behavior).\n" + msg
                )
            elif target != "order-service":
                penalty += 0.10

        elif atype == ActionType.SCALE_SERVICE:
            replicas = action.parameters.get("replicas", 2)
            result_text = self._services[target].scale(replicas)
            self._timeline.append(f"{ts} — Agent scaled {target} to {replicas} replicas")

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
            cumulative_reward=self._cumulative_reward,
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
        order_svc = self._services.get("order-service")
        deploy_mentioned = "deploy" in lower or "rollback" in lower or "v2.3" in lower
        service_mentioned = "order-service" in lower or "order service" in lower
        if deploy_mentioned and service_mentioned:
            if order_svc and order_svc.status == "healthy":
                return (
                    "Incident marked RESOLVED. Root cause correctly identified: "
                    "bad deploy on order-service. Incident closed."
                )
            else:
                return (
                    "Incident marked resolved, but order-service is still degraded. "
                    "The underlying deploy issue has not been fixed."
                )
        return (
            "Incident marked resolved. Root cause summary is incomplete — "
            "please mention the bad deploy and order-service."
        )
