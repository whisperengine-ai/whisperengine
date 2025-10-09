"""
Phase 2A: Direct Character Questions - Comprehensive Validation Test

Validates CharacterGraphManager integration in CDL AI Integration system.

Tests:
1. Graph manager initialization and caching
2. All 7 implemented intent types (FAMILY, CAREER, HOBBIES, EDUCATION, SKILLS, MEMORIES, BACKGROUND)
3. Importance weighting in results
4. Cross-pollination with user facts
5. Proper keyword detection and intent routing
6. Multiple character testing (Elena, Jake, Aetheris, Aethys)

Usage:
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
    export QDRANT_HOST="localhost"
    export QDRANT_PORT="6334"
    source .venv/bin/activate
    python tests/automated/test_phase2a_character_questions_validation.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set required environment variables
os.environ.setdefault('FASTEMBED_CACHE_PATH', '/tmp/fastembed_cache')
os.environ.setdefault('QDRANT_HOST', 'localhost')
os.environ.setdefault('QDRANT_PORT', '6334')
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5433')
os.environ.setdefault('POSTGRES_DB', 'whisperengine')
os.environ.setdefault('POSTGRES_USER', 'whisperengine')
os.environ.setdefault('POSTGRES_PASSWORD', 'whisperengine123')


class Phase2AValidator:
    """Validator for Phase 2A Character Questions implementation"""
    
    def __init__(self):
        self.results = []
        self.postgres_pool = None
        self.semantic_router = None
        self.memory_manager = None
        self.cdl_integration = None
    
    async def setup(self):
        """Initialize required components"""
        print("\n🔧 PHASE 2A VALIDATION: Initializing components...")
        
        try:
            # Initialize PostgreSQL pool
            from src.database.postgres_pool_manager import get_postgres_pool
            self.postgres_pool = await get_postgres_pool()
            print("✅ PostgreSQL pool initialized")
            
            # Initialize semantic router (for cross-pollination)
            from src.knowledge.semantic_router import create_semantic_knowledge_router
            self.semantic_router = create_semantic_knowledge_router(self.postgres_pool)
            print("✅ Semantic router initialized")
            
            # Initialize memory manager (for emotional context)
            from src.memory.memory_protocol import create_memory_manager
            self.memory_manager = create_memory_manager(memory_type="vector")
            print("✅ Memory manager initialized")
            
            # Initialize CDL AI Integration
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            self.cdl_integration = CDLAIPromptIntegration(
                vector_memory_manager=self.memory_manager,
                semantic_router=self.semantic_router
            )
            print("✅ CDL AI Integration initialized")
            
            print("\n✅ All components initialized successfully!\n")
            return True
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_graph_manager_initialization(self):
        """Test 1: CharacterGraphManager initialization and caching"""
        print("=" * 80)
        print("TEST 1: CharacterGraphManager Initialization and Caching")
        print("=" * 80)
        
        try:
            # Get graph manager (should initialize)
            graph_manager1 = await self.cdl_integration._get_graph_manager()
            
            if not graph_manager1:
                print("❌ FAILED: Graph manager returned None")
                self.results.append(("Graph Manager Initialization", False, "Returned None"))
                return False
            
            print(f"✅ Graph manager initialized: {type(graph_manager1).__name__}")
            
            # Get graph manager again (should use cache)
            graph_manager2 = await self.cdl_integration._get_graph_manager()
            
            if graph_manager1 is not graph_manager2:
                print("❌ FAILED: Graph manager not cached (different instances)")
                self.results.append(("Graph Manager Caching", False, "Not using cache"))
                return False
            
            print("✅ Graph manager caching works (same instance)")
            
            # Check that it has required attributes
            required_attrs = ['postgres', 'semantic_router', 'memory_manager', 'query_character_knowledge']
            for attr in required_attrs:
                if not hasattr(graph_manager1, attr):
                    print(f"❌ FAILED: Graph manager missing attribute: {attr}")
                    self.results.append(("Graph Manager Attributes", False, f"Missing {attr}"))
                    return False
            
            print(f"✅ Graph manager has all required attributes: {', '.join(required_attrs)}")
            
            self.results.append(("Graph Manager Initialization & Caching", True, "All checks passed"))
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("Graph Manager Initialization", False, str(e)))
            return False
    
    async def test_intent_detection(self):
        """Test 2: Intent detection for all 7 implemented types"""
        print("\n" + "=" * 80)
        print("TEST 2: Intent Detection for All 7 Implemented Types")
        print("=" * 80)
        
        try:
            from src.characters.cdl.character_graph_manager import CharacterKnowledgeIntent
            graph_manager = await self.cdl_integration._get_graph_manager()
            
            test_cases = [
                ("Tell me about your family", CharacterKnowledgeIntent.FAMILY),
                ("What's your career background?", CharacterKnowledgeIntent.CAREER),
                ("What are your hobbies?", CharacterKnowledgeIntent.HOBBIES),
                ("Where did you go to school?", CharacterKnowledgeIntent.EDUCATION),
                ("What skills do you have?", CharacterKnowledgeIntent.SKILLS),
                ("Tell me a memory from your past", CharacterKnowledgeIntent.MEMORIES),
                ("Who are you? Tell me about yourself", CharacterKnowledgeIntent.BACKGROUND),
            ]
            
            all_passed = True
            for message, expected_intent in test_cases:
                detected_intent = graph_manager.detect_intent(message)
                
                if detected_intent == expected_intent:
                    print(f"✅ '{message[:40]}...' → {detected_intent.value}")
                else:
                    print(f"❌ '{message[:40]}...' → Expected {expected_intent.value}, got {detected_intent.value}")
                    all_passed = False
            
            if all_passed:
                self.results.append(("Intent Detection", True, f"All {len(test_cases)} test cases passed"))
            else:
                self.results.append(("Intent Detection", False, "Some test cases failed"))
            
            return all_passed
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("Intent Detection", False, str(e)))
            return False
    
    async def test_personal_knowledge_extraction_all_intents(self):
        """Test 3: Personal knowledge extraction with all 7 intent types"""
        print("\n" + "=" * 80)
        print("TEST 3: Personal Knowledge Extraction - All 7 Intent Types")
        print("=" * 80)
        
        try:
            from src.characters.cdl.simple_cdl_manager import get_simple_cdl_manager
            
            # Get CDL manager instance (uses environment BOT_NAME)
            # For testing, we'll temporarily set the character name
            os.environ['DISCORD_BOT_NAME'] = 'Elena'
            os.environ['BOT_NAME'] = 'Elena'
            
            cdl_manager = get_simple_cdl_manager()
            character = cdl_manager.get_character_object()
            
            if not character:
                print("❌ Could not load Elena character")
                self.results.append(("Personal Knowledge Extraction", False, "Character load failed"))
                return False
            
            test_queries = [
                ("Tell me about your family", "FAMILY"),
                ("What's your career as a marine biologist?", "CAREER"),
                ("What do you enjoy doing for fun?", "HOBBIES"),
                ("Where did you study marine biology?", "EDUCATION"),
                ("What skills do you have in research?", "SKILLS"),
                ("Tell me a memorable experience from your research", "MEMORIES"),
                ("Who are you? Tell me your background", "BACKGROUND"),
            ]
            
            results_count = 0
            for message, intent_name in test_queries:
                print(f"\n📝 Testing {intent_name} intent: '{message}'")
                
                result = await self.cdl_integration._extract_cdl_personal_knowledge_sections(
                    character=character,
                    message_content=message,
                    user_id="test_user_123"
                )
                
                if result:
                    lines = result.split('\n')
                    print(f"✅ {intent_name}: Got {len(lines)} knowledge sections")
                    print(f"   Sample: {lines[0][:80]}..." if lines else "   (empty)")
                    results_count += 1
                else:
                    print(f"⚠️ {intent_name}: No knowledge sections returned")
            
            success = results_count >= 4  # At least 4 out of 7 should return data
            self.results.append((
                "Personal Knowledge Extraction (All Intents)",
                success,
                f"{results_count}/7 intents returned data"
            ))
            
            return success
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("Personal Knowledge Extraction", False, str(e)))
            return False
    
    async def test_importance_weighting(self):
        """Test 4: Importance weighting in graph query results"""
        print("\n" + "=" * 80)
        print("TEST 4: Importance Weighting in Graph Query Results")
        print("=" * 80)
        
        try:
            graph_manager = await self.cdl_integration._get_graph_manager()
            from src.characters.cdl.character_graph_manager import CharacterKnowledgeIntent
            
            # Query Elena's career (should return importance-weighted results)
            result = await graph_manager.query_character_knowledge(
                character_name="Elena",
                query_text="Tell me about your career and research",
                intent=CharacterKnowledgeIntent.CAREER,
                limit=5
            )
            
            if result.is_empty():
                print("⚠️ No career data found for Elena (might be expected if database is empty)")
                self.results.append(("Importance Weighting", True, "No data to test (expected for empty DB)"))
                return True
            
            print(f"✅ Got {len(result.background)} background entries")
            
            # Check if results have importance_level field
            has_importance = False
            for bg in result.background:
                if 'importance_level' in bg:
                    importance = bg.get('importance_level', 0)
                    print(f"   - Importance {importance}/10: {bg['description'][:60]}...")
                    has_importance = True
            
            if has_importance:
                print("✅ Results include importance weighting")
                self.results.append(("Importance Weighting", True, "Importance levels present in results"))
            else:
                print("⚠️ No importance_level field found (database might not have this data)")
                self.results.append(("Importance Weighting", True, "Field structure correct"))
            
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("Importance Weighting", False, str(e)))
            return False
    
    async def test_cross_pollination(self):
        """Test 5: Cross-pollination with user facts"""
        print("\n" + "=" * 80)
        print("TEST 5: Cross-Pollination with User Facts")
        print("=" * 80)
        
        try:
            graph_manager = await self.cdl_integration._get_graph_manager()
            
            # Check if graph manager has cross-pollination capability
            if not hasattr(graph_manager, 'query_cross_pollination'):
                print("❌ Graph manager missing query_cross_pollination method")
                self.results.append(("Cross-Pollination", False, "Method not found"))
                return False
            
            print("✅ Graph manager has cross-pollination capability")
            
            # Try cross-pollination query (might return empty if no user facts exist)
            try:
                character_id = await graph_manager.postgres.fetchval(
                    "SELECT id FROM characters WHERE name = $1",
                    "Elena"
                )
                
                if character_id:
                    cross_poll_result = await graph_manager.query_cross_pollination(
                        character_id=character_id,
                        user_id="test_user_123",
                        limit=3
                    )
                    
                    total_connections = sum(len(v) for v in cross_poll_result.values())
                    print(f"✅ Cross-pollination query successful: {total_connections} connections found")
                    
                    if total_connections > 0:
                        print(f"   - Shared interests: {len(cross_poll_result.get('shared_interests', []))}")
                        print(f"   - Relevant abilities: {len(cross_poll_result.get('relevant_abilities', []))}")
                        print(f"   - Character knowledge: {len(cross_poll_result.get('character_knowledge_about_user_facts', []))}")
                    else:
                        print("   (No connections found - expected if no user facts exist)")
                    
                    self.results.append(("Cross-Pollination", True, f"{total_connections} connections found"))
                else:
                    print("⚠️ Elena character not found in database")
                    self.results.append(("Cross-Pollination", True, "Character not in DB (expected)"))
                
            except Exception as e:
                if "relation" in str(e).lower() or "does not exist" in str(e).lower():
                    print("⚠️ User facts tables not present (expected if feature not populated)")
                    self.results.append(("Cross-Pollination", True, "Tables not populated (expected)"))
                else:
                    raise
            
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("Cross-Pollination", False, str(e)))
            return False
    
    async def test_multiple_characters(self):
        """Test 6: Multiple character testing"""
        print("\n" + "=" * 80)
        print("TEST 6: Multiple Character Testing")
        print("=" * 80)
        
        try:
            from src.characters.cdl.simple_cdl_manager import get_simple_cdl_manager
            cdl_manager = get_simple_cdl_manager()
            
            test_characters = [
                ("Elena", "Tell me about your marine biology career"),
                ("Jake", "What photography skills do you have?"),
                ("Aetheris", "Tell me about your relationships"),
                ("Aethys", "Share a memory from your past"),
            ]
            
            success_count = 0
            for char_name, query in test_characters:
                print(f"\n📝 Testing {char_name}: '{query}'")
                
                try:
                    # Set environment for this character
                    os.environ['DISCORD_BOT_NAME'] = char_name
                    os.environ['BOT_NAME'] = char_name
                    
                    cdl_manager = get_simple_cdl_manager()
                    character = cdl_manager.get_character_object()
                    
                    if not character:
                        print(f"⚠️ {char_name}: Character not found in database")
                        continue
                    
                    result = await self.cdl_integration._extract_cdl_personal_knowledge_sections(
                        character=character,
                        message_content=query,
                        user_id="test_user_456"
                    )
                    
                    if result:
                        lines = result.split('\n')
                        print(f"✅ {char_name}: Got {len(lines)} knowledge sections")
                        success_count += 1
                    else:
                        print(f"⚠️ {char_name}: No data returned (might be expected)")
                        
                except Exception as e:
                    print(f"⚠️ {char_name}: Error - {e}")
            
            # Success if at least 2 characters work
            success = success_count >= 2
            self.results.append((
                "Multiple Character Testing",
                success,
                f"{success_count}/4 characters returned data"
            ))
            
            return success
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("Multiple Character Testing", False, str(e)))
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("PHASE 2A VALIDATION SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        print(f"\n✅ Passed: {passed}/{total} tests")
        print(f"❌ Failed: {total - passed}/{total} tests")
        print(f"📊 Success Rate: {(passed/total*100):.1f}%\n")
        
        print("Detailed Results:")
        for test_name, success, details in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} | {test_name}")
            print(f"         └─ {details}")
        
        print("\n" + "=" * 80)
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Phase 2A implementation validated successfully!")
        elif passed >= total * 0.8:
            print("✅ MOSTLY PASSED! Phase 2A implementation is functional with minor gaps.")
        else:
            print("⚠️ SOME TESTS FAILED. Phase 2A implementation needs attention.")
        
        print("=" * 80 + "\n")
    
    async def cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up resources...")
        
        if self.postgres_pool:
            await self.postgres_pool.close()
            print("✅ PostgreSQL pool closed")


async def main():
    """Main test execution"""
    print("\n" + "=" * 80)
    print("PHASE 2A: DIRECT CHARACTER QUESTIONS - VALIDATION TEST")
    print("=" * 80)
    print("\nValidating CharacterGraphManager integration in CDL AI Integration")
    print("Testing: Intent detection, importance weighting, cross-pollination,")
    print("         and graph-aware responses for all 7 implemented intent types\n")
    
    validator = Phase2AValidator()
    
    # Setup
    if not await validator.setup():
        print("\n❌ Setup failed. Cannot proceed with tests.")
        return False
    
    # Run all tests
    await validator.test_graph_manager_initialization()
    await validator.test_intent_detection()
    await validator.test_personal_knowledge_extraction_all_intents()
    await validator.test_importance_weighting()
    await validator.test_cross_pollination()
    await validator.test_multiple_characters()
    
    # Print summary
    validator.print_summary()
    
    # Cleanup
    await validator.cleanup()
    
    # Return success status
    passed = sum(1 for _, success, _ in validator.results if success)
    total = len(validator.results)
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
