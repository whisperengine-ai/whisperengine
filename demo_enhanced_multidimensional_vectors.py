#!/usr/bin/env python3
"""
Enhanced Multi-Dimensional Vector System Demo

This script demonstrates the new enhanced vector dimensions:
- relationship: Bond development and interaction patterns
- context: Situational and environmental factors
- personality: Character trait prominence

Alongside existing dimensions:
- content: Semantic similarity
- emotion: Emotional context  
- semantic: Concept clustering
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

async def demo_enhanced_multidimensional_vectors():
    """Demonstrate the enhanced multi-dimensional vector system"""
    
    print("🚀 Enhanced Multi-Dimensional Vector System Demo")
    print("=" * 60)
    
    # Set mock environment for testing
    os.environ['QDRANT_HOST'] = 'localhost'
    os.environ['QDRANT_PORT'] = '6334'
    os.environ['QDRANT_COLLECTION_NAME'] = 'test_multidim_collection'
    os.environ['DISCORD_BOT_NAME'] = 'Elena Rodriguez'
    os.environ['CHARACTER_FILE'] = 'characters/examples/elena.json'
    
    try:
        # Import after setting environment
        from src.memory.vector_memory_system import VectorMemoryStore, VectorMemory, MemoryType
        
        # Initialize memory store
        print("📡 Initializing Enhanced Vector Memory Store...")
        memory_store = VectorMemoryStore()
        
        # Test memories with different dimensional characteristics
        test_memories = [
            # High relationship intimacy, educational context, scientific personality
            {
                "content": "I'm really worried about ocean acidification affecting coral reefs. My family has been diving there for generations and it's heartbreaking to see the changes.",
                "expected_dimensions": {
                    "relationship": "intimacy_personal_trust_trusting", 
                    "context": "mode_educational_time_general",
                    "personality": "traits_scientific_empathy"
                }
            },
            
            # Casual relationship, playful context, curious personality  
            {
                "content": "Haha, that's a funny marine biology joke! Do you know any other ocean puns?",
                "expected_dimensions": {
                    "relationship": "intimacy_casual_trust_neutral",
                    "context": "mode_playful_time_general", 
                    "personality": "traits_humorous_curious"
                }
            },
            
            # Deep relationship, crisis context, empathetic personality
            {
                "content": "I've been having panic attacks about climate change lately. I trust you to understand - you're the only one who gets how serious this is.",
                "expected_dimensions": {
                    "relationship": "intimacy_deep_trust_confidential",
                    "context": "mode_crisis_support_time_general",
                    "personality": "traits_empathy_protective"
                }
            },
            
            # Personal relationship, educational context, analytical personality
            {
                "content": "Can you explain how ocean currents work? I have a presentation tomorrow and I'm struggling with the technical details.",
                "expected_dimensions": {
                    "relationship": "intimacy_personal_trust_trusting",
                    "context": "mode_educational_time_general", 
                    "personality": "traits_analytical_scientific"
                }
            }
        ]
        
        print(f"\n📝 Storing {len(test_memories)} test memories with enhanced dimensions...")
        
        stored_memories = []
        for i, memory_data in enumerate(test_memories):
            memory = VectorMemory(
                id=f"test_multidim_{i}",
                user_id="demo_user_123",
                memory_type=MemoryType.CONVERSATION,
                content=memory_data["content"],
                metadata={"expected_dimensions": memory_data["expected_dimensions"]}
            )
            
            try:
                await memory_store.store_memory(memory)
                stored_memories.append(memory)
                print(f"  ✅ Memory {i+1}: {memory.content[:50]}...")
            except Exception as e:
                print(f"  ❌ Failed to store memory {i+1}: {e}")
        
        print(f"\n🔍 Testing Multi-Dimensional Retrieval...")
        
        # Test 1: Query by relationship intimacy (should find deep/personal memories)
        print("\n1️⃣ Searching by Relationship Context (deep trust)...")
        relationship_results = await memory_store.retrieve_memories_by_relationship_context(
            user_id="demo_user_123",
            relationship_query="deep personal conversation with trusted friend",
            limit=5
        )
        
        for result in relationship_results:
            score = result.get('score', 0)
            content = result.get('content', '')[:60]
            print(f"  🤝 Score: {score:.3f} | {content}...")
        
        # Test 2: Query by situational context (should find crisis/support memories)
        print("\n2️⃣ Searching by Situation Context (crisis support)...")
        context_results = await memory_store.retrieve_memories_by_situation_context(
            user_id="demo_user_123", 
            situation_query="emotional crisis needing support and understanding",
            limit=5
        )
        
        for result in context_results:
            score = result.get('score', 0)
            content = result.get('content', '')[:60]
            print(f"  🎭 Score: {score:.3f} | {content}...")
        
        # Test 3: Query by personality traits (should find empathetic/scientific memories)
        print("\n3️⃣ Searching by Personality Traits (empathy + scientific)...")
        personality_results = await memory_store.retrieve_memories_by_personality_traits(
            user_id="demo_user_123",
            personality_query="empathetic scientific understanding and environmental concern",
            character_name="elena",
            limit=5
        )
        
        for result in personality_results:
            score = result.get('score', 0) 
            content = result.get('content', '')[:60]
            print(f"  🎪 Score: {score:.3f} | {content}...")
        
        # Test 4: Multi-dimensional combined query
        print("\n4️⃣ Testing Multi-Dimensional Combined Search...")
        
        # Generate query embeddings for multiple dimensions
        query_text = "I need emotional support about environmental concerns"
        
        content_embedding = await memory_store.generate_embedding(query_text)
        emotion_embedding = await memory_store.generate_embedding(f"emotion worried_concerned: {query_text}")
        relationship_embedding = await memory_store.generate_embedding(f"relationship intimacy_deep_trust_trusting: {query_text}")
        
        if all([content_embedding, emotion_embedding, relationship_embedding]):
            combined_results = await memory_store.retrieve_memories_by_dimensions(
                user_id="demo_user_123",
                dimensions={
                    "content": content_embedding,
                    "emotion": emotion_embedding, 
                    "relationship": relationship_embedding
                },
                weights={
                    "content": 0.4,
                    "emotion": 0.3,
                    "relationship": 0.3
                },
                limit=5
            )
            
            print(f"  🎯 Found {len(combined_results)} memories with multi-dimensional search:")
            for result in combined_results:
                score = result.get('score', 0)
                content = result.get('content', '')[:60]
                dimensions = result.get('dimensions_used', [])
                print(f"    📊 Score: {score:.3f} | Dims: {dimensions} | {content}...")
        else:
            print("  ❌ Failed to generate query embeddings for multi-dimensional search")
        
        print("\n✅ Enhanced Multi-Dimensional Vector Demo Complete!")
        print("\n📋 Summary of New Capabilities:")
        print("  🤝 Relationship vectors track intimacy and trust levels")
        print("  🎭 Context vectors capture situational patterns")  
        print("  🎪 Personality vectors emphasize character traits")
        print("  📊 Multi-dimensional search combines all aspects")
        print("  🎯 Character authenticity preserved through dimensional intelligence")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Tip: Run this script from the project root with vector memory dependencies installed")
    except Exception as e:
        print(f"❌ Demo Error: {e}")
        logger.exception("Enhanced multi-dimensional vector demo failed")

if __name__ == "__main__":
    asyncio.run(demo_enhanced_multidimensional_vectors())