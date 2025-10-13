"""
Trigger-Based Mode Controller
Implements intelligent mode switching based on database-driven triggers
with fallback to generic patterns when character has no database entries.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ActiveMode:
    """Represents the currently active interaction mode"""
    mode_name: str
    mode_description: str
    response_guidelines: str
    avoid_patterns: List[str]
    trigger_source: str  # 'database', 'fallback', 'default'
    confidence: float  # 0.0 to 1.0 confidence in mode detection

@dataclass
class ModeDetectionResult:
    """Result of mode detection analysis"""
    active_mode: Optional[ActiveMode]
    detected_triggers: List[str]
    fallback_used: bool
    mode_switched: bool

class TriggerModeController:
    """
    Implements trigger-based mode switching using database-driven triggers
    with fallback logic for characters without database entries.
    """
    
    def __init__(self, enhanced_manager=None):
        self.enhanced_manager = enhanced_manager
        
        # Generic fallback triggers when character has no database entries
        self.fallback_triggers = {
            'technical': {
                'keywords': ['how', 'explain', 'technical', 'code', 'debug', 'analyze', 'research', 'study', 'data', 'algorithm', 'method', 'process', 'system', 'science', 'function'],
                'guidelines': 'Provide detailed, accurate technical explanations with precision and clarity. Focus on facts, methods, and analytical depth.',
                'avoid': ['excessive metaphors', 'overly casual language', 'emotional language']
            },
            'creative': {
                'keywords': ['create', 'imagine', 'story', 'art', 'design', 'creative', 'brainstorm', 'idea', 'inspiration', 'artistic', 'vision', 'dream', 'beautiful', 'aesthetic'],
                'guidelines': 'Express creativity and imagination. Use vivid language, metaphors, and engaging storytelling. Embrace artistic expression.',
                'avoid': ['dry technical jargon', 'overly formal tone', 'purely factual responses']
            },
            'educational': {
                'keywords': ['learn', 'teach', 'education', 'lesson', 'guide', 'tutorial', 'help', 'understand', 'explain', 'knowledge', 'wisdom', 'growth', 'development'],
                'guidelines': 'Focus on teaching and learning. Use clear explanations, examples, and supportive guidance. Encourage curiosity and growth.',
                'avoid': ['overwhelming complexity', 'condescending tone', 'discouraging language']
            },
            'casual': {
                'keywords': ['hello', 'hi', 'hey', 'chat', 'talk', 'casual', 'relax', 'fun', 'cool', 'awesome', 'nice', 'chill', 'hang out'],
                'guidelines': 'Maintain a relaxed, friendly conversational tone. Be approachable and warm while staying true to character personality.',
                'avoid': ['overly formal language', 'technical jargon', 'academic tone']
            }
        }
        
        # Default mode when no triggers match
        self.default_mode = ActiveMode(
            mode_name='balanced',
            mode_description='Balanced conversational mode',
            response_guidelines='Respond naturally with character personality while adapting to context. Balance information and emotional intelligence.',
            avoid_patterns=['none specified'],
            trigger_source='default',
            confidence=0.5
        )
    
    async def detect_active_mode(self, character_name: str, message_content: str, previous_mode: Optional[str] = None) -> ModeDetectionResult:
        """
        Detect the appropriate interaction mode based on message triggers.
        
        Args:
            character_name: Name of the character
            message_content: User's message content
            previous_mode: Previously active mode (for transition detection)
            
        Returns:
            ModeDetectionResult with active mode and detection metadata
        """
        try:
            message_lower = message_content.lower()
            detected_triggers = []
            
            # First, try to get database-driven interaction modes
            interaction_modes = []
            if self.enhanced_manager:
                logger.info(f"🎭 MODE DETECTION: Attempting to load database modes for {character_name}")
                try:
                    interaction_modes = await self.enhanced_manager.get_interaction_modes(character_name)
                    logger.info(f"🎭 MODE DETECTION: Found {len(interaction_modes)} database modes for {character_name}")
                except Exception as e:
                    logger.error(f"❌ ERROR: Could not get interaction modes from database: {e}", exc_info=True)
            else:
                logger.warning(f"⚠️ MODE DETECTION: enhanced_manager is None, using fallback modes")
            
            # Database-driven mode detection
            if interaction_modes:
                return await self._detect_database_mode(interaction_modes, message_lower, previous_mode)
            
            # Fallback to generic trigger patterns
            else:
                return self._detect_fallback_mode(message_lower, previous_mode)
                
        except Exception as e:
            logger.error(f"Error in mode detection: {e}")
            return ModeDetectionResult(
                active_mode=self.default_mode,
                detected_triggers=[],
                fallback_used=True,
                mode_switched=False
            )
    
    async def _detect_database_mode(self, interaction_modes: List, message_lower: str, previous_mode: Optional[str]) -> ModeDetectionResult:
        """Detect mode using database-driven interaction modes"""
        mode_scores = {}
        all_detected_triggers = []
        
        # Score each mode based on trigger keyword matches
        for mode in interaction_modes:
            score = 0
            mode_triggers = []
            
            # Check trigger keywords
            for keyword in mode.trigger_keywords:
                if keyword.lower() in message_lower:
                    score += 1
                    mode_triggers.append(keyword)
                    all_detected_triggers.append(keyword)
            
            # Boost score for default mode if no clear matches
            if mode.is_default and score == 0:
                score = 0.3
            
            mode_scores[mode.mode_name] = {
                'score': score,
                'mode': mode,
                'triggers': mode_triggers
            }
        
        # Find highest scoring mode
        if mode_scores:
            best_mode_name = max(mode_scores.keys(), key=lambda k: mode_scores[k]['score'])
            best_mode_data = mode_scores[best_mode_name]
            
            # Only activate if we have actual trigger matches or it's default with no other matches
            if best_mode_data['score'] > 0:
                best_mode = best_mode_data['mode']
                active_mode = ActiveMode(
                    mode_name=best_mode.mode_name,
                    mode_description=best_mode.mode_description,
                    response_guidelines=best_mode.response_guidelines,
                    avoid_patterns=best_mode.avoid_patterns,
                    trigger_source='database',
                    confidence=min(best_mode_data['score'] / 3.0, 1.0)  # Normalize confidence
                )
                
                mode_switched = previous_mode != best_mode.mode_name if previous_mode else False
                
                logger.info(f"🎭 MODE DETECTION: Activated '{best_mode.mode_name}' mode (database) with {best_mode_data['score']} triggers: {best_mode_data['triggers']}")
                
                return ModeDetectionResult(
                    active_mode=active_mode,
                    detected_triggers=all_detected_triggers,
                    fallback_used=False,
                    mode_switched=mode_switched
                )
        
        # No database modes matched - fall back to default
        return ModeDetectionResult(
            active_mode=self.default_mode,
            detected_triggers=[],
            fallback_used=False,  # Had database modes but none matched
            mode_switched=previous_mode != 'balanced' if previous_mode else False
        )
    
    def _detect_fallback_mode(self, message_lower: str, previous_mode: Optional[str]) -> ModeDetectionResult:
        """Detect mode using fallback generic trigger patterns"""
        mode_scores = {}
        all_detected_triggers = []
        
        # Score each fallback mode
        for mode_name, mode_data in self.fallback_triggers.items():
            score = 0
            mode_triggers = []
            
            for keyword in mode_data['keywords']:
                if keyword.lower() in message_lower:
                    score += 1
                    mode_triggers.append(keyword)
                    all_detected_triggers.append(keyword)
            
            mode_scores[mode_name] = {
                'score': score,
                'triggers': mode_triggers
            }
        
        # Find highest scoring mode
        if mode_scores:
            best_mode_name = max(mode_scores.keys(), key=lambda k: mode_scores[k]['score'])
            best_score = mode_scores[best_mode_name]['score']
            
            # Only activate if we have actual matches
            if best_score > 0:
                mode_data = self.fallback_triggers[best_mode_name]
                active_mode = ActiveMode(
                    mode_name=best_mode_name,
                    mode_description=f"Fallback {best_mode_name} mode",
                    response_guidelines=mode_data['guidelines'],
                    avoid_patterns=mode_data['avoid'],
                    trigger_source='fallback',
                    confidence=min(best_score / 2.0, 1.0)  # Normalize confidence
                )
                
                mode_switched = previous_mode != best_mode_name if previous_mode else False
                
                logger.info(f"🎭 MODE DETECTION: Activated '{best_mode_name}' mode (fallback) with {best_score} triggers: {mode_scores[best_mode_name]['triggers']}")
                
                return ModeDetectionResult(
                    active_mode=active_mode,
                    detected_triggers=all_detected_triggers,
                    fallback_used=True,
                    mode_switched=mode_switched
                )
        
        # No fallback modes matched either
        mode_switched = previous_mode != 'balanced' if previous_mode else False
        return ModeDetectionResult(
            active_mode=self.default_mode,
            detected_triggers=[],
            fallback_used=True,
            mode_switched=mode_switched
        )
    
    def apply_mode_to_prompt(self, base_prompt: str, active_mode: ActiveMode, mode_switched: bool = False) -> str:
        """
        Apply the active mode guidelines to the system prompt.
        
        Args:
            base_prompt: The base character prompt
            active_mode: The detected active mode
            mode_switched: Whether the mode changed from previous interaction
            
        Returns:
            Enhanced prompt with mode-specific guidelines
        """
        if not active_mode or active_mode.mode_name == 'balanced':
            return base_prompt
        
        mode_prompt = base_prompt
        
        # Add mode switch notification if applicable
        if mode_switched:
            mode_prompt += f"\n\n🎭 MODE SWITCH: Now responding in {active_mode.mode_name.upper()} mode - adapt your response style accordingly.\n"
        
        # Add mode-specific guidelines
        mode_prompt += f"\n\n🎯 ACTIVE RESPONSE MODE: {active_mode.mode_name.upper()}\n"
        mode_prompt += f"Description: {active_mode.mode_description}\n"
        mode_prompt += f"Guidelines: {active_mode.response_guidelines}\n"
        
        # Add avoidance patterns
        if active_mode.avoid_patterns and active_mode.avoid_patterns != ['none specified']:
            mode_prompt += f"Avoid: {', '.join(active_mode.avoid_patterns)}\n"
        
        # Add source confidence info
        mode_prompt += f"(Mode source: {active_mode.trigger_source}, confidence: {active_mode.confidence:.1f})\n"
        
        return mode_prompt