"""Pre-generated metric snapshots per service per task.

Each snapshot contains the last 6 data points (30 minutes at 5-min intervals).
Metric types: cpu_percent, memory_rss_mb, latency_p50_ms, latency_p99_ms,
              error_rate_percent, requests_per_second
"""

from __future__ import annotations

# Timestamps for last 6 data points (T-25min to T)
TIMESTAMPS = [
    "14:30 UTC",
    "14:35 UTC",
    "14:40 UTC",
    "14:45 UTC",
    "14:50 UTC",
    "14:55 UTC",
]

TIMESTAMPS_HARD = [
    "14:30 UTC",
    "14:35 UTC",
    "14:40 UTC",
    "14:45 UTC",
    "14:50 UTC",
    "14:55 UTC",
]

# ---------------------------------------------------------------------------
# Metric data: dict[task][service][metric] = list[6 values]
# ---------------------------------------------------------------------------

METRICS_EASY: dict[str, dict[str, list]] = {
    "user-service": {
        "cpu_percent":          [45, 52, 61, 78, 0, 0],
        "memory_rss_mb":        [1800, 2100, 2600, 3100, 0, 0],
        "latency_p50_ms":       [88, 95, 112, 145, 0, 0],
        "latency_p99_ms":       [210, 250, 380, 620, 0, 0],
        "error_rate_percent":   [0.1, 0.1, 0.3, 1.2, 100.0, 100.0],
        "requests_per_second":  [142, 138, 135, 121, 0, 0],
    },
    "api-gateway": {
        "cpu_percent":          [18, 19, 20, 21, 25, 27],
        "memory_rss_mb":        [512, 515, 518, 520, 522, 525],
        "latency_p50_ms":       [45, 47, 52, 68, 120, 125],
        "latency_p99_ms":       [180, 190, 210, 290, 980, 1050],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.2, 38.5, 42.1],
        "requests_per_second":  [580, 572, 568, 545, 312, 298],
    },
    "payment-service": {
        "cpu_percent":          [22, 21, 23, 22, 21, 22],
        "memory_rss_mb":        [680, 682, 680, 685, 681, 683],
        "latency_p50_ms":       [130, 128, 135, 131, 132, 129],
        "latency_p99_ms":       [290, 285, 310, 295, 288, 291],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "requests_per_second":  [48, 51, 47, 49, 50, 48],
    },
    "notification-service": {
        "cpu_percent":          [8, 8, 9, 8, 12, 14],
        "memory_rss_mb":        [256, 258, 257, 260, 263, 268],
        "latency_p50_ms":       [45, 44, 46, 45, 890, 1100],
        "latency_p99_ms":       [120, 118, 125, 122, 4500, 5000],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 62.0, 68.0],
        "requests_per_second":  [12, 11, 13, 12, 4, 3],
    },
}

METRICS_MEDIUM: dict[str, dict[str, list]] = {
    "api-gateway": {
        "cpu_percent":          [21, 22, 23, 24, 38, 41],
        "memory_rss_mb":        [820, 823, 825, 828, 835, 840],
        "latency_p50_ms":       [52, 54, 53, 55, 210, 225],
        "latency_p99_ms":       [180, 185, 182, 188, 1240, 1380],
        "error_rate_percent":   [0.1, 0.1, 0.1, 0.1, 48.2, 52.7],
        "requests_per_second":  [890, 905, 912, 895, 420, 390],
    },
    "auth-service": {
        "cpu_percent":          [14, 15, 14, 15, 14, 15],
        "memory_rss_mb":        [380, 381, 382, 380, 383, 381],
        "latency_p50_ms":       [10, 11, 10, 11, 10, 11],
        "latency_p99_ms":       [28, 29, 28, 30, 29, 28],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "requests_per_second":  [420, 418, 425, 421, 419, 422],
    },
    "order-service": {
        "cpu_percent":          [35, 36, 34, 37, 68, 71],
        "memory_rss_mb":        [740, 745, 742, 748, 790, 802],
        "latency_p50_ms":       [120, 118, 122, 119, 2100, 2350],
        "latency_p99_ms":       [380, 375, 382, 377, 8000, 9200],
        "error_rate_percent":   [0.2, 0.2, 0.3, 0.2, 54.1, 57.8],
        "requests_per_second":  [245, 248, 251, 247, 112, 98],
    },
    "inventory-service": {
        "cpu_percent":          [28, 29, 28, 30, 45, 48],
        "memory_rss_mb":        [520, 522, 521, 524, 540, 548],
        "latency_p50_ms":       [85, 87, 84, 88, 1800, 2100],
        "latency_p99_ms":       [240, 238, 245, 241, 5200, 6100],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 12.4, 18.9],
        "requests_per_second":  [180, 178, 182, 179, 85, 72],
    },
    "search-service": {
        "cpu_percent":          [22, 35, 62, 81, 78, 25],
        "memory_rss_mb":        [1100, 1105, 1115, 1128, 1132, 1108],
        "latency_p50_ms":       [42, 45, 48, 51, 49, 43],
        "latency_p99_ms":       [120, 125, 135, 142, 138, 122],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "requests_per_second":  [320, 318, 315, 312, 315, 322],
    },
    "cache-layer": {
        "cpu_percent":          [12, 13, 12, 14, 13, 12],
        "memory_rss_mb":        [1280, 1285, 1288, 1290, 1295, 1298],
        "latency_p50_ms":       [1, 1, 1, 1, 1, 1],
        "latency_p99_ms":       [4, 4, 5, 4, 5, 4],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "requests_per_second":  [8100, 8200, 8150, 8180, 8220, 8190],
    },
}

METRICS_HARD: dict[str, dict[str, list]] = {
    "api-gateway": {
        "cpu_percent":          [22, 23, 24, 26, 28, 30],
        "memory_rss_mb":        [830, 832, 835, 838, 842, 845],
        "latency_p50_ms":       [210, 215, 218, 220, 225, 228],
        "latency_p99_ms":       [450, 820, 480, 1820, 490, 2100],
        "error_rate_percent":   [0.1, 0.2, 0.1, 0.8, 0.1, 1.2],
        "requests_per_second":  [1200, 1215, 1225, 1218, 1230, 1222],
    },
    "auth-service": {
        "cpu_percent":          [15, 16, 15, 16, 15, 16],
        "memory_rss_mb":        [390, 391, 392, 390, 393, 391],
        "latency_p50_ms":       [10, 11, 10, 11, 10, 11],
        "latency_p99_ms":       [28, 29, 28, 30, 29, 28],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "requests_per_second":  [520, 518, 525, 521, 519, 522],
    },
    "user-service": {
        "cpu_percent":          [32, 33, 32, 34, 33, 35],
        "memory_rss_mb":        [680, 682, 684, 685, 687, 689],
        "latency_p50_ms":       [90, 92, 91, 93, 92, 94],
        "latency_p99_ms":       [245, 250, 248, 252, 249, 255],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "requests_per_second":  [380, 385, 382, 388, 384, 390],
    },
    "order-service": {
        "cpu_percent":          [38, 40, 39, 41, 42, 44],
        "memory_rss_mb":        [750, 752, 755, 758, 760, 763],
        "latency_p50_ms":       [125, 128, 126, 130, 128, 132],
        "latency_p99_ms":       [380, 1620, 395, 2240, 410, 2540],
        "error_rate_percent":   [0.1, 0.3, 0.1, 0.4, 0.1, 0.5],
        "requests_per_second":  [280, 278, 282, 275, 280, 272],
    },
    "payment-service": {
        "cpu_percent":          [25, 26, 25, 27, 26, 28],
        "memory_rss_mb":        [620, 622, 621, 624, 623, 626],
        "latency_p50_ms":       [140, 142, 141, 143, 142, 145],
        "latency_p99_ms":       [320, 1310, 335, 2050, 345, 2200],
        "error_rate_percent":   [0.0, 0.2, 0.0, 0.3, 0.0, 0.4],
        "requests_per_second":  [185, 183, 187, 181, 186, 179],
    },
    "notification-service": {
        "cpu_percent":          [9, 9, 10, 9, 10, 9],
        "memory_rss_mb":        [260, 261, 262, 261, 263, 262],
        "latency_p50_ms":       [48, 49, 48, 50, 49, 51],
        "latency_p99_ms":       [125, 128, 126, 130, 127, 132],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "requests_per_second":  [15, 14, 16, 15, 14, 16],
    },
    "analytics-service": {
        "cpu_percent":          [72, 75, 78, 74, 71, 18],
        "memory_rss_mb":        [2100, 2150, 2200, 2180, 2150, 2050],
        "latency_p50_ms":       [0, 0, 0, 0, 0, 0],   # batch, no request latency
        "latency_p99_ms":       [0, 0, 0, 0, 0, 0],
        "error_rate_percent":   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "requests_per_second":  [0, 0, 0, 0, 0, 0],
    },
    "cache-layer": {
        "cpu_percent":          [18, 45, 20, 52, 22, 58],  # spikes = GC pauses
        "memory_rss_mb":        [3100, 3150, 3200, 3250, 3300, 3350],  # steady climb
        "latency_p50_ms":       [1, 12, 1, 15, 1, 18],
        "latency_p99_ms":       [4, 1240, 5, 1580, 6, 1820],  # huge GC spikes
        "error_rate_percent":   [0.0, 0.8, 0.0, 1.2, 0.0, 1.8],
        "requests_per_second":  [12400, 8200, 12350, 7800, 12300, 7200],
    },
}

_ALL_METRICS = {
    "easy_oom_outage": METRICS_EASY,
    "medium_bad_deploy": METRICS_MEDIUM,
    "hard_phantom": METRICS_HARD,
}


def format_metrics(task_name: str, service_name: str, metric_type: str) -> str:
    """Return a formatted ASCII table of metrics for the given service."""
    task_data = _ALL_METRICS.get(task_name, {})
    svc_data = task_data.get(service_name)
    if svc_data is None:
        return f"No metrics available for service '{service_name}' in task '{task_name}'."

    metric_map = {
        "cpu": "cpu_percent",
        "memory": "memory_rss_mb",
        "latency": "latency_p99_ms",
        "error_rate": "error_rate_percent",
        "rps": "requests_per_second",
    }
    # Resolve aliases
    internal_key = metric_map.get(metric_type, metric_type)
    if internal_key not in svc_data:
        available = list(svc_data.keys())
        return (
            f"Unknown metric '{metric_type}' for {service_name}. "
            f"Available: {', '.join(available)}"
        )

    values = svc_data[internal_key]
    unit_map = {
        "cpu_percent": "%",
        "memory_rss_mb": " MB",
        "latency_p50_ms": " ms",
        "latency_p99_ms": " ms",
        "error_rate_percent": "%",
        "requests_per_second": " req/s",
    }
    unit = unit_map.get(internal_key, "")

    display_name = {
        "cpu_percent": "CPU Usage",
        "memory_rss_mb": "Memory RSS",
        "latency_p50_ms": "Latency P50",
        "latency_p99_ms": "Latency P99",
        "error_rate_percent": "Error Rate",
        "requests_per_second": "Requests/sec",
    }.get(internal_key, internal_key)

    header = f"=== METRICS: {service_name} — {display_name} (last 30 min) ==="
    row_sep = "+" + "-" * 14 + "+" + "-" * 14 + "+"
    row_hdr = f"| {'Timestamp':^12} | {'Value':^12} |"

    rows = [header, row_sep, row_hdr, row_sep]
    ts_list = TIMESTAMPS
    for ts, val in zip(ts_list, values):
        val_str = f"{val}{unit}"
        rows.append(f"| {ts:^12} | {val_str:^12} |")
    rows.append(row_sep)
    return "\n".join(rows)


def get_all_metrics_summary(task_name: str, service_name: str) -> str:
    """Return a multi-metric summary table."""
    task_data = _ALL_METRICS.get(task_name, {})
    svc_data = task_data.get(service_name)
    if svc_data is None:
        return f"No metrics available for '{service_name}'."

    lines = [f"=== METRICS SUMMARY: {service_name} (last 30 min, 5-min intervals) ==="]
    metric_labels = {
        "cpu_percent": "CPU %",
        "memory_rss_mb": "Mem MB",
        "latency_p99_ms": "P99 ms",
        "error_rate_percent": "Err %",
        "requests_per_second": "RPS",
    }
    header_ts = " | ".join(f"{t:>10}" for t in TIMESTAMPS)
    lines.append(f"{'Metric':<20} | {header_ts}")
    lines.append("-" * 100)
    for key, label in metric_labels.items():
        if key in svc_data:
            vals = " | ".join(f"{v:>10}" for v in svc_data[key])
            lines.append(f"{label:<20} | {vals}")
    return "\n".join(lines)
