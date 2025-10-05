#!/usr/bin/env python3
"""
Test Phase 4 through the exact same code path that MessageProcessor uses
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

async def test_message_processor_path():
    """Test Phase 4 through the exact same path as MessageProcessor"""
    try:
        from src.memory.memory_protocol import create_memory_manager
        from src.intelligence.simplified_emotion_manager import SimplifiedEmotionManager
        
        print("🔧 Creating components exactly like MessageProcessor...")
        
        # Create memory manager
        memory_manager = create_memory_manager(memory_type="vector")
        print("✅ Memory manager created")
        
        # Create simplified emotion manager (like MessageProcessor does)
        emotion_manager = SimplifiedEmotionManager(memory_manager)
        print("✅ Emotion manager created")
        
        # Create a mock Discord message (like the message processor does)
        class MockDiscordMessage:
            def __init__(self, content):
                self.content = content
                self.author = type('obj', (object,), {'id': 'test_user'})()
                self.timestamp = None
        
        discord_message = MockDiscordMessage("Hello, how are you?")
        
        print("🚀 Testing process_phase4_intelligence (exact MessageProcessor path)...")
        
        # Call the exact method that MessageProcessor calls
        result = await emotion_manager.process_phase4_intelligence(
            user_id="test_user_exact_path",
            message=discord_message,
            recent_messages=[],
            external_emotion_data=None,
            phase2_context=None
        )
        
        print(f"\n📊 RESULT ANALYSIS:")
        print(f"Result type: {type(result)}")
        
        if result is None:
            print("❌ ISSUE: process_phase4_intelligence returned None!")
            return False
            
        elif isinstance(result, dict):
            phase3_results = result.get('phase3_results')
            print(f"Phase 3 results type: {type(phase3_results)}")
            print(f"Phase 3 results content: {phase3_results}")
            
            if phase3_results is None:
                print("❌ ISSUE: Phase 3 results are None in the serialized result!")
                return False
            else:
                print("✅ SUCCESS: Phase 3 results are populated in MessageProcessor path!")
                return True
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_message_processor_path())
    if success:
        print("\n🎉 MessageProcessor path Phase 3 working!")
    else:
        print("\n🚨 MessageProcessor path still has Phase 3 issues")