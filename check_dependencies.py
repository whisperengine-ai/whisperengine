#!/usr/bin/env python3
"""
Dependency checker for WhisperEngine
Checks for missing dependencies using the new multi-tier dependency structure
"""

import importlib
import sys


class DependencyChecker:
    """Check for missing dependencies using new multi-tier structure"""

    # Core dependencies (requirements-core.txt) - required for all deployments
    CORE_DEPENDENCIES = {
        "requests": "HTTP client for LLM API calls",
        "aiohttp": "Async HTTP client",
        "python-dotenv": "Environment configuration",
        "psutil": "System monitoring",
        "chromadb": "Vector database for memory",
        "sentence-transformers": "Text embeddings",
        "numpy": "Numerical computing",
        "transformers": "NLP models",
        "llama_cpp": "Local LLM inference (llama-cpp-python)",
    }

    # Discord bot dependencies (requirements-discord.txt)
    DISCORD_DEPENDENCIES = {
        "discord": "Discord API library",
        "asyncpg": "PostgreSQL async support",
        "psycopg2": "PostgreSQL binary driver",
        "redis": "Conversation caching",
        "PyNaCl": "Voice support",
    }

    # Desktop app dependencies (requirements-desktop.txt)
    DESKTOP_DEPENDENCIES = {
        "PySide6": "Cross-platform GUI framework",
        "fastapi": "Web framework for local UI",
        "uvicorn": "ASGI server for FastAPI",
        "aiosqlite": "SQLite async support",
        "pystray": "System tray integration",
    }

    # Platform-specific optimizations (requirements-platform.txt)
    PLATFORM_DEPENDENCIES = {
        "mlx": "Apple Silicon optimization (macOS ARM64 only)",
    }

    # Optional dependencies for advanced features
    OPTIONAL_DEPENDENCIES = {
        "neo4j": "Graph database support",
        "elevenlabs": "Voice synthesis",
        "audioop": "Audio processing",
    }

    def __init__(self):
        self.missing_core = []
        self.missing_discord = []
        self.missing_desktop = []
        self.missing_platform = []
        self.missing_optional = []

    def check_dependency(self, package_name: str) -> bool:
        """Check if a single dependency is available"""
        try:
            importlib.import_module(package_name.replace("-", "_"))
            return True
        except ImportError:
            return False

    def check_all_dependencies(
        self, deployment_type: str = "all"
    ) -> dict[str, list[tuple[str, str]]]:
        """Check dependencies based on deployment type

        Args:
            deployment_type: "discord", "desktop", "all"
        """

        # Check core dependencies (always required)
        for package, description in self.CORE_DEPENDENCIES.items():
            if not self.check_dependency(package):
                self.missing_core.append((package, description))

        # Check deployment-specific dependencies
        if deployment_type in ["discord", "all"]:
            for package, description in self.DISCORD_DEPENDENCIES.items():
                if not self.check_dependency(package):
                    self.missing_discord.append((package, description))

        if deployment_type in ["desktop", "all"]:
            for package, description in self.DESKTOP_DEPENDENCIES.items():
                if not self.check_dependency(package):
                    self.missing_desktop.append((package, description))

        # Check platform-specific dependencies
        for package, description in self.PLATFORM_DEPENDENCIES.items():
            if not self.check_dependency(package):
                self.missing_platform.append((package, description))

        # Check optional dependencies
        for package, description in self.OPTIONAL_DEPENDENCIES.items():
            if not self.check_dependency(package):
                self.missing_optional.append((package, description))

        return {
            "core": self.missing_core,
            "discord": self.missing_discord,
            "desktop": self.missing_desktop,
            "platform": self.missing_platform,
            "optional": self.missing_optional,
        }

    def generate_install_commands(self) -> dict[str, str]:
        """Generate installation commands using new multi-tier structure"""
        commands = {}

        # Use new multi-tier dependency files
        commands["core"] = "pip install -r requirements-core.txt"
        commands["platform"] = "pip install -r requirements-platform.txt"
        commands["discord"] = "pip install -r requirements-discord.txt"
        commands["desktop"] = "pip install -r requirements-desktop.txt"

        # Automated installers
        commands["auto_discord"] = "./scripts/install-discord.sh  # or .bat for Windows"
        commands["auto_desktop"] = "./scripts/install-desktop.sh  # or .bat for Windows"

        return commands

    def print_dependency_report(self, deployment_type: str = "all"):
        """Print a comprehensive dependency report using new multi-tier structure"""
        missing = self.check_all_dependencies(deployment_type)

        # Core dependencies
        if missing["core"]:
            for _package, _description in missing["core"]:
                pass
        else:
            pass

        # Discord dependencies
        if deployment_type in ["discord", "all"] and missing["discord"]:
            for _package, _description in missing["discord"]:
                pass
        elif deployment_type in ["discord", "all"]:
            pass

        # Desktop dependencies
        if deployment_type in ["desktop", "all"] and missing["desktop"]:
            for _package, _description in missing["desktop"]:
                pass
        elif deployment_type in ["desktop", "all"]:
            pass

        # Platform dependencies
        if missing["platform"]:
            for _package, _description in missing["platform"]:
                pass

        # Optional dependencies
        if missing["optional"]:
            for _package, _description in missing["optional"]:
                pass

        # Installation commands
        if any(missing.values()):
            self.generate_install_commands()

            if deployment_type in ["discord", "all"]:
                pass
            if deployment_type in ["desktop", "all"]:
                pass

            if deployment_type in ["discord", "all"]:
                pass
            if deployment_type in ["desktop", "all"]:
                pass

            # Platform-specific guidance

        else:
            pass

        return len(missing["core"]) == 0

    def is_deployment_ready(self, deployment_type: str = "all") -> bool:
        """Check if deployment is ready for specified type"""
        missing = self.check_all_dependencies(deployment_type)
        return len(missing["core"]) == 0


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Check WhisperEngine dependencies")
    parser.add_argument(
        "--deployment",
        "-d",
        choices=["discord", "desktop", "all"],
        default="all",
        help="Deployment type to check",
    )

    args = parser.parse_args()

    checker = DependencyChecker()
    is_ready = checker.print_dependency_report(args.deployment)

    if is_ready:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
