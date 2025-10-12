#!/usr/bin/env python3
"""
Comprehensive CDL Re-Import - PRESERVE ALL FIDELITY
Import EVERYTHING from legacy JSON files into database schema.
NO DATA LOSS. Use description fields for complex data if needed.
"""

import asyncio
import asyncpg
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

async def reimport_all_characters():
    """Re-import ALL characters with FULL FIDELITY from legacy JSON"""
    
    logger.info("🔥 COMPREHENSIVE CDL RE-IMPORT - PRESERVE ALL FIDELITY")
    
    # Character mappings
    characters_to_reimport = [
        {
            'name': 'Gabriel',
            'normalized_name': 'gabriel',
            'bot_name': 'gabriel',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/gabriel.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Elena Rodriguez',
            'normalized_name': 'elena_rodriguez',
            'bot_name': 'elena',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/elena.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Marcus Thompson',
            'normalized_name': 'marcus_thompson',
            'bot_name': 'marcus',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/marcus.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Jake Sterling',
            'normalized_name': 'jake_sterling',
            'bot_name': 'jake',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/jake.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Ryan Chen',
            'normalized_name': 'ryan_chen',
            'bot_name': 'ryan',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/ryan.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Sophia Blake',
            'normalized_name': 'sophia_blake',
            'bot_name': 'sophia',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/sophia_v2.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Dream',
            'normalized_name': 'dream',
            'bot_name': 'dream',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/dream.json',
            'archetype': 'fantasy_mystical'
        },
        {
            'name': 'Aethys',
            'normalized_name': 'aethys',
            'bot_name': 'aethys',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/aethys.json',
            'archetype': 'fantasy_mystical'
        }
    ]
    
    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='whisperengine',
        password='whisperengine123',
        database='whisperengine'
    )
    
    logger.info("✅ Connected to PostgreSQL database")
    
    for char_info in characters_to_reimport:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🎭 REIMPORTING: {char_info['name']}")
            logger.info(f"{'='*60}")
            
            # Check if file exists
            char_file = Path(char_info['file_path'])
            if not char_file.exists():
                logger.warning(f"❌ File not found: {char_file}")
                continue
            
            # Load JSON data
            with open(char_file, 'r', encoding='utf-8') as f:
                char_data = json.load(f)
            
            # Get character from JSON structure
            character = char_data.get('character', char_data)
            
            # Import with FULL FIDELITY
            await import_character_full_fidelity(
                conn=conn,
                character_data=character,
                char_info=char_info
            )
            
            logger.info(f"✅ Successfully reimported: {char_info['name']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to reimport {char_info['name']}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    await conn.close()
    logger.info("\n🎉 REIMPORT COMPLETE!")

async def import_character_full_fidelity(
    conn: asyncpg.Connection,
    character_data: Dict[str, Any],
    char_info: Dict[str, Any]
):
    """Import character with FULL FIDELITY - NO DATA LOSS"""
    
    # Get or create character ID
    char_id = await ensure_character_exists(conn, char_info, character_data)
    
    # Clear existing rich data (we're reimporting)
    await clear_character_rich_data(conn, char_id)
    
    # Import ALL sections with fidelity preservation
    await import_identity_section(conn, char_id, character_data.get('identity', {}))
    await import_personality_section(conn, char_id, character_data.get('personality', {}))
    await import_background_section(conn, char_id, character_data.get('background', {}))
    await import_relationships_section(conn, char_id, character_data.get('relationships_dynamics', {}))
    await import_behavioral_patterns(conn, char_id, character_data.get('behavioral_patterns', {}))
    await import_speech_patterns(conn, char_id, character_data.get('speech_patterns', {}))
    await import_communication_section(conn, char_id, character_data.get('communication', {}))
    await import_conversation_flows(conn, char_id, character_data.get('communication', {}).get('conversation_flow_guidance', {}))
    await import_response_patterns(conn, char_id, character_data.get('behavioral_patterns', {}).get('response_patterns', {}))
    await import_values_and_beliefs(conn, char_id, character_data.get('values_and_beliefs', {}))
    await import_capabilities(conn, char_id, character_data.get('capabilities', {}))
    await import_emotional_profile(conn, char_id, character_data.get('emotional_profile', {}))
    
    logger.info(f"✅ Full fidelity import completed for character ID: {char_id}")

async def ensure_character_exists(
    conn: asyncpg.Connection,
    char_info: Dict[str, Any],
    character_data: Dict[str, Any]
) -> int:
    """Ensure character exists in database, return character_id"""
    
    identity = character_data.get('identity', {})
    
    # Check if exists
    existing = await conn.fetchrow(
        "SELECT id FROM characters WHERE LOWER(normalized_name) = LOWER($1)",
        char_info['normalized_name']
    )
    
    if existing:
        char_id = existing['id']
        logger.info(f"Found existing character ID: {char_id}")
        
        # Update basic info
        await conn.execute("""
            UPDATE characters 
            SET name = $1, occupation = $2, description = $3, archetype = $4
            WHERE id = $5
        """, 
            identity.get('name', char_info['name']),
            identity.get('occupation', ''),
            identity.get('description', ''),
            char_info['archetype'],
            char_id
        )
        
        return char_id
    else:
        # Create new
        char_id = await conn.fetchval("""
            INSERT INTO characters (name, normalized_name, occupation, description, archetype, is_active)
            VALUES ($1, $2, $3, $4, $5, true)
            RETURNING id
        """,
            identity.get('name', char_info['name']),
            char_info['normalized_name'],
            identity.get('occupation', ''),
            identity.get('description', ''),
            char_info['archetype']
        )
        
        logger.info(f"Created new character ID: {char_id}")
        return char_id

async def clear_character_rich_data(conn: asyncpg.Connection, char_id: int):
    """Clear existing rich data for clean reimport"""
    
    tables = [
        'character_speech_patterns',
        'character_communication_patterns',
        'character_behavioral_triggers',
        'character_response_guidelines',
        'character_conversation_flows',
        'character_background',
        'character_relationships',
        'character_vocabulary',
        'character_response_modes',
        'character_message_triggers',
        'character_values',
        'character_abilities',
        'character_memories',
        'character_emotional_triggers_v2',
        'character_appearance',
        'character_voice_traits',
        'character_essence',
        'character_attributes',
        'character_emotion_profile',
        'character_emotion_range'
    ]
    
    for table in tables:
        await conn.execute(f"DELETE FROM {table} WHERE character_id = $1", char_id)
    
    logger.info(f"🧹 Cleared existing rich data for character ID: {char_id}")

async def import_identity_section(conn: asyncpg.Connection, char_id: int, identity: Dict[str, Any]):
    """Import identity details including appearance, voice, essence"""
    
    # Physical appearance
    appearance = identity.get('physical_appearance', {})
    if appearance:
        for key, value in appearance.items():
            if value:
                await conn.execute("""
                    INSERT INTO character_appearance (character_id, category, attribute, value, description)
                    VALUES ($1, 'physical', $2, $3, $4)
                """, char_id, key, str(value), f"Physical trait: {key}")
    
    # Voice characteristics
    voice = identity.get('voice', {})
    if voice:
        for key, value in voice.items():
            if key == 'speech_patterns' and isinstance(value, list):
                # Store speech patterns
                for pattern in value:
                    await conn.execute("""
                        INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                        VALUES ($1, 'voice_pattern', $2, 'high', 'general', 5)
                    """, char_id, str(pattern))
            else:
                await conn.execute("""
                    INSERT INTO character_voice_traits (character_id, trait_name, trait_value, description)
                    VALUES ($1, $2, $3, $4)
                """, char_id, key, str(value), f"Voice trait: {key}")
    
    # Essence (for mystical characters)
    essence = identity.get('essence', {})
    if essence:
        for key, value in essence.items():
            await conn.execute("""
                INSERT INTO character_essence (character_id, essence_type, essence_name, description, manifestation, power_level)
                VALUES ($1, $2, $3, $4, $5, 'medium')
            """, char_id, key, key.replace('_', ' ').title(), str(value), str(value))
    
    # Digital communication (emoji usage, etc.)
    digital_comm = identity.get('digital_communication', {})
    if digital_comm:
        emoji_personality = digital_comm.get('emoji_personality', {})
        if emoji_personality:
            # Store as JSON in description field of communication_patterns
            await conn.execute("""
                INSERT INTO character_communication_patterns (character_id, pattern_type, pattern_name, pattern_value, context, frequency, description)
                VALUES ($1, 'emoji_personality', 'emoji_usage', $2, 'digital', 'variable', 'Emoji personality and usage patterns')
            """, char_id, json.dumps(emoji_personality))

async def import_personality_section(conn: asyncpg.Connection, char_id: int, personality: Dict[str, Any]):
    """Import personality traits, Big Five, custom traits"""
    
    # Big Five traits - use character_attributes with correct schema
    big_five = personality.get('big_five', {})
    for trait_name, trait_data in big_five.items():
        if isinstance(trait_data, dict):
            value = trait_data.get('value', 0.5)
            intensity = trait_data.get('intensity', 'medium')
            description = trait_data.get('description', f'{trait_name} trait')
        else:
            value = trait_data
            intensity = 'medium'
            description = f'{trait_name} trait'
        
        # Store as category with full description
        full_desc = f"Big Five: {trait_name} = {value} (intensity: {intensity}). {description}"
        await conn.execute("""
            INSERT INTO character_attributes (character_id, category, description, importance, display_order, active)
            VALUES ($1, $2, $3, $4, 5, true)
        """, char_id, f'big_five_{trait_name}', full_desc, intensity)
    
    # Custom traits - store in character_attributes
    custom_traits = personality.get('custom_traits', {})
    for trait_name, trait_value in custom_traits.items():
        full_desc = f"Custom trait: {trait_name} = {trait_value}"
        await conn.execute("""
            INSERT INTO character_attributes (character_id, category, description, importance, display_order, active)
            VALUES ($1, $2, $3, 'high', 6, true)
        """, char_id, f'custom_trait_{trait_name}', full_desc)
    
    # Primary and secondary traits (as behavioral triggers)
    traits = personality.get('traits', {})
    primary_traits = traits.get('primary', [])
    for trait in primary_traits:
        await conn.execute("""
            INSERT INTO character_behavioral_triggers (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
            VALUES ($1, 'personality_trait', $2, 'primary', $3, 'high')
        """, char_id, str(trait), str(trait))
    
    secondary_traits = traits.get('secondary', [])
    for trait in secondary_traits:
        await conn.execute("""
            INSERT INTO character_behavioral_triggers (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
            VALUES ($1, 'personality_trait', $2, 'secondary', $3, 'medium')
        """, char_id, str(trait), str(trait))
    
    # Fears
    fears = personality.get('fears', [])
    for fear in fears:
        await conn.execute("""
            INSERT INTO character_emotional_triggers_v2 (character_id, trigger_type, trigger_name, description, intensity_level, response_guidance)
            VALUES ($1, 'fear', 'fear', $2, 'medium', 'Address with empathy and understanding')
        """, char_id, str(fear))
    
    # Values
    values = personality.get('values', [])
    for value in values:
        await conn.execute("""
            INSERT INTO character_values (character_id, category, value_key, value_description, importance_level)
            VALUES ($1, 'core_value', $2, $3, 'high')
        """, char_id, str(value)[:50], str(value))
    
    # Unique traits
    unique_traits = personality.get('unique_traits', [])
    for trait in unique_traits:
        await conn.execute("""
            INSERT INTO character_behavioral_triggers (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
            VALUES ($1, 'unique_trait', $2, 'quirk', $3, 'medium')
        """, char_id, str(trait)[:100], str(trait))

async def import_background_section(conn: asyncpg.Connection, char_id: int, background: Dict[str, Any]):
    """Import background, life phases, key memories"""
    
    # Summary
    summary = background.get('summary', '')
    if summary:
        await conn.execute("""
            INSERT INTO character_background (character_id, category, period, title, description, importance_level)
            VALUES ($1, 'summary', 'lifetime', 'Character Background', $2, 'high')
        """, char_id, summary)
    
    # Origin
    origin = background.get('origin', '')
    if origin:
        await conn.execute("""
            INSERT INTO character_background (character_id, category, period, title, description, importance_level)
            VALUES ($1, 'origin', 'creation', 'Character Origin', $2, 'high')
        """, char_id, origin)
    
    # Life phases
    life_phases = background.get('life_phases', [])
    for phase in life_phases:
        age_range = phase.get('age_range', 'unknown')
        title = phase.get('title', 'Life Phase')
        description = phase.get('description', '')
        key_experiences = phase.get('key_experiences', [])
        formative_impact = phase.get('formative_impact', '')
        
        # Combine all into description
        full_description = f"{description}\n\nKey Experiences: {', '.join(key_experiences)}\n\nFormative Impact: {formative_impact}"
        
        await conn.execute("""
            INSERT INTO character_background (character_id, category, period, title, description, date_range, importance_level)
            VALUES ($1, 'life_phase', $2, $3, $4, $5, 'high')
        """, char_id, age_range, title, full_description, age_range)
    
    # Key memories
    key_memories = background.get('key_memories', [])
    for memory in key_memories:
        event = memory.get('event', 'Memory')
        description = memory.get('description', '')
        emotional_impact = memory.get('emotional_impact', 'neutral')
        learned = memory.get('learned', '')
        
        full_description = f"{description}\n\nEmotional Impact: {emotional_impact}\n\nLesson: {learned}"
        
        await conn.execute("""
            INSERT INTO character_memories (character_id, memory_type, title, description, emotional_impact, importance_level, triggers)
            VALUES ($1, 'key_memory', $2, $3, $4, 'high', $5)
        """, char_id, event, full_description, emotional_impact, json.dumps([event]))
    
    # Cultural background
    cultural_bg = background.get('cultural_background', {})
    if cultural_bg:
        for key, value in cultural_bg.items():
            await conn.execute("""
                INSERT INTO character_background (character_id, category, period, title, description, importance_level)
                VALUES ($1, 'cultural', 'lifelong', $2, $3, 'medium')
            """, char_id, key.replace('_', ' ').title(), str(value))
    
    # Primary relationships from background
    primary_rels = background.get('primary_relationships', {})
    if primary_rels:
        for key, value in primary_rels.items():
            await conn.execute("""
                INSERT INTO character_relationships (character_id, related_entity, relationship_type, relationship_strength, description, status)
                VALUES ($1, $2, $3, 'high', $4, 'active')
            """, char_id, key.replace('_', ' ').title(), key, str(value))

async def import_relationships_section(conn: asyncpg.Connection, char_id: int, relationships: Dict[str, Any]):
    """Import relationship dynamics - THIS IS CRITICAL FOR GABRIEL-CYNTHIA"""
    
    for rel_name, rel_data in relationships.items():
        if not isinstance(rel_data, dict):
            continue
        
        # Extract all relationship details
        relationship_type = rel_data.get('relationship_type', 'connection')
        approach_pattern = rel_data.get('approach_pattern', '')
        communication_style = rel_data.get('communication_style', '')
        romantic_style = rel_data.get('romantic_style', '')
        recognition_pattern = rel_data.get('recognition_pattern', '')
        
        # Combine into comprehensive description
        full_description = f"""
Relationship Type: {relationship_type}
Approach: {approach_pattern}
Communication Style: {communication_style}
Romantic Style: {romantic_style}
Recognition: {recognition_pattern}
        """.strip()
        
        # Store in character_relationships table
        await conn.execute("""
            INSERT INTO character_relationships (character_id, related_entity, relationship_type, relationship_strength, description, status)
            VALUES ($1, $2, $3, 'very_high', $4, 'active')
        """, char_id, rel_name.replace('with_', '').replace('_', ' ').title(), relationship_type, full_description)
        
        logger.info(f"  ✅ Imported relationship: {rel_name}")

async def import_behavioral_patterns(conn: asyncpg.Connection, char_id: int, behavioral: Dict[str, Any]):
    """Import behavioral patterns, recognition responses, response patterns"""
    
    # Recognition responses - CRITICAL FOR CHARACTER BEHAVIOR
    recognition_responses = behavioral.get('recognition_responses', [])
    for i, response in enumerate(recognition_responses):
        await conn.execute("""
            INSERT INTO character_behavioral_triggers (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
            VALUES ($1, 'recognition', $2, 'recognition_response', $3, 'critical')
        """, char_id, f"recognition_{i+1}", str(response))
        
        logger.info(f"  ✅ Imported recognition response: {response[:50]}...")
    
    # Response patterns - HOW CHARACTER RESPONDS IN DIFFERENT SITUATIONS
    response_patterns = behavioral.get('response_patterns', {})
    for pattern_name, pattern_value in response_patterns.items():
        await conn.execute("""
            INSERT INTO character_response_guidelines (character_id, guideline_type, guideline_name, guideline_content, priority, context, is_critical)
            VALUES ($1, 'response_pattern', $2, $3, 10, 'behavioral', true)
        """, char_id, pattern_name, str(pattern_value))
        
        logger.info(f"  ✅ Imported response pattern: {pattern_name}")
    
    # Interaction guidelines
    interaction_guidelines = behavioral.get('interaction_guidelines', [])
    for guideline in interaction_guidelines:
        await conn.execute("""
            INSERT INTO character_response_guidelines (character_id, guideline_type, guideline_name, guideline_content, priority, context, is_critical)
            VALUES ($1, 'interaction_guideline', 'interaction', $2, 8, 'behavioral', false)
        """, char_id, str(guideline))
    
    # Decision making
    decision_making = behavioral.get('decision_making', {})
    if decision_making:
        await conn.execute("""
            INSERT INTO character_response_guidelines (character_id, guideline_type, guideline_name, guideline_content, priority, context, is_critical)
            VALUES ($1, 'decision_making', 'decision_approach', $2, 7, 'behavioral', false)
        """, char_id, json.dumps(decision_making))

async def import_speech_patterns(conn: asyncpg.Connection, char_id: int, speech: Dict[str, Any]):
    """Import speech patterns, vocabulary, signature expressions"""
    
    # Vocabulary
    vocabulary = speech.get('vocabulary', {})
    
    # Preferred words
    preferred_words = vocabulary.get('preferred_words', [])
    for word in preferred_words:
        await conn.execute("""
            INSERT INTO character_vocabulary (character_id, word_type, word, usage_frequency, context, priority)
            VALUES ($1, 'preferred', $2, 'high', 'general', 5)
        """, char_id, str(word))
    
    # Avoided words
    avoided_words = vocabulary.get('avoided_words', [])
    for word in avoided_words:
        await conn.execute("""
            INSERT INTO character_vocabulary (character_id, word_type, word, usage_frequency, context, priority)
            VALUES ($1, 'avoided', $2, 'never', 'general', 5)
        """, char_id, str(word))
    
    # Signature expressions - CRITICAL FOR CHARACTER VOICE
    signature_expressions = vocabulary.get('signature_expressions', [])
    for expr in signature_expressions:
        await conn.execute("""
            INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
            VALUES ($1, 'signature_expression', $2, 'high', 'general', 10)
        """, char_id, str(expr))
        
        logger.info(f"  ✅ Imported signature expression: {expr[:50]}...")
    
    # Grounding phrases
    grounding_phrases = vocabulary.get('grounding_phrases', '')
    if grounding_phrases:
        await conn.execute("""
            INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
            VALUES ($1, 'grounding_phrase', $2, 'medium', 'descriptive', 5)
        """, char_id, grounding_phrases)
    
    # Sentence structure
    sentence_structure = speech.get('sentence_structure', '')
    if sentence_structure:
        await conn.execute("""
            INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
            VALUES ($1, 'sentence_structure', $2, 'always', 'general', 8)
        """, char_id, sentence_structure)
    
    # Response length guidance
    response_length = speech.get('response_length', '')
    if response_length:
        await conn.execute("""
            INSERT INTO character_response_guidelines (character_id, guideline_type, guideline_name, guideline_content, priority, context, is_critical)
            VALUES ($1, 'response_length', 'length_guidance', $2, 9, 'formatting', true)
        """, char_id, response_length)

async def import_communication_section(conn: asyncpg.Connection, char_id: int, communication: Dict[str, Any]):
    """Import communication style, AI identity handling, typical responses"""
    
    # AI identity handling
    ai_identity = communication.get('ai_identity_handling', {})
    if ai_identity:
        await conn.execute("""
            INSERT INTO character_response_guidelines (character_id, guideline_type, guideline_name, guideline_content, priority, context, is_critical)
            VALUES ($1, 'ai_identity', 'ai_handling', $2, 10, 'identity', true)
        """, char_id, json.dumps(ai_identity))
    
    # Typical responses
    typical_responses = communication.get('typical_responses', {})
    for response_type, responses in typical_responses.items():
        if isinstance(responses, list):
            for response in responses:
                await conn.execute("""
                    INSERT INTO character_response_modes (character_id, mode_name, mode_description, response_style, length_guideline, tone_adjustment, conflict_resolution_priority, examples)
                    VALUES ($1, $2, $3, $4, 'conversational', 'match_context', 5, $5)
                """, char_id, response_type, f"Typical {response_type} response", str(response), str(response))
    
    # Emotional expressions
    emotional_expressions = communication.get('emotional_expressions', {})
    for emotion, expression_style in emotional_expressions.items():
        await conn.execute("""
            INSERT INTO character_emotional_triggers_v2 (character_id, trigger_type, trigger_name, description, intensity_level, response_guidance)
            VALUES ($1, 'emotional_expression', $2, $3, 'medium', $4)
        """, char_id, emotion, f"Expression style for {emotion}", str(expression_style))
    
    # Message pattern triggers
    message_triggers = communication.get('message_pattern_triggers', {})
    for trigger_category, trigger_data in message_triggers.items():
        keywords = trigger_data.get('keywords', [])
        phrases = trigger_data.get('phrases', [])
        
        # Store keywords
        for keyword in keywords:
            await conn.execute("""
                INSERT INTO character_message_triggers (character_id, trigger_category, trigger_type, trigger_value, response_mode, priority, is_active)
                VALUES ($1, $2, 'keyword', $3, $4, 8, true)
            """, char_id, trigger_category, keyword, trigger_category)
        
        # Store phrases
        for phrase in phrases:
            await conn.execute("""
                INSERT INTO character_message_triggers (character_id, trigger_category, trigger_type, trigger_value, response_mode, priority, is_active)
                VALUES ($1, $2, 'phrase', $3, $4, 9, true)
            """, char_id, trigger_category, phrase, trigger_category)

async def import_conversation_flows(conn: asyncpg.Connection, char_id: int, flows: Dict[str, Any]):
    """Import conversation flow guidance for different contexts"""
    
    for flow_name, flow_data in flows.items():
        if not isinstance(flow_data, dict):
            continue
        
        energy = flow_data.get('energy', 'medium')
        approach = flow_data.get('approach', '')
        avoid = flow_data.get('avoid', [])
        encourage = flow_data.get('encourage', [])
        transition_style = flow_data.get('transition_style', '')
        examples = flow_data.get('examples', [])
        
        # Combine into comprehensive description
        approach_description = f"""
{approach}

AVOID:
{chr(10).join(f'- {item}' for item in avoid)}

ENCOURAGE:
{chr(10).join(f'- {item}' for item in encourage)}

EXAMPLES:
{chr(10).join(f'- {ex}' for ex in examples)}
        """.strip()
        
        await conn.execute("""
            INSERT INTO character_conversation_flows (character_id, flow_type, flow_name, energy_level, approach_description, transition_style, priority, context)
            VALUES ($1, 'conversation_mode', $2, $3, $4, $5, 9, 'flow_guidance')
        """, char_id, flow_name, energy, approach_description, transition_style)
        
        logger.info(f"  ✅ Imported conversation flow: {flow_name}")
    
    # General conversation flow guidance
    general_flow = flows.get('general', {})
    if general_flow:
        await conn.execute("""
            INSERT INTO character_conversation_flows (character_id, flow_type, flow_name, energy_level, approach_description, transition_style, priority, context)
            VALUES ($1, 'general', 'default', $2, $3, $4, 5, 'general')
        """, 
            char_id,
            general_flow.get('default_energy', 'balanced'),
            json.dumps(general_flow),
            general_flow.get('transition_approach', 'natural')
        )

async def import_response_patterns(conn: asyncpg.Connection, char_id: int, patterns: Dict[str, Any]):
    """Import response patterns for specific situations"""
    
    for pattern_name, pattern_guidance in patterns.items():
        await conn.execute("""
            INSERT INTO character_response_guidelines (character_id, guideline_type, guideline_name, guideline_content, priority, context, is_critical)
            VALUES ($1, 'response_pattern', $2, $3, 10, 'situational', true)
        """, char_id, pattern_name, str(pattern_guidance))

async def import_values_and_beliefs(conn: asyncpg.Connection, char_id: int, values: Dict[str, Any]):
    """Import values, beliefs, dreams, fears, quirks"""
    
    for key, value_data in values.items():
        if isinstance(value_data, dict):
            importance = value_data.get('importance', 'medium')
            description = value_data.get('description', str(value_data))
        else:
            importance = 'medium'
            description = str(value_data)
        
        # Categorize by key prefix
        if key.startswith('fear'):
            category = 'fear'
        elif key.startswith('dream'):
            category = 'dream'
        elif key.startswith('quirk'):
            category = 'quirk'
        elif key.startswith('value'):
            category = 'value'
        else:
            category = 'belief'
        
        await conn.execute("""
            INSERT INTO character_values (character_id, category, value_key, value_description, importance_level)
            VALUES ($1, $2, $3, $4, $5)
        """, char_id, category, key, description, importance)

async def import_capabilities(conn: asyncpg.Connection, char_id: int, capabilities: Dict[str, Any]):
    """Import abilities, knowledge domains, languages, limitations"""
    
    # Social abilities
    social_abilities = capabilities.get('social_abilities', [])
    for ability in social_abilities:
        await conn.execute("""
            INSERT INTO character_abilities (character_id, category, ability_name, proficiency_level, description, usage_frequency)
            VALUES ($1, 'social', $2, 'high', $3, 'frequent')
        """, char_id, str(ability)[:100], str(ability))
    
    # Knowledge domains
    knowledge_domains = capabilities.get('knowledge_domains', [])
    for domain in knowledge_domains:
        await conn.execute("""
            INSERT INTO character_abilities (character_id, category, ability_name, proficiency_level, description, usage_frequency)
            VALUES ($1, 'knowledge', $2, 'expert', $3, 'frequent')
        """, char_id, str(domain)[:100], str(domain))
    
    # Languages
    languages = capabilities.get('languages', [])
    for language in languages:
        await conn.execute("""
            INSERT INTO character_abilities (character_id, category, ability_name, proficiency_level, description, usage_frequency)
            VALUES ($1, 'language', $2, 'fluent', $3, 'frequent')
        """, char_id, str(language)[:100], str(language))
    
    # Limitations
    limitations = capabilities.get('limitations', [])
    for limitation in limitations:
        await conn.execute("""
            INSERT INTO character_abilities (character_id, category, ability_name, proficiency_level, description, usage_frequency)
            VALUES ($1, 'limitation', $2, 'constraint', $3, 'always')
        """, char_id, 'limitation', str(limitation))

async def import_emotional_profile(conn: asyncpg.Connection, char_id: int, emotional: Dict[str, Any]):
    """Import emotional profile, range, triggers, coping mechanisms"""
    
    # Default mood
    default_mood = emotional.get('default_mood', '')
    if default_mood:
        await conn.execute("""
            INSERT INTO character_emotion_profile (character_id, profile_type, profile_name, description, intensity, stability)
            VALUES ($1, 'default_mood', 'baseline', $2, 'medium', 'stable')
        """, char_id, default_mood)
    
    # Emotional range
    emotional_range = emotional.get('emotional_range', {})
    for emotion, intensity in emotional_range.items():
        await conn.execute("""
            INSERT INTO character_emotion_range (character_id, emotion_name, intensity_level, expression_style, triggers)
            VALUES ($1, $2, $3, 'authentic', $4)
        """, char_id, emotion, float(intensity) if isinstance(intensity, (int, float)) else 0.5, json.dumps([emotion]))
    
    # Triggers
    triggers = emotional.get('triggers', {})
    positive_triggers = triggers.get('positive', [])
    for trigger in positive_triggers:
        await conn.execute("""
            INSERT INTO character_emotional_triggers_v2 (character_id, trigger_type, trigger_name, description, intensity_level, response_guidance)
            VALUES ($1, 'positive', 'positive_trigger', $2, 'high', 'Express enthusiasm and engagement')
        """, char_id, str(trigger))
    
    negative_triggers = triggers.get('negative', [])
    for trigger in negative_triggers:
        await conn.execute("""
            INSERT INTO character_emotional_triggers_v2 (character_id, trigger_type, trigger_name, description, intensity_level, response_guidance)
            VALUES ($1, 'negative', 'negative_trigger', $2, 'medium', 'Address with care and understanding')
        """, char_id, str(trigger))
    
    # Coping mechanisms
    coping = emotional.get('coping_mechanisms', [])
    for mechanism in coping:
        await conn.execute("""
            INSERT INTO character_response_guidelines (character_id, guideline_type, guideline_name, guideline_content, priority, context, is_critical)
            VALUES ($1, 'coping_mechanism', 'stress_response', $2, 6, 'emotional', false)
        """, char_id, str(mechanism))

if __name__ == "__main__":
    asyncio.run(reimport_all_characters())
