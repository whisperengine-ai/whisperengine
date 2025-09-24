#!/usr/bin/env python3
"""
Test Bot Name Case Sensitivity in Elena's Memory Search

We found Elena's memories are stored with "bot_name": "Elena" (capital E)
but her searches return 0 results. This tests different bot name variations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.memory.memory_protocol import create_memory_manager

async def test_bot_name_case_sensitivity():
    """Test different bot name cases in memory search"""
    print("🔍 TESTING: Bot Name Case Sensitivity")
    
    # Get a real user ID from the collection data
    real_user_id = "672814231002939413"  # From the sample data we saw
    
    # Test different bot name variations
    bot_name_variations = [
        "Elena",      # Capital E (stored format)
        "elena",      # Lowercase (potential search format)
        "ELENA",      # All caps
        None,         # No bot name filtering
    ]
    
    for bot_name in bot_name_variations:
        print(f"\n=== TESTING BOT_NAME: {bot_name} ===")
        
        # Set environment for this test
        if bot_name:
            os.environ["BOT_NAME"] = bot_name
            os.environ["DISCORD_BOT_NAME"] = bot_name
        
        try:
            memory_manager = create_memory_manager(memory_type="vector")
            
            # Test memory retrieval
            memories = await memory_manager.retrieve_relevant_memories(
                user_id=real_user_id,
                query="marine biology conversation",
                limit=5
            )
            
            print(f"Found {len(memories)} memories with bot_name='{bot_name}'")
            
            if memories:
                print("✅ SUCCESS! Sample memories:")
                for i, memory in enumerate(memories[:2], 1):
                    content = memory.get("content", "")
                    role = memory.get("metadata", {}).get("role", "unknown")
                    print(f"   {i}. [{role}] '{content[:80]}{'...' if len(content) > 80 else ''}'")
                
                # This is the working configuration!
                if len(memories) > 0:
                    print(f"🎯 SOLUTION FOUND: bot_name='{bot_name}' returns {len(memories)} memories")
                    break
            else:
                print("❌ No memories found")
                
        except Exception as e:
            print(f"❌ Error with bot_name='{bot_name}': {e}")
    
    print("\n=== CHECKING MEMORY METADATA ===")
    # Let's also check what bot_name values are actually stored
    try:
        os.environ["BOT_NAME"] = "Elena"  # Use the working one
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Get memories and check their bot_name values
        memories = await memory_manager.retrieve_relevant_memories(
            user_id=real_user_id,
            query="conversation",
            limit=10
        )
        
        if memories:
            bot_names_found = set()
            for memory in memories:
                # Try to extract bot_name from memory data
                metadata = memory.get("metadata", {})
                # Check different possible locations for bot_name
                potential_bot_names = [
                    memory.get("bot_name"),
                    metadata.get("bot_name"), 
                    memory.get("source", "").split("_")[0] if "_" in memory.get("source", "") else None
                ]
                
                for name in potential_bot_names:
                    if name:
                        bot_names_found.add(name)
            
            print(f"Bot names found in memory metadata: {bot_names_found}")
        
    except Exception as e:
        print(f"❌ Error checking metadata: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_name_case_sensitivity())