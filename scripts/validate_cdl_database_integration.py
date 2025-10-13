#!/usr/bin/env python3
"""
CDL Database Integration Validation Tool

Validates that:
1. CDL database contains semantic equivalent of valuable JSON data
2. CDL integration code properly queries database for prompt building
3. Semantic mapping between old JSON schema and new CDL schema is complete

This focuses on the CURRENT system - CDL database + integration code,
not the legacy JSON files.

Usage:
    python scripts/validate_cdl_database_integration.py
"""

import asyncio
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.postgres_pool_manager import get_postgres_pool


@dataclass
class SemanticMappingResult:
    """Results of semantic mapping validation"""
    json_concept: str
    json_examples: List[str] = field(default_factory=list)
    database_representation: str = ""
    database_table: str = ""
    integration_method: str = ""
    is_mapped: bool = False
    mapping_quality: str = "none"  # "excellent", "good", "partial", "poor", "none"
    missing_semantic_value: str = ""


@dataclass
class CDLIntegrationAnalysis:
    """Analysis of how CDL integration uses database"""
    character_name: str
    database_tables_used: Set[str] = field(default_factory=set)
    integration_methods: List[str] = field(default_factory=list)
    prompt_sections_populated: List[str] = field(default_factory=list)
    semantic_gaps: List[str] = field(default_factory=list)
    integration_quality_score: float = 0.0


@dataclass
class DatabaseContentAnalysis:
    """Analysis of database content richness"""
    table_name: str
    character_count: int = 0
    total_records: int = 0
    semantic_richness_score: float = 0.0
    example_content: List[str] = field(default_factory=list)
    content_variety: int = 0


class CDLDatabaseIntegrationValidator:
    """Validates CDL database integration and semantic mapping"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path("characters/examples_legacy_backup")
        self.database_pool = None
        
        # Define semantic concept categories from JSON that should be in database
        self.semantic_concepts = {
            'identity_core': {
                'json_patterns': ['name', 'occupation', 'description', 'age', 'location'],
                'database_table': 'characters',
                'integration_method': 'load_character',
                'importance': 'critical'
            },
            'personality_traits': {
                'json_patterns': ['big_five', 'personality', 'traits', 'temperament'],
                'database_table': 'character_background',
                'integration_method': 'extract_personal_knowledge',
                'importance': 'high'
            },
            'communication_style': {
                'json_patterns': ['communication_style', 'emoji_usage', 'formality', 'tone'],
                'database_table': 'character_communication_patterns',
                'integration_method': 'get_communication_patterns',
                'importance': 'high'
            },
            'background_history': {
                'json_patterns': ['education', 'career_history', 'personal_history', 'backstory'],
                'database_table': 'character_background',
                'integration_method': 'extract_personal_knowledge',
                'importance': 'medium'
            },
            'values_beliefs': {
                'json_patterns': ['values_and_beliefs', 'values', 'beliefs', 'fears', 'dreams'],
                'database_table': 'character_background',
                'integration_method': 'extract_personal_knowledge',
                'importance': 'high'
            },
            'relationships': {
                'json_patterns': ['relationships', 'family', 'colleagues', 'connections'],
                'database_table': 'character_relationships',
                'integration_method': 'query_character_knowledge',
                'importance': 'medium'
            },
            'abilities_skills': {
                'json_patterns': ['abilities', 'skills', 'expertise', 'talents'],
                'database_table': 'character_abilities',
                'integration_method': 'query_character_knowledge',
                'importance': 'medium'
            },
            'memories_experiences': {
                'json_patterns': ['memories', 'experiences', 'formative_events'],
                'database_table': 'character_memories',
                'integration_method': 'extract_episodic_memories',
                'importance': 'medium'
            },
            'behavioral_triggers': {
                'json_patterns': ['triggers', 'reactions', 'response_patterns'],
                'database_table': 'character_behavioral_triggers',
                'integration_method': 'get_behavioral_triggers',
                'importance': 'low'
            },
            'mystical_essence': {
                'json_patterns': ['essence', 'nature', 'existence_method', 'powers'],
                'database_table': 'character_essence',
                'integration_method': 'get_essence_data',
                'importance': 'character_specific'
            },
            'physical_appearance': {
                'json_patterns': ['physical_appearance', 'digital_communication', 'style'],
                'database_table': 'character_appearance',
                'integration_method': 'get_appearance_data',
                'importance': 'low'
            }
        }

    async def initialize(self):
        """Initialize database connection"""
        try:
            self.database_pool = await get_postgres_pool()
            self.logger.info("✅ Database connection established")
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to database: {e}")
            raise

    async def validate_all_characters(self) -> Dict[str, Any]:
        """Validate CDL database integration for all characters"""
        print("🔍 Starting CDL Database Integration Validation...")
        
        # Get all characters from database
        characters = await self.get_all_characters_from_database()
        print(f"📊 Found {len(characters)} characters in database")
        
        # Analyze database content richness
        print("📊 Analyzing database content richness...")
        database_analysis = await self.analyze_database_content()
        
        # Validate semantic mapping for each character
        print("🔍 Validating semantic mapping...")
        character_analyses = {}
        semantic_mapping_results = []
        
        for character in characters:
            print(f"🎭 Analyzing {character['name']}...")
            
            # Get CDL integration analysis
            integration_analysis = await self.analyze_cdl_integration(character)
            character_analyses[character['name']] = integration_analysis
            
            # Get semantic mapping validation
            if self.backup_dir.exists():
                mapping_results = await self.validate_semantic_mapping(character)
                semantic_mapping_results.extend(mapping_results)
        
        # Analyze CDL integration code usage
        print("🔧 Analyzing CDL integration code...")
        integration_code_analysis = await self.analyze_integration_code()
        
        return {
            'characters': character_analyses,
            'database_content': database_analysis,
            'semantic_mapping': semantic_mapping_results,
            'integration_code': integration_code_analysis,
            'validation_timestamp': datetime.now().isoformat()
        }

    async def get_all_characters_from_database(self) -> List[Dict]:
        """Get all characters from CDL database"""
        if not self.database_pool:
            return []
        
        async with self.database_pool.acquire() as conn:
            query = """
                SELECT id, name, occupation, description, normalized_name, 
                       created_date, updated_date
                FROM characters 
                ORDER BY name
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def analyze_database_content(self) -> Dict[str, DatabaseContentAnalysis]:
        """Analyze content richness in each CDL database table"""
        if not self.database_pool:
            return {}
        
        analyses = {}
        
        # CDL tables to analyze
        tables = [
            'characters', 'character_metadata', 'character_appearance',
            'character_background', 'character_relationships', 'character_memories',
            'character_abilities', 'character_communication_patterns',
            'character_behavioral_triggers', 'character_essence', 'character_instructions'
        ]
        
        async with self.database_pool.acquire() as conn:
            for table in tables:
                try:
                    analysis = DatabaseContentAnalysis(table_name=table)
                    
                    # Get basic stats
                    count_query = f"SELECT COUNT(*) as total FROM {table}"
                    if table != 'characters':
                        count_query = f"SELECT COUNT(*) as total FROM {table}"
                        char_count_query = f"SELECT COUNT(DISTINCT character_id) as char_count FROM {table}"
                        
                        total_result = await conn.fetchval(count_query)
                        char_count_result = await conn.fetchval(char_count_query)
                        
                        analysis.total_records = total_result or 0
                        analysis.character_count = char_count_result or 0
                    else:
                        total_result = await conn.fetchval(count_query)
                        analysis.total_records = total_result or 0
                        analysis.character_count = total_result or 0
                    
                    # Get content examples (description/text fields)
                    if table == 'characters':
                        example_query = "SELECT name, occupation, description FROM characters LIMIT 5"
                    else:
                        # Try to find text content fields
                        columns_query = f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = '{table}' 
                            AND data_type IN ('text', 'character varying')
                            AND column_name NOT IN ('id', 'character_id', 'created_date', 'updated_date')
                        """
                        columns = await conn.fetch(columns_query)
                        text_columns = [col['column_name'] for col in columns[:3]]  # First 3 text columns
                        
                        if text_columns:
                            example_query = f"SELECT {', '.join(text_columns)} FROM {table} LIMIT 5"
                        else:
                            example_query = f"SELECT * FROM {table} LIMIT 3"
                    
                    try:
                        examples = await conn.fetch(example_query)
                        for row in examples:
                            row_content = []
                            for key, value in row.items():
                                if isinstance(value, str) and len(value.strip()) > 10:
                                    row_content.append(f"{key}: {value[:50]}...")
                            if row_content:
                                analysis.example_content.append(" | ".join(row_content))
                    except Exception as e:
                        self.logger.debug(f"Could not get examples for {table}: {e}")
                    
                    # Calculate semantic richness (content variety and meaningfulness)
                    if analysis.total_records > 0 and analysis.character_count > 0:
                        content_per_char = analysis.total_records / analysis.character_count
                        variety_score = min(content_per_char / 5.0, 1.0)  # Normalize to 0-1
                        example_score = min(len(analysis.example_content) / 5.0, 1.0)
                        analysis.semantic_richness_score = (variety_score + example_score) / 2.0
                    
                    analysis.content_variety = len(analysis.example_content)
                    analyses[table] = analysis
                    
                except Exception as e:
                    self.logger.debug(f"Could not analyze table {table}: {e}")
                    analyses[table] = DatabaseContentAnalysis(table_name=table)
        
        return analyses

    async def analyze_cdl_integration(self, character: Dict) -> CDLIntegrationAnalysis:
        """Analyze how CDL integration uses database for this character"""
        analysis = CDLIntegrationAnalysis(character_name=character['name'])
        
        if not self.database_pool:
            return analysis
        
        character_id = character['id']
        
        # Check which tables have data for this character
        tables_with_data = []
        async with self.database_pool.acquire() as conn:
            for concept, config in self.semantic_concepts.items():
                table = config['database_table']
                if table == 'characters':
                    continue  # Always has data
                
                try:
                    count = await conn.fetchval(
                        f"SELECT COUNT(*) FROM {table} WHERE character_id = $1",
                        character_id
                    )
                    if count > 0:
                        tables_with_data.append(table)
                        analysis.database_tables_used.add(table)
                        analysis.integration_methods.append(config['integration_method'])
                except Exception as e:
                    self.logger.debug(f"Could not check {table} for character {character_id}: {e}")
        
        # Analyze integration completeness
        total_concepts = len(self.semantic_concepts)
        implemented_concepts = len(tables_with_data)
        analysis.integration_quality_score = implemented_concepts / total_concepts if total_concepts > 0 else 0.0
        
        # Identify gaps
        for concept, config in self.semantic_concepts.items():
            if config['database_table'] not in tables_with_data and config['importance'] in ['critical', 'high']:
                analysis.semantic_gaps.append(f"Missing {concept} data (importance: {config['importance']})")
        
        return analysis

    async def validate_semantic_mapping(self, character: Dict) -> List[SemanticMappingResult]:
        """Validate semantic mapping between JSON and database for character"""
        results = []
        
        # Find corresponding JSON file for this character
        json_file = self.find_json_file_for_character(character['name'])
        if not json_file:
            return results
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except Exception as e:
            self.logger.debug(f"Could not read JSON file {json_file}: {e}")
            return results
        
        # Check each semantic concept
        for concept, config in self.semantic_concepts.items():
            result = SemanticMappingResult(json_concept=concept)
            
            # Extract examples from JSON
            json_examples = self.extract_json_examples(json_data, config['json_patterns'])
            result.json_examples = json_examples
            
            # Check database representation
            db_content = await self.get_database_content_for_concept(character['id'], config)
            result.database_representation = db_content
            result.database_table = config['database_table']
            result.integration_method = config['integration_method']
            
            # Evaluate mapping quality
            if json_examples and db_content:
                # Both have content - check semantic similarity
                similarity = self.calculate_semantic_similarity(json_examples, db_content)
                if similarity > 0.8:
                    result.mapping_quality = "excellent"
                    result.is_mapped = True
                elif similarity > 0.6:
                    result.mapping_quality = "good" 
                    result.is_mapped = True
                elif similarity > 0.4:
                    result.mapping_quality = "partial"
                    result.is_mapped = True
                else:
                    result.mapping_quality = "poor"
                    result.missing_semantic_value = f"Database content doesn't match JSON semantic meaning"
            elif json_examples and not db_content:
                result.mapping_quality = "none"
                result.missing_semantic_value = f"JSON has {len(json_examples)} examples but no database content"
            elif not json_examples and db_content:
                result.mapping_quality = "excellent"  # Database has content, JSON didn't
                result.is_mapped = True
            else:
                result.mapping_quality = "none"
            
            results.append(result)
        
        return results

    def find_json_file_for_character(self, character_name: str) -> Optional[Path]:
        """Find JSON backup file for character"""
        # Try different name matching strategies
        name_variations = [
            character_name.lower().replace(' ', '_'),
            character_name.lower().replace(' ', ''),
            character_name.split()[0].lower(),  # First name
            character_name.replace('Dr. ', '').lower().replace(' ', '_'),
        ]
        
        for json_file in self.backup_dir.glob("*.json"):
            for variation in name_variations:
                if variation in json_file.stem.lower():
                    return json_file
        
        return None

    def extract_json_examples(self, json_data: Dict, patterns: List[str]) -> List[str]:
        """Extract examples from JSON that match patterns"""
        examples = []
        
        def search_json(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if key matches any pattern
                    if any(pattern in key.lower() for pattern in patterns):
                        if isinstance(value, str) and len(value.strip()) > 10:
                            examples.append(f"{current_path}: {value.strip()[:100]}")
                        elif isinstance(value, dict):
                            search_json(value, current_path)
                    else:
                        search_json(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_json(item, f"{path}[{i}]")
        
        search_json(json_data)
        return examples[:10]  # Limit to 10 examples

    async def get_database_content_for_concept(self, character_id: int, config: Dict) -> str:
        """Get database content for a semantic concept"""
        if not self.database_pool:
            return ""
        
        table = config['database_table']
        content_parts = []
        
        try:
            async with self.database_pool.acquire() as conn:
                if table == 'characters':
                    row = await conn.fetchrow(
                        "SELECT name, occupation, description FROM characters WHERE id = $1",
                        character_id
                    )
                    if row:
                        for key, value in row.items():
                            if value:
                                content_parts.append(f"{key}: {str(value)[:100]}")
                else:
                    # Get sample content from table
                    rows = await conn.fetch(
                        f"""SELECT * FROM {table} WHERE character_id = $1 LIMIT 5""",
                        character_id
                    )
                    for row in rows:
                        for key, value in row.items():
                            if isinstance(value, str) and len(value.strip()) > 10 and key not in ['id', 'character_id', 'created_date', 'updated_date']:
                                content_parts.append(f"{key}: {value.strip()[:100]}")
        
        except Exception as e:
            self.logger.debug(f"Could not get database content for {table}: {e}")
        
        return " | ".join(content_parts[:5])  # Limit content

    def calculate_semantic_similarity(self, json_examples: List[str], db_content: str) -> float:
        """Calculate semantic similarity between JSON examples and database content"""
        if not json_examples or not db_content:
            return 0.0
        
        # Simple word overlap similarity
        json_words = set()
        for example in json_examples:
            words = example.lower().split()
            json_words.update([w for w in words if len(w) > 3])
        
        db_words = set(db_content.lower().split())
        db_words = {w for w in db_words if len(w) > 3}
        
        if not json_words or not db_words:
            return 0.0
        
        overlap = len(json_words & db_words)
        total = len(json_words | db_words)
        
        return overlap / total if total > 0 else 0.0

    async def analyze_integration_code(self) -> Dict[str, Any]:
        """Analyze how CDL integration code uses the database"""
        integration_analysis = {
            'methods_found': [],
            'database_queries': [],
            'prompt_integration_points': [],
            'unused_database_tables': [],
            'recommendations': []
        }
        
        # Analyze CDL integration file
        cdl_integration_file = Path("src/prompts/cdl_ai_integration.py")
        if cdl_integration_file.exists():
            try:
                with open(cdl_integration_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find database query patterns
                import re
                query_patterns = [
                    r'SELECT.*FROM\s+(\w+)',
                    r'fetchrow.*characters',
                    r'character_(\w+)',
                    r'await.*\.query',
                ]
                
                for pattern in query_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    integration_analysis['database_queries'].extend(matches)
                
                # Find integration methods
                method_patterns = [
                    r'def\s+(\w*character\w*)\(',
                    r'def\s+(\w*cdl\w*)\(',
                    r'def\s+(\w*personal\w*)\(',
                    r'def\s+(\w*knowledge\w*)\(',
                ]
                
                for pattern in method_patterns:
                    matches = re.findall(pattern, content)
                    integration_analysis['methods_found'].extend(matches)
                
                # Find prompt integration points
                prompt_patterns = [
                    r'prompt\s*\+=.*character',
                    r'f".*{character',
                    r'character\.(\w+)',
                ]
                
                for pattern in prompt_patterns:
                    matches = re.findall(pattern, content)
                    integration_analysis['prompt_integration_points'].extend(matches)
            
            except Exception as e:
                self.logger.debug(f"Could not analyze CDL integration file: {e}")
        
        # Generate recommendations
        if len(integration_analysis['database_queries']) < 5:
            integration_analysis['recommendations'].append("Limited database query patterns found - may not be fully utilizing CDL database")
        
        if not integration_analysis['methods_found']:
            integration_analysis['recommendations'].append("No clear character/CDL integration methods found")
        
        return integration_analysis

    async def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("CDL DATABASE INTEGRATION VALIDATION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # Database content analysis
        db_analysis = validation_results['database_content']
        report.append(f"\n📊 DATABASE CONTENT ANALYSIS:")
        report.append("-" * 80)
        
        total_tables = len(db_analysis)
        populated_tables = len([a for a in db_analysis.values() if a.total_records > 0])
        
        report.append(f"Total CDL Tables: {total_tables}")
        report.append(f"Populated Tables: {populated_tables} ({populated_tables/total_tables*100:.1f}%)")
        
        # Table-by-table analysis
        for table_name, analysis in sorted(db_analysis.items()):
            if analysis.total_records > 0:
                richness_icon = "🟢" if analysis.semantic_richness_score >= 0.7 else "🟡" if analysis.semantic_richness_score >= 0.4 else "🔴"
                report.append(f"\n{richness_icon} {table_name}")
                report.append(f"   Records: {analysis.total_records}")
                report.append(f"   Characters: {analysis.character_count}")
                report.append(f"   Richness: {analysis.semantic_richness_score:.1f}")
                if analysis.example_content:
                    report.append(f"   Example: {analysis.example_content[0][:80]}...")
        
        # Character integration analysis
        char_analyses = validation_results['characters']
        report.append(f"\n🎭 CHARACTER INTEGRATION ANALYSIS:")
        report.append("-" * 80)
        
        avg_integration = sum(a.integration_quality_score for a in char_analyses.values()) / len(char_analyses) if char_analyses else 0
        report.append(f"Average Integration Quality: {avg_integration:.1f}")
        
        for char_name, analysis in sorted(char_analyses.items()):
            quality_icon = "🟢" if analysis.integration_quality_score >= 0.7 else "🟡" if analysis.integration_quality_score >= 0.4 else "🔴"
            report.append(f"\n{quality_icon} {char_name}")
            report.append(f"   Integration Score: {analysis.integration_quality_score:.1f}")
            report.append(f"   Database Tables Used: {len(analysis.database_tables_used)}")
            report.append(f"   Tables: {', '.join(analysis.database_tables_used)}")
            if analysis.semantic_gaps:
                report.append(f"   Gaps: {', '.join(analysis.semantic_gaps[:2])}")
        
        # Semantic mapping analysis
        semantic_results = validation_results['semantic_mapping']
        if semantic_results:
            report.append(f"\n🔍 SEMANTIC MAPPING VALIDATION:")
            report.append("-" * 80)
            
            mapping_stats = {}
            for result in semantic_results:
                quality = result.mapping_quality
                mapping_stats[quality] = mapping_stats.get(quality, 0) + 1
            
            total_mappings = len(semantic_results)
            report.append(f"Total Concept Mappings Analyzed: {total_mappings}")
            for quality, count in sorted(mapping_stats.items()):
                report.append(f"{quality.title()}: {count} ({count/total_mappings*100:.1f}%)")
            
            # Show examples of good and poor mappings
            excellent_mappings = [r for r in semantic_results if r.mapping_quality == "excellent"]
            poor_mappings = [r for r in semantic_results if r.mapping_quality in ["poor", "none"]]
            
            if excellent_mappings:
                report.append(f"\n✅ EXCELLENT MAPPINGS (Examples):")
                for mapping in excellent_mappings[:3]:
                    report.append(f"• {mapping.json_concept} → {mapping.database_table}")
                    if mapping.database_representation:
                        report.append(f"  DB: {mapping.database_representation[:60]}...")
            
            if poor_mappings:
                report.append(f"\n⚠️ POOR/MISSING MAPPINGS:")
                for mapping in poor_mappings[:5]:
                    report.append(f"• {mapping.json_concept} → {mapping.database_table}")
                    if mapping.missing_semantic_value:
                        report.append(f"  Issue: {mapping.missing_semantic_value}")
        
        # Integration code analysis
        code_analysis = validation_results['integration_code']
        report.append(f"\n🔧 CDL INTEGRATION CODE ANALYSIS:")
        report.append("-" * 80)
        
        report.append(f"Database Query Patterns: {len(set(code_analysis['database_queries']))}")
        report.append(f"Integration Methods: {len(code_analysis['methods_found'])}")
        report.append(f"Prompt Integration Points: {len(code_analysis['prompt_integration_points'])}")
        
        if code_analysis['methods_found']:
            report.append(f"Methods Found: {', '.join(code_analysis['methods_found'][:5])}")
        
        if code_analysis['recommendations']:
            report.append(f"\nRecommendations:")
            for rec in code_analysis['recommendations']:
                report.append(f"• {rec}")
        
        # Overall recommendations
        report.append(f"\n💡 OVERALL RECOMMENDATIONS:")
        report.append("-" * 80)
        
        if populated_tables < total_tables * 0.7:
            report.append("🚨 Many CDL tables are empty - consider comprehensive JSON import")
        
        if avg_integration < 0.5:
            report.append("🔧 Low integration quality - improve CDL database utilization")
        
        poor_mapping_rate = len([r for r in semantic_results if r.mapping_quality in ["poor", "none"]]) / len(semantic_results) if semantic_results else 0
        if poor_mapping_rate > 0.3:
            report.append("📊 High rate of poor semantic mapping - review JSON→database conversion")
        
        report.append("✅ Focus on populated tables with high richness scores")
        report.append("🔍 Validate prompt quality with current database integration")
        report.append("📈 Monitor semantic richness scores for content quality")
        
        return "\n".join(report)


async def main():
    """Main execution function"""
    print("🔍 Starting CDL Database Integration Validation...")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize validator
        validator = CDLDatabaseIntegrationValidator()
        await validator.initialize()
        
        # Run validation
        print("📊 Validating CDL database integration...")
        results = await validator.validate_all_characters()
        
        # Generate report
        print("📝 Generating validation report...")
        report = await validator.generate_validation_report(results)
        
        # Save report
        report_path = Path("validation_reports/cdl_database_integration_validation.md")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Validation complete! Report saved to: {report_path}")
        
        # Print summary
        char_analyses = results['characters']
        db_analysis = results['database_content']
        
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        
        total_tables = len(db_analysis)
        populated_tables = len([a for a in db_analysis.values() if a.total_records > 0])
        avg_integration = sum(a.integration_quality_score for a in char_analyses.values()) / len(char_analyses) if char_analyses else 0
        
        print(f"Characters in Database: {len(char_analyses)}")
        print(f"Populated CDL Tables: {populated_tables}/{total_tables} ({populated_tables/total_tables*100:.1f}%)")
        print(f"Average Integration Quality: {avg_integration:.1f}")
        
        # Show table status
        print(f"\n📊 Table Population Status:")
        for table_name, analysis in sorted(db_analysis.items()):
            status = "✅" if analysis.total_records > 0 else "❌"
            print(f"   {status} {table_name}: {analysis.total_records} records")
        
        print(f"\n📄 Full report: {report_path}")
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)