# WhisperEngine Backup System Guide

A comprehensive, user-friendly backup solution for all WhisperEngine data including PostgreSQL, Redis, ChromaDB, and Neo4j datastores.

## 🎯 Quick Start

### Create Your First Backup
```bash
# Start WhisperEngine services
./bot.sh start

# Create a backup
./bot.sh backup create
```

### View Available Backups
```bash
./bot.sh backup list
```

### Restore from Backup
```bash
./bot.sh backup restore TIMESTAMP
# Example: ./bot.sh backup restore 20240912_143022
```

## 📋 Complete Command Reference

### Basic Backup Operations

#### Create Backup
```bash
./bot.sh backup create
```
- Backs up all 4 datastores: PostgreSQL, Redis, ChromaDB, Neo4j
- Creates timestamped backup directory in `./backups/`
- Includes metadata file with backup information
- Shows backup size and completion status

#### List Backups
```bash
./bot.sh backup list
```
- Shows all available backups with timestamps
- Displays backup size and creation date
- Shows which services were successfully backed up
- Provides restore commands for each backup

#### Restore Data
```bash
./bot.sh backup restore TIMESTAMP
```
- Restores all data from specified backup
- Asks for confirmation before proceeding
- Handles service restart automatically
- Shows progress for each datastore

#### Cleanup Old Backups
```bash
./bot.sh backup cleanup [DAYS]
```
- Removes backups older than specified days (default: 30)
- Shows size freed up
- Preserves recent backups automatically

### Automated Backup Scheduling

#### Install Automated Backups
```bash
# Daily backups at 2 AM (default)
./scripts/backup_scheduler.sh install daily

# Weekly backups on Sunday at 2 AM
./scripts/backup_scheduler.sh install weekly

# Monthly backups on 1st at 2 AM
./scripts/backup_scheduler.sh install monthly

# Custom schedule (every 6 hours)
./scripts/backup_scheduler.sh install "0 */6 * * *"
```

#### Check Automation Status
```bash
./scripts/backup_scheduler.sh status
```

#### Remove Automation
```bash
./scripts/backup_scheduler.sh uninstall
```

#### Manual Trigger
```bash
./scripts/backup_scheduler.sh trigger
```

## 🗂️ What Gets Backed Up

### PostgreSQL Database
- **File**: `postgresql_backup.sql`
- **Content**: User profiles, persistent data, system settings
- **Method**: Complete database dump using `pg_dumpall`
- **Size**: Typically small (< 10MB for most setups)

### Redis Cache
- **File**: `redis_backup.rdb`
- **Content**: Conversation cache, session state, temporary data
- **Method**: Background save + RDB file copy
- **Size**: Varies based on conversation history

### ChromaDB Vector Store
- **File**: `chromadb_backup.tar.gz`
- **Content**: Vector embeddings, semantic memory, collections
- **Method**: Compressed archive of data directory
- **Size**: Can be large depending on memory usage

### Neo4j Graph Database
- **File**: `neo4j_backup.tar.gz`
- **Content**: Relationship graphs, user connections, graph data
- **Method**: Compressed archive of data directory
- **Size**: Grows with relationship complexity

## 📁 Backup Structure

```
backups/
└── whisperengine_backup_YYYYMMDD_HHMMSS/
    ├── backup_info.txt          # Backup metadata
    ├── postgresql_backup.sql    # PostgreSQL dump
    ├── redis_backup.rdb         # Redis database
    ├── chromadb_backup.tar.gz   # ChromaDB vectors
    └── neo4j_backup.tar.gz      # Neo4j graph data
```

### Backup Metadata Example
```
WhisperEngine Backup Information
================================
Backup Date: Thu Sep 12 14:30:22 PDT 2024
Backup Directory: ./backups/whisperengine_backup_20240912_143022
Backup Type: Full System Backup

Services Backed Up:
✅ postgresql: postgresql_backup.sql (2.1M)
✅ redis: redis_backup.rdb (156K)
✅ chromadb: chromadb_backup.tar.gz (45M)
✅ neo4j: neo4j_backup.tar.gz (12M)
```

## 🔧 Advanced Usage

### Custom Backup Directory
```bash
# Set custom backup location
export BACKUP_DIR="/path/to/custom/backup/location"
./bot.sh backup create
```

### Partial Service Backup
The backup system automatically detects which services are running and backs up only available services. This means:
- If only some services are running, only those will be backed up
- Missing services are skipped with warnings
- Restore operations handle partial backups gracefully

### Backup Size Management
```bash
# Check total backup space usage
du -sh backups/

# Remove backups older than 7 days
./bot.sh backup cleanup 7

# Remove specific backup
rm -rf backups/whisperengine_backup_TIMESTAMP
```

## 🚨 Important Safety Notes

### Before Restoration
- ⚠️ **Restoration replaces ALL current data**
- 🛑 **Always create a backup before restoring**
- 🔄 **Services are automatically restarted during restore**
- ✅ **Confirmation prompt prevents accidental restoration**

### Data Consistency
- Backups are point-in-time snapshots
- For best consistency, create backups during low activity
- Services continue running during backup (hot backup)
- Restoration requires service restarts

### Storage Requirements
- Plan for backup growth over time
- ChromaDB backups can become large with extensive memory
- Regular cleanup prevents disk space issues
- Consider external backup storage for long-term retention

## 🔍 Troubleshooting

### Common Issues

#### "Docker not running"
```bash
# Start Docker Desktop or Docker service
docker info
./bot.sh start
```

#### "No containers are running"
```bash
# Start WhisperEngine services first
./bot.sh start
./bot.sh backup create
```

#### "PostgreSQL backup failed"
```bash
# Check PostgreSQL health
./bot.sh logs postgres
./bot.sh status
```

#### "Backup script not found"
```bash
# Ensure you're in the project root directory
cd /path/to/whisperengine
./bot.sh backup create
```

### Restore Issues

#### "Redis failed to start after restore"
```bash
# Restart Redis manually
./bot.sh restart
```

#### "ChromaDB not accessible after restore"
```bash
# Check ChromaDB logs
./bot.sh logs chromadb
# Restart if needed
./bot.sh restart
```

### Verification After Restore
```bash
# Check all services are healthy
./bot.sh status

# Verify data accessibility
./scripts/health_check.sh
```

## 🎛️ Automation Best Practices

### Recommended Schedules
- **Development**: Daily backups, 7-day retention
- **Production**: Daily backups, 30-day retention
- **Heavy usage**: Multiple daily backups, 14-day retention

### Monitoring Automated Backups
```bash
# Check automation status
./scripts/backup_scheduler.sh status

# View recent cron activity
tail -f /var/log/cron.log  # Linux
tail -f /var/log/system.log | grep cron  # macOS
```

### Backup Validation
```bash
# List recent backups to verify automation
./bot.sh backup list | head -10

# Check backup sizes for consistency
ls -lah backups/ | tail -5
```

## 💡 Tips and Best Practices

### Regular Maintenance
1. **Weekly**: Check backup automation status
2. **Monthly**: Review and cleanup old backups
3. **Quarterly**: Test restore procedures

### Before Major Changes
```bash
# Create backup before updates
./bot.sh backup create
# Proceed with updates...
```

### Testing Restores
```bash
# Test restore in development environment
cp -r backups/whisperengine_backup_TIMESTAMP test_restore/
# Test restore process...
```

### Monitoring Disk Usage
```bash
# Check backup directory size
du -sh backups/

# Monitor overall disk usage
df -h
```

## 🔗 Integration with Development Workflow

### Before Code Updates
```bash
./bot.sh backup create
git pull origin main
./bot.sh restart
```

### Before Configuration Changes
```bash
./bot.sh backup create
# Edit .env or config files
./bot.sh restart
```

### After Major Features
```bash
# Test new features
./bot.sh backup create  # Backup successful state
```

## 📞 Support and Maintenance

### Getting Help
- Check this documentation first
- Review troubleshooting section
- Check Docker and service logs
- Verify all services are running

### Manual Backup Commands
If the integrated backup system isn't available, you can manually backup individual services:

```bash
# PostgreSQL
docker-compose exec postgres pg_dumpall -U whisperengine > manual_postgres_backup.sql

# Redis
docker-compose exec redis redis-cli BGSAVE
docker-compose exec redis cat /data/dump.rdb > manual_redis_backup.rdb

# ChromaDB
docker-compose exec chromadb tar czf - /chroma/chroma > manual_chromadb_backup.tar.gz

# Neo4j
docker-compose exec neo4j tar czf - /data > manual_neo4j_backup.tar.gz
```

Remember: The integrated backup system handles service coordination, error checking, and metadata creation automatically!

---

*This backup system is designed to be simple, reliable, and user-friendly for both desktop/laptop installations and server deployments of WhisperEngine.*