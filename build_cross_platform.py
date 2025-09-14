#!/usr/bin/env python3
"""
Cross-Platform Build System for WhisperEngine Desktop App
Handles building native executables for macOS, Windows, and Linux.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import argparse


class CrossPlatformBuilder:
    """Manages cross-platform builds for WhisperEngine"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.current_platform = platform.system().lower()
        
        # Platform configurations
        self.platforms = {
            "darwin": {
                "name": "macOS",
                "executable": "WhisperEngine.app",
                "spec_file": "whisperengine-macos.spec",
                "bundle": True,
                "console": False,
                "upx": True,
            },
            "windows": {
                "name": "Windows",
                "executable": "WhisperEngine.exe",
                "spec_file": "whisperengine-windows.spec", 
                "bundle": False,
                "console": False,
                "upx": True,
            },
            "linux": {
                "name": "Linux",
                "executable": "WhisperEngine",
                "spec_file": "whisperengine-linux.spec",
                "bundle": False,
                "console": False,
                "upx": False,  # UPX often causes issues on Linux
            }
        }
    
    def detect_platform(self) -> str:
        """Detect current platform"""
        system = platform.system().lower()
        if system == "darwin":
            return "darwin"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        else:
            raise ValueError(f"Unsupported platform: {system}")
    
    def get_common_config(self) -> Dict:
        """Get common configuration for all platforms"""
        src_path = self.project_root / "src"
        ui_path = src_path / "ui"
        
        return {
            "data_files": [
                (str(ui_path / "templates" / "index.html"), "src/ui/templates/"),
                (str(ui_path / "static" / "style.css"), "src/ui/static/"),
                (str(ui_path / "static" / "app.js"), "src/ui/static/"),
                (str(ui_path / "static" / "favicon.ico"), "src/ui/static/"),
            ],
            "hidden_imports": [
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
                'pystray',
                'PIL',
                'PIL.Image',
                'PIL.ImageDraw',
                'src.ui.web_ui',
                'src.ui.system_tray',
                'src.config.adaptive_config',
                'src.database.database_integration',
                'src.optimization.cost_optimizer',
            ],
            "excludes": [
                'tkinter',
                'matplotlib',
                'numpy',
                'pandas',
                'scipy',
                'PIL.ImageTk',
                'PIL.ImageWin',
                'PIL.ImageQt',
                'test_*',
                'tests',
            ]
        }
    
    def generate_spec_file(self, target_platform: str) -> Path:
        """Generate platform-specific .spec file"""
        config = self.platforms[target_platform]
        common = self.get_common_config()
        spec_path = self.project_root / config["spec_file"]
        
        # Platform-specific adjustments
        if target_platform == "windows":
            # Windows-specific hidden imports
            common["hidden_imports"].extend([
                'win32api',
                'win32gui', 
                'win32con',
                'pywintypes',
            ])
        elif target_platform == "linux":
            # Linux-specific hidden imports
            common["hidden_imports"].extend([
                'gi',
                'gi.repository',
                'gi.repository.Gtk',
                'gi.repository.GLib',
            ])
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for WhisperEngine Desktop App - {config["name"]}
Generated by cross-platform build system.
"""

import os
from pathlib import Path

# Application paths
app_path = Path.cwd()
src_path = app_path / "src"
ui_path = src_path / "ui"

block_cipher = None

# Data files (templates, static assets)
data_files = {common["data_files"]!r}

# Hidden imports (modules not automatically detected)
hidden_imports = {common["hidden_imports"]!r}

a = Analysis(
    ['desktop_app.py'],
    pathex=[str(app_path)],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={common["excludes"]!r},
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
    name='{config["executable"].split(".")[0]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={str(config["upx"])},
    console={str(config["console"])},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx={str(config["upx"])},
    upx_exclude=[],
    name='{config["executable"].split(".")[0]}',
)
'''
        
        # Add macOS-specific bundle configuration
        if target_platform == "darwin":
            spec_content += f'''
app = BUNDLE(
    coll,
    name='{config["executable"]}',
    icon=None,
    bundle_identifier='com.whisperengine.desktop',
    info_plist={{
        'NSHighResolutionCapable': 'True',
        'NSAppleScriptEnabled': False,
        'CFBundleDisplayName': 'WhisperEngine',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'NSHumanReadableCopyright': 'WhisperEngine AI Platform',
        'NSRequiresAquaSystemAppearance': False,
        'LSEnvironment': {{
            'PYTHONPATH': '.',
        }},
    }},
)
'''
        
        # Write spec file
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"✅ Generated {config['name']} spec file: {spec_path}")
        return spec_path
    
    def build_platform(self, target_platform: str, clean: bool = True) -> bool:
        """Build for specific platform"""
        if target_platform not in self.platforms:
            print(f"❌ Unsupported platform: {target_platform}")
            return False
        
        config = self.platforms[target_platform]
        print(f"🔨 Building WhisperEngine for {config['name']}...")
        
        try:
            # Generate spec file
            spec_file = self.generate_spec_file(target_platform)
            
            # Prepare build command
            python_exe = sys.executable
            pyinstaller_path = Path(python_exe).parent / "pyinstaller"
            
            # Use pyinstaller from current Python environment
            if pyinstaller_path.exists():
                cmd = [str(pyinstaller_path)]
            else:
                # Fallback to module execution
                cmd = [python_exe, "-m", "PyInstaller"]
            
            if clean:
                cmd.append("--clean")
            cmd.extend(["--noconfirm", str(spec_file)])
            
            # Run PyInstaller
            print(f"🚀 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Check for output - be more flexible about file locations
                config = self.platforms[target_platform]
                possible_outputs = []
                
                if target_platform == "darwin":
                    possible_outputs = [
                        self.dist_dir / config["executable"],  # WhisperEngine.app
                    ]
                elif target_platform == "windows":
                    possible_outputs = [
                        self.dist_dir / config["executable"],  # WhisperEngine.exe
                        self.dist_dir / config["executable"].split(".")[0] / config["executable"],  # WhisperEngine/WhisperEngine.exe
                        self.dist_dir / config["executable"].split(".")[0] / config["executable"].split(".")[0],  # WhisperEngine/WhisperEngine
                    ]
                else:  # linux
                    possible_outputs = [
                        self.dist_dir / config["executable"],  # WhisperEngine
                        self.dist_dir / config["executable"] / config["executable"],  # WhisperEngine/WhisperEngine
                    ]
                
                # Find the actual output
                output_path = None
                for path in possible_outputs:
                    if path.exists():
                        output_path = path
                        break
                
                if output_path:
                    print(f"✅ {config['name']} build successful!")
                    print(f"📦 Output: {output_path}")
                    return True
                else:
                    print(f"❌ Build completed but output not found")
                    print(f"   Checked locations:")
                    for path in possible_outputs:
                        print(f"     - {path}")
                    print(f"   Available files in dist/:")
                    try:
                        for item in self.dist_dir.iterdir():
                            print(f"     - {item}")
                    except:
                        print("     (could not list dist directory)")
                    return False
            else:
                print(f"❌ {config['name']} build failed!")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def build_current_platform(self, clean: bool = True) -> bool:
        """Build for current platform"""
        current = self.detect_platform()
        return self.build_platform(current, clean)
    
    def build_all_supported(self, clean: bool = True) -> Dict[str, bool]:
        """Build for all supported platforms (if possible)"""
        results = {}
        
        print("🌍 Cross-platform build initiated...")
        print(f"📍 Current platform: {self.platforms[self.current_platform]['name']}")
        
        for platform_key in self.platforms:
            if platform_key == self.current_platform:
                print(f"\n🎯 Building for current platform: {self.platforms[platform_key]['name']}")
                results[platform_key] = self.build_platform(platform_key, clean)
            else:
                print(f"\n⚠️  Cross-compilation to {self.platforms[platform_key]['name']} not supported")
                print(f"   Build on native {self.platforms[platform_key]['name']} system for best results")
                results[platform_key] = False
        
        return results
    
    def clean_build_artifacts(self):
        """Clean build artifacts"""
        print("🧹 Cleaning build artifacts...")
        
        # Remove build and dist directories
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print(f"🗑️  Removed: {self.build_dir}")
        
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print(f"🗑️  Removed: {self.dist_dir}")
        
        # Remove spec files
        for platform_config in self.platforms.values():
            spec_path = self.project_root / platform_config["spec_file"]
            if spec_path.exists():
                spec_path.unlink()
                print(f"🗑️  Removed: {spec_path}")
        
        print("✅ Cleanup complete")
    
    def get_build_info(self) -> Dict:
        """Get build environment information"""
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "current_platform": self.current_platform,
            "supported_platforms": list(self.platforms.keys()),
        }


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="WhisperEngine Cross-Platform Builder")
    parser.add_argument(
        "command",
        choices=["build", "build-all", "clean", "info"],
        help="Build command to execute"
    )
    parser.add_argument(
        "--platform", 
        choices=["darwin", "windows", "linux"],
        help="Target platform (default: current platform)"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleaning build artifacts before building"
    )
    
    args = parser.parse_args()
    
    builder = CrossPlatformBuilder()
    
    print("🤖 WhisperEngine Cross-Platform Builder")
    print("=" * 50)
    
    if args.command == "info":
        info = builder.get_build_info()
        print("📊 Build Environment Information:")
        for key, value in info.items():
            print(f"   {key}: {value}")
    
    elif args.command == "clean":
        builder.clean_build_artifacts()
    
    elif args.command == "build":
        clean = not args.no_clean
        if args.platform:
            success = builder.build_platform(args.platform, clean)
        else:
            success = builder.build_current_platform(clean)
        
        if success:
            print("\n🎉 Build completed successfully!")
        else:
            print("\n💥 Build failed!")
            sys.exit(1)
    
    elif args.command == "build-all":
        clean = not args.no_clean
        results = builder.build_all_supported(clean)
        
        print("\n📊 Build Results:")
        for platform, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"   {builder.platforms[platform]['name']}: {status}")
        
        if any(results.values()):
            print("\n🎉 At least one build succeeded!")
        else:
            print("\n💥 All builds failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()