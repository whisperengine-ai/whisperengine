# WhisperEngine Containerized Setup Script for Windows PowerShell
# Downloads only necessary files - no source code required

Write-Host "🐳 Starting WhisperEngine..." -ForegroundColor Cyan
Write-Host "   This may take 2-3 minutes on first run (downloading container images)"
Write-Host "   ✨ Containers include pre-downloaded AI models (~400MB):" -ForegroundColor Yellow
Write-Host "     • FastEmbed: sentence-transformers/all-MiniLM-L6-v2 (embeddings)"
Write-Host "     • RoBERTa: cardiffnlp emotion analysis (11 emotions)"
Write-Host "   🚀 No model downloads needed - instant startup!" -ForegroundColor Green
Write-Host ""

Write-Host ""
Write-Host "🎭 WhisperEngine Containerized Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "No source code download required!"
Write-Host "Uses pre-built Docker Hub containers"
Write-Host ""

# Check if Docker is running
Write-Host "[SETUP] Checking Docker..." -ForegroundColor Blue
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not responding"
    }
    Write-Host "[SUCCESS] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Detect if we're running inside the WhisperEngine repository
if ((Test-Path "docker-compose.containerized.yml") -and (Test-Path ".env.containerized.template")) {
    Write-Host "[SETUP] Running from WhisperEngine repository directory" -ForegroundColor Blue
    $installDir = "."
    $composeFile = "docker-compose.containerized.yml"
    $envTemplate = ".env.containerized.template"
} else {
    # Create WhisperEngine directory for fresh installation
    $installDir = "whisperengine"
    $composeFile = "docker-compose.yml"
    $envTemplate = ".env.template"
    
    if (Test-Path $installDir) {
        Write-Host "[WARNING] Directory '$installDir' already exists" -ForegroundColor Yellow
        $reply = Read-Host "Remove existing directory and continue? (y/N)"
        if ($reply -eq "y" -or $reply -eq "Y") {
            Remove-Item -Recurse -Force $installDir
            Write-Host "[SETUP] Removed existing directory" -ForegroundColor Blue
        } else {
            Write-Host "[ERROR] Setup cancelled" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
    
    New-Item -ItemType Directory -Path $installDir | Out-Null
}

Set-Location $installDir
Write-Host "[SUCCESS] Using directory: $PWD" -ForegroundColor Green

if ($installDir -ne ".") {
    # Download Docker Compose file
    Write-Host "[SETUP] Downloading Docker Compose configuration..." -ForegroundColor Blue
    $composeUrl = "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/docker-compose.containerized.yml"
    try {
        Invoke-WebRequest -Uri $composeUrl -OutFile "docker-compose.yml" -UseBasicParsing -ErrorAction Stop
        Write-Host "[SUCCESS] Downloaded docker-compose.yml" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to download Docker Compose file: $_" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Download environment template
    Write-Host "[SETUP] Downloading configuration template..." -ForegroundColor Blue
    $envUrl = "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/.env.containerized.template"
    try {
        Invoke-WebRequest -Uri $envUrl -OutFile ".env.template" -UseBasicParsing -ErrorAction Stop
        Write-Host "[SUCCESS] Downloaded .env.template" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to download environment template: $_" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[SUCCESS] Using existing repository files" -ForegroundColor Green
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "[SETUP] Creating configuration file..." -ForegroundColor Blue
    Copy-Item $envTemplate ".env"
    Write-Host "[SUCCESS] Created .env file with default settings (LM Studio)" -ForegroundColor Green
    Write-Host "[SETUP] 💡 Using LM Studio as default LLM (free, local)" -ForegroundColor Yellow
    Write-Host "[SETUP] 🔧 You can edit .env later to customize settings" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "[SUCCESS] Configuration file found" -ForegroundColor Green

# Check if API key is needed (only for cloud providers)
$envContent = Get-Content ".env" -Raw
$llmClientType = "lmstudio"
# Use simpler regex pattern that doesn't require special escaping
if ($envContent -match 'LLM_CLIENT_TYPE=(\S+)') {
    $llmClientType = $Matches[1].Trim()
}

$needsApiKey = $false
if ($llmClientType -eq "openrouter" -or $llmClientType -eq "openai") {
    if ($envContent -notmatch "LLM_CHAT_API_KEY=.+\S") {
        $needsApiKey = $true
    }
}

if ($needsApiKey) {
    Write-Host ""
    Write-Host "⚠️  CONFIGURATION REQUIRED" -ForegroundColor Yellow
    Write-Host "=====================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Your configuration uses $llmClientType but no API key is set." -ForegroundColor Yellow
    Write-Host ""
    
    if ($llmClientType -eq "openrouter") {
        Write-Host "📝 To get an OpenRouter API key (recommended):" -ForegroundColor Cyan
        Write-Host "   1. Visit: https://openrouter.ai/keys"
        Write-Host "   2. Sign up (free tier available)"
        Write-Host "   3. Create an API key"
        Write-Host "   4. Add it to your .env file: LLM_CHAT_API_KEY=your_key_here"
    } elseif ($llmClientType -eq "openai") {
        Write-Host "📝 To get an OpenAI API key:" -ForegroundColor Cyan
        Write-Host "   1. Visit: https://platform.openai.com/api-keys"
        Write-Host "   2. Create an account"
        Write-Host "   3. Create an API key"
        Write-Host "   4. Add it to your .env file: LLM_CHAT_API_KEY=your_key_here"
    }
    
    Write-Host ""
    Write-Host "💡 Alternative: Use LM Studio (free, local, no API key needed)" -ForegroundColor Yellow
    Write-Host "   1. Download LM Studio: https://lmstudio.ai"
    Write-Host "   2. Change LLM_CLIENT_TYPE=lmstudio in your .env"
    Write-Host ""
    
    Write-Host "Opening .env file for editing..." -ForegroundColor Blue
    Start-Sleep -Seconds 2
    
    # Open .env in default text editor
    if (Get-Command notepad -ErrorAction SilentlyContinue) {
        Start-Process notepad ".env"
    } else {
        Write-Host "[WARNING] Could not open text editor automatically" -ForegroundColor Yellow
        Write-Host "Please edit .env manually before continuing" -ForegroundColor Yellow
    }
    
    Write-Host ""
    $reply = Read-Host "Press Enter when you've added your API key (or 'skip' to continue anyway)"
    if ($reply -eq "skip") {
        Write-Host "[WARNING] Continuing without API key - services may fail to start" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[SETUP] Starting WhisperEngine services..." -ForegroundColor Blue
Write-Host "[INFO] This will:" -ForegroundColor Cyan
Write-Host "  • Pull Docker containers from Docker Hub (~1-2GB first time)"
Write-Host "  • Start PostgreSQL database"
Write-Host "  • Start Qdrant vector database"
Write-Host "  • Start InfluxDB time-series database"
Write-Host "  • Run database migrations"
Write-Host "  • Start WhisperEngine assistant bot"
Write-Host "  • Start Web UI"
Write-Host ""

# Start services
try {
    docker-compose -f $composeFile up -d
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to start services: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "  • Ensure Docker Desktop is running"
    Write-Host "  • Check if ports are available (9090, 3001, 5432, 6333, 8086)"
    Write-Host "  • Try running cleanup script first:"
    Write-Host '    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.ps1" -OutFile "cleanup.ps1"; .\cleanup.ps1'
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[SUCCESS] Services starting..." -ForegroundColor Green
Write-Host ""
Write-Host "⏳ Waiting for services to initialize (30 seconds)..." -ForegroundColor Yellow

# Wait for services to be ready
Start-Sleep -Seconds 30

# Check health
Write-Host ""
Write-Host "[SETUP] Checking service health..." -ForegroundColor Blue

try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "[SUCCESS] WhisperEngine API is healthy!" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] API not responding yet - may need more time to initialize" -ForegroundColor Yellow
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3001" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "[SUCCESS] Web UI is healthy!" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] Web UI not responding yet - may need more time to initialize" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✨ WhisperEngine is running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Access your WhisperEngine:" -ForegroundColor Cyan
Write-Host "   • Web Interface: http://localhost:3001" -ForegroundColor Yellow
Write-Host "   • Chat API: http://localhost:9090/api/chat" -ForegroundColor Yellow
Write-Host "   • Health Check: http://localhost:9090/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 Next steps:" -ForegroundColor Cyan
Write-Host "   • Open http://localhost:3001 to create characters" -ForegroundColor White
Write-Host "   • Test the API with curl or Postman" -ForegroundColor White
Write-Host "   • Check logs: docker logs whisperengine-assistant" -ForegroundColor White
Write-Host ""
Write-Host "🛠️  Useful commands:" -ForegroundColor Cyan
Write-Host "   • Stop: docker-compose -f $composeFile down" -ForegroundColor White
Write-Host "   • Restart: docker-compose -f $composeFile restart" -ForegroundColor White
Write-Host "   • View logs: docker-compose -f $composeFile logs -f" -ForegroundColor White
Write-Host ""
Write-Host "📖 Documentation: https://github.com/whisperengine-ai/whisperengine" -ForegroundColor Cyan
Write-Host ""

# Open browser
Write-Host "Opening web interface in browser..." -ForegroundColor Blue
Start-Sleep -Seconds 2
Start-Process "http://localhost:3001"

Write-Host ""
Write-Host "Press Enter to exit" -ForegroundColor Gray
Read-Host
