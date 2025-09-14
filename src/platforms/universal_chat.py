"""
Universal Chat Platform Architecture for WhisperEngine
Abstracts conversation handling to support web UI, Discord, Slack, Teams, and other platforms.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

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
    display_name: Optional[str] = None
    platform: ChatPlatform = ChatPlatform.WEB_UI
    platform_user_id: Optional[str] = None  # Platform-specific ID
    preferences: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
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
    channel_id: Optional[str] = None
    thread_id: Optional[str] = None
    reply_to: Optional[str] = None
    attachments: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
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
    channel_id: Optional[str] = None
    title: Optional[str] = None
    messages: Optional[List[Message]] = None
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
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
    sources: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.suggestions is None:
            self.suggestions = []


class AbstractChatAdapter(ABC):
    """Abstract base class for chat platform adapters"""
    
    def __init__(self, platform: ChatPlatform, config: Dict[str, Any]):
        self.platform = platform
        self.config = config
        self.message_handlers: List[Callable] = []
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
    async def send_message(self, user_id: str, content: str, channel_id: Optional[str] = None) -> bool:
        """Send a message to the platform"""
        pass
    
    @abstractmethod
    async def get_user_info(self, user_id: str) -> Optional[User]:
        """Get user information from the platform"""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Message]:
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
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(ChatPlatform.WEB_UI, config)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self) -> bool:
        """Web UI is always connected"""
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        """Cleanup web UI sessions"""
        self.active_sessions.clear()
        self.connected = False
    
    async def send_message(self, user_id: str, content: str, channel_id: Optional[str] = None) -> bool:
        """Send message via WebSocket or store for retrieval"""
        try:
            session_id = channel_id or f"web_{user_id}"
            
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    "user_id": user_id,
                    "messages": [],
                    "websocket": None
                }
            
            # Store message for web UI retrieval
            message = {
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "type": "ai_response"
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
    
    async def get_user_info(self, user_id: str) -> Optional[User]:
        """Create web UI user info"""
        return User(
            user_id=user_id,
            username=f"web_user_{user_id[:8]}",
            display_name="Web User",
            platform=ChatPlatform.WEB_UI,
            platform_user_id=user_id
        )
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Message]:
        """Get web UI conversation history"""
        # This would typically come from the database
        return []
    
    def register_websocket(self, session_id: str, websocket):
        """Register WebSocket for real-time messaging"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["websocket"] = websocket
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get messages for a web session"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]["messages"]
        return []


class DiscordChatAdapter(AbstractChatAdapter):
    """Discord chat adapter for Discord bot integration"""
    
    def __init__(self, config: Dict[str, Any]):
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
        if self.bot and hasattr(self.bot, 'close') and callable(getattr(self.bot, 'close')):
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
            platform=ChatPlatform.DISCORD
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
                "display_name": discord_message.author.display_name
            }
        )
    
    async def send_message(self, user_id: str, content: str, channel_id: Optional[str] = None) -> bool:
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
    
    async def get_user_info(self, user_id: str) -> Optional[User]:
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
                    platform=ChatPlatform.DISCORD
                )
            
            return None
        except Exception as e:
            logging.error(f"Failed to get Discord user info: {e}")
            return None
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Message]:
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
    
    def __init__(self, config: Dict[str, Any]):
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
    
    async def send_message(self, user_id: str, content: str, channel_id: Optional[str] = None) -> bool:
        """Send Slack message"""
        # Implementation would use Slack Web API
        return True
    
    async def get_user_info(self, user_id: str) -> Optional[User]:
        """Get Slack user info"""
        # Implementation would use Slack API
        return None
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Message]:
        """Get Slack conversation history"""
        # Implementation would use Slack conversations API
        return []


class APIChatAdapter(AbstractChatAdapter):
    """REST API adapter for programmatic access"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(ChatPlatform.API, config)
        self.api_keys: Dict[str, str] = config.get("api_keys", {})
    
    async def connect(self) -> bool:
        """API is always connected"""
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        """No connection to close for API"""
        self.connected = False
    
    async def send_message(self, user_id: str, content: str, channel_id: Optional[str] = None) -> bool:
        """Store API response for retrieval"""
        # Implementation would store response in database or cache
        return True
    
    async def get_user_info(self, user_id: str) -> Optional[User]:
        """Get API user info"""
        return User(
            user_id=user_id,
            username=f"api_user_{user_id}",
            platform=ChatPlatform.API,
            platform_user_id=user_id
        )
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Message]:
        """Get API conversation history"""
        return []


class UniversalChatOrchestrator:
    """Main orchestrator that manages all chat platforms and AI responses"""
    
    def __init__(self, 
                 config_manager: AdaptiveConfigManager,
                 db_manager: DatabaseIntegrationManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.cost_optimizer = CostOptimizationEngine(db_manager)
        
        self.adapters: Dict[ChatPlatform, AbstractChatAdapter] = {}
        self.active_conversations: Dict[str, Conversation] = {}
        self.ai_engine = None  # Would integrate with existing AI system
        
        # Load platform configurations
        self.platform_configs = self._load_platform_configs()
    
    def _load_platform_configs(self) -> Dict[ChatPlatform, Dict[str, Any]]:
        """Load platform-specific configurations"""
        return {
            ChatPlatform.WEB_UI: {
                "enabled": True,
                "max_sessions": 1000,
                "session_timeout": 3600
            },
            ChatPlatform.DISCORD: {
                "enabled": self._is_discord_enabled(),
                "bot_token": self._get_env("DISCORD_BOT_TOKEN"),
                "max_guilds": 100
            },
            ChatPlatform.SLACK: {
                "enabled": self._is_slack_enabled(),
                "bot_token": self._get_env("SLACK_BOT_TOKEN"),
                "signing_secret": self._get_env("SLACK_SIGNING_SECRET")
            },
            ChatPlatform.API: {
                "enabled": True,
                "rate_limit": 1000,
                "auth_required": True
            }
        }
    
    def _is_discord_enabled(self) -> bool:
        """Check if Discord integration is enabled"""
        import os
        return bool(os.environ.get("DISCORD_BOT_TOKEN"))
    
    def _is_slack_enabled(self) -> bool:
        """Check if Slack integration is enabled"""
        import os
        return bool(os.environ.get("SLACK_BOT_TOKEN"))
    
    def _get_env(self, key: str) -> Optional[str]:
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
            
            logging.info(f"Initialized {len(self.adapters)} chat platform(s): {list(self.adapters.keys())}")
            return True
        
        except Exception as e:
            logging.error(f"Failed to initialize chat platforms: {e}")
            return False
    
    async def handle_message(self, message: Message):
        """Handle incoming message from any platform"""
        try:
            # Get or create conversation
            conversation = await self.get_or_create_conversation(message)
            
            # Ensure messages list exists
            if conversation.messages is None:
                conversation.messages = []
            
            # Add message to conversation
            conversation.messages.append(message)
            conversation.last_activity = datetime.now()
            
            # Generate AI response
            ai_response = await self.generate_ai_response(message, conversation)
            
            # Send response back to platform
            adapter = self.adapters.get(message.platform)
            if adapter:
                await adapter.send_message(
                    message.user_id, 
                    ai_response.content, 
                    message.channel_id
                )
            
            # Store conversation and response
            await self.store_conversation(conversation, ai_response)
            
        except Exception as e:
            logging.error(f"Error handling message: {e}")
    
    async def get_or_create_conversation(self, message: Message) -> Conversation:
        """Get existing conversation or create new one"""
        conversation_id = f"{message.platform.value}_{message.user_id}_{message.channel_id or 'direct'}"
        
        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]
        
        # Check database for existing conversation
        # Implementation would query database
        
        # Create new conversation
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=message.user_id,
            platform=message.platform,
            channel_id=message.channel_id,
            title=f"Chat with {message.user_id}"
        )
        
        self.active_conversations[conversation_id] = conversation
        return conversation
    
    async def generate_ai_response(self, message: Message, conversation: Conversation) -> AIResponse:
        """Generate AI response using existing WhisperEngine logic"""
        try:
            # Import LLM client
            from src.llm.llm_client import LLMClient
            
            # Initialize LLM client if not already done
            if not hasattr(self, 'llm_client'):
                self.llm_client = LLMClient()
            
            # Create request context for cost optimization
            messages_count = len(conversation.messages) if conversation.messages else 0
            prompt_tokens = int(len(message.content.split()) * 1.3)  # Rough estimate
            
            context = RequestContext(
                user_id=message.user_id,
                conversation_length=messages_count,
                prompt_tokens=prompt_tokens,
                expected_output_tokens=200,
                conversation_type="general",
                priority="normal"
            )
            
            # Select optimal model
            selected_model = await self.cost_optimizer.select_optimal_model(context)
            
            # Build conversation history for context
            chat_messages = [
                {
                    "role": "system",
                    "content": """You are WhisperEngine, an advanced AI conversation platform with emotional intelligence and memory capabilities.

You provide:
- 🧠 Advanced conversation memory and context awareness
- 💭 Emotional intelligence and empathy
- 🔒 Privacy-focused interactions
- 🚀 Multi-platform support (Discord, Web, Slack, API)

You adapt your responses based on the platform and conversation context. Be helpful, engaging, and demonstrate emotional intelligence in your responses."""
                }
            ]
            
            # Add conversation history (last 10 messages for context)
            recent_messages = conversation.messages[-10:] if conversation.messages else []
            for msg in recent_messages:
                role = "assistant" if msg.user_id == "assistant" else "user"
                chat_messages.append({
                    "role": role,
                    "content": msg.content
                })
            
            # Add current message
            chat_messages.append({
                "role": "user",
                "content": message.content
            })
            
            # Generate response using actual LLM
            start_time = datetime.now()
            response_text = self.llm_client.get_chat_response(chat_messages)
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
                confidence=0.85
            )
            
        except Exception as e:
            logging.error(f"Error generating AI response: {e}")
            # Fallback response
            return AIResponse(
                content="I apologize, but I encountered an error while processing your message. Please try again or check the system configuration.",
                model_used="fallback",
                tokens_used=20,
                cost=0.0,
                generation_time_ms=100,
                confidence=0.0
            )
    
    async def store_conversation(self, conversation: Conversation, ai_response: AIResponse):
        """Store conversation and AI response in database"""
        try:
            # Store conversation data
            # Implementation would use the database abstraction layer
            pass
        except Exception as e:
            logging.error(f"Failed to store conversation: {e}")
    
    async def get_conversation_history(self, user_id: str, platform: ChatPlatform, limit: int = 50) -> List[Message]:
        """Get conversation history for a user on a platform"""
        # Implementation would query database
        return []
    
    async def get_active_platforms(self) -> List[ChatPlatform]:
        """Get list of active chat platforms"""
        return list(self.adapters.keys())
    
    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get statistics for all platforms"""
        stats = {}
        for platform, adapter in self.adapters.items():
            stats[platform.value] = {
                "connected": adapter.connected,
                "message_handlers": len(adapter.message_handlers)
            }
        return stats
    
    async def cleanup(self):
        """Cleanup all platform connections"""
        for adapter in self.adapters.values():
            await adapter.disconnect()
        self.adapters.clear()
        self.active_conversations.clear()


# Factory function
def create_universal_chat_platform(
    config_manager: Optional[AdaptiveConfigManager] = None,
    db_manager: Optional[DatabaseIntegrationManager] = None
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
            print("Universal chat platform initialized successfully")
            
            # Show active platforms
            platforms = await chat_platform.get_active_platforms()
            print(f"Active platforms: {[p.value for p in platforms]}")
            
            # Show platform stats
            stats = await chat_platform.get_platform_stats()
            print(f"Platform stats: {stats}")
        
        else:
            print("Failed to initialize chat platform")
    
    finally:
        await chat_platform.cleanup()


if __name__ == "__main__":
    asyncio.run(main())