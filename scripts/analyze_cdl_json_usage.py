#!/usr/bin/env python3
"""
CDL JSON Field Usage Analysis Tool

Analyzes which JSON fields are actually used in the codebase versus
which are potentially redundant or auto-generated.

This helps identify:
1. Active JSON fields that have semantic impact on prompts
2. Redundant or auto-generated fields that clutter the JSON
3. Missing implementation for potentially useful fields
4. Structural optimization opportunities

Usage:
    python scripts/analyze_cdl_json_usage.py
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@dataclass
class FieldUsageAnalysis:
    """Analysis of how JSON fields are used in codebase"""
    field_path: str
    is_used_in_code: bool = False
    usage_locations: List[str] = field(default_factory=list)
    semantic_value: str = ""
    is_redundant: bool = False
    redundancy_reason: str = ""
    characters_using: Set[str] = field(default_factory=set)
    value_variety: int = 0  # How many different values across characters
    is_auto_generated: bool = False


@dataclass
class CharacterFieldAnalysis:
    """Analysis of fields in a single character JSON"""
    character_name: str
    json_file: str
    total_fields: int = 0
    semantic_fields: int = 0
    redundant_fields: int = 0
    auto_generated_fields: int = 0
    field_details: List[FieldUsageAnalysis] = field(default_factory=list)


class CDLJsonUsageAnalyzer:
    """Analyzes JSON field usage patterns across CDL system"""
    
    def __init__(self):
        self.backup_dir = Path("characters/examples_legacy_backup")
        self.src_dir = Path("src")
        
        # Track all field paths across all characters
        self.all_field_paths: Dict[str, FieldUsageAnalysis] = {}
        self.character_analyses: List[CharacterFieldAnalysis] = []
        
        # Code usage patterns to search for
        self.usage_patterns = [
            # Direct property access patterns
            r'\.(\w+)',  # .property_name
            r'\[[\'"]([\w_]+)[\'\"]\]',  # ['property_name']
            r'get\([\'"]([\w_]+)[\'\"]\)',  # get('property_name')
            r'getattr\([^,]+,\s*[\'"]([\w_]+)[\'\"]\)',  # getattr(obj, 'property_name')
            
            # JSON key references
            r'[\'"]([\w_]+)[\'"]\s*:',  # "property_name":
            r'[\'"]([\w_]+)[\'"]\s*in\s+',  # "property_name" in
            
            # CDL specific patterns
            r'character\.(\w+)',  # character.property
            r'cdl\.(\w+)',  # cdl.property
            r'personality\.(\w+)',  # personality.property
            r'identity\.(\w+)',  # identity.property
            r'communication\.(\w+)',  # communication.property
            r'values\.(\w+)',  # values.property
        ]

    def analyze_all_characters(self) -> List[CharacterFieldAnalysis]:
        """Analyze field usage across all character JSON files"""
        print("🔍 Starting CDL JSON field usage analysis...")
        
        # Find all JSON backup files
        json_files = list(self.backup_dir.glob("*.json"))
        print(f"📁 Found {len(json_files)} JSON files to analyze")
        
        # Analyze each character
        for json_file in json_files:
            if json_file.stem in ['default_assistant']:  # Skip non-character files
                continue
                
            try:
                analysis = self.analyze_character_json(json_file)
                self.character_analyses.append(analysis)
                print(f"✅ Analyzed {analysis.character_name}")
            except Exception as e:
                print(f"❌ Failed to analyze {json_file.stem}: {e}")
        
        # Analyze code usage for all discovered fields
        print("🔍 Analyzing code usage patterns...")
        self.analyze_code_usage()
        
        # Detect redundancy patterns
        print("🧹 Detecting redundancy patterns...")
        self.detect_redundancy_patterns()
        
        return self.character_analyses

    def analyze_character_json(self, json_file: Path) -> CharacterFieldAnalysis:
        """Analyze a single character JSON file"""
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        character_name = self.extract_character_name(json_data)
        analysis = CharacterFieldAnalysis(
            character_name=character_name,
            json_file=str(json_file)
        )
        
        # Traverse JSON structure and catalog all fields
        self.traverse_json_fields(json_data, analysis, character_name)
        
        return analysis

    def traverse_json_fields(self, obj: Any, analysis: CharacterFieldAnalysis, character_name: str, path: str = ""):
        """Recursively traverse JSON and catalog field usage"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                analysis.total_fields += 1
                
                # Create or update field analysis
                if current_path not in self.all_field_paths:
                    self.all_field_paths[current_path] = FieldUsageAnalysis(field_path=current_path)
                
                field_analysis = self.all_field_paths[current_path]
                field_analysis.characters_using.add(character_name)
                
                # Analyze semantic value
                if isinstance(value, str) and value.strip():
                    field_analysis.semantic_value = value.strip()[:100]  # First 100 chars
                    if len(value.strip()) > 10:  # Meaningful content
                        analysis.semantic_fields += 1
                
                # Check for auto-generation patterns
                if self.is_auto_generated_field(key, value):
                    field_analysis.is_auto_generated = True
                    analysis.auto_generated_fields += 1
                
                analysis.field_details.append(field_analysis)
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    self.traverse_json_fields(value, analysis, character_name, current_path)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self.traverse_json_fields(item, analysis, character_name, f"{path}[{i}]")

    def is_auto_generated_field(self, key: str, value: Any) -> bool:
        """Detect if a field appears to be auto-generated"""
        auto_gen_indicators = [
            # Numbered variants (often auto-generated)
            re.match(r'\w+_\d+$', key),  # field_1, field_2, etc.
            
            # Empty or placeholder values
            isinstance(value, str) and value in ["", "TODO", "TBD", "Generated"],
            
            # Generic descriptions
            isinstance(value, str) and value.strip().lower() in [
                "description", "trait", "value", "belief", "placeholder"
            ],
            
            # Metadata fields that are often auto-generated
            key in ['version', 'created_date', 'updated_date', 'id', 'character_id'],
            
            # Format indicators
            key in ['cdl_version', 'format', 'license'],
        ]
        
        return any(auto_gen_indicators)

    def analyze_code_usage(self):
        """Analyze which JSON fields are actually used in the codebase"""
        # Find all Python files in src directory
        python_files = list(self.src_dir.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Search for field usage patterns
                for field_path in self.all_field_paths:
                    field_parts = field_path.split('.')
                    
                    # Check various usage patterns
                    for pattern in self.usage_patterns:
                        # Check each part of the field path
                        for part in field_parts:
                            if len(part) > 2:  # Skip very short field names to reduce false positives
                                matches = re.findall(pattern, content)
                                if part in matches:
                                    self.all_field_paths[field_path].is_used_in_code = True
                                    location = f"{py_file.relative_to(Path.cwd())}:{part}"
                                    if location not in self.all_field_paths[field_path].usage_locations:
                                        self.all_field_paths[field_path].usage_locations.append(location)
            
            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}")

    def detect_redundancy_patterns(self):
        """Detect redundant fields across characters"""
        # Group fields by base name (without _1, _2, etc.)
        field_groups = defaultdict(list)
        
        for field_path, analysis in self.all_field_paths.items():
            # Extract base field name
            base_name = re.sub(r'_\d+$', '', field_path.split('.')[-1])
            field_groups[base_name].append((field_path, analysis))
        
        # Detect redundancy within groups
        for base_name, fields in field_groups.items():
            if len(fields) > 1:
                # Multiple fields with same base name - likely redundant
                values = []
                for field_path, analysis in fields:
                    if analysis.semantic_value:
                        values.append(analysis.semantic_value)
                
                # Check for similar/duplicate content
                if len(set(values)) == 1 and values:  # All same value
                    for field_path, analysis in fields:
                        analysis.is_redundant = True
                        analysis.redundancy_reason = f"Duplicate content in {base_name} group"
                
                elif len(values) > 1:
                    # Check for very similar content (>80% overlap)
                    for i, (field_path, analysis) in enumerate(fields):
                        similar_count = 0
                        for other_value in values:
                            if analysis.semantic_value and other_value:
                                # Simple similarity check
                                words1 = set(analysis.semantic_value.lower().split())
                                words2 = set(other_value.lower().split())
                                if len(words1) > 0 and len(words2) > 0:
                                    overlap = len(words1 & words2) / max(len(words1), len(words2))
                                    if overlap > 0.8:
                                        similar_count += 1
                        
                        if similar_count >= len(values) * 0.5:  # Similar to >50% of group
                            analysis.is_redundant = True
                            analysis.redundancy_reason = f"Similar content in {base_name} group"

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

    def calculate_value_variety(self):
        """Calculate variety of values for each field across characters"""
        for field_path, analysis in self.all_field_paths.items():
            # Count unique values for this field across all characters
            unique_values = set()
            for char_analysis in self.character_analyses:
                for field_detail in char_analysis.field_details:
                    if field_detail.field_path == field_path and field_detail.semantic_value:
                        unique_values.add(field_detail.semantic_value[:50])  # First 50 chars for comparison
            
            analysis.value_variety = len(unique_values)

    def generate_usage_report(self) -> str:
        """Generate comprehensive field usage report"""
        # Calculate value variety
        self.calculate_value_variety()
        
        report = []
        report.append("=" * 80)
        report.append("CDL JSON FIELD USAGE ANALYSIS REPORT")
        report.append(f"Characters Analyzed: {len(self.character_analyses)}")
        report.append(f"Total Unique Fields: {len(self.all_field_paths)}")
        report.append("=" * 80)
        
        # Summary statistics
        used_fields = [f for f in self.all_field_paths.values() if f.is_used_in_code]
        unused_fields = [f for f in self.all_field_paths.values() if not f.is_used_in_code]
        redundant_fields = [f for f in self.all_field_paths.values() if f.is_redundant]
        auto_gen_fields = [f for f in self.all_field_paths.values() if f.is_auto_generated]
        
        report.append(f"\n📊 FIELD USAGE SUMMARY:")
        report.append(f"Used in Code: {len(used_fields)} fields ({len(used_fields)/len(self.all_field_paths)*100:.1f}%)")
        report.append(f"Unused/Orphaned: {len(unused_fields)} fields ({len(unused_fields)/len(self.all_field_paths)*100:.1f}%)")
        report.append(f"Redundant: {len(redundant_fields)} fields ({len(redundant_fields)/len(self.all_field_paths)*100:.1f}%)")
        report.append(f"Auto-Generated: {len(auto_gen_fields)} fields ({len(auto_gen_fields)/len(self.all_field_paths)*100:.1f}%)")
        
        # Character-by-character analysis
        report.append(f"\n🎭 CHARACTER FIELD ANALYSIS:")
        report.append("-" * 80)
        
        for char_analysis in sorted(self.character_analyses, key=lambda x: x.character_name):
            total = char_analysis.total_fields
            semantic = char_analysis.semantic_fields
            redundant = char_analysis.redundant_fields
            auto_gen = char_analysis.auto_generated_fields
            
            efficiency = (semantic / total * 100) if total > 0 else 0
            efficiency_icon = "🟢" if efficiency >= 70 else "🟡" if efficiency >= 50 else "🔴"
            
            report.append(f"\n{efficiency_icon} {char_analysis.character_name}")
            report.append(f"   Total Fields: {total}")
            report.append(f"   Semantic Content: {semantic} ({semantic/total*100:.1f}%)")
            report.append(f"   Auto-Generated: {auto_gen} ({auto_gen/total*100:.1f}%)")
            report.append(f"   Efficiency Score: {efficiency:.1f}%")
        
        # Most used fields
        report.append(f"\n✅ MOST USED FIELDS (Actually implemented):")
        report.append("-" * 80)
        
        used_sorted = sorted(used_fields, key=lambda x: len(x.usage_locations), reverse=True)
        for field in used_sorted[:10]:  # Top 10
            report.append(f"• {field.field_path}")
            report.append(f"  Used in: {len(field.usage_locations)} locations")
            report.append(f"  Characters: {len(field.characters_using)}")
            if field.usage_locations:
                report.append(f"  Example: {field.usage_locations[0]}")
        
        # Orphaned fields with high semantic value
        report.append(f"\n🔍 HIGH-VALUE ORPHANED FIELDS (Not implemented but valuable):")
        report.append("-" * 80)
        
        valuable_orphaned = [
            f for f in unused_fields 
            if len(f.characters_using) > 1 and f.semantic_value and len(f.semantic_value) > 20
        ]
        valuable_orphaned = sorted(valuable_orphaned, key=lambda x: len(x.characters_using), reverse=True)
        
        for field in valuable_orphaned[:15]:  # Top 15
            report.append(f"• {field.field_path}")
            report.append(f"  Characters using: {len(field.characters_using)}")
            report.append(f"  Example value: {field.semantic_value[:60]}...")
            report.append(f"  💡 Consider implementing in CDL system")
        
        # Redundant fields to clean up
        report.append(f"\n🧹 REDUNDANT FIELDS (Candidates for cleanup):")
        report.append("-" * 80)
        
        redundant_sorted = sorted(redundant_fields, key=lambda x: len(x.characters_using), reverse=True)
        for field in redundant_sorted[:10]:  # Top 10
            report.append(f"• {field.field_path}")
            report.append(f"  Reason: {field.redundancy_reason}")
            report.append(f"  Characters affected: {len(field.characters_using)}")
        
        # Auto-generated fields
        report.append(f"\n🤖 AUTO-GENERATED FIELDS (Review for necessity):")
        report.append("-" * 80)
        
        auto_gen_sorted = sorted(auto_gen_fields, key=lambda x: len(x.characters_using), reverse=True)
        for field in auto_gen_sorted[:10]:  # Top 10
            report.append(f"• {field.field_path}")
            report.append(f"  Characters: {len(field.characters_using)}")
            if field.semantic_value:
                report.append(f"  Example: {field.semantic_value[:40]}...")
        
        # Recommendations
        report.append(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        report.append("-" * 80)
        
        unused_percentage = len(unused_fields) / len(self.all_field_paths) * 100
        redundant_percentage = len(redundant_fields) / len(self.all_field_paths) * 100
        
        if unused_percentage > 50:
            report.append(f"🚨 HIGH PRIORITY: {unused_percentage:.1f}% of fields are unused - major cleanup needed")
        
        if redundant_percentage > 20:
            report.append(f"🧹 CLEANUP: {redundant_percentage:.1f}% of fields are redundant - consolidation recommended")
        
        report.append(f"📋 Implement high-value orphaned fields in CDL database")
        report.append(f"🔧 Remove or consolidate redundant field patterns")
        report.append(f"🤖 Review auto-generated fields for actual necessity")
        report.append(f"📊 Focus on {len(used_fields)} proven-useful fields for core CDL schema")
        
        # Field category analysis
        report.append(f"\n📂 FIELD CATEGORY BREAKDOWN:")
        report.append("-" * 80)
        
        categories = defaultdict(list)
        for field_path, analysis in self.all_field_paths.items():
            # Extract category from field path
            parts = field_path.split('.')
            if len(parts) > 1:
                category = parts[0]
            else:
                category = "root"
            categories[category].append(analysis)
        
        for category, fields in sorted(categories.items()):
            used_in_cat = len([f for f in fields if f.is_used_in_code])
            total_in_cat = len(fields)
            usage_rate = (used_in_cat / total_in_cat * 100) if total_in_cat > 0 else 0
            
            rate_icon = "🟢" if usage_rate >= 50 else "🟡" if usage_rate >= 25 else "🔴"
            report.append(f"{rate_icon} {category}: {used_in_cat}/{total_in_cat} used ({usage_rate:.1f}%)")
        
        return "\n".join(report)


def main():
    """Main execution function"""
    print("🔍 Starting CDL JSON field usage analysis...")
    
    analyzer = CDLJsonUsageAnalyzer()
    analyzer.analyze_all_characters()
    
    # Generate report
    print("📝 Generating usage analysis report...")
    report = analyzer.generate_usage_report()
    
    # Save report
    report_path = Path("validation_reports/cdl_json_usage_analysis.md")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Analysis complete! Report saved to: {report_path}")
    
    # Print summary
    total_fields = len(analyzer.all_field_paths)
    used_fields = len([f for f in analyzer.all_field_paths.values() if f.is_used_in_code])
    unused_fields = len([f for f in analyzer.all_field_paths.values() if not f.is_used_in_code])
    
    print(f"\n📊 QUICK SUMMARY:")
    print(f"Total Unique Fields: {total_fields}")
    print(f"Used in Code: {used_fields} ({used_fields/total_fields*100:.1f}%)")
    print(f"Unused/Orphaned: {unused_fields} ({unused_fields/total_fields*100:.1f}%)")
    print(f"\n📄 Full analysis: {report_path}")


if __name__ == "__main__":
    main()