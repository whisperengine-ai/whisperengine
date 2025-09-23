"""
Universal Identity System for WhisperEngine

Provides platform-agnostic user identity management, allowing users to interact
via Discord, Web UI, or other platforms while maintaining consistent identity
and memory across all platforms.

Solves the Discord ID dependency issue by introducing universal user IDs
that can map to multiple platform-specific identities.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any, List
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
        
        if platform_key in self._platform_lookup:
            universal_id = self._platform_lookup[platform_key]
            return await self.get_user_by_universal_id(universal_id)
        
        universal_id = await self._load_universal_id_by_platform_key(platform_key)
        if universal_id:
            self._platform_lookup[platform_key] = universal_id
            return await self.get_user_by_universal_id(universal_id)
        
        return None
    
    async def find_users_by_username(self, username: str) -> List[UniversalUser]:
        """Find existing users by username patterns (for account discovery)"""
        if not hasattr(self, 'db_manager') or not self.db_manager:
            logger.warning("No database manager available for username search")
            return []
        
        try:
            async with self.db_manager.acquire() as conn:
                # Search in universal_users table by primary_username and display_name
                universal_query = """
                    SELECT universal_id, primary_username, display_name, email, 
                           preferences, privacy_settings, created_at, last_active
                    FROM universal_users 
                    WHERE LOWER(primary_username) = LOWER($1) 
                       OR LOWER(display_name) = LOWER($1)
                """
                universal_rows = await conn.fetch(universal_query, username)
                
                # Search in platform_identities table by username and display_name
                platform_query = """
                    SELECT DISTINCT u.universal_id, u.primary_username, u.display_name, u.email,
                           u.preferences, u.privacy_settings, u.created_at, u.last_active
                    FROM universal_users u
                    JOIN platform_identities p ON u.universal_id = p.universal_id
                    WHERE LOWER(p.username) = LOWER($1) 
                       OR LOWER(p.display_name) = LOWER($1)
                """
                platform_rows = await conn.fetch(platform_query, username)
                
                # Combine and deduplicate results
                all_rows = list(universal_rows) + list(platform_rows)
                seen_ids = set()
                unique_rows = []
                for row in all_rows:
                    if row['universal_id'] not in seen_ids:
                        seen_ids.add(row['universal_id'])
                        unique_rows.append(row)
                
                # Convert database rows to UniversalUser objects
                found_users = []
                for row in unique_rows:
                    # Load platform identities for this user
                    identity_query = """
                        SELECT platform, platform_user_id, username, display_name, 
                               email, avatar_url, verified_at, metadata
                        FROM platform_identities 
                        WHERE universal_id = $1
                    """
                    identity_rows = await conn.fetch(identity_query, row['universal_id'])
                    
                    # Build platform identities dictionary
                    platform_identities = {}
                    for identity_row in identity_rows:
                        platform = ChatPlatform(identity_row['platform'])
                        identity = PlatformIdentity(
                            platform=platform,
                            platform_user_id=identity_row['platform_user_id'],
                            username=identity_row['username'],
                            display_name=identity_row['display_name'],
                            email=identity_row['email'],
                            avatar_url=identity_row['avatar_url'],
                            verified_at=identity_row['verified_at'],
                            metadata=json.loads(identity_row['metadata']) if identity_row['metadata'] else {}
                        )
                        platform_identities[platform] = identity
                    
                    # Create UniversalUser object
                    user = UniversalUser(
                        universal_id=row['universal_id'],
                        primary_username=row['primary_username'],
                        display_name=row['display_name'],
                        email=row['email'],
                        platform_identities=platform_identities,
                        created_at=row['created_at'],
                        last_active=row['last_active'],
                        preferences=json.loads(row['preferences']) if row['preferences'] else {},
                        privacy_settings=json.loads(row['privacy_settings']) if row['privacy_settings'] else {}
                    )
                    
                    found_users.append(user)
                    self._cache_user(user)
                
                if found_users:
                    logger.info("Found %d existing users matching username '%s'", len(found_users), username)
                else:
                    logger.debug("No existing users found for username '%s'", username)
                
                return found_users
                
        except Exception as e:
            logger.error("Failed to search users by username '%s': %s", username, e)
            return []
    
    async def find_users_by_username_with_bot_memories(self, username: str) -> List[Dict[str, Any]]:
        """Find existing users by username and include their bot-specific memory counts"""
        base_users = await self.find_users_by_username(username)
        
        if not base_users:
            return []
        
        # For each found user, get their memory counts across different bots
        enhanced_users = []
        for user in base_users:
            user_data = {
                "universal_id": user.universal_id,
                "username": user.primary_username,
                "display_name": user.display_name,
                "email": user.email,
                "platform_identities": {},
                "bot_memories": {}  # This will store memory counts per bot
            }
            
            # Add platform identity information
            for platform, identity in user.platform_identities.items():
                user_data["platform_identities"][platform.value] = {
                    "username": identity.username,
                    "display_name": identity.display_name,
                    "platform_user_id": identity.platform_user_id
                }
            
            # Get memory counts for each bot (this requires querying the vector store)
            try:
                bot_memory_counts = await self._get_user_memory_counts_by_bot(user.universal_id)
                user_data["bot_memories"] = bot_memory_counts
            except Exception as e:
                logger.error("Failed to get bot memory counts for user %s: %s", user.universal_id, e)
                user_data["bot_memories"] = {}
            
            enhanced_users.append(user_data)
        
        return enhanced_users
    
    async def _get_user_memory_counts_by_bot(self, universal_id: str) -> Dict[str, int]:
        """Get memory counts for a user across different bots"""
        # This is a simplified implementation - in a full version you'd query the vector store directly
        # For now, we'll return placeholder data showing the concept
        
        bot_memory_counts = {}
        
        # In a real implementation, you would:
        # 1. Query Qdrant for memories where user_id matches any of the user's platform identities
        # 2. Group by bot_name and count
        # 3. Return the counts
        
        # For now, let's simulate this by checking if the user has Discord identity (indicating potential bot usage)
        cached_user = self._user_cache.get(universal_id)
        if cached_user and hasattr(cached_user, 'platform_identities'):
            has_discord = ChatPlatform.DISCORD in cached_user.platform_identities
            
            if has_discord:
                # Simulate some memory counts for demonstration
                bot_memory_counts = {
                    "Elena": 15,  # Marine biologist conversations
                    "Marcus": 8,  # AI researcher conversations  
                }
        
        logger.debug("Bot memory counts for user %s: %s", universal_id, bot_memory_counts)
        return bot_memory_counts
    
    async def _get_user_memory_counts_by_bot(self, universal_id: str) -> Dict[str, int]:
        """Get memory counts for a user across different bots"""
        # This is a simplified implementation - in a full version you'd query the vector store directly
        # For now, we'll return placeholder data showing the concept
        
        # Available bot names from the environment configurations
        available_bots = ["Elena", "Marcus", "Marcus Chen", "Gabriel", "Dream"]
        
        bot_memory_counts = {}
        
        # In a real implementation, you would:
        # 1. Query Qdrant for memories where user_id matches any of the user's platform identities
        # 2. Group by bot_name and count
        # 3. Return the counts
        
        # For now, let's simulate this by checking if the user has Discord identity (indicating potential bot usage)
        has_discord = any(platform.value == "discord" for platform in 
                         getattr(self._user_cache.get(universal_id, {}), 'platform_identities', {}).keys()
                         if hasattr(self._user_cache.get(universal_id, {}), 'platform_identities'))
        
        if has_discord:
            # Simulate some memory counts for demonstration
            bot_memory_counts = {
                "Elena": 15,  # Marine biologist conversations
                "Marcus": 8,  # AI researcher conversations  
            }
        
        logger.debug("Bot memory counts for user %s: %s", universal_id, bot_memory_counts)
        return bot_memory_counts

    async def _load_universal_id_by_platform_key(self, platform_key: str) -> Optional[str]:
        if not hasattr(self, 'db_manager') or not self.db_manager:
            logger.warning("No database manager available for username search")
            return []
        
        try:
            async with self.db_manager.acquire() as conn:
                # Search in universal_users table by primary_username and display_name
                universal_query = """
                    SELECT universal_id, primary_username, display_name, email, 
                           preferences, privacy_settings, created_at, last_active
                    FROM universal_users 
                    WHERE LOWER(primary_username) = LOWER($1) 
                       OR LOWER(display_name) = LOWER($1)
                """
                universal_rows = await conn.fetch(universal_query, username)
                
                # Search in platform_identities table by username and display_name
                platform_query = """
                    SELECT DISTINCT u.universal_id, u.primary_username, u.display_name, u.email,
                           u.preferences, u.privacy_settings, u.created_at, u.last_active
                    FROM universal_users u
                    JOIN platform_identities p ON u.universal_id = p.universal_id
                    WHERE LOWER(p.username) = LOWER($1) 
                       OR LOWER(p.display_name) = LOWER($1)
                """
                platform_rows = await conn.fetch(platform_query, username)
                
                # Combine and deduplicate results
                all_rows = list(universal_rows) + list(platform_rows)
                seen_ids = set()
                unique_rows = []
                for row in all_rows:
                    if row['universal_id'] not in seen_ids:
                        seen_ids.add(row['universal_id'])
                        unique_rows.append(row)
                
                # Convert database rows to UniversalUser objects
                found_users = []
                for row in unique_rows:
                    # Load platform identities for this user
                    identity_query = """
                        SELECT platform, platform_user_id, username, display_name, 
                               email, avatar_url, verified_at, metadata
                        FROM platform_identities 
                        WHERE universal_id = $1
                    """
                    identity_rows = await conn.fetch(identity_query, row['universal_id'])
                    
                    # Build platform identities dictionary
                    platform_identities = {}
                    for identity_row in identity_rows:
                        platform = ChatPlatform(identity_row['platform'])
                        identity = PlatformIdentity(
                            platform=platform,
                            platform_user_id=identity_row['platform_user_id'],
                            username=identity_row['username'],
                            display_name=identity_row['display_name'],
                            email=identity_row['email'],
                            avatar_url=identity_row['avatar_url'],
                            verified_at=identity_row['verified_at'],
                            metadata=json.loads(identity_row['metadata']) if identity_row['metadata'] else {}
                        )
                        platform_identities[platform] = identity
                    
                    # Create UniversalUser object
                    user = UniversalUser(
                        universal_id=row['universal_id'],
                        primary_username=row['primary_username'],
                        display_name=row['display_name'],
                        email=row['email'],
                        platform_identities=platform_identities,
                        created_at=row['created_at'],
                        last_active=row['last_active'],
                        preferences=json.loads(row['preferences']) if row['preferences'] else {},
                        privacy_settings=json.loads(row['privacy_settings']) if row['privacy_settings'] else {}
                    )
                    
                    found_users.append(user)
                    self._cache_user(user)
                
                if found_users:
                    logger.info("Found %d existing users matching username '%s'", len(found_users), username)
                else:
                    logger.debug("No existing users found for username '%s'", username)
                
                return found_users
                
        except Exception as e:
            logger.error("Failed to search users by username '%s': %s", username, e)
            return []
    
    async def _load_universal_id_by_platform_key(self, platform_key: str) -> Optional[str]:
        """Load universal ID by platform key - placeholder for database implementation"""
        # This would query the database for the universal_id associated with this platform key
        logger.debug("Platform key lookup for '%s' - database implementation needed", platform_key)
        return None
    
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
            # Store in PostgreSQL
            async with self.db_manager.acquire() as conn:
                # First, upsert the universal user
                await conn.execute("""
                    INSERT INTO universal_users (
                        universal_id, primary_username, display_name, email,
                        created_at, last_active, preferences, privacy_settings
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (universal_id) DO UPDATE SET
                        primary_username = EXCLUDED.primary_username,
                        display_name = EXCLUDED.display_name,
                        email = EXCLUDED.email,
                        last_active = EXCLUDED.last_active,
                        preferences = EXCLUDED.preferences,
                        privacy_settings = EXCLUDED.privacy_settings
                """, 
                    user.universal_id,
                    user.primary_username,
                    user.display_name,
                    user.email,
                    user.created_at,
                    user.last_active,
                    json.dumps(user.preferences),
                    json.dumps(user.privacy_settings)
                )
                
                # Delete existing platform identities for this user
                await conn.execute(
                    "DELETE FROM platform_identities WHERE universal_id = $1",
                    user.universal_id
                )
                
                # Insert current platform identities
                for platform, identity in user.platform_identities.items():
                    await conn.execute("""
                        INSERT INTO platform_identities (
                            universal_id, platform, platform_user_id, username,
                            display_name, email, verified_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                        user.universal_id,
                        platform.value,
                        identity.platform_user_id,
                        identity.username,
                        identity.display_name,
                        identity.email,
                        identity.verified_at
                    )
                
                logger.info("Successfully stored user %s in database", user.universal_id)
        except Exception as e:
            logger.error("Failed to store user %s: %s", user.universal_id, e)

    async def _load_user_by_universal_id(self, universal_id: str) -> Optional[UniversalUser]:
        """Load user from database by universal ID"""
        if not self.db_manager:
            return None

        try:
            async with self.db_manager.acquire() as conn:
                # Load user data
                user_row = await conn.fetchrow(
                    "SELECT * FROM universal_users WHERE universal_id = $1",
                    universal_id
                )
                
                if not user_row:
                    return None
                
                # Load platform identities
                platform_rows = await conn.fetch(
                    "SELECT * FROM platform_identities WHERE universal_id = $1",
                    universal_id
                )
                
                # Create user object
                user = UniversalUser(
                    universal_id=user_row['universal_id'],
                    primary_username=user_row['primary_username'],
                    display_name=user_row['display_name'],
                    email=user_row['email'],
                    created_at=user_row['created_at'],
                    last_active=user_row['last_active'],
                    preferences=json.loads(user_row['preferences'] or '{}'),
                    privacy_settings=json.loads(user_row['privacy_settings'] or '{}')
                )
                
                # Add platform identities
                for platform_row in platform_rows:
                    platform = ChatPlatform(platform_row['platform'])
                    identity = PlatformIdentity(
                        platform=platform,
                        platform_user_id=platform_row['platform_user_id'],
                        username=platform_row['username'],
                        display_name=platform_row['display_name'],
                        email=platform_row['email'],
                        verified_at=platform_row['verified_at']
                    )
                    user.add_platform_identity(identity)
                
                logger.debug("Loaded user %s from database", universal_id)
                return user
                
        except Exception as e:
            logger.error("Failed to load user %s: %s", universal_id, e)
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
            async with self.db_manager.acquire() as conn:
                # Find universal_id by platform identity
                platform_row = await conn.fetchrow("""
                    SELECT universal_id FROM platform_identities 
                    WHERE platform = $1 AND platform_user_id = $2
                """, platform.value, platform_user_id)
                
                if not platform_row:
                    return None
                
                # Load the full user
                return await self._load_user_by_universal_id(platform_row['universal_id'])
                
        except Exception as e:
            logger.error("Failed to load user by %s:%s: %s", platform.value, platform_user_id, e)
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