#!/usr/bin/env python3
"""
Elena Personality & Emotional Intelligence Test
Tests the core features that matter: personality and emotional flow
Runs locally with localhost configs to avoid container dependency
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path
sys.path.append('src')

# Set up localhost environment for local testing (MUST be set BEFORE any imports)
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'  # Multi-bot port
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine123'

os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6380'     # Multi-bot port
os.environ['REDIS_PASSWORD'] = ''

os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'    # Multi-bot port

# Override any container hostnames that might be in .env.elena
os.environ['MEMORY_QDRANT_HOST'] = 'localhost'
os.environ['MEMORY_QDRANT_PORT'] = '6334'
os.environ['MEMORY_POSTGRESQL_HOST'] = 'localhost'
os.environ['MEMORY_POSTGRESQL_PORT'] = '5433'
os.environ['MEMORY_REDIS_HOST'] = 'localhost'
os.environ['MEMORY_REDIS_PORT'] = '6380'

class ElenaPersonalityTester:
    """
    Elena Automated Personality & Emotional Intelligence Tester
    Focused on the core features that matter: personality and emotional flow
    """
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.elena = None
        self.memory_manager = None
        self.llm_client = None
        
        # Personality validation patterns
        self.spanish_phrases = [
            "¡Hola", "¡Ay", "¡Increíble", "¡Qué", 
            "Sí", "Por favor", "Gracias", "marinero", "océano"
        ]
        
        self.ocean_emojis = ["🌊", "💙", "🐠", "🐬", "🦑", "🌺", "🏝️", "⚓"]
        
        self.marine_terms = [
            "ocean", "marine", "sea", "coral", "reef", "fish", 
            "underwater", "diving", "species", "ecosystem", "marine life"
        ]
    
    def _setup_logger(self) -> logging.Logger:
        """Set up focused logging for personality tests"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('ElenaPersonalityTester')
    
    async def run_personality_test_suite(self) -> Dict:
        """Main test runner focused on personality and emotional intelligence"""
        self.logger.info("🧪 Starting Elena Personality & Emotional Intelligence Test")
        self.logger.info(f"📅 {datetime.now().isoformat()}")
        self.logger.info("🎯 Focus: Personality and emotional intelligence flow")
        
        results = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "branch": self._get_git_branch(),
                "focus": "personality_and_emotional_intelligence"
            },
            "tests": {}
        }
        
        # Core personality tests
        test_methods = [
            ("infrastructure_check", self.test_infrastructure),
            ("cdl_character_loading", self.test_cdl_character_system),
            ("spanish_integration", self.test_spanish_integration),
            ("ocean_emoji_usage", self.test_ocean_emoji_usage),
            ("marine_biology_personality", self.test_marine_biology_personality),
            ("emotional_intelligence_flow", self.test_emotional_intelligence),
            ("memory_personality_consistency", self.test_memory_personality),
            ("conversation_personality_flow", self.test_conversation_flow)
        ]
        
        for test_name, test_method in test_methods:
            try:
                self.logger.info(f"🔍 Running: {test_name}")
                success, details = await test_method()
                results["tests"][test_name] = {
                    "success": success,
                    "details": details,
                    "timestamp": datetime.now().isoformat()
                }
                
                if success:
                    self.logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.logger.error(f"❌ {test_name}: FAILED - {details.get('error', 'Unknown error')}")
                    
            except Exception as e:
                self.logger.error(f"💥 {test_name}: EXCEPTION - {str(e)}")
                results["tests"][test_name] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Summary
        passed = sum(1 for test in results["tests"].values() if test["success"])
        total = len(results["tests"])
        results["summary"] = {
            "passed": passed,
            "total": total,
            "success_rate": passed / total if total > 0 else 0,
            "overall_success": passed == total
        }
        
        self.logger.info(f"📊 Test Summary: {passed}/{total} passed ({results['summary']['success_rate']:.1%})")
        return results
    
    def _get_git_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            return result.stdout.strip()
        except:
            return "unknown"
    
    async def test_infrastructure(self) -> Tuple[bool, Dict]:
        """Test basic infrastructure connectivity"""
        details = {"checks": []}
        
        # Test database connectivity
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.environ['POSTGRES_HOST'],
                port=os.environ['POSTGRES_PORT'],
                database='whisperengine',
                user='whisperengine',
                password='whisperengine123'
            )
            conn.close()
            details["checks"].append({"postgres": "connected"})
        except Exception as e:
            details["checks"].append({"postgres": f"failed: {e}"})
            return False, details
        
        # Test Redis connectivity  
        try:
            import redis
            r = redis.Redis(
                host=os.environ['REDIS_HOST'],
                port=int(os.environ['REDIS_PORT']),
                decode_responses=True
            )
            r.ping()
            details["checks"].append({"redis": "connected"})
        except Exception as e:
            details["checks"].append({"redis": f"failed: {e}"})
            return False, details
        
        # Test Qdrant connectivity
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(
                host=os.environ['QDRANT_HOST'],
                port=int(os.environ['QDRANT_PORT'])
            )
            collections = client.get_collections()
            details["checks"].append({"qdrant": f"connected, {len(collections.collections)} collections"})
        except Exception as e:
            details["checks"].append({"qdrant": f"failed: {e}"})
            return False, details
            
        return True, details
    
    async def test_cdl_character_system(self) -> Tuple[bool, Dict]:
        """Test CDL character system loading"""
        details = {"character_file": None, "personality": None}
        
        try:
            from src.characters.cdl.parser import CDLParser
            
            # Check Elena character file exists
            elena_file = Path("characters/examples/elena-rodriguez.json")
            if not elena_file.exists():
                return False, {"error": "Elena character file not found"}
            
            # Parse character
            parser = CDLParser()
            character = parser.parse_character_file(str(elena_file))
            
            details["character_file"] = str(elena_file)
            details["personality"] = {
                "name": character.basic_info.name,
                "occupation": character.basic_info.occupation,
                "personality_traits": len(character.personality.personality_traits),
                "communication_style": len(character.personality.communication_style),
                "values": len(character.personality.values)
            }
            
            # Validate marine biologist identity
            if "marine" not in character.basic_info.occupation.lower():
                return False, {"error": "Elena should be marine biologist"}
            
            return True, details
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def test_spanish_integration(self) -> Tuple[bool, Dict]:
        """Test Spanish phrase integration in responses"""
        details = {"test_messages": [], "spanish_detected": []}
        
        try:
            # Initialize Elena
            await self._initialize_elena()
            
            # Test messages that should trigger Spanish responses
            test_messages = [
                "Hola Elena!",
                "How are you today?",
                "Tell me about yourself",
                "What do you love most about the ocean?"
            ]
            
            spanish_count = 0
            
            for message in test_messages:
                try:
                    response = await self._get_elena_response(message)
                    has_spanish = any(phrase in response for phrase in self.spanish_phrases)
                    
                    details["test_messages"].append({
                        "message": message,
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "has_spanish": has_spanish
                    })
                    
                    if has_spanish:
                        spanish_count += 1
                        spanish_found = [phrase for phrase in self.spanish_phrases if phrase in response]
                        details["spanish_detected"].extend(spanish_found)
                        
                except Exception as e:
                    details["test_messages"].append({
                        "message": message,
                        "error": str(e)
                    })
            
            # Should have Spanish in at least some responses
            success = spanish_count > 0
            details["spanish_responses"] = spanish_count
            details["total_responses"] = len(test_messages)
            
            return success, details
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def test_ocean_emoji_usage(self) -> Tuple[bool, Dict]:
        """Test ocean emoji usage in responses"""
        details = {"emoji_usage": [], "messages_tested": []}
        
        try:
            await self._initialize_elena()
            
            # Ocean-themed messages
            ocean_messages = [
                "Tell me about the ocean!",
                "What's your favorite sea creature?",
                "Have you been diving recently?",
                "The coral reefs are beautiful!"
            ]
            
            emoji_count = 0
            
            for message in ocean_messages:
                try:
                    response = await self._get_elena_response(message)
                    found_emojis = [emoji for emoji in self.ocean_emojis if emoji in response]
                    
                    details["messages_tested"].append({
                        "message": message,
                        "response": response[:150] + "..." if len(response) > 150 else response,
                        "emojis_found": found_emojis
                    })
                    
                    if found_emojis:
                        emoji_count += 1
                        details["emoji_usage"].extend(found_emojis)
                        
                except Exception as e:
                    details["messages_tested"].append({
                        "message": message,
                        "error": str(e)
                    })
            
            details["emoji_responses"] = emoji_count
            details["total_messages"] = len(ocean_messages)
            
            # Should use emojis in ocean-themed conversations
            return emoji_count > 0, details
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def test_marine_biology_personality(self) -> Tuple[bool, Dict]:
        """Test marine biology knowledge and enthusiasm"""
        details = {"knowledge_tests": []}
        
        try:
            await self._initialize_elena()
            
            marine_questions = [
                "What's the difference between a reef and a seamount?",
                "Tell me about bioluminescence in marine life",
                "What threatens coral reefs today?",
                "What's your research focus?"
            ]
            
            knowledge_score = 0
            
            for question in marine_questions:
                try:
                    response = await self._get_elena_response(question)
                    
                    # Check for marine biology terms
                    marine_terms_found = [term for term in self.marine_terms 
                                        if term.lower() in response.lower()]
                    
                    # Check for scientific enthusiasm markers
                    enthusiasm_markers = ["fascinating", "amazing", "incredible", "love", "passion"]
                    enthusiasm_found = [marker for marker in enthusiasm_markers 
                                      if marker.lower() in response.lower()]
                    
                    has_knowledge = len(marine_terms_found) > 0
                    has_enthusiasm = len(enthusiasm_found) > 0
                    
                    details["knowledge_tests"].append({
                        "question": question,
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "marine_terms": marine_terms_found,
                        "enthusiasm_markers": enthusiasm_found,
                        "has_knowledge": has_knowledge,
                        "has_enthusiasm": has_enthusiasm
                    })
                    
                    if has_knowledge and has_enthusiasm:
                        knowledge_score += 1
                        
                except Exception as e:
                    details["knowledge_tests"].append({
                        "question": question,
                        "error": str(e)
                    })
            
            details["knowledge_score"] = knowledge_score
            details["total_questions"] = len(marine_questions)
            
            # Should demonstrate marine biology knowledge and enthusiasm
            return knowledge_score >= len(marine_questions) // 2, details
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def test_emotional_intelligence(self) -> Tuple[bool, Dict]:
        """Test emotional intelligence flow and responsiveness"""
        details = {"emotional_tests": []}
        
        try:
            await self._initialize_elena()
            
            # Different emotional contexts
            emotional_scenarios = [
                ("excited", "I just saw the most amazing dolphins today!"),
                ("sad", "I'm feeling down about the state of our oceans..."),
                ("curious", "I've been wondering about something..."),
                ("grateful", "Thank you for always listening to me")
            ]
            
            emotional_responses = 0
            
            for emotion, message in emotional_scenarios:
                try:
                    response = await self._get_elena_response(message)
                    
                    # Check for emotional responsiveness
                    emotional_indicators = {
                        "excited": ["¡", "amazing", "wonderful", "fantastic", "incredible"],
                        "sad": ["understand", "sorry", "together", "care", "support"],
                        "curious": ["interesting", "wonder", "explore", "discover"],
                        "grateful": ["welcome", "happy", "glad", "friendship"]
                    }
                    
                    relevant_indicators = emotional_indicators.get(emotion, [])
                    found_indicators = [ind for ind in relevant_indicators 
                                     if ind.lower() in response.lower()]
                    
                    is_responsive = len(found_indicators) > 0
                    
                    details["emotional_tests"].append({
                        "emotion": emotion,
                        "message": message,
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "emotional_indicators": found_indicators,
                        "is_responsive": is_responsive
                    })
                    
                    if is_responsive:
                        emotional_responses += 1
                        
                except Exception as e:
                    details["emotional_tests"].append({
                        "emotion": emotion,
                        "message": message,
                        "error": str(e)
                    })
            
            details["responsive_emotions"] = emotional_responses
            details["total_scenarios"] = len(emotional_scenarios)
            
            # Should respond emotionally appropriately to most scenarios
            return emotional_responses >= len(emotional_scenarios) // 2, details
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def test_memory_personality(self) -> Tuple[bool, Dict]:
        """Test memory system integration with personality"""
        details = {"memory_tests": []}
        
        try:
            await self._initialize_elena()
            
            # Store a conversation with personality
            test_user = "personality_test_user"
            initial_message = "Hola Elena! I'm new to marine biology"
            
            # First interaction
            first_response = await self._get_elena_response(initial_message, test_user)
            
            # Wait a moment for memory storage
            await asyncio.sleep(1)
            
            # Follow-up message that should reference personality/memory
            followup_message = "What did we talk about before?"
            followup_response = await self._get_elena_response(followup_message, test_user)
            
            details["memory_tests"].append({
                "initial_message": initial_message,
                "initial_response": first_response[:150] + "..." if len(first_response) > 150 else first_response,
                "followup_message": followup_message,
                "followup_response": followup_response[:150] + "..." if len(followup_response) > 150 else followup_response
            })
            
            # Check if personality is consistent across interactions
            has_spanish_first = any(phrase in first_response for phrase in self.spanish_phrases)
            has_spanish_second = any(phrase in followup_response for phrase in self.spanish_phrases)
            
            has_marine_context = any(term in followup_response.lower() for term in ["marine", "ocean", "biology"])
            
            details["personality_consistency"] = {
                "spanish_first": has_spanish_first,
                "spanish_second": has_spanish_second,
                "marine_context_recalled": has_marine_context
            }
            
            # Success if personality is maintained and context is recalled
            return (has_spanish_first or has_spanish_second) and has_marine_context, details
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def test_conversation_flow(self) -> Tuple[bool, Dict]:
        """Test natural conversation flow with personality"""
        details = {"conversation": []}
        
        try:
            await self._initialize_elena()
            
            # Multi-turn conversation
            conversation_flow = [
                "Hi Elena!",
                "Tell me about your work",
                "That sounds fascinating! What's your favorite discovery?",
                "I'd love to learn more about that"
            ]
            
            test_user = "conversation_test_user"
            personality_maintained = 0
            
            for i, message in enumerate(conversation_flow):
                try:
                    response = await self._get_elena_response(message, test_user)
                    
                    # Check personality markers
                    has_spanish = any(phrase in response for phrase in self.spanish_phrases)
                    has_emojis = any(emoji in response for emoji in self.ocean_emojis)
                    has_marine_terms = any(term in response.lower() for term in self.marine_terms)
                    
                    personality_score = sum([has_spanish, has_emojis, has_marine_terms])
                    
                    details["conversation"].append({
                        "turn": i + 1,
                        "message": message,
                        "response": response[:150] + "..." if len(response) > 150 else response,
                        "personality_markers": {
                            "spanish": has_spanish,
                            "emojis": has_emojis,
                            "marine_terms": has_marine_terms
                        },
                        "personality_score": personality_score
                    })
                    
                    if personality_score > 0:
                        personality_maintained += 1
                    
                    # Small delay between messages
                    await asyncio.sleep(0.5)
                        
                except Exception as e:
                    details["conversation"].append({
                        "turn": i + 1,
                        "message": message,
                        "error": str(e)
                    })
            
            details["personality_maintained_turns"] = personality_maintained
            details["total_turns"] = len(conversation_flow)
            
            # Should maintain personality across conversation
            return personality_maintained >= len(conversation_flow) // 2, details
            
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _initialize_elena(self):
        """Initialize Elena components for testing"""
        if self.elena is not None:
            return
        
        try:
            from dotenv import load_dotenv
            load_dotenv('.env.elena')
            
            # Initialize memory manager
            from src.memory.memory_protocol import create_memory_manager
            self.memory_manager = create_memory_manager(memory_type="vector")
            
            # Initialize LLM client
            from src.llm.llm_protocol import create_llm_client
            self.llm_client = create_llm_client(llm_client_type="openai")
            
            # Initialize CDL integration
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            self.cdl_integration = CDLAIPromptIntegration()
            
            self.logger.info("✅ Elena components initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Elena: {e}")
            raise
    
    async def _get_elena_response(self, message: str, user_id: str = "test_user") -> str:
        """Get response from Elena with full personality"""
        try:
            # Get character-aware prompt
            system_prompt = await self.cdl_integration.create_character_aware_prompt(
                character_file="characters/examples/elena-rodriguez.json",
                user_id=user_id,
                message_content=message
            )
            
            # Generate response
            response = await self.llm_client.generate_response(
                user_message=message,
                system_prompt=system_prompt
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting Elena response: {e}")
            raise

    async def save_test_report(self, results: Dict):
        """Save test results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"elena_personality_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"📋 Test report saved: {report_file}")
        return report_file

async def main():
    """Run Elena personality test suite"""
    tester = ElenaPersonalityTester()
    
    try:
        results = await tester.run_personality_test_suite()
        report_file = await tester.save_test_report(results)
        
        # Print summary
        summary = results["summary"]
        print(f"\n🎯 ELENA PERSONALITY TEST RESULTS")
        print(f"{'='*50}")
        print(f"✅ Passed: {summary['passed']}/{summary['total']}")
        print(f"📊 Success Rate: {summary['success_rate']:.1%}")
        print(f"🎯 Overall: {'✅ SUCCESS' if summary['overall_success'] else '❌ FAILURES'}")
        print(f"📋 Report: {report_file}")
        
        if not summary['overall_success']:
            print(f"\n❌ FAILED TESTS:")
            for test_name, result in results["tests"].items():
                if not result["success"]:
                    error = result.get("error", result.get("details", {}).get("error", "Unknown"))
                    print(f"   - {test_name}: {error}")
        
        return summary['overall_success']
        
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)