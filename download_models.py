#!/usr/bin/env python3
"""
Model Download and Bundling Script for WhisperEngine Desktop App
Downloads and prepares Hugging Face models for offline use
"""

import os
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
import shutil

def download_models():
    """Download all required models for offline use"""
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    print("🔄 Downloading required models for offline bundling...")
    
    # Primary embedding model
    embedding_models = [
        "all-mpnet-base-v2",  # Primary embedding model (768 dim)
    ]
    
    for model_name in embedding_models:
        print(f"\n📦 Downloading {model_name}...")
        try:
            # Download and cache the model
            model = SentenceTransformer(model_name)
            
            # Save model to local directory
            model_path = models_dir / model_name
            model.save(str(model_path))
            print(f"✅ {model_name} saved to {model_path}")
            
        except Exception as e:
            print(f"❌ Failed to download {model_name}: {e}")
    
    # Download small LLM for quick-start testing
    print(f"\n🤖 Downloading Phi-3-Mini model for offline testing...")
    small_llms = [
        {
            "name": "microsoft/Phi-3-mini-4k-instruct", 
            "size": "~2GB",
            "description": "High-quality 4K context conversational model"
        }
    ]
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        for llm_info in small_llms:
            model_name = llm_info["name"]
            print(f"📦 Downloading {model_name} ({llm_info['size']}) - {llm_info['description']}...")
            try:
                model_path = models_dir / model_name.replace("/", "_")
                model_path.mkdir(exist_ok=True)
                
                # Download tokenizer and model
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForCausalLM.from_pretrained(model_name)
                
                # Add padding token if missing (needed for DialoGPT)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                # Save locally
                tokenizer.save_pretrained(str(model_path))
                model.save_pretrained(str(model_path))
                
                print(f"✅ {model_name} saved to {model_path}")
                
            except Exception as e:
                print(f"❌ Failed to download {model_name}: {e}")
                
    except ImportError:
        print("⚠️ transformers library not available, skipping LLM models")
    
    # Download emotion analysis models (required for emotional intelligence features)
    emotion_models = [
        "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "j-hartmann/emotion-english-distilroberta-base"  # Used for emotion classification
    ]
    
    print(f"\n🎭 Downloading emotion analysis models (required for AI features)...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        
        for model_name in emotion_models:
            print(f"📦 Downloading {model_name}...")
            try:
                model_path = models_dir / model_name.replace("/", "_")
                
                # Download tokenizer and model
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSequenceClassification.from_pretrained(model_name)
                
                # Save locally
                tokenizer.save_pretrained(str(model_path))
                model.save_pretrained(str(model_path))
                
                print(f"✅ {model_name} saved to {model_path}")
                
            except Exception as e:
                print(f"❌ Failed to download {model_name}: {e}")
                
    except ImportError:
        print("⚠️ transformers library not available, skipping emotion models")
    
    print(f"\n✅ Model download completed! Models saved in: {models_dir.absolute()}")
    print(f"Total size: {get_directory_size(models_dir):.1f} MB")

def download_embeddings_only():
    """Download only embedding models for minimal setup"""
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    print("🔄 Downloading minimal models (embeddings only)...")
    
    # Primary embedding model
    embedding_models = [
        "all-mpnet-base-v2",  # Primary embedding model (768 dim)
    ]
    
    for model_name in embedding_models:
        print(f"\n📦 Downloading {model_name}...")
        try:
            # Download and cache the model
            model = SentenceTransformer(model_name)
            
            # Save model to local directory
            model_path = models_dir / model_name
            model.save(str(model_path))
            print(f"✅ {model_name} saved to {model_path}")
            
        except Exception as e:
            print(f"❌ Failed to download {model_name}: {e}")
    
    print(f"\n✅ Minimal model download completed! Models saved in: {models_dir.absolute()}")
    print(f"Total size: {get_directory_size(models_dir):.1f} MB")

def get_directory_size(path):
    """Calculate directory size in MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)

def update_desktop_config():
    """Update .env.desktop to use local models"""
    
    desktop_env = Path(".env.desktop")
    if not desktop_env.exists():
        print("⚠️ .env.desktop not found, skipping config update")
        return
    
    print("\n🔧 Updating .env.desktop to use local models...")
    
    # Read current config
    with open(desktop_env, 'r') as f:
        content = f.read()
    
    # Add local model configuration
    local_config = '''

# =============================================================================
# LOCAL MODEL CONFIGURATION (Offline Models)
# =============================================================================
# Use bundled local models instead of downloading from internet
USE_LOCAL_MODELS=true
LOCAL_MODELS_DIR=./models
LLM_LOCAL_EMBEDDING_MODEL=all-mpnet-base-v2
FALLBACK_EMBEDDING_MODEL=all-mpnet-base-v2

# Bundled LLM Configuration (Quick-start testing)
# =============================================================================
# Enable local LLM for offline testing
USE_LOCAL_LLM=true
LOCAL_LLM_MODEL=microsoft_Phi-3-mini-4k-instruct
LLM_CHAT_API_URL=local://models  # Special URL for local LLM loading

# Fallback to external LLM if local fails
# LLM_CHAT_API_URL=http://localhost:1234/v1  # LM Studio
# LLM_MODEL_NAME=llama3.1:8b

# Disable external model downloads
HF_DATASETS_OFFLINE=1
TRANSFORMERS_OFFLINE=1
'''
    
    if "LOCAL_MODELS_DIR" not in content:
        with open(desktop_env, 'a') as f:
            f.write(local_config)
        print("✅ Added local model configuration to .env.desktop")
    else:
        print("✅ Local model configuration already exists")

def create_model_loader():
    """Create a helper script for loading local models"""
    
    loader_content = '''"""
Local Model Loader for WhisperEngine Desktop App
Loads pre-downloaded models from local directory
"""

import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class LocalModelManager:
    """Manages local model loading for offline use"""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.loaded_models = {}
    
    def load_embedding_model(self, model_name: str = "all-mpnet-base-v2"):
        """Load local embedding model"""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        model_path = self.models_dir / model_name
        
        if model_path.exists():
            logger.info(f"Loading local embedding model: {model_path}")
            model = SentenceTransformer(str(model_path))
            self.loaded_models[model_name] = model
            return model
        else:
            logger.warning(f"Local model not found: {model_path}, falling back to online")
            model = SentenceTransformer(model_name)
            self.loaded_models[model_name] = model
            return model
    
    def load_emotion_model(self, model_name: str):
        """Load local emotion analysis model"""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        safe_name = model_name.replace("/", "_")
        model_path = self.models_dir / safe_name
        
        if model_path.exists():
            logger.info(f"Loading local emotion model: {model_path}")
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                tokenizer = AutoTokenizer.from_pretrained(str(model_path))
                model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
                self.loaded_models[model_name] = (tokenizer, model)
                return tokenizer, model
            except ImportError:
                logger.error("transformers library not available")
                return None, None
        else:
            logger.warning(f"Local emotion model not found: {model_path}")
            return None, None
    
    def get_available_models(self):
        """List available local models"""
        if not self.models_dir.exists():
            return []
        
        models = []
        for item in self.models_dir.iterdir():
            if item.is_dir():
                models.append(item.name)
        return models

# Global model manager instance
model_manager = LocalModelManager()

def get_local_embedding_model(model_name: str = "all-mpnet-base-v2"):
    """Convenience function to get local embedding model"""
    return model_manager.load_embedding_model(model_name)

def get_local_emotion_model(model_name: str):
    """Convenience function to get local emotion model"""
    return model_manager.load_emotion_model(model_name)
'''
    
    loader_file = Path("src/utils/local_model_loader.py")
    with open(loader_file, 'w') as f:
        f.write(loader_content)
    
    print(f"✅ Created local model loader: {loader_file}")

def create_build_integration():
    """Create build script modifications for PyInstaller"""
    
    build_config = '''
# PyInstaller Build Configuration for Bundled Models
# Add this to your .spec files

# In the Analysis section, add models to datas:
datas=[
    ('models', 'models'),  # Bundle models directory
    # ... other data files
],

# In the Analysis section, add hidden imports:
hiddenimports=[
    'sentence_transformers',
    'transformers',
    'torch',
    'numpy',
    'sklearn',
    # ... other hidden imports
],

# Environment variables for offline mode
# Set these in your build environment:
# export HF_DATASETS_OFFLINE=1
# export TRANSFORMERS_OFFLINE=1
'''
    
    build_file = Path("build_models_config.txt")
    with open(build_file, 'w') as f:
        f.write(build_config)
    
    print(f"✅ Created build configuration guide: {build_file}")

def main():
    """Main function"""
    print("🚀 WhisperEngine Model Bundling Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("universal_native_app.py").exists():
        print("❌ Please run this script from the WhisperEngine root directory")
        sys.exit(1)
    
    # All AI features are enabled by default, so download all models
    print("📦 Downloading all models for full WhisperEngine functionality")
    print("� This includes: Phi-3-Mini, embeddings, and emotion analysis models")
    
    try:
        download_models()  # Download all models - emotions are now mandatory
        update_desktop_config()
        create_model_loader()
        create_build_integration()
        
        print("\n🎉 Model bundling setup completed!")
        print("\nNext steps:")
        print("1. The models are now downloaded in ./models/")
        print("2. Desktop config updated to use local models")
        print("3. Use the LocalModelManager for offline model loading")
        print("4. Update your build process to include the models directory")
        print("5. Set HF_DATASETS_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 in production")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()