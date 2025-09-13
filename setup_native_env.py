#!/usr/bin/env python3
"""
Native Python Environment Setup Utility

This script sets up all necessary dependencies for running the bot in a native Python environment,
including downloading required models for spaCy and other libraries.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_package_installed(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_requirements():
    """Install Python dependencies from requirements.txt."""
    print("📦 Installing Python dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Dependencies installed successfully!")

def setup_spacy_models():
    """Download and set up spaCy language models."""
    if not check_package_installed("spacy"):
        print("⚠️ spaCy not found. Installing spaCy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy"])
    
    print("📦 Installing spaCy English language models...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    print("✅ Small spaCy model (en_core_web_sm) installed successfully!")
    
    # Also install large model for better accuracy in native deployments
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_lg"])
        print("✅ Large spaCy model (en_core_web_lg) installed successfully!")
    except subprocess.CalledProcessError:
        print("⚠️ Large spaCy model installation failed. Small model will be used.")
        print("   You can install it later with: python -m spacy download en_core_web_lg")

def main():
    """Main setup function."""
    print("🤖 Setting up native Python environment for Discord Bot...")
    
    # Install Python dependencies
    install_requirements()
    
    # Set up spaCy models
    setup_spacy_models()
    
    # Check environment file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️ No .env file found! Creating from minimal template...")
        if Path(".env.minimal").exists():
            import shutil
            shutil.copy(".env.minimal", ".env")
            print("✅ Created .env from minimal template. Please update with your Discord token!")
        else:
            print("❌ No .env templates found. Please create .env file manually.")
    
    print("\n🚀 Setup complete! You can now run the bot with: python run.py")

if __name__ == "__main__":
    main()