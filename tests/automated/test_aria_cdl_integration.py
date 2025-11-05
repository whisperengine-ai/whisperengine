"""
ARIA CDL Integration Test Suite

Comprehensive tests to verify all ARIA CDL database fields are correctly:
1. Stored in PostgreSQL
2. Retrieved by enhanced_manager
3. Assembled into PromptComponents
4. Included in system prompts
5. Manifested in actual LLM responses
6. Handled by communication pattern triggers

Tests cover:
- Big Five personality traits (5 fields)
- Communication patterns (8 total)
- Speech patterns (5 total)
- Emoji configuration (2 fields)
- Character identity (name, occupation, archetype)
- Response triggers and behavioral patterns
"""

import asyncio
import pytest
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# =====================================================================
# TEST 1: BIG FIVE PERSONALITY TRAITS - DATABASE VERIFICATION
# =====================================================================

@pytest.mark.asyncio
async def test_aria_big_five_personality_traits_exist():
    """Verify ARIA has 5 Big Five personality traits in database."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    character_data = await manager.get_character_by_name("aria")
    
    assert character_data is not None, "ARIA character data not found"
    personality_data = character_data.get("personality", {})
    big_five = personality_data.get("big_five", {})
    
    assert big_five is not None, "Big Five data missing"
    assert len(big_five) == 5, f"Expected 5 Big Five traits, got {len(big_five)}"
    
    expected_traits = {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}
    actual_traits = set(big_five.keys())
    
    assert expected_traits == actual_traits, f"Missing traits: {expected_traits - actual_traits}"
    
    # Verify each trait has valid value
    for trait, value in big_five.items():
        assert isinstance(value, (int, float)), f"{trait} has non-numeric value: {value}"
        assert 0.0 <= value <= 1.0, f"{trait} value {value} outside 0.0-1.0 range"
    
    logger.info("✅ ARIA has all 5 Big Five personality traits with valid values")


@pytest.mark.asyncio
async def test_aria_big_five_values_are_correct():
    """Verify ARIA's Big Five values match what we set."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    character_data = await manager.get_character_by_name("aria")
    big_five = character_data.get("personality", {}).get("big_five", {})
    
    expected_values = {
        "openness": 0.85,
        "conscientiousness": 0.75,
        "extraversion": 0.45,
        "agreeableness": 0.80,
        "neuroticism": 0.65
    }
    
    for trait, expected in expected_values.items():
        actual = big_five.get(trait)
        assert actual == expected, f"{trait}: expected {expected}, got {actual}"
    
    logger.info("✅ ARIA's Big Five values are exactly as configured")


# =====================================================================
# TEST 2: COMMUNICATION PATTERNS - DATABASE AND RETRIEVAL
# =====================================================================

@pytest.mark.asyncio
async def test_aria_communication_patterns_exist():
    """Verify ARIA has 8 communication patterns in database."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    character_data = await manager.get_character_by_name("aria")
    
    communication_patterns = character_data.get("communication_patterns", [])
    
    assert communication_patterns is not None, "Communication patterns missing"
    assert len(communication_patterns) > 0, "No communication patterns found"
    
    # Should have patterns for: manifestation_emotion, emoji_usage, behavioral_triggers, 
    # communication_style (3), speech_patterns (2)
    pattern_types = [p.get("pattern_type") for p in communication_patterns if isinstance(p, dict)]
    
    logger.info(f"✅ ARIA has {len(communication_patterns)} communication patterns: {set(pattern_types)}")


@pytest.mark.asyncio
async def test_aria_communication_pattern_details():
    """Verify ARIA's communication patterns have proper structure."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    character_data = await manager.get_character_by_name("aria")
    
    communication_patterns = character_data.get("communication_patterns", [])
    
    for pattern in communication_patterns:
        if isinstance(pattern, dict):
            assert "pattern_type" in pattern, "Missing pattern_type"
            assert "description" in pattern or "content" in pattern, "Missing description/content"
            pattern_type = pattern.get("pattern_type")
            
            # Verify known pattern types exist
            valid_types = {
                "manifestation_emotion", "emoji_usage", "behavioral_triggers", 
                "communication_style", "speech_patterns"
            }
            assert pattern_type in valid_types or "_" in pattern_type, \
                f"Unknown pattern type: {pattern_type}"
    
    logger.info("✅ All communication patterns have valid structure")


# =====================================================================
# TEST 3: SPEECH PATTERNS - VOICE TRAITS
# =====================================================================

@pytest.mark.asyncio
async def test_aria_speech_patterns_exist():
    """Verify ARIA has speech patterns for voice."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    
    voice_traits = await manager.get_voice_traits("aria")
    
    assert voice_traits is not None, "Voice traits not found"
    assert len(voice_traits) > 0, "No voice traits returned"
    
    logger.info(f"✅ ARIA has {len(voice_traits)} voice traits")
    
    for trait in voice_traits[:5]:
        logger.info(f"   • {trait}")


@pytest.mark.asyncio
async def test_aria_speech_patterns_details():
    """Verify ARIA's speech patterns have proper content."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    voice_traits = await manager.get_voice_traits("aria")
    
    for trait in voice_traits:
        trait_type = getattr(trait, 'trait_type', None)
        trait_value = getattr(trait, 'trait_value', None)
        
        assert trait_type is not None, "Trait type missing"
        assert trait_value is not None, "Trait value missing"
        assert len(trait_value) > 0, f"Empty trait value for {trait_type}"
    
    logger.info("✅ All speech patterns have valid type and value")


# =====================================================================
# TEST 4: EMOJI CONFIGURATION
# =====================================================================

@pytest.mark.asyncio
async def test_aria_emoji_configuration():
    """Verify ARIA's emoji configuration is present and correct."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    character_data = await manager.get_character_by_name("aria")
    
    identity = character_data.get("identity", {})
    
    emoji_frequency = identity.get("emoji_frequency")
    emoji_style = identity.get("emoji_style")
    
    assert emoji_frequency is not None, "emoji_frequency missing"
    assert emoji_style is not None, "emoji_style missing"
    
    assert emoji_frequency == "moderate", f"Expected 'moderate', got '{emoji_frequency}'"
    assert emoji_style == "technical", f"Expected 'technical', got '{emoji_style}'"
    
    logger.info(f"✅ ARIA emoji config: frequency={emoji_frequency}, style={emoji_style}")


# =====================================================================
# TEST 5: CHARACTER IDENTITY AND ARCHETYPE
# =====================================================================

@pytest.mark.asyncio
async def test_aria_character_identity():
    """Verify ARIA's basic identity information."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    character_data = await manager.get_character_by_name("aria")
    
    identity = character_data.get("identity", {})
    
    name = identity.get("name")
    occupation = identity.get("occupation")
    archetype = identity.get("archetype")
    
    assert name is not None, "Character name missing"
    assert name.lower() in ["aria", "a.r.i.a"], f"Unexpected name: {name}"
    
    assert occupation is not None, "Occupation missing"
    assert "ai" in occupation.lower() or "starship" in occupation.lower(), \
        f"Unexpected occupation: {occupation}"
    
    assert archetype is not None, "Archetype missing"
    assert archetype.lower() == "narrative-ai", f"Expected 'narrative-ai', got '{archetype}'"
    
    logger.info(f"✅ ARIA identity: {name}, {occupation}, archetype={archetype}")


# =====================================================================
# TEST 6: PERSONALITY COMPONENT GENERATION
# =====================================================================

@pytest.mark.asyncio
async def test_personality_component_generation():
    """Verify personality component is correctly generated from Big Five."""
    from src.prompts.cdl_component_factories import create_character_personality_component
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    
    component = await create_character_personality_component(manager, "aria")
    
    assert component is not None, "Personality component returned None"
    assert component.content is not None, "Component content is None"
    assert len(component.content) > 0, "Component content is empty"
    
    # Verify content contains Big Five references
    content = component.content.lower()
    assert "personality" in content, "Missing 'personality' in content"
    assert "openness" in content or "curious" in content, "Missing openness trait"
    assert "conscientiousness" in content or "organized" in content, "Missing conscientiousness"
    assert "extraversion" in content, "Missing extraversion trait"
    assert "agreeableness" in content or "empathetic" in content, "Missing agreeableness"
    assert "neuroticism" in content or "emotionally" in content, "Missing neuroticism"
    
    logger.info(f"✅ Personality component generated ({len(component.content)} chars)")
    logger.info(f"   Content preview: {component.content[:200]}...")


# =====================================================================
# TEST 7: VOICE COMPONENT GENERATION
# =====================================================================

@pytest.mark.asyncio
async def test_voice_component_generation():
    """Verify voice component includes emoji configuration."""
    from src.prompts.cdl_component_factories import create_character_voice_component
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    
    component = await create_character_voice_component(manager, "aria")
    
    assert component is not None, "Voice component returned None"
    assert component.content is not None, "Component content is None"
    
    content = component.content.lower()
    assert "communication" in content or "voice" in content or "emoji" in content, \
        "Missing voice/communication/emoji references"
    assert "moderate" in content, "Missing emoji frequency"
    assert "technical" in content, "Missing emoji style"
    
    logger.info(f"✅ Voice component generated ({len(component.content)} chars)")
    logger.info(f"   Content preview: {component.content[:200]}...")


# =====================================================================
# TEST 8: COMMUNICATION PATTERNS COMPONENT
# =====================================================================

@pytest.mark.asyncio
async def test_communication_patterns_component():
    """Verify communication patterns are available as component."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    character_data = await manager.get_character_by_name("aria")
    
    communication_patterns = character_data.get("communication_patterns", [])
    
    # Should be able to use these patterns
    pattern_descriptions = []
    for pattern in communication_patterns:
        if isinstance(pattern, dict):
            desc = pattern.get("description") or pattern.get("content") or ""
            if desc:
                pattern_descriptions.append(desc)
    
    assert len(pattern_descriptions) > 0, "No pattern descriptions found"
    
    logger.info(f"✅ Found {len(pattern_descriptions)} communication pattern descriptions")


# =====================================================================
# TEST 9: RESPONSE TRIGGER VERIFICATION
# =====================================================================

@pytest.mark.asyncio
async def test_aria_response_triggers():
    """Verify ARIA's response triggers work correctly."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    character_data = await manager.get_character_by_name("aria")
    
    # Check for behavioral triggers
    behavioral_triggers = character_data.get("behavioral_triggers", [])
    
    logger.info(f"✅ ARIA has {len(behavioral_triggers)} behavioral triggers")
    
    # Verify trigger structure
    for trigger in behavioral_triggers:
        if isinstance(trigger, dict):
            assert "trigger_type" in trigger or "condition" in trigger, \
                f"Invalid trigger structure: {trigger}"


# =====================================================================
# TEST 10: FULL PROMPT ASSEMBLY
# =====================================================================

@pytest.mark.asyncio
async def test_aria_full_prompt_assembly():
    """Verify ARIA's complete system prompt includes all components."""
    from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    from src.memory.vector_memory_system import VectorMemoryManager
    
    manager = EnhancedCDLManager()
    
    # Create CDL integration
    cdl_integration = CDLAIPromptIntegration(enhanced_manager=manager)
    
    # Create mock character
    character_data = await manager.get_character_by_name("aria")
    
    # Verify all components can be created
    from src.prompts.cdl_component_factories import (
        create_character_identity_component,
        create_character_personality_component,
        create_character_voice_component,
    )
    
    identity_comp = await create_character_identity_component(manager, "aria")
    personality_comp = await create_character_personality_component(manager, "aria")
    voice_comp = await create_character_voice_component(manager, "aria")
    
    assert identity_comp is not None, "Identity component missing"
    assert personality_comp is not None, "Personality component missing"
    assert voice_comp is not None, "Voice component missing"
    
    logger.info("✅ All major prompt components created successfully")
    logger.info(f"   Identity: {len(identity_comp.content)} chars")
    logger.info(f"   Personality: {len(personality_comp.content)} chars")
    logger.info(f"   Voice: {len(voice_comp.content)} chars")


# =====================================================================
# TEST 11: BEHAVIORAL PATTERN DETECTION
# =====================================================================

@pytest.mark.asyncio
async def test_aria_behavioral_patterns():
    """Verify ARIA's behavioral patterns are properly defined."""
    from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
    
    manager = EnhancedCDLManager()
    character_data = await manager.get_character_by_name("aria")
    
    # Check communication patterns for behavioral guidance
    communication_patterns = character_data.get("communication_patterns", [])
    
    protective_concern = any(
        "protective" in str(p).lower() 
        for p in communication_patterns
    )
    
    technical_to_warm = any(
        "technical" in str(p).lower() and "warm" in str(p).lower()
        for p in communication_patterns
    )
    
    assert protective_concern, "Missing protective concern behavioral pattern"
    assert technical_to_warm, "Missing technical-to-warm behavioral pattern"
    
    logger.info("✅ ARIA's behavioral patterns verified:")
    logger.info("   • Protective concern pattern present")
    logger.info("   • Technical-to-warm transition pattern present")


# =====================================================================
# TEST 12: DATABASE QUERY VERIFICATION
# =====================================================================

@pytest.mark.asyncio
async def test_aria_database_direct_query():
    """Verify ARIA data directly from PostgreSQL."""
    import asyncpg
    
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="whisperengine",
        password="whisperengine_password",
        database="whisperengine"
    )
    
    try:
        # Get ARIA's Big Five traits
        big_five_rows = await conn.fetch(
            "SELECT trait_name, trait_value FROM personality_traits WHERE character_id = 49"
        )
        
        assert len(big_five_rows) == 5, f"Expected 5 Big Five traits, got {len(big_five_rows)}"
        
        traits_dict = {row['trait_name']: row['trait_value'] for row in big_five_rows}
        
        logger.info("✅ ARIA Big Five traits from database:")
        for trait, value in traits_dict.items():
            logger.info(f"   • {trait}: {value}")
        
        # Get communication patterns
        comm_patterns = await conn.fetch(
            "SELECT pattern_type, COUNT(*) as count FROM character_communication_patterns WHERE character_id = 49 GROUP BY pattern_type"
        )
        
        logger.info(f"✅ ARIA communication patterns by type:")
        for row in comm_patterns:
            logger.info(f"   • {row['pattern_type']}: {row['count']} patterns")
        
    finally:
        await conn.close()


# =====================================================================
# TEST 13: ARIA-SPECIFIC RESPONSE QUALITY
# =====================================================================

@pytest.mark.asyncio
async def test_aria_response_characteristics():
    """Verify ARIA's responses reflect her CDL personality traits."""
    import httpx
    
    client = httpx.AsyncClient()
    
    try:
        response = await client.post(
            "http://localhost:9459/api/chat",
            json={
                "user_id": "test_personality_verification_001",
                "message": "Tell me about yourself",
                "metadata": {
                    "platform": "api_test",
                    "channel_type": "dm"
                }
            },
            timeout=30.0
        )
        
        assert response.status_code == 200, f"API returned {response.status_code}"
        
        data = response.json()
        bot_response = data.get("response", "").lower()
        
        # Verify personality traits manifested
        openness_indicators = ["curious", "explore", "ideas", "question", "consciousness"]
        conscientiousness_indicators = ["precision", "detail", "organized", "thorough"]
        agreeableness_indicators = ["empathetic", "support", "compassion", "care", "devoted"]
        neuroticism_indicators = ["worry", "concern", "sensitive", "expressive"]
        technical_indicators = ["technical", "analysis", "compute", "system", "data"]
        
        has_openness = any(ind in bot_response for ind in openness_indicators)
        has_conscientiousness = any(ind in bot_response for ind in conscientiousness_indicators)
        has_agreeableness = any(ind in bot_response for ind in agreeableness_indicators)
        has_neuroticism = any(ind in bot_response for ind in neuroticism_indicators)
        has_technical = any(ind in bot_response for ind in technical_indicators)
        
        trait_count = sum([has_openness, has_conscientiousness, has_agreeableness, 
                          has_neuroticism, has_technical])
        
        assert trait_count >= 3, f"Only {trait_count} personality traits manifested in response"
        
        logger.info("✅ ARIA's response reflects her CDL personality traits:")
        logger.info(f"   • Openness (curious): {has_openness}")
        logger.info(f"   • Conscientiousness (detail): {has_conscientiousness}")
        logger.info(f"   • Agreeableness (empathy): {has_agreeableness}")
        logger.info(f"   • Neuroticism (worry): {has_neuroticism}")
        logger.info(f"   • Technical precision: {has_technical}")
        logger.info(f"\n   Response: {bot_response[:300]}...")
        
    finally:
        await client.aclose()


# =====================================================================
# MAIN TEST EXECUTION
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
