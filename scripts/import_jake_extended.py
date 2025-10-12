#!/usr/bin/env python3
"""
Import Jake Sterling Extended Data with Semantic Mapping
=========================================================

Jake uses NESTED character object format (different from Elena's flat structure).
This script extracts extended data from Jake's JSON and imports to RDBMS.

Target: ~23 extended records total
Current: 10 records (5 emoji, 1 expertise, 4 conversation_flows)
Missing: ~13 records (message_triggers, cultural_expressions, emotional_triggers, voice_traits, response_guidelines)

Semantic Mapping:
- communication.message_pattern_triggers → character_message_triggers
- communication.typical_responses → character_cultural_expressions
- communication.emotional_expressions → character_emotional_triggers
- interests.expertise → character_expertise_domains (additional)
- speech_patterns → character_voice_traits
- communication.response_length → character_response_guidelines
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


async def import_jake_extended():
    """Import Jake's missing extended data from JSON."""
    
    # Load Jake's JSON
    jake_json_path = Path(__file__).parent.parent / "characters" / "examples_legacy_backup" / "jake.json"
    with open(jake_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        jake = data['character']
    
    print(f"{'='*70}")
    print("🔧 JAKE STERLING EXTENDED DATA IMPORT (SEMANTIC MAPPING)")
    print(f"{'='*70}\n")
    
    # Initialize database connection
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get Jake's character ID
        result = await conn.fetchrow(
            "SELECT id FROM characters WHERE name = 'Jake Sterling' LIMIT 1"
        )
        
        if not result:
            print("❌ Jake Sterling not found in database")
            return
        
        character_id = result['id']
        print(f"✅ Found Jake Sterling (ID: {character_id})\n")
        
        total_imported = 0
        
        # 1. MESSAGE TRIGGERS from communication.message_pattern_triggers
        print("📨 Importing MESSAGE TRIGGERS...")
        if 'communication' in jake and 'message_pattern_triggers' in jake['communication']:
            triggers_dict = jake['communication']['message_pattern_triggers']
            
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
        if 'communication' in jake and 'typical_responses' in jake['communication']:
            responses = jake['communication']['typical_responses']
            
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
        if 'communication' in jake and 'emotional_expressions' in jake['communication']:
            emotions = jake['communication']['emotional_expressions']
            
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
        if 'speech_patterns' in jake:
            sp = jake['speech_patterns']
            
            for trait_name, trait_value in sp.items():
                if trait_name == 'patterns_reference':
                    continue  # Skip reference field
                
                # Handle vocabulary dict specially - extract lists
                if trait_name == 'vocabulary' and isinstance(trait_value, dict):
                    # Extract preferred_words list (may be empty)
                    if 'preferred_words' in trait_value and isinstance(trait_value['preferred_words'], list):
                        for word in trait_value['preferred_words']:
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, 'preferred_word', word, "Words Jake naturally uses")
                            total_imported += 1
                    
                    # Extract avoided_words list (may be empty)
                    if 'avoided_words' in trait_value and isinstance(trait_value['avoided_words'], list):
                        for word in trait_value['avoided_words']:
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, 'avoided_word', word, "Words Jake avoids")
                            total_imported += 1
                    
                    # Extract any other string fields
                    for key in ['technical_terms', 'colloquialisms', 'grounding_phrases', 'signature_expressions']:
                        if key in trait_value and isinstance(trait_value[key], str):
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, key, trait_value[key], f"Jake's {key.replace('_', ' ')}")
                            total_imported += 1
                    
                    pref_count = len(trait_value.get('preferred_words', []))
                    avoid_count = len(trait_value.get('avoided_words', []))
                    if pref_count > 0 or avoid_count > 0:
                        print(f"  ✅ vocabulary: extracted {pref_count} preferred, {avoid_count} avoided words")
                    else:
                        print(f"  ✅ vocabulary: empty lists (no words to extract)")
                else:
                    # Store other traits as-is (strings)
                    if isinstance(trait_value, str):
                        await conn.execute("""
                            INSERT INTO character_voice_traits 
                            (character_id, trait_type, trait_value, situational_context)
                            VALUES ($1, $2, $3, $4)
                        """, character_id, trait_name, trait_value, f"Jake's {trait_name.replace('_', ' ')}")
                        print(f"  ✅ {trait_name}: {trait_value[:60]}...")
                        total_imported += 1
        
        # 5. EXPERTISE DOMAINS from interests.expertise (additional)
        print("\n🎓 Importing EXPERTISE DOMAINS (additional)...")
        if 'interests' in jake and 'expertise' in jake['interests']:
            expertise_list = jake['interests']['expertise']
            
            for expertise in expertise_list:
                await conn.execute("""
                    INSERT INTO character_expertise_domains 
                    (character_id, domain_name, expertise_level, passion_level, domain_description)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, expertise, 'expert', 85, f"Jake's expertise in {expertise}")
                
                print(f"  ✅ {expertise}")
                total_imported += 1
        
        # 6. RESPONSE GUIDELINES from communication.response_length
        print("\n📋 Importing RESPONSE GUIDELINES...")
        if 'communication' in jake and 'response_length' in jake['communication']:
            response_length = jake['communication']['response_length']
            
            await conn.execute("""
                INSERT INTO character_response_guidelines 
                (character_id, guideline_type, guideline_content, priority)
                VALUES ($1, $2, $3, $4)
            """, character_id, 'response_length', response_length, 10)
            
            print(f"  ✅ response_length: {response_length[:60]}...")
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
            'character_expertise_domains'
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
    asyncio.run(import_jake_extended())
