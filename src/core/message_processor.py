"""
Shared message processing service for WhisperEngine.

This module provides platform-agnostic message processing that can be used by:
- Discord bot handlers
- External HTTP API endpoints 
- Future platform integrations

Core design principle: Abstract platform-specific details while preserving 
the sophisticated AI processing pipeline including memory, emotions, CDL character 
integration, and context management.
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass

from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


@dataclass
class MessageContext:
    """Platform-agnostic message context."""
    user_id: str
    content: str
    original_content: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    platform: str = "unknown"  # "discord", "api", etc.
    channel_id: Optional[str] = None
    channel_type: Optional[str] = None  # "dm", "guild", etc.
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessingResult:
    """Result of message processing."""
    response: str
    success: bool = True
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    memory_stored: bool = False
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MessageProcessor:
    """
    Core message processing engine for WhisperEngine.
    
    Abstracts the sophisticated AI processing pipeline from platform-specific
    implementations. Handles security, memory, emotions, CDL character integration,
    and response generation in a platform-agnostic way.
    """

    def __init__(self, bot_core, memory_manager, llm_client, security_validator=None, 
                 emoji_intelligence=None, image_processor=None, conversation_cache=None):
        """Initialize the message processor with core components."""
        self.bot_core = bot_core
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.security_validator = security_validator
        self.emoji_intelligence = emoji_intelligence
        self.image_processor = image_processor
        self.conversation_cache = conversation_cache
        
        # Track processing state for debugging
        self._last_security_validation = None
        self._last_emotional_context = None

    @handle_errors(category=ErrorCategory.VALIDATION, severity=ErrorSeverity.HIGH)
    async def process_message(self, message_context: MessageContext) -> ProcessingResult:
        """
        Process a message through the complete AI pipeline.
        
        This is the main entry point that replicates the sophisticated processing
        from the Discord handlers but in a platform-agnostic way.
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔄 MESSAGE PROCESSOR: Starting processing for user {message_context.user_id} "
                       f"on platform {message_context.platform}")
            
            # Phase 1: Security validation
            validation_result = await self._validate_security(message_context)
            if not validation_result["is_safe"]:
                logger.warning(f"SECURITY: Rejected unsafe message from user {message_context.user_id}")
                return ProcessingResult(
                    response="I'm sorry, but I can't process that message for security reasons.",
                    success=False,
                    error_message="Security validation failed"
                )
            
            # Update message content with sanitized version
            message_context.content = validation_result["sanitized_content"]
            if validation_result["warnings"]:
                logger.warning(f"SECURITY: Input warnings for user {message_context.user_id}: {validation_result['warnings']}")
            
            # Phase 2: Name detection and storage
            await self._process_name_detection(message_context)
            
            # Phase 3: Memory retrieval with context-aware filtering
            relevant_memories = await self._retrieve_relevant_memories(message_context)
            
            # Phase 4: Conversation history and context building
            conversation_context = await self._build_conversation_context(
                message_context, relevant_memories
            )
            
            # Phase 5: AI component processing (parallel)
            ai_components = await self._process_ai_components_parallel(
                message_context, conversation_context
            )
            
            # Phase 6: Image processing if attachments present
            if message_context.attachments:
                conversation_context = await self._process_attachments(
                    message_context, conversation_context
                )
            
            # Phase 7: Response generation
            response = await self._generate_response(
                message_context, conversation_context, ai_components
            )
            
            # Phase 8: Response validation and sanitization
            response = await self._validate_and_sanitize_response(
                response, message_context
            )
            
            # Phase 9: Memory storage
            memory_stored = await self._store_conversation_memory(
                message_context, response, ai_components
            )
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.info(f"✅ MESSAGE PROCESSOR: Successfully processed message for user {message_context.user_id} "
                       f"in {processing_time_ms}ms")
            
            return ProcessingResult(
                response=response,
                success=True,
                processing_time_ms=processing_time_ms,
                memory_stored=memory_stored,
                metadata={
                    "memory_count": len(relevant_memories) if relevant_memories else 0,
                    "ai_components": ai_components,
                    "security_validation": validation_result
                }
            )
            
        except Exception as e:
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error(f"❌ MESSAGE PROCESSOR: Failed to process message for user {message_context.user_id}: {e}")
            logger.error(f"❌ MESSAGE PROCESSOR: Traceback: {traceback.format_exc()}")
            
            return ProcessingResult(
                response="I apologize, but I'm experiencing technical difficulties. Please try again.",
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time_ms
            )

    async def _validate_security(self, message_context: MessageContext) -> Dict[str, Any]:
        """Validate message security and sanitize content."""
        if not self.security_validator:
            return {
                "is_safe": True,
                "sanitized_content": message_context.content,
                "warnings": []
            }
        
        try:
            # Create a mock message object for the security validator
            mock_message = type('MockMessage', (), {
                'content': message_context.content,
                'author': type('MockAuthor', (), {
                    'id': message_context.user_id,
                    'name': f"user_{message_context.user_id}"
                })()
            })()
            
            validation_result = await self.security_validator.validate_input(mock_message)
            self._last_security_validation = validation_result
            return validation_result
            
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            return {
                "is_safe": True,  # Fail open for now
                "sanitized_content": message_context.content,
                "warnings": [f"Security validation error: {e}"]
            }

    async def _process_name_detection(self, message_context: MessageContext):
        """Process message for automatic name detection and storage."""
        try:
            from src.utils.automatic_name_storage import create_automatic_name_storage
            from src.llm.llm_protocol import create_llm_client
            
            if self.memory_manager:
                llm_client = create_llm_client()
                name_storage = create_automatic_name_storage(self.memory_manager, llm_client)
                detected_name = await name_storage.process_message_for_names(
                    message_context.user_id, message_context.content
                )
                if detected_name:
                    logger.info(f"🏷️ Auto-detected name '{detected_name}' for user {message_context.user_id}")
        except Exception as e:
            logger.debug(f"Name detection failed: {e}")

    async def _retrieve_relevant_memories(self, message_context: MessageContext) -> List[Dict[str, Any]]:
        """Retrieve relevant memories with context-aware filtering."""
        if not self.memory_manager:
            logger.warning("Memory manager not available; skipping memory retrieval.")
            return []

        try:
            # Create message context for memory classification
            mock_message = type('MockMessage', (), {
                'content': message_context.content,
                'channel': type('MockChannel', (), {
                    'type': getattr(message_context, 'channel_type', 'dm')
                })(),
                'guild': None if message_context.channel_type == 'dm' else type('MockGuild', (), {})()
            })()
            
            classified_context = self.memory_manager.classify_discord_context(mock_message)
            logger.debug(f"Message context classified: {classified_context.context_type.value}")

            # Try optimized memory retrieval first if available
            if hasattr(self.memory_manager, 'retrieve_relevant_memories_optimized'):
                try:
                    query_type = self._classify_query_type(message_context.content)
                    user_preferences = self._build_user_preferences(message_context.user_id, classified_context)
                    filters = self._build_memory_filters(classified_context)
                    
                    # Add recency boost and meta-conversation filtering
                    filters["prefer_recent_conversation"] = True
                    filters["recency_hours"] = 2
                    filters["exclude_content_patterns"] = [
                        "your prompt", "your system prompt", "how you're programmed",
                        "your character file", "cdl_ai_integration.py", "fix the bot's",
                        "bot is announcing wrong time", "bot should speak like",
                        "testing bot response", "bot container",
                        "bot's speaking style", "bot's detection"
                    ]
                    
                    relevant_memories = await self.memory_manager.retrieve_relevant_memories_optimized(
                        user_id=message_context.user_id,
                        query=message_context.content,
                        query_type=query_type,
                        user_history=user_preferences,
                        filters=filters,
                        limit=20
                    )
                    
                    logger.info(f"🚀 MEMORY: Optimized retrieval returned {len(relevant_memories)} memories")
                    return relevant_memories
                    
                except Exception as e:
                    logger.warning(f"Optimized memory retrieval failed, using fallback: {e}")
            
            # Fallback to context-aware retrieval
            relevant_memories = await self.memory_manager.retrieve_context_aware_memories(
                user_id=message_context.user_id,
                query=message_context.content,
                max_memories=20,
                context=classified_context,
                emotional_context="general conversation"
            )
            
            logger.info(f"🔍 MEMORY: Retrieved {len(relevant_memories)} memories via context-aware fallback")
            return relevant_memories
            
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            return []

    def _classify_query_type(self, content: str) -> str:
        """Classify the type of query for memory optimization."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['remember', 'recall', 'what did', 'told you']):
            return 'recall'
        elif any(word in content_lower for word in ['how', 'what', 'why', 'when', 'where']):
            return 'question'
        elif any(word in content_lower for word in ['feel', 'emotion', 'mood', 'sad', 'happy', 'angry']):
            return 'emotional'
        else:
            return 'general'

    def _build_user_preferences(self, user_id: str, context) -> Dict[str, Any]:
        """Build user preferences for memory filtering."""
        return {
            'user_id': user_id,
            'context_type': getattr(context, 'context_type', None),
            'security_level': getattr(context, 'security_level', None)
        }

    def _build_memory_filters(self, context) -> Dict[str, Any]:
        """Build memory filters from message context."""
        return {
            'context_type': getattr(context, 'context_type', None),
            'security_level': getattr(context, 'security_level', None)
        }

    async def _build_conversation_context(self, message_context: MessageContext, 
                                        relevant_memories: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Build conversation context for LLM processing."""
        # This would typically involve building the conversation history
        # For now, we'll create a basic context structure
        context = []
        
        # Add system context if available
        if relevant_memories:
            memory_summary = self._summarize_memories(relevant_memories)
            context.append({
                "role": "system",
                "content": f"Relevant context from previous conversations: {memory_summary}"
            })
        
        # Add current user message
        context.append({
            "role": "user", 
            "content": message_context.content
        })
        
        return context

    def _summarize_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Create a summary of relevant memories."""
        if not memories:
            return "No previous conversation context available."
        
        # Take the most relevant memories and create a summary
        relevant_snippets = []
        for memory in memories[:5]:  # Top 5 most relevant
            content = memory.get('content', '')
            if content and len(content.strip()) > 0:
                relevant_snippets.append(content[:200])  # Truncate to 200 chars
        
        return " ... ".join(relevant_snippets) if relevant_snippets else "No relevant context found."

    async def _process_ai_components_parallel(self, message_context: MessageContext, 
                                            conversation_context: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process AI components in parallel (emotions, context analysis, etc.)."""
        # This is a simplified version - the full implementation would replicate
        # the complex parallel processing from the Discord handler
        ai_components = {
            'emotion_data': None,
            'context_analysis': None,
            'phase4_context': None,
            'comprehensive_context': None,
            'enhanced_system_prompt': None
        }
        
        try:
            # Placeholder for parallel AI component processing
            # In the full implementation, this would call the same methods
            # as _process_ai_components_parallel in the Discord handler
            logger.debug("AI component processing placeholder")
            
        except Exception as e:
            logger.error(f"AI component processing failed: {e}")
        
        return ai_components

    async def _process_attachments(self, message_context: MessageContext, 
                                 conversation_context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Process message attachments (images, etc.)."""
        if not self.image_processor or not message_context.attachments:
            return conversation_context
        
        try:
            # Process images and add to context
            # This would use the existing image processing logic
            logger.debug(f"Processing {len(message_context.attachments)} attachments")
            # Placeholder for actual image processing
            
        except Exception as e:
            logger.error(f"Attachment processing failed: {e}")
        
        return conversation_context

    async def _generate_response(self, message_context: MessageContext, 
                               conversation_context: List[Dict[str, str]], 
                               ai_components: Dict[str, Any]) -> str:
        """Generate AI response using the conversation context."""
        try:
            # Apply CDL character enhancement
            enhanced_context = await self._apply_cdl_character_enhancement(
                message_context.user_id, conversation_context, message_context, ai_components
            )
            
            # Apply emotion enhancement
            emotion_enhanced_context = await self._add_mixed_emotion_context(
                enhanced_context if enhanced_context else conversation_context,
                message_context.content,
                message_context.user_id,
                ai_components.get('emotion_data'),
                ai_components.get('external_emotion_data')
            )
            
            # Choose final context
            final_context = emotion_enhanced_context if emotion_enhanced_context else conversation_context
            
            # Generate response using LLM
            logger.info(f"🎯 GENERATING: Sending {len(final_context)} messages to LLM")
            
            from src.llm.llm_client import LLMClient
            llm_client = LLMClient()
            
            response = await asyncio.to_thread(
                llm_client.get_chat_response, final_context
            )
            
            logger.info(f"✅ GENERATED: Response with {len(response)} characters")
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."

    async def _apply_cdl_character_enhancement(self, user_id: str, conversation_context: List[Dict[str, str]], 
                                             message_context: MessageContext, ai_components: Dict[str, Any]) -> List[Dict[str, str]]:
        """Apply CDL character enhancement to conversation context."""
        # Placeholder for CDL character enhancement
        # This would replicate the _apply_cdl_character_enhancement logic from Discord handler
        logger.debug("CDL character enhancement placeholder")
        return conversation_context

    async def _add_mixed_emotion_context(self, conversation_context: List[Dict[str, str]], 
                                       content: str, user_id: str, emotion_data, external_emotion_data) -> List[Dict[str, str]]:
        """Add emotion context to conversation."""
        # Placeholder for emotion context enhancement
        logger.debug("Emotion context enhancement placeholder")
        return conversation_context

    async def _validate_and_sanitize_response(self, response: str, message_context: MessageContext) -> str:
        """Validate response for character consistency and sanitize for security."""
        try:
            # Character consistency check
            response = await self._validate_character_consistency(response, message_context.user_id, message_context)
            
            # Security scan for system leakage
            from src.security.system_message_security import scan_response_for_system_leakage
            leakage_scan = scan_response_for_system_leakage(response)
            if leakage_scan["has_leakage"]:
                logger.error(f"SECURITY: System message leakage detected in response to user {message_context.user_id}")
                response = leakage_scan["sanitized_response"]
            
            # Meta-analysis sanitization
            response = self._sanitize_meta_analysis(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            return response  # Return original if validation fails

    async def _validate_character_consistency(self, response: str, user_id: str, message_context: MessageContext) -> str:
        """Validate that response maintains character consistency."""
        # Placeholder for character consistency validation
        logger.debug("Character consistency validation placeholder")
        return response

    def _sanitize_meta_analysis(self, response: str) -> str:
        """Sanitize response to prevent meta-analytical sections."""
        try:
            import re
            patterns = [
                "Core Conversation Analysis",
                "Emotional Analysis", 
                "Technical Metadata",
                "Personality & Interaction",
                "Overall Assessment",
            ]
            trigger_count = sum(p in response for p in patterns)
            coaching_phrase = "Do you want me to" in response
            
            if trigger_count >= 2 or coaching_phrase:
                logger.warning("Meta/coaching analytical response detected - sanitizing")
                lines = response.splitlines()
                natural_parts = []
                for line in lines:
                    if any(p in line for p in patterns) or re.match(r"^[A-Z][A-Za-z &]+:\s*$", line.strip()):
                        break
                    if line.strip():
                        natural_parts.append(line.strip())
                
                base_text = " ".join(natural_parts).strip()
                if not base_text:
                    base_text = "I apologize, but I need to rephrase my response to stay in character."
                
                return base_text + "\n\n(Internal analytical sections omitted to preserve character immersion.)"
            
            return response
            
        except Exception as e:
            logger.error(f"Meta-analysis sanitization failed: {e}")
            return response

    async def _store_conversation_memory(self, message_context: MessageContext, response: str, 
                                       ai_components: Dict[str, Any]) -> bool:
        """Store conversation in memory system."""
        if not self.memory_manager:
            return False
        
        try:
            await self.memory_manager.store_conversation(
                user_id=message_context.user_id,
                user_message=message_context.content,
                bot_response=response,
                pre_analyzed_emotion_data=ai_components.get('emotion_data')
            )
            
            # Verify storage
            verification_memories = await self.memory_manager.retrieve_context_aware_memories(
                user_id=message_context.user_id,
                query=message_context.content,
                max_memories=1
            )
            
            if verification_memories:
                logger.info(f"✅ MEMORY: Successfully stored and verified conversation for user {message_context.user_id}")
                return True
            else:
                logger.warning(f"⚠️ MEMORY: Storage verification failed for user {message_context.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            return False


def create_message_processor(bot_core, memory_manager, llm_client, **kwargs) -> MessageProcessor:
    """Factory function to create a MessageProcessor instance."""
    return MessageProcessor(
        bot_core=bot_core,
        memory_manager=memory_manager, 
        llm_client=llm_client,
        **kwargs
    )