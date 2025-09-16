#!/usr/bin/env python3
"""
Comprehensive test of the Discord name capture and database integration
"""

import sys

from emotion_manager import EmotionManager
from user_profile_db import UserProfileDatabase


def test_complete_integration():
    """Test the complete Discord bot integration with database"""

    # Initialize systems
    emotion_manager = EmotionManager(use_database=True)
    db = UserProfileDatabase()

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

        try:
            # Simulate the complete bot workflow:
            # 1. Analyze emotion and update profile (with name capture)
            profile, emotion = emotion_manager.analyze_and_update_emotion(
                user_id, message, display_name=display_name
            )

            # 2. Save profiles (happens automatically in bot)
            emotion_manager.save_profiles()

            # 3. Verify persistence by loading fresh
            fresh_profile = db.load_user_profile(user_id)
            if fresh_profile and fresh_profile.name == display_name:
                pass
            else:
                return False

        except Exception:
            return False

    # Show current database content
    all_profiles = db.load_all_profiles()
    for user_id, _profile in all_profiles.items():
        pass

    # Clean up test user
    try:
        db.delete_user_profile("integration_test_user")
    except Exception:
        pass

    return True


if __name__ == "__main__":
    success = test_complete_integration()
    sys.exit(0 if success else 1)
