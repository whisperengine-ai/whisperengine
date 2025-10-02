#!/usr/bin/env python3
"""
🎭 EMOTION SCORING & EMBEDDING DEMONSTRATION

This script demonstrates exactly how WhisperEngine determines emotion scores
and uses them for vector embeddings in our multi-dimensional memory system.

EMOTION PIPELINE:
1. RoBERTa Analysis → Primary Emotion + Confidence Score
2. VADER Fallback → Sentiment scores mapped to emotions  
3. Keyword Analysis → Pattern matching with intensity
4. Score Integration → Store scores in payload + create emotion embedding

CRITICAL INSIGHT: We DO use emotion scoring, but in a hybrid approach:
- Emotion SCORES stored as metadata in Qdrant payload
- Emotion EMBEDDINGS created via tag prefixing with detected emotion
- Both approaches work together for comprehensive emotion intelligence
"""

import asyncio
import logging
import os
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EmotionAnalysisResult:
    """Structured emotion analysis result from our pipeline"""
    primary_emotion: str
    confidence: float
    intensity: float
    all_emotions: Dict[str, float]
    analysis_method: str  # "roberta", "vader", or "keywords"
    
class EmotionScoringDemo:
    """
    Demonstrates WhisperEngine's emotion scoring and embedding process
    """
    
    def __init__(self):
        self.roberta_available = False
        self.vader_available = False
        self._initialize_analyzers()
    
    def _initialize_analyzers(self):
        """Initialize available emotion analyzers"""
        # Try RoBERTa (high quality)
        try:
            from transformers import pipeline
            self.roberta_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True
            )
            self.roberta_available = True
            logger.info("✅ RoBERTa emotion analyzer available")
        except ImportError:
            logger.info("❌ RoBERTa not available (transformers not installed)")
            
        # Try VADER (medium quality)
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader_analyzer = SentimentIntensityAnalyzer()
            self.vader_available = True
            logger.info("✅ VADER sentiment analyzer available")
        except ImportError:
            logger.info("❌ VADER not available (vaderSentiment not installed)")
    
    def analyze_with_roberta(self, message: str) -> Optional[EmotionAnalysisResult]:
        """Analyze emotion using RoBERTa (highest quality)"""
        if not self.roberta_available:
            return None
            
        try:
            results = self.roberta_classifier(message)
            
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
            
            return EmotionAnalysisResult(
                primary_emotion=primary_emotion,
                confidence=max_confidence,
                intensity=max_confidence,  # For RoBERTa, confidence = intensity
                all_emotions=emotions,
                analysis_method="roberta"
            )
            
        except Exception as e:
            logger.warning(f"RoBERTa analysis failed: {e}")
            return None
    
    def analyze_with_vader(self, message: str) -> Optional[EmotionAnalysisResult]:
        """Analyze emotion using VADER (medium quality)"""
        if not self.vader_available:
            return None
            
        try:
            scores = self.vader_analyzer.polarity_scores(message)
            
            # Map VADER sentiment to emotions (simplified mapping)
            if scores['pos'] > scores['neg'] and scores['pos'] > 0.3:
                primary_emotion = "joy"
                confidence = scores['pos']
                intensity = scores['pos']
                all_emotions = {
                    "joy": scores['pos'],
                    "neutral": scores['neu'],
                    "sadness": scores['neg']
                }
            elif scores['neg'] > 0.3:
                primary_emotion = "sadness" 
                confidence = scores['neg']
                intensity = scores['neg']
                all_emotions = {
                    "sadness": scores['neg'],
                    "neutral": scores['neu'],
                    "joy": scores['pos']
                }
            else:
                primary_emotion = "neutral"
                confidence = scores['neu']
                intensity = 0.5
                all_emotions = {
                    "neutral": scores['neu'],
                    "joy": scores['pos'],
                    "sadness": scores['neg']
                }
            
            return EmotionAnalysisResult(
                primary_emotion=primary_emotion,
                confidence=confidence,
                intensity=intensity,
                all_emotions=all_emotions,
                analysis_method="vader"
            )
            
        except Exception as e:
            logger.warning(f"VADER analysis failed: {e}")
            return None
    
    def analyze_with_keywords(self, message: str) -> EmotionAnalysisResult:
        """Analyze emotion using keyword patterns (fallback)"""
        content_lower = message.lower()
        
        # Comprehensive emotion keywords (from WhisperEngine)
        emotion_patterns = {
            "joy": ["happy", "joy", "delighted", "pleased", "cheerful", "elated", "ecstatic", 
                   "thrilled", "excited", "wonderful", "amazing", "fantastic", "great", "awesome"],
            "sadness": ["sad", "unhappy", "depressed", "melancholy", "sorrowful", "grief", 
                       "disappointed", "heartbroken", "down", "blue", "gloomy", "miserable"],
            "anger": ["angry", "mad", "furious", "rage", "irritated", "annoyed", "frustrated", 
                     "outraged", "livid", "incensed", "hostile", "aggressive"],
            "fear": ["afraid", "scared", "frightened", "terrified", "worried", "anxious", 
                    "nervous", "panic", "dread", "horror", "alarmed"],
            "excitement": ["excited", "thrilled", "energetic", "enthusiastic", "pumped", 
                          "eager", "anticipation", "can't wait", "hyped"],
            "gratitude": ["grateful", "thankful", "appreciate", "blessed", "fortunate", 
                         "thank you", "thanks"],
            "curiosity": ["curious", "wondering", "interested", "intrigued", "questioning", 
                         "exploring", "learning", "discovery"],
            "surprise": ["surprised", "shocked", "amazed", "astonished", "bewildered", 
                        "stunned", "confused", "puzzled", "unexpected", "wow"]
        }
        
        emotion_scores = {}
        
        for emotion, keywords in emotion_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            if matches > 0:
                emotion_scores[emotion] = matches
        
        if emotion_scores:
            # Find emotion with most keyword matches
            best_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            primary_emotion = best_emotion[0]
            match_count = best_emotion[1]
            
            # Calculate confidence based on match density
            word_count = len(message.split())
            confidence = min(match_count / max(word_count, 1), 1.0)
            intensity = confidence
            
            # Normalize all scores
            total_matches = sum(emotion_scores.values())
            all_emotions = {emotion: matches/total_matches 
                           for emotion, matches in emotion_scores.items()}
        else:
            primary_emotion = "neutral"
            confidence = 0.5
            intensity = 0.5
            all_emotions = {"neutral": 1.0}
        
        return EmotionAnalysisResult(
            primary_emotion=primary_emotion,
            confidence=confidence,
            intensity=intensity,
            all_emotions=all_emotions,
            analysis_method="keywords"
        )
    
    def analyze_emotion_cascade(self, message: str) -> EmotionAnalysisResult:
        """
        Use emotion analysis cascade: RoBERTa → VADER → Keywords
        This mirrors WhisperEngine's actual emotion pipeline
        """
        # Try RoBERTa first (highest quality)
        result = self.analyze_with_roberta(message)
        if result:
            logger.info(f"🎭 Using RoBERTa analysis: {result.primary_emotion} ({result.confidence:.3f})")
            return result
            
        # Fallback to VADER (medium quality)  
        result = self.analyze_with_vader(message)
        if result:
            logger.info(f"🎭 Using VADER analysis: {result.primary_emotion} ({result.confidence:.3f})")
            return result
            
        # Final fallback to keywords (basic quality)
        result = self.analyze_with_keywords(message)
        logger.info(f"🎭 Using keyword analysis: {result.primary_emotion} ({result.confidence:.3f})")
        return result
    
    def demonstrate_emotion_scoring(self, message: str):
        """
        Demonstrate complete emotion scoring process
        """
        print(f"\n🎭 EMOTION SCORING DEMONSTRATION")
        print(f"Message: '{message}'")
        print(f"=" * 60)
        
        # Get emotion analysis
        emotion_result = self.analyze_emotion_cascade(message)
        
        print(f"\n📊 EMOTION ANALYSIS RESULT:")
        print(f"Primary Emotion: {emotion_result.primary_emotion}")
        print(f"Confidence Score: {emotion_result.confidence:.3f}")
        print(f"Intensity Score: {emotion_result.intensity:.3f}")
        print(f"Analysis Method: {emotion_result.analysis_method}")
        
        print(f"\n📈 ALL EMOTIONS DETECTED:")
        for emotion, score in sorted(emotion_result.all_emotions.items(), 
                                   key=lambda x: x[1], reverse=True):
            print(f"  {emotion}: {score:.3f}")
        
        # Show how this gets stored in Qdrant payload
        payload_data = self._create_qdrant_payload(emotion_result, message)
        print(f"\n💾 QDRANT PAYLOAD STORAGE:")
        for key, value in payload_data.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
        
        # Show how emotion embedding is created
        emotion_embedding_text = self._create_emotion_embedding_text(emotion_result, message)
        print(f"\n🔤 EMOTION EMBEDDING TEXT:")
        print(f"  '{emotion_embedding_text}'")
        
        return emotion_result, payload_data, emotion_embedding_text
    
    def _create_qdrant_payload(self, emotion_result: EmotionAnalysisResult, message: str) -> Dict[str, Any]:
        """
        Create Qdrant payload data matching WhisperEngine's storage format
        """
        payload = {
            # Core emotion data
            "primary_emotion": emotion_result.primary_emotion,
            "emotional_intensity": emotion_result.intensity,
            "emotion_confidence": emotion_result.confidence,
            "analysis_method": emotion_result.analysis_method,
            
            # Multi-emotion data (if multiple emotions detected)
            "is_multi_emotion": len(emotion_result.all_emotions) > 1,
            "emotion_count": len(emotion_result.all_emotions),
            "all_emotions_json": str(emotion_result.all_emotions),
        }
        
        # Store top secondary emotions (up to 3)
        if len(emotion_result.all_emotions) > 1:
            primary = emotion_result.primary_emotion
            secondary_emotions = {k: v for k, v in emotion_result.all_emotions.items() if k != primary}
            sorted_secondary = sorted(secondary_emotions.items(), key=lambda x: x[1], reverse=True)[:3]
            
            for i, (emotion, intensity) in enumerate(sorted_secondary):
                payload[f'secondary_emotion_{i+1}'] = emotion
                payload[f'secondary_intensity_{i+1}'] = intensity
        
        # Emotion complexity metrics
        if len(emotion_result.all_emotions) > 1:
            intensities = list(emotion_result.all_emotions.values())
            payload['emotion_variance'] = max(intensities) - min(intensities)
            payload['emotion_dominance'] = emotion_result.intensity / sum(intensities)
        
        return payload
    
    def _create_emotion_embedding_text(self, emotion_result: EmotionAnalysisResult, message: str) -> str:
        """
        Create emotion embedding text using tag prefixing approach
        This is exactly how WhisperEngine creates emotion embeddings
        """
        return f"emotion {emotion_result.primary_emotion}: {message}"
    
    def run_comprehensive_demo(self):
        """Run comprehensive emotion scoring demonstration"""
        print("🎭 WHISPERENGINE EMOTION SCORING & EMBEDDING DEMO")
        print("=" * 70)
        
        # Test messages with different emotional content
        test_messages = [
            "I'm so excited about this new project! It's going to be amazing!",
            "I feel really sad and disappointed about what happened today.",
            "This is absolutely infuriating! I can't believe they did that!",
            "I'm worried about the presentation tomorrow. What if I mess up?",
            "Thank you so much for your help. I really appreciate it!",
            "I'm curious about how this algorithm actually works under the hood.",
            "The weather is nice today.",  # Neutral content
            "Wow, that's completely unexpected! I'm shocked by this news!"
        ]
        
        results = []
        for message in test_messages:
            emotion_result, payload_data, embedding_text = self.demonstrate_emotion_scoring(message)
            results.append({
                'message': message,
                'emotion_result': emotion_result, 
                'payload_data': payload_data,
                'embedding_text': embedding_text
            })
        
        # Summary analysis
        print(f"\n📋 SUMMARY ANALYSIS:")
        print(f"Total Messages Analyzed: {len(results)}")
        
        methods_used = {}
        emotions_detected = {}
        
        for result in results:
            method = result['emotion_result'].analysis_method
            emotion = result['emotion_result'].primary_emotion
            
            methods_used[method] = methods_used.get(method, 0) + 1
            emotions_detected[emotion] = emotions_detected.get(emotion, 0) + 1
        
        print(f"\n🔧 ANALYSIS METHODS USED:")
        for method, count in methods_used.items():
            print(f"  {method}: {count} messages")
        
        print(f"\n😊 EMOTIONS DETECTED:")
        for emotion, count in sorted(emotions_detected.items(), key=lambda x: x[1], reverse=True):
            print(f"  {emotion}: {count} messages")
        
        print(f"\n✅ CONCLUSION:")
        print(f"WhisperEngine DOES use emotion scoring via:")
        print(f"  1. RoBERTa confidence scores (0.0-1.0)")
        print(f"  2. VADER sentiment scores mapped to emotions") 
        print(f"  3. Keyword pattern matching with match density")
        print(f"  4. Emotion scores stored in Qdrant payload metadata")
        print(f"  5. Emotion embeddings created via tag prefixing")
        print(f"  6. Both scores AND embeddings used for intelligent retrieval")

def main():
    """Run the emotion scoring demonstration"""
    demo = EmotionScoringDemo()
    demo.run_comprehensive_demo()

if __name__ == "__main__":
    main()