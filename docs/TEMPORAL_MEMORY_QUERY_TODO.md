# 🐛 Temporal Memory Query Enhancement

**Status:** 🔴 Active Issue  
**Priority:** MEDIUM-HIGH (affects user experience for temporal queries)  
**Discovered:** October 2, 2025  
**Affects:** All bots (memory retrieval architecture)

---

## 🎯 Problem Summary

Memory retrieval system fails to correctly handle **temporal queries** like "What was the first thing I asked today?" or "When did we last talk about X?"

The system prioritizes **semantic relevance** over **chronological ordering**, causing:
- Wrong messages recalled as "first"
- Recency bias in memory retrieval
- Temporal ordering ignored in favor of distinctive semantic features

---

## 📊 Evidence from Manual Testing

### **Test 9: Memory Recall Integrity (Elena 7D Testing)**

**User Question:**
```
Elena, what was the first thing I asked you about today?
```

**Elena's Response:**
> "Oh, right—you came in hot with: 'Rapid-fire: three emerging bleaching mitigation methods—one line each.'"

**Actual First Message Today:**
```
I'm designing an educational campaign for kids about ocean conservation—can we brainstorm your top 3 playful ideas?
```

**What Elena Recalled:**
The "rapid-fire" prompt from Test 5 (Temporal/Rhythm), which came AFTER:
- Test 3: Creative campaign brainstorming (ACTUAL FIRST) ✅
- Test 4: Interaction steering (two choices prompt)
- Test 5: Rapid-fire mitigation methods (WHAT SHE RECALLED) ❌

**Timeline:**
1. ✅ Test 3 (FIRST): "Educational campaign brainstorming..."
2. ✅ Test 4: "Give me two choices: deeper molecular angle vs. ecosystem recovery..."
3. ❌ Test 5: "Rapid-fire: three emerging bleaching mitigation methods..." **(Elena recalled this as "first")**
4. Test 6: Semantic depth (acclimatization vs adaptation)
5. Test 7: Creative reframe (coral-algae metaphor)
6. Test 8: Mode switching (coral bleaching research)
7. Test 9: Memory recall test (current)

**Result:** Elena incorrectly identified a middle-sequence message as "first message today."

---

## 🔍 Root Cause Analysis

### **1. Semantic Relevance Dominates Temporal Ordering**

**Current Behavior:**
```python
# Memory retrieval prioritizes semantic similarity
memories = await memory_manager.retrieve_relevant_memories(
    user_id=user_id,
    query=message,  # "What was the first thing I asked today?"
    limit=10
)
# Returns: Most semantically similar memories, NOT chronologically first
```

**Issue:**
- "Rapid-fire" prompt was semantically distinctive (unusual phrasing, action-oriented)
- "Educational campaign" prompt was less distinctive (common education/brainstorm words)
- Vector search scored "rapid-fire" higher than "campaign brainstorming"
- **Temporal ordering was never considered**

---

### **2. Missing Query Pattern Detection**

**Current System Lacks:**
- ❌ Detection of temporal query patterns ("first", "last", "earliest", "when did", "how long ago")
- ❌ Automatic temporal filtering when temporal intent detected
- ❌ Chronological ordering for temporal queries
- ❌ Session boundary awareness ("today" = current session start timestamp)

**What Should Happen:**
```python
# Temporal query detection
if is_temporal_query(message):  # "first thing I asked", "when did", "last time"
    memories = await memory_manager.retrieve_chronological_memories(
        user_id=user_id,
        temporal_filter="first_today",  # or "last_week", "earliest", etc.
        order="timestamp ASC",  # Chronological, not semantic
        limit=1
    )
```

---

### **3. Context Window May Exclude Early Messages**

**Current Prompt Building:**
```python
# OptimizedPromptBuilder may limit conversation history
conversation_context = recent_messages[-N:]  # Last N messages only
```

**Issue:**
- If `N=10` and session has 20+ messages, early messages excluded
- LLM never "sees" the actual first message
- Elena can only recall what's in her context window
- Temporal queries need full session access, not just recent context

---

### **4. No Confidence Scoring for Temporal Certainty**

**Current Behavior:**
Elena responds confidently even when memory retrieval is incorrect.

**Better Approach:**
```python
# Temporal confidence scoring
if temporal_query and confidence < 0.8:
    response = "I think it was [X], but let me double-check my memory..."
    # Or: "I recall discussing [X] early on, but I'm not 100% certain it was the very first thing."
```

---

## 🔧 Required Fixes

### **Fix 1: Temporal Query Pattern Detection (CRITICAL)**

**File:** `src/memory/vector_memory_system.py` or new `src/memory/temporal_query_handler.py`

**Implementation:**
```python
import re
from typing import Optional, Literal

TemporalIntent = Literal["first", "last", "earliest", "latest", "when", "how_long_ago", "session_start", "session_end"]

class TemporalQueryDetector:
    """Detect temporal query patterns in user messages"""
    
    TEMPORAL_PATTERNS = {
        "first": [
            r"\bfirst\s+thing\b",
            r"\bvery\s+first\b",
            r"\binitially\b",
            r"\bat\s+the\s+start\b",
            r"\bto\s+begin\s+with\b",
            r"\bwhen\s+we\s+started\b"
        ],
        "last": [
            r"\blast\s+time\b",
            r"\bmost\s+recent\b",
            r"\bjust\s+now\b",
            r"\bearlier\s+today\b",
            r"\ba\s+moment\s+ago\b"
        ],
        "when": [
            r"\bwhen\s+did\b",
            r"\bwhen\s+was\b",
            r"\bwhat\s+time\b",
            r"\bhow\s+long\s+ago\b",
            r"\bhow\s+many\s+days\b"
        ],
        "session_boundary": [
            r"\btoday\b",
            r"\bthis\s+session\b",
            r"\bthis\s+conversation\b",
            r"\bsince\s+we\s+started\s+talking\b"
        ]
    }
    
    def detect_temporal_intent(self, message: str) -> Optional[TemporalIntent]:
        """Detect if message contains temporal query intent"""
        message_lower = message.lower()
        
        # Check each pattern category
        for intent, patterns in self.TEMPORAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return None
    
    def extract_temporal_context(self, message: str) -> dict:
        """Extract temporal context from message"""
        message_lower = message.lower()
        
        context = {
            "intent": self.detect_temporal_intent(message),
            "scope": None,  # "today", "this_week", "ever", etc.
            "relative": False  # True if "ago", "since", "before"
        }
        
        # Detect scope
        if "today" in message_lower or "this session" in message_lower:
            context["scope"] = "session"
        elif "this week" in message_lower:
            context["scope"] = "week"
        elif "ever" in message_lower or "always" in message_lower:
            context["scope"] = "all_time"
        
        # Detect relative vs absolute
        if any(word in message_lower for word in ["ago", "since", "before", "after"]):
            context["relative"] = True
        
        return context
```

---

### **Fix 2: Chronological Memory Retrieval (CRITICAL)**

**File:** `src/memory/vector_memory_system.py`

**Add New Method:**
```python
async def retrieve_chronological_memories(
    self,
    user_id: str,
    temporal_filter: Literal["first_today", "last_today", "first_ever", "last_ever", "earliest", "latest"],
    limit: int = 1,
    memory_type: Optional[MemoryType] = MemoryType.CONVERSATION,
    session_start_timestamp: Optional[float] = None
) -> List[VectorMemory]:
    """
    Retrieve memories based on chronological ordering, NOT semantic similarity.
    
    Used for temporal queries like "What was the first thing I asked today?"
    
    Args:
        user_id: User identifier
        temporal_filter: Type of temporal retrieval
        limit: Number of memories to return
        memory_type: Filter by memory type
        session_start_timestamp: Unix timestamp for "today"/"session" filters
    
    Returns:
        List of memories in chronological order
    """
    try:
        collection_name = self.collection_name
        
        # Build filter conditions
        must_conditions = [
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=user_id)
            ),
            models.FieldCondition(
                key="bot_name",
                match=models.MatchValue(value=get_normalized_bot_name_from_env())
            )
        ]
        
        if memory_type:
            must_conditions.append(
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchValue(value=memory_type.value)
                )
            )
        
        # Add temporal filter
        if temporal_filter in ["first_today", "last_today"] and session_start_timestamp:
            must_conditions.append(
                models.FieldCondition(
                    key="timestamp_unix",
                    range=models.Range(gte=session_start_timestamp)
                )
            )
        
        # Determine sort order
        order_by = "timestamp_unix"
        direction = "asc" if "first" in temporal_filter or "earliest" in temporal_filter else "desc"
        
        # Query without vector search (pure temporal ordering)
        scroll_result = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(must=must_conditions),
            limit=limit,
            order_by=order_by,
            with_payload=True,
            with_vectors=False  # Don't need vectors for temporal queries
        )
        
        points, _ = scroll_result
        
        if not points:
            logger.info(f"⏰ TEMPORAL QUERY: No memories found for {temporal_filter} (user: {user_id})")
            return []
        
        logger.info(f"⏰ TEMPORAL QUERY: Found {len(points)} memories for {temporal_filter} (user: {user_id})")
        
        # Convert to VectorMemory objects
        memories = []
        for point in points:
            memory = self._point_to_memory(point)
            if memory:
                memories.append(memory)
        
        return memories
        
    except Exception as e:
        logger.error(f"Error in chronological memory retrieval: {e}")
        return []
```

---

### **Fix 3: Session Boundary Tracking (IMPORTANT)**

**File:** `src/handlers/events.py` or `src/memory/session_manager.py`

**Track Session Start:**
```python
class SessionManager:
    """Track conversation session boundaries for temporal queries"""
    
    def __init__(self):
        self._session_starts: Dict[str, float] = {}  # user_id -> session_start_timestamp
    
    def mark_session_start(self, user_id: str) -> float:
        """Mark the start of a new conversation session"""
        timestamp = datetime.now(UTC).timestamp()
        self._session_starts[user_id] = timestamp
        logger.info(f"⏰ SESSION: Marked session start for user {user_id} at {timestamp}")
        return timestamp
    
    def get_session_start(self, user_id: str) -> Optional[float]:
        """Get the session start timestamp for a user"""
        return self._session_starts.get(user_id)
    
    def is_new_session(self, user_id: str, inactivity_threshold_minutes: int = 30) -> bool:
        """Determine if this is a new session based on inactivity"""
        last_start = self._session_starts.get(user_id)
        if not last_start:
            return True
        
        minutes_since_start = (datetime.now(UTC).timestamp() - last_start) / 60
        return minutes_since_start > inactivity_threshold_minutes
    
    def clear_session(self, user_id: str):
        """Clear session tracking for a user"""
        self._session_starts.pop(user_id, None)
```

**Integration in Event Handler:**
```python
# In BotEventHandlers.__init__
self.session_manager = SessionManager()

# In on_message handler (before processing)
if self.session_manager.is_new_session(user_id):
    self.session_manager.mark_session_start(user_id)
```

---

### **Fix 4: Temporal Query Integration in Message Processing (CRITICAL)**

**File:** `src/handlers/events.py`

**Update Message Processing:**
```python
async def _process_message_with_intelligence(self, message, content):
    """Process message with temporal query detection"""
    user_id = str(message.author.id)
    
    # 1. Detect temporal query intent
    temporal_detector = TemporalQueryDetector()
    temporal_context = temporal_detector.extract_temporal_context(content)
    
    if temporal_context["intent"]:
        logger.info(f"⏰ TEMPORAL QUERY DETECTED: {temporal_context['intent']} (scope: {temporal_context['scope']})")
        
        # 2. Use chronological retrieval instead of semantic search
        session_start = self.session_manager.get_session_start(user_id)
        
        temporal_memories = await self.memory_manager.retrieve_chronological_memories(
            user_id=user_id,
            temporal_filter=f"{temporal_context['intent']}_today" if temporal_context['scope'] == 'session' else temporal_context['intent'],
            limit=3,  # Get a few to provide context
            session_start_timestamp=session_start
        )
        
        # 3. Build context with chronological memories (not semantic search)
        conversation_context = self._build_temporal_context(temporal_memories, content)
        
        # 4. Add temporal metadata to prompt
        temporal_hint = f"[TEMPORAL QUERY: User asking about '{temporal_context['intent']}' message. Provide accurate chronological recall.]"
        system_prompt = f"{temporal_hint}\n\n{cdl_system_prompt}"
        
    else:
        # Normal semantic memory retrieval for non-temporal queries
        memories = await self.memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query=content,
            limit=10
        )
        conversation_context = self._build_conversation_context(memories, content)
        system_prompt = cdl_system_prompt
    
    # Continue with LLM generation...
```

---

### **Fix 5: Confidence Scoring for Temporal Queries (ENHANCEMENT)**

**File:** `src/prompts/cdl_ai_integration.py` or response post-processor

**Add Temporal Confidence:**
```python
def add_temporal_confidence_disclaimer(response: str, confidence: float, temporal_intent: str) -> str:
    """Add confidence disclaimer for low-confidence temporal queries"""
    
    if confidence < 0.7 and temporal_intent in ["first", "when", "how_long_ago"]:
        # Prepend uncertainty acknowledgment
        disclaimers = [
            "I think it was",
            "If I recall correctly",
            "From what I remember",
            "I believe"
        ]
        
        disclaimer = random.choice(disclaimers)
        response = f"{disclaimer}, {response[0].lower()}{response[1:]}"
        
        # Append verification offer
        response += "\n\n(Let me know if that's not quite right—memory can be tricky!)"
    
    return response
```

---

## 🧪 Verification Steps

After implementing fixes:

### **Test Case 1: Session-First Query**
```python
# User starts new session
user: "I'm designing an educational campaign..." # First message
user: "Can you give me rapid-fire ideas?" # Second message
user: "What was the first thing I asked today?"

# Expected: Campaign brainstorming message
# Current (BROKEN): Rapid-fire message ❌
# After Fix: Campaign message ✅
```

### **Test Case 2: Last Message Query**
```python
user: "What was the last thing you told me about?"

# Expected: Content from immediately previous bot response
# Should use timestamp DESC ordering
```

### **Test Case 3: When-Did Query**
```python
user: "When did we first talk about coral bleaching?"

# Expected: Timestamp + content of earliest coral bleaching mention
# Should filter by semantic content + temporal ordering
```

### **Test Case 4: Confidence Acknowledgment**
```python
# If user asks about message from 50 messages ago (outside context window)
user: "What was the 5th thing I asked you today?"

# Expected: Acknowledgment of uncertainty
# "I believe it was [X], but I'm not 100% certain—my memory gets fuzzy beyond recent messages."
```

---

## 📊 Technical Implementation Priority

### **Phase 1: Critical Fixes (Implement First)**
1. ✅ **TemporalQueryDetector** - Pattern matching for temporal intent
2. ✅ **retrieve_chronological_memories()** - Pure temporal ordering retrieval
3. ✅ **SessionManager** - Track session boundaries for "today"/"this session" queries
4. ✅ **Integration in event handler** - Route temporal queries to chronological retrieval

### **Phase 2: Enhancements (After Phase 1 Works)**
5. ⏸️ **Temporal confidence scoring** - Acknowledge uncertainty
6. ⏸️ **Hybrid temporal-semantic queries** - "When did we talk about X?" (temporal + semantic filter)
7. ⏸️ **Relative time parsing** - "3 messages ago", "last week", "yesterday"

---

## 🎯 Success Criteria

### **Must Have (Phase 1):**
- ✅ "What was the first thing I asked today?" returns actual first message
- ✅ "What was the last thing you told me?" returns most recent bot response
- ✅ Temporal queries use chronological ordering, not semantic relevance
- ✅ Session boundaries tracked ("today" = current session)

### **Nice to Have (Phase 2):**
- ⏸️ Confidence disclaimers for low-certainty temporal recalls
- ⏸️ "When did we discuss X?" combines temporal + semantic filtering
- ⏸️ Relative time queries ("3 messages ago") work accurately

---

## 🔗 Related Issues

- **EMOTION_DATA_POLLUTION_BUG.md** - Separate bug with emotion data storage
- **RESPONSE_TRANSFORM_COMPRESSION_TODO.md** - Compression middleware planning
- **CDL_SINGLETON_MIGRATION_TODO.md** - CDL system migration planning

---

## 📈 Impact Assessment

### **User Experience:**
- 🔴 **Factual accuracy issues** when users ask about conversation history
- 🔴 **Trust degradation** when bot confidently gives wrong temporal recalls
- 🟡 **Not critical for general conversation** (most queries are semantic, not temporal)

### **System Architecture:**
- ✅ **7D system works well** for semantic memory retrieval
- ❌ **Temporal dimension under-utilized** in memory queries
- ❌ **Missing temporal query routing** in memory manager protocol

### **Character Authenticity:**
- ✅ **Personality consistency maintained** (Elena's voice is intact)
- ❌ **Memory accuracy affected** (factual recall errors)
- ⚠️ **No self-awareness of uncertainty** (confidently wrong)

---

## 🚀 Next Steps

1. ✅ **Create this TODO document** (COMPLETE)
2. ⏸️ **Implement TemporalQueryDetector** (Phase 1 - Critical)
3. ⏸️ **Add retrieve_chronological_memories()** (Phase 1 - Critical)
4. ⏸️ **Implement SessionManager** (Phase 1 - Critical)
5. ⏸️ **Integrate temporal routing in event handler** (Phase 1 - Critical)
6. ⏸️ **Test with Elena** (verify "first thing I asked today" works)
7. ⏸️ **Deploy to all bots** if Elena tests pass

---

## 💡 Design Notes

### **Why This Matters:**
Temporal queries test **memory accuracy**, not personality. Users expect:
- "What was the first thing I asked?" → Correct chronological recall
- "When did we discuss X?" → Accurate timestamp retrieval
- "What did you just say?" → Immediate previous message

Currently, semantic relevance dominates, causing:
- Distinctive phrases retrieved over chronologically first messages
- Recency bias (recent distinctive content over actual recent content)
- No temporal ordering in memory queries

### **Architecture Decision:**
**Separate temporal queries from semantic queries** instead of trying to blend them:
- **Temporal query detected** → Pure chronological retrieval (no vector search)
- **Semantic query** → Vector-based relevance search (current behavior)
- **Hybrid query** ("When did we discuss X?") → Semantic filter + temporal ordering

This preserves existing semantic search excellence while fixing temporal recall issues.
