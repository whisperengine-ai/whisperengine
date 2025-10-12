# WhisperEngine Version Management Summary

**Date:** October 12, 2025  
**Current Version:** 1.0.8

## What Changed

### ✅ Version Tracking Improvements

**Before:**
- ❌ `pyproject.toml` stuck at version `0.0.1` (outdated)
- ❌ No `__version__` constant for runtime access
- ❌ Manual version updates in multiple places
- ❌ Manual git tagging and Docker versioning

**After:**
- ✅ `pyproject.toml` updated to `1.0.8` (current)
- ✅ `src/__init__.py` with `__version__ = "1.0.8"`
- ✅ `VERSION` file for simple reference
- ✅ Automated `bump_version.py` script for version management

---

## Version Sources (Single Source of Truth)

WhisperEngine version is tracked in **3 locations**:

1. **`pyproject.toml`** - Python package version (authoritative)
   ```toml
   version = "1.0.8"
   ```

2. **`src/__init__.py`** - Runtime accessible (authoritative)
   ```python
   __version__ = "1.0.8"
   ```

3. **`VERSION`** - Plain text reference (optional)
   ```
   1.0.8
   ```

**All three are kept in sync automatically by `scripts/bump_version.py`**

---

## New Automated Workflow

### Quick Version Bump (Recommended)

**Patch release (bug fix):**
```bash
python scripts/bump_version.py patch
# Updates: 1.0.8 → 1.0.9
# Creates commit + tag automatically
```

**Minor release (new features):**
```bash
python scripts/bump_version.py minor
# Updates: 1.0.8 → 1.1.0
```

**Major release (breaking changes):**
```bash
python scripts/bump_version.py major
# Updates: 1.0.8 → 2.0.0
```

**Specific version:**
```bash
python scripts/bump_version.py 1.2.3
# Updates: 1.0.8 → 1.2.3
```

**Auto-push mode:**
```bash
python scripts/bump_version.py patch --push
# Automatically commits, tags, AND pushes to origin
```

### What the Script Does

1. ✅ Detects current version from `pyproject.toml`
2. ✅ Calculates new version (patch/minor/major)
3. ✅ Updates `pyproject.toml` version field
4. ✅ Updates `src/__init__.py` __version__ constant
5. ✅ Updates `VERSION` file
6. ✅ Creates git commit: `chore: bump version X.Y.Z → X.Y.Z+1`
7. ✅ Creates annotated git tag: `vX.Y.Z+1`
8. ✅ (Optional) Pushes commit and tag to origin with `--push`

**Safety features:**
- Checks for clean git working directory
- Confirms before executing changes
- Validates version format (semantic versioning)
- Shows summary before proceeding

---

## Complete Release Process

### Automated (Recommended)

```bash
# 1. Bump version and create git tag
python scripts/bump_version.py patch --push

# 2. Build and push Docker images
./push-to-dockerhub.sh whisperengine v1.0.9

# 3. Create GitHub release (manual or CLI)
gh release create v1.0.9 --generate-notes
```

### Manual (If Preferred)

```bash
# 1. Edit version files manually
# - pyproject.toml: version = "1.0.9"
# - src/__init__.py: __version__ = "1.0.9"
# - VERSION: 1.0.9

# 2. Commit changes
git add pyproject.toml src/__init__.py VERSION
git commit -m "chore: bump version 1.0.8 → 1.0.9"

# 3. Create git tag
git tag -a v1.0.9 -m "WhisperEngine v1.0.9"

# 4. Push everything
git push origin main
git push origin v1.0.9

# 5. Build Docker images
./push-to-dockerhub.sh whisperengine v1.0.9

# 6. Create GitHub release
# Go to: https://github.com/whisperengine-ai/whisperengine/releases/new
```

---

## Docker Integration

### Alembic Migrations Automatically Included

The `Dockerfile` includes:
```dockerfile
# Copy Alembic migration system
COPY alembic.ini ./
COPY alembic/ ./alembic/
```

**This means:**
- ✅ Every Docker build includes ALL migration files
- ✅ `push-to-dockerhub.sh` automatically includes migrations
- ✅ Container startup runs `alembic upgrade head`
- ✅ No manual migration deployment needed

**Your recent migration is already included:**
- `20251012_1338_c5bc995c619f_add_character_interest_topics_table.py`

---

## Usage Examples

### Access Version in Python Code

```python
from src import __version__, VERSION_INFO

print(f"WhisperEngine v{__version__}")  # "WhisperEngine v1.0.8"

# Check version programmatically
if VERSION_INFO >= (1, 1, 0):
    # Use new feature only available in 1.1.0+
    pass
```

### Check Version in Terminal

```bash
# From source
python -c "from src import __version__; print(__version__)"

# From Docker container
docker run --rm whisperengine/whisperengine:latest \
  python -c "from src import __version__; print(__version__)"

# Simple file reference
cat VERSION
```

### Version History

```bash
# View all version tags
git tag -l "v*"

# View version history
alembic history --verbose

# Check current Docker image version
docker images whisperengine/whisperengine --format "{{.Tag}}"
```

---

## Files Created/Modified

### New Files

- ✅ `scripts/bump_version.py` - Automated version bumping script
- ✅ `VERSION` - Plain text version reference
- ✅ `docs/guides/RELEASE_PROCESS.md` - Complete release documentation
- ✅ `docs/reports/VERSION_MANAGEMENT_SUMMARY.md` - This file

### Modified Files

- ✅ `src/__init__.py` - Added `__version__` and `VERSION_INFO`
- ✅ `pyproject.toml` - Updated version from `0.0.1` to `1.0.8`

### Verified Working

- ✅ `push-to-dockerhub.sh` - Already includes Alembic migrations
- ✅ `Dockerfile` - Already copies `alembic/` directory
- ✅ All version sources now synchronized at `1.0.8`

---

## Next Release (Example)

When you're ready for the next release:

```bash
# 1. Make your code changes
git add .
git commit -m "fix: resolve issue XYZ"

# 2. Bump version (patch for bug fix)
python scripts/bump_version.py patch
# This creates: 1.0.8 → 1.0.9 + commit + tag

# 3. Push to GitHub
git push origin main
git push origin v1.0.9

# 4. Build Docker
./push-to-dockerhub.sh whisperengine v1.0.9

# 5. Create GitHub release
gh release create v1.0.9 --title "WhisperEngine v1.0.9" --generate-notes
```

**Total time: ~5 minutes** (vs 15+ minutes manual process)

---

## Benefits

### Before Automation

- ⏰ 15+ minutes per release
- 🤔 Manual version tracking across multiple files
- ❌ Easy to forget updating a file
- ❌ Version mismatches between code and Docker
- ❌ Manual git tagging prone to typos
- ❌ Inconsistent commit messages

### After Automation

- ⏰ 5 minutes per release
- ✅ Single command updates all files
- ✅ Impossible to have version mismatches
- ✅ Automated git commit + tag creation
- ✅ Consistent semantic versioning
- ✅ Standardized commit messages
- ✅ Optional auto-push to streamline workflow

---

## Documentation

**Comprehensive guides created:**

- [`docs/guides/RELEASE_PROCESS.md`](../guides/RELEASE_PROCESS.md) - Complete release workflow guide
  - Version management strategies
  - Automated vs manual workflows
  - Docker image publishing
  - GitHub release creation
  - Troubleshooting guide
  - Best practices

**Quick reference:**
```bash
# View release process
cat docs/guides/RELEASE_PROCESS.md

# Run version bump
python scripts/bump_version.py --help
```

---

## Recommendations

### For Your Workflow

**Based on your current process (manually tagging Docker and git):**

1. ✅ **Use `bump_version.py` for version updates** - Eliminates manual editing
2. ✅ **Keep manual Docker pushes** - You have good control over timing
3. ✅ **Use `--push` flag when ready** - Streamlines git push workflow

**Suggested workflow:**
```bash
# After fixing Aetheris bug
python scripts/bump_version.py patch --push  # Auto-commits, tags, pushes
./push-to-dockerhub.sh whisperengine v1.0.9  # Manual Docker control
gh release create v1.0.9 --generate-notes     # Optional GitHub release
```

### Future Enhancements (Optional)

- [ ] Add GitHub Actions workflow for automated Docker builds on tag push
- [ ] Add changelog generation from git commits
- [ ] Add release notes template automation
- [ ] Add pre-release validation checks (tests, linting)

**For now, the manual workflow with `bump_version.py` gives you the best balance of automation and control.**

---

## Testing

**Verify the new system works:**

```bash
# 1. Check current version
python -c "from src import __version__; print(__version__)"
# Output: 1.0.8

# 2. Test version bump (dry run - use on a test branch)
git checkout -b test-version-bump
python scripts/bump_version.py patch
# Verify: creates commit, tag, updates files

# 3. Verify Docker includes migrations
docker run --rm whisperengine/whisperengine:latest ls -la /app/alembic/versions/
# Should list all migration files including: 20251012_1338_c5bc995c619f_...
```

---

## Questions?

**Common questions answered in:**
- `docs/guides/RELEASE_PROCESS.md` - Complete release guide
- `scripts/bump_version.py` - Run with `--help` for usage

**Need help?**
```bash
python scripts/bump_version.py --help
```

---

**Status:** ✅ Version management system complete and ready to use  
**Next Action:** Use `python scripts/bump_version.py patch` for next release  
**Recommended:** Test on a feature branch first to verify workflow
