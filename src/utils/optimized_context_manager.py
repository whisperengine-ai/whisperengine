"""
Optimized context generation for streamlined prompt engineering.

This module creates concise, high-value context summaries instead of
dumping raw data into prompts, dramatically reducing token usage while
maintaining conversational quality.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class OptimizedContextManager:
    """Generates efficient, summarized context for LLM prompts."""
    
    def __init__(self):
        self.max_core_context_tokens = 200
        self.max_recent_context_tokens = 150
        self.max_total_context_tokens = 400
    
    def generate_core_context(
        self, 
        user_id: str,
        relevant_memories: List[Dict],
        relationship_data: Optional[Dict] = None,
        emotion_data: Optional[Dict] = None
    ) -> str:
        """
        Generate concise core context about the user and relationship.
        
        Args:
            user_id: User identifier
            relevant_memories: List of memory objects
            relationship_data: Optional relationship information
            emotion_data: Optional current emotional context
            
        Returns:
            Compressed context string under token limit
        """
        context_parts = []
        
        # Relationship summary (1-2 lines max)
        if relationship_data:
            depth = relationship_data.get('depth', 'new')
            conversations = relationship_data.get('conversation_count', 0)
            
            if depth == 'established' and conversations > 20:
                context_parts.append("You have a well-established friendship with ongoing shared experiences.")
            elif depth == 'growing' and conversations > 5:
                context_parts.append("You're building a good connection through regular conversations.")
            elif conversations > 0:
                context_parts.append("You're getting to know each other through recent conversations.")
        
        # Key memories (top 3-5 most relevant only)
        if relevant_memories:
            memory_insights = []
            
            # Sort by relevance/importance and take top 3
            sorted_memories = sorted(
                relevant_memories, 
                key=lambda m: m.get('score', 0.5), 
                reverse=True
            )[:3]
            
            for memory in sorted_memories:
                metadata = memory.get('metadata', {})
                
                # Extract the most important insight from each memory
                if metadata.get('type') == 'user_fact':
                    fact = metadata.get('fact', '')
                    if fact and len(fact) < 100:
                        memory_insights.append(fact)
                elif metadata.get('user_message'):
                    msg = metadata.get('user_message', '')
                    if msg and len(msg) < 80:
                        memory_insights.append(f"They mentioned: {msg}")
            
            if memory_insights:
                context_parts.append("Key things you remember: " + "; ".join(memory_insights[:3]))
        
        # Current emotional context (1 line max)
        if emotion_data:
            primary_emotion = emotion_data.get('primary_emotion')
            if primary_emotion and primary_emotion != 'neutral':
                context_parts.append(f"They seem {primary_emotion} right now.")
        
        # Combine and limit length
        full_context = " ".join(context_parts)
        
        # Truncate if too long (rough token limit)
        if len(full_context) > self.max_core_context_tokens * 4:  # ~4 chars per token
            full_context = full_context[:self.max_core_context_tokens * 4] + "..."
        
        return full_context if full_context else "This is a new conversation."
    
    def generate_recent_context(self, recent_messages: List[Any]) -> str:
        """
        Generate concise summary of recent conversation flow.
        
        Args:
            recent_messages: List of recent message objects
            
        Returns:
            Brief conversation summary under token limit
        """
        if not recent_messages or len(recent_messages) < 2:
            return "Starting a new conversation."
        
        # Get last few exchanges (not individual messages)
        try:
            # Simple approach: summarize the topic/flow
            last_user_msg = None
            last_bot_msg = None
            
            # Find the most recent user and bot messages
            for msg in reversed(recent_messages):
                content = getattr(msg, 'content', '') or str(msg.get('content', ''))
                is_bot = getattr(msg, 'author', {}).get('bot', False) or msg.get('is_bot', False)
                
                if not is_bot and not last_user_msg and content:
                    last_user_msg = content[:100]  # Limit length
                elif is_bot and not last_bot_msg and content:
                    last_bot_msg = content[:100]
                
                if last_user_msg and last_bot_msg:
                    break
            
            if last_user_msg:
                summary = f"You were just discussing: {last_user_msg[:60]}..."
                return summary
            else:
                return "Continuing your conversation."
                
        except Exception as e:
            logger.warning(f"Error generating recent context: {e}")
            return "Continuing your conversation."
    
    def optimize_conversation_context(
        self,
        user_id: str,
        relevant_memories: List[Dict],
        recent_messages: List[Any],
        relationship_data: Optional[Dict] = None,
        emotion_data: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate all optimized context variables for prompt template.
        
        Returns:
            Dictionary with context variables for template substitution
        """
        core_context = self.generate_core_context(
            user_id, relevant_memories, relationship_data, emotion_data
        )
        
        recent_context = self.generate_recent_context(recent_messages)
        
        logger.debug(
            "Generated optimized context: core=%d chars, recent=%d chars",
            len(core_context), len(recent_context)
        )
        
        return {
            'CORE_CONTEXT': core_context,
            'RECENT_CONTEXT': recent_context
        }

def estimate_context_tokens(context_dict: Dict[str, str]) -> int:
    """Estimate total tokens in context dictionary."""
    total_chars = sum(len(str(value)) for value in context_dict.values())
    return total_chars // 4  # Rough estimation: 4 chars per token