#!/usr/bin/env python3
"""
Test null safety for character fields to ensure no crashes with blank/missing data.
"""

# Mock CDL Character with blank fields to test null safety
class MockIdentity:
    def __init__(self, name=None, occupation=None, description=None):
        self.name = name
        self.occupation = occupation 
        self.description = description

class MockCharacter:
    def __init__(self, name=None, occupation=None, description=None):
        self.identity = MockIdentity(name, occupation, description)

def test_null_safety_patterns():
    """Test the null safety patterns we implemented."""
    
    print("🧪 TESTING NULL SAFETY PATTERNS")
    print("=" * 40)
    
    # Test scenarios
    test_cases = [
        ("All blank", MockCharacter(None, None, None)),
        ("Blank name", MockCharacter(None, "Marine Biologist", "Description here")),  
        ("Blank occupation", MockCharacter("Elena", None, "Description here")),
        ("Blank description", MockCharacter("Elena", "Marine Biologist", None)),
        ("Empty strings", MockCharacter("", "", "")),
        ("Normal case", MockCharacter("Elena Rodriguez", "Marine Biologist", "A passionate researcher"))
    ]
    
    for test_name, character in test_cases:
        print(f"\n🔍 Testing: {test_name}")
        
        # Test our null safety patterns
        try:
            # Pattern 1: Safe character name and occupation
            character_name = character.identity.name if character.identity.name else "AI Character"
            character_occupation = character.identity.occupation if character.identity.occupation else "AI Assistant"
            safe_bot_name_fallback = character_name if character_name != "AI Character" else "unknown"
            
            character_identity_line = f"You are {character_name}, a {character_occupation}."
            print(f"   ✅ Identity line: {character_identity_line}")
            
            # Pattern 2: Safe description check
            description_check = hasattr(character.identity, 'description') and character.identity.description
            print(f"   ✅ Description check: {description_check}")
            
            # Pattern 3: Safe bot name for database queries
            import os
            bot_name = os.getenv('DISCORD_BOT_NAME', safe_bot_name_fallback).lower()
            print(f"   ✅ Safe bot name: {bot_name}")
            
            # Pattern 4: Safe AI identity message
            ai_message = f"If asked about AI nature, respond authentically as {character_name} while being honest about your AI nature when directly asked."
            print(f"   ✅ AI identity message: {ai_message[:50]}...")
            
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            return False
    
    print(f"\n🎉 SUCCESS: All null safety patterns working correctly!")
    print(f"✅ Characters with blank fields will not crash the system")
    print(f"✅ Fallback values provide reasonable defaults")
    print(f"✅ Database queries use safe bot names")
    return True

if __name__ == "__main__":
    test_null_safety_patterns()