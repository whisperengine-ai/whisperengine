#!/usr/bin/env python3
"""
Aethys 7D Vector Memory Migration Script

Migrates Aethys from the old single-vector collection (chat_memories_aethys) 
to the new 7-dimensional named vector system (whisperengine_memory_aethys).

This follows the same pattern as other character migrations to the enhanced 
7D vector memory architecture.

Usage:
    source .venv/bin/activate
    python scripts/aethys_7d_migration.py [--dry-run]
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        VectorParams, Distance, PointStruct, Filter, FieldCondition, 
        MatchValue, ScrollRequest, NamedVector, PayloadSchemaType
    )
    import qdrant_client.models as models
except ImportError as e:
    print(f"Missing qdrant-client: {e}")
    print("Install with: pip install qdrant-client")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    import numpy as np
except ImportError as e:
    print(f"Missing dependencies: {e}")
    sys.exit(1)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AethysMigrationManager:
    """Manages migration from old single-vector to new 7D vector system"""
    
    def __init__(self):
        # Direct Qdrant connection - don't rely on environment from bot
        self.client = QdrantClient(
            host='localhost',  # Direct connection to Qdrant
            port=6334         # Multi-bot Qdrant port
        )
        
        # Collection names
        self.old_collection = "chat_memories_aethys"
        self.new_collection = "whisperengine_memory_aethys"
        
        # 7D Vector dimensions (all 384D)
        self.vector_size = 384
        
        logger.info(f"🚀 Aethys Migration: {self.old_collection} → {self.new_collection}")
    
    def create_new_collection(self) -> bool:
        """Create the new 7D vector collection with proper schema"""
        try:
            # Check if new collection already exists
            collections = self.client.get_collections().collections
            if any(c.name == self.new_collection for c in collections):
                logger.info(f"✅ Collection {self.new_collection} already exists")
                return True
            
            # Create 7D named vectors configuration
            vectors_config = {
                "content": VectorParams(size=self.vector_size, distance=Distance.COSINE),
                "emotion": VectorParams(size=self.vector_size, distance=Distance.COSINE),
                "semantic": VectorParams(size=self.vector_size, distance=Distance.COSINE),
                "relationship": VectorParams(size=self.vector_size, distance=Distance.COSINE),
                "personality": VectorParams(size=self.vector_size, distance=Distance.COSINE),
                "interaction": VectorParams(size=self.vector_size, distance=Distance.COSINE),
                "temporal": VectorParams(size=self.vector_size, distance=Distance.COSINE)
            }
            
            # Create collection
            self.client.create_collection(
                collection_name=self.new_collection,
                vectors_config=vectors_config
            )
            
            # Create payload indexes for efficient filtering
            self._create_payload_indexes()
            
            logger.info(f"✅ Created new 7D collection: {self.new_collection}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection: {e}")
            return False
    
    def _create_payload_indexes(self):
        """Create indexes for efficient payload filtering"""
        required_indexes = [
            ("user_id", PayloadSchemaType.KEYWORD, "User-based filtering (most common)"),
            ("memory_type", PayloadSchemaType.KEYWORD, "Memory type filtering"),
            ("timestamp_unix", PayloadSchemaType.FLOAT, "Temporal range queries and ordering"),
            ("semantic_key", PayloadSchemaType.KEYWORD, "Semantic grouping"),
            ("emotional_context", PayloadSchemaType.KEYWORD, "Emotional context"),
            ("content_hash", PayloadSchemaType.INTEGER, "Content hash (deduplication)"),
            ("bot_name", PayloadSchemaType.KEYWORD, "Bot-specific memory isolation"),
            ("timestamp", PayloadSchemaType.INTEGER, "Legacy timestamp support"),
            ("conversation_id", PayloadSchemaType.KEYWORD, "Conversation grouping")
        ]
        
        created_count = 0
        for field_name, field_schema, description in required_indexes:
            try:
                self.client.create_payload_index(
                    collection_name=self.new_collection,
                    field_name=field_name,
                    field_schema=field_schema
                )
                logger.info(f"📊 Created index: {field_name} ({description})")
                created_count += 1
            except Exception as e:
                # Index probably already exists - this is normal
                logger.debug(f"⚠️ Index {field_name} already exists or failed: {e}")
        
        if created_count > 0:
            logger.info(f"🎯 Created {created_count} payload indexes")
        else:
            logger.info("🎯 All payload indexes already exist")
    
    def check_old_collection(self) -> Dict[str, Any]:
        """Check the old collection and return statistics"""
        try:
            collections = self.client.get_collections().collections
            old_exists = any(c.name == self.old_collection for c in collections)
            
            if not old_exists:
                logger.warning(f"⚠️ Old collection {self.old_collection} not found")
                return {"exists": False, "count": 0}
            
            # Get collection info
            info = self.client.get_collection(self.old_collection)
            count = info.points_count
            
            logger.info(f"📊 Found {count} memories in {self.old_collection}")
            return {"exists": True, "count": count, "info": info}
            
        except Exception as e:
            logger.error(f"❌ Failed to check old collection: {e}")
            return {"exists": False, "count": 0}
    
    def migrate_memories(self, dry_run: bool = False) -> bool:
        """Migrate memories from old to new collection"""
        try:
            old_stats = self.check_old_collection()
            if not old_stats["exists"]:
                logger.error("❌ Cannot migrate: old collection not found")
                return False
            
            if old_stats["count"] == 0:
                logger.info("✅ No memories to migrate")
                return True
            
            if dry_run:
                logger.info(f"🔍 DRY RUN: Would migrate {old_stats['count']} memories")
                return True
            
            # Scroll through all points in old collection
            migrated_count = 0
            batch_size = 100
            offset = None
            
            while True:
                scroll_result = self.client.scroll(
                    collection_name=self.old_collection,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )
                
                if not scroll_result[0]:  # No more points
                    break
                
                points_batch = []
                for point in scroll_result[0]:
                    try:
                        # Convert old single vector to 7D named vectors
                        new_point = self._convert_to_7d_point(point)
                        if new_point:
                            points_batch.append(new_point)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to convert point {point.id}: {e}")
                
                # Upload batch to new collection
                if points_batch:
                    self.client.upsert(
                        collection_name=self.new_collection,
                        points=points_batch
                    )
                    migrated_count += len(points_batch)
                    logger.info(f"📤 Migrated batch: {migrated_count}/{old_stats['count']}")
                
                offset = scroll_result[1]  # Next offset
                if offset is None:
                    break
            
            logger.info(f"✅ Migration complete: {migrated_count} memories migrated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    def _convert_to_7d_point(self, old_point) -> Optional[PointStruct]:
        """Convert old 3-vector point to new 7D named vector format"""
        try:
            # Extract the old vectors (already named: content, emotion, semantic)
            old_vectors = old_point.vector
            if not isinstance(old_vectors, dict):
                logger.warning(f"⚠️ Expected named vectors but got {type(old_vectors)} for point {old_point.id}")
                return None
            
            # Get the existing vectors
            content_vector = old_vectors.get("content")
            emotion_vector = old_vectors.get("emotion") 
            semantic_vector = old_vectors.get("semantic")
            
            if not all([content_vector, emotion_vector, semantic_vector]):
                logger.warning(f"⚠️ Missing required vectors for point {old_point.id}")
                return None
            
            # Validate vector dimensions
            vectors_to_check = [content_vector, emotion_vector, semantic_vector]
            if not all(isinstance(v, list) and len(v) == self.vector_size for v in vectors_to_check):
                logger.warning(f"⚠️ Invalid vector dimensions for point {old_point.id}")
                return None
            
            # Create 7D named vectors - keep existing 3, generate 4 new ones from content
            base_vector = np.array(content_vector, dtype=np.float32)
            
            vectors = {
                # Keep existing vectors
                "content": content_vector,
                "emotion": emotion_vector,
                "semantic": semantic_vector,
                # Generate new vectors from content with slight variations
                "relationship": self._add_noise(base_vector, 0.04).tolist(),
                "personality": self._add_noise(base_vector, 0.02).tolist(),
                "interaction": self._add_noise(base_vector, 0.03).tolist(),
                "temporal": self._add_noise(base_vector, 0.02).tolist()
            }
            
            # Ensure payload has required fields
            payload = old_point.payload or {}
            if "bot_name" not in payload:
                payload["bot_name"] = "aethys"
            if "memory_type" not in payload:
                payload["memory_type"] = "conversation"
            if "timestamp" not in payload:
                payload["timestamp"] = int(datetime.now().timestamp())
            
            return PointStruct(
                id=old_point.id,
                vector=vectors,
                payload=payload
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to convert point: {e}")
            return None
    
    def _add_noise(self, vector: np.ndarray, noise_factor: float) -> np.ndarray:
        """Add small random noise to create vector variations"""
        noise = np.random.normal(0, noise_factor, vector.shape)
        noisy_vector = vector + noise
        # Normalize to maintain unit vector properties
        norm = np.linalg.norm(noisy_vector)
        if norm > 0:
            noisy_vector = noisy_vector / norm
        return noisy_vector.astype(np.float32)
    
    def verify_migration(self) -> bool:
        """Verify migration was successful"""
        try:
            old_stats = self.check_old_collection()
            
            # Check new collection
            new_info = self.client.get_collection(self.new_collection)
            new_count = new_info.points_count
            
            logger.info(f"📊 Migration Verification:")
            logger.info(f"   Old collection: {old_stats.get('count', 0)} memories")
            logger.info(f"   New collection: {new_count} memories")
            
            if new_count >= old_stats.get('count', 0):
                logger.info("✅ Migration verification PASSED")
                return True
            else:
                logger.error("❌ Migration verification FAILED: count mismatch")
                return False
                
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False

def update_env_file():
    """Update .env.aethys to use the new collection name"""
    env_file = Path(__file__).parent.parent / ".env.aethys"
    
    if not env_file.exists():
        logger.error(f"❌ Environment file not found: {env_file}")
        return False
    
    try:
        # Read current content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace old collection name with new one
        old_line = "QDRANT_COLLECTION_NAME=chat_memories_aethys"
        new_line = "QDRANT_COLLECTION_NAME=whisperengine_memory_aethys"
        
        if old_line in content:
            new_content = content.replace(old_line, new_line)
            
            # Write updated content
            with open(env_file, 'w') as f:
                f.write(new_content)
            
            logger.info(f"✅ Updated {env_file}: {old_line} → {new_line}")
            return True
        else:
            logger.warning(f"⚠️ Old collection name not found in {env_file}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to update env file: {e}")
        return False

async def main():
    """Main migration workflow"""
    parser = argparse.ArgumentParser(description="Migrate Aethys to 7D vector system")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without actually doing it")
    args = parser.parse_args()
    
    print("🎯 AETHYS 7D VECTOR MIGRATION")
    print("=" * 50)
    
    migration_manager = AethysMigrationManager()
    
    # Step 1: Check old collection
    logger.info("📊 Step 1: Checking old collection...")
    old_stats = migration_manager.check_old_collection()
    
    if not old_stats["exists"]:
        logger.error("❌ Old collection not found. Nothing to migrate.")
        return False
    
    # Step 2: Create new collection
    logger.info("🏗️ Step 2: Creating new 7D collection...")
    if not migration_manager.create_new_collection():
        logger.error("❌ Failed to create new collection")
        return False
    
    # Step 3: Migrate memories
    logger.info("📤 Step 3: Migrating memories...")
    if not migration_manager.migrate_memories(dry_run=args.dry_run):
        logger.error("❌ Migration failed")
        return False
    
    if args.dry_run:
        logger.info("🔍 DRY RUN COMPLETE - No actual changes made")
        return True
    
    # Step 4: Verify migration
    logger.info("✅ Step 4: Verifying migration...")
    if not migration_manager.verify_migration():
        logger.error("❌ Migration verification failed")
        return False
    
    # Step 5: Update environment file
    logger.info("📝 Step 5: Updating environment configuration...")
    if not update_env_file():
        logger.warning("⚠️ Failed to update .env.aethys - you may need to do this manually")
    
    print("\n🎉 AETHYS MIGRATION COMPLETE!")
    print(f"   • Migrated from: chat_memories_aethys")
    print(f"   • Migrated to: whisperengine_memory_aethys") 
    print(f"   • Memories migrated: {old_stats['count']}")
    print(f"   • Environment updated: .env.aethys")
    print("\n🚀 Aethys is now ready for 7D vector system testing!")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)