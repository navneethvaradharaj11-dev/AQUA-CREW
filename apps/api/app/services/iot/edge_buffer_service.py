"""
AQUA CREW — Edge Device & Offline Reliability Buffer Service (Task 18)
Simulates edge gateway offline telemetry buffering, queue bounding,
clock synchronization drift estimation, and exponential backoff retransmission.
"""
import time
import math
import random
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
from datetime import datetime, timezone


class EdgeBufferQueue:
    """
    Simulates local buffer storage on an ESP32 or industrial edge gateway.
    Enforces bounded memory/flash capacity (FIFO eviction) and retention limits.
    """

    def __init__(self, device_id: str, max_capacity: int = 1000):
        self.device_id = device_id
        self.max_capacity = max_capacity
        self._buffer: deque = deque(maxlen=max_capacity)
        self.dropped_overflow_count = 0
        self.total_buffered_count = 0

    def push(self, reading: Dict[str, Any]) -> bool:
        """Pushes reading to edge buffer. If capacity exceeded, oldest item is evicted."""
        if len(self._buffer) >= self.max_capacity:
            self.dropped_overflow_count += 1

        self._buffer.append(reading)
        self.total_buffered_count += 1
        return True

    def drain(self, batch_size: int = 100) -> List[Dict[str, Any]]:
        """Drains a batch of buffered readings for retransmission upon reconnection."""
        batch = []
        for _ in range(min(batch_size, len(self._buffer))):
            batch.append(self._buffer.popleft())
        return batch

    def is_empty(self) -> bool:
        return len(self._buffer) == 0

    def size(self) -> int:
        return len(self._buffer)

    def clear(self) -> None:
        self._buffer.clear()


class EdgeRetransmissionEngine:
    """
    Manages retry policies with truncated exponential backoff and decorrelated jitter,
    and calculates clock synchronization offset.
    """

    @staticmethod
    def calculate_backoff(
        attempt: int,
        base_seconds: float = 1.0,
        max_seconds: float = 60.0,
        jitter_factor: float = 0.2,
    ) -> float:
        """
        Calculates exponential backoff with additive jitter:
        backoff = min(max_s, base_s * 2^attempt) +/- random(jitter)
        """
        exponential = base_seconds * (2 ** min(attempt, 10))
        capped = min(max_seconds, exponential)
        jitter = random.uniform(-jitter_factor * capped, jitter_factor * capped)
        return max(0.1, round(capped + jitter, 3))

    @staticmethod
    def estimate_clock_drift(device_timestamp_iso: str, server_now: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Estimates clock offset between edge device and central AQUA CREW server.
        """
        now = server_now or datetime.now(timezone.utc)
        try:
            device_dt = datetime.fromisoformat(device_timestamp_iso.replace("Z", "+00:00"))
            if device_dt.tzinfo is None:
                device_dt = device_dt.replace(tzinfo=timezone.utc)
            drift_seconds = (now - device_dt).total_seconds()
            drift_ms = round(drift_seconds * 1000.0, 1)

            # Acceptable drift is +/- 5000ms
            is_synchronized = abs(drift_ms) <= 5000.0

            return {
                "server_time": now.isoformat(),
                "device_time": device_dt.isoformat(),
                "clock_drift_ms": drift_ms,
                "is_synchronized": is_synchronized,
                "status": "NORMAL" if is_synchronized else ("BEHIND" if drift_ms > 0 else "AHEAD"),
            }
        except Exception as e:
            return {
                "server_time": now.isoformat(),
                "device_time": device_timestamp_iso,
                "clock_drift_ms": None,
                "is_synchronized": False,
                "error": f"Failed to parse device timestamp: {e}",
            }

    @staticmethod
    def compute_reading_fingerprint(device_id: str, sensor_id: str, seq: int, timestamp_str: str) -> str:
        """Computes deterministic fingerprint for duplicate suppression during burst retransmissions."""
        raw = f"{device_id}:{sensor_id}:{seq}:{timestamp_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

