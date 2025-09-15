#!/usr/bin/env python3
"""
Cross-Platform Build Verification
Shows what was actually built and explains the differences.
"""

import os
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
            result = subprocess.run(['file', str(file_path)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
    except:
        pass
    
    # Fallback to basic info
    if file_path.is_dir():
        return "📁 Directory/Bundle"
    else:
        return f"📄 File ({file_path.stat().st_size} bytes)"


def verify_builds():
    """Verify what was actually built"""
    print("🔍 WhisperEngine Cross-Platform Build Verification")
    print("=" * 60)
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ No dist directory found. Run a build first.")
        return
    
    print(f"📍 Host Platform: {platform.system()} {platform.machine()}")
    print(f"🐍 Python: {platform.python_version()}")
    print()
    
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
        print("❌ No builds found in dist directory")
        print("   Run: python build_cross_platform.py build")
        return
    
    print("📦 Built Artifacts:")
    print("-" * 30)
    
    for platform_name, bundle_path, exe_path in builds_found:
        print(f"\n🎯 {platform_name} Build:")
        print(f"   Bundle: {bundle_path}")
        print(f"   Type: {check_file_type(bundle_path)}")
        
        if exe_path.exists():
            print(f"   Executable: {exe_path}")
            print(f"   Type: {check_file_type(exe_path)}")
            
            # Check if it's actually native to current platform
            file_info = check_file_type(exe_path)
            if platform.system() == "Darwin" and "Mach-O" in file_info:
                print("   ✅ Native macOS binary")
            elif platform.system() == "Windows" and "PE32" in file_info:
                print("   ✅ Native Windows binary")
            elif platform.system() == "Linux" and "ELF" in file_info:
                print("   ✅ Native Linux binary")
            else:
                print(f"   ⚠️  Built on {platform.system()}, may not be native for target platform")
        else:
            print("   ❌ Executable not found")
    
    print("\n" + "=" * 60)
    print("💡 Understanding the Results:")
    print("   • ✅ Native builds work fully on their target platform")
    print("   • ⚠️  Cross-platform builds have correct configuration but host platform binary")
    print("   • For production: build on native platform or use CI/CD")
    print()
    print("🚀 To test functionality:")
    print("   python test_desktop_llm_complete.py")


if __name__ == "__main__":
    verify_builds()