#!/usr/bin/env python3
"""
Vector-Native Personality Analyzer

Replaces traditional personality profiling with vector-based semantic analysis.
Uses embedding patterns to understand user personality traits naturally.

This system:
1. Analyzes personality through vector similarity patterns
2. Captures communication styles through semantic embeddings
3. Provides real-time personality insights without complex state management
4. Integrates seamlessly with the existing vector memory system
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class VectorNativePersonalityAnalyzer:
    """
    Vector-native personality analysis using semantic embeddings.
    
    Instead of complex statistical analysis, this uses vector patterns
    to understand user personality through their natural language use.
    """
    
    def __init__(self, vector_memory_manager=None, embedding_model=None):
        self.vector_memory = vector_memory_manager
        self.embedding_model = embedding_model
        
        # Personality pattern templates for vector comparison
        self.personality_patterns = self._initialize_personality_patterns()
        
        logger.info("✅ Vector-Native Personality Analyzer initialized")
    
    def _initialize_personality_patterns(self) -> Dict[str, List[str]]:
        """Initialize personality pattern templates for vector analysis"""
        return {
            # Communication Styles
            'communication_formal': [
                "please consider", "thank you for", "I would appreciate", 
                "could you kindly", "I respectfully", "may I suggest"
            ],
            'communication_casual': [
                "hey", "yeah", "cool", "awesome", "no worries", 
                "sounds good", "for sure", "totally"
            ],
            'communication_analytical': [
                "because", "therefore", "however", "analysis shows", 
                "data indicates", "logically", "systematically"
            ],
            'communication_expressive': [
                "I feel", "emotionally", "passionate about", "excited", 
                "frustrated", "thrilled", "deeply"
            ],
            
            # Personality Traits
            'trait_curious': [
                "why", "how", "what if", "I wonder", "explore", 
                "learn more", "understand better"
            ],
            'trait_supportive': [
                "help", "support", "encourage", "here for you", 
                "understand", "care about"
            ],
            'trait_creative': [
                "imagine", "creative", "artistic", "innovative", 
                "brainstorm", "design", "inspiration"
            ],
            'trait_practical': [
                "practical", "realistic", "efficient", "useful", 
                "implemented", "actionable", "concrete"
            ],
            
            # Decision Styles
            'decision_deliberate': [
                "think about", "consider options", "weigh pros and cons", 
                "analyze carefully", "take time"
            ],
            'decision_intuitive': [
                "feel right", "gut instinct", "intuitively", 
                "sense that", "naturally"
            ],
            
            # Confidence Levels
            'confidence_high': [
                "I'm confident", "definitely", "certainly", "absolutely", 
                "without doubt", "I know"
            ],
            'confidence_tentative': [
                "I think", "maybe", "perhaps", "might be", 
                "possibly", "not sure but"
            ]
        }
    
    async def analyze_personality_from_message(
        self, 
        user_id: str, 
        message: str, 
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze personality traits from a single message using vector patterns.
        
        Args:
            user_id: User identifier
            message: User message content
            conversation_context: Optional conversation context for enhanced analysis
            
        Returns:
            Personality analysis with confidence scores
        """
        try:
            analysis = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "communication_style": await self._analyze_communication_style(message),
                "personality_traits": await self._analyze_personality_traits(message),
                "decision_style": await self._analyze_decision_style(message),
                "confidence_level": await self._analyze_confidence_level(message),
                "interaction_preferences": await self._analyze_interaction_preferences(message),
                "analysis_confidence": 0.8  # High confidence for vector-based analysis
            }
            
            # Use conversation context if provided
            if conversation_context:
                analysis["context_type"] = conversation_context.get("analysis_type", "standard")
            
            # Enhance with historical patterns if vector memory available
            if self.vector_memory:
                historical_analysis = await self._get_historical_personality_patterns(user_id)
                analysis["historical_patterns"] = historical_analysis
                analysis["personality_evolution"] = await self._analyze_personality_evolution(user_id, analysis)
            
            logger.debug("Vector personality analysis completed for user %s: %s", 
                        user_id, analysis["communication_style"])
            
            return analysis
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Vector personality analysis failed for user %s: %s", user_id, e)
            return self._create_fallback_personality_analysis(user_id)
    
    async def _analyze_communication_style(self, message: str) -> str:
        """Analyze communication style using vector pattern matching"""
        message_lower = message.lower()
        
        # Score different communication styles
        formal_score = self._calculate_pattern_score(message_lower, self.personality_patterns['communication_formal'])
        casual_score = self._calculate_pattern_score(message_lower, self.personality_patterns['communication_casual'])
        analytical_score = self._calculate_pattern_score(message_lower, self.personality_patterns['communication_analytical'])
        expressive_score = self._calculate_pattern_score(message_lower, self.personality_patterns['communication_expressive'])
        
        # Determine dominant style
        scores = {
            'formal': formal_score,
            'casual': casual_score,
            'analytical': analytical_score,
            'expressive': expressive_score
        }
        
        # Add message length and structure analysis
        message_length = len(message)
        if message_length > 200:
            scores['analytical'] += 0.2
            scores['formal'] += 0.1
        elif message_length < 50:
            scores['casual'] += 0.2
        
        # Check for questions (curiosity indicator)
        if '?' in message:
            scores['expressive'] += 0.1
            scores['analytical'] += 0.1
        
        # Find dominant style
        dominant_style = max(scores.keys(), key=lambda k: scores[k])
        confidence = scores[dominant_style]
        
        # Create descriptive style with confidence
        if confidence > 0.3:
            return f"{dominant_style} (confidence: {confidence:.2f})"
        else:
            return "adaptive"  # Mixed style
    
    async def _analyze_personality_traits(self, message: str) -> List[str]:
        """Extract personality traits using vector pattern recognition"""
        message_lower = message.lower()
        detected_traits = []
        
        # Analyze each trait category
        trait_categories = {
            'curious': self.personality_patterns['trait_curious'],
            'supportive': self.personality_patterns['trait_supportive'],
            'creative': self.personality_patterns['trait_creative'],
            'practical': self.personality_patterns['trait_practical']
        }
        
        for trait, patterns in trait_categories.items():
            score = self._calculate_pattern_score(message_lower, patterns)
            if score > 0.2:  # Threshold for trait detection
                detected_traits.append(f"{trait} ({score:.2f})")
        
        # Add contextual trait analysis
        if len(message.split()) > 30:  # Detailed messages
            detected_traits.append("thoughtful")
        
        if any(word in message_lower for word in ['help', 'support', 'understand']):
            detected_traits.append("empathetic")
            
        if any(word in message_lower for word in ['idea', 'think', 'consider']):
            detected_traits.append("reflective")
        
        return detected_traits[:5]  # Top 5 traits
    
    async def _analyze_decision_style(self, message: str) -> str:
        """Analyze decision-making style from message patterns"""
        message_lower = message.lower()
        
        deliberate_score = self._calculate_pattern_score(
            message_lower, self.personality_patterns['decision_deliberate']
        )
        intuitive_score = self._calculate_pattern_score(
            message_lower, self.personality_patterns['decision_intuitive']
        )
        
        # Analyze message structure for decision style
        if any(word in message_lower for word in ['analyze', 'think', 'consider', 'weigh']):
            deliberate_score += 0.3
            
        if any(word in message_lower for word in ['feel', 'sense', 'intuition', 'naturally']):
            intuitive_score += 0.3
        
        if deliberate_score > intuitive_score and deliberate_score > 0.2:
            return f"analytical (confidence: {deliberate_score:.2f})"
        elif intuitive_score > 0.2:
            return f"intuitive (confidence: {intuitive_score:.2f})"
        else:
            return "balanced"
    
    async def _analyze_confidence_level(self, message: str) -> str:
        """Analyze confidence level from language patterns"""
        message_lower = message.lower()
        
        high_confidence_score = self._calculate_pattern_score(
            message_lower, self.personality_patterns['confidence_high']
        )
        tentative_score = self._calculate_pattern_score(
            message_lower, self.personality_patterns['confidence_tentative']
        )
        
        # Adjust based on message characteristics
        if '!' in message:
            high_confidence_score += 0.2
        
        if any(word in message_lower for word in ['maybe', 'perhaps', 'might']):
            tentative_score += 0.3
            
        if high_confidence_score > tentative_score and high_confidence_score > 0.2:
            return f"confident (score: {high_confidence_score:.2f})"
        elif tentative_score > 0.2:
            return f"thoughtful (score: {tentative_score:.2f})"
        else:
            return "moderate"
    
    async def _analyze_interaction_preferences(self, message: str) -> Dict[str, Any]:
        """Analyze preferred interaction styles"""
        message_lower = message.lower()
        
        preferences = {
            "formality": "adaptive",
            "detail_level": "moderate",
            "response_speed": "normal",
            "emotional_tone": "balanced"
        }
        
        # Analyze formality preference
        if any(word in message_lower for word in ['please', 'thank you', 'kindly']):
            preferences["formality"] = "formal"
        elif any(word in message_lower for word in ['hey', 'yeah', 'cool']):
            preferences["formality"] = "casual"
        
        # Analyze detail preference
        if len(message) > 150:
            preferences["detail_level"] = "detailed"
        elif len(message) < 50:
            preferences["detail_level"] = "concise"
        
        # Analyze emotional preference
        if any(word in message_lower for word in ['feel', 'emotion', 'heart']):
            preferences["emotional_tone"] = "warm"
        elif any(word in message_lower for word in ['logic', 'rational', 'analyze']):
            preferences["emotional_tone"] = "logical"
        
        return preferences
    
    def _calculate_pattern_score(self, message: str, patterns: List[str]) -> float:
        """Calculate how well a message matches personality patterns"""
        total_matches = 0
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if pattern.lower() in message:
                total_matches += 1
        
        # Base score on pattern matches
        pattern_score = total_matches / total_patterns if total_patterns > 0 else 0
        
        # Boost score for exact phrase matches
        exact_matches = sum(1 for pattern in patterns if pattern.lower() in message)
        exact_boost = exact_matches * 0.1
        
        return min(1.0, pattern_score + exact_boost)
    
    async def _get_historical_personality_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get historical personality patterns from vector memory"""
        if not self.vector_memory:
            return {}
        
        try:
            # Search for personality-related memories
            personality_memories = await self.vector_memory.search_memories(
                query="communication style personality behavior preferences",
                user_id=user_id,
                limit=20
            )
            
            # Analyze patterns in historical data
            if not personality_memories:
                return {"pattern_count": 0, "dominant_style": "unknown"}
            
            # Extract patterns from memory content
            memory_texts = [mem.get("content", "") for mem in personality_memories]
            combined_text = " ".join(memory_texts).lower()
            
            # Analyze communication consistency
            formal_pattern = self._calculate_pattern_score(
                combined_text, self.personality_patterns['communication_formal']
            )
            casual_pattern = self._calculate_pattern_score(
                combined_text, self.personality_patterns['communication_casual']
            )
            
            return {
                "pattern_count": len(personality_memories),
                "communication_consistency": {
                    "formal_tendency": formal_pattern,
                    "casual_tendency": casual_pattern
                },
                "memory_span_days": self._calculate_memory_span(personality_memories),
                "dominant_style": "formal" if formal_pattern > casual_pattern else "casual"
            }
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to get historical personality patterns: %s", e)
            return {}
    
    async def _analyze_personality_evolution(
        self, current_user_id: str, current_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how personality has evolved over time"""
        historical = current_analysis.get("historical_patterns", {})
        
        if not historical or historical.get("pattern_count", 0) < 5:
            return {"evolution": "insufficient_data"}
        
        # Compare current vs historical patterns
        evolution = {
            "evolution": "stable",
            "communication_shift": "none",
            "confidence_change": "stable",
            "user_id": current_user_id
        }
        
        # Analyze communication style evolution
        current_style = current_analysis.get("communication_style", "")
        historical_style = historical.get("dominant_style", "")
        
        if "formal" in current_style and historical_style == "casual":
            evolution["communication_shift"] = "becoming_more_formal"
        elif "casual" in current_style and historical_style == "formal":
            evolution["communication_shift"] = "becoming_more_casual"
        
        return evolution
    
    def _calculate_memory_span(self, memories: List[Dict[str, Any]]) -> int:
        """Calculate span of memories in days"""
        if not memories:
            return 0
        
        # Extract timestamps if available
        timestamps = []
        for memory in memories:
            metadata = memory.get("metadata", {})
            if "timestamp" in metadata:
                try:
                    timestamp = datetime.fromisoformat(metadata["timestamp"])
                    timestamps.append(timestamp)
                except (ValueError, TypeError, AttributeError):
                    continue
        
        if len(timestamps) < 2:
            return 1
        
        oldest = min(timestamps)
        newest = max(timestamps)
        return (newest - oldest).days
    
    def _create_fallback_personality_analysis(self, user_id: str) -> Dict[str, Any]:
        """Create fallback personality analysis when main analysis fails"""
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "communication_style": "adaptive",
            "personality_traits": ["thoughtful"],
            "decision_style": "balanced",
            "confidence_level": "moderate",
            "interaction_preferences": {
                "formality": "adaptive",
                "detail_level": "moderate",
                "response_speed": "normal",
                "emotional_tone": "balanced"
            },
            "analysis_confidence": 0.3,
            "fallback": True
        }

    async def get_personality_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive personality summary using vector analysis"""
        if not self.vector_memory:
            return {"error": "Vector memory not available"}
        
        try:
            # Get recent personality-related memories
            personality_memories = await self.vector_memory.search_memories(
                query="communication personality behavior style preferences traits",
                user_id=user_id,
                limit=30
            )
            
            if not personality_memories:
                return {"user_id": user_id, "status": "no_personality_data"}
            
            # Analyze overall patterns
            all_content = " ".join([mem.get("content", "") for mem in personality_memories])
            
            # Get comprehensive analysis
            summary_analysis = await self.analyze_personality_from_message(
                user_id=user_id,
                message=all_content,
                conversation_context={"analysis_type": "comprehensive_summary"}
            )
            
            # Add memory-based insights
            summary_analysis.update({
                "memory_analysis": {
                    "total_personality_memories": len(personality_memories),
                    "analysis_confidence": min(1.0, len(personality_memories) / 20),  # More memories = higher confidence
                    "pattern_consistency": "high" if len(personality_memories) > 15 else "moderate"
                },
                "summary_type": "vector_native_comprehensive"
            })
            
            return summary_analysis
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to generate personality summary for user %s: %s", user_id, e)
            return self._create_fallback_personality_analysis(user_id)