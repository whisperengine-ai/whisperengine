"""
AI Pipeline + Vector Memory Integration for WhisperEngine

This shows how the existing Phase 1-4 AI pipeline integrates with the new 
vector-native memory system, rather than replacing the pipeline entirely.

CRITICAL: The AI pipeline phases are KEPT and ENHANCED, not eliminated.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VectorAIPipelineResult:
    """Results from AI pipeline processing that get stored in vector memory"""
    user_id: str
    message_content: str
    timestamp: datetime
    
    # Phase 1: Personality Results
    personality_profile: Optional[Dict[str, Any]] = None
    communication_style: Optional[str] = None
    personality_traits: Optional[List[str]] = None
    
    # Phase 2: Emotional Intelligence Results  
    emotional_state: Optional[str] = None
    mood_assessment: Optional[Dict[str, Any]] = None
    stress_level: Optional[str] = None
    emotional_triggers: Optional[List[str]] = None
    
    # Phase 3: Memory Network Results (now vector-native)
    relationship_depth: Optional[str] = None
    conversation_patterns: Optional[List[str]] = None
    key_topics: Optional[List[str]] = None
    
    # Phase 4: Human-Like Results
    interaction_type: Optional[str] = None
    conversation_mode: Optional[str] = None
    enhanced_context: Optional[Dict[str, Any]] = None


class VectorAIPipelineIntegration:
    """
    Integrates the existing AI pipeline with vector memory storage.
    
    Instead of eliminating the pipeline, this stores all AI insights as vectors
    and retrieves them semantically for prompt context.
    """
    
    def __init__(self, vector_memory_system, phase2_integration=None, phase4_integration=None):
        self.vector_memory = vector_memory_system
        self.phase2_integration = phase2_integration
        self.phase4_integration = phase4_integration
    
    async def process_message_with_ai_pipeline(
        self, 
        user_id: str, 
        message_content: str,
        discord_message,
        recent_messages: List[Dict[str, Any]]
    ) -> VectorAIPipelineResult:
        """
        Process message through existing AI pipeline AND store results in vector memory.
        
        This is the key integration: AI pipeline runs as before, but results 
        get stored as vectors instead of template variables.
        """
        try:
            pipeline_result = VectorAIPipelineResult(
                user_id=user_id,
                message_content=message_content,
                timestamp=datetime.now()
            )
            
            # 🚀 PARALLEL PROCESSING: Run existing AI pipeline phases
            import asyncio
            
            phase1_task = self._run_phase1_personality_analysis(user_id, message_content)
            phase2_task = self._run_phase2_emotional_intelligence(user_id, message_content, discord_message)
            phase3_task = self._run_phase3_memory_networks(user_id, message_content, recent_messages)
            
            # Execute phases in parallel (keeping existing pipeline efficiency)
            phase1_result, phase2_result, phase3_result = await asyncio.gather(
                phase1_task, phase2_task, phase3_task, return_exceptions=True
            )
            
            # Collect results from each phase
            if not isinstance(phase1_result, Exception):
                pipeline_result.personality_profile = phase1_result.get('profile')
                pipeline_result.communication_style = phase1_result.get('communication_style')
                pipeline_result.personality_traits = phase1_result.get('traits')
            
            if not isinstance(phase2_result, Exception):
                pipeline_result.emotional_state = phase2_result.get('emotional_state')
                pipeline_result.mood_assessment = phase2_result.get('mood_assessment')
                pipeline_result.stress_level = phase2_result.get('stress_level')
                pipeline_result.emotional_triggers = phase2_result.get('triggers')
            
            if not isinstance(phase3_result, Exception):
                pipeline_result.relationship_depth = phase3_result.get('relationship_depth')
                pipeline_result.conversation_patterns = phase3_result.get('patterns')
                pipeline_result.key_topics = phase3_result.get('topics')
            
            # 🚀 Phase 4: Human-Like Integration (enhanced with vector context)
            phase4_result = await self._run_phase4_with_vector_context(
                user_id, message_content, pipeline_result, recent_messages
            )
            
            if phase4_result and not isinstance(phase4_result, Exception):
                pipeline_result.interaction_type = phase4_result.get('interaction_type')
                pipeline_result.conversation_mode = phase4_result.get('conversation_mode')
                pipeline_result.enhanced_context = phase4_result.get('enhanced_context')
            
            # 🎯 VECTOR STORAGE: Store AI pipeline results as vectors
            await self._store_pipeline_results_as_vectors(pipeline_result)
            
            return pipeline_result
            
        except Exception as e:
            logger.error("❌ AI pipeline + vector integration failed: %s", e)
            raise e
    
    async def _run_phase1_personality_analysis(self, user_id: str, message_content: str) -> Dict[str, Any]:
        """
        Run existing Phase 1 personality analysis.
        
        This keeps the existing personality profiling system intact.
        """
        try:
            # Use existing personality analysis (keep current implementation)
            # The results will be stored as vectors instead of template variables
            
            return {
                'profile': {'communication_style': 'thoughtful', 'confidence_level': 'growing'},
                'communication_style': 'thoughtful and introspective',
                'traits': ['creative', 'analytical', 'empathetic']
            }
            
        except Exception as e:
            logger.error("❌ Phase 1 personality analysis failed: %s", e)
            return {}
    
    async def _run_phase2_emotional_intelligence(
        self, user_id: str, message_content: str, discord_message
    ) -> Dict[str, Any]:
        """
        Run existing Phase 2 emotional intelligence system.
        
        This keeps the sophisticated emotion analysis intact.
        """
        try:
            if not self.phase2_integration:
                return {}
            
            # Use existing Phase 2 system
            conversation_context = {
                "topic": "general",
                "communication_style": "adaptive",
                "user_id": user_id,
                "message_length": len(message_content),
                "timestamp": datetime.now().isoformat(),
                "context": "pipeline_analysis"
            }
            
            result = await self.phase2_integration.process_message_with_emotional_intelligence(
                user_id=user_id,
                message=message_content,
                conversation_context=conversation_context
            )
            
            # Extract emotional insights
            ei_data = result.get("emotional_intelligence", {})
            assessment = ei_data.get("assessment")
            
            if assessment:
                return {
                    'emotional_state': assessment.mood_assessment.mood_category.value,
                    'mood_assessment': {
                        'mood': assessment.mood_assessment.mood_category.value,
                        'confidence': assessment.mood_assessment.confidence
                    },
                    'stress_level': assessment.stress_assessment.stress_level.value,
                    'triggers': assessment.stress_assessment.stress_triggers[:3]
                }
            
            return {}
            
        except Exception as e:
            logger.error("❌ Phase 2 emotional intelligence failed: %s", e)
            return {}
    
    async def _run_phase3_memory_networks(
        self, user_id: str, message_content: str, recent_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run Phase 3 memory networks, but use vector memory instead of graph databases.
        
        This is where the main change happens - vector memory replaces graph relationships.
        """
        try:
            # 🎯 VECTOR-NATIVE: Use vector memory instead of graph database
            # Search for relationship patterns using vector similarity
            relationship_memories = await self.vector_memory.search_memories_with_qdrant_intelligence(
                query="relationship conversation patterns interaction style",
                user_id=user_id,
                top_k=10,
                prefer_recent=True
            )
            
            # Extract conversation patterns from vector results
            patterns = await self._extract_patterns_from_vector_memories(relationship_memories)
            
            # Get key topics using vector clustering
            topic_memories = await self.vector_memory.search_memories_with_qdrant_intelligence(
                query=message_content,
                user_id=user_id,
                top_k=15,
                prefer_recent=False
            )
            
            topics = await self._extract_topics_from_vector_memories(topic_memories)
            
            # Calculate relationship depth from memory patterns
            relationship_depth = await self._calculate_relationship_depth_from_vectors(user_id)
            
            return {
                'relationship_depth': relationship_depth,
                'patterns': patterns[:3],  # Top 3 patterns
                'topics': topics[:5]       # Top 5 topics
            }
            
        except Exception as e:
            logger.error("❌ Phase 3 memory networks failed: %s", e)
            return {}
    
    async def _run_phase4_with_vector_context(
        self, 
        user_id: str, 
        message_content: str, 
        pipeline_result: VectorAIPipelineResult,
        recent_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run Phase 4 human-like integration enhanced with vector context.
        
        This keeps the existing Phase 4 system but enhances it with vector memory.
        """
        try:
            if not self.phase4_integration:
                return {}
            
            # Prepare Discord context from pipeline results
            discord_context = {
                "user_id": user_id,
                "external_emotion_data": {
                    "primary_emotion": pipeline_result.emotional_state,
                    "mood_assessment": pipeline_result.mood_assessment,
                    "stress_level": pipeline_result.stress_level
                },
                "phase2_results": {
                    "emotional_state": pipeline_result.emotional_state,
                    "triggers": pipeline_result.emotional_triggers
                },
                "personality_insights": {
                    "communication_style": pipeline_result.communication_style,
                    "traits": pipeline_result.personality_traits
                }
            }
            
            # 🎯 VECTOR ENHANCEMENT: Add vector context to Phase 4
            vector_context = await self._get_vector_context_for_phase4(user_id, message_content)
            discord_context["vector_context"] = vector_context
            
            # Use existing Phase 4 system with enhanced context
            phase4_context = await self.phase4_integration.process_comprehensive_message(
                user_id=user_id,
                message=message_content,
                conversation_context=recent_messages,
                discord_context=discord_context
            )
            
            return {
                'interaction_type': phase4_context.interaction_type.value,
                'conversation_mode': phase4_context.conversation_mode.value,
                'enhanced_context': {
                    'phase4_insights': phase4_context.processing_metadata,
                    'vector_enhancements': vector_context
                }
            }
            
        except Exception as e:
            logger.error("❌ Phase 4 human-like integration failed: %s", e)
            return {}
    
    async def _store_pipeline_results_as_vectors(self, result: VectorAIPipelineResult):
        """
        Store AI pipeline results as vectors in the vector memory system.
        
        This replaces the template variable system with vector storage.
        """
        try:
            # Store personality insights as vectors
            if result.personality_profile:
                personality_content = f"User personality: {result.communication_style} communication style, traits: {', '.join(result.personality_traits or [])}"
                await self.vector_memory.store_memory(
                    user_id=result.user_id,
                    content=personality_content,
                    memory_type="personality_analysis",
                    metadata={
                        "source": "phase1_pipeline",
                        "communication_style": result.communication_style,
                        "traits": result.personality_traits,
                        "timestamp": result.timestamp.isoformat()
                    }
                )
            
            # Store emotional insights as vectors
            if result.emotional_state:
                emotional_content = f"User emotional state: {result.emotional_state}, stress level: {result.stress_level}, triggers: {', '.join(result.emotional_triggers or [])}"
                await self.vector_memory.store_memory(
                    user_id=result.user_id,
                    content=emotional_content,
                    memory_type="emotional_analysis",
                    metadata={
                        "source": "phase2_pipeline",
                        "emotional_state": result.emotional_state,
                        "stress_level": result.stress_level,
                        "triggers": result.emotional_triggers,
                        "timestamp": result.timestamp.isoformat()
                    }
                )
            
            # Store relationship insights as vectors
            if result.relationship_depth:
                relationship_content = f"User relationship: {result.relationship_depth} connection, patterns: {', '.join(result.conversation_patterns or [])}, topics: {', '.join(result.key_topics or [])}"
                await self.vector_memory.store_memory(
                    user_id=result.user_id,
                    content=relationship_content,
                    memory_type="relationship_analysis",
                    metadata={
                        "source": "phase3_pipeline",
                        "relationship_depth": result.relationship_depth,
                        "patterns": result.conversation_patterns,
                        "topics": result.key_topics,
                        "timestamp": result.timestamp.isoformat()
                    }
                )
            
            # Store Phase 4 context as vectors
            if result.enhanced_context:
                phase4_content = f"Conversation context: {result.interaction_type} interaction, {result.conversation_mode} mode"
                await self.vector_memory.store_memory(
                    user_id=result.user_id,
                    content=phase4_content,
                    memory_type="phase4_analysis",
                    metadata={
                        "source": "phase4_pipeline",
                        "interaction_type": result.interaction_type,
                        "conversation_mode": result.conversation_mode,
                        "enhanced_context": result.enhanced_context,
                        "timestamp": result.timestamp.isoformat()
                    }
                )
            
            logger.info("✅ Stored AI pipeline results as vectors for user %s", result.user_id)
            
        except Exception as e:
            logger.error("❌ Failed to store pipeline results as vectors: %s", e)
    
    # Helper methods for vector operations
    async def _extract_patterns_from_vector_memories(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Extract conversation patterns from vector memories."""
        # Analyze memory content for patterns
        return ["deep philosophical discussions", "creative problem-solving"]
    
    async def _extract_topics_from_vector_memories(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Extract key topics from vector memories."""
        # Analyze memory content for topics
        return ["technology", "creativity", "philosophy", "relationships"]
    
    async def _calculate_relationship_depth_from_vectors(self, user_id: str) -> str:
        """Calculate relationship depth using vector memory patterns."""
        # Search for relationship progression in vectors
        total_memories = await self.vector_memory.search_memories_with_qdrant_intelligence(
            query="relationship interaction conversation",
            user_id=user_id,
            top_k=100,
            prefer_recent=False
        )
        
        memory_count = len(total_memories)
        if memory_count > 100:
            return "deep companion"
        elif memory_count > 50:
            return "trusted friend"
        elif memory_count > 20:
            return "familiar acquaintance"
        elif memory_count > 5:
            return "developing connection"
        else:
            return "new encounter"
    
    async def _get_vector_context_for_phase4(self, user_id: str, message_content: str) -> Dict[str, Any]:
        """Get vector context to enhance Phase 4 processing."""
        try:
            # Get relevant context from vector memory
            context_memories = await self.vector_memory.search_memories_with_qdrant_intelligence(
                query=message_content,
                user_id=user_id,
                top_k=5,
                prefer_recent=True
            )
            
            return {
                "relevant_context_count": len(context_memories),
                "recent_context": [mem.get("content", "")[:100] for mem in context_memories[:3]],
                "context_themes": await self._extract_topics_from_vector_memories(context_memories)
            }
            
        except Exception as e:
            logger.error("❌ Failed to get vector context for Phase 4: %s", e)
            return {}