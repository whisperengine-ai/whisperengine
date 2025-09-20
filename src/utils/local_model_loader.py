"""
Local Model Loader for WhisperEngine Desktop App
Loads pre-downloaded models from local directory
"""

import logging
from pathlib import Path

from fastembed import TextEmbedding

logger = logging.getLogger(__name__)


class LocalModelManager:
    """Manages local model loading for offline use"""

    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.loaded_models = {}

    def load_embedding_model(self, model_name: str = "snowflake/snowflake-arctic-embed-xs"):
        """Load local embedding model"""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]

        model_path = self.models_dir / model_name

        if model_path.exists():
            logger.info(f"Loading local embedding model: {model_path}")
            model = TextEmbedding(model_name=model_name, cache_dir=str(model_path))
            self.loaded_models[model_name] = model
            return model
        else:
            logger.warning(f"Local model not found: {model_path}, falling back to online")
            model = TextEmbedding(model_name=model_name)
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
                from transformers import AutoModelForSequenceClassification, AutoTokenizer

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
