#!/usr/bin/env python3
"""
CDL Content Auditor - Specialized auditing for CDL content completeness and quality.

Provides detailed analysis of CDL content structure, customization levels, and recommendations.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Union, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ContentSection:
    """Represents analysis of a CDL content section."""
    path: str
    description: str
    exists: bool
    content_length: int = 0
    customization_level: str = "MISSING"
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ContentAuditResult:
    """Complete content audit result for a CDL file."""
    file_path: str
    character_name: str
    sections: List[ContentSection] = field(default_factory=list)
    completeness_score: float = 0.0
    quality_score: float = 0.0
    overall_rating: str = "UNKNOWN"
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def sections_by_category(self) -> Dict[str, List[ContentSection]]:
        """Group sections by top-level category."""
        categories = defaultdict(list)
        for section in self.sections:
            category = section.path.split('.')[1] if '.' in section.path else 'other'
            categories[category].append(section)
        return dict(categories)
    
    @property
    def summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        total = len(self.sections)
        present = sum(1 for s in self.sections if s.exists)
        good_quality = sum(1 for s in self.sections if s.customization_level == "GOOD")
        placeholders = sum(1 for s in self.sections if s.customization_level == "PLACEHOLDER")
        
        return {
            'total_sections': total,
            'present_sections': present,
            'missing_sections': total - present,
            'good_quality': good_quality,
            'basic_quality': sum(1 for s in self.sections if s.customization_level == "BASIC"),
            'placeholder_sections': placeholders,
            'completeness_percent': (present / total * 100) if total > 0 else 0,
            'quality_percent': (good_quality / total * 100) if total > 0 else 0
        }


class CDLContentAuditor:
    """
    Specialized CDL content auditor focusing on completeness and quality analysis.
    
    Usage:
        auditor = CDLContentAuditor()
        result = auditor.audit_file('path/to/character.json')
        auditor.print_detailed_report(result)
    """
    
    def __init__(self):
        """Initialize the content auditor."""
        # Comprehensive section definitions with priorities
        self.required_sections = {
            # Core Identity (HIGH PRIORITY)
            'character.identity': {
                'description': 'Character Identity (name, age, occupation, etc.)',
                'priority': 'HIGH',
                'quality_indicators': ['name', 'age', 'occupation', 'location']
            },
            'character.identity.appearance': {
                'description': 'Physical Appearance Description',
                'priority': 'HIGH',
                'quality_indicators': ['height', 'build', 'hair', 'eyes', 'distinctive']
            },
            'character.identity.voice': {
                'description': 'Voice and Speaking Style',
                'priority': 'HIGH',
                'quality_indicators': ['tone', 'pace', 'accent', 'vocabulary']
            },
            
            # Personality Core (HIGH PRIORITY)
            'character.personality': {
                'description': 'Core Personality Traits',
                'priority': 'HIGH',
                'quality_indicators': ['traits', 'motivations', 'values', 'fears']
            },
            'character.personality.big_five': {
                'description': 'Big Five Personality Profile',
                'priority': 'MEDIUM',
                'quality_indicators': ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            },
            'character.personality.communication_style': {
                'description': 'Communication Preferences',
                'priority': 'HIGH',
                'quality_indicators': ['formality', 'directness', 'emotional_expression']
            },
            
            # Communication System (CRITICAL)
            'character.communication': {
                'description': 'Communication Patterns',
                'priority': 'CRITICAL',
                'quality_indicators': ['typical_responses', 'message_pattern_triggers', 'conversation_flow_guidance']
            },
            'character.communication.typical_responses': {
                'description': 'Scenario-Based Responses',
                'priority': 'CRITICAL',
                'quality_indicators': ['greeting', 'farewell', 'confusion', 'excitement']
            },
            'character.communication.message_pattern_triggers': {
                'description': 'Message Pattern Triggers',
                'priority': 'CRITICAL',
                'quality_indicators': ['patterns', 'keywords', 'scenarios']
            },
            'character.communication.conversation_flow_guidance': {
                'description': 'Conversation Flow Rules',
                'priority': 'CRITICAL',
                'quality_indicators': ['flow_rules', 'response_strategies', 'engagement_patterns']
            },
            
            # Background and Context (MEDIUM PRIORITY)
            'character.background': {
                'description': 'Character Background/History',
                'priority': 'MEDIUM',
                'quality_indicators': ['origin', 'education', 'career_path', 'major_events']
            },
            'character.background.formative_experiences': {
                'description': 'Life-Shaping Events',
                'priority': 'MEDIUM',
                'quality_indicators': ['childhood', 'adolescence', 'career_defining', 'relationships']
            },
            'character.current_life': {
                'description': 'Current Life Situation',
                'priority': 'MEDIUM',
                'quality_indicators': ['daily_routine', 'current_projects', 'living_situation', 'goals']
            },
            'character.relationships': {
                'description': 'Relationship Dynamics',
                'priority': 'HIGH',
                'quality_indicators': ['family', 'friends', 'colleagues', 'romantic']
            },
            
            # AI-Specific Communication (HIGH PRIORITY)
            'character.personality.communication_style.ai_identity_handling': {
                'description': 'AI Identity Responses',
                'priority': 'HIGH',
                'quality_indicators': ['ai_acknowledgment', 'roleplay_boundaries', 'identity_consistency']
            },
            'character.personality.communication_style.ai_identity_handling.relationship_boundary_scenarios': {
                'description': 'Romantic Boundary Handling',
                'priority': 'HIGH',
                'quality_indicators': ['romantic_deflection', 'boundary_setting', 'appropriate_responses']
            },
            
            # Digital Communication (MEDIUM PRIORITY)
            'character.identity.digital_communication': {
                'description': 'Digital/Emoji Communication',
                'priority': 'MEDIUM',
                'quality_indicators': ['emoji_usage', 'digital_style', 'platform_adaptation']
            },
            'character.identity.digital_communication.emoji_personality': {
                'description': 'Emoji Usage Patterns',
                'priority': 'MEDIUM',
                'quality_indicators': ['favorite_emojis', 'emotion_mapping', 'frequency_patterns']
            },
            
            # Skills and Interests (LOW PRIORITY)
            'character.skills_and_expertise': {
                'description': 'Professional Skills',
                'priority': 'LOW',
                'quality_indicators': ['technical_skills', 'soft_skills', 'certifications', 'experience_level']
            },
            'character.interests_and_hobbies': {
                'description': 'Personal Interests',
                'priority': 'LOW',
                'quality_indicators': ['hobbies', 'entertainment', 'learning_interests', 'passion_projects']
            },
            'character.speech_patterns': {
                'description': 'Detailed Speech Patterns',
                'priority': 'MEDIUM',
                'quality_indicators': ['phrases', 'expressions', 'speech_quirks', 'language_style']
            }
        }
        
        # Quality assessment criteria
        self.placeholder_patterns = [
            'placeholder', 'todo', 'tbd', 'fill in', 'example',
            'lorem ipsum', 'sample', 'default', 'template',
            'change this', 'update this', 'add details'
        ]
        
        self.good_quality_indicators = [
            ('substantial_content', lambda x: len(str(x)) > 100),
            ('detailed_dict', lambda x: isinstance(x, dict) and len(x) > 3),
            ('detailed_list', lambda x: isinstance(x, list) and len(x) > 3),
            ('specific_examples', lambda x: 'specific' in str(x).lower() or 'unique' in str(x).lower()),
            ('numeric_details', lambda x: any(char.isdigit() for char in str(x))),
            ('proper_names', lambda x: any(word[0].isupper() for word in str(x).split() if len(word) > 2))
        ]
    
    def audit_file(self, file_path: Union[str, Path]) -> ContentAuditResult:
        """
        Perform comprehensive content audit of a CDL file.
        
        Args:
            file_path: Path to the CDL JSON file
            
        Returns:
            ContentAuditResult with detailed analysis
        """
        file_path = Path(file_path)
        
        # Initialize result
        result = ContentAuditResult(
            file_path=str(file_path),
            character_name="Unknown"
        )
        
        # Load and parse the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
                
            # Extract character name
            result.character_name = (cdl_data.get('character', {})
                                   .get('identity', {})
                                   .get('name', file_path.stem))
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            result.recommendations.append(f"Cannot parse file: {e}")
            return result
        
        # Analyze each section
        sections = []
        for section_path, section_info in self.required_sections.items():
            section_analysis = self._analyze_section(
                cdl_data, section_path, section_info
            )
            sections.append(section_analysis)
        
        result.sections = sections
        
        # Calculate scores
        result.completeness_score, result.quality_score = self._calculate_scores(sections)
        result.overall_rating = self._determine_overall_rating(result.completeness_score, result.quality_score)
        result.recommendations = self._generate_recommendations(result)
        
        return result
    
    def _analyze_section(self, cdl_data: Dict, section_path: str, 
                        section_info: Dict) -> ContentSection:
        """Analyze a specific CDL section for completeness and quality."""
        section = ContentSection(
            path=section_path,
            description=section_info['description'],
            exists=False  # Will be updated below
        )
        
        # Check if section exists
        section_data = self._get_nested_value(cdl_data, section_path)
        
        if section_data is None:
            section.exists = False
            section.customization_level = "MISSING"
            section.issues.append("Section is missing")
            section.suggestions.append(f"Add {section_info['description']} to improve character depth")
            return section
        
        section.exists = True
        section.content_length = len(str(section_data))
        
        # Analyze content quality
        section.customization_level = self._assess_customization_level(
            section_data, section_info.get('quality_indicators', [])
        )
        
        # Generate specific issues and suggestions
        self._add_section_specific_feedback(section, section_data, section_info)
        
        return section
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split('.')
        current = data
        
        try:
            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    return None
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None
    
    def _assess_customization_level(self, content: Any, quality_indicators: List[str]) -> str:
        """Assess the customization level of content."""
        if not content:
            return "MISSING"
        
        content_str = str(content).lower()
        
        # Check for placeholder patterns
        for pattern in self.placeholder_patterns:
            if pattern in content_str:
                return "PLACEHOLDER"
        
        # Count quality indicators met
        quality_score = 0
        
        # Check built-in quality indicators
        for name, check_func in self.good_quality_indicators:
            try:
                if check_func(content):
                    quality_score += 1
            except Exception:
                continue
        
        # Check section-specific quality indicators
        if isinstance(content, dict):
            for indicator in quality_indicators:
                if indicator.lower() in content_str:
                    quality_score += 1
        
        # Determine level based on quality score
        if quality_score >= 3:
            return "GOOD"
        elif quality_score >= 1:
            return "BASIC"
        else:
            return "MINIMAL"
    
    def _add_section_specific_feedback(self, section: ContentSection, 
                                     content: Any, section_info: Dict):
        """Add specific feedback based on section type and content."""
        path_parts = section.path.split('.')
        
        # Communication-specific feedback
        if 'communication' in path_parts:
            if 'message_pattern_triggers' in path_parts:
                if not isinstance(content, dict) or not content:
                    section.issues.append("Message pattern triggers should be a non-empty dictionary")
                    section.suggestions.append("Add keyword-based pattern triggers for conversation flow")
                elif len(content) < 3:
                    section.suggestions.append("Consider adding more pattern triggers for better conversation detection")
            
            elif 'conversation_flow_guidance' in path_parts:
                if not isinstance(content, dict) or not content:
                    section.issues.append("Conversation flow guidance should be a non-empty dictionary")
                    section.suggestions.append("Add guidance rules for different conversation scenarios")
        
        # Identity-specific feedback
        elif 'identity' in path_parts:
            if path_parts[-1] == 'identity' and isinstance(content, dict):
                required_fields = ['name', 'age', 'occupation']
                missing_fields = [field for field in required_fields if field not in content]
                if missing_fields:
                    section.issues.append(f"Missing basic identity fields: {', '.join(missing_fields)}")
                    section.suggestions.append("Add core identity information for character consistency")
        
        # Personality-specific feedback
        elif 'personality' in path_parts:
            if 'big_five' in path_parts and isinstance(content, dict):
                big_five_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
                missing_traits = [trait for trait in big_five_traits if trait not in content]
                if missing_traits:
                    section.suggestions.append(f"Consider adding Big Five traits: {', '.join(missing_traits)}")
            
            elif 'ai_identity_handling' in path_parts:
                if not content or (isinstance(content, dict) and len(content) < 2):
                    section.issues.append("AI identity handling needs more detailed guidance")
                    section.suggestions.append("Add specific strategies for maintaining character consistency as AI")
        
        # Background-specific feedback
        elif 'background' in path_parts or 'current_life' in path_parts:
            if isinstance(content, str) and len(content) < 50:
                section.suggestions.append("Expand background details for richer character development")
            elif isinstance(content, dict) and len(content) < 2:
                section.suggestions.append("Add more background elements for character depth")
        
        # General content length feedback
        content_length = len(str(content))
        if content_length < 20:
            section.suggestions.append("Consider expanding this section with more specific details")
        elif content_length > 1000:
            section.suggestions.append("This section is quite detailed - consider organizing into subsections")
    
    def _calculate_scores(self, sections: List[ContentSection]) -> Tuple[float, float]:
        """Calculate completeness and quality scores."""
        if not sections:
            return 0.0, 0.0
        
        # Completeness score (weighted by priority)
        total_weight = 0
        completeness_weighted = 0
        
        # Quality score (weighted by priority)
        quality_weighted = 0
        
        priority_weights = {
            'CRITICAL': 4.0,
            'HIGH': 3.0,
            'MEDIUM': 2.0,
            'LOW': 1.0
        }
        
        for section in sections:
            section_info = self.required_sections.get(section.path, {})
            weight = priority_weights.get(section_info.get('priority', 'MEDIUM'), 2.0)
            total_weight += weight
            
            if section.exists:
                completeness_weighted += weight
                
                # Quality contribution
                quality_multiplier = {
                    'GOOD': 1.0,
                    'BASIC': 0.7,
                    'MINIMAL': 0.4,
                    'PLACEHOLDER': 0.2,
                    'MISSING': 0.0
                }.get(section.customization_level, 0.0)
                
                quality_weighted += weight * quality_multiplier
        
        completeness_score = (completeness_weighted / total_weight * 100) if total_weight > 0 else 0
        quality_score = (quality_weighted / total_weight * 100) if total_weight > 0 else 0
        
        return completeness_score, quality_score
    
    def _determine_overall_rating(self, completeness: float, quality: float) -> str:
        """Determine overall rating based on completeness and quality scores."""
        avg_score = (completeness + quality) / 2
        
        if avg_score >= 90:
            return "EXCELLENT"
        elif avg_score >= 80:
            return "VERY_GOOD"
        elif avg_score >= 70:
            return "GOOD"
        elif avg_score >= 60:
            return "ADEQUATE"
        elif avg_score >= 40:
            return "NEEDS_IMPROVEMENT"
        else:
            return "POOR"
    
    def _generate_recommendations(self, result: ContentAuditResult) -> List[str]:
        """Generate overall recommendations for improvement."""
        recommendations = []
        stats = result.summary_stats
        
        # Priority-based recommendations
        if stats['completeness_percent'] < 80:
            recommendations.append("🎯 Focus on adding missing sections to improve completeness")
        
        if stats['placeholder_sections'] > 0:
            recommendations.append("📝 Replace placeholder content with character-specific details")
        
        if stats['quality_percent'] < 70:
            recommendations.append("✨ Enhance existing sections with more detailed, specific content")
        
        # Category-specific recommendations
        categories = result.sections_by_category
        
        if 'communication' in categories:
            comm_sections = categories['communication']
            missing_comm = [s for s in comm_sections if not s.exists]
            if missing_comm:
                recommendations.append("💬 Complete communication patterns - critical for conversation flow")
        
        if 'identity' in categories:
            identity_sections = categories['identity']
            basic_identity = [s for s in identity_sections if s.customization_level in ['BASIC', 'MINIMAL']]
            if basic_identity:
                recommendations.append("👤 Strengthen character identity with more specific details")
        
        # Overall improvement suggestions
        if result.overall_rating in ['POOR', 'NEEDS_IMPROVEMENT']:
            recommendations.append("🚀 Consider comprehensive character development session")
        elif result.overall_rating == 'ADEQUATE':
            recommendations.append("📈 Add depth to existing sections for richer character portrayal")
        elif result.overall_rating in ['GOOD', 'VERY_GOOD']:
            recommendations.append("🎨 Fine-tune details and consider advanced personality features")
        
        return recommendations
    
    def print_detailed_report(self, result: ContentAuditResult):
        """Print a comprehensive detailed report."""
        print(f"\n🔍 CDL CONTENT AUDIT: {result.character_name}")
        print("=" * 80)
        
        stats = result.summary_stats
        
        # Overall summary
        print(f"📊 Overall Rating: {result.overall_rating}")
        print(f"📊 Completeness: {result.completeness_score:.1f}% ({stats['present_sections']}/{stats['total_sections']} sections)")
        print(f"📊 Quality Score: {result.quality_score:.1f}%")
        
        # Section breakdown by category
        categories = result.sections_by_category
        
        for category, sections in categories.items():
            print(f"\n📂 {category.upper()} SECTIONS:")
            
            for section in sections:
                status_emoji = "✅" if section.exists else "❌"
                quality_emoji = {
                    'GOOD': '🟢',
                    'BASIC': '🟡', 
                    'MINIMAL': '🟠',
                    'PLACEHOLDER': '🔴',
                    'MISSING': '⚫'
                }.get(section.customization_level, '⚫')
                
                print(f"   {status_emoji} {quality_emoji} {section.description}")
                
                if section.issues:
                    for issue in section.issues:
                        print(f"      ⚠️  {issue}")
                
                if section.suggestions:
                    for suggestion in section.suggestions[:2]:  # Limit to top 2 suggestions
                        print(f"      💡 {suggestion}")
        
        # Recommendations
        if result.recommendations:
            print(f"\n🎯 IMPROVEMENT RECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"   {i}. {rec}")
        
        print()
    
    def print_summary_report(self, results: List[ContentAuditResult]):
        """Print a summary report for multiple audits."""
        if not results:
            print("No audit results to report.")
            return
        
        print(f"\n📊 CDL CONTENT AUDIT SUMMARY")
        print("=" * 80)
        
        # Overall statistics
        total_chars = len(results)
        avg_completeness = sum(r.completeness_score for r in results) / total_chars
        avg_quality = sum(r.quality_score for r in results) / total_chars
        
        rating_counts: defaultdict[str, int] = defaultdict(int)
        for result in results:
            rating_counts[result.overall_rating] += 1
        
        print(f"📊 Characters Analyzed: {total_chars}")
        print(f"📊 Average Completeness: {avg_completeness:.1f}%")
        print(f"📊 Average Quality: {avg_quality:.1f}%")
        
        # Rating distribution
        print(f"\n🏆 Rating Distribution:")
        rating_order = ['EXCELLENT', 'VERY_GOOD', 'GOOD', 'ADEQUATE', 'NEEDS_IMPROVEMENT', 'POOR']
        for rating in rating_order:
            count = rating_counts[rating]
            if count > 0:
                percentage = (count / total_chars) * 100
                print(f"   {rating:<20}: {count:>2} ({percentage:4.1f}%)")
        
        # Top and bottom performers
        sorted_results = sorted(results, key=lambda r: (r.completeness_score + r.quality_score) / 2, reverse=True)
        
        print(f"\n🥇 Top Performers:")
        for i, result in enumerate(sorted_results[:3], 1):
            avg_score = (result.completeness_score + result.quality_score) / 2
            print(f"   {i}. {result.character_name:<20} - {avg_score:.1f}% ({result.overall_rating})")
        
        if len(results) > 3:
            print(f"\n⚠️  Needs Attention:")
            for i, result in enumerate(sorted_results[-3:], 1):
                avg_score = (result.completeness_score + result.quality_score) / 2
                print(f"   {i}. {result.character_name:<20} - {avg_score:.1f}% ({result.overall_rating})")
        
        # Common issues
        all_issues = []
        for result in results:
            for section in result.sections:
                all_issues.extend(section.issues)
        
        if all_issues:
            issue_counts: defaultdict[str, int] = defaultdict(int)
            for issue in all_issues:
                issue_counts[issue] += 1
            
            print(f"\n🔍 Most Common Issues:")
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   • {issue} ({count} characters)")