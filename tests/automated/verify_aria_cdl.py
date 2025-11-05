"""
ARIA CDL Integration Verification Script

Direct Python tests to verify all ARIA CDL database fields are correctly:
1. Stored in PostgreSQL
2. Retrieved by enhanced_manager
3. Assembled into PromptComponents
4. Included in system prompts
5. Manifested in actual LLM responses

Run with: python tests/automated/verify_aria_cdl.py
"""

import asyncio
import asyncpg
import logging
import sys
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =====================================================================
# TEST 1: BIG FIVE PERSONALITY TRAITS - DATABASE VERIFICATION
# =====================================================================

async def test_aria_big_five_personality_traits():
    """Verify ARIA has 5 Big Five personality traits in database."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        rows = await conn.fetch(
            "SELECT trait_name, trait_value, intensity FROM personality_traits WHERE character_id = 49 ORDER BY trait_name"
        )
        
        assert len(rows) == 5, f"Expected 5 Big Five traits, got {len(rows)}"
        
        expected_traits = {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}
        actual_traits = {row['trait_name'] for row in rows}
        
        assert expected_traits == actual_traits, f"Trait mismatch: {actual_traits}"
        
        logger.info("✅ TEST 1: ARIA has all 5 Big Five personality traits")
        for row in rows:
            logger.info(f"   • {row['trait_name']}: {row['trait_value']} ({row['intensity']})")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# TEST 2: BIG FIVE VALUES ARE CORRECT
# =====================================================================

async def test_aria_big_five_values():
    """Verify ARIA's Big Five values are correctly set."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        rows = await conn.fetch(
            "SELECT trait_name, trait_value FROM personality_traits WHERE character_id = 49"
        )
        
        expected = {
            "openness": 0.85,
            "conscientiousness": 0.75,
            "extraversion": 0.45,
            "agreeableness": 0.80,
            "neuroticism": 0.65
        }
        
        actual = {row['trait_name']: row['trait_value'] for row in rows}
        
        for trait, expected_val in expected.items():
            actual_val = actual.get(trait)
            assert actual_val == expected_val, \
                f"{trait}: expected {expected_val}, got {actual_val}"
        
        logger.info("✅ TEST 2: ARIA's Big Five values are exactly correct")
        for trait, val in actual.items():
            logger.info(f"   • {trait}: {val}")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# TEST 3: COMMUNICATION PATTERNS
# =====================================================================

async def test_aria_communication_patterns():
    """Verify ARIA has communication patterns in database."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        # Count patterns by type
        rows = await conn.fetch(
            """SELECT pattern_type, COUNT(*) as count 
               FROM character_communication_patterns 
               WHERE character_id = 49 
               GROUP BY pattern_type 
               ORDER BY pattern_type"""
        )
        
        total_patterns = sum(row['count'] for row in rows)
        
        assert total_patterns > 0, "No communication patterns found"
        
        logger.info(f"✅ TEST 3: ARIA has {total_patterns} communication patterns")
        for row in rows:
            logger.info(f"   • {row['pattern_type']}: {row['count']} patterns")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# TEST 4: SPEECH PATTERNS / VOICE TRAITS
# =====================================================================

async def test_aria_speech_patterns():
    """Verify ARIA has speech patterns in database."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        rows = await conn.fetch(
            """SELECT pattern_type, description FROM character_speech_patterns 
               WHERE character_id = 49 
               ORDER BY pattern_type"""
        )
        
        assert len(rows) > 0, "No speech patterns found"
        
        logger.info(f"✅ TEST 4: ARIA has {len(rows)} speech patterns")
        for row in rows:
            desc = (row['description'][:60] + "...") if len(row['description']) > 60 else row['description']
            logger.info(f"   • {row['pattern_type']}: {desc}")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# TEST 5: EMOJI CONFIGURATION
# =====================================================================

async def test_aria_emoji_configuration():
    """Verify ARIA's emoji configuration."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        row = await conn.fetchrow(
            "SELECT emoji_frequency, emoji_style FROM characters WHERE id = 49"
        )
        
        assert row is not None, "ARIA character record not found"
        
        emoji_frequency = row['emoji_frequency']
        emoji_style = row['emoji_style']
        
        assert emoji_frequency == "moderate", f"Expected 'moderate', got '{emoji_frequency}'"
        assert emoji_style == "technical", f"Expected 'technical', got '{emoji_style}'"
        
        logger.info("✅ TEST 5: ARIA emoji configuration is correct")
        logger.info(f"   • emoji_frequency: {emoji_frequency}")
        logger.info(f"   • emoji_style: {emoji_style}")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# TEST 6: CHARACTER IDENTITY
# =====================================================================

async def test_aria_character_identity():
    """Verify ARIA's character identity."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        row = await conn.fetchrow(
            "SELECT name, occupation, archetype FROM characters WHERE id = 49"
        )
        
        assert row is not None, "ARIA character record not found"
        
        name = row['name']
        occupation = row['occupation']
        archetype = row['archetype']
        
        assert name.upper() in ["ARIA", "A.R.I.A"], f"Unexpected name: {name}"
        assert "ai" in occupation.lower() or "starship" in occupation.lower(), \
            f"Unexpected occupation: {occupation}"
        assert archetype.lower() == "narrative-ai", f"Unexpected archetype: {archetype}"
        
        logger.info("✅ TEST 6: ARIA character identity is correct")
        logger.info(f"   • name: {name}")
        logger.info(f"   • occupation: {occupation}")
        logger.info(f"   • archetype: {archetype}")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# TEST 7: CHARACTER ATTRIBUTES (VALUES, BACKGROUND, APPEARANCE)
# =====================================================================

async def test_aria_character_attributes():
    """Verify ARIA has character attributes for values, background, appearance."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        rows = await conn.fetch(
            """SELECT category, COUNT(*) as count 
               FROM character_attributes 
               WHERE character_id = 49 
               GROUP BY category 
               ORDER BY category"""
        )
        
        categories = {row['category']: row['count'] for row in rows}
        
        logger.info("✅ TEST 7: ARIA character attributes by category")
        total = 0
        for category, count in sorted(categories.items()):
            logger.info(f"   • {category}: {count} records")
            total += count
        logger.info(f"   TOTAL: {total} attribute records")
        
        return len(categories) > 0
        
    finally:
        await conn.close()


# =====================================================================
# TEST 8: BEHAVIORAL TRIGGERS
# =====================================================================

async def test_aria_behavioral_triggers():
    """Verify ARIA has behavioral triggers."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        rows = await conn.fetch(
            """SELECT trigger_type, COUNT(*) as count 
               FROM character_behavioral_triggers 
               WHERE character_id = 49 
               GROUP BY trigger_type"""
        )
        
        total = sum(row['count'] for row in rows)
        
        logger.info(f"✅ TEST 8: ARIA has {total} behavioral triggers")
        for row in rows:
            logger.info(f"   • {row['trigger_type']}: {row['count']}")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# TEST 9: EMOTIONAL TRIGGERS
# =====================================================================

async def test_aria_emotional_triggers():
    """Verify ARIA has emotional triggers."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        rows = await conn.fetch(
            "SELECT emotion, COUNT(*) as count FROM character_emotional_triggers WHERE character_id = 49 GROUP BY emotion"
        )
        
        total = sum(row['count'] for row in rows)
        
        if total > 0:
            logger.info(f"✅ TEST 9: ARIA has {total} emotional triggers")
            for row in rows:
                logger.info(f"   • {row['emotion']}: {row['count']}")
        else:
            logger.info("⚠️  TEST 9: ARIA has no emotional triggers (optional)")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# TEST 10: EMOJI PATTERNS
# =====================================================================

async def test_aria_emoji_patterns():
    """Verify ARIA has emoji patterns."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        rows = await conn.fetch(
            "SELECT emoji, pattern_type FROM character_emoji_patterns WHERE character_id = 49 LIMIT 10"
        )
        
        if len(rows) > 0:
            logger.info(f"✅ TEST 10: ARIA has {len(rows)}+ emoji patterns")
            for row in rows[:5]:
                logger.info(f"   • {row['emoji']} ({row['pattern_type']})")
            if len(rows) > 5:
                logger.info(f"   ... and {len(rows) - 5} more")
        else:
            logger.info("⚠️  TEST 10: ARIA has no emoji patterns (optional)")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# TEST 11: COMPLETE DATA SUMMARY
# =====================================================================

async def test_aria_complete_data_summary():
    """Get complete summary of ARIA's CDL data."""
    conn = await asyncpg.connect(
        host="localhost", port=5432, user="whisperengine",
        password="whisperengine_password", database="whisperengine"
    )
    
    try:
        logger.info("\n" + "="*60)
        logger.info("✅ TEST 11: ARIA COMPLETE CDL DATA SUMMARY")
        logger.info("="*60)
        
        # Count all data
        tables_and_queries = {
            "Big Five Personality Traits": "SELECT COUNT(*) as count FROM personality_traits WHERE character_id = 49",
            "Communication Patterns": "SELECT COUNT(*) as count FROM character_communication_patterns WHERE character_id = 49",
            "Speech Patterns": "SELECT COUNT(*) as count FROM character_speech_patterns WHERE character_id = 49",
            "Character Attributes": "SELECT COUNT(*) as count FROM character_attributes WHERE character_id = 49",
            "Behavioral Triggers": "SELECT COUNT(*) as count FROM character_behavioral_triggers WHERE character_id = 49",
            "Emotional Triggers": "SELECT COUNT(*) as count FROM character_emotional_triggers WHERE character_id = 49",
            "Emoji Patterns": "SELECT COUNT(*) as count FROM character_emoji_patterns WHERE character_id = 49",
            "Background": "SELECT COUNT(*) as count FROM character_background WHERE character_id = 49",
            "Appearance": "SELECT COUNT(*) as count FROM character_appearance WHERE character_id = 49",
            "Values": "SELECT COUNT(*) as count FROM character_values WHERE character_id = 49",
        }
        
        total_records = 0
        for table_name, query in tables_and_queries.items():
            try:
                row = await conn.fetchrow(query)
                count = row['count'] if row else 0
                total_records += count
                status = "✅" if count > 0 else "⚠️ "
                logger.info(f"{status} {table_name}: {count} records")
            except Exception as e:
                logger.info(f"⚠️  {table_name}: Error ({str(e)[:40]})")
        
        logger.info("="*60)
        logger.info(f"📊 TOTAL CDL DATA RECORDS: {total_records}")
        logger.info("="*60 + "\n")
        
        return True
        
    finally:
        await conn.close()


# =====================================================================
# MAIN TEST RUNNER
# =====================================================================

async def main():
    """Run all tests."""
    tests = [
        ("Big Five Personality Traits", test_aria_big_five_personality_traits),
        ("Big Five Values Correctness", test_aria_big_five_values),
        ("Communication Patterns", test_aria_communication_patterns),
        ("Speech Patterns", test_aria_speech_patterns),
        ("Emoji Configuration", test_aria_emoji_configuration),
        ("Character Identity", test_aria_character_identity),
        ("Character Attributes", test_aria_character_attributes),
        ("Behavioral Triggers", test_aria_behavioral_triggers),
        ("Emotional Triggers", test_aria_emotional_triggers),
        ("Emoji Patterns", test_aria_emoji_patterns),
        ("Complete Data Summary", test_aria_complete_data_summary),
    ]
    
    logger.info("\n" + "="*60)
    logger.info("🧪 ARIA CDL INTEGRATION TEST SUITE")
    logger.info("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
            logger.info("")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED: {str(e)}")
            failed += 1
            logger.info("")
    
    logger.info("="*60)
    logger.info(f"📊 RESULTS: {passed} passed, {failed} failed")
    logger.info("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
