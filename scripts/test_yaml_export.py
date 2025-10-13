#!/usr/bin/env python3
"""
Test YAML Export Functionality

Tests the YAML export functionality by simulating the Web UI API calls.
"""

import os
import sys
import yaml
import asyncio
import asyncpg
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dotenv import load_dotenv
load_dotenv()

async def test_yaml_export():
    """Test YAML export functionality"""
    
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5433')),
        database=os.getenv('POSTGRES_DB', 'whisperengine'),
        user=os.getenv('POSTGRES_USER', 'whisperengine'),
        password=os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
    )
    
    # Get Elena Rodriguez character (ID 1)
    character = await conn.fetchrow("""
        SELECT id, name, normalized_name, occupation, description, archetype, 
               allow_full_roleplay, is_active, created_at, updated_at
        FROM characters 
        WHERE id = 1
    """)
    
    if not character:
        print("❌ Character not found")
        return
    
    print(f"✅ Found character: {character['name']}")
    
    # Simulate Web UI YAML export structure
    yaml_structure = {
        'name': character['name'],
        'identity': {
            'name': character['name'],
            'occupation': character['occupation'],
            'description': character['description'],
            'archetype': character['archetype'] or 'real-world',
            'allow_full_roleplay_immersion': character['allow_full_roleplay'] or False
        },
        'metadata': {
            'database_id': character['id'],
            'normalized_name': character['normalized_name'],
            'export_date': datetime.now().isoformat(),
            'created_at': character['created_at'].isoformat() if character['created_at'] else None,
            'updated_at': character['updated_at'].isoformat() if character['updated_at'] else None,
            'is_active': character['is_active'],
            'schema_version': '1.0',
            'source': 'whisperengine_cdl_web_ui_test'
        }
    }
    
    # Convert to YAML
    yaml_content = yaml.dump(yaml_structure, default_flow_style=False, indent=2, sort_keys=False)
    
    # Save to test file
    test_dir = Path("tests/yaml_export_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_dir / f"test_export_{character['normalized_name']}.yaml"
    
    with open(test_file, 'w') as f:
        f.write(yaml_content)
    
    print(f"✅ YAML export test successful: {test_file}")
    print("\n📄 YAML Content:")
    print(yaml_content)
    
    # Test YAML import (parse it back)
    try:
        with open(test_file, 'r') as f:
            imported_data = yaml.safe_load(f)
        
        print(f"\n✅ YAML import test successful")
        print(f"   Character name: {imported_data['name']}")
        print(f"   Occupation: {imported_data['identity']['occupation']}")
        print(f"   Database ID: {imported_data['metadata']['database_id']}")
        
    except Exception as e:
        print(f"❌ YAML import test failed: {e}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(test_yaml_export())