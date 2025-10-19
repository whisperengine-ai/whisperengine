"""
WhisperEngine Background Enrichment Worker

Periodically scans Qdrant vector storage and generates:
1. Conversation summaries (time-windowed)
2. Future: Enhanced fact extraction, relationship mapping, etc.

Runs independently from Discord bots - zero impact on real-time performance.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
import asyncpg

from src.enrichment.config import config
from src.enrichment.summarization_engine import SummarizationEngine
from src.llm.llm_protocol import create_llm_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/enrichment/worker.log')
    ]
)
logger = logging.getLogger(__name__)


class EnrichmentWorker:
    """
    Background worker for async conversation enrichment
    
    Key Design Principles:
    - Non-blocking: Never impacts real-time bot performance
    - Incremental: Processes messages that haven't been enriched yet
    - Idempotent: Safe to re-run on same data
    - Resilient: Graceful failure handling
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        """Initialize enrichment worker"""
        self.db_pool = postgres_pool
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT
        )
        
        # Initialize LLM client for high-quality summarization
        self.llm_client = create_llm_client(llm_client_type="openrouter")
        
        # Initialize summarization engine
        self.summarizer = SummarizationEngine(
            llm_client=self.llm_client,
            llm_model=config.LLM_MODEL
        )
        
        logger.info("EnrichmentWorker initialized - Qdrant: %s:%s, Model: %s",
                   config.QDRANT_HOST, config.QDRANT_PORT, config.LLM_MODEL)
    
    async def run(self):
        """Main worker loop - runs forever in container"""
        logger.info("🚀 Enrichment worker started - interval: %s seconds",
                   config.ENRICHMENT_INTERVAL_SECONDS)
        
        while True:
            try:
                await self._enrichment_cycle()
            except Exception as e:
                logger.error("❌ Enrichment cycle failed: %s", e, exc_info=True)
            
            # Wait for next cycle
            logger.debug("⏳ Sleeping for %s seconds...", config.ENRICHMENT_INTERVAL_SECONDS)
            await asyncio.sleep(config.ENRICHMENT_INTERVAL_SECONDS)
    
    async def _enrichment_cycle(self):
        """Single enrichment processing cycle"""
        logger.info("📊 Starting enrichment cycle...")
        cycle_start = datetime.utcnow()
        
        # Get all bot collections from Qdrant
        collections = self._get_bot_collections()
        logger.info("Found %s bot collections to process", len(collections))
        
        total_summaries_created = 0
        
        for collection_name in collections:
            bot_name = self._extract_bot_name(collection_name)
            
            try:
                # Process conversation summaries for this bot
                summaries_created = await self._process_conversation_summaries(
                    collection_name=collection_name,
                    bot_name=bot_name
                )
                
                total_summaries_created += summaries_created
            except Exception as e:
                logger.error("Error processing collection %s: %s", collection_name, e)
                continue
        
        cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
        logger.info("✅ Enrichment cycle complete - %s summaries created in %.2fs",
                   total_summaries_created, cycle_duration)
    
    async def _process_conversation_summaries(
        self,
        collection_name: str,
        bot_name: str
    ) -> int:
        """Process conversation summaries for a bot collection"""
        logger.info("📝 Processing summaries for %s...", bot_name)
        
        # Get users with conversations in this collection
        users = await self._get_users_in_collection(collection_name)
        logger.debug("Found %s users with conversations", len(users))
        
        summaries_created = 0
        
        for user_id in users:
            try:
                # Check what time ranges already have summaries
                existing_summaries = await self._get_existing_summary_ranges(
                    user_id=user_id,
                    bot_name=bot_name
                )
                
                # Find conversation time windows that need summarization
                time_windows = await self._find_unsummarized_windows(
                    collection_name=collection_name,
                    user_id=user_id,
                    existing_summaries=existing_summaries
                )
                
                if not time_windows:
                    logger.debug("No new time windows to summarize for user %s", user_id)
                    continue
                
                logger.info("Found %s unsummarized windows for user %s", 
                           len(time_windows), user_id)
                
                # Process each time window
                for window in time_windows:
                    summary_created = await self._create_summary_for_window(
                        collection_name=collection_name,
                        user_id=user_id,
                        bot_name=bot_name,
                        window=window
                    )
                    
                    if summary_created:
                        summaries_created += 1
                        
            except Exception as e:
                logger.error("Error processing summaries for user %s: %s", user_id, e)
                continue
        
        logger.info("✅ Created %s summaries for %s", summaries_created, bot_name)
        return summaries_created
    
    async def _create_summary_for_window(
        self,
        collection_name: str,
        user_id: str,
        bot_name: str,
        window: Dict
    ) -> bool:
        """Create a conversation summary for a specific time window"""
        start_time = window['start_time']
        end_time = window['end_time']
        
        logger.debug("Creating summary for %s from %s to %s",
                    user_id, start_time, end_time)
        
        # Retrieve all messages in this time window
        messages = await self._get_messages_in_window(
            collection_name=collection_name,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time
        )
        
        if len(messages) < config.MIN_MESSAGES_FOR_SUMMARY:
            logger.debug("Skipping window - only %s messages (min: %s)",
                        len(messages), config.MIN_MESSAGES_FOR_SUMMARY)
            return False
        
        # Generate high-quality summary using LLM
        try:
            summary_result = await self.summarizer.generate_conversation_summary(
                messages=messages,
                user_id=user_id,
                bot_name=bot_name
            )
        except Exception as e:
            logger.error("Failed to generate summary: %s", e)
            return False
        
        # Store summary in PostgreSQL
        await self._store_conversation_summary(
            user_id=user_id,
            bot_name=bot_name,
            summary_text=summary_result['summary_text'],
            start_timestamp=start_time,
            end_timestamp=end_time,
            message_count=len(messages),
            key_topics=summary_result.get('key_topics', []),
            emotional_tone=summary_result.get('emotional_tone', 'neutral'),
            compression_ratio=summary_result.get('compression_ratio', 0.0),
            confidence_score=summary_result.get('confidence_score', 0.5)
        )
        
        logger.info("✅ Stored summary for %s (%s messages, %s-%s)",
                   user_id, len(messages),
                   start_time.strftime('%Y-%m-%d'), end_time.strftime('%Y-%m-%d'))
        return True
    
    async def _get_messages_in_window(
        self,
        collection_name: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Retrieve all messages in a time window from Qdrant"""
        try:
            # Convert datetime to Unix timestamps for Qdrant query
            start_timestamp = start_time.timestamp()
            end_timestamp = end_time.timestamp()
            
            # Scroll through Qdrant with filters
            results, _ = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        ),
                        FieldCondition(
                            key="timestamp_unix",
                            range=Range(
                                gte=start_timestamp,
                                lte=end_timestamp
                            )
                        )
                    ]
                ),
                limit=1000,
                with_payload=True,
                with_vectors=False  # Don't need vectors for summarization
            )
            
            messages = []
            for point in results:
                messages.append({
                    'content': point.payload.get('content', ''),
                    'timestamp': point.payload.get('timestamp', ''),
                    'memory_type': point.payload.get('memory_type', ''),
                    'emotion_label': point.payload.get('emotion_label', 'neutral')
                })
            
            # Sort by timestamp
            messages.sort(key=lambda m: m['timestamp'])
            return messages
            
        except Exception as e:
            logger.error("Error retrieving messages from Qdrant: %s", e)
            return []
    
    async def _find_unsummarized_windows(
        self,
        collection_name: str,
        user_id: str,
        existing_summaries: List[Dict]
    ) -> List[Dict]:
        """Find time windows that need summarization"""
        windows = []
        now = datetime.utcnow()
        
        # Create windows for last N days (configurable)
        for days_ago in range(config.LOOKBACK_DAYS):
            window_end = now - timedelta(days=days_ago)
            window_start = window_end - timedelta(hours=config.TIME_WINDOW_HOURS)
            
            # Check if this window overlaps with existing summaries
            overlaps = any(
                self._windows_overlap(
                    window_start, window_end,
                    summary['start_timestamp'], summary['end_timestamp']
                )
                for summary in existing_summaries
            )
            
            if not overlaps:
                windows.append({
                    'start_time': window_start,
                    'end_time': window_end
                })
        
        return windows
    
    def _windows_overlap(self, start1, end1, start2, end2) -> bool:
        """Check if two time windows overlap"""
        return start1 <= end2 and end1 >= start2
    
    async def _get_existing_summary_ranges(
        self,
        user_id: str,
        bot_name: str
    ) -> List[Dict]:
        """Get existing summary time ranges from PostgreSQL"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT start_timestamp, end_timestamp
                FROM conversation_summaries
                WHERE user_id = $1 AND bot_name = $2
                ORDER BY start_timestamp DESC
            """, user_id, bot_name)
        
        return [
            {
                'start_timestamp': row['start_timestamp'],
                'end_timestamp': row['end_timestamp']
            }
            for row in rows
        ]
    
    async def _store_conversation_summary(
        self,
        user_id: str,
        bot_name: str,
        summary_text: str,
        start_timestamp: datetime,
        end_timestamp: datetime,
        message_count: int,
        key_topics: List[str],
        emotional_tone: str,
        compression_ratio: float,
        confidence_score: float
    ):
        """Store conversation summary in PostgreSQL"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversation_summaries (
                    user_id,
                    bot_name,
                    summary_text,
                    start_timestamp,
                    end_timestamp,
                    message_count,
                    key_topics,
                    emotional_tone,
                    compression_ratio,
                    confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (user_id, bot_name, start_timestamp, end_timestamp)
                DO UPDATE SET
                    summary_text = EXCLUDED.summary_text,
                    message_count = EXCLUDED.message_count,
                    key_topics = EXCLUDED.key_topics,
                    emotional_tone = EXCLUDED.emotional_tone,
                    compression_ratio = EXCLUDED.compression_ratio,
                    confidence_score = EXCLUDED.confidence_score,
                    updated_at = NOW()
            """, user_id, bot_name, summary_text, start_timestamp, end_timestamp,
                 message_count, key_topics, emotional_tone, compression_ratio, confidence_score)
    
    def _get_bot_collections(self) -> List[str]:
        """Get list of all bot collections from Qdrant"""
        collections = self.qdrant_client.get_collections()
        
        # Filter for WhisperEngine memory collections
        bot_collections = [
            col.name for col in collections.collections
            if col.name.startswith('whisperengine_memory_') or 
               col.name.startswith('chat_memories_')
        ]
        
        return bot_collections
    
    async def _get_users_in_collection(self, collection_name: str) -> List[str]:
        """Get unique user IDs from a collection"""
        users = set()
        
        # Use scroll API to get all points (paginated)
        offset = None
        while True:
            try:
                results, next_offset = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=['user_id'],
                    with_vectors=False
                )
                
                for point in results:
                    user_id = point.payload.get('user_id')
                    if user_id:
                        users.add(user_id)
                
                if next_offset is None:
                    break
                
                offset = next_offset
                
            except Exception as e:
                logger.error("Error scanning collection %s: %s", collection_name, e)
                break
        
        return list(users)
    
    def _extract_bot_name(self, collection_name: str) -> str:
        """Extract bot name from collection name"""
        # whisperengine_memory_elena -> elena
        # chat_memories_aethys -> aethys
        if collection_name.startswith('whisperengine_memory_'):
            return collection_name.replace('whisperengine_memory_', '')
        elif collection_name.startswith('chat_memories_'):
            return collection_name.replace('chat_memories_', '')
        else:
            return collection_name


async def main():
    """Main entry point for enrichment worker"""
    try:
        # Validate configuration
        config.validate()
        logger.info("✅ Configuration validated")
        
        # Create PostgreSQL connection pool
        logger.info("Connecting to PostgreSQL: %s:%s/%s",
                   config.POSTGRES_HOST, config.POSTGRES_PORT, config.POSTGRES_DB)
        
        pool = await asyncpg.create_pool(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            database=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            min_size=2,
            max_size=10
        )
        
        logger.info("✅ PostgreSQL connection pool created")
        
        # Create and run enrichment worker
        worker = EnrichmentWorker(postgres_pool=pool)
        await worker.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Enrichment worker stopped by user")
    except Exception as e:
        logger.error("❌ Fatal error in enrichment worker: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
