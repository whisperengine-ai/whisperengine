"""
Bot Launcher Module - Centralized Bot Initialization and Startup

This module contains the initialization logic extracted from the main() function.
For now, it's a simple organization - dependency injection will be added later.
"""

import asyncio
import logging
import os
import time
from functools import wraps

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class BotInitializationError(Exception):
    """Exception raised when bot initialization fails."""

    pass


class ConfigurationError(Exception):
    """Exception raised when configuration is invalid."""

    pass


def should_bot_respond(ctx: commands.Context) -> bool:
    """
    Check if this bot instance should respond to the command.
    Returns True if:
    1. The command is sent via DM (always respond), OR
    2. The command message contains this bot's name as a separate word, OR
    3. The command message contains the fallback name "whisperengine" as a separate word

    For guild channels, bot name must be explicitly mentioned to prevent conflicts.
    """
    bot_name = os.getenv("DISCORD_BOT_NAME", "whisperengine").lower()
    fallback_name = "whisperengine"

    if not ctx.guild:  # Always respond to DMs
        return True

    # Split message into words for exact matching
    message_words = ctx.message.content.lower().split()

    # Check if bot name or fallback name appears as a separate word
    return bot_name in message_words or fallback_name in message_words


def bot_name_filter():
    """
    Decorator to add bot name filtering to commands.
    Commands will only execute if should_bot_respond returns True.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            if should_bot_respond(ctx):
                return await func(ctx, *args, **kwargs)
            # If bot shouldn't respond, do nothing (no error message)
            return

        return wrapper

    return decorator


def create_discord_bot() -> commands.Bot:
    """Create and configure the Discord bot instance."""
    logger.info("Creating Discord bot instance...")

    # Set up Discord intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.voice_states = True

    # Create bot instance
    bot = commands.Bot(
        command_prefix="!",
        intents=intents,
        help_command=None,  # Disable default help to use custom one
    )

    logger.info("Discord bot created with prefix '!'")
    return bot


async def start_bot(bot: commands.Bot) -> None:
    """Start the Discord bot with the token from environment."""
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    if not discord_token:
        raise ConfigurationError("DISCORD_BOT_TOKEN not found in environment")

    logger.info("Starting Discord bot...")

    try:
        await bot.start(discord_token)
    except discord.LoginFailure:
        logger.error("Invalid Discord bot token")
        raise ConfigurationError("Invalid Discord bot token")
    except discord.HTTPException as e:
        logger.error(f"Discord HTTP error: {e}")
        raise BotInitializationError(f"Discord connection failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error starting bot: {e}")
        raise BotInitializationError(f"Failed to start bot: {e}")


# For backward compatibility, expose the main function
async def main():
    """
    Simple main function for bot startup.
    The actual main() logic remains in main.py for now.
    """
    logger.info("Bot launcher main() called - delegating to main.py main() function")
    # This will be updated after main.py refactoring
    pass
