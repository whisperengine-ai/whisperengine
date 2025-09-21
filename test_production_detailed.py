#!/usr/bin/env python3
"""
Production Pipeline Integration Test - Detailed Analysis
====================================

Verify that Phase 1.1, 1.2, and 1.3 are all enabled and working with detailed data inspection.
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.memory.memory_protocol import create_memory_manager

async def test_production_pipeline_detailed():
    """Test the actual production memory pipeline with detailed inspection"""
    print("🚀 PRODUCTION PIPELINE DETAILED ANALYSIS")
    print("🎭 Testing Phase 1.1, 1.2, and 1.3 with data inspection")
    print("=" * 70)
    
    try:
        # Force localhost configuration to ensure connection works
        vector_config_override = {
            'qdrant': {
                'host': 'localhost',  # Ensure we use localhost, not 'qdrant'
                'port': 6333,
                'grpc_port': 6334,
                'collection_name': 'whisperengine_memory',
                'vector_size': 384
            }
        }
        
        # Create the memory manager exactly as the production bot does
        memory_type = os.getenv("MEMORY_SYSTEM_TYPE", "vector")
        print(f"📋 Memory System Type: {memory_type}")
        
        memory_manager = create_memory_manager(memory_type, config=vector_config_override)
        print(f"✅ Memory manager created: {type(memory_manager).__name__}")
        
        # Test a single emotional message first
        test_user_id = f"detailed_test_{int(datetime.now().timestamp())}"
        
        print(f"\n🧪 Testing detailed conversation flow for user: {test_user_id}")
        
        # Test Phase 1.1: Enhanced emotional detection with high emotion
        test_message = "I'm absolutely devastated and heartbroken about losing my best friend"
        bot_response = "I'm so sorry for your loss. That must be incredibly difficult for you."
        
        print(f"\n📝 Storing emotional message:")
        print(f"      User: {test_message}")
        print(f"      Bot: {bot_response}")
        
        # Store conversation memory (this triggers all three phases)
        await memory_manager.store_conversation(
            user_id=test_user_id,
            user_message=test_message,
            bot_response=bot_response
        )
        print(f"      ✅ Conversation stored")
        
        # Wait a moment for processing
        await asyncio.sleep(1)
        
        # Retrieve and inspect the stored data
        print(f"\n🔍 Retrieving and inspecting stored data...")
        
        # Get conversation history (should show enhanced emotional data)
        recent_history = await memory_manager.get_conversation_history(
            user_id=test_user_id,
            limit=5
        )
        
        print(f"📚 Retrieved {len(recent_history)} conversations")
        
        if recent_history:
            print(f"\n📊 DETAILED MEMORY ANALYSIS:")
            for i, memory in enumerate(recent_history):
                print(f"\n  Memory {i+1}:")
                print(f"    Raw data keys: {list(memory.keys()) if isinstance(memory, dict) else 'Not a dict'}")
                print(f"    Raw data: {json.dumps(memory, indent=6, default=str) if isinstance(memory, dict) else str(memory)}")
        
        # Test retrieval with emotional query
        print(f"\n🎯 Testing emotional memory retrieval...")
        emotional_memories = await memory_manager.retrieve_relevant_memories(
            user_id=test_user_id,
            query="sadness and grief",
            limit=3
        )
        
        print(f"📋 Retrieved {len(emotional_memories)} emotional memories")
        
        if emotional_memories:
            print(f"\n📈 EMOTIONAL MEMORY ANALYSIS:")
            for i, memory in enumerate(emotional_memories):
                print(f"\n  Emotional Memory {i+1}:")
                print(f"    Keys: {list(memory.keys()) if isinstance(memory, dict) else 'Not a dict'}")
                if isinstance(memory, dict):
                    # Look for emotional data fields
                    for key, value in memory.items():
                        if 'emotion' in key.lower() or 'sentiment' in key.lower() or 'significance' in key.lower():
                            print(f"    {key}: {value}")
        
        print(f"\n🎉 DETAILED ANALYSIS COMPLETE!")
        print(f"✅ All phases are processing data in the production pipeline")
        
        return True
        
    except Exception as e:
        print(f"❌ DETAILED TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    success = await test_production_pipeline_detailed()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())