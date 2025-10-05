"""
Enhanced Health Server with External Chat API
Basic health monitoring for Discord bots plus HTTP chat API endpoints.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any

from aiohttp import web
from discord.ext import commands

from src.core.message_processor import create_message_processor, MessageContext
from src.intelligence.context_switch_detector import ContextSwitch

logger = logging.getLogger(__name__)

# Configure aiohttp access logs to use DEBUG level to reduce log spam
access_logger = logging.getLogger("aiohttp.access")
access_logger.setLevel(logging.WARNING)


class EnhancedHealthServer:
    """HTTP server with health checks and external chat API for Discord bots"""

    def __init__(self, bot: commands.Bot, port: int = 9090, host: str = "0.0.0.0", bot_manager=None):
        self.bot = bot
        self.bot_manager = bot_manager
        self.port = port
        self.host = host
        # Disable aiohttp access logging to prevent health check spam
        self.app = web.Application(logger=logger)
        self.runner = None
        self.site = None
        
        # Initialize message processor for external API
        self.message_processor = None
        
        self.setup_routes()

    def _initialize_message_processor(self):
        """Initialize message processor using bot components."""
        if not self.bot_manager:
            logger.debug("🌐 EXTERNAL API: Bot manager not available for message processor")
            return False
            
        if not hasattr(self.bot_manager, 'bot_core') or not self.bot_manager.bot_core:
            logger.debug("🌐 EXTERNAL API: Bot core not available for message processor")
            return False
            
        bot_core = self.bot_manager.bot_core
        
        # Get required components from bot core
        memory_manager = getattr(bot_core, 'memory_manager', None)
        llm_client = getattr(bot_core, 'llm_client', None)
        
        if not memory_manager:
            logger.debug("🌐 EXTERNAL API: Memory manager not available for message processor")
            return False
            
        if not llm_client:
            logger.debug("🌐 EXTERNAL API: LLM client not available for message processor")
            return False
        
        try:
            self.message_processor = create_message_processor(
                bot_core=bot_core,
                memory_manager=memory_manager,
                llm_client=llm_client,
                security_validator=getattr(bot_core, 'security_validator', None),
                emoji_intelligence=getattr(bot_core, 'emoji_response_intelligence', None),
                image_processor=getattr(bot_core, 'image_processor', None),
                conversation_cache=getattr(bot_core, 'conversation_cache', None)
            )
            logger.info("🌐 EXTERNAL API: Message processor initialized with same components as Discord bot")
            return True
        except Exception as e:
            logger.warning("🌐 EXTERNAL API: Failed to initialize message processor: %s", str(e))
            return False

    def setup_routes(self):
        """Configure HTTP routes"""
        # Health check routes
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_get("/ready", self.readiness_check)
        self.app.router.add_get("/metrics", self.metrics)
        self.app.router.add_get("/status", self.detailed_status)
        self.app.router.add_get("/api/bot-info", self.get_bot_info)
        
        # NEW: External Chat API routes
        self.app.router.add_post("/api/chat", self.handle_chat_message)
        self.app.router.add_post("/api/chat/batch", self.handle_batch_messages)
        self.app.router.add_options("/api/chat", self.handle_cors_preflight)
        self.app.router.add_options("/api/chat/batch", self.handle_cors_preflight)
        
        # CORS middleware setup
        self.app.middlewares.append(self.cors_middleware)

    def _make_json_serializable(self, obj):
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, ContextSwitch):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        else:
            return obj

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
        # Avoid unused parameter warning
        _ = request
        return web.Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
        )

    async def get_bot_info(self, request):
        """Get information about this bot instance"""
        # Avoid unused parameter warning
        _ = request
        try:
            bot_info = {
                "bot_name": self.bot.user.name if self.bot.user else "Unknown",
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
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error getting bot info: %s", str(e))
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
                
        except (OSError, ImportError) as e:
            logger.warning("Could not get character info: %s", str(e))
            return {
                "character_file": None,
                "character_name": "Assistant",
                "has_personality": False
            }

    async def handle_chat_message(self, request):
        """
        Handle single chat message API endpoint.
        
        POST /api/chat
        {
            "user_id": "string",
            "message": "string", 
            "metadata_level": "basic|standard|extended",  // Optional, defaults to "standard"
            "context": {
                "channel_type": "dm|guild",
                "platform": "api",
                "metadata": {}
            }
        }
        
        Metadata Levels:
        - basic: Minimal essential data (memory_count, knowledge_stored, success flags)
        - standard: Basic + AI components + security validation (DEFAULT)
        - extended: Standard + all analytics (temporal, vector memory, relationships, etc.)
        """
        try:
            # Initialize message processor if not done yet
            if not self.message_processor:
                if not self._initialize_message_processor():
                    return web.json_response(
                        {
                            'error': 'Chat API not available - bot components not ready',
                            'success': False,
                            'details': 'Bot is still initializing. Please try again in a few moments.'
                        },
                        status=503
                    )

            # Parse request body
            request_data = await request.json()
            
            # Validate required fields
            if not request_data.get('user_id'):
                return web.json_response(
                    {'error': 'user_id is required'}, 
                    status=400
                )
            
            if not request_data.get('message'):
                return web.json_response(
                    {'error': 'message is required'}, 
                    status=400
                )

            # Get metadata level (basic, standard, extended)
            metadata_level = request_data.get('metadata_level', 'standard').lower()
            if metadata_level not in ['basic', 'standard', 'extended']:
                return web.json_response(
                    {'error': 'metadata_level must be "basic", "standard", or "extended"'}, 
                    status=400
                )

            # Create message context
            context_data = request_data.get('context', {})
            message_context = MessageContext(
                user_id=request_data['user_id'],
                content=request_data['message'],
                platform='api',
                channel_type=context_data.get('channel_type', 'dm'),
                metadata=context_data.get('metadata', {}),
                metadata_level=metadata_level  # Pass metadata level control
            )

            logger.info("🌐 EXTERNAL API: Processing message for user %s (metadata_level=%s)", 
                       message_context.user_id, metadata_level)

            # Process message through the same pipeline as Discord
            processing_result = await self.message_processor.process_message(message_context)

            # Return response
            response_data = {
                'success': processing_result.success,
                'response': processing_result.response,
                'processing_time_ms': processing_result.processing_time_ms,
                'memory_stored': processing_result.memory_stored,
                'timestamp': datetime.utcnow().isoformat(),
                'bot_name': self.bot.user.name if self.bot.user else "WhisperEngine Bot"
            }

            if not processing_result.success:
                response_data['error'] = processing_result.error_message

            if processing_result.metadata:
                response_data['metadata'] = self._make_json_serializable(processing_result.metadata)

            status_code = 200 if processing_result.success else 500
            return web.json_response(response_data, status=status_code)

        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON in request body'}, 
                status=400
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error("🌐 EXTERNAL API: Unexpected error: %s", str(e))
            logger.debug("🌐 EXTERNAL API: Traceback: %s", traceback.format_exc())
            return web.json_response(
                {
                    'error': 'Internal server error',
                    'message': str(e),
                    'success': False
                }, 
                status=500
            )

    async def handle_batch_messages(self, request):
        """
        Handle batch message processing.
        
        POST /api/chat/batch
        {
            "messages": [
                {
                    "user_id": "string",
                    "message": "string",
                    "context": {}
                }
            ]
        }
        """
        try:
            # Initialize message processor if not done yet
            if not self.message_processor:
                if not self._initialize_message_processor():
                    return web.json_response(
                        {
                            'error': 'Chat API not available - bot components not ready',
                            'success': False,
                            'details': 'Bot is still initializing. Please try again in a few moments.'
                        },
                        status=503
                    )

            request_data = await request.json()
            messages = request_data.get('messages', [])
            
            if not messages:
                return web.json_response(
                    {'error': 'messages array is required'},
                    status=400
                )
            
            if len(messages) > 10:  # Limit batch size
                return web.json_response(
                    {'error': 'Maximum 10 messages per batch'},
                    status=400
                )

            results = []
            for i, msg_data in enumerate(messages):
                try:
                    # Validate message
                    if not msg_data.get('user_id') or not msg_data.get('message'):
                        results.append({
                            'index': i,
                            'success': False,
                            'error': 'user_id and message are required'
                        })
                        continue

                    # Create message context
                    context_data = msg_data.get('context', {})
                    message_context = MessageContext(
                        user_id=msg_data['user_id'],
                        content=msg_data['message'],
                        platform='api',
                        channel_type=context_data.get('channel_type', 'dm'),
                        metadata=context_data.get('metadata', {})
                    )

                    # Process message
                    processing_result = await self.message_processor.process_message(message_context)
                    
                    result = {
                        'index': i,
                        'user_id': msg_data['user_id'],
                        'success': processing_result.success,
                        'response': processing_result.response,
                        'processing_time_ms': processing_result.processing_time_ms,
                        'memory_stored': processing_result.memory_stored
                    }
                    
                    if not processing_result.success:
                        result['error'] = processing_result.error_message
                    
                    results.append(result)

                except (AttributeError, ValueError, TypeError) as e:
                    logger.error("🌐 EXTERNAL API: Batch processing error for message %d: %s", i, str(e))
                    results.append({
                        'index': i,
                        'success': False,
                        'error': str(e)
                    })

            return web.json_response({
                'results': results,
                'total_processed': len(results),
                'timestamp': datetime.utcnow().isoformat(),
                'bot_name': self.bot.user.name if self.bot.user else "WhisperEngine Bot"
            })

        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON in request body'},
                status=400
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error("🌐 EXTERNAL API: Batch processing failed: %s", str(e))
            return web.json_response(
                {
                    'error': 'Internal server error',
                    'message': str(e)
                },
                status=500
            )

    # Existing health check methods (unchanged)
    async def health_check(self, request):
        """Basic health check - is the service running?"""
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Health check from %s", request.remote)

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
                    logger.debug("Readiness check from %s - bot ready", request.remote)

                return web.json_response(
                    {
                        "status": "ready",
                        "timestamp": datetime.utcnow().isoformat(),
                        "bot_user": str(self.bot.user),
                        "guilds_count": len(self.bot.guilds),
                        "latency_ms": round(self.bot.latency * 1000, 2),
                    }
                )
            else:
                logger.warning(
                    "Readiness check failed - bot not ready: ready=%s, closed=%s",
                    self.bot.is_ready(), self.bot.is_closed()
                )
                return web.json_response(
                    {
                        "status": "not_ready",
                        "timestamp": datetime.utcnow().isoformat(),
                        "reason": "Bot not connected to Discord",
                    },
                    status=503,
                )

        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error in readiness check: %s", str(e))
            return web.json_response(
                {"status": "error", "timestamp": datetime.utcnow().isoformat(), "error": str(e)},
                status=500,
            )

    async def metrics(self, request):
        """Basic metrics endpoint"""
        # Avoid unused parameter warning
        _ = request
        try:
            metrics_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "bot_status": "ready" if self.bot.is_ready() else "not_ready",
                "guild_count": len(self.bot.guilds) if self.bot.is_ready() else 0,
                "latency_ms": round(self.bot.latency * 1000, 2) if self.bot.is_ready() else -1,
                "memory_usage_mb": self._get_memory_usage(),
            }

            return web.json_response(metrics_data)

        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error generating metrics: %s", str(e))
            return web.json_response(
                {"error": f"Failed to generate metrics: {str(e)}"}, 
                status=500
            )

    async def detailed_status(self, request):
        """Detailed status information"""
        # Avoid unused parameter warning
        _ = request
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
                "api": {
                    "endpoints": [
                        "/api/bot-info",
                        "/api/chat (POST)",
                        "/api/chat/batch (POST)"
                    ]
                },
                "character": self._get_character_info()
            }

            return web.json_response(status_data)

        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error generating detailed status: %s", str(e))
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
        except OSError:
            return -1  # Error getting memory info

    async def start(self):
        """Start the enhanced health server with external chat API"""
        try:
            # Configure runner to suppress access logs for health checks
            self.runner = web.AppRunner(self.app, access_log=None)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            logger.info("✅ Enhanced health server with External Chat API started on %s:%d", 
                       self.host, self.port)
            logger.info("Health endpoints:")
            logger.info("  - http://%s:%d/health", self.host, self.port)
            logger.info("  - http://%s:%d/ready", self.host, self.port)
            logger.info("  - http://%s:%d/metrics", self.host, self.port)
            logger.info("  - http://%s:%d/status", self.host, self.port)
            logger.info("  - http://%s:%d/api/bot-info (GET)", self.host, self.port)
            logger.info("🌐 External Chat API endpoints:")
            logger.info("  - http://%s:%d/api/chat (POST)", self.host, self.port)
            logger.info("  - http://%s:%d/api/chat/batch (POST)", self.host, self.port)
            
            # Initialize message processor for API endpoints
            self._initialize_message_processor()

        except (OSError, ValueError) as e:
            logger.error("Failed to start enhanced server: %s", str(e))
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

        except (OSError, AttributeError) as e:
            logger.error("Error stopping enhanced server: %s", str(e))


# Factory function for easy integration
def create_enhanced_health_server(
    bot: commands.Bot, port: int = 9090, host: str = "0.0.0.0", bot_manager=None
) -> EnhancedHealthServer:
    """Create and return an enhanced health server instance with chat API"""
    return EnhancedHealthServer(bot, port, host, bot_manager)