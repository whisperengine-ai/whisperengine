# Hybrid Query Routing - Implementation Roadmap Tracker

**Branch:** `feature/hybrid-query-routing`  
**Started:** October 27, 2025  
**Status:** 🟡 Week 1 In Progress  
**Overall Progress:** 40% Complete

---

## 📊 Weekly Progress Overview

| Week | Focus Area | Status | Completion |
|------|-----------|--------|------------|
| Week 1-2 | Foundation (HybridQueryRouter + 5 Tools) | 🟡 In Progress | 60% |
| Week 3-4 | Bot Self-Memory (Technique 0) | ⚪ Not Started | 0% |
| Week 5 | Testing & Validation | ⚪ Not Started | 0% |
| Week 6-7 | Advanced Techniques (1-8) | ⚪ Not Started | 0% |

---

## ✅ Completed Tasks

### Documentation & Planning
- ✅ **[Oct 27]** Created `docs/architecture/hybrid-routing-initiative/` folder
- ✅ **[Oct 27]** Moved 4 architecture documents to organized location
- ✅ **[Oct 27]** Created comprehensive README.md with initiative overview
- ✅ **[Oct 27]** All documents architecturally aligned (100% consistency)

### Week 1: Foundation Implementation
- ✅ **[Oct 27]** Created `src/intelligence/hybrid_query_router.py` (499 lines)
  - Complexity assessment algorithm (sentence length, question words, entity references)
  - Configurable threshold (default: 0.3) for 80/20 routing
  - 5 core tool definitions in OpenAI function calling format
  - `should_use_tools()` method for routing decisions
  - Comprehensive logging and A/B testing support

- ✅ **[Oct 27]** Created `src/intelligence/tool_executor.py` (527 lines)
  - **Tool 1: query_user_facts** ✅ COMPLETE
    - Queries PostgreSQL user_fact_relationships + fact_entities
    - Filters enrichment markers (_processing_marker)
    - Returns facts with confidence scores
  
  - **Tool 2: recall_conversation_context** ✅ COMPLETE
    - Uses existing VectorMemorySystem.retrieve_relevant_memories()
    - Semantic search with time window filtering (24h|7d|30d|all)
    - Returns formatted memories with emotion analysis
  
  - **Tool 4: summarize_user_relationship** ✅ COMPLETE
    - Multi-source aggregation (PostgreSQL + Qdrant)
    - Combines user facts and conversation history
    - Comprehensive relationship summary

### Git Commits
```
b54056b - feat: Organize hybrid query routing architecture documentation
fb9854e - feat: Create HybridQueryRouter foundation class
77733bc - feat: Implement ToolExecutor with 5 core tools
```

---

## 🔄 In Progress

### Week 1: Integration & Testing (Current Sprint)
- 🔄 **Integration with MessageProcessor**
  - Adding HybridQueryRouter to message processing pipeline
  - Connecting LLM client for tool calling
  - Inserting after memory retrieval, before LLM generation

- 🔄 **Initial Testing**
  - Direct Python validation tests
  - HTTP chat API testing
  - Complexity assessment validation

### Partially Complete Tools
- ⚠️ **Tool 3: query_character_backstory** - PLACEHOLDER
  - Requires CDL table schema analysis (53+ character_* tables)
  - Will query character_background, identity_details, interests, etc.
  - Can use existing SimpleCDLManager/EnhancedCDLManager patterns

- ⚠️ **Tool 5: query_temporal_trends** - PLACEHOLDER
  - Requires InfluxDB schema analysis
  - Will query conversation_quality measurement
  - Time-series metrics for engagement, satisfaction, coherence

---

## 📋 Upcoming Tasks

### Week 1-2: Foundation Completion
- [ ] Complete Tool 3 (query_character_backstory)
  - Analyze CDL database schema
  - Implement PostgreSQL queries for character data
  - Handle both cdl_database and self_memory sources
  
- [ ] Complete Tool 5 (query_temporal_trends)
  - Analyze InfluxDB schema (conversation_quality measurement)
  - Implement time-series queries
  - Format temporal trend data

- [ ] MessageProcessor Integration
  - Add complexity assessment before LLM generation
  - Route to tools if threshold met
  - Add tool results to conversation context
  - Fallback to semantic routing

- [ ] Automated Test Suite
  - Create `tests/automated/test_hybrid_routing.py`
  - Test complexity assessment algorithm
  - Test tool routing and execution
  - Test fallback to semantic routing
  - HTTP chat API automation tests

- [ ] Multi-Bot Testing
  - Test with Jake/Ryan (minimal personality - memory testing)
  - Test with Elena (rich personality - CDL testing)
  - Validate tool calling across different character types

### Week 3-4: Bot Self-Memory (Technique 0)
- [ ] Refactor `bot_self_memory_system.py` (468 lines)
  - Replace JSON parsing with asyncpg queries
  - Query character_* tables (PostgreSQL)
  - Use EnhancedCDLManager patterns
  - Maintain existing method structure

- [ ] Implement 6 Bot Self-Memory Tools
  - `query_character_backstory` (shared - already exists)
  - `reflect_on_interaction` - Analyze recent conversation
  - `analyze_self_performance` - Review metrics
  - `adapt_personality_trait` - Adjust based on feedback
  - `record_self_insight` - Store learning moments
  - `analyze_conversation_patterns` - Identify themes

- [ ] Integrate Self-Memory into MessageProcessor
  - Add self-reflection triggers
  - Store insights in PostgreSQL
  - Use insights in future conversations

### Week 5: Testing & Validation
- [ ] Comprehensive Testing
  - All 5 core tools across 3 bots
  - Bot self-memory tools validation
  - Performance benchmarking (latency comparison)
  - Complexity threshold tuning (0.2, 0.3, 0.4, 0.5)

- [ ] A/B Testing Framework
  - Compare semantic routing vs tool calling
  - Compare hybrid (80/20) vs pure strategies
  - Measure latency, accuracy, user satisfaction

- [ ] Production Readiness
  - Error handling validation
  - Logging and monitoring
  - Performance optimization
  - Documentation updates

### Week 6-7: Advanced Techniques (Techniques 1-8)
- [ ] Prioritize techniques for implementation
- [ ] Implement selected techniques:
  - Cross-Encoder Re-Ranking
  - Prompt Caching
  - Shared World Memory
  - Guardrails
  - Chain-of-Thought (CoT)
  - Active Learning (depends on Bot Self-Memory)
  - Adaptive Context
  - A/B Testing framework

---

## 🚨 Blockers & Risks

### Current Blockers
- ⚠️ **Tool 3 (CDL):** Requires understanding of 53+ character_* table schema
  - **Mitigation:** Use existing SimpleCDLManager patterns, analyze schema incrementally
  
- ⚠️ **Tool 5 (InfluxDB):** Requires InfluxDB schema knowledge
  - **Mitigation:** Can implement later, not critical for initial testing

### Technical Risks
- **Qdrant Schema Frozen:** NO breaking changes allowed (production users)
  - **Status:** ✅ No schema changes needed - using existing infrastructure
  
- **LLM Tool Calling Latency:** 1500-3500ms vs 10-50ms semantic search
  - **Mitigation:** 80/20 routing strategy, complexity threshold tuning
  
- **Bot Self-Memory Refactoring:** 468 lines of JSON parsing to PostgreSQL
  - **Mitigation:** Incremental refactor, reuse existing method structure

---

## 📈 Metrics & Success Criteria

### Week 1-2 Success Criteria
- ✅ HybridQueryRouter complexity assessment working
- ✅ 3/5 tools fully functional (query_user_facts, recall_conversation_context, summarize_user_relationship)
- 🔄 Integration with MessageProcessor complete
- 🔄 Initial tests passing (complexity assessment, tool routing)
- ⚠️ 2/5 tools pending (query_character_backstory, query_temporal_trends)

### Week 3-4 Success Criteria
- bot_self_memory_system.py refactored to PostgreSQL
- 6 bot self-memory tools functional
- Self-reflection integrated into message pipeline
- Bot learning insights stored in database

### Week 5 Success Criteria
- All 5 core tools tested across 3 bots
- Performance benchmarks meet targets (80% <50ms, 20% <3500ms)
- Complexity threshold tuned for optimal routing
- A/B testing shows improvement over pure semantic routing

### Week 6-7 Success Criteria
- 3+ advanced techniques implemented
- Production deployment ready
- Documentation complete and up-to-date
- User satisfaction metrics improved

---

## 🔧 Technical Debt

### Known Issues
1. **Tool 3 Placeholder:** query_character_backstory needs CDL implementation
2. **Tool 5 Placeholder:** query_temporal_trends needs InfluxDB implementation
3. **bot_self_memory_system.py:** Uses outdated JSON parsing instead of PostgreSQL
4. **No Automated Tests Yet:** Need comprehensive test suite

### Future Improvements
1. **Caching:** Add prompt caching for CDL data (Technique 2)
2. **Cross-Encoder:** Improve memory retrieval precision (Technique 1)
3. **Guardrails:** Add safety and format compliance (Technique 4)
4. **Active Learning:** Bot-initiated clarification questions (Technique 6)

---

## 📝 Notes & Decisions

### Key Decisions Made
- **Oct 27:** Start Week 1 implementation immediately (don't wait for bot_self_memory refactor)
- **Oct 27:** Test with 3 bots (Jake/Ryan for memory, Elena for personality)
- **Oct 27:** Implement all 5 tools in Week 1 (complete foundation)
- **Oct 27:** Use incremental refactor approach for bot_self_memory_system.py

### Architecture Decisions
- **Hybrid Routing Strategy:** 80% semantic (fast) / 20% tool calling (accurate)
- **Complexity Threshold:** Default 0.3, configurable for A/B testing
- **Tool Naming:** query_character_backstory shared between Hybrid Router and Bot Self-Memory
  - Uses "source" parameter (cdl_database | self_memory | both)
- **No Feature Flags:** Tools work by default, use enable_tool_calling flag only for A/B testing

### Implementation Patterns
- **Protocol-Based:** Uses existing factory patterns (LLM client, memory system)
- **Character-Agnostic:** All tools use dynamic character loading via environment variables
- **Database-Driven:** PostgreSQL CDL system is single source of truth
- **Vector-Native:** Qdrant collections per bot for complete isolation

---

## 🎯 Current Sprint Focus (Week 1)

**Sprint Goal:** Complete foundation and initial integration

**This Week (Oct 27 - Nov 2):**
1. ✅ Create HybridQueryRouter class
2. ✅ Implement 3/5 tools (query_user_facts, recall_conversation_context, summarize_user_relationship)
3. 🔄 Integrate with MessageProcessor
4. 🔄 Create initial test suite
5. 🔄 Test with HTTP chat API
6. ⏳ Complete Tool 3 (CDL) and Tool 5 (InfluxDB) - if time permits

**Stretch Goals:**
- Start bot_self_memory_system.py refactoring
- Implement Tool 3 (query_character_backstory)
- Performance benchmarking

---

## 📚 Reference Documents

**Primary Documents:**
- [HYBRID_QUERY_ROUTING_DESIGN.md](./HYBRID_QUERY_ROUTING_DESIGN.md) - Foundation design
- [TOOL_CALLING_USE_CASES_DETAILED.md](./TOOL_CALLING_USE_CASES_DETAILED.md) - Use case scenarios
- [ADVANCED_TECHNIQUES_ARCHITECTURE.md](./ADVANCED_TECHNIQUES_ARCHITECTURE.md) - 9 advanced techniques
- [ARCHITECTURAL_ALIGNMENT_REVIEW.md](./ARCHITECTURAL_ALIGNMENT_REVIEW.md) - Consistency validation

**Implementation Files:**
- `src/intelligence/hybrid_query_router.py` - Core routing logic
- `src/intelligence/tool_executor.py` - Tool execution
- `src/core/message_processor.py` - Integration point
- `tests/automated/test_hybrid_routing.py` - Test suite (to be created)

**Related Documentation:**
- `.github/copilot-instructions.md` - Critical constraints and patterns
- `docs/architecture/README.md` - Architecture overview
- `docs/testing/DIRECT_PYTHON_TESTING_GUIDE.md` - Testing methodology

---

**Last Updated:** October 27, 2025  
**Next Review:** November 2, 2025 (End of Week 1)
