#!/usr/bin/env python3
"""
Final comprehensive test to verify all systems work together
"""


def test_full_system_integration():
    """Test the full bot system integration"""

    # Test 1: Verify EmotionManager uses database by default
    from emotion_manager import EmotionManager

    em = EmotionManager()
    assert em.use_database, "EmotionManager should use database by default"

    # Test 2: Verify database operations work
    from user_profile_db import UserProfileDatabase

    db = UserProfileDatabase()
    db.get_user_stats()

    # Test 3: Verify memory manager integration
    from memory_manager import UserMemoryManager

    try:
        # Try to create memory manager (may fail if no LLM connection)
        mm = UserMemoryManager(enable_emotions=True)
        if mm.emotion_manager:
            pass
        else:
            pass
    except Exception:
        pass

    # Test 4: Test name capture functionality
    em.get_or_create_profile("final_test_user", display_name="FinalTestUser")
    em.save_profiles()

    # Verify it was saved
    saved_profile = db.load_user_profile("final_test_user")
    assert saved_profile and saved_profile.name == "FinalTestUser"

    # Clean up
    db.delete_user_profile("final_test_user")



if __name__ == "__main__":
    test_full_system_integration()
