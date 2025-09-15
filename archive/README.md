# Archive - Native Backend Documentation

## Purpose

This archive contains documentation and files related to the **native backend integration** phase of WhisperEngine that was removed in September 2025 as part of an architectural simplification.

## What Was Archived

### Documentation Files (`docs/`)
- `MLX_INTEGRATION_GUIDE.md` - Complete MLX native backend integration guide
- `MLX_IMPLEMENTATION_SUMMARY.md` - Implementation summary for MLX native support
- `MLX_GUIDE.md` - MLX usage guide 
- `MLX_TESTING_GUIDE.md` - MLX testing procedures
- `OLLAMA_BACKEND_INTEGRATION_SUMMARY.md` - Ollama native backend implementation
- `OLLAMA_DOWNLOAD_INTEGRATION_SUMMARY.md` - Automatic Ollama download integration
- `TRANSPARENT_OLLAMA_INSTALLATION.md` - Transparent Ollama installation guide
- `UI_RESPONSIVENESS_ENHANCEMENT_SUMMARY.md` - UI enhancements referencing MLX backends

### Test Files (`tests/`)
- `test_mlx_backend.py` - MLX backend testing
- `test_ollama_integration.py` - Ollama native integration tests
- `test_ollama_complete.py` - Complete Ollama workflow tests
- `validate_mlx.sh` - MLX validation script

## Why These Were Archived

In September 2025, WhisperEngine underwent a major architectural simplification:

### Old Architecture (Archived)
- **Native Python Model Loading**: Direct loading of MLX and Ollama models in Python
- **Complex URL Schemes**: `mlx://` and `ollama://` custom protocols
- **Native Backend Classes**: MLXBackend and OllamaBackend Python classes
- **Auto-Installation**: Automatic Ollama installation and model downloads

### New Architecture (Current)
- **HTTP-Only APIs**: LM Studio, Ollama HTTP, OpenAI, OpenRouter
- **Standard Protocols**: All communication via HTTP/REST APIs
- **External Dependencies**: Users manage LM Studio/Ollama independently
- **Simplified Configuration**: No native Python model loading

## Decision Rationale

The native backend approach was removed because:

1. **Complexity**: Native backends introduced significant complexity
2. **Reliability**: HTTP APIs are more stable and predictable
3. **Maintenance**: External tools (LM Studio/Ollama) handle model management better
4. **Dependencies**: Reduced Python dependency conflicts
5. **User Experience**: Users prefer managing their own model servers

## HTTP-Only Architecture Benefits

- ✅ **Simpler Setup**: Users install LM Studio or Ollama separately
- ✅ **Better Reliability**: HTTP APIs are battle-tested
- ✅ **Easier Debugging**: Standard HTTP request/response patterns
- ✅ **Reduced Conflicts**: No complex Python ML dependencies
- ✅ **Flexible Deployment**: Works with any OpenAI-compatible API

## Migration Path

For users who had native backends configured:

```bash
# Old Native Configuration
LLM_CHAT_API_URL=mlx://microsoft/Phi-3-mini-4k-instruct-4bit
LLM_CHAT_API_URL=ollama://llama3.2:3b

# New HTTP Configuration  
LLM_CHAT_API_URL=http://localhost:1234/v1    # LM Studio
LLM_CHAT_API_URL=http://localhost:11434/v1   # Ollama HTTP
```

## Historical Context

This archive preserves the work done on native backend integration for:
- **Historical Reference**: Understanding the evolution of WhisperEngine
- **Code Archaeology**: Learning from implementation approaches
- **Feature Recovery**: If native backends ever need to be reconsidered

---

**Archive Date**: September 15, 2025  
**Branch**: `archive/native-backend-docs`  
**Reason**: Architectural simplification to HTTP-only APIs