"""
ChromaDB External Embedding Extension
Extends ChromaDB functionality to support external embedding APIs.
"""

import asyncio
import logging
import os
from typing import Any

from src.utils.embedding_manager import embedding_manager

logger = logging.getLogger(__name__)


async def add_documents_with_embeddings(
    collection, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]
) -> bool:
    """
    Add documents using external or local embeddings based on configuration

    Args:
        collection: ChromaDB collection
        documents: List of document texts
        metadatas: List of metadata dictionaries
        ids: List of document IDs

    Returns:
        True if successful, False otherwise
    """
    if not collection:
        logger.error("No collection provided for adding documents")
        return False

    try:
        from src.utils.embedding_manager import is_external_embedding_configured

        use_external = is_external_embedding_configured()

        if use_external:
            # Use external embeddings
            embeddings = await embedding_manager.get_embeddings(documents)

            collection.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)
            logger.debug(f"Added {len(documents)} documents with external embeddings")
        else:
            # Use ChromaDB's built-in embeddings (current behavior)
            collection.add(documents=documents, metadatas=metadatas, ids=ids)
            logger.debug(f"Added {len(documents)} documents with local embeddings")

        return True

    except Exception as e:
        logger.error(f"Failed to add documents: {e}")
        return False


async def query_with_embeddings(
    collection, query_texts: list[str], n_results: int = 10, where: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Query collection using external or local embeddings based on configuration

    Args:
        collection: ChromaDB collection
        query_texts: List of query texts
        n_results: Number of results to return
        where: Optional metadata filter

    Returns:
        Query results
    """
    if not collection:
        logger.error("No collection provided for querying")
        return {"documents": None, "metadatas": None, "distances": None, "ids": None}

    try:
        from src.utils.embedding_manager import is_external_embedding_configured

        use_external = is_external_embedding_configured()

        if use_external:
            # Use external embeddings for query
            query_embeddings = await embedding_manager.get_embeddings(query_texts)

            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            logger.debug(
                f"Queried with external embeddings, got {len(results.get('documents', []))} results"
            )
        else:
            # Use ChromaDB's built-in embeddings
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            logger.debug(
                f"Queried with local embeddings, got {len(results.get('documents', []))} results"
            )

        return results

    except Exception as e:
        logger.error(f"Failed to query collection: {e}")
        return {"documents": None, "metadatas": None, "distances": None, "ids": None}


async def upsert_documents_with_embeddings(
    collection, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]
) -> bool:
    """
    Upsert documents using external or local embeddings based on configuration

    Args:
        collection: ChromaDB collection
        documents: List of document texts
        metadatas: List of metadata dictionaries
        ids: List of document IDs

    Returns:
        True if successful, False otherwise
    """
    if not collection:
        logger.error("No collection provided for upserting documents")
        return False

    try:
        from src.utils.embedding_manager import is_external_embedding_configured

        use_external = is_external_embedding_configured()

        if use_external:
            # Use external embeddings
            embeddings = await embedding_manager.get_embeddings(documents)

            collection.upsert(
                documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids
            )
            logger.debug(f"Upserted {len(documents)} documents with external embeddings")
        else:
            # Use ChromaDB's built-in embeddings
            collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
            logger.debug(f"Upserted {len(documents)} documents with local embeddings")

        return True

    except Exception as e:
        logger.error(f"Failed to upsert documents: {e}")
        return False


async def test_embedding_setup() -> dict[str, Any]:
    """
    Test the current embedding setup (external or local)

    Returns:
        Test results
    """
    try:
        from src.utils.embedding_manager import is_external_embedding_configured

        use_external = is_external_embedding_configured()

        if use_external:
            # Test external embeddings
            test_result = await embedding_manager.test_connection()
            return {
                "embedding_type": "external",
                "success": test_result["success"],
                "details": test_result,
            }
        else:
            # Test local embeddings
            from chromadb.utils import embedding_functions

            try:
                local_model = os.getenv("LLM_LOCAL_EMBEDDING_MODEL", "all-Mpnet-BASE-v2")
                embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=local_model
                )

                test_texts = ["Hello world", "This is a test"]
                embeddings = embedding_function(test_texts)

                return {
                    "embedding_type": "local",
                    "success": True,
                    "dimension": len(embeddings[0]) if embeddings else 0,
                    "details": {"model": local_model, "test_embedding_count": len(embeddings)},
                }
            except Exception as e:
                return {"embedding_type": "local", "success": False, "error": str(e)}

    except Exception as e:
        return {"embedding_type": "unknown", "success": False, "error": str(e)}


# Sync wrappers for use in existing sync code
def run_async_method(async_method, *args, **kwargs):
    """
    Helper function to run async methods in sync context

    Args:
        async_method: Async method to run
        *args: Method arguments
        **kwargs: Method keyword arguments

    Returns:
        Method result
    """
    try:
        # Try to get existing event loop
        asyncio.get_running_loop()
        # If we're already in an async context, we can't run another event loop
        # Create a task instead
        import concurrent.futures

        # Run in a separate thread to avoid blocking the current event loop
        def run_in_thread():
            return asyncio.run(async_method(*args, **kwargs))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()

    except RuntimeError:
        # No event loop running, create and run one
        return asyncio.run(async_method(*args, **kwargs))


def add_documents_sync(
    collection, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]
) -> bool:
    """
    Sync wrapper for adding documents with embeddings
    """
    return run_async_method(add_documents_with_embeddings, collection, documents, metadatas, ids)


def query_documents_sync(
    collection, query_texts: list[str], n_results: int = 10, where: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Sync wrapper for querying with embeddings
    """
    return run_async_method(query_with_embeddings, collection, query_texts, n_results, where)


def upsert_documents_sync(
    collection, documents: list[str], metadatas: list[dict[str, Any]], ids: list[str]
) -> bool:
    """
    Sync wrapper for upserting documents with embeddings
    """
    return run_async_method(upsert_documents_with_embeddings, collection, documents, metadatas, ids)


def test_embeddings_sync() -> dict[str, Any]:
    """
    Sync wrapper for testing embedding setup
    """
    return run_async_method(test_embedding_setup)
