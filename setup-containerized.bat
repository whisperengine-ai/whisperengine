@echo off
REM WhisperEngine Containerized Setup Script for Windows
REM Downloads only necessary files - no echo.
setlocal enabledelayedexpansion

echo 🐳 Starting WhisperEngine...
echo    This may take 2-3 minutes on first run (downloading container images)
echo    ✨ Containers include pre-downloaded AI models (~400MB):
echo      • FastEmbed: sentence-transformers/all-MiniLM-L6-v2 (embeddings)
echo      • RoBERTa: cardiffnlp emotion analysis (11 emotions)
echo    🚀 No model downloads needed - instant startup!
echo.

echo.
echo 🎭 WhisperEngine Containerized Setup
echo =====================================
echo No source code download required!
echo Uses pre-built Docker Hub containers
echo.

REM Check if Docker is running
echo [SETUP] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [SUCCESS] Docker is running

REM Detect if we're running inside the WhisperEngine repository
if exist "docker-compose.containerized.yml" if exist ".env.containerized.template" (
    echo [SETUP] Running from WhisperEngine repository directory
    set INSTALL_DIR=.
    set COMPOSE_FILE=docker-compose.containerized.yml
    set ENV_TEMPLATE=.env.containerized.template
) else (
    REM Create WhisperEngine directory for fresh installation
    set INSTALL_DIR=whisperengine
    set COMPOSE_FILE=docker-compose.yml
    set ENV_TEMPLATE=.env.template
    
    if exist "%INSTALL_DIR%" (
        echo [WARNING] Directory '%INSTALL_DIR%' already exists
        set /p "REPLY=Remove existing directory and continue? (y/N): "
        if /i "!REPLY!" equ "y" (
            rmdir /s /q "%INSTALL_DIR%"
            echo [SETUP] Removed existing directory
        ) else (
            echo [ERROR] Setup cancelled
            pause
            exit /b 1
        )
    )
    
    mkdir "%INSTALL_DIR%"
    if not exist "%INSTALL_DIR%" (
        echo [ERROR] Failed to create directory %INSTALL_DIR%
        pause
        exit /b 1
    )
)

cd "%INSTALL_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to change to directory !INSTALL_DIR!
    pause
    exit /b 1
)
echo %CD%
echo [SUCCESS] Using directory: %CD%

if not "!INSTALL_DIR!" == "." (
    REM Download Docker Compose file
    echo [SETUP] Downloading Docker Compose configuration...
    powershell -Command "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/docker-compose.containerized.yml' -OutFile 'docker-compose.yml' -UseBasicParsing -ErrorAction Stop } catch { Write-Host 'Download failed:' $_.Exception.Message; exit 1 }"
    if errorlevel 1 (
        echo [ERROR] Failed to download Docker Compose file
        echo [ERROR] Please check your internet connection and try again
        pause
        exit /b 1
    )
    echo [SUCCESS] Downloaded docker-compose.yml

    REM Download environment template
    echo [SETUP] Downloading configuration template...
    powershell -Command "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/.env.containerized.template' -OutFile '.env.template' -UseBasicParsing -ErrorAction Stop } catch { Write-Host 'Download failed:' $_.Exception.Message; exit 1 }"
    if errorlevel 1 (
        echo [ERROR] Failed to download environment template
        echo [ERROR] Please check your internet connection and try again
        pause
        exit /b 1
    )
    echo [SUCCESS] Downloaded .env.template
) else (
    echo [SUCCESS] Using existing repository files
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo [SETUP] Creating configuration file...
    copy "!ENV_TEMPLATE!" .env >nul
    echo [SUCCESS] Created .env file with default settings (LM Studio)
    echo [SETUP] 💡 Using LM Studio as default LLM (free, local)
    echo [SETUP] 🔧 You can edit .env later to customize settings
    echo.
)

echo [SUCCESS] Configuration file found

REM Check if API key is needed (only for cloud providers)
findstr /c:"LLM_CLIENT_TYPE=lmstudio" .env >nul
if not errorlevel 1 (
    echo [SUCCESS] Using local LM Studio (no API key required)
    goto :continue_setup
)

findstr /c:"LLM_CLIENT_TYPE=ollama" .env >nul
if not errorlevel 1 (
    echo [SUCCESS] Using local Ollama (no API key required)
    goto :continue_setup
)

findstr /c:"your_api_key_here" .env >nul
if not errorlevel 1 (
    echo [WARNING] Please set your LLM_CHAT_API_KEY in the .env file for cloud providers
    echo    Edit .env and replace 'your_api_key_here' with your actual API key
    echo.
    echo    Get API keys from:
    echo    • OpenRouter: https://openrouter.ai (recommended for beginners)
    echo    • OpenAI: https://platform.openai.com
    echo.
    echo    💡 Tip: Use LM Studio instead (no API key needed):
    echo      Set LLM_CLIENT_TYPE=lmstudio in .env
    echo.
    pause
    exit /b 1
)

:continue_setup

echo [SUCCESS] API key configured

REM Create logs directory
mkdir logs 2>nul
echo [SUCCESS] Created logs directory

echo.
echo [SETUP] 🐳 Starting WhisperEngine...
echo    This may take 2-3 minutes on first run (downloading container images)
echo.

REM Pull latest images first
echo [SETUP] Pulling latest container images...
docker-compose -f "!COMPOSE_FILE!" pull

REM Start WhisperEngine
echo [SETUP] Starting services...
docker-compose -f "!COMPOSE_FILE!" up -d

echo.
echo [SETUP] ⏳ Waiting for services to start...

REM Wait for services to be healthy
set max_attempts=30
set attempt=0

:wait_loop
if !attempt! geq !max_attempts! goto timeout

REM Check if services are ready
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:3001' -UseBasicParsing | Out-Null; Invoke-WebRequest -Uri 'http://localhost:9090/health' -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto services_ready

set /a attempt+=1
echo    Waiting... (!attempt!/!max_attempts!)
timeout /t 10 /nobreak >nul
goto wait_loop

:timeout
echo [ERROR] Services didn't start properly. Check logs:
echo    docker-compose -f "!COMPOSE_FILE!" logs
pause
exit /b 1

:services_ready
echo.
echo [SUCCESS] 🎉 WhisperEngine is ready!
echo ================================
echo.
echo 🌐 Web UI:     http://localhost:3001
echo 🤖 Chat API:   http://localhost:9090/api/chat
echo 📊 Health:     http://localhost:9090/health
echo 📈 InfluxDB:   http://localhost:8086 (Metrics & Machine Learning)
echo.
echo ✨ Features:
echo • Create AI characters via web interface
echo • Persistent memory and conversation history
echo • Machine learning & temporal intelligence (InfluxDB)
echo • RESTful Chat APIs for integration
echo • Optional Discord bot functionality
echo.
echo 📖 Next steps:
echo 1. Visit http://localhost:3001 to create your first character
echo 2. Test the chat API with curl or your application
echo 3. Edit .env file to customize LLM settings if needed
echo 4. Enable Discord integration if desired
echo.
echo 🔧 Management commands:
echo    docker-compose -f !COMPOSE_FILE! stop     # Stop WhisperEngine
echo    docker-compose -f !COMPOSE_FILE! start    # Restart WhisperEngine
echo    docker-compose -f !COMPOSE_FILE! logs -f  # View live logs
echo    docker-compose -f !COMPOSE_FILE! down     # Stop and remove containers
echo.

REM Auto-open browser
echo [SETUP] 🔗 Opening web interface...
timeout /t 2 /nobreak >nul
start http://localhost:3001

echo [SUCCESS] Setup complete! Enjoy your AI character platform! 🎭
pause