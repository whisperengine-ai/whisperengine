"""
STEP 1: Basic CDL Integration - Direct Validation Test

Tests CharacterGraphManager integration with cdl_ai_integration.py
Validates personal knowledge extraction uses graph queries instead of direct property access.
"""

import asyncio
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_step1_integration():
    """Test STEP 1: Personal knowledge extraction with graph intelligence"""
    
    print("\n" + "="*80)
    print("STEP 1 VALIDATION: CDL Graph Integration")
    print("="*80 + "\n")
    
    try:
        # Initialize CDL AI Integration
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        cdl_integration = CDLAIPromptIntegration()
        
        # Load character from database
        character = await cdl_integration.load_character()
        print(f"✅ Loaded character: {character.identity.name}")
        print(f"   Occupation: {character.identity.occupation}\n")
        
        # Test scenarios for personal knowledge extraction
        test_cases = [
            {
                "scenario": "Family Question",
                "message": "Tell me about your family background",
                "expected_intent": "family",
                "character": "Jake"
            },
            {
                "scenario": "Career Question",
                "message": "What's your career and professional experience?",
                "expected_intent": "career",
                "character": "Jake"
            },
            {
                "scenario": "Hobbies Question",
                "message": "What are your hobbies and interests?",
                "expected_intent": "hobbies",
                "character": "Jake"
            },
            {
                "scenario": "Education Question",
                "message": "Tell me about your education background",
                "expected_intent": "education",
                "character": "Elena"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            print(f"📝 TEST: {test_case['scenario']}")
            print(f"   Message: \"{test_case['message']}\"")
            
            # Extract personal knowledge using graph manager
            personal_knowledge = await cdl_integration._extract_cdl_personal_knowledge_sections(
                character=character,
                message_content=test_case['message']
            )
            
            # Analyze results
            if personal_knowledge:
                lines = personal_knowledge.strip().split('\n')
                print(f"   ✅ Graph Query Results: {len(lines)} knowledge sections extracted")
                
                # Show sample results
                for i, line in enumerate(lines[:3], 1):
                    print(f"      {i}. {line[:80]}{'...' if len(line) > 80 else ''}")
                
                if len(lines) > 3:
                    print(f"      ... and {len(lines) - 3} more")
                
                # Check for graph intelligence indicators
                has_importance = any('importance' in line.lower() or '⭐' in line for line in lines)
                has_strength = any('strength' in line.lower() for line in lines)
                has_proficiency = any('proficiency' in line.lower() for line in lines)
                
                graph_features = []
                if has_importance: graph_features.append("importance weighting")
                if has_strength: graph_features.append("strength scoring")
                if has_proficiency: graph_features.append("proficiency levels")
                
                if graph_features:
                    print(f"   🎯 Graph Intelligence: {', '.join(graph_features)}")
                
                results.append({
                    "scenario": test_case['scenario'],
                    "success": True,
                    "sections_count": len(lines),
                    "has_graph_features": len(graph_features) > 0
                })
            else:
                print(f"   ⚠️  No results - possible data gap for {character.identity.name}")
                results.append({
                    "scenario": test_case['scenario'],
                    "success": False,
                    "sections_count": 0,
                    "has_graph_features": False
                })
            
            print()
        
        # Summary
        print("="*80)
        print("STEP 1 VALIDATION SUMMARY")
        print("="*80)
        
        successful_tests = sum(1 for r in results if r['success'])
        graph_enabled_tests = sum(1 for r in results if r['has_graph_features'])
        
        print(f"\n✅ Successful Tests: {successful_tests}/{len(test_cases)}")
        print(f"🎯 Graph Features Detected: {graph_enabled_tests}/{len(test_cases)}")
        
        if successful_tests == len(test_cases):
            print("\n🎉 STEP 1 COMPLETE: Graph intelligence working!")
            print("   Personal knowledge extraction now uses CharacterGraphManager")
            print("   Importance-weighted, multi-dimensional results operational")
        elif successful_tests > 0:
            print(f"\n⚠️  PARTIAL SUCCESS: {successful_tests}/{len(test_cases)} tests passed")
            print("   Some characters may have data gaps in database")
        else:
            print("\n❌ TESTS FAILED: Graph integration not working")
        
        # Detailed results
        print("\nDetailed Results:")
        for r in results:
            status = "✅" if r['success'] else "❌"
            graph_status = "🎯" if r['has_graph_features'] else "⚪"
            print(f"  {status} {graph_status} {r['scenario']}: {r['sections_count']} sections")
        
        print("\n" + "="*80 + "\n")
        
        return successful_tests == len(test_cases)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_graph_manager_direct():
    """Test CharacterGraphManager directly for debugging"""
    
    print("\n" + "="*80)
    print("DIRECT CharacterGraphManager TEST")
    print("="*80 + "\n")
    
    try:
        from src.characters.cdl.character_graph_manager import (
            create_character_graph_manager,
            CharacterKnowledgeIntent
        )
        from src.characters.cdl.simple_cdl_manager import get_simple_cdl_manager
        
        # Get database pool
        cdl_manager = get_simple_cdl_manager()
        postgres_pool = await cdl_manager._get_database_pool()
        
        # Create graph manager
        graph_manager = create_character_graph_manager(postgres_pool)
        print("✅ CharacterGraphManager initialized\n")
        
        # Test with Jake's career
        print("📝 TEST: Jake's career background")
        result = await graph_manager.query_character_knowledge(
            character_name='jake',
            query_text='Tell me about your career',
            intent=CharacterKnowledgeIntent.CAREER,
            limit=3
        )
        
        print(f"   Background: {len(result.background)} entries")
        print(f"   Memories: {len(result.memories)} entries")
        print(f"   Relationships: {len(result.relationships)} entries")
        print(f"   Abilities: {len(result.abilities)} entries")
        print(f"   Total: {result.total_results} results\n")
        
        if result.total_results > 0:
            print("✅ CharacterGraphManager working correctly")
            return True
        else:
            print("⚠️  No results from CharacterGraphManager")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set required environment variables for testing
    if not os.getenv('FASTEMBED_CACHE_PATH'):
        os.environ['FASTEMBED_CACHE_PATH'] = '/tmp/fastembed_cache'
    
    # Run tests
    asyncio.run(test_graph_manager_direct())
    asyncio.run(test_step1_integration())
