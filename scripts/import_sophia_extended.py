#!/usr/bin/env python3
"""
Import Sophia Blake Extended Data with Semantic Mapping
=======================================================

Sophia uses FLAT ROOT-LEVEL structure (NOT nested character object like Marcus/Ryan).
This script extracts extended data from Sophia's JSON and imports to RDBMS.

Target: ~80+ extended records
Current: 6 records (5 emoji, 1 expertise)
Missing: ~74+ records

Semantic Mapping Strategy:
- communication.message_pattern_triggers (nested dict with keywords/phrases) → character_message_triggers (~75: 4 categories with ~15-20 keywords each)
- speech_patterns.professional_vocabulary → character_voice_traits (~6 items)
- speech_patterns.decision_making_language → character_voice_traits (~5 items)
- speech_patterns.client_interaction_phrases → character_voice_traits (~5 items)
- expertise.primary_domains → character_expertise_domains (~3 domains)
- communication.conversation_flow_guidance → character_conversation_flows (~3 flows)

NOTE: Sophia has FLAT structure - sections at ROOT level, NOT nested under character!
- communication at ROOT (not character.communication)
- speech_patterns at ROOT (not character.speech_patterns)
- expertise at ROOT (not character.expertise)
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


async def import_sophia_extended():
    """Import Sophia Blake's missing extended data from JSON."""
    
    # Load Sophia's JSON (FLAT structure - sections at root level)
    sophia_json_path = Path(__file__).parent.parent / "characters" / "examples_legacy_backup" / "sophia_v2.json"
    with open(sophia_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Sophia's data is at ROOT level, not nested under 'character'
    
    print(f"{'='*70}")
    print("🔧 SOPHIA BLAKE EXTENDED DATA IMPORT (SEMANTIC MAPPING)")
    print(f"{'='*70}\n")
    
    # Initialize database connection
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get Sophia's character ID
        result = await conn.fetchrow(
            "SELECT id FROM characters WHERE name = 'Sophia Blake' LIMIT 1"
        )
        
        if not result:
            print("❌ Sophia Blake not found in database")
            return
        
        character_id = result['id']
        print(f"✅ Found Sophia Blake (ID: {character_id})\n")
        
        total_imported = 0
        
        # 1. MESSAGE TRIGGERS from communication.message_pattern_triggers (at ROOT level)
        print("📨 Importing MESSAGE TRIGGERS...")
        if 'communication' in data and 'message_pattern_triggers' in data['communication']:
            triggers_dict = data['communication']['message_pattern_triggers']
            
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
                    
                    print(f"  ✅ {category}: {len(keywords)} keywords")
        
        # 2. VOICE TRAITS from speech_patterns (at root level with lists)
        print("\n🗣️ Importing VOICE TRAITS...")
        if 'speech_patterns' in data:
            sp = data['speech_patterns']
            
            # Sophia's speech_patterns has lists of phrases
            for trait_name, trait_value in sp.items():
                if isinstance(trait_value, list):
                    # List of phrases - import each separately
                    for idx, phrase in enumerate(trait_value):
                        await conn.execute("""
                            INSERT INTO character_voice_traits 
                            (character_id, trait_type, trait_value, situational_context)
                            VALUES ($1, $2, $3, $4)
                        """, character_id, trait_name, phrase, f"Sophia's {trait_name.replace('_', ' ')} (phrase {idx+1})")
                        
                        print(f"  ✅ {trait_name} [{idx+1}]: {phrase[:60]}...")
                        total_imported += 1
                else:
                    # Single value
                    trait_str = json.dumps(trait_value) if isinstance(trait_value, dict) else str(trait_value)
                    await conn.execute("""
                        INSERT INTO character_voice_traits 
                        (character_id, trait_type, trait_value, situational_context)
                        VALUES ($1, $2, $3, $4)
                    """, character_id, trait_name, trait_str, f"Sophia's {trait_name.replace('_', ' ')}")
                    
                    print(f"  ✅ {trait_name}: {trait_str[:60]}...")
                    total_imported += 1
        
        # 3. EXPERTISE DOMAINS from expertise.primary_domains (at root level)
        print("\n🎓 Importing EXPERTISE DOMAINS...")
        if 'expertise' in data and 'primary_domains' in data['expertise']:
            domains = data['expertise']['primary_domains']
            
            if isinstance(domains, list):
                for domain_name in domains:
                    await conn.execute("""
                        INSERT INTO character_expertise_domains 
                        (character_id, domain_name, expertise_level, passion_level, domain_description)
                        VALUES ($1, $2, $3, $4, $5)
                    """, character_id, domain_name, 'expert', 95, f"Sophia's primary expertise in {domain_name}")
                    
                    print(f"  ✅ {domain_name}")
                    total_imported += 1
        
        # 4. CONVERSATION FLOWS from communication.conversation_flow_guidance
        print("\n� Importing CONVERSATION FLOWS...")
        if 'communication' in data and 'conversation_flow_guidance' in data['communication']:
            cfg = data['communication']['conversation_flow_guidance']
            
            # conversation_flow_guidance keys: varies by character
            for flow_type, flow_content in cfg.items():
                await conn.execute("""
                    INSERT INTO character_conversation_flows 
                    (character_id, flow_type, flow_name, approach_description, context)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, flow_type, flow_type.replace('_', ' ').title(), str(flow_content), f"Sophia's {flow_type.replace('_', ' ')} guidance")
                print(f"  ✅ {flow_type}: {str(flow_content)[:60]}...")
                total_imported += 1
        
        print(f"\n{'='*70}")
        print("✨ IMPORT COMPLETE")
        print(f"{'='*70}")
        print(f"📊 Total new records imported: {total_imported}")
        
        # Verify final counts (Sophia has different structure than Ryan/Marcus)
        print("\n📈 FINAL RECORD COUNTS:")
        
        tables = [
            'character_message_triggers',
            'character_voice_traits',
            'character_expertise_domains',
            'character_conversation_flows',
            'character_emoji_patterns'
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
    asyncio.run(import_sophia_extended())
