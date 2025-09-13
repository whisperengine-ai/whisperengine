"""
System Message Security Module
Prevents system prompt leakage and secures system message processing.
"""

import re
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SystemMessageSecurityFilter:
    """
    Security filter for system messages to prevent information disclosure and system prompt leakage.
    """
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load security patterns from external configuration file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Log only the relative path to avoid exposing full system paths
                relative_path = os.path.relpath(self.config_path)
                logger.info(f"Loaded security configuration from {relative_path}")
                return config
            else:
                relative_path = os.path.relpath(self.config_path)
                logger.warning(f"Configuration file not found: {relative_path}, using fallback patterns")
                return {}
        except Exception as e:
            logger.error(f"Error loading security configuration: {e}, using fallback patterns")
            return {}
    
    def _get_sensitive_patterns(self) -> List[str]:
        """Get sensitive patterns from config or fallback to hardcoded ones."""
        patterns = []
        
        # Load patterns from external config
        for section_name in ["response_leakage_indicators", "xml_response_patterns", "context_variable_at_start_patterns"]:
            section = self.config.get(section_name, {})
            section_patterns = section.get("patterns", [])
            
            for pattern_def in section_patterns:
                pattern = pattern_def.get("pattern", "")
                if pattern:
                    patterns.append(pattern)
        
        # If we got patterns from config, use them
        if patterns:
            logger.info(f"Loaded {len(patterns)} patterns from external configuration")
            return patterns
        
        # Fallback to hardcoded patterns
        logger.warning("Using fallback hardcoded patterns")
        return [
        
        # System prompt structure indicators
        r'##Archive.*?##Identity',
        r'##Personality.*?##Relationships',
        r'##Memory.*?##Behavior',
        r'role.*?system.*?content',
        r'DEFAULT_SYSTEM_PROMPT',
        
        # Internal system information
        r'conversation_context\.append',
        r'memory_manager\.',
        r'ChromaDB',
        r'LLM.*?server',
        r'Discord.*?bot.*?token',
        
        # User data patterns that shouldn't be exposed
        r'user_id.*?[0-9]+',
        r'emotion_context.*?relationship.*?level',
        r'interaction_count.*?[0-9]+',
        r'pre_analyzed_emotion_data',
        
        # Configuration and internal workings
        r'debug.*?mode.*?enabled',
        r'admin.*?permissions',
        r'conversation.*?cache',
        r'bootstrap.*?limit',
        
        # JSON debug output patterns - NEW
        r'"memory_network_context"',
        r'"relationship_depth_context"',
        r'"ai_system_context"',
        r'"emotional_intelligence_context"',
        r'"emotional_state_context"',
        r'"personality_context"',
        r'"external_emotion_context"',
        r'"proactive_support_context"',
        r'"emotional_prediction_context"',
        
        # JSON structure patterns that indicate debug leakage
        r'\{[\s\n]*"[a-z_]+_context"',
        r'"[A-Z_]+_CONTEXT"',
        r'CONTEXT.*?:.*?"[^"]*"',
        
        # Debug data structure patterns
        r'Intimate Style.*?AI System.*?Context',
        
        # Context variable patterns - both in templates and responses
        r'\{MEMORY_NETWORK_CONTEXT\}',
        r'\{RELATIONSHIP_DEPTH_CONTEXT\}',
        r'\{PERSONALITY_CONTEXT\}',
        r'\{EMOTIONAL_STATE_CONTEXT\}',
        r'\{EXTERNAL_EMOTION_CONTEXT\}',
        r'\{EMOTIONAL_PREDICTION_CONTEXT\}',
        r'\{RELATIONSHIP_CONTEXT\}',
        r'\{PROACTIVE_SUPPORT_CONTEXT\}',
        r'\{EMOTIONAL_INTELLIGENCE_CONTEXT\}',
        r'\{AI_SYSTEM_CONTEXT\}',
        
        # SYSTEM_INFORMATION_FILTERED patterns - these indicate already filtered content is leaking
        r'\[SYSTEM_INFORMATION_FILTERED\]',
        r'SYSTEM_INFORMATION_FILTERED',
        ]
    
    # Replacement patterns for sensitive content
    SAFE_REPLACEMENTS = {
        
        # System structure -> safe markers
        r'##[A-Za-z]+': '[SECTION]',
        r'role.*?system.*?content': '[SYSTEM_MESSAGE]',
        r'DEFAULT_SYSTEM_PROMPT': '[SYSTEM_PROMPT]',
        
        # Technical details -> generic markers
        r'conversation_context\.append.*?\n': '[CONTEXT_PROCESSING]\n',
        r'memory_manager\.[a-zA-Z_]+': '[MEMORY_OPERATION]',
        r'ChromaDB.*?collection': '[DATABASE_OPERATION]',
        
        # User data -> privacy markers
        r'user_id:\s*[0-9]+': 'user_id: [PROTECTED]',
        r'emotion_context:.*?\n': 'emotion_context: [PROTECTED]\n',
        r'interaction_count:\s*[0-9]+': 'interaction_count: [PROTECTED]',
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the system message security filter with external configuration."""
        if config_path is None:
            # Get project root directory dynamically
            project_root = Path(__file__).parent.parent.parent
            config_path = str(project_root / "config" / "security" / "response_leakage_patterns.json")
        
        self.config_path = config_path
        self.config = self._load_configuration()
        
        # Load patterns from config or use hardcoded ones as fallback
        self.SENSITIVE_PATTERNS = self._get_sensitive_patterns()
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                 for pattern in self.SENSITIVE_PATTERNS]
        self.compiled_replacements = {
            re.compile(pattern, re.IGNORECASE | re.DOTALL): replacement
            for pattern, replacement in self.SAFE_REPLACEMENTS.items()
        }
        logger.info("SystemMessageSecurityFilter initialized with configuration")
    
    def sanitize_system_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sanitize system messages to remove sensitive information while preserving functionality.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Sanitized messages with sensitive content removed/replaced
        """
        sanitized_messages = []
        
        for message in messages:
            if message.get('role') != 'system':
                # Non-system messages pass through unchanged
                sanitized_messages.append(message.copy())
                continue
            
            # Sanitize system message content
            content = message.get('content', '')
            if not content:
                continue  # Skip empty system messages
            
            sanitized_content = self._sanitize_system_content(content)
            
            # Only include system message if it has safe content after sanitization
            if sanitized_content and sanitized_content.strip():
                sanitized_message = message.copy()
                sanitized_message['content'] = sanitized_content
                sanitized_messages.append(sanitized_message)
                logger.debug(f"Sanitized system message: {len(content)} -> {len(sanitized_content)} chars")
            else:
                logger.warning("System message completely filtered out due to sensitive content")
        
        return sanitized_messages
    
    def _sanitize_system_content(self, content: str) -> str:
        """
        Sanitize system message content to remove sensitive information.
        
        Args:
            content: System message content
            
        Returns:
            Sanitized content with sensitive information removed/replaced
        """
        sanitized = content
        
        # Apply safe replacements first (preserve functionality while hiding details)
        for pattern, replacement in self.compiled_replacements.items():
            sanitized = pattern.sub(replacement, sanitized)
        
        # Remove any remaining sensitive patterns
        for pattern in self.compiled_patterns:
            if pattern.search(sanitized):
                logger.warning(f"Removing sensitive pattern from system message: {pattern.pattern[:50]}...")
                sanitized = pattern.sub('[SENSITIVE_CONTENT_REMOVED]', sanitized)
        
        # Clean up multiple consecutive markers
        sanitized = re.sub(r'\[SENSITIVE_CONTENT_REMOVED\]\s*\[SENSITIVE_CONTENT_REMOVED\]', 
                          '[SENSITIVE_CONTENT_REMOVED]', sanitized)
        
        return sanitized
    
    def scan_response_for_leakage(self, response: str) -> Dict[str, Any]:
        """
        Scan bot response for potential system message leakage.
        
        Args:
            response: Bot response text to scan
            
        Returns:
            Dict with leakage detection results:
            - 'has_leakage': Boolean indicating if leakage detected
            - 'leaked_patterns': List of patterns that were detected
            - 'sanitized_response': Response with leakage removed
        """
        leaked_patterns = []
        sanitized_response = response
        
        # Check for sensitive pattern leakage
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(response)
            if matches:
                pattern_name = self.SENSITIVE_PATTERNS[i]
                leaked_patterns.append(pattern_name)
                
                # Remove the leaked content from response
                sanitized_response = pattern.sub('[SYSTEM_INFORMATION_FILTERED]', sanitized_response)
                
                logger.error(f"SECURITY: System message leakage detected: {pattern_name}")
                logger.error(f"SECURITY: Leaked content: {matches}")
        
        # Additional checks for common leakage indicators
        leakage_indicators = [
            r'Previous conversation context:',
            r'Global Facts.*?about the world',
            r'User-specific information:',
            r'Current time:.*?UTC',
            r'emotional context:.*?relationship',
            # JSON debug output indicators - NEW
            r'"memory_network_context".*?:',
            # XML response tag wrapping - SECURITY FIX
            r'^<response>\s*',
            r'\s*</response>$',
            r'"relationship_depth_context".*?:',
            r'"ai_system_context".*?:',
            r'"emotional_intelligence_context".*?:',
            r'Intimate Mode.*?context',
            r'Memory Network.*?Status.*?:',
            r'Relationship Depth.*?:.*?(Friend|Close|Eternal)',
            r'AI System.*?:.*?Human-like',
            r'External Emotion Analysis.*?Tier',
            # Generic JSON context structure
            r'\{\s*"\w+_context"\s*:',
            r'"[a-z_]+_context"\s*:\s*"[^"]*"',
        ]
        
        for indicator in leakage_indicators:
            if re.search(indicator, response, re.IGNORECASE):
                leaked_patterns.append(f"Context leakage: {indicator}")
                sanitized_response = re.sub(indicator, '[CONTEXT_FILTERED]', sanitized_response, flags=re.IGNORECASE)
                logger.warning(f"SECURITY: Context leakage detected: {indicator}")
        
        # Additional XML response tag cleaning - handle complete tag wrapping
        if re.match(r'^\s*<response>\s*.*\s*</response>\s*$', sanitized_response, re.DOTALL):
            logger.warning("SECURITY: Complete XML response tag wrapping detected - removing tags")
            leaked_patterns.append("XML response tag wrapping")
            # Remove both opening and closing tags
            sanitized_response = re.sub(r'^\s*<response>\s*', '', sanitized_response)
            sanitized_response = re.sub(r'\s*</response>\s*$', '', sanitized_response)
            sanitized_response = sanitized_response.strip()
        
        return {
            'has_leakage': len(leaked_patterns) > 0,
            'leaked_patterns': leaked_patterns,
            'sanitized_response': sanitized_response
        }
    
    def create_secure_system_message(self, content: str, message_type: str = "general") -> Dict[str, str]:
        """
        Create a secure system message with minimal sensitive information.
        
        Args:
            content: Content for the system message
            message_type: Type of system message (general, time, emotion, memory)
            
        Returns:
            Secure system message dictionary
        """
        # Different security levels for different message types
        if message_type == "character":
            # For character/identity messages, use minimal safe description
            safe_content = "You are a helpful AI assistant with a thoughtful and caring personality."
            
        elif message_type == "time":
            # Time messages are generally safe but remove detailed formatting
            safe_content = content  # Time context is usually safe
            
        elif message_type == "emotion":
            # Emotion messages should be generic to prevent user data leakage
            safe_content = "Consider the user's emotional context when responding with empathy and understanding."
            
        elif message_type == "memory":
            # Memory messages should be heavily sanitized
            safe_content = "Use relevant background context when appropriate for the conversation."
            
        else:
            # General system messages - sanitize content
            safe_content = self._sanitize_system_content(content)
        
        return {"role": "system", "content": safe_content}
    
    def log_system_message_security_event(self, event_type: str, details: str, severity: str = "WARNING"):
        """
        Log system message security events.
        
        Args:
            event_type: Type of security event
            details: Event details
            severity: Severity level
        """
        log_message = f"SYSTEM_MESSAGE_SECURITY [{severity}] - {event_type}: {details}"
        
        if severity == "CRITICAL":
            logger.critical(log_message)
        elif severity == "ERROR":
            logger.error(log_message)
        elif severity == "WARNING":
            logger.warning(log_message)
        else:
            logger.info(log_message)


# Global instance for easy access
system_message_filter = SystemMessageSecurityFilter()


def sanitize_system_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function for sanitizing system messages.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Sanitized messages
    """
    return system_message_filter.sanitize_system_messages(messages)


def scan_response_for_system_leakage(response: str) -> Dict[str, Any]:
    """
    Convenience function for scanning responses for system message leakage.
    
    Args:
        response: Bot response to scan
        
    Returns:
        Leakage detection results
    """
    return system_message_filter.scan_response_for_leakage(response)


def create_secure_system_message(content: str, message_type: str = "general") -> Dict[str, str]:
    """
    Convenience function for creating secure system messages.
    
    Args:
        content: System message content
        message_type: Type of system message
        
    Returns:
        Secure system message
    """
    return system_message_filter.create_secure_system_message(content, message_type)
