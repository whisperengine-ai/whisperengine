#!/usr/bin/env python3
"""
WhisperEngine Main Bot Module - Modular Architecture Implementation
Discord Bot with AI capabilities and personality         if "Failed to initialize memory system" in error_msg:
            logger.error("💡 Memory system initialization failed")
                       # Multi-entity handlers removed - using vector-native memoryector store" in error_msg or "Qdrant" in error_msg:
                logger.error("💡 Solution: Start Qdrant with 'docker compose up qdrant'")
            elif "connection" in error_msg:
                logger.error("💡 Solution: Ensure Qdrant server is running and accessible")

This module serves as the main entry point using the new modular architecture.
All components are properly organized and use dependency injection.

Note: Environment loading and logging configuration is handled by the root run.py launcher.
"""

import asyncio
import logging
import os
import sys

# Core modular imports
from src.core.bot import DiscordBotCore
from src.core.bot_launcher import start_bot
# from src.handlers.admin import AdminCommandHandlers  # Disabled - over-engineered
from src.handlers.events import BotEventHandlers
from src.handlers.help import HelpCommandHandlers
# from src.handlers.memory import MemoryCommandHandlers  # Disabled - obsolete API
# Multi-entity handlers removed - using vector-native memory
from src.handlers.status import StatusCommandHandlers
from src.handlers.voice import VoiceCommandHandlers
from src.utils.enhanced_health_server import create_enhanced_health_server

# Enhanced production systems
from src.utils.production_error_handler import (
    ErrorCategory, ErrorSeverity, handle_errors
)

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
        self.bot_core: DiscordBotCore | None = None
        self.bot = None
        self.event_handlers: BotEventHandlers | None = None
        self.command_handlers = {}
        self.health_server = None

    @handle_errors(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.CRITICAL,
        operation="bot_initialization",
        max_retries=1
    )
    async def initialize(self):
        """Initialize all bot components with enhanced error handling and validation."""
        try:
            logger.info("✨ Initializing WhisperEngine Bot with modular architecture...")

            # Step 0: Quick configuration validation
            logger.info("🔍 Validating configuration...")
            essential_valid = await self._validate_essential_config()
            if not essential_valid:
                raise ValueError("Essential configuration is invalid. Please check your .env file.")

            # Step 1: Initialize bot core with all components
            logger.info("⚙️ Initializing bot core components...")
            self.bot_core = DiscordBotCore(debug_mode=self.debug_mode)
            self.bot_core.initialize_all()  # Initialize all components synchronously
            self.bot = self.bot_core.get_bot()  # Get the initialized Discord bot
            logger.info("✅ Bot core components initialized")

            # Step 2: Initialize event handlers
            logger.info("📡 Initializing event handlers...")
            self.event_handlers = BotEventHandlers(self.bot_core)
            logger.info("✅ Event handlers registered")

            # Step 3: Initialize command handlers with dependency injection
            logger.info("🎛️ Initializing command handlers...")
            await self._initialize_command_handlers()
            logger.info("✅ Command handlers initialized")

            # Step 4: Initialize health check server for container orchestration
            await self._initialize_health_server()
            logger.info("✅ Health check server initialized")

            # Get bot name for personalized startup message
            bot_name = os.getenv("DISCORD_BOT_NAME", "")
            if bot_name:
                logger.info("🤖 %s bot initialization complete - all systems ready!", bot_name)
            else:
                logger.info("🤖 WhisperEngine bot initialization complete - all systems ready!")

        except Exception as e:
            await self._handle_initialization_error(e)
            raise

    async def _validate_essential_config(self) -> bool:
        """Validate essential configuration before initialization"""
        essential_vars = ['DISCORD_BOT_TOKEN', 'LLM_CHAT_API_URL']
        
        missing_vars = []
        for var in essential_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error("❌ Missing essential configuration variables: %s", ', '.join(missing_vars))
            logger.error("💡 Please check your .env file and ensure these variables are set")
            return False
        
        return True

    async def _handle_initialization_error(self, error: Exception):
        """Handle initialization errors with helpful messages and suggestions"""
        error_msg = str(error)
        
        # Provide specific guidance for common issues
        if "Failed to initialize memory system" in error_msg or "ChromaDB" in error_msg:
            logger.debug("Memory system initialization issue: %s", error)
            if "ChromaDB server is not available" in error_msg:
                logger.debug("Solution: Start ChromaDB with 'docker compose up chromadb'")
            elif "ChromaDB server connection test failed" in error_msg:
                logger.debug("Solution: Ensure ChromaDB server is running and accessible")
            else:
                logger.debug("Check your database configuration in .env file")
        
        elif "Discord" in error_msg or "Bot" in error_msg:
            logger.debug("Discord bot initialization issue: %s", error)
            logger.error("💡 Check your DISCORD_BOT_TOKEN in .env file")
            logger.error("💡 Ensure your bot has proper permissions in Discord")
        
        elif "LLM" in error_msg or "API" in error_msg:
            logger.error("💥 LLM API initialization failed: %s", error)
            logger.error("💡 Check your LLM_CHAT_API_URL and LLM_CHAT_API_KEY in .env file")
            logger.error("💡 Ensure your LLM service is running and accessible")
        
        elif "configuration" in error_msg.lower() or "invalid" in error_msg.lower():
            logger.error("💥 Configuration error: %s", error)
            logger.error("💡 Run 'python env_manager.py --validate' to check your configuration")
        
        else:
            # For other errors, provide general guidance
            logger.error("💥 Initialization failed: %s", error)
            logger.error("💡 Check the troubleshooting guide: docs/troubleshooting/")
            
            # Show traceback for unknown errors
            import traceback
            logger.debug("Full error details: %s", traceback.format_exc())

    async def _initialize_command_handlers(self):
        """Initialize all command handler modules with proper dependency injection."""

        # Check that bot core is initialized
        if not self.bot_core:
            raise RuntimeError("Bot core not initialized")

        # Get components from bot core
        components = self.bot_core.get_components()

        # Ensure monitoring system is ready before setting up command handlers
        await self.bot_core.ensure_monitoring_ready()
        
        # Import bot command decorators and helpers
        from src.core.bot_launcher import bot_name_filter
        from src.utils.helpers import is_admin

        try:
            # Status commands
            self.command_handlers["status"] = StatusCommandHandlers(
                bot=self.bot,
                bot_name=os.getenv("DISCORD_BOT_NAME", ""),
                llm_client=components["llm_client"],
                memory_manager=components.get("memory_manager"),
                voice_manager=components.get("voice_manager"),
                voice_support_enabled=getattr(self.bot_core, "voice_support_enabled", False),
                image_processor=components.get("image_processor"),
                conversation_history=components.get("conversation_history"),
                conversation_cache=components.get("conversation_cache"),
                heartbeat_monitor=components.get("heartbeat_monitor"),
            )
            self.command_handlers["status"].register_commands(bot_name_filter)
            logger.info("✅ Status command handlers registered")

            # Help commands
            self.command_handlers["help"] = HelpCommandHandlers(
                bot=self.bot,
                bot_name=os.getenv("DISCORD_BOT_NAME", ""),
                voice_manager=components.get("voice_manager"),
                voice_support_enabled=getattr(self.bot_core, "voice_support_enabled", False),
                personality_profiler=None,  # Legacy personality profiler removed
                is_demo_bot=os.getenv("DEMO_BOT", "false").lower() == "true",
            )
            self.command_handlers["help"].register_commands(bot_name_filter, is_admin)
            logger.info("✅ Help command handlers registered")

            # Memory commands - DISABLED (obsolete API, calling non-existent methods)
            # self.command_handlers["memory"] = MemoryCommandHandlers(
            #     bot=self.bot,
            #     memory_manager=components["memory_manager"],
            #     safe_memory_manager=getattr(self.bot_core, "safe_memory_manager", None),
            #     context_memory_manager=getattr(self.bot_core, "context_memory_manager", None),
            #     graph_personality_manager=components.get("graph_personality_manager"),
            #     personality_profiler=None,  # Legacy personality profiler removed
            #     dynamic_personality_profiler=components.get("dynamic_personality_profiler"),
            # )
            # self.command_handlers["memory"].register_commands(is_admin, bot_name_filter)
            logger.info("ℹ️ Memory command handlers disabled (obsolete API - calls non-existent methods)")

            # Admin commands - DISABLED (over-engineered, backup via Discord is impractical)
            # self.command_handlers["admin"] = AdminCommandHandlers(
            #     bot=self.bot,
            #     llm_client=components["llm_client"],
            #     memory_manager=components["memory_manager"],
            #     backup_manager=components.get("backup_manager"),
            #     conversation_history=components.get("conversation_history"),
            #     health_monitor=components.get("health_monitor"),
            #     job_scheduler=getattr(self.bot_core, "job_scheduler", None),
            #     context_memory_manager=getattr(self.bot_core, "context_memory_manager", None),
            #     phase2_integration=components.get("phase2_integration"),
            # )
            # self.command_handlers["admin"].register_commands(is_admin)
            logger.info("ℹ️ Admin command handlers disabled (over-engineered - use Docker/system tools for admin tasks)")

            logger.info("ℹ️ Deleted obsolete command handlers: Privacy, CDL Test, Monitoring")

            # Voice commands (if voice support is available)
            if components.get("voice_manager") is not None:
                self.command_handlers["voice"] = VoiceCommandHandlers(
                    bot=self.bot,
                    voice_manager=components["voice_manager"]
                )
                self.command_handlers["voice"].register_commands(bot_name_filter)
                logger.info("✅ Voice command handlers registered")
            else:
                logger.info("⚠️ Voice command handlers skipped - voice functionality not available")

            # Visual emotion commands - REMOVED: superseded by vector-native multimodal approach
            logger.info("ℹ️ Visual emotion handlers removed - using vector-native multimodal approach")

            # Performance monitoring commands - DISABLED (AI-generated bloat nobody asked for)
            # self.command_handlers["performance"] = create_performance_commands(
            #     bot=self.bot,
            #     llm_client=components["llm_client"],
            #     memory_manager=components["memory_manager"],
            #     emotion_manager=components.get("emotion_manager")
            # )
            # self.command_handlers["performance"].register_commands(bot_name_filter, is_admin)
            logger.info("ℹ️ Performance monitoring commands disabled (AI-generated enterprise bloat)")

            # ℹ️ Multi-entity handlers removed - using vector-native memory approach

            logger.info("ℹ️ Deleted obsolete command handlers: CDL Test, Monitoring")

            # LLM-Powered Self-Memory Commands - ENABLED for CDL knowledge extraction
            from src.handlers.llm_self_memory_commands import create_llm_self_memory_handlers
            bot_name = os.getenv("DISCORD_BOT_NAME", "unknown")
            self.command_handlers["llm_self_memory"] = create_llm_self_memory_handlers(
                bot=self.bot,
                memory_manager=components.get("memory_manager"),
                bot_name=bot_name
            )
            await self.command_handlers["llm_self_memory"].register_commands()
            logger.info("✅ LLM-Powered Self-Memory commands enabled (CDL extraction available)")
            
            # Memory Management Tool Commands - REMOVED as part of memory system simplification
            # Complex LLM-powered memory tools have been removed to focus on core functionality
            logger.info("ℹ️ Memory Management Tool commands removed (memory system simplified)")
            
            # Store command handlers on bot instance for access by events handler
            self.bot.command_handlers = self.command_handlers

        except Exception as e:
            logger.error(f"Failed to initialize command handlers: {e}")
            raise

    async def _initialize_health_server(self):
        """Initialize the health check server for container orchestration."""
        try:
            if not self.bot:
                logger.warning("Bot not available for health server")
                return

            # Get health server configuration from environment
            health_port = int(os.getenv("HEALTH_CHECK_PORT", "9090"))
            health_host = os.getenv("HEALTH_CHECK_HOST", "0.0.0.0")

            # Create and start health server
            self.health_server = create_enhanced_health_server(self.bot, port=health_port, host=health_host, bot_manager=self)
            await self.health_server.start()

            logger.info(f"🏥 Health check server started on {health_host}:{health_port}")

        except Exception as e:
            logger.error(f"Failed to initialize health server: {e}")
            # Don't raise - health server is optional for development
            logger.warning("Continuing without health server...")

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
            # Stop health server first
            if self.health_server:
                await self.health_server.stop()
                logger.info("🏥 Health check server stopped")

            if (
                self.bot_core
                and hasattr(self.bot_core, "shutdown_manager")
                and self.bot_core.shutdown_manager
            ):
                await self.bot_core.shutdown_manager.graceful_shutdown()

            # Get bot name for personalized shutdown message
            bot_name = os.getenv("DISCORD_BOT_NAME", "")
            if bot_name:
                logger.info(f"🌙 {bot_name} bot shutting down gracefully...")
            else:
                logger.info("🌙 WhisperEngine bot shutting down gracefully...")
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

        # Start the bot (signal handlers will handle graceful shutdown)
        await bot_manager.run()

    except Exception as e:
        error_msg = str(e)
        if "Failed to initialize memory system" in error_msg:
            logger.error(f"Fatal error: {e}")
            # Don't print full traceback for known vector store configuration issues
        else:
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
    except Exception as e:
        logger.error(f"Fatal error in sync_main: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(sync_main())
