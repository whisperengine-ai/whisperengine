#!/usr/bin/env python3
"""
Pre-download all models during Docker build to eliminate runtime downloads.
This script ensures models are bundled in the Docker image.
"""

import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_embedding_models():
    """Download fastembed embedding models"""
    try:
        from fastembed import TextEmbedding
        import os
        
        models_dir = Path("/app/models/embeddings")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Primary embedding model (fastembed approach)
        model_name = "snowflake/snowflake-arctic-embed-xs"
        logger.info(f"📥 Downloading embedding model ({model_name})...")
        
        # Initialize fastembed model (this downloads it to cache)
        embedding_model = TextEmbedding(model_name=model_name)
        
        # Create a test embedding to ensure model works
        test_embedding = list(embedding_model.embed(["test sentence"]))[0]
        logger.info(f"✅ Model verification successful. Embedding dimension: {len(test_embedding)}")
        
        # Save model path info (fastembed handles caching internally)
        model_info = {
            "model_name": model_name,
            "embedding_dimension": len(test_embedding),
            "cache_location": os.path.expanduser("~/.cache/fastembed"),
            "model_type": "fastembed",
            "verified": True
        }
        
        import json
        with open(models_dir / "model_info.json", 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"✅ Embedding model cached and verified: {model_name}")
        logger.info(f"📊 Embedding dimension: {len(test_embedding)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download embedding models: {e}")
        return False

def download_emotion_models():
    """Download emotion analysis models (TextBlob for lightweight analysis)"""
    try:
        # Verify VADER is available
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        test_scores = analyzer.polarity_scores("This is a test message")
        logger.info("✅ VADER emotion analysis verified")
        
        # Initialize TextBlob and download its data
        from textblob import TextBlob
        import ssl
        import nltk
        
        # Handle SSL certificate issues
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
        
        # Download required NLTK data for TextBlob
        logger.info("📥 Downloading TextBlob corpora...")
        nltk.download('punkt', quiet=True)
        nltk.download('brown', quiet=True)
        
        # Test TextBlob functionality
        test_blob = TextBlob("This is a test message for sentiment analysis.")
        test_sentiment = test_blob.sentiment
        logger.info(f"✅ TextBlob verified - polarity: {test_sentiment.polarity:.3f}, subjectivity: {test_sentiment.subjectivity:.3f}")
        
        # Create models directory and save config
        models_dir = Path("/app/models/emotion")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        model_info = {
            "vader": {"available": True, "type": "rule_based"},
            "textblob": {"available": True, "type": "statistical", "polarity_range": [-1, 1]},
            "emotion_methods": ["vader", "textblob", "hybrid"],
            "default_method": "auto"
        }
        
        import json
        with open(models_dir / "emotion_config.json", 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info("✅ Lightweight emotion analysis models configured (VADER + TextBlob)")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import emotion model dependencies: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to setup emotion models: {e}")
        return False

def download_spacy_models():
    """Download spaCy NLP models"""
    try:
        import spacy
        from spacy.cli import download
        
        models_dir = Path("/app/models/spacy")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Download English model
        logger.info("📥 Downloading spaCy model: en_core_web_sm")
        download("en_core_web_sm")
        logger.info("✅ spaCy model en_core_web_sm downloaded successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download spaCy models: {e}")
        return False

def create_model_config():
    """Create configuration file for local model paths"""
    config = {
        "embedding_models": {
            "primary": "snowflake/snowflake-arctic-embed-xs",
            "type": "fastembed",
            "cache_dir": "~/.cache/fastembed"
        },
        "emotion_models": {
            "roberta_sentiment": "/app/models/emotion/roberta-sentiment",
            "vader_available": True,
            "method": "hybrid"
        },
        "spacy_models": {
            "english": "en_core_web_sm"
        },
        "model_cache_dir": "/app/models",
        "offline_mode": True
    }
    
    import json
    config_path = Path("/app/models/model_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("✅ Model configuration saved to /app/models/model_config.json")

def verify_downloads():
    """Verify critical models were downloaded successfully"""
    # Only require the essential embedding model - others are optional
    required_paths = [
        "/app/models/embeddings/model_info.json",
        "/app/models/model_config.json"
    ]
    
    # Optional paths that won't fail the build
    optional_paths = [
        "/app/models/emotion/emotion_config.json"
    ]
    
    all_required_present = True
    for path in required_paths:
        if not Path(path).exists():
            logger.error(f"❌ Missing required: {path}")
            all_required_present = False
        else:
            logger.info(f"✅ Found: {path}")
    
    for path in optional_paths:
        if not Path(path).exists():
            logger.warning(f"⚠️  Missing optional: {path}")
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
    """Main model download orchestrator"""
    logger.info("🚀 Starting model download process...")
    
    # Create base models directory
    Path("/app/models").mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    
    # Download embedding models (required)
    if download_embedding_models():
        success_count += 1
    else:
        logger.error("❌ Failed to download critical embedding models")
        return False
    
    # Download emotion models (optional)
    if download_emotion_models():
        success_count += 1
    else:
        logger.warning("⚠️  Emotion models download failed, continuing without them")
    
    # Download spaCy models (optional)
    if download_spacy_models():
        success_count += 1
    else:
        logger.warning("⚠️  spaCy models download failed, continuing without them")
    
    # Create configuration
    create_model_config()
    
    # Verify critical models are present
    if verify_downloads():
        logger.info("🎉 Critical models downloaded successfully!")
        logger.info(f"💾 Models bundled: {success_count}/3 (1 required embedding + 2 optional)")
        
        # Calculate approximate sizes
        total_size = 0
        for root, dirs, files in os.walk("/app/models"):
            for file in files:
                filepath = os.path.join(root, file)
                total_size += os.path.getsize(filepath)
        
        size_mb = total_size / (1024 * 1024)
        logger.info(f"📊 Total model bundle size: {size_mb:.1f} MB")
        
        return True
    else:
        logger.error("❌ Critical model verification failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)