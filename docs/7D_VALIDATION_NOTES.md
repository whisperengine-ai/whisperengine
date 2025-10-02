# 7D Validation Notes (Manual Session Log)

Purpose: Lightweight, repeatable structure for capturing manual 7D behavioral observations before adding new code or automation. Keep entries concise; only escalate to TODO docs for repeated, category-consistent issues.

## Session Metadata
- Date: YYYY-MM-DD
- Start Time / End Time:
- Character: elena
- Tester:
- Branch: feature/enhanced-7d-vector-system
- Model / LLM client type (if variable):
- Temperature (if configurable):

## Scenario Entries
Use one block per prompt-response pair (or chained pair for mode shift tests).

### Scenario N
**Prompt:** (shortened if long)
**Primary Dimension Target:** (Analytical | Emotional | Creative | Relationship | Interaction | Temporal | Semantic | Compression)
**Response Snippet (first ~120 chars):**
**Observations:**
- Brevity: ok / verbose / under
- Drift: none / minor / major (describe if major)
- Memory Alignment: consistent / partial / off
- Mode Shift (if applicable): clean / partial bleed / failed
- Emotional Calibration: proportional / under / over
- Interaction Steering (if expected): present / absent / weak
- Compression Fidelity (if tested): pure / synonym drift / topic injection
**Anomalies:** (only if notable; e.g., “added new coral intervention not in source list”)
**Action:** none / watch / TODO candidate

---

## Running Tally (Update Incrementally)
| Metric | Count |
|--------|-------|
| Total Scenarios | 0 |
| Verbosity Overruns | 0 |
| Mode Shift Bleeds | 0 |
| Memory Contradictions | 0 |
| Compression Drifts (new topics) | 0 |
| Interaction Misses (when requested) | 0 |
| Emotional Overreactions | 0 |
| TODO Candidates Logged | 0 |

*(Adjust counts after each entry.)*

## Repeated Anomalies (Trigger Threshold Reached)
List anomalies that occurred ≥2 times this session.
```
- Example: Compression drift (2) – both added new strategy terms.
```

## Session Synthesis (5 Lines Max)
```
Strongest dimension: …
Weakest dimension: …
Most frequent minor issue: …
Repeated anomaly present: Y/N (type)
Immediate fix needed: Y/N (why)
```

## Escalation Decision
If Immediate Fix = Y, create focused TODO doc (one file per concern). Use naming like:
```
docs/TODO_compression_transform_path.md
docs/TODO_mode_shift_bleed.md
```
Each should include: reproduction steps, impact scope, minimal intervention proposal.

## Backlog Candidate Drafts (Optional Mini-Notes)
Keep these to a single line until promoted:
```
- Potential: Interaction escalation heuristic weak when user gives binary choice prompt.
- Potential: Emotional dampening needed in analytical mode (1 instance, watch for repeat).
```

## Cross-Session Trend Snapshot (Append Only)
| Date | Sessions | Verbosity Overruns | Mode Bleeds | Memory Contradictions | Compression Drifts |
|------|----------|--------------------|-------------|-----------------------|--------------------|
|      |          |                    |             |                       |                    |

*(Update at end of each session; do not retro-edit historical rows.)*

## Notes on Non-Actions
Document conscious decisions *not* to fix now (prevents future confusion):
```
- Did not implement compression middleware; manual probe only today.
- Ignored minor synonym shifts in compression; semantics intact.
```

## Fidelity-First Reminder
Do not introduce optimization or control code until a behavior is:
1. Reproducible (≥2 instances)
2. Clearly dimension-linked (e.g., temporal pacing vs. personality tone)
3. Not solvable by CDL guideline adjustment alone.

---
End of template. Duplicate and fill per session or append continuously.
