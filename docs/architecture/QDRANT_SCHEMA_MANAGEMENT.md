# Qdrant Schema Management Analysis

**Date**: October 12, 2025  
**Status**: 🚨 CRITICAL GAP IDENTIFIED  
**Context**: Post-v1.0.6 migration system implementation

## 🔍 Current State Analysis

### How Qdrant Is Currently Managed

#### 1. **Collection Creation** (Application-Level)
Location: `src/memory/vector_memory_system.py:377-495`

```python
def _ensure_collection_exists(self):
    """Creates collection if it doesn't exist - runs on EVERY bot startup"""
    
    # Checks if collection exists
    collections = self.client.get_collections().collections
    
    if collection_name not in collections:
        # Creates 3D named vector collection
        vectors_config = {
            "content": VectorParams(size=384, distance=COSINE),
            "emotion": VectorParams(size=384, distance=COSINE),
            "semantic": VectorParams(size=384, distance=COSINE)
        }
        
        self.client.create_collection(...)
        self._create_payload_indexes()
    else:
        # Validates existing collection schema
        self._validate_and_upgrade_collection()
```

**When It Runs**:
- Every bot startup via `VectorMemorySystem.__init__()` (line 192)
- Each bot creates its own dedicated collection (e.g., `whisperengine_memory_elena`)

#### 2. **Payload Index Creation** (Application-Level)
Location: `src/memory/vector_memory_system.py:501-540`

```python
def _create_payload_indexes(self):
    """Creates indexes for filtering - safe to call multiple times"""
    
    required_indexes = [
        ("user_id", KEYWORD),
        ("memory_type", KEYWORD),
        ("timestamp_unix", FLOAT),
        ("semantic_key", KEYWORD),
        ("emotional_context", KEYWORD),
        ("content_hash", INTEGER)
    ]
    
    # Qdrant ignores duplicate index creation attempts
    for field_name, field_type in required_indexes:
        self.client.create_payload_index(...)
```

#### 3. **Schema Validation** (Application-Level)
Location: `src/memory/vector_memory_system.py:463-495`

```python
def _validate_and_upgrade_collection(self):
    """Validates collection has 3-vector schema"""
    
    collection_info = self.client.get_collection(collection_name)
    current_vectors = collection_info.config.params.vectors
    
    expected_vectors = {"content", "emotion", "semantic"}
    
    if missing_vectors:
        logger.error("Collection has incomplete vector schema!")
        logger.error("Please recreate collection or run migration script")
    
    # Always ensure indexes exist
    self._create_payload_indexes()
```

### 🚨 Critical Gaps Identified

#### ❌ **No Migration System for Qdrant Schema Changes**

**Problems**:
1. **Schema changes require manual intervention**
   - Adding new vector dimensions
   - Changing index configurations
   - Modifying HNSW parameters
   - Updating payload schema

2. **No versioning for vector schema**
   - Can't track which schema version a collection uses
   - No automated upgrade path from v1 → v2 → v3

3. **Risky validation-only approach**
   - `_validate_and_upgrade_collection()` only DETECTS issues
   - Doesn't actually FIX them (to avoid data loss)
   - Users must manually recreate collections

4. **No coordination with SQL migrations**
   - Alembic handles PostgreSQL schema
   - Qdrant schema handled separately
   - Could get out of sync

#### ❌ **Collection Recreation Destroys Data**

**Current Problem**:
```python
# If schema is wrong, user must:
docker exec qdrant-container qdrant-cli collection drop whisperengine_memory_elena
# Then restart bot to recreate

# Result: ALL MEMORIES LOST! 😱
```

#### ❌ **No Backup/Restore Strategy**

**Missing Capabilities**:
- No automated backups before schema changes
- No point-in-time restore
- No data migration tools for schema updates

## 🎯 Recommended Solution: Vector Schema Migration System

### Option 1: Qdrant Snapshots + Migration Scripts ✅ RECOMMENDED

**Approach**: Use Qdrant's built-in snapshot feature + custom migration logic

```python
# scripts/migrations/qdrant/migrate_qdrant_schema.py

class QdrantSchemaMigration:
    """Manages Qdrant schema migrations with safety"""
    
    def create_snapshot(self, collection_name: str) -> str:
        """Create snapshot before migration"""
        snapshot_name = f"{collection_name}_{datetime.now():%Y%m%d_%H%M%S}"
        self.client.create_snapshot(collection_name)
        return snapshot_name
    
    def migrate_collection_schema(
        self, 
        collection_name: str,
        old_schema: dict,
        new_schema: dict
    ):
        """Safely migrate collection to new schema"""
        
        # 1. Create snapshot
        snapshot = self.create_snapshot(collection_name)
        
        # 2. Create temporary collection with new schema
        temp_collection = f"{collection_name}_temp"
        self.client.create_collection(temp_collection, new_schema)
        
        # 3. Copy data with schema transformation
        self._copy_and_transform_vectors(
            source=collection_name,
            dest=temp_collection,
            transform=lambda v: self._upgrade_vector_schema(v, old_schema, new_schema)
        )
        
        # 4. Atomic swap (rename operations)
        self.client.delete_collection(collection_name)
        self.client.rename_collection(temp_collection, collection_name)
        
        # 5. Cleanup
        self.client.delete_snapshot(snapshot)  # Or keep for rollback
```

**Pros**:
- ✅ Built-in Qdrant features (snapshots are native)
- ✅ Data safety (snapshots for rollback)
- ✅ Flexible transformation logic
- ✅ Can handle complex schema changes

**Cons**:
- ⚠️ Custom migration code needed
- ⚠️ Requires careful testing
- ⚠️ Downtime during migration (seconds to minutes)

### Option 2: Parallel Collections + Gradual Migration

**Approach**: Blue-green deployment for vector collections

```python
# New collection: whisperengine_memory_elena_v2
# Old collection: whisperengine_memory_elena_v1

# Phase 1: Write to both collections
# Phase 2: Validate v2 has all data
# Phase 3: Switch reads to v2
# Phase 4: Delete v1
```

**Pros**:
- ✅ Zero downtime
- ✅ Easy rollback
- ✅ Gradual validation

**Cons**:
- ⚠️ Double storage cost during migration
- ⚠️ Complex write logic (dual writes)
- ⚠️ Slow migration process

### Option 3: Version Tracking in Payload

**Approach**: Store schema version in every vector's payload

```python
# Add to every vector:
payload = {
    "schema_version": "3.0",  # Track schema version
    "user_id": "...",
    # ... other fields
}

# On startup:
def _validate_and_upgrade_collection(self):
    # Check schema version in payload
    sample_points = self.client.scroll(limit=1)
    schema_version = sample_points[0].payload.get("schema_version", "1.0")
    
    if schema_version != CURRENT_SCHEMA_VERSION:
        self._run_schema_migration(schema_version, CURRENT_SCHEMA_VERSION)
```

**Pros**:
- ✅ Easy version detection
- ✅ Per-vector tracking
- ✅ Automated migration triggers

**Cons**:
- ⚠️ Requires updating ALL existing vectors
- ⚠️ Extra storage for version field
- ⚠️ Still need migration logic

## 📋 Proposed Implementation Plan

### Phase 1: Schema Version Tracking (Week 1)

**Goal**: Know what schema version each collection uses

1. **Add schema version to all new vectors**
   ```python
   # src/memory/vector_memory_system.py
   QDRANT_SCHEMA_VERSION = "3.0"  # 3D named vectors (current)
   
   payload = {
       "schema_version": QDRANT_SCHEMA_VERSION,
       "user_id": user_id,
       # ... existing fields
   }
   ```

2. **Create schema version table in PostgreSQL**
   ```sql
   CREATE TABLE qdrant_schema_versions (
       id SERIAL PRIMARY KEY,
       collection_name VARCHAR(255) NOT NULL UNIQUE,
       schema_version VARCHAR(50) NOT NULL,
       vectors_config JSONB NOT NULL,
       last_migration TIMESTAMP DEFAULT NOW(),
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **Track schema versions on collection creation**
   ```python
   def _ensure_collection_exists(self):
       # After creating collection
       await self._record_schema_version(
           collection_name=self.collection_name,
           schema_version=QDRANT_SCHEMA_VERSION,
           vectors_config=vectors_config
       )
   ```

### Phase 2: Migration Infrastructure (Week 2)

**Goal**: Build migration tools and safety mechanisms

1. **Create Qdrant migration manager**
   ```
   scripts/migrations/qdrant/
   ├── __init__.py
   ├── qdrant_migration_manager.py
   ├── schema_transformer.py
   └── versions/
       ├── 001_baseline_3d_vectors.py
       └── 002_add_relationship_vector.py  # Future example
   ```

2. **Implement snapshot-based migrations**
   ```python
   # scripts/migrations/qdrant/qdrant_migration_manager.py
   class QdrantMigrationManager:
       def migrate_to_version(self, target_version: str):
           """Safely migrate to target schema version"""
           
       def create_snapshot(self, collection: str):
           """Create snapshot before migration"""
           
       def restore_snapshot(self, snapshot_name: str):
           """Rollback to snapshot"""
   ```

3. **Add validation scripts**
   ```bash
   ./scripts/migrations/qdrant-migrate.sh status    # Check schema versions
   ./scripts/migrations/qdrant-migrate.sh migrate   # Apply migrations
   ./scripts/migrations/qdrant-migrate.sh rollback  # Restore snapshot
   ```

### Phase 3: Integration with Alembic (Week 3)

**Goal**: Coordinate SQL and vector schema changes

1. **Add Qdrant operations to Alembic migrations**
   ```python
   # alembic/versions/[timestamp]_add_relationship_vector.py
   
   def upgrade() -> None:
       # 1. SQL changes
       op.add_column('user_relationships', 
           sa.Column('relationship_embedding', sa.LargeBinary()))
       
       # 2. Qdrant schema changes
       from scripts.migrations.qdrant import QdrantMigrationManager
       qdrant_mgr = QdrantMigrationManager()
       qdrant_mgr.add_vector_dimension(
           collection="whisperengine_memory_*",
           vector_name="relationship",
           size=384
       )
   
   def downgrade() -> None:
       # Reverse both SQL and Qdrant changes
       pass
   ```

2. **Update Docker entrypoint**
   ```bash
   # scripts/docker-entrypoint.sh
   
   # Run SQL migrations
   alembic upgrade head
   
   # Run Qdrant migrations
   python scripts/migrations/qdrant-migrate.py upgrade
   ```

### Phase 4: Production Rollout (Week 4)

**Goal**: Apply to production safely

1. **Backfill schema versions for existing collections**
   ```bash
   python scripts/migrations/qdrant-backfill-versions.py
   ```

2. **Create snapshots of all collections**
   ```bash
   python scripts/migrations/qdrant-snapshot-all.py
   ```

3. **Document procedures**
   - Migration guide
   - Rollback procedures
   - Troubleshooting guide

## 🔧 Immediate Actions

### For v1.0.6+ Deployments

**1. Document current schema** (Do this NOW)
```bash
# Create schema documentation
./scripts/migrations/document-qdrant-schema.sh > docs/qdrant-schema-v1.0.6.json
```

**2. Add schema validation checks** (Next PR)
```python
# On bot startup, log schema version
logger.info(f"Qdrant schema version: {self._get_schema_version()}")
```

**3. Create snapshot backup script** (This week)
```bash
./scripts/migrations/backup-qdrant-collections.sh
```

## 🎓 Best Practices Going Forward

### DO ✅

- **Version all schema changes** - Track what changed and when
- **Create snapshots before migrations** - Always have rollback capability
- **Test migrations on sample data** - Verify transformations work
- **Coordinate with SQL migrations** - Keep schemas in sync
- **Document schema evolution** - Maintain schema changelog
- **Automate validation** - Detect schema drift early

### DON'T ❌

- **Manually drop collections** - Use migration scripts instead
- **Change schema without versioning** - Always track versions
- **Skip snapshots** - Data loss is not recoverable
- **Mix schema versions** - Ensure consistency across collections
- **Ignore validation errors** - Fix schema issues immediately

## 📚 References

- **Qdrant Snapshots**: https://qdrant.tech/documentation/concepts/snapshots/
- **Qdrant Collections**: https://qdrant.tech/documentation/concepts/collections/
- **Named Vectors**: https://qdrant.tech/documentation/concepts/vectors/#named-vectors
- **WhisperEngine Vector System**: `src/memory/vector_memory_system.py`

## 🎯 Next Steps

1. **Create this document** ✅ (Done)
2. **Create Qdrant migration manager** (Next PR)
3. **Implement snapshot-based migrations** (Week 2)
4. **Integrate with Alembic** (Week 3)
5. **Production rollout** (Week 4)

---

**Status**: 🚨 CRITICAL - Needs implementation  
**Priority**: HIGH - Required for schema evolution  
**Timeline**: 4 weeks to complete system
