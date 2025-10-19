"""
High-quality conversation summarization for background enrichment

Uses sophisticated LLM prompts and multi-step reasoning since we're NOT
in the hot path and can take our time for better quality.
"""

import asyncio
import logging
import json
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SummarizationEngine:
    """
    Advanced summarization engine for async enrichment
    
    Key differences from real-time summarization:
    - Higher quality models (Claude 3.5 Sonnet, GPT-4 Turbo)
    - Multi-step reasoning (extract -> analyze -> synthesize)
    - More comprehensive context analysis
    - No time pressure - can use 1000+ token responses
    """
    
    def __init__(self, llm_client, llm_model: str):
        self.llm_client = llm_client
        self.llm_model = llm_model
        logger.info(f"Initialized SummarizationEngine with model: {llm_model}")
    
    async def generate_conversation_summary(
        self,
        messages: List[Dict],
        user_id: str,
        bot_name: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive conversation summary
        
        Args:
            messages: List of message dicts with content, timestamp, memory_type
            user_id: User ID for context
            bot_name: Bot name for context
        
        Returns:
            {
                'summary_text': str,
                'key_topics': List[str],
                'emotional_tone': str,
                'compression_ratio': float,
                'confidence_score': float
            }
        """
        logger.debug(f"Generating summary for {user_id} with {len(messages)} messages...")
        
        # Build conversation context
        conversation_text = self._format_messages_for_llm(messages, bot_name)
        
        # Generate summary with high-quality LLM
        summary_text = await self._generate_summary_text(conversation_text, len(messages), bot_name)
        
        # Extract key topics
        key_topics = await self._extract_key_topics(conversation_text)
        
        # Analyze emotional tone
        emotional_tone = self._analyze_emotional_tone(messages)
        
        # Calculate compression ratio
        original_length = sum(len(m.get('content', '')) for m in messages)
        compression_ratio = len(summary_text) / original_length if original_length > 0 else 0
        
        # Confidence score (simple heuristic - could be enhanced)
        confidence_score = self._calculate_confidence(messages)
        
        logger.info(f"Generated summary: {len(summary_text)} chars, {len(key_topics)} topics, {emotional_tone} tone")
        
        return {
            'summary_text': summary_text,
            'key_topics': key_topics,
            'emotional_tone': emotional_tone,
            'compression_ratio': compression_ratio,
            'confidence_score': confidence_score
        }
    
    async def _generate_summary_text(
        self,
        conversation_text: str,
        message_count: int,
        bot_name: str
    ) -> str:
        """Generate natural language summary using LLM"""
        summary_prompt = f"""You are an expert conversation analyst. Summarize this conversation between a user and {bot_name} (an AI character).

Focus on:
1. Key topics discussed
2. Important information shared
3. Emotional tone and evolution
4. Decisions made or plans discussed
5. Any personal details or preferences mentioned

Conversation ({message_count} messages):
{conversation_text}

Provide a comprehensive 3-5 sentence summary that captures the essence of this conversation. Be specific and preserve important details."""

        try:
            # Use get_chat_response for modern chat API (asyncio.to_thread for sync method)
            response = await asyncio.to_thread(
                self.llm_client.get_chat_response,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert conversation analyst. Provide clear, detailed summaries."
                    },
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                model=self.llm_model,
                temperature=0.5,
                max_tokens=500
            )
            
            # get_chat_response returns a string directly
            summary_text = response.strip() if response else ''
            
            if not summary_text:
                logger.warning("LLM returned empty summary, using fallback")
                return self._generate_fallback_summary(message_count, bot_name)
            
            return summary_text
            
        except Exception as e:
            logger.error(f"Error generating summary with LLM: {e}")
            return self._generate_fallback_summary(message_count, bot_name)
    
    async def _extract_key_topics(self, conversation_text: str) -> List[str]:
        """Extract 3-5 key topics from conversation"""
        topics_prompt = f"""Extract the 3-5 main topics from this conversation. Return only a JSON array of topic strings.

Conversation:
{conversation_text[:2000]}

Topics (JSON array):"""

        try:
            # Use get_chat_response for modern chat API
            response_text = await asyncio.to_thread(
                self.llm_client.get_chat_response,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a topic extraction specialist. Return ONLY valid JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": topics_prompt
                    }
                ],
                model=self.llm_model,
                temperature=0.3,
                max_tokens=100
            )
            
            # get_chat_response returns string directly - parse JSON
            # Handle markdown code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            # Try to parse as JSON
            topics = json.loads(response_text)
            if isinstance(topics, list):
                return [str(t).strip() for t in topics[:5]]
            
            # Fallback: split by commas
            return [t.strip() for t in response_text.split(',')[:5]]
            
        except Exception as e:
            logger.debug(f"Topic extraction failed: {e}, using fallback")
            return ["general conversation"]
    
    def _analyze_emotional_tone(self, messages: List[Dict]) -> str:
        """Analyze overall emotional tone of conversation"""
        # Use existing emotion labels if available
        emotions = [m.get('emotion_label', 'neutral') for m in messages]
        
        if not emotions:
            return 'neutral'
        
        # Simple majority vote
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        
        # Map to simple categories
        if dominant_emotion in ['joy', 'excitement', 'love', 'happiness']:
            return 'positive'
        elif dominant_emotion in ['sadness', 'anger', 'fear', 'disgust']:
            return 'negative'
        elif dominant_emotion in ['neutral', 'curiosity']:
            return 'neutral'
        else:
            return 'mixed'
    
    def _calculate_confidence(self, messages: List[Dict]) -> float:
        """Calculate confidence score based on message characteristics"""
        # More messages = higher confidence
        if len(messages) >= 20:
            return 0.9
        elif len(messages) >= 10:
            return 0.8
        elif len(messages) >= 5:
            return 0.6
        else:
            return 0.4
    
    def _format_messages_for_llm(self, messages: List[Dict], bot_name: str) -> str:
        """Format messages for LLM context"""
        formatted = []
        
        for msg in messages:
            # CRITICAL FIX: Use 'role' field (user/bot) not 'memory_type' (conversation/fact/etc)
            msg_role = msg.get('role', '')
            
            # Determine display name
            if msg_role == 'user':
                role = "User"
            elif msg_role in ('bot', 'assistant'):
                role = bot_name
            # FALLBACK: Old memory_type field for backward compatibility
            elif msg.get('memory_type') == 'user_message':
                role = "User"
            elif msg.get('memory_type') == 'bot_response':
                role = bot_name
            else:
                role = bot_name  # Default to bot if unclear
            
            content = msg.get('content', '')[:2000]  # Discord limit: 2000 chars - preserve full fidelity
            timestamp = msg.get('timestamp', '')
            
            # Format timestamp if it's a datetime object
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M')
            
            formatted.append(f"[{timestamp}] {role}: {content}")
        
        return "\n\n".join(formatted)
    
    def _generate_fallback_summary(self, message_count: int, bot_name: str) -> str:
        """Generate simple fallback summary when LLM fails"""
        return f"Conversation with {message_count} messages between user and {bot_name}. Topics and details discussed."
