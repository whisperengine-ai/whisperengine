"""
DEPRECATED: ChromaDB External Embedding Extension
This module was deprecated and removed in v2.4.0 (September 2025).
All embedding functionality now uses local models only.

This file is kept for historical reference - all functions return no-op behavior.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def add_documents_with_embeddings(
    collection, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]
) -> bool:
    """
    DEPRECATED: Add documents using external embeddings.
    This function is deprecated as of v2.4.0 (September 2025).
    Returns False to indicate external embeddings are no longer supported.
    """
    logger.warning("External embedding functionality deprecated - use ChromaDB built-in embeddings")
    return False


async def query_with_embeddings(
    collection, query_texts: list[str], n_results: int = 10, where: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    DEPRECATED: Query collection using external embeddings.
    This function is deprecated as of v2.4.0 (September 2025).
    Returns empty results to indicate external embeddings are no longer supported.
    """
    logger.warning("External embedding functionality deprecated - use ChromaDB built-in query")
    return {"documents": [], "metadatas": [], "ids": [], "distances": []}


def run_async_method(async_method, *args, **kwargs):
    """
    DEPRECATED: Run async external embedding methods.
    This function is deprecated as of v2.4.0 (September 2025).
    Returns failure result to indicate external embeddings are no longer supported.
    """
    logger.warning("External embedding functionality deprecated")
    return False
