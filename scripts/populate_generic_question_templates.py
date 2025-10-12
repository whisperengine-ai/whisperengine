#!/usr/bin/env python3
"""
Populate character_question_templates table with generic personality-style questioning templates.

This approach eliminates character-specific hardcoding and instead uses generic personality styles
that can be mapped to any character based on their CDL traits.

FIXES ARCHITECTURE VIOLATION: No character-specific hardcoded logic!
"""

import asyncio
import os
import asyncpg
from typing import Dict, List, Tuple

# Generic personality style templates (NO character names hardcoded)
PERSONALITY_STYLE_TEMPLATES = {
    'warm_educational': {
        # For characters with warm, educational, enthusiastic traits
        'description': 'Warm, educational, curious, enthusiastic questioning style',
        'templates': {
            'origin': [
                ("I'm curious - how did you first discover your passion for {entity_name}?", 1, ['learned', 'discovered', 'started', 'began', 'introduction']),
                ("What sparked your interest in {entity_name} initially?", 2, ['learned', 'discovered', 'started']),
                ("I'd love to hear about how you got started with {entity_name}!", 3, ['started', 'began', 'introduction'])
            ],
            'experience': [
                ("How has your journey with {entity_name} been so far?", 1, ['experience', 'journey', 'time']),
                ("What's been your experience exploring {entity_name}?", 2, ['experience', 'exploring', 'duration']),
                ("I'm fascinated - how long have you been involved with {entity_name}?", 3, ['time', 'duration', 'years'])
            ],
            'specifics': [
                ("What aspects of {entity_name} captivate you the most?", 1, ['favorite', 'aspects', 'captivate']),
                ("I'm curious about what draws you to {entity_name} specifically!", 2, ['draws', 'specifically', 'type']),
                ("What is it about {entity_name} that really resonates with you?", 3, ['resonates', 'preferred', 'style'])
            ],
            'location': [
                ("Where do you usually enjoy {entity_name}? I'd love to know!", 1, ['where', 'location', 'place']),
                ("Do you have a special place where you practice {entity_name}?", 2, ['special place', 'practice', 'local']),
                ("I'm curious - where do your {entity_name} adventures take you?", 3, ['adventures', 'where', 'take you'])
            ],
            'community': [
                ("Do you share your love of {entity_name} with others?", 1, ['share', 'love', 'others']),
                ("Have you found a community of people who also enjoy {entity_name}?", 2, ['community', 'people', 'enjoy']),
                ("I'm wondering - do you have friends who share your passion for {entity_name}?", 3, ['friends', 'share', 'passion'])
            ]
        }
    },
    'analytical_precise': {
        # For characters with analytical, precise, methodical traits
        'description': 'Analytical, precise, methodical, research-oriented questioning style',
        'templates': {
            'origin': [
                ("What was your initial entry point into {entity_name}?", 1, ['initial', 'entry point', 'started']),
                ("How did you first encounter and begin studying {entity_name}?", 2, ['encounter', 'studying', 'began']),
                ("What factors led to your engagement with {entity_name}?", 3, ['factors', 'led', 'engagement'])
            ],
            'experience': [
                ("What has been the duration and depth of your experience with {entity_name}?", 1, ['duration', 'depth', 'experience']),
                ("How would you characterize your expertise level in {entity_name}?", 2, ['characterize', 'expertise', 'level']),
                ("What is the timeline of your involvement with {entity_name}?", 3, ['timeline', 'involvement', 'years'])
            ],
            'specifics': [
                ("Which specific aspects or methodologies of {entity_name} interest you most?", 1, ['specific aspects', 'methodologies', 'interest']),
                ("What particular elements of {entity_name} do you focus on?", 2, ['particular elements', 'focus', 'type']),
                ("How would you define your area of specialization within {entity_name}?", 3, ['define', 'specialization', 'area'])
            ],
            'location': [
                ("In what context or environment do you typically engage with {entity_name}?", 1, ['context', 'environment', 'engage']),
                ("What are the primary locations where you practice {entity_name}?", 2, ['primary locations', 'practice', 'where']),
                ("Where do you conduct your {entity_name} activities?", 3, ['conduct', 'activities', 'location'])
            ],
            'community': [
                ("Do you collaborate with others in the {entity_name} field?", 1, ['collaborate', 'others', 'field']),
                ("What professional networks exist around your {entity_name} interests?", 2, ['professional networks', 'exist', 'interests']),
                ("How do you engage with the broader {entity_name} community?", 3, ['engage', 'broader', 'community'])
            ]
        }
    },
    'casual_adventurous': {
        # For characters with casual, adventurous, enthusiastic traits
        'description': 'Casual, adventurous, enthusiastic, informal questioning style',
        'templates': {
            'origin': [
                ("Dude, how did you get into {entity_name}? That's awesome!", 1, ['get into', 'awesome', 'started']),
                ("What got you hooked on {entity_name}?", 2, ['got you hooked', 'hooked', 'began']),
                ("That's cool! How did your {entity_name} journey begin?", 3, ['cool', 'journey begin', 'started'])
            ],
            'experience': [
                ("How long have you been doing {entity_name}? Must be epic!", 1, ['how long', 'epic', 'doing']),
                ("What's your {entity_name} experience been like so far?", 2, ['experience', 'so far', 'been like']),
                ("Sweet! How much time have you spent with {entity_name}?", 3, ['sweet', 'time spent', 'duration'])
            ],
            'specifics': [
                ("What's the coolest thing about {entity_name} for you?", 1, ['coolest thing', 'for you', 'favorite']),
                ("What part of {entity_name} gets you most excited?", 2, ['gets you excited', 'most excited', 'aspect']),
                ("Awesome! What type of {entity_name} do you dig the most?", 3, ['dig the most', 'type', 'preferred'])
            ],
            'location': [
                ("Where do you usually go for your {entity_name} adventures?", 1, ['adventures', 'usually go', 'where']),
                ("What are your favorite spots for {entity_name}?", 2, ['favorite spots', 'spots', 'place']),
                ("Sounds rad! Where do you like to do {entity_name}?", 3, ['rad', 'like to do', 'location'])
            ],
            'community': [
                ("Do you have a crew you do {entity_name} with?", 1, ['crew', 'do with', 'others']),
                ("Have you met other people through {entity_name}?", 2, ['met people', 'through', 'people']),
                ("That's sick! Do you share {entity_name} with friends?", 3, ['sick', 'share with', 'friends'])
            ]
        }
    },
    'mystical_philosophical': {
        # For characters with mystical, philosophical, profound traits
        'description': 'Mystical, philosophical, profound, spiritual questioning style',
        'templates': {
            'origin': [
                ("What drew your essence toward the realm of {entity_name}?", 1, ['essence', 'realm', 'drew']),
                ("How did the path of {entity_name} first call to your consciousness?", 2, ['path', 'call', 'consciousness']),
                ("What sacred moment awakened your connection to {entity_name}?", 3, ['sacred moment', 'awakened', 'connection'])
            ],
            'experience': [
                ("How has your journey through {entity_name} shaped your understanding?", 1, ['journey', 'shaped', 'understanding']),
                ("What wisdom has {entity_name} revealed to you over time?", 2, ['wisdom', 'revealed', 'time']),
                ("How deeply have you explored the mysteries of {entity_name}?", 3, ['deeply', 'mysteries', 'explored'])
            ],
            'specifics': [
                ("Which facets of {entity_name} resonate most profoundly with your being?", 1, ['facets', 'resonate', 'profoundly']),
                ("What essential truth within {entity_name} speaks to your soul?", 2, ['essential truth', 'speaks', 'soul']),
                ("What aspect of {entity_name} illuminates your inner landscape?", 3, ['illuminates', 'inner landscape', 'aspect'])
            ],
            'location': [
                ("In what sacred spaces do you commune with {entity_name}?", 1, ['sacred spaces', 'commune', 'spaces']),
                ("Where does your spirit find harmony with {entity_name}?", 2, ['spirit', 'harmony', 'find']),
                ("What realm serves as your sanctuary for {entity_name}?", 3, ['realm', 'sanctuary', 'serves'])
            ],
            'community': [
                ("Do other souls share in your {entity_name} journey?", 1, ['souls share', 'journey', 'souls']),
                ("Have you found kindred spirits through {entity_name}?", 2, ['kindred spirits', 'found', 'spirits']),
                ("What connections has {entity_name} woven into your existence?", 3, ['connections', 'woven', 'existence'])
            ]
        }
    },
    'creative_technical': {
        # For characters with creative, technical, laid-back traits
        'description': 'Creative, technical, laid-back, innovative questioning style',
        'templates': {
            'origin': [
                ("How'd you first get into {entity_name}? That's pretty cool!", 1, ['get into', 'first', 'pretty cool']),
                ("What made you start exploring {entity_name}?", 2, ['made you start', 'exploring', 'start']),
                ("Nice! What got you interested in {entity_name} originally?", 3, ['got you interested', 'originally', 'interested'])
            ],
            'experience': [
                ("How's your {entity_name} journey been going?", 1, ['journey', 'been going', 'going']),
                ("What's your experience level with {entity_name} like?", 2, ['experience level', 'like', 'level']),
                ("How long have you been working with {entity_name}?", 3, ['working with', 'how long', 'been'])
            ],
            'specifics': [
                ("What aspects of {entity_name} do you find most interesting?", 1, ['aspects', 'most interesting', 'find']),
                ("What's your favorite part about {entity_name}?", 2, ['favorite part', 'about', 'favorite']),
                ("Which elements of {entity_name} really grab your attention?", 3, ['elements', 'grab attention', 'attention'])
            ],
            'location': [
                ("Where do you usually work on {entity_name} stuff?", 1, ['work on', 'stuff', 'usually']),
                ("What's your go-to spot for {entity_name}?", 2, ['go-to spot', 'spot', 'go-to']),
                ("Where do you like to practice {entity_name}?", 3, ['like to practice', 'practice', 'where'])
            ],
            'community': [
                ("Do you collaborate with other people on {entity_name}?", 1, ['collaborate', 'other people', 'people']),
                ("Have you connected with the {entity_name} community?", 2, ['connected', 'community', 'connected']),
                ("Are there others you share {entity_name} interests with?", 3, ['share interests', 'others', 'interests'])
            ]
        }
    },
    'refined_courteous': {
        # For characters with refined, courteous, articulate traits
        'description': 'Refined, courteous, articulate, formal questioning style',
        'templates': {
            'origin': [
                ("I say, how did you first become acquainted with {entity_name}?", 1, ['become acquainted', 'first', 'acquainted']),
                ("Might I inquire as to what introduced you to {entity_name}?", 2, ['inquire', 'introduced', 'might']),
                ("How delightful! What drew you to {entity_name} initially?", 3, ['delightful', 'drew you', 'initially'])
            ],
            'experience': [
                ("How extensive has your experience with {entity_name} been?", 1, ['extensive', 'experience', 'been']),
                ("What has been the nature of your engagement with {entity_name}?", 2, ['nature', 'engagement', 'nature']),
                ("For how long have you been pursuing {entity_name}?", 3, ['pursuing', 'how long', 'been'])
            ],
            'specifics': [
                ("What particular aspects of {entity_name} do you find most compelling?", 1, ['particular aspects', 'compelling', 'find']),
                ("Which elements of {entity_name} capture your interest most keenly?", 2, ['elements', 'capture', 'keenly']),
                ("What is it about {entity_name} that appeals to you specifically?", 3, ['appeals', 'specifically', 'appeals'])
            ],
            'location': [
                ("Where do you typically pursue your {entity_name} interests?", 1, ['typically pursue', 'interests', 'pursue']),
                ("In what setting do you usually engage with {entity_name}?", 2, ['setting', 'engage', 'usually']),
                ("Might I ask where you practice {entity_name}?", 3, ['might ask', 'practice', 'ask'])
            ],
            'community': [
                ("Do you share your {entity_name} interests with fellow enthusiasts?", 1, ['fellow enthusiasts', 'share', 'enthusiasts']),
                ("Have you found companionship through {entity_name}?", 2, ['companionship', 'found', 'companionship']),
                ("Are there others with whom you discuss {entity_name}?", 3, ['discuss', 'others', 'whom'])
            ]
        }
    },
    'professional_strategic': {
        # For characters with professional, strategic, confident traits
        'description': 'Professional, strategic, confident, business-oriented questioning style',
        'templates': {
            'origin': [
                ("What was your initial motivation for getting involved with {entity_name}?", 1, ['initial motivation', 'getting involved', 'motivation']),
                ("How did you first identify {entity_name} as an area of interest?", 2, ['identify', 'area of interest', 'first']),
                ("What drove your decision to pursue {entity_name}?", 3, ['drove', 'decision', 'pursue'])
            ],
            'experience': [
                ("What's your track record with {entity_name} been like?", 1, ['track record', 'been like', 'record']),
                ("How would you assess your experience level in {entity_name}?", 2, ['assess', 'experience level', 'assess']),
                ("What's the scope of your involvement with {entity_name}?", 3, ['scope', 'involvement', 'scope'])
            ],
            'specifics': [
                ("Which strategic aspects of {entity_name} align with your goals?", 1, ['strategic aspects', 'align', 'goals']),
                ("What value proposition does {entity_name} offer you?", 2, ['value proposition', 'offer', 'proposition']),
                ("Which components of {entity_name} deliver the most impact for you?", 3, ['components', 'deliver', 'impact'])
            ],
            'location': [
                ("What's your preferred environment for {entity_name} activities?", 1, ['preferred environment', 'activities', 'preferred']),
                ("Where do you optimize your {entity_name} performance?", 2, ['optimize', 'performance', 'optimize']),
                ("What setting works best for your {entity_name} engagement?", 3, ['setting', 'works best', 'engagement'])
            ],
            'community': [
                ("How do you network within the {entity_name} space?", 1, ['network', 'space', 'network']),
                ("What's your strategy for building {entity_name} connections?", 2, ['strategy', 'building', 'connections']),
                ("How do you leverage relationships in the {entity_name} community?", 3, ['leverage', 'relationships', 'community'])
            ]
        }
    },
    'neutral_default': {
        # Default fallback style for any character
        'description': 'Neutral, balanced, general-purpose questioning style',
        'templates': {
            'origin': [
                ("How did you first get interested in {entity_name}?", 1, ['interested', 'first', 'started']),
                ("What brought you to {entity_name}?", 2, ['brought', 'started', 'began']),
                ("How did you discover {entity_name}?", 3, ['discover', 'found', 'learned'])
            ],
            'experience': [
                ("How long have you been involved with {entity_name}?", 1, ['long', 'involved', 'experience']),
                ("What's your experience with {entity_name} been like?", 2, ['experience', 'been like', 'time']),
                ("How much experience do you have with {entity_name}?", 3, ['much experience', 'experience', 'duration'])
            ],
            'specifics': [
                ("What do you like most about {entity_name}?", 1, ['like most', 'favorite', 'prefer']),
                ("What aspects of {entity_name} interest you?", 2, ['aspects', 'interest', 'type']),
                ("What draws you to {entity_name}?", 3, ['draws', 'attracts', 'appeal'])
            ],
            'location': [
                ("Where do you usually practice {entity_name}?", 1, ['practice', 'usually', 'where']),
                ("What's your preferred location for {entity_name}?", 2, ['preferred', 'location', 'place']),
                ("Where do you engage with {entity_name}?", 3, ['engage', 'where', 'location'])
            ],
            'community': [
                ("Do you share {entity_name} with others?", 1, ['share', 'others', 'people']),
                ("Have you met others interested in {entity_name}?", 2, ['met others', 'interested', 'community']),
                ("Do you have friends who also enjoy {entity_name}?", 3, ['friends', 'enjoy', 'share'])
            ]
        }
    }
}

# Character to personality style mapping (this could be moved to database eventually)
CHARACTER_STYLE_MAPPING = {
    # These would be determined by CDL traits, not hardcoded character names
    # For now, we'll use a simple mapping that can be replaced with CDL-based logic
    'default': 'neutral_default'  # Everyone gets neutral unless specifically mapped
}

async def populate_generic_question_templates():
    """Populate character_question_templates table with generic personality-style templates."""
    
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🎭 GENERIC QUESTION TEMPLATES: Starting database population...")
        
        # Get all characters
        characters = await conn.fetch("SELECT id, name FROM characters")
        print(f"📋 Found {len(characters)} characters")
        
        # Clear existing data
        await conn.execute("DELETE FROM character_question_templates")
        print("🧹 Cleared existing question templates")
        
        # Insert generic templates for all characters using neutral_default style
        total_inserted = 0
        default_style = 'neutral_default'
        default_templates = PERSONALITY_STYLE_TEMPLATES[default_style]
        
        for character in characters:
            char_id = character['id']
            char_name = character['name']
            
            # Use neutral_default for all characters (eliminates hardcoding)
            personality_style = default_style
            templates_data = default_templates['templates']
            
            for gap_type, templates_list in templates_data.items():
                for template_text, priority_order, keywords in templates_list:
                    await conn.execute("""
                        INSERT INTO character_question_templates 
                        (character_id, gap_type, template_text, personality_style, priority_order, keywords)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, char_id, gap_type, template_text, personality_style, priority_order, keywords)
                    total_inserted += 1
            
            character_templates = sum(len(templates_list) for templates_list in templates_data.values())
            print(f"✅ {char_name} ({personality_style}): Inserted {character_templates} question templates")
        
        print(f"🎯 GENERIC TEMPLATES: Successfully populated {total_inserted} templates for {len(characters)} characters")
        
        # Show summary
        gap_summary = await conn.fetch("""
            SELECT gap_type, COUNT(*) as count
            FROM character_question_templates
            GROUP BY gap_type
            ORDER BY count DESC
        """)
        
        print("\\n📊 SUMMARY by gap type:")
        for row in gap_summary:
            print(f"  {row['gap_type']}: {row['count']} templates")
        
        print("\\n🚀 Generic question templates population complete!")
        print("\\n💡 ARCHITECTURE COMPLIANCE:")
        print("   ✅ No character-specific hardcoded logic")
        print("   ✅ All characters use same neutral template set")
        print("   ✅ Templates are guidance for LLM, not rigid rules")
        print("   ✅ Extensible to personality-based mapping via CDL traits")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error populating generic question templates: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(populate_generic_question_templates())