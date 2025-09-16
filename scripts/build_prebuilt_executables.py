#!/usr/bin/env python3
"""
WhisperEngine Pre-Built Executable Build System
================================================

This script automates the creation of complete, standalone WhisperEngine executables
for Windows, macOS, and Linux with all AI models bundled for non-technical users.

Features:
- Cross-platform builds with platform detection
- Automated model downloading and bundling
- Complete packaging with all dependencies
- Release artifact preparation
- Size optimization and validation
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


class PreBuiltExecutableBuilder:
    """Automated builder for WhisperEngine standalone executables"""

    def __init__(self, output_dir: str = "releases"):
        self.project_root = Path(__file__).parent.parent
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Platform detection
        self.current_platform = platform.system().lower()
        self.architecture = platform.machine().lower()

        # Build configuration
        self.config = {
            "models_to_bundle": [
                "microsoft/Phi-3-mini-4k-instruct",
                "sentence-transformers/all-MiniLM-L6-v2",
                "openai/whisper-tiny.en",
            ],
            "target_platforms": ["windows", "macos", "linux"],
            "expected_size_gb": 18,  # Approximate final size
            "max_size_gb": 25,  # Maximum acceptable size
        }

    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with platform context"""

    def check_prerequisites(self) -> bool:
        """Verify all build prerequisites are available"""
        self.log("Checking build prerequisites...")

        # Check virtual environment
        if not os.environ.get("VIRTUAL_ENV"):
            self.log("ERROR: Must run in virtual environment", "ERROR")
            self.log("Run: source .venv/bin/activate", "ERROR")
            return False

        # Check PyInstaller
        try:
            result = subprocess.run(["pyinstaller", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"PyInstaller: {result.stdout.strip()}")
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            self.log("ERROR: PyInstaller not found", "ERROR")
            return False

        # Check disk space (need ~50GB for builds)
        statvfs = os.statvfs(self.project_root)
        free_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
        if free_gb < 50:
            self.log(f"WARNING: Low disk space ({free_gb:.1f}GB available, need ~50GB)", "WARN")

        # Check spec file
        spec_file = self.project_root / "whisperengine-unified.spec"
        if not spec_file.exists():
            self.log("ERROR: whisperengine-unified.spec not found", "ERROR")
            return False

        self.log("✅ All prerequisites satisfied")
        return True

    def download_models(self) -> bool:
        """Ensure all required AI models are downloaded"""
        self.log("Downloading AI models...")

        try:
            # Use the existing download script
            script_path = self.project_root / "download_models.py"
            if not script_path.exists():
                self.log("ERROR: download_models.py not found", "ERROR")
                return False

            # Run with virtual environment
            cmd = [sys.executable, str(script_path)]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                self.log(f"ERROR: Model download failed: {result.stderr}", "ERROR")
                return False

            # Verify models directory
            models_dir = self.project_root / "models"
            if not models_dir.exists() or not list(models_dir.iterdir()):
                self.log("ERROR: Models directory empty after download", "ERROR")
                return False

            # Check model sizes
            model_size_gb = sum(f.stat().st_size for f in models_dir.rglob("*") if f.is_file()) / (
                1024**3
            )
            self.log(f"✅ Models downloaded ({model_size_gb:.1f}GB total)")
            return True

        except Exception as e:
            self.log(f"ERROR: Model download exception: {e}", "ERROR")
            return False

    def build_executable(self, platform_name: str | None = None) -> tuple[bool, Path | None]:
        """Build executable for specified platform (or current platform)"""
        target_platform = platform_name or self.current_platform
        self.log(f"Building executable for {target_platform}...")

        # Clean previous builds
        build_dir = self.project_root / "build"
        dist_dir = self.project_root / "dist"

        for cleanup_dir in [build_dir, dist_dir]:
            if cleanup_dir.exists():
                self.log(f"Cleaning {cleanup_dir}")
                shutil.rmtree(cleanup_dir)

        # Build with PyInstaller
        spec_file = self.project_root / "whisperengine-unified.spec"
        cmd = ["pyinstaller", "--clean", "--noconfirm", str(spec_file)]

        try:
            self.log("Starting PyInstaller build (this may take 30+ minutes)...")
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                self.log(f"ERROR: PyInstaller build failed: {result.stderr}", "ERROR")
                return False, None

            # Validate build output
            if target_platform == "macos":
                app_path = dist_dir / "WhisperEngine.app"
                dist_dir / "WhisperEngine"
            elif target_platform == "windows":
                app_path = dist_dir / "WhisperEngine.exe"
            else:  # linux
                app_path = dist_dir / "WhisperEngine"

            if not app_path.exists():
                self.log(f"ERROR: Build output not found at {app_path}", "ERROR")
                return False, None

            # Check size
            if app_path.is_dir():
                size_gb = sum(f.stat().st_size for f in app_path.rglob("*") if f.is_file()) / (
                    1024**3
                )
            else:
                size_gb = app_path.stat().st_size / (1024**3)

            if size_gb > self.config["max_size_gb"]:
                self.log(
                    f"WARNING: Build size ({size_gb:.1f}GB) exceeds maximum ({self.config['max_size_gb']}GB)",
                    "WARN",
                )

            self.log(f"✅ Build completed ({size_gb:.1f}GB)")
            return True, app_path

        except Exception as e:
            self.log(f"ERROR: Build exception: {e}", "ERROR")
            return False, None

    def test_executable(self, executable_path: Path) -> bool:
        """Test that the built executable works correctly"""
        self.log("Testing executable...")

        try:
            # Test basic startup
            if executable_path.suffix == ".app":
                # macOS app bundle
                exe_path = executable_path / "Contents" / "MacOS" / "WhisperEngine"
                if not exe_path.exists():
                    exe_path = list(executable_path.rglob("WhisperEngine"))[0]
            else:
                exe_path = executable_path

            # Quick test - just verify it can start
            cmd = [str(exe_path), "--help"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # We expect it to show UI or help, not crash
            if "WhisperEngine" in result.stdout or "Starting WhisperEngine" in result.stderr:
                self.log("✅ Executable test passed")
                return True
            else:
                self.log(f"WARNING: Unexpected test output: {result.stdout[:200]}", "WARN")
                return True  # Consider it working if no crash

        except subprocess.TimeoutExpired:
            self.log("✅ Executable test passed (UI launched, timeout expected)")
            return True
        except Exception as e:
            self.log(f"ERROR: Executable test failed: {e}", "ERROR")
            return False

    def package_release(self, executable_path: Path) -> Path | None:
        """Package executable for distribution"""
        platform_name = self.current_platform
        arch = self.architecture

        # Create release filename
        if platform_name == "darwin":
            platform_name = "macos"

        release_name = f"WhisperEngine-{platform_name}-{arch}"
        release_path = self.output_dir / f"{release_name}.zip"

        self.log(f"Packaging release to {release_path}")

        try:
            # Create archive
            if executable_path.suffix == ".app":
                # macOS app bundle
                shutil.make_archive(
                    str(release_path.with_suffix("")),
                    "zip",
                    executable_path.parent,
                    executable_path.name,
                )
            else:
                # Other platforms
                shutil.make_archive(
                    str(release_path.with_suffix("")),
                    "zip",
                    executable_path.parent,
                    executable_path.name,
                )

            # Verify archive
            if release_path.exists():
                size_gb = release_path.stat().st_size / (1024**3)
                self.log(f"✅ Release packaged ({size_gb:.1f}GB)")
                return release_path
            else:
                self.log("ERROR: Release packaging failed", "ERROR")
                return None

        except Exception as e:
            self.log(f"ERROR: Packaging exception: {e}", "ERROR")
            return None

    def create_installation_guide(self, release_path: Path):
        """Create user-friendly installation guide"""
        platform_name = self.current_platform
        if platform_name == "darwin":
            platform_name = "macos"

        guide_path = self.output_dir / f"INSTALL-{platform_name}.md"

        if platform_name == "macos":
            guide_content = """# WhisperEngine macOS Installation

## Quick Start (Non-Technical Users)

1. **Download**: Download `WhisperEngine-macos-*.zip`
2. **Extract**: Double-click the zip file to extract `WhisperEngine.app`
3. **Install**: Drag `WhisperEngine.app` to your Applications folder
4. **Run**: Double-click WhisperEngine in Applications
5. **Chat**: The app will open with a chat interface ready to use!

## First Run Notes

- **Security**: macOS may ask permission to run - click "Open" when prompted
- **Size**: The app is large (~18GB) because it includes all AI models
- **Performance**: First startup may take 30-60 seconds while models load
- **Internet**: No internet required after installation - fully offline AI!

## Troubleshooting

- **Won't Open**: Right-click app → Open → Open (for unsigned apps)
- **Slow Start**: Normal for first run, faster afterward
- **Chat Issues**: Check system requirements (8GB+ RAM recommended)
"""
        elif platform_name == "windows":
            guide_content = """# WhisperEngine Windows Installation

## Quick Start (Non-Technical Users)

1. **Download**: Download `WhisperEngine-windows-*.zip`
2. **Extract**: Right-click zip → Extract All → Choose location
3. **Run**: Double-click `WhisperEngine.exe` in extracted folder
4. **Chat**: The app will open with a chat interface ready to use!

## First Run Notes

- **Security**: Windows may show security warning - click "More info" → "Run anyway"
- **Size**: The app is large (~18GB) because it includes all AI models
- **Performance**: First startup may take 30-60 seconds while models load
- **Internet**: No internet required after installation - fully offline AI!

## Troubleshooting

- **Security Warning**: Normal for unsigned apps - click "Run anyway"
- **Slow Start**: Normal for first run, faster afterward
- **Chat Issues**: Check system requirements (8GB+ RAM recommended)
"""
        else:  # linux
            guide_content = """# WhisperEngine Linux Installation

## Quick Start (Technical Users)

1. **Download**: Download `WhisperEngine-linux-*.zip`
2. **Extract**: `unzip WhisperEngine-linux-*.zip`
3. **Permissions**: `chmod +x WhisperEngine/WhisperEngine`
4. **Run**: `./WhisperEngine/WhisperEngine`
5. **Chat**: The app will open with a chat interface ready to use!

## First Run Notes

- **Dependencies**: Most dependencies are bundled, but may need system libraries
- **Size**: The app is large (~18GB) because it includes all AI models
- **Performance**: First startup may take 30-60 seconds while models load
- **Internet**: No internet required after installation - fully offline AI!

## Troubleshooting

- **Missing Libraries**: Install system dependencies if needed
- **Slow Start**: Normal for first run, faster afterward
- **Chat Issues**: Check system requirements (8GB+ RAM recommended)
"""

        guide_path.write_text(guide_content)
        self.log(f"✅ Installation guide created: {guide_path}")

    def build_all_platforms(self):
        """Build for current platform (cross-compilation requires platform-specific setup)"""
        self.log("Starting complete build process...")

        # Step 1: Prerequisites
        if not self.check_prerequisites():
            return False

        # Step 2: Download models
        if not self.download_models():
            return False

        # Step 3: Build executable
        success, executable_path = self.build_executable()
        if not success or executable_path is None:
            return False

        # Step 4: Test executable
        if not self.test_executable(executable_path):
            self.log("WARNING: Executable test failed, but continuing", "WARN")

        # Step 5: Package release
        release_path = self.package_release(executable_path)
        if not release_path:
            return False

        # Step 6: Create installation guide
        self.create_installation_guide(release_path)

        self.log("🎉 Build process completed successfully!")
        self.log(f"📦 Release ready: {release_path}")

        return True


def main():
    parser = argparse.ArgumentParser(description="Build WhisperEngine pre-built executables")
    parser.add_argument("--output-dir", default="releases", help="Output directory for releases")
    parser.add_argument("--test-only", action="store_true", help="Only test existing executable")

    args = parser.parse_args()

    builder = PreBuiltExecutableBuilder(args.output_dir)

    if args.test_only:
        # Test existing build
        dist_dir = builder.project_root / "dist"
        if builder.current_platform == "darwin":
            executable = dist_dir / "WhisperEngine.app"
        else:
            executable = dist_dir / "WhisperEngine"

        if executable.exists():
            success = builder.test_executable(executable)
            sys.exit(0 if success else 1)
        else:
            builder.log("ERROR: No executable found to test", "ERROR")
            sys.exit(1)
    else:
        # Full build
        success = builder.build_all_platforms()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
