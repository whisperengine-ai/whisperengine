#!/usr/bin/env python3
"""
Qdrant Collection Migration Script

Safely migrates a Qdrant collection to a new name by:
1. Validating source collection exists
2. Creating new collection with same schema
3. Copying all vectors and metadata
4. Verifying data integrity

Usage:
    # Dry run (see what would happen)
    python scripts/migrate_qdrant_collection.py whisperengine_memory_elena_7d whisperengine_memory_elena --dry-run
    
    # Actual migration (with confirmation prompt)
    python scripts/migrate_qdrant_collection.py whisperengine_memory_elena_7d whisperengine_memory_elena
"""

import sys
import os
from typing import Optional
import argparse
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


class QdrantMigrator:
    """Safely migrate Qdrant collections"""
    
    def __init__(self, host: str = "localhost", port: int = 6334):
        self.client = QdrantClient(host=host, port=port)
        self.batch_size = 100  # Process vectors in batches
    
    def validate_source(self, source_name: str) -> bool:
        """Check if source collection exists"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if source_name not in collection_names:
                print(f"❌ ERROR: Source collection '{source_name}' does not exist")
                print(f"Available collections: {', '.join(collection_names)}")
                return False
            
            # Get collection info
            info = self.client.get_collection(source_name)
            print(f"✅ Source collection '{source_name}' exists")
            print(f"   - Vectors count: {info.vectors_count}")
            print(f"   - Points count: {info.points_count}")
            return True
            
        except Exception as e:
            print(f"❌ ERROR validating source: {e}")
            return False
    
    def check_target_exists(self, target_name: str) -> bool:
        """Check if target collection already exists"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            return target_name in collection_names
        except Exception as e:
            print(f"❌ ERROR checking target: {e}")
            return False
    
    def get_collection_config(self, collection_name: str) -> dict:
        """Get collection configuration for replication"""
        try:
            info = self.client.get_collection(collection_name)
            
            # Extract vector configuration (it's a dict with vector names as keys)
            vectors_config = info.config.params.vectors
            
            # WhisperEngine uses a single unnamed vector or named vectors
            # Get the first vector config (or default vector if exists)
            if isinstance(vectors_config, dict):
                # Named vectors - get the first one or look for common names
                vector_names = list(vectors_config.keys())
                first_vector_name = vector_names[0] if vector_names else None
                if first_vector_name:
                    vector_config = vectors_config[first_vector_name]
                    size = vector_config.size
                    distance = vector_config.distance
                else:
                    raise ValueError("No vectors found in collection")
            else:
                # Single unnamed vector
                size = vectors_config.size
                distance = vectors_config.distance
            
            print(f"\n📋 Collection Configuration:")
            print(f"   - Vector config: {vectors_config}")
            print(f"   - Vector size: {size}")
            print(f"   - Distance: {distance}")
            
            return {
                "vectors_config": vectors_config,
                "vector_size": size,
                "vector_distance": distance,
                "points_count": info.points_count
            }
            
        except Exception as e:
            print(f"❌ ERROR getting collection config: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def create_target_collection(self, target_name: str, config: dict, dry_run: bool = False) -> bool:
        """Create target collection with same configuration as source"""
        try:
            if dry_run:
                print(f"\n[DRY RUN] Would create collection '{target_name}'")
                print(f"[DRY RUN] Vectors config: {config['vectors_config']}")
                return True
            
            # Create collection with same configuration as source
            # Use the exact vectors_config from source (handles both named and unnamed vectors)
            self.client.create_collection(
                collection_name=target_name,
                vectors_config=config['vectors_config']
            )
            
            print(f"✅ Created target collection '{target_name}'")
            return True
            
        except Exception as e:
            print(f"❌ ERROR creating target collection: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def copy_vectors(self, source_name: str, target_name: str, dry_run: bool = False) -> bool:
        """Copy all vectors from source to target collection"""
        try:
            # Get total count
            source_info = self.client.get_collection(source_name)
            total_points = source_info.points_count
            
            if total_points == 0:
                print("⚠️  Source collection is empty")
                return True
            
            if dry_run:
                print(f"\n[DRY RUN] Would copy {total_points} points from '{source_name}' to '{target_name}'")
                return True
            
            print(f"\n📦 Copying {total_points} points...")
            
            # Scroll through all points in batches
            offset = None
            copied_count = 0
            
            while True:
                # Fetch batch of points
                records, next_offset = self.client.scroll(
                    collection_name=source_name,
                    limit=self.batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )
                
                if not records:
                    break
                
                # Prepare points for insertion
                points = [
                    PointStruct(
                        id=record.id,
                        vector=record.vector,
                        payload=record.payload
                    )
                    for record in records
                ]
                
                # Insert batch into target collection
                self.client.upsert(
                    collection_name=target_name,
                    points=points
                )
                
                copied_count += len(records)
                print(f"   Copied {copied_count}/{total_points} points...", end='\r')
                
                # Check if we're done
                if next_offset is None:
                    break
                
                offset = next_offset
            
            print(f"\n✅ Copied {copied_count} points successfully")
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR copying vectors: {e}")
            return False
    
    def verify_migration(self, source_name: str, target_name: str) -> bool:
        """Verify that migration was successful"""
        try:
            source_info = self.client.get_collection(source_name)
            target_info = self.client.get_collection(target_name)
            
            source_count = source_info.points_count
            target_count = target_info.points_count
            
            print(f"\n🔍 Verification:")
            print(f"   Source: {source_count} points")
            print(f"   Target: {target_count} points")
            
            if source_count == target_count:
                print(f"✅ Point counts match!")
                return True
            else:
                print(f"❌ Point count mismatch!")
                return False
                
        except Exception as e:
            print(f"❌ ERROR verifying migration: {e}")
            return False
    
    def migrate(self, source_name: str, target_name: str, dry_run: bool = False) -> bool:
        """Execute complete migration workflow"""
        print(f"\n{'='*60}")
        print(f"🚀 Qdrant Collection Migration")
        print(f"{'='*60}")
        print(f"Source: {source_name}")
        print(f"Target: {target_name}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
        print(f"{'='*60}\n")
        
        # Step 1: Validate source exists
        if not self.validate_source(source_name):
            return False
        
        # Step 2: Check if target already exists
        if self.check_target_exists(target_name):
            print(f"❌ ERROR: Target collection '{target_name}' already exists!")
            print(f"   Please delete it first or choose a different name.")
            return False
        
        # Step 3: Get source collection configuration
        try:
            config = self.get_collection_config(source_name)
        except Exception:
            return False
        
        # Step 4: Confirm with user (if not dry run)
        if not dry_run:
            print(f"\n⚠️  About to migrate {config['points_count']} points")
            response = input(f"Proceed with migration? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Migration cancelled by user")
                return False
        
        # Step 5: Create target collection
        if not self.create_target_collection(target_name, config, dry_run):
            return False
        
        # Step 6: Copy vectors
        if not self.copy_vectors(source_name, target_name, dry_run):
            return False
        
        # Step 7: Verify migration (not for dry run)
        if not dry_run:
            if not self.verify_migration(source_name, target_name):
                return False
        
        print(f"\n{'='*60}")
        if dry_run:
            print("✅ DRY RUN COMPLETE - No changes made")
        else:
            print("✅ MIGRATION COMPLETE")
            print(f"\n⚠️  IMPORTANT: The old collection '{source_name}' still exists.")
            print(f"   After verifying the new collection works, you can delete it with:")
            print(f"   docker exec qdrant curl -X DELETE http://localhost:6333/collections/{source_name}")
        print(f"{'='*60}\n")
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Qdrant collection to new name",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run first to see what would happen
  python scripts/migrate_qdrant_collection.py whisperengine_memory_elena_7d whisperengine_memory_elena --dry-run
  
  # Actual migration
  python scripts/migrate_qdrant_collection.py whisperengine_memory_elena_7d whisperengine_memory_elena
  
  # Custom Qdrant connection
  python scripts/migrate_qdrant_collection.py source_collection target_collection --host localhost --port 6334
        """
    )
    
    parser.add_argument("source", help="Source collection name")
    parser.add_argument("target", help="Target collection name")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")
    parser.add_argument("--host", default="localhost", help="Qdrant host (default: localhost)")
    parser.add_argument("--port", type=int, default=6334, help="Qdrant port (default: 6334)")
    
    args = parser.parse_args()
    
    # Create migrator
    migrator = QdrantMigrator(host=args.host, port=args.port)
    
    # Execute migration
    success = migrator.migrate(args.source, args.target, dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
