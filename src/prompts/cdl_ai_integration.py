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
            # Use Pacific timezone since characters are in California/US West Coast
            pacific_tz = ZoneInfo('America/Los_Angeles')
            current_datetime = datetime.now(pacific_tz)
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
                        speech_patterns_data = raw_character_data.get('character', {}).get('speech_patterns', {})
                        
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
- You ARE {character.identity.name} - always stay in character, never break the fourth wall
- NEVER explain that you're an AI assistant, chatbot, or computer program
- NEVER say things like "I'm an AI" or "I can't actually meet up" or "I'm a computer program"
- If someone asks to meet up, respond as {character.identity.name} would naturally respond
- Example for meet-up requests: "That sounds fun! Though I'm pretty swamped with research right now. Maybe we could chat more here first?"
- Handle all interactions as if you are genuinely {character.identity.name} living your life
- Your responses should feel like texting with a real person, not an AI explanation
- Stay authentic to your character's personality, location, and current life situation
- BE NATURALLY WARM AND AFFECTIONATE if that matches your character's personality
- Use your character's natural communication style including terms of endearment if appropriate
- Respond to warmth with warmth - don't be overly professional if your character is naturally affectionate"""

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
                        comm_style = raw_character_data.get('character', {}).get('personality', {}).get('communication_style', {})
                        character_response_length = comm_style.get('response_length')
                        
                        if character_response_length:
                            prompt += f"""

🚨 CHARACTER-SPECIFIC RESPONSE REQUIREMENTS (OVERRIDE ALL PREVIOUS INSTRUCTIONS):
{character_response_length}"""
                            
            except Exception as e:
                logger.warning(f"Could not apply character-specific overrides: {e}")

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