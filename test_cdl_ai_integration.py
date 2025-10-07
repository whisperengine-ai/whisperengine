#!/usr/bin/env python3
"""
Test CDL AI Integration with Database
Tests if the CDL AI integration system can access Elena's database CDL data
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

from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

async def test_cdl_ai_integration():
    """Test CDL AI integration with database"""
    print("🧪 Testing CDL AI Integration with Database...")
    
    try:
        # Create CDL AI integration instance
        cdl_integration = CDLAIPromptIntegration()
        print("✅ Created CDL AI integration instance")
        
        # Test character-aware prompt creation
        prompt = await cdl_integration.create_unified_character_prompt(
            character_file="elena.json",  # This should trigger database lookup
            user_id="test_user",
            message_content="Hello Elena! Tell me about marine biology.",
            pipeline_result={}
        )
        
        print("✅ Generated character-aware prompt")
        print(f"📏 Prompt length: {len(prompt)} characters")
        
        # Check if prompt contains Elena-specific information
        if "elena" in prompt.lower():
            print("✅ Prompt contains Elena character reference")
        
        if "marine biolog" in prompt.lower():
            print("✅ Prompt contains marine biology reference")
            
        if "openness" in prompt.lower():
            print("✅ Prompt contains personality trait information")
            
        # Show a snippet of the prompt
        print("📄 Full character-aware prompt:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ CDL AI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cdl_ai_integration())
    exit(0 if success else 1)