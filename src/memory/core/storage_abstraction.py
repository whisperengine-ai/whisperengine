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
        
        # Create embedding function using same logic as memory manager
        self.embedding_function = self._create_embedding_function()
    
    def _create_embedding_function(self):
        """Create embedding function for ChromaDB collections"""
        import os
        from chromadb.utils import embedding_functions
        
        use_local_models = os.getenv("USE_LOCAL_MODELS", "false").lower() == "true"
        local_models_dir = os.getenv("LOCAL_MODELS_DIR", "./models")
        embedding_model = os.getenv("LLM_LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        if use_local_models and os.path.exists(
            os.path.join(local_models_dir, embedding_model)
        ):
            # Use bundled local model
            model_path = os.path.join(local_models_dir, embedding_model)
            logger.info(f"HierarchicalMemory: Using bundled local embedding model: {model_path}")
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model_path
            )
        else:
            # Use online model (will download if not cached)
            logger.info(f"HierarchicalMemory: Using online embedding model: {embedding_model}")
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            )
    
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
                port=chroma_config.get('port', 8000),
                embedding_function=self.embedding_function
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
        """Generate enhanced summary for ChromaDB storage with instructional content preservation"""
        topics = self._extract_topics(user_message)
        intent = self._extract_intent(user_message)
        
        # Detect instructional/mentorship content
        is_instructional = self._is_instructional_content(bot_response)
        has_mentor_context = self._has_mentor_context(user_message, bot_response)
        
        topic_text = ", ".join(topics[:3]) if topics else "general conversation"
        
        if is_instructional or has_mentor_context:
            # Preserve more detail for instructional content
            summary = self._create_detailed_summary(user_message, bot_response, topics, intent)
            max_length = 300  # Allow longer summaries for instructional content
        else:
            # Standard summary for general conversations
            summary = f"User {intent} about {topic_text}. Bot provided assistance."
            max_length = 150
        
        return summary[:max_length]
    
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
    
    def _is_instructional_content(self, bot_response: str) -> bool:
        """Detect if bot response contains instructional/tutorial content"""
        import re
        response_lower = bot_response.lower()
        
        # Check for step-by-step patterns
        step_patterns = [
            r'step \d+', r'\d+\.\s', r'first[,\s]', r'second[,\s]', r'third[,\s]',
            r'next[,\s]', r'then[,\s]', r'finally[,\s]'
        ]
        if any(re.search(pattern, response_lower) for pattern in step_patterns):
            return True
            
        # Check for instructional keywords
        instructional_keywords = [
            'tutorial', 'guide', 'instruction', 'how to', 'pipeline', 'workflow',
            'technique', 'method', 'approach', 'strategy', 'tips', 'advice',
            'assignment', 'homework', 'practice', 'exercise'
        ]
        if any(keyword in response_lower for keyword in instructional_keywords):
            return True
            
        # Check for long detailed responses (likely instructional)
        return len(bot_response) > 500
    
    def _has_mentor_context(self, user_message: str, bot_response: str) -> bool:
        """Detect mentorship/coaching context"""
        combined_text = (user_message + " " + bot_response).lower()
        
        mentor_keywords = [
            'mentor', 'tyler', 'teacher', 'instructor', 'coach', 'tutor',
            'feedback', 'critique', 'review', 'session', 'lesson'
        ]
        return any(keyword in combined_text for keyword in mentor_keywords)
    
    def _create_detailed_summary(self, user_message: str, bot_response: str, topics: List[str], intent: str) -> str:
        """Create detailed summary preserving instructional content"""
        import re
        
        topic_text = ", ".join(topics[:3]) if topics else "general topic"
        
        # Extract key instructional elements
        steps = self._extract_steps(bot_response)
        techniques = self._extract_techniques(bot_response)
        assignments = self._extract_assignments(bot_response)
        
        # Build rich summary
        summary_parts = [f"User {intent} about {topic_text}."]
        
        if steps:
            summary_parts.append(f"Bot provided {len(steps)}-step guide:")
            summary_parts.append(" → ".join(steps[:3]))
            if len(steps) > 3:
                summary_parts.append("...")
        
        if techniques:
            summary_parts.append(f"Techniques: {', '.join(techniques[:3])}")
        
        if assignments:
            summary_parts.append(f"Assignment: {assignments[0]}")
        
        if not (steps or techniques or assignments):
            summary_parts.append("Bot provided detailed assistance.")
        
        return " ".join(summary_parts)
    
    def _extract_steps(self, text: str) -> List[str]:
        """Extract step-by-step instructions"""
        import re
        steps = []
        
        # Look for numbered steps
        step_matches = re.findall(r'(?:step \d+|^\d+\.)\s*[–—-]?\s*([^.!?]+)', text.lower(), re.MULTILINE)
        steps.extend([step.strip()[:50] for step in step_matches])
        
        # Look for bullet points or dashes
        bullet_matches = re.findall(r'[•\-*]\s*([^.!?\n]+)', text)
        steps.extend([step.strip()[:50] for step in bullet_matches])
        
        return steps[:5]  # Limit to 5 steps
    
    def _extract_techniques(self, text: str) -> List[str]:
        """Extract mentioned techniques or methods"""
        import re
        text_lower = text.lower()
        
        technique_patterns = [
            r'(gesture[^.!?]*)', r'(construction[^.!?]*)', r'(silhouette[^.!?]*)',
            r'(perspective[^.!?]*)', r'(composition[^.!?]*)', r'(anatomy[^.!?]*)',
            r'(shading[^.!?]*)', r'(rendering[^.!?]*)', r'(sketching[^.!?]*)'
        ]
        
        techniques = []
        for pattern in technique_patterns:
            matches = re.findall(pattern, text_lower)
            techniques.extend([match.strip()[:30] for match in matches])
        
        return list(set(techniques))[:3]  # Limit to 3 unique techniques
    
    def _extract_assignments(self, text: str) -> List[str]:
        """Extract assignments or homework"""
        import re
        text_lower = text.lower()
        
        assignment_patterns = [
            r'assignment[^.!?]*[.!?]',
            r'homework[^.!?]*[.!?]',
            r'for next time[^.!?]*[.!?]',
            r'by sunday[^.!?]*[.!?]',
            r'practice[^.!?]*[.!?]'
        ]
        
        assignments = []
        for pattern in assignment_patterns:
            matches = re.findall(pattern, text_lower)
            assignments.extend([match.strip()[:80] for match in matches])
        
        return assignments[:2]  # Limit to 2 assignments
    
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