#!/usr/bin/env python3
"""
WhisperEngine Build Validation System
Validates all build methods and deployment options
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse


class BuildValidator:
    """Comprehensive build validation for WhisperEngine"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {}
        self.errors = []

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except (subprocess.SubprocessError, OSError) as e:
            return False, str(e)

    def validate_environment(self) -> bool:
        """Validate environment configuration"""
        print("🔍 Validating environment configuration...")

        try:
            # Test environment loading
            success, output = self.run_command(
                [
                    sys.executable,
                    "-c",
                    "from env_manager import load_environment; assert load_environment()",
                ]
            )

            if success:
                print("  ✅ Environment configuration valid")
                self.results["environment"] = "pass"
                return True
            else:
                print(f"  ❌ Environment validation failed: {output}")
                self.results["environment"] = "fail"
                self.errors.append(f"Environment: {output}")
                return False

        except (ImportError, ValueError, KeyError) as e:
            print(f"  ❌ Environment validation error: {e}")
            self.results["environment"] = "fail"
            self.errors.append(f"Environment: {e}")
            return False

    def validate_dependencies(self) -> bool:
        """Validate all dependency files are consistent"""
        print("📦 Validating dependencies...")

        req_files = [
            "requirements-core.txt",
            "requirements-desktop.txt",
            "requirements-discord.txt",
            "requirements-platform.txt",
        ]

        all_valid = True

        for req_file in req_files:
            req_path = self.project_root / req_file
            if not req_path.exists():
                print(f"  ❌ Missing {req_file}")
                all_valid = False
                self.errors.append(f"Missing requirement file: {req_file}")
                continue

            # Test pip check for this file
            success, output = self.run_command(
                [sys.executable, "-m", "pip", "install", "--dry-run", "-r", str(req_path)]
            )

            if success:
                print(f"  ✅ {req_file} valid")
            else:
                print(f"  ❌ {req_file} has issues: {output}")
                all_valid = False
                self.errors.append(f"{req_file}: {output}")

        self.results["dependencies"] = "pass" if all_valid else "fail"
        return all_valid

    def validate_pyinstaller_build(self) -> bool:
        """Validate PyInstaller builds"""
        print("🔨 Validating PyInstaller builds...")

        try:
            # Test the cross-platform builder
            success, output = self.run_command([sys.executable, "build_cross_platform.py", "info"])

            if success:
                print("  ✅ PyInstaller builder available")

                # Try a test build (dry run)
                success, output = self.run_command(
                    [sys.executable, "build_cross_platform.py", "build", "--no-clean"]
                )

                if success:
                    print("  ✅ PyInstaller build successful")
                    self.results["pyinstaller"] = "pass"
                    return True
                else:
                    print(f"  ❌ PyInstaller build failed: {output}")
                    self.results["pyinstaller"] = "fail"
                    self.errors.append(f"PyInstaller build: {output}")
                    return False
            else:
                print(f"  ❌ PyInstaller builder failed: {output}")
                self.results["pyinstaller"] = "fail"
                self.errors.append(f"PyInstaller: {output}")
                return False

        except (subprocess.SubprocessError, OSError, ValueError) as e:
            print(f"  ❌ PyInstaller validation error: {e}")
            self.results["pyinstaller"] = "fail"
            self.errors.append(f"PyInstaller: {e}")
            return False

    def validate_docker_build(self) -> bool:
        """Validate Docker builds"""
        print("🐳 Validating Docker builds...")

        # Check if Docker is available
        success, output = self.run_command(["docker", "--version"])
        if not success:
            print("  ⚠️ Docker not available, skipping Docker validation")
            self.results["docker"] = "skip"
            return True

        try:
            # Validate Dockerfile syntax
            dockerfile_path = self.project_root / "docker" / "Dockerfile.multi-stage"
            if not dockerfile_path.exists():
                print("  ❌ Dockerfile.multi-stage not found")
                self.results["docker"] = "fail"
                self.errors.append("Docker: Dockerfile.multi-stage missing")
                return False

            # Test Docker build (base stage only for speed)
            success, output = self.run_command(
                [
                    "docker",
                    "build",
                    "-f",
                    str(dockerfile_path),
                    "--target",
                    "base",
                    "-t",
                    "whisperengine-validation:test",
                    ".",
                ]
            )

            if success:
                print("  ✅ Docker build successful")

                # Clean up test image
                self.run_command(["docker", "rmi", "whisperengine-validation:test"])

                self.results["docker"] = "pass"
                return True
            else:
                print(f"  ❌ Docker build failed: {output}")
                self.results["docker"] = "fail"
                self.errors.append(f"Docker build: {output}")
                return False

        except (subprocess.SubprocessError, OSError, ValueError) as e:
            print(f"  ❌ Docker validation error: {e}")
            self.results["docker"] = "fail"
            self.errors.append(f"Docker: {e}")
            return False

    def validate_installation_scripts(self) -> bool:
        """Validate installation scripts"""
        print("📋 Validating installation scripts...")

        scripts = [
            "setup.sh",
            "setup.bat",
            "scripts/install-desktop.sh",
            "scripts/install-discord.sh",
        ]

        all_valid = True

        for script in scripts:
            script_path = self.project_root / script
            if not script_path.exists():
                print(f"  ❌ Missing {script}")
                all_valid = False
                self.errors.append(f"Missing script: {script}")
                continue

            # Check if script is executable (Unix scripts)
            if script.endswith(".sh"):
                if not os.access(script_path, os.X_OK):
                    print(f"  ⚠️ {script} not executable")
                    # Try to fix permissions
                    try:
                        os.chmod(script_path, 0o755)
                        print(f"  ✅ Fixed permissions for {script}")
                    except (OSError, PermissionError) as e:
                        print(f"  ❌ Cannot fix permissions for {script}: {e}")
                        all_valid = False
                        self.errors.append(f"Script permissions: {script}")
                        continue

                # Basic syntax check for shell scripts
                success, output = self.run_command(["bash", "-n", str(script_path)])
                if success:
                    print(f"  ✅ {script} syntax valid")
                else:
                    print(f"  ❌ {script} syntax error: {output}")
                    all_valid = False
                    self.errors.append(f"Script syntax: {script}")
            else:
                print(f"  ✅ {script} exists")

        self.results["installation_scripts"] = "pass" if all_valid else "fail"
        return all_valid

    def validate_github_workflows(self) -> bool:
        """Validate GitHub Actions workflows"""
        print("🔄 Validating GitHub Actions workflows...")

        workflows_dir = self.project_root / ".github" / "workflows"
        if not workflows_dir.exists():
            print("  ❌ .github/workflows directory missing")
            self.results["github_workflows"] = "fail"
            self.errors.append("GitHub workflows: directory missing")
            return False

        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        if not workflow_files:
            print("  ❌ No workflow files found")
            self.results["github_workflows"] = "fail"
            self.errors.append("GitHub workflows: no files found")
            return False

        all_valid = True
        for workflow in workflow_files:
            try:
                import yaml

                with open(workflow, "r", encoding="utf-8") as f:
                    yaml.safe_load(f)
                print(f"  ✅ {workflow.name} syntax valid")
            except ImportError:
                print("  ⚠️ PyYAML not available, skipping YAML validation")
                break
            except (yaml.YAMLError, OSError, ValueError) as e:
                print(f"  ❌ {workflow.name} invalid: {e}")
                all_valid = False
                self.errors.append(f"Workflow {workflow.name}: {e}")

        self.results["github_workflows"] = "pass" if all_valid else "fail"
        return all_valid

    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print("🚀 WhisperEngine Build Validation")
        print("=" * 50)

        validations = [
            self.validate_environment,
            self.validate_dependencies,
            self.validate_installation_scripts,
            self.validate_github_workflows,
            self.validate_pyinstaller_build,
            self.validate_docker_build,
        ]

        all_passed = True
        for validation in validations:
            try:
                if not validation():
                    all_passed = False
            except (subprocess.SubprocessError, OSError, ValueError) as e:
                print(f"  ❌ Validation failed with exception: {e}")
                all_passed = False
            print()

        return all_passed

    def generate_report(self) -> Dict:
        """Generate validation report"""
        return {
            "overall_status": (
                "pass"
                if all(status in ["pass", "skip"] for status in self.results.values())
                else "fail"
            ),
            "results": self.results,
            "errors": self.errors,
            "summary": {
                "total_checks": len(self.results),
                "passed": len([r for r in self.results.values() if r == "pass"]),
                "failed": len([r for r in self.results.values() if r == "fail"]),
                "skipped": len([r for r in self.results.values() if r == "skip"]),
            },
        }

    def print_summary(self):
        """Print validation summary"""
        report = self.generate_report()

        print("📊 VALIDATION SUMMARY")
        print("=" * 50)

        for check, status in self.results.items():
            emoji = {"pass": "✅", "fail": "❌", "skip": "⚠️"}.get(status, "❓")
            print(f"{emoji} {check.replace('_', ' ').title()}: {status.upper()}")

        print()
        summary = report["summary"]
        print(
            f"Total: {summary['total_checks']} | "
            f"Passed: {summary['passed']} | "
            f"Failed: {summary['failed']} | "
            f"Skipped: {summary['skipped']}"
        )

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")

        overall = report["overall_status"]
        print(f"\n🎯 OVERALL STATUS: {overall.upper()}")

        return overall == "pass"


def main():
    parser = argparse.ArgumentParser(description="WhisperEngine Build Validation")
    parser.add_argument("--output", "-o", help="Output report to JSON file")
    parser.add_argument(
        "--exit-code", action="store_true", help="Exit with non-zero code on validation failure"
    )

    args = parser.parse_args()

    validator = BuildValidator()
    _ = validator.run_all_validations()  # We don't use the return value

    # Print summary
    overall_success = validator.print_summary()

    # Save report if requested
    if args.output:
        report = validator.generate_report()
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to {args.output}")

    # Exit with appropriate code
    if args.exit_code and not overall_success:
        sys.exit(1)

    return overall_success


if __name__ == "__main__":
    main()
