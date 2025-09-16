#!/usr/bin/env python3
"""
Test the emotion manager name capture system
"""

import sys

from emotion_manager import EmotionManager
from user_profile_db import UserProfileDatabase


def test_name_capture():
    """Test that the emotion manager captures and updates user names"""

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

        try:
            # This should capture the name
            emotion_manager.get_or_create_profile(user_id, display_name=display_name)

            # Save the profiles to database (this is what the Discord bot does)
            emotion_manager.save_profiles()

            # Verify name was saved
            saved_profile = db.load_user_profile(user_id)
            if saved_profile and saved_profile.name == display_name:
                created_users += 1
            else:
                if saved_profile:
                    pass

        except Exception:
            pass


    # List all users to verify
    all_profiles = db.load_all_profiles()

    for user_id, _profile in all_profiles.items():
        pass

    # Count users with names
    sum(
        1 for profile in all_profiles.values() if profile.name and profile.name != "No name"
    )

    if created_users >= len(test_cases):
        return True
    else:
        return False


if __name__ == "__main__":
    success = test_name_capture()
    sys.exit(0 if success else 1)
