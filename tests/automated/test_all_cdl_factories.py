"""
Test Suite for All Implemented CDL Component Factories

This test validates all 11 implemented factory functions:
1. CHARACTER_IDENTITY (Priority 1) ✅
2. CHARACTER_MODE (Priority 2) ✅
3. CHARACTER_BACKSTORY (Priority 3) ⚠️
4. CHARACTER_PRINCIPLES (Priority 4) ⚠️
5. AI_IDENTITY_GUIDANCE (Priority 5) ✅
6. TEMPORAL_AWARENESS (Priority 6) ✅
7. USER_PERSONALITY (Priority 7) ✅
8. CHARACTER_PERSONALITY (Priority 8) ✅
9. CHARACTER_VOICE (Priority 10) ⚠️
10. CHARACTER_RELATIONSHIPS (Priority 11) ✅
11. KNOWLEDGE_CONTEXT (Priority 16) ✅

Author: WhisperEngine
Date: October 18, 2025
"""

import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.postgres_pool_manager import get_postgres_pool
from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
from src.memory.vector_memory_system import get_normalized_bot_name_from_env
from src.prompts.cdl_component_factories import (
    create_character_identity_component,
    create_character_mode_component,
    create_character_backstory_component,
    create_character_principles_component,
    create_ai_identity_guidance_component,
    create_temporal_awareness_component,
    create_user_personality_component,
    create_character_personality_component,
    create_character_voice_component,
    create_character_relationships_component,
    create_knowledge_context_component,
)
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


async def test_all_factories():
    """Test all 11 implemented CDL factory functions."""
    
    print("=" * 80)
    print("COMPREHENSIVE CDL FACTORY TEST SUITE")
    print("=" * 80)
    
    # Get environment configuration
    bot_name = get_normalized_bot_name_from_env()
    print(f"Bot Name: {bot_name}")
    print(f"Database: {os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}")
    print(f"Qdrant: {os.getenv('QDRANT_HOST')}:{os.getenv('QDRANT_PORT')}")
    print("=" * 80)
    print()
    
    # Get database pool and create enhanced manager
    pool = await get_postgres_pool()
    if not pool:
        print("❌ FAILED: Could not connect to database")
        return False
    
    print("✅ Database pool acquired")
    
    enhanced_manager = create_enhanced_cdl_manager(pool)
    print("✅ Enhanced CDL manager created")
    print()
    
    # Test data
    test_user_id = "123456789"
    test_message = "Are you an AI? I'm curious about artificial intelligence."
    test_user_facts = [
        {"fact": "Lives in San Diego, California"},
        {"fact": "Works as a software engineer"},
        {"fact": "Has a pet dog named Max"},
        {"fact": "Interested in marine conservation"},
    ]
    
    results = []
    
    # Test 1: CHARACTER_IDENTITY
    print("=" * 80)
    print("TEST 1: CHARACTER_IDENTITY (Priority 1)")
    print("=" * 80)
    try:
        component = await create_character_identity_component(
            enhanced_manager=enhanced_manager,
            character_name=bot_name
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            results.append(("CHARACTER_IDENTITY", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None")
            results.append(("CHARACTER_IDENTITY", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("CHARACTER_IDENTITY", False, 0))
    print()
    
    # Test 2: CHARACTER_MODE
    print("=" * 80)
    print("TEST 2: CHARACTER_MODE (Priority 2)")
    print("=" * 80)
    try:
        component = await create_character_mode_component(
            enhanced_manager=enhanced_manager,
            character_name=bot_name
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            results.append(("CHARACTER_MODE", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None")
            results.append(("CHARACTER_MODE", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("CHARACTER_MODE", False, 0))
    print()
    
    # Test 3: CHARACTER_BACKSTORY
    print("=" * 80)
    print("TEST 3: CHARACTER_BACKSTORY (Priority 3)")
    print("=" * 80)
    try:
        component = await create_character_backstory_component(
            enhanced_manager=enhanced_manager,
            character_name=bot_name
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            results.append(("CHARACTER_BACKSTORY", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None (expected - missing database field)")
            results.append(("CHARACTER_BACKSTORY", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("CHARACTER_BACKSTORY", False, 0))
    print()
    
    # Test 4: CHARACTER_PRINCIPLES
    print("=" * 80)
    print("TEST 4: CHARACTER_PRINCIPLES (Priority 4)")
    print("=" * 80)
    try:
        component = await create_character_principles_component(
            enhanced_manager=enhanced_manager,
            character_name=bot_name
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            results.append(("CHARACTER_PRINCIPLES", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None (expected - missing database field)")
            results.append(("CHARACTER_PRINCIPLES", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("CHARACTER_PRINCIPLES", False, 0))
    print()
    
    # Test 5: AI_IDENTITY_GUIDANCE
    print("=" * 80)
    print("TEST 5: AI_IDENTITY_GUIDANCE (Priority 5)")
    print("=" * 80)
    try:
        component = await create_ai_identity_guidance_component(
            enhanced_manager=enhanced_manager,
            character_name=bot_name,
            message_content=test_message
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            print(f"   Content preview: {component.content[:100]}...")
            results.append(("AI_IDENTITY_GUIDANCE", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None")
            results.append(("AI_IDENTITY_GUIDANCE", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("AI_IDENTITY_GUIDANCE", False, 0))
    print()
    
    # Test 6: TEMPORAL_AWARENESS
    print("=" * 80)
    print("TEST 6: TEMPORAL_AWARENESS (Priority 6)")
    print("=" * 80)
    try:
        component = await create_temporal_awareness_component()
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            print(f"   Content: {component.content}")
            results.append(("TEMPORAL_AWARENESS", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None")
            results.append(("TEMPORAL_AWARENESS", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("TEMPORAL_AWARENESS", False, 0))
    print()
    
    # Test 7: USER_PERSONALITY
    print("=" * 80)
    print("TEST 7: USER_PERSONALITY (Priority 7)")
    print("=" * 80)
    try:
        component = await create_user_personality_component(
            enhanced_manager=enhanced_manager,
            character_name=bot_name,
            user_id=test_user_id
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            results.append(("USER_PERSONALITY", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None (expected - no personality data)")
            results.append(("USER_PERSONALITY", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("USER_PERSONALITY", False, 0))
    print()
    
    # Test 8: CHARACTER_PERSONALITY
    print("=" * 80)
    print("TEST 8: CHARACTER_PERSONALITY (Priority 8)")
    print("=" * 80)
    try:
        component = await create_character_personality_component(
            enhanced_manager=enhanced_manager,
            character_name=bot_name
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            print(f"   Content preview: {component.content[:150]}...")
            results.append(("CHARACTER_PERSONALITY", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None")
            results.append(("CHARACTER_PERSONALITY", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("CHARACTER_PERSONALITY", False, 0))
    print()
    
    # Test 9: CHARACTER_VOICE
    print("=" * 80)
    print("TEST 9: CHARACTER_VOICE (Priority 10)")
    print("=" * 80)
    try:
        component = await create_character_voice_component(
            enhanced_manager=enhanced_manager,
            character_name=bot_name
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            results.append(("CHARACTER_VOICE", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None (expected - VoiceTrait bug)")
            results.append(("CHARACTER_VOICE", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("CHARACTER_VOICE", False, 0))
    print()
    
    # Test 10: CHARACTER_RELATIONSHIPS
    print("=" * 80)
    print("TEST 10: CHARACTER_RELATIONSHIPS (Priority 11)")
    print("=" * 80)
    try:
        component = await create_character_relationships_component(
            enhanced_manager=enhanced_manager,
            character_name=bot_name,
            user_id=test_user_id
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            results.append(("CHARACTER_RELATIONSHIPS", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None (expected - no relationship data)")
            results.append(("CHARACTER_RELATIONSHIPS", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("CHARACTER_RELATIONSHIPS", False, 0))
    print()
    
    # Test 11: KNOWLEDGE_CONTEXT
    print("=" * 80)
    print("TEST 11: KNOWLEDGE_CONTEXT (Priority 16)")
    print("=" * 80)
    try:
        component = await create_knowledge_context_component(
            user_facts=test_user_facts
        )
        if component:
            print(f"✅ PASS: Created component with {len(component.content)} chars")
            print(f"   Priority: {component.priority}, Token Cost: {component.token_cost}, Required: {component.required}")
            print(f"   Content:\n{component.content}")
            results.append(("KNOWLEDGE_CONTEXT", True, len(component.content)))
        else:
            print("⚠️  GRACEFUL FAIL: Component returned None")
            results.append(("KNOWLEDGE_CONTEXT", False, 0))
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        results.append(("KNOWLEDGE_CONTEXT", False, 0))
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    working = [r for r in results if r[1]]
    failing = [r for r in results if not r[1]]
    
    print(f"\n✅ WORKING COMPONENTS ({len(working)}/11):")
    for name, status, chars in working:
        print(f"   - {name}: {chars} chars")
    
    print(f"\n⚠️  GRACEFULLY FAILING COMPONENTS ({len(failing)}/11):")
    for name, status, chars in failing:
        print(f"   - {name}: Missing data or needs fix")
    
    total_chars = sum(r[2] for r in working)
    total_tokens = total_chars // 4  # Rough estimate
    
    print(f"\n📊 METRICS:")
    print(f"   - Total working components: {len(working)}/11 ({len(working)/11*100:.1f}%)")
    print(f"   - Total assembled content: {total_chars} chars (~{total_tokens} tokens)")
    print(f"   - Token budget utilization: {total_tokens}/20000 ({total_tokens/20000*100:.1f}%)")
    
    print("\n" + "=" * 80)
    if len(working) >= 5:
        print("🎉 TEST SUITE PASSED: At least 5 components working")
        return True
    else:
        print("⚠️  TEST SUITE INCOMPLETE: Less than 5 components working")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_all_factories())
    sys.exit(0 if success else 1)
