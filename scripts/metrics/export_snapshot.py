"""Export a metrics snapshot from the in-process metrics collector.

This provides a simple CLI to dump current counters & timings to JSON.
Intended for ad-hoc inspection, CI artifact capture, or diffing between
runs. It does NOT exercise workloads; see `scripts/perf/collect_baseline.py`
for an active workload & KPI baseline generator.

Usage (venv active):
  python scripts/metrics/export_snapshot.py --output metrics_snapshot.json
  python scripts/metrics/export_snapshot.py --pretty --reset
  python scripts/metrics/export_snapshot.py  # writes JSON to stdout

Flags:
  --output <file> : Path to write JSON (default: stdout)
  --pretty        : Pretty-print JSON (indent=2)
  --reset         : Reset collector after snapshot (zero out metrics)

Environment:
  ENABLE_METRICS_LOGGING (default: true) must be true; otherwise an empty
  structure is still emitted for consistency.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone as tz
from typing import Any

from src.metrics import metrics_collector as metrics


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export in-process metrics snapshot")
    parser.add_argument("--output", "-o", type=str, default=None, help="File path to write JSON (default: stdout)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON with indentation")
    parser.add_argument("--reset", action="store_true", help="Reset metrics after exporting snapshot")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    snap = metrics.export_snapshot(reset=args.reset)

    payload: dict[str, Any] = {
        "generated_at": datetime.now(tz.utc).isoformat(),
        "metrics_enabled": metrics.metrics_enabled(),
        "process": {
            "pid": os.getpid(),
            "cwd": os.getcwd(),
        },
        "snapshot": snap,
    }

    text = json.dumps(payload, indent=2 if args.pretty else None, sort_keys=bool(args.pretty))

    if args.output:
        try:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"📊 Metrics snapshot written to {args.output}")
        except OSError as e:  # pragma: no cover - simple IO failure path
            print(f"❌ Failed to write metrics snapshot: {e}", file=sys.stderr)
            return 1
    else:
        print(text)
    if args.reset:
        print("ℹ️  Metrics collector reset after snapshot")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
