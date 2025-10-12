#!/usr/bin/env python3
"""
Import Dr. Marcus Thompson Extended Data with Semantic Mapping
===============================================================

Marcus uses NESTED character object format with unique semantic mappings.
This script extracts extended data from Marcus's JSON and imports to RDBMS.

Target: ~50+ extended records
Current: 6 records (5 emoji, 1 expertise)
Missing: ~44+ records

Semantic Mapping Strategy:
- communication.typical_responses → character_cultural_expressions (~9)
- communication.emotional_expressions → character_emotional_triggers (~4)
- communication.message_pattern_triggers → character_message_triggers (~25 keywords)
- communication.conversation_flow_guidance → character_conversation_flows (~4)
- communication.response_length → character_response_guidelines (~1)
- voice.speech_patterns → character_voice_traits (~1 trait)
- voice.common_phrases → character_cultural_expressions (~5)
- memory_integration.knowledge_areas → character_expertise_domains (~2)
- relationship_dynamics.adaptation_patterns → character_ai_scenarios (~3)
- behavioral_patterns.decision_making → character_response_guidelines (~3)
- behavioral_patterns.problem_solving → character_ai_scenarios (~3)
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


async def import_marcus_extended():
    """Import Dr. Marcus Thompson's missing extended data from JSON."""
    
    # Load Marcus's JSON
    marcus_json_path = Path(__file__).parent.parent / "characters" / "examples_legacy_backup" / "marcus.json"
    with open(marcus_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        marcus = data['character']
    
    print(f"{'='*70}")
    print("🔧 DR. MARCUS THOMPSON EXTENDED DATA IMPORT (SEMANTIC MAPPING)")
    print(f"{'='*70}\n")
    
    # Initialize database connection
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get Marcus's character ID
        result = await conn.fetchrow(
            "SELECT id FROM characters WHERE name = 'Dr. Marcus Thompson' LIMIT 1"
        )
        
        if not result:
            print("❌ Dr. Marcus Thompson not found in database")
            return
        
        character_id = result['id']
        print(f"✅ Found Dr. Marcus Thompson (ID: {character_id})\n")
        
        total_imported = 0
        
        # 1. MESSAGE TRIGGERS from communication.message_pattern_triggers
        print("📨 Importing MESSAGE TRIGGERS...")
        if 'communication' in marcus and 'message_pattern_triggers' in marcus['communication']:
            triggers_dict = marcus['communication']['message_pattern_triggers']
            
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
        if 'communication' in marcus and 'typical_responses' in marcus['communication']:
            responses = marcus['communication']['typical_responses']
            
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
        if 'communication' in marcus and 'emotional_expressions' in marcus['communication']:
            emotions = marcus['communication']['emotional_expressions']
            
            for emotion, expression in emotions.items():
                await conn.execute("""
                    INSERT INTO character_emotional_triggers 
                    (character_id, trigger_type, trigger_content, emotional_response, response_intensity)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, emotion, emotion, expression, 'medium')
                
                print(f"  ✅ {emotion}: {expression[:60]}...")
                total_imported += 1
        
        # 4. VOICE TRAITS from voice.speech_patterns (STRING) and voice.common_phrases (LIST)
        print("\n🗣️ Importing VOICE TRAITS...")
        if 'voice' in marcus:
            # speech_patterns is a STRING (91 chars) not a dict
            if 'speech_patterns' in marcus['voice']:
                speech_pattern = marcus['voice']['speech_patterns']
                
                await conn.execute("""
                    INSERT INTO character_voice_traits 
                    (character_id, trait_type, trait_value, situational_context)
                    VALUES ($1, $2, $3, $4)
                """, character_id, 'speech_patterns', speech_pattern, "Marcus's characteristic speech style")
                
                print(f"  ✅ speech_patterns: {speech_pattern[:60]}...")
                total_imported += 1
            
            # common_phrases is a LIST
            if 'common_phrases' in marcus['voice']:
                for idx, phrase in enumerate(marcus['voice']['common_phrases']):
                    await conn.execute("""
                        INSERT INTO character_voice_traits 
                        (character_id, trait_type, trait_value, situational_context)
                        VALUES ($1, $2, $3, $4)
                    """, character_id, f'common_phrase_{idx+1}', phrase, "Frequently used expression")
                    
                    print(f"  ✅ common_phrase_{idx+1}: {phrase[:60]}...")
                    total_imported += 1
        
        # 5. RESPONSE GUIDELINES from communication.response_length + behavioral_patterns.decision_making
        print("\n📋 Importing RESPONSE GUIDELINES...")
        
        # From communication.response_length
        if 'communication' in marcus and 'response_length' in marcus['communication']:
            response_length = marcus['communication']['response_length']
            
            await conn.execute("""
                INSERT INTO character_response_guidelines 
                (character_id, guideline_type, guideline_content, priority)
                VALUES ($1, $2, $3, $4)
            """, character_id, 'response_length', response_length, 100)
            
            print(f"  ✅ response_length: {response_length[:80]}...")
            total_imported += 1
        
        # From behavioral_patterns.decision_making (dict with 3 keys)
        if 'behavioral_patterns' in marcus and 'decision_making' in marcus['behavioral_patterns']:
            dm = marcus['behavioral_patterns']['decision_making']
            
            for key, value in dm.items():
                await conn.execute("""
                    INSERT INTO character_response_guidelines 
                    (character_id, guideline_type, guideline_content, priority)
                    VALUES ($1, $2, $3, $4)
                """, character_id, f'decision_making_{key}', str(value), 80)
                
                print(f"  ✅ decision_making_{key}: {str(value)[:60]}...")
                total_imported += 1
        
        # 6. AI SCENARIOS from relationship_dynamics.adaptation_patterns + behavioral_patterns.problem_solving
        print("\n🤖 Importing AI SCENARIOS...")
        
        # From relationship_dynamics.adaptation_patterns (dict with 3 keys)
        if 'relationship_dynamics' in marcus and 'adaptation_patterns' in marcus['relationship_dynamics']:
            patterns = marcus['relationship_dynamics']['adaptation_patterns']
            
            for pattern_type, pattern_content in patterns.items():
                await conn.execute("""
                    INSERT INTO character_ai_scenarios 
                    (character_id, scenario_type, scenario_name, tier_1_response)
                    VALUES ($1, $2, $3, $4)
                """, character_id, 'adaptation_pattern', pattern_type.replace('_', ' ').title(), str(pattern_content))
                
                print(f"  ✅ adaptation: {pattern_type}: {str(pattern_content)[:60]}...")
                total_imported += 1
        
        # From behavioral_patterns.problem_solving (dict with 3 keys)
        if 'behavioral_patterns' in marcus and 'problem_solving' in marcus['behavioral_patterns']:
            ps = marcus['behavioral_patterns']['problem_solving']
            
            for key, value in ps.items():
                await conn.execute("""
                    INSERT INTO character_ai_scenarios 
                    (character_id, scenario_type, scenario_name, tier_1_response)
                    VALUES ($1, $2, $3, $4)
                """, character_id, 'problem_solving', key.replace('_', ' ').title(), str(value))
                
                print(f"  ✅ problem_solving_{key}: {str(value)[:60]}...")
                total_imported += 1
        
        # 7. EXPERTISE DOMAINS from memory_integration.knowledge_areas
        print("\n🎓 Importing EXPERTISE DOMAINS...")
        if 'memory_integration' in marcus and 'knowledge_areas' in marcus['memory_integration']:
            ka = marcus['memory_integration']['knowledge_areas']
            
            # knowledge_areas has: deep_expertise, working_knowledge (dict with 2 keys)
            for expertise_level, domains_list in ka.items():
                if isinstance(domains_list, list):
                    for domain_name in domains_list:
                        await conn.execute("""
                            INSERT INTO character_expertise_domains 
                            (character_id, domain_name, expertise_level, passion_level, domain_description)
                            VALUES ($1, $2, $3, $4, $5)
                        """, character_id, domain_name, expertise_level, 90 if expertise_level == 'deep_expertise' else 70, 
                        f"Marcus's {expertise_level.replace('_', ' ')} in {domain_name}")
                        
                        print(f"  ✅ {domain_name} ({expertise_level})")
                        total_imported += 1
        
        # 8. CONVERSATION FLOWS from communication.conversation_flow_guidance
        print("\n💬 Importing CONVERSATION FLOWS...")
        if 'communication' in marcus and 'conversation_flow_guidance' in marcus['communication']:
            cfg = marcus['communication']['conversation_flow_guidance']
            
            # conversation_flow_guidance has 4 keys: technical_education, ethical_discussion, general, response_style
            for flow_type, flow_content in cfg.items():
                await conn.execute("""
                    INSERT INTO character_conversation_flows 
                    (character_id, flow_type, flow_name, approach_description, context)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, flow_type, flow_type.replace('_', ' ').title(), str(flow_content), f"Marcus's {flow_type.replace('_', ' ')} guidance")
                
                print(f"  ✅ {flow_type}: {str(flow_content)[:60]}...")
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
    asyncio.run(import_marcus_extended())
