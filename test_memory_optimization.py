#!/usr/bin/env python3
"""
Memory Optimization Integration Test
Tests if the new memory optimization components work together
"""
import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test importing our new memory optimization components
    from src.memory.context_prioritizer import (
        ContextItem,
        ContextType,
        IntelligentContextPrioritizer,
    )
    from src.memory.conversation_summarizer import (
        AdvancedConversationSummarizer,
        ConversationSummary,
    )
    from src.memory.semantic_deduplicator import MemoryFingerprint, SemanticMemoryDeduplicator
    from src.memory.topic_clusterer import AdvancedTopicClusterer, TopicCluster


except ImportError:
    sys.exit(1)


# Mock components for testing
class MockLLMClient:
    """Mock LLM client for testing"""

    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Mock response generation"""
        if "summarize" in prompt.lower():
            return """
            {
                "summary": "User discussed Python programming and asked about debugging techniques.",
                "key_topics": ["Python", "debugging", "programming"],
                "important_facts": ["User is working on a web application", "Having issues with async code"],
                "emotional_evolution": "curious → frustrated → hopeful"
            }
            """
        elif "topics" in prompt.lower():
            return """
            {
                "topics": ["Python programming", "debugging", "web development"],
                "description": "Technical programming discussion"
            }
            """
        else:
            return "This is a mock response for testing purposes."


class MockEmbeddingManager:
    """Mock embedding manager for testing"""

    def generate_embedding(self, text: str) -> list[float]:
        """Generate mock embedding based on text hash"""
        import hashlib
        import random

        # Create deterministic "embedding" based on text
        hash_obj = hashlib.md5(text.encode())
        random.seed(int(hash_obj.hexdigest(), 16) % (2**32))

        # Generate 384-dimensional mock embedding
        return [random.uniform(-1, 1) for _ in range(384)]

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate batch embeddings"""
        return [self.generate_embedding(text) for text in texts]


class MockMemoryManager:
    """Mock memory manager for testing"""

    def __init__(self):
        self.stored_facts = []

    async def extract_facts_from_text(self, text: str) -> list[str]:
        """Mock fact extraction"""
        facts = []
        if "python" in text.lower():
            facts.append("User is learning Python programming")
        if "debug" in text.lower():
            facts.append("User needs help with debugging")
        if "web" in text.lower():
            facts.append("User is building web applications")
        return facts


async def test_conversation_summarizer():
    """Test conversation summarization functionality"""

    llm_client = MockLLMClient()
    memory_manager = MockMemoryManager()

    summarizer = AdvancedConversationSummarizer(
        llm_client=llm_client, memory_manager=memory_manager
    )

    # Test messages
    test_messages = [
        {
            "user_id": "test_user",
            "content": "I'm having trouble with my Python web application",
            "timestamp": "2025-09-15T10:00:00Z",
            "role": "user",
        },
        {
            "user_id": "assistant",
            "content": "I can help with that! What specific issues are you facing?",
            "timestamp": "2025-09-15T10:01:00Z",
            "role": "assistant",
        },
        {
            "user_id": "test_user",
            "content": "My async functions aren't working properly in the web framework",
            "timestamp": "2025-09-15T10:02:00Z",
            "role": "user",
        },
    ]

    # Test summarization
    try:
        await summarizer.should_summarize_conversation("test_user", test_messages)

        if len(test_messages) >= 3:  # Force summarization for testing
            await summarizer.create_conversation_summary("test_user", test_messages)
        else:
            pass

    except Exception:
        return False

    return True


async def test_semantic_deduplicator():
    """Test semantic deduplication functionality"""

    embedding_manager = MockEmbeddingManager()
    deduplicator = SemanticMemoryDeduplicator(embedding_manager=embedding_manager)

    # Test memories with some duplicates
    test_memories = [
        {
            "memory_id": "mem_1",
            "content": "User is learning Python programming",
            "user_id": "test_user",
            "timestamp": "2025-09-15T10:00:00Z",
        },
        {
            "memory_id": "mem_2",
            "content": "User wants to learn Python development",  # Similar to mem_1
            "user_id": "test_user",
            "timestamp": "2025-09-15T10:05:00Z",
        },
        {
            "memory_id": "mem_3",
            "content": "User is working on web applications",
            "user_id": "test_user",
            "timestamp": "2025-09-15T10:10:00Z",
        },
    ]

    try:
        await deduplicator.optimize_memory_collection(memories=test_memories, user_id="test_user")

    except Exception:
        return False

    return True


async def test_topic_clusterer():
    """Test topic clustering functionality"""

    llm_client = MockLLMClient()
    embedding_manager = MockEmbeddingManager()

    clusterer = AdvancedTopicClusterer(llm_client=llm_client, embedding_manager=embedding_manager)

    # Test topics for clustering
    test_topics = [
        "Python programming",
        "Web development",
        "Machine learning",
        "Python debugging",
        "JavaScript programming",
        "Database design",
        "Python web frameworks",
        "API development",
    ]

    test_memories = [
        {
            "memory_id": f"mem_{i}",
            "content": f"Discussion about {topic}",
            "topic": topic,
            "user_id": "test_user",
            "timestamp": datetime.now().isoformat(),
            "embedding": embedding_manager.generate_embedding(topic),
        }
        for i, topic in enumerate(test_topics)
    ]

    try:
        clustering_result = await clusterer.create_intelligent_clusters(
            memories=test_memories, user_id="test_user"
        )

        if clustering_result["clusters"]:
            for _i, _cluster in enumerate(clustering_result["clusters"][:3]):
                pass

    except Exception:
        return False

    return True


async def test_context_prioritizer():
    """Test context prioritization functionality"""

    embedding_manager = MockEmbeddingManager()
    prioritizer = IntelligentContextPrioritizer(embedding_manager=embedding_manager)

    # Test context items
    test_context = [
        {
            "id": "ctx_1",
            "content": "User is learning Python programming and web development",
            "type": "conversation",
            "timestamp": "2025-09-15T10:00:00Z",
            "keywords": ["Python", "programming", "web"],
            "embedding": embedding_manager.generate_embedding("Python programming web"),
        },
        {
            "id": "ctx_2",
            "content": "User feels excited about their new project",
            "type": "emotional",
            "timestamp": "2025-09-15T09:30:00Z",
            "keywords": ["excited", "project"],
            "embedding": embedding_manager.generate_embedding("excited project"),
        },
        {
            "id": "ctx_3",
            "content": "User completed a JavaScript course last month",
            "type": "fact",
            "timestamp": "2025-08-15T10:00:00Z",
            "keywords": ["JavaScript", "course", "completed"],
            "embedding": embedding_manager.generate_embedding("JavaScript course completed"),
        },
    ]

    try:
        # Test prioritization
        query = "I need help with Python web development"
        prioritized_context = await prioritizer.prioritize_context(
            query=query, user_id="test_user", available_context=test_context, context_limit=10
        )

        for _i, _item in enumerate(prioritized_context):
            pass

        # Test context recommendations
        await prioritizer.get_context_recommendations(
            user_id="test_user", recent_topics=["Python", "programming"], limit=5
        )

    except Exception:
        return False

    return True


async def test_integration():
    """Test integration between all components"""

    # Create all components
    llm_client = MockLLMClient()
    embedding_manager = MockEmbeddingManager()
    memory_manager = MockMemoryManager()

    summarizer = AdvancedConversationSummarizer(llm_client, memory_manager, embedding_manager)
    deduplicator = SemanticMemoryDeduplicator(embedding_manager)
    clusterer = AdvancedTopicClusterer(llm_client, embedding_manager)
    prioritizer = IntelligentContextPrioritizer(embedding_manager)

    # Test workflow: conversation → summarization → deduplication → clustering → prioritization
    try:
        # 1. Create conversation to summarize
        messages = [
            {
                "user_id": "test_user",
                "content": "I want to learn Python",
                "timestamp": "2025-09-15T10:00:00Z",
                "role": "user",
            },
            {
                "user_id": "assistant",
                "content": "Great! Python is excellent for beginners",
                "timestamp": "2025-09-15T10:01:00Z",
                "role": "assistant",
            },
            {
                "user_id": "test_user",
                "content": "What about web development with Python?",
                "timestamp": "2025-09-15T10:02:00Z",
                "role": "user",
            },
        ]

        # 2. Summarize conversation
        summary = await summarizer.create_conversation_summary("test_user", messages)

        # 3. Create memory items for deduplication
        memories = [
            {
                "memory_id": "mem_1",
                "content": summary.summary_text,
                "user_id": "test_user",
                "timestamp": summary.timestamp_end,
            },
            {
                "memory_id": "mem_2",
                "content": "User wants to learn Python programming",
                "user_id": "test_user",
                "timestamp": "2025-09-15T09:00:00Z",
            },
        ]

        # 4. Deduplicate memories
        await deduplicator.optimize_memory_collection(memories, "test_user")

        # 5. Cluster topics
        cluster_memories = [
            {
                "memory_id": "mem_1",
                "content": "Python programming discussion",
                "topic": "Python",
                "user_id": "test_user",
                "timestamp": datetime.now().isoformat(),
                "embedding": embedding_manager.generate_embedding("Python programming"),
            }
        ]

        await clusterer.create_intelligent_clusters(cluster_memories, "test_user")

        # 6. Prioritize context
        context_items = [
            {
                "id": "ctx_1",
                "content": summary.summary_text,
                "type": "summary",
                "timestamp": summary.timestamp_end,
                "embedding": embedding_manager.generate_embedding(summary.summary_text),
            }
        ]

        await prioritizer.prioritize_context("Python web development", "test_user", context_items)

        return True

    except Exception:
        return False


async def main():
    """Run all tests"""

    tests = [
        ("Conversation Summarizer", test_conversation_summarizer),
        ("Semantic Deduplicator", test_semantic_deduplicator),
        ("Topic Clusterer", test_topic_clusterer),
        ("Context Prioritizer", test_context_prioritizer),
        ("Component Integration", test_integration),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception:
            results[test_name] = False

    # Summary

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        pass

    if passed == total:
        return True
    else:
        return False


if __name__ == "__main__":
    asyncio.run(main())
