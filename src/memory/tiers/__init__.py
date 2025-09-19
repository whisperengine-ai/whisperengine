# src/memory/tiers/__init__.py

"""
Memory Storage Tiers for Hierarchical Architecture

This package contains the four-tier storage system:
- Tier 1: Redis Cache (ultra-fast recent context)
- Tier 2: PostgreSQL Archive (complete conversation history)
- Tier 3: ChromaDB Summaries (semantic search on summaries)
- Tier 4: Neo4j Relationships (knowledge graph connections)
"""

from .tier1_redis_cache import RedisContextCache

__all__ = [
    'RedisContextCache',
]

# Import tier modules conditionally based on available dependencies
try:
    from .tier2_postgresql import PostgreSQLConversationArchive
    __all__.append('PostgreSQLConversationArchive')
except ImportError:
    pass

try:
    from .tier3_chromadb_summaries import ChromaDBSemanticSummaries
    __all__.append('ChromaDBSemanticSummaries')
except ImportError:
    pass

try:
    from .tier4_neo4j_relationships import Neo4jRelationshipEngine
    __all__.append('Neo4jRelationshipEngine')
except ImportError:
    pass