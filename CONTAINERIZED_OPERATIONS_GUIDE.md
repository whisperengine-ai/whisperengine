# WhisperEngine Containerized Operations Guide

Complete guide for managing, updating, backing up, and troubleshooting your containerized WhisperEngine installation.

## 📋 Quick Reference

### **Essential Commands**
```bash
# Start WhisperEngine
./setup-containerized.sh              # Linux/macOS
setup-containerized.bat               # Windows

# Check status
docker ps
curl http://localhost:3001            # Web UI
curl http://localhost:9090/health     # API health

# View logs
docker logs whisperengine-app
docker logs whisperengine-ui

# Stop everything
docker-compose -f docker-compose.containerized.yml down

# Update to latest version
docker-compose -f docker-compose.containerized.yml down
docker-compose -f docker-compose.containerized.yml pull
docker-compose -f docker-compose.containerized.yml up -d
```

### **Emergency Commands**
```bash
# Complete reset (⚠️ DELETES ALL DATA!)
docker-compose -f docker-compose.containerized.yml down -v
docker volume prune
./setup-containerized.sh

# Restart specific service
docker-compose -f docker-compose.containerized.yml restart whisperengine-app
docker-compose -f docker-compose.containerized.yml restart whisperengine-ui
```

## 🔄 Updates & Version Management

### **Standard Update Process**

**Method 1: Quick Update (Recommended)**
```bash
# Stop containers
docker-compose -f docker-compose.containerized.yml down

# Pull latest versions
docker-compose -f docker-compose.containerized.yml pull

# Start with new versions
docker-compose -f docker-compose.containerized.yml up -d

# Verify update
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
```

**Method 2: Re-run Setup Script**
```bash
# Quick method - re-run setup script
./setup-containerized.sh              # Linux/macOS
setup-containerized.bat               # Windows
```

### **Version Management**

**Check Current Versions:**
```bash
# Container versions
docker images | grep whisperengine

# Running container details
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

# API version info
curl http://localhost:9090/health | jq '.version'  # If jq installed
curl http://localhost:9090/health                  # Raw output
```

**Pin to Specific Version:**
Edit `docker-compose.containerized.yml`:
```yaml
services:
  whisperengine-app:
    image: whisperengine/whisperengine:v1.0.0  # Instead of 'latest'
  
  whisperengine-ui:
    image: whisperengine/whisperengine-ui:v1.0.0  # Instead of 'latest'
```

**Roll Back to Previous Version:**
```bash
# Stop current containers
docker-compose -f docker-compose.containerized.yml down

# Edit docker-compose.containerized.yml to use specific version tags
# Then pull the specific versions
docker pull whisperengine/whisperengine:v1.0.0
docker pull whisperengine/whisperengine-ui:v1.0.0

# Start with specific version
docker-compose -f docker-compose.containerized.yml up -d
```

### **Update Notifications**

**Check for New Releases:**
- Visit: https://github.com/whisperengine-ai/whisperengine/releases
- Docker Hub: https://hub.docker.com/r/whisperengine/whisperengine/tags

**Set Up Update Reminders:**
```bash
# Add to crontab for weekly update checks
crontab -e

# Add this line to check weekly:
0 9 * * 1 echo "Check for WhisperEngine updates: https://github.com/whisperengine-ai/whisperengine/releases" | mail -s "WhisperEngine Update Check" your-email@example.com
```

## 💾 Backup & Data Protection

### **Understanding WhisperEngine Data**

**Data Volumes:**
- **`whisperengine_postgres_data`**: Character definitions, user accounts, conversation metadata
- **`whisperengine_qdrant_data`**: Vector memories, semantic search indexes, conversation embeddings
- **`whisperengine_app_logs`**: Application logs, error traces, debug information

**What's Backed Up:**
- ✅ All your custom characters
- ✅ User accounts and profiles
- ✅ Complete conversation history
- ✅ Character memories and personality adaptation
- ✅ System configuration and logs

**What's NOT Backed Up:**
- ❌ Container images (re-downloaded from Docker Hub)
- ❌ Temporary files and caches
- ❌ API keys (stored in .env - back up separately)

### **Automated Backup Solution**

**Linux/macOS Backup Script (`backup-whisperengine.sh`):**
```bash
#!/bin/bash
set -e

# Configuration
BACKUP_BASE_DIR="whisperengine-backups"
BACKUP_DIR="$BACKUP_BASE_DIR/$(date +%Y%m%d_%H%M%S)"
MAX_BACKUPS=7  # Keep last 7 backups

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "🔄 Creating WhisperEngine backup in $BACKUP_DIR..."

# Backup PostgreSQL data (characters, users, metadata)
echo "📊 Backing up PostgreSQL data..."
docker run --rm \
  -v whisperengine_postgres_data:/source:ro \
  -v "$(pwd)/$BACKUP_DIR":/backup \
  alpine tar czf /backup/postgres_data.tar.gz -C /source .

# Backup Qdrant data (vector memories)
echo "🧠 Backing up vector memories..."
docker run --rm \
  -v whisperengine_qdrant_data:/source:ro \
  -v "$(pwd)/$BACKUP_DIR":/backup \
  alpine tar czf /backup/qdrant_data.tar.gz -C /source .

# Backup application logs
echo "📝 Backing up logs..."
docker run --rm \
  -v whisperengine_app_logs:/source:ro \
  -v "$(pwd)/$BACKUP_DIR":/backup \
  alpine tar czf /backup/app_logs.tar.gz -C /source .

# Backup configuration files
echo "⚙️ Backing up configuration..."
cp docker-compose.containerized.yml "$BACKUP_DIR/" 2>/dev/null || true
cp .env "$BACKUP_DIR/" 2>/dev/null || true

# Create backup manifest
cat > "$BACKUP_DIR/backup_manifest.txt" << EOF
WhisperEngine Backup Created: $(date)
Backup Directory: $BACKUP_DIR
Components:
- PostgreSQL Data: postgres_data.tar.gz
- Qdrant Data: qdrant_data.tar.gz  
- Application Logs: app_logs.tar.gz
- Configuration: docker-compose.containerized.yml, .env

Restore Command:
./restore-whisperengine.sh $(basename "$BACKUP_DIR")
EOF

# Cleanup old backups
echo "🧹 Cleaning up old backups (keeping last $MAX_BACKUPS)..."
cd "$BACKUP_BASE_DIR"
ls -1t | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -rf
cd - > /dev/null

echo "✅ Backup completed: $BACKUP_DIR"
echo "📁 Files created:"
ls -lh "$BACKUP_DIR/"
echo ""
echo "📋 Backup manifest:"
cat "$BACKUP_DIR/backup_manifest.txt"
```

**Windows Backup Script (`backup-whisperengine.bat`):**
```batch
@echo off
setlocal enabledelayedexpansion

REM Configuration
set MAX_BACKUPS=7

REM Create timestamp
for /f "tokens=1-6 delims=/: " %%i in ("%date% %time%") do (
    set BACKUP_DIR=whisperengine-backups\%%k%%j%%i_%%l%%m
)

mkdir "%BACKUP_DIR%" 2>nul

echo Creating WhisperEngine backup in %BACKUP_DIR%...

REM Backup PostgreSQL data
echo Backing up PostgreSQL data...
docker run --rm -v whisperengine_postgres_data:/source:ro -v "%cd%\%BACKUP_DIR%":/backup alpine tar czf /backup/postgres_data.tar.gz -C /source .

REM Backup Qdrant data  
echo Backing up vector memories...
docker run --rm -v whisperengine_qdrant_data:/source:ro -v "%cd%\%BACKUP_DIR%":/backup alpine tar czf /backup/qdrant_data.tar.gz -C /source .

REM Backup logs
echo Backing up logs...
docker run --rm -v whisperengine_app_logs:/source:ro -v "%cd%\%BACKUP_DIR%":/backup alpine tar czf /backup/app_logs.tar.gz -C /source .

REM Backup configuration
echo Backing up configuration...
copy docker-compose.containerized.yml "%BACKUP_DIR%\" >nul 2>&1
copy .env "%BACKUP_DIR%\" >nul 2>&1

REM Create manifest
echo WhisperEngine Backup Created: %date% %time% > "%BACKUP_DIR%\backup_manifest.txt"
echo Backup Directory: %BACKUP_DIR% >> "%BACKUP_DIR%\backup_manifest.txt"
echo. >> "%BACKUP_DIR%\backup_manifest.txt"
echo Restore with: restore-whisperengine.bat %BACKUP_DIR% >> "%BACKUP_DIR%\backup_manifest.txt"

echo Backup completed: %BACKUP_DIR%
dir "%BACKUP_DIR%"
```

### **Restore Solution**

**Linux/macOS Restore Script (`restore-whisperengine.sh`):**
```bash
#!/bin/bash
set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_directory_name>"
    echo "Example: $0 20241010_143000"
    echo ""
    echo "Available backups:"
    ls -1 whisperengine-backups/ 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_DIR="whisperengine-backups/$BACKUP_NAME"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "⚠️  WARNING: This will replace ALL current WhisperEngine data!"
echo "Restoring from: $BACKUP_DIR"
echo "Type 'RESTORE' to confirm:"
read confirmation

if [ "$confirmation" != "RESTORE" ]; then
    echo "❌ Restore cancelled"
    exit 1
fi

echo "🔄 Stopping WhisperEngine..."
docker-compose -f docker-compose.containerized.yml down

echo "🗑️  Removing existing volumes..."
docker volume rm whisperengine_postgres_data 2>/dev/null || true
docker volume rm whisperengine_qdrant_data 2>/dev/null || true
docker volume rm whisperengine_app_logs 2>/dev/null || true

echo "📊 Restoring PostgreSQL data..."
docker run --rm \
  -v whisperengine_postgres_data:/target \
  -v "$(pwd)/$BACKUP_DIR":/backup:ro \
  alpine tar xzf /backup/postgres_data.tar.gz -C /target

echo "🧠 Restoring vector memories..."
docker run --rm \
  -v whisperengine_qdrant_data:/target \
  -v "$(pwd)/$BACKUP_DIR":/backup:ro \
  alpine tar xzf /backup/qdrant_data.tar.gz -C /target

echo "📝 Restoring logs..."
docker run --rm \
  -v whisperengine_app_logs:/target \
  -v "$(pwd)/$BACKUP_DIR":/backup:ro \
  alpine tar xzf /backup/app_logs.tar.gz -C /target

echo "🚀 Starting WhisperEngine..."
docker-compose -f docker-compose.containerized.yml up -d

echo "✅ Restore completed successfully!"
echo "🌐 Web interface: http://localhost:3001"
echo "🔌 API endpoint: http://localhost:9090"
```

### **Backup Scheduling**

**Daily Automated Backups (Linux/macOS):**
```bash
# Make scripts executable
chmod +x backup-whisperengine.sh
chmod +x restore-whisperengine.sh

# Add to crontab for daily backups at 2 AM
crontab -e

# Add these lines:
# Daily backup at 2 AM
0 2 * * * /full/path/to/whisperengine/backup-whisperengine.sh >> /var/log/whisperengine-backup.log 2>&1

# Weekly cleanup at 3 AM on Sundays
0 3 * * 0 find /full/path/to/whisperengine/whisperengine-backups -type d -mtime +30 -exec rm -rf {} \;
```

**Windows Task Scheduler Setup:**
1. Open Task Scheduler
2. Create Basic Task → "WhisperEngine Daily Backup"
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `cmd.exe`
6. Arguments: `/c "cd /d C:\path\to\whisperengine && backup-whisperengine.bat"`

### **Backup Verification**

**Check Backup Integrity:**
```bash
# Verify backup files exist and aren't empty
BACKUP_DIR="whisperengine-backups/20241010_143000"

echo "🔍 Verifying backup integrity..."

# Check file sizes
echo "📁 Backup files:"
ls -lh "$BACKUP_DIR/"

# Verify tar files can be read
echo "📊 Testing PostgreSQL backup..."
tar -tzf "$BACKUP_DIR/postgres_data.tar.gz" > /dev/null && echo "✅ PostgreSQL backup OK" || echo "❌ PostgreSQL backup corrupted"

echo "🧠 Testing Qdrant backup..."
tar -tzf "$BACKUP_DIR/qdrant_data.tar.gz" > /dev/null && echo "✅ Qdrant backup OK" || echo "❌ Qdrant backup corrupted"

echo "📝 Testing logs backup..."
tar -tzf "$BACKUP_DIR/app_logs.tar.gz" > /dev/null && echo "✅ Logs backup OK" || echo "❌ Logs backup corrupted"

# Check manifest
if [ -f "$BACKUP_DIR/backup_manifest.txt" ]; then
    echo "📋 Backup manifest:"
    cat "$BACKUP_DIR/backup_manifest.txt"
else
    echo "⚠️  Backup manifest missing"
fi
```

## 🧹 Cleanup & Reset Operations

### **Cleanup Strategies**

#### **1. Soft Cleanup (Keep All Data)**
```bash
# Stop containers only
docker-compose -f docker-compose.containerized.yml down

# Remove container images (will re-download on next start)
docker rmi whisperengine/whisperengine:latest 2>/dev/null || true
docker rmi whisperengine/whisperengine-ui:latest 2>/dev/null || true

# Clean up unused Docker resources
docker system prune -f

# Restart fresh (preserves all your data)
./setup-containerized.sh  # Linux/macOS
# OR  
setup-containerized.bat   # Windows
```

#### **2. Moderate Cleanup (Keep Characters, Reset Conversations)**
```bash
# ⚠️ This keeps characters but removes conversation history

# Stop WhisperEngine
docker-compose -f docker-compose.containerized.yml down

# Remove only vector memory (conversations/memories)
docker volume rm whisperengine_qdrant_data
docker volume rm whisperengine_app_logs

# Keep character definitions (PostgreSQL data preserved)
# Restart
docker-compose -f docker-compose.containerized.yml up -d
```

#### **3. Complete Reset (Nuclear Option)**
```bash
# ⚠️ WARNING: This deletes EVERYTHING!

echo "This will delete ALL WhisperEngine data including:"
echo "- All custom characters"  
echo "- All conversation history"
echo "- All user accounts"
echo "- All memories and personalization"
echo ""
echo "Type 'DELETE_EVERYTHING' to confirm:"
read confirmation

if [ "$confirmation" = "DELETE_EVERYTHING" ]; then
    echo "🔄 Performing complete reset..."
    
    # Stop and remove containers + volumes
    docker-compose -f docker-compose.containerized.yml down -v
    
    # Remove all WhisperEngine volumes explicitly
    docker volume rm whisperengine_postgres_data 2>/dev/null || true
    docker volume rm whisperengine_qdrant_data 2>/dev/null || true
    docker volume rm whisperengine_app_logs 2>/dev/null || true
    
    # Remove container images
    docker rmi whisperengine/whisperengine:latest 2>/dev/null || true
    docker rmi whisperengine/whisperengine-ui:latest 2>/dev/null || true
    
    # Clean up Docker system
    docker system prune -af
    
    echo "✅ Complete reset finished."
    echo "🚀 Run ./setup-containerized.sh to start fresh"
else
    echo "❌ Reset cancelled. No changes made."
fi
```

### **Disk Space Management**

#### **Check Docker Disk Usage**
```bash
# Overview of Docker disk usage
docker system df

# Detailed breakdown
docker system df -v

# Check specific volumes
docker volume ls
du -sh /var/lib/docker/volumes/whisperengine_* 2>/dev/null || echo "Volumes not found"
```

#### **Free Up Disk Space**
```bash
# Clean up unused containers, networks, images (safe)
docker system prune

# More aggressive cleanup (removes all unused items)
docker system prune -a

# Clean up specific items
docker container prune    # Remove stopped containers
docker image prune        # Remove unused images  
docker network prune      # Remove unused networks

# ⚠️ Be careful with volume cleanup - this can delete data!
# docker volume prune     # Only run if you're sure!
```

#### **Monitor Disk Usage**
```bash
# Create a disk monitoring script
cat > monitor-disk-usage.sh << 'EOF'
#!/bin/bash
echo "=== Docker Disk Usage Report ==="
echo "Date: $(date)"
echo ""

echo "📊 Overall Docker usage:"
docker system df
echo ""

echo "📦 WhisperEngine volumes:"
docker volume ls | grep whisperengine
echo ""

echo "🖥️  System disk usage:"
df -h /
echo ""

echo "📈 Volume sizes:"
for vol in $(docker volume ls -q | grep whisperengine); do
    size=$(docker run --rm -v $vol:/data alpine du -sh /data | cut -f1)
    echo "  $vol: $size"
done
EOF

chmod +x monitor-disk-usage.sh
./monitor-disk-usage.sh
```

## 🔧 Troubleshooting Guide

### **Diagnostic Commands**

#### **Quick Health Check**
```bash
# All-in-one health check
cat > health-check.sh << 'EOF'
#!/bin/bash
echo "🔍 WhisperEngine Health Check"
echo "============================="

echo "1. Docker Status:"
docker --version 2>/dev/null && echo "✅ Docker installed" || echo "❌ Docker not found"
docker info >/dev/null 2>&1 && echo "✅ Docker running" || echo "❌ Docker not running"

echo ""
echo "2. Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep whisperengine

echo ""
echo "3. Service Health:"
curl -s http://localhost:3001 >/dev/null && echo "✅ Web UI responding" || echo "❌ Web UI not responding"
curl -s http://localhost:9090/health >/dev/null && echo "✅ API responding" || echo "❌ API not responding"

echo ""
echo "4. Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep whisperengine

echo ""
echo "5. Recent Errors:"
echo "App container errors (last 10 lines):"
docker logs whisperengine-app --tail 10 2>/dev/null | grep -i error || echo "No recent errors"

echo ""
echo "UI container errors (last 10 lines):"
docker logs whisperengine-ui --tail 10 2>/dev/null | grep -i error || echo "No recent errors"
EOF

chmod +x health-check.sh
./health-check.sh
```

### **Common Issues & Solutions**

#### **Issue 1: Setup Script Fails**

**Symptoms:**
- Script hangs or exits with error
- "Docker not found" or "permission denied" messages

**Solutions:**
```bash
# Check Docker installation
docker --version
docker info

# Fix permissions (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Manual setup if script fails
docker-compose -f docker-compose.containerized.yml pull
docker-compose -f docker-compose.containerized.yml up -d

# Check what went wrong
docker-compose -f docker-compose.containerized.yml logs
```

#### **Issue 2: Containers Won't Start**

**Symptoms:**
- Containers appear then disappear
- Exit codes 1, 125, 126, 127

**Diagnosis:**
```bash
# Check container status
docker ps -a

# Check exit codes and reasons
docker-compose -f docker-compose.containerized.yml ps

# Check logs for errors
docker-compose -f docker-compose.containerized.yml logs whisperengine-app
docker-compose -f docker-compose.containerized.yml logs whisperengine-ui
```

**Solutions:**
```bash
# Try starting services one by one
docker-compose -f docker-compose.containerized.yml up -d postgres qdrant
sleep 10
docker-compose -f docker-compose.containerized.yml up -d whisperengine-app
sleep 10  
docker-compose -f docker-compose.containerized.yml up -d whisperengine-ui

# Check system resources
docker stats
df -h  # Disk space
free -h  # Memory (Linux)

# Reset if corrupted
docker-compose -f docker-compose.containerized.yml down -v
./setup-containerized.sh
```

#### **Issue 3: Port Conflicts**

**Symptoms:**
- "Port already in use" errors
- Cannot access web interface or API

**Diagnosis:**
```bash
# Check what's using the ports
lsof -i :3001    # Web UI
lsof -i :9090    # API
lsof -i :5432    # PostgreSQL  
lsof -i :6333    # Qdrant

# On Windows:
netstat -ano | findstr :3001
netstat -ano | findstr :9090
```

**Solutions:**
```bash
# Kill conflicting processes (replace <PID>)
kill -9 <PID>

# Or change ports in docker-compose.containerized.yml
# Edit the file and change "3001:3000" to "3002:3000" etc.

# Restart with new ports
docker-compose -f docker-compose.containerized.yml down
docker-compose -f docker-compose.containerized.yml up -d
```

#### **Issue 4: Web Interface Loading Issues**

**Symptoms:**
- Blank page, loading forever
- "Connection refused" errors
- 404 or 500 errors

**Diagnosis:**
```bash
# Check UI container
docker ps | grep whisperengine-ui
docker logs whisperengine-ui

# Check if UI is responding
curl http://localhost:3001
curl http://localhost:3001/api/health

# Check browser network tab for errors
```

**Solutions:**
```bash
# Restart UI container
docker-compose -f docker-compose.containerized.yml restart whisperengine-ui

# Check browser cache
# Try incognito/private mode
# Try different browser

# Reset UI container
docker-compose -f docker-compose.containerized.yml stop whisperengine-ui
docker rmi whisperengine/whisperengine-ui:latest
docker-compose -f docker-compose.containerized.yml up -d whisperengine-ui
```

#### **Issue 5: API Connection Problems**

**Symptoms:**
- API requests timeout
- "Internal server error" responses
- Character responses don't work

**Diagnosis:**
```bash
# Check app container
docker ps | grep whisperengine-app
docker logs whisperengine-app

# Test API health
curl http://localhost:9090/health
curl -X POST http://localhost:9090/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "hello"}'

# Check database connections
docker exec whisperengine-app python -c "
import psycopg2
try:
    conn = psycopg2.connect('host=postgres user=whisperengine password=whisperengine_password dbname=whisperengine')
    print('✅ PostgreSQL connected')
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL error: {e}')
"
```

**Solutions:**
```bash
# Restart app container
docker-compose -f docker-compose.containerized.yml restart whisperengine-app

# Check dependencies are running
docker-compose -f docker-compose.containerized.yml ps postgres qdrant

# Full restart in correct order
docker-compose -f docker-compose.containerized.yml down
docker-compose -f docker-compose.containerized.yml up -d postgres qdrant
sleep 10
docker-compose -f docker-compose.containerized.yml up -d whisperengine-app whisperengine-ui
```

#### **Issue 6: Performance Problems**

**Symptoms:**
- Slow response times
- High CPU/memory usage
- System becoming unresponsive

**Diagnosis:**
```bash
# Check resource usage
docker stats

# Check system resources
top          # Linux/macOS
htop         # If available
df -h        # Disk space
free -h      # Memory (Linux)

# Check container limits
docker inspect whisperengine-app | grep -A 10 "Memory"
```

**Solutions:**
```bash
# Add resource limits to docker-compose.containerized.yml
services:
  whisperengine-app:
    image: whisperengine/whisperengine:latest
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

# Clean up disk space
docker system prune
df -h

# Restart to clear memory leaks
docker-compose -f docker-compose.containerized.yml restart
```

### **Advanced Troubleshooting**

#### **Container Debugging**
```bash
# Enter running container for debugging
docker exec -it whisperengine-app /bin/bash
docker exec -it whisperengine-ui /bin/sh

# Check container filesystem
docker exec whisperengine-app ls -la /app
docker exec whisperengine-app cat /app/logs/app.log

# Check environment variables
docker exec whisperengine-app env | grep WHISPER

# Check network connectivity between containers
docker exec whisperengine-app ping postgres
docker exec whisperengine-app ping qdrant
```

#### **Log Analysis**
```bash
# Follow logs in real-time
docker-compose -f docker-compose.containerized.yml logs -f

# Search for specific errors
docker logs whisperengine-app 2>&1 | grep -i "error\|exception\|failed"

# Export logs for analysis
docker logs whisperengine-app > app-logs.txt 2>&1
docker logs whisperengine-ui > ui-logs.txt 2>&1

# Check log rotation
docker exec whisperengine-app ls -la /app/logs/
```

#### **Network Debugging**
```bash
# Check Docker networks
docker network ls
docker network inspect $(docker-compose -f docker-compose.containerized.yml ps -q | head -1)

# Test connectivity
docker exec whisperengine-app curl http://postgres:5432
docker exec whisperengine-app curl http://qdrant:6333

# Check DNS resolution
docker exec whisperengine-app nslookup postgres
docker exec whisperengine-app nslookup qdrant
```

## 📞 Getting Help

### **Self-Service Resources**

1. **Check this guide first** - Most issues are covered here
2. **Docker documentation** - https://docs.docker.com/
3. **WhisperEngine logs** - `docker logs whisperengine-app`
4. **Health check** - Run `./health-check.sh` (created above)

### **Community Support**

- **GitHub Issues**: Report bugs and request features
- **Discord Server**: Real-time community help
- **Documentation**: Complete guides and API reference

### **Emergency Procedures**

**If everything is broken:**
1. Create backup: `./backup-whisperengine.sh`
2. Complete reset: Follow "Complete Reset" procedure above
3. Restore from backup if needed: `./restore-whisperengine.sh BACKUP_DATE`

**If you need immediate help:**
1. Run health check: `./health-check.sh`
2. Collect logs: `docker-compose -f docker-compose.containerized.yml logs > debug-logs.txt`
3. Include system info: `docker info >> debug-logs.txt`
4. Share debug-logs.txt when asking for help

---

## 📋 Operations Checklist

### **Daily Operations**
- [ ] Check health status: `./health-check.sh`
- [ ] Monitor disk usage: `docker system df`
- [ ] Check for errors in logs: `docker logs whisperengine-app --tail 50`

### **Weekly Operations**  
- [ ] Check for updates: Visit GitHub releases page
- [ ] Run backup: `./backup-whisperengine.sh`
- [ ] Clean up unused Docker resources: `docker system prune`
- [ ] Verify backup integrity: Check backup files exist and aren't empty

### **Before Major Changes**
- [ ] Create backup: `./backup-whisperengine.sh`
- [ ] Test backup restoration (on copy of system)
- [ ] Document configuration changes
- [ ] Plan rollback procedure

### **After Updates**
- [ ] Verify all services started: `docker ps`
- [ ] Test web interface: Visit http://localhost:3001
- [ ] Test API: `curl http://localhost:9090/health`
- [ ] Check logs for errors: `docker-compose logs`
- [ ] Create post-update backup: `./backup-whisperengine.sh`

This guide covers the essential operations for managing your containerized WhisperEngine installation. Keep it handy and update it as you discover new solutions!