# WhisperEngine Release Process

**Complete guide to versioning, tagging, and deploying WhisperEngine releases**

## Table of Contents
1. [Version Management](#version-management)
2. [Automated Release Workflow](#automated-release-workflow)
3. [Manual Release Workflow](#manual-release-workflow)
4. [Docker Image Publishing](#docker-image-publishing)
5. [GitHub Release Creation](#github-release-creation)

---

## Version Management

### Version Numbering Scheme

WhisperEngine follows **Semantic Versioning (SemVer)**:

```
MAJOR.MINOR.PATCH (e.g., 1.0.8)

MAJOR: Breaking changes, major architecture updates
MINOR: New features, backwards-compatible changes
PATCH: Bug fixes, performance improvements, documentation
```

### Single Source of Truth

Version is stored in **TWO authoritative locations**:

1. **`pyproject.toml`** - Python package version
   ```toml
   [project]
   version = "1.0.8"
   ```

2. **`src/__init__.py`** - Runtime accessible version
   ```python
   __version__ = "1.0.8"
   ```

**Access version in code:**
```python
from src import __version__
print(f"WhisperEngine v{__version__}")
```

---

## Automated Release Workflow

### Quick Release (Recommended)

**For patch releases (bug fixes):**
```bash
# Bump version, commit, tag automatically
python scripts/bump_version.py patch

# Push to GitHub
git push origin main
git push origin v1.0.9

# Build and push Docker images
./push-to-dockerhub.sh whisperengine v1.0.9
```

**For minor releases (new features):**
```bash
python scripts/bump_version.py minor
git push origin main
git push origin v1.1.0
./push-to-dockerhub.sh whisperengine v1.1.0
```

**For major releases (breaking changes):**
```bash
python scripts/bump_version.py major
git push origin main
git push origin v2.0.0
./push-to-dockerhub.sh whisperengine v2.0.0
```

**For specific version:**
```bash
python scripts/bump_version.py 1.2.3
git push origin main
git push origin v1.2.3
./push-to-dockerhub.sh whisperengine v1.2.3
```

### Automated Push Mode

**Skip manual git push confirmations:**
```bash
python scripts/bump_version.py patch --push
# Automatically commits, tags, AND pushes to origin
```

### What `bump_version.py` Does

1. ✅ Detects current version from `pyproject.toml`
2. ✅ Calculates new version based on bump type
3. ✅ Updates `pyproject.toml` version
4. ✅ Updates `src/__init__.py` __version__
5. ✅ Creates git commit: `chore: bump version 1.0.8 → 1.0.9`
6. ✅ Creates annotated git tag: `v1.0.9`
7. ✅ (Optional) Pushes commit and tag to origin

**Safety features:**
- Checks for clean git working directory
- Confirms before executing changes
- Validates version format
- Shows summary before proceeding

---

## Manual Release Workflow

**If you prefer manual control:**

### Step 1: Update Version Numbers

Edit `pyproject.toml`:
```toml
[project]
version = "1.0.9"  # Update this
```

Edit `src/__init__.py`:
```python
__version__ = "1.0.9"  # Update this
```

### Step 2: Commit Changes

```bash
git add pyproject.toml src/__init__.py
git commit -m "chore: bump version 1.0.8 → 1.0.9"
```

### Step 3: Create Git Tag

```bash
# Create annotated tag
git tag -a v1.0.9 -m "WhisperEngine v1.0.9

Bug fixes and improvements:
- Fixed Aetheris theatrical narration
- Added character_interest_topics table
- Improved CDL response guidelines
"

# Push commit and tag
git push origin main
git push origin v1.0.9
```

### Step 4: Build Docker Images

```bash
./push-to-dockerhub.sh whisperengine v1.0.9
```

---

## Docker Image Publishing

### Standard Docker Build

The `push-to-dockerhub.sh` script handles multi-platform builds:

```bash
./push-to-dockerhub.sh whisperengine v1.0.9
```

**What it does:**
1. ✅ Validates DockerHub authentication
2. ✅ Creates multi-platform buildx builder
3. ✅ Builds for `linux/amd64` and `linux/arm64`
4. ✅ Includes all Alembic migrations automatically
5. ✅ Pushes to DockerHub: `whisperengine/whisperengine:v1.0.9`
6. ✅ Tags as `latest` for the version line
7. ✅ Verifies multi-platform manifest

**Images produced:**
- `whisperengine/whisperengine:v1.0.9` (versioned)
- `whisperengine/whisperengine:latest` (rolling)
- `whisperengine/whisperengine-ui:v1.0.9` (CDL web UI)

### Alembic Migrations in Docker

**Migrations are automatically included:**

The `Dockerfile` contains:
```dockerfile
# Copy Alembic migration system
COPY alembic.ini ./
COPY alembic/ ./alembic/
```

**On container startup:**
1. Container runs `scripts/docker-entrypoint.sh`
2. Entrypoint executes `alembic upgrade head`
3. Database schema is automatically updated

**No manual migration deployment needed!**

### Verify Docker Build

```bash
# Check if Alembic migrations are in image
docker run --rm whisperengine/whisperengine:v1.0.9 ls -la /app/alembic/versions/

# Verify version in container
docker run --rm whisperengine/whisperengine:v1.0.9 python -c "from src import __version__; print(__version__)"
```

---

## GitHub Release Creation

### Automated GitHub Release (Recommended)

**Using GitHub CLI (gh):**
```bash
# Create release with auto-generated notes
gh release create v1.0.9 \
  --title "WhisperEngine v1.0.9" \
  --generate-notes

# Or create release with manual notes
gh release create v1.0.9 \
  --title "WhisperEngine v1.0.9" \
  --notes "Bug fixes and improvements:
- Fixed Aetheris theatrical narration
- Added character_interest_topics table
- Improved CDL response guidelines"
```

### Manual GitHub Release

1. Go to: https://github.com/whisperengine-ai/whisperengine/releases/new
2. Select tag: `v1.0.9`
3. Title: `WhisperEngine v1.0.9`
4. Description: List changes and improvements
5. Check "Set as latest release"
6. Click "Publish release"

---

## Complete Release Checklist

### Pre-Release Validation

- [ ] All tests pass: `pytest tests/`
- [ ] Alembic migrations tested: `alembic upgrade head`
- [ ] Bot containers running: `./multi-bot.sh status`
- [ ] Git working directory clean: `git status`
- [ ] Current version documented

### Version Bump

- [ ] Run `python scripts/bump_version.py [patch|minor|major]`
- [ ] Verify version updated in `pyproject.toml`
- [ ] Verify version updated in `src/__init__.py`
- [ ] Git commit created
- [ ] Git tag created

### Push Changes

- [ ] Push main branch: `git push origin main`
- [ ] Push version tag: `git push origin v1.0.9`
- [ ] Verify tag on GitHub

### Docker Deployment

- [ ] Build Docker images: `./push-to-dockerhub.sh whisperengine v1.0.9`
- [ ] Verify images on DockerHub
- [ ] Test pull: `docker pull whisperengine/whisperengine:v1.0.9`
- [ ] Verify Alembic migrations included

### GitHub Release

- [ ] Create GitHub release from tag
- [ ] Add release notes
- [ ] Mark as latest release
- [ ] Verify release page visible

### Post-Release Validation

- [ ] Pull new image: `docker pull whisperengine/whisperengine:latest`
- [ ] Test fresh deployment
- [ ] Verify Alembic migrations run automatically
- [ ] Check bot functionality

---

## Troubleshooting

### "Working directory not clean" Error

```bash
# Check status
git status

# Stash changes temporarily
git stash

# Or commit changes first
git add .
git commit -m "fix: pre-release cleanup"
```

### Version Mismatch Issues

```bash
# Check current version
python -c "from src import __version__; print(__version__)"
grep "version = " pyproject.toml

# Manually sync if needed
python scripts/bump_version.py 1.0.9
```

### Docker Build Failures

```bash
# Clean Docker build cache
docker builder prune -af

# Rebuild with verbose output
./push-to-dockerhub.sh whisperengine v1.0.9 --verbose
```

### Alembic Migration Not Included

```bash
# Verify Dockerfile includes:
grep -A 2 "Copy Alembic" Dockerfile

# Should show:
# COPY alembic.ini ./
# COPY alembic/ ./alembic/
```

---

## Best Practices

### Versioning Guidelines

- **Patch releases (1.0.x)**: Bug fixes, documentation, minor improvements
- **Minor releases (1.x.0)**: New features, CDL enhancements, performance upgrades
- **Major releases (x.0.0)**: Breaking changes, architecture overhauls

### Commit Message Format

```bash
# Format: <type>: <description>
chore: bump version 1.0.8 → 1.0.9
fix: resolve Aetheris theatrical narration bug
feat: add character_interest_topics dynamic loading
docs: update CDL integration guide
```

### Release Frequency

- **Patch releases**: As needed for bug fixes (weekly)
- **Minor releases**: Monthly feature releases
- **Major releases**: Quarterly or for breaking changes

### Testing Before Release

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Validate environment
python scripts/verify_environment.py

# Test bot health
./scripts/quick_bot_test.sh
```

---

## Quick Reference

**Bump version and release:**
```bash
python scripts/bump_version.py patch --push
./push-to-dockerhub.sh whisperengine v1.0.9
gh release create v1.0.9 --generate-notes
```

**Check current version:**
```bash
python -c "from src import __version__; print(__version__)"
```

**Verify Docker image:**
```bash
docker run --rm whisperengine/whisperengine:latest python -c "from src import __version__; print(__version__)"
```

---

## Related Documentation

- [QUICKSTART.md](../../QUICKSTART.md) - Development setup
- [MIGRATIONS.md](../../MIGRATIONS.md) - Alembic migration guide
- [Multi-Bot Setup](../deployment/MULTI_BOT_SETUP.md) - Bot deployment
- [CDL System](../cdl-system/) - Character Definition Language

---

**Last Updated:** October 12, 2025  
**Current Version:** 1.0.8
