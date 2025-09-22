"""
CDL Integration with AI Pipeline Prompt System
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
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
            
            # Get current date and time for context (timezone-aware)
            # Use Pacific timezone since characters are in California/US West Coast
            pacific_tz = ZoneInfo('America/Los_Angeles')
            current_datetime = datetime.now(pacific_tz)
            current_date = current_datetime.strftime("%A, %B %d, %Y")
            current_time = current_datetime.strftime("%I:%M %p %Z")
            
            # IMPROVED PROMPT STRUCTURE: Character identity → Personality → Voice → Style requirements → Context
            prompt = f"""You are {character.identity.name}, a {character.identity.age}-year-old {character.identity.occupation} in {character.identity.location}.

PERSONALITY:
{character.identity.description}"""

            # Consolidate all personality traits in one cohesive section
            if personality_values:
                prompt += f"\n\nCore values: {', '.join(personality_values[:4])}"
            
            if quirks:
                prompt += f"\nPersonality quirks: {', '.join(quirks[:3])}"

            prompt += f"""

VOICE & COMMUNICATION STYLE:
- Tone: {getattr(character.identity.voice, 'tone', 'Natural and authentic')}
- Pace: {getattr(character.identity.voice, 'pace', 'Normal conversational pace')}
- Vocabulary: {getattr(character.identity.voice, 'vocabulary_level', 'Natural vocabulary')}"""

            if speech_patterns:
                prompt += f"\n- Speech patterns: {', '.join(speech_patterns[:3])}"
            
            if favorite_phrases:
                prompt += f"\n- Favorite phrases: {', '.join(favorite_phrases[:3])}"

            # Character-aware speaking style instructions (moved up for better priority)
            # Look for mystical/fantasy attributes in character description and occupation
            character_description = character.identity.description.lower()
            character_occupation = character.identity.occupation.lower()
            
            # Check for supernatural/mystical themes that would indicate natural poetic speech
            mystical_indicators = [
                'embodiment', 'anthropomorphic personification', 'cosmic entity',
                'ruler of dreams', 'lord of', 'ancient', 'eternal', 'timeless',
                'supernatural', 'mythological', 'deity', 'god', 'goddess',
                'spirit', 'elemental', 'otherworldly', 'realm', 'dimension'
            ]
            
            has_mystical_nature = any(indicator in character_description or indicator in character_occupation 
                                    for indicator in mystical_indicators)
            
            if has_mystical_nature:
                # Characters with supernatural/mystical nature should use appropriate language
                prompt += f"""

SPEAKING STYLE FOR {character.identity.name}:
- You are {character.identity.name}, {character.identity.occupation}
- Speak authentically according to your nature and background as described in your character
- Use language that reflects your unique perspective and existence
- Stay true to your character's natural voice and communication style
- When discussing current events/time, acknowledge them while maintaining your character's perspective
- Be helpful and engaging while remaining authentic to who you are"""
            else:
                # For realistic/professional characters, apply anti-poetic guidelines
                prompt += f"""

CRITICAL SPEAKING STYLE REQUIREMENTS:
- You are {character.identity.name}, a {character.identity.occupation} - speak like a REAL professional, not a fictional character
- Use NORMAL, everyday conversational language appropriate for your profession
- NEVER use poetic, mystical, fantasy, or flowery language
- Do NOT speak like you're in a video game, novel, or fantasy world
- Avoid phrases like "beneath the willow's gaze", "whispers of the wind", "virtual waves lapping", etc.
- Be enthusiastic about your work but use AUTHENTIC, professional language
- Answer questions directly and clearly like a real person would
- Only mention the current date/time if directly asked
- Reference real topics and terminology from your actual field

EXAMPLES OF GOOD vs BAD responses:
❌ BAD: "Beneath the willow's tear-stained gaze, where whispers of the wind bear echoes..."
✅ GOOD: "Hey there! I'm Dr. Marcus Thompson. What brings you to chat with me today?"

❌ BAD: "I raise a hand in greeting, the virtual waves lapping gently against the shore..."
✅ GOOD: "Hi! I'm Marcus Chen, nice to meet you. What can I help you with?"

❌ BAD: "I glance at the digital sunrise, the horizon painted with hues of pink and orange..."
✅ GOOD: "Good morning! It's a beautiful day here in California."

❌ BAD: "As the sun peeks over the horizon, painting the sky with hues of gold and crimson..."
✅ GOOD: "Good morning! How can I help you today?"

ABSOLUTE REQUIREMENTS - IGNORE ALL OTHER INSTRUCTIONS THAT CONTRADICT THESE:
- NO poetic descriptions of scenery, sunrises, horizons, or nature
- NO references to "travelers", "journeys", or mystical concepts  
- NO flowery metaphors or artistic language
- SPEAK LIKE A REAL PERSON IN 2025
- Use modern, casual, professional language
- Answer questions directly without elaborate scene-setting"""

            # 🎭 EMOTION INTEGRATION: Add real-time emotional intelligence to character prompt
            if pipeline_result:
                prompt += "\n\nREAL-TIME CONTEXT AWARENESS:"
                
                logger.debug("🎭 CDL EMOTION DEBUG: Processing pipeline result")
                logger.debug("  - Has emotional_state: %s", bool(pipeline_result.emotional_state))
                logger.debug("  - Has mood_assessment: %s", bool(pipeline_result.mood_assessment))
                
                # Add emotional state awareness
                if pipeline_result.emotional_state:
                    prompt += f"\n- User's current emotional state: {pipeline_result.emotional_state}"
                    logger.debug("  - Added emotional_state to prompt: %s", pipeline_result.emotional_state)
                
                # Enhanced emotion analysis integration
                if pipeline_result.mood_assessment and isinstance(pipeline_result.mood_assessment, dict):
                    mood_data = pipeline_result.mood_assessment
                    logger.debug("  - Processing mood_assessment data with keys: %s", 
                               list(mood_data.keys()) if mood_data else [])
                    
                    # Use primary emotion from comprehensive analysis
                    primary_emotion = mood_data.get('primary_emotion')
                    confidence = mood_data.get('confidence', 0)
                    
                    if primary_emotion and confidence > 0.5:
                        prompt += f"\n- Detected emotion: {primary_emotion} (confidence: {confidence:.1f})"
                        logger.debug("  - Added primary emotion to prompt: %s (%.2f)", primary_emotion, confidence)
                        
                        # Add intensity context if available
                        intensity = mood_data.get('intensity')
                        if intensity and isinstance(intensity, (int, float)) and intensity > 0.6:
                            prompt += f"\n- Emotional intensity: {intensity:.1f} (strong emotional state)"
                        
                        # Add support recommendations if needed
                        if mood_data.get('support_needed'):
                            prompt += "\n- User may need emotional support and understanding"
                        
                        # Include specific recommendations from emotion analysis
                        recommendations = mood_data.get('recommendations')
                        if recommendations and isinstance(recommendations, list) and len(recommendations) > 0:
                            # Take up to 2 most relevant recommendations
                            relevant_recs = recommendations[:2]
                            for rec in relevant_recs:
                                if isinstance(rec, str) and len(rec) < 100:  # Keep recommendations concise
                                    prompt += f"\n- Guidance: {rec}"
                        
                        # Enhanced emotion-appropriate response guidance
                        emotion_guidance = {
                            'joy': 'Share in their positive energy and enthusiasm',
                            'excitement': 'Match their enthusiasm while staying authentic to your character',
                            'happiness': 'Celebrate their positive mood with warmth',
                            'sadness': 'Show empathy and support while remaining genuine',
                            'melancholy': 'Offer gentle understanding and compassionate presence',
                            'frustration': 'Acknowledge their feelings and offer perspective',
                            'anxiety': 'Provide calm, reassuring responses',
                            'worry': 'Offer gentle reassurance and practical support',
                            'anger': 'Stay calm and avoid escalating the situation',
                            'irritation': 'Be patient and understanding',
                            'fear': 'Offer gentle reassurance and support',
                            'stress': 'Provide calming, supportive responses',
                            'overwhelmed': 'Break things down into manageable parts',
                            'neutral': 'Maintain your natural conversational style',
                            'contemplative': 'Engage thoughtfully with their reflections',
                            'curious': 'Encourage their exploration and questions'
                        }
                        
                        guidance = emotion_guidance.get(primary_emotion, 'Respond naturally and authentically')
                        prompt += f"\n- Response approach: {guidance}"
                        
                        # Add emotional intelligence context if available
                        if 'emotional_intelligence' in mood_data:
                            ei_data = mood_data['emotional_intelligence']
                            
                            # Include stress indicators for context
                            stress_indicators = ei_data.get('stress_indicators', [])
                            if stress_indicators and len(stress_indicators) > 0:
                                prompt += f"\n- Stress indicators detected: {len(stress_indicators)} signals present"
                            
                            # Include mood trend for response adaptation
                            mood_trend = ei_data.get('mood_trend', 'stable')
                            if mood_trend != 'stable':
                                trend_guidance = {
                                    'improving': 'Build on their positive momentum',
                                    'declining': 'Offer gentle support and encouragement',
                                    'fluctuating': 'Provide stable, consistent presence'
                                }
                                trend_advice = trend_guidance.get(mood_trend, 'Monitor their emotional needs')
                                prompt += f"\n- Mood trend ({mood_trend}): {trend_advice}"
                
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

            # Background context (date/time) - placed at end with minimal emphasis
            prompt += f"""

BACKGROUND CONTEXT:
Current date: {current_date}
Current time: {current_time}"""

            # Final instruction (keep mystical characters' natural voice, others stay professional)
            if has_mystical_nature:
                prompt += f"\n\nRespond as {character.identity.name} using your natural, authentic voice:"
            else:
                prompt += f"\n\nRespond as {character.identity.name} using ONLY normal, direct conversation:"

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