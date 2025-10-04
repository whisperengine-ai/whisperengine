"""
CDL Manager - Singleton for Character Definition Language Data Access

Provides lazy-loaded, in-memory access to CDL character data with:
- Singleton pattern for single file load
- Generic field access via dot notation or dict-style
- Schema validation and error handling
- Thread-safe access
- Clean separation from parsing logic
"""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CDLFieldAccess:
    """Result of CDL field access with metadata"""
    value: Any
    exists: bool
    path: str
    
    def __bool__(self):
        """Allow direct boolean evaluation"""
        return self.exists and self.value is not None


class CDLManager:
    """
    Singleton manager for Character Definition Language data access.
    
    Features:
    - Lazy loading from CDL_DEFAULT_CHARACTER environment variable
    - Thread-safe singleton pattern
    - Generic field access with dot notation or dict-style paths
    - Schema validation and error handling
    - In-memory caching for performance
    
    Usage:
        cdl = CDLManager.get_instance()
        
        # Access conversation flow guidelines
        flow_guidelines = cdl.get_field("character.conversation_flow_guidelines")
        
        # Access with default fallback
        max_length = cdl.get_field("character.conversation_flow_guidelines.platform_awareness.discord.max_response_length", 
                                   default="1-2 messages")
        
        # Check if field exists
        if cdl.has_field("character.conversation_flow_guidelines"):
            guidelines = cdl.get_field("character.conversation_flow_guidelines")
        
        # Get character name
        name = cdl.get_field("character.metadata.name", default="Unknown")
    """
    
    _instance = None
    _lock = threading.Lock()
    _data: Optional[Dict[str, Any]] = None
    _character_file: Optional[str] = None
    _loaded = False
    _character_object: Optional[Any] = None  # Cached Character object from parser
    
    def __new__(cls):
        """Thread-safe singleton implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CDLManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'CDLManager':
        """Get the singleton instance"""
        return cls()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton for testing purposes"""
        with cls._lock:
            cls._instance = None
            cls._data = None
            cls._character_file = None
            cls._loaded = False
            cls._character_object = None  # Clear cached Character object
    
    def _load_character_data(self) -> None:
        """Lazy load character data from CDL_DEFAULT_CHARACTER environment variable"""
        if self._loaded:
            return
            
        with self._lock:
            if self._loaded:  # Double-check locking
                return
                
            try:
                character_file = os.getenv('CDL_DEFAULT_CHARACTER', '')
                if not character_file:
                    logger.warning("CDL_DEFAULT_CHARACTER environment variable not set")
                    self._data = {}
                    self._loaded = True
                    return
                
                character_path = Path(character_file)
                if not character_path.exists():
                    logger.error(f"Character file not found: {character_file}")
                    self._data = {}
                    self._loaded = True
                    return
                
                with open(character_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                    self._character_file = character_file
                    logger.info(f"✅ CDL Manager: Loaded character data from {character_file}")
                    
                # Basic schema validation
                self._validate_schema()
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ CDL Manager: JSON decode error in {character_file}: {e}")
                self._data = {}
            except Exception as e:
                logger.error(f"❌ CDL Manager: Error loading character data: {e}")
                self._data = {}
            finally:
                self._loaded = True
    
    def _validate_schema(self) -> None:
        """Basic schema validation for CDL structure"""
        if not isinstance(self._data, dict):
            raise ValueError("CDL data must be a dictionary")
        
        if 'character' not in self._data:
            logger.warning("CDL data missing 'character' root key")
        
        # Validate character metadata if present
        character_data = self._data.get('character', {})
        if 'metadata' in character_data:
            metadata = character_data['metadata']
            if not isinstance(metadata, dict):
                logger.warning("CDL character.metadata is not a dictionary")
            elif 'name' not in metadata:
                logger.warning("CDL character.metadata missing 'name' field")
    
    def get_field(self, field_path: str, default: Any = None) -> Any:
        """
        Get a field value using dot notation path.
        
        Args:
            field_path: Dot-separated path like "character.metadata.name"
            default: Default value if field doesn't exist
            
        Returns:
            Field value or default
            
        Examples:
            name = cdl.get_field("character.metadata.name")
            flow_guidelines = cdl.get_field("character.conversation_flow_guidelines")
            max_length = cdl.get_field("character.conversation_flow_guidelines.platform_awareness.discord.max_response_length")
        """
        self._load_character_data()
        
        if not self._data:
            return default
        
        try:
            current = self._data
            parts = field_path.split('.')
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            
            return current
            
        except Exception as e:
            logger.debug(f"Error accessing field '{field_path}': {e}")
            return default
    
    def get_field_with_metadata(self, field_path: str, default: Any = None) -> CDLFieldAccess:
        """
        Get field value with access metadata.
        
        Returns:
            CDLFieldAccess object with value, exists flag, and path
        """
        self._load_character_data()
        
        if not self._data:
            return CDLFieldAccess(value=default, exists=False, path=field_path)
        
        try:
            current = self._data
            parts = field_path.split('.')
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return CDLFieldAccess(value=default, exists=False, path=field_path)
            
            return CDLFieldAccess(value=current, exists=True, path=field_path)
            
        except Exception as e:
            logger.debug(f"Error accessing field '{field_path}': {e}")
            return CDLFieldAccess(value=default, exists=False, path=field_path)
    
    def has_field(self, field_path: str) -> bool:
        """Check if a field exists in the CDL data"""
        return self.get_field_with_metadata(field_path).exists
    
    def get_character_name(self) -> str:
        """Convenience method to get character name"""
        return self.get_field("character.metadata.name", default="Unknown")
    
    def get_character_occupation(self) -> str:
        """Convenience method to get character occupation"""
        return self.get_field("character.identity.occupation", default="")
    
    def get_conversation_flow_guidelines(self) -> Dict[str, Any]:
        """Convenience method to get conversation flow guidelines - UNIFIED PATH"""
        # 🎯 UNIFIED: Use single standardized path
        return self.get_field("character.communication.conversation_flow_guidance", {})
    
    def get_response_style(self) -> Dict[str, Any]:
        """Convenience method to get response_style - UNIFIED PATH"""
        # 🎯 UNIFIED: Use single standardized path only
        guidelines = self.get_field("character.communication.conversation_flow_guidance", {})
        return guidelines.get('response_style', {})
    
    def get_communication_style(self) -> Dict[str, Any]:
        """Convenience method to get communication style"""
        return self.get_field("character.identity.communication_style", default={})
    
    def get_personality_traits(self) -> Dict[str, Any]:
        """Convenience method to get personality traits"""
        return self.get_field("character.personality", default={})
    
    def get_ai_identity_handling(self) -> Dict[str, Any]:
        """Convenience method to get AI identity handling"""
        return self.get_field("character.identity.communication_style.ai_identity_handling", default={})
    
    def reload(self) -> None:
        """Force reload of character data (for development/testing)"""
        with self._lock:
            self._loaded = False
            self._data = None
            self._character_file = None
            self._character_object = None  # Clear cached Character object too
        self._load_character_data()
        logger.info("🔄 CDL Manager: Reloaded character data")
    
    def get_character_object(self):
        """
        Get cached Character object from parser.
        
        Lazy loads and caches the full Character object on first access.
        This provides the parsed Character object needed by CDLAIPromptIntegration
        without re-parsing the JSON on every request.
        
        Returns:
            Character: Parsed Character object from CDL parser
        """
        self._load_character_data()
        
        if self._character_object is None:
            with self._lock:
                if self._character_object is None:  # Double-check locking
                    try:
                        from src.characters.cdl.parser import load_character
                        
                        if not self._character_file:
                            logger.error("❌ CDL Manager: No character file loaded")
                            raise ValueError("No character file loaded in CDL Manager")
                        
                        logger.info("🔄 CDL Manager: Loading Character object from parser (first access)")
                        self._character_object = load_character(self._character_file)
                        logger.info("✅ CDL Manager: Cached Character object: %s", self._character_object.identity.name)
                        
                    except Exception as e:
                        logger.error("❌ CDL Manager: Failed to load Character object: %s", e)
                        raise
        
        return self._character_object
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data for debugging"""
        self._load_character_data()
        
        if not self._data:
            return {"status": "no_data", "file": self._character_file}
        
        summary = {
            "status": "loaded",
            "file": self._character_file,
            "character_name": self.get_character_name(),
            "character_occupation": self.get_character_occupation(),
            "has_conversation_flow_guidelines": self.has_field("character.conversation_flow_guidelines"),
            "has_communication_style": self.has_field("character.identity.communication_style"),
            "has_personality": self.has_field("character.personality"),
            "root_keys": list(self._data.keys()) if isinstance(self._data, dict) else [],
        }
        
        character_data = self._data.get('character', {})
        if isinstance(character_data, dict):
            summary["character_keys"] = list(character_data.keys())
        
        return summary


# Global convenience function for easy access
def get_cdl_manager() -> CDLManager:
    """Get the global CDL manager instance"""
    return CDLManager.get_instance()


# Convenience functions for common access patterns
def get_cdl_field(field_path: str, default: Any = None) -> Any:
    """Global convenience function to get CDL field"""
    return get_cdl_manager().get_field(field_path, default)


def has_cdl_field(field_path: str) -> bool:
    """Global convenience function to check CDL field existence"""
    return get_cdl_manager().has_field(field_path)


def get_character_name() -> str:
    """Global convenience function to get character name"""
    return get_cdl_manager().get_character_name()


def get_conversation_flow_guidelines() -> Dict[str, Any]:
    """Global convenience function to get conversation flow guidelines"""
    return get_cdl_manager().get_conversation_flow_guidelines()


def get_response_style() -> Dict[str, Any]:
    """Global convenience function to get response style from CDL"""
    return get_cdl_manager().get_response_style()