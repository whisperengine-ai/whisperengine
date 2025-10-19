"""document_enrichment_semantic_knowledge_graph

Revision ID: 27e207ded5a0
Revises: a71d62f22c10
Create Date: 2025-10-19 18:58:39.061692+00:00

DOCUMENTATION MIGRATION - NO CHANGES APPLIED

This migration documents the enrichment semantic knowledge graph schema that was
previously created via SQL init files (sql/semantic_knowledge_graph_schema.sql).

TABLES DOCUMENTED:
- fact_entities: Core entity storage with full-text search
- user_fact_relationships: Knowledge graph relationships between users and entities
- entity_relationships: Relationships between entities (graph edges)

These tables were created during the Phase 1 PostgreSQL Graph Integration (Oct 2025)
and are used by BOTH inline fact extraction AND enrichment worker fact extraction.

WHY DOCUMENT-ONLY MIGRATION:
- Tables already exist in production via SQL init files
- Running CREATE TABLE would fail with "already exists" error
- This migration serves as version control documentation only
- Enables: alembic current, alembic history to show full schema evolution

ORIGINAL SCHEMA SOURCE:
- sql/semantic_knowledge_graph_schema.sql (379 lines)
- Commit: e897fa9 - "feat: Full PostgreSQL graph integration for enrichment worker"
- Date: October 2025

USAGE BY SYSTEM COMPONENTS:
1. Inline fact extraction: src/knowledge/semantic_router.py:store_user_fact()
2. Enrichment worker: src/enrichment/worker.py:_store_facts_in_postgres()
3. Both use IDENTICAL storage patterns (verified Oct 19, 2025)

For full schema details, see:
- docs/schema/DATABASE_SCHEMA_CONSISTENCY_AUDIT.md
- sql/semantic_knowledge_graph_schema.sql
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '27e207ded5a0'
down_revision: Union[str, None] = 'a71d62f22c10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    DOCUMENTATION-ONLY: Record enrichment schema in Alembic history.
    
    NO CHANGES APPLIED - Tables already exist via SQL init files.
    
    This migration documents the following existing tables:
    
    1. fact_entities (379 lines in semantic_knowledge_graph_schema.sql)
       - id: UUID PRIMARY KEY
       - entity_type: TEXT (food, hobby, person, place, media, activity, topic, other)
       - entity_name: TEXT
       - category: TEXT
       - subcategory: TEXT
       - attributes: JSONB
       - search_vector: tsvector (auto-generated for full-text search)
       - created_at, updated_at: TIMESTAMP
       - UNIQUE(entity_type, entity_name)
       - Indexes: type, category, search (GIN), attributes (GIN), name (trigram)
    
    2. user_fact_relationships (knowledge graph core)
       - id: UUID PRIMARY KEY
       - user_id: VARCHAR(255) REFERENCES universal_users(universal_id)
       - entity_id: UUID REFERENCES fact_entities(id)
       - relationship_type: TEXT (likes, dislikes, knows, visited, wants, owns, prefers)
       - confidence: FLOAT (0-1)
       - strength: FLOAT (0-1)
       - emotional_context: TEXT
       - context_metadata: JSONB
       - source_conversation_id: TEXT
       - mentioned_by_character: TEXT
       - source_platform: TEXT
       - related_entities: JSONB (array of related entity connections)
       - created_at, updated_at: TIMESTAMP
       - UNIQUE(user_id, entity_id, relationship_type)
       - Indexes: lookup, type, entity, character, emotional, related (GIN), created
    
    3. entity_relationships (entity-to-entity graph edges)
       - id: UUID PRIMARY KEY
       - from_entity_id: UUID REFERENCES fact_entities(id)
       - to_entity_id: UUID REFERENCES fact_entities(id)
       - relationship_type: TEXT (similar_to, part_of, category_of, related_to, opposite_of, requires)
       - weight: FLOAT (0-1)
       - bidirectional: BOOLEAN
       - metadata: JSONB
       - created_at: TIMESTAMP
       - UNIQUE(from_entity_id, to_entity_id, relationship_type)
       - CHECK(from_entity_id != to_entity_id)
       - Indexes: forward, reverse, type, bidirectional
    
    VERIFICATION QUERY:
    If you need to verify these tables exist, run:
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('fact_entities', 'user_fact_relationships', 'entity_relationships')
        ORDER BY table_name;
    
    Expected result: All 3 tables listed
    """
    
    # NO-OP: Tables already exist via sql/semantic_knowledge_graph_schema.sql
    # This migration exists purely for documentation and version control
    pass


def downgrade() -> None:
    """
    DOCUMENTATION-ONLY: No downgrade action.
    
    Since this migration doesn't create tables (they exist via SQL init),
    downgrade is also a no-op.
    
    WARNING: Do NOT drop these tables manually - they are actively used by:
    - All character bots (inline fact extraction)
    - Enrichment worker (background fact extraction)
    - Knowledge graph queries
    
    Dropping these tables would cause:
    - Loss of all learned facts about users
    - Foreign key violations
    - System-wide fact extraction failures
    """
    
    # NO-OP: Tables were created via SQL init, not this migration
    # Downgrade does not drop tables
    pass
