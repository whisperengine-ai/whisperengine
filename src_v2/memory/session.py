from typing import Optional
import uuid
import datetime
from loguru import logger
from src_v2.core.database import db_manager

class SessionManager:
    async def get_active_session(self, user_id: str, character_name: str) -> Optional[str]:
        """
        Returns the ID of the active session for the user/character.
        If no active session exists, returns None.
        """
        if not db_manager.postgres_pool:
            return None

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id FROM v2_conversation_sessions
                    WHERE user_id = $1 AND character_name = $2 AND is_active = TRUE
                """, str(user_id), character_name)
                
                if row:
                    return str(row['id'])
                return None
        except Exception as e:
            logger.error(f"Failed to get active session: {e}")
            return None

    async def create_session(self, user_id: str, character_name: str) -> Optional[str]:
        """
        Creates a new active session.
        """
        if not db_manager.postgres_pool:
            return None

        try:
            session_id = uuid.uuid4()
            async with db_manager.postgres_pool.acquire() as conn:
                # Close any existing active sessions just in case
                await conn.execute("""
                    UPDATE v2_conversation_sessions
                    SET is_active = FALSE, end_time = NOW()
                    WHERE user_id = $1 AND character_name = $2 AND is_active = TRUE
                """, str(user_id), character_name)

                await conn.execute("""
                    INSERT INTO v2_conversation_sessions (id, user_id, character_name)
                    VALUES ($1, $2, $3)
                """, session_id, str(user_id), character_name)
                
            logger.info(f"Created new session {session_id} for user {user_id}")
            return str(session_id)
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    async def close_session(self, session_id: str):
        """
        Closes a session.
        """
        if not db_manager.postgres_pool:
            return

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE v2_conversation_sessions
                    SET is_active = FALSE, end_time = NOW()
                    WHERE id = $1
                """, uuid.UUID(session_id))
            logger.info(f"Closed session {session_id}")
        except Exception as e:
            logger.error(f"Failed to close session: {e}")

session_manager = SessionManager()
