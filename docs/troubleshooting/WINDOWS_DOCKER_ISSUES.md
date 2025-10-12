# Windows Docker Issues - Troubleshooting Guide

## Issue 1: YAML Syntax Error (Line 25)

### Error Message
```
yaml: line 25: did not find expected '-' indicator
```

### Root Cause
You downloaded the **full WhisperEngine source code repository** which is intended for developers. The main `docker-compose.yml` file currently has malformed YAML comments that cause syntax errors.

### ✅ SOLUTION: Use Containerized Setup (Recommended)

**You should NOT download the source code as a ZIP file.** Instead, use the containerized setup which downloads only the necessary config files:

**Windows PowerShell:**
```powershell
# Delete the whisperengine-main folder
Remove-Item -Recurse -Force whisperengine-main

# Run the proper setup command
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

**Windows Command Prompt:**
```cmd
# Delete the whisperengine-main folder
rmdir /s /q whisperengine-main

# Run the proper setup command
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

This will:
- ✅ Download **only** the necessary config files (~5KB)
- ✅ Use pre-built Docker images from Docker Hub
- ✅ Avoid YAML syntax issues
- ✅ Work out of the box

---

## Issue 2: WSL/Docker Desktop Errors

### Error Messages
```
DockerDesktop/Wsl/ExecError: c:\windows\system32\wsl.exe --unmount docker_data.vhdx: exit status 0xffffffff
```
```
struggling to pull db migrate whisperengine assistant and extract c71e1110855
```

### Root Causes
1. **WSL2 backend issues** - Docker Desktop's WSL integration is having problems
2. **Corrupted Docker data** - The docker_data.vhdx file may be corrupted
3. **Network/download issues** - Unable to pull Docker images properly

### ✅ SOLUTIONS

#### Solution 1: Restart Docker Desktop (Try This First)

1. **Quit Docker Desktop completely**
   - Right-click Docker Desktop in system tray
   - Click "Quit Docker Desktop"
   - Wait 10 seconds

2. **Restart Docker Desktop**
   - Open Docker Desktop again
   - Wait for it to fully start (whale icon should be steady)

3. **Try setup again**

#### Solution 2: Reset Docker Data (If Restart Doesn't Work)

**⚠️ Warning: This will delete all Docker containers, images, and volumes**

1. **Open Docker Desktop**
2. **Go to Settings (gear icon)**
3. **Click "Troubleshoot" on left sidebar**
4. **Click "Clean / Purge data"**
5. **Click "Reset to factory defaults"**
6. **Restart Docker Desktop**
7. **Try setup again**

#### Solution 3: Fix WSL2 Integration

1. **Open Docker Desktop Settings**
2. **Go to "General"**
3. **Ensure "Use the WSL 2 based engine" is checked**
4. **Go to "Resources" → "WSL Integration"**
5. **Enable integration for your WSL2 distro**
6. **Click "Apply & Restart"**

#### Solution 4: Repair WSL2 (Advanced)

If Docker still fails, repair WSL2:

**PowerShell (Run as Administrator):**
```powershell
# Check WSL status
wsl --status

# Update WSL
wsl --update

# Shutdown WSL completely
wsl --shutdown

# Wait 10 seconds, then restart Docker Desktop
```

#### Solution 5: Check Disk Space

Ensure you have enough disk space:
- **Minimum**: 10GB free space
- **Recommended**: 20GB free space

Check in Windows Explorer → This PC → Local Disk (C:)

#### Solution 6: Check Network Connection

If Docker can't pull images:

1. **Test internet connection**
   ```powershell
   Test-Connection hub.docker.com
   ```

2. **Check Docker Hub is accessible**
   - Visit: https://hub.docker.com
   - Should load without errors

3. **Configure Docker proxy** (if behind corporate firewall)
   - Docker Desktop → Settings → Resources → Proxies

---

## Complete Fresh Setup Process

If all else fails, do a complete fresh start:

### Step 1: Complete Cleanup

```powershell
# Stop all containers
docker stop $(docker ps -aq)

# Remove all containers
docker rm $(docker ps -aq)

# Remove all images
docker rmi $(docker images -q)

# Remove all volumes
docker volume prune -a -f

# Quit Docker Desktop
# (Right-click system tray → Quit)
```

### Step 2: Reset Docker Desktop

1. Open Docker Desktop Settings
2. Troubleshoot → Reset to factory defaults
3. Wait for reset to complete
4. Restart Docker Desktop

### Step 3: Verify Docker Works

```powershell
# Test Docker
docker run hello-world
```

Should output "Hello from Docker!"

### Step 4: Run WhisperEngine Setup

```powershell
# Run containerized setup
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

---

## What You Should NOT Do

❌ **Don't download the repository as a ZIP file**
- The main `docker-compose.yml` is for developers
- Contains source code build instructions
- More complex and error-prone

❌ **Don't use `docker compose --build`**
- Containerized setup uses pre-built images
- No building required
- Faster and more reliable

❌ **Don't manually edit docker-compose.yml**
- Let the setup script handle it
- Reduces chance of syntax errors

---

## What You SHOULD Do

✅ **Use the containerized setup script**
- Designed for end users
- Downloads only config files
- Uses pre-built Docker images

✅ **Ensure Docker Desktop is fully started**
- Wait for whale icon to be steady
- Check Settings → Kubernetes (if enabled)

✅ **Have stable internet connection**
- Needed to download Docker images (~1-2GB)
- First time only

✅ **Check system requirements**
- Windows 10/11 64-bit
- WSL2 installed and updated
- Virtualization enabled in BIOS
- 8GB RAM minimum (16GB recommended)

---

## Getting Help

If you're still stuck after trying these solutions:

1. **Collect diagnostic information:**
   ```powershell
   # Docker version
   docker version
   
   # Docker info
   docker info
   
   # WSL status
   wsl --status
   
   # Windows version
   winver
   ```

2. **Create a GitHub issue:**
   - Visit: https://github.com/whisperengine-ai/whisperengine/issues
   - Click "New Issue"
   - Include:
     - Windows version
     - Docker Desktop version
     - WSL2 version
     - Complete error messages
     - What you tried

3. **Check existing issues:**
   - Search: https://github.com/whisperengine-ai/whisperengine/issues
   - Filter by "windows" or "docker" labels

---

## Quick Command Reference

### Check Docker Status
```powershell
docker ps                    # Running containers
docker ps -a                 # All containers
docker images                # Downloaded images
docker volume ls             # Created volumes
wsl --status                 # WSL2 status
```

### Clean Up Docker
```powershell
docker system prune -a -f    # Remove all unused data
docker volume prune -f       # Remove unused volumes
wsl --shutdown               # Shutdown WSL2
```

### Restart Everything
```powershell
# Shutdown WSL
wsl --shutdown

# Quit Docker Desktop (via system tray)
# Wait 10 seconds

# Start Docker Desktop
# Wait for full startup

# Verify it works
docker run hello-world
```

---

## Summary

**Your main issue is using the wrong setup method.**

Instead of downloading the repository ZIP:
1. ✅ Delete the `whisperengine-main` folder
2. ✅ Run the PowerShell setup script (see top of this guide)
3. ✅ Let it download only what's needed
4. ✅ Use pre-built Docker images

This will avoid YAML errors and simplify the entire process!
