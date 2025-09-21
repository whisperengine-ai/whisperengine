#!/usr/bin/env python3
"""
Pre-download vector-native models during Docker build.
This script only downloads models needed for the vector-native architecture:
- FastEmbed embedding models only
- No legacy spaCy or VADER models needed
"""

import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_embedding_models():
    """Download fastembed embedding models - ONLY vector-native models needed"""
    try:
        from fastembed import TextEmbedding
        import os
        
        models_dir = Path("/app/models/embeddings")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Primary embedding model (fastembed approach)
        model_name = "snowflake/snowflake-arctic-embed-xs"
        logger.info(f"📥 Downloading vector-native embedding model ({model_name})...")
        
        # Initialize fastembed model (this downloads it to cache)
        embedding_model = TextEmbedding(model_name=model_name)
        
        # Create a test embedding to ensure model works
        test_embedding = list(embedding_model.embed(["test sentence"]))[0]
        logger.info(f"✅ Vector-native model verification successful. Embedding dimension: {len(test_embedding)}")
        
        # Save model path info (fastembed handles caching internally)
        model_info = {
            "model_name": model_name,
            "embedding_dimension": len(test_embedding),
            "cache_location": os.path.expanduser("~/.cache/fastembed"),
            "model_type": "fastembed",
            "architecture": "vector_native",
            "verified": True
        }
        
        import json
        with open(models_dir / "model_info.json", 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"✅ Vector-native embedding model ready: {model_name}")
        logger.info(f"📊 Embedding dimension: {len(test_embedding)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download vector-native embedding models: {e}")
        return False

def create_model_config():
    """Create configuration file for vector-native model paths"""
    config = {
        "embedding_models": {
            "primary": "snowflake/snowflake-arctic-embed-xs",
            "type": "fastembed",
            "cache_dir": "~/.cache/fastembed"
        },
        "architecture": "vector_native",
        "emotion_analysis": "vector_embedded",  # No separate emotion models needed
        "personality_analysis": "vector_embedded",  # No separate personality models needed
        "model_cache_dir": "/app/models",
        "legacy_nlp_removed": True,
        "docker_optimized": True
    }
    
    import json
    config_path = Path("/app/models/model_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("✅ Model configuration saved to /app/models/model_config.json")

def verify_downloads():
    """Verify vector-native models were downloaded successfully"""
    # Only require the essential embedding model for vector-native architecture
    required_paths = [
        "/app/models/embeddings/model_info.json",
        "/app/models/model_config.json"
    ]
    
    all_required_present = True
    for path in required_paths:
        if not Path(path).exists():
            logger.error(f"❌ Missing required vector-native model: {path}")
            all_required_present = False
        else:
            logger.info(f"✅ Found: {path}")
    
    # Verify fastembed cache exists
    import os
    fastembed_cache = os.path.expanduser("~/.cache/fastembed")
    if os.path.exists(fastembed_cache):
        logger.info(f"✅ FastEmbed cache found: {fastembed_cache}")
    else:
        logger.warning(f"⚠️  FastEmbed cache not found: {fastembed_cache}")
    
    return all_required_present

def main():
    """Main vector-native model download orchestrator"""
    logger.info("🚀 Starting vector-native model download process...")
    
    # Create base models directory
    Path("/app/models").mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    
    # Download embedding models (ONLY required for vector-native)
    if download_embedding_models():
        success_count += 1
        logger.info("✅ Vector-native embedding models ready")
    else:
        logger.error("❌ Failed to download critical vector-native embedding models")
        return False
    
    # Create configuration
    create_model_config()
    
    # Verify critical models are present
    if verify_downloads():
        logger.info("🎉 Vector-native models downloaded successfully!")
        logger.info("� Docker image optimization: Legacy NLP models (spaCy/VADER) removed")
        
        # Calculate approximate sizes
        total_size = 0
        for root, dirs, files in os.walk("/app/models"):
            for file in files:
                filepath = os.path.join(root, file)
                total_size += os.path.getsize(filepath)
        
        size_mb = total_size / (1024 * 1024)
        logger.info(f"📊 Total model bundle size: {size_mb:.1f} MB (dramatically reduced!)")
        logger.info("🎯 Vector-native architecture: emotion/personality via embeddings")
        
        return True
    else:
        logger.error("❌ Vector-native model verification failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)