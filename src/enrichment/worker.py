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
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
import asyncpg

from src.enrichment.config import config
from src.enrichment.summarization_engine import SummarizationEngine
from src.enrichment.fact_extraction_engine import FactExtractionEngine
from src.enrichment.memory_aging_engine import MemoryAgingEngine
from src.enrichment.character_performance_engine import CharacterPerformanceEngine
from src.enrichment.personality_profile_engine import PersonalityProfileEngine
from src.enrichment.context_switch_engine import ContextSwitchEngine
from src.enrichment.human_memory_behavior_engine import HumanMemoryBehaviorEngine
from src.enrichment.conversation_pattern_engine import ConversationPatternEngine
from src.enrichment.proactive_engagement_engine import ProactiveEngagementEngine
from src.llm.llm_protocol import create_llm_client
from src.temporal.temporal_protocol import create_temporal_intelligence_system
from src.memory.memory_protocol import create_memory_manager

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
        
        # Optional: Initialize spaCy preprocessor if available
        try:
            from src.enrichment.nlp_preprocessor import EnrichmentNLPPreprocessor
            self._nlp_preprocessor = EnrichmentNLPPreprocessor()
        except Exception:
            self._nlp_preprocessor = None

        # Initialize summarization engine (uses LLM_CHAT_MODEL)
        self.summarizer = SummarizationEngine(
            llm_client=self.llm_client,
            llm_model=config.LLM_CHAT_MODEL,
            preprocessor=self._nlp_preprocessor
        )
        
        # Initialize fact extraction engine (uses LLM_FACT_EXTRACTION_MODEL)
        # Defaults to Claude Sonnet 4.5 for superior conversation-level analysis
        # Can be overridden to GPT-3.5 in .env for cost savings
        self.fact_extractor = FactExtractionEngine(
            llm_client=self.llm_client,
            model=config.LLM_FACT_EXTRACTION_MODEL,
            preprocessor=self._nlp_preprocessor
        )
        
        # Initialize temporal client for InfluxDB metrics (used by CharacterPerformanceEngine)
        self.temporal_client, _ = create_temporal_intelligence_system()
        
        # Initialize vector memory manager (used by personality/context engines)
        # Note: Only initialize if fastembed is available (not in minimal enrichment containers)
        try:
            self.vector_memory = create_memory_manager(memory_type="vector")
            logger.info("✅ Vector memory manager initialized for personality/context engines")
        except ImportError as e:
            logger.warning("⚠️ Vector memory manager unavailable (fastembed not installed): %s", e)
            logger.warning("PersonalityProfileEngine and ContextSwitchEngine will be skipped")
            self.vector_memory = None
        
        # Initialize memory aging engine for strategic intelligence
        self.memory_aging_engine = MemoryAgingEngine(
            qdrant_client=self.qdrant_client,
            postgres_pool=self.db_pool
        )
        
        # Initialize character performance engine (InfluxDB metrics analysis)
        self.character_performance_engine = CharacterPerformanceEngine(
            temporal_client=self.temporal_client
        )
        
        # Initialize personality profile engine (user behavior modeling)
        self.personality_profile_engine = PersonalityProfileEngine(
            qdrant_client=self.qdrant_client,
            temporal_client=self.temporal_client
        )
        
        # Initialize context switch engine (topic transition analysis)
        self.context_switch_engine = ContextSwitchEngine(
            qdrant_client=self.qdrant_client
        )
        
        # Initialize human memory behavior engine (forgetting curves)
        self.human_memory_behavior_engine = HumanMemoryBehaviorEngine(
            qdrant_client=self.qdrant_client,
            postgres_pool=self.db_pool
        )
        
        # Initialize conversation pattern engine (behavioral patterns)
        self.conversation_pattern_engine = ConversationPatternEngine(
            qdrant_client=self.qdrant_client,
            postgres_pool=self.db_pool
        )
        
        # Initialize proactive engagement engine (re-engagement opportunities)
        self.proactive_engagement_engine = ProactiveEngagementEngine(
            qdrant_client=self.qdrant_client,
            postgres_pool=self.db_pool
        )
        
        logger.info("EnrichmentWorker initialized - Qdrant: %s:%s, Summary Model: %s, Fact Model: %s",
                   config.QDRANT_HOST, config.QDRANT_PORT, 
                   config.LLM_CHAT_MODEL, config.LLM_FACT_EXTRACTION_MODEL)
        logger.info("✅ Strategic Intelligence Engines initialized: 7/7 engines ready")
    
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
        cycle_start = datetime.now(timezone.utc)
        
        # Get all bot collections from Qdrant
        collections = self._get_bot_collections()
        logger.info("Found %s bot collections to process", len(collections))
        
        total_summaries_created = 0
        total_facts_extracted = 0
        total_preferences_extracted = 0
        total_emoji_feedback_processed = 0
        total_reflections_created = 0
        total_strategic_intelligence_processed = 0
        
        for collection_name in collections:
            bot_name = await self._extract_bot_name(collection_name)
            
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
                
                # Process preference extraction (LLM-based conversation analysis)
                preferences_extracted = await self._process_preference_extraction(
                    collection_name=collection_name,
                    bot_name=bot_name
                )
                
                total_preferences_extracted += preferences_extracted
                
                # Process emoji reactions for ML training feedback
                emoji_feedback = await self._process_emoji_feedback(
                    collection_name=collection_name,
                    bot_name=bot_name
                )
                
                total_emoji_feedback_processed += emoji_feedback
                
                # Process bot self-reflections (hybrid storage: PostgreSQL + Qdrant + InfluxDB)
                reflections_created = await self._process_bot_self_reflections(
                    collection_name=collection_name,
                    bot_name=bot_name
                )
                
                total_reflections_created += reflections_created
                
                # Process strategic intelligence (memory aging, character performance, etc.)
                strategic_count = await self._process_strategic_intelligence(
                    collection_name=collection_name,
                    bot_name=bot_name
                )
                
                total_strategic_intelligence_processed += strategic_count
                
            except Exception as e:
                logger.error("Error processing collection %s: %s", collection_name, e)
                continue
        
        cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
        logger.info("✅ Enrichment cycle complete - %s summaries, %s facts, %s preferences, %s emoji feedback, %s reflections, %s strategic intelligence in %.2fs",
                   total_summaries_created, total_facts_extracted, total_preferences_extracted, 
                   total_emoji_feedback_processed, total_reflections_created, total_strategic_intelligence_processed, cycle_duration)
    
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
                    'role': point.payload.get('role', ''),  # CRITICAL: Include role field for message formatting
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
            
            logger.debug(
                f"[QDRANT_QUERY] user={user_id}, collection={collection_name}, "
                f"since_timestamp={since_timestamp.isoformat()}, since_unix={since_unix}"
            )
            
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
            
            logger.debug(f"[QDRANT_RESULT] Found {len(results)} messages for user {user_id}")
            
            messages = []
            for point in results:
                # Parse timestamp
                timestamp_str = point.payload.get('timestamp', '')
                timestamp_unix = point.payload.get('timestamp_unix', 0)
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    # Make timezone-naive for comparison consistency
                    if timestamp.tzinfo is not None:
                        timestamp = timestamp.replace(tzinfo=None)
                except:
                    timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
                
                messages.append({
                    'content': point.payload.get('content', ''),
                    'timestamp': timestamp,
                    'memory_type': point.payload.get('memory_type', ''),
                    'role': point.payload.get('role', ''),  # CRITICAL: Include role field for message formatting
                    'emotion_label': point.payload.get('emotion_label', 'neutral')
                })
            
            # Sort by timestamp
            messages.sort(key=lambda m: m['timestamp'])
            
            # DEBUG: Log first and last message timestamps
            if messages:
                logger.debug(
                    f"[QDRANT_TIMESTAMPS] user={user_id}, first_msg={messages[0]['timestamp'].isoformat()}, "
                    f"last_msg={messages[-1]['timestamp'].isoformat()}, count={len(messages)}"
                )
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
        now = datetime.now(timezone.utc)
        
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
    
    async def _process_strategic_intelligence(
        self,
        collection_name: str,
        bot_name: str
    ) -> int:
        """
        Process strategic intelligence components for a bot collection
        
        Implements all 7 strategic intelligence engines:
        1. Memory aging analysis (memory health, retrieval trends, forgetting risks)
        2. Character performance analysis (InfluxDB metrics)
        3. Personality profile modeling (user behavior patterns)
        4. Context switch detection (topic transitions)
        5. Human memory behavior simulation (forgetting curves)
        6. Conversation pattern analysis (behavioral patterns)
        7. Proactive engagement opportunities (re-engagement signals)
        
        Incremental processing:
        - Only processes users with stale/missing cache entries
        - Respects TTL (15-minute cache expiration, longer than 11-minute enrichment cycle)
        - Avoids redundant computation
        
        Returns:
            Number of users processed with strategic intelligence
        """
        logger.info("🧠 Processing strategic intelligence for %s...", bot_name)
        
        # Get users with conversations in this collection
        users = await self._get_users_in_collection(collection_name)
        logger.debug("Found %s users for strategic analysis", len(users))
        
        # Filter to users needing analysis (stale or missing cache)
        users_to_process = await self._get_users_needing_strategic_analysis(users, bot_name)
        
        if not users_to_process:
            logger.info("✅ All users have fresh strategic intelligence cache")
            return 0
        
        logger.info("📊 Strategic analysis needed for %s/%s users (cache stale/missing)", 
                   len(users_to_process), len(users))
        
        processed_count = 0
        
        # Process in batches to avoid overwhelming the system
        batch_size = 10  # Process 10 users at a time
        
        for i in range(0, len(users_to_process), batch_size):
            batch = users_to_process[i:i + batch_size]
            
            for user_id in batch:
                try:
                    # Engine 1: Memory Aging - Analyze memory health
                    memory_health = await self.memory_aging_engine.analyze_memory_health(
                        user_id=user_id,
                        bot_name=bot_name,
                        collection_name=collection_name
                    )
                    if memory_health:
                        await self.memory_aging_engine.store_memory_health(metrics=memory_health)
                        logger.debug("✅ [1/7] Memory aging analysis complete for %s", user_id)
                        
                    # Engine 2: Character Performance - Analyze bot performance from InfluxDB
                    performance = await self.character_performance_engine.analyze_performance(
                        bot_name=bot_name,
                        user_id=user_id,
                        lookback_hours=168  # 7 days
                    )
                    if performance and performance.get('metrics_available'):
                        await self._store_character_performance(user_id, bot_name, performance)
                        logger.debug("✅ [2/7] Character performance analysis complete for %s", user_id)
                    
                    # Engine 3: Personality Profile - Model user personality from conversations
                    if self.vector_memory:
                        personality = await self.personality_profile_engine.analyze_personality(
                            bot_name=bot_name,
                            user_id=user_id,
                            lookback_days=30
                        )
                        if personality and personality.get('message_count', 0) > 0:
                            await self._store_personality_profile(user_id, bot_name, personality)
                            logger.debug("✅ [3/7] Personality profile analysis complete for %s", user_id)
                    else:
                        logger.debug("⏭️  [3/7] Personality profile skipped (vector memory unavailable)")
                    
                    # Engine 4: Context Switch - Detect topic transitions
                    if self.vector_memory:
                        context_switches = await self.context_switch_engine.analyze_context_switches(
                            bot_name=bot_name,
                            user_id=user_id,
                            lookback_days=30
                        )
                        if context_switches and context_switches.get('switch_count', 0) > 0:
                            await self._store_context_patterns(user_id, bot_name, context_switches)
                            logger.debug("✅ [4/7] Context switch analysis complete for %s", user_id)
                    else:
                        logger.debug("⏭️  [4/7] Context switch skipped (vector memory unavailable)")
                    
                    # Engine 5: Human Memory Behavior - Forgetting curve simulation
                    memory_behavior = await self.human_memory_behavior_engine.analyze_memory_behavior(
                        user_id=user_id,
                        bot_name=bot_name,
                        time_window_days=30
                    )
                    if memory_behavior and memory_behavior.get('conversation_count', 0) > 0:
                        logger.debug("✅ [5/7] Memory behavior analysis complete for %s", user_id)
                    
                    # Engine 6: Conversation Pattern - Behavioral pattern detection
                    patterns = await self.conversation_pattern_engine.analyze_conversation_patterns(
                        user_id=user_id,
                        bot_name=bot_name,
                        time_window_days=30
                    )
                    if patterns and patterns.get('conversation_count', 0) > 0:
                        logger.debug("✅ [6/7] Conversation pattern analysis complete for %s", user_id)
                    
                    # Engine 7: Proactive Engagement - Re-engagement opportunity detection
                    engagement = await self.proactive_engagement_engine.analyze_engagement_opportunities(
                        user_id=user_id,
                        bot_name=bot_name,
                        time_window_days=30
                    )
                    if engagement and engagement.get('conversation_count', 0) > 0:
                        logger.debug("✅ [7/7] Proactive engagement analysis complete for %s", user_id)
                    
                    processed_count += 1
                    logger.debug("✅ All 7 strategic engines processed for user %s", user_id)
                        
                except Exception as e:
                    logger.error("❌ Failed to process strategic intelligence for user %s: %s", 
                               user_id, e, exc_info=True)
                    continue
            
            # Brief pause between batches to avoid resource contention
            if i + batch_size < len(users_to_process):
                await asyncio.sleep(0.5)
        
        logger.info("✅ Processed strategic intelligence (7 engines) for %s/%s users in %s",
                   processed_count, len(users_to_process), bot_name)
        return processed_count
    
    async def _get_users_needing_strategic_analysis(
        self,
        users: List[str],
        bot_name: str
    ) -> List[str]:
        """
        Filter users to those needing strategic analysis (stale/missing cache).
        
        Returns only users where:
        - No cache entry exists in strategic_memory_health, OR
        - Cache entry has expired (expires_at < NOW())
        
        This prevents redundant re-processing on every enrichment cycle.
        """
        if not users:
            return []
        
        try:
            async with self.db_pool.acquire() as conn:
                # Get users with fresh cache (expires_at > NOW())
                rows = await conn.fetch("""
                    SELECT DISTINCT user_id
                    FROM strategic_memory_health
                    WHERE bot_name = $1
                      AND user_id = ANY($2::text[])
                      AND expires_at > NOW()
                """, bot_name, users)
                
                users_with_fresh_cache = {row['user_id'] for row in rows}
                
                # Return users NOT in fresh cache set
                users_needing_analysis = [
                    user_id for user_id in users 
                    if user_id not in users_with_fresh_cache
                ]
                
                logger.debug(
                    "Strategic cache status: %s fresh, %s stale/missing",
                    len(users_with_fresh_cache),
                    len(users_needing_analysis)
                )
                
                return users_needing_analysis
                
        except Exception as e:
            logger.error("Failed to check strategic cache status: %s", e)
            # On error, process all users (safe fallback)
            return users
    
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
    
    async def _extract_bot_name(self, collection_name: str) -> str:
        """
        Extract bot name from Qdrant collection name using standard naming convention.
        
        Collection names follow the convention: whisperengine_memory_{bot_name}
        This method removes the prefix and any _7d suffix to get the bot name.
        
        Examples:
        - whisperengine_memory_elena → elena
        - whisperengine_memory_elena_7d → elena (legacy suffix removed)
        - whisperengine_memory_jake → jake
        - whisperengine_memory_jake_7d → jake (legacy suffix removed)
        """
        prefix = "whisperengine_memory_"
        
        if collection_name.startswith(prefix):
            bot_name = collection_name.removeprefix(prefix)
            
            # Remove legacy _7d suffix if present
            if bot_name.endswith("_7d"):
                bot_name = bot_name.removesuffix("_7d")
            
            logger.debug(f"Extracted bot name '{bot_name}' from collection '{collection_name}'")
            return bot_name
        
        # Fallback: collection name doesn't match convention
        logger.warning(
            f"Collection '{collection_name}' doesn't follow naming convention "
            f"'{prefix}{{bot_name}}'. Using collection name as-is."
        )
        return collection_name


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
        llm_calls_made = 0
        
        for user_id in users:
            try:
                # Get last processed timestamp from existing facts
                existing_facts = await self._get_existing_facts(user_id, bot_name)
                
                if existing_facts:
                    # Find most recent MESSAGE timestamp we've processed
                    # CRITICAL FIX: Use latest_message_timestamp from context_metadata, not created_at
                    # This ensures we don't reprocess messages, only get NEW ones
                    timestamps = []
                    for fact in existing_facts:
                        # Handle context_metadata being a string, dict, or None
                        context_metadata = fact.get('context_metadata')
                        if isinstance(context_metadata, str):
                            import json
                            try:
                                context_metadata = json.loads(context_metadata)
                            except (json.JSONDecodeError, TypeError):
                                context_metadata = {}
                        elif not isinstance(context_metadata, dict):
                            context_metadata = {}
                        
                        if context_metadata.get('latest_message_timestamp'):
                            ts = datetime.fromisoformat(context_metadata['latest_message_timestamp'])
                            # TIMEZONE FIX: Keep timezone-aware for comparison
                            if ts.tzinfo is None:
                                ts = ts.replace(tzinfo=timezone.utc)
                            timestamps.append(ts)
                        elif fact.get('created_at'):
                            ts = fact['created_at']
                            # TIMEZONE FIX: Keep timezone-aware for comparison
                            if hasattr(ts, 'tzinfo') and ts.tzinfo is None:
                                ts = ts.replace(tzinfo=timezone.utc)
                            timestamps.append(ts)
                    
                    if timestamps:
                        last_processed = max(timestamps)
                    else:
                        last_processed = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
                    
                    logger.debug("Last processed MESSAGE timestamp for user %s: %s", user_id, last_processed)
                else:
                    # No facts yet - backfill from LOOKBACK_DAYS ago
                    last_processed = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
                    logger.debug("No existing facts for user %s, backfilling from %s", user_id, last_processed)
                
                # CRITICAL: Enforce maximum lookback window - NEVER process messages older than LOOKBACK_DAYS
                # This prevents burning tokens on ancient conversations even if marker timestamp is old
                max_lookback = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
                if last_processed < max_lookback:
                    logger.info(
                        f"⏭️  [ENFORCING LOOKBACK] User {user_id} marker is old ({last_processed.isoformat()}), "
                        f"enforcing {config.LOOKBACK_DAYS}-day limit (since {max_lookback.isoformat()})"
                    )
                    last_processed = max_lookback
                
                # Get NEW messages since last processing
                new_messages = await self._get_new_messages_since(
                    collection_name=collection_name,
                    user_id=user_id,
                    since_timestamp=last_processed
                )
                
                if not new_messages:
                    logger.info("⏭️  [NO LLM CALL] No new messages for fact extraction (user %s)", user_id)
                    continue
                
                if len(new_messages) < config.MIN_MESSAGES_FOR_SUMMARY:
                    logger.info("⏭️  [NO LLM CALL] Skipping user %s - only %s new messages (min: %s)", user_id, len(new_messages), config.MIN_MESSAGES_FOR_SUMMARY)
                    continue
                
                logger.info("🔍 [LLM CALL] Extracting facts from %s new messages (user %s)", len(new_messages), user_id)
                
                # Track the latest message timestamp for incremental processing
                latest_message_timestamp = max(msg['timestamp'] for msg in new_messages)
                
                # Extract facts from NEW conversation window
                extracted_facts = await self.fact_extractor.extract_facts_from_conversation_window(
                    messages=new_messages,
                    user_id=user_id,
                    bot_name=bot_name
                )
                
                llm_calls_made += 1
                
                if not extracted_facts:
                    logger.info("✅ [LLM CALL COMPLETE] No facts extracted from new messages (user %s) - 0 facts found", user_id)
                    # CRITICAL FIX: Still need to update the timestamp so we don't reprocess same messages!
                    # Store a marker record that we've processed up to latest_message_timestamp
                    await self._store_last_processed_timestamp(
                        user_id=user_id,
                        bot_name=bot_name,
                        latest_message_timestamp=latest_message_timestamp,
                        marker_type='fact'
                    )
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
                    bot_name=bot_name,
                    latest_message_timestamp=latest_message_timestamp  # Track for incremental processing
                )
                
                facts_extracted += stored_count
                logger.info("✅ [LLM CALL COMPLETE] Extracted and stored %s facts for user %s", stored_count, user_id)
                
                # CRITICAL: Update the processing marker timestamp AFTER successful extraction
                # This tells the next cycle: "we've processed messages up to latest_message_timestamp"
                # Without this, we'll keep re-extracting the same facts over and over
                await self._store_last_processed_timestamp(
                    user_id=user_id,
                    bot_name=bot_name,
                    latest_message_timestamp=latest_message_timestamp,
                    marker_type='fact'
                )
                
            except Exception as e:
                logger.error("Error extracting facts for user %s: %s", user_id, e, exc_info=True)
                continue
        
        logger.info("📊 [CYCLE SUMMARY - FACTS] Bot=%s | LLM Calls Made=%s | Facts Extracted=%s", bot_name, llm_calls_made, facts_extracted)
        return facts_extracted
    
    async def _get_existing_facts(self, user_id: str, bot_name: str) -> List[Dict]:
        """
        Get existing facts for user from PostgreSQL.
        
        Uses fact_entities + user_fact_relationships tables (matches inline extraction).
        Returns facts with created_at timestamps for incremental processing.
        
        CRITICAL: Processing markers should be returned REGARDLESS of bot_name,
        since a marker just indicates "messages have been processed up to this timestamp"
        regardless of which bot created it.
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
                  AND (
                    fe.entity_type = '_processing_marker'
                    OR ufr.context_metadata->>'bot_name' = $2
                    OR ufr.context_metadata IS NULL
                  )
                ORDER BY ufr.created_at DESC
                """,
                user_id,
                bot_name
            )
            
            return [dict(row) for row in rows]
    
    async def _store_last_processed_timestamp(
        self,
        user_id: str,
        bot_name: str,
        latest_message_timestamp: datetime,
        marker_type: str = 'fact'  # 'fact' or 'preference' for separate tracking
    ):
        """
        Store the last processed message timestamp for incremental processing.
        
        CRITICAL FIX (Oct 2025): Separate markers for facts and preferences.
        Previously, both used same marker, causing preferences to skip if facts processed first.
        
        Args:
            marker_type: 'fact' or 'preference' - determines which marker to update
        
        This creates/updates a marker record in user_fact_relationships with the latest_message_timestamp
        in context_metadata, allowing separate tracking for fact and preference extraction.
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # First, ensure user exists in universal_users (FK requirement)
                await conn.execute("""
                    INSERT INTO universal_users 
                    (universal_id, primary_username, display_name, created_at, last_active)
                    VALUES ($1, $2, $3, NOW(), NOW())
                    ON CONFLICT (universal_id) DO UPDATE SET last_active = NOW()
                """, user_id, f"user_{user_id[-8:]}", f"User {user_id[-6:]}")
                
                # Create separate marker entities for facts and preferences
                # This allows independent tracking and prevents the skip-on-second-process bug
                marker_entity_name = f"{bot_name}_{user_id}_{marker_type}"
                marker_relationship_type = f'_enrichment_{marker_type}_marker'
                
                # Create a marker entity to track processing progress
                marker_entity_id = await conn.fetchval("""
                    INSERT INTO fact_entities (entity_type, entity_name, category, attributes)
                    VALUES ('_processing_marker', $1, '_marker', $2::jsonb)
                    ON CONFLICT (entity_type, entity_name) 
                    DO UPDATE SET updated_at = NOW()
                    RETURNING id
                """, marker_entity_name, json.dumps({"type": f"enrichment_{marker_type}_progress"}))
                
                # Store the timestamp in the marker's relationship
                # CRITICAL: Ensure timestamp is naive UTC datetime for consistency
                ts_to_store = latest_message_timestamp
                if ts_to_store.tzinfo is not None:
                    ts_to_store = ts_to_store.replace(tzinfo=None)
                
                context_metadata = {
                    'latest_message_timestamp': ts_to_store.isoformat(),
                    'bot_name': bot_name,
                    'marker_type': f'enrichment_{marker_type}_progress'
                }
                
                logger.debug(
                    f"[TIMESTAMP_UPDATE] user_id={user_id}, bot_name={bot_name}, "
                    f"timestamp={ts_to_store.isoformat()}, marker_id={marker_entity_id}, type={marker_type}"
                )
                
                # DEBUG: Log what we're about to insert
                json_str = json.dumps(context_metadata)
                logger.info(f"[TIMESTAMP_DEBUG] About to INSERT: user_id={user_id}, entity_id={marker_entity_id}, context_metadata={json_str}, marker_type={marker_type}")
                
                result = await conn.execute("""
                    INSERT INTO user_fact_relationships 
                    (user_id, entity_id, relationship_type, confidence, context_metadata)
                    VALUES ($1, $2, $3, 1.0, $4::jsonb)
                    ON CONFLICT (user_id, entity_id, relationship_type)
                    DO UPDATE SET
                        context_metadata = $4::jsonb,
                        updated_at = NOW()
                """, user_id, marker_entity_id, marker_relationship_type, json_str)
                
                logger.info(f"[TIMESTAMP_RESULT] Execute result: {result}")
                
                logger.debug(
                    f"[TIMESTAMP_UPDATE_SUCCESS] user_id={user_id} - marker updated"
                )
    
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
        bot_name: str,
        latest_message_timestamp: datetime
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
        
        Args:
            latest_message_timestamp: The timestamp of the LATEST message in the conversation window.
                This is used for incremental processing - we'll query for messages AFTER this timestamp
                in the next enrichment cycle, avoiding reprocessing the same messages.
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
                            'extracted_at': datetime.now(timezone.utc).isoformat(),
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
                        # CRITICAL: Include latest_message_timestamp for incremental processing
                        context_metadata = {
                            'confirmation_count': fact.confirmation_count,
                            'related_facts': fact.related_facts,
                            'temporal_context': fact.temporal_context,
                            'reasoning': fact.reasoning,
                            'source_messages': fact.source_messages,
                            'extraction_method': 'enrichment_worker',
                            'extracted_at': datetime.now(timezone.utc).isoformat(),
                            'latest_message_timestamp': latest_message_timestamp.isoformat(),  # For incremental processing
                            'conversation_window_size': len(relationships) if relationships else 1,
                            'multi_message_confirmed': fact.confirmation_count > 1,
                            'bot_name': bot_name  # Track which bot extracted this
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
                        
                        # Check for similar/redundant relationships and consolidate to highest confidence
                        should_store = await self._consolidate_similar_relationships_enrichment(
                            conn, user_id, entity_id, fact.relationship_type, fact.confidence
                        )
                        
                        if not should_store:
                            # Weaker similar relationship exists - skip storing this one
                            logger.info(
                                f"🔄 DEDUP: Skipped storing weaker '{fact.relationship_type}' for {fact.entity_name} - "
                                f"stronger similar relationship exists"
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
                                    'relation': 'related_to',  # Changed from 'semantic_link' - this is metadata, not DB constraint
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
                        # NOTE: Removed context_metadata and updated_at - columns don't exist in schema
                        await conn.execute("""
                            INSERT INTO entity_relationships 
                            (from_entity_id, to_entity_id, relationship_type, weight)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (from_entity_id, to_entity_id, relationship_type)
                            DO UPDATE SET 
                                weight = GREATEST(entity_relationships.weight, $4)
                        """, source_entity_id, target_entity_id, 
                             relationship['relationship_type'], 
                             relationship['confidence'])
                        
                    except Exception as e:
                        logger.error("Failed to store relationship: %s", e)
                        continue
                
                # Track character interactions (PostgreSQL graph feature)
                # NOTE: Disabled - character_interactions table doesn't exist in current schema
                # TODO: Enable when table is created
                # if facts:
                #     entity_names = [fact.entity_name for fact in facts]
                #     await conn.execute("""
                #         INSERT INTO character_interactions (
                #             user_id, character_name, interaction_type,
                #             entity_references, emotional_tone, metadata
                #         ) VALUES ($1, $2, $3, $4, $5, $6)
                #     """, user_id, bot_name, 'fact_mention',
                #          json.dumps(entity_names), 'analytical',
                #          json.dumps({'extraction_method': 'enrichment_worker'}))
        
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
    
    async def _consolidate_similar_relationships_enrichment(
        self,
        conn,
        user_id: str,
        entity_id: int,
        new_relationship: str,
        new_confidence: float
    ) -> bool:
        """
        Consolidate similar/redundant relationships for the same entity (enrichment version).
        
        When storing extracted facts, check if similar relationships already exist (e.g., "likes" vs "enjoys").
        Keep only the highest confidence relationship and remove duplicates.
        
        Returns:
            True if should proceed with insert, False if insert should be skipped
        """
        # Similar relationship groups (from semantic_router.py)
        similar_groups = {
            # Positive preferences - all are similar positive expressions
            'likes': ['likes', 'loves', 'enjoys', 'prefers'],
            'loves': ['likes', 'loves', 'enjoys', 'prefers'],
            'enjoys': ['likes', 'loves', 'enjoys', 'prefers'],
            'prefers': ['likes', 'loves', 'enjoys', 'prefers'],
            
            # Negative preferences
            'dislikes': ['dislikes', 'hates', 'avoids'],
            'hates': ['dislikes', 'hates', 'avoids'],
            'avoids': ['dislikes', 'hates', 'avoids'],
            
            # Action/activity relationships
            'does': ['does', 'plays', 'practices'],
            'plays': ['does', 'plays', 'practices'],
            'practices': ['does', 'plays', 'practices'],
            
            # Possession relationships
            'owns': ['owns', 'has'],
            'has': ['owns', 'has'],
        }
        
        if new_relationship not in similar_groups:
            return True
        
        # Get similar relationships that already exist for this entity
        similar_types = similar_groups[new_relationship]
        existing = await conn.fetch("""
            SELECT relationship_type, confidence, updated_at
            FROM user_fact_relationships 
            WHERE user_id = $1 AND entity_id = $2 
            AND relationship_type = ANY($3)
            ORDER BY confidence DESC, updated_at DESC
        """, user_id, entity_id, similar_types)
        
        if not existing:
            return True
        
        # Find if there's a stronger existing relationship
        strongest_existing = existing[0]
        existing_confidence = float(strongest_existing['confidence'])
        existing_relationship = strongest_existing['relationship_type']
        
        # If we're trying to add a weaker relationship, skip it and remove duplicates
        if new_confidence <= existing_confidence:
            logger.debug(
                f"🔄 DEDUP (enrichment): Skipping weaker '{new_relationship}' (confidence: {new_confidence:.2f}) "
                f"for entity {entity_id} - stronger '{existing_relationship}' exists "
                f"(confidence: {existing_confidence:.2f})"
            )
            
            # Remove any other weaker similar relationships
            for other in existing[1:]:
                await conn.execute("""
                    DELETE FROM user_fact_relationships 
                    WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                """, user_id, entity_id, other['relationship_type'])
                logger.debug(f"🗑️ Removed redundant '{other['relationship_type']}' relationship")
            
            # Don't store the new weaker one
            return False
        else:
            # New relationship is stronger - remove all existing weaker ones
            logger.info(
                f"🔄 DEDUP (enrichment): Replacing weaker '{existing_relationship}' (confidence: {existing_confidence:.2f}) "
                f"with stronger '{new_relationship}' (confidence: {new_confidence:.2f}) for entity {entity_id}"
            )
            for other in existing:
                await conn.execute("""
                    DELETE FROM user_fact_relationships 
                    WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                """, user_id, entity_id, other['relationship_type'])
                logger.debug(f"🗑️ Removed redundant '{other['relationship_type']}' relationship")
            
            return True
        
        return stored_count

    async def _process_preference_extraction(
        self,
        collection_name: str,
        bot_name: str
    ) -> int:
        """
        Process conversation-level preference extraction using LLM analysis.
        
        Extracts user preferences from conversation windows:
        - Preferred name/nicknames
        - Pronouns (he/him, she/her, they/them, etc.)
        - Timezone/location
        - Communication style (brief, detailed, casual, formal)
        - Response length preferences
        - Language preferences
        - Topic preferences
        
        SUPERIOR to inline regex extraction:
        - Conversation context (Q&A patterns, confirmations)
        - Implicit preferences (repeated behavior patterns)
        - Preference evolution tracking
        - Unlimited preference types (not hardcoded)
        
        Stores in PostgreSQL universal_users.preferences JSONB (same as inline).
        """
        logger.info("👤 Processing preference extraction for %s...", bot_name)
        
        # Get users with conversations
        users = await self._get_users_in_collection(collection_name)
        logger.debug("Found %s users for preference extraction", len(users))
        
        preferences_extracted = 0
        llm_calls_made = 0
        
        for user_id in users:
            try:
                # Get last preference extraction timestamp
                last_extraction = await self._get_last_preference_extraction(user_id, bot_name)
                
                # CRITICAL: Enforce maximum lookback window - NEVER process messages older than LOOKBACK_DAYS
                # This prevents burning tokens on ancient conversations even if marker timestamp is old
                max_lookback = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
                if last_extraction < max_lookback:
                    logger.info(
                        f"⏭️  [ENFORCING LOOKBACK] User {user_id} preference marker is old ({last_extraction.isoformat()}), "
                        f"enforcing {config.LOOKBACK_DAYS}-day limit (since {max_lookback.isoformat()})"
                    )
                    last_extraction = max_lookback
                
                # Get NEW messages since last extraction
                new_messages = await self._get_new_messages_since(
                    collection_name=collection_name,
                    user_id=user_id,
                    since_timestamp=last_extraction
                )
                
                if not new_messages:
                    logger.info("⏭️  [NO LLM CALL] No new messages for preference extraction (user %s)", user_id)
                    continue
                
                if len(new_messages) < 3:  # Need at least a few messages for context
                    logger.info("⏭️  [NO LLM CALL] Skipping user %s - only %s new messages (min: 3)", user_id, len(new_messages))
                    continue
                
                logger.info("🔍 [LLM CALL] Extracting preferences from %s new messages (user %s)", len(new_messages), user_id)
                
                # Extract preferences from conversation window using LLM
                # Track latest message timestamp for preference extraction
                latest_message_timestamp = max(msg['timestamp'] for msg in new_messages)
                
                extracted_prefs = await self._extract_preferences_from_window(
                    messages=new_messages,
                    user_id=user_id,
                    bot_name=bot_name
                )
                
                llm_calls_made += 1
                
                if not extracted_prefs:
                    logger.info("✅ [LLM CALL COMPLETE] No preferences extracted from new messages (user %s) - 0 preferences found", user_id)
                    # CRITICAL FIX: Still need to update the timestamp so we don't reprocess same messages!
                    await self._store_last_processed_timestamp(
                        user_id=user_id,
                        bot_name=bot_name,
                        latest_message_timestamp=latest_message_timestamp,
                        marker_type='preference'
                    )
                    continue
                
                # Store preferences in PostgreSQL
                stored_count = await self._store_preferences_in_postgres(
                    preferences=extracted_prefs,
                    user_id=user_id,
                    bot_name=bot_name
                )
                
                preferences_extracted += stored_count
                logger.info("✅ [LLM CALL COMPLETE] Extracted and stored %s preferences for user %s", stored_count, user_id)
                
                # CRITICAL: Update the processing marker timestamp AFTER successful extraction
                # This tells the next cycle: "we've processed messages up to latest_message_timestamp"
                # Without this, we'll keep re-extracting the same preferences over and over
                await self._store_last_processed_timestamp(
                    user_id=user_id,
                    bot_name=bot_name,
                    latest_message_timestamp=latest_message_timestamp,
                    marker_type='preference'
                )
                
            except Exception as e:
                logger.error("Error extracting preferences for user %s: %s", user_id, e, exc_info=True)
                continue
        
        logger.info("📊 [CYCLE SUMMARY - PREFS] Bot=%s | LLM Calls Made=%s | Preferences Extracted=%s", bot_name, llm_calls_made, preferences_extracted)
        return preferences_extracted
    
    async def _get_last_preference_extraction(self, user_id: str, bot_name: str) -> datetime:
        """
        Get timestamp of last preference extraction for incremental processing.
        
        CRITICAL FIX (Oct 2025): Uses PREFERENCE-SPECIFIC marker (_enrichment_preference_marker).
        Previously used shared marker with facts, causing preferences to skip after facts processed.
        Now facts and preferences track progress independently.
        
        INCREMENTAL APPROACH:
        - Checks preference marker's latest_message_timestamp
        - Only processes NEW messages since last preference extraction
        - Independent from fact extraction progress
        """
        async with self.db_pool.acquire() as conn:
            # Check if user has a preference processing marker (separate from facts)
            row = await conn.fetchrow("""
                SELECT ufr.context_metadata, ufr.created_at
                FROM user_fact_relationships ufr
                JOIN fact_entities fe ON ufr.entity_id = fe.id
                WHERE ufr.user_id = $1 
                  AND fe.entity_type = '_processing_marker'
                  AND ufr.relationship_type = '_enrichment_preference_marker'
                LIMIT 1
            """, user_id)
            
            if row and row['context_metadata']:
                # Extract timestamp from processing marker
                context_metadata = row['context_metadata']
                if isinstance(context_metadata, str):
                    import json
                    try:
                        context_metadata = json.loads(context_metadata)
                    except json.JSONDecodeError:
                        context_metadata = {}
                
                if context_metadata.get('latest_message_timestamp'):
                    try:
                        ts = datetime.fromisoformat(context_metadata['latest_message_timestamp'])
                        # TIMEZONE FIX: Keep timezone-aware for comparison
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        logger.debug("Last preference extraction for user %s: %s (from marker)", user_id, ts)
                        return ts
                    except (ValueError, TypeError) as e:
                        logger.warning("Failed to parse marker timestamp for user %s: %s", user_id, e)
            
            # No marker yet - backfill from LOOKBACK_DAYS ago
            backfill_from = datetime.now(timezone.utc) - timedelta(days=config.LOOKBACK_DAYS)
            logger.debug("No existing preference marker for user %s, backfilling from %s", user_id, backfill_from)
            return backfill_from
    
    async def _extract_preferences_from_window(
        self,
        messages: List[Dict],
        user_id: str,
        bot_name: str
    ) -> List[Dict]:
        """
        Use LLM to extract preferences from conversation window.
        
        Analyzes conversation for:
        - Explicit preferences ("call me Mark", "I prefer brief responses")
        - Implicit preferences (user consistently requests shorter answers)
        - Preference changes over time
        - Confirmation patterns (Bot asks, user confirms)
        
        Returns list of preferences with type, value, confidence, reasoning.
        """
        # Format conversation for LLM analysis
        conversation_text = self._format_messages_for_preference_analysis(messages)

        # Optional: add pre-identified preference indicators from local NLP
        preidentified = ""
        if (
            getattr(self, "_nlp_preprocessor", None) is not None
            and self._nlp_preprocessor
            and hasattr(self._nlp_preprocessor, "is_available")
            and self._nlp_preprocessor.is_available()
        ):
            try:
                signals = self._nlp_preprocessor.extract_preference_indicators(conversation_text)
                logger.info(
                    "✅ SPACY PREFERENCE EXTRACTION: Using spaCy preprocessing "
                    f"(names={len(signals.get('names', []))}, "
                    f"locations={len(signals.get('locations', []))}, "
                    f"questions={len(signals.get('question_sentences', []))})"
                )
                preidentified = (
                    "Pre-identified signals (spaCy):\n"
                    f"- Names mentioned: {signals.get('names', [])}\n"
                    f"- Locations: {signals.get('locations', [])}\n"
                    f"- Pronoun usage: {signals.get('pronoun_counts', {})}\n"
                    f"- Question sentences: {signals.get('question_sentences', [])[:5]}\n\n"
                )
            except Exception as e:
                logger.warning(f"⚠️ SPACY PREFERENCE EXTRACTION: Failed to extract preference indicators: {e}")
                preidentified = ""
        else:
            logger.info("ℹ️ PREFERENCE EXTRACTION: Using pure LLM (no spaCy preprocessing)")
        
        prompt = f"""Analyze this conversation and extract user preferences.

{preidentified}Conversation between user and {bot_name}:
{conversation_text}

Extract ANY of these preference types that are clearly stated or strongly implied:

**Preference Types**:
1. **preferred_name**: What the user wants to be called
2. **pronouns**: Preferred pronouns (he/him, she/her, they/them, etc.)
3. **timezone**: User's timezone (EST, PST, GMT+8, etc.)
4. **location**: Where the user lives/is located
5. **communication_style**: How they prefer responses (brief, detailed, casual, formal, technical, simple)
6. **response_length**: Preferred length (short, medium, long)
7. **language**: Preferred language if not English
8. **topic_preferences**: Topics they want to focus on or avoid
9. **formality_level**: Preferred formality (casual, professional, friendly, formal)

**CRITICAL RULES**:
- ONLY extract if clearly stated OR strongly implied from repeated patterns
- Mark explicit statements with confidence 0.9-1.0
- Mark implied/inferred preferences with confidence 0.6-0.8
- Include conversation context showing where preference came from
- Detect preference CHANGES (user updated their preference)
- Handle Q&A patterns (Bot: "What should I call you?" User: "Mark is fine")

**Return JSON ONLY** (no markdown, no explanations):
{{
  "preferences": [
    {{
      "preference_type": "preferred_name",
      "preference_value": "Mark",
      "confidence": 0.95,
      "reasoning": "User explicitly stated 'call me Mark' when asked",
      "conversation_context": "Bot asked 'What should I call you?' and user responded 'Mark is fine'",
      "is_explicit": true,
      "is_preference_change": false
    }}
  ]
}}

If no clear preferences found, return {{"preferences": []}}

JSON Response:"""
        
        try:
            # Call LLM with low temperature for consistency
            messages_for_llm = [
                {
                    "role": "system",
                    "content": "You are a preference extraction specialist. Extract user preferences from conversations with high accuracy. Return ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = self.llm_client.get_chat_response(
                messages_for_llm,
                temperature=0.2,  # Low temperature for consistency
                model=config.LLM_FACT_EXTRACTION_MODEL  # Reuse fact extraction model
            )
            
            # Parse JSON response (handle markdown code blocks)
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            result = json.loads(response)
            preferences = result.get('preferences', [])
            
            logger.debug("LLM extracted %s preferences from %s messages", len(preferences), len(messages))
            return preferences
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM preference response: %s", e)
            logger.debug("Raw LLM response: %s", response[:500])
            return []
        except Exception as e:
            logger.error("LLM preference extraction failed: %s", e)
            return []
    
    def _format_messages_for_preference_analysis(self, messages: List[Dict]) -> str:
        """Format messages into readable conversation for LLM"""
        formatted = []
        
        for msg in messages:
            # CRITICAL FIX: Use 'role' field (user/bot) not 'memory_type' (conversation/fact/etc)
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            if role == 'user':
                formatted.append(f"User: {content}")
            elif role in ('bot', 'assistant'):
                formatted.append(f"Bot: {content}")
            # FALLBACK: Old memory_type field for backward compatibility
            elif msg.get('memory_type') == 'user_message':
                formatted.append(f"User: {content}")
            elif msg.get('memory_type') == 'bot_response':
                formatted.append(f"Bot: {content}")
        
        return "\n".join(formatted)
    
    async def _store_preferences_in_postgres(
        self,
        preferences: List[Dict],
        user_id: str,
        bot_name: str
    ) -> int:
        """
        Store extracted preferences in PostgreSQL universal_users.preferences JSONB.
        
        Uses SAME storage schema as inline preference extraction (semantic_router.store_user_preference).
        This ensures bots see preferences from BOTH inline AND enrichment extraction.
        
        Storage format:
        {
          "preferred_name": {
            "value": "Mark",
            "confidence": 0.95,
            "updated_at": "2025-10-19T...",
            "metadata": {
              "extraction_method": "enrichment_worker",
              "reasoning": "...",
              "conversation_context": "...",
              "is_explicit": true
            }
          }
        }
        """
        stored_count = 0
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Auto-create user in universal_users (FK requirement)
                await conn.execute("""
                    INSERT INTO universal_users 
                    (universal_id, primary_username, display_name, created_at, last_active, preferences)
                    VALUES ($1, $2, $3, NOW(), NOW(), '{}'::jsonb)
                    ON CONFLICT (universal_id) DO UPDATE SET last_active = NOW()
                """, user_id, f"user_{user_id[-8:]}", f"User {user_id[-6:]}")
                
                for pref in preferences:
                    try:
                        pref_type = pref.get('preference_type')
                        pref_value = pref.get('preference_value')
                        confidence = pref.get('confidence', 0.8)
                        
                        if not pref_type or not pref_value:
                            logger.warning("Skipping invalid preference: %s", pref)
                            continue
                        
                        # Build preference object (matches inline extraction format)
                        preference_obj = {
                            'value': pref_value,
                            'confidence': confidence,
                            'updated_at': datetime.now(timezone.utc).isoformat(),
                            'metadata': {
                                'extraction_method': 'enrichment_worker',
                                'reasoning': pref.get('reasoning', ''),
                                'conversation_context': pref.get('conversation_context', ''),
                                'is_explicit': pref.get('is_explicit', False),
                                'is_preference_change': pref.get('is_preference_change', False),
                                'bot_name': bot_name
                            }
                        }
                        
                        # Update preferences JSONB (merge with existing)
                        await conn.execute("""
                            UPDATE universal_users
                            SET preferences = COALESCE(preferences::jsonb, '{}'::jsonb) || 
                                jsonb_build_object($2::text, $3::jsonb)
                            WHERE universal_id = $1
                        """, user_id, pref_type, json.dumps(preference_obj))
                        
                        stored_count += 1
                        logger.info("✅ PREFERENCE: Stored %s='%s' for user %s (confidence: %.2f, method: enrichment_worker)",
                                  pref_type, pref_value, user_id, confidence)
                        
                    except Exception as e:
                        logger.error("Failed to store preference %s: %s", pref, e)
                        continue
        
        return stored_count


    async def _process_emoji_feedback(
        self,
        collection_name: str,
        bot_name: str
    ) -> int:
        """
        Process emoji reactions as ML training feedback.
        
        Analyzes context to determine if emoji is:
        - RATING: User evaluating bot response quality → satisfaction_score
        - AGREEMENT: User affirming bot's statement → engagement_score
        - EMOTIONAL: User expressing feeling about topic → emotional_resonance
        - CONVERSATIONAL: User acknowledging/continuing → natural_flow
        
        Only writes to InfluxDB when emoji represents actual quality feedback.
        """
        logger.info("😀 Processing emoji feedback for %s...", bot_name)
        
        # Get time window for unprocessed emoji reactions
        time_window_hours = config.TIME_WINDOW_HOURS
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
        
        # Query Qdrant for EMOJI REACTION memories (interaction_type=emoji_reaction)
        # These are stored by emoji_reaction_intelligence.py with original_bot_message metadata
        scroll_result = self.qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="timestamp_unix",
                        range=Range(
                            gte=int(time_threshold.timestamp())
                        )
                    ),
                    FieldCondition(
                        key="interaction_type",
                        match=MatchValue(value="emoji_reaction")
                    )
                ]
            ),
            limit=1000,  # Process up to 1000 recent emoji reactions per cycle
            with_payload=True,
            with_vectors=False
        )
        
        points = scroll_result[0] if scroll_result else []
        logger.info("Found %s emoji reaction memories to analyze", len(points))
        
        feedback_processed = 0
        
        # Process each emoji reaction with context
        for point in points:
            if not point.payload:
                continue
            
            try:
                user_id = point.payload.get('user_id')
                if not user_id:
                    continue
                
                # Check if already processed
                already_processed = await self._check_emoji_feedback_processed(
                    user_id=user_id,
                    bot_name=bot_name,
                    point_id=str(point.id)
                )
                
                if already_processed:
                    continue
                
                # Extract emoji reaction data from Qdrant payload
                user_message = point.payload.get('content', '')  # "[EMOJI_REACTION] ❤️"
                bot_response = point.payload.get('response', '')  # "[EMOTIONAL_FEEDBACK] ..."
                emoji = user_message.replace('[EMOJI_REACTION]', '').strip()
                
                # CRITICAL: Get original bot message from metadata
                original_bot_message = point.payload.get('original_bot_message', '')
                emotion_type = point.payload.get('emotion_type', '')
                confidence_score = point.payload.get('confidence_score', 0.0)
                
                if not original_bot_message or not emoji:
                    logger.warning("Emoji reaction missing original_bot_message or emoji: %s", point.id)
                    continue
                
                # Get surrounding conversation for context
                conversation_context = await self._get_conversation_context_around_time(
                    collection_name=collection_name,
                    user_id=user_id,
                    timestamp_unix=point.payload.get('timestamp_unix', 0),
                    window_messages=5  # Get 5 messages before the emoji
                )
                
                # Analyze emoji context using LLM
                emoji_analysis = await self._analyze_emoji_context(
                    bot_message=original_bot_message,
                    user_emoji=emoji,
                    emoji_type=emotion_type,
                    conversation_context=conversation_context
                )
                
                # Import temporal client for InfluxDB recording
                from src.temporal.temporal_protocol import create_temporal_intelligence_system
                temporal_client, _ = create_temporal_intelligence_system()
                
                if not temporal_client:
                    logger.warning("No temporal client available for emoji feedback recording")
                    continue
                
                # Record emoji feedback based on type
                if emoji_analysis['feedback_type'] == 'RATING':
                    # Quality rating → satisfaction_score
                    await temporal_client.record_emoji_reaction_feedback(
                        bot_name=bot_name,
                        user_id=user_id,
                        reaction_emoji=emoji,
                        user_reaction_score=emoji_analysis['user_reaction_score'],
                        satisfaction_score=emoji_analysis['satisfaction_score'],
                        message_id=str(point.id),
                        timestamp=None  # Use current time
                    )
                    
                    logger.info("📊 EMOJI FEEDBACK (RATING): %s → satisfaction=%.2f (confidence=%.2f) for %s/%s",
                              emoji,
                              emoji_analysis['satisfaction_score'],
                              emoji_analysis['confidence'],
                              bot_name, user_id)
                    
                    feedback_processed += 1
                
                elif emoji_analysis['feedback_type'] in ['AGREEMENT', 'CONVERSATIONAL']:
                    # Agreement/conversational → engagement_score boost
                    # Multiple emojis indicate high engagement, not quality rating
                    await temporal_client.record_emoji_reaction_feedback(
                        bot_name=bot_name,
                        user_id=user_id,
                        reaction_emoji=emoji,
                        user_reaction_score=0.0,  # Not a rating
                        satisfaction_score=0.0,   # Not a satisfaction score
                        message_id=str(point.id),
                        timestamp=None
                    )
                    
                    logger.info("📊 EMOJI FEEDBACK (ENGAGEMENT): %s → %s (confidence=%.2f) for %s/%s",
                              emoji,
                              emoji_analysis['feedback_type'],
                              emoji_analysis['confidence'],
                              bot_name, user_id)
                    
                    feedback_processed += 1
                
                else:
                    # EMOTIONAL reactions → track but don't record as quality/engagement
                    logger.debug("😀 EMOJI CONTEXT (EMOTIONAL): %s → %s (confidence=%.2f) for %s/%s",
                               emoji,
                               emoji_analysis['feedback_type'],
                               emoji_analysis['confidence'],
                               bot_name, user_id)
                
                # Mark as processed to avoid re-analyzing (stores feedback_type for debugging)
                await self._mark_emoji_feedback_processed(
                    user_id=user_id,
                    bot_name=bot_name,
                    point_id=str(point.id),
                    feedback_type=emoji_analysis['feedback_type'],
                    confidence=emoji_analysis.get('confidence', 0.0)
                )
                
            except Exception as e:
                logger.error("Failed to process emoji feedback for point %s: %s", point.id, e)
                continue
        
        return feedback_processed
    
    async def _get_conversation_context_around_time(
        self,
        collection_name: str,
        user_id: str,
        timestamp_unix: int,
        window_messages: int = 5
    ) -> List[Dict]:
        """
        Get conversation messages around the time of emoji reaction for context.
        
        Returns up to `window_messages` messages BEFORE the emoji timestamp.
        """
        # Query for conversation messages before emoji timestamp
        before_time = timestamp_unix
        after_time = timestamp_unix - (3600 * 2)  # Look back 2 hours max
        
        scroll_result = self.qdrant_client.scroll(
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
                            gte=after_time,
                            lte=before_time
                        )
                    ),
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(value="conversation")
                    )
                ]
            ),
            limit=window_messages,
            with_payload=True,
            with_vectors=False
        )
        
        points = scroll_result[0] if scroll_result else []
        
        # Convert to context format
        context = []
        for point in points:
            if not point.payload:
                continue
            
            context.append({
                'content': point.payload.get('content', ''),
                'role': point.payload.get('role', ''),
                'timestamp': point.payload.get('timestamp', ''),
                'timestamp_unix': point.payload.get('timestamp_unix', 0)
            })
        
        # Sort by timestamp (oldest first)
        context.sort(key=lambda x: x['timestamp_unix'])
        
        return context
    
    async def _analyze_emoji_context(
        self,
        bot_message: str,
        user_emoji: str,
        emoji_type: str,
        conversation_context: List[Dict]
    ) -> Dict:
        """
        Use LLM to determine if emoji is RATING vs AGREEMENT vs EMOTIONAL vs CONVERSATIONAL.
        
        Returns:
            {
                'feedback_type': 'RATING' | 'AGREEMENT' | 'EMOTIONAL' | 'CONVERSATIONAL',
                'confidence': 0.0-1.0,
                'satisfaction_score': 0.0-1.0,  # If RATING
                'user_reaction_score': 0.0-1.0,  # If RATING
                'reasoning': 'explanation'
            }
        """
        # Build conversation context (last 5 messages for efficiency)
        recent_messages = conversation_context[-5:] if len(conversation_context) > 5 else conversation_context
        context_str = "\n".join([
            f"{'Bot' if m['role'] == 'bot' else 'User'}: {m['content'][:100]}"
            for m in recent_messages
        ])
        
        prompt = f"""Analyze this emoji reaction in context:

Conversation (recent messages):
{context_str}

Bot's message: "{bot_message[:200]}"
User reacted with: {user_emoji} (classified as: {emoji_type})

Determine the PRIMARY purpose of this emoji:
A) RATING - User is evaluating the QUALITY of the bot's response (helpful, good answer, well-explained)
B) AGREEMENT - User is agreeing with the bot's STATEMENT or opinion (not rating quality, but affirming content)
C) EMOTIONAL - User is expressing an EMOTION about the topic being discussed (reacting to subject matter, not bot)
D) CONVERSATIONAL - User is acknowledging or continuing the conversation (casual social response)

Respond in JSON format:
{{
    "feedback_type": "RATING|AGREEMENT|EMOTIONAL|CONVERSATIONAL",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Examples:
- Bot explains concept → ❤️ = RATING (loved the explanation)
- Bot: "Ocean is beautiful" → ❤️ = AGREEMENT (agrees with statement)
- Bot: "Your pet died" → 😢 = EMOTIONAL (sad about topic, not rating bot)
- Bot: "How's your day?" → 👍 = CONVERSATIONAL (casual acknowledgment)
"""
        
        try:
            response = await self.llm_client.chat_completion(
                model=config.LLM_CHAT_MODEL,  # Use same model as summaries
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            # Parse JSON response
            analysis = json.loads(response)
            
            # Map emoji_type to satisfaction scores (only if RATING)
            if analysis['feedback_type'] == 'RATING':
                if 'POSITIVE_STRONG' in emoji_type:
                    satisfaction_score = 0.95
                    user_reaction_score = 1.0
                elif 'POSITIVE_MILD' in emoji_type:
                    satisfaction_score = 0.85
                    user_reaction_score = 0.85
                elif 'NEUTRAL' in emoji_type:
                    satisfaction_score = 0.6
                    user_reaction_score = 0.5
                elif 'NEGATIVE_MILD' in emoji_type:
                    satisfaction_score = 0.35
                    user_reaction_score = 0.2
                elif 'NEGATIVE_STRONG' in emoji_type:
                    satisfaction_score = 0.15
                    user_reaction_score = 0.0
                else:
                    satisfaction_score = 0.6
                    user_reaction_score = 0.5
                
                analysis['satisfaction_score'] = satisfaction_score
                analysis['user_reaction_score'] = user_reaction_score
            
            return analysis
            
        except Exception as e:
            logger.error("Failed to analyze emoji context: %s", e)
            # Default to treating as conversational (safest assumption)
            return {
                'feedback_type': 'CONVERSATIONAL',
                'confidence': 0.3,
                'reasoning': f'Failed to analyze: {e}',
                'satisfaction_score': 0.0,
                'user_reaction_score': 0.0
            }
    
    async def _check_emoji_feedback_processed(self, user_id: str, bot_name: str, point_id: str) -> bool:
        """Check if emoji reaction has already been processed"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM enrichment_processing_log
                    WHERE user_id = $1 AND bot_name = $2 
                    AND point_id = $3 AND processing_type = 'emoji_feedback'
                )
            """, user_id, bot_name, point_id)
            return result
    
    async def _mark_emoji_feedback_processed(
        self, 
        user_id: str, 
        bot_name: str, 
        point_id: str,
        feedback_type: Optional[str] = None,
        confidence: Optional[float] = None
    ):
        """Mark emoji reaction as processed with optional metadata"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO enrichment_processing_log 
                (user_id, bot_name, point_id, processing_type, processed_at, feedback_type, confidence)
                VALUES ($1, $2, $3, 'emoji_feedback', NOW(), $4, $5)
                ON CONFLICT (user_id, bot_name, point_id, processing_type) DO NOTHING
            """, user_id, bot_name, point_id, feedback_type, confidence)
    
    async def _process_bot_self_reflections(
        self,
        collection_name: str,
        bot_name: str
    ) -> int:
        """
        Process bot self-reflections for character learning and evolution
        
        HYBRID STORAGE ARCHITECTURE:
        - PostgreSQL: Primary structured storage (bot_self_reflections table)
        - Qdrant: Semantic index (bot_self_{bot_name} namespace)
        - InfluxDB: Time-series metrics (bot_self_reflection measurement)
        
        TRIGGERS:
        - Time-based: Every enrichment cycle (2 hours default)
        - Event-based: High emotion, user feedback, abandonment
        - Quality filters: Message count >= 5, emotional engagement
        """
        logger.info("🧠 Processing self-reflections for %s...", bot_name)
        
        # Get users with conversations in this collection
        users = await self._get_users_in_collection(collection_name)
        logger.debug("Found %s users with conversations for self-reflection", len(users))
        
        reflections_created = 0
        
        for user_id in users:
            try:
                # Get recent bot conversations (last 2 hours or since last reflection)
                recent_conversations = await self._get_reflection_worthy_conversations(
                    collection_name=collection_name,
                    user_id=user_id,
                    bot_name=bot_name,
                    time_window_hours=2
                )
                
                logger.info(f"🔍 User {user_id}: got {len(recent_conversations) if recent_conversations else 0} reflection-worthy conversations")
                
                if not recent_conversations:
                    logger.debug("No reflection-worthy conversations for user %s", user_id)
                    continue
                
                # Quality filter: Must have enough messages
                if len(recent_conversations) < 5:
                    logger.info(f"❌ User {user_id} filtered: only {len(recent_conversations)} messages (need >= 5)")
                    logger.debug("Insufficient messages (%s) for reflection with user %s", 
                               len(recent_conversations), user_id)
                    continue
                
                logger.info(f"✅ User {user_id} passed all filters: generating self-reflection...")
                
                # Generate self-reflection via LLM
                reflection_data = await self._generate_bot_self_reflection(
                    bot_name=bot_name,
                    user_id=user_id,
                    conversations=recent_conversations
                )
                
                if not reflection_data:
                    continue
                
                # Store in PostgreSQL (primary storage)
                reflection_id = await self._store_reflection_postgres(
                    bot_name=bot_name,
                    user_id=user_id,
                    reflection_data=reflection_data
                )
                
                # Store in Qdrant (semantic search)
                await self._store_reflection_qdrant(
                    bot_name=bot_name,
                    reflection_id=reflection_id,
                    reflection_data=reflection_data
                )
                
                # Store in InfluxDB (time-series metrics)
                await self._store_reflection_influxdb(
                    bot_name=bot_name,
                    reflection_data=reflection_data
                )
                
                reflections_created += 1
                logger.debug("✅ Created self-reflection for %s <> user %s", bot_name, user_id)
                
            except Exception as e:
                logger.error("Error creating self-reflection for user %s: %s", user_id, e)
                continue
        
        logger.info("✅ Created %s self-reflections for %s", reflections_created, bot_name)
        return reflections_created
    
    async def _get_reflection_worthy_conversations(
        self,
        collection_name: str,
        user_id: str,
        bot_name: str,
        time_window_hours: int = 2
    ) -> List[Dict[str, Any]]:
        """Get conversations worthy of self-reflection (quality filters applied)"""
        try:
            # Calculate time window (use UTC timezone-aware datetime to match storage)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Check if we already reflected on recent conversations
            async with self.db_pool.acquire() as conn:
                last_reflection = await conn.fetchrow("""
                    SELECT MAX(created_at) as last_reflection_time
                    FROM bot_self_reflections
                    WHERE bot_name = $1 AND user_id = $2
                """, bot_name, user_id)
                
                if last_reflection and last_reflection['last_reflection_time']:
                    last_time = last_reflection['last_reflection_time']
                    cutoff_timestamp = last_time.timestamp()
            
            # Query Qdrant for conversations since cutoff
            # WORKAROUND: Create fresh client instance to avoid stale connection issues
            from qdrant_client import QdrantClient
            from src.enrichment.config import config
            fresh_client = QdrantClient(
                host=config.QDRANT_HOST,
                port=config.QDRANT_PORT
            )
            logger.info(f"🔍 Querying Qdrant: collection={collection_name}, user={user_id}, cutoff={cutoff_time.isoformat()}")
            scroll_result = fresh_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        ),
                        FieldCondition(
                            key="timestamp_unix",
                            range=Range(gte=cutoff_timestamp)
                        )
                    ]
                ),
                limit=100,  # Max 100 messages per reflection window
                with_payload=True,
                with_vectors=False
            )
            logger.info(f"🔍 Scroll result type: {type(scroll_result)}, length: {len(scroll_result) if isinstance(scroll_result, (list, tuple)) else 'N/A'}")
            points = scroll_result[0] if isinstance(scroll_result, tuple) else scroll_result
            logger.info(f"🔍 Retrieved {len(points)} points for user {user_id}")
            
            # Extract conversation data
            conversations = []
            for point in points:
                if not point.payload:
                    continue
                    
                content = point.payload.get('content', '')
                role = point.payload.get('role', '')
                # CRITICAL FIX: Field name is 'emotional_context' not 'emotion_label'
                emotion_label = point.payload.get('emotional_context', 'neutral')
                roberta_confidence = point.payload.get('roberta_confidence', 0.0)
                
                # Event-based triggers: High emotion
                is_high_emotion = (
                    emotion_label in ['joy', 'anger', 'fear', 'sadness'] and 
                    roberta_confidence > 0.7
                )
                
                conversations.append({
                    'content': content,
                    'role': role,
                    'emotion_label': emotion_label,
                    'roberta_confidence': roberta_confidence,
                    'is_high_emotion': is_high_emotion,
                    'timestamp': point.payload.get('timestamp', ''),
                    'timestamp_unix': point.payload.get('timestamp_unix', 0)
                })
            
            # Sort by timestamp
            conversations.sort(key=lambda x: x['timestamp_unix'])
            
            # Quality filter: Must have emotional engagement
            high_emotion_count = sum(1 for c in conversations if c['is_high_emotion'])
            logger.info(f"🔍 Quality filter check: user={user_id}, conversations={len(conversations)}, high_emotion={high_emotion_count}")
            if high_emotion_count == 0 and len(conversations) < 10:
                # Need either high emotion OR substantial conversation
                logger.info(f"❌ Filtered out user {user_id}: insufficient quality ({high_emotion_count} emotions, {len(conversations)} messages)")
                return []
            
            logger.info(f"✅ User {user_id} passed quality filter: returning {len(conversations)} conversations")
            return conversations
            
        except Exception as e:
            logger.error("Error getting reflection-worthy conversations: %s", e)
            return []
    
    async def _generate_bot_self_reflection(
        self,
        bot_name: str,
        user_id: str,
        conversations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Generate self-reflection via LLM analysis"""
        try:
            # Build conversation context for LLM
            conversation_text = []
            for conv in conversations[-20:]:  # Last 20 messages max
                role_label = "User" if conv['role'] == 'user' else "Bot"
                emotion_label = f" [{conv['emotion_label']}]" if conv['is_high_emotion'] else ""
                conversation_text.append(f"{role_label}{emotion_label}: {conv['content']}")
            
            context = "\n".join(conversation_text)
            
            # LLM prompt for self-reflection
            prompt = f"""You are analyzing a conversation between AI character "{bot_name}" and a user.
Generate a self-reflection from the bot's perspective, analyzing effectiveness, authenticity, and emotional resonance.

CONVERSATION:
{context}

Analyze this conversation and provide a structured self-reflection with:
1. effectiveness_score (0.0-1.0): How effective were the bot's responses?
2. authenticity_score (0.0-1.0): How authentic to character personality?
3. emotional_resonance (0.0-1.0): How well did bot connect emotionally?
4. learning_insight: What did the bot learn from this interaction?
5. improvement_suggestion: How could the bot improve in similar future conversations?
6. reflection_category: Category of learning (emotional_handling, topic_expertise, conversation_flow, etc.)
7. trigger_type: What prompted this reflection? (time_based, high_emotion, user_feedback, etc.)

Respond in JSON format only."""
            
            # Generate reflection via LLM (synchronous method)
            logger.info(f"🤖 Calling LLM for self-reflection: model={config.LLM_CHAT_MODEL}, max_tokens=800")
            response = self.llm_client.generate_chat_completion(
                model=config.LLM_CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            # Extract content from OpenAI-style response format
            content = None
            if response and isinstance(response, dict):
                # Standard OpenAI format: response['choices'][0]['message']['content']
                if 'choices' in response and len(response['choices']) > 0:
                    message = response['choices'][0].get('message', {})
                    content = message.get('content', '')
                # Legacy format: response['content'] (direct)
                elif 'content' in response:
                    content = response['content']
            
            logger.info(f"🤖 Extracted content length: {len(content) if content else 0}")
            if content:
                logger.info(f"🤖 Content preview: {content[:150]}...")
            
            if not content:
                logger.warning(f"Empty LLM response for self-reflection: response keys={response.keys() if isinstance(response, dict) else 'not dict'}")
                return None
            
            # Parse JSON response (content already extracted above)
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            reflection_data = json.loads(content)
            
            # Unwrap if LLM wrapped response in a root key (e.g., {"self_reflection": {...}})
            if len(reflection_data) == 1 and isinstance(list(reflection_data.values())[0], dict):
                root_key = list(reflection_data.keys())[0]
                logger.info(f"🔧 Unwrapping nested response from key: {root_key}")
                reflection_data = reflection_data[root_key]
            
            # Add metadata
            reflection_data['interaction_context'] = context[:500]  # First 500 chars
            reflection_data['bot_response_preview'] = conversations[-1]['content'][:200] if conversations else ''
            reflection_data['conversation_id'] = None  # TODO: Add conversation_id tracking
            
            # Validate required fields
            required_fields = ['effectiveness_score', 'authenticity_score', 'emotional_resonance', 
                             'learning_insight', 'improvement_suggestion']
            if not all(field in reflection_data for field in required_fields):
                logger.warning(f"Missing required fields in reflection data. Have: {list(reflection_data.keys())}")
                return None
            
            return reflection_data
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM reflection response as JSON: %s", e)
            return None
        except Exception as e:
            logger.error("Error generating bot self-reflection: %s", e)
            return None
    
    async def _store_reflection_postgres(
        self,
        bot_name: str,
        user_id: str,
        reflection_data: Dict[str, Any]
    ) -> str:
        """Store self-reflection in PostgreSQL (primary storage)"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO bot_self_reflections (
                    bot_name, user_id, conversation_id, interaction_id,
                    effectiveness_score, authenticity_score, emotional_resonance,
                    learning_insight, improvement_suggestion, interaction_context,
                    bot_response_preview, trigger_type, reflection_category
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id
            """,
                bot_name,
                user_id,
                reflection_data.get('conversation_id'),
                reflection_data.get('interaction_id'),
                reflection_data.get('effectiveness_score'),
                reflection_data.get('authenticity_score'),
                reflection_data.get('emotional_resonance'),
                reflection_data.get('learning_insight'),
                reflection_data.get('improvement_suggestion'),
                reflection_data.get('interaction_context'),
                reflection_data.get('bot_response_preview'),
                reflection_data.get('trigger_type', 'time_based'),
                reflection_data.get('reflection_category', 'general')
            )
            return str(row['id'])
    
    async def _store_reflection_qdrant(
        self,
        bot_name: str,
        reflection_id: str,
        reflection_data: Dict[str, Any]
    ):
        """Store self-reflection in Qdrant (semantic search)"""
        try:
            from src.memory.memory_protocol import create_memory_manager
            
            # Get bot's self-memory namespace
            memory_manager = create_memory_manager(memory_type="vector")
            
            # Create searchable content
            learning_insight = reflection_data.get('learning_insight', '')
            improvement_suggestion = reflection_data.get('improvement_suggestion', '')
            content = f"[SELF_REFLECTION] {learning_insight}\n\nImprovement: {improvement_suggestion}"
            
            # Store using store_conversation with bot_name as user_id (bot's self-memory)
            # This will store in bot_self_{bot_name} namespace
            await memory_manager.store_conversation(
                user_id=bot_name,  # Use bot_name for self-memory namespace
                user_message=f"Reflection on interaction: {reflection_data.get('interaction_context', '')[:200]}",
                bot_response=content,
                pre_analyzed_emotion_data={
                    'primary_emotion': 'neutral',
                    'emotion_scores': {},
                    'roberta_confidence': 1.0,
                    'metadata': {
                        'reflection_id': reflection_id,
                        'category': reflection_data.get('reflection_category', 'general'),
                        'trigger_type': reflection_data.get('trigger_type', 'time_based'),
                        'effectiveness_score': reflection_data.get('effectiveness_score', 0.0),
                        'authenticity_score': reflection_data.get('authenticity_score', 0.0),
                        'emotional_resonance': reflection_data.get('emotional_resonance', 0.0),
                        'memory_type': 'bot_self_reflection'
                    }
                }
            )
            
        except Exception as e:
            logger.error("Error storing reflection in Qdrant: %s", e)
    
    async def _store_reflection_influxdb(
        self,
        bot_name: str,
        reflection_data: Dict[str, Any]
    ):
        """Store self-reflection metrics in InfluxDB (time-series)"""
        try:
            from src.temporal.temporal_protocol import create_temporal_intelligence_system
            
            temporal_client, _ = create_temporal_intelligence_system()
            if not temporal_client:
                logger.warning("No temporal client available for reflection metrics")
                return
            
            # Record reflection metrics
            await temporal_client.record_bot_self_reflection(
                bot_name=bot_name,
                effectiveness_score=reflection_data.get('effectiveness_score', 0.0),
                authenticity_score=reflection_data.get('authenticity_score', 0.0),
                emotional_resonance=reflection_data.get('emotional_resonance', 0.0),
                reflection_category=reflection_data.get('reflection_category', 'general'),
                trigger_type=reflection_data.get('trigger_type', 'time_based')
            )
            
        except Exception as e:
            logger.error("Error storing reflection in InfluxDB: %s", e)
    
    async def _store_character_performance(
        self,
        user_id: str,
        bot_name: str,
        performance: Dict[str, Any]
    ):
        """Store character performance analysis in strategic_character_performance table"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO strategic_character_performance (
                        user_id, bot_name, 
                        avg_response_time, response_time_trend,
                        avg_quality_score, quality_trend,
                        avg_engagement_score, engagement_trend,
                        conversation_count, analysis_period_hours,
                        performance_summary, recommendations,
                        expires_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                        NOW() + INTERVAL '5 minutes'
                    )
                    ON CONFLICT (user_id, bot_name) DO UPDATE SET
                        avg_response_time = EXCLUDED.avg_response_time,
                        response_time_trend = EXCLUDED.response_time_trend,
                        avg_quality_score = EXCLUDED.avg_quality_score,
                        quality_trend = EXCLUDED.quality_trend,
                        avg_engagement_score = EXCLUDED.avg_engagement_score,
                        engagement_trend = EXCLUDED.engagement_trend,
                        conversation_count = EXCLUDED.conversation_count,
                        analysis_period_hours = EXCLUDED.analysis_period_hours,
                        performance_summary = EXCLUDED.performance_summary,
                        recommendations = EXCLUDED.recommendations,
                        updated_at = NOW(),
                        expires_at = NOW() + INTERVAL '15 minutes'
                """,
                    user_id, bot_name,
                    performance.get('avg_response_time', 0.0),
                    performance.get('response_time_trend', 'stable'),
                    performance.get('avg_quality_score', 0.0),
                    performance.get('quality_trend', 'stable'),
                    performance.get('avg_engagement_score', 0.0),
                    performance.get('engagement_trend', 'stable'),
                    performance.get('conversation_count', 0),
                    performance.get('analysis_period_hours', 168),
                    performance.get('performance_summary', ''),
                    json.dumps(performance.get('recommendations', []))
                )
        except Exception as e:
            logger.error("Error storing character performance for %s/%s: %s", bot_name, user_id, e)
    
    async def _store_personality_profile(
        self,
        user_id: str,
        bot_name: str,
        personality: Dict[str, Any]
    ):
        """Store personality profile analysis in strategic_personality_profiles table"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO strategic_personality_profiles (
                        user_id, bot_name,
                        communication_style, formality_level, verbosity_level,
                        primary_topics, topic_diversity_score,
                        emotional_range, dominant_emotions,
                        question_frequency, avg_message_length,
                        interaction_frequency_pattern, preferred_times,
                        personality_summary,
                        expires_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                        NOW() + INTERVAL '5 minutes'
                    )
                    ON CONFLICT (user_id, bot_name) DO UPDATE SET
                        communication_style = EXCLUDED.communication_style,
                        formality_level = EXCLUDED.formality_level,
                        verbosity_level = EXCLUDED.verbosity_level,
                        primary_topics = EXCLUDED.primary_topics,
                        topic_diversity_score = EXCLUDED.topic_diversity_score,
                        emotional_range = EXCLUDED.emotional_range,
                        dominant_emotions = EXCLUDED.dominant_emotions,
                        question_frequency = EXCLUDED.question_frequency,
                        avg_message_length = EXCLUDED.avg_message_length,
                        interaction_frequency_pattern = EXCLUDED.interaction_frequency_pattern,
                        preferred_times = EXCLUDED.preferred_times,
                        personality_summary = EXCLUDED.personality_summary,
                        updated_at = NOW(),
                        expires_at = NOW() + INTERVAL '15 minutes'
                """,
                    user_id, bot_name,
                    personality.get('communication_style', 'balanced'),
                    personality.get('formality_level', 'moderate'),
                    personality.get('verbosity_level', 'moderate'),
                    json.dumps(personality.get('primary_topics', [])),
                    personality.get('topic_diversity_score', 0.5),
                    personality.get('emotional_range', 'moderate'),
                    json.dumps(personality.get('dominant_emotions', [])),
                    personality.get('question_frequency', 0.0),
                    personality.get('avg_message_length', 0),
                    personality.get('interaction_frequency_pattern', 'irregular'),
                    json.dumps(personality.get('preferred_times', [])),
                    personality.get('personality_summary', '')
                )
        except Exception as e:
            logger.error("Error storing personality profile for %s/%s: %s", bot_name, user_id, e)
    
    async def _store_context_patterns(
        self,
        user_id: str,
        bot_name: str,
        context_switches: Dict[str, Any]
    ):
        """Store context switch patterns in strategic_context_patterns table"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO strategic_context_patterns (
                        user_id, bot_name,
                        switch_count, switch_frequency,
                        avg_topic_duration_minutes, switch_patterns,
                        common_transitions, abrupt_switch_rate,
                        context_coherence_score,
                        expires_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9,
                        NOW() + INTERVAL '5 minutes'
                    )
                    ON CONFLICT (user_id, bot_name) DO UPDATE SET
                        switch_count = EXCLUDED.switch_count,
                        switch_frequency = EXCLUDED.switch_frequency,
                        avg_topic_duration_minutes = EXCLUDED.avg_topic_duration_minutes,
                        switch_patterns = EXCLUDED.switch_patterns,
                        common_transitions = EXCLUDED.common_transitions,
                        abrupt_switch_rate = EXCLUDED.abrupt_switch_rate,
                        context_coherence_score = EXCLUDED.context_coherence_score,
                        updated_at = NOW(),
                        expires_at = NOW() + INTERVAL '15 minutes'
                """,
                    user_id, bot_name,
                    context_switches.get('switch_count', 0),
                    context_switches.get('switch_frequency', 0.0),
                    context_switches.get('avg_topic_duration_minutes', 0.0),
                    json.dumps(context_switches.get('switch_patterns', [])),
                    json.dumps(context_switches.get('common_transitions', [])),
                    context_switches.get('abrupt_switch_rate', 0.0),
                    context_switches.get('context_coherence_score', 0.5)
                )
        except Exception as e:
            logger.error("Error storing context patterns for %s/%s: %s", bot_name, user_id, e)


async def main():
    """Main entry point for enrichment worker"""
    try:
        # Validate configuration
        config.validate()
        logger.info("✅ Configuration validated")
        
        # Create PostgreSQL connection pool with retry logic
        logger.info("Connecting to PostgreSQL: %s:%s/%s",
                   config.POSTGRES_HOST, config.POSTGRES_PORT, config.POSTGRES_DB)
        
        max_retries = 5
        retry_delay = 2  # seconds
        pool = None
        
        for attempt in range(1, max_retries + 1):
            try:
                pool = await asyncpg.create_pool(
                    host=config.POSTGRES_HOST,
                    port=config.POSTGRES_PORT,
                    database=config.POSTGRES_DB,
                    user=config.POSTGRES_USER,
                    password=config.POSTGRES_PASSWORD,
                    min_size=2,
                    max_size=10,
                    timeout=10  # 10 second connection timeout
                )
                logger.info("✅ PostgreSQL connection pool created")
                break
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"⚠️ Failed to connect to PostgreSQL (attempt {attempt}/{max_retries}): {e}")
                    logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to connect to PostgreSQL after {max_retries} attempts")
                    raise
        
        if pool is None:
            raise RuntimeError("Failed to create PostgreSQL connection pool")
        
        # Create and run enrichment worker
        worker = EnrichmentWorker(postgres_pool=pool)
        await worker.run()
        
    except Exception as e:
        logger.error("❌ Fatal error in enrichment worker: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
