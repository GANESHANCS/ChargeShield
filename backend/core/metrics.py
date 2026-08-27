"""
Operational Metrics Collector for ChargeShield Production Observability.
Provides thread-safe metrics counters for API traffic, error rates, DB pool health, and SLA indicators.
"""

import threading
import time
from typing import Dict, Any


class MetricsCollector:
    """Thread-safe operational counters and latency accumulator."""
    def __init__(self):
        self._lock = threading.Lock()
        self._requests_total = 0
        self._errors_total = 0
        self._auth_failures_total = 0
        self._db_errors_total = 0
        self._predictions_total = 0
        self._ingestion_failures_total = 0
        self._jobs_failed_total = 0
        self._total_latency_ms = 0.0
        self._start_time = time.time()

    def record_request(self, status_code: int, latency_ms: float):
        with self._lock:
            self._requests_total += 1
            self._total_latency_ms += latency_ms
            if status_code >= 400:
                self._errors_total += 1
            if status_code in (401, 403):
                self._auth_failures_total += 1

    def record_db_error(self):
        with self._lock:
            self._db_errors_total += 1

    def record_prediction(self):
        with self._lock:
            self._predictions_total += 1

    def record_ingestion_failure(self):
        with self._lock:
            self._ingestion_failures_total += 1

    def record_job_failure(self):
        with self._lock:
            self._jobs_failed_total += 1

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = round(self._total_latency_ms / max(self._requests_total, 1), 2)
            uptime_seconds = int(time.time() - self._start_time)
            return {
                "uptime_seconds": uptime_seconds,
                "requests_total": self._requests_total,
                "errors_total": self._errors_total,
                "auth_failures_total": self._auth_failures_total,
                "db_errors_total": self._db_errors_total,
                "predictions_total": self._predictions_total,
                "ingestion_failures_total": self._ingestion_failures_total,
                "jobs_failed_total": self._jobs_failed_total,
                "avg_request_latency_ms": avg_latency,
                "error_rate_pct": round((self._errors_total / max(self._requests_total, 1)) * 100, 2)
            }


metrics_collector = MetricsCollector()
