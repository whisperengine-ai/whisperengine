#!/usr/bin/env python3
"""
🗑️ Vector Data Cleanup Script

Since WhisperEngine is in ALPHA/DEV phase with no production users,
we can safely delete all vector data and start fresh with proper
named vector format.

This script:
1. Connects to Qdrant
2. Deletes the whisperengine_memories collection  
3. Recreates it with proper named vector configuration
4. Confirms the cleanup was successful

Usage:
    python cleanup_vector_data.py
    
⚠️ WARNING: This will delete ALL vector memories for ALL bots!
Only safe because we're in development phase.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qdrant_client import QdrantClient
from qdrant_client import models
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_vector_data():
    """Delete all vector data and recreate collection with proper format"""
    
    print("🗑️  VECTOR DATA CLEANUP - ALPHA/DEV PHASE")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    # Connect to Qdrant
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port = int(os.getenv('QDRANT_PORT', 6334))
    collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'whisperengine_memories')
    
    client = QdrantClient(host=qdrant_host, port=qdrant_port)
    
    print(f"📡 Connected to Qdrant: {qdrant_host}:{qdrant_port}")
    print(f"🎯 Target collection: {collection_name}")
    
    try:
        # Check if collection exists
        try:
            collection_info = client.get_collection(collection_name)
            points_count = collection_info.points_count or 0
            print(f"📊 Found existing collection with {points_count} points")
            collection_exists = True
        except Exception:
            print("📊 Collection doesn't exist yet")
            points_count = 0
            collection_exists = False
        
        # Delete collection if it exists
        if collection_exists:
            print(f"🗑️  Deleting collection with {points_count} points...")
            client.delete_collection(collection_name)
            print("✅ Collection deleted successfully")
        
        # Recreate collection with proper named vector configuration
        print("🔨 Recreating collection with named vector format...")
        
        vector_config = models.VectorParams(
            size=384,  # BAAI/bge-small-en-v1.5 dimension
            distance=models.Distance.COSINE
        )
        
        # Create named vectors configuration
        vectors_config = {
            "content": vector_config,    # Main semantic content
            "emotion": vector_config,    # Emotional context  
            "semantic": vector_config    # Additional semantic context
        }
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config
        )
        
        # Verify collection was created properly
        new_collection = client.get_collection(collection_name)
        print(f"✅ Collection recreated successfully")
        print(f"📊 Points count: {new_collection.points_count}")
        
        print("\n🎉 CLEANUP COMPLETE!")
        print("=" * 60)
        print("✅ All old vector data deleted")
        print("✅ Collection recreated with proper named vector format")
        print("✅ Ready for fresh data with correct architecture")
        print("\n💡 Next steps:")
        print("   1. Start your bots: ./multi-bot.sh start all")
        print("   2. Have conversations to generate new properly-formatted memories")
        print("   3. All new data will use correct named vector format")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False
        
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        # Skip confirmation if --confirm flag is provided
        success = cleanup_vector_data()
        sys.exit(0 if success else 1)
    else:
        print("⚠️  WARNING: This will delete ALL vector memories!")
        print("Only safe because WhisperEngine is in ALPHA/DEV phase.")
        print("\nTo run: python cleanup_vector_data.py --confirm")
        sys.exit(1)