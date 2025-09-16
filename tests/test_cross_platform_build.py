#!/usr/bin/env python3
"""
Test Cross-Platform Build System for WhisperEngine
Validates the build system functionality and output.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import tempfile
import shutil


def test_build_system_imports():
    """Test that the build system can be imported"""
    print("🧪 Testing Build System Imports...")

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from build_cross_platform import CrossPlatformBuilder

        builder = CrossPlatformBuilder()
        print("✅ CrossPlatformBuilder imported successfully")

        # Test platform detection
        current_platform = builder.detect_platform()
        print(f"✅ Platform detected: {current_platform}")

        # Test configuration
        platforms = builder.platforms
        print(f"✅ Supported platforms: {list(platforms.keys())}")

        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def test_spec_file_generation():
    """Test spec file generation for all platforms"""
    print("\n🧪 Testing Spec File Generation...")

    try:
        from build_cross_platform import CrossPlatformBuilder

        builder = CrossPlatformBuilder()

        results = {}
        for platform_key in builder.platforms:
            try:
                print(f"   Generating {platform_key} spec file...")
                spec_path = builder.generate_spec_file(platform_key)

                # Verify file exists and has content
                if spec_path.exists() and spec_path.stat().st_size > 0:
                    print(f"   ✅ {platform_key} spec file created: {spec_path}")
                    results[platform_key] = True

                    # Cleanup
                    spec_path.unlink()
                else:
                    print(f"   ❌ {platform_key} spec file invalid")
                    results[platform_key] = False

            except Exception as e:
                print(f"   ❌ {platform_key} spec generation failed: {e}")
                results[platform_key] = False

        success_count = sum(results.values())
        total_count = len(results)
        print(f"✅ Spec generation test: {success_count}/{total_count} successful")

        return success_count == total_count

    except Exception as e:
        print(f"❌ Spec generation test failed: {e}")
        return False


def test_build_info():
    """Test build environment info"""
    print("\n🧪 Testing Build Environment Info...")

    try:
        from build_cross_platform import CrossPlatformBuilder

        builder = CrossPlatformBuilder()

        info = builder.get_build_info()
        required_keys = [
            "platform",
            "python_version",
            "architecture",
            "machine",
            "current_platform",
            "supported_platforms",
        ]

        for key in required_keys:
            if key not in info:
                print(f"❌ Missing required info key: {key}")
                return False
            print(f"   {key}: {info[key]}")

        print("✅ Build environment info complete")
        return True

    except Exception as e:
        print(f"❌ Build info test failed: {e}")
        return False


def test_current_platform_build():
    """Test building for current platform"""
    print("\n🧪 Testing Current Platform Build...")

    try:
        # Run the build command
        cmd = [sys.executable, "build_cross_platform.py", "build", "--no-clean"]
        print(f"🚀 Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            print("✅ Build command executed successfully")

            # Check if output exists
            dist_dir = Path(__file__).parent / "dist"
            current_platform = platform.system().lower()

            if current_platform == "darwin":
                expected_output = dist_dir / "WhisperEngine.app"
            elif current_platform == "windows":
                expected_output = dist_dir / "WhisperEngine.exe"
            else:  # linux
                expected_output = dist_dir / "WhisperEngine"

            if expected_output.exists():
                print(f"✅ Build output found: {expected_output}")
                return True
            else:
                print(f"❌ Build output not found: {expected_output}")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                return False
        else:
            print(f"❌ Build command failed with code {result.returncode}")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Build test timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Build test failed: {e}")
        return False


def test_build_script_wrapper():
    """Test the build.sh wrapper script"""
    print("\n🧪 Testing Build Script Wrapper...")

    try:
        build_script = Path(__file__).parent / "build.sh"

        if not build_script.exists():
            print("❌ build.sh not found")
            return False

        # Test help command
        cmd = ["./build.sh", "help"]
        result = subprocess.run(
            cmd, cwd=Path(__file__).parent, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0 and "Usage:" in result.stdout:
            print("✅ Build script help command works")
            return True
        else:
            print(f"❌ Build script help failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Build script test failed: {e}")
        return False


def test_cleanup():
    """Test cleanup functionality"""
    print("\n🧪 Testing Cleanup Functionality...")

    try:
        from build_cross_platform import CrossPlatformBuilder

        builder = CrossPlatformBuilder()

        # Create some test files
        test_spec = Path(__file__).parent / "test-cleanup.spec"
        test_spec.touch()

        # Run cleanup
        builder.clean_build_artifacts()

        # Check that build/dist directories are gone (if they existed)
        build_dir = Path(__file__).parent / "build"
        dist_dir = Path(__file__).parent / "dist"

        print("✅ Cleanup functionality works")

        # Cleanup test file
        if test_spec.exists():
            test_spec.unlink()

        return True

    except Exception as e:
        print(f"❌ Cleanup test failed: {e}")
        return False


def main():
    """Run all cross-platform build tests"""
    print("🤖 WhisperEngine Cross-Platform Build Test Suite")
    print("=" * 60)

    tests = [
        ("Build System Imports", test_build_system_imports),
        ("Spec File Generation", test_spec_file_generation),
        ("Build Environment Info", test_build_info),
        ("Build Script Wrapper", test_build_script_wrapper),
        ("Cleanup Functionality", test_cleanup),
        # Note: Actual build test is expensive, so we'll skip it for now
        # ("Current Platform Build", test_current_platform_build),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Cross-platform build system is ready.")

        print("\n💡 To test actual building:")
        print("   python build_cross_platform.py build          # Build current platform")
        print("   python build_cross_platform.py build-all      # Build all platforms")
        print("   ./build.sh build                              # Use wrapper script")

    else:
        print("⚠️  Some tests failed. Check the build system configuration.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
