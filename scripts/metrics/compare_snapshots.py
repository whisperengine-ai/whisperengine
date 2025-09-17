"""Compare two metrics snapshot JSON files and highlight deltas.

Usage:
  python scripts/metrics/compare_snapshots.py --old old_snapshot.json --new new_snapshot.json \
      --warn-pct 25 --error-pct 50

- Computes % change for timing avg_seconds and counter values (matching name+labels)
- Emits JSON + human readable summary
- Exit codes:
    0 = OK (no thresholds exceeded)
    1 = Warning threshold exceeded
    2 = Error threshold exceeded
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Dict, Tuple

Key = Tuple[str, Tuple[Tuple[str, str], ...]]  # (metric_name, sorted labels tuple)


def _canon(name: str, labels: Dict[str, Any]) -> Key:
    return name, tuple(sorted((str(k), str(v)) for k, v in labels.items()))


def load_snapshot(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Accept either direct metrics snapshot or wrapper {snapshot: {...}}
    if "snapshot" in data and isinstance(data["snapshot"], dict):
        return data["snapshot"]
    return data


def index_counters(snap: dict) -> dict[Key, int]:
    out: dict[Key, int] = {}
    for c in snap.get("counters", []):
        out[_canon(c["name"], c.get("labels", {}))] = c.get("value", 0)
    return out


def index_timings(snap: dict) -> dict[Key, dict]:
    out: dict[Key, dict] = {}
    for t in snap.get("timings", []):
        out[_canon(t["name"], t.get("labels", {}))] = t
    return out


def pct_change(old: float, new: float) -> float:
    if old == 0:
        return math.inf if new > 0 else 0.0
    return (new - old) / old * 100.0


def compare(old_snap: dict, new_snap: dict) -> dict:
    old_c = index_counters(old_snap)
    new_c = index_counters(new_snap)
    old_t = index_timings(old_snap)
    new_t = index_timings(new_snap)

    counter_deltas = []
    for key in sorted(set(old_c) | set(new_c)):
        old_val = old_c.get(key, 0)
        new_val = new_c.get(key, 0)
        counter_deltas.append({
            "name": key[0],
            "labels": dict(key[1]),
            "old": old_val,
            "new": new_val,
            "pct_change": pct_change(old_val, new_val),
        })

    timing_deltas = []
    for key in sorted(set(old_t) | set(new_t)):
        old_entry = old_t.get(key, {"avg_seconds": 0.0})
        new_entry = new_t.get(key, {"avg_seconds": 0.0})
        timing_deltas.append({
            "name": key[0],
            "labels": dict(key[1]),
            "old_avg_seconds": old_entry.get("avg_seconds", 0.0),
            "new_avg_seconds": new_entry.get("avg_seconds", 0.0),
            "pct_change": pct_change(old_entry.get("avg_seconds", 0.0), new_entry.get("avg_seconds", 0.0)),
        })

    return {"counters": counter_deltas, "timings": timing_deltas}


def summarize(deltas: dict, warn_pct: float, error_pct: float) -> tuple[str, int]:
    exit_code = 0
    lines = ["Counter Changes:"]
    for c in deltas["counters"]:
        pct = c["pct_change"]
        status = "OK"
        if abs(pct) >= error_pct:
            status = "ERROR"; exit_code = max(exit_code, 2)
        elif abs(pct) >= warn_pct:
            status = "WARN"; exit_code = max(exit_code, 1)
        lines.append(f"  [{status}] {c['name']} {c['labels']} {c['old']} -> {c['new']} ({pct:.1f}%)")

    lines.append("\nTiming Changes:")
    for t in deltas["timings"]:
        pct = t["pct_change"]
        status = "OK"
        if abs(pct) >= error_pct:
            status = "ERROR"; exit_code = max(exit_code, 2)
        elif abs(pct) >= warn_pct:
            status = "WARN"; exit_code = max(exit_code, 1)
        lines.append(f"  [{status}] {t['name']} {t['labels']} {t['old_avg_seconds']:.4f}s -> {t['new_avg_seconds']:.4f}s ({pct:.1f}%)")

    return "\n".join(lines), exit_code


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare two metrics snapshots")
    p.add_argument("--old", required=True, help="Old/baseline snapshot JSON")
    p.add_argument("--new", required=True, help="New/current snapshot JSON")
    p.add_argument("--warn-pct", type=float, default=30.0, help="Warning threshold percentage change (abs)")
    p.add_argument("--error-pct", type=float, default=80.0, help="Error threshold percentage change (abs)")
    p.add_argument("--output-json", type=str, default=None, help="Optional file to write structured delta JSON")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    old_snap = load_snapshot(args.old)
    new_snap = load_snapshot(args.new)
    deltas = compare(old_snap, new_snap)
    summary, code = summarize(deltas, args.warn_pct, args.error_pct)
    print(summary)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump({
                "deltas": deltas,
                "warn_pct": args.warn_pct,
                "error_pct": args.error_pct,
                "exit_code": code,
            }, f, indent=2)
        print(f"\nΔ JSON written to {args.output_json}")
    return code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
