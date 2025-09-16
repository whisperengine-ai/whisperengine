#!/usr/bin/env python3
"""
Test External Embedding Implementation

This script tests the external embedding functionality and provides
a way to verify that the implementation works correctly.

Usage:
    # Test with current environment settings
    python test_embeddings.py

    # Test external embeddings specifically
    USE_EXTERNAL_EMBEDDINGS=true python test_embeddings.py

    # Test local embeddings specifically
    USE_EXTERNAL_EMBEDDINGS=false python test_embeddings.py
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.memory.chromadb_external_embeddings import (
    add_documents_with_embeddings,
    query_with_embeddings,
    test_embedding_setup,
    test_embeddings_sync,
)
from src.utils.embedding_manager import (
    embedding_manager,
    get_embedding_config,
    test_embedding_connection,
)


async def test_embedding_manager():
    """Test the embedding manager directly"""

    # Test configuration
    config = get_embedding_config()
    for key, _value in config.items():
        if key == "has_api_key":
            pass
        else:
            pass

    # Test connection
    connection_test = await test_embedding_connection()
    if connection_test["success"]:
        pass
    else:
        pass

    # Test embedding generation
    test_texts = [
        "Hello, this is a test.",
        "The weather is nice today.",
        "I love programming with Python.",
        "Discord bots are really useful.",
    ]

    time.time()
    try:
        embeddings = await embedding_manager.get_embeddings(test_texts)
        time.time()


        # Show first few values of first embedding
        if embeddings and embeddings[0]:
            embeddings[0][:5]  # First 5 values

    except Exception:
        pass



async def test_chromadb_integration():
    """Test ChromaDB integration with external embeddings"""

    # Test the embedding setup function
    setup_test = await test_embedding_setup()

    if setup_test["success"]:
        if "details" in setup_test:
            details = setup_test["details"]
            if isinstance(details, dict):
                for _key, _value in details.items():
                    pass
    else:
        pass


    # Test with actual ChromaDB (if available)
    try:
        import chromadb
        from chromadb.config import Settings
        from chromadb.utils import embedding_functions


        # Create temporary ChromaDB instance
        settings = Settings(anonymized_telemetry=False)
        client = chromadb.Client(settings)

        # Configure collection based on external embedding setting
        use_external = os.getenv("USE_EXTERNAL_EMBEDDINGS", "false").lower() == "true"

        if use_external:
            # Create collection without embedding function (we'll provide embeddings manually)
            collection = client.create_collection("test_collection")
        else:
            # Create collection with local embedding function
            embedding_model = os.getenv("LOCAL_EMBEDDING_MODEL", "all-mpnet-base-v2")
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            )
            # Type issue with ChromaDB - use get_or_create instead
            collection = client.get_or_create_collection(
                "test_collection", embedding_function=embedding_function  # type: ignore
            )

        # Test data
        test_documents = [
            "The Discord bot can remember user preferences.",
            "External embeddings provide better semantic understanding.",
            "ChromaDB is a great vector database for AI applications.",
            "Python makes it easy to build complex systems.",
        ]

        test_metadatas = [
            {"type": "test", "category": "bot"},
            {"type": "test", "category": "embedding"},
            {"type": "test", "category": "database"},
            {"type": "test", "category": "programming"},
        ]

        test_ids = ["test_1", "test_2", "test_3", "test_4"]

        # Test adding documents
        add_success = await add_documents_with_embeddings(
            collection, test_documents, test_metadatas, test_ids
        )

        if add_success:
            pass
        else:
            return

        # Test querying
        query_texts = ["How does the bot remember things?", "What is a vector database?"]

        query_results = await query_with_embeddings(collection, query_texts, n_results=2)

        if query_results and query_results.get("documents"):
            for i, docs in enumerate(query_results["documents"]):
                for j, _doc in enumerate(docs):
                    (
                        query_results["distances"][i][j]
                        if query_results.get("distances")
                        else "unknown"
                    )
        else:
            pass

        # Clean up
        client.delete_collection("test_collection")

    except ImportError:
        pass
    except Exception:
        pass



def test_sync_wrappers():
    """Test the sync wrapper functions"""

    try:
        sync_test = test_embeddings_sync()

        if sync_test["success"]:
            pass
        else:
            pass

    except Exception:
        pass



async def main():
    """Run all tests"""

    # Test embedding manager
    await test_embedding_manager()

    # Test ChromaDB integration
    await test_chromadb_integration()

    # Test sync wrappers
    test_sync_wrappers()


    # Provide usage recommendations
    use_external = os.getenv("USE_EXTERNAL_EMBEDDINGS", "false").lower() == "true"

    if use_external:
        pass
    else:
        pass



if __name__ == "__main__":
    asyncio.run(main())
