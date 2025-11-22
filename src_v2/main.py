import asyncio
import sys
from loguru import logger
from src_v2.config.settings import settings
from src_v2.core.database import db_manager
from src_v2.memory.manager import memory_manager
from src_v2.discord.bot import bot
from src_v2.scripts.migrate import run_migrations
from src_v2.utils.shutdown import shutdown_handler

async def main():
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level=settings.LOG_LEVEL)
    
    logger.info("Starting WhisperEngine 2.0...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER} ({settings.LLM_MODEL_NAME})")
    
    try:
        # Run Migrations
        run_migrations()

        # Initialize components
        logger.info("Initializing database connections...")
        await db_manager.connect_all()
        
        logger.info("Initializing memory system...")
        await memory_manager.initialize()
        
        # Register cleanup tasks
        shutdown_handler.add_cleanup_task(db_manager.disconnect_all)
        
        # Start Discord Bot
        logger.info("Starting Discord Bot...")
        async with bot:
            # Run bot in a task so we can wait for shutdown signal
            bot_task = asyncio.create_task(bot.start(settings.DISCORD_TOKEN.get_secret_value()))
            
            # Wait for shutdown signal (SIGINT/SIGTERM)
            await shutdown_handler.wait_for_shutdown_signal()
            
            # Close bot explicitly
            if not bot.is_closed():
                logger.info("Closing Discord bot...")
                await bot.close()
                
            # Wait for bot task to finish
            try:
                await bot_task
            except Exception as e:
                logger.warning(f"Bot task finished with: {e}")
            
    except Exception as e:
        logger.exception(f"Critical error during startup: {e}")
        sys.exit(1)
    # finally block is removed because cleanup is handled by shutdown_handler

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This might be caught by the signal handler first, but just in case
        pass
    except Exception as e:
        logger.exception(f"Critical error: {e}")
        sys.exit(1)
