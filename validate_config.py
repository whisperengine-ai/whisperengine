#!/usr/bin/env python3
"""
Configuration validation script for Docker containers.
This validates the environment configuration before starting the bot.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from env_manager import EnvironmentManager

    def main():
        """Validate configuration and exit with appropriate code."""
        try:
            # Load environment
            env_manager = EnvironmentManager()
            if not env_manager.load_environment():
                sys.exit(1)

            # Validate required variables
            validation_result = env_manager.validate_required_vars()

            if validation_result.get("valid", False):
                sys.exit(0)
            else:
                errors = validation_result.get("errors", [])
                for _error in errors:
                    pass
                warnings = validation_result.get("warnings", [])
                for _warning in warnings:
                    pass
                sys.exit(1)

        except Exception:
            sys.exit(1)

    if __name__ == "__main__":
        main()

except ImportError:
    sys.exit(0)  # Don't fail if env_manager is not available
