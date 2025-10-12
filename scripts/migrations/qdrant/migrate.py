"""
Qdrant Schema Migration Manager

Manages Qdrant vector database schema changes with safety mechanisms:
- Snapshot-based backups before migrations
- Schema version tracking
- Rollback capability
- Validation and testing

Usage:
    python scripts/migrations/qdrant/migrate.py status
    python scripts/migrations/qdrant/migrate.py snapshot <collection>
    python scripts/migrations/qdrant/migrate.py migrate <collection> <version>
    python scripts/migrations/qdrant/migrate.py rollback <collection> <snapshot>
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Qdrant imports
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Current schema version
CURRENT_SCHEMA_VERSION = "3.0"  # 3D named vectors (content, emotion, semantic)


class QdrantMigrationManager:
    """Manages Qdrant schema migrations with safety mechanisms."""
    
    def __init__(self):
        """Initialize migration manager."""
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6334"))
        self.client = QdrantClient(host=self.host, port=self.port)
        
        logger.info(f"🔧 Connected to Qdrant at {self.host}:{self.port}")
    
    def get_all_collections(self) -> List[str]:
        """Get list of all collections."""
        collections = self.client.get_collections().collections
        return [c.name for c in collections]
    
    def get_schema_version(self, collection_name: str) -> Optional[str]:
        """
        Get schema version for a collection.
        
        Checks:
        1. Payload field 'schema_version' in vectors
        2. Collection metadata (if implemented)
        3. Defaults to "1.0" (legacy)
        """
        try:
            # Try to get a sample vector with schema_version
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                limit=1,
                with_payload=["schema_version"]
            )
            
            if scroll_result[0]:
                point = scroll_result[0][0]
                schema_version = point.payload.get("schema_version", "1.0")
                return schema_version
            
            # No vectors yet
            return None
            
        except Exception as e:
            logger.warning(f"Could not determine schema version for {collection_name}: {e}")
            return "unknown"
    
    def get_collection_schema(self, collection_name: str) -> Dict[str, Any]:
        """Get current schema configuration for a collection."""
        try:
            collection_info = self.client.get_collection(collection_name)
            
            return {
                "name": collection_name,
                "vectors_config": collection_info.config.params.vectors,
                "vector_count": collection_info.points_count,
                "schema_version": self.get_schema_version(collection_name),
                "indexed_fields": self._get_indexed_fields(collection_name)
            }
        except Exception as e:
            logger.error(f"Failed to get schema for {collection_name}: {e}")
            return {}
    
    def _get_indexed_fields(self, collection_name: str) -> List[str]:
        """Get list of indexed payload fields."""
        try:
            collection_info = self.client.get_collection(collection_name)
            # Extract indexed fields from collection info
            # Note: This is a simplified version
            return []  # TODO: Implement based on Qdrant API
        except Exception as e:
            logger.warning(f"Could not get indexed fields: {e}")
            return []
    
    def create_snapshot(self, collection_name: str) -> str:
        """
        Create snapshot of collection before migration.
        
        Returns:
            Snapshot name for rollback
        """
        try:
            snapshot_name = f"{collection_name}_{datetime.now():%Y%m%d_%H%M%S}"
            
            logger.info(f"📸 Creating snapshot: {snapshot_name}")
            result = self.client.create_snapshot(collection_name)
            
            logger.info(f"✅ Snapshot created: {result.name}")
            return result.name
            
        except Exception as e:
            logger.error(f"❌ Failed to create snapshot: {e}")
            raise
    
    def list_snapshots(self, collection_name: str) -> List[str]:
        """List available snapshots for a collection."""
        try:
            snapshots = self.client.list_snapshots(collection_name)
            return [s.name for s in snapshots]
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []
    
    def validate_schema(self, collection_name: str) -> Dict[str, Any]:
        """
        Validate collection schema against current version.
        
        Returns:
            Validation report with issues and recommendations
        """
        schema = self.get_collection_schema(collection_name)
        current_version = schema.get("schema_version", "unknown")
        
        issues = []
        recommendations = []
        
        # Check vector configuration
        vectors_config = schema.get("vectors_config", {})
        
        if isinstance(vectors_config, dict):
            # Named vectors (v3.0)
            expected_vectors = {"content", "emotion", "semantic"}
            current_vectors = set(vectors_config.keys())
            
            missing = expected_vectors - current_vectors
            extra = current_vectors - expected_vectors
            
            if missing:
                issues.append(f"Missing vectors: {missing}")
                recommendations.append("Run migration to add missing vectors")
            
            if extra:
                issues.append(f"Extra vectors (legacy): {extra}")
                recommendations.append("Extra vectors are OK but not used in current schema")
        else:
            # Single vector (legacy v1.0)
            issues.append("Legacy single-vector schema detected")
            recommendations.append("Migrate to 3D named vector schema (v3.0)")
        
        # Check schema version
        if current_version != CURRENT_SCHEMA_VERSION:
            issues.append(f"Schema version mismatch: {current_version} (expected {CURRENT_SCHEMA_VERSION})")
            recommendations.append(f"Run migration to upgrade to v{CURRENT_SCHEMA_VERSION}")
        
        return {
            "collection": collection_name,
            "current_version": current_version,
            "target_version": CURRENT_SCHEMA_VERSION,
            "issues": issues,
            "recommendations": recommendations,
            "status": "valid" if not issues else "needs_migration"
        }
    
    def show_status(self):
        """Show status of all collections."""
        collections = self.get_all_collections()
        
        print("=" * 80)
        print("Qdrant Schema Status")
        print("=" * 80)
        print(f"Host: {self.host}:{self.port}")
        print(f"Current Schema Version: {CURRENT_SCHEMA_VERSION}")
        print(f"Collections Found: {len(collections)}")
        print()
        
        for collection_name in collections:
            schema = self.get_collection_schema(collection_name)
            validation = self.validate_schema(collection_name)
            
            status_icon = "✅" if validation["status"] == "valid" else "⚠️"
            
            print(f"{status_icon} {collection_name}")
            print(f"   Version: {schema.get('schema_version', 'unknown')}")
            print(f"   Vectors: {schema.get('vector_count', 0):,}")
            
            if validation["issues"]:
                print(f"   Issues: {len(validation['issues'])}")
                for issue in validation["issues"][:2]:  # Show first 2
                    print(f"     - {issue}")
            
            print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    command = sys.argv[1].lower()
    
    try:
        manager = QdrantMigrationManager()
        
        if command == "status":
            manager.show_status()
            return 0
        
        elif command == "snapshot":
            if len(sys.argv) < 3:
                print("Usage: migrate.py snapshot <collection_name>")
                return 1
            
            collection_name = sys.argv[2]
            snapshot_name = manager.create_snapshot(collection_name)
            print(f"✅ Snapshot created: {snapshot_name}")
            return 0
        
        elif command == "snapshots":
            if len(sys.argv) < 3:
                print("Usage: migrate.py snapshots <collection_name>")
                return 1
            
            collection_name = sys.argv[2]
            snapshots = manager.list_snapshots(collection_name)
            
            print(f"Snapshots for {collection_name}:")
            for snapshot in snapshots:
                print(f"  - {snapshot}")
            return 0
        
        elif command == "validate":
            if len(sys.argv) < 3:
                print("Usage: migrate.py validate <collection_name>")
                return 1
            
            collection_name = sys.argv[2]
            validation = manager.validate_schema(collection_name)
            
            print(json.dumps(validation, indent=2))
            return 0 if validation["status"] == "valid" else 1
        
        elif command == "migrate":
            print("❌ Migration not yet implemented")
            print("This will be implemented in Phase 2")
            return 1
        
        elif command == "rollback":
            print("❌ Rollback not yet implemented")
            print("This will be implemented in Phase 2")
            return 1
        
        else:
            print(f"❌ Unknown command: {command}")
            print(__doc__)
            return 1
    
    except Exception as e:
        logger.error(f"❌ Command failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
