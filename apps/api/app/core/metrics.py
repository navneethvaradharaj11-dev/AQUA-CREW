"""
AQUA CREW — Prometheus Metrics Collector (Task 17)
Aggregates operational, security, simulation, and telemetry metrics in standard
Prometheus text exposition format (text/plain; version=0.0.4).
"""
import threading
from collections import defaultdict
from typing import Dict, Tuple
import time

class MetricsCollector:
    def __init__(self):
        self._lock = threading.Lock()
        # (method, endpoint, status_code) -> count
        self.http_requests_total: Dict[Tuple[str, str, int], int] = defaultdict(int)
        # event_type -> count
        self.security_events_total: Dict[str, int] = defaultdict(int)
        self.simulation_ticks_total: int = 0
        self.start_time: float = time.time()

    def record_http_request(self, method: str, endpoint: str, status_code: int):
        with self._lock:
            # Normalize path to avoid high cardinality
            path_parts = endpoint.split("/")
            normalized = []
            for part in path_parts:
                if len(part) > 20 or (part.startswith("ROV-") or part.startswith("MSN-") or part.startswith("PIPE-") or part.startswith("PLN-") or part.startswith("REC-")):
                    normalized.append("{id}")
                else:
                    normalized.append(part)
            norm_endpoint = "/".join(normalized) or "/"
            self.http_requests_total[(method, norm_endpoint, status_code)] += 1

    def record_security_event(self, event_type: str):
        with self._lock:
            self.security_events_total[event_type] += 1

    def record_simulation_tick(self):
        with self._lock:
            self.simulation_ticks_total += 1

    def generate_prometheus_text(self, active_ws: int = 0, active_rovers: int = 0, db_latency_ms: float = 0.0) -> str:
        lines = []

        # HELP and TYPE definitions
        lines.append("# HELP aqua_http_requests_total Total number of HTTP requests processed by AQUA CREW.")
        lines.append("# TYPE aqua_http_requests_total counter")
        with self._lock:
            for (method, endpoint, status_code), count in sorted(self.http_requests_total.items()):
                lines.append(f'aqua_http_requests_total{{method="{method}",endpoint="{endpoint}",status="{status_code}"}} {count}')

        lines.append("\n# HELP aqua_active_websocket_connections Current number of active WebSocket telemetry subscribers.")
        lines.append("# TYPE aqua_active_websocket_connections gauge")
        lines.append(f"aqua_active_websocket_connections {active_ws}")

        lines.append("\n# HELP aqua_active_rovers_count Number of registered rovers in active operating states.")
        lines.append("# TYPE aqua_active_rovers_count gauge")
        lines.append(f"aqua_active_rovers_count {active_rovers}")

        lines.append("\n# HELP aqua_simulation_ticks_total Cumulative simulation engine ticks executed.")
        lines.append("# TYPE aqua_simulation_ticks_total counter")
        lines.append(f"aqua_simulation_ticks_total {self.simulation_ticks_total}")

        lines.append("\n# HELP aqua_security_events_total Security and authentication audit events recorded.")
        lines.append("# TYPE aqua_security_events_total counter")
        with self._lock:
            for event_type, count in sorted(self.security_events_total.items()):
                lines.append(f'aqua_security_events_total{{event_type="{event_type}"}} {count}')

        lines.append("\n# HELP aqua_database_latency_seconds Latency of database connectivity verification in seconds.")
        lines.append("# TYPE aqua_database_latency_seconds gauge")
        lines.append(f"aqua_database_latency_seconds {round(db_latency_ms / 1000.0, 5)}")

        uptime_seconds = int(time.time() - self.start_time)
        lines.append("\n# HELP aqua_uptime_seconds Total runtime of the API process in seconds.")
        lines.append("# TYPE aqua_uptime_seconds counter")
        lines.append(f"aqua_uptime_seconds {uptime_seconds}\n")

        return "\n".join(lines)


metrics_collector = MetricsCollector()

