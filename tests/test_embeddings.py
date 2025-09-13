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

import os
import sys
import asyncio
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.embedding_manager import embedding_manager, test_embedding_connection, get_embedding_config
from src.memory.chromadb_external_embeddings import (
    add_documents_with_embeddings, 
    query_with_embeddings, 
    test_embedding_setup,
    test_embeddings_sync
)

async def test_embedding_manager():
    """Test the embedding manager directly"""
    print("=" * 60)
    print("TESTING EMBEDDING MANAGER")
    print("=" * 60)
    
    # Test configuration
    config = get_embedding_config()
    print(f"📋 Configuration:")
    for key, value in config.items():
        if key == "has_api_key":
            print(f"  {key}: {'Yes' if value else 'No'}")
        else:
            print(f"  {key}: {value}")
    print()
    
    # Test connection
    print("🔌 Testing connection...")
    connection_test = await test_embedding_connection()
    if connection_test["success"]:
        print(f"✅ Connection successful!")
        print(f"   Service: {connection_test.get('service', 'unknown')}")
        print(f"   Model: {connection_test.get('model', 'unknown')}")
        print(f"   Dimension: {connection_test.get('dimension', 'unknown')}")
        print(f"   Response time: {connection_test.get('response_time', 0):.3f}s")
    else:
        print(f"❌ Connection failed: {connection_test.get('error', 'Unknown error')}")
    print()
    
    # Test embedding generation
    print("🧮 Testing embedding generation...")
    test_texts = [
        "Hello, this is a test.",
        "The weather is nice today.",
        "I love programming with Python.",
        "Discord bots are really useful."
    ]
    
    start_time = time.time()
    try:
        embeddings = await embedding_manager.get_embeddings(test_texts)
        end_time = time.time()
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"   Dimension: {len(embeddings[0]) if embeddings else 0}")
        print(f"   Processing time: {end_time - start_time:.3f}s")
        print(f"   Average time per embedding: {(end_time - start_time) / len(embeddings):.3f}s")
        
        # Show first few values of first embedding
        if embeddings and embeddings[0]:
            first_embedding = embeddings[0][:5]  # First 5 values
            print(f"   Sample values: {[f'{x:.4f}' for x in first_embedding]}")
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
    
    print()


async def test_chromadb_integration():
    """Test ChromaDB integration with external embeddings"""
    print("=" * 60)
    print("TESTING CHROMADB INTEGRATION")
    print("=" * 60)
    
    # Test the embedding setup function
    print("🔧 Testing embedding setup...")
    setup_test = await test_embedding_setup()
    
    if setup_test["success"]:
        print(f"✅ Embedding setup working!")
        print(f"   Type: {setup_test['embedding_type']}")
        if "details" in setup_test:
            details = setup_test["details"]
            if isinstance(details, dict):
                for key, value in details.items():
                    print(f"   {key}: {value}")
    else:
        print(f"❌ Embedding setup failed: {setup_test.get('error', 'Unknown error')}")
    
    print()
    
    # Test with actual ChromaDB (if available)
    try:
        import chromadb
        from chromadb.config import Settings
        from chromadb.utils import embedding_functions
        
        print("🗄️  Testing with temporary ChromaDB...")
        
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
            embedding_model = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model
            )
            # Type issue with ChromaDB - use get_or_create instead
            collection = client.get_or_create_collection(
                "test_collection", 
                embedding_function=embedding_function  # type: ignore
            )
        
        # Test data
        test_documents = [
            "The Discord bot can remember user preferences.",
            "External embeddings provide better semantic understanding.",
            "ChromaDB is a great vector database for AI applications.",
            "Python makes it easy to build complex systems."
        ]
        
        test_metadatas = [
            {"type": "test", "category": "bot"},
            {"type": "test", "category": "embedding"},
            {"type": "test", "category": "database"},
            {"type": "test", "category": "programming"}
        ]
        
        test_ids = ["test_1", "test_2", "test_3", "test_4"]
        
        # Test adding documents
        print("📝 Adding test documents...")
        add_success = await add_documents_with_embeddings(
            collection, test_documents, test_metadatas, test_ids
        )
        
        if add_success:
            print("✅ Documents added successfully")
        else:
            print("❌ Failed to add documents")
            return
        
        # Test querying
        print("🔍 Testing queries...")
        query_texts = ["How does the bot remember things?", "What is a vector database?"]
        
        query_results = await query_with_embeddings(
            collection, query_texts, n_results=2
        )
        
        if query_results and query_results.get("documents"):
            print("✅ Query successful!")
            for i, docs in enumerate(query_results["documents"]):
                print(f"   Query {i+1}: '{query_texts[i]}'")
                for j, doc in enumerate(docs):
                    distance = query_results["distances"][i][j] if query_results.get("distances") else "unknown"
                    print(f"     Result {j+1}: {doc[:50]}... (distance: {distance})")
        else:
            print("❌ Query failed or returned no results")
        
        # Clean up
        client.delete_collection("test_collection")
        print("🧹 Cleaned up test collection")
        
    except ImportError as e:
        print(f"⚠️  ChromaDB not available for testing: {e}")
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
    
    print()


def test_sync_wrappers():
    """Test the sync wrapper functions"""
    print("=" * 60)
    print("TESTING SYNC WRAPPERS")
    print("=" * 60)
    
    try:
        print("🔄 Testing sync embedding test...")
        sync_test = test_embeddings_sync()
        
        if sync_test["success"]:
            print(f"✅ Sync test successful!")
            print(f"   Type: {sync_test['embedding_type']}")
        else:
            print(f"❌ Sync test failed: {sync_test.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Sync wrapper test failed: {e}")
    
    print()


async def main():
    """Run all tests"""
    print("🚀 EXTERNAL EMBEDDING SYSTEM TEST")
    print(f"🌍 Environment: USE_EXTERNAL_EMBEDDINGS={os.getenv('USE_EXTERNAL_EMBEDDINGS', 'false')}")
    print()
    
    # Test embedding manager
    await test_embedding_manager()
    
    # Test ChromaDB integration
    await test_chromadb_integration()
    
    # Test sync wrappers
    test_sync_wrappers()
    
    print("=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)
    
    # Provide usage recommendations
    print("\n📖 USAGE RECOMMENDATIONS:")
    use_external = os.getenv("USE_EXTERNAL_EMBEDDINGS", "false").lower() == "true"
    
    if use_external:
        print("🌐 You are using EXTERNAL embeddings.")
        print("   Make sure to set your API key and URL in the environment.")
        print("   Benefits: Higher quality embeddings, scalability")
        print("   Considerations: API costs, network dependency")
    else:
        print("🏠 You are using LOCAL embeddings.")
        print("   Using ChromaDB's built-in SentenceTransformer embeddings.")
        print("   Benefits: No API costs, works offline")
        print("   Considerations: Lower quality than commercial models")
    
    print("\n🔧 To switch embedding types:")
    print("   External: export USE_EXTERNAL_EMBEDDINGS=true")
    print("   Local:    export USE_EXTERNAL_EMBEDDINGS=false")


if __name__ == "__main__":
    asyncio.run(main())
