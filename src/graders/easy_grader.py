"""Grader for Task 1: Easy OOM Outage."""

from __future__ import annotations

from src.graders.base import BaseGrader


class EasyGrader(BaseGrader):
    """
    Checkpoints:
      checked_affected_logs    +0.15  — checked logs of user-service
      identified_oom           +0.15  — queried memory metrics OR checked logs (OOM seen)
      restarted_correct        +0.30  — restarted user-service
      healthcheck_passed       +0.15  — ran healthcheck on user-service after restart
      marked_resolved_correct  +0.24  — marked resolved with OOM + user-service in summary
    Penalties:
      restart_wrong_service    -0.10  per wrong restart
      random_actions           -0.05  per clearly irrelevant action
    """

    _CHECKPOINTS = {
        "checked_affected_logs": 0.15,
        "identified_oom": 0.15,
        "restarted_correct": 0.30,
        "healthcheck_passed": 0.15,
        "marked_resolved_correct": 0.24,
    }

    def get_checkpoints(self) -> dict[str, float]:
        return dict(self._CHECKPOINTS)

    def evaluate_checkpoints(
        self,
        action_history: list[dict],
        services: dict,
        latest_action: dict,
    ) -> list[str]:
        """Return the full list of checkpoints currently achieved."""
        hit = []
        atype = latest_action.get("action_type", "")
        target = latest_action.get("target_service", "")

        # Build cumulative history sets for detection
        all_check_logs_targets = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "check_logs"
        }
        all_query_memory_targets = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "query_metrics"
            and a.get("parameters", {}).get("metric_type", "") == "memory"
        }
        all_restarted = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "restart_service"
        }
        all_healthchecked = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "run_healthcheck"
        }
        all_mark_resolved = [
            a for a in action_history if a["action_type"] == "mark_resolved"
        ]

        # Checkpoint 1: checked logs of affected service
        if "user-service" in all_check_logs_targets:
            hit.append("checked_affected_logs")

        # Checkpoint 2: identified OOM (via logs check or memory metrics)
        if (
            "user-service" in all_check_logs_targets
            or "user-service" in all_query_memory_targets
        ):
            hit.append("identified_oom")

        # Checkpoint 3: restarted correct service
        if "user-service" in all_restarted:
            hit.append("restarted_correct")

        # Checkpoint 4: healthcheck passed after restart
        restart_seen = any(
            a["action_type"] == "restart_service" and a["target_service"] == "user-service"
            for a in action_history
        )
        if restart_seen and "user-service" in all_healthchecked:
            # Check healthcheck came AFTER restart
            restart_idx = next(
                i for i, a in enumerate(action_history)
                if a["action_type"] == "restart_service" and a["target_service"] == "user-service"
            )
            healthcheck_after = any(
                a["action_type"] == "run_healthcheck" and a["target_service"] == "user-service"
                for a in action_history[restart_idx + 1:]
            )
            if healthcheck_after:
                hit.append("healthcheck_passed")

        # Checkpoint 5: marked resolved with correct root cause
        for mr in all_mark_resolved:
            summary = mr.get("parameters", {}).get("root_cause_summary", "").lower()
            if ("oom" in summary or "out of memory" in summary or "memory" in summary) and (
                "user-service" in summary or "user service" in summary
            ):
                hit.append("marked_resolved_correct")
                break

        return hit

    def grade(self, action_history: list[dict], state: dict) -> float:
        """Compute total score strictly within (0, 1)."""
        services = state.get("services", {})
        if not action_history:
            return 0.01
        latest = action_history[-1]
        checkpoints = self.evaluate_checkpoints(action_history, services, latest)
        score = sum(self._CHECKPOINTS.get(c, 0.0) for c in checkpoints)
        return min(0.99, max(0.01, score))
