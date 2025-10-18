#!/usr/bin/env python3
"""
Seed test conversation data for summary validation.

This script creates a realistic conversation history between a test user and Elena
so we can test if conversation summaries actually improve response quality.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.memory.memory_protocol import create_memory_manager

# Your Discord ID
TEST_USER_ID = "672814231002939413"

# Realistic conversation turns (marine biology research theme)
CONVERSATION_TURNS = [
    {
        "user": "Hi Elena! I'm starting my thesis on ocean acidification impacts on coral reefs.",
        "bot": "That's fascinating! Ocean acidification is such a critical topic. What specific aspect are you focusing on? The physiological impacts on coral calcification, or perhaps the broader ecosystem effects?"
    },
    {
        "user": "I'm looking at how pH changes affect coral growth rates in the Indo-Pacific region.",
        "bot": "Excellent focus area! The Indo-Pacific has some of the most diverse coral communities. Have you considered using calcification rate measurements as your primary metric? And what's your sampling strategy looking like?"
    },
    {
        "user": "Yes, I'm planning to collect water samples monthly and measure calcium carbonate deposition.",
        "bot": "Smart approach! Monthly sampling should give you good temporal resolution. Make sure to account for seasonal variations and temperature fluctuations - they can interact with pH in complex ways. Are you working with any specific coral species?"
    },
    {
        "user": "I'm focusing on Acropora species since they're so common and sensitive to environmental changes.",
        "bot": "Perfect choice! Acropora are excellent indicator species. Their branching morphology also makes them relatively easy to measure for growth rates. Have you thought about your control sites? You'll want comparable locations with different pH levels."
    },
    {
        "user": "Yeah, I'm worried about finding good control sites. It's been challenging.",
        "bot": "That's a very real challenge in field research. Could you potentially look at historical data from your target sites? Sometimes you can establish baselines from existing marine monitoring programs. It's not perfect, but it can strengthen your comparative analysis."
    },
    {
        "user": "That's a great idea! I hadn't thought about using historical data.",
        "bot": "I'm glad I could help! Historical data can really fill in gaps, especially for slow-growing organisms like corals. Just be mindful of methodology differences - measurement techniques have evolved quite a bit over the past decade."
    },
    {
        "user": "I'm also worried about my thesis deadline. I have so much data to analyze still.",
        "bot": "Research timelines can definitely feel overwhelming! How far along are you with data collection? Sometimes it helps to break down the analysis into smaller, manageable chunks rather than seeing it as one massive task."
    },
    {
        "user": "I'm about 70% done with collection but haven't started analysis yet. My advisor wants preliminary results soon.",
        "bot": "Okay, you're in a better position than you might think! Starting analysis before collection is complete is actually pretty normal. What if you began with your early datasets while continuing collection? That way you can identify any methodological issues early and your advisor gets those preliminary results."
    }
]


async def main():
    """Seed conversation history for testing."""
    
    print("\n" + "="*80)
    print("SEEDING TEST CONVERSATION DATA")
    print("="*80)
    print(f"\nUser ID: {TEST_USER_ID}")
    print(f"Conversation turns: {len(CONVERSATION_TURNS)}")
    print("\nCreating realistic research conversation with Elena...\n")
    
    # Initialize memory manager
    print("🔧 Initializing memory manager...")
    memory_manager = create_memory_manager(memory_type="vector")
    
    # Store each conversation turn
    for i, turn in enumerate(CONVERSATION_TURNS, 1):
        print(f"💬 Storing turn {i}/{len(CONVERSATION_TURNS)}...")
        print(f"   User: {turn['user'][:60]}...")
        print(f"   Bot:  {turn['bot'][:60]}...")
        
        await memory_manager.store_conversation(
            user_id=TEST_USER_ID,
            user_message=turn['user'],
            bot_response=turn['bot'],
            conversation_metadata={
                "channel_id": "test_channel_001",
                "message_id": f"test_msg_{i:03d}",
                "character_name": "elena"
            }
        )
        
        print(f"   ✅ Stored")
    
    print("\n✅ CONVERSATION HISTORY SEEDED SUCCESSFULLY")
    print("\nConversation themes:")
    print("   • Marine biology research (ocean acidification)")
    print("   • Coral reef ecology (Acropora species)")  
    print("   • Thesis methodology (sampling strategy)")
    print("   • Academic anxiety (deadline pressure)")
    print("   • Data analysis planning")
    
    # Verify retrieval
    print("\n🔍 Verifying memory retrieval...")
    test_query = "What should I focus on with my research?"
    memories = await memory_manager.retrieve_relevant_memories(
        user_id=TEST_USER_ID,
        query=test_query,
        limit=5
    )
    
    print(f"\nRetrieved {len(memories)} relevant memories for query:")
    print(f'   "{test_query}"')
    
    if memories:
        print("\nTop 3 most relevant:")
        for i, mem in enumerate(memories[:3], 1):
            content = mem.get('content', '')[:70]
            semantic_key = mem.get('semantic_key', 'unknown')
            print(f"   {i}. [{semantic_key}] {content}...")
    
    print("\n" + "="*80)
    print("✅ READY TO TEST CONVERSATION SUMMARY VALUE")
    print("="*80)
    print("\nNow run: python tests/automated/test_summary_value_validation.py")
    print("This will show if summaries actually improve Elena's responses.")
    print("")


if __name__ == "__main__":
    asyncio.run(main())
