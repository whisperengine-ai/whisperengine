# WhisperEngine Docker Images

**Production-ready Docker images for WhisperEngine AI character platform with persistent memory and adaptive learning intelligence.**

## 🚀 Quick Start for End Users

**Don't use these Docker files directly!** End users should use our containerized setup scripts:

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

The setup script provides:
- ✅ **Web Interface** at http://localhost:3001 for character creation
- ✅ **Pre-built containers** from Docker Hub (no compilation required)
- ✅ **Database-based CDL** character system
- ✅ **Modern architecture** with all current services
- ✅ **Cross-platform support**

## �️ Docker Hub Tags

- `whisperengine/whisperengine:latest` - Latest stable release (recommended)
- `whisperengine/whisperengine:v1.x.x` - Specific version releases
- `whisperengine/whisperengine-web:latest` - Web interface container

## 🏗️ Docker Files in This Directory

### Production Images
- **`Dockerfile`** - Main production image for WhisperEngine bots
- **`Dockerfile.multi-stage`** - Multi-stage build for optimized production deployments
- **`.dockerignore`** - Build optimization (excludes unnecessary files)

### Configuration
- **`qdrant_config.yml`** - Qdrant vector database configuration

## 🎭 Current WhisperEngine Architecture

WhisperEngine uses a **modern multi-service architecture**:

### Core Services
- **🌐 Web Interface** - Character creation and management UI (port 3001)
- **🤖 AI Characters** - Multiple character bots with unique personalities
- **🔍 Qdrant** - Vector database for semantic memory (384D embeddings)
- **🐘 PostgreSQL** - CDL character definitions and user data
- **� InfluxDB** - Temporal intelligence metrics

### Character System
- **Database-based CDL** - Character Definition Language stored in PostgreSQL
- **Multi-character support** - Deploy multiple AI characters simultaneously
- **Persistent memory** - Each character remembers conversations independently
- **Adaptive learning** - Characters improve responses based on interactions

### Memory Intelligence
- **Vector-native memory** - Qdrant with 384D embeddings
- **Named vector system** - Content, emotion, semantic vectors (3D system)
- **Bot-specific collections** - Complete memory isolation between characters
- **RoBERTa emotion analysis** - Advanced emotional intelligence for every message

## 🔧 For Developers

### Building Images Locally
```bash
# Build main production image
docker build -f docker/Dockerfile -t whisperengine:local .

# Build multi-stage optimized image
docker build -f docker/Dockerfile.multi-stage --target production -t whisperengine:optimized .
```

### Multi-Platform Builds
```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -f docker/Dockerfile -t whisperengine:multiarch .
```

### Development Setup
For development, use the repository's multi-bot Docker Compose:
```bash
# Clone repository for development
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# Start development environment
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d elena-bot
```

## 📊 System Requirements

**Minimum:**
- 4GB RAM
- 2 CPU cores  
- 10GB disk space
- Docker & Docker Compose

**Recommended:**
- 8GB+ RAM
- 4+ CPU cores
- SSD storage
- 20GB+ free disk space

## 🔗 Links

- **📖 Main Repository**: https://github.com/whisperengine-ai/whisperengine
- **🐳 Docker Hub**: https://hub.docker.com/r/whisperengine/whisperengine
- **� Documentation**: See main repository docs/ folder
- **🐛 Issues**: https://github.com/whisperengine-ai/whisperengine/issues

## 📝 License

MIT License - See [LICENSE](https://github.com/whisperengine-ai/whisperengine/blob/main/LICENSE) for details.

---

**For end users**: Use the setup scripts, not these Docker files directly!  
**For developers**: Clone the repository for full development environment.