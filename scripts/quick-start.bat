@echo off
REM =============================================================================
REM WhisperEngine Quick Start - Windows Batch Edition
REM =============================================================================
REM Get WhisperEngine (Dream of the Endless) running in under 2 minutes!
REM 
REM Usage:
REM   quick-start.bat         - Use latest version
REM   quick-start.bat v1.0.0  - Use specific version
REM   quick-start.bat dev     - Use development version
REM =============================================================================

setlocal enabledelayedexpansion

REM Set version parameter
set VERSION=%1
if "%VERSION%"=="" set VERSION=latest
if "%VERSION%"=="dev" set VERSION=develop

echo 🎭 WhisperEngine Lightning Quick Start (Windows)
echo ==============================================
echo.

REM Check for help request
if "%1"=="help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="--help" goto :show_help

REM Check Docker availability
echo ℹ️  Checking Docker availability...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found or not running
    echo ℹ️  Please install and start Docker Desktop for Windows:
    echo    Download: https://desktop.docker.com/win/main/amd64/Docker Desktop Installer.exe
    echo    Make sure Docker Desktop is running before trying again
    pause
    exit /b 1
)

REM Get Docker version
for /f "delims=" %%i in ('docker --version 2^>nul') do set DOCKER_VERSION=%%i
echo ✅ Docker found: !DOCKER_VERSION!

REM Check Docker daemon
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker daemon not accessible
    echo ℹ️  Please start Docker Desktop and try again
    pause
    exit /b 1
)
echo ✅ Docker daemon is running

echo ℹ️  Using version: %VERSION%

REM Create project directory
set PROJECT_DIR=whisperengine-%VERSION%
echo 🎭 Creating WhisperEngine project: %PROJECT_DIR%

if exist "%PROJECT_DIR%" (
    echo ⚠️  Directory %PROJECT_DIR% already exists
    set /p "RESPONSE=Remove it and continue? (y/N): "
    if /i "!RESPONSE!"=="y" (
        rmdir /s /q "%PROJECT_DIR%" 2>nul
        if exist "%PROJECT_DIR%" (
            echo ❌ Failed to remove directory: %PROJECT_DIR%
            pause
            exit /b 1
        )
        echo ✅ Removed existing directory
    ) else (
        echo ❌ Cancelled by user
        pause
        exit /b 1
    )
)

mkdir "%PROJECT_DIR%" 2>nul
if errorlevel 1 (
    echo ❌ Failed to create directory: %PROJECT_DIR%
    pause
    exit /b 1
)

cd "%PROJECT_DIR%"
echo ✅ Created project directory

REM Download configuration files using PowerShell
echo ℹ️  Downloading WhisperEngine configuration files...

set BASE_URL=https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main
set QUICKSTART_URL=%BASE_URL%/docker/quick-start

REM Download docker-compose.yml
echo   Downloading docker-compose.yml...
powershell -Command "try { Invoke-WebRequest -Uri '%QUICKSTART_URL%/docker-compose.yml' -OutFile 'docker-compose.yml' -UseBasicParsing; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo ❌ Failed to download docker-compose.yml
    goto :download_error
)

REM Download .env.minimal
echo   Downloading .env.minimal...
powershell -Command "try { Invoke-WebRequest -Uri '%QUICKSTART_URL%/.env.minimal' -OutFile '.env.minimal' -UseBasicParsing; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo ❌ Failed to download .env.minimal
    goto :download_error
)

REM Download system_prompt.md
echo   Downloading system_prompt.md...
powershell -Command "try { Invoke-WebRequest -Uri '%BASE_URL%/system_prompt.md' -OutFile 'system_prompt.md' -UseBasicParsing; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo ❌ Failed to download system_prompt.md
    goto :download_error
)

REM Download README.md
echo   Downloading README.md...
powershell -Command "try { Invoke-WebRequest -Uri '%QUICKSTART_URL%/README.md' -OutFile 'README.md' -UseBasicParsing; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo ❌ Failed to download README.md
    goto :download_error
)

echo ✅ Downloaded all configuration files

REM Set up environment file
echo ℹ️  Setting up environment configuration...

if not exist ".env" (
    copy ".env.minimal" ".env" >nul 2>&1
    if errorlevel 1 (
        echo ❌ Failed to create .env file
        pause
        exit /b 1
    )
    REM Also create a visible copy for easy reference
    copy ".env.minimal" "env.example" >nul 2>&1
    echo ✅ Created .env (hidden) and env.example (visible copy)
    echo.
    echo ⚠️  IMPORTANT: Configure your Discord bot token!
    echo ℹ️  Required environment variable:
    echo    DISCORD_BOT_TOKEN=your_discord_bot_token_here
    echo.
    echo ℹ️  Configuration files created:
    echo    .env           # Hidden file used by Docker (edit this one^)
    echo    env.example    # Visible copy for reference
    echo.
    echo ℹ️  Optional: Configure your LLM provider (LM Studio, Ollama, etc.^)
    echo.
    echo ℹ️  Opening .env in your default editor...
    
    REM Try to open with best available editor
    where code >nul 2>&1
    if not errorlevel 1 (
        start "" code ".env"
        echo ✅ Opened in VS Code
    ) else (
        start "" notepad ".env"
        echo ✅ Opened in Notepad
    )
    
    echo.
    echo Press any key after configuring your .env file...
    pause >nul
) else (
    echo ✅ .env file already exists
)

REM Start WhisperEngine services
echo 🎭 Starting WhisperEngine services...
echo ℹ️  This may take a few minutes for the first run (downloading images^)...
echo.

REM Pull latest images
echo ℹ️  Pulling latest Docker images...
docker-compose pull
if errorlevel 1 (
    echo ❌ Failed to pull Docker images
    goto :docker_error
)

REM Start services
echo ℹ️  Starting services in background...
docker-compose up -d
if errorlevel 1 (
    echo ❌ Failed to start services
    goto :docker_error
)

REM Wait for services to initialize
timeout /t 3 /nobreak >nul 2>&1

echo.
echo 🎭 ✨ WhisperEngine is starting!
echo.

REM Show service status
echo ℹ️  Service status:
docker-compose ps

echo.
echo ✅ 🎉 Setup complete!
echo.
echo ℹ️  Useful commands:
echo   Monitor logs:     docker-compose logs -f whisperengine
echo   View all logs:    docker-compose logs
echo   Stop services:    docker-compose down
echo   Restart:          docker-compose restart
echo   Update images:    docker-compose pull ^&^& docker-compose up -d
echo.
echo ℹ️  Configuration files:
echo   Environment:      .env (hidden), env.example (visible)
echo   Bot personality:  system_prompt.md
echo   Services:         docker-compose.yml
echo.
echo 🎭 Dream of the Endless now dwells in your Discord server...
echo 🎭 The realm of conversations and stories awaits!
echo.
echo ℹ️  🎭 WhisperEngine Quick Start completed successfully!
pause
exit /b 0

:show_help
echo 🎭 WhisperEngine Quick Start (Windows Batch)
echo.
echo USAGE:
echo   quick-start.bat              # Latest stable version
echo   quick-start.bat v1.0.0       # Specific version
echo   quick-start.bat dev          # Development version
echo   quick-start.bat help         # Show this help
echo.
echo REQUIREMENTS:
echo   - Docker Desktop for Windows (running^)
echo   - Windows Command Prompt with PowerShell access
echo   - Discord bot token
echo.
echo WHAT IT DOES:
echo   - Downloads WhisperEngine configuration
echo   - Sets up environment files
echo   - Starts all services with Docker Compose
echo   - Provides monitoring commands
echo.
echo 🎭 Dream of the Endless awaits in the realm of containers...
pause
exit /b 0

:download_error
echo ❌ Failed to download configuration files
echo ℹ️  Please check your internet connection and try again
echo ℹ️  For help, visit: https://github.com/WhisperEngine-AI/whisperengine/wiki
pause
exit /b 1

:docker_error
echo ❌ Failed to start WhisperEngine services
echo.
echo ℹ️  Troubleshooting steps:
echo   1. Ensure Docker Desktop is running
echo   2. Check Docker has sufficient resources (4GB+ RAM^)
echo   3. Verify internet connection for image downloads
echo   4. Check logs: docker-compose logs
echo.
echo ℹ️  For help, visit: https://github.com/WhisperEngine-AI/whisperengine/wiki
pause
exit /b 1