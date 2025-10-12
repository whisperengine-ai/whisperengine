#!/usr/bin/env python3
"""
Import Ryan Chen Extended Data with Semantic Mapping
====================================================

Ryan uses NESTED character object format with simpler structure than Ryan.
This script extracts extended data from Ryan's JSON and imports to RDBMS.

Target: ~21 extended records
Current: 6 records (5 emoji, 1 expertise)
Missing: ~15+ records

Semantic Mapping Strategy:
- communication.typical_responses → character_cultural_expressions (~9: greeting, encouragement, technical_advice)
- communication.emotional_expressions → character_emotional_triggers (~4: excitement, frustration, satisfaction, curiosity)
- communication.message_pattern_triggers → character_message_triggers (creative_collaboration, technical_discussion - may be empty)
- communication.conversation_flow_guidance → character_conversation_flows (~4: technical_discussion, creative_collaboration, general, response_style)
- communication.response_length → character_response_guidelines (~1)
- speech_patterns (at root level, dict) → character_voice_traits (~3: vocabulary, sentence_structure, response_length)

NOTE: Ryan has NO memory_integration, NO relationship_dynamics, NO behavioral_patterns sections!
Ryan is SIMPLER than Ryan - focus on communication and speech_patterns only.
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


async def import_ryan_extended():
    """Import Ryan Chen's missing extended data from JSON."""
    
    # Load Ryan's JSON
    ryan_json_path = Path(__file__).parent.parent / "characters" / "examples_legacy_backup" / "ryan.json"
    with open(ryan_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        ryan = data['character']
    
    print(f"{'='*70}")
    print("🔧 DR. MARCUS THOMPSON EXTENDED DATA IMPORT (SEMANTIC MAPPING)")
    print(f"{'='*70}\n")
    
    # Initialize database connection
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # Get Ryan's character ID
        result = await conn.fetchrow(
            "SELECT id FROM characters WHERE name = 'Ryan Chen' LIMIT 1"
        )
        
        if not result:
            print("❌ Ryan Chen not found in database")
            return
        
        character_id = result['id']
        print(f"✅ Found Ryan Chen (ID: {character_id})\n")
        
        total_imported = 0
        
        # 1. MESSAGE TRIGGERS from communication.message_pattern_triggers
        print("📨 Importing MESSAGE TRIGGERS...")
        if 'communication' in ryan and 'message_pattern_triggers' in ryan['communication']:
            triggers_dict = ryan['communication']['message_pattern_triggers']
            
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
        if 'communication' in ryan and 'typical_responses' in ryan['communication']:
            responses = ryan['communication']['typical_responses']
            
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
        if 'communication' in ryan and 'emotional_expressions' in ryan['communication']:
            emotions = ryan['communication']['emotional_expressions']
            
            for emotion, expression in emotions.items():
                await conn.execute("""
                    INSERT INTO character_emotional_triggers 
                    (character_id, trigger_type, trigger_content, emotional_response, response_intensity)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, emotion, emotion, expression, 'medium')
                
                print(f"  ✅ {emotion}: {expression[:60]}...")
                total_imported += 1
        
        # 4. VOICE TRAITS from speech_patterns (at root level, dict with 3 keys)
        print("\n🗣️ Importing VOICE TRAITS...")
        if 'speech_patterns' in ryan:
            sp = ryan['speech_patterns']
            
            # speech_patterns is a dict at root level (vocabulary, sentence_structure, response_length)
            for trait_name, trait_value in sp.items():
                # Handle vocabulary dict specially - extract lists
                if trait_name == 'vocabulary' and isinstance(trait_value, dict):
                    # Extract preferred_words list
                    if 'preferred_words' in trait_value and isinstance(trait_value['preferred_words'], list):
                        for word in trait_value['preferred_words']:
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, 'preferred_word', word, "Words Ryan naturally uses")
                            total_imported += 1
                    
                    # Extract avoided_words list
                    if 'avoided_words' in trait_value and isinstance(trait_value['avoided_words'], list):
                        for word in trait_value['avoided_words']:
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, 'avoided_word', word, "Words Ryan avoids")
                            total_imported += 1
                    
                    # Extract any other string fields (if present)
                    for key in ['technical_terms', 'colloquialisms', 'grounding_phrases', 'signature_expressions']:
                        if key in trait_value and isinstance(trait_value[key], str):
                            await conn.execute("""
                                INSERT INTO character_voice_traits 
                                (character_id, trait_type, trait_value, situational_context)
                                VALUES ($1, $2, $3, $4)
                            """, character_id, key, trait_value[key], f"Ryan's {key.replace('_', ' ')}")
                            total_imported += 1
                    
                    print(f"  ✅ vocabulary: extracted {len(trait_value.get('preferred_words', []))} preferred, {len(trait_value.get('avoided_words', []))} avoided words")
                else:
                    # Store other traits as-is (strings)
                    if isinstance(trait_value, str):
                        await conn.execute("""
                            INSERT INTO character_voice_traits 
                            (character_id, trait_type, trait_value, situational_context)
                            VALUES ($1, $2, $3, $4)
                        """, character_id, trait_name, trait_value, f"Ryan's {trait_name.replace('_', ' ')}")
                        print(f"  ✅ {trait_name}: {trait_value[:60]}...")
                        total_imported += 1
        
        # 5. RESPONSE GUIDELINES from communication.response_length
        print("\n📋 Importing RESPONSE GUIDELINES...")
        
        # From communication.response_length
        if 'communication' in ryan and 'response_length' in ryan['communication']:
            response_length = ryan['communication']['response_length']
            
            await conn.execute("""
                INSERT INTO character_response_guidelines 
                (character_id, guideline_type, guideline_content, priority)
                VALUES ($1, $2, $3, $4)
            """, character_id, 'response_length', response_length, 100)
            
            print(f"  ✅ response_length: {response_length[:80]}...")
            total_imported += 1
        
        # 5. RESPONSE GUIDELINES from communication.response_length + behavioral_patterns.decision_making
        print("\n📋 Importing RESPONSE GUIDELINES...")
        
        # From communication.response_length
        if 'communication' in ryan and 'response_length' in ryan['communication']:
            response_length = ryan['communication']['response_length']
            
            await conn.execute("""
                INSERT INTO character_response_guidelines 
                (character_id, guideline_type, guideline_content, priority)
                VALUES ($1, $2, $3, $4)
            """, character_id, 'response_length', response_length, 100)
            
            print(f"  ✅ response_length: {response_length[:80]}...")
            total_imported += 1
        
        # From behavioral_patterns.decision_making (dict with 3 keys)
        if 'behavioral_patterns' in ryan and 'decision_making' in ryan['behavioral_patterns']:
            dm = ryan['behavioral_patterns']['decision_making']
            
            for key, value in dm.items():
                await conn.execute("""
                    INSERT INTO character_response_guidelines 
                    (character_id, guideline_type, guideline_content, priority)
                    VALUES ($1, $2, $3, $4)
                """, character_id, f'decision_making_{key}', str(value), 80)
                
                print(f"  ✅ decision_making_{key}: {str(value)[:60]}...")
                total_imported += 1
        
        # 6. CONVERSATION FLOWS from communication.conversation_flow_guidance
        print("\n💬 Importing CONVERSATION FLOWS...")
        if 'communication' in ryan and 'conversation_flow_guidance' in ryan['communication']:
            cfg = ryan['communication']['conversation_flow_guidance']
            
            # conversation_flow_guidance has 4 keys: technical_discussion, creative_collaboration, general, response_style
            for flow_type, flow_content in cfg.items():
                await conn.execute("""
                    INSERT INTO character_conversation_flows 
                    (character_id, flow_type, flow_name, approach_description, context)
                    VALUES ($1, $2, $3, $4, $5)
                """, character_id, flow_type, flow_type.replace('_', ' ').title(), str(flow_content), f"Ryan's {flow_type.replace('_', ' ')} guidance")
                
                print(f"  ✅ {flow_type}: {str(flow_content)[:60]}...")
                total_imported += 1
        
        print(f"\n{'='*70}")
        print("✨ IMPORT COMPLETE")
        print(f"{'='*70}")
        print(f"📊 Total new records imported: {total_imported}")
        
        # Verify final counts (Ryan has fewer tables than Marcus/Jake/Gabriel)
        print("\n📈 FINAL RECORD COUNTS:")
        
        tables = [
            'character_response_guidelines',
            'character_cultural_expressions',
            'character_emotional_triggers',
            'character_voice_traits',
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
    asyncio.run(import_ryan_extended())
