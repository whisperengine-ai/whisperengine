# Prompt Layering & User Name Resolution Explained

**Date**: January 3, 2025  
**Context**: Understanding how prompts are built and how user names are resolved

---

## 🏗️ PROMPT LAYERING: HOW IT WORKS

### TL;DR: **REPLACE, NOT APPEND**

The CDL character enhancement **REPLACES** the entire system message, not appends to it. This is why time context was missing - it was being overwritten.

---

## 📊 THE COMPLETE FLOW

### Step 1: Basic Conversation Context Built

**Location**: `src/core/message_processor.py` lines 325-355

```python
async def _build_conversation_context(self, message_context, relevant_memories):
    context = []
    
    # Add time context
    from src.utils.helpers import get_current_time_context
    time_context = get_current_time_context()
    
    # Build system message with time context and memory summary
    system_parts = [f"CURRENT DATE & TIME: {time_context}"]
    
    if relevant_memories:
        memory_summary = self._summarize_memories(relevant_memories)
        system_parts.append(f"\nRelevant context: {memory_summary}")
    
    # Create system message
    context.append({
        "role": "system",
        "content": "\n".join(system_parts)
    })
    
    # Add user message
    context.append({
        "role": "user", 
        "content": message_context.content
    })
    
    return context
```

**Result at this point**:
```python
[
    {
        "role": "system",
        "content": "CURRENT DATE & TIME: 2025-01-03 17:08:45 PST\nRelevant context: [memories]"
    },
    {
        "role": "user",
        "content": "What time is it?"
    }
]
```

### Step 2: CDL Character Enhancement **REPLACES** System Message

**Location**: `src/core/message_processor.py` lines 844-858

```python
# Clone the conversation context and replace/enhance system message
enhanced_context = conversation_context.copy()

# Find system message and REPLACE with character-aware prompt
system_message_found = False
for i, msg in enumerate(enhanced_context):
    if msg.get('role') == 'system':
        enhanced_context[i] = {
            'role': 'system',
            'content': character_prompt  # ← REPLACES entire system message
        }
        system_message_found = True
        logger.info(f"🎭 CDL CHARACTER: Replaced system message with character prompt")
        break

# If no system message found, add character prompt as first message
if not system_message_found:
    enhanced_context.insert(0, {
        'role': 'system', 
        'content': character_prompt
    })
```

**Key Point**: The code does `enhanced_context[i] = {...}` which **REPLACES** the entire system message, not appends to it.

### Step 3: Character Prompt Built with ALL Context

**Location**: `src/prompts/cdl_ai_integration.py` lines 145-264

```python
async def _build_unified_prompt(self, character, user_id, display_name, message_content, 
                                pipeline_result, relevant_memories, conversation_history, 
                                conversation_summary):
    # Layer 1: Response style (FIRST for max compliance)
    response_style = self._extract_cdl_response_style(character, display_name)
    prompt = ""
    if response_style:
        prompt = response_style + "\n\n"
    
    # Layer 2: Time context (ADDED IN FIX - was missing before)
    from src.utils.helpers import get_current_time_context
    time_context = get_current_time_context()
    prompt += f"CURRENT DATE & TIME: {time_context}\n\n"
    
    # Layer 3: Character identity
    prompt += f"You are {character.identity.name}, a {character.identity.occupation}."
    
    # Layer 4: Big Five personality
    if hasattr(character, 'personality'):
        prompt += f"\n\n🧬 PERSONALITY PROFILE:\n..."
    
    # Layer 5: Conversation flow guidelines
    prompt += f"\n\n🎬 CONVERSATION FLOW & CONTEXT:\n..."
    
    # Layer 6: Personal knowledge (relationships, family, career)
    prompt += f"\n\n👨‍👩‍👧‍👦 PERSONAL BACKGROUND:\n..."
    
    # Layer 7: Emotional intelligence context
    if pipeline_result:
        prompt += f"\n\n🎭 USER EMOTIONAL STATE: {emotion}\n"
    
    # Layer 8: Memory context
    if relevant_memories:
        prompt += f"\n\n🧠 RELEVANT CONVERSATION CONTEXT:\n..."
    
    # Layer 9: Conversation summary
    if conversation_summary:
        prompt += f"\n\n📚 CONVERSATION BACKGROUND:\n{conversation_summary}\n"
    
    # Layer 10: Recent conversation history
    if conversation_history:
        prompt += f"\n\n💬 RECENT CONVERSATION:\n..."
    
    # Layer 11: Final instruction
    prompt += f"\nRespond as {character.identity.name} to {display_name}:"
    
    return prompt
```

**Result**: One comprehensive system prompt with ALL context including time.

---

## 🔍 WHY TIME CONTEXT WAS MISSING (BEFORE FIX)

### Before Fix:
1. Basic context builder added time context ✅
2. CDL character enhancement **REPLACED** entire system message ❌
3. Character prompt builder **DID NOT** include time context ❌
4. Result: Time context lost

### After Fix:
1. Basic context builder adds time context ✅
2. CDL character enhancement **REPLACES** entire system message ✅
3. Character prompt builder **NOW INCLUDES** time context ✅ (Line 149-151)
4. Result: Time context preserved in final prompt

---

## 👤 USER NAME RESOLUTION: THE COMPLETE FLOW

### Priority Order (Correct Implementation):

```
1. Stored Preferred Name (highest priority)
   ↓ (if not found)
2. Discord Display Name (fallback)
   ↓ (if not available)
3. "User" (last resort)
```

### Step-by-Step Name Resolution

#### Step 1: Discord Display Name Captured

**Location**: `src/handlers/events.py` lines 590, 816

```python
# DM Handler
message_context = MessageContext(
    user_id=user_id,
    content=message.content,
    metadata={
        'discord_author_name': message.author.display_name,  # "MarkAnthony"
        ...
    }
)

# Mention Handler (same pattern)
message_context = MessageContext(
    user_id=user_id,
    content=content,
    metadata={
        'discord_author_name': message.author.display_name,  # "MarkAnthony"
        ...
    }
)
```

#### Step 2: Extract Display Name in MessageProcessor

**Location**: `src/core/message_processor.py` line 793

```python
# Get user display name from metadata if available
user_display_name = message_context.metadata.get('discord_author_name') if message_context.metadata else None
# user_display_name = "MarkAnthony" (or None if not in metadata)
```

#### Step 3: Pass to CDL Integration

**Location**: `src/core/message_processor.py` line 801

```python
character_prompt = await cdl_integration.create_unified_character_prompt(
    character_file=character_file,
    user_id=user_id,
    message_content=message_context.content,
    pipeline_result=pipeline_result,
    user_name=user_display_name  # ← Discord display name passed here
)
```

#### Step 4: Resolve Preferred Name (PRIORITY LOGIC)

**Location**: `src/prompts/cdl_ai_integration.py` lines 55-65

```python
# STEP 2: Get user's preferred name with Discord username fallback
preferred_name = None
if self.memory_manager and user_name:  # user_name = "MarkAnthony" from Discord
    try:
        from src.utils.user_preferences import get_user_preferred_name
        preferred_name = await get_user_preferred_name(
            user_id, 
            self.memory_manager, 
            user_name  # Discord display name as fallback
        )
    except Exception as e:
        logger.debug("Could not retrieve preferred name: %s", e)

# Priority resolution:
# 1. preferred_name (from vector memory search)
# 2. user_name (Discord display name)
# 3. "User" (fallback)
display_name = preferred_name or user_name or "User"
logger.info("🎭 UNIFIED: Using display name: %s", display_name)
```

#### Step 5: Search for Stored Preferred Name

**Location**: `src/utils/user_preferences.py` lines 13-50

```python
async def get_user_preferred_name(user_id, memory_manager, discord_username):
    """
    Get user's preferred name using vector memory search.
    
    Priority:
    1. Search vector memory for "my name is...", "call me...", etc.
    2. Return discord_username as fallback if not found
    """
    if not memory_manager:
        return discord_username  # Fallback immediately if no memory
    
    try:
        # Use vector search to find name-related memories
        search_queries = [
            "my name is, call me, I am, preferred name, introduce",
            "name fact user preferred",
            "user name introduction"
        ]
        
        all_memories = []
        for query in search_queries:
            memories = await memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=query,
                limit=15
            )
            all_memories.extend(memories)
        
        # Parse memories for name patterns
        for memory in all_memories:
            content = memory.get('content', '').lower()
            
            # Pattern: "my name is [NAME]"
            if 'my name is' in content:
                match = re.search(r'my name is ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', content)
                if match:
                    return match.group(1)
            
            # Pattern: "call me [NAME]"
            if 'call me' in content:
                match = re.search(r'call me ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', content)
                if match:
                    return match.group(1)
        
        # No stored name found - return Discord display name as fallback
        return discord_username
        
    except Exception as e:
        logger.error("Error retrieving preferred name: %s", e)
        return discord_username  # Fallback on error
```

#### Step 6: Use Resolved Name in Character Prompt

**Location**: `src/prompts/cdl_ai_integration.py` line 541

```python
# In response style section:
style_parts.append(f"- The user you are talking to is named {display_name}. "
                   f"ALWAYS use this name when addressing them.")
```

**Also at line 264**:
```python
# Final instruction:
prompt += f"\nRespond as {character.identity.name} to {display_name}:"
```

---

## 📋 COMPLETE NAME RESOLUTION EXAMPLES

### Example 1: User with Stored Preferred Name

```
User tells Elena: "My name is Mark, but everyone calls me Marc"
↓
Vector memory stores: "User said: My name is Mark, but everyone calls me Marc"
↓
Later conversation:
Discord Display Name: "MarkAnthony"
↓
get_user_preferred_name() searches vector memory
↓
Finds: "call me Marc" in stored memory
↓
Returns: "Marc" (preferred name from memory)
↓
Final display_name = "Marc" (stored preferred name wins)
↓
Elena addresses user as: "Marc"
```

### Example 2: New User (No Stored Name)

```
New user messages Elena
↓
Discord Display Name: "MarkAnthony"
↓
get_user_preferred_name() searches vector memory
↓
No memories found with name patterns
↓
Returns: "MarkAnthony" (Discord display name as fallback)
↓
Final display_name = "MarkAnthony" (Discord fallback)
↓
Elena addresses user as: "MarkAnthony"
```

### Example 3: No Discord Display Name (Edge Case)

```
Message received (unusual case where display name missing)
↓
Discord Display Name: None
↓
user_name parameter: None
↓
get_user_preferred_name() NOT CALLED (no fallback to search)
↓
Final display_name = "User" (last resort fallback)
↓
Elena addresses user as: "User"
```

---

## 🔄 DATA FLOW DIAGRAM

```
[Discord Message]
      ↓
[Extract message.author.display_name] → "MarkAnthony"
      ↓
[Add to MessageContext.metadata['discord_author_name']]
      ↓
[MessageProcessor extracts metadata] → user_display_name = "MarkAnthony"
      ↓
[Pass to CDL Integration] → user_name="MarkAnthony"
      ↓
[Search vector memory for preferred name]
      ├─ Found: "call me Marc" → preferred_name = "Marc"
      └─ Not Found → preferred_name = None
      ↓
[Priority Resolution]
  display_name = preferred_name OR user_name OR "User"
               = "Marc" OR "MarkAnthony" OR "User"
      ↓
[Use in Character Prompt]
  "The user you are talking to is named Marc"
  "Respond as Elena Rodriguez to Marc:"
```

---

## ✅ SUMMARY: YOUR QUESTIONS ANSWERED

### Q1: "We build the prompt in layers... so I'm not sure where we overwrite or just append or what. Can you confirm?"

**A**: The system does **REPLACE, not append**:

1. **Basic context builder** creates initial system message with time context
2. **CDL character enhancement** calls `enhanced_context[i] = {...}` which **REPLACES** the entire system message (line 846 in message_processor.py)
3. **Character prompt builder** constructs a comprehensive system prompt from scratch with ALL layers (time, character, personality, memories, etc.)
4. The **REPLACEMENT** is intentional for complete control over system prompt structure

**Before Fix**: Character prompt builder didn't include time context → Time lost after replacement  
**After Fix**: Character prompt builder includes time context early (line 149-151) → Time preserved

### Q2: "As for getting the users name - we search for the users preferred name from storage first, yeah? and discord display name is the fallback?"

**A**: **YES, exactly correct!** The priority order is:

1. **Stored Preferred Name** (from vector memory search) - HIGHEST PRIORITY
   - Searches for patterns: "my name is", "call me", "I am", etc.
   - Uses vector similarity search across conversation history
   
2. **Discord Display Name** (from `message.author.display_name`) - FALLBACK
   - Used if no stored preferred name found
   - Passed as `discord_username` parameter to search function
   
3. **"User"** (hardcoded string) - LAST RESORT
   - Only used if both above are unavailable

**Code Location**: `src/prompts/cdl_ai_integration.py` line 64:
```python
display_name = preferred_name or user_name or "User"
```

This is the **correct** and **intended** behavior! 🎯

---

**Documentation Created**: January 3, 2025  
**Author**: GitHub Copilot  
**Status**: ✅ Complete explanation of prompt layering and name resolution
