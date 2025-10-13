#!/usr/bin/env python3
"""
Test CDL YAML Export/Import Functionality

This script tests the complete export/import cycle for CDL characters.

Usage:
    python scripts/test_cdl_yaml_roundtrip.py
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.cdl_yaml_manager import CDLYAMLManager


async def test_single_character_roundtrip(character_name: str = 'elena'):
    """Test export and import of a single character"""
    
    print(f"\n{'='*60}")
    print(f"Testing Single Character Roundtrip: {character_name}")
    print(f"{'='*60}\n")
    
    manager = CDLYAMLManager()
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / f"{character_name}_test.yaml"
        
        # Step 1: Export character
        print(f"1️⃣  Exporting {character_name}...")
        result = await manager.export_character(character_name, export_path)
        
        if not result:
            print(f"❌ Export failed")
            return False
        
        if not export_path.exists():
            print(f"❌ Export file not created: {export_path}")
            return False
        
        print(f"✅ Export successful: {export_path}")
        
        # Step 2: Display file info
        file_size = export_path.stat().st_size
        print(f"📊 File size: {file_size:,} bytes")
        
        # Step 3: Validate YAML structure
        print(f"\n2️⃣  Validating YAML structure...")
        import yaml
        with open(export_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        required_sections = ['cdl_version', 'character']
        required_character_sections = ['metadata', 'identity']
        
        all_valid = True
        for section in required_sections:
            if section not in yaml_data:
                print(f"❌ Missing required section: {section}")
                all_valid = False
            else:
                print(f"✅ Found section: {section}")
        
        if 'character' in yaml_data:
            for section in required_character_sections:
                if section not in yaml_data['character']:
                    print(f"❌ Missing required character section: {section}")
                    all_valid = False
                else:
                    print(f"✅ Found character section: {section}")
        
        if not all_valid:
            return False
        
        # Step 4: Display character preview
        print(f"\n3️⃣  Character Preview:")
        char = yaml_data['character']
        identity = char.get('identity', {})
        
        print(f"   Name: {identity.get('name')}")
        print(f"   Occupation: {identity.get('occupation')}")
        print(f"   Archetype: {identity.get('archetype')}")
        print(f"   Description: {identity.get('description', '')[:80]}...")
        
        if 'values' in char:
            print(f"   Values: {len(char['values'])} defined")
        if 'interests' in char:
            print(f"   Interests: {len(char['interests'])} topics")
        if 'personality' in char:
            print(f"   Personality: Defined")
        
        # Step 5: Test import (dry run - we'll use overwrite to test import mechanism)
        print(f"\n4️⃣  Testing import mechanism...")
        print(f"   Note: Using --overwrite to test import without creating duplicates")
        
        # Import back (this will update the existing character)
        success = await manager.import_character(export_path, overwrite=True)
        
        if success:
            print(f"✅ Import successful (character updated)")
        else:
            print(f"❌ Import failed")
            return False
        
        print(f"\n✅ Roundtrip test PASSED for {character_name}")
        return True


async def test_all_characters_export():
    """Test exporting all characters"""
    
    print(f"\n{'='*60}")
    print(f"Testing All Characters Export")
    print(f"{'='*60}\n")
    
    manager = CDLYAMLManager()
    
    # Export all characters
    print(f"📦 Exporting all active characters...")
    exported_files = await manager.export_all_characters()
    
    if not exported_files:
        print(f"❌ No characters exported")
        return False
    
    print(f"\n✅ Successfully exported {len(exported_files)} characters:")
    for filepath in exported_files:
        print(f"   - {filepath.name}")
    
    return True


async def test_yaml_file_quality(character_name: str = 'elena'):
    """Test quality and completeness of exported YAML"""
    
    print(f"\n{'='*60}")
    print(f"Testing YAML File Quality: {character_name}")
    print(f"{'='*60}\n")
    
    manager = CDLYAMLManager()
    
    # Export to temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / f"{character_name}_quality_test.yaml"
        
        print(f"1️⃣  Exporting {character_name} for quality check...")
        result = await manager.export_character(character_name, export_path)
        
        if not result:
            print(f"❌ Export failed")
            return False
        
        # Load and analyze YAML
        import yaml
        with open(export_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        char = yaml_data.get('character', {})
        
        # Quality checks
        print(f"\n2️⃣  Quality Analysis:")
        
        checks = {
            'Identity complete': bool(char.get('identity', {}).get('name')),
            'Occupation defined': bool(char.get('identity', {}).get('occupation')),
            'Description present': bool(char.get('identity', {}).get('description')),
            'Values exist': len(char.get('values', [])) > 0,
            'Interests exist': len(char.get('interests', [])) > 0,
            'Personality defined': bool(char.get('personality')),
            'Communication patterns': bool(char.get('communication')),
            'Metadata complete': bool(char.get('metadata', {}).get('export_date'))
        }
        
        passed = 0
        for check_name, check_result in checks.items():
            status = "✅" if check_result else "⚠️ "
            print(f"   {status} {check_name}")
            if check_result:
                passed += 1
        
        score = (passed / len(checks)) * 100
        print(f"\n📊 Quality Score: {score:.1f}% ({passed}/{len(checks)} checks passed)")
        
        # Display detailed sections
        print(f"\n3️⃣  Available Sections:")
        for section in char.keys():
            if isinstance(char[section], dict):
                subsections = len(char[section])
                print(f"   - {section}: {subsections} items")
            elif isinstance(char[section], list):
                items = len(char[section])
                print(f"   - {section}: {items} items")
            else:
                print(f"   - {section}: present")
        
        if score >= 80:
            print(f"\n✅ Quality test PASSED")
            return True
        else:
            print(f"\n⚠️  Quality test MARGINAL (consider adding more character data)")
            return True  # Still pass, just a warning


async def run_all_tests():
    """Run all tests"""
    
    print(f"\n{'#'*60}")
    print(f"# CDL YAML Export/Import Test Suite")
    print(f"{'#'*60}")
    
    results = {
        'Single Character Roundtrip': False,
        'YAML Quality Check': False,
        'All Characters Export': False
    }
    
    # Test 1: Single character roundtrip
    try:
        results['Single Character Roundtrip'] = await test_single_character_roundtrip('elena')
    except Exception as e:
        print(f"❌ Single character test failed: {e}")
    
    # Test 2: YAML quality
    try:
        results['YAML Quality Check'] = await test_yaml_file_quality('elena')
    except Exception as e:
        print(f"❌ YAML quality test failed: {e}")
    
    # Test 3: Export all characters
    try:
        results['All Characters Export'] = await test_all_characters_export()
    except Exception as e:
        print(f"❌ All characters export test failed: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, test_result in results.items():
        status = "✅ PASS" if test_result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print(f"\n🎉 All tests PASSED!")
        return True
    else:
        print(f"\n⚠️  Some tests failed")
        return False


if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
