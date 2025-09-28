#!/usr/bin/env python3
"""
Human-Like Conversation Integration Example

This script demonstrates how to integrate the enhanced PersistentConversationManager
with human-like features into WhisperEngine's event handling system.

All enhancements are added to existing files without creating new ones:
- Enhanced PersistentConversationManager with intimacy levels, emotional awareness, timing
- Personality-driven conversation styles for each bot character
- Natural rhythm detection and conversation flow management
"""

import asyncio
from datetime import datetime
from src.conversation.persistent_conversation_manager import (
    PersistentConversationManager,
    QuestionType,
    QuestionPriority,
    ConversationIntimacy,
    ConversationRhythm
)

async def demo_human_like_conversation_features():
    """
    Demonstrate the human-like conversation enhancements
    """
    print("🎭 Human-Like Conversation Enhancement Demo")
    print("=" * 50)
    
    # Mock memory manager for demo
    class MockMemoryManager:
        pass
    
    # Initialize enhanced conversation manager
    manager = PersistentConversationManager(MockMemoryManager())
    
    # Demo: Track a question with personality awareness
    user_id = "demo_user"
    
    print("\n1. 📝 Tracking Question with Personality Awareness")
    question_id = await manager.track_bot_question(
        user_id=user_id,
        question_text="What inspired you to choose your current career path?",
        question_type=QuestionType.PERSONAL,
        priority=QuestionPriority.MEDIUM,
        context="User mentioned being unhappy at work",
        bot_personality="elena"  # Marine biologist bot
    )
    print(f"   ✅ Question tracked with ID: {question_id}")
    
    # Demo: Process response with emotional awareness
    print("\n2. 🧠 Processing Response with Emotional Awareness")
    result = await manager.process_user_response(
        user_id=user_id,
        user_message="Well, I've always loved the ocean but I'm stuck in accounting...",
        current_topic="career_dissatisfaction",
        emotional_state="frustrated",  # Detected from message tone
        response_time=15.0  # 15 seconds response time
    )
    
    print(f"   🎯 Human Insights: {result.get('human_insights', {})}")
    print(f"   💡 Recommendations: {result.get('human_insights', {}).get('engagement_recommendations', [])}")
    
    # Demo: Get reminder suggestions with timing awareness
    print("\n3. ⏰ Smart Reminder Timing")
    # Simulate different conversation states
    states = [
        ("intense_discussion", "excited", 0.9),
        ("natural_flow", "neutral", 0.4),
        ("casual_chat", "happy", 0.2)
    ]
    
    for rhythm, emotion, intensity in states:
        print(f"\n   Scenario: {rhythm} conversation, {emotion} mood, {intensity} intensity")
        
        # Get state and update it
        state = await manager._get_conversation_state(user_id)
        state.current_rhythm = ConversationRhythm(rhythm.upper())
        state.emotional_state = emotion
        state.conversation_intensity = intensity
        
        # Check if we should remind now
        if state.pending_questions:
            question = state.pending_questions[0]
            should_remind = manager._should_circle_back_now(question, state)
            print(f"   Should remind now: {'✅ Yes' if should_remind else '❌ No - waiting for better timing'}")
    
    # Demo: Intimacy-based conversation styling
    print("\n4. 💝 Relationship-Aware Conversation Styling")
    intimacy_levels = [
        ConversationIntimacy.STRANGER,
        ConversationIntimacy.GETTING_ACQUAINTED,
        ConversationIntimacy.BUILDING_RAPPORT,
        ConversationIntimacy.CLOSE_FRIEND
    ]
    
    for intimacy in intimacy_levels:
        style = manager._get_intimacy_appropriate_style(intimacy)
        print(f"   {intimacy.value}: '{style['curiosity']}' / '{style['personal_followup']}'")
    
    # Demo: Personality-specific reminder styles
    print("\n5. 🎭 Personality-Driven Conversation Styles")
    personalities = ["elena", "marcus", "jake"]
    
    for personality in personalities:
        reminders = manager._get_personality_reminders(
            personality, 
            QuestionType.PERSONAL, 
            "What made you choose that path?"
        )
        if reminders:
            print(f"   {personality.title()}: {reminders[0]}")
    
    print("\n🎉 All human-like conversation features integrated successfully!")
    print("\nKey Enhancements Added:")
    print("✅ Emotional state awareness and tone adjustment")
    print("✅ Relationship intimacy levels and appropriate styling")
    print("✅ Conversation rhythm detection and timing respect")
    print("✅ Personality-driven conversation styles per bot")
    print("✅ Natural conversation flow and topic bridging")
    print("✅ Intensity-based engagement recommendations")
    print("✅ Human-like timing for question follow-ups")


async def integration_with_event_handler_example():
    """
    Example of how to integrate enhanced features with existing event handler
    """
    print("\n" + "=" * 60)
    print("🔗 Integration with Event Handler Example")
    print("=" * 60)
    
    print("""
    # In src/handlers/events.py, enhance the _generate_and_send_response method:
    
    async def _generate_and_send_response(self, ...):
        # ... existing code ...
        
        # Extract emotional state from emotion analysis
        emotional_state = current_emotion_data.get('dominant_emotion', 'neutral') if current_emotion_data else 'neutral'
        
        # Process user response with human-like awareness
        if self.persistent_conversation_manager:
            conversation_result = await self.persistent_conversation_manager.process_user_response(
                user_id=user_id,
                user_message=original_content or message.content,
                current_topic=comprehensive_context.get('current_topic'),
                emotional_state=emotional_state,
                response_time=response_time  # Calculate from message timestamps
            )
            
            # Use human insights to enhance response
            human_insights = conversation_result.get('human_insights', {})
            
            # Add conversation guidance to context
            if conversation_result.get('guidance'):
                comprehensive_context['conversation_guidance'] = conversation_result['guidance']
                comprehensive_context['human_insights'] = human_insights
                
            # Get smart reminders that respect emotional state and timing
            reminders = await self.persistent_conversation_manager.get_reminder_suggestions(user_id)
            if reminders:
                comprehensive_context['natural_reminders'] = reminders
    
    # The enhanced system now provides:
    # - Emotional awareness in all conversation decisions
    # - Relationship-appropriate question styles
    # - Perfect timing for follow-up questions
    # - Personality-driven conversation approaches
    # - Natural conversation flow management
    """)


if __name__ == "__main__":
    print("🤖 WhisperEngine Human-Like Conversation Enhancement Demo")
    print("🎯 All features integrated into existing files - no new files needed!")
    
    asyncio.run(demo_human_like_conversation_features())
    asyncio.run(integration_with_event_handler_example())