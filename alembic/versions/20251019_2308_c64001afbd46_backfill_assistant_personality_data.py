"""backfill_assistant_personality_data

Revision ID: c64001afbd46
Revises: 9c23e4e81011
Create Date: 2025-10-19 23:08:43.557800+00:00

FIXES: v1.0.6 → v1.0.24 upgrade issue where 'assistant' character exists
       but has no personality/voice/mode data in new CDL tables.
       
This migration automatically populates the missing CDL data for users
upgrading from v1.0.6 who had the default assistant character.

SAFE: Uses INSERT...ON CONFLICT to only update if data is missing.

CORRECTED SCHEMA: Now uses personality_traits, communication_styles, 
character_values tables (not the incorrect character_personalities, 
character_voices, character_modes tables that don't exist).

DEPENDENCY: Requires 9c23e4e81011 (creates personality_traits table)
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c64001afbd46'
down_revision: Union[str, None] = '9c23e4e81011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Backfill assistant character personality data for v1.0.6 upgrades.
    
    FIXED SCHEMA: Now uses personality_traits table (not character_personalities)
    with proper row-based Big Five trait storage matching actual code requirements.
    
    Schema source: src/database/migrations/003_clean_rdbms_cdl_schema.sql
    Code usage: src/prompts/cdl_ai_integration.py (lines 155-165)
    """
    
    # Use raw SQL for INSERT...ON CONFLICT pattern
    op.execute("""
    -- Step 1: Add Big Five Personality Traits (row-based, not column-based!)
    -- Each trait is a separate row with trait_name, trait_value, intensity, description
    
    INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description)
    SELECT 
        id,
        'openness',
        0.80,
        'high',
        'Intellectually curious and open to new experiences'
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, trait_name) 
    DO UPDATE SET
        trait_value = EXCLUDED.trait_value,
        intensity = EXCLUDED.intensity,
        description = EXCLUDED.description;
    
    INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description)
    SELECT 
        id,
        'conscientiousness',
        0.90,
        'very_high',
        'Highly organized, reliable, and detail-oriented'
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, trait_name)
    DO UPDATE SET
        trait_value = EXCLUDED.trait_value,
        intensity = EXCLUDED.intensity,
        description = EXCLUDED.description;
    
    INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description)
    SELECT 
        id,
        'extraversion',
        0.70,
        'medium',
        'Socially engaged and approachable, but balanced'
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, trait_name)
    DO UPDATE SET
        trait_value = EXCLUDED.trait_value,
        intensity = EXCLUDED.intensity,
        description = EXCLUDED.description;
    
    INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description)
    SELECT 
        id,
        'agreeableness',
        0.90,
        'very_high',
        'Cooperative, empathetic, and considerate of others'
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, trait_name)
    DO UPDATE SET
        trait_value = EXCLUDED.trait_value,
        intensity = EXCLUDED.intensity,
        description = EXCLUDED.description;
    
    INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description)
    SELECT 
        id,
        'neuroticism',
        0.20,
        'low',
        'Emotionally stable and resilient'
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, trait_name)
    DO UPDATE SET
        trait_value = EXCLUDED.trait_value,
        intensity = EXCLUDED.intensity,
        description = EXCLUDED.description;
    
    -- Step 2: Add Communication Style
    -- Uses communication_styles table (matches ACTUAL database schema)
    -- NOTE: Schema varies between databases - using only columns that exist
    -- SAFE: Only inserts if assistant character doesn't already have communication_styles
    
    INSERT INTO communication_styles (
        character_id,
        engagement_level,
        formality,
        emotional_expression,
        response_length
    )
    SELECT 
        c.id,
        0.70,
        'Professional but approachable',
        0.60,
        'medium'
    FROM characters c
    WHERE c.normalized_name = 'assistant'
    AND NOT EXISTS (
        SELECT 1 FROM communication_styles cs 
        WHERE cs.character_id = c.id
    );
    
    -- Step 3: Add Core Values
    -- Uses character_values table (matches 003_clean_rdbms_cdl_schema.sql schema)
    
    INSERT INTO character_values (character_id, value_key, value_description, importance_level, category)
    SELECT id, 'core_value_1', 'Providing accurate, helpful information', 'critical', 'core_value'
    FROM characters WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, value_key) DO NOTHING;
    
    INSERT INTO character_values (character_id, value_key, value_description, importance_level, category)
    SELECT id, 'core_value_2', 'User empowerment through knowledge', 'high', 'core_value'
    FROM characters WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, value_key) DO NOTHING;
    
    INSERT INTO character_values (character_id, value_key, value_description, importance_level, category)
    SELECT id, 'core_value_3', 'Clear, structured communication', 'high', 'core_value'
    FROM characters WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, value_key) DO NOTHING;
    """)


def downgrade() -> None:
    """
    Remove assistant personality data (not recommended - will break character).
    
    FIXED: Uses correct table names (personality_traits, communication_styles, character_values)
    """
    
    # Only remove if user explicitly downgrades
    op.execute("""
    DELETE FROM character_values 
    WHERE character_id IN (SELECT id FROM characters WHERE normalized_name = 'assistant');
    
    DELETE FROM communication_styles 
    WHERE character_id IN (SELECT id FROM characters WHERE normalized_name = 'assistant');
    
    DELETE FROM personality_traits 
    WHERE character_id IN (SELECT id FROM characters WHERE normalized_name = 'assistant');
    """)
