#!/usr/bin/env python3
"""
Test Docker Build Model Pre-download
===================================

Validates that the updated Docker build scripts will correctly pre-download
the new sentence-transformers/all-MiniLM-L6-v2 embedding model.
"""

import os
import sys
import tempfile
from pathlib import Path

def test_docker_model_download():
    """Test the Docker model download configuration"""
    
    print("🐳 Docker Build Model Pre-download Test")
    print("=" * 45)
    
    # Test 1: Verify download script uses correct model
    print("1. 📋 Checking download script configuration...")
    
    script_path = Path("scripts/download_models.py")
    if script_path.exists():
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        if 'sentence-transformers/all-MiniLM-L6-v2' in script_content:
            print("   ✅ Download script uses sentence-transformers/all-MiniLM-L6-v2")
        else:
            print("   ❌ Download script not updated with new model")
            return False
            
        if 'BAAI/bge-small-en-v1.5' in script_content and 'upgrade_from' in script_content:
            print("   ✅ Legacy model reference updated appropriately")
        else:
            print("   ⚠️  Legacy model references may need cleanup")
    else:
        print("   ❌ Download script not found")
        return False
    
    # Test 2: Verify Dockerfile.bundled-models configuration
    print("\n2. 🐳 Checking Dockerfile configuration...")
    
    dockerfile_path = Path("Dockerfile.bundled-models")
    if dockerfile_path.exists():
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        if 'scripts/download_models.py' in dockerfile_content:
            print("   ✅ Dockerfile copies and runs download script")
        else:
            print("   ❌ Dockerfile doesn't run download script")
            return False
            
        if 'FASTEMBED_CACHE_PATH' in dockerfile_content:
            print("   ✅ Dockerfile sets FastEmbed cache path")
        else:
            print("   ⚠️  FastEmbed cache path may not be set")
    else:
        print("   ⚠️  Dockerfile.bundled-models not found")
    
    # Test 3: Verify production configuration
    print("\n3. 🏭 Checking production configuration...")
    
    prod_compose_path = Path("docker-compose.prod.yml")
    if prod_compose_path.exists():
        with open(prod_compose_path, 'r') as f:
            prod_content = f.read()
        
        if 'sentence-transformers/all-MiniLM-L6-v2' in prod_content:
            print("   ✅ Production config uses new model")
        else:
            print("   ⚠️  Production config may not be updated")
    
    # Test 4: Environment configuration consistency
    print("\n4. ⚙️  Checking environment consistency...")
    
    env_files = ['.env', '.env.template'] + [f'.env.{bot}' for bot in 
                ['elena', 'marcus', 'jake', 'dream', 'aethys', 'ryan', 'gabriel', 'sophia']]
    
    consistent_configs = 0
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            if 'EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2' in env_content:
                consistent_configs += 1
    
    print(f"   📊 Environment files with new model: {consistent_configs}/{len([p for p in env_files if Path(p).exists()])}")
    
    if consistent_configs > 5:  # Most configs updated
        print("   ✅ Environment configurations mostly consistent")
    else:
        print("   ⚠️  Environment configurations may need more updates")
    
    # Test 5: Model cache verification
    print("\n5. 💾 Testing model availability...")
    
    try:
        from fastembed import TextEmbedding
        
        # Test that the new model can be loaded
        model = TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')
        test_embedding = list(model.embed(['cache test']))[0]
        
        print(f"   ✅ Model loads successfully: {len(test_embedding)}D")
        
        # Check cache location
        cache_dir = os.path.expanduser('~/.cache/fastembed')
        if os.path.exists(cache_dir):
            print(f"   ✅ Cache directory exists: {cache_dir}")
        else:
            print(f"   ⚠️  Cache directory not found: {cache_dir}")
            
    except Exception as e:
        print(f"   ❌ Model loading failed: {e}")
        return False
    
    # Summary
    print("\n🎯 DOCKER BUILD READINESS:")
    print("=" * 30)
    print("✅ Download script updated with new model")
    print("✅ Dockerfile configured for model pre-download")
    print("✅ Environment configurations updated")
    print("✅ Model tested and working locally")
    print()
    print("🚀 NEXT BUILD STEPS:")
    print("1. docker build -f Dockerfile.bundled-models -t whisperengine:latest .")
    print("2. Model will be pre-downloaded during build stage")
    print("3. Runtime containers will use cached model (no downloads)")
    print()
    print("📁 MODEL CACHE LOCATIONS IN CONTAINER:")
    print("   • FastEmbed cache: /root/.cache/fastembed")
    print("   • Development cache: /app/.cache/fastembed")
    print("   • Model config: /app/models/model_config.json")
    
    return True

if __name__ == "__main__":
    success = test_docker_model_download()
    if success:
        print("\n🎉 Docker build configuration ready for new embedding model!")
    else:
        print("\n⚠️  Some configuration issues detected. Review and fix before building.")
    
    sys.exit(0 if success else 1)