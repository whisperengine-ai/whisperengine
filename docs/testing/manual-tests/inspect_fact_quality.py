#!/usr/bin/env python3
"""
Fact Quality Inspection Script
Analyzes the quality of facts stored in PostgreSQL after LLM extraction implementation.
"""

import asyncio
import asyncpg
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection details (matching Docker setup)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'whisperengine',
    'user': 'whisperengine',
    'password': 'whisperengine'
}

async def get_database_connection():
    """Get PostgreSQL connection."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

async def analyze_fact_quality():
    """Analyze the quality of facts stored in the database."""
    conn = await get_database_connection()
    if not conn:
        return
    
    try:
        print("🔍 FACT QUALITY ANALYSIS")
        print("=" * 50)
        
        # 1. Basic fact count and recent activity
        print("\n📊 BASIC STATISTICS")
        
        # Total facts
        total_facts = await conn.fetchval("""
            SELECT COUNT(*) FROM user_fact_relationships
        """)
        print(f"Total facts stored: {total_facts}")
        
        # Unique users with facts
        unique_users = await conn.fetchval("""
            SELECT COUNT(DISTINCT user_id) FROM user_fact_relationships
        """)
        print(f"Users with facts: {unique_users}")
        
        # Recent facts (last 7 days)
        recent_facts = await conn.fetchval("""
            SELECT COUNT(*) FROM user_fact_relationships 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        print(f"Recent facts (last 7 days): {recent_facts}")
        
        # 2. Entity type distribution
        print("\n📋 ENTITY TYPE DISTRIBUTION")
        entity_types = await conn.fetch("""
            SELECT fe.entity_type, COUNT(*) as count
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            GROUP BY fe.entity_type
            ORDER BY count DESC
        """)
        
        for row in entity_types:
            print(f"  {row['entity_type']}: {row['count']}")
        
        # 3. Relationship type distribution
        print("\n🔗 RELATIONSHIP TYPE DISTRIBUTION")
        relationship_types = await conn.fetch("""
            SELECT relationship_type, COUNT(*) as count
            FROM user_fact_relationships
            GROUP BY relationship_type
            ORDER BY count DESC
        """)
        
        for row in relationship_types:
            print(f"  {row['relationship_type']}: {row['count']}")
        
        # 4. Confidence distribution
        print("\n📈 CONFIDENCE DISTRIBUTION")
        confidence_stats = await conn.fetchrow("""
            SELECT 
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                COUNT(CASE WHEN confidence >= 0.8 THEN 1 END) as high_confidence,
                COUNT(CASE WHEN confidence >= 0.5 AND confidence < 0.8 THEN 1 END) as medium_confidence,
                COUNT(CASE WHEN confidence < 0.5 THEN 1 END) as low_confidence
            FROM user_fact_relationships
        """)
        
        print(f"  Average confidence: {confidence_stats['avg_confidence']:.3f}")
        print(f"  Range: {confidence_stats['min_confidence']:.3f} - {confidence_stats['max_confidence']:.3f}")
        print(f"  High confidence (≥0.8): {confidence_stats['high_confidence']}")
        print(f"  Medium confidence (0.5-0.8): {confidence_stats['medium_confidence']}")
        print(f"  Low confidence (<0.5): {confidence_stats['low_confidence']}")
        
        # 5. Recent sample facts for quality inspection
        print("\n🔎 RECENT FACTS SAMPLE (Last 20)")
        print("-" * 60)
        recent_samples = await conn.fetch("""
            SELECT 
                fe.entity_name,
                fe.entity_type,
                ufr.relationship_type,
                ufr.confidence,
                ufr.emotional_context,
                ufr.mentioned_by_character,
                ufr.created_at
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            ORDER BY ufr.created_at DESC
            LIMIT 20
        """)
        
        for fact in recent_samples:
            entity = fact['entity_name']
            entity_type = fact['entity_type']
            relationship = fact['relationship_type']
            confidence = fact['confidence']
            emotion = fact['emotional_context'] or 'N/A'
            character = fact['mentioned_by_character'] or 'N/A'
            created = fact['created_at'].strftime('%Y-%m-%d %H:%M')
            
            print(f"  [{created}] {entity} ({entity_type}) - {relationship} (conf: {confidence:.2f})")
            print(f"    Emotion: {emotion} | Character: {character}")
        
        # 6. Check for potential noise patterns
        print("\n⚠️ POTENTIAL NOISE ANALYSIS")
        
        # Very low confidence facts
        low_conf_count = await conn.fetchval("""
            SELECT COUNT(*) FROM user_fact_relationships 
            WHERE confidence < 0.3
        """)
        print(f"Very low confidence facts (<0.3): {low_conf_count}")
        
        # Generic entity names (potential noise)
        generic_entities = await conn.fetch("""
            SELECT fe.entity_name, COUNT(*) as count
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE fe.entity_name IN ('you', 'i', 'me', 'this', 'that', 'it', 'thing', 'stuff')
            GROUP BY fe.entity_name
            ORDER BY count DESC
        """)
        
        if generic_entities:
            print("Generic/noisy entity names found:")
            for entity in generic_entities:
                print(f"  '{entity['entity_name']}': {entity['count']} occurrences")
        else:
            print("✅ No obvious generic entity names found")
        
        # 7. Character-specific analysis
        print("\n🎭 CHARACTER-SPECIFIC ANALYSIS")
        character_stats = await conn.fetch("""
            SELECT 
                mentioned_by_character,
                COUNT(*) as fact_count,
                AVG(confidence) as avg_confidence
            FROM user_fact_relationships
            WHERE mentioned_by_character IS NOT NULL
            GROUP BY mentioned_by_character
            ORDER BY fact_count DESC
        """)
        
        for char_stat in character_stats:
            character = char_stat['mentioned_by_character']
            count = char_stat['fact_count']
            avg_conf = char_stat['avg_confidence']
            print(f"  {character}: {count} facts (avg conf: {avg_conf:.3f})")
        
        # 8. User fact density analysis
        print("\n👥 USER FACT DENSITY")
        user_density = await conn.fetch("""
            SELECT 
                COUNT(*) as fact_count,
                COUNT(DISTINCT user_id) as user_count
            FROM (
                SELECT user_id, COUNT(*) as facts_per_user
                FROM user_fact_relationships
                GROUP BY user_id
                HAVING COUNT(*) >= 5
            ) t
        """)
        
        users_with_many_facts = await conn.fetchval("""
            SELECT COUNT(DISTINCT user_id) 
            FROM user_fact_relationships
            GROUP BY user_id
            HAVING COUNT(*) >= 5
        """)
        
        if users_with_many_facts:
            print(f"Users with 5+ facts: {users_with_many_facts}")
        else:
            print("No users with 5+ facts yet")
        
        # 9. Top entities across all users
        print("\n🏆 TOP ENTITIES (Most Mentioned)")
        top_entities = await conn.fetch("""
            SELECT 
                fe.entity_name,
                fe.entity_type,
                COUNT(*) as mention_count,
                AVG(ufr.confidence) as avg_confidence
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            GROUP BY fe.entity_name, fe.entity_type
            HAVING COUNT(*) > 1
            ORDER BY mention_count DESC
            LIMIT 10
        """)
        
        for entity in top_entities:
            name = entity['entity_name']
            etype = entity['entity_type']
            count = entity['mention_count']
            avg_conf = entity['avg_confidence']
            print(f"  {name} ({etype}): {count} mentions (avg conf: {avg_conf:.3f})")
        
        print("\n" + "=" * 50)
        print("✅ Fact quality analysis complete!")
        
        # Summary assessment
        if total_facts == 0:
            print("\n🚨 NO FACTS FOUND - LLM extraction may not be working")
        elif total_facts < 10:
            print(f"\n⚠️ LOW FACT COUNT ({total_facts}) - May need more user activity")
        else:
            print(f"\n✅ GOOD FACT COUNT ({total_facts}) - LLM extraction appears active")
            
            # Quality indicators
            if confidence_stats['avg_confidence'] > 0.7:
                print("✅ HIGH AVERAGE CONFIDENCE - Quality looks good")
            elif confidence_stats['avg_confidence'] > 0.5:
                print("⚠️ MEDIUM AVERAGE CONFIDENCE - Quality acceptable")
            else:
                print("🚨 LOW AVERAGE CONFIDENCE - Quality concerns")
                
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
    finally:
        await conn.close()

async def sample_raw_facts_for_inspection():
    """Get raw sample facts for manual quality inspection."""
    conn = await get_database_connection()
    if not conn:
        return
        
    try:
        print("\n\n" + "=" * 60)
        print("📝 RAW FACT SAMPLES FOR MANUAL INSPECTION")
        print("=" * 60)
        
        # Get diverse sample facts
        sample_facts = await conn.fetch("""
            SELECT 
                ufr.user_id,
                fe.entity_name,
                fe.entity_type,
                fe.category,
                ufr.relationship_type,
                ufr.confidence,
                ufr.emotional_context,
                ufr.mentioned_by_character,
                ufr.source_conversation_id,
                ufr.context_metadata,
                ufr.created_at
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            ORDER BY RANDOM()
            LIMIT 15
        """)
        
        for i, fact in enumerate(sample_facts, 1):
            print(f"\n--- Sample {i} ---")
            print(f"Entity: '{fact['entity_name']}' ({fact['entity_type']})")
            print(f"Relationship: {fact['relationship_type']}")
            print(f"Confidence: {fact['confidence']:.3f}")
            print(f"Emotion: {fact['emotional_context'] or 'N/A'}")
            print(f"Character: {fact['mentioned_by_character']}")
            print(f"Created: {fact['created_at']}")
            
            # Try to parse metadata if present
            if fact['context_metadata']:
                try:
                    metadata = json.loads(fact['context_metadata']) if isinstance(fact['context_metadata'], str) else fact['context_metadata']
                    print(f"Metadata: {metadata}")
                except:
                    print(f"Metadata: {fact['context_metadata']}")
                    
    except Exception as e:
        logger.error(f"Error getting samples: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🔍 WhisperEngine Fact Quality Inspector")
    print("Analyzing LLM-extracted facts in PostgreSQL database...")
    
    asyncio.run(analyze_fact_quality())
    asyncio.run(sample_raw_facts_for_inspection())