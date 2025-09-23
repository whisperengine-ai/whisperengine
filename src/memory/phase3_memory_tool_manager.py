"""
Phase 3 LLM Tool Manager: Multi-Dimensional Memory Networks
===========================================================

Provides LLM-callable tools for advanced memory network analysis, pattern detection,
and memory importance evaluation. Enables the AI to proactively analyze and leverage
complex memory relationships for enhanced conversation intelligence.

Phase 3 Tools:
- Memory Network Analysis
- Pattern Detection & Cross-referencing  
- Memory Importance Evaluation
- Semantic Memory Clustering
- Memory Insights Generation
- Network Relationship Discovery
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict
import json

from .phase3_integration import Phase3MemoryNetworks, MemoryNetworkState, MemoryInsight

logger = logging.getLogger(__name__)


class Phase3MemoryToolManager:
    """LLM Tool Manager for Phase 3 Multi-Dimensional Memory Networks"""
    
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.phase3_networks = Phase3MemoryNetworks()
        
        # Define tools available to LLM
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_memory_network",
                    "description": "Perform comprehensive analysis of user's complete memory network including clustering, importance, and pattern detection. Use when you need deep insights about user's conversation patterns, preferences, and relationship history.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string", 
                                "description": "User ID to analyze memory network for"
                            },
                            "focus_area": {
                                "type": "string",
                                "description": "Optional focus area for analysis (e.g. 'emotional_patterns', 'conversation_topics', 'relationship_development', 'preferences')",
                                "enum": ["emotional_patterns", "conversation_topics", "relationship_development", "preferences", "communication_style", "support_needs"]
                            },
                            "time_window": {
                                "type": "string", 
                                "description": "Time window for analysis",
                                "enum": ["recent", "all_time", "last_week", "last_month"]
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "detect_memory_patterns",
                    "description": "Detect recurring patterns, themes, and cross-references in user memories. Useful for understanding user behavior patterns, recurring topics, and relationship evolution.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID to detect patterns for"
                            },
                            "pattern_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["emotional_shifts", "topic_transitions", "relationship_milestones", "preference_changes", "communication_evolution"]
                                },
                                "description": "Types of patterns to detect"
                            },
                            "minimum_confidence": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Minimum confidence threshold for pattern detection (0.0-1.0)"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "evaluate_memory_importance", 
                    "description": "Evaluate and rank memory importance for understanding what matters most to the user. Helps prioritize memories for conversation context.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID to evaluate memory importance for"
                            },
                            "memory_query": {
                                "type": "string",
                                "description": "Optional query to focus importance evaluation on specific topics or themes"
                            },
                            "importance_factors": {
                                "type": "array", 
                                "items": {
                                    "type": "string",
                                    "enum": ["emotional_intensity", "personal_significance", "relationship_impact", "frequency_referenced", "recency", "uniqueness"]
                                },
                                "description": "Factors to consider when evaluating importance"
                            },
                            "top_k": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 50, 
                                "description": "Number of top important memories to return"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_memory_clusters",
                    "description": "Get semantic clusters of related memories to understand thematic groupings in user's conversation history. Useful for topic-based conversation contextualization.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID to get memory clusters for"
                            },
                            "cluster_focus": {
                                "type": "string", 
                                "description": "Optional focus for clustering",
                                "enum": ["topics", "emotions", "relationships", "activities", "preferences", "problems"]
                            },
                            "max_clusters": {
                                "type": "integer",
                                "minimum": 3,
                                "maximum": 20,
                                "description": "Maximum number of clusters to generate"
                            },
                            "include_summaries": {
                                "type": "boolean",
                                "description": "Whether to include cluster summaries"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_memory_insights",
                    "description": "Generate actionable insights from memory network analysis. Creates personalized understanding and suggestions for better conversation engagement.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string", 
                                "description": "User ID to generate insights for"
                            },
                            "insight_types": {
                                "type": "array",
                                "items": {
                                    "type": "string", 
                                    "enum": ["conversation_preferences", "emotional_needs", "relationship_status", "growth_opportunities", "support_recommendations", "engagement_strategies"]
                                },
                                "description": "Types of insights to generate"
                            },
                            "include_recommendations": {
                                "type": "boolean",
                                "description": "Whether to include actionable recommendations"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "discover_memory_connections",
                    "description": "Discover hidden connections and relationships between memories. Useful for understanding complex user narratives and relationship evolution.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID to discover connections for" 
                            },
                            "connection_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["causal_relationships", "temporal_sequences", "emotional_threads", "topic_evolution", "relationship_development"]
                                },
                                "description": "Types of connections to discover"
                            },
                            "minimum_strength": {
                                "type": "number",
                                "minimum": 0.0, 
                                "maximum": 1.0,
                                "description": "Minimum connection strength threshold"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            }
        ]
        
    async def handle_tool_call(self, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Phase 3 memory network tool calls from LLM"""
        
        try:
            if function_name == "analyze_memory_network":
                return await self._analyze_memory_network(parameters)
            elif function_name == "detect_memory_patterns":
                return await self._detect_memory_patterns(parameters)
            elif function_name == "evaluate_memory_importance":
                return await self._evaluate_memory_importance(parameters)
            elif function_name == "get_memory_clusters":
                return await self._get_memory_clusters(parameters)  
            elif function_name == "generate_memory_insights":
                return await self._generate_memory_insights(parameters)
            elif function_name == "discover_memory_connections":
                return await self._discover_memory_connections(parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown Phase 3 memory tool: {function_name}",
                    "tool_category": "phase3_memory_networks"
                }
                
        except Exception as e:
            logger.error(f"Phase 3 memory tool error in {function_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_category": "phase3_memory_networks",
                "function_name": function_name
            }
    
    async def _analyze_memory_network(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze complete memory network for user"""
        user_id = parameters["user_id"]
        focus_area = parameters.get("focus_area")
        time_window = parameters.get("time_window", "all_time")
        
        logger.info(f"Analyzing memory network for user {user_id} (focus: {focus_area}, window: {time_window})")
        
        # Perform comprehensive memory network analysis
        analysis_result = await self.phase3_networks.analyze_complete_memory_network(
            user_id, self.memory_manager
        )
        
        # Filter results based on focus area if specified
        if focus_area:
            analysis_result = self._filter_analysis_by_focus(analysis_result, focus_area)
        
        return {
            "success": True,
            "tool_category": "phase3_memory_networks", 
            "function_name": "analyze_memory_network",
            "user_id": user_id,
            "focus_area": focus_area,
            "time_window": time_window,
            "analysis": analysis_result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _detect_memory_patterns(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect patterns in user memories"""
        user_id = parameters["user_id"]
        pattern_types = parameters.get("pattern_types", ["emotional_shifts", "topic_transitions"])
        min_confidence = parameters.get("minimum_confidence", 0.6)
        
        logger.info(f"Detecting memory patterns for user {user_id} (types: {pattern_types}, min_conf: {min_confidence})")
        
        # Get user memories and conversation history
        try:
            memories = await self._get_user_memories(user_id, limit=100)
            conversation_history = await self._get_conversation_history(user_id, limit=50)
            
            # Detect patterns using Phase 3 pattern detector
            patterns = await self.phase3_networks.pattern_detector.detect_memory_patterns(
                user_id, memories, conversation_history
            )
            
            # Filter patterns by type and confidence
            filtered_patterns = [
                pattern for pattern in patterns
                if (not pattern_types or any(pt in pattern.pattern_type.value for pt in pattern_types))
                and pattern.confidence >= min_confidence
            ]
            
            return {
                "success": True,
                "tool_category": "phase3_memory_networks",
                "function_name": "detect_memory_patterns", 
                "user_id": user_id,
                "pattern_types": pattern_types,
                "minimum_confidence": min_confidence,
                "patterns_found": len(filtered_patterns),
                "patterns": [asdict(pattern) for pattern in filtered_patterns],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Pattern detection failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": f"Pattern detection failed: {str(e)}",
                "tool_category": "phase3_memory_networks",
                "function_name": "detect_memory_patterns"
            }
    
    async def _evaluate_memory_importance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate memory importance for user"""
        user_id = parameters["user_id"]
        memory_query = parameters.get("memory_query")
        importance_factors = parameters.get("importance_factors", ["emotional_intensity", "personal_significance"])
        top_k = parameters.get("top_k", 10)
        
        logger.info(f"Evaluating memory importance for user {user_id} (query: {memory_query}, top_k: {top_k})")
        
        try:
            # Get user memories
            memories = await self._get_user_memories(user_id, limit=200)
            
            if not memories:
                return {
                    "success": True,
                    "message": "No memories found for importance evaluation",
                    "important_memories": [],
                    "tool_category": "phase3_memory_networks"
                }
            
            # Evaluate importance using Phase 3 importance engine
            importance_results = await self.phase3_networks.importance_engine.evaluate_memory_importance(
                user_id, memories, importance_factors
            )
            
            # Filter by query if provided
            if memory_query:
                importance_results = self._filter_memories_by_query(importance_results, memory_query)
            
            # Get top K most important
            top_memories = importance_results[:top_k]
            
            return {
                "success": True,
                "tool_category": "phase3_memory_networks",
                "function_name": "evaluate_memory_importance",
                "user_id": user_id, 
                "memory_query": memory_query,
                "importance_factors": importance_factors,
                "top_k": top_k,
                "total_memories_evaluated": len(importance_results),
                "important_memories": top_memories,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Memory importance evaluation failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": f"Memory importance evaluation failed: {str(e)}",
                "tool_category": "phase3_memory_networks"
            }
    
    async def _get_memory_clusters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get semantic memory clusters for user"""
        user_id = parameters["user_id"]
        cluster_focus = parameters.get("cluster_focus", "topics")
        max_clusters = parameters.get("max_clusters", 10)
        include_summaries = parameters.get("include_summaries", True)
        
        logger.info(f"Getting memory clusters for user {user_id} (focus: {cluster_focus}, max: {max_clusters})")
        
        try:
            # Use Qdrant native clustering through vector memory store
            if hasattr(self.memory_manager, 'vector_store') and hasattr(self.memory_manager.vector_store, 'get_memory_clusters_for_roleplay'):
                clusters = await self.memory_manager.vector_store.get_memory_clusters_for_roleplay(
                    user_id=user_id,
                    num_clusters=max_clusters,
                    focus=cluster_focus
                )
                
                # Add cluster summaries if requested
                if include_summaries and clusters:
                    for cluster in clusters:
                        cluster["summary"] = await self._generate_cluster_summary(cluster)
                        
                return {
                    "success": True,
                    "tool_category": "phase3_memory_networks",
                    "function_name": "get_memory_clusters",
                    "user_id": user_id,
                    "cluster_focus": cluster_focus,
                    "max_clusters": max_clusters,
                    "clusters_found": len(clusters),
                    "clusters": clusters,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Vector memory clustering not available",
                    "tool_category": "phase3_memory_networks",
                    "fallback": "Use memory network analysis instead"
                }
                
        except Exception as e:
            logger.error(f"Memory clustering failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": f"Memory clustering failed: {str(e)}",
                "tool_category": "phase3_memory_networks"
            }
    
    async def _generate_memory_insights(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate memory insights for user"""
        user_id = parameters["user_id"]
        insight_types = parameters.get("insight_types", ["conversation_preferences", "emotional_needs"])
        include_recommendations = parameters.get("include_recommendations", True)
        
        logger.info(f"Generating memory insights for user {user_id} (types: {insight_types})")
        
        try:
            # Perform comprehensive analysis to generate insights
            analysis_result = await self.phase3_networks.analyze_complete_memory_network(
                user_id, self.memory_manager
            )
            
            # Extract insights based on requested types
            insights = []
            if "conversation_preferences" in insight_types:
                insights.extend(self._extract_conversation_insights(analysis_result))
            if "emotional_needs" in insight_types:
                insights.extend(self._extract_emotional_insights(analysis_result))
            if "relationship_status" in insight_types:
                insights.extend(self._extract_relationship_insights(analysis_result))
            if "growth_opportunities" in insight_types:
                insights.extend(self._extract_growth_insights(analysis_result))
            if "support_recommendations" in insight_types:
                insights.extend(self._extract_support_insights(analysis_result))
            if "engagement_strategies" in insight_types:
                insights.extend(self._extract_engagement_insights(analysis_result))
            
            return {
                "success": True,
                "tool_category": "phase3_memory_networks", 
                "function_name": "generate_memory_insights",
                "user_id": user_id,
                "insight_types": insight_types,
                "include_recommendations": include_recommendations,
                "insights_generated": len(insights),
                "insights": insights,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Memory insights generation failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": f"Memory insights generation failed: {str(e)}",
                "tool_category": "phase3_memory_networks"
            }
    
    async def _discover_memory_connections(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Discover connections between memories"""
        user_id = parameters["user_id"]
        connection_types = parameters.get("connection_types", ["causal_relationships", "temporal_sequences"])
        min_strength = parameters.get("minimum_strength", 0.5)
        
        logger.info(f"Discovering memory connections for user {user_id} (types: {connection_types})")
        
        try:
            # Get user memories
            memories = await self._get_user_memories(user_id, limit=150)
            
            if len(memories) < 2:
                return {
                    "success": True,
                    "message": "Insufficient memories for connection discovery",
                    "connections": [],
                    "tool_category": "phase3_memory_networks"
                }
            
            # Discover connections using pattern detector
            connections = await self._analyze_memory_connections(
                memories, connection_types, min_strength
            )
            
            return {
                "success": True,
                "tool_category": "phase3_memory_networks",
                "function_name": "discover_memory_connections",
                "user_id": user_id,
                "connection_types": connection_types,
                "minimum_strength": min_strength,
                "connections_found": len(connections),
                "connections": connections,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Memory connection discovery failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": f"Memory connection discovery failed: {str(e)}",
                "tool_category": "phase3_memory_networks"
            }
    
    # Helper methods
    
    async def _get_user_memories(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user memories from memory manager"""
        try:
            if hasattr(self.memory_manager, 'get_memories'):
                return await self.memory_manager.get_memories(user_id, limit=limit)
            elif hasattr(self.memory_manager, 'retrieve_relevant_memories'):
                return await self.memory_manager.retrieve_relevant_memories(
                    user_id=user_id, query="", limit=limit
                )
            else:
                logger.warning("No compatible memory retrieval method found")
                return []
        except Exception as e:
            logger.error(f"Failed to get user memories: {e}")
            return []
    
    async def _get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history from memory manager"""
        try:
            if hasattr(self.memory_manager, 'get_conversation_history'):
                return await self.memory_manager.get_conversation_history(user_id, limit=limit)
            else:
                # Fallback to getting memories
                return await self._get_user_memories(user_id, limit=limit)
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    def _filter_analysis_by_focus(self, analysis: Dict[str, Any], focus_area: str) -> Dict[str, Any]:
        """Filter analysis results by focus area"""
        if focus_area in ["emotional_patterns", "preferences", "communication_style", "support_needs"]:
            # Keep only relevant sections of analysis
            filtered = {
                "focus_area": focus_area,
                "summary": analysis.get("summary", ""),
                "relevant_patterns": [],
                "key_insights": []
            }
            
            # Filter patterns and insights relevant to focus area
            for pattern in analysis.get("patterns", []):
                if focus_area.lower() in pattern.get("description", "").lower():
                    filtered["relevant_patterns"].append(pattern)
            
            for insight in analysis.get("insights", []):
                if focus_area.lower() in insight.get("title", "").lower():
                    filtered["key_insights"].append(insight)
                    
            return filtered
        
        return analysis
    
    def _filter_memories_by_query(self, memories: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Filter memories by query relevance"""
        query_lower = query.lower()
        filtered = []
        
        for memory in memories:
            content = memory.get("content", "").lower()
            if query_lower in content:
                filtered.append(memory)
        
        return filtered
    
    async def _generate_cluster_summary(self, cluster: Dict[str, Any]) -> str:
        """Generate summary for memory cluster"""
        try:
            memories = cluster.get("memories", [])
            if not memories:
                return "Empty cluster"
            
            # Extract key themes from cluster memories
            themes = []
            for memory in memories[:5]:  # Limit to first 5 memories
                content = memory.get("content", "")
                if content:
                    themes.append(content[:100])  # First 100 chars
            
            return f"Cluster contains {len(memories)} memories about: {', '.join(themes[:3])}"
            
        except Exception as e:
            logger.error(f"Failed to generate cluster summary: {e}")
            return "Summary generation failed"
    
    def _extract_conversation_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract conversation preference insights"""
        insights = []
        
        # Analyze communication patterns
        patterns = analysis.get("patterns", [])
        for pattern in patterns:
            if "communication" in pattern.get("pattern_type", "").lower():
                insights.append({
                    "type": "conversation_preferences",
                    "title": "Communication Style Preference",
                    "description": pattern.get("description", ""),
                    "confidence": pattern.get("confidence", 0.0),
                    "recommendations": pattern.get("implications", [])
                })
        
        return insights
    
    def _extract_emotional_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract emotional needs insights"""
        insights = []
        
        # Analyze emotional patterns
        patterns = analysis.get("patterns", [])
        for pattern in patterns:
            if "emotional" in pattern.get("pattern_type", "").lower():
                insights.append({
                    "type": "emotional_needs",
                    "title": "Emotional Support Pattern",
                    "description": pattern.get("description", ""),
                    "confidence": pattern.get("confidence", 0.0),
                    "recommendations": pattern.get("implications", [])
                })
        
        return insights
    
    def _extract_relationship_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationship status insights"""
        return [{
            "type": "relationship_status",
            "title": "Relationship Development",
            "description": "Based on conversation history and interaction patterns",
            "confidence": 0.7,
            "recommendations": ["Continue building trust", "Maintain consistent engagement"]
        }]
    
    def _extract_growth_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract growth opportunity insights"""
        return [{
            "type": "growth_opportunities", 
            "title": "Conversation Growth Areas",
            "description": "Areas where deeper engagement could be beneficial",
            "confidence": 0.6,
            "recommendations": ["Explore new topics", "Ask more personal questions"]
        }]
    
    def _extract_support_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract support recommendation insights"""
        return [{
            "type": "support_recommendations",
            "title": "Optimal Support Approach",
            "description": "Recommended approach for providing emotional support",
            "confidence": 0.8,
            "recommendations": ["Listen actively", "Provide empathetic responses", "Offer practical suggestions when appropriate"]
        }]
    
    def _extract_engagement_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract engagement strategy insights"""
        return [{
            "type": "engagement_strategies",
            "title": "Optimal Engagement Approach", 
            "description": "Best strategies for maintaining engaging conversations",
            "confidence": 0.7,
            "recommendations": ["Reference past conversations", "Ask follow-up questions", "Share relevant experiences"]
        }]
    
    async def _analyze_memory_connections(self, memories: List[Dict[str, Any]], 
                                       connection_types: List[str], 
                                       min_strength: float) -> List[Dict[str, Any]]:
        """Analyze connections between memories"""
        connections = []
        
        # Simple connection analysis (can be enhanced with more sophisticated algorithms)
        for i, memory1 in enumerate(memories):
            for j, memory2 in enumerate(memories[i+1:], i+1):
                
                # Calculate connection strength based on content similarity
                strength = self._calculate_connection_strength(memory1, memory2)
                
                if strength >= min_strength:
                    connection_type = self._determine_connection_type(memory1, memory2, connection_types)
                    if connection_type:
                        connections.append({
                            "memory1": memory1.get("content", "")[:100],
                            "memory2": memory2.get("content", "")[:100],
                            "connection_type": connection_type,
                            "strength": strength,
                            "explanation": f"Connected by {connection_type} with strength {strength:.2f}"
                        })
        
        return connections
    
    def _calculate_connection_strength(self, memory1: Dict[str, Any], memory2: Dict[str, Any]) -> float:
        """Calculate connection strength between two memories"""
        # Simple implementation - can be enhanced with vector similarity
        content1 = memory1.get("content", "").lower().split()
        content2 = memory2.get("content", "").lower().split()
        
        if not content1 or not content2:
            return 0.0
        
        # Calculate word overlap
        overlap = len(set(content1) & set(content2))
        total_words = len(set(content1) | set(content2))
        
        return overlap / total_words if total_words > 0 else 0.0
    
    def _determine_connection_type(self, memory1: Dict[str, Any], memory2: Dict[str, Any], 
                                 connection_types: List[str]) -> Optional[str]:
        """Determine the type of connection between memories"""
        # Simple heuristic-based connection type determination
        content1 = memory1.get("content", "").lower()
        content2 = memory2.get("content", "").lower()
        
        for conn_type in connection_types:
            if conn_type == "causal_relationships" and ("because" in content1 or "because" in content2):
                return "causal_relationships"
            elif conn_type == "temporal_sequences" and ("then" in content1 or "then" in content2):
                return "temporal_sequences"
            elif conn_type == "emotional_threads" and any(emotion in content1 and emotion in content2 
                                                         for emotion in ["happy", "sad", "angry", "excited", "worried"]):
                return "emotional_threads"
            elif conn_type == "topic_evolution" and len(set(content1.split()) & set(content2.split())) > 2:
                return "topic_evolution"
            elif conn_type == "relationship_development":
                return "relationship_development"  # Default for personal conversations
        
        return None