# Response Transform & Deterministic Compression TODO

Status: PLANNED (Not Started)
Owner: (Assign later)  
Created: 2025-10-02  
Scope: Multi-character (character-agnostic) — no hardcoded Elena logic

## 1. Problem Summary

Current system relies on ad‑hoc prompt instructions to request compressed / shorter variants of the *previous* bot response. This produces inconsistent behavior:

Observed issues:
1. Occasional non-sequitur generation (fresh ideation instead of pure compression).
2. Injection of novel topic nouns not present in the source response.
3. Word-count overshoot (lack of deterministic cap enforcement; relies on LLM adherence).
4. Emojis and stylistic flourishes sometimes bloat length when strict compression is desired.
5. No explicit “transform intent” detection layer; compression requests still traverse full LLM generation path.
6. No fallback deterministic compressor when LLM output violates constraints.
7. Lack of test harness to evaluate success metrics (topic fidelity, word cap, structural cleanliness).

Constraints (from WhisperEngine directives):
- No feature flags for local code — must work by default in dev.
- Character agnostic (use CDL only for style modulation if needed; do NOT hardcode names or personality traits).
- Fidelity-first principle: preserve semantic/core idea salience before trimming stylistic content.
- Avoid adding separate heavy NLP pipeline; leverage light regex + token heuristics + existing context data.

## 2. Goal Definition

Implement a deterministic response transformation layer that intercepts user “compression/shorten” requests and produces a strictly constrained output with:
- Zero new topical nouns not in the previous bot response (unless user explicitly allows expansion).
- Hard word cap (configurable, e.g. ≤25 words) with guaranteed enforcement.
- Optional stylistic toggles (allow_emojis, keep_question, preserve_emphasis).
- Fallback deterministic compressor if LLM attempt fails policy check.
- Extensible to future transforms: expand, paraphrase, bulletize, tone-shift.

## 3. Reproduction Steps (Current Broken Behavior)

Preconditions:
1. Start Elena (or any bot) via `./multi-bot.sh start elena`.
2. In Discord, stimulate a longer ideation response (e.g., “Give me 6 playful marine conservation campaign ideas for kids”).
3. Bot responds with multi-sentence creative content.
4. User sends a compression request:
   > “Please ONLY compress the previous response to ≤25 words—no new ideas.”

Potential Outcomes (undesired):
- Bot invents *new* idea phrasing absent from source (e.g., introduces “bubble nets” if not present).
- Bot exceeds 25 words by 2–8 words.
- Bot reframes content instead of direct compression.

Validation that bug exists:
1. Copy original bot response text R₀.
2. Tokenize (simple `split()` for quick test) and build noun phrase list (rudimentary regex for `[A-Za-z][A-Za-z\-]+` filtering stopwords).
3. Apply same to compressed response C.
4. Identify OOV nouns = nouns(C) − nouns(R₀). Presence > 0 indicates topic injection failure.
5. Count words in C; if > requested cap → cap enforcement missing.

## 4. High-Level Architecture Additions

New modules (character-agnostic):
1. `src/conversation/transform_intent_detector.py`
   - `detect(message_text: str) -> Optional[TransformIntent]`
   - Detects transform type (currently only `compress`).
   - Extracts numeric word cap patterns: `≤25`, `<= 25`, `under 25 words`, `max 25 words`, `25 words max`.
   - Flags `no_new_topics` if phrases like “only compress”, “no new topics”, “don’t add”, “no additions” present.

2. `src/conversation/response_transformer.py`
   - Core deterministic compression implementation.
   - `compress(previous_text: str, word_cap: int, no_new_topics: bool, allow_emojis: bool, keep_question: bool) -> str`
   - Steps:
     a. Sentence split (naive punctuation segmentation).
     b. Candidate phrase extraction (noun phrases, key verbs).
     c. Salience scoring: frequency + positional weight (first sentence bonus, optional rhetorical ending weight if question retained).
     d. Assemble compressed draft (list style vs single clause detection: if original had >=3 distinct idea markers -> join with commas/“or”).
     e. Enforce cap strictly (truncate on word boundary; ensure punctuation hygiene).
     f. Optional: Append preserved interrogative tail if within cap.

3. `src/conversation/transform_pipeline.py` (Or integrate into existing message dispatch layer)
   - Orchestrates detection → transformation → policy validation.
   - If transform intent found AND previous bot message present:
     - Bypass LLM generation path entirely.
     - Run deterministic compressor.
   - Else fallback to normal generation.

4. Policy Validator (lightweight inline):
   - Checks OOV nouns if `no_new_topics` true.
   - Re-runs compression removing offending tokens if violation.

5. Tests: `tests/unit/conversation/test_transform_compression.py`
   - Cases: basic detection, numeric cap extraction, OOV filtering, strict cap enforcement, emoji toggle, question preservation.

## 5. Detailed Implementation Phases

### Phase 0: Baseline Instrumentation
Add temporary logging (structured) when user message contains compression intent phrases to measure frequency + failure categories. (Remove after Phase 3.)

### Phase 1: Transform Intent Detector
Regex set:
```
COMPRESS_KEYWORDS = (compress|condense|shorten|tldr|summarize|make it shorter|tighten)
CAP_PATTERN = r"(?:(?:≤|<=|under|below|max|at most)\s*(\d{1,3})\s*words?)|(\d{1,3})\s*words\s*(?:max|limit)"
NO_NEW_TOPICS = phrases: ["only compress", "no new", "don’t add", "no additions", "no extra", "no new topics"]
```
Return `TransformIntent(type='compress', word_cap=extracted_or_default_25, no_new_topics=True/False)`.

### Phase 2: Deterministic Compressor
Minimal linguistic heuristics (avoid external heavy libs to keep footprint low):
- Tokenization: `re.findall(r"[A-Za-z0-9'\-]+", text)`
- Stopwords: small curated inline set (avoid large external lists).
- Noun phrase approximation: sequences of 1–3 non-stopword tokens.
- Scoring formula: `(freq * 1.0) + (is_first_sentence * 0.15) + (ends_with_question * 0.10)`.
- Assembly strategy:
  * If source has >=3 high-salience phrases: join with commas + final “or” if list-like.
  * Else compress into one clause with concise verb phrase.
- Strict cap: If > cap → iteratively remove lowest salience trailing phrases; final hard trim if still > cap.

### Phase 3: Integration Layer
Hook into post-user-message pipeline before LLM call (preferred) to avoid wasted tokens:
1. Retrieve last bot response (conversation memory manager or in-process cache).
2. If not present → send user clarification: “Need a prior response to compress—none found.”
3. Run transformer, send output, store as new bot response (so chain compressions allowed on latest compressed form).

### Phase 4: Style & Policy Options
Expose internal flags (not environment feature flags):
```
TransformOptions {
  allow_emojis: True (default) – emoji stripping via simple unicode category filter
  keep_question: Auto-detect if original ended in ?
  enforce_terminal_punctuation: True
}
```
Potential extension: `tone_profile` learned from CDL (e.g., keep a single signature stylistic flourish).

### Phase 5: Evaluation & Metrics
Add test harness script `utilities/eval/compression_probe.py` to:
1. Feed synthetic long responses.
2. Apply varying caps (15, 25, 40).
3. Report: word_count, oov_nouns, compression_ratio, kept_question, emoji_count.
Store JSON snapshots in `benchmarks/` for regression tracking.

## 6. Data Structures

```python
@dataclass
class TransformIntent:
    type: str  # 'compress'
    word_cap: int
    no_new_topics: bool = True
    raw_trigger: str = ""

@dataclass
class TransformOptions:
    allow_emojis: bool = True
    keep_question: bool = True
    enforce_terminal_punctuation: bool = True
```

## 7. Edge Cases & Handling

| Case | Handling |
|------|----------|
| No previous bot response | Send clarification; do not fabricate source. |
| Word cap < 5 | Minimum floor 5; acknowledge adjustment. |
| Source already ≤ cap | Return source unchanged (idempotent). |
| Source extremely short (≤10 words) & compress requested | Treat as no-op; inform user if beneficial? (Skip for now). |
| Repeated compression requests | Always operate on most recent bot response (already compressed). |
| Mixed instructions: compress + add new idea | Detector returns intent with `no_new_topics=False`. |
| Emojis push over cap | Optionally drop emojis first, re-count, then phrases. |
| Non-ASCII punctuation | Normalize to ASCII equivalents before phrase extraction. |

## 8. Success Criteria

Quantitative:
- ≥95% of compression responses stay within word cap on first attempt (no fallback needed).
- 0 OOV topical nouns when `no_new_topics=True` across test suite.
- Compression ratio ≥ 50% on samples > 60 words.

Qualitative:
- Maintains semantic distinctness of top 2–3 original ideas.
- Retains interrogative ending when source ended with a question (unless cap prohibits).
- Feels character-consistent (optionally preserve 1 signature stylistic element drawn from CDL — deferred).

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Over-aggressive pruning removes nuance | Weighted salience and minimum phrase floor (≥2). |
| Tokenization naive for multilingual | Initial scope: English only; add language guard later. |
| Developer drift: transform bypass not updated when pipeline changes | Centralize hook in a shared dispatch/helper, document in this file + architecture notes. |
| Emojis counted as words inconsistently | Strip before count; re-append if space remains. |
| OOV detection false positives (stemming forms) | Basic lowercase compare; accept mild false positives to err on safety. |

## 10. Out-of-Scope (For Now)
- Advanced syntactic parsing (no spaCy / heavy NLP libs in alpha stage).
- Semantic similarity scoring using embeddings (could leverage existing vector infra later for ranking phrases).
- Multi-lingual compression.
- Tone shifting / sentiment-aware transforms.

## 11. Planned File Additions
```
src/conversation/transform_intent_detector.py
src/conversation/response_transformer.py
src/conversation/transform_pipeline.py (optional consolidated orchestrator)
tests/unit/conversation/test_transform_compression.py
utilities/eval/compression_probe.py
```

## 12. Minimal Pseudocode Snippets

Intent Detection:
```python
def detect(text: str) -> Optional[TransformIntent]:
    if not re.search(COMPRESS_KEYWORDS, text, re.I):
        return None
    cap = extract_cap(text) or 25
    no_new = any(p in text.lower() for p in NO_NEW_PHRASES)
    return TransformIntent(type='compress', word_cap=cap, no_new_topics=no_new, raw_trigger=text)
```

Deterministic Compression:
```python
def compress(prev: str, cap: int, no_new_topics: bool, opts: TransformOptions) -> str:
    if word_count(prev) <= cap: return prev
    phrases = extract_phrases(prev)
    ranked = rank(phrases)
    draft = assemble(ranked, cap)
    if opts.keep_question and prev.strip().endswith('?') and not draft.endswith('?'):
        maybe_append_question(draft, prev)
    draft = enforce_cap(draft, cap)
    if no_new_topics:
        draft = remove_oov(draft, source_vocab(prev))
    if not opts.allow_emojis:
        draft = strip_emojis(draft)
    return finalize(draft)
```

## 13. Integration Hook (Proposed Flow)

```
User Message -> TransformIntentDetector
  -> if intent and previous_bot_message exists:
         deterministic_transform(previous_bot_message)
         send + store
         (skip LLM)
     else:
         normal LLM path
```

## 14. Test Plan (Initial Unit Tests)
1. Detect basic compress intent.
2. Extract numerical cap ("<= 18 words" → 18).
3. Enforce minimum cap (cap=3 → 5 floor).
4. OOV filtering removes novel noun.
5. Question preserved.
6. Emoji removal toggle.
7. Idempotent when already under cap.

## 15. Manual QA Checklist
- [ ] Long multi-idea response → compress (≤25) → verify no new nouns.
- [ ] Chain compression (original → 25 words → 15 words) retains core semantics.
- [ ] Request with “no new topics” + ambiguous phrasing still safe.
- [ ] Request without “no new” allows mild paraphrase.
- [ ] Emoji toggle works (simulate by setting allow_emojis False temporarily).

## 16. Deployment Notes
- No env vars introduced (stay compliant with no local feature flags rule).
- Modules imported in core dispatch; default active.
- If future disable needed in production, use TYPE-based strategy (e.g. TRANSFORM_PIPELINE_MODE=disabled) — postpone until real production pressure.

## 17. Follow-Up Enhancements (Future Backlog)
1. Embedding-based phrase salience (reuse Qdrant vectors) for smarter selection.
2. Paraphrase transform (tone softening / formalization) with deterministic guardrails.
3. Multi-lingual support (language detection + fallback to LLM if non-English).
4. Conversational diff explanation mode: “Here’s what I kept & why.”
5. Compression quality scoring (ROUGE-lite vs source, stored in metrics).

## 18. Open Questions
- Should we store transform lineage (so memory retrieval can backtrack to original full responses)? Probably yes; add `metadata.original_response_id` link in memory payload.
- Where to persist transform stats? Possibly lightweight JSON in `benchmarks/` until observability layer matures.

## 19. Approval / Next Steps
- Review this document.
- Green-light Phase 1–2 implementation.
- Add tasks to tracking system / backlog.
- Implement incrementally; run unit tests after each phase.

---
End of document.
