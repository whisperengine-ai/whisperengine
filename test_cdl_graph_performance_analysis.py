#!/usr/bin/env python3
"""
CDL Graph Intelligence Performance Analysis
STEP 8: Database Performance Optimization Validation

Tests query performance improvements with new indexes for:
- Character background queries (<10ms target)
- Memory trigger queries (<15ms target)  
- Cross-pollination queries (<20ms target)
- Confidence-aware queries (<10ms target)
- Overall graph operations (<50ms target)
"""

import os
import asyncio
import time
import statistics
from typing import List, Dict, Tuple
import asyncpg
from dotenv import load_dotenv

# Load environment
load_dotenv()

class CDLGraphPerformanceAnalyzer:
    def __init__(self):
        self.db_pool = None
        self.performance_results = {}
        
    async def initialize(self):
        """Initialize database connection pool"""
        database_url = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'devpass123')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5433')}/"
            f"{os.getenv('POSTGRES_DB', 'whisperengine')}"
        )
        
        self.db_pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=5
        )
        print("🔗 Database connection established")
        
    async def close(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
            
    async def run_performance_test(self, query: str, params: List = None, test_name: str = "") -> Dict:
        """Run single query performance test with timing"""
        if not params:
            params = []
            
        times = []
        results_count = 0
        
        # Run query 10 times for statistical analysis
        for i in range(10):
            async with self.db_pool.acquire() as conn:
                start_time = time.perf_counter()
                try:
                    if params:
                        results = await conn.fetch(query, *params)
                    else:
                        results = await conn.fetch(query)
                    end_time = time.perf_counter()
                    
                    execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    times.append(execution_time)
                    results_count = len(results)
                    
                except Exception as e:
                    print(f"❌ Query failed: {test_name}")
                    print(f"   Error: {e}")
                    return {"status": "failed", "error": str(e)}
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        
        return {
            "status": "success",
            "test_name": test_name,
            "avg_time_ms": round(avg_time, 2),
            "min_time_ms": round(min_time, 2),
            "max_time_ms": round(max_time, 2),
            "median_time_ms": round(median_time, 2),
            "results_count": results_count,
            "all_times": [round(t, 2) for t in times]
        }
    
    async def test_character_background_queries(self) -> Dict:
        """Test character background query performance (<10ms target)"""
        print("\n🧠 Testing Character Background Queries...")
        
        # Get a character ID for testing
        async with self.db_pool.acquire() as conn:
            char_result = await conn.fetchrow("SELECT id FROM characters WHERE name = 'elena' LIMIT 1")
            if not char_result:
                return {"status": "skipped", "reason": "No elena character found"}
            character_id = char_result['id']
        
        # Test importance-sorted background query
        query = """
        SELECT id, description, importance_level, category 
        FROM character_background 
        WHERE character_id = $1 
        ORDER BY importance_level DESC 
        LIMIT 20
        """
        
        result = await self.run_performance_test(
            query, 
            [character_id], 
            "Character Background - Importance Sorted"
        )
        
        if result["status"] == "success":
            target_met = result["avg_time_ms"] < 10.0
            result["target_met"] = target_met
            result["target_ms"] = 10.0
            
        return result
    
    async def test_memory_trigger_queries(self) -> Dict:
        """Test memory trigger array overlap queries (<15ms target)"""
        print("🧠 Testing Memory Trigger Queries...")
        
        # Get a character ID for testing
        async with self.db_pool.acquire() as conn:
            char_result = await conn.fetchrow("SELECT id FROM characters WHERE name = 'elena' LIMIT 1")
            if not char_result:
                return {"status": "skipped", "reason": "No elena character found"}
            character_id = char_result['id']
        
        # Test GIN array overlap query (using actual column name 'description' instead of 'memory_content')
        query = """
        SELECT id, description, importance_level, emotional_impact
        FROM character_memories 
        WHERE character_id = $1 
        AND triggers && ARRAY['diving', 'research', 'ocean']
        ORDER BY importance_level DESC
        LIMIT 15
        """
        
        result = await self.run_performance_test(
            query,
            [character_id],
            "Memory Trigger - Array Overlap"
        )
        
        if result["status"] == "success":
            target_met = result["avg_time_ms"] < 15.0
            result["target_met"] = target_met
            result["target_ms"] = 15.0
            
        return result
    
    async def test_cross_pollination_queries(self) -> Dict:
        """Test cross-pollination queries (<20ms target)"""
        print("🔄 Testing Cross-Pollination Queries...")
        
        # Complex query simulating cross-pollination between user facts and character background
        query = """
        WITH user_entities AS (
            SELECT ARRAY['diving', 'marine_biology', 'research', 'ocean'] as entities
        )
        SELECT cb.id, cb.description, cb.importance_level, cb.category
        FROM character_background cb, user_entities ue
        WHERE cb.triggers && ue.entities
        AND cb.importance_level >= 7
        ORDER BY cb.importance_level DESC
        LIMIT 10
        """
        
        result = await self.run_performance_test(
            query,
            [],
            "Cross-Pollination - User Facts to Character Background"
        )
        
        if result["status"] == "success":
            target_met = result["avg_time_ms"] < 20.0
            result["target_met"] = target_met
            result["target_ms"] = 20.0
            
        return result
    
    async def test_confidence_aware_queries(self) -> Dict:
        """Test confidence-aware user fact queries (<10ms target)"""
        print("📊 Testing Confidence-Aware Queries...")
        
        # Test confidence-sorted user fact queries (using actual column name 'confidence')
        query = """
        SELECT ufr.id, fe.entity_name, ufr.confidence, ufr.relationship_type
        FROM user_fact_relationships ufr
        JOIN fact_entities fe ON ufr.entity_id = fe.id
        WHERE ufr.user_id = $1
        ORDER BY ufr.confidence DESC
        LIMIT 20
        """
        
        result = await self.run_performance_test(
            query,
            ["test_user_performance"],
            "Confidence-Aware - User Facts by Confidence"
        )
        
        if result["status"] == "success":
            target_met = result["avg_time_ms"] < 10.0
            result["target_met"] = target_met  
            result["target_ms"] = 10.0
            
        return result
    
    async def test_relationship_queries(self) -> Dict:
        """Test character relationship queries (<10ms target)"""
        print("🤝 Testing Character Relationship Queries...")
        
        # Get a character ID for testing
        async with self.db_pool.acquire() as conn:
            char_result = await conn.fetchrow("SELECT id FROM characters WHERE name = 'elena' LIMIT 1")
            if not char_result:
                return {"status": "skipped", "reason": "No elena character found"}
            character_id = char_result['id']
        
        # Test relationship strength queries
        query = """
        SELECT id, person_name, relationship_type, relationship_strength, description
        FROM character_relationships
        WHERE character_id = $1
        ORDER BY relationship_strength DESC
        LIMIT 15
        """
        
        result = await self.run_performance_test(
            query,
            [character_id],
            "Character Relationships - Strength Sorted"
        )
        
        if result["status"] == "success":
            target_met = result["avg_time_ms"] < 10.0
            result["target_met"] = target_met
            result["target_ms"] = 10.0
            
        return result
    
    async def test_ability_queries(self) -> Dict:
        """Test character ability queries (<10ms target)"""
        print("💪 Testing Character Ability Queries...")
        
        # Get a character ID for testing
        async with self.db_pool.acquire() as conn:
            char_result = await conn.fetchrow("SELECT id FROM characters WHERE name = 'elena' LIMIT 1")
            if not char_result:
                return {"status": "skipped", "reason": "No elena character found"}
            character_id = char_result['id']
        
        # Test proficiency-sorted ability queries (using actual column names)
        query = """
        SELECT id, ability_name, category, proficiency_level, description
        FROM character_abilities
        WHERE character_id = $1
        ORDER BY proficiency_level DESC
        LIMIT 15
        """
        
        result = await self.run_performance_test(
            query,
            [character_id],
            "Character Abilities - Proficiency Sorted"
        )
        
        if result["status"] == "success":
            target_met = result["avg_time_ms"] < 10.0
            result["target_met"] = target_met
            result["target_ms"] = 10.0
            
        return result
    
    async def analyze_index_usage(self) -> Dict:
        """Analyze CDL graph index usage statistics"""
        print("📈 Analyzing Index Usage Statistics...")
        
        query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan as scans,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
        FROM pg_stat_user_indexes
        WHERE indexname LIKE 'idx_character_%' 
           OR indexname LIKE 'idx_fact_%'
           OR indexname LIKE 'idx_user_fact_%'
        ORDER BY idx_scan DESC
        """
        
        async with self.db_pool.acquire() as conn:
            results = await conn.fetch(query)
            
        index_stats = []
        for row in results:
            index_stats.append({
                "table": row['tablename'],
                "index": row['indexname'],
                "scans": row['scans'],
                "tuples_read": row['tuples_read'],
                "tuples_fetched": row['tuples_fetched'],
                "size": row['index_size']
            })
            
        return {"index_statistics": index_stats}
    
    async def run_comprehensive_analysis(self) -> Dict:
        """Run complete CDL Graph Intelligence performance analysis"""
        print("🚀 Running CDL Graph Intelligence Performance Analysis")
        print("="*60)
        
        results = {}
        total_start_time = time.perf_counter()
        
        # Run all performance tests
        tests = [
            ("character_background", self.test_character_background_queries),
            ("memory_triggers", self.test_memory_trigger_queries),
            ("cross_pollination", self.test_cross_pollination_queries),
            ("confidence_aware", self.test_confidence_aware_queries),
            ("relationships", self.test_relationship_queries),
            ("abilities", self.test_ability_queries)
        ]
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                results[test_name] = {"status": "error", "error": str(e)}
        
        # Analyze index usage
        try:
            index_analysis = await self.analyze_index_usage()
            results["index_analysis"] = index_analysis
        except Exception as e:
            results["index_analysis"] = {"status": "error", "error": str(e)}
        
        total_end_time = time.perf_counter()
        total_time = (total_end_time - total_start_time) * 1000
        
        # Calculate overall performance summary
        successful_tests = [r for r in results.values() if r.get("status") == "success"]
        if successful_tests:
            avg_query_time = statistics.mean([r["avg_time_ms"] for r in successful_tests if "avg_time_ms" in r])
            targets_met = sum(1 for r in successful_tests if r.get("target_met", False))
            total_targets = len([r for r in successful_tests if "target_met" in r])
        else:
            avg_query_time = 0
            targets_met = 0
            total_targets = 0
        
        # Overall assessment
        overall_target_met = total_time < 50.0  # <50ms total target
        
        results["summary"] = {
            "total_analysis_time_ms": round(total_time, 2),
            "avg_query_time_ms": round(avg_query_time, 2) if avg_query_time else 0,
            "targets_met": targets_met,
            "total_targets": total_targets,
            "success_rate": f"{(targets_met/total_targets*100):.1f}%" if total_targets > 0 else "0%",
            "overall_target_met": overall_target_met,
            "overall_target_ms": 50.0
        }
        
        return results

def print_performance_report(results: Dict):
    """Print detailed performance analysis report"""
    print("\n" + "="*60)
    print("📊 CDL GRAPH INTELLIGENCE PERFORMANCE REPORT")
    print("="*60)
    
    summary = results.get("summary", {})
    print(f"\n🎯 OVERALL PERFORMANCE:")
    print(f"   Total Analysis Time: {summary.get('total_analysis_time_ms', 0)}ms")
    print(f"   Average Query Time: {summary.get('avg_query_time_ms', 0)}ms")
    print(f"   Targets Met: {summary.get('targets_met', 0)}/{summary.get('total_targets', 0)}")
    print(f"   Success Rate: {summary.get('success_rate', '0%')}")
    print(f"   Overall Target (<50ms): {'✅ PASSED' if summary.get('overall_target_met') else '❌ NEEDS OPTIMIZATION'}")
    
    print(f"\n📈 INDIVIDUAL TEST RESULTS:")
    
    test_names = {
        "character_background": "Character Background Queries",
        "memory_triggers": "Memory Trigger Queries", 
        "cross_pollination": "Cross-Pollination Queries",
        "confidence_aware": "Confidence-Aware Queries",
        "relationships": "Character Relationship Queries",
        "abilities": "Character Ability Queries"
    }
    
    for test_key, display_name in test_names.items():
        if test_key in results:
            result = results[test_key]
            
            if result.get("status") == "success":
                avg_time = result.get("avg_time_ms", 0)
                target = result.get("target_ms", 0)
                target_met = result.get("target_met", False)
                results_count = result.get("results_count", 0)
                
                status_icon = "✅" if target_met else "⚠️"
                print(f"   {status_icon} {display_name}:")
                print(f"      Average: {avg_time}ms (target: <{target}ms)")
                print(f"      Range: {result.get('min_time_ms', 0)}-{result.get('max_time_ms', 0)}ms")
                print(f"      Results: {results_count} rows")
                
            elif result.get("status") == "skipped":
                print(f"   ⏭️ {display_name}: SKIPPED ({result.get('reason', 'Unknown')})")
                
            else:
                print(f"   ❌ {display_name}: FAILED ({result.get('error', 'Unknown error')})")
    
    # Index usage analysis
    if "index_analysis" in results and "index_statistics" in results["index_analysis"]:
        print(f"\n🗂️ INDEX USAGE ANALYSIS:")
        index_stats = results["index_analysis"]["index_statistics"]
        
        if index_stats:
            for stat in index_stats[:10]:  # Show top 10 most used indexes
                print(f"   📋 {stat['index']} ({stat['table']}):")
                print(f"      Scans: {stat['scans']}, Size: {stat['size']}")
        else:
            print("   No index usage data available")
    
    print("\n" + "="*60)
    
    # Performance recommendations
    failed_tests = [k for k, v in results.items() if v.get("status") == "success" and not v.get("target_met", True)]
    if failed_tests:
        print("🔧 OPTIMIZATION RECOMMENDATIONS:")
        for test in failed_tests:
            if test == "memory_triggers":
                print("   • Consider additional GIN index tuning for memory trigger arrays")
            elif test == "cross_pollination":
                print("   • Optimize cross-pollination query with materialized views")
            elif test == "character_background":
                print("   • Review character background table partitioning")
            else:
                print(f"   • Review {test} query optimization strategies")
    else:
        print("🎉 ALL PERFORMANCE TARGETS MET! CDL Graph Intelligence is optimized.")
    
    print("="*60)

async def main():
    """Main execution function"""
    analyzer = CDLGraphPerformanceAnalyzer()
    
    try:
        # Initialize database connection
        await analyzer.initialize()
        
        # Run comprehensive performance analysis
        results = await analyzer.run_comprehensive_analysis()
        
        # Print detailed report
        print_performance_report(results)
        
        # Return success/failure based on results
        summary = results.get("summary", {})
        success_rate = float(summary.get("success_rate", "0%").rstrip("%"))
        
        if success_rate >= 80.0:
            print(f"\n🎉 CDL Graph Intelligence Performance: EXCELLENT ({success_rate}% targets met)")
            return True
        elif success_rate >= 60.0:
            print(f"\n⚠️ CDL Graph Intelligence Performance: GOOD ({success_rate}% targets met)")
            return True
        else:
            print(f"\n❌ CDL Graph Intelligence Performance: NEEDS OPTIMIZATION ({success_rate}% targets met)")
            return False
        
    except Exception as e:
        print(f"❌ Performance analysis failed: {e}")
        return False
        
    finally:
        await analyzer.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)