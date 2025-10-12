# WhisperEngine Docker Cleanup Script (Windows PowerShell)
# Removes all containers, volumes, and networks for a fresh start

# Colors for output
$ErrorActionPreference = "SilentlyContinue"

function Write-Step {
    param($Message)
    Write-Host "🔧 $Message" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

Write-Host ""
Write-Host "🧹 WhisperEngine Docker Cleanup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "This will remove ALL WhisperEngine containers, volumes, and data"
Write-Host ""

Write-Warning "This will DELETE:"
Write-Warning "  • All WhisperEngine containers"
Write-Warning "  • All database data (PostgreSQL)"
Write-Warning "  • All vector memory data (Qdrant)"
Write-Warning "  • All time-series data (InfluxDB)"
Write-Warning "  • All conversation logs"
Write-Warning ""
Write-Warning "You will need to reconfigure your LLM settings after cleanup!"
Write-Host ""

$confirm = Read-Host "Are you sure you want to continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Cleanup cancelled"
    exit 0
}

Write-Host ""
Write-Step "Stopping all WhisperEngine containers..."

# First, try to stop using any compose files we can find
$composeFiles = @(
    "docker-compose.quickstart.yml",
    "docker-compose.containerized.yml",
    "docker-compose.yml"
)

foreach ($composeFile in $composeFiles) {
    if (Test-Path $composeFile) {
        Write-Success "Stopping containers from $composeFile..."
        docker-compose -f $composeFile down 2>$null
    }
}

# Then stop any containers with whisperengine in the name
$containers = docker ps -aq --filter "name=whisperengine" 2>$null
if ($containers) {
    foreach ($container in $containers) {
        if ($container) {
            $containerName = docker inspect --format '{{.Name}}' $container 2>$null
            $containerName = $containerName.TrimStart('/')
            docker stop $container 2>$null | Out-Null
            docker rm $container 2>$null | Out-Null
            Write-Success "Removed container: $containerName"
        }
    }
}

Write-Step "Removing WhisperEngine volumes..."

# First, get all volumes with whisperengine in the name
$volumes = docker volume ls --format "{{.Name}}" 2>$null | Select-String -Pattern "whisperengine" -CaseSensitive:$false

if ($volumes) {
    foreach ($volume in $volumes) {
        $volumeName = $volume.ToString().Trim()
        if ($volumeName) {
            docker volume rm $volumeName 2>$null | Out-Null
            Write-Success "Removed volume: $volumeName"
        }
    }
} else {
    Write-Success "No WhisperEngine volumes found"
}

# Also try common volume name patterns without prefix
$commonVolumes = @("postgres_data", "qdrant_data", "influxdb_data", "whisperengine_logs", "grafana_data")
foreach ($volume in $commonVolumes) {
    $exists = docker volume ls --format "{{.Name}}" 2>$null | Select-String -Pattern "^$volume$" -Quiet
    if ($exists) {
        docker volume rm $volume 2>$null | Out-Null
        Write-Success "Removed volume: $volume"
    }
}

Write-Step "Removing WhisperEngine networks..."

# Remove networks
$networks = @("whisperengine-network", "whisperengine_default")
foreach ($network in $networks) {
    $exists = docker network ls --format "{{.Name}}" 2>$null | Select-String -Pattern $network -Quiet
    if ($exists) {
        docker network rm $network 2>$null | Out-Null
        Write-Success "Removed network: $network"
    }
}

Write-Step "Cleaning up dangling resources..."

# Remove dangling volumes
docker volume prune -f 2>$null | Out-Null

Write-Host ""
Write-Success "Cleanup complete! 🎉"
Write-Host ""
Write-Host "📋 Next steps:"
Write-Host ""
Write-Host "1. Run the quickstart setup again:" -ForegroundColor Cyan
Write-Host "   .\quickstart-setup.ps1" -ForegroundColor Blue
Write-Host ""
Write-Host "2. Or if you already have the files, start fresh:" -ForegroundColor Cyan
Write-Host "   docker-compose -f docker-compose.quickstart.yml up -d" -ForegroundColor Blue
Write-Host ""
Write-Host "💡 You'll need to reconfigure your LLM settings in .env" -ForegroundColor Yellow
Write-Host ""
