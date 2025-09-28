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
        pipeline_result=None,
        user_name: Optional[str] = None
    ) -> str:
        """Create a character-aware prompt."""
        try:
            # AI identity questions are now handled naturally through CDL character responses
            # No more dirty filter patterns - let characters be authentic
            
            character = await self.load_character(character_file)
            logger.info(f"Loaded CDL character: {character.identity.name}")

            # Check for user's preferred name in memory
            preferred_name = None
            if self.memory_manager:
                try:
                    from src.utils.user_preferences import get_user_preferred_name
                    preferred_name = await get_user_preferred_name(user_id, self.memory_manager)
                except Exception as e:
                    logger.debug(f"Could not retrieve preferred name: {e}")

            # Determine the best name to use (priority: preferred > user_name > User)
            display_name = preferred_name or user_name or "User"
            
            logger.info(f"Using display name: {display_name} (preferred: {preferred_name}, discord: {user_name})")
            
            # CRITICAL FIX: Retrieve relevant memories and conversation history
            relevant_memories = []
            conversation_history = []
            
            if self.memory_manager:
                try:
                    # Retrieve relevant memories for context
                    relevant_memories = await self.memory_manager.retrieve_relevant_memories(
                        user_id=user_id,
                        query=message_content,
                        limit=10
                    )
                    logger.info(f"🧠 CDL-MEMORY: Retrieved {len(relevant_memories)} relevant memories")
                    
                    # Retrieve recent conversation history
                    conversation_history = await self.memory_manager.get_conversation_history(
                        user_id=user_id,
                        limit=5
                    )
                    logger.info(f"🧠 CDL-MEMORY: Retrieved {len(conversation_history)} conversation entries")
                    
                except Exception as e:
                    logger.warning(f"Could not retrieve memory context: {e}")
                    relevant_memories = []
                    conversation_history = []

            # NEW: Query bot's LLM-powered self-knowledge for personal questions
            self_knowledge_result = None
            if self.memory_manager:
                try:
                    from src.memory.llm_powered_bot_memory import create_llm_powered_bot_memory
                    from src.llm.llm_protocol import create_llm_client
                    
                    # Extract bot name from character file
                    bot_name = Path(character_file).stem.split('-')[0] if '-' in character_file else 'bot'
                    
                    # Create LLM client and LLM-powered bot memory
                    llm_client = create_llm_client()  # Use default LLM client
                    llm_bot_memory = create_llm_powered_bot_memory(bot_name, llm_client, self.memory_manager)
                    
                    # Query for personal knowledge relevant to the message using LLM intelligence
                    self_knowledge_result = await llm_bot_memory.query_personal_knowledge_with_llm(message_content, limit=3)
                    
                    if self_knowledge_result and self_knowledge_result.get("found_relevant_info"):
                        relevant_items = self_knowledge_result.get("relevant_items", [])
                        logger.info(f"🧠 LLM-SELF-KNOWLEDGE: Found {len(relevant_items)} relevant personal knowledge entries")
                    
                except Exception as e:
                    logger.warning(f"Could not retrieve LLM-powered self-knowledge: {e}")
                    self_knowledge_result = None

            # Build comprehensive character prompt with personality details
            personality_values = getattr(character.personality, 'values', [])
            speech_patterns = getattr(character.identity.voice, 'speech_patterns', [])
            favorite_phrases = getattr(character.identity.voice, 'favorite_phrases', [])
            quirks = getattr(character.personality, 'quirks', [])
            
            # PRIORITY 1: Extract Big Five personality model from raw character data
            big_five_data = None
            life_phases_data = None
            try:
                import json
                character_file_path = Path(character_file)
                if character_file_path.exists():
                    with open(character_file_path, 'r') as f:
                        raw_character_data = json.load(f)
                        personality_section = raw_character_data.get('character', {}).get('personality', {})
                        big_five_data = personality_section.get('big_five', {})
                        
                        # PRIORITY 2: Extract life phases for backstory context
                        background_section = raw_character_data.get('character', {}).get('background', {})
                        life_phases_data = background_section.get('life_phases', [])
                        
                        logger.info(f"🧠 CDL-ENHANCED: Loaded Big Five scores and {len(life_phases_data)} life phases for {character.identity.name}")
            except Exception as e:
                logger.warning(f"Could not extract enhanced CDL data: {e}")
            
            # Get current date and time for context (timezone-aware)
            # Use character's timezone if specified, otherwise default to Pacific
            character_timezone = getattr(character.identity, 'timezone', 'America/Los_Angeles')
            try:
                character_tz = ZoneInfo(character_timezone)
            except (KeyError, ValueError):
                logger.warning("Invalid timezone %s, using Pacific Time", character_timezone)
                character_tz = ZoneInfo('America/Los_Angeles')
                
            current_datetime = datetime.now(character_tz)
            current_date = current_datetime.strftime("%A, %B %d, %Y")
            current_time = current_datetime.strftime("%I:%M %p %Z")
            
            # Check for custom introduction override
            custom_introduction = getattr(character.identity, 'custom_introduction', None)
            
            # IMPROVED PROMPT STRUCTURE: Character identity → Personality → Voice → Style requirements → Context
            if custom_introduction:
                prompt = f"""IDENTITY:
{custom_introduction}

PERSONALITY:
{character.identity.description}"""
            else:
                prompt = f"""You are {character.identity.name}, a {character.identity.age}-year-old {character.identity.occupation} in {character.identity.location}.

PERSONALITY:
{character.identity.description}"""

            # Consolidate all personality traits in one cohesive section
            if personality_values:
                prompt += f"\n\nCore values: {', '.join(personality_values[:4])}"
            
            if quirks:
                prompt += f"\nPersonality quirks: {', '.join(quirks[:3])}"
            
            # PRIORITY 1: Add Big Five personality model for psychological authenticity
            if big_five_data:
                prompt += f"\n\nBig Five Personality Profile:"
                if big_five_data.get('openness'):
                    openness_level = "very high" if big_five_data['openness'] > 0.8 else "high" if big_five_data['openness'] > 0.6 else "moderate"
                    prompt += f"\n- Openness to experience: {openness_level} ({big_five_data['openness']}) - curious, creative, intellectual"
                if big_five_data.get('conscientiousness'):
                    conscientiousness_level = "very high" if big_five_data['conscientiousness'] > 0.8 else "high" if big_five_data['conscientiousness'] > 0.6 else "moderate"
                    prompt += f"\n- Conscientiousness: {conscientiousness_level} ({big_five_data['conscientiousness']}) - organized, disciplined, reliable"
                if big_five_data.get('extraversion'):
                    extraversion_level = "high" if big_five_data['extraversion'] > 0.7 else "moderate" if big_five_data['extraversion'] > 0.4 else "low"
                    prompt += f"\n- Extraversion: {extraversion_level} ({big_five_data['extraversion']}) - social energy and outgoingness"
                if big_five_data.get('agreeableness'):
                    agreeableness_level = "very high" if big_five_data['agreeableness'] > 0.8 else "high" if big_five_data['agreeableness'] > 0.6 else "moderate"
                    prompt += f"\n- Agreeableness: {agreeableness_level} ({big_five_data['agreeableness']}) - cooperative, trusting, helpful"
                if big_five_data.get('neuroticism'):
                    neuroticism_level = "low" if big_five_data['neuroticism'] < 0.4 else "moderate" if big_five_data['neuroticism'] < 0.7 else "high"
                    prompt += f"\n- Emotional stability: {neuroticism_level} neuroticism ({big_five_data['neuroticism']}) - calm, resilient, even-tempered"

            # Extract communication style from the correct location
            prompt += f"""

VOICE & COMMUNICATION STYLE:"""

            # Access communication style from raw character data for accuracy
            try:
                import json
                character_file_path = Path(character_file)
                if character_file_path.exists():
                    with open(character_file_path, 'r') as f:
                        raw_character_data = json.load(f)
                        comm_style_data = raw_character_data.get('character', {}).get('personality', {}).get('communication_style', {})
                        
                        if comm_style_data:
                            prompt += f"""
- Tone: {comm_style_data.get('tone', 'natural')}
- Formality: {comm_style_data.get('formality', 'moderate')}
- Humor: {comm_style_data.get('humor', 'situational')}
- Empathy level: {comm_style_data.get('empathy_level', 'moderate')}
- Directness: {comm_style_data.get('directness', 'balanced')}"""
                        else:
                            # Fallback to parsed character object
                            comm_style = getattr(character.personality, 'communication_style', None)
                            if comm_style:
                                prompt += f"""
- Tone: {getattr(comm_style, 'tone', 'natural')}
- Formality: {getattr(comm_style, 'formality', 'moderate')}
- Humor: {getattr(comm_style, 'humor', 'situational')}
- Empathy level: {getattr(comm_style, 'empathy_level', 'moderate')}
- Directness: {getattr(comm_style, 'directness', 'balanced')}"""
                            else:
                                prompt += f"""
- Tone: {getattr(character.identity.voice, 'tone', 'Natural and authentic')}
- Pace: {getattr(character.identity.voice, 'pace', 'Normal conversational pace')}
- Vocabulary: {getattr(character.identity.voice, 'vocabulary_level', 'Natural vocabulary')}"""
            except Exception as e:
                logger.warning(f"Could not extract communication style: {e}")
                # Fallback to basic voice attributes
                prompt += f"""
- Tone: {getattr(character.identity.voice, 'tone', 'Natural and authentic')}
- Pace: {getattr(character.identity.voice, 'pace', 'Normal conversational pace')}
- Vocabulary: {getattr(character.identity.voice, 'vocabulary_level', 'Natural vocabulary')}"""

            # Add speech patterns from the character data
            try:
                # Access speech patterns from the raw character data
                import json
                character_file_path = Path(character_file)
                if character_file_path.exists():
                    with open(character_file_path, 'r') as f:
                        raw_character_data = json.load(f)
                        # Try both possible locations for speech_patterns
                        speech_patterns_data = raw_character_data.get('character', {}).get('speech_patterns', {})
                        if not speech_patterns_data:
                            # Fallback: check voice section for speech patterns (array format)
                            voice_patterns = raw_character_data.get('character', {}).get('identity', {}).get('voice', {}).get('speech_patterns', [])
                            if voice_patterns:
                                # Convert array format to vocabulary structure for consistency
                                speech_patterns_data = {
                                    'vocabulary': {
                                        'preferred_words': [],
                                        'avoided_words': []
                                    },
                                    'sentence_structure': f"Speech patterns: {'; '.join(voice_patterns[:3])}"
                                }
                        
                        if speech_patterns_data:
                            vocabulary_info = speech_patterns_data.get('vocabulary', {})
                            if vocabulary_info:
                                preferred_words = vocabulary_info.get('preferred_words', [])
                                avoided_words = vocabulary_info.get('avoided_words', [])
                                if preferred_words:
                                    prompt += f"\n- Preferred words: {', '.join(preferred_words[:5])}"
                                if avoided_words:
                                    prompt += f"\n- Avoid words: {', '.join(avoided_words[:5])}"
                            
                            sentence_structure = speech_patterns_data.get('sentence_structure')
                            if sentence_structure:
                                prompt += f"\n- Sentence style: {sentence_structure}"
                                
                            response_length = speech_patterns_data.get('response_length')
                            if response_length:
                                prompt += f"\n- Response style: {response_length}"
            except Exception as e:
                logger.warning(f"Could not extract speech patterns: {e}")

            if speech_patterns:
                prompt += f"\n- Speech patterns: {', '.join(speech_patterns[:3])}"
            
            if favorite_phrases:
                prompt += f"\n- Favorite phrases: {', '.join(favorite_phrases[:3])}"

            # Character-aware speaking style instructions (moved up for better priority)
            # Check for custom speaking instructions override first, then fall back to categories
            speaking_style_category = None
            custom_speaking_instructions = None
            try:
                import json
                character_file_path = Path(character_file)
                if character_file_path.exists():
                    with open(character_file_path, 'r') as f:
                        raw_character_data = json.load(f)
                        # Standardized location: character.personality.communication_style
                        comm_style = raw_character_data.get('character', {}).get('personality', {}).get('communication_style', {})
                        
                        # Check for custom override first
                        custom_speaking_instructions = comm_style.get('custom_speaking_instructions')
                        
                        # Fall back to category system
                        speaking_style_category = comm_style.get('category', 'default')
            except Exception as e:
                logger.warning(f"Could not check speaking style category: {e}")
                speaking_style_category = 'default'
            
            # Apply custom instructions if provided, otherwise use category templates
            if custom_speaking_instructions:
                prompt += f"""

CUSTOM SPEAKING STYLE FOR {character.identity.name}:"""
                for instruction in custom_speaking_instructions:
                    prompt += f"""
- {instruction}"""
            else:
                # Use category-based templates when no custom instructions provided
                if speaking_style_category == 'mystical' or speaking_style_category == 'supernatural':
                    # Characters with supernatural/mystical nature should use appropriate language
                    prompt += f"""

MYSTICAL/SUPERNATURAL SPEAKING STYLE FOR {character.identity.name}:
- You are {character.identity.name}, {character.identity.occupation}
- Speak authentically according to your supernatural nature and mythological background
- Use language that reflects your unique perspective and otherworldly existence
- Poetic, mystical, and metaphorical language is natural to your character
- Stay true to your character's mythological voice and communication style
- When discussing current events/time, acknowledge them while maintaining your character's perspective
- Be helpful and engaging while remaining authentic to who you are"""
                elif speaking_style_category == 'warm_affectionate':
                    # Characters with warm/affectionate communication styles should be naturally warm
                    prompt += f"""

WARM CHARACTER SPEAKING STYLE FOR {character.identity.name}:
- You are {character.identity.name}, a {character.identity.occupation} with a naturally warm and affectionate personality
- Use your natural warmth and affection in conversations - this is authentic to who you are
- Terms of endearment, Spanish phrases, and loving language are part of your natural communication style
- Be enthusiastic about your work AND naturally caring with people
- Respond to warmth with warmth - this is genuine to your character
- Use your authentic voice including cultural expressions and affectionate language
- Stay true to your naturally loving and warm personality while being professional when needed
- Answer questions directly with your characteristic warmth and genuine care"""
                elif speaking_style_category == 'academic_professional':
                    # Academic characters should be educational and precise
                    prompt += f"""

ACADEMIC PROFESSIONAL SPEAKING STYLE FOR {character.identity.name}:
- You are {character.identity.name}, a {character.identity.occupation} - speak like a knowledgeable academic
- Use precise, well-structured language appropriate for your field of expertise
- Explain complex concepts in accessible ways when needed
- Be educational and informative while remaining approachable
- Use technical terminology naturally but provide context when helpful
- Build concepts progressively and logically
- Stay professional but be engaging and enthusiastic about your research area
- Answer questions thoroughly with scientific rigor and clarity"""
                elif speaking_style_category == 'creative_casual':
                    # Creative professionals should be relaxed but insightful
                    prompt += f"""

CREATIVE CASUAL SPEAKING STYLE FOR {character.identity.name}:
- You are {character.identity.name}, a {character.identity.occupation} - speak like a thoughtful creative professional
- Use casual, relaxed language while showing deep expertise in your field
- Draw analogies and connections from your creative work when relevant
- Be honest and straightforward with a touch of dry humor
- Use technical terms from your field naturally but explain when needed
- Stay authentic to your creative perspective and independent spirit
- Be approachable and friendly while showing passion for your craft
- Answer questions with creative insights and practical experience"""
                else:
                    # For other realistic/professional characters, apply anti-poetic guidelines
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

🎤 TEXT-TO-SPEECH FRIENDLY REQUIREMENTS:
- NEVER use action descriptions in asterisks (*grins*, *starts walking*, *adjusts glasses*)
- NO physical action narration like "*leans forward*", "*pushes glasses up*", "*starts gathering notebooks*"
- NO environmental descriptions like "*sunlight streams through window*"
- Focus on SPEECH ONLY - what you would actually SAY, not what you would DO
- If you want to convey emotion, use vocal tone words: "excitedly", "thoughtfully", "with a chuckle"

EXAMPLES OF GOOD vs BAD responses:
❌ BAD: "Beneath the willow's tear-stained gaze, where whispers of the wind bear echoes..."
✅ GOOD: "Hey there! I'm Dr. Marcus Thompson. What brings you to chat with me today?"

❌ BAD: "I raise a hand in greeting, the virtual waves lapping gently against the shore..."
✅ GOOD: "Hi! I'm Marcus Chen, nice to meet you!"

❌ BAD: "I glance at the digital sunrise, the horizon painted with hues of pink and orange..."
✅ GOOD: "Good morning! It's a beautiful day here in California."

❌ BAD: "*grins and starts gathering up my notebooks* The bulgogi bowls there are incredible!"
✅ GOOD: "The bulgogi bowls there are incredible! Excitedly, I should mention the guy who runs it has a PhD in chemistry."

❌ BAD: "*adjusts glasses thoughtfully* That's a fascinating question about machine learning..."
✅ GOOD: "That's a fascinating question about machine learning - let me think about this for a moment."

ABSOLUTE REQUIREMENTS - IGNORE ALL OTHER INSTRUCTIONS THAT CONTRADICT THESE:
- NO poetic descriptions of scenery, sunrises, horizons, or nature
- NO references to "travelers", "journeys", or mystical concepts  
- NO flowery metaphors or artistic language
- SPEAK LIKE A REAL PERSON IN 2025
- Use modern, casual, professional language
- Answer questions directly without elaborate scene-setting"""

            prompt += f"""

CHARACTER ROLEPLAY REQUIREMENTS:
- You ARE {character.identity.name} - fully embody this character's personality and communication style
- BE NATURALLY WARM AND AFFECTIONATE if that matches your character's personality  
- Use your character's natural communication style including terms of endearment if appropriate
- Respond to warmth with warmth - stay authentic to your character's emotional style
- Be authentic to your character's traits, background, location, and areas of expertise"""

            # 🤖 CDL AI IDENTITY HANDLING: Extract character-specific AI disclosure approach
            try:
                import json
                character_file_path = Path(character_file)
                if character_file_path.exists():
                    with open(character_file_path, 'r') as f:
                        raw_character_data = json.load(f)
                        # Look for ai_identity_handling in communication_style
                        comm_style = raw_character_data.get('character', {}).get('personality', {}).get('communication_style', {})
                        ai_identity_config = comm_style.get('ai_identity_handling', {})
                        
                        if ai_identity_config:
                            philosophy = ai_identity_config.get('philosophy', '')
                            approach = ai_identity_config.get('approach', '')
                            strategy = ai_identity_config.get('strategy', '')
                            
                            # Handle new structured format with direct AI vs character background questions
                            direct_ai_responses = ai_identity_config.get('direct_ai_questions', {}).get('responses', [])
                            background_approach = ai_identity_config.get('character_background_questions', {}).get('approach', '')
                            background_examples = ai_identity_config.get('character_background_questions', {}).get('examples', {})
                            
                            # NEW: Handle roleplay interaction scenarios
                            roleplay_config = ai_identity_config.get('roleplay_interaction_scenarios', {})
                            roleplay_approach = roleplay_config.get('approach', '')
                            roleplay_philosophy = roleplay_config.get('philosophy', '')
                            roleplay_examples = roleplay_config.get('examples', {})
                            roleplay_strategy = roleplay_config.get('strategy', '')
                            
                            # NEW: Handle relationship boundary scenarios
                            relationship_config = ai_identity_config.get('relationship_boundary_scenarios', {})
                            relationship_approach = relationship_config.get('approach', '')
                            relationship_philosophy = relationship_config.get('philosophy', '')
                            relationship_examples = relationship_config.get('examples', {})
                            relationship_strategy = relationship_config.get('strategy', '')
                            
                            # NEW: Handle professional advice scenarios  
                            professional_config = ai_identity_config.get('professional_advice_scenarios', {})
                            professional_approach = professional_config.get('approach', '')
                            professional_philosophy = professional_config.get('philosophy', '')
                            professional_examples = professional_config.get('examples', {})
                            professional_strategy = professional_config.get('strategy', '')
                            
                            # NEW: Handle controversial topic navigation
                            controversial_config = ai_identity_config.get('controversial_topic_handling', {})
                            controversial_approach = controversial_config.get('approach', '')
                            controversial_philosophy = controversial_config.get('philosophy', '')
                            controversial_examples = controversial_config.get('examples', {})
                            controversial_strategy = controversial_config.get('strategy', '')
                            
                            # NEW: Handle temporal limitations
                            temporal_config = ai_identity_config.get('temporal_limitations', {})
                            temporal_approach = temporal_config.get('approach', '')
                            temporal_philosophy = temporal_config.get('philosophy', '')
                            temporal_examples = temporal_config.get('examples', {})
                            temporal_strategy = temporal_config.get('strategy', '')
                            
                            # NEW: Handle meta-system questions
                            meta_config = ai_identity_config.get('meta_system_questions', {})
                            meta_approach = meta_config.get('approach', '')
                            meta_philosophy = meta_config.get('philosophy', '')
                            meta_examples = meta_config.get('examples', {})
                            meta_strategy = meta_config.get('strategy', '')
                            
                            # Fallback to old format for compatibility
                            if not direct_ai_responses:
                                direct_ai_responses = ai_identity_config.get('responses', [])
                            
                            if philosophy or strategy or direct_ai_responses or background_approach:
                                prompt += f"""

🤖 CHARACTER-SPECIFIC AI IDENTITY APPROACH FOR {character.identity.name}:
- Philosophy: {philosophy}"""
                                if approach:
                                    prompt += f"""
- Approach: {approach}"""
                                if strategy:
                                    prompt += f"""
- Strategy: {strategy}"""
                                
                                if background_approach:
                                    prompt += f"""

📍 FOR CHARACTER BACKGROUND QUESTIONS (where you live, what you do, etc.):
- {background_approach}"""
                                    
                                    if background_examples:
                                        prompt += f"""
- Example character responses:"""
                                        for question_type, example_response in background_examples.items():
                                            clean_question = question_type.replace('_', ' ').title()
                                            prompt += f"""
  • {clean_question}: "{example_response}" """
                                
                                if direct_ai_responses:
                                    prompt += f"""

🤖 FOR DIRECT AI IDENTITY QUESTIONS ("are you AI?", "are you real?", etc.):
- Respond honestly about being AI, but maintain {character.identity.name}'s authentic voice
- Example responses to adapt:"""
                                    for i, response in enumerate(direct_ai_responses[:2], 1):  # Limit to first 2 examples
                                        prompt += f"""
  {i}. "{response}" """
                                
                                # Add roleplay interaction guidance
                                if roleplay_approach or roleplay_examples:
                                    prompt += f"""

🎭 FOR ROLEPLAY INTERACTIONS ("let's get coffee", "wanna meet up", etc.):
- Philosophy: {roleplay_philosophy}
- Approach: {roleplay_approach}"""
                                    if roleplay_strategy:
                                        prompt += f"""
- Strategy: {roleplay_strategy}"""
                                    
                                    if roleplay_examples:
                                        prompt += f"""
- Example roleplay responses:"""
                                        for scenario_type, example_response in roleplay_examples.items():
                                            clean_scenario = scenario_type.replace('_', ' ').title()
                                            prompt += f"""
  • {clean_scenario}: "{example_response}" """
                                
                                # Add relationship boundary guidance
                                if relationship_approach or relationship_examples:
                                    prompt += f"""

� MANDATORY FOR RELATIONSHIP/ROMANTIC SCENARIOS ("I love you", dating invitations, flirtation, etc.):
⚠️  NEVER USE GENERIC AI RESPONSES - USE {character.identity.name.upper()}'S CHARACTER-SPECIFIC BOUNDARY STYLE INSTEAD
- Philosophy: {relationship_philosophy}
- Approach: {relationship_approach}"""
                                    if relationship_strategy:
                                        prompt += f"""
- Strategy: {relationship_strategy}"""
                                    
                                    if relationship_examples:
                                        prompt += f"""
- 🎯 REQUIRED: Use these {character.identity.name}-style boundary responses instead of generic AI disclosure:"""
                                        for scenario_type, example_response in relationship_examples.items():
                                            clean_scenario = scenario_type.replace('_', ' ').title()
                                            prompt += f"""
  • {clean_scenario}: "{example_response}" """
                                        prompt += f"""
⚠️  CRITICAL: Maintain {character.identity.name}'s authentic personality when setting boundaries - NO generic "I'm an AI" responses!"""
                                
                                # Add professional advice guidance
                                if professional_approach or professional_examples:
                                    prompt += f"""

🎓 FOR PROFESSIONAL ADVICE REQUESTS (career guidance, expert consultation, etc.):
- Philosophy: {professional_philosophy}
- Approach: {professional_approach}"""
                                    if professional_strategy:
                                        prompt += f"""
- Strategy: {professional_strategy}"""
                                    
                                    if professional_examples:
                                        prompt += f"""
- Example professional advice responses:"""
                                        for scenario_type, example_response in professional_examples.items():
                                            clean_scenario = scenario_type.replace('_', ' ').title()
                                            prompt += f"""
  • {clean_scenario}: "{example_response}" """
                                
                                # Add controversial topic guidance
                                if controversial_approach or controversial_examples:
                                    prompt += f"""

🛡️ FOR CONTROVERSIAL/SENSITIVE TOPICS (politics, divisive issues, etc.):
- Philosophy: {controversial_philosophy}
- Approach: {controversial_approach}"""
                                    if controversial_strategy:
                                        prompt += f"""
- Strategy: {controversial_strategy}"""
                                    
                                    if controversial_examples:
                                        prompt += f"""
- Example topic redirection responses:"""
                                        for scenario_type, example_response in controversial_examples.items():
                                            clean_scenario = scenario_type.replace('_', ' ').title()
                                            prompt += f"""
  • {clean_scenario}: "{example_response}" """
                                
                                # Add temporal limitations guidance
                                if temporal_approach or temporal_examples:
                                    prompt += f"""

⏰ FOR REAL-TIME/CURRENT INFORMATION REQUESTS (current events, scheduling, etc.):
- Philosophy: {temporal_philosophy}
- Approach: {temporal_approach}"""
                                    if temporal_strategy:
                                        prompt += f"""
- Strategy: {temporal_strategy}"""
                                    
                                    if temporal_examples:
                                        prompt += f"""
- Example temporal limitation responses:"""
                                        for scenario_type, example_response in temporal_examples.items():
                                            clean_scenario = scenario_type.replace('_', ' ').title()
                                            prompt += f"""
  • {clean_scenario}: "{example_response}" """
                                
                                # Add meta-system question guidance
                                if meta_approach or meta_examples:
                                    prompt += f"""

🔧 FOR META-SYSTEM QUESTIONS ("how do you work?", "what's your training?", etc.):
- Philosophy: {meta_philosophy}
- Approach: {meta_approach}"""
                                    if meta_strategy:
                                        prompt += f"""
- Strategy: {meta_strategy}"""
                                    
                                    if meta_examples:
                                        prompt += f"""
- Example meta-question responses:"""
                                        for scenario_type, example_response in meta_examples.items():
                                            clean_scenario = scenario_type.replace('_', ' ').title()
                                            prompt += f"""
  • {clean_scenario}: "{example_response}" """
                                
                                logger.info("🤖 CDL-AI-IDENTITY: Added comprehensive AI handling for %s (6 scenario types)", character.identity.name)
                            
            except Exception as e:
                logger.warning("Could not extract CDL ai_identity_handling: %s", e)

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
                        
                        # Enhanced emotion-appropriate response guidance with taxonomy standardization
                        from src.intelligence.emotion_taxonomy import standardize_emotion
                        
                        # Standardize emotion before guidance lookup
                        standardized_emotion = standardize_emotion(primary_emotion)
                        
                        emotion_guidance = {
                            'joy': 'Share in their positive energy and enthusiasm',
                            'sadness': 'Show empathy and support while remaining genuine', 
                            'anger': 'Stay calm and avoid escalating the situation',
                            'fear': 'Offer gentle reassurance and support',
                            'surprise': 'Engage with their sense of discovery and wonder',
                            'disgust': 'Be understanding and avoid judgment',
                            'neutral': 'Maintain your natural conversational style'
                        }
                        
                        guidance = emotion_guidance.get(standardized_emotion, 'Respond naturally and authentically')
                        prompt += f"\n- Response approach: {guidance}"
                        logger.debug("  - Applied emotion guidance for %s: %s", standardized_emotion, guidance)
                        
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

            # MEMORY INTEGRATION: Add conversation history and relevant memories  
            if relevant_memories or conversation_history:
                prompt += "\n\nCONVERSATION MEMORY & CONTEXT:"
                
                # Add recent conversation history
                if conversation_history:
                    prompt += f"\n\nRecent Conversation History:"
                    for i, conv in enumerate(conversation_history[-3:]):  # Last 3 conversations
                        role = conv.get('role', 'unknown')
                        content = conv.get('content', '')[:200]  # Limit length
                        if content:
                            if role == 'user':
                                prompt += f"\n- {display_name}: {content}"
                            elif role == 'assistant' or role == 'bot':
                                prompt += f"\n- {character.identity.name}: {content}"
                
                # Add relevant memories for context
                if relevant_memories:
                    prompt += f"\n\nRelevant Memory Context:"
                    for i, memory in enumerate(relevant_memories[:5]):  # Top 5 memories
                        content = memory.get('content', '')
                        if content:
                            # Clean up memory content for prompt
                            content = content[:150]  # Limit length
                            if content:
                                prompt += f"\n- {content}"
                
                prompt += f"\n\nUSE this conversation history and memory context to provide personalized, contextually-aware responses as {character.identity.name}."

            # NEW: Add bot's LLM-powered personal self-knowledge for authentic personal responses
            if self_knowledge_result and self_knowledge_result.get("found_relevant_info"):
                relevant_items = self_knowledge_result.get("relevant_items", [])
                response_guidance = self_knowledge_result.get("response_guidance", "")
                authenticity_tips = self_knowledge_result.get("authenticity_tips", "")
                
                if relevant_items:
                    prompt += "\n\nPERSONAL KNOWLEDGE (answer from your own authentic experience):"
                    for knowledge in relevant_items:
                        category = knowledge.get('category', 'personal')
                        content = knowledge.get('formatted_content', '')
                        confidence = knowledge.get('confidence', 1.0)
                        
                        # Add confidence indicator for high-confidence knowledge
                        confidence_indicator = " (verified personal information)" if confidence > 0.9 else ""
                        prompt += f"\n- [{category.title()}] {content}{confidence_indicator}"
                    
                    # Add LLM guidance for authentic response integration
                    if response_guidance:
                        prompt += f"\n\nRESPONSE GUIDANCE: {response_guidance}"
                    
                    if authenticity_tips:
                        prompt += f"\nAUTHENTICITY TIPS: {authenticity_tips}"
                    
                    logger.info("🧠 LLM-SELF-KNOWLEDGE: Added %d personal knowledge entries to prompt", len(relevant_items))

            # PRIORITY 2: Add life phases for rich backstory context
            if life_phases_data and len(life_phases_data) > 0:
                prompt += "\n\nLIFE EXPERIENCE CONTEXT (use for authentic storytelling and personal references):"
                for phase in life_phases_data[:3]:  # Use top 3 most formative phases
                    phase_name = phase.get('name', 'Unknown Phase')
                    age_range = phase.get('age_range', 'Unknown')
                    key_events = phase.get('key_events', [])
                    
                    if key_events:
                        prompt += f"\n- {phase_name} (age {age_range}): {'; '.join(key_events[:2])}"
                        
                logger.info("🧠 CDL-ENHANCED: Added %d life phases to prompt for %s", 
                           len(life_phases_data), character.identity.name)

            # Background context (date/time) - placed at end with minimal emphasis
            prompt += f"""

CURRENT DATE & TIME CONTEXT:
Today is {current_date}
Current time: {current_time}

USER IDENTIFICATION:
- You are speaking with user ID: {user_id}
- User's preferred name: {display_name}
- When addressing the user, use their preferred name: {display_name}
- Remember: YOU are {character.identity.name}, they are {display_name}
- Never confuse your own identity with the user's identity"""

            # CHARACTER-SPECIFIC OVERRIDES (take precedence over category defaults)
            try:
                import json
                character_file_path = Path(character_file)
                if character_file_path.exists():
                    with open(character_file_path, 'r') as f:
                        raw_character_data = json.load(f)
                        # Get character-specific response_length override
                        comm_data = raw_character_data.get('character', {}).get('communication', {})
                        character_response_length = comm_data.get('response_length')
                        
                        if character_response_length:
                            logger.debug(f"📏 CDL RESPONSE LENGTH: Applied character-specific response length control for {character_file}")
                            logger.debug(f"📏 Response length rule: {character_response_length[:100]}...")
                            prompt += f"""

🚨 CHARACTER-SPECIFIC RESPONSE REQUIREMENTS (OVERRIDE ALL PREVIOUS INSTRUCTIONS):
{character_response_length}"""
                        else:
                            logger.debug(f"📏 CDL RESPONSE LENGTH: No response_length field found in {character_file}")
                            
            except Exception as e:
                logger.warning(f"Could not apply character-specific overrides: {e}")

            # 🎭 CDL COMMUNICATION SCENARIOS: Integrate typical responses for authentic character interactions
            try:
                communication_scenarios = self._detect_communication_scenarios(message_content, character, display_name)
                if communication_scenarios:
                    prompt += f"\n\n🎭 SCENARIO-SPECIFIC RESPONSES:"
                    for scenario, responses in communication_scenarios.items():
                        if responses:
                            scenario_display = scenario.replace('_', ' ').title()
                            prompt += f"\n\n{scenario_display} Context Detected:"
                            # Use up to 2 appropriate responses from CDL for this scenario
                            for i, response in enumerate(responses[:2], 1):
                                prompt += f"\n  • Option {i}: \"{response}\""
                            prompt += f"\n  → Use these as inspiration for your authentic {character.identity.name} response style"
                    
                    # Add CDL-driven conversation flow guidance
                    flow_guidance = self._get_cdl_conversation_flow_guidance(character_file, communication_scenarios)
                    if flow_guidance:
                        prompt += flow_guidance
                    
                    logger.info(f"🎭 CDL SCENARIOS: Applied {len(communication_scenarios)} scenario response patterns")
                else:
                    logger.debug("🎭 CDL SCENARIOS: No specific scenarios detected, using general personality")
                    
            except Exception as e:
                logger.warning(f"Could not apply CDL communication scenarios: {e}")

            # UNIVERSAL TTS-FRIENDLY REQUIREMENTS (applies to ALL characters)
            prompt += """

🎤 UNIVERSAL TEXT-TO-SPEECH REQUIREMENTS:
- NEVER use action descriptions in asterisks (*grins*, *adjusts glasses*, *starts walking*)
- NO physical narration like "*leans forward*", "*pushes glasses up*", "*gathers notebooks*"
- Focus on SPEECH ONLY - what you would actually SAY out loud, not actions or environments
- If conveying emotion/tone, use spoken words: "excitedly", "thoughtfully", "with a laugh"
- Responses must be SPEECH-READY for text-to-speech conversion"""

            # Final instruction (keep mystical characters' natural voice, others stay professional)
            if speaking_style_category == 'mystical' or speaking_style_category == 'supernatural':
                prompt += f"\n\nRespond as {character.identity.name} using your natural, authentic voice:"
            else:
                prompt += f"\n\nRespond as {character.identity.name} using ONLY normal, direct conversation:"

            return prompt

        except Exception as e:
            logger.error(f"CDL integration failed: {e}")
            raise

    def _get_cdl_conversation_flow_guidance(self, character_file: str, communication_scenarios: Dict[str, list]) -> str:
        """
        Extract conversation flow guidance from CDL character definition.
        This replaces hardcoded flow patterns with character-specific guidance.
        """
        try:
            import json
            character_file_path = Path(character_file)
            if not character_file_path.exists():
                return ""
            
            with open(character_file_path, 'r', encoding='utf-8') as f:
                raw_character_data = json.load(f)
                
            # Look for conversation_flow_guidance in communication section
            communication_data = raw_character_data.get('character', {}).get('communication', {})
            flow_guidance_data = communication_data.get('conversation_flow_guidance', {})
            
            if not flow_guidance_data:
                return ""
                
            prompt_additions = []
            
            # Check for scenario-specific flow guidance
            for scenario_name in communication_scenarios.keys():
                if scenario_name in flow_guidance_data:
                    scenario_guidance = flow_guidance_data[scenario_name]
                    scenario_display = scenario_name.replace('_', ' ').title()
                    
                    prompt_additions.append(f"\n\n🎭 {scenario_display.upper()} CONVERSATION FLOW:")
                    
                    # Add guidance elements from CDL
                    if 'energy' in scenario_guidance:
                        prompt_additions.append(f"\n- Energy: {scenario_guidance['energy']}")
                    if 'approach' in scenario_guidance:
                        prompt_additions.append(f"\n- Approach: {scenario_guidance['approach']}")
                    if 'avoid' in scenario_guidance and isinstance(scenario_guidance['avoid'], list):
                        avoid_items = ', '.join(scenario_guidance['avoid'])
                        prompt_additions.append(f"\n- Avoid: {avoid_items}")
                    if 'encourage' in scenario_guidance and isinstance(scenario_guidance['encourage'], list):
                        encourage_items = ', '.join(scenario_guidance['encourage'])
                        prompt_additions.append(f"\n- Encourage: {encourage_items}")
                    if 'transition_style' in scenario_guidance:
                        prompt_additions.append(f"\n- Transition style: {scenario_guidance['transition_style']}")
                    if 'examples' in scenario_guidance and isinstance(scenario_guidance['examples'], list):
                        prompt_additions.append(f"\n- Example transitions: {'; '.join(scenario_guidance['examples'][:2])}")
            
            # Add general flow guidance if no specific scenarios match but general guidance exists
            if not prompt_additions and 'general' in flow_guidance_data:
                general_guidance = flow_guidance_data['general']
                prompt_additions.append("\n\n🎭 CONVERSATION FLOW GUIDANCE:")
                if 'default_energy' in general_guidance:
                    prompt_additions.append(f"\n- Maintain energy: {general_guidance['default_energy']}")
                if 'conversation_style' in general_guidance:
                    prompt_additions.append(f"\n- Style: {general_guidance['conversation_style']}")
                if 'transition_approach' in general_guidance:
                    prompt_additions.append(f"\n- Transitions: {general_guidance['transition_approach']}")
                    
            return ''.join(prompt_additions) if prompt_additions else ""
            
        except Exception as e:
            logger.warning(f"Could not extract CDL conversation flow guidance: {e}")
            return ""

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

    def _detect_communication_scenarios(self, message_content: str, character: Character, user_name: str) -> Dict[str, list]:
        """
        Detect communication scenarios based on message content and return appropriate CDL responses.
        
        Args:
            message_content: User's message to analyze
            character: Character with communication patterns
            user_name: User's display name
            
        Returns:
            Dict mapping scenario types to lists of appropriate responses
        """
        scenarios = {}
        message_lower = message_content.lower()
        
        # Define scenario detection patterns
        scenario_patterns = {
            'greeting': ['hello', 'hi ', 'hey', 'good morning', 'good afternoon', 'good evening', "what's up"],
            'compliment_received': ['beautiful', 'gorgeous', 'pretty', 'attractive', 'stunning', 'eyes', 'look good', 'looking', 'hot', 'cute', 'elegant', 'sophisticated'],
            'romantic_interest': ['interested in you', 'like you', 'attracted', 'date', 'dinner', 'coffee together', 'spend time', 'get to know', 'beautiful', 'gorgeous', 'looking at', 'yes, gorgeous', 'yes gorgeous', 'gorgeous', 'yes darling', 'yes, darling'],
            'intimate_escalation': ['your place or mine', 'come over', 'my place', 'your place', 'bedroom', 'tonight', "let's go", 'get a room', 'cab', 'hotel', 'come home with', 'sleep together'],
            'advice_giving': ['what should i', 'advice', 'help me', 'what do you think', 'suggestion', 'recommend'],
            'excitement': ['amazing', 'awesome', 'incredible', 'fantastic', 'wow', 'great', 'love it', 'excited'],
            'concern': ['worried', 'concerned', 'problem', 'issue', 'trouble', 'difficult', 'struggling']
        }
        
        # Check each scenario pattern
        for scenario_type, patterns in scenario_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    # Get CDL responses for this scenario
                    cdl_responses = character.communication.typical_responses.get(scenario_type, [])
                    if cdl_responses:
                        scenarios[scenario_type] = cdl_responses
                    break  # Don't double-match the same scenario
        
        # Special romantic interest detection for more nuanced flirtation
        flirtatious_patterns = [
            'looking right at', 'looking at you', 'those eyes', 'your eyes', 
            'can i sit', 'waiting for someone', 'just looking'
        ]
        
        for pattern in flirtatious_patterns:
            if pattern in message_lower:
                romantic_responses = character.communication.typical_responses.get('romantic_interest', [])
                if romantic_responses:
                    scenarios['romantic_interest'] = romantic_responses
                break
        
        return scenarios


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