# Qdrant Schema Migrations

This directory contains tools for managing Qdrant vector database schema changes.

## 🚨 Current Status

**Phase 1**: Schema validation and snapshot creation (IMPLEMENTED)  
**Phase 2**: Migration execution (TODO)  
**Phase 3**: Alembic integration (TODO)

## Quick Start

### Check Schema Status
```bash
python scripts/migrations/qdrant/migrate.py status
```

### Create Snapshot Before Changes
```bash
python scripts/migrations/qdrant/migrate.py snapshot whisperengine_memory_elena
```

### Validate Schema
```bash
python scripts/migrations/qdrant/migrate.py validate whisperengine_memory_elena
```

### List Snapshots
```bash
python scripts/migrations/qdrant/migrate.py snapshots whisperengine_memory_elena
```

## Current Schema Version

**v3.0**: 3D Named Vectors (current production)
- `content`: Main semantic content (384D)
- `emotion`: Emotional context (384D)  
- `semantic`: Concept/personality context (384D)

## Schema Evolution

- **v1.0**: Single vector (legacy)
- **v2.0**: 7D named vectors (deprecated)
- **v3.0**: 3D named vectors (current) ✅

## Documentation

See `docs/architecture/QDRANT_SCHEMA_MANAGEMENT.md` for complete guide.

## Coming Soon

- [ ] Automated schema migrations
- [ ] Rollback capability
- [ ] Integration with Alembic SQL migrations
- [ ] Zero-downtime migrations

---

**Status**: Phase 1 Complete  
**Next**: Implement migration execution
