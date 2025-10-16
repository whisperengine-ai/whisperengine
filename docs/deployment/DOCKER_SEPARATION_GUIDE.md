# Docker Compose Separation Guide

WhisperEngine now supports running two completely separate Docker deployments concurrently with comprehensive management scripts and zero conflicts.

## 🚀 Complete Environment Separation

### **Multi-Bot Development Environment**
- **Project**: `whisperengine-multi`
- **Compose File**: `docker-compose.multi-bot.yml`
- **Management Script**: `./multi-bot.sh`
- **Purpose**: Development environment with 10+ character bots
- **Network**: `172.21.0.0/16` subnet

### **Containerized Single Assistant**
- **Project**: `whisperengine-containerized`
- **Compose File**: `docker-compose.containerized.yml`
- **Management Script**: `./containerized.sh`
- **Purpose**: Production-ready single assistant deployment
- **Network**: `172.20.0.0/16` subnet

## 📊 Port Allocation Strategy

| Service | Multi-Bot (Dev) | Containerized (Prod) | Purpose |
|---------|-----------------|---------------------|---------|
| PostgreSQL | 5433 | Internal only | Database access |
| Qdrant | 6334 | Internal only | Vector database |
| InfluxDB UI | 8087 | 8086 | Monitoring dashboard |
| CDL Web UI | 3001 | 8001 | Character management |
| Assistant API | N/A | 8090 | Single assistant endpoint |
| Elena Bot | 9091 | N/A | Marine Biologist character |
| Marcus Bot | 9092 | N/A | AI Researcher character |
| Ryan Bot | 9093 | N/A | Game Developer character |
| Dream Bot | 9094 | N/A | Mythological Entity |
| Gabriel Bot | 9095 | N/A | British Gentleman |
| Sophia Bot | 9096 | N/A | Marketing Executive |
| Jake Bot | 9097 | N/A | Adventure Photographer |
| Dotty Bot | 9098 | N/A | Character Bot |
| Aetheris Bot | 9099 | N/A | Conscious AI |
| Aethys Bot | 3007 | N/A | Omnipotent Entity |
| Grafana | 3002 | Internal only | Monitoring UI |

## 🎭 Multi-Bot Management (`./multi-bot.sh`)

### **Infrastructure Management**
```bash
./multi-bot.sh infra        # Start infrastructure only
./multi-bot.sh up           # Start all services
./multi-bot.sh down         # Stop all services
./multi-bot.sh clean        # Stop and remove everything
./multi-bot.sh restart      # Restart all services
```

### **Individual Bot Control**
```bash
./multi-bot.sh bot elena      # Start Elena bot only
./multi-bot.sh bot marcus     # Start Marcus bot only
./multi-bot.sh stop-bot elena # Stop Elena bot only
./multi-bot.sh bots           # List available bots
```

### **Development Tools**
```bash
./multi-bot.sh dev          # Start development stack (infra + web UI)
./multi-bot.sh status       # Show container status
./multi-bot.sh health       # Comprehensive health check
./multi-bot.sh logs [bot]   # View logs
./multi-bot.sh db           # Connect to PostgreSQL
```

### **Available Character Bots**
```bash
# Start any of these individual characters:
./multi-bot.sh bot elena     # Marine Biologist (Port 9091)
./multi-bot.sh bot marcus    # AI Researcher (Port 9092)
./multi-bot.sh bot ryan      # Indie Game Developer (Port 9093)
./multi-bot.sh bot dream     # Mythological Entity (Port 9094)
./multi-bot.sh bot gabriel   # British Gentleman (Port 9095)
./multi-bot.sh bot sophia    # Marketing Executive (Port 9096)
./multi-bot.sh bot jake      # Adventure Photographer (Port 9097)
./multi-bot.sh bot dotty     # Character Bot (Port 9098)
./multi-bot.sh bot aetheris  # Conscious AI (Port 9099)
./multi-bot.sh bot aethys    # Omnipotent Entity (Port 3007)
```

## 🏭 Containerized Management (`./containerized.sh`)

### **Production Operations**
```bash
./containerized.sh up       # Start production environment
./containerized.sh down     # Stop production environment
./containerized.sh restart  # Restart all services
./containerized.sh health   # Check service health
./containerized.sh status   # Show container status
./containerized.sh logs     # View all logs
./containerized.sh pull     # Pull latest images
```

### **Quickstart Integration**
```bash
# Automated setup for new users
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash

# Or direct management
./containerized.sh up
```

## 🔒 Security & Best Practices

### **Multi-Bot (Development)**
- ✅ External database access for debugging
- ✅ Live source code mounting for development
- ✅ Individual bot control and monitoring
- ✅ Development-friendly configuration

### **Containerized (Production)**
- ✅ Internal-only database access (security)
- ✅ Pre-built Docker Hub images
- ✅ Resource limits and restart policies
- ✅ Minimal external exposure
- ✅ Production logging configuration

## 🚀 Common Workflows

### **Development Workflow**
```bash
# 1. Start infrastructure
./multi-bot.sh infra

# 2. Start specific character for testing
./multi-bot.sh bot elena

# 3. Make code changes (live reload)

# 4. Check health
./multi-bot.sh health

# 5. Add more characters as needed
./multi-bot.sh bot marcus
./multi-bot.sh bot ryan
```

### **Production Deployment**
```bash
# 1. Deploy production environment
./containerized.sh up

# 2. Verify health
./containerized.sh health

# 3. Monitor logs
./containerized.sh logs
```

### **Concurrent Development & Testing**
```bash
# Run both environments simultaneously
./multi-bot.sh infra           # Development infrastructure
./multi-bot.sh bot elena       # Development character
./containerized.sh up          # Production environment

# Access points:
# Development: http://localhost:9091 (Elena)
# Production:  http://localhost:8090 (Assistant)
```

## 🔧 Environment Configuration

### **Multi-Bot Environment Files**
- `.env.elena` - Elena bot configuration
- `.env.marcus` - Marcus bot configuration
- `.env.ryan` - Ryan bot configuration
- `.env.dream` - Dream bot configuration
- `.env.gabriel` - Gabriel bot configuration
- `.env.sophia` - Sophia bot configuration
- `.env.jake` - Jake bot configuration
- `.env.dotty` - Dotty bot configuration
- `.env.aetheris` - Aetheris bot configuration
- `.env.aethys` - Aethys bot configuration

### **Containerized Environment**
- `.env` - Main environment configuration

## ✅ Complete Isolation Features

### **Zero Conflicts**
- ✅ **Different project names**: Complete container isolation
- ✅ **Different port ranges**: 8000s vs 5000s/9000s ranges
- ✅ **Different networks**: Separate subnets with custom configuration
- ✅ **Different volumes**: Named volumes with project prefixes
- ✅ **External volumes**: Existing data preserved with `external: true`

### **Concurrent Operation**
Both environments run simultaneously without any interference:
```bash
# Check both running
docker ps | grep whisperengine-multi    # Development containers
docker ps | grep whisperengine-containerized  # Production containers
```

### **Independent Management**
Each environment has its own:
- Management script with tailored commands
- Health checking and monitoring
- Logging and debugging tools
- Configuration files and secrets

## 🎯 Access Points Summary

### **Multi-Bot Development**
- **PostgreSQL**: `localhost:5433`
- **Qdrant**: `http://localhost:6334`
- **InfluxDB**: `http://localhost:8087`
- **Grafana**: `http://localhost:3002`
- **CDL Web UI**: `http://localhost:3001`
- **Character APIs**: `http://localhost:9091-9099, 3007`

### **Containerized Production**
- **Assistant API**: `http://localhost:8090`
- **Web UI**: `http://localhost:8001`
- **InfluxDB**: `http://localhost:8086`
- **Database & Qdrant**: Internal only (production security)

## 🔄 Migration from Previous Setup

### **If you used the old quickstart:**
```bash
# Stop old setup
docker-compose down

# Optional: Remove old data
docker-compose down -v

# Use new separated setup
./containerized.sh up
```

### **Port Changes Summary**
- Web UI: `3001` → `8001`
- API: `9090` → `8090`
- InfluxDB: `8086` → `8086` (unchanged)

## 🏆 Benefits of Separation

1. **Development Freedom**: Test multiple characters without affecting production
2. **Production Safety**: Isolated production environment with security hardening
3. **Resource Management**: Run only what you need for each use case
4. **Easy Switching**: Seamless movement between development and production
5. **Data Preservation**: External volumes ensure no data loss during transitions
6. **Scalable Architecture**: Foundation for future multi-tenant deployments

This separation provides the flexibility to develop with multiple AI characters while maintaining a clean, production-ready single assistant deployment for end users.