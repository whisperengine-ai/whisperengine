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




    from src.config.desktop_settings import DesktopSettingsManager

    manager = DesktopSettingsManager()

    # Show current system prompt
    manager.get_active_system_prompt()

    # Demonstrate custom prompt
    custom_prompt = """You are WhisperEngine, a highly intelligent AI assistant specialized in helping developers.

You have expertise in:
- Python programming and best practices
- AI/ML model integration and deployment
- Discord bot development
- Local LLM setup and configuration
- Privacy-focused AI solutions

Be helpful, accurate, and provide practical examples."""

    manager.save_custom_prompt("developer_assistant", custom_prompt)

    # Set as active
    manager.set_active_prompt("custom", "developer_assistant")


    # Demonstrate LLM configuration

    # Example OpenAI setup
    manager.set_llm_config(
        api_url="https://api.openai.com/v1",
        api_key="sk-your-openai-key-here",
        model_name="gpt-3.5-turbo",
    )

    # Example local LLM setup
    manager.set_llm_config(
        api_url="http://localhost:1234/v1",
        api_key="",  # No key needed for local
        model_name="local-model",
    )

    manager.get_llm_config()


    # Demonstrate Discord setup

    # Example Discord token (fake)
    manager.set_discord_token("your-discord-bot-token-here")

    discord_config = manager.get_discord_config()
    len(discord_config["bot_token"])


    # Show settings file location

    # Demonstrate export
    manager.export_settings()







if __name__ == "__main__":
    asyncio.run(demo_settings_features())
