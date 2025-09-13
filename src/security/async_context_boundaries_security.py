"""
Async Context Boundaries Manager with PostgreSQL Backend
This replaces the JSON file approach with PostgreSQL for better data integrity and performance
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

from src.security.context_boundaries_security import (
    PrivacyLevel, ConsentStatus, PrivacyPreferences, ContextBoundaryDecision
)
from src.security.postgres_privacy_manager import PostgreSQLPrivacyManager, create_privacy_manager_from_env
from src.memory.context_aware_memory_security import MemoryContext, MemoryContextType

logger = logging.getLogger(__name__)

class AsyncContextBoundariesManager:
    """
    Async manager for user privacy preferences and context boundary enforcement
    Uses PostgreSQL backend for better performance and data integrity
    """
    
    def __init__(self, postgres_manager: Optional[PostgreSQLPrivacyManager] = None):
        """Initialize async context boundaries manager"""
        self.postgres_manager = postgres_manager or create_privacy_manager_from_env()
        self._initialized = False
        
        # Default privacy rules matrix (same as original)
        self.default_compatibility_rules = {
            PrivacyLevel.STRICT: {
                "dm_to_server": False,
                "server_to_dm": False,
                "cross_server": False,
                "private_to_public": False,
                "public_to_private": True  # Public info can go to private
            },
            PrivacyLevel.MODERATE: {
                "dm_to_server": False,
                "server_to_dm": False, 
                "cross_server": True,      # Cross-server safe content only
                "private_to_public": False,
                "public_to_private": True
            },
            PrivacyLevel.PERMISSIVE: {
                "dm_to_server": True,
                "server_to_dm": True,
                "cross_server": True,
                "private_to_public": False,  # Still protect private channels
                "public_to_private": True
            }
        }
        
        logger.info("Async Context boundaries manager initialized")
    
    async def initialize(self):
        """Initialize the manager and database connection"""
        if not self._initialized:
            await self.postgres_manager.initialize()
            self._initialized = True
            logger.info("Async Context boundaries manager database connection initialized")
    
    async def close(self):
        """Close database connections"""
        if self._initialized:
            await self.postgres_manager.close()
            self._initialized = False
    
    async def get_user_preferences(self, user_id: str) -> PrivacyPreferences:
        """Get user privacy preferences, creating defaults if needed"""
        if not self._initialized:
            await self.initialize()
        
        preferences = await self.postgres_manager.get_user_preferences(user_id)
        
        if preferences is None:
            # Create default preferences
            preferences = PrivacyPreferences(
                user_id=user_id,
                privacy_level=PrivacyLevel.MODERATE,
                allow_cross_server=False,
                allow_dm_to_server=False,
                allow_server_to_dm=False,
                allow_private_to_public=False,
                custom_rules={},
                consent_status=ConsentStatus.NOT_ASKED,
                consent_timestamp=None,
                updated_timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            await self.postgres_manager.update_user_preferences(preferences)
            logger.info(f"Created default privacy preferences for user {user_id}")
        
        return preferences
    
    async def update_user_preferences(self, user_id: str, 
                                    privacy_level: Optional[PrivacyLevel] = None,
                                    allow_cross_server: Optional[bool] = None,
                                    allow_dm_to_server: Optional[bool] = None,
                                    allow_server_to_dm: Optional[bool] = None,
                                    allow_private_to_public: Optional[bool] = None,
                                    custom_rules: Optional[Dict[str, bool]] = None,
                                    consent_status: Optional[ConsentStatus] = None,
                                    consent_timestamp: Optional[str] = None):
        """Update user privacy preferences"""
        if not self._initialized:
            await self.initialize()
        
        # Get current preferences
        current_prefs = await self.get_user_preferences(user_id)
        
        # Update only provided fields
        updated_prefs = PrivacyPreferences(
            user_id=user_id,
            privacy_level=privacy_level or current_prefs.privacy_level,
            allow_cross_server=allow_cross_server if allow_cross_server is not None else current_prefs.allow_cross_server,
            allow_dm_to_server=allow_dm_to_server if allow_dm_to_server is not None else current_prefs.allow_dm_to_server,
            allow_server_to_dm=allow_server_to_dm if allow_server_to_dm is not None else current_prefs.allow_server_to_dm,
            allow_private_to_public=allow_private_to_public if allow_private_to_public is not None else current_prefs.allow_private_to_public,
            custom_rules=custom_rules or current_prefs.custom_rules,
            consent_status=consent_status or current_prefs.consent_status,
            consent_timestamp=consent_timestamp or current_prefs.consent_timestamp,
            updated_timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        await self.postgres_manager.update_user_preferences(updated_prefs)
        logger.info(f"Updated privacy preferences for user {user_id}")
    
    async def _log_decision(self, user_id: str, source_context: str, target_context: str, 
                           decision: str, reason: str, privacy_level: str):
        """Log a privacy decision to the audit trail"""
        if not self._initialized:
            await self.initialize()
        
        await self.postgres_manager.log_decision(
            user_id=user_id,
            source_context=source_context,
            target_context=target_context,
            decision=decision,
            reason=reason,
            privacy_level=privacy_level
        )
    
    def _get_context_type_string(self, context: MemoryContext) -> str:
        """Convert MemoryContext to string for logging"""
        if context.context_type == MemoryContextType.DM:
            return "dm"
        elif context.context_type == MemoryContextType.PUBLIC_CHANNEL:
            return "public_channel"
        elif context.context_type == MemoryContextType.PRIVATE_CHANNEL:
            return "private_channel"
        elif context.context_type == MemoryContextType.SERVER_CHANNEL:
            return "server_channel"
        else:
            return str(context.context_type)
    
    def _determine_context_boundary_type(self, source_context: MemoryContext, 
                                       target_context: MemoryContext) -> str:
        """Determine the type of context boundary crossing"""
        source_type = source_context.context_type
        target_type = target_context.context_type
        
        # DM to server boundaries
        if source_type == MemoryContextType.DM and target_type in [MemoryContextType.PUBLIC_CHANNEL, MemoryContextType.PRIVATE_CHANNEL]:
            return "dm_to_server"
        
        # Server to DM boundaries
        if source_type in [MemoryContextType.PUBLIC_CHANNEL, MemoryContextType.PRIVATE_CHANNEL] and target_type == MemoryContextType.DM:
            return "server_to_dm"
        
        # Cross-server boundaries
        if (source_context.server_id and target_context.server_id and 
            source_context.server_id != target_context.server_id):
            return "cross_server"
        
        # Private to public boundaries
        if (source_type == MemoryContextType.PRIVATE_CHANNEL and 
            target_type == MemoryContextType.PUBLIC_CHANNEL):
            return "private_to_public"
        
        # Public to private boundaries
        if (source_type == MemoryContextType.PUBLIC_CHANNEL and 
            target_type == MemoryContextType.PRIVATE_CHANNEL):
            return "public_to_private"
        
        return "same_context"
    
    async def check_context_boundary(self, user_id: str, 
                                   source_context: MemoryContext,
                                   target_context: MemoryContext) -> tuple[bool, str]:
        """
        Check if context boundary crossing is allowed
        Returns (allowed: bool, reason: str)
        """
        if not self._initialized:
            await self.initialize()
        
        # Get user preferences
        preferences = await self.get_user_preferences(user_id)
        
        # Determine boundary type
        boundary_type = self._determine_context_boundary_type(source_context, target_context)
        
        # If same context, always allow
        if boundary_type == "same_context":
            return True, "Same context - allowed"
        
        # Check custom rules first
        if preferences.custom_rules and boundary_type in preferences.custom_rules:
            allowed = preferences.custom_rules[boundary_type]
            reason = f"Custom rule: {boundary_type}"
            
            await self._log_decision(
                user_id=user_id,
                source_context=self._get_context_type_string(source_context),
                target_context=self._get_context_type_string(target_context),
                decision="allowed" if allowed else "blocked",
                reason=reason,
                privacy_level=preferences.privacy_level.value
            )
            
            return allowed, reason
        
        # Check individual preference flags
        if boundary_type == "dm_to_server" and not preferences.allow_dm_to_server:
            reason = f"Privacy level {preferences.privacy_level.value} rule: dm_to_server"
            await self._log_decision(user_id, self._get_context_type_string(source_context), 
                                   self._get_context_type_string(target_context), "blocked", reason, 
                                   preferences.privacy_level.value)
            return False, reason
        
        if boundary_type == "server_to_dm" and not preferences.allow_server_to_dm:
            reason = f"Privacy level {preferences.privacy_level.value} rule: server_to_dm"
            await self._log_decision(user_id, self._get_context_type_string(source_context), 
                                   self._get_context_type_string(target_context), "blocked", reason, 
                                   preferences.privacy_level.value)
            return False, reason
        
        if boundary_type == "cross_server" and not preferences.allow_cross_server:
            reason = f"Privacy level {preferences.privacy_level.value} rule: cross_server"
            await self._log_decision(user_id, self._get_context_type_string(source_context), 
                                   self._get_context_type_string(target_context), "blocked", reason, 
                                   preferences.privacy_level.value)
            return False, reason
        
        if boundary_type == "private_to_public" and not preferences.allow_private_to_public:
            reason = f"Privacy level {preferences.privacy_level.value} rule: private_to_public"
            await self._log_decision(user_id, self._get_context_type_string(source_context), 
                                   self._get_context_type_string(target_context), "blocked", reason, 
                                   preferences.privacy_level.value)
            return False, reason
        
        # Check default compatibility rules
        default_rules = self.default_compatibility_rules.get(preferences.privacy_level, {})
        if boundary_type in default_rules and not default_rules[boundary_type]:
            reason = f"Default privacy level {preferences.privacy_level.value} rule: {boundary_type}"
            await self._log_decision(user_id, self._get_context_type_string(source_context), 
                                   self._get_context_type_string(target_context), "blocked", reason, 
                                   preferences.privacy_level.value)
            return False, reason
        
        # If we reach here, allow the boundary crossing
        reason = f"Privacy level {preferences.privacy_level.value} allows: {boundary_type}"
        await self._log_decision(user_id, self._get_context_type_string(source_context), 
                               self._get_context_type_string(target_context), "allowed", reason, 
                               preferences.privacy_level.value)
        return True, reason
    
    async def request_consent(self, user_id: str, source_context: MemoryContext, 
                            target_context: MemoryContext) -> str:
        """Request user consent for context boundary crossing"""
        if not self._initialized:
            await self.initialize()
        
        boundary_type = self._determine_context_boundary_type(source_context, target_context)
        
        await self._log_decision(
            user_id=user_id,
            source_context=self._get_context_type_string(source_context),
            target_context=self._get_context_type_string(target_context),
            decision="consent_requested",
            reason=f"Consent requested for {boundary_type}",
            privacy_level=(await self.get_user_preferences(user_id)).privacy_level.value
        )
        
        return f"consent_requested_{boundary_type}"
    
    async def process_consent_response(self, user_id: str, source_context: MemoryContext,
                                     target_context: MemoryContext, response: str) -> bool:
        """Process user consent response"""
        if not self._initialized:
            await self.initialize()
        
        boundary_type = self._determine_context_boundary_type(source_context, target_context)
        preferences = await self.get_user_preferences(user_id)
        
        if response.lower() in ['yes', 'allow', 'permit', 'ok', 'allow_once']:
            # Allow once
            await self._log_decision(
                user_id=user_id,
                source_context=self._get_context_type_string(source_context),
                target_context=self._get_context_type_string(target_context),
                decision="allowed_once",
                reason=f"User consented once for {boundary_type}",
                privacy_level=preferences.privacy_level.value
            )
            return True
        
        elif response.lower() in ['allow_always', 'always_allow', 'remember_yes']:
            # Update preferences to always allow this boundary type
            custom_rules = (preferences.custom_rules or {}).copy()
            custom_rules[boundary_type] = True
            
            await self.update_user_preferences(
                user_id=user_id,
                custom_rules=custom_rules,
                consent_status=ConsentStatus.GRANTED,
                consent_timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            await self._log_decision(
                user_id=user_id,
                source_context=self._get_context_type_string(source_context),
                target_context=self._get_context_type_string(target_context),
                decision="allowed_always",
                reason=f"User consented always for {boundary_type}",
                privacy_level=preferences.privacy_level.value
            )
            return True
        
        elif response.lower() in ['no', 'deny', 'block', 'deny_once']:
            await self._log_decision(
                user_id=user_id,
                source_context=self._get_context_type_string(source_context),
                target_context=self._get_context_type_string(target_context),
                decision="denied_once",
                reason=f"User denied once for {boundary_type}",
                privacy_level=preferences.privacy_level.value
            )
            return False
        
        elif response.lower() in ['deny_always', 'never_allow', 'remember_no']:
            # Update preferences to never allow this boundary type
            custom_rules = (preferences.custom_rules or {}).copy()
            custom_rules[boundary_type] = False
            
            await self.update_user_preferences(
                user_id=user_id,
                custom_rules=custom_rules,
                consent_status=ConsentStatus.DENIED,
                consent_timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            await self._log_decision(
                user_id=user_id,
                source_context=self._get_context_type_string(source_context),
                target_context=self._get_context_type_string(target_context),
                decision="denied_always",
                reason=f"User denied always for {boundary_type}",
                privacy_level=preferences.privacy_level.value
            )
            return False
        
        # Default to deny if response is unclear
        return False
    
    async def get_audit_history(self, user_id: Optional[str] = None, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit history for privacy decisions"""
        if not self._initialized:
            await self.initialize()
        
        return await self.postgres_manager.get_audit_history(user_id, limit)
    
    async def cleanup_old_audit_entries(self, days_to_keep: int = 90) -> int:
        """Clean up old audit entries for privacy compliance"""
        if not self._initialized:
            await self.initialize()
        
        return await self.postgres_manager.cleanup_old_audit_entries(days_to_keep)

# Global instance for backward compatibility
_global_async_manager: Optional[AsyncContextBoundariesManager] = None

def get_async_context_boundaries_manager() -> AsyncContextBoundariesManager:
    """Get or create the global async context boundaries manager"""
    global _global_async_manager
    if _global_async_manager is None:
        _global_async_manager = AsyncContextBoundariesManager()
    return _global_async_manager

async def cleanup_global_manager():
    """Clean up the global manager when shutting down"""
    global _global_async_manager
    if _global_async_manager:
        await _global_async_manager.close()
        _global_async_manager = None
