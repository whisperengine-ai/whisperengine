# MLX Testing and Validation Guide

## Overview

This guide provides comprehensive testing procedures for the native MLX integration in WhisperEngine. After implementing native MLX support with direct Python model loading, these tests validate the complete pipeline from model downloading through AI response generation.

## Quick Validation

### 1-Minute Health Check

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Switch to MLX configuration
python toggle_models.py mlx

# Start desktop app (should start without errors)
python universal_native_app.py
```

**Expected Result**: Desktop app starts with clean logs:
```
✅ Desktop environment configuration loaded
🤖 Starting WhisperEngine Universal Native App on Darwin...
✅ Application started successfully!
```

## Comprehensive Testing Suite

### Test 1: MLX Framework Availability

**Purpose**: Verify MLX is properly installed and detects Apple Silicon

```bash
python -c "
import platform
from src.llm.mlx_backend import MLXBackend

print(f'Platform: {platform.system()} {platform.machine()}')
print(f'MLX Available: {MLXBackend.is_available()}')

if MLXBackend.is_available():
    print('✅ MLX framework ready')
else:
    print('❌ MLX not available')
"
```

**Expected Output**:
```
Platform: Darwin arm64
MLX Available: True
✅ MLX framework ready
```

### Test 2: Model Download and Storage

**Purpose**: Verify model downloading and storage structure

```bash
# Check model exists
ls -la models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit/

# Re-download if needed
python download_models.py

# Verify model files
find models/mlx -name "*.safetensors" -o -name "config.json" -o -name "tokenizer.model"
```

**Expected Files**:
```
models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit/config.json
models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit/tokenizer.model  
models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit/weights.safetensors
```

### Test 3: Raw MLX Generation

**Purpose**: Test MLX framework directly without WhisperEngine wrapper

```bash
python -c "
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler
import time

print('🧪 Testing raw MLX generation...')

# Load model
start_time = time.time()
model, tokenizer = load('./models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit')
load_time = time.time() - start_time
print(f'⏱️  Model loaded in {load_time:.2f}s')

# Test generation with proper sampler
sampler = make_sampler(temp=0.7, top_p=0.9)
prompt = 'What is 2+2?'

start_time = time.time()
response = generate(
    model, 
    tokenizer, 
    prompt, 
    max_tokens=50, 
    sampler=sampler, 
    verbose=True
)
gen_time = time.time() - start_time

print(f'📝 Prompt: {prompt}')
print(f'💬 Response: {response}')
print(f'⏱️  Generated in {gen_time:.2f}s')
print('✅ Raw MLX generation successful')
"
```

**Expected Output**:
```
🧪 Testing raw MLX generation...
⏱️  Model loaded in 3.45s
==========
What is 2+2? 4

2 + 2 equals 4. This is a basic arithmetic operation.
==========
Prompt: 5 tokens, 12.345 tokens-per-sec
Generation: 15 tokens, 89.123 tokens-per-sec
Peak memory: 2.255 GB
📝 Prompt: What is 2+2?
💬 Response: What is 2+2? 4

2 + 2 equals 4. This is a basic arithmetic operation.
⏱️  Generated in 1.23s
✅ Raw MLX generation successful
```

### Test 4: MLX Backend Integration

**Purpose**: Test WhisperEngine's MLX backend wrapper

```bash
python -c "
from src.llm.mlx_backend import create_mlx_backend, get_default_mlx_model_config
import asyncio

async def test_backend():
    print('🔧 Testing MLX backend integration...')
    
    # Test model config creation
    model_name = 'microsoft/Phi-3-mini-4k-instruct-4bit'
    config = get_default_mlx_model_config(model_name)
    print(f'📁 Model path: {config.model_path}')
    print(f'🎛️  Max tokens: {config.max_tokens}')
    print(f'🌡️  Temperature: {config.temperature}')
    
    # Test backend creation
    backend = create_mlx_backend()
    if not backend:
        print('❌ Failed to create MLX backend')
        return False
    
    # Test model loading
    if not backend.load_model(config):
        print('❌ Failed to load model')
        return False
    
    print('✅ Model loaded successfully')
    
    # Test generation
    response = await backend.generate_response(
        'Hello! How are you?',
        max_tokens=30,
        temperature=0.7
    )
    
    print(f'💬 Generated response: {response[:100]}...')
    print('✅ MLX backend integration successful')
    return True

asyncio.run(test_backend())
"
```

### Test 5: LLM Client Integration

**Purpose**: Test full LLM client with MLX backend

```bash
python test_mlx_backend.py
```

**Expected Output**:
```
🧪 Testing MLX Backend End-to-End
==================================================
🔧 API URL: mlx://microsoft/Phi-3-mini-4k-instruct-4bit
🤖 Model: microsoft/Phi-3-mini-4k-instruct

📡 Initializing client...
✅ Client initialized successfully

💬 Testing simple generation...
✅ Response received: Hello! I'm doing well, thank you for asking. How can I assist you today...

🎉 MLX backend test passed!
```

### Test 6: Desktop App Integration

**Purpose**: Test complete desktop application with MLX

```bash
# Start app in background
python universal_native_app.py &
APP_PID=$!

# Give it time to start
sleep 5

# Check if process is running
if ps -p $APP_PID > /dev/null; then
    echo "✅ Desktop app started successfully"
    # Kill the app
    kill $APP_PID
else
    echo "❌ Desktop app failed to start"
fi
```

### Test 7: Performance Benchmarking

**Purpose**: Measure MLX performance characteristics

```bash
python -c "
import time
import psutil
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler

print('📊 MLX Performance Benchmarks')
print('=' * 40)

# Memory before loading
mem_before = psutil.virtual_memory().used / 1024**3
print(f'Memory before: {mem_before:.2f} GB')

# Load model and measure
start = time.time()
model, tokenizer = load('./models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit')
load_time = time.time() - start
mem_after = psutil.virtual_memory().used / 1024**3

print(f'Load time: {load_time:.2f}s')
print(f'Memory after: {mem_after:.2f} GB')
print(f'Memory used: {mem_after - mem_before:.2f} GB')

# Generation benchmark
sampler = make_sampler(temp=0.7, top_p=0.9)
prompt = 'Write a short paragraph about artificial intelligence.'

# Warm up
generate(model, tokenizer, 'Test', max_tokens=5, sampler=sampler)

# Benchmark multiple generations
times = []
for i in range(3):
    start = time.time()
    response = generate(model, tokenizer, prompt, max_tokens=100, sampler=sampler)
    gen_time = time.time() - start
    times.append(gen_time)
    print(f'Generation {i+1}: {gen_time:.2f}s ({len(response.split())} words)')

avg_time = sum(times) / len(times)
print(f'Average generation: {avg_time:.2f}s')
print(f'Peak memory: {psutil.virtual_memory().used / 1024**3:.2f} GB')
"
```

## Configuration Testing

### Test Environment Variables

```bash
# Check MLX configuration
python -c "
import os
from env_manager import load_environment

load_environment()
print('MLX Environment Configuration:')
print('=' * 35)
print(f'LLM_CHAT_API_URL: {os.getenv("LLM_CHAT_API_URL")}')
print(f'LLM_CHAT_MODEL: {os.getenv("LLM_CHAT_MODEL")}')
print(f'MLX_ENABLED: {os.getenv("MLX_ENABLED")}')
print(f'MLX_MEMORY_LIMIT: {os.getenv("MLX_MEMORY_LIMIT")}')
"
```

### Test Model Toggle

```bash
# Test switching between configurations
echo "Testing configuration switching..."

# Test remote
python toggle_models.py remote
grep "LLM_CHAT_API_URL" .env

# Test local  
python toggle_models.py local
grep "LLM_CHAT_API_URL" .env

# Test MLX
python toggle_models.py mlx
grep "LLM_CHAT_API_URL" .env
```

## Troubleshooting Tests

### Memory Usage Test

```bash
python -c "
import psutil

mem = psutil.virtual_memory()
print(f'Total Memory: {mem.total / 1024**3:.1f} GB')
print(f'Available: {mem.available / 1024**3:.1f} GB') 
print(f'Used: {mem.used / 1024**3:.1f} GB')
print(f'Free: {mem.free / 1024**3:.1f} GB')

if mem.available < 4 * 1024**3:  # 4GB
    print('⚠️  Warning: Low memory for MLX operations')
elif mem.available < 8 * 1024**3:  # 8GB
    print('✅ Sufficient memory for 4-bit models')
else:
    print('✅ Excellent memory for all models')
"
```

### Error Reproduction Test

```bash
# Test error scenarios
python -c "
from src.llm.mlx_backend import MLXBackend, get_default_mlx_model_config

print('Testing error scenarios...')

# Test with invalid model
try:
    config = get_default_mlx_model_config('invalid/model')
    backend = MLXBackend()
    backend.load_model(config)
    print('❌ Should have failed with invalid model')
except Exception as e:
    print(f'✅ Properly handled invalid model: {e}')

# Test with corrupted path
try:
    config = get_default_mlx_model_config('microsoft/Phi-3-mini-4k-instruct-4bit')
    config.model_path = '/invalid/path'
    backend = MLXBackend()
    backend.load_model(config)
    print('❌ Should have failed with invalid path')
except Exception as e:
    print(f'✅ Properly handled invalid path: {e}')
"
```

## Automated Test Suite

### Complete Validation Script

Create `validate_mlx.sh`:

```bash
#!/bin/bash
set -e

echo "🧪 WhisperEngine MLX Validation Suite"
echo "====================================="

# Activate environment
source .venv/bin/activate

# Test 1: Framework availability
echo "Test 1: MLX Framework..."
python -c "from src.llm.mlx_backend import MLXBackend; assert MLXBackend.is_available()"
echo "✅ PASS"

# Test 2: Model exists
echo "Test 2: Model Files..."
test -f "models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit/config.json"
echo "✅ PASS"

# Test 3: Configuration
echo "Test 3: Configuration..."
python toggle_models.py mlx > /dev/null
grep -q "mlx://microsoft/Phi-3-mini-4k-instruct-4bit" .env
echo "✅ PASS"

# Test 4: Backend integration
echo "Test 4: Backend Integration..."
python test_mlx_backend.py > /dev/null
echo "✅ PASS"

# Test 5: Memory check
echo "Test 5: Memory Check..."
python -c "
import psutil
mem = psutil.virtual_memory()
assert mem.available > 3 * 1024**3, 'Insufficient memory'
"
echo "✅ PASS"

echo ""
echo "🎉 All MLX tests passed!"
echo "Ready for production use."
```

Make it executable and run:

```bash
chmod +x validate_mlx.sh
./validate_mlx.sh
```

## Performance Baselines

### Expected Performance Metrics

| Metric | 4-bit Model | Full Model |
|--------|-------------|------------|
| Model Load Time | 3-5 seconds | 8-12 seconds |
| Memory Usage | 2.0-2.5 GB | 4.5-5.5 GB |
| Generation Speed | 80-120 tok/s | 60-90 tok/s |
| Prompt Processing | 10-20 tok/s | 8-15 tok/s |

### Benchmark Script

```bash
python -c "
import time
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler

# Benchmark parameters
MODEL_PATH = './models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit'
TEST_PROMPT = 'Explain quantum computing in simple terms.'
MAX_TOKENS = 100

print('Running MLX Performance Benchmark...')
print('=' * 40)

# Load benchmark
start = time.time()
model, tokenizer = load(MODEL_PATH)
load_time = time.time() - start
print(f'Model Load: {load_time:.2f}s')

# Generation benchmark  
sampler = make_sampler(temp=0.7, top_p=0.9)
start = time.time()
response = generate(model, tokenizer, TEST_PROMPT, max_tokens=MAX_TOKENS, sampler=sampler, verbose=True)
gen_time = time.time() - start

tokens_generated = len(response.split()) * 1.3  # Rough token estimate
speed = tokens_generated / gen_time

print(f'Generation Time: {gen_time:.2f}s')
print(f'Estimated Speed: {speed:.1f} tokens/sec')
print(f'Response Length: {len(response)} chars')
"
```

## Continuous Integration Tests

For automated testing in CI/CD:

```yaml
# .github/workflows/test-mlx.yml
name: MLX Integration Tests
on: [push, pull_request]

jobs:
  test-mlx:
    runs-on: macos-latest
    if: contains(runner.arch, 'ARM64')
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        
    - name: Download test models
      run: |
        source .venv/bin/activate
        python download_models.py
        
    - name: Run MLX tests
      run: |
        source .venv/bin/activate
        python test_mlx_backend.py
        
    - name: Validate configuration
      run: |
        source .venv/bin/activate
        python toggle_models.py mlx
        grep -q "mlx://" .env
```

This comprehensive testing guide ensures the MLX integration is working correctly at every level, from the raw MLX framework through the complete WhisperEngine desktop application.