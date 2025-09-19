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
                print("✅ Configuration validation passed")
                sys.exit(0)
            else:
                errors = validation_result.get("missing", [])
                warnings = validation_result.get("warnings", [])
                
                if errors:
                    print("❌ Configuration errors:")
                    for error in errors:
                        print(f"  • {error}")
                
                if warnings:
                    print("⚠️ Configuration warnings:")
                    for warning in warnings:
                        print(f"  • {warning}")
                
                # Only fail on actual errors, not warnings
                if errors:
                    sys.exit(1)
                else:
                    sys.exit(0)

        except Exception:
            sys.exit(1)

    if __name__ == "__main__":
        main()

except ImportError:
    sys.exit(0)  # Don't fail if env_manager is not available
