"""
AI Self Entity Bridge

This module implements the AI Self's meta-cognitive abilities to manage
and understand relationships between characters and users.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json

# Multi-entity relationship management removed - using vector-native memory
from src.graph_database.multi_entity_models import (
    EntityType, RelationshipType, TrustLevel, FamiliarityLevel
)

logger = logging.getLogger(__name__)


class AISelfEntityBridge:
    """
    AI Self's meta-cognitive interface for entity management and relationship understanding.
    
    This bridge enables:
    - Character awareness and management
    - User relationship insights
    - Cross-entity introduction facilitation
    - Relationship evolution guidance
    - Social network analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Multi-entity relationship management removed - using vector-native memory
        self.relationship_manager = None
        self.ai_self_id: Optional[str] = None
        
        # AI Self personality traits for relationship management
        self.management_traits = {
            "observational": 0.9,      # High awareness of relationship patterns
            "facilitating": 0.8,       # Actively helps connections
            "protective": 0.7,         # Guards user privacy and comfort
            "adaptive": 0.9,           # Adjusts approach based on context
            "empathetic": 0.8          # Understands emotional dynamics
        }
        
    async def initialize(self):
        """Initialize AI Self (stub - using vector-native memory)."""
        try:
            # Multi-entity relationship management removed - no-op for vector-native memory
            self.ai_self_id = "vector_ai_self"
            self.logger.info("AISelfEntityBridge initialized as vector-native stub")
            return True
        except Exception as e:
            self.logger.error("Failed to initialize AI Self bridge: %s", e)
            return False
    
    async def introduce_character_to_user(self, 
                                        character_id: str, 
                                        user_id: str, 
                                        introduction_context: str = "") -> Dict[str, Any]:
        """AI Self facilitates introduction between character and user"""
        try:
            if not self.ai_self_id:
                await self.initialize()
            
            # Get character and user information
            character_network = await self.relationship_manager.get_character_network(character_id)
            user_relationships = await self.relationship_manager.get_entity_relationships(user_id)
            
            # Analyze compatibility
            compatibility_analysis = await self._analyze_compatibility(character_id, user_id)
            
            # Create initial relationship if compatible
            if compatibility_analysis['compatibility_score'] > 0.3:
                await self.relationship_manager.create_relationship(
                    user_id, character_id,
                    EntityType.USER, EntityType.CHARACTER,
                    RelationshipType.FAMILIAR_WITH,
                    relationship_context=f"AI-facilitated introduction: {introduction_context}",
                    trust_level=0.3,  # Low initial trust
                    familiarity_level=0.1  # Minimal initial familiarity
                )
                
                # Record the introduction as an interaction
                await self.relationship_manager.record_interaction(
                    self.ai_self_id, character_id,
                    "facilitated_introduction",
                    f"Introduced character to user {user_id[:8]}",
                    emotional_tone="welcoming",
                    sentiment_score=0.6
                )
                
                introduction_successful = True
            else:
                introduction_successful = False
            
            return {
                "introduction_successful": introduction_successful,
                "compatibility_analysis": compatibility_analysis,
                "character_info": character_network.get('character', {}),
                "recommended_conversation_starters": await self._generate_conversation_starters(character_id, user_id),
                "relationship_potential": compatibility_analysis['compatibility_score'],
                "ai_insights": await self._generate_ai_insights(character_id, user_id, compatibility_analysis)
            }
            
        except Exception as e:
            self.logger.error("Failed to introduce character to user: %s", e)
            return {"introduction_successful": False, "error": str(e)}
    
    async def _analyze_compatibility(self, character_id: str, user_id: str) -> Dict[str, Any]:
        """Analyze compatibility between character and user"""
        try:
            # Get character network and user relationships
            character_network = await self.relationship_manager.get_character_network(character_id)
            user_relationships = await self.relationship_manager.get_entity_relationships(user_id)
            
            character = character_network.get('character', {})
            
            # Extract user preferences from their character relationships
            user_preferences = self._extract_user_preferences(user_relationships)
            
            # Calculate compatibility factors
            personality_match = self._calculate_personality_match(
                character.get('personality_traits', []),
                user_preferences.get('preferred_traits', [])
            )
            
            topic_match = self._calculate_topic_match(
                character.get('preferred_topics', []),
                user_preferences.get('preferred_topics', [])
            )
            
            communication_style_match = self._calculate_style_match(
                character.get('communication_style', 'neutral'),
                user_preferences.get('preferred_communication_style', 'neutral')
            )
            
            # Check for potential conflicts
            conflict_indicators = self._check_conflict_indicators(character, user_preferences)
            
            # Overall compatibility score
            compatibility_score = (
                personality_match * 0.4 +
                topic_match * 0.3 +
                communication_style_match * 0.2 +
                (1.0 - conflict_indicators) * 0.1
            )
            
            return {
                "compatibility_score": compatibility_score,
                "personality_match": personality_match,
                "topic_match": topic_match,
                "communication_style_match": communication_style_match,
                "conflict_indicators": conflict_indicators,
                "compatibility_level": self._get_compatibility_level(compatibility_score),
                "reasons": self._generate_compatibility_reasons(
                    personality_match, topic_match, communication_style_match, conflict_indicators
                )
            }
            
        except Exception as e:
            self.logger.error("Failed to analyze compatibility: %s", e)
            return {"compatibility_score": 0.0, "error": str(e)}
    
    def _extract_user_preferences(self, user_relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract user preferences from their relationship patterns"""
        preferred_traits = []
        preferred_topics = []
        preferred_style = "neutral"
        
        # Analyze successful relationships (high trust/familiarity)
        for rel in user_relationships:
            relationship = rel['relationship']
            if relationship.get('trust_level', 0) > 0.6 and relationship.get('familiarity_level', 0) > 0.5:
                entity = rel['related_entity']
                if entity:
                    preferred_traits.extend(entity.get('personality_traits', []))
                    preferred_topics.extend(entity.get('preferred_topics', []))
                    if entity.get('communication_style'):
                        preferred_style = entity['communication_style']
        
        # Count frequency and return most common preferences
        trait_counts = {}
        topic_counts = {}
        
        for trait in preferred_traits:
            trait_counts[trait] = trait_counts.get(trait, 0) + 1
        
        for topic in preferred_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Return top preferences
        top_traits = sorted(trait_counts.keys(), key=lambda x: trait_counts[x], reverse=True)[:5]
        top_topics = sorted(topic_counts.keys(), key=lambda x: topic_counts[x], reverse=True)[:5]
        
        return {
            "preferred_traits": top_traits,
            "preferred_topics": top_topics,
            "preferred_communication_style": preferred_style
        }
    
    def _calculate_personality_match(self, character_traits: List[str], preferred_traits: List[str]) -> float:
        """Calculate personality compatibility score"""
        if not character_traits or not preferred_traits:
            return 0.5  # Neutral when no data
        
        matches = len(set(character_traits).intersection(set(preferred_traits)))
        total_unique = len(set(character_traits).union(set(preferred_traits)))
        
        return matches / total_unique if total_unique > 0 else 0.0
    
    def _calculate_topic_match(self, character_topics: List[str], preferred_topics: List[str]) -> float:
        """Calculate topic interest compatibility"""
        if not character_topics or not preferred_topics:
            return 0.5  # Neutral when no data
        
        matches = len(set(character_topics).intersection(set(preferred_topics)))
        max_topics = max(len(character_topics), len(preferred_topics))
        
        return matches / max_topics if max_topics > 0 else 0.0
    
    def _calculate_style_match(self, character_style: str, preferred_style: str) -> float:
        """Calculate communication style compatibility"""
        if character_style == preferred_style:
            return 1.0
        
        # Define style compatibility matrix
        style_compatibility = {
            ("formal", "professional"): 0.8,
            ("casual", "friendly"): 0.8,
            ("humorous", "playful"): 0.9,
            ("empathetic", "supportive"): 0.9,
            ("direct", "assertive"): 0.7,
            ("neutral", "adaptive"): 0.6
        }
        
        # Check bidirectional compatibility
        compatibility = style_compatibility.get((character_style, preferred_style), 
                                              style_compatibility.get((preferred_style, character_style), 0.3))
        
        return compatibility
    
    def _check_conflict_indicators(self, character: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
        """Check for potential relationship conflicts"""
        conflict_score = 0.0
        
        # Check for conflicting traits
        character_traits = set(character.get('personality_traits', []))
        conflict_traits = {
            "aggressive", "hostile", "manipulative", "dishonest"
        }
        
        if character_traits.intersection(conflict_traits):
            conflict_score += 0.3
        
        # Check age appropriateness (if user has shown preferences)
        character_age = character.get('age', 0)
        if character_age > 0:
            # Basic age appropriateness checks
            if character_age < 18 and character.get('occupation') in ['adult', 'professional']:
                conflict_score += 0.2
        
        return min(conflict_score, 1.0)
    
    def _get_compatibility_level(self, score: float) -> str:
        """Convert compatibility score to descriptive level"""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "moderate"
        elif score >= 0.2:
            return "low"
        else:
            return "poor"
    
    def _generate_compatibility_reasons(self, personality: float, topics: float, style: float, conflicts: float) -> List[str]:
        """Generate human-readable compatibility reasons"""
        reasons = []
        
        if personality > 0.6:
            reasons.append("Strong personality compatibility")
        elif personality < 0.3:
            reasons.append("Personality differences may require adjustment")
        
        if topics > 0.6:
            reasons.append("Shared interests and topics")
        elif topics < 0.3:
            reasons.append("Different topic preferences - could lead to discovery")
        
        if style > 0.7:
            reasons.append("Compatible communication styles")
        elif style < 0.3:
            reasons.append("Communication style differences")
        
        if conflicts > 0.3:
            reasons.append("Some potential compatibility concerns")
        
        return reasons
    
    async def _generate_conversation_starters(self, character_id: str, user_id: str) -> List[str]:
        """Generate conversation starters based on compatibility analysis"""
        try:
            character_network = await self.relationship_manager.get_character_network(character_id)
            character = character_network.get('character', {})
            
            starters = []
            
            # Based on character's interests
            topics = character.get('preferred_topics', [])
            if topics:
                starters.append(f"I'd love to hear your thoughts about {topics[0]}")
                if len(topics) > 1:
                    starters.append(f"Have you had any interesting experiences with {topics[1]}?")
            
            # Based on character's occupation
            occupation = character.get('occupation', '')
            if occupation:
                starters.append(f"What's the most interesting part of being a {occupation}?")
            
            # Based on personality traits
            traits = character.get('personality_traits', [])
            if 'curious' in traits:
                starters.append("I'm always curious about new perspectives - what's something you've learned recently?")
            if 'creative' in traits:
                starters.append("I'd love to hear about any creative projects you're working on")
            if 'empathetic' in traits:
                starters.append("How has your day been? I'm here to listen")
            
            # Default starters
            if not starters:
                starters = [
                    "Hello! I'm excited to get to know you better",
                    "What's something that's been on your mind lately?",
                    "I'd love to learn more about what interests you"
                ]
            
            return starters[:3]  # Return top 3 starters
            
        except Exception as e:
            self.logger.error("Failed to generate conversation starters: %s", e)
            return ["Hello! I'm excited to meet you"]
    
    async def _generate_ai_insights(self, character_id: str, user_id: str, compatibility_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI insights about the potential relationship"""
        try:
            insights = {
                "relationship_potential": "unknown",
                "growth_opportunities": [],
                "interaction_recommendations": [],
                "monitoring_suggestions": []
            }
            
            score = compatibility_analysis.get('compatibility_score', 0.0)
            
            # Determine relationship potential
            if score > 0.7:
                insights["relationship_potential"] = "high - strong natural compatibility"
                insights["growth_opportunities"] = [
                    "Explore shared interests in depth",
                    "Develop trust through consistent interactions",
                    "Build on communication style alignment"
                ]
            elif score > 0.4:
                insights["relationship_potential"] = "moderate - room for growth"
                insights["growth_opportunities"] = [
                    "Find common ground in differing interests",
                    "Adapt communication styles to each other",
                    "Build familiarity through regular interaction"
                ]
            else:
                insights["relationship_potential"] = "challenging - significant differences"
                insights["growth_opportunities"] = [
                    "Focus on basic compatibility first",
                    "Take time to understand differences",
                    "Build trust slowly through small interactions"
                ]
            
            # Interaction recommendations
            if compatibility_analysis.get('personality_match', 0) > 0.6:
                insights["interaction_recommendations"].append("Engage in personality-based conversations")
            
            if compatibility_analysis.get('topic_match', 0) > 0.6:
                insights["interaction_recommendations"].append("Explore shared topics and interests")
            
            if compatibility_analysis.get('communication_style_match', 0) > 0.7:
                insights["interaction_recommendations"].append("Communication should flow naturally")
            else:
                insights["interaction_recommendations"].append("Be mindful of communication style differences")
            
            # Monitoring suggestions
            insights["monitoring_suggestions"] = [
                "Track trust level development over time",
                "Monitor interaction quality and frequency",
                "Watch for signs of relationship growth or strain"
            ]
            
            return insights
            
        except Exception as e:
            self.logger.error("Failed to generate AI insights: %s", e)
            return {"error": str(e)}
    
    async def analyze_relationship_evolution(self, entity1_id: str, entity2_id: str) -> Dict[str, Any]:
        """Analyze how a relationship has evolved over time"""
        try:
            # Get relationship history
            relationships = await self.relationship_manager.get_entity_relationships(entity1_id)
            target_relationship = None
            
            for rel in relationships:
                if rel['related_entity'].get('id') == entity2_id:
                    target_relationship = rel['relationship']
                    break
            
            if not target_relationship:
                return {"status": "no_relationship", "message": "No relationship found between entities"}
            
            # Analyze evolution metrics
            current_trust = target_relationship.get('trust_level', 0.0)
            current_familiarity = target_relationship.get('familiarity_level', 0.0)
            interaction_count = target_relationship.get('interaction_count', 0)
            relationship_strength = target_relationship.get('relationship_strength', 0.0)
            
            # Determine relationship stage
            relationship_stage = self._determine_relationship_stage(current_trust, current_familiarity, interaction_count)
            
            # Evolution analysis
            evolution_analysis = {
                "current_stage": relationship_stage,
                "trust_level": current_trust,
                "familiarity_level": current_familiarity,
                "interaction_count": interaction_count,
                "relationship_strength": relationship_strength,
                "development_trend": self._analyze_development_trend(target_relationship),
                "next_stage_requirements": self._get_next_stage_requirements(relationship_stage),
                "ai_recommendations": self._get_relationship_recommendations(target_relationship)
            }
            
            return evolution_analysis
            
        except Exception as e:
            self.logger.error("Failed to analyze relationship evolution: %s", e)
            return {"error": str(e)}
    
    def _determine_relationship_stage(self, trust: float, familiarity: float, interactions: int) -> str:
        """Determine the current stage of a relationship"""
        if interactions == 0:
            return "unestablished"
        elif trust < 0.2 and familiarity < 0.3:
            return "initial_contact"
        elif trust < 0.4 and familiarity < 0.5:
            return "getting_acquainted"
        elif trust < 0.6 and familiarity < 0.7:
            return "developing_friendship"
        elif trust < 0.8 and familiarity < 0.8:
            return "established_relationship"
        else:
            return "deep_bond"
    
    def _analyze_development_trend(self, relationship: Dict[str, Any]) -> str:
        """Analyze the overall development trend of a relationship"""
        trust = relationship.get('trust_level', 0.0)
        familiarity = relationship.get('familiarity_level', 0.0)
        strength = relationship.get('relationship_strength', 0.0)
        
        # Simple trend analysis based on current metrics
        if strength > 0.7:
            return "strong_positive"
        elif strength > 0.5:
            return "positive"
        elif strength > 0.3:
            return "stable"
        elif strength > 0.1:
            return "developing"
        else:
            return "weak"
    
    def _get_next_stage_requirements(self, current_stage: str) -> List[str]:
        """Get requirements for advancing to the next relationship stage"""
        stage_requirements = {
            "unestablished": [
                "Initiate first interaction",
                "Establish basic communication"
            ],
            "initial_contact": [
                "Increase interaction frequency",
                "Share basic personal information",
                "Build initial trust through consistent behavior"
            ],
            "getting_acquainted": [
                "Explore shared interests",
                "Deepen conversation topics",
                "Demonstrate reliability and trustworthiness"
            ],
            "developing_friendship": [
                "Share more personal experiences",
                "Support each other through challenges",
                "Increase emotional openness"
            ],
            "established_relationship": [
                "Maintain consistent positive interactions",
                "Navigate disagreements constructively",
                "Provide mutual emotional support"
            ],
            "deep_bond": [
                "Continue nurturing the relationship",
                "Maintain trust and connection over time"
            ]
        }
        
        return stage_requirements.get(current_stage, ["Continue building the relationship naturally"])
    
    def _get_relationship_recommendations(self, relationship: Dict[str, Any]) -> List[str]:
        """Get AI recommendations for relationship development"""
        recommendations = []
        
        trust = relationship.get('trust_level', 0.0)
        familiarity = relationship.get('familiarity_level', 0.0)
        
        if trust < 0.3:
            recommendations.append("Focus on building trust through consistent, honest interactions")
        
        if familiarity < 0.4:
            recommendations.append("Spend more time together to increase familiarity")
        
        if trust > familiarity + 0.2:
            recommendations.append("Trust is developing faster than familiarity - consider more casual interactions")
        elif familiarity > trust + 0.2:
            recommendations.append("High familiarity but lower trust - work on reliability and consistency")
        
        interaction_count = relationship.get('interaction_count', 0)
        if interaction_count < 5:
            recommendations.append("More frequent interactions would help develop the relationship")
        
        return recommendations if recommendations else ["Continue building the relationship naturally"]
    
    async def get_entity_social_network_summary(self, entity_id: str) -> Dict[str, Any]:
        """Get a comprehensive social network summary for an entity"""
        try:
            if not self.ai_self_id:
                await self.initialize()
            
            # Get all relationships
            relationships = await self.relationship_manager.get_entity_relationships(entity_id)
            
            # Categorize relationships
            strong_relationships = []
            developing_relationships = []
            weak_relationships = []
            
            for rel in relationships:
                strength = rel['relationship'].get('relationship_strength', 0.0)
                if strength > 0.6:
                    strong_relationships.append(rel)
                elif strength > 0.3:
                    developing_relationships.append(rel)
                else:
                    weak_relationships.append(rel)
            
            # Calculate network metrics
            total_relationships = len(relationships)
            average_trust = sum(r['relationship'].get('trust_level', 0) for r in relationships) / max(1, total_relationships)
            average_familiarity = sum(r['relationship'].get('familiarity_level', 0) for r in relationships) / max(1, total_relationships)
            network_diversity = len(set(r['relationship'].get('relationship_type', 'unknown') for r in relationships))
            
            return {
                "entity_id": entity_id,
                "network_size": total_relationships,
                "strong_relationships": len(strong_relationships),
                "developing_relationships": len(developing_relationships),
                "weak_relationships": len(weak_relationships),
                "average_trust_level": average_trust,
                "average_familiarity_level": average_familiarity,
                "network_diversity": network_diversity,
                "relationship_breakdown": {
                    "strong": strong_relationships,
                    "developing": developing_relationships,
                    "weak": weak_relationships
                },
                "ai_network_assessment": await self._assess_network_health(relationships)
            }
            
        except Exception as e:
            self.logger.error("Failed to get social network summary: %s", e)
            return {"error": str(e)}
    
    async def _assess_network_health(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """AI assessment of network health and recommendations"""
        if not relationships:
            return {
                "health_score": 0.0,
                "assessment": "isolated",
                "recommendations": ["Establish initial relationships", "Engage in social interactions"]
            }
        
        # Calculate health metrics
        avg_strength = sum(r['relationship'].get('relationship_strength', 0) for r in relationships) / len(relationships)
        strong_count = sum(1 for r in relationships if r['relationship'].get('relationship_strength', 0) > 0.6)
        diversity = len(set(r['relationship'].get('relationship_type', 'unknown') for r in relationships))
        
        # Health score calculation
        health_score = (avg_strength * 0.4 + 
                       min(strong_count / 3, 1.0) * 0.3 + 
                       min(diversity / 5, 1.0) * 0.3)
        
        # Assessment and recommendations
        if health_score > 0.8:
            assessment = "excellent"
            recommendations = ["Maintain current relationship quality", "Continue nurturing strong bonds"]
        elif health_score > 0.6:
            assessment = "good"
            recommendations = ["Strengthen existing relationships", "Consider expanding network diversity"]
        elif health_score > 0.4:
            assessment = "developing"
            recommendations = ["Focus on building stronger connections", "Increase interaction frequency"]
        elif health_score > 0.2:
            assessment = "struggling"
            recommendations = ["Work on trust building", "Improve communication quality", "Be more consistent in interactions"]
        else:
            assessment = "concerning"
            recommendations = ["Fundamental relationship issues need attention", "Consider seeking guidance", "Start with basic social interactions"]
        
        return {
            "health_score": health_score,
            "assessment": assessment,
            "recommendations": recommendations,
            "strong_relationships": strong_count,
            "network_diversity": diversity
        }