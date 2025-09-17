"""Tests for the lightweight metrics collector snapshot/export functionality.

Focus: structure, accumulation, reset semantics.
"""
from __future__ import annotations

from src.metrics import metrics_collector as metrics


def test_snapshot_structure_and_accumulation():
    metrics.incr("unit_test_counter", amount=3, scenario="baseline")
    metrics.record_timing("unit_test_timing", 0.01, phase="alpha")
    metrics.record_timing("unit_test_timing", 0.02, phase="alpha")

    snap = metrics.export_snapshot(reset=False)
    assert "generated_at" in snap
    assert "uptime_seconds" in snap
    assert isinstance(snap["counters"], list)
    assert isinstance(snap["timings"], list)

    # Validate counter presence
    counter_names = {c["name"] for c in snap["counters"]}
    assert "unit_test_counter" in counter_names

    # Validate timing aggregation
    timing_entries = [t for t in snap["timings"] if t["name"] == "unit_test_timing"]
    assert timing_entries, "Timing metric missing"
    t = timing_entries[0]
    assert t["count"] == 2
    assert 0.0 < t["avg_seconds"] <= t["max_seconds"]


def test_snapshot_reset_behavior():
    metrics.incr("reset_counter", amount=5)
    metrics.export_snapshot(reset=True)
    # After reset, a fresh snapshot should not show the same counter value growing
    post = metrics.export_snapshot(reset=False)

    # Either counter absent or value zero after reset
    post_counters = {c["name"]: c["value"] for c in post["counters"]}
    if "reset_counter" in post_counters:
        assert post_counters["reset_counter"] == 0
