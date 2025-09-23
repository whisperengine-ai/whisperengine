"""
Universal Identity System for WhisperEngine

Provides platform-agnostic user identity management, allowing users to interact
via Discord, Web UI, or other platforms while maintaining consistent identity
and memory across all platforms.

Solves the Discord ID dependency issue by introducing universal user IDs
that can map to multiple platform-specific identities.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
import logging

from src.platforms.universal_chat import ChatPlatform

logger = logging.getLogger(__name__)


class IdentityProvider(Enum):
    """Supported identity providers"""
    DISCORD = "discord"
    WEB_UI = "web_ui"
    SLACK = "slack"
    GOOGLE = "google"
    GITHUB = "github"
    ANONYMOUS = "anonymous"


@dataclass
class PlatformIdentity:
    """Platform-specific identity information"""
    platform: ChatPlatform
    platform_user_id: str  # Platform's native user ID (Discord ID, email, etc.)
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    verified_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UniversalUser:
    """Universal user identity across all platforms"""
    
    # Universal unique identifier (not platform-specific)
    universal_id: str
    
    # Primary identity info
    primary_username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    
    # Platform identities (user can have multiple)
    platform_identities: Dict[ChatPlatform, PlatformIdentity] = field(default_factory=dict)
    
    # Account metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Privacy and settings
    privacy_settings: Dict[str, Any] = field(default_factory=dict)
    
    def get_platform_identity(self, platform: ChatPlatform) -> Optional[PlatformIdentity]:
        """Get platform-specific identity"""
        return self.platform_identities.get(platform)
    
    def add_platform_identity(self, identity: PlatformIdentity):
        """Add or update platform identity"""
        self.platform_identities[identity.platform] = identity
        self.last_active = datetime.now()
    
    def get_effective_username(self, platform: ChatPlatform) -> str:
        """Get username for specific platform, fallback to primary"""
        platform_identity = self.get_platform_identity(platform)
        if platform_identity:
            return platform_identity.username
        return self.primary_username
    
    def has_platform(self, platform: ChatPlatform) -> bool:
        """Check if user has identity on platform"""
        return platform in self.platform_identities


class UniversalIdentityManager:
    """Manages universal user identities across platforms"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self._user_cache: Dict[str, UniversalUser] = {}
        self._platform_lookup: Dict[str, str] = {}  # platform_key -> universal_id
        
    def _generate_universal_id(self) -> str:
        """Generate a new universal user ID"""
        return f"weu_{uuid.uuid4().hex[:16]}"  # WhisperEngine User prefix
    
    def _create_platform_key(self, platform: ChatPlatform, platform_user_id: str) -> str:
        """Create lookup key for platform identity"""
        return f"{platform.value}:{platform_user_id}"
    
    async def create_web_user(
        self, 
        username: str, 
        email: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> UniversalUser:
        """Create a new web-only user"""
        universal_id = self._generate_universal_id()
        
        # Create web platform identity
        web_identity = PlatformIdentity(
            platform=ChatPlatform.WEB_UI,
            platform_user_id=universal_id,  # Use universal ID as web platform ID
            username=username,
            display_name=display_name,
            email=email
        )
        
        # Create universal user
        user = UniversalUser(
            universal_id=universal_id,
            primary_username=username,
            display_name=display_name,
            email=email
        )
        user.add_platform_identity(web_identity)
        
        # Store in database and cache
        await self._store_user(user)
        self._cache_user(user)
        
        logger.info("Created new web user: %s (%s)", username, universal_id)
        return user
    
    async def get_or_create_discord_user(
        self, 
        discord_user_id: str, 
        username: str,
        display_name: Optional[str] = None
    ) -> UniversalUser:
        """Get existing or create new user from Discord identity"""
        platform_key = self._create_platform_key(ChatPlatform.DISCORD, discord_user_id)
        
        # Check if user already exists
        universal_id = self._platform_lookup.get(platform_key)
        if universal_id and universal_id in self._user_cache:
            user = self._user_cache[universal_id]
            user.last_active = datetime.now()
            return user
        
        # Load from database
        user = await self._load_user_by_platform(ChatPlatform.DISCORD, discord_user_id)
        if user:
            self._cache_user(user)
            return user
        
        # Create new user
        universal_id = self._generate_universal_id()
        
        discord_identity = PlatformIdentity(
            platform=ChatPlatform.DISCORD,
            platform_user_id=discord_user_id,
            username=username,
            display_name=display_name
        )
        
        user = UniversalUser(
            universal_id=universal_id,
            primary_username=username,
            display_name=display_name
        )
        user.add_platform_identity(discord_identity)
        
        await self._store_user(user)
        self._cache_user(user)
        
        logger.info("Created new Discord user: %s (%s)", username, universal_id)
        return user
    
    async def link_platform_identity(
        self, 
        universal_id: str, 
        platform_identity: PlatformIdentity
    ) -> bool:
        """Link additional platform identity to existing user"""
        user = await self.get_user_by_universal_id(universal_id)
        if not user:
            return False
        
        # Check if platform identity already exists elsewhere
        existing_user = await self._load_user_by_platform(
            platform_identity.platform, 
            platform_identity.platform_user_id
        )
        if existing_user and existing_user.universal_id != universal_id:
            logger.warning("Platform identity already linked to different user")
            return False
        
        user.add_platform_identity(platform_identity)
        await self._store_user(user)
        self._cache_user(user)
        
        logger.info("Linked %s identity to user %s", platform_identity.platform.value, universal_id)
        return True
    
    async def get_user_by_universal_id(self, universal_id: str) -> Optional[UniversalUser]:
        """Get user by universal ID"""
        if universal_id in self._user_cache:
            return self._user_cache[universal_id]
        
        user = await self._load_user_by_universal_id(universal_id)
        if user:
            self._cache_user(user)
        return user
    
    async def get_user_by_platform_id(
        self, 
        platform: ChatPlatform, 
        platform_user_id: str
    ) -> Optional[UniversalUser]:
        """Get user by platform-specific ID"""
        platform_key = self._create_platform_key(platform, platform_user_id)
        
        universal_id = self._platform_lookup.get(platform_key)
        if universal_id:
            return await self.get_user_by_universal_id(universal_id)
        
        user = await self._load_user_by_platform(platform, platform_user_id)
        if user:
            self._cache_user(user)
        return user
    
    async def authenticate_web_user(
        self, 
        session_token: str
    ) -> Optional[UniversalUser]:
        """Authenticate web user by session token"""
        # In production, this would validate JWT or session token
        # For now, extract universal_id from token
        try:
            if session_token.startswith("weu_"):
                return await self.get_user_by_universal_id(session_token)
        except Exception as e:
            logger.error(f"Web authentication failed: {e}")
        return None
    
    def _cache_user(self, user: UniversalUser):
        """Cache user and platform lookups"""
        self._user_cache[user.universal_id] = user
        
        for platform, identity in user.platform_identities.items():
            platform_key = self._create_platform_key(platform, identity.platform_user_id)
            self._platform_lookup[platform_key] = user.universal_id
    
    async def _store_user(self, user: UniversalUser):
        """Store user in database"""
        if not self.db_manager:
            logger.warning("No database manager - user not persisted")
            return
        
        try:
            # Implementation would store in database
            # For now, just log
            logger.debug(f"Storing user {user.universal_id} in database")
        except Exception as e:
            logger.error(f"Failed to store user: {e}")
    
    async def _load_user_by_universal_id(self, universal_id: str) -> Optional[UniversalUser]:
        """Load user from database by universal ID"""
        if not self.db_manager:
            return None
        
        try:
            # Implementation would load from database
            logger.debug(f"Loading user {universal_id} from database")
            return None
        except Exception as e:
            logger.error(f"Failed to load user: {e}")
            return None
    
    async def _load_user_by_platform(
        self, 
        platform: ChatPlatform, 
        platform_user_id: str
    ) -> Optional[UniversalUser]:
        """Load user from database by platform identity"""
        if not self.db_manager:
            return None
        
        try:
            # Implementation would load from database
            logger.debug(f"Loading user by {platform.value}:{platform_user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to load user by platform: {e}")
            return None


def create_identity_manager(db_manager=None) -> UniversalIdentityManager:
    """Factory function for identity manager"""
    return UniversalIdentityManager(db_manager)


# Example usage for migration from Discord IDs
async def migrate_discord_user_to_universal(
    identity_manager: UniversalIdentityManager,
    discord_user_id: str,
    username: str
) -> str:
    """Helper to migrate existing Discord user to universal system"""
    user = await identity_manager.get_or_create_discord_user(
        discord_user_id=discord_user_id,
        username=username
    )
    return user.universal_id