# Docker Hub Publishing Setup Guide

This guide explains how to set up automated Docker Hub publishing for WhisperEngine.

## Prerequisites

1. **Docker Hub Account**: Create account at https://hub.docker.com
2. **Docker Hub Repository**: Create `whisperengine/whisperengine` repository
3. **GitHub Repository**: Admin access to configure secrets

## Step 1: Create Docker Hub Access Token

1. Go to Docker Hub → Account Settings → Security
2. Click "New Access Token"
3. Name: `GitHub Actions WhisperEngine`
4. Permissions: `Read, Write, Delete`
5. Copy the generated token (you won't see it again)

## Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these **Repository Secrets**:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `DOCKERHUB_USERNAME` | `whisperengine` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | `dckr_pat_xxx...` | Access token from Step 1 |

## Step 3: Verify Workflow Permissions

Ensure GitHub Actions has the right permissions:

1. Go to Settings → Actions → General
2. Under "Workflow permissions":
   - Select "Read and write permissions"
   - Check "Allow GitHub Actions to create and approve pull requests"

## Step 4: Test the Workflow

### Automatic Triggers
The workflow automatically runs on:
- **Push to `main`** → Builds `latest` tag
- **Push to `develop`** → Builds `develop` tag  
- **Version tags** (`v1.2.3`) → Builds versioned releases
- **Pull requests** → Builds without pushing (test only)

### Manual Trigger
You can also trigger manually:
1. Go to Actions → "Build and Publish Docker Images"
2. Click "Run workflow"
3. Select branch and click "Run workflow"

## Step 5: Verify Docker Hub Images

After a successful workflow run, check:

1. **Main Image**: https://hub.docker.com/r/whisperengine/whisperengine
2. **ChromaDB Image**: https://hub.docker.com/r/whisperengine/chromadb
3. **Multi-Architecture**: Should show `linux/amd64` and `linux/arm64`

## What Gets Built

### Main Application (`whisperengine/whisperengine`)
- **Tags**: `latest`, `develop`, `v1.x.x`
- **Platforms**: `linux/amd64`, `linux/arm64`
- **Dockerfile**: `docker/Dockerfile`

### Custom ChromaDB (`whisperengine/chromadb`) 
- **Tags**: `latest`, `develop`, `v1.x.x`
- **Platforms**: `linux/amd64`, `linux/arm64`
- **Dockerfile**: `docker/Dockerfile.chromadb`

## Troubleshooting

### Build Failures
- Check GitHub Actions logs in the "Actions" tab
- Verify Docker Hub credentials are correct
- Ensure Dockerfile paths exist

### Permission Issues
```
Error: buildx failed with: ERROR: failed to solve: failed to push
```
- Verify `DOCKERHUB_TOKEN` has `Write` permissions
- Check repository name matches exactly

### Multi-Arch Build Issues
```
Error: Multiple platforms feature is currently not supported
```
- This should auto-resolve with `docker/setup-buildx-action@v3`
- If persistent, check GitHub runner availability

## Docker Hub Repository Settings

### Repository Visibility
- Set to **Public** for open source project
- Enable "Auto-build" if desired

### Repository Description
- The workflow automatically updates from `docker/README.md`
- Manual updates: Repository → Settings → Description

### Webhooks (Optional)
Configure webhooks to notify on successful builds:
- Discord webhook for team notifications
- Slack integration for development updates

## Security Best Practices

1. **Token Scope**: Use minimal required permissions
2. **Token Rotation**: Rotate access tokens quarterly
3. **Branch Protection**: Protect `main` branch from direct pushes
4. **Review Process**: Require PR reviews before merging

## Release Process

### Creating a New Release

1. **Update Version**: Increment version in relevant files
2. **Create Git Tag**: 
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```
3. **Automatic Build**: GitHub Actions will build and push versioned images
4. **Update Documentation**: Update any version references in docs

### Version Tagging Strategy

- `v1.2.3` → Full semantic version
- `v1.2` → Minor version alias  
- `v1` → Major version alias
- `latest` → Latest stable release

## Monitoring

### Build Status
- Add build status badge to README:
  ```markdown
  ![Docker Build](https://github.com/WhisperEngine-AI/whisperengine/actions/workflows/docker-publish.yml/badge.svg)
  ```

### Docker Hub Metrics
Monitor at Docker Hub → Repository → Analytics:
- Pull statistics
- Geographic distribution
- Popular tags

---

**Need Help?** 
- GitHub Actions Documentation: https://docs.github.com/en/actions
- Docker Hub Documentation: https://docs.docker.com/docker-hub/
- WhisperEngine Discord: Join for support and discussion