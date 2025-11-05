# Prompt Components: Infrastructure Blockers and Implementation Plan

Date: 2025-11-05
Owner: WhisperEngine
Scope: Remaining CDL-integrated prompt components and adjacent systems that are not yet fully implemented in the PromptAssembler path.

**⚠️ IMPORTANT: This document is NOT prescriptive.**

The solutions outlined below require significant architectural and design decisions around:
- Real-time vs. strategic (enrichment worker) execution paths
- Data ownership and persistence boundaries (PostgreSQL vs. Qdrant vs. InfluxDB)
- Inference pipeline complexity and confidence thresholds
- Service initialization and dependency injection patterns
- Component token budgets and priority ordering trade-offs

These components touch core identity, learning, and emotional intelligence systems. They must be carefully thought through, prototyped, and validated before implementation. Use this document as a starting point for discussion and design—not a ready-to-implement specification.

---

## Context: Recent CDL Dual Path Unification Refactor

**Note: Some gaps in component implementation may be intentional following the October 2025 CDL refactoring.**

Between **October 18-21, 2025**, WhisperEngine underwent a major architectural refactoring to eliminate dual prompt assembly paths:

**Key Commits:**
- `7658fd6` (Oct 18): "docs: Update all docs to reflect dual prompt paths resolution"
- `747cb45` (Oct 21): "refactor: Delete dead code phase 2 - remove unused _apply_cdl_character_enhancement()"
- `ee2ba29` (Oct 21): "refactor: Delete dead code phase 3 - remove unified prompt builder methods"
- `0391f8d` (Oct 21): "feat: Implement CDL relationship system with component factory integration"

**What Changed:**
- Eliminated dual path where Phase 4 (PromptAssembler) work was replaced by Phase 5.5 (CDL enhancement)
- Removed ~1,755 lines of dead code (old unified prompt builder, CDL enhancement methods)
- Established single unified prompt assembly path via PromptAssembler + CDL component factories
- Performance gain: ~150ms per message by eliminating wasted processing

**Result:** CDL character data now flows through structured assembly as first-class components. Some components that existed in the old unified prompt builder were intentionally NOT migrated to the new system pending design decisions about their role in the simplified architecture.

See: `docs/architecture/DUAL_PROMPT_ASSEMBLY_INVESTIGATION.md` for full resolution details.

---

## Current Status and Clarifications

This document focuses on three in-scope items from our active TODOs:

- USER_PERSONALITY (Priority 7)
- CHARACTER_LEARNING (Priority 9)
- EMOTIONAL_TRIGGERS (Priority 12)

**Real-time vs. Strategic Path:**
- **User preferences/facts**: Already available in real-time prompt path via PostgreSQL (universal_users.preferences, user_fact_relationships, fact_entities).
- **Conversation summaries**: Strategic/background (enrichment worker); consumable by prompts when available but not blocking.
- **Emotional triggers**: CDL table exists (character_emotional_triggers), API exists (EnhancedCDLManager.get_emotional_triggers()), suitable for real-time prompts when populated by designers.
- **Character learning**: Designed as strategic/background intelligence; not currently active in real-time prompt path; services (insight extractor/storage) are referenced but not initialized.

The goal is to identify blockers, explore design constraints, and outline potential approaches—not to prescribe final implementation.

---

## Shared constraints and guardrails

- Production safety: No breaking changes to Qdrant schema. Additive-only payload/fields.
- No local feature flags: Components should work by default in development. Flags are reserved for external services only.
- Database-first: Character data comes from PostgreSQL CDL tables; add Alembic migrations for any new tables.
- MessageProcessor is the single path: All context assembly goes through `src/core/message_processor.py`.
- Personality-first: Maintain character authenticity. Do not hardcode character logic in Python.

---

## USER_PERSONALITY (Priority 7)

Status: Not Implemented

Intended role: Provide a concise, structured profile of the user’s stable traits and preferences that meaningfully shape the bot’s tone and approach.

Existing assets:
- `universal_users.preferences` JSONB contains multiple preference domains (preferred_name, location, timezone, food_preferences, topic_preferences, communication_style, response_length, etc.).
- User facts/relationships tables: `user_fact_relationships`, `fact_entities` provide entity-level facts (pets, hobbies, family relations). These already feed knowledge context.

Blockers:
- No standardized "personality" representation (e.g., Big Five or house-style trait schema) is persisted for users.
- No inference pipeline producing stable personality traits from conversation signals.
- No dedicated API surface to retrieve a compact personality prompt component separate from the broader user facts context.

Design questions requiring architectural decisions:
- Should user personality traits be inferred from conversation patterns (ML-based), explicitly set by users (UI/onboarding), or designer-curated per user cohort?
- What trait taxonomy is appropriate? Big Five, MBTI-style, house-style dimensions, or custom WhisperEngine schema?
- How do we balance trait inference confidence vs. prompt assembly requirements (omit low-confidence vs. use neutral defaults)?
- Should this live in universal_users.preferences (JSONB), a dedicated table, or derived on-the-fly from existing preference fields?
- How does this interact with existing user facts (entity relationships) without creating redundancy or conflicts?

Possible approach (requires validation):
- Data contract: Introduce a compact personality schema embedded in `universal_users.preferences` under a new key `personality_profile` (JSONB). This avoids new tables and respects additive-only changes.
  - Example shape:
    ```json
    {
      "personality_profile": {
        "style": {"value": "casual", "confidence": 0.74, "updated_at": "..."},
        "detail_preference": {"value": "concise", "confidence": 0.68, "updated_at": "..."},
        "empathy_preference": {"value": "balanced", "confidence": 0.61, "updated_at": "..."}
      }
    }
    ```
  - Keep it small; 3-5 traits max to start. Use the same value/confidence/updated_at pattern used elsewhere.
- Inference path (Phase 1): Derive from existing fields with simple heuristics (e.g., historical response length preference, prior positive reactions), then iteratively improve.
- Retrieval API: Implement `get_user_personality_profile(user_id)` in a suitable service (e.g., a small module under `src/users/`) that returns a typed structure for the component factory.
- Component factory: Add `create_user_personality_component()` to `cdl_component_factories.py` or a dedicated user factory file. Output a brief, stable directive suitable for Priority 7.

Acceptance criteria (tentative):
- For a user with `preferences` populated, the component returns a short, legible directive (<= 200 tokens) that measurably affects tone/structure.
- For a user without data, the component is omitted or falls back to a neutral baseline without blocking prompt assembly.

Risks and open questions:
- Misclassification: Keep confidence thresholds; omit low-confidence traits.
- Drift: Record `updated_at` and include a small time-decay; refresh based on interaction volume.
- Privacy: User personality inference must respect user data policies and opt-out mechanisms.

---

## CHARACTER_LEARNING (Priority 9)

Status: Not Implemented; code references exist but services are None

Intended role: Reflect character’s self-discoveries and stable insights learned over time, beyond pure memory recall. Think: identity-deepening heuristics, personal growth threads.

Observed issues in code:
- `self.character_insight_extractor` and `self.character_insight_storage` are referenced in `message_processor.py` but appear uninitialized (typed as None), producing analyzer errors.
- No clear persistent store or migration for insights (distinct from Qdrant episodic memory).

Blockers:
- Missing extractor module (contract and implementation) to convert selected learning moments into normalized insights.
- Missing storage abstraction and tables to persist insights outside of Qdrant (PostgreSQL recommended for structured querying).

Design questions requiring architectural decisions:
- Should character learning be real-time (every message) or strategic (enrichment worker background processing)?
- What constitutes a "learning moment" vs. ordinary conversation? Threshold for insight extraction?
- How do we distinguish character self-discoveries from user-taught facts or designer-authored backstory?
- Should insights be per-user-character pair, or aggregated across all users for a given character?
- How does this integrate with existing CDL character identity data without creating contradictions?
- What is the confidence model for insight quality? How do we prevent noise or hallucinated learnings?

Possible approach (requires validation):
- Data model (PostgreSQL via Alembic):
  - `character_learning_insights` (id, bot_name, user_id, insight_type, content, confidence, source_memory_ids[], created_at, updated_at, metadata JSONB)
  - `character_learning_topics` (optional) to aggregate themes over time.
- API surface:
  - `CharacterInsightExtractor.extract_insights(messages|memories) -> List[Insight]`
  - `CharacterInsightStorage.store_insight(Insight) -> id`
  - `CharacterInsightStorage.get_recent_insights(bot_name, user_id, limit, horizon)`
- Component factory:
  - `create_character_learning_component(bot_name, user_id, priority=9)` that renders a very short list of high-signal insights, or omits the component if none.
- Integration:
  - Initialize `character_insight_extractor` and `character_insight_storage` during bot startup/injection to remove None references.

Acceptance criteria (tentative):
- With at least 1 stored insight, Priority 9 produces a compact, actionable snippet (<= 120 tokens) aligned with character identity.
- No insights -> component omitted, no errors.

Risks and open questions:
- Duplicates: Add a uniqueness check (hash of normalized content + bot + user + time window).
- Noise: Require minimum confidence and cross-reference with InfluxDB engagement/satisfaction signals if available.
- Real-time latency: If insights are extracted synchronously, ensure extraction is fast or move to background worker.
- Character consistency: Insights must align with designer-authored CDL personality and not contradict core identity.

---

## EMOTIONAL_TRIGGERS (Priority 12)

Status: Not Implemented

Intended role: Provide character-specific guidance for responding to emotionally charged cues (what to amplify, what to avoid), grounded in CDL and real-time emotion signals.

Existing assets:
- RoBERTa emotion analysis already integrated (`src/intelligence/enhanced_vector_emotion_analyzer.py`) and stored as metadata per message.
- InfluxDB trajectory concepts referenced for longer-term emotional trends, though the pipeline for combining with prompts is not finalized.
- `character_emotional_triggers` table exists in PostgreSQL (created in legacy SQL migrations).
- `EnhancedCDLManager.get_emotional_triggers()` API already implemented and available.

Blockers:
- CDL table schema may not match current component requirements (needs validation).
- No component factory combining trigger guidance with recent emotion trajectory and current message analysis.
- Designer workflow for populating emotional triggers not established (are these per-character universal rules, or dynamically inferred?).

Design questions requiring architectural decisions:
- Are emotional triggers designer-authored CDL data (static per character) or dynamically inferred from user interaction patterns?
- Should triggers be conditional on recent emotional trajectory (InfluxDB) or just current message emotion (RoBERTa)?
- How do we prevent trigger guidance from conflicting with RESPONSE_STYLE component (Priority 17) which also guides tone?
- What granularity is appropriate? Per-emotion triggers (sadness → validation) or complex combinations (sadness + frustration → specific strategy)?
- Should this be real-time (every message) or strategic (enrichment worker identifies emotional patterns over time)?

Possible approach (requires validation):
- Leverage existing `character_emotional_triggers` table and `get_emotional_triggers()` API.
- Component factory:
  - `create_emotional_triggers_component(bot_name, recent_emotion_trajectory, current_emotion_inference, priority=12)` that outputs concise guidance (“If user shows sadness + frustration, use validating language and avoid prescriptive tone”).
- Integration:
  - Leverage existing RoBERTa outputs and any available trajectory metadata; pass into the factory from `message_processor`.

Acceptance criteria (tentative):
- When triggers exist, component outputs <= 150 tokens of concrete guidance aligned with the character's style.
- No triggers -> component omitted and no assembly errors.

Risks and open questions:
- Overfitting or rigidity: Keep guidance general and character-aligned; rely on RESPONSE_STYLE for stylistic nuance.
- Token pressure: Keep it terse and allow assembler to drop at lower priority if needed.
- Redundancy with RESPONSE_STYLE: Ensure triggers provide emotional-specific guidance without duplicating character voice/style.
- Real-time performance: If trajectory analysis is complex, consider caching or moving to enrichment worker.

---

## Implementation order and milestones

**These are NOT prescriptive steps—they represent possible sequencing IF the design decisions above are resolved in favor of implementation.**

1) USER_PERSONALITY (P7)
   - Finalize trait taxonomy and inference approach.
   - Add retrieval API + factory; bootstrap from `universal_users.preferences`.
   - Ship without new tables; iterate heuristics.

2) EMOTIONAL_TRIGGERS (P12)
   - Validate existing `character_emotional_triggers` table schema against component requirements.
   - Establish designer workflow for populating triggers (or decide on inference approach).
   - Add component factory using current RoBERTa + optional trajectories.
   - Keep guidance compact to minimize token footprint.

3) CHARACTER_LEARNING (P9)
   - Decide on real-time vs. strategic execution path.
   - Add tables + extractor/storage services; initialize in bot DI.
   - Start with manual curation or simple rules before LLM summarization.

---

## Contracts summary (tiny)

**Note: These are tentative contracts subject to design validation.**

- Inputs:
  - bot_name, user_id, current message (text + emotion inference), optional trajectories.
- Outputs:
  - PromptComponent content strings suitable for the assembler with strict token budgets.
- Error modes:
  - Missing data -> omit component without failing prompt assembly.

---

## Next steps

**This document is a starting point for architectural discussion, NOT a ready-to-implement specification.**

- Schedule design review sessions for each component with stakeholders (product, eng, design).
- Prototype one component end-to-end (USER_PERSONALITY recommended as simplest) to validate approach.
- Establish testing criteria: A/B test impact on engagement, satisfaction, character authenticity metrics.
- Define privacy and user consent requirements for personality inference.
- Document trade-offs between real-time and strategic execution paths with performance benchmarks.
- Validate existing CDL table schemas against proposed component requirements (EMOTIONAL_TRIGGERS).
- Create minimal viable implementation plans AFTER design decisions are finalized.
