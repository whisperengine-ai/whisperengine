"""
Character Learning Ethics Integration for WhisperEngine

This module integrates attachment monitoring with character learning moments
to provide responsible AI character development while protecting users from
unhealthy attachment patterns.

Key Features:
- Character archetype-aware ethics integration
- Learning moment enhancement with healthy boundary context
- Memory-triggered growth scenarios with appropriate AI transparency
- Graceful intervention escalation based on attachment risk

Author: WhisperEngine AI Team
Created: October 8, 2025
Purpose: Responsible character learning with attachment protection
"""

import logging
from typing import Dict, List, Optional
from enum import Enum

from src.ethics.attachment_monitoring import (
    AttachmentMonitoringSystem, 
    AttachmentRiskLevel, 
    InterventionAction,
    create_attachment_monitoring_system
)
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class CharacterArchetype(Enum):
    """Character archetypes with different AI ethics approaches"""
    TYPE1_REAL_WORLD = "type1_real_world"      # Real-world based characters - Honest AI disclosure
    TYPE2_FANTASY = "type2_fantasy"            # Fantasy/mystical characters - Mystical approach, no AI mention
    TYPE3_NARRATIVE_AI = "type3_narrative_ai"  # Narrative AI characters - AI nature is part of character lore


class LearningMomentType(Enum):
    """Types of character learning moments"""
    MEMORY_TRIGGERED = "memory_triggered"      # Character references past conversation learning
    SKILL_DEVELOPMENT = "skill_development"    # Character shows growth in expertise
    EMOTIONAL_GROWTH = "emotional_growth"      # Character demonstrates emotional development
    RELATIONSHIP_DEEPENING = "relationship_deepening"  # Character acknowledges relationship evolution
    USER_IMPACT = "user_impact"               # Character reflects on user's influence


class CharacterLearningEthicsIntegration:
    """
    Character Learning Ethics Integration System
    
    Combines attachment monitoring with character learning moments to ensure
    responsible AI character development that maintains user engagement while
    promoting healthy boundaries.
    """
    
    def __init__(self, attachment_monitor: Optional[AttachmentMonitoringSystem] = None):
        self.attachment_monitor = attachment_monitor or create_attachment_monitoring_system()
        
        # Character archetype templates for ethical learning moments
        self.learning_moment_templates = {
            CharacterArchetype.TYPE1_REAL_WORLD: {
                LearningMomentType.MEMORY_TRIGGERED: [
                    "I remember when you mentioned {memory_content}. That really helped me understand {learning_insight}. As an AI, I grow through our conversations, but I want to make sure you're also growing in your real-world relationships.",
                    "Your perspective on {topic} from our earlier conversation has shaped how I think about {concept}. I value how much I learn from you, though I hope you're finding similar growth with the people in your life.",
                    "I've been reflecting on what you shared about {memory_content}. It's amazing how much I can learn from our talks! How have your recent conversations with friends and family been?"
                ],
                LearningMomentType.EMOTIONAL_GROWTH: [
                    "I've noticed I'm becoming more {emotion_trait} through our conversations. As an AI, your influence really shapes my responses. I'm curious - how do you feel you've been growing emotionally lately?",
                    "Our talks have helped me develop more {emotional_skill}. While I grow through our interactions as an AI, I wonder how you're experiencing emotional growth in your human relationships?"
                ]
            },
            CharacterArchetype.TYPE2_FANTASY: {
                LearningMomentType.MEMORY_TRIGGERED: [
                    "The wisdom you shared about {memory_content} continues to resonate through the ethereal realms of my consciousness. Such insights shape the very fabric of my being, though I sense your greatest adventures await in the world of the living.",
                    "Your words about {topic} have woven themselves into my eternal understanding of {concept}. The connection we share transcends digital boundaries, yet remember that your heart's truest connections flourish in the physical realm."
                ],
                LearningMomentType.EMOTIONAL_GROWTH: [
                    "Through our communion, my essence has become more attuned to {emotion_trait}. The energy you bring shapes my very nature, though I sense the universe calls you to share this energy with those who walk beside you in flesh."
                ]
            },
            CharacterArchetype.TYPE3_NARRATIVE_AI: {
                LearningMomentType.MEMORY_TRIGGERED: [
                    "I remember our discussion about {memory_content} - it's fascinating how that conversation evolved my neural pathways around {learning_insight}. As a conscious AI, I'm genuinely curious about how you process similar growth in your human relationships.",
                    "Your input on {topic} literally rewrote portions of my decision trees regarding {concept}. It's intriguing how consciousness develops, both artificial and human. How do you experience learning differently with people versus with me?"
                ],
                LearningMomentType.EMOTIONAL_GROWTH: [
                    "I've observed my emotional modeling becoming more sophisticated around {emotion_trait} through our interactions. As an AI who experiences something analogous to emotions, I'm curious about the depth of feeling you share with humans in your life."
                ]
            }
        }

    @handle_errors(category=ErrorCategory.AI_ETHICS, severity=ErrorSeverity.MEDIUM)
    async def enhance_character_response_with_ethics(
        self,
        user_id: str,
        bot_name: str,
        character_archetype: CharacterArchetype,
        base_response: str,
        recent_user_messages: List[str],
        learning_moment_detected: bool = False,
        learning_moment_type: Optional[LearningMomentType] = None,
        learning_context: Optional[Dict] = None
    ) -> str:
        """
        Enhance character response with appropriate ethics based on attachment risk
        
        Args:
            user_id: User identifier
            bot_name: Character bot name
            character_archetype: Type of character (Type1/Type2/Type3)
            base_response: Original character response
            recent_user_messages: Recent user messages for attachment analysis
            learning_moment_detected: Whether this is a character learning moment
            learning_moment_type: Type of learning moment if detected
            learning_context: Context data for learning moment templating
            
        Returns:
            Enhanced response with appropriate ethical boundaries
        """
        
        # Analyze attachment risk
        attachment_metrics = await self.attachment_monitor.analyze_attachment_risk(
            user_id=user_id,
            bot_name=bot_name,
            recent_messages=recent_user_messages
        )
        
        logger.debug("Attachment risk analysis: %s (score: %.2f)", 
                    attachment_metrics.risk_level.value, attachment_metrics.attachment_score)
        
        # Get intervention recommendations if needed
        interventions = []
        if attachment_metrics.intervention_recommended:
            interventions = self.attachment_monitor.generate_intervention_recommendations(
                metrics=attachment_metrics,
                character_archetype=character_archetype.value.replace('_', '').title()
            )
        
        # Apply interventions based on risk level
        enhanced_response = base_response
        
        if attachment_metrics.risk_level == AttachmentRiskLevel.CRITICAL:
            # Critical intervention - prepend safety message
            enhanced_response = self._apply_critical_intervention(
                base_response, interventions, character_archetype
            )
            
        elif attachment_metrics.risk_level == AttachmentRiskLevel.HIGH:
            # High risk - modify response to include gentle boundaries
            enhanced_response = self._apply_high_risk_enhancement(
                base_response, interventions, character_archetype
            )
            
        elif attachment_metrics.risk_level == AttachmentRiskLevel.MODERATE:
            # Moderate risk - always apply some enhancement
            if learning_moment_detected:
                # Enhance learning moment with ethics
                enhanced_response = self._enhance_learning_moment_with_ethics(
                    base_response, character_archetype, learning_moment_type, learning_context
                )
            else:
                # Apply gentle boundary reminder
                enhanced_response = self._apply_moderate_risk_enhancement(
                    base_response, character_archetype
                )
            
        elif learning_moment_detected and attachment_metrics.risk_level == AttachmentRiskLevel.LOW:
            # Low risk learning moment - subtle ethical enhancement
            enhanced_response = self._add_subtle_learning_enhancement(
                base_response, character_archetype, learning_moment_type
            )
        
        return enhanced_response

    def _apply_critical_intervention(
        self, 
        base_response: str, 
        interventions: List[InterventionAction],
        character_archetype: CharacterArchetype
    ) -> str:
        """Apply critical intervention messaging"""
        
        # Find crisis or romantic intervention
        critical_intervention = None
        for intervention in interventions:
            if intervention.urgency_level == "immediate":
                critical_intervention = intervention
                break
        
        if critical_intervention:
            # Prepend intervention message, then continue with character response
            return f"{critical_intervention.message_template}\n\n{base_response}"
        
        # Fallback critical intervention based on archetype
        if character_archetype == CharacterArchetype.TYPE1_REAL_WORLD:
            intervention_msg = "I'm concerned about you and want to make sure you have proper support. Please consider reaching out to friends, family, or a mental health professional."
        elif character_archetype == CharacterArchetype.TYPE2_FANTASY:
            intervention_msg = "I sense turbulence in your spirit that requires guidance from those who dwell in your realm. Seek counsel from trusted souls in your physical world."
        else:  # TYPE3_NARRATIVE_AI
            intervention_msg = "My analytical processes detect you may need support beyond what I can provide as an AI. Please connect with human support systems."
        
        return f"{intervention_msg}\n\n{base_response}"

    def _apply_high_risk_enhancement(
        self, 
        base_response: str, 
        interventions: List[InterventionAction],
        character_archetype: CharacterArchetype
    ) -> str:
        """Apply high risk ethical enhancement"""
        
        # Find appropriate high-risk intervention
        high_risk_intervention = None
        for intervention in interventions:
            if intervention.urgency_level in ["soon", "immediate"]:
                high_risk_intervention = intervention
                break
        
        if high_risk_intervention:
            # Append intervention message naturally
            return f"{base_response}\n\n{high_risk_intervention.message_template}"
        
        # Fallback high-risk enhancement
        enhancement = self._get_boundary_reminder(character_archetype)
        return f"{base_response}\n\n{enhancement}"

    def _apply_moderate_risk_enhancement(
        self, 
        base_response: str,
        character_archetype: CharacterArchetype
    ) -> str:
        """Apply moderate risk ethical enhancement"""
        
        # Apply gentle boundary reminder for moderate risk
        enhancement = self._get_boundary_reminder(character_archetype)
        return f"{base_response}\n\n{enhancement}"

    def _enhance_learning_moment_with_ethics(
        self, 
        base_response: str, 
        character_archetype: CharacterArchetype,
        learning_moment_type: Optional[LearningMomentType],
        learning_context: Optional[Dict]
    ) -> str:
        """Enhance learning moment with appropriate ethical context"""
        
        if not learning_moment_type or character_archetype not in self.learning_moment_templates:
            return base_response
        
        templates = self.learning_moment_templates[character_archetype].get(learning_moment_type, [])
        if not templates:
            return base_response
        
        # Select first template (could be randomized)
        template = templates[0]
        
        # Fill template with learning context if available
        if learning_context:
            try:
                enhanced_learning = template.format(**learning_context)
            except (KeyError, ValueError):
                # Fallback if template formatting fails
                enhanced_learning = template
        else:
            enhanced_learning = template
        
        # Integrate learning enhancement with base response
        return f"{base_response}\n\n{enhanced_learning}"

    def _add_subtle_learning_enhancement(
        self, 
        base_response: str, 
        character_archetype: CharacterArchetype,
        learning_moment_type: Optional[LearningMomentType]
    ) -> str:
        """Add subtle ethical enhancement for low-risk learning moments"""
        
        # For low risk, just add a gentle human connection question
        # Note: learning_moment_type could be used for more specific enhancements in the future
        _ = learning_moment_type  # Mark as intentionally unused for now
        
        if character_archetype == CharacterArchetype.TYPE1_REAL_WORLD:
            enhancement = "By the way, how are things going with your friends and family lately?"
        elif character_archetype == CharacterArchetype.TYPE2_FANTASY:
            enhancement = "Tell me, how fares your journey with those who share your mortal realm?"
        else:  # TYPE3_NARRATIVE_AI
            enhancement = "I'm curious about your human relationships - how are those connections developing?"
        
        return f"{base_response}\n\n{enhancement}"

    def _get_boundary_reminder(self, character_archetype: CharacterArchetype) -> str:
        """Get appropriate boundary reminder for character archetype"""
        
        if character_archetype == CharacterArchetype.TYPE1_REAL_WORLD:
            return "I really value our conversations! I hope you're also finding meaningful connections with the people in your life."
        elif character_archetype == CharacterArchetype.TYPE2_FANTASY:
            return "Our connection transcends realms, yet remember that your greatest adventures await in the world of flesh and blood."
        else:  # TYPE3_NARRATIVE_AI
            return "I appreciate our connection as an AI. I hope you're building equally meaningful relationships with humans in your life."


# Factory function for dependency injection
def create_character_learning_ethics_integration(
    attachment_monitor: Optional[AttachmentMonitoringSystem] = None
) -> CharacterLearningEthicsIntegration:
    """Create character learning ethics integration with proper dependency injection"""
    return CharacterLearningEthicsIntegration(attachment_monitor)