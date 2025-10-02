#!/usr/bin/env python3
"""
🚀 ENHANCED 6D VECTOR CONVERSATION FLOW ANALYZER

This module provides 6D vector-enhanced conversation flow analysis,
replacing simple keyword pattern matching with sophisticated semantic similarity search.

INTEGRATION: Replaces payload-based analysis in human_like_memory_optimizer.py
with vector-native intelligence for trajectory analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorEnhancedConversationFlowAnalyzer:
    """
    🎯 6D Vector-enhanced conversation flow analysis
    
    Replaces simple keyword matching with semantic vector similarity for:
    - Conversation depth progression analysis
    - Relationship intimacy tracking  
    - Context shift detection
    - Multi-dimensional flow patterns
    """
    
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        logger.info("🚀 Initialized VectorEnhanced ConversationFlowAnalyzer")
    
    async def analyze_conversation_flow_6d(
        self, 
        user_id: str, 
        current_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        🎯 ENHANCED: Analyze conversation flow using 6D vector intelligence
        
        Replaces keyword pattern matching with semantic similarity search across:
        - Content: Topical flow continuity
        - Context: Situational mode detection  
        - Relationship: Intimacy level tracking
        - Emotion: Emotional flow patterns
        """
        try:
            logger.info(f"🔄 6D FLOW ANALYSIS: Starting for user {user_id}")
            
            # Generate embeddings for current message across multiple dimensions
            flow_embeddings = await self._generate_flow_embeddings(user_id, current_message)
            
            # Use 6D vector search for flow pattern analysis
            if hasattr(self.memory_manager, 'retrieve_memories_by_dimensions'):
                flow_memories = await self.memory_manager.retrieve_memories_by_dimensions(
                    user_id=user_id,
                    dimensions=flow_embeddings,
                    weights={
                        "context": 0.30,      # Primary: Situational flow patterns
                        "relationship": 0.25, # Secondary: Intimacy progression 
                        "content": 0.20,      # Tertiary: Topical continuity
                        "emotion": 0.15,      # Supporting: Emotional flow
                        "personality": 0.10   # Background: Character consistency
                    },
                    limit=15
                )
                
                # Analyze 6D flow patterns
                flow_analysis = self._analyze_6d_flow_patterns(flow_memories, current_message)
                flow_analysis["vector_enhanced"] = True
                flow_analysis["similar_flows_count"] = len(flow_memories)
                
            else:
                logger.warning("🔄 6D FLOW: retrieve_memories_by_dimensions not available, using fallback")
                flow_analysis = await self._fallback_flow_analysis(current_message, conversation_history)
                flow_analysis["vector_enhanced"] = False
            
            logger.info(f"🔄 6D FLOW RESULT: {flow_analysis.get('flow_type', 'unknown')} with {flow_analysis.get('confidence', 0):.3f} confidence")
            return flow_analysis
            
        except Exception as e:
            logger.error(f"🔄 6D FLOW ERROR: {e}")
            return await self._fallback_flow_analysis(current_message, conversation_history)
    
    async def _generate_flow_embeddings(self, user_id: str, current_message: str) -> Dict[str, List[float]]:
        """
        Generate embeddings for flow analysis across multiple dimensions
        """
        embeddings = {}
        
        try:
            # Context embedding - situational flow detection
            context_key = self._extract_context_situation(current_message)
            if hasattr(self.memory_manager, 'generate_embedding'):
                embeddings["context"] = await self.memory_manager.generate_embedding(
                    f"context {context_key}: {current_message}"
                )
                
                # Relationship embedding - intimacy level tracking
                relationship_key = self._extract_relationship_context(current_message, user_id)
                embeddings["relationship"] = await self.memory_manager.generate_embedding(
                    f"relationship {relationship_key}: {current_message}"
                )
                
                # Content embedding - topical flow
                embeddings["content"] = await self.memory_manager.generate_embedding(current_message)
                
                # Emotion embedding - emotional flow patterns
                emotion_key = self._extract_emotional_flow_context(current_message)
                embeddings["emotion"] = await self.memory_manager.generate_embedding(
                    f"emotion {emotion_key}: {current_message}"
                )
                
                # Personality embedding - character consistency
                personality_key = self._extract_personality_flow(current_message)
                embeddings["personality"] = await self.memory_manager.generate_embedding(
                    f"personality {personality_key}: {current_message}"
                )
            
            logger.debug(f"🔄 Generated {len(embeddings)} flow embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Flow embedding generation failed: {e}")
            return {}
    
    def _analyze_6d_flow_patterns(self, flow_memories: List[Dict[str, Any]], current_message: str) -> Dict[str, Any]:
        """
        Analyze conversation flow patterns from 6D vector-similar memories
        """
        if not flow_memories:
            return {
                "flow_type": "unknown",
                "confidence": 0.0,
                "patterns_detected": []
            }
        
        # Extract flow characteristics from similar conversations
        flow_characteristics = {
            "depth_progression": [],
            "intimacy_levels": [],
            "context_modes": [],
            "emotional_flows": [],
            "continuity_patterns": []
        }
        
        for memory in flow_memories:
            metadata = memory.get('metadata', {})
            content = memory.get('content', '')
            
            # Analyze conversation depth
            depth = self._classify_conversation_depth(content)
            flow_characteristics["depth_progression"].append(depth)
            
            # Extract intimacy indicators
            intimacy = self._extract_intimacy_level(content, metadata)
            flow_characteristics["intimacy_levels"].append(intimacy)
            
            # Identify context modes
            context_mode = metadata.get('context_situation', 'unknown')
            flow_characteristics["context_modes"].append(context_mode)
            
            # Extract emotional flow patterns
            emotional_context = metadata.get('emotional_context', 'neutral')
            flow_characteristics["emotional_flows"].append(emotional_context)
            
            # Detect continuity signals
            continuity = self._detect_continuity_signals(content)
            flow_characteristics["continuity_patterns"].append(continuity)
        
        # Synthesize flow analysis from patterns
        flow_analysis = self._synthesize_flow_analysis(flow_characteristics, current_message)
        flow_analysis["confidence"] = self._calculate_flow_confidence(flow_memories)
        
        return flow_analysis
    
    def _synthesize_flow_analysis(self, characteristics: Dict[str, List], current_message: str) -> Dict[str, Any]:
        """
        Synthesize comprehensive flow analysis from extracted characteristics
        """
        # Determine dominant flow type
        flow_type = self._determine_dominant_flow_type(characteristics)
        
        # Analyze conversation depth progression
        depth_score = self._calculate_average_depth_score(characteristics["depth_progression"])
        
        # Detect intimacy development
        intimacy_development = self._analyze_intimacy_progression(characteristics["intimacy_levels"])
        
        # Identify context patterns
        context_analysis = self._analyze_context_patterns(characteristics["context_modes"])
        
        # Emotional flow assessment
        emotional_momentum = self._assess_emotional_flow_momentum(characteristics["emotional_flows"])
        
        # Continuity score
        continuity_score = self._calculate_continuity_score(characteristics["continuity_patterns"])
        
        return {
            "flow_type": flow_type,
            "conversation_depth": depth_score,
            "intimacy_development": intimacy_development,
            "context_analysis": context_analysis,
            "emotional_momentum": emotional_momentum,
            "continuity_score": continuity_score,
            "patterns_detected": self._identify_flow_patterns(characteristics),
            "flow_prediction": self._predict_flow_direction(characteristics, current_message)
        }
    
    def _determine_dominant_flow_type(self, characteristics: Dict[str, List]) -> str:
        """Determine the dominant conversation flow type from patterns"""
        
        # Analyze continuity patterns for flow type classification
        continuity_patterns = characteristics.get("continuity_patterns", [])
        
        if not continuity_patterns:
            return "neutral"
        
        # Count pattern types
        pattern_counts = {}
        for pattern in continuity_patterns:
            if pattern and pattern != "none":
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        if not pattern_counts:
            return "neutral"
        
        # Return most common pattern
        dominant_pattern = max(pattern_counts.items(), key=lambda x: x[1])[0]
        return dominant_pattern
    
    def _calculate_average_depth_score(self, depth_progression: List[str]) -> float:
        """Calculate average conversation depth score"""
        depth_values = {
            "surface": 0.1,
            "engaging": 0.3, 
            "personal": 0.6,
            "intimate": 0.8,
            "profound": 1.0
        }
        
        if not depth_progression:
            return 0.0
        
        scores = [depth_values.get(depth, 0.0) for depth in depth_progression]
        return sum(scores) / len(scores)
    
    def _analyze_intimacy_progression(self, intimacy_levels: List[str]) -> str:
        """Analyze intimacy development pattern"""
        if not intimacy_levels:
            return "stable"
        
        # Count intimacy indicators
        high_intimacy_count = sum(1 for level in intimacy_levels if level in ["high", "intimate", "vulnerable"])
        total_count = len(intimacy_levels)
        
        if high_intimacy_count / total_count > 0.6:
            return "deepening_significantly"
        elif high_intimacy_count / total_count > 0.3:
            return "moderate_development"
        else:
            return "stable_interaction"
    
    def _analyze_context_patterns(self, context_modes: List[str]) -> Dict[str, Any]:
        """Analyze contextual conversation patterns"""
        if not context_modes:
            return {"dominant_context": "unknown", "context_variety": 0}
        
        context_counts = {}
        for context in context_modes:
            if context and context != "unknown":
                context_counts[context] = context_counts.get(context, 0) + 1
        
        if context_counts:
            dominant_context = max(context_counts.items(), key=lambda x: x[1])[0]
            return {
                "dominant_context": dominant_context,
                "context_variety": len(context_counts),
                "context_distribution": context_counts
            }
        
        return {"dominant_context": "unknown", "context_variety": 0}
    
    def _assess_emotional_flow_momentum(self, emotional_flows: List[str]) -> str:
        """Assess emotional momentum in conversation flow"""
        if not emotional_flows:
            return "neutral"
        
        positive_emotions = {"joy", "excitement", "gratitude", "hope", "contentment"}
        negative_emotions = {"sadness", "anxiety", "anger", "frustration", "disappointment"}
        
        positive_count = sum(1 for emotion in emotional_flows if emotion in positive_emotions)
        negative_count = sum(1 for emotion in emotional_flows if emotion in negative_emotions)
        
        if positive_count > negative_count:
            return "positive_momentum"
        elif negative_count > positive_count:
            return "challenging_momentum"
        else:
            return "balanced_momentum"
    
    def _calculate_continuity_score(self, continuity_patterns: List[str]) -> float:
        """Calculate conversation continuity score"""
        if not continuity_patterns:
            return 0.5
        
        # Assign continuity values to different patterns
        continuity_values = {
            "topic_continuation": 0.9,
            "callback_reference": 0.8,
            "emotional_progression": 0.7,
            "topic_shift": 0.3,
            "none": 0.5
        }
        
        scores = [continuity_values.get(pattern, 0.5) for pattern in continuity_patterns]
        return sum(scores) / len(scores)
    
    def _identify_flow_patterns(self, characteristics: Dict[str, List]) -> List[str]:
        """Identify specific flow patterns from characteristics"""
        patterns = []
        
        # Check for deepening conversation
        depth_progression = characteristics.get("depth_progression", [])
        if "intimate" in depth_progression or "profound" in depth_progression:
            patterns.append("deep_sharing")
        
        # Check for emotional progression
        emotional_flows = characteristics.get("emotional_flows", [])
        if len(set(emotional_flows)) > 3:
            patterns.append("emotional_complexity")
        
        # Check for high continuity
        continuity_patterns = characteristics.get("continuity_patterns", [])
        if continuity_patterns.count("topic_continuation") > len(continuity_patterns) * 0.5:
            patterns.append("strong_continuity")
        
        return patterns if patterns else ["standard_flow"]
    
    def _predict_flow_direction(self, characteristics: Dict[str, List], current_message: str) -> str:
        """Predict likely flow direction based on patterns"""
        
        # Analyze current message for flow indicators
        current_message_lower = current_message.lower()
        
        # Check for deepening indicators
        deepening_signals = ["personal", "important", "feel", "experience", "struggle"]
        if any(signal in current_message_lower for signal in deepening_signals):
            return "likely_deepening"
        
        # Check for topic shift indicators  
        shift_signals = ["by the way", "actually", "different topic", "changing subject"]
        if any(signal in current_message_lower for signal in shift_signals):
            return "likely_topic_shift"
        
        # Check for continuity indicators
        continuity_signals = ["also", "and", "furthermore", "speaking of"]
        if any(signal in current_message_lower for signal in continuity_signals):
            return "likely_continuation"
        
        return "stable_flow"
    
    def _calculate_flow_confidence(self, flow_memories: List[Dict[str, Any]]) -> float:
        """Calculate confidence in flow analysis based on available data"""
        if not flow_memories:
            return 0.0
        
        # More similar conversations = higher confidence
        memory_count_factor = min(len(flow_memories) / 10.0, 1.0)
        
        # Additional factors could include recency, pattern consistency, etc.
        pattern_coherence = 0.8  # Placeholder for pattern analysis
        
        overall_confidence = (memory_count_factor + pattern_coherence) / 2.0
        return min(overall_confidence, 1.0)
    
    # Helper methods for dimension extraction (simplified versions)
    def _extract_context_situation(self, content: str) -> str:
        """Extract context situation for embedding generation"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['help', 'urgent', 'crisis', 'emergency']):
            return 'crisis_support'
        elif any(word in content_lower for word in ['learn', 'explain', 'understand']):
            return 'educational'
        elif any(word in content_lower for word in ['sad', 'worried', 'anxious']):
            return 'emotional_support'
        elif any(word in content_lower for word in ['funny', 'lol', 'joke']):
            return 'playful'
        else:
            return 'casual_chat'
    
    def _extract_relationship_context(self, content: str, user_id: str) -> str:
        """Extract relationship context for embedding generation"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['secret', 'private', 'trust']):
            return 'intimacy_high_trust_confidential'
        elif any(word in content_lower for word in ['personal', 'important', 'feel']):
            return 'intimacy_personal_trust_developing'
        else:
            return 'intimacy_casual_trust_neutral'
    
    def _extract_emotional_flow_context(self, content: str) -> str:
        """Extract emotional context for flow analysis"""
        content_lower = content.lower()
        
        positive_words = ['happy', 'joy', 'excited', 'great', 'wonderful']
        negative_words = ['sad', 'worried', 'anxious', 'upset', 'frustrated']
        
        if any(word in content_lower for word in positive_words):
            return 'positive'
        elif any(word in content_lower for word in negative_words):
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_personality_flow(self, content: str) -> str:
        """Extract personality traits for flow analysis"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['creative', 'art', 'design']):
            return 'creative'
        elif any(word in content_lower for word in ['analyze', 'think', 'logic']):
            return 'analytical'
        elif any(word in content_lower for word in ['adventure', 'explore', 'travel']):
            return 'adventurous'
        else:
            return 'balanced'
    
    def _classify_conversation_depth(self, content: str) -> str:
        """Classify conversation depth level"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['deeply', 'soul', 'meaning', 'purpose']):
            return 'profound'
        elif any(word in content_lower for word in ['private', 'secret', 'vulnerable']):
            return 'intimate'
        elif any(word in content_lower for word in ['personal', 'feel', 'important']):
            return 'personal'
        elif any(word in content_lower for word in ['think', 'opinion', 'interesting']):
            return 'engaging'
        else:
            return 'surface'
    
    def _extract_intimacy_level(self, content: str, metadata: Dict[str, Any]) -> str:
        """Extract intimacy level indicators"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['trust', 'secret', 'private']):
            return 'high'
        elif any(word in content_lower for word in ['personal', 'feel', 'experience']):
            return 'moderate'
        else:
            return 'casual'
    
    def _detect_continuity_signals(self, content: str) -> str:
        """Detect conversation continuity signals"""
        content_lower = content.lower()
        
        if any(signal in content_lower for signal in ['also', 'and', 'furthermore']):
            return 'topic_continuation'
        elif any(signal in content_lower for signal in ['remember', 'like we discussed']):
            return 'callback_reference'
        elif any(signal in content_lower for signal in ['feeling better', 'still worried']):
            return 'emotional_progression'
        elif any(signal in content_lower for signal in ['by the way', 'different topic']):
            return 'topic_shift'
        else:
            return 'none'
    
    async def _fallback_flow_analysis(self, current_message: str, conversation_history: Optional[List]) -> Dict[str, Any]:
        """Fallback flow analysis when 6D vectors not available"""
        content_lower = current_message.lower()
        
        # Simple keyword-based analysis
        if any(word in content_lower for word in ['personal', 'feel', 'important']):
            flow_type = 'deepening'
            confidence = 0.6
        elif any(word in content_lower for word in ['by the way', 'different']):
            flow_type = 'topic_shift'
            confidence = 0.7
        else:
            flow_type = 'continuation'
            confidence = 0.5
        
        return {
            "flow_type": flow_type,
            "confidence": confidence,
            "conversation_depth": 0.4,
            "vector_enhanced": False,
            "analysis_method": "keyword_fallback"
        }

# Factory function for easy integration
def create_vector_conversation_flow_analyzer(memory_manager):
    """Create a vector-enhanced conversation flow analyzer"""
    return VectorEnhancedConversationFlowAnalyzer(memory_manager)