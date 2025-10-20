"""
Generic Keyword Template Manager

Provides database-driven keyword templates for LLM guidance instead of hardcoded lists.
Used by CDL integration for AI identity detection, physical interaction handling, etc.

ARCHITECTURE COMPLIANCE:
- No character-specific hardcoded logic
- Generic templates usable by any character
- Database-driven extensibility
- LLM guidance, not rigid rules
"""

import logging
import asyncpg
import os
from typing import Dict, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class GenericKeywordTemplateManager:
    """Manager for database-driven generic keyword templates."""
    
    def __init__(self):
        self._cache = {}
        self._cache_timestamp = 0
        
    async def get_keywords_for_category(self, category: str) -> List[str]:
        """
        Get keywords for a specific category from database.
            
        Returns:
            List of keywords for LLM guidance
        """
        # TODO: Accept connection pool as constructor parameter to avoid bypassing pool
        logger.debug("⚠️ GenericKeywordManager creating direct connection - should use pool")
        try:
            DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
            
            conn = await asyncpg.connect(DATABASE_URL)
            
            # Get all keywords for the category, ordered by priority
            results = await conn.fetch("""
                SELECT keywords
                FROM generic_keyword_templates
                WHERE category = $1 AND is_active = true
                ORDER BY priority_order
            """, category)
            
            await conn.close()
            
            # Flatten all keyword arrays into a single list
            all_keywords = []
            for row in results:
                all_keywords.extend(row['keywords'])
            
            logger.debug(f"📋 KEYWORDS: Loaded {len(all_keywords)} keywords for category '{category}'")
            return all_keywords
            
        except Exception as e:
            logger.warning(f"Could not load keywords for category '{category}': {e}")
            # Return fallback keywords for essential categories
            return self._get_fallback_keywords(category)
    
    def _get_fallback_keywords(self, category: str) -> List[str]:
        """Fallback keywords if database is unavailable."""
        fallbacks = {
            'ai_identity': ['ai', 'artificial intelligence', 'robot', 'computer', 'program', 'bot'],
            'physical_interaction': ['hug', 'kiss', 'touch', 'hold', 'cuddle', 'pet', 'pat', 'embrace'],
            'romantic_interaction': ['love', 'romance', 'date', 'relationship'],
            'emotional_support': ['sad', 'depressed', 'anxious', 'worried']
        }
        return fallbacks.get(category, [])
    
    async def check_message_for_category(self, message: str, category: str) -> bool:
        """
        Check if message contains keywords from a specific category.
        
        Args:
            message: User message to check
            category: Category to check against
            
        Returns:
            True if message contains keywords from the category
        """
        keywords = await self.get_keywords_by_category(category)
        message_lower = message.lower()
        
        return any(keyword in message_lower for keyword in keywords)
    
    async def get_all_categories(self) -> List[str]:
        """Get list of all available keyword categories."""
        # TODO: Accept connection pool as constructor parameter to avoid bypassing pool
        logger.debug("⚠️ GenericKeywordManager creating direct connection - should use pool")
        try:
            DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
            
            conn = await asyncpg.connect(DATABASE_URL)
            
            results = await conn.fetch("""
                SELECT DISTINCT category
                FROM generic_keyword_templates
                WHERE is_active = true
                ORDER BY category
            """)
            
            await conn.close()
            
            categories = [row['category'] for row in results]
            logger.debug(f"📋 CATEGORIES: Found {len(categories)} keyword categories")
            return categories
            
        except Exception as e:
            logger.warning(f"Could not load keyword categories: {e}")
            return ['ai_identity', 'physical_interaction', 'romantic_interaction', 'emotional_support']

# Global instance for easy access
_keyword_manager = None

def get_keyword_manager() -> GenericKeywordTemplateManager:
    """Get the global keyword template manager instance."""
    global _keyword_manager
    if _keyword_manager is None:
        _keyword_manager = GenericKeywordTemplateManager()
    return _keyword_manager