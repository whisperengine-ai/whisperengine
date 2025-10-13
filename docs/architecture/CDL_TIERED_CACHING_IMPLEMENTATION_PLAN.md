# CDL Tiered Caching Implementation Plan

## Goal: Minimal Code Changes, Maximum Safety

Implement Tier 1 caching (stable data) while keeping Tier 2/3 as fresh queries.

---

## ✅ SAFE IMPLEMENTATION: 3 Small Changes Only

### Change 1: Add Tier 1 Cache Fields (src/prompts/cdl_ai_integration.py)

**Location**: `__init__()` method (lines 18-57)

**Add these cache fields**:
```python
# 🚀 PERFORMANCE: Character caching for load_character performance
self._cached_character = None
self._cached_character_bot_name = None

# 🚀 TIER 1 CACHE: Stable character data (rare changes)
self._cached_voice_traits = None
self._cached_cultural_expressions = None
self._cached_ai_scenarios = None
self._cached_interest_topics = None
```

**Risk**: ✅ ZERO - Just adding new fields, no behavior change

---

### Change 2: Add Preload Method (src/prompts/cdl_ai_integration.py)

**Location**: After `load_character()` method (around line 2050)

**Add new method**:
```python
async def preload_tier1_stable_data(self):
    """
    🚀 TIER 1 CACHING: Preload stable character data during bot initialization.
    
    These fields rarely change (character identity/personality core) so caching
    them eliminates unnecessary database queries while maintaining immediate
    feedback for dynamic fields (relationships, triggers, expertise).
    
    Cache invalidation: Bot restart via ./multi-bot.sh restart <bot>
    """
    try:
        from src.memory.vector_memory_system import get_normalized_bot_name_from_env
        bot_name = get_normalized_bot_name_from_env()
        
        if not self.enhanced_manager:
            logger.warning("⚠️ Enhanced manager not available - skipping Tier 1 preload")
            return
        
        logger.info("🚀 TIER 1 CACHE: Preloading stable character data for %s...", bot_name)
        
        # Cache stable data that rarely changes
        self._cached_voice_traits = await self.enhanced_manager.get_voice_traits(bot_name)
        self._cached_cultural_expressions = await self.enhanced_manager.get_cultural_expressions(bot_name)
        self._cached_ai_scenarios = await self.enhanced_manager.get_ai_scenarios(bot_name)
        self._cached_interest_topics = await self.enhanced_manager.get_interest_topics(bot_name)
        
        logger.info("✅ TIER 1 CACHE: Preloaded %d voice traits, %d cultural expressions, %d AI scenarios, %d interest topics",
                   len(self._cached_voice_traits) if self._cached_voice_traits else 0,
                   len(self._cached_cultural_expressions) if self._cached_cultural_expressions else 0,
                   len(self._cached_ai_scenarios) if self._cached_ai_scenarios else 0,
                   len(self._cached_interest_topics) if self._cached_interest_topics else 0)
        
    except Exception as e:
        logger.warning("⚠️ TIER 1 CACHE: Preload failed (will fetch fresh): %s", e)
        # Not fatal - will fall back to fresh queries
```

**Risk**: ✅ LOW - New method, optional feature with fallback

---

### Change 3: Use Cached Data in Prompt Building (src/prompts/cdl_ai_integration.py)

**Location**: Replace 4 database queries with cache lookups

#### 3a. Voice Traits (line ~2926)
```python
# BEFORE:
if self.enhanced_manager:
    try:
        bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
        voice_traits = await self.enhanced_manager.get_voice_traits(bot_name)

# AFTER:
if self.enhanced_manager:
    try:
        # 🚀 TIER 1 CACHE: Use cached voice traits (stable data)
        voice_traits = self._cached_voice_traits
        if voice_traits is None:  # Fallback if cache not loaded
            bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
            voice_traits = await self.enhanced_manager.get_voice_traits(bot_name)
            logger.debug("⚠️ TIER 1 CACHE MISS: Fetched voice traits fresh (cache not preloaded)")
```

#### 3b. Cultural Expressions (line ~2991)
```python
# BEFORE:
if self.enhanced_manager:
    try:
        bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
        cultural_expressions = await self.enhanced_manager.get_cultural_expressions(bot_name)

# AFTER:
if self.enhanced_manager:
    try:
        # 🚀 TIER 1 CACHE: Use cached cultural expressions (stable data)
        cultural_expressions = self._cached_cultural_expressions
        if cultural_expressions is None:  # Fallback if cache not loaded
            bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
            cultural_expressions = await self.enhanced_manager.get_cultural_expressions(bot_name)
            logger.debug("⚠️ TIER 1 CACHE MISS: Fetched cultural expressions fresh (cache not preloaded)")
```

#### 3c. AI Scenarios (line ~1092)
```python
# BEFORE:
if self.enhanced_manager:
    try:
        bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
        ai_scenarios = await self.enhanced_manager.get_ai_scenarios(bot_name)

# AFTER:
if self.enhanced_manager:
    try:
        # 🚀 TIER 1 CACHE: Use cached AI scenarios (stable data)
        ai_scenarios = self._cached_ai_scenarios
        if ai_scenarios is None:  # Fallback if cache not loaded
            bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
            ai_scenarios = await self.enhanced_manager.get_ai_scenarios(bot_name)
            logger.debug("⚠️ TIER 1 CACHE MISS: Fetched AI scenarios fresh (cache not preloaded)")
```

#### 3d. Interest Topics (line ~474)
```python
# BEFORE:
if self.enhanced_manager:
    try:
        from src.memory.vector_memory_system import get_normalized_bot_name_from_env
        bot_name = get_normalized_bot_name_from_env()
        interest_topics = await self.enhanced_manager.get_interest_topics(bot_name)

# AFTER:
if self.enhanced_manager:
    try:
        # 🚀 TIER 1 CACHE: Use cached interest topics (stable data)
        interest_topics = self._cached_interest_topics
        if interest_topics is None:  # Fallback if cache not loaded
            from src.memory.vector_memory_system import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            interest_topics = await self.enhanced_manager.get_interest_topics(bot_name)
            logger.debug("⚠️ TIER 1 CACHE MISS: Fetched interest topics fresh (cache not preloaded)")
```

**Risk**: ✅ LOW - Cache-with-fallback pattern is bulletproof

---

### Change 4: Call Preload During Bot Initialization (src/core/bot.py)

**Location**: After enhanced manager initialization (line ~251)

```python
# Update character system with enhanced manager
if self.character_system:
    self.character_system.enhanced_manager = enhanced_manager
    # 🐛 FIX: Also update TriggerModeController's enhanced_manager reference
    if hasattr(self.character_system, 'trigger_mode_controller') and self.character_system.trigger_mode_controller:
        self.character_system.trigger_mode_controller.enhanced_manager = enhanced_manager
        self.logger.info("✅ TriggerModeController updated with enhanced CDL manager for database-driven mode detection")
    self.logger.info("✅ Character system updated with enhanced CDL manager for relationships, triggers, and speech patterns")
    
    # 🚀 TIER 1 CACHE: Preload stable character data
    try:
        await self.character_system.preload_tier1_stable_data()
    except Exception as e:
        self.logger.warning("⚠️ Tier 1 cache preload failed (will use fresh queries): %s", e)
```

**Risk**: ✅ ZERO - Optional preload with exception handling, doesn't break anything if it fails

---

## Safety Analysis

### ✅ Why This Is Safe:

1. **Cache-with-Fallback Pattern**: Every cached field has `if cache is None: fetch fresh`
   - If cache fails → Falls back to existing behavior (fetch fresh)
   - If cache works → Uses cached data (faster)
   - **No failure modes**

2. **Optional Preload**: If `preload_tier1_stable_data()` fails, bot continues normally
   - Exception caught and logged
   - Prompt building falls back to fresh queries
   - **No degraded functionality**

3. **No Breaking Changes**: 
   - Tier 2/3 fields still fetch fresh (relationships, triggers, expertise, emoji)
   - Existing behavior preserved for dynamic fields
   - **Immediate CDL edit feedback maintained**

4. **Small Surface Area**:
   - Only 4 locations changed (voice traits, cultural expressions, AI scenarios, interest topics)
   - Each change is 3 lines: check cache → fallback to fresh
   - **Easy to review and test**

5. **Gradual Rollout**:
   - Can test on one bot first
   - Can disable by commenting out preload call
   - Can add debug logging to verify cache hits
   - **Low risk deployment**

---

## Performance Impact

### Query Reduction:
- **Before**: 9 queries per message
- **After**: 5 queries per message (relationships, emotional triggers, expertise domains, emoji patterns, + conditional response guidelines)
- **Reduction**: 44% fewer queries
- **Latency savings**: 4-20ms per message

### What Still Fetches Fresh (Tier 2/3):
- ✅ Relationships (immediate feedback)
- ✅ Emotional triggers (immediate feedback)
- ✅ Expertise domains (immediate feedback)
- ✅ Emoji patterns (immediate feedback)
- ✅ Response guidelines (conditional, rare access)

---

## Testing Plan

### 1. Test Cache Preload:
```bash
./multi-bot.sh restart elena
docker logs elena-bot --tail 50 | grep "TIER 1 CACHE"

# Expected output:
# ✅ TIER 1 CACHE: Preloaded 5 voice traits, 8 cultural expressions, 4 AI scenarios, 10 interest topics
```

### 2. Test Cache Usage:
```bash
# Send a message that triggers voice traits section
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Tell me about your work", "context": {}}'

# Check logs for cache hits (no "CACHE MISS" warnings)
docker logs elena-bot --tail 20 | grep "TIER 1"
```

### 3. Test Fallback:
```bash
# Temporarily break preload to test fallback
# (Comment out preload call in bot.py)
./multi-bot.sh restart elena

# Should see: "⚠️ TIER 1 CACHE MISS: Fetched voice traits fresh"
# Bot should still work normally
```

### 4. Test Dynamic Field Updates:
```bash
# Edit a relationship in database
psql -h localhost -p 5433 -U whisperengine_user -d whisperengine -c \
  "UPDATE character_relationships SET description = 'Updated relationship test' WHERE character_id = 1 LIMIT 1;"

# Send message immediately - should see updated relationship
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "test", "context": {}}'

# Check prompt log for "Updated relationship test"
docker exec elena-bot cat /app/logs/prompts/elena_*.json | jq '.messages[0].content' | grep "Updated relationship test"
```

---

## Rollback Plan

If anything goes wrong:

### Option 1: Disable Preload
```python
# In src/core/bot.py line ~260
# Comment out the preload call:
# await self.character_system.preload_tier1_stable_data()
```

### Option 2: Force Fresh Queries
```python
# In src/prompts/cdl_ai_integration.py
# Change cache checks to always fetch fresh:
voice_traits = self._cached_voice_traits if False else await self.enhanced_manager.get_voice_traits(bot_name)
```

### Option 3: Revert Commit
```bash
git revert <commit_hash>
./multi-bot.sh restart elena
```

---

## Code Size Estimate

- **New code**: ~50 lines total
  - 4 lines: Cache field declarations
  - 25 lines: Preload method
  - 12 lines: Cache lookups (3 lines × 4 fields)
  - 4 lines: Preload call in bot.py
  - 5 lines: Exception handling/logging

- **Files modified**: 2 files only
  - `src/prompts/cdl_ai_integration.py`
  - `src/core/bot.py`

- **Complexity**: LOW (cache-with-fallback is simple pattern)
- **Test time**: 10 minutes (restart + send test messages)

---

## Recommendation

**✅ IMPLEMENT NOW** - This is a safe, incremental improvement with:
- ✅ Minimal code changes (~50 lines)
- ✅ Zero risk (cache-with-fallback pattern)
- ✅ Easy rollback (comment out preload call)
- ✅ Immediate testing (restart + send message)
- ✅ 44% query reduction
- ✅ Maintains immediate feedback for tunable fields

**Priority**: MEDIUM - Low effort, medium benefit, zero risk

**Time estimate**: 30 minutes implementation + 10 minutes testing = 40 minutes total
