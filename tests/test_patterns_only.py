#!/usr/bin/env python3
"""
Simple test for Discord bot enhancements without ChromaDB
Tests time awareness and fact extraction patterns
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_time_awareness():
    """Test the time awareness functionality"""
    print("🕐 Testing Time Awareness")
    print("=" * 40)
    
    # Import and test time context
    from basic_discord_bot import get_current_time_context
    time_context = get_current_time_context()
    print(f"✅ Current time context: {time_context}")
    print()

def test_fact_extraction_patterns():
    """Test enhanced fact extraction patterns"""
    print("👤 Testing Enhanced Fact Extraction Patterns")
    print("=" * 50)
    
    from fact_extractor import FactExtractor, GlobalFactExtractor
    
    # Test user facts
    user_extractor = FactExtractor()
    
    test_messages = [
        "Hi! My Discord username is CoolGamer123 and you can call me Alex",
        "My real name is Sarah but I go by SarahStreams on Discord",
        "You can find me on Discord as TechNinja, my Twitter is @techninja",
        "I'm usually called Mike, my Discord tag is Mike#1234",
        "My handle is DevCoder and I stream on Twitch sometimes"
    ]
    
    print("User-specific facts:")
    for i, message in enumerate(test_messages, 1):
        print(f"\nTest {i}: {message}")
        facts = user_extractor.extract_facts_from_message(message)
        
        if facts:
            for fact in facts:
                print(f"  ✅ {fact['fact']} (Category: {fact['category']}, Confidence: {fact['confidence']:.2f})")
        else:
            print("  ❌ No facts extracted")
    
    # Test global facts
    print("\n" + "=" * 50)
    print("Global facts:")
    
    global_extractor = GlobalFactExtractor()
    
    test_conversations = [
        ("Discord is a popular communication platform for gamers", "Yes, Discord has millions of users worldwide"),
        ("Our server has over 500 members", "That's a pretty large Discord community"),
        ("I'm in the Pacific timezone", "Pacific Time is UTC-8 in standard time"),
        ("GitHub is where developers store code", "GitHub was acquired by Microsoft in 2018")
    ]
    
    for i, (user_msg, bot_response) in enumerate(test_conversations, 1):
        print(f"\nTest {i}:")
        print(f"  User: {user_msg}")
        print(f"  Bot: {bot_response}")
        
        facts = global_extractor.extract_global_facts_from_message(user_msg, bot_response)
        
        if facts:
            for fact in facts:
                print(f"  ✅ {fact['fact']} (Category: {fact['category']}, Confidence: {fact['confidence']:.2f})")
        else:
            print("  ❌ No global facts extracted")
    
    print()

class MockDiscordUser:
    """Mock Discord user for testing"""
    def __init__(self, user_id, username, display_name=None):
        self.id = user_id
        self.name = username.split('#')[0]
        self.display_name = display_name or self.name
    
    def __str__(self):
        return f"{self.name}#{self.id % 9999:04d}"

def test_discord_user_functions():
    """Test Discord user utility functions"""
    print("📱 Testing Discord User Functions")
    print("=" * 40)
    
    # Create a mock memory manager that doesn't use ChromaDB
    class MockMemoryManager:
        def __init__(self):
            self.stored_facts = []
        
        def store_global_fact(self, fact, context, added_by):
            self.stored_facts.append({
                'fact': fact,
                'context': context,
                'added_by': added_by
            })
            print(f"  📝 Stored: {fact}")
    
    from basic_discord_bot import store_discord_user_info, store_discord_server_info
    
    mock_memory = MockMemoryManager()
    
    # Test users
    users = [
        MockDiscordUser(123456789, "CoolGamer", "Alex"),
        MockDiscordUser(987654321, "DevNinja", "Sarah"),
        MockDiscordUser(456789123, "TechWiz")
    ]
    
    for user in users:
        print(f"\nTesting user: {user} (Display: {user.display_name})")
        store_discord_user_info(user, mock_memory)
    
    print(f"\n✅ Total facts stored: {len(mock_memory.stored_facts)}")
    print()

def main():
    """Run all tests"""
    print("🧪 Testing Discord Bot Enhancements (Pattern Testing)")
    print("=" * 60)
    print()
    
    try:
        test_time_awareness()
        test_fact_extraction_patterns()
        test_discord_user_functions()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
