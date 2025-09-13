# 🏗️ Build Guide - Discord AI Bot

This document provides comprehensive instructions for building the Discord AI Bot container images for different environments and deployment scenarios.

## 📋 Table of Contents

- [Overview](#overview)
- [Build Targets](#build-targets)
- [Prerequisites](#prerequisites)
- [Quick Build Commands](#quick-build-commands)
- [Detailed Build Instructions](#detailed-build-instructions)
- [Build Optimization](#build-optimization)
- [Troubleshooting](#troubleshooting)
- [CI/CD Integration](#cicd-integration)

---

## 🎯 Overview

The Discord AI Bot uses Docker for containerized deployment with multiple build configurations and external datastores:

- **Universal Dockerfile** (`docker/Dockerfile`) - Single-stage optimized build
- **Multi-stage Dockerfile** (`docker/Dockerfile.multi-stage`) - Development, production, and minimal builds
- **Docker Compose** configurations for different environments
- **External Datastores** - ChromaDB, PostgreSQL, and Redis services

### Project Structure
```
whisper-engine/
├── docker/
│   ├── Dockerfile                 # Universal build (recommended)
│   ├── Dockerfile.multi-stage     # Multi-stage builds
│   └── scripts/
├── docker-compose.yml             # Development/Universal
├── docker-compose.prod.yml        # Production optimized
├── docker-compose.dev.yml         # Development with hot-reload
├── requirements.txt               # Python dependencies
└── External Services:
    ├── ChromaDB (vector database)
    ├── PostgreSQL (relational database)
    └── Redis (caching layer)
```

---

## 🎪 Build Targets

### 1. **Universal Build** (Recommended)
- **File**: `docker/Dockerfile`
- **Use Case**: General purpose, production-ready
- **Size**: ~800MB
- **Features**: All dependencies, optimized layers

### 2. **Production Build** (Multi-stage)
- **File**: `docker/Dockerfile.multi-stage` (target: `production`)
- **Use Case**: Production deployment with resource limits
- **Size**: ~750MB
- **Features**: Minimal dependencies, security hardened

### 3. **Development Build** (Multi-stage)
- **File**: `docker/Dockerfile.multi-stage` (target: `development`)
- **Use Case**: Development with hot-reload and debugging tools
- **Size**: ~900MB
- **Features**: Development dependencies, debugging tools

### 4. **Minimal Build** (Multi-stage)
- **File**: `docker/Dockerfile.multi-stage` (target: `minimal`)
- **Use Case**: Lightweight deployment (Alpine-based)
- **Size**: ~400MB
- **Features**: Essential dependencies only

---

## ✅ Prerequisites

### System Requirements
- **Docker**: 20.10+ (with BuildKit support)
- **Docker Compose**: 2.0+
- **Memory**: 2GB+ available for builds
- **Storage**: 5GB+ free disk space

### Verify Installation
```bash
# Check Docker version
docker --version
docker compose version

# Verify BuildKit is enabled (optional but recommended)
export DOCKER_BUILDKIT=1
```

### Environment Files
Ensure you have the appropriate environment file:
```bash
# For development builds
cp .env.example .env

# For production builds  
cp .env.production .env

# For minimal setups
cp .env.minimal .env
```

---

## ⚡ Quick Build Commands

### Using Docker Compose (Recommended)

```bash
# Universal build (development/production)
docker compose build

# Production optimized build
docker compose -f docker-compose.prod.yml build

# Development build with hot-reload
docker compose -f docker-compose.dev.yml build

# Force rebuild without cache
docker compose build --no-cache
```

### Using Docker Build Directly

```bash
# Universal build (recommended)
docker build -f docker/Dockerfile -t discord-bot:latest .

# Production build (multi-stage)
docker build -f docker/Dockerfile.multi-stage --target production -t discord-bot:prod .

# Development build (multi-stage)
docker build -f docker/Dockerfile.multi-stage --target development -t discord-bot:dev .

# Minimal build (smallest size)
docker build -f docker/Dockerfile.multi-stage --target minimal -t discord-bot:minimal .
```

### Using Management Scripts

```bash
# Build and start (Unix/Linux/macOS)
./bot.sh build    # Build image
./bot.sh start    # Build and start in production mode

# Windows PowerShell
.\bot-manager.ps1 build
.\bot-manager.ps1 start
```

---

## �️ External Datastore Configuration

The Discord AI Bot now uses external datastores instead of local volume mounts:

### Required External Services

| Service | Purpose | Default Connection |
|---------|---------|-------------------|
| **ChromaDB** | Vector database for embeddings | `CHROMADB_HOST:8000` |
| **PostgreSQL** | Relational database for structured data | `POSTGRES_HOST:5432` |
| **Redis** | Caching and session storage | `REDIS_HOST:6379` |

### Environment Configuration

```bash
# Database connections (required)
CHROMADB_HOST=your-chromadb-server.com
CHROMADB_PORT=8000

POSTGRES_HOST=your-postgres-server.com  
POSTGRES_PORT=5432
POSTGRES_DB=discord_bot
POSTGRES_USER=bot_user
POSTGRES_PASSWORD=your-secure-password

REDIS_HOST=your-redis-server.com
REDIS_PORT=6379
REDIS_DB=0
```

### Benefits of External Datastores

- ✅ **Scalability**: Independent scaling of compute and storage
- ✅ **Persistence**: Data survives container restarts/rebuilds
- ✅ **Performance**: Dedicated database resources
- ✅ **Backup**: Managed database backup solutions
- ✅ **Multi-instance**: Multiple bot instances can share data

---

## �🔧 Detailed Build Instructions

### 1. Universal Build Process

The universal build (`docker/Dockerfile`) is the recommended approach:

```bash
# Step 1: Clone and navigate
git clone https://github.com/theRealMarkCastillo/whisper-engine
cd whisper-engine

# Step 2: Configure environment
cp .env.example .env
nano .env  # Edit configuration

# Step 3: Build image
docker build -f docker/Dockerfile -t discord-bot:latest .

# Step 4: Verify build
docker images discord-bot
```

### 2. Multi-stage Production Build

For production deployments with optimization:

```bash
# Build production target
docker build \
  -f docker/Dockerfile.multi-stage \
  --target production \
  -t discord-bot:prod-v1.0.0 \
  --build-arg VERSION=v1.0.0 \
  .

# Tag for registry
docker tag discord-bot:prod-v1.0.0 your-registry.com/discord-bot:v1.0.0

# Push to registry
docker push your-registry.com/discord-bot:v1.0.0
```

### 3. Development Build with Hot-Reload

For development with live code editing:

```bash
# Build development target
docker build \
  -f docker/Dockerfile.multi-stage \
  --target development \
  -t discord-bot:dev \
  .

# Start development environment with external datastores
docker compose -f docker-compose.dev.yml up -d
```

### 4. Minimal Alpine Build  

For resource-constrained environments:

```bash
# Build minimal Alpine-based image
docker build \
  -f docker/Dockerfile.multi-stage \
  --target minimal \
  -t discord-bot:minimal \
  .

# Verify size reduction
docker images discord-bot
```

---

## 🚀 Build Optimization

### Layer Caching Strategy

The Dockerfiles are optimized for build caching:

1. **System dependencies** installed first (rarely change)
2. **Requirements.txt** copied before source code (dependencies cache)
3. **Source code** copied last (frequently changed)

### Build Arguments

Available build arguments for customization:

```bash
# Version tagging
docker build --build-arg VERSION=v1.2.3 -t discord-bot:v1.2.3 .

# Python version override
docker build --build-arg PYTHON_VERSION=3.13-slim -t discord-bot:py313 .

# Custom requirements file
docker build --build-arg REQUIREMENTS_FILE=requirements-gpu.txt -t discord-bot:gpu .
```

### Multi-platform Builds

Build for multiple architectures:

```bash
# Create buildx builder
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile \
  -t discord-bot:multiarch \
  --push \
  .
```

### Build Performance Tips

```bash
# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1

# Use build cache mount for pip dependencies
docker build --mount=type=cache,target=/root/.cache/pip -t discord-bot .

# Parallel builds with docker compose
docker compose build --parallel

# Build only the bot service (skip datastores if they're external)
docker compose build discord-bot
```

---

## 🛠️ Build Configurations

### Environment-Specific Builds

#### Development Configuration
```bash
# Build with development dependencies
docker compose -f docker-compose.dev.yml build

# Features:
# - Hot-reload enabled
# - Debug tools included
# - Development dependencies
# - External datastore connections (ChromaDB, PostgreSQL)
```

#### Production Configuration  
```bash
# Build optimized for production
docker compose -f docker-compose.prod.yml build

# Features:
# - Minimal dependencies only
# - Security hardened
# - Resource limits configured
# - Health checks enabled
# - Non-root user
# - External datastore connections (ChromaDB, PostgreSQL, Redis)
```

#### Minimal Configuration
```bash
# Build smallest possible image
docker build -f docker/Dockerfile.multi-stage --target minimal -t discord-bot:minimal .

# Features:
# - Alpine Linux base (~400MB vs ~800MB)
# - Essential dependencies only
# - Optimized for resource constraints
```

---

## 🔍 Troubleshooting

### Common Build Issues

#### 1. **Out of Disk Space**
```bash
# Clean up Docker resources
docker system prune -a

# Remove unused images
docker image prune -a

# Check disk usage
docker system df
```

#### 2. **Build Cache Issues**
```bash
# Force rebuild without cache
docker build --no-cache -f docker/Dockerfile -t discord-bot .

# Clear build cache
docker builder prune
```

#### 3. **Dependency Installation Failures**
```bash
# Check requirements.txt format
cat requirements.txt

# Test requirements installation locally
pip install -r requirements.txt

# Build with verbose output
docker build --progress=plain -f docker/Dockerfile -t discord-bot .
```

#### 4. **Platform Compatibility Issues**
```bash
# Force specific platform
docker build --platform linux/amd64 -f docker/Dockerfile -t discord-bot .

# Check current platform
docker version | grep -A 5 "Server:"
```

### Build Validation

#### Test Built Image
```bash
# Run configuration validation
docker run --rm discord-bot:latest python validate_config.py

# Test container startup
docker run --rm -e DISCORD_BOT_TOKEN=test discord-bot:latest python -c "print('Build successful')"

# Check image layers
docker history discord-bot:latest
```

#### Security Scan
```bash
# Scan for vulnerabilities (if available)
docker scan discord-bot:latest

#### Security Validation
```bash
# Scan for vulnerabilities (if available)
docker scan discord-bot:latest

# Verify no sensitive data in image
docker run --rm -it discord-bot:latest find /app -name "*.env*" -o -name "*key*"

# Test external datastore connections
docker run --rm -e DISCORD_BOT_TOKEN=test 
  -e CHROMADB_HOST=your-chromadb-host 
  -e POSTGRES_HOST=your-postgres-host 
  discord-bot:latest python -c "print('External connections configured')"
```

docker run --rm -it discord-bot:latest find /app -name "*.env*" -o -name "*key*"
```

---

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./docker/Dockerfile
        platforms: linux/amd64,linux/arm64
        push: true
        tags: |
          ghcr.io/${{ github.repository }}:latest
          ghcr.io/${{ github.repository }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

### Automated Testing

```bash
# Build test script
#!/bin/bash
set -e

echo "Building all targets..."
docker build -f docker/Dockerfile -t discord-bot:universal .
docker build -f docker/Dockerfile.multi-stage --target production -t discord-bot:prod .
docker build -f docker/Dockerfile.multi-stage --target minimal -t discord-bot:minimal .

echo "Testing builds..."
docker run --rm discord-bot:universal python --version
docker run --rm discord-bot:prod python --version  
docker run --rm discord-bot:minimal python --version

echo "All builds successful!"
```

---

## 📊 Build Comparison

| Build Type | Size | Build Time | Use Case | Features |
|------------|------|------------|----------|----------|
| **Universal** | ~800MB | 3-5 min | General use | Full featured, optimized |
| **Production** | ~750MB | 4-6 min | Production deploy | Security hardened, minimal |
| **Development** | ~900MB | 4-7 min | Development | Debug tools, hot-reload |
| **Minimal** | ~400MB | 2-4 min | Resource constrained | Alpine-based, essential only |

---

## 📝 Build Checklist

Before building:
- [ ] Docker and Docker Compose installed
- [ ] Environment file configured (`.env`)
- [ ] External datastores configured (ChromaDB, PostgreSQL, Redis)
- [ ] Network connectivity to external services verified
- [ ] Sufficient disk space (5GB+)
- [ ] Network access for dependency downloads

After building:
- [ ] Image built successfully
- [ ] Configuration validation passes
- [ ] Container starts without errors
- [ ] External datastore connections established
- [ ] Health checks pass (if configured)
- [ ] Application logs show successful initialization

---

## 🆘 Support

If you encounter build issues:

1. **Check logs**: `docker build` output for error details
2. **Verify environment**: Ensure all required environment variables are set
3. **Clean rebuild**: Use `--no-cache` flag to force clean build
4. **Check resources**: Ensure sufficient disk space and memory
5. **Update dependencies**: Verify all system requirements are met

For additional help, see:
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development workflow
- [README.md](README.md) - General setup instructions
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and solutions

---

*Last updated: September 10, 2025*
*Version: 1.0.0*
