# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for WhisperEngine Desktop App
Bundles the web UI and all dependencies into a native macOS application.
"""

import os
from pathlib import Path

# Application paths
app_path = Path.cwd()  # Current working directory
src_path = app_path / "src"
ui_path = src_path / "ui"

block_cipher = None

# Collect data files (including bundled models for offline use)
data_files = [
    ('models', 'models'),  # Bundle all downloaded models
]

# Hidden imports (modules not automatically detected)
hidden_imports = [
    'fastapi',
    'uvicorn',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'starlette',
    'starlette.applications',
    'starlette.routing',
    'starlette.staticfiles',
    'starlette.templating',
    'starlette.responses',
    'starlette.middleware',
    'starlette.middleware.cors',
    'jinja2',
    'python_multipart',
    'websockets',
    'websockets.legacy',
    'websockets.legacy.server',
    'sqlite3',
    'json',
    'asyncio',
    'logging',
    'webbrowser',
    'threading',
    'signal',
    'src.ui.web_ui',
    'src.config.adaptive_config',
    'src.database.database_integration',
    'src.optimization.cost_optimizer',
    # Model-related imports for offline use
    'sentence_transformers',
    'transformers', 
    'torch',
    'numpy',
    'sklearn',
    'src.utils.local_model_loader',
    'src.utils.embedding_manager',
    # Local LLM support
    'transformers.models.gpt2', 'transformers.tokenization_utils_base',
    'transformers.models.auto.modeling_auto', 'transformers.models.auto.tokenization_auto'
]

a = Analysis(
    ['desktop_app.py'],
    pathex=[str(app_path)],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL.ImageTk',
        'PIL.ImageWin',
        'PIL.ImageQt',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=False,  # No console window for desktop app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Remove icon for now
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WhisperEngine',
)

app = BUNDLE(
    coll,
    name='WhisperEngine.app',
    icon=None,  # Remove icon for now
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
        },
    },
)