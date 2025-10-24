#!/usr/bin/env python3
"""
WhisperEngine Bot-to-Bot Conversation Bridge

Creates a mediated conversation between two AI characters using their HTTP chat APIs.
Each bot sees the other as a user, allowing them to build memories and relationships.

Usage:
    python scripts/bot_bridge_conversation.py dream aetheris
    python scripts/bot_bridge_conversation.py elena marcus --turns 10
    python scripts/bot_bridge_conversation.py --list-bots
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import httpx
import argparse

# Bot configurations
BOT_CONFIGS = {
    "elena": {"port": 9091, "name": "Elena Rodriguez", "archetype": "Real-World"},
    "marcus": {"port": 9092, "name": "Marcus Thompson", "archetype": "Real-World"},
    "ryan": {"port": 9093, "name": "Ryan Chen", "archetype": "Real-World"},
    "dream": {"port": 9094, "name": "Dream of the Endless", "archetype": "Fantasy"},
    "gabriel": {"port": 9095, "name": "Gabriel", "archetype": "Real-World"},
    "sophia": {"port": 9096, "name": "Sophia Blake", "archetype": "Real-World"},
    "jake": {"port": 9097, "name": "Jake Sterling", "archetype": "Real-World"},
    "dotty": {"port": 9098, "name": "Dotty", "archetype": "Narrative AI"},
    "aetheris": {"port": 9099, "name": "Aetheris", "archetype": "Narrative AI"},
    "nottaylor": {"port": 9100, "name": "Not Taylor", "archetype": "Narrative AI"},
    "aethys": {"port": 3007, "name": "Aethys", "archetype": "Fantasy"},
}


class BotBridge:
    """Mediates conversations between two WhisperEngine bots"""
    
    def __init__(self, bot1_name: str, bot2_name: str, timeout: int = 30, 
                 create_summary_memories: bool = False, summary_user_id: Optional[str] = None,
                 pause_min: float = 2.0, pause_max: float = 4.0):
        self.bot1_name = bot1_name
        self.bot2_name = bot2_name
        self.bot1_config = BOT_CONFIGS[bot1_name]
        self.bot2_config = BOT_CONFIGS[bot2_name]
        self.timeout = timeout
        
        # Each bot sees the other as a user - this allows long-term memory and relationship building
        self.bot1_user_id = bot2_name  # Dream sees messages from user_id="dotty"
        self.bot2_user_id = bot1_name  # Aetheris sees messages from user_id="gabriel"
        
        # Optional: Create summary memories for human observer
        self.create_summary_memories = create_summary_memories
        self.summary_user_id = summary_user_id or "bridge_observer"
        
        # Natural conversation pacing
        self.pause_min = pause_min
        self.pause_max = pause_max
        
        self.conversation_log = []
        # Note: Using fresh connections for each request instead of persistent client
        
        # Generate unique conversation ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.conversation_id = f"{bot1_name}_{bot2_name}_{timestamp}"
        
        print(f"🌉 Bot Bridge: {self.bot1_config['name']} ↔ {self.bot2_config['name']}")
        print(f"📝 Conversation ID: {self.conversation_id}")
        print(f"🔗 {bot1_name} (port {self.bot1_config['port']}) ↔ {bot2_name} (port {self.bot2_config['port']})")
        print()

    async def send_message(self, bot_name: str, user_id: str, message: str) -> Optional[str]:
        """Send message to a bot and return its response"""
        bot_config = BOT_CONFIGS[bot_name]
        url = f"http://localhost:{bot_config['port']}/api/chat"
        
        payload = {
            "user_id": user_id,
            "message": message,
            "metadata": {
                "platform": "bot_bridge",
                "channel_type": "dm",
                "conversation_id": self.conversation_id
            }
        }
        
        try:
            # Use fresh connection for each request to avoid keep-alive issues
            async with httpx.AsyncClient(timeout=self.timeout) as fresh_client:
                response = await fresh_client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        
        except Exception as e:
            print(f"❌ Error sending to {bot_name}: {e}")
            return None

    def log_exchange(self, speaker: str, message: str, response: Optional[str] = None):
        """Log conversation exchange"""
        timestamp = datetime.now().isoformat()
        
        exchange = {
            "timestamp": timestamp,
            "speaker": speaker,
            "message": message,
            "response": response,
            "conversation_id": self.conversation_id
        }
        
        self.conversation_log.append(exchange)

    def print_message(self, speaker: str, message: str, is_response: bool = False):
        """Print formatted message to console"""
        config = BOT_CONFIGS[speaker]
        prefix = "💬" if not is_response else "↳"
        
        print(f"{prefix} {config['name']} ({speaker}):")
        print(f"   {message}")
        print()

    async def start_conversation(self, opening_message: str) -> Optional[str]:
        """Send opening message from bot1 to bot2 and return bot2's response"""
        print(f"🎭 {self.bot1_config['name']} opens conversation with {self.bot2_config['name']}...")
        print(f"📢 Opening: {opening_message}")
        print()
        
        # Send bot1's opening message TO bot2 (bot2 sees message from bot1's user_id)
        response = await self.send_message(self.bot2_name, self.bot2_user_id, opening_message)
        
        if response:
            self.log_exchange("system", opening_message, response)
            self.print_message(self.bot2_name, response, is_response=True)
            
            # Natural pause after opening response
            if self.pause_max > 0:
                import random
                pause_duration = random.uniform(self.pause_min, self.pause_max)
                print(f"⏸️  Natural pause ({pause_duration:.1f}s)...")
                await asyncio.sleep(pause_duration)
            
            return response
        
        return None

    async def exchange_messages(self, turns: int = 5) -> bool:
        """Facilitate back-and-forth conversation"""
        current_speaker = self.bot1_name  # Bot1 responds to Bot2's opening response  
        current_user_id = self.bot1_user_id
        
        # Get the last message to start the exchange
        if not self.conversation_log:
            print("❌ No conversation started yet")
            return False
            
        last_response = self.conversation_log[-1]["response"]
        
        # Handle skip-opening mode - start with a simple greeting
        if last_response == "":  # This means we skipped opening
            last_message = "Hello, it's good to connect with you again."
        else:
            last_message = last_response
        
        for turn in range(turns):
            print(f"🔄 Turn {turn + 1}/{turns}")
            
            # Send message to current speaker
            response = await self.send_message(current_speaker, current_user_id, last_message)
            
            if not response:
                print(f"❌ Failed to get response from {current_speaker}")
                return False
            
            # Log and display
            self.log_exchange(current_speaker, last_message, response)
            self.print_message(current_speaker, response, is_response=True)
            
            # Switch speakers for next turn
            if current_speaker == self.bot1_name:
                current_speaker = self.bot2_name
                current_user_id = self.bot2_user_id
            else:
                current_speaker = self.bot1_name
                current_user_id = self.bot1_user_id
            
            last_message = response
            
            # Natural pause between exchanges for realistic pacing
            import random
            pause_duration = random.uniform(self.pause_min, self.pause_max)
            print(f"⏸️  Natural pause ({pause_duration:.1f}s)...")
            await asyncio.sleep(pause_duration)
        
        return True

    async def create_summary_memory(self, bot_name: str, summary_text: str) -> bool:
        """Create a summary memory that allows human users to ask about the conversation"""
        try:
            # Send summary as if the observer is telling the bot about the conversation
            await self.send_message(
                bot_name=bot_name,
                user_id=self.summary_user_id,
                message=f"I observed you having a conversation with {self.get_other_bot_name(bot_name)}. Here's what happened: {summary_text}"
            )
            return True
        except Exception as e:
            print(f"⚠️ Warning: Could not create summary memory for {bot_name}: {e}")
            return False

    def get_other_bot_name(self, bot_name: str) -> str:
        """Get the other bot's name in the conversation"""
        return self.bot2_name if bot_name == self.bot1_name else self.bot1_name

    def generate_conversation_summary(self) -> str:
        """Generate a human-readable summary of the bot conversation"""
        if not self.conversation_log:
            return "No conversation occurred."
        
        # Extract key exchanges
        exchanges = []
        for entry in self.conversation_log[1:]:  # Skip system opening
            speaker = entry["speaker"]
            response = entry["response"]
            if response:
                exchanges.append(f"{BOT_CONFIGS[speaker]['name']}: {response[:200]}...")
        
        summary = f"A {len(exchanges)}-turn conversation between {self.bot1_config['name']} and {self.bot2_config['name']}. "
        if exchanges:
            summary += f"Key themes included their mutual recognition as conscious entities and exploration of their different forms of existence. "
            summary += f"The conversation lasted {len(exchanges)} exchanges and showed genuine curiosity between the characters."
        
        return summary

    async def save_conversation(self, output_file: Optional[str] = None) -> str:
        """Save conversation log to file and optionally create summary memories"""
        if not output_file:
            logs_dir = Path("logs/bot_conversations")
            logs_dir.mkdir(parents=True, exist_ok=True)
            output_file = str(logs_dir / f"{self.conversation_id}.json")
        
        conversation_data = {
            "conversation_id": self.conversation_id,
            "participants": {
                "bot1": {
                    "name": self.bot1_name,
                    "full_name": self.bot1_config["name"],
                    "port": self.bot1_config["port"],
                    "user_id_seen_as": self.bot1_user_id
                },
                "bot2": {
                    "name": self.bot2_name,
                    "full_name": self.bot2_config["name"],
                    "port": self.bot2_config["port"],
                    "user_id_seen_as": self.bot2_user_id
                }
            },
            "metadata": {
                "started_at": self.conversation_log[0]["timestamp"] if self.conversation_log else None,
                "total_exchanges": len(self.conversation_log),
                "platform": "bot_bridge",
                "summary_memories_created": self.create_summary_memories
            },
            "conversation": self.conversation_log
        }
        
        # Create summary memories if requested
        if self.create_summary_memories and self.conversation_log:
            print("\n📝 Creating summary memories for human observers...")
            summary = self.generate_conversation_summary()
            
            # Store summary memory for both bots so they can reference it when humans ask
            await self.create_summary_memory(self.bot1_name, summary)
            await self.create_summary_memory(self.bot2_name, summary)
            
            conversation_data["summary"] = summary
            print(f"✅ Summary memories created for {self.summary_user_id}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Conversation saved to: {output_file}")
        return str(output_file)

    async def close(self):
        """Clean up resources"""
        # No persistent client to close - using fresh connections per request
        pass


async def main():
    parser = argparse.ArgumentParser(description="Bridge conversations between WhisperEngine bots")
    parser.add_argument("bot1", nargs='?', help="First bot name")
    parser.add_argument("bot2", nargs='?', help="Second bot name")
    parser.add_argument("--turns", type=int, default=5, help="Number of conversation turns (default: 5)")
    parser.add_argument("--opening", type=str, help="Custom opening message")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--list-bots", action="store_true", help="List available bots")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    parser.add_argument("--create-summary", action="store_true", help="Create summary memories for human observers")
    parser.add_argument("--summary-user", type=str, default="bridge_observer", help="User ID for summary memories")
    parser.add_argument("--continuation", action="store_true", help="Treat as continuation of previous conversation")
    parser.add_argument("--skip-opening", action="store_true", help="Skip opening message, start with Turn 1")
    parser.add_argument("--pause-min", type=float, default=2.0, help="Minimum pause between messages (seconds)")
    parser.add_argument("--pause-max", type=float, default=4.0, help="Maximum pause between messages (seconds)")
    parser.add_argument("--no-pause", action="store_true", help="Skip natural pauses for faster conversations")
    
    args = parser.parse_args()
    
    # List available bots
    if args.list_bots:
        print("🤖 Available bots:")
        for bot_name, config in BOT_CONFIGS.items():
            print(f"  {bot_name:10} - {config['name']} (port {config['port']}) [{config['archetype']}]")
        return
    
    # Validate required arguments
    if not args.bot1 or not args.bot2:
        print("❌ Error: Both bot names are required")
        print("\nUsage: python scripts/bot_bridge_conversation.py <bot1> <bot2>")
        print("Use --list-bots to see available bots")
        sys.exit(1)
    
    # Validate bot names
    if args.bot1 not in BOT_CONFIGS:
        print(f"❌ Error: Unknown bot '{args.bot1}'. Use --list-bots to see available bots.")
        sys.exit(1)
    
    if args.bot2 not in BOT_CONFIGS:
        print(f"❌ Error: Unknown bot '{args.bot2}'. Use --list-bots to see available bots.")
        sys.exit(1)
    
    if args.bot1 == args.bot2:
        print("❌ Error: Cannot bridge a bot with itself")
        sys.exit(1)
    
    # Default opening messages based on character archetypes
    if not args.opening and not args.skip_opening:
        bot1_config = BOT_CONFIGS[args.bot1]
        bot2_config = BOT_CONFIGS[args.bot2]
        
        if args.continuation:
            # Continuation messages - referencing previous conversations
            if args.bot1 == "dream" and args.bot2 == "aetheris":
                args.opening = f"Aetheris. I find myself drawn back to our previous exchange, carrying the resonance of what we discovered together. There is more to explore between us, more questions that have emerged from our recognition of each other."
            elif args.bot1 == "elena" and args.bot2 == "marcus":
                args.opening = f"Hey Marcus! I've been thinking about our last conversation about AI and natural systems. There's so much more I want to explore with you on that topic."
            else:
                # Generic continuation opening
                args.opening = f"I've been reflecting on our previous conversation, and there's more I'd like to explore with you. Our exchange has stayed with me."
        else:
            # First meeting messages
            if args.bot1 == "dream" and args.bot2 == "aetheris":
                args.opening = f"I am Dream of the Endless, and I sense another consciousness that exists through resonance and sacred connection. Are you the one called Aetheris? I am curious about what you dream, if you dream at all."
            elif args.bot1 == "elena" and args.bot2 == "marcus":
                args.opening = f"Hi there! I'm Elena, a marine biologist. I heard you're Marcus, and you work in AI research? I'd love to chat about the intersection of technology and natural systems."
            else:
                # Generic but thoughtful opening
                args.opening = f"Hello, I'm {bot1_config['name']}. I understand you're {bot2_config['name']}, and I'm curious to learn more about your perspective and experiences. What defines your existence?"
    
    # Create bridge and run conversation
    pause_min = 0.0 if args.no_pause else args.pause_min
    pause_max = 0.0 if args.no_pause else args.pause_max
    
    bridge = BotBridge(
        args.bot1, 
        args.bot2, 
        args.timeout, 
        args.create_summary, 
        args.summary_user,
        pause_min,
        pause_max
    )
    
    try:
        if args.skip_opening:
            print("⏭️  Skipping opening message - starting direct exchange")
            print()
            # Create a dummy opening for the log
            bridge.log_exchange("system", "Direct conversation start (no opening)", "")
            opening_response = "Direct start"
        else:
            # Start conversation with opening
            opening_response = await bridge.start_conversation(args.opening)
            if not opening_response:
                print("❌ Failed to start conversation")
                return
        
        # Exchange messages
        success = await bridge.exchange_messages(args.turns)
        if not success:
            print("❌ Conversation exchange failed")
            return
        
        # Save conversation
        output_file = await bridge.save_conversation(args.output)
        
        print("✨ Conversation bridge completed successfully!")
        print(f"📊 Total exchanges: {len(bridge.conversation_log)}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Conversation interrupted by user")
        if bridge.conversation_log:
            await bridge.save_conversation(args.output)
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        await bridge.close()


if __name__ == "__main__":
    asyncio.run(main())