"""Phase 1 & 2: CDL database cleanup - Drop legacy and versioned tables

Revision ID: phase1_2_cleanup
Revises: drop_legacy_json
Create Date: 2025-10-13 22:30:00.000000

Description:
    Safe cleanup of deprecated CDL tables identified in audit:
    
    Phase 1 (Zero Risk):
    - DROP character_conversation_flows_json_backup (orphaned backup, no FK dependencies)
    
    Phase 2 (Low Risk):
    - DROP character_emotional_triggers_v2 (abandoned migration attempt, no code usage)
    - RENAME character_roleplay_scenarios_v2 → character_roleplay_scenarios
    - RENAME character_scenario_triggers_v2 → character_scenario_triggers
    
    Benefits:
    - Removes 73 orphaned rows (15 backup + 58 v2 triggers)
    - Eliminates version number confusion (_v2 suffix)
    - Cleans up abandoned migration artifacts
    - ~150 kB storage reclaimed

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'phase1_2_cleanup'
down_revision = 'drop_legacy_json'
branch_labels = None
depends_on = None


def upgrade():
    print("\n🧹 PHASE 1 & 2: CDL Database Cleanup")
    print("=" * 60)
    
    # Phase 1: Drop orphaned backup table (no foreign key dependencies)
    print("\n📦 PHASE 1: Dropping orphaned backup table...")
    print("  - Checking character_conversation_flows_json_backup...")
    
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) as count FROM character_conversation_flows_json_backup"
    ))
    backup_count = result.fetchone()[0]
    print(f"  - Found {backup_count} backup records (will be dropped)")
    
    op.execute("DROP TABLE IF EXISTS character_conversation_flows_json_backup CASCADE")
    print("  ✅ Dropped character_conversation_flows_json_backup")
    
    # Phase 2: Drop abandoned V2 emotional triggers
    print("\n📦 PHASE 2: Cleaning up versioned tables...")
    print("  - Checking character_emotional_triggers_v2...")
    
    result = conn.execute(sa.text(
        "SELECT COUNT(*) as count FROM character_emotional_triggers_v2"
    ))
    v2_count = result.fetchone()[0]
    print(f"  - Found {v2_count} V2 trigger records (abandoned migration)")
    
    op.execute("DROP TABLE IF EXISTS character_emotional_triggers_v2 CASCADE")
    print("  ✅ Dropped character_emotional_triggers_v2")
    
    # Phase 2: Rename roleplay scenarios tables (remove _v2 suffix)
    print("\n  - Renaming character_roleplay_scenarios_v2...")
    
    # Check if target name already exists (safety check)
    result = conn.execute(sa.text("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'character_roleplay_scenarios' AND table_schema = 'public'
    """))
    if result.fetchone()[0] > 0:
        print("  ⚠️  character_roleplay_scenarios already exists, skipping rename")
    else:
        op.execute("ALTER TABLE character_roleplay_scenarios_v2 RENAME TO character_roleplay_scenarios")
        print("  ✅ Renamed character_roleplay_scenarios_v2 → character_roleplay_scenarios")
    
    print("\n  - Renaming character_scenario_triggers_v2...")
    
    # Check if target name already exists (safety check)
    result = conn.execute(sa.text("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'character_scenario_triggers' AND table_schema = 'public'
    """))
    if result.fetchone()[0] > 0:
        print("  ⚠️  character_scenario_triggers already exists, skipping rename")
    else:
        op.execute("ALTER TABLE character_scenario_triggers_v2 RENAME TO character_scenario_triggers")
        print("  ✅ Renamed character_scenario_triggers_v2 → character_scenario_triggers")
    
    print("\n" + "=" * 60)
    print("✅ Phase 1 & 2 cleanup complete!")
    print(f"   - Dropped {backup_count + v2_count} orphaned rows")
    print("   - Removed _v2 version suffixes from 2 tables")
    print("   - Storage reclaimed: ~150 kB")
    print("\n⚠️  IMPORTANT: Update code references:")
    print("   - File: src/characters/cdl/enhanced_cdl_manager.py:1252")
    print("   - Change: character_roleplay_scenarios_v2 → character_roleplay_scenarios")


def downgrade():
    print("\n⏪ Rolling back Phase 1 & 2 cleanup...")
    
    # Recreate backup table (empty)
    op.execute("""
        CREATE TABLE IF NOT EXISTS character_conversation_flows_json_backup (
            id INTEGER,
            character_id INTEGER,
            flow_name VARCHAR(200),
            approach_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            backup_reason TEXT DEFAULT 'Restored by migration downgrade'
        )
    """)
    print("  ✅ Recreated character_conversation_flows_json_backup (empty)")
    
    # Recreate V2 emotional triggers (empty)
    op.execute("""
        CREATE TABLE IF NOT EXISTS character_emotional_triggers_v2 (
            id SERIAL PRIMARY KEY,
            character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
            trigger_text TEXT NOT NULL,
            valence VARCHAR(100) NOT NULL,
            emotion_evoked VARCHAR(200),
            intensity INTEGER CHECK (intensity >= 1 AND intensity <= 10),
            response_guidance TEXT,
            display_order INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(character_id, trigger_text, valence)
        )
    """)
    print("  ✅ Recreated character_emotional_triggers_v2 (empty)")
    
    # Rename back to _v2 suffix
    op.execute("ALTER TABLE IF EXISTS character_roleplay_scenarios RENAME TO character_roleplay_scenarios_v2")
    print("  ✅ Renamed character_roleplay_scenarios → character_roleplay_scenarios_v2")
    
    op.execute("ALTER TABLE IF EXISTS character_scenario_triggers RENAME TO character_scenario_triggers_v2")
    print("  ✅ Renamed character_scenario_triggers → character_scenario_triggers_v2")
    
    print("\n⚠️  Note: Original data NOT restored (was orphaned/abandoned)")
    print("   Tables recreated empty for schema consistency only")
