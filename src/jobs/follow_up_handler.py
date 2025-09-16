"""
Follow-up Handler for Job Scheduler
===================================

Handler for scheduling and executing follow-up messages to users.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FollowUpHandler:
    """Handler for follow-up message jobs"""

    def __init__(self, postgres_pool, bot_client=None, memory_manager=None):
        self.postgres_pool = postgres_pool
        self.bot_client = bot_client
        self.memory_manager = memory_manager

    def set_bot(self, bot_client):
        """Set the bot client for sending messages"""
        self.bot_client = bot_client
        logger.info("Bot client set for FollowUpHandler")

    async def execute(self, payload: dict[str, Any]):
        """Execute a follow-up message job"""
        try:
            user_id = payload.get("user_id")
            channel_id = payload.get("channel_id")
            message = payload.get("message", "Following up on our previous conversation!")
            message_context = payload.get("message_context", {})

            # Try to get channel_id from message_context if not in main payload
            if not channel_id and "channel" in message_context:
                channel_id = str(message_context["channel"])

            if not user_id:
                error_msg = f"Missing required payload data: user_id={user_id}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            if not channel_id:
                error_msg = (
                    f"Missing required payload data: user_id={user_id}, channel_id={channel_id}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Check if user has follow-ups enabled
            if not await self._is_follow_up_enabled(user_id):
                logger.info(f"Follow-ups disabled for user {user_id}, skipping")
                return

            # Send the follow-up message
            if self.bot_client:
                try:
                    channel = self.bot_client.get_channel(int(channel_id))
                    if channel:
                        await channel.send(f"<@{user_id}> {message}")
                        logger.info(
                            f"Sent follow-up message to user {user_id} in channel {channel_id}"
                        )
                    else:
                        error_msg = f"Could not find channel {channel_id} for follow-up"
                        logger.warning(error_msg)
                        raise ValueError(error_msg)
                except Exception as e:
                    logger.error(f"Failed to send follow-up message: {e}")
                    raise
            else:
                error_msg = "No bot client available for sending follow-up messages"
                logger.warning(error_msg)
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"Error executing follow-up job: {e}")
            raise

    async def _is_follow_up_enabled(self, user_id: str) -> bool:
        """Check if user has follow-ups enabled"""
        try:
            async with self.postgres_pool.acquire() as conn:
                result = await conn.fetchval(
                    """
                    SELECT follow_ups_enabled
                    FROM user_profiles
                    WHERE user_id = $1
                """,
                    user_id,
                )

                # Default to True if no preference set
                return result if result is not None else True

        except Exception as e:
            logger.error(f"Error checking follow-up preference for user {user_id}: {e}")
            return True  # Default to enabled on error


async def initialize_follow_up_schema(postgres_pool):
    """Initialize database schema for follow-up system"""
    try:
        async with postgres_pool.acquire() as conn:
            # Check if user_profiles table exists
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'user_profiles'
                )
            """
            )

            if not table_exists:
                # Create user_profiles table if it doesn't exist
                await conn.execute(
                    """
                    CREATE TABLE user_profiles (
                        user_id VARCHAR(50) PRIMARY KEY,
                        follow_ups_enabled BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """
                )
                logger.info("Created user_profiles table")
            else:
                # Table exists, check if follow_ups_enabled column exists
                column_exists = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public'
                        AND table_name = 'user_profiles'
                        AND column_name = 'follow_ups_enabled'
                    )
                """
                )

                if not column_exists:
                    # Add the follow_ups_enabled column
                    await conn.execute(
                        """
                        ALTER TABLE user_profiles
                        ADD COLUMN follow_ups_enabled BOOLEAN DEFAULT TRUE
                    """
                    )
                    logger.info("Added follow_ups_enabled column to existing user_profiles table")

            # Create index for better performance (IF NOT EXISTS handles existing indexes)
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_profiles_follow_ups
                ON user_profiles(user_id, follow_ups_enabled)
            """
            )

            logger.info("✅ Follow-up schema initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize follow-up schema: {e}")
        raise
