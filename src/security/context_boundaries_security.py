"""
Context Boundaries Security Enhancement Module

This module implements comprehensive user privacy controls and consent management
for cross-context memory sharing to address "Insufficient Context Boundaries" 
vulnerability (CVSS 6.8).

SECURITY FEATURES:
- User privacy preference management
- Cross-context consent controls  
- Context-aware response filtering
- Granular privacy settings per context type
- Audit trail for privacy decisions

VULNERABILITY ADDRESSED: Insufficient Context Boundaries (CVSS 6.8)
"""

import logging
import json
import os
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class PrivacyLevel(Enum):
    """User privacy preference levels"""
    STRICT = "strict"           # Only same context
    MODERATE = "moderate"       # Same context + cross-server safe
    PERMISSIVE = "permissive"   # All compatible contexts
    CUSTOM = "custom"           # User-defined rules

class ConsentStatus(Enum):
    """User consent status for cross-context sharing"""
    NOT_ASKED = "not_asked"
    GRANTED = "granted"
    DENIED = "denied"
    EXPIRED = "expired"

@dataclass
class PrivacyPreferences:
    """User privacy preferences for context boundaries"""
    user_id: str
    privacy_level: PrivacyLevel = PrivacyLevel.MODERATE
    allow_cross_server: bool = False
    allow_dm_to_server: bool = False
    allow_server_to_dm: bool = False
    allow_private_to_public: bool = False
    custom_rules: Optional[Dict[str, bool]] = None
    consent_status: ConsentStatus = ConsentStatus.NOT_ASKED
    consent_timestamp: Optional[str] = None
    updated_timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.custom_rules is None:
            self.custom_rules = {}
        if self.updated_timestamp is None:
            self.updated_timestamp = datetime.now().isoformat()

@dataclass
class ContextBoundaryDecision:
    """Audit record for context boundary decisions"""
    user_id: str
    request_timestamp: str
    source_context: str
    target_context: str
    decision: str  # "allowed", "blocked", "consent_required"
    reason: str
    privacy_level: str
    
class ContextBoundariesManager:
    """
    Manager for user privacy preferences and context boundary enforcement
    """
    
    def __init__(self, data_dir: str = "./privacy_data"):
        """Initialize context boundaries manager"""
        self.data_dir = data_dir
        self.preferences_file = os.path.join(data_dir, "user_privacy_preferences.json")
        self.audit_file = os.path.join(data_dir, "context_boundary_audit.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing preferences
        self.user_preferences = self._load_preferences()
        
        # Default privacy rules matrix
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
        
        logger.info("Context boundaries manager initialized")
    
    def _load_preferences(self) -> Dict[str, PrivacyPreferences]:
        """Load user privacy preferences from disk"""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r') as f:
                    data = json.load(f)
                    preferences = {}
                    for user_id, pref_data in data.items():
                        # Handle enum conversion
                        if 'privacy_level' in pref_data:
                            pref_data['privacy_level'] = PrivacyLevel(pref_data['privacy_level'])
                        if 'consent_status' in pref_data:
                            pref_data['consent_status'] = ConsentStatus(pref_data['consent_status'])
                        
                        preferences[user_id] = PrivacyPreferences(**pref_data)
                    
                    logger.info(f"Loaded privacy preferences for {len(preferences)} users")
                    return preferences
        except Exception as e:
            logger.error(f"Error loading privacy preferences: {e}")
        
        return {}
    
    def _save_preferences(self):
        """Save user privacy preferences to disk"""
        try:
            # Convert to serializable format
            data = {}
            for user_id, prefs in self.user_preferences.items():
                pref_dict = asdict(prefs)
                # Convert enums to strings
                pref_dict['privacy_level'] = prefs.privacy_level.value
                pref_dict['consent_status'] = prefs.consent_status.value
                data[user_id] = pref_dict
            
            with open(self.preferences_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved privacy preferences for {len(data)} users")
        except Exception as e:
            logger.error(f"Error saving privacy preferences: {e}")
    
    def _log_decision(self, user_id: str, source_context: str, target_context: str, 
                     decision: str, reason: str, privacy_level: str):
        """Log context boundary decision for audit trail"""
        try:
            audit_record = ContextBoundaryDecision(
                user_id=user_id,
                request_timestamp=datetime.now().isoformat(),
                source_context=source_context,
                target_context=target_context,
                decision=decision,
                reason=reason,
                privacy_level=privacy_level
            )
            
            # Load existing audit log
            audit_log = []
            if os.path.exists(self.audit_file):
                try:
                    with open(self.audit_file, 'r') as f:
                        audit_log = json.load(f)
                except:
                    audit_log = []
            
            # Add new record
            audit_log.append(asdict(audit_record))
            
            # Keep only last 1000 records per user
            user_records = [r for r in audit_log if r['user_id'] == user_id]
            other_records = [r for r in audit_log if r['user_id'] != user_id]
            
            if len(user_records) > 1000:
                user_records = user_records[-1000:]
            
            audit_log = other_records + user_records
            
            # Save audit log
            with open(self.audit_file, 'w') as f:
                json.dump(audit_log, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging context boundary decision: {e}")
    
    def get_user_preferences(self, user_id: str) -> PrivacyPreferences:
        """Get user privacy preferences, creating defaults if needed"""
        if user_id not in self.user_preferences:
            # Create default preferences
            self.user_preferences[user_id] = PrivacyPreferences(
                user_id=user_id,
                privacy_level=PrivacyLevel.MODERATE,  # Safe default
                consent_status=ConsentStatus.NOT_ASKED
            )
            self._save_preferences()
        
        return self.user_preferences[user_id]
    
    def update_user_preferences(self, user_id: str, **updates) -> bool:
        """Update user privacy preferences"""
        try:
            prefs = self.get_user_preferences(user_id)
            
            # Update fields
            for field, value in updates.items():
                if hasattr(prefs, field):
                    # Handle enum conversions
                    if field == 'privacy_level' and isinstance(value, str):
                        value = PrivacyLevel(value)
                    elif field == 'consent_status' and isinstance(value, str):
                        value = ConsentStatus(value)
                    
                    setattr(prefs, field, value)
            
            # Update timestamp
            prefs.updated_timestamp = datetime.now().isoformat()
            
            self._save_preferences()
            logger.info(f"Updated privacy preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    def request_consent(self, user_id: str, source_context: str, target_context: str) -> Dict[str, Any]:
        """
        Generate consent request for cross-context memory sharing
        
        Returns:
            Dict with consent request information
        """
        prefs = self.get_user_preferences(user_id)
        
        consent_request = {
            "user_id": user_id,
            "consent_required": True,
            "source_context": source_context,
            "target_context": target_context,
            "current_privacy_level": prefs.privacy_level.value,
            "consent_status": prefs.consent_status.value,
            "message": self._generate_consent_message(source_context, target_context),
            "options": [
                {"key": "allow_once", "label": "Allow once"},
                {"key": "allow_always", "label": "Always allow this type of sharing"},
                {"key": "deny_once", "label": "Deny this request"},
                {"key": "deny_always", "label": "Never allow this type of sharing"},
                {"key": "privacy_settings", "label": "Adjust privacy settings"}
            ]
        }
        
        # Log the consent request
        self._log_decision(user_id, source_context, target_context, "consent_requested", 
                          "User consent required for cross-context sharing", prefs.privacy_level.value)
        
        return consent_request
    
    def _generate_consent_message(self, source_context: str, target_context: str) -> str:
        """Generate user-friendly consent message"""
        context_names = {
            "dm": "direct messages",
            "public_channel": "public server channels", 
            "private_channel": "private server channels",
            "cross_server": "different servers"
        }
        
        source_name = context_names.get(source_context, source_context)
        target_name = context_names.get(target_context, target_context)
        
        return (f"🔒 **Privacy Notice**: I have information from your {source_name} "
                f"that might be relevant to this {target_name} conversation. "
                f"Would you like me to use that information here?")
    
    def process_consent_response(self, user_id: str, response: str, 
                               source_context: str, target_context: str) -> Dict[str, Any]:
        """Process user consent response"""
        try:
            prefs = self.get_user_preferences(user_id)
            
            result = {
                "user_id": user_id,
                "response": response,
                "memory_sharing_allowed": False,
                "preferences_updated": False
            }
            
            if response == "allow_once":
                result["memory_sharing_allowed"] = True
                self._log_decision(user_id, source_context, target_context, "allowed_once",
                                 "User granted one-time consent", prefs.privacy_level.value)
            
            elif response == "allow_always":
                # Update preferences to allow this type of sharing
                rule_key = f"{source_context}_to_{target_context}"
                if prefs.custom_rules is None:
                    prefs.custom_rules = {}
                prefs.custom_rules[rule_key] = True
                prefs.consent_status = ConsentStatus.GRANTED
                prefs.consent_timestamp = datetime.now().isoformat()
                
                result["memory_sharing_allowed"] = True
                result["preferences_updated"] = True
                
                self._log_decision(user_id, source_context, target_context, "allowed_always",
                                 "User granted permanent consent", prefs.privacy_level.value)
            
            elif response == "deny_once":
                result["memory_sharing_allowed"] = False
                self._log_decision(user_id, source_context, target_context, "denied_once",
                                 "User denied one-time request", prefs.privacy_level.value)
            
            elif response == "deny_always":
                # Update preferences to block this type of sharing
                rule_key = f"{source_context}_to_{target_context}"
                if prefs.custom_rules is None:
                    prefs.custom_rules = {}
                prefs.custom_rules[rule_key] = False
                prefs.consent_status = ConsentStatus.DENIED
                prefs.consent_timestamp = datetime.now().isoformat()
                
                result["memory_sharing_allowed"] = False
                result["preferences_updated"] = True
                
                self._log_decision(user_id, source_context, target_context, "denied_always",
                                 "User denied permanent consent", prefs.privacy_level.value)
            
            self._save_preferences()
            return result
            
        except Exception as e:
            logger.error(f"Error processing consent response: {e}")
            return {"error": str(e)}
    
    def check_context_boundary_permission(self, user_id: str, source_context: str, 
                                        target_context: str, memory_sensitivity: str = "normal") -> Dict[str, Any]:
        """
        Check if cross-context memory sharing is allowed for user
        
        Args:
            user_id: User ID
            source_context: Context where memory was created
            target_context: Current context
            memory_sensitivity: Sensitivity level of memory content
            
        Returns:
            Dict with decision and reason
        """
        try:
            prefs = self.get_user_preferences(user_id)
            
            # Same context is always allowed
            if source_context == target_context:
                return {
                    "allowed": True,
                    "reason": "same_context",
                    "requires_consent": False
                }
            
            # Check custom rules first
            rule_key = f"{source_context}_to_{target_context}"
            if prefs.custom_rules and rule_key in prefs.custom_rules:
                allowed = prefs.custom_rules[rule_key]
                self._log_decision(user_id, source_context, target_context, 
                                 "allowed" if allowed else "blocked",
                                 f"Custom rule: {rule_key}", prefs.privacy_level.value)
                
                return {
                    "allowed": allowed,
                    "reason": "custom_rule",
                    "requires_consent": False
                }
            
            # Apply privacy level rules
            if prefs.privacy_level == PrivacyLevel.CUSTOM:
                # Custom level with no specific rule - require consent
                return {
                    "allowed": False,
                    "reason": "custom_consent_required",
                    "requires_consent": True
                }
            
            # Get default rules for privacy level
            rules = self.default_compatibility_rules.get(prefs.privacy_level, {})
            
            # Check specific context transitions
            transition_key = f"{source_context}_to_{target_context}"
            
            # Map common transitions to rule keys
            rule_mapping = {
                "dm_to_public_channel": "dm_to_server",
                "dm_to_private_channel": "dm_to_server", 
                "public_channel_to_dm": "server_to_dm",
                "private_channel_to_dm": "server_to_dm",
                "private_channel_to_public_channel": "private_to_public",
                "public_channel_to_private_channel": "public_to_private"
            }
            
            # Check cross-server scenarios
            if "server" in source_context and "server" in target_context:
                rule_key = "cross_server"
            else:
                rule_key = rule_mapping.get(transition_key, transition_key)
            
            allowed = rules.get(rule_key, False)
            
            # High sensitivity memories require stricter controls
            if memory_sensitivity == "high" and allowed:
                if prefs.privacy_level != PrivacyLevel.PERMISSIVE:
                    return {
                        "allowed": False,
                        "reason": "high_sensitivity_blocked",
                        "requires_consent": True
                    }
            
            self._log_decision(user_id, source_context, target_context,
                             "allowed" if allowed else "blocked",
                             f"Privacy level {prefs.privacy_level.value} rule: {rule_key}",
                             prefs.privacy_level.value)
            
            return {
                "allowed": allowed,
                "reason": f"privacy_level_{prefs.privacy_level.value}",
                "requires_consent": not allowed and prefs.privacy_level != PrivacyLevel.STRICT
            }
            
        except Exception as e:
            logger.error(f"Error checking context boundary permission: {e}")
            # Default to blocked for safety
            return {
                "allowed": False,
                "reason": "error_default_block",
                "requires_consent": False,
                "error": str(e)
            }
    
    def get_privacy_settings_ui(self, user_id: str) -> Dict[str, Any]:
        """Generate privacy settings UI for user"""
        prefs = self.get_user_preferences(user_id)
        
        return {
            "user_id": user_id,
            "current_settings": {
                "privacy_level": prefs.privacy_level.value,
                "allow_cross_server": prefs.allow_cross_server,
                "allow_dm_to_server": prefs.allow_dm_to_server,
                "allow_server_to_dm": prefs.allow_server_to_dm,
                "allow_private_to_public": prefs.allow_private_to_public,
                "consent_status": prefs.consent_status.value
            },
            "privacy_levels": [
                {
                    "value": "strict",
                    "label": "🔒 Strict",
                    "description": "Never share information between different contexts"
                },
                {
                    "value": "moderate", 
                    "label": "⚖️ Moderate",
                    "description": "Allow cross-server sharing of non-sensitive information"
                },
                {
                    "value": "permissive",
                    "label": "🌐 Permissive", 
                    "description": "Allow most cross-context sharing (still protects private channels)"
                },
                {
                    "value": "custom",
                    "label": "⚙️ Custom",
                    "description": "Ask for permission on each cross-context request"
                }
            ],
            "custom_rules": prefs.custom_rules,
            "last_updated": prefs.updated_timestamp
        }

def get_context_boundaries_manager() -> ContextBoundariesManager:
    """Get singleton instance of context boundaries manager"""
    if not hasattr(get_context_boundaries_manager, '_instance'):
        get_context_boundaries_manager._instance = ContextBoundariesManager()
    return get_context_boundaries_manager._instance
