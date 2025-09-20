#!/usr/bin/env python3
"""
Vector Memory System Performance Test
Tests memory operations against <200ms targets specified in the architecture
"""

import asyncio
import time
import statistics
import json
from datetime import datetime
from typing import List, Dict
from uuid import uuid4

# Import the vector memory system
import sys
import os
sys.path.append('/app/src')

from src.memory.vector_memory_system import VectorMemoryManager, VectorMemory, MemoryType


class PerformanceResults:
    """Container for performance test results"""
    
    def __init__(self):
        self.embedding_times: List[float] = []
        self.storage_times: List[float] = []
        self.search_times: List[float] = []
        self.conversation_storage_times: List[float] = []
        self.fact_storage_times: List[float] = []
        self.recent_conversations_times: List[float] = []
        
    def add_measurement(self, operation: str, duration_ms: float):
        """Add a performance measurement"""
        if operation == 'embedding':
            self.embedding_times.append(duration_ms)
        elif operation == 'storage':
            self.storage_times.append(duration_ms)
        elif operation == 'search':
            self.search_times.append(duration_ms)
        elif operation == 'conversation_storage':
            self.conversation_storage_times.append(duration_ms)
        elif operation == 'fact_storage':
            self.fact_storage_times.append(duration_ms)
        elif operation == 'recent_conversations':
            self.recent_conversations_times.append(duration_ms)
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation"""
        times = getattr(self, f"{operation}_times", [])
        if not times:
            return {"count": 0}
        
        return {
            "count": len(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "avg_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "p95_ms": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
            "target_200ms": all(t < 200 for t in times),
            "under_200ms_percent": (sum(1 for t in times if t < 200) / len(times)) * 100
        }
    
    def print_summary(self):
        """Print performance summary"""
        print("\n" + "="*80)
        print("🚀 VECTOR MEMORY SYSTEM PERFORMANCE REPORT")
        print("="*80)
        
        operations = [
            ('embedding', 'Embedding Generation'),
            ('storage', 'Memory Storage'),
            ('search', 'Memory Search'),
            ('conversation_storage', 'Conversation Storage'),
            ('fact_storage', 'Fact Storage'),
            ('recent_conversations', 'Recent Conversations')
        ]
        
        for op_key, op_name in operations:
            stats = self.get_stats(op_key)
            if stats["count"] == 0:
                continue
                
            print(f"\n📊 {op_name}:")
            print(f"   Tests run: {stats['count']}")
            print(f"   Average: {stats['avg_ms']:.1f}ms")
            print(f"   Median: {stats['median_ms']:.1f}ms")
            print(f"   Min/Max: {stats['min_ms']:.1f}ms / {stats['max_ms']:.1f}ms")
            print(f"   95th percentile: {stats['p95_ms']:.1f}ms")
            
            # Performance target assessment
            target_met = "✅" if stats['target_200ms'] else "❌"
            print(f"   {target_met} <200ms target: {stats['under_200ms_percent']:.1f}% under target")
            
            if not stats['target_200ms']:
                print(f"   ⚠️  {100 - stats['under_200ms_percent']:.1f}% of operations exceeded 200ms")


async def measure_time(operation_name: str, coro, results: PerformanceResults):
    """Measure execution time of an async operation"""
    start_time = time.perf_counter()
    result = await coro
    end_time = time.perf_counter()
    
    duration_ms = (end_time - start_time) * 1000
    results.add_measurement(operation_name, duration_ms)
    
    print(f"⏱️  {operation_name}: {duration_ms:.1f}ms")
    return result


async def test_vector_memory_performance():
    """Comprehensive performance test for vector memory system"""
    
    print("🧪 Starting Vector Memory Performance Test")
    print(f"📅 Test Date: {datetime.now().isoformat()}")
    
    # Initialize vector memory manager
    config = {
        'qdrant': {
            'host': 'qdrant',  # Docker service name
            'port': 6333,
            'collection_name': 'performance_test'
        },
        'embeddings': {
            'model_name': 'all-MiniLM-L6-v2'
        }
    }
    
    print("\n🔧 Initializing VectorMemoryManager...")
    memory_manager = VectorMemoryManager(config)
    
    # Wait for initialization
    await asyncio.sleep(2)
    
    results = PerformanceResults()
    test_user_id = "perf_test_user_12345"
    
    print("\n" + "="*60)
    print("🧠 EMBEDDING GENERATION PERFORMANCE")
    print("="*60)
    
    # Test embedding generation with various text lengths
    test_texts = [
        "Hello world",
        "This is a medium length text for testing embedding generation performance",
        "This is a much longer text that includes multiple sentences and should test how the embedding model performs with longer content. It includes various topics and concepts to ensure we're testing realistic scenarios that the bot might encounter in actual conversations with users.",
        "Short",
        "Another test message with different content and vocabulary to ensure comprehensive testing"
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\nTest {i+1}: Text length {len(text)} chars")
        await measure_time(
            'embedding',
            memory_manager.vector_store.generate_embedding(text),
            results
        )
    
    print("\n" + "="*60)
    print("💾 MEMORY STORAGE PERFORMANCE")
    print("="*60)
    
    # Test memory storage
    for i in range(5):
        memory = VectorMemory(
            id=str(uuid4()),  # Use proper UUID
            user_id=test_user_id,
            memory_type=MemoryType.CONVERSATION,
            content=f"This is test memory {i} for performance testing",
            source="performance_test",
            metadata={"test_id": i, "performance": True}
        )
        
        print(f"\nStoring memory {i+1}")
        await measure_time(
            'storage',
            memory_manager.vector_store.store_memory(memory),
            results
        )
    
    print("\n" + "="*60)
    print("🔍 MEMORY SEARCH PERFORMANCE")
    print("="*60)
    
    # Test memory search
    search_queries = [
        "test memory",
        "performance testing",
        "conversation",
        "hello world",
        "different content"
    ]
    
    for i, query in enumerate(search_queries):
        print(f"\nSearch {i+1}: '{query}'")
        await measure_time(
            'search',
            memory_manager.vector_store.search_memories(
                query=query,
                user_id=test_user_id,
                top_k=10
            ),
            results
        )
    
    print("\n" + "="*60)
    print("💬 CONVERSATION STORAGE PERFORMANCE")
    print("="*60)
    
    # Test conversation storage (high-level API)
    conversations = [
        ("What's the weather like?", "I can't check weather, but I'd be happy to chat about other topics!"),
        ("Tell me about Python", "Python is a versatile programming language known for its simplicity and readability."),
        ("How are you doing?", "I'm doing well, thank you for asking! How can I help you today?"),
        ("What's your favorite color?", "I don't have personal preferences, but I find the concept of color fascinating!"),
        ("Can you help me with coding?", "Absolutely! I'd be happy to help you with coding questions and problems.")
    ]
    
    for i, (user_msg, bot_msg) in enumerate(conversations):
        print(f"\nConversation {i+1}")
        await measure_time(
            'conversation_storage',
            memory_manager.store_conversation(
                user_id=test_user_id,
                user_message=user_msg,
                bot_response=bot_msg,
                channel_id="perf_test_channel",
                metadata={"test_conversation": i}
            ),
            results
        )
    
    print("\n" + "="*60)
    print("📝 FACT STORAGE PERFORMANCE")
    print("="*60)
    
    # Test fact storage
    facts = [
        ("User likes pizza", "food preferences"),
        ("User works in tech", "career information"),
        ("User has a dog named Max", "personal life"),
        ("User prefers morning workouts", "lifestyle"),
        ("User is learning Spanish", "education")
    ]
    
    for i, (fact, context) in enumerate(facts):
        print(f"\nFact {i+1}")
        await measure_time(
            'fact_storage',
            memory_manager.store_fact(
                user_id=test_user_id,
                fact=fact,
                context=context,
                confidence=0.9
            ),
            results
        )
    
    print("\n" + "="*60)
    print("📚 RECENT CONVERSATIONS PERFORMANCE")
    print("="*60)
    
    # Test recent conversations retrieval
    for i in range(3):
        print(f"\nRecent conversations test {i+1}")
        await measure_time(
            'recent_conversations',
            memory_manager.get_recent_conversations(
                user_id=test_user_id,
                limit=10
            ),
            results
        )
    
    # Print comprehensive results
    results.print_summary()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vector_memory_performance_{timestamp}.json"
    
    performance_data = {
        "timestamp": datetime.now().isoformat(),
        "test_config": config,
        "results": {
            "embedding": results.get_stats('embedding'),
            "storage": results.get_stats('storage'),
            "search": results.get_stats('search'),
            "conversation_storage": results.get_stats('conversation_storage'),
            "fact_storage": results.get_stats('fact_storage'),
            "recent_conversations": results.get_stats('recent_conversations')
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(performance_data, f, indent=2)
    
    print(f"\n💾 Performance results saved to: {filename}")
    
    # Performance assessment
    print("\n" + "="*80)
    print("🎯 PERFORMANCE ASSESSMENT")
    print("="*80)
    
    all_operations_under_200ms = True
    for operation in ['embedding', 'storage', 'search', 'conversation_storage', 'fact_storage', 'recent_conversations']:
        stats = results.get_stats(operation)
        if stats.get("count", 0) > 0 and not stats.get("target_200ms", False):
            all_operations_under_200ms = False
            break
    
    if all_operations_under_200ms:
        print("✅ SUCCESS: All memory operations meet the <200ms performance target!")
        print("🚀 Vector memory system is ready for production workloads.")
    else:
        print("⚠️  WARNING: Some operations exceeded the 200ms target.")
        print("🔧 Consider optimization or infrastructure scaling.")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_vector_memory_performance())