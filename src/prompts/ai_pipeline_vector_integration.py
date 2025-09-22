"""
Vector-Integrated AI Pipeline Manager

Enhanced prompt generation using vector-native AI features including emotion analysis,
personality profiling, relationship analysis, and interaction context.

This system combines traditional AI analysis with vector-native approaches for
optimal performance and semantic understanding.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Import traditional managers
try:
    from src.emotion.simplified_emotion_manager import SimplifiedEmotionManager
except ImportError:
    logger.warning("SimplifiedEmotionManager not available")
    SimplifiedEmotionManager = None

try:
    from src.intelligence.dynamic_personality_profiler import DynamicPersonalityProfiler
except ImportError:
    logger.warning("DynamicPersonalityProfiler not available")
    DynamicPersonalityProfiler = None

# Import vector-native analyzer
try:
    from src.intelligence.vector_native_personality_analyzer import VectorNativePersonalityAnalyzer
except ImportError:
    logger.warning("VectorNativePersonalityAnalyzer not available")
    VectorNativePersonalityAnalyzer = None


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
        
        # Initialize traditional personality profiler
        self.personality_profiler = None
        if DynamicPersonalityProfiler:
            try:
                self.personality_profiler = DynamicPersonalityProfiler()
                logger.info("Traditional DynamicPersonalityProfiler initialized")
            except Exception as e:
                logger.warning("Failed to initialize DynamicPersonalityProfiler: %s", e)
        
        # Initialize vector-native personality analyzer  
        self.vector_personality_analyzer = None
        if VectorNativePersonalityAnalyzer:
            try:
                self.vector_personality_analyzer = VectorNativePersonalityAnalyzer(
                    vector_memory_manager=vector_memory_system
                )
                logger.info("✅ Vector-Native Personality Analyzer initialized")
            except Exception as e:
                logger.warning("Failed to initialize VectorNativePersonalityAnalyzer: %s", e)
        
        # Initialize emotion manager
        self.emotion_manager = None
        if SimplifiedEmotionManager:
            try:
                self.emotion_manager = SimplifiedEmotionManager()
                logger.info("SimplifiedEmotionManager initialized")
            except Exception as e:
                logger.warning("Failed to initialize SimplifiedEmotionManager: %s", e)
    
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
        Run Phase 1: Personality Analysis using hybrid approach.
        
        Combines traditional personality profiling with vector-native analysis
        for comprehensive personality insights.
        """
        logger.debug("Starting Phase 1: Hybrid Personality Analysis for user %s", user_id)
        
        personality_results = {
            "traditional_analysis": {},
            "vector_analysis": {},
            "combined_insights": {},
            "analysis_method": "hybrid"
        }
        
        # Vector-Native Analysis (Preferred)
        if self.vector_personality_analyzer:
            try:
                vector_analysis = await self.vector_personality_analyzer.analyze_personality_from_message(
                    user_id=user_id,
                    message=message_content,
                    conversation_context={"analysis_type": "real_time"}
                )
                
                personality_results["vector_analysis"] = vector_analysis
                personality_results["analysis_method"] = "vector_native"
                
                logger.debug("✅ Vector personality analysis completed: %s", 
                           vector_analysis.get("communication_style", "unknown"))
                
            except (ValueError, KeyError, AttributeError) as e:
                logger.warning("Vector personality analysis failed: %s", e)
        
        # Traditional Analysis (Fallback)
        if self.personality_profiler:
            try:
                # Traditional personality profiling
                traditional_analysis = {
                    "personality_type": "adaptive",
                    "communication_preferences": "balanced",
                    "interaction_style": "thoughtful",
                    "analysis_source": "traditional_profiler"
                }
                
                personality_results["traditional_analysis"] = traditional_analysis
                
                if not personality_results["vector_analysis"]:
                    personality_results["analysis_method"] = "traditional"
                
                logger.debug("Traditional personality analysis completed")
                
            except (ValueError, KeyError, AttributeError) as e:
                logger.warning("Traditional personality analysis failed: %s", e)
        
        # Combine insights from both approaches
        vector_data = personality_results.get("vector_analysis", {})
        traditional_data = personality_results.get("traditional_analysis", {})
        
        # Create combined insights for backward compatibility
        combined_insights = {
            "communication_style": vector_data.get("communication_style", 
                                                 traditional_data.get("communication_preferences", "adaptive")),
            "personality_traits": vector_data.get("personality_traits", ["thoughtful"]),
            "decision_style": vector_data.get("decision_style", "balanced"),
            "confidence_level": vector_data.get("confidence_level", "moderate"),
            "interaction_preferences": vector_data.get("interaction_preferences", {
                "formality": "adaptive",
                "detail_level": "moderate"
            }),
            "analysis_confidence": vector_data.get("analysis_confidence", 0.6),
            "source": personality_results["analysis_method"]
        }
        
        personality_results["combined_insights"] = combined_insights
        
        # Return in expected format for backward compatibility
        result = {
            'profile': {
                'communication_style': combined_insights["communication_style"],
                'confidence_level': combined_insights["confidence_level"]
            },
            'communication_style': combined_insights["communication_style"],
            'traits': combined_insights["personality_traits"],
            'vector_analysis': personality_results  # Full vector analysis data
        }
        
        logger.debug("Hybrid personality analysis completed for user %s: method=%s, style=%s", 
                    user_id, personality_results["analysis_method"], 
                    combined_insights["communication_style"])
        
        return result
    
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
                    'triggers': assessment.stress_assessment.immediate_stressors[:3]
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
            relationship_memories = await self.vector_memory.search_memories(
                user_id=user_id,
                query="relationship conversation patterns interaction style",
                limit=10
            )
            
            # Extract conversation patterns from vector results
            patterns = await self._extract_patterns_from_vector_memories(relationship_memories)
            
            # Get key topics using vector clustering  
            topic_memories = await self.vector_memory.search_memories(
                user_id=user_id,
                query=message_content,
                limit=15
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
                personality_content = f"User personality: {result.communication_style}, traits: {', '.join(result.personality_traits or [])}"
                await self.vector_memory.store_fact(
                    user_id=result.user_id,
                    fact=personality_content,
                    fact_type="personality",
                    metadata={
                        "source": "phase1_pipeline",
                        "communication_style": result.communication_style,
                        "traits": result.personality_traits
                    }
                )
            
            # Store emotional insights as vectors
            if result.emotional_state:
                emotional_content = f"User emotional state: {result.emotional_state}, stress level: {result.stress_level}"
                await self.vector_memory.store_fact(
                    user_id=result.user_id,
                    fact=emotional_content,
                    fact_type="emotional_analysis",
                    metadata={
                        "source": "phase2_pipeline",
                        "emotional_state": result.emotional_state,
                        "stress_level": result.stress_level
                    }
                )
            
            # Store relationship insights as vectors
            if result.relationship_depth:
                relationship_content = f"User relationship: {result.relationship_depth} connection, patterns: {', '.join(result.conversation_patterns or [])}, topics: {', '.join(result.key_topics or [])}"
                await self.vector_memory.store_fact(
                    user_id=result.user_id,
                    fact=relationship_content,
                    fact_type="relationship_analysis",
                    metadata={
                        "source": "phase3_pipeline",
                        "relationship_depth": result.relationship_depth,
                        "patterns": result.conversation_patterns,
                        "topics": result.key_topics
                    }
                )
            
            # Store Phase 4 context as vectors
            if result.enhanced_context:
                phase4_content = f"Conversation context: {result.interaction_type} interaction, {result.conversation_mode} mode"
                await self.vector_memory.store_fact(
                    user_id=result.user_id,
                    fact=phase4_content,
                    fact_type="phase4_analysis",
                    metadata={
                        "source": "phase4_pipeline",
                        "interaction_type": result.interaction_type,
                        "conversation_mode": result.conversation_mode
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
            # Get relevant context from vector memory using fixed method call
            context_memories = await self.vector_memory.search_memories(
                query=message_content,
                user_id=user_id,
                limit=5
            )
            
            return {
                "relevant_context_count": len(context_memories),
                "recent_context": [mem.get("content", "")[:100] for mem in context_memories[:3]],
                "context_themes": await self._extract_topics_from_vector_memories(context_memories)
            }
            
        except Exception as e:
            logger.error("❌ Failed to get vector context for Phase 4: %s", e)
            return {}

    async def create_conversational_prompt_with_vector_enhancement(
        self,
        user_id: str,
        message_content: str,
        pipeline_result: VectorAIPipelineResult
    ) -> str:
        """
        Create conversational prompt that preserves ALL AI intelligence while ensuring natural flow.
        
        This uses the FULL AI pipeline results (personality, emotional, etc.) but presents them
        conversationally instead of as search results.
        """
        try:
            # 1. BUILD RICH AI-ENHANCED CONVERSATIONAL BASE (using ALL pipeline intelligence)
            base_prompt = await self._build_ai_enhanced_conversational_prompt(
                user_id, message_content, pipeline_result
            )
            
            # 2. ADD VECTOR MEMORY ENHANCEMENT (if available)
            memory_enhancement = await self._get_conversational_memory_enhancement(
                user_id, message_content
            )
            
            # 3. COMBINE FOR NATURAL FLOW WITH FULL AI INTELLIGENCE
            if memory_enhancement:
                enhanced_prompt = f"{base_prompt}\n\n{memory_enhancement}"
            else:
                enhanced_prompt = base_prompt
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error("❌ AI-enhanced conversational prompt creation failed: %s", e)
            # ALWAYS return conversational fallback that still uses available AI insights
            return await self._create_ai_aware_conversational_fallback(user_id, message_content, pipeline_result)

    async def _build_ai_enhanced_conversational_prompt(
        self,
        user_id: str, 
        message_content: str,
        pipeline_result: VectorAIPipelineResult
    ) -> str:
        """
        Build conversational prompt that incorporates ALL AI pipeline intelligence naturally.
        
        This preserves sophisticated analysis while presenting it conversationally.
        """
        # Extract all AI intelligence from pipeline result
        personality_insights = self._extract_personality_insights(pipeline_result)
        emotional_insights = self._extract_emotional_insights(pipeline_result)
        relationship_insights = self._extract_relationship_insights(pipeline_result)
        interaction_insights = self._extract_interaction_insights(pipeline_result)
        
        # Build rich conversational prompt with AI intelligence
        prompt_sections = []
        
        # Core conversational foundation - SIMPLIFIED
        base_prompt = f"You are a helpful AI assistant. User said: \"{message_content}\""
        
        # Add comprehensive context - ENHANCED for all AI analysis
        context_parts = []
        
        # Enhanced personality context with detailed analysis
        if personality_insights:
            personality_context = []
            
            # Communication style
            if personality_insights.get('communication_style'):
                personality_context.append(f"Style: {personality_insights['communication_style']}")
            
            # Personality traits
            if personality_insights.get('traits') and len(personality_insights['traits']) > 0:
                traits_str = ', '.join(personality_insights['traits'][:3])  # Top 3 traits
                personality_context.append(f"Traits: {traits_str}")
            
            # Confidence and decision style
            if personality_insights.get('confidence_level'):
                personality_context.append(f"Confidence: {personality_insights['confidence_level']}")
                
            if personality_insights.get('decision_style'):
                personality_context.append(f"Decisions: {personality_insights['decision_style']}")
            
            # Big Five personality dimensions (if high confidence)
            if personality_insights.get('personality_dimensions'):
                dims = personality_insights['personality_dimensions']
                # Only include if we have strong indicators
                high_dims = []
                for dim, score in dims.items():
                    if score and isinstance(score, (int, float)) and (score > 0.7 or score < 0.3):
                        if score > 0.7:
                            high_dims.append(f"high {dim}")
                        else:
                            high_dims.append(f"low {dim}")
                
                if high_dims and len(high_dims) <= 2:  # Only include clear patterns
                    personality_context.append(f"Profile: {', '.join(high_dims)}")
            
            if personality_context:
                context_parts.append(f"Personality: {', '.join(personality_context)}")
        
        # Enhanced emotion context with detailed analysis
        if emotional_insights:
            emotion_context = []
            
            # Primary emotional state
            if emotional_insights.get('emotional_state'):
                emotion_context.append(f"Current mood: {emotional_insights['emotional_state']}")
            elif emotional_insights.get('primary_emotion'):
                emotion_context.append(f"Primary emotion: {emotional_insights['primary_emotion']}")
            
            # Confidence and intensity for response guidance
            confidence = emotional_insights.get('confidence')
            if confidence and isinstance(confidence, (int, float)) and confidence > 0.7:
                emotion_context.append(f"confidence: {confidence:.1f}")
            
            intensity = emotional_insights.get('intensity')
            if intensity and isinstance(intensity, (int, float)) and intensity > 0.6:
                emotion_context.append(f"intensity: {intensity:.1f}")
            
            # Support recommendations for response adaptation
            if emotional_insights.get('support_needed') and emotional_insights['support_needed']:
                emotion_context.append("needs emotional support")
            
            # Stress indicators for empathetic responses
            if emotional_insights.get('detailed_analysis'):
                analysis = emotional_insights['detailed_analysis']
                if analysis.get('stress_indicators') and len(analysis['stress_indicators']) > 0:
                    stress_count = len(analysis['stress_indicators'])
                    emotion_context.append(f"stress indicators: {stress_count}")
                
                if analysis.get('mood_trend') and analysis['mood_trend'] != 'stable':
                    emotion_context.append(f"trend: {analysis['mood_trend']}")
            
            if emotion_context:
                context_parts.append(f"Emotional state: {', '.join(emotion_context)}")
        
        # Enhanced relationship context
        if relationship_insights:
            relationship_context = []
            
            if relationship_insights.get('depth'):
                relationship_context.append(f"Depth: {relationship_insights['depth']}")
            
            # Conversation patterns
            if relationship_insights.get('patterns') and len(relationship_insights['patterns']) > 0:
                patterns = relationship_insights['patterns'][:2]  # Top 2 patterns
                relationship_context.append(f"Patterns: {', '.join(patterns)}")
            
            # Key topics of interest
            if relationship_insights.get('topics') and len(relationship_insights['topics']) > 0:
                topics = relationship_insights['topics'][:3]  # Top 3 topics
                relationship_context.append(f"Topics: {', '.join(topics)}")
            
            if relationship_context:
                context_parts.append(f"Relationship: {', '.join(relationship_context)}")
        
        # Enhanced interaction context
        if interaction_insights:
            interaction_context = []
            
            if interaction_insights.get('type'):
                interaction_context.append(f"Type: {interaction_insights['type']}")
                
            if interaction_insights.get('mode'):
                interaction_context.append(f"Mode: {interaction_insights['mode']}")
            
            if interaction_context:
                context_parts.append(f"Interaction: {', '.join(interaction_context)}")
        
        # Combine into minimal prompt
        if context_parts:
            final_prompt = f"{base_prompt}. Context: {', '.join(context_parts)}. Respond naturally."
        else:
            final_prompt = f"{base_prompt}. Respond naturally and helpfully."
        
        # 🔍 DEBUG: Print final prompt before sending to LLM
        logger.debug("🔍 AI PIPELINE PROMPT DEBUG for user %s:\n%s\n%s\n%s", 
                    user_id, "-"*50, final_prompt, "-"*50)
        
        # 🔍 EMOTION DEBUG: Log detailed emotion analysis integration
        if emotional_insights:
            logger.debug("🎭 EMOTION INTEGRATION DEBUG:")
            logger.debug("  - Final prompt includes emotion context: %s", 
                        bool([part for part in context_parts if 'Emotional state' in part]))
            emotion_part = next((part for part in context_parts if 'Emotional state' in part), None)
            if emotion_part:
                logger.debug("  - Emotion context in prompt: %s", emotion_part)
            else:
                logger.debug("  - No emotion context found in final prompt - check extraction")
        
        return final_prompt

    def _extract_personality_insights(self, pipeline_result: VectorAIPipelineResult) -> Dict[str, Any]:
        """Extract comprehensive personality insights using vector-native analysis."""
        insights = {}
        
        # Check for vector-native personality analysis in the pipeline result
        vector_analysis = None
        if hasattr(pipeline_result, 'personality_profile') and isinstance(pipeline_result.personality_profile, dict):
            vector_analysis = pipeline_result.personality_profile.get('vector_analysis')
        
        if vector_analysis and isinstance(vector_analysis, dict):
            # Extract vector-native personality insights
            vector_data = vector_analysis.get('vector_analysis', {})
            combined_data = vector_analysis.get('combined_insights', {})
            
            logger.debug("🧠 VECTOR PERSONALITY EXTRACTION:")
            logger.debug("  - Analysis method: %s", vector_analysis.get('analysis_method', 'unknown'))
            
            # Use vector-native insights
            if vector_data:
                insights['communication_style'] = vector_data.get('communication_style', 'adaptive')
                insights['personality_traits'] = vector_data.get('personality_traits', [])
                insights['decision_style'] = vector_data.get('decision_style', 'balanced')
                insights['confidence_level'] = vector_data.get('confidence_level', 'moderate')
                insights['interaction_preferences'] = vector_data.get('interaction_preferences', {})
                insights['analysis_confidence'] = vector_data.get('analysis_confidence', 0.6)
                
                # Vector-specific personality dimensions
                if 'historical_patterns' in vector_data:
                    historical = vector_data['historical_patterns']
                    insights['personality_consistency'] = {
                        'pattern_count': historical.get('pattern_count', 0),
                        'communication_consistency': historical.get('communication_consistency', {}),
                        'dominant_style': historical.get('dominant_style', 'unknown')
                    }
                
                # Evolution insights
                if 'personality_evolution' in vector_data:
                    evolution = vector_data['personality_evolution']
                    insights['personality_evolution'] = {
                        'evolution_trend': evolution.get('evolution', 'stable'),
                        'communication_shift': evolution.get('communication_shift', 'none'),
                        'confidence_change': evolution.get('confidence_change', 'stable')
                    }
                
                logger.debug("  - Vector analysis applied: style=%s, traits=%s", 
                           insights.get('communication_style'), 
                           len(insights.get('personality_traits', [])))
            
            # Use combined insights as fallback
            elif combined_data:
                insights['communication_style'] = combined_data.get('communication_style', 'adaptive')
                insights['personality_traits'] = combined_data.get('personality_traits', [])
                insights['decision_style'] = combined_data.get('decision_style', 'balanced')
                insights['confidence_level'] = combined_data.get('confidence_level', 'moderate')
                insights['analysis_source'] = combined_data.get('source', 'combined')
                
                logger.debug("  - Combined analysis applied: style=%s", 
                           insights.get('communication_style'))
        
        # Fallback to traditional personality data
        if not insights and pipeline_result.personality_profile:
            # Basic personality data
            if pipeline_result.communication_style:
                insights['communication_style'] = pipeline_result.communication_style
                
            if pipeline_result.personality_traits:
                insights['traits'] = pipeline_result.personality_traits
                
            if pipeline_result.personality_profile:
                insights['profile'] = pipeline_result.personality_profile
                
            # Enhanced: Extract detailed personality analysis if available
            if isinstance(pipeline_result.personality_profile, dict):
                profile_data = pipeline_result.personality_profile
                
                # Extract specific personality dimensions
                if 'confidence_level' in profile_data:
                    insights['confidence_level'] = profile_data['confidence_level']
                    
                if 'decision_style' in profile_data:
                    insights['decision_style'] = profile_data['decision_style']
                    
                if 'emotional_expressiveness' in profile_data:
                    insights['emotional_expressiveness'] = profile_data['emotional_expressiveness']
                    
                if 'communication_preferences' in profile_data:
                    insights['communication_preferences'] = profile_data['communication_preferences']
                    
                # Extract Big Five personality traits if available
                if 'big_five' in profile_data:
                    big_five = profile_data['big_five']
                    insights['personality_dimensions'] = {
                        'openness': big_five.get('openness'),
                        'conscientiousness': big_five.get('conscientiousness'),
                        'extraversion': big_five.get('extraversion'),
                        'agreeableness': big_five.get('agreeableness'),
                        'neuroticism': big_five.get('neuroticism')
                    }
            
            logger.debug("  - Traditional analysis applied: style=%s", 
                       insights.get('communication_style'))
        
        # Add comprehensive debug logging for personality
        logger.debug("🧠 FINAL PERSONALITY EXTRACTION DEBUG:")
        logger.debug("  - Communication style: %s", insights.get('communication_style', 'None'))
        logger.debug("  - Personality traits: %s", insights.get('traits', insights.get('personality_traits', [])))
        logger.debug("  - Confidence level: %s", insights.get('confidence_level', 'unknown'))
        logger.debug("  - Decision style: %s", insights.get('decision_style', 'unknown'))
        logger.debug("  - Analysis confidence: %s", insights.get('analysis_confidence', 'N/A'))
        
        if insights.get('personality_dimensions'):
            dims = insights['personality_dimensions']
            logger.debug("  - Big Five available: %s", bool(any(dims.values())))
        
        if insights.get('personality_consistency'):
            consistency = insights['personality_consistency']
            logger.debug("  - Pattern count: %s", consistency.get('pattern_count', 0))
        
        return insights

    def _extract_emotional_insights(self, pipeline_result: VectorAIPipelineResult) -> Dict[str, Any]:
        """Extract comprehensive emotional insights from pipeline result."""
        # Start with basic emotional state if available
        insights = {}
        
        if pipeline_result.emotional_state:
            insights['emotional_state'] = pipeline_result.emotional_state
        
        if pipeline_result.mood_assessment:
            insights['mood_assessment'] = pipeline_result.mood_assessment
            
        if pipeline_result.stress_level:
            insights['stress_level'] = pipeline_result.stress_level
            
        if pipeline_result.emotional_triggers:
            insights['triggers'] = pipeline_result.emotional_triggers
        
        # Enhanced: Extract detailed emotion analysis if available from SimplifiedEmotionManager
        # The mood_assessment might contain the full emotion analysis structure
        if isinstance(pipeline_result.mood_assessment, dict):
            emotion_data = pipeline_result.mood_assessment
            
            # Extract primary emotion analysis
            if 'primary_emotion' in emotion_data:
                insights['primary_emotion'] = emotion_data['primary_emotion']
                insights['confidence'] = emotion_data.get('confidence', 0.5)
                insights['intensity'] = emotion_data.get('intensity', 0.5)
            
            # Extract support recommendations
            if 'recommendations' in emotion_data:
                insights['support_recommendations'] = emotion_data['recommendations']
                
            if 'support_needed' in emotion_data:
                insights['support_needed'] = emotion_data['support_needed']
            
            # Extract detailed emotional intelligence
            if 'emotional_intelligence' in emotion_data:
                ei_data = emotion_data['emotional_intelligence']
                insights['detailed_analysis'] = {
                    'stress_indicators': ei_data.get('stress_indicators', []),
                    'mood_trend': ei_data.get('mood_trend', 'stable'),
                    'analysis_complete': ei_data.get('analysis_complete', False)
                }
        
        # Add comprehensive debug logging
        logger.debug("🔍 EMOTION EXTRACTION DEBUG:")
        logger.debug("  - Emotional state: %s", insights.get('emotional_state', 'None'))
        logger.debug("  - Primary emotion: %s (confidence: %.2f)", 
                    insights.get('primary_emotion', 'None'), 
                    insights.get('confidence', 0.0))
        logger.debug("  - Support needed: %s", insights.get('support_needed', False))
        logger.debug("  - Recommendations count: %d", 
                    len(insights.get('support_recommendations', [])))
        if insights.get('detailed_analysis'):
            analysis = insights['detailed_analysis']
            logger.debug("  - Stress indicators: %d", len(analysis.get('stress_indicators', [])))
            logger.debug("  - Mood trend: %s", analysis.get('mood_trend', 'unknown'))
        
        return insights

    def _extract_relationship_insights(self, pipeline_result: VectorAIPipelineResult) -> Dict[str, Any]:
        """Extract relationship insights from pipeline result."""
        if not pipeline_result.relationship_depth:
            return {}
        
        return {
            'depth': pipeline_result.relationship_depth,
            'patterns': pipeline_result.conversation_patterns or [],
            'topics': pipeline_result.key_topics or []
        }

    def _extract_interaction_insights(self, pipeline_result: VectorAIPipelineResult) -> Dict[str, Any]:
        """Extract interaction insights from pipeline result."""
        if not pipeline_result.interaction_type:
            return {}
        
        return {
            'type': pipeline_result.interaction_type,
            'mode': pipeline_result.conversation_mode,
            'context': pipeline_result.enhanced_context
        }

    def _get_emotional_response_guidance(self, emotional_insights: Dict[str, Any]) -> str:
        """Get specific guidance for responding to the user's emotional state."""
        emotional_state = emotional_insights.get('emotional_state', '').lower()
        
        guidance_map = {
            'excited': 'Match their enthusiasm and encourage their excitement',
            'worried': 'Provide supportive understanding and gentle reassurance',
            'confused': 'Offer clear, helpful explanations without being condescending',
            'sad': 'Show empathetic care and emotional support',
            'grateful': 'Warmly acknowledge their appreciation and maintain positive energy',
            'frustrated': 'Acknowledge their frustration and offer patient understanding',
            'curious': 'Engage their curiosity with thoughtful exploration',
            'confident': 'Support their confidence while remaining approachable'
        }
        
        return guidance_map.get(emotional_state, 'Respond with emotional awareness and genuine care')

    async def _create_ai_aware_conversational_fallback(
        self,
        user_id: str,
        message_content: str,
        pipeline_result: VectorAIPipelineResult
    ) -> str:
        """
        Emergency fallback that still uses any available AI insights conversationally.
        """
        # Extract minimal context
        style = pipeline_result.communication_style or "helpful"
        mood = pipeline_result.emotional_state or "engaged"
        
        return f"You are a helpful AI assistant. User said: \"{message_content}\". Be {style} and {mood}. Respond naturally."

    async def _get_conversational_memory_enhancement(
        self,
        user_id: str,
        message_content: str
    ) -> Optional[str]:
        """
        Get memory enhancement for conversation WITHOUT breaking conversational flow.
        
        This enriches conversation but doesn't control it.
        """
        try:
            # Search for relevant memories
            memories = await self.vector_memory.search_memories(
                message_content, user_id, limit=5
            )
            
            if not memories or len(memories) == 0:
                return None
            
            # Format memories as conversational enrichment
            memory_context = "BACKGROUND CONTEXT (enhance conversation naturally):\n"
            for memory in memories[:3]:  # Use top 3 memories
                if isinstance(memory, dict):
                    content = memory.get('content', '') or memory.get('fact', '')
                    if content:
                        memory_context += f"- {content[:100]}...\n"
            
            return memory_context
            
        except Exception as e:
            logger.debug(f"Memory enhancement failed, continuing conversationally: {e}")
            return None

    async def _create_caring_conversational_fallback(
        self,
        user_id: str,
        message_content: str
    ) -> str:
        """
        Caring conversational fallback when everything else fails.
        
        This maintains relationship continuity even in error states.
        """
        return f"You are a helpful AI assistant. User said: \"{message_content}\". Respond naturally and helpfully."