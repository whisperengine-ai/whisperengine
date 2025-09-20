"""
Memory Manager Factory for WhisperEngine

Provides easy migration from the old polymorphic mess to the new unified manager.
"""

import logging
from typing import Any, Optional

from .consolidated_memory_manager import ConsolidatedMemoryManager
from .memory_interface import MemoryManagerProtocol
from src.memory.memory_manager import UserMemoryManager

logger = logging.getLogger(__name__)


def create_memory_manager(
    mode: str = "unified",
    llm_client: Optional[Any] = None,
    base_manager: Optional[UserMemoryManager] = None,
    emotion_manager: Optional[Any] = None,
    graph_manager: Optional[Any] = None,
    *,
    # Feature toggles for gradual migration
    use_legacy_mode: bool = False,
    enable_enhanced_queries: bool = True,
    enable_context_security: bool = True,
    enable_thread_safety: bool = True,
    enable_optimization: bool = True,
    enable_graph_integration: bool = False,
    max_workers: int = 4,
    **kwargs
) -> MemoryManagerProtocol:
    """
    Factory function to create the appropriate memory manager.
    
    Creates either the new unified ConsolidatedMemoryManager (default) or 
    legacy wrapper chains for backward compatibility during migration.
    
    Args:
        mode: "unified" (default) or "legacy" for memory manager type
        llm_client: LLM client instance for the manager
        base_manager: Base UserMemoryManager instance (created if None)
        emotion_manager: Emotion manager instance  
        graph_manager: Graph manager instance
        use_legacy_mode: If True, returns legacy wrapped manager for compatibility
        enable_*: Feature toggles for the unified manager
        max_workers: Thread pool workers for unified manager
        **kwargs: Additional configuration options
    
    Returns:
        MemoryManagerProtocol implementation
    """
    
    if use_legacy_mode or mode == "legacy":
        logger.warning(
            "Using legacy memory manager mode. "
            "Consider migrating to unified manager for better performance."
        )
        return _create_legacy_manager(base_manager, emotion_manager, graph_manager, **kwargs)

    # Create new unified manager
    if not base_manager:
        base_manager = UserMemoryManager(llm_client=llm_client)
        
    return ConsolidatedMemoryManager(
        base_memory_manager=base_manager,
        emotion_manager=emotion_manager,
        graph_manager=graph_manager,
        enable_enhanced_queries=enable_enhanced_queries,
        enable_context_security=enable_context_security,
        enable_optimization=enable_optimization,
        enable_graph_sync=enable_graph_integration and graph_manager is not None,
        max_workers=max_workers,
        **kwargs
    )
def _create_legacy_manager(
    base_manager: Optional[UserMemoryManager],
    emotion_manager: Optional[Any],
    graph_manager: Optional[Any],
    **kwargs
) -> Any:
    """
    Create legacy wrapped manager for backward compatibility.
    
    This recreates the old wrapper chain temporarily during migration.
    """
    try:
        manager = base_manager or UserMemoryManager()
        
        # Apply wrappers in order (recreating the old mess temporarily)
        if kwargs.get('enable_enhanced_queries', True):
            from src.utils.enhanced_memory_manager import EnhancedMemoryManager
            manager = EnhancedMemoryManager(manager)
        
        if kwargs.get('enable_context_security', True):
            from src.memory.context_aware_memory_security import ContextAwareMemoryManager
            manager = ContextAwareMemoryManager(manager)
        
        if kwargs.get('enable_thread_safety', True):
            from src.memory.thread_safe_memory import ThreadSafeMemoryManager
            manager = ThreadSafeMemoryManager(manager)
        
        if emotion_manager and kwargs.get('enable_integration', True):
            from src.memory.integrated_memory_manager import IntegratedMemoryManager
            manager = IntegratedMemoryManager(
                memory_manager=manager,
                emotion_manager=emotion_manager,
                enable_graph_sync=graph_manager is not None
            )
        
        return manager
        
    except ImportError as e:
        logger.error(f"Legacy manager creation failed: {e}")
        # Fallback to base manager
        return base_manager or UserMemoryManager()


async def migrate_to_unified_manager(
    current_manager: Any,
    target_manager: Optional[ConsolidatedMemoryManager] = None
) -> ConsolidatedMemoryManager:
    """
    Helper function to migrate from existing manager to unified manager.
    
    Args:
        current_manager: Existing memory manager (wrapped/decorated)
        target_manager: Optional pre-configured target manager
    
    Returns:
        Unified manager instance
    """
    
    if target_manager is None:
        # Extract base manager from wrapper chain
        base_manager = _extract_base_manager(current_manager)
        
        # Extract other components
        emotion_manager = getattr(current_manager, 'emotion_manager', None)
        graph_manager = getattr(current_manager, 'graph_manager', None)
        
        # Create unified manager
        target_manager = ConsolidatedMemoryManager(
            base_memory_manager=base_manager,
            emotion_manager=emotion_manager,
            graph_manager=graph_manager,
        )
    
    # Initialize the new manager
    await target_manager.initialize()
    
    logger.info("Successfully migrated to unified memory manager")
    return target_manager


def _extract_base_manager(wrapped_manager: Any) -> UserMemoryManager:
    """
    Extract the base UserMemoryManager from a chain of wrappers.
    
    Traverses through all the decorator/wrapper layers to find the core manager.
    """
    current = wrapped_manager
    
    # Common wrapper attribute names
    wrapper_attrs = [
        'base_memory_manager',
        'base_manager', 
        'memory_manager',
        'base',
        '_base',
    ]
    
    # Traverse wrapper chain
    for _ in range(10):  # Prevent infinite loops
        # Check if this is already a base manager
        if isinstance(current, UserMemoryManager):
            return current
        
        # Look for wrapper attributes
        found_wrapper = False
        for attr in wrapper_attrs:
            if hasattr(current, attr):
                inner = getattr(current, attr)
                if inner is not None:
                    current = inner
                    found_wrapper = True
                    break
        
        if not found_wrapper:
            break
    
    # If we couldn't find a base manager, create a new one
    if not isinstance(current, UserMemoryManager):
        logger.warning("Could not extract base manager, creating new one")
        return UserMemoryManager()
    
    return current


# Convenience aliases for common configurations
def create_basic_memory_manager(**kwargs) -> ConsolidatedMemoryManager:
    """Create basic memory manager with minimal features."""
    return create_memory_manager(
        enable_all_features=False,
        enable_enhanced_queries=True,
        **kwargs
    )


def create_full_memory_manager(
    emotion_manager: Any, 
    graph_manager: Any, 
    **kwargs
) -> ConsolidatedMemoryManager:
    """Create fully-featured memory manager with all enhancements."""
    return create_memory_manager(
        emotion_manager=emotion_manager,
        graph_manager=graph_manager,
        enable_all_features=True,
        **kwargs
    )