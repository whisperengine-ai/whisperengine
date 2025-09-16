"""
Test Suite for Admin Access Control System
Tests CVSS 5.4 Administrative Access Control Gaps fixes

This test suite validates that the admin access control system properly:
- Enforces multi-level admin authorization
- Manages admin sessions with timeouts
- Performs operation-level permission checks
- Logs admin activities for audit trail
- Prevents privilege escalation attacks
- Handles failed access attempts appropriately
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

from admin_access_control import (
    AdminAccessController,
    AdminLevel,
    AdminOperation,
)
from discord.ext import commands


class TestAdminAccessControl(unittest.TestCase):
    """Test suite for admin access control functionality"""

    def setUp(self):
        """Set up test environment"""
        self.controller = AdminAccessController(
            session_timeout_minutes=60,
            elevation_timeout_minutes=15,
            max_failed_attempts=3,
            lockout_duration_minutes=30,
        )

        # Mock Discord objects
        self.mock_user = Mock()
        self.mock_user.id = 123456789012345678
        self.mock_user.name = "TestUser"

        self.mock_admin_user = Mock()
        self.mock_admin_user.id = 987654321098765432
        self.mock_admin_user.name = "AdminUser"

        self.mock_super_admin_user = Mock()
        self.mock_super_admin_user.id = 111222333444555666
        self.mock_super_admin_user.name = "SuperAdmin"

        self.mock_guild = Mock()
        self.mock_guild.id = 555666777888999000

        self.mock_channel = Mock()
        self.mock_channel.id = 333444555666777888

        # Mock Discord contexts
        self.mock_ctx = Mock(spec=commands.Context)
        self.mock_ctx.author = self.mock_user
        self.mock_ctx.guild = self.mock_guild
        self.mock_ctx.channel = self.mock_channel

        self.mock_admin_ctx = Mock(spec=commands.Context)
        self.mock_admin_ctx.author = self.mock_admin_user
        self.mock_admin_ctx.guild = self.mock_guild
        self.mock_admin_ctx.channel = self.mock_channel

        self.mock_super_admin_ctx = Mock(spec=commands.Context)
        self.mock_super_admin_ctx.author = self.mock_super_admin_user
        self.mock_super_admin_ctx.guild = self.mock_guild
        self.mock_super_admin_ctx.channel = self.mock_channel

        # Configure admin levels
        admin_config = {
            "admins": {
                str(self.mock_admin_user.id): "administrator",
                str(self.mock_super_admin_user.id): "super_admin",
            },
            "owners": [str(self.mock_super_admin_user.id)],
        }
        self.controller.load_admin_config(admin_config)

    def test_admin_level_assignment(self):
        """Test that admin levels are correctly assigned"""

        # Test non-admin user
        normal_level = self.controller.get_user_admin_level(self.mock_ctx)
        self.assertEqual(normal_level, AdminLevel.NONE)

        # Test admin user
        admin_level = self.controller.get_user_admin_level(self.mock_admin_ctx)
        self.assertEqual(admin_level, AdminLevel.ADMINISTRATOR)

        # Test super admin user
        super_admin_level = self.controller.get_user_admin_level(self.mock_super_admin_ctx)
        self.assertEqual(super_admin_level, AdminLevel.SUPER_ADMIN)


    def test_admin_session_creation(self):
        """Test admin session creation and validation"""

        # Test session creation for admin user
        session = self.controller.create_admin_session(self.mock_admin_ctx)
        self.assertIsNotNone(session)
        self.assertEqual(session.user_id, self.mock_admin_user.id)
        self.assertEqual(session.admin_level, AdminLevel.ADMINISTRATOR)
        self.assertIsNotNone(session.session_token)

        # Test session creation for non-admin user (should fail)
        no_session = self.controller.create_admin_session(self.mock_ctx)
        self.assertIsNone(no_session)


    def test_session_timeout(self):
        """Test admin session timeout functionality"""

        # Create session
        session = self.controller.create_admin_session(self.mock_admin_ctx)
        self.assertIsNotNone(session)

        # Validate session (should be valid)
        valid_session = self.controller.validate_admin_session(self.mock_admin_user.id)
        self.assertIsNotNone(valid_session)

        # Simulate timeout by setting last activity to past
        session.last_activity = datetime.utcnow() - timedelta(hours=2)

        # Validate session (should be expired)
        expired_session = self.controller.validate_admin_session(self.mock_admin_user.id)
        self.assertIsNone(expired_session)


    def test_operation_permission_checks(self):
        """Test operation-level permission checking"""

        # Test moderator operation with admin user (should succeed)
        allowed, reason = self.controller.check_operation_permission(
            self.mock_admin_ctx, AdminOperation.ADD_USER_FACT
        )
        self.assertTrue(allowed)

        # Test super admin operation with admin user (should fail)
        denied, reason = self.controller.check_operation_permission(
            self.mock_admin_ctx, AdminOperation.DEBUG_MODE
        )
        self.assertFalse(denied)
        self.assertIn("requires SUPER_ADMIN", reason)

        # Test super admin operation with super admin user (should succeed)
        allowed, reason = self.controller.check_operation_permission(
            self.mock_super_admin_ctx, AdminOperation.DEBUG_MODE
        )
        self.assertTrue(allowed)


    def test_privilege_elevation(self):
        """Test privilege elevation for sensitive operations"""

        # Create super admin session
        session = self.controller.create_admin_session(self.mock_super_admin_ctx)
        self.assertIsNotNone(session)

        # Test elevation (should succeed for super admin)
        success, message = self.controller.elevate_privileges(self.mock_super_admin_ctx)
        self.assertTrue(success)
        self.assertIn("elevated", message)

        # Check that session is now elevated
        updated_session = self.controller.validate_admin_session(self.mock_super_admin_user.id)
        self.assertTrue(updated_session.is_elevated)
        self.assertIsNotNone(updated_session.elevation_expires)

        # Test elevation with regular admin (should fail)
        success, message = self.controller.elevate_privileges(self.mock_admin_ctx)
        self.assertFalse(success)
        self.assertIn("requires Super Admin", message)


    def test_failed_attempt_tracking(self):
        """Test failed access attempt tracking and lockout"""

        user_id = self.mock_user.id

        # Simulate failed attempts
        for _i in range(3):
            self.controller._record_failed_attempt(user_id, "test_operation")

        # User should now be locked
        is_locked = self.controller._is_user_locked(user_id)
        self.assertTrue(is_locked)

        # Admin level check should return NONE for locked user
        level = self.controller.get_user_admin_level(self.mock_ctx)
        self.assertEqual(level, AdminLevel.NONE)


    def test_admin_audit_logging(self):
        """Test admin operation audit logging"""

        # Log some admin operations
        self.controller.log_admin_operation(
            self.mock_admin_ctx, AdminOperation.ADD_GLOBAL_FACT, True, "Added fact: Test fact"
        )

        self.controller.log_admin_operation(
            self.mock_admin_ctx,
            AdminOperation.REMOVE_GLOBAL_FACT,
            False,
            "Failed to remove non-existent fact",
        )

        # Check audit log
        self.assertEqual(len(self.controller.audit_log), 2)

        # Check first entry
        first_entry = self.controller.audit_log[0]
        self.assertEqual(first_entry.user_id, self.mock_admin_user.id)
        self.assertEqual(first_entry.operation, AdminOperation.ADD_GLOBAL_FACT)
        self.assertTrue(first_entry.success)

        # Check second entry
        second_entry = self.controller.audit_log[1]
        self.assertEqual(second_entry.user_id, self.mock_admin_user.id)
        self.assertEqual(second_entry.operation, AdminOperation.REMOVE_GLOBAL_FACT)
        self.assertFalse(second_entry.success)


    def test_admin_status_reporting(self):
        """Test admin status information retrieval"""

        # Create session for testing
        self.controller.create_admin_session(self.mock_admin_ctx)

        # Get admin status
        status = self.controller.get_admin_status(self.mock_admin_ctx)

        # Verify status information
        self.assertEqual(status["user_id"], self.mock_admin_user.id)
        self.assertEqual(status["username"], self.mock_admin_user.name)
        self.assertEqual(status["admin_level"], "ADMINISTRATOR")
        self.assertTrue(status["has_session"])
        self.assertFalse(status["is_locked"])


    def test_audit_summary_generation(self):
        """Test audit summary generation"""

        # Generate some audit entries
        for i in range(5):
            self.controller.log_admin_operation(
                self.mock_admin_ctx,
                AdminOperation.ADD_GLOBAL_FACT,
                i % 2 == 0,  # Alternate success/failure
                f"Test operation {i}",
            )

        # Get audit summary
        summary = self.controller.get_audit_summary(hours=24)

        # Verify summary
        self.assertEqual(summary["total_operations"], 5)
        self.assertEqual(summary["successful_operations"], 3)
        self.assertEqual(summary["failed_operations"], 2)
        self.assertEqual(summary["unique_users"], 1)


    def test_session_cleanup(self):
        """Test cleanup of expired sessions"""

        # Create session
        session = self.controller.create_admin_session(self.mock_admin_ctx)
        self.assertEqual(len(self.controller.active_sessions), 1)

        # Expire the session
        session.last_activity = datetime.utcnow() - timedelta(hours=2)

        # Run cleanup
        cleaned_count = self.controller.cleanup_expired_sessions()

        # Verify cleanup
        self.assertEqual(cleaned_count, 1)
        self.assertEqual(len(self.controller.active_sessions), 0)


    def test_privilege_elevation_timeout(self):
        """Test privilege elevation timeout"""

        # Create super admin session and elevate
        session = self.controller.create_admin_session(self.mock_super_admin_ctx)
        success, _ = self.controller.elevate_privileges(self.mock_super_admin_ctx)
        self.assertTrue(success)

        # Verify elevation
        self.assertTrue(session.is_elevated)

        # Simulate elevation timeout
        session.elevation_expires = datetime.utcnow() - timedelta(minutes=1)

        # Validate session (should clear elevation)
        updated_session = self.controller.validate_admin_session(self.mock_super_admin_user.id)
        self.assertFalse(updated_session.is_elevated)
        self.assertIsNone(updated_session.elevation_expires)


    def test_operation_requires_elevation(self):
        """Test operations that require privilege elevation"""

        # Create super admin session (not elevated)
        self.controller.create_admin_session(self.mock_super_admin_ctx)

        # Test operation requiring elevation (should fail)
        allowed, reason = self.controller.check_operation_permission(
            self.mock_super_admin_ctx, AdminOperation.SYSTEM_OVERRIDE, require_elevation=True
        )
        self.assertFalse(allowed)
        self.assertIn("requires privilege elevation", reason)

        # Elevate privileges
        success, _ = self.controller.elevate_privileges(self.mock_super_admin_ctx)
        self.assertTrue(success)

        # Test operation again (should succeed)
        allowed, reason = self.controller.check_operation_permission(
            self.mock_super_admin_ctx, AdminOperation.SYSTEM_OVERRIDE, require_elevation=True
        )
        self.assertTrue(allowed)


    def test_lockout_expiration(self):
        """Test that user lockouts expire after timeout"""

        user_id = self.mock_user.id

        # Lock the user
        for _i in range(3):
            self.controller._record_failed_attempt(user_id, "test_operation")

        # Verify user is locked
        self.assertTrue(self.controller._is_user_locked(user_id))

        # Simulate lockout expiration by backdating the lockout
        self.controller.locked_users[user_id] = datetime.utcnow() - timedelta(hours=1)

        # Check if user is still locked (should be unlocked)
        self.assertFalse(self.controller._is_user_locked(user_id))



if __name__ == "__main__":

    # Run the tests
    unittest.main(verbosity=0, exit=False)

