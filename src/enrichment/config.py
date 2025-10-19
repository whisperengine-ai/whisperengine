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
- ENRICHMENT_INTERVAL_SECONDS: How often to run enrichment cycle (default: 300)
- ENRICHMENT_BATCH_SIZE: Messages to process per batch (default: 50)
- LLM_MODEL: Model to use for enrichment (default: anthropic/claude-3.5-sonnet)
- OPENROUTER_API_KEY: OpenRouter API key for LLM access
"""

import os


class EnrichmentConfig:
    """Configuration for enrichment worker"""
    
    # Qdrant configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    
    # PostgreSQL configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "whisperengine_db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    
    # Enrichment settings
    ENRICHMENT_INTERVAL_SECONDS: int = int(os.getenv("ENRICHMENT_INTERVAL_SECONDS", "300"))
    ENRICHMENT_BATCH_SIZE: int = int(os.getenv("ENRICHMENT_BATCH_SIZE", "50"))
    
    # LLM configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet")
    # Support both OPENROUTER_API_KEY and LLM_CHAT_API_KEY (for compatibility)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_CHAT_API_KEY", "")
    
    # Processing thresholds
    MIN_MESSAGES_FOR_SUMMARY: int = int(os.getenv("MIN_MESSAGES_FOR_SUMMARY", "5"))
    TIME_WINDOW_HOURS: int = int(os.getenv("TIME_WINDOW_HOURS", "24"))
    LOOKBACK_DAYS: int = int(os.getenv("LOOKBACK_DAYS", "30"))
    
    @classmethod
    def get_postgres_dsn(cls) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY or LLM_CHAT_API_KEY environment variable is required")
        
        if not cls.POSTGRES_PASSWORD:
            raise ValueError("POSTGRES_PASSWORD environment variable is required")


# Create global config instance
config = EnrichmentConfig()
