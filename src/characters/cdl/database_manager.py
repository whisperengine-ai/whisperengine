"""
CDL Database Manager - PostgreSQL-backed character data management
Uses proper normalized schema with hybrid JSON approach for extensibility.

This replaces the JSONB blob approach with a proper RDBMS design that gives us:
1. Normalized tables for core, queryable fields (identity, personality traits)
2. JSON columns for extensible/nested data (custom traits, complex structures)
3. Proper schema versioning for evolution over time

This is now a compatibility layer that delegates to the normalized manager.
"""

# Import the new normalized manager
from .normalized_database_manager import (
    NormalizedCDLManager,
    get_normalized_cdl_manager,
    get_cdl_field,
    get_conversation_flow_guidelines,
    CDLFieldAccess
)

import logging

logger = logging.getLogger(__name__)


# Compatibility aliases for existing code
DatabaseCDLManager = NormalizedCDLManager
get_database_cdl_manager = get_normalized_cdl_manager


def main():
    """Test the normalized database manager"""
    logger.info("� Testing Normalized CDL Database Manager")
    
    # Test loading character data
    manager = get_database_cdl_manager()
    
    # Test basic field access
    character_name = manager.get_character_name()
    occupation = manager.get_character_occupation()
    
    logger.info("Character: %s", character_name)
    logger.info("Occupation: %s", occupation)
    
    # Test getting character object
    character_obj = manager.get_character_object()
    if character_obj:
        logger.info("✅ Successfully created Character object")
        logger.info("Identity: %s - %s", character_obj.identity.name, character_obj.identity.occupation)
    else:
        logger.error("❌ Failed to create Character object")
    
    # Test data summary
    summary = manager.get_data_summary()
    logger.info("Data summary: %s", summary)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()