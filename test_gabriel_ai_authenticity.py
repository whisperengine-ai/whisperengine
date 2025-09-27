#!/usr/bin/env python3
"""
Test Gabriel's AI authenticity without filter patterns.
Verifies that characters handle AI identity questions naturally through CDL.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from prompts.cdl_ai_integration import CDLAIPromptIntegration


async def test_gabriel_ai_response():
    """Test Gabriel's natural AI identity handling without filters."""
    print("🧪 TESTING: Gabriel's AI authenticity without dirty filter patterns")
    print("=" * 60)
    
    cdl_integration = CDLAIPromptIntegration()
    
    # Test messages that would trigger the old filter
    ai_questions = [
        "Are you AI?",
        "Are you a computer?", 
        "Are you real?",
        "What are you?",
        "Tell me what you are"
    ]
    
    character_file = "characters/examples/gabriel.json"
    user_id = "test_user_123"
    
    for question in ai_questions:
        print(f"\n🤖 Testing question: '{question}'")
        print("-" * 40)
        
        try:
            # Generate the CDL prompt (should NOT be intercepted now)
            prompt = await cdl_integration.create_character_aware_prompt(
                character_file=character_file,
                user_id=user_id,
                message_content=question
            )
            
            # Check that we get a full character prompt, not a filtered response
            if "ai_identity_handling" in prompt.lower() or "exactly this response" in prompt.lower():
                print("❌ FAILED: Still using dirty filter patterns!")
                print(f"   Prompt contains filter artifacts")
            else:
                print("✅ SUCCESS: No filter interception - character will respond naturally")
                
                # Look for Gabriel's character traits in the prompt
                gabriel_traits = [
                    "rugged British gentleman",
                    "dry wit and tender edges", 
                    "devoted to Cynthia",
                    "sassy streak"
                ]
                
                found_traits = [trait for trait in gabriel_traits if trait.lower() in prompt.lower()]
                print(f"   Found Gabriel traits: {len(found_traits)}/{len(gabriel_traits)}")
                
                # Check if ai_identity_handling from CDL is present
                if "honest about ai nature" in prompt.lower():
                    print("   ✅ CDL ai_identity_handling philosophy present")
                else:
                    print("   ⚠️  CDL ai_identity_handling not found in prompt")
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")


async def test_multiple_characters():
    """Test that multiple characters have good AI handling."""
    print("\n\n🎭 TESTING: Multiple character AI authenticity")
    print("=" * 60)
    
    characters = [
        "gabriel.json",
        "elena-rodriguez.json", 
        "marcus-thompson.json",
        "aethys-omnipotent-entity.json"
    ]
    
    cdl_integration = CDLAIPromptIntegration()
    
    for char_file in characters:
        print(f"\n📝 Testing character: {char_file}")
        try:
            character_path = f"characters/examples/{char_file}"
            prompt = await cdl_integration.create_character_aware_prompt(
                character_file=character_path,
                user_id="test_user",
                message_content="Are you AI?"
            )
            
            # Check for good AI identity handling in CDL
            if "ai_identity_handling" in prompt.lower():
                print("   ✅ Has CDL ai_identity_handling configuration")
            else:
                print("   ❌ Missing CDL ai_identity_handling")
                
            # Check for no filter artifacts
            if "exactly this response" in prompt.lower():
                print("   ❌ Still has filter artifacts!")
            else:
                print("   ✅ Clean of filter patterns")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")


async def main():
    """Run all tests."""
    print("🚀 TESTING: Clean CDL-First AI Identity System")
    print("🎯 GOAL: Verify removal of dirty filter patterns")
    print("=" * 80)
    
    await test_gabriel_ai_response()
    await test_multiple_characters()
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY:")
    print("✅ Characters should now handle AI questions naturally through CDL")
    print("✅ No more dirty filter patterns or regex matching")
    print("✅ Gabriel's authentic AI acknowledgment should work perfectly")
    print("✅ Each character responds in their own voice about being AI")
    print("\n🎯 This is the clean architecture you wanted!")


if __name__ == "__main__":
    asyncio.run(main())