# WhisperEngine Environment Variables Report

## Overview
This document catalogs all environment variables used in the WhisperEngine Python codebase, organized by functional category with their default values and descriptions.

---

## 🔧 Core Bot Configuration

### Discord Bot Settings
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `DISCORD_BOT_TOKEN` | *None* | **REQUIRED** Discord bot token for authentication | `src/core/config.py`, `src/core/bot_launcher.py` |
| `DISCORD_BOT_NAME` | `""` | Bot display name for identification and logging | `src/core/config.py`, `src/core/bot.py`, `src/memory/vector_memory_system.py` |
| `DISCORD_COMMAND_PREFIX` | `"!"` | Command prefix for Discord bot commands | `src/core/bot.py`, `src/handlers/events.py` |
| `DISCORD_HEARTBEAT_TIMEOUT` | `60.0` | Heartbeat timeout in seconds for Discord connection | `src/core/bot.py` |
| `DISCORD_CHUNK_GUILDS` | `false` | Whether to chunk guild member data on startup | `src/core/bot.py` |
| `DISCORD_HEARTBEAT_CHECK_INTERVAL` | `10.0` | Interval for Discord heartbeat checks in seconds | `src/core/bot.py` |
| `DISCORD_MESSAGE_TRACE` | `false` | Enable detailed message processing tracing | `src/handlers/events.py` |
| `DISCORD_RESPOND_MODE` | `"mention"` | Response mode: "mention", "all", etc. | `src/handlers/events.py` |
| `REQUIRE_DISCORD_MENTION` | `false` | Require bot mention to respond | `src/handlers/events.py` |

---

## 🤖 LLM Configuration

### Core LLM Settings
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `LLM_CLIENT_TYPE` | `"openrouter"` | LLM client implementation type | `src/llm/llm_protocol.py`, `src/core/bot.py` |
| `LLM_CHAT_API_URL` | `"http://localhost:1234/v1"` | Primary chat API endpoint URL | `src/llm/llm_client.py`, `src/core/config.py` |
| `LLM_CHAT_API_KEY` | `""` | API key for LLM chat service | `src/llm/llm_client.py`, `src/config/llm_config_validator.py` |
| `LLM_BASE_URL` | *None* | Base URL for LLM service | `src/config/llm_config_validator.py` |
| `LLM_API_KEY` | `""` | Legacy LLM API key | `src/core/config.py` |

### Model Configuration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `LLM_CHAT_MODEL` | *None* | Chat model name | `src/core/config.py`, `src/config/llm_config_validator.py` |
| `CHAT_MODEL_NAME` | *None* | Chat model name (legacy) | `src/core/config.py` |
| `LLM_EMOTION_MODEL` | *Uses chat model* | Model for emotion analysis | `src/llm/llm_client.py` |
| `LLM_FACTS_MODEL` | *Uses chat model* | Model for fact extraction | `src/llm/llm_client.py` |

### Token Limits
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `LLM_MAX_TOKENS_CHAT` | `4096` | Maximum tokens for chat responses | `src/llm/llm_client.py`, `src/security/llm_message_role_security.py` |
| `LLM_MAX_TOKENS_COMPLETION` | `1024` | Maximum tokens for completions | `src/llm/llm_client.py` |
| `LLM_MAX_TOKENS_EMOTION` | `200` | Maximum tokens for emotion analysis | `src/llm/llm_client.py` |
| `LLM_MAX_TOKENS_FACT_EXTRACTION` | `500` | Maximum tokens for fact extraction | `src/llm/llm_client.py` |
| `LLM_MAX_TOKENS_PERSONAL_INFO` | `400` | Maximum tokens for personal info extraction | `src/llm/llm_client.py` |
| `LLM_MAX_TOKENS_USER_FACTS` | `400` | Maximum tokens for user facts extraction | `src/llm/llm_client.py` |
| `MAX_SYSTEM_MESSAGE_LENGTH` | *calculated* | Maximum system message length | `src/llm/llm_client.py`, `src/security/llm_message_role_security.py` |

### API Configuration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `LLM_EMOTION_API_URL` | *Uses chat API* | Emotion analysis API endpoint | `src/llm/llm_client.py` |
| `LLM_EMOTION_API_KEY` | *Uses chat key* | Emotion analysis API key | `src/llm/llm_client.py` |
| `LLM_FACTS_API_URL` | *Uses chat API* | Facts extraction API endpoint | `src/llm/llm_client.py` |
| `LLM_FACTS_API_KEY` | *Uses chat key* | Facts extraction API key | `src/llm/llm_client.py` |
| `LLM_REQUEST_TIMEOUT` | `90` | Request timeout in seconds | `src/llm/llm_client.py` |
| `LLM_CONNECTION_TIMEOUT` | `10` | Connection timeout in seconds | `src/llm/llm_client.py` |
| `LLM_SUPPORTS_VISION` | `false` | Whether LLM supports vision/images | `src/llm/llm_client.py` |
| `LLM_VISION_MAX_IMAGES` | `5` | Maximum images per vision request | `src/llm/llm_client.py` |

### Concurrent Processing
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `LLM_MAX_WORKERS` | `max(3, cpu_count // 2)` | Max worker threads for LLM processing | `src/llm/concurrent_llm_manager.py` |
| `MAX_WORKER_THREADS` | `cpu_count * 2` | Maximum worker threads | `src/integration/production_system_integration.py`, `src/conversation/concurrent_conversation_manager.py` |
| `MAX_WORKER_PROCESSES` | `cpu_count` | Maximum worker processes | `src/integration/production_system_integration.py`, `src/conversation/concurrent_conversation_manager.py` |

---

## 🧠 Memory System Configuration

### Core Memory Settings
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `MEMORY_SYSTEM_TYPE` | `"vector"` | Memory system implementation type | `src/core/bot.py` |

### Vector Memory (Qdrant)
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `QDRANT_HOST` | `"localhost"` | Qdrant vector database host | `src/memory/memory_protocol.py` |
| `QDRANT_PORT` | `6334` | Qdrant vector database port | `src/memory/memory_protocol.py` |
| `QDRANT_COLLECTION_NAME` | `"whisperengine_memory"` | Qdrant collection name for memories | `src/memory/memory_protocol.py` |

### Embedding Configuration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `EMBEDDING_MODEL` | `"sentence-transformers/all-MiniLM-L6-v2"` | Embedding model for vector memory | `src/memory/memory_protocol.py`, `src/utils/embedding_manager.py` |
| `EMBEDDING_DEVICE` | `"cpu"` | Device for embedding computation | `src/memory/memory_protocol.py` |
| `VECTOR_DIMENSION` | `384` | Vector embedding dimension | `src/memory/memory_protocol.py` |
| `FALLBACK_EMBEDDING_MODEL` | *Uses primary model* | Fallback embedding model | `src/utils/embedding_manager.py` |
| `EMBEDDING_BATCH_SIZE` | `16` | Batch size for embedding operations | `src/utils/embedding_manager.py` |
| `EMBEDDING_MAX_CONCURRENT` | `1` | Max concurrent embedding operations | `src/utils/embedding_manager.py` |
| `EMBEDDING_CACHE_SIZE` | `1000` | Embedding cache size | `src/utils/embedding_manager.py` |
| `FASTEMBED_CACHE_PATH` | `"/root/.cache/fastembed"` | FastEmbed model cache directory | `src/memory/vector_memory_system.py`, `src/utils/embedding_manager.py` |

### Redis Configuration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `REDIS_HOST` | `"localhost"` | Redis server host | `src/memory/redis_profile_memory_cache.py`, `src/memory/memory_protocol.py` |
| `REDIS_PORT` | `6379` | Redis server port | `src/memory/redis_profile_memory_cache.py`, `src/memory/memory_protocol.py` |
| `REDIS_DB` | `0` | Redis database number | `src/memory/redis_profile_memory_cache.py` |
| `REDIS_TTL` | `1800` | Redis cache TTL in seconds | `src/memory/memory_protocol.py` |

---

## 🗃️ Database Configuration

### PostgreSQL Settings
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `USE_POSTGRESQL` | `false` | Enable PostgreSQL database | `src/database/database_integration.py`, `src/utils/emotion_manager.py` |
| `POSTGRES_HOST` | `"localhost"` | PostgreSQL server host | Multiple locations |
| `POSTGRES_PORT` | `5433` | PostgreSQL server port | Multiple locations |
| `POSTGRES_DB` | `"whisperengine"` | PostgreSQL database name | Multiple locations |
| `POSTGRES_USER` | `"whisperengine"` | PostgreSQL username | Multiple locations |
| `POSTGRES_PASSWORD` | `""` | PostgreSQL password | Multiple locations |
| `DB_POOL_SIZE` | `10` | Database connection pool size | `src/database/database_integration.py` |

### Database Cache Settings
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `USE_REDIS_CACHE` | `false` | Enable Redis caching | `src/database/database_integration.py` |

### Backup Configuration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `BACKUP_ENABLED` | `false` | Enable automatic backups | `src/database/database_integration.py` |
| `BACKUP_DIRECTORY` | `"./data/backups"` | Backup storage directory | `src/database/database_integration.py` |
| `BACKUP_MAX_FILES` | `5` | Maximum backup files to retain | `src/database/database_integration.py` |
| `BACKUP_COMPRESSION` | `true` | Enable backup compression | `src/database/database_integration.py` |
| `BACKUP_PATH` | `"./backups"` | Backup path for memory system | `src/memory/backup_manager.py` |
| `AUTO_BACKUP_INTERVAL_HOURS` | `24` | Backup interval in hours | `src/memory/backup_manager.py` |
| `BACKUP_RETENTION_COUNT` | `5` | Number of backups to retain | `src/memory/backup_manager.py` |

---

## 🎯 Character & AI Features

### Character System
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `CDL_DEFAULT_CHARACTER` | `"characters/default_assistant.json"` | Default character file path | Multiple locations |
| `BOT_SYSTEM_PROMPT_FILE` | `"./prompts/default.md"` | System prompt file path | `src/core/config.py` |

### Intelligence Features
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `EMOJI_ENABLED` | `true` | Enable emoji intelligence | `src/intelligence/cdl_emoji_integration.py` |
| `EMOJI_BASE_THRESHOLD` | `0.4` | Base threshold for emoji reactions | `src/intelligence/vector_emoji_intelligence.py` |
| `EMOJI_NEW_USER_THRESHOLD` | `0.3` | Threshold for new user emoji reactions | `src/intelligence/vector_emoji_intelligence.py` |

### Emotion Analysis
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ENHANCED_EMOTION_KEYWORD_WEIGHT` | `0.3` | Weight for keyword-based emotion analysis | `src/intelligence/enhanced_vector_emotion_analyzer.py` |
| `ENHANCED_EMOTION_SEMANTIC_WEIGHT` | `0.4` | Weight for semantic emotion analysis | `src/intelligence/enhanced_vector_emotion_analyzer.py` |
| `ENHANCED_EMOTION_CONTEXT_WEIGHT` | `0.3` | Weight for context-based emotion analysis | `src/intelligence/enhanced_vector_emotion_analyzer.py` |
| `ENHANCED_EMOTION_CONFIDENCE_THRESHOLD` | `0.3` | Confidence threshold for emotion detection | `src/intelligence/enhanced_vector_emotion_analyzer.py` |
| `ROBERTA_EMOTION_MODEL_NAME` | `"cardiffnlp/twitter-roberta-base-emotion-multilabel-latest"` | RoBERTa emotion model name | `src/intelligence/enhanced_vector_emotion_analyzer.py` |

---

## 🎤 Voice & Audio Configuration

### ElevenLabs TTS/STT
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ELEVENLABS_API_KEY` | *None* | ElevenLabs API key | `src/llm/elevenlabs_client.py`, `src/web/voice_api.py` |
| `ELEVENLABS_DEFAULT_VOICE_ID` | `"ked1vRAQW5Sk9vhZC3vI"` | Default voice ID for TTS | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_VOICE_STABILITY` | `0.5` | Voice stability setting | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_VOICE_SIMILARITY_BOOST` | `0.8` | Voice similarity boost | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_VOICE_STYLE` | `0.0` | Voice style setting (0.0 = most natural) | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_USE_SPEAKER_BOOST` | `true` | Enable speaker boost | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_TTS_MODEL` | `"eleven_monolingual_v1"` | TTS model to use | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_STT_MODEL` | `"eleven_speech_to_text_v1"` | STT model to use | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_REQUEST_TIMEOUT` | `30` | Request timeout in seconds | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_CONNECTION_TIMEOUT` | `10` | Connection timeout in seconds | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_OUTPUT_FORMAT` | `"mp3_44100_128"` | Audio output format | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_OPTIMIZE_STREAMING` | `2` | Streaming optimization level | `src/llm/elevenlabs_client.py` |
| `ELEVENLABS_USE_STREAMING` | `true` | Enable streaming audio | `src/llm/elevenlabs_client.py` |

### Voice Manager Settings
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `VOICE_SERVICE_TYPE` | `"discord_elevenlabs"` | Voice service implementation | `src/core/bot.py`, `src/voice/voice_protocol.py` |
| `VOICE_AUTO_JOIN` | `false` | Auto-join voice channels | `src/voice/voice_manager.py`, `src/handlers/status.py` |
| `VOICE_MAX_AUDIO_LENGTH` | `30` | Maximum audio length in seconds | `src/voice/voice_manager.py` |
| `VOICE_RESPONSE_DELAY` | `1.0` | Voice response delay in seconds | `src/voice/voice_manager.py` |
| `VOICE_JOIN_ANNOUNCEMENTS` | `true` | Announce when joining voice channels | `src/voice/voice_manager.py` |
| `VOICE_KEEPALIVE_INTERVAL` | `300` | Voice keepalive interval in seconds | `src/voice/voice_manager.py`, `src/handlers/voice.py` |
| `VOICE_HEARTBEAT_INTERVAL` | `30` | Voice heartbeat interval in seconds | `src/voice/voice_manager.py`, `src/handlers/voice.py` |
| `VOICE_MAX_RECONNECT_ATTEMPTS` | `3` | Maximum voice reconnection attempts | `src/voice/voice_manager.py`, `src/handlers/voice.py` |
| `VOICE_RECONNECT_DELAY` | `5.0` | Voice reconnection delay in seconds | `src/voice/voice_manager.py` |
| `VOICE_MAX_RESPONSE_LENGTH` | `300` | Maximum voice response length | `src/handlers/events.py` |
| `VOICE_USE_PATTERN_FALLBACK` | `false` | Use pattern fallback for voice channels | `src/handlers/events.py` |
| `VOICE_TEXT_CHANNELS` | `""` | Comma-separated voice text channels | `src/handlers/events.py` |
| `VOICE_RESPONSE_ENABLED` | `true` | Enable voice responses | `src/handlers/status.py` |

---

## 🌐 Vision & Media Configuration

### Vision Processing
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `VISION_SUMMARIZER_ENABLED` | `false` | Enable vision/image summarization | `src/vision/vision_summarizer.py` |
| `VISION_SUMMARIZER_API_URL` | `""` | Vision API endpoint URL | `src/vision/vision_summarizer.py` |
| `VISION_SUMMARIZER_MODEL` | `""` | Vision model name | `src/vision/vision_summarizer.py` |
| `VISION_SUMMARIZER_MAX_IMAGES` | `3` | Maximum images per request | `src/vision/vision_summarizer.py` |
| `VISION_SUMMARIZER_TIMEOUT` | `25` | Vision API timeout in seconds | `src/vision/vision_summarizer.py` |
| `VISION_SUMMARIZER_MAX_TOKENS` | `180` | Maximum tokens for vision responses | `src/vision/vision_summarizer.py` |
| `VISION_SUMMARIZER_TEMPERATURE` | `0.2` | Temperature for vision responses | `src/vision/vision_summarizer.py` |
| `VISION_SUMMARIZER_API_KEY` | `""` | Vision API authentication key | `src/vision/vision_summarizer.py` |

### Image Processing
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `TEMP_IMAGES_DIR` | `"temp_images"` | Temporary images directory | `src/utils/image_processor.py` |

---

## 🔒 Security & Privacy Configuration

### Security Settings
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `SECURITY_LOG_LEVEL` | `"quiet"` | Security logging level | `src/security/llm_message_role_security.py` |
| `ADMIN_USER_IDS` | *None* | Comma-separated admin user IDs | `src/utils/helpers.py` |

### Privacy Manager
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `POSTGRES_PRIVACY_MIN_CONNECTIONS` | `3` | Minimum privacy DB connections | `src/security/postgres_privacy_manager.py` |
| `POSTGRES_PRIVACY_MAX_CONNECTIONS` | `10` | Maximum privacy DB connections | `src/security/postgres_privacy_manager.py` |

---

## 📊 Monitoring & Analytics

### Metrics Collection
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ENABLE_METRICS_COLLECTION` | `true` | Enable metrics collection | `src/metrics/metrics_integration.py` |
| `ENABLE_AB_TESTING` | `false` | Enable A/B testing | `src/metrics/metrics_integration.py` |
| `ENABLE_METRICS_LOGGING` | `true` | Enable metrics logging | `src/metrics/metrics_collector.py` |

### Health Monitoring
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `HEALTH_CHECK_PORT` | `9090` | Health check server port | `src/main.py` |
| `HEALTH_CHECK_HOST` | `"0.0.0.0"` | Health check server host | `src/main.py` |
| `ENABLE_MONITORING_DASHBOARD` | `false` | Enable monitoring dashboard | `src/monitoring/__init__.py` |
| `DASHBOARD_HOST` | `"127.0.0.1"` | Dashboard host address | `src/monitoring/__init__.py` |
| `DASHBOARD_PORT` | `8080` | Dashboard port | `src/monitoring/__init__.py` |
| `DASHBOARD_DEBUG` | `false` | Enable dashboard debug mode | `src/monitoring/__init__.py` |
| `HEALTH_CHECK_INTERVAL` | `30` | Health check interval in seconds | `src/monitoring/__init__.py` |
| `HEALTH_FULL_CHECK_INTERVAL` | `300` | Full health check interval in seconds | `src/monitoring/__init__.py` |
| `HEALTH_MAX_HISTORY` | `100` | Maximum health check history entries | `src/monitoring/__init__.py` |

### Engagement Tracking
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ENGAGEMENT_DATA_DIR` | `"data/engagement"` | Engagement data directory | `src/monitoring/__init__.py` |
| `ENGAGEMENT_SESSION_TIMEOUT` | `30` | Session timeout in minutes | `src/monitoring/__init__.py` |
| `ENGAGEMENT_MAX_HISTORY_DAYS` | `90` | Maximum engagement history in days | `src/monitoring/__init__.py` |

### Error Tracking
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ERROR_DATA_DIR` | `"data/errors"` | Error data directory | `src/monitoring/__init__.py` |
| `ERROR_PATTERN_THRESHOLD` | `5` | Error pattern detection threshold | `src/monitoring/__init__.py` |
| `ERROR_MAX_HISTORY_DAYS` | `30` | Maximum error history in days | `src/monitoring/__init__.py` |

---

## 🚀 Deployment & Environment

### Environment Detection
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ENV_MODE` | *auto-detect* | Explicit environment mode | `src/utils/configuration_validator.py` |
| `DEPLOYMENT_MODE` | `"container"` | Deployment mode identifier | `src/database/database_integration.py` |
| `DOCKER_CONTAINER` | *None* | Docker container indicator | `src/database/simple_datastore_factory.py`, `src/analysis/deployment_config.py` |
| `CLOUD_PROVIDER` | *None* | Cloud provider indicator | `src/database/simple_datastore_factory.py`, `src/database/datastore_factory.py` |
| `KUBERNETES_SERVICE_HOST` | *None* | Kubernetes environment indicator | `src/database/simple_datastore_factory.py`, `src/database/datastore_factory.py` |
| `RUNNING_IN_DOCKER` | `false` | Docker runtime indicator | `src/web/simple_chat_app.py` |
| `CONTAINER_MODE` | *None* | Container mode indicator | `env_manager.py` |
| `DOCKER_ENV` | *None* | Docker environment indicator | `env_manager.py` |
| `DEV_MODE` | *None* | Development mode indicator | `env_manager.py` |

### Development Settings
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `DEBUG` | `false` | Enable debug mode | `src/platforms/universal_chat.py` |
| `DEBUG_MODE` | `false` | Debug mode flag | `env_manager.py` |
| `DEMO_BOT` | `false` | Demo bot mode | `src/main.py` |

---

## 🧪 Local LLM & Development

### Local Model Configuration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `LOCAL_LLM_MODEL` | `"microsoft_Phi-3-mini-4k-instruct"` | Local LLM model name | `src/llm/llm_client.py`, `src/utils/optimized_prompt_manager.py` |
| `LOCAL_MODELS_DIR` | `"./models"` | Local models directory | `src/llm/llm_client.py` |
| `MODEL_CACHE_DIR` | `"/app/models"` | Model cache directory | `src/utils/embedding_manager.py` |

### LlamaCpp Configuration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `LLAMACPP_MODEL_PATH` | *None* | Path to LlamaCpp model file | `src/llm/llm_client.py` |
| `LLAMACPP_USE_GPU` | `"auto"` | Enable GPU acceleration | `src/llm/llm_client.py` |
| `LLAMACPP_CONTEXT_SIZE` | `4096` | Context size for LlamaCpp | `src/llm/llm_client.py` |
| `LLAMACPP_THREADS` | `4` | Number of threads for LlamaCpp | `src/llm/llm_client.py` |

---

## 🔄 Conversation Management

### Concurrent Processing
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ENABLE_CONCURRENT_CONVERSATION_MANAGER` | `false` | Enable concurrent conversation manager | `src/core/bot.py` |
| `MAX_CONCURRENT_SESSIONS` | `1000` | Maximum concurrent sessions | `src/core/bot.py` |
| `SESSION_TIMEOUT_MINUTES` | `30` | Session timeout in minutes | `src/core/bot.py` |

### Engagement Engine
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ENGAGEMENT_ENGINE_TYPE` | `"full"` | Engagement engine implementation | `src/core/bot.py`, `src/conversation/engagement_protocol.py` |
| `ENGAGEMENT_STAGNATION_THRESHOLD_MINUTES` | `5` | Stagnation threshold in minutes | `src/conversation/proactive_engagement_engine.py` |
| `ENGAGEMENT_CHECK_INTERVAL_MINUTES` | `3` | Check interval in minutes | `src/conversation/proactive_engagement_engine.py` |
| `ENGAGEMENT_MAX_SUGGESTIONS_PER_HOUR` | `8` | Maximum suggestions per hour | `src/conversation/proactive_engagement_engine.py` |

---

## 🧪 Advanced AI Features

### Phase 3 Intelligence
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `CONTEXT_SWITCH_TOPIC_SHIFT_THRESHOLD` | `0.4` | Topic shift detection threshold | `src/intelligence/context_switch_detector.py` |
| `CONTEXT_SWITCH_EMOTIONAL_SHIFT_THRESHOLD` | `0.3` | Emotional shift detection threshold | `src/intelligence/context_switch_detector.py` |
| `CONTEXT_SWITCH_CONVERSATION_MODE_THRESHOLD` | `0.5` | Conversation mode threshold | `src/intelligence/context_switch_detector.py` |
| `CONTEXT_SWITCH_URGENCY_CHANGE_THRESHOLD` | `0.4` | Urgency change detection threshold | `src/intelligence/context_switch_detector.py` |
| `CONTEXT_SWITCH_MAX_MEMORIES` | `50` | Maximum memories for analysis | `src/intelligence/context_switch_detector.py` |
| `CONTEXT_SWITCH_ANALYSIS_TIMEOUT` | `60` | Analysis timeout in seconds | `src/intelligence/context_switch_detector.py` |

### Empathy Calibration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `EMPATHY_MIN_INTERACTIONS_FOR_CONFIDENCE` | `3` | Minimum interactions for empathy confidence | `src/intelligence/empathy_calibrator.py` |
| `EMPATHY_EFFECTIVENESS_THRESHOLD` | `0.6` | Empathy effectiveness threshold | `src/intelligence/empathy_calibrator.py` |
| `EMPATHY_LEARNING_RATE` | `0.1` | Empathy learning rate | `src/intelligence/empathy_calibrator.py` |
| `EMPATHY_CONFIDENCE_THRESHOLD` | `0.7` | Empathy confidence threshold | `src/intelligence/empathy_calibrator.py` |

### Feature Toggles
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `DISABLE_PHASE4_INTELLIGENCE` | `false` | Disable Phase 4 intelligence features | `src/handlers/events.py` |
| `DISABLE_PHASE2_EMOTION` | `false` | Disable Phase 2 emotion analysis | `src/handlers/events.py` |
| `DISABLE_PHASE3_CONTEXT_DETECTION` | `false` | Disable Phase 3 context detection | `src/handlers/events.py` |
| `DISABLE_PHASE3_EMPATHY_CALIBRATION` | `false` | Disable Phase 3 empathy calibration | `src/handlers/events.py` |
| `DISABLE_PERSONALITY_PROFILING` | `false` | Disable personality profiling | `src/handlers/events.py` |

---

## 📂 Logging & Output

### Logging Configuration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `LOG_LEVEL` | *None* | Global log level | `src/utils/logging_config.py` |
| `CONSOLE_LOG_LEVEL` | *None* | Console-specific log level | `src/utils/logging_config.py` |
| `FORCE_READABLE_LOGS` | `false` | Force human-readable log format | `src/utils/logging_config.py` |
| `LOG_TO_FILE` | `true` | Enable file logging | `src/utils/logging_config.py` |

---

## 🔧 Miscellaneous

### External API Keys
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `OPENAI_API_KEY` | *None* | OpenAI API key | `src/llm/smart_backend_selector.py` |
| `ANTHROPIC_API_KEY` | *None* | Anthropic API key | `src/llm/smart_backend_selector.py` |
| `ALLOWED_ORIGINS` | `'http://localhost:3000,http://localhost:8080'` | CORS allowed origins for API | `src/api/external_chat_api.py` |

### NLP & Processing
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `NLP_SPACY_MODEL` | `"en_core_web_lg"` | SpaCy model for NLP processing | `src/analysis/deployment_config.py` |

### Graph Database (Legacy)
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ENABLE_GRAPH_DATABASE` | `false` | Enable graph database features | `src/utils/graph_integrated_emotion_manager.py`, `src/examples/complete_integration_example.py` |
| `EMOTION_GRAPH_SYNC_INTERVAL` | `10` | Graph sync interval for emotions | `src/utils/graph_integrated_emotion_manager.py` |
| `FALLBACK_TO_EXISTING` | `true` | Fallback to existing system on graph failure | `src/utils/graph_integrated_emotion_manager.py` |

### ChromaDB (Legacy)
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `CHROMADB_HOST` | `"localhost"` | ChromaDB host | `src/memory/backup_manager.py` |
| `CHROMADB_PORT` | `8000` | ChromaDB port | `src/memory/backup_manager.py` |
| `CHROMADB_DATA_PATH` | `"./chromadb_data"` | ChromaDB data path | `src/memory/backup_manager.py` |

### Production Optimization
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `ENABLE_PRODUCTION_OPTIMIZATION` | `true` | Enable production optimizations | `src/integration/production_system_integration.py` |

---

## 🏗️ Temporal Intelligence (InfluxDB)

### InfluxDB Configuration
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `INFLUXDB_URL` | `"http://localhost:8086"` | InfluxDB server URL | `src/temporal/temporal_intelligence_client.py`, `src/monitoring/fidelity_metrics_collector.py` |
| `INFLUXDB_TOKEN` | *None* | InfluxDB authentication token | `src/temporal/temporal_intelligence_client.py`, `src/monitoring/fidelity_metrics_collector.py` |
| `INFLUXDB_ORG` | *None* | InfluxDB organization | `src/temporal/temporal_intelligence_client.py`, `src/monitoring/fidelity_metrics_collector.py` |
| `INFLUXDB_BUCKET` | *None* | InfluxDB bucket name | `src/temporal/temporal_intelligence_client.py`, `src/monitoring/fidelity_metrics_collector.py` |

---

## 💾 Memory Cache Configuration

### Conversation Cache
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `CONVERSATION_CACHE_TIMEOUT_MINUTES` | *varies* | Cache timeout in minutes | `src/memory/local_memory_cache.py` |
| `CONVERSATION_CACHE_BOOTSTRAP_LIMIT` | *varies* | Bootstrap limit for cache | `src/memory/local_memory_cache.py` |
| `CONVERSATION_CACHE_MAX_LOCAL` | *varies* | Maximum local cache entries | `src/memory/local_memory_cache.py` |

### Memory Management
| Variable | Default | Description | Location |
|----------|---------|-------------|----------|
| `MEMORY_DECAY_LAMBDA` | `0.01` | Memory decay rate for aging | `src/core/message_processor.py` |
| `MEMORY_PRUNE_THRESHOLD` | `0.2` | Threshold for memory pruning | `src/core/message_processor.py` |

---

## 🔧 Miscellaneous

---

## 📝 Notes

### Required Variables
The following variables are **required** for basic functionality:
- `DISCORD_BOT_TOKEN`
- `LLM_CHAT_API_URL`

### Recommended Variables
For production deployments, these variables should be configured:
- `REDIS_HOST`
- `POSTGRES_HOST`
- `QDRANT_HOST`

### Environment File Loading
The system loads environment variables in this order:
1. `DOTENV_PATH` (if specified)
2. Docker Compose environment variables
3. Local `.env` file overrides

### Auto-Detection
Many settings auto-detect appropriate defaults based on:
- Container environment detection (`/.dockerenv`, `DOCKER_CONTAINER`)
- Cloud environment detection (`CLOUD_PROVIDER`, `KUBERNETES_SERVICE_HOST`)
- Development indicators (`DEV_MODE`, `bot.sh` presence)

---

*Generated on: 2025-10-08*
*Total Variables Documented: 225+*
*Last Updated: Added missing environment variables (MEMORY_DECAY_LAMBDA, MEMORY_PRUNE_THRESHOLD, corrected ELEVENLABS defaults)*