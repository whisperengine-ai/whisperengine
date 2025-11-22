from typing import Optional
from datetime import datetime, timedelta, timezone
from loguru import logger
from src_v2.core.database import db_manager

class SessionManager:
    """
    Manages conversation sessions.
    A session is a continuous period of conversation.
    Sessions are closed after a period of inactivity (e.g., 30 minutes).
    """
    
    SESSION_TIMEOUT_MINUTES = 30

    def __init__(self):
        logger.info("SessionManager initialized")

    async def get_active_session(self, user_id: str, character_name: str) -> str:
        """
        Retrieves the active session ID for a user/character pair.
        If the active session is stale (timed out), it closes it and creates a new one.
        If no active session exists, creates a new one.
        
        Returns:
            session_id (str): UUID of the active session.
        """
        if not db_manager.postgres_pool:
            logger.warning("Database not available, cannot manage sessions.")
            return "00000000-0000-0000-0000-000000000000" # Dummy UUID

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                # 1. Find currently active session
                row = await conn.fetchrow("""
                    SELECT id, updated_at 
                    FROM v2_conversation_sessions 
                    WHERE user_id = $1 AND character_name = $2 AND is_active = TRUE
                    ORDER BY start_time DESC
                    LIMIT 1
                """, user_id, character_name)

                if row:
                    session_id = str(row['id'])
                    last_activity = row['updated_at']
                    
                    # Check for timeout
                    # Ensure last_activity is timezone-aware or naive as needed. 
                    # Postgres usually returns timezone-aware if column is timestamptz.
                    now = datetime.now(timezone.utc)
                    
                    if (now - last_activity) > timedelta(minutes=self.SESSION_TIMEOUT_MINUTES):
                        logger.info(f"Session {session_id} timed out. Closing and creating new one.")
                        await self.close_session(session_id)
                        return await self.create_session(user_id, character_name)
                    else:
                        # Update activity timestamp
                        await self.update_session_activity(session_id)
                        return session_id
                else:
                    # No active session, create new
                    return await self.create_session(user_id, character_name)

        except Exception as e:
            logger.error(f"Failed to get active session: {e}")
            return "00000000-0000-0000-0000-000000000000"

    async def create_session(self, user_id: str, character_name: str) -> str:
        """Creates a new active session."""
        if not db_manager.postgres_pool:
            return "00000000-0000-0000-0000-000000000000"

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                # Close any existing active sessions just in case
                await conn.execute("""
                    UPDATE v2_conversation_sessions
                    SET is_active = FALSE, end_time = NOW()
                    WHERE user_id = $1 AND character_name = $2 AND is_active = TRUE
                """, user_id, character_name)

                session_id = await conn.fetchval("""
                    INSERT INTO v2_conversation_sessions (user_id, character_name, is_active)
                    VALUES ($1, $2, TRUE)
                    RETURNING id
                """, user_id, character_name)
                
                logger.info(f"Created new session {session_id} for {user_id} with {character_name}")
                return str(session_id)
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return "00000000-0000-0000-0000-000000000000"

    async def close_session(self, session_id: str):
        """Marks a session as inactive."""
        if not db_manager.postgres_pool:
            return

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE v2_conversation_sessions
                    SET is_active = FALSE, end_time = NOW()
                    WHERE id = $1
                """, session_id)
                logger.debug(f"Closed session {session_id}")
                
                # TODO: Trigger summarization here?
                # For now, we'll let the caller handle triggers or use a background task.
        except Exception as e:
            logger.error(f"Failed to close session: {e}")

    async def update_session_activity(self, session_id: str):
        """Updates the updated_at timestamp of a session."""
        if not db_manager.postgres_pool:
            return

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE v2_conversation_sessions
                    SET updated_at = NOW()
                    WHERE id = $1
                """, session_id)
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")

    async def get_session_start_time(self, session_id: str) -> Optional[datetime]:
        """Retrieves the start time of a session."""
        if not db_manager.postgres_pool:
            return None

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                start_time = await conn.fetchval("""
                    SELECT start_time 
                    FROM v2_conversation_sessions 
                    WHERE id = $1
                """, session_id)
                return start_time
        except Exception as e:
            logger.error(f"Failed to get session start time: {e}")
            return None

# Global instance
session_manager = SessionManager()
