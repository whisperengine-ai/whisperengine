"""
Test Suite for Error Message Security System
Tests CVSS 5.3 Error Message Information Disclosure vulnerability fixes
"""

import unittest
from unittest.mock import Mock, patch
import discord
from error_message_security import (
    ErrorMessageSecurity,
    ErrorSeverity,
    ErrorContext,
    secure_error_handler,
    sanitize_error_for_logging,
)


class TestErrorMessageSecurity(unittest.TestCase):
    """Test error message sanitization and security features"""

    def setUp(self):
        self.error_security = ErrorMessageSecurity()

    def test_file_path_sanitization(self):
        """Test that file paths are properly sanitized"""
        error_msg = "Failed to read /Users/johndoe/secret/database.db"
        response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.PUBLIC_CHANNEL
        )

        # File path should be redacted
        self.assertIn("[PATH_REDACTED]", response.user_message)
        self.assertNotIn("/Users/johndoe", response.user_message)

        # Log message should preserve original for debugging
        self.assertIn("/Users/johndoe", response.log_message)

    def test_api_endpoint_sanitization(self):
        """Test that API endpoints are properly sanitized"""
        error_msg = "Connection failed to https://api.openai.com/v1/chat/completions"
        response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.PUBLIC_CHANNEL
        )

        # API endpoint should be redacted
        self.assertIn("[OPENAI_API_REDACTED]", response.user_message)
        self.assertNotIn("openai.com", response.user_message)

    def test_user_id_sanitization(self):
        """Test that Discord user IDs are properly sanitized"""
        error_msg = "Failed to store memory for user_id: 123456789012345678"
        response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.PUBLIC_CHANNEL
        )

        # User ID should be redacted
        self.assertIn("[USER_ID_REDACTED]", response.user_message)
        self.assertNotIn("123456789012345678", response.user_message)

    def test_database_schema_sanitization(self):
        """Test that database schema information is sanitized"""
        error_msg = 'No memories found in collection "user_memories_sensitive"'
        response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.PUBLIC_CHANNEL
        )

        # Collection name should be redacted
        self.assertIn("[COLLECTION_REDACTED]", response.user_message)
        self.assertNotIn("user_memories_sensitive", response.user_message)

    def test_api_key_sanitization(self):
        """Test that API keys are properly sanitized"""
        error_msg = "Authentication failed with token sk-1234567890abcdef1234567890abcdef"
        response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.PUBLIC_CHANNEL
        )

        # API key should be redacted
        self.assertIn("[API_KEY_REDACTED]", response.user_message)
        self.assertNotIn("sk-1234567890abcdef", response.user_message)

    def test_error_severity_classification(self):
        """Test error severity classification"""

        # Critical errors
        critical_msg = "Authentication failed: invalid API key"
        response = self.error_security.sanitize_error_message(critical_msg)
        self.assertEqual(response.severity, ErrorSeverity.CRITICAL)

        # High severity errors
        high_msg = "Database connection timeout"
        response = self.error_security.sanitize_error_message(high_msg)
        self.assertEqual(response.severity, ErrorSeverity.HIGH)

        # Medium severity errors
        medium_msg = "Invalid input format"
        response = self.error_security.sanitize_error_message(medium_msg)
        self.assertEqual(response.severity, ErrorSeverity.MEDIUM)

        # Low severity errors
        low_msg = "Something went wrong"
        response = self.error_security.sanitize_error_message(low_msg)
        self.assertEqual(response.severity, ErrorSeverity.LOW)

    def test_context_based_filtering(self):
        """Test that filtering varies based on context"""
        error_msg = "TimeoutError: Database query took too long"

        # Public channel - most restrictive
        public_response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.PUBLIC_CHANNEL
        )

        # Private DM - less restrictive
        dm_response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.PRIVATE_DM
        )

        # Admin channel - minimal filtering
        admin_response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.ADMIN_CHANNEL
        )

        # Public should be most sanitized
        self.assertIn("Error occurred", public_response.user_message)

        # DM should preserve some technical detail
        self.assertIn("TimeoutError", dm_response.user_message)

        # Admin should preserve most detail
        self.assertIn("Database query", admin_response.user_message)

    def test_generic_error_messages(self):
        """Test that generic messages are used for high/critical severity"""

        critical_msg = "SQL injection detected in user input"
        response = self.error_security.sanitize_error_message(
            critical_msg, context=ErrorContext.PUBLIC_CHANNEL, error_type="validation_error"
        )

        # Should use generic message instead of exposing security details
        self.assertEqual(
            response.user_message,
            "There was an issue with the input provided. Please check and try again.",
        )
        self.assertNotIn("SQL injection", response.user_message)

    def test_suspicious_error_detection(self):
        """Test detection of potentially malicious error patterns"""

        # SQL injection attempt
        sql_msg = "Error processing: SELECT * FROM users UNION SELECT password FROM admin"
        response = self.error_security.sanitize_error_message(sql_msg)
        self.assertTrue(response.requires_admin_notification)

        # XSS attempt
        xss_msg = "Parse error: <script>alert('xss')</script>"
        response = self.error_security.sanitize_error_message(xss_msg)
        self.assertTrue(response.requires_admin_notification)

        # Normal error should not trigger notification
        normal_msg = "Connection timeout"
        response = self.error_security.sanitize_error_message(normal_msg)
        self.assertFalse(response.requires_admin_notification)

    def test_error_code_generation(self):
        """Test that unique error codes are generated"""

        error_msg = "Test error message"
        response1 = self.error_security.sanitize_error_message(error_msg)
        response2 = self.error_security.sanitize_error_message(error_msg)

        # Same error should generate same code (for tracking)
        self.assertEqual(response1.error_code, response2.error_code)

        # Different errors should generate different codes
        different_msg = "Different error message"
        response3 = self.error_security.sanitize_error_message(different_msg)
        self.assertNotEqual(response1.error_code, response3.error_code)

        # Error codes should follow expected format
        self.assertRegex(response1.error_code, r"ERR-\d{8}-[A-F0-9]{8}")

    def test_stack_trace_filtering(self):
        """Test that stack traces are properly filtered"""

        error_msg = """Traceback (most recent call last):
  File "/Users/user/bot/memory_manager.py", line 123, in store_memory
    raise Exception("Database connection failed")
Exception: Database connection failed"""

        # Public channel should completely remove stack trace
        public_response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.PUBLIC_CHANNEL
        )
        self.assertNotIn("Traceback", public_response.user_message)
        self.assertNotIn("/Users/user", public_response.user_message)

        # Private DM should show sanitized version
        dm_response = self.error_security.sanitize_error_message(
            error_msg, context=ErrorContext.PRIVATE_DM
        )
        self.assertIn("[Stack trace omitted]", dm_response.user_message)

    def test_error_frequency_tracking(self):
        """Test that error frequency is tracked for security monitoring"""

        error_msg = "Repeated error pattern"

        # Simulate multiple occurrences of same error
        for _ in range(12):  # Above threshold of 10
            self.error_security.sanitize_error_message(error_msg)

        # Check that pattern is being tracked
        self.assertTrue(len(self.error_security.error_counts) > 0)

        # Find our pattern in the counts
        pattern_found = False
        for pattern_hash, data in self.error_security.error_counts.items():
            if data["count"] > 10:
                pattern_found = True
                self.assertEqual(data["sample_message"], error_msg[:100])
                break

        self.assertTrue(pattern_found, "High frequency error pattern should be tracked")

    @patch("discord.Message")
    def test_discord_error_handling(self, mock_message):
        """Test Discord-specific error handling with context"""

        # Setup mock Discord message
        mock_channel = Mock()
        mock_channel.type = discord.ChannelType.text
        mock_guild = Mock()
        mock_guild.id = 123456789
        mock_channel.guild = mock_guild
        mock_message.channel = mock_channel
        mock_message.guild = mock_guild

        # Test various Discord errors
        test_cases = [
            (discord.HTTPException(response=Mock(), message="Rate limited"), "rate_limit_error"),
            (discord.Forbidden(response=Mock(), message="Missing permissions"), "permission_error"),
            (ConnectionError("Connection failed"), "connection_error"),
            (TimeoutError("Request timeout"), "timeout_error"),
        ]

        for error, expected_type in test_cases:
            with self.subTest(error=error):
                result = self.error_security.handle_discord_error(error, mock_message)

                # Should return safe error message
                self.assertIsInstance(result, str)
                self.assertNotIn(str(error), result)  # Original error not exposed

                # Should be a generic message appropriate for error type
                expected_generic = self.error_security.generic_messages.get(
                    expected_type, self.error_security.generic_messages["unknown_error"]
                )
                self.assertEqual(result, expected_generic)

    def test_logging_sanitization(self):
        """Test sanitization for logging purposes"""

        sensitive_msg = "User 123456789012345678 failed auth with token sk-abcd1234"
        sanitized = sanitize_error_for_logging(sensitive_msg)

        # Should sanitize sensitive information even for logs
        self.assertIn("[USER_ID_REDACTED]", sanitized)
        self.assertIn("[API_KEY_REDACTED]", sanitized)
        self.assertNotIn("123456789012345678", sanitized)
        self.assertNotIn("sk-abcd1234", sanitized)

    def test_secure_error_handler_function(self):
        """Test the convenient secure_error_handler function"""

        # Create a test error
        test_error = ValueError("Test validation error with /secret/path")

        # Test with mock Discord context
        mock_message = Mock()
        mock_message.channel = Mock()
        mock_message.channel.type = discord.ChannelType.private
        mock_message.guild = None

        result = secure_error_handler(test_error, mock_message)

        # Should return sanitized message
        self.assertIsInstance(result, str)
        self.assertNotIn("/secret/path", result)
        self.assertIn("There was an issue with the input provided", result)

    def test_memory_address_sanitization(self):
        """Test that memory addresses are sanitized"""

        error_msg = "Segmentation fault at memory address 0x7fff5fbff7c0"
        response = self.error_security.sanitize_error_message(error_msg)

        self.assertIn("[ADDR_REDACTED]", response.user_message)
        self.assertNotIn("0x7fff5fbff7c0", response.user_message)

    def test_environment_variable_sanitization(self):
        """Test that environment variables are sanitized"""

        error_msg = 'Missing environment variable: os.environ["SECRET_API_KEY"]'
        response = self.error_security.sanitize_error_message(error_msg)

        self.assertIn("[ENV_VAR_REDACTED]", response.user_message)
        self.assertNotIn("SECRET_API_KEY", response.user_message)

    def test_port_and_pid_sanitization(self):
        """Test that ports and process IDs are sanitized"""

        error_msg = "Service failed on port 8080, PID 12345"
        response = self.error_security.sanitize_error_message(error_msg)

        self.assertIn("[PORT_REDACTED]", response.user_message)
        self.assertIn("[PID_REDACTED]", response.user_message)
        self.assertNotIn("8080", response.user_message)
        self.assertNotIn("12345", response.user_message)


class TestErrorSecurityIntegration(unittest.TestCase):
    """Integration tests for error security with other components"""

    def test_integration_with_secure_logging(self):
        """Test that error security integrates properly with secure logging"""

        with patch("error_message_security.HAS_SECURE_LOGGING", True):
            with patch("error_message_security.secure_logger") as mock_logger:
                error_security = ErrorMessageSecurity()

                # Test critical error logging
                critical_msg = "Authentication bypass detected"
                response = error_security.sanitize_error_message(
                    critical_msg, error_type="security_error"
                )

                # Should have called secure logging
                mock_logger.log_security_event.assert_called()

                # Verify correct parameters were passed
                call_args = mock_logger.log_security_event.call_args
                self.assertIn("critical_error", str(call_args))
                self.assertEqual(call_args[1]["threat_level"], "critical")

    def test_admin_notification_trigger(self):
        """Test that admin notifications are triggered for critical errors"""

        critical_errors = [
            "SQL injection detected: UNION SELECT * FROM users",
            "XSS attempt: <script>alert('hack')</script>",
            "Directory traversal: ../../etc/passwd",
            "Authentication bypass detected",
        ]

        for error_msg in critical_errors:
            with self.subTest(error=error_msg):
                error_security = ErrorMessageSecurity()
                response = error_security.sanitize_error_message(error_msg)

                self.assertTrue(
                    response.requires_admin_notification,
                    f"Error should trigger admin notification: {error_msg}",
                )


if __name__ == "__main__":
    unittest.main()
