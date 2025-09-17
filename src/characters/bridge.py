"""
Character System Bridge for WhisperEngine Integration

This module provides the bridge between the character memory system and
the main WhisperEngine conversation flows, memory managers, and platforms.
"""

import logging
from typing import Dict, List, Optional, Any

from src.characters.memory.integration import CharacterMemoryIntegrator, CharacterMemoryContextProvider
from src.characters.models.character import Character
from src.characters.cdl.parser import CDLParser

logger = logging.getLogger(__name__)


class CharacterSystemBridge:
    """
    Bridge class that integrates character memory system with WhisperEngine.
    
    This class provides a clean interface for the main conversation system
    to interact with character memories without tightly coupling to the
    character system internals.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Active character integrators by character_id
        self._active_integrators: Dict[str, CharacterMemoryIntegrator] = {}
        self._context_providers: Dict[str, CharacterMemoryContextProvider] = {}
        
        # Character registry
        self._loaded_characters: Dict[str, Character] = {}
        
        # Integration settings
        self.auto_memory_creation = True
        self.memory_prompt_injection = True
        self.max_memory_context_tokens = 500
        
    async def load_character(self, character_file_path: str) -> Optional[str]:
        """
        Load a character from CDL file and initialize memory system.
        
        Args:
            character_file_path: Path to character YAML file
            
        Returns:
            character_id if successful, None if failed
        """
        try:
            # Load character using CDL parser
            parser = CDLParser()
            character = parser.parse_file(character_file_path)
            
            if not character:
                self.logger.error("Failed to load character from %s", character_file_path)
                return None
            
            character_id = character.metadata.character_id
            
            # Store character
            self._loaded_characters[character_id] = character
            
            # Create memory integrator
            integrator = CharacterMemoryIntegrator(character)
            self._active_integrators[character_id] = integrator
            
            # Create context provider
            context_provider = CharacterMemoryContextProvider(integrator)
            self._context_providers[character_id] = context_provider
            
            # Initialize character memories
            await integrator.ensure_initialized()
            
            self.logger.info("Loaded character %s (%s)", character.identity.name, character_id)
            return character_id
            
        except Exception as e:
            self.logger.error("Failed to load character from %s: %s", character_file_path, e)
            return None
    
    async def get_character_context_for_conversation(self, 
                                                   character_id: str,
                                                   conversation_themes: Optional[List[str]] = None,
                                                   user_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Get character memory context for a conversation.
        
        This method is called by the main conversation system to get
        character-specific context that should influence responses.
        
        Args:
            character_id: ID of active character
            conversation_themes: Themes extracted from conversation
            user_message: Current user message for context
            
        Returns:
            Dictionary with character context for conversation
        """
        try:
            if character_id not in self._active_integrators:
                self.logger.warning("Character %s not loaded", character_id)
                return self._empty_context()
            
            integrator = self._active_integrators[character_id]
            
            # Get memory context
            memory_context = integrator.get_character_memory_context(conversation_themes)
            
            # Get response hints if user message provided
            response_hints = {}
            if user_message and character_id in self._context_providers:
                context_provider = self._context_providers[character_id]
                response_hints = await context_provider.get_response_context_hints(user_message)
            
            # Combine contexts
            context = {
                'character_id': character_id,
                'character_name': self._loaded_characters[character_id].identity.name,
                'memory_context': memory_context,
                'response_hints': response_hints,
                'has_character_memories': memory_context['memory_count'] > 0,
                'prompt_injection_ready': self.memory_prompt_injection
            }
            
            return context
            
        except Exception as e:
            self.logger.error("Failed to get character context for %s: %s", character_id, e)
            return self._empty_context()
    
    async def enhance_system_prompt_with_character_memories(self, 
                                                          character_id: str,
                                                          base_system_prompt: str,
                                                          conversation_themes: Optional[List[str]] = None) -> str:
        """
        Enhance system prompt with character memory context.
        
        This method is called by prompt engineering workflows to inject
        character memories into system prompts for consistency.
        
        Args:
            character_id: ID of active character  
            base_system_prompt: Original system prompt
            conversation_themes: Themes to focus character memories on
            
        Returns:
            Enhanced system prompt with character memory context
        """
        try:
            if not self.memory_prompt_injection:
                return base_system_prompt
            
            if character_id not in self._context_providers:
                self.logger.warning("Character %s not available for prompt enhancement", character_id)
                return base_system_prompt
            
            context_provider = self._context_providers[character_id]
            
            # Get character memory addition
            memory_addition = await context_provider.get_system_prompt_addition(conversation_themes)
            
            if not memory_addition:
                return base_system_prompt
            
            # Inject character memories into system prompt
            enhanced_prompt = f"{base_system_prompt}\n\n{memory_addition}"
            
            # Optionally truncate if too long
            if len(enhanced_prompt) > self.max_memory_context_tokens * 4:  # Rough token estimate
                self.logger.warning("Character memory context too long, truncating")
                memory_addition = memory_addition[:self.max_memory_context_tokens * 2]
                enhanced_prompt = f"{base_system_prompt}\n\n{memory_addition}"
            
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error("Failed to enhance system prompt for %s: %s", character_id, e)
            return base_system_prompt
    
    async def process_conversation_for_character_memory(self, 
                                                      character_id: str,
                                                      user_message: str,
                                                      character_response: str,
                                                      emotional_context: Optional[Dict] = None) -> bool:
        """
        Process a conversation to potentially create character memories.
        
        This method is called after conversation responses to determine
        if the interaction should become a character memory.
        
        Args:
            character_id: ID of active character
            user_message: User's message
            character_response: Character's response  
            emotional_context: Emotional analysis data
            
        Returns:
            True if memory was created, False otherwise
        """
        try:
            if not self.auto_memory_creation:
                return False
            
            if character_id not in self._active_integrators:
                self.logger.warning("Character %s not available for memory creation", character_id)
                return False
            
            integrator = self._active_integrators[character_id]
            
            # Create conversation memory
            memory = await integrator.create_conversation_memory(
                conversation_content=f"{user_message} | {character_response}",
                user_message=user_message,
                character_response=character_response,
                emotional_context=emotional_context
            )
            
            return memory is not None
            
        except Exception as e:
            self.logger.error("Failed to process conversation for character memory %s: %s", character_id, e)
            return False
    
    async def add_character_daily_reflection(self, character_id: str, themes: Optional[List[str]] = None) -> bool:
        """
        Add a daily reflection for a character.
        
        This can be called periodically or at the end of conversation
        sessions to help characters develop and remember their experiences.
        
        Args:
            character_id: ID of character
            themes: Optional themes to focus reflection on
            
        Returns:
            True if reflection was added, False otherwise
        """
        try:
            if character_id not in self._active_integrators:
                return False
            
            integrator = self._active_integrators[character_id]
            reflection = await integrator.add_daily_reflection(themes)
            
            return reflection is not None
            
        except Exception as e:
            self.logger.error("Failed to add daily reflection for %s: %s", character_id, e)
            return False
    
    def get_character_memory_statistics(self, character_id: str) -> Dict[str, Any]:
        """Get memory statistics for a character"""
        try:
            if character_id not in self._active_integrators:
                return {}
            
            integrator = self._active_integrators[character_id]
            return integrator.self_memory.get_memory_statistics()
            
        except Exception as e:
            self.logger.error("Failed to get memory statistics for %s: %s", character_id, e)
            return {}
    
    def get_loaded_characters(self) -> Dict[str, str]:
        """Get list of loaded characters (id -> name mapping)"""
        return {
            char_id: char.identity.name 
            for char_id, char in self._loaded_characters.items()
        }
    
    def is_character_loaded(self, character_id: str) -> bool:
        """Check if a character is loaded and available"""
        return character_id in self._active_integrators
    
    def _empty_context(self) -> Dict[str, Any]:
        """Return empty context for when character is not available"""
        return {
            'character_id': None,
            'character_name': None,
            'memory_context': {
                'memories': [],
                'formatted_memories': '',
                'memory_count': 0,
                'total_memories': 0,
                'average_emotional_weight': 0.0,
                'dominant_themes': [],
                'character_development_level': 'none'
            },
            'response_hints': {},
            'has_character_memories': False,
            'prompt_injection_ready': False
        }


class ConversationCharacterEnhancer:
    """
    Helper class that provides character memory enhancements for conversation flows.
    
    This class can be used by conversation handlers to easily integrate
    character memory functionality without complex setup.
    """
    
    def __init__(self, character_bridge: CharacterSystemBridge):
        self.bridge = character_bridge
        self.logger = logging.getLogger(__name__)
        
        # Current session state
        self.active_character_id: Optional[str] = None
        self.conversation_themes: List[str] = []
        
    async def set_active_character(self, character_file_path: str) -> bool:
        """
        Set the active character for this conversation session.
        
        Args:
            character_file_path: Path to character CDL file
            
        Returns:
            True if character was loaded successfully
        """
        try:
            character_id = await self.bridge.load_character(character_file_path)
            if character_id:
                self.active_character_id = character_id
                self.logger.info("Set active character: %s", character_id)
                return True
            return False
            
        except Exception as e:
            self.logger.error("Failed to set active character: %s", e)
            return False
    
    async def enhance_response_generation(self, 
                                        user_message: str, 
                                        base_system_prompt: str) -> tuple[str, Dict[str, Any]]:
        """
        Enhance response generation with character memory context.
        
        Args:
            user_message: User's message
            base_system_prompt: Base system prompt
            
        Returns:
            Tuple of (enhanced_system_prompt, character_context)
        """
        if not self.active_character_id:
            return base_system_prompt, {}
        
        try:
            # Extract themes from user message
            integrator = self.bridge._active_integrators.get(self.active_character_id)
            if integrator:
                themes = integrator.extract_conversation_themes(user_message)
                self.conversation_themes = themes
            
            # Get character context
            character_context = await self.bridge.get_character_context_for_conversation(
                self.active_character_id, 
                self.conversation_themes,
                user_message
            )
            
            # Enhance system prompt
            enhanced_prompt = await self.bridge.enhance_system_prompt_with_character_memories(
                self.active_character_id,
                base_system_prompt,
                self.conversation_themes
            )
            
            return enhanced_prompt, character_context
            
        except Exception as e:
            self.logger.error("Failed to enhance response generation: %s", e)
            return base_system_prompt, {}
    
    async def process_conversation_interaction(self, 
                                             user_message: str,
                                             character_response: str,
                                             emotional_context: Optional[Dict] = None) -> bool:
        """
        Process completed conversation interaction for character memory.
        
        Args:
            user_message: User's message
            character_response: Character's response
            emotional_context: Optional emotional analysis
            
        Returns:
            True if memory was created
        """
        if not self.active_character_id:
            return False
        
        return await self.bridge.process_conversation_for_character_memory(
            self.active_character_id,
            user_message,
            character_response,
            emotional_context
        )
    
    def get_character_info(self) -> Dict[str, Any]:
        """Get information about the active character"""
        if not self.active_character_id:
            return {'active': False}
        
        character = self.bridge._loaded_characters.get(self.active_character_id)
        stats = self.bridge.get_character_memory_statistics(self.active_character_id)
        
        return {
            'active': True,
            'character_id': self.active_character_id,
            'name': character.identity.name if character else 'Unknown',
            'occupation': character.identity.occupation if character else 'Unknown',
            'total_memories': stats.get('total_memories', 0),
            'development_level': self._calculate_development_level(stats),
            'current_themes': self.conversation_themes
        }
    
    def _calculate_development_level(self, stats: Dict) -> str:
        """Calculate character development level from statistics"""
        total = stats.get('total_memories', 0)
        avg_weight = stats.get('average_emotional_weight', 0.0)
        
        if total >= 50 and avg_weight >= 0.6:
            return 'advanced'
        elif total >= 20 and avg_weight >= 0.4:
            return 'intermediate'
        elif total >= 5:
            return 'developing'
        else:
            return 'basic'


# Global instance for easy access
_global_character_bridge = None


def get_character_bridge() -> CharacterSystemBridge:
    """Get the global character system bridge instance"""
    global _global_character_bridge
    if _global_character_bridge is None:
        _global_character_bridge = CharacterSystemBridge()
    return _global_character_bridge


def create_conversation_enhancer() -> ConversationCharacterEnhancer:
    """Create a new conversation character enhancer"""
    bridge = get_character_bridge()
    return ConversationCharacterEnhancer(bridge)