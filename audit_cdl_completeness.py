#!/usr/bin/env python3
"""
Comprehensive CDL Content Audit - Check completeness and customization of all CDL sections.
Identifies missing sections, placeholder content, and customization levels.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class CDLContentAuditor:
    def __init__(self):
        self.audit_results = {}
        
    def check_section_completeness(self, data: Dict, section_path: str) -> Dict[str, Any]:
        """Check if a nested section exists and has content."""
        keys = section_path.split('.')
        current = data
        
        try:
            for key in keys:
                if key not in current:
                    return {'exists': False, 'reason': f'Missing key: {key}'}
                current = current[key]
                
            if not current:
                return {'exists': False, 'reason': 'Empty section'}
                
            if isinstance(current, dict) and not current:
                return {'exists': False, 'reason': 'Empty dictionary'}
                
            if isinstance(current, list) and not current:
                return {'exists': False, 'reason': 'Empty list'}
                
            return {'exists': True, 'content': current}
            
        except (KeyError, TypeError) as e:
            return {'exists': False, 'reason': f'Access error: {e}'}

    def analyze_customization_level(self, content: Any, section_name: str) -> str:
        """Analyze how well customized a section is."""
        if not content:
            return "MISSING"
            
        # Convert to string for analysis
        content_str = str(content).lower()
        
        # Check for placeholder patterns
        placeholder_patterns = [
            'placeholder', 'todo', 'tbd', 'fill in', 'example',
            'default', 'template', 'changeme', 'fixme',
            'lorem ipsum', 'sample text'
        ]
        
        for pattern in placeholder_patterns:
            if pattern in content_str:
                return "PLACEHOLDER"
        
        # Check for very short or generic content
        if isinstance(content, str) and len(content.strip()) < 10:
            return "MINIMAL"
            
        if isinstance(content, dict):
            if len(content) < 2:
                return "MINIMAL"
            # Check if all values are very short
            if all(isinstance(v, str) and len(str(v)) < 5 for v in content.values()):
                return "MINIMAL"
                
        if isinstance(content, list):
            if len(content) < 2:
                return "MINIMAL"
            if all(isinstance(item, str) and len(item) < 10 for item in content):
                return "MINIMAL"
        
        # Check content richness
        if isinstance(content, str):
            word_count = len(content.split())
            if word_count > 20:
                return "RICH"
            elif word_count > 5:
                return "GOOD"
            else:
                return "BASIC"
                
        if isinstance(content, dict) and len(content) > 3:
            return "GOOD"
            
        if isinstance(content, list) and len(content) > 3:
            return "GOOD"
            
        return "BASIC"

    def audit_cdl_file(self, file_path: Path) -> Dict[str, Any]:
        """Comprehensive audit of a single CDL file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            character_name = data.get('character', {}).get('identity', {}).get('name', 'Unknown')
            
            # Define all expected CDL sections
            sections_to_check = {
                # Core required sections
                'character.identity': 'Character Identity (name, age, occupation, etc.)',
                'character.identity.appearance': 'Physical Appearance Description',
                'character.identity.voice': 'Voice and Speaking Style',
                'character.personality': 'Core Personality Traits',
                'character.personality.big_five': 'Big Five Personality Profile',
                'character.personality.communication_style': 'Communication Preferences',
                'character.communication': 'Communication Patterns',
                'character.communication.typical_responses': 'Scenario-Based Responses',
                'character.communication.message_pattern_triggers': 'Message Pattern Triggers',
                'character.communication.conversation_flow_guidance': 'Conversation Flow Rules',
                
                # Enhanced sections
                'character.background': 'Character Background/History',
                'character.background.formative_experiences': 'Life-Shaping Events',
                'character.current_life': 'Current Life Situation',
                'character.relationships': 'Relationship Dynamics',
                'character.personality.communication_style.ai_identity_handling': 'AI Identity Responses',
                'character.personality.communication_style.ai_identity_handling.relationship_boundary_scenarios': 'Romantic Boundary Handling',
                
                # Specialized sections
                'character.identity.digital_communication': 'Digital/Emoji Communication',
                'character.identity.digital_communication.emoji_personality': 'Emoji Usage Patterns',
                'character.skills_and_expertise': 'Professional Skills',
                'character.interests_and_hobbies': 'Personal Interests',
                'character.speech_patterns': 'Detailed Speech Patterns',
            }
            
            audit_result = {
                'character_name': character_name,
                'file_name': file_path.name,
                'sections': {},
                'summary': {
                    'total_sections': len(sections_to_check),
                    'present_sections': 0,
                    'missing_sections': 0,
                    'placeholder_sections': 0,
                    'well_customized_sections': 0
                }
            }
            
            # Check each section
            for section_path, description in sections_to_check.items():
                check_result = self.check_section_completeness(data, section_path)
                
                if check_result['exists']:
                    customization_level = self.analyze_customization_level(
                        check_result['content'], section_path
                    )
                    audit_result['sections'][section_path] = {
                        'description': description,
                        'status': 'PRESENT',
                        'customization': customization_level,
                        'content_preview': str(check_result['content'])[:100] + "..." if len(str(check_result['content'])) > 100 else str(check_result['content'])
                    }
                    audit_result['summary']['present_sections'] += 1
                    
                    if customization_level in ['RICH', 'GOOD']:
                        audit_result['summary']['well_customized_sections'] += 1
                    elif customization_level == 'PLACEHOLDER':
                        audit_result['summary']['placeholder_sections'] += 1
                        
                else:
                    audit_result['sections'][section_path] = {
                        'description': description,
                        'status': 'MISSING',
                        'reason': check_result['reason']
                    }
                    audit_result['summary']['missing_sections'] += 1
            
            return audit_result
            
        except Exception as e:
            return {
                'character_name': 'ERROR',
                'file_name': file_path.name,
                'error': str(e),
                'sections': {},
                'summary': {'error': True}
            }

    def print_detailed_audit(self, audit_result: Dict[str, Any]):
        """Print detailed audit results for a character."""
        print(f"\n📋 {audit_result['character_name']} ({audit_result['file_name']})")
        print("=" * 60)
        
        if 'error' in audit_result:
            print(f"❌ ERROR: {audit_result['error']}")
            return
            
        summary = audit_result['summary']
        print(f"📊 Summary: {summary['present_sections']}/{summary['total_sections']} sections present")
        print(f"✅ Well Customized: {summary['well_customized_sections']}")
        print(f"⚠️  Placeholders: {summary['placeholder_sections']}")
        print(f"❌ Missing: {summary['missing_sections']}")
        
        # Group sections by status
        missing_sections = []
        placeholder_sections = []
        good_sections = []
        
        for section_path, section_data in audit_result['sections'].items():
            if section_data['status'] == 'MISSING':
                missing_sections.append(section_data['description'])
            elif section_data.get('customization') == 'PLACEHOLDER':
                placeholder_sections.append(section_data['description'])
            elif section_data.get('customization') in ['RICH', 'GOOD']:
                good_sections.append(section_data['description'])
        
        if missing_sections:
            print(f"\n❌ Missing Sections ({len(missing_sections)}):")
            for section in missing_sections:
                print(f"   • {section}")
                
        if placeholder_sections:
            print(f"\n⚠️  Placeholder Content ({len(placeholder_sections)}):")
            for section in placeholder_sections:
                print(f"   • {section}")
                
        print(f"\n✅ Well Customized ({len(good_sections)}):")
        for section in good_sections:
            print(f"   • {section}")

    def audit_all_cdl_files(self):
        """Audit all CDL files and provide comprehensive report."""
        print("🔍 Comprehensive CDL Content Audit")
        print("=" * 80)
        print("Checking completeness and customization levels of all CDL sections...")
        
        characters_dir = Path("characters/examples")
        if not characters_dir.exists():
            print("❌ Characters directory not found!")
            return
            
        cdl_files = list(characters_dir.glob("*.json"))
        if not cdl_files:
            print("❌ No CDL files found!")
            return
            
        print(f"📁 Found {len(cdl_files)} CDL files to audit")
        
        # Audit each file
        all_audits = []
        for cdl_file in sorted(cdl_files):
            audit_result = self.audit_cdl_file(cdl_file)
            all_audits.append(audit_result)
            self.print_detailed_audit(audit_result)
        
        # Overall summary
        self.print_overall_summary(all_audits)
    
    def print_overall_summary(self, all_audits: List[Dict[str, Any]]):
        """Print overall audit summary across all characters."""
        print(f"\n🎯 OVERALL CDL AUDIT SUMMARY")
        print("=" * 80)
        
        total_characters = len(all_audits)
        total_sections = sum(audit.get('summary', {}).get('total_sections', 0) for audit in all_audits)
        total_present = sum(audit.get('summary', {}).get('present_sections', 0) for audit in all_audits)
        total_missing = sum(audit.get('summary', {}).get('missing_sections', 0) for audit in all_audits)
        total_placeholders = sum(audit.get('summary', {}).get('placeholder_sections', 0) for audit in all_audits)
        total_well_customized = sum(audit.get('summary', {}).get('well_customized_sections', 0) for audit in all_audits)
        
        print(f"📊 Characters Analyzed: {total_characters}")
        print(f"📋 Total Sections: {total_sections}")
        print(f"✅ Present: {total_present} ({(total_present/total_sections)*100:.1f}%)")
        print(f"❌ Missing: {total_missing} ({(total_missing/total_sections)*100:.1f}%)")
        print(f"⚠️  Placeholders: {total_placeholders} ({(total_placeholders/total_sections)*100:.1f}%)")
        print(f"🌟 Well Customized: {total_well_customized} ({(total_well_customized/total_sections)*100:.1f}%)")
        
        # Character rankings by completeness
        print(f"\n🏆 Character Completeness Rankings:")
        character_scores = []
        for audit in all_audits:
            if 'error' not in audit:
                summary = audit['summary']
                completion_score = summary['well_customized_sections'] + (summary['present_sections'] - summary['placeholder_sections']) * 0.5
                character_scores.append((audit['character_name'], completion_score, summary['present_sections'], summary['total_sections']))
        
        character_scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, score, present, total) in enumerate(character_scores, 1):
            print(f"{i:2}. {name:20} - {present}/{total} sections ({score:.1f} quality score)")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if total_missing > total_sections * 0.1:  # More than 10% missing
            print("   • High number of missing sections - consider adding missing CDL sections")
        if total_placeholders > total_sections * 0.05:  # More than 5% placeholders
            print("   • Replace placeholder content with character-specific details")
        if total_well_customized < total_sections * 0.7:  # Less than 70% well customized
            print("   • Enhance customization depth in existing sections")
        else:
            print("   • Excellent CDL customization level across all characters! 🎉")

async def main():
    """Run comprehensive CDL content audit."""
    auditor = CDLContentAuditor()
    auditor.audit_all_cdl_files()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())