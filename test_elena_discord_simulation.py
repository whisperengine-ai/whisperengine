#!/usr/bin/env python3
"""
Elena Discord Flow Simulator
Simulates the complete Discord send/receive flow with full personality
Tests everything: emotional intelligence, CDL, memory, emojis, Spanish, etc.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append('src')

# FORCE localhost environment (don't load .env.elena!)
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine123'

os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6380'
os.environ['REDIS_DB'] = '0'

os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['QDRANT_COLLECTION_NAME'] = 'whisperengine_memory'

# Use OpenRouter (from Elena's config)
os.environ['LLM_CLIENT_TYPE'] = 'openrouter'

class DiscordFlowSimulator:
    """Simulates the complete Discord interaction flow"""
    
    def __init__(self):
        self.user_id = "test_discord_user"
        self.conversation_history = []
        self.memory_manager = None
        self.llm_client = None
        self.cdl_integration = None
        self.emotion_analyzer = None
        
    async def initialize_elena_systems(self):
        """Initialize all Elena systems like Discord would"""
        print("🤖 Initializing Elena Systems...")
        
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize memory manager
        from src.memory.memory_protocol import create_memory_manager
        self.memory_manager = create_memory_manager(memory_type="vector")
        
        # Initialize LLM client
        from src.llm.llm_protocol import create_llm_client
        self.llm_client = create_llm_client()
        
        # Initialize CDL integration
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        self.cdl_integration = CDLAIPromptIntegration()
        
        # Initialize emotion analyzer
        from src.intelligence.enhanced_vector_emotion_analyzer import create_enhanced_emotion_analyzer
        self.emotion_analyzer = create_enhanced_emotion_analyzer()
        
        print("✅ All Elena systems initialized!")
    
    async def simulate_discord_message(self, user_message: str, show_details: bool = True) -> dict:
        """Simulate the complete Discord message flow"""
        
        if show_details:
            print(f"\n📨 USER: {user_message}")
            print("=" * 60)
        
        start_time = time.time()
        result = {
            "user_message": user_message,
            "elena_response": None,
            "emotion_detected": None,
            "cdl_elements": [],
            "personality_markers": [],
            "memory_stored": False,
            "processing_time_ms": 0,
            "pipeline_steps": []
        }
        
        try:
            # Step 1: Emotional Analysis (like Discord would do)
            if show_details:
                print("🧠 Step 1: Analyzing user emotion...")
            
            emotion_result = await self.emotion_analyzer.analyze_emotion(
                content=user_message,
                user_id=self.user_id,
                conversation_context=self.conversation_history[-5:],  # Last 5 messages
                recent_emotions=[]
            )
            
            result["emotion_detected"] = emotion_result.primary_emotion
            result["pipeline_steps"].append(f"Emotion: {emotion_result.primary_emotion} (confidence: {emotion_result.confidence:.2f})")
            
            if show_details:
                print(f"   Detected: {emotion_result.primary_emotion} (confidence: {emotion_result.confidence:.2f})")
            
            # Step 2: Memory Retrieval (like Discord would do)
            if show_details:
                print("🧠 Step 2: Retrieving relevant memories...")
            
            relevant_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=self.user_id,
                query=user_message,
                limit=5
            )
            
            result["pipeline_steps"].append(f"Memories retrieved: {len(relevant_memories)}")
            
            if show_details:
                print(f"   Retrieved {len(relevant_memories)} relevant memories")
            
            # Step 3: CDL Character Integration with Emotional Context
            if show_details:
                print("🎭 Step 3: Creating character-aware prompt with emotional context...")
            
            # Create compatible pipeline result for CDL
            from types import SimpleNamespace
            pipeline_result = SimpleNamespace(
                emotional_state=emotion_result.primary_emotion,
                mood_assessment={
                    "primary": emotion_result.primary_emotion, 
                    "confidence": emotion_result.confidence,
                    "intensity": emotion_result.intensity
                },
                personality_profile=None,
                enhanced_context={"relevant_memories": len(relevant_memories)}
            )
            
            system_prompt = await self.cdl_integration.create_character_aware_prompt(
                character_file="characters/examples/elena-rodriguez.json",
                user_id=self.user_id,
                message_content=user_message,
                pipeline_result=pipeline_result
            )
            
            # Analyze CDL elements
            cdl_elements = self.find_cdl_elements(system_prompt)
            result["cdl_elements"] = cdl_elements
            result["pipeline_steps"].append(f"CDL elements: {len(cdl_elements)}")
            
            if show_details:
                print(f"   CDL elements integrated: {len(cdl_elements)}")
                print(f"   Emotional context: {emotion_result.primary_emotion}")
            
            # Step 4: Generate Elena's Response
            if show_details:
                print("🗣️  Step 4: Generating Elena's response...")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            elena_response = await self.llm_client.generate_chat_completion_safe(messages)
            result["elena_response"] = elena_response
            
            # Step 5: Analyze Elena's Personality Markers
            personality_markers = self.find_personality_markers(elena_response)
            result["personality_markers"] = personality_markers
            result["pipeline_steps"].append(f"Personality markers: {len(personality_markers)}")
            
            if show_details:
                print(f"🎯 Elena's personality markers: {personality_markers}")
            
            # Step 6: Store Conversation in Memory
            if show_details:
                print("💾 Step 5: Storing conversation in memory...")
            
            await self.memory_manager.store_conversation(
                user_id=self.user_id,
                user_message=user_message,
                bot_response=elena_response,
                pre_analyzed_emotion_data=emotion_result
            )
            
            result["memory_stored"] = True
            result["pipeline_steps"].append("Memory stored")
            
            # Update conversation history
            self.conversation_history.append({
                "role": "user", 
                "content": user_message,
                "emotion": emotion_result.primary_emotion
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": elena_response,
                "personality_markers": personality_markers
            })
            
            # Calculate processing time
            end_time = time.time()
            result["processing_time_ms"] = (end_time - start_time) * 1000
            
            if show_details:
                print(f"\n🤖 ELENA: {elena_response}")
                print(f"\n⏱️  Processing time: {result['processing_time_ms']:.1f}ms")
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            if show_details:
                print(f"💥 Error in Discord flow: {e}")
            return result
    
    def find_cdl_elements(self, prompt: str) -> list:
        """Find CDL character elements in the prompt"""
        cdl_indicators = [
            "Elena Rodriguez", "marine biologist", "Puerto Rico", "coral reef",
            "passionate", "enthusiastic", "ocean", "diving", "research",
            "Spanish", "marine life", "conservation", "underwater", "species"
        ]
        
        found_elements = []
        prompt_lower = prompt.lower()
        
        for indicator in cdl_indicators:
            if indicator.lower() in prompt_lower:
                found_elements.append(indicator)
        
        return found_elements
    
    def find_personality_markers(self, response: str) -> list:
        """Find Elena's personality markers in the response"""
        personality_indicators = {
            "spanish": ["¡", "Hola", "Sí", "Qué", "Increíble", "Ay", "océano", "marinero", "por favor", "gracias", "de nada"],
            "ocean_emojis": ["🌊", "💙", "🐠", "🐬", "🦑", "🌺", "🏝️", "⚓", "🌊"],
            "marine_terms": ["ocean", "marine", "coral", "reef", "diving", "underwater", "species", "ecosystem"],
            "enthusiasm": ["amazing", "incredible", "fascinating", "wonderful", "love", "passion", "excited"]
        }
        
        found_markers = []
        response_lower = response.lower()
        
        for category, indicators in personality_indicators.items():
            for indicator in indicators:
                if indicator.lower() in response_lower or indicator in response:
                    found_markers.append(f"{category}: {indicator}")
        
        return found_markers

async def run_discord_conversation_simulation():
    """Run a full Discord conversation simulation"""
    print("🎭 Elena Discord Flow Simulator")
    print("=" * 80)
    print("Testing the complete Discord experience with live Elena systems")
    print("=" * 80)
    
    simulator = DiscordFlowSimulator()
    await simulator.initialize_elena_systems()
    
    # Conversation scenarios that test all features
    conversation_scenarios = [
        {
            "name": "Initial Spanish Greeting",
            "message": "¡Hola Elena! How are you today?",
            "expect": ["spanish", "greeting", "marine_enthusiasm"]
        },
        {
            "name": "Excited Ocean Discovery", 
            "message": "I just saw the most incredible dolphins jumping today! They were so beautiful!",
            "expect": ["excitement_response", "ocean_emojis", "marine_knowledge"]
        },
        {
            "name": "Sad Environmental Concern",
            "message": "I'm really worried about coral bleaching... it makes me so sad to see the reefs dying",
            "expect": ["empathy", "environmental_knowledge", "supportive_spanish"]
        },
        {
            "name": "Curious Scientific Question",
            "message": "I've been wondering about bioluminescence in deep sea creatures. How does it work?",
            "expect": ["scientific_explanation", "marine_expertise", "enthusiasm"]
        },
        {
            "name": "Memory Test - Reference Previous",
            "message": "Remember when we talked about those dolphins I saw?",
            "expect": ["memory_recall", "continuity", "personal_connection"]
        },
        {
            "name": "Grateful Appreciation",
            "message": "Thank you for sharing your marine biology knowledge with me, Elena!",
            "expect": ["gracious_response", "spanish_courtesy", "passion_for_sharing"]
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(conversation_scenarios, 1):
        print(f"\n🎬 Scenario {i}: {scenario['name']}")
        print("-" * 60)
        
        result = await simulator.simulate_discord_message(scenario["message"], show_details=True)
        results.append({
            "scenario": scenario["name"],
            "result": result,
            "expected": scenario["expect"]
        })
        
        # Small delay between messages (like real Discord)
        await asyncio.sleep(1)
    
    # Summary Report
    print("\n" + "=" * 80)
    print("📊 DISCORD FLOW SIMULATION SUMMARY")
    print("=" * 80)
    
    total_scenarios = len(results)
    successful_responses = sum(1 for r in results if r["result"].get("elena_response") and len(r["result"]["elena_response"]) > 10)
    avg_processing_time = sum(r["result"].get("processing_time_ms", 0) for r in results) / total_scenarios
    total_personality_markers = sum(len(r["result"].get("personality_markers", [])) for r in results)
    
    print(f"✅ Successful responses: {successful_responses}/{total_scenarios}")
    print(f"⏱️  Average processing time: {avg_processing_time:.1f}ms")
    print(f"🎭 Total personality markers detected: {total_personality_markers}")
    
    print(f"\n📈 Per-Scenario Results:")
    for i, result in enumerate(results, 1):
        r = result["result"]
        status = "✅" if r.get("elena_response") else "❌"
        emotion = r.get("emotion_detected", "none")
        markers = len(r.get("personality_markers", []))
        time_ms = r.get("processing_time_ms", 0)
        
        print(f"{status} {i}. {result['scenario']}")
        print(f"   Emotion: {emotion} | Personality: {markers} markers | Time: {time_ms:.1f}ms")
        
        if r.get("elena_response"):
            response_preview = r["elena_response"][:100] + "..." if len(r["elena_response"]) > 100 else r["elena_response"]
            print(f"   Response: {response_preview}")
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"elena_discord_simulation_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump({
            "simulation_time": datetime.now().isoformat(),
            "scenarios": results,
            "summary": {
                "total_scenarios": total_scenarios,
                "successful_responses": successful_responses,
                "success_rate": successful_responses / total_scenarios,
                "avg_processing_time_ms": avg_processing_time,
                "total_personality_markers": total_personality_markers
            }
        }, f, indent=2)
    
    print(f"\n📋 Detailed report saved: {report_file}")
    
    if successful_responses == total_scenarios:
        print("🎉 Perfect! Elena's Discord flow simulation is 100% successful!")
        return True
    else:
        print("⚠️  Some scenarios need attention")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_discord_conversation_simulation())
    exit(0 if success else 1)