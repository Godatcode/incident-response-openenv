"""Tests for grader checkpoint logic."""

import pytest

from src.graders.easy_grader import EasyGrader
from src.graders.hard_grader import HardGrader
from src.graders.medium_grader import MediumGrader


# ---------------------------------------------------------------------------
# Easy Grader Tests
# ---------------------------------------------------------------------------


class TestEasyGrader:
    def setup_method(self):
        self.grader = EasyGrader()

    def _action(self, atype, target="", params=None):
        return {"action_type": atype, "target_service": target, "parameters": params or {}}

    def test_empty_history_yields_no_checkpoints(self):
        result = self.grader.evaluate_checkpoints([], {}, self._action("check_logs", "api-gateway"))
        assert result == []

    def test_check_logs_user_service_hits_checkpoint(self):
        history = [self._action("check_logs", "user-service")]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "checked_affected_logs" in result
        assert "identified_oom" in result

    def test_restart_user_service_hits_checkpoint(self):
        history = [
            self._action("check_logs", "user-service"),
            self._action("restart_service", "user-service"),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "restarted_correct" in result

    def test_healthcheck_after_restart_hits_checkpoint(self):
        history = [
            self._action("check_logs", "user-service"),
            self._action("restart_service", "user-service"),
            self._action("run_healthcheck", "user-service"),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "healthcheck_passed" in result

    def test_healthcheck_before_restart_does_not_hit_checkpoint(self):
        history = [
            self._action("run_healthcheck", "user-service"),
            self._action("restart_service", "user-service"),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        # Healthcheck was BEFORE restart — should not count
        assert "healthcheck_passed" not in result

    def test_correct_mark_resolved_hits_checkpoint(self):
        history = [
            self._action(
                "mark_resolved",
                params={"root_cause_summary": "user-service OOM caused downtime"},
            )
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "marked_resolved_correct" in result

    def test_incorrect_mark_resolved_does_not_hit(self):
        history = [
            self._action(
                "mark_resolved",
                params={"root_cause_summary": "network issue"},
            )
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "marked_resolved_correct" not in result

    def test_full_optimal_solution_max_score(self):
        history = [
            self._action("check_logs", "user-service"),
            self._action("restart_service", "user-service"),
            self._action("run_healthcheck", "user-service"),
            self._action(
                "mark_resolved",
                params={"root_cause_summary": "user-service OOM crash, restarted"},
            ),
        ]
        checkpoints = self.grader.evaluate_checkpoints(history, {}, history[-1])
        score = sum(self.grader.get_checkpoints().get(c, 0) for c in checkpoints)
        assert score == pytest.approx(1.0)

    def test_checkpoint_weights_sum_to_one(self):
        total = sum(self.grader.get_checkpoints().values())
        assert total == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Medium Grader Tests
# ---------------------------------------------------------------------------


class TestMediumGrader:
    def setup_method(self):
        self.grader = MediumGrader()

    def _action(self, atype, target="", params=None):
        return {"action_type": atype, "target_service": target, "parameters": params or {}}

    def test_checkpoint_weights_sum_to_one(self):
        total = sum(self.grader.get_checkpoints().values())
        assert total == pytest.approx(1.0)

    def test_investigating_multiple_services_hits_checkpoint(self):
        history = [
            self._action("check_logs", "order-service"),
            self._action("check_logs", "inventory-service"),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "investigated_multiple" in result

    def test_single_service_does_not_hit_multiple_checkpoint(self):
        history = [self._action("check_logs", "order-service")]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "investigated_multiple" not in result

    def test_avoided_red_herring_by_default(self):
        history = [self._action("check_logs", "order-service")]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "avoided_red_herring" in result

    def test_touching_search_service_loses_red_herring_bonus(self):
        history = [
            self._action("check_logs", "order-service"),
            self._action("rollback_deploy", "search-service"),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "avoided_red_herring" not in result

    def test_rollback_order_service_hits_checkpoint(self):
        history = [
            self._action("check_logs", "order-service"),
            self._action("check_logs", "inventory-service"),
            self._action("rollback_deploy", "order-service"),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "rolled_back_order" in result

    def test_verified_downstream_after_rollback(self):
        history = [
            self._action("check_logs", "order-service"),
            self._action("check_logs", "inventory-service"),
            self._action("rollback_deploy", "order-service"),
            self._action("run_healthcheck", "inventory-service"),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "verified_downstream" in result

    def test_correct_resolution_summary(self):
        history = [
            self._action(
                "mark_resolved",
                params={"root_cause_summary": "bad deploy on order-service, rolled back v2.3.1"},
            )
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "marked_resolved_correct" in result


# ---------------------------------------------------------------------------
# Hard Grader Tests
# ---------------------------------------------------------------------------


class TestHardGrader:
    def setup_method(self):
        self.grader = HardGrader()

    def _action(self, atype, target="", params=None):
        return {"action_type": atype, "target_service": target, "parameters": params or {}}

    def test_checkpoint_weights_sum_to_one(self):
        total = sum(self.grader.get_checkpoints().values())
        assert total == pytest.approx(1.0)

    def test_investigating_3_services_hits_checkpoint(self):
        history = [
            self._action("check_logs", "api-gateway"),
            self._action("check_logs", "order-service"),
            self._action("check_logs", "payment-service"),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "investigated_3_services" in result

    def test_checking_cache_layer_hits_dependency_checkpoint(self):
        history = [self._action("check_logs", "cache-layer")]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "identified_cache_dependency" in result

    def test_querying_cache_memory_hits_checkpoint(self):
        history = [
            self._action("query_metrics", "cache-layer", {"metric_type": "memory"})
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "queried_cache_memory" in result

    def test_checking_cache_logs_hits_checkpoint(self):
        history = [self._action("check_logs", "cache-layer")]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "checked_cache_logs" in result

    def test_did_not_restart_cache_by_default(self):
        history = [self._action("check_logs", "api-gateway")]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "did_not_restart_cache" in result

    def test_restarting_cache_loses_bonus(self):
        history = [self._action("restart_service", "cache-layer")]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "did_not_restart_cache" not in result

    def test_scale_cache_hits_checkpoint(self):
        history = [
            self._action("scale_service", "cache-layer", {"replicas": 3})
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "scaled_cache" in result

    def test_healthcheck_after_scale_hits_checkpoint(self):
        history = [
            self._action("scale_service", "cache-layer", {"replicas": 3}),
            self._action("run_healthcheck", "cache-layer"),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "healthcheck_after_scale" in result

    def test_correct_resolution_mentions_cache_and_gc(self):
        history = [
            self._action(
                "mark_resolved",
                params={
                    "root_cause_summary": (
                        "cache-layer memory leak causing GC pauses and downstream latency"
                    )
                },
            )
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "marked_resolved_correct" in result

    def test_incomplete_resolution_no_checkpoint(self):
        history = [
            self._action(
                "mark_resolved",
                params={"root_cause_summary": "latency issue in api-gateway"},
            )
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "marked_resolved_correct" not in result

    def test_correlated_gc_latency_checkpoint(self):
        history = [
            self._action("query_metrics", "api-gateway", {"metric_type": "latency"}),
            self._action("query_metrics", "order-service", {"metric_type": "latency"}),
            self._action("query_metrics", "cache-layer", {"metric_type": "memory"}),
        ]
        result = self.grader.evaluate_checkpoints(history, {}, history[-1])
        assert "correlated_gc_latency" in result

    def test_delta_reward_computation(self):
        prev = []
        new = ["investigated_3_services", "identified_cache_dependency"]
        delta, newly_hit, reason = self.grader.compute_delta_reward(prev, new, 0.0)
        assert delta == pytest.approx(0.05 + 0.10)
        assert set(newly_hit) == {"investigated_3_services", "identified_cache_dependency"}

    def test_delta_reward_with_penalty(self):
        prev = []
        new = ["investigated_3_services"]
        delta, _, _ = self.grader.compute_delta_reward(prev, new, 0.20)
        assert delta == pytest.approx(0.05 - 0.20)
