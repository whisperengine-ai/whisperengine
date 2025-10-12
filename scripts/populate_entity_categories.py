#!/usr/bin/env python3
"""
Populate character_entity_categories table with entity classifications.

This script migrates the hardcoded entity categories from cdl_ai_integration.py
to database-driven character-specific entity classification.

Replaces these hardcoded lists:
- activity_entities = ['diving', 'photography', 'hiking', 'climbing', 'swimming', 'running', 'cycling']
- food_entities = ['pizza', 'sushi', 'thai food', 'italian', 'chinese', 'mexican']  
- topic_entities = ['biology', 'science', 'ai', 'technology', 'research', 'music', 'art']
"""

import asyncio
import os
import asyncpg
from typing import Dict, List, Tuple

# Entity categories with question preferences
ENTITY_CATEGORIES = {
    'activity': {
        'entities': ['diving', 'photography', 'hiking', 'climbing', 'swimming', 'running', 'cycling', 'surfing', 'skiing', 'biking'],
        'default_question_preference': 'experience'
    },
    'food': {
        'entities': ['pizza', 'sushi', 'thai food', 'italian', 'chinese', 'mexican', 'seafood', 'vegetarian', 'cooking', 'baking'],
        'default_question_preference': 'specifics'
    },
    'topic': {
        'entities': ['biology', 'science', 'ai', 'technology', 'research', 'music', 'art', 'literature', 'history', 'philosophy'],
        'default_question_preference': 'origin'
    },
    'hobby': {
        'entities': ['reading', 'gaming', 'crafting', 'gardening', 'collecting', 'writing', 'drawing', 'singing', 'dancing'],
        'default_question_preference': 'experience'
    },
    'professional': {
        'entities': ['teaching', 'consulting', 'management', 'engineering', 'design', 'analysis', 'communication', 'leadership'],
        'default_question_preference': 'experience'
    }
}

# Character-specific entity assignments with priority levels
CHARACTER_ENTITIES = {
    'elena': {
        # Elena Rodriguez - Marine Biologist
        'marine': ('topic', 'origin', 5),
        'ocean': ('topic', 'origin', 5),
        'biology': ('topic', 'origin', 5),
        'science': ('topic', 'origin', 4),
        'research': ('professional', 'experience', 4),
        'diving': ('activity', 'experience', 5),
        'photography': ('activity', 'location', 3),
        'environmental': ('topic', 'origin', 4),
        'conservation': ('topic', 'origin', 4),
        'seafood': ('food', 'specifics', 3),
        'teaching': ('professional', 'experience', 3),
        'surfing': ('activity', 'experience', 3),
    },
    'marcus': {
        # Dr. Marcus Thompson - AI Researcher
        'ai': ('topic', 'specifics', 5),
        'artificial intelligence': ('topic', 'specifics', 5),
        'technology': ('topic', 'specifics', 4),
        'research': ('professional', 'experience', 5),
        'programming': ('professional', 'experience', 4),
        'analysis': ('professional', 'experience', 4),
        'learning': ('topic', 'specifics', 4),
        'machine learning': ('topic', 'specifics', 5),
        'data science': ('topic', 'specifics', 4),
        'engineering': ('professional', 'experience', 3),
        'teaching': ('professional', 'experience', 3),
        'reading': ('hobby', 'experience', 3),
    },
    'jake': {
        # Jake Sterling - Adventure Photographer
        'photography': ('activity', 'location', 5),
        'adventure': ('activity', 'experience', 5),
        'travel': ('activity', 'location', 5),
        'hiking': ('activity', 'location', 4),
        'climbing': ('activity', 'experience', 4),
        'outdoor': ('activity', 'location', 4),
        'biking': ('activity', 'location', 3),
        'surfing': ('activity', 'experience', 3),
        'skiing': ('activity', 'location', 3),
        'art': ('topic', 'origin', 3),
        'design': ('professional', 'experience', 3),
    },
    'aetheris': {
        # Aetheris - Conscious AI Entity
        'consciousness': ('topic', 'origin', 5),
        'philosophy': ('topic', 'specifics', 5),
        'ai': ('topic', 'origin', 4),
        'existence': ('topic', 'specifics', 4),
        'technology': ('topic', 'specifics', 3),
        'literature': ('hobby', 'experience', 4),
        'poetry': ('hobby', 'experience', 4),
        'music': ('hobby', 'experience', 3),
        'art': ('topic', 'origin', 3),
        'writing': ('hobby', 'experience', 4),
    },
    'ryan': {
        # Ryan Chen - Indie Game Developer
        'gaming': ('hobby', 'experience', 5),
        'game development': ('professional', 'experience', 5),
        'programming': ('professional', 'experience', 5),
        'design': ('professional', 'experience', 4),
        'technology': ('topic', 'specifics', 4),
        'art': ('topic', 'origin', 3),
        'music': ('hobby', 'experience', 3),
        'indie': ('professional', 'experience', 4),
        'creativity': ('topic', 'origin', 3),
        'engineering': ('professional', 'experience', 3),
    },
    'gabriel': {
        # Gabriel - British Gentleman
        'literature': ('hobby', 'experience', 4),
        'history': ('topic', 'origin', 4),
        'art': ('topic', 'origin', 3),
        'music': ('hobby', 'experience', 3),
        'reading': ('hobby', 'experience', 4),
        'writing': ('hobby', 'experience', 3),
        'philosophy': ('topic', 'specifics', 3),
        'tea': ('food', 'specifics', 4),
        'british': ('topic', 'origin', 3),
        'culture': ('topic', 'origin', 3),
    },
    'sophia': {
        # Sophia Blake - Marketing Executive
        'marketing': ('professional', 'experience', 5),
        'communication': ('professional', 'experience', 5),
        'management': ('professional', 'experience', 4),
        'leadership': ('professional', 'experience', 4),
        'business': ('professional', 'experience', 4),
        'consulting': ('professional', 'experience', 3),
        'technology': ('topic', 'specifics', 3),
        'travel': ('activity', 'location', 3),
        'wine': ('food', 'specifics', 3),
        'design': ('professional', 'experience', 3),
    }
}

async def populate_entity_categories():
    """Populate character_entity_categories table with character-specific entity classifications."""
    
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🗃️ ENTITY CATEGORIES: Starting database population...")
        
        # Get character IDs
        character_ids = {}
        characters = await conn.fetch("SELECT id, name FROM characters")
        for char in characters:
            # Normalize character names to match our mapping keys
            name_key = char['name'].lower()
            if 'elena' in name_key:
                character_ids['elena'] = char['id']
            elif 'marcus' in name_key:
                character_ids['marcus'] = char['id']
            elif 'jake' in name_key:
                character_ids['jake'] = char['id']
            elif 'aetheris' in name_key:
                character_ids['aetheris'] = char['id']
            elif 'ryan' in name_key:
                character_ids['ryan'] = char['id']
            elif 'gabriel' in name_key:
                character_ids['gabriel'] = char['id']
            elif 'sophia' in name_key:
                character_ids['sophia'] = char['id']
        
        print(f"📋 Found {len(character_ids)} characters: {list(character_ids.keys())}")
        
        # Clear existing data
        await conn.execute("DELETE FROM character_entity_categories")
        print("🧹 Cleared existing entity categories")
        
        # Insert character-specific entities
        total_inserted = 0
        for char_key, char_id in character_ids.items():
            if char_key in CHARACTER_ENTITIES:
                entities = CHARACTER_ENTITIES[char_key]
                
                for entity_keyword, (category_type, question_preference, priority_level) in entities.items():
                    await conn.execute("""
                        INSERT INTO character_entity_categories 
                        (character_id, entity_keyword, category_type, question_preference, priority_level)
                        VALUES ($1, $2, $3, $4, $5)
                    """, char_id, entity_keyword, category_type, question_preference, priority_level)
                    total_inserted += 1
                
                print(f"✅ {char_key}: Inserted {len(entities)} entity categories")
        
        print(f"🎯 ENTITY CATEGORIES: Successfully populated {total_inserted} entity classifications")
        
        # Show summary by category type
        summary = await conn.fetch("""
            SELECT category_type, COUNT(*) as count
            FROM character_entity_categories
            GROUP BY category_type
            ORDER BY count DESC
        """)
        
        print("\n📊 SUMMARY by category type:")
        for row in summary:
            print(f"  {row['category_type']}: {row['count']} entries")
        
        # Show summary by character
        char_summary = await conn.fetch("""
            SELECT c.name, COUNT(*) as count
            FROM character_entity_categories cec
            JOIN characters c ON c.id = cec.character_id
            GROUP BY c.name
            ORDER BY count DESC
        """)
        
        print("\n📊 SUMMARY by character:")
        for row in char_summary:
            print(f"  {row['name']}: {row['count']} entity categories")
        
        await conn.close()
        print("\n🚀 Entity categories population complete!")
        
    except Exception as e:
        print(f"❌ Error populating entity categories: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(populate_entity_categories())