@echo off
REM Windows Discord Bot Installation Script
REM Supports: Windows 10/11 x64

echo 🤖 Installing WhisperEngine Discord Bot for Windows...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set python_version=%%i
echo ✅ Python %python_version% detected

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 🔧 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install core dependencies
echo 📦 Installing core dependencies...
pip install -r requirements-core.txt

REM Install Discord-specific dependencies
echo 🤖 Installing Discord bot dependencies...
pip install -r requirements-discord.txt

REM Install platform-specific optimizations
echo 🚀 Installing platform optimizations...
pip install -r requirements-platform.txt

REM Verify installation
echo ✅ Verifying installation...
python -c "import discord; print(f'Discord.py version: {discord.__version__}')"

echo.
echo 🎉 Discord Bot installation complete!
echo.
echo 📝 Next steps:
echo 1. Copy .env.example to .env.discord
echo 2. Configure your Discord bot token and LLM settings
echo 3. Run: python run.py
echo.
echo 📚 See QUICK_START.md for detailed setup instructions

pause