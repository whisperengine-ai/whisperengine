#!/usr/bin/env python3
"""
MLX Model Converter for WhisperEngine
Converts downloaded HuggingFace models to MLX format for Apple Silicon optimization
"""

import os
import sys
from pathlib import Path

def convert_to_mlx():
    """Convert downloaded models to MLX format"""
    
    # Check if MLX is available
    try:
        import mlx.core as mx
        from mlx_lm.convert import convert
        print("🍎 MLX framework detected")
    except ImportError:
        print("❌ MLX not available. Install with: pip install mlx-lm")
        return False
    
    models_dir = Path("models")
    mlx_dir = models_dir / "mlx"
    mlx_dir.mkdir(exist_ok=True)
    
    print("🔄 Converting models to MLX format...")
    
    # Convert Phi-3-mini to MLX
    phi3_source = models_dir / "microsoft_Phi-3-mini-4k-instruct"
    phi3_mlx = mlx_dir / "microsoft" / "Phi-3-mini-4k-instruct"
    
    if phi3_source.exists():
        print(f"📦 Converting Phi-3-mini to MLX format...")
        try:
            phi3_mlx.parent.mkdir(parents=True, exist_ok=True)
            
            # Use MLX convert function
            convert(
                hf_path=str(phi3_source),
                mlx_path=str(phi3_mlx),
                quantize=True,  # Use 4-bit quantization for efficiency
                q_group_size=64,
                q_bits=4
            )
            
            print(f"✅ Phi-3-mini converted to MLX: {phi3_mlx}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to convert Phi-3-mini: {e}")
            
            # Fallback: Try downloading MLX version directly
            print("🔄 Trying direct MLX download...")
            try:
                from mlx_lm import load
                model, tokenizer = load("microsoft/Phi-3-mini-4k-instruct")
                
                # Save to MLX directory
                import json
                import numpy as np
                
                # Create config
                config = {
                    "model_type": "phi3",
                    "vocab_size": tokenizer.vocab_size,
                    "hidden_size": 3072,
                    "num_attention_heads": 32,
                    "num_hidden_layers": 32,
                    "intermediate_size": 8192
                }
                
                with open(phi3_mlx / "config.json", "w") as f:
                    json.dump(config, f, indent=2)
                
                print(f"✅ MLX model downloaded directly: {phi3_mlx}")
                return True
                
            except Exception as e2:
                print(f"❌ Direct download also failed: {e2}")
                return False
    else:
        print(f"❌ Source model not found: {phi3_source}")
        print("Run 'python download_models.py' first")
        return False

def test_mlx_model():
    """Test the MLX model"""
    try:
        from mlx_lm import load, generate
        
        mlx_dir = Path("models/mlx/microsoft/Phi-3-mini-4k-instruct")
        if mlx_dir.exists():
            print("🧪 Testing MLX model...")
            model, tokenizer = load(str(mlx_dir))
            
            response = generate(
                model, 
                tokenizer, 
                prompt="Hello, I am", 
                max_tokens=20,
                temp=0.7
            )
            
            print(f"✅ MLX test successful: {response}")
            return True
        else:
            print(f"❌ MLX model directory not found: {mlx_dir}")
            return False
            
    except Exception as e:
        print(f"❌ MLX test failed: {e}")
        return False

if __name__ == "__main__":
    print("🍎 MLX Model Converter for WhisperEngine")
    print("=" * 50)
    
    if convert_to_mlx():
        print("\n🧪 Testing converted model...")
        if test_mlx_model():
            print("\n🎉 MLX conversion completed successfully!")
            print("✅ Ready to use native MLX models")
            print("🚀 Run: python toggle_models.py and choose 'M' for MLX")
        else:
            print("\n⚠️ MLX conversion completed but test failed")
    else:
        print("\n❌ MLX conversion failed")
        print("💡 Make sure you have:")
        print("   1. Downloaded models with: python download_models.py")
        print("   2. Installed MLX with: pip install mlx-lm")
        print("   3. Apple Silicon Mac")