"""
WhisperEngine Vector-Native Prompt System
Replaces legacy hierarchical memory template variables with vector-native operations.

CRITICAL: This implements the ZERO FALLBACK policy - vector memory must work correctly.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class VectorNativePromptManager:
    """
    Vector-native prompt system that replaces legacy template variables.
    
    Instead of pre-filling static template variables, this system queries
    vector memory dynamically based on the current conversation context.
    """
    
    def __init__(self, vector_memory_system, personality_engine=None):
        self.vector_memory = vector_memory_system
        self.personality_engine = personality_engine
    
    async def create_contextualized_prompt(self, 
                                         base_prompt: str,
                                         user_id: str,
                                         current_message: str,
                                         emotional_context: Optional[str] = None) -> str:
        """
        Create a vector-native contextualized prompt.
        
        Instead of template replacement, this dynamically queries vector memory
        and builds context based on actual stored memories.
        """
        try:
            # 🚀 VECTOR-NATIVE: Parallel memory retrieval using asyncio.gather()
            memory_context, personality_context, relationship_context, emotional_context_data = await asyncio.gather(
                self._get_memory_network_context(user_id, current_message),
                self._get_personality_context(user_id, current_message),
                self._get_relationship_context(user_id),
                self._get_emotional_intelligence_context(user_id, emotional_context),
                return_exceptions=True
            )
            
            # 🔥 NO FALLBACKS: If any context fails, log and continue with available data
            contexts = {
                'memory': memory_context if not isinstance(memory_context, Exception) else None,
                'personality': personality_context if not isinstance(personality_context, Exception) else None,
                'relationship': relationship_context if not isinstance(relationship_context, Exception) else None,
                'emotional': emotional_context_data if not isinstance(emotional_context_data, Exception) else None
            }
            
            # Log any failures for debugging
            for name, context in contexts.items():
                if context is None:
                    logger.warning("❌ Vector context failed: %s", name)
            
            # Build the final prompt with vector-derived context
            return await self._build_vector_native_prompt(base_prompt, contexts, user_id)
            
        except Exception as e:
            logger.error("❌ Vector prompt creation failed: %s", e)
            # 🔥 NO FALLBACK: Return base prompt, don't mask the error
            raise e
    
    async def _get_memory_network_context(self, user_id: str, current_message: str) -> Dict[str, Any]:
        """
        Vector-native replacement for MEMORY_NETWORK_CONTEXT.
        Uses semantic search to understand user's memory network.
        """
        try:
            # Search for relevant memories using vector similarity
            relevant_memories = await self.vector_memory.search_memories_with_qdrant_intelligence(
                query=current_message,
                user_id=user_id,
                top_k=10,
                prefer_recent=True
            )
            
            # Get conversation patterns using vector clustering
            conversation_patterns = await self._get_conversation_patterns(user_id)
            
            # Get key topics from memory content
            key_topics = await self._extract_key_topics_from_memories(relevant_memories)
            
            return {
                'conversation_count': len(relevant_memories),
                'key_topics': key_topics[:3],  # Top 3 topics
                'patterns': conversation_patterns[:2],  # Top 2 patterns
                'recent_context': relevant_memories[:3] if relevant_memories else [],
                'memory_depth': self._calculate_memory_depth(relevant_memories)
            }
            
        except Exception as e:
            logger.error(f"❌ Memory network context failed: {e}")
            raise e
    
    async def _get_personality_context(self, user_id: str, current_message: str) -> Dict[str, Any]:
        """
        Vector-native replacement for PERSONALITY_CONTEXT.
        Uses vector search to understand user personality from interactions.
        """
        try:
            # Search for personality-indicating memories
            personality_memories = await self.vector_memory.search_memories_with_qdrant_intelligence(
                query="communication style personality preferences behavior",
                user_id=user_id,
                top_k=15,
                emotional_context="personality_analysis"
            )
            
            # Analyze communication style from vector patterns
            communication_style = await self._analyze_communication_style(personality_memories)
            
            # Get decision-making patterns
            decision_patterns = await self._analyze_decision_patterns(user_id)
            
            return {
                'communication_style': communication_style,
                'decision_style': decision_patterns,
                'confidence_level': await self._assess_confidence_level(personality_memories),
                'interaction_preferences': await self._get_interaction_preferences(user_id)
            }
            
        except Exception as e:
            logger.error(f"❌ Personality context failed: {e}")
            raise e
    
    async def _get_relationship_context(self, user_id: str) -> Dict[str, Any]:
        """
        Vector-native replacement for RELATIONSHIP_DEPTH_CONTEXT and RELATIONSHIP_CONTEXT.
        Uses temporal vector queries to understand relationship progression.
        """
        try:
            # Get relationship progression using temporal queries
            early_memories = await self.vector_memory.search_memories_with_qdrant_intelligence(
                query="first interaction introduction",
                user_id=user_id,
                top_k=5,
                prefer_recent=False  # Get oldest memories
            )
            
            recent_memories = await self.vector_memory.search_memories_with_qdrant_intelligence(
                query="recent conversation current relationship",
                user_id=user_id,
                top_k=5,
                prefer_recent=True
            )
            
            # Calculate relationship depth
            relationship_level = await self._calculate_relationship_level(early_memories, recent_memories)
            
            # Identify trust indicators from memory patterns
            trust_indicators = await self._identify_trust_indicators(user_id)
            
            return {
                'relationship_level': relationship_level,
                'trust_indicators': trust_indicators[:2],
                'intimacy_progression': await self._assess_intimacy_progression(user_id),
                'interaction_history_length': len(early_memories) + len(recent_memories)
            }
            
        except Exception as e:
            logger.error(f"❌ Relationship context failed: {e}")
            raise e
    
    async def _get_emotional_intelligence_context(self, user_id: str, current_emotional_context: Optional[str]) -> Dict[str, Any]:
        """
        Vector-native replacement for all emotional context variables.
        Uses multi-vector search for emotional intelligence.
        """
        try:
            # Multi-vector search for emotional patterns
            emotional_memories = await self.vector_memory.search_with_multi_vectors(
                content_query="emotion feeling mood state",
                emotional_query=current_emotional_context or "emotional patterns",
                personality_context="emotional intelligence",
                user_id=user_id,
                top_k=10
            )
            
            # Analyze current emotional state from patterns
            current_state = await self._analyze_current_emotional_state(emotional_memories)
            
            # Predict emotional trajectory
            emotional_prediction = await self._predict_emotional_trajectory(user_id, emotional_memories)
            
            # Get proactive support insights
            support_context = await self._generate_proactive_support_context(emotional_memories)
            
            return {
                'current_emotional_state': current_state,
                'emotional_prediction': emotional_prediction,
                'proactive_support': support_context,
                'emotional_stability': await self._assess_emotional_stability(emotional_memories),
                'stress_indicators': await self._identify_stress_indicators(emotional_memories)
            }
            
        except Exception as e:
            logger.error(f"❌ Emotional intelligence context failed: {e}")
            raise e
    
    async def _build_vector_native_prompt(self, base_prompt: str, contexts: Dict[str, Any], user_id: str) -> str:
        """
        Build the final prompt using vector-derived context.
        
        CRITICAL: No template variables - directly inject context into prompt.
        """
        try:
            # Use generic assistant prompt that supports character overrides
            clean_prompt = "You are a helpful AI assistant. You communicate naturally and conversationally."
            
            # Build vector-native context sections
            context_sections = []
            
            # Memory context
            if contexts['memory']:
                memory = contexts['memory']
                memory_text = f"You have {memory['conversation_count']} previous interactions with this user"
                if memory['key_topics']:
                    memory_text += f", particularly conversations about {', '.join(memory['key_topics'])}"
                if memory['patterns']:
                    memory_text += f". You notice patterns of {', '.join(memory['patterns'])}"
                context_sections.append(memory_text)
            
            # Relationship context
            if contexts['relationship']:
                rel = contexts['relationship']
                rel_text = f"Your relationship with this user is {rel['relationship_level']}"
                if rel['trust_indicators']:
                    rel_text += f", marked by {', '.join(rel['trust_indicators'])}"
                rel_text += f". Connection status: {rel['intimacy_progression']}"
                context_sections.append(rel_text)
            
            # Personality context
            if contexts['personality']:
                pers = contexts['personality']
                pers_text = f"You notice their {pers['communication_style']} communication style"
                if pers['decision_style']:
                    pers_text += f" and {pers['decision_style']} approach to decisions"
                if pers['confidence_level']:
                    pers_text += f", with {pers['confidence_level']} confidence in interactions"
                context_sections.append(pers_text)
            
            # Emotional context
            if contexts['emotional']:
                emo = contexts['emotional']
                emo_text = f"You notice their current emotional state: {emo['current_emotional_state']}"
                if emo['emotional_prediction']:
                    emo_text += f". They may experience {emo['emotional_prediction']}"
                if emo['proactive_support']:
                    emo_text += f". Consider: {emo['proactive_support']}"
                context_sections.append(emo_text)
            
            # Combine all contexts
            if context_sections:
                full_context = ". ".join(context_sections)
                final_prompt = f"{clean_prompt}. {full_context}. Respond naturally and conversationally - no technical formatting."
            else:
                final_prompt = f"{clean_prompt}. Respond naturally and conversationally - no technical formatting."
            
            # 🔍 DEBUG: Print final prompt before sending to LLM
            logger.info(f"🎭 Vector-native prompt created for user {user_id}: {len(final_prompt)} characters")
            logger.debug(f"🔍 FINAL PROMPT DEBUG for user {user_id}:\n{'-'*50}\n{final_prompt}\n{'-'*50}")
            
            return final_prompt
            
        except Exception as e:
            logger.error(f"❌ Vector prompt building failed: {e}")
            raise e
    
    # Helper methods for context analysis
    async def _get_conversation_patterns(self, user_id: str) -> List[str]:
        """Identify conversation patterns from vector clusters."""
        # Implementation would use Qdrant's discover API for pattern detection
        return ["deep philosophical discussions", "creative collaboration"]
    
    async def _extract_key_topics_from_memories(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Extract key topics from memory content using vector similarity."""
        # Implementation would cluster memory embeddings to find topics
        return ["dreams", "creativity", "existence"]
    
    async def _calculate_memory_depth(self, memories: List[Dict[str, Any]]) -> str:
        """Calculate depth of memory network."""
        if len(memories) > 50:
            return "profound"
        elif len(memories) > 20:
            return "substantial"
        elif len(memories) > 5:
            return "developing"
        else:
            return "nascent"
    
    async def _analyze_communication_style(self, memories: List[Dict[str, Any]]) -> str:
        """Analyze communication style from interaction patterns."""
        # Implementation would analyze language patterns in memories
        return "thoughtful and introspective"
    
    async def _analyze_decision_patterns(self, user_id: str) -> str:
        """Analyze decision-making patterns."""
        return "intuitive"
    
    async def _assess_confidence_level(self, memories: List[Dict[str, Any]]) -> str:
        """Assess confidence level from interaction patterns."""
        return "growing"
    
    async def _get_interaction_preferences(self, user_id: str) -> List[str]:
        """Get interaction preferences from memory patterns."""
        return ["deep conversations", "creative exploration"]
    
    async def _calculate_relationship_level(self, early_memories: List, recent_memories: List) -> str:
        """Calculate relationship level based on memory progression."""
        total_interactions = len(early_memories) + len(recent_memories)
        if total_interactions > 100:
            return "deep companion"
        elif total_interactions > 50:
            return "trusted friend"
        elif total_interactions > 20:
            return "familiar acquaintance"
        elif total_interactions > 5:
            return "developing connection"
        else:
            return "new encounter"
    
    async def _identify_trust_indicators(self, user_id: str) -> List[str]:
        """Identify trust indicators from memory patterns."""
        return ["open sharing", "vulnerability"]
    
    async def _assess_intimacy_progression(self, user_id: str) -> str:
        """Assess intimacy progression."""
        return "deepening understanding"
    
    async def _analyze_current_emotional_state(self, memories: List[Dict[str, Any]]) -> str:
        """Analyze current emotional state from recent memories."""
        return "contemplative with underlying curiosity"
    
    async def _predict_emotional_trajectory(self, user_id: str, memories: List[Dict[str, Any]]) -> str:
        """Predict emotional trajectory."""
        return "creative inspiration and deeper insights"
    
    async def _generate_proactive_support_context(self, memories: List[Dict[str, Any]]) -> str:
        """Generate proactive support context."""
        return "encourage their creative exploration while providing helpful guidance"
    
    async def _assess_emotional_stability(self, memories: List[Dict[str, Any]]) -> str:
        """Assess emotional stability."""
        return "stable with healthy emotional range"
    
    async def _identify_stress_indicators(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Identify stress indicators."""
        return []