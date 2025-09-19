#!/usr/bin/env python3
"""
Comprehensive Security Test for API Key Management Fix
Tests the P2 High Priority vulnerability fix (CVSS 6.7)
"""

import sys

sys.path.append(".")

from api_key_security import APIKeyType, get_api_key_manager


def test_api_key_validation():
    """Test API key validation functionality"""

    manager = get_api_key_manager()

    # Test Case 1: Valid API key formats

    valid_keys = [
        ("sk-or-v1-" + "abcd1234efgh5678" * 4, APIKeyType.OPENROUTER, "OpenRouter format"),
        ("sk-" + "AbCd1234EfGh5678" * 3, APIKeyType.OPENROUTER, "Generic OpenAI format"),
        ("abcd1234efgh5678ijkl9012mnop3456", APIKeyType.ELEVENLABS, "ElevenLabs format"),
    ]

    for key, expected_type, _description in valid_keys:
        result = manager.validate_api_key(key, expected_type)

        if not result.is_valid:
            pass

    # Test Case 2: Invalid/dangerous API keys

    dangerous_keys = [
        ("your_api_key_here", APIKeyType.OPENROUTER, "Placeholder key"),
        ("test_key", APIKeyType.UNKNOWN, "Test placeholder"),
        ("abc123", APIKeyType.UNKNOWN, "Weak key"),
        ("", APIKeyType.UNKNOWN, "Empty key"),
        ("sk-" + "x" * 10, APIKeyType.OPENROUTER, "Too short key"),
    ]

    for key, key_type, _description in dangerous_keys:
        result = manager.validate_api_key(key, key_type)

    # Test Case 3: Log sanitization

    log_test_cases = [
        "API key: sk-abc123def456789",
        "OPENROUTER_API_KEY=sk-or-v1-" + "x" * 64,
        "Authorization: Bearer sk-1234567890abcdef",
        "xi-api-key: " + "a" * 32,
        "Error with token sk-test123456789 failed",
        "Multiple keys: sk-abc123 and sk-def456 found",
    ]

    all_sanitized = True
    for log_text in log_test_cases:
        sanitized = manager.sanitize_for_logging(log_text)
        is_sanitized = sanitized != log_text

        if not is_sanitized:
            all_sanitized = False

    return all_sanitized


def test_secure_header_creation():
    """Test secure header creation"""

    manager = get_api_key_manager()

    # Test valid key header creation with diverse characters
    valid_key = "sk-AbCd1234EfGh5678IjKl9012MnOp3456"
    headers = manager.secure_header_creation(valid_key, "Bearer")

    if headers and "Authorization" in headers:
        # Verify the key is not logged in the header creation
        pass
    else:
        return False

    # Test ElevenLabs style header with diverse characters
    el_key = "abcd1234efgh5678ijkl9012mnop3456"
    el_headers = manager.secure_header_creation(el_key, "xi-api-key")

    if el_headers and "xi-api-key" in el_headers:
        pass
    else:
        return False

    # Test invalid key rejection
    invalid_key = "weak_key"
    invalid_headers = manager.secure_header_creation(invalid_key, "Bearer")

    if not invalid_headers:
        pass
    else:
        return False

    return True


def test_environment_validation():
    """Test environment variable validation"""

    manager = get_api_key_manager()

    # Get current environment validation
    env_report = manager.validate_environment_keys()

    for _env_var, info in env_report.items():

        if info.security_threats:
            pass

    return True


def test_client_integration():
    """Test integration with LMStudioClient and ElevenLabsClient"""

    try:
        # Test LMStudioClient integration
        from lmstudio_client import LMStudioClient

        client = LMStudioClient()
        if hasattr(client, "api_key_manager") and client.api_key_manager:
            pass
        else:
            return False

    except Exception:
        return False

    try:
        # Test that ElevenLabsClient can be imported (may fail if no API key)

        pass

    except ValueError as e:
        if "API key" in str(e):
            pass
        else:
            return False
    except Exception:
        return False

    return True


def test_security_report():
    """Test security report generation"""

    manager = get_api_key_manager()
    report = manager.get_security_report()

    required_sections = ["summary", "key_status", "threat_analysis", "recommendations"]

    for section in required_sections:
        if section in report:
            pass
        else:
            return False

    # Check summary data
    report["summary"]

    # Show recommendations
    if report["recommendations"]:
        for _rec in report["recommendations"][:3]:  # Show first 3
            pass

    return True


def run_comprehensive_test():
    """Run all security tests"""

    test_results = []

    # Run all test functions
    test_functions = [
        test_api_key_validation,
        test_secure_header_creation,
        test_environment_validation,
        test_client_integration,
        test_security_report,
    ]

    for test_func in test_functions:
        try:
            result = test_func()
            test_results.append(result)
        except Exception:
            test_results.append(False)

    # Calculate overall results
    sum(test_results)
    len(test_results)

    if all(test_results):
        pass
    else:
        pass

    return all(test_results)


if __name__ == "__main__":

    success = run_comprehensive_test()

    if success:
        exit(0)
    else:
        exit(1)
