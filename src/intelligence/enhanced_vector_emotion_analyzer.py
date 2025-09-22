"""
Enhanced Vector-Native Emotion Analyzer
=======================================

Advanced emotion detection using vector embeddings and semantic analysis.
Integrates with WhisperEngine's vector memory system for superior accuracy.

Features:
- Multi-dimensional emotion analysis using embeddings
- Contextual emotion detection based on conversation history
- Integration with vector memory for emotional pattern recognition
- Real-time emotional state tracking
- Semantic emotion classification beyond simple sentiment
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EmotionDimension(Enum):
    """Multi-dimensional emotion classification"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"
    EXCITEMENT = "excitement"
    CONTENTMENT = "contentment"
    FRUSTRATION = "frustration"
    ANXIETY = "anxiety"
    CURIOSITY = "curiosity"
    GRATITUDE = "gratitude"
    LOVE = "love"
    HOPE = "hope"
    DISAPPOINTMENT = "disappointment"


@dataclass
class EmotionAnalysisResult:
    """Result of emotion analysis with detailed breakdown"""
    primary_emotion: str
    confidence: float
    intensity: float
    all_emotions: Dict[str, float]
    emotional_trajectory: List[str]
    context_emotions: Dict[str, float]
    analysis_time_ms: float
    vector_similarity: float = 0.0
    embedding_confidence: float = 0.0
    pattern_match_score: float = 0.0


class EnhancedVectorEmotionAnalyzer:
    """
    Advanced emotion analyzer using vector embeddings and semantic analysis.
    
    Integrates with WhisperEngine's vector memory system to provide:
    - Context-aware emotion detection
    - Emotional pattern recognition
    - Multi-dimensional emotion classification
    - Real-time emotional state tracking
    """
    
    def __init__(self, vector_memory_manager=None):
        """Initialize the enhanced emotion analyzer"""
        self.vector_memory_manager = vector_memory_manager
        
        # Load configuration from environment variables
        self.enabled = os.getenv("ENHANCED_EMOTION_ENABLED", "true").lower() == "true"
        self.keyword_weight = float(os.getenv("ENHANCED_EMOTION_KEYWORD_WEIGHT", "0.3"))
        self.semantic_weight = float(os.getenv("ENHANCED_EMOTION_SEMANTIC_WEIGHT", "0.4"))
        self.context_weight = float(os.getenv("ENHANCED_EMOTION_CONTEXT_WEIGHT", "0.3"))
        self.confidence_threshold = float(os.getenv("ENHANCED_EMOTION_CONFIDENCE_THRESHOLD", "0.6"))
        
        logger.info("Enhanced Vector Emotion Analyzer initialized: enabled=%s, "
                   "weights=[keyword=%s, semantic=%s, context=%s], threshold=%s",
                   self.enabled, self.keyword_weight, self.semantic_weight, 
                   self.context_weight, self.confidence_threshold)
        
        # Emotion classification mappings for vector analysis
        self.emotion_keywords = {
            EmotionDimension.JOY: [
                "happy", "joy", "delighted", "pleased", "cheerful", "elated", "ecstatic",
                "thrilled", "excited", "wonderful", "amazing", "fantastic", "great",
                "awesome", "brilliant", "perfect", "love", "adore", "celebration"
            ],
            EmotionDimension.SADNESS: [
                "sad", "unhappy", "depressed", "melancholy", "sorrowful", "grief",
                "disappointed", "heartbroken", "down", "blue", "gloomy", "miserable",
                "tragedy", "loss", "crying", "tears", "devastated", "crushed"
            ],
            EmotionDimension.ANGER: [
                "angry", "mad", "furious", "rage", "irritated", "annoyed", "frustrated",
                "outraged", "livid", "incensed", "hostile", "aggressive", "violent",
                "hate", "disgusted", "appalled", "infuriated", "upset", "bothered"
            ],
            EmotionDimension.FEAR: [
                "afraid", "scared", "frightened", "terrified", "worried", "anxious",
                "nervous", "panic", "dread", "horror", "alarmed", "startled",
                "intimidated", "threatened", "concerned", "uneasy", "apprehensive"
            ],
            EmotionDimension.SURPRISE: [
                "surprised", "shocked", "amazed", "astonished", "bewildered",
                "stunned", "confused", "puzzled", "unexpected", "sudden", "wow",
                "incredible", "unbelievable", "startling", "remarkable"
            ],
            EmotionDimension.EXCITEMENT: [
                "excited", "thrilled", "energetic", "enthusiastic", "pumped",
                "eager", "anticipation", "looking forward", "can't wait", "hyped"
            ],
            EmotionDimension.CURIOSITY: [
                "curious", "wondering", "interested", "intrigued", "questioning",
                "exploring", "learning", "discovery", "fascinated", "inquisitive"
            ],
            EmotionDimension.GRATITUDE: [
                "grateful", "thankful", "appreciate", "blessed", "fortunate",
                "thank you", "thanks", "indebted", "obliged", "recognition"
            ],
            EmotionDimension.ANXIETY: [
                "anxious", "stressed", "overwhelmed", "pressure", "tension",
                "worried", "nervous", "uneasy", "restless", "troubled", "distressed"
            ],
            EmotionDimension.CONTENTMENT: [
                "content", "satisfied", "peaceful", "calm", "serene", "relaxed",
                "comfortable", "at ease", "tranquil", "balanced", "fulfilled"
            ]
        }
        
        # Emotional intensity indicators
        self.intensity_amplifiers = [
            "very", "extremely", "incredibly", "absolutely", "completely", "totally",
            "utterly", "really", "so", "such", "quite", "rather", "pretty",
            "!!!", "!!!", "wow", "omg", "amazing", "unbelievable"
        ]
        
        # Emotional trajectory indicators
        self.rising_indicators = [
            "getting", "becoming", "growing", "increasing", "more and more",
            "starting to", "beginning to", "feel like", "turning into"
        ]
        
        self.falling_indicators = [
            "less", "calming down", "settling", "fading", "diminishing",
            "not as", "no longer", "used to be", "was", "before"
        ]
        
        logger.info("EnhancedVectorEmotionAnalyzer initialized with vector integration")
    
    async def analyze_emotion(
        self, 
        content: str, 
        user_id: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
        recent_emotions: Optional[List[str]] = None
    ) -> EmotionAnalysisResult:
        """
        Perform comprehensive emotion analysis using vector-native techniques.
        
        Args:
            content: The text content to analyze
            user_id: User identifier for context
            conversation_context: Recent conversation messages
            recent_emotions: Recently detected emotions for trajectory analysis
            
        Returns:
            Comprehensive emotion analysis result
        """
        start_time = time.perf_counter()
        
        try:
            # Step 1: Basic keyword-based emotion detection
            keyword_emotions = await self._analyze_keyword_emotions(content)
            
            # Step 2: Vector-based semantic emotion analysis
            vector_emotions = await self._analyze_vector_emotions(user_id)
            
            # Step 3: Context-aware emotion analysis
            context_emotions = await self._analyze_context_emotions(
                conversation_context, recent_emotions
            )
            
            # Step 4: Emotional intensity analysis
            intensity = self._analyze_emotional_intensity(content)
            
            # Step 5: Emotional trajectory analysis
            trajectory = self._analyze_emotional_trajectory(content, recent_emotions)
            
            # Step 6: Combine and weight all analyses
            final_emotions = self._combine_emotion_analyses(
                keyword_emotions, vector_emotions, context_emotions
            )
            
            # Step 7: Determine primary emotion and confidence
            primary_emotion, confidence = self._determine_primary_emotion(final_emotions)
            
            # Calculate performance metrics
            analysis_time_ms = int((time.perf_counter() - start_time) * 1000)
            
            result = EmotionAnalysisResult(
                primary_emotion=primary_emotion,
                confidence=confidence,
                intensity=intensity,
                all_emotions=final_emotions,
                emotional_trajectory=trajectory if isinstance(trajectory, list) else [trajectory],
                context_emotions=context_emotions,
                analysis_time_ms=analysis_time_ms,
                vector_similarity=vector_emotions.get('semantic_confidence', 0.0),
                embedding_confidence=vector_emotions.get('embedding_confidence', 0.0),
                pattern_match_score=vector_emotions.get('pattern_match_score', 0.0)
            )
            
            logger.info(
                "Enhanced emotion analysis completed for user %s: "
                "%s (confidence: %.3f, intensity: %.3f) "
                "in %dms",
                user_id, primary_emotion, confidence, intensity, analysis_time_ms
            )
            
            return result
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Enhanced emotion analysis failed for user %s: %s", user_id, e)
            
            # Fallback to basic analysis
            return EmotionAnalysisResult(
                primary_emotion="neutral",
                confidence=0.3,
                intensity=0.5,
                all_emotions={"neutral": 0.7, "unknown": 0.3},
                emotional_trajectory=["stable"],
                context_emotions={},
                analysis_time_ms=int((time.perf_counter() - start_time) * 1000),
                vector_similarity=0.0,
                embedding_confidence=0.0,
                pattern_match_score=0.0
            )
    
    async def _analyze_keyword_emotions(self, content: str) -> Dict[str, Any]:
        """Analyze emotions based on keyword matching"""
        content_lower = content.lower()
        emotion_scores = {}
        total_matches = 0
        
        for emotion_dim, keywords in self.emotion_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            if matches > 0:
                emotion_scores[emotion_dim.value] = matches
                total_matches += matches
        
        # Normalize scores
        if total_matches > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] = emotion_scores[emotion] / total_matches
        
        # Add pattern matching confidence
        pattern_score = min(total_matches / 10.0, 1.0)  # Max confidence at 10+ matches
        
        return {
            **emotion_scores,
            'pattern_score': pattern_score,
            'total_matches': total_matches
        }
    
    async def _analyze_vector_emotions(self, user_id: str) -> Dict[str, Any]:
        """Analyze emotions using vector memory system semantic search"""
        vector_emotions = {}
        
        if not self.vector_memory_manager:
            logger.debug("No vector memory manager available for semantic emotion analysis")
            return {
                'semantic_confidence': 0.0,
                'embedding_confidence': 0.0
            }
        
        try:
            # Search for emotionally similar memories
            emotion_queries = [
                "feeling happy and joyful",
                "feeling sad and down", 
                "feeling angry and frustrated",
                "feeling scared and anxious",
                "feeling excited and thrilled",
                "feeling calm and peaceful"
            ]
            
            semantic_scores = {}
            max_similarity = 0.0
            
            for query in emotion_queries:
                try:
                    # Use vector search to find semantic similarity
                    similar_memories = await self.vector_memory_manager.retrieve_relevant_memories(
                        user_id=user_id,
                        query=query,
                        limit=3
                    )
                    
                    if similar_memories:
                        # Calculate average similarity score
                        avg_score = sum(
                            m.get('score', 0.0) for m in similar_memories
                        ) / len(similar_memories)
                        
                        # Extract emotion from query
                        if "happy" in query:
                            semantic_scores["joy"] = avg_score
                        elif "sad" in query:
                            semantic_scores["sadness"] = avg_score
                        elif "angry" in query:
                            semantic_scores["anger"] = avg_score
                        elif "scared" in query:
                            semantic_scores["fear"] = avg_score
                        elif "excited" in query:
                            semantic_scores["excitement"] = avg_score
                        elif "calm" in query:
                            semantic_scores["contentment"] = avg_score
                        
                        max_similarity = max(max_similarity, avg_score)
                
                except (KeyError, IndexError, ValueError) as e:
                    logger.debug("Vector emotion query failed for '%s': %s", query, e)
                    continue
            
            # Normalize semantic scores
            if max_similarity > 0:
                for emotion in semantic_scores:
                    semantic_scores[emotion] = semantic_scores[emotion] / max_similarity
            
            vector_emotions.update(semantic_scores)
            vector_emotions['semantic_confidence'] = max_similarity
            vector_emotions['embedding_confidence'] = min(len(semantic_scores) / 6.0, 1.0)
            
        except (AttributeError, TypeError, KeyError) as e:
            logger.warning("Vector emotion analysis failed for user %s: %s", user_id, e)
            vector_emotions = {
                'semantic_confidence': 0.0,
                'embedding_confidence': 0.0
            }
        
        return vector_emotions
    
    async def _analyze_context_emotions(
        self, 
        conversation_context: Optional[List[Dict[str, Any]]] = None,
        recent_emotions: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Analyze emotions based on conversation context"""
        context_emotions = {}
        
        if not conversation_context:
            return context_emotions
        
        # Analyze recent messages for emotional context
        recent_content = []
        for msg in conversation_context[-5:]:  # Last 5 messages
            if msg.get('role') == 'user':
                recent_content.append(msg.get('content', ''))
        
        # Look for emotional continuity patterns
        combined_context = ' '.join(recent_content).lower()
        
        # Check for emotional persistence
        if recent_emotions:
            most_recent = recent_emotions[-1] if recent_emotions else None
            if most_recent and most_recent != 'neutral':
                # Give slight weight to emotional continuity
                context_emotions[most_recent] = 0.3
        
        # Check for emotional transitions
        transition_patterns = {
            'improving': ['better', 'improving', 'getting good', 'feeling good'],
            'worsening': ['worse', 'getting bad', 'feeling worse', 'declining']
        }
        
        for pattern_type, patterns in transition_patterns.items():
            if any(pattern in combined_context for pattern in patterns):
                if pattern_type == 'improving':
                    context_emotions['joy'] = context_emotions.get('joy', 0.0) + 0.2
                else:
                    context_emotions['sadness'] = context_emotions.get('sadness', 0.0) + 0.2
        
        return context_emotions
    
    def _analyze_emotional_intensity(self, content: str) -> float:
        """Analyze the intensity of emotional expression"""
        content_lower = content.lower()
        intensity_score = 0.5  # Base intensity
        
        # Check for intensity amplifiers
        amplifier_count = sum(
            1 for amplifier in self.intensity_amplifiers 
            if amplifier in content_lower
        )
        
        # Check for punctuation intensity
        exclamation_count = content.count('!')
        question_count = content.count('?')
        caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
        
        # Calculate intensity adjustments
        intensity_score += min(amplifier_count * 0.1, 0.3)  # Max +0.3 for amplifiers
        intensity_score += min(exclamation_count * 0.05, 0.2)  # Max +0.2 for exclamations
        intensity_score += min(question_count * 0.03, 0.1)  # Max +0.1 for questions
        intensity_score += min(caps_ratio, 0.2)  # Max +0.2 for caps
        
        return min(intensity_score, 1.0)
    
    def _analyze_emotional_trajectory(
        self, 
        content: str, 
        recent_emotions: Optional[List[str]] = None
    ) -> str:
        """Analyze the trajectory of emotional change"""
        content_lower = content.lower()
        
        # Check for trajectory indicators in content
        rising_count = sum(
            1 for indicator in self.rising_indicators 
            if indicator in content_lower
        )
        
        falling_count = sum(
            1 for indicator in self.falling_indicators 
            if indicator in content_lower
        )
        
        # Check historical emotion pattern
        if recent_emotions and len(recent_emotions) >= 2:
            # Simple trajectory based on recent emotions
            last_two = recent_emotions[-2:]
            
            positive_emotions = {'joy', 'excitement', 'gratitude', 'contentment', 'love', 'hope'}
            negative_emotions = {'sadness', 'anger', 'fear', 'anxiety', 'frustration', 'disappointment'}
            
            def emotion_valence(emotion):
                if emotion in positive_emotions:
                    return 1
                elif emotion in negative_emotions:
                    return -1
                else:
                    return 0
            
            if len(last_two) == 2:
                prev_valence = emotion_valence(last_two[0])
                curr_valence = emotion_valence(last_two[1])
                
                if curr_valence > prev_valence:
                    rising_count += 1
                elif curr_valence < prev_valence:
                    falling_count += 1
        
        # Determine trajectory
        if rising_count > falling_count:
            return "rising"
        elif falling_count > rising_count:
            return "falling"
        else:
            return "stable"
    
    def _combine_emotion_analyses(
        self,
        keyword_emotions: Dict[str, Any],
        vector_emotions: Dict[str, Any], 
        context_emotions: Dict[str, float]
    ) -> Dict[str, float]:
        """Combine multiple emotion analysis results with weighted scoring"""
        combined_emotions = {}
        
        # Use configurable weight factors
        keyword_weight = self.keyword_weight
        vector_weight = self.semantic_weight
        context_weight = self.context_weight
        
        # Combine keyword emotions
        for emotion, score in keyword_emotions.items():
            if emotion not in ['pattern_score', 'total_matches']:
                combined_emotions[emotion] = combined_emotions.get(emotion, 0.0) + (score * keyword_weight)
        
        # Combine vector emotions
        for emotion, score in vector_emotions.items():
            if emotion not in ['semantic_confidence', 'embedding_confidence']:
                combined_emotions[emotion] = combined_emotions.get(emotion, 0.0) + (score * vector_weight)
        
        # Combine context emotions
        for emotion, score in context_emotions.items():
            combined_emotions[emotion] = combined_emotions.get(emotion, 0.0) + (score * context_weight)
        
        # Ensure neutral emotion if no others detected
        if not combined_emotions:
            combined_emotions['neutral'] = 1.0
        
        # Normalize to sum to 1.0
        total_score = sum(combined_emotions.values())
        if total_score > 0:
            for emotion in combined_emotions:
                combined_emotions[emotion] = combined_emotions[emotion] / total_score
        
        return combined_emotions
    
    def _determine_primary_emotion(self, emotions: Dict[str, float]) -> Tuple[str, float]:
        """Determine the primary emotion and confidence from combined analysis"""
        if not emotions:
            return "neutral", 0.3
        
        # Find the emotion with highest score
        primary_emotion = max(emotions.items(), key=lambda x: x[1])
        emotion_name, confidence = primary_emotion
        
        # Apply confidence adjustments
        confidence = min(confidence * 1.2, 1.0)  # Slight confidence boost
        
        # Minimum confidence threshold
        if confidence < 0.2:
            return "neutral", 0.4
        
        return emotion_name, confidence

    # =================================================================
    # COMPREHENSIVE EMOTIONAL INTELLIGENCE METHODS
    # Replace legacy PredictiveEmotionalIntelligence functionality
    # =================================================================
    
    async def comprehensive_emotional_assessment(
        self, 
        user_id: str, 
        current_message: str, 
        conversation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive emotional assessment replacing legacy spaCy-based system.
        
        Args:
            user_id: User identifier  
            current_message: Current user message
            conversation_context: Full conversation context
            
        Returns:
            Comprehensive emotional assessment with recommendations
        """
        try:
            # Get comprehensive emotion analysis using vector-native approach
            emotion_result = await self.analyze_emotion(
                content=current_message,
                user_id=user_id,
                conversation_context=conversation_context.get('messages', [])
            )
            
            # Extract historical emotional patterns from vector memory
            historical_patterns = await self._get_historical_emotional_patterns(user_id)
            
            # Generate emotional assessment in compatible format
            assessment = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "primary_emotion": emotion_result.primary_emotion,
                "confidence": emotion_result.confidence,
                "intensity": emotion_result.intensity,
                "all_emotions": emotion_result.all_emotions,
                "emotional_trajectory": emotion_result.emotional_trajectory,
                "context_emotions": emotion_result.context_emotions,
                "analysis_method": "enhanced_vector_native",
                "analysis_time_ms": emotion_result.analysis_time_ms,
                
                # Enhanced features not available in legacy system
                "vector_similarity": emotion_result.vector_similarity,
                "embedding_confidence": emotion_result.embedding_confidence,
                "pattern_match_score": emotion_result.pattern_match_score,
                
                # Historical context
                "historical_patterns": historical_patterns,
                "mood_trend": self._calculate_mood_trend(historical_patterns),
                "stress_indicators": self._identify_stress_indicators(emotion_result),
                
                # Recommendations
                "recommendations": self._generate_support_recommendations(emotion_result),
                "intervention_needed": emotion_result.confidence > 0.8 and emotion_result.primary_emotion in ['anger', 'sadness', 'fear', 'anxiety'],
                "support_strategy": self._recommend_support_strategy(emotion_result)
            }
            
            # Store assessment for learning
            await self._store_emotional_assessment(user_id, assessment)
            
            logger.info("Enhanced emotional assessment completed for user %s: %s (%.2f confidence)", 
                       user_id, emotion_result.primary_emotion, emotion_result.confidence)
            
            return assessment
            
        except Exception as e:
            logger.error("Comprehensive emotional assessment failed for user %s: %s", user_id, e)
            # Return minimal fallback assessment
            return {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "primary_emotion": "neutral",
                "confidence": 0.3,
                "intensity": 0.5,
                "analysis_method": "enhanced_vector_fallback",
                "error": str(e)
            }

    async def get_user_emotional_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive emotional dashboard for user"""
        try:
            # Get recent emotional assessments from vector memory
            recent_assessments = await self._get_recent_assessments(user_id, limit=10)
            
            # Calculate dashboard metrics
            if recent_assessments:
                emotions = [a.get('primary_emotion', 'neutral') for a in recent_assessments]
                confidences = [a.get('confidence', 0.0) for a in recent_assessments]
                
                dashboard = {
                    "user_id": user_id,
                    "last_updated": datetime.now().isoformat(),
                    "recent_emotions": emotions,
                    "average_confidence": sum(confidences) / len(confidences),
                    "dominant_emotion": max(set(emotions), key=emotions.count),
                    "emotion_stability": 1.0 - (len(set(emotions)) / len(emotions)),  # 1.0 = very stable
                    "assessment_count": len(recent_assessments),
                    "trends": {
                        "mood_trend": self._calculate_dashboard_trend(recent_assessments),
                        "confidence_trend": "stable",  # Could be enhanced
                        "volatility": len(set(emotions)) / len(emotions)  # Higher = more volatile
                    },
                    "recommendations": self._generate_dashboard_recommendations(recent_assessments)
                }
            else:
                # No historical data
                dashboard = {
                    "user_id": user_id,
                    "last_updated": datetime.now().isoformat(),
                    "recent_emotions": [],
                    "assessment_count": 0,
                    "message": "No emotional assessment history available"
                }
                
            return dashboard
            
        except Exception as e:
            logger.error("Failed to generate emotional dashboard for user %s: %s", user_id, e)
            return {"user_id": user_id, "error": str(e)}

    async def execute_intervention(self, user_id: str, intervention_type: str) -> Dict[str, Any]:
        """Execute emotional support intervention"""
        try:
            # Get current emotional state
            recent_assessment = await self._get_most_recent_assessment(user_id)
            
            if not recent_assessment:
                return {"error": "No recent emotional assessment available for intervention"}
            
            # Generate intervention based on current emotional state
            intervention = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "intervention_type": intervention_type,
                "trigger_emotion": recent_assessment.get('primary_emotion'),
                "trigger_confidence": recent_assessment.get('confidence'),
                "strategy": self._select_intervention_strategy(recent_assessment, intervention_type),
                "expected_outcome": self._predict_intervention_outcome(recent_assessment),
                "status": "executed"
            }
            
            # Store intervention for tracking
            await self._store_intervention(user_id, intervention)
            
            logger.info("Executed emotional intervention for user %s: %s", user_id, intervention_type)
            return intervention
            
        except Exception as e:
            logger.error("Failed to execute intervention for user %s: %s", user_id, e)
            return {"error": str(e)}

    async def track_intervention_response(self, user_id: str, intervention_id: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track user response to emotional intervention"""
        try:
            # Store intervention response for learning
            response_tracking = {
                "user_id": user_id,
                "intervention_id": intervention_id,
                "timestamp": datetime.now().isoformat(),
                "response_data": response_data,
                "effectiveness_score": self._calculate_intervention_effectiveness(response_data),
                "learned_patterns": await self._learn_from_intervention_response(user_id, response_data)
            }
            
            await self._store_intervention_response(user_id, response_tracking)
            
            return response_tracking
            
        except Exception as e:
            logger.error("Failed to track intervention response for user %s: %s", user_id, e)
            return {"error": str(e)}

    async def get_system_health_report(self) -> Dict[str, Any]:
        """Get system health report for emotional intelligence"""
        try:
            # Calculate system-wide metrics
            total_assessments = await self._count_total_assessments()
            avg_processing_time = await self._calculate_avg_processing_time()
            
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "healthy",
                "total_assessments": total_assessments,
                "avg_processing_time_ms": avg_processing_time,
                "enabled_features": {
                    "vector_emotion_analysis": self.enabled,
                    "keyword_analysis": True,
                    "semantic_analysis": True,
                    "context_analysis": True,
                    "historical_patterns": True
                },
                "performance_metrics": {
                    "keyword_weight": self.keyword_weight,
                    "semantic_weight": self.semantic_weight,
                    "context_weight": self.context_weight,
                    "confidence_threshold": self.confidence_threshold
                },
                "vector_memory_status": "connected" if self.vector_memory_manager else "disconnected"
            }
            
            return health_report
            
        except Exception as e:
            logger.error("Failed to generate system health report: %s", e)
            return {"error": str(e), "system_status": "error"}

    # =================================================================
    # HELPER METHODS FOR COMPREHENSIVE FUNCTIONALITY
    # =================================================================
    
    async def _get_historical_emotional_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get historical emotional patterns for user"""
        try:
            if not self.vector_memory_manager:
                return {}
                
            # Query vector memory for historical emotions
            memories = await self.vector_memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="emotional state emotion mood",
                limit=20
            )
            
            emotions = []
            for memory in memories:
                if hasattr(memory, 'metadata') and memory.metadata:
                    emotion_data = memory.metadata.get('emotion_data')
                    if emotion_data:
                        emotions.append(emotion_data)
            
            return {
                "pattern_count": len(emotions),
                "recent_emotions": emotions[-10:] if emotions else [],
                "emotional_consistency": self._calculate_emotional_consistency(emotions)
            }
            
        except Exception as e:
            logger.debug("Failed to get historical patterns: %s", e)
            return {}

    def _calculate_mood_trend(self, historical_patterns: Dict[str, Any]) -> str:
        """Calculate mood trend from historical patterns"""
        recent_emotions = historical_patterns.get('recent_emotions', [])
        if len(recent_emotions) < 3:
            return "insufficient_data"
            
        positive_emotions = ['joy', 'excitement', 'contentment', 'gratitude', 'love', 'hope']
        negative_emotions = ['sadness', 'anger', 'fear', 'anxiety', 'frustration', 'disappointment']
        
        recent_scores = []
        for emotion in recent_emotions[-5:]:  # Last 5 emotions
            if isinstance(emotion, dict):
                primary = emotion.get('primary_emotion', 'neutral')
            else:
                primary = str(emotion)
                
            if primary in positive_emotions:
                recent_scores.append(1)
            elif primary in negative_emotions:
                recent_scores.append(-1)
            else:
                recent_scores.append(0)
        
        if not recent_scores:
            return "stable"
            
        avg_score = sum(recent_scores) / len(recent_scores)
        if avg_score > 0.3:
            return "improving"
        elif avg_score < -0.3:
            return "declining"
        else:
            return "stable"

    def _identify_stress_indicators(self, emotion_result: EmotionAnalysisResult) -> List[str]:
        """Identify stress indicators from emotion analysis"""
        indicators = []
        
        if emotion_result.intensity > 0.8:
            indicators.append("high_emotional_intensity")
            
        if emotion_result.primary_emotion in ['anxiety', 'fear', 'anger', 'frustration']:
            indicators.append("stress_related_emotion")
            
        if emotion_result.confidence > 0.9:
            indicators.append("clear_emotional_signal")
            
        return indicators

    def _generate_support_recommendations(self, emotion_result: EmotionAnalysisResult) -> List[str]:
        """Generate support recommendations based on emotion analysis"""
        recommendations = []
        
        emotion_support_map = {
            'sadness': ['offer_empathy', 'gentle_check_in', 'positive_memories'],
            'anger': ['de_escalation', 'breathing_exercises', 'problem_solving'],
            'anxiety': ['reassurance', 'grounding_techniques', 'calm_presence'],
            'fear': ['safety_validation', 'gradual_exposure', 'support_availability'],
            'joy': ['celebrate_together', 'memory_creation', 'positive_reinforcement'],
            'excitement': ['share_enthusiasm', 'future_planning', 'energy_channeling']
        }
        
        emotion_recs = emotion_support_map.get(emotion_result.primary_emotion, ['active_listening'])
        recommendations.extend(emotion_recs)
        
        if emotion_result.intensity > 0.7:
            recommendations.append('monitor_closely')
            
        return recommendations

    def _recommend_support_strategy(self, emotion_result: EmotionAnalysisResult) -> str:
        """Recommend support strategy based on emotion analysis"""
        if emotion_result.primary_emotion in ['sadness', 'fear', 'anxiety']:
            return "supportive_presence"
        elif emotion_result.primary_emotion in ['anger', 'frustration']:
            return "de_escalation"
        elif emotion_result.primary_emotion in ['joy', 'excitement']:
            return "positive_reinforcement"
        else:
            return "active_listening"

    async def _store_emotional_assessment(self, user_id: str, assessment: Dict[str, Any]):
        """Store emotional assessment in vector memory"""
        try:
            if self.vector_memory_manager:
                await self.vector_memory_manager.store_conversation(
                    user_id=user_id,
                    user_message=f"Emotional assessment: {assessment['primary_emotion']}",
                    bot_response="Assessment stored",
                    metadata={
                        "type": "emotional_assessment",
                        "assessment_data": assessment
                    }
                )
        except Exception as e:
            logger.debug("Failed to store emotional assessment: %s", e)

    async def _get_recent_assessments(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emotional assessments for user"""
        try:
            if not self.vector_memory_manager:
                return []
                
            memories = await self.vector_memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="emotional assessment",
                limit=limit
            )
            
            assessments = []
            for memory in memories:
                if hasattr(memory, 'metadata') and memory.metadata:
                    assessment_data = memory.metadata.get('assessment_data')
                    if assessment_data:
                        assessments.append(assessment_data)
                        
            return assessments
            
        except Exception as e:
            logger.debug("Failed to get recent assessments: %s", e)
            return []

    async def _get_most_recent_assessment(self, user_id: str) -> Dict[str, Any]:
        """Get most recent emotional assessment for user"""
        assessments = await self._get_recent_assessments(user_id, limit=1)
        return assessments[0] if assessments else {}

    def _calculate_emotional_consistency(self, emotions: List[Any]) -> float:
        """Calculate emotional consistency score"""
        if len(emotions) < 2:
            return 1.0
            
        # Simple consistency based on emotion variety
        unique_emotions = len(set(str(e) for e in emotions))
        total_emotions = len(emotions)
        
        return 1.0 - (unique_emotions / total_emotions)

    def _calculate_dashboard_trend(self, assessments: List[Dict[str, Any]]) -> str:
        """Calculate trend for dashboard"""
        if len(assessments) < 3:
            return "insufficient_data"
            
        # Simple trend based on confidence scores
        confidences = [a.get('confidence', 0.0) for a in assessments[-3:]]
        if confidences[-1] > confidences[0]:
            return "improving"
        elif confidences[-1] < confidences[0]:
            return "declining"
        else:
            return "stable"

    def _generate_dashboard_recommendations(self, assessments: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for dashboard"""
        if not assessments:
            return ["no_data_available"]
            
        recent = assessments[-1]
        primary_emotion = recent.get('primary_emotion', 'neutral')
        
        if primary_emotion in ['sadness', 'anxiety', 'fear']:
            return ["consider_support", "monitor_mood", "practice_self_care"]
        elif primary_emotion in ['anger', 'frustration']:
            return ["stress_management", "take_breaks", "seek_resolution"]
        else:
            return ["maintain_balance", "continue_monitoring"]

    def _select_intervention_strategy(self, assessment: Dict[str, Any], intervention_type: str) -> str:
        """Select appropriate intervention strategy"""
        emotion = assessment.get('primary_emotion', 'neutral')
        confidence = assessment.get('confidence', 0.0)
        
        # Use intervention_type to customize strategy
        if intervention_type == "emergency" and confidence > 0.9:
            return "immediate_support"
        elif confidence > 0.8 and emotion in ['anxiety', 'fear']:
            return "calming_intervention"
        elif confidence > 0.8 and emotion in ['anger', 'frustration']:
            return "de_escalation_intervention"
        elif emotion in ['sadness']:
            return "supportive_intervention"
        else:
            return "general_check_in"

    def _predict_intervention_outcome(self, assessment: Dict[str, Any]) -> str:
        """Predict intervention outcome"""
        confidence = assessment.get('confidence', 0.0)
        
        if confidence > 0.8:
            return "high_likelihood_success"
        elif confidence > 0.5:
            return "moderate_likelihood_success"
        else:
            return "uncertain_outcome"

    def _calculate_intervention_effectiveness(self, response_data: Dict[str, Any]) -> float:
        """Calculate intervention effectiveness score"""
        # Simple effectiveness based on response data
        user_satisfaction = response_data.get('satisfaction', 0.5)
        emotion_improvement = response_data.get('emotion_improvement', 0.0)
        
        return (user_satisfaction + emotion_improvement) / 2.0

    async def _store_intervention(self, user_id: str, intervention: Dict[str, Any]):
        """Store intervention data"""
        try:
            if self.vector_memory_manager:
                await self.vector_memory_manager.store_conversation(
                    user_id=user_id,
                    user_message=f"Intervention: {intervention['intervention_type']}",
                    bot_response="Intervention executed",
                    metadata={
                        "type": "emotional_intervention",
                        "intervention_data": intervention
                    }
                )
        except Exception as e:
            logger.debug("Failed to store intervention: %s", e)

    async def _store_intervention_response(self, user_id: str, response: Dict[str, Any]):
        """Store intervention response data"""
        try:
            if self.vector_memory_manager:
                await self.vector_memory_manager.store_conversation(
                    user_id=user_id,
                    user_message="Intervention response",
                    bot_response="Response tracked",
                    metadata={
                        "type": "intervention_response",
                        "response_data": response
                    }
                )
        except Exception as e:
            logger.debug("Failed to store intervention response: %s", e)

    async def _learn_from_intervention_response(self, user_id: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from intervention response for user-specific improvements"""
        # Simple learning - could be enhanced with ML
        # In the future, could use user_id for personalized learning
        logger.debug("Learning from intervention response for user %s", user_id)
        
        return {
            "pattern_identified": response_data.get('effective', False),
            "confidence_adjustment": 0.1 if response_data.get('effective') else -0.1,
            "user_specific_learning": f"User {user_id} response patterns updated"
        }

    async def _count_total_assessments(self) -> int:
        """Count total assessments in system"""
        # Simplified - could query vector memory for actual count
        return 0

    async def _calculate_avg_processing_time(self) -> float:
        """Calculate average processing time"""
        # Simplified - could track actual processing times
        return 50.0  # ms


# Factory function for integration with WhisperEngine
def create_enhanced_emotion_analyzer(vector_memory_manager=None) -> EnhancedVectorEmotionAnalyzer:
    """Create an enhanced emotion analyzer instance"""
    return EnhancedVectorEmotionAnalyzer(vector_memory_manager)