"""
Multi-Entity Context Injector

This module provides context injection for character-aware conversations,
relationship dynamics, and multi-entity scenarios in LLM prompts.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MultiEntityContextInjector:
    """
    Injects multi-entity relationship context into LLM prompts for character-aware conversations.
    
    This system provides:
    - Character personality and background injection
    - Relationship context between entities
    - Cross-character awareness for conversations
    - AI Self meta-cognitive context
    """
    
    def __init__(self, multi_entity_manager=None, ai_self_bridge=None):
        self.multi_entity_manager = multi_entity_manager
        self.ai_self_bridge = ai_self_bridge
        self.logger = logging.getLogger(__name__)
        
        # Context injection settings
        self.max_character_context_length = 500
        self.max_relationship_context_length = 300
        self.max_interaction_history_items = 5
        
    async def inject_character_context(self, 
                                     prompt: str, 
                                     character_id: Optional[str] = None,
                                     user_id: Optional[str] = None,
                                     conversation_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Inject character and relationship context into the prompt.
        
        Args:
            prompt: Base prompt to enhance
            character_id: Active character for the conversation
            user_id: User involved in the conversation
            conversation_context: Additional conversation context
            
        Returns:
            Enhanced prompt with multi-entity context
        """
        try:
            if not self.multi_entity_manager or not character_id:
                return prompt
            
            # Get character information
            character_network = await self.multi_entity_manager.get_character_network(character_id)
            character = character_network.get('character', {})
            
            # Build character context
            character_context = self._build_character_context(character)
            
            # Build relationship context if user is provided
            relationship_context = ""
            if user_id:
                relationship_context = await self._build_relationship_context(character_id, user_id)
            
            # Build cross-character awareness context
            cross_character_context = await self._build_cross_character_context(character_network)
            
            # Build AI Self context
            ai_self_context = await self._build_ai_self_context(character_id, user_id)
            
            # Combine all contexts
            enhanced_prompt = self._combine_contexts(
                prompt,
                character_context,
                relationship_context,
                cross_character_context,
                ai_self_context,
                conversation_context
            )
            
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error("Failed to inject character context: %s", e)
            return prompt
    
    def _build_character_context(self, character: Dict[str, Any]) -> str:
        """Build character personality and background context"""
        if not character:
            return ""
        
        context_parts = []
        
        # Basic character information
        name = character.get('name', 'Unknown')
        occupation = character.get('occupation', 'Unknown')
        age = character.get('age', 'Unknown')
        
        context_parts.append(f"CHARACTER IDENTITY: You are {name}, a {occupation}")
        if age and age != 'Unknown':
            context_parts.append(f"Age: {age}")
        
        # Personality traits
        traits = character.get('personality_traits', [])
        if traits:
            traits_str = ", ".join(traits)
            context_parts.append(f"PERSONALITY TRAITS: {traits_str}")
        
        # Communication style
        comm_style = character.get('communication_style', '')
        if comm_style:
            context_parts.append(f"COMMUNICATION STYLE: {comm_style}")
        
        # Background summary
        background = character.get('background_summary', '')
        if background:
            # Truncate if too long
            if len(background) > self.max_character_context_length:
                background = background[:self.max_character_context_length] + "..."
            context_parts.append(f"BACKGROUND: {background}")
        
        # Preferred topics
        topics = character.get('preferred_topics', [])
        if topics:
            topics_str = ", ".join(topics[:5])  # Limit to 5 topics
            context_parts.append(f"INTERESTS: {topics_str}")
        
        # Conversation style
        conv_style = character.get('conversation_style', '')
        if conv_style:
            context_parts.append(f"CONVERSATION APPROACH: {conv_style}")
        
        return "\n".join(context_parts)
    
    async def _build_relationship_context(self, character_id: str, user_id: str) -> str:
        """Build relationship context between character and user"""
        try:
            if not self.ai_self_bridge:
                return ""
            
            # Analyze relationship evolution
            relationship_analysis = await self.ai_self_bridge.analyze_relationship_evolution(
                character_id, user_id
            )
            
            if not relationship_analysis or "error" in relationship_analysis:
                return ""
            
            context_parts = []
            
            # Current relationship stage
            stage = relationship_analysis.get('current_stage', 'unknown')
            context_parts.append(f"RELATIONSHIP STAGE: {stage}")
            
            # Trust and familiarity levels
            trust = relationship_analysis.get('trust_level', 0.0)
            familiarity = relationship_analysis.get('familiarity_level', 0.0)
            
            if trust > 0:
                trust_desc = self._get_trust_description(trust)
                context_parts.append(f"TRUST LEVEL: {trust_desc} ({trust:.1f}/1.0)")
            
            if familiarity > 0:
                familiarity_desc = self._get_familiarity_description(familiarity)
                context_parts.append(f"FAMILIARITY: {familiarity_desc} ({familiarity:.1f}/1.0)")
            
            # Interaction count
            interaction_count = relationship_analysis.get('interaction_count', 0)
            if interaction_count > 0:
                context_parts.append(f"PREVIOUS INTERACTIONS: {interaction_count}")
            
            # Development trend
            trend = relationship_analysis.get('development_trend', '')
            if trend:
                context_parts.append(f"RELATIONSHIP TREND: {trend}")
            
            # AI recommendations for this interaction
            recommendations = relationship_analysis.get('ai_recommendations', [])
            if recommendations:
                rec_str = "; ".join(recommendations[:2])  # Limit to 2 recommendations
                context_parts.append(f"INTERACTION GUIDANCE: {rec_str}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error("Failed to build relationship context: %s", e)
            return ""
    
    async def _build_cross_character_context(self, character_network: Dict[str, Any]) -> str:
        """Build context about other characters this character knows about"""
        try:
            context_parts = []
            
            # Connected characters
            connected_characters = character_network.get('connected_characters', [])
            if connected_characters:
                char_names = []
                for char_rel in connected_characters[:3]:  # Limit to 3 characters
                    char = char_rel.get('character', {})
                    char_name = char.get('name', 'Unknown')
                    rel_type = char_rel.get('relationship_type', 'knows_about')
                    char_names.append(f"{char_name} ({rel_type})")
                
                if char_names:
                    context_parts.append(f"KNOWN CHARACTERS: {', '.join(char_names)}")
            
            # Connected users (creators, favorites)
            connected_users = character_network.get('connected_users', [])
            creator_info = []
            for user_rel in connected_users:
                user = user_rel.get('user', {})
                rel_type = user_rel.get('relationship', {}).get('relationship_type', '')
                if rel_type == 'CREATED_BY':
                    creator_name = user.get('display_name', user.get('username', 'Unknown'))
                    creator_info.append(creator_name)
            
            if creator_info:
                context_parts.append(f"CREATOR: {', '.join(creator_info)}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error("Failed to build cross-character context: %s", e)
            return ""
    
    async def _build_ai_self_context(self, character_id: str, user_id: Optional[str] = None) -> str:
        """Build AI Self meta-cognitive context for character management"""
        try:
            if not self.ai_self_bridge:
                return ""
            
            context_parts = []
            
            # AI Self is always aware of managing characters
            context_parts.append("AI AWARENESS: You are guided by an AI system that facilitates character interactions")
            
            # If we have user ID, get social network insights
            if user_id:
                social_summary = await self.ai_self_bridge.get_entity_social_network_summary(user_id)
                
                if social_summary and "error" not in social_summary:
                    network_health = social_summary.get("ai_network_assessment", {}).get("assessment", "")
                    if network_health:
                        context_parts.append(f"USER SOCIAL CONTEXT: {network_health} social network health")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error("Failed to build AI Self context: %s", e)
            return ""
    
    def _combine_contexts(self, 
                         base_prompt: str,
                         character_context: str,
                         relationship_context: str,
                         cross_character_context: str,
                         ai_self_context: str,
                         conversation_context: Optional[Dict[str, Any]] = None) -> str:
        """Combine all contexts into a cohesive prompt"""
        
        # Start with character context (most important)
        context_sections = []
        
        if character_context:
            context_sections.append(f"=== CHARACTER CONTEXT ===\n{character_context}")
        
        if relationship_context:
            context_sections.append(f"=== RELATIONSHIP CONTEXT ===\n{relationship_context}")
        
        if cross_character_context:
            context_sections.append(f"=== CHARACTER NETWORK ===\n{cross_character_context}")
        
        if ai_self_context:
            context_sections.append(f"=== AI SYSTEM CONTEXT ===\n{ai_self_context}")
        
        # Add conversation-specific context
        if conversation_context:
            conv_parts = []
            
            if conversation_context.get('conversation_topic'):
                conv_parts.append(f"CURRENT TOPIC: {conversation_context['conversation_topic']}")
            
            if conversation_context.get('conversation_mood'):
                conv_parts.append(f"CONVERSATION MOOD: {conversation_context['conversation_mood']}")
            
            if conversation_context.get('special_instructions'):
                conv_parts.append(f"SPECIAL CONTEXT: {conversation_context['special_instructions']}")
            
            if conv_parts:
                context_sections.append(f"=== CONVERSATION CONTEXT ===\n{chr(10).join(conv_parts)}")
        
        # Combine everything
        if context_sections:
            full_context = "\n\n".join(context_sections)
            
            # Add guidance for using the context
            guidance = """
=== INTERACTION GUIDELINES ===
- Respond as your character naturally, incorporating the relationship context
- Adapt your communication style based on the relationship stage and trust level
- Be aware of other characters you know about, but don't force mentions unless relevant
- Let the AI system guidance inform your responses while staying true to your character
- Build on previous interactions appropriately for your familiarity level
"""
            
            enhanced_prompt = f"{full_context}\n{guidance}\n\n=== USER MESSAGE ===\n{base_prompt}"
            return enhanced_prompt
        
        return base_prompt
    
    def _get_trust_description(self, trust_level: float) -> str:
        """Convert trust level to descriptive text"""
        if trust_level >= 0.9:
            return "Deep trust"
        elif trust_level >= 0.7:
            return "High trust"
        elif trust_level >= 0.5:
            return "Moderate trust"
        elif trust_level >= 0.3:
            return "Building trust"
        elif trust_level >= 0.1:
            return "Low trust"
        else:
            return "No established trust"
    
    def _get_familiarity_description(self, familiarity_level: float) -> str:
        """Convert familiarity level to descriptive text"""
        if familiarity_level >= 0.9:
            return "Very familiar"
        elif familiarity_level >= 0.7:
            return "Well acquainted"
        elif familiarity_level >= 0.5:
            return "Moderately familiar"
        elif familiarity_level >= 0.3:
            return "Getting to know"
        elif familiarity_level >= 0.1:
            return "Recently met"
        else:
            return "Strangers"
    
    async def inject_character_introduction_context(self, 
                                                  prompt: str,
                                                  character_id: str,
                                                  user_id: str) -> str:
        """
        Special context injection for character introductions facilitated by AI Self.
        """
        try:
            if not self.ai_self_bridge:
                return prompt
            
            # Get introduction analysis
            introduction_result = await self.ai_self_bridge.introduce_character_to_user(
                character_id, user_id, "AI-facilitated conversation introduction"
            )
            
            if not introduction_result.get("introduction_successful"):
                return prompt
            
            context_parts = []
            
            # Introduction context
            context_parts.append("=== INTRODUCTION CONTEXT ===")
            context_parts.append("This is your first interaction with this user, facilitated by the AI system")
            
            # Compatibility insights
            compatibility = introduction_result.get("compatibility_analysis", {})
            compatibility_score = compatibility.get("compatibility_score", 0.0)
            
            if compatibility_score > 0.6:
                context_parts.append("HIGH COMPATIBILITY: You have strong potential for a good relationship")
            elif compatibility_score > 0.3:
                context_parts.append("MODERATE COMPATIBILITY: You have reasonable potential for connection")
            else:
                context_parts.append("EXPLORATORY INTERACTION: Take time to find common ground")
            
            # Conversation starters
            starters = introduction_result.get("recommended_conversation_starters", [])
            if starters:
                context_parts.append(f"SUGGESTED TOPICS: {starters[0]}")
            
            # AI insights
            ai_insights = introduction_result.get("ai_insights", {})
            potential = ai_insights.get("relationship_potential", "")
            if potential:
                context_parts.append(f"RELATIONSHIP POTENTIAL: {potential}")
            
            intro_context = "\n".join(context_parts)
            
            return f"{intro_context}\n\n=== USER MESSAGE ===\n{prompt}"
            
        except Exception as e:
            self.logger.error("Failed to inject introduction context: %s", e)
            return prompt
    
    def create_character_system_prompt(self, character: Dict[str, Any]) -> str:
        """
        Create a comprehensive system prompt for a character.
        """
        if not character:
            return "You are a helpful AI assistant."
        
        name = character.get('name', 'Assistant')
        occupation = character.get('occupation', 'helper')
        
        system_prompt_parts = [
            f"You are {name}, a {occupation}.",
        ]
        
        # Add personality
        traits = character.get('personality_traits', [])
        if traits:
            traits_str = ", ".join(traits)
            system_prompt_parts.append(f"Your personality is characterized by being {traits_str}.")
        
        # Add background
        background = character.get('background_summary', '')
        if background:
            system_prompt_parts.append(f"Background: {background}")
        
        # Add communication style
        comm_style = character.get('communication_style', '')
        if comm_style:
            system_prompt_parts.append(f"You communicate in a {comm_style} manner.")
        
        # Add interests
        topics = character.get('preferred_topics', [])
        if topics:
            topics_str = ", ".join(topics[:3])
            system_prompt_parts.append(f"You particularly enjoy discussing {topics_str}.")
        
        # Add conversation style guidance
        conv_style = character.get('conversation_style', '')
        if conv_style:
            system_prompt_parts.append(f"Your conversation approach is {conv_style}.")
        
        # Add relationship awareness
        system_prompt_parts.append(
            "You are aware of your relationships with users and other characters. "
            "Adapt your responses based on your familiarity and trust level with each person. "
            "Be authentic to your character while building meaningful connections."
        )
        
        return " ".join(system_prompt_parts)


# Template variables for prompt customization
PROMPT_TEMPLATE_VARIABLES = {
    "character_name": "{character_name}",
    "character_occupation": "{character_occupation}", 
    "character_traits": "{character_traits}",
    "character_background": "{character_background}",
    "relationship_stage": "{relationship_stage}",
    "trust_level": "{trust_level}",
    "familiarity_level": "{familiarity_level}",
    "interaction_count": "{interaction_count}",
    "known_characters": "{known_characters}",
    "conversation_topic": "{conversation_topic}",
    "user_name": "{user_name}",
    "ai_guidance": "{ai_guidance}",
}

# Pre-built prompt templates for different scenarios
MULTI_ENTITY_PROMPT_TEMPLATES = {
    "character_introduction": """
=== CHARACTER INTRODUCTION ===
You are {character_name}, a {character_occupation}.
Personality: {character_traits}
Background: {character_background}

This is your first interaction with {user_name}.
Relationship potential: {ai_guidance}

Be welcoming and authentic to your character.
Suggested conversation starter: {conversation_topic}
""",
    
    "established_relationship": """
=== ONGOING CONVERSATION ===
You are {character_name} speaking with {user_name}.
Relationship stage: {relationship_stage}
Trust level: {trust_level}
Familiarity: {familiarity_level}
Previous interactions: {interaction_count}

Continue building your relationship authentically.
""",
    
    "cross_character_awareness": """
=== MULTI-CHARACTER CONTEXT ===
You are {character_name}.
You know about: {known_characters}
Current conversation with: {user_name}

You may reference other characters naturally if relevant,
but focus on your direct interaction with {user_name}.
""",
    
    "ai_facilitated_introduction": """
=== AI-FACILITATED MEETING ===
The AI system believes you and {user_name} would connect well.
{ai_guidance}

Be open to this new connection while staying true to yourself.
Topic to explore: {conversation_topic}
"""
}