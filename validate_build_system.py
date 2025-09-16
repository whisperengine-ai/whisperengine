#!/usr/bin/env python3
"""
WhisperEngine Build Validation System
Validates all build methods and deployment options
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


class BuildValidator:
    """Comprehensive build validation for WhisperEngine"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {}
        self.errors = []

    def run_command(self, cmd: list[str], cwd: Path | None = None) -> tuple[bool, str]:
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
                self.results["environment"] = "pass"
                return True
            else:
                self.results["environment"] = "fail"
                self.errors.append(f"Environment: {output}")
                return False

        except (ImportError, ValueError, KeyError) as e:
            self.results["environment"] = "fail"
            self.errors.append(f"Environment: {e}")
            return False

    def validate_dependencies(self) -> bool:
        """Validate all dependency files are consistent"""

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
                all_valid = False
                self.errors.append(f"Missing requirement file: {req_file}")
                continue

            # Test pip check for this file
            success, output = self.run_command(
                [sys.executable, "-m", "pip", "install", "--dry-run", "-r", str(req_path)]
            )

            if success:
                pass
            else:
                all_valid = False
                self.errors.append(f"{req_file}: {output}")

        self.results["dependencies"] = "pass" if all_valid else "fail"
        return all_valid

    def validate_pyinstaller_build(self) -> bool:
        """Validate PyInstaller builds"""

        try:
            # Test the cross-platform builder
            success, output = self.run_command([sys.executable, "build_cross_platform.py", "info"])

            if success:

                # Try a test build (dry run)
                success, output = self.run_command(
                    [sys.executable, "build_cross_platform.py", "build", "--no-clean"]
                )

                if success:
                    self.results["pyinstaller"] = "pass"
                    return True
                else:
                    self.results["pyinstaller"] = "fail"
                    self.errors.append(f"PyInstaller build: {output}")
                    return False
            else:
                self.results["pyinstaller"] = "fail"
                self.errors.append(f"PyInstaller: {output}")
                return False

        except (subprocess.SubprocessError, OSError, ValueError) as e:
            self.results["pyinstaller"] = "fail"
            self.errors.append(f"PyInstaller: {e}")
            return False

    def validate_docker_build(self) -> bool:
        """Validate Docker builds"""

        # Check if Docker is available
        success, output = self.run_command(["docker", "--version"])
        if not success:
            self.results["docker"] = "skip"
            return True

        try:
            # Validate Dockerfile syntax
            dockerfile_path = self.project_root / "docker" / "Dockerfile.multi-stage"
            if not dockerfile_path.exists():
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

                # Clean up test image
                self.run_command(["docker", "rmi", "whisperengine-validation:test"])

                self.results["docker"] = "pass"
                return True
            else:
                self.results["docker"] = "fail"
                self.errors.append(f"Docker build: {output}")
                return False

        except (subprocess.SubprocessError, OSError, ValueError) as e:
            self.results["docker"] = "fail"
            self.errors.append(f"Docker: {e}")
            return False

    def validate_installation_scripts(self) -> bool:
        """Validate installation scripts"""

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
                all_valid = False
                self.errors.append(f"Missing script: {script}")
                continue

            # Check if script is executable (Unix scripts)
            if script.endswith(".sh"):
                if not os.access(script_path, os.X_OK):
                    # Try to fix permissions
                    try:
                        os.chmod(script_path, 0o755)
                    except (OSError, PermissionError):
                        all_valid = False
                        self.errors.append(f"Script permissions: {script}")
                        continue

                # Basic syntax check for shell scripts
                success, output = self.run_command(["bash", "-n", str(script_path)])
                if success:
                    pass
                else:
                    all_valid = False
                    self.errors.append(f"Script syntax: {script}")
            else:
                pass

        self.results["installation_scripts"] = "pass" if all_valid else "fail"
        return all_valid

    def validate_github_workflows(self) -> bool:
        """Validate GitHub Actions workflows"""

        workflows_dir = self.project_root / ".github" / "workflows"
        if not workflows_dir.exists():
            self.results["github_workflows"] = "fail"
            self.errors.append("GitHub workflows: directory missing")
            return False

        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        if not workflow_files:
            self.results["github_workflows"] = "fail"
            self.errors.append("GitHub workflows: no files found")
            return False

        all_valid = True
        for workflow in workflow_files:
            try:
                import yaml

                with open(workflow, encoding="utf-8") as f:
                    yaml.safe_load(f)
            except ImportError:
                break
            except (yaml.YAMLError, OSError, ValueError) as e:
                all_valid = False
                self.errors.append(f"Workflow {workflow.name}: {e}")

        self.results["github_workflows"] = "pass" if all_valid else "fail"
        return all_valid

    def run_all_validations(self) -> bool:
        """Run all validation checks"""

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
            except (subprocess.SubprocessError, OSError, ValueError):
                all_passed = False

        return all_passed

    def generate_report(self) -> dict:
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

        for _check, status in self.results.items():
            {"pass": "✅", "fail": "❌", "skip": "⚠️"}.get(status, "❓")

        report["summary"]

        if self.errors:
            for _error in self.errors:
                pass

        overall = report["overall_status"]

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

    # Exit with appropriate code
    if args.exit_code and not overall_success:
        sys.exit(1)

    return overall_success


if __name__ == "__main__":
    main()
