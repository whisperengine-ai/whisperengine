# MLX Model Testing Guide for WhisperEngine

## 🍎 What is MLX?
MLX is Apple's machine learning framework optimized for Apple Silicon (M1/M2/M3). It provides significant speed improvements for AI models on Mac hardware.

## ⚡ Quick Setup

### 1. Switch to MLX Models
```bash
source .venv/bin/activate && python toggle_models.py
# Choose 'M' for MLX
```

### 2. Run Desktop App
```bash
source .venv/bin/activate && python universal_native_app.py
```

## 🎯 MLX Configuration in WhisperEngine

When you choose MLX mode, the toggle script:
- ✅ Sets up local LM Studio connection
- ✅ Uses Google Gemma-3-4B (optimized for MLX)
- ✅ Adds MLX environment flags
- ✅ Configures memory limits for your 64GB system

## 🚀 Performance Optimizations

### Environment Variables (Auto-configured)
```bash
MLX_ENABLED=true
MLX_MEMORY_LIMIT=8192  # 8GB allocation
```

### Optional Optimizations
Add to your shell profile (`~/.zshrc`):
```bash
# MLX optimizations
export PYTORCH_ENABLE_MPS_FALLBACK=1
export MLX_METAL_DEBUG=0  # Disable debug for performance
```

## 🔧 Model Recommendations for MLX

**Currently Using:**
- **google/gemma-3-4b** - Fast, efficient 4B parameter model

**Alternative MLX-Optimized Models:**
- **microsoft/Phi-3-mini-4k-instruct** - Excellent for reasoning
- **meta-llama/Llama-3.2-1B-Instruct** - Ultra-fast for testing
- **apple/OpenELM-1_1B** - Native Apple model

## 📊 Expected Performance

With your **64GB RAM Apple Silicon** setup:
- 🟢 **google/gemma-3-4b**: ~50-100 tokens/sec
- 🟢 **Phi-3-mini**: ~80-150 tokens/sec  
- 🟢 **Llama-3.2-1B**: ~200+ tokens/sec

## 🔄 Switching Between Modes

**Test Different Configurations:**
```bash
python toggle_models.py
# L = LM Studio (standard)
# M = MLX optimized (Apple Silicon)
# R = Remote (OpenRouter)
```

## 🐛 Troubleshooting

### If MLX isn't working:
```bash
# Check MLX installation
python -c "import mlx; print('MLX OK')"

# Install if missing
pip install mlx-lm
```

### For better performance:
- Close other GPU-intensive apps
- Ensure LM Studio is using the correct model
- Monitor Activity Monitor for memory usage

## 💡 Pro Tips

1. **Start with Gemma-3-4B** - Good balance of speed/quality
2. **Use Phi-3-mini** for complex reasoning tasks
3. **Try Llama-3.2-1B** for maximum speed
4. **Monitor token/sec** in the desktop app output
5. **64GB RAM** means you can run larger models if needed

Ready to test! 🚀