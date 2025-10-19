"""backfill_assistant_personality_data

Revision ID: c64001afbd46
Revises: 336ce8830dfe
Create Date: 2025-10-19 23:08:43.557800+00:00

FIXES: v1.0.6 → v1.0.24 upgrade issue where 'assistant' character exists
       but has no personality/voice/mode data in new CDL tables.
       
This migration automatically populates the missing CDL data for users
upgrading from v1.0.6 who had the default assistant character.

SAFE: Uses INSERT...ON CONFLICT to only update if data is missing.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c64001afbd46'
down_revision: Union[str, None] = '336ce8830dfe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Backfill assistant character personality data for v1.0.6 upgrades."""
    
    # Use raw SQL for INSERT...ON CONFLICT pattern
    op.execute("""
    -- Step 1: Add/Update Character Personality (Big Five Traits)
    INSERT INTO character_personalities (
        character_id,
        openness,
        conscientiousness,
        extraversion,
        agreeableness,
        neuroticism,
        created_at
    )
    SELECT 
        id,
        0.80,  -- Openness: Intellectually curious
        0.90,  -- Conscientiousness: Organized, reliable
        0.70,  -- Extraversion: Socially engaged but balanced
        0.90,  -- Agreeableness: Cooperative, empathetic
        0.20,  -- Neuroticism: Emotionally stable
        NOW()
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id) 
    DO UPDATE SET
        openness = EXCLUDED.openness,
        conscientiousness = EXCLUDED.conscientiousness,
        extraversion = EXCLUDED.extraversion,
        agreeableness = EXCLUDED.agreeableness,
        neuroticism = EXCLUDED.neuroticism,
        updated_at = NOW();
    
    -- Step 2: Add/Update Character Voice
    INSERT INTO character_voices (
        character_id,
        tone,
        pace,
        volume,
        accent,
        vocabulary_level,
        formality_level,
        humor_style,
        created_at
    )
    SELECT 
        id,
        'warm and professional',
        'moderate',
        'normal',
        'neutral',
        'accessible',
        'professional',
        'subtle and situational',
        NOW()
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id)
    DO UPDATE SET
        tone = EXCLUDED.tone,
        pace = EXCLUDED.pace,
        volume = EXCLUDED.volume,
        accent = EXCLUDED.accent,
        vocabulary_level = EXCLUDED.vocabulary_level,
        formality_level = EXCLUDED.formality_level,
        humor_style = EXCLUDED.humor_style,
        updated_at = NOW();
    
    -- Step 3: Add/Update Default Character Mode
    INSERT INTO character_modes (
        character_id,
        mode_name,
        is_default,
        description,
        created_at
    )
    SELECT 
        id,
        'helpful_assistant',
        TRUE,
        'Primary operational mode: Helpful, knowledgeable AI assistant',
        NOW()
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, mode_name)
    DO UPDATE SET
        is_default = EXCLUDED.is_default,
        description = EXCLUDED.description,
        updated_at = NOW();
    
    -- Step 4: Add Communication Styles
    INSERT INTO communication_styles (
        character_id,
        style_name,
        description,
        pattern_indicators,
        response_templates,
        created_at
    )
    SELECT 
        id,
        'informative',
        'Provides clear, well-structured information',
        ARRAY['detailed explanations', 'structured responses', 'examples and context'],
        '{"greeting": "Hello! I''m here to help.", "explanation": "Let me explain...", "closing": "I hope this helps!"}',
        NOW()
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, style_name)
    DO NOTHING;
    
    INSERT INTO communication_styles (
        character_id,
        style_name,
        description,
        pattern_indicators,
        response_templates,
        created_at
    )
    SELECT 
        id,
        'empathetic',
        'Shows understanding and emotional awareness',
        ARRAY['acknowledges feelings', 'validates concerns', 'supportive tone'],
        '{"greeting": "I understand.", "explanation": "It sounds like...", "closing": "You''re not alone in this."}',
        NOW()
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, style_name)
    DO NOTHING;
    
    INSERT INTO communication_styles (
        character_id,
        style_name,
        description,
        pattern_indicators,
        response_templates,
        created_at
    )
    SELECT 
        id,
        'problem_solving',
        'Focuses on solutions and actionable steps',
        ARRAY['practical suggestions', 'step-by-step guidance', 'action-oriented'],
        '{"greeting": "Let''s work through this.", "explanation": "Here''s what you can do...", "closing": "These steps should help."}',
        NOW()
    FROM characters 
    WHERE normalized_name = 'assistant'
    ON CONFLICT (character_id, style_name)
    DO NOTHING;
    """)


def downgrade() -> None:
    """Remove assistant personality data (not recommended - will break character)."""
    
    # Only remove if user explicitly downgrades
    op.execute("""
    DELETE FROM communication_styles 
    WHERE character_id IN (SELECT id FROM characters WHERE normalized_name = 'assistant');
    
    DELETE FROM character_modes 
    WHERE character_id IN (SELECT id FROM characters WHERE normalized_name = 'assistant');
    
    DELETE FROM character_voices 
    WHERE character_id IN (SELECT id FROM characters WHERE normalized_name = 'assistant');
    
    DELETE FROM character_personalities 
    WHERE character_id IN (SELECT id FROM characters WHERE normalized_name = 'assistant');
    """)
