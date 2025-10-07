"""
Multi-Bot Memory Query System

Advanced memory querying capabilities that work across multiple bots:
1. Global queries (all bots)
2. Selective queries (specific bots)
3. Cross-bot analysis
4. Comparative bot intelligence

This module extends the existing bot-segmented memory system to support
advanced multi-bot queries while maintaining data isolation by default.
"""

import os
import logging
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Union
from qdrant_client import models

from .vector_memory_system import VectorMemoryStore
from .memory_protocol import create_memory_manager

logger = logging.getLogger(__name__)


class MultiBotMemoryQuerier:
    """
    Advanced multi-bot memory query capabilities for WhisperEngine
    
    Features:
    - Query all bots (admin/debugging)
    - Query specific bot subsets (team analysis)
    - Cross-bot memory analysis
    - Comparative bot intelligence
    - Maintains existing bot isolation by default
    """
    
    def __init__(self, memory_manager=None):
        """Initialize with optional memory manager, or create one"""
        if memory_manager:
            self.memory_manager = memory_manager
        else:
            # Create memory manager in multi-bot query context
            original_bot_name = os.getenv("DISCORD_BOT_NAME")
            os.environ["DISCORD_BOT_NAME"] = "multi_bot_querier"
            self.memory_manager = create_memory_manager(memory_type="vector")
            if original_bot_name:
                os.environ["DISCORD_BOT_NAME"] = original_bot_name
        
        self.vector_store = self.memory_manager.vector_store
    
    async def _discover_bot_collections(self) -> Dict[str, str]:
        """
        Dynamically discover bot collections from environment files
        Following WhisperEngine's character-agnostic architecture
        
        Returns:
            Dict mapping bot_name -> collection_name
        """
        bot_collections = {}
        
        # Find all .env.* files in the project root
        env_files = glob.glob('/Users/markcastillo/git/whisperengine/.env.*')
        
        for env_file in env_files:
            # Skip template and local files
            if 'template' in env_file or 'local' in env_file:
                continue
                
            # Extract bot name from filename (.env.botname)
            bot_name = os.path.basename(env_file).replace('.env.', '')
            
            # Read the collection name from the env file
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('QDRANT_COLLECTION_NAME='):
                            collection_name = line.split('=', 1)[1].strip()
                            bot_collections[bot_name] = collection_name
                            break
            except Exception as e:
                logger.warning(f"Failed to read collection name from {env_file}: {e}")
        
        logger.info(f"Discovered {len(bot_collections)} bot collections: {list(bot_collections.keys())}")
        return bot_collections
    
    async def query_all_bots(self, 
                            query: str, 
                            user_id: str, 
                            top_k: int = 10,
                            min_score: float = 0.0) -> Dict[str, List[Dict]]:
        """
        Query across ALL bots' memories using their dedicated collections
        
        Use cases:
        - Admin debugging and analysis
        - Global pattern detection
        - Cross-bot user behavior analysis
        - System-wide memory search
        
        Args:
            query: Search query text
            user_id: User to search memories for
            top_k: Maximum results per search
            min_score: Minimum relevance score
            
        Returns:
            Dict mapping bot_name -> List of memory results
        """
        try:
            logger.info(f"Performing global memory query for user {user_id}: '{query}'")
            
            # Get query embedding
            query_embedding = list(self.vector_store.embedder.embed([query]))[0]
            
            # 🎯 NEW ARCHITECTURE: Dynamically discover bot collections from environment files
            bot_collections = await self._discover_bot_collections()
            
            results_by_bot = {}
            
            for bot_name, collection_name in bot_collections.items():
                try:
                    # Query each bot's collection individually
                    search_results = self.vector_store.client.search(
                        collection_name=collection_name,
                        query_vector=models.NamedVector(name="content", vector=query_embedding),
                        query_filter=models.Filter(
                            must=[
                                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
                                # 🎯 NO bot_name filter needed - collection is already bot-specific
                            ]
                        ),
                        limit=top_k,
                        score_threshold=min_score,
                        with_payload=True
                    )
                    
                    if search_results:
                        results_by_bot[bot_name] = []
                        for result in search_results:
                            results_by_bot[bot_name].append({
                                'content': result.payload.get('content', '') if result.payload else '',
                                'score': result.score,
                                'timestamp': result.payload.get('timestamp', '') if result.payload else '',
                                'memory_type': result.payload.get('memory_type', '') if result.payload else '',
                                'confidence': result.payload.get('confidence', 0.0) if result.payload else 0.0,
                                'source': result.payload.get('source', '') if result.payload else '',
                                'significance': result.payload.get('overall_significance', 0.0) if result.payload else 0.0
                            })
                    
                except Exception as e:
                    logger.warning(f"Failed to query {bot_name} collection {collection_name}: {e}")
            
            logger.info(f"Global query found memories from {len(results_by_bot)} bots")
            return results_by_bot
            
        except Exception as e:
            logger.error(f"Failed to perform global memory query: {e}")
            return {}
    
    async def query_specific_bots(self, 
                                 query: str, 
                                 user_id: str, 
                                 bot_names: List[str],
                                 top_k: int = 10,
                                 min_score: float = 0.0) -> Dict[str, List[Dict]]:
        """
        Query specific subset of bots using their dedicated collections
        
        Use cases:
        - Team-based analysis (e.g., all analytical bots)
        - Comparative bot studies
        - Selective memory retrieval
        - Bot category analysis
        
        Args:
            query: Search query text
            user_id: User to search memories for
            bot_names: List of specific bot names to query
            top_k: Maximum results per search
            min_score: Minimum relevance score
            
        Returns:
            Dict mapping bot_name -> List of memory results
        """
        try:
            logger.info(f"Performing selective memory query for bots {bot_names}, user {user_id}: '{query}'")
            
            # Get query embedding
            query_embedding = list(self.vector_store.embedder.embed([query]))[0]
            
            # 🎯 NEW ARCHITECTURE: Dynamically discover bot collections from environment files
            bot_collections = await self._discover_bot_collections()
            
            results_by_bot = {}
            
            for bot_name in bot_names:
                if bot_name not in bot_collections:
                    logger.warning(f"Unknown bot name: {bot_name}")
                    continue
                
                collection_name = bot_collections[bot_name]
                try:
                    # Query the specific bot's collection
                    search_results = self.vector_store.client.search(
                        collection_name=collection_name,
                        query_vector=models.NamedVector(name="content", vector=query_embedding),
                        query_filter=models.Filter(
                            must=[
                                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
                                # 🎯 NO bot_name filter needed - collection is already bot-specific
                            ]
                        ),
                        limit=top_k,
                        score_threshold=min_score,
                        with_payload=True
                    )
                    
                    if search_results:
                        results_by_bot[bot_name] = []
                        for result in search_results:
                            results_by_bot[bot_name].append({
                                'content': result.payload.get('content', '') if result.payload else '',
                                'score': result.score,
                                'timestamp': result.payload.get('timestamp', '') if result.payload else '',
                                'memory_type': result.payload.get('memory_type', '') if result.payload else '',
                                'confidence': result.payload.get('confidence', 0.0) if result.payload else 0.0,
                                'source': result.payload.get('source', '') if result.payload else '',
                                'significance': result.payload.get('overall_significance', 0.0) if result.payload else 0.0
                            })
                
                except Exception as e:
                    logger.warning(f"Failed to query {bot_name} collection {collection_name}: {e}")
            
            logger.info(f"Selective query found memories from {len(results_by_bot)} of {len(bot_names)} requested bots")
            return results_by_bot
            
        except Exception as e:
            logger.error(f"Failed to perform selective memory query: {e}")
            return {}
    
    async def cross_bot_analysis(self, 
                               user_id: str, 
                               analysis_topic: str,
                               include_bots: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze how different bots remember/perceive the same user or topic
        
        Use cases:
        - User behavior pattern analysis
        - Bot perspective comparison
        - Collaborative decision making
        - Memory consistency checking
        
        Args:
            user_id: User to analyze
            analysis_topic: Topic/query to analyze across bots
            include_bots: Optional list to limit analysis to specific bots
            
        Returns:
            Comprehensive analysis report
        """
        try:
            logger.info(f"Performing cross-bot analysis for user {user_id}, topic: '{analysis_topic}'")
            
            # Get memories from all or specific bots
            if include_bots:
                all_results = await self.query_specific_bots(analysis_topic, user_id, include_bots, top_k=50)
            else:
                all_results = await self.query_all_bots(analysis_topic, user_id, top_k=50)
            
            analysis = {
                'topic': analysis_topic,
                'user_id': user_id,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'bots_analyzed': list(all_results.keys()),
                'total_memories': sum(len(memories) for memories in all_results.values()),
                'bot_perspectives': {},
                'insights': {
                    'most_relevant_bot': None,
                    'highest_confidence_bot': None,
                    'most_memories_bot': None,
                    'average_relevance_scores': {},
                    'memory_type_distribution': {},
                    'temporal_patterns': {}
                }
            }
            
            # Analyze each bot's perspective
            best_relevance = 0
            best_confidence = 0
            most_memories = 0
            
            for bot_name, memories in all_results.items():
                if not memories:
                    continue
                
                # Calculate statistics
                avg_score = sum(m['score'] for m in memories) / len(memories)
                avg_confidence = sum(m['confidence'] for m in memories) / len(memories)
                avg_significance = sum(m['significance'] for m in memories) / len(memories)
                
                memory_types = [m['memory_type'] for m in memories]
                memory_type_counts = {}
                for mt in memory_types:
                    memory_type_counts[mt] = memory_type_counts.get(mt, 0) + 1
                
                # Bot perspective analysis
                analysis['bot_perspectives'][bot_name] = {
                    'memory_count': len(memories),
                    'average_relevance_score': avg_score,
                    'average_confidence': avg_confidence,
                    'average_significance': avg_significance,
                    'memory_types': memory_type_counts,
                    'top_memory': memories[0]['content'][:100] + "..." if memories else "",
                    'recent_memories': len([m for m in memories if 'timestamp' in m and m['timestamp']])
                }
                
                # Track bests
                if avg_score > best_relevance:
                    best_relevance = avg_score
                    analysis['insights']['most_relevant_bot'] = bot_name
                
                if avg_confidence > best_confidence:
                    best_confidence = avg_confidence
                    analysis['insights']['highest_confidence_bot'] = bot_name
                
                if len(memories) > most_memories:
                    most_memories = len(memories)
                    analysis['insights']['most_memories_bot'] = bot_name
                
                analysis['insights']['average_relevance_scores'][bot_name] = avg_score
            
            logger.info(f"Cross-bot analysis complete: {len(analysis['bots_analyzed'])} bots, {analysis['total_memories']} memories")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to perform cross-bot analysis: {e}")
            return {
                'error': str(e),
                'topic': analysis_topic,
                'user_id': user_id,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_bot_memory_stats(self, user_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get memory statistics for all bots
        
        Use cases:
        - System health monitoring
        - Bot performance comparison
        - Memory usage analysis
        - Debugging and optimization
        
        Args:
            user_id: Optional user to filter stats for
            
        Returns:
            Dict mapping bot_name -> statistics
        """
        try:
            logger.info(f"Getting bot memory statistics for user: {user_id or 'all users'}")
            
            # Scroll through all memories to get statistics
            filter_conditions = []
            if user_id:
                filter_conditions.append(
                    models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
                )
            
            query_filter = models.Filter(must=filter_conditions) if filter_conditions else None
            
            scroll_result = self.vector_store.client.scroll(
                collection_name=self.vector_store.collection_name,
                scroll_filter=query_filter,
                limit=10000,  # Large limit to get comprehensive stats
                with_payload=True
            )[0]  # Get points from scroll result
            
            # Group and analyze by bot
            bot_stats = {}
            for point in scroll_result:
                bot_name = point.payload.get('bot_name', 'unknown')
                
                if bot_name not in bot_stats:
                    bot_stats[bot_name] = {
                        'total_memories': 0,
                        'memory_types': {},
                        'confidence_scores': [],
                        'significance_scores': [],
                        'unique_users': set(),
                        'date_range': {'earliest': None, 'latest': None}
                    }
                
                stats = bot_stats[bot_name]
                stats['total_memories'] += 1
                
                # Memory type distribution
                memory_type = point.payload.get('memory_type', 'unknown')
                stats['memory_types'][memory_type] = stats['memory_types'].get(memory_type, 0) + 1
                
                # Confidence and significance tracking
                confidence = point.payload.get('confidence', 0.0)
                significance = point.payload.get('overall_significance', 0.0)
                stats['confidence_scores'].append(confidence)
                stats['significance_scores'].append(significance)
                
                # User tracking
                user_id_from_memory = point.payload.get('user_id')
                if user_id_from_memory:
                    stats['unique_users'].add(user_id_from_memory)
                
                # Date range tracking
                timestamp = point.payload.get('timestamp')
                if timestamp:
                    if not stats['date_range']['earliest'] or timestamp < stats['date_range']['earliest']:
                        stats['date_range']['earliest'] = timestamp
                    if not stats['date_range']['latest'] or timestamp > stats['date_range']['latest']:
                        stats['date_range']['latest'] = timestamp
            
            # Calculate summary statistics
            summary_stats = {}
            for bot_name, stats in bot_stats.items():
                summary_stats[bot_name] = {
                    'total_memories': stats['total_memories'],
                    'unique_users': len(stats['unique_users']),
                    'memory_types': stats['memory_types'],
                    'average_confidence': sum(stats['confidence_scores']) / len(stats['confidence_scores']) if stats['confidence_scores'] else 0,
                    'average_significance': sum(stats['significance_scores']) / len(stats['significance_scores']) if stats['significance_scores'] else 0,
                    'date_range': {
                        'earliest': stats['date_range']['earliest'],
                        'latest': stats['date_range']['latest']
                    }
                }
            
            logger.info(f"Memory statistics calculated for {len(summary_stats)} bots")
            return summary_stats
            
        except Exception as e:
            logger.error(f"Failed to get bot memory statistics: {e}")
            return {}


# Factory function for easy integration
def create_multi_bot_querier(memory_manager=None) -> MultiBotMemoryQuerier:
    """
    Factory function to create a MultiBotMemoryQuerier
    
    Args:
        memory_manager: Optional existing memory manager to use
        
    Returns:
        MultiBotMemoryQuerier instance
    """
    return MultiBotMemoryQuerier(memory_manager=memory_manager)