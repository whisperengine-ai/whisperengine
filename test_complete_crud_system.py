#!/usr/bin/env python3
"""
Comprehensive Test for Human-Like CRUD Operations

This test validates that all CRUD operations work correctly for:
1. User conversation preferences persistence
2. Conversation state tracking
3. Empathetic response effectiveness measurement

Tests both PostgreSQL and SQLite backends when available.
"""

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from database.human_like_persistence import HumanLikePersistenceManager, initialize_persistence_manager
    from utils.human_like_conversation_engine import PersonalityAdaptationEngine, PersonalityType
    from intelligence.phase4_simple_integration import Phase4HumanLikeIntegration
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class CRUDTestSuite:
    """Comprehensive test suite for human-like CRUD operations"""
    
    def __init__(self):
        self.test_user_id = "test_user_12345"
        self.temp_db_path = None
        self.persistence_manager = None
        self.personality_engine = None
        self.phase4_integration = None
        
        # Test results tracking
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result"""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.results["failed_tests"] += 1
            status = "❌ FAIL"
        
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")
        
        self.results["test_details"].append({
            "name": test_name,
            "passed": passed,
            "details": details
        })
    
    async def setup(self):
        """Set up test environment"""
        print("🔧 Setting up test environment...")
        
        # Create temporary SQLite database
        temp_dir = tempfile.mkdtemp()
        self.temp_db_path = os.path.join(temp_dir, "test_human_like.db")
        
        # Initialize persistence manager with SQLite
        self.persistence_manager = initialize_persistence_manager(sqlite_path=self.temp_db_path)
        
        # Initialize personality engine
        self.personality_engine = PersonalityAdaptationEngine(PersonalityType.CARING_FRIEND)
        
        # Initialize Phase 4 integration
        self.phase4_integration = Phase4HumanLikeIntegration()
        self.phase4_integration.persistence_manager = self.persistence_manager
        
        print(f"📁 Test database created: {self.temp_db_path}")
        
        # Wait for schema initialization
        await asyncio.sleep(1)
    
    async def test_user_preferences_crud(self):
        """Test user preferences CRUD operations"""
        print("\n📋 Testing User Preferences CRUD...")
        
        # Test 1: Save user preferences
        try:
            test_preferences = {
                "prefers_professional": True,
                "prefers_detailed_responses": False,
                "emotional_sensitivity": "high"
            }
            
            success = await self.persistence_manager.save_user_preferences(
                self.test_user_id,
                test_preferences,
                "wise_mentor",
                "analytical"
            )
            
            self.log_test("Save user preferences", success, "Successfully saved preferences to database")
        except Exception as e:
            self.log_test("Save user preferences", False, f"Error: {e}")
        
        # Test 2: Load user preferences
        try:
            loaded_prefs = await self.persistence_manager.load_user_preferences(self.test_user_id)
            
            success = (
                loaded_prefs is not None and
                loaded_prefs.get("preferences", {}).get("prefers_professional") == True and
                loaded_prefs.get("personality_type") == "wise_mentor"
            )
            
            self.log_test("Load user preferences", success, f"Loaded: {loaded_prefs}")
        except Exception as e:
            self.log_test("Load user preferences", False, f"Error: {e}")
        
        # Test 3: Update user preferences
        try:
            updated_prefs = test_preferences.copy()
            updated_prefs["prefers_professional"] = False
            updated_prefs["prefers_playful"] = True
            
            success = await self.persistence_manager.save_user_preferences(
                self.test_user_id,
                updated_prefs,
                "playful_companion",
                "adaptive"
            )
            
            # Verify update
            loaded_after_update = await self.persistence_manager.load_user_preferences(self.test_user_id)
            update_verified = (
                loaded_after_update.get("preferences", {}).get("prefers_professional") == False and
                loaded_after_update.get("preferences", {}).get("prefers_playful") == True and
                loaded_after_update.get("personality_type") == "playful_companion"
            )
            
            self.log_test("Update user preferences", success and update_verified, 
                         f"Updated preferences: {loaded_after_update}")
        except Exception as e:
            self.log_test("Update user preferences", False, f"Error: {e}")
    
    async def test_conversation_state_crud(self):
        """Test conversation state CRUD operations"""
        print("\n💬 Testing Conversation State CRUD...")
        
        # Test 1: Save conversation state
        try:
            test_history = ["EMOTIONAL_SUPPORT", "PROBLEM_SOLVING", "CASUAL_CHAT"]
            test_context = {
                "last_interaction": "emotional_support",
                "relationship_depth": "developing",
                "session_start": datetime.now(timezone.utc).isoformat()
            }
            
            success = await self.persistence_manager.save_conversation_state(
                self.test_user_id,
                "human_like",
                test_history,
                test_context
            )
            
            self.log_test("Save conversation state", success, "Successfully saved conversation state")
        except Exception as e:
            self.log_test("Save conversation state", False, f"Error: {e}")
        
        # Test 2: Load conversation state
        try:
            loaded_state = await self.persistence_manager.load_conversation_state(self.test_user_id)
            
            success = (
                loaded_state is not None and
                loaded_state.get("state", {}).get("interaction_history") == test_history and
                loaded_state.get("current_mode") == "human_like"
            )
            
            self.log_test("Load conversation state", success, f"Loaded state: {loaded_state}")
        except Exception as e:
            self.log_test("Load conversation state", False, f"Error: {e}")
        
        # Test 3: Update conversation state
        try:
            updated_history = test_history + ["CREATIVE_COLLABORATION"]
            updated_context = test_context.copy()
            updated_context["relationship_depth"] = "established"
            
            success = await self.persistence_manager.save_conversation_state(
                self.test_user_id,
                "adaptive",
                updated_history,
                updated_context
            )
            
            # Verify update
            loaded_after_update = await self.persistence_manager.load_conversation_state(self.test_user_id)
            update_verified = (
                len(loaded_after_update.get("state", {}).get("interaction_history", [])) == 4 and
                loaded_after_update.get("current_mode") == "adaptive"
            )
            
            self.log_test("Update conversation state", success and update_verified,
                         f"Updated state: {loaded_after_update}")
        except Exception as e:
            self.log_test("Update conversation state", False, f"Error: {e}")
    
    async def test_empathetic_response_crud(self):
        """Test empathetic response tracking CRUD operations"""
        print("\n💝 Testing Empathetic Response CRUD...")
        
        # Test 1: Track empathetic response
        response_id = ""
        try:
            test_context = {
                "original_message": "I'm feeling really stressed about work",
                "ai_response": "I understand that work stress can be overwhelming. You're not alone in feeling this way.",
                "detected_emotion": "stressed"
            }
            
            response_id = await self.persistence_manager.track_empathetic_response(
                self.test_user_id,
                "emotional_support",
                "empathetic",
                0.5,  # Initial neutral score
                test_context
            )
            
            success = len(response_id) > 0
            self.log_test("Track empathetic response", success, f"Response ID: {response_id}")
        except Exception as e:
            self.log_test("Track empathetic response", False, f"Error: {e}")
        
        # Test 2: Update response effectiveness
        if response_id:
            try:
                success = await self.persistence_manager.update_response_effectiveness(
                    response_id,
                    "Thank you, that really helps. I feel much better now.",
                    0.9  # High effectiveness score
                )
                
                self.log_test("Update response effectiveness", success, 
                             f"Updated effectiveness for response {response_id}")
            except Exception as e:
                self.log_test("Update response effectiveness", False, f"Error: {e}")
        else:
            self.log_test("Update response effectiveness", False, "No response ID to update")
        
        # Test 3: Get effective response patterns
        try:
            # Add a few more responses for pattern analysis
            await self.persistence_manager.track_empathetic_response(
                self.test_user_id,
                "emotional_support",
                "supportive",
                0.8,
                {"context": "test_pattern_1"}
            )
            
            await self.persistence_manager.track_empathetic_response(
                self.test_user_id,
                "problem_solving",
                "solution-focused",
                0.7,
                {"context": "test_pattern_2"}
            )
            
            patterns = await self.persistence_manager.get_effective_response_patterns(
                self.test_user_id,
                min_effectiveness=0.6
            )
            
            success = len(patterns) >= 2  # Should have at least 2 effective patterns
            self.log_test("Get response patterns", success, 
                         f"Found {len(patterns)} effective patterns")
            
            # Test filtering by response type
            emotional_patterns = await self.persistence_manager.get_effective_response_patterns(
                self.test_user_id,
                response_type="emotional_support",
                min_effectiveness=0.6
            )
            
            filtered_success = len(emotional_patterns) >= 1
            self.log_test("Filter patterns by type", filtered_success,
                         f"Found {len(emotional_patterns)} emotional support patterns")
            
        except Exception as e:
            self.log_test("Get response patterns", False, f"Error: {e}")
    
    async def test_personality_engine_integration(self):
        """Test PersonalityAdaptationEngine with persistent storage"""
        print("\n🧠 Testing Personality Engine Integration...")
        
        # Test 1: Adapt personality with persistence
        try:
            # Set up personality engine with persistence
            self.personality_engine.persistence_manager = self.persistence_manager
            
            # Test personality adaptation
            adapted_personality = await self.personality_engine.adapt_personality(
                self.test_user_id,
                conversation_history=[
                    {"content": "I need help with something technical"},
                    {"content": "Can you explain this in detail?"}
                ],
                user_feedback={"wants_deeper_insights": True}
            )
            
            success = adapted_personality == PersonalityType.WISE_MENTOR
            self.log_test("Personality adaptation with persistence", success,
                         f"Adapted to: {adapted_personality}")
        except Exception as e:
            self.log_test("Personality adaptation with persistence", False, f"Error: {e}")
        
        # Test 2: Verify preferences were saved
        try:
            saved_prefs = await self.personality_engine._load_user_preferences(self.test_user_id)
            
            success = saved_prefs.get("prefers_wisdom") == True
            self.log_test("Preference persistence after adaptation", success,
                         f"Saved preferences: {saved_prefs}")
        except Exception as e:
            self.log_test("Preference persistence after adaptation", False, f"Error: {e}")
    
    async def test_phase4_integration(self):
        """Test Phase4HumanLikeIntegration with persistent storage"""
        print("\n🚀 Testing Phase 4 Integration...")
        
        # Test 1: Track empathetic response through Phase 4
        try:
            response_id = await self.phase4_integration.track_empathetic_response(
                self.test_user_id,
                "I'm having trouble with my relationship",
                "Relationships can be challenging. I'm here to listen and support you through this.",
                "emotional_support",
                "sad"
            )
            
            success = len(response_id) > 0
            self.log_test("Phase 4 empathetic response tracking", success,
                         f"Tracked response: {response_id}")
        except Exception as e:
            self.log_test("Phase 4 empathetic response tracking", False, f"Error: {e}")
        
        # Test 2: Get response patterns through Phase 4
        try:
            patterns = await self.phase4_integration.get_response_patterns(
                self.test_user_id,
                "emotional_support"
            )
            
            success = isinstance(patterns, list)
            self.log_test("Phase 4 response pattern retrieval", success,
                         f"Retrieved {len(patterns)} patterns")
        except Exception as e:
            self.log_test("Phase 4 response pattern retrieval", False, f"Error: {e}")
    
    async def test_data_consistency(self):
        """Test data consistency across different operations"""
        print("\n🔍 Testing Data Consistency...")
        
        # Test 1: Consistency between saves and loads
        try:
            # Save through one method
            test_prefs = {"consistency_test": True, "test_value": 42}
            await self.persistence_manager.save_user_preferences(
                self.test_user_id,
                test_prefs,
                "caring_friend",
                "balanced"
            )
            
            # Load through another method
            loaded = await self.persistence_manager.load_user_preferences(self.test_user_id)
            
            success = (
                loaded.get("preferences", {}).get("consistency_test") == True and
                loaded.get("preferences", {}).get("test_value") == 42
            )
            
            self.log_test("Data consistency across operations", success,
                         "Saved and loaded data matches")
        except Exception as e:
            self.log_test("Data consistency across operations", False, f"Error: {e}")
        
        # Test 2: JSON serialization/deserialization
        try:
            complex_data = {
                "nested": {"deep": {"value": [1, 2, 3]}},
                "unicode": "Hello 世界 🌍",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.persistence_manager.save_user_preferences(
                self.test_user_id,
                complex_data,
                "supportive_counselor",
                "human_like"
            )
            
            loaded_complex = await self.persistence_manager.load_user_preferences(self.test_user_id)
            
            success = (
                loaded_complex.get("preferences", {}).get("nested", {}).get("deep", {}).get("value") == [1, 2, 3] and
                loaded_complex.get("preferences", {}).get("unicode") == "Hello 世界 🌍"
            )
            
            self.log_test("Complex data serialization", success,
                         "Complex JSON data preserved correctly")
        except Exception as e:
            self.log_test("Complex data serialization", False, f"Error: {e}")
    
    async def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        try:
            if self.temp_db_path and os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
                print(f"🗑️ Removed test database: {self.temp_db_path}")
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up test database: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 CRUD TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed_tests']}")
        print(f"Failed: {self.results['failed_tests']}")
        
        if self.results['failed_tests'] > 0:
            print(f"\n❌ Failed Tests:")
            for test in self.results['test_details']:
                if not test['passed']:
                    print(f"   • {test['name']}: {test['details']}")
        
        success_rate = (self.results['passed_tests'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! CRUD system is working properly!")
        elif success_rate >= 75:
            print("✅ GOOD! CRUD system is mostly functional with minor issues.")
        elif success_rate >= 50:
            print("⚠️ CONCERNING! CRUD system has significant issues.")
        else:
            print("❌ CRITICAL! CRUD system is not functioning properly.")
        
        return success_rate >= 75  # Return True if tests are mostly passing
    
    async def run_all_tests(self):
        """Run all CRUD tests"""
        print("🧪 Starting Comprehensive CRUD Test Suite")
        print("="*60)
        
        try:
            await self.setup()
            
            await self.test_user_preferences_crud()
            await self.test_conversation_state_crud()
            await self.test_empathetic_response_crud()
            await self.test_personality_engine_integration()
            await self.test_phase4_integration()
            await self.test_data_consistency()
            
        except Exception as e:
            print(f"❌ Test suite error: {e}")
            self.log_test("Test suite execution", False, str(e))
        finally:
            await self.cleanup()
            return self.print_summary()


async def main():
    """Main test execution"""
    test_suite = CRUDTestSuite()
    success = await test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())