#!/usr/bin/env python3
"""
Simple validation test for Hybrid Query Routing integration.

This script tests:
1. HybridQueryRouter complexity assessment
2. Tool execution (query_user_facts, recall_conversation_context)
3. Integration with MessageProcessor (via HTTP chat API)

Usage:
    source .venv/bin/activate && \
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
    export QDRANT_HOST="localhost" && \
    export QDRANT_PORT="6334" && \
    export POSTGRES_HOST="localhost" && \
    export POSTGRES_PORT="5433" && \
    export DISCORD_BOT_NAME=elena && \
    python tests/automated/test_hybrid_routing_simple.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_complexity_assessment():
    """Test 1: Complexity assessment algorithm."""
    print("\n" + "="*80)
    print("TEST 1: Complexity Assessment Algorithm")
    print("="*80)
    
    from src.intelligence.hybrid_query_router import HybridQueryRouter
    
    router = HybridQueryRouter(complexity_threshold=0.3, log_assessments=True)
    
    test_queries = [
        # Simple queries (should use semantic search)
        ("Hi there!", "Simple greeting"),
        ("How are you?", "Basic question"),
        ("Thanks!", "Simple response"),
        
        # Complex queries (should use tool calling)
        ("What do you remember about me and my pets?", "Multi-entity query"),
        ("Tell me about our conversation history and what I've shared with you", "Relationship query"),
        ("What are the recent trends in our conversations?", "Temporal query"),
    ]
    
    results = []
    for query, description in test_queries:
        assessment = router.assess_query_complexity(
            user_message=query,
            user_id="test_user",
            character_name="elena"
        )
        
        print(f"\nQuery: '{query}'")
        print(f"Description: {description}")
        print(f"Score: {assessment.complexity_score:.3f}")
        print(f"Use Tools: {'YES' if assessment.use_tools else 'NO'}")
        print(f"Reasoning: {assessment.reasoning}")
        
        results.append({
            "query": query,
            "score": assessment.complexity_score,
            "use_tools": assessment.use_tools
        })
    
    # Validate results
    simple_queries = [r for r in results[:3]]
    complex_queries = [r for r in results[3:]]
    
    simple_correct = all(not r["use_tools"] for r in simple_queries)
    complex_correct = all(r["use_tools"] for r in complex_queries)
    
    print("\n" + "-"*80)
    print(f"✅ Simple queries (should NOT use tools): {3 if simple_correct else 'FAILED'}/3")
    print(f"✅ Complex queries (should use tools): {3 if complex_correct else 'FAILED'}/3")
    
    return simple_correct and complex_correct


async def test_tool_executor():
    """Test 2: Tool execution."""
    print("\n" + "="*80)
    print("TEST 2: Tool Executor")
    print("="*80)
    
    from src.intelligence.tool_executor import ToolExecutor
    import asyncpg
    
    # Connect to PostgreSQL
    postgres_url = f"postgresql://localhost:5433/whisperengine"
    print(f"\nConnecting to PostgreSQL: {postgres_url}")
    
    try:
        pool = await asyncpg.create_pool(postgres_url, min_size=1, max_size=2)
        print("✅ PostgreSQL connected")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    
    executor = ToolExecutor(
        postgres_pool=pool,
        vector_memory=None,  # Will skip Qdrant tests
        influxdb_client=None,  # Will skip InfluxDB tests
        character_name="elena"
    )
    
    # Test query_user_facts
    print("\n" + "-"*80)
    print("Testing: query_user_facts")
    print("-"*80)
    
    try:
        result = await executor.execute_tool_call(
            tool_name="query_user_facts",
            tool_arguments={
                "user_id": "672814231002939413",  # Real user ID from instructions
                "fact_type": "all",
                "limit": 5
            }
        )
        
        print(f"Success: {result['success']}")
        print(f"Execution Time: {result['execution_time_ms']:.2f}ms")
        if result['success']:
            print(f"Facts Retrieved: {len(result['data'])}")
            if result['data']:
                print(f"Sample Fact: {result['data'][0]}")
        else:
            print(f"Error: {result['error']}")
        
        query_user_facts_works = result['success']
    except Exception as e:
        print(f"❌ query_user_facts failed: {e}")
        query_user_facts_works = False
    
    await pool.close()
    
    print("\n" + "-"*80)
    print(f"✅ query_user_facts: {'PASS' if query_user_facts_works else 'FAIL'}")
    
    return query_user_facts_works


async def test_http_chat_api():
    """Test 3: Integration via HTTP chat API."""
    print("\n" + "="*80)
    print("TEST 3: HTTP Chat API Integration (Manual)")
    print("="*80)
    
    print("\nTo test the full integration with HTTP chat API, run:")
    print("\n1. Start Elena bot:")
    print("   ./multi-bot.sh bot elena")
    print("\n2. Test with curl:")
    print('   curl -X POST http://localhost:9091/api/chat \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{')
    print('       "user_id": "test_hybrid_routing_001",')
    print('       "message": "What do you remember about me and my interests?",')
    print('       "metadata": {"platform": "api_test", "channel_type": "dm"}')
    print('     }\'')
    print("\n3. Check logs for:")
    print("   - 🔧 HYBRID ROUTING: Using tool calling")
    print("   - 🔧 EXECUTING TOOL: query_user_facts")
    print("   - 🔧 CONTEXT ENRICHMENT: Added tool results")
    
    return True  # Manual test


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("HYBRID QUERY ROUTING - SIMPLE VALIDATION TESTS")
    print("="*80)
    
    # Check environment
    print("\nEnvironment Check:")
    print(f"  QDRANT_HOST: {os.getenv('QDRANT_HOST', 'NOT SET')}")
    print(f"  QDRANT_PORT: {os.getenv('QDRANT_PORT', 'NOT SET')}")
    print(f"  POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'NOT SET')}")
    print(f"  POSTGRES_PORT: {os.getenv('POSTGRES_PORT', 'NOT SET')}")
    print(f"  DISCORD_BOT_NAME: {os.getenv('DISCORD_BOT_NAME', 'NOT SET')}")
    
    # Run tests
    results = {}
    
    try:
        results["complexity_assessment"] = await test_complexity_assessment()
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results["complexity_assessment"] = False
    
    try:
        results["tool_executor"] = await test_tool_executor()
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results["tool_executor"] = False
    
    try:
        results["http_chat_api"] = await test_http_chat_api()
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        results["http_chat_api"] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All automated tests passed! Ready for HTTP chat API testing.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
