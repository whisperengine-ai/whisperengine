#!/usr/bin/env python3
"""
WhisperEngine Interactive Setup Wizard
A comprehensive onboarding experience for new users with personalized guidance
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import subprocess
import shutil

logger = logging.getLogger(__name__)


class UserExperienceLevel(Enum):
    """User experience levels for personalized guidance"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class DeploymentMode(Enum):
    """Available deployment modes"""
    DISCORD_BOT = "discord"
    DOCKER_COMPOSE = "docker"
    DEVELOPMENT = "development"


@dataclass
class OnboardingProfile:
    """User onboarding profile for personalized setup"""
    experience_level: UserExperienceLevel
    deployment_mode: DeploymentMode
    use_cases: List[str]
    preferred_llm: Optional[str] = None
    has_openai_key: bool = False
    has_docker: bool = False
    wants_memory_features: bool = True
    wants_voice_features: bool = False
    wants_visual_features: bool = True


class InteractiveSetupWizard:
    """
    Interactive setup wizard for WhisperEngine onboarding
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.profile: Optional[OnboardingProfile] = None
        self.config_data: Dict[str, Any] = {}
        
        # Import our existing validation system
        try:
            from src.utils.configuration_validator import ConfigurationValidator
            self.validator = ConfigurationValidator()
        except ImportError:
            logger.warning("Configuration validator not available")
            self.validator = None
    
    def welcome_banner(self):
        """Display welcome banner"""
        print("""
🎭 ═══════════════════════════════════════════════════════════════
   Welcome to WhisperEngine AI Setup Wizard! 
   
   Let's get you up and running with your AI conversation platform.
   This wizard will guide you through the setup process step by step.
═══════════════════════════════════════════════════════════════

""")
    
    def get_user_experience(self) -> UserExperienceLevel:
        """Determine user experience level"""
        print("🎯 First, let's understand your experience level:\n")
        
        options = {
            "1": ("🌱 Beginner", "New to AI bots and Discord development"),
            "2": ("🔧 Intermediate", "Some experience with bots or AI systems"),
            "3": ("⚡ Advanced", "Experienced developer, just want the essentials")
        }
        
        for key, (title, desc) in options.items():
            print(f"   {key}. {title}")
            print(f"      {desc}")
        
        while True:
            choice = input("\nSelect your experience level (1-3): ").strip()
            if choice == "1":
                return UserExperienceLevel.BEGINNER
            elif choice == "2":
                return UserExperienceLevel.INTERMEDIATE
            elif choice == "3":
                return UserExperienceLevel.ADVANCED
            else:
                print("❌ Please enter 1, 2, or 3")
    
    def get_deployment_mode(self) -> DeploymentMode:
        """Determine preferred deployment mode"""
        print("\n🚀 How would you like to run WhisperEngine?\n")
        
        options = {
            "1": ("🤖 Discord Bot", "Run as a Discord bot in your server"),
            "2": (" Docker Setup", "Professional deployment with containers"),
            "3": ("🛠️  Development", "Development environment for contributing")
        }
        
        for key, (title, desc) in options.items():
            print(f"   {key}. {title}")
            print(f"      {desc}")
        
        while True:
            choice = input("\nSelect deployment mode (1-3): ").strip()
            if choice == "1":
                return DeploymentMode.DISCORD_BOT
            elif choice == "2":
                return DeploymentMode.DOCKER_COMPOSE
            elif choice == "3":
                return DeploymentMode.DEVELOPMENT
            else:
                print("❌ Please enter 1, 2, 3, or 4")
    
    def get_use_cases(self) -> List[str]:
        """Determine user's intended use cases"""
        print("\n🎯 What would you like to do with WhisperEngine? (Select all that apply)\n")
        
        options = {
            "1": "💬 Conversational AI assistant",
            "2": "🧠 Memory-enhanced conversations", 
            "3": "🎭 Emotional intelligence & personality",
            "4": "🖼️  Image analysis and description",
            "5": "🎤 Voice interactions (if supported)",
            "6": "📊 Performance monitoring & analytics",
            "7": "🔧 Custom AI development"
        }
        
        for key, desc in options.items():
            print(f"   {key}. {desc}")
        
        print("\nEnter numbers separated by commas (e.g., 1,2,3):")
        
        while True:
            choices = input("Your selections: ").strip()
            
            if not choices:
                print("❌ Please select at least one use case")
                continue
            
            try:
                selected = [int(x.strip()) for x in choices.split(",")]
                if all(1 <= x <= 7 for x in selected):
                    return [options[str(x)] for x in selected]
                else:
                    print("❌ Please enter numbers between 1 and 7")
            except ValueError:
                print("❌ Please enter valid numbers separated by commas")
    
    def get_llm_preference(self) -> Optional[str]:
        """Determine LLM preference"""
        print("\n🤖 Which AI service would you like to use?\n")
        
        options = {
            "1": ("🌐 OpenAI (GPT-4)", "Cloud-based, requires API key, high quality"),
            "2": ("🔴 OpenRouter", "Access to multiple models, requires API key"),
            "3": ("🏠 Local LM Studio", "Run models locally, private, free"),
            "4": ("🦙 Ollama", "Local models, easy setup, privacy-focused"),
            "5": ("❓ Not sure", "Help me choose based on my needs")
        }
        
        for key, (title, desc) in options.items():
            print(f"   {key}. {title}")
            print(f"      {desc}")
        
        while True:
            choice = input("\nSelect LLM service (1-5): ").strip()
            if choice == "1":
                return "openai"
            elif choice == "2":
                return "openrouter"
            elif choice == "3":
                return "lmstudio"
            elif choice == "4":
                return "ollama"
            elif choice == "5":
                return self._recommend_llm_service()
            else:
                print("❌ Please enter 1, 2, 3, 4, or 5")
    
    def _recommend_llm_service(self) -> str:
        """Recommend LLM service based on user profile"""
        print("\n🤔 Let me help you choose...\n")
        
        # Default to lmstudio if profile is not set yet
        if not self.profile:
            print("💡 LM Studio is usually the best starting point!")
            return "lmstudio"
        
        if self.profile.experience_level == UserExperienceLevel.BEGINNER:
            print("📝 For beginners, I recommend:")
            print("   • 🏠 LM Studio - Easy to set up, free, and private")
            print("   • 🌐 OpenAI - If you don't mind paying and want best quality")
            print("\n💡 LM Studio is usually the best starting point!")
            return "lmstudio"
        
        elif self.profile.experience_level == UserExperienceLevel.INTERMEDIATE:
            print("📝 For intermediate users, I recommend:")
            print("   • 🔴 OpenRouter - Access to many models with one API key")
            print("   • 🦙 Ollama - Great local option with easy model management")
            return "openrouter"
        
        else:  # Advanced
            print("📝 For advanced users:")
            print("   • You probably know what you want! 😄")
            print("   • 🦙 Ollama for local deployment")
            print("   • 🔴 OpenRouter for cloud with model variety")
            return "ollama"
    
    def check_system_requirements(self) -> Dict[str, bool]:
        """Check system requirements and tools"""
        print("\n🔍 Checking your system...\n")
        
        requirements = {}
        
        # Check Python version
        python_version = sys.version_info
        requirements["python"] = python_version >= (3, 13)
        status = "✅" if requirements["python"] else "❌"
        print(f"   {status} Python {python_version.major}.{python_version.minor} "
              f"({'✅ Compatible' if requirements['python'] else '❌ Need 3.13+'})")
        
        # Check Git
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            requirements["git"] = True
            print("   ✅ Git (Available)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            requirements["git"] = False
            print("   ❌ Git (Not found - recommended for updates)")
        
        # Check Docker
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            requirements["docker"] = True
            print("   ✅ Docker (Available)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            requirements["docker"] = False
            print("   ⚠️  Docker (Not found - needed for some deployment modes)")
        
        # Check virtual environment
        requirements["venv"] = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        status = "✅" if requirements["venv"] else "⚠️"
        print(f"   {status} Virtual Environment ({'Active' if requirements['venv'] else 'Recommended'})")
        
        # Check disk space
        try:
            disk_usage = shutil.disk_usage(self.project_root)
            free_gb = disk_usage.free / (1024 ** 3)
            requirements["disk_space"] = free_gb >= 2.0
            status = "✅" if requirements["disk_space"] else "⚠️"
            print(f"   {status} Disk Space ({free_gb:.1f}GB free, need 2GB+)")
        except Exception:
            requirements["disk_space"] = True
            print("   ❓ Disk Space (Could not check)")
        
        return requirements
    
    def create_onboarding_profile(self) -> OnboardingProfile:
        """Create user onboarding profile through interactive questions"""
        print("📋 Let's create your personalized setup profile...\n")
        
        # Get basic preferences
        experience = self.get_user_experience()
        deployment = self.get_deployment_mode()
        use_cases = self.get_use_cases()
        llm_preference = self.get_llm_preference()
        
        # Check for API keys
        print("\n🔑 Do you have an OpenAI API key? (y/n): ", end="")
        has_openai = input().strip().lower() in ['y', 'yes', '1', 'true']
        
        # Check system capabilities
        requirements = self.check_system_requirements()
        
        return OnboardingProfile(
            experience_level=experience,
            deployment_mode=deployment,
            use_cases=use_cases,
            preferred_llm=llm_preference,
            has_openai_key=has_openai,
            has_docker=requirements.get("docker", False),
            wants_memory_features="🧠 Memory-enhanced conversations" in use_cases,
            wants_voice_features="🎤 Voice interactions" in use_cases,
            wants_visual_features="🖼️  Image analysis" in use_cases
        )
    
    def generate_configuration(self) -> Dict[str, Any]:
        """Generate configuration based on user profile"""
        print("⚙️ Generating your personalized configuration...\n")
        
        if not self.profile:
            raise ValueError("User profile not created. Run create_onboarding_profile() first.")
        
        config = {
            "# WhisperEngine Configuration": "Generated by Setup Wizard",
            "ENV_MODE": "development" if self.profile.deployment_mode == DeploymentMode.DEVELOPMENT else "production"
        }
        
        # Discord Bot Configuration
        if self.profile.deployment_mode == DeploymentMode.DISCORD_BOT:
            config.update({
                "DISCORD_BOT_TOKEN": "your_discord_bot_token_here",
                "DISCORD_BOT_NAME": "WhisperEngine"
            })
        
        # LLM Configuration
        if self.profile.preferred_llm == "openai":
            config.update({
                "LLM_CHAT_API_URL": "https://api.openai.com/v1",
                "LLM_CHAT_API_KEY": "your_openai_api_key_here" if self.profile.has_openai_key else "sk-placeholder",
                "LLM_CHAT_MODEL": "gpt-4"
            })
        elif self.profile.preferred_llm == "openrouter":
            config.update({
                "LLM_CHAT_API_URL": "https://openrouter.ai/api/v1",
                "LLM_CHAT_API_KEY": "your_openrouter_api_key_here",
                "LLM_CHAT_MODEL": "anthropic/claude-3-sonnet"
            })
        elif self.profile.preferred_llm == "lmstudio":
            config.update({
                "LLM_CHAT_API_URL": "http://localhost:1234/v1",
                "LLM_CHAT_API_KEY": "not-needed",
                "LLM_CHAT_MODEL": "local-model"
            })
        elif self.profile.preferred_llm == "ollama":
            config.update({
                "LLM_CHAT_API_URL": "http://localhost:11434/v1",
                "LLM_CHAT_API_KEY": "not-needed",
                "LLM_CHAT_MODEL": "llama2"
            })
        
        # Feature Configuration
        config.update({
            "ENABLE_EMOTIONAL_INTELLIGENCE": "true" if "🎭 Emotional intelligence" in self.profile.use_cases else "false",
            "ENABLE_PHASE3_MEMORY": "true" if self.profile.wants_memory_features else "false",
            "ENABLE_VISUAL_EMOTION_ANALYSIS": "true" if self.profile.wants_visual_features else "false",
            "ENABLE_PERFORMANCE_MONITORING": "true",
        })
        
        # Database Configuration - Always use HTTP mode for ChromaDB
        if self.profile.deployment_mode == DeploymentMode.DOCKER_COMPOSE:
            config.update({
                "CHROMADB_HTTP_URL": "http://localhost:8000",
                "USE_REDIS_CACHE": "true",
                "REDIS_URL": "redis://localhost:6379"
            })
        else:
            config.update({
                "USE_REDIS_CACHE": "false"
            })
        
        return config
    
    def save_configuration(self, config: Dict[str, Any]) -> str:
        """Save configuration to appropriate .env file"""
        
        if not self.profile:
            raise ValueError("User profile not created. Run create_onboarding_profile() first.")
        
        # Determine filename based on deployment mode
        if self.profile.deployment_mode == DeploymentMode.DISCORD_BOT:
            filename = ".env.discord"
        elif self.profile.deployment_mode == DeploymentMode.DOCKER_COMPOSE:
            filename = ".env.docker"
        else:
            filename = ".env.development"
        
        filepath = self.project_root / filename
        
        # Write configuration
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# WhisperEngine Configuration\n")
            f.write(f"# Generated by Setup Wizard for {self.profile.deployment_mode.value} mode\n")
            f.write(f"# Experience Level: {self.profile.experience_level.value}\n\n")
            
            for key, value in config.items():
                if key.startswith("#"):
                    f.write(f"{key}={value}\n")
                else:
                    f.write(f"{key}={value}\n")
        
        return str(filepath)
    
    def provide_next_steps(self, config_file: str):
        """Provide personalized next steps"""
        print(f"\n🎉 Configuration saved to: {config_file}\n")
        
        if not self.profile:
            print("⚠️ Profile not available, providing general next steps.\n")
            print("🚀 General Next Steps:\n")
            print("   1️⃣ Install dependencies: pip install -r requirements.txt")
            print("   2️⃣ Configure your .env file with API keys")
            print("   3️⃣ Run: python run.py")
            return
        
        print("🚀 Your Next Steps:\n")
        
        # Step 1: Environment setup
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("   1️⃣ Set up virtual environment:")
            print("      python -m venv .venv")
            print("      source .venv/bin/activate  # macOS/Linux")
            print("      .venv\\Scripts\\activate     # Windows")
            print()
        
        # Step 2: Install dependencies
        print("   2️⃣ Install dependencies:")
        if self.profile.deployment_mode == DeploymentMode.DISCORD_BOT:
            print("      pip install -r requirements-discord.txt")
        else:
            print("      pip install -r requirements.txt")
        print()
        
        # Step 3: API Keys and tokens
        if self.profile.deployment_mode == DeploymentMode.DISCORD_BOT:
            print("   3️⃣ Set up Discord Bot:")
            print("      • Go to https://discord.com/developers/applications")
            print("      • Create new application → Bot")
            print(f"      • Copy bot token to {config_file}")
            print("      • Invite bot to your server with proper permissions")
            print()
        
        if self.profile.preferred_llm in ["openai", "openrouter"] and not self.profile.has_openai_key:
            print("   4️⃣ Get API Key:")
            if self.profile.preferred_llm == "openai":
                print("      • Go to https://platform.openai.com/api-keys")
                print("      • Create new API key")
            else:
                print("      • Go to https://openrouter.ai/keys")
                print("      • Create new API key")
            print(f"      • Add key to {config_file}")
            print()
        
        # Step 4: LLM Setup
        if self.profile.preferred_llm in ["lmstudio", "ollama"]:
            print("   5️⃣ Set up local LLM:")
            if self.profile.preferred_llm == "lmstudio":
                print("      • Download LM Studio from https://lmstudio.ai")
                print("      • Download a model (e.g., Llama 2 7B)")
                print("      • Start local server on port 1234")
            else:
                print("      • Install Ollama from https://ollama.ai")
                print("      • Run: ollama pull llama2")
                print("      • Run: ollama serve")
            print()
        
        # Step 5: Run the application
        print("   🎯 Start WhisperEngine:")
        if self.profile.deployment_mode == DeploymentMode.DISCORD_BOT:
            print("      python run.py")
        elif self.profile.deployment_mode == DeploymentMode.DOCKER_COMPOSE:
            print("      docker-compose up")
        else:
            print("      python run.py")
        print()
        
        # Experience-specific tips
        if self.profile.experience_level == UserExperienceLevel.BEGINNER:
            print("💡 Beginner Tips:")
            print("   • Start with LM Studio for easiest setup")
            print("   • Use !help in Discord to see all commands")
            print("   • Check logs if something isn't working")
            print("   • Join our community for support")
        elif self.profile.experience_level == UserExperienceLevel.ADVANCED:
            print("⚡ Advanced Options:")
            print("   • Customize system prompts in prompts/")
            print("   • Enable graph database with Neo4j")
            print("   • Use Docker for production deployment")
            print("   • Check performance with !perf command")
        
        print("\n📚 Need help? Check the documentation or run: python env_manager.py --validate")
    
    async def run_setup_wizard(self):
        """Run the complete interactive setup wizard"""
        try:
            # Welcome
            self.welcome_banner()
            
            # Create user profile
            self.profile = self.create_onboarding_profile()
            
            # Generate configuration
            self.config_data = self.generate_configuration()
            
            # Save configuration
            config_file = self.save_configuration(self.config_data)
            
            # Validate configuration if validator is available
            if self.validator:
                print("\n🔍 Validating your configuration...")
                try:
                    # The validator expects a path, not a boolean
                    validation_results = await self.validator.validate_configuration(test_connections=True)
                    
                    # Calculate overall score from validation results
                    if validation_results:
                        passed_count = sum(1 for result in validation_results if result.is_valid)
                        total_count = len(validation_results)
                        overall_score = (passed_count / total_count * 100) if total_count > 0 else 0
                        
                        if overall_score >= 70:
                            print(f"✅ Configuration looks good! Score: {overall_score:.0f}%")
                        else:
                            print(f"⚠️ Configuration needs attention. Score: {overall_score:.0f}%")
                            print("💡 Run 'python env_manager.py --validate' for detailed feedback")
                    else:
                        print("⚠️ Could not validate configuration - no results returned")
                        
                except Exception as e:
                    print(f"⚠️ Could not validate configuration: {e}")
                    print("💡 You can validate manually later with: python env_manager.py --validate")
            
            # Provide next steps
            self.provide_next_steps(config_file)
            
            print("\n🎉 Setup wizard completed successfully!")
            print("   Welcome to WhisperEngine AI! 🎭")
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n👋 Setup wizard cancelled by user. You can run it again anytime!")
            return False
        except Exception as e:
            print(f"\n❌ Setup wizard failed: {e}")
            logger.exception("Setup wizard error")
            return False


async def main():
    """Main entry point for setup wizard"""
    wizard = InteractiveSetupWizard()
    success = await wizard.run_setup_wizard()
    return success


if __name__ == "__main__":
    # Run the setup wizard
    success = asyncio.run(main())
    sys.exit(0 if success else 1)