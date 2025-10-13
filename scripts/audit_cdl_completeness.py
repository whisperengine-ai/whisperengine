#!/usr/bin/env python3
"""
CDL Database Completeness Audit Tool

Compares CDL database contents with backup JSON files to identify:
1. Missing semantic information in database
2. Unused/orphaned JSON elements
3. Structural completeness gaps
4. Information fidelity assessment

Usage:
    python scripts/audit_cdl_completeness.py
"""

import asyncio
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from datetime import datetime
from dataclasses import dataclass, field

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.postgres_pool_manager import get_postgres_pool


@dataclass
class AuditResult:
    """Results from CDL completeness audit"""
    character_name: str
    json_file_path: str
    database_completeness_score: float = 0.0
    missing_information: List[str] = field(default_factory=list)
    unused_json_elements: List[str] = field(default_factory=list)
    semantic_gaps: List[str] = field(default_factory=list)
    structure_analysis: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class JsonStructureAnalysis:
    """Analysis of JSON file structure and content"""
    total_fields: int = 0
    nested_depth: int = 0
    key_categories: Set[str] = field(default_factory=set)
    value_types: Dict[str, int] = field(default_factory=dict)
    semantic_content_fields: List[str] = field(default_factory=list)
    redundant_fields: List[str] = field(default_factory=list)


class CDLCompletenessAuditor:
    """Audits CDL database completeness against JSON backups"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path("characters/examples_legacy_backup")
        self.database_pool = None
        
        # Define semantic categories and their importance
        self.semantic_categories = {
            'core_identity': ['name', 'occupation', 'description', 'age', 'ethnicity', 'location'],
            'personality_traits': ['big_five', 'personality', 'values_and_beliefs', 'fears', 'dreams'],
            'communication_patterns': ['communication_style', 'emoji_usage', 'formality', 'emotional_expression'],
            'background_history': ['education', 'career_history', 'personal_history', 'cultural_background'],
            'relationships': ['relationships', 'family', 'colleagues', 'mentors'],
            'abilities_skills': ['abilities', 'skills', 'expertise', 'talents'],
            'memories_experiences': ['memories', 'experiences', 'formative_events'],
            'behavioral_triggers': ['triggers', 'reactions', 'response_patterns'],
            'essence_mystical': ['essence', 'nature', 'existence_method', 'powers'],
            'visual_appearance': ['physical_appearance', 'digital_communication', 'style']
        }
        
        # Database table mapping
        self.db_table_mapping = {
            'core_identity': 'characters',
            'personality_traits': ['character_metadata', 'character_background'],
            'communication_patterns': 'character_communication_patterns',
            'background_history': 'character_background',
            'relationships': 'character_relationships',
            'abilities_skills': 'character_abilities',
            'memories_experiences': 'character_memories',
            'behavioral_triggers': 'character_behavioral_triggers',
            'essence_mystical': 'character_essence',
            'visual_appearance': 'character_appearance'
        }

    async def initialize(self):
        """Initialize database connection"""
        try:
            self.database_pool = await get_postgres_pool()
            self.logger.info("✅ Database connection established")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to database: {e}")
            raise

    async def audit_all_characters(self) -> List[AuditResult]:
        """Audit all characters with JSON backups"""
        results = []
        
        # Find all JSON backup files
        json_files = list(self.backup_dir.glob("*.json"))
        self.logger.info(f"🔍 Found {len(json_files)} JSON backup files")
        
        for json_file in json_files:
            if json_file.stem in ['default_assistant']:  # Skip non-character files
                continue
                
            try:
                result = await self.audit_character_completeness(json_file)
                results.append(result)
                self.logger.info(f"✅ Completed audit for {result.character_name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to audit {json_file.stem}: {e}")
                # Create error result
                error_result = AuditResult(
                    character_name=json_file.stem,
                    json_file_path=str(json_file),
                    database_completeness_score=0.0,
                    missing_information=[f"Audit failed: {str(e)}"]
                )
                results.append(error_result)
        
        return results

    async def audit_character_completeness(self, json_file_path: Path) -> AuditResult:
        """Audit completeness for a single character"""
        self.logger.info(f"🔍 Auditing character: {json_file_path.stem}")
        
        # Load and analyze JSON structure
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        json_analysis = self.analyze_json_structure(json_data)
        character_name = self.extract_character_name(json_data)
        
        # Get database data for this character
        db_data = await self.get_database_data(character_name)
        
        # Perform completeness analysis
        result = AuditResult(
            character_name=character_name,
            json_file_path=str(json_file_path)
        )
        
        # Analyze each semantic category
        await self.analyze_semantic_completeness(json_data, db_data, result)
        
        # Calculate overall completeness score
        result.database_completeness_score = self.calculate_completeness_score(result)
        
        # Structure analysis
        result.structure_analysis = {
            'json_total_fields': json_analysis.total_fields,
            'json_nested_depth': json_analysis.nested_depth,
            'json_categories': list(json_analysis.key_categories),
            'database_tables_populated': len([t for t in db_data.keys() if db_data[t]]),
            'semantic_content_coverage': len(result.missing_information) == 0
        }
        
        # Generate recommendations
        result.recommendations = self.generate_recommendations(result, json_analysis)
        
        return result

    def analyze_json_structure(self, json_data: Dict) -> JsonStructureAnalysis:
        """Analyze JSON file structure for semantic content"""
        analysis = JsonStructureAnalysis()
        
        def traverse_json(obj, depth=0, path=""):
            nonlocal analysis
            analysis.nested_depth = max(analysis.nested_depth, depth)
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    analysis.total_fields += 1
                    analysis.key_categories.add(key.split('_')[0])  # First word of key
                    
                    # Identify semantic content fields
                    if self.is_semantic_field(key, value):
                        analysis.semantic_content_fields.append(current_path)
                    
                    # Check for redundancy
                    if self.is_potentially_redundant(key, value):
                        analysis.redundant_fields.append(current_path)
                    
                    # Track value types
                    value_type = type(value).__name__
                    analysis.value_types[value_type] = analysis.value_types.get(value_type, 0) + 1
                    
                    traverse_json(value, depth + 1, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    traverse_json(item, depth + 1, f"{path}[{i}]")
        
        traverse_json(json_data)
        return analysis

    def is_semantic_field(self, key: str, value: Any) -> bool:
        """Determine if a field contains meaningful semantic content"""
        semantic_indicators = [
            'description', 'name', 'occupation', 'background', 'history',
            'personality', 'trait', 'value', 'belief', 'fear', 'dream',
            'memory', 'experience', 'relationship', 'ability', 'skill',
            'trigger', 'response', 'pattern', 'style', 'essence', 'nature'
        ]
        
        if isinstance(value, str) and len(value.strip()) > 10:  # Meaningful text content
            return True
        
        return any(indicator in key.lower() for indicator in semantic_indicators)

    def is_potentially_redundant(self, key: str, value: Any) -> bool:
        """Check if field might be redundant or auto-generated"""
        redundancy_indicators = [
            key.endswith('_1') and isinstance(value, dict) and 'description' in value,
            key.startswith('generated_'),
            isinstance(value, str) and value == "",
            isinstance(value, dict) and len(value) == 1 and 'description' in value and value['description'] == ""
        ]
        
        return any(redundancy_indicators)

    def extract_character_name(self, json_data: Dict) -> str:
        """Extract character name from JSON data"""
        # Try multiple possible paths
        paths = [
            ['character', 'identity', 'name'],
            ['identity', 'name'],
            ['character', 'metadata', 'name'],
            ['metadata', 'name'],
            ['name']
        ]
        
        for path in paths:
            try:
                current = json_data
                for key in path:
                    current = current[key]
                if isinstance(current, str) and current.strip():
                    return current.strip()
            except (KeyError, TypeError):
                continue
        
        return "Unknown"

    async def get_database_data(self, character_name: str) -> Dict[str, List[Dict]]:
        """Get all database data for a character"""
        if not self.database_pool:
            return {}
        
        db_data = {}
        
        async with self.database_pool.acquire() as conn:
            # Get character ID
            character_row = await conn.fetchrow(
                "SELECT id, name, occupation, description FROM characters WHERE name = $1",
                character_name
            )
            
            if not character_row:
                self.logger.warning(f"⚠️ Character '{character_name}' not found in database")
                return db_data
            
            character_id = character_row['id']
            db_data['characters'] = [dict(character_row)]
            
            # Get data from all CDL tables
            tables = [
                'character_metadata', 'character_appearance', 'character_background',
                'character_relationships', 'character_memories', 'character_abilities',
                'character_communication_patterns', 'character_behavioral_triggers',
                'character_essence', 'character_instructions'
            ]
            
            for table in tables:
                try:
                    rows = await conn.fetch(
                        f"SELECT * FROM {table} WHERE character_id = $1",
                        character_id
                    )
                    db_data[table] = [dict(row) for row in rows]
                except Exception as e:
                    self.logger.debug(f"Could not query {table}: {e}")
                    db_data[table] = []
        
        return db_data

    async def analyze_semantic_completeness(self, json_data: Dict, db_data: Dict, result: AuditResult):
        """Analyze semantic completeness for each category"""
        
        for category, json_fields in self.semantic_categories.items():
            json_content = self.extract_json_content_for_category(json_data, json_fields)
            db_content = self.extract_db_content_for_category(db_data, category)
            
            # Check if semantic content from JSON exists in database
            if json_content and not db_content:
                result.missing_information.append(
                    f"{category}: Found {len(json_content)} entries in JSON but none in database"
                )
            elif json_content and len(db_content) < len(json_content):
                result.missing_information.append(
                    f"{category}: JSON has {len(json_content)} entries, database has {len(db_content)}"
                )
            
            # Check for semantic gaps
            if json_content:
                semantic_gap = self.find_semantic_gaps(json_content, db_content, category)
                if semantic_gap:
                    result.semantic_gaps.append(semantic_gap)

    def extract_json_content_for_category(self, json_data: Dict, fields: List[str]) -> List[str]:
        """Extract meaningful content from JSON for a semantic category"""
        content = []
        
        def search_json(obj, target_fields, current_path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if any(field in key.lower() for field in target_fields):
                        if isinstance(value, str) and value.strip():
                            content.append(f"{current_path}.{key}: {value.strip()}")
                        elif isinstance(value, dict):
                            search_json(value, target_fields, f"{current_path}.{key}")
                    else:
                        search_json(value, target_fields, f"{current_path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_json(item, target_fields, f"{current_path}[{i}]")
        
        search_json(json_data, fields)
        return content

    def extract_db_content_for_category(self, db_data: Dict, category: str) -> List[str]:
        """Extract content from database for a semantic category"""
        content = []
        
        if category not in self.db_table_mapping:
            return content
        
        table_names = self.db_table_mapping[category]
        if isinstance(table_names, str):
            table_names = [table_names]
        
        for table_name in table_names:
            if table_name in db_data:
                for row in db_data[table_name]:
                    # Extract meaningful text fields
                    for key, value in row.items():
                        if isinstance(value, str) and value.strip() and key not in ['id', 'character_id', 'created_date', 'updated_date']:
                            content.append(f"{table_name}.{key}: {value.strip()}")
        
        return content

    def find_semantic_gaps(self, json_content: List[str], db_content: List[str], category: str) -> Optional[str]:
        """Find semantic gaps between JSON and database content"""
        if not json_content:
            return None
        
        # Simple semantic comparison - check if key concepts exist
        json_concepts = set()
        db_concepts = set()
        
        for item in json_content:
            # Extract key words from content
            text = item.split(': ', 1)[-1].lower()
            words = [w for w in text.split() if len(w) > 3]
            json_concepts.update(words[:5])  # Take first 5 meaningful words
        
        for item in db_content:
            text = item.split(': ', 1)[-1].lower()
            words = [w for w in text.split() if len(w) > 3]
            db_concepts.update(words[:5])
        
        missing_concepts = json_concepts - db_concepts
        if len(missing_concepts) > len(json_concepts) * 0.5:  # More than 50% concepts missing
            return f"{category}: Key concepts missing from database: {', '.join(list(missing_concepts)[:10])}"
        
        return None

    def calculate_completeness_score(self, result: AuditResult) -> float:
        """Calculate overall completeness score (0-100)"""
        total_categories = len(self.semantic_categories)
        missing_categories = len(result.missing_information)
        semantic_gaps = len(result.semantic_gaps)
        
        # Base score from category coverage
        category_score = max(0, (total_categories - missing_categories) / total_categories)
        
        # Penalty for semantic gaps
        gap_penalty = min(semantic_gaps * 0.1, 0.3)  # Max 30% penalty
        
        final_score = max(0, category_score - gap_penalty)
        return round(final_score * 100, 1)

    def generate_recommendations(self, result: AuditResult, json_analysis: JsonStructureAnalysis) -> List[str]:
        """Generate recommendations for improving database completeness"""
        recommendations = []
        
        if result.database_completeness_score < 70:
            recommendations.append("🚨 Critical: Database completeness below 70% - major information missing")
        
        if result.missing_information:
            recommendations.append(f"📋 Import missing categories: {', '.join(result.missing_information[:3])}")
        
        if result.semantic_gaps:
            recommendations.append(f"🔍 Address semantic gaps in: {', '.join([gap.split(':')[0] for gap in result.semantic_gaps[:3]])}")
        
        if json_analysis.redundant_fields:
            recommendations.append(f"🧹 Clean redundant JSON fields: {len(json_analysis.redundant_fields)} identified")
        
        if len(json_analysis.semantic_content_fields) > 20:
            recommendations.append("📊 Consider consolidating JSON structure - high field count detected")
        
        if result.database_completeness_score > 90:
            recommendations.append("✅ Excellent completeness - minor optimizations recommended")
        
        return recommendations

    async def generate_audit_report(self, results: List[AuditResult]) -> str:
        """Generate comprehensive audit report"""
        report = []
        report.append("=" * 80)
        report.append("CDL DATABASE COMPLETENESS AUDIT REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Characters Audited: {len(results)}")
        report.append("=" * 80)
        
        # Summary statistics
        avg_score = sum(r.database_completeness_score for r in results) / len(results) if results else 0
        high_scores = [r for r in results if r.database_completeness_score >= 80]
        low_scores = [r for r in results if r.database_completeness_score < 50]
        
        report.append(f"\n📊 SUMMARY STATISTICS:")
        report.append(f"Average Completeness Score: {avg_score:.1f}%")
        report.append(f"High Completeness (80%+): {len(high_scores)} characters")
        report.append(f"Low Completeness (<50%): {len(low_scores)} characters")
        
        # Sort by completeness score for prioritized reporting
        results_sorted = sorted(results, key=lambda x: x.database_completeness_score, reverse=True)
        
        report.append(f"\n🎯 CHARACTER COMPLETENESS DETAILS:")
        report.append("-" * 80)
        
        for result in results_sorted:
            score_icon = "🟢" if result.database_completeness_score >= 80 else "🟡" if result.database_completeness_score >= 50 else "🔴"
            
            report.append(f"\n{score_icon} {result.character_name}")
            report.append(f"   Completeness Score: {result.database_completeness_score}%")
            report.append(f"   JSON File: {Path(result.json_file_path).name}")
            
            if result.missing_information:
                report.append(f"   ⚠️ Missing Information:")
                for missing in result.missing_information[:3]:  # Show top 3
                    report.append(f"      • {missing}")
                if len(result.missing_information) > 3:
                    report.append(f"      • ... and {len(result.missing_information) - 3} more")
            
            if result.semantic_gaps:
                report.append(f"   🔍 Semantic Gaps:")
                for gap in result.semantic_gaps[:2]:  # Show top 2
                    report.append(f"      • {gap}")
            
            if result.recommendations:
                report.append(f"   💡 Top Recommendations:")
                for rec in result.recommendations[:2]:  # Show top 2
                    report.append(f"      • {rec}")
        
        # Priority action items
        report.append(f"\n🚨 PRIORITY ACTION ITEMS:")
        report.append("-" * 80)
        
        if low_scores:
            report.append(f"1. Critical Import Needed: {', '.join([r.character_name for r in low_scores])}")
        
        # Find most common missing categories
        all_missing = []
        for result in results:
            all_missing.extend([m.split(':')[0] for m in result.missing_information])
        
        if all_missing:
            from collections import Counter
            common_missing = Counter(all_missing).most_common(3)
            report.append(f"2. Most Common Missing Categories:")
            for category, count in common_missing:
                report.append(f"   • {category}: {count} characters affected")
        
        # Recommendations for overall improvement
        report.append(f"\n📋 SYSTEM-WIDE RECOMMENDATIONS:")
        report.append("-" * 80)
        
        if avg_score < 70:
            report.append("• 🚨 Implement comprehensive JSON-to-database import process")
            report.append("• 🔧 Review database schema for missing semantic categories")
        
        report.append("• 🧹 Clean redundant JSON fields to improve maintainability")
        report.append("• 📊 Consider automated sync process between JSON and database")
        report.append("• 🔄 Implement regular completeness monitoring")
        
        return "\n".join(report)


async def main():
    """Main execution function"""
    print("🔍 Starting CDL Database Completeness Audit...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize auditor
        auditor = CDLCompletenessAuditor()
        await auditor.initialize()
        
        # Run audit
        print("📊 Analyzing character completeness...")
        results = await auditor.audit_all_characters()
        
        # Generate report
        print("📝 Generating audit report...")
        report = await auditor.generate_audit_report(results)
        
        # Save report
        report_path = Path("validation_reports/cdl_completeness_audit.md")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Audit complete! Report saved to: {report_path}")
        print("\n" + "="*50)
        print("AUDIT SUMMARY")
        print("="*50)
        
        # Print summary to console
        avg_score = sum(r.database_completeness_score for r in results) / len(results) if results else 0
        print(f"Characters Audited: {len(results)}")
        print(f"Average Completeness: {avg_score:.1f}%")
        
        high_scores = [r for r in results if r.database_completeness_score >= 80]
        low_scores = [r for r in results if r.database_completeness_score < 50]
        
        print(f"High Completeness (80%+): {len(high_scores)}")
        print(f"Low Completeness (<50%): {len(low_scores)}")
        
        if low_scores:
            print(f"\n🚨 Critical Action Needed:")
            for result in low_scores:
                print(f"   • {result.character_name}: {result.database_completeness_score}%")
        
        print(f"\n📄 Full report: {report_path}")
        
    except Exception as e:
        logger.error(f"❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)