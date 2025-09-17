## Performance & Quality Baseline (Initial)

This document explains how to collect and interpret a local performance baseline for key WhisperEngine subsystems.

### Instrumented Subsystems

| Subsystem | Metric Prefix | Description |
|-----------|---------------|-------------|
| Emotional Intelligence | `emotional_assessment_*` | Latency + counts per assessment cycle |
| Memory Importance | `memory_importance_*` | Importance calculation latency + distribution buckets |
| Retrieval (Chroma + Graph) | `memory_retrieval_*` | Retrieval latency and request mode counts |
| Automatic Learning Hooks | `learning_*` | Trigger counts, skipped events, hook latency |

### Running the Baseline Collector

Activate your virtual environment first.

```bash
source .venv/bin/activate
python scripts/perf/collect_baseline.py --iterations 25 --output baseline_perf.json
```

This will:
1. Run synthetic emotional assessments
2. Execute multiple memory importance calculations with varied content
3. Perform contextual retrieval attempts
4. Emit a JSON file `baseline_perf.json` with raw metrics + derived KPIs

### Example KPI Fields

```json
{
  "kpis": {
    "avg_emotional_assessment_seconds": 0.0421,
    "avg_memory_importance_calc_seconds": 0.00031,
    "avg_memory_retrieval_seconds": 0.0032
  }
}
```

### Interpreting Results

| KPI | Guidance |
|-----|----------|
| Emotional assessment avg | < 100ms synthetic (real may be higher w/ external models) |
| Importance calc avg | Should remain sub-millisecond; regression >5x needs review |
| Retrieval avg | Depends on Chroma + optional graph; track trend not absolute |

### Tracking Over Time

Commit the first JSON artifact under `perf_baselines/` (add to repo if desired). Future runs can be diffed to identify regressions.

Suggested naming: `perf_baselines/baseline_YYYYMMDD.json`.

### Extending Metrics

Future additions could include:
* Token usage per response (after LLM integration layer instrumentation)
* Persistence round-trip timings (PostgreSQL inserts/selects)
* Vector similarity search latency buckets
* Memory pruning / compaction timings

### Disabling Metrics

Set `ENABLE_METRICS_LOGGING=false` in your environment to disable collection if overhead becomes a concern. Current implementation is extremely lightweight.

### Caveats

* Synthetic workload uses stubs—not reflective of production emotional model complexity.
* Graph-enhanced retrieval only engages if graph + emotion manager are fully configured.
* A single-process snapshot; distributed modes need external aggregation.

---
Initial version established by metrics instrumentation task.
