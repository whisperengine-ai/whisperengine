# ⚠️ DEPRECATED: llama-cpp-python Integration for WhisperEngine

## ⚠️ **DEPRECATION NOTICE**
**This integration is no longer supported as of Sprint 6 (September 2025).** 

WhisperEngine now uses **LM Studio** and **Ollama** as the primary local AI backends instead of direct llama-cpp-python integration. 

**For current local AI setup, see:**
- **[LM Studio Setup](../deployment/LOCAL_SETUP.md)** - User-friendly local AI
- **[Ollama Setup](../deployment/LOCAL_SETUP.md)** - Production-ready local AI  
- **[Deployment Modes](../deployment/DEPLOYMENT_MODES.md)** - Choose your setup

---

# llama-cpp-python Integration for WhisperEngine (DEPRECATED)

## Overview

WhisperEngine now supports `llama-cpp-python` as an optimized backend for local AI inference. This provides significant performance and memory improvements over the traditional PyTorch-based approach.

## Benefits of llama-cpp-python

### Performance
- **50-80% lower memory usage** compared to PyTorch models
- **Faster inference** especially on CPU
- **Quantized models** (4-bit, 8-bit) for even smaller memory footprint
- **Optimized C++ backend** with SIMD instructions

### Deployment
- **Smaller dependencies** - no need for full PyTorch stack
- **Better cross-platform support** for different architectures
- **No internet required** for inference once model is downloaded
- **Compatible with GGUF model ecosystem** from HuggingFace

## Quick Start

### 1. Install Dependencies
```bash
# Install in virtual environment (REQUIRED)
source .venv/bin/activate && pip install llama-cpp-python
```

### 2. Download a GGUF Model
```bash
# Create models directory
mkdir -p ./models

# Download a small efficient model (example)
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
mv Phi-3-mini-4k-instruct-q4.gguf ./models/
```

### 3. Configure Environment
```bash
# Set API URL to use llama-cpp-python
export LLM_CHAT_API_URL=llamacpp://local

# Optional: Specify exact model path
export LLAMACPP_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

### 4. Run WhisperEngine
```bash
# Native desktop app
source .venv/bin/activate && python universal_native_app.py

# Discord bot
source .venv/bin/activate && python run.py
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_CHAT_API_URL` | `http://localhost:1234/v1` | Set to `llamacpp://local` for llama-cpp-python |
| `LLAMACPP_MODEL_PATH` | Auto-detect | Path to GGUF model file |
| `LOCAL_MODELS_DIR` | `./models` | Directory to search for GGUF models |
| `LLAMACPP_CONTEXT_SIZE` | `4096` | Context window size |
| `LLAMACPP_THREADS` | `4` | Number of CPU threads |
| `LLAMACPP_USE_GPU` | `auto` | GPU usage: `true`, `false`, or `auto` |

### Auto-Detection
If `LLAMACPP_MODEL_PATH` is not set, WhisperEngine will automatically detect the first `.gguf` file in the `LOCAL_MODELS_DIR`.

### GPU Acceleration
- **CUDA**: Automatically detected and used when available
- **Apple Silicon (MPS)**: Partial GPU acceleration on macOS
- **CPU**: Fallback with optimized performance

## Model Recommendations

### Small Models (< 4GB RAM)
- **Phi-3-mini-4k-instruct-q4.gguf** (~2GB) - Great for general chat
- **TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf** (~800MB) - Ultra lightweight

### Medium Models (4-8GB RAM)
- **Phi-3-medium-4k-instruct-q4.gguf** (~4GB) - Better reasoning
- **Llama-2-7B-Chat.Q4_K_M.gguf** (~4GB) - Well-rounded performance

### Large Models (8GB+ RAM)
- **Llama-2-13B-Chat.Q4_K_M.gguf** (~8GB) - High quality responses
- **CodeLlama-13B-Instruct.Q4_K_M.gguf** (~8GB) - Code-focused

## Integration Architecture

### URL Scheme
WhisperEngine uses the `llamacpp://` URL scheme to identify llama-cpp-python backends:

```python
# Traditional HTTP API
LLM_CHAT_API_URL=http://localhost:1234/v1

# llama-cpp-python backend
LLM_CHAT_API_URL=llamacpp://local
```

### Routing Logic
The LLMClient automatically routes requests based on the URL scheme:

1. **llamacpp://** → Direct llama-cpp-python inference
2. **local://** → PyTorch transformers inference  
3. **http://** → HTTP API (LM Studio, Ollama, etc.)

### Error Handling
- Graceful fallback when models fail to load
- Clear error messages for troubleshooting
- Automatic detection and configuration guidance

## Desktop App Integration

The desktop app includes automatic llama-cpp-python detection and configuration:

```python
from src.llm.desktop_llm_manager import configure_llamacpp_for_desktop

# Auto-configure llamacpp if GGUF models are available
result = await configure_llamacpp_for_desktop()
```

## Testing

Run the integration tests to verify everything works:

```bash
source .venv/bin/activate && python test_llamacpp_integration.py
```

## Troubleshooting

### Model Not Loading
```
WARNING: No GGUF models found in ./models and LLAMACPP_MODEL_PATH not set
```
**Solution**: Download a GGUF model and place it in `./models/`

### Memory Issues
```
ERROR: Failed to initialize llama-cpp-python model: out of memory
```
**Solutions**:
- Use a smaller quantized model (Q4_K_M instead of Q8_0)
- Reduce `LLAMACPP_CONTEXT_SIZE`
- Set `LLAMACPP_USE_GPU=false` to use CPU only

### Performance Issues
```
Slow inference on CPU
```
**Solutions**:
- Increase `LLAMACPP_THREADS` to match your CPU cores
- Enable GPU acceleration with `LLAMACPP_USE_GPU=true`
- Use a smaller model for faster responses

### Import Errors
```
ImportError: llama-cpp-python not available
```
**Solution**: Install in virtual environment:
```bash
source .venv/bin/activate && pip install llama-cpp-python
```

## Comparison with Other Backends

| Backend | Memory Usage | Speed | Setup Complexity | GPU Support |
|---------|--------------|-------|------------------|-------------|
| **llama-cpp-python** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| PyTorch (local://) | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| LM Studio | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Ollama | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## Migration from PyTorch

To migrate existing PyTorch models to llama-cpp-python:

1. **Find GGUF version** of your model on HuggingFace
2. **Download the GGUF file** instead of the PyTorch version
3. **Update environment** to use `llamacpp://local`
4. **Test performance** and adjust settings as needed

## Advanced Configuration

### Custom Chat Templates
llama-cpp-python automatically handles chat templates for most models. For custom templates:

```python
# In _initialize_llamacpp_llm()
self.llamacpp_model = Llama(
    model_path=model_path,
    chat_format="custom",  # or "chatml", "llama-2", etc.
    # ... other parameters
)
```

### Streaming Support
While not implemented in this initial version, llama-cpp-python supports token streaming:

```python
# Future enhancement
response = self.llamacpp_model.create_chat_completion(
    messages=messages,
    stream=True  # Enable streaming
)
```

## Contributing

To contribute improvements to the llama-cpp-python integration:

1. Add tests to `test_llamacpp_integration.py`
2. Update this documentation
3. Follow WhisperEngine's coding standards
4. Test with multiple model types and sizes

## Resources

- [llama-cpp-python Documentation](https://github.com/abetlen/llama-cpp-python)
- [GGUF Models on HuggingFace](https://huggingface.co/models?library=gguf)
- [Model Quantization Guide](https://github.com/ggerganov/llama.cpp/blob/master/examples/quantize/README.md)
- [WhisperEngine Documentation](./README.md)