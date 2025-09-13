#!/usr/bin/env python3
"""
Debug Mode Security Enhancement Module
Addresses CVSS 7.1 vulnerability - Debug Mode Information Disclosure

This module provides secure debug logging that prevents sensitive user information
from being exposed in logs while maintaining useful debugging capabilities.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum
import hashlib
import re

logger = logging.getLogger(__name__)

class DebugSensitivityLevel(Enum):
    """Define sensitivity levels for debug information"""
    PUBLIC = "public"           # Safe for any log level
    INTERNAL = "internal"       # Safe for DEBUG level only
    SENSITIVE = "sensitive"     # Should be masked/hashed
    PRIVATE = "private"         # Should never be logged

class SecureDebugLogger:
    """
    Secure debug logger that sanitizes sensitive information before logging
    """
    
    def __init__(self, enable_debug_mode: bool = False):
        self.enable_debug_mode = enable_debug_mode
        self.user_id_cache = {}  # Cache for user ID hashing
        
    def hash_user_id(self, user_id: str) -> str:
        """Create a consistent hash for user ID that can be used for debugging"""
        if user_id in self.user_id_cache:
            return self.user_id_cache[user_id]
        
        # Create a short hash for debugging purposes
        hash_obj = hashlib.sha256(user_id.encode())
        short_hash = hash_obj.hexdigest()[:8]  # Use first 8 characters
        hashed_id = f"user_{short_hash}"
        
        self.user_id_cache[user_id] = hashed_id
        return hashed_id
    
    def sanitize_username(self, username: str) -> str:
        """Sanitize username for safe logging"""
        if not self.enable_debug_mode:
            return "[username_hidden]"
        
        # In debug mode, show partial username
        if len(username) <= 3:
            return "[username_short]"
        
        # Show first 2 and last 1 characters with asterisks in between
        return f"{username[:2]}{'*' * (len(username) - 3)}{username[-1]}"
    
    def sanitize_sensitive_data(self, data: str) -> str:
        """Remove or mask sensitive data patterns from strings"""
        if not data:
            return data
        
        # Common sensitive patterns to mask (removed word boundaries for better matching)
        sensitive_patterns = [
            (r'\d{3}-\d{2}-\d{4}', '[SSN_MASKED]'),           # SSN
            (r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}', '[CARD_MASKED]'),  # Credit card
            (r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', '[EMAIL_MASKED]'),  # Email
            (r'((?:password|pass|pwd)[\s:=]+)\S+', r'\1[PASSWORD_MASKED]'),  # Password with capture group
            (r'((?:token|key|secret)[\s:=]+)\S+', r'\1[TOKEN_MASKED]'),  # API keys/tokens with capture group
        ]
        
        sanitized = data
        for pattern, replacement in sensitive_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def log_user_debug_info(self, user_id: str, debug_data: Dict[str, Any], 
                           message_id: Optional[str] = None):
        """
        Log user debug information securely
        
        Args:
            user_id: User ID to log debug info for
            debug_data: Dictionary containing debug information
            message_id: Optional message ID for context
        """
        if not self.enable_debug_mode:
            # In production, only log minimal information
            logger.debug("User debug info collected (details hidden in production)")
            return
        
        # Create secure debug info
        hashed_user = self.hash_user_id(user_id)
        hashed_message = f"msg_{hashlib.sha256(message_id.encode()).hexdigest()[:8]}" if message_id else "no_msg"
        
        # Sanitize debug data
        secure_debug = {}
        for key, value in debug_data.items():
            if key in ['emotion', 'relationship_level']:
                # These are enums/safe values, but still mark as internal
                secure_debug[key] = str(value)
            elif key in ['interaction_count', 'escalation_count']:
                # Numeric values are generally safe
                secure_debug[key] = value
            elif key == 'name':
                # Names should be sanitized
                secure_debug[key] = self.sanitize_username(str(value)) if value else None
            else:
                # Unknown fields - sanitize for safety
                secure_debug[key] = self.sanitize_sensitive_data(str(value))
        
        # Log at DEBUG level with hashed identifiers
        logger.debug(f"USER_DEBUG [{hashed_user}] [{hashed_message}] - {secure_debug}")
    
    def log_user_activity(self, user_id: str, activity: str, details: Optional[str] = None):
        """
        Log user activity securely
        
        Args:
            user_id: User ID
            activity: Activity description (should be non-sensitive)
            details: Optional details (will be sanitized)
        """
        if not self.enable_debug_mode:
            return
        
        hashed_user = self.hash_user_id(user_id)
        safe_details = self.sanitize_sensitive_data(details) if details else ""
        
        logger.debug(f"USER_ACTIVITY [{hashed_user}] - {activity} {safe_details}".strip())
    
    def log_system_debug(self, component: str, message: str, sensitive_data: Optional[Dict] = None):
        """
        Log system debug information securely
        
        Args:
            component: Component name
            message: Debug message
            sensitive_data: Optional sensitive data to be sanitized
        """
        if not self.enable_debug_mode:
            return
        
        safe_message = self.sanitize_sensitive_data(message)
        
        if sensitive_data:
            safe_data = {k: self.sanitize_sensitive_data(str(v)) for k, v in sensitive_data.items()}
            logger.debug(f"SYSTEM_DEBUG [{component}] - {safe_message} | Data: {safe_data}")
        else:
            logger.debug(f"SYSTEM_DEBUG [{component}] - {safe_message}")

# Global secure debug logger instance
_secure_debug_logger = None

def get_secure_debug_logger(enable_debug_mode: bool = False) -> SecureDebugLogger:
    """Get or create the global secure debug logger instance"""
    global _secure_debug_logger
    if _secure_debug_logger is None:
        _secure_debug_logger = SecureDebugLogger(enable_debug_mode)
    return _secure_debug_logger

def secure_add_debug_info_to_response(response: str, user_id: str, memory_manager, 
                                    message_id: Optional[str] = None, 
                                    enable_debug_mode: bool = False) -> str:
    """
    Secure version of add_debug_info_to_response that doesn't expose sensitive information
    
    Args:
        response: Original bot response
        user_id: User ID for debug context
        memory_manager: Memory manager instance
        message_id: Optional message ID
        enable_debug_mode: Whether debug mode is enabled
        
    Returns:
        Original response (debug info is logged securely, not added to response)
    """
    if not enable_debug_mode:
        return response
    
    # Get secure debug logger
    debug_logger = get_secure_debug_logger(enable_debug_mode)
    
    # Prevent duplicate processing
    if message_id:
        message_key = f"{user_id}_{message_id}"
        # Use a simple set to track processed messages (could be made more sophisticated)
        if hasattr(secure_add_debug_info_to_response, '_processed_messages'):
            if message_key in secure_add_debug_info_to_response._processed_messages:
                debug_logger.log_system_debug("debug", f"Skipping duplicate debug processing for message", 
                                           {"user_hash": debug_logger.hash_user_id(user_id)})
                return response
        else:
            secure_add_debug_info_to_response._processed_messages = set()
        
        secure_add_debug_info_to_response._processed_messages.add(message_key)
        
        # Clean up old entries
        if len(secure_add_debug_info_to_response._processed_messages) > 100:
            secure_add_debug_info_to_response._processed_messages.clear()
    
    try:
        # Get emotion context safely
        if hasattr(memory_manager, 'get_user_emotion_profile') and memory_manager.enable_emotions:
            profile = memory_manager.get_user_emotion_profile(user_id)
            if profile:
                debug_data = {
                    'emotion': profile.current_emotion.value.title(),
                    'relationship_level': profile.relationship_level.value.title(),
                    'interaction_count': profile.interaction_count
                }
                
                if profile.escalation_count >= 3:
                    debug_data['escalation_count'] = profile.escalation_count
                
                if profile.name:
                    debug_data['name'] = profile.name
                
                # Log securely
                debug_logger.log_user_debug_info(user_id, debug_data, message_id)
            else:
                debug_logger.log_user_activity(user_id, "emotion_profile_unavailable")
        else:
            debug_logger.log_system_debug("emotion", "Emotion system not available")
            
    except Exception as e:
        # Log error securely without exposing user data
        debug_logger.log_system_debug("debug", f"Error retrieving debug info: {str(e)}")
    
    # Always return original response - debug info is logged, not added to response
    return response

def secure_log_user_info(user, memory_manager, enable_debug_mode: bool = False):
    """
    Securely log Discord user information without exposing sensitive details
    
    Args:
        user: Discord user object
        memory_manager: Memory manager instance
        enable_debug_mode: Whether debug mode is enabled
    """
    if not enable_debug_mode:
        return
    
    debug_logger = get_secure_debug_logger(enable_debug_mode)
    
    try:
        user_id = str(user.id)
        username = str(user)
        
        # Log with sanitized information
        debug_logger.log_user_activity(
            user_id, 
            "discord_user_info_available", 
            f"username: {debug_logger.sanitize_username(username)}"
        )
        
    except Exception as e:
        debug_logger.log_system_debug("discord", f"Failed to process Discord user info: {str(e)}")

def secure_log_server_info(guild, memory_manager, enable_debug_mode: bool = False):
    """
    Securely log Discord server information without exposing sensitive details
    
    Args:
        guild: Discord guild object
        memory_manager: Memory manager instance
        enable_debug_mode: Whether debug mode is enabled
    """
    if not enable_debug_mode:
        return
    
    debug_logger = get_secure_debug_logger(enable_debug_mode)
    
    try:
        if guild:
            # Guild names are generally not sensitive, but sanitize just in case
            safe_guild_name = debug_logger.sanitize_sensitive_data(guild.name)
            guild_hash = hashlib.sha256(str(guild.id).encode()).hexdigest()[:8]
            
            debug_logger.log_system_debug(
                "discord", 
                f"Server info available: guild_{guild_hash}",
                {"guild_name": safe_guild_name}
            )
            
    except Exception as e:
        debug_logger.log_system_debug("discord", f"Failed to process Discord server info: {str(e)}")

# Test functions to validate the security enhancements
def test_secure_debug_logging():
    """Test the secure debug logging functionality"""
    print("🧪 Testing secure debug logging...")
    
    # Test with debug mode enabled
    debug_logger = SecureDebugLogger(enable_debug_mode=True)
    
    # Test user ID hashing
    user_id = "123456789"
    hashed = debug_logger.hash_user_id(user_id)
    print(f"  User ID {user_id} -> {hashed}")
    
    # Test username sanitization
    username = "sensitive_user@example.com"
    sanitized = debug_logger.sanitize_username(username)
    print(f"  Username {username} -> {sanitized}")
    
    # Test sensitive data sanitization
    sensitive_text = "My SSN is 123-45-6789 and my email is user@example.com"
    sanitized_text = debug_logger.sanitize_sensitive_data(sensitive_text)
    print(f"  Sensitive: {sensitive_text}")
    print(f"  Sanitized: {sanitized_text}")
    
    # Test debug logging
    debug_data = {
        'emotion': 'happy',
        'relationship_level': 'friendly',
        'interaction_count': 42,
        'name': 'TestUser123'
    }
    
    debug_logger.log_user_debug_info(user_id, debug_data, "test_message_123")
    
    print("✅ Secure debug logging test complete")

if __name__ == "__main__":
    # Run tests if executed directly
    test_secure_debug_logging()
