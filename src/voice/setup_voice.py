#!/usr/bin/env python3
"""
Voice Setup Script for Discord Bot
Helps configure voice functionality with ElevenLabs
"""

import asyncio
import logging
import os
import sys
from typing import Any

# Suppress info logging for cleaner output
logging.basicConfig(level=logging.WARNING)


def print_header(text: str):
    """Print a formatted header"""


def print_step(step: int, text: str):
    """Print a step with formatting"""


def print_success(text: str):
    """Print success message"""


def print_warning(text: str):
    """Print warning message"""


def print_error(text: str):
    """Print error message"""


def check_dependencies():
    """Check if required dependencies are installed"""
    print_step(1, "Checking Dependencies")

    required_packages = [
        ("discord.py", "discord"),
        ("PyNaCl", "nacl"),
        ("aiohttp", "aiohttp"),
        ("python-dotenv", "dotenv"),
    ]

    missing_packages = []

    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print_success(f"{package_name} is installed")
        except ImportError:
            print_error(f"{package_name} is missing")
            missing_packages.append(package_name)

    # Check FFmpeg
    try:
        import subprocess

        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success("FFmpeg is installed")
        else:
            print_error("FFmpeg not found in PATH")
            missing_packages.append("FFmpeg")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print_error("FFmpeg not found in PATH")
        missing_packages.append("FFmpeg")

    if missing_packages:
        print_warning("Missing dependencies detected!")

        if "FFmpeg" in missing_packages:
            pass

        return False

    print_success("All dependencies are installed!")
    return True


async def test_elevenlabs_connection(api_key: str) -> tuple[bool, list[dict[str, Any]] | None]:
    """Test ElevenLabs API connection"""
    try:
        # Import here to avoid issues if not installed
        from src.llm.elevenlabs_client import ElevenLabsClient

        client = ElevenLabsClient(api_key=api_key)
        voices = await client.get_available_voices()

        if voices:
            return True, voices
        else:
            return False, None

    except ImportError:
        print_error("ElevenLabs client not available - check voice file imports")
        return False, None
    except Exception as e:
        print_error(f"ElevenLabs connection failed: {e}")
        return False, None


def setup_environment():
    """Set up environment configuration"""
    print_step(2, "Environment Configuration")

    env_file = ".env"
    env_exists = os.path.exists(env_file)

    if env_exists:
        print_success(f"Found existing {env_file}")
    else:
        print_warning(f"No {env_file} found - you'll need to create one")

    # Check for ElevenLabs API key
    api_key = os.getenv("ELEVENLABS_API_KEY")

    if not api_key:
        print_warning("ELEVENLABS_API_KEY not found in environment")
        api_key = input("\n🔑 Enter your ElevenLabs API key (or press Enter to skip): ").strip()

        if api_key:
            # Validate the key format (basic check)
            if len(api_key) < 20:
                print_error("API key seems too short - please verify it's correct")
            else:
                print_success("API key provided")
        else:
            print_warning("Skipping API key setup - you'll need to add it manually")
            return None
    else:
        print_success("Found ELEVENLABS_API_KEY in environment")

    return api_key


async def test_voice_functionality(api_key: str):
    """Test voice functionality"""
    print_step(3, "Testing Voice Functionality")

    # Test ElevenLabs connection
    success, voices = await test_elevenlabs_connection(api_key)

    if not success:
        print_error("Failed to connect to ElevenLabs API")
        return False

    if voices:
        print_success(f"Connected to ElevenLabs API - {len(voices)} voices available")

        # Show available voices
        for _i, voice in enumerate(voices[:5], 1):  # Show first 5
            voice.get("name", "Unknown")
            voice.get("voice_id", "Unknown")
            voice.get("category", "Unknown")

        if len(voices) > 5:
            pass
    else:
        print_error("No voices returned from ElevenLabs API")

    # Test TTS
    try:
        from src.llm.elevenlabs_client import ElevenLabsClient

        client = ElevenLabsClient(api_key=api_key)

        test_text = "Hello! This is a test of the voice system."
        audio_data = await client.text_to_speech(test_text)

        if audio_data and len(audio_data) > 1000:  # Basic sanity check
            print_success(f"TTS test successful - generated {len(audio_data)} bytes of audio")
        else:
            print_error("TTS test failed - no audio data generated")
            return False

    except Exception as e:
        print_error(f"TTS test failed: {e}")
        return False

    print_success("Voice functionality test completed successfully!")
    return True


def show_configuration_guide():
    """Show configuration guide"""
    print_step(4, "Configuration Guide")





def main():
    """Main setup function"""
    print_header("Discord Bot Voice Setup")

    # Check dependencies first
    if not check_dependencies():
        print_error("\nPlease install missing dependencies before continuing")
        sys.exit(1)

    # Set up environment
    api_key = setup_environment()

    if api_key:
        # Test functionality
        try:
            success = asyncio.run(test_voice_functionality(api_key))
            if not success:
                print_warning("Voice functionality test failed")
        except Exception as e:
            print_error(f"Error during voice testing: {e}")
            print_warning("Voice testing failed, but bot should still work")

    # Show configuration guide
    show_configuration_guide()

    print_header("Setup Complete!")




if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        sys.exit(1)
