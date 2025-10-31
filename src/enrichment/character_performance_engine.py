"""
Character Performance Engine - Strategic Intelligence Engine 2/7

Analyzes bot performance metrics from InfluxDB to identify:
- Response time trends
- Conversation quality patterns
- User engagement metrics
- Bot effectiveness indicators

This engine queries temporal data to provide performance insights that inform
adaptive bot behavior and conversation strategies.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CharacterPerformanceEngine:
    """
    Analyzes character/bot performance metrics from InfluxDB.
    
    Provides insights into:
    - Average response times and trends
    - Conversation quality scores
    - User engagement levels
    - Performance degradation signals
    """
    
    def __init__(self, temporal_client):
        """
        Initialize the Character Performance Engine.
        
        Args:
            temporal_client: TemporalIntelligenceClient for querying InfluxDB
        """
        self.temporal_client = temporal_client
        self.influx_client = temporal_client.client if temporal_client else None
        self.query_api = temporal_client.query_api if temporal_client else None
    
    async def analyze_performance(
        self,
        bot_name: str,
        user_id: str,
        lookback_hours: int = 168  # 7 days default
    ) -> Dict[str, Any]:
        """
        Analyze bot performance for a specific user interaction.
        
        Args:
            bot_name: Name of the bot/character
            user_id: User ID to analyze performance for
            lookback_hours: Hours to look back for performance data
            
        Returns:
            Dict containing performance metrics and insights
        """
        if not self.influx_client:
            logger.warning("No InfluxDB client available for performance analysis")
            return self._empty_performance_result()
        
        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # Query multiple performance metrics in parallel
            metrics = await asyncio.gather(
                self._query_response_times(bot_name, user_id, start_time, end_time),
                self._query_conversation_quality(bot_name, user_id, start_time, end_time),
                self._query_engagement_metrics(bot_name, user_id, start_time, end_time),
                self._query_llm_performance(bot_name, user_id, start_time, end_time),
                return_exceptions=True
            )
            
            # Unpack results with proper type handling
            response_times = metrics[0] if isinstance(metrics[0], dict) else {}
            quality_scores = metrics[1] if isinstance(metrics[1], dict) else {}
            engagement = metrics[2] if isinstance(metrics[2], dict) else {}
            llm_perf = metrics[3] if isinstance(metrics[3], dict) else {}
            
            # Analyze trends and compute insights
            performance_insights = self._compute_performance_insights(
                response_times, quality_scores, engagement, llm_perf
            )
            
            return {
                "bot_name": bot_name,
                "user_id": user_id,
                "lookback_hours": lookback_hours,
                "analyzed_at": end_time.isoformat(),
                "response_times": response_times,
                "conversation_quality": quality_scores,
                "engagement": engagement,
                "llm_performance": llm_perf,
                "insights": performance_insights,
                "overall_health": self._calculate_health_score(performance_insights)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance for {bot_name}/{user_id}: {e}")
            return self._empty_performance_result()
    
    async def _query_response_times(
        self,
        bot_name: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Query response time metrics from InfluxDB."""
        try:
            # Query from vector_memory_performance measurement
            query = f'''
            from(bucket: "performance_metrics")
              |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
              |> filter(fn: (r) => r._measurement == "vector_memory_performance")
              |> filter(fn: (r) => r.bot_name == "{bot_name}")
              |> filter(fn: (r) => r.user_id == "{user_id}")
              |> filter(fn: (r) => r._field == "duration_ms")
              |> filter(fn: (r) => r.operation_type == "message_processing_retrieval")
            '''
            
            result = await self._execute_influx_query(query)
            
            if not result:
                return {"avg_response_time_ms": None, "trend": "unknown", "data_points": 0}
            
            # Calculate statistics
            durations = [r["_value"] for r in result]
            avg_duration = sum(durations) / len(durations)
            
            # Calculate trend (comparing first half vs second half)
            trend = self._calculate_trend(durations)
            
            return {
                "avg_response_time_ms": round(avg_duration, 2),
                "min_response_time_ms": round(min(durations), 2),
                "max_response_time_ms": round(max(durations), 2),
                "trend": trend,
                "data_points": len(durations)
            }
            
        except Exception as e:
            logger.error(f"Error querying response times: {e}")
            return {"avg_response_time_ms": None, "trend": "unknown", "data_points": 0}
    
    async def _query_conversation_quality(
        self,
        bot_name: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Query conversation quality metrics from InfluxDB."""
        try:
            # Query conversation quality scores
            query = f'''
            from(bucket: "performance_metrics")
              |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
              |> filter(fn: (r) => r._measurement == "conversation_quality")
              |> filter(fn: (r) => r.bot_name == "{bot_name}")
              |> filter(fn: (r) => r.user_id == "{user_id}")
              |> filter(fn: (r) => r._field == "engagement_score" or r._field == "coherence_score" or r._field == "satisfaction_score")
            '''
            
            result = await self._execute_influx_query(query)
            
            if not result:
                return {"quality_score": None, "trend": "unknown", "data_points": 0}
            
            # Aggregate quality metrics
            engagement_scores = [r["_value"] for r in result if r.get("_field") == "engagement_score"]
            coherence_scores = [r["_value"] for r in result if r.get("_field") == "coherence_score"]
            satisfaction_scores = [r["_value"] for r in result if r.get("_field") == "satisfaction_score"]
            
            # Calculate composite quality score
            all_scores = engagement_scores + coherence_scores + satisfaction_scores
            avg_quality = sum(all_scores) / len(all_scores) if all_scores else None
            
            return {
                "quality_score": round(avg_quality, 3) if avg_quality else None,
                "engagement_avg": round(sum(engagement_scores) / len(engagement_scores), 3) if engagement_scores else None,
                "coherence_avg": round(sum(coherence_scores) / len(coherence_scores), 3) if coherence_scores else None,
                "satisfaction_avg": round(sum(satisfaction_scores) / len(satisfaction_scores), 3) if satisfaction_scores else None,
                "trend": self._calculate_trend(all_scores) if all_scores else "unknown",
                "data_points": len(all_scores)
            }
            
        except Exception as e:
            logger.error(f"Error querying conversation quality: {e}")
            return {"quality_score": None, "trend": "unknown", "data_points": 0}
    
    async def _query_engagement_metrics(
        self,
        bot_name: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Query user engagement metrics from InfluxDB."""
        try:
            # Query relationship progression (trust, affection)
            query = f'''
            from(bucket: "performance_metrics")
              |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
              |> filter(fn: (r) => r._measurement == "relationship_progression")
              |> filter(fn: (r) => r.bot_name == "{bot_name}")
              |> filter(fn: (r) => r.user_id == "{user_id}")
              |> filter(fn: (r) => r._field == "trust" or r._field == "affection")
            '''
            
            result = await self._execute_influx_query(query)
            
            if not result:
                return {"engagement_level": "unknown", "trust_trend": "unknown", "data_points": 0}
            
            # Extract trust and affection scores
            trust_scores = [r["_value"] for r in result if r.get("_field") == "trust"]
            affection_scores = [r["_value"] for r in result if r.get("_field") == "affection"]
            
            # Calculate engagement level
            avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.5
            avg_affection = sum(affection_scores) / len(affection_scores) if affection_scores else 0.5
            
            engagement_level = self._classify_engagement(avg_trust, avg_affection)
            trust_trend = self._calculate_trend(trust_scores) if trust_scores else "unknown"
            
            return {
                "engagement_level": engagement_level,
                "avg_trust": round(avg_trust, 3),
                "avg_affection": round(avg_affection, 3),
                "trust_trend": trust_trend,
                "data_points": len(result)
            }
            
        except Exception as e:
            logger.error(f"Error querying engagement metrics: {e}")
            return {"engagement_level": "unknown", "trust_trend": "unknown", "data_points": 0}
    
    async def _query_llm_performance(
        self,
        bot_name: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Query LLM performance metrics from InfluxDB."""
        try:
            # Query LLM response times
            query = f'''
            from(bucket: "performance_metrics")
              |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
              |> filter(fn: (r) => r._measurement == "temporal_metrics")
              |> filter(fn: (r) => r.bot_name == "{bot_name}")
              |> filter(fn: (r) => r.user_id == "{user_id}")
              |> filter(fn: (r) => r._field == "llm_time_ms")
            '''
            
            result = await self._execute_influx_query(query)
            
            if not result:
                return {"avg_llm_time_ms": None, "trend": "unknown", "data_points": 0}
            
            # Calculate LLM performance statistics
            llm_times = [r["_value"] for r in result]
            avg_llm_time = sum(llm_times) / len(llm_times)
            
            return {
                "avg_llm_time_ms": round(avg_llm_time, 2),
                "min_llm_time_ms": round(min(llm_times), 2),
                "max_llm_time_ms": round(max(llm_times), 2),
                "trend": self._calculate_trend(llm_times),
                "data_points": len(llm_times)
            }
            
        except Exception as e:
            logger.error(f"Error querying LLM performance: {e}")
            return {"avg_llm_time_ms": None, "trend": "unknown", "data_points": 0}
    
    async def _execute_influx_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute InfluxDB query and return results."""
        try:
            # Note: Actual implementation depends on influxdb-client library
            # This is a placeholder that needs to be adapted to your InfluxDB client
            
            # For now, return empty list (will be implemented when testing)
            logger.debug(f"Would execute InfluxDB query: {query[:100]}...")
            return []
            
        except Exception as e:
            logger.error(f"Error executing InfluxDB query: {e}")
            return []
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend from a series of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            "improving", "declining", or "stable"
        """
        if not values or len(values) < 2:
            return "unknown"
        
        # Split into first half and second half
        mid_point = len(values) // 2
        first_half = values[:mid_point]
        second_half = values[mid_point:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        # Calculate percentage change
        if first_avg == 0:
            return "stable"
        
        change_pct = ((second_avg - first_avg) / first_avg) * 100
        
        if change_pct > 10:
            return "improving"
        elif change_pct < -10:
            return "declining"
        else:
            return "stable"
    
    def _classify_engagement(self, trust: float, affection: float) -> str:
        """
        Classify engagement level based on trust and affection scores.
        
        Args:
            trust: Trust score (0-1)
            affection: Affection score (0-1)
            
        Returns:
            Engagement level: "high", "medium", "low", "new"
        """
        avg_score = (trust + affection) / 2
        
        if avg_score >= 0.7:
            return "high"
        elif avg_score >= 0.5:
            return "medium"
        elif avg_score >= 0.3:
            return "low"
        else:
            return "new"
    
    def _compute_performance_insights(
        self,
        response_times: Dict[str, Any],
        quality_scores: Dict[str, Any],
        engagement: Dict[str, Any],
        llm_perf: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute actionable insights from performance metrics.
        
        Args:
            response_times: Response time metrics
            quality_scores: Conversation quality metrics
            engagement: Engagement metrics
            llm_perf: LLM performance metrics
            
        Returns:
            Dict of insights and recommendations
        """
        insights = {
            "performance_issues": [],
            "positive_signals": [],
            "recommendations": []
        }
        
        # Check response time issues
        if response_times.get("avg_response_time_ms"):
            if response_times["avg_response_time_ms"] > 5000:
                insights["performance_issues"].append("High average response time")
                insights["recommendations"].append("Consider optimizing vector retrieval")
            elif response_times["trend"] == "declining":
                insights["performance_issues"].append("Response time degrading")
                insights["recommendations"].append("Monitor memory system performance")
            else:
                insights["positive_signals"].append("Response times within acceptable range")
        
        # Check conversation quality
        if quality_scores.get("quality_score"):
            if quality_scores["quality_score"] < 0.5:
                insights["performance_issues"].append("Low conversation quality")
                insights["recommendations"].append("Review conversation context and memory relevance")
            elif quality_scores["trend"] == "declining":
                insights["performance_issues"].append("Conversation quality declining")
                insights["recommendations"].append("Increase context awareness and memory depth")
            else:
                insights["positive_signals"].append("Good conversation quality maintained")
        
        # Check engagement
        engagement_level = engagement.get("engagement_level", "unknown")
        if engagement_level == "low":
            insights["performance_issues"].append("Low user engagement")
            insights["recommendations"].append("Consider proactive engagement strategies")
        elif engagement_level in ["high", "medium"]:
            insights["positive_signals"].append(f"User engagement is {engagement_level}")
        
        # Check LLM performance
        if llm_perf.get("avg_llm_time_ms"):
            if llm_perf["avg_llm_time_ms"] > 10000:
                insights["performance_issues"].append("Slow LLM response times")
                insights["recommendations"].append("Consider model optimization or caching")
            elif llm_perf["trend"] == "improving":
                insights["positive_signals"].append("LLM performance improving")
        
        return insights
    
    def _calculate_health_score(self, insights: Dict[str, Any]) -> str:
        """
        Calculate overall health score based on insights.
        
        Args:
            insights: Performance insights dict
            
        Returns:
            Health score: "excellent", "good", "fair", "poor"
        """
        issue_count = len(insights.get("performance_issues", []))
        positive_count = len(insights.get("positive_signals", []))
        
        if issue_count == 0 and positive_count >= 2:
            return "excellent"
        elif issue_count <= 1 and positive_count >= 1:
            return "good"
        elif issue_count <= 2:
            return "fair"
        else:
            return "poor"
    
    def _empty_performance_result(self) -> Dict[str, Any]:
        """Return empty performance result structure."""
        return {
            "bot_name": None,
            "user_id": None,
            "lookback_hours": 0,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "response_times": {},
            "conversation_quality": {},
            "engagement": {},
            "llm_performance": {},
            "insights": {
                "performance_issues": [],
                "positive_signals": [],
                "recommendations": []
            },
            "overall_health": "unknown"
        }
