# Hybrid Query Routing Design Document

**Date**: October 27, 2025  
**Status**: ⚠️ **DESIGN PHASE - PARTIALLY IMPLEMENTED**  
**Author**: WhisperEngine Architecture  
**Target**: Multi-Bot Production Platform (10+ characters)

---

## ⚠️ IMPLEMENTATION STATUS DISCLAIMER

**This document contains BOTH design concepts and actual implementation details.**

### ✅ What Was Actually Implemented (October 2025):
- **SemanticKnowledgeRouter** with 10 LLM-callable tools (5 foundation + 5 self-reflection)
- **Tool execution pipeline** in MessageProcessor (LLM decides which tools to call)
- **Single master switch**: `ENABLE_LLM_TOOL_CALLING` environment variable
- **PostgreSQL + Qdrant + InfluxDB** hybrid data storage working
- **Bot self-reflection system** with dedicated PostgreSQL table + Qdrant namespace

### ❌ What Was NOT Implemented (Design Concepts Only):
- **Complexity-based routing threshold** (no automatic fast/intelligent path selection)
- **`ENABLE_HYBRID_ROUTING` flag** (not used in code)
- **`ENABLE_SEMANTIC_ROUTER` flag** (not used in code)
- **Per-character routing configuration** (no `routing_config.yaml`)
- **HybridQueryRouter class** (design only - not coded)
- **Automatic query complexity assessment** (no _assess_query_complexity() method)

### 🎯 Actual Behavior:
- When `ENABLE_LLM_TOOL_CALLING=true`: LLM has access to all 10 tools, decides when to use them
- When `ENABLE_LLM_TOOL_CALLING=false`: No tools available, standard conversation only
- No automatic "fast path" vs "intelligent path" routing (LLM makes all tool decisions)

**Read this document as a design reference, not implementation documentation.**

---

## 🎯 Executive Summary

**Problem**: Current semantic routing works well but lacks flexibility for complex queries. Full LLM tool calling would add 2-3x latency for simple queries.

**Solution**: Hybrid routing system that uses **semantic routing for speed** (80% of queries) and **LLM tool calling for intelligence** (20% of queries).

**Impact**:
- ✅ Maintains current performance for simple queries (800-2000ms)
- ✅ Enables complex multi-step reasoning when needed
- ✅ No regression in user experience
- ✅ Foundation for advanced AI features

---

## 📊 Performance Analysis

### Current Semantic Routing Performance

```
User Message → analyze_query_intent (pattern match) → route_to_data_store → PostgreSQL query → response
└─ Total: ~10-50ms for intent analysis + database query
└─ Single LLM call: 500-1500ms
└─ Total message processing: 800-2000ms
```

**Strengths**:
- ✅ Fast (single LLM call)
- ✅ Predictable latency
- ✅ Low API costs
- ✅ Works well for 80% of queries

**Limitations**:
- ❌ Fixed intent categories (7 hardcoded types)
- ❌ Pattern matching misses nuanced queries
- ❌ Cannot handle multi-step reasoning
- ❌ No dynamic decision making

### Full LLM Tool Calling Performance

```
User Message → LLM decides to call tool → tool_call_1 (PostgreSQL query) → LLM final response
└─ LLM call #1: 500-1500ms (with tools)
└─ Tool execution: 5-20ms  
└─ LLM call #2: 500-1500ms (synthesize response)
└─ Total: 1000-3000ms+
```

**Strengths**:
- ✅ Natural language understanding
- ✅ Dynamic routing based on context
- ✅ Multi-tool chains for complex queries
- ✅ Flexible and extensible

**Limitations**:
- ❌ 2-3x latency increase for simple queries
- ❌ 2x minimum LLM API costs
- ❌ Overkill for "What's my dog's name?"
- ❌ Production users notice 1+ second delays

### Latency Comparison by Query Type

| Query Type | Example | Semantic Routing | Tool Calling | Latency Increase |
|------------|---------|------------------|--------------|------------------|
| **Simple fact** | "What's my favorite food?" | 817ms | 1512ms | +85% ❌ |
| **Memory recall** | "Do you remember my dog?" | 850ms | 1600ms | +88% ❌ |
| **Character backstory** | "Where do you work?" | 800ms | 1450ms | +81% ❌ |
| **Complex analysis** | "Have my preferences changed?" | 1200ms (limited) | 2100ms | +75% ⚠️ |
| **Multi-step** | "Analyze my patterns and suggest topics" | Not possible | 2800ms | N/A ✅ |
| **Relationship summary** | "What do you know about me?" | 1100ms (basic) | 2300ms | +109% ⚠️ |

**Key Insight**: Tool calling adds 800-1500ms latency for queries that semantic routing handles well.

---

## 🏗️ Hybrid Architecture Design

### Core Principle

**Use the right tool for the job:**
- **Simple queries** (80% of traffic) → Semantic routing (fast path)
- **Complex queries** (20% of traffic) → LLM tool calling (intelligent path)

### Architecture Diagram

```
                          ┌─────────────────────────┐
                          │   User Query Message    │
                          └───────────┬─────────────┘
                                      │
                                      ▼
                          ┌─────────────────────────┐
                          │  Query Complexity       │
                          │  Assessment (Fast)      │
                          │  - Heuristics           │
                          │  - Keyword analysis     │
                          │  - Structure patterns   │
                          └───────────┬─────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
         complexity < 0.3                    complexity ≥ 0.3
                    │                                   │
                    ▼                                   ▼
    ┌───────────────────────────┐         ┌───────────────────────────┐
    │   FAST PATH                │         │   INTELLIGENT PATH        │
    │   (Semantic Routing)       │         │   (LLM Tool Calling)      │
    ├───────────────────────────┤         ├───────────────────────────┤
    │ 1. analyze_query_intent()  │         │ 1. LLM analyzes query     │
    │ 2. route_to_data_store()   │         │ 2. LLM selects tools      │
    │ 3. Execute PostgreSQL/     │         │ 3. Execute tool(s)        │
    │    Qdrant query           │         │ 4. LLM synthesizes result │
    │ 4. Inject into prompt     │         │                           │
    │ 5. Single LLM call        │         │                           │
    ├───────────────────────────┤         ├───────────────────────────┤
    │ Latency: 800-1200ms       │         │ Latency: 1500-3000ms      │
    │ LLM Calls: 1x             │         │ LLM Calls: 2-3x           │
    └─────────────┬─────────────┘         └─────────────┬─────────────┘
                  │                                     │
                  └─────────────────┬───────────────────┘
                                    ▼
                          ┌─────────────────────────┐
                          │   Character Response    │
                          └─────────────────────────┘
```

### Query Complexity Assessment Algorithm

```python
def assess_query_complexity(message: str) -> float:
    """
    Fast heuristic-based complexity scoring (< 1ms)
    
    Returns:
        0.0-1.0 complexity score
        < 0.3: Simple query (semantic routing)
        ≥ 0.3: Complex query (tool calling)
    """
    complexity = 0.0
    message_lower = message.lower()
    
    # Multi-part queries (coordination needed)
    if " and " in message_lower or "," in message_lower:
        complexity += 0.3
    
    # Analytical/temporal keywords (requires reasoning)
    analytical_keywords = [
        'analyze', 'pattern', 'changed', 'trend', 'compared',
        'evolution', 'progression', 'development', 'how have',
        'difference between', 'similar to'
    ]
    if any(kw in message_lower for kw in analytical_keywords):
        complexity += 0.4
    
    # Meta-questions about relationship (requires synthesis)
    meta_keywords = [
        'what do you know', 'tell me about me', 'summarize',
        'what have we', 'our relationship', 'how well do you know'
    ]
    if any(kw in message_lower for kw in meta_keywords):
        complexity += 0.3
    
    # Temporal reasoning (requires time-series analysis)
    temporal_keywords = ['lately', 'recently', 'over time', 'used to']
    if any(kw in message_lower for kw in temporal_keywords):
        complexity += 0.2
    
    # Hypothetical/planning queries (requires simulation)
    hypothetical_keywords = ['what if', 'could you', 'would you', 'suggest']
    if any(kw in message_lower for kw in hypothetical_keywords):
        complexity += 0.2
    
    return min(complexity, 1.0)
```

---

## 🛠️ Implementation Plan

### Phase 1: Create Hybrid Router (Week 1)

**Files to Create/Modify:**
- `src/knowledge/hybrid_query_router.py` (NEW)
- `src/core/message_processor.py` (MODIFY)

**Implementation:**

```python
# src/knowledge/hybrid_query_router.py

from typing import Dict, Any, Optional
from enum import Enum
import logging

from src.knowledge.semantic_router import SemanticKnowledgeRouter
from src.memory.llm_tool_integration_manager import LLMToolIntegrationManager

logger = logging.getLogger(__name__)


class QueryPath(Enum):
    """Routing path selection"""
    FAST = "fast"           # Semantic routing (< 0.3 complexity)
    INTELLIGENT = "intelligent"  # Tool calling (≥ 0.3 complexity)
    FALLBACK = "fallback"   # Error recovery


class HybridQueryRouter:
    """
    Intelligent query router combining semantic routing and LLM tool calling
    
    Strategy:
    - Simple queries (80%): Semantic routing → Fast (1 LLM call)
    - Complex queries (20%): Tool calling → Intelligent (2+ LLM calls)
    
    Performance:
    - Fast path: 800-1200ms
    - Intelligent path: 1500-3000ms
    - Average: ~1000-1500ms (vs 800-2000ms baseline)
    """
    
    def __init__(
        self,
        semantic_router: SemanticKnowledgeRouter,
        tool_manager: Optional[LLMToolIntegrationManager] = None,
        complexity_threshold: float = 0.3
    ):
        """
        Initialize hybrid router
        
        Args:
            semantic_router: Existing semantic routing system
            tool_manager: LLM tool calling manager (optional)
            complexity_threshold: Complexity score threshold for routing (0.0-1.0)
        """
        self.semantic_router = semantic_router
        self.tool_manager = tool_manager
        self.complexity_threshold = complexity_threshold
        
        # Metrics tracking
        self._fast_path_count = 0
        self._intelligent_path_count = 0
        self._fallback_count = 0
        
        logger.info(
            "✅ HybridQueryRouter initialized (threshold=%.2f, tool_calling=%s)",
            complexity_threshold,
            "enabled" if tool_manager else "disabled"
        )
    
    async def route_and_execute(
        self,
        message: str,
        user_id: str,
        conversation_context: list[dict],
        character_name: str
    ) -> Dict[str, Any]:
        """
        Route query and execute appropriate path
        
        Args:
            message: User's query message
            user_id: User identifier
            conversation_context: Full conversation history
            character_name: Bot character name
            
        Returns:
            Dict with 'path', 'data', 'latency_ms', 'llm_calls'
        """
        import time
        start_time = time.time()
        
        # Assess query complexity
        complexity = self._assess_query_complexity(message)
        
        # Determine routing path
        if complexity < self.complexity_threshold:
            path = QueryPath.FAST
        elif self.tool_manager is not None:
            path = QueryPath.INTELLIGENT
        else:
            # Tool manager not available, fallback to semantic routing
            path = QueryPath.FAST
            logger.warning(
                "Complex query detected but tool manager unavailable, using fast path"
            )
        
        # Execute selected path
        try:
            if path == QueryPath.FAST:
                result = await self._execute_fast_path(message, user_id)
                self._fast_path_count += 1
            else:  # QueryPath.INTELLIGENT
                result = await self._execute_intelligent_path(
                    message, user_id, conversation_context, character_name
                )
                self._intelligent_path_count += 1
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.info(
                "🎯 HYBRID ROUTE: path=%s, complexity=%.2f, latency=%.0fms",
                path.value, complexity, latency_ms
            )
            
            return {
                "path": path.value,
                "complexity": complexity,
                "data": result.get("data"),
                "latency_ms": latency_ms,
                "llm_calls": result.get("llm_calls", 1),
                "tools_used": result.get("tools_used", [])
            }
            
        except Exception as e:
            logger.error("Hybrid routing failed: %s, using fallback", str(e))
            self._fallback_count += 1
            
            # Fallback to fast path
            result = await self._execute_fast_path(message, user_id)
            return {
                "path": QueryPath.FALLBACK.value,
                "complexity": complexity,
                "data": result.get("data"),
                "latency_ms": (time.time() - start_time) * 1000,
                "llm_calls": 1,
                "error": str(e)
            }
    
    def _assess_query_complexity(self, message: str) -> float:
        """
        Fast heuristic-based complexity scoring
        
        Returns:
            0.0-1.0 complexity score
        """
        complexity = 0.0
        message_lower = message.lower()
        
        # Multi-part queries (coordination needed)
        if " and " in message_lower or "," in message_lower:
            complexity += 0.3
        
        # Analytical/temporal keywords (requires reasoning)
        analytical_keywords = [
            'analyze', 'pattern', 'changed', 'trend', 'compared',
            'evolution', 'progression', 'development', 'how have',
            'difference between', 'similar to'
        ]
        if any(kw in message_lower for kw in analytical_keywords):
            complexity += 0.4
        
        # Meta-questions about relationship (requires synthesis)
        meta_keywords = [
            'what do you know', 'tell me about me', 'summarize',
            'what have we', 'our relationship', 'how well do you know'
        ]
        if any(kw in message_lower for kw in meta_keywords):
            complexity += 0.3
        
        # Temporal reasoning (requires time-series analysis)
        temporal_keywords = ['lately', 'recently', 'over time', 'used to']
        if any(kw in message_lower for kw in temporal_keywords):
            complexity += 0.2
        
        # Hypothetical/planning queries (requires simulation)
        hypothetical_keywords = ['what if', 'could you', 'would you', 'suggest']
        if any(kw in message_lower for kw in hypothetical_keywords):
            complexity += 0.2
        
        return min(complexity, 1.0)
    
    async def _execute_fast_path(
        self,
        message: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute semantic routing (fast path)
        
        Strategy:
        1. Analyze query intent via pattern matching
        2. Route to appropriate data store
        3. Retrieve facts/memories
        4. Return data for system prompt injection
        
        Returns:
            Dict with 'data' and 'llm_calls' (1)
        """
        # Analyze intent using existing semantic router
        intent_result = await self.semantic_router.analyze_query_intent(message)
        
        # Route to appropriate data store based on intent
        query_result = await self.semantic_router.query_user_knowledge(
            user_id=user_id,
            query=message,
            intent=intent_result
        )
        
        return {
            "data": query_result,
            "llm_calls": 1,
            "intent": intent_result.intent_type.value
        }
    
    async def _execute_intelligent_path(
        self,
        message: str,
        user_id: str,
        conversation_context: list[dict],
        character_name: str
    ) -> Dict[str, Any]:
        """
        Execute LLM tool calling (intelligent path)
        
        Strategy:
        1. LLM analyzes query and decides which tools to call
        2. Execute tool(s) (may be multiple in sequence)
        3. LLM synthesizes results into character-appropriate response
        
        Returns:
            Dict with 'data', 'llm_calls' (2+), 'tools_used'
        """
        if self.tool_manager is None:
            raise ValueError("Tool manager not available for intelligent path")
        
        # Get available query tools
        tools = self._get_query_tools()
        
        # Execute tool calling workflow
        tool_result = await self.tool_manager.execute_tool_workflow(
            messages=conversation_context,
            available_tools=tools,
            user_id=user_id,
            character_name=character_name
        )
        
        return {
            "data": tool_result.get("data"),
            "llm_calls": tool_result.get("llm_calls", 2),
            "tools_used": tool_result.get("tools_used", [])
        }
    
    def _get_query_tools(self) -> list[dict]:
        """
        Define query-specific tools for LLM tool calling
        
        Returns:
            List of tool definitions in OpenAI format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_user_facts",
                    "description": "Search for factual information about the user (preferences, pets, hobbies, location, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What to search for (e.g., 'user's pets', 'food preferences')"
                            },
                            "entity_type": {
                                "type": "string",
                                "description": "Optional filter: 'pet', 'hobby', 'food', 'person', etc.",
                                "enum": ["pet", "hobby", "food", "person", "location", "all"]
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_conversation_context",
                    "description": "Search past conversations for context about specific topics or emotional moments",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What to search for in conversation history"
                            },
                            "time_range": {
                                "type": "string",
                                "description": "Time window for search",
                                "enum": ["recent", "last_week", "last_month", "all_time"]
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_character_backstory",
                    "description": "Answer questions about the character's identity, backstory, and personality traits",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What aspect to look up (e.g., 'where do I work', 'what's my background')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "summarize_user_relationship",
                    "description": "Provide comprehensive summary of what the bot knows about the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "include_preferences": {
                                "type": "boolean",
                                "description": "Include user preferences and likes"
                            },
                            "include_relationships": {
                                "type": "boolean",
                                "description": "Include user's relationships with others"
                            },
                            "include_conversation_patterns": {
                                "type": "boolean",
                                "description": "Include conversation style and patterns"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_temporal_trends",
                    "description": "Analyze how user preferences or patterns have changed over time",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric": {
                                "type": "string",
                                "description": "What to analyze (e.g., 'preference_changes', 'emotional_trends', 'topic_evolution')"
                            },
                            "time_window": {
                                "type": "string",
                                "description": "Time period for analysis",
                                "enum": ["last_week", "last_month", "last_3_months", "all_time"]
                            }
                        },
                        "required": ["metric"]
                    }
                }
            }
        ]
    
    def get_routing_metrics(self) -> Dict[str, Any]:
        """
        Get routing statistics
        
        Returns:
            Dict with path usage counts and percentages
        """
        total = self._fast_path_count + self._intelligent_path_count + self._fallback_count
        
        if total == 0:
            return {
                "total_queries": 0,
                "fast_path_pct": 0.0,
                "intelligent_path_pct": 0.0,
                "fallback_pct": 0.0
            }
        
        return {
            "total_queries": total,
            "fast_path_count": self._fast_path_count,
            "fast_path_pct": (self._fast_path_count / total) * 100,
            "intelligent_path_count": self._intelligent_path_count,
            "intelligent_path_pct": (self._intelligent_path_count / total) * 100,
            "fallback_count": self._fallback_count,
            "fallback_pct": (self._fallback_count / total) * 100
        }
```

### Phase 2: Integration Testing (Week 2)

**Test Scenarios:**

1. **Simple fact queries** (expect fast path):
   - "What's my favorite food?"
   - "Do you remember my dog's name?"
   - "Where do you work?"
   
2. **Complex analytical queries** (expect intelligent path):
   - "Have my preferences changed lately?"
   - "Analyze my conversation patterns and suggest topics"
   - "What do you know about me and how have I evolved?"

3. **Edge cases**:
   - Tool manager unavailable (fallback to fast path)
   - LLM tool call fails (error handling)
   - Multi-tool chains (verify latency)

### Phase 3: Production Deployment (Week 3)

**Rollout Strategy:**
1. Deploy with `complexity_threshold=0.3` (default)
2. Monitor routing metrics for 1 week
3. Adjust threshold based on latency/intelligence tradeoff
4. Enable tool calling for specific bots first (Elena, Marcus)

**Monitoring:**
- Track fast_path vs intelligent_path usage
- Measure average latency per path
- User satisfaction correlation

---

## 📋 Tool Definitions

### Core Query Tools

**1. query_user_facts**
- **Purpose**: Search PostgreSQL `user_fact_relationships` + `fact_entities` tables
- **Execution Time**: 10-20ms
- **Use Cases**: "What foods do I like?", "What's my dog's name?"
- **Implementation**: Direct PostgreSQL query with entity_type filtering

**2. recall_conversation_context**
- **Purpose**: Semantic search in Qdrant vector memory
- **Execution Time**: 20-50ms
- **Use Cases**: "What did we talk about last week?", "Do you remember when I told you about X?"
- **Implementation**: Vector similarity search with time filtering

**3. query_character_backstory**
- **Purpose**: Retrieve character data from CDL database
- **Execution Time**: 5-15ms
- **Use Cases**: "Where do you work?", "Tell me about your background"
- **Implementation**: CDL database query for character_background, character_identity_details

**4. summarize_user_relationship**
- **Purpose**: Aggregate user facts, preferences, conversation patterns
- **Execution Time**: 30-80ms (multiple queries)
- **Use Cases**: "What do you know about me?", "Summarize our relationship"
- **Implementation**: Multi-table JOIN + aggregation

**5. query_temporal_trends**
- **Purpose**: Analyze changes over time in preferences/patterns
- **Execution Time**: 50-100ms (time-series analysis)
- **Use Cases**: "How have my preferences changed?", "Am I getting happier?"
- **Implementation**: InfluxDB temporal queries + trend analysis

---

## 🎯 Decision Matrix

### When to Use Fast Path (Semantic Routing)

**Characteristics:**
- Single fact retrieval
- Clear entity type (pet, food, hobby)
- No temporal reasoning required
- No multi-step coordination

**Examples:**
- ✅ "What's my favorite food?"
- ✅ "Do you remember my dog?"
- ✅ "Where do you live?"
- ✅ "What's my cat's name?"

**Complexity Score**: < 0.3

### When to Use Intelligent Path (Tool Calling)

**Characteristics:**
- Multi-part queries requiring coordination
- Analytical reasoning needed
- Temporal trend analysis
- Meta-questions about relationship
- Hypothetical scenarios

**Examples:**
- ✅ "What do you know about me and how have my preferences changed?"
- ✅ "Analyze my conversation patterns and suggest topics"
- ✅ "Am I happier lately compared to last month?"
- ✅ "If I got a new pet, what would you suggest?"

**Complexity Score**: ≥ 0.3

---

## 📈 Expected Performance

### Baseline (Current System)
- **Average latency**: 800-2000ms
- **LLM calls per message**: 1
- **Query capabilities**: Basic fact retrieval

### Hybrid System (Projected)
- **Average latency**: 1000-1500ms (25% slowdown worst case)
- **Fast path (80%)**: 800-1200ms (no change)
- **Intelligent path (20%)**: 1500-3000ms (enables new capabilities)
- **User experience**: Fast when possible, intelligent when needed

### Performance by Query Distribution

| Distribution Scenario | Avg Latency | vs Baseline |
|----------------------|-------------|-------------|
| **80% simple, 20% complex** | 1160ms | +16% |
| **90% simple, 10% complex** | 1030ms | +3% |
| **70% simple, 30% complex** | 1290ms | +29% |

**Recommendation**: Target 80/20 distribution via threshold tuning (0.25-0.35).

---

## 🚀 Migration Path

### Stage 1: Preserve Existing Behavior (Week 1)
- Deploy hybrid router with `tool_manager=None`
- All queries use fast path (semantic routing)
- Validate no regression in current behavior
- Collect complexity metrics

### Stage 2: Enable Tool Calling (Week 2-3)
- Enable tool manager for specific bots (Elena, Marcus)
- Start with high threshold (0.4) - only very complex queries
- Monitor latency impact
- Gradually lower threshold based on data

### Stage 3: Optimize Threshold (Week 4)
- Analyze routing metrics
- Adjust threshold to target 80/20 distribution
- Fine-tune complexity scoring heuristics
- Document optimal threshold per character type

### Stage 4: Full Rollout (Week 5+)
- Enable for all production bots
- Monitor user satisfaction correlation
- Iterate on tool definitions
- Add new tools as needed

---

## 🔧 Configuration

### Environment Variables

```bash
# Master switch for LLM tool calling system (enables semantic router + all tools)
# This is the ONLY flag needed - enables all hybrid routing functionality
ENABLE_LLM_TOOL_CALLING=true

# NOTE: The following flags are DESIGN CONCEPTS ONLY (not implemented):
# - ENABLE_HYBRID_ROUTING (not used in actual code)
# - ENABLE_SEMANTIC_ROUTER (not used in actual code)
# - HYBRID_ROUTING_THRESHOLD (not implemented)
# - MAX_TOOL_ITERATIONS (not implemented)
# - TOOL_CALLING_TIMEOUT (not implemented)

# Actual implementation:
# - SemanticKnowledgeRouter is ALWAYS initialized when available
# - Tool calling is controlled by ENABLE_LLM_TOOL_CALLING
# - No complexity-based routing threshold (all tools available when flag is true)
```

### Per-Character Configuration

**NOTE:** The per-character routing configuration shown below is a **design concept** that was NOT implemented.

**Actual Implementation:**
- Tool calling is enabled/disabled globally via `ENABLE_LLM_TOOL_CALLING` environment variable
- Each bot's `.env` file controls whether that bot has tool calling enabled
- No per-character complexity thresholds (design concept only)
- No `routing_config.yaml` file (not implemented)

**Example (Actual):**
```bash
# .env.elena
ENABLE_LLM_TOOL_CALLING=true  # Elena has all tools available

# .env.jake  
ENABLE_LLM_TOOL_CALLING=false  # Jake has no tools (simple character)
```

**Design Concept (NOT IMPLEMENTED):**
```yaml
# config/routing_config.yaml (DOES NOT EXIST)
characters:
  elena:
    enable_hybrid_routing: true
    complexity_threshold: 0.3
    enable_tool_calling: true
  
  marcus:
    enable_hybrid_routing: true
    complexity_threshold: 0.25  # More analytical character, lower threshold
    enable_tool_calling: true
  
  jake:
    enable_hybrid_routing: false  # Simple character, semantic routing only
    enable_tool_calling: false
```

---

## 🎭 Character-Specific Considerations

### Educational Characters (Elena, Marcus)
- **Lower threshold** (0.25-0.30) - more tool calling
- **Analytical queries common** - users ask complex questions
- **Teaching style benefits** from multi-step explanations

### Simple Characters (Jake, Ryan)
- **Higher threshold** (0.40-0.50) - mostly semantic routing
- **Casual conversation focus** - simple fact retrieval
- **Performance priority** - minimize latency

### Fantasy Characters (Dream, Aethys)
- **Medium threshold** (0.30-0.35) - balanced approach
- **Narrative immersion** - tool calling can break immersion
- **Mystical explanations** work well with synthesis

---

## 🔍 Monitoring & Observability

### Key Metrics

**Routing Metrics:**
```python
{
    "total_queries": 1000,
    "fast_path_count": 820,
    "fast_path_pct": 82.0,
    "intelligent_path_count": 170,
    "intelligent_path_pct": 17.0,
    "fallback_count": 10,
    "fallback_pct": 1.0
}
```

**Performance Metrics:**
```python
{
    "avg_latency_fast_path": 980,
    "avg_latency_intelligent_path": 2150,
    "avg_latency_overall": 1178,
    "p95_latency_fast_path": 1450,
    "p95_latency_intelligent_path": 3200,
    "p95_latency_overall": 1820
}
```

**Tool Usage Metrics:**
```python
{
    "query_user_facts": 85,
    "recall_conversation_context": 45,
    "query_character_backstory": 20,
    "summarize_user_relationship": 12,
    "query_temporal_trends": 8
}
```

### Dashboard Integration

Add to Grafana dashboards:
- Routing path distribution (pie chart)
- Latency by path (time series)
- Complexity score distribution (histogram)
- Tool usage frequency (bar chart)

---

## 🚨 Risk Mitigation

### Risk 1: Latency Regression
**Mitigation:**
- Start with high threshold (0.4) - conservative routing
- Monitor P95 latency closely
- Roll back if latency increases > 20%
- Gradual threshold adjustment

### Risk 2: Tool Calling Failures
**Mitigation:**
- Fallback to semantic routing on tool errors
- Retry logic with exponential backoff
- Circuit breaker for repeated failures
- Comprehensive error logging

### Risk 3: Increased API Costs
**Mitigation:**
- Monitor LLM API calls per user
- Set per-user rate limits for tool calling
- Cost alerts in monitoring
- Optimize threshold to minimize unnecessary tool calls

### Risk 4: User Experience Degradation
**Mitigation:**
- A/B testing with user cohorts
- User satisfaction surveys
- Response time perception studies
- Easy rollback mechanism

---

## 💡 Future Enhancements

### Phase 2 Features (Post-Launch)

**1. Adaptive Threshold Learning**
- ML model learns optimal threshold per user
- Personalized complexity scoring
- User preference for speed vs intelligence

**2. Tool Caching**
- Cache tool results for repeated queries
- Invalidation strategy for stale data
- Redis-based distributed cache

**3. Parallel Tool Execution**
- Execute independent tools concurrently
- Reduce latency for multi-tool queries
- Dependency graph analysis

**4. Streaming Tool Results**
- Stream partial results to user
- Progressive disclosure pattern
- Perceived latency reduction

**5. Context-Aware Routing**
- Consider conversation history
- User's typical query patterns
- Time-of-day preferences

---

## 📚 References

### Related Documentation
- `docs/ai-features/LLM_TOOL_CALLING_ROADMAP.md` - Tool calling implementation
- `docs/architecture/QUERY_AND_SEMANTIC_ROUTING_ARCHITECTURE_REVIEW.md` - Semantic routing analysis
- `docs/roadmaps/PERFORMANCE_OPTIMIZATION_ROADMAP.md` - Performance considerations
- `src/knowledge/semantic_router.py` - Existing semantic routing implementation
- `src/memory/llm_tool_integration_manager.py` - Tool calling infrastructure

### External Resources
- OpenAI Function Calling API Documentation
- LangChain Tools and Agents
- Performance optimization best practices

---

## ✅ Success Criteria

**Phase 1 (Week 1)**
- ✅ Hybrid router implemented and tested
- ✅ No regression in baseline latency
- ✅ Complexity metrics collected

**Phase 2 (Week 2-3)**
- ✅ Tool calling enabled for 2+ bots
- ✅ 80/20 routing distribution achieved
- ✅ Latency increase < 20% overall

**Phase 3 (Week 4+)**
- ✅ Deployed to all production bots
- ✅ User satisfaction maintained or improved
- ✅ Complex queries handled successfully
- ✅ Monitoring dashboard operational

---

## 📝 Conclusion

The hybrid query routing system provides the best of both worlds:

**✅ Maintains speed** for the 80% case (simple queries)  
**✅ Enables intelligence** for the 20% case (complex queries)  
**✅ No regression** in current user experience  
**✅ Foundation for advanced features** (character learning, temporal analysis)  
**✅ Production-ready** with comprehensive monitoring and fallbacks

**Recommendation**: Proceed with phased implementation starting Week 1.

---

**Next Steps:**
1. Review this design document with team
2. Get approval for Phase 1 implementation
3. Create implementation branch
4. Begin coding hybrid router (Week 1)
