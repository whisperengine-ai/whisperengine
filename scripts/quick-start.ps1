# WhisperEngine Quick Start - Windows PowerShell Edition
# =============================================================================
# Get WhisperEngine (Dream of the Endless) running in under 2 minutes!
# 
# Usage:
#   .\quick-start.ps1                    # Use latest version
#   .\quick-start.ps1 -Version v1.0.0    # Use specific version
#   .\quick-start.ps1 -Help              # Show help
# =============================================================================

param(
    [string]$Version = "latest",
    [switch]$Help,
    [switch]$Dev
)

# Colors for output (PowerShell compatible)
function Write-Status { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Blue }
function Write-Dream { param($Message) Write-Host "🎭 $Message" -ForegroundColor Magenta }

if ($Help) {
    Write-Dream "WhisperEngine Quick Start (Windows PowerShell)"
    Write-Host ""
    Write-Host "USAGE:"
    Write-Host "  .\quick-start.ps1                    # Latest stable version"
    Write-Host "  .\quick-start.ps1 -Version v1.0.0    # Specific version"
    Write-Host "  .\quick-start.ps1 -Dev               # Development version"
    Write-Host "  .\quick-start.ps1 -Help              # Show this help"
    Write-Host ""
    Write-Host "REQUIREMENTS:"
    Write-Host "  - Docker Desktop for Windows (running)"
    Write-Host "  - PowerShell 5.1 or later"
    Write-Host "  - Discord bot token"
    Write-Host ""
    Write-Host "WHAT IT DOES:"
    Write-Host "  - Downloads WhisperEngine configuration"
    Write-Host "  - Sets up environment files"
    Write-Host "  - Starts all services with Docker Compose"
    Write-Host "  - Provides monitoring commands"
    Write-Host ""
    Write-Host "🎭 Dream of the Endless awaits in the realm of containers..."
    exit 0
}

Write-Dream "WhisperEngine Lightning Quick Start (Windows)"
Write-Host "=============================================="
Write-Host ""

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error "PowerShell 5.1 or later required. Current: $($PSVersionTable.PSVersion)"
    Write-Info "Update PowerShell: https://aka.ms/powershell"
    exit 1
}

# Check Docker availability
Write-Info "Checking Docker availability..."
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Status "Docker found: $dockerVersion"
} catch {
    Write-Error "Docker not found or not running"
    Write-Info "Please install and start Docker Desktop for Windows:"
    Write-Info "  Download: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    Write-Info "  Make sure Docker Desktop is running before trying again"
    exit 1
}

# Check Docker daemon
try {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Status "Docker daemon is running"
} catch {
    Write-Error "Docker daemon not accessible"
    Write-Info "Please start Docker Desktop and try again"
    exit 1
}

# Determine version
if ($Dev) {
    $Version = "develop"
    Write-Info "Using development version"
} else {
    Write-Info "Using version: $Version"
}

# Create project directory
$projectDir = "whisperengine-$Version"
Write-Dream "Creating WhisperEngine project: $projectDir"

if (Test-Path $projectDir) {
    Write-Warning "Directory '$projectDir' already exists"
    $response = Read-Host "Remove it and continue? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        try {
            Remove-Item -Recurse -Force $projectDir
            Write-Status "Removed existing directory"
        } catch {
            Write-Error "Failed to remove directory: $projectDir"
            exit 1
        }
    } else {
        Write-Error "Cancelled by user"
        exit 1
    }
}

try {
    New-Item -ItemType Directory -Name $projectDir | Out-Null
    Set-Location $projectDir
    Write-Status "Created project directory"
} catch {
    Write-Error "Failed to create directory: $projectDir"
    exit 1
}

# Download configuration files
Write-Info "Downloading WhisperEngine configuration files..."

$baseUrl = "https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main"
$quickStartUrl = "$baseUrl/docker/quick-start"

$files = @{
    "docker-compose.yml" = "$quickStartUrl/docker-compose.yml"
    ".env.minimal" = "$quickStartUrl/.env.minimal" 
    "README.md" = "$quickStartUrl/README.md"
}

foreach ($file in $files.GetEnumerator()) {
    try {
        Write-Host "  Downloading $($file.Name)..." -NoNewline
        Invoke-WebRequest -Uri $file.Value -OutFile $file.Name -UseBasicParsing
        Write-Host " ✅" -ForegroundColor Green
    } catch {
        Write-Host " ❌" -ForegroundColor Red
        Write-Error "Failed to download $($file.Name) from $($file.Value)"
        Write-Info "Please check your internet connection and try again"
        exit 1
    }
}

Write-Status "Downloaded all configuration files"

# Set up environment file
Write-Info "Setting up environment configuration..."

if (-not (Test-Path ".env")) {
    try {
        Copy-Item ".env.minimal" ".env"
        # Also create a visible copy for easy reference
        Copy-Item ".env.minimal" "env.example"
        Write-Status "Created .env (hidden) and env.example (visible copy)"
    } catch {
        Write-Error "Failed to create .env file"
        exit 1
    }
    
    Write-Host ""
    Write-Warning "IMPORTANT: Configure your Discord bot token!"
    Write-Info "Required environment variable:"
    Write-Host "   DISCORD_BOT_TOKEN=your_discord_bot_token_here" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Configuration files created:"
    Write-Host "   .env           # Hidden file used by Docker (edit this one)" -ForegroundColor Cyan
    Write-Host "   env.example    # Visible copy for reference" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Optional: Configure your LLM provider (LM Studio, Ollama, etc.)"
    Write-Host ""
    
    # Attempt to open .env in default editor
    Write-Info "Opening .env in your default editor..."
    try {
        if (Get-Command "code" -ErrorAction SilentlyContinue) {
            # VS Code available
            Start-Process "code" ".env"
            Write-Status "Opened in VS Code"
        } elseif (Get-Command "notepad.exe" -ErrorAction SilentlyContinue) {
            # Fallback to Notepad
            Start-Process "notepad.exe" ".env"
            Write-Status "Opened in Notepad"
        } else {
            Write-Info "Please edit .env file manually to add your Discord bot token"
        }
    } catch {
        Write-Info "Please edit .env file manually to add your Discord bot token"
    }
    
    Write-Host ""
    Write-Host "Press Enter after configuring your .env file..." -ForegroundColor Yellow
    Read-Host
} else {
    Write-Status ".env file already exists"
}

# Validate environment
if ((Get-Content ".env" | Select-String "DISCORD_BOT_TOKEN=your_discord_bot_token_here") -or 
    -not (Get-Content ".env" | Select-String "DISCORD_BOT_TOKEN=.+")) {
    Write-Warning "Discord bot token not configured in .env file"
    Write-Info "The bot will not work without a valid Discord bot token"
    Write-Info "Get one at: https://discord.com/developers/applications"
}

# Start WhisperEngine services
Write-Dream "Starting WhisperEngine services..."
Write-Info "This may take a few minutes for the first run (downloading images)..."
Write-Host ""

try {
    # Pull latest images
    Write-Info "Pulling latest Docker images..."
    docker-compose pull
    if ($LASTEXITCODE -ne 0) { throw "Docker pull failed" }
    
    # Start services
    Write-Info "Starting services in background..."
    docker-compose up -d
    if ($LASTEXITCODE -ne 0) { throw "Docker compose up failed" }
    
    # Wait a moment for services to initialize
    Start-Sleep -Seconds 3
    
    Write-Host ""
    Write-Dream "✨ WhisperEngine is starting!"
    Write-Host ""
    
    # Show service status
    Write-Info "Service status:"
    docker-compose ps
    
    Write-Host ""
    Write-Status "🎉 Setup complete!"
    Write-Host ""
    Write-Info "Useful commands:"
    Write-Host "  Monitor logs:     docker-compose logs -f whisperengine" -ForegroundColor Cyan
    Write-Host "  View all logs:    docker-compose logs" -ForegroundColor Cyan
    Write-Host "  Stop services:    docker-compose down" -ForegroundColor Cyan
    Write-Host "  Restart:          docker-compose restart" -ForegroundColor Cyan
    Write-Host "  Update images:    docker-compose pull && docker-compose up -d" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "Configuration files:"
    Write-Host "  Environment:      .env (hidden), env.example (visible)" -ForegroundColor Cyan
    Write-Host "  Bot personality:  prompts/default.md" -ForegroundColor Cyan  
    Write-Host "  Services:         docker-compose.yml" -ForegroundColor Cyan
    Write-Host ""
    Write-Dream "🎭 Dream of the Endless now dwells in your Discord server..."
    Write-Dream "The realm of conversations and stories awaits!"
    
} catch {
    Write-Error "Failed to start WhisperEngine services"
    Write-Info "Error details: $($_.Exception.Message)"
    Write-Host ""
    Write-Info "Troubleshooting steps:"
    Write-Host "  1. Ensure Docker Desktop is running"
    Write-Host "  2. Check Docker has sufficient resources (4GB+ RAM)"
    Write-Host "  3. Verify internet connection for image downloads"
    Write-Host "  4. Check logs: docker-compose logs"
    Write-Host ""
    Write-Info "For help, visit: https://github.com/WhisperEngine-AI/whisperengine/wiki"
    exit 1
}

Write-Host ""
Write-Info "🎭 WhisperEngine Quick Start completed successfully!"