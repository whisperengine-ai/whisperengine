# Next Steps: Build and Test Quickstart Images

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
