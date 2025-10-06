# WhisperEngine Naming Refactoring Plan

## 🚨 PROBLEM: Development Phase Names in Production Code

**Issue**: Code contains development-phase names like "sprint1", "sprint2", "sprint3", "phase4", etc. This creates confusion and makes the codebase harder to understand. These names describe WHEN features were built, not WHAT they do.

**Goal**: Replace all sprint/phase-based names with semantic, domain-driven names that describe functionality.

---

## Naming Conversion Map

### Feature-Level Names

| Current Name | New Semantic Name | Description |
|--------------|-------------------|-------------|
| **Sprint 1: TrendWise** | `conversation_quality_tracking` | Conversation quality analysis and confidence trends |
| **Sprint 2: MemoryBoost** | `emotion_analysis_enhancement` | RoBERTa emotion metadata and multi-vector memory |
| **Sprint 3: RelationshipTuner** | `relationship_evolution` | Dynamic relationship scoring and trust recovery |
| **Phase 3** | `memory_clustering` | OBSOLETED - functionality replaced by PostgreSQL |
| **Phase 4** | `conversation_intelligence` | Conversation intelligence and AI components |
| **Phase 5** | `temporal_intelligence` | Time-aware metrics and InfluxDB integration |

### Variable/Dictionary Key Names

| Current Name | New Name | Context |
|--------------|----------|---------|
| `sprint3_relationship` | `relationship_state` | Relationship scores (trust, affection, attunement) |
| `sprint1_confidence` | `conversation_confidence` | Conversation quality and confidence metrics |
| `sprint2_roberta` | `emotion_analysis` | RoBERTa emotion detection metadata |
| `phase4_intelligence` | `conversation_intelligence` | AI conversation components |
| `phase3_memory` | ❌ OBSOLETE | Removed - use PostgreSQL semantic knowledge graph |

### File/Module Names

#### Already Good (No Changes Needed) ✅
- `src/relationships/evolution_engine.py` - Semantic name ✅
- `src/relationships/trust_recovery.py` - Semantic name ✅
- `src/analytics/trend_analyzer.py` - Semantic name ✅
- `src/temporal/temporal_intelligence_client.py` - Semantic name ✅
- `src/intelligence/enhanced_vector_emotion_analyzer.py` - Semantic name ✅

#### Need Renaming 🔄
- ✅ `scripts/migrations/sprint3_relationship_tuner_schema.py` → `scripts/migrations/relationship_evolution_schema.py`
- ✅ `tests/automated/test_sprint3_relationship_tuner_validation.py` → `tests/automated/test_relationship_evolution_validation.py`
- ✅ `tests/automated/test_sprint_1_3_e2e_jake.py` → `tests/automated/test_adaptive_learning_e2e_jake.py`
- ✅ `tests/automated/test_sprint_1_3_e2e_elena.py` → `tests/automated/test_adaptive_learning_e2e_elena.py`
- ✅ `tests/automated/test_sprint2_complete_validation.py` → `tests/automated/test_memoryboost_complete_validation.py`
- ✅ `tests/automated/test_sprint2_roberta_validation.py` → `tests/automated/test_roberta_emotion_validation.py`

### Database Schema Names

#### Already Good ✅
- `relationship_scores` - Semantic table name ✅
- `relationship_events` - Semantic table name ✅
- `trust_recovery_state` - Semantic table name ✅

#### Need Updating 🔄
- Column references to "sprint" in comments/metadata should be updated

### Class/Method Names

| Current Name | New Name | File |
|--------------|----------|------|
| `_enrich_ai_components_with_adaptive_learning()` | ✅ Good - keep as is | message_processor.py |
| `RelationshipEvolutionEngine` | ✅ Good - keep as is | evolution_engine.py |
| `TrustRecoverySystem` | ✅ Good - keep as is | trust_recovery.py |
| `TrendAnalyzer` | ✅ Good - keep as is | trend_analyzer.py |

### Log Messages

| Current Pattern | New Pattern |
|----------------|-------------|
| `🎯 SPRINT 3 PROMPT: Added relationship scores` | `🎯 RELATIONSHIP: Added relationship scores to prompt` |
| `🔄 SPRINT 3: Relationship updated` | `🔄 RELATIONSHIP: Trust/affection/attunement updated` |
| `📊 SPRINT 1: Added confidence data` | `📊 CONFIDENCE: Added conversation quality metrics` |
| `🎯 SPRINT 3: Added relationship data to pipeline` | `🎯 RELATIONSHIP: Added relationship state to pipeline` |

---

## Implementation Priority

### Phase 1: High-Impact Variable Names (PRIORITY) 🔥
1. **Dictionary keys in ai_components and pipeline_result**
   - `sprint3_relationship` → `relationship_state`
   - `sprint1_confidence` → `conversation_confidence`
   - Impact: Core data flow throughout application
   - Files: `message_processor.py`, `cdl_ai_integration.py`, test files

2. **Log messages**
   - Replace "SPRINT X" with semantic labels
   - Impact: Developer debugging and monitoring
   - Files: `message_processor.py`, `evolution_engine.py`, `trust_recovery.py`

### Phase 2: File/Module Names
1. **Test files** - Rename sprint-based test files
2. **Migration scripts** - Rename sprint-based migration files
3. **Documentation** - Update references in markdown docs

### Phase 3: Documentation Updates
1. **README updates** - Remove sprint/phase references
2. **Architecture docs** - Use semantic feature names
3. **Copilot instructions** - Add anti-pattern guidance

---

## Anti-Pattern Guidance for Future Development

### ❌ AVOID: Development Phase Names
- sprint1, sprint2, sprint3, sprint4, etc.
- phase1, phase2, phase3, phase4, etc.
- iteration1, iteration2, etc.
- v1_feature, v2_feature, etc.

### ✅ PREFER: Semantic, Domain-Driven Names
- `relationship_evolution` (describes WHAT it does)
- `conversation_quality_tracking` (describes WHAT it tracks)
- `emotion_analysis_enhancement` (describes WHAT it enhances)
- `trust_recovery` (describes WHAT it recovers)

### Naming Principles
1. **Describe functionality, not history** - Names should explain what code does, not when it was built
2. **Domain language** - Use terms from the problem domain (relationships, conversations, emotions)
3. **Intent-revealing** - Reader should understand purpose without looking at implementation
4. **Timeless** - Names should remain accurate as codebase evolves

### Examples of Good vs Bad Names

| ❌ Bad (Phase-Based) | ✅ Good (Semantic) | Why Better? |
|---------------------|-------------------|-------------|
| `sprint3_data` | `relationship_state` | Describes what data represents |
| `phase4_processor` | `conversation_intelligence_analyzer` | Describes what it processes |
| `sprint1_metrics` | `conversation_quality_metrics` | Describes what it measures |
| `_update_sprint3_scores()` | `_update_relationship_scores()` | Describes what it updates |

---

## Migration Strategy

### Step 1: Backward-Compatible Transition
1. Add new semantic names alongside old names
2. Update all new code to use semantic names
3. Add deprecation warnings to old names
4. Document migration path

### Step 2: Gradual Rollout
1. Update core data flow (ai_components, pipeline_result)
2. Update log messages for better debugging
3. Rename test files and migration scripts
4. Update documentation last

### Step 3: Clean Removal
1. Remove deprecated sprint/phase names
2. Update all references in tests
3. Final documentation sweep

---

## Immediate Action Items

1. ✅ **Document Sprint 1-3 completion** - Update SPRINT_3_RELATIONSHIPTUNER_COMPLETE.md
2. 🔄 **Start variable renaming** - Begin with dictionary keys in message_processor.py
3. 🔄 **Update log messages** - Replace "SPRINT X" with semantic labels
4. 📝 **Update copilot instructions** - Add anti-pattern guidance
5. 📝 **Create migration guide** - Help developers transition existing code

---

## Success Criteria

✅ No references to "sprint1", "sprint2", "sprint3" in production code  
✅ No references to "phase3", "phase4" in production code  
✅ All dictionary keys use semantic names  
✅ All log messages use semantic labels  
✅ Test files use descriptive feature names  
✅ Documentation updated with semantic terminology  
✅ Copilot instructions include anti-pattern guidance  

---

**Estimated Effort**: 4-6 hours for complete refactoring  
**Risk Level**: Low (mostly find/replace with testing)  
**Priority**: High (code quality and maintainability)

---

## Notes

- **Database schema** is already mostly semantic (relationship_scores, relationship_events, trust_recovery_state) ✅
- **Core classes** already use semantic names (RelationshipEvolutionEngine, TrustRecoverySystem) ✅
- **Main issue** is in variable names, dictionary keys, and log messages
- **Test files** and **migration scripts** need file-level renaming
