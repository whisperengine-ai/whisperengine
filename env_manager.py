#!/usr/bin/env python3
"""
Enhanced environment configuration manager with best practices.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging

class EnvironmentManager:
    """Centralized environment configuration management."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent
        self.loaded_files = []
        
    def load_environment(self, mode: Optional[str] = None, force_reload: bool = False) -> bool:
        """
        Load environment configuration with proper precedence.
        
        Loading order:
        1. DOTENV_PATH environment variable (highest priority - for deployment subdirectories)
        2. Docker Compose provides base configuration via environment variables
        3. Mode-specific .env.{mode} file (e.g., .env.desktop, .env.development)
        4. Generic .env file provides local overrides and secrets
        
        Args:
            mode: Environment mode (used for logging only)
            force_reload: Clear existing env vars before loading
        """
        if force_reload:
            self._clear_bot_env_vars()
            
        # Check for explicit DOTENV_PATH first (deployment subdirectories)
        explicit_dotenv_path = os.getenv('DOTENV_PATH')
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
        
        # First, try to load mode-specific environment file
        if mode:
            mode_env = self.project_root / f'.env.{mode}'
            if mode_env.exists():
                load_dotenv(mode_env, override=True)
                self.loaded_files.append(str(mode_env))
                success = True
                logging.info(f"✅ Mode-specific .env.{mode} loaded")
        
        # Then load local .env file (overrides mode-specific and Docker environment)
        local_env = self.project_root / '.env'
        if local_env.exists():
            load_dotenv(local_env, override=True)  # Override everything else
            self.loaded_files.append(str(local_env))
            success = True
            logging.info(f"✅ Local .env loaded for {mode} mode")
            logging.debug(f"Loaded files: {', '.join(self.loaded_files)}")
        elif success:
            logging.info(f"✅ Using mode-specific .env.{mode} for {mode} mode")
        else:
            logging.info(f"✅ Using Docker Compose environment for {mode} mode (no local .env)")
            success = True  # Docker provides the base config
            
        return success
        
    def _detect_environment_mode(self) -> str:
        """Auto-detect environment mode."""
        # Check for explicit ENV_MODE setting first
        explicit_mode = os.getenv('ENV_MODE')
        if explicit_mode:
            return explicit_mode.lower()
            
        # Check for container indicators
        if (os.path.exists('/.dockerenv') or 
            os.getenv('CONTAINER_MODE') or
            os.getenv('DOCKER_ENV')):
            return 'production'
            
        # Check for development indicators
        if (os.getenv('DEV_MODE') or
            os.path.exists(self.project_root / 'bot.sh')):
            return 'development'
            
        # Check for any available .env.{mode} files (excluding templates)
        import glob
        env_pattern = str(self.project_root / '.env.*')
        env_files = glob.glob(env_pattern)
        
        # Filter out template files
        env_files = [f for f in env_files if not f.endswith('.example')]
        
        if env_files:
            # Extract mode from first available file (e.g., .env.production -> production)
            first_file = Path(env_files[0])
            mode = first_file.name.split('.env.')[1]
            logging.info(f"Auto-detected mode '{mode}' from available .env files: {[Path(f).name for f in env_files]}")
            return mode
            
        # Default to development for safety
        return 'development'
        
    def _clear_bot_env_vars(self):
        """Clear bot-specific environment variables."""
        bot_prefixes = ['DISCORD_', 'LLM_', 'REDIS_', 'POSTGRES_', 'CHROMADB_']
        for key in list(os.environ.keys()):
            if any(key.startswith(prefix) for prefix in bot_prefixes):
                del os.environ[key]
                
    def validate_required_vars(self) -> Dict[str, Any]:
        """Validate required environment variables."""
        required_vars = {
            'DISCORD_BOT_TOKEN': 'Discord bot token is required',
            'LLM_CHAT_API_URL': 'LLM API URL is required',
            'REDIS_HOST': 'Redis host is required',
            'POSTGRES_HOST': 'PostgreSQL host is required',
        }
        
        missing = []
        for var, description in required_vars.items():
            if not os.getenv(var):
                missing.append(f"{var}: {description}")
                
        return {
            'valid': len(missing) == 0,
            'missing': missing,
            'mode': self._detect_environment_mode(),
            'loaded_files': self.loaded_files
        }
        
    def get_environment_info(self) -> Dict[str, Any]:
        """Get comprehensive environment information."""
        return {
            'mode': self._detect_environment_mode(),
            'loaded_files': self.loaded_files,
            'config': {
                'redis_host': os.getenv('REDIS_HOST', 'not set'),
                'postgres_host': os.getenv('POSTGRES_HOST', 'not set'),
                'chromadb_host': os.getenv('CHROMADB_HOST', 'not set'),
                'llm_api_url': os.getenv('LLM_CHAT_API_URL', 'not set'),
                'debug_mode': os.getenv('DEBUG_MODE', 'false'),
            },
            'validation': self.validate_required_vars()
        }
        
    def get_available_modes(self) -> list:
        """Get list of all available environment modes from .env.{mode} files."""
        import glob
        env_pattern = str(self.project_root / '.env.*')
        env_files = glob.glob(env_pattern)
        
        # Extract modes from files, excluding templates
        modes = []
        for file_path in env_files:
            file_name = Path(file_path).name
            if not file_name.endswith('.example') and file_name.startswith('.env.'):
                mode = file_name.split('.env.')[1]
                modes.append(mode)
                
        return sorted(modes)

# Global instance for easy import
env_manager = EnvironmentManager()

def load_environment(mode: Optional[str] = None) -> bool:
    """Convenience function for loading environment."""
    return env_manager.load_environment(mode)

def validate_environment() -> Dict[str, Any]:
    """Convenience function for validation."""
    return env_manager.validate_required_vars()

if __name__ == "__main__":
    # CLI usage
    import argparse
    parser = argparse.ArgumentParser(description='Environment configuration manager')
    # Get available modes dynamically
    available_modes = env_manager.get_available_modes()
    parser.add_argument('--mode', choices=available_modes if available_modes else ['development', 'production'], 
                       help=f'Environment mode (available: {", ".join(available_modes) if available_modes else "development, production"})')
    parser.add_argument('--validate', action='store_true', 
                       help='Validate configuration')
    parser.add_argument('--info', action='store_true', 
                       help='Show environment info')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    if env_manager.load_environment(args.mode):
        if args.validate:
            validation = env_manager.validate_required_vars()
            if validation['valid']:
                print("✅ All required environment variables are set")
            else:
                print("❌ Missing required environment variables:")
                for missing in validation['missing']:
                    print(f"  - {missing}")
                sys.exit(1)
                
        if args.info:
            info = env_manager.get_environment_info()
            print(f"🔧 Environment mode: {info['mode']}")
            print(f"📁 Loaded files: {', '.join(info['loaded_files'])}")
            print(f"📊 Redis: {info['config']['redis_host']}")
            print(f"🐘 PostgreSQL: {info['config']['postgres_host']}")
            print(f"🔍 ChromaDB: {info['config']['chromadb_host']}")
            print(f"🤖 LLM API: {info['config']['llm_api_url']}")
            print(f"🐛 Debug mode: {info['config']['debug_mode']}")
    else:
        print("❌ Failed to load environment configuration")
        sys.exit(1)
