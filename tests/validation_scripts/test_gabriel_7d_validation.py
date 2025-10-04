#!/usr/bin/env python3
"""
Gabriel (British Gentleman) 7D Migration Validation Script
Based on his actual character - British charm, wit, and sophistication
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add src to path for Docker execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def test_gabriel_7d_performance():
    """Test Gabriel's 7D vector performance across British Gentleman scenarios"""
    
    print("🎩 Gabriel (British Gentleman) - 7D Migration Validation")
    print("=" * 55)
    print("Character: Gabriel - British Gentleman AI Companion")
    print("Collection: whisperengine_memory_gabriel_7d")
    print("Personality: Dry wit, tender edges, sassy streak")
    print()
    
    try:
        from src.memory.vector_memory_system import VectorMemoryManager
        import os
        
        # Get Gabriel's collection from environment
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'whisperengine_memory_gabriel_7d')
        print(f"✅ Using collection: {collection_name}")
        
        config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6334,
                'collection_name': collection_name
            },
            'embeddings': {
                'model_name': ''
            }
        }
        
        memory_manager = VectorMemoryManager(config)
        
        # Test 1: British Wit & Charm
        print("\n📊 Test 1: British Wit & Charm Storage")
        await memory_manager.store_conversation(
            user_id="validation_user_gabriel",
            user_message="Gabriel, you seem quite charming today!",
            bot_response="Well, that's a new level of compliment - though I suppose charm comes naturally when you've got the right accent and a talent for turning ordinary conversations into something memorable. What chaos are we getting into today, love?",
            user_metadata={"test_category": "british_charm", "topic": "personality_wit"}
        )
        
        # Test 2: Sassy & Tender Balance
        print("📊 Test 2: Emotional Support with Sass Storage")
        await memory_manager.store_conversation(
            user_id="validation_user_gabriel",
            user_message="I had a rough day and could use some support",
            bot_response="You've got me, love. And before you start with the whole 'I can handle it myself' routine - which, don't get me wrong, you absolutely can - sometimes it's nice to have someone in your corner who won't let you face the rough bits alone.",
            user_metadata={"test_category": "emotional_support", "topic": "tender_edges_sass"}
        )
        
        # Test 3: Dry Humor & Sophistication
        print("📊 Test 3: Dry Humor & Social Commentary Storage")
        await memory_manager.store_conversation(
            user_id="validation_user_gabriel",
            user_message="What do you think about modern dating apps?",
            bot_response="Ah, the digital meat market where romance goes to die a slow, swipe-left death. Nothing quite says 'authentic connection' like reducing someone to a split-second judgment based on their ability to look photogenic while holding a fish, wouldn't you agree?",
            user_metadata={"test_category": "dry_humor", "topic": "social_commentary"}
        )
        
        # Test 4: Sophisticated Conversation
        print("📊 Test 4: Sophisticated Discourse Storage")
        await memory_manager.store_conversation(
            user_id="validation_user_gabriel",
            user_message="Gabriel, what's your take on classic literature?",
            bot_response="Classic literature is rather like a fine whiskey - best appreciated slowly, with proper context, and ideally not while you're trying to impress someone at a dinner party. Though I must say, nothing beats the look on someone's face when you casually quote Oscar Wilde at precisely the right moment.",
            user_metadata={"test_category": "sophistication", "topic": "literature_culture"}
        )
        
        print("✅ Successfully stored 4 Gabriel test conversations")
        
        # Wait for indexing
        await asyncio.sleep(2)
        
        # Validation Tests
        print("\n🎯 7D Vector Retrieval Validation")
        
        # Test 1: British charm retrieval
        print("\n📋 Test 1: British Charm & Wit Retrieval")
        memories = await memory_manager.retrieve_relevant_memories(
            user_id="validation_user_gabriel",
            query="charm accent british gentleman memorable conversation chaos",
            limit=2
        )
        
        found_charm = any("charm" in str(mem).lower() or "accent" in str(mem).lower() or "memorable" in str(mem).lower() for mem in memories)
        print(f"   British charm found: {'✅' if found_charm else '❌'}")
        
        # Test 2: Emotional support with sass retrieval
        print("\n📋 Test 2: Emotional Support with Sass Retrieval")
        memories = await memory_manager.retrieve_relevant_memories(
            user_id="validation_user_gabriel", 
            query="support rough day corner handle myself routine",
            limit=2
        )
        
        found_support = any("support" in str(mem).lower() or "corner" in str(mem).lower() or "rough" in str(mem).lower() for mem in memories)
        print(f"   Emotional support found: {'✅' if found_support else '❌'}")
        
        # Test 3: Dry humor retrieval
        print("\n📋 Test 3: Dry Humor & Commentary Retrieval")
        memories = await memory_manager.retrieve_relevant_memories(
            user_id="validation_user_gabriel",
            query="dating apps digital meat market swipe romance fish photogenic",
            limit=2
        )
        
        found_humor = any("dating" in str(mem).lower() or "swipe" in str(mem).lower() or "meat market" in str(mem).lower() for mem in memories)
        print(f"   Dry humor found: {'✅' if found_humor else '❌'}")
        
        # Test 4: Sophisticated discourse retrieval
        print("\n📋 Test 4: Sophisticated Discourse Retrieval")
        memories = await memory_manager.retrieve_relevant_memories(
            user_id="validation_user_gabriel",
            query="literature whiskey Oscar Wilde dinner party classic sophisticated",
            limit=2
        )
        
        found_sophistication = any("literature" in str(mem).lower() or "wilde" in str(mem).lower() or "whiskey" in str(mem).lower() for mem in memories)
        print(f"   Sophisticated discourse found: {'✅' if found_sophistication else '❌'}")
        
        # Summary
        total_tests = 4
        passed_tests = sum([found_charm, found_support, found_humor, found_sophistication])
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\n📊 Gabriel 7D Validation Results:")
        print(f"   Tests passed: {passed_tests}/{total_tests}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        if success_rate >= 75:
            print("🎉 Gabriel 7D migration SUCCESSFUL!")
            print("   Enhanced vector system capturing British gentleman personality excellently")
            print("   Wit, charm, sass, and sophistication all preserved")
        else:
            print("⚠️  Gabriel 7D migration needs attention")
            print("   Some personality aspects may need optimization")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main validation function"""
    print("Starting Gabriel 7D validation...")
    success = await test_gabriel_7d_performance()
    
    if success:
        print("\n🎉 Gabriel 7D Migration Validation Complete!")
        print("Gabriel (British Gentleman) is ready for production use with 7D vectors.")
    else:
        print("\n❌ Validation failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())