#!/usr/bin/env python3
"""
Dependency checker for WhisperEngine
Checks for missing dependencies using the new multi-tier dependency structure
"""

import sys
import importlib
import subprocess
from typing import List, Dict, Tuple

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
        "llama_cpp": "Local LLM inference (llama-cpp-python)"
    }
    
    # Discord bot dependencies (requirements-discord.txt)
    DISCORD_DEPENDENCIES = {
        "discord": "Discord API library",
        "asyncpg": "PostgreSQL async support",
        "psycopg2": "PostgreSQL binary driver",
        "redis": "Conversation caching",
        "PyNaCl": "Voice support"
    }
    
    # Desktop app dependencies (requirements-desktop.txt)  
    DESKTOP_DEPENDENCIES = {
        "PySide6": "Cross-platform GUI framework",
        "fastapi": "Web framework for local UI",
        "uvicorn": "ASGI server for FastAPI",
        "aiosqlite": "SQLite async support",
        "pystray": "System tray integration"
    }
    
    # Platform-specific optimizations (requirements-platform.txt)
    PLATFORM_DEPENDENCIES = {
        "mlx": "Apple Silicon optimization (macOS ARM64 only)",
    }
    
    # Optional dependencies for advanced features
    OPTIONAL_DEPENDENCIES = {
        "neo4j": "Graph database support",
        "elevenlabs": "Voice synthesis",
        "audioop": "Audio processing"
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
    
    def check_all_dependencies(self, deployment_type: str = "all") -> Dict[str, List[Tuple[str, str]]]:
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
            "optional": self.missing_optional
        }
    
    def generate_install_commands(self) -> Dict[str, str]:
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
        
        print("🔍 WhisperEngine Multi-Tier Dependency Check")
        print("=" * 60)
        print(f"Deployment Type: {deployment_type}")
        print()
        
        # Core dependencies
        if missing["core"]:
            print("❌ MISSING CORE DEPENDENCIES (Required for all deployments):")
            for package, description in missing["core"]:
                print(f"   • {package:20} - {description}")
            print()
        else:
            print("✅ All core dependencies are installed")
        
        # Discord dependencies
        if deployment_type in ["discord", "all"] and missing["discord"]:
            print("❌ MISSING DISCORD BOT DEPENDENCIES:")
            for package, description in missing["discord"]:
                print(f"   • {package:20} - {description}")
            print()
        elif deployment_type in ["discord", "all"]:
            print("✅ All Discord bot dependencies are installed")
        
        # Desktop dependencies  
        if deployment_type in ["desktop", "all"] and missing["desktop"]:
            print("❌ MISSING DESKTOP APP DEPENDENCIES:")
            for package, description in missing["desktop"]:
                print(f"   • {package:20} - {description}")
            print()
        elif deployment_type in ["desktop", "all"]:
            print("✅ All desktop app dependencies are installed")
        
        # Platform dependencies
        if missing["platform"]:
            print("⚠️  MISSING PLATFORM OPTIMIZATIONS:")
            for package, description in missing["platform"]:
                print(f"   • {package:20} - {description}")
            print()
        
        # Optional dependencies
        if missing["optional"]:
            print("💡 MISSING OPTIONAL DEPENDENCIES (Enhanced features):")
            for package, description in missing["optional"]:
                print(f"   • {package:20} - {description}")
            print()
        
        # Installation commands
        if any(missing.values()):
            print("🛠️  INSTALLATION COMMANDS (New Multi-Tier Structure):")
            commands = self.generate_install_commands()
            
            print("   Manual Installation:")
            print(f"     Core dependencies:     {commands['core']}")
            print(f"     Platform optimizations: {commands['platform']}")
            if deployment_type in ["discord", "all"]:
                print(f"     Discord bot:           {commands['discord']}")
            if deployment_type in ["desktop", "all"]:
                print(f"     Desktop app:           {commands['desktop']}")
            
            print("\n   Automated Installation:")
            if deployment_type in ["discord", "all"]:
                print(f"     Discord bot:           {commands['auto_discord']}")
            if deployment_type in ["desktop", "all"]:
                print(f"     Desktop app:           {commands['auto_desktop']}")
            
            print("\n   For full documentation: DEPENDENCY_MANAGEMENT.md")
            
            # Platform-specific guidance
            print("\n📋 PLATFORM-SPECIFIC NOTES:")
            print("   • Apple Silicon (M1/M2/M3):")
            print("     Automatic MLX optimization available")
            print("   • macOS with Homebrew Python:")
            print("     Use virtual environment: python3 -m venv .venv")
            print("   • Externally managed environments:")
            print("     python3 -m venv .venv && source .venv/bin/activate")
            
        else:
            print("🎉 All dependencies are installed! WhisperEngine should work properly.")
        
        return len(missing["core"]) == 0
    
    def is_deployment_ready(self, deployment_type: str = "all") -> bool:
        """Check if deployment is ready for specified type"""
        missing = self.check_all_dependencies(deployment_type)
        return len(missing["core"]) == 0

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check WhisperEngine dependencies")
    parser.add_argument("--deployment", "-d", 
                       choices=["discord", "desktop", "all"],
                       default="all",
                       help="Deployment type to check")
    
    args = parser.parse_args()
    
    checker = DependencyChecker()
    is_ready = checker.print_dependency_report(args.deployment)
    
    if is_ready:
        print(f"\n✅ Ready to run WhisperEngine ({args.deployment})!")
        sys.exit(0)
    else:
        print(f"\n❌ Install missing dependencies before running {args.deployment} deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()