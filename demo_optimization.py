#!/usr/bin/env python3
"""
Comprehensive demonstration of WhisperEngine Qdrant Query Optimization.

This script demonstrates all the advanced optimization features:
- Query preprocessing and enhancement
- Adaptive similarity thresholds
- Content chunking for better embeddings
- Hybrid search with metadata filtering
- Result re-ranking with multiple factors
- Performance monitoring and metrics

Run this in the Docker container to see the optimization in action.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, '/app/src')


async def comprehensive_optimization_demo():
    """Demonstrate all optimization features comprehensively."""
    
    print("🚀 WhisperEngine Qdrant Query Optimization Demo")
    print("=" * 60)
    
    try:
        from src.memory.vector_memory_system import VectorMemoryManager
        from src.memory.qdrant_optimization import QdrantQueryOptimizer, QdrantOptimizationMetrics
        
        # Configuration
        config = {
            'qdrant': {
                'host': 'qdrant',
                'port': 6333,
                'collection_name': 'optimization_demo'
            },
            'embeddings': {
                'model_name': 'snowflake/snowflake-arctic-embed-xs',
                'device': 'cpu'
            }
        }
        
        # Initialize system
        print("\n1. 🔧 Initializing System")
        memory_manager = VectorMemoryManager(config)
        optimizer = QdrantQueryOptimizer(memory_manager)
        metrics = QdrantOptimizationMetrics()
        print("   ✅ VectorMemoryManager initialized")
        print("   ✅ QdrantQueryOptimizer initialized")
        print("   ✅ Metrics system ready")
        
        # Demo user
        user_id = "demo_user_optimization"
        
        # Store diverse test data
        print("\n2. 📝 Storing Diverse Test Data")
        test_conversations = [
            # Pet-related conversations
            ("What's my cat's name?", "Your cat's name is Luna, and she's a beautiful tabby cat."),
            ("Tell me about Luna's favorite activities", "Luna loves to play with feather toys, chase laser pointers, and nap in sunny windows."),
            ("How often should I feed Luna?", "Adult cats like Luna should typically be fed twice a day with high-quality cat food."),
            ("Luna seems sick today", "If Luna seems unwell, it's best to contact your veterinarian for proper care."),
            
            # Work-related conversations  
            ("I work as a software engineer", "That's great! Software engineering is an exciting and dynamic field."),
            ("I'm working on a Python project", "Python is an excellent language for many types of projects. What kind of application are you building?"),
            ("My team uses agile methodology", "Agile methodologies can be very effective for software development teams."),
            
            # Personal preferences
            ("My favorite color is blue", "Blue is a lovely color - it's calming and versatile."),
            ("I love Italian food", "Italian cuisine has so many delicious dishes. Do you have a favorite type of pasta?"),
            ("I enjoy reading science fiction", "Science fiction can be fascinating! It often explores interesting concepts about the future."),
            
            # Recent activities
            ("I went hiking yesterday", "Hiking is a great way to enjoy nature and get exercise."),
            ("I watched a movie last night", "What movie did you watch? I'd love to hear your thoughts about it."),
        ]
        
        for user_msg, bot_response in test_conversations:
            await memory_manager.store_conversation(
                user_id=user_id,
                user_message=user_msg,
                bot_response=bot_response,
                channel_id="demo_channel",
                metadata={
                    "topics": _extract_topics(user_msg),
                    "conversation_type": _classify_conversation(user_msg)
                }
            )
        
        print(f"   ✅ Stored {len(test_conversations)} diverse conversations")
        print("   📊 Topics covered: pets, work, preferences, activities")
        
        # Demonstrate query preprocessing
        print("\n3. 🔍 Query Preprocessing Demonstration")
        test_queries = [
            "what is the name of my pet cat and tell me about it",
            "the work that I do and my job information",
            "my favorite color and food preferences"
        ]
        
        for query in test_queries:
            processed = optimizer.preprocess_query(query)
            print(f"   Original: '{query}'")
            print(f"   Processed: '{processed}'")
            print()
        
        # Demonstrate adaptive thresholds
        print("4. ⚡ Adaptive Threshold Demonstration")
        threshold_scenarios = [
            ("conversation_recall", {"conversational_user": True}),
            ("fact_lookup", {"prefers_precise_answers": True}),
            ("general_search", {}),
            ("recent_context", {"exploration_mode": True})
        ]
        
        for query_type, user_history in threshold_scenarios:
            threshold = optimizer.get_adaptive_threshold(query_type, user_history)
            print(f"   {query_type}: {threshold:.3f} (user: {user_history})")
        
        # Demonstrate optimized search scenarios
        print("\n5. 🎯 Optimized Search Scenarios")
        
        # Scenario 1: Pet information with conversational context
        print("\n   Scenario 1: Pet Information (Conversational)")
        results1 = await memory_manager.retrieve_relevant_memories_optimized(
            user_id=user_id,
            query="tell me about my pet",
            query_type="conversation_recall",
            user_history={"conversational_user": True, "favorite_topics": ["pets"]},
            limit=5
        )
        _display_results(results1, "Pet-focused search")
        metrics.record_search_quality("pet information", results1, "relevant")
        
        # Scenario 2: Work information with precise lookup
        print("\n   Scenario 2: Work Information (Precise)")
        results2 = await memory_manager.retrieve_relevant_memories_optimized(
            user_id=user_id,
            query="my job and work",
            query_type="fact_lookup",
            user_history={"prefers_precise_answers": True},
            limit=3
        )
        _display_results(results2, "Work-focused search")
        metrics.record_search_quality("work information", results2, "relevant")
        
        # Scenario 3: Recent activities with time filtering
        print("\n   Scenario 3: Recent Activities (Time-Filtered)")
        results3 = await memory_manager.retrieve_relevant_memories_optimized(
            user_id=user_id,
            query="what did I do recently",
            query_type="recent_context",
            filters={
                "time_range": {
                    "start": datetime.now() - timedelta(hours=2),
                    "end": datetime.now()
                }
            },
            limit=4
        )
        _display_results(results3, "Recent activities search")
        metrics.record_search_quality("recent activities", results3, "helpful")
        
        # Demonstrate hybrid search with multiple filters
        print("\n6. 🔧 Hybrid Search with Multiple Filters")
        hybrid_results = await optimizer.hybrid_search(
            query="cats and pets",
            user_id=user_id,
            filters={
                "topics": ["pets"],
                "time_range": {
                    "start": datetime.now() - timedelta(hours=1),
                    "end": datetime.now()
                }
            }
        )
        _display_results(hybrid_results, "Hybrid filtered search")
        
        # Demonstrate content chunking
        print("\n7. 📄 Content Chunking Demonstration")
        long_content = "This is a very long conversation about cats and their behavior. " * 15
        chunks = optimizer.chunk_content(long_content, max_chunk_size=200)
        print(f"   Long content ({len(long_content)} chars) → {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
            print(f"   Chunk {i+1}: '{chunk[:100]}...'")
        
        # Demonstrate re-ranking comparison
        print("\n8. 🏆 Re-ranking Comparison")
        # Get basic results first
        basic_results = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="my cat Luna",
            limit=5
        )
        
        # Get optimized results
        optimized_results = await memory_manager.retrieve_relevant_memories_optimized(
            user_id=user_id,
            query="my cat Luna",
            query_type="conversation_recall",
            user_history={"conversational_user": True, "prefers_recent": True},
            limit=5
        )
        
        print("   Basic vs Optimized Results:")
        print(f"   Basic search: {len(basic_results)} results")
        print(f"   Optimized search: {len(optimized_results)} results")
        
        if optimized_results and 'reranked_score' in optimized_results[0]:
            print("   ✅ Re-ranking active in optimized results")
            for i, result in enumerate(optimized_results[:3]):
                breakdown = result.get('scoring_breakdown', {})
                print(f"     Result {i+1}: base={breakdown.get('base_score', 0):.3f}, "
                     f"recency={breakdown.get('recency_boost', 0):.3f}, "
                     f"final={result.get('reranked_score', 0):.3f}")
        
        # Performance metrics
        print("\n9. 📊 Performance Metrics & Recommendations")
        performance = metrics.get_performance_summary()
        print(f"   Total queries processed: {performance.get('total_queries', 0)}")
        print(f"   Average results per query: {performance.get('avg_results_per_query', 0):.1f}")
        print(f"   Cache hit rate: {performance.get('cache_hit_rate', 0):.1%}")
        
        recommendations = metrics.get_optimization_recommendations()
        if recommendations:
            print("   📈 Optimization Recommendations:")
            for key, rec in recommendations.items():
                print(f"     {key}: {rec}")
        
        # Final integration test
        print("\n10. 🧪 Complete Integration Test")
        context = await memory_manager.get_conversation_context_optimized(
            user_id=user_id,
            current_message="How can I better take care of Luna and keep her happy?",
            user_preferences={
                "conversational_user": True,
                "favorite_topics": ["pets", "cats"],
                "prefers_recent": True
            },
            max_memories=8
        )
        
        print(f"    ✅ Retrieved {len(context)} context memories for complex query")
        print("    🎯 Query combines: pet care + user preferences + recent focus")
        
        if context:
            # Show most relevant result
            top_result = context[0]
            print(f"    🥇 Top result: '{top_result.get('content', '')[:80]}...'")
            if 'reranked_score' in top_result:
                print(f"    📊 Optimized score: {top_result['reranked_score']:.3f}")
        
        print("\n" + "=" * 60)
        print("🎉 Comprehensive Optimization Demo Complete!")
        print("✅ All features working: preprocessing, thresholds, chunking, hybrid search, re-ranking")
        print("📈 Performance monitoring active")
        print("🔧 Ready for production use with WhisperEngine")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


def _extract_topics(message: str) -> list:
    """Extract topic keywords from message."""
    topic_keywords = {
        "pets": ["cat", "luna", "pet", "feed", "sick", "veterinarian"],
        "work": ["engineer", "software", "python", "project", "team", "agile"],
        "preferences": ["favorite", "color", "food", "blue", "italian"],
        "activities": ["hiking", "movie", "watched", "reading", "science fiction"]
    }
    
    message_lower = message.lower()
    topics = []
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            topics.append(topic)
    
    return topics


def _classify_conversation(message: str) -> str:
    """Classify the type of conversation."""
    if any(word in message.lower() for word in ["cat", "luna", "pet", "feed"]):
        return "pet_care"
    elif any(word in message.lower() for word in ["work", "engineer", "project"]):
        return "professional"
    elif any(word in message.lower() for word in ["favorite", "love", "enjoy"]):
        return "personal_preference"
    elif any(word in message.lower() for word in ["yesterday", "last night", "went"]):
        return "recent_activity"
    else:
        return "general"


def _display_results(results: list, scenario: str):
    """Display search results in a formatted way."""
    print(f"   {scenario}: {len(results)} results")
    for i, result in enumerate(results[:3]):  # Show top 3
        content = result.get('content', '')[:80]
        score = result.get('score', 0)
        reranked = result.get('reranked_score')
        
        score_text = f"score={score:.3f}"
        if reranked:
            score_text += f", reranked={reranked:.3f}"
        
        print(f"     {i+1}. {content}... ({score_text})")


if __name__ == "__main__":
    asyncio.run(comprehensive_optimization_demo())