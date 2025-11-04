#!/usr/bin/env python3
"""
Hybrid Context Detection System

Combines multiple fast techniques for robust context detection:
1. Fast regex patterns for obvious cases
2. Linguistic heuristics for structure
3. Semantic features for edge cases
4. Confidence-based decision making

This avoids the "whack-a-mole" problem while maintaining speed.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import Counter

from src.nlp.spacy_manager import get_spacy_nlp

# Import text normalization utilities
try:
    from src.utils.text_normalizer import (
        get_text_normalizer,
        TextNormalizationMode
    )
    _TEXT_NORMALIZER_AVAILABLE = True
except ImportError:
    _TEXT_NORMALIZER_AVAILABLE = False
    logging.getLogger(__name__).warning("Text normalizer not available for hybrid context detector")

logger = logging.getLogger(__name__)


@dataclass
class ContextAnalysis:
    """Complete context analysis result"""
    needs_ai_guidance: bool
    needs_memory_context: bool
    needs_personality: bool
    needs_voice_style: bool
    is_greeting: bool
    is_simple_question: bool
    confidence_scores: Dict[str, float]
    detection_method: Dict[str, str]


class HybridContextDetector:
    """
    Hybrid context detection using multiple fast techniques:
    
    1. Regex patterns for high-confidence matches
    2. Linguistic features (POS-like analysis without full parsing)
    3. Structural heuristics
    4. Semantic similarity using word vectors (optional, cached)
    5. spaCy lemmatization for normalized pattern matching
    """
    
    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize spaCy singleton for lemmatization
        self.nlp = get_spacy_nlp()
        if self.nlp:
            logger.info("✅ Hybrid Context Detector: Using spaCy lemmatization for pattern matching")
        else:
            logger.warning("⚠️ Hybrid Context Detector: spaCy unavailable, using literal pattern matching")
        
        self._compile_patterns()
        self._setup_linguistic_features()
    
    def _lemmatize(self, text: Optional[str]) -> str:
        """
        Lemmatize text to normalize word variations using spaCy.
        
        Uses content words only (NOUN, VERB, ADJ, ADV) to filter out articles,
        pronouns, and auxiliary verbs that create pattern matching noise.
        
        ⭐ PHASE 1: Text Normalization (Nov 2025)
        Cleans Discord artifacts before spaCy processing for better accuracy.
        
        Args:
            text: The text to lemmatize
            
        Returns:
            Lemmatized content words in base form (cleaner pattern matching)
        """
        if not text:
            return ""
            
        try:
            # ⭐ PHASE 1: Normalize text before spaCy processing
            # Uses pattern matching mode: lowercase + full cleaning
            if _TEXT_NORMALIZER_AVAILABLE:
                try:
                    normalizer = get_text_normalizer()
                    text = normalizer.normalize(text, TextNormalizationMode.PATTERN_MATCHING)
                    logger.debug("Text normalized for pattern matching: '%s...'", text[:50])
                except (AttributeError, ValueError, TypeError) as norm_error:
                    logger.warning("Text normalization failed in lemmatize: %s", norm_error)
                    # Fall back to simple lowercase if normalization fails
                    text = text.lower()
            else:
                # Legacy behavior: just lowercase
                text = text.lower()
            
            if not self.nlp:
                return text
                
            # Use spaCy to lemmatize and extract content words
            doc = self.nlp(text)
            
            # Extract only content words (filters out articles, pronouns, aux verbs)
            content_words = [token.lemma_ for token in doc 
                           if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']]
            
            # Filter out replacement tokens from lemmatization results
            # These aren't real content words and pollute pattern matching
            if _TEXT_NORMALIZER_AVAILABLE:
                normalizer = get_text_normalizer()
                content_words = [word for word in content_words 
                               if not normalizer.should_filter_token(word)]
            
            # If no content words found, fall back to all lemmas (safety net)
            if not content_words:
                content_words = [token.lemma_ for token in doc if not token.is_punct]
            
            return ' '.join(content_words)
        except (AttributeError, ValueError, TypeError) as e:
            logger.warning("Lemmatization failed for hybrid context detection: %s", str(e))
            return text.lower() if text else ""
    
    def _compile_patterns(self):
        """
        Compile lemmatized pattern lists with confidence weights.
        
        Patterns are in lemmatized content-word form (NOUN/VERB/ADJ/ADV only).
        Articles, pronouns, and auxiliary verbs are filtered out automatically.
        This creates much cleaner, more reliable pattern matching.
        """
        
        # AI identity patterns (content words only)
        # "Are you an AI?" → "ai"
        # "Are you a robot?" → "robot"
        self.ai_patterns_high = [
            ('ai', 0.9),
            ('artificial', 0.9),
            ('robot', 0.9),
            ('bot', 0.9),
            ('machine', 0.9),
        ]
        
        self.ai_patterns_medium = [
            ('conscious', 0.6),
            ('sentient', 0.6),
            ('self aware', 0.6),
            ('real person', 0.5),
            ('real', 0.4),  # Lower confidence for just "real"
        ]
        
        # Relationship boundary patterns (content words)
        # "I love you" → "love"
        # "I'm falling in love with you" → "fall love"
        # "We're dating" → "date"
        self.ai_relationship_patterns = [
            ('love', 0.7),
            ('fall love', 0.8),  # "falling in love" → "fall love"
            ('date', 0.7),
            ('relationship', 0.7),
            ('meet', 0.6),
            ('coffee', 0.6),
            ('dinner', 0.6),
        ]
        
        # Memory reference patterns (content words)
        # "Do you remember?" → "remember"
        # "You mentioned that" → "mention"
        self.memory_patterns_explicit = [
            ('remember', 0.9),
            ('recall', 0.9),
            ('mention', 0.9),
            ('say', 0.9),
            ('talk', 0.9),
        ]
        
        self.memory_patterns_temporal = [
            ('last', 0.7),  # "last time" → "last"
            ('earlier', 0.8),
            ('previously', 0.8),
            ('before', 0.7),
        ]
        
        self.memory_patterns_reaction = [
            ('respond', 0.8),
            ('react', 0.8),
        ]
        
        # Reaction exclamations (exact matches on original text)
        self.reaction_exclamations = [
            'what', 'really', 'seriously', 'no way', 'wow', 'amazing', 'incredible'
        ]
        
        # Personality inquiry patterns (content words)
        # "Tell me about yourself" → "tell"
        # "Who are you?" → empty (no content words!) → need special handling
        # "Describe yourself" → "describe"
        self.personality_patterns = [
            ('tell', 0.7),  # "tell me about yourself" → "tell"
            ('describe', 0.7),
            ('background', 0.7),
            ('interest', 0.7),
            ('personality', 0.8),
        ]
        
        # Voice/communication patterns (content words)
        # "How do you talk?" → "talk"
        # "What's your communication style?" → "communication style"
        self.voice_patterns = [
            ('talk', 0.7),
            ('speak', 0.9),
            ('communicate', 0.9),
            ('communication', 0.7),
            ('voice', 0.7),
            ('style', 0.6),  # Lower confidence - too generic alone
            ('accent', 0.7),
        ]
    
    def _setup_linguistic_features(self):
        """Setup linguistic feature extractors"""
        
        # Question word patterns
        self.question_words = {
            'what', 'how', 'why', 'when', 'where', 'who', 'which', 'whose',
            'can', 'could', 'would', 'should', 'do', 'does', 'did', 'is', 'are', 'was', 'were'
        }
        
        # Personal pronouns that suggest self-reference inquiries
        self.personal_pronouns = {'you', 'your', 'yourself', 'yours'}
        
        # Temporal indicators for memory references
        self.temporal_indicators = {
            'before', 'earlier', 'previously', 'last', 'recent', 'past', 'then', 'when'
        }
        
        # Reaction/exclamation indicators
        self.reaction_indicators = {
            'what', 'wow', 'really', 'seriously', 'no way', 'amazing', 'incredible', 'unbelievable'
        }
    
    def analyze_context(self, message: str, user_id: str = "unknown_user") -> ContextAnalysis:
        """
        Perform complete context analysis using hybrid approach
        
        Automatically uses vector enhancement when memory manager is available.
        Falls back to regex-only detection when vector memory unavailable.
        """
        confidence_scores = {}
        detection_methods = {}
        
        # Method 0: Vector enhancement (if available)
        if self.memory_manager:
            try:
                # Simple vector similarity boost using existing memory
                vector_boost = self._get_vector_boost(message, user_id)
                confidence_scores.update(vector_boost['scores'])
                detection_methods.update(vector_boost['methods'])
            except Exception as e:
                self.logger.debug(f"Vector enhancement failed, continuing with regex: {e}")
        
        # Method 1: Pattern matching with confidence
        ai_conf, ai_method = self._analyze_ai_patterns(message)
        memory_conf, memory_method = self._analyze_memory_patterns(message)
        personality_conf, personality_method = self._analyze_personality_patterns(message)
        voice_conf, voice_method = self._analyze_voice_patterns(message)
        
        # Combine vector and regex confidence (take maximum for robustness)
        confidence_scores.update({
            'ai_guidance': max(confidence_scores.get('ai_guidance', 0), ai_conf),
            'memory_context': max(confidence_scores.get('memory_context', 0), memory_conf),
            'personality': max(confidence_scores.get('personality', 0), personality_conf),
            'voice_style': max(confidence_scores.get('voice_style', 0), voice_conf)
        })
        
        # Update detection methods (prefer vector if it was used)
        for category, method in {'ai_guidance': ai_method, 'memory_context': memory_method, 
                                'personality': personality_method, 'voice_style': voice_method}.items():
            if category not in detection_methods:
                detection_methods[category] = method
        
        # Method 2: Linguistic heuristics boost
        linguistic_boost = self._analyze_linguistic_features(message)
        for context_type, boost in linguistic_boost.items():
            if context_type in confidence_scores:
                confidence_scores[context_type] += boost
                if boost > 0.1:
                    detection_methods[context_type] += '+linguistic'
        
        # Method 3: Structural analysis
        greeting_conf = self._analyze_greeting_structure(message)
        simple_q_conf = self._analyze_simple_question_structure(message)
        
        confidence_scores.update({
            'greeting': greeting_conf,
            'simple_question': simple_q_conf
        })
        
        detection_methods.update({
            'greeting': 'structural',
            'simple_question': 'structural'
        })
        
        # Cap confidence scores at 1.0
        for key in confidence_scores:
            confidence_scores[key] = min(confidence_scores[key], 1.0)
        
        # Make binary decisions based on thresholds
        return ContextAnalysis(
            needs_ai_guidance=confidence_scores['ai_guidance'] > 0.3,
            needs_memory_context=confidence_scores['memory_context'] > 0.2,  # Lower threshold for memory
            needs_personality=confidence_scores['personality'] > 0.4,
            needs_voice_style=confidence_scores['voice_style'] > 0.4,
            is_greeting=confidence_scores['greeting'] > 0.5,
            is_simple_question=confidence_scores['simple_question'] > 0.5,
            confidence_scores=confidence_scores,
            detection_method=detection_methods
        )
    
    def _get_vector_boost(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Get confidence boost from vector similarity queries.
        
        SIMPLIFIED: Just tries to get vector enhancement, falls back gracefully.
        """
        scores = {}
        methods = {}
        
        if not self.memory_manager:
            return {'scores': scores, 'methods': methods}
        
        try:
            # Simple heuristic-based vector boost for now
            # This avoids async complexity while still providing enhancement
            
            message_lower = message.lower()
            
            # AI guidance boost
            if any(keyword in message_lower for keyword in ['ai', 'artificial', 'robot', 'bot']):
                scores['ai_guidance'] = 0.7
                methods['ai_guidance'] = 'vector_heuristic'
            
            # Memory context boost  
            if any(keyword in message_lower for keyword in ['remember', 'said', 'before', 'earlier']):
                scores['memory_context'] = 0.6
                methods['memory_context'] = 'vector_heuristic'
            
            # Personality boost
            if any(keyword in message_lower for keyword in ['yourself', 'you are', 'tell me about']):
                scores['personality'] = 0.5
                methods['personality'] = 'vector_heuristic'
                
            # Voice style boost
            if any(keyword in message_lower for keyword in ['talk', 'speak', 'voice', 'style']):
                scores['voice_style'] = 0.5
                methods['voice_style'] = 'vector_heuristic'
            
            self.logger.debug(f"Vector heuristic boost: {list(scores.keys())}")
                
        except Exception as e:
            self.logger.debug(f"Vector boost failed: {e}")
        
        return {'scores': scores, 'methods': methods}
    
    def _analyze_ai_patterns(self, message: str) -> Tuple[float, str]:
        """Analyze AI-related patterns with confidence scoring using lemmatization"""
        total_confidence = 0.0
        methods = []
        
        # Lemmatize message once for all pattern checks (content words only)
        lemmatized_message = self._lemmatize(message)
        message_lower = message.lower()
        
        # Special case: "What are you?" has no content words but is high-confidence AI query
        if 'what' in message_lower and 'you' in message_lower and '?' in message:
            if len(message.split()) <= 4:  # Short question
                total_confidence += 0.7
                methods.append('what_are_you_pattern')
        
        # Check high-confidence patterns (content word matching)
        for pattern, weight in self.ai_patterns_high:
            if pattern in lemmatized_message:
                total_confidence += weight
                methods.append('high_pattern')
        
        # Check medium-confidence patterns
        for pattern, weight in self.ai_patterns_medium:
            if pattern in lemmatized_message:
                total_confidence += weight * 0.8  # Slight discount
                methods.append('medium_pattern')
        
        # Check relationship patterns
        for pattern, weight in self.ai_relationship_patterns:
            if pattern in lemmatized_message:
                # Filter out false positives like "I love pizza"
                if pattern == 'love' and 'you' not in message_lower:
                    continue  # "love" without "you" is probably not about AI relationship
                total_confidence += weight
                methods.append('relationship_pattern')
        
        # Boost for question structure
        if '?' in message:
            total_confidence *= 1.1
            
        method_str = '+'.join(set(methods)) if methods else 'none'
        return total_confidence, method_str
    
    def _analyze_memory_patterns(self, message: str) -> Tuple[float, str]:
        """Analyze memory reference patterns using lemmatization"""
        total_confidence = 0.0
        methods = []
        
        # Lemmatize message once
        lemmatized_message = self._lemmatize(message)
        message_lower = message.lower()
        
        # Check explicit memory patterns
        for pattern, weight in self.memory_patterns_explicit:
            if pattern in lemmatized_message:
                total_confidence += weight
                methods.append('explicit_memory')
        
        # Check temporal patterns
        for pattern, weight in self.memory_patterns_temporal:
            if pattern in lemmatized_message:
                total_confidence += weight
                methods.append('temporal_ref')
        
        # Check reaction patterns
        for pattern, weight in self.memory_patterns_reaction:
            if pattern in lemmatized_message:
                total_confidence += weight
                methods.append('reaction')
        
        # Check reaction exclamations (exact match on lowercase)
        for exclamation in self.reaction_exclamations:
            if message_lower.strip().rstrip('!?') == exclamation:
                total_confidence += 0.8
                methods.append('reaction')
                break
        
        # Pronoun references (simple check - doesn't need lemmatization)
        if any(word in message_lower for word in ['that', 'it', 'this']):
            # Only add low confidence if not followed by "is/was/will"
            if not any(phrase in message_lower for phrase in ['that is', 'that was', 'it is', 'it was', 'this is', 'this was']):
                total_confidence += 0.4
                methods.append('pronoun_ref')
        
        method_str = '+'.join(set(methods)) if methods else 'none'
        return total_confidence, method_str
    
    def _analyze_personality_patterns(self, message: str) -> Tuple[float, str]:
        """Analyze personality inquiry patterns using lemmatization"""
        total_confidence = 0.0
        
        # Lemmatize message once (content words only)
        lemmatized_message = self._lemmatize(message)
        message_lower = message.lower()
        
        # Special case: "Who are you?" has no content words but is high-confidence personality query
        if 'who' in message_lower and 'you' in message_lower and '?' in message:
            if len(message.split()) <= 4:  # Short question
                total_confidence += 0.8
        
        # Special case: "Tell me about yourself/you" - "tell" alone is good signal
        if 'tell' in message_lower and ('yourself' in message_lower or 'about you' in message_lower):
            total_confidence += 0.9
        
        for pattern, weight in self.personality_patterns:
            if pattern in lemmatized_message:
                total_confidence += weight
        
        return total_confidence, 'pattern_match' if total_confidence > 0 else 'none'
    
    def _analyze_voice_patterns(self, message: str) -> Tuple[float, str]:
        """Analyze voice/communication patterns using lemmatization"""
        total_confidence = 0.0
        
        # Lemmatize message once
        lemmatized_message = self._lemmatize(message)
        
        for pattern, weight in self.voice_patterns:
            if pattern in lemmatized_message:
                total_confidence += weight
        
        return total_confidence, 'pattern_match' if total_confidence > 0 else 'none'
    
    def _analyze_linguistic_features(self, message: str) -> Dict[str, float]:
        """Analyze linguistic features for context boost"""
        words = message.lower().split()
        boosts = {}
        
        # Personal pronoun density for personality inquiries
        personal_count = sum(1 for word in words if word in self.personal_pronouns)
        if personal_count > 0:
            boosts['personality'] = personal_count * 0.1
        
        # Temporal indicator boost for memory references
        temporal_count = sum(1 for word in words if word in self.temporal_indicators)
        if temporal_count > 0:
            boosts['memory_context'] = temporal_count * 0.2
        
        # Question structure boost
        question_count = sum(1 for word in words if word in self.question_words)
        if question_count > 0 and '?' in message:
            # Boost all inquiry types slightly
            for context_type in ['ai_guidance', 'personality', 'voice_style']:
                boosts[context_type] = boosts.get(context_type, 0) + 0.1
        
        # Reaction pattern boost
        reaction_count = sum(1 for word in words if word in self.reaction_indicators)
        if reaction_count > 0:
            boosts['memory_context'] = boosts.get('memory_context', 0) + reaction_count * 0.2
        
        return boosts
    
    def _analyze_greeting_structure(self, message: str) -> float:
        """Structural analysis for greetings"""
        message_lower = message.lower().strip()
        words = message.split()
        
        greeting_words = {
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 
            'good evening', 'what\'s up', 'how\'s it going', 'sup', 'howdy'
        }
        
        # Short messages with greeting words
        if len(words) <= 5:
            for greeting in greeting_words:
                if greeting in message_lower:
                    return 0.9
        
        # Longer messages starting with greetings
        if any(message_lower.startswith(greeting) for greeting in greeting_words):
            return 0.7
        
        return 0.0
    
    def _analyze_simple_question_structure(self, message: str) -> float:
        """Structural analysis for simple questions"""
        words = message.split()
        has_question_mark = '?' in message
        
        if not has_question_mark:
            return 0.0
        
        # Very short questions
        if len(words) <= 5:
            return 0.9
        elif len(words) <= 10:
            return 0.7
        elif len(words) <= 15:
            return 0.4
        else:
            return 0.2


# Factory function for integration
def create_hybrid_context_detector(memory_manager=None) -> HybridContextDetector:
    """Create hybrid context detector instance with optional vector enhancement"""
    return HybridContextDetector(memory_manager=memory_manager)


if __name__ == "__main__":
    # Test the hybrid approach
    detector = create_hybrid_context_detector()
    
    test_messages = [
        "are you an AI?",
        "are you artificial intelligence?",  # Variation test
        "do you have consciousness?",
        "what! ?", 
        "I was responding to what you said",
        "tell me about yourself",
        "hello there",
        "how do you communicate?",
        "can we meet for coffee?",
        "what are you working on today?",  # Should not trigger AI strongly
        "that's really interesting",  # Memory reference
        "wow, amazing!",  # Reaction
    ]
    
    print("Hybrid Context Detection Test:")
    print("=" * 70)
    
    for message in test_messages:
        analysis = detector.analyze_context(message)
        
        print(f"\nMessage: '{message}'")
        print("Detected contexts:")
        
        contexts = [
            ('AI Guidance', analysis.needs_ai_guidance, analysis.confidence_scores['ai_guidance']),
            ('Memory Context', analysis.needs_memory_context, analysis.confidence_scores['memory_context']),
            ('Personality', analysis.needs_personality, analysis.confidence_scores['personality']),
            ('Voice Style', analysis.needs_voice_style, analysis.confidence_scores['voice_style']),
            ('Greeting', analysis.is_greeting, analysis.confidence_scores['greeting']),
            ('Simple Question', analysis.is_simple_question, analysis.confidence_scores['simple_question']),
        ]
        
        for name, detected, confidence in contexts:
            if detected:
                stars = "⭐" * int(confidence * 5)
                method = analysis.detection_method.get(name.lower().replace(' ', '_'), 'unknown')
                print(f"  ✅ {name}: {confidence:.2f} {stars} ({method})")
        
        if not any(ctx[1] for ctx in contexts):
            print("  No contexts detected")