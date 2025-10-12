# Windows Quickstart Troubleshooting & Fixes

## Issues Fixed (October 12, 2025)

### 1. PowerShell Setup Script Syntax Errors

**File**: `setup-containerized.ps1`

**Problems**:
- Line 107: Regex pattern `[^\r\n]` not properly escaped in PowerShell
- Line 190: Mixed quote nesting causing string termination errors

**Fixes Applied**:
- ✅ Changed `[^\r\n]` to `[^`r`n]` (proper backtick escaping)
- ✅ Changed quote style from double-with-single to single-with-double

**User Impact**: PowerShell quickstart now works without syntax errors

---

### 2. PowerShell Cleanup Script Template Syntax

**File**: `cleanup-docker.ps1`

**Problems**:
- Docker Go template syntax `{{.Name}}` wrapped in double quotes
- PowerShell may interpret curly braces incorrectly

**Fixes Applied**:
- ✅ Changed all `{{.Name}}` occurrences from double quotes to single quotes
- ✅ Single quotes preserve literal strings in PowerShell

**User Impact**: Cleanup command now works correctly

---

### 3. Batch File Download Failures

**File**: `setup-containerized.bat`

**Problems**:
- Variable expansion issues in embedded PowerShell commands
- Insufficient error messages for debugging
- Poor error handling for directory operations

**Fixes Applied**:
- ✅ Hardcoded URLs directly in PowerShell commands (avoid variable expansion issues)
- ✅ Added `-ErrorAction Stop` to PowerShell download commands
- ✅ Added better error messages with internet connection hints
- ✅ Added directory creation validation
- ✅ Added explicit error checking after `cd` command

**User Impact**: Batch file now downloads files correctly and provides better error messages

---

## How to Use Fixed Scripts

### PowerShell (Recommended)

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

### Command Prompt (Batch)

```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

### Cleanup

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.ps1" -OutFile "cleanup.ps1"; .\cleanup.ps1
```

---

## Alternative: Manual Setup (If Scripts Still Fail)

If you continue to experience issues with the automated scripts, use this manual approach:

### Step 1: Create Directory and Files

```cmd
mkdir whisperengine
cd whisperengine
```

### Step 2: Download Files Manually

**Option A: Using PowerShell**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/docker-compose.containerized.yml" -OutFile "docker-compose.yml"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/.env.containerized.template" -OutFile ".env"
```

**Option B: Using Browser**
1. Download: https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/docker-compose.containerized.yml
   - Save as: `docker-compose.yml` in `whisperengine` folder
2. Download: https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/.env.containerized.template
   - Save as: `.env` in `whisperengine` folder

### Step 3: Configure .env File

Edit `.env` file and add your LLM configuration:

```bash
# For OpenRouter (recommended)
LLM_CLIENT_TYPE=openrouter
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
LLM_CHAT_API_KEY=your_openrouter_key_here
LLM_CHAT_MODEL=mistralai/mistral-small-3.2-24b-instruct

# Or for LM Studio (local, free)
LLM_CLIENT_TYPE=lmstudio
LLM_CHAT_API_URL=http://host.docker.internal:1234/v1
LLM_CHAT_API_KEY=not-needed
LLM_CHAT_MODEL=model-name-in-lm-studio
```

### Step 4: Start Services

```cmd
docker-compose up -d
```

### Step 5: Wait for Services

Wait 30-60 seconds, then access:
- Web UI: http://localhost:3001
- Chat API: http://localhost:9090/api/chat

---

## Common Issues & Solutions

### "Failed to download Docker Compose file"

**Possible causes**:
1. Internet connection issues
2. GitHub rate limiting
3. Firewall blocking downloads
4. PowerShell execution policy

**Solutions**:
- Check internet connection
- Try manual download approach above
- Check firewall settings
- Run PowerShell as Administrator

### "Docker is not running"

**Solution**:
- Open Docker Desktop
- Wait for it to fully start (Docker icon should be steady, not animated)
- Try script again

### Unicode/Emoji Display Issues

**Not a problem**: The garbled characters (­ƒÉ│, Ô£¿, etc.) are just emoji display issues in cmd.exe. The script functionality is not affected.

**Solution**: Use PowerShell instead of Command Prompt for better Unicode support

### "Port already in use"

**Solution**:
```cmd
# Stop existing services
docker-compose down

# Or stop specific ports
docker ps
docker stop <container_id>
```

---

## Need More Help?

- **Documentation**: https://github.com/whisperengine-ai/whisperengine/blob/main/README.md
- **Issues**: https://github.com/whisperengine-ai/whisperengine/issues
- **Quick Reference**: https://github.com/whisperengine-ai/whisperengine/blob/main/QUICK_REFERENCE.md
