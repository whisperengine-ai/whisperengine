"""
CDL Emoji Integration for WhisperEngine Bots
===========================================

Integrates the CDL-aware emoji personality system with the existing bot architecture.
Provides natural emoji+text responses based on character personalities.
"""

import logging
import os
from typing import Dict, Optional, Any, Tuple

from .cdl_emoji_personality import CDLEmojiGenerator, EmojiResponse
from .vector_emoji_intelligence import EmojiResponseDecision, EmojiResponseContext

logger = logging.getLogger(__name__)


class CDLEmojiIntegration:
    """
    Integration layer between CDL emoji personalities and WhisperEngine bot responses
    """
    
    def __init__(self, character_files_dir: str = "characters/examples"):
        self.emoji_generator = CDLEmojiGenerator(character_files_dir)
        self.enabled = os.getenv("EMOJI_ENABLED", "true").lower() == "true"
        
        # Override thresholds when CDL system is active
        self.cdl_base_threshold = 0.3  # Lower threshold since CDL handles frequency internally
        self.cdl_new_user_threshold = 0.2
        
        logger.info(f"🎭 CDL Emoji Integration initialized (enabled: {self.enabled})")
        
    def enhance_bot_response(self,
                           character_file: str,
                           user_id: str,
                           user_message: str,
                           bot_response: str,
                           context: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Enhance bot response with CDL-appropriate emojis
        
        Args:
            character_file: CDL character file (e.g., "elena-rodriguez.json")
            user_id: User identifier
            user_message: User's input message
            bot_response: Bot's text response to enhance
            context: Additional context (conversation history, emotional state, etc.)
            
        Returns:
            (enhanced_response, emoji_metadata)
        """
        if not self.enabled:
            return bot_response, {"cdl_emoji_applied": False, "reason": "disabled"}
            
        try:
            # Determine if we should add emojis based on CDL personality
            should_add, confidence = self.emoji_generator.should_add_emojis(
                character_file, user_message, bot_response, context
            )
            
            if not should_add:
                logger.debug("🎭 CDL EMOJI INTEGRATION: Skipping emoji enhancement - threshold not met (confidence: %.2f)", confidence)
                return bot_response, {
                    "cdl_emoji_applied": False,
                    "reason": "cdl_personality_threshold_not_met",
                    "confidence": confidence
                }
            
            logger.debug("🎭 CDL EMOJI INTEGRATION: Starting emoji enhancement for %s", character_file)
            
            # Detect excitement level for appropriate emoji intensity
            excitement = self._detect_excitement_level(user_message, bot_response, context)
            logger.debug("🎭 CDL EMOJI INTEGRATION: Detected excitement level: %s", excitement)
            
            # Generate emoji-enhanced response
            emoji_response = self.emoji_generator.generate_emoji_response(
                character_file=character_file,
                user_message=user_message,
                bot_response_text=bot_response,
                excitement_level=excitement,
                context=context
            )
            
            emoji_metadata = {
                "cdl_emoji_applied": True,
                "character_file": character_file,
                "emoji_additions": emoji_response.emoji_additions,
                "placement_style": emoji_response.placement_style,
                "confidence": emoji_response.confidence,
                "reasoning": emoji_response.reasoning,
                "excitement_level": excitement
            }
            
            logger.debug("🎭 CDL EMOJI INTEGRATION: Enhancement complete - %d emojis added, confidence: %.2f", 
                        len(emoji_response.emoji_additions), emoji_response.confidence)
            logger.debug("🎭 CDL emoji enhancement for %s: %d emojis added", character_file, len(emoji_response.emoji_additions))
            
            return emoji_response.response_text, emoji_metadata
            
        except Exception as e:
            logger.error(f"Error in CDL emoji enhancement: {e}")
            return bot_response, {"cdl_emoji_applied": False, "error": str(e)}
            
    def _detect_excitement_level(self, 
                               user_message: str, 
                               bot_response: str, 
                               context: Optional[Dict[str, Any]] = None) -> str:
        """Detect excitement level from conversation context"""
        context = context or {}
        
        # Check for high-excitement indicators
        high_indicators = ["!", "amazing", "incredible", "awesome", "love it", "fantastic", "brilliant"]
        medium_indicators = ["cool", "nice", "good", "interesting", "thanks", "?"]
        
        combined_text = (user_message + " " + bot_response).lower()
        
        high_count = sum(1 for indicator in high_indicators if indicator in combined_text)
        medium_count = sum(1 for indicator in medium_indicators if indicator in combined_text)
        
        # Check emotional context if available
        if context.get("emotional_intensity") == "high":
            return "high"
        elif context.get("emotional_intensity") == "low":
            return "low"
            
        # Determine from text analysis
        if high_count >= 2 or "!!" in combined_text:
            return "high"
        elif high_count >= 1 or medium_count >= 2:
            return "medium"
        else:
            return "low"
            
    def get_character_emoji_profile_summary(self, character_file: str) -> Dict[str, Any]:
        """Get summary of character's emoji personality for debugging/admin"""
        try:
            profile = self.emoji_generator.load_character_profile(character_file)
            return {
                "character_name": profile.character_name,
                "frequency": profile.frequency.value,
                "style": profile.style,
                "age_demographic": profile.age_demographic,
                "cultural_influence": profile.cultural_influence,
                "preferred_combination": profile.preferred_combination.value,
                "comment": profile.comment
            }
        except Exception as e:
            logger.error(f"Error getting profile summary for {character_file}: {e}")
            return {"error": str(e)}
            
    def create_emoji_response_decision(self,
                                     character_file: str,
                                     user_message: str,
                                     context: Optional[Dict[str, Any]] = None) -> EmojiResponseDecision:
        """
        Create EmojiResponseDecision compatible with existing vector emoji system
        
        This allows CDL system to integrate with existing emoji infrastructure
        while using character-specific personalities.
        """
        try:
            # Use CDL system to determine response approach
            should_add, confidence = self.emoji_generator.should_add_emojis(
                character_file, user_message, "", context
            )
            
            profile = self.emoji_generator.load_character_profile(character_file)
            
            # Map CDL response types to existing emoji system contexts
            context_mapping = {
                "text_plus_emoji": EmojiResponseContext.PLAYFUL_INTERACTION,
                "text_with_accent_emoji": EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT,
                "minimal_symbolic_emoji": EmojiResponseContext.MYSTICAL_WONDER,
                "emoji_only": EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
            }
            
            response_context = context_mapping.get(
                profile.preferred_combination.value,
                EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
            )
            
            return EmojiResponseDecision(
                should_use_emoji=should_add,
                emoji_choice=None,  # Will be filled by generate_emoji_response
                confidence_score=confidence,
                context_reason=response_context,
                fallback_text=None,
                supporting_evidence={
                    "cdl_character": profile.character_name,
                    "cdl_reasoning": f"CDL personality decision for {profile.character_name}",
                    "cdl_style": profile.style
                }
            )
            
        except Exception as e:
            logger.error("Error creating emoji response decision: %s", str(e))
            # Fallback to no emoji
            return EmojiResponseDecision(
                should_use_emoji=False,
                emoji_choice=None,
                confidence_score=0.0,
                context_reason=EmojiResponseContext.CONVERSATION_CLOSER,
                fallback_text=None,
                supporting_evidence={
                    "cdl_error": str(e),
                    "reasoning": "CDL system error"
                }
            )


def create_cdl_emoji_integration(character_files_dir: str = "characters/examples") -> CDLEmojiIntegration:
    """Factory function to create CDL emoji integration"""
    return CDLEmojiIntegration(character_files_dir)


if __name__ == "__main__":
    # Test the integration
    integration = create_cdl_emoji_integration()
    
    # Test different characters
    test_cases = [
        {
            "character": "elena-rodriguez.json",
            "user_msg": "Tell me about whales!",
            "bot_response": "Whales are absolutely incredible creatures with complex social behaviors!",
            "name": "Elena (High frequency + Text+Emoji)"
        },
        {
            "character": "marcus-thompson.json", 
            "user_msg": "How does machine learning work?",
            "bot_response": "Machine learning algorithms learn patterns from data to make predictions.",
            "name": "Marcus (Moderate frequency + Text+Accent)"
        },
        {
            "character": "dream_of_the_endless.json",
            "user_msg": "What do you see in my dreams?",
            "bot_response": "I witness the eternal tapestry of mortal hopes and fears.",
            "name": "Dream (Symbolic minimal)"
        },
        {
            "character": "sophia-blake.json",
            "user_msg": "I got a promotion!",
            "bot_response": "Darling, that's absolutely brilliant! You've earned every bit of that success.",
            "name": "Sophia (Sophisticated + Strategic emojis)"
        }
    ]
    
    for test in test_cases:
        print(f"\n{test['name']}:")
        enhanced, metadata = integration.enhance_bot_response(
            test["character"],
            "test_user",
            test["user_msg"], 
            test["bot_response"]
        )
        print(f"  Original: {test['bot_response']}")
        print(f"  Enhanced: {enhanced}")
        print(f"  Metadata: {metadata.get('reasoning', 'N/A')}")