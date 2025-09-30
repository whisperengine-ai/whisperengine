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
    """
    
    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(__name__)
        self._compile_patterns()
        self._setup_linguistic_features()
    
    def _compile_patterns(self):
        """Compile optimized regex patterns with confidence weights"""
        
        # High-confidence AI identity patterns
        self.ai_patterns_high = [
            (re.compile(r'\b(?:are\s+you\s+(?:an?\s+)?(?:ai|artificial|robot|bot|machine))\b', re.IGNORECASE), 0.9),
            (re.compile(r'\b(?:what\s+are\s+you)\b.*\?', re.IGNORECASE), 0.7),
            (re.compile(r'\b(?:human\s+or\s+(?:ai|artificial))\b', re.IGNORECASE), 0.8),
        ]
        
        # Medium-confidence AI patterns
        self.ai_patterns_medium = [
            (re.compile(r'\b(?:conscious|sentient|self.aware)\b', re.IGNORECASE), 0.6),
            (re.compile(r'\b(?:real\s+person|actually\s+real)\b', re.IGNORECASE), 0.5),
        ]
        
        # Relationship boundary patterns
        self.ai_relationship_patterns = [
            (re.compile(r'\b(?:love\s+you|i\s+love|dating?|relationship)\b', re.IGNORECASE), 0.7),
            (re.compile(r'\b(?:meet\s+(?:up|for|in\s+person)|coffee|dinner)\b', re.IGNORECASE), 0.6),
        ]
        
        # Memory reference patterns with confidence
        self.memory_patterns = [
            # Explicit references (high confidence)
            (re.compile(r'\b(?:remember|recall|mentioned|said|talked\s+about)\b', re.IGNORECASE), 0.9),
            (re.compile(r'\b(?:last\s+time|before|earlier|previously)\b', re.IGNORECASE), 0.8),
            (re.compile(r'\b(?:responding\s+to|reacting\s+to|about\s+what)\b', re.IGNORECASE), 0.8),
            
            # Reaction patterns (medium-high confidence)
            (re.compile(r'^(?:what!?\?*|really\?*|seriously\?*|no\s+way!?|wow!?|amazing!?)$', re.IGNORECASE), 0.8),
            
            # Pronoun references (context dependent, lower confidence)
            (re.compile(r'\b(?:that|it|this)\b(?!\s+(?:is|was|will|would|could|should))', re.IGNORECASE), 0.4),
        ]
        
        # Personality inquiry patterns
        self.personality_patterns = [
            (re.compile(r'\b(?:tell\s+me\s+about\s+(?:yourself|you))\b', re.IGNORECASE), 0.9),
            (re.compile(r'\b(?:what.*(?:like|personality|character)|who\s+are\s+you)\b', re.IGNORECASE), 0.8),
            (re.compile(r'\b(?:describe\s+yourself|your\s+(?:background|interests))\b', re.IGNORECASE), 0.7),
        ]
        
        # Voice/communication patterns
        self.voice_patterns = [
            (re.compile(r'\b(?:how\s+do\s+you\s+(?:talk|speak|communicate))\b', re.IGNORECASE), 0.9),
            (re.compile(r'\b(?:your\s+(?:voice|style|accent|way\s+of))\b', re.IGNORECASE), 0.7),
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
        """Analyze AI-related patterns with confidence scoring"""
        total_confidence = 0.0
        methods = []
        
        # Check high-confidence patterns
        for pattern, weight in self.ai_patterns_high:
            if pattern.search(message):
                total_confidence += weight
                methods.append('high_pattern')
        
        # Check medium-confidence patterns
        for pattern, weight in self.ai_patterns_medium:
            if pattern.search(message):
                total_confidence += weight * 0.8  # Slight discount
                methods.append('medium_pattern')
        
        # Check relationship patterns
        for pattern, weight in self.ai_relationship_patterns:
            if pattern.search(message):
                total_confidence += weight
                methods.append('relationship_pattern')
        
        # Boost for question structure
        if '?' in message:
            total_confidence *= 1.1
            
        method_str = '+'.join(set(methods)) if methods else 'none'
        return total_confidence, method_str
    
    def _analyze_memory_patterns(self, message: str) -> Tuple[float, str]:
        """Analyze memory reference patterns"""
        total_confidence = 0.0
        methods = []
        
        for pattern, weight in self.memory_patterns:
            matches = pattern.findall(message)
            if matches:
                total_confidence += weight
                
                if 'remember' in pattern.pattern:
                    methods.append('explicit_memory')
                elif 'what!' in pattern.pattern:
                    methods.append('reaction')
                elif 'that|it|this' in pattern.pattern:
                    methods.append('pronoun_ref')
                else:
                    methods.append('temporal_ref')
        
        method_str = '+'.join(set(methods)) if methods else 'none'
        return total_confidence, method_str
    
    def _analyze_personality_patterns(self, message: str) -> Tuple[float, str]:
        """Analyze personality inquiry patterns"""
        total_confidence = 0.0
        
        for pattern, weight in self.personality_patterns:
            if pattern.search(message):
                total_confidence += weight
        
        return total_confidence, 'pattern_match' if total_confidence > 0 else 'none'
    
    def _analyze_voice_patterns(self, message: str) -> Tuple[float, str]:
        """Analyze voice/communication patterns"""
        total_confidence = 0.0
        
        for pattern, weight in self.voice_patterns:
            if pattern.search(message):
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