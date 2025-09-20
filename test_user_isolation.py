#!/usr/bin/env python3
"""
Test script to verify user isolation in WhisperEngine memory system.
This checks that each user only sees their own conversation history.
"""

import asyncio
import os
import sys
import logging

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory.vector_memory_system import VectorMemoryManager

async def test_user_isolation():
    """Test that users only see their own memories and conversations."""
    
    print("🔍 Testing User Isolation in WhisperEngine Memory System")
    print("=" * 60)
    
    # Initialize memory manager with Docker config
    config = {
        'qdrant': {
            'host': 'localhost',  # Change to 'qdrant' if running inside Docker
            'port': 6333,
            'collection_name': 'whisperengine_memory',
            'vector_size': 384
        },
        'embeddings': {
            'model_name': 'snowflake/snowflake-arctic-embed-xs',
            'device': 'cpu'
        }
    }
    
    try:
        memory_manager = VectorMemoryManager(config)
        print("✅ Memory manager initialized")
        
        # Test data for different users
        user_alice = "123456789"
        user_bob = "987654321"
        user_charlie = "555666777"
        
        test_data = {
            user_alice: [
                ("Hi, my cat's name is Luna", "Your cat's name is Luna, right?"),
                ("I love programming in Python", "Python is a great language!"),
                ("My favorite color is blue", "Blue is a lovely color!")
            ],
            user_bob: [
                ("I have a dog named Max", "Max sounds like a great dog!"),
                ("I work as a doctor", "Medicine is an important field!"),
                ("I enjoy hiking", "Hiking is excellent exercise!")
            ],
            user_charlie: [
                ("I'm learning guitar", "Guitar is a wonderful instrument!"),
                ("I live in Seattle", "Seattle is a beautiful city!"),
                ("I love coffee", "Coffee is indeed amazing!")
            ]
        }
        
        # Store test conversations for each user
        print("\n📝 Storing test conversations...")
        for user_id, conversations in test_data.items():
            for user_msg, bot_response in conversations:
                success = await memory_manager.store_conversation(
                    user_id=user_id,
                    user_message=user_msg,
                    bot_response=bot_response,
                    channel_id=f"test_channel_{user_id}"
                )
                if success:
                    print(f"   ✅ Stored for user {user_id}: '{user_msg[:30]}...'")
                else:
                    print(f"   ❌ Failed to store for user {user_id}")
        
        print("\n🔍 Testing memory retrieval isolation...")
        
        # Test 1: Alice searches for pet-related content
        print(f"\n1️⃣ Alice searches for 'pet cat dog':")
        alice_memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_alice,
            query="pet cat dog",
            limit=10
        )
        
        alice_content = " ".join([m.get('content', '') for m in alice_memories])
        print(f"   Alice found {len(alice_memories)} memories")
        
        # Check for cross-contamination
        if "Max" in alice_content or "dog" in alice_content.lower():
            print(f"   ❌ SECURITY VIOLATION: Alice can see Bob's dog content!")
            print(f"   Content: {alice_content}")
            return False
        else:
            print(f"   ✅ Alice only sees her own content (Luna the cat)")
        
        # Test 2: Bob searches for work-related content
        print(f"\n2️⃣ Bob searches for 'work profession job':")
        bob_memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_bob,
            query="work profession job",
            limit=10
        )
        
        bob_content = " ".join([m.get('content', '') for m in bob_memories])
        print(f"   Bob found {len(bob_memories)} memories")
        
        # Check for cross-contamination
        if "Python" in bob_content or "programming" in bob_content.lower():
            print(f"   ❌ SECURITY VIOLATION: Bob can see Alice's programming content!")
            print(f"   Content: {bob_content}")
            return False
        else:
            print(f"   ✅ Bob only sees his own content (doctor work)")
        
        # Test 3: Charlie searches for hobby content
        print(f"\n3️⃣ Charlie searches for 'music hobby interest':")
        charlie_memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_charlie,
            query="music hobby interest",
            limit=10
        )
        
        charlie_content = " ".join([m.get('content', '') for m in charlie_memories])
        print(f"   Charlie found {len(charlie_memories)} memories")
        
        # Check for cross-contamination
        if "hiking" in charlie_content.lower() or "doctor" in charlie_content.lower():
            print(f"   ❌ SECURITY VIOLATION: Charlie can see Bob's content!")
            print(f"   Content: {charlie_content}")
            return False
        else:
            print(f"   ✅ Charlie only sees his own content (guitar)")
        
        # Test 4: Cross-user query test
        print(f"\n4️⃣ Cross-user content verification:")
        
        # Alice tries to search for Bob's specific content
        alice_cross_search = await memory_manager.retrieve_relevant_memories(
            user_id=user_alice,
            query="doctor Max dog hiking",
            limit=20
        )
        
        alice_cross_content = " ".join([m.get('content', '') for m in alice_cross_search])
        
        if any(word in alice_cross_content.lower() for word in ["max", "doctor", "hiking"]):
            print(f"   ❌ CRITICAL SECURITY VIOLATION: Alice can access Bob's private data!")
            print(f"   Leaked content: {alice_cross_content}")
            return False
        else:
            print(f"   ✅ Alice cannot access Bob's private information")
        
        print(f"\n🎉 All user isolation tests PASSED!")
        print(f"✅ Each user only sees their own conversation history")
        print(f"✅ No cross-user data contamination detected")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_user_isolation())
    if result:
        print(f"\n🔒 User isolation is properly implemented!")
        sys.exit(0)
    else:
        print(f"\n⚠️  User isolation may have security issues!")
        sys.exit(1)