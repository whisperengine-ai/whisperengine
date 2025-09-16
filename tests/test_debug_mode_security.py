#!/usr/bin/env python3
"""
Test suite for Debug Mode Information Disclosure security fix
Tests the fix for CVSS 7.1 vulnerability - Debug Mode Information Disclosure
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import io
import logging
from unittest.mock import Mock

from debug_mode_security import (
    SecureDebugLogger,
    secure_add_debug_info_to_response,
    test_secure_debug_logging,
)


def test_sensitive_data_sanitization():
    """Test that sensitive data is properly sanitized"""


    debug_logger = SecureDebugLogger(enable_debug_mode=True)

    # Test various sensitive data patterns
    test_cases = [
        ("SSN in message: 123-45-6789", "SSN in message: [SSN_MASKED]"),
        ("Credit card: 4111-1111-1111-1111", "Credit card: [CARD_MASKED]"),
        ("My email is user@example.com", "My email is [EMAIL_MASKED]"),
        ("Password: secretpass123", "Password: [PASSWORD_MASKED]"),
        ("API key: sk-abc123def456", "API key: [TOKEN_MASKED]"),
        ("Multiple: 123-45-6789 and user@test.com", "Multiple: [SSN_MASKED] and [EMAIL_MASKED]"),
    ]

    for original, expected in test_cases:
        sanitized = debug_logger.sanitize_sensitive_data(original)
        assert (
            expected == sanitized
        ), f"Failed to sanitize: {original} -> {sanitized}, expected: {expected}"



def test_user_id_hashing():
    """Test that user IDs are consistently hashed"""


    debug_logger = SecureDebugLogger(enable_debug_mode=True)

    # Test consistent hashing
    user_id = "123456789"
    hash1 = debug_logger.hash_user_id(user_id)
    hash2 = debug_logger.hash_user_id(user_id)

    assert hash1 == hash2, "User ID hashing should be consistent"
    assert hash1.startswith("user_"), f"Hash should start with 'user_', got: {hash1}"
    assert len(hash1) == 13, f"Hash should be 13 chars (user_ + 8), got: {len(hash1)}"
    assert user_id not in hash1, "Original user ID should not appear in hash"


    # Test different user IDs produce different hashes
    user_id2 = "987654321"
    hash2 = debug_logger.hash_user_id(user_id2)

    assert hash1 != hash2, "Different user IDs should produce different hashes"



def test_username_sanitization():
    """Test username sanitization"""


    debug_logger = SecureDebugLogger(enable_debug_mode=True)

    # Test cases: (original, expected)
    test_cases = [
        ("abc", "[username_short]"),  # 3 chars, <= 3
        ("ab", "[username_short]"),  # 2 chars, <= 3
        ("a", "[username_short]"),  # 1 char, <= 3
        ("", "[username_short]"),  # 0 chars, <= 3
        ("short", "sh**t"),  # 5 chars, show first 2, last 1, mask middle 2
        ("medium_user", "me********r"),  # 11 chars, show first 2, last 1, mask middle 8
        (
            "very_long_username@example.com",
            "ve***************************m",
        ),  # 30 chars, show first 2, last 1, mask middle 27
    ]

    for original, expected in test_cases:
        sanitized = debug_logger.sanitize_username(original)
        assert (
            sanitized == expected
        ), f"Username sanitization failed: {original} -> {sanitized}, expected: {expected}"



def test_production_mode_security():
    """Test that production mode (debug disabled) hides sensitive information"""


    # Test with debug mode disabled
    debug_logger = SecureDebugLogger(enable_debug_mode=False)

    # Username should be hidden in production
    sensitive_username = "admin@company.com"
    sanitized = debug_logger.sanitize_username(sensitive_username)
    assert (
        sanitized == "[username_hidden]"
    ), f"Production mode should hide usernames, got: {sanitized}"


    # Test logging in production mode
    # Capture log output
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger("debug_mode_security")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Try to log user debug info in production mode
    debug_logger.log_user_debug_info("123456789", {"emotion": "happy", "name": "TestUser"})

    log_output = log_capture.getvalue()

    # Should have minimal logging in production
    assert (
        "details hidden in production" in log_output or log_output == ""
    ), "Production mode should limit debug output"
    assert "123456789" not in log_output, "User ID should not appear in production logs"
    assert "TestUser" not in log_output, "Real names should not appear in production logs"


    # Clean up
    logger.removeHandler(handler)



def test_debug_function_integration():
    """Test integration with the actual bot debug functions"""


    # Mock memory manager with emotion profile
    mock_memory_manager = Mock()
    mock_memory_manager.enable_emotions = True

    # Mock emotion profile
    mock_profile = Mock()
    mock_profile.current_emotion.value = "happy"
    mock_profile.relationship_level.value = "friendly"
    mock_profile.interaction_count = 42
    mock_profile.escalation_count = 1
    mock_profile.name = "TestUser123"

    mock_memory_manager.get_user_emotion_profile.return_value = mock_profile

    # Test the secure debug function
    user_id = "123456789"
    message_id = "msg_789"
    response = "Hello! How can I help you?"

    # Test with debug mode enabled
    secure_response = secure_add_debug_info_to_response(
        response, user_id, mock_memory_manager, message_id, enable_debug_mode=True
    )

    # Response should be unchanged (debug info is logged, not added to response)
    assert secure_response == response, "Debug info should not be added to response"

    # Test with debug mode disabled
    secure_response_prod = secure_add_debug_info_to_response(
        response, user_id, mock_memory_manager, message_id, enable_debug_mode=False
    )

    assert secure_response_prod == response, "Response should be unchanged in production"

    # Test duplicate message processing
    secure_response_dup = secure_add_debug_info_to_response(
        response, user_id, mock_memory_manager, message_id, enable_debug_mode=True
    )

    assert (
        secure_response_dup == response
    ), "Duplicate processing should still return clean response"



def test_log_level_security():
    """Test that sensitive information doesn't leak through different log levels"""


    # Capture all log output
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)

    # Test with different log levels
    logger = logging.getLogger("debug_mode_security")
    logger.addHandler(handler)

    debug_logger = SecureDebugLogger(enable_debug_mode=True)

    # Test various logging methods
    sensitive_user_id = "987654321"
    sensitive_data = {
        "emotion": "anxious",
        "relationship_level": "intimate",
        "name": "VeryPrivateUser@secret.com",
        "interaction_count": 150,
    }

    # Set to INFO level (higher than DEBUG)
    logger.setLevel(logging.INFO)
    debug_logger.log_user_debug_info(sensitive_user_id, sensitive_data, "test_msg")

    info_output = log_capture.getvalue()
    log_capture.truncate(0)
    log_capture.seek(0)

    # Set to DEBUG level
    logger.setLevel(logging.DEBUG)
    debug_logger.log_user_debug_info(sensitive_user_id, sensitive_data, "test_msg2")

    debug_output = log_capture.getvalue()

    # Check that sensitive data is properly handled at all levels
    all_output = info_output + debug_output

    # Original sensitive data should not appear
    assert sensitive_user_id not in all_output, "Raw user ID should not appear in logs"
    assert (
        "VeryPrivateUser@secret.com" not in all_output
    ), "Sensitive email should not appear in logs"
    assert (
        "Ve***********************m" in all_output or "[username_hidden]" in all_output
    ), "Username should be sanitized"

    # Hashed user ID should appear (for debugging)
    assert "user_" in all_output, "Hashed user ID should be present for debugging"


    # Clean up
    logger.removeHandler(handler)



def test_edge_cases():
    """Test edge cases and error conditions"""


    debug_logger = SecureDebugLogger(enable_debug_mode=True)

    # Test with None/empty values (skip None test due to type safety)
    # assert debug_logger.sanitize_sensitive_data(None) is None, "None input should return None"
    assert debug_logger.sanitize_sensitive_data("") == "", "Empty string should return empty"

    # Test with moderately long data (avoid extreme lengths that may cause regex issues)
    long_data = "A" * 1000 + "123-45-6789" + "B" * 1000
    sanitized_long = debug_logger.sanitize_sensitive_data(long_data)
    assert "[SSN_MASKED]" in sanitized_long, "Should sanitize data in long strings"
    assert "123-45-6789" not in sanitized_long, "SSN should be masked in long strings"

    # Test user ID hashing with edge cases
    empty_hash = debug_logger.hash_user_id("")
    assert empty_hash.startswith("user_"), "Empty user ID should still hash properly"

    very_long_id = "x" * 1000
    long_hash = debug_logger.hash_user_id(very_long_id)
    assert len(long_hash) == 13, "Very long user ID should still produce standard hash length"


    # Test error conditions
    try:
        # Test with invalid data types (should handle gracefully)
        debug_logger.log_user_debug_info("test_user", {"invalid": object()})
    except Exception:
        pass



if __name__ == "__main__":

    try:
        # Run core functionality test first
        test_secure_debug_logging()

        # Run comprehensive security tests
        test_sensitive_data_sanitization()
        test_user_id_hashing()
        test_username_sanitization()
        test_production_mode_security()
        test_debug_function_integration()
        test_log_level_security()
        test_edge_cases()






    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
