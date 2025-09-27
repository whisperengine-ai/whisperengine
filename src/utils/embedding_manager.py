"""
Local Embedding Manager
High-performance local embedding processing using fastembed.
Optimized for WhisperEngine with FAISS compatibility and ultra-fast processing.
"""

import asyncio
import logging
import os
import time
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class LocalEmbeddingManager:
    """
    Local-only embedding manager optimized for WhisperEngine.
    Uses fastembed for fast, high-quality embeddings with fewer dependencies.
    """

    def __init__(self):
        """Initialize the local embedding manager with optimal models"""

        # Model configuration - optimized for speed and quality
        self.embedding_model_name = os.getenv(
            "EMBEDDING_MODEL",
            "",  # Use FastEmbed default (BAAI/bge-small-en-v1.5) - no rate limits, 384-dim
        )

        # Fallback model (same as primary for consistency)
        self.fallback_model_name = os.getenv("FALLBACK_EMBEDDING_MODEL", self.embedding_model_name)

        # Performance settings
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))
        self.max_concurrent = int(
            os.getenv("EMBEDDING_MAX_CONCURRENT", "1")
        )  # Single model instance

        # Model caching and initialization
        self._model = None
        self._model_lock = asyncio.Lock()
        self._is_initialized = False

        # Performance tracking
        self.total_embeddings = 0
        self.total_time = 0.0
        self.cache_hits = 0

        # Embedding cache (LRU)
        self._embedding_cache = {}
        self.cache_max_size = int(os.getenv("EMBEDDING_CACHE_SIZE", "1000"))

        logger.info(f"LocalEmbeddingManager initialized with model: {self.embedding_model_name}")

    async def initialize(self):
        """Initialize the embedding model"""
        if self._is_initialized:
            return

        async with self._model_lock:
            if self._is_initialized:
                return

            try:
                await self._load_model()
                self._is_initialized = True
                logger.info("✅ Local embedding model initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize embedding model: {e}")
                raise

    async def _load_model(self):
        """Load the fastembed model"""
        try:
            from fastembed import TextEmbedding
            import os

            # Load in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def load_model_safely():
                # Get FastEmbed cache directory
                fastembed_cache_dir = os.getenv("FASTEMBED_CACHE_PATH", "/root/.cache/fastembed")
                
                # Check for pre-bundled models first (Docker environment)
                model_cache_dir = os.getenv("MODEL_CACHE_DIR", "/app/models")
                bundled_model_path = os.path.join(model_cache_dir, "embeddings")
                
                # Initialize fastembed model with proper cache configuration
                if os.path.exists(bundled_model_path):
                    logger.info("✅ Using pre-bundled models from: %s", bundled_model_path)
                    # Use the FastEmbed cache directory
                    if self.embedding_model_name:
                        model = TextEmbedding(
                            model_name=self.embedding_model_name,
                            cache_dir=fastembed_cache_dir
                        )
                    else:
                        # Use FastEmbed default model
                        model = TextEmbedding(cache_dir=fastembed_cache_dir)
                elif os.path.exists(self.embedding_model_name):
                    logger.info("Loading local model from: %s", self.embedding_model_name)
                    model = TextEmbedding(model_name=self.embedding_model_name, cache_dir=fastembed_cache_dir)
                else:
                    logger.warning("⚠️  No pre-bundled models found, downloading at runtime: %s", self.embedding_model_name)
                    if self.embedding_model_name:
                        model = TextEmbedding(model_name=self.embedding_model_name, cache_dir=fastembed_cache_dir)
                    else:
                        # Use FastEmbed default model
                        model = TextEmbedding(cache_dir=fastembed_cache_dir)
                
                return model
            
            self._model = await loop.run_in_executor(None, load_model_safely)

            # Test the model and get dimensions
            test_embedding = await self._encode_texts(["test"])
            self.embedding_dimension = len(test_embedding[0])

            logger.info("✅ Model loaded: %s", self.embedding_model_name)
            logger.info("   Embedding dimension: %s", self.embedding_dimension)
            logger.info("   Batch size: %s", self.batch_size)

        except ImportError:
            logger.error("❌ fastembed not available")
            raise
        except Exception as e:
            logger.error("❌ Model loading failed: %s", e)
            raise

    @lru_cache(maxsize=1000)
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return f"embed_{hash(text)}"

    async def _encode_texts(self, texts: list[str]) -> list[list[float]]:
        """Encode texts using fastembed"""
        if not self._model:
            await self.initialize()

        loop = asyncio.get_event_loop()

        # Run encoding in executor to avoid blocking
        def encode_with_fastembed():
            # fastembed returns a generator, convert to list
            embeddings = list(self._model.embed(texts))
            return [embedding.tolist() for embedding in embeddings]

        embeddings = await loop.run_in_executor(None, encode_with_fastembed)
        return embeddings

    async def get_embeddings(
        self, texts: str | list[str], use_cache: bool = True
    ) -> list[list[float]]:
        """
        Get embeddings for text(s) with local processing only

        Args:
            texts: Single text string or list of texts to embed
            use_cache: Whether to use embedding cache

        Returns:
            List of embedding vectors (even for single text input)
        """
        # Normalize input to list
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return []

        start_time = time.time()

        # Check cache first
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []

        if use_cache:
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    cached_embeddings.append((i, self._embedding_cache[cache_key]))
                    self.cache_hits += 1
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))

        # Generate embeddings for uncached texts
        new_embeddings = []
        if uncached_texts:
            new_embeddings = await self._encode_texts(uncached_texts)

            # Cache new embeddings
            if use_cache:
                for text, embedding in zip(uncached_texts, new_embeddings, strict=False):
                    cache_key = self._get_cache_key(text)

                    # Manage cache size
                    if len(self._embedding_cache) >= self.cache_max_size:
                        # Remove oldest entries (simple FIFO)
                        oldest_keys = list(self._embedding_cache.keys())[:100]
                        for key in oldest_keys:
                            del self._embedding_cache[key]

                    self._embedding_cache[cache_key] = embedding

        # Combine cached and new embeddings in correct order
        result_embeddings: list[list[float]] = [[] for _ in texts]

        # Fill in cached embeddings
        for i, embedding in cached_embeddings:
            result_embeddings[i] = embedding

        # Fill in new embeddings
        for i, idx in enumerate(uncached_indices):
            result_embeddings[idx] = new_embeddings[i]

        # Update performance tracking
        self.total_embeddings += len(texts)
        self.total_time += time.time() - start_time

        logger.debug(
            f"Generated {len(texts)} embeddings in {(time.time() - start_time)*1000:.2f}ms"
        )

        return result_embeddings

    async def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model"""
        if not self._is_initialized:
            await self.initialize()
        return self.embedding_dimension

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics"""
        avg_time_per_embedding = self.total_time / max(self.total_embeddings, 1) * 1000

        cache_hit_rate = self.cache_hits / max(self.total_embeddings, 1)

        return {
            "model_name": self.embedding_model_name,
            "embedding_dimension": getattr(self, "embedding_dimension", "unknown"),
            "total_embeddings": self.total_embeddings,
            "avg_time_per_embedding_ms": avg_time_per_embedding,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self._embedding_cache),
            "is_initialized": self._is_initialized,
        }

    async def warmup(self, sample_texts: list[str] | None = None):
        """Warm up the model with sample texts"""
        if not sample_texts:
            sample_texts = [
                "Hello, how are you today?",
                "I'm having a great conversation!",
                "Machine learning is fascinating.",
            ]

        logger.info("🔥 Warming up embedding model...")
        start_time = time.time()

        await self.get_embeddings(sample_texts)

        warmup_time = time.time() - start_time
        logger.info(f"✅ Model warmup completed in {warmup_time*1000:.2f}ms")

    async def shutdown(self):
        """Clean shutdown"""
        self._embedding_cache.clear()
        self._model = None
        self._is_initialized = False
        logger.info("✅ LocalEmbeddingManager shutdown complete")


# Create default instance
_default_manager = None


async def get_default_embedding_manager() -> LocalEmbeddingManager:
    """Get the default embedding manager instance"""
    global _default_manager
    if _default_manager is None:
        _default_manager = LocalEmbeddingManager()
        await _default_manager.initialize()
    return _default_manager


async def get_embeddings(texts: str | list[str]) -> list[list[float]]:
    """Convenience function for getting embeddings"""
    manager = await get_default_embedding_manager()
    return await manager.get_embeddings(texts)


# Test function
async def test_local_embeddings():
    """Test the local embedding system"""

    manager = LocalEmbeddingManager()
    await manager.warmup()

    # Test single embedding
    await manager.get_embeddings("Hello world!")

    # Test batch embedding
    batch_texts = ["Hello", "World", "AI", "Embeddings"] * 5
    start_time = time.time()
    await manager.get_embeddings(batch_texts)
    batch_time = time.time() - start_time

    # Test caching
    start_time = time.time()
    await manager.get_embeddings(batch_texts)  # Should be cached
    cache_time = time.time() - start_time

    # Show stats
    stats = manager.get_performance_stats()
    for _key, _value in stats.items():
        pass

    await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(test_local_embeddings())