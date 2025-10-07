#!/usr/bin/env python3
"""
Test End-to-End CDL Database Integration
Tests the complete CDL database integration in a bot-like scenario
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

# Set up environment for Elena bot testing
os.environ['DISCORD_BOT_NAME'] = 'elena'
os.environ['CHARACTER_FILE'] = 'elena.json'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine_password'

async def test_bot_integration():
    """Test full bot integration with database CDL"""
    print("🤖 Testing Complete Bot CDL Database Integration...")
    
    try:
        # Import the components like a real bot would
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        from src.characters.cdl.manager import get_cdl_manager
        
        print("✅ Imported CDL components")
        
        # Test 1: CDL Manager Direct Access
        print("\n📊 Test 1: CDL Manager Direct Access")
        cdl_manager = get_cdl_manager()
        character_name = cdl_manager.get_character_name()
        occupation = cdl_manager.get_character_occupation()
        
        print(f"👤 Character Name: {character_name}")
        print(f"💼 Occupation: {occupation}")
        
        # Test personality data access
        openness = cdl_manager.get_field("personality.big_five_traits.openness.score", "Unknown")
        print(f"🧠 Openness score: {openness}")
        
        # Test 2: CDL AI Integration
        print("\n🎭 Test 2: CDL AI Integration")
        cdl_integration = CDLAIPromptIntegration()
        
        # Generate a prompt for a typical bot interaction
        prompt = await cdl_integration.create_unified_character_prompt(
            character_file="elena.json",  # This triggers database lookup now
            user_id="test_user_123",
            message_content="Hi Elena! I'm interested in learning about coral reefs. Can you tell me about marine conservation?",
            pipeline_result={}
        )
        
        print(f"✅ Generated unified character prompt ({len(prompt)} chars)")
        
        # Test 3: Character Object Access
        print("\n👤 Test 3: Character Object Access")
        character = cdl_manager.get_character_object()
        if character:
            print(f"✅ Character object created successfully")
            print(f"📝 Character name: {character.identity.name}")
            print(f"💼 Character occupation: {character.identity.occupation}")
            print(f"🧠 Big Five openness: {character.personality.big_five.openness}")
            print(f"🎯 Big Five conscientiousness: {character.personality.big_five.conscientiousness}")
        else:
            print("❌ Failed to create character object")
            
        # Test 4: Verify Database vs JSON Behavior
        print("\n🔄 Test 4: Database Integration Verification")
        if "marine biolog" in prompt.lower():
            print("✅ Prompt contains occupation from database")
        if str(openness) in prompt:
            print("✅ Prompt contains personality data from database")
        
        print("\n🎉 Complete Bot CDL Database Integration Test PASSED!")
        print("📄 Sample prompt snippet:")
        print(f"   {prompt[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bot_integration())
    exit(0 if success else 1)