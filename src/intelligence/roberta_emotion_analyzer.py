"""
RoBERTa-Enhanced Emotion Analyzer for WhisperEngine

Provides state-of-art emotion detection using RoBERTa transformer models 
with VADER sentiment analysis as fallback/enhancement.

Models:
- j-hartmann/emotion-english-distilroberta-base (Primary)
  * Emotions: anger, disgust, fear, joy, neutral, sadness, surprise
  * Accuracy: ~85-90% on emotion classification
  * Size: ~250MB (vs VADER 125KB)

Architecture: RoBERTa Primary + VADER Fallback + Keywords Backup
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Import with fallback strategy
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    ROBERTA_AVAILABLE = True
except ImportError:
    ROBERTA_AVAILABLE = False

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

logger = logging.getLogger(__name__)

class EmotionDimension(Enum):
    # Primary emotions from RoBERTa model
    ANGER = "anger"
    DISGUST = "disgust"
    FEAR = "fear"
    JOY = "joy"
    NEUTRAL = "neutral"
    SADNESS = "sadness"
    SURPRISE = "surprise"
    
    # Extended emotions from Enhanced Vector Analyzer
    ANTICIPATION = "anticipation"
    TRUST = "trust"
    LOVE = "love"
    OPTIMISM = "optimism"
    PESSIMISM = "pessimism"
    EXCITEMENT = "excitement"
    CONTEMPT = "contempt"
    PRIDE = "pride"
    SHAME = "shame"
    GUILT = "guilt"
    ENVY = "envy"

@dataclass
class EmotionResult:
    dimension: EmotionDimension
    intensity: float
    confidence: float
    method: str  # "roberta", "vader", "keyword"

class RoBertaEmotionAnalyzer:
    """
    Advanced emotion analyzer using RoBERTa transformers with multi-layer fallbacks.
    
    Architecture:
    1. RoBERTa Transformer (Primary) - State-of-art accuracy
    2. VADER Sentiment (Fallback) - Fast, reliable sentiment
    3. Keyword Matching (Backup) - Always available
    """
    
    def __init__(self):
        self.roberta_classifier = None
        self.vader_analyzer = None
        self.initialization_complete = False
        
        # Initialize immediately in sync context
        self._init_analyzers()
    
    def _init_analyzers(self):
        """Initialize available analyzers with graceful fallbacks."""
        
        # Initialize RoBERTa if available
        if ROBERTA_AVAILABLE:
            try:
                logger.info("Initializing RoBERTa emotion classifier...")
                self.roberta_classifier = pipeline(
                    "text-classification",
                    model="j-hartmann/emotion-english-distilroberta-base",
                    return_all_scores=True
                )
                logger.info("✅ RoBERTa emotion classifier initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize RoBERTa classifier: {e}")
                self.roberta_classifier = None
        else:
            logger.warning("transformers library not available - RoBERTa disabled")
        
        # Initialize VADER if available  
        if VADER_AVAILABLE:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                logger.info("✅ VADER sentiment analyzer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize VADER analyzer: {e}")
                self.vader_analyzer = None
        else:
            logger.warning("vaderSentiment library not available - VADER disabled")
        
        # Keyword emotions (always available)
        self.emotion_keywords = {
            EmotionDimension.JOY: ["happy", "joyful", "elated", "cheerful", "delighted", "pleased", "content", "glad"],
            EmotionDimension.SADNESS: ["sad", "depressed", "melancholy", "grief", "sorrow", "despair", "heartbroken"],
            EmotionDimension.ANGER: ["angry", "furious", "irritated", "annoyed", "rage", "hostile", "livid"],
            EmotionDimension.FEAR: ["afraid", "scared", "terrified", "anxious", "worried", "nervous", "panic"],
            EmotionDimension.SURPRISE: ["surprised", "shocked", "amazed", "astonished", "stunned", "bewildered"],
            EmotionDimension.DISGUST: ["disgusted", "revolted", "repulsed", "sickened", "nauseated", "appalled"],
            EmotionDimension.TRUST: ["trust", "confident", "secure", "faithful", "reliable", "certain"],
            EmotionDimension.ANTICIPATION: ["excited", "eager", "hopeful", "expectant", "anticipating", "looking forward"],
        }
        
        self.initialization_complete = True
        logger.info(f"Emotion analyzer initialized - RoBERTa: {self.roberta_classifier is not None}, VADER: {self.vader_analyzer is not None}")
    
    async def analyze_emotion(self, text: str) -> List[EmotionResult]:
        """
        Analyze emotions in text using multi-layer approach.
        
        Returns emotions sorted by intensity (highest first).
        """
        if not text or not text.strip():
            return [EmotionResult(EmotionDimension.NEUTRAL, 0.5, 0.3, "default")]
        
        text = text.strip()
        all_emotions = []
        
        # Layer 1: RoBERTa Transformer Analysis (Primary)
        if self.roberta_classifier:
            try:
                roberta_results = await self._analyze_with_roberta(text)
                all_emotions.extend(roberta_results)
                logger.debug(f"RoBERTa analysis: {len(roberta_results)} emotions detected")
            except Exception as e:
                logger.warning(f"RoBERTa analysis failed: {e}")
        
        # Layer 2: VADER Sentiment Analysis (Fallback)
        if self.vader_analyzer:
            try:
                vader_results = await self._analyze_with_vader(text)
                all_emotions.extend(vader_results)
                logger.debug(f"VADER analysis: {len(vader_results)} emotions detected")
            except Exception as e:
                logger.warning(f"VADER analysis failed: {e}")
        
        # Layer 3: Keyword Analysis (Backup)
        try:
            keyword_results = await self._analyze_with_keywords(text)
            all_emotions.extend(keyword_results)
            logger.debug(f"Keyword analysis: {len(keyword_results)} emotions detected")
        except Exception as e:
            logger.error(f"Keyword analysis failed: {e}")
        
        # Return top emotions, remove duplicates, sort by intensity
        if not all_emotions:
            return [EmotionResult(EmotionDimension.NEUTRAL, 0.5, 0.2, "fallback")]
        
        # Deduplicate by emotion dimension, keeping highest intensity
        emotion_map = {}
        for emotion in all_emotions:
            if emotion.dimension not in emotion_map or emotion.intensity > emotion_map[emotion.dimension].intensity:
                emotion_map[emotion.dimension] = emotion
        
        # Sort by intensity descending
        sorted_emotions = sorted(emotion_map.values(), key=lambda x: x.intensity, reverse=True)
        
        logger.debug(f"Final emotion analysis: {len(sorted_emotions)} unique emotions")
        return sorted_emotions[:5]  # Return top 5 emotions
    
    async def _analyze_with_roberta(self, text: str) -> List[EmotionResult]:
        """Analyze emotions using RoBERTa transformer model."""
        results = []
        
        try:
            # RoBERTa inference (may be slow on first run due to model download)
            classifications = self.roberta_classifier(text)
            
            for result in classifications[0]:  # First (only) text result
                label = result["label"].lower()
                score = result["score"]
                
                # Map to our emotion dimensions
                try:
                    emotion_dim = EmotionDimension(label)
                    results.append(EmotionResult(
                        dimension=emotion_dim,
                        intensity=score,
                        confidence=0.9,  # RoBERTa has high confidence
                        method="roberta"
                    ))
                except ValueError:
                    # Unknown emotion label from model
                    logger.debug(f"Unknown RoBERTa emotion label: {label}")
                    continue
            
        except Exception as e:
            logger.error(f"RoBERTa analysis error: {e}")
        
        return results
    
    async def _analyze_with_vader(self, text: str) -> List[EmotionResult]:
        """Analyze emotions using VADER sentiment analysis."""
        results = []
        
        try:
            scores = self.vader_analyzer.polarity_scores(text)
            
            # Convert VADER sentiment to emotion dimensions
            pos_score = scores["pos"]
            neg_score = scores["neg"]
            compound = scores["compound"]
            
            # Map sentiment to emotions
            if pos_score > 0.3:
                results.append(EmotionResult(
                    dimension=EmotionDimension.JOY,
                    intensity=pos_score,
                    confidence=0.7,
                    method="vader"
                ))
            
            if neg_score > 0.3:
                # Negative sentiment could be sadness or anger
                if compound <= -0.5:
                    results.append(EmotionResult(
                        dimension=EmotionDimension.SADNESS,
                        intensity=neg_score,
                        confidence=0.6,
                        method="vader"
                    ))
                else:
                    results.append(EmotionResult(
                        dimension=EmotionDimension.ANGER,
                        intensity=neg_score * 0.8,
                        confidence=0.5,
                        method="vader"
                    ))
            
            # Neutral handling
            if abs(compound) < 0.1:
                results.append(EmotionResult(
                    dimension=EmotionDimension.NEUTRAL,
                    intensity=scores["neu"],
                    confidence=0.6,
                    method="vader"
                ))
                
        except Exception as e:
            logger.error(f"VADER analysis error: {e}")
        
        return results
    
    async def _analyze_with_keywords(self, text: str) -> List[EmotionResult]:
        """Analyze emotions using keyword matching (always available fallback)."""
        results = []
        text_lower = text.lower()
        
        for emotion_dim, keywords in self.emotion_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                # Calculate intensity based on keyword density
                intensity = min(matches / len(keywords.split()), 1.0)
                results.append(EmotionResult(
                    dimension=emotion_dim,
                    intensity=intensity,
                    confidence=0.4,  # Lower confidence for keyword matching
                    method="keyword"
                ))
        
        return results
    
    def get_primary_emotion(self, emotions: List[EmotionResult]) -> EmotionResult:
        """Get the strongest emotion from analysis results."""
        if not emotions:
            return EmotionResult(EmotionDimension.NEUTRAL, 0.5, 0.2, "default")
        
        return emotions[0]  # Already sorted by intensity
    
    def is_available(self) -> Dict[str, bool]:
        """Check which analysis methods are available."""
        return {
            "roberta": self.roberta_classifier is not None,
            "vader": self.vader_analyzer is not None,
            "keywords": True,  # Always available
            "initialized": self.initialization_complete
        }

# Global instance for reuse
_emotion_analyzer = None

def get_emotion_analyzer() -> RoBertaEmotionAnalyzer:
    """Get singleton emotion analyzer instance."""
    global _emotion_analyzer
    if _emotion_analyzer is None:
        _emotion_analyzer = RoBertaEmotionAnalyzer()
    return _emotion_analyzer

# Factory function for protocol compliance
async def create_roberta_emotion_analyzer() -> RoBertaEmotionAnalyzer:
    """Create and return RoBERTa emotion analyzer."""
    analyzer = get_emotion_analyzer()
    # Ensure initialization is complete
    if not analyzer.initialization_complete:
        analyzer._init_analyzers()
    return analyzer