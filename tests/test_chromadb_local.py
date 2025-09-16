#!/usr/bin/env python3
"""
Quick test to verify ChromaDB local storage is working
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment mode
os.environ['ENV_MODE'] = 'desktop'

from env_manager import load_environment
load_environment('desktop')

# Test ChromaDB directly
import chromadb
from pathlib import Path

def test_chromadb_local():
    """Test ChromaDB local file persistence"""
    print("🔍 Testing ChromaDB Local File Persistence...")
    
    try:
        # Create ChromaDB client using the same settings as the app
        chromadb_path = os.path.expanduser("~/.whisperengine/chromadb_data")
        Path(chromadb_path).mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(path=chromadb_path)
        print(f"✅ ChromaDB client created: {chromadb_path}")
        
        # Get or create a collection
        collection = client.get_or_create_collection("test_collection")
        print(f"✅ Collection created/retrieved: {collection.name}")
        
        # Add a test document
        collection.add(
            documents=["I like cats and their behavior"],
            metadatas=[{"user_id": "123456789012345678", "timestamp": "2025-09-14"}],
            ids=["test_doc_1"]
        )
        print("✅ Test document added")
        
        # Query the document
        results = collection.query(
            query_texts=["tell me about cats"],
            n_results=1
        )
        print(f"✅ Query results: {results}")
        
        if results['documents'][0]:
            print("🎉 ChromaDB local storage is working correctly!")
            return True
        else:
            print("❌ No results found")
            return False
            
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_chromadb_local()