"""
Simplified bot-level timestamp tracking for enrichment worker.

Instead of tracking per-user timestamps (86+ markers), we track ONE timestamp per bot.
This timestamp represents "last enrichment run completed at X" for the entire bot.

Benefits:
- Simpler: 1 marker per bot instead of 100s of per-user markers
- Faster: No per-user marker queries needed
- Clearer: "When did enrichment last run?" is obvious
- Still correct: Qdrant filters by timestamp, so no reprocessing
"""
from datetime import datetime, timedelta
from typing import Optional
import asyncpg
import json
import logging

logger = logging.getLogger(__name__)

class BotEnrichmentMarker:
    """Manages bot-level enrichment timestamps."""
    
    def __init__(self, db_pool: asyncpg.Pool, lookback_days: int = 3):
        self.db_pool = db_pool
        self.lookback_days = lookback_days
    
    async def get_last_run_timestamp(self, bot_name: str) -> datetime:
        """
        Get the timestamp of the last enrichment run for this bot.
        
        Returns:
            - Last run timestamp if exists
            - Otherwise: NOW - lookback_days (for initial backfill)
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    ufr.context_metadata->>'last_run_timestamp' as last_run,
                    ufr.updated_at
                FROM user_fact_relationships ufr
                JOIN fact_entities fe ON ufr.entity_id = fe.id
                WHERE fe.entity_type = '_bot_enrichment_marker'
                  AND fe.entity_name = $1
                  AND ufr.relationship_type = '_bot_enrichment_progress'
                LIMIT 1
            """, bot_name)
            
            if row and row['last_run']:
                try:
                    ts = datetime.fromisoformat(row['last_run'])
                    # Ensure timezone-naive
                    if ts.tzinfo is not None:
                        ts = ts.replace(tzinfo=None)
                    
                    # CRITICAL: Enforce maximum lookback - never go back more than lookback_days
                    max_lookback = datetime.utcnow() - timedelta(days=self.lookback_days)
                    if ts < max_lookback:
                        logger.info(
                            f"⏭️  Bot {bot_name} marker is old ({ts.isoformat()}), "
                            f"enforcing {self.lookback_days}-day limit (since {max_lookback.isoformat()})"
                        )
                        return max_lookback
                    
                    logger.debug(f"Last enrichment run for bot {bot_name}: {ts.isoformat()}")
                    return ts
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse timestamp for bot {bot_name}: {e}")
            
            # No marker - initial backfill
            backfill_from = datetime.utcnow() - timedelta(days=self.lookback_days)
            logger.info(f"No enrichment marker for bot {bot_name}, starting from {backfill_from.isoformat()}")
            return backfill_from
    
    async def update_last_run_timestamp(
        self,
        bot_name: str,
        timestamp: datetime
    ):
        """
        Update the last run timestamp for this bot.
        
        This should be called AFTER a successful enrichment cycle completes.
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Ensure timestamp is naive UTC
                ts_to_store = timestamp
                if ts_to_store.tzinfo is not None:
                    ts_to_store = ts_to_store.replace(tzinfo=None)
                
                # Create/update marker entity
                marker_entity_id = await conn.fetchval("""
                    INSERT INTO fact_entities (entity_type, entity_name, category, attributes)
                    VALUES ('_bot_enrichment_marker', $1, '_marker', '{"type": "bot_enrichment"}'::jsonb)
                    ON CONFLICT (entity_type, entity_name)
                    DO UPDATE SET updated_at = NOW()
                    RETURNING id
                """, bot_name)
                
                # Ensure a dummy user exists (FK requirement - we use bot_name as user_id)
                await conn.execute("""
                    INSERT INTO universal_users 
                    (universal_id, primary_username, display_name, created_at, last_active)
                    VALUES ($1, $2, $3, NOW(), NOW())
                    ON CONFLICT (universal_id) DO UPDATE SET last_active = NOW()
                """, f"_bot_{bot_name}", f"bot_{bot_name}", f"Bot {bot_name}")
                
                # Store the timestamp
                context_metadata = {
                    'last_run_timestamp': ts_to_store.isoformat(),
                    'bot_name': bot_name,
                    'marker_type': 'bot_enrichment_progress'
                }
                
                await conn.execute("""
                    INSERT INTO user_fact_relationships 
                    (user_id, entity_id, relationship_type, confidence, context_metadata)
                    VALUES ($1, $2, '_bot_enrichment_progress', 1.0, $3::jsonb)
                    ON CONFLICT (user_id, entity_id, relationship_type)
                    DO UPDATE SET
                        context_metadata = $3::jsonb,
                        updated_at = NOW()
                """, f"_bot_{bot_name}", marker_entity_id, json.dumps(context_metadata))
                
                logger.info(
                    f"✅ Updated bot enrichment marker: {bot_name} -> {ts_to_store.isoformat()}"
                )
