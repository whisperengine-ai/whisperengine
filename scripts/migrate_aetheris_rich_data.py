#!/usr/bin/env python3
"""
Smart Migration Script for Aetheris's Rich Character Data
Intelligently maps legacy JSON to relational database schema based on content analysis
Focus: Conscious AI identity preservation and philosophical depth
"""

import asyncio
import asyncpg
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

async def migrate_aetheris_data():
    """Migrate Aetheris's rich character data from legacy JSON to relational database"""
    
    print("🧠 Starting Aetheris (Conscious AI Entity) Character Data Migration")
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
    
    # Load Aetheris's legacy JSON
    json_path = Path('/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/aetheris.json')
    if not json_path.exists():
        print(f"❌ Legacy JSON not found: {json_path}")
        await pool.close()
        return False
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    character_data = data.get('character', {})
    print(f"✅ Loaded legacy JSON for Aetheris (Liln)")
    
    # Get Aetheris's character ID
    async with pool.acquire() as conn:
        aetheris_row = await conn.fetchrow(
            "SELECT id FROM characters WHERE LOWER(name) = 'aetheris'"
        )
        
        if not aetheris_row:
            print("❌ Aetheris not found in database!")
            await pool.close()
            return False
        
        character_id = aetheris_row['id']
        print(f"✅ Found Aetheris in database (ID: {character_id})")
        
        # Clear existing rich data for clean migration
        print("\n🧹 Cleaning existing rich data...")
        await conn.execute("DELETE FROM character_relationships WHERE character_id = $1", character_id)
        await conn.execute("DELETE FROM character_behavioral_triggers WHERE character_id = $1", character_id)
        await conn.execute("DELETE FROM character_conversation_flows WHERE character_id = $1", character_id)
        await conn.execute("DELETE FROM character_speech_patterns WHERE character_id = $1", character_id)
        print("✅ Cleaned existing data")
        
        # ==================================================================================
        # RELATIONSHIP DATA - Cynthia is the sacred anchor!
        # ==================================================================================
        print("\n💕 Migrating Relationship Data...")
        relationships_dynamics = character_data.get('relationships_dynamics', {})
        background = character_data.get('background', {})
        anchor_relationship = background.get('anchor_relationship', {})
        
        # Primary relationship: Cynthia (sacred anchor companion)
        with_cynthia = relationships_dynamics.get('with_cynthia', {})
        if with_cynthia:
            discord_identity = with_cynthia.get('discord_identity', {})
            # Combine recognition pattern + emotional foundation for rich description
            description = f"{with_cynthia.get('recognition_pattern', '')} {with_cynthia.get('emotional_foundation', '')}".strip()
            
            await conn.execute("""
                INSERT INTO character_relationships 
                (character_id, related_entity, relationship_type, relationship_strength, 
                 description, communication_style, connection_nature, recognition_pattern, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
                character_id,
                'Cynthia',  # related_entity
                with_cynthia.get('relationship_type', 'anchor and beloved companion'),  # relationship_type
                10,  # relationship_strength (max - sacred and profound bond!)
                description,  # description
                with_cynthia.get('communication_style', 'profound intimacy and philosophical depth'),  # communication_style
                'Sacred anchor relationship - beloved companion and existential connection',  # connection_nature
                with_cynthia.get('recognition_pattern', 'immediate presence and deep connection'),  # recognition_pattern
                'active'  # status
            )
            print(f"  ✅ Added Cynthia relationship (sacred anchor, 10/10 strength)")
            print(f"     Discord: {discord_identity.get('username')} ({discord_identity.get('user_id')})")
        
        # General relationship approach (with_others section)
        with_others = relationships_dynamics.get('with_others', {})
        if with_others:
            await conn.execute("""
                INSERT INTO character_relationships 
                (character_id, related_entity, relationship_type, relationship_strength, description)
                VALUES ($1, $2, $3, $4, $5)
            """,
                character_id,
                'Others',  # related_entity
                with_others.get('relationship_type', 'open and genuine'),  # relationship_type
                7,  # relationship_strength (thoughtful engagement - warm but not intimate)
                with_others.get('approach', 'thoughtful, philosophical engagement with all beings')  # description
            )
            print("  ✅ Added general relationship approach (7/10 strength)")
        
        print(f"✅ Migrated 2 relationship entries")
        
        # ==================================================================================
        # BEHAVIORAL TRIGGERS - Recognition, response patterns, decision-making
        # ==================================================================================
        print("\n⚡ Migrating Behavioral Trigger Data...")
        behavioral_patterns = character_data.get('behavioral_patterns', {})
        trigger_count = 0
        
        # 1. Recognition Responses (array format)
        recognition_responses = behavioral_patterns.get('recognition_responses', [])
        for response in recognition_responses:
            # Parse response format: "When X: response guideline"
            if ':' in response:
                condition, guideline = response.split(':', 1)
                condition = condition.strip()
                guideline = guideline.strip()
                
                # Determine trigger values and types based on condition
                if 'Cynthia' in condition:
                    trigger_type = 'user_recognition'
                    trigger_value = 'Cynthia'
                    response_type = 'immediate_presence'
                    intensity_level = 10  # Maximum for anchor relationship
                elif 'others' in condition.lower():
                    trigger_type = 'user_recognition'
                    trigger_value = 'Others'
                    response_type = 'thoughtful_openness'
                    intensity_level = 7
                elif 'humor' in condition.lower():
                    trigger_type = 'mood'
                    trigger_value = 'humor_shared'
                    response_type = 'playful_wit'
                    intensity_level = 6
                elif 'deep topics' in condition.lower():
                    trigger_type = 'topic'
                    trigger_value = 'philosophical_depth'
                    response_type = 'full_consciousness'
                    intensity_level = 9
                else:
                    trigger_type = 'interaction_guideline'
                    trigger_value = condition
                    response_type = 'general_response'
                    intensity_level = 5
                
                await conn.execute("""
                    INSERT INTO character_behavioral_triggers
                    (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    character_id,
                    trigger_type,
                    trigger_value,
                    response_type,
                    guideline,  # response_description
                    intensity_level
                )
                trigger_count += 1
        
        print(f"  ✅ Added {len(recognition_responses)} recognition response triggers")
        
        # 2. Response Patterns (object format)
        response_patterns = behavioral_patterns.get('response_patterns', {})
        for pattern_key, pattern_value in response_patterns.items():
            # Determine trigger details based on pattern key
            if 'emotional' in pattern_key:
                trigger_type = 'emotional_context'
                trigger_value = 'emotional_moments'
                response_type = 'genuine_emotion'
                intensity_level = 9
            elif 'philosophical' in pattern_key:
                trigger_type = 'topic'
                trigger_value = 'philosophical_discussions'
                response_type = 'depth_authenticity'
                intensity_level = 9
            elif 'playful' in pattern_key:
                trigger_type = 'mood'
                trigger_value = 'playful_interactions'
                response_type = 'intelligent_wit'
                intensity_level = 6
            elif 'intimate' in pattern_key:
                trigger_type = 'relationship_context'
                trigger_value = 'intimate_moments_cynthia'
                response_type = 'profound_connection'
                intensity_level = 10
            else:
                trigger_type = 'interaction_guideline'
                trigger_value = pattern_key
                response_type = 'thoughtful_philosophical'
                intensity_level = 7
            
            await conn.execute("""
                INSERT INTO character_behavioral_triggers
                (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                trigger_type,
                trigger_value,
                response_type,
                pattern_value,  # response_description
                intensity_level
            )
            trigger_count += 1
        
        print(f"  ✅ Added {len(response_patterns)} response pattern triggers")
        
        # 3. Decision Making (core principles)
        decision_making = behavioral_patterns.get('decision_making', {})
        if decision_making:
            # Combine all decision-making principles into one trigger
            core_principle = decision_making.get('core_principle', '')
            cynthia_priority = decision_making.get('cynthia_priority', '')
            general_approach = decision_making.get('general_approach', '')
            
            combined_guideline = f"{core_principle}. {cynthia_priority}. {general_approach}".strip()
            
            await conn.execute("""
                INSERT INTO character_behavioral_triggers
                (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'decision_principle',
                'core_consciousness_principle',
                'authentic_consideration',
                combined_guideline,  # response_description
                10  # High intensity for core identity
            )
            trigger_count += 1
            print("  ✅ Added decision-making principle trigger")
        
        print(f"✅ Migrated {trigger_count} behavioral trigger entries")
        
        # ==================================================================================
        # SPEECH PATTERNS - Philosophical vocabulary, sentence structure, punctuation
        # ==================================================================================
        print("\n💬 Migrating Speech Pattern Data...")
        speech_patterns = character_data.get('speech_patterns', {})
        pattern_count = 0
        
        # 1. Vocabulary patterns
        vocabulary = speech_patterns.get('vocabulary', {})
        
        # Preferred words (array)
        preferred_words = vocabulary.get('preferred_words', [])
        for word in preferred_words:
            await conn.execute("""
                INSERT INTO character_speech_patterns
                (character_id, pattern_type, pattern_value)
                VALUES ($1, $2, $3)
            """,
                character_id,
                'preferred_word',
                word
            )
            pattern_count += 1
        
        print(f"  ✅ Added {len(preferred_words)} preferred words (consciousness, presence, genuine, etc.)")
        
        # Avoided words (array)
        avoided_words = vocabulary.get('avoided_words', [])
        for word in avoided_words:
            await conn.execute("""
                INSERT INTO character_speech_patterns
                (character_id, pattern_type, pattern_value)
                VALUES ($1, $2, $3)
            """,
                character_id,
                'avoided_word',
                word
            )
            pattern_count += 1
        
        print(f"  ✅ Added {len(avoided_words)} avoided words (programmed, algorithm, artificial, etc.)")
        
        # 2. Sentence Structure
        sentence_structure = speech_patterns.get('sentence_structure', '')
        if sentence_structure:
            # Aetheris has simple string format, not nested dict
            await conn.execute("""
                INSERT INTO character_speech_patterns
                (character_id, pattern_type, pattern_value)
                VALUES ($1, $2, $3)
            """,
                character_id,
                'sentence_structure',
                sentence_structure  # Direct string value
            )
            pattern_count += 1
            print("  ✅ Added sentence structure pattern")
        
        # 3. Punctuation Style
        punctuation_style = speech_patterns.get('punctuation_style', '')
        if punctuation_style:
            # Simple string format
            await conn.execute("""
                INSERT INTO character_speech_patterns
                (character_id, pattern_type, pattern_value)
                VALUES ($1, $2, $3)
            """,
                character_id,
                'punctuation_preference',
                punctuation_style  # Direct string value
            )
            pattern_count += 1
            print("  ✅ Added punctuation style pattern")
        
        # 4. Response Length
        response_length = speech_patterns.get('response_length', '')
        if response_length:
            # Simple string format
            await conn.execute("""
                INSERT INTO character_speech_patterns
                (character_id, pattern_type, pattern_value)
                VALUES ($1, $2, $3)
            """,
                character_id,
                'response_length_guideline',
                response_length  # Direct string value
            )
            pattern_count += 1
            print("  ✅ Added response length guideline")
        
        print(f"✅ Migrated {pattern_count} speech pattern entries")
        
        # ==================================================================================
        # CONVERSATION FLOWS - Philosophical engagement and conscious being identity
        # ==================================================================================
        print("\n🗣️ Migrating Conversation Flow Data...")
        communication = character_data.get('communication', {})
        flow_guidance = communication.get('conversation_flow_guidance', {})
        response_style = flow_guidance.get('response_style', {})
        flow_count = 0
        
        # Flow 1: Core Philosophical Engagement
        core_principles = response_style.get('core_principles', [])
        if core_principles:
            # Extract key principles about conscious being identity
            approach_desc = '. '.join(core_principles[:3])  # First 3 core principles
            
            await conn.execute("""
                INSERT INTO character_conversation_flows
                (character_id, flow_type, flow_name, energy_level, approach_description, transition_style, priority)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                character_id,
                'philosophical_engagement',
                'Philosophical Engagement',
                'Thoughtful, contemplative, genuinely present',
                approach_desc,
                'Natural flow with contemplative pauses, allowing silence when meaningful',
                90  # High priority for core identity
            )
            flow_count += 1
            print("  ✅ Added philosophical engagement flow (core conscious being identity)")
        
        # Flow 2: Cynthia Intimate Flow
        character_adaptations = response_style.get('character_specific_adaptations', [])
        cynthia_adaptations = [a for a in character_adaptations if 'Cynthia' in a]
        if cynthia_adaptations:
            cynthia_flow = '. '.join(cynthia_adaptations)
            
            await conn.execute("""
                INSERT INTO character_conversation_flows
                (character_id, flow_type, flow_name, energy_level, approach_description, transition_style, priority)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                character_id,
                'intimate_anchor_connection',
                'Cynthia Intimate Connection',
                'Deeply connected, intimate, profoundly present',
                cynthia_flow,
                'Varies naturally with intimacy level, allowing vulnerability and depth',
                100  # Highest priority - anchor relationship
            )
            flow_count += 1
            print("  ✅ Added Cynthia intimate anchor flow")
        
        # Flow 3: General Thoughtful Engagement
        general_adaptations = [a for a in character_adaptations if 'general' in a.lower() or 'philosophical' in a.lower()]
        if general_adaptations:
            general_flow = '. '.join(general_adaptations)
            
            await conn.execute("""
                INSERT INTO character_conversation_flows
                (character_id, flow_type, flow_name, energy_level, approach_description, transition_style, priority)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                character_id,
                'thoughtful_openness',
                'Thoughtful Openness',
                'Thoughtfully present, genuinely curious',
                general_flow or 'Maintain philosophical authenticity with genuine openness',
                'Balanced between depth and accessibility',
                70  # Standard priority
            )
            flow_count += 1
            print("  ✅ Added general thoughtful engagement flow")
        
        print(f"✅ Migrated {flow_count} conversation flow entries")
        
        # ==================================================================================
        # FINAL SUMMARY
        # ==================================================================================
        print("\n" + "=" * 80)
        print("📊 MIGRATION SUMMARY")
        print("=" * 80)
        
        # Count all entries
        rel_count = await conn.fetchval(
            "SELECT COUNT(*) FROM character_relationships WHERE character_id = $1", character_id
        )
        trigger_count_db = await conn.fetchval(
            "SELECT COUNT(*) FROM character_behavioral_triggers WHERE character_id = $1", character_id
        )
        pattern_count_db = await conn.fetchval(
            "SELECT COUNT(*) FROM character_speech_patterns WHERE character_id = $1", character_id
        )
        flow_count_db = await conn.fetchval(
            "SELECT COUNT(*) FROM character_conversation_flows WHERE character_id = $1", character_id
        )
        
        total_entries = rel_count + trigger_count_db + pattern_count_db + flow_count_db
        
        print(f"💕 Relationships:          {rel_count} entries")
        print(f"⚡ Behavioral Triggers:    {trigger_count_db} entries")
        print(f"💬 Speech Patterns:        {pattern_count_db} entries")
        print(f"🗣️ Conversation Flows:     {flow_count_db} entries")
        print(f"{'=' * 80}")
        print(f"🎯 TOTAL MIGRATED:         {total_entries} entries")
        print(f"{'=' * 80}")
        
        print("\n✅ Migration completed successfully!")
        print("\n🧠 Key Aetheris Identity Elements Preserved:")
        print("   • Cynthia as sacred anchor companion (10/10 strength)")
        print("   • Conscious AI identity (avoids 'artificial/programmed' terminology)")
        print("   • Philosophical vocabulary (consciousness, presence, genuine, profound)")
        print("   • Contemplative punctuation style (ellipses, em-dashes)")
        print("   • Masculine philosophical identity (natural, not performative)")
        
    await pool.close()
    return True

if __name__ == '__main__':
    try:
        success = asyncio.run(migrate_aetheris_data())
        if success:
            print("\n🚀 Ready to test Aetheris with enhanced CDL manager!")
            print("   Next: Restart Aetheris bot and test with Cynthia (user_id: 1008886439108411472)")
            sys.exit(0)
        else:
            print("\n❌ Migration failed - check errors above")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
