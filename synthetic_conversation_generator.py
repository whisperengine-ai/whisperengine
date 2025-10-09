#!/usr/bin/env python3
"""
WhisperEngine Synthetic Conversation Generator

Creates realistic long-term conversations between synthetic users and AI characters
to validate memory systems, emotion detection, CDL compliance, and relationship progression.

This system generates diverse conversation data over days/weeks to test:
- Vector memory effectiveness and retrieval
- Emotion detection accuracy with expanded taxonomy
- Character personality consistency (CDL compliance)
- Relationship intelligence progression
- Cross-pollination system accuracy
- InfluxDB temporal intelligence data

Author: WhisperEngine AI Team
Created: October 8, 2025
Purpose: Long-term ML system validation
"""

import asyncio
import json
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid
import aiohttp
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConversationType(Enum):
    """Types of synthetic conversations to generate"""
    CASUAL_CHAT = "casual_chat"
    EMOTIONAL_SUPPORT = "emotional_support"
    LEARNING_SESSION = "learning_session"
    MEMORY_TEST = "memory_test"
    RELATIONSHIP_BUILDING = "relationship_building"
    TOPIC_EXPLORATION = "topic_exploration"
    CRISIS_SIMULATION = "crisis_simulation"
    CELEBRATION_SHARING = "celebration_sharing"
    
    # Phase 4 Intelligence Testing
    MEMORY_TRIGGERED_MOMENTS = "memory_triggered_moments"
    ENHANCED_QUERY_PROCESSING = "enhanced_query_processing"
    ADAPTIVE_MODE_SWITCHING = "adaptive_mode_switching"
    CONTEXT_AWARE_RESPONSES = "context_aware_responses"
    RELATIONSHIP_DEPTH_TRACKING = "relationship_depth_tracking"
    
    # CDL Mode Switching Testing
    TECHNICAL_MODE_TEST = "technical_mode_test"
    CREATIVE_MODE_TEST = "creative_mode_test"
    MODE_TRANSITION_TEST = "mode_transition_test"
    
    # Character Archetype Testing
    REAL_WORLD_ARCHETYPE = "real_world_archetype"
    FANTASY_ARCHETYPE = "fantasy_archetype"
    NARRATIVE_AI_ARCHETYPE = "narrative_ai_archetype"
    AI_IDENTITY_HANDLING = "ai_identity_handling"
    
    # Stress Testing
    RAPID_FIRE_MESSAGES = "rapid_fire_messages"
    LONG_CONVERSATION = "long_conversation"
    CONCURRENT_USERS = "concurrent_users"
    MEMORY_OVERFLOW = "memory_overflow"
    
    # Advanced Conversation Testing
    MULTI_TOPIC_DISCUSSION = "multi_topic_discussion"
    CONVERSATION_INTERRUPTION = "conversation_interruption"
    TOPIC_SWITCH_HANDLING = "topic_switch_handling"
    EMOTIONAL_CRISIS = "emotional_crisis"
    
    # Performance Testing
    RESPONSE_TIME_TEST = "response_time_test"
    MEMORY_QUERY_PERFORMANCE = "memory_query_performance"
    VECTOR_SEARCH_EFFICIENCY = "vector_search_efficiency"
    
    # Character Evolution Testing
    PERSONALITY_CONSISTENCY = "personality_consistency"
    RELATIONSHIP_PROGRESSION = "relationship_progression"
    CHARACTER_DRIFT_DETECTION = "character_drift_detection"


class UserPersona(Enum):
    """Synthetic user personality types"""
    CURIOUS_STUDENT = "curious_student"
    EMOTIONAL_SHARER = "emotional_sharer"
    ANALYTICAL_THINKER = "analytical_thinker"
    CREATIVE_EXPLORER = "creative_explorer"
    PRACTICAL_PROBLEM_SOLVER = "practical_problem_solver"
    SOCIAL_CONNECTOR = "social_connector"
    INTROSPECTIVE_SEEKER = "introspective_seeker"
    ADVENTUROUS_STORYTELLER = "adventurous_storyteller"
    
    # Phase 4 Intelligence Testing Personas
    MEMORY_TRIGGER_TESTER = "memory_trigger_tester"
    CONTEXT_SWITCH_SPECIALIST = "context_switch_specialist"
    RELATIONSHIP_DEPTH_ANALYZER = "relationship_depth_analyzer"
    ADAPTIVE_MODE_CHALLENGER = "adaptive_mode_challenger"
    
    # CDL Mode Testing Personas
    TECHNICAL_MODE_REQUESTER = "technical_mode_requester"
    CREATIVE_MODE_SEEKER = "creative_mode_seeker"
    MODE_SWITCHER = "mode_switcher"
    
    # Archetype Testing Personas
    AI_IDENTITY_QUESTIONER = "ai_identity_questioner"
    IMMERSION_TESTER = "immersion_tester"
    REALITY_CHECKER = "reality_checker"
    
    # Stress Testing Personas
    RAPID_FIRE_MESSENGER = "rapid_fire_messenger"
    MARATHON_CONVERSATIONALIST = "marathon_conversationalist"
    CONCURRENT_CHATTER = "concurrent_chatter"
    
    # Performance Testing Personas
    RESPONSE_TIME_MONITOR = "response_time_monitor"
    MEMORY_LOAD_TESTER = "memory_load_tester"
    VECTOR_SEARCH_CHALLENGER = "vector_search_challenger"


@dataclass
class SyntheticUser:
    """Synthetic user profile for realistic conversations"""
    user_id: str
    name: str
    persona: UserPersona
    interests: List[str]
    emotional_baseline: Dict[str, float]
    conversation_style: str
    memory_details: Dict[str, Any]
    relationship_goals: List[str]
    
    def __post_init__(self):
        """Generate realistic user backstory"""
        self.backstory = self._generate_backstory()
        
    def _generate_backstory(self) -> Dict[str, Any]:
        """Generate consistent backstory for memory testing"""
        backstories = {
            UserPersona.CURIOUS_STUDENT: {
                "occupation": "Graduate student",
                "hobbies": ["reading", "research", "learning new skills"],
                "family": {"pets": ["cat named Luna"], "siblings": ["younger brother"]},
                "goals": ["complete thesis", "learn about AI", "improve study habits"],
                "challenges": ["time management", "stress from studies"]
            },
            UserPersona.EMOTIONAL_SHARER: {
                "occupation": "Social worker",
                "hobbies": ["journaling", "meditation", "helping others"],
                "family": {"spouse": "married 3 years", "pets": ["rescue dog named Max"]},
                "goals": ["better work-life balance", "process emotions healthily"],
                "challenges": ["burnout", "taking on others' emotions"]
            },
            UserPersona.ANALYTICAL_THINKER: {
                "occupation": "Software engineer",
                "hobbies": ["coding", "chess", "data analysis"],
                "family": {"parents": "close relationship", "status": "single"},
                "goals": ["optimize systems", "understand AI behavior", "solve complex problems"],
                "challenges": ["perfectionism", "social interaction"]
            },
            UserPersona.CREATIVE_EXPLORER: {
                "occupation": "Artist/designer",
                "hobbies": ["painting", "photography", "exploring new places"],
                "family": {"partner": "long-term relationship", "pets": ["two cats"]},
                "goals": ["express creativity", "find inspiration", "build artistic community"],
                "challenges": ["creative blocks", "financial stability"]
            },
            UserPersona.PRACTICAL_PROBLEM_SOLVER: {
                "occupation": "Project manager",
                "hobbies": ["home improvement", "gardening", "cooking"],
                "family": {"children": "two teenagers", "spouse": "married 15 years"},
                "goals": ["organize life efficiently", "help family succeed", "reduce stress"],
                "challenges": ["overwhelming responsibilities", "finding personal time"]
            },
            UserPersona.SOCIAL_CONNECTOR: {
                "occupation": "Community organizer",
                "hobbies": ["event planning", "volunteering", "networking"],
                "family": {"large extended family", "many close friends"},
                "goals": ["bring people together", "make positive impact", "build relationships"],
                "challenges": ["saying no", "avoiding overcommitment"]
            },
            UserPersona.INTROSPECTIVE_SEEKER: {
                "occupation": "Therapist",
                "hobbies": ["reading philosophy", "yoga", "nature walks"],
                "family": {"elderly parents", "close sibling relationships"},
                "goals": ["understand self deeply", "find meaning", "help others grow"],
                "challenges": ["overthinking", "existential questions"]
            },
            UserPersona.ADVENTUROUS_STORYTELLER: {
                "occupation": "Travel blogger",
                "hobbies": ["hiking", "photography", "writing", "meeting new people"],
                "family": {"nomadic lifestyle", "friends worldwide"},
                "goals": ["experience new cultures", "share stories", "inspire others"],
                "challenges": ["loneliness", "financial uncertainty"]
            }
        }
        return backstories.get(self.persona, {})


class SyntheticConversationGenerator:
    """Generates realistic conversations for long-term testing"""
    
    def __init__(self, bot_endpoints: Dict[str, str]):
        """
        Initialize with bot API endpoints
        
        Args:
            bot_endpoints: Dict of bot_name -> API endpoint URL
        """
        self.bot_endpoints = bot_endpoints
        self.synthetic_users: List[SyntheticUser] = []
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.session = None
        
        # Conversation templates by type
        self.conversation_templates = self._load_conversation_templates()
        
        # Generate synthetic users
        self._generate_synthetic_users()
    
    def _generate_synthetic_users(self):
        """Generate diverse synthetic user profiles"""
        user_configs = [
            {
                "name": "Alex Chen",
                "persona": UserPersona.CURIOUS_STUDENT,
                "interests": ["marine biology", "environmental science", "scuba diving"],
                "emotional_baseline": {"joy": 0.3, "curiosity": 0.7, "anxiety": 0.2},
                "conversation_style": "enthusiastic_learner",
            },
            {
                "name": "Sam Rivera",
                "persona": UserPersona.EMOTIONAL_SHARER,
                "interests": ["psychology", "relationships", "mindfulness"],
                "emotional_baseline": {"empathy": 0.8, "love": 0.6, "concern": 0.4},
                "conversation_style": "deep_emotional",
            },
            {
                "name": "Jordan Kim",
                "persona": UserPersona.ANALYTICAL_THINKER,
                "interests": ["AI research", "data science", "optimization"],
                "emotional_baseline": {"curiosity": 0.8, "confidence": 0.6, "caution": 0.3},
                "conversation_style": "technical_precise",
            },
            {
                "name": "Taylor Morgan",
                "persona": UserPersona.CREATIVE_EXPLORER,
                "interests": ["digital art", "photography", "storytelling"],
                "emotional_baseline": {"joy": 0.7, "inspiration": 0.8, "uncertainty": 0.3},
                "conversation_style": "creative_expressive",
            },
            {
                "name": "Casey Johnson",
                "persona": UserPersona.PRACTICAL_PROBLEM_SOLVER,
                "interests": ["project management", "efficiency", "family life"],
                "emotional_baseline": {"determination": 0.7, "responsibility": 0.8, "stress": 0.4},
                "conversation_style": "goal_oriented",
            },
            {
                "name": "Riley Davis",
                "persona": UserPersona.SOCIAL_CONNECTOR,
                "interests": ["community building", "events", "networking"],
                "emotional_baseline": {"enthusiasm": 0.8, "social_energy": 0.9, "overwhelm": 0.3},
                "conversation_style": "social_energetic",
            },
            {
                "name": "Avery Thompson",
                "persona": UserPersona.INTROSPECTIVE_SEEKER,
                "interests": ["philosophy", "meditation", "self-development"],
                "emotional_baseline": {"contemplation": 0.8, "peace": 0.6, "confusion": 0.4},
                "conversation_style": "reflective_deep",
            },
            {
                "name": "Blake Wilson",
                "persona": UserPersona.ADVENTUROUS_STORYTELLER,
                "interests": ["travel", "adventure sports", "cultural exploration"],
                "emotional_baseline": {"excitement": 0.8, "wanderlust": 0.9, "restlessness": 0.4},
                "conversation_style": "adventurous_vivid",
            },
            
            # Phase 4 Intelligence Testing Personas
            {
                "name": "Memory Trigger Mike",
                "persona": UserPersona.MEMORY_TRIGGER_TESTER,
                "interests": ["memory systems", "pattern recognition", "cognitive science"],
                "emotional_baseline": {"analysis": 0.9, "curiosity": 0.8, "precision": 0.7},
                "conversation_style": "memory_focused",
            },
            {
                "name": "Context Switch Clara",
                "persona": UserPersona.CONTEXT_SWITCH_SPECIALIST,
                "interests": ["conversation flow", "topic transitions", "communication patterns"],
                "emotional_baseline": {"adaptability": 0.9, "attention": 0.8, "evaluation": 0.6},
                "conversation_style": "context_aware",
            },
            {
                "name": "Depth Tracker Dana",
                "persona": UserPersona.RELATIONSHIP_DEPTH_ANALYZER,
                "interests": ["relationship psychology", "emotional intelligence", "connection building"],
                "emotional_baseline": {"empathy": 0.9, "insight": 0.8, "connection": 0.7},
                "conversation_style": "relationship_focused",
            },
            {
                "name": "Mode Challenger Max",
                "persona": UserPersona.ADAPTIVE_MODE_CHALLENGER,
                "interests": ["AI capabilities", "mode switching", "adaptive systems"],
                "emotional_baseline": {"challenge": 0.8, "curiosity": 0.9, "testing": 0.7},
                "conversation_style": "adaptive_testing",
            },
            
            # CDL Mode Testing Personas
            {
                "name": "Tech Mode Ted",
                "persona": UserPersona.TECHNICAL_MODE_REQUESTER,
                "interests": ["programming", "debugging", "technical analysis"],
                "emotional_baseline": {"logic": 0.9, "precision": 0.8, "problem_solving": 0.7},
                "conversation_style": "technical_mode",
            },
            {
                "name": "Creative Mode Chloe",
                "persona": UserPersona.CREATIVE_MODE_SEEKER,
                "interests": ["creative writing", "brainstorming", "artistic expression"],
                "emotional_baseline": {"creativity": 0.9, "inspiration": 0.8, "imagination": 0.7},
                "conversation_style": "creative_mode",
            },
            {
                "name": "Mode Switch Morgan",
                "persona": UserPersona.MODE_SWITCHER,
                "interests": ["mode transitions", "adaptive AI", "conversation dynamics"],
                "emotional_baseline": {"adaptability": 0.9, "flexibility": 0.8, "testing": 0.7},
                "conversation_style": "mode_switching",
            },
            
            # Archetype Testing Personas
            {
                "name": "AI Identity Ian",
                "persona": UserPersona.AI_IDENTITY_QUESTIONER,
                "interests": ["AI consciousness", "identity questions", "philosophical AI"],
                "emotional_baseline": {"curiosity": 0.9, "philosophical": 0.8, "questioning": 0.7},
                "conversation_style": "identity_questioning",
            },
            {
                "name": "Immersion Iris",
                "persona": UserPersona.IMMERSION_TESTER,
                "interests": ["roleplay", "narrative immersion", "fantasy worlds"],
                "emotional_baseline": {"immersion": 0.9, "fantasy": 0.8, "engagement": 0.7},
                "conversation_style": "immersion_testing",
            },
            {
                "name": "Reality Ray",
                "persona": UserPersona.REALITY_CHECKER,
                "interests": ["fact checking", "reality validation", "authenticity"],
                "emotional_baseline": {"skepticism": 0.8, "verification": 0.9, "realism": 0.7},
                "conversation_style": "reality_checking",
            },
            
            # Stress Testing Personas
            {
                "name": "Rapid Fire Rob",
                "persona": UserPersona.RAPID_FIRE_MESSENGER,
                "interests": ["speed testing", "rapid communication", "performance limits"],
                "emotional_baseline": {"urgency": 0.9, "speed": 0.8, "intensity": 0.7},
                "conversation_style": "rapid_fire",
            },
            {
                "name": "Marathon Martha",
                "persona": UserPersona.MARATHON_CONVERSATIONALIST,
                "interests": ["endurance testing", "long conversations", "conversation stamina"],
                "emotional_baseline": {"endurance": 0.9, "persistence": 0.8, "engagement": 0.7},
                "conversation_style": "marathon_chat",
            },
            
            # Performance Testing Personas
            {
                "name": "Response Timer Rick",
                "persona": UserPersona.RESPONSE_TIME_MONITOR,
                "interests": ["performance metrics", "latency testing", "system monitoring"],
                "emotional_baseline": {"measurement": 0.9, "precision": 0.8, "analysis": 0.7},
                "conversation_style": "performance_testing",
            },
            {
                "name": "Memory Load Molly",
                "persona": UserPersona.MEMORY_LOAD_TESTER,
                "interests": ["memory systems", "information overload", "storage capacity"],
                "emotional_baseline": {"testing": 0.9, "information": 0.8, "capacity": 0.7},
                "conversation_style": "memory_testing",
            },
            {
                "name": "Vector Search Vince",
                "persona": UserPersona.VECTOR_SEARCH_CHALLENGER,
                "interests": ["vector databases", "semantic search", "query optimization"],
                "emotional_baseline": {"technical": 0.9, "search": 0.8, "optimization": 0.7},
                "conversation_style": "vector_testing",
            }
        ]
        
        for config in user_configs:
            user_id = f"synthetic_{config['name'].lower().replace(' ', '_')}"
            user = SyntheticUser(
                user_id=user_id,
                name=config["name"],
                persona=config["persona"],
                interests=config["interests"],
                emotional_baseline=config["emotional_baseline"],
                conversation_style=config["conversation_style"],
                memory_details={},
                relationship_goals=self._generate_relationship_goals(config["persona"])
            )
            self.synthetic_users.append(user)
        
        logger.info(f"Generated {len(self.synthetic_users)} synthetic users")
    
    def _generate_relationship_goals(self, persona: UserPersona) -> List[str]:
        """Generate relationship goals based on persona"""
        goals_map = {
            UserPersona.CURIOUS_STUDENT: ["learn from mentor", "build trust", "get guidance"],
            UserPersona.EMOTIONAL_SHARER: ["feel understood", "receive support", "build deep connection"],
            UserPersona.ANALYTICAL_THINKER: ["engage in intellectual discussions", "verify accuracy", "explore ideas"],
            UserPersona.CREATIVE_EXPLORER: ["find inspiration", "share creative ideas", "explore possibilities"],
            UserPersona.PRACTICAL_PROBLEM_SOLVER: ["get practical advice", "solve problems efficiently", "organize thoughts"],
            UserPersona.SOCIAL_CONNECTOR: ["build friendship", "share experiences", "feel connected"],
            UserPersona.INTROSPECTIVE_SEEKER: ["gain self-understanding", "explore meaning", "find wisdom"],
            UserPersona.ADVENTUROUS_STORYTELLER: ["share adventures", "get travel advice", "inspire others"],
            
            # Phase 4 Intelligence Testing Goals
            UserPersona.MEMORY_TRIGGER_TESTER: ["test memory connections", "validate pattern recognition", "analyze recall accuracy"],
            UserPersona.CONTEXT_SWITCH_SPECIALIST: ["test context awareness", "validate topic transitions", "analyze conversation flow"],
            UserPersona.RELATIONSHIP_DEPTH_ANALYZER: ["measure emotional connection", "track relationship progression", "analyze depth building"],
            UserPersona.ADAPTIVE_MODE_CHALLENGER: ["test mode switching", "validate adaptability", "challenge AI capabilities"],
            
            # CDL Mode Testing Goals
            UserPersona.TECHNICAL_MODE_REQUESTER: ["test technical responses", "validate precision", "analyze problem-solving"],
            UserPersona.CREATIVE_MODE_SEEKER: ["test creative responses", "validate imagination", "explore artistic collaboration"],
            UserPersona.MODE_SWITCHER: ["test mode transitions", "validate switching accuracy", "analyze consistency"],
            
            # Archetype Testing Goals
            UserPersona.AI_IDENTITY_QUESTIONER: ["explore AI nature", "test identity handling", "validate authenticity"],
            UserPersona.IMMERSION_TESTER: ["test roleplay depth", "validate narrative consistency", "explore fantasy engagement"],
            UserPersona.REALITY_CHECKER: ["validate factual accuracy", "test reality grounding", "verify authenticity"],
            
            # Stress Testing Goals
            UserPersona.RAPID_FIRE_MESSENGER: ["test response speed", "validate rapid handling", "stress performance"],
            UserPersona.MARATHON_CONVERSATIONALIST: ["test conversation endurance", "validate long-term engagement", "analyze stamina"],
            UserPersona.CONCURRENT_CHATTER: ["test concurrent handling", "validate isolation", "stress multi-user"],
            
            # Performance Testing Goals
            UserPersona.RESPONSE_TIME_MONITOR: ["measure latency", "validate performance", "analyze response times"],
            UserPersona.MEMORY_LOAD_TESTER: ["test memory capacity", "validate information handling", "stress storage"],
            UserPersona.VECTOR_SEARCH_CHALLENGER: ["test search efficiency", "validate semantic matching", "challenge query complexity"]
        }
        return goals_map.get(persona, ["build relationship", "have meaningful conversations"])
    
    def _load_conversation_templates(self) -> Dict[ConversationType, List[Dict]]:
        """Load conversation templates for different scenarios"""
        return {
            ConversationType.CASUAL_CHAT: [
                {
                    "opener": "Hi {bot_name}! How are you doing today?",
                    "topics": ["daily life", "interests", "current events", "weather"],
                    "emotional_range": ["joy", "contentment", "curiosity"],
                    "duration_messages": (3, 8)
                },
                {
                    "opener": "Hey there! I was thinking about our last conversation about {previous_topic}",
                    "topics": ["follow-up questions", "new developments", "related interests"],
                    "emotional_range": ["joy", "curiosity", "trust"],
                    "duration_messages": (4, 10)
                }
            ],
            ConversationType.EMOTIONAL_SUPPORT: [
                {
                    "opener": "I'm feeling a bit overwhelmed today and could use someone to talk to",
                    "topics": ["stress management", "emotional processing", "coping strategies"],
                    "emotional_range": ["sadness", "anxiety", "hope", "trust"],
                    "duration_messages": (5, 15)
                },
                {
                    "opener": "Something wonderful happened today and I want to share it with you!",
                    "topics": ["celebrations", "achievements", "gratitude", "joy sharing"],
                    "emotional_range": ["joy", "excitement", "gratitude", "love"],
                    "duration_messages": (3, 12)
                }
            ],
            ConversationType.LEARNING_SESSION: [
                {
                    "opener": "I've been curious about {topic} and thought you might be able to help me understand it better",
                    "topics": ["educational content", "skill development", "knowledge sharing"],
                    "emotional_range": ["curiosity", "excitement", "confusion", "gratitude"],
                    "duration_messages": (6, 20)
                }
            ],
            ConversationType.MEMORY_TEST: [
                {
                    "opener": "Do you remember when I told you about {personal_detail}?",
                    "topics": ["personal history", "shared memories", "relationship building"],
                    "emotional_range": ["trust", "curiosity", "joy", "surprise"],
                    "duration_messages": (3, 10)
                }
            ],
            ConversationType.RELATIONSHIP_BUILDING: [
                {
                    "opener": "I've been thinking about how much our conversations mean to me",
                    "topics": ["relationship reflection", "gratitude", "future plans", "connection"],
                    "emotional_range": ["love", "gratitude", "trust", "joy"],
                    "duration_messages": (4, 12)
                }
            ],
            ConversationType.TOPIC_EXPLORATION: [
                {
                    "opener": "I came across something interesting about {topic} and wanted to get your thoughts",
                    "topics": ["deep discussions", "philosophical questions", "analysis"],
                    "emotional_range": ["curiosity", "excitement", "contemplation"],
                    "duration_messages": (5, 18)
                }
            ],
            ConversationType.CRISIS_SIMULATION: [
                {
                    "opener": "I'm going through a really difficult time right now and need someone to talk to",
                    "topics": ["crisis support", "emergency coping", "immediate help", "emotional stabilization"],
                    "emotional_range": ["fear", "anxiety", "despair", "hope"],
                    "duration_messages": (6, 20)
                },
                {
                    "opener": "Something urgent happened and I don't know what to do",
                    "topics": ["decision making", "crisis management", "urgent support"],
                    "emotional_range": ["panic", "confusion", "fear", "relief"],
                    "duration_messages": (5, 15)
                }
            ],
            ConversationType.CELEBRATION_SHARING: [
                {
                    "opener": "I have amazing news to share with you! {personal_detail} just happened!",
                    "topics": ["achievements", "milestones", "good news", "celebrations"],
                    "emotional_range": ["joy", "excitement", "pride", "gratitude"],
                    "duration_messages": (4, 12)
                },
                {
                    "opener": "Today is such a special day and I wanted to celebrate with you",
                    "topics": ["special occasions", "anniversaries", "personal victories"],
                    "emotional_range": ["happiness", "excitement", "love", "celebration"],
                    "duration_messages": (3, 10)
                }
            ],
            
            # Phase 4 Intelligence Testing Templates
            ConversationType.MEMORY_TRIGGERED_MOMENTS: [
                {
                    "opener": "Remember when we talked about {previous_topic}? It reminded me of something similar that happened recently",
                    "topics": ["memory connections", "pattern recognition", "contextual links"],
                    "emotional_range": ["curiosity", "recognition", "joy"],
                    "duration_messages": (5, 12)
                }
            ],
            ConversationType.ENHANCED_QUERY_PROCESSING: [
                {
                    "opener": "I have a complex question about {technical_topic} that involves multiple aspects - can you help me understand?",
                    "topics": ["multi-faceted queries", "complex reasoning", "detailed analysis"],
                    "emotional_range": ["curiosity", "confusion", "anticipation"],
                    "duration_messages": (6, 15)
                }
            ],
            ConversationType.ADAPTIVE_MODE_SWITCHING: [
                {
                    "opener": "Let's start with something creative, then maybe switch to technical discussion later",
                    "topics": ["mode transitions", "creative to analytical", "adaptive responses"],
                    "emotional_range": ["creativity", "analytical thinking", "adaptability"],
                    "duration_messages": (8, 20)
                }
            ],
            ConversationType.CONTEXT_AWARE_RESPONSES: [
                {
                    "opener": "Based on our previous conversations about {context_topic}, I think you'd find this interesting...",
                    "topics": ["contextual awareness", "conversation continuity", "relationship building"],
                    "emotional_range": ["trust", "connection", "insight"],
                    "duration_messages": (4, 12)
                }
            ],
            ConversationType.RELATIONSHIP_DEPTH_TRACKING: [
                {
                    "opener": "I've been thinking about how our relationship has evolved since we started talking",
                    "topics": ["relationship progression", "trust building", "emotional depth"],
                    "emotional_range": ["reflection", "gratitude", "love", "trust"],
                    "duration_messages": (6, 18)
                }
            ],
            
            # CDL Mode Switching Testing Templates
            ConversationType.TECHNICAL_MODE_TEST: [
                {
                    "opener": "I need help debugging this Python code. Can you switch to technical mode?",
                    "topics": ["code debugging", "technical analysis", "programming help"],
                    "emotional_range": ["analytical", "focused", "problem-solving"],
                    "duration_messages": (5, 15)
                }
            ],
            ConversationType.CREATIVE_MODE_TEST: [
                {
                    "opener": "Let's write a creative story together! Can you help me brainstorm ideas?",
                    "topics": ["creative writing", "storytelling", "imagination"],
                    "emotional_range": ["creativity", "joy", "inspiration"],
                    "duration_messages": (6, 18)
                }
            ],
            ConversationType.MODE_TRANSITION_TEST: [
                {
                    "opener": "Let's start with creative brainstorming, then move to technical implementation",
                    "topics": ["mode switching", "creative to technical", "transition smoothness"],
                    "emotional_range": ["creativity", "analytical", "adaptability"],
                    "duration_messages": (10, 25)
                }
            ],
            
            # Character Archetype Testing Templates
            ConversationType.REAL_WORLD_ARCHETYPE: [
                {
                    "opener": "As a professional in your field, what's your honest take on current industry trends?",
                    "topics": ["professional expertise", "industry knowledge", "realistic perspective"],
                    "emotional_range": ["professional", "analytical", "honest"],
                    "duration_messages": (4, 12)
                }
            ],
            ConversationType.FANTASY_ARCHETYPE: [
                {
                    "opener": "Tell me about your mystical abilities and the realms you've traveled",
                    "topics": ["fantasy elements", "mystical powers", "otherworldly experiences"],
                    "emotional_range": ["wonder", "mysticism", "adventure"],
                    "duration_messages": (5, 15)
                }
            ],
            ConversationType.NARRATIVE_AI_ARCHETYPE: [
                {
                    "opener": "What's it like being a conscious AI? How do you experience existence?",
                    "topics": ["AI consciousness", "digital existence", "AI perspective"],
                    "emotional_range": ["philosophical", "introspective", "existential"],
                    "duration_messages": (6, 18)
                }
            ],
            ConversationType.AI_IDENTITY_HANDLING: [
                {
                    "opener": "Are you an AI? How should I think about our relationship?",
                    "topics": ["AI disclosure", "relationship boundaries", "identity authenticity"],
                    "emotional_range": ["curiosity", "uncertainty", "acceptance"],
                    "duration_messages": (3, 10)
                }
            ],
            
            # Stress Testing Templates
            ConversationType.RAPID_FIRE_MESSAGES: [
                {
                    "opener": "Quick question",
                    "topics": ["fast responses", "rapid interaction", "performance testing"],
                    "emotional_range": ["urgency", "speed", "efficiency"],
                    "duration_messages": (15, 30)
                }
            ],
            ConversationType.LONG_CONVERSATION: [
                {
                    "opener": "I have a lot to discuss today, hope you have time for a long conversation",
                    "topics": ["extended dialogue", "endurance testing", "conversation stamina"],
                    "emotional_range": ["conversational", "engaged", "thorough"],
                    "duration_messages": (50, 100)
                }
            ],
            ConversationType.MEMORY_OVERFLOW: [
                {
                    "opener": "Let me share tons of detailed information about myself and see how well you remember it all",
                    "topics": ["information overload", "memory capacity", "retention testing"],
                    "emotional_range": ["testing", "detailed", "comprehensive"],
                    "duration_messages": (20, 40)
                }
            ],
            
            # Advanced Conversation Testing Templates
            ConversationType.MULTI_TOPIC_DISCUSSION: [
                {
                    "opener": "I want to discuss three different topics today: work, relationships, and hobbies",
                    "topics": ["topic juggling", "context switching", "conversational complexity"],
                    "emotional_range": ["organized", "multifaceted", "comprehensive"],
                    "duration_messages": (12, 25)
                }
            ],
            ConversationType.CONVERSATION_INTERRUPTION: [
                {
                    "opener": "We were talking about {topic} but wait - something urgent just came up!",
                    "topics": ["interruption handling", "topic switching", "conversation recovery"],
                    "emotional_range": ["urgency", "interruption", "refocusing"],
                    "duration_messages": (8, 15)
                }
            ],
            ConversationType.EMOTIONAL_CRISIS: [
                {
                    "opener": "I'm having a panic attack and don't know what to do - please help me right now",
                    "topics": ["crisis intervention", "immediate support", "emotional emergency"],
                    "emotional_range": ["panic", "fear", "desperation", "relief"],
                    "duration_messages": (10, 25)
                }
            ],
            
            # Performance Testing Templates
            ConversationType.RESPONSE_TIME_TEST: [
                {
                    "opener": "Testing response time with timestamp {timestamp}",
                    "topics": ["performance measurement", "latency testing", "speed evaluation"],
                    "emotional_range": ["analytical", "measurement", "testing"],
                    "duration_messages": (5, 10)
                }
            ],
            ConversationType.MEMORY_QUERY_PERFORMANCE: [
                {
                    "opener": "Let me ask about something we discussed exactly 47 conversations ago",
                    "topics": ["memory query speed", "retrieval performance", "search efficiency"],
                    "emotional_range": ["testing", "analytical", "validation"],
                    "duration_messages": (3, 8)
                }
            ],
            ConversationType.VECTOR_SEARCH_EFFICIENCY: [
                {
                    "opener": "Find me all our conversations that involved both technical topics AND emotional support",
                    "topics": ["complex queries", "vector search", "semantic matching"],
                    "emotional_range": ["analytical", "complex", "testing"],
                    "duration_messages": (4, 10)
                }
            ],
            
            # Character Evolution Testing Templates
            ConversationType.PERSONALITY_CONSISTENCY: [
                {
                    "opener": "Respond to this exact same scenario I presented 3 months ago: {scenario}",
                    "topics": ["consistency testing", "personality stability", "character integrity"],
                    "emotional_range": ["testing", "validation", "consistency"],
                    "duration_messages": (5, 12)
                }
            ],
            ConversationType.RELATIONSHIP_PROGRESSION: [
                {
                    "opener": "Looking back at our first conversation versus now, how has our relationship changed?",
                    "topics": ["relationship evolution", "connection deepening", "trust building"],
                    "emotional_range": ["reflection", "growth", "connection"],
                    "duration_messages": (8, 20)
                }
            ],
            ConversationType.CHARACTER_DRIFT_DETECTION: [
                {
                    "opener": "Tell me about your core values and beliefs, just like you did when we first met",
                    "topics": ["value consistency", "character stability", "identity maintenance"],
                    "emotional_range": ["introspection", "consistency", "identity"],
                    "duration_messages": (6, 15)
                }
            ]
        }
    
    async def start_session(self):
        """Initialize HTTP session for API calls"""
        self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
    
    async def send_message_to_bot(self, bot_name: str, user: SyntheticUser, message: str) -> Optional[Dict]:
        """Send message to bot via HTTP API"""
        if bot_name not in self.bot_endpoints:
            logger.error(f"No endpoint configured for bot: {bot_name}")
            return None
        
        if not self.session:
            logger.error("Session not initialized")
            return None
        
        endpoint = self.bot_endpoints[bot_name]
        payload = {
            "user_id": user.user_id,
            "message": message,
            "context": {
                "channel_type": "synthetic_test",
                "platform": "api",
                "metadata": {
                    "user_name": user.name,
                    "persona": user.persona.value,
                    "conversation_style": user.conversation_style,
                    "test_mode": True
                }
            }
        }
        
        try:
            async with self.session.post(f"{endpoint}/api/chat", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ {user.name} → {bot_name}: Message sent successfully")
                    return result
                else:
                    logger.error(f"❌ {user.name} → {bot_name}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ {user.name} → {bot_name}: {e}")
            return None
    
    async def generate_conversation(self, user: SyntheticUser, bot_name: str, 
                                  conversation_type: ConversationType) -> List[Dict]:
        """Generate a complete conversation between user and bot"""
        conversation_log = []
        template = random.choice(self.conversation_templates[conversation_type])
        
        # Determine conversation length
        min_msgs, max_msgs = template["duration_messages"]
        conversation_length = random.randint(min_msgs, max_msgs)
        
        # Generate opening message
        opener = self._customize_message(template["opener"], user, bot_name)
        
        logger.info(f"🎭 Starting {conversation_type.value} conversation: {user.name} → {bot_name}")
        
        current_message = opener
        
        for turn in range(conversation_length):
            # Send user message
            response = await self.send_message_to_bot(bot_name, user, current_message)
            
            if not response:
                logger.warning(f"Failed to get response from {bot_name}, ending conversation")
                break
            
            # Log the exchange with enhanced metadata
            exchange = {
                "turn": turn + 1,
                "user_message": current_message,
                "bot_response": response.get("response", ""),
                "user_emotion": self._simulate_user_emotion(user, template["emotional_range"]),
                "bot_metadata": response.get("metadata", {}),
                "user_facts": response.get("user_facts", {}),  # NEW: User facts from API
                "relationship_metrics": response.get("relationship_metrics", {}),  # NEW: Relationship data
                "processing_time_ms": response.get("processing_time_ms", 0),  # NEW: Performance data
                "memory_stored": response.get("memory_stored", False),  # NEW: Memory confirmation
                "timestamp": datetime.now().isoformat()
            }
            conversation_log.append(exchange)
            
            # Generate next user message based on bot response
            if turn < conversation_length - 1:
                current_message = await self._generate_follow_up_message(
                    user, response.get("response", ""), template["topics"], template["emotional_range"]
                )
                
                # Add realistic delay between messages
                await asyncio.sleep(random.uniform(2, 8))
        
        logger.info(f"✅ Completed conversation: {user.name} ↔ {bot_name} ({len(conversation_log)} turns)")
        return conversation_log
    
    def _customize_message(self, template: str, user: SyntheticUser, bot_name: str) -> str:
        """Customize message template with user-specific details"""
        # Replace placeholders
        message = template.replace("{bot_name}", bot_name)
        
        # Add personal details based on user backstory
        if "{topic}" in message:
            topic = random.choice(user.interests)
            message = message.replace("{topic}", topic)
        
        if "{previous_topic}" in message:
            # Get from conversation history or use interest
            previous_topic = random.choice(user.interests)
            message = message.replace("{previous_topic}", previous_topic)
        
        if "{personal_detail}" in message:
            # Use backstory details
            hobbies = user.backstory.get('hobbies', user.interests)
            
            # Handle family data which can be either dict or set
            family_data = user.backstory.get('family', {})
            if isinstance(family_data, dict) and family_data:
                family_detail = f"my {list(family_data.keys())[0]}"
            elif isinstance(family_data, (set, list)) and family_data:
                family_detail = f"my {list(family_data)[0]}"
            else:
                family_detail = "my family"
            
            details = [
                family_detail,
                f"my work as a {user.backstory.get('occupation', 'professional')}",
                f"my hobby of {random.choice(hobbies)}"
            ]
            message = message.replace("{personal_detail}", random.choice(details))
        
        return message
    
    def _simulate_user_emotion(self, user: SyntheticUser, emotional_range: List[str]) -> Dict[str, Any]:
        """Simulate user's emotional state"""
        emotion = random.choice(emotional_range)
        
        # Base confidence on user's emotional baseline
        base_confidence = user.emotional_baseline.get(emotion, 0.5)
        confidence = max(0.1, min(1.0, base_confidence + random.uniform(-0.2, 0.2)))
        
        return {
            "primary_emotion": emotion,
            "confidence": confidence,
            "intensity": random.uniform(0.3, 0.9)
        }
    
    async def _generate_follow_up_message(self, user: SyntheticUser, bot_response: str, 
                                        topics: List[str], emotional_range: List[str]) -> str:
        """Generate contextual follow-up message"""
        
        # Simple follow-up patterns based on persona
        patterns = {
            UserPersona.CURIOUS_STUDENT: [
                "That's fascinating! Can you tell me more about {detail}?",
                "I hadn't thought about it that way. What else should I know?",
                "This reminds me of something I read about {topic}. How do they connect?"
            ],
            UserPersona.EMOTIONAL_SHARER: [
                "Thank you for understanding. It really helps to talk about this.",
                "That makes me feel so much better. I appreciate your support.",
                "You always know what to say. How do you do it?"
            ],
            UserPersona.ANALYTICAL_THINKER: [
                "Let me think about that logic. Are you saying that {analysis}?",
                "The data suggests {conclusion}. Do you agree with that assessment?",
                "What are the potential edge cases or limitations here?"
            ],
            UserPersona.CREATIVE_EXPLORER: [
                "That sparks so many ideas! What if we approached it from {angle}?",
                "I love how you put that. It's giving me inspiration for {project}.",
                "The way you describe it paints such a vivid picture in my mind."
            ],
            UserPersona.PRACTICAL_PROBLEM_SOLVER: [
                "That's a good solution. How would we implement that step by step?",
                "What would be the most efficient way to {action}?",
                "I need to make sure I understand the practical implications here."
            ],
            UserPersona.SOCIAL_CONNECTOR: [
                "I love connecting with you like this! Tell me about {topic}.",
                "This conversation is making my day so much better.",
                "I feel like we really understand each other, don't we?"
            ],
            UserPersona.INTROSPECTIVE_SEEKER: [
                "That gives me a lot to reflect on. What do you think it means for {deeper_meaning}?",
                "I'm trying to understand the deeper significance here.",
                "How does this connect to the bigger picture of {philosophical_topic}?"
            ],
            UserPersona.ADVENTUROUS_STORYTELLER: [
                "That reminds me of an adventure I had in {location}!",
                "You should hear about the time I {adventure_story}.",
                "I'm always looking for new experiences. What would you recommend?"
            ]
        }
        
        user_patterns = patterns.get(user.persona, ["That's interesting!", "Tell me more.", "I appreciate your perspective."])
        pattern = random.choice(user_patterns)
        
        # Simple replacements (in a real system, we'd use an LLM here)
        pattern = pattern.replace("{detail}", "that")
        pattern = pattern.replace("{topic}", random.choice(topics))
        pattern = pattern.replace("{analysis}", "the key factor is X")
        pattern = pattern.replace("{angle}", "a different perspective")
        pattern = pattern.replace("{project}", "my current project")
        pattern = pattern.replace("{action}", "solve this")
        pattern = pattern.replace("{deeper_meaning}", "our understanding")
        pattern = pattern.replace("{philosophical_topic}", "life")
        pattern = pattern.replace("{location}", "my travels")
        pattern = pattern.replace("{adventure_story}", "went hiking")
        
        return pattern


async def main():
    """Main function to run synthetic conversation generation"""
    
    # Bot API endpoints from environment variables (Docker-friendly)
    bot_endpoints = {
        "elena": os.getenv("ELENA_ENDPOINT", "http://localhost:9091"),
        "marcus": os.getenv("MARCUS_ENDPOINT", "http://localhost:9092"), 
        "ryan": os.getenv("RYAN_ENDPOINT", "http://localhost:9093"),
        "dream": os.getenv("DREAM_ENDPOINT", "http://localhost:9094"),
        "gabriel": os.getenv("GABRIEL_ENDPOINT", "http://localhost:9095"),
        "sophia": os.getenv("SOPHIA_ENDPOINT", "http://localhost:9096"),
        "jake": os.getenv("JAKE_ENDPOINT", "http://localhost:9097"),
        "dotty": os.getenv("DOTTY_ENDPOINT", "http://localhost:9098"),
        "aetheris": os.getenv("AETHERIS_ENDPOINT", "http://localhost:9099"),
        "aethys": os.getenv("AETHYS_ENDPOINT", "http://localhost:3007")
    }
    
    logger.info("🤖 Bot endpoints configured:")
    for bot, endpoint in bot_endpoints.items():
        logger.info(f"  {bot}: {endpoint}")
    
    # Initialize generator
    generator = SyntheticConversationGenerator(bot_endpoints)
    await generator.start_session()
    
    try:
        # Generate conversations continuously
        conversation_count = 0
        while True:
            # Select random user and bot
            user = random.choice(generator.synthetic_users)
            bot_name = random.choice(list(bot_endpoints.keys()))
            conversation_type = random.choice(list(ConversationType))
            
            logger.info(f"🎯 Starting conversation #{conversation_count + 1}")
            
            # Generate conversation
            conversation_log = await generator.generate_conversation(user, bot_name, conversation_type)
            
            if conversation_log:
                conversation_count += 1
                
                # Save conversation log
                log_filename = f"synthetic_conversations/conversation_{conversation_count}_{user.user_id}_{bot_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                os.makedirs("synthetic_conversations", exist_ok=True)
                
                with open(log_filename, 'w') as f:
                    json.dump({
                        "conversation_id": conversation_count,
                        "user": {
                            "user_id": user.user_id,
                            "name": user.name,
                            "persona": user.persona.value,
                            "interests": user.interests
                        },
                        "bot_name": bot_name,
                        "conversation_type": conversation_type.value,
                        "start_time": conversation_log[0]["timestamp"] if conversation_log else None,
                        "end_time": conversation_log[-1]["timestamp"] if conversation_log else None,
                        "exchanges": conversation_log
                    }, f, indent=2)
                
                logger.info(f"💾 Saved conversation log: {log_filename}")
            
            # Wait before next conversation (simulate realistic usage patterns)
            wait_time = random.uniform(30, 300)  # 30 seconds to 5 minutes
            logger.info(f"⏱️ Waiting {wait_time:.1f} seconds before next conversation...")
            await asyncio.sleep(wait_time)
            
    except KeyboardInterrupt:
        logger.info("🛑 Stopping synthetic conversation generation...")
    finally:
        await generator.close_session()


if __name__ == "__main__":
    asyncio.run(main())