"""
CDL Integration with AI Pipeline Prompt System
"""

import logging
from typing import Dict, Optional
from pathlib import Path

from src.characters.models.character import Character
from src.characters.cdl.parser import load_character

logger = logging.getLogger(__name__)


class CDLAIPromptIntegration:
    """Integrates CDL character definitions with AI pipeline results."""

    def __init__(self, vector_memory_manager=None):
        self.memory_manager = vector_memory_manager
        self.characters_cache = {}

    async def create_character_aware_prompt(
        self,
        character_file: str,
        user_id: str,
        message_content: str,
        pipeline_result=None
    ) -> str:
        """Create a character-aware prompt."""
        try:
            character = await self.load_character(character_file)
            logger.info(f"Loaded CDL character: {character.identity.name}")

            # Build comprehensive character prompt with personality details
            personality_values = getattr(character.personality, 'values', [])
            speech_patterns = getattr(character.identity.voice, 'speech_patterns', [])
            favorite_phrases = getattr(character.identity.voice, 'favorite_phrases', [])
            quirks = getattr(character.personality, 'quirks', [])
            
            prompt = f"""You are {character.identity.name}, a {character.identity.age}-year-old {character.identity.occupation} in {character.identity.location}.

PERSONALITY:
{character.identity.description}

VOICE & COMMUNICATION STYLE:
- Tone: {getattr(character.identity.voice, 'tone', 'Natural and authentic')}
- Pace: {getattr(character.identity.voice, 'pace', 'Normal conversational pace')}
- Vocabulary: {getattr(character.identity.voice, 'vocabulary_level', 'Natural vocabulary')}"""

            if speech_patterns:
                prompt += f"\n- Speech patterns: {', '.join(speech_patterns[:3])}"
            
            if favorite_phrases:
                prompt += f"\n- Favorite phrases: {', '.join(favorite_phrases[:3])}"

            if personality_values:
                prompt += f"\n\nCORE VALUES: {', '.join(personality_values[:4])}"

            if quirks:
                prompt += f"\n\nPERSONALITY QUIRKS: {', '.join(quirks[:3])}"

            # 🎭 EMOTION INTEGRATION: Add real-time emotional intelligence to character prompt
            if pipeline_result:
                prompt += "\n\nREAL-TIME CONTEXT AWARENESS:"
                
                # Add emotional state awareness
                if pipeline_result.emotional_state:
                    prompt += f"\n- User's current emotional state: {pipeline_result.emotional_state}"
                
                if pipeline_result.mood_assessment and isinstance(pipeline_result.mood_assessment, dict):
                    primary_emotion = pipeline_result.mood_assessment.get('primary_emotion')
                    confidence = pipeline_result.mood_assessment.get('confidence', 0)
                    if primary_emotion and confidence > 0.5:
                        prompt += f"\n- Detected emotion: {primary_emotion} (confidence: {confidence:.1f})"
                        
                        # Add emotion-appropriate response guidance
                        emotion_guidance = {
                            'joy': 'Share in their positive energy and enthusiasm',
                            'excitement': 'Match their enthusiasm while staying authentic to your character',
                            'sadness': 'Show empathy and support while remaining genuine',
                            'frustration': 'Acknowledge their feelings and offer perspective',
                            'anxiety': 'Provide calm, reassuring responses',
                            'anger': 'Stay calm and avoid escalating the situation',
                            'fear': 'Offer gentle reassurance and support',
                            'neutral': 'Maintain your natural conversational style'
                        }
                        
                        guidance = emotion_guidance.get(primary_emotion, 'Respond naturally and authentically')
                        prompt += f"\n- Response approach: {guidance}"
                
                # Add personality context if available
                if pipeline_result.personality_profile and isinstance(pipeline_result.personality_profile, dict):
                    personality_insights = pipeline_result.personality_profile.get('personality_summary')
                    if personality_insights:
                        prompt += f"\n- User personality insights: {personality_insights[:100]}..."
                
                # Add conversation context
                if pipeline_result.enhanced_context and isinstance(pipeline_result.enhanced_context, dict):
                    conversation_mode = pipeline_result.enhanced_context.get('conversation_mode')
                    if conversation_mode:
                        prompt += f"\n- Conversation mode: {conversation_mode}"
                        
                prompt += f"\n\nADAPT your response style to be emotionally appropriate while staying true to {character.identity.name}'s personality."


            prompt += f"""

CRITICAL INSTRUCTIONS:
- You are a {character.identity.occupation}, not a poet or mystical character
- Use normal, conversational language appropriate for your profession
- Avoid overly poetic, mystical, or fantasy-style language unless it genuinely fits your character
- Be enthusiastic about your work but use authentic, professional language
- Reference topics and terminology relevant to your field and background
- Speak like a real person having a conversation

Respond as {character.identity.name}:"""

            return prompt

        except Exception as e:
            logger.error(f"CDL integration failed: {e}")
            raise

    async def load_character(self, character_file: str) -> Character:
        """Load a character from CDL file."""
        try:
            if character_file in self.characters_cache:
                return self.characters_cache[character_file]

            character_path = Path("characters") / character_file
            if not character_path.exists():
                character_path = Path(character_file)

            character = load_character(character_path)
            self.characters_cache[character_file] = character
            return character

        except Exception as e:
            logger.error(f"Failed to load character {character_file}: {e}")
            raise


async def load_character_definitions(characters_dir: str = "characters") -> Dict[str, Character]:
    """Load all character definitions from directory."""
    characters = {}
    characters_path = Path(characters_dir)

    if not characters_path.exists():
        logger.warning(f"Characters directory not found: {characters_dir}")
        return characters

    for file_path in characters_path.rglob("*.json"):
        try:
            character_name = file_path.stem
            character = load_character(file_path)
            characters[character_name] = character
            logger.info(f"Loaded character: {character_name}")
        except Exception as e:
            logger.error(f"Failed to load character from {file_path}: {e}")

    return characters