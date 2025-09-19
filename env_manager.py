#!/usr/bin/env python3
"""
Enhanced environment configuration manager with best practices.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class EnvironmentManager:
    """Centralized environment configuration management."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent
        self.loaded_files = []

    def load_environment(self, mode: str | None = None, force_reload: bool = False) -> bool:
        """
        Load environment configuration with proper precedence.

        Loading order:
        1. DOTENV_PATH environment variable (highest priority - for deployment subdirectories)
        2. Docker Compose provides base configuration via environment variables
        3. Generic .env file provides local overrides and secrets
        4. Auto-detection handles mode-specific behavior

        Args:
            mode: Environment mode (used for logging only)
            force_reload: Clear existing env vars before loading
        """
        if force_reload:
            self._clear_bot_env_vars()

        # Check for explicit DOTENV_PATH first (deployment subdirectories)
        explicit_dotenv_path = os.getenv("DOTENV_PATH")
        if explicit_dotenv_path:
            dotenv_path = Path(explicit_dotenv_path)
            if dotenv_path.exists():
                load_dotenv(dotenv_path, override=True)
                self.loaded_files.append(str(dotenv_path))
                logging.info(f"✅ Explicit .env loaded from: {dotenv_path}")
                return True
            else:
                logging.warning(f"⚠️ DOTENV_PATH specified but file not found: {dotenv_path}")

        # Auto-detect mode if not specified
        if mode is None:
            mode = self._detect_environment_mode()

        success = False

        # Load local .env file if it exists
        local_env = self.project_root / ".env"
        if local_env.exists():
            load_dotenv(local_env, override=True)  # Override everything else
            self.loaded_files.append(str(local_env))
            success = True
            logging.info(f"✅ Local .env loaded for {mode} mode")
            logging.debug(f"Loaded files: {', '.join(self.loaded_files)}")
        else:
            logging.info(f"✅ Using Docker Compose environment for {mode} mode (no local .env)")
            success = True  # Docker provides the base config

        return success

    def _detect_environment_mode(self) -> str:
        """Auto-detect environment mode."""
        # Check for explicit ENV_MODE setting first
        explicit_mode = os.getenv("ENV_MODE")
        if explicit_mode:
            return explicit_mode.lower()

        # Check for container indicators
        if os.path.exists("/.dockerenv") or os.getenv("CONTAINER_MODE") or os.getenv("DOCKER_ENV"):
            return "production"

        # Check for development indicators
        if os.getenv("DEV_MODE") or os.path.exists(self.project_root / "bot.sh"):
            return "development"

        # Default to development for safety
        return "development"

    def _clear_bot_env_vars(self):
        """Clear bot-specific environment variables."""
        bot_prefixes = ["DISCORD_", "LLM_", "REDIS_", "POSTGRES_", "CHROMADB_"]
        for key in list(os.environ.keys()):
            if any(key.startswith(prefix) for prefix in bot_prefixes):
                del os.environ[key]

    def validate_required_vars(self) -> dict[str, Any]:
        """Validate required environment variables."""
        # Core required variables (must be present for basic functionality)
        required_vars = {
            "DISCORD_BOT_TOKEN": "Discord bot token is required",
            "LLM_CHAT_API_URL": "LLM API URL is required", 
        }

        # Recommended variables (infrastructure can use defaults but should be set for production)
        recommended_vars = {
            "REDIS_HOST": "Redis host is recommended for optimal caching",
            "POSTGRES_HOST": "PostgreSQL host is recommended for persistent storage",
        }

        missing_required = []
        missing_recommended = []
        
        for var, description in required_vars.items():
            if not os.getenv(var):
                missing_required.append(f"{var}: {description}")
                
        for var, description in recommended_vars.items():
            if not os.getenv(var):
                missing_recommended.append(f"{var}: {description}")

        return {
            "valid": len(missing_required) == 0,
            "missing": missing_required,
            "warnings": missing_recommended,
            "mode": self._detect_environment_mode(),
            "loaded_files": self.loaded_files,
        }

    def get_environment_info(self) -> dict[str, Any]:
        """Get comprehensive environment information."""
        return {
            "mode": self._detect_environment_mode(),
            "loaded_files": self.loaded_files,
            "config": {
                "redis_host": os.getenv("REDIS_HOST", "not set"),
                "postgres_host": os.getenv("POSTGRES_HOST", "not set"),
                "chromadb_host": os.getenv("CHROMADB_HOST", "not set"),
                "llm_api_url": os.getenv("LLM_CHAT_API_URL", "not set"),
                "debug_mode": os.getenv("DEBUG_MODE", "false"),
            },
            "validation": self.validate_required_vars(),
        }

    def get_available_modes(self) -> list:
        """Get list of all available environment modes from .env.{mode} files."""
        import glob

        env_pattern = str(self.project_root / ".env.*")
        env_files = glob.glob(env_pattern)

        # Extract modes from files, excluding templates
        modes = []
        for file_path in env_files:
            file_name = Path(file_path).name
            if not file_name.endswith(".example") and file_name.startswith(".env."):
                mode = file_name.split(".env.")[1]
                modes.append(mode)

        return sorted(modes)


# Global instance for easy import
env_manager = EnvironmentManager()


def load_environment(mode: str | None = None) -> bool:
    """Convenience function for loading environment."""
    return env_manager.load_environment(mode)


def validate_environment() -> dict[str, Any]:
    """Convenience function for validation."""
    return env_manager.validate_required_vars()


if __name__ == "__main__":
    # Enhanced CLI with comprehensive validation and setup
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="WhisperEngine Environment Manager")
    # Get available modes dynamically
    available_modes = env_manager.get_available_modes()
    parser.add_argument(
        "--mode",
        choices=available_modes if available_modes else ["development", "production"],
        help=f'Environment mode (available: {", ".join(available_modes) if available_modes else "development, production"})',
    )
    parser.add_argument("--validate", action="store_true", help="Basic configuration validation")
    parser.add_argument("--validate-full", action="store_true", help="Comprehensive validation with connection tests")
    parser.add_argument("--setup", action="store_true", help="Interactive setup assistant")
    parser.add_argument("--info", action="store_true", help="Show environment info")
    parser.add_argument("--force", action="store_true", help="Force reload environment")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if env_manager.load_environment(args.mode, force_reload=args.force):
        if args.setup:
            # Run interactive setup
            try:
                from src.utils.configuration_validator import interactive_setup
                asyncio.run(interactive_setup())
            except ImportError:
                print("❌ Interactive setup not available. Please ensure all dependencies are installed.")
                sys.exit(1)
        
        elif args.validate_full:
            # Run comprehensive validation
            try:
                from src.utils.configuration_validator import config_validator
                async def run_validation():
                    print("🔍 Running comprehensive configuration validation...")
                    results = await config_validator.validate_configuration(test_connections=True)
                    
                    # Show summary
                    summary = config_validator.get_validation_summary()
                    print(f"\\n📊 Validation Results:")
                    print(f"   ✅ {summary['valid_checks']}/{summary['total_checks']} checks passed ({summary['validation_percentage']}%)")
                    print(f"   🔴 {summary['required_issues']} required issues found")
                    print(f"   🚀 Ready to deploy: {'Yes' if summary['ready_to_deploy'] else 'No'}")
                    
                    # Show detailed results
                    required_issues = [r for r in results if r.level.value == 'required' and not r.is_valid]
                    if required_issues:
                        print(f"\\n🔴 Required Issues:")
                        for issue in required_issues:
                            print(f"   • {issue.variable}: {issue.message}")
                            if issue.suggestion:
                                print(f"     💡 {issue.suggestion}")
                    
                    recommended_issues = [r for r in results if r.level.value == 'recommended' and not r.is_valid]
                    if recommended_issues:
                        print(f"\\n🟡 Recommended Improvements:")
                        for issue in recommended_issues:
                            print(f"   • {issue.variable}: {issue.message}")
                    
                    return summary['ready_to_deploy']
                
                is_valid = asyncio.run(run_validation())
                sys.exit(0 if is_valid else 1)
                
            except ImportError:
                print("❌ Full validation not available. Please ensure all dependencies are installed.")
                sys.exit(1)
        
        elif args.validate:
            # Basic validation
            validation = env_manager.validate_required_vars()
            if validation["valid"]:
                print("✅ Basic configuration validation passed")
                print("💡 For comprehensive validation, use: --validate-full")
            else:
                print("❌ Configuration validation failed")
                print("Missing required variables:")
                for missing in validation["missing"]:
                    print(f"   • {missing}")
                print("\\n💡 Check your .env file or run: --setup")
                sys.exit(1)

        if args.info:
            info = env_manager.get_environment_info()
            print("🌍 Environment Information:")
            for key, value in info.items():
                print(f"   {key}: {value}")
    else:
        print("❌ Failed to load environment configuration")
        print("💡 Try running: --setup")
        sys.exit(1)
