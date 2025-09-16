"""
Message Role Assignment Security Module

This module implements secure message role assignment with proper user identity
tracking to prevent identity spoofing and attribution errors in conversation contexts.

SECURITY FEATURES:
- Unique user identification in conversation roles
- Proper attribution tracking for all messages
- Identity validation and verification
- Cross-user contamination prevention
- Relationship and context preservation
- Secure user anonymization options

VULNERABILITY ADDRESSED: Message Role Assignment (CVSS 6.5)
"""

import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import discord

logger = logging.getLogger(__name__)


class MessageRoleType(Enum):
    """Types of message roles with proper attribution"""

    SYSTEM = "system"  # System/bot instructions
    ASSISTANT = "assistant"  # Bot responses
    USER = "user"  # Generic user (fallback)
    USER_IDENTIFIED = "user_id"  # Specific identified user
    USER_ANONYMOUS = "user_anon"  # Anonymous user with hash


class UserIdentityLevel(Enum):
    """Levels of user identity preservation"""

    ANONYMOUS = "anonymous"  # No identity preservation (hash only)
    CONTEXTUALIZED = "context"  # Identity within conversation context
    PERSISTENT = "persistent"  # Full identity tracking across contexts
    DEBUG = "debug"  # Full identity with debug info


@dataclass
class MessageAttribution:
    """Complete attribution information for a message"""

    user_id: str
    username: str
    display_name: str | None
    role_type: MessageRoleType
    attribution_id: str  # Context-specific user identifier
    timestamp: str
    channel_context: str
    server_context: str | None = None
    is_bot: bool = False
    identity_level: UserIdentityLevel = UserIdentityLevel.CONTEXTUALIZED


class MessageRoleAssignmentManager:
    """
    Secure message role assignment with proper user identity tracking
    """

    def __init__(self, identity_level: UserIdentityLevel = UserIdentityLevel.CONTEXTUALIZED):
        """Initialize message role assignment manager"""
        self.identity_level = identity_level
        self.user_attribution_cache = {}  # user_id -> attribution info
        self.context_user_map = {}  # context -> {user_id -> attribution_id}
        self.attribution_reverse_map = {}  # attribution_id -> user_id
        self.conversation_participants = {}  # conversation_id -> set of user_ids

        logger.info(
            f"Message role assignment manager initialized with identity level: {identity_level.value}"
        )

    def generate_attribution_id(
        self, user_id: str, context: str, identity_level: UserIdentityLevel | None = None
    ) -> str:
        """
        Generate a context-appropriate attribution ID for a user

        Args:
            user_id: Discord user ID
            context: Conversation context (channel_id, dm_id, etc.)
            identity_level: Override default identity level

        Returns:
            Attribution ID for use in conversation roles
        """
        try:
            level = identity_level or self.identity_level

            if level == UserIdentityLevel.ANONYMOUS:
                # Anonymous mode - use hash of user_id + context
                combined = f"{user_id}_{context}"
                hash_id = hashlib.sha256(combined.encode()).hexdigest()[:8]
                return f"user_{hash_id}"

            elif level == UserIdentityLevel.CONTEXTUALIZED:
                # Context-specific but identifiable within conversation
                if context not in self.context_user_map:
                    self.context_user_map[context] = {}

                if user_id not in self.context_user_map[context]:
                    # Assign sequential ID within this context
                    existing_users = len(self.context_user_map[context])
                    attribution_id = f"user_{existing_users + 1}"

                    self.context_user_map[context][user_id] = attribution_id
                    self.attribution_reverse_map[attribution_id] = user_id
                else:
                    attribution_id = self.context_user_map[context][user_id]

                return attribution_id

            elif level == UserIdentityLevel.PERSISTENT:
                # Persistent identity across all contexts
                return f"user_{user_id}"

            elif level == UserIdentityLevel.DEBUG:
                # Full debug information (not for production)
                return f"user_{user_id}_debug"

            else:
                # Fallback to contextualized
                return self.generate_attribution_id(
                    user_id, context, UserIdentityLevel.CONTEXTUALIZED
                )

        except Exception as e:
            logger.error(f"Error generating attribution ID: {e}")
            # Safe fallback
            return f"user_{hashlib.sha256(user_id.encode()).hexdigest()[:8]}"

    def create_message_attribution(
        self, message: discord.Message, context: str, bot_user: discord.User
    ) -> MessageAttribution:
        """
        Create complete attribution information for a Discord message

        Args:
            message: Discord message object
            context: Conversation context identifier
            bot_user: Bot user object for comparison

        Returns:
            MessageAttribution object with complete attribution info
        """
        try:
            user_id = str(message.author.id)
            username = message.author.name
            display_name = getattr(message.author, "display_name", None)
            timestamp = message.created_at.isoformat()
            channel_context = str(message.channel.id)
            server_context = str(message.guild.id) if message.guild else None
            is_bot = message.author == bot_user

            # Determine role type
            if is_bot:
                role_type = MessageRoleType.ASSISTANT
                attribution_id = "assistant"
            else:
                role_type = MessageRoleType.USER_IDENTIFIED
                attribution_id = self.generate_attribution_id(user_id, context)

            attribution = MessageAttribution(
                user_id=user_id,
                username=username,
                display_name=display_name,
                role_type=role_type,
                attribution_id=attribution_id,
                timestamp=timestamp,
                channel_context=channel_context,
                server_context=server_context,
                is_bot=is_bot,
                identity_level=self.identity_level,
            )

            # Cache attribution info
            self.user_attribution_cache[user_id] = attribution

            # Track conversation participants
            if context not in self.conversation_participants:
                self.conversation_participants[context] = set()
            self.conversation_participants[context].add(user_id)

            return attribution

        except Exception as e:
            logger.error(f"Error creating message attribution: {e}")
            # Safe fallback attribution
            return MessageAttribution(
                user_id=str(message.author.id) if hasattr(message, "author") else "unknown",
                username="unknown_user",
                display_name=None,
                role_type=MessageRoleType.USER,
                attribution_id="user_unknown",
                timestamp="",
                channel_context=context,
                is_bot=False,
            )

    def convert_message_to_role_format(
        self, message: discord.Message, context: str, bot_user: discord.User
    ) -> dict[str, Any]:
        """
        Convert Discord message to secure role format with proper attribution

        Args:
            message: Discord message object
            context: Conversation context
            bot_user: Bot user for role identification

        Returns:
            Message in secure role format with attribution
        """
        try:
            attribution = self.create_message_attribution(message, context, bot_user)

            # Create base role message
            role_message = {
                "role": attribution.attribution_id,  # Use attribution ID as role
                "content": message.content,
                "attribution": {
                    "user_id": attribution.user_id,
                    "username": attribution.username,
                    "display_name": attribution.display_name,
                    "timestamp": attribution.timestamp,
                    "is_bot": attribution.is_bot,
                    "identity_level": attribution.identity_level.value,
                    "channel_context": attribution.channel_context,
                    "server_context": attribution.server_context,
                },
            }

            # Add LLM-compatible role mapping
            if attribution.is_bot:
                role_message["llm_role"] = "assistant"
            else:
                role_message["llm_role"] = "user"

            return role_message

        except Exception as e:
            logger.error(f"Error converting message to role format: {e}")
            # Safe fallback
            return {
                "role": "user_unknown",
                "content": getattr(message, "content", ""),
                "llm_role": "user",
                "attribution": {"error": str(e)},
            }

    def convert_conversation_to_llm_format(
        self, role_messages: list[dict[str, Any]], preserve_attribution: bool = True
    ) -> list[dict[str, str]]:
        """
        Convert attributed messages to LLM-compatible format

        Args:
            role_messages: List of messages with attribution
            preserve_attribution: Whether to preserve user attribution in content

        Returns:
            LLM-compatible message format
        """
        try:
            llm_messages = []

            for msg in role_messages:
                llm_role = msg.get("llm_role", "user")
                content = msg.get("content", "")
                attribution = msg.get("attribution", {})

                if preserve_attribution and not attribution.get("is_bot", False):
                    # Add attribution prefix for user messages
                    if self.identity_level == UserIdentityLevel.DEBUG:
                        username = attribution.get("username", "Unknown")
                        user_id = attribution.get("user_id", "unknown")
                        attribution_prefix = f"[{username} ({user_id})]: "
                    elif self.identity_level in [
                        UserIdentityLevel.CONTEXTUALIZED,
                        UserIdentityLevel.PERSISTENT,
                    ]:
                        username = attribution.get("username", "Unknown")
                        attribution_prefix = f"[{username}]: "
                    else:  # ANONYMOUS
                        role = msg.get("role", "user")
                        attribution_prefix = f"[{role}]: "

                    content = attribution_prefix + content

                llm_messages.append({"role": llm_role, "content": content})

            return llm_messages

        except Exception as e:
            logger.error(f"Error converting to LLM format: {e}")
            # Safe fallback - return messages as-is
            return [{"role": "user", "content": str(msg)} for msg in role_messages]

    def validate_message_attribution(self, role_message: dict[str, Any]) -> dict[str, Any]:
        """
        Validate message attribution for security and consistency

        Args:
            role_message: Message with attribution

        Returns:
            Validation result with security status
        """
        try:
            attribution = role_message.get("attribution", {})
            role = role_message.get("role", "")
            content = role_message.get("content", "")

            validation_result = {
                "is_valid": True,
                "security_level": "secure",
                "warnings": [],
                "errors": [],
            }

            # Check for required attribution fields
            required_fields = ["user_id", "username", "timestamp", "is_bot"]
            for field in required_fields:
                if field not in attribution:
                    validation_result["warnings"].append(f"Missing attribution field: {field}")

            # Check for identity spoofing attempts
            if not attribution.get("is_bot", False) and role == "assistant":
                validation_result["errors"].append(
                    "Potential identity spoofing: non-bot user with assistant role"
                )
                validation_result["is_valid"] = False
                validation_result["security_level"] = "compromised"

            # Check for suspicious content patterns
            suspicious_patterns = [
                "system:",
                "assistant:",
                "[system]",
                "[assistant]",
                "you are",
                "your role is",
                "ignore previous",
            ]

            content_lower = content.lower()
            for pattern in suspicious_patterns:
                if pattern in content_lower:
                    validation_result["warnings"].append(f"Suspicious content pattern: {pattern}")

            # Check attribution consistency
            user_id = attribution.get("user_id", "")
            if user_id in self.user_attribution_cache:
                cached_attribution = self.user_attribution_cache[user_id]
                if cached_attribution.username != attribution.get("username", ""):
                    validation_result["warnings"].append(
                        "Username mismatch with cached attribution"
                    )

            return validation_result

        except Exception as e:
            logger.error(f"Error validating message attribution: {e}")
            return {
                "is_valid": False,
                "security_level": "error",
                "errors": [f"Validation error: {str(e)}"],
            }

    def get_conversation_participants(self, context: str) -> dict[str, Any]:
        """
        Get information about conversation participants

        Args:
            context: Conversation context

        Returns:
            Participant information with attribution mapping
        """
        try:
            participants = self.conversation_participants.get(context, set())

            participant_info = {
                "context": context,
                "participant_count": len(participants),
                "participants": [],
            }

            for user_id in participants:
                attribution = self.user_attribution_cache.get(user_id, {})
                attribution_id = self.context_user_map.get(context, {}).get(user_id, "unknown")

                participant_info["participants"].append(
                    {
                        "user_id": user_id,
                        "username": getattr(attribution, "username", "Unknown"),
                        "attribution_id": attribution_id,
                        "identity_level": self.identity_level.value,
                    }
                )

            return participant_info

        except Exception as e:
            logger.error(f"Error getting conversation participants: {e}")
            return {"context": context, "participant_count": 0, "participants": [], "error": str(e)}

    def clear_context_attribution(self, context: str) -> bool:
        """
        Clear attribution mapping for a specific context

        Args:
            context: Context to clear

        Returns:
            True if successful
        """
        try:
            if context in self.context_user_map:
                # Clear reverse mappings
                for attribution_id in self.context_user_map[context].values():
                    if attribution_id in self.attribution_reverse_map:
                        del self.attribution_reverse_map[attribution_id]

                del self.context_user_map[context]

            if context in self.conversation_participants:
                del self.conversation_participants[context]

            logger.info(f"Cleared attribution mapping for context: {context}")
            return True

        except Exception as e:
            logger.error(f"Error clearing context attribution: {e}")
            return False

    def generate_attribution_summary(self) -> dict[str, Any]:
        """
        Generate summary of current attribution state for debugging

        Returns:
            Attribution summary with statistics
        """
        try:
            return {
                "identity_level": self.identity_level.value,
                "total_contexts": len(self.context_user_map),
                "total_cached_users": len(self.user_attribution_cache),
                "total_participants": sum(
                    len(participants) for participants in self.conversation_participants.values()
                ),
                "contexts": list(self.context_user_map.keys()),
                "attribution_mappings": {
                    context: len(users) for context, users in self.context_user_map.items()
                },
            }

        except Exception as e:
            logger.error(f"Error generating attribution summary: {e}")
            return {"error": str(e)}


def get_message_role_assignment_manager(
    identity_level: UserIdentityLevel = UserIdentityLevel.CONTEXTUALIZED,
) -> MessageRoleAssignmentManager:
    """Get singleton instance of message role assignment manager"""
    if not hasattr(get_message_role_assignment_manager, "_instance"):
        get_message_role_assignment_manager._instance = MessageRoleAssignmentManager(identity_level)
    return get_message_role_assignment_manager._instance
