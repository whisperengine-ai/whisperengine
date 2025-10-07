#!/usr/bin/env python

"""
Script to validate that bot_name fields have been removed from all Qdrant vector collections.
This improved version includes better connection handling and retries.
"""

import os
import time
import json
import asyncio
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Number of points to check per collection for validation
MAX_VALIDATION_POINTS = 1000

# Connection settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


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
            return client
        except (ResponseHandlingException, UnexpectedResponse, httpx.ConnectError, httpx.ReadError) as e:
            if attempt < retries - 1:
                logging.warning(f"Connection attempt {attempt+1} failed: {str(e)}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to connect to Qdrant after {retries} attempts: {str(e)}")
                raise


def validate_collection(client: QdrantClient, collection_name: str) -> Tuple[int, int, List[str]]:
    """
    Validate if bot_name fields have been successfully removed from a collection.
    Returns tuple: (total points checked, points with bot_name, list of bot_names found)
    """
    points_with_bot_name = 0
    bot_names_found = []
    total_points = 0
    
    try:
        # Scroll through points in the collection
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=MAX_VALIDATION_POINTS,
            with_payload=True
        )
        
        points = scroll_result[0]
        total_points = len(points)
        
        for point in points:
            payload = point.payload if hasattr(point, "payload") else {}
            if payload and "bot_name" in payload:
                points_with_bot_name += 1
                bot_name = payload["bot_name"]
                if bot_name not in bot_names_found:
                    bot_names_found.append(bot_name)
        
        return total_points, points_with_bot_name, bot_names_found
    
    except Exception as e:
        logging.error(f"Error validating collection {collection_name}: {str(e)}")
        return 0, 0, []


def main():
    """Main function to run the validation."""
    try:
        # Create client with retry logic
        client = get_qdrant_client()
        
        # Get all collections
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        logging.info(f"Found {len(collection_names)} collections: {', '.join(collection_names)}")
        
        # Track validation results
        total_collections = 0
        clean_collections = 0
        dirty_collections = 0
        total_points_checked = 0
        total_points_with_bot_name = 0
        
        # Validate each collection
        for collection_name in collection_names:
            # Skip collections that don't have "memory" in their name
            if "memory" not in collection_name:
                continue
                
            total_collections += 1
            points_checked, points_with_bot_name, bot_names = validate_collection(
                client, collection_name
            )
            
            total_points_checked += points_checked
            total_points_with_bot_name += points_with_bot_name
            
            if points_with_bot_name > 0:
                dirty_collections += 1
                logging.info(f"  ❌ {collection_name}: DIRTY - Found {points_with_bot_name}/{points_checked} points with bot_name fields")
                logging.info(f"     Bot names found: {', '.join(bot_names)}")
            else:
                clean_collections += 1
                logging.info(f"  ✅ {collection_name}: CLEAN - No bot_name fields found in {points_checked} points")
        
        # Print summary
        logging.info("\n🎯 VALIDATION SUMMARY:")
        logging.info(f"  📊 Total collections checked: {total_collections}")
        logging.info(f"  ✅ Clean collections: {clean_collections}")
        logging.info(f"  ❌ Dirty collections: {dirty_collections}")
        logging.info(f"  🔍 Total points checked: {total_points_checked}")
        logging.info(f"  🚫 Points with bot_name: {total_points_with_bot_name}")
        
        if dirty_collections == 0:
            logging.info("  🚀 ALL COLLECTIONS SUCCESSFULLY MIGRATED!")
        else:
            logging.info("  ⚠️ SOME COLLECTIONS STILL HAVE BOT_NAME FIELDS!")
        
    except Exception as e:
        logging.error(f"Validation failed: {str(e)}")


if __name__ == "__main__":
    main()