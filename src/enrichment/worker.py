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
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
import asyncpg

from src.enrichment.config import config
from src.enrichment.summarization_engine import SummarizationEngine
from src.enrichment.fact_extraction_engine import FactExtractionEngine
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
        self.llm_client = create_llm_client(
            llm_client_type="openrouter",
            api_url=config.LLM_API_URL,
            api_key=config.LLM_API_KEY
        )
        
        # Initialize summarization engine (uses LLM_CHAT_MODEL)
        self.summarizer = SummarizationEngine(
            llm_client=self.llm_client,
            llm_model=config.LLM_CHAT_MODEL
        )
        
        # Initialize fact extraction engine (uses LLM_FACT_EXTRACTION_MODEL)
        # Defaults to Claude Sonnet 4.5 for superior conversation-level analysis
        # Can be overridden to GPT-3.5 in .env for cost savings
        self.fact_extractor = FactExtractionEngine(
            llm_client=self.llm_client,
            model=config.LLM_FACT_EXTRACTION_MODEL
        )
        
        logger.info("EnrichmentWorker initialized - Qdrant: %s:%s, Summary Model: %s, Fact Model: %s",
                   config.QDRANT_HOST, config.QDRANT_PORT, 
                   config.LLM_CHAT_MODEL, config.LLM_FACT_EXTRACTION_MODEL)
    
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
        total_facts_extracted = 0
        
        for collection_name in collections:
            bot_name = self._extract_bot_name(collection_name)
            
            try:
                # Process conversation summaries for this bot
                summaries_created = await self._process_conversation_summaries(
                    collection_name=collection_name,
                    bot_name=bot_name
                )
                
                total_summaries_created += summaries_created
                
                # Process fact extraction (conversation-level analysis)
                facts_extracted = await self._process_fact_extraction(
                    collection_name=collection_name,
                    bot_name=bot_name
                )
                
                total_facts_extracted += facts_extracted
                
            except Exception as e:
                logger.error("Error processing collection %s: %s", collection_name, e)
                continue
        
        cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
        logger.info("✅ Enrichment cycle complete - %s summaries, %s facts extracted in %.2fs",
                   total_summaries_created, total_facts_extracted, cycle_duration)
    
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
                    logger.debug("✅ No new messages for user %s", user_id)
                    continue
                
                logger.info("🔍 Found %s windows for user %s (new message activity detected)", 
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
        
        logger.info("📝 Creating summary for %s from %s to %s",
                    user_id, start_time, end_time)
        
        # Retrieve all messages in this time window
        messages = await self._get_messages_in_window(
            collection_name=collection_name,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time
        )
        
        logger.info("📊 Retrieved %s messages for window", len(messages))
        
        if len(messages) < config.MIN_MESSAGES_FOR_SUMMARY:
            logger.info("⏭️  Skipping window - only %s messages (min: %s)",
                        len(messages), config.MIN_MESSAGES_FOR_SUMMARY)
            return False
        
        logger.info("🤖 Generating LLM summary for %s messages...", len(messages))
        
        # Generate high-quality summary using LLM
        try:
            summary_result = await self.summarizer.generate_conversation_summary(
                messages=messages,
                user_id=user_id,
                bot_name=bot_name
            )
            logger.info("✅ LLM summary generated: %s chars", len(summary_result.get('summary_text', '')))
        except Exception as e:
            logger.error("❌ Failed to generate summary: %s", e, exc_info=True)
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
            logger.error("Error retrieving messages: %s", e)
            return []
    
    async def _get_new_messages_since(
        self,
        collection_name: str,
        user_id: str,
        since_timestamp: datetime
    ) -> List[Dict]:
        """
        Get NEW messages for a user since a specific timestamp.
        
        This is the INCREMENTAL approach - only fetch messages we haven't processed yet.
        Avoids wasteful re-querying of old conversations.
        """
        try:
            # Convert datetime to Unix timestamp for Qdrant query
            since_unix = since_timestamp.timestamp()
            
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
                                gt=since_unix  # Greater than (not gte) to avoid re-processing
                            )
                        )
                    ]
                ),
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            messages = []
            for point in results:
                # Parse timestamp
                timestamp_str = point.payload.get('timestamp', '')
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.utcnow()
                
                messages.append({
                    'content': point.payload.get('content', ''),
                    'timestamp': timestamp,
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
        """
        Find time windows that need summarization using INCREMENTAL approach.
        
        Strategy:
        1. Find the LAST processed timestamp (most recent summary end_timestamp)
        2. Query Qdrant for NEW messages since that timestamp
        3. Create windows ONLY for new message activity
        4. Avoids wasteful re-processing of same old conversations
        """
        windows = []
        now = datetime.utcnow()
        
        # Find the last processed timestamp
        if existing_summaries:
            # Get the most recent summary's end time
            last_processed = max(s['end_timestamp'] for s in existing_summaries)
            logger.debug("Last processed timestamp for user %s: %s", user_id, last_processed)
        else:
            # No summaries yet - look back N days for initial backfill
            last_processed = now - timedelta(days=config.LOOKBACK_DAYS)
            logger.debug("No existing summaries for user %s, backfilling from %s", user_id, last_processed)
        
        # Get NEW messages since last processing
        new_messages = await self._get_new_messages_since(
            collection_name=collection_name,
            user_id=user_id,
            since_timestamp=last_processed
        )
        
        if not new_messages:
            logger.debug("No new messages for user %s since %s", user_id, last_processed)
            return []
        
        # Group new messages into time-based windows
        # Use 24-hour windows for consistency
        message_times = [msg['timestamp'] for msg in new_messages]
        earliest_new = min(message_times)
        latest_new = max(message_times)
        
        # Create windows covering the new message timespan
        current_window_start = earliest_new
        while current_window_start < latest_new:
            window_end = min(current_window_start + timedelta(hours=config.TIME_WINDOW_HOURS), latest_new)
            
            windows.append({
                'start_time': current_window_start,
                'end_time': window_end
            })
            
            current_window_start = window_end
        
        logger.debug("Created %s windows for %s new messages (user %s)", 
                    len(windows), len(new_messages), user_id)
        
        return windows
    
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


        return bot_name


    async def _process_fact_extraction(
        self,
        collection_name: str,
        bot_name: str
    ) -> int:
        """
        Process conversation-level fact extraction for a bot collection.
        
        Uses INCREMENTAL approach (same as summaries):
        1. Tracks last processed timestamp via existing facts
        2. Only processes NEW messages since last extraction
        3. Avoids wasteful re-processing of old conversations
        4. Analyzes conversation windows for context
        5. Detects confirmation patterns and conflicts
        6. Builds knowledge graph relationships
        """
        logger.info("🧠 Processing fact extraction for %s...", bot_name)
        
        # Get users with conversations in this collection
        users = await self._get_users_in_collection(collection_name)
        logger.debug("Found %s users for fact extraction", len(users))
        
        facts_extracted = 0
        
        for user_id in users:
            try:
                # Get last processed timestamp from existing facts
                existing_facts = await self._get_existing_facts(user_id, bot_name)
                
                if existing_facts:
                    # Find most recent fact extraction timestamp
                    last_processed = max(
                        fact.get('created_at', datetime.utcnow() - timedelta(days=30))
                        for fact in existing_facts
                    )
                    logger.debug("Last fact extraction for user %s: %s", user_id, last_processed)
                else:
                    # No facts yet - backfill from 30 days ago
                    last_processed = datetime.utcnow() - timedelta(days=config.LOOKBACK_DAYS)
                    logger.debug("No existing facts for user %s, backfilling from %s", user_id, last_processed)
                
                # Get NEW messages since last processing
                new_messages = await self._get_new_messages_since(
                    collection_name=collection_name,
                    user_id=user_id,
                    since_timestamp=last_processed
                )
                
                if not new_messages:
                    logger.debug("✅ No new messages for fact extraction (user %s)", user_id)
                    continue
                
                if len(new_messages) < config.MIN_MESSAGES_FOR_SUMMARY:
                    logger.debug("Skipping user %s - only %s new messages", user_id, len(new_messages))
                    continue
                
                logger.info("🔍 Extracting facts from %s new messages (user %s)", len(new_messages), user_id)
                
                # Extract facts from NEW conversation window
                extracted_facts = await self.fact_extractor.extract_facts_from_conversation_window(
                    messages=new_messages,
                    user_id=user_id,
                    bot_name=bot_name
                )
                
                if not extracted_facts:
                    logger.debug("No facts extracted from new messages (user %s)", user_id)
                    continue
                
                # Detect conflicts with existing facts
                conflicts = await self.fact_extractor.detect_fact_conflicts(
                    new_facts=extracted_facts,
                    existing_facts=existing_facts
                )
                
                # Resolve conflicts
                if conflicts:
                    logger.info("Detected %s fact conflicts for user %s", len(conflicts), user_id)
                    resolutions = await self.fact_extractor.resolve_fact_conflicts(conflicts)
                    await self._apply_conflict_resolutions(resolutions, user_id, bot_name)
                
                # Build knowledge graph relationships
                relationships = await self.fact_extractor.build_knowledge_graph_relationships(
                    facts=extracted_facts,
                    user_id=user_id,
                    bot_name=bot_name
                )
                
                # Organize and classify facts
                organized_facts = await self.fact_extractor.organize_and_classify_facts(
                    facts=extracted_facts
                )
                
                # Store facts in PostgreSQL (same tables as inline extraction)
                stored_count = await self._store_facts_in_postgres(
                    facts=extracted_facts,
                    relationships=relationships,
                    user_id=user_id,
                    bot_name=bot_name
                )
                
                facts_extracted += stored_count
                logger.info("✅ Extracted and stored %s facts for user %s", stored_count, user_id)
                
            except Exception as e:
                logger.error("Error extracting facts for user %s: %s", user_id, e, exc_info=True)
                continue
        
        logger.info("✅ Extracted %s total facts for %s", facts_extracted, bot_name)
        return facts_extracted
    
    async def _get_existing_facts(self, user_id: str, bot_name: str) -> List[Dict]:
        """
        Get existing facts for user from PostgreSQL.
        
        Uses fact_entities + user_fact_relationships tables (matches inline extraction).
        Returns facts with created_at timestamps for incremental processing.
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    fe.entity_name,
                    fe.entity_type,
                    ufr.relationship_type,
                    ufr.confidence,
                    ufr.created_at,
                    ufr.context_metadata
                FROM user_fact_relationships ufr
                JOIN fact_entities fe ON ufr.entity_id = fe.id
                WHERE ufr.user_id = $1 
                  AND (ufr.context_metadata->>'bot_name' = $2 OR ufr.context_metadata IS NULL)
                ORDER BY ufr.created_at DESC
                """,
                user_id,
                bot_name
            )
            
            return [dict(row) for row in rows]
    
    async def _apply_conflict_resolutions(
        self,
        resolutions: List[Dict],
        user_id: str,
        bot_name: str
    ):
        """
        Apply conflict resolution actions to database.
        
        Uses fact_entities + user_fact_relationships tables (NOT user_facts).
        """
        async with self.db_pool.acquire() as conn:
            for resolution in resolutions:
                try:
                    if resolution['action'] == 'update':
                        # Archive old fact by updating metadata in user_fact_relationships
                        fact_to_archive = resolution['fact_to_archive']
                        await conn.execute(
                            """
                            UPDATE user_fact_relationships
                            SET metadata = jsonb_set(
                                COALESCE(metadata, '{}'::jsonb),
                                '{archived}',
                                'true'
                            )
                            WHERE user_id = $1
                              AND entity_id = (
                                  SELECT entity_id FROM fact_entities 
                                  WHERE entity_name = $2 LIMIT 1
                              )
                              AND relationship_type = $3
                            """,
                            user_id,
                            fact_to_archive.entity_name,
                            fact_to_archive.relationship_type
                        )
                        logger.debug("Archived conflicting fact: %s", fact_to_archive.entity_name)
                    
                    elif resolution['action'] == 'flag':
                        # Flag for manual review
                        logger.warning(
                            "Fact conflict flagged for review - User: %s, Conflict: %s",
                            user_id,
                            resolution['reasoning']
                        )
                        
                except Exception as e:
                    logger.error("Failed to apply resolution: %s", e)
                    continue
    
    async def _store_facts_in_postgres(
        self,
        facts: List,
        relationships: List[Dict],
        user_id: str,
        bot_name: str
    ) -> int:
        """
        Store extracted facts in PostgreSQL using SAME schema as inline extraction.
        
        Uses fact_entities and user_fact_relationships tables (matches semantic_router.py).
        This ensures bots see facts from BOTH inline AND enrichment extraction.
        
        Storage logic matches store_user_fact() in semantic_router.py:
        1. Auto-create user in universal_users
        2. Insert/update fact_entities
        3. Check for opposing relationship conflicts
        4. Insert/update user_fact_relationships
        5. Auto-discover similar entities
        """
        stored_count = 0
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Auto-create user in universal_users (FK requirement)
                await conn.execute("""
                    INSERT INTO universal_users 
                    (universal_id, primary_username, display_name, created_at, last_active)
                    VALUES ($1, $2, $3, NOW(), NOW())
                    ON CONFLICT (universal_id) DO UPDATE SET last_active = NOW()
                """, user_id, f"user_{user_id[-8:]}", f"User {user_id[-6:]}")
                
                for fact in facts:
                    try:
                        # Build attributes JSONB for fact_entities
                        attributes = {
                            'extraction_method': 'enrichment_worker',
                            'extracted_at': datetime.utcnow().isoformat(),
                            'tags': fact.related_facts  # Used for full-text search
                        }
                        
                        # Insert or update entity in fact_entities (matches semantic_router.py)
                        # Include category field to match inline extraction schema
                        entity_id = await conn.fetchval("""
                            INSERT INTO fact_entities (entity_type, entity_name, category, attributes)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (entity_type, entity_name) 
                            DO UPDATE SET 
                                category = COALESCE($3, fact_entities.category),
                                attributes = fact_entities.attributes || COALESCE($4, '{}'::jsonb),
                                updated_at = NOW()
                            RETURNING id
                        """, fact.entity_type, fact.entity_name, fact.entity_type, json.dumps(attributes))
                        
                        # Build context_metadata JSONB for user_fact_relationships
                        # This leverages PostgreSQL graph features for rich metadata
                        context_metadata = {
                            'confirmation_count': fact.confirmation_count,
                            'related_facts': fact.related_facts,
                            'temporal_context': fact.temporal_context,
                            'reasoning': fact.reasoning,
                            'source_messages': fact.source_messages,
                            'extraction_method': 'enrichment_worker',
                            'extracted_at': datetime.utcnow().isoformat(),
                            'conversation_window_size': len(relationships) if relationships else 1,
                            'multi_message_confirmed': fact.confirmation_count > 1
                        }
                        
                        # Check for opposing relationship conflicts (matches semantic_router.py)
                        conflict_result = await self._detect_opposing_relationships_inline_style(
                            conn, user_id, entity_id, fact.relationship_type, fact.confidence
                        )
                        
                        if conflict_result == 'keep_existing':
                            # Don't store - stronger opposing relationship exists
                            logger.info(
                                f"🚫 CONFLICT: Skipped storing '{fact.relationship_type}' for {fact.entity_name} - "
                                f"stronger opposing relationship exists"
                            )
                            continue
                        
                        # Insert or update user-fact relationship with context_metadata
                        # Leverages PostgreSQL graph features: context_metadata JSONB for rich storage
                        await conn.execute("""
                            INSERT INTO user_fact_relationships 
                            (user_id, entity_id, relationship_type, confidence, emotional_context, 
                             mentioned_by_character, source_conversation_id, context_metadata)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                            ON CONFLICT (user_id, entity_id, relationship_type)
                            DO UPDATE SET
                                confidence = GREATEST(user_fact_relationships.confidence, $4),
                                context_metadata = user_fact_relationships.context_metadata || $8::jsonb,
                                mentioned_by_character = COALESCE($6, user_fact_relationships.mentioned_by_character),
                                updated_at = NOW()
                        """, user_id, entity_id, fact.relationship_type, fact.confidence,
                             'neutral',  # Emotional context from conversation analysis
                             bot_name, 
                             None,  # No source_conversation_id for enrichment
                             json.dumps(context_metadata))
                        
                        stored_count += 1
                        logger.info(
                            f"✅ ENRICHMENT FACT: Stored '{fact.entity_name}' "
                            f"({fact.entity_type}, {fact.relationship_type}, confidence={fact.confidence:.2f})"
                        )
                        
                        # Build related_entities JSONB array (PostgreSQL graph feature)
                        # Links facts to their semantic relationships for fast graph traversal
                        related_entities_array = []
                        for related_fact_name in fact.related_facts:
                            # Find related entity ID
                            related_entity_id = await conn.fetchval("""
                                SELECT id FROM fact_entities 
                                WHERE entity_name = $1
                            """, related_fact_name)
                            
                            if related_entity_id:
                                related_entities_array.append({
                                    'entity_id': str(related_entity_id),
                                    'relation': 'semantic_link',
                                    'weight': 0.8
                                })
                        
                        # Update related_entities JSONB array
                        if related_entities_array:
                            await conn.execute("""
                                UPDATE user_fact_relationships
                                SET related_entities = $1
                                WHERE user_id = $2 AND entity_id = $3 AND relationship_type = $4
                            """, json.dumps(related_entities_array), user_id, entity_id, fact.relationship_type)
                        
                        # Auto-discover similar entities (matches semantic_router.py)
                        similar_entities = await conn.fetch("""
                            SELECT id, entity_name, 
                                   similarity(entity_name, $1) as sim_score
                            FROM fact_entities
                            WHERE entity_type = $2
                              AND id != $3
                              AND similarity(entity_name, $1) > 0.3
                            ORDER BY sim_score DESC
                            LIMIT 5
                        """, fact.entity_name, fact.entity_type, entity_id)
                        
                        # Create entity relationships for similar entities
                        # Mark as bidirectional (PostgreSQL graph feature for symmetric relationships)
                        for similar in similar_entities:
                            await conn.execute("""
                                INSERT INTO entity_relationships 
                                (from_entity_id, to_entity_id, relationship_type, weight, bidirectional)
                                VALUES ($1, $2, 'similar_to', $3, true)
                                ON CONFLICT (from_entity_id, to_entity_id, relationship_type) 
                                DO UPDATE SET 
                                    weight = GREATEST(entity_relationships.weight, $3),
                                    bidirectional = true
                            """, entity_id, similar["id"], min(float(similar["sim_score"]), 0.9))
                        
                    except Exception as e:
                        logger.error("Failed to store fact %s: %s", fact.entity_name, e)
                        continue
                
                # Store knowledge graph relationships (from fact extraction intelligence)
                for relationship in relationships:
                    try:
                        source_fact = relationship.get('source_fact')
                        target_fact = relationship.get('target_fact')
                        
                        if not source_fact or not target_fact:
                            continue
                        
                        # Get entity IDs for both facts
                        source_entity_id = await conn.fetchval("""
                            SELECT id FROM fact_entities 
                            WHERE entity_type = $1 AND entity_name = $2
                        """, source_fact.entity_type, source_fact.entity_name)
                        
                        target_entity_id = await conn.fetchval("""
                            SELECT id FROM fact_entities 
                            WHERE entity_type = $1 AND entity_name = $2
                        """, target_fact.entity_type, target_fact.entity_name)
                        
                        if not source_entity_id or not target_entity_id:
                            continue
                        
                        # Store in entity_relationships table
                        await conn.execute("""
                            INSERT INTO entity_relationships 
                            (from_entity_id, to_entity_id, relationship_type, weight, context_metadata)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (from_entity_id, to_entity_id, relationship_type)
                            DO UPDATE SET 
                                weight = GREATEST(entity_relationships.weight, $4),
                                updated_at = NOW()
                        """, source_entity_id, target_entity_id, 
                             relationship['relationship_type'], 
                             relationship['confidence'],
                             json.dumps({
                                'reasoning': relationship.get('reasoning'),
                                'extraction_method': 'enrichment_worker'
                             }))
                        
                    except Exception as e:
                        logger.error("Failed to store relationship: %s", e)
                        continue
                
                # Track character interactions (PostgreSQL graph feature)
                # This enables character-aware responses by tracking which character learned which facts
                if facts:
                    entity_names = [fact.entity_name for fact in facts]
                    
                    await conn.execute("""
                        INSERT INTO character_interactions (
                            user_id, character_name, interaction_type,
                            entity_references, emotional_tone, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                    """, user_id, bot_name, 'fact_mention',
                         json.dumps(entity_names),
                         'analytical',  # Enrichment worker tone
                         json.dumps({
                             'extraction_method': 'enrichment_worker',
                             'facts_extracted': len(facts),
                             'relationships_created': len(relationships),
                             'extracted_at': datetime.utcnow().isoformat()
                         }))
                    
                    logger.info(
                        f"✅ CHARACTER INTERACTION: Logged {len(entity_names)} entity mentions by {bot_name}"
                    )
        
        return stored_count
    
    async def _detect_opposing_relationships_inline_style(
        self,
        conn,
        user_id: str,
        entity_id: int,
        new_relationship: str,
        new_confidence: float
    ) -> Optional[str]:
        """
        Detect opposing relationships (matches semantic_router.py logic).
        
        Returns:
            'keep_existing', 'resolved', or None if no conflicts
        """
        # Opposing relationships mapping (from fact_extraction_engine.py)
        opposing_relationships = {
            'likes': ['dislikes', 'hates', 'avoids'],
            'loves': ['dislikes', 'hates', 'avoids'],
            'enjoys': ['dislikes', 'hates', 'avoids'],
            'prefers': ['dislikes', 'avoids', 'rejects'],
            'wants': ['rejects', 'avoids', 'dislikes'],
            'needs': ['rejects', 'avoids'],
            'supports': ['opposes', 'rejects'],
            'trusts': ['distrusts', 'suspects'],
            'believes': ['doubts', 'rejects'],
            # Reverse mappings
            'dislikes': ['likes', 'loves', 'enjoys', 'prefers', 'wants'],
            'hates': ['likes', 'loves', 'enjoys'],
            'avoids': ['likes', 'loves', 'enjoys', 'prefers', 'wants', 'needs'],
            'rejects': ['wants', 'needs', 'prefers', 'supports', 'believes'],
            'opposes': ['supports'],
            'distrusts': ['trusts'],
            'doubts': ['believes'],
            'suspects': ['trusts']
        }
        
        if new_relationship not in opposing_relationships:
            return None
        
        # Check for existing opposing relationships
        opposing_types = opposing_relationships[new_relationship]
        conflicts = await conn.fetch("""
            SELECT relationship_type, confidence, updated_at, mentioned_by_character
            FROM user_fact_relationships 
            WHERE user_id = $1 AND entity_id = $2 
            AND relationship_type = ANY($3)
            ORDER BY confidence DESC, updated_at DESC
        """, user_id, entity_id, opposing_types)
        
        if not conflicts:
            return None
        
        for conflict in conflicts:
            conflict_confidence = float(conflict['confidence'])
            
            if conflict_confidence > new_confidence:
                # Keep stronger existing opposing relationship
                logger.info(
                    f"⚠️ CONFLICT DETECTED: Keeping stronger existing '{conflict['relationship_type']}' "
                    f"(confidence: {conflict_confidence:.2f}) over new '{new_relationship}' "
                    f"(confidence: {new_confidence:.2f})"
                )
                return 'keep_existing'
            else:
                # Replace weaker opposing relationship with stronger new one
                await conn.execute("""
                    DELETE FROM user_fact_relationships 
                    WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                """, user_id, entity_id, conflict['relationship_type'])
                
                logger.info(
                    f"🔄 CONFLICT RESOLVED: Replaced weaker '{conflict['relationship_type']}' "
                    f"(confidence: {conflict_confidence:.2f}) with stronger '{new_relationship}' "
                    f"(confidence: {new_confidence:.2f})"
                )
        
        return 'resolved'
        
        return stored_count


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
        
    except Exception as e:
        logger.error("❌ Fatal error in enrichment worker: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
