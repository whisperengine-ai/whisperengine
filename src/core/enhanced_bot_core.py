#!/usr/bin/env python3
"""
Enhanced Bot Core with Datastore Abstraction
Integrates the datastore factory for unified component management
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from src.core.bot import DiscordBotCore
from src.database.simple_datastore_factory import create_simple_datastore_factory

logger = logging.getLogger(__name__)


class EnhancedBotCore:
    """
    Enhanced bot core that uses datastore abstractions for desktop mode compatibility
    """

    def __init__(self, debug_mode: bool = False, use_datastore_factory: bool = True):
        """
        Initialize enhanced bot core

        Args:
            debug_mode: Enable debug logging
            use_datastore_factory: Use datastore factory for component creation
        """
        self.debug_mode = debug_mode
        self.use_datastore_factory = use_datastore_factory

        # Initialize base bot core (but don't initialize all components yet)
        self.base_bot_core = DiscordBotCore(debug_mode=debug_mode)

        # Initialize datastore factory first if enabled
        self.datastore_factory = None
        self.datastore_components = {}

        if self.use_datastore_factory:
            self._initialize_datastore_factory()

        # Try to initialize all base bot core components (gracefully handle failures)
        self._initialize_base_components()

        logger.info(
            f"EnhancedBotCore initialized (datastore_factory: {self.use_datastore_factory})"
        )

    def _initialize_datastore_factory(self):
        """Initialize the datastore factory and components"""
        try:
            # Detect if we're in desktop mode
            data_dir = Path("data") if not os.path.exists("/.dockerenv") else Path("/app/data")

            self.datastore_factory = create_simple_datastore_factory(data_dir=data_dir)
            logger.info("✅ Datastore factory initialized")

        except Exception as e:
            logger.error(f"Failed to initialize datastore factory: {e}")
            self.datastore_factory = None

    def _initialize_base_components(self):
        """Initialize base bot core components with graceful fallback"""
        try:
            # Try to initialize all components
            self.base_bot_core.initialize_all()
            logger.info("✅ Full bot core components initialized successfully")

        except Exception as e:
            logger.warning(f"Failed to initialize full bot core ({e}), creating minimal components")

            # Initialize minimal components for desktop mode
            self._initialize_minimal_components()

    def _initialize_minimal_components(self):
        """Initialize minimal components when full initialization fails"""
        try:
            # Import required components
            from src.llm.llm_client import LLMClient
            from src.llm.concurrent_llm_manager import ConcurrentLLMManager

            # Initialize basic LLM client first
            if not self.base_bot_core.llm_client:
                base_llm = LLMClient()
                self.base_bot_core.llm_client = ConcurrentLLMManager(base_llm)
                logger.info("✅ Minimal LLM client initialized")

            # Initialize basic memory manager placeholder
            if not self.base_bot_core.memory_manager:
                # For now, just create a basic placeholder that won't cause errors
                self.base_bot_core.memory_manager = type(
                    "MockMemoryManager",
                    (),
                    {
                        "search_memories": lambda *args, **kwargs: [],
                        "store_conversation": lambda *args, **kwargs: None,
                        "get_user_conversations": lambda *args, **kwargs: [],
                    },
                )()
                logger.info("✅ Minimal memory manager placeholder initialized")

            # Create a safe memory manager reference (handle type mismatch)
            if not self.base_bot_core.safe_memory_manager:
                # Use setattr to bypass type checking
                setattr(
                    self.base_bot_core, "safe_memory_manager", self.base_bot_core.memory_manager
                )
                logger.info("✅ Safe memory manager reference created")

        except Exception as e:
            logger.error(f"Failed to initialize minimal components: {e}")
            # If even minimal initialization fails, create None placeholders
            if not self.base_bot_core.llm_client:
                self.base_bot_core.llm_client = None
            if not self.base_bot_core.memory_manager:
                self.base_bot_core.memory_manager = None
            if not self.base_bot_core.safe_memory_manager:
                self.base_bot_core.safe_memory_manager = None

    async def initialize_datastore_components(self):
        """Initialize datastore components"""
        if not self.datastore_factory:
            logger.warning("Datastore factory not available, skipping component initialization")
            return

        try:
            logger.info("🏗️ Initializing datastore components...")

            # Initialize all datastore components
            self.datastore_components = await self.datastore_factory.initialize_all()

            # Override base bot core components with datastore factory components
            if "conversation_cache" in self.datastore_components:
                self.base_bot_core.conversation_cache = self.datastore_components[
                    "conversation_cache"
                ]
                logger.info("✅ Conversation cache replaced with datastore factory version")

            # Note: Memory manager and other components will use the factory's vector storage
            # when they initialize, but we don't need to replace them directly

            logger.info("✅ Datastore components integration complete")

        except Exception as e:
            logger.error(f"Failed to initialize datastore components: {e}")

    def get_conversation_cache(self):
        """Get conversation cache (from datastore factory if available)"""
        if "conversation_cache" in self.datastore_components:
            return self.datastore_components["conversation_cache"]
        return self.base_bot_core.conversation_cache

    def get_vector_storage(self):
        """Get vector storage (from datastore factory if available)"""
        if "vector_storage" in self.datastore_components:
            return self.datastore_components["vector_storage"]
        return None

    def get_database_manager(self):
        """Get database manager (from datastore factory if available)"""
        if "database" in self.datastore_components:
            return self.datastore_components["database"]
        return None

    def get_graph_storage(self):
        """Get graph storage (from datastore factory if available)"""
        if "graph_storage" in self.datastore_components:
            return self.datastore_components["graph_storage"]
        return None

    async def initialize_all(self):
        """Initialize all bot components including datastore abstractions"""
        try:
            # Initialize datastore components first
            if self.use_datastore_factory:
                await self.initialize_datastore_components()

            # Initialize base bot core components (synchronous)
            self.base_bot_core.initialize_all()

            logger.info("✅ Enhanced bot core fully initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize enhanced bot core: {e}")
            return False

    def get_bot(self):
        """Get the Discord bot instance"""
        return self.base_bot_core.get_bot()

    def get_components(self) -> Dict[str, Any]:
        """Get all bot components including datastore components"""
        base_components = self.base_bot_core.get_components()

        # Add datastore components
        enhanced_components = {
            **base_components,
            "datastore_factory": self.datastore_factory,
            "conversation_cache": self.get_conversation_cache(),  # Use enhanced version
            "vector_storage": self.get_vector_storage(),
            "database_manager": self.get_database_manager(),
            "graph_storage": self.get_graph_storage(),
        }

        return enhanced_components

    def get_datastore_info(self) -> Dict[str, Any]:
        """Get information about datastore configuration"""
        if self.datastore_factory:
            return self.datastore_factory.get_availability_info()
        else:
            return {"status": "datastore_factory_disabled"}

    # Delegate commonly used properties to base bot core
    @property
    def bot(self):
        return self.base_bot_core.bot

    @property
    def llm_client(self):
        return self.base_bot_core.llm_client

    @property
    def memory_manager(self):
        return self.base_bot_core.memory_manager

    @property
    def safe_memory_manager(self):
        return self.base_bot_core.safe_memory_manager

    @property
    def conversation_cache(self):
        return self.get_conversation_cache()

    @property
    def image_processor(self):
        return self.base_bot_core.image_processor

    @property
    def health_monitor(self):
        return self.base_bot_core.health_monitor

    @property
    def external_emotion_ai(self):
        return self.base_bot_core.external_emotion_ai

    @property
    def phase2_integration(self):
        return self.base_bot_core.phase2_integration

    @property
    def phase3_memory_networks(self):
        return self.base_bot_core.phase3_memory_networks

    def __getattr__(self, name):
        """Delegate unknown attributes to the base bot core"""
        try:
            return getattr(self.base_bot_core, name)
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    async def cleanup(self):
        """Cleanup all components"""
        try:
            # Cleanup datastore components
            for component in self.datastore_components.values():
                if hasattr(component, "close"):
                    try:
                        if hasattr(component.close, "__call__"):
                            await component.close()
                    except Exception as e:
                        logger.warning(f"Error closing datastore component: {e}")

            # Note: Base bot core doesn't have async cleanup method
            logger.info("✅ Enhanced bot core cleanup complete")

        except Exception as e:
            logger.error(f"Error during enhanced bot core cleanup: {e}")


def create_enhanced_bot_core(
    debug_mode: bool = False, use_datastore_factory: bool = True
) -> EnhancedBotCore:
    """Create an enhanced bot core instance"""
    return EnhancedBotCore(debug_mode=debug_mode, use_datastore_factory=use_datastore_factory)
