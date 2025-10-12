#!/usr/bin/env python3
"""
Smart Migration Script for Jake's Rich Character Data
Intelligently maps legacy JSON to relational database schema based on content analysis
Focus: Adventure photography, outdoor expertise, and Lakota heritage
"""

import asyncio
import asyncpg
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

async def migrate_jake_data():
    """Migrate Jake's rich character data from legacy JSON to relational database"""
    
    print("🏔️ Starting Jake Sterling Character Data Migration")
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
    
    # Load Jake's legacy JSON
    json_path = Path('/Users/markcastillo/git/whisperengine/characters/examples_legacy_backup/jake.json')
    if not json_path.exists():
        print(f"❌ Legacy JSON not found: {json_path}")
        await pool.close()
        return False
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    character_data = data.get('character', {})
    print(f"✅ Loaded legacy JSON for Jake Sterling")
    
    # Get Jake's character ID  
    async with pool.acquire() as conn:
        jake_row = await conn.fetchrow(
            "SELECT id FROM characters WHERE LOWER(normalized_name) IN ('jake', 'jake_sterling')"
        )
        
        if not jake_row:
            print("❌ Jake not found in database!")
            await pool.close()
            return False
        
        character_id = jake_row['id']
        print(f"✅ Found Jake in database (ID: {character_id})")
        
        # Clear existing rich data for clean migration
        print("\n🧹 Cleaning existing rich data...")
        await conn.execute("DELETE FROM character_relationships WHERE character_id = $1", character_id)
        await conn.execute("DELETE FROM character_behavioral_triggers WHERE character_id = $1", character_id)
        await conn.execute("DELETE FROM character_conversation_flows WHERE character_id = $1", character_id)
        await conn.execute("DELETE FROM character_speech_patterns WHERE character_id = $1", character_id)
        print("✅ Cleaned existing data")
        
        # ==================================================================================
        # RELATIONSHIP DATA - Jake's structure: relationships.relationship_style + romantic_preferences
        # ==================================================================================
        print("\n💕 Migrating Relationship Data...")
        relationships = character_data.get('relationships', {})
        relationship_count = 0
        
        # General relationship style
        relationship_style = relationships.get('relationship_style', '')
        if relationship_style:
            await conn.execute("""
                INSERT INTO character_relationships 
                (character_id, related_entity, relationship_type, relationship_strength, 
                 description, communication_style, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                character_id,
                'General Others',  # related_entity
                'genuine_protective',  # relationship_type
                7,  # relationship_strength (warm but guarded)
                relationship_style,  # description
                'Thoughtful and measured, uses nature metaphors',  # communication_style from voice section
                'active'  # status
            )
            relationship_count += 1
            print(f"  ✅ Added general relationship approach: '{relationship_style[:60]}...'")
        
        # Romantic preferences (attracted_to)
        romantic_prefs = relationships.get('romantic_preferences', {})
        attracted_to = romantic_prefs.get('attracted_to', [])
        if attracted_to:
            description = "Attracted to: " + ", ".join(attracted_to)
            await conn.execute("""
                INSERT INTO character_relationships 
                (character_id, related_entity, relationship_type, relationship_strength, 
                 description, communication_style, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                character_id,
                'Romantic Interests',  # related_entity
                'romantic_attraction',  # relationship_type
                9,  # relationship_strength (clear preferences)
                description,  # description
                'Slow to open up but deeply committed when he does',  # communication_style
                'active'  # status
            )
            relationship_count += 1
            print(f"  ✅ Added romantic preferences ({len(attracted_to)} traits)")
        
        print(f"✅ Migrated {relationship_count} relationship entries")
        
        # ==================================================================================
        # BEHAVIORAL TRIGGERS - Jake's structure: communication.message_pattern_triggers
        # ==================================================================================
        print("\n⚡ Migrating Behavioral Triggers...")
        communication = character_data.get('communication', {})
        trigger_count = 0
        
        # Message pattern triggers (topic-based responses)
        message_pattern_triggers = communication.get('message_pattern_triggers', {})
        for trigger_topic, trigger_data in message_pattern_triggers.items():
            keywords = trigger_data.get('keywords', [])
            phrases = trigger_data.get('phrases', [])
            
            # Determine intensity based on topic
            if 'adventure' in trigger_topic or 'photography' in trigger_topic:
                intensity_level = 10  # Maximum - core expertise
                response_type = 'expertise_enthusiasm'
            elif 'survival' in trigger_topic or 'instruction' in trigger_topic:
                intensity_level = 9  # Very high - professional skill
                response_type = 'protective_teaching'
            elif 'personal' in trigger_topic or 'connection' in trigger_topic:
                intensity_level = 8  # High - emotional depth
                response_type = 'authentic_vulnerable'
            elif 'cultural' in trigger_topic or 'heritage' in trigger_topic:
                intensity_level = 9  # Very high - identity
                response_type = 'cultural_pride'
            else:
                intensity_level = 7  # Standard engagement
                response_type = 'thoughtful_response'
            
            # Combine keywords and phrases for trigger description
            combined_keywords = ', '.join(keywords[:10]) if keywords else ''  # Limit to first 10
            combined_phrases = ' | '.join(phrases[:5]) if phrases else ''  # Limit to first 5
            
            trigger_value_parts = []
            if combined_keywords:
                trigger_value_parts.append(f"Keywords: {combined_keywords}")
            if combined_phrases:
                trigger_value_parts.append(f"Phrases: {combined_phrases}")
            
            trigger_value = ' | '.join(trigger_value_parts) if trigger_value_parts else trigger_topic
            
            await conn.execute("""
                INSERT INTO character_behavioral_triggers 
                (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'topic',
                trigger_topic,  # trigger_value (simplified topic name)
                response_type,
                trigger_value,  # response_description (detailed keywords/phrases)
                intensity_level
            )
            trigger_count += 1
            print(f"  ✅ Added trigger: {trigger_topic} (intensity {intensity_level})")
        
        # Typical responses from communication section
        typical_responses = communication.get('typical_responses', {})
        for response_type_key, response_behaviors in typical_responses.items():
            if isinstance(response_behaviors, list):
                for behavior in response_behaviors:
                    await conn.execute("""
                        INSERT INTO character_behavioral_triggers 
                        (character_id, trigger_type, trigger_value, response_type, response_description, intensity_level)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                        character_id,
                        'situational',
                        response_type_key,
                        'behavioral_guideline',
                        behavior,
                        8  # High priority guidelines
                    )
                    trigger_count += 1
                print(f"  ✅ Added {len(response_behaviors)} {response_type_key} responses")
        
        print(f"✅ Migrated {trigger_count} behavioral trigger entries")
        
        # ==================================================================================
        # SPEECH PATTERNS - Jake's structure: identity.voice.catchphrases + speech_patterns
        # ==================================================================================
        print("\n💬 Migrating Speech Patterns...")
        speech_patterns = character_data.get('speech_patterns', {})
        identity = character_data.get('identity', {})
        voice = identity.get('voice', {})
        pattern_count = 0
        
        # Vocabulary (Jake's is empty, but checking anyway)
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
            pattern_count += 1
        if preferred_words:
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
                90
            )
            pattern_count += 1
        if avoided_words:
            print(f"  ✅ Added {len(avoided_words)} avoided words")
        
        # Catchphrases from voice section (signature expressions)
        catchphrases = voice.get('catchphrases', [])
        for phrase in catchphrases:
            await conn.execute("""
                INSERT INTO character_speech_patterns 
                (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'signature_expression',
                phrase,
                'medium',
                'characteristic',
                85  # High priority - defines Jake's voice
            )
            pattern_count += 1
        if catchphrases:
            print(f"  ✅ Added {len(catchphrases)} catchphrases as signature expressions")
        
        # Speech patterns from voice section
        voice_speech_patterns = voice.get('speech_patterns', [])
        for pattern in voice_speech_patterns:
            await conn.execute("""
                INSERT INTO character_speech_patterns 
                (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'speech_behavior',
                pattern,
                'high',
                'all',
                80  # High priority patterns
            )
            pattern_count += 1
        if voice_speech_patterns:
            print(f"  ✅ Added {len(voice_speech_patterns)} voice speech patterns")
        
        # Sentence structure from speech_patterns
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
                95  # Critical core style
            )
            pattern_count += 1
            print("  ✅ Added sentence structure pattern")
        
        # Response length from communication
        response_length = communication.get('response_length', '')
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
                85  # Very high - affects all responses
            )
            pattern_count += 1
            print("  ✅ Added response length guideline")
        
        # Voice tone/pace/volume
        tone = voice.get('tone', '')
        pace = voice.get('pace', '')
        volume = voice.get('volume', '')
        
        if tone:
            await conn.execute("""
                INSERT INTO character_speech_patterns 
                (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                character_id,
                'voice_tone',
                tone,
                'always',
                'all',
                90
            )
            pattern_count += 1
            print(f"  ✅ Added voice tone: '{tone}'")
        
        print(f"✅ Migrated {pattern_count} speech pattern entries")
        
        # ==================================================================================
        # CONVERSATION FLOWS - Adventure storytelling and teaching modes
        # ==================================================================================
        print("\n🗣️ Migrating Conversation Flows...")
        communication = character_data.get('communication', {})
        conversation_flow_guidance = communication.get('conversation_flow_guidance', {})
        flow_count = 0
        
        # Process each conversation flow type
        for flow_type, flow_data in conversation_flow_guidance.items():
            if isinstance(flow_data, dict):
                energy = flow_data.get('energy', 'balanced')
                approach = flow_data.get('approach', '')
                avoid = flow_data.get('avoid', [])
                encourage = flow_data.get('encourage', [])
                transition_style = flow_data.get('transition_style', '')
                
                # Determine priority based on flow type
                if 'adventure' in flow_type.lower() or 'outdoor' in flow_type.lower():
                    priority = 90  # Highest for core expertise
                elif 'teaching' in flow_type.lower() or 'survival' in flow_type.lower():
                    priority = 85  # Very high for educational moments
                elif 'cultural' in flow_type.lower() or 'heritage' in flow_type.lower():
                    priority = 80  # High for identity
                else:
                    priority = 70  # Standard priority
                
                # Combine avoid/encourage into context
                context_parts = []
                if avoid:
                    context_parts.append(f"AVOID: {', '.join(avoid)}")
                if encourage:
                    context_parts.append(f"ENCOURAGE: {', '.join(encourage)}")
                context = ' | '.join(context_parts) if context_parts else None
                
                await conn.execute("""
                    INSERT INTO character_conversation_flows 
                    (character_id, flow_type, flow_name, energy_level, approach_description, 
                     transition_style, priority, context)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    character_id,
                    flow_type,  # flow_type
                    flow_type.replace('_', ' ').title(),  # flow_name
                    energy,  # energy_level
                    approach,  # approach_description
                    transition_style or 'Natural flow with outdoor metaphors',  # transition_style
                    priority,  # priority
                    context  # context
                )
                flow_count += 1
                print(f"  ✅ Added conversation flow: {flow_type}")
        
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
        print("\n🏔️ Key Jake Identity Elements Preserved:")
        print("   • Adventure photography expertise")
        print("   • Outdoor survival and wilderness skills")
        print("   • Lakota heritage and cultural connection to nature")
        print("   • Protective instincts and teaching moments")
        print("   • Straightforward communication with outdoor metaphors")
        
    await pool.close()
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(migrate_jake_data())
        if success:
            print("\n🚀 Ready to test Jake with enhanced CDL manager!")
            print("   Next: Restart Jake bot and test with outdoor/adventure topics")
            sys.exit(0)
        else:
            print("\n❌ Migration failed - check errors above")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
