# Next Steps: Database Migrations & Qdrant Schema Management

## 🚨 CRITICAL: Qdrant Schema Management Gap (October 12, 2025)

**Status**: 🚨 NO MIGRATION SYSTEM FOR VECTOR DATABASE  
**Priority**: HIGH - Required for schema evolution

### Problem Identified

While SQL migrations (Alembic) are now in place, **Qdrant vector database has NO migration system**:

❌ **Schema changes require manual collection recreation** (destroys all memories!)  
❌ **No versioning for vector schema** (can't track v1 → v2 → v3)  
❌ **No automated upgrade path** (validation detects issues but doesn't fix them)  
❌ **No coordination with SQL migrations** (schemas can get out of sync)

### Current State

**Collection Initialization**: Application-level in `src/memory/vector_memory_system.py`
- `_ensure_collection_exists()` - Creates 3D named vector collections on startup
- `_create_payload_indexes()` - Creates search indexes (safe to call multiple times)
- `_validate_and_upgrade_collection()` - Only DETECTS schema issues, doesn't FIX them

**Schema Validation Only**: No automated fixes
```python
if missing_vectors:
    logger.error("Collection has incomplete vector schema!")
    logger.error("Please recreate collection or run migration script")
    # ⚠️ Does NOT automatically fix - user must manually recreate!
```

### Quick Actions

```bash
# 1. Check current Qdrant schema status
python scripts/migrations/qdrant/migrate.py status

# 2. Create snapshots before any changes
python scripts/migrations/qdrant/migrate.py snapshot whisperengine_memory_elena

# 3. Validate schema compliance
python scripts/migrations/qdrant/migrate.py validate whisperengine_memory_elena
```

**See**: `docs/architecture/QDRANT_SCHEMA_MANAGEMENT.md` for complete analysis and roadmap

### Implementation Roadmap

- **Phase 1** (Week 1): Schema version tracking + snapshot tools ✅ STARTED
- **Phase 2** (Week 2): Migration execution with safety mechanisms
- **Phase 3** (Week 3): Integration with Alembic SQL migrations  
- **Phase 4** (Week 4): Production rollout and backfill

---

## 🔥 NEW: Database Migration System (October 11, 2025)

**Status**: ✅ Complete with Smart Auto-Migration  
**Priority**: CRITICAL - Required for post-v1.0.6 schema changes

### For v1.0.7+ Deployments:

**Zero manual commands required!** The smart entrypoint automatically:
- ✅ Detects fresh vs existing databases
- ✅ Handles v1.0.6 → v1.0.7 upgrades automatically  
- ✅ Applies pending migrations on future upgrades

```bash
# For new installations or v1.0.6 upgrades - just start containers
docker-compose up -d  # Everything automatic! ✅
```

### Manual Control (Optional):

```bash
# Only if you want explicit control over migrations
./scripts/migrations/db-migrate.sh stamp head  # v1.0.6 users only
```

### For New Features Requiring Schema Changes:

```bash
# 1. Create migration
./scripts/migrations/db-migrate.sh create "Add your feature description"

# 2. Edit alembic/versions/[generated_file].py
#    - Add SQL in upgrade()
#    - Add rollback SQL in downgrade()

# 3. Test locally
./scripts/migrations/db-migrate.sh upgrade

# 4. Test rollback
./scripts/migrations/db-migrate.sh downgrade -1

# 5. Commit migration file
git add alembic/versions/[generated_file].py
git commit -m "feat: Add [feature] database migration"
```

**See**: `docs/guides/DATABASE_MIGRATIONS.md` for complete guide

---

## 🔥 IMMEDIATE: Test Alternation Fixes (October 11, 2025)

**Status**: ✅ Fixes applied, awaiting validation  
**Priority**: CRITICAL - Blocks next major architecture improvement

### Testing Steps:

```bash
# 1. Test with Jake and Elena bots in Discord
# Send 3-5 messages to each bot, check responses

# 2. Inspect prompt logs for proper alternation
ls -lht logs/prompts/Jake_*672814231002939413.json | head -1
cat logs/prompts/Jake_*.json | jq '.messages[] | {role: .role, content_preview: .content[:100]}'

# 3. Validate: System message at beginning only, no mid-conversation system messages

# 4. Check memory context length (should be 500-5000 chars, NOT 136!)
cat logs/prompts/Jake_*.json | jq '.messages[0].content | length'
```

**See**: `ALTERNATION_FIX_TESTING_GUIDE.md` for comprehensive testing checklist

**Success Criteria**:
- ✅ No system messages mid-conversation
- ✅ Proper user→assistant→user alternation
- ✅ Memory context present in initial system message
- ✅ No hallucinations or API errors

---

## 🚀 IN PROGRESS: Structured Prompt Assembly Architecture (HIGH PRIORITY)

**Status**: ✅ Phase 2 COMPLETE - Active by default  
**Priority**: HIGH 🔥  
**Progress**: 50% complete (2/4 phases done)

### Why This Matters:
Recent alternation bugs exposed fragility of string concatenation approach. Structured assembly:
- ✅ Prevents alternation issues by design
- ✅ Enables token budget management
- ✅ Supports model-specific formatting (Claude XML, OpenAI sections, Mistral)
- ✅ Better debugging via component inspection
- ✅ Dynamic reordering without code changes

**See**: `docs/architecture/STRUCTURED_PROMPT_ASSEMBLY_ENHANCEMENT.md` for complete implementation plan

### Implementation Phases:
1. **Phase 1**: Core Infrastructure ✅ COMPLETE (Commit: eef0e5e)
   - PromptComponent dataclass with 20+ semantic types
   - PromptAssembler with filter→sort→budget→deduplicate pipeline
   - Comprehensive test suite: 18/18 tests passing in 5.11s
   - Coverage: prompt_components.py (96%), prompt_assembler.py (88%)
   
2. **Phase 2**: Message Processor Integration ✅ COMPLETE (Commits: c84f0f0, 1543d90)
   - New _build_conversation_context_structured() method (220 lines)
   - ✅ NO FEATURE FLAG - Active by default (compliance with dev rules)
   - Validation test suite: 9/9 checks passing
   - **Production status: ACTIVE on all bots**
   
3. **Phase 3**: Model-Specific Formatting 📋 NEXT
   - Implement Anthropic XML formatting (_assemble_anthropic)
   - Implement OpenAI section headers (_assemble_openai)
   - Implement Mistral concise optimization (_assemble_mistral)
   - Add model type detection from environment
   
4. **Phase 4**: Production Rollout 📋 PLANNED
   - Production monitoring and validation
   - Remove legacy _build_conversation_context() method
   - Update documentation
   - Archive old string concatenation approach

---

## 📋 BACKLOG: Build and Test Quickstart Images

## 🚀 Quick Commands

```bash
# 1. Build WhisperEngine bot image (with auto-migration)
cd /Users/mark/git/whisperengine
docker build -t whisperengine/whisperengine:latest .

# 2. Build Web UI image (with database library)
cd /Users/mark/git/whisperengine/cdl-web-ui
docker build -t whisperengine/whisperengine-ui:latest .

# 3. Test fresh quickstart deployment
cd /Users/mark/git/whisperengine
docker-compose -f docker-compose.quickstart.yml down -v
docker-compose -f docker-compose.quickstart.yml up -d

# 4. Verify auto-migration worked
docker logs whisperengine-assistant 2>&1 | grep -i "database initialization"

# 5. Test web UI health
curl http://localhost:3001/api/health

# 6. Test characters API
curl http://localhost:3001/api/characters

# 7. Push to Docker Hub (when ready)
docker push whisperengine/whisperengine:latest
docker push whisperengine/whisperengine-ui:latest
```

## ✅ What to Look For

### Auto-Migration Success Logs:
```
🔧 Checking database initialization...
✅ Database initialization complete!
```

### Web UI Health Check:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-10T...",
  "database": "connected"
}
```

### Characters API Response:
```json
{
  "success": true,
  "count": 1,
  "characters": [...]
}
```

## 🔍 Troubleshooting

If auto-migration fails:
```bash
# Check migration logs
docker logs whisperengine-assistant 2>&1 | grep -E "migration|database|error"

# Check if PostgreSQL is ready
docker logs whisperengine-postgres | tail -20

# Force recreate assistant
docker-compose -f docker-compose.quickstart.yml up -d --force-recreate whisperengine-assistant
```

## 📝 Summary

**Changes implemented:**
- ✅ Auto-migration in run.py (single source of truth)
- ✅ Web UI database library (db.ts)
- ✅ Port fixes (5433 → 5432)
- ✅ Docker configs updated (:latest tags)
- ✅ Documentation created (update guide)

**Ready to test:**
- Build both Docker images
- Test fresh deployment
- Verify auto-migration
- Push to Docker Hub
