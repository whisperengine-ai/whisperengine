"""
LLM Client Protocol and Factory for WhisperEngine

Provides a clean, extensible interface for LLM functionality with factory pattern
for simplified dependency injection and configuration management.
"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


def create_llm_client(
    llm_client_type: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Any:
    """
    Factory function to create LLM client instances.
    
    Args:
        llm_client_type: Type of LLM client ('openrouter', 'local', 'mock', 'disabled')
        api_url: Custom API URL (optional)
        api_key: Custom API key (optional)
        
    Returns:
        LLM client implementation (wrapped with concurrent safety)
    """
    if llm_client_type is None:
        llm_client_type = os.getenv("LLM_CLIENT_TYPE", "openrouter")
    
    llm_client_type = llm_client_type.lower()
    
    logger.info("Creating LLM client: %s", llm_client_type)
    
    if llm_client_type == "disabled":
        return NoOpLLMClient()
    
    elif llm_client_type in ["openrouter", "local", "ollama", "lmstudio"]:
        try:
            from src.llm.llm_client import LLMClient
            from src.llm.concurrent_llm_manager import ConcurrentLLMManager
            
            # Create base LLM client
            base_client = LLMClient(api_url=api_url, api_key=api_key)
            
            # Wrap with concurrent safety
            safe_client = ConcurrentLLMManager(base_client)
            
            logger.info("LLM client initialized with concurrent safety")
            return safe_client
            
        except ImportError as e:
            logger.warning("Failed to import LLM dependencies: %s", e)
            logger.info("Falling back to disabled LLM client")
            return NoOpLLMClient()
        except (OSError, RuntimeError, ValueError) as e:
            logger.error("Failed to initialize LLM client: %s", e)
            logger.info("Falling back to disabled LLM client")
            return NoOpLLMClient()
    
    elif llm_client_type == "mock":
        # For testing - could implement a mock LLM client
        logger.info("Mock LLM client not implemented, using disabled")
        return NoOpLLMClient()
    
    else:
        logger.warning("Unknown LLM client type: %s, using disabled", llm_client_type)
        return NoOpLLMClient()


class NoOpLLMClient:
    """No-operation LLM client for when LLM functionality is disabled."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def generate_chat_completion(self, messages, **kwargs):
        """No-op chat completion."""
        _ = messages, kwargs  # Unused arguments
        self.logger.debug("LLM client disabled - generate_chat_completion no-op")
        return {"choices": [{"message": {"content": "LLM functionality disabled"}}]}
    
    async def generate_completion(self, prompt, **kwargs):
        """No-op completion."""
        _ = prompt, kwargs  # Unused arguments
        self.logger.debug("LLM client disabled - generate_completion no-op")
        return {"choices": [{"text": "LLM functionality disabled"}]}
    
    def chat_completion_sync(self, messages, **kwargs):
        """No-op sync chat completion."""
        _ = messages, kwargs  # Unused arguments
        self.logger.debug("LLM client disabled - chat_completion_sync no-op")
        return {"choices": [{"message": {"content": "LLM functionality disabled"}}]}
    
    def completion_sync(self, prompt, **kwargs):
        """No-op sync completion."""
        _ = prompt, kwargs  # Unused arguments
        self.logger.debug("LLM client disabled - completion_sync no-op")
        return {"choices": [{"text": "LLM functionality disabled"}]}
    
    @property
    def api_url(self):
        """Mock API URL."""
        return "disabled://localhost"
    
    @property
    def api_key(self):
        """Mock API key."""
        return None