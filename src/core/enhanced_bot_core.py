#!/usr/bin/env python3
"""
Enhanced Bot Core with Datastore Abstraction
Integrates the datastore factory for unified component management
"""

import logging
import os
from pathlib import Path
from typing import Any

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

        # Initialize all base bot core components - NO FALLBACKS
        self._initialize_base_components()

        logger.info(
            f"EnhancedBotCore initialized (datastore_factory: {self.use_datastore_factory})"
        )

    def _initialize_datastore_factory(self):
        """Initialize the datastore factory and components - NO FALLBACKS"""
        # Detect if we're in desktop mode
        data_dir = Path("data") if not os.path.exists("/.dockerenv") else Path("/app/data")

        self.datastore_factory = create_simple_datastore_factory(data_dir=data_dir)
        logger.info("✅ Datastore factory initialized")

    def _initialize_base_components(self):
        """Initialize base bot core components - NO FALLBACKS, FAIL FAST"""
        # Initialize all components properly or die trying
        self.base_bot_core.initialize_all()
        logger.info("✅ Bot core components initialized successfully")

    async def initialize_datastore_components(self):
        """Initialize datastore components - NO FALLBACKS"""
        if not self.datastore_factory:
            raise RuntimeError("Datastore factory not available - fix your configuration!")

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
        """Initialize all bot components including datastore abstractions - NO FALLBACKS"""
        # Initialize datastore components first
        if self.use_datastore_factory:
            await self.initialize_datastore_components()

        # Initialize base bot core components (synchronous)
        self.base_bot_core.initialize_all()

        logger.info("✅ Enhanced bot core fully initialized")

    def get_bot(self):
        """Get the Discord bot instance"""
        return self.base_bot_core.get_bot()

    def get_components(self) -> dict[str, Any]:
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

    def get_datastore_info(self) -> dict[str, Any]:
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
                        if callable(component.close):
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
