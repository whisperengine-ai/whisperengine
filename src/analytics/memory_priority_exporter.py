"""
📊 Memory Priority Metrics Export - Quick Win Feature
Export emotional memory prioritization metrics for analysis
"""
import json
import csv
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MemoryPriorityMetricsExporter:
    """Export memory prioritization metrics for analysis and reporting"""
    
    def __init__(self, memory_manager, emotion_analyzer):
        self.memory_manager = memory_manager
        self.emotion_analyzer = emotion_analyzer
    
    async def export_user_emotional_memory_report(self, user_id: str, format_type: str = "json") -> str:
        """Export comprehensive emotional memory report for a user"""
        try:
            # Gather comprehensive data
            dashboard_data = await self.emotion_analyzer.get_user_emotional_dashboard(user_id)
            all_memories = await self.memory_manager.retrieve_relevant_memories(user_id, "all", limit=100)
            
            # Analyze priority distribution
            priority_analysis = self._analyze_priority_distribution(all_memories)
            emotional_patterns = self._analyze_emotional_patterns(all_memories)
            
            report_data = {
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_memories": len(all_memories),
                    "high_priority_memories": priority_analysis["high_priority_count"],
                    "priority_percentage": priority_analysis["high_priority_percentage"],
                    "dominant_emotion": dashboard_data.get("dominant_emotion", "neutral"),
                    "emotional_confidence": dashboard_data.get("average_confidence", 0.0)
                },
                "priority_distribution": priority_analysis,
                "emotional_patterns": emotional_patterns,
                "recent_emotional_journey": dashboard_data.get("recent_emotions", []),
                "memory_effectiveness": {
                    "context_usage_rate": self._calculate_context_usage_rate(all_memories),
                    "emotional_memory_impact": self._calculate_emotional_impact(all_memories)
                }
            }
            
            if format_type.lower() == "csv":
                return self._export_as_csv(report_data)
            else:
                return json.dumps(report_data, indent=2)
                
        except Exception as e:
            logger.error("Failed to export user emotional memory report: %s", e)
            return json.dumps({"error": str(e)})
    
    async def export_system_priority_metrics(self, timeframe_days: int = 7) -> Dict[str, Any]:
        """Export system-wide memory prioritization metrics"""
        try:
            # This would integrate with existing analytics infrastructure
            # For now, providing structure for what metrics to track
            
            system_metrics = {
                "timeframe": f"last_{timeframe_days}_days",
                "generated_at": datetime.now().isoformat(),
                "system_wide_stats": {
                    "total_users_with_memories": 0,  # Would query from actual data
                    "total_memories_stored": 0,
                    "high_priority_memories_system_wide": 0,
                    "average_emotional_weight": 0.0,
                    "crisis_detection_events": 0,
                    "memory_prioritization_efficiency": 0.0
                },
                "performance_metrics": {
                    "average_retrieval_time_ms": 0.0,
                    "priority_boost_applications": 0,
                    "emotional_context_enhancements": 0,
                    "conversation_momentum_detections": 0
                },
                "trend_analysis": {
                    "emotional_memory_growth_rate": 0.0,
                    "priority_distribution_stability": 0.0,
                    "user_engagement_correlation": 0.0
                }
            }
            
            return system_metrics
            
        except Exception as e:
            logger.error("Failed to export system priority metrics: %s", e)
            return {"error": str(e)}
    
    def _analyze_priority_distribution(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze priority distribution in memory set"""
        if not memories:
            return {"high_priority_count": 0, "high_priority_percentage": 0.0}
        
        high_priority = sum(1 for m in memories if m.get('emotional_weight', 0.5) > 0.7)
        medium_priority = sum(1 for m in memories if 0.4 <= m.get('emotional_weight', 0.5) <= 0.7)
        normal_priority = len(memories) - high_priority - medium_priority
        
        return {
            "high_priority_count": high_priority,
            "medium_priority_count": medium_priority, 
            "normal_priority_count": normal_priority,
            "high_priority_percentage": (high_priority / len(memories)) * 100,
            "priority_distribution": {
                "high": high_priority,
                "medium": medium_priority,
                "normal": normal_priority
            }
        }
    
    def _analyze_emotional_patterns(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze emotional patterns in memories"""
        if not memories:
            return {}
        
        emotions = [m.get('emotional_category', 'neutral') for m in memories if m.get('emotional_category')]
        emotion_weights = [m.get('emotional_weight', 0.5) for m in memories]
        
        from collections import Counter
        emotion_counts = Counter(emotions)
        
        return {
            "most_common_emotions": dict(emotion_counts.most_common(5)),
            "average_emotional_weight": sum(emotion_weights) / len(emotion_weights) if emotion_weights else 0.0,
            "emotional_range": len(set(emotions)),
            "high_intensity_emotions": sum(1 for w in emotion_weights if w > 0.8)
        }
    
    def _calculate_context_usage_rate(self, memories: List[Dict[str, Any]]) -> float:
        """Calculate how often high-priority memories are used in context"""
        # Placeholder - would integrate with actual usage tracking
        return 0.85  # 85% usage rate example
    
    def _calculate_emotional_impact(self, memories: List[Dict[str, Any]]) -> float:
        """Calculate emotional impact score of memory prioritization"""
        if not memories:
            return 0.0
        
        high_priority_memories = [m for m in memories if m.get('emotional_weight', 0) > 0.7]
        return len(high_priority_memories) / len(memories) * 100
    
    def _export_as_csv(self, report_data: Dict[str, Any]) -> str:
        """Convert report data to CSV format"""
        # Simplified CSV export - would expand based on needs
        import io
        output = io.StringIO()
        
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["User ID", report_data["user_id"]])
        writer.writerow(["Total Memories", report_data["summary"]["total_memories"]])
        writer.writerow(["High Priority Memories", report_data["summary"]["high_priority_memories"]])
        writer.writerow(["Priority Percentage", f"{report_data['summary']['priority_percentage']:.1f}%"])
        writer.writerow(["Dominant Emotion", report_data["summary"]["dominant_emotion"]])
        
        return output.getvalue()