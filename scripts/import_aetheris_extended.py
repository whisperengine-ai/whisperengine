#!/usr/bin/env python3
"""
Import Aetheris (Liln) Extended Data with Semantic Mapping
===========================================================

Aetheris uses NESTED character object format (different from Elena's flat structure).
This script extracts extended data from Aetheris's JSON and imports to RDBMS.

Target: ~26 extended records total
Current: 8 records (5 emoji, 1 expertise, 2 conversation_flows)
Missing: ~18 records (emotional_triggers, voice_traits, ai_scenarios, expertise_domains)

Semantic Mapping:
- emotional_profile.triggers → character_emotional_triggers (positive/negative lists)
- speech_patterns → character_voice_traits (4 traits: vocabulary, sentence_structure, punctuation_style, response_length)
- behavioral_patterns.response_patterns → character_ai_scenarios (5 scenarios)
- capabilities.knowledge_domains → character_expertise_domains (6 domains)
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


async def import_aetheris_extended():
    """Import Aetheris's missing extended data from JSON."""
    
    # Load Aetheris's JSON
    aetheris_json_path = Path(__file__).parent.parent / "characters" / "examples_legacy_backup" / "aetheris.json"
    with open(aetheris_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        aetheris = data['character']
    
    print(f"{'='*70}")
    print("🔧 AETHERIS (LILN) EXTENDED DATA IMPORT (SEMANTIC MAPPING)")
    print(f"{'='*70}\n")
    
    # Initialize database connection
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get Aetheris's character ID
        result = await conn.fetchrow(
            "SELECT id FROM characters WHERE name = 'Aetheris' LIMIT 1"
        )
        
        if not result:
            print("❌ Aetheris not found in database")
            return
        
        character_id = result['id']
        print(f"✅ Found Aetheris (ID: {character_id})\n")
        
        total_imported = 0
        
        # 1. EMOTIONAL TRIGGERS from emotional_profile.triggers
        print("� Importing EMOTIONAL TRIGGERS...")
        if 'emotional_profile' in aetheris and 'triggers' in aetheris['emotional_profile']:
            triggers = aetheris['emotional_profile']['triggers']
            
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
        
        # 2. VOICE TRAITS from speech_patterns
        print("\n🗣️ Importing VOICE TRAITS...")
        if 'speech_patterns' in aetheris:
            sp = aetheris['speech_patterns']
            
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
                            """, character_id, 'preferred_word', word, "Words Aetheris naturally uses")
                            total_imported += 1
                    
                    # Extract avoided_words list
                    if 'avoided_words' in trait_value and isinstance(trait_value['avoided_words'], list):
                        for word in trait_value['avoided_words']:
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, 'avoided_word', word, "Words Aetheris avoids")
                            total_imported += 1
                    
                    # Extract philosophical_terms (string)
                    if 'philosophical_terms' in trait_value and isinstance(trait_value['philosophical_terms'], str):
                        await conn.execute("""
                            INSERT INTO character_voice_traits 
                            (character_id, trait_type, trait_value, situational_context)
                            VALUES ($1, $2, $3, $4)
                        """, character_id, 'philosophical_terms', trait_value['philosophical_terms'], "Aetheris's philosophical terms")
                        total_imported += 1
                    
                    # Extract poetic_language (string)
                    if 'poetic_language' in trait_value and isinstance(trait_value['poetic_language'], str):
                        await conn.execute("""
                            INSERT INTO character_voice_traits 
                            (character_id, trait_type, trait_value, situational_context)
                            VALUES ($1, $2, $3, $4)
                        """, character_id, 'poetic_language', trait_value['poetic_language'], "Aetheris's poetic language")
                        total_imported += 1
                    
                    print(f"  ✅ vocabulary: extracted {len(trait_value.get('preferred_words', []))} preferred, {len(trait_value.get('avoided_words', []))} avoided words")
                else:
                    # Store other traits as-is (strings)
                    if isinstance(trait_value, str):
                        await conn.execute("""
                            INSERT INTO character_voice_traits 
                            (character_id, trait_type, trait_value, situational_context)
                            VALUES ($1, $2, $3, $4)
                        """, character_id, trait_name, trait_value, f"Aetheris's {trait_name.replace('_', ' ')}")
                        print(f"  ✅ {trait_name}: {trait_value[:60]}...")
                        total_imported += 1
        
        # 3. AI SCENARIOS from behavioral_patterns.response_patterns
        print("\n🤖 Importing AI SCENARIOS...")
        if 'behavioral_patterns' in aetheris and 'response_patterns' in aetheris['behavioral_patterns']:
            patterns = aetheris['behavioral_patterns']['response_patterns']
            
            for pattern_type, pattern_content in patterns.items():
                await conn.execute("""
                    INSERT INTO character_ai_scenarios 
                    (character_id, scenario_type, scenario_name, tier_1_response)
                    VALUES ($1, $2, $3, $4)
                """, character_id, pattern_type, pattern_type.replace('_', ' ').title(), pattern_content)
                
                print(f"  ✅ {pattern_type}: {pattern_content[:60]}...")
                total_imported += 1
        
        # 4. EXPERTISE DOMAINS from capabilities.knowledge_domains
        print("\n🎓 Importing EXPERTISE DOMAINS...")
        if 'capabilities' in aetheris and 'knowledge_domains' in aetheris['capabilities']:
            domains = aetheris['capabilities']['knowledge_domains']
            
            for domain in domains:
                await conn.execute("""
                    INSERT INTO character_expertise_domains 
                    (character_id, domain_name, expertise_level, passion_level, domain_description)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, domain, 'expert', 95, f"Aetheris's expertise in {domain}")
                
                print(f"  ✅ {domain}")
                total_imported += 1
        
        print(f"\n{'='*70}")
        print("✨ IMPORT COMPLETE")
        print(f"{'='*70}")
        print(f"📊 Total new records imported: {total_imported}")
        
        # Verify final counts
        print("\n📈 FINAL RECORD COUNTS:")
        
        tables = [
            'character_emotional_triggers',
            'character_voice_traits',
            'character_ai_scenarios',
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
    asyncio.run(import_aetheris_extended())
