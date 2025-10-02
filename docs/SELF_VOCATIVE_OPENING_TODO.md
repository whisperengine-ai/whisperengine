# Self-Vocative Opening Issue (Deferred Solution)

Status: Deferred (tracking only)  
Created: 2025-10-02  
Owner: (assign later)  

## 1. Problem Summary
Some AI roleplay character responses occasionally begin by addressing themselves by name (e.g., `Oh, Elena—` or `Elena, ...`) when the *user* message starts with the character name. This is stylistically awkward and breaks immersion—characters should respond to the user, not call themselves out.

Example:
User: `Elena, what's the current research on coral bleaching mechanisms?`
Bot: `Oh, Elena—I love that you’re digging into the guts of this...`

## 2. Root Cause
The LLM mirrors the leading token sequence from the user message (name + comma/emdash) and reframes it as an address. Without an explicit instruction or a post-processing guard, this slips through. Current prompt layers don't explicitly forbid self-vocative openings.

## 3. Impact
Low functional impact but reduces conversational polish and authenticity. Could also slightly inflate token count.

## 4. Reproduction Steps
1. Start any character bot (e.g., `./multi-bot.sh start elena`).
2. In Discord, send a message beginning with the bot name + comma, dash, colon, or em dash:
   - `Elena, can you summarize current coral bleaching pathways?`
   - `Elena - give me a concise update on symbiosis disruption.`
3. About 5–20% of responses (estimate) may start with self-name vocative styling depending on randomness and temperature.

## 5. Current State
- No mitigation in place (sanitizer experiment removed to minimize code churn right now).
- No guideline in CDL limiting self-vocatives.
- Not instrumented (no metric collection on frequency).

## 6. Options (Future Iterations)

| Option | Description | Pros | Cons | Effort |
|--------|-------------|------|------|--------|
| A | Add CDL guideline (communication style): “Never begin responses by addressing yourself by name.” | Zero code | May be ignored sometimes | Very low |
| B | Inline system prompt rule appended during prompt build | Faster effect, no code restructure | Adds prompt clutter | Low |
| C | Post-generation sanitizer (strip leading self-name vocative) | Deterministic fix | Minor maintenance surface | Low-Medium |
| D | Combined A + C (defense in depth) | High reliability | Slight redundancy | Medium |
| E | LLM re-ask when self-name detected (regenerate once) | High fidelity if second pass clean | Extra latency & tokens | Medium |
| F | Style scoring + rejection (scans opening tokens) | Flexible foundation for future style rules | More code (scoring layer) | Medium-High |
| G | Embed self-intro usage metric in fidelity monitor | Gives observability | Doesn’t fix alone | Low |

## 7. Recommended Path (Staged)
Phase 1 (Fast polish): Add CDL guideline + single prompt line.  
Phase 2: Lightweight sanitizer if incidence remains >2%.  
Phase 3: Optional metric counter (log structured event if cleaned).  

## 8. Proposed Sanitizer Logic (If Implemented Later)
Regex (start of string after whitespace):
```
^(?:oh|well|hey|okay|ok|alright)?[\s,]*<bot_first_name>[\s]*[,:;—-]+\s+
```
Action: Remove matched prefix if remainder is non-empty.

## 9. Edge Cases to Consider
| Case | Handling |
|------|----------|
| User intentionally roleplays addressing character (“Elena— listen…”) | Allowed; only strip in bot output. |
| Character legitimately uses own name for emphasis (“Elena here with an update…”) | Possibly allow if followed by “here” or “reporting”. |
| Name overlap with common word (not current issue) | Add whitelist or boundary checks. |
| Multi-character cross-talk scenario | Ensure we only strip when it’s the **same** bot’s name. |

## 10. Success Criteria
- Self-vocative openings reduced to near zero (<0.5% after mitigation).
- No accidental stripping of legitimate self-identification patterns (target <0.1% false positives).
- No increase in latency or token usage beyond negligible overhead.

## 11. Deferral Rationale
Current priorities: 7D behavioral validation + compression/transform path design. This is cosmetic and can wait until core fidelity features stabilize.

## 12. Next Step Triggers
Implement mitigation if ANY of:
- Frequency subjectively noticeable during manual 7D test suite runs.
- Feedback notes immersion break.
- Adding compression middleware (we can piggyback with a shared post-processing stage).

## 13. Minimal Future Implementation Checklist
- [ ] Add CDL line: "Do not start responses by addressing yourself by name."  
- [ ] (Optional) Add prompt builder insertion if CDL signal insufficient.  
- [ ] (Optional) Integrate sanitizer into unified transform pipeline.  
- [ ] Add unit test for 3 sample patterns (comma, em dash, colon).  
- [ ] Log count of sanitized events (debug).  

## 14. Open Questions
1. Should characters ever intentionally self-identify first-person (“Elena here—”)? If yes, define whitelist.
2. Does this interact with future multi-character scenes (narrative mode)? Might need richer speaker tagging.

---
Document prepared for tracking; no active code changes required right now.
