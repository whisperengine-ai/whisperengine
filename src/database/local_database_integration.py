#!/usr/bin/env python3
"""
Local Database Integration Manager
Manages all local database components for native WhisperEngine installations.

Components:
- SQLite for relational data (users, conversations, settings)
- Enhanced Local Vector Storage for embeddings (ChromaDB replacement)
- Local Graph Storage with NetworkX for relationships (Neo4j replacement)
- Redis-compatible local cache for session data
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import WhisperEngineDatabaseConfig, DatabaseIntegrationManager
from src.memory.enhanced_local_vector_storage import EnhancedLocalVectorStorage, ChromaDBCompatibilityLayer
from src.graph_database.local_graph_storage import LocalGraphStorage
from src.memory.desktop_conversation_cache import DesktopConversationCache

logger = logging.getLogger(__name__)


class LocalDatabaseIntegrationManager(DatabaseIntegrationManager):
    """
    Extended database integration manager for local native installations.
    
    Adds local replacements for external services:
    - Local vector storage instead of ChromaDB
    - Local graph storage instead of Neo4j
    - Local cache instead of Redis
    """
    
    def __init__(self, config_manager: AdaptiveConfigManager):
        super().__init__(config_manager)
        
        # Local storage components
        self.vector_storage: Optional[EnhancedLocalVectorStorage] = None
        self.chromadb_compat: Optional[ChromaDBCompatibilityLayer] = None
        self.graph_storage: Optional[LocalGraphStorage] = None
        self.local_cache: Optional[DesktopConversationCache] = None
        
        # Storage paths
        self.data_dir = Path.home() / '.whisperengine'
        self.vector_dir = self.data_dir / 'vectors'
        self.graph_db_path = self.data_dir / 'graph.db'
        self.cache_dir = self.data_dir / 'cache'
        
        # Ensure directories exist
        for directory in [self.data_dir, self.vector_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("LocalDatabaseIntegrationManager initialized")
    
    async def initialize(self) -> bool:
        """Initialize all local database components"""
        try:
            # Initialize base SQL database
            base_init_success = await super().initialize()
            if not base_init_success:
                logger.error("Failed to initialize base database")
                return False
            
            # Initialize vector storage (ChromaDB replacement)
            logger.info("🔍 Initializing local vector storage...")
            self.vector_storage = EnhancedLocalVectorStorage(
                storage_dir=self.vector_dir,
                embedding_dim=384  # Standard embedding dimension
            )
            
            # Create ChromaDB compatibility layer
            self.chromadb_compat = ChromaDBCompatibilityLayer(self.vector_storage)
            
            # Initialize graph storage (Neo4j replacement)
            logger.info("🕸️ Initializing local graph storage...")
            self.graph_storage = LocalGraphStorage(db_path=self.graph_db_path)
            await self.graph_storage.connect()
            
            # Initialize local cache (Redis replacement)
            logger.info("💾 Initializing local conversation cache...")
            self.local_cache = DesktopConversationCache()
            
            # Create default collections and setup
            await self._setup_default_collections()
            
            logger.info("✅ All local database components initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize local database components: {e}")
            return False
    
    async def _setup_default_collections(self):
        """Setup default vector collections and graph nodes"""
        try:
            # Create default vector collections
            default_collections = [
                ('conversations', {'description': 'User conversation embeddings'}),
                ('memories', {'description': 'AI memory embeddings'}),
                ('facts', {'description': 'Global fact embeddings'}),
                ('user_profiles', {'description': 'User profile embeddings'})
            ]
            
            for collection_name, metadata in default_collections:
                if collection_name not in self.vector_storage.collections:
                    self.vector_storage.create_collection(collection_name, metadata)
                    logger.debug(f"Created vector collection: {collection_name}")
            
            # Initialize system settings in graph
            system_user_id = "system_001"
            await self.graph_storage.create_or_update_user(
                user_id=system_user_id,
                discord_id="",
                username="system",
                display_name="WhisperEngine System"
            )
            
        except Exception as e:
            logger.warning(f"Failed to setup default collections: {e}")
    
    # ========== Vector Storage Interface ==========
    
    def get_vector_storage(self) -> EnhancedLocalVectorStorage:
        """Get the local vector storage instance"""
        if not self.vector_storage:
            raise RuntimeError("Vector storage not initialized")
        return self.vector_storage
    
    def get_chromadb_client(self) -> ChromaDBCompatibilityLayer:
        """Get ChromaDB-compatible client"""
        if not self.chromadb_compat:
            raise RuntimeError("ChromaDB compatibility layer not initialized")
        return self.chromadb_compat
    
    async def store_conversation_embedding(self, user_id: str, content: str, 
                                         embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store conversation embedding in local vector database"""
        try:
            doc_id = f"conv_{user_id}_{hash(content)}_{int(datetime.now().timestamp())}"
            
            doc = {
                'id': doc_id,
                'content': content,
                'metadata': {
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'conversation',
                    **(metadata or {})
                }
            }
            
            result = self.vector_storage.add_documents('conversations', [doc], [embedding])
            logger.debug(f"Stored conversation embedding: {doc_id}")
            
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to store conversation embedding: {e}")
            raise
    
    async def search_similar_conversations(self, query_embedding: List[float], 
                                         user_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar conversations using vector similarity"""
        try:
            where_filter = None
            if user_id:
                where_filter = {'user_id': user_id}
            
            results = self.vector_storage.query(
                'conversations', 
                query_embedding, 
                n_results=limit,
                where=where_filter,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results.get('documents') and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results.get('metadatas', [[]])[0]
                distances = results.get('distances', [[]])[0]
                
                for i, doc in enumerate(documents):
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadatas[i] if i < len(metadatas) else {},
                        'similarity': 1.0 - distances[i] if i < len(distances) else 0.0
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search similar conversations: {e}")
            return []
    
    # ========== Graph Storage Interface ==========
    
    def get_graph_storage(self) -> LocalGraphStorage:
        """Get the local graph storage instance"""
        if not self.graph_storage:
            raise RuntimeError("Graph storage not initialized")
        return self.graph_storage
    
    async def create_user_in_graph(self, user_id: str, username: str = "", **kwargs) -> Dict[str, Any]:
        """Create user node in graph database"""
        # Extract known parameters to avoid duplication in **kwargs
        discord_id = kwargs.pop('discord_id', '')
        display_name = kwargs.pop('display_name', username)
        avatar_url = kwargs.pop('avatar_url', '')
        
        return await self.graph_storage.create_or_update_user(
            user_id=user_id,
            discord_id=discord_id,
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
            **kwargs
        )
    
    async def store_memory_with_relationships(self, memory_id: str, user_id: str,
                                            content: str, topics: Optional[List[str]] = None,
                                            **kwargs) -> Dict[str, Any]:
        """Store memory with graph relationships"""
        return await self.graph_storage.create_memory_with_relationships(
            memory_id=memory_id,
            user_id=user_id,
            content=content,
            topics=topics or [],
            **kwargs
        )
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context from graph"""
        return await self.graph_storage.get_user_relationship_context(user_id)
    
    async def get_contextual_memories(self, user_id: str, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get contextual memories using graph traversal"""
        return await self.graph_storage.get_contextual_memories(user_id, topic, limit=limit)
    
    # ========== Cache Interface ==========
    
    def get_local_cache(self) -> DesktopConversationCache:
        """Get the local cache instance"""
        if not self.local_cache:
            raise RuntimeError("Local cache not initialized")
        return self.local_cache
    
    async def cache_conversation(self, user_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Cache conversation data locally"""
        try:
            # Create conversation ID for user
            conversation_id = f"user_{user_id}"
            
            # Add message to cache
            await self.local_cache.add_message(conversation_id, {
                'content': conversation_data.get('message', ''),
                'author_id': user_id,
                'author_name': conversation_data.get('username', 'User'),
                'timestamp': datetime.now().isoformat(),
                'bot': False,
                'metadata': conversation_data.get('metadata', {})
            })
            
            # Add response if available
            response = conversation_data.get('response')
            if response:
                await self.local_cache.add_message(conversation_id, {
                    'content': response,
                    'author_id': 'assistant',
                    'author_name': 'WhisperEngine',
                    'timestamp': datetime.now().isoformat(),
                    'bot': True,
                    'metadata': conversation_data.get('metadata', {})
                })
            
            return True
        except Exception as e:
            logger.error(f"Failed to cache conversation: {e}")
            return False
    
    async def get_cached_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get cached conversations for user"""
        try:
            # Use a dummy channel since we're in desktop mode
            channel = "desktop_app"
            context = await self.local_cache.get_user_conversation_context(
                channel=channel,
                user_id=int(hash(user_id) % (2**31)),  # Convert string user_id to int
                limit=limit
            )
            return context
        except Exception as e:
            logger.error(f"Failed to get cached conversations: {e}")
            return []
    
    # ========== Health and Monitoring ==========
    
    async def get_comprehensive_health_check(self) -> Dict[str, Any]:
        """Get health status of all database components"""
        # Initialize basic health data
        health_data: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'deployment_mode': 'local_native'
        }
        
        # Add base database health if available
        try:
            # Try to get database health directly
            if self.database_manager:
                health_data['database'] = {'status': 'connected', 'type': 'sqlite'}
            else:
                health_data['database'] = {'status': 'not_initialized'}
        except Exception as e:
            health_data['database'] = {'status': 'error', 'error': str(e)}
        
        # Add local component health
        try:
            # Vector storage health
            vector_stats = self.vector_storage.get_stats() if self.vector_storage else {'status': 'not_initialized'}
            health_data['vector_storage'] = {
                'status': 'healthy' if self.vector_storage else 'not_initialized',
                'stats': vector_stats
            }
            
            # Graph storage health
            graph_health = await self.graph_storage.health_check() if self.graph_storage else {'status': 'not_initialized'}
            health_data['graph_storage'] = graph_health
            
            # Cache health
            cache_stats = await self.local_cache.get_cache_stats() if self.local_cache else {'status': 'not_initialized'}
            health_data['local_cache'] = {
                'status': 'healthy' if self.local_cache else 'not_initialized',
                'stats': cache_stats
            }
            
            # Overall status
            components = [
                health_data.get('database', {}),
                health_data.get('vector_storage', {}), 
                health_data.get('graph_storage', {}),
                health_data.get('local_cache', {})
            ]
            
            all_healthy = all(
                comp.get('status') in ['healthy', 'connected'] 
                for comp in components if comp
            )
            
            health_data['overall_status'] = 'healthy' if all_healthy else 'degraded'
            health_data['deployment_mode'] = 'local_native'
            
        except Exception as e:
            logger.error(f"Error getting comprehensive health check: {e}")
            health_data['health_check_error'] = str(e)
        
        return health_data
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get detailed storage statistics for all components"""
        stats: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'deployment_mode': 'local_native',
            'data_directory': str(self.data_dir)
        }
        
        try:
            # Database stats
            if self.database_manager:
                stats['database'] = {
                    'type': 'sqlite',
                    'path': str(self.data_dir / 'database.db'),
                    'size_mb': self._get_file_size_mb(self.data_dir / 'database.db')
                }
            
            # Vector storage stats
            if self.vector_storage:
                stats['vector_storage'] = self.vector_storage.get_stats()
                stats['vector_storage']['path'] = str(self.vector_dir)
                stats['vector_storage']['size_mb'] = self._get_directory_size_mb(self.vector_dir)
            
            # Graph storage stats
            if self.graph_storage:
                graph_health = await self.graph_storage.health_check()
                stats['graph_storage'] = graph_health
                stats['graph_storage']['size_mb'] = self._get_file_size_mb(self.graph_db_path)
            
            # Cache stats
            if self.local_cache:
                cache_stats = await self.local_cache.get_cache_stats()
                stats['local_cache'] = cache_stats
                stats['local_cache']['path'] = str(self.cache_dir)
                stats['local_cache']['size_mb'] = self._get_directory_size_mb(self.cache_dir)
            
        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def _get_file_size_mb(self, file_path: Path) -> float:
        """Get file size in MB"""
        try:
            return file_path.stat().st_size / (1024 * 1024) if file_path.exists() else 0.0
        except:
            return 0.0
    
    def _get_directory_size_mb(self, dir_path: Path) -> float:
        """Get directory size in MB"""
        try:
            total_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
            return total_size / (1024 * 1024)
        except:
            return 0.0
    
    # ========== Cleanup ==========
    
    async def cleanup(self):
        """Cleanup all database connections and resources"""
        try:
            # Cleanup graph storage
            if self.graph_storage:
                await self.graph_storage.disconnect()
            
            # Cleanup cache
            if self.local_cache:
                await self.local_cache.close()
            
            # Cleanup base database
            await super().cleanup()
            
            logger.info("✅ Local database integration cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# ========== Factory Function ==========

def create_local_database_integration(config_manager: AdaptiveConfigManager) -> LocalDatabaseIntegrationManager:
    """Factory function to create local database integration manager"""
    return LocalDatabaseIntegrationManager(config_manager)


# ========== Example Usage ==========

async def example_usage():
    """Example usage of local database integration"""
    from src.config.adaptive_config import AdaptiveConfigManager
    
    # Create configuration
    config_manager = AdaptiveConfigManager()
    
    # Create local database integration
    db_integration = create_local_database_integration(config_manager)
    
    # Initialize all components
    success = await db_integration.initialize()
    print(f"Initialization success: {success}")
    
    if success:
        # Example: Store a conversation embedding
        fake_embedding = [0.1] * 384  # Placeholder embedding
        doc_id = await db_integration.store_conversation_embedding(
            user_id="user_123",
            content="Hello, how are you?",
            embedding=fake_embedding,
            metadata={"emotion": "friendly"}
        )
        print(f"Stored conversation: {doc_id}")
        
        # Example: Create user in graph
        user_result = await db_integration.create_user_in_graph(
            user_id="user_123",
            username="alice",
            display_name="Alice"
        )
        print(f"Created user: {user_result}")
        
        # Example: Get health check
        health = await db_integration.get_comprehensive_health_check()
        print(f"Health check: {health}")
        
        # Example: Get statistics
        stats = await db_integration.get_storage_statistics()
        print(f"Storage stats: {stats}")
        
        # Cleanup
        await db_integration.cleanup()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())