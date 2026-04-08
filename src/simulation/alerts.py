"""Pre-generated alerts per task."""

from __future__ import annotations

from src.models import Alert


def get_alerts(task_name: str) -> list[Alert]:
    """Return the initial active alerts for a given task."""
    if task_name == "easy_oom_outage":
        return _alerts_easy()
    elif task_name == "medium_bad_deploy":
        return _alerts_medium()
    elif task_name == "hard_phantom":
        return _alerts_hard()
    else:
        return []


def _alerts_easy() -> list[Alert]:
    return [
        Alert(
            alert_id="ALERT-001",
            severity="critical",
            service="user-service",
            message="user-service is DOWN — health check failing for 12 minutes. Exit code 137 (OOM kill).",
            timestamp="2024-01-15 14:44:05 UTC",
        ),
        Alert(
            alert_id="ALERT-002",
            severity="warning",
            service="api-gateway",
            message="api-gateway error rate elevated: 42% of requests returning 502 (upstream user-service unavailable).",
            timestamp="2024-01-15 14:44:25 UTC",
        ),
        Alert(
            alert_id="ALERT-003",
            severity="warning",
            service="notification-service",
            message="notification-service degraded — cannot reach user-service for preference lookups. Queue backlog: 47 jobs.",
            timestamp="2024-01-15 14:46:00 UTC",
        ),
    ]


def _alerts_medium() -> list[Alert]:
    return [
        Alert(
            alert_id="ALERT-001",
            severity="critical",
            service="order-service",
            message="order-service error rate >50% — POST /orders/create returning HTTP 500. Started ~14:50 UTC.",
            timestamp="2024-01-15 14:51:30 UTC",
        ),
        Alert(
            alert_id="ALERT-002",
            severity="warning",
            service="inventory-service",
            message="inventory-service latency P99 >2s — downstream dependency on order-service timing out.",
            timestamp="2024-01-15 14:52:00 UTC",
        ),
        Alert(
            alert_id="ALERT-003",
            severity="warning",
            service="search-service",
            message="search-service CPU usage >80% — elevated resource consumption detected.",
            timestamp="2024-01-15 14:50:00 UTC",
        ),
    ]


def _alerts_hard() -> list[Alert]:
    return [
        Alert(
            alert_id="ALERT-001",
            severity="warning",
            service="api-gateway",
            message="api-gateway P99 latency >1s intermittently — spikes to 1.8-2.1s, then returns to normal.",
            timestamp="2024-01-15 14:30:00 UTC",
        ),
        Alert(
            alert_id="ALERT-002",
            severity="warning",
            service="order-service",
            message="order-service P99 latency >1.5s intermittently — pattern repeating every 15-20 minutes.",
            timestamp="2024-01-15 14:30:00 UTC",
        ),
        Alert(
            alert_id="ALERT-003",
            severity="warning",
            service="payment-service",
            message="payment-service P99 latency >1.2s intermittently — 3 payment transactions timed out.",
            timestamp="2024-01-15 14:45:00 UTC",
        ),
        Alert(
            alert_id="ALERT-004",
            severity="info",
            service="auth-service",
            message="auth-service config updated 2 hours ago — log level changed from INFO to DEBUG.",
            timestamp="2024-01-15 13:00:05 UTC",
        ),
        Alert(
            alert_id="ALERT-005",
            severity="info",
            service="analytics-service",
            message="analytics-service CPU at 75% — daily batch aggregation job running (scheduled, expected).",
            timestamp="2024-01-15 14:30:00 UTC",
        ),
    ]
