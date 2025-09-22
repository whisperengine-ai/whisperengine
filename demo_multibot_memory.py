#!/usr/bin/env python3
"""
Multi-Bot Memory Query System

Demonstrates advanced multi-bot memory capabilities:
1. Query all bots (global search)
2. Query specific subset of bots  
3. Cross-bot memory analysis
4. Bot-specific comparative analysis
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

# Add src to path
sys.path.insert(0, 'src')

class MultiBotMemoryQuerier:
    """Advanced multi-bot memory query capabilities"""
    
    def __init__(self):
        # Set local Qdrant configuration
        os.environ["VECTOR_QDRANT_HOST"] = "localhost"
        os.environ["VECTOR_QDRANT_PORT"] = "6333"
        os.environ["VECTOR_QDRANT_GRPC_PORT"] = "6334"
        os.environ["VECTOR_QDRANT_COLLECTION"] = "whisperengine_memory"
        os.environ["MEMORY_SYSTEM_TYPE"] = "vector"
    
    async def query_all_bots(self, query: str, user_id: str, top_k: int = 10) -> Dict[str, List[Dict]]:
        """
        Query across ALL bots' memories - useful for:
        - Admin/debugging purposes
        - Cross-bot pattern analysis
        - Global memory search
        """
        from memory.memory_protocol import create_memory_manager
        from qdrant_client import models
        
        print(f"🌍 Querying ALL bots for: '{query}'")
        
        # Create memory manager but override the search to bypass bot filtering
        os.environ["DISCORD_BOT_NAME"] = "system_admin"  # Special admin context
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Get embeddings for the query
        query_embedding = list(memory_manager.vector_store.embedder.embed([query]))[0]
        
        # Search WITHOUT bot_name filtering (global search)
        search_results = memory_manager.vector_store.client.search(
            collection_name=memory_manager.vector_store.collection_name,
            query_vector=("content", query_embedding),  # 🎯 Use named vector for content search
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
                    # Note: NO bot_name filter = search all bots
                ]
            ),
            limit=top_k,
            with_payload=True
        )
        
        # Group results by bot
        results_by_bot = {}
        for result in search_results:
            bot_name = result.payload.get('bot_name', 'unknown')
            if bot_name not in results_by_bot:
                results_by_bot[bot_name] = []
            
            results_by_bot[bot_name].append({
                'content': result.payload.get('content', ''),
                'score': result.score,
                'timestamp': result.payload.get('timestamp', ''),
                'memory_type': result.payload.get('memory_type', ''),
                'confidence': result.payload.get('confidence', 0.0)
            })
        
        print(f"   📊 Found memories from {len(results_by_bot)} bots")
        for bot_name, memories in results_by_bot.items():
            print(f"   🤖 {bot_name}: {len(memories)} memories")
        
        return results_by_bot
    
    async def query_specific_bots(self, query: str, user_id: str, bot_names: List[str], top_k: int = 10) -> Dict[str, List[Dict]]:
        """
        Query specific subset of bots - useful for:
        - Comparing similar bot types
        - Team-based analysis (e.g., all analytical bots)
        - Selective memory retrieval
        """
        from memory.memory_protocol import create_memory_manager
        from qdrant_client import models
        
        print(f"🎯 Querying specific bots {bot_names} for: '{query}'")
        
        # Create memory manager 
        os.environ["DISCORD_BOT_NAME"] = "multi_query_system"
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Get embeddings for the query
        query_embedding = list(memory_manager.vector_store.embedder.embed([query]))[0]
        
        # Search with bot_name filter for specific bots
        search_results = memory_manager.vector_store.client.search(
            collection_name=memory_manager.vector_store.collection_name,
            query_vector=("content", query_embedding),  # 🎯 Use named vector for content search
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                    models.FieldCondition(key="bot_name", match=models.MatchAny(any=bot_names))  # 🎯 Multi-bot filter
                ]
            ),
            limit=top_k,
            with_payload=True
        )
        
        # Group results by bot
        results_by_bot = {}
        for result in search_results:
            bot_name = result.payload.get('bot_name', 'unknown')
            if bot_name not in results_by_bot:
                results_by_bot[bot_name] = []
            
            results_by_bot[bot_name].append({
                'content': result.payload.get('content', ''),
                'score': result.score,
                'timestamp': result.payload.get('timestamp', ''),
                'memory_type': result.payload.get('memory_type', ''),
                'confidence': result.payload.get('confidence', 0.0)
            })
        
        print(f"   📊 Found memories from {len(results_by_bot)} of {len(bot_names)} requested bots")
        for bot_name in bot_names:
            count = len(results_by_bot.get(bot_name, []))
            print(f"   🤖 {bot_name}: {count} memories")
        
        return results_by_bot
    
    async def cross_bot_analysis(self, user_id: str, analysis_topic: str) -> Dict[str, Any]:
        """
        Analyze how different bots remember/perceive the same user or topic
        """
        print(f"🔍 Cross-bot analysis for topic: '{analysis_topic}'")
        
        # Query all bots for this topic
        all_results = await self.query_all_bots(analysis_topic, user_id, top_k=20)
        
        analysis = {
            'topic': analysis_topic,
            'user_id': user_id,
            'bots_analyzed': list(all_results.keys()),
            'total_memories': sum(len(memories) for memories in all_results.values()),
            'bot_perspectives': {},
            'common_themes': [],
            'unique_insights': {}
        }
        
        # Analyze each bot's perspective
        for bot_name, memories in all_results.items():
            if not memories:
                continue
                
            # Extract key characteristics for this bot's memories
            avg_score = sum(m['score'] for m in memories) / len(memories)
            avg_confidence = sum(m['confidence'] for m in memories) / len(memories)
            memory_types = list(set(m['memory_type'] for m in memories))
            
            analysis['bot_perspectives'][bot_name] = {
                'memory_count': len(memories),
                'average_relevance_score': avg_score,
                'average_confidence': avg_confidence,
                'memory_types': memory_types,
                'sample_content': memories[0]['content'][:100] + "..." if memories else ""
            }
        
        return analysis
    
    async def demonstrate_multi_bot_capabilities(self):
        """Demonstrate all multi-bot memory capabilities"""
        
        print("🚀 Multi-Bot Memory Query Demonstration")
        print("=" * 50)
        
        # First, create some test memories for different bots
        await self.create_demo_memories()
        
        test_user = "demo_user_multibot"
        
        # 1. Query all bots
        print("\n🌍 CAPABILITY 1: Query All Bots")
        print("-" * 30)
        all_bot_results = await self.query_all_bots("test memory", test_user, top_k=20)
        
        # 2. Query specific subset of bots
        print("\n🎯 CAPABILITY 2: Query Specific Bots")
        print("-" * 30)
        subset_results = await self.query_specific_bots(
            "emotional support", 
            test_user, 
            ["Elena", "Gabriel"], 
            top_k=10
        )
        
        # 3. Cross-bot analysis
        print("\n🔍 CAPABILITY 3: Cross-Bot Analysis")
        print("-" * 30)
        analysis = await self.cross_bot_analysis(test_user, "user preferences")
        
        print(f"\n📊 Analysis Results:")
        print(f"   🎯 Topic: {analysis['topic']}")
        print(f"   🤖 Bots analyzed: {len(analysis['bots_analyzed'])}")
        print(f"   💾 Total memories: {analysis['total_memories']}")
        
        for bot_name, perspective in analysis['bot_perspectives'].items():
            print(f"\n   🤖 {bot_name} Perspective:")
            print(f"      📊 Memory count: {perspective['memory_count']}")
            print(f"      🎯 Avg relevance: {perspective['average_relevance_score']:.3f}")
            print(f"      💫 Avg confidence: {perspective['average_confidence']:.3f}")
            print(f"      📝 Sample: {perspective['sample_content']}")
        
        print("\n🎉 Multi-Bot Memory Capabilities Demonstrated!")
        print("\nFuture Use Cases:")
        print("   🔍 Admin debugging across all bots")
        print("   📊 Cross-bot user behavior analysis")
        print("   🤝 Collaborative bot decision making")
        print("   🧠 Global knowledge synthesis")
        print("   📈 Comparative bot performance analysis")
    
    async def create_demo_memories(self):
        """Create demo memories for different bots"""
        from memory.memory_protocol import create_memory_manager
        from memory.vector_memory_system import MemoryType, VectorMemory
        
        demo_memories = {
            "Elena": [
                "User prefers warm emotional support conversations",
                "User appreciates empathetic responses to stress"
            ],
            "Gabriel": [
                "User enjoys philosophical discussions about consciousness", 
                "User is interested in exploring deep existential questions"
            ],
            "Marcus": [
                "User needs strategic analysis for business decisions",
                "User values logical problem-solving approaches"
            ]
        }
        
        for bot_name, memories in demo_memories.items():
            print(f"   📝 Creating demo memories for {bot_name}...")
            os.environ["DISCORD_BOT_NAME"] = bot_name
            memory_manager = create_memory_manager(memory_type="vector")
            
            for memory_text in memories:
                memory = VectorMemory(
                    id=str(uuid.uuid4()),
                    user_id="demo_user_multibot",
                    content=memory_text,
                    memory_type=MemoryType.FACT,
                    timestamp=datetime.utcnow(),
                    confidence=0.8,
                    source=f"demo_{bot_name.lower()}"
                )
                
                try:
                    await memory_manager.vector_store.store_memory(memory)
                except Exception as e:
                    print(f"      ⚠️ Failed to store memory: {e}")
        
        print("   ✅ Demo memories created for all bots")


async def main():
    """Run the multi-bot memory query demonstration"""
    querier = MultiBotMemoryQuerier()
    await querier.demonstrate_multi_bot_capabilities()


if __name__ == "__main__":
    asyncio.run(main())