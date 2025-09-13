#!/usr/bin/env python3
"""
Voice Setup Script for Discord Bot
Helps configure voice functionality with ElevenLabs
"""

import os
import sys
import asyncio
import logging
from typing import Optional, List, Dict, Any

# Suppress info logging for cleaner output
logging.basicConfig(level=logging.WARNING)

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_step(step: int, text: str):
    """Print a step with formatting"""
    print(f"\n📋 Step {step}: {text}")

def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")

def print_warning(text: str):
    """Print warning message"""
    print(f"⚠️  {text}")

def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print_step(1, "Checking Dependencies")
    
    required_packages = [
        ('discord.py', 'discord'),
        ('PyNaCl', 'nacl'),
        ('aiohttp', 'aiohttp'),
        ('python-dotenv', 'dotenv')
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
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
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
        print("\nTo install missing Python packages:")
        print("pip install -r requirements.txt")
        
        if "FFmpeg" in missing_packages:
            print("\nTo install FFmpeg:")
            print("macOS: brew install ffmpeg")
            print("Ubuntu/Debian: sudo apt install ffmpeg")
            print("Windows: Download from https://ffmpeg.org/download.html")
        
        return False
    
    print_success("All dependencies are installed!")
    return True

async def test_elevenlabs_connection(api_key: str) -> tuple[bool, Optional[List[Dict[str, Any]]]]:
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
    print("Testing ElevenLabs connection...")
    success, voices = await test_elevenlabs_connection(api_key)
    
    if not success:
        print_error("Failed to connect to ElevenLabs API")
        print("Please check:")
        print("- API key is correct")
        print("- You have ElevenLabs credits")
        print("- Internet connection is working")
        return False
    
    if voices:
        print_success(f"Connected to ElevenLabs API - {len(voices)} voices available")
        
        # Show available voices
        print("\n🎤 Available Voices:")
        for i, voice in enumerate(voices[:5], 1):  # Show first 5
            name = voice.get('name', 'Unknown')
            voice_id = voice.get('voice_id', 'Unknown')
            category = voice.get('category', 'Unknown')
            print(f"  {i}. {name} (ID: {voice_id}, Category: {category})")
        
        if len(voices) > 5:
            print(f"  ... and {len(voices) - 5} more voices")
    else:
        print_error("No voices returned from ElevenLabs API")
    
    # Test TTS
    print("\nTesting Text-to-Speech...")
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
    
    print("\n📝 Add these to your .env file:")
    print("-" * 40)
    print("# ElevenLabs Voice Configuration")
    print("ELEVENLABS_API_KEY=your_api_key_here")
    print("ELEVENLABS_DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel voice")
    print("")
    print("# Voice Features")
    print("VOICE_RESPONSE_ENABLED=true")
    print("VOICE_LISTENING_ENABLED=true")
    print("VOICE_MAX_AUDIO_LENGTH=30")
    print("")
    print("# Optional: Voice Quality Settings")
    print("ELEVENLABS_VOICE_STABILITY=0.5")
    print("ELEVENLABS_VOICE_SIMILARITY_BOOST=0.8")
    print("ELEVENLABS_VOICE_STYLE=0.0")
    print("-" * 40)
    
    print("\n🎮 Voice Commands Available:")
    print("!join                    - Join voice channel")
    print("!leave                   - Leave voice channel")
    print("!speak <text>            - Make bot speak")
    print("!voice_status            - Show voice status")
    print("!voice_help              - Show all voice commands")
    
    print("\n🔧 Advanced Configuration:")
    print("See .env.voice.example for all available settings")
    print("See docs/VOICE_INTEGRATION_GUIDE.md for detailed documentation")

def main():
    """Main setup function"""
    print_header("Discord Bot Voice Setup")
    print("This script will help you set up voice functionality with ElevenLabs")
    
    # Check dependencies first
    if not check_dependencies():
        print_error("\nPlease install missing dependencies before continuing")
        sys.exit(1)
    
    # Set up environment
    api_key = setup_environment()
    
    if api_key:
        # Test functionality
        print("\nTesting voice functionality...")
        try:
            success = asyncio.run(test_voice_functionality(api_key))
            if not success:
                print_warning("Voice functionality test failed")
                print("The bot will still work, but voice features may not function properly")
        except Exception as e:
            print_error(f"Error during voice testing: {e}")
            print_warning("Voice testing failed, but bot should still work")
    
    # Show configuration guide
    show_configuration_guide()
    
    print_header("Setup Complete!")
    print("✅ Voice setup completed!")
    print("\nNext steps:")
    print("1. Start your Discord bot: python run.py")
    print("2. Join a voice channel and use !join")
    print("3. Test with !speak Hello everyone!")
    print("4. Check !voice_help for all commands")
    
    print("\n💡 Tips:")
    print("- Use !voice_status to check current voice status")
    print("- Voice messages are automatically processed when bot is in voice channel")
    print("- Adjust voice settings in .env for different voice characteristics")
    
    print("\n📚 For more information:")
    print("- Read docs/VOICE_INTEGRATION_GUIDE.md")
    print("- Check the ElevenLabs dashboard for usage and billing")
    print("- Monitor bot logs for any voice-related issues")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)
