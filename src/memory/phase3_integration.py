"""
Phase 3 Integration: Multi-Dimensional Memory Networks
=====================================================

Integration layer that coordinates semantic clustering, memory importance,
and pattern detection to create a comprehensive memory network system.

Phase 3: Multi-Dimensional Memory Networks
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Optional, Union
from enum import Enum

from .memory_importance_engine import MemoryImportanceEngine
from .pattern_detector import CrossReferencePatternDetector, DetectedPattern, PatternType

# Semantic clustering now handled by Qdrant vector store natively
# Removed obsolete SemanticMemoryClusterer in favor of VectorMemoryStore.get_memory_clusters_for_roleplay()

logger = logging.getLogger(__name__)


class ClusterType(Enum):
    """Types of memory clusters"""
    TOPICAL = "topical"
    TEMPORAL = "temporal"
    EMOTIONAL = "emotional"
    SEMANTIC = "semantic"


@dataclass
class MemoryNetworkState:
    """Current state of user's memory network"""

    user_id: str
    total_memories: int
    cluster_count: int
    core_memories_count: int
    pattern_count: int
    network_density: float
    last_updated: datetime
    processing_status: str


@dataclass
class MemoryInsight:
    """Insight derived from memory network analysis"""

    insight_type: str
    title: str
    description: str
    confidence: float
    supporting_data: dict[str, Any]
    actionable_suggestions: list[str]
    created_at: datetime


class SemanticClustererStub:
    """Stub for semantic clustering functionality (handled by Qdrant)"""
    
    async def get_clusters_by_type(self, user_id: str, cluster_type: ClusterType):
        """Get clusters by type"""
        return []
    
    async def create_memory_clusters(self, user_id: str, memory_manager):
        """Create memory clusters"""
        return {}
    
    async def update_cluster_relationships(self, user_id: str, memory_manager):
        """Update cluster relationships"""
        pass
    
    def get_clustering_statistics(self, scope: str):
        """Get clustering statistics"""
        return {"total_clusters": 0, "scope": scope}


class Phase3MemoryNetworks:
    """Main integration class for Phase 3 memory network functionality"""

    def __init__(self):
        """Initialize Phase 3 memory networks system"""
        # Semantic clustering now handled natively by Qdrant vector store
        # Use VectorMemoryStore.get_memory_clusters_for_roleplay() instead
        self.importance_engine = MemoryImportanceEngine()
        self.pattern_detector = CrossReferencePatternDetector()
        self.semantic_clusterer = SemanticClustererStub()  # Stub for compatibility

        # Performance limits to prevent excessive processing
        self.max_memories_for_analysis = int(os.getenv("PHASE3_MAX_MEMORIES", "50"))
        self.memory_selection_strategy = os.getenv(
            "PHASE3_MEMORY_STRATEGY", "recent_important"
        )  # recent_important, recent, important
        self.analysis_timeout = int(os.getenv("PHASE3_ANALYSIS_TIMEOUT", "60"))  # seconds

        # Integration state
        self.network_states = {}
        self.processing_queue = {}
        self.insights_cache = {}

        logger.info(
            f"Phase 3 Memory Networks initialized with max_memories={self.max_memories_for_analysis}, strategy={self.memory_selection_strategy}"
        )

    async def analyze_complete_memory_network(self, user_id: str, memory_manager) -> dict[str, Any]:
        """
        Perform comprehensive analysis of user's memory network

        Args:
            user_id: User identifier
            memory_manager: Memory manager instance

        Returns:
            Complete memory network analysis
        """
        logger.info(
            f"Starting complete memory network analysis for user {user_id} (timeout: {self.analysis_timeout}s)"
        )

        try:
            # Run the analysis with timeout protection
            return await asyncio.wait_for(
                self._perform_memory_analysis(user_id, memory_manager),
                timeout=self.analysis_timeout,
            )
        except TimeoutError:
            logger.error(
                f"Memory network analysis timed out after {self.analysis_timeout} seconds for user {user_id}"
            )
            self._update_processing_status(user_id, "timeout")
            return self._create_minimal_analysis_result(user_id)
        except Exception as e:
            logger.error(f"Memory network analysis failed for user {user_id}: {e}")
            self._update_processing_status(user_id, "error")
            return self._create_minimal_analysis_result(user_id)

    async def _perform_memory_analysis(self, user_id: str, memory_manager) -> dict[str, Any]:
        """Internal method to perform the actual memory analysis"""
        try:
            # Update processing status
            self._update_processing_status(user_id, "analyzing")

            # Fetch user data
            memories = await self._fetch_user_memories(user_id, memory_manager)
            conversation_history = await self._fetch_conversation_history(user_id, memory_manager)

            if len(memories) < 2:
                logger.warning(f"Insufficient memories for network analysis: {len(memories)}")
                return self._create_minimal_analysis_result(user_id)

            # Run all analysis components in parallel
            # Note: Semantic clustering now handled by Qdrant vector store natively
            # Use memory_manager.vector_store.get_memory_clusters_for_roleplay() for clustering
                
            importance_task = self._analyze_memory_importance(
                user_id, memories, conversation_history, memory_manager
            )
            pattern_task = self.pattern_detector.detect_memory_patterns(
                user_id, memories, conversation_history
            )

            # Wait for all analysis tasks to complete
            tasks = [importance_task, pattern_task]
                
            results = await asyncio.gather(*tasks)
            
            # Unpack results (no clustering task since Qdrant handles clustering natively)
            importance_results, pattern_results = results
            clustering_results = {"clusters": [], "statistics": {"total_clusters": 0}}

            # Generate cross-component insights
            insights = await self._generate_network_insights(
                user_id, clustering_results, importance_results, pattern_results
            )

            # Create comprehensive result
            analysis_result = {
                "user_id": user_id,
                "analysis_timestamp": datetime.now(UTC),
                "memory_clusters": clustering_results,
                "importance_analysis": importance_results,
                "pattern_detection": pattern_results,
                "network_insights": insights,
                "network_state": self._calculate_network_state(
                    user_id, memories, clustering_results, importance_results, pattern_results
                ),
                "recommendations": await self._generate_recommendations(user_id, insights),
                "performance_metrics": {
                    "total_memories_analyzed": len(memories),
                    "processing_time_seconds": 0,  # Would be calculated
                    "analysis_completeness": self._calculate_analysis_completeness(
                        clustering_results, importance_results, pattern_results
                    ),
                },
            }

            # Cache results
            self._update_processing_status(user_id, "complete")
            self.insights_cache[user_id] = insights

            logger.info(f"Memory network analysis completed for user {user_id}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error in memory network analysis for user {user_id}: {e}")
            self._update_processing_status(user_id, "error")
            return self._create_error_analysis_result(user_id, str(e))

    async def _fetch_user_memories(self, user_id: str, memory_manager) -> list[dict]:
        """Fetch user memories for analysis with intelligent selection"""
        try:
            all_memories = await memory_manager.get_memories_by_user(user_id)
            total_memories = len(all_memories)

            logger.debug(f"Retrieved {total_memories} total memories for user {user_id}")

            # Format memories for consistent processing
            formatted_memories = []
            for memory in all_memories:
                formatted_memory = {
                    "id": memory.get("id", memory.get("memory_id", "")),
                    "memory_id": memory.get("id", memory.get("memory_id", "")),
                    "content": memory.get("content", ""),
                    "topic": memory.get("topic", ""),
                    "emotional_context": memory.get("emotional_context", {}),
                    "timestamp": memory.get("timestamp", datetime.now(UTC)),
                    "importance_score": memory.get("importance_score", 0.5),
                    "metadata": memory.get("metadata", {}),
                }
                formatted_memories.append(formatted_memory)

            # Apply memory selection strategy if we have too many memories
            if len(formatted_memories) > self.max_memories_for_analysis:
                logger.info(
                    f"Limiting memory analysis from {len(formatted_memories)} to {self.max_memories_for_analysis} memories using strategy: {self.memory_selection_strategy}"
                )
                formatted_memories = self._select_memories_for_analysis(formatted_memories)

            logger.debug(f"Using {len(formatted_memories)} memories for Phase 3 analysis")
            return formatted_memories

        except Exception as e:
            logger.error(f"Error fetching user memories: {e}")
            return []

    def _select_memories_for_analysis(self, memories: list[dict]) -> list[dict]:
        """Select most relevant memories for analysis based on strategy"""
        if len(memories) <= self.max_memories_for_analysis:
            return memories

        if self.memory_selection_strategy == "recent":
            # Sort by timestamp (most recent first)
            sorted_memories = sorted(memories, key=lambda m: m["timestamp"], reverse=True)
            return sorted_memories[: self.max_memories_for_analysis]

        elif self.memory_selection_strategy == "important":
            # Sort by importance score (highest first)
            sorted_memories = sorted(memories, key=lambda m: m["importance_score"], reverse=True)
            return sorted_memories[: self.max_memories_for_analysis]

        elif self.memory_selection_strategy == "recent_important":
            # Balanced approach: take top half by importance, then sort by recency
            half_limit = self.max_memories_for_analysis // 2

            # Get most important memories
            by_importance = sorted(memories, key=lambda m: m["importance_score"], reverse=True)
            important_memories = by_importance[:half_limit]

            # Get most recent memories from remaining
            remaining_memories = by_importance[half_limit:]
            by_recency = sorted(remaining_memories, key=lambda m: m["timestamp"], reverse=True)
            recent_memories = by_recency[: self.max_memories_for_analysis - half_limit]

            # Combine and sort by timestamp for final ordering
            selected_memories = important_memories + recent_memories
            return sorted(selected_memories, key=lambda m: m["timestamp"], reverse=True)

        else:
            # Default: most recent
            sorted_memories = sorted(memories, key=lambda m: m["timestamp"], reverse=True)
            return sorted_memories[: self.max_memories_for_analysis]

    async def _fetch_conversation_history(self, user_id: str, memory_manager) -> list[dict]:
        """Fetch conversation history for pattern analysis"""
        try:
            # This would ideally fetch from a conversation history store
            # For now, we'll use memories as a proxy for conversation history
            memories = await self._fetch_user_memories(user_id, memory_manager)

            # Convert memories to conversation-like format
            conversation_history = []
            for memory in memories:
                interaction = {
                    "id": memory["id"],
                    "content": memory["content"],
                    "topic": memory["topic"],
                    "timestamp": memory["timestamp"],
                    "emotional_context": memory["emotional_context"],
                    "user_id": user_id,
                }
                conversation_history.append(interaction)

            # Sort by timestamp
            conversation_history.sort(key=lambda x: x["timestamp"])

            logger.debug(
                f"Prepared {len(conversation_history)} conversation entries for user {user_id}"
            )
            return conversation_history

        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}")
            return []

    async def _analyze_memory_importance(
        self, user_id: str, memories: list[dict], conversation_history: list[dict], memory_manager
    ) -> dict[str, Any]:
        """Analyze importance scores for all memories"""
        logger.debug("Analyzing memory importance scores")

        importance_results = {
            "memory_scores": [],
            "core_memories": [],
            "importance_statistics": {},
            "importance_distribution": {},
        }

        try:
            # Calculate importance for all memories in parallel (batch processing)
            importance_tasks = []
            for memory in memories:
                memory_id = memory["id"]
                task = self.importance_engine.calculate_memory_importance(
                    memory_id, user_id, memory, conversation_history, memory_manager
                )
                importance_tasks.append(task)
            
            # Execute all importance calculations in parallel
            if importance_tasks:
                importance_scores = await asyncio.gather(*importance_tasks)
                importance_results["memory_scores"] = importance_scores
            else:
                importance_results["memory_scores"] = []

            # Identify core memories
            core_memories = await self.importance_engine.identify_core_memories(
                user_id, limit=20, memory_manager=memory_manager
            )
            importance_results["core_memories"] = core_memories

            # Generate statistics
            importance_results["importance_statistics"] = (
                self.importance_engine.get_importance_statistics(user_id)
            )

            # Calculate importance distribution
            scores = [score.overall_score for score in importance_results["memory_scores"]]
            if scores:
                importance_results["importance_distribution"] = {
                    "high_importance": len([s for s in scores if s >= 0.8]),
                    "medium_importance": len([s for s in scores if 0.5 <= s < 0.8]),
                    "low_importance": len([s for s in scores if s < 0.5]),
                    "average_score": sum(scores) / len(scores),
                }

            logger.debug(f"Importance analysis completed for {len(memories)} memories")
            return importance_results

        except Exception as e:
            logger.error(f"Error in importance analysis: {e}")
            return importance_results

    async def _generate_network_insights(
        self,
        user_id: str,
        clustering_results: dict,
        importance_results: dict,
        pattern_results: dict,
    ) -> list[MemoryInsight]:
        """Generate insights by combining results from all analysis components"""
        logger.debug("Generating cross-component network insights")

        insights = []

        try:
            # Insight 1: Cluster-Importance Correlation
            cluster_importance_insight = self._analyze_cluster_importance_correlation(
                clustering_results, importance_results
            )
            if cluster_importance_insight:
                insights.append(cluster_importance_insight)

            # Insight 2: Pattern-Memory Relevance
            pattern_memory_insight = self._analyze_pattern_memory_relevance(
                pattern_results, importance_results
            )
            if pattern_memory_insight:
                insights.append(pattern_memory_insight)

            # Insight 3: Emotional Pattern Clusters
            emotional_insight = self._analyze_emotional_pattern_clusters(
                clustering_results, pattern_results
            )
            if emotional_insight:
                insights.append(emotional_insight)

            # Insight 4: Memory Network Density
            network_density_insight = self._analyze_network_density(
                clustering_results, pattern_results, importance_results
            )
            if network_density_insight:
                insights.append(network_density_insight)

            # Insight 5: Temporal Memory Evolution
            temporal_insight = self._analyze_temporal_memory_evolution(
                clustering_results, pattern_results, importance_results
            )
            if temporal_insight:
                insights.append(temporal_insight)

            logger.debug(f"Generated {len(insights)} network insights")
            return insights

        except Exception as e:
            logger.error(f"Error generating network insights: {e}")
            return []

    def _analyze_cluster_importance_correlation(
        self, clustering_results: dict, importance_results: dict
    ) -> Optional[MemoryInsight]:
        """Analyze correlation between cluster membership and memory importance"""

        try:
            topic_clusters = clustering_results.get("topic_clusters", [])
            memory_scores = importance_results.get("memory_scores", [])

            if not topic_clusters or not memory_scores:
                return None

            # Create memory_id to importance mapping
            importance_map = {score.memory_id: score.overall_score for score in memory_scores}

            # Calculate average importance by cluster
            cluster_importance = []
            for cluster in topic_clusters:
                cluster_scores = [
                    importance_map.get(memory_id, 0.5)
                    for memory_id in cluster.memories
                    if memory_id in importance_map
                ]

                if cluster_scores:
                    avg_importance = sum(cluster_scores) / len(cluster_scores)
                    cluster_importance.append(
                        {
                            "cluster_id": cluster.cluster_id,
                            "cluster_summary": cluster.cluster_summary,
                            "average_importance": avg_importance,
                            "memory_count": len(cluster_scores),
                        }
                    )

            if not cluster_importance:
                return None

            # Find highest importance cluster
            highest_cluster = max(cluster_importance, key=lambda x: x["average_importance"])

            # Calculate overall insight confidence
            confidence = highest_cluster["average_importance"]

            return MemoryInsight(
                insight_type="cluster_importance_correlation",
                title="High-Value Memory Clusters Identified",
                description=f"Cluster '{highest_cluster['cluster_summary']}' contains the most important memories with an average importance of {highest_cluster['average_importance']:.2f}",
                confidence=confidence,
                supporting_data={
                    "highest_importance_cluster": highest_cluster,
                    "all_cluster_importance": cluster_importance,
                },
                actionable_suggestions=[
                    "Focus conversation context on high-importance cluster topics",
                    "Use insights from this cluster for personalized responses",
                    f"Consider the {highest_cluster['memory_count']} memories in this cluster as key reference points",
                ],
                created_at=datetime.now(UTC),
            )

        except Exception as e:
            logger.error(f"Error analyzing cluster-importance correlation: {e}")
            return None

    def _analyze_pattern_memory_relevance(
        self, pattern_results: dict, importance_results: dict
    ) -> Optional[MemoryInsight]:
        """Analyze how detected patterns relate to memory importance"""

        try:
            all_patterns = []
            for _pattern_type, patterns in pattern_results.items():
                if isinstance(patterns, list):
                    all_patterns.extend(patterns)

            core_memories = importance_results.get("core_memories", [])

            if not all_patterns or not core_memories:
                return None

            # Find patterns that involve core memories
            core_memory_ids = [cm["memory"]["id"] for cm in core_memories if "memory" in cm]

            relevant_patterns = []
            for pattern in all_patterns:
                if hasattr(pattern, "related_memories"):
                    overlap = set(pattern.related_memories) & set(core_memory_ids)
                    if overlap:
                        relevant_patterns.append(
                            {
                                "pattern": pattern,
                                "core_memory_overlap": len(overlap),
                                "relevance_score": (
                                    len(overlap) / len(pattern.related_memories)
                                    if pattern.related_memories
                                    else 0
                                ),
                            }
                        )

            if not relevant_patterns:
                return None

            # Find most relevant pattern
            most_relevant = max(relevant_patterns, key=lambda x: x["relevance_score"])
            pattern = most_relevant["pattern"]

            return MemoryInsight(
                insight_type="pattern_memory_relevance",
                title="Core Memory Pattern Detected",
                description=f"Pattern '{pattern.description}' strongly involves core memories ({most_relevant['core_memory_overlap']} core memories affected)",
                confidence=pattern.confidence_score,
                supporting_data={
                    "most_relevant_pattern": {
                        "description": pattern.description,
                        "type": pattern.pattern_type.value,
                        "strength": pattern.pattern_strength.value,
                        "core_memory_overlap": most_relevant["core_memory_overlap"],
                    },
                    "all_relevant_patterns": len(relevant_patterns),
                },
                actionable_suggestions=[
                    f"Consider this {pattern.pattern_type.value} when engaging about related topics",
                    "Use this pattern for predictive conversation guidance",
                    "Monitor for continuation or evolution of this pattern",
                ],
                created_at=datetime.now(UTC),
            )

        except Exception as e:
            logger.error(f"Error analyzing pattern-memory relevance: {e}")
            return None

    def _analyze_emotional_pattern_clusters(
        self, clustering_results: dict, pattern_results: dict
    ) -> Optional[MemoryInsight]:
        """Analyze relationship between emotional clusters and emotional patterns"""

        try:
            emotional_clusters = clustering_results.get("emotional_clusters", [])
            emotional_triggers = pattern_results.get("emotional_triggers", [])

            if not emotional_clusters or not emotional_triggers:
                return None

            # Find strongest emotional pattern
            strongest_trigger = max(emotional_triggers, key=lambda x: x.confidence_score)

            # Find corresponding emotional cluster
            trigger_emotion = strongest_trigger.pattern_metadata.get("triggered_emotion")

            matching_clusters = [
                cluster
                for cluster in emotional_clusters
                if trigger_emotion in cluster.emotional_signature
            ]

            if matching_clusters:
                cluster = matching_clusters[0]

                return MemoryInsight(
                    insight_type="emotional_pattern_clusters",
                    title="Emotional Trigger-Cluster Alignment",
                    description=f"Strong emotional trigger pattern aligns with {trigger_emotion} memory cluster containing {len(cluster.memories)} memories",
                    confidence=strongest_trigger.confidence_score,
                    supporting_data={
                        "trigger_pattern": strongest_trigger.description,
                        "matching_cluster": cluster.cluster_summary,
                        "emotion": trigger_emotion,
                        "memory_count": len(cluster.memories),
                    },
                    actionable_suggestions=[
                        f"Be mindful of {trigger_emotion} triggers in conversation",
                        "Reference positive memories from this emotional cluster for support",
                        "Monitor for early warning signs of this emotional pattern",
                    ],
                    created_at=datetime.now(UTC),
                )

            return None

        except Exception as e:
            logger.error(f"Error analyzing emotional pattern clusters: {e}")
            return None

    def _analyze_network_density(
        self, clustering_results: dict, pattern_results: dict, importance_results: dict
    ) -> Optional[MemoryInsight]:
        """Analyze overall network density and connectivity"""

        try:
            total_memories = importance_results.get("importance_statistics", {}).get(
                "total_memories_scored", 0
            )

            if total_memories == 0:
                return None

            # Count connections from clusters
            cluster_connections = 0
            for cluster_type, clusters in clustering_results.items():
                if cluster_type != "clustering_metadata" and isinstance(clusters, list):
                    for cluster in clusters:
                        if hasattr(cluster, "memories"):
                            cluster_connections += len(cluster.memories)

            # Count connections from patterns
            pattern_connections = 0
            for _pattern_type, patterns in pattern_results.items():
                if isinstance(patterns, list):
                    for pattern in patterns:
                        if hasattr(pattern, "related_memories"):
                            pattern_connections += len(pattern.related_memories)

            # Calculate density score
            total_possible_connections = total_memories * (total_memories - 1) / 2
            actual_connections = cluster_connections + pattern_connections
            density = (
                actual_connections / total_possible_connections
                if total_possible_connections > 0
                else 0
            )

            # Normalize density
            normalized_density = min(density, 1.0)

            if normalized_density > 0.3:  # Significant density
                return MemoryInsight(
                    insight_type="network_density",
                    title="Rich Memory Network Detected",
                    description=f"Memory network shows high connectivity (density: {normalized_density:.2f}) with strong interconnections between memories",
                    confidence=normalized_density,
                    supporting_data={
                        "network_density": normalized_density,
                        "total_memories": total_memories,
                        "cluster_connections": cluster_connections,
                        "pattern_connections": pattern_connections,
                    },
                    actionable_suggestions=[
                        "Leverage rich network for contextual conversation enhancement",
                        "Use network connectivity for better memory retrieval",
                        "Consider network patterns for predictive insights",
                    ],
                    created_at=datetime.now(UTC),
                )

            return None

        except Exception as e:
            logger.error(f"Error analyzing network density: {e}")
            return None

    def _analyze_temporal_memory_evolution(
        self, clustering_results: dict, pattern_results: dict, importance_results: dict
    ) -> Optional[MemoryInsight]:
        """Analyze how memory network has evolved over time"""

        try:
            temporal_clusters = clustering_results.get("temporal_clusters", [])
            preference_evolution = pattern_results.get("preference_evolution", [])

            if not temporal_clusters and not preference_evolution:
                return None

            # Analyze temporal evolution
            evolution_insights = []

            if temporal_clusters:
                # Sort clusters by time
                sorted_clusters = sorted(
                    temporal_clusters, key=lambda c: c.temporal_span.get("start_date", "")
                )

                if len(sorted_clusters) >= 2:
                    recent_cluster = sorted_clusters[-1]
                    evolution_insights.append(
                        f"Recent period shows focus on: {', '.join(recent_cluster.topic_keywords[:3])}"
                    )

            if preference_evolution:
                strongest_evolution = max(preference_evolution, key=lambda x: x.confidence_score)
                evolution_insights.append(
                    f"Preference evolution: {strongest_evolution.description}"
                )

            if evolution_insights:
                return MemoryInsight(
                    insight_type="temporal_memory_evolution",
                    title="Memory Evolution Pattern Detected",
                    description="; ".join(evolution_insights),
                    confidence=0.7,  # Base confidence for temporal analysis
                    supporting_data={
                        "temporal_clusters_count": len(temporal_clusters),
                        "preference_evolutions_count": len(preference_evolution),
                        "evolution_details": evolution_insights,
                    },
                    actionable_suggestions=[
                        "Adapt conversation style to reflect recent preferences",
                        "Acknowledge user's evolving interests",
                        "Use historical context to understand current perspectives",
                    ],
                    created_at=datetime.now(UTC),
                )

            return None

        except Exception as e:
            logger.error(f"Error analyzing temporal memory evolution: {e}")
            return None

    def _calculate_network_state(
        self,
        user_id: str,
        memories: list[dict],
        clustering_results: dict,
        importance_results: dict,
        pattern_results: dict,
    ) -> MemoryNetworkState:
        """Calculate current state of memory network"""

        try:
            # Count clusters
            cluster_count = sum(
                len(cluster_list)
                for key, cluster_list in clustering_results.items()
                if key != "clustering_metadata" and isinstance(cluster_list, list)
            )

            # Count core memories
            core_memories_count = len(importance_results.get("core_memories", []))

            # Count patterns
            pattern_count = sum(
                len(pattern_list)
                for pattern_list in pattern_results.values()
                if isinstance(pattern_list, list)
            )

            # Calculate network density (simplified)
            total_memories = len(memories)
            if total_memories > 0:
                network_density = (cluster_count + pattern_count) / total_memories
            else:
                network_density = 0.0

            return MemoryNetworkState(
                user_id=user_id,
                total_memories=total_memories,
                cluster_count=cluster_count,
                core_memories_count=core_memories_count,
                pattern_count=pattern_count,
                network_density=min(network_density, 1.0),
                last_updated=datetime.now(UTC),
                processing_status="complete",
            )

        except Exception as e:
            logger.error(f"Error calculating network state: {e}")
            return MemoryNetworkState(
                user_id=user_id,
                total_memories=0,
                cluster_count=0,
                core_memories_count=0,
                pattern_count=0,
                network_density=0.0,
                last_updated=datetime.now(UTC),
                processing_status="error",
            )

    async def _generate_recommendations(
        self, user_id: str, insights: list[MemoryInsight]
    ) -> list[dict[str, Any]]:
        """Generate actionable recommendations based on insights"""

        recommendations = []

        try:
            # Group insights by type
            insight_types = {}
            for insight in insights:
                if insight.insight_type not in insight_types:
                    insight_types[insight.insight_type] = []
                insight_types[insight.insight_type].append(insight)

            # Generate recommendations for each insight type
            for insight_type, _type_insights in insight_types.items():
                if insight_type == "cluster_importance_correlation":
                    recommendations.append(
                        {
                            "type": "conversation_enhancement",
                            "priority": "high",
                            "title": "Focus on High-Value Topics",
                            "description": "Prioritize discussion topics from high-importance memory clusters",
                            "implementation": "Use cluster topic keywords for conversation guidance",
                        }
                    )

                elif insight_type == "emotional_pattern_clusters":
                    recommendations.append(
                        {
                            "type": "emotional_support",
                            "priority": "high",
                            "title": "Emotional Pattern Awareness",
                            "description": "Monitor for emotional trigger patterns and provide proactive support",
                            "implementation": "Integrate with emotional intelligence system for early intervention",
                        }
                    )

                elif insight_type == "network_density":
                    recommendations.append(
                        {
                            "type": "memory_utilization",
                            "priority": "medium",
                            "title": "Leverage Rich Memory Network",
                            "description": "Use strong memory interconnections for enhanced context",
                            "implementation": "Implement cross-reference memory retrieval in responses",
                        }
                    )

                elif insight_type == "temporal_memory_evolution":
                    recommendations.append(
                        {
                            "type": "adaptation",
                            "priority": "medium",
                            "title": "Adapt to Evolving Preferences",
                            "description": "Adjust interaction style based on preference evolution patterns",
                            "implementation": "Weight recent preferences higher in conversation planning",
                        }
                    )

            # Add general recommendations
            if len(insights) > 3:
                recommendations.append(
                    {
                        "type": "system_optimization",
                        "priority": "low",
                        "title": "Rich Memory Analysis Available",
                        "description": "Comprehensive memory network provides deep personalization opportunities",
                        "implementation": "Implement advanced memory-based personalization features",
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _calculate_analysis_completeness(
        self, clustering_results: dict, importance_results: dict, pattern_results: dict
    ) -> float:
        """Calculate how complete the analysis is"""

        completeness_factors = []

        # Check clustering completeness
        if clustering_results.get("topic_clusters"):
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)

        # Check importance analysis completeness
        if importance_results.get("memory_scores"):
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)

        # Check pattern detection completeness
        pattern_count = sum(
            len(pattern_list)
            for pattern_list in pattern_results.values()
            if isinstance(pattern_list, list)
        )
        if pattern_count > 0:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)

        return (
            sum(completeness_factors) / len(completeness_factors) if completeness_factors else 0.0
        )

    def _update_processing_status(self, user_id: str, status: str):
        """Update processing status for user"""
        self.processing_queue[user_id] = {"status": status, "timestamp": datetime.now(UTC)}

    def _create_minimal_analysis_result(self, user_id: str) -> dict[str, Any]:
        """Create minimal analysis result for insufficient data"""
        return {
            "user_id": user_id,
            "analysis_timestamp": datetime.now(UTC),
            "memory_clusters": {"clustering_metadata": {"total_memories": 0}},
            "importance_analysis": {"memory_scores": [], "core_memories": []},
            "pattern_detection": {},
            "network_insights": [],
            "network_state": MemoryNetworkState(
                user_id=user_id,
                total_memories=0,
                cluster_count=0,
                core_memories_count=0,
                pattern_count=0,
                network_density=0.0,
                last_updated=datetime.now(UTC),
                processing_status="insufficient_data",
            ),
            "recommendations": [],
            "performance_metrics": {
                "total_memories_analyzed": 0,
                "processing_time_seconds": 0,
                "analysis_completeness": 0.0,
            },
        }

    def _create_error_analysis_result(self, user_id: str, error_message: str) -> dict[str, Any]:
        """Create error analysis result"""
        return {
            "user_id": user_id,
            "analysis_timestamp": datetime.now(UTC),
            "error": error_message,
            "memory_clusters": {},
            "importance_analysis": {},
            "pattern_detection": {},
            "network_insights": [],
            "network_state": MemoryNetworkState(
                user_id=user_id,
                total_memories=0,
                cluster_count=0,
                core_memories_count=0,
                pattern_count=0,
                network_density=0.0,
                last_updated=datetime.now(UTC),
                processing_status="error",
            ),
            "recommendations": [],
            "performance_metrics": {
                "total_memories_analyzed": 0,
                "processing_time_seconds": 0,
                "analysis_completeness": 0.0,
            },
        }

    # Public API methods

    async def get_memory_clusters(
        self, user_id: str, cluster_type: Optional[ClusterType] = None, memory_manager=None
    ) -> list:
        """Get memory clusters for user, optionally filtered by type"""
        if cluster_type:
            return await self.semantic_clusterer.get_clusters_by_type(user_id, cluster_type)
        else:
            clusters = await self.semantic_clusterer.create_memory_clusters(user_id, memory_manager)
            all_clusters = []
            for cluster_list in clusters.values():
                if isinstance(cluster_list, list):
                    all_clusters.extend(cluster_list)
            return all_clusters

    async def get_core_memories(
        self, user_id: str, limit: int = 20, memory_manager=None
    ) -> list[dict]:
        """Get core memories for user"""
        return await self.importance_engine.identify_core_memories(user_id, limit, memory_manager)

    async def get_memory_patterns(
        self, user_id: str, pattern_type: Optional[PatternType] = None
    ) -> list[DetectedPattern]:
        """Get detected patterns for user, optionally filtered by type"""
        user_patterns = self.pattern_detector.detected_patterns.get(user_id, {})

        if pattern_type:
            pattern_key = pattern_type.value.replace("_", "_")
            return user_patterns.get(pattern_key, [])
        else:
            all_patterns = []
            for pattern_list in user_patterns.values():
                if isinstance(pattern_list, list):
                    all_patterns.extend(pattern_list)
            return all_patterns

    async def get_network_insights(self, user_id: str) -> list[MemoryInsight]:
        """Get generated insights for user"""
        return self.insights_cache.get(user_id, [])

    async def get_network_state(self, user_id: str) -> Optional[MemoryNetworkState]:
        """Get current network state for user"""
        return self.network_states.get(user_id)

    async def update_memory_network(self, user_id: str, memory_manager=None):
        """Update memory network analysis when new memories are added"""
        logger.info(f"Updating memory network for user {user_id}")

        try:
            # Update clusters
            await self.semantic_clusterer.update_cluster_relationships(user_id, memory_manager)

            # Update importance scores
            await self.importance_engine.auto_adjust_importance(user_id, memory_manager)

            # Re-run pattern detection
            memories = await self._fetch_user_memories(user_id, memory_manager)
            conversation_history = await self._fetch_conversation_history(user_id, memory_manager)

            if memories:
                await self.pattern_detector.detect_memory_patterns(
                    user_id, memories, conversation_history
                )

            logger.info(f"Memory network updated for user {user_id}")

        except Exception as e:
            logger.error(f"Error updating memory network: {e}")

    def get_system_statistics(self) -> dict[str, Any]:
        """Get overall system statistics"""
        return {
            "total_users_analyzed": len(self.network_states),
            "total_insights_generated": sum(
                len(insights) for insights in self.insights_cache.values()
            ),
            "processing_queue_size": len(self.processing_queue),
            "clustering_statistics": self.semantic_clusterer.get_clustering_statistics("all"),
            "pattern_statistics": {
                user_id: self.pattern_detector.get_pattern_statistics(user_id)
                for user_id in self.pattern_detector.detected_patterns.keys()
            },
            "timestamp": datetime.now(UTC),
        }
