"""
🚨 FAIL-FAST RoBERTa Architecture

Instead of silent fallbacks that mask quality issues, we should:
1. FAIL FAST when RoBERTa is unavailable 
2. Expose quality metrics prominently
3. Alert when degraded modes are active
4. Make fallback usage visible to users

This prevents the "silent quality degradation" problem.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AnalysisQuality(Enum):
    """Quality levels for emotion analysis"""
    HIGH_QUALITY = "roberta"      # RoBERTa analysis
    MEDIUM_QUALITY = "vader"      # VADER fallback  
    LOW_QUALITY = "keywords"      # Keyword fallback
    DEGRADED = "unknown"          # System issues

@dataclass
class QualityAwareResult:
    """Result with explicit quality indication"""
    primary_emotion: str
    confidence: float
    all_emotions: Dict[str, float]
    
    # Quality transparency
    analysis_quality: AnalysisQuality
    quality_score: float  # 0.0-1.0
    fallback_reason: Optional[str]
    
    # Performance metrics
    processing_time_ms: float
    model_availability: bool

class FailFastEmotionAnalyzer:
    """
    Emotion analyzer that fails fast and exposes quality degradation
    """
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.quality_stats = {
            "total_analyses": 0,
            "roberta_successes": 0,
            "vader_fallbacks": 0, 
            "keyword_fallbacks": 0,
            "failures": 0
        }
        
        # Initialize RoBERTa or FAIL FAST
        self._initialize_roberta_or_fail()
    
    def _initialize_roberta_or_fail(self):
        """Initialize RoBERTa or fail fast if not available"""
        try:
            from transformers import pipeline
            self._roberta_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True
            )
            self.roberta_available = True
            logger.info("✅ RoBERTa emotion analyzer initialized - HIGH QUALITY MODE")
            
        except ImportError as e:
            if self.strict_mode:
                raise RuntimeError(
                    f"🚨 FAIL FAST: RoBERTa dependencies not available: {e}\n"
                    f"Expected: transformers, torch pre-installed in Docker\n"
                    f"This indicates a serious deployment issue!"
                ) from e
            else:
                logger.error("🚨 RoBERTa unavailable - DEGRADED QUALITY MODE ACTIVE")
                self.roberta_available = False
                
        except Exception as e:
            if self.strict_mode:
                raise RuntimeError(
                    f"🚨 FAIL FAST: RoBERTa model loading failed: {e}\n"
                    f"This indicates model corruption or resource issues!"
                ) from e
            else:
                logger.error("🚨 RoBERTa failed - DEGRADED QUALITY MODE ACTIVE")
                self.roberta_available = False
    
    async def analyze_with_quality_awareness(
        self, 
        message: str, 
        user_id: str
    ) -> QualityAwareResult:
        """
        Analyze emotions with explicit quality reporting
        """
        import time
        start_time = time.time()
        
        self.quality_stats["total_analyses"] += 1
        
        # Attempt RoBERTa analysis
        if self.roberta_available:
            try:
                results = self._roberta_classifier(message)
                
                # Process RoBERTa results
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
                
                processing_time = (time.time() - start_time) * 1000
                self.quality_stats["roberta_successes"] += 1
                
                return QualityAwareResult(
                    primary_emotion=primary_emotion,
                    confidence=max_confidence,
                    all_emotions=emotions,
                    analysis_quality=AnalysisQuality.HIGH_QUALITY,
                    quality_score=1.0,
                    fallback_reason=None,
                    processing_time_ms=processing_time,
                    model_availability=True
                )
                
            except Exception as e:
                logger.error("🚨 RoBERTa analysis failed: %s", str(e))
                self.quality_stats["failures"] += 1
                
                if self.strict_mode:
                    # In strict mode, bubble up the error
                    raise RuntimeError(
                        f"🚨 FAIL FAST: RoBERTa analysis failed for critical message\n"
                        f"Error: {e}\nMessage: {message[:50]}..."
                    ) from e
        
        # Fallback to VADER with quality warning
        logger.warning("🔻 QUALITY DEGRADATION: Using VADER fallback for message: %s", 
                      message[:50])
        
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            
            if not hasattr(self, '_vader_analyzer'):
                self._vader_analyzer = SentimentIntensityAnalyzer()
            
            scores = self._vader_analyzer.polarity_scores(message)
            
            # Map VADER to basic emotions (MUCH LESS ACCURATE)
            if scores['pos'] > scores['neg'] and scores['pos'] > 0.3:
                primary_emotion = "joy"
                confidence = scores['pos']
            elif scores['neg'] > 0.3:
                primary_emotion = "sadness"  # Oversimplified!
                confidence = scores['neg']
            else:
                primary_emotion = "neutral"
                confidence = abs(scores['neu'])
            
            processing_time = (time.time() - start_time) * 1000
            self.quality_stats["vader_fallbacks"] += 1
            
            return QualityAwareResult(
                primary_emotion=primary_emotion,
                confidence=confidence * 0.6,  # Reduce confidence for fallback
                all_emotions={primary_emotion: confidence},
                analysis_quality=AnalysisQuality.MEDIUM_QUALITY,
                quality_score=0.6,  # Explicitly lower quality
                fallback_reason="RoBERTa analysis failed",
                processing_time_ms=processing_time,
                model_availability=False
            )
            
        except Exception as e:
            logger.error("🚨 Even VADER fallback failed: %s", str(e))
            self.quality_stats["keyword_fallbacks"] += 1
            
            # Last resort - keyword analysis
            return self._keyword_analysis_fallback(message, start_time)
    
    def _keyword_analysis_fallback(self, message: str, start_time: float) -> QualityAwareResult:
        """Ultra-basic keyword fallback with explicit quality warning"""
        
        keywords = {
            'joy': ['happy', 'excited', 'great', 'amazing', 'wonderful'],
            'sadness': ['sad', 'down', 'depressed', 'upset', 'disappointed'],
            'anger': ['angry', 'mad', 'furious', 'frustrated', 'annoyed'],
            'fear': ['scared', 'afraid', 'worried', 'anxious', 'nervous']
        }
        
        message_lower = message.lower()
        detected_emotions = {}
        
        for emotion, emotion_keywords in keywords.items():
            matches = sum(1 for keyword in emotion_keywords if keyword in message_lower)
            if matches > 0:
                detected_emotions[emotion] = matches / len(emotion_keywords)
        
        if detected_emotions:
            primary_emotion = max(detected_emotions, key=detected_emotions.get)
            confidence = detected_emotions[primary_emotion]
        else:
            primary_emotion = "neutral"
            confidence = 0.5
            detected_emotions = {"neutral": 0.5}
        
        processing_time = (time.time() - start_time) * 1000
        
        return QualityAwareResult(
            primary_emotion=primary_emotion,
            confidence=confidence * 0.3,  # Very low confidence
            all_emotions=detected_emotions,
            analysis_quality=AnalysisQuality.LOW_QUALITY,
            quality_score=0.3,  # Explicitly poor quality
            fallback_reason="RoBERTa and VADER both failed",
            processing_time_ms=processing_time,
            model_availability=False
        )
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Get quality metrics for monitoring"""
        total = self.quality_stats["total_analyses"]
        if total == 0:
            return {"status": "no_analyses_yet"}
        
        return {
            "roberta_success_rate": self.quality_stats["roberta_successes"] / total,
            "vader_fallback_rate": self.quality_stats["vader_fallbacks"] / total,
            "keyword_fallback_rate": self.quality_stats["keyword_fallbacks"] / total,
            "failure_rate": self.quality_stats["failures"] / total,
            "quality_health": "healthy" if self.quality_stats["roberta_successes"] / total > 0.95 else "degraded",
            "total_analyses": total,
            "roberta_available": self.roberta_available
        }

# Factory with explicit quality mode choice
def create_fail_fast_emotion_analyzer(strict_mode: bool = True) -> FailFastEmotionAnalyzer:
    """
    Create emotion analyzer with fail-fast or graceful degradation
    
    Args:
        strict_mode: True = fail fast on RoBERTa unavailability
                    False = graceful degradation with quality warnings
    """
    return FailFastEmotionAnalyzer(strict_mode=strict_mode)