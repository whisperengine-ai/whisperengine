from typing import List, Optional
from fastembed import TextEmbedding
from loguru import logger

class EmbeddingService:
    """
    Service for generating vector embeddings using FastEmbed.
    Defaults to 'sentence-transformers/all-MiniLM-L6-v2' (384 dimensions).
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model: Optional[TextEmbedding] = None
        
    @property
    def model(self) -> TextEmbedding:
        """Lazy loading of the model to avoid startup overhead if not used."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = TextEmbedding(model_name=self.model_name)
            logger.info("Embedding model loaded successfully.")
        return self._model

    def embed_query(self, text: str) -> List[float]:
        """Embed a single string query."""
        # list(self.model.embed([text])) returns a generator of numpy arrays
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

    async def embed_query_async(self, text: str) -> List[float]:
        """Embed a single string query asynchronously."""
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.embed_query, text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]
