#!/usr/bin/env python3
"""
CPU-Based Context Detection with Fast Models

Explores lightweight CPU models that could enhance context detection:
1. VADER sentiment (already in use)
2. spaCy lightweight models
3. TextBlob for quick NLP features
4. scikit-learn TF-IDF + small classifiers

Performance target: <10ms per message
"""

import time
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelBasedAnalysis:
    """Results from model-based context analysis"""
    context_predictions: Dict[str, float]
    confidence: float
    processing_time_ms: float
    model_used: str
    fallback_used: bool


class CPUContextAnalyzer:
    """
    CPU-based context detection using lightweight models
    
    Models evaluated for speed vs accuracy:
    1. spaCy (en_core_web_sm): ~5-15ms, good accuracy
    2. TextBlob: ~2-8ms, moderate accuracy  
    3. VADER + keyword enhancement: ~1-3ms, good for sentiment
    4. scikit-learn vectorizer + tiny classifier: ~2-5ms, trainable
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models_available = {}
        self.performance_stats = {}
        
        # Initialize available models with graceful fallbacks
        self._initialize_spacy()
        self._initialize_textblob()
        self._initialize_vader()
        self._initialize_sklearn_classifier()
    
    def _initialize_spacy(self):
        """Initialize spaCy lightweight model"""
        try:
            import spacy
            # Try lightweight model first
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.models_available['spacy'] = True
                logger.info("✅ spaCy en_core_web_sm loaded (~50MB)")
            except OSError:
                # Fallback to even smaller model if available
                try:
                    self.nlp = spacy.load("en_core_web_trf")  # Transformer-based but still small
                    self.models_available['spacy'] = True
                    logger.info("✅ spaCy transformer model loaded")
                except OSError:
                    self.models_available['spacy'] = False
                    logger.warning("⚠️ No spaCy models found - install with: python -m spacy download en_core_web_sm")
        except ImportError:
            self.models_available['spacy'] = False
            logger.warning("⚠️ spaCy not installed")
    
    def _initialize_textblob(self):
        """Initialize TextBlob"""
        try:
            from textblob import TextBlob
            # Test basic functionality
            test_blob = TextBlob("test")
            _ = test_blob.sentiment
            self.models_available['textblob'] = True
            logger.info("✅ TextBlob available")
        except (ImportError, Exception) as e:
            self.models_available['textblob'] = False
            logger.warning("⚠️ TextBlob unavailable: %s", e)
    
    def _initialize_vader(self):
        """Initialize VADER (reuse from emotion analyzer)"""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.vader_analyzer = SentimentIntensityAnalyzer()
            self.models_available['vader'] = True
            logger.info("✅ VADER sentiment available")
        except ImportError:
            self.models_available['vader'] = False
            logger.warning("⚠️ VADER unavailable")
    
    def _initialize_sklearn_classifier(self):
        """Initialize a tiny scikit-learn classifier for context detection"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            import pickle
            import os
            
            # Check if we have a pre-trained model
            model_path = "models/context_classifier.pkl"
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.sklearn_model = pickle.load(f)
                self.models_available['sklearn'] = True
                logger.info("✅ Pre-trained context classifier loaded")
            else:
                # Create a simple model with basic training data
                self.sklearn_model = self._create_simple_classifier()
                self.models_available['sklearn'] = True
                logger.info("✅ Simple context classifier created")
                
        except ImportError:
            self.models_available['sklearn'] = False
            logger.warning("⚠️ scikit-learn unavailable")
    
    def _create_simple_classifier(self):
        """Create a simple context classifier with basic training data"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        
        # Basic training data for context types
        training_data = [
            # AI identity questions
            ("are you an AI?", "ai_inquiry"),
            ("are you artificial?", "ai_inquiry"),
            ("what are you?", "ai_inquiry"),
            ("are you real?", "ai_inquiry"),
            ("do you have consciousness?", "ai_inquiry"),
            ("are you human?", "ai_inquiry"),
            
            # Memory references
            ("remember what you said", "memory_reference"),
            ("that's interesting", "memory_reference"),
            ("what!", "memory_reference"),
            ("responding to your message", "memory_reference"),
            ("about that story", "memory_reference"),
            ("like you mentioned", "memory_reference"),
            
            # Personality inquiries
            ("tell me about yourself", "personality_inquiry"),
            ("what are you like?", "personality_inquiry"),
            ("describe your personality", "personality_inquiry"),
            ("who are you?", "personality_inquiry"),
            
            # Voice/communication
            ("how do you talk?", "voice_inquiry"),
            ("your communication style", "voice_inquiry"),
            ("how do you speak?", "voice_inquiry"),
            
            # Greetings
            ("hello there", "greeting"),
            ("good morning", "greeting"),
            ("hi", "greeting"),
            
            # Neutral/other
            ("what's the weather?", "neutral"),
            ("tell me a joke", "neutral"),
            ("how to cook pasta", "neutral"),
        ]
        
        texts, labels = zip(*training_data)
        
        # Create a simple pipeline
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
            ('classifier', LogisticRegression(random_state=42))
        ])
        
        pipeline.fit(texts, labels)
        return pipeline
    
    def analyze_with_models(self, message: str) -> ModelBasedAnalysis:
        """
        Analyze context using available CPU models
        
        Strategy: Try fastest accurate model first, fallback to simpler ones
        """
        start_time = time.time()
        
        predictions = {}
        confidence = 0.0
        model_used = "none"
        fallback_used = False
        
        # Strategy 1: Try spaCy (most comprehensive, ~5-15ms)
        if self.models_available.get('spacy'):
            try:
                spacy_results = self._analyze_with_spacy(message)
                predictions.update(spacy_results)
                confidence = max(confidence, max(spacy_results.values()) if spacy_results else 0)
                model_used = "spacy"
            except Exception as e:
                logger.debug("spaCy analysis failed: %s", e)
                fallback_used = True
        
        # Strategy 2: Enhance with TextBlob sentiment (fast, ~2-8ms)
        if self.models_available.get('textblob'):
            try:
                textblob_results = self._analyze_with_textblob(message)
                for key, value in textblob_results.items():
                    predictions[key] = predictions.get(key, 0) + value * 0.3  # Weighted boost
                confidence = max(confidence, max(textblob_results.values()) if textblob_results else 0)
                if model_used == "none":
                    model_used = "textblob"
                else:
                    model_used += "+textblob"
            except Exception as e:
                logger.debug("TextBlob analysis failed: %s", e)
                fallback_used = True
        
        # Strategy 3: VADER for emotional context (very fast, ~1-3ms)
        if self.models_available.get('vader'):
            try:
                vader_results = self._analyze_with_vader_context(message)
                for key, value in vader_results.items():
                    predictions[key] = predictions.get(key, 0) + value * 0.2  # Light boost
                if model_used == "none":
                    model_used = "vader"
                elif "vader" not in model_used:
                    model_used += "+vader"
            except Exception as e:
                logger.debug("VADER analysis failed: %s", e)
                fallback_used = True
        
        # Strategy 4: Tiny sklearn classifier (fast, ~2-5ms)
        if self.models_available.get('sklearn'):
            try:
                sklearn_results = self._analyze_with_sklearn(message)
                for key, value in sklearn_results.items():
                    predictions[key] = predictions.get(key, 0) + value * 0.4  # Moderate boost
                confidence = max(confidence, max(sklearn_results.values()) if sklearn_results else 0)
                if model_used == "none":
                    model_used = "sklearn"
                elif "sklearn" not in model_used:
                    model_used += "+sklearn"
            except Exception as e:
                logger.debug("sklearn analysis failed: %s", e)
                fallback_used = True
        
        processing_time = (time.time() - start_time) * 1000
        
        # If no models worked, return empty predictions
        if model_used == "none":
            fallback_used = True
            logger.warning("All CPU models failed for context detection")
        
        return ModelBasedAnalysis(
            context_predictions=predictions,
            confidence=min(confidence, 1.0),
            processing_time_ms=processing_time,
            model_used=model_used,
            fallback_used=fallback_used
        )
    
    def _analyze_with_spacy(self, message: str) -> Dict[str, float]:
        """Use spaCy for comprehensive linguistic analysis"""
        doc = self.nlp(message)
        
        predictions = {}
        
        # AI inquiry detection using POS and entities
        question_words = ['what', 'who', 'are', 'do']
        ai_words = ['ai', 'artificial', 'robot', 'human']
        
        has_question = any(token.text.lower() in question_words for token in doc)
        has_ai_terms = any(token.text.lower() in ai_words for token in doc)
        is_question = message.endswith('?')
        
        if has_question and has_ai_terms and is_question:
            predictions['ai_inquiry'] = 0.8
        
        # Memory reference detection using dependency parsing
        pronouns = [token for token in doc if token.pos_ == 'PRON']
        past_verbs = [token for token in doc if token.tag_ in ['VBD', 'VBN']]
        
        if pronouns and ('that' in message.lower() or 'it' in message.lower()):
            predictions['memory_reference'] = 0.6
        
        if past_verbs or any(word in message.lower() for word in ['remember', 'said', 'mentioned']):
            predictions['memory_reference'] = predictions.get('memory_reference', 0) + 0.4
        
        # Personality inquiry using dependency patterns
        personal_pronouns = [token for token in doc if token.text.lower() in ['you', 'your']]
        if personal_pronouns and has_question:
            predictions['personality_inquiry'] = 0.7
        
        return predictions
    
    def _analyze_with_textblob(self, message: str) -> Dict[str, float]:
        """Use TextBlob for sentiment and basic NLP"""
        from textblob import TextBlob
        
        blob = TextBlob(message)
        sentiment = blob.sentiment
        
        predictions = {}
        
        # Use sentiment polarity for context clues
        if sentiment.polarity > 0.5:  # Very positive
            predictions['memory_reference'] = 0.3  # Might be reacting positively
        elif sentiment.polarity < -0.3:  # Negative
            predictions['ai_inquiry'] = 0.2  # Might be questioning/skeptical
        
        # Use sentiment subjectivity
        if sentiment.subjectivity > 0.7:  # Very subjective
            predictions['personality_inquiry'] = 0.4  # Personal questions tend to be subjective
        
        return predictions
    
    def _analyze_with_vader_context(self, message: str) -> Dict[str, float]:
        """Use VADER sentiment for context hints"""
        scores = self.vader_analyzer.polarity_scores(message)
        
        predictions = {}
        
        # High compound score might indicate excitement (reaction)
        if scores['compound'] > 0.6:
            predictions['memory_reference'] = 0.4
        
        # Question + neutral/negative might be AI inquiry
        if '?' in message and scores['compound'] < 0.1:
            predictions['ai_inquiry'] = 0.3
        
        return predictions
    
    def _analyze_with_sklearn(self, message: str) -> Dict[str, float]:
        """Use tiny sklearn classifier"""
        try:
            # Get prediction probabilities
            proba = self.sklearn_model.predict_proba([message])[0]
            classes = self.sklearn_model.classes_
            
            predictions = {}
            for class_name, prob in zip(classes, proba):
                if class_name != 'neutral':
                    predictions[class_name] = prob
            
            return predictions
        except Exception as e:
            logger.debug("sklearn prediction failed: %s", e)
            return {}


def benchmark_cpu_models():
    """Benchmark different CPU model approaches"""
    analyzer = CPUContextAnalyzer()
    
    test_messages = [
        "are you an AI?",
        "that's really interesting!",
        "tell me about yourself",
        "how do you communicate?",
        "hello there",
        "what's the weather like?",
    ]
    
    print("CPU Model Context Detection Benchmark:")
    print("=" * 60)
    
    total_times = []
    
    for message in test_messages:
        result = analyzer.analyze_with_models(message)
        total_times.append(result.processing_time_ms)
        
        print(f"\nMessage: '{message}'")
        print(f"Model(s): {result.model_used}")
        print(f"Time: {result.processing_time_ms:.2f}ms")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Fallback used: {result.fallback_used}")
        
        if result.context_predictions:
            print("Predictions:")
            for context, score in result.context_predictions.items():
                if score > 0.1:
                    stars = "⭐" * int(score * 5)
                    print(f"  {context}: {score:.2f} {stars}")
    
    avg_time = sum(total_times) / len(total_times)
    print(f"\n{'='*60}")
    print(f"Average processing time: {avg_time:.2f}ms")
    print(f"Available models: {list(analyzer.models_available.keys())}")


if __name__ == "__main__":
    benchmark_cpu_models()