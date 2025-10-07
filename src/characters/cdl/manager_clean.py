"""
CDL Character Manager - Database-backed wrapper
Provides backward compatibility interface to database-backed CDL system.
"""

# Import database-backed implementation
from src.characters.cdl.database_manager import (
    get_database_cdl_manager,
    get_cdl_field,
    get_conversation_flow_guidelines,
    CDLFieldAccess,
    DatabaseCDLManager
)

# For backward compatibility, we provide the same interface as the original CDL manager

# Global manager instance (for legacy compatibility)
_cdl_manager = None


def get_cdl_manager():
    """Get the global CDL manager instance (backward compatibility)"""
    global _cdl_manager
    if _cdl_manager is None:
        _cdl_manager = get_database_cdl_manager()
    return _cdl_manager


# Export the main functions for backward compatibility
__all__ = [
    'get_cdl_manager',
    'get_cdl_field', 
    'get_conversation_flow_guidelines',
    'CDLFieldAccess',
    'DatabaseCDLManager'
]