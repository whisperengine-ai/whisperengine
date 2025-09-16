#!/usr/bin/env python3
"""
Cross-Platform Build Verification
Shows what was actually built and explains the differences.
"""

import platform
import subprocess
from pathlib import Path


def check_file_type(file_path: Path) -> str:
    """Check file type using system tools"""
    if not file_path.exists():
        return "❌ File not found"

    try:
        # Use 'file' command on Unix systems
        if platform.system() != "Windows":
            result = subprocess.run(["file", str(file_path)], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
    except Exception:
        pass

    # Fallback to basic info
    if file_path.is_dir():
        return "📁 Directory/Bundle"
    else:
        return f"📄 File ({file_path.stat().st_size} bytes)"


def verify_builds():
    """Verify what was actually built"""

    dist_dir = Path("dist")
    if not dist_dir.exists():
        return


    # Check what we built
    builds_found = []

    # macOS app bundle
    macos_app = dist_dir / "WhisperEngine.app"
    if macos_app.exists():
        executable = macos_app / "Contents" / "MacOS" / "WhisperEngine"
        builds_found.append(("macOS", macos_app, executable))

    # Windows/Linux executable directory
    exe_dir = dist_dir / "WhisperEngine"
    if exe_dir.exists():
        executable = exe_dir / "WhisperEngine"
        builds_found.append(("Windows/Linux", exe_dir, executable))

    # Standalone executable
    standalone = dist_dir / "WhisperEngine"
    if standalone.exists() and standalone.is_file():
        builds_found.append(("Standalone", standalone, standalone))

    if not builds_found:
        return


    for _platform_name, _bundle_path, exe_path in builds_found:

        if exe_path.exists():

            # Check if it's actually native to current platform
            file_info = check_file_type(exe_path)
            if platform.system() == "Darwin" and "Mach-O" in file_info:
                pass
            elif platform.system() == "Windows" and "PE32" in file_info:
                pass
            elif platform.system() == "Linux" and "ELF" in file_info:
                pass
            else:
                pass
        else:
            pass



if __name__ == "__main__":
    verify_builds()
