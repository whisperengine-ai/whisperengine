# WhisperEngine Cleanup Scripts

## Purpose
These scripts completely remove all WhisperEngine Docker containers, volumes, and data for a fresh start. Use this when:
- Experiencing database migration errors
- Starting a fresh deployment
- Clearing out old test data
- Troubleshooting persistent issues

## ⚠️ Warning
These scripts will **DELETE ALL DATA**:
- All WhisperEngine containers
- All database data (PostgreSQL)
- All vector memory data (Qdrant)
- All time-series data (InfluxDB)
- All conversation logs

You will need to reconfigure your LLM settings after cleanup.

## Quick Usage (No Git Required)

### For End Users - Direct From GitHub

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.sh | bash
```

**Windows (PowerShell - Recommended):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.ps1" -OutFile "cleanup.ps1"; .\cleanup.ps1
```

**Windows (Command Prompt):**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.bat -o cleanup.bat && cleanup.bat
```

### For Developers - Local Repository

If you have the repository cloned:

**Linux / macOS:**
```bash
./cleanup-docker.sh
```

**Windows (PowerShell):**
```powershell
.\cleanup-docker.ps1
```

**Windows (Command Prompt):**
```cmd
cleanup-docker.bat
```

## What Gets Cleaned Up

### Containers
- All containers with "whisperengine" in the name
- Containers from compose files (quickstart, containerized, default)

### Volumes
- `whisperengine_postgres_data`
- `whisperengine_qdrant_data`
- `whisperengine_influxdb_data`
- `whisperengine_whisperengine_logs`
- `whisperengine_influxdb_config`
- `whisperengine_grafana_data`
- Plus any other volumes containing "whisperengine"

### Networks
- `whisperengine-network`
- `whisperengine_default`

### Dangling Resources
- Unused volumes
- Orphaned build cache

## After Cleanup

Once cleanup is complete, you can start fresh:

### Option 1: Run quickstart setup (Recommended)

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

**Windows (PowerShell - Recommended):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

**Windows (Command Prompt):**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

### Option 2: If you already have config files

If you already have `docker-compose.quickstart.yml` and `.env` files:
```bash
docker-compose -f docker-compose.quickstart.yml up -d
```

## Troubleshooting

### Permission Denied (Linux/macOS)
Make the script executable:
```bash
chmod +x cleanup-docker.sh
./cleanup-docker.sh
```

### Execution Policy Error (Windows PowerShell)
If you get an execution policy error, run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try running the cleanup script again:
```powershell
.\cleanup-docker.ps1
```

### Docker Not Running
Ensure Docker Desktop is running before executing cleanup scripts.

### Some Volumes Won't Delete
If volumes are in use by running containers, stop all containers first:
```bash
docker stop $(docker ps -aq)
```

Then run the cleanup script again.

## Safe to Run Multiple Times
All cleanup scripts are safe to run multiple times. They will:
- Skip resources that don't exist (no errors)
- Only remove WhisperEngine-related resources
- Leave other Docker containers/volumes untouched

## Need Help?
If you encounter issues with cleanup scripts, please report them at:
https://github.com/whisperengine-ai/whisperengine/issues
