@echo off
REM WhisperEngine Containerized Setup Script for Windows
REM Downloads only necessary files - no echo.
echo 🐳 Starting WhisperEngine...
echo    This may take 2-3 minutes on first run (downloading container images)
echo    ✨ Containers include pre-downloaded AI models (~400MB):
echo      • FastEmbed: sentence-transformers/all-MiniLM-L6-v2 (embeddings)
echo      • RoBERTa: cardiffnlp emotion analysis (11 emotions)
echo    🚀 No model downloads needed - instant startup!
echo.ce code required!

setlocal enabledelayedexpansion

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

REM Create WhisperEngine directory
set INSTALL_DIR=whisperengine
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
cd "%INSTALL_DIR%"
echo [SUCCESS] Created directory: %INSTALL_DIR%

REM Download Docker Compose file
echo [SETUP] Downloading Docker Compose configuration...
set COMPOSE_URL=https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/docker-compose.containerized.yml
curl -sSL "%COMPOSE_URL%" -o docker-compose.yml
if errorlevel 1 (
    echo [ERROR] Failed to download Docker Compose file
    pause
    exit /b 1
)
echo [SUCCESS] Downloaded docker-compose.yml

REM Download environment template
echo [SETUP] Downloading configuration template...
set ENV_URL=https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/.env.containerized.template
curl -sSL "%ENV_URL%" -o .env.template
if errorlevel 1 (
    echo [ERROR] Failed to download environment template
    pause
    exit /b 1
)
echo [SUCCESS] Downloaded .env.template

REM Create .env file if it doesn't exist
if not exist .env (
    echo [SETUP] Creating configuration file...
    copy .env.template .env >nul
    echo [SUCCESS] Created .env file from template
    echo.
    echo [WARNING] IMPORTANT: You need to edit the .env file with your settings!
    echo    Required: Set your LLM_CHAT_API_KEY
    echo    Optional: Set DISCORD_BOT_TOKEN for Discord integration
    echo.
    
    REM Open .env file for editing
    echo [SETUP] Opening .env file for editing...
    notepad .env
    
    echo.
    echo 📖 After editing .env, run this script again to start WhisperEngine
    pause
    exit /b 0
)

echo [SUCCESS] Configuration file found

REM Check if API key is set
findstr /c:"your_api_key_here" .env >nul
if not errorlevel 1 (
    echo [WARNING] Please set your LLM_CHAT_API_KEY in the .env file
    echo    Edit .env and replace 'your_api_key_here' with your actual API key
    echo.
    echo    Get API keys from:
    echo    • OpenRouter: https://openrouter.ai (recommended for beginners)
    echo    • OpenAI: https://platform.openai.com
    echo.
    pause
    exit /b 1
)

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
docker-compose pull

REM Start WhisperEngine
echo [SETUP] Starting services...
docker-compose up -d

echo.
echo [SETUP] ⏳ Waiting for services to start...

REM Wait for services to be healthy
set max_attempts=30
set attempt=0

:wait_loop
if !attempt! geq !max_attempts! goto timeout

REM Check if services are ready
curl -s http://localhost:3001 >nul 2>&1 && curl -s http://localhost:9090/health >nul 2>&1
if not errorlevel 1 goto services_ready

set /a attempt+=1
echo    Waiting... (!attempt!/!max_attempts!)
timeout /t 10 /nobreak >nul
goto wait_loop

:timeout
echo [ERROR] Services didn't start properly. Check logs:
echo    docker-compose logs
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
echo.
echo ✨ Features:
echo • Create AI characters via web interface
echo • Persistent memory and conversation history
echo • RESTful Chat APIs for integration
echo • Optional Discord bot functionality
echo.
echo 📖 Next steps:
echo 1. Visit http://localhost:3001 to create your first character
echo 2. Test the chat API with curl or your application
echo 3. Enable Discord integration if desired
echo.
echo 🔧 Management commands:
echo    docker-compose stop     # Stop WhisperEngine
echo    docker-compose start    # Restart WhisperEngine
echo    docker-compose logs -f  # View live logs
echo    docker-compose down     # Stop and remove containers
echo.

REM Auto-open browser
echo [SETUP] 🔗 Opening web interface...
timeout /t 2 /nobreak >nul
start http://localhost:3001

echo [SUCCESS] Setup complete! Enjoy your AI character platform! 🎭
pause