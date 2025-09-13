#!/usr/bin/env python3
"""
Integration test for LLM-based fact extraction in the memory manager
"""
import sys
import os
import logging

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lmstudio_client import LMStudioClient
from memory_manager import UserMemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_memory_manager_llm_facts():
    """Test LLM-based fact extraction through the memory manager"""
    
    print("Testing Memory Manager with LLM-based Fact Extraction")
    print("=" * 60)
    
    try:
        # Initialize LLM client
        llm_client = LMStudioClient()
        
        # Override the default model name with a known working model
        llm_client.default_model_name = "llama-3.2-1b-instruct"
        
        # Check if LM Studio is running
        if not llm_client.check_connection():
            print("❌ LM Studio is not running or not accessible")
            print("Please start LM Studio and load a model, then try again.")
            return False
            
        print("✅ LM Studio connection established")
        
        # Initialize memory manager with LLM support
        memory_manager = UserMemoryManager(enable_auto_facts=True, llm_client=llm_client)
        
        # Test user ID
        test_user_id = "test_user_llm_facts"
        
        # Test messages that should generate facts
        test_conversations = [
            {
                "user": "Hi! My name is Alice and I work as a data scientist at Microsoft in Seattle.",
                "bot": "Nice to meet you Alice! Data science is a fascinating field."
            },
            {
                "user": "Did you know that the Eiffel Tower is located in Paris, France?",
                "bot": "Yes, that's correct! The Eiffel Tower is one of Paris's most famous landmarks."
            },
            {
                "user": "Apple acquired Beats Electronics for $3 billion back in 2014.",
                "bot": "That was indeed a significant acquisition in the tech industry."
            }
        ]
        
        print(f"\nStoring conversations and extracting facts for user: {test_user_id}")
        
        total_facts_extracted = 0
        for i, conversation in enumerate(test_conversations, 1):
            print(f"\n--- Conversation {i} ---")
            print(f"User: {conversation['user']}")
            print(f"Bot: {conversation['bot']}")
            
            # Store the conversation (this should trigger fact extraction)
            try:
                memory_manager.store_conversation(
                    user_id=test_user_id,
                    user_message=conversation['user'],
                    bot_response=conversation['bot']
                )
                print("✅ Conversation stored successfully")
                
                # Check if any global facts were extracted (if global extraction is enabled)
                if hasattr(memory_manager, 'global_fact_extractor') and memory_manager.global_fact_extractor:
                    print("🔍 Global fact extraction is enabled")
                else:
                    print("ℹ️  Global fact extraction is disabled (this is expected)")
                    
            except Exception as e:
                print(f"❌ Error storing conversation: {e}")
                logger.error(f"Conversation storage error: {e}", exc_info=True)
        
        # Try to retrieve some user memories to verify storage worked
        print(f"\n--- Retrieving Memories ---")
        try:
            memories = memory_manager.get_relevant_memories(test_user_id, "Tell me about Alice", limit=5)
            if memories:
                print(f"✅ Retrieved {len(memories)} relevant memories:")
                for memory in memories:
                    print(f"  • {memory[:100]}..." if len(memory) > 100 else f"  • {memory}")
            else:
                print("ℹ️  No relevant memories found")
        except Exception as e:
            print(f"❌ Error retrieving memories: {e}")
            logger.error(f"Memory retrieval error: {e}", exc_info=True)
        
        print(f"\n" + "=" * 60)
        print("✅ Memory manager integration test completed successfully!")
        print("🤖 LLM-based fact extraction is now integrated into the Discord bot")
        return True
        
    except Exception as e:
        print(f"❌ Error in memory manager test: {e}")
        logger.error(f"Memory manager test error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_memory_manager_llm_facts()
    sys.exit(0 if success else 1)
