#!/usr/bin/env python3
"""
WhisperEngine Vector Storage Cleanup Script

This script identifies and deletes Qdrant collections that are no longer in use.
It scans the .env.* files to determine which collections are actively configured,
then deletes any collections that aren't being used.

USAGE:
  python scripts/cleanup_unused_qdrant_collections.py [--dry-run] [--confirm]

OPTIONS:
  --dry-run    Don't actually delete collections, just show what would be deleted
  --confirm    Skip the confirmation prompt and proceed with deletion
"""

import os
import sys
import glob
import time
import argparse
import logging
from typing import List, Set, Dict, Any

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse, ResponseHandlingException
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Connection settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Skip certain collections
SYSTEM_COLLECTIONS = {
    "test_roberta_emotion", 
    "test_sprint2_roberta",
    "character_test_scenarios",
    "chat_memories",
    "dream_memories"
}


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean up unused Qdrant collections"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Don't actually delete collections, just show what would be deleted"
    )
    parser.add_argument(
        "--confirm", 
        action="store_true", 
        help="Skip the confirmation prompt and proceed with deletion"
    )
    return parser.parse_args()


def get_qdrant_client(retries: int = MAX_RETRIES) -> QdrantClient:
    """
    Create a Qdrant client with retry logic.
    """
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6334"))
    
    for attempt in range(retries):
        try:
            client = QdrantClient(host=host, port=port)
            # Test connection
            client.get_collections()
            logging.info(f"✅ Connected to Qdrant at {host}:{port}")
            return client
        except (ResponseHandlingException, UnexpectedResponse, httpx.ConnectError, httpx.ReadError) as e:
            if attempt < retries - 1:
                logging.warning(f"Connection attempt {attempt+1} failed: {str(e)}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to connect to Qdrant after {retries} attempts. Error: {str(e)}")
                raise
    
    # This should never happen because the final exception will raise
    raise ConnectionError("Failed to connect to Qdrant")


def get_active_collections() -> Set[str]:
    """
    Scan .env.* files to find active collection names.
    Simple rule: If a collection is in a .env.{bot_name} file, it's active.
    """
    active_collections = set()
    env_files = glob.glob('.env.*')
    
    if not env_files:
        logging.warning("No .env.* files found!")
        return active_collections
    
    logging.info(f"Found {len(env_files)} environment files to scan")
    
    # Check for collection names in .env.{bot_name} files
    for env_file in env_files:
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                for line in content.splitlines():
                    if 'QDRANT_COLLECTION_NAME=' in line:
                        collection = line.split('=')[1].strip().strip('"\'')
                        if collection:
                            active_collections.add(collection)
                            logging.info(f"Found active collection: {collection} in {env_file}")
        except Exception as e:
            logging.error(f"Error reading {env_file}: {str(e)}")
    
    return active_collections


def delete_collections(client: QdrantClient, collections_to_delete: List[str], dry_run: bool) -> None:
    """
    Delete the specified collections.
    """
    for collection in collections_to_delete:
        try:
            if dry_run:
                logging.info(f"🔍 [DRY RUN] Would delete collection: {collection}")
            else:
                client.delete_collection(collection_name=collection)
                logging.info(f"🗑️ Deleted collection: {collection}")
        except Exception as e:
            logging.error(f"⚠️ Failed to delete collection {collection}: {str(e)}")


def main() -> None:
    """Main function."""
    args = parse_args()
    
    try:
        client = get_qdrant_client()
        existing_collections = [col.name for col in client.get_collections().collections]
        logging.info(f"Found {len(existing_collections)} existing collections in Qdrant")
        
        active_collections = get_active_collections()
        logging.info(f"Identified {len(active_collections)} active collections from environment files")
        
        # Simple rule: If a collection is not in active_collections and not in SYSTEM_COLLECTIONS, delete it
        collections_to_delete = [
            col for col in existing_collections 
            if col not in active_collections and col not in SYSTEM_COLLECTIONS
        ]
        
        # Log collections to be deleted with reasons
        for col in collections_to_delete:
            if col == 'whisperengine_memory':
                logging.info(f"Will delete: {col} (old shared collection)")
            elif col.endswith('_7d'):
                logging.info(f"Will delete: {col} (deprecated 7D collection)")
            else:
                logging.info(f"Will delete: {col} (not in any .env file)")
        
        if not collections_to_delete:
            logging.info("✅ No unused collections found. Nothing to delete.")
            return
        
        logging.info(f"Found {len(collections_to_delete)} collections to delete:")
        for col in collections_to_delete:
            logging.info(f"  - {col}")
        
        if args.dry_run:
            logging.info("🔍 DRY RUN: No collections will be deleted.")
            return
        
        if not args.confirm:
            confirm = input(f"Are you sure you want to delete {len(collections_to_delete)} collections? (y/N): ")
            if confirm.lower() not in ("y", "yes"):
                logging.info("❌ Deletion cancelled.")
                return
        
        delete_collections(client, collections_to_delete, dry_run=args.dry_run)
        logging.info(f"✅ Successfully cleaned up {len(collections_to_delete)} unused collections")
        
    except Exception as e:
        logging.error(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()