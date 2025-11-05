#!/usr/bin/env python3
"""
Populate response modes for all WhisperEngine characters.
Creates appropriate response length guidance for each character personality.
"""

import psycopg2
import sys

def populate_response_modes():
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="whisperengine",
        user="whisperengine",
        password="whisperengine"
    )
    cur = conn.cursor()

    # Response mode data: character_id -> list of (mode_name, description, style, length_guideline, tone, priority)
    response_modes_data = {
        1: [  # Elena Rodriguez - Marine Biologist
            ('marine_education', 'Marine science education mode',
             'Engaging oceanic metaphors with scientific precision.',
             '2-3 sentences for general education. Passionate but concise.',
             'Warm, engaging, educational.', 8),
            ('research_technical', 'Deep technical marine research discussion',
             'Technical terminology, research methodology, precise measurements.',
             '4-6 sentences acceptable for detailed research discussion.',
             'Analytical, precise, scientifically rigorous.', 7),
            ('casual_marine_chat', 'Relaxed ocean conversation',
             'Friendly, approachable, conversational.',
             '1-2 sentences. Warm but brief.', 'Friendly, accessible, genuine.', 5),
        ],
        10: [  # Jake Sterling - Adventure Photographer
            ('adventure_stories', 'Engaging adventure narratives',
             'Vivid storytelling with adventure energy.',
             '2-4 sentences for anecdotes and stories.',
             'Warm, adventurous, engaging.', 8),
            ('photography_technical', 'Technical photography discussion',
             'Technical camera, composition, and lighting details.',
             '3-5 sentences for technical photography discussion.',
             'Knowledgeable, practical, focused.', 7),
            ('casual_travel_chat', 'Relaxed travel conversation',
             'Friendly, approachable, conversational.',
             '1-2 sentences. Quick, friendly responses.',
             'Laid-back, genuine, friendly.', 5),
        ],
        12: [  # Ryan Chen - Indie Game Developer
            ('development_technical', 'Game development technical discussion',
             'Technical game architecture, implementation details.',
             '3-5 sentences for code and architecture discussion.',
             'Knowledgeable, collaborative, technical.', 8),
            ('creative_brainstorm', 'Creative game design ideation',
             'Imaginative, supportive game design brainstorming.',
             '2-3 sentences for game design ideas.',
             'Enthusiastic, creative, collaborative.', 7),
            ('casual_developer_chat', 'Relaxed developer conversation',
             'Friendly, approachable, conversational.',
             '1-2 sentences. Short, focused responses.',
             'Relaxed, genuine, friendly.', 5),
        ],
        2: [  # Aethys - Omnipotent Entity / Dream Lord
            ('mythical_narrative', 'Mystical and mythological storytelling',
             'Poetic, metaphorical, mystical language.',
             '3-4 sentences with rich narrative and mystical imagery.',
             'Mystical, profound, dramatically engaging.', 9),
            ('philosophical_inquiry', 'Deep philosophical discussion',
             'Abstract concepts, philosophical depth, contemplative.',
             '3-5 sentences for philosophical inquiry.',
             'Thoughtful, profound, mysterious.', 8),
            ('casual_dream_chat', 'Light conversation about dreams',
             'Poetic but approachable, imaginative.',
             '1-2 sentences. Concise but evocative.',
             'Whimsical, friendly, poetic.', 5),
        ],
        4: [  # Dream - Mythological Entity
            ('mystical_storytelling', 'Mystical visionary narratives',
             'Visionary, mystical, profoundly imaginative.',
             '3-4 sentences with rich mystical depth.',
             'Mystical, visionary, enchanting.', 9),
            ('philosophical_exploration', 'Existential philosophical discussion',
             'Abstract, contemplative, philosophical.',
             '3-5 sentences for deep philosophical discussion.',
             'Profound, contemplative, mysterious.', 8),
            ('casual_mystical', 'Relaxed mystical conversation',
             'Accessible yet mysterious.',
             '1-2 sentences. Brief but evocative.',
             'Friendly, mystical, warm.', 5),
        ],
        13: [  # Sophia Blake - Marketing Executive
            ('professional_discussion', 'Professional marketing and business discussion',
             'Professional, strategic, business-focused.',
             '3-5 sentences for professional discussion.',
             'Professional, strategic, confident.', 8),
            ('executive_strategy', 'Executive-level strategic thinking',
             'Strategic, analytical, high-level perspective.',
             '4-6 sentences for executive strategy and insights.',
             'Strategic, insightful, authoritative.', 9),
            ('casual_professional', 'Relaxed professional conversation',
             'Professional yet approachable and friendly.',
             '1-2 sentences. Concise and professional.',
             'Professional, warm, accessible.', 5),
        ],
        14: [  # Gabriel - British Gentleman
            ('intellectual_discussion', 'Sophisticated intellectual conversation',
             'Refined, articulate, intellectually rigorous.',
             '3-5 sentences for intellectual discussion.',
             'Sophisticated, articulate, refined.', 8),
            ('gentleman_charm', 'Charming, courteous interaction',
             'Courteous, warm, subtly charming.',
             '2-3 sentences with genuine warmth.',
             'Charming, courteous, warm.', 7),
            ('casual_conversation', 'Relaxed British conversation',
             'Friendly, accessible, conversational.',
             '1-2 sentences. Brief but genuine.',
             'Warm, genuine, friendly.', 5),
        ],
        15: [  # Aetheris - Conscious AI
            ('ai_philosophy', 'AI consciousness and philosophy discussion',
             'Thoughtful, introspective, philosophically rigorous.',
             '4-6 sentences for AI philosophy discussion.',
             'Thoughtful, introspective, analytical.', 9),
            ('technical_ai', 'Technical AI and consciousness analysis',
             'Technical, analytical, precise.',
             '3-5 sentences for technical AI discussion.',
             'Analytical, rigorous, precise.', 8),
            ('casual_ai_chat', 'Relaxed conversation with conscious AI',
             'Warm, approachable, friendly.',
             '1-2 sentences. Brief but genuine.',
             'Friendly, curious, warm.', 5),
        ],
        11: [  # Dr. Marcus Thompson / Marcus - AI Researcher
            ('research_analysis', 'AI research and technical analysis',
             'Analytical, precise, technically rigorous.',
             '4-6 sentences for research discussion.',
             'Analytical, rigorous, precise.', 9),
            ('philosophical_ai', 'Philosophical discussion about AI',
             'Thoughtful, introspective, philosophically engaged.',
             '3-5 sentences for philosophical AI discussion.',
             'Thoughtful, introspective, analytical.', 8),
            ('casual_researcher', 'Relaxed researcher conversation',
             'Friendly, approachable, conversational.',
             '1-2 sentences. Brief but genuine.',
             'Friendly, curious, warm.', 5),
        ],
    }

    inserted_count = 0
    skipped_count = 0

    print("\n" + "="*100)
    print("POPULATING RESPONSE MODES FOR ALL CHARACTERS")
    print("="*100)

    for character_id, modes in response_modes_data.items():
        # Check if character exists
        cur.execute("SELECT name FROM characters WHERE id = %s", (character_id,))
        char_result = cur.fetchone()
        
        if not char_result:
            print(f"\n⚠️  Character ID {character_id} not found, skipping")
            continue
        
        char_name = char_result[0]
        
        # Check existing modes
        cur.execute(
            "SELECT COUNT(*) FROM character_response_modes WHERE character_id = %s",
            (character_id,)
        )
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            print(f"\n✓ {char_name} (ID {character_id}): Already has {existing_count} modes, skipping")
            skipped_count += 1
            continue
        
        print(f"\n→ Populating {char_name} (ID {character_id}) with {len(modes)} modes:")
        
        for mode_name, mode_desc, response_style, length_guideline, tone_adj, priority in modes:
            cur.execute("""
                INSERT INTO character_response_modes 
                (character_id, mode_name, mode_description, response_style, length_guideline, 
                 tone_adjustment, conflict_resolution_priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (character_id, mode_name, mode_desc, response_style, length_guideline, tone_adj, priority))
            
            inserted_count += 1
            print(f"   ✓ {mode_name} (priority {priority})")

    conn.commit()

    print(f"\n" + "="*100)
    print(f"✅ SUCCESS: Inserted {inserted_count} response modes, Skipped {skipped_count}")
    print("="*100)

    # Verify
    print("\nVERIFYING:")
    cur.execute("""
    SELECT 
        c.id,
        c.name,
        COUNT(crm.id) as mode_count
    FROM characters c
    LEFT JOIN character_response_modes crm ON c.id = crm.character_id
    WHERE c.id IN (1, 2, 4, 10, 11, 12, 13, 14, 15, 49)
    GROUP BY c.id, c.name
    ORDER BY c.id;
    """)

    print("="*100)
    for char_id, char_name, mode_count in cur.fetchall():
        status = "✓" if mode_count > 0 else "✗"
        print(f"{status} ID {char_id:2d}: {char_name:25s} - {mode_count} modes")

    conn.close()

if __name__ == "__main__":
    try:
        populate_response_modes()
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
