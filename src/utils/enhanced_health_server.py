"""
Enhanced Health Server with Chat API for Web UI Integration
Extends the basic health server to include chat endpoints that integrate with
the universal chat orchestrator for seamless web UI communication.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import discord
from aiohttp import web
from discord.ext import commands

# Import normalized bot name function
try:
    from src.memory.vector_memory_system import get_normalized_bot_name_from_env
except ImportError:
    def get_normalized_bot_name_from_env():
        import os
        return os.getenv('DISCORD_BOT_NAME', 'WhisperEngine')

from src.platforms.universal_chat import (
    UniversalChatOrchestrator,
    Message,
    ChatPlatform,
    MessageType,
    create_universal_chat_platform
)
from src.identity.universal_identity import (
    UniversalIdentityManager,
    create_identity_manager
)

logger = logging.getLogger(__name__)

# Configure aiohttp access logs to use DEBUG level to reduce log spam
access_logger = logging.getLogger("aiohttp.access")
access_logger.setLevel(logging.WARNING)


class EnhancedHealthServer:
    """HTTP server with health checks AND chat API endpoints for web UI integration"""

    def __init__(self, bot: commands.Bot, port: int = 9090, host: str = "0.0.0.0", bot_manager=None):
        self.bot = bot
        self.bot_manager = bot_manager  # Reference to ModularBotManager for accessing event_handlers
        self.port = port
        self.host = host
        # Disable aiohttp access logging to prevent health check spam
        self.app = web.Application(logger=logger)
        self.runner = None
        self.site = None
        
        # Initialize universal chat components
        self.universal_orchestrator: Optional[UniversalChatOrchestrator] = None
        self.identity_manager: Optional[UniversalIdentityManager] = None
        
        self.setup_routes()
        # Universal chat will be initialized when server starts

    def setup_routes(self):
        """Configure HTTP routes"""
        # Health check routes (existing)
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_get("/ready", self.readiness_check)
        self.app.router.add_get("/metrics", self.metrics)
        self.app.router.add_get("/status", self.detailed_status)
        
        # New chat API routes for web UI
        self.app.router.add_post("/api/chat", self.handle_chat_message)
        self.app.router.add_get("/api/bot-info", self.get_bot_info)
        self.app.router.add_options("/api/chat", self.handle_cors_preflight)
        
        # CORS middleware setup
        self.app.middlewares.append(self.cors_middleware)

    async def _initialize_universal_chat(self):
        """Initialize universal chat orchestrator and identity management (lazy initialization)"""
        try:
            logger.info("🔄 Initializing universal chat components for enhanced health server...")
            
            # Initialize identity manager
            self.identity_manager = create_identity_manager()
            logger.info("✅ Identity manager initialized")
            
            # Note: We'll defer finding the universal orchestrator until the first chat request
            # since bot cogs may not be loaded yet when health server starts
            logger.info("ℹ️ Universal orchestrator will be initialized on first chat request")
            
        except Exception as e:
            logger.error(f"Failed to initialize universal chat components: {e}")
            logger.warning("Chat API will fall back to basic responses")

    async def _get_or_create_universal_orchestrator(self):
        """Get existing universal orchestrator or create a new one (lazy initialization)"""
        if self.universal_orchestrator:
            return self.universal_orchestrator
            
        try:
            # Try to get existing universal chat orchestrator from bot manager's event handlers
            logger.error(f"🚨 DEBUG: bot_manager={self.bot_manager is not None}")
            if self.bot_manager and hasattr(self.bot_manager, 'event_handlers'):
                event_handlers = self.bot_manager.event_handlers
                logger.error(f"🚨 DEBUG: event_handlers={event_handlers is not None}")
                if event_handlers and hasattr(event_handlers, 'chat_orchestrator'):
                    orchestrator = getattr(event_handlers, 'chat_orchestrator', None)
                    logger.error(f"🚨 DEBUG: event_handlers.chat_orchestrator={orchestrator is not None}")
                    if orchestrator:
                        # Check if this orchestrator has proper bot_core setup
                        bot_core_check = getattr(orchestrator, 'bot_core', None)
                        memory_manager_check = hasattr(bot_core_check, 'memory_manager') if bot_core_check else False
                        logger.error(f"🚨 DEBUG: Found orchestrator bot_core={bot_core_check is not None}, memory_manager={memory_manager_check}")
                        
                        # 🔥 FIX: If bot_core doesn't have memory_manager, add it from event_handlers
                        if bot_core_check and not memory_manager_check:
                            event_memory_manager = getattr(event_handlers, 'memory_manager', None)
                            logger.error(f"🚨 FIX: event_handlers.memory_manager={event_memory_manager is not None}")
                            if event_memory_manager:
                                setattr(bot_core_check, 'memory_manager', event_memory_manager)
                                logger.info("✅ Added memory_manager to bot_core for CDL routing")
                            else:
                                logger.warning("⚠️ Could not find memory_manager in event_handlers")
                        
                        # 🔥 FIX: Also add llm_client if missing
                        llm_client_check = hasattr(bot_core_check, 'llm_client') if bot_core_check else False
                        if bot_core_check and not llm_client_check:
                            event_llm_client = getattr(event_handlers, 'llm_client', None)
                            logger.error(f"🚨 FIX: event_handlers.llm_client={event_llm_client is not None}")
                            if event_llm_client:
                                setattr(bot_core_check, 'llm_client', event_llm_client)
                                logger.info("✅ Added llm_client to bot_core for CDL routing")
                            else:
                                logger.warning("⚠️ Could not find llm_client in event_handlers")
                        
                        self.universal_orchestrator = orchestrator
                        # 🚨 CRITICAL: Ensure bot has memory_manager for CDL routing
                        if self.bot_manager and hasattr(self.bot_manager, 'event_handlers') and self.bot_manager.event_handlers.memory_manager:
                            self.bot.memory_manager = self.bot_manager.event_handlers.memory_manager
                            logger.info("✅ Added memory_manager to bot for CDL routing (existing orchestrator)")
                        
                        # 🚨 CRITICAL: Ensure existing orchestrator has bot_core set for CDL
                        self.universal_orchestrator.set_bot_core(self.bot)
                        logger.info("✅ Found existing universal chat orchestrator from bot manager event handlers with CDL integration")
                        return self.universal_orchestrator
                    else:
                        logger.info("⚠️ Event handlers have chat_orchestrator attribute but it's None")
                else:
                    logger.info("ℹ️ Event handlers don't have chat_orchestrator attribute")
            else:
                logger.info("ℹ️ Bot manager or event handlers not available")
            
            # Try to get from bot cogs as fallback (for traditional Discord.py setup)
            logger.info(f"🔍 Searching bot cogs as fallback: {list(self.bot.cogs.keys())}")
            
            for cog_name, cog in self.bot.cogs.items():
                logger.info(f"🔍 Checking cog '{cog_name}' for chat_orchestrator attribute")
                if hasattr(cog, 'chat_orchestrator'):
                    orchestrator = getattr(cog, 'chat_orchestrator', None)
                    if orchestrator:
                        self.universal_orchestrator = orchestrator
                        # 🚨 CRITICAL: Ensure bot has memory_manager for CDL routing
                        if self.bot_manager and hasattr(self.bot_manager, 'event_handlers') and self.bot_manager.event_handlers.memory_manager:
                            self.bot.memory_manager = self.bot_manager.event_handlers.memory_manager
                            logger.info("✅ Added memory_manager to bot for CDL routing (cog orchestrator)")
                        
                        # 🚨 CRITICAL: Ensure existing orchestrator has bot_core set for CDL
                        self.universal_orchestrator.set_bot_core(self.bot)
                        logger.info(f"✅ Found existing universal chat orchestrator from bot cog '{cog_name}' with CDL integration")
                        return self.universal_orchestrator
                    else:
                        logger.info(f"⚠️ Cog '{cog_name}' has chat_orchestrator attribute but it's None")
                else:
                    logger.info(f"ℹ️ Cog '{cog_name}' does not have chat_orchestrator attribute")
            
            logger.info("🔍 No existing orchestrator found, attempting to create new one...")
            # Initialize our own universal chat orchestrator if none found
            # Try multiple ways to get the database manager
            db_manager = None
            
            # Method 1: Direct from bot
            db_manager = getattr(self.bot, 'db_manager', None)
            
            # Method 2: From bot_manager
            if not db_manager and self.bot_manager:
                db_manager = getattr(self.bot_manager, 'db_manager', None)
            
            # Method 3: From event handlers
            if not db_manager and self.bot_manager and hasattr(self.bot_manager, 'event_handlers'):
                db_manager = getattr(self.bot_manager.event_handlers, 'db_manager', None)
            
            # Method 4: Create new one
            if not db_manager:
                logger.info("🔧 Creating database manager for health server...")
                try:
                    from src.database.database_integration import DatabaseIntegrationManager
                    db_manager = DatabaseIntegrationManager()
                    logger.info("✅ Created database manager for health server")
                except Exception as e:
                    logger.error(f"❌ Failed to create database manager: {e}")
            
            if db_manager:
                self.universal_orchestrator = UniversalChatOrchestrator(
                    db_manager=db_manager,
                    bot_core=self.bot,
                    use_enhanced_core=True
                )
                # 🚨 CRITICAL: Ensure bot has memory_manager for CDL routing
                if self.bot_manager and hasattr(self.bot_manager, 'event_handlers') and self.bot_manager.event_handlers.memory_manager:
                    self.bot.memory_manager = self.bot_manager.event_handlers.memory_manager
                    logger.info("✅ Added memory_manager to bot for CDL routing")
                else:
                    logger.warning("⚠️ Could not set memory_manager on bot - CDL may not work")
                
                # 🚨 CRITICAL: Set bot core to enable CDL character system
                self.universal_orchestrator.set_bot_core(self.bot)
                logger.info("✅ Created new universal chat orchestrator for health server with CDL integration")
                return self.universal_orchestrator
            else:
                logger.warning("Database manager not available - will use fallback responses")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get/create universal chat orchestrator: {e}")
            return None

    @web.middleware
    async def cors_middleware(self, request, handler):
        """Handle CORS for web UI requests"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    async def handle_cors_preflight(self, request):
        """Handle CORS preflight requests"""
        return web.Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
        )

    async def handle_chat_message(self, request):
        """Handle chat messages from web UI"""
        try:
            # Parse request data
            data = await request.json()
            user_id = data.get('user_id', 'web_user')
            message_content = data.get('message', '')
            platform = data.get('platform', 'WEB_UI')
            # Extract user display name for CDL integration consistency with Discord
            user_display_name = data.get('display_name') or data.get('username') or f"web_user_{user_id[:8]}"
            
            if not message_content.strip():
                return web.json_response(
                    {"error": "Message content cannot be empty"}, 
                    status=400
                )
            
            logger.info(f"🌐 Chat API: Received message from {user_id} ({user_display_name}): {message_content[:50]}...")
            
            # Auto-detect and store user name if present
            try:
                from src.utils.automatic_name_storage import create_automatic_name_storage
                from src.llm.llm_protocol import create_llm_client
                
                # Create name storage system if memory manager available
                memory_manager = None
                if self.bot_manager and hasattr(self.bot_manager, 'event_handlers'):
                    memory_manager = getattr(self.bot_manager.event_handlers, 'memory_manager', None)
                
                if memory_manager:
                    llm_client = create_llm_client() if hasattr(self, 'bot') else None
                    name_storage = create_automatic_name_storage(memory_manager, llm_client)
                    detected_name = await name_storage.process_message_for_names(user_id, message_content)
                    if detected_name:
                        logger.info(f"🏷️ Auto-detected name '{detected_name}' for user {user_id}")
            except Exception as e:
                logger.debug(f"Name detection failed: {e}")
            
            # Create universal message
            universal_message = Message(
                message_id=f"web_{datetime.now().timestamp()}",
                user_id=user_id,
                content=message_content,
                message_type=MessageType.TEXT,
                platform=ChatPlatform.WEB_UI,
                timestamp=datetime.now()
            )
            
            # Process message through universal orchestrator if available
            orchestrator = await self._get_or_create_universal_orchestrator()
<<<<<<< Updated upstream
            logger.error(f"🚨 HEALTH SERVER DEBUG: orchestrator={orchestrator is not None}")
=======
            logger.info(f"🔍 HEALTH SERVER DEBUG: Orchestrator available: {orchestrator is not None}")
>>>>>>> Stashed changes
            if orchestrator:
                logger.info(f"🔍 HEALTH SERVER DEBUG: Orchestrator character_system: {orchestrator.character_system is not None}")
                try:
                    # Generate AI response using universal system
                    conversation_context = await orchestrator.build_conversation_context(
                        user_id, "web_chat", message_content
                    )
<<<<<<< Updated upstream
                    logger.error(f"🚨 HEALTH SERVER DEBUG: About to call generate_ai_response")
                    ai_response = await orchestrator.generate_ai_response(
                        universal_message, 
                        conversation_context,
                        user_display_name=user_display_name  # Pass user display name for CDL consistency
                    )
                    logger.error(f"🚨 HEALTH SERVER DEBUG: generate_ai_response completed")
=======
                    logger.info(f"🔍 HEALTH SERVER DEBUG: About to call generate_ai_response")
                    try:
                        ai_response = await orchestrator.generate_ai_response(
                            universal_message, 
                            conversation_context,
                            user_display_name=user_display_name  # Pass user display name for CDL consistency
                        )
                        logger.info(f"🔍 HEALTH SERVER DEBUG: AI response generated: {len(str(ai_response))} chars")
                    except Exception as e:
                        logger.error(f"🚨 HEALTH SERVER ERROR: generate_ai_response failed: {e}")
                        logger.error(f"🚨 HEALTH SERVER ERROR: Exception type: {type(e)}")
                        import traceback
                        logger.error(f"🚨 HEALTH SERVER ERROR: Stack trace: {traceback.format_exc()}")
                        raise
>>>>>>> Stashed changes
                    
                    response_content = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
                    
                    # Store conversation pair
                    await orchestrator.store_conversation_pair(
                        user_id, "web_chat", message_content, response_content
                    )
                    
                    # CRITICAL FIX: Also store directly through memory manager if available
                    # This ensures proper vector storage regardless of orchestrator issues
                    if self.bot_manager and hasattr(self.bot_manager, 'event_handlers') and self.bot_manager.event_handlers.memory_manager:
                        try:
                            await self.bot_manager.event_handlers.memory_manager.store_conversation(
                                user_id=user_id,
                                user_message=message_content, 
                                bot_response=response_content,
                                metadata={
                                    "platform": "web_api",
                                    "channel_id": "web_chat",
                                    "timestamp": datetime.now().isoformat()
                                }
                            )
                            logger.info("✅ Stored conversation directly in vector memory for user %s", user_id)
                        except Exception as e:
                            logger.warning("Direct memory storage failed: %s", e)
                    
                    logger.info(f"✅ Chat API: Generated response for {user_id}")
                    
                    return web.json_response({
                        "response": response_content,
                        "timestamp": datetime.now().isoformat(),
                        "message_id": universal_message.message_id,
                        "bot_name": get_normalized_bot_name_from_env(),
                        "success": True
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing message through universal orchestrator: {e}")
                    # Fall back to basic response
                    
            # Fallback: Basic response if universal orchestrator not available
            bot_name = get_normalized_bot_name_from_env()
            fallback_response = (
                f"Hello! I'm {bot_name}. I received your message: '{message_content[:100]}...'. "
                "I'm currently in development mode for web UI integration. "
                "Full AI capabilities will be available soon!"
            )
            
            return web.json_response({
                "response": fallback_response,
                "timestamp": datetime.now().isoformat(),
                "message_id": universal_message.message_id,
                "bot_name": get_normalized_bot_name_from_env(),
                "success": True,
                "mode": "fallback"
            })
            
        except json.JSONDecodeError:
            return web.json_response(
                {"error": "Invalid JSON in request body"}, 
                status=400
            )
        except Exception as e:
            logger.error(f"Error in chat API: {e}")
            return web.json_response(
                {"error": f"Internal server error: {str(e)}"}, 
                status=500
            )

    async def get_bot_info(self, request):
        """Get information about this bot instance"""
        try:
            bot_info = {
                "bot_name": get_normalized_bot_name_from_env(),
                "bot_id": str(self.bot.user.id) if self.bot.user else "unknown",
                "status": "online" if self.bot.is_ready() else "offline",
                "platform": "discord",
                "api_version": "1.0",
                "capabilities": [
                    "text_chat",
                    "conversation_memory",
                    "character_personality"
                ],
                "character_info": self._get_character_info(),
                "timestamp": datetime.now().isoformat()
            }
            
            return web.json_response(bot_info)
            
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return web.json_response(
                {"error": f"Failed to get bot info: {str(e)}"}, 
                status=500
            )

    def _get_character_info(self) -> Dict[str, Any]:
        """Get character information for this bot instance"""
        try:
            # Try to get character info from environment or bot configuration
            import os
            character_file = os.getenv("CDL_DEFAULT_CHARACTER")
            
            if character_file:
                # Extract character name from file path
                character_name = character_file.split('/')[-1].replace('.json', '').replace('-', ' ').title()
                return {
                    "character_file": character_file,
                    "character_name": character_name,
                    "has_personality": True
                }
            else:
                return {
                    "character_file": None,
                    "character_name": "Default Assistant", 
                    "has_personality": False
                }
                
        except Exception as e:
            logger.warning(f"Could not get character info: {e}")
            return {
                "character_file": None,
                "character_name": "Assistant",
                "has_personality": False
            }

    # Existing health check methods (unchanged)
    async def health_check(self, request):
        """Basic health check - is the service running?"""
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Health check from {request.remote}")

        return web.json_response(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "WhisperEngine Discord Bot",
            }
        )

    async def readiness_check(self, request):
        """Readiness check - is the service ready to handle requests?"""
        try:
            is_ready = (
                self.bot.is_ready() and self.bot.user is not None and not self.bot.is_closed()
            )

            if is_ready:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Readiness check from {request.remote} - bot ready")

                return web.json_response(
                    {
                        "status": "ready",
                        "timestamp": datetime.utcnow().isoformat(),
                        "bot_user": str(self.bot.user),
                        "guilds_count": len(self.bot.guilds),
                        "latency_ms": round(self.bot.latency * 1000, 2),
                        "chat_api_available": self.universal_orchestrator is not None,
                    }
                )
            else:
                logger.warning(
                    f"Readiness check failed - bot not ready: ready={self.bot.is_ready()}, closed={self.bot.is_closed()}"
                )
                return web.json_response(
                    {
                        "status": "not_ready",
                        "timestamp": datetime.utcnow().isoformat(),
                        "reason": "Bot not connected to Discord",
                    },
                    status=503,
                )

        except Exception as e:
            logger.error(f"Error in readiness check: {e}")
            return web.json_response(
                {"status": "error", "timestamp": datetime.utcnow().isoformat(), "error": str(e)},
                status=500,
            )

    async def metrics(self, request):
        """Basic metrics endpoint"""
        try:
            metrics_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "bot_status": "ready" if self.bot.is_ready() else "not_ready",
                "guild_count": len(self.bot.guilds) if self.bot.is_ready() else 0,
                "latency_ms": round(self.bot.latency * 1000, 2) if self.bot.is_ready() else -1,
                "memory_usage_mb": self._get_memory_usage(),
                "chat_api_status": "available" if self.universal_orchestrator else "lazy_init"
            }

            return web.json_response(metrics_data)

        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return web.json_response(
                {"error": f"Failed to generate metrics: {str(e)}"}, 
                status=500
            )

    async def detailed_status(self, request):
        """Detailed status information"""
        try:
            status_data = {
                "service": "WhisperEngine Discord Bot",
                "timestamp": datetime.utcnow().isoformat(),
                "bot": {
                    "ready": self.bot.is_ready(),
                    "closed": self.bot.is_closed(),
                    "user": str(self.bot.user) if self.bot.user else None,
                    "latency_ms": round(self.bot.latency * 1000, 2) if self.bot.is_ready() else -1,
                },
                "chat_api": {
                    "universal_orchestrator": self.universal_orchestrator is not None,
                    "identity_manager": self.identity_manager is not None,
                    "endpoints": ["/api/chat", "/api/bot-info"]
                },
                "character": self._get_character_info()
            }

            return web.json_response(status_data)

        except Exception as e:
            logger.error(f"Error generating detailed status: {e}")
            return web.json_response(
                {"error": f"Failed to generate status: {str(e)}"}, 
                status=500
            )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            return round(memory_mb, 2)
        except ImportError:
            return -1  # psutil not available
        except Exception:
            return -1  # Error getting memory info

    async def start(self):
        """Start the enhanced health and chat server"""
        try:
            # Initialize universal chat after bot is ready
            await self._initialize_universal_chat()
            
            # Configure runner to suppress access logs for health checks
            self.runner = web.AppRunner(self.app, access_log=None)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            logger.info(f"✅ Enhanced health & chat server started on {self.host}:{self.port}")
            logger.info("Available endpoints:")
            logger.info(f"  - http://{self.host}:{self.port}/health")
            logger.info(f"  - http://{self.host}:{self.port}/ready")
            logger.info(f"  - http://{self.host}:{self.port}/metrics")
            logger.info(f"  - http://{self.host}:{self.port}/status")
            logger.info(f"  - http://{self.host}:{self.port}/api/chat (POST)")
            logger.info(f"  - http://{self.host}:{self.port}/api/bot-info (GET)")

        except Exception as e:
            logger.error(f"Failed to start enhanced server: {e}")
            raise

    async def stop(self):
        """Stop the enhanced server"""
        try:
            if self.site:
                await self.site.stop()
                logger.info("Enhanced server stopped")

            if self.runner:
                await self.runner.cleanup()
                logger.info("Enhanced server cleaned up")

        except Exception as e:
            logger.error(f"Error stopping enhanced server: {e}")


# Factory function for easy integration
def create_enhanced_health_server(
    bot: commands.Bot, port: int = 9090, host: str = "0.0.0.0", bot_manager=None
) -> EnhancedHealthServer:
    """Create and return an enhanced health server instance with chat API"""
    return EnhancedHealthServer(bot, port, host, bot_manager)