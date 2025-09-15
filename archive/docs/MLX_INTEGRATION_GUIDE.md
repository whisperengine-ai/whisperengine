# MLX Integration Guide for WhisperEngine

## Overview

WhisperEngine now includes native support for Apple's MLX framework, providing optimized inference on Apple Silicon devices (M1, M2, M3, M4+ chips). MLX offers superior performance and memory efficiency compared to traditional LLM backends on Apple Silicon.

## Features

- **🍎 Apple Silicon Optimized**: Built specifically for Apple's unified memory architecture
- **⚡ Superior Performance**: 20-40% faster inference compared to other backends
- **💾 Memory Efficient**: Better utilization of unified memory on Apple Silicon
- **🔄 Automatic Fallback**: Seamlessly falls back to Ollama/LM Studio if MLX unavailable
- **🎯 Smart Detection**: Automatically detects Apple Silicon and prefers MLX when available

## Requirements

- **Hardware**: Apple Silicon Mac (M1, M2, M3, M4+)
- **OS**: macOS 12.0+ (Monterey or later)
- **Python**: 3.9+
- **Package**: `mlx-lm>=0.10.0` (automatically installed on Apple Silicon)

## Installation

### Automatic Installation
MLX is automatically installed on Apple Silicon devices when you install WhisperEngine:

```bash
# MLX will be installed automatically on Apple Silicon
pip install -r requirements.txt
```

### Manual Installation
If you need to install MLX manually:

```bash
# Only works on Apple Silicon
pip install mlx-lm>=0.10.0
```

## Configuration

### Environment Variables

```bash
# Enable MLX backend (automatic on Apple Silicon)
LLM_CHAT_API_URL="mlx://llama-3.1-8b-instruct"

# MLX-specific settings
MLX_MODEL_NAME="llama-3.1-8b-instruct"
MLX_MAX_TOKENS=2048
MLX_TEMPERATURE=0.7
MLX_TOP_P=0.9

# Model storage location
LOCAL_MODELS_DIR="./models"
```

### Model Configuration

MLX models are stored in `./models/mlx/` directory:

```
./models/mlx/
├── llama-3.1-8b-instruct/
│   ├── config.json
│   ├── tokenizer.json
│   ├── weights.npz
│   └── tokenizer_config.json
├── mistral-7b-instruct/
│   └── ...
└── codellama-7b/
    └── ...
```

## Model Setup

### Option 1: Download Pre-converted MLX Models

```bash
# Download from Hugging Face (if available)
git clone https://huggingface.co/mlx-community/Llama-3.1-8B-Instruct-mlx ./models/mlx/llama-3.1-8b-instruct
```

### Option 2: Convert Existing Models

```python
from src.llm.mlx_backend import convert_model_to_mlx

# Convert a HuggingFace model to MLX format
success = convert_model_to_mlx(
    source_model_path="./models/llama-3.1-8b-instruct",
    target_model_name="llama-3.1-8b-instruct"
)
```

### Option 3: Using MLX CLI Tools

```bash
# Install conversion tools
pip install mlx-lm[convert]

# Convert model
python -m mlx_lm.convert \\
    --hf-path microsoft/Phi-3-mini-4k-instruct \\
    --mlx-path ./models/mlx/phi-3-mini
```

## Usage

### Automatic Backend Selection

WhisperEngine automatically detects Apple Silicon and prefers MLX:

```python
from src.llm.smart_backend_selector import get_smart_backend_selector

# Automatically selects optimal backend
selector = get_smart_backend_selector()
optimal_backend = selector.get_optimal_backend()

print(f"Selected backend: {optimal_backend.name}")
# Output on Apple Silicon: "Selected backend: MLX"
```

### Manual MLX Usage

```python
from src.llm.mlx_backend import create_mlx_backend, get_default_mlx_model_config

# Create MLX backend
mlx_backend = create_mlx_backend()
if mlx_backend:
    # Load model
    config = get_default_mlx_model_config("llama-3.1-8b-instruct")
    mlx_backend.load_model(config)
    
    # Generate response
    response = mlx_backend.generate_response(
        prompt="Hello, how are you?",
        max_tokens=100,
        temperature=0.7
    )
    print(response)
```

### Using with LLM Client

```python
from src.llm.llm_client import LLMClient

# MLX backend via URL scheme
client = LLMClient(api_url="mlx://llama-3.1-8b-instruct")

# Chat completion
response = client.chat_completion(
    messages=[
        {"role": "user", "content": "Explain Apple Silicon benefits"}
    ]
)
```

## Fallback Chain

WhisperEngine implements an intelligent fallback system:

1. **MLX** (Apple Silicon only) - Highest priority
2. **LM Studio** - User-friendly local server
3. **Ollama** - Production-ready server
4. **llama-cpp-python** - Direct Python integration
5. **Transformers** - HuggingFace models

```python
# Get fallback chain
selector = get_smart_backend_selector()
fallback_chain = selector.get_fallback_chain()

for backend in fallback_chain:
    print(f"{backend.priority}. {backend.name} - {backend.description}")
```

## Performance Optimization

### Memory Management

```python
# Automatic memory management
mlx_backend.unload_model()  # Free memory when done

# Check memory usage
import psutil
memory_info = psutil.virtual_memory()
print(f"Memory usage: {memory_info.percent}%")
```

### Model Selection

**Recommended models for different memory configurations:**

- **8GB RAM**: `phi-3-mini`, `llama-3.2-3b`
- **16GB RAM**: `llama-3.1-8b-instruct`, `mistral-7b-instruct`
- **32GB+ RAM**: `llama-3.1-70b` (when available)

### GPU Acceleration

MLX automatically uses Apple Silicon GPU via Metal:

```python
# GPU acceleration is automatic
import mlx.core as mx
print(f"MLX device: {mx.default_device()}")
# Output: metal
```

## Troubleshooting

### Common Issues

**1. MLX not available**
```
Error: MLX not available. This backend requires Apple Silicon and mlx-lm package.
```
**Solution**: Ensure you're on Apple Silicon and install MLX:
```bash
pip install mlx-lm
```

**2. Model not found**
```
Error: Model path does not exist: ./models/mlx/model-name
```
**Solution**: Download or convert models to MLX format.

**3. Memory errors**
```
Error: Out of memory during model loading
```
**Solution**: Use smaller models or increase swap space.

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("src.llm.mlx_backend").setLevel(logging.DEBUG)
```

Check MLX availability:

```python
from src.llm.mlx_backend import MLXBackend

print(f"MLX available: {MLXBackend.is_available()}")
print(f"Available models: {MLXBackend.find_available_models()}")
```

## Desktop App Integration

MLX is automatically integrated into the WhisperEngine desktop app:

### Settings Dialog

The settings dialog includes MLX-specific options:
- Model selection
- Memory management
- Performance tuning

### System Tray

MLX status is shown in the system tray:
- 🍎 Green: MLX active and working
- 🟡 Yellow: MLX available but not active
- 🔴 Red: MLX unavailable

### Resource Monitoring

Real-time MLX performance monitoring:
- Memory usage
- Inference speed
- Token generation rate

## Advanced Configuration

### Custom Model Configuration

```python
from src.llm.mlx_backend import MLXModelConfig

custom_config = MLXModelConfig(
    model_path="./models/mlx/custom-model",
    dtype="float16",
    max_tokens=4096,
    temperature=0.8,
    top_p=0.95
)
```

### Performance Tuning

```bash
# Environment variables for tuning
MLX_MEMORY_POOL_SIZE=8192  # MB
MLX_BATCH_SIZE=1           # Batch size for inference
MLX_QUANTIZATION=true      # Enable quantization
```

### Model Conversion Options

```bash
# Advanced conversion with quantization
python -m mlx_lm.convert \\
    --hf-path microsoft/Phi-3-mini-4k-instruct \\
    --mlx-path ./models/mlx/phi-3-mini \\
    --quantize \\
    --q-bits 8
```

## Best Practices

1. **Model Selection**: Choose models appropriate for your RAM
2. **Memory Management**: Unload models when switching
3. **Fallback Planning**: Always configure fallback backends
4. **Performance Monitoring**: Monitor memory and inference speed
5. **Model Updates**: Keep MLX models updated for best performance

## API Reference

### MLXBackend Class

```python
class MLXBackend:
    def __init__(self)
    def load_model(self, config: MLXModelConfig) -> bool
    def unload_model(self) -> None
    def generate_response(self, prompt: str, **kwargs) -> str
    def generate_response_async(self, prompt: str, **kwargs) -> str
    def get_model_info(self) -> Dict[str, Any]
    
    @classmethod
    def is_available(cls) -> bool
    @classmethod
    def find_available_models(cls) -> List[str]
```

### Smart Backend Selector

```python
class SmartBackendSelector:
    def get_optimal_backend(self) -> Optional[BackendInfo]
    def get_fallback_chain(self) -> List[BackendInfo]
    def auto_configure_environment(self) -> bool
    def get_setup_recommendations(self) -> List[str]
```

## Contributing

To contribute MLX improvements:

1. Test on Apple Silicon hardware
2. Benchmark against other backends
3. Submit performance improvements
4. Report compatibility issues

## Resources

- [MLX GitHub Repository](https://github.com/ml-explore/mlx)
- [MLX Documentation](https://ml-explore.github.io/mlx/build/html/index.html)
- [MLX Examples](https://github.com/ml-explore/mlx-examples)
- [Apple Silicon Performance Guide](https://developer.apple.com/documentation/metal/optimizing_performance_with_the_gpu_counters_instrument)