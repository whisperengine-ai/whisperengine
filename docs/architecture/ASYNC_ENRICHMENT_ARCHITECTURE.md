# WhisperEngine Async Enrichment Architecture

**Created**: October 19, 2025  
**Status**: 🟡 Design Phase  
**Priority**: HIGH - Performance optimization + feature enhancement

---

## 📊 ARCHITECTURAL OVERVIEW

### Design Philosophy
Separate **hot path** (user-facing, real-time) from **cold path** (enrichment, async) processing to optimize user-perceived latency while enhancing intelligence quality.

### Core Concept
```
┌─────────────────────────────────────────────────────────────────┐
│                    WhisperEngine Platform                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HOT PATH (Real-time, <3s target)                             │
│  ┌──────────┐    ┌────────────┐    ┌──────────┐              │
│  │ Discord  │ -> │   Memory   │ -> │ Response │              │
│  │ Message  │    │  Storage   │    │   Send   │              │
│  └──────────┘    └────────────┘    └──────────┘              │
│                         │                                       │
│                         v (vectors only)                        │
│                   Qdrant Storage                               │
│                         │                                       │
│  ═══════════════════════════════════════════════════════════  │
│                         │                                       │
│  COLD PATH (Async, batch, high-quality)                       │
│                         v                                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │         Background Enrichment Worker                     │  │
│  │  (Separate Docker Container, Periodic Execution)        │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  1. Scan Qdrant for un-enriched messages               │  │
│  │  2. Batch fact extraction (high-quality LLM)           │  │
│  │  3. Batch conversation summarization                    │  │
│  │  4. Store enrichments in PostgreSQL                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                         │                                       │
│                         v                                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │         PostgreSQL Enrichment Storage                    │  │
│  ├─────────────────────────────────────────────────────────┤  │
│  │  • user_facts (extracted entities, preferences)         │  │
│  │  • conversation_summaries (timestamped digests)         │  │
│  │  • enrichment_metadata (processing status)              │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 KEY BENEFITS

### 1. **Performance Impact** (Hot Path)
- **Remove 2 LLM calls** from synchronous pipeline
- **Estimated savings**: 500-1000ms per message
- **User-perceived latency**: 10.35s → ~9.35s (+ other optimizations = <7s target)

### 2. **Quality Enhancement** (Cold Path)
- **High-quality models**: GPT-4 Turbo, Claude 3 Opus for summarization
- **Better fact extraction**: More comprehensive entity resolution
- **No time pressure**: Can use multi-step reasoning, chain-of-thought

### 3. **Cost Optimization**
- **Batch processing**: Better rate limit management
- **Selective enrichment**: Only process messages that need it
- **Cost tracking**: Separate budget for enrichment vs real-time

### 4. **Natural Time-Anchored Queries**
- **"What did we talk about last week?"** → Pre-computed summaries with timestamps
- **"Remind me what I told you about my job"** → Indexed facts by category
- **"Summarize our conversations from October"** → Ready-to-serve aggregations

### 5. **Scalability**
- **Independent scaling**: Background worker scales separately from Discord bots
- **Resource isolation**: Heavy LLM work doesn't affect real-time responsiveness
- **Horizontal scaling**: Multiple enrichment workers for high-volume deployments

---

## 🏗️ COMPONENT ARCHITECTURE

### 1. Hot Path (Real-time Processing)

#### Modified Memory Storage
```python
# src/memory/vector_memory_system.py (SIMPLIFIED)

class VectorMemorySystem:
    async def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        pre_analyzed_emotion_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Simplified storage - NO fact extraction, NO summarization
        Just store vectors + emotion analysis (already computed)
        """
        # Generate embeddings (still needed for retrieval)
        user_embedding = await self._generate_embedding(user_message)
        bot_embedding = await self._generate_embedding(bot_response)
        
        # Store user message vector
        await self._store_vector_point(
            collection_name=self.collection_name,
            vector_data={
                "content": user_embedding,
                "emotion": emotion_vector,  # From pre_analyzed_emotion_data
                "semantic": semantic_vector
            },
            payload={
                "user_id": user_id,
                "content": user_message,
                "memory_type": "user_message",
                "timestamp": datetime.utcnow().isoformat(),
                "enrichment_status": "pending",  # NEW: Track enrichment status
                **emotion_metadata
            }
        )
        
        # Store bot response vector
        await self._store_vector_point(...)
        
        # REMOVED: await self._extract_and_store_facts(...)
        # REMOVED: await self._generate_conversation_summary(...)
        
        logger.info(f"Stored conversation for user {user_id} - enrichment pending")
```

**Key Changes**:
- Remove `_extract_and_store_facts()` call
- Remove `_generate_conversation_summary()` call
- Add `enrichment_status: "pending"` to payload
- Maintain all vector storage + emotion analysis (already fast)

---

### 2. Cold Path (Background Enrichment Worker)

#### New Docker Container: `enrichment-worker`
```dockerfile
# docker/Dockerfile.enrichment-worker

FROM python:3.11-slim

WORKDIR /app

# Install only enrichment dependencies
COPY requirements-enrichment.txt .
RUN pip install --no-cache-dir -r requirements-enrichment.txt

# Copy enrichment worker code
COPY src/enrichment/ ./src/enrichment/
COPY src/memory/ ./src/memory/
COPY src/llm/ ./src/llm/
COPY src/database/ ./src/database/

# Run enrichment worker
CMD ["python", "-m", "src.enrichment.worker"]
```

#### Enrichment Worker Implementation
```python
# src/enrichment/worker.py

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from qdrant_client import QdrantClient
from src.llm.llm_protocol import create_llm_client
from src.database.database_manager import DatabaseManager

class EnrichmentWorker:
    """
    Background worker for async fact extraction and conversation summarization
    
    Runs periodically to:
    1. Scan Qdrant for un-enriched messages (enrichment_status == "pending")
    2. Batch process fact extraction with high-quality LLM
    3. Batch process conversation summarization
    4. Store results in PostgreSQL
    5. Update enrichment_status to "completed"
    """
    
    def __init__(
        self,
        qdrant_host: str,
        qdrant_port: int,
        postgres_pool,
        enrichment_interval_seconds: int = 300,  # 5 minutes default
        batch_size: int = 50,
        llm_model: str = "anthropic/claude-3-opus"  # High-quality model
    ):
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.db_manager = DatabaseManager(postgres_pool)
        self.llm_client = create_llm_client(llm_client_type="openrouter")
        self.enrichment_interval = enrichment_interval_seconds
        self.batch_size = batch_size
        self.llm_model = llm_model
        
    async def run(self):
        """Main worker loop"""
        logger.info(f"Enrichment worker started - interval: {self.enrichment_interval}s")
        
        while True:
            try:
                await self._enrichment_cycle()
            except Exception as e:
                logger.error(f"Enrichment cycle failed: {e}", exc_info=True)
            
            # Wait for next cycle
            await asyncio.sleep(self.enrichment_interval)
    
    async def _enrichment_cycle(self):
        """Single enrichment processing cycle"""
        logger.info("Starting enrichment cycle...")
        
        # 1. Scan all bot collections for pending enrichments
        for collection_name in await self._get_bot_collections():
            pending_messages = await self._get_pending_messages(
                collection_name=collection_name,
                limit=self.batch_size
            )
            
            if not pending_messages:
                logger.debug(f"No pending enrichments for {collection_name}")
                continue
            
            logger.info(f"Processing {len(pending_messages)} messages from {collection_name}")
            
            # 2. Batch fact extraction
            await self._batch_extract_facts(pending_messages, collection_name)
            
            # 3. Batch conversation summarization
            await self._batch_summarize_conversations(pending_messages, collection_name)
            
            # 4. Mark as enriched
            await self._mark_messages_enriched(pending_messages, collection_name)
        
        logger.info("Enrichment cycle completed")
    
    async def _get_pending_messages(
        self,
        collection_name: str,
        limit: int
    ) -> List[Dict]:
        """Get messages that need enrichment"""
        # Query Qdrant for messages with enrichment_status == "pending"
        results = await self.qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter={
                "must": [
                    {"key": "enrichment_status", "match": {"value": "pending"}}
                ]
            },
            limit=limit,
            with_payload=True,
            with_vectors=False  # Don't need vectors for enrichment
        )
        
        return [
            {
                "point_id": point.id,
                "user_id": point.payload["user_id"],
                "content": point.payload["content"],
                "timestamp": point.payload["timestamp"],
                "memory_type": point.payload["memory_type"]
            }
            for point in results[0]  # results is tuple (points, next_offset)
        ]
    
    async def _batch_extract_facts(
        self,
        messages: List[Dict],
        collection_name: str
    ):
        """Batch fact extraction with high-quality LLM"""
        # Group messages by user_id for context-aware extraction
        user_messages = {}
        for msg in messages:
            user_id = msg["user_id"]
            if user_id not in user_messages:
                user_messages[user_id] = []
            user_messages[user_id].append(msg)
        
        # Process each user's messages
        for user_id, msgs in user_messages.items():
            # Batch prompt for fact extraction
            batch_content = "\n\n".join([
                f"[{msg['timestamp']}] {msg['content']}"
                for msg in msgs
                if msg['memory_type'] == 'user_message'
            ])
            
            extraction_prompt = f"""
Extract factual information from the following user messages.
Focus on: personal details, preferences, relationships, events, plans, commitments.

Messages:
{batch_content}

Output JSON array of facts:
[
  {{"category": "personal", "fact": "...", "confidence": 0.95}},
  {{"category": "preference", "fact": "...", "confidence": 0.88}},
  ...
]
"""
            
            # High-quality LLM call (NOT blocking user response)
            response = await self.llm_client.generate_completion(
                prompt=extraction_prompt,
                model=self.llm_model,
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse and store facts
            facts = self._parse_facts_response(response)
            await self._store_facts(user_id, facts, collection_name)
            
            logger.info(f"Extracted {len(facts)} facts for user {user_id}")
    
    async def _batch_summarize_conversations(
        self,
        messages: List[Dict],
        collection_name: str
    ):
        """Batch conversation summarization with high-quality LLM"""
        # Group messages by user_id and time windows
        user_conversations = self._group_by_time_windows(messages)
        
        for user_id, time_window, conversation in user_conversations:
            # Build conversation context
            conversation_text = "\n\n".join([
                f"{'User' if msg['memory_type'] == 'user_message' else 'Bot'}: {msg['content']}"
                for msg in conversation
            ])
            
            summarization_prompt = f"""
Summarize the following conversation concisely but comprehensively.
Capture: key topics, emotional tone, decisions made, information exchanged.

Conversation ({time_window['start']} to {time_window['end']}):
{conversation_text}

Provide a structured summary (200-300 words).
"""
            
            # High-quality LLM call
            response = await self.llm_client.generate_completion(
                prompt=summarization_prompt,
                model=self.llm_model,
                temperature=0.5,
                max_tokens=500
            )
            
            # Store summary in PostgreSQL
            await self._store_conversation_summary(
                user_id=user_id,
                bot_name=self._extract_bot_name(collection_name),
                summary=response,
                start_time=time_window['start'],
                end_time=time_window['end'],
                message_count=len(conversation)
            )
            
            logger.info(f"Summarized conversation for user {user_id}: {time_window}")
    
    async def _store_facts(
        self,
        user_id: str,
        facts: List[Dict],
        collection_name: str
    ):
        """Store extracted facts in PostgreSQL"""
        bot_name = self._extract_bot_name(collection_name)
        
        async with self.db_manager.pool.acquire() as conn:
            for fact in facts:
                await conn.execute("""
                    INSERT INTO user_facts (
                        user_id,
                        bot_name,
                        category,
                        fact_content,
                        confidence,
                        extracted_at,
                        source_collection
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (user_id, bot_name, fact_content) 
                    DO UPDATE SET 
                        confidence = GREATEST(user_facts.confidence, EXCLUDED.confidence),
                        extracted_at = EXCLUDED.extracted_at
                """, user_id, bot_name, fact['category'], fact['fact'], 
                     fact['confidence'], datetime.utcnow(), collection_name)
    
    async def _store_conversation_summary(
        self,
        user_id: str,
        bot_name: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        message_count: int
    ):
        """Store conversation summary in PostgreSQL"""
        async with self.db_manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversation_summaries (
                    user_id,
                    bot_name,
                    summary_text,
                    start_timestamp,
                    end_timestamp,
                    message_count,
                    created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, user_id, bot_name, summary, start_time, end_time, 
                 message_count, datetime.utcnow())
    
    async def _mark_messages_enriched(
        self,
        messages: List[Dict],
        collection_name: str
    ):
        """Update enrichment_status to 'completed' in Qdrant"""
        for msg in messages:
            await self.qdrant_client.set_payload(
                collection_name=collection_name,
                payload={"enrichment_status": "completed"},
                points=[msg["point_id"]]
            )
    
    def _group_by_time_windows(
        self,
        messages: List[Dict],
        window_hours: int = 24
    ) -> List[tuple]:
        """Group messages into time-based conversation windows"""
        # Implementation: Group messages by user_id and 24-hour windows
        # Return: [(user_id, time_window_dict, messages_list), ...]
        pass
    
    def _extract_bot_name(self, collection_name: str) -> str:
        """Extract bot name from Qdrant collection name"""
        # whisperengine_memory_elena -> elena
        return collection_name.split("_")[-1]
```

---

### 3. PostgreSQL Schema (Enrichment Storage)

```sql
-- Database: whisperengine_db

-- User Facts Table (Extracted Entities)
CREATE TABLE user_facts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- 'personal', 'preference', 'relationship', etc.
    fact_content TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    extracted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    source_collection VARCHAR(255),  -- Qdrant collection name
    
    -- Prevent duplicate facts
    UNIQUE(user_id, bot_name, fact_content)
);

CREATE INDEX idx_user_facts_user_bot ON user_facts(user_id, bot_name);
CREATE INDEX idx_user_facts_category ON user_facts(category);
CREATE INDEX idx_user_facts_extracted_at ON user_facts(extracted_at);

-- Conversation Summaries Table (Time-Anchored)
CREATE TABLE conversation_summaries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(100) NOT NULL,
    summary_text TEXT NOT NULL,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    message_count INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Prevent duplicate summaries for same time window
    UNIQUE(user_id, bot_name, start_timestamp, end_timestamp)
);

CREATE INDEX idx_conversation_summaries_user_bot ON conversation_summaries(user_id, bot_name);
CREATE INDEX idx_conversation_summaries_time ON conversation_summaries(start_timestamp, end_timestamp);
CREATE INDEX idx_conversation_summaries_created_at ON conversation_summaries(created_at);

-- Enrichment Metadata Table (Processing Status)
CREATE TABLE enrichment_metadata (
    id SERIAL PRIMARY KEY,
    collection_name VARCHAR(255) NOT NULL,
    last_enrichment_run TIMESTAMP NOT NULL,
    messages_processed INTEGER NOT NULL,
    facts_extracted INTEGER NOT NULL,
    summaries_created INTEGER NOT NULL,
    processing_duration_seconds FLOAT NOT NULL,
    
    UNIQUE(collection_name, last_enrichment_run)
);

CREATE INDEX idx_enrichment_metadata_collection ON enrichment_metadata(collection_name);
CREATE INDEX idx_enrichment_metadata_run ON enrichment_metadata(last_enrichment_run);
```

---

### 4. Docker Compose Integration

```yaml
# docker-compose.multi-bot.template.yml (ADD THIS SERVICE)

services:
  # ... existing services (postgres, qdrant, bots, etc.) ...
  
  # NEW: Background Enrichment Worker
  enrichment-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.enrichment-worker
    container_name: enrichment-worker
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=whisperengine_db
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - ENRICHMENT_INTERVAL_SECONDS=300  # 5 minutes
      - ENRICHMENT_BATCH_SIZE=50
      - LLM_MODEL=anthropic/claude-3-opus
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    depends_on:
      - postgres
      - qdrant
    networks:
      - whisperengine-network
    restart: unless-stopped
    volumes:
      - ./logs/enrichment:/app/logs
```

---

### 5. Integration with Message Processor

```python
# src/core/message_processor.py (MODIFIED)

class MessageProcessor:
    async def _build_conversation_context_structured(
        self,
        user_id: str,
        message_content: str,
        character_name: str
    ) -> Dict[str, Any]:
        """
        Build conversation context with RETRIEVED facts + summaries
        (NOT generated inline)
        """
        # Retrieve recent conversation from Qdrant (as before)
        recent_memories = await self.memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query=message_content,
            limit=10
        )
        
        # NEW: Retrieve extracted facts from PostgreSQL
        user_facts = await self._retrieve_user_facts(user_id, character_name)
        
        # NEW: Retrieve relevant conversation summaries
        conversation_summaries = await self._retrieve_conversation_summaries(
            user_id=user_id,
            character_name=character_name,
            query=message_content  # Semantic search on summaries
        )
        
        return {
            "recent_conversation": self._format_memories(recent_memories),
            "user_facts": user_facts,  # Pre-extracted by worker
            "conversation_history": conversation_summaries,  # Pre-summarized by worker
            "current_message": message_content
        }
    
    async def _retrieve_user_facts(
        self,
        user_id: str,
        bot_name: str,
        limit: int = 20
    ) -> List[Dict]:
        """Retrieve pre-extracted facts from PostgreSQL"""
        async with self.db_pool.acquire() as conn:
            facts = await conn.fetch("""
                SELECT category, fact_content, confidence, extracted_at
                FROM user_facts
                WHERE user_id = $1 AND bot_name = $2
                ORDER BY confidence DESC, extracted_at DESC
                LIMIT $3
            """, user_id, bot_name, limit)
        
        return [dict(fact) for fact in facts]
    
    async def _retrieve_conversation_summaries(
        self,
        user_id: str,
        bot_name: str,
        query: str,
        time_range_days: int = 30
    ) -> List[Dict]:
        """Retrieve relevant conversation summaries from PostgreSQL"""
        cutoff_date = datetime.utcnow() - timedelta(days=time_range_days)
        
        async with self.db_pool.acquire() as conn:
            summaries = await conn.fetch("""
                SELECT 
                    summary_text,
                    start_timestamp,
                    end_timestamp,
                    message_count
                FROM conversation_summaries
                WHERE user_id = $1 
                  AND bot_name = $2
                  AND end_timestamp >= $3
                ORDER BY end_timestamp DESC
                LIMIT 10
            """, user_id, bot_name, cutoff_date)
        
        return [dict(summary) for summary in summaries]
```

---

## 🚀 DEPLOYMENT WORKFLOW

### Phase 1: Foundation (Week 1)
1. **Database Schema**: Create PostgreSQL tables for facts + summaries
2. **Hot Path Simplification**: Remove inline fact extraction and summarization
3. **Testing**: Validate hot path performance improvement

### Phase 2: Worker Implementation (Week 2)
1. **Enrichment Worker**: Implement core worker logic
2. **Batch Processing**: Implement fact extraction and summarization
3. **Docker Container**: Package worker as separate container

### Phase 3: Integration (Week 3)
1. **Retrieval Integration**: Update MessageProcessor to query PostgreSQL
2. **Docker Compose**: Add worker to multi-bot orchestration
3. **Monitoring**: Add Grafana dashboards for enrichment metrics

### Phase 4: Optimization (Week 4)
1. **Semantic Search**: Add vector embeddings for conversation summaries
2. **Smart Scheduling**: Implement adaptive enrichment intervals
3. **Quality Tuning**: Optimize LLM prompts for fact extraction

---

## 📊 EXPECTED IMPACT

### Performance (Hot Path)
- **Current**: 3,988ms internal processing
- **After Removal**: ~2,988ms (-1,000ms, 25% faster!)
- **User-Perceived**: 10.35s → ~8.35s (before other optimizations)

### Quality (Cold Path)
- **Better Models**: Claude 3 Opus, GPT-4 Turbo for deep analysis
- **More Context**: Batch processing allows cross-message reasoning
- **Higher Accuracy**: No time pressure = better fact extraction

### Cost Optimization
- **Batch Efficiency**: Process 50 messages per LLM call
- **Selective Processing**: Only enrich messages that need it
- **Rate Limiting**: Better control over API usage

### Feature Enablement
- **Time-Anchored Queries**: "What did we talk about last week?"
- **Fact Retrieval**: "What do you know about my job?"
- **Conversation Search**: "Find our discussion about travel plans"

---

## 🚨 RISKS & MITIGATION

### Risk 1: Delayed Fact Availability
**Problem**: User mentions fact, expects bot to remember in next message (before enrichment runs)

**Mitigation**:
- **Hot path still has recent conversation** (10+ messages with full context)
- **Enrichment runs every 5 minutes** (acceptable delay for most use cases)
- **Optional fast-track enrichment**: Trigger immediate enrichment on demand

### Risk 2: Worker Failure
**Problem**: Enrichment worker crashes or fails

**Mitigation**:
- **Docker restart policy**: `restart: unless-stopped`
- **Graceful degradation**: Bot still functions with recent conversation only
- **Health checks**: Monitor enrichment lag and alert on failures
- **Idempotent processing**: Re-run enrichment on previously processed messages safely

### Risk 3: PostgreSQL Query Performance
**Problem**: Retrieving facts + summaries adds database query time

**Mitigation**:
- **Indexed queries**: All fact/summary lookups use database indexes
- **Caching**: Implement request-scoped cache for fact retrieval (Priority 1.2)
- **Parallel retrieval**: Fetch facts + summaries in parallel with `asyncio.gather()`

### Risk 4: Storage Growth
**Problem**: Summaries + facts accumulate over time

**Mitigation**:
- **TTL policies**: Archive old summaries after 90 days
- **Fact consolidation**: Merge duplicate/outdated facts periodically
- **Pruning worker**: Separate job to clean up stale data

---

## 📚 RELATED DOCUMENTATION

- **Performance Optimization**: `docs/roadmaps/PERFORMANCE_OPTIMIZATION_ROADMAP.md`
- **Memory System**: `src/memory/vector_memory_system.py`
- **Message Processor**: `src/core/message_processor.py`
- **Docker Orchestration**: `docker-compose.multi-bot.yml`

---

## 🎯 SUCCESS METRICS

### Performance Metrics
- **Hot path latency**: Target <3,000ms (from 3,988ms)
- **Enrichment throughput**: 50+ messages per minute
- **Worker uptime**: >99% availability

### Quality Metrics
- **Fact accuracy**: >90% precision on extracted facts
- **Summary relevance**: User feedback on "what did we talk about" queries
- **Retrieval success**: % of time-anchored queries satisfied by summaries

### Cost Metrics
- **LLM cost per message**: Separate hot path vs cold path
- **Batch efficiency**: Average messages per LLM call
- **Total cost reduction**: Compare synchronous vs async enrichment

---

## 🚀 NEXT ACTIONS

### Immediate
1. User approval for architectural shift
2. Create PostgreSQL migration for facts + summaries tables
3. Begin hot path simplification (remove inline processing)

### Short-term
1. Implement enrichment worker MVP
2. Test batch fact extraction with real data
3. Validate performance improvement

### Medium-term
1. Deploy enrichment worker to production
2. Monitor enrichment lag and quality
3. Iterate on LLM prompts for better extraction

---

**Last Updated**: October 19, 2025  
**Owner**: WhisperEngine Development Team  
**Status**: 🟡 Design phase - awaiting approval to implement
