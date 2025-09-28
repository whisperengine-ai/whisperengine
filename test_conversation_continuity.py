#!/usr/bin/env python3
"""
Test script for persistent conversation tracking functionality.

This script demonstrates the conversation continuity improvements:
1. Bot asks questions and tracks them
2. User responses are analyzed for answers
3. Natural reminders are generated for unanswered questions
4. Conversation health monitoring
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from src.conversation.persistent_conversation_manager import (
    PersistentConversationManager, 
    QuestionType, 
    QuestionPriority
)
from src.memory.memory_protocol import create_memory_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_conversation_continuity():
    """Test the persistent conversation tracking functionality"""
    
    print("\n🔗 PERSISTENT CONVERSATION TRACKING TEST")
    print("=" * 50)
    
    # Initialize memory manager (mock for testing)
    try:
        memory_manager = create_memory_manager("vector")
        print("✅ Memory manager initialized")
    except Exception as e:
        print(f"⚠️ Could not initialize memory manager: {e}")
        print("📝 Using mock memory manager for testing")
        memory_manager = None
    
    # Initialize persistent conversation manager
    conversation_manager = PersistentConversationManager(memory_manager)
    print("✅ Persistent conversation manager initialized")
    
    # Simulate a conversation scenario
    user_id = "test_user_123"
    print(f"\n🧪 Testing with user ID: {user_id}")
    
    # Test 1: Bot asks some questions
    print("\n📝 TEST 1: Bot asks questions")
    questions_to_track = [
        ("What's your favorite ocean creature?", QuestionType.OPINION, QuestionPriority.MEDIUM),
        ("Have you ever been scuba diving?", QuestionType.PERSONAL, QuestionPriority.LOW),
        ("When did you first become interested in marine life?", QuestionType.FACTUAL, QuestionPriority.MEDIUM),
    ]
    
    tracked_questions = []
    for question_text, q_type, priority in questions_to_track:
        question_id = await conversation_manager.track_bot_question(
            user_id=user_id,
            question_text=question_text,
            question_type=q_type,
            priority=priority,
            current_topic="marine_life"
        )
        tracked_questions.append(question_id)
        print(f"   ✅ Tracked: '{question_text}' -> {question_id}")
    
    # Test 2: User responds to some questions
    print("\n💬 TEST 2: User responds")
    user_responses = [
        "I love dolphins! They're so intelligent and playful.",
        "I've always been fascinated by the ocean since I was a kid.",
    ]
    
    for response in user_responses:
        result = await conversation_manager.process_user_response(
            user_id=user_id,
            user_message=response,
            current_topic="marine_life"
        )
        print(f"   📥 User: '{response[:50]}...'")
        if result["answered_questions"]:
            for answered_q in result["answered_questions"]:
                print(f"   ✅ Resolved: '{answered_q.question_text[:40]}...' (quality: {answered_q.resolution_quality:.2f})")
        else:
            print("   📝 No questions resolved by this response")
    
    # Test 3: Get reminder suggestions
    print("\n🔔 TEST 3: Get reminder suggestions")
    reminders = await conversation_manager.get_reminder_suggestions(user_id)
    if reminders:
        for i, reminder in enumerate(reminders, 1):
            print(f"   💡 Reminder {i}: {reminder}")
    else:
        print("   📝 No reminders needed at this time")
    
    # Test 4: Detect conversation issues
    print("\n🔍 TEST 4: Conversation health check")
    issues = await conversation_manager.detect_conversation_issues(user_id)
    print(f"   📊 Issues found: {len(issues.get('issues', []))}")
    print(f"   📈 Answer ratio: {issues.get('question_answer_ratio', 0.0):.2f}")
    print(f"   🎯 Engagement level: {issues.get('engagement_level', 'unknown')}")
    
    if issues.get('suggestions'):
        print("   💡 Suggestions:")
        for suggestion in issues['suggestions'][:3]:  # Show first 3
            print(f"      - {suggestion}")
    
    print("\n✅ PERSISTENT CONVERSATION TRACKING TEST COMPLETE")
    print(f"📊 Summary:")
    print(f"   - Questions tracked: {len(tracked_questions)}")
    print(f"   - User responses processed: {len(user_responses)}")
    print(f"   - Reminders available: {len(reminders) if reminders else 0}")
    print(f"   - Conversation health: {'Good' if issues.get('question_answer_ratio', 0) > 0.3 else 'Needs improvement'}")

async def main():
    """Main test function"""
    try:
        await test_conversation_continuity()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Persistent Conversation Tracking Test...")
    asyncio.run(main())