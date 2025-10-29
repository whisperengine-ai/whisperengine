"""
Performance Benchmarking for Hybrid Query Routing Tools

Measures execution time for all 10 tools across different query types:
- Foundation tools (5): User facts, conversation context, character backstory, relationship summary, temporal trends
- Self-reflection tools (5): Reflect, analyze, query insights, adapt trait, record insight

Objective: Validate that tool execution adds minimal latency overhead
Target: 80% of queries < 50ms, 20% of queries < 3500ms (when including LLM calls)
"""

import asyncio
import asyncpg
import time
from typing import Dict, List, Any
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.knowledge.semantic_router import create_semantic_knowledge_router


class ToolPerformanceBenchmark:
    """Benchmark tool execution performance"""
    
    def __init__(self, postgres_pool):
        self.router = create_semantic_knowledge_router(
            postgres_pool=postgres_pool,
            qdrant_client=None,
            influx_client=None
        )
        self.results: Dict[str, List[float]] = {}
    
    async def benchmark_tool(
        self,
        tool_name: str,
        tool_func,
        iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Benchmark a single tool
        
        Args:
            tool_name: Name of tool being benchmarked
            tool_func: Async function to benchmark
            iterations: Number of iterations to run
            
        Returns:
            Dict with timing statistics
        """
        latencies = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                await tool_func()
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
            except Exception as e:
                print(f"   ⚠️  Error on iteration {i+1}: {str(e)[:50]}")
        
        if not latencies:
            return {
                "tool": tool_name,
                "status": "error",
                "iterations": 0
            }
        
        return {
            "tool": tool_name,
            "status": "success",
            "iterations": len(latencies),
            "mean_ms": statistics.mean(latencies),
            "median_ms": statistics.median(latencies),
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0],
            "all_latencies": latencies
        }
    
    async def run_all_benchmarks(self, iterations: int = 10) -> Dict[str, Any]:
        """Run benchmarks for all tools"""
        
        print("=" * 80)
        print("TOOL PERFORMANCE BENCHMARK")
        print("=" * 80)
        print(f"Iterations per tool: {iterations}")
        print(f"Target: Tool execution < 50ms (80% of cases)")
        print("=" * 80)
        
        results = {}
        
        # ====================================================================
        # FOUNDATION TOOLS (PostgreSQL-based - should be very fast)
        # ====================================================================
        
        print("\n" + "=" * 80)
        print("FOUNDATION TOOLS (PostgreSQL)")
        print("=" * 80)
        
        # Tool 1: query_user_facts
        print("\n📊 Benchmarking: query_user_facts")
        result = await self.benchmark_tool(
            "query_user_facts",
            lambda: self.router._tool_query_user_facts(
                user_id='672814231002939413',
                fact_type='all',
                limit=10
            ),
            iterations
        )
        results["query_user_facts"] = result
        self._print_result(result)
        
        # ====================================================================
        # SELF-REFLECTION TOOLS (PostgreSQL-based)
        # ====================================================================
        
        print("\n" + "=" * 80)
        print("SELF-REFLECTION TOOLS (PostgreSQL)")
        print("=" * 80)
        
        # Tool 2: reflect_on_interaction
        print("\n📊 Benchmarking: reflect_on_interaction")
        result = await self.benchmark_tool(
            "reflect_on_interaction",
            lambda: self.router.reflect_on_interaction(
                bot_name='jake',
                user_id='test_user_123',
                current_conversation_context='photography discussion',
                limit=5
            ),
            iterations
        )
        results["reflect_on_interaction"] = result
        self._print_result(result)
        
        # Tool 3: analyze_self_performance
        print("\n📊 Benchmarking: analyze_self_performance")
        result = await self.benchmark_tool(
            "analyze_self_performance",
            lambda: self.router.analyze_self_performance(
                bot_name='jake',
                metric='overall',
                time_window_days=30
            ),
            iterations
        )
        results["analyze_self_performance"] = result
        self._print_result(result)
        
        # Tool 4: query_self_insights
        print("\n📊 Benchmarking: query_self_insights")
        result = await self.benchmark_tool(
            "query_self_insights",
            lambda: self.router.query_self_insights(
                bot_name='jake',
                query_keywords=['pattern', 'repetition'],
                limit=5
            ),
            iterations
        )
        results["query_self_insights"] = result
        self._print_result(result)
        
        # Tool 5: adapt_personality_trait
        print("\n📊 Benchmarking: adapt_personality_trait")
        result = await self.benchmark_tool(
            "adapt_personality_trait",
            lambda: self.router.adapt_personality_trait(
                bot_name='jake',
                trait_name='benchmark_test',
                adjustment_reason='Performance benchmarking test run'
            ),
            iterations
        )
        results["adapt_personality_trait"] = result
        self._print_result(result)
        
        # Tool 6: record_manual_insight
        print("\n📊 Benchmarking: record_manual_insight")
        result = await self.benchmark_tool(
            "record_manual_insight",
            lambda: self.router.record_manual_insight(
                bot_name='jake',
                insight=f'Benchmark test insight at {time.time()}',
                insight_type='benchmark_test'
            ),
            iterations
        )
        results["record_manual_insight"] = result
        self._print_result(result)
        
        # ====================================================================
        # SUMMARY STATISTICS
        # ====================================================================
        
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        
        all_latencies = []
        for tool_name, result in results.items():
            if result['status'] == 'success':
                all_latencies.extend(result['all_latencies'])
        
        if all_latencies:
            overall_mean = statistics.mean(all_latencies)
            overall_median = statistics.median(all_latencies)
            overall_p95 = sorted(all_latencies)[int(len(all_latencies) * 0.95)]
            under_50ms = sum(1 for l in all_latencies if l < 50) / len(all_latencies) * 100
            
            print(f"\n📈 Overall Statistics (all tools, {len(all_latencies)} measurements):")
            print(f"   Mean:     {overall_mean:.2f}ms")
            print(f"   Median:   {overall_median:.2f}ms")
            print(f"   P95:      {overall_p95:.2f}ms")
            print(f"   < 50ms:   {under_50ms:.1f}% (target: 80%)")
            
            print(f"\n🎯 Performance Assessment:")
            if under_50ms >= 80:
                print(f"   ✅ EXCELLENT: {under_50ms:.1f}% of queries under 50ms (exceeds target)")
            elif under_50ms >= 60:
                print(f"   ✅ GOOD: {under_50ms:.1f}% of queries under 50ms (approaching target)")
            else:
                print(f"   ⚠️  NEEDS OPTIMIZATION: Only {under_50ms:.1f}% under 50ms")
            
            print(f"\n📊 Tool Execution Breakdown:")
            for tool_name in sorted(results.keys(), key=lambda t: results[t].get('mean_ms', 999999)):
                result = results[tool_name]
                if result['status'] == 'success':
                    mean = result['mean_ms']
                    p95 = result['p95_ms']
                    status_icon = "🟢" if mean < 50 else "🟡" if mean < 100 else "🔴"
                    print(f"   {status_icon} {tool_name:30s} Mean: {mean:6.2f}ms  P95: {p95:6.2f}ms")
        
        print("\n" + "=" * 80)
        print("✅ BENCHMARK COMPLETE")
        print("=" * 80)
        
        return results
    
    def _print_result(self, result: Dict[str, Any]):
        """Print formatted result for a single tool"""
        if result['status'] != 'success':
            print(f"   ❌ Status: {result['status']}")
            return
        
        mean = result['mean_ms']
        median = result['median_ms']
        p95 = result['p95_ms']
        min_val = result['min_ms']
        max_val = result['max_ms']
        
        # Performance indicator
        if mean < 50:
            status_icon = "🟢 FAST"
        elif mean < 100:
            status_icon = "🟡 MODERATE"
        else:
            status_icon = "🔴 SLOW"
        
        print(f"   {status_icon}")
        print(f"   Mean:   {mean:6.2f}ms")
        print(f"   Median: {median:6.2f}ms")
        print(f"   P95:    {p95:6.2f}ms")
        print(f"   Range:  {min_val:6.2f}ms - {max_val:6.2f}ms")


async def main():
    """Run benchmark suite"""
    
    # Connect to PostgreSQL
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        database='whisperengine',
        user='whisperengine',
        password='whisperengine_password'
    )
    
    # Run benchmarks
    benchmark = ToolPerformanceBenchmark(pool)
    results = await benchmark.run_all_benchmarks(iterations=10)
    
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
