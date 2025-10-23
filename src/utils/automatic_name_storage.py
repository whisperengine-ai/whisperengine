"""
Automatic Name Detection and Storage System

⚠️ DEPRECATED: This module is no longer used.

Name storage now happens directly in MessageProcessor using Discord display names
from metadata. No regex patterns, no LLM calls - just direct Discord metadata.

See: src/core/message_processor.py -> _process_name_detection()

This file is kept for backward compatibility only.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class AutomaticNameStorage:
    """Handles automatic detection and storage of user names during conversations"""
    
    def __init__(self, memory_manager, llm_client=None):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        
    async def process_message_for_names(self, user_id: str, message: str) -> Optional[str]:
        """
        Process a user message for name information and store if found.
        
        Uses ONLY regex pattern matching - NO LLM calls.
        
        Args:
            user_id: The user's ID
            message: The user's message content
            
        Returns:
            The detected name if found, None otherwise
        """
        try:
            # Use pattern detection ONLY (fast, no LLM calls)
            detected_name = self._extract_name_from_text(message)
            
            # Store the name if detected
            if detected_name:
                await self._store_user_name(user_id, detected_name, message)
                logger.info("✅ Auto-detected and stored name '%s' for user %s", detected_name, user_id)
                return detected_name
                
        except (ValueError, RuntimeError, OSError) as e:
            logger.warning("Failed to process message for names: %s", e)
            
        return None
    
    def _extract_name_from_text(self, text: str) -> Optional[str]:
        """Extract name from text using pattern matching"""
        if not text:
            return None
            
        text_lower = text.lower().strip()
        
        # Look for explicit name introductions
        patterns = [
            r"my name is\s+([a-zA-Z][a-zA-Z\s\-']{1,20})",
            r"i'm\s+([a-zA-Z][a-zA-Z\s\-']{1,20})",
            r"i am\s+([a-zA-Z][a-zA-Z\s\-']{1,20})",
            r"call me\s+([a-zA-Z][a-zA-Z\s\-']{1,20})",
            r"please call me\s+([a-zA-Z][a-zA-Z\s\-']{1,20})",
            r"you can call me\s+([a-zA-Z][a-zA-Z\s\-']{1,20})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                potential_name = match.group(1).strip().title()
                if self._is_valid_name(potential_name):
                    return potential_name
                    
        return None
    
    async def _llm_extract_name(self, message: str) -> Optional[str]:
        """
        DEPRECATED: LLM-based name extraction disabled to avoid unnecessary LLM calls.
        Use regex pattern matching only (_extract_name_from_text).
        """
        logger.debug("LLM name extraction is deprecated - use pattern matching only")
        return None
    
    def _is_valid_name(self, name: str) -> bool:
        """Validate if a string looks like a valid name"""
        if not name or not isinstance(name, str):
            return False
            
        # Basic validation: 2-30 chars, mostly letters
        if not (2 <= len(name) <= 30):
            return False
            
        # Must be mostly alphabetic (allow for names like "Mary-Ann" or "O'Connor")
        alpha_chars = sum(1 for c in name if c.isalpha())
        if alpha_chars < len(name) * 0.7:  # At least 70% alphabetic
            return False
            
        # Avoid common non-name words
        non_names = {
            'and', 'the', 'but', 'you', 'not', 'yes', 'can', 'will', 'that', 'this',
            'here', 'there', 'when', 'where', 'what', 'how', 'why', 'who', 'which',
            'good', 'bad', 'nice', 'great', 'fine', 'okay', 'sure', 'maybe', 'perhaps'
        }
        if name.lower() in non_names:
            return False
            
        return True
    
    async def _store_user_name(self, user_id: str, name: str, context_message: str):
        """Store the detected name as a fact in vector memory"""
        try:
            # Store as a fact with high confidence
            if hasattr(self.memory_manager, 'store_fact'):
                await self.memory_manager.store_fact(
                    user_id=user_id,
                    fact=f"User's preferred name is {name}",
                    context=f"Detected from message: {context_message[:100]}...",
                    confidence=0.95,
                    metadata={
                        "preferred_name": name,
                        "detection_method": "automatic",
                        "source_message": context_message[:200]
                    }
                )
            else:
                # Fallback: store as regular conversation with special metadata
                await self.memory_manager.store_conversation(
                    user_id=user_id,
                    user_message=context_message,
                    bot_response=f"I'll remember that your name is {name}.",
                    metadata={
                        "preferred_name": name,
                        "memory_type": "name_fact",
                        "confidence": 0.95,
                        "detection_method": "automatic"
                    }
                )
                
        except (ValueError, RuntimeError, OSError, AttributeError) as e:
            logger.error("Failed to store user name: %s", e)


def create_automatic_name_storage(memory_manager, llm_client=None):
    """Factory function to create AutomaticNameStorage instance"""
    return AutomaticNameStorage(memory_manager, llm_client)