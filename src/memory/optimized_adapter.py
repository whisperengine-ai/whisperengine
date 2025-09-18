"""
Memory Performance Integration Adapter

This module provides seamless integration between the memory performance optimizer
and the existing WhisperEngine memory system. It acts as a bridge layer that
maintains backward compatibility while adding performance optimizations.

Key features:
- Drop-in replacement for existing memory operations
- Automatic optimization based on usage patterns
- Configurable optimization levels per environment
- Performance monitoring integration
- Graceful fallback to original methods
"""

import logging
import os
from typing import Any

from src.memory.performance_optimizer import (
    MemoryPerformanceOptimizer,
    QueryOptimizationLevel,
)

logger = logging.getLogger(__name__)


class OptimizedMemoryAdapter:
    """
    Adapter that integrates memory performance optimization with existing systems
    """

    def __init__(
        self,
        chromadb_manager,
        enable_optimization: bool | None = None,
        optimization_level: str | None = None,
        cache_size: int | None = None,
        monitoring_enabled: bool | None = None,
    ):
        """
        Initialize optimized memory adapter

        Args:
            chromadb_manager: Existing ChromaDB manager instance
            enable_optimization: Whether to enable optimization (auto-detect if None)
            optimization_level: Optimization level (minimal/standard/aggressive)
            cache_size: Cache size (auto-configure if None)
            monitoring_enabled: Enable performance monitoring (auto-detect if None)
        """
        self.chromadb_manager = chromadb_manager

        # Auto-configure optimization settings from environment
        self.enable_optimization = self._determine_optimization_enabled(enable_optimization)
        self.optimization_level = self._determine_optimization_level(optimization_level)
        self.cache_size = self._determine_cache_size(cache_size)
        self.monitoring_enabled = self._determine_monitoring_enabled(monitoring_enabled)

        # Initialize optimizer if enabled
        self.optimizer = None
        if self.enable_optimization:
            try:
                self.optimizer = MemoryPerformanceOptimizer(
                    chromadb_manager=chromadb_manager,
                    cache_max_size=self.cache_size,
                    cache_ttl_seconds=300,
                    batch_size=50,
                    optimization_level=QueryOptimizationLevel(self.optimization_level),
                    enable_monitoring=self.monitoring_enabled,
                )
                logger.info(f"Memory optimization enabled: {self.optimization_level} level")
            except Exception as e:
                logger.warning(f"Failed to initialize memory optimizer: {e}")
                self.enable_optimization = False
                self.optimizer = None

        if not self.enable_optimization:
            logger.info("Memory optimization disabled - using original methods")

    # Main memory operations with optimization

    async def search_memories(
        self,
        query_text: str,
        user_id: str | None = None,
        limit: int = 5,
        doc_types: list[str] | None = None,
    ) -> list[dict]:
        """Search memories with optional optimization"""
        if self.optimizer:
            try:
                return await self.optimizer.search_memories_optimized(
                    query_text=query_text, user_id=user_id, limit=limit, doc_types=doc_types
                )
            except Exception as e:
                logger.warning(f"Optimized search failed, falling back: {e}")

        # Fallback to original method
        return await self.chromadb_manager.search_memories(query_text, user_id, limit, doc_types)

    async def store_conversation(
        self, user_id: str, message: str, response: str, metadata: dict | None = None
    ) -> str:
        """Store conversation with optional optimization"""
        if self.optimizer:
            try:
                return await self.optimizer.store_conversation_optimized(
                    user_id=user_id, message=message, response=response, metadata=metadata
                )
            except Exception as e:
                logger.warning(f"Optimized storage failed, falling back: {e}")

        # Fallback to original method
        return await self.chromadb_manager.store_conversation(user_id, message, response, metadata)

    async def store_user_fact(
        self,
        user_id: str,
        fact: str,
        category: str | None = None,
        confidence: float = 1.0,
        metadata: dict | None = None,
    ) -> str:
        """Store user fact (always use original method for consistency)"""
        return await self.chromadb_manager.store_user_fact(
            user_id, fact, category, confidence, metadata
        )

    async def store_global_fact(
        self,
        fact: str,
        category: str | None = None,
        confidence: float = 1.0,
        metadata: dict | None = None,
    ) -> str:
        """Store global fact (always use original method for consistency)"""
        return await self.chromadb_manager.store_global_fact(fact, category, confidence, metadata)

    async def get_user_conversations(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get user conversations with optional optimization"""
        if self.optimizer:
            try:
                return await self.optimizer.get_user_conversations_optimized(
                    user_id=user_id, limit=limit
                )
            except Exception as e:
                logger.warning(f"Optimized user conversations failed, falling back: {e}")

        # Fallback to original method
        return await self.chromadb_manager.get_user_conversations(user_id, limit)

    async def get_user_facts(
        self, user_id: str, category: str | None = None, limit: int = 20
    ) -> list[dict]:
        """Get user facts (always use original method for consistency)"""
        return await self.chromadb_manager.get_user_facts(user_id, category, limit)

    async def get_global_facts(self, category: str | None = None, limit: int = 20) -> list[dict]:
        """Get global facts (always use original method for consistency)"""
        return await self.chromadb_manager.get_global_facts(category, limit)

    # Embedding operations with optimization

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings with optional optimization"""
        if self.optimizer and len(texts) > 1:  # Only optimize batch requests
            try:
                return await self.optimizer.get_embeddings_optimized(texts)
            except Exception as e:
                logger.warning(f"Optimized embeddings failed, falling back: {e}")

        # Fallback to original method
        return await self.chromadb_manager.embedding_manager.get_embeddings(texts)

    # Performance and monitoring methods

    def get_performance_statistics(self) -> dict[str, Any]:
        """Get performance statistics"""
        base_stats = {
            "optimization_enabled": self.enable_optimization,
            "optimization_level": self.optimization_level,
            "cache_size": self.cache_size,
            "monitoring_enabled": self.monitoring_enabled,
        }

        if self.optimizer:
            optimizer_stats = self.optimizer.get_performance_statistics()
            base_stats.update(optimizer_stats)

        return base_stats

    async def cleanup_caches(self) -> dict[str, Any]:
        """Cleanup caches if optimization is enabled"""
        if self.optimizer:
            cleanup_results = await self.optimizer.cleanup_caches()
            return {"optimization_enabled": True, "cleanup_results": cleanup_results}

        return {"optimization_enabled": False, "message": "No caches to cleanup"}

    async def warm_up_cache(
        self, common_queries: list[str] | None = None, user_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """Warm up caches with common operations"""
        if not self.optimizer:
            return {"optimization_enabled": False, "message": "Cache warm-up not available"}

        # Use default queries if none provided
        if common_queries is None:
            common_queries = [
                "conversation history",
                "help with",
                "question about",
                "information",
                "remember when",
            ]

        if user_ids is None:
            user_ids = ["cache_warmup_user"]  # Dummy user for warm-up

        try:
            await self.optimizer.warm_up_cache(common_queries, user_ids)
            return {
                "optimization_enabled": True,
                "warmup_successful": True,
                "queries_processed": len(common_queries),
                "users_processed": len(user_ids),
            }
        except Exception as e:
            logger.warning(f"Cache warm-up failed: {e}")
            return {"optimization_enabled": True, "warmup_successful": False, "error": str(e)}

    def get_cache_summary(self) -> dict[str, Any]:
        """Get cache summary"""
        if self.optimizer:
            return self.optimizer.get_cache_summary()

        return {"optimization_enabled": False, "message": "No caches available"}

    # Configuration methods

    def _determine_optimization_enabled(self, explicit_value: bool | None) -> bool:
        """Determine if optimization should be enabled"""
        if explicit_value is not None:
            return explicit_value

        # Check environment variables
        env_enabled = os.getenv("ENABLE_MEMORY_OPTIMIZATION", "auto").lower()

        if env_enabled in ["true", "1", "yes", "on"]:
            return True
        elif env_enabled in ["false", "0", "no", "off"]:
            return False
        else:
            # Auto-detect based on environment
            # Enable optimization in production or when explicitly configured
            return (
                os.getenv("ENVIRONMENT", "").lower() in ["production", "prod"]
                or os.getenv("CHROMADB_HOST", "localhost") != "localhost"
            )

    def _determine_optimization_level(self, explicit_value: str | None) -> str:
        """Determine optimization level"""
        if explicit_value is not None:
            return explicit_value

        env_level = os.getenv("MEMORY_OPTIMIZATION_LEVEL", "auto").lower()

        if env_level in ["minimal", "standard", "aggressive"]:
            return env_level
        else:
            # Auto-detect based on environment
            environment = os.getenv("ENVIRONMENT", "").lower()

            if environment in ["production", "prod"]:
                return "standard"  # Balanced for production
            elif environment in ["development", "dev"]:
                return "minimal"  # Conservative for development
            else:
                return "standard"  # Default

    def _determine_cache_size(self, explicit_value: int | None) -> int:
        """Determine cache size"""
        if explicit_value is not None:
            return explicit_value

        # Get from environment or auto-configure
        env_size = os.getenv("MEMORY_CACHE_SIZE")
        if env_size:
            try:
                return int(env_size)
            except ValueError:
                pass

        # Auto-configure based on environment and available memory
        try:
            import psutil

            available_memory_gb = psutil.virtual_memory().total / (1024**3)

            if available_memory_gb >= 8:
                return 3000  # Large cache for systems with 8GB+ RAM
            elif available_memory_gb >= 4:
                return 2000  # Medium cache for systems with 4GB+ RAM
            else:
                return 1000  # Small cache for systems with <4GB RAM
        except Exception:
            return 1500  # Default if memory detection fails

    def _determine_monitoring_enabled(self, explicit_value: bool | None) -> bool:
        """Determine if monitoring should be enabled"""
        if explicit_value is not None:
            return explicit_value

        env_monitoring = os.getenv("ENABLE_MEMORY_MONITORING", "auto").lower()

        if env_monitoring in ["true", "1", "yes", "on"]:
            return True
        elif env_monitoring in ["false", "0", "no", "off"]:
            return False
        else:
            # Auto-enable monitoring in development and production
            environment = os.getenv("ENVIRONMENT", "").lower()
            return environment in ["development", "dev", "production", "prod"]

    # Backward compatibility methods

    async def initialize(self):
        """Initialize the adapter (for compatibility)"""
        if hasattr(self.chromadb_manager, "initialize"):
            await self.chromadb_manager.initialize()

    @property
    def client(self):
        """Access underlying ChromaDB client"""
        return getattr(self.chromadb_manager, "client", None)

    @property
    def user_collection(self):
        """Access user collection"""
        return getattr(self.chromadb_manager, "user_collection", None)

    @property
    def global_collection(self):
        """Access global collection"""
        return getattr(self.chromadb_manager, "global_collection", None)

    @property
    def embedding_manager(self):
        """Access embedding manager"""
        return getattr(self.chromadb_manager, "embedding_manager", None)

    def __getattr__(self, name):
        """Delegate unknown attributes to underlying manager"""
        return getattr(self.chromadb_manager, name)


# Utility functions for easy integration


async def create_optimized_memory_manager() -> OptimizedMemoryAdapter:
    """
    Create an optimized memory manager instance using HTTP ChromaDB

    Returns:
        OptimizedMemoryAdapter instance
    """
    # Always use HTTP manager for containerized ChromaDB
    from src.memory.chromadb_http_manager import ChromaDBHTTPManager

    manager = ChromaDBHTTPManager()
    await manager.initialize()

    # Create optimized adapter
    return OptimizedMemoryAdapter(manager)


def get_optimization_configuration() -> dict[str, Any]:
    """Get current optimization configuration from environment"""
    return {
        "optimization_enabled": os.getenv("ENABLE_MEMORY_OPTIMIZATION", "auto"),
        "optimization_level": os.getenv("MEMORY_OPTIMIZATION_LEVEL", "auto"),
        "cache_size": os.getenv("MEMORY_CACHE_SIZE", "auto"),
        "monitoring_enabled": os.getenv("ENABLE_MEMORY_MONITORING", "auto"),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "chromadb_host": os.getenv("CHROMADB_HOST", "localhost"),
    }


# Global optimized manager instance for backward compatibility
_optimized_manager = None


async def get_optimized_chromadb_manager() -> OptimizedMemoryAdapter:
    """Get or create optimized ChromaDB manager instance"""
    global _optimized_manager
    if _optimized_manager is None:
        _optimized_manager = await create_optimized_memory_manager()
    return _optimized_manager
