@echo off
REM Windows Desktop App Installation Script
REM Supports: Windows 10/11 x64

echo 🖥️ Installing WhisperEngine Desktop App for Windows...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set python_version=%%i
echo ✅ Python %python_version% detected

REM Check for Visual C++ Redistributable (needed for some dependencies)
echo 🔧 Checking system requirements...
where vcruntime140.dll >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Visual C++ Redistributable may be missing
    echo   Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
)

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

REM Install desktop-specific dependencies
echo 🖥️ Installing desktop app dependencies...
pip install -r requirements-desktop.txt

REM Install platform-specific optimizations
echo 🚀 Installing platform optimizations...
pip install -r requirements-platform.txt

REM Verify installation
echo ✅ Verifying installation...
python -c "import PySide6; print(f'PySide6 version: {PySide6.__version__}')"
python -c "import transformers; print(f'Transformers version: {transformers.__version__}')"

echo.
echo 🎉 Desktop App installation complete!
echo.
echo 📝 Next steps:
echo 1. Copy .env.example to .env.desktop-app
echo 2. Configure your LLM settings (local or API)
echo 3. Run: python universal_native_app.py
echo.
echo 💡 For local LLM:
echo   - Start LM Studio or install Ollama HTTP server
echo.
echo 📚 See QUICK_START.md for detailed setup instructions

pause