"""
External Chat API for WhisperEngine.

Provides HTTP endpoints for external systems to interact with WhisperEngine
AI characters using the same sophisticated processing pipeline as Discord.

Key Features:
- Platform-agnostic message processing
- Shared AI components with Discord handlers
- RESTful API design
- Environment-controlled CORS and security
- Consistent response format
"""

import asyncio
import logging
import os
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

    def _make_json_serializable(self, obj):
        """Convert objects to JSON-serializable format"""
        from enum import Enum
        from datetime import datetime, date
        from decimal import Decimal
        
        if isinstance(obj, Enum):
            # Handle all Enum types (including EngagementStrategy)
            return obj.value
        elif isinstance(obj, (datetime, date)):
            # Handle datetime objects
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            # Handle Decimal objects
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            # Handle objects with to_dict method
            return obj.to_dict()
        else:
            return obj

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
                metadata=context_data.get('metadata', {}),
                metadata_level='standard'  # Include AI components and character learning moments
            )

            logger.info("API CHAT: Processing message for user %s", message_context.user_id)

            # Process message through the same pipeline as Discord
            processing_result = await self.message_processor.process_message(message_context)

            # Extract user facts and relationship metrics
            user_facts = await self._extract_user_facts(request_data['user_id'])
            relationship_metrics = await self._extract_relationship_metrics(request_data['user_id'])

            # Return response
            response_data = {
                'success': processing_result.success,
                'response': processing_result.response,
                'processing_time_ms': processing_result.processing_time_ms,
                'memory_stored': processing_result.memory_stored,
                'timestamp': datetime.utcnow().isoformat(),
                'user_facts': user_facts,
                'relationship_metrics': relationship_metrics
            }

            if not processing_result.success:
                response_data['error'] = processing_result.error_message

            if processing_result.metadata:
                response_data['metadata'] = self._make_json_serializable(processing_result.metadata)
                
                # Extract reasoning transparency for top-level API response
                ai_components = processing_result.metadata.get('ai_components', {})
                character_reasoning = ai_components.get('character_reasoning')
                if character_reasoning:
                    response_data['reasoning'] = character_reasoning

            return web.json_response(response_data)

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

    async def _extract_user_facts(self, user_id: str) -> Dict[str, Any]:
        """Extract user facts from memory system."""
        try:
            # Get user profile from memory system - could be used for future enhancements
            if hasattr(self.memory_manager, 'get_user_profile'):
                _ = await self.memory_manager.get_user_profile(user_id)  # Reserved for future use
            
            # Get conversation history to extract facts
            if hasattr(self.memory_manager, 'get_conversation_history'):
                conversation_history = await self.memory_manager.get_conversation_history(user_id, limit=20)
            else:
                conversation_history = []

            # Extract basic user facts from memory
            user_facts = {}
            
            # Try to get name from profile or conversation history
            name = None
            for memory in conversation_history:
                content = memory.get('content', '')
                memory_metadata = memory.get('metadata', {})
                
                # Look for name in metadata or content patterns
                if memory_metadata.get('user_name'):
                    name = memory_metadata.get('user_name')
                    break
                elif 'my name is' in content.lower() or 'i am' in content.lower():
                    # Simple name extraction - could be enhanced with NLP
                    words = content.lower().split()
                    if 'my name is' in content.lower():
                        try:
                            name_idx = words.index('name') + 2  # Skip "is"
                            if name_idx < len(words):
                                name = words[name_idx].strip('.,!?').title()
                        except (ValueError, IndexError):
                            pass
            
            if name:
                user_facts['name'] = name

            # Add other extractable facts
            interaction_count = len(conversation_history)
            if interaction_count > 0:
                user_facts['interaction_count'] = interaction_count
                user_facts['first_interaction'] = conversation_history[-1].get('timestamp') if conversation_history else None
                user_facts['last_interaction'] = conversation_history[0].get('timestamp') if conversation_history else None

            return user_facts

        except Exception as e:
            logger.warning("Failed to extract user facts for %s: %s", user_id, e)
            return {}

    async def _extract_relationship_metrics(self, user_id: str) -> Dict[str, Any]:
        """Extract relationship metrics from emotion manager and memory system."""
        try:
            # Initialize default metrics
            relationship_metrics = {
                'affection': 50,
                'trust': 42,
                'attunement': 78
            }

            # Get emotion manager if available
            emotion_manager = getattr(self.bot_core, 'emotion_manager', None)
            if emotion_manager and hasattr(emotion_manager, 'user_profiles'):
                user_profiles = emotion_manager.user_profiles
                if user_id in user_profiles:
                    profile = user_profiles[user_id]
                    
                    # Convert relationship level to affection score
                    relationship_mapping = {
                        'stranger': 30,
                        'acquaintance': 50, 
                        'friend': 70,
                        'close_friend': 90
                    }
                    
                    if hasattr(profile, 'relationship_level'):
                        level_name = profile.relationship_level.value if hasattr(profile.relationship_level, 'value') else str(profile.relationship_level)
                        relationship_metrics['affection'] = relationship_mapping.get(level_name, 50)
                    
                    # Calculate trust based on interaction count and positive interactions
                    if hasattr(profile, 'interaction_count'):
                        # Base trust grows with interactions (capped at 80)
                        base_trust = min(80, 20 + (profile.interaction_count * 2))
                        
                        # Reduce trust for escalation count
                        if hasattr(profile, 'escalation_count'):
                            trust_penalty = profile.escalation_count * 10
                            base_trust = max(10, base_trust - trust_penalty)
                        
                        relationship_metrics['trust'] = base_trust
                    
                    # Calculate attunement based on emotional understanding
                    if hasattr(profile, 'emotion_history') and profile.emotion_history:
                        # Higher attunement for users with emotional history (shows understanding)
                        emotion_diversity = len(set(e.detected_emotion.value if hasattr(e.detected_emotion, 'value') else str(e.detected_emotion) 
                                                   for e in profile.emotion_history[-10:]))  # Last 10 emotions
                        attunement_base = min(90, 60 + (emotion_diversity * 5))
                        relationship_metrics['attunement'] = attunement_base

            # Get memory-based relationship indicators
            if hasattr(self.memory_manager, 'retrieve_relevant_memories'):
                try:
                    # Look for positive/negative sentiment in recent memories
                    recent_memories = await self.memory_manager.retrieve_relevant_memories(
                        user_id=user_id,
                        query="positive negative sentiment emotion feeling",
                        limit=10
                    )
                    
                    positive_count = 0
                    negative_count = 0
                    
                    for memory in recent_memories:
                        content = memory.get('content', '').lower()
                        # metadata could be used for additional sentiment context in future
                        
                        # Simple sentiment indicators
                        positive_words = ['thank', 'love', 'great', 'amazing', 'wonderful', 'perfect', 'happy', 'excited']
                        negative_words = ['hate', 'terrible', 'awful', 'frustrated', 'angry', 'disappointed', 'worried']
                        
                        if any(word in content for word in positive_words):
                            positive_count += 1
                        if any(word in content for word in negative_words):
                            negative_count += 1
                    
                    # Adjust trust based on sentiment
                    if positive_count > negative_count:
                        relationship_metrics['trust'] = min(95, relationship_metrics['trust'] + (positive_count - negative_count) * 5)
                    elif negative_count > positive_count:
                        relationship_metrics['trust'] = max(10, relationship_metrics['trust'] - (negative_count - positive_count) * 3)
                
                except Exception as e:
                    logger.debug("Could not analyze sentiment for relationship metrics: %s", e)

            return relationship_metrics

        except Exception as e:
            logger.warning("Failed to extract relationship metrics for %s: %s", user_id, e)
            return {'affection': 50, 'trust': 42, 'attunement': 78}  # Fallback values

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
                        metadata=context_data.get('metadata', {}),
                        metadata_level='standard'  # Include AI components and character learning moments
                    )

                    # Process message
                    processing_result = await self.message_processor.process_message(message_context)
                    
                    # Extract user facts and relationship metrics for batch processing
                    user_facts = await self._extract_user_facts(msg_data['user_id'])
                    relationship_metrics = await self._extract_relationship_metrics(msg_data['user_id'])
                    
                    result = {
                        'index': i,
                        'user_id': msg_data['user_id'],
                        'success': processing_result.success,
                        'response': processing_result.response,
                        'processing_time_ms': processing_result.processing_time_ms,
                        'memory_stored': processing_result.memory_stored,
                        'user_facts': user_facts,
                        'relationship_metrics': relationship_metrics
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
    """
    CORS middleware with environment-controlled allowed origins.
    
    Security: Only allows requests from explicitly configured origins.
    Set ALLOWED_ORIGINS environment variable (comma-separated list).
    Example: ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com
    """
    # Handle preflight OPTIONS requests
    if request.method == 'OPTIONS':
        response = web.Response()
    else:
        response = await handler(request)
    
    # Get allowed origins from environment (default to localhost for development)
    allowed_origins_str = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8080')
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]
    
    # Get request origin
    request_origin = request.headers.get('Origin')
    
    # Check if origin is allowed
    if request_origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = request_origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours cache for preflight
    elif request_origin:
        # Origin provided but not allowed - log for security monitoring
        logger.warning(
            "CORS: Rejected request from unauthorized origin: %s (allowed: %s)",
            request_origin,
            allowed_origins
        )
    
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