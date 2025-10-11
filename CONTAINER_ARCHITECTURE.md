# WhisperEngine Container Architecture

## 📦 Published Docker Hub Images

WhisperEngine uses **2 container images** on Docker Hub:

### 1. **Main Application Container** (`whisperengine/whisperengine`)

**Image**: `whisperengine/whisperengine:latest` or `whisperengine/whisperengine:v1.0.2`

**Contains**:
- ✅ Main WhisperEngine AI application
- ✅ HTTP Chat API server
- ✅ Discord bot capabilities (optional)
- ✅ Database migration scripts (`scripts/run_migrations.py`)
- ✅ Pre-downloaded AI models (~400MB)
  - FastEmbed: sentence-transformers/all-MiniLM-L6-v2
  - RoBERTa: cardiffnlp emotion analysis

**Used For**:
1. **Main bot application**: Run with default entrypoint
   ```bash
   docker run whisperengine/whisperengine:latest
   ```

2. **Database migrations**: Run with migration command
   ```bash
   docker run whisperengine/whisperengine:latest python /app/scripts/run_migrations.py
   ```

**Why Combined?**
- ✅ **Single source of truth**: Migrations always match application version
- ✅ **No version conflicts**: Migration scripts and app code stay in sync
- ✅ **Simpler deployment**: One container image to manage
- ✅ **Atomic updates**: Update migrations and app together

### 2. **Web UI Container** (`whisperengine/whisperengine-ui`)

**Image**: `whisperengine/whisperengine-ui:latest` or `whisperengine/whisperengine-ui:v1.0.2`

**Contains**:
- ✅ CDL Character Management interface
- ✅ Configuration management web UI
- ✅ Next.js production build
- ✅ Character creation and editing tools

**Used For**:
- Web-based character and configuration management
- User-friendly interface for non-technical users

---

## 🔧 How Migrations Work

### **Pattern**: Init Container with Main Image

WhisperEngine uses the **init container pattern** where migrations run before the main application starts, using the same container image:

```yaml
services:
  # Migration init container (runs once)
  db-migrate:
    image: whisperengine/whisperengine:latest
    command: ["python", "/app/scripts/run_migrations.py"]
    restart: "no"  # Only runs once
    depends_on:
      postgres:
        condition: service_healthy
  
  # Main application (runs continuously)
  whisperengine-assistant:
    image: whisperengine/whisperengine:latest
    depends_on:
      db-migrate:
        condition: service_completed_successfully
```

### **Benefits of This Pattern**:

1. **Version Consistency**:
   - Main app: `whisperengine:v1.0.2`
   - Migrations: `whisperengine:v1.0.2` (same image!)
   - ✅ Guaranteed compatibility

2. **No Separate Build**:
   - ❌ Don't need `whisperengine/migrations:latest`
   - ✅ Just use `whisperengine/whisperengine:latest` with different command

3. **Simpler CI/CD**:
   - Build once, use twice (migrations + app)
   - Single Docker Hub push
   - Single version tag to manage

4. **Development Match**:
   - Dev environment: `python scripts/run_migrations.py`
   - Production: `docker run whisperengine:latest python /app/scripts/run_migrations.py`
   - ✅ Identical execution

---

## 🏗️ Container Build Process

When you run `./push-to-dockerhub.sh whisperengine v1.0.2`, it builds **2 containers**:

### **Build 1: Main Application** 
```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t whisperengine/whisperengine:v1.0.2 \
  -t whisperengine/whisperengine:latest \
  -f Dockerfile \
  --push .
```

**Includes**:
- Application code
- Migration scripts (automatically included via `COPY scripts/`)
- Pre-downloaded models
- All dependencies

### **Build 2: Web UI**
```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t whisperengine/whisperengine-ui:v1.0.2 \
  -t whisperengine/whisperengine-ui:latest \
  -f cdl-web-ui/Dockerfile \
  --push ./cdl-web-ui
```

---

## ❓ FAQ

### **Q: Why not a separate migrations container?**

**A**: The main container already includes migration scripts. Using the same image:
- ✅ Ensures version compatibility (migrations match app version)
- ✅ Reduces build complexity (1 build instead of 2)
- ✅ Simplifies deployment (1 image to pull)
- ✅ Follows Docker best practices (init container pattern)

### **Q: How do I run migrations separately?**

**A**: Use the same main container with a different command:

```bash
# Development:
python scripts/run_migrations.py

# Docker:
docker run whisperengine/whisperengine:latest python /app/scripts/run_migrations.py

# Docker Compose (init container):
services:
  db-migrate:
    image: whisperengine/whisperengine:latest
    command: ["python", "/app/scripts/run_migrations.py"]
    restart: "no"
```

### **Q: Do migrations run automatically?**

**A**: Depends on deployment method:

- **Quick Start** (`docker-compose.quickstart.yml`): ✅ Yes, via init container
- **Manual Docker**: ❌ No, you must run migrations manually first
- **Development**: ❌ No, run `python scripts/run_migrations.py` manually

### **Q: What if migration scripts change?**

**A**: Pull the latest container image:

```bash
docker pull whisperengine/whisperengine:latest
```

The updated migration scripts are automatically included because they're part of the main image.

### **Q: Can I run migrations without pulling the full app?**

**A**: No, but that's intentional. The migration scripts are tightly coupled to the application code. Running them from the same image prevents version mismatches.

---

## 🚀 Multi-Platform Support

Both containers are built for **multi-platform support**:

✅ **linux/amd64** (Intel/AMD processors)  
✅ **linux/arm64** (ARM processors, Apple Silicon)

Users on any platform can pull and run the images:

```bash
# Works on any platform (Docker automatically pulls correct arch)
docker pull whisperengine/whisperengine:latest
docker pull whisperengine/whisperengine-ui:latest

# Or explicitly specify platform
docker pull --platform linux/amd64 whisperengine/whisperengine:latest
docker pull --platform linux/arm64 whisperengine/whisperengine:latest
```

---

## 📋 Summary

| Component | Image | Purpose | Multi-Platform |
|-----------|-------|---------|----------------|
| **Main App** | `whisperengine/whisperengine` | AI bot + HTTP API + migrations | ✅ AMD64 + ARM64 |
| **Web UI** | `whisperengine/whisperengine-ui` | Character management interface | ✅ AMD64 + ARM64 |
| **Migrations** | _(uses main app image)_ | Database schema updates | ✅ AMD64 + ARM64 |

**Total Published Images**: **2** (not 3 - migrations use main app image)

**Build Command**: `./push-to-dockerhub.sh whisperengine v1.0.2`

**Result**: Builds and pushes 2 multi-platform images to Docker Hub
