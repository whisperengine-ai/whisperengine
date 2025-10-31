"""
Conversation Pattern Engine for Strategic Intelligence System.

Extracts recurring conversation patterns and user behavior cycles from history.
Analyzes:
- Common question types and recurring topics
- Conversation initiation patterns (time of day, day of week)
- Response length preferences
- Interaction rituals and habits
- Conversational style evolution

This is a background strategic analysis engine (Phase 3B - Engine 6/7).
Results are cached in PostgreSQL strategic_conversation_patterns table and retrieved
by hot path in <5ms during Phase 2.8.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import Counter
import asyncpg
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class ConversationPatternEngine:
    """
    Analyzes recurring conversation patterns and user behavior cycles.
    
    Key Insights:
    - Most common question types (what, how, why, when, etc.)
    - Preferred interaction times (morning, afternoon, evening, night)
    - Average message length and complexity
    - Conversation starters and rituals
    - Topic preferences and recurring themes
    """
    
    def __init__(
        self,
        qdrant_client: QdrantClient,
        postgres_pool: asyncpg.Pool
    ):
        self.qdrant_client = qdrant_client
        self.db_pool = postgres_pool
        
        logger.info("✅ ConversationPatternEngine initialized")
    
    async def analyze_conversation_patterns(
        self,
        user_id: str,
        bot_name: str,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze conversation patterns for a user.
        
        Args:
            user_id: User identifier
            bot_name: Bot name for collection routing
            time_window_days: Analysis window (default 30 days)
        
        Returns:
            Conversation pattern analysis with behavioral insights
        """
        try:
            logger.info("🗣️ Analyzing conversation patterns for user %s (bot: %s)", user_id, bot_name)
            
            # Retrieve conversation history
            conversation_history = await self._get_conversation_history(
                user_id, bot_name, time_window_days
            )
            
            if not conversation_history:
                logger.warning("No conversation history for user %s", user_id)
                return self._empty_analysis()
            
            # Extract patterns
            question_patterns = self._analyze_question_types(conversation_history)
            temporal_patterns = self._analyze_temporal_patterns(conversation_history)
            length_patterns = self._analyze_message_lengths(conversation_history)
            initiation_patterns = self._analyze_conversation_initiation(conversation_history)
            topic_patterns = self._extract_topic_patterns(conversation_history)
            style_evolution = self._analyze_style_evolution(conversation_history)
            
            # Store results
            await self._store_analysis(
                user_id=user_id,
                bot_name=bot_name,
                question_patterns=question_patterns,
                temporal_patterns=temporal_patterns,
                length_patterns=length_patterns,
                initiation_patterns=initiation_patterns,
                topic_patterns=topic_patterns,
                style_evolution=style_evolution
            )
            
            logger.info("✅ Conversation pattern analysis complete for user %s", user_id)
            
            return {
                'user_id': user_id,
                'bot_name': bot_name,
                'analysis_timestamp': datetime.now().isoformat(),
                'question_patterns': question_patterns,
                'temporal_patterns': temporal_patterns,
                'length_patterns': length_patterns,
                'initiation_patterns': initiation_patterns,
                'topic_patterns': topic_patterns,
                'style_evolution': style_evolution,
                'conversation_count': len(conversation_history)
            }
            
        except Exception as e:
            logger.error("Conversation pattern analysis failed for user %s: %s", user_id, str(e))
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
                limit=500,
                with_payload=True,
                with_vectors=False
            )
            
            # Extract payloads
            memories = []
            for point in search_result[0]:
                payload = point.payload
                if payload:
                    memories.append(payload)
            
            # Sort chronologically
            memories.sort(key=lambda x: x.get('timestamp', 0))
            
            logger.debug("Retrieved %d conversation memories", len(memories))
            return memories
            
        except Exception as e:
            logger.error("Failed to retrieve conversation history: %s", str(e))
            return []
    
    def _analyze_question_types(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze types of questions user asks.
        
        Categorizes questions by:
        - Information seeking (what, when, where)
        - Reasoning (why, how)
        - Confirmation (is, are, can, do)
        - Other
        """
        question_types = Counter()
        total_messages = 0
        total_questions = 0
        
        for conversation in conversation_history:
            content = conversation.get('content', '').strip()
            role = conversation.get('role', '')
            
            # Only analyze user messages
            if role != 'user':
                continue
            
            total_messages += 1
            
            if not content.endswith('?'):
                continue
            
            total_questions += 1
            content_lower = content.lower()
            
            # Categorize by question word
            if any(word in content_lower for word in ['what', 'which']):
                question_types['information_seeking'] += 1
            elif any(word in content_lower for word in ['why', 'how']):
                question_types['reasoning'] += 1
            elif any(word in content_lower for word in ['is', 'are', 'can', 'do', 'does', 'will', 'would', 'could', 'should']):
                question_types['confirmation'] += 1
            elif 'when' in content_lower:
                question_types['temporal'] += 1
            elif 'where' in content_lower:
                question_types['location'] += 1
            else:
                question_types['other'] += 1
        
        # Calculate percentages
        question_distribution = {}
        if total_questions > 0:
            for q_type, count in question_types.items():
                question_distribution[q_type] = {
                    'count': count,
                    'percentage': round((count / total_questions) * 100, 1)
                }
        
        return {
            'total_questions': total_questions,
            'total_messages': total_messages,
            'question_frequency': round(total_questions / max(1, total_messages), 3),
            'question_distribution': question_distribution,
            'most_common_type': question_types.most_common(1)[0][0] if question_types else 'none'
        }
    
    def _analyze_temporal_patterns(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze when user typically interacts (time of day, day of week).
        """
        hour_distribution = Counter()
        day_of_week_distribution = Counter()
        
        for conversation in conversation_history:
            timestamp = conversation.get('timestamp')
            role = conversation.get('role', '')
            
            # Only analyze user messages
            if role != 'user' or not timestamp:
                continue
            
            try:
                if isinstance(timestamp, (int, float)):
                    dt = datetime.fromtimestamp(timestamp)
                else:
                    dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                
                hour_distribution[dt.hour] += 1
                day_of_week_distribution[dt.strftime('%A')] += 1
                
            except (ValueError, OSError):
                continue
        
        # Classify time of day preferences
        morning = sum(hour_distribution[h] for h in range(6, 12))
        afternoon = sum(hour_distribution[h] for h in range(12, 18))
        evening = sum(hour_distribution[h] for h in range(18, 23))
        night = sum(hour_distribution[h] for h in range(0, 6)) + hour_distribution.get(23, 0)
        
        total = morning + afternoon + evening + night
        time_of_day_dist = {}
        if total > 0:
            time_of_day_dist = {
                'morning': {'count': morning, 'percentage': round((morning / total) * 100, 1)},
                'afternoon': {'count': afternoon, 'percentage': round((afternoon / total) * 100, 1)},
                'evening': {'count': evening, 'percentage': round((evening / total) * 100, 1)},
                'night': {'count': night, 'percentage': round((night / total) * 100, 1)}
            }
        
        # Most active time
        most_active_time = max(
            [('morning', morning), ('afternoon', afternoon), ('evening', evening), ('night', night)],
            key=lambda x: x[1]
        )[0] if total > 0 else 'unknown'
        
        # Day of week preferences
        day_distribution = {}
        total_days = sum(day_of_week_distribution.values())
        if total_days > 0:
            for day, count in day_of_week_distribution.items():
                day_distribution[day] = {
                    'count': count,
                    'percentage': round((count / total_days) * 100, 1)
                }
        
        most_active_day = day_of_week_distribution.most_common(1)[0][0] if day_of_week_distribution else 'unknown'
        
        return {
            'time_of_day_distribution': time_of_day_dist,
            'most_active_time': most_active_time,
            'day_of_week_distribution': day_distribution,
            'most_active_day': most_active_day,
            'total_interactions': total
        }
    
    def _analyze_message_lengths(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze user's message length preferences.
        """
        user_message_lengths = []
        
        for conversation in conversation_history:
            content = conversation.get('content', '')
            role = conversation.get('role', '')
            
            if role != 'user':
                continue
            
            word_count = len(content.split())
            char_count = len(content)
            
            user_message_lengths.append({
                'word_count': word_count,
                'char_count': char_count
            })
        
        if not user_message_lengths:
            return self._default_length_patterns()
        
        avg_word_count = sum(m['word_count'] for m in user_message_lengths) / len(user_message_lengths)
        avg_char_count = sum(m['char_count'] for m in user_message_lengths) / len(user_message_lengths)
        
        # Classify message style
        if avg_word_count < 10:
            message_style = 'concise'
        elif avg_word_count < 30:
            message_style = 'moderate'
        elif avg_word_count < 60:
            message_style = 'detailed'
        else:
            message_style = 'elaborate'
        
        return {
            'avg_word_count': round(avg_word_count, 1),
            'avg_char_count': round(avg_char_count, 1),
            'message_style': message_style,
            'total_messages_analyzed': len(user_message_lengths)
        }
    
    def _analyze_conversation_initiation(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze how user typically starts conversations.
        """
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy', "what's up", 'sup']
        questions_starters = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'do', 'does', 'is', 'are']
        
        greeting_count = 0
        question_start_count = 0
        direct_statement_count = 0
        total_initiations = 0
        
        # Identify conversation initiations (simplified: first message after 1+ hour gap)
        previous_timestamp = None
        
        for conversation in conversation_history:
            content = conversation.get('content', '').strip().lower()
            role = conversation.get('role', '')
            timestamp = conversation.get('timestamp')
            
            if role != 'user' or not timestamp:
                continue
            
            try:
                if isinstance(timestamp, (int, float)):
                    dt = datetime.fromtimestamp(timestamp)
                else:
                    dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                
                # Check if this is a conversation initiation (1+ hour gap or first message)
                is_initiation = False
                if previous_timestamp is None:
                    is_initiation = True
                else:
                    time_diff = (dt - previous_timestamp).total_seconds() / 3600  # hours
                    if time_diff >= 1.0:
                        is_initiation = True
                
                previous_timestamp = dt
                
                if not is_initiation:
                    continue
                
                total_initiations += 1
                
                # Categorize initiation type
                if any(greeting in content for greeting in greetings):
                    greeting_count += 1
                elif any(content.startswith(starter) for starter in questions_starters):
                    question_start_count += 1
                else:
                    direct_statement_count += 1
                    
            except (ValueError, OSError):
                continue
        
        if total_initiations == 0:
            return self._default_initiation_patterns()
        
        return {
            'total_initiations': total_initiations,
            'greeting_percentage': round((greeting_count / total_initiations) * 100, 1),
            'question_start_percentage': round((question_start_count / total_initiations) * 100, 1),
            'direct_statement_percentage': round((direct_statement_count / total_initiations) * 100, 1),
            'preferred_initiation': self._determine_preferred_initiation(
                greeting_count, question_start_count, direct_statement_count
            )
        }
    
    def _determine_preferred_initiation(
        self,
        greeting_count: int,
        question_count: int,
        statement_count: int
    ) -> str:
        """Determine most common initiation style."""
        max_count = max(greeting_count, question_count, statement_count)
        
        if max_count == 0:
            return 'varied'
        
        if greeting_count == max_count:
            return 'greeting'
        elif question_count == max_count:
            return 'question'
        else:
            return 'direct_statement'
    
    def _extract_topic_patterns(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract recurring topics and themes.
        
        Uses simple keyword frequency analysis (in production, could use NER/topic modeling).
        """
        word_frequency: Counter = Counter()
        bigram_frequency: Counter = Counter()
        
        # Common stopwords to filter out
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'me', 'him', 'us', 'them', 'my',
            'your', 'his', 'its', 'our', 'their', 'this', 'that', 'these',
            'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
        }
        
        for conversation in conversation_history:
            content = conversation.get('content', '').lower()
            role = conversation.get('role', '')
            
            if role != 'user':
                continue
            
            # Extract words (alphanumeric only)
            import re
            words = re.findall(r'\b[a-z]{3,}\b', content)  # 3+ char words
            
            # Filter stopwords
            filtered_words = [w for w in words if w not in stopwords]
            
            # Count words
            word_frequency.update(filtered_words)
            
            # Count bigrams
            for i in range(len(filtered_words) - 1):
                bigram = f"{filtered_words[i]} {filtered_words[i+1]}"
                bigram_frequency[bigram] += 1
        
        # Top topics (single words)
        top_words = word_frequency.most_common(10)
        
        # Top phrases (bigrams)
        top_phrases = bigram_frequency.most_common(10)
        
        return {
            'top_keywords': [
                {'word': word, 'frequency': count}
                for word, count in top_words
            ],
            'top_phrases': [
                {'phrase': phrase, 'frequency': count}
                for phrase, count in top_phrases
            ],
            'unique_word_count': len(word_frequency),
            'total_words_analyzed': sum(word_frequency.values())
        }
    
    def _analyze_style_evolution(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze how user's conversation style evolves over time.
        
        Tracks changes in:
        - Message length
        - Question frequency
        - Formality (punctuation, capitalization)
        """
        if len(conversation_history) < 10:
            return {'evolution_detected': False, 'reason': 'insufficient_data'}
        
        # Split into early vs recent conversations
        midpoint = len(conversation_history) // 2
        early_conversations = conversation_history[:midpoint]
        recent_conversations = conversation_history[midpoint:]
        
        # Analyze each period
        early_stats = self._compute_period_stats(early_conversations)
        recent_stats = self._compute_period_stats(recent_conversations)
        
        # Compare periods
        length_change = recent_stats['avg_length'] - early_stats['avg_length']
        question_change = recent_stats['question_freq'] - early_stats['question_freq']
        formality_change = recent_stats['formality_score'] - early_stats['formality_score']
        
        return {
            'evolution_detected': True,
            'early_period': early_stats,
            'recent_period': recent_stats,
            'changes': {
                'message_length': {
                    'direction': 'increased' if length_change > 5 else ('decreased' if length_change < -5 else 'stable'),
                    'magnitude': round(abs(length_change), 1)
                },
                'question_frequency': {
                    'direction': 'increased' if question_change > 0.1 else ('decreased' if question_change < -0.1 else 'stable'),
                    'magnitude': round(abs(question_change), 3)
                },
                'formality': {
                    'direction': 'increased' if formality_change > 0.1 else ('decreased' if formality_change < -0.1 else 'stable'),
                    'magnitude': round(abs(formality_change), 3)
                }
            }
        }
    
    def _compute_period_stats(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute statistics for a conversation period."""
        user_messages = [c for c in conversations if c.get('role') == 'user']
        
        if not user_messages:
            return {'avg_length': 0.0, 'question_freq': 0.0, 'formality_score': 0.0}
        
        total_words = 0
        question_count = 0
        proper_punctuation_count = 0
        proper_capitalization_count = 0
        
        for msg in user_messages:
            content = msg.get('content', '')
            
            # Length
            total_words += len(content.split())
            
            # Questions
            if content.endswith('?'):
                question_count += 1
            
            # Formality indicators
            if content.endswith(('.', '!', '?')):
                proper_punctuation_count += 1
            
            if content and content[0].isupper():
                proper_capitalization_count += 1
        
        avg_length = total_words / len(user_messages)
        question_freq = question_count / len(user_messages)
        formality_score = (proper_punctuation_count + proper_capitalization_count) / (len(user_messages) * 2)
        
        return {
            'avg_length': round(avg_length, 1),
            'question_freq': round(question_freq, 3),
            'formality_score': round(formality_score, 3),
            'message_count': len(user_messages)
        }
    
    async def _store_analysis(
        self,
        user_id: str,
        bot_name: str,
        question_patterns: Dict[str, Any],
        temporal_patterns: Dict[str, Any],
        length_patterns: Dict[str, Any],
        initiation_patterns: Dict[str, Any],
        topic_patterns: Dict[str, Any],
        style_evolution: Dict[str, Any]
    ) -> None:
        """Store conversation pattern analysis in strategic_conversation_patterns table."""
        import json
        
        try:
            query = """
                INSERT INTO strategic_conversation_patterns (
                    user_id, bot_name, analysis_timestamp,
                    question_patterns, temporal_patterns, length_patterns,
                    initiation_patterns, topic_patterns, style_evolution
                )
                VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7::jsonb, $8::jsonb, $9::jsonb)
                ON CONFLICT (user_id, bot_name)
                DO UPDATE SET
                    analysis_timestamp = EXCLUDED.analysis_timestamp,
                    question_patterns = EXCLUDED.question_patterns,
                    temporal_patterns = EXCLUDED.temporal_patterns,
                    length_patterns = EXCLUDED.length_patterns,
                    initiation_patterns = EXCLUDED.initiation_patterns,
                    topic_patterns = EXCLUDED.topic_patterns,
                    style_evolution = EXCLUDED.style_evolution
            """
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    user_id,
                    bot_name,
                    datetime.now(),
                    json.dumps(question_patterns),
                    json.dumps(temporal_patterns),
                    json.dumps(length_patterns),
                    json.dumps(initiation_patterns),
                    json.dumps(topic_patterns),
                    json.dumps(style_evolution)
                )
            
            logger.debug("Stored conversation pattern analysis for user %s", user_id)
            
        except Exception as e:
            logger.error("Failed to store conversation pattern analysis: %s", str(e))
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis when no data available."""
        return {
            'question_patterns': self._default_question_patterns(),
            'temporal_patterns': self._default_temporal_patterns(),
            'length_patterns': self._default_length_patterns(),
            'initiation_patterns': self._default_initiation_patterns(),
            'topic_patterns': {'top_keywords': [], 'top_phrases': [], 'unique_word_count': 0, 'total_words_analyzed': 0},
            'style_evolution': {'evolution_detected': False, 'reason': 'no_data'},
            'conversation_count': 0
        }
    
    def _default_question_patterns(self) -> Dict[str, Any]:
        """Return default question pattern analysis."""
        return {
            'total_questions': 0,
            'total_messages': 0,
            'question_frequency': 0.0,
            'question_distribution': {},
            'most_common_type': 'none'
        }
    
    def _default_temporal_patterns(self) -> Dict[str, Any]:
        """Return default temporal pattern analysis."""
        return {
            'time_of_day_distribution': {},
            'most_active_time': 'unknown',
            'day_of_week_distribution': {},
            'most_active_day': 'unknown',
            'total_interactions': 0
        }
    
    def _default_length_patterns(self) -> Dict[str, Any]:
        """Return default message length analysis."""
        return {
            'avg_word_count': 0.0,
            'avg_char_count': 0.0,
            'message_style': 'unknown',
            'total_messages_analyzed': 0
        }
    
    def _default_initiation_patterns(self) -> Dict[str, Any]:
        """Return default initiation pattern analysis."""
        return {
            'total_initiations': 0,
            'greeting_percentage': 0.0,
            'question_start_percentage': 0.0,
            'direct_statement_percentage': 0.0,
            'preferred_initiation': 'unknown'
        }
