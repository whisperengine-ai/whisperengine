#!/usr/bin/env python3
"""
Configuration validation script for Docker containers.
This validates the environment configuration before starting the bot.
"""

import sys
import os
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
                print("❌ Failed to load environment configuration")
                sys.exit(1)
            
            # Validate required variables
            validation_result = env_manager.validate_required_vars()
            
            if validation_result.get('valid', False):
                print("✅ Configuration validation passed")
                sys.exit(0)
            else:
                print("❌ Configuration validation failed:")
                errors = validation_result.get('errors', [])
                for error in errors:
                    print(f"  • {error}")
                warnings = validation_result.get('warnings', [])
                for warning in warnings:
                    print(f"  ⚠️  {warning}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Configuration validation error: {e}")
            sys.exit(1)
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Failed to import environment manager: {e}")
    print("⚠️  Skipping validation - proceeding anyway")
    sys.exit(0)  # Don't fail if env_manager is not available