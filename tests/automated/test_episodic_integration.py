#!/usr/bin/env python3
"""
Test Vector Episodic Intelligence Integration
Validates that episodic memories are now included in character prompts
"""

import os
import sys
import asyncio
import asyncpg

async def test_episodic_integration():
    """Test that episodic intelligence is integrated into character prompts"""
    
    print("=" * 80)
    print("VECTOR EPISODIC INTELLIGENCE INTEGRATION TEST")
    print("=" * 80)
    print("Testing that episodic memories are now included in character prompts")
    
    # Set up environment
    os.environ.setdefault('FASTEMBED_CACHE_PATH', '/tmp/fastembed_cache')
    os.environ.setdefault('QDRANT_HOST', 'localhost')
    os.environ.setdefault('QDRANT_PORT', '6334')
    os.environ.setdefault('DISCORD_BOT_NAME', 'elena')
    
    # Add src to Python path
    sys.path.insert(0, '/Users/markcastillo/git/whisperengine/src')
    
    try:
        # Import the integration class
        from prompts.cdl_ai_integration import CDLAIPromptIntegration
        from memory.memory_protocol import create_memory_manager
        
        print("✅ Successfully imported CDL AI Integration classes")
        
        # Create memory manager for episodic intelligence
        memory_manager = create_memory_manager(memory_type="vector")
        print("✅ Created vector memory manager")
        
        # Create CDL integration instance with memory manager
        cdl_integration = CDLAIPromptIntegration(
            vector_memory_manager=memory_manager
        )
        print("✅ Created CDL AI Integration with memory manager")
        
        # Test with Elena character and a sample message
        test_user_id = "test_episodic_integration"
        test_message = "I'd love to hear about your marine biology research!"
        
        print(f"\n📝 Testing episodic integration with:")
        print(f"   User ID: {test_user_id}")
        print(f"   Message: {test_message}")
        print(f"   Character: Elena (marine biologist)")
        
        # Generate character prompt with episodic intelligence
        print("\n🚀 Generating character prompt with episodic intelligence...")
        character_prompt = await cdl_integration.create_unified_character_prompt(
            user_id=test_user_id,
            message_content=test_message,
            pipeline_result=None,
            user_name="TestUser"
        )
        
        print(f"✅ Character prompt generated successfully!")
        print(f"   Prompt length: {len(character_prompt)} characters")
        
        # Check for episodic intelligence markers
        episodic_markers = [
            "✨ CHARACTER EPISODIC MEMORIES",
            "emotionally significant moments",
            "You remember these",
            "Emotional significance:",
            "may naturally reference these memories"
        ]
        
        found_markers = []
        for marker in episodic_markers:
            if marker in character_prompt:
                found_markers.append(marker)
        
        print(f"\n🔍 Episodic Intelligence Integration Analysis:")
        print(f"   Episodic markers found: {len(found_markers)}/{len(episodic_markers)}")
        
        for marker in found_markers:
            print(f"   ✅ Found: '{marker}'")
        
        for marker in episodic_markers:
            if marker not in found_markers:
                print(f"   ⚠️ Missing: '{marker}'")
        
        # Show a snippet of the episodic section if found
        if "✨ CHARACTER EPISODIC MEMORIES" in character_prompt:
            # Extract the episodic section
            start = character_prompt.find("✨ CHARACTER EPISODIC MEMORIES")
            end = character_prompt.find("\n\n", start + 100) if start != -1 else -1
            
            if start != -1 and end != -1:
                episodic_section = character_prompt[start:end]
                print(f"\n📋 Episodic Intelligence Section Preview:")
                print("   " + "\n   ".join(episodic_section.split('\n')[:10]))
                print("   ...")
        
        # Test success criteria
        integration_success = len(found_markers) >= 2  # At least 2 episodic markers found
        
        print(f"\n" + "=" * 80)
        if integration_success:
            print("🎉 EPISODIC INTELLIGENCE INTEGRATION SUCCESSFUL!")
            print("✅ Character prompts now include episodic memories")
            print("✅ Characters can reference past memorable moments")
            print("✅ Vector episodic intelligence is fully integrated")
        else:
            print("⚠️ EPISODIC INTELLIGENCE INTEGRATION NEEDS ATTENTION")
            print("❌ Episodic markers not found in character prompt")
            print("❌ May need to check graph manager initialization")
        
        print("=" * 80)
        return integration_success
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_episodic_integration())
    sys.exit(0 if success else 1)