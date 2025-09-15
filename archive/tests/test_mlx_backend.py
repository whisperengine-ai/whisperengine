#!/usr/bin/env python3
"""
Comprehensive MLX backend testing script for WhisperEngine

This script validates the complete MLX integration pipeline:
- Environment configuration loading
- MLX backend initialization  
- Model loading and configuration
- AI response generation
- Performance measurement

Usage:
    source .venv/bin/activate && python test_mlx_backend.py
"""

import asyncio
import sys
import os
import time
import psutil

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llm.llm_client import LLMClient

def print_header(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    """Print a test step"""
    print(f"\n{step}. {description}")

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

def measure_memory():
    """Get current memory usage in GB"""
    return psutil.virtual_memory().used / 1024**3

def test_mlx_backend():
    """Comprehensive MLX backend test suite"""
    print_header("WhisperEngine MLX Backend Validation")
    
    # System Information
    print_info(f"Platform: {os.uname().sysname} {os.uname().machine}")
    print_info(f"Python: {sys.version.split()[0]}")
    print_info(f"Available Memory: {psutil.virtual_memory().available / 1024**3:.1f} GB")
    
    # Step 1: Environment Configuration
    print_step(1, "Loading Environment Configuration")
    
    api_url = os.getenv("LLM_CHAT_API_URL", "mlx://microsoft/Phi-3-mini-4k-instruct-4bit")
    model_name = os.getenv("LLM_CHAT_MODEL", "microsoft/Phi-3-mini-4k-instruct")
    
    print_info(f"API URL: {api_url}")
    print_info(f"Model: {model_name}")
    
    if not api_url.startswith("mlx://"):
        print_error("Not configured for MLX! Run: python toggle_models.py mlx")
        return False
    
    print_success("Environment configured for MLX")
    
    # Step 2: Client Initialization
    print_step(2, "Initializing LLM Client")
    
    try:
        start_time = time.time()
        client = LLMClient(api_url=api_url)
        init_time = time.time() - start_time
        
        print_info(f"Client initialization: {init_time:.2f}s")
        print_success("LLM Client created successfully")
        
    except Exception as e:
        print_error(f"Client initialization failed: {e}")
        return False
    
    # Step 3: Backend Availability Check
    print_step(3, "Checking MLX Backend Availability")
    
    try:
        # Check if MLX backend is properly initialized
        if hasattr(client, 'mlx_backend') and client.mlx_backend:
            print_success("MLX backend is available and loaded")
            
            # Check model loading status
            if hasattr(client.mlx_backend, 'is_loaded') and client.mlx_backend.is_loaded:
                print_success("Model is loaded and ready")
            else:
                print_error("Model is not loaded")
                return False
        else:
            print_error("MLX backend not available")
            return False
            
    except Exception as e:
        print_error(f"Backend check failed: {e}")
        return False
    
    # Step 4: Memory Usage Check
    print_step(4, "Measuring Memory Usage")
    
    current_memory = measure_memory()
    print_info(f"Current memory usage: {current_memory:.2f} GB")
    
    if current_memory > 6.0:
        print_error("High memory usage detected")
    else:
        print_success("Memory usage within acceptable range")
    
    # Step 5: Simple Generation Test
    print_step(5, "Testing Simple AI Generation")
    
    test_messages = [
        {"role": "user", "content": "What is 2+2? Answer briefly."}
    ]
    
    try:
        start_time = time.time()
        response = client.generate_chat_completion(test_messages)
        gen_time = time.time() - start_time
        
        if response and 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            if content and len(content.strip()) > 0:
                print_success(f"Generation successful in {gen_time:.2f}s")
                print_info(f"Response: '{content[:100]}{'...' if len(content) > 100 else ''}'")
                
                # Rough performance estimate
                words = len(content.split())
                speed = words / gen_time if gen_time > 0 else 0
                print_info(f"Estimated speed: {speed:.1f} words/sec")
                
            else:
                print_error("Empty response content")
                return False
        else:
            print_error("Invalid response structure")
            return False
            
    except Exception as e:
        print_error(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Complex Generation Test
    print_step(6, "Testing Complex AI Generation")
    
    complex_messages = [
        {"role": "user", "content": "Explain quantum computing in exactly 2 sentences."}
    ]
    
    try:
        start_time = time.time()
        response = client.generate_chat_completion(complex_messages)
        gen_time = time.time() - start_time
        
        if response and 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            if content and len(content.strip()) > 0:
                print_success(f"Complex generation successful in {gen_time:.2f}s")
                print_info(f"Response: '{content[:150]}{'...' if len(content) > 150 else ''}'")
            else:
                print_error("Empty complex response content")
                return False
        else:
            print_error("Complex generation failed")
            return False
            
    except Exception as e:
        print_error(f"Complex generation failed: {e}")
        return False
    
    # Step 7: Performance Summary
    print_step(7, "Performance Summary")
    
    final_memory = measure_memory()
    memory_change = final_memory - current_memory
    
    print_info(f"Final memory usage: {final_memory:.2f} GB")
    print_info(f"Memory change: {memory_change:+.2f} GB")
    
    if memory_change < 0.5:
        print_success("Excellent memory efficiency")
    elif memory_change < 1.0:
        print_success("Good memory efficiency")
    else:
        print_error("High memory usage detected")
    
    return True

def run_performance_benchmark():
    """Run additional performance benchmarks"""
    print_header("Performance Benchmarks")
    
    try:
        from mlx_lm import load, generate
        from mlx_lm.sample_utils import make_sampler
        
        print_step(1, "Raw MLX Performance Test")
        
        model_path = "./models/mlx/microsoft/Phi-3-mini-4k-instruct-4bit"
        
        # Model loading benchmark
        start = time.time()
        model, tokenizer = load(model_path)
        load_time = time.time() - start
        
        print_info(f"Model load time: {load_time:.2f}s")
        
        # Generation benchmark
        sampler = make_sampler(temp=0.7, top_p=0.9)
        test_prompt = "Write a haiku about technology."
        
        start = time.time()
        response = generate(model, tokenizer, test_prompt, max_tokens=50, sampler=sampler)
        gen_time = time.time() - start
        
        print_info(f"Generation time: {gen_time:.2f}s")
        print_info(f"Response: '{response[:100]}...'")
        
        print_success("Performance benchmark completed")
        
    except Exception as e:
        print_error(f"Performance benchmark failed: {e}")

if __name__ == "__main__":
    print_header("Starting WhisperEngine MLX Validation")
    
    # Load environment
    try:
        from env_manager import load_environment
        if not load_environment():
            print_error("Failed to load environment configuration")
            sys.exit(1)
        print_success("Environment loaded successfully")
    except Exception as e:
        print_error(f"Environment loading error: {e}")
        sys.exit(1)
    
    # Run main test suite
    try:
        success = test_mlx_backend()
        
        if success:
            print_header("SUCCESS: MLX Backend Validation Passed")
            print_success("MLX integration is working correctly!")
            print_info("Ready for production use")
            
            # Run performance benchmarks if main tests pass
            run_performance_benchmark()
            
            sys.exit(0)
        else:
            print_header("FAILURE: MLX Backend Validation Failed")
            print_error("MLX integration has issues that need to be addressed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print_error("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)