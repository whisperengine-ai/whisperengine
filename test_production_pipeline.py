#!/usr/bin/env python3
"""
Production Pipeline Integration Test
====================================

Verify that Phase 1.1, 1.2, and 1.3 are all enabled and working in the 
actual Discord bot pipeline when processing messages.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.memory.memory_protocol import create_memory_manager

async def test_production_pipeline_integration():
    """Test the actual production memory pipeline"""
    print("🚀 PRODUCTION PIPELINE INTEGRATION TEST")
    print("🎭 Testing Phase 1.1, 1.2, and 1.3 in actual bot pipeline")
    print("=" * 60)
    
    try:
        # Create the memory manager exactly as the production bot does
        memory_type = os.getenv("MEMORY_SYSTEM_TYPE", "vector")
        print(f"📋 Memory System Type: {memory_type}")
        
        memory_manager = create_memory_manager(memory_type)
        print(f"✅ Memory manager created: {type(memory_manager).__name__}")
        
        # Test a realistic conversation flow
        test_user_id = f"pipeline_test_{int(datetime.now().timestamp())}"
        
        print(f"\n🧪 Testing conversation flow for user: {test_user_id}")
        
        # Test Phase 1.1: Enhanced emotional detection
        emotional_messages = [
            ("I'm absolutely thrilled about my new job opportunity!", "Should detect very_positive"),
            ("I feel really anxious about the upcoming presentation", "Should detect anxious"), 
            ("I'm devastated about losing my pet", "Should detect very_negative"),
            ("That's an interesting point about AI", "Should detect neutral/contemplative")
        ]
        
        for i, (message, expectation) in enumerate(emotional_messages):
            print(f"\n  📝 Message {i+1}: {expectation}")
            print(f"      User: {message}")
            
            success = await memory_manager.store_conversation(
                user_id=test_user_id,
                user_message=message,
                bot_response=f"I understand. Let me help you with that situation.",
                metadata={"test_phase": "pipeline_integration", "message_num": i+1}
            )
            
            if success:
                print(f"      ✅ Stored successfully")
            else:
                print(f"      ❌ Storage failed")
                return False
        
        # Retrieve memories to verify all phases worked
        print(f"\n📊 Retrieving conversation history to verify phase integration...")
        
        memories = await memory_manager.get_conversation_history(test_user_id, limit=10)
        print(f"📋 Retrieved {len(memories)} memories")
        
        if not memories:
            print("❌ No memories retrieved - pipeline test failed")
            return False
        
        # Check for Phase 1.1, 1.2, and 1.3 data in retrieved memories
        phases_verified = {
            "1.1_emotional_detection": False,
            "1.2_trajectory_tracking": False, 
            "1.3_significance_scoring": False
        }
        
        for memory in memories:
            metadata = memory.get('metadata', {})
            
            # Phase 1.1: Check emotional context detection
            if 'emotional_context' in metadata:
                emotion = metadata['emotional_context']
                print(f"    🎭 Phase 1.1 ✅: Emotional context = '{emotion}'")
                phases_verified["1.1_emotional_detection"] = True
            
            # Phase 1.2: Check trajectory tracking
            if 'emotional_trajectory' in metadata:
                trajectory = metadata.get('emotional_trajectory', [])
                velocity = metadata.get('emotional_velocity', 0)
                momentum = metadata.get('emotional_momentum', 'unknown')
                print(f"    🎭 Phase 1.2 ✅: Trajectory length={len(trajectory)}, velocity={velocity:.3f}, momentum={momentum}")
                phases_verified["1.2_trajectory_tracking"] = True
            
            # Phase 1.3: Check significance scoring  
            if 'overall_significance' in metadata:
                significance = metadata.get('overall_significance', 0)
                tier = metadata.get('significance_tier', 'unknown')
                decay_resistance = metadata.get('decay_resistance', 0)
                print(f"    🎯 Phase 1.3 ✅: Significance={significance:.3f}, tier={tier}, decay_resistance={decay_resistance:.3f}")
                phases_verified["1.3_significance_scoring"] = True
        
        print(f"\n📊 PIPELINE INTEGRATION RESULTS:")
        all_phases_working = True
        
        for phase, verified in phases_verified.items():
            status = "✅ WORKING" if verified else "❌ MISSING"
            print(f"    {phase}: {status}")
            if not verified:
                all_phases_working = False
        
        if all_phases_working:
            print(f"\n🎉 SUCCESS: All phases (1.1, 1.2, 1.3) are integrated and working in production!")
            print(f"✅ The WhisperEngine AI pipeline is enhanced and ready for production use")
            return True
        else:
            print(f"\n❌ FAILURE: Some phases are not working in the production pipeline")
            print(f"🔧 Check the memory system configuration and phase integration")
            return False
            
    except Exception as e:
        print(f"❌ PIPELINE TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    success = await test_production_pipeline_integration()
    
    if success:
        print(f"\n🚀 PRODUCTION READY: Phase 1.1, 1.2, and 1.3 verified in Discord bot pipeline!")
    else:
        print(f"\n🛠️  ATTENTION NEEDED: Fix pipeline integration issues")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())