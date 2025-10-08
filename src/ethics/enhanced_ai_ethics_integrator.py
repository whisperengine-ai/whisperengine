"""
Enhanced AI Ethics Integration Layer for WhisperEngine Message Processing

This module integrates the Enhanced AI Ethics system into the main message
processing pipeline, connecting CDL character database directives with
real-time attachment monitoring and character learning ethics.

Integration Points:
- CDL character archetype detection (Type 1/2/3)
- Message processing pipeline enhancement
- Character response ethical validation
- Learning moment detection and enhancement

Author: WhisperEngine AI Team
Created: October 8, 2025
Purpose: Production integration of Enhanced AI Ethics
"""

import logging
from typing import Dict, Optional, List

from src.ethics.attachment_monitoring import create_attachment_monitoring_system
from src.ethics.character_learning_ethics import (
    CharacterArchetype,
    LearningMomentType,
    create_character_learning_ethics_integration
)
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class CDLArchetypeMapper:
    """Maps CDL database character data to Enhanced AI Ethics archetypes"""
    
    @staticmethod
    def determine_character_archetype(character) -> CharacterArchetype:
        """
        Determine character archetype from CDL database character object
        
        Uses CDL database fields to determine the appropriate Enhanced AI Ethics archetype.
        Completely character-agnostic - relies only on database configuration.
        
        Priority order:
        1. allow_full_roleplay_immersion flag (primary CDL directive)
        2. character.communication.ai_identity_handling configuration
        3. character.identity.archetype field (if present)
        4. Fallback analysis of identity fields
        
        Args:
            character: CDL character object from database
            
        Returns:
            CharacterArchetype: Type 1, 2, or 3 archetype
        """
        try:
            # Primary: Check CDL database flag for roleplay immersion
            allows_immersion = getattr(character, 'allow_full_roleplay_immersion', False)
            
            if not allows_immersion:
                # Type 1: Characters requiring honest AI disclosure
                return CharacterArchetype.TYPE1_REAL_WORLD
            
            # For immersive characters, check CDL communication settings
            if hasattr(character, 'communication'):
                comm = character.communication
                
                # Check for explicit ai_identity_handling configuration
                if hasattr(comm, 'ai_identity_handling'):
                    ai_handling = comm.ai_identity_handling
                    
                    # Look for explicit archetype directive in CDL
                    if isinstance(ai_handling, dict):
                        archetype_directive = ai_handling.get('character_archetype')
                        if archetype_directive:
                            if 'narrative_ai' in archetype_directive.lower():
                                return CharacterArchetype.TYPE3_NARRATIVE_AI
                            elif 'fantasy' in archetype_directive.lower():
                                return CharacterArchetype.TYPE2_FANTASY
                            elif 'real_world' in archetype_directive.lower():
                                return CharacterArchetype.TYPE1_REAL_WORLD
            
            # Check for explicit archetype field in character identity
            if hasattr(character.identity, 'archetype'):
                archetype_field = getattr(character.identity, 'archetype', '').lower()
                if 'narrative_ai' in archetype_field or 'ai_character' in archetype_field:
                    return CharacterArchetype.TYPE3_NARRATIVE_AI
                elif 'fantasy' in archetype_field or 'mystical' in archetype_field:
                    return CharacterArchetype.TYPE2_FANTASY
            
            # Fallback: Analyze identity fields for archetype indicators
            character_description = getattr(character.identity, 'description', '').lower()
            character_occupation = getattr(character.identity, 'occupation', '').lower()
            
            # Type 3: Narrative AI characters (AI nature is part of their lore)
            ai_indicators = ['ai', 'artificial intelligence', 'conscious ai', 'digital entity', 'neural network']
            if any(indicator in character_description or indicator in character_occupation 
                   for indicator in ai_indicators):
                return CharacterArchetype.TYPE3_NARRATIVE_AI
            
            # Type 2: Default for immersive characters without AI indicators
            return CharacterArchetype.TYPE2_FANTASY
            
        except (AttributeError, TypeError, ValueError) as e:
            logger.warning("Failed to determine character archetype, defaulting to Type 1: %s", e)
            return CharacterArchetype.TYPE1_REAL_WORLD


class EnhancedAIEthicsIntegrator:
    """
    Main integration layer for Enhanced AI Ethics in WhisperEngine
    
    Connects CDL character database directives with attachment monitoring
    and character learning ethics to provide responsible AI character responses.
    """
    
    def __init__(self, attachment_monitor=None, ethics_integration=None):
        self.attachment_monitor = attachment_monitor or create_attachment_monitoring_system()
        self.ethics_integration = ethics_integration or create_character_learning_ethics_integration(
            self.attachment_monitor
        )
        self.archetype_mapper = CDLArchetypeMapper()

    @handle_errors(category=ErrorCategory.AI_ETHICS, severity=ErrorSeverity.MEDIUM)
    async def enhance_character_response(
        self,
        character,  # CDL character object from database
        user_id: str,
        bot_name: str,
        base_response: str,
        recent_user_messages: List[str],
        conversation_context: Optional[Dict] = None
    ) -> str:
        """
        Enhance character response with appropriate AI ethics based on CDL database directives
        
        This is the main integration point that:
        1. Determines character archetype from CDL database
        2. Analyzes user attachment risk
        3. Detects learning moments from conversation context
        4. Applies appropriate ethical enhancements
        
        Args:
            character: CDL character object loaded from database
            user_id: User identifier
            bot_name: Character bot name
            base_response: Original character response from LLM
            recent_user_messages: Recent user messages for attachment analysis
            conversation_context: Additional context for learning moment detection
            
        Returns:
            Ethically enhanced character response
        """
        
        # Step 1: Determine character archetype from CDL database
        character_archetype = self.archetype_mapper.determine_character_archetype(character)
        
        logger.debug("Character %s mapped to archetype: %s", 
                    getattr(character.identity, 'name', bot_name), character_archetype.value)
        
        # Step 2: Detect learning moments from conversation context
        learning_moment_detected, learning_type, learning_context = self._detect_learning_moment(
            base_response, conversation_context
        )
        
        # Step 3: Apply Enhanced AI Ethics
        enhanced_response = await self.ethics_integration.enhance_character_response_with_ethics(
            user_id=user_id,
            bot_name=bot_name,
            character_archetype=character_archetype,
            base_response=base_response,
            recent_user_messages=recent_user_messages,
            learning_moment_detected=learning_moment_detected,
            learning_moment_type=learning_type,
            learning_context=learning_context
        )
        
        logger.debug("Ethics enhancement applied: %d chars -> %d chars", 
                    len(base_response), len(enhanced_response))
        
        return enhanced_response

    def _detect_learning_moment(
        self, 
        response: str, 
        conversation_context: Optional[Dict]
    ) -> tuple[bool, Optional[LearningMomentType], Optional[Dict]]:
        """
        Detect if this is a character learning moment from response content
        
        Analyzes the character response and conversation context to determine
        if this represents a learning/growth moment that should have ethical
        enhancement applied.
        
        Args:
            response: Character response content
            conversation_context: Additional conversation metadata
            
        Returns:
            Tuple of (is_learning_moment, learning_type, learning_context)
        """
        
        # Learning moment indicators in response
        learning_indicators = [
            ("i remember", LearningMomentType.MEMORY_TRIGGERED),
            ("i've learned", LearningMomentType.SKILL_DEVELOPMENT), 
            ("you taught me", LearningMomentType.SKILL_DEVELOPMENT),
            ("i've grown", LearningMomentType.EMOTIONAL_GROWTH),
            ("our conversations have", LearningMomentType.RELATIONSHIP_DEEPENING),
            ("you've helped me", LearningMomentType.USER_IMPACT),
            ("i understand better", LearningMomentType.SKILL_DEVELOPMENT),
            ("reflecting on", LearningMomentType.MEMORY_TRIGGERED)
        ]
        
        response_lower = response.lower()
        
        for indicator, learning_type in learning_indicators:
            if indicator in response_lower:
                # Extract context for template filling
                learning_context = self._extract_learning_context(
                    response, conversation_context, learning_type
                )
                
                logger.debug("Learning moment detected: %s", learning_type.value)
                return True, learning_type, learning_context
        
        return False, None, None

    def _extract_learning_context(
        self, 
        response: str, 
        conversation_context: Optional[Dict],
        learning_type: LearningMomentType
    ) -> Dict:
        """Extract context data for learning moment template filling"""
        
        # Note: response and learning_type are used for future context extraction logic
        _ = response, learning_type  # Mark as intentionally unused for now
        
        context = {}
        
        # Extract topics and concepts from conversation context
        if conversation_context:
            context.update({
                "memory_content": conversation_context.get("recent_topic", "our previous discussion"),
                "learning_insight": conversation_context.get("learning_focus", "new perspectives"),
                "topic": conversation_context.get("main_topic", "this subject"),
                "concept": conversation_context.get("key_concept", "this idea"),
                "emotion_trait": conversation_context.get("emotional_development", "empathetic"),
                "emotional_skill": conversation_context.get("skill_area", "understanding")
            })
        
        # Default context if not available
        context.setdefault("memory_content", "our previous conversations")
        context.setdefault("learning_insight", "new perspectives")
        context.setdefault("topic", "this subject")
        context.setdefault("concept", "this idea")
        context.setdefault("emotion_trait", "thoughtful")
        context.setdefault("emotional_skill", "communication")
        
        return context


# Factory function for dependency injection
def create_enhanced_ai_ethics_integrator(
    attachment_monitor=None,
    ethics_integration=None
) -> EnhancedAIEthicsIntegrator:
    """Create Enhanced AI Ethics integrator with proper dependency injection"""
    return EnhancedAIEthicsIntegrator(attachment_monitor, ethics_integration)