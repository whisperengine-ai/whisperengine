#!/usr/bin/env python3
"""
Simple test for Discord bot enhancements without ChromaDB
Tests time awareness and fact extraction patterns
"""

import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_time_awareness():
    """Test the time awareness functionality"""

    # Import and test time context
    from basic_discord_bot import get_current_time_context

    get_current_time_context()


def test_fact_extraction_patterns():
    """Test enhanced fact extraction patterns"""

    from fact_extractor import FactExtractor, GlobalFactExtractor

    # Test user facts
    user_extractor = FactExtractor()

    test_messages = [
        "Hi! My Discord username is CoolGamer123 and you can call me Alex",
        "My real name is Sarah but I go by SarahStreams on Discord",
        "You can find me on Discord as TechNinja, my Twitter is @techninja",
        "I'm usually called Mike, my Discord tag is Mike#1234",
        "My handle is DevCoder and I stream on Twitch sometimes",
    ]

    for _i, message in enumerate(test_messages, 1):
        facts = user_extractor.extract_facts_from_message(message)

        if facts:
            for _fact in facts:
                pass
        else:
            pass

    # Test global facts

    global_extractor = GlobalFactExtractor()

    test_conversations = [
        (
            "Discord is a popular communication platform for gamers",
            "Yes, Discord has millions of users worldwide",
        ),
        ("Our server has over 500 members", "That's a pretty large Discord community"),
        ("I'm in the Pacific timezone", "Pacific Time is UTC-8 in standard time"),
        ("GitHub is where developers store code", "GitHub was acquired by Microsoft in 2018"),
    ]

    for _i, (user_msg, bot_response) in enumerate(test_conversations, 1):

        facts = global_extractor.extract_global_facts_from_message(user_msg, bot_response)

        if facts:
            for _fact in facts:
                pass
        else:
            pass



class MockDiscordUser:
    """Mock Discord user for testing"""

    def __init__(self, user_id, username, display_name=None):
        self.id = user_id
        self.name = username.split("#")[0]
        self.display_name = display_name or self.name

    def __str__(self):
        return f"{self.name}#{self.id % 9999:04d}"


def test_discord_user_functions():
    """Test Discord user utility functions"""

    # Create a mock memory manager that doesn't use ChromaDB
    class MockMemoryManager:
        def __init__(self):
            self.stored_facts = []

        def store_global_fact(self, fact, context, added_by):
            self.stored_facts.append({"fact": fact, "context": context, "added_by": added_by})

    from basic_discord_bot import store_discord_user_info

    mock_memory = MockMemoryManager()

    # Test users
    users = [
        MockDiscordUser(123456789, "CoolGamer", "Alex"),
        MockDiscordUser(987654321, "DevNinja", "Sarah"),
        MockDiscordUser(456789123, "TechWiz"),
    ]

    for user in users:
        store_discord_user_info(user, mock_memory)



def main():
    """Run all tests"""

    try:
        test_time_awareness()
        test_fact_extraction_patterns()
        test_discord_user_functions()


    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
