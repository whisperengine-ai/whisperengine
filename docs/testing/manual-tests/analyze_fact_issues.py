#!/usr/bin/env python3
"""
Fact Quality Issues Analysis
Identifies specific quality problems in LLM-extracted facts.
"""

import asyncio
import asyncpg
import json
import logging
from collections import Counter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'whisperengine',
    'user': 'whisperengine',
    'password': 'whisperengine'
}

async def analyze_quality_issues():
    """Analyze specific quality issues in the extracted facts."""
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        print("🚨 FACT QUALITY ISSUES ANALYSIS")
        print("=" * 60)
        
        # 1. Partial sentence fragments (common LLM extraction issue)
        print("\n🔍 PARTIAL SENTENCE FRAGMENTS")
        fragments = await conn.fetch("""
            SELECT fe.entity_name, fe.entity_type, ufr.relationship_type, COUNT(*) as count
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE (
                fe.entity_name LIKE '%at %' OR 
                fe.entity_name LIKE '%the %' OR
                fe.entity_name LIKE '%and %' OR
                fe.entity_name LIKE '%or %' OR
                fe.entity_name LIKE '%it %' OR
                fe.entity_name LIKE '%that %' OR
                fe.entity_name LIKE '%when %' OR
                fe.entity_name LIKE '%if %' OR
                fe.entity_name LIKE '%just %' OR
                fe.entity_name LIKE '%like %' OR
                fe.entity_name LIKE '% -' OR
                fe.entity_name LIKE '- %' OR
                LENGTH(fe.entity_name) > 30
            )
            GROUP BY fe.entity_name, fe.entity_type, ufr.relationship_type
            ORDER BY count DESC
            LIMIT 20
        """)
        
        for frag in fragments:
            name = frag['entity_name']
            etype = frag['entity_type']
            rel = frag['relationship_type']
            count = frag['count']
            print(f"  '{name}' ({etype}) - {rel} [{count}x]")
        
        # 2. Weird entity types being used for obvious things
        print("\n🎭 MISCLASSIFIED ENTITIES")
        misclassified = await conn.fetch("""
            SELECT fe.entity_name, fe.entity_type, COUNT(*) as count
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE (
                (fe.entity_name IN ('pizza', 'sushi', 'coffee', 'tea', 'beer', 'wine') AND fe.entity_type != 'food' AND fe.entity_type != 'drink') OR
                (fe.entity_name IN ('hiking', 'programming', 'coding', 'reading', 'writing', 'gaming') AND fe.entity_type != 'hobby') OR
                (fe.entity_name IN ('Tokyo', 'London', 'Paris', 'New York', 'beach', 'mountains') AND fe.entity_type != 'place')
            )
            GROUP BY fe.entity_name, fe.entity_type
            ORDER BY count DESC
        """)
        
        for misc in misclassified:
            name = misc['entity_name']
            wrong_type = misc['entity_type']
            count = misc['count']
            print(f"  '{name}' classified as '{wrong_type}' [{count}x]")
        
        # 3. Generic pronouns being extracted as entities
        print("\n👤 PRONOUN/GENERIC EXTRACTIONS")
        generics = await conn.fetch("""
            SELECT fe.entity_name, fe.entity_type, ufr.relationship_type, COUNT(*) as count
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE fe.entity_name IN ('i', 'you', 'me', 'we', 'they', 'it', 'this', 'that', 'something', 'anything', 'everything')
            GROUP BY fe.entity_name, fe.entity_type, ufr.relationship_type
            ORDER BY count DESC
        """)
        
        for gen in generics:
            name = gen['entity_name']
            etype = gen['entity_type']
            rel = gen['relationship_type']
            count = gen['count']
            print(f"  '{name}' ({etype}) - {rel} [{count}x]")
        
        # 4. Repetitive patterns (sign of extraction issues)
        print("\n🔄 REPETITIVE EXTRACTIONS")
        repetitive = await conn.fetch("""
            SELECT fe.entity_name, COUNT(*) as count, ARRAY_AGG(DISTINCT fe.entity_type) as types
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            GROUP BY fe.entity_name
            HAVING COUNT(*) > 10
            ORDER BY count DESC
            LIMIT 15
        """)
        
        for rep in repetitive:
            name = rep['entity_name']
            count = rep['count']
            types = ', '.join(rep['types'])
            print(f"  '{name}': {count} mentions across types: {types}")
        
        # 5. Strange relationship types
        print("\n🔗 UNUSUAL RELATIONSHIP TYPES")
        unusual_rels = await conn.fetch("""
            SELECT relationship_type, COUNT(*) as count,
                   ARRAY_AGG(DISTINCT fe.entity_name) as example_entities
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE relationship_type NOT IN ('likes', 'dislikes', 'enjoys', 'owns', 'visited', 'wants', 'prefers', 'loves', 'has')
            GROUP BY relationship_type
            ORDER BY count DESC
            LIMIT 20
        """)
        
        for rel in unusual_rels:
            rel_type = rel['relationship_type']
            count = rel['count']
            examples = ', '.join(rel['example_entities'][:3])
            print(f"  '{rel_type}': {count}x (examples: {examples})")
        
        # 6. Entities with special characters (noise indicators)
        print("\n💥 ENTITIES WITH SPECIAL CHARACTERS")
        special_chars = await conn.fetch("""
            SELECT fe.entity_name, fe.entity_type, COUNT(*) as count
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE fe.entity_name ~ '[<>#@\$%\^&\*\(\)\[\]\{\}]'
            GROUP BY fe.entity_name, fe.entity_type
            ORDER BY count DESC
            LIMIT 10
        """)
        
        for char in special_chars:
            name = char['entity_name']
            etype = char['entity_type']
            count = char['count']
            print(f"  '{name}' ({etype}) [{count}x]")
        
        # 7. Very short or very long entity names (likely noise)
        print("\n📏 UNUSUAL ENTITY NAME LENGTHS")
        
        # Very short (1-2 characters)
        short_entities = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE LENGTH(fe.entity_name) <= 2
        """)
        print(f"Very short entities (≤2 chars): {short_entities}")
        
        # Very long (>50 characters)
        long_entities = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE LENGTH(fe.entity_name) > 50
        """)
        print(f"Very long entities (>50 chars): {long_entities}")
        
        # 8. Quality Score Assessment
        print("\n📊 QUALITY ASSESSMENT")
        
        total_facts = await conn.fetchval("SELECT COUNT(*) FROM user_fact_relationships")
        
        # Count various quality issues
        fragment_count = len([f for f in fragments if any(word in f['entity_name'] for word in ['at ', 'the ', 'and ', 'or ', 'it ', 'that ', 'when ', 'if ', 'just ', 'like '])])
        generic_count = sum(gen['count'] for gen in generics)
        special_char_count = sum(char['count'] for char in special_chars)
        
        noise_score = (fragment_count + generic_count + special_char_count) / total_facts * 100
        
        print(f"Total facts: {total_facts}")
        print(f"Fragment-like entities: {fragment_count}")
        print(f"Generic pronoun extractions: {generic_count}")
        print(f"Special character entities: {special_char_count}")
        print(f"Estimated noise percentage: {noise_score:.1f}%")
        
        if noise_score < 5:
            print("✅ GOOD: Low noise level")
        elif noise_score < 15:
            print("⚠️ MODERATE: Some quality issues")
        else:
            print("🚨 HIGH: Significant quality problems - LLM extraction needs tuning")
        
        # 9. Recent extraction samples for debugging
        print(f"\n🔍 RECENT EXTRACTION SAMPLES (Last 10)")
        recent_extractions = await conn.fetch("""
            SELECT 
                fe.entity_name,
                fe.entity_type,
                ufr.relationship_type,
                ufr.confidence,
                ufr.created_at,
                ufr.mentioned_by_character
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            ORDER BY ufr.created_at DESC
            LIMIT 10
        """)
        
        for ext in recent_extractions:
            name = ext['entity_name']
            etype = ext['entity_type']
            rel = ext['relationship_type']
            conf = ext['confidence']
            char = ext['mentioned_by_character']
            created = ext['created_at'].strftime('%m-%d %H:%M')
            
            # Quality indicator
            quality = "🟢"
            if any(word in name for word in ['at ', 'the ', 'and ', 'or ', 'it ', 'that ', 'when ', 'if ', 'just ', 'like ', '- ']):
                quality = "🔴"
            elif name in ['i', 'you', 'me', 'we', 'they', 'it', 'this', 'that']:
                quality = "🔴"
            elif len(name) <= 2 or len(name) > 30:
                quality = "🟡"
            
            print(f"  {quality} [{created}] '{name}' ({etype}) - {rel} ({conf:.2f}) by {char}")
            
    except Exception as e:
        logger.error(f"Analysis error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🔍 WhisperEngine LLM Fact Extraction Quality Issues Analysis")
    asyncio.run(analyze_quality_issues())