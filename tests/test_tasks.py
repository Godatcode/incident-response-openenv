"""Tests for each task — scenario correctness and state transitions."""

import pytest

from src.models import Action, ActionType
from src.tasks.easy_oom_outage import EasyOomOutageTask
from src.tasks.hard_phantom import HardPhantomTask
from src.tasks.medium_bad_deploy import MediumBadDeployTask


# ---------------------------------------------------------------------------
# Easy Task Tests
# ---------------------------------------------------------------------------


class TestEasyOomOutage:
    def setup_method(self):
        self.task = EasyOomOutageTask()
        self.task.reset()

    def test_initial_state_has_critical_alert(self):
        obs = self.task.reset()
        critical = [a for a in obs.active_alerts if a.severity == "critical"]
        assert len(critical) >= 1
        assert any("user-service" in a.service for a in critical)

    def test_user_service_initially_down(self):
        obs = self.task.reset()
        user_svc = next(s for s in obs.service_statuses if s.name == "user-service")
        assert user_svc.status == "down"

    def test_check_logs_user_service_shows_oom(self):
        obs, reward, done, info = self.task.step(
            Action(action_type=ActionType.CHECK_LOGS, target_service="user-service")
        )
        assert "OutOfMemoryError" in obs.last_action_result or "OOM" in obs.last_action_result
        assert reward.value >= 0

    def test_restart_user_service_fixes_it(self):
        self.task.step(Action(action_type=ActionType.CHECK_LOGS, target_service="user-service"))
        obs, reward, done, info = self.task.step(
            Action(action_type=ActionType.RESTART_SERVICE, target_service="user-service")
        )
        user_svc = next(s for s in obs.service_statuses if s.name == "user-service")
        assert user_svc.status == "healthy"
        assert reward.value > 0

    def test_restart_wrong_service_penalized(self):
        obs, reward, done, info = self.task.step(
            Action(action_type=ActionType.RESTART_SERVICE, target_service="payment-service")
        )
        assert reward.value == 0.0

    def test_correct_full_solution(self):
        """Full optimal solution should yield high cumulative reward."""
        self.task.reset()
        self.task.step(Action(action_type=ActionType.CHECK_LOGS, target_service="user-service"))
        self.task.step(Action(action_type=ActionType.RESTART_SERVICE, target_service="user-service"))
        self.task.step(Action(action_type=ActionType.RUN_HEALTHCHECK, target_service="user-service"))
        _, _, done, _ = self.task.step(
            Action(
                action_type=ActionType.MARK_RESOLVED,
                parameters={"root_cause_summary": "user-service crashed due to OOM, restarted"},
            )
        )
        assert done is True
        state = self.task.get_state()
        assert state.cumulative_reward >= 0.85

    def test_max_steps_terminates(self):
        self.task.reset()
        done = False
        steps = 0
        while not done and steps < 20:
            _, _, done, _ = self.task.step(
                Action(action_type=ActionType.CHECK_LOGS, target_service="api-gateway")
            )
            steps += 1
        assert done is True
        assert steps <= self.task.max_steps


# ---------------------------------------------------------------------------
# Medium Task Tests
# ---------------------------------------------------------------------------


class TestMediumBadDeploy:
    def setup_method(self):
        self.task = MediumBadDeployTask()
        self.task.reset()

    def test_initial_alerts_include_order_service(self):
        obs = self.task.reset()
        services_in_alerts = {a.service for a in obs.active_alerts}
        assert "order-service" in services_in_alerts

    def test_search_service_alert_is_red_herring(self):
        """search-service alert is WARNING, CPU spike from reindex."""
        obs = self.task.reset()
        search_alerts = [a for a in obs.active_alerts if a.service == "search-service"]
        assert all(a.severity == "warning" for a in search_alerts)

    def test_order_service_logs_show_deploy_and_npe(self):
        obs, _, _, _ = self.task.step(
            Action(action_type=ActionType.CHECK_LOGS, target_service="order-service")
        )
        result = obs.last_action_result
        assert "NullPointerException" in result or "Deploy" in result

    def test_rollback_order_service_fixes_incident(self):
        self.task.step(Action(action_type=ActionType.CHECK_LOGS, target_service="order-service"))
        obs, reward, done, _ = self.task.step(
            Action(action_type=ActionType.ROLLBACK_DEPLOY, target_service="order-service")
        )
        order_svc = next(s for s in obs.service_statuses if s.name == "order-service")
        assert order_svc.status == "healthy"
        assert reward.value > 0

    def test_restart_order_service_does_not_fix(self):
        """Restart without rollback should not fix bad deploy."""
        obs, reward, _, _ = self.task.step(
            Action(action_type=ActionType.RESTART_SERVICE, target_service="order-service")
        )
        order_svc = next(s for s in obs.service_statuses if s.name == "order-service")
        # Still degraded — code is broken
        assert order_svc.status == "degraded"

    def test_rollback_search_service_penalized(self):
        _, reward, _, _ = self.task.step(
            Action(action_type=ActionType.ROLLBACK_DEPLOY, target_service="search-service")
        )
        assert reward.value == 0.0

    def test_correct_full_solution(self):
        self.task.reset()
        self.task.step(Action(action_type=ActionType.CHECK_LOGS, target_service="order-service"))
        self.task.step(Action(action_type=ActionType.CHECK_LOGS, target_service="inventory-service"))
        self.task.step(Action(action_type=ActionType.ROLLBACK_DEPLOY, target_service="order-service"))
        self.task.step(Action(action_type=ActionType.RUN_HEALTHCHECK, target_service="inventory-service"))
        _, _, done, _ = self.task.step(
            Action(
                action_type=ActionType.MARK_RESOLVED,
                parameters={
                    "root_cause_summary": "bad deploy v2.3.1 on order-service caused 500s, rolled back"
                },
            )
        )
        assert done is True
        state = self.task.get_state()
        assert state.cumulative_reward >= 0.80


# ---------------------------------------------------------------------------
# Hard Task Tests
# ---------------------------------------------------------------------------


class TestHardPhantom:
    def setup_method(self):
        self.task = HardPhantomTask()
        self.task.reset()

    def test_initial_alerts_all_warnings_no_critical(self):
        obs = self.task.reset()
        critical = [a for a in obs.active_alerts if a.severity == "critical"]
        assert len(critical) == 0  # All intermittent — no hard down

    def test_cache_layer_not_in_initial_alerts(self):
        """Cache-layer is the root cause but doesn't appear in alerts."""
        obs = self.task.reset()
        cache_alerts = [a for a in obs.active_alerts if a.service == "cache-layer"]
        assert len(cache_alerts) == 0

    def test_cache_layer_logs_show_gc_pauses(self):
        obs, _, _, _ = self.task.step(
            Action(action_type=ActionType.CHECK_LOGS, target_service="cache-layer")
        )
        result = obs.last_action_result
        assert "GC pause" in result or "GC" in result

    def test_cache_layer_memory_metrics_show_leak(self):
        obs, _, _, _ = self.task.step(
            Action(
                action_type=ActionType.QUERY_METRICS,
                target_service="cache-layer",
                parameters={"metric_type": "memory"},
            )
        )
        result = obs.last_action_result
        # Memory should be showing high and climbing values
        assert "MB" in result
        assert "3" in result  # 3xxx MB values

    def test_restart_cache_layer_penalized_heavily(self):
        _, reward, _, _ = self.task.step(
            Action(action_type=ActionType.RESTART_SERVICE, target_service="cache-layer")
        )
        assert reward.value == 0.0

    def test_scale_cache_layer_fixes_incident(self):
        obs, reward, _, _ = self.task.step(
            Action(
                action_type=ActionType.SCALE_SERVICE,
                target_service="cache-layer",
                parameters={"replicas": 3},
            )
        )
        cache_svc = next(s for s in obs.service_statuses if s.name == "cache-layer")
        assert cache_svc.replicas == 3
        assert reward.value > 0

    def test_rollback_auth_service_penalized(self):
        """auth-service config change is a red herring."""
        _, reward, _, _ = self.task.step(
            Action(action_type=ActionType.ROLLBACK_DEPLOY, target_service="auth-service")
        )
        assert reward.value == 0.0

    def test_correct_full_solution(self):
        self.task.reset()
        self.task.step(Action(action_type=ActionType.CHECK_LOGS, target_service="api-gateway"))
        self.task.step(Action(action_type=ActionType.CHECK_LOGS, target_service="order-service"))
        self.task.step(Action(action_type=ActionType.CHECK_LOGS, target_service="payment-service"))
        self.task.step(
            Action(
                action_type=ActionType.QUERY_METRICS,
                target_service="cache-layer",
                parameters={"metric_type": "memory"},
            )
        )
        self.task.step(Action(action_type=ActionType.CHECK_LOGS, target_service="cache-layer"))
        self.task.step(
            Action(
                action_type=ActionType.SCALE_SERVICE,
                target_service="cache-layer",
                parameters={"replicas": 3},
            )
        )
        self.task.step(Action(action_type=ActionType.RUN_HEALTHCHECK, target_service="cache-layer"))
        _, _, done, _ = self.task.step(
            Action(
                action_type=ActionType.MARK_RESOLVED,
                parameters={
                    "root_cause_summary": (
                        "cache-layer memory leak causing GC pauses, "
                        "affecting downstream latency. Scaled horizontally."
                    )
                },
            )
        )
        assert done is True
        state = self.task.get_state()
        assert state.cumulative_reward >= 0.85
