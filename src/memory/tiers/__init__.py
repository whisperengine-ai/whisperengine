# src/memory/tiers/__init__.py

"""
DEPRECATED: Hierarchical Memory Architecture

This package contained the legacy four-tier storage system that has been
REPLACED by the vector-native memory system as per MEMORY_ARCHITECTURE_V2.md:

REMOVED Components:
- Tier 1: Redis Cache → ELIMINATED (vector search is fast enough)
- Tier 2: PostgreSQL Archive → REPLACED by Qdrant vectors
- Tier 3: ChromaDB Summaries → REPLACED by Qdrant (better local Docker support)  
- Tier 4: Neo4j Relationships → REPLACED by vector semantic relationships

This directory will be removed in the next cleanup phase.
All memory functionality now uses the unified vector-native system.
"""

# All tier modules have been removed - this __init__.py remains temporarily
# to prevent import errors during the migration period
__all__ = []