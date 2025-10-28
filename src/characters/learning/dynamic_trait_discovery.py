"""
Dynamic Trait Discovery System - PHASE 3A Implementation
Enables characters to understand their own motivations, preferences, and behavioral patterns without hardcoded logic.

This module implements the Dynamic Trait Discovery system from the Memory Intelligence Convergence Roadmap PHASE 3A.
It provides characters with self-awareness capabilities to understand their own personality patterns, motivations,
and behavioral tendencies through intelligent analysis of their trait relationships.

Features:
- Dynamic motivation analysis from character traits
- Behavioral pattern discovery from trait combinations
- Preference inference from interests and values
- Self-awareness queries for character responses
- Adaptive trait learning from conversation patterns

Integration: Works with Character Self-Knowledge Extractor and Graph Knowledge Builder for comprehensive self-awareness.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TraitMotivation:
    """Represents a discovered motivation from character traits."""
    
    def __init__(self, motivation_type: str, description: str, source_traits: List[str], 
                 confidence: float, context: Optional[str] = None):
        self.motivation_type = motivation_type
        self.description = description
        self.source_traits = source_traits
        self.confidence = confidence  # 0.0 to 1.0
        self.context = context
        self.discovered_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analysis."""
        return {
            'motivation_type': self.motivation_type,
            'description': self.description,
            'source_traits': self.source_traits,
            'confidence': self.confidence,
            'context': self.context,
            'discovered_at': self.discovered_at.isoformat()
        }

class BehavioralPattern:
    """Represents a discovered behavioral pattern."""
    
    def __init__(self, pattern_name: str, description: str, triggers: List[str],
                 typical_responses: List[str], confidence: float):
        self.pattern_name = pattern_name
        self.description = description
        self.triggers = triggers  # What activates this pattern
        self.typical_responses = typical_responses  # How character typically responds
        self.confidence = confidence
        self.discovered_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analysis."""
        return {
            'pattern_name': self.pattern_name,
            'description': self.description,
            'triggers': self.triggers,
            'typical_responses': self.typical_responses,
            'confidence': self.confidence,
            'discovered_at': self.discovered_at.isoformat()
        }

class DynamicTraitDiscovery:
    """
    Dynamic system for characters to discover and understand their own traits and motivations.
    
    This class enables characters to develop self-awareness by analyzing their trait relationships,
    discovering motivations, and understanding behavioral patterns without hardcoded logic.
    """
    
    def __init__(self, character_self_knowledge_extractor, character_graph_knowledge_builder):
        """Initialize with character knowledge systems."""
        self.knowledge_extractor = character_self_knowledge_extractor
        self.graph_builder = character_graph_knowledge_builder
        self.discovery_cache = {}  # Cache for frequent discoveries
        
        # Discovery patterns for different types of self-knowledge
        self.motivation_patterns = {
            'helping_others': ['empathy', 'caring', 'support', 'assistance', 'guidance'],
            'learning_growth': ['knowledge', 'learning', 'study', 'research', 'curiosity'],
            'creative_expression': ['creativity', 'art', 'innovation', 'imagination', 'design'],
            'connection_building': ['relationship', 'friendship', 'community', 'social', 'bonding'],
            'problem_solving': ['analysis', 'solution', 'fix', 'resolve', 'tackle'],
            'sharing_knowledge': ['teach', 'educate', 'explain', 'share', 'inform']
        }
        
        self.behavioral_triggers = {
            'educational_response': ['question', 'confusion', 'learning', 'explain'],
            'supportive_response': ['stress', 'sadness', 'worry', 'concern', 'difficulty'],
            'enthusiastic_response': ['interest', 'excitement', 'passion', 'love', 'enjoy'],
            'analytical_response': ['problem', 'complex', 'analysis', 'data', 'research'],
            'creative_response': ['idea', 'innovative', 'creative', 'artistic', 'imagine']
        }
    
    async def discover_character_motivations(self, character_name: str) -> List[TraitMotivation]:
        """
        Discover core motivations that drive the character's behavior.
        
        Args:
            character_name: Name of the character to analyze
            
        Returns:
            List of discovered motivations with confidence scores
        """
        try:
            logger.info("🔍 Discovering motivations for character %s", character_name)
            
            # Extract character knowledge
            character_knowledge = await self.knowledge_extractor.extract_character_self_knowledge(character_name)
            if not character_knowledge:
                logger.warning("No character knowledge available for motivation discovery: %s", character_name)
                return []
            
            # Get trait relationships
            trait_relationships = await self.graph_builder.query_character_relationships(character_name)
            
            discovered_motivations = []
            
            # Analyze values for motivations
            values_motivations = await self._analyze_values_for_motivations(character_knowledge, trait_relationships)
            discovered_motivations.extend(values_motivations)
            
            # Analyze interests for motivations
            interest_motivations = await self._analyze_interests_for_motivations(character_knowledge, trait_relationships)
            discovered_motivations.extend(interest_motivations)
            
            # Analyze communication style for motivations
            comm_motivations = await self._analyze_communication_for_motivations(character_knowledge, trait_relationships)
            discovered_motivations.extend(comm_motivations)
            
            # Sort by confidence and remove duplicates
            discovered_motivations = self._deduplicate_motivations(discovered_motivations)
            discovered_motivations.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info("✅ Discovered %d motivations for %s", len(discovered_motivations), character_name)
            
            return discovered_motivations
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.error("Failed to discover character motivations for %s: %s", character_name, e)
            return []
    
    async def discover_behavioral_patterns(self, character_name: str) -> List[BehavioralPattern]:
        """
        Discover behavioral patterns from character traits and relationships.
        
        Args:
            character_name: Name of the character to analyze
            
        Returns:
            List of discovered behavioral patterns
        """
        try:
            logger.info("🔍 Discovering behavioral patterns for character %s", character_name)
            
            # Extract character knowledge
            character_knowledge = await self.knowledge_extractor.extract_character_self_knowledge(character_name)
            if not character_knowledge:
                return []
            
            # Get trait relationships
            trait_relationships = await self.graph_builder.query_character_relationships(character_name)
            
            discovered_patterns = []
            
            # Analyze trait combinations for behavioral patterns
            for pattern_name, triggers in self.behavioral_triggers.items():
                pattern = await self._discover_behavioral_pattern(
                    character_name, pattern_name, triggers, character_knowledge, trait_relationships
                )
                if pattern:
                    discovered_patterns.append(pattern)
            
            # Discover custom patterns from trait relationships
            custom_patterns = await self._discover_custom_behavioral_patterns(
                character_knowledge, trait_relationships
            )
            discovered_patterns.extend(custom_patterns)
            
            # Sort by confidence
            discovered_patterns.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info("✅ Discovered %d behavioral patterns for %s", len(discovered_patterns), character_name)
            
            return discovered_patterns
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.error("Failed to discover behavioral patterns for %s: %s", character_name, e)
            return []
    
    async def get_self_awareness_insights(self, character_name: str, query_type: str) -> Dict[str, Any]:
        """
        Get self-awareness insights for character responses.
        
        Args:
            character_name: Name of the character
            query_type: Type of self-awareness query ('motivation', 'behavior', 'preferences', 'values')
            
        Returns:
            Dictionary containing relevant self-awareness insights
        """
        try:
            cache_key = f"{character_name}:{query_type}"
            
            # Check cache first (expire after 1 hour)
            if cache_key in self.discovery_cache:
                cached_result = self.discovery_cache[cache_key]
                if datetime.now() - cached_result['cached_at'] < timedelta(hours=1):
                    return cached_result['insights']
            
            insights = {}
            
            if query_type == 'motivation':
                motivations = await self.discover_character_motivations(character_name)
                insights = {
                    'type': 'motivation',
                    'primary_motivations': [m.to_dict() for m in motivations[:3]],  # Top 3
                    'total_discovered': len(motivations),
                    'high_confidence_count': len([m for m in motivations if m.confidence > 0.8])
                }
            
            elif query_type == 'behavior':
                patterns = await self.discover_behavioral_patterns(character_name)
                insights = {
                    'type': 'behavior',
                    'behavioral_patterns': [p.to_dict() for p in patterns[:5]],  # Top 5
                    'total_patterns': len(patterns),
                    'dominant_patterns': [p.pattern_name for p in patterns if p.confidence > 0.7]
                }
            
            elif query_type == 'preferences':
                preferences = await self._discover_preferences(character_name)
                insights = {
                    'type': 'preferences',
                    'conversation_preferences': preferences.get('conversation', []),
                    'topic_preferences': preferences.get('topics', []),
                    'interaction_preferences': preferences.get('interaction', [])
                }
            
            elif query_type == 'values':
                value_analysis = await self._analyze_value_system(character_name)
                insights = {
                    'type': 'values',
                    'core_values': value_analysis.get('core_values', []),
                    'value_conflicts': value_analysis.get('conflicts', []),
                    'value_expressions': value_analysis.get('expressions', [])
                }
            
            # Cache result
            self.discovery_cache[cache_key] = {
                'insights': insights,
                'cached_at': datetime.now()
            }
            
            return insights
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.error("Failed to get self-awareness insights for %s: %s", character_name, e)
            return {}
    
    async def _analyze_values_for_motivations(self, character_knowledge: Dict, trait_relationships: List) -> List[TraitMotivation]:
        """Analyze character values to discover motivations."""
        motivations = []
        
        try:
            values = character_knowledge.get('values', {})
            
            for value_name, value_data in values.items():
                value_description = value_data.get('description', '').lower()
                
                # Match value description against motivation patterns
                for motivation_type, keywords in self.motivation_patterns.items():
                    matches = sum(1 for keyword in keywords if keyword in value_description)
                    if matches > 0:
                        confidence = min(0.9, matches / len(keywords) + 0.3)
                        
                        # Find supporting trait relationships
                        supporting_traits = [rel['target_trait'] for rel in trait_relationships 
                                           if rel['source_trait'] == f"value:{value_name}"]
                        
                        motivation = TraitMotivation(
                            motivation_type=motivation_type,
                            description=f"Motivated by {motivation_type} due to value: {value_name}",
                            source_traits=[f"value:{value_name}"] + supporting_traits[:2],
                            confidence=confidence,
                            context=f"Inferred from value '{value_name}': {value_data.get('description', '')}"
                        )
                        motivations.append(motivation)
            
        except (KeyError, TypeError) as e:
            logger.warning("Error analyzing values for motivations: %s", e)
        
        return motivations
    
    async def _analyze_interests_for_motivations(self, character_knowledge: Dict, _trait_relationships: List) -> List[TraitMotivation]:
        """Analyze character interests to discover motivations."""
        motivations = []
        
        try:
            interests = character_knowledge.get('interests', {})
            
            for interest_name, interest_data in interests.items():
                interest_description = interest_data.get('description', '').lower()
                
                # Match interest against motivation patterns
                for motivation_type, keywords in self.motivation_patterns.items():
                    matches = sum(1 for keyword in keywords if keyword in interest_description)
                    if matches > 0:
                        confidence = min(0.85, matches / len(keywords) + 0.4)
                        
                        motivation = TraitMotivation(
                            motivation_type=motivation_type,
                            description=f"Motivated by {motivation_type} through interest in {interest_name}",
                            source_traits=[f"interest:{interest_name}"],
                            confidence=confidence,
                            context=f"Inferred from interest '{interest_name}': {interest_description}"
                        )
                        motivations.append(motivation)
            
        except (KeyError, TypeError) as e:
            logger.warning("Error analyzing interests for motivations: %s", e)
        
        return motivations
    
    async def _analyze_communication_for_motivations(self, character_knowledge: Dict, _trait_relationships: List) -> List[TraitMotivation]:
        """Analyze communication style for underlying motivations."""
        motivations = []
        
        try:
            comm_style = character_knowledge.get('communication_style', {})
            
            # Analyze tone for motivations
            tone = comm_style.get('tone', {})
            for tone_name, tone_data in tone.items():
                tone_description = tone_data.get('description', '').lower()
                
                if 'supportive' in tone_description or 'caring' in tone_description:
                    motivation = TraitMotivation(
                        motivation_type='helping_others',
                        description="Motivated by helping others through supportive communication",
                        source_traits=[f"communication:tone:{tone_name}"],
                        confidence=0.7,
                        context=f"Inferred from supportive communication tone: {tone_description}"
                    )
                    motivations.append(motivation)
                
                if 'enthusiastic' in tone_description or 'passionate' in tone_description:
                    motivation = TraitMotivation(
                        motivation_type='sharing_knowledge',
                        description="Motivated by sharing knowledge through enthusiastic communication",
                        source_traits=[f"communication:tone:{tone_name}"],
                        confidence=0.6,
                        context=f"Inferred from enthusiastic communication: {tone_description}"
                    )
                    motivations.append(motivation)
            
        except (KeyError, TypeError) as e:
            logger.warning("Error analyzing communication for motivations: %s", e)
        
        return motivations
    
    async def _discover_behavioral_pattern(self, _character_name: str, pattern_name: str, triggers: List[str],
                                         character_knowledge: Dict, _trait_relationships: List) -> Optional[BehavioralPattern]:
        """Discover a specific behavioral pattern from character traits."""
        try:
            # Look for triggers in character traits
            trait_matches = 0
            supporting_traits = []
            
            # Check values
            values = character_knowledge.get('values', {})
            for value_data in values.values():
                value_desc = value_data.get('description', '').lower()
                if any(trigger in value_desc for trigger in triggers):
                    trait_matches += 1
                    supporting_traits.append(f"value:{value_data.get('name', 'unknown')}")
            
            # Check interests  
            interests = character_knowledge.get('interests', {})
            for interest_data in interests.values():
                interest_desc = interest_data.get('description', '').lower()
                if any(trigger in interest_desc for trigger in triggers):
                    trait_matches += 1
                    supporting_traits.append(f"interest:{interest_data.get('name', 'unknown')}")
            
            # Check communication style
            comm_style = character_knowledge.get('communication_style', {})
            for style_section in comm_style.values():
                if isinstance(style_section, dict):
                    for style_data in style_section.values():
                        if isinstance(style_data, dict):
                            style_desc = style_data.get('description', '').lower()
                            if any(trigger in style_desc for trigger in triggers):
                                trait_matches += 1
                                supporting_traits.append(f"communication:{style_data.get('name', 'unknown')}")
            
            # If we found enough matches, create behavioral pattern
            if trait_matches >= 1:
                confidence = min(0.9, trait_matches * 0.3 + 0.4)
                
                # Generate typical responses based on pattern
                typical_responses = self._generate_typical_responses(pattern_name, character_knowledge)
                
                pattern = BehavioralPattern(
                    pattern_name=pattern_name,
                    description=f"Character tends to exhibit {pattern_name} when encountering {', '.join(triggers)}",
                    triggers=triggers,
                    typical_responses=typical_responses,
                    confidence=confidence
                )
                
                return pattern
            
            return None
            
        except (KeyError, TypeError) as e:
            logger.warning("Error discovering behavioral pattern %s: %s", pattern_name, e)
            return None
    
    async def _discover_custom_behavioral_patterns(self, _character_knowledge: Dict, trait_relationships: List) -> List[BehavioralPattern]:
        """Discover custom behavioral patterns from trait relationships."""
        patterns = []
        
        try:
            # Look for strong trait combinations that suggest behavioral patterns
            relationship_strength_threshold = 0.7
            
            strong_relationships = [rel for rel in trait_relationships if rel['strength'] >= relationship_strength_threshold]
            
            # Group by relationship type
            relationship_groups: dict[str, list[dict]] = {}
            for rel in strong_relationships:
                rel_type = rel['relationship_type']
                if rel_type not in relationship_groups:
                    relationship_groups[rel_type] = []
                relationship_groups[rel_type].append(rel)
            
            # Create patterns from relationship groups
            for rel_type, relationships in relationship_groups.items():
                if len(relationships) >= 2:  # Need multiple relationships to form a pattern
                    pattern_name = f"custom_{rel_type}_pattern"
                    description = f"Shows {rel_type} relationships between multiple traits"
                    
                    triggers = [rel['source_trait'].split(':')[-1] for rel in relationships]
                    typical_responses = [rel['target_trait'].split(':')[-1] for rel in relationships]
                    
                    confidence = sum(rel['strength'] for rel in relationships) / len(relationships)
                    
                    pattern = BehavioralPattern(
                        pattern_name=pattern_name,
                        description=description,
                        triggers=triggers,
                        typical_responses=typical_responses,
                        confidence=confidence
                    )
                    patterns.append(pattern)
            
        except (KeyError, TypeError) as e:
            logger.warning("Error discovering custom behavioral patterns: %s", e)
        
        return patterns
    
    def _generate_typical_responses(self, pattern_name: str, _character_knowledge: Dict) -> List[str]:
        """Generate typical responses based on pattern and character knowledge."""
        responses = []
        
        try:
            if pattern_name == 'educational_response':
                responses = ['Provide explanations', 'Share knowledge', 'Ask clarifying questions', 'Offer examples']
            elif pattern_name == 'supportive_response':
                responses = ['Offer encouragement', 'Show empathy', 'Provide comfort', 'Suggest solutions']
            elif pattern_name == 'enthusiastic_response':
                responses = ['Express excitement', 'Share related experiences', 'Ask follow-up questions', 'Encourage exploration']
            elif pattern_name == 'analytical_response':
                responses = ['Break down problems', 'Suggest methodical approaches', 'Provide data', 'Offer analysis']
            elif pattern_name == 'creative_response':
                responses = ['Suggest creative solutions', 'Share artistic perspectives', 'Encourage innovation', 'Provide inspiration']
            else:
                responses = ['Respond authentically', 'Stay true to character', 'Express personality', 'Engage meaningfully']
            
        except (KeyError, TypeError) as e:
            logger.warning("Error generating typical responses: %s", e)
        
        return responses
    
    def _deduplicate_motivations(self, motivations: List[TraitMotivation]) -> List[TraitMotivation]:
        """Remove duplicate motivations, keeping the highest confidence ones."""
        seen_motivations = {}
        
        for motivation in motivations:
            key = motivation.motivation_type
            if key not in seen_motivations or motivation.confidence > seen_motivations[key].confidence:
                seen_motivations[key] = motivation
        
        return list(seen_motivations.values())
    
    async def _discover_preferences(self, character_name: str) -> Dict[str, List[str]]:
        """Discover character preferences for conversations and interactions."""
        try:
            character_knowledge = await self.knowledge_extractor.extract_character_self_knowledge(character_name)
            if not character_knowledge:
                return {}
            
            preferences = {
                'conversation': [],
                'topics': [],
                'interaction': []
            }
            
            # Extract conversation preferences from communication style
            comm_style = character_knowledge.get('communication_style', {})
            if 'preferred_style' in comm_style:
                for style_name, _style_data in comm_style['preferred_style'].items():
                    preferences['conversation'].append(f"Prefers {style_name} communication style")
            
            # Extract topic preferences from interests
            interests = character_knowledge.get('interests', {})
            for interest_name in interests.keys():
                preferences['topics'].append(f"Enjoys discussing {interest_name}")
            
            # Extract interaction preferences from values
            values = character_knowledge.get('values', {})
            for value_name, value_data in values.items():
                if 'interaction' in value_data.get('description', '').lower():
                    preferences['interaction'].append(f"Values {value_name} in interactions")
            
            return preferences
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning("Error discovering preferences for %s: %s", character_name, e)
            return {}
    
    async def _analyze_value_system(self, character_name: str) -> Dict[str, List]:
        """Analyze character's value system for core values and potential conflicts."""
        try:
            character_knowledge = await self.knowledge_extractor.extract_character_self_knowledge(character_name)
            if not character_knowledge:
                return {}
            
            analysis = {
                'core_values': [],
                'conflicts': [],
                'expressions': []
            }
            
            values = character_knowledge.get('values', {})
            
            # Identify core values (those with rich descriptions)
            for value_name, value_data in values.items():
                description = value_data.get('description', '')
                if len(description) > 50:  # Rich description suggests core value
                    analysis['core_values'].append({
                        'name': value_name,
                        'description': description,
                        'importance': 'high'
                    })
            
            # Look for value expressions in trait relationships
            trait_relationships = await self.graph_builder.query_character_relationships(character_name)
            for rel in trait_relationships:
                if rel['source_trait'].startswith('value:'):
                    analysis['expressions'].append({
                        'value': rel['source_trait'],
                        'expression': rel['target_trait'],
                        'strength': rel['strength']
                    })
            
            return analysis
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning("Error analyzing value system for %s: %s", character_name, e)
            return {}

def create_dynamic_trait_discovery(character_self_knowledge_extractor, character_graph_knowledge_builder):
    """Factory function to create DynamicTraitDiscovery instance."""
    return DynamicTraitDiscovery(
        character_self_knowledge_extractor=character_self_knowledge_extractor,
        character_graph_knowledge_builder=character_graph_knowledge_builder
    )