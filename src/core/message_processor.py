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
import os
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity
from src.adapters.platform_adapters import (
    create_discord_message_adapter,
    create_discord_attachment_adapters
)

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
    # Platform-specific context for features like typing indicators
    platform_context: Optional[Any] = None  # Discord channel, HTTP response object, etc.

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
            logger.info("🔄 MESSAGE PROCESSOR: Starting processing for user %s on platform %s", 
                       message_context.user_id, message_context.platform)
            
            # Phase 1: Security validation
            validation_result = await self._validate_security(message_context)
            if not validation_result["is_safe"]:
                logger.warning("SECURITY: Rejected unsafe message from user %s", message_context.user_id)
                return ProcessingResult(
                    response="I'm sorry, but I can't process that message for security reasons.",
                    success=False,
                    error_message="Security validation failed"
                )
            
            # Update message content with sanitized version
            message_context.content = validation_result["sanitized_content"]
            if validation_result["warnings"]:
                logger.warning("SECURITY: Input warnings for user %s: %s", 
                             message_context.user_id, validation_result['warnings'])
            
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
            
            # Phase 9: Memory storage (vector + knowledge graph)
            memory_stored = await self._store_conversation_memory(
                message_context, response, ai_components
            )
            
            # Phase 9b: Knowledge extraction and storage (PostgreSQL)
            knowledge_stored = await self._extract_and_store_knowledge(
                message_context, ai_components
            )
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.info("✅ MESSAGE PROCESSOR: Successfully processed message for user %s in %dms", 
                       message_context.user_id, processing_time_ms)
            
            return ProcessingResult(
                response=response,
                success=True,
                processing_time_ms=processing_time_ms,
                memory_stored=memory_stored,
                metadata={
                    "memory_count": len(relevant_memories) if relevant_memories else 0,
                    "knowledge_stored": knowledge_stored,
                    "memory_count": len(relevant_memories) if relevant_memories else 0,
                    "ai_components": ai_components,
                    "security_validation": validation_result
                }
            )
            
        except (ValueError, KeyError, TypeError) as e:
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error("❌ MESSAGE PROCESSOR: Failed to process message for user %s: %s", 
                        message_context.user_id, str(e))
            logger.debug("❌ MESSAGE PROCESSOR: Traceback: %s", traceback.format_exc())
            
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
            # Create adapter for Discord-specific components
            discord_message = create_discord_message_adapter(message_context)
            
            validation_result = await self.security_validator.validate_input(discord_message)
            self._last_security_validation = validation_result
            return validation_result
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Security validation failed: %s", str(e))
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
                    logger.info("🏷️ Auto-detected name '%s' for user %s", detected_name, message_context.user_id)
        except (ImportError, AttributeError, ValueError) as e:
            logger.debug("Name detection failed: %s", str(e))

    async def _retrieve_relevant_memories(self, message_context: MessageContext) -> List[Dict[str, Any]]:
        """Retrieve relevant memories with context-aware filtering."""
        if not self.memory_manager:
            logger.warning("Memory manager not available; skipping memory retrieval.")
            return []

        try:
            # Create platform-agnostic message context classification
            classified_context = self._classify_message_context(message_context)
            logger.debug("Message context classified: %s", classified_context.context_type.value)

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
                    
                    logger.info("🚀 MEMORY: Optimized retrieval returned %d memories", len(relevant_memories))
                    return relevant_memories
                    
                except (AttributeError, ValueError, TypeError) as e:
                    logger.warning("Optimized memory retrieval failed, using fallback: %s", str(e))
            
            # Fallback to context-aware retrieval
            relevant_memories = await self.memory_manager.retrieve_context_aware_memories(
                user_id=message_context.user_id,
                query=message_context.content,
                max_memories=20,
                context=classified_context,
                emotional_context="general conversation"
            )
            
            logger.info("🔍 MEMORY: Retrieved %d memories via context-aware fallback", len(relevant_memories))
            return relevant_memories
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Memory retrieval failed: %s", str(e))
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
        """
        🚀 SOPHISTICATED CONVERSATION CONTEXT BUILDING 🚀
        
        Build conversation context for LLM processing with sophisticated memory narrative,
        conversation cache integration, and advanced system message consolidation.
        
        Restored from original events.py implementation with full sophistication.
        """
        conversation_context = []
        
        # Debug memory input
        user_id = message_context.user_id
        logger.info(f"🤖 LLM CONTEXT DEBUG: Building context for user {user_id}")
        logger.info(f"🤖 LLM CONTEXT DEBUG: Memory input - {len(relevant_memories) if relevant_memories else 0} memories")
        
        # Add time context for temporal awareness
        from src.utils.helpers import get_current_time_context
        time_context = get_current_time_context()
        
        # 🚨 SOPHISTICATED MEMORY NARRATIVE BUILDING: Restored from original implementation
        memory_fragments = []
        if relevant_memories:
            logger.info(f"🤖 LLM CONTEXT DEBUG: Processing {len(relevant_memories)} memories for context")
            
            # Handle both legacy and hierarchical memory formats (original sophistication)
            global_facts = []
            user_memories = []
            
            for i, m in enumerate(relevant_memories):
                logger.info(f"🤖 LLM CONTEXT DEBUG: Memory {i+1} structure: {list(m.keys())}")
                
                # Check if memory has metadata (legacy format) or use memory_type (hierarchical format)
                if "metadata" in m:
                    # Legacy format
                    if m["metadata"].get("is_global", False):
                        global_facts.append(m)
                    else:
                        user_memories.append(m)
                else:
                    # Hierarchical format - treat all as user memories for now
                    user_memories.append(m)
            
            logger.info(f"🤖 LLM CONTEXT DEBUG: Categorized - {len(global_facts)} global facts, {len(user_memories)} user memories")
            logger.info(f"🔍 CONDITION DEBUG: user_memories={len(user_memories) if user_memories else 0}")
            
            # Process global facts
            if global_facts:
                gf_text = "; ".join(
                    memory["metadata"].get("fact", "")[:160] for memory in global_facts
                    if memory.get("metadata", {}).get("type") == "global_fact"
                )
                if gf_text:
                    memory_fragments.append(f"Shared truths: {gf_text}")
                    logger.info(f"🤖 LLM CONTEXT DEBUG: Added global facts: {gf_text[:100]}...")
            
            # 🚀 ADVANCED USER MEMORY PROCESSING: Restored sophisticated narrative building
            if user_memories:
                logger.info(f"🔍 USER MEMORIES DEBUG: Processing {len(user_memories)} user memories")
                
                conversation_memory_parts = []
                recent_conversation_parts = []  # Prioritize recent conversation context
                
                for memory in user_memories[:6]:  # limit
                    # ALWAYS try content field first - no complex format detection
                    content = memory.get("content", "")
                    timestamp = memory.get("timestamp", "")
                    logger.info(f"🔍 MEMORY DEBUG [{memory.get('id', 'unknown')}]: content='{content[:50]}...', timestamp='{timestamp}', has_metadata={'metadata' in memory}")
                    
                    # Determine if this is recent conversation (last 2 hours)
                    is_recent = False
                    if timestamp:
                        try:
                            from datetime import datetime, timedelta
                            if isinstance(timestamp, str):
                                # Parse timestamp
                                memory_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            elif isinstance(timestamp, (int, float)):
                                memory_time = datetime.fromtimestamp(timestamp)
                            else:
                                memory_time = timestamp
                            
                            # Check if within last 2 hours
                            if (datetime.now(memory_time.tzinfo if memory_time.tzinfo else None) - memory_time) < timedelta(hours=2):
                                is_recent = True
                        except Exception as e:
                            logger.debug(f"Could not parse timestamp for recency check: {e}")
                    
                    if content and content.strip():
                        # Try to parse if it contains conversation structure
                        if "User:" in content and "Bot:" in content:
                            memory_text = f"[Previous conversation: {content[:120]}]"
                        else:
                            memory_text = f"[Memory: {content[:120]}]"
                        
                        # Prioritize recent conversation
                        if is_recent:
                            recent_conversation_parts.append(memory_text)
                            logger.info(f"🔍 MEMORY DEBUG: ✅ Added RECENT memory content")
                        else:
                            conversation_memory_parts.append(memory_text)
                            logger.info(f"🔍 MEMORY DEBUG: ✅ Added older memory content")
                    else:
                        # Only try metadata if content is empty/missing
                        md = memory.get("metadata", {})
                        if md.get("user_message") and md.get("bot_response"):
                            user_msg = md.get("user_message")[:100]
                            bot_msg = md.get("bot_response")[:100]
                            memory_text = f"[User said: \"{user_msg}\", You responded: \"{bot_msg}\"]"
                            
                            if is_recent:
                                recent_conversation_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added RECENT from metadata conversation")
                            else:
                                conversation_memory_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added older from metadata conversation")
                        elif md.get("user_message"):
                            user_msg = md.get("user_message")[:120]
                            memory_text = f"[User said: \"{user_msg}\"]"
                            
                            if is_recent:
                                recent_conversation_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added RECENT from metadata user message")
                            else:
                                conversation_memory_parts.append(memory_text)
                                logger.info(f"🔍 MEMORY DEBUG: ✅ Added older from metadata user message")
                        elif md.get("type") == "user_fact":
                            memory_text = f"[Fact: {md.get('fact', '')[:120]}]"
                            conversation_memory_parts.append(memory_text)  # Facts are not time-sensitive
                            logger.info(f"🔍 MEMORY DEBUG: ✅ Added from metadata fact")
                        else:
                            logger.warning(f"🔍 MEMORY DEBUG: ❌ No valid content or metadata structure")
                
                # Build memory narrative with recent conversation prioritized
                memory_parts = []
                if recent_conversation_parts:
                    memory_parts.append("RECENT CONVERSATION CONTEXT: " + "; ".join(recent_conversation_parts))
                if conversation_memory_parts:
                    memory_parts.append("PREVIOUS INTERACTIONS AND FACTS: " + "; ".join(conversation_memory_parts))
                
                if memory_parts:
                    memory_fragments.append(" ".join(memory_parts))
                    logger.info(f"🤖 LLM CONTEXT DEBUG: Added {len(recent_conversation_parts)} recent + {len(conversation_memory_parts)} older memories")
                else:
                    logger.error(f"🤖 LLM CONTEXT DEBUG: FAILED - No valid memory content found from {len(user_memories)} memories")
            else:
                logger.info(f"🤖 LLM CONTEXT DEBUG: No memories to process (memories: {relevant_memories is not None})")
        
        memory_narrative = " ".join(memory_fragments)
        logger.info(f"🤖 LLM CONTEXT DEBUG: Final memory narrative: '{memory_narrative[:200]}...'")
        
        # � CONVERSATION CACHE INTEGRATION: Restored sophisticated conversation history processing
        try:
            from src.utils.helpers import generate_conversation_summary
            
            # Get recent messages from conversation cache if available
            recent_messages = []
            if self.conversation_cache:
                try:
                    # Try to get recent messages from conversation cache
                    cache_key = f"recent_messages_{user_id}"
                    cached_messages = await self.conversation_cache.get(cache_key)
                    if cached_messages:
                        recent_messages = cached_messages
                        logger.info(f"🔥 CONVERSATION CACHE: Retrieved {len(recent_messages)} cached messages")
                except Exception as e:
                    logger.debug(f"Conversation cache retrieval failed: {e}")
            
            # Fallback to memory manager conversation history
            if not recent_messages:
                conversation_history = await self.memory_manager.get_conversation_history(
                    user_id=user_id, 
                    limit=15  # Get more messages for better context (matching previous implementation)
                )
                
                # Convert to expected format for generate_conversation_summary
                recent_messages = []
                for msg in conversation_history:
                    if isinstance(msg, dict):
                        recent_messages.append({
                            'content': msg.get('content', ''),
                            'role': msg.get('role', 'user'),
                            'bot': msg.get('role') in ['assistant', 'bot']
                        })
                    else:
                        recent_messages.append({
                            'content': getattr(msg, 'content', ''),
                            'role': getattr(msg, 'role', 'user'),
                            'bot': getattr(msg, 'role', 'user') in ['assistant', 'bot']
                        })
                
                logger.info(f"🔥 FALLBACK: Using memory manager conversation history - {len(recent_messages)} messages")
            
            # ALWAYS generate conversation summary - NO CONDITIONAL FALLBACKS
            conversation_summary = generate_conversation_summary(recent_messages, user_id)
            if conversation_summary and len(conversation_summary) > 600:
                conversation_summary = conversation_summary[:600] + "..."
            
            logger.info(f"📝 CONVERSATION SUMMARY: Generated summary ({len(conversation_summary)} chars)")
            
        except Exception as e:
            logger.warning(f"⚠️ Conversation cache integration failed: {e}")
            conversation_summary = ""
            recent_messages = []
        
        # 🚀 ADVANCED SYSTEM MESSAGE CONSOLIDATION: Restored sophisticated system prompt building
        
        # Build comprehensive system message with all contexts
        system_prompt_content = f"CURRENT DATE & TIME: {time_context}"
        
        # Add memory narrative if available
        if memory_narrative:
            system_prompt_content += f"\n\n{memory_narrative}"
        
        # Add conversation summary if available
        if conversation_summary:
            system_prompt_content += f"\n\nRecent thread: {conversation_summary}"
        
        # Add attachment guard if needed
        attachment_guard = ""
        if message_context.attachments and len(message_context.attachments) > 0:
            bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
            attachment_guard = (
                f" Image policy: respond only in-character ({bot_name}), never output analysis sections, "
                f"headings, scores, tables, coaching offers, or 'Would you like me to' prompts."
            )
        
        # Add guidance clause for natural conversation
        bot_name = os.getenv('DISCORD_BOT_NAME', 'Assistant')
        guidance_clause = (
            f" Communication style: Respond naturally and authentically as {bot_name} - "
            f"be warm, genuine, and conversational. No meta-analysis, breakdowns, bullet summaries, "
            f"or section headings. Stay in character and speak like a real person would."
        )
        
        # Consolidate all system context
        consolidated_system = system_prompt_content + attachment_guard + guidance_clause
        
        conversation_context.append({"role": "system", "content": consolidated_system})
        
        # 🚀 SOPHISTICATED RECENT MESSAGE PROCESSING: Restored conversation cache integration
        try:
            if recent_messages:
                logger.info(f"🔥 CONTEXT DEBUG: Processing {len(recent_messages)} recent messages for conversation context")
                
                # Add recent messages with proper alternation
                user_assistant_messages = []
                
                # Filter out commands and responses
                skip_next_bot_response = False
                for msg in recent_messages:
                    msg_content = msg.get('content', '')
                    is_bot_msg = msg.get('bot', False)
                    
                    logger.info(f"🔥 CONTEXT DEBUG: Processing message - is_bot: {is_bot_msg}, content: '{msg_content[:100]}...'")
                    
                    if msg_content.startswith("!"):
                        logger.debug(f"Skipping command from conversation history: {msg_content[:50]}...")
                        skip_next_bot_response = True
                        continue

                    if is_bot_msg and skip_next_bot_response:
                        logger.debug(f"Skipping bot response to command: {msg_content[:50]}...")
                        skip_next_bot_response = False
                        continue

                    if not is_bot_msg:
                        skip_next_bot_response = False

                    role = "assistant" if is_bot_msg else "user"
                    user_assistant_messages.append({"role": role, "content": msg_content})
                    logger.info(f"🔥 CONTEXT DEBUG: Added to conversation context as [{role}]: '{msg_content[:100]}...'")
                
                logger.info(f"🔥 CONTEXT DEBUG: Before alternation fix: {len(user_assistant_messages)} messages")
                
                # Apply alternation fix to ensure proper user/assistant flow
                fixed_history = self._fix_message_alternation(user_assistant_messages)
                logger.info(f"🔥 CONTEXT DEBUG: After alternation fix: {len(fixed_history)} messages")
                
                # Add the conversation history to context
                conversation_context.extend(fixed_history)
                
                logger.info(f"✅ SOPHISTICATED CONTEXT: Added {len(recent_messages)} raw messages, "
                           f"{len(fixed_history)} after filtering/alternation for conversation continuity")
            else:
                logger.info("🔥 CONTEXT DEBUG: No recent messages available for context")
                
        except Exception as e:
            logger.warning(f"⚠️ Recent message processing failed: {e}")
        
        # Add current user message
        conversation_context.append({
            "role": "user", 
            "content": message_context.content
        })
        
        logger.info(f"🔥 CONTEXT DEBUG: Final conversation context has {len(conversation_context)} total messages")
        
        return conversation_context

    def _fix_message_alternation(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Fix message alternation to ensure proper user/assistant flow.
        Removes duplicate consecutive messages from the same role.
        Based on the previous Discord implementation pattern.
        """
        if not messages:
            return []
        
        fixed_messages = []
        last_role = None
        
        for msg in messages:
            current_role = msg.get('role')
            
            # Skip if same role as previous message (avoid duplicates)
            if current_role != last_role:
                fixed_messages.append(msg)
                last_role = current_role
        
        return fixed_messages

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
        """
        🚀 SOPHISTICATED AI COMPONENT PROCESSING 🚀
        
        Process 9+ AI components in parallel using asyncio.gather for maximum efficiency.
        Restored from original events.py implementation with full Phase 4 intelligence.
        
        Components processed:
        1. Vector-native emotion analysis 
        2. Enhanced context analysis
        3. Dynamic personality profiling
        4. Phase 4 human-like intelligence
        5. Thread management analysis  
        6. Proactive engagement analysis
        7. Human-like memory optimization
        8. Conversation analysis
        9. Context switch detection
        """
        ai_components = {}
        
        try:
            logger.info("🧠 SOPHISTICATED AI PROCESSING: Starting 9-component parallel analysis")
            
            # 🚀 PHASE 4 SOPHISTICATED INTELLIGENCE PROCESSING 
            # Restored from original implementation with full asyncio.gather parallel processing
            
            # Prepare parallel tasks for sophisticated AI component processing
            tasks = []
            task_names = []
            
            # Task 1: Vector-native emotion analysis using existing infrastructure
            if self.bot_core and hasattr(self.bot_core, 'phase2_integration'):
                emotion_task = self._analyze_emotion_vector_native(
                    message_context.user_id, 
                    message_context.content,
                    message_context
                )
                tasks.append(emotion_task)
                task_names.append("emotion_analysis")
            
            # Task 2: Enhanced context analysis using hybrid detector
            context_task = self._analyze_enhanced_context(
                message_context.content,
                conversation_context,
                message_context.user_id
            )
            tasks.append(context_task)
            task_names.append("context_analysis")
            
            # Task 3: Dynamic personality profiling if available
            if self.bot_core and hasattr(self.bot_core, 'dynamic_personality_profiler'):
                personality_task = self._analyze_dynamic_personality(
                    message_context.user_id,
                    message_context.content,
                    message_context
                )
                tasks.append(personality_task)
                task_names.append("personality_analysis")
            
            # Task 4: Phase 4 human-like intelligence processing
            if self.bot_core and hasattr(self.bot_core, 'phase2_integration'):
                phase4_task = self._process_phase4_intelligence_sophisticated(
                    message_context.user_id,
                    message_context.content,
                    message_context,
                    conversation_context
                )
                tasks.append(phase4_task)
                task_names.append("phase4_intelligence")
            
            # Task 5: Thread management analysis (Phase 4.2)
            if self.bot_core and hasattr(self.bot_core, 'phase4_thread_manager'):
                thread_task = self._process_thread_management(
                    message_context.user_id,
                    message_context.content,
                    message_context
                )
                tasks.append(thread_task)
                task_names.append("thread_management")
            
            # Task 6: Proactive engagement analysis (Phase 4.3)
            if self.bot_core and hasattr(self.bot_core, 'engagement_engine'):
                engagement_task = self._process_proactive_engagement(
                    message_context.user_id,
                    message_context.content,
                    message_context
                )
                tasks.append(engagement_task)
                task_names.append("proactive_engagement")
            
            # Task 7: Human-like memory optimization
            if self.memory_manager and hasattr(self.memory_manager, 'human_like_optimizer'):
                memory_task = self._process_human_like_memory(
                    message_context.user_id,
                    message_context.content,
                    message_context
                )
                tasks.append(memory_task)
                task_names.append("human_like_memory")
            
            # Task 8: Conversation analysis for enhanced guidance
            conversation_analysis_task = self._analyze_conversation_patterns(
                message_context.content,
                conversation_context,
                message_context.user_id
            )
            tasks.append(conversation_analysis_task)
            task_names.append("conversation_analysis")
            
            # Task 9: Context switch detection for conversation flow
            if self.bot_core and hasattr(self.bot_core, 'context_switch_detector'):
                context_switch_task = self._detect_context_switches(
                    message_context.content,
                    conversation_context,
                    message_context.user_id
                )
                tasks.append(context_switch_task)
                task_names.append("context_switches")
            
            logger.info(f"🧠 SOPHISTICATED AI PROCESSING: Executing {len(tasks)} components in parallel")
            
            # 🚀 PARALLEL EXECUTION: Use asyncio.gather for maximum efficiency
            import asyncio
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions gracefully
            idx = 0
            for task_name in task_names:
                if idx < len(results):
                    result = results[idx]
                    if not isinstance(result, Exception):
                        ai_components[task_name] = result
                        logger.debug(f"✅ {task_name}: Successfully processed")
                    else:
                        ai_components[task_name] = None
                        logger.warning(f"⚠️ {task_name}: Failed with {type(result).__name__}: {result}")
                    idx += 1
            
            # 🚀 SOPHISTICATED RESULT INTEGRATION: Merge components with intelligent prioritization
            
            # Extract core components for backward compatibility
            ai_components['emotion_data'] = ai_components.get('emotion_analysis')
            ai_components['external_emotion_data'] = ai_components.get('emotion_analysis')
            ai_components['context_analysis'] = ai_components.get('context_analysis')
            ai_components['personality_context'] = ai_components.get('personality_analysis')
            ai_components['phase4_context'] = ai_components.get('phase4_intelligence')
            
            # Build comprehensive context from all AI components
            comprehensive_context = {}
            
            # Add Phase 4 intelligence context
            if ai_components.get('phase4_intelligence'):
                phase4_context = ai_components['phase4_intelligence']
                if hasattr(phase4_context, '__dict__'):
                    comprehensive_context.update({
                        'phase4_context': phase4_context,
                        'interaction_type': getattr(phase4_context, 'interaction_type', None),
                        'conversation_mode': getattr(phase4_context, 'conversation_mode', None),
                    })
            
            # Add thread management results (Phase 4.2)
            if ai_components.get('thread_management'):
                comprehensive_context['phase4_2_thread_analysis'] = ai_components['thread_management']
                logger.info("🧠 Added Phase 4.2 Advanced Thread Management results to context")
            
            # Add proactive engagement results (Phase 4.3)
            if ai_components.get('proactive_engagement'):
                comprehensive_context['phase4_3_engagement_analysis'] = ai_components['proactive_engagement']
                logger.info("🧠 Added Phase 4.3 Proactive Engagement results to context")
            
            # Add human-like memory optimization
            if ai_components.get('human_like_memory'):
                human_like_context = ai_components['human_like_memory']
                if isinstance(human_like_context, dict):
                    comprehensive_context.update({
                        'human_like_context': human_like_context.get('human_context', {}),
                        'human_like_memories': human_like_context.get('memories', []),
                        'human_like_performance': human_like_context.get('search_performance', {})
                    })
                    logger.info("🧠 Added human-like memory optimization to context")
            
            # Add conversation analysis for enhanced response guidance
            if ai_components.get('conversation_analysis'):
                conversation_analysis = ai_components['conversation_analysis']
                if isinstance(conversation_analysis, dict):
                    comprehensive_context.update({
                        'conversation_analysis': conversation_analysis,
                        'response_guidance': conversation_analysis.get('response_guidance', ''),
                        'conversation_mode': conversation_analysis.get('mode', 'standard'),
                        'interaction_type': conversation_analysis.get('interaction_type', 'general'),
                        'personality_type': conversation_analysis.get('personality_type', 'default'),
                        'relationship_level': conversation_analysis.get('relationship_level', 'acquaintance')
                    })
                    logger.info("🧠 Added conversation analysis for enhanced response guidance")
            
            # Add context switches for conversation flow
            if ai_components.get('context_switches'):
                comprehensive_context['context_switches'] = ai_components['context_switches']
                logger.info("🧠 Added context switch detection to comprehensive context")
            
            # Store comprehensive context in ai_components
            ai_components['comprehensive_context'] = comprehensive_context if comprehensive_context else None
            ai_components['enhanced_system_prompt'] = None  # Generated later in CDL enhancement
            
            logger.info(f"✅ SOPHISTICATED AI PROCESSING: Completed {len(task_names)} components with comprehensive integration")
            logger.info(f"🧠 Final comprehensive context size: {len(str(comprehensive_context))} chars")
            logger.info(f"🧠 Final comprehensive context keys: {list(comprehensive_context.keys())}")
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Sophisticated AI component processing failed: %s", str(e))
            # Fallback to basic components
            ai_components = {
                'emotion_data': None,
                'external_emotion_data': None,
                'context_analysis': None,
                'personality_context': None,
                'phase4_context': None,
                'comprehensive_context': None,
                'enhanced_system_prompt': None
            }
        
        return ai_components

    async def _analyze_enhanced_context(self, content: str, conversation_context: List[Dict[str, str]], 
                                      user_id: str) -> Dict[str, Any]:
        """Enhanced context analysis with vector boost and confidence scoring."""
        try:
            # Use the hybrid context detector for sophisticated analysis
            context_result = self.detect_context_patterns(
                message=content,
                conversation_history=conversation_context,
                vector_boost=True,
                confidence_threshold=0.7
            )
            logger.debug(f"Enhanced context analysis successful for user {user_id}")
            return context_result
        except Exception as e:
            logger.debug(f"Enhanced context analysis failed: {e}")
            return {
                'needs_ai_guidance': True,
                'needs_memory_context': True,
                'needs_personality': True,
                'needs_voice_style': True,
                'is_greeting': False,
                'is_simple_question': False,
                'confidence_scores': {},
                'detection_method': 'fallback'
            }

    async def _process_phase4_intelligence_sophisticated(self, user_id: str, content: str, 
                                                       message_context: MessageContext,
                                                       conversation_context: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Sophisticated Phase 4 intelligence processing with full integration."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase2_integration'):
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Process with full Phase 4 sophistication
            phase4_context = await self.bot_core.phase2_integration.process_phase4_intelligence(
                user_id=user_id,
                message=discord_message,
                recent_messages=conversation_context,
                external_emotion_data=None,
                phase2_context=None
            )
            
            logger.debug(f"Sophisticated Phase 4 intelligence processing successful for user {user_id}")
            return phase4_context
            
        except Exception as e:
            logger.debug(f"Sophisticated Phase 4 intelligence processing failed: {e}")
            return None

    async def _process_thread_management(self, user_id: str, content: str, 
                                       message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Process Phase 4.2 Advanced Thread Management."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase4_thread_manager'):
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Process thread management
            thread_result = await self.bot_core.phase4_thread_manager.analyze_thread_context(
                user_id=user_id,
                message=discord_message,
                conversation_history=[]
            )
            
            logger.debug(f"Thread management analysis successful for user {user_id}")
            return thread_result
            
        except Exception as e:
            logger.debug(f"Thread management analysis failed: {e}")
            return None

    async def _process_proactive_engagement(self, user_id: str, content: str, 
                                          message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Process Phase 4.3 Proactive Engagement Analysis."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'engagement_engine'):
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Process proactive engagement
            engagement_result = await self.bot_core.engagement_engine.analyze_engagement_potential(
                user_id=user_id,
                message=discord_message,
                conversation_history=[]
            )
            
            logger.debug(f"Proactive engagement analysis successful for user {user_id}")
            return engagement_result
            
        except Exception as e:
            logger.debug(f"Proactive engagement analysis failed: {e}")
            return None

    async def _process_human_like_memory(self, user_id: str, content: str, 
                                       message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Process human-like memory optimization."""
        try:
            if not self.memory_manager or not hasattr(self.memory_manager, 'human_like_optimizer'):
                return None
            
            # Process human-like memory optimization
            memory_result = await self.memory_manager.human_like_optimizer.optimize_memory_context(
                user_id=user_id,
                query=content,
                conversation_context=[]
            )
            
            logger.debug(f"Human-like memory optimization successful for user {user_id}")
            return memory_result
            
        except Exception as e:
            logger.debug(f"Human-like memory optimization failed: {e}")
            return None

    async def _analyze_conversation_patterns(self, content: str, conversation_context: List[Dict[str, str]], 
                                           user_id: str) -> Dict[str, Any]:
        """Analyze conversation patterns for enhanced response guidance."""
        try:
            # Analyze conversation patterns and provide guidance
            analysis = {
                'mode': 'standard',
                'interaction_type': 'general',
                'personality_type': 'default',
                'relationship_level': 'acquaintance',
                'response_guidance': 'Respond naturally and authentically'
            }
            
            # Detect conversation patterns
            content_lower = content.lower()
            
            if any(word in content_lower for word in ['how are you', 'how have you been', 'whats up']):
                analysis['interaction_type'] = 'greeting'
                analysis['response_guidance'] = 'Respond warmly to greeting'
            elif any(word in content_lower for word in ['help', 'assist', 'support']):
                analysis['interaction_type'] = 'assistance_request'
                analysis['response_guidance'] = 'Provide helpful guidance'
            elif any(word in content_lower for word in ['tell me about', 'explain', 'what is']):
                analysis['interaction_type'] = 'information_seeking'
                analysis['response_guidance'] = 'Provide informative explanation'
            
            logger.debug(f"Conversation pattern analysis successful for user {user_id}")
            return analysis
            
        except Exception as e:
            logger.debug(f"Conversation pattern analysis failed: {e}")
            return {
                'mode': 'standard',
                'interaction_type': 'general',
                'personality_type': 'default',
                'relationship_level': 'acquaintance',
                'response_guidance': 'Respond naturally and authentically'
            }

    async def _detect_context_switches(self, content: str, conversation_context: List[Dict[str, str]], 
                                     user_id: str) -> Optional[Dict[str, Any]]:
        """Detect context switches for conversation flow management."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'context_switch_detector'):
                return None
            
            # Detect context switches
            context_switches = await self.bot_core.context_switch_detector.detect_switches(
                current_message=content,
                conversation_history=conversation_context,
                user_id=user_id
            )
            
            logger.debug(f"Context switch detection successful for user {user_id}")
            return context_switches
            
        except Exception as e:
            logger.debug(f"Context switch detection failed: {e}")
            return None

    async def _process_attachments(self, message_context: MessageContext, 
                                 conversation_context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Process message attachments (images, etc.)."""
        if not self.image_processor or not message_context.attachments:
            return conversation_context
        
        try:
            # Process images and add to context using existing image processing logic
            logger.debug("Processing %d attachments", len(message_context.attachments))
            
            # Use existing image processing from utils.helpers
            from src.utils.helpers import process_message_with_images
            
            # Convert MessageContext attachments to Discord format using adapter
            discord_attachments = create_discord_attachment_adapters(message_context.attachments)
            
            # Process images with existing logic
            enhanced_context = await process_message_with_images(
                message_context.content,
                discord_attachments,
                conversation_context,
                self.llm_client,
                self.image_processor
            )
            
            return enhanced_context
            
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Attachment processing failed: %s", str(e))
        
        return conversation_context

    async def _analyze_emotion_vector_native(self, user_id: str, content: str, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Analyze emotions using vector-native approach."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase2_integration'):
                return None
            
            # Use the enhanced vector emotion analyzer from the bot core
            from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
            
            analyzer = EnhancedVectorEmotionAnalyzer(
                vector_memory_manager=self.memory_manager
            )
            
            # Analyze emotion with vector intelligence (use the correct method name)
            emotion_results = await analyzer.analyze_emotion(
                content=content,
                user_id=user_id,
                conversation_context=[],  # Could be enhanced with history
                recent_emotions=None
            )
            
            # Convert results to dictionary format
            if emotion_results:
                emotion_data = {
                    'primary_emotion': emotion_results.primary_emotion,
                    'intensity': emotion_results.intensity,
                    'confidence': emotion_results.confidence,
                    'analysis_method': 'vector_native'
                }
                logger.debug("Vector emotion analysis successful for user %s", user_id)
                return emotion_data
            
        except Exception as e:
            logger.debug("Vector emotion analysis failed: %s", str(e))
        
        return None

    async def _analyze_dynamic_personality(self, user_id: str, content: str, message_context: MessageContext) -> Optional[Dict[str, Any]]:
        """Analyze dynamic personality if profiler is available."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'dynamic_personality_profiler'):
                return None
            
            profiler = self.bot_core.dynamic_personality_profiler
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Analyze personality
            personality_data = await profiler.analyze_personality(
                user_id=user_id,
                content=content,
                message=discord_message,
                recent_messages=[]
            )
            
            logger.debug("Dynamic personality analysis successful for user %s", user_id)
            return personality_data
            
        except Exception as e:
            logger.debug("Dynamic personality analysis failed: %s", str(e))
        
        return None

    async def _process_phase4_intelligence(self, user_id: str, content: str, message_context: MessageContext, emotion_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Process Phase 4 human-like intelligence if available."""
        try:
            if not self.bot_core or not hasattr(self.bot_core, 'phase2_integration'):
                return None
            
            # Create adapter for Discord-specific component
            discord_message = create_discord_message_adapter(message_context)
            
            # Use Phase 4 integration if available
            phase4_context = await self.bot_core.phase2_integration.process_phase4_intelligence(
                user_id=user_id,
                message=discord_message,
                recent_messages=[],
                external_emotion_data=emotion_data,
                phase2_context=emotion_data
            )
            
            logger.debug("Phase 4 intelligence processing successful for user %s", user_id)
            return phase4_context
            
        except Exception as e:
            logger.debug("Phase 4 intelligence processing failed: %s", str(e))
        
        return None

    def detect_context_patterns(self, message: str, conversation_history: List[Dict[str, str]], 
                               vector_boost: bool = True, confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """Detect context patterns using hybrid context detector."""
        try:
            from src.prompts.hybrid_context_detector import create_hybrid_context_detector
            
            # Create context detector with memory manager if available
            context_detector = create_hybrid_context_detector(memory_manager=self.memory_manager)
            
            # Analyze context using the correct method name
            context_analysis = context_detector.analyze_context(
                message=message,
                user_id="context_analysis"  # Could be enhanced with actual user_id
            )
            
            # Convert to expected format
            context_result = {
                'needs_ai_guidance': context_analysis.needs_ai_guidance,
                'needs_memory_context': context_analysis.needs_memory_context,
                'needs_personality': context_analysis.needs_personality,
                'needs_voice_style': context_analysis.needs_voice_style,
                'is_greeting': context_analysis.is_greeting,
                'is_simple_question': context_analysis.is_simple_question,
                'confidence_scores': context_analysis.confidence_scores,
                'detection_method': context_analysis.detection_method
            }
            
            logger.debug("Context pattern detection successful")
            return context_result
            
        except Exception as e:
            logger.debug("Context pattern detection failed: %s", str(e))
            # Return sensible defaults
            return {
                'needs_ai_guidance': True,
                'needs_memory_context': True,
                'needs_personality': True,
                'needs_voice_style': True,
                'is_greeting': False,
                'is_simple_question': False,
                'confidence_scores': {},
                'detection_method': {}
            }

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
            logger.info("🎯 GENERATING: Sending %d messages to LLM", len(final_context))
            
            from src.llm.llm_client import LLMClient
            llm_client = LLMClient()
            
            response = await asyncio.to_thread(
                llm_client.get_chat_response, final_context
            )
            
            logger.info("✅ GENERATED: Response with %d characters", len(response))
            
            # 🎭 CDL EMOJI ENHANCEMENT: Add character-appropriate emojis to text response
            try:
                character_file = os.getenv("CDL_DEFAULT_CHARACTER")
                if character_file:
                    from src.intelligence.cdl_emoji_integration import create_cdl_emoji_integration
                    
                    cdl_emoji_integration = create_cdl_emoji_integration()
                    
                    # Extract just the filename if full path is provided
                    if "/" in character_file:
                        character_file = character_file.split("/")[-1]
                    
                    # Enhance response with CDL-appropriate emojis (ADDS to text, doesn't replace)
                    enhanced_response, emoji_metadata = cdl_emoji_integration.enhance_bot_response(
                        character_file=character_file,
                        user_id=message_context.user_id,
                        user_message=message_context.content,
                        bot_response=response,
                        context={
                            'emotional_context': ai_components.get('emotion_data'),
                            'conversation_history': conversation_context[:3] if conversation_context else []
                        }
                    )
                    
                    if emoji_metadata.get("cdl_emoji_applied", False):
                        response = enhanced_response
                        logger.info(f"🎭 CDL EMOJI: Enhanced response with {len(emoji_metadata.get('emoji_additions', []))} emojis "
                                  f"({emoji_metadata.get('placement_style', 'unknown')} style)")
                    else:
                        logger.debug(f"🎭 CDL EMOJI: No enhancement applied - {emoji_metadata.get('reason', 'unknown')}")
            except Exception as e:
                logger.error(f"CDL emoji enhancement failed (non-critical): {e}")
                # Continue with original response if CDL emoji enhancement fails
            
            return response
            
        except (ImportError, AttributeError, ValueError, TypeError) as e:
            logger.error("Response generation failed: %s", str(e))
            return "I apologize, but I'm having trouble generating a response right now. Please try again."

    async def _apply_cdl_character_enhancement(self, user_id: str, conversation_context: List[Dict[str, str]], 
                                             message_context: MessageContext, ai_components: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
        """
        🎭 SOPHISTICATED CDL CHARACTER INTEGRATION 🎭
        
        Apply sophisticated CDL character enhancement to conversation context with full AI pipeline integration.
        Restored from original events.py implementation with complete VectorAIPipelineResult creation.
        
        This injects character-aware prompts that combine:
        - CDL character personality, backstory, and voice
        - AI pipeline emotional analysis and memory networks  
        - Real-time conversation context and relationship dynamics
        - Context analysis insights from sophisticated AI processing
        - Phase 4 comprehensive context and human-like intelligence
        """
        try:
            import os
            logger.info("🎭 CDL CHARACTER DEBUG: Starting sophisticated enhancement for user %s", user_id)
            
            # Use CDL_DEFAULT_CHARACTER directly from environment - no dependency on CDL handler
            character_file = os.getenv("CDL_DEFAULT_CHARACTER")
            
            if not character_file:
                logger.info("🎭 CDL CHARACTER DEBUG: No CDL_DEFAULT_CHARACTER environment variable set")
                return None
            
            bot_name = os.getenv("DISCORD_BOT_NAME", "Unknown")
            logger.info("🎭 CDL CHARACTER: Using %s bot default character (%s) for user %s", 
                       bot_name, character_file, user_id)
            
            logger.info("🎭 CDL CHARACTER: User %s has active character: %s", user_id, character_file)
            
            # Import CDL integration modules
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineResult
            from datetime import datetime
            
            # 🚀 SOPHISTICATED PIPELINE RESULT CREATION: Map ALL AI components to VectorAIPipelineResult
            pipeline_result = VectorAIPipelineResult(
                user_id=user_id,
                message_content=message_context.content,
                timestamp=datetime.now(),
                # Map emotion data to emotional_state
                emotional_state=str(ai_components.get('external_emotion_data')) if ai_components.get('external_emotion_data') else str(ai_components.get('emotion_data')) if ai_components.get('emotion_data') else None,
                mood_assessment=ai_components.get('external_emotion_data') if isinstance(ai_components.get('external_emotion_data'), dict) else None,
                # Map personality data 
                personality_profile=ai_components.get('personality_context') if isinstance(ai_components.get('personality_context'), dict) else None,
                # Map phase4 data
                enhanced_context=ai_components.get('phase4_context') if isinstance(ai_components.get('phase4_context'), dict) else None
            )
            
            # 🎯 SOPHISTICATED CONTEXT ANALYSIS INTEGRATION: Add context analysis insights to pipeline result
            context_analysis = ai_components.get('context_analysis')
            if context_analysis and not isinstance(context_analysis, Exception):
                try:
                    # Convert context analysis to dict for pipeline compatibility
                    context_dict = {
                        'needs_ai_guidance': getattr(context_analysis, 'needs_ai_guidance', False),
                        'needs_memory_context': getattr(context_analysis, 'needs_memory_context', False),
                        'needs_personality': getattr(context_analysis, 'needs_personality', False),
                        'needs_voice_style': getattr(context_analysis, 'needs_voice_style', False),
                        'is_greeting': getattr(context_analysis, 'is_greeting', False),
                        'is_simple_question': getattr(context_analysis, 'is_simple_question', False),
                        'confidence_scores': getattr(context_analysis, 'confidence_scores', {}),
                    }
                    # Add to enhanced_context if available, otherwise create new field
                    if isinstance(pipeline_result.enhanced_context, dict):
                        pipeline_result.enhanced_context['context_analysis'] = context_dict
                    else:
                        pipeline_result.enhanced_context = {'context_analysis': context_dict}
                    
                    logger.info("🎯 CDL: Enhanced pipeline with context analysis insights")
                except Exception as e:
                    logger.debug(f"Failed to add context analysis to pipeline: {e}")
            
            # 🚀 COMPREHENSIVE CONTEXT INTEGRATION: Add all AI components to pipeline
            comprehensive_context = ai_components.get('comprehensive_context')
            if comprehensive_context and isinstance(comprehensive_context, dict):
                # Merge comprehensive context into pipeline enhanced_context
                if isinstance(pipeline_result.enhanced_context, dict):
                    pipeline_result.enhanced_context.update(comprehensive_context)
                else:
                    pipeline_result.enhanced_context = comprehensive_context.copy()
                
                logger.info("🎯 CDL: Enhanced pipeline with comprehensive context from sophisticated AI processing")
            
            # Use centralized character system if available, otherwise create new instance
            if self.bot_core and hasattr(self.bot_core, 'character_system'):
                cdl_integration = self.bot_core.character_system
                logger.info("🎭 CDL: Using centralized character system for %s", user_id)
            else:
                # Fallback: Create CDL integration instance
                cdl_integration = CDLAIPromptIntegration(
                    vector_memory_manager=self.memory_manager,
                    llm_client=self.llm_client
                )
                logger.warning("⚠️ CDL: Using fallback CDL instance for %s - character system not initialized", user_id)
            
            # Get user's display name for better identification
            user_display_name = message_context.metadata.get('discord_author_name') if message_context.metadata else None
            
            # 🚀 FULL INTELLIGENCE: Use complete character-aware prompt with all emotional intelligence
            character_prompt = await cdl_integration.create_unified_character_prompt(
                character_file=character_file,
                user_id=user_id,
                message_content=message_context.content,
                pipeline_result=pipeline_result,
                user_name=user_display_name
            )
            
            # 🚀 VECTOR-NATIVE ENHANCEMENT: Enhance character prompt with dynamic vector context
            try:
                from src.prompts.vector_native_prompt_manager import create_vector_native_prompt_manager
                
                # Create vector-native prompt manager
                vector_prompt_manager = create_vector_native_prompt_manager(
                    vector_memory_system=self.memory_manager,
                    personality_engine=None  # Reserved for future use
                )
                
                # Extract emotional context from pipeline for vector enhancement
                emotional_context = None
                if pipeline_result and hasattr(pipeline_result, 'emotional_state'):
                    emotional_context = pipeline_result.emotional_state
                
                # Enhance character prompt with vector-native context
                vector_enhanced_prompt = await vector_prompt_manager.create_contextualized_prompt(
                    base_prompt=character_prompt,
                    user_id=user_id,
                    current_message=message_context.content,
                    emotional_context=emotional_context
                )
                
                logger.info("🎯 VECTOR-NATIVE: Enhanced character prompt with dynamic context (%d chars)", len(vector_enhanced_prompt))
                character_prompt = vector_enhanced_prompt
                
            except ImportError as e:
                logger.debug("Vector-native prompt enhancement unavailable, using CDL-only: %s", e)
                # Continue with CDL-only character prompt
            
            # Clone the conversation context and replace/enhance system message
            enhanced_context = conversation_context.copy()
            
            # Find system message and replace with character-aware prompt
            system_message_found = False
            for i, msg in enumerate(enhanced_context):
                if msg.get('role') == 'system':
                    enhanced_context[i] = {
                        'role': 'system',
                        'content': character_prompt
                    }
                    system_message_found = True
                    logger.info("🎭 CDL CHARACTER: Replaced system message with character prompt (%d chars)", len(character_prompt))
                    break
            
            # If no system message found, add character prompt as first message
            if not system_message_found:
                enhanced_context.insert(0, {
                    'role': 'system', 
                    'content': character_prompt
                })
                logger.info("🎭 CDL CHARACTER: Added character prompt as new system message (%d chars)", len(character_prompt))
            
            logger.info("🎭 CDL CHARACTER: Enhanced conversation context with %s personality", character_file)
            return enhanced_context
            
        except Exception as e:
            logger.error("🎭 CDL CHARACTER ERROR: Failed to apply character enhancement: %s", e)
            logger.error("🎭 CDL CHARACTER ERROR: Falling back to original conversation context")
            return None
            try:
                from src.prompts.vector_native_prompt_manager import create_vector_native_prompt_manager
                
                # Create vector-native prompt manager
                vector_prompt_manager = create_vector_native_prompt_manager(
                    vector_memory_system=self.memory_manager,
                    personality_engine=None  # Reserved for future use
                )
                
                # Extract emotional context from pipeline for vector enhancement
                emotional_context = None
                if pipeline_result and hasattr(pipeline_result, 'emotional_state'):
                    emotional_context = pipeline_result.emotional_state
                
                # Enhance character prompt with vector-native context
                vector_enhanced_prompt = await vector_prompt_manager.create_contextualized_prompt(
                    base_prompt=character_prompt,
                    user_id=user_id,
                    current_message=message_context.content,
                    emotional_context=emotional_context
                )
                
                logger.info(f"🎯 VECTOR-NATIVE: Enhanced character prompt with dynamic context ({len(vector_enhanced_prompt)} chars)")
                character_prompt = vector_enhanced_prompt
                
            except Exception as e:
                logger.debug(f"Vector-native prompt enhancement unavailable, using CDL-only: {e}")
                # Continue with CDL-only character prompt
            
            # Clone the conversation context and replace/enhance system message
            enhanced_context = conversation_context.copy()
            
            # Find system message and replace with character-aware prompt
            system_message_found = False
            for i, msg in enumerate(enhanced_context):
                if msg.get('role') == 'system':
                    enhanced_context[i] = {
                        'role': 'system',
                        'content': character_prompt
                    }
                    system_message_found = True
                    logger.info(f"🎭 CDL CHARACTER: Replaced system message with character prompt ({len(character_prompt)} chars)")
                    break
            
            # If no system message found, add character prompt as first message
            if not system_message_found:
                enhanced_context.insert(0, {
                    'role': 'system', 
                    'content': character_prompt
                })
                logger.info(f"🎭 CDL CHARACTER: Added character prompt as new system message ({len(character_prompt)} chars)")
            
            logger.info(f"🎭 CDL CHARACTER: Enhanced conversation context with {character_file} personality")
            return enhanced_context
            
        except Exception as e:
            logger.error(f"🎭 CDL CHARACTER ERROR: Failed to apply character enhancement: {e}")
            logger.error(f"🎭 CDL CHARACTER ERROR: Falling back to original conversation context")
            return conversation_context

    async def _add_mixed_emotion_context(self, conversation_context: List[Dict[str, str]], 
                                       content: str, user_id: str, emotion_data, external_emotion_data) -> List[Dict[str, str]]:
        """Add emotion context to conversation."""
        # TODO: Implement emotion context enhancement
        logger.debug("Emotion context enhancement placeholder for user %s with content length %d", 
                    user_id, len(content))
        # Avoid unused parameter warnings by referencing them  
        _ = emotion_data, external_emotion_data
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
                logger.error("SECURITY: System message leakage detected in response to user %s", 
                           message_context.user_id)
                response = leakage_scan["sanitized_response"]
            
            # Meta-analysis sanitization
            response = self._sanitize_meta_analysis(response)
            
            return response
            
        except (ImportError, AttributeError, ValueError, TypeError) as e:
            logger.error("Response validation failed: %s", str(e))
            return response  # Return original if validation fails

    async def _validate_character_consistency(self, response: str, user_id: str, message_context: MessageContext) -> str:
        """Validate that response maintains character consistency."""
        # TODO: Implement character consistency validation
        logger.debug("Character consistency validation placeholder for user %s", user_id)
        # Avoid unused parameter warnings
        _ = message_context
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
            
        except (ValueError, TypeError) as e:
            logger.error("Meta-analysis sanitization failed: %s", str(e))
            return response

    async def _extract_and_store_knowledge(self, message_context: MessageContext, 
                                          ai_components: Dict[str, Any]) -> bool:
        """
        Extract factual knowledge from message and store in PostgreSQL knowledge graph.
        
        This is Phase 3 of the Semantic Knowledge Graph implementation:
        - Detects factual statements (preferences, facts about user)
        - Extracts entity information
        - Stores in PostgreSQL with automatic relationship discovery
        
        Args:
            message_context: The message context
            ai_components: AI processing results including emotion data
            
        Returns:
            True if knowledge was extracted and stored
        """
        # Check if knowledge router is available
        if not hasattr(self.bot_core, 'knowledge_router') or not self.bot_core.knowledge_router:
            return False
        
        try:
            content = message_context.content.lower()
            
            # Simple pattern-based factual detection for Phase 3
            # This will be enhanced with semantic analysis in future iterations
            factual_patterns = {
                # Food preferences
                'food_preference': [
                    ('love', 'likes'), ('like', 'likes'), ('enjoy', 'likes'),
                    ('favorite', 'likes'), ('prefer', 'likes'),
                    ('hate', 'dislikes'), ('dislike', 'dislikes'), ("don't like", 'dislikes')
                ],
                # Drink preferences  
                'drink_preference': [
                    ('love', 'likes'), ('like', 'likes'), ('enjoy', 'likes'),
                    ('favorite', 'likes'), ('prefer', 'likes'),
                    ('hate', 'dislikes'), ('dislike', 'dislikes'), ("don't like", 'dislikes')
                ],
                # Hobbies
                'hobby_preference': [
                    ('love', 'enjoys'), ('like', 'enjoys'), ('enjoy', 'enjoys'),
                    ('hobby', 'enjoys'), ('do for fun', 'enjoys')
                ],
                # Places visited
                'place_visited': [
                    ('visited', 'visited'), ('been to', 'visited'), ('went to', 'visited'),
                    ('traveled to', 'visited')
                ]
            }
            
            # Entity type keywords for classification
            entity_keywords = {
                'food': ['pizza', 'pasta', 'sushi', 'burger', 'taco', 'food', 'meal', 'dish', 'eat', 'eating'],
                'drink': ['beer', 'wine', 'coffee', 'tea', 'water', 'soda', 'juice', 'drink'],
                'hobby': ['hiking', 'reading', 'gaming', 'cooking', 'photography', 'music', 'hobby'],
                'place': ['city', 'country', 'beach', 'mountain', 'park', 'place', 'location']
            }
            
            detected_facts = []
            
            # Detect factual statements
            for event_type, patterns in factual_patterns.items():
                for pattern, relationship in patterns:
                    if pattern in content:
                        # Determine entity type based on keywords
                        entity_type = 'other'
                        for etype, keywords in entity_keywords.items():
                            if any(kw in content for kw in keywords):
                                entity_type = etype
                                break
                        
                        # Extract entity name (simplified - will be enhanced)
                        entity_name = self._extract_entity_from_content(content, pattern, entity_type)
                        
                        if entity_name:
                            detected_facts.append({
                                'entity_name': entity_name,
                                'entity_type': entity_type,
                                'relationship_type': relationship,
                                'confidence': 0.8,
                                'event_type': event_type
                            })
            
            # Store detected facts in PostgreSQL
            if detected_facts:
                bot_name = os.getenv('DISCORD_BOT_NAME', 'assistant').lower()
                emotion_data = ai_components.get('emotion_data', {})
                emotional_context = emotion_data.get('primary_emotion', 'neutral') if emotion_data else 'neutral'
                
                for fact in detected_facts:
                    stored = await self.bot_core.knowledge_router.store_user_fact(
                        user_id=message_context.user_id,
                        entity_name=fact['entity_name'],
                        entity_type=fact['entity_type'],
                        relationship_type=fact['relationship_type'],
                        confidence=fact['confidence'],
                        emotional_context=emotional_context,
                        mentioned_by_character=bot_name,
                        source_conversation_id=message_context.channel_id
                    )
                    
                    if stored:
                        logger.info(f"✅ KNOWLEDGE: Stored fact '{fact['entity_name']}' ({fact['entity_type']}) "
                                  f"for user {message_context.user_id}")
                
                return len(detected_facts) > 0
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Knowledge extraction failed: {e}")
            return False
    
    def _extract_entity_from_content(self, content: str, pattern: str, entity_type: str) -> Optional[str]:
        """
        Extract entity name from content based on pattern and entity type.
        
        Simple extraction for Phase 3 - will be enhanced with NLP in future.
        
        Args:
            content: User message content
            pattern: Detected pattern (e.g., "love", "like")
            entity_type: Type of entity (food, drink, hobby, place)
            
        Returns:
            Extracted entity name or None
        """
        try:
            # Find the pattern in content
            pattern_idx = content.find(pattern)
            if pattern_idx == -1:
                return None
            
            # Extract words after the pattern
            after_pattern = content[pattern_idx + len(pattern):].strip()
            
            # Remove common articles and prepositions
            articles = ['the', 'a', 'an', 'to', 'for', 'of']
            words = after_pattern.split()
            
            # Filter out articles and take first 1-3 meaningful words
            entity_words = []
            for word in words[:5]:  # Look at first 5 words
                clean_word = word.strip('.,!?;:')
                if clean_word and clean_word.lower() not in articles:
                    entity_words.append(clean_word)
                if len(entity_words) >= 3:  # Max 3 words for entity name
                    break
            
            if entity_words:
                entity_name = ' '.join(entity_words)
                # Basic cleanup
                entity_name = entity_name.strip('.,!?;:').lower()
                return entity_name if len(entity_name) > 1 else None
            
            return None
            
        except Exception as e:
            logger.debug(f"Entity extraction failed: {e}")
            return None

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
                logger.info("✅ MEMORY: Successfully stored and verified conversation for user %s", 
                           message_context.user_id)
                return True
            else:
                logger.warning("⚠️ MEMORY: Storage verification failed for user %s", message_context.user_id)
                return False
                
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Memory storage failed: %s", str(e))
            return False
    
    def _classify_message_context(self, message_context: MessageContext):
        """
        Platform-agnostic message context classification.
        
        Args:
            message_context: MessageContext object
            
        Returns:
            MemoryContext object with platform-agnostic classification
        """
        from src.memory.context_aware_memory_security import MemoryContext, MemoryContextType, ContextSecurity
        
        try:
            # Determine context type based on platform and channel type
            if message_context.platform == "api":
                # External API calls are treated as DM-like private contexts
                return MemoryContext(
                    context_type=MemoryContextType.DM,
                    server_id=None,
                    channel_id=getattr(message_context, 'channel_id', 'api_channel'),
                    is_private=True,
                    security_level=ContextSecurity.PRIVATE_DM,
                )
            elif message_context.platform == "discord":
                # Discord-specific classification
                if getattr(message_context, 'channel_type', 'dm') == 'dm':
                    return MemoryContext(
                        context_type=MemoryContextType.DM,
                        server_id=None,
                        channel_id=getattr(message_context, 'channel_id', 'unknown'),
                        is_private=True,
                        security_level=ContextSecurity.PRIVATE_DM,
                    )
                else:
                    # Guild/server context
                    return MemoryContext(
                        context_type=MemoryContextType.PUBLIC_CHANNEL,
                        server_id=getattr(message_context, 'server_id', None),
                        channel_id=getattr(message_context, 'channel_id', 'unknown'),
                        is_private=False,
                        security_level=ContextSecurity.PUBLIC_CHANNEL,
                    )
            else:
                # Unknown platform - default to private for security
                return MemoryContext(
                    context_type=MemoryContextType.DM,
                    server_id=None,
                    channel_id='unknown',
                    is_private=True,
                    security_level=ContextSecurity.PRIVATE_DM,
                )
                
        except Exception as e:
            logger.warning("Context classification failed: %s, using safe defaults", str(e))
            # Safe default - treat as private
            return MemoryContext(
                context_type=MemoryContextType.DM,
                server_id=None,
                channel_id='error',
                is_private=True,
                security_level=ContextSecurity.PRIVATE_DM,
            )


def create_message_processor(bot_core, memory_manager, llm_client, **kwargs) -> MessageProcessor:
    """Factory function to create a MessageProcessor instance."""
    return MessageProcessor(
        bot_core=bot_core,
        memory_manager=memory_manager, 
        llm_client=llm_client,
        **kwargs
    )