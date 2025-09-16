"""
Admin Access Control Security System
Addresses CVSS 5.4 Administrative Access Control Gaps

This module provides comprehensive admin access control with:
- Multi-level admin authorization
- Session management and timeout
- Admin audit logging
- Operation-level permission checks
- Privilege escalation controls
- Admin activity monitoring
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from discord.ext import commands

# Import secure logging for admin audit trail
try:
    from secure_logging import DataSensitivity, LogLevel, get_secure_logger

    secure_logger = get_secure_logger("admin_access_control")
    HAS_SECURE_LOGGING = True
except ImportError:
    # Fallback to standard logging if secure logging not available
    secure_logger = logging.getLogger("admin_access_control")
    HAS_SECURE_LOGGING = False


def log_admin_action(message: str, user_id: int | None = None, level: str = "INFO"):
    """Helper function to log admin actions with fallback"""
    if HAS_SECURE_LOGGING:
        log_level = getattr(LogLevel, level, LogLevel.INFO)
        secure_logger.log_user_action(
            level=log_level,
            message=message,
            user_id=user_id,
            context="admin_access_control",
            sensitivity=DataSensitivity.SENSITIVE,
        )
    else:
        log_func = getattr(secure_logger, level.lower(), secure_logger.info)
        log_func(f"[Admin] {message} (User: {user_id})")


def log_security_event(
    message: str,
    user_id: int | None = None,
    threat_level: str = "medium",
    event_type: str = "admin_security",
    additional_data: dict | None = None,
):
    """Helper function to log security events with fallback"""
    if HAS_SECURE_LOGGING:
        secure_logger.log_security_event(
            message=message,
            user_id=user_id,
            threat_level=threat_level,
            event_type=event_type,
            additional_data=additional_data,
        )
    else:
        secure_logger.warning(f"[Security] {message} (User: {user_id}, Type: {event_type})")


class AdminLevel(Enum):
    """Admin authorization levels with different permissions"""

    NONE = 0  # No admin privileges
    MODERATOR = 1  # Basic moderation (fact management)
    ADMINISTRATOR = 2  # Full admin (global facts, user management)
    SUPER_ADMIN = 3  # System admin (debug, configuration)
    OWNER = 4  # Bot owner (all permissions)


class AdminOperation(Enum):
    """Types of admin operations with specific permission requirements"""

    # Moderator level operations
    ADD_USER_FACT = "add_user_fact"
    REMOVE_USER_FACT = "remove_user_fact"
    LIST_USER_FACTS = "list_user_facts"
    CLEAR_USER_CACHE = "clear_user_cache"

    # Administrator level operations
    ADD_GLOBAL_FACT = "add_global_fact"
    REMOVE_GLOBAL_FACT = "remove_global_fact"
    LIST_GLOBAL_FACTS = "list_global_facts"
    MANAGE_USERS = "manage_users"
    VIEW_USER_DATA = "view_user_data"

    # Super Admin level operations
    DEBUG_MODE = "debug_mode"
    SYSTEM_CONFIG = "system_config"
    DATABASE_ACCESS = "database_access"
    LOG_ACCESS = "log_access"

    # Owner level operations
    SHUTDOWN_BOT = "shutdown_bot"
    MODIFY_ADMIN_PERMISSIONS = "modify_admin_permissions"
    SYSTEM_OVERRIDE = "system_override"


@dataclass
class AdminSession:
    """Admin session with timeout and activity tracking"""

    user_id: int
    username: str
    admin_level: AdminLevel
    session_start: datetime
    last_activity: datetime
    session_token: str
    operations_performed: list[str] = field(default_factory=list)
    failed_operations: list[str] = field(default_factory=list)
    is_elevated: bool = False
    elevation_expires: datetime | None = None


@dataclass
class AdminAuditEntry:
    """Admin audit log entry for security monitoring"""

    timestamp: datetime
    user_id: int
    username: str
    operation: AdminOperation
    success: bool
    details: str
    session_token: str
    channel_id: int | None = None
    guild_id: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AdminAccessController:
    """
    Comprehensive admin access control system

    Features:
    - Multi-level admin authorization
    - Session management with timeouts
    - Operation-level permission checks
    - Admin audit logging
    - Privilege escalation controls
    - Failed access attempt monitoring
    """

    def __init__(
        self,
        session_timeout_minutes: int = 60,
        elevation_timeout_minutes: int = 15,
        max_failed_attempts: int = 3,
        lockout_duration_minutes: int = 30,
    ):

        # Admin configuration
        self.admin_users: dict[int, AdminLevel] = {}
        self.owner_user_ids: set[int] = set()

        # Session management
        self.active_sessions: dict[int, AdminSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.elevation_timeout = timedelta(minutes=elevation_timeout_minutes)

        # Security controls
        self.failed_attempts: dict[int, list[datetime]] = {}
        self.locked_users: dict[int, datetime] = {}
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = timedelta(minutes=lockout_duration_minutes)

        # Audit logging
        self.audit_log: list[AdminAuditEntry] = []
        self.max_audit_entries = 10000  # Keep last 10k entries in memory

        # Operation permissions mapping
        self.operation_permissions = {
            # Moderator operations
            AdminOperation.ADD_USER_FACT: AdminLevel.MODERATOR,
            AdminOperation.REMOVE_USER_FACT: AdminLevel.MODERATOR,
            AdminOperation.LIST_USER_FACTS: AdminLevel.MODERATOR,
            AdminOperation.CLEAR_USER_CACHE: AdminLevel.MODERATOR,
            # Administrator operations
            AdminOperation.ADD_GLOBAL_FACT: AdminLevel.ADMINISTRATOR,
            AdminOperation.REMOVE_GLOBAL_FACT: AdminLevel.ADMINISTRATOR,
            AdminOperation.LIST_GLOBAL_FACTS: AdminLevel.ADMINISTRATOR,
            AdminOperation.MANAGE_USERS: AdminLevel.ADMINISTRATOR,
            AdminOperation.VIEW_USER_DATA: AdminLevel.ADMINISTRATOR,
            # Super Admin operations
            AdminOperation.DEBUG_MODE: AdminLevel.SUPER_ADMIN,
            AdminOperation.SYSTEM_CONFIG: AdminLevel.SUPER_ADMIN,
            AdminOperation.DATABASE_ACCESS: AdminLevel.SUPER_ADMIN,
            AdminOperation.LOG_ACCESS: AdminLevel.SUPER_ADMIN,
            # Owner operations
            AdminOperation.SHUTDOWN_BOT: AdminLevel.OWNER,
            AdminOperation.MODIFY_ADMIN_PERMISSIONS: AdminLevel.OWNER,
            AdminOperation.SYSTEM_OVERRIDE: AdminLevel.OWNER,
        }

        log_admin_action("Admin Access Controller initialized")

    def load_admin_config(self, admin_config: dict[str, Any]):
        """
        Load admin configuration from environment or config file

        Expected format:
        {
            "admins": {
                "123456789": "administrator",
                "987654321": "super_admin"
            },
            "owners": ["123456789"]
        }
        """
        try:
            # Load admin users
            if "admins" in admin_config:
                for user_id_str, level_str in admin_config["admins"].items():
                    user_id = int(user_id_str)
                    admin_level = AdminLevel[level_str.upper()]
                    self.admin_users[user_id] = admin_level

            # Load owner users
            if "owners" in admin_config:
                for user_id_str in admin_config["owners"]:
                    user_id = int(user_id_str)
                    self.owner_user_ids.add(user_id)
                    self.admin_users[user_id] = AdminLevel.OWNER

            log_admin_action(
                f"Admin configuration loaded: {len(self.admin_users)} admins, {len(self.owner_user_ids)} owners"
            )

        except Exception as e:
            log_admin_action(f"Failed to load admin configuration: {str(e)}", level="ERROR")
            raise

    def _generate_session_token(self, user_id: int) -> str:
        """Generate secure session token"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{user_id}_{timestamp}_{id(self)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _is_user_locked(self, user_id: int) -> bool:
        """Check if user is locked due to failed attempts"""
        if user_id in self.locked_users:
            lockout_time = self.locked_users[user_id]
            if datetime.utcnow() < lockout_time + self.lockout_duration:
                return True
            else:
                # Lockout expired, remove from locked users
                del self.locked_users[user_id]
                if user_id in self.failed_attempts:
                    del self.failed_attempts[user_id]
        return False

    def _record_failed_attempt(self, user_id: int, operation: str):
        """Record failed access attempt and check for lockout"""
        now = datetime.utcnow()

        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = []

        self.failed_attempts[user_id].append(now)

        # Remove attempts older than lockout duration
        cutoff_time = now - self.lockout_duration
        self.failed_attempts[user_id] = [
            attempt_time
            for attempt_time in self.failed_attempts[user_id]
            if attempt_time > cutoff_time
        ]

        # Check if user should be locked
        if len(self.failed_attempts[user_id]) >= self.max_failed_attempts:
            self.locked_users[user_id] = now

            log_security_event(
                f"User locked due to {len(self.failed_attempts[user_id])} failed admin attempts",
                user_id=user_id,
                threat_level="high",
                event_type="admin_lockout",
                additional_data={
                    "operation": operation,
                    "attempt_count": len(self.failed_attempts[user_id]),
                },
            )

    def get_user_admin_level(self, ctx: commands.Context) -> AdminLevel:
        """
        Get user's admin level with enhanced checks

        Args:
            ctx: Discord command context

        Returns:
            AdminLevel: User's admin level
        """
        user_id = ctx.author.id

        # Check if user is locked
        if self._is_user_locked(user_id):
            return AdminLevel.NONE

        # Check configured admin users first
        if user_id in self.admin_users:
            return self.admin_users[user_id]

        # Check Discord guild permissions (fallback)
        if ctx.guild and hasattr(ctx.author, "guild_permissions"):
            try:
                if ctx.author.guild_permissions.administrator:
                    # Guild admin gets Administrator level by default
                    return AdminLevel.ADMINISTRATOR
            except AttributeError:
                # ctx.author might be User instead of Member in DMs
                pass

        return AdminLevel.NONE

    def create_admin_session(self, ctx: commands.Context) -> AdminSession | None:
        """
        Create admin session for user

        Args:
            ctx: Discord command context

        Returns:
            AdminSession or None if not authorized
        """
        user_id = ctx.author.id
        admin_level = self.get_user_admin_level(ctx)

        if admin_level == AdminLevel.NONE:
            self._record_failed_attempt(user_id, "session_creation")
            return None

        # Create session
        session = AdminSession(
            user_id=user_id,
            username=ctx.author.name,
            admin_level=admin_level,
            session_start=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            session_token=self._generate_session_token(user_id),
        )

        self.active_sessions[user_id] = session

        log_admin_action(f"Admin session created for level {admin_level.name}", user_id=user_id)

        return session

    def validate_admin_session(self, user_id: int) -> AdminSession | None:
        """
        Validate and refresh admin session

        Args:
            user_id: User ID to validate

        Returns:
            AdminSession or None if invalid/expired
        """
        if user_id not in self.active_sessions:
            return None

        session = self.active_sessions[user_id]
        now = datetime.utcnow()

        # Check session timeout
        if now - session.last_activity > self.session_timeout:
            del self.active_sessions[user_id]

            log_admin_action("Admin session expired due to timeout", user_id=user_id)

            return None

        # Check elevation timeout
        if session.is_elevated and session.elevation_expires:
            if now > session.elevation_expires:
                session.is_elevated = False
                session.elevation_expires = None

                log_admin_action("Admin privilege elevation expired", user_id=user_id)

        # Update last activity
        session.last_activity = now
        return session

    def check_operation_permission(
        self, ctx: commands.Context, operation: AdminOperation, require_elevation: bool = False
    ) -> tuple[bool, str]:
        """
        Check if user has permission for specific operation

        Args:
            ctx: Discord command context
            operation: Operation to check
            require_elevation: Whether operation requires privilege elevation

        Returns:
            Tuple of (authorized, reason)
        """
        user_id = ctx.author.id

        # Validate session
        session = self.validate_admin_session(user_id)
        if not session:
            # Try to create new session
            session = self.create_admin_session(ctx)
            if not session:
                self._record_failed_attempt(user_id, operation.value)
                return False, "No valid admin session and insufficient permissions"

        # Check if user is locked
        if self._is_user_locked(user_id):
            return False, "User account is temporarily locked due to failed attempts"

        # Check operation permission level
        required_level = self.operation_permissions.get(operation, AdminLevel.OWNER)
        if session.admin_level.value < required_level.value:
            self._record_failed_attempt(user_id, operation.value)
            session.failed_operations.append(operation.value)

            log_security_event(
                f"Insufficient admin level for operation {operation.value}",
                user_id=user_id,
                threat_level="medium",
                event_type="unauthorized_admin_operation",
                additional_data={
                    "required_level": required_level.name,
                    "user_level": session.admin_level.name,
                    "operation": operation.value,
                },
            )

            return (
                False,
                f"Operation requires {required_level.name} level (user has {session.admin_level.name})",
            )

        # Check elevation requirement
        if require_elevation and not session.is_elevated:
            return False, "Operation requires privilege elevation - use !admin_elevate first"

        return True, "Authorized"

    def elevate_privileges(self, ctx: commands.Context) -> tuple[bool, str]:
        """
        Elevate user's privileges for sensitive operations

        Args:
            ctx: Discord command context

        Returns:
            Tuple of (success, message)
        """
        user_id = ctx.author.id
        session = self.validate_admin_session(user_id)

        if not session:
            return False, "No valid admin session"

        if session.admin_level.value < AdminLevel.SUPER_ADMIN.value:
            return False, "Privilege elevation requires Super Admin level or higher"

        # Elevate privileges
        session.is_elevated = True
        session.elevation_expires = datetime.utcnow() + self.elevation_timeout

        log_security_event(
            "Admin privileges elevated for sensitive operations",
            user_id=user_id,
            threat_level="high",
            event_type="admin_privilege_elevation",
            additional_data={
                "admin_level": session.admin_level.name,
                "elevation_duration": self.elevation_timeout.total_seconds(),
            },
        )

        return True, f"Privileges elevated for {self.elevation_timeout.total_seconds()//60} minutes"

    def log_admin_operation(
        self, ctx: commands.Context, operation: AdminOperation, success: bool, details: str = ""
    ):
        """
        Log admin operation for audit trail

        Args:
            ctx: Discord command context
            operation: Operation performed
            success: Whether operation succeeded
            details: Additional details about the operation
        """
        user_id = ctx.author.id
        session = self.active_sessions.get(user_id)

        audit_entry = AdminAuditEntry(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            username=ctx.author.name,
            operation=operation,
            success=success,
            details=details,
            session_token=session.session_token if session else "no_session",
            channel_id=ctx.channel.id if ctx.channel else None,
            guild_id=ctx.guild.id if ctx.guild else None,
        )

        self.audit_log.append(audit_entry)

        # Keep audit log size manageable
        if len(self.audit_log) > self.max_audit_entries:
            self.audit_log = self.audit_log[-self.max_audit_entries :]

        # Update session activity
        if session:
            if success:
                session.operations_performed.append(operation.value)
            else:
                session.failed_operations.append(operation.value)

        # Log to secure logger
        log_admin_action(
            f"Admin operation {operation.value}: {'SUCCESS' if success else 'FAILED'} - {details}",
            user_id=user_id,
            level="INFO" if success else "WARNING",
        )

    def get_admin_status(self, ctx: commands.Context) -> dict[str, Any]:
        """
        Get admin status information for user

        Args:
            ctx: Discord command context

        Returns:
            Dict with admin status information
        """
        user_id = ctx.author.id
        admin_level = self.get_user_admin_level(ctx)
        session = self.active_sessions.get(user_id)

        status = {
            "user_id": user_id,
            "username": ctx.author.name,
            "admin_level": admin_level.name,
            "has_session": session is not None,
            "is_locked": self._is_user_locked(user_id),
            "failed_attempts": len(self.failed_attempts.get(user_id, [])),
        }

        if session:
            status.update(
                {
                    "session_start": session.session_start.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "is_elevated": session.is_elevated,
                    "operations_performed": len(session.operations_performed),
                    "failed_operations": len(session.failed_operations),
                }
            )

            if session.elevation_expires:
                status["elevation_expires"] = session.elevation_expires.isoformat()

        return status

    def get_audit_summary(self, hours: int = 24) -> dict[str, Any]:
        """
        Get audit summary for recent admin activities

        Args:
            hours: Number of hours to look back

        Returns:
            Dict with audit summary
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_entries = [entry for entry in self.audit_log if entry.timestamp > cutoff_time]

        summary = {
            "time_period_hours": hours,
            "total_operations": len(recent_entries),
            "successful_operations": len([e for e in recent_entries if e.success]),
            "failed_operations": len([e for e in recent_entries if not e.success]),
            "unique_users": len({e.user_id for e in recent_entries}),
            "operations_by_type": {},
            "users_by_activity": {},
        }

        # Count operations by type
        for entry in recent_entries:
            op_name = entry.operation.value
            if op_name not in summary["operations_by_type"]:
                summary["operations_by_type"][op_name] = {"success": 0, "failed": 0}

            if entry.success:
                summary["operations_by_type"][op_name]["success"] += 1
            else:
                summary["operations_by_type"][op_name]["failed"] += 1

        # Count users by activity
        for entry in recent_entries:
            username = entry.username
            if username not in summary["users_by_activity"]:
                summary["users_by_activity"][username] = {"success": 0, "failed": 0}

            if entry.success:
                summary["users_by_activity"][username]["success"] += 1
            else:
                summary["users_by_activity"][username]["failed"] += 1

        return summary

    def cleanup_expired_sessions(self):
        """Clean up expired sessions and audit logs"""
        now = datetime.utcnow()
        expired_sessions = []

        for user_id, session in self.active_sessions.items():
            if now - session.last_activity > self.session_timeout:
                expired_sessions.append(user_id)

        for user_id in expired_sessions:
            del self.active_sessions[user_id]
            log_admin_action("Admin session cleaned up (expired)", user_id=user_id)

        # Clean up old failed attempts
        cutoff_time = now - self.lockout_duration * 2  # Keep double lockout duration
        for user_id in list(self.failed_attempts.keys()):
            self.failed_attempts[user_id] = [
                attempt_time
                for attempt_time in self.failed_attempts[user_id]
                if attempt_time > cutoff_time
            ]
            if not self.failed_attempts[user_id]:
                del self.failed_attempts[user_id]

        return len(expired_sessions)


# Global admin controller instance
admin_controller = AdminAccessController()
