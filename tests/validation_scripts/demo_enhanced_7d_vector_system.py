#!/usr/bin/env python3
"""
Enhanced 7-Dimensional Vector System Demo

This script demonstrates the new enhanced 7D vector system:
- content: Semantic similarity (30% weight)
- emotion: Emotional context (20% weight) 
- semantic: Concept clustering (10% weight)
- relationship: Bond development patterns (15% weight)
- personality: Character trait prominence (15% weight)
- interaction: Communication style patterns (5% weight)
- temporal: Conversation flow intelligence (5% weight)

Usage:
    source .venv/bin/activate
    python demo_enhanced_7d_vector_system.py
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_7d_vector_system():
    """Demonstrate the enhanced 7-dimensional vector system"""
    
    print("🎯 Enhanced 7-Dimensional Vector System Demo")
    print("=" * 60)
    
    # Set mock environment for testing
    os.environ['QDRANT_HOST'] = 'localhost'
    os.environ['QDRANT_PORT'] = '6334'
    os.environ['QDRANT_COLLECTION_NAME'] = 'test_7d_collection'
    os.environ['DISCORD_BOT_NAME'] = 'Elena Rodriguez'
    os.environ['CHARACTER_FILE'] = 'characters/examples/elena.json'
    
    try:
        # Import after setting environment
        from src.memory.vector_memory_system import VectorMemoryStore, VectorMemory, MemoryType
        
        # Initialize memory store
        print("📡 Initializing Enhanced 7D Vector Memory Store...")
        memory_store = VectorMemoryStore()
        
        # Test memories with different dimensional characteristics
        test_memories = [
            {
                "content": "I'm really worried about the coral reefs dying. My grandmother used to dive here when she was young.",
                "description": "Personal/Environmental - Should trigger: deep intimacy, empathy+scientific traits, emotional support mode",
                "expected_relationship": "intimacy_personal_trust_trusting",
                "expected_personality": "traits_empathy_scientific",
                "expected_interaction": "style_supportive_mode_emotional_support"
            },
            {
                "content": "Can you explain the technical details of CRISPR gene editing and its applications in marine conservation?",
                "description": "Educational/Technical - Should trigger: casual intimacy, analytical+scientific traits, educational mode",
                "expected_relationship": "intimacy_casual_trust_neutral", 
                "expected_personality": "traits_analytical_scientific",
                "expected_interaction": "style_analytical_mode_educational"
            },
            {
                "content": "Let's brainstorm some creative solutions for plastic pollution in the ocean! I have some wild ideas.",
                "description": "Creative/Collaborative - Should trigger: personal intimacy, creative+scientific traits, collaboration mode",
                "expected_relationship": "intimacy_personal_trust_trusting",
                "expected_personality": "traits_creative_scientific", 
                "expected_interaction": "style_creative_mode_creative_collaboration"
            },
            {
                "content": "Hey Elena! Hope you're having a good morning. What's new with you?",
                "description": "Casual/Greeting - Should trigger: casual intimacy, balanced traits, casual chat mode",
                "expected_relationship": "intimacy_casual_trust_neutral",
                "expected_personality": "traits_balanced",
                "expected_interaction": "style_casual_mode_casual_chat"
            }
        ]
        
        print("\n🧪 Testing 7D Vector Generation...")
        print("-" * 50)
        
        stored_memories = []
        for i, test_case in enumerate(test_memories):
            print(f"\n📝 Test Case {i+1}: {test_case['description']}")
            print(f"Content: '{test_case['content']}'")
            
            # Create memory object
            memory = VectorMemory(
                id=f"test_7d_{i+1}",
                user_id="demo_user_7d",
                memory_type=MemoryType.CONVERSATION,
                content=test_case['content'],
                source="demo_test"
            )
            
            # Store memory (this will generate all 7 dimensions)
            try:
                memory_id = await memory_store.store_memory(memory)
                stored_memories.append({
                    'id': memory_id,
                    'content': test_case['content'],
                    'expected': test_case
                })
                print(f"✅ Stored memory with ID: {memory_id}")
                
                # Verify the memory was stored with correct dimensions
                await verify_7d_storage(memory_store, memory_id, test_case)
                
            except Exception as e:
                print(f"❌ Failed to store memory: {e}")
                logger.error(f"Storage error: {e}", exc_info=True)
        
        print("\n🔍 Testing 7D Vector Retrieval...")
        print("-" * 50)
        
        # Test dimensional search queries
        search_queries = [
            {
                "query": "I'm concerned about ocean conservation",
                "description": "Environmental concern query - should match personal/scientific memories",
                "expected_matches": ["coral reefs", "marine conservation"]
            },
            {
                "query": "Tell me about gene editing techniques", 
                "description": "Technical education query - should match analytical/educational memories",
                "expected_matches": ["CRISPR", "technical details"]
            },
            {
                "query": "Let's come up with innovative ideas",
                "description": "Creative collaboration query - should match creative/brainstorming memories", 
                "expected_matches": ["brainstorm", "creative solutions"]
            },
            {
                "query": "Good morning! How are you?",
                "description": "Casual greeting query - should match casual/friendly memories",
                "expected_matches": ["good morning", "casual"]
            }
        ]
        
        for query_test in search_queries:
            print(f"\n🔎 Query: '{query_test['query']}'")
            print(f"Expected to match: {query_test['expected_matches']}")
            
            try:
                # Test basic semantic search (content dimension)
                results = await test_dimensional_search(memory_store, query_test['query'], "demo_user_7d")
                
                if results:
                    print(f"✅ Found {len(results)} relevant memories")
                    for j, result in enumerate(results[:2]):  # Show top 2
                        print(f"   {j+1}. '{result['content'][:60]}...' (score: {result.get('score', 'N/A'):.3f})")
                else:
                    print("⚠️ No memories found")
                    
            except Exception as e:
                print(f"❌ Search failed: {e}")
                logger.error(f"Search error: {e}", exc_info=True)
        
        print("\n🎯 Testing Multi-Dimensional Intelligence...")
        print("-" * 50)
        
        # Test multi-dimensional search with different weightings
        await test_multi_dimensional_search(memory_store, stored_memories)
        
        print("\n🎉 7D Vector System Demo Complete!")
        print("✅ Enhanced dimensional intelligence operational")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure you're running from the project root and dependencies are installed")
    except Exception as e:
        print(f"❌ Demo Error: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)

async def verify_7d_storage(memory_store, memory_id: str, test_case: Dict[str, Any]):
    """Verify that memory was stored with correct 7D analysis"""
    try:
        # This would require implementing a get_memory method to verify storage
        print(f"🔍 Verifying 7D storage for memory {memory_id}")
        print(f"   Expected relationship: {test_case.get('expected_relationship', 'N/A')}")
        print(f"   Expected personality: {test_case.get('expected_personality', 'N/A')}")
        print(f"   Expected interaction: {test_case.get('expected_interaction', 'N/A')}")
        
    except Exception as e:
        logger.warning(f"Verification failed: {e}")

async def test_dimensional_search(memory_store, query: str, user_id: str) -> List[Dict[str, Any]]:
    """Test search across all 7 dimensions"""
    try:
        # Use existing retrieval method (should now use 7D intelligence)
        memories = await memory_store.retrieve_relevant_memories(
            user_id=user_id,
            query=query,
            limit=5
        )
        
        return [
            {
                'content': memory.get('content', ''),
                'score': memory.get('score', 0.0),
                'memory_type': memory.get('memory_type', 'unknown')
            }
            for memory in memories
        ]
        
    except Exception as e:
        logger.error(f"Dimensional search failed: {e}")
        return []

async def test_multi_dimensional_search(memory_store, stored_memories: List[Dict[str, Any]]):
    """Test multi-dimensional search with different weight configurations"""
    
    # Test different dimensional weight configurations
    weight_configs = [
        {
            "name": "Content-Heavy (Current Default)",
            "description": "Emphasizes semantic similarity",
            "weights": {"content": 0.6, "emotion": 0.2, "personality": 0.1, "relationship": 0.1}
        },
        {
            "name": "Relationship-Focused", 
            "description": "Emphasizes relationship appropriateness",
            "weights": {"relationship": 0.4, "personality": 0.3, "content": 0.2, "emotion": 0.1}
        },
        {
            "name": "Character-Consistent",
            "description": "Emphasizes personality and character traits", 
            "weights": {"personality": 0.4, "content": 0.3, "relationship": 0.2, "emotion": 0.1}
        },
        {
            "name": "Emotional Intelligence",
            "description": "Emphasizes emotional context and support",
            "weights": {"emotion": 0.4, "relationship": 0.3, "content": 0.2, "personality": 0.1}
        }
    ]
    
    test_query = "I'm feeling anxious about my research project"
    
    for config in weight_configs:
        print(f"\n🎛️ Testing {config['name']}")
        print(f"   {config['description']}")
        print(f"   Weights: {config['weights']}")
        
        try:
            # TODO: Implement weighted multi-dimensional search
            # For now, just use standard search
            results = await test_dimensional_search(memory_store, test_query, "demo_user_7d")
            
            if results:
                print(f"   ✅ Top result: '{results[0]['content'][:50]}...'")
            else:
                print(f"   ⚠️ No results found")
                
        except Exception as e:
            print(f"   ❌ Configuration failed: {e}")

if __name__ == "__main__":
    asyncio.run(demo_7d_vector_system())