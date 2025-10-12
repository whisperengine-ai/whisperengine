#!/usr/bin/env python3
"""
DREAM EXTENDED DATA IMPORT (SEMANTIC MAPPING)

This script imports extended character data for Dream (Dream Lord) from 
dream.json into the PostgreSQL character extension tables.

SEMANTIC MAPPING STRATEGY:
- Dream has NESTED structure: data['character'][section]
- Target: ~36 extractable records (35 new + 1 existing expertise)

Extraction paths:
- message_triggers: character.communication.message_pattern_triggers (~2)
- cultural_expressions: character.communication.typical_responses (~9)
- emotional_triggers: character.communication.emotional_expressions (~4)
- voice_traits: character.speech_patterns fields (~4)
- response_guidelines: character.communication.ai_identity_handling (~4)
- ai_scenarios: character.behavioral_patterns.response_patterns (~4)
- expertise_domains: character.dream_lord_abilities (~5)
- conversation_flows: character.communication.conversation_flow_guidance (~4)

CHARACTER: Dream (ID 4)
CURRENT: 6 records (5 emoji + 1 expertise)
TARGET: ~41 total records after import
"""

import asyncio
import json
import sys
import os
import asyncpg
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5433')),
    'user': os.getenv('POSTGRES_USER', 'whisperengine'),
    'password': os.getenv('POSTGRES_PASSWORD', 'whisperengine_dev'),
    'database': os.getenv('POSTGRES_DB', 'whisperengine')
}


async def import_dream_extended():
    """Import Dream's missing extended data from JSON."""
    
    # Load Dream's JSON
    dream_json_path = Path(__file__).parent.parent / "characters" / "examples_legacy_backup" / "dream.json"
    with open(dream_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        dream = data['character']
    
    print(f"{'='*70}")
    print("🔧 DREAM EXTENDED DATA IMPORT (SEMANTIC MAPPING)")
    print(f"{'='*70}\n")
    
    # Initialize database connection
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get Dream's character ID
        result = await conn.fetchrow(
            "SELECT id FROM characters WHERE name = 'Dream' LIMIT 1"
        )
        
        if not result:
            print("❌ Dream not found in database")
            return
        
        character_id = result['id']
        print(f"✅ Found Dream (ID: {character_id})\n")
        
        total_imported = 0
        
        # 1. MESSAGE TRIGGERS from communication.message_pattern_triggers
        print("📨 Importing MESSAGE TRIGGERS...")
        if 'communication' in dream and 'message_pattern_triggers' in dream['communication']:
            triggers_dict = dream['communication']['message_pattern_triggers']
            
            for category, trigger_data in triggers_dict.items():
                # Extract trigger phrases from nested structure
                if isinstance(trigger_data, dict):
                    keywords = trigger_data.get('keywords', [])
                    guidance = trigger_data.get('guidance', '')
                    
                    # Insert each keyword as a trigger
                    for keyword in keywords:
                        await conn.execute("""
                            INSERT INTO character_message_triggers 
                            (character_id, trigger_category, trigger_type, trigger_value, response_mode, priority, is_active)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """, character_id, category, 'keyword', keyword, 'standard', 50, True)
                        total_imported += 1
                    
                    print(f"  ✅ {category}: {len(keywords)} keywords from {guidance[:40]}...")
        
        # 2. CULTURAL EXPRESSIONS from communication.typical_responses
        print("\n🌍 Importing CULTURAL EXPRESSIONS...")
        if 'communication' in dream and 'typical_responses' in dream['communication']:
            responses = dream['communication']['typical_responses']
            
            for response_type, response_data in responses.items():
                # Handle both list and string formats
                if isinstance(response_data, list):
                    # Multiple expressions for this type
                    for idx, response_text in enumerate(response_data):
                        await conn.execute("""
                            INSERT INTO character_cultural_expressions 
                            (character_id, expression_type, expression_value, meaning, usage_context)
                            VALUES ($1, $2, $3, $4, $5)
                        """, character_id, response_type, str(response_text), 
                            response_type.replace('_', ' ').title(), 
                            f"Typical {response_type} response (variant {idx + 1})")
                        
                        print(f"  ✅ {response_type} [{idx+1}]: {str(response_text)[:60]}...")
                        total_imported += 1
                else:
                    # Single expression (string)
                    await conn.execute("""
                        INSERT INTO character_cultural_expressions 
                        (character_id, expression_type, expression_value, meaning, usage_context)
                        VALUES ($1, $2, $3, $4, $5)
                    """, character_id, response_type, str(response_data), 
                        response_type.replace('_', ' ').title(), f"Typical {response_type} response")
                    
                    print(f"  ✅ {response_type}: {str(response_data)[:60]}...")
                    total_imported += 1
        
        # 3. EMOTIONAL TRIGGERS from communication.emotional_expressions
        print("\n💭 Importing EMOTIONAL TRIGGERS...")
        if 'communication' in dream and 'emotional_expressions' in dream['communication']:
            emotions = dream['communication']['emotional_expressions']
            
            for emotion, expression in emotions.items():
                await conn.execute("""
                    INSERT INTO character_emotional_triggers 
                    (character_id, trigger_type, trigger_content, emotional_response, response_intensity)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, emotion, emotion, expression, 'medium')
                
                print(f"  ✅ {emotion}: {expression[:60]}...")
                total_imported += 1
        
        # 4. VOICE TRAITS from speech_patterns
        print("\n🗣️ Importing VOICE TRAITS...")
        if 'speech_patterns' in dream:
            sp = dream['speech_patterns']
            
            for trait_name, trait_value in sp.items():
                if trait_name == 'patterns_reference':
                    continue  # Skip reference field
                
                # Handle vocabulary dict specially - extract lists
                if trait_name == 'vocabulary' and isinstance(trait_value, dict):
                    # Extract preferred_words list
                    if 'preferred_words' in trait_value and isinstance(trait_value['preferred_words'], list):
                        for word in trait_value['preferred_words']:
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, 'preferred_word', word, "Words Dream naturally uses")
                            total_imported += 1
                    
                    # Extract avoided_words list
                    if 'avoided_words' in trait_value and isinstance(trait_value['avoided_words'], list):
                        for word in trait_value['avoided_words']:
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, 'avoided_word', word, "Words Dream avoids")
                            total_imported += 1
                    
                    # Extract string fields as single records
                    for key in ['technical_terms', 'colloquialisms']:
                        if key in trait_value and isinstance(trait_value[key], str):
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, key, trait_value[key], f"Dream's {key.replace('_', ' ')}")
                            total_imported += 1
                    
                    print(f"  ✅ vocabulary: extracted {len(trait_value.get('preferred_words', []))} preferred, {len(trait_value.get('avoided_words', []))} avoided words")
                else:
                    # Store other traits as-is (strings)
                    if isinstance(trait_value, str):
                        await conn.execute("""
                            INSERT INTO character_voice_traits 
                            (character_id, trait_type, trait_value, situational_context)
                            VALUES ($1, $2, $3, $4)
                        """, character_id, trait_name, trait_value, f"Dream's {trait_name.replace('_', ' ')}")
                        print(f"  ✅ {trait_name}: {trait_value[:60]}...")
                        total_imported += 1
                
                print(f"  ✅ {trait_name}: {str(trait_value)[:60]}...")
                total_imported += 1
        
        # 5. RESPONSE GUIDELINES from behavioral_patterns.interaction_guidelines + response_length
        print("\n📋 Importing RESPONSE GUIDELINES...")
        
        # From behavioral_patterns.interaction_guidelines (list format)
        if 'behavioral_patterns' in dream and 'interaction_guidelines' in dream['behavioral_patterns']:
            guidelines = dream['behavioral_patterns']['interaction_guidelines']
            
            if isinstance(guidelines, list):
                for idx, guideline_content in enumerate(guidelines):
                    await conn.execute("""
                        INSERT INTO character_response_guidelines 
                        (character_id, guideline_type, guideline_content, priority)
                        VALUES ($1, $2, $3, $4)
                    """, character_id, f'interaction_guideline_{idx+1}', guideline_content, 50 - idx)
                    
                    print(f"  ✅ guideline_{idx+1}: {guideline_content[:60]}...")
                    total_imported += 1
        
        # From communication.response_length
        if 'communication' in dream and 'response_length' in dream['communication']:
            response_length = dream['communication']['response_length']
            
            await conn.execute("""
                INSERT INTO character_response_guidelines 
                (character_id, guideline_type, guideline_content, priority)
                VALUES ($1, $2, $3, $4)
            """, character_id, 'response_length', response_length, 10)
            
            print(f"  ✅ response_length: {response_length[:60]}...")
            total_imported += 1
        
        # 6. AI SCENARIOS from behavioral_patterns.response_patterns
        print("\n🤖 Importing AI SCENARIOS...")
        if 'behavioral_patterns' in dream and 'response_patterns' in dream['behavioral_patterns']:
            patterns = dream['behavioral_patterns']['response_patterns']
            
            for pattern_type, pattern_content in patterns.items():
                await conn.execute("""
                    INSERT INTO character_ai_scenarios 
                    (character_id, scenario_type, scenario_name, tier_1_response)
                    VALUES ($1, $2, $3, $4)
                """, character_id, pattern_type, pattern_type.replace('_', ' ').title(), pattern_content)
                
                print(f"  ✅ {pattern_type}: {pattern_content[:60]}...")
                total_imported += 1
        
        # 7. EXPERTISE DOMAINS from dream_lord_abilities (Dream-specific)
        print("\n🎓 Importing EXPERTISE DOMAINS (Dream Lord Abilities)...")
        if 'dream_lord_abilities' in dream:
            abilities = dream['dream_lord_abilities']
            
            for ability_name, ability_description in abilities.items():
                await conn.execute("""
                    INSERT INTO character_expertise_domains 
                    (character_id, domain_name, expertise_level, passion_level, domain_description)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, ability_name.replace('_', ' ').title(), 'master', 95, ability_description)
                
                print(f"  ✅ {ability_name}: {ability_description[:60]}...")
                total_imported += 1
        
        # 8. CONVERSATION FLOWS from communication.conversation_flow_guidance
        print("\n💬 Importing CONVERSATION FLOWS...")
        if 'communication' in dream and 'conversation_flow_guidance' in dream['communication']:
            cfg = dream['communication']['conversation_flow_guidance']
            
            for flow_type, flow_data in cfg.items():
                if isinstance(flow_data, dict):
                    # Extract dict fields properly (NO JSON dump!)
                    energy = flow_data.get('energy', '')
                    approach = flow_data.get('approach', '')
                    transition = flow_data.get('transition_style', '')
                    
                    await conn.execute("""
                        INSERT INTO character_conversation_flows 
                        (character_id, flow_type, flow_name, energy_level, approach_description, transition_style, context)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, character_id, flow_type, flow_type.replace('_', ' ').title(), 
                         energy, approach, transition, f"Dream's {flow_type.replace('_', ' ')} guidance")
                    
                    print(f"  ✅ {flow_type}: {approach[:60]}...")
                    total_imported += 1
        
        # 9. EMOTIONAL TRIGGERS from emotional_profile.triggers (additional)
        print("\n💫 Importing ADDITIONAL EMOTIONAL TRIGGERS...")
        if 'emotional_profile' in dream and 'triggers' in dream['emotional_profile']:
            triggers = dream['emotional_profile']['triggers']
            
            for trigger_type, trigger_list in triggers.items():
                if isinstance(trigger_list, list):
                    for trigger_content in trigger_list:
                        await conn.execute("""
                            INSERT INTO character_emotional_triggers 
                            (character_id, trigger_type, trigger_content, emotional_response, response_intensity)
                            VALUES ($1, $2, $3, $4, $5)
                        """, character_id, trigger_type, trigger_content, trigger_type, 'high')
                        
                        print(f"  ✅ {trigger_type}: {trigger_content[:60]}...")
                        total_imported += 1
        
        print(f"\n{'='*70}")
        print("✨ IMPORT COMPLETE")
        print(f"{'='*70}")
        print(f"📊 Total new records imported: {total_imported}")
        
        # Verify final counts
        print("\n📈 FINAL RECORD COUNTS:")
        
        tables = [
            'character_response_guidelines',
            'character_message_triggers',
            'character_cultural_expressions',
            'character_emotional_triggers',
            'character_voice_traits',
            'character_expertise_domains',
            'character_ai_scenarios',
            'character_conversation_flows'
        ]
        
        for table in tables:
            count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {table} WHERE character_id = $1",
                character_id
            )
            print(f"  • {table.replace('character_', '')}: {count}")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(import_dream_extended())
