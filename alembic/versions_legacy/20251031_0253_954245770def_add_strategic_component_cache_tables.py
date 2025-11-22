"""Add strategic component cache tables

Revision ID: 954245770def
Revises: 604332ba3c03
Create Date: 2025-10-31 02:53:14.419436+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '954245770def'
down_revision: Union[str, None] = '604332ba3c03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Import necessary types
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    
    # Table 1: strategic_memory_health
    # Tracks memory aging, staleness, retrieval patterns
    op.create_table(
        'strategic_memory_health',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('bot_name', sa.Text(), nullable=False),
        sa.Column('memory_snapshot', JSONB, nullable=False, comment='Top stale/fresh memories'),
        sa.Column('avg_memory_age_hours', sa.Float(), nullable=True),
        sa.Column('retrieval_frequency_trend', sa.Text(), nullable=True, comment='increasing, stable, declining'),
        sa.Column('forgetting_risk_memories', JSONB, nullable=True, comment='Array of memory IDs at risk'),
        sa.Column('computed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False, comment='NOW() + 5 minutes'),
        sa.UniqueConstraint('user_id', 'bot_name', name='uq_memory_health_user_bot')
    )
    op.create_index('idx_memory_health_expires', 'strategic_memory_health', ['expires_at'])
    
    # Table 2: strategic_character_performance
    # 7-day rolling performance metrics
    op.create_table(
        'strategic_character_performance',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('bot_name', sa.Text(), nullable=False),
        sa.Column('time_window_hours', sa.Integer(), nullable=False, server_default=sa.text('168'), comment='Default: 7 days'),
        sa.Column('engagement_score_avg', sa.Float(), nullable=True),
        sa.Column('satisfaction_score_avg', sa.Float(), nullable=True),
        sa.Column('coherence_score_avg', sa.Float(), nullable=True),
        sa.Column('personality_consistency_index', sa.Float(), nullable=True, comment='0.0-1.0'),
        sa.Column('quality_trend', sa.Text(), nullable=True, comment='improving, stable, declining'),
        sa.Column('recent_anomalies', JSONB, nullable=True, comment='Array of detected issues'),
        sa.Column('computed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint('bot_name', 'time_window_hours', name='uq_character_perf_bot_window')
    )
    op.create_index('idx_character_perf_expires', 'strategic_character_performance', ['expires_at'])
    
    # Table 3: strategic_personality_profiles
    # User-bot personality interaction evolution
    op.create_table(
        'strategic_personality_profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('bot_name', sa.Text(), nullable=False),
        sa.Column('dominant_traits', JSONB, nullable=True, comment='Array of {trait, frequency, effectiveness}'),
        sa.Column('user_response_patterns', JSONB, nullable=True, comment='How user reacts to each trait'),
        sa.Column('adaptation_suggestions', JSONB, nullable=True, comment='Recommended personality adjustments'),
        sa.Column('trait_evolution_history', JSONB, nullable=True, comment='30-day trait activation trends'),
        sa.Column('computed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'bot_name', name='uq_personality_user_bot')
    )
    op.create_index('idx_personality_expires', 'strategic_personality_profiles', ['expires_at'])
    
    # Table 4: strategic_conversation_patterns
    # Topic switches, conversation flow, patterns
    op.create_table(
        'strategic_conversation_patterns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('bot_name', sa.Text(), nullable=False),
        sa.Column('recent_topics', JSONB, nullable=True, comment='Array of {topic, start_time, end_time}'),
        sa.Column('avg_topic_duration_minutes', sa.Float(), nullable=True),
        sa.Column('context_switch_frequency', sa.Float(), nullable=True, comment='switches per hour'),
        sa.Column('predicted_switch_likelihood', sa.Float(), nullable=True, comment='0.0-1.0'),
        sa.Column('topic_transition_graph', JSONB, nullable=True, comment='Common topic → topic paths'),
        sa.Column('computed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'bot_name', name='uq_conv_patterns_user_bot')
    )
    op.create_index('idx_conv_patterns_expires', 'strategic_conversation_patterns', ['expires_at'])
    
    # Table 5: strategic_memory_behavior
    # Human-like forgetting/recall modeling
    op.create_table(
        'strategic_memory_behavior',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('bot_name', sa.Text(), nullable=False),
        sa.Column('forgetting_curve_params', JSONB, nullable=True, comment='Model parameters'),
        sa.Column('high_retention_memories', JSONB, nullable=True, comment='Memories with strong recall'),
        sa.Column('low_retention_memories', JSONB, nullable=True, comment='Memories at risk of forgetting'),
        sa.Column('recall_simulation_score', sa.Float(), nullable=True, comment='How human-like memory access is'),
        sa.Column('computed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'bot_name', name='uq_memory_behavior_user_bot')
    )
    op.create_index('idx_memory_behavior_expires', 'strategic_memory_behavior', ['expires_at'])
    
    # Table 6: strategic_engagement_opportunities
    # Proactive engagement timing and topics
    op.create_table(
        'strategic_engagement_opportunities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('bot_name', sa.Text(), nullable=False),
        sa.Column('optimal_timing_hours', sa.Float(), nullable=True, comment='Hours since last message to reach out'),
        sa.Column('receptivity_score', sa.Float(), nullable=True, comment='0.0-1.0, how likely user is receptive'),
        sa.Column('suggested_topics', JSONB, nullable=True, comment='Array of topics likely to engage user'),
        sa.Column('last_engagement_gap_hours', sa.Float(), nullable=True),
        sa.Column('proactive_success_rate', sa.Float(), nullable=True, comment='Historical success of proactive messages'),
        sa.Column('computed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint('user_id', 'bot_name', name='uq_engagement_user_bot')
    )
    op.create_index('idx_engagement_expires', 'strategic_engagement_opportunities', ['expires_at'])


def downgrade() -> None:
    """Revert migration changes."""
    # Drop tables in reverse order
    op.drop_index('idx_engagement_expires', table_name='strategic_engagement_opportunities')
    op.drop_table('strategic_engagement_opportunities')
    
    op.drop_index('idx_memory_behavior_expires', table_name='strategic_memory_behavior')
    op.drop_table('strategic_memory_behavior')
    
    op.drop_index('idx_conv_patterns_expires', table_name='strategic_conversation_patterns')
    op.drop_table('strategic_conversation_patterns')
    
    op.drop_index('idx_personality_expires', table_name='strategic_personality_profiles')
    op.drop_table('strategic_personality_profiles')
    
    op.drop_index('idx_character_perf_expires', table_name='strategic_character_performance')
    op.drop_table('strategic_character_performance')
    
    op.drop_index('idx_memory_health_expires', table_name='strategic_memory_health')
    op.drop_table('strategic_memory_health')
