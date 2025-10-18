#!/usr/bin/env python3
"""
Test conversation summary integration with prompt building.

This script investigates:
1. Why semantic keys show as "unknown" in search results
2. How conversation summaries appear in the final LLM prompt
3. Whether the summary adds meaningful context vs raw messages
4. If the semantic vector clustering improves relevance
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.memory_protocol import create_memory_manager
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration


async def inspect_qdrant_payload():
    """Check what's actually stored in Qdrant payload for semantic_key field."""
    print("\n" + "="*80)
    print("INSPECTING QDRANT PAYLOAD STRUCTURE")
    print("="*80 + "\n")
    
    memory_manager = create_memory_manager(memory_type="vector")
    test_user_id = "test_summary_user_001"
    
    # Get raw Qdrant points to inspect payload
    from qdrant_client import models
    from src.memory.vector_memory_system import VectorMemoryManager
    
    # Cast to concrete type to access attributes
    if isinstance(memory_manager, VectorMemoryManager):
        # Access via __dict__ or getattr to bypass type checking
        collection_name = getattr(memory_manager, 'collection_name', 'unknown')
        client = getattr(memory_manager, 'client', None)
        
        if not client:
            print("⚠️ Could not access Qdrant client")
            return []
    else:
        print("⚠️ Not using VectorMemoryManager")
        return []
    
    print(f"📦 Collection: {collection_name}\n")
    
    # Scroll to get actual points
    points, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=test_user_id)
                )
            ]
        ),
        limit=5,
        with_payload=True,
        with_vectors=False
    )
    
    print(f"Found {len(points)} points for test user\n")
    
    for i, point in enumerate(points, 1):
        print(f"Point {i}:")
        print(f"  ID: {point.id}")
        print(f"  Payload keys: {list(point.payload.keys())}")
        
        # Check if semantic_key exists
        if 'semantic_key' in point.payload:
            semantic_key = point.payload['semantic_key']
            print(f"  ✅ semantic_key found: '{semantic_key}'")
        else:
            print(f"  ❌ semantic_key NOT in payload")
        
        # Show relevant payload fields
        if 'user_message' in point.payload:
            content = point.payload['user_message'][:80]
            print(f"  Content: {content}...")
        
        if 'memory_type' in point.payload:
            print(f"  Memory type: {point.payload['memory_type']}")
        
        print()
    
    return points


async def test_summary_in_prompt():
    """Test how conversation summary appears in the actual LLM prompt."""
    print("\n" + "="*80)
    print("TESTING SUMMARY INTEGRATION IN LLM PROMPT")
    print("="*80 + "\n")
    
    test_user_id = "test_summary_user_001"
    test_message = "Tell me more about ocean acidification research"
    
    # Create memory manager and CDL integration
    memory_manager = create_memory_manager(memory_type="vector")
    cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
    
    print("🔨 Building character-aware prompt with conversation summary...\n")
    
    # Build the full prompt that would go to the LLM
    # Note: character_name comes from DISCORD_BOT_NAME environment variable
    system_prompt = await cdl_integration.create_unified_character_prompt(
        user_id=test_user_id,
        message_content=test_message
    )
    
    print("="*80)
    print("📜 COMPLETE SYSTEM PROMPT (showing conversation summary section)")
    print("="*80 + "\n")
    
    # Find and extract the conversation summary section
    lines = system_prompt.split('\n')
    in_summary_section = False
    summary_lines = []
    
    for line in lines:
        if '## Recent Conversation Summary' in line or 'Recent conversation topics' in line.lower():
            in_summary_section = True
        elif in_summary_section and line.strip().startswith('##'):
            # Next section starts
            break
        
        if in_summary_section:
            summary_lines.append(line)
    
    if summary_lines:
        print("🎯 CONVERSATION SUMMARY SECTION:")
        print("-" * 80)
        for line in summary_lines:
            print(line)
        print("-" * 80)
    else:
        print("⚠️ No conversation summary section found in prompt")
    
    # Also show recent messages section for comparison
    print("\n" + "="*80)
    print("📝 RECENT MESSAGES SECTION (for comparison)")
    print("="*80 + "\n")
    
    in_messages_section = False
    message_lines = []
    
    for line in lines:
        if 'Recent conversation history' in line or 'Recent messages' in line.lower():
            in_messages_section = True
        elif in_messages_section and line.strip().startswith('##'):
            break
        
        if in_messages_section:
            message_lines.append(line)
    
    if message_lines:
        print("💬 RECENT MESSAGES:")
        print("-" * 80)
        # Show first 20 lines
        for line in message_lines[:20]:
            print(line)
        if len(message_lines) > 20:
            print(f"... ({len(message_lines) - 20} more lines)")
        print("-" * 80)
    
    return system_prompt


async def compare_with_and_without_summary():
    """Compare prompt tokens and relevance with vs without summary."""
    print("\n" + "="*80)
    print("COMPARING PROMPT WITH AND WITHOUT SUMMARY")
    print("="*80 + "\n")
    
    test_user_id = "test_summary_user_001"
    test_message = "Tell me more about ocean acidification research"
    
    memory_manager = create_memory_manager(memory_type="vector")
    cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
    
    # Get prompt WITH summary (default)
    prompt_with_summary = await cdl_integration.create_unified_character_prompt(
        user_id=test_user_id,
        message_content=test_message
    )
    
    # Count tokens (rough approximation: 1 token ≈ 4 chars)
    tokens_with_summary = len(prompt_with_summary) // 4
    
    # Count lines
    lines_with_summary = len(prompt_with_summary.split('\n'))
    
    print("📊 PROMPT STATISTICS:")
    print(f"  Characters: {len(prompt_with_summary):,}")
    print(f"  Estimated tokens: {tokens_with_summary:,}")
    print(f"  Lines: {lines_with_summary}")
    print()
    
    # Analyze content
    has_summary = "Recent Conversation Summary" in prompt_with_summary or "conversation topics" in prompt_with_summary.lower()
    has_themes = "Themes:" in prompt_with_summary or "academic_research" in prompt_with_summary
    
    print("📋 CONTENT ANALYSIS:")
    print(f"  ✅ Has summary section: {has_summary}")
    print(f"  ✅ Has conversation themes: {has_themes}")
    print()
    
    # Extract summary content
    if "Topic Summary:" in prompt_with_summary:
        summary_start = prompt_with_summary.find("Topic Summary:")
        summary_end = prompt_with_summary.find("\n\n", summary_start)
        if summary_end == -1:
            summary_end = summary_start + 500
        summary_text = prompt_with_summary[summary_start:summary_end]
        
        print("📝 EXTRACTED SUMMARY:")
        print("-" * 80)
        print(summary_text)
        print("-" * 80)
        print()
    
    # Also check for the CONVERSATION BACKGROUND section
    if "📚 CONVERSATION BACKGROUND:" in prompt_with_summary:
        print("✅ FOUND '📚 CONVERSATION BACKGROUND:' section!")
        bg_start = prompt_with_summary.find("📚 CONVERSATION BACKGROUND:")
        bg_end = prompt_with_summary.find("\n\n", bg_start)
        if bg_end == -1:
            bg_end = bg_start + 500
        bg_text = prompt_with_summary[bg_start:bg_end]
        print(bg_text)
        print()
    else:
        print("❌ '📚 CONVERSATION BACKGROUND:' section NOT FOUND")
        print()
        print("Searching for 'conversation' in prompt...")
        conv_count = prompt_with_summary.lower().count('conversation')
        print(f"   Found 'conversation' {conv_count} times")
        print()
    
    return prompt_with_summary


async def test_semantic_clustering_quality():
    """Test if semantic vector actually improves conversation retrieval."""
    print("\n" + "="*80)
    print("TESTING SEMANTIC CLUSTERING VS CONTENT SEARCH")
    print("="*80 + "\n")
    
    memory_manager = create_memory_manager(memory_type="vector")
    test_user_id = "test_summary_user_001"
    
    test_queries = [
        "Tell me about ocean acidification",
        "I'm feeling anxious about my thesis",
        "What do you think about diving?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: \"{query}\"")
        print("-" * 80)
        
        # Get relevant memories (uses multi-vector search)
        memories = await memory_manager.retrieve_relevant_memories(
            user_id=test_user_id,
            query=query,
            limit=5
        )
        
        print(f"\nFound {len(memories)} relevant memories:\n")
        
        for i, memory in enumerate(memories, 1):
            # Extract content
            content = memory.get('user_message', '')[:100]
            semantic_key = memory.get('semantic_key', 'unknown')
            
            print(f"{i}. Semantic key: {semantic_key}")
            print(f"   Content: {content}...")
            print()
        
        # Check if results are topically coherent
        semantic_keys = [m.get('semantic_key', 'unknown') for m in memories]
        unique_keys = set(semantic_keys)
        
        print(f"📊 Topic diversity: {len(unique_keys)} unique semantic keys")
        print(f"   Keys: {', '.join(unique_keys)}")
        print()


async def full_pipeline_test():
    """Test the full pipeline: storage → retrieval → summary → prompt."""
    print("\n" + "="*80)
    print("FULL PIPELINE TEST: STORAGE → RETRIEVAL → SUMMARY → PROMPT")
    print("="*80 + "\n")
    
    memory_manager = create_memory_manager(memory_type="vector")
    test_user_id = "test_summary_user_001"
    
    # Step 1: Check storage
    print("1️⃣ STORAGE CHECK")
    print("-" * 80)
    history = await memory_manager.get_conversation_history(
        user_id=test_user_id,
        limit=10
    )
    print(f"✅ Found {len(history)} stored conversations\n")
    
    # Step 2: Check retrieval with semantic vector
    print("2️⃣ RETRIEVAL CHECK (Semantic Vector)")
    print("-" * 80)
    memories = await memory_manager.retrieve_relevant_memories(
        user_id=test_user_id,
        query="ocean acidification",
        limit=5
    )
    print(f"✅ Retrieved {len(memories)} relevant memories")
    
    marine_biology_count = sum(
        1 for m in memories 
        if any(keyword in str(m).lower() for keyword in ['ocean', 'coral', 'reef', 'ph', 'acidification'])
    )
    print(f"   Marine biology related: {marine_biology_count}/{len(memories)}\n")
    
    # Step 3: Check summary generation
    print("3️⃣ SUMMARY GENERATION CHECK")
    print("-" * 80)
    
    # Get conversation history first
    conversation_history = await memory_manager.get_conversation_history(
        user_id=test_user_id,
        limit=20
    )
    
    summary_result = await memory_manager.get_conversation_summary_with_recommendations(
        user_id=test_user_id,
        conversation_history=conversation_history,
        limit=5  # Number of summary sentences
    )
    
    print(f"✅ Summary generated:")
    print(f"   Method: {summary_result.get('method', 'unknown')}")
    print(f"   Themes: {summary_result.get('conversation_themes', [])}")
    print(f"   Summary length: {len(summary_result.get('topic_summary', ''))} chars\n")
    
    # Step 4: Check prompt integration
    print("4️⃣ PROMPT INTEGRATION CHECK")
    print("-" * 80)
    cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)
    prompt = await cdl_integration.create_unified_character_prompt(
        user_id=test_user_id,
        message_content="Tell me about your research"
    )
    
    # Check for summary section (updated to match actual format)
    has_summary = ("📚 CONVERSATION BACKGROUND:" in prompt or 
                   "Topic Summary:" in prompt or 
                   "conversation topics" in prompt.lower())
    has_themes = any(theme in prompt for theme in summary_result.get('conversation_themes', []))
    
    print(f"✅ Prompt built:")
    print(f"   Contains summary: {has_summary}")
    print(f"   Contains themes: {has_themes}")
    print(f"   Total length: {len(prompt):,} chars\n")
    
    # Step 5: Validate end-to-end
    print("5️⃣ END-TO-END VALIDATION")
    print("-" * 80)
    
    checks = {
        "Storage working": len(history) > 0,
        "Retrieval working": len(memories) > 0,
        "Semantic clustering": marine_biology_count >= 3,
        "Summary generation": len(summary_result.get('topic_summary', '')) > 0,
        "Themes detected": len(summary_result.get('conversation_themes', [])) > 0,
        "Prompt integration": has_summary and has_themes
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
    
    print()
    print("="*80)
    print(f"FINAL SCORE: {passed}/{total} checks passed")
    print("="*80)
    
    if passed == total:
        print("🎉 EXCELLENT - Full pipeline working perfectly!")
    elif passed >= total * 0.8:
        print("✅ GOOD - Pipeline working with minor issues")
    else:
        print("⚠️ NEEDS IMPROVEMENT - Pipeline has significant issues")
    
    return checks


async def main():
    """Run all investigation tests."""
    print("\n" + "="*80)
    print("CONVERSATION SUMMARY INVESTIGATION")
    print("Testing semantic keys, prompt integration, and LLM value")
    print("="*80)
    
    try:
        # Test 1: Inspect Qdrant payload
        print("\n🔍 TEST 1: Qdrant Payload Structure")
        await inspect_qdrant_payload()
        
        # Test 2: Summary in prompt
        print("\n🔍 TEST 2: Summary in LLM Prompt")
        await test_summary_in_prompt()
        
        # Test 3: Compare with/without summary
        print("\n🔍 TEST 3: Prompt Comparison")
        await compare_with_and_without_summary()
        
        # Test 4: Semantic clustering quality
        print("\n🔍 TEST 4: Semantic Clustering Quality")
        await test_semantic_clustering_quality()
        
        # Test 5: Full pipeline
        print("\n🔍 TEST 5: Full Pipeline Test")
        checks = await full_pipeline_test()
        
        print("\n" + "="*80)
        print("INVESTIGATION COMPLETE")
        print("="*80)
        
        return checks
        
    except Exception as e:
        print(f"\n❌ Investigation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return {}


if __name__ == "__main__":
    results = asyncio.run(main())
