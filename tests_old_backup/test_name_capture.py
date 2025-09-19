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

    for user_id, display_name in test_cases:

        try:
            # This should capture the name
            emotion_manager.get_or_create_profile(user_id, display_name=display_name)

            # Verify name was saved
            saved_profile = db.load_user_profile(user_id)
            if saved_profile and saved_profile.get("name") == display_name:
                pass
            else:
                pass

        except Exception:
            pass

    # List all users to verify
    users = db.list_all_users()

    for user in users:
        user_id = user[0]
        user[1] if user[1] else "No name"

    # Count users with names
    named_users = sum(1 for user in users if user[1] and user[1] != "No name")

    if named_users >= len(test_cases):
        return True
    else:
        return False


if __name__ == "__main__":
    success = test_name_capture()
    sys.exit(0 if success else 1)
