"""
WhisperEngine Enrichment Worker Configuration

Environment variables:
- QDRANT_HOST: Qdrant server host
- QDRANT_PORT: Qdrant server port
- POSTGRES_HOST: PostgreSQL host
- POSTGRES_PORT: PostgreSQL port
- POSTGRES_DB: PostgreSQL database name
- POSTGRES_USER: PostgreSQL username
- POSTGRES_PASSWORD: PostgreSQL password
- ENRICHMENT_INTERVAL_SECONDS: How often to run enrichment cycle (default: 660 = 11 minutes)
- ENRICHMENT_BATCH_SIZE: Messages to process per batch (default: 50)
- LLM_CHAT_API_KEY: API key for LLM access (standardized with main bot)
- LLM_CHAT_API_URL: LLM API URL (default: https://openrouter.ai/api/v1)
- LLM_CHAT_MODEL: Model for conversation summaries (default: anthropic/claude-sonnet-4.5)
- LLM_FACT_EXTRACTION_MODEL: Model for fact extraction (default: anthropic/claude-sonnet-4.5)
- LLM_TEMPERATURE: Temperature for summaries (default: 0.7)
- LLM_FACT_EXTRACTION_TEMPERATURE: Temperature for fact extraction (default: 0.2)
"""

import os


class EnrichmentConfig:
    """Configuration for enrichment worker"""
    
    # Qdrant configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Embedding model configuration (must match main bot)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    FASTEMBED_CACHE_PATH: str = os.getenv("FASTEMBED_CACHE_PATH", "/tmp/fastembed_cache")
    
    # PostgreSQL configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "whisperengine")  # Match bot config
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "whisperengine")  # Match bot config
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "whisperengine_password")  # Match bot config
    
    # Enrichment settings
    ENRICHMENT_INTERVAL_SECONDS: int = int(os.getenv("ENRICHMENT_INTERVAL_SECONDS", "660"))  # 11 minutes (prime number - avoids harmonic interference)
    ENRICHMENT_BATCH_SIZE: int = int(os.getenv("ENRICHMENT_BATCH_SIZE", "50"))
    
    # LLM configuration
    # Use same API key as main bot (standardized)
    LLM_API_KEY: str = os.getenv("LLM_CHAT_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")
    LLM_API_URL: str = os.getenv("LLM_CHAT_API_URL", "https://openrouter.ai/api/v1")
    
    # Separate models for different tasks (matches main bot pattern)
    # Summaries: High-quality conversational understanding
    LLM_CHAT_MODEL: str = os.getenv("LLM_CHAT_MODEL", "anthropic/claude-sonnet-4.5")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # Fact extraction: Can use cheaper model OR same high-quality model
    # Since enrichment runs async (no latency cost), we CAN afford Claude for better quality
    # But user can override to use GPT-3.5 if they prefer cost savings
    LLM_FACT_EXTRACTION_MODEL: str = os.getenv("LLM_FACT_EXTRACTION_MODEL", "anthropic/claude-sonnet-4.5")
    LLM_FACT_EXTRACTION_TEMPERATURE: float = float(os.getenv("LLM_FACT_EXTRACTION_TEMPERATURE", "0.2"))
    
    # Legacy compatibility
    OPENROUTER_API_KEY: str = LLM_API_KEY  # Deprecated, use LLM_CHAT_API_KEY
    
    # Processing thresholds
    MIN_MESSAGES_FOR_SUMMARY: int = int(os.getenv("MIN_MESSAGES_FOR_SUMMARY", "5"))
    TIME_WINDOW_HOURS: int = int(os.getenv("TIME_WINDOW_HOURS", "24"))
    LOOKBACK_DAYS: int = int(os.getenv("LOOKBACK_DAYS", "3"))  # Reduced from 30 to avoid massive backfill token burn
    
    @classmethod
    def get_postgres_dsn(cls) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration"""
        if not cls.LLM_API_KEY:
            raise ValueError("LLM_CHAT_API_KEY environment variable is required")
        
        if not cls.POSTGRES_PASSWORD:
            raise ValueError("POSTGRES_PASSWORD environment variable is required")


# Create global config instance
config = EnrichmentConfig()
