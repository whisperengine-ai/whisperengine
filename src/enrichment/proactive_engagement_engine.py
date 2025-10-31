"""
Proactive Engagement Engine for Strategic Intelligence System.

Identifies opportunities for bot-initiated engagement and follow-ups.
Analyzes:
- Conversation lulls and re-engagement timing
- Unresolved topics and follow-up opportunities
- Milestone celebrations (achievements, anniversaries)
- Check-in opportunities based on user state
- Optimal engagement windows (time/day preferences)

This is a background strategic analysis engine (Phase 3B - Engine 7/7).
Results are cached in PostgreSQL strategic_engagement_opportunities table and retrieved
by hot path in <5ms during Phase 2.8.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncpg
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class ProactiveEngagementEngine:
    """
    Identifies opportunities for bot-initiated proactive engagement.
    
    Key Insights:
    - When to reach out (conversation lulls, optimal timing)
    - What to say (follow-ups, check-ins, celebrations)
    - Why now (user state, milestones, unresolved topics)
    - Engagement probability score (0.0-1.0)
    
    Opportunity Types:
    - conversation_lull: User inactive for extended period
    - topic_follow_up: Unresolved topic from past conversation
    - milestone_celebration: Anniversary, achievement, birthday
    - check_in: Periodic check-in based on relationship depth
    - continuation_prompt: Natural conversation continuation
    """
    
    def __init__(
        self,
        qdrant_client: QdrantClient,
        postgres_pool: asyncpg.Pool,
        lull_threshold_hours: float = 24.0,
        min_engagement_score: float = 0.5
    ):
        self.qdrant_client = qdrant_client
        self.db_pool = postgres_pool
        self.lull_threshold_hours = lull_threshold_hours
        self.min_engagement_score = min_engagement_score
        
        logger.info("✅ ProactiveEngagementEngine initialized")
    
    async def analyze_engagement_opportunities(
        self,
        user_id: str,
        bot_name: str,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze proactive engagement opportunities for a user.
        
        Args:
            user_id: User identifier
            bot_name: Bot name for collection routing
            time_window_days: Analysis window (default 30 days)
        
        Returns:
            Engagement opportunity analysis with recommendations
        """
        try:
            logger.info("💬 Analyzing engagement opportunities for user %s (bot: %s)", user_id, bot_name)
            
            # Retrieve conversation history
            conversation_history = await self._get_conversation_history(
                user_id, bot_name, time_window_days
            )
            
            if not conversation_history:
                logger.warning("No conversation history for user %s", user_id)
                return self._empty_analysis()
            
            # Detect conversation lulls
            lull_analysis = self._analyze_conversation_lulls(conversation_history)
            
            # Identify unresolved topics
            unresolved_topics = self._identify_unresolved_topics(conversation_history)
            
            # Detect milestones
            milestone_opportunities = self._detect_milestones(conversation_history, user_id, bot_name)
            
            # Calculate optimal engagement timing
            optimal_timing = self._calculate_optimal_engagement_timing(conversation_history)
            
            # Generate engagement recommendations
            recommendations = self._generate_engagement_recommendations(
                lull_analysis,
                unresolved_topics,
                milestone_opportunities,
                optimal_timing
            )
            
            # Store results
            await self._store_analysis(
                user_id=user_id,
                bot_name=bot_name,
                lull_analysis=lull_analysis,
                unresolved_topics=unresolved_topics,
                milestone_opportunities=milestone_opportunities,
                optimal_timing=optimal_timing,
                recommendations=recommendations
            )
            
            logger.info("✅ Engagement opportunity analysis complete for user %s", user_id)
            
            return {
                'user_id': user_id,
                'bot_name': bot_name,
                'analysis_timestamp': datetime.now().isoformat(),
                'lull_analysis': lull_analysis,
                'unresolved_topics': unresolved_topics,
                'milestone_opportunities': milestone_opportunities,
                'optimal_timing': optimal_timing,
                'recommendations': recommendations,
                'conversation_count': len(conversation_history)
            }
            
        except Exception as e:
            logger.error("Engagement opportunity analysis failed for user %s: %s", user_id, str(e))
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
    
    def _analyze_conversation_lulls(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze conversation lulls (periods of inactivity).
        
        A lull is a gap where user hasn't engaged for extended period.
        """
        if not conversation_history:
            return self._default_lull_analysis()
        
        # Get last user message timestamp
        user_messages = [c for c in conversation_history if c.get('role') == 'user']
        
        if not user_messages:
            return self._default_lull_analysis()
        
        # Find most recent user message
        last_user_message = user_messages[-1]
        last_timestamp = last_user_message.get('timestamp')
        
        if not last_timestamp:
            return self._default_lull_analysis()
        
        # Calculate time since last message
        try:
            if isinstance(last_timestamp, (int, float)):
                last_dt = datetime.fromtimestamp(last_timestamp)
            else:
                last_dt = datetime.fromisoformat(str(last_timestamp).replace('Z', '+00:00'))
            
            now = datetime.now()
            hours_since_last = (now - last_dt).total_seconds() / 3600
            
            # Determine if in lull state
            is_in_lull = hours_since_last >= self.lull_threshold_hours
            
            # Calculate lull severity
            if hours_since_last < 24:
                severity = 'none'
            elif hours_since_last < 72:
                severity = 'mild'
            elif hours_since_last < 168:  # 1 week
                severity = 'moderate'
            else:
                severity = 'significant'
            
            return {
                'is_in_lull': is_in_lull,
                'hours_since_last_message': round(hours_since_last, 1),
                'lull_severity': severity,
                'last_message_content': last_user_message.get('content', '')[:100],  # First 100 chars
                'recommended_action': 'reach_out' if is_in_lull else 'wait'
            }
            
        except (ValueError, OSError):
            return self._default_lull_analysis()
    
    def _identify_unresolved_topics(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify topics that were mentioned but not fully resolved.
        
        Heuristics:
        - User asked question, bot answered, but no follow-up confirmation
        - Topic mentioned, then conversation shifted without conclusion
        - Future plans discussed but not followed up on
        """
        unresolved = []
        
        # Look for question-answer pairs without follow-up
        for i in range(len(conversation_history) - 2):
            current = conversation_history[i]
            next_msg = conversation_history[i + 1]
            
            if current.get('role') != 'user' or next_msg.get('role') != 'bot':
                continue
            
            user_content = current.get('content', '')
            bot_content = next_msg.get('content', '')
            
            # Check if user asked question
            if not user_content.endswith('?'):
                continue
            
            # Check if there's a follow-up from user
            has_follow_up = False
            if i + 2 < len(conversation_history):
                follow_up = conversation_history[i + 2]
                if follow_up.get('role') == 'user':
                    has_follow_up = True
            
            # If no follow-up, mark as potentially unresolved
            if not has_follow_up:
                unresolved.append({
                    'topic': self._extract_topic_from_question(user_content),
                    'user_question': user_content[:100],
                    'bot_response': bot_content[:100],
                    'timestamp': current.get('timestamp'),
                    'confidence': 0.6,  # Medium confidence (heuristic-based)
                    'follow_up_suggestion': self._generate_follow_up(user_content, bot_content)
                })
        
        # Limit to top 5 most recent unresolved topics
        unresolved = sorted(
            unresolved,
            key=lambda x: x.get('timestamp', 0),
            reverse=True
        )[:5]
        
        return unresolved
    
    def _extract_topic_from_question(self, question: str) -> str:
        """Extract topic from a question (simplified NLP)."""
        # Remove question words
        question_words = ['what', 'when', 'where', 'why', 'how', 'who', 'which', 'is', 'are', 'do', 'does', 'can', 'could', 'would', 'should']
        
        words = question.lower().split()
        topic_words = [w for w in words if w not in question_words and len(w) > 3]
        
        if topic_words:
            return ' '.join(topic_words[:3])  # First 3 significant words
        
        return 'general_topic'
    
    def _generate_follow_up(self, user_question: str, bot_response: str) -> str:
        """Generate a follow-up prompt based on question and response."""
        # Simple template-based follow-up generation
        topic = self._extract_topic_from_question(user_question)
        
        return f"Following up on our discussion about {topic} - how did that work out?"
    
    def _detect_milestones(
        self,
        conversation_history: List[Dict[str, Any]],
        user_id: str,
        bot_name: str
    ) -> List[Dict[str, Any]]:
        """
        Detect potential milestones worth celebrating.
        
        Milestones:
        - Conversation anniversary (X days/weeks since first chat)
        - Achievement mentions (completed, finished, succeeded)
        - Special dates mentioned (birthday, anniversary, etc.)
        """
        milestones = []
        
        if not conversation_history:
            return milestones
        
        # Conversation anniversary
        first_message = conversation_history[0]
        first_timestamp = first_message.get('timestamp')
        
        if first_timestamp:
            try:
                if isinstance(first_timestamp, (int, float)):
                    first_dt = datetime.fromtimestamp(first_timestamp)
                else:
                    first_dt = datetime.fromisoformat(str(first_timestamp).replace('Z', '+00:00'))
                
                now = datetime.now()
                days_since_first = (now - first_dt).days
                
                # Check for week/month milestones
                if days_since_first % 7 == 0 and days_since_first > 0:
                    weeks = days_since_first // 7
                    milestones.append({
                        'type': 'conversation_anniversary',
                        'milestone': f'{weeks}_week{"s" if weeks > 1 else ""}',
                        'message': f"It's been {weeks} week{'s' if weeks > 1 else ''} since we started chatting!",
                        'confidence': 0.9
                    })
                
                if days_since_first % 30 == 0 and days_since_first > 0:
                    months = days_since_first // 30
                    milestones.append({
                        'type': 'conversation_anniversary',
                        'milestone': f'{months}_month{"s" if months > 1 else ""}',
                        'message': f"Happy {months} month{'s' if months > 1 else ''} of conversations!",
                        'confidence': 0.95
                    })
                    
            except (ValueError, OSError):
                pass
        
        # Achievement detection
        achievement_keywords = [
            'completed', 'finished', 'succeeded', 'accomplished', 'achieved',
            'graduated', 'promoted', 'won', 'passed', 'launched'
        ]
        
        for conversation in conversation_history[-10:]:  # Check recent messages
            content = conversation.get('content', '').lower()
            role = conversation.get('role', '')
            
            if role != 'user':
                continue
            
            for keyword in achievement_keywords:
                if keyword in content:
                    milestones.append({
                        'type': 'achievement',
                        'milestone': keyword,
                        'message': f"Congrats on the {keyword.upper()} you mentioned!",
                        'context': content[:100],
                        'confidence': 0.7
                    })
                    break  # One achievement per message
        
        return milestones[:5]  # Top 5 milestones
    
    def _calculate_optimal_engagement_timing(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate optimal timing for proactive engagement.
        
        Based on:
        - User's typical active hours
        - Day of week preferences
        - Response patterns
        """
        if not conversation_history:
            return self._default_timing_analysis()
        
        # Analyze when user is typically active
        hour_activity: Dict[int, int] = {}
        day_activity: Dict[str, int] = {}
        
        user_messages = [c for c in conversation_history if c.get('role') == 'user']
        
        for message in user_messages:
            timestamp = message.get('timestamp')
            
            if not timestamp:
                continue
            
            try:
                if isinstance(timestamp, (int, float)):
                    dt = datetime.fromtimestamp(timestamp)
                else:
                    dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                
                hour_activity[dt.hour] = hour_activity.get(dt.hour, 0) + 1
                day_name = dt.strftime('%A')
                day_activity[day_name] = day_activity.get(day_name, 0) + 1
                
            except (ValueError, OSError):
                continue
        
        # Find optimal hour
        optimal_hour = max(hour_activity.items(), key=lambda x: x[1])[0] if hour_activity else 12
        
        # Find optimal day
        optimal_day = max(day_activity.items(), key=lambda x: x[1])[0] if day_activity else 'Monday'
        
        # Calculate engagement probability by time of day
        total_messages = len(user_messages)
        time_of_day_prob = {}
        for hour, count in hour_activity.items():
            time_of_day_prob[hour] = round(count / total_messages, 3) if total_messages > 0 else 0.0
        
        return {
            'optimal_hour': optimal_hour,
            'optimal_day': optimal_day,
            'hour_activity_distribution': hour_activity,
            'day_activity_distribution': day_activity,
            'engagement_probability_by_hour': time_of_day_prob,
            'recommended_engagement_window': self._format_engagement_window(optimal_hour, optimal_day)
        }
    
    def _format_engagement_window(self, hour: int, day: str) -> str:
        """Format optimal engagement window as human-readable string."""
        time_label = self._hour_to_time_label(hour)
        return f"{day} {time_label} ({hour:02d}:00)"
    
    def _hour_to_time_label(self, hour: int) -> str:
        """Convert hour to time label."""
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 23:
            return 'evening'
        else:
            return 'night'
    
    def _generate_engagement_recommendations(
        self,
        lull_analysis: Dict[str, Any],
        unresolved_topics: List[Dict[str, Any]],
        milestone_opportunities: List[Dict[str, Any]],
        optimal_timing: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized engagement recommendations.
        
        Each recommendation includes:
        - type: Type of engagement
        - message: Suggested message
        - priority: high, medium, low
        - engagement_score: 0.0-1.0 probability of positive response
        - timing: When to send
        """
        recommendations = []
        
        # Priority 1: Milestones (highest engagement)
        for milestone in milestone_opportunities:
            if milestone.get('confidence', 0) >= 0.7:
                recommendations.append({
                    'type': 'milestone_celebration',
                    'message': milestone.get('message', ''),
                    'priority': 'high',
                    'engagement_score': milestone.get('confidence', 0.8),
                    'timing': optimal_timing.get('recommended_engagement_window', 'anytime'),
                    'context': milestone
                })
        
        # Priority 2: Unresolved topics (medium-high engagement)
        for topic in unresolved_topics[:3]:  # Top 3
            if topic.get('confidence', 0) >= self.min_engagement_score:
                recommendations.append({
                    'type': 'topic_follow_up',
                    'message': topic.get('follow_up_suggestion', ''),
                    'priority': 'medium',
                    'engagement_score': topic.get('confidence', 0.6),
                    'timing': optimal_timing.get('recommended_engagement_window', 'anytime'),
                    'context': topic
                })
        
        # Priority 3: Lull re-engagement (medium engagement)
        if lull_analysis.get('is_in_lull'):
            severity = lull_analysis.get('lull_severity', 'mild')
            hours = lull_analysis.get('hours_since_last_message', 0)
            
            if severity in ['moderate', 'significant']:
                recommendations.append({
                    'type': 'lull_reengagement',
                    'message': self._generate_lull_message(hours, severity),
                    'priority': 'medium' if severity == 'moderate' else 'low',
                    'engagement_score': 0.5 if severity == 'moderate' else 0.4,
                    'timing': optimal_timing.get('recommended_engagement_window', 'anytime'),
                    'context': lull_analysis
                })
        
        # Sort by engagement score (descending)
        recommendations.sort(key=lambda x: x['engagement_score'], reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_lull_message(self, hours: float, severity: str) -> str:
        """Generate appropriate message for lull re-engagement."""
        if severity == 'significant':
            return f"It's been {int(hours // 24)} days - hope everything's going well! Just checking in."
        elif severity == 'moderate':
            return f"Haven't heard from you in a few days - how have things been?"
        else:
            return "Hope you're doing well! Feel free to reach out anytime."
    
    async def _store_analysis(
        self,
        user_id: str,
        bot_name: str,
        lull_analysis: Dict[str, Any],
        unresolved_topics: List[Dict[str, Any]],
        milestone_opportunities: List[Dict[str, Any]],
        optimal_timing: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> None:
        """Store engagement opportunity analysis in strategic_engagement_opportunities table."""
        import json
        
        try:
            query = """
                INSERT INTO strategic_engagement_opportunities (
                    user_id, bot_name, analysis_timestamp,
                    is_in_lull, hours_since_last_message, lull_severity,
                    unresolved_topic_count, milestone_count,
                    optimal_engagement_hour, optimal_engagement_day,
                    recommendations
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
                ON CONFLICT (user_id, bot_name)
                DO UPDATE SET
                    analysis_timestamp = EXCLUDED.analysis_timestamp,
                    is_in_lull = EXCLUDED.is_in_lull,
                    hours_since_last_message = EXCLUDED.hours_since_last_message,
                    lull_severity = EXCLUDED.lull_severity,
                    unresolved_topic_count = EXCLUDED.unresolved_topic_count,
                    milestone_count = EXCLUDED.milestone_count,
                    optimal_engagement_hour = EXCLUDED.optimal_engagement_hour,
                    optimal_engagement_day = EXCLUDED.optimal_engagement_day,
                    recommendations = EXCLUDED.recommendations
            """
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    query,
                    user_id,
                    bot_name,
                    datetime.now(),
                    lull_analysis.get('is_in_lull', False),
                    lull_analysis.get('hours_since_last_message', 0.0),
                    lull_analysis.get('lull_severity', 'none'),
                    len(unresolved_topics),
                    len(milestone_opportunities),
                    optimal_timing.get('optimal_hour', 12),
                    optimal_timing.get('optimal_day', 'Monday'),
                    json.dumps(recommendations)
                )
            
            logger.debug("Stored engagement opportunity analysis for user %s", user_id)
            
        except Exception as e:
            logger.error("Failed to store engagement opportunity analysis: %s", str(e))
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis when no data available."""
        return {
            'lull_analysis': self._default_lull_analysis(),
            'unresolved_topics': [],
            'milestone_opportunities': [],
            'optimal_timing': self._default_timing_analysis(),
            'recommendations': [],
            'conversation_count': 0
        }
    
    def _default_lull_analysis(self) -> Dict[str, Any]:
        """Return default lull analysis."""
        return {
            'is_in_lull': False,
            'hours_since_last_message': 0.0,
            'lull_severity': 'none',
            'last_message_content': '',
            'recommended_action': 'wait'
        }
    
    def _default_timing_analysis(self) -> Dict[str, Any]:
        """Return default timing analysis."""
        return {
            'optimal_hour': 12,
            'optimal_day': 'Monday',
            'hour_activity_distribution': {},
            'day_activity_distribution': {},
            'engagement_probability_by_hour': {},
            'recommended_engagement_window': 'anytime'
        }
