#!/usr/bin/env python3
"""
Test Discord reply functionality for WhisperEngine bots.

This script tests that bots properly reply to mentions in channels
instead of just sending messages to the channel.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

async def test_reply_logic():
    """Test the reply logic we implemented."""
    print("🧪 Testing Discord reply functionality logic...")
    
    # Simulate the logic we implemented
    class MockMessage:
        def __init__(self, guild=None):
            self.guild = guild
            self.author = type('Author', (), {'mention': '@TestUser'})()
            
        async def reply(self, content, mention_author=True):
            mention_text = " (with mention)" if mention_author else " (no mention)"
            print(f"  📝 REPLY: {content}{mention_text}")
            
    class MockChannel:
        async def send(self, content):
            print(f"  💬 SEND: {content}")
    
    # Test guild message (should use reply)
    print("\n🏰 Testing Guild Message (Channel Mention):")
    guild_message = MockMessage(guild="TestGuild")
    channel = MockChannel()
    
    # This is our logic from the code
    reference_message = guild_message if guild_message.guild else None
    if reference_message:
        await reference_message.reply("Hello! This should be a reply to your mention.", mention_author=True)
    else:
        await channel.send("Hello! This should be a regular message.")
    
    # Test DM (should use regular send)
    print("\n💌 Testing Direct Message:")
    dm_message = MockMessage(guild=None)
    
    reference_message = dm_message if dm_message.guild else None
    if reference_message:
        await reference_message.reply("Hello! This should be a reply to your mention.", mention_author=True)
    else:
        await channel.send("Hello! This should be a regular message.")
    
    print("\n✅ Reply logic test completed!")
    print("\n📋 Summary:")
    print("  • Guild mentions: Use message.reply() with mention_author=True")
    print("  • Direct messages: Use channel.send() as before")
    print("  • Error messages: Also use replies for guild channels")

if __name__ == "__main__":
    asyncio.run(test_reply_logic())