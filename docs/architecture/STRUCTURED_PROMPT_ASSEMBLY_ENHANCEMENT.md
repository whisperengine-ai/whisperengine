# Structured Prompt Assembly Enhancement

**Status**: 📋 READY TO START (Tech Debt)  
**Priority**: HIGH 🔥  
**Created**: October 11, 2025  
**Updated**: October 11, 2025 - Elevated to HIGH priority after alternation fixes  
**Category**: Architecture Enhancement

## Problem Statement

Currently, WhisperEngine assembles LLM prompts using **string concatenation** in a rigid, sequential order. This approach has several limitations:

### Current Implementation Issues:

```python
# CURRENT APPROACH: String concatenation (inflexible)
core_system = system_prompt_content + attachment_guard + guidance_clause
core_system_parts.append(f"\n\nRELEVANT MEMORIES: {memory_narrative}")
core_system_parts.append(f"\n\nCONVERSATION FLOW: {conversation_summary}")
consolidated_system = "".join(core_system_parts)
```

**Problems**:
1. ❌ **Cannot reorder** components based on priority/importance
2. ❌ **Hard to conditionally remove** sections
3. ❌ **Difficult to deduplicate** content
4. ❌ **No flexibility** for different LLM requirements
5. ❌ **String concat order is rigid** - set at code time, not runtime
6. ❌ **No token budget management** - can't drop low-priority sections if over limit
7. ❌ **Model-specific formatting difficult** - Claude vs OpenAI vs Mistral have different preferences

## Proposed Solution

Implement a **structured component assembly system** that builds prompts from discrete, metadata-enriched components before final rendering.

### Architecture Design:

```python
from dataclasses import dataclass
from typing import List, Callable, Optional, Dict, Any
from enum import Enum

class PromptComponentType(Enum):
    """Types of prompt components."""
    CORE_SYSTEM = "core_system"
    TIME_CONTEXT = "time_context"
    ATTACHMENT_GUARD = "attachment_guard"
    MEMORY = "memory"
    CONVERSATION_FLOW = "conversation_flow"
    USER_FACTS = "user_facts"
    GUIDANCE = "guidance"
    AI_INTELLIGENCE = "ai_intelligence"
    TRENDWISE_ADAPTATION = "trendwise_adaptation"
    ANTI_HALLUCINATION = "anti_hallucination"

@dataclass
class PromptComponent:
    """A discrete component of a system prompt with metadata."""
    type: PromptComponentType
    content: str
    priority: int  # Lower number = higher priority
    required: bool = False
    condition: Optional[Callable[[], bool]] = None
    token_cost: Optional[int] = None  # Estimated token count
    metadata: Dict[str, Any] = None
    
    def should_include(self) -> bool:
        """Determine if this component should be included."""
        if not self.content or not self.content.strip():
            return False
        if self.condition:
            return self.condition()
        return True

class PromptAssembler:
    """Assembles structured prompt components into final prompt."""
    
    def __init__(self, max_tokens: Optional[int] = None):
        self.max_tokens = max_tokens
        self.components: List[PromptComponent] = []
    
    def add_component(self, component: PromptComponent):
        """Add a component to the assembly queue."""
        self.components.append(component)
    
    def assemble(self, model_type: str = "generic") -> str:
        """Assemble components into final prompt.
        
        Args:
            model_type: LLM model type for model-specific formatting
                       ("openai", "anthropic", "mistral", "generic")
        
        Returns:
            Final assembled prompt string
        """
        # Filter components
        valid_components = [
            c for c in self.components 
            if c.should_include()
        ]
        
        # Sort by priority (lower number = higher priority)
        valid_components.sort(key=lambda c: c.priority)
        
        # Apply token budget if specified
        if self.max_tokens:
            valid_components = self._apply_token_budget(valid_components)
        
        # Deduplicate content
        valid_components = self._deduplicate(valid_components)
        
        # Model-specific formatting
        if model_type == "anthropic":
            return self._assemble_anthropic(valid_components)
        elif model_type == "openai":
            return self._assemble_openai(valid_components)
        elif model_type == "mistral":
            return self._assemble_mistral(valid_components)
        else:
            return self._assemble_generic(valid_components)
    
    def _apply_token_budget(self, components: List[PromptComponent]) -> List[PromptComponent]:
        """Drop low-priority optional components if over token budget."""
        total_tokens = sum(c.token_cost or len(c.content) // 4 for c in components)
        
        if total_tokens <= self.max_tokens:
            return components
        
        # Keep required components, drop optional ones starting from lowest priority
        required = [c for c in components if c.required]
        optional = [c for c in components if not c.required]
        
        # Add optional components until budget is reached
        current_tokens = sum(c.token_cost or len(c.content) // 4 for c in required)
        result = required.copy()
        
        for component in optional:
            component_tokens = component.token_cost or len(component.content) // 4
            if current_tokens + component_tokens <= self.max_tokens:
                result.append(component)
                current_tokens += component_tokens
        
        return result
    
    def _deduplicate(self, components: List[PromptComponent]) -> List[PromptComponent]:
        """Remove duplicate content across components."""
        seen_content = set()
        deduplicated = []
        
        for component in components:
            # Create content hash for deduplication
            content_key = component.content.strip()[:100]  # First 100 chars as key
            
            if content_key not in seen_content:
                deduplicated.append(component)
                seen_content.add(content_key)
        
        return deduplicated
    
    def _assemble_generic(self, components: List[PromptComponent]) -> str:
        """Generic assembly with section headers."""
        sections = []
        
        for component in components:
            if component.type == PromptComponentType.CORE_SYSTEM:
                sections.append(component.content)
            elif component.type == PromptComponentType.MEMORY:
                sections.append(f"\n\nRELEVANT MEMORIES:\n{component.content}")
            elif component.type == PromptComponentType.CONVERSATION_FLOW:
                sections.append(f"\n\nCONVERSATION FLOW:\n{component.content}")
            else:
                sections.append(f"\n\n{component.content}")
        
        return "".join(sections)
    
    def _assemble_anthropic(self, components: List[PromptComponent]) -> str:
        """Anthropic-specific assembly (prefers XML-like tags)."""
        sections = []
        
        for component in components:
            if component.type == PromptComponentType.MEMORY:
                sections.append(f"\n\n<memory>\n{component.content}\n</memory>")
            elif component.type == PromptComponentType.CONVERSATION_FLOW:
                sections.append(f"\n\n<conversation_context>\n{component.content}\n</conversation_context>")
            else:
                sections.append(f"\n\n{component.content}")
        
        return "".join(sections)
    
    def _assemble_openai(self, components: List[PromptComponent]) -> str:
        """OpenAI-specific assembly (prefers clear sections)."""
        # OpenAI likes clear section headers
        return self._assemble_generic(components)
    
    def _assemble_mistral(self, components: List[PromptComponent]) -> str:
        """Mistral-specific assembly."""
        # Mistral performs well with concise, structured prompts
        return self._assemble_generic(components)
```

### Usage Example:

```python
async def _build_conversation_context(
    self, message_context: MessageContext, relevant_memories: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """Build conversation context using structured assembly."""
    
    # Create assembler
    assembler = PromptAssembler(max_tokens=8000)
    
    # Add core system prompt (highest priority, required)
    assembler.add_component(PromptComponent(
        type=PromptComponentType.CORE_SYSTEM,
        content=system_prompt_content,
        priority=1,
        required=True,
        token_cost=estimate_tokens(system_prompt_content)
    ))
    
    # Add time context (high priority, required)
    assembler.add_component(PromptComponent(
        type=PromptComponentType.TIME_CONTEXT,
        content=f"CURRENT DATE & TIME: {time_context}",
        priority=2,
        required=True,
        token_cost=20
    ))
    
    # Add attachment guard (conditional)
    if message_context.attachments:
        assembler.add_component(PromptComponent(
            type=PromptComponentType.ATTACHMENT_GUARD,
            content=attachment_guard,
            priority=3,
            required=True,
            condition=lambda: len(message_context.attachments) > 0
        ))
    
    # Add memory narrative (important but optional)
    if memory_narrative:
        assembler.add_component(PromptComponent(
            type=PromptComponentType.MEMORY,
            content=memory_narrative,
            priority=4,
            required=False,
            token_cost=estimate_tokens(memory_narrative)
        ))
    else:
        # Anti-hallucination warning if no memory
        assembler.add_component(PromptComponent(
            type=PromptComponentType.ANTI_HALLUCINATION,
            content="⚠️ MEMORY STATUS: No previous conversation history found...",
            priority=4,
            required=True
        ))
    
    # Add conversation flow (optional)
    if conversation_summary:
        assembler.add_component(PromptComponent(
            type=PromptComponentType.CONVERSATION_FLOW,
            content=conversation_summary,
            priority=5,
            required=False,
            token_cost=estimate_tokens(conversation_summary)
        ))
    
    # Add guidance (required)
    assembler.add_component(PromptComponent(
        type=PromptComponentType.GUIDANCE,
        content=guidance_clause,
        priority=6,
        required=True,
        token_cost=50
    ))
    
    # Add AI intelligence guidance (optional)
    if ai_guidance:
        assembler.add_component(PromptComponent(
            type=PromptComponentType.AI_INTELLIGENCE,
            content=ai_guidance,
            priority=7,
            required=False
        ))
    
    # Assemble based on model type
    model_type = self._detect_model_type()  # "anthropic", "openai", "mistral"
    final_system_prompt = assembler.assemble(model_type=model_type)
    
    # Build conversation context
    conversation_context = [{"role": "system", "content": final_system_prompt}]
    
    # Add user/assistant messages...
    # (rest of implementation)
    
    return conversation_context
```

## Benefits

### Immediate Benefits:
1. ✅ **Dynamic reordering** - Prioritize most important content
2. ✅ **Conditional inclusion** - Easily add/remove sections based on context
3. ✅ **Token budget management** - Automatically drop low-priority sections if over limit
4. ✅ **Deduplication** - Prevent duplicate content across components
5. ✅ **Model-specific formatting** - Optimize for Claude, OpenAI, Mistral, etc.

### Future Benefits:
6. ✅ **A/B testing** - Easy to test different component orders
7. ✅ **Monitoring** - Track which components are included/dropped
8. ✅ **Debugging** - Inspect individual components
9. ✅ **Extensibility** - Add new component types without refactoring
10. ✅ **Configuration** - External config files can control component priority/inclusion

## Implementation Plan

### Phase 1: Core Infrastructure (Sprint 1)
- [ ] Create `PromptComponent` dataclass
- [ ] Create `PromptComponentType` enum
- [ ] Create `PromptAssembler` class with basic assembly
- [ ] Add unit tests for assembler

### Phase 2: Integration (Sprint 2)
- [ ] Refactor `_build_conversation_context()` to use structured assembly
- [ ] Migrate all system prompt components to structured format
- [ ] Add token estimation helper
- [ ] Integration tests with actual bots

### Phase 3: Model-Specific Formatting (Sprint 3)
- [ ] Implement Anthropic-specific assembly (XML tags)
- [ ] Implement OpenAI-specific assembly
- [ ] Implement Mistral-specific assembly
- [ ] Model detection helper
- [ ] A/B testing framework

### Phase 4: Advanced Features (Sprint 4)
- [ ] Token budget management with automatic component dropping
- [ ] Content deduplication across components
- [ ] Component inclusion monitoring/logging
- [ ] External configuration support
- [ ] Performance optimization

## Migration Strategy

### Safe Migration Path:
1. **Parallel implementation** - Build new system alongside existing
2. **Feature flag** - `USE_STRUCTURED_PROMPT_ASSEMBLY=true/false`
3. **Gradual rollout** - Test with one bot first (Jake or Ryan for simplicity)
4. **Monitoring** - Compare prompt outputs between old/new systems
5. **Rollback plan** - Keep old system for quick revert if issues
6. **Full migration** - Remove old code once validated

### Validation Requirements:
- ✅ All existing tests pass
- ✅ Prompt outputs identical (or improved) compared to old system
- ✅ No performance regression
- ✅ All bots tested with new system
- ✅ Edge cases handled (no memory, long conversations, attachments)

## Files to Modify

### Core Changes:
- `src/core/message_processor.py` - Main prompt building logic
- `src/prompts/prompt_assembler.py` (NEW) - Structured assembly system
- `src/prompts/prompt_components.py` (NEW) - Component definitions

### Supporting Changes:
- `src/utils/token_estimation.py` (NEW) - Token counting helper
- `tests/unit/test_prompt_assembler.py` (NEW) - Unit tests
- `tests/integration/test_structured_prompts.py` (NEW) - Integration tests

## Risks & Mitigation

### Risks:
1. **Breaking existing functionality** - Prompts might change unexpectedly
   - *Mitigation*: Feature flag + extensive testing + parallel implementation
2. **Performance impact** - Additional processing overhead
   - *Mitigation*: Profile and optimize, cache assembled prompts where possible
3. **Increased complexity** - More code to maintain
   - *Mitigation*: Clear documentation, comprehensive tests, simple API design
4. **Migration bugs** - Edge cases not handled in new system
   - *Mitigation*: Gradual rollout, one bot at a time, keep old system as fallback

## Success Metrics

### Must Have:
- ✅ All existing tests pass
- ✅ Zero functional regressions
- ✅ Prompt quality maintained or improved

### Nice to Have:
- ✅ 20% reduction in average prompt size (via smart component dropping)
- ✅ Support for 3+ different LLM model types
- ✅ Token budget management prevents context overflow errors
- ✅ Improved debugging via component inspection

## Related Documentation

- `MEMORY_HALLUCINATION_FIX.md` - Recent memory system fixes
- `MESSAGE_LIMITS_AUDIT.md` - Current message/memory limits
- `WHISPERENGINE_ARCHITECTURE_EVOLUTION.md` - System architecture timeline

## Notes

**Why HIGH Priority Now?**
- ✅ Message alternation bugs exposed fragility of string concatenation approach
- ✅ System recently stabilized after fixing 5 critical memory bugs + alternation fixes
- ✅ Current fix works but is architectural band-aid, not long-term solution
- ✅ Structured assembly prevents alternation issues by design
- ✅ Unlocks token budget management, model-specific formatting, better debugging
- ✅ User approved elevation to HIGH priority after seeing alternation problems

**When to Implement?**
- 🎯 **NEXT**: After Jake/Elena testing confirms alternation fixes are working
- After system has been stable for a few days with current fixes
- Before adding new LLM APIs that require different prompt formats
- Before token budget management becomes critical blocker

**Why Not Immediate?**
- Need to validate current alternation fixes work correctly first
- Want baseline stability before major refactor
- Need comprehensive test coverage for safe migration
- Risk of introducing new bugs during structural changes

**Alternatives Considered**:
1. **Keep current approach** - Works but inflexible
2. **Template-based system** - Less flexible than component-based
3. **LLM-specific subclasses** - More complex, harder to maintain

---

**Status**: 📋 READY TO START - Awaiting alternation fix validation  
**Priority**: HIGH 🔥 - Architectural improvement to prevent future alternation issues  
**Estimated Effort**: 2-3 weeks (4 sprints as outlined above)  
**Next Steps**: 
1. Validate current alternation fixes with Jake/Elena testing
2. Create detailed implementation plan with test strategy
3. Begin Phase 1: Core Infrastructure implementation

