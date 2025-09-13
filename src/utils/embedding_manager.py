"""
External Embedding Manager
Manages external embedding API calls with fallback to local embeddings.
Follows the same pattern as the LLM API manager for consistency.
"""

import aiohttp
import asyncio
import logging
import os
import numpy as np
from typing import List, Optional, Dict, Any, Union
import json
import time

logger = logging.getLogger(__name__)

class ExternalEmbeddingManager:
    """
    Manage external embedding API calls similar to LLM pattern.
    Supports OpenAI, Azure OpenAI, and local embedding servers.
    """
    
    def __init__(self):
        """Initialize the external embedding manager"""
        # Embedding service configuration - follow same pattern as LLM models
        # Fall back to LLM_CHAT_API_URL if LLM_EMBEDDING_API_URL is not provided
        self.embedding_api_url = (
            os.getenv("LLM_EMBEDDING_API_URL") or 
            os.getenv("LLM_CHAT_API_URL") or  # Fallback to main LLM API URL
            "http://localhost:1234/v1"
        )
        # Support both specific embedding API key and fallback to general keys
        self.embedding_api_key = (
            os.getenv("LLM_EMBEDDING_API_KEY") or 
            os.getenv("OPENAI_API_KEY") or  # Fallback for OpenAI API
            os.getenv("OPENROUTER_API_KEY")  # Fallback for OpenRouter API
        )
        self.embedding_model = os.getenv("LLM_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5")
        
        # Control whether to use external embeddings - auto-detect based on API URL configuration
        # This matches the pattern used in memory_manager.py for consistency
        self.use_external = (
            os.getenv("LLM_EMBEDDING_API_URL") is not None or
            os.getenv("USE_EXTERNAL_EMBEDDINGS", "false").lower() == "true" or
            (os.getenv("LLM_EMBEDDING_API_URL") is None and 
             os.getenv("LLM_CHAT_API_URL") is not None and
             self._supports_embeddings(os.getenv("LLM_CHAT_API_URL", "")))
        )
        
        # Batch processing settings
        self.max_batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
        self.max_retries = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("EMBEDDING_RETRY_DELAY", "1.0"))
        
        # Concurrency control - limit concurrent requests to prevent overwhelming APIs
        self.max_concurrent_requests = int(os.getenv("EMBEDDING_MAX_CONCURRENT", "5"))
        self._request_semaphore = None  # Will be initialized when needed
        
        # Adaptive throttling based on rate limit responses
        self._rate_limit_backoff = 1.0  # Current backoff multiplier
        self._consecutive_rate_limits = 0  # Track consecutive rate limit hits
        
        # Control fallback model loading
        self.load_fallback_models = os.getenv("LOAD_FALLBACK_EMBEDDING_MODELS", "true").lower() == "true"
        
        # Initialize local embedding fallback
        self._init_local_embeddings()
        
        logger.info(f"ExternalEmbeddingManager initialized - External: {self.use_external}")
    
    def _supports_embeddings(self, api_url: str) -> bool:
        """Check if the given API URL supports embedding endpoints"""
        if not api_url:
            return False
        
        # Check for known providers that support embeddings
        embedding_providers = [
            'openai.com',
            'api.openai.com', 
            'openrouter.ai',
            'api.anthropic.com',  # If they add embedding support
            'localhost',  # Local servers like LM Studio, Ollama
            '127.0.0.1',  # Local servers
            'host.docker.internal'  # Docker host reference
        ]
        
        return any(provider in api_url.lower() for provider in embedding_providers)
    
    def _init_local_embeddings(self):
        """Initialize local ChromaDB embeddings as fallback"""
        self.local_embedding_function = None
        
        if not self.use_external:
            try:
                from chromadb.utils import embedding_functions
                local_model = os.getenv("LLM_LOCAL_EMBEDDING_MODEL", "all-mpnet-base-v2")
                self.local_embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=local_model
                )
                logger.info(f"Local embedding model initialized: {local_model}")
            except ImportError as e:
                logger.error(f"Failed to import ChromaDB embedding functions: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize local embeddings: {e}")
        else:
            # Initialize local embeddings as fallback (only if enabled)
            if self.load_fallback_models:
                try:
                    from chromadb.utils import embedding_functions
                    local_model = os.getenv("FALLBACK_EMBEDDING_MODEL", "all-mpnet-base-v2")
                    self.local_embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=local_model
                    )
                    logger.info(f"Fallback embedding model initialized: {local_model}")
                except Exception as e:
                    logger.warning(f"Failed to initialize fallback embeddings: {e}")
            else:
                logger.info("Fallback embedding models disabled - external API required")
    
    async def get_embeddings(self, texts: Union[str, List[str]], 
                           batch_size: Optional[int] = None) -> List[List[float]]:
        """
        Get embeddings for text(s) with concurrency control and adaptive throttling
        
        Args:
            texts: Single text string or list of texts to embed
            batch_size: Override default batch size for processing
            
        Returns:
            List of embedding vectors (even for single text input)
        """
        # Normalize input to list
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []
        
        # Use local embeddings if external is disabled
        if not self.use_external:
            return self._get_local_embeddings(texts)
        
        # Initialize semaphore if needed
        if self._request_semaphore is None:
            self._request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        # Use provided batch size or default
        effective_batch_size = batch_size or self.max_batch_size
        
        all_embeddings = []
        
        # Process in batches for large requests with concurrency control
        for i in range(0, len(texts), effective_batch_size):
            batch = texts[i:i + effective_batch_size]
            
            # Use semaphore to limit concurrent requests
            async with self._request_semaphore:
                batch_embeddings = await self._get_external_embeddings_batch_with_throttling(batch)
                all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    async def _get_external_embeddings_batch_with_throttling(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings with adaptive throttling based on rate limit responses"""
        try:
            # Apply adaptive delay if we've been rate limited recently
            if self._rate_limit_backoff > 1.0:
                delay = (self._rate_limit_backoff - 1.0) * 0.5  # Scale back the delay
                logger.debug(f"Applying adaptive throttling delay: {delay:.2f}s")
                await asyncio.sleep(delay)
            
            # Make the actual request
            result = await self._get_external_embeddings_batch(texts)
            
            # Success - gradually reduce backoff
            if self._consecutive_rate_limits > 0:
                self._consecutive_rate_limits = max(0, self._consecutive_rate_limits - 1)
                self._rate_limit_backoff = max(1.0, self._rate_limit_backoff * 0.8)
                if self._rate_limit_backoff <= 1.1:  # Close enough to 1.0
                    self._rate_limit_backoff = 1.0
                    logger.debug("Rate limit backoff reset - API responding normally")
            
            return result
            
        except Exception as e:
            # Check if this was a rate limit error
            if "rate limit" in str(e).lower() or "429" in str(e):
                self._consecutive_rate_limits += 1
                # Exponential backoff, but cap it at reasonable limits
                self._rate_limit_backoff = min(8.0, self._rate_limit_backoff * 1.5)
                logger.warning(f"Rate limit detected, increasing backoff to {self._rate_limit_backoff:.1f}x")
            
            raise
    
    async def _get_external_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts from external API"""
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.embedding_api_key:
            headers["Authorization"] = f"Bearer {self.embedding_api_key}"
        
        # OpenAI-compatible embedding API format
        payload = {
            "input": texts,
            "model": self.embedding_model,
            "encoding_format": "float"
        }
        
        for attempt in range(self.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.embedding_api_url}/embeddings",
                        json=payload,
                        headers=headers,
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            embeddings = [item["embedding"] for item in data["data"]]
                            
                            logger.debug(f"Got {len(embeddings)} embeddings from external API")
                            return embeddings
                            
                        elif response.status == 429:  # Rate limited
                            error_text = await response.text()
                            wait_time = self.retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limited (attempt {attempt + 1}), waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                            
                        else:
                            error_text = await response.text()
                            logger.error(f"Embedding API error {response.status}: {error_text}")
                            if attempt == self.max_retries - 1:
                                # Last attempt failed, use fallback
                                logger.warning("All external embedding attempts failed, using fallback")
                                return self._get_local_embeddings(texts)
                            await asyncio.sleep(self.retry_delay)
                            
            except aiohttp.ClientError as e:
                logger.error(f"External embedding API connection error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    logger.warning("All external embedding attempts failed due to connection issues, using fallback")
                    return self._get_local_embeddings(texts)
                await asyncio.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"Unexpected error in external embedding API (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    logger.warning("All external embedding attempts failed due to unexpected error, using fallback")
                    return self._get_local_embeddings(texts)
                await asyncio.sleep(self.retry_delay)
        
        # Should not reach here, but fallback just in case
        return self._get_local_embeddings(texts)
    
    def _get_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Fallback to local ChromaDB embeddings"""
        if not self.local_embedding_function:
            logger.error("No local embedding function available")
            # Return zero vectors as last resort
            return [[0.0] * 768 for _ in texts]  # 768 is mpnet dimension
        
        try:
            embeddings = self.local_embedding_function(texts)
            logger.debug(f"Generated {len(embeddings)} local embeddings")
            
            # Convert to List[List[float]] if needed
            if embeddings and isinstance(embeddings[0], (list, np.ndarray)):
                # Ensure all values are regular Python floats
                return [[float(x) for x in embedding] for embedding in embeddings]
            else:
                # Handle other formats
                return [[float(x) for x in embedding] for embedding in embeddings]
            
        except Exception as e:
            logger.error(f"Local embedding generation failed: {e}")
            # Return zero vectors as last resort
            return [[0.0] * 768 for _ in texts]
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the current model
        
        Returns:
            Embedding dimension
        """
        if self.use_external:
            # Common dimensions for popular models
            model_dimensions = {
                "text-embedding-ada-002": 1536,
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "all-Mpnet-BASE-v2": 384,
                "all-mpnet-base-v2": 768,
                "text-embedding-nomic-embed-text-v1.5": 768,  # Nomic embed model
                "nomic-embed-text-v1.5": 768,  # Alternative name
            }
            return model_dimensions.get(self.embedding_model, 1536)  # Default to OpenAI dimension
        else:
            # Local model dimensions
            local_model = os.getenv("LLM_LOCAL_EMBEDDING_MODEL", "all-mpnet-base-v2")
            if "MiniLM" in local_model:
                return 384
            elif "mpnet" in local_model:
                return 768
            else:
                return 384  # Safe default
    
    def get_embeddings_sync(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Synchronous wrapper for get_embeddings that can be called from sync contexts
        
        Args:
            texts: Text(s) to embed
        
        Returns:
            List of embeddings
        """
        import asyncio
        import threading
        
        if isinstance(texts, str):
            texts = [texts]
        
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, run in a new thread
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(self.get_embeddings(texts))
                finally:
                    new_loop.close()
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        except RuntimeError:
            # No event loop running, we can use asyncio.run
            return asyncio.run(self.get_embeddings(texts))
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the embedding service connection
        
        Returns:
            Dict with connection test results
        """
        test_text = "Hello, this is a test embedding."
        
        try:
            if self.use_external:
                start_time = time.time()
                embeddings = await self.get_embeddings([test_text])
                end_time = time.time()
                
                return {
                    "success": True,
                    "service": "external",
                    "model": self.embedding_model,
                    "api_url": self.embedding_api_url,
                    "dimension": len(embeddings[0]) if embeddings else 0,
                    "response_time": end_time - start_time,
                    "message": "External embedding service connection successful"
                }
            else:
                start_time = time.time()
                embeddings = self._get_local_embeddings([test_text])
                end_time = time.time()
                
                return {
                    "success": True,
                    "service": "local",
                    "model": os.getenv("LLM_LOCAL_EMBEDDING_MODEL", "all-Mpnet-BASE-v2"),
                    "dimension": len(embeddings[0]) if embeddings else 0,
                    "response_time": end_time - start_time,
                    "message": "Local embedding service connection successful"
                }
                
        except Exception as e:
            return {
                "success": False,
                "service": "external" if self.use_external else "local",
                "error": str(e),
                "message": f"Embedding service connection failed: {e}"
            }
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        Get current embedding configuration information
        
        Returns:
            Dict with configuration details
        """
        return {
            "use_external": self.use_external,
            "embedding_api_url": self.embedding_api_url,
            "embedding_model": self.embedding_model,
            "local_model": os.getenv("LLM_LOCAL_EMBEDDING_MODEL", "all-mpnet-base-v2"),
            "max_batch_size": self.max_batch_size,
            "max_retries": self.max_retries,
            "has_api_key": bool(self.embedding_api_key),
            "has_local_function": bool(self.local_embedding_function)
        }


# Global instance for easy access
embedding_manager = ExternalEmbeddingManager()


# Convenience functions
async def get_embeddings(texts: Union[str, List[str]], 
                        batch_size: Optional[int] = None) -> List[List[float]]:
    """
    Convenience function for getting embeddings
    
    Args:
        texts: Text(s) to embed
        batch_size: Optional batch size override
        
    Returns:
        List of embedding vectors
    """
    return await embedding_manager.get_embeddings(texts, batch_size)


async def test_embedding_connection() -> Dict[str, Any]:
    """
    Convenience function for testing embedding connection
    
    Returns:
        Connection test results
    """
    return await embedding_manager.test_connection()


def get_embedding_config() -> Dict[str, Any]:
    """
    Convenience function for getting embedding configuration
    
    Returns:
        Configuration information
    """
    return embedding_manager.get_config_info()


def is_external_embedding_configured() -> bool:
    """
    Check if external embeddings should be used based on configuration.
    
    This function provides a consistent way to determine if external embeddings
    are configured across all modules. It checks:
    1. Explicit LLM_EMBEDDING_API_URL configuration
    2. Manual USE_EXTERNAL_EMBEDDINGS flag
    3. Fallback to LLM_CHAT_API_URL if it supports embeddings
    
    Returns:
        True if external embeddings should be used, False otherwise
    """
    # Explicit embedding API configuration
    if os.getenv("LLM_EMBEDDING_API_URL") is not None:
        return True
    
    # Manual override flag
    if os.getenv("USE_EXTERNAL_EMBEDDINGS", "false").lower() == "true":
        return True
    
    # Check if main LLM API supports embeddings and can be used as fallback
    llm_chat_url = os.getenv("LLM_CHAT_API_URL")
    if llm_chat_url:
        # Check for known providers that support embeddings
        embedding_providers = [
            'openai.com',
            'api.openai.com', 
            'openrouter.ai',
            'api.anthropic.com',  # If they add embedding support
            'localhost',  # Local servers like LM Studio, Ollama
            '127.0.0.1',  # Local servers
            'host.docker.internal'  # Docker host reference
        ]
        
        if any(provider in llm_chat_url.lower() for provider in embedding_providers):
            return True
    
    return False
