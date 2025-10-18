#!/usr/bin/env python3
"""
Test conversation summary quality with LIVE data.

This script:
1. Stores test conversations with NEW semantic key extraction
2. Retrieves conversation history
3. Tests summary generation quality
4. Validates semantic topic clustering
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.memory_protocol import create_memory_manager

async def store_test_conversations():
    """Store test conversations to build fresh semantic vector clusters."""
    
    print("=" * 80)
    print("STORING TEST CONVERSATIONS WITH NEW SEMANTIC KEYS")
    print("=" * 80)
    print()
    
    memory_manager = create_memory_manager(memory_type="vector")
    test_user_id = "test_summary_user_001"
    
    # Test conversations covering different semantic topics
    test_conversations = [
        # Topic 1: Marine Biology (academic_research / marine_biology)
        {
            "user": "I'm studying ocean acidification and its impact on coral reefs",
            "bot": "That's fascinating research! Ocean acidification is one of the most pressing issues facing marine ecosystems. What specific aspects are you focusing on?",
            "topic": "marine_biology"
        },
        {
            "user": "The pH levels in my research area are dropping faster than expected",
            "bot": "That's concerning. Have you been able to identify any localized factors that might be accelerating the acidification in your study site?",
            "topic": "marine_biology"
        },
        {
            "user": "I'm analyzing how coral respiration affects local pH measurements",
            "bot": "Excellent approach! Coral respiration can definitely create microclimates with different pH levels. Are you seeing patterns between day and night cycles?",
            "topic": "marine_biology"
        },
        
        # Topic 2: Academic Anxiety (academic_anxiety)
        {
            "user": "I'm feeling really anxious about my thesis deadline next month",
            "bot": "Thesis deadlines can definitely be stressful. What's causing you the most concern right now?",
            "topic": "academic_anxiety"
        },
        {
            "user": "My data analysis is taking longer than I expected and I'm worried I won't finish",
            "bot": "That's a common challenge in research. Have you talked with your advisor about potentially adjusting your timeline or scope?",
            "topic": "academic_anxiety"
        },
        
        # Topic 3: Personal Interests (marine_biology but different context)
        {
            "user": "I went diving last weekend and saw the most beautiful reef ecosystem",
            "bot": "That sounds amazing! What made this dive particularly special for you?",
            "topic": "marine_biology"
        },
        {
            "user": "The biodiversity was incredible - I counted over 30 species of fish",
            "bot": "Wow, that's a rich ecosystem! Were you able to identify any indicator species that suggest the reef's health?",
            "topic": "marine_biology"
        },
        
        # Topic 4: Learning Discovery
        {
            "user": "I just realized that wave action might be affecting my pH measurements!",
            "bot": "That's a great insight! Wave action can definitely influence water mixing and localized chemistry. How do you plan to account for this in your analysis?",
            "topic": "learning_discovery"
        }
    ]
    
    print(f"Storing {len(test_conversations)} test conversations...\n")
    
    for i, convo in enumerate(test_conversations, 1):
        user_msg = convo["user"]
        bot_response = convo["bot"]
        expected_topic = convo["topic"]
        
        print(f"Conversation {i}/{len(test_conversations)}:")
        print(f"  User: {user_msg[:60]}...")
        print(f"  Bot: {bot_response[:60]}...")
        print(f"  Expected topic: {expected_topic}")
        
        # Store conversation
        success = await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message=user_msg,
            bot_response=bot_response
        )
        
        if success:
            print(f"  ✅ Stored successfully")
        else:
            print(f"  ❌ Storage failed")
        
        print()
        
        # Small delay to ensure ordering
        await asyncio.sleep(0.1)
    
    print("=" * 80)
    print(f"✅ Stored {len(test_conversations)} conversations")
    print("=" * 80)
    print()
    
    return test_user_id, test_conversations

async def test_conversation_summary(test_user_id: str):
    """Test conversation summary generation with fresh data."""
    
    print("=" * 80)
    print("TESTING CONVERSATION SUMMARY GENERATION")
    print("=" * 80)
    print()
    
    memory_manager = create_memory_manager(memory_type="vector")
    
    # Get recent conversation history
    print("📝 Retrieving recent conversation history...")
    recent_messages = await memory_manager.get_conversation_history(
        user_id=test_user_id,
        limit=20
    )
    
    print(f"   Retrieved {len(recent_messages)} messages\n")
    
    if not recent_messages:
        print("❌ No conversation history found!")
        return False
    
    # Display recent messages
    print("Recent conversation context:")
    for i, msg in enumerate(recent_messages[-6:], 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:70]
        print(f"  {i}. [{role}] {content}...")
    print()
    
    # Generate summary
    print("🔍 Generating conversation summary...\n")
    
    summary_data = await memory_manager.vector_store.get_conversation_summary_with_recommendations(
        user_id=test_user_id,
        conversation_history=recent_messages,
        limit=20
    )
    
    # Display results
    print("=" * 80)
    print("📊 SUMMARY RESULTS")
    print("=" * 80)
    print()
    
    print(f"Topic Summary:")
    print(f"  {summary_data.get('topic_summary', 'N/A')}")
    print()
    
    print(f"Conversation Themes:")
    print(f"  {summary_data.get('conversation_themes', 'N/A')}")
    print()
    
    print(f"Method:")
    print(f"  {summary_data.get('recommendation_method', 'N/A')}")
    print()
    
    print(f"Sentences Analyzed:")
    print(f"  {summary_data.get('sentences_analyzed', 0)}")
    print()
    
    print(f"Emotions Detected:")
    print(f"  {summary_data.get('emotions_detected', 0)}")
    print()
    
    # Quality assessment
    print("=" * 80)
    print("🎯 QUALITY ASSESSMENT")
    print("=" * 80)
    print()
    
    topic_summary = summary_data.get('topic_summary', '')
    themes = summary_data.get('conversation_themes', '')
    
    checks_passed = 0
    total_checks = 5
    
    # Check 1: Not empty
    if topic_summary and len(topic_summary) > 20:
        print("✅ Summary has meaningful content")
        checks_passed += 1
    else:
        print("❌ Summary is empty or too short")
    
    # Check 2: Not generic
    generic_phrases = ['general conversation', 'continuing conversation', 'general']
    if not any(phrase in topic_summary.lower() for phrase in generic_phrases):
        print("✅ No generic phrases")
        checks_passed += 1
    else:
        print("❌ Contains generic phrases")
    
    # Check 3: Specific themes
    if themes != 'general':
        print(f"✅ Specific themes detected: {themes}")
        checks_passed += 1
    else:
        print("❌ Generic theme detected")
    
    # Check 4: Expected topics present
    expected_topics = ['marine', 'biology', 'academic', 'research', 'thesis', 'coral', 'ocean']
    found_topics = [topic for topic in expected_topics 
                    if topic in topic_summary.lower() or topic in themes.lower()]
    
    if len(found_topics) >= 2:
        print(f"✅ Expected topics found: {found_topics}")
        checks_passed += 1
    else:
        print(f"⚠️  Few expected topics found: {found_topics}")
    
    # Check 5: Uses extractive method
    if summary_data.get('recommendation_method') == 'fastembed_extractive':
        print("✅ Using FastEmbed extractive method")
        checks_passed += 1
    else:
        print("⚠️  Not using FastEmbed extractive method")
    
    print()
    print("=" * 80)
    print(f"SCORE: {checks_passed}/{total_checks} checks passed")
    print("=" * 80)
    
    if checks_passed >= 4:
        print("\n🎉 EXCELLENT - Summary quality is high!")
        return True
    elif checks_passed >= 3:
        print("\n✅ GOOD - Summary quality is acceptable")
        return True
    else:
        print("\n⚠️  NEEDS IMPROVEMENT - Summary quality is low")
        return False

async def test_semantic_clustering(test_user_id: str):
    """Test that semantic vector properly clusters related topics."""
    
    print("\n" + "=" * 80)
    print("TESTING SEMANTIC VECTOR CLUSTERING")
    print("=" * 80)
    print()
    
    memory_manager = create_memory_manager(memory_type="vector")
    
    # Search for marine biology topics using semantic vector
    print("🔍 Searching for marine biology topics using semantic vector...\n")
    
    query = "Tell me about ocean acidification research"
    
    # Get semantic key for query
    semantic_key = memory_manager.vector_store._get_semantic_key(query)
    print(f"Query semantic key: {semantic_key}\n")
    
    # Retrieve memories (should use semantic vector routing)
    memories = await memory_manager.retrieve_relevant_memories(
        user_id=test_user_id,
        query=query,
        limit=10
    )
    
    print(f"Found {len(memories)} relevant memories:\n")
    
    marine_count = 0
    for i, memory in enumerate(memories[:5], 1):
        content = memory.get('content', '')[:80]
        score = memory.get('score', 0)
        semantic_key_stored = memory.get('metadata', {}).get('semantic_key', 'unknown')
        
        print(f"{i}. Score: {score:.3f}")
        print(f"   Semantic key: {semantic_key_stored}")
        print(f"   Content: {content}...")
        print()
        
        if any(word in content.lower() for word in ['marine', 'ocean', 'coral', 'reef', 'ph']):
            marine_count += 1
    
    print("=" * 80)
    print(f"Marine biology related: {marine_count}/{min(5, len(memories))} results")
    print("=" * 80)
    
    if marine_count >= 3:
        print("\n✅ EXCELLENT - Semantic clustering working well!")
        return True
    elif marine_count >= 2:
        print("\n✅ GOOD - Semantic clustering is functional")
        return True
    else:
        print("\n⚠️  Semantic clustering may need improvement")
        return False

async def main():
    """Run all conversation summary tests."""
    
    print("=" * 80)
    print("LIVE CONVERSATION SUMMARY QUALITY TEST")
    print("=" * 80)
    print()
    
    try:
        # Step 1: Store test conversations
        test_user_id, conversations = await store_test_conversations()
        
        # Small delay to ensure indexing
        print("⏳ Waiting for indexing...\n")
        await asyncio.sleep(2)
        
        # Step 2: Test summary generation
        summary_passed = await test_conversation_summary(test_user_id)
        
        # Step 3: Test semantic clustering
        clustering_passed = await test_semantic_clustering(test_user_id)
        
        # Final results
        print("\n" + "=" * 80)
        print("FINAL RESULTS")
        print("=" * 80)
        print()
        
        if summary_passed:
            print("✅ Summary Generation: PASSED")
        else:
            print("❌ Summary Generation: NEEDS IMPROVEMENT")
        
        if clustering_passed:
            print("✅ Semantic Clustering: PASSED")
        else:
            print("⚠️  Semantic Clustering: NEEDS IMPROVEMENT")
        
        print()
        
        if summary_passed and clustering_passed:
            print("🎉 ALL TESTS PASSED - Conversation summary system working excellently!")
            sys.exit(0)
        elif summary_passed or clustering_passed:
            print("✅ PARTIAL SUCCESS - Core functionality working")
            sys.exit(0)
        else:
            print("❌ TESTS FAILED - System needs debugging")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
