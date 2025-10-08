# STEP2 Cross-Pollination Integration Plan

**Date**: October 8, 2025  
**Status**: PLAN  
**Scope**: Cross-Pollination Enhancement Integration

---

## Overview

The Cross-Pollination Enhancement connects character knowledge with user facts from the SemanticKnowledgeRouter. This integration plan outlines how to update the CDL AI Integration to incorporate cross-pollination features and pass user_id to the CharacterGraphManager.

## Key Components

1. **Update CDL AI Integration Constructor**: Add semantic_router parameter
2. **Update _extract_cdl_personal_knowledge_sections**: Add user_id parameter
3. **Add Cross-Pollination Integration**: Create new method for cross-pollination results
4. **Update _get_graph_manager**: Pass semantic_router to create_character_graph_manager
5. **Update create_character_aware_prompt**: Pass user_id to personal knowledge extraction

## Implementation Plan

### 1. Update CDL AI Integration Constructor

```python
def __init__(self, vector_memory_manager=None, llm_client=None, 
             knowledge_router=None, bot_core=None, semantic_router=None):
    self.memory_manager = vector_memory_manager
    self.llm_client = llm_client
    self.knowledge_router = knowledge_router
    self.semantic_router = semantic_router  # NEW: Store semantic router for user facts
    self.bot_core = bot_core  # Store bot_core for personality profiler access
```

### 2. Update _extract_cdl_personal_knowledge_sections Method

```python
async def _extract_cdl_personal_knowledge_sections(self, character, message_content: str, user_id: str = None) -> str:
    """
    Extract relevant personal knowledge sections using CharacterGraphManager.
    
    STEP 1: Basic graph intelligence integration
    STEP 2: Cross-pollination with user facts
    
    Args:
        character: Character object
        message_content: User message
        user_id: Optional user ID for cross-pollination
    """
    # ... existing code ...
    
    # If user_id provided, pass to query_character_knowledge for cross-pollination
    result = await graph_manager.query_character_knowledge(
        character_name=character.identity.name,
        query_text=message_content,
        intent=CharacterKnowledgeIntent.FAMILY,
        limit=3,
        user_id=user_id  # NEW: Pass user_id for cross-pollination
    )
```

### 3. Add Cross-Pollination Integration Method

```python
async def _incorporate_cross_pollination_results(self, character, result, personal_sections):
    """
    Incorporate cross-pollination results into personal knowledge sections.
    
    Args:
        character: Character object
        result: CharacterKnowledgeResult with cross-pollination
        personal_sections: List to add sections to
    """
    # Find cross-pollinated entries (marked with cross_pollinated=True)
    cross_pollinated_entries = []
    
    for entry in result.background:
        if entry.get('cross_pollinated'):
            cross_pollinated_entries.append(entry)
    
    for entry in result.abilities:
        if entry.get('cross_pollinated'):
            cross_pollinated_entries.append(entry)
            
    for entry in result.memories:
        if entry.get('cross_pollinated'):
            cross_pollinated_entries.append(entry)
    
    # Add special sections for cross-pollinated knowledge
    if cross_pollinated_entries:
        personal_sections.append("---")
        personal_sections.append("KNOWLEDGE RELATED TO YOUR INTERESTS:")
        
        for entry in cross_pollinated_entries:
            if entry.get('title'):
                personal_sections.append(f"{entry['title']}: {entry['description']}")
            else:
                personal_sections.append(f"{entry['description']}")
```

### 4. Update _get_graph_manager Method

```python
async def _get_graph_manager(self):
    """Get CharacterGraphManager instance (cached)"""
    if hasattr(self, '_graph_manager') and self._graph_manager:
        return self._graph_manager
        
    try:
        from src.characters.cdl.character_graph_manager import create_character_graph_manager
        
        # Find PostgreSQL pool
        if self.bot_core and hasattr(self.bot_core, 'postgres_pool'):
            postgres_pool = self.bot_core.postgres_pool
        elif self.knowledge_router:
            postgres_pool = getattr(self.knowledge_router, 'postgres_pool', None)
        else:
            postgres_pool = None
            
        if postgres_pool:
            # NEW: Pass semantic_router for cross-pollination
            self._graph_manager = create_character_graph_manager(
                postgres_pool, 
                semantic_router=self.semantic_router
            )
            return self._graph_manager
    except ImportError as e:
        logger.warning(f"CharacterGraphManager not available: {e}")
        
    return None
```

### 5. Update create_character_aware_prompt Method

```python
async def create_character_aware_prompt(self, character_name, user_id, message_content):
    # ... existing code ...
    
    # Get character data from CDL database
    character = await self._get_character(character_name)
    
    # Extract personality traits for system prompt enhancement
    personality_traits = self._extract_personality_traits(character)
    
    # Extract personal knowledge using graph intelligence and cross-pollination
    personal_knowledge = await self._extract_cdl_personal_knowledge_sections(
        character, 
        message_content,
        user_id=user_id  # NEW: Pass user_id for cross-pollination
    )
```

## Testing Plan

1. **Setup**: Ensure a test user with facts in PostgreSQL database
2. **Test Case 1**: Basic cross-pollination with user books and character reading interests
3. **Test Case 2**: Cross-pollination with user hobbies and character abilities
4. **Test Case 3**: Cross-pollination with user travel locations and character memories

## Discord Validation

Test in Discord with commands:
- "Elena, have you read any books I've mentioned?"
- "Jake, do you know anything about photography equipment I own?"
- "Marcus, have you heard of any AI companies I work with?"

## Expected Results

Character responses should include:
- Identification of shared interests ("You mentioned X, which I also...")
- Character knowledge related to user facts
- Weighted by importance/relevance
- Naturally integrated into conversation

---

**Next Steps**:
1. Implement constructor and method updates
2. Test with mock user facts
3. Integrate with real user facts via SemanticKnowledgeRouter
4. Validate in Discord with live testing