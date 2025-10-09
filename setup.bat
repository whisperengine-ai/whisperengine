@echo off
REM WhisperEngine Quick Setup Script for Windows
REM Makes setup easy for Windows users

echo 🚀 WhisperEngine Quick Setup
echo ==============================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Check if .env exists
if not exist .env (
    echo 📝 Creating configuration file...
    copy .env.quickstart.template .env >nul
    echo ✅ Created .env file from template
    echo.
    echo ⚠️  IMPORTANT: You need to edit the .env file with your settings!
    echo    Required: Set your LLM_CHAT_API_KEY
    echo    Optional: Set DISCORD_BOT_TOKEN for Discord integration
    echo.
    
    echo 🔧 Opening .env file for editing...
    notepad .env
    
    echo.
    echo 📖 After editing .env, run this script again to start WhisperEngine
    pause
    exit /b 0
)

echo 📝 Configuration file found
echo.

echo 🐳 Starting WhisperEngine services...
docker-compose -f docker-compose.quickstart.yml up -d

if %errorlevel% neq 0 (
    echo ❌ Failed to start services. Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ✅ WhisperEngine is starting up!
echo.
echo 🔗 Web Interface: http://localhost:3001
echo 📊 Health Check: http://localhost:9091/health
echo.
echo 📋 What's available:
echo    • CDL Character Management: http://localhost:3001
echo    • Chat API Endpoint: http://localhost:9091/api/chat
echo    • Optional Discord Integration (if token provided)
echo.

REM Wait a moment for services to start
echo ⏳ Waiting for services to initialize...
timeout /t 10 /nobreak >nul

REM Check health
echo 🔍 Checking service health...
curl -s http://localhost:9091/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ WhisperEngine is healthy and ready!
) else (
    echo ⚠️  Services are starting... may take a minute to be fully ready
)

echo.
echo 🌐 Opening web interface...
start http://localhost:3001

echo.
echo 🎉 Setup complete!
echo.
echo 💡 Next steps:
echo    1. Use the web interface to customize your AI character
echo    2. Test the chat API at http://localhost:9091/api/chat
echo    3. Optional: Set up Discord integration in .env file
echo.
echo 🛑 To stop WhisperEngine:
echo    docker-compose -f docker-compose.quickstart.yml down
echo.
pause