#!/usr/bin/env python3
"""
AETHYS EXTENDED DATA IMPORT - SEMANTIC MAPPING

Character: Aethys (ID: 2)
Source: characters/examples_legacy_backup/aethys.json
Target: PostgreSQL extended data tables

Import Strategy:
- message_pattern_triggers → character_message_triggers (keywords + phrases)
- typical_responses → character_cultural_expressions
- emotional_expressions → character_emotional_triggers
- speaking_patterns → character_voice_traits (with vocabulary extraction)
- conversation_flow_guidance → character_conversation_flows
- mystical_abilities → character_expertise_domains
- response_length → character_response_guidelines

CRITICAL: Vocabulary extraction pattern applied from the start:
- preferred_words LIST → individual records (trait_type='preferred_word')
- avoided_words LIST → individual records (trait_type='avoided_word')
- String fields → single records
NO JSON dumps!
"""

import asyncio
import asyncpg
import json
import os
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5433)),
    'database': os.getenv('POSTGRES_DB', 'whisperengine'),
    'user': os.getenv('POSTGRES_USER', 'whisperengine'),
    'password': os.getenv('POSTGRES_PASSWORD', 'whisperengine123')
}

async def import_aethys_extended():
    """Import Aethys extended data with semantic mapping"""
    
    # Load Aethys JSON
    json_path = Path('characters/examples_legacy_backup/aethys.json')
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    aethys = data.get('character', {})
    
    # Connect to database
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        print("=" * 70)
        print("🔧 AETHYS EXTENDED DATA IMPORT (SEMANTIC MAPPING)")
        print("=" * 70)
        
        # Get character_id
        character_id = await conn.fetchval("SELECT id FROM characters WHERE name = 'Aethys'")
        if not character_id:
            print("❌ Aethys not found in database!")
            return
        
        print(f"\n✅ Found Aethys (ID: {character_id})")
        
        total_imported = 0
        
        # 1. MESSAGE TRIGGERS from communication.message_pattern_triggers
        print("\n📨 Importing MESSAGE TRIGGERS...")
        if 'communication' in aethys and 'message_pattern_triggers' in aethys['communication']:
            triggers = aethys['communication']['message_pattern_triggers']
            
            for trigger_category, trigger_data in triggers.items():
                # Extract keywords
                if isinstance(trigger_data, dict) and 'keywords' in trigger_data:
                    keywords = trigger_data['keywords']
                    if isinstance(keywords, list):
                        for keyword in keywords:
                            await conn.execute("""
                                INSERT INTO character_message_triggers 
                                (character_id, trigger_category, trigger_type, trigger_value)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, trigger_category, 'keyword', keyword)
                            total_imported += 1
                        
                        print(f"  ✅ {trigger_category}: {len(keywords)} keywords from {', '.join(keywords[:3])}...")
                
                # Extract phrases
                if isinstance(trigger_data, dict) and 'phrases' in trigger_data:
                    phrases = trigger_data['phrases']
                    if isinstance(phrases, list):
                        for phrase in phrases:
                            await conn.execute("""
                                INSERT INTO character_message_triggers 
                                (character_id, trigger_category, trigger_type, trigger_value)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, trigger_category, 'phrase', phrase)
                            total_imported += 1
                        
                        print(f"  ✅ {trigger_category}: {len(phrases)} phrases added")
        
        # 2. CULTURAL EXPRESSIONS from communication.typical_responses
        print("\n🌍 Importing CULTURAL EXPRESSIONS...")
        if 'communication' in aethys and 'typical_responses' in aethys['communication']:
            responses = aethys['communication']['typical_responses']
            
            for response_type, response_list in responses.items():
                if isinstance(response_list, list):
                    for idx, response_text in enumerate(response_list):
                        await conn.execute("""
                            INSERT INTO character_cultural_expressions 
                            (character_id, expression_type, expression_value, meaning, usage_context)
                            VALUES ($1, $2, $3, $4, $5)
                        """, character_id, response_type, response_text, 
                            response_type.replace('_', ' ').title(), f"Typical {response_type} response")
                        
                        print(f"  ✅ {response_type} [{idx+1}]: {response_text[:60]}...")
                        total_imported += 1
        
        # 3. EMOTIONAL TRIGGERS from communication.emotional_expressions
        print("\n💭 Importing EMOTIONAL TRIGGERS...")
        if 'communication' in aethys and 'emotional_expressions' in aethys['communication']:
            emotions = aethys['communication']['emotional_expressions']
            
            for emotion, expression in emotions.items():
                await conn.execute("""
                    INSERT INTO character_emotional_triggers 
                    (character_id, trigger_type, trigger_content, emotional_response, response_intensity)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, emotion, emotion, expression, 'high')
                
                print(f"  ✅ {emotion}: {expression[:60]}...")
                total_imported += 1
        
        # 4. VOICE TRAITS from speaking_patterns (WITH VOCABULARY EXTRACTION)
        print("\n🗣️ Importing VOICE TRAITS...")
        if 'speaking_patterns' in aethys:
            sp = aethys['speaking_patterns']
            
            for trait_name, trait_value in sp.items():
                # Handle vocabulary specially - it's a SIMPLE STRING, not a dict!
                # Aethys has: "vocabulary": "cosmic, transcendent, infinite..."
                if trait_name == 'vocabulary':
                    # Store as single record - it's already a string
                    if isinstance(trait_value, str):
                        await conn.execute("""
                            INSERT INTO character_voice_traits 
                            (character_id, trait_type, trait_value, situational_context)
                            VALUES ($1, $2, $3, $4)
                        """, character_id, 'vocabulary', trait_value, "Aethys's cosmic vocabulary")
                        print(f"  ✅ vocabulary: {trait_value[:80]}...")
                        total_imported += 1
                else:
                    # Store other traits as-is (strings)
                    if isinstance(trait_value, str):
                        await conn.execute("""
                            INSERT INTO character_voice_traits 
                            (character_id, trait_type, trait_value, situational_context)
                            VALUES ($1, $2, $3, $4)
                        """, character_id, trait_name, trait_value, f"Aethys's {trait_name.replace('_', ' ')}")
                        print(f"  ✅ {trait_name}: {trait_value[:60]}...")
                        total_imported += 1
        
        # 5. RESPONSE GUIDELINES from communication.response_length
        print("\n📋 Importing RESPONSE GUIDELINES...")
        if 'communication' in aethys and 'response_length' in aethys['communication']:
            response_length = aethys['communication']['response_length']
            
            await conn.execute("""
                INSERT INTO character_response_guidelines 
                (character_id, guideline_type, guideline_content, priority)
                VALUES ($1, $2, $3, $4)
            """, character_id, 'response_length', response_length, 100)
            
            print(f"  ✅ response_length: {response_length[:80]}...")
            total_imported += 1
        
        # 6. CONVERSATION FLOWS from communication.conversation_flow_guidance
        print("\n💬 Importing CONVERSATION FLOWS...")
        if 'communication' in aethys and 'conversation_flow_guidance' in aethys['communication']:
            flows = aethys['communication']['conversation_flow_guidance']
            
            for flow_name, flow_data in flows.items():
                # Extract fields from dict
                if isinstance(flow_data, dict):
                    energy = flow_data.get('energy', flow_data.get('default_energy', ''))
                    approach = flow_data.get('approach', flow_data.get('conversation_style', ''))
                    transition = flow_data.get('transition_style', flow_data.get('transition_approach', ''))
                    context = flow_data.get('response_patterns', '')
                    
                    # Convert response_patterns dict to string if needed
                    if isinstance(context, dict):
                        context = str(context)
                    
                    await conn.execute("""
                        INSERT INTO character_conversation_flows 
                        (character_id, flow_type, flow_name, energy_level, approach_description, transition_style, context)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, character_id, flow_name, flow_name.replace('_', ' ').title(), 
                        energy, approach, transition, context)
                    
                    print(f"  ✅ {flow_name}: {approach[:60] if approach else energy[:60]}...")
                    total_imported += 1
        
        # 7. EXPERTISE DOMAINS from mystical_abilities
        print("\n🎓 Importing EXPERTISE DOMAINS (Mystical Abilities)...")
        if 'mystical_abilities' in aethys:
            abilities = aethys['mystical_abilities']
            
            # mystical_abilities is likely a dict with ability names as keys
            if isinstance(abilities, dict):
                for ability_name, ability_desc in abilities.items():
                    # Create description from ability data
                    if isinstance(ability_desc, dict):
                        desc = ability_desc.get('description', str(ability_desc))
                    else:
                        desc = str(ability_desc)
                    
                    await conn.execute("""
                        INSERT INTO character_expertise_domains 
                        (character_id, domain_name, expertise_level, passion_level, domain_description)
                        VALUES ($1, $2, $3, $4, $5)
                    """, character_id, ability_name.replace('_', ' ').title(), 'omnipotent', 100, desc[:500])
                    
                    print(f"  ✅ {ability_name}: {desc[:60] if isinstance(desc, str) else 'mystical ability'}...")
                    total_imported += 1
            elif isinstance(abilities, list):
                for ability in abilities:
                    await conn.execute("""
                        INSERT INTO character_expertise_domains 
                        (character_id, domain_name, expertise_level, passion_level, domain_description)
                        VALUES ($1, $2, $3, $4, $5)
                    """, character_id, ability.replace('_', ' ').title(), 'omnipotent', 100, f"Aethys's {ability}")
                    
                    print(f"  ✅ {ability}")
                    total_imported += 1
        
        print("\n" + "=" * 70)
        print("✨ IMPORT COMPLETE")
        print("=" * 70)
        print(f"📊 Total new records imported: {total_imported}")
        
        # Show final counts
        print("\n📈 FINAL RECORD COUNTS:")
        tables = [
            ('response_guidelines', 'character_response_guidelines'),
            ('message_triggers', 'character_message_triggers'),
            ('cultural_expressions', 'character_cultural_expressions'),
            ('emotional_triggers', 'character_emotional_triggers'),
            ('voice_traits', 'character_voice_traits'),
            ('expertise_domains', 'character_expertise_domains'),
            ('conversation_flows', 'character_conversation_flows')
        ]
        
        for label, table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table} WHERE character_id = $1", character_id)
            print(f"  • {label}: {count}")
    
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(import_aethys_extended())
