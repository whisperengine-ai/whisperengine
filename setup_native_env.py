#!/usr/bin/env python3
"""
Native Python Environment Setup Utility

This script sets up all necessary dependencies for running the bot in a native Python environment,
including downloading required models for spaCy and other libraries.
"""

import subprocess
import sys
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
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def setup_spacy_models():
    """Download and set up spaCy language models."""
    if not check_package_installed("spacy"):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy"])

    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])

    # Also install large model for better accuracy in native deployments
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_lg"])
    except subprocess.CalledProcessError:
        pass


def main():
    """Main setup function."""

    # Install Python dependencies
    install_requirements()

    # Set up spaCy models
    setup_spacy_models()

    # Check environment file exists
    env_file = Path(".env")
    if not env_file.exists():
        if Path(".env.minimal").exists():
            import shutil

            shutil.copy(".env.minimal", ".env")
        else:
            pass



if __name__ == "__main__":
    main()
