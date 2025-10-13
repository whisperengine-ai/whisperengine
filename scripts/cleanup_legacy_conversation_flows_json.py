#!/usr/bin/env python3
"""
Legacy Data Cleanup: Remove JSON data from character_conversation_flows.approach_description

This script safely removes the problematic JSON data from the legacy conversation flows table
to prevent confusion now that we have proper normalized tables.

Usage:
    python scripts/cleanup_legacy_conversation_flows_json.py

Safety Features:
    - Shows what will be changed before making modifications
    - Provides rollback information
    - Only affects the 15 records with JSON data
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncpg
from typing import Dict, List, Any, Optional


class LegacyDataCleanup:
    """Safely cleans up legacy JSON data from character_conversation_flows."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn: Optional[asyncpg.Connection] = None
        
    async def connect(self):
        """Connect to the database."""
        self.conn = await asyncpg.connect(self.database_url)
        
    async def disconnect(self):
        """Disconnect from the database."""
        if self.conn:
            await self.conn.close()
            
    def _ensure_connected(self):
        """Ensure database connection exists."""
        if self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")

    async def analyze_legacy_data(self) -> Dict[str, Any]:
        """Analyze what legacy data exists before cleanup."""
        
        self._ensure_connected()
        
        # Get all character_conversation_flows with JSON in approach_description
        analysis_query = """
            SELECT c.normalized_name, ccf.flow_name, ccf.approach_description,
                   LENGTH(ccf.approach_description) as data_size
            FROM characters c
            JOIN character_conversation_flows ccf ON c.id = ccf.character_id
            WHERE ccf.approach_description LIKE '{%'
            ORDER BY c.normalized_name, ccf.flow_name
        """
        
        flows = await self.conn.fetch(analysis_query)  # type: ignore
        
        analysis = {
            'total_records': len(flows),
            'characters_affected': set(),
            'flow_types': set(),
            'total_data_size': 0,
            'records': []
        }
        
        for flow in flows:
            analysis['characters_affected'].add(flow['normalized_name'])
            analysis['flow_types'].add(flow['flow_name'])
            analysis['total_data_size'] += flow['data_size']
            analysis['records'].append({
                'character': flow['normalized_name'],
                'flow_name': flow['flow_name'],
                'data_size': flow['data_size'],
                'preview': flow['approach_description'][:100] + '...' if len(flow['approach_description']) > 100 else flow['approach_description']
            })
        
        analysis['characters_affected'] = list(analysis['characters_affected'])
        analysis['flow_types'] = list(analysis['flow_types'])
        
        return analysis
    
    async def create_backup_table(self) -> str:
        """Create a backup table with the legacy data before cleanup."""
        
        self._ensure_connected()
        
        backup_table_name = "character_conversation_flows_json_backup"
        
        # Create backup table
        backup_query = f"""
            CREATE TABLE IF NOT EXISTS {backup_table_name} (
                id INTEGER,
                character_id INTEGER,
                flow_name VARCHAR(200),
                approach_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                backup_reason TEXT DEFAULT 'Legacy JSON cleanup'
            )
        """
        
        await self.conn.execute(backup_query)  # type: ignore
        
        # Insert data to backup
        insert_backup_query = f"""
            INSERT INTO {backup_table_name} (id, character_id, flow_name, approach_description)
            SELECT ccf.id, ccf.character_id, ccf.flow_name, ccf.approach_description
            FROM character_conversation_flows ccf
            WHERE ccf.approach_description LIKE '{{%'
        """
        
        rows_backed_up = await self.conn.execute(insert_backup_query)  # type: ignore
        
        return f"Backed up {rows_backed_up} records to {backup_table_name}"
    
    async def cleanup_legacy_json(self) -> Dict[str, Any]:
        """Clean up the legacy JSON data from approach_description fields."""
        
        self._ensure_connected()
        
        # Update approach_description to NULL for records with JSON data
        cleanup_query = """
            UPDATE character_conversation_flows 
            SET approach_description = NULL
            WHERE approach_description LIKE '{%'
        """
        
        rows_updated = await self.conn.execute(cleanup_query)  # type: ignore
        
        # Verify cleanup
        verification_query = """
            SELECT COUNT(*) as remaining_json_records
            FROM character_conversation_flows 
            WHERE approach_description LIKE '{%'
        """
        
        remaining = await self.conn.fetchval(verification_query)  # type: ignore
        
        return {
            'rows_cleaned': rows_updated,
            'remaining_json_records': remaining,
            'cleanup_successful': remaining == 0
        }
    
    async def show_normalized_data_status(self) -> Dict[str, Any]:
        """Show the status of normalized data for affected characters."""
        
        self._ensure_connected()
        
        status_query = """
            SELECT c.normalized_name, 
                   COUNT(ccm.id) as conversation_modes,
                   COUNT(cmg.id) as guidance_items,
                   COUNT(cme.id) as examples
            FROM characters c
            LEFT JOIN character_conversation_modes ccm ON c.id = ccm.character_id
            LEFT JOIN character_mode_guidance cmg ON ccm.id = cmg.mode_id
            LEFT JOIN character_mode_examples cme ON ccm.id = cme.mode_id
            WHERE c.normalized_name IN ('ryan', 'marcus', 'sophia')
            GROUP BY c.normalized_name
            ORDER BY c.normalized_name
        """
        
        status_rows = await self.conn.fetch(status_query)  # type: ignore
        
        return {
            'normalized_data_summary': [
                {
                    'character': row['normalized_name'],
                    'conversation_modes': row['conversation_modes'],
                    'guidance_items': row['guidance_items'],
                    'examples': row['examples']
                }
                for row in status_rows
            ]
        }


async def main():
    """Main cleanup function."""
    
    # Database connection URL
    database_url = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'whisperengine')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5433')}/"
        f"{os.getenv('POSTGRES_DB', 'whisperengine')}"
    )
    
    print("🧹 Starting legacy conversation flows JSON cleanup")
    print(f"Database: {database_url.split('@')[1]}")  # Hide password in output
    
    cleanup = LegacyDataCleanup(database_url)
    
    try:
        await cleanup.connect()
        print("✅ Connected to database")
        
        # Step 1: Analyze legacy data
        print("\n📊 ANALYZING LEGACY DATA:")
        analysis = await cleanup.analyze_legacy_data()
        
        print(f"  Total Records with JSON: {analysis['total_records']}")
        print(f"  Characters Affected: {', '.join(analysis['characters_affected'])}")
        print(f"  Flow Types: {', '.join(analysis['flow_types'])}")
        print(f"  Total Data Size: {analysis['total_data_size']:,} characters")
        
        print("\n📋 RECORDS TO BE CLEANED:")
        for record in analysis['records']:
            print(f"  • {record['character']}.{record['flow_name']} ({record['data_size']:,} chars)")
            print(f"    Preview: {record['preview']}")
        
        # Step 2: Show normalized data status
        print("\n✅ NORMALIZED DATA STATUS:")
        normalized_status = await cleanup.show_normalized_data_status()
        
        for char_data in normalized_status['normalized_data_summary']:
            print(f"  • {char_data['character']}: {char_data['conversation_modes']} modes, "
                  f"{char_data['guidance_items']} guidance, {char_data['examples']} examples")
        
        # Step 3: Create backup
        print("\n💾 CREATING BACKUP:")
        backup_result = await cleanup.create_backup_table()
        print(f"  {backup_result}")
        
        # Step 4: Get user confirmation
        print("\n⚠️  READY TO CLEANUP LEGACY JSON DATA")
        print("This will:")
        print("  - Set approach_description to NULL for 15 records with JSON data")
        print("  - Keep all other data in character_conversation_flows intact")
        print("  - Preserve normalized data (already confirmed working)")
        print("  - Create backup table for rollback if needed")
        
        confirmation = input("\nProceed with cleanup? (yes/no): ").lower().strip()
        
        if confirmation not in ['yes', 'y']:
            print("❌ Cleanup cancelled by user")
            return 1
        
        # Step 5: Perform cleanup
        print("\n🧹 PERFORMING CLEANUP:")
        cleanup_result = await cleanup.cleanup_legacy_json()
        
        print(f"  Rows Updated: {cleanup_result['rows_cleaned']}")
        print(f"  Remaining JSON Records: {cleanup_result['remaining_json_records']}")
        print(f"  Cleanup Successful: {'✅' if cleanup_result['cleanup_successful'] else '❌'}")
        
        if cleanup_result['cleanup_successful']:
            print("\n🎉 LEGACY CLEANUP COMPLETED SUCCESSFULLY!")
            print("\n📝 SUMMARY:")
            print("  ✅ Legacy JSON data removed from character_conversation_flows")
            print("  ✅ Normalized tables remain intact and functional")
            print("  ✅ Backup created for rollback if needed")
            print("  ✅ CDL system now uses only clean normalized data")
            print("\n💡 Next: Proceed with web UI development using normalized tables")
        else:
            print("\n❌ CLEANUP INCOMPLETE - some JSON records remain")
            return 1
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return 1
        
    finally:
        await cleanup.disconnect()
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)