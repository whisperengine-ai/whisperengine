#!/bin/bash
# MLX Validation Script for WhisperEngine
# Runs comprehensive tests to validate MLX integration

set -e

echo "🧪 WhisperEngine MLX Validation Suite"
echo "====================================="

# Check if we're on Apple Silicon
if [[ $(uname -m) != "arm64" ]]; then
    echo "❌ MLX requires Apple Silicon (arm64), found: $(uname -m)"
    exit 1
fi

echo "✅ Apple Silicon detected"

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Activating virtual environment..."
    source .venv/bin/activate
fi

echo "✅ Virtual environment active"

# Test 1: MLX Framework availability
echo ""
echo "Test 1: MLX Framework Availability"
echo "----------------------------------"
python -c "
from src.llm.mlx_backend import MLXBackend
if MLXBackend.is_available():
    print('✅ MLX framework is available')
else:
    print('❌ MLX framework not available')
    exit(1)
"

# Test 2: Model files exist
echo ""
echo "Test 2: Model Files"  
echo "-------------------"
MODEL_DIR="models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit"
if [[ -f "$MODEL_DIR/config.json" ]] && [[ -f "$MODEL_DIR/model.safetensors" ]]; then
    echo "✅ Model files exist"
    echo "   📁 Path: $MODEL_DIR"
    echo "   📊 Size: $(du -sh $MODEL_DIR | cut -f1)"
else
    echo "❌ Model files missing"
    echo "   Run: python download_models.py"
    exit 1
fi

# Test 3: Configuration
echo ""
echo "Test 3: MLX Configuration"
echo "-------------------------"
python toggle_models.py mlx > /dev/null 2>&1
if grep -q "mlx://microsoft/Phi-3-mini-4k-instruct-4bit" .env; then
    echo "✅ MLX configuration active"
    echo "   🔧 URL: $(grep LLM_CHAT_API_URL .env | cut -d'=' -f2)"
else
    echo "❌ MLX configuration not set"
    exit 1
fi

# Test 4: Memory check
echo ""
echo "Test 4: System Memory"
echo "---------------------"
python -c "
import psutil
mem = psutil.virtual_memory()
available_gb = mem.available / 1024**3
total_gb = mem.total / 1024**3

print(f'Total: {total_gb:.1f} GB')
print(f'Available: {available_gb:.1f} GB')

if available_gb < 3:
    print('❌ Insufficient memory (need 3GB+)')
    exit(1)
elif available_gb < 6:
    print('⚠️  Limited memory - may affect performance')
else:
    print('✅ Sufficient memory available')
"

# Test 5: Raw MLX functionality
echo ""
echo "Test 5: Raw MLX Generation"
echo "--------------------------"
python -c "
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler
import time

try:
    print('Loading model...')
    start = time.time()
    model, tokenizer = load('./models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit')
    load_time = time.time() - start
    
    print(f'✅ Model loaded in {load_time:.1f}s')
    
    print('Testing generation...')
    sampler = make_sampler(temp=0.7)
    response = generate(model, tokenizer, 'Hello', max_tokens=10, sampler=sampler)
    
    print(f'✅ Generation successful: {response[:50]}...')
    
except Exception as e:
    print(f'❌ Raw MLX test failed: {e}')
    exit(1)
"

# Test 6: Backend integration
echo ""
echo "Test 6: Backend Integration"
echo "---------------------------"
python -c "
from src.llm.mlx_backend import create_mlx_backend, get_default_mlx_model_config

try:
    config = get_default_mlx_model_config('microsoft/Phi-3-mini-4k-instruct-4bit')
    backend = create_mlx_backend()
    
    if backend and backend.load_model(config):
        print('✅ Backend integration successful')
    else:
        print('❌ Backend integration failed')
        exit(1)
        
except Exception as e:
    print(f'❌ Backend test failed: {e}')
    exit(1)
"

# Test 7: End-to-end test
echo ""
echo "Test 7: End-to-End Test"
echo "-----------------------"
if python test_mlx_backend.py > /dev/null 2>&1; then
    echo "✅ End-to-end test passed"
else
    echo "❌ End-to-end test failed"
    echo "   Run manually: python test_mlx_backend.py"
    exit 1
fi

# Success summary
echo ""
echo "🎉 ALL TESTS PASSED!"
echo "=================="
echo "✅ MLX framework ready"
echo "✅ Models downloaded" 
echo "✅ Configuration correct"
echo "✅ Memory sufficient"
echo "✅ Raw MLX working"
echo "✅ Backend integration working"
echo "✅ End-to-end pipeline working"
echo ""
echo "🚀 WhisperEngine MLX is ready for use!"
echo "   Start desktop app: python universal_native_app.py"
echo "   Quick test: python test_mlx_backend.py"