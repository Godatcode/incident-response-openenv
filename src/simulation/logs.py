"""Pre-generated realistic log entries per service per task."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Task 1: Easy OOM Outage
# ---------------------------------------------------------------------------

LOGS_EASY: dict[str, list[str]] = {
    "user-service": [
        "[2024-01-15 14:30:01 UTC] INFO  user-service: Application started on port 8080",
        "[2024-01-15 14:31:15 UTC] INFO  user-service: GET /api/v1/users/profile 200 45ms",
        "[2024-01-15 14:33:42 UTC] INFO  user-service: GET /api/v1/users/search 200 112ms",
        "[2024-01-15 14:35:10 UTC] INFO  user-service: POST /api/v1/users/login 200 88ms",
        "[2024-01-15 14:38:02 UTC] WARN  user-service: Heap usage at 78% — consider tuning JVM flags",
        "[2024-01-15 14:40:19 UTC] INFO  user-service: GET /api/v1/users/profile 200 53ms",
        "[2024-01-15 14:42:55 UTC] WARN  user-service: Heap usage at 87% — GC pressure increasing",
        "[2024-01-15 14:44:01 UTC] ERROR user-service: java.lang.OutOfMemoryError: Java heap space",
        "[2024-01-15 14:44:01 UTC] ERROR user-service:   at java.util.Arrays.copyOf(Arrays.java:3210)",
        "[2024-01-15 14:44:01 UTC] ERROR user-service:   at com.example.user.UserCacheManager.loadAll(UserCacheManager.java:142)",
        "[2024-01-15 14:44:01 UTC] ERROR user-service:   at com.example.user.UserService.warmCache(UserService.java:87)",
        "[2024-01-15 14:44:02 UTC] FATAL user-service: Process killed by OOM killer — kernel signal received",
        "[2024-01-15 14:44:02 UTC] FATAL user-service: Exit code 137 — container terminated (OOM)",
        "[2024-01-15 14:44:03 UTC] ERROR user-service: [supervisor] user-service exited with code 137; not restarting (max retries exceeded)",
    ],
    "api-gateway": [
        "[2024-01-15 14:30:00 UTC] INFO  api-gateway: Gateway started. Upstream services: user-service, payment-service",
        "[2024-01-15 14:31:00 UTC] INFO  api-gateway: GET /users/profile -> user-service 200 52ms",
        "[2024-01-15 14:35:00 UTC] INFO  api-gateway: GET /payments/history -> payment-service 200 34ms",
        "[2024-01-15 14:44:10 UTC] ERROR api-gateway: upstream user-service connection refused (EOF)",
        "[2024-01-15 14:44:11 UTC] ERROR api-gateway: GET /users/profile -> user-service 502 Bad Gateway",
        "[2024-01-15 14:44:15 UTC] ERROR api-gateway: upstream user-service connection timeout after 5000ms",
        "[2024-01-15 14:44:20 UTC] WARN  api-gateway: Circuit breaker for user-service OPEN — fast-failing requests",
        "[2024-01-15 14:44:25 UTC] ERROR api-gateway: GET /users/search -> user-service 502 Bad Gateway",
        "[2024-01-15 14:45:00 UTC] ERROR api-gateway: Retry attempt 3/3 to user-service — still unreachable",
        "[2024-01-15 14:50:00 UTC] INFO  api-gateway: payment-service still healthy, routing payment requests normally",
    ],
    "payment-service": [
        "[2024-01-15 14:30:00 UTC] INFO  payment-service: Service healthy. Connected to payment gateway.",
        "[2024-01-15 14:31:00 UTC] INFO  payment-service: POST /payments/charge 200 145ms",
        "[2024-01-15 14:35:00 UTC] INFO  payment-service: GET /payments/history 200 67ms",
        "[2024-01-15 14:40:00 UTC] INFO  payment-service: POST /payments/refund 200 189ms",
        "[2024-01-15 14:45:00 UTC] INFO  payment-service: Health check OK. DB pool: 8/20 active.",
        "[2024-01-15 14:48:00 UTC] INFO  payment-service: POST /payments/charge 200 133ms",
        "[2024-01-15 14:50:00 UTC] INFO  payment-service: Processed 247 transactions in last 10 minutes. Normal load.",
        "[2024-01-15 14:52:00 UTC] INFO  payment-service: POST /payments/charge 200 141ms",
        "[2024-01-15 14:55:00 UTC] INFO  payment-service: Health check OK. All systems nominal.",
    ],
    "notification-service": [
        "[2024-01-15 14:30:00 UTC] INFO  notification-service: Worker pool started (4 workers)",
        "[2024-01-15 14:31:00 UTC] INFO  notification-service: Sent email notification to user_id=4821",
        "[2024-01-15 14:35:00 UTC] INFO  notification-service: Sent push notification batch (12 devices)",
        "[2024-01-15 14:44:15 UTC] ERROR notification-service: Failed to fetch user preferences from user-service: connection refused",
        "[2024-01-15 14:44:15 UTC] WARN  notification-service: Cannot enrich notifications — user-service unreachable",
        "[2024-01-15 14:44:30 UTC] ERROR notification-service: POST /notify/email failed — user lookup timeout (5000ms)",
        "[2024-01-15 14:45:00 UTC] WARN  notification-service: Falling back to cached user preferences (stale by 18 minutes)",
        "[2024-01-15 14:46:00 UTC] ERROR notification-service: 3 notification jobs failed in last 2 minutes — user-service still down",
        "[2024-01-15 14:50:00 UTC] WARN  notification-service: Queue backlog: 47 pending notifications awaiting user-service recovery",
    ],
}


# ---------------------------------------------------------------------------
# Task 2: Medium Bad Deploy
# ---------------------------------------------------------------------------

LOGS_MEDIUM: dict[str, list[str]] = {
    "api-gateway": [
        "[2024-01-15 14:45:00 UTC] INFO  api-gateway: Routing normally. All upstreams healthy.",
        "[2024-01-15 14:50:00 UTC] INFO  api-gateway: deploy notification: order-service v2.3.1 rolled out",
        "[2024-01-15 14:50:45 UTC] WARN  api-gateway: order-service error rate rising: 12% (threshold: 5%)",
        "[2024-01-15 14:51:00 UTC] ERROR api-gateway: order-service returning 500s: POST /orders/create -> 500",
        "[2024-01-15 14:51:30 UTC] ERROR api-gateway: order-service error rate: 54% — circuit breaker threshold approaching",
        "[2024-01-15 14:52:00 UTC] ERROR api-gateway: POST /orders/create -> order-service 500 Internal Server Error (87ms)",
        "[2024-01-15 14:52:30 UTC] WARN  api-gateway: Circuit breaker for order-service HALF-OPEN",
        "[2024-01-15 14:53:00 UTC] ERROR api-gateway: 3 consecutive failures from order-service — circuit OPEN",
        "[2024-01-15 14:55:00 UTC] INFO  api-gateway: auth-service, search-service still responding normally",
    ],
    "auth-service": [
        "[2024-01-15 14:40:00 UTC] INFO  auth-service: JWT validation service running normally",
        "[2024-01-15 14:45:00 UTC] INFO  auth-service: Processed 2,341 auth requests in last 5 minutes. Avg latency 12ms.",
        "[2024-01-15 14:50:00 UTC] INFO  auth-service: POST /auth/token 200 11ms",
        "[2024-01-15 14:52:00 UTC] INFO  auth-service: POST /auth/validate 200 9ms",
        "[2024-01-15 14:55:00 UTC] INFO  auth-service: Health OK. Token cache hit rate: 94%.",
        "[2024-01-15 14:57:00 UTC] INFO  auth-service: POST /auth/token 200 10ms",
        "[2024-01-15 14:59:00 UTC] INFO  auth-service: All systems nominal. No anomalies detected.",
    ],
    "order-service": [
        "[2024-01-15 14:45:00 UTC] INFO  order-service: Running v2.3.0 — stable. Processed 1,204 orders today.",
        "[2024-01-15 14:50:00 UTC] INFO  order-service: Deploy v2.3.1 starting — feature: async payment validation",
        "[2024-01-15 14:50:15 UTC] INFO  order-service: Deploy v2.3.1 completed at 14:50 UTC. Restarting...",
        "[2024-01-15 14:50:20 UTC] INFO  order-service: v2.3.1 startup complete. Accepting requests.",
        "[2024-01-15 14:50:35 UTC] ERROR order-service: java.lang.NullPointerException",
        "[2024-01-15 14:50:35 UTC] ERROR order-service:   at com.example.order.OrderHandler.processPayment(OrderHandler.java:247)",
        "[2024-01-15 14:50:35 UTC] ERROR order-service:   at com.example.order.OrderService.createOrder(OrderService.java:103)",
        "[2024-01-15 14:50:36 UTC] ERROR order-service: POST /orders/create failed with 500 — NullPointerException in payment handler",
        "[2024-01-15 14:51:00 UTC] ERROR order-service: 23 requests failed in last 30 seconds — all NullPointerException in OrderHandler.processPayment",
        "[2024-01-15 14:51:30 UTC] ERROR order-service: Error rate: 54%. All POST /orders/create requests failing.",
        "[2024-01-15 14:52:00 UTC] WARN  order-service: Deploy v2.3.1 appears to have introduced regression in payment processing code path",
        "[2024-01-15 14:53:00 UTC] ERROR order-service: Cumulative failures since deploy: 187 orders lost",
    ],
    "inventory-service": [
        "[2024-01-15 14:45:00 UTC] INFO  inventory-service: Stock levels nominal. 15,243 SKUs tracked.",
        "[2024-01-15 14:50:30 UTC] WARN  inventory-service: order-service response slow (1200ms, timeout in 2000ms)",
        "[2024-01-15 14:51:00 UTC] ERROR inventory-service: Timeout waiting for order-service response (2000ms exceeded)",
        "[2024-01-15 14:51:15 UTC] ERROR inventory-service: Cannot confirm inventory reservation — order-service unreachable",
        "[2024-01-15 14:51:30 UTC] WARN  inventory-service: Inventory reservations piling up (47 pending) — order-service not confirming",
        "[2024-01-15 14:52:00 UTC] ERROR inventory-service: order-service RPC call failed: received HTTP 500",
        "[2024-01-15 14:53:00 UTC] WARN  inventory-service: Holding inventory locks for 24 items — cannot release until order-service responds",
        "[2024-01-15 14:55:00 UTC] ERROR inventory-service: P99 latency spiked to 2,340ms due to blocked inventory reservations",
    ],
    "search-service": [
        "[2024-01-15 14:40:00 UTC] INFO  search-service: Elasticsearch cluster healthy. 2.3M documents indexed.",
        "[2024-01-15 14:45:00 UTC] INFO  search-service: Scheduled reindex job started at 14:45 UTC — weekly product catalog refresh",
        "[2024-01-15 14:45:01 UTC] INFO  search-service: Reindex job: 0/50,000 products processed",
        "[2024-01-15 14:47:00 UTC] INFO  search-service: CPU spike expected during reindex — this is normal scheduled behavior",
        "[2024-01-15 14:48:00 UTC] INFO  search-service: Reindex job: 18,000/50,000 products processed (36%)",
        "[2024-01-15 14:50:00 UTC] INFO  search-service: CPU at 83% — reindex job in progress, expected high usage",
        "[2024-01-15 14:52:00 UTC] INFO  search-service: Reindex job: 34,000/50,000 products processed (68%)",
        "[2024-01-15 14:55:00 UTC] INFO  search-service: Reindex job complete. CPU returning to baseline (22%).",
        "[2024-01-15 14:56:00 UTC] INFO  search-service: GET /search?q=laptop 200 43ms — search healthy",
    ],
    "cache-layer": [
        "[2024-01-15 14:40:00 UTC] INFO  cache-layer: Redis 7.2 running. Memory: 1.2GB / 4GB. Hit rate: 92%.",
        "[2024-01-15 14:45:00 UTC] INFO  cache-layer: PING OK. Connected clients: 47.",
        "[2024-01-15 14:50:00 UTC] INFO  cache-layer: Memory: 1.3GB / 4GB. Hit rate: 91%. Evictions: 0.",
        "[2024-01-15 14:55:00 UTC] INFO  cache-layer: Connected clients: 51. Ops/sec: 8,234. All healthy.",
        "[2024-01-15 15:00:00 UTC] INFO  cache-layer: Memory: 1.3GB / 4GB. Hit rate: 92%. Evictions: 0.",
    ],
}


# ---------------------------------------------------------------------------
# Task 3: Hard Phantom (memory leak in cache-layer)
# ---------------------------------------------------------------------------

LOGS_HARD: dict[str, list[str]] = {
    "api-gateway": [
        "[2024-01-15 11:00:00 UTC] INFO  api-gateway: All upstreams healthy. Load balanced.",
        "[2024-01-15 12:00:00 UTC] INFO  api-gateway: P99 latency: 210ms — within SLA",
        "[2024-01-15 13:00:00 UTC] WARN  api-gateway: P99 latency spike: 1,240ms (threshold: 1,000ms) — transient",
        "[2024-01-15 13:10:00 UTC] INFO  api-gateway: P99 latency back to 195ms",
        "[2024-01-15 14:00:00 UTC] WARN  api-gateway: P99 latency spike: 1,450ms — lasting 8 seconds",
        "[2024-01-15 14:15:00 UTC] INFO  api-gateway: P99 latency normalized: 220ms",
        "[2024-01-15 14:30:00 UTC] WARN  api-gateway: P99 latency spike: 1,820ms — lasting 14 seconds",
        "[2024-01-15 14:35:00 UTC] INFO  api-gateway: P99 latency normalized: 215ms",
        "[2024-01-15 14:45:00 UTC] WARN  api-gateway: P99 latency spike: 2,100ms — lasting 22 seconds",
        "[2024-01-15 14:55:00 UTC] WARN  api-gateway: Latency spikes increasing in duration and severity",
    ],
    "auth-service": [
        "[2024-01-15 13:00:00 UTC] INFO  auth-service: Config reload initiated — log level change from INFO to DEBUG",
        "[2024-01-15 13:00:05 UTC] INFO  auth-service: Config update applied: log_level=DEBUG (was INFO)",
        "[2024-01-15 13:00:05 UTC] DEBUG auth-service: Debug logging enabled",
        "[2024-01-15 13:05:00 UTC] INFO  auth-service: JWT validation healthy. P99: 11ms.",
        "[2024-01-15 14:00:00 UTC] INFO  auth-service: POST /auth/validate 200 10ms",
        "[2024-01-15 14:30:00 UTC] INFO  auth-service: POST /auth/token 200 12ms",
        "[2024-01-15 14:50:00 UTC] INFO  auth-service: Health check OK. Token cache hit rate: 96%.",
        "[2024-01-15 14:55:00 UTC] INFO  auth-service: No anomalies. Config change at 13:00 was routine (log level only).",
    ],
    "user-service": [
        "[2024-01-15 14:00:00 UTC] INFO  user-service: Serving requests normally. P99: 95ms.",
        "[2024-01-15 14:30:00 UTC] INFO  user-service: GET /users/profile 200 88ms",
        "[2024-01-15 14:45:00 UTC] INFO  user-service: 4,211 requests in last 15 min. P99: 102ms.",
        "[2024-01-15 14:55:00 UTC] INFO  user-service: Cache hit rate: 88%. All healthy.",
    ],
    "order-service": [
        "[2024-01-15 11:00:00 UTC] INFO  order-service: Running v2.4.0. Normal operations.",
        "[2024-01-15 13:00:00 UTC] WARN  order-service: P99 latency spike: 1,620ms — intermittent",
        "[2024-01-15 13:00:08 UTC] INFO  order-service: Latency normalized after 8s. Cache response was slow.",
        "[2024-01-15 14:00:00 UTC] WARN  order-service: P99 latency spike: 1,890ms",
        "[2024-01-15 14:00:14 UTC] INFO  order-service: Latency normalized. Spike correlated with cache slowness.",
        "[2024-01-15 14:30:00 UTC] WARN  order-service: P99 latency spike: 2,240ms — longest so far",
        "[2024-01-15 14:30:22 UTC] INFO  order-service: Latency normalized. All spikes coincide with cache-layer slow responses.",
        "[2024-01-15 14:45:00 UTC] WARN  order-service: P99 latency: 2,540ms. Spike frequency increasing.",
        "[2024-01-15 14:55:00 UTC] WARN  order-service: 6 latency spikes in last hour. Pattern: every 15-20 min.",
    ],
    "payment-service": [
        "[2024-01-15 11:00:00 UTC] INFO  payment-service: P99 latency: 145ms. Normal.",
        "[2024-01-15 13:00:00 UTC] WARN  payment-service: P99 latency spike: 1,310ms — brief",
        "[2024-01-15 14:00:00 UTC] WARN  payment-service: P99 latency spike: 1,750ms",
        "[2024-01-15 14:30:00 UTC] WARN  payment-service: P99 latency spike: 2,050ms — payment timeouts starting",
        "[2024-01-15 14:30:20 UTC] INFO  payment-service: Latency normalized. Spike started/ended with cache-layer GC pause.",
        "[2024-01-15 14:45:00 UTC] WARN  payment-service: 3 payment transactions timed out during latency spike",
        "[2024-01-15 14:55:00 UTC] WARN  payment-service: Customer impact: payment page slow intermittently",
    ],
    "notification-service": [
        "[2024-01-15 14:00:00 UTC] INFO  notification-service: Queue depth: 12. Processing normally.",
        "[2024-01-15 14:30:00 UTC] INFO  notification-service: Queue depth: 8. All workers healthy.",
        "[2024-01-15 14:55:00 UTC] INFO  notification-service: 1,243 notifications sent today. No errors.",
    ],
    "analytics-service": [
        "[2024-01-15 13:00:00 UTC] INFO  analytics-service: Daily batch aggregation started",
        "[2024-01-15 13:30:00 UTC] INFO  analytics-service: Processing 2.4M events — CPU intensive but expected",
        "[2024-01-15 14:00:00 UTC] INFO  analytics-service: CPU at 72% — normal for batch window",
        "[2024-01-15 14:30:00 UTC] INFO  analytics-service: Batch aggregation 60% complete. CPU: 78%.",
        "[2024-01-15 14:45:00 UTC] INFO  analytics-service: Batch aggregation 85% complete. CPU: 74%.",
        "[2024-01-15 14:55:00 UTC] INFO  analytics-service: Batch aggregation complete. CPU returning to 15%. This is routine daily processing.",
    ],
    "cache-layer": [
        "[2024-01-15 11:00:00 UTC] INFO  cache-layer: Redis 7.2 started. Memory RSS: 2.1GB. GC: none.",
        "[2024-01-15 11:30:00 UTC] INFO  cache-layer: Memory RSS: 2.2GB. Hit rate: 93%. Normal operation.",
        "[2024-01-15 12:00:00 UTC] INFO  cache-layer: Memory RSS: 2.3GB. Ops/sec: 12,400.",
        "[2024-01-15 12:30:00 UTC] WARN  cache-layer: Minor GC triggered. Pause: 180ms. RSS: 2.4GB.",
        "[2024-01-15 12:30:00 UTC] WARN  cache-layer: GC pause 180ms — downstream services may see brief latency",
        "[2024-01-15 13:00:00 UTC] WARN  cache-layer: Memory RSS: 2.5GB. Minor GC pause: 450ms.",
        "[2024-01-15 13:00:00 UTC] WARN  cache-layer: GC pause 450ms — connections queued: 34",
        "[2024-01-15 13:30:00 UTC] INFO  cache-layer: Memory RSS: 2.6GB. Hit rate: 91%.",
        "[2024-01-15 14:00:00 UTC] WARN  cache-layer: Memory RSS: 2.9GB. Major GC collection triggered.",
        "[2024-01-15 14:00:00 UTC] WARN  cache-layer: GC pause 820ms — connections queued: 78. STOP-THE-WORLD event.",
        "[2024-01-15 14:30:00 UTC] WARN  cache-layer: Memory RSS: 3.1GB. Major GC pause: 1,240ms. All writes blocked.",
        "[2024-01-15 14:30:00 UTC] ERROR cache-layer: GC pause 1240ms — 112 client connections timed out during pause",
        "[2024-01-15 14:45:00 UTC] WARN  cache-layer: Memory RSS: 3.3GB (steady increase ~50MB/hour since startup).",
        "[2024-01-15 14:45:00 UTC] ERROR cache-layer: Major GC pause 1,580ms. Memory not fully reclaimed after GC. Possible leak.",
        "[2024-01-15 14:55:00 UTC] ERROR cache-layer: Memory RSS approaching configured max (4GB). GC pauses will worsen.",
        "[2024-01-15 14:55:00 UTC] ERROR cache-layer: GC pause pattern: 180ms → 450ms → 820ms → 1240ms → 1580ms (growing). Memory leak suspected.",
    ],
}


def get_logs(task_name: str, service_name: str) -> list[str]:
    """Return log lines for a given task and service."""
    mapping = {
        "easy_oom_outage": LOGS_EASY,
        "medium_bad_deploy": LOGS_MEDIUM,
        "hard_phantom": LOGS_HARD,
    }
    logs = mapping.get(task_name, {})
    return logs.get(service_name, [f"[2024-01-15 14:55:00 UTC] INFO  {service_name}: No log data available"])


def format_logs(task_name: str, service_name: str) -> str:
    """Return formatted log output (last 20 lines) for a service."""
    lines = get_logs(task_name, service_name)
    last_20 = lines[-20:]
    header = f"=== LOGS: {service_name} (last {len(last_20)} entries) ==="
    return header + "\n" + "\n".join(last_20)
