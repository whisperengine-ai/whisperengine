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

# Collect data files (templates, static assets)
data_files = [
    (str(ui_path / "templates" / "index.html"), "src/ui/templates/"),
    (str(ui_path / "static" / "style.css"), "src/ui/static/"),
    (str(ui_path / "static" / "app.js"), "src/ui/static/"),
    (str(ui_path / "static" / "favicon.ico"), "src/ui/static/"),
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
        },
    },
)