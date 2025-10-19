# User Preference Extraction Analysis

## 🔍 CURRENT IMPLEMENTATION

### Location
**File**: `src/core/message_processor.py`
**Method**: `_extract_and_store_user_preferences()` (lines 6100-6263)
**Called**: Line 834 - Phase 9c (AFTER response generation, ALWAYS runs)

### Detection Method
**REGEX-BASED KEYWORD MATCHING** - Same issue as fact extraction

### Patterns Detected
1. **Preferred Name**:
   - "My name is Mark"
   - "Call me Mark"
   - "I prefer to be called Mark"
   - "I go by Mark"
   - "You can call me Mark"
   - "I'm Mark"

2. **Timezone**:
   - "I'm in EST"
   - "My timezone is Pacific"
   - "I live in PST"

3. **Location**:
   - "I live in Seattle"
   - "I'm from Chicago"
   - "My location is Boston"

4. **Communication Style**:
   - "I prefer short responses"
   - "Keep it brief"
   - "I want detailed answers"

### Storage
- **Database**: PostgreSQL `universal_users.preferences` (JSONB column)
- **Method**: `semantic_router.store_user_preference()`
- **Structure**:
```json
{
  "preferred_name": {
    "value": "Mark",
    "confidence": 0.95,
    "updated_at": "2025-10-19T...",
    "metadata": {
      "detected_pattern": "regex_pattern",
      "source_message": "My name is Mark",
      "detection_method": "regex_pattern"
    }
  },
  "timezone": {
    "value": "PST",
    "confidence": 0.90,
    ...
  }
}
```

### Retrieval
- **Method**: `semantic_router.get_user_preference(user_id, preference_type)`
- **Performance**: <1ms (direct JSONB query)
- **Usage**: Prompt building, personalization

---

## 🚨 CRITICAL ISSUES (Same as Fact Extraction)

### 1. **Runs in Critical Response Path**
- Executes AFTER response generation (Phase 9c, line 834)
- Preferences detected don't affect current response
- Perfect candidate for async enrichment worker

### 2. **Regex Limitations**
- **Brittle patterns**: Misses variations like "everyone calls me Mark", "Mark's my name"
- **False positives**: "I go by bike" might match "I go by" pattern
- **Language variations**: Won't catch "people know me as Mark", "I answer to Mark"
- **Context blind**: "Don't call me Mark" vs "Call me Mark"

### 3. **Single-Message Context Only**
- Can't detect preferences from conversation flow:
  - Bot: "What should I call you?"
  - User: "Mark is fine"  ← Current regex won't catch this!
- Can't detect confirmation patterns:
  - User: "You can call me whatever"
  - Bot: "How about Mark?"
  - User: "Perfect!" ← Confirms preference

### 4. **Limited Preference Types**
Current regex only handles 4 types:
- ✅ preferred_name
- ✅ timezone  
- ✅ location
- ✅ communication_style

**Missing common preferences**:
- ❌ Pronouns (he/she/they)
- ❌ Language preference
- ❌ Response length preference (actual length, not style)
- ❌ Formality level
- ❌ Topic preferences
- ❌ Availability/schedule preferences

### 5. **No Feature Flag**
Unlike fact extraction (`ENABLE_RUNTIME_FACT_EXTRACTION`), preference extraction has:
- ❌ **No disable flag** - always runs
- ❌ **Can't be turned off** for enrichment-worker-only mode
- ❌ **Always adds processing overhead** (even if minimal)

---

## 🎯 ENRICHMENT WORKER OPPORTUNITY

### Why LLM-Based Preference Extraction is Superior

#### **Current Regex (Inline)**
```python
# Pattern: r"(?:my|My)\s+name\s+is\s+([A-Z][a-z]+)"
User: "My name is Mark"  ✅ DETECTED
User: "everyone calls me Mark"  ❌ MISSED
User: "Mark's my name"  ❌ MISSED
User: "people know me as Mark"  ❌ MISSED

# Pattern: r"(?:i|I)\s+go\s+by\s+([A-Z][a-z]+)"
User: "I go by Mark"  ✅ DETECTED
User: "I go by bike"  ⚠️ FALSE POSITIVE (might extract "bike")
```

#### **Enrichment Worker LLM (Conversation Context)**
```python
# Conversation window analysis:
Bot: "What should I call you?"
User: "Mark is fine"
User: "or just M works too"

LLM extracts:
{
  "preferred_name": "Mark",
  "alternate_names": ["M"],
  "confidence": 0.95,
  "reasoning": "User explicitly stated preference when asked",
  "conversation_context": "direct question-answer"
}
```

### Conversation-Level Benefits

**Example 1: Context-Aware Preference Detection**
```
User: "I prefer more detail"
Bot: "Got it! I'll provide comprehensive explanations"
User: "Actually, keep it shorter"  ← PREFERENCE CHANGE

Enrichment worker detects:
- Initial preference: detailed
- Updated preference: concise
- Temporal evolution: preference_change
- Final stored: communication_style = "concise"
```

**Example 2: Implicit Preference from Behavior**
```
User: "Can you shorten that?"
Bot: "Sure! [shorter response]"
User: "Perfect, thanks"
(repeats 3 times across conversations)

Enrichment worker infers:
- preference_type: communication_style
- preference_value: brief
- confidence: 0.85 (inferred from pattern, not explicit)
- reasoning: "User consistently requests shorter responses"
```

**Example 3: Pronoun Preference**
```
Bot: "What are your pronouns?"
User: "they/them please"

OR (harder):
User: "I'm non-binary btw"
Bot: "Thanks for sharing!"
User: "yeah, use they/them"

Enrichment worker extracts both cases with conversation context
```

---

## 🏗️ PROPOSED SOLUTION

### Phase 1: Add Feature Flag (IMMEDIATE)

**Add to `.env` files**:
```bash
# User Preference Extraction (optional - default: false)
# Controls whether preferences are extracted during message processing
# RECOMMENDED: false (enrichment worker handles preference extraction with better quality)
# Set to 'true' only for testing or immediate preference capture
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=false
```

**Modify** `src/core/message_processor.py` line 833:
```python
# Phase 9c: User preference extraction and storage (PostgreSQL)
# FEATURE FLAG: Runtime preference extraction (disabled by default)
preference_stored = False
if os.getenv('ENABLE_RUNTIME_PREFERENCE_EXTRACTION', 'false').lower() == 'true':
    preference_stored = await self._extract_and_store_user_preferences(
        message_context
    )
else:
    logger.debug("⏭️ RUNTIME PREFERENCE EXTRACTION: Disabled (enrichment worker handles this)")
```

### Phase 2: Enrichment Worker Preference Extraction

**Add to** `src/enrichment/worker.py`:

```python
async def _extract_preferences_for_users(self) -> int:
    """
    Extract user preferences from conversation windows using LLM.
    
    Similar to fact extraction but focused on:
    - Preferred name/nicknames
    - Pronouns
    - Timezone/location
    - Communication style
    - Response length preferences
    - Formality level
    - Topic preferences
    
    Returns:
        Number of preferences extracted
    """
    preferences_extracted = 0
    
    try:
        # Get all active users (last 30 days)
        active_users = await self._get_active_users(days=30)
        
        for user_id, bot_name in active_users:
            try:
                # Get last preference extraction timestamp
                last_extraction = await self._get_last_preference_extraction(
                    user_id, bot_name
                )
                
                # Get new messages since last extraction
                recent_messages = await self._get_new_messages_since(
                    user_id=user_id,
                    bot_name=bot_name,
                    since_timestamp=last_extraction
                )
                
                if not recent_messages:
                    continue
                
                # Extract preferences from conversation window
                preferences = await self._extract_preferences_from_window(
                    messages=recent_messages,
                    user_id=user_id,
                    bot_name=bot_name
                )
                
                if preferences:
                    await self._store_preferences_in_postgres(
                        user_id=user_id,
                        bot_name=bot_name,
                        preferences=preferences
                    )
                    preferences_extracted += len(preferences)
                
                # Update last extraction timestamp
                await self._update_last_preference_extraction(
                    user_id, bot_name
                )
                
            except Exception as e:
                logger.error(f"Failed to extract preferences for user {user_id}: {e}")
                continue
        
        return preferences_extracted
        
    except Exception as e:
        logger.error(f"Preference extraction failed: {e}")
        return 0


async def _extract_preferences_from_window(
    self,
    messages: List[Dict],
    user_id: str,
    bot_name: str
) -> List[Dict[str, Any]]:
    """
    Use LLM to extract preferences from conversation window.
    
    Prompts LLM to analyze conversation for:
    - Explicit preferences ("call me Mark")
    - Implicit preferences (user consistently requests shorter responses)
    - Preference changes over time
    """
    # Build conversation window
    conversation_text = self._format_messages_for_preference_extraction(messages)
    
    prompt = f"""Analyze this conversation and extract user preferences.

Conversation:
{conversation_text}

Extract ANY of these preference types that are clearly stated or strongly implied:

1. **preferred_name**: What the user wants to be called
2. **pronouns**: Preferred pronouns (he/him, she/her, they/them, etc.)
3. **timezone**: User's timezone (EST, PST, GMT, etc.)
4. **location**: Where the user lives/is located
5. **communication_style**: How they prefer responses (brief, detailed, casual, formal)
6. **response_length**: Preferred length (short, medium, long)
7. **language**: Preferred language if not English
8. **topic_preferences**: Topics they want to focus on or avoid

CRITICAL:
- ONLY extract if clearly stated or strongly implied from repeated patterns
- Mark explicit statements with confidence 0.9-1.0
- Mark implied/inferred with confidence 0.6-0.8
- Include conversation context showing where preference came from
- Detect preference CHANGES (user updated their preference)

Return JSON:
{{
  "preferences": [
    {{
      "preference_type": "preferred_name",
      "preference_value": "Mark",
      "confidence": 0.95,
      "reasoning": "User explicitly stated 'call me Mark' when asked",
      "conversation_context": "Bot asked 'What should I call you?' and user responded 'Mark is fine'",
      "is_explicit": true,
      "is_preference_change": false
    }}
  ]
}}

If no clear preferences found, return {{"preferences": []}}
"""
    
    # Call LLM
    messages_for_llm = [
        {"role": "system", "content": "You are a preference extraction specialist. Extract user preferences from conversations with high accuracy."},
        {"role": "user", "content": prompt}
    ]
    
    response = await self.llm_client.get_chat_response(
        messages_for_llm,
        temperature=0.2  # Low temperature for consistency
    )
    
    # Parse response
    try:
        # Handle markdown code blocks
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        result = json.loads(response)
        return result.get('preferences', [])
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM preference response: {e}")
        return []
```

### Phase 3: Update Enrichment Worker Main Loop

**Modify** `src/enrichment/worker.py` `_enrichment_cycle()`:
```python
async def _enrichment_cycle(self):
    """Single enrichment cycle - process summaries, facts, AND preferences"""
    try:
        # Generate conversation summaries
        summaries_created = await self._generate_summaries()
        logger.info(f"📊 ENRICHMENT: Created {summaries_created} summaries")
        
        # Extract facts from conversations
        facts_extracted = await self._extract_facts_for_users()
        logger.info(f"📊 ENRICHMENT: Extracted {facts_extracted} facts")
        
        # Extract preferences from conversations (NEW)
        preferences_extracted = await self._extract_preferences_for_users()
        logger.info(f"📊 ENRICHMENT: Extracted {preferences_extracted} preferences")
        
    except Exception as e:
        logger.error(f"Enrichment cycle failed: {e}")
```

---

## 📊 COMPARISON: Regex vs LLM Preference Extraction

| Feature | Current Regex (Inline) | Enrichment Worker LLM |
|---------|----------------------|---------------------|
| **Detection Method** | Hardcoded regex patterns | LLM conversation analysis |
| **Context Awareness** | Single message only | Full conversation window |
| **Preference Types** | 4 types (hardcoded) | Unlimited (LLM can extract any preference) |
| **Implicit Preferences** | ❌ Can't detect | ✅ Detects from patterns |
| **Preference Changes** | ❌ No tracking | ✅ Detects evolution |
| **False Positives** | ⚠️ High (regex brittleness) | ✅ Low (LLM understands context) |
| **Language Variations** | ❌ Misses variations | ✅ Handles natural language |
| **Performance Impact** | Minimal (regex fast) | ❌ None (async background) |
| **User-Facing Latency** | ~1-5ms added to response | ⚡ 0ms (runs in background) |
| **Maintenance** | ⚠️ High (add new regex for each pattern) | ✅ Low (LLM adapts) |

---

## 🎯 RECOMMENDATION

### **Disable inline preference extraction, enable enrichment worker**

**Benefits**:
1. ✅ **Better quality**: Conversation-level context vs single-message regex
2. ✅ **More preferences**: LLM can extract unlimited types vs 4 hardcoded patterns
3. ✅ **Implicit detection**: Catches preferences from behavior patterns
4. ✅ **Preference evolution**: Tracks changes over time
5. ✅ **Zero user latency**: Background processing vs inline regex
6. ✅ **Same storage**: Uses identical PostgreSQL `preferences` JSONB column

**Trade-offs**:
- ⏱️ **5-minute delay**: Preferences available after enrichment cycle (vs immediate)
- 💰 **LLM cost**: Small additional cost for preference extraction

**Is 5-minute delay acceptable?**
- ✅ **YES for most preferences**: Preferred name, timezone, pronouns don't need immediate application
- ✅ **User already mentioned it**: Preference already in conversation context (vector memory)
- ✅ **Next conversation**: Preference stored and retrieved from PostgreSQL (<1ms)
- ⚠️ **MAYBE for communication style**: User says "keep it brief" and expects next response to be brief
  - But conversation context already includes the request
  - Bot can respond appropriately even without stored preference

**Verdict**: 5-minute delay is acceptable for enrichment-worker-only preference extraction

---

## 📝 IMPLEMENTATION CHECKLIST

- [ ] **Phase 1: Add feature flag** (5 minutes)
  - [ ] Add `ENABLE_RUNTIME_PREFERENCE_EXTRACTION` check to message_processor.py
  - [ ] Update .env.template with documentation
  - [ ] Set to `false` in all bot .env files

- [ ] **Phase 2: Enrichment worker preference extraction** (2-3 hours)
  - [ ] Add `_extract_preferences_for_users()` method
  - [ ] Add `_extract_preferences_from_window()` method
  - [ ] Add `_store_preferences_in_postgres()` method
  - [ ] Add tracking table for last_preference_extraction timestamp
  - [ ] Test with conversation windows

- [ ] **Phase 3: Integration & testing** (1 hour)
  - [ ] Update enrichment worker main loop
  - [ ] Test preference extraction from real conversations
  - [ ] Verify PostgreSQL storage matches schema
  - [ ] Compare quality vs regex extraction

- [ ] **Phase 4: Documentation** (30 minutes)
  - [ ] Update enrichment worker docs
  - [ ] Add preference extraction guide
  - [ ] Document new LLM-based approach

**Total estimated time**: 4-5 hours

---

## 🚀 EXPECTED RESULTS

### Before (Current Regex)
```
User: "My name is Mark"  → ✅ Detected (0.95 confidence)
User: "everyone calls me Mark"  → ❌ Missed
User: "Mark's fine"  → ❌ Missed
User: "I answer to Mark"  → ❌ Missed
User: "use they/them"  → ❌ Missed (no pronoun regex)

Total detected: 1/5 (20%)
```

### After (Enrichment Worker LLM)
```
Conversation analysis:
Bot: "What should I call you?"
User: "Mark's fine, everyone calls me that"
User: "oh and I use they/them pronouns"

LLM extracts:
✅ preferred_name: "Mark" (0.95 confidence, explicit)
✅ alternate_names: ["Mark"] (0.90 confidence)
✅ pronouns: "they/them" (0.98 confidence, explicit)

Total detected: 3/3 (100%) + context understanding
```

---

**Conclusion**: Preference extraction has the SAME issues as fact extraction and should follow the SAME migration path: disable inline regex, enable enrichment worker LLM-based extraction.
