@echo off
REM WhisperEngine Quick Setup Script for Windows
REM This script sets up WhisperEngine with bundled AI models

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

echo 📦 Setting up virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

echo 📥 Installing dependencies...
pip install -r requirements.txt

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
echo 🚀 To start WhisperEngine:
echo    .venv\Scripts\activate.bat
echo    python universal_native_app.py
echo.
echo 📖 Then open your browser to: http://localhost:8501
echo.
echo 💡 For more options, see BUILD_AND_USER_GUIDE.md
pause