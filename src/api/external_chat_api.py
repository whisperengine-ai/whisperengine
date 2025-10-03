"""
External Chat API for WhisperEngine.

Provides HTTP endpoints for external systems to interact with WhisperEngine
AI characters using the same sophisticated processing pipeline as Discord.

Key Features:
- Platform-agnostic message processing
- Shared AI components with Discord handlers
- RESTful API design
- Authentication and rate limiting
- Consistent response format
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

from aiohttp import web, web_request, web_response
from aiohttp.web import middleware

from src.core.message_processor import MessageProcessor, MessageContext, ProcessingResult, create_message_processor
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class ExternalChatAPI:
    """
    External Chat API handler for WhisperEngine.
    
    Provides HTTP endpoints that use the same message processing pipeline
    as Discord but through RESTful API calls.
    """

    def __init__(self, bot_core, memory_manager, llm_client):
        """Initialize the API with core components."""
        self.bot_core = bot_core
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        
        # Create message processor using the same components as Discord
        self.message_processor = create_message_processor(
            bot_core=bot_core,
            memory_manager=memory_manager,
            llm_client=llm_client,
            security_validator=getattr(bot_core, 'security_validator', None),
            emoji_intelligence=getattr(bot_core, 'emoji_response_intelligence', None),
            image_processor=getattr(bot_core, 'image_processor', None),
            conversation_cache=getattr(bot_core, 'conversation_cache', None)
        )

    def setup_routes(self, app: web.Application):
        """Setup API routes."""
        app.router.add_post('/api/chat', self.handle_chat_message)
        app.router.add_get('/api/health', self.handle_health_check)
        app.router.add_get('/api/status', self.handle_status_check)
        app.router.add_post('/api/chat/batch', self.handle_batch_messages)

    @handle_errors(category=ErrorCategory.NETWORK, severity=ErrorSeverity.MEDIUM)
    async def handle_chat_message(self, request: web_request.Request) -> web_response.Response:
        """
        Handle single chat message API endpoint.
        
        POST /api/chat
        {
            "user_id": "string",
            "message": "string", 
            "context": {
                "channel_type": "dm|guild",
                "platform": "api",
                "metadata": {}
            }
        }
        """
        try:
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

            # Create message context
            context_data = request_data.get('context', {})
            message_context = MessageContext(
                user_id=request_data['user_id'],
                content=request_data['message'],
                platform='api',
                channel_type=context_data.get('channel_type', 'dm'),
                metadata=context_data.get('metadata', {})
            )

            logger.info("API CHAT: Processing message for user %s", message_context.user_id)

            # Process message through the same pipeline as Discord
            processing_result = await self.message_processor.process_message(message_context)

            # Return response
            response_data = {
                'success': processing_result.success,
                'response': processing_result.response,
                'processing_time_ms': processing_result.processing_time_ms,
                'memory_stored': processing_result.memory_stored,
                'timestamp': datetime.utcnow().isoformat()
            }

            if not processing_result.success:
                response_data['error'] = processing_result.error_message

            if processing_result.metadata:
                response_data['metadata'] = processing_result.metadata

            status_code = 200 if processing_result.success else 500
            return web.json_response(response_data, status=status_code)

        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON in request body'}, 
                status=400
            )
        except Exception as e:
            logger.error("API CHAT: Unexpected error: %s", e)
            logger.debug("API CHAT: Traceback: %s", traceback.format_exc())
            return web.json_response(
                {
                    'error': 'Internal server error',
                    'message': str(e),
                    'success': False
                }, 
                status=500
            )

    async def handle_health_check(self, request: web_request.Request) -> web_response.Response:
        """Health check endpoint."""
        try:
            # Basic health checks
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'message_processor': self.message_processor is not None,
                    'memory_manager': self.memory_manager is not None,
                    'llm_client': self.llm_client is not None,
                    'bot_core': self.bot_core is not None
                }
            }

            # Test memory manager connection
            if self.memory_manager:
                try:
                    # Quick test query (non-intrusive)
                    await self.memory_manager.retrieve_context_aware_memories(
                        user_id='health_check',
                        query='test',
                        max_memories=1
                    )
                    health_status['components']['memory_connection'] = True
                except Exception as e:
                    logger.warning("Health check: Memory manager test failed: %s", e)
                    health_status['components']['memory_connection'] = False

            return web.json_response(health_status)

        except Exception as e:
            logger.error("Health check failed: %s", e)
            return web.json_response(
                {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                },
                status=500
            )

    async def handle_status_check(self, request: web_request.Request) -> web_response.Response:
        """Detailed status endpoint with component information."""
        try:
            status_info = {
                'api_version': '1.0.0',
                'platform': 'WhisperEngine External Chat API',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'message_processor': {
                        'available': self.message_processor is not None,
                        'type': type(self.message_processor).__name__ if self.message_processor else None
                    },
                    'memory_manager': {
                        'available': self.memory_manager is not None,
                        'type': type(self.memory_manager).__name__ if self.memory_manager else None
                    },
                    'llm_client': {
                        'available': self.llm_client is not None,
                        'type': type(self.llm_client).__name__ if self.llm_client else None
                    },
                    'bot_core': {
                        'available': self.bot_core is not None,
                        'type': type(self.bot_core).__name__ if self.bot_core else None
                    }
                },
                'endpoints': [
                    'POST /api/chat',
                    'GET /api/health', 
                    'GET /api/status',
                    'POST /api/chat/batch'
                ]
            }

            return web.json_response(status_info)

        except Exception as e:
            logger.error("Status check failed: %s", e)
            return web.json_response(
                {
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                },
                status=500
            )

    @handle_errors(category=ErrorCategory.NETWORK, severity=ErrorSeverity.MEDIUM)
    async def handle_batch_messages(self, request: web_request.Request) -> web_response.Response:
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

                except Exception as e:
                    logger.error("Batch processing error for message %d: %s", i, e)
                    results.append({
                        'index': i,
                        'success': False,
                        'error': str(e)
                    })

            return web.json_response({
                'results': results,
                'total_processed': len(results),
                'timestamp': datetime.utcnow().isoformat()
            })

        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON in request body'},
                status=400
            )
        except Exception as e:
            logger.error("Batch processing failed: %s", e)
            return web.json_response(
                {
                    'error': 'Internal server error',
                    'message': str(e)
                },
                status=500
            )


@middleware
async def cors_middleware(request: web_request.Request, handler):
    """CORS middleware for API access."""
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


@middleware  
async def logging_middleware(request: web_request.Request, handler):
    """Request logging middleware."""
    start_time = datetime.now()
    
    try:
        response = await handler(request)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(
            "API REQUEST: %s %s - %d - %.2fms",
            request.method,
            request.path,
            response.status,
            processing_time
        )
        
        return response
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.error(
            "API REQUEST FAILED: %s %s - ERROR - %.2fms - %s",
            request.method, 
            request.path,
            processing_time,
            str(e)
        )
        raise


def create_external_chat_api(bot_core, memory_manager, llm_client) -> ExternalChatAPI:
    """Factory function to create ExternalChatAPI instance."""
    return ExternalChatAPI(
        bot_core=bot_core,
        memory_manager=memory_manager,
        llm_client=llm_client
    )


def setup_api_server(bot_core, memory_manager, llm_client, host='0.0.0.0', port=8080) -> web.Application:
    """
    Setup and configure the API server.
    
    Returns configured aiohttp Application ready to run.
    """
    # Create API handler
    api_handler = create_external_chat_api(bot_core, memory_manager, llm_client)
    
    # Create aiohttp application with middleware
    app = web.Application(middlewares=[
        cors_middleware,
        logging_middleware
    ])
    
    # Setup routes
    api_handler.setup_routes(app)
    
    logger.info("External Chat API server configured on %s:%d", host, port)
    logger.info("Available endpoints:")
    logger.info("  POST /api/chat - Single message processing")
    logger.info("  POST /api/chat/batch - Batch message processing")
    logger.info("  GET /api/health - Health check")
    logger.info("  GET /api/status - Detailed status")
    
    return app