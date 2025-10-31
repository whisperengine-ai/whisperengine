"""
Human Memory Behavior Engine for Strategic Intelligence System.

Models human forgetting curves and memory retrieval patterns from conversation history.
Analyzes:
- Memory decay patterns over time (forgetting curves)
- Retrieval frequency and success rates
- Memory reinforcement opportunities
- Optimal recall timing predictions

This is a background strategic analysis engine (Phase 3B - Engine 5/7).
Results are cached in PostgreSQL strategic_memory_behavior table and retrieved
by hot path in <5ms during Phase 2.8.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import math
import asyncpg
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class HumanMemoryBehaviorEngine:
    """
    Analyzes human-like memory behavior patterns to model forgetting and retrieval.
    
    Key Metrics:
    - Forgetting curve coefficients (decay rate, retention baseline)
    - Memory retrieval success probability over time
    - Reinforcement event frequency
    - Optimal recall timing predictions
    
    Uses conversation history from Qdrant to model:
    1. How quickly topics/entities fade from active memory
    2. Which memories are reinforced through repeated mentions
    3. Optimal timing for bot to reference past conversations
    """
    
    def __init__(
        self,
        qdrant_client: QdrantClient,
        postgres_pool: asyncpg.Pool
    ):
        self.qdrant_client = qdrant_client
        self.db_pool = postgres_pool
        
        # Forgetting curve parameters (based on Ebbinghaus forgetting curve)
        # R(t) = baseline + (1 - baseline) * e^(-decay_rate * t)
        self.default_decay_rate = 0.1  # Default decay per day
        self.default_retention_baseline = 0.2  # Long-term retention floor
        
        logger.info("✅ HumanMemoryBehaviorEngine initialized")
    
    async def analyze_memory_behavior(
        self,
        user_id: str,
        bot_name: str,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze human-like memory behavior patterns for a user.
        
        Args:
            user_id: User identifier
            bot_name: Bot name for collection routing
            time_window_days: Analysis window (default 30 days)
        
        Returns:
            Memory behavior analysis with forgetting curves and predictions
        """
        try:
            logger.info("🧠 Analyzing memory behavior for user %s (bot: %s)", user_id, bot_name)
            
            # Retrieve conversation history
            conversation_history = await self._get_conversation_history(
                user_id, bot_name, time_window_days
            )
            
            if not conversation_history:
                logger.warning("No conversation history for user %s", user_id)
                return self._empty_analysis()
            
            # Extract memory events (mentions of topics/entities)
            memory_events = self._extract_memory_events(conversation_history)
            
            # Model forgetting curves for different memory types
            forgetting_analysis = self._analyze_forgetting_curves(memory_events)
            
            # Analyze retrieval patterns
            retrieval_analysis = self._analyze_retrieval_patterns(memory_events)
            
            # Identify reinforcement opportunities
            reinforcement_opportunities = self._identify_reinforcement_opportunities(
                memory_events, forgetting_analysis
            )
            
            # Predict optimal recall timing
            recall_predictions = self._predict_optimal_recall_timing(
                memory_events, forgetting_analysis
            )
            
            # Store results in strategic_memory_behavior table
            await self._store_analysis(
                user_id=user_id,
                bot_name=bot_name,
                forgetting_analysis=forgetting_analysis,
                retrieval_analysis=retrieval_analysis,
                reinforcement_opportunities=reinforcement_opportunities,
                recall_predictions=recall_predictions
            )
            
            logger.info("✅ Memory behavior analysis complete for user %s", user_id)
            
            return {
                'user_id': user_id,
                'bot_name': bot_name,
                'analysis_timestamp': datetime.now().isoformat(),
                'forgetting_curves': forgetting_analysis,
                'retrieval_patterns': retrieval_analysis,
                'reinforcement_opportunities': reinforcement_opportunities,
                'recall_predictions': recall_predictions,
                'conversation_count': len(conversation_history)
            }
            
        except Exception as e:
            logger.error("Memory behavior analysis failed for user %s: %s", user_id, str(e))
            return self._empty_analysis()
    
    async def _get_conversation_history(
        self,
        user_id: str,
        bot_name: str,
        time_window_days: int
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history from Qdrant."""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
            
            cutoff_timestamp = (datetime.now() - timedelta(days=time_window_days)).timestamp()
            collection_name = f"whisperengine_memory_{bot_name}"
            
            # Query Qdrant for user's conversation history
            search_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="memory_type", match=MatchValue(value="conversation")),
                        FieldCondition(
                            key="timestamp",
                            range=Range(gte=cutoff_timestamp)
                        )
                    ]
                ),
                limit=500,  # Large limit to get full history
                with_payload=True,
                with_vectors=False
            )
            
            # Extract payloads and convert to list
            memories = []
            for point in search_result[0]:  # scroll returns (points, next_page_offset)
                payload = point.payload
                if payload:
                    memories.append(payload)
            
            # Sort chronologically by timestamp
            memories.sort(
                key=lambda x: x.get('timestamp', 0)
            )
            
            logger.debug("Retrieved %d conversation memories", len(memories))
            return memories
            
        except Exception as e:
            logger.error("Failed to retrieve conversation history: %s", str(e))
            return []
    
    def _extract_memory_events(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract memory events (mentions of topics/entities) from conversations.
        
        A memory event represents when a topic or entity is mentioned in conversation.
        Multiple mentions of the same topic = reinforcement events.
        """
        memory_events = []
        topic_mentions: Dict[str, List[datetime]] = {}
        
        for idx, conversation in enumerate(conversation_history):
            timestamp_str = conversation.get('timestamp', '')
            if not timestamp_str:
                continue
            
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            content = conversation.get('content', '')
            
            # Extract potential topics (simplified - in production could use NER)
            # For now, use simple heuristics: nouns, proper nouns, key phrases
            topics = self._extract_topics_from_content(content)
            
            for topic in topics:
                if topic not in topic_mentions:
                    topic_mentions[topic] = []
                topic_mentions[topic].append(timestamp)
                
                memory_events.append({
                    'topic': topic,
                    'timestamp': timestamp,
                    'conversation_index': idx,
                    'is_reinforcement': len(topic_mentions[topic]) > 1,
                    'reinforcement_count': len(topic_mentions[topic]),
                    'time_since_first_mention': (
                        (timestamp - topic_mentions[topic][0]).total_seconds() / 86400
                        if len(topic_mentions[topic]) > 1 else 0
                    )
                })
        
        logger.debug("Extracted %d memory events across %d topics", len(memory_events), len(topic_mentions))
        return memory_events
    
    def _extract_topics_from_content(self, content: str) -> List[str]:
        """
        Extract potential topics from conversation content.
        
        Simplified approach: extract capitalized words/phrases that might be topics.
        In production, this could use NER (Named Entity Recognition) for better accuracy.
        """
        import re
        
        # Extract capitalized words (potential proper nouns/topics)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        
        # Filter out common words and stopwords
        stopwords = {'The', 'This', 'That', 'These', 'Those', 'My', 'Your', 'Our', 
                     'What', 'When', 'Where', 'Why', 'How', 'Who', 'Which'}
        topics = [t for t in capitalized if t not in stopwords]
        
        # Deduplicate while preserving order
        seen = set()
        unique_topics = []
        for topic in topics:
            if topic.lower() not in seen:
                seen.add(topic.lower())
                unique_topics.append(topic)
        
        return unique_topics[:10]  # Limit to top 10 topics per message
    
    def _analyze_forgetting_curves(
        self,
        memory_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze forgetting curves by modeling memory decay patterns.
        
        Uses Ebbinghaus forgetting curve model:
        R(t) = baseline + (1 - baseline) * e^(-decay_rate * t)
        
        Where:
        - R(t) = retention probability at time t (days)
        - baseline = long-term retention floor (0-1)
        - decay_rate = how quickly memory fades (higher = faster decay)
        """
        if not memory_events:
            return self._default_forgetting_analysis()
        
        # Group events by topic
        topic_events: Dict[str, List[Dict[str, Any]]] = {}
        for event in memory_events:
            topic = event['topic']
            if topic not in topic_events:
                topic_events[topic] = []
            topic_events[topic].append(event)
        
        # Analyze decay patterns for topics with multiple mentions
        reinforced_topics = {
            topic: events for topic, events in topic_events.items()
            if len(events) > 1
        }
        
        if not reinforced_topics:
            return self._default_forgetting_analysis()
        
        # Calculate average decay rate from reinforcement intervals
        decay_rates = []
        for topic, events in reinforced_topics.items():
            events_sorted = sorted(events, key=lambda x: x['timestamp'])
            
            # Calculate intervals between mentions
            intervals = []
            for i in range(1, len(events_sorted)):
                interval_days = (
                    events_sorted[i]['timestamp'] - events_sorted[i-1]['timestamp']
                ).total_seconds() / 86400
                intervals.append(interval_days)
            
            if intervals:
                # Shorter intervals suggest stronger retention (slower decay)
                avg_interval = sum(intervals) / len(intervals)
                # Model: longer intervals = higher decay rate
                estimated_decay = max(0.05, min(0.3, 1.0 / (avg_interval + 1)))
                decay_rates.append(estimated_decay)
        
        avg_decay_rate = sum(decay_rates) / len(decay_rates) if decay_rates else self.default_decay_rate
        
        # Estimate retention baseline from long-term reinforcement patterns
        retention_baseline = self._estimate_retention_baseline(reinforced_topics)
        
        return {
            'decay_rate': round(avg_decay_rate, 4),
            'retention_baseline': round(retention_baseline, 4),
            'reinforced_topic_count': len(reinforced_topics),
            'total_topic_count': len(topic_events),
            'model': 'ebbinghaus_exponential',
            'confidence': min(1.0, len(reinforced_topics) / 10.0)  # Higher confidence with more data
        }
    
    def _estimate_retention_baseline(
        self,
        reinforced_topics: Dict[str, List[Dict[str, Any]]]
    ) -> float:
        """
        Estimate long-term retention baseline from reinforcement patterns.
        
        Topics reinforced more frequently have higher baseline retention.
        """
        if not reinforced_topics:
            return self.default_retention_baseline
        
        # Calculate reinforcement density (mentions per day)
        densities = []
        for _topic, events in reinforced_topics.items():
            if len(events) < 2:
                continue
            
            events_sorted = sorted(events, key=lambda x: x['timestamp'])
            time_span = (events_sorted[-1]['timestamp'] - events_sorted[0]['timestamp']).total_seconds() / 86400
            
            if time_span > 0:
                density = len(events) / time_span
                densities.append(density)
        
        if not densities:
            return self.default_retention_baseline
        
        avg_density = sum(densities) / len(densities)
        
        # Higher density = higher baseline retention
        # Map density [0, 1+] to baseline [0.1, 0.4]
        baseline = 0.1 + min(0.3, avg_density * 0.3)
        
        return baseline
    
    def _analyze_retrieval_patterns(
        self,
        memory_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze memory retrieval patterns (when topics are recalled).
        
        Retrieval = when a topic is mentioned again after initial encoding.
        """
        if not memory_events:
            return self._default_retrieval_analysis()
        
        # Group by topic
        topic_events: Dict[str, List[Dict[str, Any]]] = {}
        for event in memory_events:
            topic = event['topic']
            if topic not in topic_events:
                topic_events[topic] = []
            topic_events[topic].append(event)
        
        # Analyze retrieval intervals
        retrieval_intervals = []
        retrieval_success_count = 0
        
        for topic, events in topic_events.items():
            if len(events) < 2:
                continue
            
            events_sorted = sorted(events, key=lambda x: x['timestamp'])
            
            for i in range(1, len(events_sorted)):
                interval_days = (
                    events_sorted[i]['timestamp'] - events_sorted[i-1]['timestamp']
                ).total_seconds() / 86400
                retrieval_intervals.append(interval_days)
                retrieval_success_count += 1
        
        if not retrieval_intervals:
            return self._default_retrieval_analysis()
        
        avg_retrieval_interval = sum(retrieval_intervals) / len(retrieval_intervals)
        min_retrieval_interval = min(retrieval_intervals)
        max_retrieval_interval = max(retrieval_intervals)
        
        # Calculate retrieval probability decay
        # Probability of retrieval decreases with time since last mention
        retrieval_probs = []
        for interval in retrieval_intervals:
            # Model: P(retrieval) = e^(-0.1 * interval_days)
            prob = math.exp(-0.1 * interval)
            retrieval_probs.append(prob)
        
        avg_retrieval_prob = sum(retrieval_probs) / len(retrieval_probs)
        
        return {
            'total_retrievals': retrieval_success_count,
            'avg_interval_days': round(avg_retrieval_interval, 2),
            'min_interval_days': round(min_retrieval_interval, 2),
            'max_interval_days': round(max_retrieval_interval, 2),
            'avg_retrieval_probability': round(avg_retrieval_prob, 4),
            'retrieval_pattern': self._classify_retrieval_pattern(avg_retrieval_interval)
        }
    
    def _classify_retrieval_pattern(self, avg_interval: float) -> str:
        """Classify retrieval pattern based on average interval."""
        if avg_interval < 1.0:
            return 'frequent_active_recall'
        elif avg_interval < 3.0:
            return 'regular_reinforcement'
        elif avg_interval < 7.0:
            return 'weekly_retrieval'
        elif avg_interval < 14.0:
            return 'biweekly_retrieval'
        else:
            return 'infrequent_recall'
    
    def _identify_reinforcement_opportunities(
        self,
        memory_events: List[Dict[str, Any]],
        forgetting_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify opportunities for memory reinforcement.
        
        Opportunities = topics at risk of being forgotten (high decay probability).
        """
        if not memory_events:
            return []
        
        # Group by topic with last mention timestamp
        topic_last_mention: Dict[str, datetime] = {}
        for event in memory_events:
            topic = event['topic']
            if topic not in topic_last_mention or event['timestamp'] > topic_last_mention[topic]:
                topic_last_mention[topic] = event['timestamp']
        
        # Calculate decay probability for each topic
        decay_rate = forgetting_analysis.get('decay_rate', self.default_decay_rate)
        retention_baseline = forgetting_analysis.get('retention_baseline', self.default_retention_baseline)
        
        now = datetime.now()
        opportunities = []
        
        for topic, last_mention in topic_last_mention.items():
            days_since_mention = (now - last_mention).total_seconds() / 86400
            
            # Calculate current retention probability
            retention_prob = retention_baseline + (1 - retention_baseline) * math.exp(-decay_rate * days_since_mention)
            
            # Opportunity = retention falling below threshold (0.5)
            if retention_prob < 0.5:
                opportunities.append({
                    'topic': topic,
                    'last_mentioned_days_ago': round(days_since_mention, 1),
                    'estimated_retention': round(retention_prob, 4),
                    'urgency': 'high' if retention_prob < 0.3 else 'medium',
                    'recommended_action': 'prompt_recall'
                })
        
        # Sort by urgency (lowest retention first)
        opportunities.sort(key=lambda x: x['estimated_retention'])
        
        return opportunities[:10]  # Return top 10 opportunities
    
    def _predict_optimal_recall_timing(
        self,
        memory_events: List[Dict[str, Any]],
        forgetting_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict optimal timing for recalling past topics.
        
        Uses spaced repetition principles: review before forgetting threshold.
        """
        if not memory_events:
            return {
                'next_optimal_recall_days': 3.0,
                'recall_strategy': 'default_spacing',
                'confidence': 0.0
            }
        
        decay_rate = forgetting_analysis.get('decay_rate', self.default_decay_rate)
        retention_baseline = forgetting_analysis.get('retention_baseline', self.default_retention_baseline)
        
        # Calculate when retention drops to 50% threshold
        # Solve: 0.5 = baseline + (1 - baseline) * e^(-decay_rate * t)
        # t = -ln((0.5 - baseline) / (1 - baseline)) / decay_rate
        
        if retention_baseline >= 0.5:
            # Already at or above threshold - recommend longer interval
            optimal_days = 7.0
        else:
            try:
                optimal_days = -math.log((0.5 - retention_baseline) / (1 - retention_baseline)) / decay_rate
                optimal_days = max(1.0, min(14.0, optimal_days))  # Clamp to reasonable range
            except (ValueError, ZeroDivisionError):
                optimal_days = 3.0  # Default fallback
        
        return {
            'next_optimal_recall_days': round(optimal_days, 1),
            'recall_strategy': self._determine_recall_strategy(optimal_days),
            'confidence': forgetting_analysis.get('confidence', 0.5)
        }
    
    def _determine_recall_strategy(self, optimal_days: float) -> str:
        """Determine recall strategy based on optimal interval."""
        if optimal_days < 2.0:
            return 'daily_active_recall'
        elif optimal_days < 4.0:
            return 'short_interval_spacing'
        elif optimal_days < 7.0:
            return 'medium_interval_spacing'
        else:
            return 'long_interval_spacing'
    
    async def _store_analysis(
        self,
        user_id: str,
        bot_name: str,
        forgetting_analysis: Dict[str, Any],
        retrieval_analysis: Dict[str, Any],
        reinforcement_opportunities: List[Dict[str, Any]],
        recall_predictions: Dict[str, Any]
    ) -> None:
        """Store memory behavior analysis in strategic_memory_behavior table."""
        import json
        
        try:
            query = """
                INSERT INTO strategic_memory_behavior (
                    user_id, bot_name, analysis_timestamp,
                    decay_rate, retention_baseline, reinforced_topic_count,
                    total_retrieval_count, avg_retrieval_interval_days,
                    reinforcement_opportunities, optimal_recall_days,
                    recall_strategy, confidence
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11, $12)
                ON CONFLICT (user_id, bot_name)
                DO UPDATE SET
                    analysis_timestamp = EXCLUDED.analysis_timestamp,
                    decay_rate = EXCLUDED.decay_rate,
                    retention_baseline = EXCLUDED.retention_baseline,
                    reinforced_topic_count = EXCLUDED.reinforced_topic_count,
                    total_retrieval_count = EXCLUDED.total_retrieval_count,
                    avg_retrieval_interval_days = EXCLUDED.avg_retrieval_interval_days,
                    reinforcement_opportunities = EXCLUDED.reinforcement_opportunities,
                    optimal_recall_days = EXCLUDED.optimal_recall_days,
                    recall_strategy = EXCLUDED.recall_strategy,
                    confidence = EXCLUDED.confidence
            """
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    user_id,
                    bot_name,
                    datetime.now(),
                    forgetting_analysis.get('decay_rate', self.default_decay_rate),
                    forgetting_analysis.get('retention_baseline', self.default_retention_baseline),
                    forgetting_analysis.get('reinforced_topic_count', 0),
                    retrieval_analysis.get('total_retrievals', 0),
                    retrieval_analysis.get('avg_interval_days', 0.0),
                    json.dumps(reinforcement_opportunities),  # JSONB
                    recall_predictions.get('next_optimal_recall_days', 3.0),
                    recall_predictions.get('recall_strategy', 'default_spacing'),
                    forgetting_analysis.get('confidence', 0.5)
                )
            
            logger.debug("Stored memory behavior analysis for user %s", user_id)
            
        except Exception as e:
            logger.error("Failed to store memory behavior analysis: %s", str(e))
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis when no data available."""
        return {
            'forgetting_curves': self._default_forgetting_analysis(),
            'retrieval_patterns': self._default_retrieval_analysis(),
            'reinforcement_opportunities': [],
            'recall_predictions': {
                'next_optimal_recall_days': 3.0,
                'recall_strategy': 'default_spacing',
                'confidence': 0.0
            },
            'conversation_count': 0
        }
    
    def _default_forgetting_analysis(self) -> Dict[str, Any]:
        """Return default forgetting curve analysis."""
        return {
            'decay_rate': self.default_decay_rate,
            'retention_baseline': self.default_retention_baseline,
            'reinforced_topic_count': 0,
            'total_topic_count': 0,
            'model': 'ebbinghaus_exponential',
            'confidence': 0.0
        }
    
    def _default_retrieval_analysis(self) -> Dict[str, Any]:
        """Return default retrieval pattern analysis."""
        return {
            'total_retrievals': 0,
            'avg_interval_days': 0.0,
            'min_interval_days': 0.0,
            'max_interval_days': 0.0,
            'avg_retrieval_probability': 0.5,
            'retrieval_pattern': 'insufficient_data'
        }
