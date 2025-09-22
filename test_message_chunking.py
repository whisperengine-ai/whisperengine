#!/usr/bin/env python3
"""
Test script for the new message chunking feature
"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

from src.memory.vector_memory_system import VectorMemoryStore, VectorMemory, MemoryType
from datetime import datetime
from uuid import uuid4

async def test_message_chunking():
    """Test the message chunking functionality"""
    
    print("🔄 Testing Message Chunking Feature")
    print("=" * 50)
    
    try:
        # Initialize vector store
        vector_store = VectorMemoryStore(
            qdrant_host="localhost",
            qdrant_port=6333,
            collection_name="test_chunking"
        )
        
        # Test cases
        test_cases = [
            {
                "name": "Short Message (No Chunking)",
                "content": "Hello, how are you today?",
                "should_chunk": False
            },
            {
                "name": "Long Single Sentence (No Chunking)",
                "content": "I am having a really great day and everything is going wonderfully well for me today and I hope you are doing well too",
                "should_chunk": False
            },
            {
                "name": "Multiple Sentences (Should Chunk)",
                "content": "Hey, I'm really excited about my new job at Google as a software engineer! I start Monday and I'm nervous but thrilled. The interview process was intense - 5 rounds including system design. My manager seems really supportive and the team works on search algorithms. I'm particularly interested in their machine learning applications for ranking. Do you think I should prepare anything specific for my first week?",
                "should_chunk": True
            },
            {
                "name": "Multiple Questions (Should Chunk)",
                "content": "What time is it? Are you busy today? Can you help me with something? I have a lot of questions!",
                "should_chunk": True
            },
            {
                "name": "Emotional Expressions (Should Chunk)",
                "content": "I'm so happy today! Everything is going great! I got the promotion I wanted! I can't believe it happened!",
                "should_chunk": True
            }
        ]
        
        # Test chunking logic
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test_case['name']}")
            print(f"   Content: {test_case['content'][:80]}..." if len(test_case['content']) > 80 else f"   Content: {test_case['content']}")
            
            # Test chunking decision
            should_chunk = vector_store._should_chunk_content(test_case['content'])
            print(f"   Should chunk: {should_chunk}")
            print(f"   Expected: {test_case['should_chunk']}")
            
            if should_chunk == test_case['should_chunk']:
                print("   ✅ Chunking decision correct")
            else:
                print("   ❌ Chunking decision incorrect")
            
            # Test actual chunking if applicable
            if should_chunk:
                chunks = vector_store._create_content_chunks(test_case['content'])
                print(f"   Created {len(chunks)} chunks:")
                for j, chunk in enumerate(chunks):
                    print(f"     Chunk {j+1}: {chunk[:60]}..." if len(chunk) > 60 else f"     Chunk {j+1}: {chunk}")
        
        print("\n" + "=" * 50)
        print("🧪 Testing Full Storage Process")
        
        # Test full storage process with chunking
        test_memory = VectorMemory(
            id=str(uuid4()),
            user_id="test_user_chunking",
            memory_type=MemoryType.CONVERSATION,
            content="I'm really excited about starting my new job tomorrow! The onboarding process looks comprehensive. I've been reading about the company culture and it seems amazing. Do you have any tips for making a good first impression? I want to make sure I integrate well with the team.",
            source="test_message",
            confidence=0.8,
            timestamp=datetime.now()
        )
        
        print(f"Storing test memory with content length: {len(test_memory.content)}")
        
        # Store the memory (should trigger chunking)
        memory_id = await vector_store.store_memory(test_memory)
        print(f"✅ Memory stored with ID: {memory_id}")
        
        # Search for the memory to verify it was stored correctly
        search_results = await vector_store.search_memories(
            query="new job excited onboarding",
            user_id="test_user_chunking",
            top_k=5
        )
        
        print(f"Found {len(search_results)} related memories:")
        for result in search_results:
            is_chunked = result.get('is_chunked', False)
            chunk_info = f" (Chunk {result.get('chunk_index', 0)+1}/{result.get('total_chunks', 1)})" if is_chunked else ""
            print(f"  - {result['content'][:60]}...{chunk_info}")
            print(f"    Score: {result['score']:.3f}")
        
        print("\n✅ Message chunking test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_message_chunking())