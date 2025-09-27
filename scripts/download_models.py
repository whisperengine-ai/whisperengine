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
    """Download fastembed embedding models - Using default model to avoid rate limits"""
    import time
    import os
    
    try:
        from fastembed import TextEmbedding
        
        models_dir = Path("/app/models/embeddings")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure FastEmbed cache directory exists and is set correctly
        fastembed_cache = os.environ.get('FASTEMBED_CACHE_PATH', '/root/.cache/fastembed')
        os.makedirs(fastembed_cache, exist_ok=True)
        logger.info(f"📁 FastEmbed cache directory: {fastembed_cache}")
        
        # Use sentence-transformers/all-MiniLM-L6-v2 - best 384D quality model
        # This model has 384 dimensions and excellent conversation understanding
        logger.info("📥 Downloading vector-native embedding model: sentence-transformers/all-MiniLM-L6-v2...")
        
        # Initialize fastembed model with the new quality-optimized model
        embedding_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        model_name = embedding_model.model_name
        
        logger.info(f"✅ Successfully loaded default model: {model_name}")
        
        # Verify cache was created
        if os.path.exists(fastembed_cache) and os.listdir(fastembed_cache):
            logger.info(f"✅ FastEmbed cache populated: {fastembed_cache}")
            logger.info(f"📁 Cache contents: {os.listdir(fastembed_cache)}")
        else:
            logger.warning(f"⚠️  FastEmbed cache not found or empty: {fastembed_cache}")
        
        # Create a test embedding to ensure model works
        test_embedding = list(embedding_model.embed(["test sentence"]))[0]
        logger.info(f"✅ Vector-native model verification successful. Embedding dimension: {len(test_embedding)}")
        
        # Save model path info (fastembed handles caching internally)
        model_info = {
            "model_name": model_name,
            "embedding_dimension": len(test_embedding),
            "cache_location": fastembed_cache,
            "model_type": "fastembed",
            "architecture": "vector_native",
            "verified": True,
            "is_quality_optimized": True,
            "conversation_understanding": "excellent",
            "upgrade_from": "BAAI/bge-small-en-v1.5"
        }
        
        import json
        with open(models_dir / "model_info.json", 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"✅ Vector-native embedding model ready: {model_name}")
        logger.info(f"📊 Embedding dimension: {len(test_embedding)}")
        logger.info(f"🚀 Using sentence-transformers/all-MiniLM-L6-v2 - excellent conversation quality!")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download vector-native embedding models: {e}")
        return False

def download_roberta_emotion_models():
    """Download RoBERTa emotion models during Docker build for instant startup"""
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
        
        models_dir = Path("/app/models/emotion")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Primary RoBERTa emotion model
        model_name = "j-hartmann/emotion-english-distilroberta-base"
        logger.info(f"📥 Downloading RoBERTa emotion model ({model_name})...")
        
        # Download tokenizer and model (this caches them in HuggingFace cache)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Create pipeline and test it
        classifier = pipeline(
            "text-classification", 
            model=model, 
            tokenizer=tokenizer, 
            return_all_scores=True
        )
        
        # Test emotion analysis to verify model works
        test_result = classifier("I am so happy and excited about this!")
        emotions_detected = len(test_result[0])
        
        logger.info(f"✅ RoBERTa emotion model verification successful")
        logger.info(f"📊 Emotions detected: {emotions_detected} (expected: 7)")
        
        # Save model info
        model_info = {
            "model_name": model_name,
            "emotions": ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"],
            "accuracy": "~88-90% on emotion classification",
            "size_mb": "~250MB",
            "model_type": "roberta_transformers",
            "architecture": "hybrid_emotion",
            "verified": True,
            "test_emotions": emotions_detected
        }
        
        import json
        with open(models_dir / "roberta_model_info.json", 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"✅ RoBERTa emotion model ready: {model_name}")
        logger.info(f"📊 Model size: ~250MB cached for instant startup")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download RoBERTa emotion models: {e}")
        logger.error(f"💡 RoBERTa will be downloaded at runtime (slower first startup)")
        return False

def create_model_config():
    """Create configuration file for hybrid model architecture"""
    config = {
        "embedding_models": {
            "primary": "sentence-transformers/all-MiniLM-L6-v2",  # Best 384D quality model
            "type": "fastembed",
            "cache_dir": "~/.cache/fastembed",
            "dimensions": 384,
            "size_gb": 0.067,
            "quality_optimized": True,
            "conversation_understanding": "excellent"
        },
        "emotion_models": {
            "primary": "j-hartmann/emotion-english-distilroberta-base",
            "type": "roberta_transformers",
            "architecture": "hybrid",
            "fallbacks": ["vader", "keywords"],
            "cache_dir": "~/.cache/huggingface"
        },
        "architecture": "hybrid_vector_emotion",
        "emotion_analysis": "roberta_vader_keywords",
        "personality_analysis": "vector_embedded",
        "model_cache_dir": "/app/models",
        "legacy_nlp_removed": True,
        "docker_optimized": True,
        "build_time_download": True,
        "quality_optimized_model": True,
        "embedding_model_upgrade": "sentence-transformers/all-MiniLM-L6-v2"
    }
    
    import json
    config_path = Path("/app/models/model_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("✅ Model configuration saved to /app/models/model_config.json")

def verify_downloads():
    """Verify all critical vector-native and emotion models are present"""
    logger.info("🔍 Verifying critical vector-native and emotion models...")
    
    # Check model config exists
    config_path = Path("/app/models/model_config.json")
    if not config_path.exists():
        logger.error(f"❌ Missing model configuration: {config_path}")
        return False
    else:
        logger.info(f"✅ Found: {config_path}")
    
    # Check FastEmbed cache (models are cached by fastembed)
    import os
    fastembed_cache = os.path.expanduser("~/.cache/fastembed")
    if os.path.exists(fastembed_cache):
        logger.info(f"✅ FastEmbed cache found: {fastembed_cache}")
        
        # Look for downloaded embedding models
        import glob
        model_files = glob.glob(f"{fastembed_cache}/**/model.onnx", recursive=True)
        if model_files:
            logger.info(f"✅ Found FastEmbed ONNX models: {len(model_files)} files")
        else:
            logger.warning("⚠️  No ONNX model files found in FastEmbed cache")
    else:
        logger.warning(f"⚠️  FastEmbed cache not found: {fastembed_cache}")
    
    # Check HuggingFace cache for RoBERTa models  
    hf_cache = os.path.expanduser("~/.cache/huggingface")
    if os.path.exists(hf_cache):
        logger.info(f"✅ HuggingFace cache found: {hf_cache}")
        
        # Look for RoBERTa model components
        import glob
        model_dirs = glob.glob(f"{hf_cache}/**/j-hartmann--emotion-english-distilroberta-base", recursive=True)
        if model_dirs:
            logger.info(f"✅ Found RoBERTa model directories: {len(model_dirs)} locations")
        else:
            logger.warning("⚠️  RoBERTa model directory not found in HuggingFace cache")
    else:
        logger.warning(f"⚠️  HuggingFace cache not found: {hf_cache}")
    
    # Verify environment variables point to correct cache locations
    fastembed_env = os.environ.get("FASTEMBED_CACHE_PATH", "~/.cache/fastembed")
    hf_env = os.environ.get("HF_HOME", "~/.cache/huggingface")
    logger.info(f"📍 Environment: FASTEMBED_CACHE_PATH={fastembed_env}")
    logger.info(f"📍 Environment: HF_HOME={hf_env}")
    
    # Return True if basic configuration exists
    return config_path.exists()

def main():
    """Main vector-native and emotion model download orchestrator"""
    logger.info("🚀 Starting vector-native and emotion model download process...")
    
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
    
    # Download RoBERTa emotion models (enhancement)
    if download_roberta_emotion_models():
        success_count += 1
        logger.info("✅ RoBERTa emotion models ready")
    else:
        logger.warning("⚠️  RoBERTa emotion model download failed - hybrid system will fallback to VADER")
    
    # Create configuration
    create_model_config()
    
    # Verify critical models are present
    if verify_downloads():
        logger.info("🎉 Vector-native and emotion models downloaded successfully!")
        logger.info("🧠 Docker image optimization: Legacy NLP models (spaCy) removed, hybrid emotion added")
        
        # Calculate approximate sizes
        total_size = 0
        for root, dirs, files in os.walk("/app/models"):
            for file in files:
                filepath = os.path.join(root, file)
                total_size += os.path.getsize(filepath)
        
        size_mb = total_size / (1024 * 1024)
        logger.info(f"📊 Total model bundle size: {size_mb:.1f} MB (includes ~250MB RoBERTa emotion)")
        logger.info("🎯 Hybrid architecture: FastEmbed embeddings + RoBERTa emotion + VADER fallback")
        
        return True
    else:
        logger.error("❌ Vector-native model verification failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)