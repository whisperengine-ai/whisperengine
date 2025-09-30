#!/usr/bin/env python3
"""
Enhanced Context Detection - Moving Beyond Keyword Whack-a-mole

This explores different approaches to context detection that are more robust
than simple keyword matching while maintaining speed.
"""

import re
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContextSignal:
    """Represents a context detection signal with confidence"""
    context_type: str
    confidence: float
    evidence: str
    method: str  # 'regex', 'heuristic', 'pattern', 'semantic'


class AdvancedContextDetector:
    """
    Advanced context detection using multiple techniques:
    1. Semantic patterns (regex with intent)
    2. Structural analysis (message length, punctuation, etc.)
    3. Conversational heuristics (question types, reaction patterns)
    4. Fast linguistic features
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for different context types"""
        
        # AI Identity patterns - much more comprehensive
        self.ai_patterns = [
            # Direct AI questions
            re.compile(r'\b(are\s+you\s+(?:an?\s+)?(?:ai|artificial|robot|bot|machine))\b', re.IGNORECASE),
            re.compile(r'\b(what\s+are\s+you\b.*(?:ai|artificial|real|human))', re.IGNORECASE),
            re.compile(r'\b(human\s+or\s+(?:ai|artificial|robot))\b', re.IGNORECASE),
            
            # Consciousness/sentience
            re.compile(r'\b(conscious|sentient|self.aware|real\s+person)\b', re.IGNORECASE),
            
            # Relationship boundaries
            re.compile(r'\b(love\s+you|date\s+(?:me|you)|(?:boy|girl)friend|relationship)\b', re.IGNORECASE),
            re.compile(r'\b(meet\s+(?:up|for|in\s+person)|coffee|dinner|hang\s+out)\b', re.IGNORECASE),
        ]
        
        # Memory/Reference patterns
        self.memory_patterns = [
            # Explicit references
            re.compile(r'\b(remember|recall|mentioned|said|talked\s+about)\b', re.IGNORECASE),
            re.compile(r'\b(last\s+time|before|earlier|previously)\b', re.IGNORECASE),
            
            # Implicit references (harder to catch with keywords)
            re.compile(r'\b(that|it|this|your\s+\w+)\b(?!\s+(?:is|was|will))', re.IGNORECASE),
            re.compile(r'^(what!?\?*|really\?*|seriously\?*|wow|amazing|incredible)$', re.IGNORECASE),
            
            # Response/reaction patterns
            re.compile(r'\b(responding\s+to|reacting\s+to|about\s+(?:what|that))\b', re.IGNORECASE),
        ]
        
        # Personality inquiry patterns  
        self.personality_patterns = [
            re.compile(r'\b(how\s+are\s+you|tell\s+me\s+about\s+(?:yourself|you))\b', re.IGNORECASE),
            re.compile(r'\b(what.*(?:like|personality|character)|who\s+are\s+you)\b', re.IGNORECASE),
            re.compile(r'\b(describe\s+yourself|your\s+(?:background|interests|hobbies))\b', re.IGNORECASE),
        ]
        
        # Voice/communication patterns
        self.voice_patterns = [
            re.compile(r'\b(how\s+do\s+you\s+(?:talk|speak|communicate))\b', re.IGNORECASE),
            re.compile(r'\b(your\s+(?:voice|style|accent|way\s+of))\b', re.IGNORECASE),
        ]
    
    def detect_context_needs(self, message: str) -> Dict[str, ContextSignal]:
        """
        Detect what context types are needed using multiple methods
        
        Returns dict of context_type -> ContextSignal
        """
        results = {}
        
        # Method 1: Pattern matching with confidence scoring
        ai_signal = self._detect_ai_inquiry(message)
        if ai_signal.confidence > 0.1:
            results['needs_ai_guidance'] = ai_signal
            
        memory_signal = self._detect_memory_reference(message)
        if memory_signal.confidence > 0.1:
            results['needs_memory_context'] = memory_signal
            
        personality_signal = self._detect_personality_inquiry(message)
        if personality_signal.confidence > 0.1:
            results['needs_personality'] = personality_signal
            
        voice_signal = self._detect_voice_inquiry(message)
        if voice_signal.confidence > 0.1:
            results['needs_voice_style'] = voice_signal
        
        # Method 2: Structural heuristics
        greeting_signal = self._detect_greeting_heuristic(message)
        if greeting_signal.confidence > 0.5:
            results['is_greeting'] = greeting_signal
            
        simple_signal = self._detect_simple_question_heuristic(message)
        if simple_signal.confidence > 0.5:
            results['is_simple_question'] = simple_signal
        
        return results
    
    def _detect_ai_inquiry(self, message: str) -> ContextSignal:
        """Detect AI identity questions with confidence scoring"""
        confidence = 0.0
        evidence = []
        
        for pattern in self.ai_patterns:
            matches = pattern.findall(message)
            if matches:
                # Different patterns have different confidence weights
                if 'are you' in pattern.pattern.lower():
                    confidence += 0.8  # Direct questions are high confidence
                elif 'what are you' in pattern.pattern.lower():
                    confidence += 0.7
                elif 'conscious' in pattern.pattern.lower():
                    confidence += 0.6
                elif 'love' in pattern.pattern.lower():
                    confidence += 0.5  # Relationship questions
                else:
                    confidence += 0.4
                    
                evidence.extend(matches)
        
        # Boost confidence for question marks
        if '?' in message:
            confidence *= 1.2
            
        # Reduce confidence for longer messages (less likely to be direct AI questions)
        word_count = len(message.split())
        if word_count > 15:
            confidence *= 0.7
            
        return ContextSignal(
            context_type='ai_guidance',
            confidence=min(confidence, 1.0),
            evidence=', '.join(evidence) if evidence else '',
            method='regex_pattern'
        )
    
    def _detect_memory_reference(self, message: str) -> ContextSignal:
        """Detect references to previous conversation"""
        confidence = 0.0
        evidence = []
        
        for pattern in self.memory_patterns:
            matches = pattern.findall(message)
            if matches:
                # Weight different types of references
                if 'remember' in pattern.pattern.lower():
                    confidence += 0.9  # Explicit memory references
                elif 'that|it|this' in pattern.pattern.lower():
                    confidence += 0.6  # Implicit references (context dependent)
                elif 'what!' in pattern.pattern.lower():
                    confidence += 0.8  # Strong reaction patterns
                elif 'responding' in pattern.pattern.lower():
                    confidence += 0.7  # Explicit response references
                else:
                    confidence += 0.5
                    
                evidence.extend(matches)
        
        # Boost for very short messages (likely reactions)
        word_count = len(message.split())
        if word_count <= 3:
            confidence += 0.3
            
        # Check for pronoun density (indicates reference to previous context)
        pronouns = len(re.findall(r'\b(that|it|this|they|them|those)\b', message, re.IGNORECASE))
        if pronouns > 0:
            confidence += pronouns * 0.2
            
        return ContextSignal(
            context_type='memory_context',
            confidence=min(confidence, 1.0),
            evidence=', '.join(evidence) if evidence else '',
            method='regex_pattern'
        )
    
    def _detect_personality_inquiry(self, message: str) -> ContextSignal:
        """Detect personality-related questions"""
        confidence = 0.0
        evidence = []
        
        for pattern in self.personality_patterns:
            matches = pattern.findall(message)
            if matches:
                confidence += 0.7
                evidence.extend(matches)
        
        # Check for personal question indicators
        personal_words = len(re.findall(r'\b(you|your|yourself|personality|character|like)\b', message, re.IGNORECASE))
        confidence += personal_words * 0.1
        
        return ContextSignal(
            context_type='personality',
            confidence=min(confidence, 1.0),
            evidence=', '.join(evidence) if evidence else '',
            method='regex_pattern'
        )
    
    def _detect_voice_inquiry(self, message: str) -> ContextSignal:
        """Detect voice/communication style questions"""
        confidence = 0.0
        evidence = []
        
        for pattern in self.voice_patterns:
            matches = pattern.findall(message)
            if matches:
                confidence += 0.8
                evidence.extend(matches)
        
        return ContextSignal(
            context_type='voice_style',
            confidence=min(confidence, 1.0),
            evidence=', '.join(evidence) if evidence else '',
            method='regex_pattern'
        )
    
    def _detect_greeting_heuristic(self, message: str) -> ContextSignal:
        """Detect greetings using structural heuristics"""
        # Simple but effective heuristics for greetings
        message_lower = message.lower().strip()
        word_count = len(message.split())
        
        greeting_indicators = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 
            'good evening', 'what\'s up', 'how\'s it going', 'sup'
        ]
        
        confidence = 0.0
        
        # Short messages starting with greeting words
        if word_count <= 5 and any(message_lower.startswith(greeting) for greeting in greeting_indicators):
            confidence = 0.9
        elif any(greeting in message_lower for greeting in greeting_indicators):
            confidence = 0.6
            
        return ContextSignal(
            context_type='greeting',
            confidence=confidence,
            evidence=message_lower if confidence > 0 else '',
            method='heuristic'
        )
    
    def _detect_simple_question_heuristic(self, message: str) -> ContextSignal:
        """Detect simple questions using structural analysis"""
        word_count = len(message.split())
        has_question_mark = '?' in message
        
        # Simple questions are typically short with question marks
        if has_question_mark and word_count < 10:
            confidence = 0.8
        elif has_question_mark and word_count < 15:
            confidence = 0.5
        else:
            confidence = 0.0
            
        return ContextSignal(
            context_type='simple_question',
            confidence=confidence,
            evidence=f'{word_count} words, has_question_mark={has_question_mark}',
            method='heuristic'
        )


# Factory function for integration
def create_advanced_context_detector() -> AdvancedContextDetector:
    """Create an advanced context detector instance"""
    return AdvancedContextDetector()


if __name__ == "__main__":
    # Quick test
    detector = create_advanced_context_detector()
    
    test_messages = [
        "are you an AI?",
        "what! ?", 
        "I was responding to what you said",
        "tell me about yourself",
        "hello there",
        "how do you communicate?",
        "do you have consciousness?",
        "can we meet for coffee?",
        "what are you working on today?",  # Should not trigger AI
    ]
    
    print("Testing Advanced Context Detection:")
    print("=" * 60)
    
    for message in test_messages:
        results = detector.detect_context_needs(message)
        print(f"\nMessage: '{message}'")
        
        if results:
            for context_type, signal in results.items():
                confidence_display = "⭐" * int(signal.confidence * 5)
                print(f"  {context_type}: {signal.confidence:.2f} {confidence_display}")
                print(f"    Evidence: {signal.evidence}")
                print(f"    Method: {signal.method}")
        else:
            print("  No significant context signals detected")