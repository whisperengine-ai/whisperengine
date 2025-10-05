#!/usr/bin/env python3
"""
Full test of Phase 3 with proper bot_core initialization like Elena bot
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

# Set required environment variables for testing
os.environ['FASTEMBED_CACHE_PATH'] = "/tmp/fastembed_cache"
os.environ['QDRANT_HOST'] = "localhost"
os.environ['QDRANT_PORT'] = "6334"

async def test_full_bot_setup():
    """Test Phase 3 with full bot setup like Elena bot"""
    try:
        from src.core.message_processor import create_message_processor, MessageContext
        from src.memory.memory_protocol import create_memory_manager
        from src.llm.llm_protocol import create_llm_client
        from src.core.bot import DiscordBotCore
        
        print("🔧 Creating full bot setup...")
        
        # Create components like the actual bot
        memory_manager = create_memory_manager(memory_type="vector")
        llm_client = create_llm_client(llm_client_type="openrouter")
        
        # Create bot core (this is what was missing in my previous test!)
        bot_core = DiscordBotCore()
        
        # Set the components that the bot needs
        bot_core.memory_manager = memory_manager
        bot_core.llm_client = llm_client
        
        # Initialize the bot core properly
        bot_core.initialize_all()
        
        print("✅ Bot core initialized")
        print(f"Bot core has phase2_integration: {hasattr(bot_core, 'phase2_integration')}")
        if hasattr(bot_core, 'phase2_integration'):
            print(f"phase2_integration is: {bot_core.phase2_integration}")
        
        # Now create message processor with proper bot_core
        message_processor = create_message_processor(bot_core, memory_manager, llm_client)
        
        print("✅ Message processor created with bot_core")
        
        # Test with a message
        test_message = "Hello! How are you doing today?"
        message_context = MessageContext(
            user_id="test_full_bot_setup", 
            content=test_message, 
            platform="direct_test"
        )
        
        print("🚀 Processing message with full bot setup...")
        result = await message_processor.process_message(message_context)
        
        # Check for Phase 3 results
        ai_components = result.metadata.get('ai_components', {}) if result.metadata else {}
        phase4_data = ai_components.get('phase4_intelligence', {})
        
        print(f"\n📊 PHASE 3 RESULTS CHECK (Full Bot Setup):")
        print(f"Phase 4 data exists: {bool(phase4_data)}")
        
        if isinstance(phase4_data, dict):
            phase3_results = phase4_data.get('phase3_results')
            processing_metadata = phase4_data.get('processing_metadata', {})
            phases_executed = processing_metadata.get('phases_executed', [])
            
            print(f"Phases executed: {phases_executed}")
            print(f"Phase 3 results type: {type(phase3_results)}")
            print(f"Phase 3 results: {phase3_results}")
            
            if phase3_results is None:
                print("❌ ISSUE: Phase 3 results are still None!")
                print("🔍 Debugging Phase execution...")
                if 'phase3' not in phases_executed:
                    print("❌ Phase 3 was not executed at all!")
                    if 'phase2' in phases_executed:
                        print("✅ Phase 2 was executed")
                    else:
                        print("❌ Phase 2 was also not executed")
                return False
            else:
                print("✅ SUCCESS: Phase 3 results are populated with full bot setup!")
                return True
        else:
            print(f"❌ No Phase 4 data: {phase4_data}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_bot_setup())
    if success:
        print("\n🎉 Full bot setup Phase 3 working!")
    else:
        print("\n🚨 Full bot setup still has Phase 3 issues")