# API Key Configuration Guide

## Overview

This document provides a comprehensive overview of all API key configuration options available in the Discord bot. All API keys are configured via environment variables for security.

## 🔑 Supported API Key Variables

### Main LLM Services

| Variable | Purpose | Providers | Required |
|----------|---------|-----------|----------|
| `OPENAI_API_KEY` | OpenAI API access | OpenAI GPT models | When using OpenAI |
| `OPENROUTER_API_KEY` | OpenRouter API access | Multiple providers via OpenRouter | When using OpenRouter |
| `LLM_API_KEY` | Generic LLM API key | Any OpenAI-compatible API | When using generic API |

### Specialized LLM Services

| Variable | Purpose | Usage | Required |
|----------|---------|--------|----------|
| `LLM_EMOTION_API_KEY` | Emotion analysis service | Separate API key for emotion analysis | Optional |
| `LLM_FACTS_API_KEY` | Fact extraction service | Separate API key for fact extraction | Optional |

### Embedding Services

| Variable | Purpose | Usage | Required |
|----------|---------|--------|----------|
| `LLM_EMBEDDING_API_KEY` | External embeddings | High-quality embeddings via API | Optional |

### Voice Services

| Variable | Purpose | Usage | Required |
|----------|---------|--------|----------|
| `ELEVENLABS_API_KEY` | ElevenLabs voice synthesis | Text-to-speech functionality | When voice enabled |

## 🛠️ Configuration Examples

### OpenAI Configuration
```bash
# OpenAI for all services
LLM_CHAT_API_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=sk-your_openai_key_here

# OpenAI embeddings
LLM_EMBEDDING_API_URL=https://api.openai.com/v1
LLM_EMBEDDING_MODEL_NAME=text-embedding-3-small
LLM_EMBEDDING_API_KEY=sk-your_openai_key_here
```

### OpenRouter Configuration
```bash
# OpenRouter for LLM services
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=anthropic/claude-3.5-sonnet
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key_here

# OpenRouter embeddings
LLM_EMBEDDING_API_URL=https://openrouter.ai/api/v1
LLM_EMBEDDING_MODEL_NAME=text-embedding-nomic-embed-text-v1.5
LLM_EMBEDDING_API_KEY=sk-or-v1-your_openrouter_key_here
```

### Hybrid Configuration (Cost Optimization)
```bash
# Premium chat with OpenRouter
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=anthropic/claude-3.5-sonnet
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key_here

# Cheaper analysis with different provider
LLM_EMOTION_API_URL=https://api.openai.com/v1
LLM_EMOTION_MODEL_NAME=gpt-4o-mini
LLM_EMOTION_API_KEY=sk-your_openai_key_here

# Local embeddings (no API key needed)
# Leave LLM_EMBEDDING_API_URL unset to use local ChromaDB
```

### Voice Configuration
```bash
# Enable voice features
VOICE_SUPPORT_ENABLED=true
ELEVENLABS_API_KEY=sk_your_elevenlabs_key_here
```

## 🔒 Security Best Practices

### Environment Variable Security
- ✅ **DO**: Store API keys in `.env` files (never commit to git)
- ✅ **DO**: Use different API keys for development/production
- ✅ **DO**: Rotate API keys regularly
- ❌ **DON'T**: Hard-code API keys in source code
- ❌ **DON'T**: Share API keys in chat or documentation

### API Key Validation
The bot includes built-in API key validation that:
- Masks keys in logs for security
- Validates key format before use
- Detects potentially compromised keys
- Provides clear error messages for invalid keys

### Key Rotation
When rotating API keys:
1. Generate new key in provider dashboard
2. Update `.env` file with new key
3. Restart the bot
4. Delete old key from provider dashboard

## 🎯 Provider-Specific Instructions

### OpenAI Setup
1. Visit [platform.openai.com](https://platform.openai.com)
2. Create account and add billing information
3. Generate API key in API keys section
4. Add key to your `.env` file as `OPENAI_API_KEY`

### OpenRouter Setup
1. Visit [openrouter.ai](https://openrouter.ai)
2. Create account and add credits
3. Generate API key in settings
4. Add key to your `.env` file as `OPENROUTER_API_KEY`

### ElevenLabs Setup
1. Visit [elevenlabs.io](https://elevenlabs.io)
2. Create account 
3. Generate API key in profile settings
4. Add key to your `.env` file as `ELEVENLABS_API_KEY`

## 🔧 Troubleshooting

### Common Issues

**"API key not configured" errors:**
- Check that the correct API key variable is set
- Verify key format (should start with provider prefix)
- Ensure `.env` file is in the correct location

**"Invalid API key" errors:**
- Verify key is copied correctly (no extra spaces)
- Check that key hasn't been revoked
- Ensure account has sufficient credits/quota

**Mixed provider configurations:**
- Remember that different services can use different providers
- Each service needs its own API key if using separate providers
- Fallback chain: specific key → generic key → provider key

### Getting Help
- Use `!config` command in Discord to see current configuration
- Check bot logs for detailed error messages
- Verify configuration with `python validate_config.py`

## 📚 Related Documentation
- [External Embeddings Guide](archive/EXTERNAL_EMBEDDINGS_GUIDE.md)
- [Installation Guide](INSTALLATION.md)
- [Quick Start Guide](QUICK_START.md)
