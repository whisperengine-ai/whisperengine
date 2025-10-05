# 🚀 GitHub Actions Docker Hub Setup

This guide helps you set up automated Docker Hub publishing for WhisperEngine.

## 📋 Prerequisites

1. **Docker Hub Account**: Create at https://hub.docker.com
2. **Docker Hub Repository**: Create `whisperengine/whisperengine` repository  
3. **GitHub Repository**: Admin access to configure secrets

## 🔧 Quick Setup

### Step 1: Create Docker Hub Access Token

1. Go to Docker Hub → Account Settings → Security
2. Click "New Access Token"  
3. Name: `GitHub Actions WhisperEngine`
4. Permissions: `Read, Write, Delete`
5. Copy the generated token

### Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these **Repository Secrets** (supports both naming conventions):

**Option 1: Standard Docker Hub naming:**
| Secret Name | Value | Description |
|-------------|-------|-------------|  
| `DOCKERHUB_USERNAME` | `whisperengine` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | `dckr_pat_xxx...` | Access token from Step 1 |

**Option 2: Legacy Docker naming:**
| Secret Name | Value | Description |
|-------------|-------|-------------|  
| `DOCKER_USERNAME` | `whisperengine` | Your Docker Hub username |
| `DOCKER_PASSWORD` | `dckr_pat_xxx...` | Access token from Step 1 |

> ℹ️ **Note**: The workflow supports both naming conventions. Use whichever matches your existing secrets.

### Step 3: Test the Setup

1. **Manual Test**: Go to Actions → "🐳 Docker Build and Push" → "Run workflow"
2. **Automatic Test**: Push to `main` branch or create a tag like `v1.0.0`

## 🎯 What Gets Built

### Model Download Strategy

**🚀 Release Images (Tagged Versions):**
- ✅ **Models pre-downloaded** during build
- ✅ **Instant startup** - no waiting for downloads
- ✅ **Production ready** - works offline
- ⚠️ **Larger image size** (~500MB-1GB vs ~200MB)

**🔧 Development Images (main, branches):**
- ❌ **No models included** in image
- ⚠️ **First run delay** - downloads models (~2-5 minutes)
- ✅ **Faster builds** - no model download time
- ✅ **Smaller images** - faster CI/CD

### Usage Recommendations

```bash
# For production: Use tagged releases (instant startup)
docker pull whisperengine/whisperengine:v1.0.0    # ✅ Models included
docker run -d whisperengine/whisperengine:v1.0.0  # ✅ Starts immediately

# For development: Use latest (smaller, faster builds)  
docker pull whisperengine/whisperengine:latest    # ❌ No models
docker run -d whisperengine/whisperengine:latest  # ⚠️ 2-5min first startup
```

| Trigger | Image Tags | Platforms | Models |
|---------|------------|-----------|---------|
| Push to `main` | `latest` | linux/amd64, linux/arm64 | ❌ Download on first run |
| Version tag (e.g., `v1.0.0`) | `v1.0.0`, `1.0` | linux/amd64, linux/arm64 | ✅ **Pre-downloaded** |
| Other branches | `dev-<commit>` | linux/amd64, linux/arm64 | ❌ Download on first run |
| Pull requests | Build only (no push) | linux/amd64, linux/arm64 | ❌ Download on first run |

## 🧪 Testing

You can test the Docker build without pushing:

```bash
# Test build locally
docker build -f docker/Dockerfile.multi-stage --target production -t whisperengine-test .

# Run the test workflow manually
# Go to Actions → "🧪 Test Docker Build" → "Run workflow"
```

## 🚀 Usage

Once published, users can deploy WhisperEngine with:

```bash
# Quick start
docker pull whisperengine/whisperengine:latest
docker run -d --name whisperengine \
  -e DISCORD_BOT_TOKEN=your_token \
  whisperengine/whisperengine:latest

# Or with docker-compose
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/docker/quick-start/docker-compose.yml -o docker-compose.yml
docker-compose up -d
```

## 🔍 Troubleshooting

### Common Issues

**Build fails with permission error:**
- Verify your Docker Hub token has "Write" permissions
- Check the token hasn't expired
- Ensure secret names match: `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN` or `DOCKER_USERNAME`/`DOCKER_PASSWORD`

**"Repository not found" error:**
- Ensure Docker Hub repository `whisperengine/whisperengine` exists
- Verify repository is public (for public access)

**Workflow doesn't trigger:**
- Check workflow permissions in Settings → Actions → General
- Ensure secrets are set at repository level, not environment level

**Multi-architecture build fails:**
- This should auto-resolve with the buildx setup
- If persistent, check GitHub runner availability

### Debug Commands

```bash
# Check if images are available
docker pull whisperengine/whisperengine:latest

# Test image functionality  
docker run --rm whisperengine/whisperengine:latest python -c "print('Test passed')"

# Check build logs
# Go to Actions → Latest workflow run → "Build and push Docker image"
```

## 📊 Monitoring

- **Build Status**: Check Actions tab for workflow runs
- **Docker Hub**: Monitor pulls at https://hub.docker.com/r/whisperengine/whisperengine
- **Image Size**: Workflows report final image sizes in summaries

---

**🎉 Once setup is complete, users can deploy WhisperEngine in under 2 minutes!**