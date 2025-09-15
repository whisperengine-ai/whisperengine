@echo off
REM WhisperEngine Quick Setup Script for Windows
REM This script sets up WhisperEngine with the new multi-tier dependency system

echo 🚀 WhisperEngine Quick Setup
echo ==============================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is required. Please install Python 3.9 or later.
    echo    Download from: https://python.org/downloads/
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "universal_native_app.py" (
    echo ❌ Please run this script from the WhisperEngine directory
    echo    Current directory: %CD%
    pause
    exit /b 1
)

REM Ask user what they want to install
echo 📦 What would you like to install?
echo 1) Desktop App only (recommended for local use)
echo 2) Discord Bot only (for server deployment)
echo 3) Both Desktop App and Discord Bot
echo.
set /p choice="Choose option (1-3): "

if "%choice%"=="1" (
    set INSTALL_TYPE=desktop
    echo 🖥️ Installing Desktop App...
) else if "%choice%"=="2" (
    set INSTALL_TYPE=discord
    echo 🤖 Installing Discord Bot...
) else if "%choice%"=="3" (
    set INSTALL_TYPE=both
    echo � Installing Both Desktop App and Discord Bot...
) else (
    echo ❌ Invalid choice. Defaulting to Desktop App.
    set INSTALL_TYPE=desktop
)

echo �📦 Setting up virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

echo 📥 Installing dependencies...

REM Install core dependencies (always needed)
echo    📦 Installing core AI/ML dependencies...
pip install -r requirements-core.txt

REM Install platform-specific optimizations
echo    🚀 Installing platform optimizations...
pip install -r requirements-platform.txt

REM Install application-specific dependencies
if "%INSTALL_TYPE%"=="desktop" (
    echo    🖥️ Installing desktop app dependencies...
    pip install -r requirements-desktop.txt
) else if "%INSTALL_TYPE%"=="discord" (
    echo    🤖 Installing Discord bot dependencies...
    pip install -r requirements-discord.txt
) else if "%INSTALL_TYPE%"=="both" (
    echo    🖥️ Installing desktop app dependencies...
    pip install -r requirements-desktop.txt
    echo    🤖 Installing Discord bot dependencies...
    pip install -r requirements-discord.txt
)

echo 🤖 Downloading AI models (this may take 5-10 minutes)...
echo    - Phi-3-Mini conversational AI (~2GB)
echo    - Embedding models for memory (~500MB)
echo    - Emotion analysis models (~600MB)
echo    Total size: ~3.1GB (full functionality)
echo.

python download_models.py

echo.
echo 🎉 Setup completed successfully!
echo.

REM Provide startup instructions based on what was installed
if "%INSTALL_TYPE%"=="desktop" (
    echo �️ To start the Desktop App:
    echo    .venv\Scripts\activate.bat
    echo    python universal_native_app.py
    echo.
) else if "%INSTALL_TYPE%"=="discord" (
    echo 🤖 To start the Discord Bot:
    echo    1. Copy .env.example to .env
    echo    2. Configure your Discord bot token and LLM settings
    echo    3. .venv\Scripts\activate.bat
    echo    4. python run.py
    echo.
) else if "%INSTALL_TYPE%"=="both" (
    echo 🔄 Installation complete for both apps:
    echo.
    echo 🖥️ To start the Desktop App:
    echo    .venv\Scripts\activate.bat
    echo    python universal_native_app.py
    echo.
    echo 🤖 To start the Discord Bot:
    echo    1. Copy .env.example to .env
    echo    2. Configure your Discord bot token and LLM settings  
    echo    3. .venv\Scripts\activate.bat
    echo    4. python run.py
    echo.
)

echo � For detailed documentation, see:
echo    - QUICK_START.md (getting started)
echo    - DEPENDENCY_MANAGEMENT.md (dependency system)
echo    - BUILD_AND_USER_GUIDE.md (advanced setup)
echo.
echo 💡 Use automated installers for future setups:
echo    scripts\install-desktop.bat (desktop app)
echo    scripts\install-discord.bat (discord bot)

pause