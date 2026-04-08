"""Grader for Task 3: Hard Phantom (cache-layer memory leak)."""

from __future__ import annotations

from src.graders.base import BaseGrader


class HardGrader(BaseGrader):
    """
    Checkpoints:
      investigated_3_services    +0.05  — investigated ≥3 distinct services
      identified_cache_dependency+0.10  — checked cache-layer (common dependency)
      queried_cache_memory       +0.15  — queried memory metrics for cache-layer
      checked_cache_logs         +0.15  — checked cache-layer logs (finds GC pauses)
      correlated_gc_latency      +0.10  — queried latency on ≥2 affected services + cache memory
      scaled_cache               +0.20  — scaled cache-layer (correct mitigation)
      did_not_restart_cache      +0.05  — bonus if cache was never restarted
      healthcheck_after_scale    +0.05  — ran healthcheck after scaling
      marked_resolved_correct    +0.15  — resolution mentions memory leak/GC + cache-layer
    Penalties:
      restarted_cache_layer      -0.20  — worst possible action (thundering herd)
      rolled_back_auth_service   -0.10  — chasing red herring
      random_actions             -0.05  — very irrelevant actions
    """

    _CHECKPOINTS = {
        "investigated_3_services": 0.05,
        "identified_cache_dependency": 0.10,
        "queried_cache_memory": 0.15,
        "checked_cache_logs": 0.15,
        "correlated_gc_latency": 0.10,
        "scaled_cache": 0.20,
        "did_not_restart_cache": 0.05,
        "healthcheck_after_scale": 0.05,
        "marked_resolved_correct": 0.15,
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

        investigated = {
            a["target_service"]
            for a in action_history
            if a["action_type"] in ("check_logs", "query_metrics", "run_healthcheck")
        }
        checked_logs = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "check_logs"
        }
        queried_metrics = {
            (a["target_service"], a.get("parameters", {}).get("metric_type", ""))
            for a in action_history
            if a["action_type"] == "query_metrics"
        }
        scaled = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "scale_service"
        }
        restarted = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "restart_service"
        }
        rolled_back = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "rollback_deploy"
        }
        healthchecked = {
            a["target_service"]
            for a in action_history
            if a["action_type"] == "run_healthcheck"
        }
        mark_resolved_list = [
            a for a in action_history if a["action_type"] == "mark_resolved"
        ]

        # Checkpoint 1: investigated ≥3 services
        if len(investigated) >= 3:
            hit.append("investigated_3_services")

        # Checkpoint 2: identified cache-layer as common dependency (checked it)
        if "cache-layer" in investigated:
            hit.append("identified_cache_dependency")

        # Checkpoint 3: queried cache-layer memory metrics
        if ("cache-layer", "memory") in queried_metrics:
            hit.append("queried_cache_memory")

        # Checkpoint 4: checked cache-layer logs
        if "cache-layer" in checked_logs:
            hit.append("checked_cache_logs")

        # Checkpoint 5: correlated GC with downstream latency
        # (queried latency on ≥2 affected services AND queried cache memory or checked cache logs)
        latency_queries = {
            svc
            for svc, metric in queried_metrics
            if metric in ("latency", "latency_p99_ms")
        }
        affected = {"api-gateway", "order-service", "payment-service"}
        cache_investigated = (
            "cache-layer" in checked_logs
            or ("cache-layer", "memory") in queried_metrics
        )
        if len(latency_queries & affected) >= 2 and cache_investigated:
            hit.append("correlated_gc_latency")

        # Checkpoint 6: scaled cache-layer
        if "cache-layer" in scaled:
            hit.append("scaled_cache")

        # Checkpoint 7: did NOT restart cache-layer
        if "cache-layer" not in restarted:
            hit.append("did_not_restart_cache")

        # Checkpoint 8: healthcheck after scaling
        scale_idx = next(
            (
                i for i, a in enumerate(action_history)
                if a["action_type"] == "scale_service" and a["target_service"] == "cache-layer"
            ),
            None,
        )
        if scale_idx is not None:
            post_scale = action_history[scale_idx + 1:]
            if any(a["action_type"] == "run_healthcheck" for a in post_scale):
                hit.append("healthcheck_after_scale")

        # Checkpoint 9: correct resolution summary
        for mr in mark_resolved_list:
            summary = mr.get("parameters", {}).get("root_cause_summary", "").lower()
            cache_ok = "cache" in summary or "cache-layer" in summary
            cause_ok = (
                "memory" in summary or "leak" in summary
                or "gc" in summary or "garbage" in summary or "pause" in summary
            )
            if cache_ok and cause_ok:
                hit.append("marked_resolved_correct")
                break

        return hit

    def grade(self, action_history: list[dict], state: dict) -> float:
        services = state.get("services", {})
        if not action_history:
            return 0.0
        latest = action_history[-1]
        checkpoints = self.evaluate_checkpoints(action_history, services, latest)
        score = sum(self._CHECKPOINTS.get(c, 0.0) for c in checkpoints)
        return min(1.0, max(0.0, score))
