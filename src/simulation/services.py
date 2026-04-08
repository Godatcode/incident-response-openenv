from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


ServiceStatusLiteral = Literal["healthy", "degraded", "down", "unknown"]


class DeployRecord(BaseModel):
    version: str
    timestamp: str
    healthy: bool = True


class ServiceNode(BaseModel):
    """Internal mutable service state."""

    name: str
    status: ServiceStatusLiteral
    dependencies: list[str] = []
    replicas: int = 1
    deploy_history: list[DeployRecord] = []
    current_version: str = "v1.0.0"
    # For tasks where a specific service is the root cause
    is_root_cause: bool = False
    root_cause_type: str = ""  # "oom", "bad_deploy", "memory_leak", etc.

    def last_deploy_time(self) -> str | None:
        if self.deploy_history:
            return self.deploy_history[-1].timestamp
        return None

    def restart(self) -> str:
        """Restart service — brings it back up (unless root cause is still active)."""
        if self.status in ("down", "degraded"):
            self.status = "healthy"
            return (
                f"[{self.name}] Service restarted successfully. "
                f"Status: healthy. Replicas: {self.replicas}/{ self.replicas} running."
            )
        return f"[{self.name}] Service is already {self.status}. No action taken."

    def rollback(self) -> tuple[str, bool]:
        """Roll back to previous deploy. Returns (message, success)."""
        if len(self.deploy_history) >= 2:
            bad_deploy = self.deploy_history[-1]
            self.deploy_history = self.deploy_history[:-1]
            self.current_version = self.deploy_history[-1].version
            self.status = "healthy"
            return (
                f"[{self.name}] Rollback from {bad_deploy.version} to "
                f"{self.current_version} completed. Service recovering — "
                f"error rate dropping to baseline.",
                True,
            )
        return f"[{self.name}] No previous deploy found. Cannot rollback.", False

    def scale(self, replicas: int) -> str:
        """Scale service to N replicas."""
        old = self.replicas
        self.replicas = replicas
        if self.status == "degraded":
            self.status = "healthy"
            return (
                f"[{self.name}] Scaled from {old} to {replicas} replicas. "
                f"Memory pressure per instance reduced. Status transitioning to healthy."
            )
        return (
            f"[{self.name}] Scaled from {old} to {replicas} replicas. "
            f"Load redistributed across instances."
        )

    def healthcheck(self) -> str:
        """Return healthcheck output."""
        if self.status == "healthy":
            return (
                f"[{self.name}] Health check PASSED. "
                f"HTTP 200 OK. Replicas: {self.replicas}/{self.replicas} ready. "
                f"Latency P99: normal."
            )
        elif self.status == "degraded":
            return (
                f"[{self.name}] Health check DEGRADED. "
                f"HTTP 200 OK but latency elevated. "
                f"Replicas: {self.replicas}/{self.replicas} running."
            )
        else:
            return (
                f"[{self.name}] Health check FAILED. "
                f"Connection refused. Replicas: 0/{self.replicas} ready."
            )


def build_services_easy() -> dict[str, ServiceNode]:
    """4 services for Task 1: OOM outage."""
    return {
        "api-gateway": ServiceNode(
            name="api-gateway",
            status="degraded",
            dependencies=[],
            replicas=2,
            current_version="v3.1.0",
            deploy_history=[
                DeployRecord(version="v3.0.0", timestamp="2024-01-15 08:00:00 UTC"),
                DeployRecord(version="v3.1.0", timestamp="2024-01-15 10:30:00 UTC"),
            ],
        ),
        "user-service": ServiceNode(
            name="user-service",
            status="down",
            dependencies=[],
            replicas=1,
            current_version="v2.4.1",
            is_root_cause=True,
            root_cause_type="oom",
            deploy_history=[
                DeployRecord(version="v2.4.0", timestamp="2024-01-14 16:00:00 UTC"),
                DeployRecord(version="v2.4.1", timestamp="2024-01-15 09:00:00 UTC"),
            ],
        ),
        "payment-service": ServiceNode(
            name="payment-service",
            status="healthy",
            dependencies=[],
            replicas=2,
            current_version="v1.8.3",
            deploy_history=[
                DeployRecord(version="v1.8.3", timestamp="2024-01-13 14:00:00 UTC"),
            ],
        ),
        "notification-service": ServiceNode(
            name="notification-service",
            status="degraded",
            dependencies=["user-service"],
            replicas=1,
            current_version="v1.2.0",
            deploy_history=[
                DeployRecord(version="v1.2.0", timestamp="2024-01-10 11:00:00 UTC"),
            ],
        ),
    }


def build_services_medium() -> dict[str, ServiceNode]:
    """6 services for Task 2: Bad deploy."""
    return {
        "api-gateway": ServiceNode(
            name="api-gateway",
            status="degraded",
            dependencies=[],
            replicas=3,
            current_version="v4.2.0",
            deploy_history=[
                DeployRecord(version="v4.2.0", timestamp="2024-01-15 09:00:00 UTC"),
            ],
        ),
        "auth-service": ServiceNode(
            name="auth-service",
            status="healthy",
            dependencies=[],
            replicas=2,
            current_version="v2.1.1",
            deploy_history=[
                DeployRecord(version="v2.1.1", timestamp="2024-01-15 11:00:00 UTC"),
            ],
        ),
        "order-service": ServiceNode(
            name="order-service",
            status="degraded",
            dependencies=["inventory-service", "cache-layer"],
            replicas=2,
            current_version="v2.3.1",
            is_root_cause=True,
            root_cause_type="bad_deploy",
            deploy_history=[
                DeployRecord(
                    version="v2.3.0",
                    timestamp="2024-01-15 08:00:00 UTC",
                    healthy=True,
                ),
                DeployRecord(
                    version="v2.3.1",
                    timestamp="2024-01-15 14:50:00 UTC",
                    healthy=False,
                ),
            ],
        ),
        "inventory-service": ServiceNode(
            name="inventory-service",
            status="degraded",
            dependencies=[],
            replicas=2,
            current_version="v1.5.2",
            deploy_history=[
                DeployRecord(version="v1.5.2", timestamp="2024-01-14 10:00:00 UTC"),
            ],
        ),
        "search-service": ServiceNode(
            name="search-service",
            status="healthy",
            dependencies=["cache-layer"],
            replicas=2,
            current_version="v3.0.0",
            deploy_history=[
                DeployRecord(version="v3.0.0", timestamp="2024-01-12 09:00:00 UTC"),
            ],
        ),
        "cache-layer": ServiceNode(
            name="cache-layer",
            status="healthy",
            dependencies=[],
            replicas=1,
            current_version="v1.1.0",
            deploy_history=[
                DeployRecord(version="v1.1.0", timestamp="2024-01-08 12:00:00 UTC"),
            ],
        ),
    }


def build_services_hard() -> dict[str, ServiceNode]:
    """8 services for Task 3: Phantom memory leak."""
    return {
        "api-gateway": ServiceNode(
            name="api-gateway",
            status="degraded",
            dependencies=[],
            replicas=3,
            current_version="v4.2.0",
            deploy_history=[
                DeployRecord(version="v4.2.0", timestamp="2024-01-15 06:00:00 UTC"),
            ],
        ),
        "auth-service": ServiceNode(
            name="auth-service",
            status="healthy",
            dependencies=[],
            replicas=2,
            current_version="v2.1.2",
            deploy_history=[
                DeployRecord(version="v2.1.1", timestamp="2024-01-15 09:00:00 UTC"),
                DeployRecord(version="v2.1.2", timestamp="2024-01-15 13:00:00 UTC"),
            ],
        ),
        "user-service": ServiceNode(
            name="user-service",
            status="healthy",
            dependencies=["cache-layer"],
            replicas=2,
            current_version="v2.5.0",
            deploy_history=[
                DeployRecord(version="v2.5.0", timestamp="2024-01-14 16:00:00 UTC"),
            ],
        ),
        "order-service": ServiceNode(
            name="order-service",
            status="degraded",
            dependencies=["cache-layer", "payment-service"],
            replicas=2,
            current_version="v2.4.0",
            deploy_history=[
                DeployRecord(version="v2.4.0", timestamp="2024-01-15 07:00:00 UTC"),
            ],
        ),
        "payment-service": ServiceNode(
            name="payment-service",
            status="degraded",
            dependencies=["cache-layer"],
            replicas=2,
            current_version="v1.9.0",
            deploy_history=[
                DeployRecord(version="v1.9.0", timestamp="2024-01-13 15:00:00 UTC"),
            ],
        ),
        "notification-service": ServiceNode(
            name="notification-service",
            status="healthy",
            dependencies=[],
            replicas=1,
            current_version="v1.3.0",
            deploy_history=[
                DeployRecord(version="v1.3.0", timestamp="2024-01-12 11:00:00 UTC"),
            ],
        ),
        "analytics-service": ServiceNode(
            name="analytics-service",
            status="healthy",
            dependencies=[],
            replicas=1,
            current_version="v2.0.1",
            deploy_history=[
                DeployRecord(version="v2.0.1", timestamp="2024-01-10 09:00:00 UTC"),
            ],
        ),
        "cache-layer": ServiceNode(
            name="cache-layer",
            status="degraded",
            dependencies=[],
            replicas=1,
            current_version="v1.1.0",
            is_root_cause=True,
            root_cause_type="memory_leak",
            deploy_history=[
                DeployRecord(version="v1.1.0", timestamp="2024-01-08 12:00:00 UTC"),
            ],
        ),
    }
