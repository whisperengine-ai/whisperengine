"""
Custom exceptions for the Discord bot
"""

class BotError(Exception):
    """Base exception for bot-related errors"""
    pass

class LLMError(BotError):
    """LLM-related errors"""
    pass

class LLMConnectionError(LLMError):
    """Connection errors with LM Studio"""
    pass

class LLMTimeoutError(LLMError):
    """Timeout errors with LM Studio"""
    pass

class LLMRateLimitError(LLMError):
    """Rate limit errors with LM Studio"""
    pass

class MemoryError(BotError):
    """Memory management errors"""
    pass

class MemoryStorageError(MemoryError):
    """Errors storing data in ChromaDB"""
    pass

class MemoryRetrievalError(MemoryError):
    """Errors retrieving data from ChromaDB"""
    pass

class ValidationError(BotError):
    """Input validation errors"""
    pass

class ConfigurationError(BotError):
    """Configuration-related errors"""
    pass
