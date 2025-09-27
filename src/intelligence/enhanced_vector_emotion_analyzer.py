"""
Enhanced Vector-Native Emotion Analyzer with RoBERTa Integration
===============================================================

Advanced emotion detection using RoBERTa transformers with vector embeddings.
Integrates with WhisperEngine's vector memory system for superior accuracy.

Features:
- RoBERTa transformer models for state-of-art emotion detection (Primary)
- VADER sentiment analysis for fast sentiment backup (Secondary)
- Multi-dimensional emotion analysis using embeddings (Tertiary)
- Contextual emotion detection based on conversation history
- Integration with vector memory for emotional pattern recognition
- Real-time emotional state tracking
- Semantic emotion classification beyond simple sentiment

Architecture: RoBERTa → VADER → Keywords → Embeddings
Performance: Accuracy over speed (emotional intelligence is core value)
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# RoBERTa Integration with graceful fallbacks
try:
    from transformers import pipeline
    ROBERTA_AVAILABLE = True
except ImportError:
    ROBERTA_AVAILABLE = False
    
# VADER Integration  
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

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
        
        # Load configuration from environment variables - always enabled in development!
        self.enabled = True  # Always enabled in development
        self.keyword_weight = float(os.getenv("ENHANCED_EMOTION_KEYWORD_WEIGHT", "0.3"))
        self.semantic_weight = float(os.getenv("ENHANCED_EMOTION_SEMANTIC_WEIGHT", "0.4"))
        self.context_weight = float(os.getenv("ENHANCED_EMOTION_CONTEXT_WEIGHT", "0.3"))
        self.confidence_threshold = float(os.getenv("ENHANCED_EMOTION_CONFIDENCE_THRESHOLD", "0.6"))
        
        logger.info("Enhanced Vector Emotion Analyzer initialized: enabled=%s, "
                   "weights=[keyword=%s, semantic=%s, context=%s], threshold=%s",
                   self.enabled, self.keyword_weight, self.semantic_weight, 
                   self.context_weight, self.confidence_threshold)
        
        # Emotion classification mappings for vector analysis
        # Comprehensive emotion keywords for fallback analysis (expanded with intensity indicators)
        self.emotion_keywords = {
            "joy": ["happy", "joy", "delighted", "pleased", "cheerful", "elated", "ecstatic", 
                   "thrilled", "excited", "wonderful", "amazing", "fantastic", "great", "awesome", 
                   "brilliant", "perfect", "love", "adore", "celebration", "bliss", "euphoric",
                   "overjoyed", "gleeful", "jubilant", "radiant", "beaming", "yay"],
            "sadness": ["sad", "unhappy", "depressed", "melancholy", "sorrowful", "grief", 
                       "disappointed", "heartbroken", "down", "blue", "gloomy", "miserable", "crying",
                       "tragedy", "loss", "tears", "devastated", "crushed", "despair", "desolate",
                       "mournful", "dejected", "forlorn", "disheartened", "crestfallen", "woeful"],
            "anger": ["angry", "mad", "furious", "rage", "irritated", "annoyed", "frustrated", 
                     "outraged", "livid", "incensed", "hostile", "aggressive", "hate", "disgusted",
                     "appalled", "infuriated", "upset", "bothered", "irate", "enraged", "seething",
                     "wrathful", "indignant", "resentful", "bitter", "raging"],
            "fear": ["afraid", "scared", "frightened", "terrified", "worried", "anxious", 
                    "nervous", "panic", "dread", "horror", "alarmed", "startled", "intimidated",
                    "threatened", "concerned", "uneasy", "apprehensive", "petrified", "horrified",
                    "panicked", "fearful", "timid", "trembling", "shaking"],
            "excitement": ["excited", "thrilled", "energetic", "enthusiastic", "pumped", 
                          "eager", "anticipation", "can't wait", "hyped", "electrified", "exhilarated",
                          "animated", "spirited", "vivacious", "dynamic", "charged"],
            "gratitude": ["grateful", "thankful", "appreciate", "blessed", "fortunate", 
                         "thank you", "thanks", "indebted", "obliged", "recognition", "appreciative",
                         "beholden", "grateful for", "much appreciated"],
            "curiosity": ["curious", "wondering", "interested", "intrigued", "questioning", 
                         "exploring", "learning", "discovery", "fascinated", "inquisitive", "puzzled",
                         "perplexed", "bewildered", "inquiring", "investigative"],
            "surprise": ["surprised", "shocked", "amazed", "astonished", "bewildered", 
                        "stunned", "confused", "puzzled", "unexpected", "wow", "incredible", 
                        "unbelievable", "startling", "remarkable", "astounded", "flabbergasted",
                        "dumbfounded", "taken aback"],
            "anxiety": ["anxious", "stressed", "overwhelmed", "pressure", "tension",
                       "worried", "nervous", "uneasy", "restless", "troubled", "distressed",
                       "frazzled", "agitated", "jittery", "on edge", "wound up"],
            "contentment": ["content", "satisfied", "peaceful", "calm", "serene", "relaxed",
                           "comfortable", "at ease", "tranquil", "balanced", "fulfilled", "placid",
                           "composed", "untroubled", "at peace", "mellow"],
            "disgust": ["disgusted", "gross", "eww", "revolting", "nauseating", "repulsive",
                       "sickening", "appalling", "repugnant", "loathsome", "abhorrent"],
            "shame": ["ashamed", "embarrassed", "humiliated", "mortified", "shameful", "guilty",
                     "regretful", "remorseful", "sheepish", "chagrined", "red-faced"],
            "pride": ["proud", "accomplished", "achievement", "triumphant", "victorious", "successful",
                     "accomplished", "pleased with", "satisfied with", "boastful"],
            "loneliness": ["lonely", "isolated", "alone", "solitary", "abandoned", "forsaken",
                          "desolate", "friendless", "cut off", "estranged"]
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
        
        logger.info(f"🎭 EMOTION ANALYZER: Starting comprehensive emotion analysis for user {user_id}")
        logger.info(f"🎭 EMOTION ANALYZER: Content to analyze: '{content[:100]}{'...' if len(content) > 100 else ''}'")
        logger.info(f"🎭 EMOTION ANALYZER: Context provided: {bool(conversation_context)}, Recent emotions: {recent_emotions}")
        
        try:
            # VECTOR-NATIVE ANALYSIS WITH KEYWORD FALLBACK
            
            # Step 1: Vector-based semantic emotion analysis using the actual message content
            logger.debug(f"🎭 STEP 1: Starting vector-based semantic emotion analysis")
            vector_emotions = await self._analyze_vector_emotions(user_id, content)
            logger.info(f"🎭 STEP 1 RESULT: Vector emotions: {vector_emotions}")
            
            # Step 2: Context-aware emotion analysis using vector memory
            logger.debug(f"🎭 STEP 2: Starting context-aware emotion analysis")
            context_emotions = await self._analyze_context_emotions(
                conversation_context, recent_emotions
            )
            logger.info(f"🎭 STEP 2 RESULT: Context emotions: {context_emotions}")
            
            # Step 3: Keyword-based fallback analysis (essential for new users)
            logger.debug(f"🎭 STEP 3: Starting keyword-based fallback analysis")
            keyword_emotions = self._analyze_keyword_emotions(content)
            logger.info(f"🎭 STEP 3 RESULT: Keyword emotions: {keyword_emotions}")
            
            # Step 4: Emotional intensity analysis
            logger.debug(f"🎭 STEP 4: Analyzing emotional intensity")
            intensity = self._analyze_emotional_intensity(content)
            logger.info(f"🎭 STEP 4 RESULT: Emotional intensity: {intensity:.3f}")
            
            # Step 5: Emotional trajectory analysis
            logger.debug(f"🎭 STEP 5: Analyzing emotional trajectory")
            trajectory = self._analyze_emotional_trajectory(content, recent_emotions)
            logger.info(f"🎭 STEP 5 RESULT: Emotional trajectory: {trajectory}")
            
            # Step 6: Combine all emotion analyses
            logger.debug(f"🎭 STEP 6: Combining all emotion analyses")
            final_emotions = self._combine_emotion_analyses(
                keyword_emotions, vector_emotions, context_emotions
            )
            logger.info(f"🎭 STEP 6 RESULT: Final combined emotions: {final_emotions}")
            
            # Step 7: Determine primary emotion and confidence
            primary_emotion, confidence = self._determine_primary_emotion(final_emotions)
            
            # Calculate performance metrics
            analysis_time_ms = int((time.perf_counter() - start_time) * 1000)
            
            logger.info(f"🎭 FINAL RESULT: Creating EmotionAnalysisResult with:")
            logger.info(f"  - Primary emotion: {primary_emotion}")
            logger.info(f"  - Confidence: {confidence:.3f}")
            logger.info(f"  - Intensity: {intensity:.3f}")
            logger.info(f"  - All emotions: {final_emotions}")
            logger.info(f"  - Analysis time: {analysis_time_ms}ms")
            
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
                "🎭 ENHANCED EMOTION ANALYSIS COMPLETE for user %s: "
                "%s (confidence: %.3f, intensity: %.3f) "
                "in %dms",
                user_id, primary_emotion, confidence, intensity, analysis_time_ms
            )
            
            return result
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("🎭 ENHANCED EMOTION ANALYSIS FAILED for user %s: %s", user_id, e)
            
            # Fallback to basic analysis
            fallback_result = EmotionAnalysisResult(
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
            
            logger.info(f"🎭 FALLBACK RESULT: Returning neutral fallback due to error: {fallback_result}")
            return fallback_result
    
    # KEYWORD ANALYSIS - Essential fallback for new users!
    
    def _analyze_keyword_emotions(self, content: str) -> Dict[str, float]:
        """
        Multi-layer emotion analysis: RoBERTa (primary) → VADER (fallback) → Keywords (backup).
        This is the core emotion detection method with state-of-art accuracy.
        """
        logger.info(f"🔍 KEYWORD ANALYSIS: Starting multi-layer emotion analysis for: '{content[:50]}{'...' if len(content) > 50 else ''}'")
        
        try:
            if not content:
                logger.info(f"🔍 KEYWORD ANALYSIS: Empty content, returning empty emotions")
                return {}
            
            content_lower = content.lower()
            emotion_scores = {}
            
            # LAYER 1: RoBERTa Transformer Analysis (PRIMARY - State-of-art accuracy)
            if ROBERTA_AVAILABLE:
                logger.info(f"🤖 ROBERTA ANALYSIS: RoBERTa transformer available, starting analysis")
                try:
                    # Initialize RoBERTa classifier if not already done
                    if not hasattr(self, '_roberta_classifier') or self._roberta_classifier is None:
                        logger.info("🤖 ROBERTA ANALYSIS: Initializing RoBERTa emotion classifier...")
                        self._roberta_classifier = pipeline(
                            "text-classification",
                            model="j-hartmann/emotion-english-distilroberta-base",
                            return_all_scores=True
                        )
                        logger.info("🤖 ROBERTA ANALYSIS: ✅ RoBERTa emotion classifier initialized")
                    
                    # Analyze emotions with RoBERTa
                    logger.debug(f"🤖 ROBERTA ANALYSIS: Running RoBERTa inference on content")
                    results = self._roberta_classifier(content)
                    logger.info(f"🤖 ROBERTA ANALYSIS: RoBERTa completed with {len(results[0])} emotion results")
                    
                    # Process RoBERTa results
                    for result in results[0]:  # First (only) text result
                        emotion_label = result["label"].lower()
                        confidence = result["score"]
                        
                        # Map RoBERTa labels to our emotion dimensions
                        emotion_scores[emotion_label] = confidence
                        logger.info(f"🤖 ROBERTA ANALYSIS: RoBERTa detected {emotion_label}: {confidence:.3f}")
                    
                    # If RoBERTa found strong emotions, prioritize them
                    if any(score > 0.6 for score in emotion_scores.values()):
                        logger.info(f"🤖 ROBERTA ANALYSIS: Strong emotions detected (>0.6), using RoBERTa as primary: {emotion_scores}")
                        return emotion_scores  # Return RoBERTa results directly
                    else:
                        logger.info(f"🤖 ROBERTA ANALYSIS: No strong emotions, continuing to VADER analysis")
                        
                except Exception as roberta_error:
                    logger.warning(f"🤖 ROBERTA ANALYSIS: RoBERTa analysis failed: {roberta_error}")
            else:
                logger.info(f"🤖 ROBERTA ANALYSIS: RoBERTa not available, skipping to VADER")
            
            # LAYER 2: VADER Sentiment Analysis (FALLBACK)
            if VADER_AVAILABLE:
                logger.info(f"😊 VADER ANALYSIS: VADER sentiment analyzer available, starting analysis")
                try:
                    if not hasattr(self, '_vader_analyzer') or self._vader_analyzer is None:
                        self._vader_analyzer = SentimentIntensityAnalyzer()
                        logger.info(f"😊 VADER ANALYSIS: VADER sentiment analyzer initialized")
                    
                    scores = self._vader_analyzer.polarity_scores(content)
                    logger.info(f"😊 VADER ANALYSIS: VADER scores: {scores}")
                    
                    # Map VADER scores to our emotion categories
                    if scores['pos'] > 0.3:  # Positive sentiment
                        emotion_scores['joy'] = max(emotion_scores.get('joy', 0.0), scores['pos'])
                        logger.info(f"😊 VADER ANALYSIS: Positive sentiment detected, joy score: {emotion_scores['joy']:.3f}")
                    if scores['neg'] > 0.3:  # Negative sentiment  
                        # Determine if it's anger or sadness based on keywords
                        if any(word in content_lower for word in ['angry', 'mad', 'furious', 'hate', 'rage']):
                            emotion_scores['anger'] = max(emotion_scores.get('anger', 0.0), scores['neg'])
                            logger.info(f"😊 VADER ANALYSIS: Anger keywords detected, anger score: {emotion_scores['anger']:.3f}")
                        else:
                            emotion_scores['sadness'] = max(emotion_scores.get('sadness', 0.0), scores['neg'])
                            logger.info(f"😊 VADER ANALYSIS: Negative sentiment without anger keywords, sadness score: {emotion_scores['sadness']:.3f}")
                    
                    # Use compound score for overall intensity
                    if abs(scores['compound']) > 0.1:  # Significant emotion detected
                        intensity_multiplier = min(abs(scores['compound']) + 1.0, 2.0)
                        # Boost all detected emotions based on VADER intensity
                        original_scores = emotion_scores.copy()
                        for emotion in emotion_scores:
                            emotion_scores[emotion] *= intensity_multiplier
                        logger.info(f"😊 VADER ANALYSIS: Applied intensity multiplier {intensity_multiplier:.2f}, scores before: {original_scores}, after: {emotion_scores}")
                    
                    logger.info(f"😊 VADER ANALYSIS: Final VADER-enhanced emotions: {emotion_scores}")
                    
                except Exception as vader_error:
                    logger.warning(f"😊 VADER ANALYSIS: VADER analysis failed: {vader_error}")
            else:
                logger.info(f"😊 VADER ANALYSIS: VADER not available, proceeding to keyword analysis")
            
            # LAYER 3: Keyword Analysis (BACKUP - Always available)
            # Check for emotion keywords
            for emotion_dimension, keywords in self.emotion_keywords.items():
                emotion_name = emotion_dimension  # Fixed: emotion_dimension is already a string
                matches = 0
                total_weight = 0.0
                
                for keyword in keywords:
                    if keyword in content_lower:
                        matches += 1
                        # Weight longer keywords more highly
                        weight = min(len(keyword) / 10.0, 1.0)
                        total_weight += weight
                
                if matches > 0:
                    # Base score on number of matches and total weight
                    base_score = min(matches / 3.0, 1.0)  # Max 3 matches for full score
                    weight_score = min(total_weight, 1.0)
                    keyword_score = (base_score + weight_score) / 2.0
                    
                    # Combine with any existing scores (from RoBERTa/VADER)
                    emotion_scores[emotion_name] = max(
                        emotion_scores.get(emotion_name, 0.0), 
                        keyword_score
                    )
            
            # LAYER 4: Apply intensity amplifiers
            for amplifier in self.intensity_amplifiers:
                if amplifier in content_lower:
                    # Boost all detected emotions when intensity amplifiers are present
                    for emotion in emotion_scores:
                        emotion_scores[emotion] = min(emotion_scores[emotion] * 1.3, 1.0)
                    break  # Only apply once
            
            return emotion_scores
            
        except Exception as analysis_error:
            logger.error("Emotion analysis failed: %s", analysis_error)
            # Return neutral emotion as ultimate fallback
            return {"neutral": 0.5}
    
    def _analyze_emoji_emotions(self, content: str) -> Dict[str, float]:
        """Analyze emotions from emojis in the content"""
        emoji_emotions = {
            "joy": ["😀", "😁", "😂", "😃", "😄", "😆", "😊", "😍", "🤩", "❤️", "💖", "🥰"],
            "sadness": ["😢", "😭", "😔", "💔", "😞", "😟", "🥺", "😰"],
            "anger": ["😠", "😡", "🤬", "💢"],
            "surprise": ["😲", "😱", "🤯", "😯"],
            "fear": ["😰", "😱", "😨", "😬"],
            "excitement": ["🤩", "🎉", "🔥", "⚡", "💥"],
            "gratitude": ["🙏", "💝", "🤗"],
            "curiosity": ["🤔", "❓", "🧐"]
        }
        
        emotion_scores = {}
        for emotion, emojis in emoji_emotions.items():
            count = sum(content.count(emoji) for emoji in emojis)
            if count > 0:
                emotion_scores[emotion] = min(count * 0.3, 1.0)  # Each emoji adds 0.3, max 1.0
                
        return emotion_scores
    
    async def _analyze_vector_emotions(self, user_id: str, content: str) -> Dict[str, Any]:
        """Analyze emotions using vector memory system semantic search with actual message content"""
        vector_emotions = {}
        
        if not self.vector_memory_manager:
            logger.debug("No vector memory manager available for semantic emotion analysis")
            return {
                'semantic_confidence': 0.0,
                'embedding_confidence': 0.0
            }
        
        try:
            # VECTOR-NATIVE APPROACH: Use the actual message content for semantic emotion analysis
            # Find emotionally similar messages in user's memory
            similar_emotional_memories = await self.vector_memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=content,  # Use actual message content, not hardcoded emotion queries!
                limit=5
            )
            
            semantic_scores = {}
            max_similarity = 0.0
            
            if similar_emotional_memories:
                # Extract emotional patterns from semantically similar memories
                for memory in similar_emotional_memories:
                    score = memory.get('score', 0.0)
                    max_similarity = max(max_similarity, score)
                    
                    # Get emotional context from memory metadata
                    metadata = memory.get('metadata', {})
                    emotional_context = metadata.get('emotional_context', '')
                    
                    if emotional_context and score > 0.1:  # Only consider meaningful similarities
                        # Use vector similarity to weight emotional context
                        if emotional_context in semantic_scores:
                            semantic_scores[emotional_context] = max(
                                semantic_scores[emotional_context], 
                                score
                            )
                        else:
                            semantic_scores[emotional_context] = score
            
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