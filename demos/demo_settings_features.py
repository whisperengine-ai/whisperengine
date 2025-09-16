#!/usr/bin/env python3
"""
Quick Demo: Desktop App Settings Features
Demonstrates how to use the new settings system in WhisperEngine desktop app.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def demo_settings_features():
    """Demonstrate the new settings features"""

    print("🎉 WhisperEngine Desktop App - Settings System Demo")
    print("=" * 60)

    print("\n🆕 NEW FEATURES ADDED:")
    print("1️⃣ System Prompt Management")
    print("2️⃣ LLM API Configuration")
    print("3️⃣ Discord Bot Setup")
    print("4️⃣ Settings Persistence")
    print("5️⃣ Web UI Settings Page")

    print("\n" + "=" * 60)
    print("📝 SYSTEM PROMPT MANAGEMENT")
    print("=" * 60)

    from src.config.desktop_settings import DesktopSettingsManager

    manager = DesktopSettingsManager()

    # Show current system prompt
    current_prompt = manager.get_active_system_prompt()
    print(f"Current system prompt: {len(current_prompt)} characters")
    print(f"Source: {manager.get_system_prompt_config()['prompt_source']}")

    # Demonstrate custom prompt
    print("\n✏️ Creating custom prompt...")
    custom_prompt = """You are WhisperEngine, a highly intelligent AI assistant specialized in helping developers.

You have expertise in:
- Python programming and best practices
- AI/ML model integration and deployment  
- Discord bot development
- Local LLM setup and configuration
- Privacy-focused AI solutions

Be helpful, accurate, and provide practical examples."""

    success = manager.save_custom_prompt("developer_assistant", custom_prompt)
    print(f"Custom prompt saved: {success}")

    # Set as active
    manager.set_active_prompt("custom", "developer_assistant")
    print("✅ Custom prompt activated")

    print("\n" + "=" * 60)
    print("🤖 LLM API CONFIGURATION")
    print("=" * 60)

    # Demonstrate LLM configuration
    print("Setting up LLM configuration...")

    # Example OpenAI setup
    manager.set_llm_config(
        api_url="https://api.openai.com/v1",
        api_key="sk-your-openai-key-here",
        model_name="gpt-3.5-turbo",
    )
    print("✅ OpenAI configuration saved")

    # Example local LLM setup
    manager.set_llm_config(
        api_url="http://localhost:1234/v1",
        api_key="",  # No key needed for local
        model_name="local-model",
    )
    print("✅ Local LLM configuration saved")

    config = manager.get_llm_config()
    print(f"Current API URL: {config['api_url']}")
    print(f"Current model: {config['model_name']}")

    print("\n" + "=" * 60)
    print("🤖 DISCORD BOT CONFIGURATION")
    print("=" * 60)

    # Demonstrate Discord setup
    print("Setting up Discord bot...")

    # Example Discord token (fake)
    manager.set_discord_token("your-discord-bot-token-here")
    print("✅ Discord bot token saved")

    discord_config = manager.get_discord_config()
    token_length = len(discord_config["bot_token"])
    print(f"Token length: {token_length} characters")

    print("\n" + "=" * 60)
    print("💾 SETTINGS PERSISTENCE")
    print("=" * 60)

    # Show settings file location
    print(f"Settings stored in: {manager.settings_file}")
    print(f"System prompts in: {manager.system_prompts_dir}")

    # Demonstrate export
    export_data = manager.export_settings()
    print(f"Settings export contains: {len(export_data)} sections")
    print(f"Export keys: {list(export_data.keys())}")

    print("\n" + "=" * 60)
    print("🌐 WEB UI ACCESS")
    print("=" * 60)

    print("Access the settings through the web UI:")
    print("1. Start the desktop app: python universal_native_app.py")
    print("2. Click '⚙️ Settings' in the top-right corner")
    print("3. Use the tabbed interface to configure:")
    print("   • 📝 System Prompt (edit, upload files)")
    print("   • 🤖 LLM Configuration (API keys, model discovery)")
    print("   • 🤖 Discord Bot (token validation)")
    print("   • 🎨 UI Preferences (auto-save, themes)")

    print("\n" + "=" * 60)
    print("✨ KEY BENEFITS")
    print("=" * 60)

    print("🔒 Privacy: All settings stored locally in ~/.whisperengine/")
    print("🔄 Persistence: Settings survive app restarts")
    print("✅ Validation: Built-in testing for API keys and tokens")
    print("📁 File Upload: Easy system prompt file management")
    print("🔍 Model Discovery: Automatic detection of available models")
    print("📤 Backup: Export/import settings for easy migration")
    print("🎨 User-Friendly: Beautiful web interface with real-time validation")

    print("\n🚀 Your WhisperEngine desktop app now has comprehensive")
    print("   configuration management for all AI services!")


if __name__ == "__main__":
    asyncio.run(demo_settings_features())
