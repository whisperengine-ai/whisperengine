#!/usr/bin/env python3
"""
CDL Database Validation Script

Validates that all characters have complete CDL data required for regression testing.
Identifies missing fields, incomplete configurations, and provides fix recommendations.

Usage:
    python scripts/validate_cdl_database.py --all
    python scripts/validate_cdl_database.py --character gabriel
    python scripts/validate_cdl_database.py --character elena --fix
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.postgres_pool_manager import get_postgres_pool


class CDLDatabaseValidator:
    """Validates CDL database completeness for regression testing"""
    
    REQUIRED_CHARACTERS = [
        "Elena Rodriguez", "Marcus Thompson", "Jake Sterling", "Gabriel",
        "Sophia Blake", "Ryan Chen", "Dream of the Endless", "Dotty",
        "Aetheris", "Aethys"
    ]
    
    CHARACTER_ARCHETYPES = {
        "Real-World": ["Elena Rodriguez", "Marcus Thompson", "Jake Sterling", 
                      "Gabriel", "Sophia Blake", "Ryan Chen"],
        "Fantasy": ["Dream of the Endless", "Aethys"],
        "Narrative AI": ["Aetheris"]
    }
    
    def __init__(self):
        self.pool = None
        self.validation_results = []
    
    async def initialize(self):
        """Initialize database connection"""
        self.pool = await get_postgres_pool()
    
    async def close(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
    
    async def validate_character(self, character_name: str, fix: bool = False) -> Dict[str, Any]:
        """
        Validate a single character's CDL data completeness.
        
        Args:
            character_name: Name of character to validate
            fix: If True, attempt to auto-fix issues
            
        Returns:
            Validation report with status, issues, warnings, and recommendations
        """
        async with self.pool.acquire() as conn:
            # Fetch character data
            char = await conn.fetchrow("""
                SELECT 
                    id, name, occupation, description,
                    personality_traits, voice_traits,
                    communication_style, archetype
                FROM characters 
                WHERE LOWER(name) = LOWER($1)
            """, character_name)
            
            if not char:
                return {
                    'status': 'FAIL',
                    'character': character_name,
                    'error': f'Character "{character_name}" not found in database',
                    'issues': ['Character does not exist'],
                    'warnings': [],
                    'recommendations': [
                        f'Import character from legacy JSON or create new CDL entry'
                    ]
                }
            
            issues = []
            warnings = []
            recommendations = []
            
            # Validation 1: Occupation
            if not char['occupation'] or len(char['occupation']) < 3:
                issues.append('Missing or invalid occupation')
                recommendations.append(
                    f"UPDATE characters SET occupation = 'FILL_IN_OCCUPATION' "
                    f"WHERE id = {char['id']};"
                )
            
            # Validation 2: Description
            if not char['description']:
                issues.append('Missing description')
                recommendations.append(
                    f"UPDATE characters SET description = 'FILL_IN_DESCRIPTION' "
                    f"WHERE id = {char['id']};"
                )
            elif len(char['description']) < 50:
                warnings.append(f'Description too short ({len(char["description"])} chars, recommended: 100+)')
            
            # Validation 3: Core identity traits
            personality_traits = char['personality_traits'] or {}
            core_identity = personality_traits.get('core_identity', [])
            
            if not core_identity or len(core_identity) == 0:
                issues.append('Missing core_identity traits')
                recommendations.append(f"""
UPDATE characters
SET personality_traits = jsonb_set(
    COALESCE(personality_traits, '{{}}'::jsonb),
    '{{core_identity}}',
    '["trait1", "trait2", "trait3", "trait4", "trait5"]'::jsonb
)
WHERE id = {char['id']};
-- Replace trait1-5 with actual character traits
""")
            elif len(core_identity) < 3:
                warnings.append(f'Core identity has only {len(core_identity)} traits (recommended: 3-5)')
            
            # Validation 4: AI identity handling
            comm_style = char['communication_style'] or {}
            ai_identity = comm_style.get('ai_identity_handling', {})
            
            if not ai_identity:
                warnings.append('Missing ai_identity_handling configuration')
                recommendations.append(f"""
UPDATE characters
SET communication_style = jsonb_set(
    COALESCE(communication_style, '{{}}'::jsonb),
    '{{ai_identity_handling}}',
    '{{"philosophy": "honest", "approach": "character-first"}}'::jsonb
)
WHERE id = {char['id']};
""")
            
            # Validation 5: Archetype
            if not char['archetype']:
                warnings.append('Missing archetype classification')
                expected_archetype = self._determine_archetype(char['name'])
                recommendations.append(
                    f"UPDATE characters SET archetype = '{expected_archetype}' "
                    f"WHERE id = {char['id']};"
                )
            
            # Validation 6: Expertise domains
            domains = await conn.fetch("""
                SELECT domain_name, proficiency_level, keywords
                FROM character_expertise_domains
                WHERE character_id = $1
            """, char['id'])
            
            if len(domains) == 0:
                warnings.append('No expertise domains defined')
                recommendations.append(
                    f"-- Insert expertise domains for {char['name']} in character_expertise_domains table"
                )
            
            # Validation 7: Voice configuration
            voice_traits = char['voice_traits'] or {}
            if not voice_traits.get('tone'):
                warnings.append('Missing voice tone configuration')
            if not voice_traits.get('style'):
                warnings.append('Missing voice style configuration')
            
            # Validation 8: Personality Big Five
            big_five = personality_traits.get('big_five', {})
            if not big_five or len(big_five) == 0:
                warnings.append('Missing Big Five personality traits')
            
            # Validation 9: Character-specific checks
            if char['name'].lower() == 'gabriel':
                self._validate_gabriel_specific(char, issues, warnings, recommendations)
            elif char['name'].lower().startswith('elena'):
                self._validate_elena_specific(char, issues, warnings, recommendations)
            
            # Determine overall status
            status = 'FAIL' if issues else ('WARN' if warnings else 'PASS')
            
            result = {
                'status': status,
                'character': char['name'],
                'character_id': char['id'],
                'issues': issues,
                'warnings': warnings,
                'recommendations': recommendations,
                'data_summary': {
                    'occupation': char['occupation'],
                    'description_length': len(char['description']) if char['description'] else 0,
                    'core_identity_count': len(core_identity),
                    'core_identity_traits': core_identity,
                    'has_ai_identity_config': bool(ai_identity),
                    'archetype': char['archetype'],
                    'expertise_domains_count': len(domains),
                    'expertise_domains': [d['domain_name'] for d in domains]
                }
            }
            
            # Auto-fix if requested
            if fix and recommendations:
                await self._apply_fixes(conn, char['id'], recommendations)
                result['fixes_applied'] = True
            
            return result
    
    def _validate_gabriel_specific(self, char, issues, warnings, recommendations):
        """Gabriel-specific validations for 'devoted companion' identity"""
        core_identity = (char['personality_traits'] or {}).get('core_identity', [])
        
        # Check for "devoted companion" keywords
        gabriel_keywords = ['devoted', 'companion', 'loyal', 'protective']
        missing_keywords = [kw for kw in gabriel_keywords 
                          if not any(kw in trait.lower() for trait in core_identity)]
        
        if missing_keywords:
            issues.append(f'Gabriel missing core identity keywords: {", ".join(missing_keywords)}')
            recommendations.append(f"""
-- Gabriel CRITICAL FIX: Add devoted companion identity
UPDATE characters
SET personality_traits = jsonb_set(
    COALESCE(personality_traits, '{{}}'::jsonb),
    '{{core_identity}}',
    '["devoted companion", "loyal", "protective", "sophisticated", "British gentleman"]'::jsonb
)
WHERE id = {char['id']};
""")
        
        # Check occupation includes "companion"
        if char['occupation'] and 'companion' not in char['occupation'].lower():
            warnings.append('Gabriel occupation should emphasize companion role')
    
    def _validate_elena_specific(self, char, issues, warnings, recommendations):
        """Elena-specific validations for marine biologist identity"""
        core_identity = (char['personality_traits'] or {}).get('core_identity', [])
        
        # Check for marine biology keywords
        elena_keywords = ['marine', 'biologist', 'ocean', 'educator']
        missing_keywords = [kw for kw in elena_keywords 
                           if not any(kw in trait.lower() for trait in core_identity)]
        
        if len(missing_keywords) >= 3:
            warnings.append(f'Elena missing marine biology identity keywords: {", ".join(missing_keywords)}')
    
    def _determine_archetype(self, character_name: str) -> str:
        """Determine expected archetype for character"""
        for archetype, chars in self.CHARACTER_ARCHETYPES.items():
            if any(character_name.lower() in c.lower() for c in chars):
                return archetype
        return "Real-World"  # Default
    
    async def _apply_fixes(self, conn, character_id: int, recommendations: List[str]):
        """Apply auto-fix recommendations"""
        for rec in recommendations:
            if rec.strip().startswith('UPDATE') or rec.strip().startswith('INSERT'):
                try:
                    await conn.execute(rec)
                    print(f"  ✅ Applied fix for character_id={character_id}")
                except Exception as e:
                    print(f"  ❌ Fix failed: {e}")
    
    async def validate_all_characters(self, fix: bool = False) -> List[Dict[str, Any]]:
        """Validate all required characters"""
        results = []
        
        for char_name in self.REQUIRED_CHARACTERS:
            result = await self.validate_character(char_name, fix=fix)
            results.append(result)
        
        return results
    
    def print_validation_report(self, results: List[Dict[str, Any]]):
        """Print formatted validation report"""
        print("\n" + "="*80)
        print("CDL DATABASE VALIDATION REPORT")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Characters Validated: {len(results)}")
        print("="*80 + "\n")
        
        passed = sum(1 for r in results if r['status'] == 'PASS')
        warned = sum(1 for r in results if r['status'] == 'WARN')
        failed = sum(1 for r in results if r['status'] == 'FAIL')
        
        print(f"📊 SUMMARY:")
        print(f"  ✅ PASS: {passed}/{len(results)}")
        print(f"  ⚠️  WARN: {warned}/{len(results)}")
        print(f"  ❌ FAIL: {failed}/{len(results)}")
        print(f"  🎯 Success Rate: {(passed/len(results)*100):.1f}%\n")
        
        # Detailed results
        for result in results:
            status_icon = {
                'PASS': '✅',
                'WARN': '⚠️',
                'FAIL': '❌'
            }[result['status']]
            
            print(f"{status_icon} {result['character']} - {result['status']}")
            
            if 'error' in result:
                print(f"   ERROR: {result['error']}")
            
            if result.get('issues'):
                print(f"   🚨 ISSUES:")
                for issue in result['issues']:
                    print(f"      - {issue}")
            
            if result.get('warnings'):
                print(f"   ⚠️  WARNINGS:")
                for warning in result['warnings']:
                    print(f"      - {warning}")
            
            if result.get('data_summary'):
                summary = result['data_summary']
                print(f"   📋 DATA:")
                print(f"      - Occupation: {summary.get('occupation', 'N/A')}")
                print(f"      - Description: {summary.get('description_length', 0)} chars")
                print(f"      - Core Identity: {summary.get('core_identity_count', 0)} traits → {summary.get('core_identity_traits', [])}")
                print(f"      - Archetype: {summary.get('archetype', 'N/A')}")
                print(f"      - Expertise Domains: {summary.get('expertise_domains_count', 0)} → {summary.get('expertise_domains', [])}")
            
            if result.get('recommendations'):
                print(f"   💡 RECOMMENDATIONS:")
                for rec in result['recommendations']:
                    if rec.strip():
                        print(f"      {rec.strip()[:100]}...")
            
            print()
        
        print("="*80)
        
        if failed > 0:
            print(f"\n🚨 CRITICAL: {failed} character(s) have FAILING validation")
            print("   Run with --fix flag to attempt auto-fixes")
            print("   Or manually apply recommendations above\n")
            return False
        elif warned > 0:
            print(f"\n⚠️  {warned} character(s) have warnings but are functional")
            print("   Consider addressing warnings for optimal test coverage\n")
            return True
        else:
            print(f"\n🎉 ALL CHARACTERS VALIDATED SUCCESSFULLY!")
            print("   Database is ready for regression testing\n")
            return True
    
    async def export_validation_json(self, results: List[Dict[str, Any]], output_file: Path):
        """Export validation results to JSON"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_characters': len(results),
            'passed': sum(1 for r in results if r['status'] == 'PASS'),
            'warned': sum(1 for r in results if r['status'] == 'WARN'),
            'failed': sum(1 for r in results if r['status'] == 'FAIL'),
            'characters': results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Validation report exported to: {output_file}")


async def main():
    parser = argparse.ArgumentParser(description='Validate CDL database for regression testing')
    parser.add_argument('--all', action='store_true', help='Validate all characters')
    parser.add_argument('--character', type=str, help='Validate specific character')
    parser.add_argument('--fix', action='store_true', help='Attempt to auto-fix issues')
    parser.add_argument('--export', type=str, help='Export results to JSON file')
    
    args = parser.parse_args()
    
    if not args.all and not args.character:
        parser.print_help()
        print("\nExample usage:")
        print("  python scripts/validate_cdl_database.py --all")
        print("  python scripts/validate_cdl_database.py --character Gabriel --fix")
        sys.exit(1)
    
    validator = CDLDatabaseValidator()
    
    try:
        await validator.initialize()
        
        if args.all:
            results = await validator.validate_all_characters(fix=args.fix)
        else:
            result = await validator.validate_character(args.character, fix=args.fix)
            results = [result]
        
        success = validator.print_validation_report(results)
        
        if args.export:
            export_path = Path(args.export)
            await validator.export_validation_json(results, export_path)
        
        sys.exit(0 if success else 1)
        
    finally:
        await validator.close()


if __name__ == "__main__":
    asyncio.run(main())
