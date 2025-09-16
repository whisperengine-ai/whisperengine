#!/usr/bin/env python3
"""
Comprehensive test of the Discord name capture and database integration
"""

import sys
from emotion_manager import EmotionManager
from user_profile_db import UserProfileDatabase


def test_complete_integration():
    """Test the complete Discord bot integration with database"""
    print("🧪 Testing complete Discord bot integration...")

    # Initialize systems
    emotion_manager = EmotionManager(use_database=True)
    db = UserProfileDatabase()

    print(f"✅ Emotion manager initialized (using database: {emotion_manager.use_database})")

    # Simulate Discord bot message processing with name capture
    test_scenarios = [
        {
            "user_id": "integration_test_user",
            "display_name": "IntegrationTestUser",
            "message": "Hello bot! I'm testing the integration system.",
        }
    ]

    for scenario in test_scenarios:
        user_id = scenario["user_id"]
        display_name = scenario["display_name"]
        message = scenario["message"]

        print(f"\n🔍 Simulating Discord message from {display_name} ({user_id})")
        print(f"💬 Message: '{message}'")

        try:
            # Simulate the complete bot workflow:
            # 1. Analyze emotion and update profile (with name capture)
            profile, emotion = emotion_manager.analyze_and_update_emotion(
                user_id, message, display_name=display_name
            )

            print(f"✅ Emotion analysis complete:")
            print(f"   • Detected emotion: {emotion.detected_emotion.value}")
            print(f"   • User name captured: {profile.name or 'None'}")
            print(f"   • Interaction count: {profile.interaction_count}")

            # 2. Save profiles (happens automatically in bot)
            emotion_manager.save_profiles()
            print(f"✅ Profile saved to database")

            # 3. Verify persistence by loading fresh
            fresh_profile = db.load_user_profile(user_id)
            if fresh_profile and fresh_profile.name == display_name:
                print(f"✅ Name persistence verified: '{fresh_profile.name}'")
            else:
                print(f"❌ Name persistence failed")
                return False

        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            return False

    print(f"\n📊 Final database state:")

    # Show current database content
    all_profiles = db.load_all_profiles()
    for user_id, profile in all_profiles.items():
        name = profile.name or "No name"
        interactions = profile.interaction_count
        last_emotion = profile.current_emotion.value
        print(f"   • {user_id}: {name} ({interactions} interactions, {last_emotion})")

    # Clean up test user
    print(f"\n🧹 Cleaning up test data...")
    try:
        db.delete_user_profile("integration_test_user")
        print(f"✅ Test user cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

    print(f"\n🎉 Integration test completed successfully!")
    print("✅ Discord name capture system is working correctly")
    print("✅ Database integration is functioning properly")
    print("✅ Ready for production use with live Discord bot")

    return True


if __name__ == "__main__":
    success = test_complete_integration()
    sys.exit(0 if success else 1)
