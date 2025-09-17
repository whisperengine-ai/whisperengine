"""
Human-Like Feature Database Persistence Layer

This module provides CRUD operations for human-like conversation features
that were previously stored only in memory, including:
- User conversation preferences
- Per-user conversation modes and interaction history
- Empathetic response effectiveness tracking
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Database availability check
try:
    import asyncpg
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


class HumanLikePersistenceManager:
    """Database persistence manager for human-like conversation features"""
    
    def __init__(self, postgres_pool=None, sqlite_path: str = None):
        """
        Initialize persistence manager
        
        Args:
            postgres_pool: PostgreSQL connection pool (preferred)
            sqlite_path: SQLite database path (fallback)
        """
        self.postgres_pool = postgres_pool
        self.sqlite_path = sqlite_path or "./data/human_like_data.db"
        self.use_postgres = postgres_pool is not None and POSTGRES_AVAILABLE
        self.use_sqlite = not self.use_postgres and SQLITE_AVAILABLE
        
        if not self.use_postgres and not self.use_sqlite:
            logger.warning("No database backend available for human-like persistence")
        
        # Initialize database schema
        asyncio.create_task(self.initialize_schema())
    
    async def initialize_schema(self):
        """Initialize database tables for human-like features"""
        if self.use_postgres:
            await self._initialize_postgres_schema()
        elif self.use_sqlite:
            await self._initialize_sqlite_schema()
    
    async def _initialize_postgres_schema(self):
        """Initialize PostgreSQL schema"""
        try:
            async with self.postgres_pool.acquire() as connection:
                # User conversation preferences table
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS user_conversation_preferences (
                        user_id TEXT PRIMARY KEY,
                        preferences JSONB NOT NULL DEFAULT '{}',
                        personality_type TEXT DEFAULT 'caring_friend',
                        conversation_mode TEXT DEFAULT 'adaptive',
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # User conversation state table
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS user_conversation_state (
                        user_id TEXT PRIMARY KEY,
                        current_mode TEXT DEFAULT 'adaptive',
                        interaction_history JSONB NOT NULL DEFAULT '[]',
                        conversation_context JSONB NOT NULL DEFAULT '{}',
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Empathetic response effectiveness tracking
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS empathetic_response_tracking (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        intervention_type TEXT NOT NULL,
                        response_style TEXT NOT NULL,
                        effectiveness_score REAL NOT NULL,
                        context JSONB DEFAULT '{}',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                await connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_conversation_preferences_user_id 
                    ON user_conversation_preferences(user_id)
                """)
                
                await connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_conversation_state_user_id 
                    ON user_conversation_state(user_id)
                """)
                
                await connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_empathetic_response_tracking_user_id 
                    ON empathetic_response_tracking(user_id)
                """)
                
                logger.info("PostgreSQL schema initialized for human-like persistence")
                
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
    
    async def _initialize_sqlite_schema(self):
        """Initialize SQLite schema"""
        try:
            import aiosqlite
            
            async with aiosqlite.connect(self.sqlite_path) as connection:
                # User conversation preferences table
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS user_conversation_preferences (
                        user_id TEXT PRIMARY KEY,
                        preferences TEXT NOT NULL DEFAULT '{}',
                        personality_type TEXT DEFAULT 'caring_friend',
                        conversation_mode TEXT DEFAULT 'adaptive',
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # User conversation state table
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS user_conversation_state (
                        user_id TEXT PRIMARY KEY,
                        current_mode TEXT DEFAULT 'adaptive',
                        interaction_history TEXT NOT NULL DEFAULT '[]',
                        conversation_context TEXT NOT NULL DEFAULT '{}',
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Empathetic response effectiveness tracking
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS empathetic_response_tracking (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        response_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        intervention_type TEXT NOT NULL,
                        response_style TEXT NOT NULL,
                        effectiveness_score REAL NOT NULL,
                        context_data TEXT DEFAULT '{}',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                await connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_conversation_preferences_user_id 
                    ON user_conversation_preferences(user_id)
                """)
                
                await connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_conversation_state_user_id 
                    ON user_conversation_state(user_id)
                """)
                
                await connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_empathetic_response_tracking_user_id 
                    ON empathetic_response_tracking(user_id)
                """)
                
                await connection.commit()
                logger.info("SQLite schema initialized for human-like persistence")
                
        except Exception as e:
            logger.error(f"Failed to initialize SQLite schema: {e}")
    
    # =====================================================================
    # USER CONVERSATION PREFERENCES CRUD
    # =====================================================================
    
    async def save_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any],
        personality_type: str = "caring_friend",
        conversation_mode: str = "adaptive"
    ) -> bool:
        """
        Save user conversation preferences
        
        Args:
            user_id: User identifier
            preferences: Dictionary of user preferences
            personality_type: Preferred personality type
            conversation_mode: Preferred conversation mode
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_postgres:
                return await self._save_user_preferences_postgres(
                    user_id, preferences, personality_type, conversation_mode
                )
            elif self.use_sqlite:
                return await self._save_user_preferences_sqlite(
                    user_id, preferences, personality_type, conversation_mode
                )
            else:
                logger.warning("No database backend available for saving preferences")
                return False
                
        except Exception as e:
            logger.error(f"Failed to save user preferences for {user_id}: {e}")
            return False
    
    async def _save_user_preferences_postgres(
        self, user_id: str, preferences: Dict[str, Any], 
        personality_type: str, conversation_mode: str
    ) -> bool:
        """Save preferences to PostgreSQL"""
        async with self.postgres_pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO user_conversation_preferences 
                (user_id, preferences, personality_type, conversation_mode, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    preferences = $2,
                    personality_type = $3,
                    conversation_mode = $4,
                    updated_at = $5
            """, user_id, json.dumps(preferences), personality_type, conversation_mode, datetime.now(UTC))
            return True
    
    async def _save_user_preferences_sqlite(
        self, user_id: str, preferences: Dict[str, Any], 
        personality_type: str, conversation_mode: str
    ) -> bool:
        """Save preferences to SQLite"""
        import aiosqlite
        
        async with aiosqlite.connect(self.sqlite_path) as connection:
            await connection.execute("""
                INSERT OR REPLACE INTO user_conversation_preferences 
                (user_id, preferences, personality_type, conversation_mode, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, json.dumps(preferences), personality_type, conversation_mode, datetime.now(UTC).isoformat()))
            await connection.commit()
            return True
    
    async def load_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Load user conversation preferences
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with preferences, or None if not found
        """
        try:
            if self.use_postgres:
                return await self._load_user_preferences_postgres(user_id)
            elif self.use_sqlite:
                return await self._load_user_preferences_sqlite(user_id)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to load user preferences for {user_id}: {e}")
            return None
    
    async def _load_user_preferences_postgres(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load preferences from PostgreSQL"""
        async with self.postgres_pool.acquire() as connection:
            row = await connection.fetchrow("""
                SELECT preferences, personality_type, conversation_mode, updated_at
                FROM user_conversation_preferences 
                WHERE user_id = $1
            """, user_id)
            
            if row:
                return {
                    "preferences": json.loads(row["preferences"]),
                    "personality_type": row["personality_type"],
                    "conversation_mode": row["conversation_mode"],
                    "updated_at": row["updated_at"]
                }
            return None
    
    async def _load_user_preferences_sqlite(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load preferences from SQLite"""
        import aiosqlite
        
        async with aiosqlite.connect(self.sqlite_path) as connection:
            async with connection.execute("""
                SELECT preferences, personality_type, conversation_mode, updated_at
                FROM user_conversation_preferences 
                WHERE user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "preferences": json.loads(row[0]),
                        "personality_type": row[1],
                        "conversation_mode": row[2],
                        "updated_at": row[3]
                    }
                return None
    
    # =====================================================================
    # USER CONVERSATION STATE CRUD
    # =====================================================================
    
    async def save_conversation_state(
        self,
        user_id: str,
        current_mode: str,
        interaction_history: List[str],
        conversation_context: Dict[str, Any]
    ) -> bool:
        """
        Save user conversation state
        
        Args:
            user_id: User identifier
            current_mode: Current conversation mode
            interaction_history: List of recent interaction types
            conversation_context: Additional conversation context
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_postgres:
                return await self._save_conversation_state_postgres(
                    user_id, current_mode, interaction_history, conversation_context
                )
            elif self.use_sqlite:
                return await self._save_conversation_state_sqlite(
                    user_id, current_mode, interaction_history, conversation_context
                )
            else:
                logger.warning("No database backend available for saving conversation state")
                return False
                
        except Exception as e:
            logger.error(f"Failed to save conversation state for {user_id}: {e}")
            return False
    
    async def _save_conversation_state_postgres(
        self, user_id: str, current_mode: str, 
        interaction_history: List[str], conversation_context: Dict[str, Any]
    ) -> bool:
        """Save conversation state to PostgreSQL"""
        async with self.postgres_pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO user_conversation_state 
                (user_id, current_mode, interaction_history, conversation_context, updated_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    current_mode = $2,
                    interaction_history = $3,
                    conversation_context = $4,
                    updated_at = $5
            """, user_id, current_mode, json.dumps(interaction_history), 
            json.dumps(conversation_context), datetime.now(UTC))
            return True
    
    async def _save_conversation_state_sqlite(
        self, user_id: str, current_mode: str, 
        interaction_history: List[str], conversation_context: Dict[str, Any]
    ) -> bool:
        """Save conversation state to SQLite"""
        import aiosqlite
        
        async with aiosqlite.connect(self.sqlite_path) as connection:
            await connection.execute("""
                INSERT OR REPLACE INTO user_conversation_state 
                (user_id, current_mode, interaction_history, conversation_context, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, current_mode, json.dumps(interaction_history), 
            json.dumps(conversation_context), datetime.now(UTC).isoformat()))
            await connection.commit()
            return True
    
    async def load_conversation_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Load user conversation state
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with conversation state, or None if not found
        """
        try:
            if self.use_postgres:
                return await self._load_conversation_state_postgres(user_id)
            elif self.use_sqlite:
                return await self._load_conversation_state_sqlite(user_id)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to load conversation state for {user_id}: {e}")
            return None
    
    async def _load_conversation_state_postgres(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state from PostgreSQL"""
        async with self.postgres_pool.acquire() as connection:
            row = await connection.fetchrow("""
                SELECT current_mode, interaction_history, conversation_context, updated_at
                FROM user_conversation_state 
                WHERE user_id = $1
            """, user_id)
            
            if row:
                return {
                    "current_mode": row["current_mode"],
                    "interaction_history": json.loads(row["interaction_history"]),
                    "conversation_context": json.loads(row["conversation_context"]),
                    "updated_at": row["updated_at"]
                }
            return None
    
    async def _load_conversation_state_sqlite(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state from SQLite"""
        import aiosqlite
        
        async with aiosqlite.connect(self.sqlite_path) as connection:
            async with connection.execute("""
                SELECT current_mode, interaction_history, conversation_context, updated_at
                FROM user_conversation_state 
                WHERE user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "current_mode": row[0],
                        "interaction_history": json.loads(row[1]),
                        "conversation_context": json.loads(row[2]),
                        "updated_at": row[3]
                    }
                return None
    
    # =====================================================================
    # EMPATHETIC RESPONSE EFFECTIVENESS CRUD
    # =====================================================================
    
    async def track_empathetic_response(
        self,
        user_id: str,
        intervention_type: str,
        response_style: str,
        effectiveness_score: float,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Track empathetic response and return response ID for later effectiveness updates
        
        Args:
            user_id: User identifier
            intervention_type: Type of intervention used
            response_style: Style of response
            effectiveness_score: Initial effectiveness score (0.0-1.0)
            context: Additional context information
            
        Returns:
            Response ID for tracking, empty string if failed
        """
        try:
            context = context or {}
            current_time = datetime.now(UTC)
            
            # Generate a unique response ID
            import uuid
            response_id = str(uuid.uuid4())
            
            if self.use_postgres:
                async with self.postgres_pool.acquire() as connection:
                    await connection.execute("""
                        INSERT INTO empathetic_response_tracking 
                        (id, user_id, response_date, intervention_type, response_style, effectiveness_score, context_data)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, response_id, user_id, current_time, intervention_type, response_style, effectiveness_score, json.dumps(context))
            elif self.use_sqlite:
                import aiosqlite
                async with aiosqlite.connect(self.sqlite_path) as conn:
                    await conn.execute("""
                        INSERT INTO empathetic_response_tracking 
                        (id, user_id, response_date, intervention_type, response_style, effectiveness_score, context_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (response_id, user_id, current_time.isoformat(), intervention_type, response_style, effectiveness_score, json.dumps(context)))
                    await conn.commit()
            else:
                logger.warning("No database backend available for tracking empathetic response")
                return ""
                
            logger.debug("Tracked empathetic response %s for user %s", response_id, user_id)
            return response_id
            
        except Exception as e:
            logger.error("Failed to track empathetic response: %s", e)
            return ""
    
    async def update_response_effectiveness(
        self,
        response_id: str,
        user_follow_up: str,
        effectiveness_score: float
    ) -> bool:
        """
        Update the effectiveness of a previously tracked empathetic response
        
        Args:
            response_id: Response tracking ID from track_empathetic_response
            user_follow_up: User's follow-up message after the empathetic response
            effectiveness_score: Updated effectiveness score (0.0-1.0)
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            if self.use_postgres:
                async with self.postgres_pool.acquire() as connection:
                    result = await connection.execute("""
                        UPDATE empathetic_response_tracking 
                        SET effectiveness_score = $1, context_data = jsonb_set(
                            COALESCE(context_data, '{}'),
                            '{user_follow_up}',
                            $2
                        )
                        WHERE id = $3
                    """, effectiveness_score, json.dumps(user_follow_up), response_id)
                    
                    return result == "UPDATE 1"
            elif self.use_sqlite:
                import aiosqlite
                async with aiosqlite.connect(self.sqlite_path) as conn:
                    # For SQLite, we need to get current context and update it
                    cursor = await conn.execute("""
                        SELECT context_data FROM empathetic_response_tracking WHERE id = ?
                    """, (response_id,))
                    
                    row = await cursor.fetchone()
                    if not row:
                        return False
                    
                    # Update context with follow-up
                    try:
                        context = json.loads(row[0]) if row[0] else {}
                    except json.JSONDecodeError:
                        context = {}
                    
                    context['user_follow_up'] = user_follow_up
                    
                    await conn.execute("""
                        UPDATE empathetic_response_tracking 
                        SET effectiveness_score = ?, context_data = ?
                        WHERE id = ?
                    """, (effectiveness_score, json.dumps(context), response_id))
                    
                    await conn.commit()
                    return True
            else:
                logger.warning("No database backend available for updating response effectiveness")
                return False
                    
        except Exception as e:
            logger.error("Failed to update response effectiveness: %s", e)
            return False
    
    async def get_effective_response_patterns(
        self,
        user_id: str,
        response_type: Optional[str] = None,
        min_effectiveness: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Get patterns of effective empathetic responses for this user
        
        Args:
            user_id: User identifier
            response_type: Optional filter by response type
            min_effectiveness: Minimum effectiveness threshold
            
        Returns:
            List of effective response patterns
        """
        try:
            if self.use_postgres:
                async with self.postgres_pool.acquire() as connection:
                    if response_type:
                        cursor = await connection.execute("""
                            SELECT intervention_type, response_style, effectiveness_score, context_data
                            FROM empathetic_response_tracking 
                            WHERE user_id = $1 AND intervention_type = $2 AND effectiveness_score >= $3
                            ORDER BY effectiveness_score DESC, response_date DESC
                            LIMIT 10
                        """, user_id, response_type, min_effectiveness)
                    else:
                        cursor = await connection.execute("""
                            SELECT intervention_type, response_style, effectiveness_score, context_data
                            FROM empathetic_response_tracking 
                            WHERE user_id = $1 AND effectiveness_score >= $2
                            ORDER BY effectiveness_score DESC, response_date DESC
                            LIMIT 20
                        """, user_id, min_effectiveness)
                    
                    rows = await cursor.fetchall()
            elif self.use_sqlite:
                import aiosqlite
                async with aiosqlite.connect(self.sqlite_path) as conn:
                    if response_type:
                        cursor = await conn.execute("""
                            SELECT intervention_type, response_style, effectiveness_score, context_data
                            FROM empathetic_response_tracking 
                            WHERE user_id = ? AND intervention_type = ? AND effectiveness_score >= ?
                            ORDER BY effectiveness_score DESC, response_date DESC
                            LIMIT 10
                        """, (user_id, response_type, min_effectiveness))
                    else:
                        cursor = await conn.execute("""
                            SELECT intervention_type, response_style, effectiveness_score, context_data
                            FROM empathetic_response_tracking 
                            WHERE user_id = ? AND effectiveness_score >= ?
                            ORDER BY effectiveness_score DESC, response_date DESC
                            LIMIT 20
                        """, (user_id, min_effectiveness))
                    
                    rows = await cursor.fetchall()
            else:
                logger.warning("No database backend available for getting response patterns")
                return []
            
            patterns = []
            for row in rows:
                try:
                    context = json.loads(row[3]) if row[3] else {}
                except json.JSONDecodeError:
                    context = {}
                
                patterns.append({
                    'intervention_type': row[0],
                    'response_style': row[1],
                    'effectiveness_score': row[2],
                    'context': context
                })
            
            return patterns
                
        except Exception as e:
            logger.error("Failed to get effective response patterns: %s", e)
            return []
            
            if self.use_postgres:
                return await self._track_empathetic_response_postgres(
                    user_id, intervention_type, response_style, effectiveness_score, context
                )
            elif self.use_sqlite:
                return await self._track_empathetic_response_sqlite(
                    user_id, intervention_type, response_style, effectiveness_score, context
                )
            else:
                logger.warning("No database backend available for tracking empathetic responses")
                return False
                
        except Exception as e:
            logger.error(f"Failed to track empathetic response for {user_id}: {e}")
            return False
    
    async def _track_empathetic_response_postgres(
        self, user_id: str, intervention_type: str, response_style: str,
        effectiveness_score: float, context: Dict[str, Any]
    ) -> bool:
        """Track empathetic response in PostgreSQL"""
        async with self.postgres_pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO empathetic_response_tracking 
                (user_id, intervention_type, response_style, effectiveness_score, context)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, intervention_type, response_style, effectiveness_score, json.dumps(context))
            return True
    
    async def _track_empathetic_response_sqlite(
        self, user_id: str, intervention_type: str, response_style: str,
        effectiveness_score: float, context: Dict[str, Any]
    ) -> bool:
        """Track empathetic response in SQLite"""
        import aiosqlite
        
        async with aiosqlite.connect(self.sqlite_path) as connection:
            await connection.execute("""
                INSERT INTO empathetic_response_tracking 
                (user_id, intervention_type, response_style, effectiveness_score, context)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, intervention_type, response_style, effectiveness_score, json.dumps(context)))
            await connection.commit()
            return True
    
    async def get_effective_response_strategies(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get most effective response strategies for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of effective strategies sorted by effectiveness
        """
        try:
            if self.use_postgres:
                return await self._get_effective_strategies_postgres(user_id)
            elif self.use_sqlite:
                return await self._get_effective_strategies_sqlite(user_id)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to get effective strategies for {user_id}: {e}")
            return []
    
    async def _get_effective_strategies_postgres(self, user_id: str) -> List[Dict[str, Any]]:
        """Get effective strategies from PostgreSQL"""
        async with self.postgres_pool.acquire() as connection:
            rows = await connection.fetch("""
                SELECT intervention_type, response_style, 
                       AVG(effectiveness_score) as avg_effectiveness,
                       COUNT(*) as usage_count
                FROM empathetic_response_tracking 
                WHERE user_id = $1 
                GROUP BY intervention_type, response_style
                HAVING AVG(effectiveness_score) > 0.6
                ORDER BY avg_effectiveness DESC, usage_count DESC
                LIMIT 10
            """, user_id)
            
            return [
                {
                    "intervention_type": row["intervention_type"],
                    "response_style": row["response_style"],
                    "avg_effectiveness": float(row["avg_effectiveness"]),
                    "usage_count": row["usage_count"]
                }
                for row in rows
            ]
    
    async def _get_effective_strategies_sqlite(self, user_id: str) -> List[Dict[str, Any]]:
        """Get effective strategies from SQLite"""
        import aiosqlite
        
        async with aiosqlite.connect(self.sqlite_path) as connection:
            async with connection.execute("""
                SELECT intervention_type, response_style, 
                       AVG(effectiveness_score) as avg_effectiveness,
                       COUNT(*) as usage_count
                FROM empathetic_response_tracking 
                WHERE user_id = ? 
                GROUP BY intervention_type, response_style
                HAVING AVG(effectiveness_score) > 0.6
                ORDER BY avg_effectiveness DESC, usage_count DESC
                LIMIT 10
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                
                return [
                    {
                        "intervention_type": row[0],
                        "response_style": row[1],
                        "avg_effectiveness": float(row[2]),
                        "usage_count": row[3]
                    }
                    for row in rows
                ]
    
    # =====================================================================
    # UTILITY METHODS
    # =====================================================================
    
    async def delete_user_data(self, user_id: str) -> bool:
        """
        Delete all human-like data for a user (GDPR compliance)
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_postgres:
                return await self._delete_user_data_postgres(user_id)
            elif self.use_sqlite:
                return await self._delete_user_data_sqlite(user_id)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete user data for {user_id}: {e}")
            return False
    
    async def _delete_user_data_postgres(self, user_id: str) -> bool:
        """Delete user data from PostgreSQL"""
        async with self.postgres_pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute("DELETE FROM user_conversation_preferences WHERE user_id = $1", user_id)
                await connection.execute("DELETE FROM user_conversation_state WHERE user_id = $1", user_id)
                await connection.execute("DELETE FROM empathetic_response_tracking WHERE user_id = $1", user_id)
            return True
    
    async def _delete_user_data_sqlite(self, user_id: str) -> bool:
        """Delete user data from SQLite"""
        import aiosqlite
        
        async with aiosqlite.connect(self.sqlite_path) as connection:
            await connection.execute("DELETE FROM user_conversation_preferences WHERE user_id = ?", (user_id,))
            await connection.execute("DELETE FROM user_conversation_state WHERE user_id = ?", (user_id,))
            await connection.execute("DELETE FROM empathetic_response_tracking WHERE user_id = ?", (user_id,))
            await connection.commit()
            return True
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a user's human-like interactions
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with user statistics
        """
        try:
            preferences = await self.load_user_preferences(user_id)
            state = await self.load_conversation_state(user_id)
            strategies = await self.get_effective_response_strategies(user_id)
            
            return {
                "has_preferences": preferences is not None,
                "has_conversation_state": state is not None,
                "effective_strategies_count": len(strategies),
                "preferences": preferences,
                "state": state,
                "top_strategies": strategies[:3] if strategies else []
            }
            
        except Exception as e:
            logger.error(f"Failed to get user statistics for {user_id}: {e}")
            return {}


# Singleton instance for global access
_persistence_manager: Optional[HumanLikePersistenceManager] = None

def get_persistence_manager() -> Optional[HumanLikePersistenceManager]:
    """Get the global persistence manager instance"""
    return _persistence_manager

def initialize_persistence_manager(postgres_pool=None, sqlite_path: str = None) -> HumanLikePersistenceManager:
    """Initialize the global persistence manager"""
    global _persistence_manager
    _persistence_manager = HumanLikePersistenceManager(postgres_pool, sqlite_path)
    return _persistence_manager