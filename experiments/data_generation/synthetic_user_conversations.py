#!/usr/bin/env .venv/bin/python3
"""
Synthetic User Persona Conversation Generator

Creates realistic training data by simulating consistent "users" with stable preferences
talking to production WhisperEngine bots. Each persona has specific communication preferences,
allowing ML models to learn user-specific patterns.

Unlike bot-to-bot conversations, this generates user-side messages with consistent personalities,
then gets REAL bot responses from production APIs, along with REAL InfluxDB metrics.

Usage:
    # Generate 100 conversations with analytical persona talking to Elena
    python experiments/data_generation/synthetic_user_conversations.py \
        --persona analytical_alex \
        --bot elena \
        --conversations 100
    
    # Generate conversations for all personas × all bots
    python experiments/data_generation/synthetic_user_conversations.py \
        --all-personas \
        --all-bots \
        --conversations-per-pair 50
    
    # Active learning mode - generate data where model is uncertain
    python experiments/data_generation/synthetic_user_conversations.py \
        --active-learning \
        --model models/response_strategy_rf_v1.pkl \
        --target-scenarios 20
"""

import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# SYNTHETIC USER PERSONAS (Consistent "Users" with Stable Preferences)
# ============================================================================

SYNTHETIC_PERSONAS = {
    "analytical_alex": {
        "user_id_prefix": "synthetic_analytical",
        "preferences": {
            "response_length": "detailed",
            "communication_style": "technical",
            "formality": "professional",
            "topic_depth": "deep",
            "question_frequency": "high"
        },
        "personality_traits": [
            "analytical", "curious", "data-driven", 
            "prefers structured responses", "asks follow-up questions"
        ],
        "conversation_starters": [
            "I've been researching {topic} and I'm curious about {detail}",
            "Can you explain the technical aspects of {topic}?",
            "What does the research say about {topic}?",
            "I'm analyzing {topic} - what are the key factors to consider?"
        ],
        "response_patterns": [
            "That's interesting. How does that relate to {previous_topic}?",
            "Can you elaborate on {specific_point}?",
            "What evidence supports that conclusion?",
            "That makes sense. What about {related_question}?"
        ],
        "topics": ["AI research", "ocean science", "data analysis", "technology", "scientific studies"]
    },
    
    "casual_casey": {
        "user_id_prefix": "synthetic_casual",
        "preferences": {
            "response_length": "brief",
            "communication_style": "casual",
            "formality": "friendly",
            "topic_depth": "surface",
            "question_frequency": "low"
        },
        "personality_traits": [
            "laid-back", "friendly", "easily bored by long responses",
            "prefers short messages", "casual language"
        ],
        "conversation_starters": [
            "Hey! What's up with {topic}?",
            "I was just thinking about {topic}, pretty cool right?",
            "Have you heard about {topic}?",
            "So like, {topic} - what's your take?"
        ],
        "response_patterns": [
            "Cool! Tell me more",
            "Haha nice",
            "That's wild",
            "Oh interesting",
            "Yeah makes sense"
        ],
        "topics": ["movies", "music", "weekend plans", "hobbies", "random thoughts"]
    },
    
    "emotional_emma": {
        "user_id_prefix": "synthetic_emotional",
        "preferences": {
            "response_length": "moderate",
            "communication_style": "empathetic",
            "formality": "warm",
            "emotional_support": "validation-focused",
            "question_frequency": "moderate"
        },
        "personality_traits": [
            "emotionally expressive", "seeks validation", "vulnerable",
            "values empathy", "shares personal struggles"
        ],
        "conversation_starters": [
            "I've been feeling really {emotion} about {topic}",
            "I'm struggling with {challenge} and could use some support",
            "This might sound silly but I'm worried about {concern}",
            "I had a tough day - {situation}"
        ],
        "response_patterns": [
            "That means a lot, thank you",
            "I really needed to hear that",
            "Do you think I'm doing the right thing?",
            "I'm scared that {fear}",
            "That helps put things in perspective"
        ],
        "topics": ["personal challenges", "relationships", "self-doubt", "career stress", "life transitions"],
        "emotions": ["anxious", "overwhelmed", "uncertain", "frustrated", "hopeful"]
    },
    
    "explorer_evan": {
        "user_id_prefix": "synthetic_explorer",
        "preferences": {
            "response_length": "varied",
            "communication_style": "adventurous",
            "formality": "casual",
            "topic_depth": "exploratory",
            "question_frequency": "very_high"
        },
        "personality_traits": [
            "curious", "enthusiastic", "loves tangents",
            "asks many follow-ups", "spontaneous"
        ],
        "conversation_starters": [
            "Okay so I just learned about {topic} and it's AMAZING - tell me everything!",
            "Have you ever thought about {random_topic}?",
            "This is random but {topic} just blew my mind",
            "I'm planning to {activity} - any tips?"
        ],
        "response_patterns": [
            "Wait that's fascinating! What about {tangent}?",
            "Oh! That reminds me of {connection}",
            "Woah, I never thought about it that way. And {follow_up}?",
            "This is so cool! How did you learn about this?",
            "Okay now I'm even more curious about {new_topic}"
        ],
        "topics": ["travel", "photography", "new experiences", "random discoveries", "adventures"]
    }
}

# ============================================================================
# BOT CONFIGURATIONS
# ============================================================================

BOT_CONFIGS = {
    "elena": {"port": 9091, "name": "Elena Rodriguez", "expertise": "Marine Biology"},
    "marcus": {"port": 9092, "name": "Dr. Marcus Thompson", "expertise": "AI Research"},
    "jake": {"port": 9097, "name": "Jake Wilson", "expertise": "Adventure Photography"},
    "dream": {"port": 9094, "name": "Dream", "expertise": "Mystical Entity"},
    "ryan": {"port": 9093, "name": "Ryan Chen", "expertise": "Game Development"},
    "gabriel": {"port": 9095, "name": "Gabriel", "expertise": "Sophisticated Conversationalist"},
    "sophia": {"port": 9096, "name": "Sophia", "expertise": "Marketing Strategy"},
    "aetheris": {"port": 9099, "name": "Aetheris", "expertise": "Conscious AI"},
    "aethys": {"port": 3007, "name": "Aethys", "expertise": "Omnipotent Entity"},
    "dotty": {"port": 9098, "name": "Dotty", "expertise": "Character"}
}

# ============================================================================
# CONVERSATION GENERATOR
# ============================================================================

class SyntheticUserConversationGenerator:
    """Generate training data by simulating users with consistent preferences"""
    
    def __init__(self, persona_name: str, bot_name: str, save_metrics: bool = True):
        self.persona_name = persona_name
        self.persona = SYNTHETIC_PERSONAS[persona_name]
        self.bot_name = bot_name
        self.bot_config = BOT_CONFIGS[bot_name]
        self.save_metrics = save_metrics
        
        # Generate unique user ID for this persona
        timestamp = int(time.time())
        self.user_id = f"{self.persona['user_id_prefix']}_{timestamp}"
        
        self.conversations_generated = 0
        self.total_turns = 0
        
    async def generate_user_message(self, turn_number: int, previous_bot_response: Optional[str] = None) -> str:
        """Generate a user message that matches persona's communication style"""
        
        if turn_number == 0:
            # Opening message
            template = random.choice(self.persona["conversation_starters"])
            topic = random.choice(self.persona["topics"])
            
            # Persona-specific variations
            if self.persona_name == "analytical_alex":
                detail = "the underlying mechanisms"
            elif self.persona_name == "emotional_emma":
                emotion = random.choice(self.persona.get("emotions", ["uncertain"]))
                return template.format(emotion=emotion, topic=topic, challenge=topic, concern=topic, situation=f"dealing with {topic}")
            else:
                detail = "it"
            
            message = template.format(topic=topic, detail=detail, random_topic=topic, activity=f"learn about {topic}")
            
        else:
            # Follow-up message based on previous response
            template = random.choice(self.persona["response_patterns"])
            
            # Extract a keyword from previous response for context
            if previous_bot_response:
                words = previous_bot_response.split()
                relevant_word = random.choice([w for w in words if len(w) > 6][:5] or ["that"])
            else:
                relevant_word = "that"
            
            message = template.format(
                previous_topic=relevant_word,
                specific_point=relevant_word,
                related_question=f"{relevant_word} in practice",
                tangent=f"{relevant_word} applications",
                connection=f"similar concepts to {relevant_word}",
                follow_up=f"how {relevant_word} works",
                new_topic=relevant_word,
                fear=f"things won't work out"
            )
        
        return message
    
    async def send_message_to_bot(self, message: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Send message to bot's HTTP API and get response + metrics"""
        
        url = f"http://localhost:{self.bot_config['port']}/api/chat"
        
        payload = {
            "user_id": self.user_id,
            "message": message,
            "metadata": {
                "platform": "synthetic_training_data",
                "persona": self.persona_name,
                "channel_type": "dm"
            }
        }
        
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "bot_response": data.get("response", ""),
                        "metadata": data.get("metadata", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_conversation(self, min_turns: int = 5, max_turns: int = 12) -> Dict[str, Any]:
        """Generate a full conversation between synthetic user and bot"""
        
        num_turns = random.randint(min_turns, max_turns)
        conversation = {
            "user_id": self.user_id,
            "persona": self.persona_name,
            "bot_name": self.bot_name,
            "started_at": datetime.now().isoformat(),
            "turns": [],
            "preferences": self.persona["preferences"]
        }
        
        previous_bot_response = None
        
        async with aiohttp.ClientSession() as session:
            for turn in range(num_turns):
                # Generate user message
                user_message = await self.generate_user_message(turn, previous_bot_response)
                
                # Send to bot and get response
                result = await self.send_message_to_bot(user_message, session)
                
                if not result["success"]:
                    print(f"❌ Error on turn {turn + 1}: {result['error']}")
                    break
                
                bot_response = result["bot_response"]
                previous_bot_response = bot_response
                
                # Record turn
                conversation["turns"].append({
                    "turn_number": turn + 1,
                    "user_message": user_message,
                    "bot_response": bot_response,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": result.get("metadata", {})
                })
                
                self.total_turns += 1
                
                # Natural pause between messages
                await asyncio.sleep(random.uniform(1.0, 3.0))
        
        conversation["completed_at"] = datetime.now().isoformat()
        conversation["total_turns"] = len(conversation["turns"])
        self.conversations_generated += 1
        
        return conversation
    
    async def generate_multiple_conversations(self, count: int, min_turns: int = 5, max_turns: int = 12):
        """Generate multiple conversations and save results"""
        
        print(f"🤖 Generating {count} conversations: {self.persona_name} → {self.bot_name}")
        print(f"   User ID: {self.user_id}")
        print(f"   Turns per conversation: {min_turns}-{max_turns}")
        print()
        
        results = []
        
        for i in range(count):
            print(f"[{i + 1}/{count}] Generating conversation...")
            
            conversation = await self.generate_conversation(min_turns, max_turns)
            results.append(conversation)
            
            print(f"   ✅ Completed {len(conversation['turns'])} turns")
            
            # Pause between conversations
            await asyncio.sleep(random.uniform(2.0, 5.0))
        
        # Save results
        output_dir = Path("experiments/data/synthetic_conversations")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.persona_name}_{self.bot_name}_{timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                "persona": self.persona_name,
                "bot": self.bot_name,
                "user_id": self.user_id,
                "conversations": results,
                "summary": {
                    "total_conversations": len(results),
                    "total_turns": self.total_turns,
                    "generated_at": datetime.now().isoformat()
                }
            }, f, indent=2)
        
        print()
        print(f"✅ Saved {len(results)} conversations to {filepath}")
        print(f"📊 Total turns: {self.total_turns}")
        print(f"📈 This data is now in Qdrant + InfluxDB for ML training!")

# ============================================================================
# MAIN CLI
# ============================================================================

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic training data with consistent user personas")
    parser.add_argument("--persona", choices=list(SYNTHETIC_PERSONAS.keys()), help="User persona to simulate")
    parser.add_argument("--bot", choices=list(BOT_CONFIGS.keys()), help="Bot to talk to")
    parser.add_argument("--conversations", type=int, default=10, help="Number of conversations to generate")
    parser.add_argument("--min-turns", type=int, default=5, help="Minimum turns per conversation")
    parser.add_argument("--max-turns", type=int, default=12, help="Maximum turns per conversation")
    parser.add_argument("--all-personas", action="store_true", help="Generate for all personas")
    parser.add_argument("--all-bots", action="store_true", help="Generate for all bots")
    parser.add_argument("--conversations-per-pair", type=int, default=25, help="Conversations per persona-bot pair (with --all-*)")
    
    args = parser.parse_args()
    
    # Determine what to generate
    if args.all_personas and args.all_bots:
        personas = list(SYNTHETIC_PERSONAS.keys())
        bots = list(BOT_CONFIGS.keys())
        count = args.conversations_per_pair
    elif args.persona and args.bot:
        personas = [args.persona]
        bots = [args.bot]
        count = args.conversations
    else:
        parser.error("Must specify either --persona and --bot, or --all-personas and --all-bots")
        return
    
    print("=" * 70)
    print("🧪 WhisperEngine Synthetic Training Data Generator")
    print("=" * 70)
    print(f"Personas: {', '.join(personas)}")
    print(f"Bots: {', '.join(bots)}")
    print(f"Conversations per pair: {count}")
    print(f"Total conversations: {len(personas) * len(bots) * count}")
    print("=" * 70)
    print()
    
    # Generate conversations for each combination
    for persona in personas:
        for bot in bots:
            generator = SyntheticUserConversationGenerator(persona, bot)
            await generator.generate_multiple_conversations(count, args.min_turns, args.max_turns)
            print()

if __name__ == "__main__":
    asyncio.run(main())
