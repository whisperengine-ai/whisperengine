# 🚀 GitHub Actions Docker Hub Setup - Step-by-Step Guide

**Complete checklist to enable automated Docker Hub publishing for WhisperEngine**

## ✅ Prerequisites Checklist

- [ ] GitHub repository with admin access
- [ ] Docker Hub account created
- [ ] WhisperEngine code pushed to GitHub

## 📋 Step-by-Step Setup

### Step 1: Create Docker Hub Repository

1. **Go to Docker Hub**: https://hub.docker.com
2. **Create Repository**:
   - Repository Name: `whisperengine`
   - Namespace: `whisperengine` (or your username)
   - Full name: `whisperengine/whisperengine`
   - Visibility: **Public** (for open source)
   - Description: "Advanced AI Discord bot with Phase 4 human-like intelligence"

### Step 2: Generate Docker Hub Access Token

1. **Navigate to Security Settings**:
   - Go to Docker Hub → Account Settings → Security
   - Or direct link: https://hub.docker.com/settings/security

2. **Create New Access Token**:
   - Click "New Access Token"
   - Token Description: `GitHub Actions WhisperEngine`
   - Access Permissions: **Read, Write, Delete**
   - Click "Generate"

3. **Copy Token**:
   - **IMPORTANT**: Copy the token immediately (format: `dckr_pat_xxx...`)
   - You won't be able to see it again!

### Step 3: Configure GitHub Repository Secrets

1. **Navigate to Repository Secrets**:
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Or: `https://github.com/WhisperEngine-AI/whisperengine/settings/secrets/actions`

2. **Add Required Secrets**:
   
   **Secret 1: Docker Hub Username**
   - Click "New repository secret"
   - Name: `DOCKERHUB_USERNAME`
   - Secret: `whisperengine` (your Docker Hub username)
   - Click "Add secret"

   **Secret 2: Docker Hub Token**
   - Click "New repository secret"
   - Name: `DOCKERHUB_TOKEN`
   - Secret: `dckr_pat_xxx...` (paste the token from Step 2)
   - Click "Add secret"

### Step 4: Verify GitHub Actions Permissions

1. **Check Workflow Permissions**:
   - Go to Settings → Actions → General
   - Or: `https://github.com/WhisperEngine-AI/whisperengine/settings/actions`

2. **Configure Permissions**:
   - Under "Workflow permissions":
   - Select: ☑️ **"Read and write permissions"**
   - Check: ☑️ **"Allow GitHub Actions to create and approve pull requests"**
   - Click "Save"

### Step 5: Test the Workflow

#### Option A: Automatic Trigger (Recommended)
```bash
# The workflow will trigger automatically on:
# - Push to main branch
# - Push to develop branch  
# - Creating version tags (v1.0.0, etc.)
# - Pull requests (test builds only)

# To trigger with a version tag:
git tag v1.0.0
git push origin v1.0.0
```

#### Option B: Manual Trigger
1. Go to GitHub Actions tab
2. Select "Build and Publish Docker Images"
3. Click "Run workflow"
4. Select branch (usually `main`)
5. Click "Run workflow"

### Step 6: Verify Success

1. **Check GitHub Actions**:
   - Go to Actions tab in your repository
   - Verify the workflow runs successfully (green checkmark ✅)
   - Check build logs for any errors

2. **Verify Docker Hub**:
   - Go to https://hub.docker.com/r/whisperengine/whisperengine
   - Confirm images are published with correct tags
   - Verify multi-architecture support (AMD64 + ARM64)

3. **Test the Images**:
   ```bash
   # Test pulling the image
   docker pull whisperengine/whisperengine:latest
   
   # Test the quick-start script
   curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash
   ```

## 🔧 What the Workflow Does

### Automatic Builds
- **Main Branch** → `latest` tag (stable release)
- **Develop Branch** → `develop` tag (beta builds)
- **Version Tags** (`v1.2.3`) → Versioned releases (`1.2.3`, `1.2`, `1`)
- **Pull Requests** → Test builds (not published)

### Multi-Architecture Support
- Builds for both `linux/amd64` and `linux/arm64`
- Works on Intel/AMD servers and Apple M1/M2 Macs

### Features
- ✅ Automated Docker Hub README updates
- ✅ Build caching for faster builds
- ✅ Security scanning
- ✅ Multi-platform support

## 🚨 Troubleshooting

### Common Issues

**Build Fails with Permission Error**
```
Error: buildx failed with: ERROR: failed to push
```
**Solution**: Verify `DOCKERHUB_TOKEN` has "Write" permissions

**"Repository not found" Error**
```
Error: failed to push whisperengine/whisperengine:latest
```
**Solution**: Ensure Docker Hub repository exists and name matches exactly

**GitHub Actions Not Triggering**
**Solution**: Check workflow permissions in Settings → Actions → General

**Multi-Architecture Build Fails**
**Solution**: This should auto-resolve with the buildx setup. If persistent, check GitHub runner availability.

### Verification Commands

```bash
# Check if image was built correctly
docker run --rm whisperengine/whisperengine:latest --version

# Inspect image architecture
docker image inspect whisperengine/whisperengine:latest | grep Architecture

# Test multi-arch pull
docker pull --platform linux/arm64 whisperengine/whisperengine:latest
docker pull --platform linux/amd64 whisperengine/whisperengine:latest
```

## 📊 Success Criteria

✅ **GitHub Actions runs successfully**
✅ **Docker images published to Docker Hub**
✅ **Multi-architecture support working**
✅ **Version tagging works correctly**
✅ **Quick-start script pulls and runs images**
✅ **Docker Hub README updated automatically**

## 🔄 Ongoing Maintenance

### Regular Tasks
- **Monitor build success rate** (aim for 99%+)
- **Review Docker Hub analytics** monthly
- **Update base images** quarterly for security
- **Test quick-start script** with each major release

### Release Process
```bash
# For new releases:
git tag v1.2.3
git push origin v1.2.3

# GitHub Actions will automatically:
# 1. Build multi-arch images
# 2. Push to Docker Hub with version tags
# 3. Update latest tag if on main branch
# 4. Update Docker Hub README
```

---

## 📝 Quick Reference

**Docker Hub Repository**: `whisperengine/whisperengine`
**GitHub Secrets Needed**: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
**Workflow File**: `.github/workflows/docker-publish.yml`
**Test Command**: `curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash`

**🎉 Once setup is complete, users can deploy WhisperEngine in 2 minutes with a single command!**