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
    """Discord chat adapter (existing WhisperEngine integration)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(ChatPlatform.DISCORD, config)
        self.bot = None
    
    async def connect(self) -> bool:
        """Connect to Discord"""
        try:
            # This would integrate with existing Discord bot setup
            self.connected = True
            return True
        except Exception as e:
            logging.error(f"Failed to connect to Discord: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Discord"""
        if self.bot and hasattr(self.bot, 'close') and callable(getattr(self.bot, 'close')):
            try:
                await self.bot.close()
            except Exception as e:
                logging.warning(f"Error closing Discord bot: {e}")
        self.connected = False
    
    async def send_message(self, user_id: str, content: str, channel_id: Optional[str] = None) -> bool:
        """Send Discord message"""
        # Implementation would use existing Discord bot methods
        return True
    
    async def get_user_info(self, user_id: str) -> Optional[User]:
        """Get Discord user info"""
        # Implementation would use Discord API
        return None
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Message]:
        """Get Discord conversation history"""
        # Implementation would use Discord message history
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
        
        # WhisperEngine AI Components (will be set by factory function)
        self.memory_manager = None
        self.llm_client = None
        self.external_emotion_ai = None
        self.phase2_integration = None
        self.conversation_cache = None
        self.image_processor = None
        
        # Feature flags
        self.enable_emotional_intelligence = False
        self.enable_memory_features = False
        
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
        
        # Generate response (this would integrate with existing AI system)
        # For now, return a mock response
        return AIResponse(
            content=f"I understand your message: '{message.content}'. This response was generated using {selected_model}.",
            model_used=selected_model,
            tokens_used=150,
            cost=0.001,
            generation_time_ms=500,
            confidence=0.85
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
    db_manager: Optional[DatabaseIntegrationManager] = None,
    whisperengine_components: Optional[Dict[str, Any]] = None
) -> UniversalChatOrchestrator:
    """Factory function to create universal chat platform with WhisperEngine AI components"""
    if config_manager is None:
        config_manager = AdaptiveConfigManager()
    if db_manager is None:
        db_manager = DatabaseIntegrationManager(config_manager)
    
    orchestrator = UniversalChatOrchestrator(config_manager, db_manager)
    
    # Add WhisperEngine AI components if provided
    if whisperengine_components:
        orchestrator.memory_manager = whisperengine_components.get('memory_manager')
        orchestrator.llm_client = whisperengine_components.get('llm_client')
        orchestrator.external_emotion_ai = whisperengine_components.get('external_emotion_ai')
        orchestrator.phase2_integration = whisperengine_components.get('phase2_integration')
        orchestrator.conversation_cache = whisperengine_components.get('conversation_cache')
        orchestrator.image_processor = whisperengine_components.get('image_processor')
        
        # Enable sophisticated AI features if components are available
        orchestrator.enable_emotional_intelligence = bool(
            orchestrator.external_emotion_ai or orchestrator.phase2_integration
        )
        orchestrator.enable_memory_features = bool(orchestrator.memory_manager)
        
    return orchestrator


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