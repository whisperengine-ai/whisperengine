# src/memory/core/storage_abstraction.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Assembled conversation context from all tiers"""
    recent_messages: List[Dict[str, Any]]
    semantic_summaries: List[Dict[str, Any]] 
    related_topics: List[Dict[str, Any]]
    full_conversations: List[Dict[str, Any]]
    assembly_metadata: Dict[str, Any]
    
    def to_context_string(self, max_length: int = 4000) -> str:
        """Convert to optimized context string for LLM"""
        # Intelligent context string assembly
        # Priority: recent > semantic > topical > historical
        context_parts = []
        current_length = 0
        
        # Add recent messages first (highest priority)
        if self.recent_messages:
            recent_text = "Recent conversation:\n"
            for msg in self.recent_messages[:5]:  # Limit recent messages
                msg_text = f"User: {msg.get('user_message', '')}\nBot: {msg.get('bot_response', '')}\n"
                if current_length + len(msg_text) < max_length * 0.4:  # 40% for recent
                    recent_text += msg_text
                    current_length += len(msg_text)
                else:
                    break
            context_parts.append(recent_text)
        
        # Add semantic summaries (medium priority)
        if self.semantic_summaries and current_length < max_length * 0.7:
            summary_text = "\nRelevant past topics:\n"
            for summary in self.semantic_summaries[:3]:
                summary_line = f"- {summary.get('summary', '')}\n"
                if current_length + len(summary_line) < max_length * 0.7:
                    summary_text += summary_line
                    current_length += len(summary_line)
                else:
                    break
            context_parts.append(summary_text)
        
        # Add related topics (lower priority)
        if self.related_topics and current_length < max_length * 0.9:
            topic_text = "\nRelated interests:\n"
            for topic in self.related_topics[:2]:
                topic_line = f"- {topic.get('topic', '')}\n"
                if current_length + len(topic_line) < max_length * 0.9:
                    topic_text += topic_line
                    current_length += len(topic_line)
                else:
                    break
            context_parts.append(topic_text)
        
        return "".join(context_parts)

@dataclass
class StorageMetrics:
    """Performance and usage metrics"""
    retrieval_time_ms: int
    sources_used: List[str]
    context_size_chars: int
    cache_hit_ratio: float
    total_conversations: int

class HierarchicalMemoryManager:
    """
    Main interface for hierarchical memory system
    Coordinates all four storage tiers for optimal performance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tier1_cache = None      # Redis recent context
        self.tier2_archive = None    # PostgreSQL full conversations
        self.tier3_semantic = None   # ChromaDB summaries  
        self.tier4_graph = None      # Neo4j relationships
        
        self.metrics = StorageMetrics(0, [], 0, 0.0, 0)
        self.initialized = False
    
    async def initialize(self):
        """Initialize all storage tiers"""
        logger.info("Initializing hierarchical memory system...")
        
        try:
            # Initialize each tier with proper error handling
            await self._init_tier1_cache()
            await self._init_tier2_archive() 
            await self._init_tier3_semantic()
            await self._init_tier4_graph()
            
            self.initialized = True
            logger.info("Hierarchical memory system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize hierarchical memory system: {e}")
            raise
    
    async def _init_tier1_cache(self):
        """Initialize Redis cache tier"""
        try:
            if not self.config.get('redis_enabled', True):
                logger.info("Redis tier disabled by configuration")
                return
                
            from src.memory.tiers.tier1_redis_cache import RedisContextCache
            
            redis_config = self.config.get('redis', {})
            self.tier1_cache = RedisContextCache(
                redis_url=redis_config.get('url', 'redis://localhost:6379'),
                default_ttl=redis_config.get('ttl', 1800)
            )
            await self.tier1_cache.initialize()
            logger.info("✅ Tier 1 (Redis cache) initialized")
            
        except Exception as e:
            logger.warning(f"Tier 1 (Redis) initialization failed: {e}")
            self.tier1_cache = None
    
    async def _init_tier2_archive(self):
        """Initialize PostgreSQL archive tier"""
        try:
            if not self.config.get('postgresql_enabled', True):
                logger.info("PostgreSQL tier disabled by configuration")
                return
                
            from src.memory.tiers.tier2_postgresql import PostgreSQLConversationArchive
            
            pg_config = self.config.get('postgresql', {})
            self.tier2_archive = PostgreSQLConversationArchive(
                database_url=pg_config.get('url', 'postgresql://localhost/whisperengine')
            )
            await self.tier2_archive.initialize()
            logger.info("✅ Tier 2 (PostgreSQL archive) initialized")
            
        except Exception as e:
            logger.warning(f"Tier 2 (PostgreSQL) initialization failed: {e}")
            self.tier2_archive = None
    
    async def _init_tier3_semantic(self):
        """Initialize ChromaDB semantic tier"""
        try:
            if not self.config.get('chromadb_enabled', True):
                logger.info("ChromaDB tier disabled by configuration")
                return
                
            from src.memory.tiers.tier3_chromadb_summaries import ChromaDBSemanticSummaries
            
            chroma_config = self.config.get('chromadb', {})
            self.tier3_semantic = ChromaDBSemanticSummaries(
                host=chroma_config.get('host', 'localhost'),
                port=chroma_config.get('port', 8000)
            )
            await self.tier3_semantic.initialize()
            logger.info("✅ Tier 3 (ChromaDB semantic) initialized")
            
        except Exception as e:
            logger.warning(f"Tier 3 (ChromaDB) initialization failed: {e}")
            self.tier3_semantic = None
    
    async def _init_tier4_graph(self):
        """Initialize Neo4j graph tier"""
        try:
            if not self.config.get('neo4j_enabled', False):  # Default disabled
                logger.info("Neo4j tier disabled by configuration")
                return
                
            from src.memory.tiers.tier4_neo4j_relationships import Neo4jRelationshipEngine
            
            neo4j_config = self.config.get('neo4j', {})
            self.tier4_graph = Neo4jRelationshipEngine(
                uri=neo4j_config.get('uri', 'bolt://localhost:7687'),
                user=neo4j_config.get('user', 'neo4j'),
                password=neo4j_config.get('password', 'password')
            )
            await self.tier4_graph.initialize()
            logger.info("✅ Tier 4 (Neo4j graph) initialized")
            
        except Exception as e:
            logger.warning(f"Tier 4 (Neo4j) initialization failed: {e}")
            self.tier4_graph = None
    
    async def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store conversation across all appropriate tiers
        Returns conversation_id for future reference
        """
        start_time = datetime.now()
        conversation_id = None
        
        try:
            # Step 1: Store full conversation in PostgreSQL (source of truth)
            if self.tier2_archive:
                conversation_id = await self.tier2_archive.store_conversation(
                    user_id=user_id,
                    user_message=user_message,
                    bot_response=bot_response,
                    metadata=metadata
                )
            else:
                # Fallback ID generation if PostgreSQL unavailable
                import uuid
                conversation_id = str(uuid.uuid4())
            
            # Step 2: Generate and store semantic summary in ChromaDB
            if self.tier3_semantic:
                summary = await self._generate_conversation_summary(
                    user_message, bot_response
                )
                await self.tier3_semantic.store_summary(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    summary=summary,
                    metadata=metadata
                )
            
            # Step 3: Extract and store relationships in Neo4j
            if self.tier4_graph:
                await self._extract_and_store_relationships(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    user_message=user_message,
                    bot_response=bot_response
                )
            
            # Step 4: Update recent context cache in Redis
            if self.tier1_cache:
                await self.tier1_cache.add_to_recent_context(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    bot_response=bot_response,
                    metadata=metadata
                )
            
            # Record storage metrics
            storage_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"Stored conversation {conversation_id} in {storage_time:.2f}ms")
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            # Attempt cleanup if partial storage occurred
            if conversation_id:
                await self._cleanup_partial_storage(conversation_id)
            raise
    
    async def get_conversation_context(
        self,
        user_id: str,
        current_query: str,
        max_context_length: int = 4000
    ) -> ConversationContext:
        """
        Intelligent context assembly from all tiers
        Target: <100ms total retrieval time
        """
        start_time = datetime.now()
        
        try:
            # Execute retrieval from all tiers in parallel for optimal performance
            retrieval_tasks = [
                self._get_recent_context(user_id),
                self._get_semantic_context(user_id, current_query),
                self._get_topical_context(user_id, current_query),
            ]
            
            recent_context, semantic_context, topical_context = await asyncio.gather(
                *retrieval_tasks, return_exceptions=True
            )
            
            # Handle any retrieval failures gracefully
            recent_context = recent_context if not isinstance(recent_context, Exception) else []
            semantic_context = semantic_context if not isinstance(semantic_context, Exception) else []
            topical_context = topical_context if not isinstance(topical_context, Exception) else []
            
            # Get full conversation details for most relevant items
            relevant_conversation_ids = self._extract_relevant_conversation_ids(
                semantic_context, topical_context, limit=3
            )
            
            full_conversations = []
            if self.tier2_archive and relevant_conversation_ids:
                full_conversations = await self.tier2_archive.get_conversations(
                    conversation_ids=relevant_conversation_ids
                )
            
            # Assemble final context with intelligent prioritization
            context = ConversationContext(
                recent_messages=recent_context,
                semantic_summaries=semantic_context,
                related_topics=topical_context,
                full_conversations=full_conversations,
                assembly_metadata={
                    'retrieval_time_ms': (datetime.now() - start_time).total_seconds() * 1000,
                    'sources_used': self._get_sources_used(recent_context, semantic_context, topical_context),
                    'query': current_query,
                    'user_id': user_id
                }
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error assembling conversation context: {e}")
            # Return minimal context from cache if available
            return await self._get_fallback_context(user_id)
    
    async def _get_recent_context(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent context from Redis cache"""
        if not self.tier1_cache:
            return []
        
        try:
            return await self.tier1_cache.get_recent_context(user_id, limit=10)
        except Exception as e:
            logger.warning(f"Failed to get recent context: {e}")
            return []
    
    async def _get_semantic_context(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Get semantic context from ChromaDB"""
        if not self.tier3_semantic:
            return []
        
        try:
            return await self.tier3_semantic.search_summaries(
                user_id=user_id,
                query=query,
                limit=5,
                time_decay=True
            )
        except Exception as e:
            logger.warning(f"Failed to get semantic context: {e}")
            return []
    
    async def _get_topical_context(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Get topical context from Neo4j"""
        if not self.tier4_graph:
            return []
        
        try:
            return await self.tier4_graph.get_related_conversation_topics(
                user_id=user_id,
                current_topics=self._extract_topics(query),
                limit=3
            )
        except Exception as e:
            logger.warning(f"Failed to get topical context: {e}")
            return []
    
    async def _generate_conversation_summary(self, user_message: str, bot_response: str) -> str:
        """Generate summary for ChromaDB storage"""
        # Simple summarization - can be enhanced with LLM later
        topics = self._extract_topics(user_message)
        intent = self._extract_intent(user_message)
        
        topic_text = ", ".join(topics[:3]) if topics else "general conversation"
        summary = f"User {intent} about {topic_text}. Bot provided assistance."
        
        return summary[:150]  # Optimal length for semantic search
    
    def _extract_topics(self, text: str) -> List[str]:
        """Simple topic extraction"""
        # This could be enhanced with proper NLP
        import re
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return list(set(words))[:5]
    
    def _extract_intent(self, text: str) -> str:
        """Simple intent extraction"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['how', 'what', 'why', 'when', 'where']):
            return "asked"
        elif any(word in text_lower for word in ['help', 'need', 'can you', 'please']):
            return "requested help"
        else:
            return "discussed"
    
    def _extract_relevant_conversation_ids(
        self, 
        semantic_context: List[Dict[str, Any]], 
        topical_context: List[Dict[str, Any]], 
        limit: int = 3
    ) -> List[str]:
        """Extract conversation IDs from context results"""
        conversation_ids = []
        
        # Get IDs from semantic context
        for item in semantic_context:
            if 'conversation_id' in item:
                conversation_ids.append(item['conversation_id'])
        
        # Get IDs from topical context
        for item in topical_context:
            if 'conversation_id' in item:
                conversation_ids.append(item['conversation_id'])
        
        # Remove duplicates and limit
        return list(set(conversation_ids))[:limit]
    
    def _get_sources_used(self, recent: List, semantic: List, topical: List) -> List[str]:
        """Determine which sources were used"""
        sources = []
        if recent:
            sources.append('redis')
        if semantic:
            sources.append('chromadb')
        if topical:
            sources.append('neo4j')
        return sources
    
    async def _get_fallback_context(self, user_id: str) -> ConversationContext:
        """Get minimal fallback context"""
        return ConversationContext(
            recent_messages=[],
            semantic_summaries=[],
            related_topics=[],
            full_conversations=[],
            assembly_metadata={
                'retrieval_time_ms': 0,
                'sources_used': ['fallback'],
                'query': '',
                'user_id': user_id
            }
        )
    
    async def _extract_and_store_relationships(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        bot_response: str
    ):
        """Extract and store relationships in Neo4j"""
        if not self.tier4_graph:
            return
        
        try:
            # Extract topics and entities
            topics = self._extract_topics(user_message + " " + bot_response)
            
            # Store relationships
            await self.tier4_graph.store_conversation_relationships(
                conversation_id=conversation_id,
                user_id=user_id,
                topics=topics,
                metadata={}
            )
            
        except Exception as e:
            logger.warning(f"Failed to store relationships: {e}")
    
    async def _cleanup_partial_storage(self, conversation_id: str):
        """Cleanup partial storage on error"""
        logger.info(f"Cleaning up partial storage for conversation {conversation_id}")
        
        # Attempt to remove from all tiers
        tasks = []
        
        if self.tier2_archive:
            tasks.append(self.tier2_archive.delete_conversation(conversation_id))
        
        if self.tier3_semantic:
            tasks.append(self.tier3_semantic.delete_summary(conversation_id))
        
        if self.tier4_graph:
            tasks.append(self.tier4_graph.delete_conversation(conversation_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_metrics(self) -> StorageMetrics:
        """Get current system metrics"""
        return self.metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all storage tiers"""
        health = {
            'tier1_redis': False,
            'tier2_postgresql': False,
            'tier3_chromadb': False,
            'tier4_neo4j': False,
            'overall_healthy': False
        }
        
        # Check each tier
        if self.tier1_cache:
            try:
                await self.tier1_cache.ping()
                health['tier1_redis'] = True
            except:
                pass
        
        if self.tier2_archive:
            try:
                await self.tier2_archive.ping()
                health['tier2_postgresql'] = True
            except:
                pass
        
        if self.tier3_semantic:
            try:
                await self.tier3_semantic.ping()
                health['tier3_chromadb'] = True
            except:
                pass
        
        if self.tier4_graph:
            try:
                await self.tier4_graph.ping()
                health['tier4_neo4j'] = True
            except:
                pass
        
        # Overall health if at least 2 tiers are working
        working_tiers = sum(health[key] for key in health if key != 'overall_healthy')
        health['overall_healthy'] = working_tiers >= 2
        
        return health