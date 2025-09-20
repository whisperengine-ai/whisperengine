# WhisperEngine Phantom Features Environment Variables Guide

**Version:** 1.0  
**Date:** September 19, 2025  
**Purpose:** Comprehensive guide to all phantom feature environment variables

## Overview

This guide documents all environment variables available for controlling WhisperEngine's phantom features - advanced AI capabilities that are implemented but can be enabled/disabled based on your needs and resource constraints.

## Core Environment & Mode Configuration

### 🎯 **Essential Runtime Configuration**

These core environment variables control WhisperEngine's fundamental runtime behavior and should be configured first:

#### `WHISPERENGINE_MODE` - Bot Architecture Mode
- **Default:** `single_bot`
- **Valid Options:**
  - `single_bot` - Single Discord bot instance (recommended)
  - `multi_bot` - Multi-bot scaling architecture for enterprise
  - `desktop` - Desktop application mode
- **Description:** Controls the fundamental architecture pattern
- **Resource Impact:** Minimal
- **Example:** `WHISPERENGINE_MODE=single_bot`

#### `ENVIRONMENT` - Runtime Environment
- **Default:** `development`
- **Valid Options:**
  - `development` - Development mode with debug features and detailed logging
  - `production` - Production mode with optimizations and error handling
  - `staging` - Staging environment for testing before production
  - `test` - Testing environment for automated tests
- **Description:** Controls logging levels, error handling, and performance optimizations
- **Resource Impact:** Production mode uses 10-20% fewer resources
- **Example:** `ENVIRONMENT=production`

#### `CONTAINER_MODE` - Container Detection
- **Default:** Auto-detected
- **Valid Options:**
  - `true` - Running in Docker container
  - `false` - Running natively on host system
- **Description:** Affects file paths, networking, and resource management
- **Auto-Detection:** Automatically set based on container presence
- **Example:** `CONTAINER_MODE=true`

#### `DOCKER_ENV` - Docker Environment Detection
- **Default:** Auto-detected  
- **Valid Options:**
  - `true` - Docker environment with container networking
  - `false` - Non-Docker environment
- **Description:** Controls networking configuration and service discovery
- **Auto-Detection:** Set automatically by Docker Compose
- **Example:** `DOCKER_ENV=true`

#### `DEV_MODE` - Development Features
- **Default:** `false`
- **Valid Options:**
  - `true` - Enable hot-reload, debug endpoints, extended logging
  - `false` - Disable development features for performance
- **Description:** Enables/disables development-specific features
- **Resource Impact:** Dev mode uses 20-30% more memory for debugging
- **Example:** `DEV_MODE=true`

#### `MEMORY_SYSTEM_TYPE` - Memory Architecture ✨
- **Default:** `hierarchical`
- **Valid Options:**
  - `hierarchical` - 4-tier hierarchical memory (Redis → PostgreSQL → ChromaDB → Neo4j)
  - `experimental_v2` - Future experimental memory system (not implemented)
  - `test_mock` - Mock memory for testing
- **Description:** Controls which memory management system to use
- **Resource Impact:** Hierarchical uses full database stack
- **Recommendation:** Keep as `hierarchical` for best performance
- **Example:** `MEMORY_SYSTEM_TYPE=hierarchical`

### 🎯 **Recommended Configuration Presets**

#### **🛠️ Development Configuration**
```bash
WHISPERENGINE_MODE=single_bot
ENVIRONMENT=development
CONTAINER_MODE=true
DOCKER_ENV=true
DEV_MODE=true
MEMORY_SYSTEM_TYPE=hierarchical
```

#### **🚀 Production Configuration**
```bash
WHISPERENGINE_MODE=single_bot
ENVIRONMENT=production
CONTAINER_MODE=true
DOCKER_ENV=true
DEV_MODE=false
MEMORY_SYSTEM_TYPE=hierarchical
```

#### **🏠 Local Development (Native)**
```bash
WHISPERENGINE_MODE=single_bot
ENVIRONMENT=development
CONTAINER_MODE=false
DOCKER_ENV=false
DEV_MODE=true
MEMORY_SYSTEM_TYPE=hierarchical
```

---

## Quick Reference

| Feature Category | Basic Setup | Production Setup | Resource Impact |
|------------------|-------------|------------------|-----------------|
| **Emotion Processing** | Enable 1-2 features | Enable all features | Medium-High |
| **Conversation Management** | Enable thread manager only | Enable all features | High |
| **Topic Analysis** | Enable basic extractor | Enable all features | Medium |
| **Monitoring** | Enable basic monitoring | Enable full monitoring | Low |

## Environment Variables by Category

### 🧠 Advanced Emotion Processing

#### Core Emotion Features

##### `ENABLE_LOCAL_EMOTION_ENGINE`
- **Default:** `false`
- **Description:** High-performance emotion analysis using VADER + RoBERTa models
- **Impact:** Replaces basic emotion system with 5-10x faster processing
- **Resource Requirements:** 512MB RAM, 20% CPU
- **Dependencies:** Requires VADER and RoBERTa model downloads
- **Recommended for:** All environments where emotion analysis is important

**Example:**
```bash
ENABLE_LOCAL_EMOTION_ENGINE=true
```

##### `ENABLE_VECTORIZED_EMOTION_PROCESSOR`
- **Default:** `false`
- **Description:** Batch emotion processing using pandas optimization
- **Impact:** Enables processing of conversation history and emotion trending
- **Resource Requirements:** 1GB RAM, 40% CPU during batch operations
- **Dependencies:** Requires `ENABLE_LOCAL_EMOTION_ENGINE=true`
- **Recommended for:** Production environments with high conversation volume

**Example:**
```bash
ENABLE_VECTORIZED_EMOTION_PROCESSOR=true
VECTORIZED_EMOTION_MAX_WORKERS=4
```

##### `ENABLE_ADVANCED_EMOTION_DETECTOR`
- **Default:** `false`
- **Description:** Multi-modal emotion detection from text, emojis, and punctuation
- **Impact:** Detects 12+ emotion categories vs basic sentiment
- **Resource Requirements:** 128MB RAM, 5% CPU
- **Dependencies:** None (can work independently)
- **Recommended for:** All environments wanting detailed emotion analysis

**Example:**
```bash
ENABLE_ADVANCED_EMOTION_DETECTOR=true
```

#### Emotion Processing Performance Settings

##### `VECTORIZED_EMOTION_MAX_WORKERS`
- **Default:** `4`
- **Description:** Number of worker threads for batch emotion processing
- **Valid Range:** 1-16
- **Recommendation:** 
  - Development: 1-2
  - Production: 4-8
  - High-load: 8-16

##### `EMOTION_ANALYSIS_TIMEOUT`
- **Default:** `10`
- **Description:** Timeout in seconds for emotion analysis operations
- **Valid Range:** 5-60
- **Recommendation:**
  - Fast responses: 5-10
  - Thorough analysis: 15-30

##### `EMOTION_BATCH_PROCESSING_SIZE`
- **Default:** `16`
- **Description:** Number of messages to process in each batch
- **Valid Range:** 8-64
- **Impact:** Higher values = more memory usage but better throughput

### 💬 Advanced Conversation Management

#### Core Conversation Features

##### `ENABLE_PROACTIVE_ENGAGEMENT_ENGINE`
- **Default:** `false`
- **Description:** AI-driven conversation initiation based on user patterns
- **Impact:** Bot can start conversations proactively based on user behavior
- **Resource Requirements:** 256MB RAM, 15% CPU
- **Dependencies:** Requires personality profiler (already integrated)
- **Recommended for:** Production environments wanting dynamic engagement

**Example:**
```bash
ENABLE_PROACTIVE_ENGAGEMENT_ENGINE=true
PROACTIVE_ENGAGEMENT_CHECK_INTERVAL=300
```

##### `ENABLE_ADVANCED_THREAD_MANAGER`
- **Default:** `false`
- **Description:** Multi-thread conversation tracking and context management
- **Impact:** Enables sophisticated conversation threading and context switching
- **Resource Requirements:** 512MB RAM, 20% CPU
- **Dependencies:** None
- **Recommended for:** All environments with complex conversations

**Example:**
```bash
ENABLE_ADVANCED_THREAD_MANAGER=true
THREAD_MANAGER_MAX_ACTIVE_THREADS=10
```

##### `ENABLE_CONCURRENT_CONVERSATION_MANAGER`
- **Default:** `false`
- **Description:** Parallel conversation handling for multiple users
- **Impact:** Enables true multi-user concurrent conversations
- **Resource Requirements:** 1GB RAM, 30% CPU
- **Dependencies:** Requires `ENABLE_ADVANCED_THREAD_MANAGER=true`
- **Recommended for:** Production environments with multiple users

**Example:**
```bash
ENABLE_CONCURRENT_CONVERSATION_MANAGER=true
CONCURRENT_CONVERSATIONS_LIMIT=50
```

#### Conversation Performance Settings

##### `PROACTIVE_ENGAGEMENT_CHECK_INTERVAL`
- **Default:** `300` (5 minutes)
- **Description:** How often (in seconds) to check for engagement opportunities
- **Valid Range:** 60-3600
- **Recommendation:**
  - Active environments: 180-300
  - Quiet environments: 600-900

##### `THREAD_MANAGER_MAX_ACTIVE_THREADS`
- **Default:** `10`
- **Description:** Maximum number of concurrent conversation threads
- **Valid Range:** 1-100
- **Impact on Resources:** Each thread uses ~50MB RAM

##### `CONCURRENT_CONVERSATIONS_LIMIT`
- **Default:** `50`
- **Description:** Maximum number of parallel conversations
- **Valid Range:** 1-1000
- **Impact on Resources:** Each conversation uses ~20MB RAM

##### `CONVERSATION_CONTEXT_RETENTION_HOURS`
- **Default:** `72`
- **Description:** How long to retain detailed conversation context
- **Valid Range:** 1-168 (1 week)
- **Impact:** Longer retention = more memory usage

### 🔍 Advanced Topic Analysis

#### Topic Analysis Features

##### `ENABLE_ADVANCED_TOPIC_EXTRACTOR`
- **Default:** `false`
- **Description:** Sophisticated topic modeling and extraction from conversations
- **Impact:** Enables automatic topic detection and conversation categorization
- **Resource Requirements:** 512MB RAM, 25% CPU
- **Dependencies:** Requires NLP models
- **Recommended for:** Environments wanting conversation analytics

**Example:**
```bash
ENABLE_ADVANCED_TOPIC_EXTRACTOR=true
TOPIC_ANALYSIS_MIN_CONFIDENCE=0.7
```

#### Topic Analysis Settings

##### `TOPIC_ANALYSIS_MIN_CONFIDENCE`
- **Default:** `0.7`
- **Description:** Minimum confidence threshold for topic detection
- **Valid Range:** 0.1-1.0
- **Recommendation:**
  - Sensitive detection: 0.5-0.6
  - Balanced: 0.7-0.8
  - Conservative: 0.8-0.9

##### `TOPIC_CLUSTERING_MAX_TOPICS`
- **Default:** `10`
- **Description:** Maximum number of topics to extract from conversations
- **Valid Range:** 1-50
- **Impact:** More topics = more processing time and memory

##### `TOPIC_SIMILARITY_THRESHOLD`
- **Default:** `0.75`
- **Description:** Threshold for grouping similar topics
- **Valid Range:** 0.1-1.0
- **Impact:** Lower values = more topic grouping

### 📊 Monitoring & Performance

#### Monitoring Features

##### `ENABLE_PHANTOM_FEATURE_MONITORING`
- **Default:** `true`
- **Description:** Enable monitoring and metrics collection for phantom features
- **Impact:** Provides performance metrics and health monitoring
- **Resource Requirements:** 64MB RAM, 2% CPU
- **Recommended for:** All environments

##### `PHANTOM_FEATURES_PERFORMANCE_LOGGING`
- **Default:** `true`
- **Description:** Enable detailed performance logging for phantom features
- **Impact:** Provides detailed logs for troubleshooting and optimization
- **Log Level:** INFO and DEBUG
- **Recommended for:** Development and production

##### `PHANTOM_FEATURES_DETAILED_ANALYTICS`
- **Default:** `false`
- **Description:** Enable comprehensive analytics and reporting
- **Impact:** Collects detailed usage statistics and performance metrics
- **Resource Requirements:** 128MB RAM, 5% CPU
- **Recommended for:** Production environments wanting detailed insights

### 🔧 Performance & Resource Control

#### Resource Limits

##### `MAX_PHANTOM_FEATURE_MEMORY_MB`
- **Default:** `2048` (2GB)
- **Description:** Maximum memory allocation for all phantom features combined
- **Valid Range:** 256-8192
- **Recommendation:**
  - Development: 512-1024
  - Production: 2048-4096

##### `MAX_PHANTOM_FEATURE_CPU_PERCENT`
- **Default:** `60`
- **Description:** Maximum CPU usage percentage for phantom features
- **Valid Range:** 10-90
- **Recommendation:**
  - Shared environments: 30-50
  - Dedicated environments: 60-80

#### Performance Optimization

##### `PHANTOM_FEATURES_ASYNC_PROCESSING`
- **Default:** `true`
- **Description:** Enable asynchronous processing for phantom features
- **Impact:** Better performance and responsiveness
- **Recommended for:** All environments

##### `PHANTOM_FEATURES_CONNECTION_POOLING`
- **Default:** `true`
- **Description:** Enable database connection pooling for phantom features
- **Impact:** Better database performance and resource usage
- **Recommended for:** Production environments

##### `PHANTOM_FEATURES_RESULT_CACHING`
- **Default:** `true`
- **Description:** Enable result caching for phantom feature operations
- **Impact:** Faster responses for repeated operations
- **Memory Impact:** Increases memory usage by ~10-20%

### 🛡️ Security & Privacy

#### Security Features

##### `PHANTOM_FEATURES_ENCRYPTION_ENABLED`
- **Default:** `true`
- **Description:** Enable encryption for phantom feature data storage
- **Impact:** Ensures data security at rest and in transit
- **Performance Impact:** ~5% CPU overhead
- **Recommended for:** Production environments

##### `PHANTOM_FEATURES_DATA_ANONYMIZATION`
- **Default:** `true`
- **Description:** Enable automatic data anonymization for phantom features
- **Impact:** Removes or hashes PII from stored data
- **Recommended for:** All environments handling user data

##### `PHANTOM_FEATURES_AUDIT_LOGGING`
- **Default:** `false`
- **Description:** Enable comprehensive audit logging for phantom features
- **Impact:** Logs all phantom feature operations for compliance
- **Storage Impact:** Significant log storage requirements
- **Recommended for:** Compliance-required environments

#### Privacy Controls

##### `PHANTOM_FEATURES_DATA_RETENTION_DAYS`
- **Default:** `90`
- **Description:** Number of days to retain phantom feature data
- **Valid Range:** 1-365
- **Impact:** Longer retention = more storage requirements
- **Compliance:** Consider local data protection regulations

##### `PHANTOM_FEATURES_CONSENT_REQUIRED`
- **Default:** `true`
- **Description:** Require user consent before processing with phantom features
- **Impact:** May require additional user interaction
- **Recommended for:** All environments in regulated jurisdictions

## Configuration Templates

### Development Configuration
```bash
# Minimal phantom features for development
ENABLE_LOCAL_EMOTION_ENGINE=true
ENABLE_ADVANCED_EMOTION_DETECTOR=true
ENABLE_ADVANCED_THREAD_MANAGER=true
ENABLE_PHANTOM_FEATURE_MONITORING=true

# Conservative resource limits
MAX_PHANTOM_FEATURE_MEMORY_MB=512
MAX_PHANTOM_FEATURE_CPU_PERCENT=25
VECTORIZED_EMOTION_MAX_WORKERS=1
THREAD_MANAGER_MAX_ACTIVE_THREADS=3
```

### Production Configuration
```bash
# Full phantom features for production
ENABLE_LOCAL_EMOTION_ENGINE=true
ENABLE_VECTORIZED_EMOTION_PROCESSOR=true
ENABLE_ADVANCED_EMOTION_DETECTOR=true
ENABLE_PROACTIVE_ENGAGEMENT_ENGINE=true
ENABLE_ADVANCED_THREAD_MANAGER=true
ENABLE_CONCURRENT_CONVERSATION_MANAGER=true
ENABLE_ADVANCED_TOPIC_EXTRACTOR=true
ENABLE_PHANTOM_FEATURE_MONITORING=true

# Production resource settings
MAX_PHANTOM_FEATURE_MEMORY_MB=2048
MAX_PHANTOM_FEATURE_CPU_PERCENT=60
VECTORIZED_EMOTION_MAX_WORKERS=8
THREAD_MANAGER_MAX_ACTIVE_THREADS=50
CONCURRENT_CONVERSATIONS_LIMIT=200

# Performance optimization
PHANTOM_FEATURES_ASYNC_PROCESSING=true
PHANTOM_FEATURES_CONNECTION_POOLING=true
PHANTOM_FEATURES_RESULT_CACHING=true
```

### High-Performance Configuration
```bash
# Maximum performance phantom features
ENABLE_LOCAL_EMOTION_ENGINE=true
ENABLE_VECTORIZED_EMOTION_PROCESSOR=true
ENABLE_ADVANCED_EMOTION_DETECTOR=true
ENABLE_PROACTIVE_ENGAGEMENT_ENGINE=true
ENABLE_ADVANCED_THREAD_MANAGER=true
ENABLE_CONCURRENT_CONVERSATION_MANAGER=true
ENABLE_ADVANCED_TOPIC_EXTRACTOR=true

# High-performance settings
MAX_PHANTOM_FEATURE_MEMORY_MB=4096
MAX_PHANTOM_FEATURE_CPU_PERCENT=80
VECTORIZED_EMOTION_MAX_WORKERS=16
EMOTION_BATCH_PROCESSING_SIZE=64
THREAD_MANAGER_MAX_ACTIVE_THREADS=100
CONCURRENT_CONVERSATIONS_LIMIT=500

# Aggressive optimization
PHANTOM_FEATURES_ASYNC_PROCESSING=true
PHANTOM_FEATURES_CONNECTION_POOLING=true
PHANTOM_FEATURES_RESULT_CACHING=true
USE_GPU_EMOTION_PROCESSING=true  # If GPU available
```

### Resource-Constrained Configuration
```bash
# Minimal phantom features for resource-constrained environments
ENABLE_LOCAL_EMOTION_ENGINE=false  # Use basic emotion system
ENABLE_ADVANCED_EMOTION_DETECTOR=true  # Low resource impact
ENABLE_ADVANCED_THREAD_MANAGER=true   # Essential for conversation quality
ENABLE_PHANTOM_FEATURE_MONITORING=true

# Strict resource limits
MAX_PHANTOM_FEATURE_MEMORY_MB=256
MAX_PHANTOM_FEATURE_CPU_PERCENT=15
THREAD_MANAGER_MAX_ACTIVE_THREADS=2
EMOTION_ANALYSIS_TIMEOUT=5

# Disable resource-intensive features
ENABLE_VECTORIZED_EMOTION_PROCESSOR=false
ENABLE_CONCURRENT_CONVERSATION_MANAGER=false
PHANTOM_FEATURES_DETAILED_ANALYTICS=false
```

## Troubleshooting

### Common Issues

#### High Memory Usage
**Symptoms:** Bot using excessive memory  
**Solutions:**
- Reduce `MAX_PHANTOM_FEATURE_MEMORY_MB`
- Decrease `VECTORIZED_EMOTION_MAX_WORKERS`
- Disable `ENABLE_VECTORIZED_EMOTION_PROCESSOR`
- Lower `CONCURRENT_CONVERSATIONS_LIMIT`

#### Slow Response Times
**Symptoms:** Bot responding slowly to messages  
**Solutions:**
- Reduce `EMOTION_ANALYSIS_TIMEOUT`
- Enable `PHANTOM_FEATURES_ASYNC_PROCESSING`
- Enable `PHANTOM_FEATURES_RESULT_CACHING`
- Increase `VECTORIZED_EMOTION_MAX_WORKERS` (if not memory-constrained)

#### Phantom Features Not Working
**Symptoms:** Advanced features not functioning  
**Checks:**
1. Verify environment variables are set correctly
2. Check dependencies are enabled (e.g., LocalEmotionEngine before VectorizedProcessor)
3. Ensure resource limits aren't too restrictive
4. Check logs for error messages

### Performance Tuning Guide

#### For High-Volume Environments
```bash
# Optimize for throughput
VECTORIZED_EMOTION_MAX_WORKERS=8
EMOTION_BATCH_PROCESSING_SIZE=32
CONCURRENT_CONVERSATIONS_LIMIT=200
PHANTOM_FEATURES_CONNECTION_POOLING=true
```

#### For Low-Latency Environments
```bash
# Optimize for response time
EMOTION_ANALYSIS_TIMEOUT=5
PHANTOM_FEATURES_ASYNC_PROCESSING=true
PHANTOM_FEATURES_RESULT_CACHING=true
PROACTIVE_ENGAGEMENT_CHECK_INTERVAL=600  # Less frequent checks
```

#### For Memory-Constrained Environments
```bash
# Minimize memory usage
ENABLE_VECTORIZED_EMOTION_PROCESSOR=false
CONCURRENT_CONVERSATIONS_LIMIT=10
THREAD_MANAGER_MAX_ACTIVE_THREADS=3
CONVERSATION_CONTEXT_RETENTION_HOURS=24
```

## Validation

Use the built-in configuration validation to check your phantom feature settings:

```bash
python validate_config.py --phantom-features
```

This will check for:
- Invalid environment variable values
- Missing dependencies
- Resource conflicts
- Performance recommendations

---

**Last Updated:** September 19, 2025  
**Next Review:** October 19, 2025  
**Maintained by:** WhisperEngine Development Team