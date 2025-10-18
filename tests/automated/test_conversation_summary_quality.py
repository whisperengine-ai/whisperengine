#!/usr/bin/env python3
"""
Test conversation summary quality and usefulness.

Tests the get_conversation_summary_with_recommendations() method to ensure
summaries are actually helpful and not just generic templates.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.memory_protocol import create_memory_manager

async def test_conversation_summary():
    """Test conversation summary generation with realistic data."""
    
    print("🧪 TESTING CONVERSATION SUMMARY QUALITY\n")
    
    # Create memory manager
    memory_manager = create_memory_manager(memory_type="vector")
    
    # Test user
    test_user_id = "test_user_summary_001"
    
    # Realistic conversation history with RoBERTa emotion context
    test_conversations = [
        {
            "id": "msg_001",
            "role": "user",
            "content": "I've been feeling really anxious about my marine biology thesis. The ocean acidification data isn't matching my hypothesis.",
            "timestamp": "2025-10-18T10:00:00Z"
        },
        {
            "id": "msg_002", 
            "role": "assistant",
            "content": "That's a common challenge in marine research! Ocean systems are incredibly complex. Tell me more about what patterns you're seeing in your data.",
            "timestamp": "2025-10-18T10:01:00Z"
        },
        {
            "id": "msg_003",
            "role": "user", 
            "content": "The pH levels are dropping faster in the coral reef zones than in open water. I expected the opposite based on current models.",
            "timestamp": "2025-10-18T10:02:00Z"
        },
        {
            "id": "msg_004",
            "role": "assistant",
            "content": "Fascinating! Coral reef zones have complex microclimates. Have you considered the impact of coral respiration on local pH levels?",
            "timestamp": "2025-10-18T10:03:00Z"
        },
        {
            "id": "msg_005",
            "role": "user",
            "content": "Oh wow, I hadn't thought about coral respiration! That could explain the localized acidification patterns.",
            "timestamp": "2025-10-18T10:04:00Z"
        }
    ]
    
    print("📝 Test conversation:")
    for msg in test_conversations[-3:]:
        role = "USER" if msg["role"] == "user" else "BOT"
        content_preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
        print(f"  {role}: {content_preview}")
    print()
    
    # Generate summary
    print("🔍 Generating conversation summary with FastEmbed extractive method...")
    print("   (This uses semantic sentence centrality scoring)")
    summary_data = await memory_manager.get_conversation_summary_with_recommendations(
        user_id=test_user_id,
        conversation_history=test_conversations,
        limit=20
    )
    
    print("\n📊 SUMMARY RESULTS:")
    print("=" * 80)
    
    # Display all returned data
    for key, value in summary_data.items():
        print(f"\n{key}:")
        print(f"  {value}")
    
    print("\n" + "=" * 80)
    
    # Quality assessment
    print("\n🎯 QUALITY ASSESSMENT:")
    
    topic_summary = summary_data.get('topic_summary', '')
    themes = summary_data.get('conversation_themes', '')
    
    issues = []
    
    # Check for generic/useless phrases
    generic_phrases = [
        'general conversation',
        'continuing conversation', 
        'discussing general',
        'focused on general'
    ]
    
    if any(phrase in topic_summary.lower() for phrase in generic_phrases):
        issues.append("❌ Summary contains generic phrase")
    else:
        print("✅ No generic phrases")
    
    # Check for actual content
    if len(topic_summary) < 20:
        issues.append("❌ Summary too short to be useful")
    else:
        print("✅ Summary has reasonable length")
    
    # Check if keywords are meaningful
    if '(topics:' in topic_summary:
        keywords_part = topic_summary.split('(topics:')[1].split(')')[0]
        keywords = [k.strip() for k in keywords_part.split(',')]
        
        # Check if keywords are actually from the conversation
        conversation_text = ' '.join([msg['content'].lower() for msg in test_conversations])
        meaningful_keywords = [k for k in keywords if k in conversation_text]
        
        if len(meaningful_keywords) < len(keywords) * 0.5:
            issues.append(f"❌ Keywords not relevant to conversation: {keywords}")
        else:
            print(f"✅ Keywords are relevant: {keywords}")
    
    # Check theme detection
    if themes == 'general':
        issues.append("❌ Theme detection failed - marked as 'general'")
    else:
        print(f"✅ Specific theme detected: {themes}")
    
    # Expected: Should detect research/academic theme, anxiety emotion, marine biology topic
    conversation_keywords = ['anxious', 'thesis', 'ocean', 'acidification', 'research', 'coral', 'reef']
    found_keywords = [k for k in conversation_keywords if k in topic_summary.lower() or k in themes.lower()]
    
    if len(found_keywords) < 2:
        issues.append(f"❌ Summary missed key conversation topics. Found only: {found_keywords}")
    else:
        print(f"✅ Summary captures key topics: {found_keywords}")
    
    print("\n" + "=" * 80)
    
    if issues:
        print("\n⚠️ ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print("\n❌ SUMMARY QUALITY: NEEDS IMPROVEMENT")
        return False
    else:
        print("\n✅ SUMMARY QUALITY: GOOD")
        return True

async def test_empty_history():
    """Test summary with empty conversation history."""
    print("\n" + "=" * 80)
    print("🧪 TESTING EMPTY CONVERSATION HISTORY")
    print("=" * 80 + "\n")
    
    memory_manager = create_memory_manager(memory_type="vector")
    
    summary_data = await memory_manager.get_conversation_summary_with_recommendations(
        user_id="test_user",
        conversation_history=[],
        limit=5
    )
    
    print("📊 Result:")
    print(f"  topic_summary: {summary_data.get('topic_summary')}")
    print(f"  method: {summary_data.get('recommendation_method')}")
    
    if summary_data.get('recommendation_method') == 'empty_history':
        print("\n✅ Empty history handled correctly")
        return True
    else:
        print("\n❌ Empty history not handled properly")
        return False

async def main():
    """Run all summary quality tests."""
    
    print("=" * 80)
    print("CONVERSATION SUMMARY QUALITY TEST")
    print("=" * 80)
    print()
    
    results = []
    
    # Test 1: Quality with realistic conversation
    try:
        result = await test_conversation_summary()
        results.append(("Quality Test", result))
    except Exception as e:
        print(f"\n❌ Quality test failed with error: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Quality Test", False))
    
    # Test 2: Empty history
    try:
        result = await test_empty_history()
        results.append(("Empty History Test", result))
    except Exception as e:
        print(f"\n❌ Empty history test failed with error: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Empty History Test", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n⚠️ SOME TESTS FAILED - Summary needs improvement")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
