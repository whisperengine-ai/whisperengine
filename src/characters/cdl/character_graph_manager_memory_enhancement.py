"""
Memory Trigger Enhancement Implementation

This file contains the implementation for STEP 3: Memory Trigger Enhancement
which enables character memories to be activated from user fact entities,
not just message keywords.
"""

import logging
from typing import Dict, List, Optional, Any
import asyncpg

logger = logging.getLogger(__name__)

class MemoryTriggerEnhancer:
    """
    Enhances character memories by activating them from user fact entities.
    
    This class implements the STEP 3: Memory Trigger Enhancement feature:
    - User mentions diving hobby → Elena's diving memories auto-surface
    - User mentions photography → Jake's photo expedition memories activate
    - User discusses stress → Character's stress-related memories surface
    """
    
    def __init__(self, postgres_pool, semantic_router=None):
        """
        Initialize the memory trigger enhancer.
        
        Args:
            postgres_pool: PostgreSQL connection pool
            semantic_router: Optional SemanticKnowledgeRouter for user facts
        """
        self.postgres = postgres_pool
        self.semantic_router = semantic_router
        
    async def query_memories_with_user_facts(
        self,
        character_id: int,
        message_triggers: List[str],
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query character memories with trigger-based activation from:
        1. Direct message keywords (current functionality)
        2. User fact entities (NEW - "user mentioned diving")
        
        Args:
            character_id: Character ID
            message_triggers: Trigger keywords from the message
            user_id: Optional user ID for user fact enhancement
            limit: Maximum number of memories to return
            
        Returns:
            List of triggered memories
        """
        # If no semantic router or user_id, fall back to standard triggering
        if not self.semantic_router or not user_id:
            return await self._query_memories_with_message_triggers(
                character_id=character_id,
                triggers=message_triggers,
                limit=limit
            )
        
        try:
            # 1. Get user facts to extract additional triggers
            from src.knowledge.semantic_router import QueryIntent, IntentAnalysisResult
            
            # Create a general intent for fetching user facts
            intent = IntentAnalysisResult(
                intent_type=QueryIntent.FACTUAL_RECALL,
                entity_type="general",  # Get all types
                relationship_type=None,  # Get all relationships
                confidence=1.0,
                keywords=[]
            )
            
            user_facts = await self.semantic_router.get_user_facts(
                user_id=user_id,
                intent=intent,
                limit=10  # Get enough facts to extract relevant triggers
            )
            
            # 2. Extract entity names as additional triggers
            user_triggers = []
            for fact in user_facts:
                # Extract entity name as trigger
                entity_name = fact.get('entity_name', '').lower()
                if entity_name and len(entity_name) > 2:  # Skip very short names
                    user_triggers.append(entity_name)
                
                # Also extract any category as trigger
                category = fact.get('category', '').lower()
                if category and len(category) > 3 and category != 'general':
                    user_triggers.append(category)
            
            # 3. Combine message triggers with user fact triggers
            combined_triggers = list(set(message_triggers + user_triggers))
            
            # Log the enhancement
            if user_triggers:
                logger.info("🧠 Enhanced memory triggers with user facts: %s", user_triggers)
            
            # 4. Query memories with combined triggers
            return await self._query_memories_with_message_triggers(
                character_id=character_id,
                triggers=combined_triggers,
                limit=limit
            )
            
        except Exception as e:
            logger.error("❌ Error in memory trigger enhancement: %s", e)
            # Fall back to standard message-only triggering
            return await self._query_memories_with_message_triggers(
                character_id=character_id,
                triggers=message_triggers,
                limit=limit
            )
    
    async def _query_memories_with_message_triggers(
        self,
        character_id: int,
        triggers: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Query memories with message triggers only.
        
        This is the core implementation that's used by both
        standard triggering and enhanced triggering.
        
        Args:
            character_id: Character ID
            triggers: List of trigger keywords
            limit: Maximum number of memories to return
            
        Returns:
            List of triggered memories
        """
        if not triggers:
            return []
            
        async with self.postgres.acquire() as conn:
            query = """
                SELECT 
                    memory_type,
                    title,
                    description,
                    emotional_impact,
                    time_period,
                    importance_level,
                    triggers,
                    created_date
                FROM character_memories
                WHERE character_id = $1
                  AND triggers && $2::TEXT[]
                ORDER BY importance_level DESC, emotional_impact DESC
                LIMIT $3
            """
            
            rows = await conn.fetch(query, character_id, triggers, limit)
            
            results = []
            for row in rows:
                results.append({
                    'memory_type': row['memory_type'],
                    'title': row['title'],
                    'description': row['description'],
                    'emotional_impact': row['emotional_impact'],
                    'time_period': row['time_period'],
                    'importance_level': row['importance_level'],
                    'triggers': row['triggers'],
                    'created_date': row['created_date']
                })
            
            return results