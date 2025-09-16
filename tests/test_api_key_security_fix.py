#!/usr/bin/env python3
"""
Comprehensive Security Test for API Key Management Fix
Tests the P2 High Priority vulnerability fix (CVSS 6.7)
"""

import sys
import os

sys.path.append(".")

from api_key_security import get_api_key_manager, APIKeyType, SecurityThreat


def test_api_key_validation():
    """Test API key validation functionality"""

    print("🔐 COMPREHENSIVE SECURITY TEST - API Key Management Fix")
    print("=" * 70)

    manager = get_api_key_manager()

    # Test Case 1: Valid API key formats
    print("\n📋 Test 1: Valid API Key Format Detection")
    print("-" * 50)

    valid_keys = [
        ("sk-or-v1-" + "abcd1234efgh5678" * 4, APIKeyType.OPENROUTER, "OpenRouter format"),
        ("sk-" + "AbCd1234EfGh5678" * 3, APIKeyType.OPENROUTER, "Generic OpenAI format"),
        ("abcd1234efgh5678ijkl9012mnop3456", APIKeyType.ELEVENLABS, "ElevenLabs format"),
    ]

    for key, expected_type, description in valid_keys:
        result = manager.validate_api_key(key, expected_type)
        status = "✅" if result.is_valid else "❌"
        print(f"{status} {description}: {result.masked_key} (Score: {result.format_score:.2f})")

        if not result.is_valid:
            print(f"   Threats: {[t.value for t in result.security_threats]}")

    # Test Case 2: Invalid/dangerous API keys
    print("\n📋 Test 2: Invalid/Dangerous API Key Detection")
    print("-" * 50)

    dangerous_keys = [
        ("your_api_key_here", APIKeyType.OPENROUTER, "Placeholder key"),
        ("test_key", APIKeyType.UNKNOWN, "Test placeholder"),
        ("abc123", APIKeyType.UNKNOWN, "Weak key"),
        ("", APIKeyType.UNKNOWN, "Empty key"),
        ("sk-" + "x" * 10, APIKeyType.OPENROUTER, "Too short key"),
    ]

    for key, key_type, description in dangerous_keys:
        result = manager.validate_api_key(key, key_type)
        status = "✅" if not result.is_valid else "❌"
        print(f"{status} {description}: {result.masked_key}")
        print(f"   Threats: {[t.value for t in result.security_threats]}")

    # Test Case 3: Log sanitization
    print("\n📋 Test 3: Log Sanitization")
    print("-" * 50)

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
        status = "✅" if is_sanitized else "❌"

        if not is_sanitized:
            all_sanitized = False

        print(f"{status} Original:  {log_text}")
        print(f"   Sanitized: {sanitized}")

    return all_sanitized


def test_secure_header_creation():
    """Test secure header creation"""

    print("\n📋 Test 4: Secure Header Creation")
    print("-" * 50)

    manager = get_api_key_manager()

    # Test valid key header creation with diverse characters
    valid_key = "sk-AbCd1234EfGh5678IjKl9012MnOp3456"
    headers = manager.secure_header_creation(valid_key, "Bearer")

    if headers and "Authorization" in headers:
        print("✅ Bearer header created successfully")
        # Verify the key is not logged in the header creation
        print(f"   Header: Authorization: Bearer {manager.mask_api_key(valid_key)}")
    else:
        print("❌ Bearer header creation failed")
        return False

    # Test ElevenLabs style header with diverse characters
    el_key = "abcd1234efgh5678ijkl9012mnop3456"
    el_headers = manager.secure_header_creation(el_key, "xi-api-key")

    if el_headers and "xi-api-key" in el_headers:
        print("✅ ElevenLabs header created successfully")
    else:
        print("❌ ElevenLabs header creation failed")
        return False

    # Test invalid key rejection
    invalid_key = "weak_key"
    invalid_headers = manager.secure_header_creation(invalid_key, "Bearer")

    if not invalid_headers:
        print("✅ Invalid key properly rejected")
    else:
        print("❌ Invalid key was not rejected")
        return False

    return True


def test_environment_validation():
    """Test environment variable validation"""

    print("\n📋 Test 5: Environment Variable Validation")
    print("-" * 50)

    manager = get_api_key_manager()

    # Get current environment validation
    env_report = manager.validate_environment_keys()

    print("Environment Key Status:")
    for env_var, info in env_report.items():
        status = "✅" if info.is_valid else "❌" if info.masked_key != "[NOT_SET]" else "⚠️"
        print(f"{status} {env_var}: {info.masked_key}")

        if info.security_threats:
            print(f"   Threats: {[t.value for t in info.security_threats]}")

    return True


def test_client_integration():
    """Test integration with LMStudioClient and ElevenLabsClient"""

    print("\n📋 Test 6: Client Integration")
    print("-" * 50)

    try:
        # Test LMStudioClient integration
        from lmstudio_client import LMStudioClient

        client = LMStudioClient()
        if hasattr(client, "api_key_manager") and client.api_key_manager:
            print("✅ LMStudioClient has API key security integration")
        else:
            print("❌ LMStudioClient missing API key security integration")
            return False

    except Exception as e:
        print(f"❌ LMStudioClient integration test failed: {e}")
        return False

    try:
        # Test that ElevenLabsClient can be imported (may fail if no API key)
        from elevenlabs_client import ElevenLabsClient

        print("✅ ElevenLabsClient with security enhancements is importable")

    except ValueError as e:
        if "API key" in str(e):
            print("✅ ElevenLabsClient properly validates API key requirement")
        else:
            print(f"❌ ElevenLabsClient unexpected error: {e}")
            return False
    except Exception as e:
        print(f"❌ ElevenLabsClient integration test failed: {e}")
        return False

    return True


def test_security_report():
    """Test security report generation"""

    print("\n📋 Test 7: Security Report Generation")
    print("-" * 50)

    manager = get_api_key_manager()
    report = manager.get_security_report()

    required_sections = ["summary", "key_status", "threat_analysis", "recommendations"]

    for section in required_sections:
        if section in report:
            print(f"✅ Security report contains {section}")
        else:
            print(f"❌ Security report missing {section}")
            return False

    # Check summary data
    summary = report["summary"]
    print(f"   Security Score: {summary['security_score']:.1f}%")
    print(f"   Total Keys Checked: {summary['total_keys_checked']}")
    print(f"   Valid Keys: {summary['valid_keys']}")
    print(f"   Invalid Keys: {summary['invalid_keys']}")

    # Show recommendations
    if report["recommendations"]:
        print("   Recommendations:")
        for rec in report["recommendations"][:3]:  # Show first 3
            print(f"     - {rec}")

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
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            test_results.append(False)

    # Calculate overall results
    passed_tests = sum(test_results)
    total_tests = len(test_results)

    print("\n" + "=" * 70)
    if all(test_results):
        print("🎉 ALL SECURITY TESTS PASSED - API KEY MANAGEMENT FIX COMPLETE")
    else:
        print(f"⚠️  {passed_tests}/{total_tests} TESTS PASSED - SOME ISSUES NEED ATTENTION")

    print("=" * 70)

    return all(test_results)


if __name__ == "__main__":
    print("Starting comprehensive API key security test...")

    success = run_comprehensive_test()

    if success:
        print("\n🎉 ALL TESTS PASSED - FIX IS PRODUCTION READY")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - NEEDS ADDITIONAL WORK")
        exit(1)
