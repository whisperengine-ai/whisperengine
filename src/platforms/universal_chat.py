"""
Universal Chat Platform Architecture for WhisperEngine
Abstracts conversation handling to support Discord, Slack, Teams, and other platforms.
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager
# Removed cost optimizer - not needed

# Import character definition system
try:
    from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
except ImportError:
    CDLAIPromptIntegration = None


class ChatPlatform(Enum):
    """Supported chat platforms"""

    DISCORD = "discord"
    SLACK = "slack"
    TEAMS = "teams"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    API = "api"
    CLI = "cli"


class MessageType(Enum):
    """Types of messages in the conversation"""

    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    COMMAND = "command"


@dataclass
class User:
    """Universal user representation"""

    user_id: str
    username: str
    display_name: str | None = None
    platform: ChatPlatform = ChatPlatform.DISCORD
    platform_user_id: str | None = None  # Platform-specific ID
    preferences: dict[str, Any] | None = None
    created_at: datetime | None = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Message:
    """Universal message representation"""

    message_id: str
    user_id: str
    content: str
    message_type: MessageType = MessageType.TEXT
    platform: ChatPlatform = ChatPlatform.DISCORD
    channel_id: str | None = None
    thread_id: str | None = None
    reply_to: str | None = None
    attachments: list[str] | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Conversation:
    """Universal conversation representation"""

    conversation_id: str
    user_id: str
    platform: ChatPlatform
    channel_id: str | None = None
    title: str | None = None
    messages: list[Message] | None = None
    created_at: datetime | None = None
    last_activity: datetime | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()


@dataclass
class AIResponse:
    """AI response with metadata"""

    content: str
    model_used: str
    tokens_used: int
    cost: float
    generation_time_ms: int
    confidence: float = 0.8
    sources: list[str] | None = None
    suggestions: list[str] | None = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.suggestions is None:
            self.suggestions = []


class AbstractChatAdapter(ABC):
    """Abstract base class for chat platform adapters"""

    def __init__(self, platform: ChatPlatform, config: dict[str, Any]):
        self.platform = platform
        self.config = config
        self.message_handlers: list[Callable] = []
        self.connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the chat platform"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the chat platform"""
        pass

    @abstractmethod
    async def send_message(self, user_id: str, content: str, channel_id: str | None = None) -> bool:
        """Send a message to the platform"""
        pass

    @abstractmethod
    async def get_user_info(self, user_id: str) -> User | None:
        """Get user information from the platform"""
        pass

    @abstractmethod
    async def get_conversation_history(
        self, conversation_id: str, limit: int = 50
    ) -> list[Message]:
        """Get conversation history"""
        pass

    def add_message_handler(self, handler: Callable):
        """Add a message handler"""
        self.message_handlers.append(handler)

    async def handle_message(self, message: Message):
        """Handle incoming message"""
        for handler in self.message_handlers:
            try:
                await handler(message)
            except Exception as e:
                logging.error(f"Message handler error: {e}")


class DiscordChatAdapter(AbstractChatAdapter):
    """Discord chat adapter for Discord bot integration"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(ChatPlatform.DISCORD, config)
        self.bot = None
        self.guild_cache = {}

    def set_bot_instance(self, bot):
        """Set the Discord bot instance for integration"""
        self.bot = bot

    async def connect(self) -> bool:
        """Connect to Discord (delegates to existing bot connection)"""
        try:
            # Discord connection is handled by the main bot instance
            # This adapter just provides message abstraction
            self.connected = True
            logging.info("Discord chat adapter connected")
            return True
        except Exception as e:
            logging.error(f"Failed to connect Discord chat adapter: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Discord"""
        if self.bot and hasattr(self.bot, "close") and callable(self.bot.close):
            try:
                await self.bot.close()
            except Exception as e:
                logging.warning(f"Error closing Discord bot: {e}")
        self.connected = False

    def discord_message_to_universal_message(self, discord_message) -> Message:
        """Convert Discord message to universal message format"""
        # Handle content - can be string or include attachments
        content = discord_message.content
        if discord_message.attachments:
            # Add attachment info to content
            attachment_info = []
            for attachment in discord_message.attachments:
                attachment_info.append(f"[Attachment: {attachment.filename}]")
            if content:
                content += "\n" + "\n".join(attachment_info)
            else:
                content = "\n".join(attachment_info)

        # Create User object
        user = User(
            user_id=str(discord_message.author.id),
            username=discord_message.author.name,
            display_name=discord_message.author.display_name,
            platform=ChatPlatform.DISCORD,
        )

        return Message(
            message_id=str(discord_message.id),
            user_id=str(discord_message.author.id),
            content=content,
            platform=ChatPlatform.DISCORD,
            channel_id=str(discord_message.channel.id),
            message_type=MessageType.TEXT,
            timestamp=discord_message.created_at,
            metadata={
                "user": user,
                "original_message": discord_message,  # Keep reference for Discord-specific operations
                "guild_id": str(discord_message.guild.id) if discord_message.guild else None,
                "username": discord_message.author.name,
                "display_name": discord_message.author.display_name,
            },
        )

    async def send_message(self, user_id: str, content: str, channel_id: str | None = None) -> bool:
        """Send Discord message"""
        try:
            if not self.bot:
                logging.error("Discord bot instance not set")
                return False

            if channel_id:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(content)
                    return True
            else:
                # Send DM
                user = self.bot.get_user(int(user_id))
                if user:
                    await user.send(content)
                    return True

            return False
        except Exception as e:
            logging.error(f"Failed to send Discord message: {e}")
            return False

    async def get_user_info(self, user_id: str) -> User | None:
        """Get Discord user info"""
        try:
            if not self.bot:
                return None

            discord_user = self.bot.get_user(int(user_id))
            if not discord_user:
                # Try fetching if not in cache
                discord_user = await self.bot.fetch_user(int(user_id))

            if discord_user:
                return User(
                    user_id=str(discord_user.id),
                    username=discord_user.name,
                    display_name=discord_user.display_name,
                    platform=ChatPlatform.DISCORD,
                )

            return None
        except Exception as e:
            logging.error(f"Failed to get Discord user info: {e}")
            return None

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 50
    ) -> list[Message]:
        """Get Discord conversation history"""
        try:
            if not self.bot:
                return []

            channel = self.bot.get_channel(int(conversation_id))
            if not channel:
                return []

            messages = []
            async for discord_msg in channel.history(limit=limit):
                universal_msg = self.discord_message_to_universal_message(discord_msg)
                messages.append(universal_msg)

            return list(reversed(messages))  # Return in chronological order
        except Exception as e:
            logging.error(f"Failed to get Discord conversation history: {e}")
            return []


class SlackChatAdapter(AbstractChatAdapter):
    """Slack chat adapter for enterprise integration"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(ChatPlatform.SLACK, config)
        self.slack_token = config.get("slack_token")

    async def connect(self) -> bool:
        """Connect to Slack"""
        try:
            # Implementation would use Slack SDK
            self.connected = True
            return True
        except Exception as e:
            logging.error(f"Failed to connect to Slack: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Slack"""
        self.connected = False

    async def send_message(self, user_id: str, content: str, channel_id: str | None = None) -> bool:
        """Send Slack message"""
        # Implementation would use Slack Web API
        return True

    async def get_user_info(self, user_id: str) -> User | None:
        """Get Slack user info"""
        # Implementation would use Slack API
        return None

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 50
    ) -> list[Message]:
        """Get Slack conversation history"""
        # Implementation would use Slack conversations API
        return []


class APIChatAdapter(AbstractChatAdapter):
    """REST API adapter for programmatic access"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(ChatPlatform.API, config)
        self.api_keys: dict[str, str] = config.get("api_keys", {})

    async def connect(self) -> bool:
        """API is always connected"""
        self.connected = True
        return True

    async def disconnect(self) -> None:
        """No connection to close for API"""
        self.connected = False

    async def send_message(self, user_id: str, content: str, channel_id: str | None = None) -> bool:
        """Store API response for retrieval"""
        # Implementation would store response in database or cache
        return True

    async def get_user_info(self, user_id: str) -> User | None:
        """Get API user info"""
        return User(
            user_id=user_id,
            username=f"api_user_{user_id}",
            platform=ChatPlatform.API,
            platform_user_id=user_id,
        )

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 50
    ) -> list[Message]:
        """Get API conversation history"""
        return []


class UniversalChatOrchestrator:
    """Main orchestrator that manages all chat platforms and AI responses"""

    def __init__(
        self,
        config_manager: AdaptiveConfigManager,
        db_manager: DatabaseIntegrationManager,
        bot_core=None,
        use_enhanced_core: bool = True,
    ):  # Add flag for enhanced core
        self.config_manager = config_manager
        self.db_manager = db_manager
        # Removed cost optimizer - not needed

        # Initialize enhanced bot core if requested and no bot_core provided
        if bot_core is None and use_enhanced_core:
            try:
                import os

                from src.core.enhanced_bot_core import create_enhanced_bot_core

                self.bot_core = create_enhanced_bot_core(
                    debug_mode=os.getenv("DEBUG", "false").lower() == "true",
                    use_datastore_factory=True,
                )
                logging.info(
                    "✅ Universal Chat using enhanced bot core with datastore abstractions"
                )
            except ImportError as e:
                logging.warning(
                    f"Enhanced bot core not available: {e}, falling back to standard core"
                )
                self.bot_core = bot_core
        else:
            self.bot_core = bot_core

        self.adapters: dict[ChatPlatform, AbstractChatAdapter] = {}
        self.active_conversations: dict[str, Conversation] = {}
        self.ai_engine = None  # Would integrate with existing AI system

        # Initialize character system
        self.character_system = None
        if CDLAIPromptIntegration:
            try:
                self.character_system = CDLAIPromptIntegration()
                logging.info("✅ Character Definition Language (CDL) system initialized")
            except Exception as e:
                logging.warning(f"Failed to initialize CDL character system: {e}")

        # Simple in-memory conversation history storage
        # Format: {user_id_channel_id: [{'user_message': str, 'assistant_response': str, 'timestamp': datetime}, ...]}
        self.conversation_history: dict[str, list[dict[str, Any]]] = {}

        # Load platform configurations
        self.platform_configs = self._load_platform_configs()

    def set_bot_core(self, bot_instance):
        """Set the bot instance to access command handlers for CDL character integration"""
        self.bot_core = bot_instance
        logging.info(f"🎭 UNIVERSAL CHAT: Bot core set, command handlers available: {list(getattr(bot_instance, 'command_handlers', {}).keys())}")

    def _load_platform_configs(self) -> dict[ChatPlatform, dict[str, Any]]:
        """Load platform-specific configurations"""
        return {
            ChatPlatform.DISCORD: {
                "enabled": self._is_discord_enabled(),
                "bot_token": self._get_env("DISCORD_BOT_TOKEN"),
                "max_guilds": 100,
            },
            ChatPlatform.SLACK: {
                "enabled": self._is_slack_enabled(),
                "bot_token": self._get_env("SLACK_BOT_TOKEN"),
                "signing_secret": self._get_env("SLACK_SIGNING_SECRET"),
            },
            ChatPlatform.API: {"enabled": True, "rate_limit": 1000, "auth_required": True},
        }

    def _is_discord_enabled(self) -> bool:
        """Check if Discord integration is enabled"""
        import os

        return bool(os.environ.get("DISCORD_BOT_TOKEN"))

    def _is_slack_enabled(self) -> bool:
        """Check if Slack integration is enabled"""
        import os

        return bool(os.environ.get("SLACK_BOT_TOKEN"))

    def _get_env(self, key: str) -> str | None:
        """Get environment variable"""
        import os

        return os.environ.get(key)

    def _is_error_response(self, response_text: str) -> bool:
        """
        Detect if the response appears to be an error message rather than actual AI response.
        
        Args:
            response_text: The response text to check
            
        Returns:
            True if this appears to be an error message
        """
        if not response_text or len(response_text.strip()) < 10:
            return False
            
        # Common error patterns from various LLM providers
        error_patterns = [
            # OpenAI/OpenRouter errors
            "context length exceeded",
            "request too large", 
            "invalid request",
            "model capacity exceeded",
            "rate limit exceeded",
            "quota exceeded",
            "timeout error",
            "service unavailable",
            "internal server error",
            "bad request",
            "unauthorized",
            "forbidden",
            "not found",
            "too many requests",
            
            # Generic API errors
            "error:",
            "exception:",
            "failed to",
            "unable to process",
            "request failed",
            "connection error",
            "network error",
            "api error",
            
            # Model-specific errors
            "maximum context length",
            "token limit",
            "input too long",
            "prompt too large",
            "sequence too long",
            
            # Short suspicious responses (likely errors)
            "null",
            "undefined",
            "none",
            "error",
            "fail",
            "{",  # JSON error fragments
            "}",
            "[",
            "]",
            "status:",
            "code:",
        ]
        
        response_lower = response_text.lower().strip()
        
        # Check for error patterns
        for pattern in error_patterns:
            if pattern in response_lower:
                return True
                
        # Check for suspiciously short responses that are likely errors
        # If response is very short and contains technical terms, it's likely an error
        if len(response_text.strip()) < 50:
            technical_terms = ["http", "json", "xml", "api", "server", "client", "request", "response"]
            if any(term in response_lower for term in technical_terms):
                return True
                
        return False

    async def initialize(self) -> bool:
        """Initialize all enabled chat platforms"""
        try:
            # Enable Discord if configured
            if self.platform_configs[ChatPlatform.DISCORD]["enabled"]:
                discord_adapter = DiscordChatAdapter(self.platform_configs[ChatPlatform.DISCORD])
                if await discord_adapter.connect():
                    discord_adapter.add_message_handler(self.handle_message)
                    self.adapters[ChatPlatform.DISCORD] = discord_adapter

            # Enable Slack if configured
            if self.platform_configs[ChatPlatform.SLACK]["enabled"]:
                slack_adapter = SlackChatAdapter(self.platform_configs[ChatPlatform.SLACK])
                if await slack_adapter.connect():
                    slack_adapter.add_message_handler(self.handle_message)
                    self.adapters[ChatPlatform.SLACK] = slack_adapter

            # Always enable API
            api_adapter = APIChatAdapter(self.platform_configs[ChatPlatform.API])
            await api_adapter.connect()
            api_adapter.add_message_handler(self.handle_message)
            self.adapters[ChatPlatform.API] = api_adapter

            logging.info(
                f"Initialized {len(self.adapters)} chat platform(s): {list(self.adapters.keys())}"
            )
            return True

        except Exception as e:
            logging.error(f"Failed to initialize chat platforms: {e}")
            return False

    async def handle_message(self, message: Message):
        """Handle incoming message from any platform"""
        try:
            # Build conversation context from stored conversation pairs (Discord model)
            conversation_context = self.build_conversation_context(
                message.user_id, message.channel_id or "direct", message.content
            )

            # Generate AI response using full context
            ai_response = await self.generate_ai_response(message, conversation_context)

            # Send response back to platform
            adapter = self.adapters.get(message.platform)
            if adapter:
                await adapter.send_message(message.user_id, ai_response.content, message.channel_id)

            # Store this conversation pair (user message + AI response)
            await self.store_conversation_pair(
                message.user_id,
                message.channel_id or "direct",
                message.content,
                ai_response.content,
            )

        except Exception as e:
            logging.error(f"Error handling message: {e}")

    async def get_or_create_conversation(self, message: Message) -> Conversation:
        """Get existing conversation or create new one"""
        conversation_id = (
            f"{message.platform.value}_{message.user_id}_{message.channel_id or 'direct'}"
        )

        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]

        # Try to load conversation from datastore
        conversation = await self._load_conversation_from_datastore(conversation_id, message)

        if conversation:
            self.active_conversations[conversation_id] = conversation
            return conversation

        # Create new conversation
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=message.user_id,
            platform=message.platform,
            channel_id=message.channel_id,
            title=f"Chat with {message.user_id}",
        )

        self.active_conversations[conversation_id] = conversation
        return conversation

    async def _load_conversation_from_datastore(
        self, conversation_id: str, message: Message
    ) -> Conversation | None:
        """Load conversation from datastore if available"""
        try:
            if self.bot_core and hasattr(self.bot_core, "conversation_cache"):
                conversation_cache = getattr(self.bot_core, "conversation_cache", None)

                if conversation_cache and hasattr(conversation_cache, "get_conversation"):
                    try:
                        cached_data = await conversation_cache.get_conversation(
                            message.user_id, conversation_id
                        )

                        if cached_data and "messages" in cached_data:
                            # Reconstruct conversation from cached data
                            conversation = Conversation(
                                conversation_id=conversation_id,
                                user_id=message.user_id,
                                platform=message.platform,
                                channel_id=message.channel_id,
                                title=f"Chat with {message.user_id}",
                            )

                            # Reconstruct messages
                            messages = []
                            for msg_data in cached_data["messages"]:
                                msg = Message(
                                    message_id=f"restored_{len(messages)}",
                                    user_id=msg_data.get("user_id", message.user_id),
                                    content=msg_data.get("content", ""),
                                    platform=message.platform,
                                    channel_id=message.channel_id,
                                    timestamp=datetime.fromisoformat(
                                        msg_data.get("timestamp", datetime.now().isoformat())
                                    ),
                                )
                                messages.append(msg)

                            conversation.messages = messages
                            conversation.last_activity = datetime.fromisoformat(
                                cached_data.get("last_activity", datetime.now().isoformat())
                            )

                            logging.info(
                                f"✅ Loaded conversation {conversation_id} with {len(messages)} messages from cache"
                            )
                            return conversation

                    except Exception as e:
                        logging.warning(f"Failed to load conversation from cache: {e}")

        except Exception as e:
            logging.warning(f"Error loading conversation from datastore: {e}")

        return None

    async def generate_ai_response(
        self, 
        message: Message, 
        conversation_context: list[dict[str, str]],
        phase3_context_switches=None,
        phase3_empathy_calibration=None
    ) -> AIResponse:
        """Generate AI response using conversation context with Phase 3 intelligence"""
        try:
            # Check if we have access to the full WhisperEngine AI framework
            if self.bot_core and hasattr(self.bot_core, "memory_manager"):
                return await self._generate_full_ai_response(
                    message, conversation_context, phase3_context_switches, phase3_empathy_calibration
                )
            else:
                # Use the character-enhanced conversation context passed in
                # Don't override with generic WhisperEngine prompt
                return await self._generate_basic_ai_response(message, conversation_context)

        except Exception as e:
            logging.error(f"Error generating AI response: {e}")

            # Check if this is a dependency issue
            error_str = str(e)
            if "requests" in error_str or "ModuleNotFoundError" in error_str:
                error_content = f"⚠️ Missing Dependencies: Cannot make LLM API calls. Install required packages: pip install requests aiohttp. Error: {error_str}"
                logging.warning("Universal Chat falling back due to missing dependencies")
            else:
                error_content = f"I apologize, but I encountered an error while processing your message. Please try again or check the system configuration. Error: {error_str}"

            # Fallback response with dependency guidance
            return AIResponse(
                content=error_content,
                model_used="fallback",
                tokens_used=20,
                cost=0.0,
                generation_time_ms=100,
                confidence=0.0,
            )

    async def _generate_full_ai_response(
        self, 
        message: Message, 
        conversation_context: list[dict[str, str]],
        phase3_context_switches=None,
        phase3_empathy_calibration=None
    ) -> AIResponse:
        """Generate AI response using the full WhisperEngine AI framework"""
        try:
            start_time = datetime.now()

            # Access the Discord bot's sophisticated AI components
            memory_manager = getattr(self.bot_core, "memory_manager", None)
            safe_memory_manager = getattr(self.bot_core, "safe_memory_manager", None)
            llm_client = getattr(self.bot_core, "llm_client", None)

            if not memory_manager or not llm_client:
                logging.warning(
                    "Full AI framework components not available, falling back to basic response"
                )
                return await self._generate_basic_ai_response(message, conversation_context)

            # Create a mock Discord-like message object for compatibility
            mock_discord_message = type(
                "MockMessage",
                (),
                {
                    "content": message.content,
                    "author": type(
                        "MockAuthor",
                        (),
                        {
                            "id": (
                                int(message.user_id)
                                if message.user_id.isdigit()
                                else hash(message.user_id)
                            ),
                            "name": f"web_user_{message.user_id[:8]}",
                            "display_name": "Web User",
                        },
                    )(),
                    "channel": type(
                        "MockChannel",
                        (),
                        {
                            "id": (
                                int(message.channel_id)
                                if message.channel_id and message.channel_id.isdigit()
                                else hash(message.channel_id or "web")
                            ),
                        },
                    )(),
                    "guild": None,  # Web UI doesn't have guilds
                    "attachments": [],
                },
            )()

            # 🔥 FIX: Use the conversation context passed from events.py (includes character enhancement)
            # DO NOT rebuild conversation_context - it already contains character-enhanced system prompts!
            logging.info(f"🎭 UNIVERSAL CHAT: Using passed conversation context ({len(conversation_context)} messages)")
            
            # Log the system message for debugging
            system_messages = [msg for msg in conversation_context if msg.get("role") == "system"]
            if system_messages:
                logging.info(f"🎭 UNIVERSAL CHAT: Found {len(system_messages)} system message(s)")
                for i, sys_msg in enumerate(system_messages):
                    content_preview = sys_msg.get("content", "")[:100]
                    logging.info(f"🎭 UNIVERSAL CHAT: System message {i+1} preview: {content_preview}...")
            else:
                logging.warning(f"🎭 UNIVERSAL CHAT: No system messages found in passed context!")
                
                # Only add fallback system prompt if NO system message exists
                template_context = {}
                if hasattr(memory_manager, "get_emotion_context"):
                    try:
                        template_context["emotional_intelligence"] = await memory_manager.get_emotion_context(
                            message.user_id
                        )
                    except Exception as e:
                        logging.debug(f"Could not get emotion context: {e}")
                
                system_prompt = await self._load_system_prompt(message.user_id, template_context)
                conversation_context.append({"role": "system", "content": system_prompt})

            # Use the Discord bot's memory classification
            message_context = None
            if hasattr(memory_manager, "classify_discord_context"):
                try:
                    message_context = memory_manager.classify_discord_context(mock_discord_message)
                except Exception as e:
                    logging.warning(f"Memory classification failed: {e}")

            # Retrieve relevant memories using the sophisticated memory system
            relevant_memories = []
            if hasattr(memory_manager, "retrieve_context_aware_memories"):
                try:
                    relevant_memories = await memory_manager.retrieve_context_aware_memories(
                        user_id=message.user_id, 
                        query=message.content, 
                        max_memories=10,
                        context=message_context
                    )
                except Exception as e:
                    logging.warning(f"Context-aware memory retrieval failed: {e}")

            # Get emotional context
            emotion_context = {}
            if hasattr(memory_manager, "get_emotion_context"):
                try:
                    emotion_context = await memory_manager.get_emotion_context(message.user_id)
                except Exception as e:
                    logging.warning(f"Emotion context retrieval failed: {e}")

            # Memory retrieval is handled by the vector memory system
            additional_memories = []

            # Apply Phase 4 Intelligence if available
            if hasattr(memory_manager, "process_with_phase4_intelligence"):
                try:
                    await memory_manager.process_with_phase4_intelligence(
                        message.user_id, message.content, relevant_memories, emotion_context
                    )
                except Exception as e:
                    logging.warning(f"Phase 4 intelligence processing failed: {e}")

            # Apply Phase 4.1: Memory-Triggered Personality Moments if available
            memory_moments_context = None
            if (
                hasattr(self.bot_core, "memory_moments")
                and self.bot_core
                and getattr(self.bot_core, "memory_moments", None) is not None
            ):
                try:
                    memory_moments = self.bot_core.memory_moments
                    # Discover memory connections for current conversation
                    # Build conversation_entry as required by _discover_memory_connections
                    conversation_entry = {
                        "timestamp": datetime.now(),
                        "context_id": getattr(message, "context_id", "universal_chat"),
                        "message": message.content,
                        "emotional_context": getattr(message, "emotional_context", None),
                        "keywords": memory_moments._extract_keywords(message.content) if hasattr(memory_moments, "_extract_keywords") else [],
                        "themes": memory_moments._identify_themes(message.content) if hasattr(memory_moments, "_identify_themes") else [],
                    }
                    memory_connections = await memory_moments._discover_memory_connections(
                        message.user_id,
                        conversation_entry
                    )

                    if memory_connections:
                        # Generate personality moments based on connections
                        personality_moments = await memory_moments.generate_personality_moments(
                            memory_connections, conversation_context={"messages": [message.content]}
                        )

                        if personality_moments:
                            # Apply the most appropriate moment
                            applied_moment = await memory_moments.apply_appropriate_moment(
                                personality_moments, {"messages": [message.content]}
                            )

                            if applied_moment:
                                memory_moments_context = {
                                    "moment": applied_moment,
                                    "connections": len(memory_connections),
                                    "prompt_guidance": applied_moment.get("prompt_guidance", ""),
                                }
                                logging.info(
                                    f"✅ Memory-triggered personality moment activated: {applied_moment.get('moment_type', 'unknown')}"
                                )

                except Exception as e:
                    logging.warning(f"Phase 4.1 memory moments processing failed: {e}")

            # Add memory context to conversation with relevance assessment
            if relevant_memories or additional_memories or emotion_context or memory_moments_context:
                context_parts = []
                
                # 🎯 MEMORY RELEVANCE ASSESSMENT
                memory_confidence = self._assess_memory_relevance(
                    message.content, relevant_memories, additional_memories
                )

                if relevant_memories:
                    context_parts.append("📚 **Relevant Memories:**")
                    for memory in relevant_memories[:3]:
                        context_parts.append(f"- {str(memory)}")

                if emotion_context:
                    context_parts.append(f"💭 **Emotional Context:** {str(emotion_context)}")

                    # Enhanced: Add emotional adaptation guidance if available
                    if (
                        hasattr(memory_manager, "emotion_manager")
                        and memory_manager.emotion_manager
                    ):
                        try:
                            # Get comprehensive emotional context from actual emotion manager
                            if (
                                hasattr(memory_manager.emotion_manager, "phase2_integration")
                                and memory_manager.emotion_manager.phase2_integration
                                and hasattr(
                                    memory_manager.emotion_manager.phase2_integration,
                                    "emotional_context_engine",
                                )
                            ):

                                # Use the actual emotional context engine with real data
                                emotional_context_engine = (
                                    memory_manager.emotion_manager.phase2_integration.emotional_context_engine
                                )
                                if emotional_context_engine:
                                    emotional_context_data = await emotional_context_engine.get_conversation_emotional_context(
                                        user_id=message.user_id, current_message=message.content
                                    )

                                    if emotional_context_data.get("recent_emotions"):
                                        recent_emotions = [
                                            e["emotion"]
                                            for e in emotional_context_data["recent_emotions"][-3:]
                                        ]
                                        context_parts.append(
                                            f"🎭 **Emotional Patterns:** Recent emotions: {', '.join(recent_emotions)}"
                                        )

                                    if emotional_context_data.get("cluster_insights"):
                                        patterns = [
                                            c["pattern"]
                                            for c in emotional_context_data["cluster_insights"][:2]
                                        ]
                                        context_parts.append(
                                            f"🔍 **Emotional Clusters:** Patterns: {', '.join(patterns)}"
                                        )

                                    if emotional_context_data.get("adaptation_prompt"):
                                        # Add adaptation guidance to system context
                                        context_parts.append(
                                            f"📋 **Adaptation Strategy:** {emotional_context_data['adaptation_prompt'][:200]}..."
                                        )
                                else:
                                    # Fallback to simple pattern detection
                                    user_profile = memory_manager.emotion_manager.get_profile(
                                        message.user_id
                                    )
                                    if user_profile and user_profile.emotion_history:
                                        recent_emotions = [
                                            e.detected_emotion.value
                                            for e in user_profile.emotion_history[-3:]
                                        ]
                                        if recent_emotions:
                                            context_parts.append(
                                                f"🎭 **Emotional Patterns:** Recent emotions: {', '.join(recent_emotions)}"
                                            )

                                            # Add adaptation guidance based on patterns
                                            if any(
                                                emotion in ["frustrated", "angry", "disappointed"]
                                                for emotion in recent_emotions
                                            ):
                                                context_parts.append(
                                                    "📋 **Adaptation Strategy:** Use supportive, calming tone. Acknowledge frustration and offer help."
                                                )
                                            elif any(
                                                emotion in ["excited", "happy", "grateful"]
                                                for emotion in recent_emotions
                                            ):
                                                context_parts.append(
                                                    "📋 **Adaptation Strategy:** Match positive energy while maintaining helpful focus."
                                                )
                                            elif any(
                                                emotion in ["worried", "sad"]
                                                for emotion in recent_emotions
                                            ):
                                                context_parts.append(
                                                    "📋 **Adaptation Strategy:** Provide gentle encouragement and emotional support."
                                                )
                            else:
                                # Fallback to simple pattern detection
                                user_profile = memory_manager.emotion_manager.get_profile(
                                    message.user_id
                                )
                                if user_profile and user_profile.emotion_history:
                                    recent_emotions = [
                                        e.detected_emotion.value
                                        for e in user_profile.emotion_history[-3:]
                                    ]
                                    if recent_emotions:
                                        context_parts.append(
                                            f"🎭 **Emotional Patterns:** Recent emotions: {', '.join(recent_emotions)}"
                                        )

                                        # Add adaptation guidance based on patterns
                                        if any(
                                            emotion in ["frustrated", "angry", "disappointed"]
                                            for emotion in recent_emotions
                                        ):
                                            context_parts.append(
                                                "📋 **Adaptation Strategy:** Use supportive, calming tone. Acknowledge frustration and offer help."
                                            )
                                        elif any(
                                            emotion in ["excited", "happy", "grateful"]
                                            for emotion in recent_emotions
                                        ):
                                            context_parts.append(
                                                "📋 **Adaptation Strategy:** Match positive energy while maintaining helpful focus."
                                            )
                                        elif any(
                                            emotion in ["worried", "sad"]
                                            for emotion in recent_emotions
                                        ):
                                            context_parts.append(
                                                "📋 **Adaptation Strategy:** Provide gentle encouragement and emotional support."
                                            )
                        except Exception as e:
                            logging.debug(f"Emotional adaptation enhancement failed: {e}")

                if additional_memories:
                    context_parts.append("🧠 **Additional Context:**")
                    
                    # Process additional memories 
                    for memory in additional_memories[:5]:  # Show more memories
                        memory_str = str(memory)
                        if (
                            "knowledge_domain" in str(memory).lower()
                            or "domain_specific" in str(memory).lower()
                        ):
                            domain_facts.append(memory_str)
                        else:
                            regular_memories.append(memory_str)

                    # Show regular memories
                    for memory in regular_memories[:2]:
                        context_parts.append(f"- {memory}")

                    # Show domain-specific knowledge if available
                    if domain_facts:
                        context_parts.append("🏷️ **Domain Knowledge:**")
                        for fact in domain_facts[:2]:
                            context_parts.append(f"- {fact}")

                # Add memory-triggered personality moments context
                if memory_moments_context:
                    context_parts.append("💭 **Memory-Triggered Personality Moment:**")
                    moment = memory_moments_context["moment"]
                    context_parts.append(f"- **Type:** {moment.get('moment_type', 'unknown')}")
                    context_parts.append(
                        f"- **Connections Found:** {memory_moments_context['connections']}"
                    )

                    if moment.get("prompt_guidance"):
                        context_parts.append(
                            f"- **Guidance:** {moment['prompt_guidance'][:150]}..."
                        )

                    if moment.get("trigger_memories"):
                        context_parts.append(
                            f"- **Triggered by:** {len(moment['trigger_memories'])} related memories"
                        )

                # Add Phase 3 intelligence context
                if phase3_context_switches or phase3_empathy_calibration:
                    context_parts.append("🧠 **Phase 3 Intelligence:**")
                    
                    if phase3_context_switches:
                        context_parts.append(f"- **Context Switches Detected:** {len(phase3_context_switches)} switches")
                        for switch in phase3_context_switches[:2]:  # Show top 2 switches
                            switch_type = switch.get('switch_type', 'unknown')
                            strength = switch.get('strength', 'unknown')
                            description = switch.get('description', 'no description')[:100]
                            context_parts.append(f"  - {switch_type} ({strength}): {description}")
                            
                            # Add adaptation strategy if available
                            if switch.get('adaptation_strategy'):
                                context_parts.append(f"    Strategy: {switch.get('adaptation_strategy')}")
                    
                    if phase3_empathy_calibration:
                        empathy_style = phase3_empathy_calibration.get('empathy_style', 'unknown')
                        confidence = phase3_empathy_calibration.get('confidence', 0.0)
                        context_parts.append(f"- **Empathy Calibration:** Style: {empathy_style}, Confidence: {confidence:.2f}")
                        
                        # Add empathy guidance if available
                        if phase3_empathy_calibration.get('guidance'):
                            guidance = phase3_empathy_calibration.get('guidance', '')[:150]
                            context_parts.append(f"  Guidance: {guidance}")
                        
                        # Add personalization factors if available
                        if phase3_empathy_calibration.get('personalization_factors'):
                            factors = phase3_empathy_calibration.get('personalization_factors', {})
                            if factors:
                                factor_list = [f"{k}: {v}" for k, v in list(factors.items())[:2]]
                                context_parts.append(f"  Personalization: {', '.join(factor_list)}")

                if context_parts:
                    # Include memory confidence assessment
                    confidence_guidance = self._get_confidence_guidance(memory_confidence)
                    context_message = "\n".join(context_parts)
                    
                    # Add confidence indicator to help with hallucination prevention
                    full_context = f"**Context for this conversation:**\n{context_message}\n\n{confidence_guidance}"
                    
                    conversation_context.append(
                        {
                            "role": "system",
                            "content": full_context,
                        }
                    )

            # Add current message to conversation context
            conversation_context.append({"role": "user", "content": message.content})

            # Generate response using the Discord bot's LLM client (run in thread to avoid blocking)
            response_data = await asyncio.to_thread(
                llm_client.generate_chat_completion, conversation_context
            )

            # Extract the response content if it's in OpenAI format
            if isinstance(response_data, dict) and "choices" in response_data:
                try:
                    response_text = response_data["choices"][0]["message"]["content"]
                    
                    # Check for common error patterns in the response
                    if response_text and self._is_error_response(response_text):
                        logging.error(f"Detected error response from LLM: {response_text}")
                        response_text = "I apologize, but I encountered an issue processing your request. Please try again with a shorter message."
                    elif not response_text:
                        logging.error(f"Empty content in LLM response: {response_data}")
                        response_text = "I apologize, but I'm having trouble generating a response right now. Please try again."
                except (KeyError, IndexError, TypeError) as e:
                    logging.error(f"Error extracting content from LLM response: {e}")
                    logging.error(f"Response structure: {response_data}")
                    response_text = "I apologize, but I'm having trouble processing my response. Please try again."
            else:
                # If response is already a string or unexpected format
                if isinstance(response_data, str):
                    response_text = response_data
                    # Check for error patterns in string responses too
                    if self._is_error_response(response_text):
                        logging.error(f"Detected error in string response: {response_text}")
                        response_text = "I apologize, but I encountered an issue processing your request. Please try again."
                else:
                    logging.error(f"Unexpected LLM response format: {type(response_data)} - {response_data}")
                    response_text = "I apologize, but I received an unexpected response format. Please try again."

            # Ensure we have a valid response
            if not response_text or not response_text.strip():
                logging.error("Final response_text is empty or whitespace-only")
                response_text = "I apologize, but I'm unable to generate a proper response right now. Please try again."
            
            # Note: Removed overly aggressive prompt-to-response size comparison
            # The _is_error_response() method above already handles actual error detection
            # Short responses to short user messages are perfectly normal and valid

            end_time = datetime.now()
            generation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Estimate tokens and cost
            estimated_tokens = len(response_text.split()) * 1.3
            estimated_cost = estimated_tokens * 0.00001

            logging.info(
                "✅ Generated full WhisperEngine AI response: %d chars, %dms", 
                len(response_text), generation_time_ms
            )

            return AIResponse(
                content=response_text,
                model_used="whisperengine_full_ai",
                tokens_used=int(estimated_tokens),
                cost=estimated_cost,
                generation_time_ms=generation_time_ms,
                confidence=0.95,  # Higher confidence for full AI system
            )

        except Exception as e:
            logging.error(f"Full AI response generation failed: {e}")
            import traceback

            traceback.print_exc()
            # Fall back to basic response
            return await self._generate_basic_ai_response(message, conversation_context)

    async def _load_system_prompt(
        self, user_id: str | None = None, template_context: dict | None = None
    ) -> str:
        """Load the system prompt using the proper config system with template contextualization"""
        
        logging.info(f"🎭 UNIVERSAL CHAT DEBUG: Loading system prompt for user {user_id}")
        
        # FIRST: Try to use character-aware prompt if character system is available
        if self.character_system and user_id:
            logging.info(f"🎭 UNIVERSAL CHAT DEBUG: Character system available, checking user character")
            try:
                # Check if user has an active character
                character_file = self._get_user_active_character(user_id)
                if not character_file:
                    # Fall back to environment-configured default character
                    default_character = os.getenv("CDL_DEFAULT_CHARACTER", "characters/default_assistant.json")
                    character_file = default_character
                    logging.info(f"🎭 UNIVERSAL CHAT: User {user_id} has no active character, using default CDL: {character_file}")
                else:
                    logging.info(f"🎭 UNIVERSAL CHAT: User {user_id} has active character: {character_file}")
                    
                character_prompt = await self.character_system.create_character_aware_prompt(
                    character_file=character_file,
                    user_id=user_id,
                    current_message=""  # No current message in this context
                )
                if character_prompt:
                    logging.info(f"✅ UNIVERSAL CHAT: Using character-aware prompt for user {user_id} ({len(character_prompt)} chars)")
                    logging.info(f"🎭 UNIVERSAL CHAT DEBUG: Character prompt preview: {character_prompt[:200]}...")
                    return character_prompt
            except Exception as e:
                logging.warning(f"Failed to generate character-aware prompt: {e}")
        else:
            if not self.character_system:
                logging.warning(f"🎭 UNIVERSAL CHAT DEBUG: No character system available")
            if not user_id:
                logging.warning(f"🎭 UNIVERSAL CHAT DEBUG: No user_id provided")
        
        # 🔥 CDL-ONLY: No fallback to legacy prompt system!
        logging.error(f"🎭 UNIVERSAL CHAT: CDL system failed for user {user_id} - system is CDL-only, no fallbacks!")
        raise RuntimeError(f"CDL character system is required but failed for user {user_id}. Check CDL_DEFAULT_CHARACTER configuration.")

    async def _generate_basic_ai_response(
        self, message: Message, conversation_context: list[dict[str, str]]
    ) -> AIResponse:
        """Generate AI response using existing WhisperEngine logic"""
        try:
            # Import LLM client
            from src.llm.llm_client import LLMClient

            # Initialize LLM client if not already done
            if not hasattr(self, "llm_client"):
                self.llm_client = LLMClient()

            # Use configured model from LLM client
            selected_model = None  # Will use default from LLM client

            # Use the provided conversation context (which includes history and current message)
            # Character-enhanced system prompts should already be included by events.py
            chat_messages = conversation_context.copy()

            # Generate response using actual LLM (run in thread to avoid blocking)
            start_time = datetime.now()
            response_text = await asyncio.to_thread(
                self.llm_client.get_chat_response, chat_messages
            )
            end_time = datetime.now()

            generation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Estimate tokens and cost (rough approximation)
            estimated_tokens = len(response_text.split()) * 1.3
            estimated_cost = estimated_tokens * 0.00001  # Rough cost estimate

            return AIResponse(
                content=response_text,
                model_used="openrouter/auto",  # Will use configured model
                tokens_used=int(estimated_tokens),
                cost=estimated_cost,
                generation_time_ms=generation_time_ms,
                confidence=0.85,
            )

        except Exception as e:
            logging.error(f"Error generating AI response: {e}")

            # Check if this is a dependency issue
            error_str = str(e)
            if "requests" in error_str or "ModuleNotFoundError" in error_str:
                error_content = f"⚠️ Missing Dependencies: Cannot make LLM API calls. Install required packages: pip install requests aiohttp. Error: {error_str}"
                logging.warning("Universal Chat falling back due to missing dependencies")
            else:
                error_content = f"I apologize, but I encountered an error while processing your message. Please try again or check the system configuration. Error: {error_str}"

            # Fallback response with dependency guidance
            return AIResponse(
                content=error_content,
                model_used="fallback",
                tokens_used=20,
                cost=0.0,
                generation_time_ms=100,
                confidence=0.0,
            )

    async def store_conversation(self, conversation: Conversation, ai_response: AIResponse):
        """Store conversation and AI response in database"""
        try:
            # Ensure conversation has messages list
            if conversation.messages is None:
                conversation.messages = []

            # Store conversation data using our datastore abstractions
            if self.bot_core and hasattr(self.bot_core, "memory_manager"):
                memory_manager = self.bot_core.memory_manager

                # Store the conversation in memory system if available
                if memory_manager and hasattr(memory_manager, "store_conversation"):
                    try:
                        # Store the last user message and AI response
                        last_user_message = None
                        for msg in reversed(conversation.messages):
                            if msg.user_id != "whisperengine_ai":
                                last_user_message = msg
                                break

                        if last_user_message:
                            await memory_manager.store_conversation(
                                conversation.user_id,
                                last_user_message.content,
                                ai_response.content,
                                metadata={
                                    "conversation_id": conversation.conversation_id,
                                    "platform": conversation.platform.value,
                                    "channel_id": conversation.channel_id,
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )
                    except Exception as e:
                        logging.warning(f"Failed to store in memory system: {e}")

                # Also try to store in conversation cache if available
                conversation_cache = getattr(self.bot_core, "conversation_cache", None)
                if conversation_cache and hasattr(conversation_cache, "store_conversation"):
                    try:
                        last_activity = conversation.last_activity or datetime.now()
                        await conversation_cache.store_conversation(
                            conversation.user_id,
                            conversation.conversation_id,
                            {
                                "messages": [
                                    {
                                        "user_id": msg.user_id,
                                        "content": msg.content,
                                        "timestamp": (
                                            msg.timestamp.isoformat()
                                            if msg.timestamp
                                            else datetime.now().isoformat()
                                        ),
                                    }
                                    for msg in conversation.messages[-10:]  # Store last 10 messages
                                ],
                                "last_activity": last_activity.isoformat(),
                            },
                        )
                    except Exception as e:
                        logging.warning(f"Failed to store in conversation cache: {e}")

            logging.info(
                f"✅ Stored conversation {conversation.conversation_id} with {len(conversation.messages)} messages"
            )

        except Exception as e:
            logging.error(f"Failed to store conversation: {e}")

    async def get_conversation_history(
        self, user_id: str, platform: ChatPlatform, limit: int = 50
    ) -> list[Message]:
        """Get conversation history for a user on a platform"""
        # Implementation would query database
        return []

    async def get_active_platforms(self) -> list[ChatPlatform]:
        """Get list of active chat platforms"""
        return list(self.adapters.keys())

    async def get_platform_stats(self) -> dict[str, Any]:
        """Get statistics for all platforms"""
        stats = {}
        for platform, adapter in self.adapters.items():
            stats[platform.value] = {
                "connected": adapter.connected,
                "message_handlers": len(adapter.message_handlers),
            }
        return stats

    def generate_conversation_id(self, user_id: str, platform_value: str, channel_id: str) -> str:
        """Generate consistent conversation ID across platforms"""
        return f"conversation_{user_id}_{platform_value}_{channel_id or 'direct'}"

    def build_conversation_context(
        self, user_id: str, channel_id: str, current_message: str
    ) -> list[dict[str, str]]:
        """Build conversation context from stored message pairs (Discord architecture)"""
        conversation_context = []

        try:
            # Add character-aware system prompt first (only if available)
            system_prompt = self._get_basic_system_prompt(user_id, current_message)
            if system_prompt:
                conversation_context.append({"role": "system", "content": system_prompt})
            else:
                logging.info(f"🎭 UNIVERSAL CHAT: No system prompt available - using existing context as-is")

            # Get recent conversation pairs for context
            recent_pairs = self._get_recent_conversation_pairs(user_id, channel_id, limit=5)

            # Add each pair to conversation context
            for pair in recent_pairs:
                conversation_context.append({"role": "user", "content": pair["user_message"]})
                conversation_context.append(
                    {"role": "assistant", "content": pair["assistant_response"]}
                )

            # Add current message
            conversation_context.append({"role": "user", "content": current_message})

            logging.info(
                f"Built conversation context: {len(conversation_context)} messages for user {user_id}"
            )
            return conversation_context

        except Exception as e:
            logging.error(f"Error building conversation context: {e}")
            # 🔥 NO FALLBACK CODE - Return minimal context without overriding character
            return [
                {"role": "user", "content": current_message},
            ]

    def _get_recent_conversation_pairs(
        self, user_id: str, channel_id: str, limit: int = 5
    ) -> list[dict[str, str]]:
        """Get recent conversation pairs from memory system (Discord architecture)"""
        try:
            # First try our simple in-memory storage (guaranteed to work)
            conversation_key = f"{user_id}_{channel_id}"
            if conversation_key in self.conversation_history:
                recent_entries = self.conversation_history[conversation_key][-limit:]
                pairs = []
                for entry in recent_entries:
                    pairs.append(
                        {
                            "user_message": entry["user_message"],
                            "assistant_response": entry["assistant_response"],
                        }
                    )
                if pairs:
                    logging.debug(
                        f"✅ Retrieved {len(pairs)} conversation pairs from memory for user {user_id}"
                    )
                    return pairs

            # Try to get from memory manager as fallback
            if self.bot_core and hasattr(self.bot_core, "memory_manager"):
                memory_manager = self.bot_core.memory_manager
                if memory_manager:  # Add null check
                    # Check for get_conversation_history method
                    if hasattr(memory_manager, "get_conversation_history"):
                        try:
                            # Use async call if available
                            if asyncio.iscoroutinefunction(memory_manager.get_conversation_history):
                                # Need to handle async in sync context - use current event loop if available
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        # Create a task for later execution
                                        conversations = []
                                    else:
                                        conversations = loop.run_until_complete(
                                            memory_manager.get_conversation_history(
                                                user_id, limit=limit
                                            )
                                        )
                                except RuntimeError:
                                    # No event loop, skip async call
                                    conversations = []
                            else:
                                conversations = memory_manager.get_conversation_history(
                                    user_id, limit=limit
                                )

                            pairs = []
                            for conv in conversations:
                                if isinstance(conv, dict):
                                    # Look for user_message and assistant_response or similar fields
                                    user_msg = (
                                        conv.get("user_message")
                                        or conv.get("message")
                                        or conv.get("content")
                                    )
                                    ai_response = (
                                        conv.get("assistant_response")
                                        or conv.get("response")
                                        or conv.get("ai_response")
                                    )

                                    if user_msg and ai_response:
                                        pairs.append(
                                            {
                                                "user_message": str(user_msg),
                                                "assistant_response": str(ai_response),
                                            }
                                        )
                            if pairs:
                                return pairs
                        except Exception as e:
                            logging.warning(f"Memory manager conversation retrieval failed: {e}")

            # Return empty if no data available - this is fine, just means no conversation history
            logging.debug(f"No conversation history found for user {user_id}, channel {channel_id}")
            return []

        except Exception as e:
            logging.error(f"Error getting recent conversation pairs: {e}")
            return []

    async def store_conversation_pair(
        self, user_id: str, channel_id: str, user_message: str, assistant_response: str
    ):
        """Store a conversation pair using Discord architecture"""
        try:
            # Store in simple in-memory storage first (guaranteed to work)
            conversation_key = f"{user_id}_{channel_id}"
            if conversation_key not in self.conversation_history:
                self.conversation_history[conversation_key] = []

            conversation_entry = {
                "user_message": user_message,
                "assistant_response": assistant_response,
                "timestamp": datetime.now(),
            }

            self.conversation_history[conversation_key].append(conversation_entry)

            # Keep only last 20 conversation pairs to manage memory
            if len(self.conversation_history[conversation_key]) > 20:
                self.conversation_history[conversation_key] = self.conversation_history[
                    conversation_key
                ][-20:]

            logging.debug(
                f"✅ Stored conversation pair in memory for user {user_id}, channel {channel_id}"
            )

            # Store using memory manager (primary method)
            if self.bot_core and hasattr(self.bot_core, "memory_manager"):
                memory_manager = self.bot_core.memory_manager
                if memory_manager and hasattr(memory_manager, "store_conversation"):
                    try:
                        # Check if it's an async method
                        if asyncio.iscoroutinefunction(memory_manager.store_conversation):
                            await memory_manager.store_conversation(
                                user_id,
                                user_message,
                                assistant_response,
                                metadata={
                                    "channel_id": channel_id,
                                    "platform": "universal_chat",
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )
                        else:
                            # Sync method
                            memory_manager.store_conversation(
                                user_id,
                                user_message,
                                assistant_response,
                                metadata={
                                    "channel_id": channel_id,
                                    "platform": "universal_chat",
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )
                        logging.info(
                            f"✅ Stored conversation pair in memory manager for user {user_id}"
                        )
                    except Exception as e:
                        logging.warning(f"Memory manager storage failed: {e}")

            # Store using safe memory manager as fallback
            if self.bot_core and hasattr(self.bot_core, "safe_memory_manager"):
                safe_memory_manager = self.bot_core.safe_memory_manager
                if safe_memory_manager and hasattr(safe_memory_manager, "store_conversation"):
                    try:
                        if asyncio.iscoroutinefunction(safe_memory_manager.store_conversation):
                            await safe_memory_manager.store_conversation(
                                user_id,
                                user_message,
                                assistant_response,
                                metadata={
                                    "channel_id": channel_id,
                                    "platform": "universal_chat",
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )
                        else:
                            safe_memory_manager.store_conversation(
                                user_id,
                                user_message,
                                assistant_response,
                                metadata={
                                    "channel_id": channel_id,
                                    "platform": "universal_chat",
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )
                        logging.info(
                            f"✅ Stored conversation pair in safe memory manager for user {user_id}"
                        )
                    except Exception as e:
                        logging.warning(f"Safe memory manager storage failed: {e}")

        except Exception as e:
            logging.error(f"Error storing conversation pair: {e}")
            # Don't fail the whole conversation if storage fails
            pass

    def _get_user_active_character(self, user_id: str) -> str | None:
        """Get user's active character file if available"""
        try:
            logging.info(f"🎭 UNIVERSAL CHAT DEBUG: Checking active character for user {user_id}")
            # Access the bot's CDL command handler to check active character
            if (hasattr(self.bot_core, 'command_handlers') and 
                'cdl_test' in getattr(self.bot_core, 'command_handlers', {})):
                
                cdl_handler = self.bot_core.command_handlers['cdl_test']
                character_file = cdl_handler.get_user_character(user_id)
                logging.info(f"🎭 UNIVERSAL CHAT DEBUG: User {user_id} active character: {character_file}")
                return character_file
            else:
                logging.warning(f"🎭 UNIVERSAL CHAT DEBUG: CDL handler not found in bot_core.command_handlers")
                logging.info(f"🎭 UNIVERSAL CHAT DEBUG: Available handlers: {list(getattr(self.bot_core, 'command_handlers', {}).keys())}")
        except Exception as e:
            logging.warning(f"Failed to get user active character: {e}")
        return None

    def _get_basic_system_prompt(self, user_id: str = None, current_message: str = "") -> str:
        """Get system prompt - character-aware if CDL system is available"""
        
        logging.info(f"🎭 UNIVERSAL CHAT DEBUG: Getting system prompt for user {user_id}")
        
        # Try to use character-aware prompt if character system is available
        if self.character_system and user_id:
            logging.info(f"🎭 UNIVERSAL CHAT DEBUG: Character system available, checking user character")
            try:
                # Check if user has an active character
                character_file = self._get_user_active_character(user_id)
                if not character_file:
                    # Fall back to environment-configured default character
                    default_character = os.getenv("CDL_DEFAULT_CHARACTER", "characters/default_assistant.json")
                    character_file = default_character
                    logging.info(f"🎭 UNIVERSAL CHAT: User {user_id} has no active character, using default: {character_file}")
                else:
                    logging.info(f"🎭 UNIVERSAL CHAT: User {user_id} has active character: {character_file}")
                
                character_prompt = asyncio.run(
                    self.character_system.create_character_aware_prompt(
                        character_file=character_file,
                        user_id=user_id,
                        current_message=current_message
                    )
                )
                if character_prompt:
                    logging.info(f"✅ UNIVERSAL CHAT: Using character-aware prompt for user {user_id} ({len(character_prompt)} chars)")
                    logging.info(f"🎭 UNIVERSAL CHAT DEBUG: Character prompt preview: {character_prompt[:200]}...")
                    return character_prompt
            except Exception as e:
                logging.warning(f"Failed to generate character-aware prompt: {e}")
        else:
            if not self.character_system:
                logging.warning(f"🎭 UNIVERSAL CHAT DEBUG: No character system available")
            if not user_id:
                logging.warning(f"🎭 UNIVERSAL CHAT DEBUG: No user_id provided")
        
        # 🔥 CDL-ONLY: No fallback to legacy prompt system!
        logging.error(f"🎭 UNIVERSAL CHAT: CDL system failed for user {user_id} - system is CDL-only, no fallbacks!")
        raise RuntimeError(f"CDL character system is required but failed for user {user_id}. Check CDL_DEFAULT_CHARACTER configuration.")

    async def cleanup(self):
        """Cleanup all platform connections"""
        for adapter in self.adapters.values():
            await adapter.disconnect()
        self.adapters.clear()
        self.active_conversations.clear()


# Factory function
    def _is_error_response(self, response_text: str) -> bool:
        """Check if the response indicates an error"""
        error_indicators = [
            "error occurred",
            "failed to",
            "unable to",
            "something went wrong",
            "try again",
            "internal error",
        ]
        response_lower = response_text.lower()
        return any(indicator in response_lower for indicator in error_indicators)

    def _assess_memory_relevance(self, query: str, relevant_memories: list, additional_memories: list) -> dict:
        """
        🎯 HALLUCINATION PREVENTION: Assess if memories contain relevant information
        
        Returns confidence assessment for guiding LLM responses
        """
        query_lower = query.lower()
        logging.info(f"🔍 ANTI-HALLUCINATION: Assessing memory relevance for query: '{query}'")
        
        # 🔥 CONVERSATIONAL CONTEXT DETECTION: Check if this is a conversational response vs fact-seeking query
        conversational_indicators = [
            'haha', 'lol', 'yeah', 'maybe', 'perhaps', 'i guess', 'not sure', 'dunno',
            'ok', 'alright', 'sure', 'yep', 'nope', 'hmm', 'oh', 'ah', 'well',
            'right', 'exactly', 'true', 'definitely', 'absolutely', 'kinda', 'sorta'
        ]
        
        is_conversational_response = any(indicator in query_lower for indicator in conversational_indicators)
        is_short_response = len(query.split()) <= 6  # Short responses are usually conversational
        
        if is_conversational_response or is_short_response:
            logging.info(f"🔍 ANTI-HALLUCINATION: CONVERSATIONAL RESPONSE detected - using high confidence")
            return {
                'has_relevant_info': True,
                'confidence': 0.9,  # High confidence for conversational flow
                'query_type': ['conversational_response'],
                'memory_count': len((relevant_memories or []) + (additional_memories or []))
            }
        
        # Extract key query terms for fact-seeking questions
        query_keywords = set()
        if any(word in query_lower for word in ['pet', 'pets', 'cat', 'dog', 'animal']):
            query_keywords.add('pets')
        if any(word in query_lower for word in ['remember', 'recall', 'told', 'mentioned']):
            query_keywords.add('memory_check')
        if any(word in query_lower for word in ['name', 'named', 'called']):
            query_keywords.add('names')
            
        logging.info(f"🔍 ANTI-HALLUCINATION: Query keywords: {query_keywords}")
        logging.info(f"🔍 ANTI-HALLUCINATION: Memory counts - relevant: {len(relevant_memories)}, additional: {len(additional_memories)}")
        
        # Assess memory content relevance
        memory_contains_info = False
        memory_confidence = 0.0
        
        all_memories = (relevant_memories or []) + (additional_memories or [])
        
        for memory in all_memories:
            memory_str = str(memory).lower()
            logging.debug(f"🔍 ANTI-HALLUCINATION: Checking memory: {memory_str[:100]}...")
            
            # Check if memory contains relevant information
            if 'pets' in query_keywords:
                if any(word in memory_str for word in ['pet', 'cat', 'dog', 'animal', 'luna', 'max']):
                    memory_contains_info = True
                    memory_confidence += 0.3
                    logging.info(f"🔍 ANTI-HALLUCINATION: Found pet-related content in memory")
            
            if 'names' in query_keywords:
                # Look for actual names/proper nouns in memory
                if any(word in memory_str for word in ['named', 'called', 'name is']):
                    memory_contains_info = True
                    memory_confidence += 0.4
                    logging.info(f"🔍 ANTI-HALLUCINATION: Found name-related content in memory")
        
        memory_confidence = min(memory_confidence, 1.0)
        
        assessment_result = {
            'has_relevant_info': memory_contains_info,
            'confidence': memory_confidence,
            'query_type': list(query_keywords),
            'memory_count': len(all_memories)
        }
        
        logging.info(f"🔍 ANTI-HALLUCINATION: Memory assessment result: {assessment_result}")
        return assessment_result

    def _get_confidence_guidance(self, memory_assessment: dict) -> str:
        """
        🎯 HALLUCINATION PREVENTION: Provide guidance based on memory confidence
        """
        logging.info(f"🔍 ANTI-HALLUCINATION: Generating confidence guidance for assessment: {memory_assessment}")
        
        if not memory_assessment['has_relevant_info'] or memory_assessment['confidence'] < 0.3:
            guidance = (
                "⚠️ **IMPORTANT MEMORY GUIDANCE:** "
                "The retrieved memories do not contain specific information relevant to this question. "
                "You should respond honestly that you don't have this information in your memory. "
                "Do NOT fabricate details, names, or facts not found in the actual memory content above."
            )
            logging.info(f"🔍 ANTI-HALLUCINATION: Generated LOW confidence guidance")
            return guidance
        elif memory_assessment['confidence'] < 0.7:
            guidance = (
                "ℹ️ **MEMORY CONFIDENCE:** "
                "Limited relevant information found in memories. "
                "Base your response only on the specific details provided in the memory content above. "
                "If asked for details not in the memories, be honest about not having that information."
            )
            logging.info(f"🔍 ANTI-HALLUCINATION: Generated MEDIUM confidence guidance")
            return guidance
        else:
            guidance = (
                "✅ **MEMORY CONFIDENCE:** "
                "Good relevant information found in memories. "
                "You can confidently respond based on the memory content provided above."
            )
            logging.info(f"🔍 ANTI-HALLUCINATION: Generated HIGH confidence guidance")
            return guidance


def create_universal_chat_platform(
    config_manager: AdaptiveConfigManager | None = None,
    db_manager: DatabaseIntegrationManager | None = None,
) -> UniversalChatOrchestrator:
    """Factory function to create universal chat platform"""
    if config_manager is None:
        config_manager = AdaptiveConfigManager()
    if db_manager is None:
        db_manager = DatabaseIntegrationManager(config_manager)

    return UniversalChatOrchestrator(config_manager, db_manager)


# Example usage
async def main():
    """Example usage of universal chat platform"""
    # Create platform
    chat_platform = create_universal_chat_platform()

    try:
        # Initialize all platforms
        if await chat_platform.initialize():

            # Show active platforms
            await chat_platform.get_active_platforms()

            # Show platform stats
            await chat_platform.get_platform_stats()

        else:
            pass

    finally:
        await chat_platform.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
