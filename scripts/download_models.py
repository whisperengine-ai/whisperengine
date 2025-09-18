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
    """Download sentence-transformers embedding models"""
    try:
        from sentence_transformers import SentenceTransformer
        
        models_dir = Path("/app/models/embeddings")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Primary embedding model (single model approach)
        logger.info("📥 Downloading embedding model (MiniLM-L6-v2)...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding_model.save(str(models_dir / 'all-MiniLM-L6-v2'))
        logger.info("✅ Embedding model saved to /app/models/embeddings/all-MiniLM-L6-v2")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download embedding models: {e}")
        return False

def download_emotion_models():
    """Download transformers emotion analysis models"""
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        
        models_dir = Path("/app/models/emotion")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # RoBERTa emotion model
        model_name = 'cardiffnlp/twitter-roberta-base-sentiment-latest'
        logger.info(f"📥 Downloading emotion model: {model_name}")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Save locally
        tokenizer.save_pretrained(str(models_dir / 'roberta-sentiment'))
        model.save_pretrained(str(models_dir / 'roberta-sentiment'))
        
        logger.info("✅ Emotion model saved to /app/models/emotion/roberta-sentiment")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download emotion models: {e}")
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
            "primary": "/app/models/embeddings/all-MiniLM-L6-v2"
        },
        "emotion_models": {
            "roberta_sentiment": "/app/models/emotion/roberta-sentiment"
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
    """Verify all models were downloaded successfully"""
    required_paths = [
        "/app/models/embeddings/all-MiniLM-L6-v2", 
        "/app/models/emotion/roberta-sentiment",
        "/app/models/model_config.json"
    ]
    
    all_present = True
    for path in required_paths:
        if not Path(path).exists():
            logger.error(f"❌ Missing: {path}")
            all_present = False
        else:
            logger.info(f"✅ Found: {path}")
    
    return all_present

def main():
    """Main model download orchestrator"""
    logger.info("🚀 Starting model download process...")
    
    # Create base models directory
    Path("/app/models").mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    
    # Download each model type
    if download_embedding_models():
        success_count += 1
    
    if download_emotion_models():
        success_count += 1
    
    if download_spacy_models():
        success_count += 1
    
    # Create configuration
    create_model_config()
    
    # Verify everything downloaded
    if verify_downloads():
        logger.info("🎉 All models downloaded successfully!")
        logger.info("💾 Total models bundled: 3 (1 embedding + 1 emotion + 1 spaCy)")
        
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
        logger.error("❌ Model download verification failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)