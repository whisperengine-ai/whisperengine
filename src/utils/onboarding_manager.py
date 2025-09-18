#!/usr/bin/env python3
"""
First-Run Detection and Onboarding System
Automatically detects when WhisperEngine is being run for the first time and launches the setup wizard
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List
import asyncio

logger = logging.getLogger(__name__)


class FirstRunDetector:
    """
    Detects first-run conditions and manages onboarding experience
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.setup_markers_file = self.project_root / ".setup_complete"
        self.config_files = [
            ".env",
            ".env.discord", 
            ".env.desktop-app",
            ".env.docker",
            ".env.development"
        ]
    
    def is_first_run(self) -> bool:
        """Check if this is the first time running WhisperEngine"""
        
        # Check if setup completion marker exists
        if self.setup_markers_file.exists():
            return False
        
        # In container mode, check environment variables instead of files
        if self._is_container_mode():
            if self._has_valid_env_configuration():
                # Mark as setup complete if we find valid environment config
                self._mark_setup_complete()
                return False
        else:
            # Check if any configuration files exist with proper tokens/keys
            for config_file in self.config_files:
                config_path = self.project_root / config_file
                if config_path.exists():
                    if self._has_valid_configuration(config_path):
                        # Mark as setup complete if we find valid config
                        self._mark_setup_complete()
                        return False
        
        return True
    
    def _has_valid_configuration(self, config_path: Path) -> bool:
        """Check if a config file has valid essential configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for Discord bot configuration
            has_discord_token = "DISCORD_BOT_TOKEN=" in content and not "your_discord_bot_token_here" in content
            
            # Check for LLM configuration
            has_llm_url = "LLM_CHAT_API_URL=" in content
            
            # Check for API keys (either not needed for local, or present for cloud)
            has_valid_api_key = (
                "LLM_CHAT_API_KEY=not-needed" in content or  # Local LLM
                ("LLM_CHAT_API_KEY=" in content and not "your_" in content and not "sk-placeholder" in content)  # Real API key
            )
            
            # Consider config valid if it has basic LLM setup, and Discord token if needed
            return has_llm_url and has_valid_api_key and (has_discord_token or "DISCORD_BOT_TOKEN=" not in content)
            
        except Exception as e:
            logger.debug(f"Error reading config file {config_path}: {e}")
            return False
    
    def _mark_setup_complete(self):
        """Mark setup as completed"""
        try:
            with open(self.setup_markers_file, 'w', encoding='utf-8') as f:
                f.write("# WhisperEngine setup completed\n")
                f.write(f"# Completed at: {os.popen('date').read().strip()}\n")
        except Exception as e:
            logger.debug(f"Could not create setup marker: {e}")
    
    def _is_container_mode(self) -> bool:
        """Check if running in a container (Docker/Podman/etc.)"""
        return (
            os.path.exists("/.dockerenv") or
            bool(os.getenv("CONTAINER_MODE")) or
            bool(os.getenv("DOCKER_ENV")) or
            os.getenv("ENV_MODE") == "production"
        )
    
    def _has_valid_env_configuration(self) -> bool:
        """Check if environment variables contain valid configuration"""
        # Check for Discord bot configuration
        discord_token = os.getenv("DISCORD_BOT_TOKEN", "")
        has_discord_token = bool(discord_token and not discord_token.startswith("your_"))
        
        # Check for LLM configuration
        llm_url = os.getenv("LLM_CHAT_API_URL", "")
        has_llm_url = bool(llm_url)
        
        # Check for API keys (either not needed for local, or present for cloud)
        llm_api_key = os.getenv("LLM_CHAT_API_KEY", "")
        has_valid_api_key = (
            llm_api_key == "not-needed" or  # Local LLM
            (llm_api_key and not llm_api_key.startswith("your_") and not llm_api_key == "sk-placeholder")  # Real API key
        )
        
        # Consider config valid if it has basic LLM setup and Discord token
        return has_llm_url and has_valid_api_key and has_discord_token
    
    def get_missing_requirements(self) -> List[str]:
        """Get list of missing requirements that prevent running"""
        missing = []
        
        # Check Python version
        if sys.version_info < (3, 9):
            missing.append(f"Python 3.9+ required (current: {sys.version_info.major}.{sys.version_info.minor})")
        
        # Check for essential configuration
        if self._is_container_mode():
            # In container mode, check environment variables
            if not self._has_valid_env_configuration():
                missing.append("Missing required environment variables (DISCORD_BOT_TOKEN, LLM_CHAT_API_URL, etc.)")
        else:
            # In native mode, check for configuration files
            has_any_config = any(
                (self.project_root / config_file).exists() 
                for config_file in self.config_files
            )
            
            if not has_any_config:
                missing.append("No configuration file found (.env, .env.discord, etc.)")
        
        # Check for requirements.txt dependencies (basic check)
        try:
            import discord
            import requests
        except ImportError as e:
            missing.append(f"Missing Python dependencies: {e.name}")
        
        return missing
    
    async def handle_first_run(self) -> bool:
        """Handle first-run experience with setup wizard"""
        print("🎭 Welcome to WhisperEngine AI!")
        print("=" * 50)
        print("It looks like this is your first time running WhisperEngine.")
        print("Let's get you set up with a quick configuration wizard.\n")
        
        # Check for missing requirements
        missing = self.get_missing_requirements()
        if missing:
            print("❌ Some requirements are missing:")
            for item in missing:
                print(f"   • {item}")
            print("\n💡 Please install missing requirements and try again.")
            return False
        
        # Ask if user wants to run setup wizard
        print("Would you like to run the interactive setup wizard? (recommended)")
        print("This will help you configure WhisperEngine for your specific needs.\n")
        
        response = input("Run setup wizard? [Y/n]: ").strip().lower()
        
        if response in ['', 'y', 'yes', '1', 'true']:
            try:
                # Import and run the setup wizard
                from setup_wizard import InteractiveSetupWizard
                
                wizard = InteractiveSetupWizard()
                success = await wizard.run_setup_wizard()
                
                if success:
                    self._mark_setup_complete()
                    print("\n🎉 Setup completed! You can now run WhisperEngine normally.")
                    return True
                else:
                    print("\n⚠️ Setup was not completed. You can run it again anytime with:")
                    print("   python setup_wizard.py")
                    return False
                    
            except ImportError:
                print("❌ Setup wizard not available. Please configure manually.")
                return False
            except Exception as e:
                print(f"❌ Setup wizard failed: {e}")
                return False
        else:
            print("\n📝 Manual setup:")
            print("   1. Copy .env.example to .env")
            print("   2. Edit .env with your configuration")
            print("   3. Run: python run.py")
            print("\n   Or run the wizard later: python setup_wizard.py")
            return False
    
    def get_startup_help(self) -> str:
        """Get helpful startup information for new users"""
        help_text = """
🎭 WhisperEngine AI - Quick Start Guide

📁 Configuration:
   • Discord Bot: Use .env.discord or set ENV_MODE=discord
   • Desktop App: Use .env.desktop-app or set ENV_MODE=desktop-app  
   • Development: Use .env.development or .env

🤖 LLM Setup:
   • Local (Free): LM Studio (localhost:1234) or Ollama (localhost:11434)
   • Cloud (Paid): OpenAI (api.openai.com) or OpenRouter (openrouter.ai)

✨ Quick Commands:
   • Discord Bot: python run.py
   • Desktop App: python universal_native_app.py
   • Setup Wizard: python setup_wizard.py
   • Validate Config: python env_manager.py --validate

💡 Need help? Check the documentation or join our community!
"""
        return help_text


class OnboardingManager:
    """
    Manages the overall onboarding experience and user guidance
    """
    
    def __init__(self):
        self.detector = FirstRunDetector()
        self.user_preferences = {}
    
    async def check_and_handle_onboarding(self) -> bool:
        """
        Check if onboarding is needed and handle it appropriately
        Returns True if the application should continue, False if it should exit
        """
        
        if self.detector.is_first_run():
            print("\n🌟 First time setup detected!")
            success = await self.detector.handle_first_run()
            
            if not success:
                print("\n👋 Setup incomplete. Exiting...")
                print("💡 Run 'python setup_wizard.py' when you're ready to configure WhisperEngine.")
                return False
                
            print("\n✨ Setup complete! Starting WhisperEngine...")
            return True
        else:
            # Not first run, but check for common issues
            missing = self.detector.get_missing_requirements()
            if missing:
                print("⚠️ Configuration issues detected:")
                for item in missing:
                    print(f"   • {item}")
                print("\n💡 Run 'python setup_wizard.py' to reconfigure.")
                
                # Ask if user wants to continue anyway
                response = input("Continue anyway? [y/N]: ").strip().lower()
                return response in ['y', 'yes', '1', 'true']
            
            return True
    
    def show_welcome_back_message(self):
        """Show a friendly welcome back message for returning users"""
        print("🎭 Welcome back to WhisperEngine AI!")
        print("💡 Use --help for command options, or run 'python setup_wizard.py' to reconfigure.")


# Global onboarding manager instance
onboarding_manager = OnboardingManager()


async def ensure_onboarding_complete() -> bool:
    """
    Ensure onboarding is complete before starting the application
    Returns True if app should continue, False if it should exit
    """
    return await onboarding_manager.check_and_handle_onboarding()


def show_startup_help():
    """Show startup help information"""
    detector = FirstRunDetector()
    print(detector.get_startup_help())


if __name__ == "__main__":
    # Allow running this module directly for testing
    async def main():
        detector = FirstRunDetector()
        
        print("🔍 First Run Detection Test")
        print("=" * 30)
        print(f"Is first run: {detector.is_first_run()}")
        print(f"Missing requirements: {detector.get_missing_requirements()}")
        
        if len(sys.argv) > 1 and sys.argv[1] == "--setup":
            await detector.handle_first_run()
    
    asyncio.run(main())