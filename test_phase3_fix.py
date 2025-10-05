#!/usr/bin/env python3
"""
Quick test to validate Phase 3 fix
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

async def test_phase3_fix():
    """Test if Phase 3 is now working and not null"""
    try:
        from src.core.message_processor import create_message_processor, MessageContext
        from src.memory.memory_protocol import create_memory_manager
        from src.llm.llm_protocol import create_llm_client
        
        print("🔧 Creating message processor components...")
        
        # Create components
        memory_manager = create_memory_manager(memory_type="vector")
        llm_client = create_llm_client(llm_client_type="openrouter")
        message_processor = create_message_processor(None, memory_manager, llm_client)
        
        print("✅ Components created successfully")
        
        # Test with a simple message
        test_message = "Hello! How are you doing today?"
        message_context = MessageContext(
            user_id="test_user_phase3", 
            content=test_message, 
            platform="direct_test"
        )
        
        print("🚀 Processing message to test Phase 3...")
        result = await message_processor.process_message(message_context)
        
        # Check for Phase 3 results
        ai_components = result.metadata.get('ai_components', {})
        phase4_data = ai_components.get('phase4_intelligence', {})
        
        print(f"\n📊 PHASE 3 RESULTS CHECK:")
        print(f"Phase 4 data type: {type(phase4_data)}")
        
        if isinstance(phase4_data, dict):
            phase3_results = phase4_data.get('phase3_results')
            print(f"Phase 3 results: {type(phase3_results)} = {phase3_results}")
            
            if phase3_results is None:
                print("❌ ISSUE: Phase 3 results are still None!")
                return False
            else:
                print("✅ SUCCESS: Phase 3 results are now populated!")
                print(f"Phase 3 data keys: {list(phase3_results.keys()) if isinstance(phase3_results, dict) else 'Not a dict'}")
                return True
        else:
            print(f"❌ Phase 4 data structure issue: {phase4_data}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_phase3_fix())
    if success:
        print("\n🎉 Phase 3 fix successful!")
    else:
        print("\n🚨 Phase 3 still has issues")