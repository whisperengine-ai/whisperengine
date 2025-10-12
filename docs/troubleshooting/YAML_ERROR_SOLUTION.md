# SOLUTION: YAML Error on Line 25 + WSL Issues

## Your Situation

You downloaded `whisperengine-main.zip`, tried to run `docker compose -f docker-compose.yml up`, and got:

```
yaml: line 25: did not find expected '-' indicator
```

Plus WSL errors: `exit status 0xffffffff`

## Root Cause

**You're using the wrong files!** You downloaded the **developer source code** (which has known YAML bugs in `docker-compose.yml`) instead of using the **end-user containerized setup**.

## Solution (5 Minutes)

### Step 1: Delete Everything

```powershell
# Delete the whisperengine-main folder
Remove-Item -Recurse -Force whisperengine-main
```

### Step 2: Use Containerized Setup

Open **PowerShell** as Administrator and run:

```powershell
# Download and run setup script (uses docker-compose.containerized.yml - NO YAML ERRORS)
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/your-repo/whisperengine/main/setup-containerized.ps1' -OutFile 'setup.ps1'
.\setup.ps1
```

### Step 3: Access WhisperEngine

```
http://localhost:9090
```

That's it! No Git, no ZIP downloads, no YAML errors.

## Why This Works

| What You Did | What You Should Do |
|--------------|-------------------|
| Downloaded ZIP with source code | Use containerized setup script |
| Used `docker-compose.yml` (broken YAML) | Uses `docker-compose.containerized.yml` (valid YAML) |
| Tried to build from source | Downloads pre-built Docker images |
| Required developer setup | Works with just Docker Desktop |

## Still Having Issues?

### WSL Errors Persist?

```powershell
# Restart WSL
wsl --shutdown
# Wait 10 seconds, then try setup again
```

### Docker Desktop Not Working?

1. Open Docker Desktop
2. Go to: Settings → General → "Use WSL 2 based engine" (check this)
3. Apply & Restart

### Nuclear Option (Reset Docker)

```powershell
# Stop Docker Desktop
# Open PowerShell as Admin
wsl --shutdown
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data
# Restart Docker Desktop (will recreate WSL instances)
```

## What Was Wrong with docker-compose.yml?

The file you downloaded has **malformed YAML comments** (lines 28-160):

```yaml
# WRONG (causes parser errors)
      #   qdrant:
      #     image: qdrant/qdrant:latest

# RIGHT (proper YAML)
  # qdrant:
  #   image: qdrant/qdrant:latest
```

**But you don't need to fix this!** The containerized setup uses a different file (`docker-compose.containerized.yml`) that has no YAML errors.

## For Future Reference

### End Users (You)

✅ **DO**: Use containerized setup script  
❌ **DON'T**: Download repo ZIP, clone Git, edit YAML files

### Developers (Contributing to WhisperEngine)

✅ **DO**: Clone repo, use `./multi-bot.sh`  
❌ **DON'T**: Use `docker-compose.yml` directly (it's broken)

## Quick Commands

```powershell
# Complete fresh setup (one command)
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/your-repo/whisperengine/main/setup-containerized.ps1' -OutFile 'setup.ps1'; .\setup.ps1

# Cleanup if needed (delete old containers/volumes)
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/your-repo/whisperengine/main/cleanup-docker.ps1' -OutFile 'cleanup.ps1'; .\cleanup.ps1

# Access WhisperEngine
Start-Process "http://localhost:9090"
```

## Related Documentation

- Full guide: `docs/troubleshooting/WINDOWS_DOCKER_ISSUES.md`
- PowerShell issues: `docs/troubleshooting/WINDOWS_POWERSHELL_SETUP.md`
- Docker Compose files explained: `docs/deployment/DOCKER_COMPOSE_FILES_EXPLAINED.md`
- Quick reference: `QUICK_REFERENCE.md`

## Summary

1. **Delete** whisperengine-main folder
2. **Run** containerized setup script (PowerShell one-liner above)
3. **Access** http://localhost:9090
4. **Forget** about YAML files, ZIP downloads, Git cloning

The containerized setup handles everything automatically using the correct files. You'll be chatting with your AI character in 5 minutes! 🚀
