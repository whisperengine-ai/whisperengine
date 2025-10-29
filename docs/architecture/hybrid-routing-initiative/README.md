# Hybrid Query Routing Initiative

**Status:** ✅ **IMPLEMENTATION COMPLETE - PRODUCTION READY**  
**Priority:** High - Foundation for Advanced Techniques  
**Timeline:** Week 1 Complete (October 27, 2025)

---

## 📋 Overview

The **Hybrid Query Routing Initiative** introduces intelligent LLM tool calling capabilities to WhisperEngine, enabling characters to dynamically access structured data (user facts, character backstory, conversation history) through natural language queries.

### ✅ Implementation Status

**All 13 tasks completed successfully!**
- ✅ **Architecture**: Extended existing UnifiedQueryClassifier + SemanticKnowledgeRouter
- ✅ **All 5 Tools**: Fully implemented and tested
- ✅ **Integration**: MessageProcessor successfully integrated with tool system
- ✅ **Validation**: HTTP API testing complete, 3 critical bugs fixed
- ✅ **Testing**: Comprehensive test suite (unit + integration)
- ✅ **Documentation**: Complete and up-to-date

### Core Architecture (As Implemented)

**Hybrid Routing Strategy:** 80% semantic routing (10-50ms) / 20% LLM tool calling (3-6 seconds)
- **Complexity Threshold:** 0.3 (configurable)
- **Decision Point:** `UnifiedQueryClassifier._assess_tool_complexity()`
- **Integration:** Extended existing systems (no duplicate classification logic)
- **Fallback:** Semantic routing always available (graceful degradation)

### Key Benefits

1. **Intelligent Data Access**: Characters query structured data (PostgreSQL CDL, user facts, conversation history) using natural language
2. **Cost Efficiency**: 80% of queries route to fast semantic search, 20% to LLM tool calling
3. **Foundation for Advanced Techniques**: Enables bot self-memory, active learning, adaptive context, and 6 other advanced techniques
4. **Production Ready**: All tools working, integration bugs fixed, validated with Elena bot
5. **Zero Architectural Debt**: Extended existing systems, eliminated 345 lines of code

---

## 📚 Documentation Structure

### 1. [HYBRID_QUERY_ROUTING_DESIGN.md](./HYBRID_QUERY_ROUTING_DESIGN.md) - Foundation Design
**Purpose:** Complete architectural specification for the hybrid routing system  
**Contents:**
- `HybridQueryRouter` class design and API
- Complexity assessment algorithm (sentence length, question words, entity references)
- 5 Core Tool Definitions (query_user_facts, recall_conversation_context, query_character_backstory, summarize_user_relationship, query_temporal_trends)
- Performance analysis with latency comparison tables
- 4-stage migration path (Weeks 1-4)

**Read this first** - establishes the foundation for all other documents.

---

### 2. [TOOL_CALLING_USE_CASES_DETAILED.md](./TOOL_CALLING_USE_CASES_DETAILED.md) - Use Case Scenarios
**Purpose:** 4 detailed scenarios showing when and why to use LLM tool calling  
**Contents:**
- **Use Case 1:** Character Self-Reflection & Learning (4 tools: reflect_on_interaction, analyze_self_performance, adapt_personality_trait, record_self_insight) - [CONCRETE TOOL]
- **Use Case 2:** Complex Multi-Step Analysis (3 tools: multi-step patterns like analyze_conversation_evolution, identify_recurring_patterns, predict_user_needs) - [EXAMPLE PATTERN]
- **Use Case 3:** User Relationship Summarization (1 tool: summarize_user_relationship) - [CONCRETE TOOL]
- **Use Case 4:** Temporal Trend Analysis (1 tool: query_temporal_trends) - [CONCRETE TOOL]

**Tool Labeling Convention:**
- `[CONCRETE TOOL]` = Must implement (10 tools total)
- `[EXAMPLE PATTERN]` = Implementation reference (3 tools)

**Read this second** - shows practical applications of the hybrid routing system.

---

### 3. [ADVANCED_TECHNIQUES_ARCHITECTURE.md](./ADVANCED_TECHNIQUES_ARCHITECTURE.md) - Advanced Techniques
**Purpose:** 9 advanced techniques building on hybrid routing foundation  
**Contents:**

#### Technique 0: Bot Self-Memory (Foundation)
- **6 Bot Self-Memory Tools:** query_character_backstory, reflect_on_interaction, analyze_self_performance, adapt_personality_trait, record_self_insight, analyze_conversation_patterns
- **Shared Tool:** `query_character_backstory` (source parameter: cdl_database | self_memory | both)
- **Refactoring Required:** Migrate bot_self_memory_system.py from JSON to PostgreSQL

#### Techniques 1-8:
1. **Cross-Encoder Re-Ranking** - Improve memory retrieval precision
2. ~~**Prompt Caching**~~ (REMOVED - not applicable for WhisperEngine's dynamic prompts)
3. **Shared World Memory** - Cross-character knowledge (e.g., news events, public facts)
4. **Guardrails** - Safety, format compliance, character authenticity
5. **Chain-of-Thought (CoT)** - Expose reasoning process for complex queries
6. **Active Learning** - Bot-initiated clarification questions (depends on Bot Self-Memory)
7. **Adaptive Context** - Dynamic token budget allocation based on query complexity
8. **A/B Testing** - Compare routing strategies (semantic vs tool calling vs hybrid)

**Dependency Matrix:**
- **CRITICAL Dependency:** Hybrid Query Router (Technique 0 prerequisite)
- **Bot Self-Memory → Active Learning** (personality insights needed for intelligent questions)
- **All Techniques Independent** (except Active Learning)

**Read this third** - extends the hybrid routing system with advanced capabilities.

---

### 4. [ARCHITECTURAL_ALIGNMENT_REVIEW.md](./ARCHITECTURAL_ALIGNMENT_REVIEW.md) - Consistency Analysis
**Purpose:** Comprehensive cross-document consistency validation  
**Contents:**
- **Tool Definition Consistency Matrix:** 10 unique tools analyzed across all documents
- **Dependency Chain Validation:** 4-layer dependency graph (Infrastructure → Hybrid Router → Bot Self-Memory → Advanced Techniques)
- **3 Issues Identified + Resolutions:**
  1. ✅ Tool name collision (query_character_backstory) - **RESOLVED** with "source" parameter
  2. ✅ Missing 4 self-reflection tools in Advanced Techniques - **RESOLVED** by adding to Technique 0
  3. ✅ Unclear tool status (concrete vs example) - **RESOLVED** with `[CONCRETE TOOL]` / `[EXAMPLE PATTERN]` labels
- **Implementation Roadmap Consistency:** 7-week timeline validated across all documents

**Final Result:** 100% architectural consistency across all documents

**Read this fourth** - validates that all documents are aligned and ready for implementation.

---

## 🛠️ Implementation Roadmap

### Week 1-2: Foundation (HybridQueryRouter)
- Implement `HybridQueryRouter` class with complexity assessment
- Integrate 5 core tools (query_user_facts, recall_conversation_context, query_character_backstory, summarize_user_relationship, query_temporal_trends)
- Add to `MessageProcessor.process_message()` pipeline

### Week 3-4: Bot Self-Memory (Technique 0)
- Refactor `bot_self_memory_system.py` (468 lines) from JSON → PostgreSQL
- Implement 6 bot self-memory tools (shared query_character_backstory + 5 self-reflection tools)
- Add self-reflection triggers to `MessageProcessor`

### Week 5: Testing & Validation
- Automated testing with HTTP chat API (`http://localhost:{BOT_PORT}/api/chat`)
- Test with Jake/Ryan bots (minimal personality) for memory validation
- Test with Elena bot (rich CDL personality) for personality/CDL validation

### Week 6-7: Advanced Techniques (Techniques 1-8)
- Implement prioritized techniques (Cross-Encoder Re-Ranking, Prompt Caching, etc.)
- A/B testing framework for routing strategies
- Performance optimization and production rollout

---

## 🚨 Critical Constraints

### QDRANT SCHEMA IS FROZEN
- **WhisperEngine has PRODUCTION USERS** - schema changes break existing data
- **NEVER change:** vector dimensions (384D), named vector names (content/emotion/semantic), payload field types
- **ADDITIVE ONLY:** You MAY add NEW optional payload fields, but NEVER remove/rename existing
- **Collection Per Bot:** Each character has dedicated collection (whisperengine_memory_{bot_name})

### CHARACTER-AGNOSTIC DEVELOPMENT
- **NO hardcoded character names** in Python code - use dynamic loading
- **NO personality assumptions** - all character data from PostgreSQL CDL database
- **Characters loaded:** via `DISCORD_BOT_NAME` environment variable from database

### NO FEATURE FLAGS FOR LOCAL CODE
- **ONLY use feature flags for REMOTE/EXTERNAL dependencies** (APIs, external services)
- **NEVER use feature flags for LOCAL code dependencies** - creates spaghetti conditionals
- Environment variables are for infrastructure config ONLY (database URLs, API keys)

---

## 📊 Tool Registry

### 10 Concrete Tools (Must Implement)

#### 5 Core Hybrid Router Tools
1. `query_user_facts` - Query PostgreSQL user_fact_relationships table
2. `recall_conversation_context` - Query Qdrant conversation history with semantic search
3. `query_character_backstory` - Query PostgreSQL CDL database for character facts [SHARED with Bot Self-Memory]
4. `summarize_user_relationship` - Aggregate user facts + conversation history for relationship summary
5. `query_temporal_trends` - Query InfluxDB for conversation quality metrics over time

#### 5 Bot Self-Memory Tools (Self-Reflection)
6. `reflect_on_interaction` - Analyze recent conversation for learning insights
7. `analyze_self_performance` - Review conversation quality metrics (InfluxDB)
8. `adapt_personality_trait` - Adjust character personality based on feedback
9. `record_self_insight` - Store character learning moments
10. `analyze_conversation_patterns` - Identify recurring themes in conversations

### 3 Example Pattern Tools (Implementation Reference)
1. `analyze_conversation_evolution` - Multi-step analysis pattern
2. `identify_recurring_patterns` - Multi-step analysis pattern
3. `predict_user_needs` - Multi-step analysis pattern

---

## 🧪 Testing Strategy

### Direct Python Validation (PREFERRED)
```bash
source .venv/bin/activate && \
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
export QDRANT_HOST="localhost" && \
export QDRANT_PORT="6334" && \
export POSTGRES_HOST="localhost" && \
export POSTGRES_PORT="5433" && \
export DISCORD_BOT_NAME=elena && \
python tests/automated/test_hybrid_routing.py
```

### HTTP Chat API Testing (Automation)
```bash
# Test Elena bot (rich CDL personality)
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_12345",
    "message": "What do you remember about me?",
    "metadata": {"platform": "api_test", "channel_type": "dm"}
  }'

# Test Jake bot (minimal personality - good for memory testing)
curl -X POST http://localhost:9097/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_67890",
    "message": "Tell me about yourself",
    "metadata": {"platform": "api_test", "channel_type": "dm"}
  }'
```

### Bot Selection for Testing
- **Memory Testing:** Use Jake (port 9097) or Ryan (port 9093) - minimal personality complexity
- **Personality/CDL Testing:** Use Elena (port 9091) - richest CDL personality
- **CDL Mode Switching:** Use Mistral models for better compliance

---

## 🔗 Related Documentation

### Infrastructure
- `docs/architecture/README.md` - Current architecture overview
- `.github/copilot-instructions.md` - Critical system constraints and development patterns
- `docs/architecture/WHISPERENGINE_ARCHITECTURE_EVOLUTION.md` - Evolution timeline

### Testing & Development
- `docs/testing/DIRECT_PYTHON_TESTING_GUIDE.md` - Testing methodology
- `CHARACTER_TUNING_GUIDE.md` - Character configuration
- `QUICK_REFERENCE.md` - Development quick start

### Historical Context
- `docs/architecture/TOOL_CALLING_CLEANUP_COMPLETE.md` - Infrastructure cleanup (533 lines deleted)
- `docs/roadmaps/MEMORY_INTELLIGENCE_CONVERGENCE_ROADMAP.md` - Character learning roadmap
- `docs/roadmaps/CDL_INTEGRATION_COMPLETE_ROADMAP.md` - Character system progress

---

## 🚀 Getting Started

1. **Read HYBRID_QUERY_ROUTING_DESIGN.md** - Understand the foundation
2. **Review TOOL_CALLING_USE_CASES_DETAILED.md** - See practical applications
3. **Scan ADVANCED_TECHNIQUES_ARCHITECTURE.md** - Explore future capabilities
4. **Validate with ARCHITECTURAL_ALIGNMENT_REVIEW.md** - Confirm architectural consistency
5. **Start Week 1 Implementation** - Build `HybridQueryRouter` class

---

**Questions?** Reference `.github/copilot-instructions.md` for critical system constraints and development patterns.

**Ready to implement?** Start with `src/intelligence/hybrid_query_router.py` (create new file) and integrate into `src/core/message_processor.py`.
