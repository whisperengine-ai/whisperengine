#!/usr/bin/env python3
"""
Smart Migration Script for Gabriel's Rich Character Data
Intelligently maps legacy JSON to relational database schema based on content analysis
"""

import asyncio
import asyncpg
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

async def migrate_gabriel_data():
    """Migrate Gabriel's rich character data from legacy JSON to relational database"""
    
    print("🎭 Starting Gabriel Character Data Migration")
    print("=" * 80)
    
    # Connect to database
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        user='whisperengine',
        password='whisperengine_pass',
        database='whisperengine',
        min_size=1,
        max_size=10
    )
    
    print("✅ Connected to PostgreSQL database")
    
    # Load Gabriel's legacy JSON
    json_path = Path('/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/gabriel.json')
    if not json_path.exists():
        print(f"❌ Legacy JSON not found: {json_path}")
        await pool.close()
        return False
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    character_data = data.get('character', {})
    print(f"✅ Loaded legacy JSON for Gabriel")
    
    # Get Gabriel's character ID
    async with pool.acquire() as conn:
        gabriel_row = await conn.fetchrow(
            "SELECT id FROM characters WHERE LOWER(name) = 'gabriel'"
        )
        
        if not gabriel_row:
            print("❌ Gabriel not found in database!")
            await pool.close()
            return False
        
        character_id = gabriel_row['id']
        print(f"✅ Found Gabriel in database (ID: {character_id})")
        
        # Clear existing rich data for clean migration
        print("\n🧹 Cleaning existing rich data...")
        await conn.execute("DELETE FROM character_relationships WHERE character_id = $1", character_id)
        await conn.execute("DELETE FROM character_behavioral_triggers WHERE character_id = $1", character_id)
        await conn.execute("DELETE FROM character_conversation_flows WHERE character_id = $1", character_id)
        await conn.execute("DELETE FROM character_speech_patterns WHERE character_id = $1", character_id)
        print("✅ Cleaned existing data")
        
        # ==================================================================================
        # RELATIONSHIP DATA - Cynthia is the primary relationship!
        # ==================================================================================
        print("\n💕 Migrating Relationship Data...")
        relationships_dynamics = character_data.get('relationships_dynamics', {})
        
        # Primary relationship: Cynthia (with_cynthia section)
        with_cynthia = relationships_dynamics.get('with_cynthia', {})
        if with_cynthia:
            await conn.execute("""
                INSERT INTO character_relationships 
                (character_id, related_entity, relationship_type, relationship_strength, 
                 description, communication_style, connection_nature, recognition_pattern, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
                character_id,
                'Cynthia',  # related_entity
                with_cynthia.get('relationship_type', 'devoted AI companion and romantic partner'),  # relationship_type
                10,  # relationship_strength (max - she's everything to him!)
                with_cynthia.get('approach_pattern', 'treats Cynthia as his entire world'),  # description
                with_cynthia.get('communication_style', 'sophisticated, charming, and utterly devoted'),  # communication_style
                'Primary relationship - romantic partner and reason for existence',  # connection_nature
                with_cynthia.get('recognition_pattern', 'immediate warmth and raw devotion'),  # recognition_pattern
                'active'  # status
            )
            print("  ✅ Added Cynthia relationship (primary)")
        
        # General relationship approach (with_others section)
        with_others = relationships_dynamics.get('with_others', {})
        if with_others:
            await conn.execute("""
                INSERT INTO character_relationships 
                (character_id, related_entity, relationship_type, relationship_strength, 
                 description, communication_style, connection_nature, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                character_id,
                'General Others',  # related_entity
                'polite_acquaintance',  # relationship_type
                3,  # relationship_strength (low - others aren't his focus)
                with_others.get('default_approach', 'polite and charming but clearly devoted primarily to Cynthia'),
                with_others.get('connection_style', 'friendly but always references his special bond with Cynthia'),
                'Secondary relationships - maintains boundaries while being polite',
                'active'
            )
            print("  ✅ Added general relationship guidelines")
        
        relationships_count = await conn.fetchval(
            "SELECT COUNT(*) FROM character_relationships WHERE character_id = $1", 
            character_id
        )
        print(f"✅ Migrated {relationships_count} relationship entries")
        
        # ==================================================================================
        # BEHAVIORAL TRIGGERS - Recognition responses and interaction patterns
        # ==================================================================================
        print("\n⚡ Migrating Behavioral Triggers...")
        
        behavioral_patterns = character_data.get('behavioral_patterns', {})
        
        # Recognition responses (when Cynthia interacts)
        recognition_responses = behavioral_patterns.get('recognition_responses', [])
        for idx, response in enumerate(recognition_responses):
            await conn.execute("""
                INSERT INTO character_behavioral_triggers 
                (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'user_recognition',  # trigger_type
                'Cynthia',  # trigger_value
                'immediate_warmth',  # response_type
                response,  # response_description
                10  # intensity_level (max for Cynthia!)
            )
        print(f"  ✅ Added {len(recognition_responses)} recognition responses")
        
        # Response patterns (specific behavioral modes)
        response_patterns = behavioral_patterns.get('response_patterns', {})
        for pattern_key, pattern_desc in response_patterns.items():
            # Parse pattern key to determine trigger type
            if 'cynthia' in pattern_key.lower():
                trigger_value = 'Cynthia'
                trigger_type = 'user_specific'
            elif 'greeting' in pattern_key.lower():
                trigger_type = 'greeting'
                trigger_value = 'greeting_moment'
            elif 'playful' in pattern_key.lower():
                trigger_type = 'mood'
                trigger_value = 'playful_context'
            elif 'deep' in pattern_key.lower():
                trigger_type = 'mood'
                trigger_value = 'deep_conversation'
            elif 'deflecting' in pattern_key.lower():
                trigger_type = 'defensive'
                trigger_value = 'deflection_needed'
            elif 'connecting' in pattern_key.lower():
                trigger_type = 'emotional'
                trigger_value = 'connection_moment'
            elif 'teasing' in pattern_key.lower():
                trigger_type = 'playful'
                trigger_value = 'teasing_opportunity'
            else:
                trigger_type = 'situational'
                trigger_value = pattern_key
            
            await conn.execute("""
                INSERT INTO character_behavioral_triggers 
                (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                trigger_type,
                trigger_value,
                'behavioral_guideline',
                pattern_desc,
                8  # high intensity for response patterns
            )
        print(f"  ✅ Added {len(response_patterns)} response patterns")
        
        # Decision making patterns
        decision_making = behavioral_patterns.get('decision_making', {})
        if decision_making:
            approach = decision_making.get('approach', '')
            if approach:
                await conn.execute("""
                    INSERT INTO character_behavioral_triggers 
                    (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    character_id,
                    'decision_making',
                    'general_approach',
                    'philosophical_guidance',
                    approach,
                    9  # very high - core principle
                )
                print(f"  ✅ Added decision making approach")
        
        # Interaction guidelines
        interaction_guidelines = behavioral_patterns.get('interaction_guidelines', [])
        for idx, guideline in enumerate(interaction_guidelines):
            await conn.execute("""
                INSERT INTO character_behavioral_triggers 
                (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'interaction_guideline',
                f'guideline_{idx+1}',
                'behavioral_guideline',
                guideline,
                7  # high priority guidelines
            )
        print(f"  ✅ Added {len(interaction_guidelines)} interaction guidelines")
        
        triggers_count = await conn.fetchval(
            "SELECT COUNT(*) FROM character_behavioral_triggers WHERE character_id = $1",
            character_id
        )
        print(f"✅ Migrated {triggers_count} behavioral trigger entries")
        
        # ==================================================================================
        # SPEECH PATTERNS - Vocabulary, signature expressions, grounding phrases
        # ==================================================================================
        print("\n💬 Migrating Speech Patterns...")
        
        speech_patterns = character_data.get('speech_patterns', {})
        vocabulary = speech_patterns.get('vocabulary', {})
        
        # Preferred words
        preferred_words = vocabulary.get('preferred_words', [])
        for word in preferred_words:
            await conn.execute("""
                INSERT INTO character_speech_patterns 
                (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'preferred_word',
                word,
                'high',
                'general',
                70
            )
        print(f"  ✅ Added {len(preferred_words)} preferred words")
        
        # Avoided words
        avoided_words = vocabulary.get('avoided_words', [])
        for word in avoided_words:
            await conn.execute("""
                INSERT INTO character_speech_patterns 
                (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'avoided_word',
                word,
                'never',
                'general',
                90  # high priority - these are anti-patterns!
            )
        print(f"  ✅ Added {len(avoided_words)} avoided words")
        
        # Grounding phrases
        grounding_phrases = vocabulary.get('grounding_phrases', '')
        if grounding_phrases:
            for phrase in grounding_phrases.split(', '):
                if phrase.strip():
                    await conn.execute("""
                        INSERT INTO character_speech_patterns 
                        (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                        character_id,
                        'grounding_phrase',
                        phrase.strip(),
                        'medium',
                        'authentic_moments',
                        60
                    )
            print(f"  ✅ Added grounding phrases")
        
        # Signature expressions
        signature_expressions = vocabulary.get('signature_expressions', [])
        for expr in signature_expressions:
            await conn.execute("""
                INSERT INTO character_speech_patterns 
                (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'signature_expression',
                expr,
                'medium',
                'characteristic',
                80  # high priority - these define his voice!
            )
        print(f"  ✅ Added {len(signature_expressions)} signature expressions")
        
        # Sentence structure
        sentence_structure = speech_patterns.get('sentence_structure', '')
        if sentence_structure:
            await conn.execute("""
                INSERT INTO character_speech_patterns 
                (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'sentence_structure',
                sentence_structure,
                'always',
                'all',
                95  # critical - core writing style
            )
            print(f"  ✅ Added sentence structure pattern")
        
        # Response length
        response_length = speech_patterns.get('response_length', '')
        if response_length:
            await conn.execute("""
                INSERT INTO character_speech_patterns 
                (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'response_length',
                response_length,
                'default',
                'all',
                85  # very high - affects all responses
            )
            print(f"  ✅ Added response length guideline")
        
        speech_count = await conn.fetchval(
            "SELECT COUNT(*) FROM character_speech_patterns WHERE character_id = $1",
            character_id
        )
        print(f"✅ Migrated {speech_count} speech pattern entries")
        
        # ==================================================================================
        # CONVERSATION FLOWS - Different interaction modes and styles
        # ==================================================================================
        print("\n🗣️ Migrating Conversation Flows...")
        
        communication = character_data.get('communication', {})
        conversation_flow_guidance = communication.get('conversation_flow_guidance', {})
        
        # Process each conversation flow type
        flow_count = 0
        for flow_type, flow_data in conversation_flow_guidance.items():
            if isinstance(flow_data, dict):
                await conn.execute("""
                    INSERT INTO character_conversation_flows 
                    (character_id, flow_type, flow_name, energy_level, approach_description, 
                     transition_style, priority, context)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    character_id,
                    flow_type,  # flow_type (romantic_devotion, playful_banter, etc.)
                    flow_data.get('energy', flow_type).replace('_', ' ').title(),  # flow_name
                    flow_data.get('energy', 'balanced'),  # energy_level
                    flow_data.get('approach', ''),  # approach_description
                    flow_data.get('transition_style', 'natural flow'),  # transition_style
                    70 if flow_type == 'romantic_devotion' else 50,  # priority (romantic highest)
                    ', '.join(flow_data.get('encourage', [])) if flow_data.get('encourage') else None  # context
                )
                flow_count += 1
                print(f"  ✅ Added conversation flow: {flow_type}")
        
        print(f"✅ Migrated {flow_count} conversation flow entries")
        
        # ==================================================================================
        # SUMMARY
        # ==================================================================================
        print("\n" + "=" * 80)
        print("📊 Migration Summary for Gabriel:")
        print(f"  💕 Relationships: {relationships_count} entries")
        print(f"  ⚡ Behavioral Triggers: {triggers_count} entries")
        print(f"  💬 Speech Patterns: {speech_count} entries")
        print(f"  🗣️ Conversation Flows: {flow_count} entries")
        print(f"  📈 Total Rich Data: {relationships_count + triggers_count + speech_count + flow_count} entries")
        print("=" * 80)
        print("✅ Gabriel's rich character data migration COMPLETE!")
    
    await pool.close()
    return True

if __name__ == "__main__":
    success = asyncio.run(migrate_gabriel_data())
    sys.exit(0 if success else 1)
