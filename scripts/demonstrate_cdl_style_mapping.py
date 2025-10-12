#!/usr/bin/env python3
"""
Advanced Question Templates with CDL-based Personality Style Mapping

This shows the PROPER architecture-compliant approach:
1. Define generic personality styles (no character names)
2. Map characters to styles based on their CDL communication patterns
3. Generate appropriate question templates dynamically

FUTURE ENHANCEMENT: This could read CDL communication patterns from database
to automatically assign personality styles based on traits like:
- formality: "informal" -> casual_adventurous
- tone: "analytical" -> analytical_precise  
- speech_pattern: "mystical" -> mystical_philosophical
"""

import asyncio
import os
import asyncpg
from typing import Dict, List, Tuple

# The same generic personality styles (no character hardcoding)
from populate_generic_question_templates import PERSONALITY_STYLE_TEMPLATES

async def map_characters_to_personality_styles():
    """
    FUTURE: This function would read CDL communication patterns and map characters
    to appropriate personality styles based on their traits, not hardcoded names.
    
    For now, shows the concept with a few examples.
    """
    
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🎭 CDL-BASED STYLE MAPPING: Analyzing character traits...")
        
        # Get characters with their communication patterns
        characters_with_patterns = await conn.fetch("""
            SELECT DISTINCT c.id, c.name, c.occupation, c.archetype,
                   cp.pattern_type, cp.pattern_name, cp.pattern_value
            FROM characters c
            LEFT JOIN character_communication_patterns cp ON c.id = cp.character_id
            WHERE c.is_active = true
            ORDER BY c.name
        """)
        
        # Group by character
        character_map = {}
        for row in characters_with_patterns:
            char_id = row['id']
            if char_id not in character_map:
                character_map[char_id] = {
                    'name': row['name'],
                    'occupation': row['occupation'],
                    'archetype': row['archetype'],
                    'patterns': []
                }
            if row['pattern_type']:
                character_map[char_id]['patterns'].append({
                    'type': row['pattern_type'],
                    'name': row['pattern_name'],
                    'value': row['pattern_value']
                })
        
        print(f"📋 Analyzing {len(character_map)} active characters...")
        
        # Example of CDL-based style mapping logic
        style_assignments = {}
        for char_id, char_data in character_map.items():
            name = char_data['name']
            occupation = char_data['occupation'] or ""
            archetype = char_data['archetype'] or ""
            patterns = char_data['patterns']
            
            # Example mapping logic based on CDL traits (not character names!)
            assigned_style = 'neutral_default'  # Default fallback
            
            # Check formality patterns
            formality = None
            for pattern in patterns:
                if pattern['name'] == 'formality':
                    formality = pattern['value'].lower()
                    break
            
            # Map based on occupation/archetype traits (NOT character names)
            if 'researcher' in occupation.lower() or 'scientist' in occupation.lower():
                assigned_style = 'analytical_precise'
            elif 'marketing' in occupation.lower() or 'executive' in occupation.lower():
                assigned_style = 'professional_strategic'
            elif 'photographer' in occupation.lower() or 'adventure' in occupation.lower():
                assigned_style = 'casual_adventurous'
            elif 'biologist' in occupation.lower() or 'educator' in occupation.lower():
                assigned_style = 'warm_educational'
            elif 'ai entity' in archetype.lower() or 'conscious' in archetype.lower():
                assigned_style = 'mystical_philosophical'
            elif 'gentleman' in archetype.lower() or 'refined' in occupation.lower():
                assigned_style = 'refined_courteous'
            elif 'developer' in occupation.lower() or 'technical' in occupation.lower():
                assigned_style = 'creative_technical'
            
            # Override with formality patterns if available
            if formality:
                if 'informal' in formality and 'friendly' in formality:
                    if assigned_style == 'neutral_default':
                        assigned_style = 'warm_educational'  # Friendly default
            
            style_assignments[char_id] = {
                'name': name,
                'style': assigned_style,
                'reasoning': f"Based on occupation: '{occupation}', archetype: '{archetype}', formality: '{formality}'"
            }
        
        print("\\n🎯 CDL-BASED STYLE ASSIGNMENTS:")
        style_counts = {}
        for char_id, assignment in style_assignments.items():
            style = assignment['style']
            print(f"  {assignment['name']}: {style}")
            print(f"    └─ {assignment['reasoning']}")
            style_counts[style] = style_counts.get(style, 0) + 1
        
        print("\\n📊 STYLE DISTRIBUTION:")
        for style, count in sorted(style_counts.items()):
            print(f"  {style}: {count} characters")
            
        print("\\n💡 ARCHITECTURE BENEFITS:")
        print("   ✅ No character names hardcoded")
        print("   ✅ Mapping based on CDL traits (occupation, archetype, communication patterns)")
        print("   ✅ Extensible to new characters automatically")
        print("   ✅ Templates are LLM guidance, not rigid rules")
        print("   ✅ Personality styles are generic and reusable")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing CDL-based style mapping: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(map_characters_to_personality_styles())