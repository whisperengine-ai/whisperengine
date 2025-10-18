# CDL to PromptComponent Mapping

**Date**: October 18, 2025  
**Purpose**: Map CDL prompt sections to PromptComponent architecture for unified assembly  
**Status**: Analysis phase for Option 1 implementation

---

## 📋 Current CDL Prompt Structure

Based on `_build_unified_prompt()` in `src/prompts/cdl_ai_integration.py:809-2100`

### **Section Order in CDL System**:

```
1. Character Identity Foundation (line 833-841)
2. Trigger-Based Mode Detection (line 844-882)
3. Dynamic Custom Fields (line 884-893)
4. AI Identity Guidance (line 896-909)
5. Temporal Awareness (line 912-916)
6. User Personality & Facts (line 918-928)
7. Big Five Personality (line 933-1006)
8. Character Learning Persistence (line 1020-1067)
9. Character Learning Moments (line 1069-1105)
10. Voice & Communication Style (line 1107-1111)
11. Relationships (line 1122-1147)
12. Emotional Triggers (line 1218-1275)
13. Character Episodic Memories (line 1960-1995)
14. Conversation Background Summary (line 1997-1998)
15. Unified Character Intelligence (line 2000-2071)
16. Intent-Based Knowledge Sprinkling (line 1335-1520)
17. Response Style Reminder (line ~1778, end of prompt)
```

---

## 🎯 Proposed PromptComponent Mapping

### **Component Type Enum Extensions**:

```python
class PromptComponentType(Enum):
    # Existing types (keep these)
    CORE_SYSTEM = "core_system"
    MEMORY = "memory"
    USER_FACTS = "user_facts"
    CONVERSATION_FLOW = "conversation_flow"
    ANTI_HALLUCINATION = "anti_hallucination"
    GUIDANCE = "guidance"
    ATTACHMENT_GUARD = "attachment_guard"
    
    # New CDL types
    CHARACTER_IDENTITY = "character_identity"           # Priority 1
    CHARACTER_MODE = "character_mode"                   # Priority 2
    CHARACTER_BACKSTORY = "character_backstory"         # Priority 3
    CHARACTER_PRINCIPLES = "character_principles"       # Priority 4
    AI_IDENTITY_GUIDANCE = "ai_identity_guidance"       # Priority 5
    TEMPORAL_AWARENESS = "temporal_awareness"           # Priority 6
    USER_PERSONALITY = "user_personality"               # Priority 7
    CHARACTER_PERSONALITY = "character_personality"     # Priority 8 (Big Five)
    CHARACTER_LEARNING = "character_learning"           # Priority 9
    CHARACTER_VOICE = "character_voice"                 # Priority 10
    CHARACTER_RELATIONSHIPS = "character_relationships" # Priority 11
    EMOTIONAL_TRIGGERS = "emotional_triggers"           # Priority 12
    EPISODIC_MEMORIES = "episodic_memories"            # Priority 13
    CONVERSATION_SUMMARY = "conversation_summary"       # Priority 14
    UNIFIED_INTELLIGENCE = "unified_intelligence"       # Priority 15
    KNOWLEDGE_CONTEXT = "knowledge_context"             # Priority 16
    RESPONSE_STYLE = "response_style"                   # Priority 17 (end)
```

---

## 🏗️ Component Factory Functions

### **1. Character Identity Component**

**Source**: `_build_unified_prompt` lines 833-841  
**Data**: Character.identity (name, occupation, description)  
**Priority**: 1 (highest)  
**Required**: Yes

```python
def create_character_identity_component(
    character,
    priority: int = 1
) -> PromptComponent:
    """
    Create character identity foundation component.
    
    Example output:
    "You are Elena Martinez, a marine biologist. [description]"
    """
    character_name = character.identity.name if character.identity.name else "AI Character"
    character_occupation = character.identity.occupation if character.identity.occupation else "AI Assistant"
    
    content = f"You are {character_name}, a {character_occupation}."
    
    if hasattr(character.identity, 'description') and character.identity.description:
        content += f" {character.identity.description}"
    
    return PromptComponent(
        type=PromptComponentType.CHARACTER_IDENTITY,
        content=content,
        priority=priority,
        required=True,
        token_budget=200  # Very compact
    )
```

---

### **2. Character Mode Component**

**Source**: `_build_unified_prompt` lines 844-882  
**Data**: TriggerModeController.detect_active_mode()  
**Priority**: 2  
**Required**: No (context-dependent)

```python
async def create_character_mode_component(
    character_name: str,
    message_content: str,
    trigger_mode_controller,
    previous_mode: Optional[str],
    priority: int = 2
) -> Optional[PromptComponent]:
    """
    Create trigger-based mode detection component.
    
    Detects context (storytelling, philosophical, educational, etc.)
    and applies appropriate interaction guidance.
    """
    try:
        mode_detection_result = await trigger_mode_controller.detect_active_mode(
            character_name=character_name,
            message_content=message_content,
            previous_mode=previous_mode
        )
        
        if mode_detection_result.active_mode:
            # Get mode-specific guidance
            mode_content = trigger_mode_controller.get_mode_guidance(
                mode_detection_result.active_mode
            )
            
            return PromptComponent(
                type=PromptComponentType.CHARACTER_MODE,
                content=mode_content,
                priority=priority,
                required=False,
                token_budget=500,
                metadata={
                    'mode_name': mode_detection_result.active_mode.mode_name,
                    'confidence': mode_detection_result.active_mode.confidence,
                    'triggers': mode_detection_result.detected_triggers
                }
            )
    except Exception as e:
        logger.debug(f"Could not detect interaction mode: {e}")
        return None
```

---

### **3. Character Backstory Component**

**Source**: `_build_unified_prompt` lines 884-893 (dynamic custom fields)  
**Data**: Character.backstory, Character.custom_fields  
**Priority**: 3  
**Required**: Yes (for character depth)

```python
async def create_character_backstory_component(
    character,
    priority: int = 3
) -> PromptComponent:
    """
    Create character backstory and custom fields component.
    
    Includes professional background, personal history, formative experiences.
    """
    content_parts = []
    
    try:
        full_character_data = character.get_full_character_data()
        
        # Extract backstory sections
        if 'backstory' in full_character_data:
            content_parts.append(f"\\n\\nBACKSTORY:\\n{full_character_data['backstory']}")
        
        # Extract other custom sections dynamically
        for section_name, section_data in full_character_data.items():
            if section_name not in ['identity', 'backstory', 'personality']:
                if isinstance(section_data, str):
                    content_parts.append(f"\\n\\n{section_name.upper()}:\\n{section_data}")
    
    except Exception as e:
        logger.debug(f"Could not build backstory: {e}")
    
    content = "".join(content_parts) if content_parts else ""
    
    return PromptComponent(
        type=PromptComponentType.CHARACTER_BACKSTORY,
        content=content,
        priority=priority,
        required=True,
        token_budget=2000  # Can be large
    )
```

---

### **4. Character Principles Component**

**Source**: Would be part of dynamic custom fields  
**Data**: Character.core_principles, Character.beliefs, Character.values  
**Priority**: 4  
**Required**: Yes (for personality depth)

```python
def create_character_principles_component(
    character,
    priority: int = 4
) -> PromptComponent:
    """
    Create character core principles and beliefs component.
    
    Includes values, motivations, life philosophy, ethical framework.
    """
    content_parts = []
    
    if hasattr(character, 'core_principles') and character.core_principles:
        content_parts.append(f"\\n\\nCORE PRINCIPLES:\\n{character.core_principles}")
    
    if hasattr(character, 'values') and character.values:
        content_parts.append(f"\\n\\nVALUES:\\n{character.values}")
    
    if hasattr(character, 'beliefs') and character.beliefs:
        content_parts.append(f"\\n\\nBELIEFS:\\n{character.beliefs}")
    
    content = "".join(content_parts) if content_parts else ""
    
    return PromptComponent(
        type=PromptComponentType.CHARACTER_PRINCIPLES,
        content=content,
        priority=priority,
        required=True,
        token_budget=1000
    )
```

---

### **5. AI Identity Guidance Component**

**Source**: `_build_unified_prompt` lines 896-909  
**Data**: Keyword detection for AI-related questions  
**Priority**: 5  
**Required**: No (context-dependent)

```python
async def create_ai_identity_guidance_component(
    character_name: str,
    message_content: str,
    keyword_manager,
    priority: int = 5
) -> Optional[PromptComponent]:
    """
    Create AI identity guidance for handling direct AI questions.
    
    Archetype-specific handling (Real-World, Fantasy, Narrative AI).
    """
    try:
        if await keyword_manager.check_message_for_category(message_content, 'ai_identity'):
            content = f" If asked about AI nature, respond authentically as {character_name} while being honest about your AI nature when directly asked."
            
            return PromptComponent(
                type=PromptComponentType.AI_IDENTITY_GUIDANCE,
                content=content,
                priority=priority,
                required=False,
                token_budget=200
            )
    except Exception:
        # Fallback keyword detection
        if any(keyword in message_content.lower() for keyword in ['ai', 'artificial intelligence', 'robot', 'bot']):
            content = f" If asked about AI nature, respond authentically as {character_name}."
            return PromptComponent(
                type=PromptComponentType.AI_IDENTITY_GUIDANCE,
                content=content,
                priority=priority,
                required=False,
                token_budget=200
            )
    
    return None
```

---

### **6. Temporal Awareness Component**

**Source**: `_build_unified_prompt` lines 912-916  
**Data**: `get_current_time_context()`  
**Priority**: 6  
**Required**: Yes

```python
def create_temporal_awareness_component(
    priority: int = 6
) -> PromptComponent:
    """
    Create temporal awareness component with current date/time.
    """
    from src.utils.helpers import get_current_time_context
    time_context = get_current_time_context()
    
    return PromptComponent(
        type=PromptComponentType.TEMPORAL_AWARENESS,
        content=f"\\n\\nCURRENT DATE & TIME: {time_context}\\n\\n",
        priority=priority,
        required=True,
        token_budget=100
    )
```

---

### **7-17. Additional Components**

Following the same pattern for:
- **User Personality Component** (Priority 7)
- **Character Personality Component** (Priority 8 - Big Five)
- **Character Learning Component** (Priority 9)
- **Character Voice Component** (Priority 10)
- **Character Relationships Component** (Priority 11)
- **Emotional Triggers Component** (Priority 12)
- **Episodic Memories Component** (Priority 13)
- **Conversation Summary Component** (Priority 14)
- **Unified Intelligence Component** (Priority 15)
- **Knowledge Context Component** (Priority 16)
- **Response Style Component** (Priority 17)

---

## 🔄 Integration with PromptAssembler

### **Current Phase 4 Pattern**:

```python
async def _build_conversation_context_structured(
    self, message_context: MessageContext, relevant_memories: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    # Initialize assembler
    assembler = create_prompt_assembler(max_tokens=16000)
    
    # Add components
    assembler.add_component(create_core_system_component(..., priority=1))
    assembler.add_component(create_user_facts_component(..., priority=3))
    assembler.add_component(create_memory_component(..., priority=5))
    
    # Assemble system message
    system_message_content = assembler.assemble(model_type="generic")
    
    # Build conversation context
    conversation_context = [
        {"role": "system", "content": system_message_content}
    ]
    
    # Add recent messages
    recent_messages = await self._get_recent_messages_structured(message_context.user_id)
    conversation_context.extend(recent_messages)
    
    return conversation_context
```

### **Proposed Unified Pattern**:

```python
async def _build_conversation_context_structured(
    self, message_context: MessageContext, relevant_memories: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    # Initialize assembler (increase budget for CDL richness)
    assembler = create_prompt_assembler(max_tokens=20000)
    
    # Get character and CDL system
    character = await self._load_character_for_assembly()
    
    # ==========================
    # CDL COMPONENTS (Priority 1-17)
    # ==========================
    
    # 1. Character Identity (MUST come first)
    assembler.add_component(
        create_character_identity_component(character, priority=1)
    )
    
    # 2. Character Mode (context-dependent)
    mode_component = await create_character_mode_component(
        character_name=character.identity.name,
        message_content=message_context.content,
        trigger_mode_controller=self.cdl_integration.trigger_mode_controller,
        previous_mode=self.cdl_integration._previous_mode,
        priority=2
    )
    if mode_component:
        assembler.add_component(mode_component)
    
    # 3. Character Backstory
    assembler.add_component(
        await create_character_backstory_component(character, priority=3)
    )
    
    # 4. Character Principles
    assembler.add_component(
        create_character_principles_component(character, priority=4)
    )
    
    # 5. AI Identity Guidance (context-dependent)
    ai_identity_component = await create_ai_identity_guidance_component(
        character_name=character.identity.name,
        message_content=message_context.content,
        keyword_manager=self.keyword_manager,
        priority=5
    )
    if ai_identity_component:
        assembler.add_component(ai_identity_component)
    
    # 6. Temporal Awareness
    assembler.add_component(
        create_temporal_awareness_component(priority=6)
    )
    
    # 7. User Personality & Facts
    user_personality_component = await create_user_personality_component(
        user_id=message_context.user_id,
        message_content=message_context.content,
        cdl_integration=self.cdl_integration,
        priority=7
    )
    if user_personality_component:
        assembler.add_component(user_personality_component)
    
    # 8. Character Personality (Big Five)
    big_five_component = await create_character_personality_component(
        character=character,
        ai_components=getattr(self, '_ai_components', {}),
        priority=8
    )
    if big_five_component:
        assembler.add_component(big_five_component)
    
    # ... Continue for all 17 priorities ...
    
    # Assemble system message
    system_message_content = assembler.assemble(model_type="generic")
    
    # Build conversation context
    conversation_context = [
        {"role": "system", "content": system_message_content}
    ]
    
    # Add recent messages
    recent_messages = await self._get_recent_messages_structured(message_context.user_id)
    conversation_context.extend(recent_messages)
    
    return conversation_context
```

---

## 📊 Token Budget Allocation

**Total Budget**: 20,000 tokens (~80K characters)  
**Upgrade from**: 16,000 tokens (Phase 4 original)

| Component | Priority | Token Budget | Required |
|-----------|----------|--------------|----------|
| Character Identity | 1 | 200 | Yes |
| Character Mode | 2 | 500 | No |
| Character Backstory | 3 | 2000 | Yes |
| Character Principles | 4 | 1000 | Yes |
| AI Identity Guidance | 5 | 200 | No |
| Temporal Awareness | 6 | 100 | Yes |
| User Personality | 7 | 1000 | No |
| Character Personality (Big Five) | 8 | 800 | Yes |
| Character Learning | 9 | 1000 | No |
| Character Voice | 10 | 1500 | Yes |
| Character Relationships | 11 | 800 | No |
| Emotional Triggers | 12 | 600 | No |
| Episodic Memories | 13 | 1500 | No |
| Conversation Summary | 14 | 800 | No |
| Unified Intelligence | 15 | 2000 | Yes |
| Knowledge Context | 16 | 1000 | No |
| Response Style | 17 | 200 | Yes |
| **Total** | - | **~15,200** | - |

**Safety Margin**: ~4,800 tokens (~24%)

---

## 🎯 Migration Strategy

### **Phase 1: Component Creation** (1 day)
- Add new PromptComponentType enum values
- Create factory functions for all 17 CDL components
- Test each component independently

### **Phase 2: Integration** (1 day)
- Modify `_build_conversation_context_structured()` to use CDL components
- Remove `_apply_cdl_character_enhancement()` call from `_generate_response()`
- Fix `_build_conversation_context_with_ai_intelligence()` duplicate rebuild

### **Phase 3: Testing** (0.5 days)
- Direct Python validation
- Live Discord message testing
- Token count verification

### **Phase 4: Cleanup** (0.5 days)
- Deprecate old methods
- Update documentation
- Remove legacy code paths

**Total Effort**: 3 days

---

## ✅ Success Criteria

1. **Single Assembly Point**: All prompts built in `_build_conversation_context_structured()`
2. **No Replacement Logic**: System message never replaced after assembly
3. **Token Budget Enforced**: PromptAssembler manages all component sizes
4. **Character Fidelity**: All CDL personality data preserved
5. **Performance**: ~150ms savings per message (29% reduction)
6. **Maintainability**: Clear ownership for each prompt component

---

## 📚 Next Steps

1. ✅ Component mapping complete (this document)
2. ⏭️ Implement component factory functions
3. ⏭️ Update `_build_conversation_context_structured()`
4. ⏭️ Remove legacy CDL enhancement
5. ⏭️ Test and validate
