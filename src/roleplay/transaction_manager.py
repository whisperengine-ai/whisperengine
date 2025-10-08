"""
Roleplay Transaction Manager

Lightweight PostgreSQL-based state tracking for transactional roleplay interactions.
Used for stateful scenarios like drink orders, purchases, quests, services, etc.

Design Philosophy:
- Simple table structure (8 columns)
- LLM-friendly (inject state as context, AI responds naturally)
- Character-agnostic (works for any bot via bot_name)
- Persistent (survives container restarts)
- Optional (only bots that need it use it)

Example Use Cases:
- Dotty the bartender: Drink orders with payment tracking
- Shop NPCs: Item purchases and inventory
- Quest givers: Multi-step quest progression
- Service bots: Appointment scheduling, reservations

Integration Pattern:
1. Check for pending transactions before building prompt
2. Inject transaction context into system prompt
3. LLM responds naturally with character personality
4. Detect state changes via semantic patterns or LLM classification
5. Update transaction state in database
"""

import asyncio
import asyncpg
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class TransactionState(Enum):
    """Transaction state enumeration"""
    PENDING = "pending"
    AWAITING_PAYMENT = "awaiting_payment"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class RoleplayTransaction:
    """Roleplay transaction data model"""
    id: Optional[int]
    user_id: str
    bot_name: str
    transaction_type: str
    state: str
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bot_name": self.bot_name,
            "transaction_type": self.transaction_type,
            "state": self.state,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def to_context_string(self) -> str:
        """Convert to human-readable context for LLM prompt injection"""
        context_items = []
        for key, value in self.context.items():
            if isinstance(value, (str, int, float)):
                context_items.append(f"{key}: {value}")
        
        duration = (datetime.now() - self.created_at).total_seconds() / 60
        
        return (
            f"PENDING TRANSACTION: {self.transaction_type} (ID: {self.id})\n"
            f"State: {self.state}\n"
            f"Details: {', '.join(context_items)}\n"
            f"Started: {duration:.1f} minutes ago"
        )


class TransactionManager:
    """
    Manages roleplay transaction state in PostgreSQL
    
    Provides lightweight state tracking for transactional roleplay interactions.
    LLM-friendly design: inject transaction context into prompts, let AI respond naturally.
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        """
        Initialize transaction manager
        
        Args:
            db_pool: PostgreSQL connection pool (optional - creates if not provided)
        """
        self.db_pool = db_pool
        self._initialized = False
    
    async def initialize(self):
        """Initialize PostgreSQL connection pool using centralized manager"""
        if not self.db_pool:
            try:
                # Try to use centralized pool manager first
                from src.database.postgres_pool_manager import get_postgres_pool
                self.db_pool = await get_postgres_pool()
                
                if self.db_pool:
                    logger.info("✅ TransactionManager using centralized PostgreSQL pool")
                    self._initialized = True
                else:
                    logger.error("❌ TransactionManager: No centralized PostgreSQL pool available")
                    self._initialized = False
                    
            except Exception as e:
                logger.error("❌ Failed to get centralized PostgreSQL pool for TransactionManager: %s", str(e))
                self._initialized = False
        else:
            self._initialized = True
    
    async def close(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("✅ TransactionManager closed")
    
    async def check_pending_transaction(
        self,
        user_id: str,
        bot_name: str,
        transaction_type: Optional[str] = None
    ) -> Optional[RoleplayTransaction]:
        """
        Check if user has any pending transactions with bot
        
        Args:
            user_id: Discord user ID
            bot_name: Bot name (e.g., 'dotty', 'shop_npc')
            transaction_type: Optional filter by transaction type
            
        Returns:
            RoleplayTransaction if found, None otherwise
        """
        if not self._initialized or not self.db_pool:
            logger.warning("TransactionManager not initialized")
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                # Query for active (non-completed) transactions
                if transaction_type:
                    query = """
                        SELECT * FROM roleplay_transactions
                        WHERE user_id = $1 AND bot_name = $2 AND transaction_type = $3
                        AND state NOT IN ('completed', 'cancelled', 'expired')
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    row = await conn.fetchrow(query, user_id, bot_name, transaction_type)
                else:
                    query = """
                        SELECT * FROM roleplay_transactions
                        WHERE user_id = $1 AND bot_name = $2
                        AND state NOT IN ('completed', 'cancelled', 'expired')
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    row = await conn.fetchrow(query, user_id, bot_name)
                
                if row:
                    # Parse JSONB context (asyncpg may return as string or dict)
                    context = row['context']
                    if isinstance(context, str):
                        context = json.loads(context)
                    elif context is None:
                        context = {}
                    
                    return RoleplayTransaction(
                        id=row['id'],
                        user_id=row['user_id'],
                        bot_name=row['bot_name'],
                        transaction_type=row['transaction_type'],
                        state=row['state'],
                        context=context,
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        completed_at=row['completed_at']
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Error checking pending transaction: {e}")
            return None
    
    async def create_transaction(
        self,
        user_id: str,
        bot_name: str,
        transaction_type: str,
        context: Dict[str, Any],
        state: str = "pending"
    ) -> Optional[int]:
        """
        Create a new transaction
        
        Args:
            user_id: Discord user ID
            bot_name: Bot name
            transaction_type: Type of transaction (e.g., 'drink_order')
            context: Transaction-specific data (JSONB)
            state: Initial state (default: 'pending')
            
        Returns:
            Transaction ID if created, None on failure
        """
        if not self._initialized or not self.db_pool:
            logger.warning("TransactionManager not initialized")
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    INSERT INTO roleplay_transactions
                    (user_id, bot_name, transaction_type, state, context)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                """
                transaction_id = await conn.fetchval(
                    query, user_id, bot_name, transaction_type, state, json.dumps(context)
                )
                
                logger.info(f"✅ Created transaction {transaction_id} for {bot_name}/{user_id}: {transaction_type}")
                return transaction_id
                
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return None
    
    async def update_transaction_state(
        self,
        transaction_id: int,
        new_state: str,
        context_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update transaction state and optionally merge context updates
        
        Args:
            transaction_id: Transaction ID
            new_state: New state value
            context_updates: Optional context fields to merge/update
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self._initialized or not self.db_pool:
            logger.warning("TransactionManager not initialized")
            return False
        
        try:
            async with self.db_pool.acquire() as conn:
                if context_updates:
                    # Merge context updates with existing context
                    query = """
                        UPDATE roleplay_transactions
                        SET state = $1,
                            context = context || $2::jsonb,
                            updated_at = NOW()
                        WHERE id = $3
                    """
                    await conn.execute(query, new_state, json.dumps(context_updates), transaction_id)
                else:
                    query = """
                        UPDATE roleplay_transactions
                        SET state = $1, updated_at = NOW()
                        WHERE id = $2
                    """
                    await conn.execute(query, new_state, transaction_id)
                
                logger.info(f"✅ Updated transaction {transaction_id} to state: {new_state}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating transaction: {e}")
            return False
    
    async def complete_transaction(
        self,
        transaction_id: int,
        final_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Mark transaction as completed
        
        Args:
            transaction_id: Transaction ID
            final_context: Optional final context updates
            
        Returns:
            True if completed successfully, False otherwise
        """
        if not self._initialized or not self.db_pool:
            logger.warning("TransactionManager not initialized")
            return False
        
        try:
            async with self.db_pool.acquire() as conn:
                if final_context:
                    query = """
                        UPDATE roleplay_transactions
                        SET state = 'completed',
                            context = context || $1::jsonb,
                            completed_at = NOW(),
                            updated_at = NOW()
                        WHERE id = $2
                    """
                    await conn.execute(query, json.dumps(final_context), transaction_id)
                else:
                    query = """
                        UPDATE roleplay_transactions
                        SET state = 'completed',
                            completed_at = NOW(),
                            updated_at = NOW()
                        WHERE id = $1
                    """
                    await conn.execute(query, transaction_id)
                
                logger.info(f"✅ Completed transaction {transaction_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error completing transaction: {e}")
            return False
    
    async def cancel_transaction(self, transaction_id: int, reason: Optional[str] = None) -> bool:
        """Cancel a transaction"""
        context_update = {"cancellation_reason": reason} if reason else None
        return await self.update_transaction_state(transaction_id, "cancelled", context_update)
    
    async def get_transaction_history(
        self,
        user_id: str,
        bot_name: str,
        limit: int = 10
    ) -> List[RoleplayTransaction]:
        """
        Get transaction history for user with bot
        
        Args:
            user_id: Discord user ID
            bot_name: Bot name
            limit: Maximum transactions to return
            
        Returns:
            List of transactions ordered by created_at DESC
        """
        if not self._initialized or not self.db_pool:
            return []
        
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT * FROM roleplay_transactions
                    WHERE user_id = $1 AND bot_name = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                """
                rows = await conn.fetch(query, user_id, bot_name, limit)
                
                transactions = []
                for row in rows:
                    # Parse JSONB context (asyncpg may return as string or dict)
                    context = row['context']
                    if isinstance(context, str):
                        context = json.loads(context)
                    elif context is None:
                        context = {}
                    
                    transactions.append(RoleplayTransaction(
                        id=row['id'],
                        user_id=row['user_id'],
                        bot_name=row['bot_name'],
                        transaction_type=row['transaction_type'],
                        state=row['state'],
                        context=context,
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        completed_at=row['completed_at']
                    ))
                
                return transactions
                
        except Exception as e:
            logger.error(f"Error fetching transaction history: {e}")
            return []


# Factory function
def create_transaction_manager(db_pool: Optional[asyncpg.Pool] = None) -> TransactionManager:
    """Create transaction manager instance"""
    return TransactionManager(db_pool=db_pool)
