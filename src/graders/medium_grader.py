"""Grader for Task 2: Medium Bad Deploy."""

from __future__ import annotations

from src.graders.base import BaseGrader


class MediumGrader(BaseGrader):
    """
    Checkpoints:
      investigated_multiple     +0.10  — checked logs/metrics for ≥2 distinct services
      correlated_deploy_timing  +0.15  — checked order-service logs (sees deploy timestamp)
      avoided_red_herring       +0.10  — never rolled back / restarted search-service
      rolled_back_order         +0.25  — rolled back order-service
      verified_downstream       +0.15  — ran healthcheck or checked inventory-service after rollback
      marked_resolved_correct   +0.24  — resolution mentions deploy + order-service
    Penalties:
      rollback_wrong_service    -0.15  per wrong rollback
      restart_instead_rollback  -0.05  restarted order-service instead of rollback
    """

    _CHECKPOINTS = {
        "investigated_multiple": 0.10,
        "correlated_deploy_timing": 0.15,
        "avoided_red_herring": 0.10,
        "rolled_back_order": 0.25,
        "verified_downstream": 0.15,
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
        hit = []

        investigated_services = {
            a["target_service"]
            for a in action_history
            if a["action_type"] in ("check_logs", "query_metrics")
        }
        rolled_back = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "rollback_deploy"
        }
        restarted = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "restart_service"
        }
        healthchecked = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "run_healthcheck"
        }
        checked_logs = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "check_logs"
        }
        mark_resolved_list = [
            a for a in action_history if a["action_type"] == "mark_resolved"
        ]

        # Checkpoint 1: investigated multiple services (≥2)
        if len(investigated_services) >= 2:
            hit.append("investigated_multiple")

        # Checkpoint 2: checked order-service logs (correlated deploy timing)
        if "order-service" in checked_logs:
            hit.append("correlated_deploy_timing")

        # Checkpoint 3: avoided red herring — never took action on search-service
        red_herring_touched = (
            "search-service" in rolled_back or "search-service" in restarted
        )
        if not red_herring_touched:
            hit.append("avoided_red_herring")

        # Checkpoint 4: rolled back order-service
        if "order-service" in rolled_back:
            hit.append("rolled_back_order")

        # Checkpoint 5: verified downstream recovery after rollback
        rollback_idx = next(
            (
                i for i, a in enumerate(action_history)
                if a["action_type"] == "rollback_deploy" and a["target_service"] == "order-service"
            ),
            None,
        )
        if rollback_idx is not None:
            post_rollback = action_history[rollback_idx + 1:]
            downstream_verified = any(
                a["target_service"] in ("inventory-service", "api-gateway", "order-service")
                and a["action_type"] in ("run_healthcheck", "check_logs", "query_metrics")
                for a in post_rollback
            )
            if downstream_verified:
                hit.append("verified_downstream")

        # Checkpoint 6: correct resolution summary
        for mr in mark_resolved_list:
            summary = mr.get("parameters", {}).get("root_cause_summary", "").lower()
            if ("deploy" in summary or "rollback" in summary or "v2.3" in summary) and (
                "order-service" in summary or "order service" in summary
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
