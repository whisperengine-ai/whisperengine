#!/usr/bin/env python3
"""
Native AI Service for WhisperEngine Desktop Applications
Provides a clean interface between native UIs and the AI core components.
"""

import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

# Import AI core components
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class AIMessage:
    """Structured AI message for native UIs"""

    content: str
    timestamp: datetime
    message_type: str = "text"  # text, system, error
    emotions: Optional[Dict] = None
    suggestions: Optional[List[str]] = None
    memory_updates: Optional[Dict] = None


@dataclass
class ConversationInfo:
    """Information about a conversation"""

    conversation_id: str
    title: str
    created_at: datetime
    last_active: datetime
    message_count: int = 0


class NativeAIService:
    """Platform-agnostic AI service for native desktop applications"""

    def __init__(self, user_id: Optional[str] = None):
        """Initialize the AI service with core components"""
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        # Use Discord-like user ID format for compatibility with memory system
        self.current_user_id = user_id or "123456789012345678"  # 18-digit Discord-like ID
        self.current_conversation_id = None

        # AI components (will be initialized)
        self.universal_chat = None
        self.enhanced_core = None
        self.memory_system = None
        self.config_manager = None

        # Threading for async operations
        self.event_loop = None
        self.loop_thread = None

        # Conversation management
        self.conversations: Dict[str, ConversationInfo] = {}

    async def initialize(self) -> bool:
        """Initialize AI components asynchronously"""
        try:
            self.logger.info("Initializing Native AI Service...")

            # Set environment mode to desktop for proper configuration
            import os

            os.environ["ENV_MODE"] = "desktop"

            # Load desktop environment configuration
            from env_manager import load_environment

            if not load_environment():
                self.logger.warning("Failed to load desktop environment, continuing with defaults")

            # Auto-configure optimal LLM backend (respects user overrides)
            try:
                from src.llm.smart_backend_selector import get_smart_backend_selector

                backend_selector = get_smart_backend_selector()

                # Check if user has configured their own settings
                user_config = backend_selector.has_user_configuration()
                if any(user_config.values()):
                    self.logger.info("🔧 Using user-configured LLM settings")
                else:
                    # Auto-configure optimal backend for desktop app
                    # Priority: 1) Local servers (Ollama/LM Studio), 2) Python APIs (MLX/llama-cpp-python)
                    if backend_selector.auto_configure_environment(respect_user_overrides=True):
                        effective_config = backend_selector.get_effective_configuration()
                        self.logger.info(
                            f"✅ Auto-configured LLM backend: {effective_config.get('backend_name', 'Unknown')}"
                        )
                    else:
                        self.logger.warning(
                            "⚠️ No suitable LLM backend found - may need manual configuration"
                        )

            except Exception as e:
                self.logger.warning(f"Failed to auto-configure LLM backend: {e}")
                self.logger.info("Continuing with manual/environment configuration...")

            # Import and initialize components
            from src.config.adaptive_config import AdaptiveConfigManager
            from src.database.database_integration import DatabaseIntegrationManager
            from src.platforms.universal_chat import UniversalChatOrchestrator

            # Create components (using direct orchestrator instead of web UI)
            self.config_manager = AdaptiveConfigManager()
            db_manager = DatabaseIntegrationManager(self.config_manager)

            # Create the Universal Chat Orchestrator directly
            self.universal_chat = UniversalChatOrchestrator(
                config_manager=self.config_manager,
                db_manager=db_manager,
                bot_core=None,
                use_enhanced_core=True,
            )

            # Initialize the orchestrator
            success = await self.universal_chat.initialize()
            if success:
                self.logger.info("✅ Universal Chat Orchestrator initialized")
            else:
                self.logger.warning("⚠️ Universal Chat Orchestrator initialization failed")

            # Get enhanced core if available
            if hasattr(self.universal_chat, "bot_core") and self.universal_chat.bot_core:
                # Get enhanced core from orchestrator if available
                if hasattr(self.universal_chat.bot_core, "enhanced_bot_core"):
                    self.enhanced_core = self.universal_chat.bot_core.enhanced_bot_core
                    self.logger.info("✅ Enhanced Bot Core initialized")
                else:
                    self.enhanced_core = self.universal_chat.bot_core
                    self.logger.info("✅ Standard Bot Core initialized")

            # Create a default conversation
            await self.create_new_conversation("Default Chat")

            self.is_initialized = True
            self.logger.info("🚀 Native AI Service fully initialized")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AI service: {e}")
            import traceback

            traceback.print_exc()
            return False

    def start_event_loop(self):
        """Start the async event loop in a separate thread"""

        def run_loop():
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)

            # Initialize AI components
            try:
                init_task = self.event_loop.create_task(self.initialize())
                self.event_loop.run_until_complete(init_task)

                # Keep loop running until stopped
                self.event_loop.run_forever()
            except Exception as e:
                self.logger.error(f"Event loop error: {e}")
            finally:
                self.event_loop.close()

        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()

        # Wait for initialization
        import time

        for _ in range(50):  # Wait up to 5 seconds
            if self.is_initialized:
                break
            time.sleep(0.1)

    def stop_event_loop(self):
        """Stop the async event loop"""
        if self.event_loop and not self.event_loop.is_closed():
            try:
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
                self.logger.info("AI service event loop stopped")
            except Exception as e:
                self.logger.warning(f"Error stopping event loop: {e}")

    async def process_message_async(
        self, message: str, conversation_id: Optional[str] = None
    ) -> AIMessage:
        """Process a message asynchronously"""
        try:
            if not self.is_initialized:
                return AIMessage(
                    content="AI service not initialized",
                    timestamp=datetime.now(),
                    message_type="error",
                )

            conversation_id = conversation_id or self.current_conversation_id

            # Create context for the message
            user_context = {
                "user_id": self.current_user_id,
                "conversation_id": conversation_id,
                "platform": "native_macos",
                "timestamp": datetime.now().isoformat(),
            }

            # Process through Universal Chat Orchestrator
            if self.universal_chat:
                # Create a Message object for the orchestrator
                from src.platforms.universal_chat import Message, MessageType, ChatPlatform
                import uuid

                message_obj = Message(
                    message_id=str(uuid.uuid4()),
                    user_id=self.current_user_id,
                    content=message,
                    message_type=MessageType.TEXT,
                    platform=ChatPlatform.WEB_UI,
                    channel_id=conversation_id or "native_chat",
                )

                # Use the handle_message method (but we need the response)
                # Let's use a different approach - call the AI generation directly
                conversation_context = self.universal_chat.build_conversation_context(
                    self.current_user_id, conversation_id or "native_chat", message
                )

                ai_response = await self.universal_chat.generate_ai_response(
                    message_obj, conversation_context
                )

                # Update conversation info
                if conversation_id in self.conversations:
                    conv = self.conversations[conversation_id]
                    conv.last_active = datetime.now()
                    conv.message_count += 2  # User message + AI response

                return AIMessage(
                    content=ai_response.content,
                    timestamp=datetime.now(),
                    message_type="text",
                    emotions=None,  # AIResponse doesn't have emotions field
                    suggestions=ai_response.suggestions,
                )

            else:
                # Fallback response
                return AIMessage(
                    content="I'm sorry, the AI core is not fully initialized yet. Please try again in a moment.",
                    timestamp=datetime.now(),
                    message_type="system",
                )

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return AIMessage(
                content=f"Error processing message: {str(e)}",
                timestamp=datetime.now(),
                message_type="error",
            )

    def process_message(self, message: str, conversation_id: Optional[str] = None) -> AIMessage:
        """Process a message synchronously (for native UI threads)"""
        if not self.event_loop:
            return AIMessage(
                content="AI service not started", timestamp=datetime.now(), message_type="error"
            )

        # Schedule async operation in the event loop
        future = asyncio.run_coroutine_threadsafe(
            self.process_message_async(message, conversation_id), self.event_loop
        )

        try:
            # Wait for result with timeout
            return future.result(timeout=30)
        except asyncio.TimeoutError:
            return AIMessage(
                content="Request timed out. Please try again.",
                timestamp=datetime.now(),
                message_type="error",
            )
        except Exception as e:
            return AIMessage(
                content=f"Error: {str(e)}", timestamp=datetime.now(), message_type="error"
            )

    async def create_new_conversation(self, title: Optional[str] = None) -> str:
        """Create a new conversation"""
        import uuid

        conversation_id = str(uuid.uuid4())

        if not title:
            title = f"Chat {len(self.conversations) + 1}"

        self.conversations[conversation_id] = ConversationInfo(
            conversation_id=conversation_id,
            title=title,
            created_at=datetime.now(),
            last_active=datetime.now(),
        )

        self.current_conversation_id = conversation_id
        self.logger.info(f"Created new conversation: {title}")
        return conversation_id

    def get_conversations(self) -> List[ConversationInfo]:
        """Get list of all conversations"""
        return list(self.conversations.values())

    def switch_conversation(self, conversation_id: str) -> bool:
        """Switch to a different conversation"""
        if conversation_id in self.conversations:
            self.current_conversation_id = conversation_id
            self.conversations[conversation_id].last_active = datetime.now()
            return True
        return False

    def get_conversation_history(self, conversation_id: Optional[str] = None) -> List[Dict]:
        """Get conversation history (placeholder for now)"""
        # This would integrate with the memory system
        # For now, return empty list
        return []


# Global instance for native apps
_native_ai_service = None


def get_native_ai_service() -> NativeAIService:
    """Get or create the global native AI service instance"""
    global _native_ai_service
    if _native_ai_service is None:
        _native_ai_service = NativeAIService()
    return _native_ai_service


def start_ai_service() -> NativeAIService:
    """Start the AI service for native applications"""
    service = get_native_ai_service()
    if not service.is_initialized:
        service.start_event_loop()
    return service
