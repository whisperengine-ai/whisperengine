#!/usr/bin/env python3
"""
Test script for Discord bot enhancements
Tests user information storage, time awareness, and global facts
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import UserMemoryManager
from fact_extractor import FactExtractor, GlobalFactExtractor
from basic_discord_bot import get_current_time_context, store_discord_user_info

def test_time_awareness():
    """Test the time awareness functionality"""
    print("🕐 Testing Time Awareness")
    print("=" * 40)
    
    time_context = get_current_time_context()
    print(f"Current time context: {time_context}")
    print()

def test_user_fact_extraction():
    """Test enhanced user fact extraction with Discord patterns"""
    print("👤 Testing Enhanced User Fact Extraction")
    print("=" * 40)
    
    extractor = FactExtractor()
    
    test_messages = [
        "Hi! My Discord username is CoolGamer123 and you can call me Alex",
        "My real name is Sarah but I go by SarahStreams on Discord",
        "You can find me on Discord as TechNinja, my Twitter is @techninja",
        "I'm usually called Mike, my Discord tag is Mike#1234",
        "My handle is DevCoder and I stream on Twitch sometimes"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")
        facts = extractor.extract_facts_from_message(message)
        
        if facts:
            for fact in facts:
                print(f"  ✅ Extracted: {fact['fact']} (Category: {fact['category']}, Confidence: {fact['confidence']:.2f})")
        else:
            print("  ❌ No facts extracted")
        print()

def test_global_fact_extraction():
    """Test enhanced global fact extraction"""
    print("🌍 Testing Enhanced Global Fact Extraction")
    print("=" * 40)
    
    extractor = GlobalFactExtractor()
    
    test_conversations = [
        ("Discord is a popular communication platform for gamers", "Yes, Discord has millions of users worldwide"),
        ("Our server has over 500 members", "That's a pretty large Discord community"),
        ("I'm in the Pacific timezone", "Pacific Time is UTC-8 in standard time"),
        ("GitHub is where developers store code", "GitHub was acquired by Microsoft in 2018")
    ]
    
    for i, (user_msg, bot_response) in enumerate(test_conversations, 1):
        print(f"Test {i}:")
        print(f"  User: {user_msg}")
        print(f"  Bot: {bot_response}")
        
        facts = extractor.extract_global_facts_from_message(user_msg, bot_response)
        
        if facts:
            for fact in facts:
                print(f"  ✅ Global fact: {fact['fact']} (Category: {fact['category']}, Confidence: {fact['confidence']:.2f})")
        else:
            print("  ❌ No global facts extracted")
        print()

def test_memory_storage():
    """Test memory storage with Discord enhancements"""
    print("💾 Testing Memory Storage")
    print("=" * 40)
    
    try:
        # Use test ChromaDB directory
        memory_manager = UserMemoryManager(persist_directory="./test_chromadb", enable_auto_facts=True)
        
        # Test storing a conversation with Discord elements
        user_id = "test_user_123"
        message = "Hey! My Discord username is TestUser and I'm in the EST timezone. I love gaming on Discord servers."
        response = "Nice to meet you, TestUser! Eastern Time is a common timezone for Discord communities."
        
        # Store the conversation
        memory_manager.store_conversation(user_id, message, response)
        print(f"✅ Stored conversation for user {user_id}")
        
        # Test storing a global fact about Discord
        global_fact = "Discord supports voice and text communication in organized servers and channels"
        memory_manager.store_global_fact(global_fact, "Information about Discord platform", "test_admin")
        print(f"✅ Stored global fact: {global_fact}")
        
        # Test retrieval
        query = "Discord gaming timezone"
        memories = memory_manager.retrieve_relevant_memories(user_id, query, limit=5)
        
        print(f"\nRetrieved {len(memories)} relevant memories for query: '{query}'")
        for memory in memories:
            metadata = memory['metadata']
            if metadata.get('is_global'):
                print(f"  🌍 Global: {metadata.get('fact', memory['text'])}")
            else:
                print(f"  👤 User: {metadata.get('fact', memory['text'])}")
        
    except Exception as e:
        print(f"❌ Error testing memory storage: {e}")
    
    print()

class MockDiscordUser:
    """Mock Discord user for testing"""
    def __init__(self, user_id, username, display_name=None):
        self.id = user_id
        self.name = username.split('#')[0]  # Discord username without discriminator
        self.display_name = display_name or self.name
    
    def __str__(self):
        return f"{self.name}#{self.id % 9999:04d}"  # Simulate discriminator

def test_discord_user_info_storage():
    """Test Discord user information storage"""
    print("📱 Testing Discord User Info Storage")
    print("=" * 40)
    
    try:
        memory_manager = UserMemoryManager(persist_directory="./test_chromadb", enable_auto_facts=True)
        
        # Create mock Discord users
        users = [
            MockDiscordUser(123456789, "CoolGamer", "Alex"),
            MockDiscordUser(987654321, "DevNinja", "Sarah"),
            MockDiscordUser(456789123, "TechWiz")
        ]
        
        # Test storing user info
        for user in users:
            store_discord_user_info(user, memory_manager)
            print(f"✅ Stored info for {user} (Display: {user.display_name})")
        
        # Test retrieval of user facts
        query = "Discord user CoolGamer"
        global_facts = memory_manager.retrieve_relevant_global_facts(query, limit=5)
        
        print(f"\nRetrieved {len(global_facts)} global facts for query: '{query}'")
        for fact in global_facts:
            print(f"  🌍 {fact['metadata']['fact']}")
            
    except Exception as e:
        print(f"❌ Error testing Discord user info storage: {e}")
    
    print()

def main():
    """Run all tests"""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Discord Bot Enhancements")
    print("=" * 50)
    print()
    
    # Run tests
    test_time_awareness()
    test_user_fact_extraction()
    test_global_fact_extraction()
    test_memory_storage()
    test_discord_user_info_storage()
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    main()
