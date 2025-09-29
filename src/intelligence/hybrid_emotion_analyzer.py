"""
🚀 Hybrid Emotion Analysis Architecture

Smart emotion analysis that uses:
- RoBERTa: Where accuracy is critical (memory storage, conversation analysis)
- VADER: Where speed is critical (real-time reactions, emoji selection)
- Keywords: Where reliability is critical (health checks, fallbacks)

Design Principles:
1. Speed-Critical Paths → VADER (0.01s response time)
2. Accuracy-Critical Paths → RoBERTa (2-10s, batch processing)
3. Reliability-Critical Paths → Keywords (always available)
4. Quality monitoring and explicit choices

Author: WhisperEngine AI Team  
Created: 2024-09-23
"""

import logging
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class AnalysisMode(Enum):
    """Different analysis modes for different use cases"""
    SPEED_OPTIMIZED = "speed"      # VADER - Real-time reactions  
    ACCURACY_OPTIMIZED = "accuracy"  # RoBERTa - Memory storage
    RELIABILITY_OPTIMIZED = "reliability"  # Keywords - Always works
    ADAPTIVE = "adaptive"          # Choose based on context

class UseCase(Enum):
    """Different use cases with different requirements"""
    # Speed-critical (< 100ms response time needed)
    EMOJI_REACTIONS = "emoji_reactions"
    QUICK_SENTIMENT = "quick_sentiment" 
    REAL_TIME_CHAT = "real_time_chat"
    HEALTH_CHECK = "health_check"
    
    # Accuracy-critical (quality more important than speed)
    MEMORY_STORAGE = "memory_storage"
    CONVERSATION_ANALYSIS = "conversation_analysis"
    PERSONALITY_DETECTION = "personality_detection"
    ADVANCED_INSIGHTS = "advanced_insights"
    
    # Reliability-critical (must never fail)
    SYSTEM_MONITORING = "system_monitoring"
    FALLBACK_ANALYSIS = "fallback_analysis"
    BASIC_CATEGORIZATION = "basic_categorization"

@dataclass
class HybridAnalysisResult:
    """Result from hybrid emotion analysis with explicit mode tracking"""
    primary_emotion: str
    confidence: float
    all_emotions: Dict[str, float]
    
    # Hybrid tracking
    analysis_mode: AnalysisMode
    processing_time_ms: float
    use_case: UseCase
    quality_score: float
    
    # Performance data
    speed_optimized: bool
    accuracy_optimized: bool
    reliability_guaranteed: bool

class HybridEmotionAnalyzer:
    """
    Smart hybrid emotion analyzer that chooses the right tool for each job
    """
    
    def __init__(self):
        self.roberta_available = False
        self.vader_available = False
        
        # Initialize components
        self._initialize_roberta()
        self._initialize_vader()
        
        # Use case routing configuration
        self.use_case_routing = {
            # Speed-critical → VADER
            UseCase.EMOJI_REACTIONS: AnalysisMode.SPEED_OPTIMIZED,
            UseCase.QUICK_SENTIMENT: AnalysisMode.SPEED_OPTIMIZED,
            UseCase.REAL_TIME_CHAT: AnalysisMode.SPEED_OPTIMIZED,
            UseCase.HEALTH_CHECK: AnalysisMode.RELIABILITY_OPTIMIZED,
            
            # Accuracy-critical → RoBERTa
            UseCase.MEMORY_STORAGE: AnalysisMode.ACCURACY_OPTIMIZED,
            UseCase.CONVERSATION_ANALYSIS: AnalysisMode.ACCURACY_OPTIMIZED,
            UseCase.PERSONALITY_DETECTION: AnalysisMode.ACCURACY_OPTIMIZED,
            UseCase.ADVANCED_INSIGHTS: AnalysisMode.ACCURACY_OPTIMIZED,
            
            # Reliability-critical → Keywords
            UseCase.SYSTEM_MONITORING: AnalysisMode.RELIABILITY_OPTIMIZED,
            UseCase.FALLBACK_ANALYSIS: AnalysisMode.RELIABILITY_OPTIMIZED,
            UseCase.BASIC_CATEGORIZATION: AnalysisMode.RELIABILITY_OPTIMIZED
        }
        
        # Performance tracking
        self.performance_stats = {
            "roberta_analyses": 0,
            "vader_analyses": 0, 
            "keyword_analyses": 0,
            "roberta_avg_time": 0.0,
            "vader_avg_time": 0.0,
            "keyword_avg_time": 0.0
        }
        
        logger.info("Hybrid Emotion Analyzer initialized - RoBERTa: %s, VADER: %s", 
                   self.roberta_available, self.vader_available)
    
    def _initialize_roberta(self):
        """Initialize RoBERTa with proper error handling"""
        try:
            from transformers import pipeline
            self._roberta_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True
            )
            self.roberta_available = True
            logger.info("✅ RoBERTa initialized - ACCURACY MODE available")
        except Exception as e:
            logger.warning("⚠️ RoBERTa unavailable: %s - ACCURACY MODE disabled", str(e))
            self.roberta_available = False
    
    def _initialize_vader(self):
        """Initialize VADER with proper error handling"""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._vader_analyzer = SentimentIntensityAnalyzer()
            self.vader_available = True
            logger.info("✅ VADER initialized - SPEED MODE available")
        except Exception as e:
            logger.warning("⚠️ VADER unavailable: %s - SPEED MODE disabled", str(e))
            self.vader_available = False
    
    async def analyze_for_use_case(
        self, 
        message: str, 
        use_case: UseCase,
        user_id: str = "hybrid_analyzer"
    ) -> HybridAnalysisResult:
        """
        Analyze emotion using the optimal method for the specific use case
        """
        start_time = time.time()
        
        # Determine analysis mode based on use case
        optimal_mode = self.use_case_routing[use_case]
        
        # Route to appropriate analyzer
        if optimal_mode == AnalysisMode.ACCURACY_OPTIMIZED:
            if self.roberta_available:
                result = await self._analyze_with_roberta(message)
                analysis_mode = AnalysisMode.ACCURACY_OPTIMIZED
            elif self.vader_available:
                logger.warning("RoBERTa unavailable for accuracy use case, using VADER")
                result = await self._analyze_with_vader(message)  
                analysis_mode = AnalysisMode.SPEED_OPTIMIZED
            else:
                logger.error("Both RoBERTa and VADER unavailable, using keywords")
                result = self._analyze_with_keywords(message)
                analysis_mode = AnalysisMode.RELIABILITY_OPTIMIZED
                
        elif optimal_mode == AnalysisMode.SPEED_OPTIMIZED:
            if self.vader_available:
                result = await self._analyze_with_vader(message)
                analysis_mode = AnalysisMode.SPEED_OPTIMIZED
            elif self.roberta_available:
                logger.info("VADER unavailable for speed use case, using RoBERTa (slower)")
                result = await self._analyze_with_roberta(message)
                analysis_mode = AnalysisMode.ACCURACY_OPTIMIZED
            else:
                result = self._analyze_with_keywords(message)
                analysis_mode = AnalysisMode.RELIABILITY_OPTIMIZED
                
        else:  # RELIABILITY_OPTIMIZED
            result = self._analyze_with_keywords(message)
            analysis_mode = AnalysisMode.RELIABILITY_OPTIMIZED
        
        processing_time = (time.time() - start_time) * 1000
        
        # Update performance tracking
        self._update_performance_stats(analysis_mode, processing_time)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(analysis_mode, result)
        
        return HybridAnalysisResult(
            primary_emotion=result['primary_emotion'],
            confidence=result['confidence'],
            all_emotions=result['all_emotions'],
            analysis_mode=analysis_mode,
            processing_time_ms=processing_time,
            use_case=use_case,
            quality_score=quality_score,
            speed_optimized=analysis_mode == AnalysisMode.SPEED_OPTIMIZED,
            accuracy_optimized=analysis_mode == AnalysisMode.ACCURACY_OPTIMIZED,
            reliability_guaranteed=analysis_mode == AnalysisMode.RELIABILITY_OPTIMIZED
        )
    
    async def _analyze_with_roberta(self, message: str) -> Dict[str, Any]:
        """RoBERTa analysis - high accuracy, slower"""
        results = self._roberta_classifier(message)
        
        emotions = {}
        primary_emotion = "neutral"
        max_confidence = 0.0
        
        for result in results[0]:
            emotion = result["label"].lower()
            confidence = result["score"]
            emotions[emotion] = confidence
            
            if confidence > max_confidence:
                max_confidence = confidence
                primary_emotion = emotion
        
        return {
            'primary_emotion': primary_emotion,
            'confidence': max_confidence,
            'all_emotions': emotions
        }
    
    async def _analyze_with_vader(self, message: str) -> Dict[str, Any]:
        """VADER analysis - fast, good accuracy"""
        scores = self._vader_analyzer.polarity_scores(message)
        
        # Use Universal Emotion Taxonomy for consistent VADER mapping
        try:
            from src.intelligence.emotion_taxonomy import UniversalEmotionTaxonomy
            
            emotion_tuples = UniversalEmotionTaxonomy.vader_sentiment_to_emotions(scores)
            
            if not emotion_tuples:
                # Fallback to neutral
                return {
                    'primary_emotion': "neutral",
                    'confidence': 0.5,
                    'all_emotions': {"neutral": 0.5}
                }
            
            # Get primary emotion (highest intensity)
            primary_emotion_obj, primary_intensity, primary_confidence = max(
                emotion_tuples, key=lambda x: x[1]
            )
            primary_emotion = primary_emotion_obj.value
            
            # Build emotion distribution
            emotions = {}
            for emotion_obj, intensity, confidence in emotion_tuples:
                emotions[emotion_obj.value] = intensity
            
            return {
                'primary_emotion': primary_emotion,
                'confidence': primary_confidence,
                'all_emotions': emotions
            }
            
        except Exception as e:
            logger.error(f"VADER taxonomy mapping failed: {e}")
            # Fallback to legacy mapping
            if scores['pos'] > max(scores['neg'], scores['neu']) and scores['pos'] > 0.3:
                primary_emotion = "joy"
                confidence = scores['pos']
            elif scores['neg'] > max(scores['pos'], scores['neu']) and scores['neg'] > 0.3:
                primary_emotion = "sadness" if scores['neg'] < 0.7 else "anger"
                confidence = scores['neg']
            else:
                primary_emotion = "neutral"
                confidence = scores['neu']
            
            return {
                'primary_emotion': primary_emotion,
                'confidence': confidence,
                'all_emotions': {primary_emotion: confidence}
            }
    
    def _analyze_with_keywords(self, message: str) -> Dict[str, Any]:
        """Keyword analysis - always reliable, basic accuracy"""
        keywords = {
            'joy': ['happy', 'excited', 'great', 'amazing', 'wonderful', 'awesome', 'fantastic'],
            'sadness': ['sad', 'down', 'depressed', 'upset', 'disappointed', 'miserable'],
            'anger': ['angry', 'mad', 'furious', 'frustrated', 'annoyed', 'irritated'],
            'fear': ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'terrified'],
            'surprise': ['surprised', 'shocked', 'amazed', 'stunned', 'astonished'],
            'disgust': ['disgusted', 'revolted', 'sick', 'gross', 'awful', 'terrible']
        }
        
        message_lower = message.lower()
        detected_emotions = {}
        
        for emotion, emotion_keywords in keywords.items():
            matches = sum(1 for keyword in emotion_keywords if keyword in message_lower)
            if matches > 0:
                detected_emotions[emotion] = min(matches / len(emotion_keywords), 1.0)
        
        if detected_emotions:
            primary_emotion = max(detected_emotions, key=detected_emotions.get)
            confidence = detected_emotions[primary_emotion]
        else:
            primary_emotion = "neutral"
            confidence = 0.5
            detected_emotions = {"neutral": 0.5}
        
        return {
            'primary_emotion': primary_emotion,
            'confidence': confidence,
            'all_emotions': detected_emotions
        }
    
    def _calculate_quality_score(self, mode: AnalysisMode, result: Dict[str, Any]) -> float:
        """Calculate quality score based on analysis mode and results"""
        base_scores = {
            AnalysisMode.ACCURACY_OPTIMIZED: 0.9,    # RoBERTa
            AnalysisMode.SPEED_OPTIMIZED: 0.7,       # VADER
            AnalysisMode.RELIABILITY_OPTIMIZED: 0.5   # Keywords
        }
        
        base_score = base_scores[mode]
        
        # Boost for high confidence
        confidence = result['confidence']
        if confidence > 0.8:
            base_score += 0.05
        elif confidence < 0.3:
            base_score -= 0.1
        
        return min(1.0, max(0.0, base_score))
    
    def _update_performance_stats(self, mode: AnalysisMode, processing_time: float):
        """Update performance tracking"""
        if mode == AnalysisMode.ACCURACY_OPTIMIZED:
            self.performance_stats["roberta_analyses"] += 1
            current_avg = self.performance_stats["roberta_avg_time"]
            count = self.performance_stats["roberta_analyses"]
            self.performance_stats["roberta_avg_time"] = (
                (current_avg * (count - 1) + processing_time) / count
            )
        elif mode == AnalysisMode.SPEED_OPTIMIZED:
            self.performance_stats["vader_analyses"] += 1
            current_avg = self.performance_stats["vader_avg_time"]
            count = self.performance_stats["vader_analyses"]
            self.performance_stats["vader_avg_time"] = (
                (current_avg * (count - 1) + processing_time) / count
            )
        else:
            self.performance_stats["keyword_analyses"] += 1
            current_avg = self.performance_stats["keyword_avg_time"]
            count = self.performance_stats["keyword_analyses"]
            self.performance_stats["keyword_avg_time"] = (
                (current_avg * (count - 1) + processing_time) / count
            )
    
    # Convenience methods for common use cases
    async def analyze_for_memory_storage(self, message: str, user_id: str) -> HybridAnalysisResult:
        """High-accuracy analysis for memory storage"""
        return await self.analyze_for_use_case(message, UseCase.MEMORY_STORAGE, user_id)
    
    async def analyze_for_emoji_reaction(self, message: str, user_id: str) -> HybridAnalysisResult:
        """Fast analysis for emoji reactions"""
        return await self.analyze_for_use_case(message, UseCase.EMOJI_REACTIONS, user_id)
    
    async def analyze_for_conversation_insights(self, message: str, user_id: str) -> HybridAnalysisResult:
        """High-accuracy analysis for conversation analysis"""
        return await self.analyze_for_use_case(message, UseCase.CONVERSATION_ANALYSIS, user_id)
    
    def analyze_for_health_check(self, message: str = "test") -> HybridAnalysisResult:
        """Reliable analysis for system health checks"""
        # Synchronous version for health checks
        start_time = time.time()
        result = self._analyze_with_keywords(message)
        processing_time = (time.time() - start_time) * 1000
        
        return HybridAnalysisResult(
            primary_emotion=result['primary_emotion'],
            confidence=result['confidence'],
            all_emotions=result['all_emotions'],
            analysis_mode=AnalysisMode.RELIABILITY_OPTIMIZED,
            processing_time_ms=processing_time,
            use_case=UseCase.HEALTH_CHECK,
            quality_score=0.5,
            speed_optimized=False,
            accuracy_optimized=False,
            reliability_guaranteed=True
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance analytics"""
        total_analyses = (
            self.performance_stats["roberta_analyses"] + 
            self.performance_stats["vader_analyses"] + 
            self.performance_stats["keyword_analyses"]
        )
        
        if total_analyses == 0:
            return {"status": "no_analyses_yet"}
        
        return {
            "total_analyses": total_analyses,
            "roberta_usage_rate": self.performance_stats["roberta_analyses"] / total_analyses,
            "vader_usage_rate": self.performance_stats["vader_analyses"] / total_analyses,
            "keyword_usage_rate": self.performance_stats["keyword_analyses"] / total_analyses,
            "average_times": {
                "roberta_ms": self.performance_stats["roberta_avg_time"],
                "vader_ms": self.performance_stats["vader_avg_time"],
                "keyword_ms": self.performance_stats["keyword_avg_time"]
            },
            "availability": {
                "roberta_available": self.roberta_available,
                "vader_available": self.vader_available,
                "keywords_available": True  # Always available
            }
        }

# Factory function
def create_hybrid_emotion_analyzer() -> HybridEmotionAnalyzer:
    """Create hybrid emotion analyzer with smart routing"""
    return HybridEmotionAnalyzer()