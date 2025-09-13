#!/usr/bin/env python3
"""
WhisperEngine Main Bot Module - Modular Architecture Implementation
Dream of the Endless - A Discord Bot embodying the Sandman

This module serves as the main entry point using the new modular architecture.
All components are properly organized and use dependency injection.

Note: Environment loading and logging configuration is handled by the root run.py launcher.
"""

import asyncio
import logging
import os
import sys
from typing import Optional

# Core modular imports
from src.core.bot import DiscordBotCore
from src.core.bot_launcher import create_discord_bot, start_bot, bot_name_filter
from src.handlers.events import BotEventHandlers
from src.handlers.status import StatusCommandHandlers
from src.handlers.help import HelpCommandHandlers
from src.handlers.memory import MemoryCommandHandlers
from src.handlers.admin import AdminCommandHandlers
from src.handlers.privacy import PrivacyCommandHandlers
from src.handlers.voice import VoiceCommandHandlers
from src.utils.helpers import is_admin

# Logging is already configured by the root launcher
logger = logging.getLogger(__name__)


class ModularBotManager:
    """
    Manages the modular Discord bot architecture.
    
    This class coordinates all the modular components and ensures proper
    initialization and dependency injection.
    """
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the modular bot manager.
        
        Args:
            debug_mode: Enable debug logging and features
        """
        self.debug_mode = debug_mode
        self.bot_core: Optional[DiscordBotCore] = None
        self.bot = None
        self.event_handlers: Optional[BotEventHandlers] = None
        self.command_handlers = {}
        
    async def initialize(self):
        """Initialize all bot components in the correct order."""
        try:
            logger.info("🚀 Initializing WhisperEngine Bot with modular architecture...")
            
            # Step 1: Initialize bot core with all components
            self.bot_core = DiscordBotCore(debug_mode=self.debug_mode)
            self.bot_core.initialize_all()  # Initialize all components synchronously
            self.bot = self.bot_core.get_bot()  # Get the initialized Discord bot
            logger.info("✅ Bot core components initialized")
            
            # Step 2: Initialize event handlers
            self.event_handlers = BotEventHandlers(self.bot_core)
            logger.info("✅ Event handlers registered")
            
            # Step 3: Initialize command handlers with dependency injection
            await self._initialize_command_handlers()
            logger.info("✅ Command handlers initialized")
            
            logger.info("🎭 Dream of the Endless awakens... The modular realm is ready.")
            
        except Exception as e:
            logger.error(f"💥 Failed to initialize bot: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def _initialize_command_handlers(self):
        """Initialize all command handler modules with proper dependency injection."""
        
        # Check that bot core is initialized
        if not self.bot_core:
            raise RuntimeError("Bot core not initialized")
        
        # Get components from bot core
        components = self.bot_core.get_components()
        
        try:
            # Status commands
            self.command_handlers['status'] = StatusCommandHandlers(
                bot=self.bot,
                bot_name=os.getenv('BOT_NAME', ''),
                llm_client=components['llm_client'],
                voice_manager=components.get('voice_manager'),
                voice_support_enabled=getattr(self.bot_core, 'voice_support_enabled', False),
                VOICE_AVAILABLE=hasattr(self.bot_core, 'voice_manager') and components.get('voice_manager') is not None,
                image_processor=components.get('image_processor'),
                conversation_history=components.get('conversation_history'),
                conversation_cache=components.get('conversation_cache'),
                heartbeat_monitor=components.get('heartbeat_monitor')
            )
            self.command_handlers['status'].register_commands(bot_name_filter)
            logger.info("✅ Status command handlers registered")
            
            # Help commands
            self.command_handlers['help'] = HelpCommandHandlers(
                bot=self.bot,
                bot_name=os.getenv('BOT_NAME', ''),
                voice_manager=components.get('voice_manager'),
                voice_support_enabled=getattr(self.bot_core, 'voice_support_enabled', False),
                VOICE_AVAILABLE=hasattr(self.bot_core, 'voice_manager') and components.get('voice_manager') is not None,
                personality_profiler=components.get('personality_profiler')
            )
            self.command_handlers['help'].register_commands(bot_name_filter, is_admin)
            logger.info("✅ Help command handlers registered")
            
            # Memory commands
            self.command_handlers['memory'] = MemoryCommandHandlers(
                bot=self.bot,
                memory_manager=components['memory_manager'],
                safe_memory_manager=getattr(self.bot_core, 'safe_memory_manager', None),
                context_memory_manager=getattr(self.bot_core, 'context_memory_manager', None),
                graph_personality_manager=components.get('graph_personality_manager'),
                personality_profiler=components.get('personality_profiler')
            )
            self.command_handlers['memory'].register_commands(is_admin, bot_name_filter)
            logger.info("✅ Memory command handlers registered")
            
            # Admin commands
            self.command_handlers['admin'] = AdminCommandHandlers(
                bot=self.bot,
                llm_client=components['llm_client'],
                memory_manager=components['memory_manager'],
                backup_manager=components.get('backup_manager'),
                conversation_history=components.get('conversation_history'),
                health_monitor=components.get('health_monitor'),
                job_scheduler=getattr(self.bot_core, 'job_scheduler', None),
                context_memory_manager=getattr(self.bot_core, 'context_memory_manager', None),
                phase2_integration=components.get('phase2_integration')
            )
            self.command_handlers['admin'].register_commands(is_admin)
            logger.info("✅ Admin command handlers registered")
            
            # Privacy commands
            self.command_handlers['privacy'] = PrivacyCommandHandlers(
                bot=self.bot
            )
            self.command_handlers['privacy'].register_commands()
            logger.info("✅ Privacy command handlers registered")
            
            # Voice commands (if voice support is available)
            if components.get('voice_manager') is not None:
                self.command_handlers['voice'] = VoiceCommandHandlers(
                    bot=self.bot,
                    voice_manager=components['voice_manager'],
                    voice_support_enabled=getattr(self.bot_core, 'voice_support_enabled', False),
                    VOICE_AVAILABLE=hasattr(self.bot_core, 'voice_manager') and components.get('voice_manager') is not None
                )
                self.command_handlers['voice'].register_commands()
                logger.info("✅ Voice command handlers registered")
            else:
                logger.info("⚠️ Voice command handlers skipped - voice functionality not available")
            
        except Exception as e:
            logger.error(f"Failed to initialize command handlers: {e}")
            raise
    
    async def run(self):
        """Start the Discord bot."""
        if not self.bot:
            raise RuntimeError("Bot not initialized")
        
        try:
            await start_bot(self.bot)
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources when shutting down."""
        try:
            if self.bot_core and hasattr(self.bot_core, 'shutdown_manager') and self.bot_core.shutdown_manager:
                await self.bot_core.shutdown_manager.graceful_shutdown()
            logger.info("🌙 Dream returns to the realm of sleep...")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """
    Main entry point using the modular architecture.
    
    This initializes all components using dependency injection and proper
    separation of concerns.
    """
    bot_manager = None
    
    try:
        # Initialize the modular bot manager
        bot_manager = ModularBotManager(debug_mode=False)
        await bot_manager.initialize()
        
        # Start the bot
        await bot_manager.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1
    finally:
        if bot_manager:
            await bot_manager.cleanup()
    
    return 0


def sync_main():
    """Synchronous wrapper for the main async function."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error in sync_main: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(sync_main())