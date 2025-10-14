"""Drop legacy roleplay scenario tables (superseded by character_ai_scenarios)

Revision ID: drop_legacy_roleplay
Revises: phase1_2_cleanup
Create Date: 2025-10-14 00:30:00.000000

Description:
    Remove legacy roleplay scenario system that has been superseded by the modern
    character_ai_scenarios + generic_keyword_templates architecture.
    
    Tables to Drop:
    1. character_scenario_triggers (0 rows - never used)
    2. character_roleplay_scenarios (5 rows - Elena only, legacy data)
    
    Modern Replacement:
    - character_ai_scenarios: Active table with 59 total records across 5 characters
    - generic_keyword_templates: Database-driven keyword detection
    - See: src/prompts/generic_keyword_manager.py for implementation
    
    Justification:
    - Code no longer loads character_roleplay_scenarios (removed Oct 13, 2025)
    - character_scenario_triggers is empty (no triggers defined)
    - Modern system is character-agnostic with better trigger detection
    - Eliminates raw dict dumps in prompts
    
    Risk Level: LOW
    - No code dependencies (loading removed in enhanced_cdl_manager.py)
    - Only Elena has data (5 records), already exists in character_ai_scenarios
    - No foreign key dependencies from other tables TO these tables
    
    Storage Reclaimed: ~2-5 kB
    
    Related Documentation:
    - docs/bug-fixes/CDL_ROLEPLAY_SCENARIOS_CLEANUP.md
    - Git commit: [current] - Remove legacy roleplay_scenarios loading

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'drop_legacy_roleplay'
down_revision = 'phase1_2_cleanup'
branch_labels = None
depends_on = None


def upgrade():
    print("\n🧹 LEGACY ROLEPLAY SCENARIOS CLEANUP")
    print("=" * 60)
    
    conn = op.get_bind()
    
    # Step 1: Show current data before dropping
    print("\n📊 CURRENT STATE:")
    
    # Check if character_roleplay_scenarios table exists
    roleplay_exists_result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'character_roleplay_scenarios'
        )
    """))
    row = roleplay_exists_result.fetchone()
    roleplay_exists = row[0] if row else False
    
    if roleplay_exists:
        # Check character_roleplay_scenarios
        result = conn.execute(sa.text("""
            SELECT c.name, COUNT(*) as scenario_count
            FROM character_roleplay_scenarios crs
            JOIN characters c ON crs.character_id = c.id
            GROUP BY c.name
        """))
        roleplay_data = result.fetchall()
        
        if roleplay_data:
            print("  character_roleplay_scenarios:")
            for row in roleplay_data:
                print(f"    - {row[0]}: {row[1]} scenarios")
        else:
            print("  character_roleplay_scenarios: empty")
    else:
        print("  character_roleplay_scenarios: table doesn't exist")
    
    # Check character_scenario_triggers
    trigger_exists_result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'character_scenario_triggers'
        )
    """))
    row = trigger_exists_result.fetchone()
    trigger_exists = row[0] if row else False
    
    if trigger_exists:
        result = conn.execute(sa.text(
            "SELECT COUNT(*) as count FROM character_scenario_triggers"
        ))
        row = result.fetchone()
        trigger_count = row[0] if row else 0
        print(f"  character_scenario_triggers: {trigger_count} triggers")
    else:
        print("  character_scenario_triggers: table doesn't exist")
    
    # Show modern replacement system
    print("\n✅ MODERN REPLACEMENT (keeping):")
    result = conn.execute(sa.text("""
        SELECT c.name, COUNT(*) as scenario_count
        FROM character_ai_scenarios cas
        JOIN characters c ON cas.character_id = c.id
        GROUP BY c.name
        ORDER BY c.name
    """))
    modern_data = result.fetchall()
    
    print("  character_ai_scenarios (active system):")
    for row in modern_data:
        print(f"    - {row[0]}: {row[1]} scenarios")
    
    # Step 2: Drop legacy tables (foreign keys will be dropped automatically)
    print("\n🗑️  DROPPING LEGACY TABLES:")
    
    print("  1. Dropping character_scenario_triggers...")
    if trigger_exists:
        op.drop_table('character_scenario_triggers')
        print("     ✅ Dropped character_scenario_triggers")
    else:
        print("     ℹ️  character_scenario_triggers doesn't exist, skipping")
    
    print("  2. Dropping character_roleplay_scenarios...")
    if roleplay_exists:
        op.drop_table('character_roleplay_scenarios')
        print("     ✅ Dropped character_roleplay_scenarios")
    else:
        print("     ℹ️  character_roleplay_scenarios doesn't exist, skipping")
    
    print("\n✨ CLEANUP COMPLETE")
    print("=" * 60)
    print("Legacy roleplay scenario tables removed successfully.")
    print("Modern character_ai_scenarios system continues to work.")
    print("\nVerify with:")
    print("  docker exec postgres psql -U whisperengine -d whisperengine \\")
    print("    -c \"SELECT tablename FROM pg_tables WHERE tablename LIKE '%scenario%';\"")
    print()


def downgrade():
    """
    Recreate legacy tables (structure only, data not restored).
    
    NOTE: This only recreates the table structure. The original data from
    character_roleplay_scenarios (5 Elena records) will NOT be restored.
    Use the modern character_ai_scenarios system instead.
    """
    print("\n⚠️  DOWNGRADE: Recreating legacy roleplay scenario tables")
    print("=" * 60)
    print("WARNING: Table structure only - original data will NOT be restored!")
    print()
    
    # Recreate character_roleplay_scenarios
    print("  1. Recreating character_roleplay_scenarios...")
    op.create_table(
        'character_roleplay_scenarios',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('scenario_name', sa.String(length=500), nullable=False),
        sa.Column('response_pattern', sa.String(length=500), nullable=True),
        sa.Column('tier_1_response', sa.Text(), nullable=True),
        sa.Column('tier_2_response', sa.Text(), nullable=True),
        sa.Column('tier_3_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('character_id', 'scenario_name', name='character_roleplay_scenarios_character_id_scenario_name_key')
    )
    
    # Create indexes
    op.create_index('idx_roleplay_scenarios_char', 'character_roleplay_scenarios', ['character_id'])
    print("     ✅ Recreated character_roleplay_scenarios (EMPTY)")
    
    # Recreate character_scenario_triggers
    print("  2. Recreating character_scenario_triggers...")
    op.create_table(
        'character_scenario_triggers',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('trigger_phrase', sa.Text(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['scenario_id'], ['character_roleplay_scenarios.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('scenario_id', 'trigger_phrase', name='character_scenario_triggers_scenario_id_trigger_phrase_key')
    )
    
    # Create indexes
    op.create_index('idx_scenario_triggers_scenario', 'character_scenario_triggers', ['scenario_id'])
    print("     ✅ Recreated character_scenario_triggers (EMPTY)")
    
    print("\n⚠️  DOWNGRADE COMPLETE")
    print("=" * 60)
    print("Legacy tables recreated (structure only, no data).")
    print("Consider using character_ai_scenarios system instead.")
    print()
