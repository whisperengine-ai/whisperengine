#!/usr/bin/env python3
"""
Test the emotion manager name capture system
"""

import sys
from emotion_manager import EmotionManager
from user_profile_db import UserProfileDatabase


def test_name_capture():
    """Test that the emotion manager captures and updates user names"""
    print("🧪 Testing emotion manager name capture system...")

    # Create test instance
    emotion_manager = EmotionManager()
    db = UserProfileDatabase()

    # Test scenarios
    test_cases = [
        ("new_user_123", "NewUser"),
        ("existing_user_456", "ExistingUser"),
        ("test_user_789", "TestUser789"),
    ]

    created_users = 0

    for user_id, display_name in test_cases:
        print(f"\n🔍 Testing user: {display_name} ({user_id})")

        try:
            # This should capture the name
            profile = emotion_manager.get_or_create_profile(user_id, display_name=display_name)
            print(f"✅ Created/updated profile for {display_name}")

            # Save the profiles to database (this is what the Discord bot does)
            emotion_manager.save_profiles()

            # Verify name was saved
            saved_profile = db.load_user_profile(user_id)
            if saved_profile and saved_profile.name == display_name:
                print(f"✅ Name '{display_name}' correctly saved in database")
                created_users += 1
            else:
                print(f"⚠️  Name may not have been saved correctly")
                if saved_profile:
                    print(f"    Saved name: '{saved_profile.name}'")

        except Exception as e:
            print(f"❌ Error processing user: {e}")

    print("\n🔍 Checking final database state...")

    # List all users to verify
    all_profiles = db.load_all_profiles()
    print(f"\n📊 Found {len(all_profiles)} users in database:")

    for user_id, profile in all_profiles.items():
        name = profile.name if profile.name else "No name"
        print(f"   • {user_id}: {name}")

    # Count users with names
    named_users = sum(
        1 for profile in all_profiles.values() if profile.name and profile.name != "No name"
    )
    print(f"\n📈 {named_users}/{len(all_profiles)} users have names")

    if created_users >= len(test_cases):
        print("✅ Name capture system is working correctly!")
        return True
    else:
        print("⚠️  Some names may not have been captured")
        return False


if __name__ == "__main__":
    success = test_name_capture()
    sys.exit(0 if success else 1)
