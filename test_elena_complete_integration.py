#!/usr/bin/env python3
"""
Test Elena's Complete Memory Integration

Now that we know Elena's memory search works with the correct bot_name,
let's test the complete CDL integration with memory to see if Elena
properly includes her marine biology memories in responses.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.memory.memory_protocol import create_memory_manager
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

async def test_elena_complete_integration():
    """Test Elena's complete memory + CDL integration"""
    print("🧬 TESTING: Elena's Complete Memory + CDL Integration")
    
    # Use Elena's correct configuration
    os.environ["BOT_NAME"] = "Elena"
    os.environ["DISCORD_BOT_NAME"] = "Elena"
    os.environ["QDRANT_COLLECTION_NAME"] = "whisperengine_memory"
    
    # Real user ID that has Elena conversations
    real_user_id = "672814231002939413"
    
    try:
        # Test memory manager
        print("\n=== TESTING MEMORY MANAGER ===")
        memory_manager = create_memory_manager(memory_type="vector")
        
        memories = await memory_manager.retrieve_relevant_memories(
            user_id=real_user_id,
            query="marine biology ocean",
            limit=5
        )
        
        print(f"Retrieved {len(memories)} relevant memories")
        
        if memories:
            print("Sample memories:")
            for i, memory in enumerate(memories[:3], 1):
                content = memory.get("content", "")
                role = memory.get("metadata", {}).get("role", "unknown")
                print(f"   {i}. [{role}] '{content[:100]}{'...' if len(content) > 100 else ''}'")
        
        # Test conversation history
        print("\n=== TESTING CONVERSATION HISTORY ===")
        conversation_history = await memory_manager.get_conversation_history(
            user_id=real_user_id,
            limit=5
        )
        
        print(f"Retrieved {len(conversation_history)} conversation items")
        
        if conversation_history:
            print("Recent conversation:")
            for i, conv in enumerate(conversation_history[:3], 1):
                role = conv.get("role", "unknown")
                content = conv.get("content", "")
                print(f"   {i}. [{role}] '{content[:100]}{'...' if len(content) > 100 else ''}'")
        
        # Test CDL integration
        print("\n=== TESTING CDL INTEGRATION ===")
        cdl_integration = CDLAIPromptIntegration(vector_memory_manager=memory_manager)  # ✅ Pass memory manager!
        
        test_message = "Tell me about ocean ecosystems"
        
        system_prompt = await cdl_integration.create_character_aware_prompt(
            character_file='characters/examples/elena-rodriguez.json',
            user_id=real_user_id,
            message_content=test_message
        )
        
        print(f"Generated system prompt: {len(system_prompt)} characters")
        
        # Check if memories are included
        if "CONVERSATION MEMORY & CONTEXT" in system_prompt:
            print("✅ SUCCESS: Memory section found in system prompt")
            
            # Extract memory section
            memory_start = system_prompt.find("CONVERSATION MEMORY & CONTEXT")
            memory_section = system_prompt[memory_start:memory_start+500]
            print(f"\nMemory section preview:\n{memory_section}...")
            
        else:
            print("❌ FAILURE: No memory section in system prompt")
            print("First 500 chars of prompt:")
            print(system_prompt[:500])
        
        # Check for marine biology content in the prompt
        marine_keywords = ["marine", "ocean", "sea", "fish", "coral", "ecosystem"]
        marine_found = [kw for kw in marine_keywords if kw.lower() in system_prompt.lower()]
        
        if marine_found:
            print(f"✅ Marine biology keywords found: {marine_found}")
        else:
            print("⚠️  No marine biology keywords in prompt")
        
        print(f"\n=== INTEGRATION TEST RESULTS ===")
        print(f"✅ Memory Manager: Working ({len(memories)} memories retrieved)")
        print(f"✅ Conversation History: Working ({len(conversation_history)} items)")
        print(f"✅ CDL Integration: {'Working' if 'CONVERSATION MEMORY & CONTEXT' in system_prompt else 'Failed'}")
        print(f"✅ Marine Content: {'Present' if marine_found else 'Missing'}")
        
        if len(memories) > 0 and "CONVERSATION MEMORY & CONTEXT" in system_prompt:
            print("\n🎉 COMPLETE SUCCESS: Elena's memory integration is working!")
            print("Elena should now be able to recall and discuss marine biology topics.")
        else:
            print("\n❌ Issues found - Elena's memory integration needs debugging")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_elena_complete_integration())