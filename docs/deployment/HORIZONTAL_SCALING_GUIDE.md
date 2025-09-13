# Discord Bot Horizontal Scaling with Sharding

## 🎯 Overview

This guide shows how to scale your Discord bot horizontally using Discord's sharding feature. Sharding allows you to run multiple bot instances that each handle a subset of Discord servers, enabling you to scale beyond the limits of a single instance.

## 🧠 How Discord Sharding Works

### Guild Distribution
Discord uses a simple formula to determine which shard handles each guild (server):
```
shard_id = (guild_id >> 22) % shard_count
```

This ensures guilds are evenly distributed across shards and always go to the same shard.

### Benefits of Sharding
- **Higher Capacity**: Handle more guilds and users than a single instance
- **Better Performance**: Distribute computational load across multiple processes
- **Improved Reliability**: If one shard fails, others continue working
- **Resource Scaling**: Scale horizontally across multiple servers/containers

## 🚀 Quick Start

### Method 1: Native Multi-Process (Recommended for Development)

1. **Start multiple shards locally:**
```bash
# Start all shards with the manager script
./shard_manager.sh start

# Or start individual shards manually
python main_sharded.py --shard-id 0 --shard-count 4 &
python main_sharded.py --shard-id 1 --shard-count 4 &
python main_sharded.py --shard-id 2 --shard-count 4 &
python main_sharded.py --shard-id 3 --shard-count 4 &
```

2. **Monitor shard status:**
```bash
./shard_manager.sh status
./shard_manager.sh monitor  # Real-time monitoring
```

### Method 2: Docker Compose (Recommended for Production)

1. **Configure environment:**
```bash
# Set your Discord bot token
export DISCORD_BOT_TOKEN="your_bot_token_here"

# Configure shard count (default: 4)
export DISCORD_SHARD_COUNT=4

# Set your LLM API endpoint
export LLM_CHAT_API_URL="https://openrouter.ai/api/v1"
export OPENROUTER_API_KEY="your_api_key"
```

2. **Start sharded deployment:**
```bash
docker-compose -f docker-compose.sharded.yml up -d
```

3. **Monitor shards:**
```bash
docker-compose -f docker-compose.sharded.yml logs -f bot-shard-0
docker-compose -f docker-compose.sharded.yml ps
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_SHARD_ID` | ID of this shard (0-based) | `0` |
| `DISCORD_SHARD_COUNT` | Total number of shards | `1` |
| `DISCORD_AUTO_SHARD` | Let Discord determine shard count | `false` |
| `DISCORD_HEARTBEAT_TIMEOUT` | Heartbeat timeout per shard | `60.0` |

### Determining Shard Count

**Small bots (< 1,000 guilds):**
- 1 shard (no sharding needed)

**Medium bots (1,000 - 10,000 guilds):**
- 2-4 shards
- `DISCORD_SHARD_COUNT=4`

**Large bots (10,000+ guilds):**
- 8+ shards
- Consider auto-sharding: `DISCORD_AUTO_SHARD=true`

**Discord's auto-sharding recommendation:**
- 1 shard per ~1,000 guilds
- Discord will suggest optimal shard count when your bot grows

## 🗃️ Data Architecture with Sharding

### Shared Infrastructure
All shards share the same backend services:
- **PostgreSQL**: User profiles and relational data
- **Redis**: Conversation caching and session data  
- **ChromaDB**: Vector embeddings and memories
- **Neo4j**: Graph relationships and contexts

### Shard-Specific Data
Each shard maintains isolated data:
- **Memory Collections**: `shard_0_user_memories`, `shard_1_user_memories`, etc.
- **Cache Keys**: Prefixed with shard ID to prevent conflicts
- **Log Files**: Separate log files per shard for debugging

### Cross-Shard Communication
Shards are independent but can share data through:
- **Global Facts**: Stored in shared PostgreSQL database
- **User Profiles**: Centralized user data across all shards
- **Backup Systems**: Consolidated backups from all shards

## 🔧 Advanced Configuration

### Custom Shard Assignment

```python
# For advanced users: custom shard assignment
from src.sharding.shard_manager import create_sharded_bot_instance

# Run specific shards on different servers
bot = create_sharded_bot_instance(
    command_prefix='!',
    intents=intents,
    total_shards=8,
    shard_ids=[0, 2, 4]  # This instance handles shards 0, 2, and 4
)
```

### Resource Optimization per Shard

```bash
# Different resource allocation per shard
export MEMORY_THREAD_POOL_SIZE=2  # Smaller for each shard
export CONVERSATION_CACHE_TIMEOUT=300  # Shorter cache for high-load shards
export CHROMADB_CONNECTION_POOL_SIZE=10  # Shared pool size
```

### Load Balancer Integration

```yaml
# nginx.conf for load balancing web interfaces
upstream bot_shards {
    server localhost:8081;  # Shard 0 web interface
    server localhost:8082;  # Shard 1 web interface  
    server localhost:8083;  # Shard 2 web interface
    server localhost:8084;  # Shard 3 web interface
}
```

## 📊 Monitoring and Management

### Shard Manager Commands

```bash
# Basic operations
./shard_manager.sh start           # Start all shards
./shard_manager.sh stop            # Stop all shards
./shard_manager.sh restart         # Restart all shards
./shard_manager.sh status          # Check shard status

# Monitoring
./shard_manager.sh monitor         # Real-time status monitoring
./shard_manager.sh logs 2          # View logs for shard 2
./shard_manager.sh auto-restart    # Auto-restart failed shards

# Custom shard counts
DISCORD_SHARD_COUNT=8 ./shard_manager.sh start
```

### Health Monitoring

Each shard provides health metrics:
- **Connection Status**: Connected, disconnected, ready
- **Guild Count**: Number of servers handled by this shard
- **User Count**: Approximate users on this shard
- **Memory Usage**: ChromaDB collections and Redis cache usage
- **Response Times**: LLM API latency and memory retrieval times

### Log Aggregation

```bash
# View all shard logs together
tail -f logs/shards/shard_*.log

# Search across all shard logs
grep "ERROR" logs/shards/shard_*.log

# Monitor specific events
grep "shard.*ready" logs/shards/shard_*.log
```

## 🚨 Troubleshooting

### Common Issues

**1. Shard assignment mismatch:**
```
Warning: Guild joined shard 2 but should be on shard 1
```
- **Cause**: Shard count changed after deployment
- **Fix**: Restart all shards with consistent `DISCORD_SHARD_COUNT`

**2. Database connection errors:**
```
Failed to connect to PostgreSQL from shard 3
```
- **Cause**: Database overwhelmed by multiple connections
- **Fix**: Increase `CHROMADB_CONNECTION_POOL_SIZE`, use connection pooling

**3. Memory conflicts:**
```
Collection 'user_memories' already exists with different schema
```
- **Cause**: Shards sharing same ChromaDB collections
- **Fix**: Ensure `ShardedMemoryManager` is properly configured

### Performance Optimization

**High Memory Usage:**
```bash
# Reduce per-shard cache size
export CONVERSATION_CACHE_MAX_LOCAL=25  # Reduced from 50
export CONVERSATION_CACHE_TIMEOUT=5     # Reduced from 15 minutes
```

**High CPU Usage:**
```bash
# Reduce thread pools per shard
export MEMORY_THREAD_POOL_SIZE=2   # Reduced from 4
export IMAGE_THREAD_POOL_SIZE=1    # Reduced from 2
```

**Database Contention:**
```bash
# Stagger shard startup to reduce initial load
./shard_manager.sh start &
sleep 10
# Additional shards start with delay
```

## 🎯 Production Deployment

### Kubernetes Deployment

```yaml
# k8s-sharded-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whisperengine-shards
spec:
  replicas: 4
  selector:
    matchLabels:
      app: discord-bot
  template:
    metadata:
      labels:
        app: discord-bot
    spec:
      containers:
      - name: bot-shard
        image: your-registry/discord-bot:latest
        env:
        - name: DISCORD_SHARD_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.annotations['shard-id']
        - name: DISCORD_SHARD_COUNT
          value: "4"
        - name: DISCORD_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: discord-secrets
              key: bot-token
```

### Auto-Scaling Considerations

**When to add shards:**
- Bot reaches 1,000+ guilds per shard
- Response times increase significantly
- Memory usage consistently high
- Rate limiting becomes frequent

**When to use Discord auto-sharding:**
- Your bot is in 10,000+ guilds
- You want Discord to manage optimal shard count
- You're hitting Discord's gateway limits

## 📈 Performance Metrics

### Expected Improvements with Sharding

| Metric | Single Instance | 4 Shards | 8 Shards |
|--------|----------------|----------|----------|
| **Max Guilds** | ~2,500 | ~10,000 | ~20,000 |
| **Response Time** | 2-5s | 1-3s | 1-2s |
| **Memory Usage** | 2-4GB | 1-2GB per shard | 0.5-1GB per shard |
| **Concurrent Users** | ~5,000 | ~20,000 | ~40,000 |

### Monitoring Dashboards

The included monitoring service (`shard-monitor`) provides:
- Real-time shard status
- Guild distribution visualization
- Performance metrics per shard
- Alert system for failed shards

Access at: `http://localhost:8080` (when using Docker Compose)

## 🔗 Integration with Existing Features

All existing bot features work with sharding:
- ✅ **Memory System**: Automatically partitioned by shard
- ✅ **Voice Commands**: Each shard handles its assigned guilds
- ✅ **Privacy Controls**: Per-user settings work across shards
- ✅ **Backup System**: Consolidated backups from all shards
- ✅ **Admin Commands**: Work on the shard where admin is present
- ✅ **Multi-Bot Setup**: Can combine with Aetheris/Dream configuration

## 🚀 Next Steps

1. **Start with 2-4 shards** to test the system
2. **Monitor performance** and adjust shard count as needed
3. **Implement auto-scaling** based on guild growth
4. **Consider geographic distribution** for global bots
5. **Set up monitoring alerts** for production deployment

Your bot is now ready for horizontal scaling! 🎉
