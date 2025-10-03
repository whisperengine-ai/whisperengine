"""
Integration example for External Chat API with existing WhisperEngine bot structure.

This shows how to add the HTTP API to an existing bot without disrupting 
the Discord functionality.
"""

import asyncio
import logging
from aiohttp import web

from src.api.external_chat_api import setup_api_server
from src.core.bot import DiscordBotCore

logger = logging.getLogger(__name__)


class BotWithExternalAPI(DiscordBotCore):
    """
    Extended DiscordBotCore that includes HTTP API functionality.
    
    This demonstrates how to add external API capabilities to existing bots
    without modifying the core Discord functionality.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_server = None
        self.api_runner = None
        self.api_site = None

    async def initialize_api_server(self, host='0.0.0.0', port=8080):
        """Initialize the HTTP API server."""
        try:
            logger.info("🌐 EXTERNAL API: Initializing HTTP API server...")
            
            # Wait for core components to be initialized
            if not self.memory_manager or not self.llm_client:
                logger.warning("Core components not ready, waiting...")
                await asyncio.sleep(1)
            
            # Setup API server using same components as Discord bot
            self.api_server = setup_api_server(
                bot_core=self,
                memory_manager=self.memory_manager,
                llm_client=self.llm_client,
                host=host,
                port=port
            )
            
            # Create runner and site for serving
            self.api_runner = web.AppRunner(self.api_server)
            await self.api_runner.setup()
            
            self.api_site = web.TCPSite(self.api_runner, host, port)
            await self.api_site.start()
            
            logger.info("✅ EXTERNAL API: HTTP API server started on %s:%d", host, port)
            logger.info("🔗 EXTERNAL API: Same AI components as Discord bot")
            
        except Exception as e:
            logger.error("❌ EXTERNAL API: Failed to start HTTP API server: %s", e)
            raise

    async def close_api_server(self):
        """Cleanup API server on shutdown."""
        try:
            if self.api_site:
                await self.api_site.stop()
                logger.info("🌐 EXTERNAL API: HTTP site stopped")
            
            if self.api_runner:
                await self.api_runner.cleanup()
                logger.info("🌐 EXTERNAL API: HTTP runner cleaned up")
                
        except Exception as e:
            logger.error("Error during API server cleanup: %s", e)

    async def start(self):
        """Override start to include API server initialization."""
        # Start Discord bot first
        await super().start()
        
        # Then start API server
        try:
            await self.initialize_api_server()
        except Exception as e:
            logger.error("Failed to start API server: %s", e)
            # Continue without API server rather than crashing the Discord bot

    async def close(self):
        """Override close to include API server cleanup."""
        # Stop API server first
        await self.close_api_server()
        
        # Then stop Discord bot
        await super().close()


# Example usage in run.py or main.py
async def main_with_api():
    """Example of running bot with external API."""
    from src.core.bot import create_bot_core
    
    # Create bot with API support
    bot_core = BotWithExternalAPI()
    
    try:
        # Initialize all components
        await bot_core.initialize_all()
        
        # Start Discord bot and API server
        await bot_core.start()
        
        logger.info("🚀 Bot with External API started successfully")
        logger.info("📱 Discord: Bot is connected and ready")
        logger.info("🌐 HTTP API: Available at http://localhost:8080")
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error("Bot startup failed: %s", e)
        raise
    finally:
        await bot_core.close()


if __name__ == "__main__":
    asyncio.run(main_with_api())