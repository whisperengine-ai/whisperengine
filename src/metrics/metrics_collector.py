"""Lightweight in-process metrics collection for WhisperEngine.

This provides simple counters and timing instrumentation without pulling in an
external dependency or metrics backend. It is intentionally minimal and
thread-safe enough for current usage patterns (GIL protected increments).

Design goals:
  * Zero external deps
  * O(1) hot-path operations
  * JSON serializable snapshot for logging / baselining
  * Labels support (converted to stable tuple key)
  * Guarded by ENABLE_METRICS_LOGGING env var (default: true)

Future extensions (not implemented yet):
  * Export to Prometheus/OpenTelemetry
  * Sliding window statistics
  * Percentile estimation (HDR histogram / CKMS)
"""

from __future__ import annotations

import os
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Any
from datetime import datetime, timezone as tz

_METRICS_ENABLED = os.getenv("ENABLE_METRICS_LOGGING", "true").lower() == "true"


def metrics_enabled() -> bool:
    return _METRICS_ENABLED


LabelKey = Tuple[Tuple[str, str], ...]  # canonicalized sorted (k,v) tuples


def _canon_labels(labels: Dict[str, Any] | None) -> LabelKey:
    if not labels:
        return tuple()
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


@dataclass
class CounterStat:
    name: str
    value: int
    labels: Dict[str, str]


@dataclass
class TimingStat:
    name: str
    count: int
    total_seconds: float
    min_seconds: float
    max_seconds: float
    labels: Dict[str, str]

    @property
    def avg_seconds(self) -> float:
        return self.total_seconds / self.count if self.count else 0.0


class MetricsCollector:
    """Singleton-style in-process metrics aggregator."""

    _instance: "MetricsCollector" | None = None  # type: ignore[valid-type]
    _lock = threading.Lock()

    def __init__(self):
        self._counters: Dict[str, Dict[LabelKey, int]] = defaultdict(lambda: defaultdict(int))
        self._timings: Dict[str, Dict[LabelKey, Dict[str, float]]] = defaultdict(lambda: defaultdict(lambda: {
            "count": 0,
            "total": 0.0,
            "min": float("inf"),
            "max": 0.0,
        }))
        self._created_at = datetime.now(tz.utc)

    # ------------------------------------------------------------------
    # Access / singleton
    # ------------------------------------------------------------------
    @classmethod
    def get(cls) -> "MetricsCollector":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = MetricsCollector()
        return cls._instance

    # ------------------------------------------------------------------
    # Counter API
    # ------------------------------------------------------------------
    def incr(self, name: str, amount: int = 1, **labels: Any):
        if not _METRICS_ENABLED:
            return
        lk = _canon_labels(labels)
        self._counters[name][lk] += amount

    # ------------------------------------------------------------------
    # Timing API
    # ------------------------------------------------------------------
    def record_timing(self, name: str, seconds: float, **labels: Any):
        if not _METRICS_ENABLED:
            return
        lk = _canon_labels(labels)
        stat = self._timings[name][lk]
        stat["count"] += 1
        stat["total"] += seconds
        if seconds < stat["min"]:
            stat["min"] = seconds
        if seconds > stat["max"]:
            stat["max"] = seconds

    def time_block(self, name: str, **labels: Any):  # context manager
        collector = self

        class _TimerCtx:
            def __init__(self):
                self._start = 0.0

            def __enter__(self):
                self._start = time.perf_counter()
                return self

            def __exit__(self, exc_type, exc, tb):
                duration = time.perf_counter() - self._start
                collector.record_timing(name, duration, **labels, error=bool(exc_type))
                return False  # don't swallow exceptions

        return _TimerCtx()

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------
    def snapshot(self, reset: bool = False) -> Dict[str, Any]:
        counters_out = []
        for name, label_map in self._counters.items():
            for lk, val in label_map.items():
                counters_out.append(CounterStat(name=name, value=val, labels=dict(lk)))

        timings_out = []
        for name, label_map in self._timings.items():
            for lk, stat in label_map.items():
                timings_out.append(
                    TimingStat(
                        name=name,
                        count=int(stat["count"]),
                        total_seconds=stat["total"],
                        min_seconds=(0.0 if stat["count"] == 0 else stat["min"]),
                        max_seconds=stat["max"],
                        labels=dict(lk),
                    )
                )

        out = {
            "generated_at": datetime.now(tz.utc).isoformat(),
            "uptime_seconds": (datetime.now(tz.utc) - self._created_at).total_seconds(),
            "counters": [asdict(c) for c in counters_out],
            "timings": [dict(**asdict(t), avg_seconds=t.avg_seconds) for t in timings_out],
        }

        if reset:
            self._counters.clear()
            self._timings.clear()
        return out


# Convenience module-level functions
def incr(name: str, amount: int = 1, **labels: Any):
    MetricsCollector.get().incr(name, amount, **labels)


def record_timing(name: str, seconds: float, **labels: Any):
    MetricsCollector.get().record_timing(name, seconds, **labels)


def time_block(name: str, **labels: Any):
    return MetricsCollector.get().time_block(name, **labels)


def export_snapshot(reset: bool = False) -> Dict[str, Any]:
    return MetricsCollector.get().snapshot(reset=reset)
