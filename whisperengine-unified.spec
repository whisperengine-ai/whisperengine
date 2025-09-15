# -*- mode: python ; coding: utf-8 -*-
"""
Unified PyInstaller spec file for WhisperEngine Desktop App
Cross-platform build configuration with automatic platform detection.
"""

import os
import sys
from pathlib import Path

# Application paths
app_path = Path.cwd()
src_path = app_path / "src"
ui_path = src_path / "ui"

# Platform detection
is_windows = sys.platform.startswith('win')
is_macos = sys.platform == 'darwin'
is_linux = sys.platform.startswith('linux')

block_cipher = None

# Collect data files (including bundled models for offline use)
data_files = [
    ('models', 'models'),  # Bundle all downloaded models (~8GB with Phi-3-Mini)
    ('system_prompt.md', '.'),
    # UI files would go here if using web UI - currently using Qt native UI
]

# Hidden imports - comprehensive list for all platforms
hidden_imports = [
    # FastAPI and web framework
    'fastapi', 'uvicorn', 'uvicorn.lifespan', 'uvicorn.lifespan.on',
    'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols',
    'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
    'starlette', 'starlette.applications', 'starlette.routing',
    'starlette.responses', 'starlette.middleware', 'starlette.middleware.cors',
    'jinja2', 'python_multipart', 'websockets', 'websockets.legacy',
    'websockets.legacy.server',
    
    # Core Python modules
    'sqlite3', 'json', 'asyncio', 'logging', 'webbrowser', 'threading', 'signal',
    
    # Platform-specific UI (conditionally added below)
    
    # WhisperEngine modules
    'src.ui.web_ui', 'src.config.adaptive_config', 'src.database.database_integration',
    'src.optimization.cost_optimizer', 'src.llm.llm_client', 'src.memory.memory_manager',
    'src.platforms.universal_chat', 'src.core.enhanced_bot_core',
    
    # AI/ML models for offline use
    'sentence_transformers', 'transformers', 'torch', 'numpy', 'sklearn',
    'chromadb', 'requests', 'aiohttp', 'src.utils.local_model_loader',
    'src.utils.embedding_manager', 'huggingface_hub',
]

# Add platform-specific imports
if is_macos or is_linux:
    hidden_imports.extend([
        'pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'src.ui.system_tray'
    ])

if is_windows:
    hidden_imports.extend([
        'pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'src.ui.system_tray',
        'win32gui', 'win32con'  # Windows-specific if needed
    ])

# Analysis configuration
a = Analysis(
    ['universal_native_app.py'],
    pathex=[str(app_path)],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',  # Exclude tkinter to reduce size
        'matplotlib',  # Exclude matplotlib unless needed
        'IPython',  # Exclude IPython to reduce size
    ],
    noarchive=False,
    optimize=0,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WhisperEngine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect all files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WhisperEngine'
)

# Platform-specific app bundle creation
if is_macos:
    app = BUNDLE(
        coll,
        name='WhisperEngine.app',
        icon=None,
        bundle_identifier='com.whisperengine.desktop',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'NSAppleScriptEnabled': False,
            'CFBundleDisplayName': 'WhisperEngine',
            'CFBundleShortVersionString': '2.0.0',
            'CFBundleVersion': '2.0.0',
            'NSHumanReadableCopyright': 'WhisperEngine AI Platform',
            'NSRequiresAquaSystemAppearance': False,
            'LSEnvironment': {
                'PYTHONPATH': '.',
                # AI Features - All enabled by default for bundled executable
                'ENABLE_EMOTIONAL_INTELLIGENCE': 'true',
                'ENABLE_PHASE3_MEMORY': 'true',
                'ENABLE_PHASE4_INTELLIGENCE': 'true', 
                'PERSONALITY_ADAPTATION_ENABLED': 'true',
                'ENABLE_PROMPT_OPTIMIZATION': 'true',
                'OPTIMIZED_PROMPT_MODE': 'auto',
                'ENABLE_AI_CACHING': 'true',
                'USE_LOCAL_MODELS': 'true',
                # Performance tuning for bundled apps
                'MAX_CONCURRENT_AI_OPERATIONS': '2',
                'AI_RESPONSE_TIMEOUT': '45',
                'MEMORY_MAX_ENTRIES': '5000',
                'CHROMA_BATCH_SIZE': '50',
            },
        },
    )

elif is_windows:
    # Windows-specific configuration could go here
    # For now, the exe and coll are sufficient
    pass

elif is_linux:
    # Linux-specific configuration (AppImage, etc.)
    # For now, the exe and coll are sufficient
    pass