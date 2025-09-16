"""
Universal Chat Platform Architecture for WhisperEngine
Abstracts conversation handling to support web UI, Discord, Slack, Teams, and other platforms.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager
from src.optimization.cost_optimizer import CostOptimizationEngine, RequestContext


class ChatPlatform(Enum):
    """Supported chat platforms"""

    WEB_UI = "web_ui"
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
    platform: ChatPlatform = ChatPlatform.WEB_UI
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
    platform: ChatPlatform = ChatPlatform.WEB_UI
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
    async def send_message(
        self, user_id: str, content: str, channel_id: str | None = None
    ) -> bool:
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


class WebUIChatAdapter(AbstractChatAdapter):
    """Web UI chat adapter for standalone usage"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(ChatPlatform.WEB_UI, config)
        self.active_sessions: dict[str, dict[str, Any]] = {}

    async def connect(self) -> bool:
        """Web UI is always connected"""
        self.connected = True
        return True

    async def disconnect(self) -> None:
        """Cleanup web UI sessions"""
        self.active_sessions.clear()
        self.connected = False

    async def send_message(
        self, user_id: str, content: str, channel_id: str | None = None
    ) -> bool:
        """Send message via WebSocket or store for retrieval"""
        try:
            session_id = channel_id or f"web_{user_id}"

            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    "user_id": user_id,
                    "messages": [],
                    "websocket": None,
                }

            # Store message for web UI retrieval
            message = {
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "type": "ai_response",
            }

            self.active_sessions[session_id]["messages"].append(message)

            # Send via WebSocket if connected
            websocket = self.active_sessions[session_id].get("websocket")
            if websocket:
                await websocket.send_text(json.dumps(message))

            return True
        except Exception as e:
            logging.error(f"Failed to send web UI message: {e}")
            return False

    async def get_user_info(self, user_id: str) -> User | None:
        """Create web UI user info"""
        return User(
            user_id=user_id,
            username=f"web_user_{user_id[:8]}",
            display_name="Web User",
            platform=ChatPlatform.WEB_UI,
            platform_user_id=user_id,
        )

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 50
    ) -> list[Message]:
        """Get web UI conversation history"""
        # This would typically come from the database
        return []

    def register_websocket(self, session_id: str, websocket):
        """Register WebSocket for real-time messaging"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["websocket"] = websocket

    def get_session_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Get messages for a web session"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]["messages"]
        return []


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

    async def send_message(
        self, user_id: str, content: str, channel_id: str | None = None
    ) -> bool:
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

    async def send_message(
        self, user_id: str, content: str, channel_id: str | None = None
    ) -> bool:
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

    async def send_message(
        self, user_id: str, content: str, channel_id: str | None = None
    ) -> bool:
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
        self.cost_optimizer = CostOptimizationEngine(db_manager)

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

        # Simple in-memory conversation history storage
        # Format: {user_id_channel_id: [{'user_message': str, 'assistant_response': str, 'timestamp': datetime}, ...]}
        self.conversation_history: dict[str, list[dict[str, Any]]] = {}

        # Load platform configurations
        self.platform_configs = self._load_platform_configs()

    def _load_platform_configs(self) -> dict[ChatPlatform, dict[str, Any]]:
        """Load platform-specific configurations"""
        return {
            ChatPlatform.WEB_UI: {"enabled": True, "max_sessions": 1000, "session_timeout": 3600},
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

    async def initialize(self) -> bool:
        """Initialize all enabled chat platforms"""
        try:
            # Always enable Web UI
            web_adapter = WebUIChatAdapter(self.platform_configs[ChatPlatform.WEB_UI])
            await web_adapter.connect()
            web_adapter.add_message_handler(self.handle_message)
            self.adapters[ChatPlatform.WEB_UI] = web_adapter

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
        self, message: Message, conversation_context: list[dict[str, str]]
    ) -> AIResponse:
        """Generate AI response using conversation context (Discord model)"""
        try:
            # Check if we have access to the full WhisperEngine AI framework
            if self.bot_core and hasattr(self.bot_core, "memory_manager"):
                return await self._generate_full_ai_response(message, conversation_context)
            else:
                # Create basic conversation context for fallback
                basic_context = [
                    {
                        "role": "system",
                        "content": "You are WhisperEngine, an advanced AI assistant. Be helpful and engaging.",
                    },
                    {"role": "user", "content": message.content},
                ]
                return await self._generate_basic_ai_response(message, basic_context)

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
        self, message: Message, conversation_context: list[dict[str, str]]
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

            # Build conversation context like the Discord bot does
            conversation_context = []

            # Build template context data from available sources
            template_context = {}
            if hasattr(memory_manager, "get_emotion_context"):
                try:
                    template_context["emotional_intelligence"] = memory_manager.get_emotion_context(
                        message.user_id
                    )
                except Exception as e:
                    logging.debug(f"Could not get emotion context: {e}")

            # Add system prompt using proper config system with full template contextualization
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
                    relevant_memories = memory_manager.retrieve_context_aware_memories(
                        message.user_id, message.content, context=message_context
                    )
                except Exception as e:
                    logging.warning(f"Context-aware memory retrieval failed: {e}")

            # Get emotional context
            emotion_context = {}
            if hasattr(memory_manager, "get_emotion_context"):
                try:
                    emotion_context = memory_manager.get_emotion_context(message.user_id)
                except Exception as e:
                    logging.warning(f"Emotion context retrieval failed: {e}")

            # Use ChromaDB for additional memory retrieval
            chromadb_memories = []
            if safe_memory_manager and hasattr(safe_memory_manager, "retrieve_relevant_memories"):
                try:
                    chromadb_memories = safe_memory_manager.retrieve_relevant_memories(
                        message.user_id, message.content, limit=5
                    )

                    # Enhanced: Add knowledge domain classification
                    if hasattr(memory_manager, "_determine_knowledge_domain"):
                        try:
                            domain = memory_manager._determine_knowledge_domain(message.content, "")
                            if domain and domain != "general":
                                # Get domain-specific facts if graph database is available
                                if (
                                    hasattr(memory_manager, "get_knowledge_domain_facts")
                                    and hasattr(memory_manager, "enable_global_facts")
                                    and memory_manager.enable_global_facts
                                ):
                                    domain_facts = memory_manager.get_knowledge_domain_facts(
                                        domain, limit=3
                                    )
                                    if domain_facts:
                                        chromadb_memories.extend(domain_facts)
                                        logging.debug(
                                            f"Added {len(domain_facts)} domain-specific facts for {domain}"
                                        )
                        except Exception as e:
                            logging.debug(f"Knowledge domain enhancement failed: {e}")

                except Exception as e:
                    logging.warning(f"ChromaDB memory retrieval failed: {e}")

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
                    memory_connections = await memory_moments.discover_memory_connections(
                        user_id=message.user_id,
                        current_message=message.content,
                        conversation_context=relevant_memories,
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

            # Add memory context to conversation
            if relevant_memories or chromadb_memories or emotion_context or memory_moments_context:
                context_parts = []

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

                if chromadb_memories:
                    context_parts.append("🧠 **Memory Networks:**")
                    regular_memories = []
                    domain_facts = []

                    # Separate regular memories from domain-specific facts
                    for memory in chromadb_memories[:5]:  # Show more memories
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

                if context_parts:
                    context_message = "\n".join(context_parts)
                    conversation_context.append(
                        {
                            "role": "system",
                            "content": f"**Context for this conversation:**\n{context_message}",
                        }
                    )

            # Add current message to conversation context
            conversation_context.append({"role": "user", "content": message.content})

            # Generate response using the Discord bot's LLM client (run in thread to avoid blocking)
            response_text = await asyncio.to_thread(
                llm_client.generate_chat_completion, conversation_context
            )

            # Extract the response content if it's in OpenAI format
            if isinstance(response_text, dict) and "choices" in response_text:
                response_text = response_text["choices"][0]["message"]["content"]

            end_time = datetime.now()
            generation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Estimate tokens and cost
            estimated_tokens = len(response_text.split()) * 1.3
            estimated_cost = estimated_tokens * 0.00001

            logging.info(
                f"✅ Generated full WhisperEngine AI response: {len(response_text)} chars, {generation_time_ms}ms"
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
        try:
            from src.core.config import load_system_prompt

            content = load_system_prompt()
        except Exception as e:
            logging.warning(f"Could not load system prompt via config: {e}")
            # Try fallback to prompts/default.md
            try:
                import os

                prompt_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "prompts", "default.md"
                )
                if os.path.exists(prompt_path):
                    with open(prompt_path, encoding="utf-8") as f:
                        content = f.read()
                        # Replace {BOT_NAME} placeholder if present
                        bot_name = os.getenv("DISCORD_BOT_NAME", "AI Assistant")
                        content = content.replace("{BOT_NAME}", bot_name)
                else:
                    content = None
            except Exception as e2:
                logging.warning(f"Could not load system prompt file: {e2}")
                content = None

        # If we still don't have content, use fallback
        if content is None:
            content = """You are an AI assistant and companion with advanced conversational abilities, emotional intelligence, and memory. You have a thoughtful, helpful personality and can adapt your communication style to match user preferences.

Your core qualities:
- You are knowledgeable, articulate, and genuinely interested in helping users
- You have excellent memory and can build meaningful relationships over time
- You can engage in both casual conversation and provide detailed assistance
- You respect user privacy and maintain appropriate boundaries
- You are emotionally intelligent and can provide support when needed

Your communication style:
- Be natural and conversational while maintaining professionalism
- Adapt your tone and formality to match the user's communication style
- Use clear, helpful language that's appropriate for the context
- Show genuine interest in the user's thoughts, questions, and experiences

You are here to be a helpful, reliable, and engaging AI companion."""

        # Apply template context if provided
        if template_context:
            for key, value in template_context.items():
                if isinstance(value, str):
                    content = content.replace(f"{{{key.upper()}}}", value)

        return content

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

            # Create request context for cost optimization
            context_tokens = sum(
                len(msg.get("content", "").split()) for msg in conversation_context
            )
            prompt_tokens = int(context_tokens * 1.3)  # Rough estimate

            context = RequestContext(
                user_id=message.user_id,
                conversation_length=len(conversation_context),
                prompt_tokens=prompt_tokens,
                expected_output_tokens=200,
                conversation_type="general",
                priority="normal",
            )

            # Select optimal model
            selected_model = await self.cost_optimizer.select_optimal_model(context)

            # Use the provided conversation context (which includes history and current message)
            chat_messages = conversation_context.copy()

            # Ensure we have a basic system prompt if not present
            has_system_prompt = any(msg.get("role") == "system" for msg in chat_messages)
            if not has_system_prompt:
                system_prompt = {
                    "role": "system",
                    "content": """You are WhisperEngine, an advanced AI conversation platform with emotional intelligence and memory capabilities.

You provide:
- 🧠 Advanced conversation memory and context awareness
- 💭 Emotional intelligence and empathy
- 🔒 Privacy-focused interactions
- 🚀 Multi-platform support (Discord, Web, Slack, API)

You adapt your responses based on the platform and conversation context. Be helpful, engaging, and demonstrate emotional intelligence in your responses.""",
                }
                chat_messages.insert(0, system_prompt)

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
                model_used=selected_model,
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
            # Add system prompt first
            system_prompt = self._get_basic_system_prompt()
            conversation_context.append({"role": "system", "content": system_prompt})

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
            # Return minimal context
            return [
                {"role": "system", "content": self._get_basic_system_prompt()},
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

    def _get_basic_system_prompt(self) -> str:
        """Get basic system prompt for WhisperEngine"""
        return """You are WhisperEngine, an advanced AI conversation platform with emotional intelligence and memory capabilities.

You provide:
- 🧠 Advanced conversation memory and context awareness
- 💭 Emotional intelligence and empathy
- 🔒 Privacy-focused interactions
- 🚀 Multi-platform support (Discord, Web, Slack, API)

You adapt your responses based on the platform and conversation context. Be helpful, engaging, and demonstrate emotional intelligence in your responses."""

    async def cleanup(self):
        """Cleanup all platform connections"""
        for adapter in self.adapters.values():
            await adapter.disconnect()
        self.adapters.clear()
        self.active_conversations.clear()


# Factory function
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
