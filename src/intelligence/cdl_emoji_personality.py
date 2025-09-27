"""
CDL-Aware Emoji Personality System
=================================

Reads Character Definition Language (CDL) digital_communication profiles to create
authentic emoji usage patterns that match each character's age, culture, and personality.

Supports:
- Mixed emoji+text responses (most natural online communication)
- Character-specific emoji frequencies and styles  
- Age-demographic appropriate usage (Gen Z vs Gen X vs timeless entities)
- Cultural influences on emoji expression
- Context-aware emoji placement and intensity
"""

import json
import logging
import os
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class EmojiFrequency(Enum):
    """Emoji usage frequency levels from CDL profiles"""
    NONE = "none"                           # No emoji usage
    MINIMAL = "minimal"                     # Rare, only for emphasis  
    LOW = "low"                            # Occasional usage
    MODERATE = "moderate"                   # Regular but thoughtful usage
    HIGH = "high"                          # Frequent, expressive usage
    SELECTIVE_SYMBOLIC = "selective_symbolic"  # Rare but deeply meaningful (Dream-style)


class EmojiCombinationType(Enum):
    """How emojis combine with text from CDL profiles"""
    EMOJI_ONLY = "emoji_only"                      # Just emoji responses
    TEXT_ONLY = "text_only"                        # No emojis at all
    TEXT_PLUS_EMOJI = "text_plus_emoji"            # Elena style: full text with emoji throughout
    TEXT_WITH_ACCENT_EMOJI = "text_with_accent_emoji"  # Marcus style: text with single accent emoji
    MINIMAL_SYMBOLIC_EMOJI = "minimal_symbolic_emoji"   # Dream style: rare symbolic emojis


@dataclass
class CDLEmojiProfile:
    """Character emoji personality from CDL digital_communication section"""
    character_name: str
    frequency: EmojiFrequency
    style: str
    age_demographic: str
    cultural_influence: str
    preferred_combination: EmojiCombinationType
    emoji_placement: str
    comment: str
    usage_patterns: Dict[str, Any]
    
    
@dataclass
class EmojiResponse:
    """Generated emoji+text response based on CDL personality"""
    response_text: str
    emoji_additions: List[str]
    placement_style: str
    confidence: float
    reasoning: str


class CDLEmojiPersonalityReader:
    """Reads CDL files and extracts digital communication emoji personalities"""
    
    def __init__(self, character_files_dir: str = "characters/examples"):
        self.character_files_dir = character_files_dir
        self.emoji_profiles: Dict[str, CDLEmojiProfile] = {}
        self.default_profile = self._create_default_profile()
        
    def load_character_emoji_profile(self, character_file: str) -> Optional[CDLEmojiProfile]:
        """Load emoji personality from a CDL character file"""
        try:
            file_path = os.path.join(self.character_files_dir, character_file)
            if not os.path.exists(file_path):
                file_path = character_file  # Try as absolute path
                
            with open(file_path, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
                
            # Extract digital_communication section
            digital_comm = cdl_data.get("character", {}).get("identity", {}).get("digital_communication")
            if not digital_comm:
                logger.debug(f"No digital_communication section found in {character_file}")
                return None
                
            emoji_personality = digital_comm.get("emoji_personality", {})
            usage_patterns = digital_comm.get("emoji_usage_patterns", {})
            
            profile = CDLEmojiProfile(
                character_name=cdl_data.get("character", {}).get("metadata", {}).get("name", "Unknown"),
                frequency=EmojiFrequency(emoji_personality.get("frequency", "moderate")),
                style=emoji_personality.get("style", "general"),
                age_demographic=emoji_personality.get("age_demographic", "millennial"),
                cultural_influence=emoji_personality.get("cultural_influence", "general"),
                preferred_combination=EmojiCombinationType(emoji_personality.get("preferred_combination", "text_with_accent_emoji")),
                emoji_placement=emoji_personality.get("emoji_placement", "end_of_message"),
                comment=emoji_personality.get("comment", ""),
                usage_patterns=usage_patterns
            )
            
            self.emoji_profiles[character_file] = profile
            logger.info("📱 Loaded CDL emoji profile for %s: %s frequency, %s style", 
                       profile.character_name, profile.frequency.value, profile.preferred_combination.value)
            logger.debug("📱 CDL EMOJI PROFILE: Full details - style=%s, age=%s, culture=%s, placement=%s", 
                        profile.style, profile.age_demographic, profile.cultural_influence, profile.emoji_placement)
            return profile
            
        except Exception as e:
            logger.error("Error loading emoji profile from %s: %s", character_file, e)
            return None
            
    def _create_default_profile(self) -> CDLEmojiProfile:
        """Create default emoji profile for characters without digital_communication section"""
        return CDLEmojiProfile(
            character_name="Default",
            frequency=EmojiFrequency.MODERATE,
            style="general",
            age_demographic="millennial",
            cultural_influence="general",
            preferred_combination=EmojiCombinationType.TEXT_WITH_ACCENT_EMOJI,
            emoji_placement="end_of_message",
            comment="Default profile for characters without specific digital communication preferences",
            usage_patterns={
                "excitement_level": {
                    "low": "Single emoji at end 👍",
                    "medium": "1-2 meaningful emojis 😊✨",
                    "high": "2-3 expressive emojis 🎉😄💫"
                },
                "topic_specific": {
                    "general": ["😊", "👍", "✨", "🎉", "❤️"]
                }
            }
        )


class CDLEmojiGenerator:
    """Generates emoji responses based on CDL character personalities"""
    
    def __init__(self, character_files_dir: str = "characters/examples"):
        self.profile_reader = CDLEmojiPersonalityReader(character_files_dir)
        self.current_profiles: Dict[str, CDLEmojiProfile] = {}
        
    def load_character_profile(self, character_file: str) -> CDLEmojiProfile:
        """Load and cache a character's emoji profile"""
        if character_file not in self.current_profiles:
            profile = self.profile_reader.load_character_emoji_profile(character_file)
            self.current_profiles[character_file] = profile or self.profile_reader.default_profile
        return self.current_profiles[character_file]
        
    def should_add_emojis(self, 
                         character_file: str,
                         user_message: str,
                         bot_response_text: str,
                         context: Optional[Dict[str, Any]] = None) -> Tuple[bool, float]:
        """
        Determine if emojis should be added based on CDL personality
        
        Returns:
            (should_add_emojis, confidence_score)
        """
        profile = self.load_character_profile(character_file)
        context = context or {}
        
        # Base probability from frequency setting
        frequency_probabilities = {
            EmojiFrequency.NONE: 0.0,
            EmojiFrequency.MINIMAL: 0.1,
            EmojiFrequency.LOW: 0.3,
            EmojiFrequency.MODERATE: 0.6,
            EmojiFrequency.HIGH: 0.8,
            EmojiFrequency.SELECTIVE_SYMBOLIC: 0.2  # Low frequency but high meaning
        }
        
        base_prob = frequency_probabilities[profile.frequency]
        
        # Adjust based on excitement level detected in message
        excitement_multiplier = self._detect_excitement_level(user_message, bot_response_text)
        
        # Adjust based on preferred combination type
        combination_multipliers = {
            EmojiCombinationType.EMOJI_ONLY: 0.9,  # Almost always emoji
            EmojiCombinationType.TEXT_ONLY: 0.0,   # Never emoji
            EmojiCombinationType.TEXT_PLUS_EMOJI: 0.9,  # Frequent emoji+text
            EmojiCombinationType.TEXT_WITH_ACCENT_EMOJI: 0.6,  # Moderate emoji accent
            EmojiCombinationType.MINIMAL_SYMBOLIC_EMOJI: 0.3   # Rare but meaningful
        }
        
        combination_mult = combination_multipliers[profile.preferred_combination]
        
        final_probability = base_prob * excitement_multiplier * combination_mult
        should_add = random.random() < final_probability
        
        logger.debug("📱 %s emoji decision: %s (prob: %.2f)", profile.character_name, should_add, final_probability)
        return should_add, final_probability
        
    def generate_emoji_response(self,
                              character_file: str,
                              user_message: str, 
                              bot_response_text: str,
                              excitement_level: str = "medium",
                              context: Optional[Dict[str, Any]] = None) -> EmojiResponse:
        """Generate emoji-enhanced response based on CDL personality"""
        profile = self.load_character_profile(character_file)
        context = context or {}
        
        logger.debug("🎭 CDL EMOJI: Starting emoji generation for character %s", profile.character_name)
        logger.debug("🎭 Emoji profile: frequency=%s, style=%s, combination=%s", 
                    profile.frequency.value, profile.style, profile.preferred_combination.value)
        logger.debug("🎭 Excitement level detected: %s", excitement_level)
        
        # Get excitement-appropriate emoji pattern
        excitement_patterns = profile.usage_patterns.get("excitement_level", {})
        # Remove unused pattern variable
        excitement_patterns.get(excitement_level, excitement_patterns.get("medium", ""))
        
        # DIRECT CDL EMOTION MAPPING: Use CDL data directly instead of calling taxonomy
        emotion_emojis = []
        if context and 'detected_emotion' in context:
            try:
                emotion = context['detected_emotion']
                emotion_emojis = self._get_emotion_specific_emojis(profile, emotion)
                logger.debug("🎭 CDL emotion-aware emojis for %s: %s", emotion, emotion_emojis)
            except Exception as e:
                logger.debug("🎭 Could not get CDL emotion-aware emojis: %s", e)
        
        # Extract topic-specific emojis and blend with emotion-aware ones
        topic_emojis = self._get_topic_emojis(profile, user_message, bot_response_text)
        
        # Combine topic and emotion emojis (emotion takes priority)
        combined_emojis = emotion_emojis[:2] + topic_emojis  # Max 2 emotion emojis + topic emojis
        logger.debug("🎭 Combined emojis (emotion + topic): %s", combined_emojis)
        
        # Generate based on combination preference using combined emojis
        if profile.preferred_combination == EmojiCombinationType.TEXT_PLUS_EMOJI:
            result = self._generate_text_plus_emoji(profile, bot_response_text, combined_emojis, excitement_level)
            logger.debug("🎭 Applied TEXT_PLUS_EMOJI style, added %d emojis", len(result.emoji_additions))
        elif profile.preferred_combination == EmojiCombinationType.TEXT_WITH_ACCENT_EMOJI:
            result = self._generate_text_with_accent(profile, bot_response_text, combined_emojis, excitement_level)
            logger.debug("🎭 Applied TEXT_WITH_ACCENT_EMOJI style, added %d emojis", len(result.emoji_additions))
        elif profile.preferred_combination == EmojiCombinationType.MINIMAL_SYMBOLIC_EMOJI:
            result = self._generate_minimal_symbolic(profile, bot_response_text, combined_emojis, excitement_level)
            logger.debug("🎭 Applied MINIMAL_SYMBOLIC_EMOJI style, added %d emojis", len(result.emoji_additions))
        elif profile.preferred_combination == EmojiCombinationType.EMOJI_ONLY:
            result = self._generate_emoji_only(profile, bot_response_text, combined_emojis, excitement_level)
            logger.debug("🎭 Applied EMOJI_ONLY style, added %d emojis", len(result.emoji_additions))
        else:
            result = EmojiResponse(
                response_text=bot_response_text,
                emoji_additions=[],
                placement_style="none",
                confidence=0.0,
                reasoning="TEXT_ONLY preference"
            )
            logger.debug("🎭 Applied TEXT_ONLY style - no emojis added")
        
        logger.debug("🎭 CDL EMOJI: Final response confidence: %.2f, reasoning: %s", 
                    result.confidence, result.reasoning)
        
        return result
            
    def _detect_excitement_level(self, user_message: str, bot_response: str) -> float:
        """Detect excitement level from message content"""
        excitement_indicators = ["!", "amazing", "wow", "incredible", "awesome", "love", "excited"]
        question_indicators = ["?", "how", "what", "why", "when"]
        
        combined_text = (user_message + " " + bot_response).lower()
        
        excitement_count = sum(1 for indicator in excitement_indicators if indicator in combined_text)
        question_count = sum(1 for indicator in question_indicators if indicator in combined_text)
        
        if excitement_count >= 2:
            return 1.5  # High excitement
        elif excitement_count >= 1 or question_count >= 1:
            return 1.2  # Medium excitement
        else:
            return 1.0  # Normal level
            
    def _get_topic_emojis(self, profile: CDLEmojiProfile, user_message: str, bot_response: str) -> List[str]:
        """Extract relevant topic emojis based on message content"""
        topic_specific = profile.usage_patterns.get("topic_specific", {})
        combined_text = (user_message + " " + bot_response).lower()
        
        relevant_emojis = []
        for topic, emojis in topic_specific.items():
            if topic in combined_text or any(word in combined_text for word in topic.split("_")):
                relevant_emojis.extend(emojis[:2])  # Max 2 per topic
                
        return relevant_emojis[:4]  # Max 4 total topic emojis
    
    def _get_emotion_specific_emojis(self, profile: CDLEmojiProfile, emotion: str) -> List[str]:
        """Get emotion-specific emojis directly from CDL data"""
        emotion_lower = emotion.lower()
        
        # Map core emotions to CDL topic categories that express those emotions
        emotion_to_topics = {
            'joy': ['affection_warmth', 'science_discovery', 'excitement'],
            'sadness': ['disappointment', 'melancholy'],  
            'anger': ['frustration', 'strong_disagreement'],
            'surprise': ['science_discovery', 'wonder', 'amazement'],
            'fear': ['worry', 'concern', 'anxiety'],
            'disgust': ['disapproval', 'strong_disagreement'], 
            'neutral': ['general', 'acknowledgment']
        }
        
        # Get relevant topic categories for this emotion
        relevant_topics = emotion_to_topics.get(emotion_lower, ['general'])
        
        # Extract emojis from matching CDL topic categories
        emotion_emojis = []
        topic_specific = profile.usage_patterns.get("topic_specific", {})
        
        for topic_key, emojis in topic_specific.items():
            # Check if this topic matches our emotion categories
            if any(topic in topic_key.lower() for topic in relevant_topics):
                emotion_emojis.extend(emojis[:2])  # Max 2 per matching topic
        
        # Fallback to general emojis if no emotion-specific ones found
        if not emotion_emojis and 'general' in topic_specific:
            emotion_emojis = topic_specific['general'][:2]
        
        return emotion_emojis[:3]  # Max 3 emotion-specific emojis
        
    def _generate_text_plus_emoji(self, profile: CDLEmojiProfile, text: str, topic_emojis: List[str], excitement: str) -> EmojiResponse:
        """Elena style: Enthusiastic text with emojis throughout"""
        emoji_count = {"low": 1, "medium": 2, "high": 3}.get(excitement, 2)
        selected_emojis = random.sample(topic_emojis, min(emoji_count, len(topic_emojis)))
        
        # Add emojis throughout the text
        enhanced_text = text
        if selected_emojis:
            # Add emoji at end
            enhanced_text += " " + "".join(selected_emojis)
            
        return EmojiResponse(
            response_text=enhanced_text,
            emoji_additions=selected_emojis,
            placement_style="throughout_and_end",
            confidence=0.8,
            reasoning=f"CDL {profile.character_name} text_plus_emoji style"
        )
        
    def _generate_text_with_accent(self, profile: CDLEmojiProfile, text: str, topic_emojis: List[str], excitement: str) -> EmojiResponse:
        """Marcus style: Text with single meaningful emoji accent"""
        # Note: excitement parameter available for future enhancement
        _ = excitement  # Acknowledge parameter for future use
        # Select one most relevant emoji
        if topic_emojis:
            selected_emoji = [random.choice(topic_emojis)]
            enhanced_text = text + " " + selected_emoji[0]
        else:
            # Fallback to general positive emoji
            general_emojis = ["👍", "✨", "💡", "🤔"]
            selected_emoji = [random.choice(general_emojis)]
            enhanced_text = text + " " + selected_emoji[0]
            
        return EmojiResponse(
            response_text=enhanced_text,
            emoji_additions=selected_emoji,
            placement_style="end_accent",
            confidence=0.7,
            reasoning=f"CDL {profile.character_name} text_with_accent style"
        )
        
    def _generate_minimal_symbolic(self, profile: CDLEmojiProfile, text: str, topic_emojis: List[str], excitement: str) -> EmojiResponse:
        """Dream style: Rare but deeply symbolic emoji"""
        if excitement == "high" and topic_emojis:
            # Only add emoji for high excitement with relevant topics
            symbolic_emoji = [random.choice(topic_emojis)]
            enhanced_text = text + " " + symbolic_emoji[0]
            return EmojiResponse(
                response_text=enhanced_text,
                emoji_additions=symbolic_emoji,
                placement_style="symbolic_end",
                confidence=0.9,
                reasoning=f"CDL {profile.character_name} high-meaning symbolic emoji"
            )
        else:
            # Most of the time, no emoji
            return EmojiResponse(
                response_text=text,
                emoji_additions=[],
                placement_style="pure_text",
                confidence=0.6,
                reasoning=f"CDL {profile.character_name} minimal symbolic - threshold not met"
            )
            
    def _generate_emoji_only(self, profile: CDLEmojiProfile, text: str, topic_emojis: List[str], excitement: str) -> EmojiResponse:
        """Pure emoji response (for very simple acknowledgments)"""
        # Note: text parameter available for future content analysis
        _ = text  # Acknowledge parameter for future use
        emoji_count = {"low": 1, "medium": 2, "high": 3}.get(excitement, 2)
        
        if topic_emojis:
            selected_emojis = random.sample(topic_emojis, min(emoji_count, len(topic_emojis)))
        else:
            general_emojis = ["😊", "👍", "✨", "❤️"]
            selected_emojis = random.sample(general_emojis, min(emoji_count, len(general_emojis)))
            
        emoji_response = "".join(selected_emojis)
        
        return EmojiResponse(
            response_text=emoji_response,
            emoji_additions=selected_emojis,
            placement_style="emoji_only",
            confidence=0.9,
            reasoning=f"CDL {profile.character_name} emoji_only response"
        )


# Factory function for integration
def create_cdl_emoji_generator(character_files_dir: str = "characters/examples") -> CDLEmojiGenerator:
    """Factory function to create CDL emoji generator"""
    return CDLEmojiGenerator(character_files_dir)


if __name__ == "__main__":
    # Quick test
    generator = create_cdl_emoji_generator()
    
    # Test Elena (high frequency, text+emoji)
    elena_response = generator.generate_emoji_response(
        "elena-rodriguez.json",
        "Tell me about whales!",
        "Whales are absolutely incredible creatures!",
        excitement_level="high"
    )
    print(f"Elena: {elena_response.response_text}")
    
    # Test Marcus (moderate frequency, text+accent)
    marcus_response = generator.generate_emoji_response(
        "marcus-thompson.json", 
        "How does AI work?",
        "AI uses neural networks to process patterns in data.",
        excitement_level="medium"
    )
    print(f"Marcus: {marcus_response.response_text}")
    
    # Test Dream (minimal symbolic)
    dream_response = generator.generate_emoji_response(
        "dream_of_the_endless.json",
        "What do you see in my dreams?",
        "I see the endless tapestry of mortal hopes.",
        excitement_level="high" 
    )
    print(f"Dream: {dream_response.response_text}")