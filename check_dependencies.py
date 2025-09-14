#!/usr/bin/env python3
"""
Dependency checker for WhisperEngine Web UI
Checks for missing dependencies and provides installation guidance
"""

import sys
import importlib
import subprocess
from typing import List, Dict, Tuple

class DependencyChecker:
    """Check for missing dependencies and provide installation guidance"""
    
    # Core dependencies required for Web UI functionality
    CORE_DEPENDENCIES = {
        "requests": "HTTP client for LLM API calls",
        "fastapi": "Web framework for UI server",
        "uvicorn": "ASGI server for FastAPI",
        "aiohttp": "Async HTTP client",
        "python-dotenv": "Environment configuration",
        "psutil": "System monitoring"
    }
    
    # AI/ML dependencies for advanced features
    AI_DEPENDENCIES = {
        "chromadb": "Vector database for memory",
        "sentence-transformers": "Text embeddings",
        "numpy": "Numerical computing",
        "transformers": "NLP models"
    }
    
    # Optional dependencies
    OPTIONAL_DEPENDENCIES = {
        "redis": "Conversation caching",
        "asyncpg": "PostgreSQL async support",
        "neo4j": "Graph database support"
    }
    
    def __init__(self):
        self.missing_core = []
        self.missing_ai = []
        self.missing_optional = []
        
    def check_dependency(self, package_name: str) -> bool:
        """Check if a single dependency is available"""
        try:
            importlib.import_module(package_name.replace("-", "_"))
            return True
        except ImportError:
            return False
    
    def check_all_dependencies(self) -> Dict[str, List[Tuple[str, str]]]:
        """Check all dependencies and categorize missing ones"""
        
        # Check core dependencies
        for package, description in self.CORE_DEPENDENCIES.items():
            if not self.check_dependency(package):
                self.missing_core.append((package, description))
        
        # Check AI dependencies
        for package, description in self.AI_DEPENDENCIES.items():
            if not self.check_dependency(package):
                self.missing_ai.append((package, description))
        
        # Check optional dependencies
        for package, description in self.OPTIONAL_DEPENDENCIES.items():
            if not self.check_dependency(package):
                self.missing_optional.append((package, description))
        
        return {
            "core": self.missing_core,
            "ai": self.missing_ai,
            "optional": self.missing_optional
        }
    
    def generate_install_commands(self) -> Dict[str, str]:
        """Generate installation commands for missing dependencies"""
        commands = {}
        
        if self.missing_core:
            core_packages = " ".join([pkg for pkg, _ in self.missing_core])
            commands["core"] = f"pip install {core_packages}"
        
        if self.missing_ai:
            ai_packages = " ".join([pkg for pkg, _ in self.missing_ai])
            commands["ai"] = f"pip install {ai_packages}"
        
        if self.missing_optional:
            optional_packages = " ".join([pkg for pkg, _ in self.missing_optional])
            commands["optional"] = f"pip install {optional_packages}"
        
        # Full requirements file command
        commands["all"] = "pip install -r requirements.txt"
        
        return commands
    
    def print_dependency_report(self):
        """Print a comprehensive dependency report"""
        missing = self.check_all_dependencies()
        
        print("🔍 WhisperEngine Dependency Check")
        print("=" * 50)
        
        # Core dependencies
        if missing["core"]:
            print("❌ MISSING CORE DEPENDENCIES (Required for basic functionality):")
            for package, description in missing["core"]:
                print(f"   • {package:20} - {description}")
            print()
        else:
            print("✅ All core dependencies are installed")
        
        # AI dependencies
        if missing["ai"]:
            print("⚠️  MISSING AI DEPENDENCIES (Required for advanced AI features):")
            for package, description in missing["ai"]:
                print(f"   • {package:20} - {description}")
            print()
        else:
            print("✅ All AI dependencies are installed")
        
        # Optional dependencies
        if missing["optional"]:
            print("💡 MISSING OPTIONAL DEPENDENCIES (Enhanced features):")
            for package, description in missing["optional"]:
                print(f"   • {package:20} - {description}")
            print()
        
        # Installation commands
        if any(missing.values()):
            print("🛠️  INSTALLATION COMMANDS:")
            commands = self.generate_install_commands()
            
            if "core" in commands:
                print(f"   Core packages:     {commands['core']}")
            if "ai" in commands:
                print(f"   AI packages:       {commands['ai']}")
            if "optional" in commands:
                print(f"   Optional packages: {commands['optional']}")
            
            print(f"\n   Install all:       {commands['all']}")
            
            # Platform-specific guidance
            print("\n📋 PLATFORM-SPECIFIC NOTES:")
            print("   • macOS with Homebrew Python:")
            print("     pip install --user -r requirements.txt")
            print("   • Externally managed environments:")
            print("     python3 -m venv venv && source venv/bin/activate")
            print("     pip install -r requirements.txt")
            
        else:
            print("🎉 All dependencies are installed! Web UI should work with real AI responses.")
        
        return len(missing["core"]) == 0
    
    def is_web_ui_ready(self) -> bool:
        """Check if Web UI can run with real AI responses"""
        missing = self.check_all_dependencies()
        return len(missing["core"]) == 0

def main():
    """Main function for command-line usage"""
    checker = DependencyChecker()
    is_ready = checker.print_dependency_report()
    
    if is_ready:
        print("\n✅ Ready to run Web UI with real AI responses!")
        sys.exit(0)
    else:
        print("\n❌ Install missing dependencies before running Web UI")
        sys.exit(1)

if __name__ == "__main__":
    main()