# Time Windows & Timeouts Audit

**Date**: October 4, 2025  
**Purpose**: Comprehensive review of all time-based thresholds across WhisperEngine

## Executive Summary

**ISSUE FOUND**: Multiple time windows were too long, causing conversation context mixing.

## 1. Conversation History Windows

### ✅ FIXED: Conversation History Retrieval
**File**: `src/memory/vector_memory_system.py:4591`
- **Before**: 7 days (`timedelta(days=7)`)
- **After**: 1 hour (`timedelta(hours=1)`)
- **Purpose**: Get recent messages for current conversation thread
- **Rationale**: 7 days was mixing completely different conversations. 1 hour captures current active thread.
- **Backup**: Conversation summary + memory narrative provide long-term context

### ⚠️ NEEDS REVIEW: Recent Memory Cutoff (Multiple Locations)
**File**: `src/memory/vector_memory_system.py:1254`
```python
recent_cutoff = datetime.utcnow() - timedelta(days=7)  # Last 7 days
```
- **Current**: 7 days
- **Purpose**: Define "recent" memories for prioritization
- **Recommendation**: Consider reducing to 24-48 hours for active context, keep 7 days for memory statistics

**File**: `src/memory/vector_memory_system.py:2467, 2473`
```python
recent_cutoff_dt = datetime.utcnow() - timedelta(hours=4)
```
- **Current**: 4 hours
- **Purpose**: Recent memories in fidelity-first retrieval
- **Status**: ✅ APPROPRIATE - Good balance for recent vs older memories

**File**: `src/memory/vector_memory_system.py:2477`
```python
recent_cutoff_dt = datetime.utcnow() - timedelta(hours=24)
```
- **Current**: 24 hours
- **Purpose**: Fallback recent memory window
- **Status**: ✅ APPROPRIATE

### Memory Narrative Recent Window
**File**: `src/core/message_processor.py:266, 418`
```python
filters["recency_hours"] = 2
if (datetime.now() - memory_time) < timedelta(hours=2):
```
- **Current**: 2 hours
- **Purpose**: Prioritize very recent memories in narrative
- **Status**: ✅ APPROPRIATE - Good for "what we just talked about"

## 2. Thread & Session Management

### Thread Timeout
**File**: `src/conversation/advanced_thread_manager.py:204`
```python
thread_timeout_hours: int = 48
```
- **Current**: 48 hours (2 days)
- **Purpose**: Auto-close inactive threads
- **Status**: ✅ APPROPRIATE - Discord threads can span multiple days

### Thread Activity Detection
**File**: `src/conversation/advanced_thread_manager.py:356`
```python
if time_since_last < timedelta(hours=2):  # Recent activity
```
- **Current**: 2 hours
- **Purpose**: Consider thread "recently active"
- **Status**: ✅ APPROPRIATE

### Session Timeout
**File**: `src/conversation/boundary_manager.py:139`
**File**: `src/conversation/concurrent_conversation_manager.py:146`
```python
session_timeout_minutes: int = 30
```
- **Current**: 30 minutes
- **Purpose**: Auto-end inactive sessions
- **Status**: ⚠️ QUESTIONABLE - May be too short for thoughtful conversations
- **Recommendation**: Consider 60-90 minutes for deeper discussions

### Context Switch Detection
**File**: `src/conversation/enhanced_context_manager.py:217`
```python
time_gap_threshold_minutes: int = 30
```
- **Current**: 30 minutes
- **Purpose**: Detect conversation breaks/topic switches
- **Status**: ✅ APPROPRIATE - Good balance for context switching

## 3. Question/Response Timeouts

### Question Auto-Resolve
**File**: `src/conversation/persistent_conversation_manager.py:195`
```python
self.question_timeout_hours = 24  # Auto-resolve after 24h
```
- **Current**: 24 hours
- **Purpose**: Auto-close unanswered questions
- **Status**: ✅ APPROPRIATE

### Reminder Delays
**File**: `src/conversation/persistent_conversation_manager.py:196`
```python
self.gentle_reminder_delay_minutes = 15  # Wait before first reminder
```
- **Current**: 15 minutes
- **Purpose**: Delay before sending reminder
- **Status**: ✅ APPROPRIATE - Not too pushy

## 4. Memory Lifecycle

### Memory Tier Management
**File**: `src/memory/vector_memory_system.py:1860-1874`
```python
# Working tier → Core tier promotion
if age_days >= 3 and (significance >= 0.6 or emotional_intensity >= 0.7):
    # Promote to core

# Working tier → Expired
elif age_days >= 7 and significance < 0.3:
    stats["expired"] += 1

# Core tier → Archive promotion
if age_days >= 7 and (significance >= 0.8 or emotional_intensity >= 0.9):
    # Promote to archive

# Core tier → Demotion
elif age_days >= 14 and significance < 0.4:
    # Demote
```
- **Status**: ✅ APPROPRIATE - Good tiered aging system

### Recent Memory Detection
**File**: `src/memory/vector_memory_system.py:4326`
```python
def _is_recent_memory(self, timestamp: str, hours: int = 24) -> bool:
```
- **Current**: 24 hours default
- **Status**: ✅ APPROPRIATE - Good definition of "recent"

## 5. HTTP/API Timeouts

### Health Check Timeouts
**File**: `src/handlers/status.py:458, 474`
```python
timeout = aiohttp.ClientTimeout(total=5)
```
- **Current**: 5 seconds
- **Status**: ✅ APPROPRIATE - Health checks should be fast

### Performance Test Timeouts
**File**: `src/handlers/simple_performance_commands.py:292, 311`
```python
timeout=aiohttp.ClientTimeout(total=2)
```
- **Current**: 2 seconds
- **Status**: ✅ APPROPRIATE - Quick performance checks

### Discord Reaction Wait
**File**: `src/handlers/memory.py:1265`
```python
reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
```
- **Current**: 30 seconds
- **Status**: ✅ APPROPRIATE - Give users time to react

## 6. Backup/Cleanup Windows

### Recent Week Stats
**File**: `src/memory/vector_memory_system.py:4899`
```python
'start': datetime.utcnow() - timedelta(days=7),  # Recent week
```
- **Current**: 7 days
- **Purpose**: Weekly memory statistics
- **Status**: ✅ APPROPRIATE - Week is a good stats window

### Thread Activity Cleanup
**File**: `src/conversation/advanced_thread_manager.py:1154`
```python
cutoff_time = datetime.now() - timedelta(hours=24)
```
- **Current**: 24 hours
- **Purpose**: Clean up old thread activity
- **Status**: ✅ APPROPRIATE

## Recommendations Summary

### ✅ NO ACTION NEEDED (Appropriate)
- Memory narrative recent window: 2 hours
- Thread timeout: 48 hours
- Thread activity detection: 2 hours
- Context switch detection: 30 minutes
- Question auto-resolve: 24 hours
- Reminder delays: 15 minutes
- Recent memory definition: 24 hours
- HTTP timeouts: 2-5 seconds
- Memory tier aging: 3-14 days

### ⚠️ CONSIDER ADJUSTING
1. **Session timeout**: 30 minutes → 60-90 minutes
   - Rationale: Allow deeper, more thoughtful conversations
   - Impact: Better for complex discussions, slight memory increase

2. **Recent memory cutoff** (line 1254): 7 days → 24-48 hours
   - Rationale: More focused "recent" definition for active context
   - Impact: Better memory prioritization
   - Note: Keep 7 days for historical statistics

### ✅ ALREADY FIXED
1. **Conversation history window**: 7 days → 1 hour ✅
   - Fixed context mixing issues
   - Long-term context preserved via conversation summary

## Testing Recommendations

1. Monitor conversation continuity with 1-hour window
2. Test session timeout with longer conversations (30 min may be too short)
3. Validate memory tier promotions with current day thresholds
4. Ensure context switching detection works at 30-minute threshold

## Configuration Suggestions

Consider making these configurable via environment variables:
```bash
# Conversation windows
CONVERSATION_HISTORY_HOURS=1          # Current thread detail
MEMORY_NARRATIVE_HOURS=2              # Recent memory narrative
RECENT_MEMORY_HOURS=24                # "Recent" memory definition

# Session management
SESSION_TIMEOUT_MINUTES=60            # Consider increasing from 30
CONTEXT_SWITCH_MINUTES=30             # Topic switch detection
THREAD_TIMEOUT_HOURS=48               # Thread auto-close

# Memory lifecycle
MEMORY_TIER_PROMOTION_DAYS=3          # Working → Core
MEMORY_TIER_EXPIRY_DAYS=7             # Working → Expired
MEMORY_ARCHIVE_DAYS=7                 # Core → Archive
```

## Impact Assessment

**High Impact (Already Fixed):**
- ✅ Conversation history window: Eliminates context mixing

**Medium Impact (Consider):**
- Session timeout increase: Better for complex conversations
- Recent memory cutoff adjustment: Improved context prioritization

**Low Impact (Optional):**
- Making timeouts configurable: Better operational flexibility
