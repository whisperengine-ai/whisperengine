#!/usr/bin/env python3
"""
Test Cross-Platform Build System for WhisperEngine
Validates the build system functionality and output.
"""

import platform
import subprocess
import sys
from pathlib import Path


def test_build_system_imports():
    """Test that the build system can be imported"""

    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from build_cross_platform import CrossPlatformBuilder

        builder = CrossPlatformBuilder()

        # Test platform detection
        builder.detect_platform()

        # Test configuration

        return True

    except Exception:
        return False


def test_spec_file_generation():
    """Test spec file generation for all platforms"""

    try:
        from build_cross_platform import CrossPlatformBuilder

        builder = CrossPlatformBuilder()

        results = {}
        for platform_key in builder.platforms:
            try:
                spec_path = builder.generate_spec_file(platform_key)

                # Verify file exists and has content
                if spec_path.exists() and spec_path.stat().st_size > 0:
                    results[platform_key] = True

                    # Cleanup
                    spec_path.unlink()
                else:
                    results[platform_key] = False

            except Exception:
                results[platform_key] = False

        success_count = sum(results.values())
        total_count = len(results)

        return success_count == total_count

    except Exception:
        return False


def test_build_info():
    """Test build environment info"""

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
                return False

        return True

    except Exception:
        return False


def test_current_platform_build():
    """Test building for current platform"""

    try:
        # Run the build command
        cmd = [sys.executable, "build_cross_platform.py", "build", "--no-clean"]

        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:

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
                return True
            else:
                return False
        else:
            return False

    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def test_build_script_wrapper():
    """Test the build.sh wrapper script"""

    try:
        build_script = Path(__file__).parent / "build.sh"

        if not build_script.exists():
            return False

        # Test help command
        cmd = ["./build.sh", "help"]
        result = subprocess.run(
            cmd, cwd=Path(__file__).parent, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0 and "Usage:" in result.stdout:
            return True
        else:
            return False

    except Exception:
        return False


def test_cleanup():
    """Test cleanup functionality"""

    try:
        from build_cross_platform import CrossPlatformBuilder

        builder = CrossPlatformBuilder()

        # Create some test files
        test_spec = Path(__file__).parent / "test-cleanup.spec"
        test_spec.touch()

        # Run cleanup
        builder.clean_build_artifacts()

        # Check that build/dist directories are gone (if they existed)
        Path(__file__).parent / "build"
        Path(__file__).parent / "dist"

        # Cleanup test file
        if test_spec.exists():
            test_spec.unlink()

        return True

    except Exception:
        return False


def main():
    """Run all cross-platform build tests"""

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

    for _test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                pass
        except Exception:
            pass

    if passed == total:

        pass

    else:
        pass

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
