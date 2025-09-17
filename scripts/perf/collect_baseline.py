"""Collect a performance & quality baseline snapshot for WhisperEngine.

This script exercises key subsystems with synthetic data and exports a
metrics snapshot + derived summary to JSON for tracking over time.

Usage (venv active):
  python scripts/perf/collect_baseline.py --output baseline_perf.json --iterations 25

It relies on the lightweight in-process metrics collector. Ensure
ENABLE_METRICS_LOGGING=true (default) to gather data.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import string
from datetime import datetime, timezone as tz

from src.metrics import metrics_collector as metrics
from src.intelligence.emotional_intelligence import PredictiveEmotionalIntelligence
from src.memory.integrated_memory_manager import IntegratedMemoryManager


def _rand_user() -> str:
    return "testuser_" + ''.join(random.choices(string.ascii_lowercase, k=6))


async def _run_emotional_assessments(ei: PredictiveEmotionalIntelligence, user_id: str, n: int):
    for i in range(n):
        msg = random.choice([
            "I'm feeling a bit overwhelmed by work today",
            "Everything is fine just checking in",
            "I had a great day and finished my project!",
            "Not sure what to do about this problem",
            "Thanks for the help earlier, it meant a lot",
        ])
        ctx = {"topic": "general", "turn": i}
        await ei.comprehensive_emotional_assessment(user_id, msg, ctx)


async def _run_memory_importance(im: IntegratedMemoryManager, user_id: str, n: int):
    sample_messages = [
        "This is a neutral statement about the weather.",
        "I really need help figuring out why my code crashes when I run tests.",
        "I'm excited about the new feature launch tomorrow!",
        "I feel sad about the recent news.",
        "Here's a long reflective message detailing my personal goals and challenges over the past year...",
    ]
    for _ in range(n):
        msg = random.choice(sample_messages)
        # Fake profiles/emotion minimal objects
        class EP:  # emotion profile stub
            detected_emotion = type("E", (), {"value": random.choice(["neutral", "sad", "excited", "grateful"])})()
            intensity = random.random()
            confidence = random.random()
            triggers = []

        class UP:  # user profile stub
            relationship_level = type("R", (), {"value": random.choice(["acquaintance", "friend", "close_friend"])})()

    # Direct call for instrumentation purposes (private method acceptable in controlled baseline)
    im._calculate_memory_importance(msg, EP(), UP())  # noqa: SLF001


async def _run_retrieval(im: IntegratedMemoryManager, user_id: str, n: int):
    queries = ["help", "project", "feeling", "weather", "advice"]
    for _ in range(n):
        await im.retrieve_contextual_memories(user_id, random.choice(queries), limit=5)


async def main(iterations: int, output: str):
    user_id = _rand_user()
    ei = PredictiveEmotionalIntelligence()
    im = IntegratedMemoryManager()

    # Run workloads
    await _run_emotional_assessments(ei, user_id, iterations)
    await _run_memory_importance(im, user_id, iterations * 2)
    await _run_retrieval(im, user_id, iterations)

    snap = metrics.export_snapshot(reset=False)

    # Derive summary KPIs
    timings = {t["name"]: [] for t in snap["timings"]}
    for t in snap["timings"]:
        timings.setdefault(t["name"], []).append(t["avg_seconds"])

    summary = {
        "generated_at": datetime.now(tz.utc).isoformat(),
        "iterations": iterations,
        "kpis": {
            "avg_emotional_assessment_seconds": _avg_for(snap, "emotional_assessment_seconds"),
            "avg_memory_importance_calc_seconds": _avg_for(snap, "memory_importance_calc_seconds"),
            "avg_memory_retrieval_seconds": _avg_for(snap, "memory_retrieval_seconds"),
        },
        "raw_metrics": snap,
    }

    with open(output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Baseline metrics written to {output}")


def _avg_for(snap: dict, metric_name: str) -> float:
    vals = [t["avg_seconds"] for t in snap["timings"] if t["name"] == metric_name]
    return sum(vals) / len(vals) if vals else 0.0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect WhisperEngine performance baseline")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations per workload")
    parser.add_argument("--output", type=str, default="baseline_performance.json", help="Output JSON file path")
    args = parser.parse_args()
    asyncio.run(main(args.iterations, args.output))
