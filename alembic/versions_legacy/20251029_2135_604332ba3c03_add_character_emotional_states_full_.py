"""add_character_emotional_states_full_spectrum

Revision ID: 604332ba3c03
Revises: 06cb86fd8471
Create Date: 2025-10-29 21:35:38.024006+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '604332ba3c03'
down_revision: Union[str, None] = '06cb86fd8471'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Check if old table exists (with JSONB state_data column)
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'character_emotional_states' AND column_name = 'state_data'
    """))
    has_old_structure = result.fetchone() is not None
    
    if has_old_structure:
        print("\n🔄 Migrating character_emotional_states from old 5-dimension JSONB to new 11-emotion columns...")
        
        # Rename old table
        op.rename_table('character_emotional_states', 'character_emotional_states_old')
        print("  ✅ Renamed old table to character_emotional_states_old")
    
    # Create new character_emotional_states table with full 11-emotion RoBERTa spectrum
    op.create_table(
        'character_emotional_states',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('character_name', sa.String(100), nullable=False, comment='Character name (elena, marcus, etc.)'),
        sa.Column('user_id', sa.String(255), nullable=False, comment='Platform user ID (Discord ID, etc.)'),
        
        # 11 RoBERTa emotions (current state, 0.0-1.0)
        sa.Column('anger', sa.Float(), nullable=False, server_default='0.1', comment='Current anger level (0.0-1.0)'),
        sa.Column('anticipation', sa.Float(), nullable=False, server_default='0.4', comment='Current anticipation level (0.0-1.0)'),
        sa.Column('disgust', sa.Float(), nullable=False, server_default='0.05', comment='Current disgust level (0.0-1.0)'),
        sa.Column('fear', sa.Float(), nullable=False, server_default='0.15', comment='Current fear level (0.0-1.0)'),
        sa.Column('joy', sa.Float(), nullable=False, server_default='0.7', comment='Current joy level (0.0-1.0)'),
        sa.Column('love', sa.Float(), nullable=False, server_default='0.6', comment='Current love level (0.0-1.0)'),
        sa.Column('optimism', sa.Float(), nullable=False, server_default='0.65', comment='Current optimism level (0.0-1.0)'),
        sa.Column('pessimism', sa.Float(), nullable=False, server_default='0.2', comment='Current pessimism level (0.0-1.0)'),
        sa.Column('sadness', sa.Float(), nullable=False, server_default='0.15', comment='Current sadness level (0.0-1.0)'),
        sa.Column('surprise', sa.Float(), nullable=False, server_default='0.25', comment='Current surprise level (0.0-1.0)'),
        sa.Column('trust', sa.Float(), nullable=False, server_default='0.7', comment='Current trust level (0.0-1.0)'),
        
        # 11 baseline emotions (CDL personality defaults, 0.0-1.0)
        sa.Column('baseline_anger', sa.Float(), nullable=False, server_default='0.1', comment='CDL baseline anger (0.0-1.0)'),
        sa.Column('baseline_anticipation', sa.Float(), nullable=False, server_default='0.4', comment='CDL baseline anticipation (0.0-1.0)'),
        sa.Column('baseline_disgust', sa.Float(), nullable=False, server_default='0.05', comment='CDL baseline disgust (0.0-1.0)'),
        sa.Column('baseline_fear', sa.Float(), nullable=False, server_default='0.15', comment='CDL baseline fear (0.0-1.0)'),
        sa.Column('baseline_joy', sa.Float(), nullable=False, server_default='0.7', comment='CDL baseline joy (0.0-1.0)'),
        sa.Column('baseline_love', sa.Float(), nullable=False, server_default='0.6', comment='CDL baseline love (0.0-1.0)'),
        sa.Column('baseline_optimism', sa.Float(), nullable=False, server_default='0.65', comment='CDL baseline optimism (0.0-1.0)'),
        sa.Column('baseline_pessimism', sa.Float(), nullable=False, server_default='0.2', comment='CDL baseline pessimism (0.0-1.0)'),
        sa.Column('baseline_sadness', sa.Float(), nullable=False, server_default='0.15', comment='CDL baseline sadness (0.0-1.0)'),
        sa.Column('baseline_surprise', sa.Float(), nullable=False, server_default='0.25', comment='CDL baseline surprise (0.0-1.0)'),
        sa.Column('baseline_trust', sa.Float(), nullable=False, server_default='0.7', comment='CDL baseline trust (0.0-1.0)'),
        
        # Metadata
        sa.Column('total_interactions', sa.Integer(), nullable=False, server_default='0', comment='Total conversation interactions'),
        sa.Column('recent_emotion_history', sa.JSON(), nullable=False, server_default='[]', comment='Last 5 full emotion profiles (JSONB array)'),
        sa.Column('last_updated', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Last emotion update timestamp'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()'), comment='Record creation timestamp'),
        
        sa.PrimaryKeyConstraint('id')
    )
    print("  ✅ Created new character_emotional_states table with 11-emotion columns")
    
    # Create indexes for common query patterns
    op.create_index('idx_char_emotional_states_char_user', 'character_emotional_states', ['character_name', 'user_id'], unique=True)
    op.create_index('idx_char_emotional_states_character', 'character_emotional_states', ['character_name'])
    op.create_index('idx_char_emotional_states_user', 'character_emotional_states', ['user_id'])
    op.create_index('idx_char_emotional_states_last_updated', 'character_emotional_states', ['last_updated'])
    print("  ✅ Created indexes")
    
    # Migrate data from old table if it exists
    if has_old_structure:
        print("\n  🔄 Migrating data from old 5-dimension format to new 11-emotion format...")
        
        # Best-effort mapping from old 5 dimensions to new 11 emotions
        # Old: enthusiasm, stress, contentment, empathy, confidence
        # New: anger, anticipation, disgust, fear, joy, love, optimism, pessimism, sadness, surprise, trust
        op.execute("""
            INSERT INTO character_emotional_states (
                character_name, user_id, 
                joy, love, optimism, trust,  -- Positive emotions
                anger, fear, sadness, pessimism,  -- Negative emotions
                anticipation, surprise, disgust,  -- Neutral/Mixed emotions
                baseline_joy, baseline_love, baseline_optimism, baseline_trust,
                baseline_anger, baseline_fear, baseline_sadness, baseline_pessimism,
                baseline_anticipation, baseline_surprise, baseline_disgust,
                total_interactions, last_updated, created_at
            )
            SELECT 
                character_name, 
                user_id,
                -- Map old enthusiasm → joy, optimism
                LEAST(GREATEST((state_data->>'enthusiasm')::float, 0.0), 1.0) AS joy,
                -- Map old empathy → love, trust
                LEAST(GREATEST((state_data->>'empathy')::float, 0.0), 1.0) AS love,
                -- Map old confidence + enthusiasm → optimism
                LEAST(GREATEST(((state_data->>'confidence')::float + (state_data->>'enthusiasm')::float) / 2.0, 0.0), 1.0) AS optimism,
                -- Map old empathy → trust
                LEAST(GREATEST((state_data->>'empathy')::float, 0.0), 1.0) AS trust,
                
                -- Map old stress → anger, fear
                LEAST(GREATEST((state_data->>'stress')::float * 0.6, 0.0), 1.0) AS anger,
                LEAST(GREATEST((state_data->>'stress')::float * 0.8, 0.0), 1.0) AS fear,
                -- Map old (1 - contentment) → sadness
                LEAST(GREATEST(1.0 - (state_data->>'contentment')::float, 0.0), 1.0) AS sadness,
                -- Map old (1 - confidence) → pessimism
                LEAST(GREATEST(1.0 - (state_data->>'confidence')::float, 0.0), 1.0) AS pessimism,
                
                -- Defaults for anticipation, surprise, disgust (no old mapping)
                0.4 AS anticipation,
                0.25 AS surprise,
                0.05 AS disgust,
                
                -- Baselines (use same logic for now)
                LEAST(GREATEST((state_data->>'baseline_enthusiasm')::float, 0.0), 1.0) AS baseline_joy,
                LEAST(GREATEST((state_data->>'baseline_empathy')::float, 0.0), 1.0) AS baseline_love,
                LEAST(GREATEST(((state_data->>'baseline_confidence')::float + (state_data->>'baseline_enthusiasm')::float) / 2.0, 0.0), 1.0) AS baseline_optimism,
                LEAST(GREATEST((state_data->>'baseline_empathy')::float, 0.0), 1.0) AS baseline_trust,
                LEAST(GREATEST((state_data->>'baseline_stress')::float * 0.6, 0.0), 1.0) AS baseline_anger,
                LEAST(GREATEST((state_data->>'baseline_stress')::float * 0.8, 0.0), 1.0) AS baseline_fear,
                LEAST(GREATEST(1.0 - (state_data->>'baseline_contentment')::float, 0.0), 1.0) AS baseline_sadness,
                LEAST(GREATEST(1.0 - (state_data->>'baseline_confidence')::float, 0.0), 1.0) AS baseline_pessimism,
                0.4 AS baseline_anticipation,
                0.25 AS baseline_surprise,
                0.05 AS baseline_disgust,
                
                (state_data->>'total_interactions')::integer AS total_interactions,
                last_updated,
                created_at
            FROM character_emotional_states_old
            WHERE state_data IS NOT NULL
        """)
        
        # Get count of migrated records
        result = conn.execute(sa.text("SELECT COUNT(*) FROM character_emotional_states"))
        migrated_count = result.scalar()
        print(f"  ✅ Migrated {migrated_count} records from old format")
        
        # Drop old table
        op.drop_table('character_emotional_states_old')
        print("  ✅ Dropped old table")
    
    # Add table comment
    op.execute("""
        COMMENT ON TABLE character_emotional_states IS 
        'Stores character persistent emotional states with full 11-emotion RoBERTa spectrum.
        Replaces old 5-dimension system (enthusiasm, stress, contentment, empathy, confidence).
        Part of CHARACTER EMOTIONAL STATE FULL-SPECTRUM REDESIGN (October 2025).
        Tracks both current emotional state and CDL baseline values for homeostasis.
        Computed properties (dominant_emotion, emotional_intensity, valence, complexity) 
        are calculated on-the-fly in application layer.';
    """)
    print("\n✅ Character emotional states migration complete!")


def downgrade() -> None:
    """Revert migration changes."""
    print("\n⚠️  WARNING: Downgrading will LOSE 11-emotion data and revert to 5-dimension JSONB storage")
    print("  This is a destructive operation that cannot preserve full emotional fidelity!")
    
    # Drop new table
    op.drop_index('idx_char_emotional_states_last_updated', table_name='character_emotional_states')
    op.drop_index('idx_char_emotional_states_user', table_name='character_emotional_states')
    op.drop_index('idx_char_emotional_states_character', table_name='character_emotional_states')
    op.drop_index('idx_char_emotional_states_char_user', table_name='character_emotional_states')
    op.drop_table('character_emotional_states')
    print("  ✅ Dropped new 11-emotion table")
    
    # Recreate old table structure (empty - data cannot be recovered)
    op.create_table(
        'character_emotional_states',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('character_name', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('state_data', sa.JSON(), nullable=False),
        sa.Column('last_updated', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_character_emotional_states_last_updated', 'character_emotional_states', ['last_updated'])
    op.create_index('idx_character_emotional_states_lookup', 'character_emotional_states', ['character_name', 'user_id'])
    op.create_index('ix_character_emotional_states_character_name', 'character_emotional_states', ['character_name'])
    op.create_index('ix_character_emotional_states_user_id', 'character_emotional_states', ['user_id'])
    op.create_index('unique_character_user_state', 'character_emotional_states', ['character_name', 'user_id'], unique=True)
    print("  ✅ Recreated old 5-dimension JSONB table structure (EMPTY)")
    print("\n⚠️  Downgrade complete - emotional state data was LOST")
