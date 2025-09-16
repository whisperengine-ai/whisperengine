#!/usr/bin/env python3
"""
ChromaDB Initialization Script
Pre-creates collections with proper metadata validation and schema setup
"""

import asyncio
import logging
import os
import sys
from datetime import UTC
from typing import Any

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaDBInitializer:
    """Initialize ChromaDB collections with proper schema and validation"""

    def __init__(self, host: str = "localhost", port: int = 8000, enable_auth: bool = False):
        """
        Initialize ChromaDB initializer

        Args:
            host: ChromaDB server host
            port: ChromaDB server port
            enable_auth: Enable authentication (for production)
        """
        self.host = host
        self.port = port
        self.enable_auth = enable_auth
        self.client = None

        # Collection configurations
        self.collection_configs = {
            "user_memories": {
                "description": "User-specific conversation memories and experiences",
                "metadata_schema": {
                    "user_id": "string",  # Required: Discord user ID
                    "timestamp": "string",  # Required: ISO timestamp
                    "doc_type": "string",  # conversation, fact, summary
                    "channel_id": "string",  # Optional: Discord channel ID
                    "confidence": "float",  # Optional: 0.0-1.0 confidence score
                    "emotional_context": "object",  # Optional: emotion data
                    "importance_score": "float",  # Optional: 0.0-1.0 importance
                    "topic": "string",  # Optional: conversation topic
                },
                "required_fields": ["user_id", "timestamp", "doc_type"],
                "max_documents": 10000,  # Per user limit
            },
            "global_facts": {
                "description": "Shared knowledge and global facts across users",
                "metadata_schema": {
                    "doc_type": "string",  # Required: global_fact, knowledge
                    "category": "string",  # Required: general, technical, etc.
                    "timestamp": "string",  # Required: ISO timestamp
                    "confidence": "float",  # Required: 0.0-1.0 confidence
                    "source": "string",  # Optional: where fact came from
                    "last_verified": "string",  # Optional: last verification time
                    "tags": "array",  # Optional: searchable tags
                },
                "required_fields": ["doc_type", "category", "timestamp", "confidence"],
                "max_documents": 5000,  # Global limit
            },
        }

    async def initialize(self) -> bool:
        """Initialize ChromaDB collections and schema"""
        try:
            logger.info("🗃️ Initializing ChromaDB collections...")

            # Connect to ChromaDB
            if not await self._connect():
                return False

            # Create collections with schema validation
            for collection_name, config in self.collection_configs.items():
                if not await self._create_collection(collection_name, config):
                    return False

            # Verify collections
            if not await self._verify_collections():
                return False

            logger.info("✅ ChromaDB initialization completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            return False

    async def _connect(self) -> bool:
        """Connect to ChromaDB server"""
        try:
            # Configure ChromaDB client for HTTP connection
            settings = Settings(
                chroma_server_host=self.host,
                chroma_server_http_port=self.port,
                chroma_client_auth_provider=(
                    "chromadb.auth.basic.BasicAuthClientProvider" if self.enable_auth else None
                ),
            )

            self.client = chromadb.HttpClient(host=self.host, port=self.port, settings=settings)

            # Test connection
            version = self.client.get_version()
            logger.info(f"Connected to ChromaDB {version} at {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            return False

    async def _create_collection(self, name: str, config: dict) -> bool:
        """Create a collection with proper configuration"""
        try:
            if not self.client:
                logger.error("ChromaDB client not initialized")
                return False

            logger.info(f"Creating collection: {name}")

            # Check if collection already exists
            try:
                self.client.get_collection(name)
                logger.info(f"Collection '{name}' already exists, verifying schema...")
                return await self._verify_collection_schema(name, config)
            except Exception:
                # Collection doesn't exist, create it
                pass

            # Create collection with metadata
            self.client.create_collection(
                name=name,
                metadata={
                    "description": config["description"],
                    "schema_version": "1.0",
                    "created_at": self._get_timestamp(),
                    "required_fields": config["required_fields"],
                    "max_documents": config["max_documents"],
                },
            )

            logger.info(f"✅ Created collection '{name}' with schema validation")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection '{name}': {e}")
            return False

    async def _verify_collection_schema(self, name: str, config: dict) -> bool:
        """Verify existing collection has correct schema"""
        try:
            if not self.client:
                logger.error("ChromaDB client not initialized")
                return False

            collection = self.client.get_collection(name)
            metadata = collection.metadata

            # Check required fields
            if "required_fields" not in metadata:
                logger.warning(f"Collection '{name}' missing required_fields metadata")
                return False

            # Verify required fields match
            expected_fields = set(config["required_fields"])
            actual_fields = set(metadata["required_fields"])

            if expected_fields != actual_fields:
                logger.warning(
                    f"Collection '{name}' schema mismatch: expected {expected_fields}, got {actual_fields}"
                )
                return False

            logger.info(f"✅ Collection '{name}' schema verified")
            return True

        except Exception as e:
            logger.error(f"Failed to verify collection '{name}': {e}")
            return False

    async def _verify_collections(self) -> bool:
        """Verify all collections were created successfully"""
        try:
            if not self.client:
                logger.error("ChromaDB client not initialized")
                return False

            collections = self.client.list_collections()
            collection_names = [c.name for c in collections]

            for expected_name in self.collection_configs.keys():
                if expected_name not in collection_names:
                    logger.error(f"Collection '{expected_name}' not found after creation")
                    return False

            logger.info(f"✅ Verified {len(self.collection_configs)} collections")
            return True

        except Exception as e:
            logger.error(f"Failed to verify collections: {e}")
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime

        return datetime.now(UTC).isoformat()

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on ChromaDB setup"""
        health_status = {
            "chromadb_accessible": False,
            "collections_exist": False,
            "total_collections": 0,
            "collection_details": {},
            "errors": [],
        }

        try:
            # Test connection
            if not self.client:
                await self._connect()

            if not self.client:
                health_status["errors"].append("Failed to connect to ChromaDB")
                return health_status

            version = self.client.get_version()
            health_status["chromadb_accessible"] = True
            health_status["version"] = version

            # Check collections
            collections = self.client.list_collections()
            health_status["total_collections"] = len(collections)

            # Check each expected collection
            all_exist = True
            for name, config in self.collection_configs.items():
                try:
                    collection = self.client.get_collection(name)
                    count = collection.count()
                    health_status["collection_details"][name] = {
                        "exists": True,
                        "document_count": count,
                        "max_documents": config["max_documents"],
                        "usage_percent": (count / config["max_documents"]) * 100,
                    }
                except Exception as e:
                    all_exist = False
                    health_status["collection_details"][name] = {"exists": False, "error": str(e)}
                    health_status["errors"].append(f"Collection '{name}': {e}")

            health_status["collections_exist"] = all_exist

        except Exception as e:
            health_status["errors"].append(f"Health check failed: {e}")

        return health_status


def get_chromadb_config() -> dict[str, Any]:
    """Get ChromaDB configuration from environment"""
    return {
        "host": os.getenv("CHROMADB_HOST", "localhost"),
        "port": int(os.getenv("CHROMADB_PORT", "8000")),
        "enable_auth": os.getenv("CHROMADB_AUTH_ENABLED", "false").lower() == "true",
    }


async def main():
    """Main initialization function"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Get configuration
    config = get_chromadb_config()

    # Initialize ChromaDB
    initializer = ChromaDBInitializer(**config)

    # Perform initialization
    success = await initializer.initialize()

    if success:

        # Perform health check
        health = await initializer.health_check()

        if health["chromadb_accessible"]:

            for _name, details in health["collection_details"].items():
                if details["exists"]:
                    details["usage_percent"]
                else:
                    pass

        if health["errors"]:
            for _error in health["errors"]:
                pass

        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
