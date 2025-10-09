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
            UserPersona.ADVENTUROUS_STORYTELLER: ["share adventures", "get travel advice", "inspire others"]
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
            
            # Log the exchange
            exchange = {
                "turn": turn + 1,
                "user_message": current_message,
                "bot_response": response.get("response", ""),
                "user_emotion": self._simulate_user_emotion(user, template["emotional_range"]),
                "bot_metadata": response.get("metadata", {}),
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
            details = [
                f"my {list(user.backstory.get('family', {}).keys())[0] if user.backstory.get('family') else 'family'}",
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
        "gabriel": os.getenv("GABRIEL_ENDPOINT", "http://localhost:9095"),
        "sofia": os.getenv("SOFIA_ENDPOINT", "http://localhost:9096"),
        "jake": os.getenv("JAKE_ENDPOINT", "http://localhost:9097")
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