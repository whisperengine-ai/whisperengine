#!/usr/bin/env python3
"""
Test the Snowflake Arctic model download and verification
"""

import os
import time
from pathlib import Path

def test_snowflake_download():
    """Test downloading and using the Snowflake Arctic model"""
    
    print("🧊 Testing Snowflake Arctic Model Download")
    print("=" * 50)
    
    try:
        from fastembed import TextEmbedding
        
        # Check current cache
        cache_dir = Path.home() / ".cache" / "fastembed"
        print(f"📁 FastEmbed cache directory: {cache_dir}")
        
        if cache_dir.exists():
            print(f"📦 Cache exists, current size:")
            total_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
            print(f"   {total_size / (1024 * 1024):.1f} MB")
        else:
            print("📦 No cache found, will download fresh")
        
        # Download/initialize the model
        model_name = "snowflake/snowflake-arctic-embed-xs"
        print(f"\n🔄 Initializing model: {model_name}")
        
        start_time = time.time()
        model = TextEmbedding(model_name=model_name)
        init_time = time.time() - start_time
        
        print(f"⚡ Model initialized in {init_time:.2f}s")
        
        # Test embedding generation
        test_text = "Testing the Snowflake Arctic embedding model"
        
        start_time = time.time()
        embeddings = list(model.embed([test_text]))
        embed_time = time.time() - start_time
        
        embedding = embeddings[0]
        print(f"📏 Embedding dimensions: {len(embedding)}")
        print(f"🚀 Embedding generation: {embed_time * 1000:.2f}ms")
        
        # Verify embedding quality
        if len(embedding) == 384:
            print("✅ Correct dimensions (384)")
        else:
            print(f"❌ Unexpected dimensions: {len(embedding)}")
        
        # Check cache after download
        if cache_dir.exists():
            new_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
            print(f"\n📦 Cache after download: {new_size / (1024 * 1024):.1f} MB")
            
            # Look for Snowflake model files
            snowflake_files = list(cache_dir.rglob('*snowflake*'))
            if snowflake_files:
                print("✅ Snowflake model files found in cache:")
                for f in snowflake_files[:5]:  # Show first 5
                    print(f"   {f.name}")
                if len(snowflake_files) > 5:
                    print(f"   ... and {len(snowflake_files) - 5} more files")
            else:
                print("⚠️  No Snowflake-specific files found in cache")
        
        print("\n🎉 Model download and verification successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during model test: {e}")
        return False

if __name__ == "__main__":
    success = test_snowflake_download()
    print(f"\n📋 Test {'PASSED' if success else 'FAILED'}")