# Docker Compose Files Explained

## Overview

WhisperEngine has multiple Docker Compose files for different use cases. **If you're an end user just trying to run WhisperEngine, you should use the containerized setup script - NOT any of these files directly.**

## File Purposes

### For End Users (Recommended)

**`docker-compose.containerized.yml`** - Production-ready setup
- **Purpose**: Self-contained deployment for end users
- **What it does**: Downloads pre-built Docker images from Docker Hub, no source code needed
- **How to use**: Run the setup script (see below)
- **Status**: ✅ Production-ready, actively maintained
- **YAML Status**: ✅ Valid syntax

**Setup Commands**:

```powershell
# Windows PowerShell (RECOMMENDED)
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/your-repo/whisperengine/main/setup-containerized.ps1' -OutFile 'setup.ps1'; .\setup.ps1
```

```bash
# macOS/Linux
curl -fsSL https://raw.githubusercontent.com/your-repo/whisperengine/main/setup-containerized.sh | bash
```

### For Developers

**`docker-compose.multi-bot.yml`** - Multi-bot deployment (Active)
- **Purpose**: Production multi-bot system managed by `./multi-bot.sh`
- **What it does**: Runs multiple character bots with shared infrastructure
- **How to use**: `./multi-bot.sh start all` or `./multi-bot.sh start elena`
- **Status**: ✅ Production-ready, auto-generated from template
- **YAML Status**: ✅ Valid syntax (auto-generated)

**`docker-compose.multi-bot.template.yml`** - Multi-bot template
- **Purpose**: Template for generating multi-bot.yml
- **What it does**: Source template filled in by `scripts/generate_multi_bot_config.py`
- **How to use**: Edit this, then run: `python scripts/generate_multi_bot_config.py`
- **Status**: ✅ Maintained template
- **YAML Status**: ✅ Valid syntax

**`docker-compose.yml`** - Developer infrastructure (Problematic)
- **Purpose**: Original developer compose file with mixed infrastructure + bots
- **What it does**: Was intended for local development
- **Status**: ⚠️ **OUTDATED and PROBLEMATIC** - contains malformed YAML and mixed concerns
- **YAML Status**: ❌ **Syntax errors** - lines 28-160 have improperly indented comments
- **Problem**: Contains both infrastructure AND bot configurations (violates separation of concerns)
- **Should contain**: ONLY PostgreSQL, Qdrant infrastructure (bots should be in multi-bot.yml)
- **DO NOT USE**: Use `docker-compose.multi-bot.yml` or containerized setup instead

**`docker-compose.dev.yml`** - Development mode
- **Purpose**: Hot-reload development with source code mounting
- **Status**: Legacy, replaced by multi-bot system
- **YAML Status**: Unknown (not reviewed)

### Specialized Files

**`docker-compose.quickstart.yml`** - Quick test deployment
- **Purpose**: Minimal single-bot setup for testing
- **Status**: Legacy reference
- **YAML Status**: ✅ Valid syntax

**`docker-compose.prod.yml`** - Production deployment (Legacy)
- **Purpose**: Old production configuration
- **Status**: Superseded by containerized setup
- **YAML Status**: Unknown (not reviewed)

**Other compose files**: Various specialized configs for monitoring, logging, specific features - not for general use.

## Why the YAML Errors Occur

### Root Cause

The `docker-compose.yml` file (developer infrastructure file) has **malformed YAML comments** in lines 28-160:

```yaml
# WRONG - Improperly indented comments (causes parser errors)
      #   #         memory: 512M
      #   #         cpus: '0.5'
      # 
      #   qdrant:
      #     image: qdrant/qdrant:latest

# RIGHT - Comments at column 0 or properly structured
  # Qdrant - Vector database (commented out)
  # qdrant:
  #   image: qdrant/qdrant:latest
```

### Why This Happens

- YAML comments MUST start at column 0 (beginning of line) or follow proper YAML structure
- The problematic lines have spaces BEFORE the `#` character
- YAML parser sees this as malformed structure, not comments

### Why It's Not Fixed Yet

1. **End users don't use this file** - they use `docker-compose.containerized.yml` (no errors)
2. **Developers use multi-bot.yml** - generated from template (no errors)
3. **File should be refactored** - needs separation of concerns (infrastructure-only)
4. **Low priority** - doesn't affect production deployments

## Common Mistake: Downloading the Repo ZIP

### What Users Do Wrong

1. Download `whisperengine-main.zip` from GitHub
2. Extract the ZIP file
3. Try to run: `docker compose -f docker-compose.yml up`
4. Get YAML syntax error on line 25

### Why This Fails

- You downloaded the **developer source code** (with YAML bugs)
- You're using the **wrong docker-compose file** (docker-compose.yml)
- You're trying to **build from source** (requires dev setup)

### Correct Solution

**DON'T download the repo ZIP!** Instead:

1. **Delete the whisperengine-main folder**
2. **Use the containerized setup script**:

```powershell
# Windows PowerShell
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/your-repo/whisperengine/main/setup-containerized.ps1' -OutFile 'setup.ps1'
.\setup.ps1
```

```bash
# macOS/Linux
curl -fsSL https://raw.githubusercontent.com/your-repo/whisperengine/main/setup-containerized.sh | bash
```

3. **Access WhisperEngine**: http://localhost:9090

## Which File Should YOU Use?

### ✅ End Users (Just want to run WhisperEngine)

**Use**: Containerized setup script (downloads docker-compose.containerized.yml)

**Don't**: Download the repo, clone Git, build from source

### ✅ Developers (Contributing to WhisperEngine)

**Use**: `docker-compose.multi-bot.yml` via `./multi-bot.sh`

**Don't**: Use docker-compose.yml directly

### ✅ Template Editors (Modifying bot configs)

**Use**: `docker-compose.multi-bot.template.yml` + regenerate script

**Don't**: Edit docker-compose.multi-bot.yml directly (gets overwritten)

## File Status Summary

| File | Purpose | Status | YAML Valid | Who Uses |
|------|---------|--------|------------|----------|
| `docker-compose.containerized.yml` | End user deployment | ✅ Active | ✅ Yes | End users |
| `docker-compose.multi-bot.yml` | Multi-bot system | ✅ Active | ✅ Yes | Developers |
| `docker-compose.multi-bot.template.yml` | Multi-bot template | ✅ Active | ✅ Yes | Config editors |
| `docker-compose.yml` | Developer infrastructure | ⚠️ Outdated | ❌ **NO** | Nobody (broken) |
| `docker-compose.quickstart.yml` | Quick test | 📋 Reference | ✅ Yes | Testing only |
| `docker-compose.dev.yml` | Development mode | 📋 Legacy | ❓ Unknown | Superseded |

## Fixing docker-compose.yml (Developer Task)

If you're a developer and need to fix `docker-compose.yml`:

### Option 1: Remove Bot Configurations (Recommended)

Keep ONLY shared infrastructure:

```yaml
services:
  postgresql:
    # ... postgres config ...
  
  qdrant:
    # ... qdrant config ...

networks:
  whisperengine-network:
    driver: bridge

volumes:
  postgresql_data:
    driver: local
  qdrant_data:
    driver: local
```

**Move all bot configs to**: `docker-compose.multi-bot.yml`

### Option 2: Fix YAML Comments

Replace lines 28-160 with properly formatted comments:

```yaml
# Comments must start at column 0
# No spaces before the # character
# Each commented line needs proper # prefix

# Example properly commented section:
# redis:
#   image: redis:7-alpine
#   container_name: whisperengine-redis
#   ports:
#     - "6379:6379"
```

### Option 3: Delete Commented Sections

If sections are commented out anyway, just delete them entirely:

```yaml
# Before (malformed)
      #   qdrant:
      #     image: qdrant/qdrant:latest

# After (deleted)
# (nothing - section removed)
```

## Related Documentation

- **Troubleshooting**: `docs/troubleshooting/WINDOWS_DOCKER_ISSUES.md`
- **Windows PowerShell Setup**: `docs/troubleshooting/WINDOWS_POWERSHELL_SETUP.md`
- **Quick Reference**: `QUICK_REFERENCE.md`
- **Main README**: `README.md`

## Questions?

- **"I got a YAML error on line 25"** → You're using wrong file, use containerized setup
- **"Should I fix docker-compose.yml?"** → No, unless you're a core developer
- **"Which file is production-ready?"** → docker-compose.containerized.yml
- **"How do I run multiple bots?"** → Use `./multi-bot.sh` with docker-compose.multi-bot.yml
- **"Can I just clone the repo?"** → Only if you're developing, not for end users

## Next Steps

**End Users**: 
1. Delete any downloaded whisperengine folders
2. Run containerized setup script
3. Access http://localhost:9090

**Developers**:
1. Clone the repo: `git clone <repo-url>`
2. Use multi-bot system: `./multi-bot.sh start all`
3. Contribute fixes via pull requests

**Template Editors**:
1. Edit: `docker-compose.multi-bot.template.yml`
2. Regenerate: `python scripts/generate_multi_bot_config.py`
3. Test: `./multi-bot.sh restart all`
