#!/usr/bin/env python3
"""
Elena Discord Personality Simulator
Simulates Discord send/receive flow focusing on personality and emotional intelligence
Tests the core features: Spanish, emojis, CDL, emotions - without full memory system
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add src to path
sys.path.append('src')

# Set environment
os.environ['LLM_CLIENT_TYPE'] = 'openrouter'

class ElenaPersonalitySimulator:
    """Simulates Elena's personality in Discord-like conversations"""
    
    def __init__(self):
        self.conversation_history = []
        self.llm_client = None
        self.cdl_integration = None
        self.emotion_analyzer = None
        
    async def initialize_systems(self):
        """Initialize core personality systems"""
        print("🤖 Initializing Elena Personality Systems...")
        
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize LLM client
        from src.llm.llm_protocol import create_llm_client
        self.llm_client = create_llm_client()
        
        # Initialize CDL integration
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        self.cdl_integration = CDLAIPromptIntegration()
        
        # Initialize emotion analyzer
        from src.intelligence.enhanced_vector_emotion_analyzer import create_enhanced_emotion_analyzer
        self.emotion_analyzer = create_enhanced_emotion_analyzer()
        
        print("✅ Elena personality systems ready!")
    
    async def chat_with_elena(self, user_message: str) -> dict:
        """Complete Elena chat simulation"""
        
        print(f"\n💬 YOU: {user_message}")
        print("-" * 60)
        
        start_time = time.time()
        result = {
            "user_message": user_message,
            "elena_response": None,
            "emotion_detected": None,
            "spanish_phrases": [],
            "ocean_emojis": [],
            "marine_terms": [],
            "enthusiasm_markers": [],
            "cdl_elements": 0,
            "processing_time_ms": 0,
            "success": False
        }
        
        try:
            # Step 1: Emotion Analysis
            print("🧠 Analyzing emotion...")
            try:
                emotion_result = await self.emotion_analyzer.analyze_emotion(
                    content=user_message,
                    user_id="discord_user",
                    conversation_context=self.conversation_history[-3:],
                    recent_emotions=[]
                )
                result["emotion_detected"] = emotion_result.primary_emotion
                print(f"   Emotion: {emotion_result.primary_emotion} ({emotion_result.confidence:.2f})")
            except Exception as e:
                print(f"   ⚠️  Emotion analysis failed: {e}")
                result["emotion_detected"] = "neutral"
            
            # Step 2: CDL Character Prompt
            print("🎭 Creating character-aware prompt...")
            try:
                # Create pipeline result for CDL integration
                from types import SimpleNamespace
                pipeline_result = SimpleNamespace(
                    emotional_state=result["emotion_detected"],
                    mood_assessment={"primary": result["emotion_detected"]},
                    personality_profile=None,
                    enhanced_context={"conversation_length": len(self.conversation_history)}
                )
                
                system_prompt = await self.cdl_integration.create_character_aware_prompt(
                    character_file="characters/examples/elena-rodriguez.json",
                    user_id="discord_user",
                    message_content=user_message,
                    pipeline_result=pipeline_result
                )
                
                # Count CDL elements
                cdl_indicators = ["Elena", "marine", "biologist", "ocean", "Spanish", "passionate", "diving"]
                result["cdl_elements"] = sum(1 for indicator in cdl_indicators if indicator.lower() in system_prompt.lower())
                print(f"   CDL elements: {result['cdl_elements']}")
                
            except Exception as e:
                print(f"   ⚠️  CDL integration failed: {e}")
                system_prompt = "You are Elena, a marine biologist. Respond with personality."
            
            # Step 3: Generate Response
            print("🗣️  Generating Elena's response...")
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
                
                elena_response = await self.llm_client.generate_chat_completion_safe(messages)
                result["elena_response"] = elena_response
                
                # Analyze personality markers in response
                result["spanish_phrases"] = self.find_spanish_phrases(elena_response)
                result["ocean_emojis"] = self.find_ocean_emojis(elena_response)
                result["marine_terms"] = self.find_marine_terms(elena_response)
                result["enthusiasm_markers"] = self.find_enthusiasm_markers(elena_response)
                
                print(f"🎯 Spanish phrases: {result['spanish_phrases']}")
                print(f"🌊 Ocean emojis: {result['ocean_emojis']}")
                print(f"🐠 Marine terms: {result['marine_terms']}")
                print(f"✨ Enthusiasm: {result['enthusiasm_markers']}")
                
                result["success"] = len(elena_response) > 10
                
            except Exception as e:
                print(f"   ⚠️  Response generation failed: {e}")
                result["elena_response"] = ""
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            if result["elena_response"]:
                self.conversation_history.append({"role": "assistant", "content": result["elena_response"]})
            
            # Processing time
            end_time = time.time()
            result["processing_time_ms"] = (end_time - start_time) * 1000
            
            if result["elena_response"]:
                print(f"\n🤖 ELENA: {result['elena_response']}")
                print(f"⏱️  Processing: {result['processing_time_ms']:.1f}ms")
            
            return result
            
        except Exception as e:
            print(f"💥 Chat failed: {e}")
            result["error"] = str(e)
            return result
    
    def find_spanish_phrases(self, text: str) -> list:
        """Find Spanish phrases Elena uses"""
        spanish_indicators = [
            "¡Hola", "¡Ay", "¡Increíble", "¡Qué", "Sí", "por favor", 
            "gracias", "de nada", "marinero", "océano", "¡"
        ]
        return [phrase for phrase in spanish_indicators if phrase.lower() in text.lower() or phrase in text]
    
    def find_ocean_emojis(self, text: str) -> list:
        """Find ocean-themed emojis"""
        ocean_emojis = ["🌊", "💙", "🐠", "🐬", "🦑", "🌺", "🏝️", "⚓"]
        return [emoji for emoji in ocean_emojis if emoji in text]
    
    def find_marine_terms(self, text: str) -> list:
        """Find marine biology terms"""
        marine_terms = [
            "ocean", "marine", "coral", "reef", "diving", "underwater", 
            "species", "ecosystem", "sea", "water", "fish", "biology"
        ]
        return [term for term in marine_terms if term.lower() in text.lower()]
    
    def find_enthusiasm_markers(self, text: str) -> list:
        """Find enthusiasm and passion markers"""
        enthusiasm_markers = [
            "amazing", "incredible", "fascinating", "wonderful", "love", 
            "passion", "excited", "beautiful", "fantastic"
        ]
        return [marker for marker in enthusiasm_markers if marker.lower() in text.lower()]

async def run_personality_chat_simulation():
    """Run Elena personality chat simulation"""
    print("🎭 Elena Discord Personality Simulator")
    print("=" * 70)
    print("Testing Elena's personality in Discord-like conversations")
    print("=" * 70)
    
    elena = ElenaPersonalitySimulator()
    await elena.initialize_systems()
    
    # Conversation scenarios testing all personality aspects
    chat_scenarios = [
        "¡Hola Elena! How are you today?",
        "I just saw the most amazing dolphins jumping in the ocean!",
        "I'm feeling sad about coral bleaching... what can we do?", 
        "Tell me about bioluminescence in deep sea creatures",
        "What's your favorite thing about being a marine biologist?",
        "Thank you for sharing your passion for the ocean with me!"
    ]
    
    results = []
    
    for i, message in enumerate(chat_scenarios, 1):
        print(f"\n🎬 Chat {i}/6")
        print("=" * 40)
        
        result = await elena.chat_with_elena(message)
        results.append(result)
        
        # Brief pause between messages
        await asyncio.sleep(0.5)
    
    # Summary Analysis
    print("\n" + "=" * 70)
    print("📊 ELENA PERSONALITY ANALYSIS")
    print("=" * 70)
    
    successful_chats = sum(1 for r in results if r["success"])
    total_spanish = sum(len(r["spanish_phrases"]) for r in results)
    total_emojis = sum(len(r["ocean_emojis"]) for r in results)
    total_marine_terms = sum(len(r["marine_terms"]) for r in results)
    total_enthusiasm = sum(len(r["enthusiasm_markers"]) for r in results)
    avg_processing = sum(r["processing_time_ms"] for r in results) / len(results)
    
    print(f"✅ Successful conversations: {successful_chats}/{len(results)}")
    print(f"🇪🇸 Spanish phrases detected: {total_spanish}")
    print(f"🌊 Ocean emojis used: {total_emojis}")  
    print(f"🐠 Marine biology terms: {total_marine_terms}")
    print(f"✨ Enthusiasm markers: {total_enthusiasm}")
    print(f"⏱️  Average response time: {avg_processing:.1f}ms")
    
    print(f"\n📈 Individual Chat Results:")
    for i, result in enumerate(results, 1):
        status = "✅" if result["success"] else "❌"
        emotion = result["emotion_detected"]
        spanish = len(result["spanish_phrases"])
        emojis = len(result["ocean_emojis"])
        marine = len(result["marine_terms"])
        enthusiasm = len(result["enthusiasm_markers"])
        
        print(f"{status} Chat {i}: {emotion} | Spanish:{spanish} Emojis:{emojis} Marine:{marine} Enthusiasm:{enthusiasm}")
        
        if result.get("elena_response"):
            response_preview = result["elena_response"][:80] + "..." if len(result["elena_response"]) > 80 else result["elena_response"]
            print(f"   '{response_preview}'")
    
    # Personality Score
    personality_score = (total_spanish > 0) + (total_emojis > 0) + (total_marine_terms > 2) + (total_enthusiasm > 1)
    max_score = 4
    
    print(f"\n🎭 Elena Personality Score: {personality_score}/{max_score}")
    
    if personality_score == max_score and successful_chats == len(results):
        print("🎉 Perfect! Elena's personality is fully working in Discord simulation!")
        success = True
    elif personality_score >= 3:
        print("👍 Good! Elena's personality is mostly working")  
        success = True
    else:
        print("⚠️  Elena's personality needs attention")
        success = False
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"elena_personality_chat_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump({
            "simulation_time": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "successful_chats": successful_chats,
                "total_spanish": total_spanish,
                "total_emojis": total_emojis,
                "total_marine_terms": total_marine_terms,
                "total_enthusiasm": total_enthusiasm,
                "avg_processing_ms": avg_processing,
                "personality_score": personality_score,
                "max_score": max_score
            }
        }, f, indent=2)
    
    print(f"📋 Report saved: {report_file}")
    return success

if __name__ == "__main__":
    success = asyncio.run(run_personality_chat_simulation())
    exit(0 if success else 1)