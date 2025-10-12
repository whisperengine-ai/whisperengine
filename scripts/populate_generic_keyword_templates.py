#!/usr/bin/env python3
"""
Populate generic_keyword_templates table with AI identity and physical interaction keywords.

This replaces hardcoded keyword lists in cdl_ai_integration.py with database-driven,
generic templates that provide LLM guidance for detecting common conversation patterns.

ARCHITECTURE COMPLIANCE:
- No character-specific hardcoding
- Generic templates usable by any character  
- LLM guidance, not rigid rules
- Extensible without code changes
"""

import asyncio
import os
import asyncpg

# Generic keyword templates (no character-specific logic)
GENERIC_KEYWORD_TEMPLATES = {
    'ai_identity': [
        {
            'template_name': 'basic_ai_terms',
            'keywords': ['ai', 'artificial intelligence', 'robot', 'computer', 'program', 'bot'],
            'description': 'Basic AI-related terms that might prompt identity questions',
            'priority_order': 1
        },
        {
            'template_name': 'technical_ai_terms', 
            'keywords': ['machine learning', 'neural network', 'algorithm', 'artificial', 'digital'],
            'description': 'Technical AI-related terms for advanced identity discussions',
            'priority_order': 2
        },
        {
            'template_name': 'consciousness_terms',
            'keywords': ['conscious', 'sentient', 'aware', 'thinking', 'intelligence'],
            'description': 'Consciousness and awareness related terms',
            'priority_order': 3
        }
    ],
    'physical_interaction': [
        {
            'template_name': 'basic_physical_contact',
            'keywords': ['hug', 'kiss', 'touch', 'hold', 'cuddle', 'pet', 'pat', 'embrace'],
            'description': 'Basic physical interaction requests that may need special handling',
            'priority_order': 1
        },
        {
            'template_name': 'intimate_physical_contact',
            'keywords': ['caress', 'stroke', 'massage', 'snuggle', 'nuzzle', 'squeeze'],
            'description': 'More intimate physical interaction terms',
            'priority_order': 2
        },
        {
            'template_name': 'casual_physical_contact',
            'keywords': ['handshake', 'high five', 'fist bump', 'shoulder pat', 'hand on shoulder'],
            'description': 'Casual, friendly physical interaction terms',
            'priority_order': 3
        }
    ],
    'romantic_interaction': [
        {
            'template_name': 'romantic_expressions',
            'keywords': ['love', 'romance', 'date', 'relationship', 'romantic', 'valentine'],
            'description': 'Romantic interaction terms that may need character-appropriate responses',
            'priority_order': 1
        },
        {
            'template_name': 'affection_terms',
            'keywords': ['honey', 'sweetheart', 'darling', 'beloved', 'dear', 'babe'],
            'description': 'Terms of endearment and affection',
            'priority_order': 2
        }
    ],
    'emotional_support': [
        {
            'template_name': 'distress_indicators',
            'keywords': ['sad', 'depressed', 'anxious', 'worried', 'scared', 'upset', 'crying'],
            'description': 'Terms indicating user emotional distress requiring supportive responses',
            'priority_order': 1
        },
        {
            'template_name': 'crisis_indicators', 
            'keywords': ['suicide', 'kill myself', 'end it all', 'hopeless', 'worthless'],
            'description': 'Crisis-level emotional indicators requiring careful handling',
            'priority_order': 2
        }
    ]
}

async def populate_generic_keyword_templates():
    """Populate generic_keyword_templates table with generic LLM guidance templates."""
    
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🔑 GENERIC KEYWORD TEMPLATES: Starting database population...")
        
        # Clear existing data
        await conn.execute("DELETE FROM generic_keyword_templates")
        print("🧹 Cleared existing keyword templates")
        
        # Insert generic keyword templates
        total_inserted = 0
        for category, templates_list in GENERIC_KEYWORD_TEMPLATES.items():
            for template_data in templates_list:
                await conn.execute("""
                    INSERT INTO generic_keyword_templates 
                    (category, template_name, keywords, description, priority_order, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                category, 
                template_data['template_name'],
                template_data['keywords'],
                template_data['description'],
                template_data['priority_order'],
                True
                )
                total_inserted += 1
                
                print(f"✅ {category}.{template_data['template_name']}: {len(template_data['keywords'])} keywords")
        
        print(f"🎯 KEYWORD TEMPLATES: Successfully populated {total_inserted} generic templates")
        
        # Show summary by category
        category_summary = await conn.fetch("""
            SELECT category, COUNT(*) as template_count, SUM(array_length(keywords, 1)) as total_keywords
            FROM generic_keyword_templates
            GROUP BY category
            ORDER BY category
        """)
        
        print("\\n📊 SUMMARY by category:")
        for row in category_summary:
            print(f"  {row['category']}: {row['template_count']} templates, {row['total_keywords']} keywords total")
        
        # Show examples of each category
        print("\\n🔍 EXAMPLES by category:")
        for category in GENERIC_KEYWORD_TEMPLATES.keys():
            example = await conn.fetchrow("""
                SELECT template_name, keywords[1:3] as sample_keywords, description
                FROM generic_keyword_templates
                WHERE category = $1
                ORDER BY priority_order
                LIMIT 1
            """, category)
            
            if example:
                sample_keywords = ", ".join(example['sample_keywords'][:3])
                print(f"  {category}: {example['template_name']} - [{sample_keywords}...] - {example['description']}")
        
        print("\\n💡 ARCHITECTURE BENEFITS:")
        print("   ✅ No character-specific hardcoded logic")
        print("   ✅ Generic templates work for any character")
        print("   ✅ LLM guidance, not rigid keyword matching")
        print("   ✅ Extensible without code changes")
        print("   ✅ Categories support different conversation patterns")
        
        await conn.close()
        print("\\n🚀 Generic keyword templates population complete!")
        
    except Exception as e:
        print(f"❌ Error populating generic keyword templates: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(populate_generic_keyword_templates())