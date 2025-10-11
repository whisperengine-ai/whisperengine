# WhisperEngine Quickstart Update Guide

## 🚀 Quick Update Commands

After your initial WhisperEngine installation, updating to the latest version is simple:

### Standard Update (Recommended)

```bash
# Navigate to your WhisperEngine directory
cd ~/whisperengine

# Pull latest Docker images
docker-compose -f docker-compose.quickstart.yml pull

# Restart with updated images (preserves data)
docker-compose -f docker-compose.quickstart.yml up -d

# Verify health
docker-compose -f docker-compose.quickstart.yml ps
```

**What this does:**
- ✅ Downloads latest WhisperEngine bot image
- ✅ Downloads latest CDL Web UI image
- ✅ Preserves all your data (PostgreSQL, Qdrant, InfluxDB volumes)
- ✅ Automatically applies database migrations
- ✅ Zero downtime for data storage (PostgreSQL/Qdrant/InfluxDB containers unaffected)

---

## 📋 Update Scenarios

### 1. Regular Updates (Keep All Data)

```bash
# Pull latest images
docker-compose -f docker-compose.quickstart.yml pull

# Recreate containers with new images
docker-compose -f docker-compose.quickstart.yml up -d
```

**Data preserved:**
- Character conversations and memory
- Vector embeddings
- User preferences and settings
- Custom character definitions
- Performance metrics

### 2. Update with Configuration Changes

If you've modified your `.env` file:

```bash
# Pull latest images
docker-compose -f docker-compose.quickstart.yml pull

# Restart to apply both image updates AND config changes
docker-compose -f docker-compose.quickstart.yml down
docker-compose -f docker-compose.quickstart.yml up -d
```

### 3. Clean Slate Update (Reset Everything)

⚠️ **Warning:** This deletes all data, conversations, and custom characters!

```bash
# Stop and remove everything including volumes
docker-compose -f docker-compose.quickstart.yml down -v

# Re-initialize with latest images
docker-compose -f docker-compose.quickstart.yml up -d
```

---

## 🔍 Checking Your Current Version

### View Running Image Tags

```bash
docker-compose -f docker-compose.quickstart.yml images
```

Expected output showing `:latest` tags:
```
CONTAINER                    IMAGE                                    TAG
whisperengine-assistant      whisperengine/whisperengine             latest
whisperengine-web-ui         whisperengine/whisperengine-ui          latest
whisperengine-postgres       postgres                                16.4-alpine
whisperengine-qdrant         qdrant/qdrant                           v1.15.4
whisperengine-influxdb       influxdb                                2.7-alpine
```

### Check Container Health

```bash
# View status
docker-compose -f docker-compose.quickstart.yml ps

# Check bot health
curl http://localhost:8080/health

# Check web UI health
curl http://localhost:3001/api/health
```

---

## 🛠️ Troubleshooting Updates

### Update Fails - Image Pull Error

```bash
# Check Docker Hub connectivity
docker pull whisperengine/whisperengine:latest

# If successful, retry compose update
docker-compose -f docker-compose.quickstart.yml pull
docker-compose -f docker-compose.quickstart.yml up -d
```

### Containers Won't Start After Update

```bash
# View container logs
docker-compose -f docker-compose.quickstart.yml logs whisperengine-assistant
docker-compose -f docker-compose.quickstart.yml logs whisperengine-web-ui

# Check for database migration errors
docker logs whisperengine-assistant 2>&1 | grep -i migration
```

### Database Migration Issues

WhisperEngine automatically applies database migrations on startup. If you see migration errors:

```bash
# View migration logs
docker logs whisperengine-assistant 2>&1 | grep -i "database\|migration"

# Force recreation (preserves data)
docker-compose -f docker-compose.quickstart.yml up -d --force-recreate whisperengine-assistant
```

### Rolling Back to Previous Version

If an update causes issues:

```bash
# Stop current version
docker-compose -f docker-compose.quickstart.yml down

# Pull specific version (example)
docker pull whisperengine/whisperengine:v1.0.1
docker pull whisperengine/whisperengine-ui:v1.0.1

# Temporarily edit docker-compose.quickstart.yml to use specific tags
# Then restart:
docker-compose -f docker-compose.quickstart.yml up -d
```

---

## 📊 Update Maintenance Best Practices

### Before Updating

```bash
# 1. Check current system health
docker-compose -f docker-compose.quickstart.yml ps
curl http://localhost:8080/health

# 2. Backup volumes (optional but recommended)
docker run --rm -v whisperengine-postgres-data:/data \
  -v $(pwd)/backups:/backup ubuntu tar czf \
  /backup/postgres-backup-$(date +%Y%m%d).tar.gz /data
```

### After Updating

```bash
# 1. Verify containers started
docker-compose -f docker-compose.quickstart.yml ps

# 2. Check health endpoints
curl http://localhost:8080/health
curl http://localhost:3001/api/health

# 3. Test web UI
open http://localhost:3001

# 4. Check logs for errors
docker-compose -f docker-compose.quickstart.yml logs --tail 50
```

---

## 🔄 Automatic Updates (Advanced)

For users who want automatic updates:

### Option 1: Manual Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add weekly update check (Sundays at 2 AM)
0 2 * * 0 cd ~/whisperengine && docker-compose -f docker-compose.quickstart.yml pull && docker-compose -f docker-compose.quickstart.yml up -d
```

### Option 2: Watchtower (Automated Container Updates)

```bash
# Add to docker-compose.quickstart.yml:
# services:
#   watchtower:
#     image: containrrr/watchtower
#     volumes:
#       - /var/run/docker.sock:/var/run/docker.sock
#     environment:
#       - WATCHTOWER_POLL_INTERVAL=86400  # Check daily
#       - WATCHTOWER_CLEANUP=true
#       - WATCHTOWER_INCLUDE_STOPPED=false
```

---

## 📝 What Gets Updated

### WhisperEngine Bot Container (`whisperengine/whisperengine:latest`)
- Core AI personality engine
- Memory systems (vector, graph, temporal)
- Database migrations
- Character intelligence systems
- API endpoints
- Performance optimizations

### Web UI Container (`whisperengine/whisperengine-ui:latest`)
- Character management interface
- CDL editor improvements
- Dashboard enhancements
- Bug fixes
- UX improvements

### What Doesn't Change
- Database volumes (conversations, characters, settings)
- Vector embeddings (Qdrant data)
- Time-series metrics (InfluxDB data)
- Your `.env` configuration
- Infrastructure containers (PostgreSQL, Qdrant, InfluxDB use pinned versions)

---

## 🆘 Getting Help

If you encounter issues during updates:

1. **Check Logs:** `docker-compose -f docker-compose.quickstart.yml logs`
2. **GitHub Issues:** https://github.com/yourusername/whisperengine/issues
3. **Discord Community:** [Your Discord Link]
4. **Documentation:** https://github.com/yourusername/whisperengine/wiki

---

## 🎯 Quick Reference

```bash
# Update everything
docker-compose -f docker-compose.quickstart.yml pull && \
  docker-compose -f docker-compose.quickstart.yml up -d

# View logs
docker-compose -f docker-compose.quickstart.yml logs -f

# Check health
docker-compose -f docker-compose.quickstart.yml ps
curl http://localhost:8080/health

# Restart specific service
docker-compose -f docker-compose.quickstart.yml restart whisperengine-assistant

# Stop everything
docker-compose -f docker-compose.quickstart.yml down

# Start everything
docker-compose -f docker-compose.quickstart.yml up -d
```

---

**Note:** WhisperEngine uses `:latest` tags in quickstart for automatic updates. Database migrations are handled automatically - no manual SQL scripts needed!
