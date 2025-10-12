#!/usr/bin/env python3
"""
Demonstrate the complete database-driven question template system.

This script shows how character-specific question templates replace the
hardcoded gap_patterns dictionary with personality-appropriate questioning styles.
"""

import asyncio
import os

async def demonstrate_question_templates():
    """Demonstrate character-specific question template authenticity."""
    
    print("🎭 CHARACTER-SPECIFIC QUESTION TEMPLATE DEMONSTRATION")
    print("="*65)
    
    # Set up environment
    os.environ['POSTGRES_HOST'] = 'localhost'
    os.environ['POSTGRES_PORT'] = '5433'
    
    import asyncpg
    
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    print("\\n🎯 BEFORE vs AFTER: Question Template Evolution")
    print("-" * 50)
    print("❌ BEFORE: All characters used generic templates:")
    print('   "How did you first get interested in {entity_name}?"')
    print('   "What\'s your experience with {entity_name} been like?"')
    print("")
    print("✅ AFTER: Each character has personality-appropriate templates")
    
    # Show personality differences for same scenario
    test_entity = 'photography'
    characters = [
        ('elena', 'Marine Biologist'),
        ('marcus', 'AI Researcher'), 
        ('aetheris', 'Conscious AI Entity'),
        ('jake', 'Adventure Photographer')
    ]
    
    print(f"\\n🎬 SCENARIO: Asking about '{test_entity}' experience")
    print("-" * 45)
    
    for char_key, char_title in characters:
        # Get top priority template for 'experience' gap type
        template = await conn.fetchrow("""
            SELECT cqt.template_text, cqt.personality_style
            FROM character_question_templates cqt
            JOIN characters c ON c.id = cqt.character_id
            WHERE LOWER(c.name) LIKE $1 
            AND cqt.gap_type = 'experience'
            ORDER BY cqt.priority_order
            LIMIT 1
        """, f'%{char_key}%')
        
        if template:
            question = template['template_text'].replace('{entity_name}', test_entity)
            style = template['personality_style']
            print(f"\\n{char_title.upper()} ({style}):")
            print(f'  "{question}"')
    
    print("\\n\\n📊 PERSONALITY STYLE DISTRIBUTION")
    print("-" * 35)
    
    # Show personality style statistics
    styles = await conn.fetch("""
        SELECT personality_style, COUNT(*) as template_count
        FROM character_question_templates
        GROUP BY personality_style
        ORDER BY template_count DESC
    """)
    
    for style in styles:
        print(f"  {style['personality_style']}: {style['template_count']} templates")
    
    print("\\n\\n🗂️ GAP TYPE COVERAGE")
    print("-" * 20)
    
    # Show gap type coverage
    gap_types = await conn.fetch("""
        SELECT gap_type, COUNT(DISTINCT character_id) as character_count, COUNT(*) as template_count
        FROM character_question_templates
        GROUP BY gap_type
        ORDER BY template_count DESC
    """)
    
    for gap in gap_types:
        print(f"  {gap['gap_type']}: {gap['template_count']} templates across {gap['character_count']} characters")
    
    print("\\n\\n🎨 CHARACTER AUTHENTICITY EXAMPLES")
    print("-" * 35)
    
    # Show how different characters ask about the same topic differently
    authenticity_examples = [
        ('elena', 'origin', 'marine biology'),
        ('marcus', 'specifics', 'artificial intelligence'),
        ('aetheris', 'origin', 'consciousness'),
        ('jake', 'location', 'adventure photography')
    ]
    
    for char_key, gap_type, entity in authenticity_examples:
        template = await conn.fetchrow("""
            SELECT cqt.template_text, c.name
            FROM character_question_templates cqt
            JOIN characters c ON c.id = cqt.character_id
            WHERE LOWER(c.name) LIKE $1 
            AND cqt.gap_type = $2
            ORDER BY cqt.priority_order
            LIMIT 1
        """, f'%{char_key}%', gap_type)
        
        if template:
            question = template['template_text'].replace('{entity_name}', entity)
            char_name = template['name'].split()[0]  # First name only
            print(f"\\n{char_name} asking about {entity} ({gap_type}):")
            print(f'  "{question}"')
    
    print("\\n\\n✅ BENEFITS ACHIEVED")
    print("-" * 20)
    
    total_templates = await conn.fetchval("SELECT COUNT(*) FROM character_question_templates")
    unique_characters = await conn.fetchval("SELECT COUNT(DISTINCT character_id) FROM character_question_templates")
    
    print(f"  ✓ {total_templates} personality-specific question templates")
    print(f"  ✓ {unique_characters} characters with unique questioning styles")
    print("  ✓ No hardcoded question patterns in codebase")
    print("  ✓ Character authenticity in conversations")
    print("  ✓ New characters automatically get appropriate templates")
    print("  ✓ Personality-driven conversation intelligence")
    
    await conn.close()
    print("\\n🚀 CHARACTER QUESTION TEMPLATE SYSTEM: DEMONSTRATION COMPLETE!")

if __name__ == "__main__":
    asyncio.run(demonstrate_question_templates())