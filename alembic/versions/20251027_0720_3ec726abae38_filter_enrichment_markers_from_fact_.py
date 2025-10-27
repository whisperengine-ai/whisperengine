"""filter_enrichment_markers_from_fact_queries

Revision ID: 3ec726abae38
Revises: 20251026_emoji_log
Create Date: 2025-10-27 07:20:33.437622+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ec726abae38'
down_revision: Union[str, None] = '20251026_emoji_log'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Update get_user_facts_with_relations() SQL function to filter out enrichment markers.
    
    BUG FIX: Enrichment markers were being returned in user fact queries and displayed
    to users in Discord conversations (e.g., "enrichment preference marker marcus_...").
    
    Markers are internal tracking records with:
    - entity_type: '_processing_marker'
    - relationship_type: '_enrichment_progress_marker', '_enrichment_fact_marker', '_enrichment_preference_marker'
    
    These should NEVER be shown to users.
    """
    op.execute("""
    CREATE OR REPLACE FUNCTION get_user_facts_with_relations(
        p_user_id VARCHAR(255),
        p_entity_type TEXT DEFAULT NULL,
        p_min_confidence FLOAT DEFAULT 0.5,
        p_limit INT DEFAULT 20
    )
    RETURNS TABLE (
        entity_name TEXT,
        entity_category TEXT,
        relationship_type TEXT,
        confidence FLOAT,
        emotional_context TEXT,
        mentioned_by_character TEXT,
        related_entities_count BIGINT,
        last_updated TIMESTAMP
    ) AS $$
    BEGIN
        RETURN QUERY
        WITH user_entities AS (
            SELECT 
                fe.entity_name,
                fe.category,
                ufr.relationship_type,
                ufr.confidence,
                ufr.emotional_context,
                ufr.mentioned_by_character,
                ufr.updated_at,
                ufr.entity_id
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE ufr.user_id = p_user_id
              AND fe.entity_type != '_processing_marker'
              AND ufr.relationship_type NOT LIKE '_enrichment%'
              AND (p_entity_type IS NULL OR fe.entity_type = p_entity_type)
              AND ufr.confidence >= p_min_confidence
        )
        SELECT 
            ue.entity_name,
            ue.category,
            ue.relationship_type,
            ue.confidence,
            ue.emotional_context,
            ue.mentioned_by_character,
            COUNT(er.id) as related_count,
            ue.updated_at
        FROM user_entities ue
        LEFT JOIN entity_relationships er ON ue.entity_id = er.from_entity_id
        GROUP BY 
            ue.entity_name, ue.category, ue.relationship_type, 
            ue.confidence, ue.emotional_context, ue.mentioned_by_character, ue.updated_at
        ORDER BY ue.confidence DESC, ue.updated_at DESC
        LIMIT p_limit;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """
    Revert to original function without marker filtering.
    """
    op.execute("""
    CREATE OR REPLACE FUNCTION get_user_facts_with_relations(
        p_user_id VARCHAR(255),
        p_entity_type TEXT DEFAULT NULL,
        p_min_confidence FLOAT DEFAULT 0.5,
        p_limit INT DEFAULT 20
    )
    RETURNS TABLE (
        entity_name TEXT,
        entity_category TEXT,
        relationship_type TEXT,
        confidence FLOAT,
        emotional_context TEXT,
        mentioned_by_character TEXT,
        related_entities_count BIGINT,
        last_updated TIMESTAMP
    ) AS $$
    BEGIN
        RETURN QUERY
        WITH user_entities AS (
            SELECT 
                fe.entity_name,
                fe.category,
                ufr.relationship_type,
                ufr.confidence,
                ufr.emotional_context,
                ufr.mentioned_by_character,
                ufr.updated_at,
                ufr.entity_id
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE ufr.user_id = p_user_id
              AND (p_entity_type IS NULL OR fe.entity_type = p_entity_type)
              AND ufr.confidence >= p_min_confidence
        )
        SELECT 
            ue.entity_name,
            ue.category,
            ue.relationship_type,
            ue.confidence,
            ue.emotional_context,
            ue.mentioned_by_character,
            COUNT(er.id) as related_count,
            ue.updated_at
        FROM user_entities ue
        LEFT JOIN entity_relationships er ON ue.entity_id = er.from_entity_id
        GROUP BY 
            ue.entity_name, ue.category, ue.relationship_type, 
            ue.confidence, ue.emotional_context, ue.mentioned_by_character, ue.updated_at
        ORDER BY ue.confidence DESC, ue.updated_at DESC
        LIMIT p_limit;
    END;
    $$ LANGUAGE plpgsql;
    """)
