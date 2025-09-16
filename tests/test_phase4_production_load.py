"""
Phase 4 Production-Ready Concurrency and Load Testing

This test suite validates Phase 4 systems under realistic production loads,
focusing on thread safety, race conditions, and performance under stress.

Test Scenarios:
1. High-volume concurrent user conversations
2. Memory system thread safety under load  
3. Engagement analysis performance scaling
4. Cross-component integration stability
5. Resource exhaustion and recovery testing
"""

import asyncio
import logging
import time
import uuid
import random
from typing import List, Dict, Any
import statistics

# Import Phase 4 components
from src.personality.memory_moments import MemoryTriggeredMoments
from src.conversation.advanced_thread_manager import AdvancedConversationThreadManager
from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine

logger = logging.getLogger(__name__)

class Phase4ProductionLoadTester:
    """Production-grade load testing for Phase 4 systems"""
    
    def __init__(self):
        self.memory_moments = MemoryTriggeredMoments()
        self.thread_manager = AdvancedConversationThreadManager()
        self.engagement_engine = ProactiveConversationEngagementEngine()
        
        logger.info("✅ Phase 4 components initialized for load testing")
    
    def generate_conversation_patterns(self, pattern_count: int) -> List[List[str]]:
        """Generate realistic conversation patterns for testing"""
        patterns = [
            # Career development conversation
            [
                "I've been thinking about my career path lately",
                "I'm considering a transition to data science",
                "It seems like a growing field with good opportunities",
                "But I'm worried about the learning curve",
                "What do you think about online courses vs bootcamps?",
                "I want to make sure I'm making the right choice"
            ],
            
            # Personal growth conversation  
            [
                "I've been working on building better habits",
                "I started meditating 10 minutes every morning",
                "It's actually been really helpful for my focus",
                "I'm also trying to read more books",
                "Do you have any book recommendations?",
                "I'm interested in psychology and self-improvement"
            ],
            
            # Relationship conversation
            [
                "I had an interesting conversation with my friend yesterday",
                "We were talking about how technology affects relationships",
                "It's amazing how we can stay connected but also feel distant",
                "Sometimes I miss the simplicity of face-to-face conversations",
                "But I also appreciate being able to reach out anytime",
                "It's all about finding the right balance I think"
            ],
            
            # Creative project conversation
            [
                "I started a new creative project last week",
                "I'm learning to paint with watercolors",
                "It's much harder than I expected!",
                "But also really relaxing and meditative",
                "I love how colors blend in unexpected ways",
                "I think creativity is important for mental health"
            ],
            
            # Travel planning conversation
            [
                "I'm planning a trip to Japan next year",
                "I've always been fascinated by the culture",
                "The food, the architecture, the technology",
                "I'm trying to learn some basic Japanese phrases",
                "Do you think two weeks would be enough time?",
                "I want to visit both Tokyo and Kyoto"
            ]
        ]
        
        # Generate requested number of patterns by cycling and varying
        result_patterns = []
        for i in range(pattern_count):
            base_pattern = patterns[i % len(patterns)]
            
            # Add some variation to make each pattern unique
            varied_pattern = []
            for message in base_pattern:
                if random.random() < 0.3:  # 30% chance to add variation
                    variations = [
                        f"{message} Actually, let me think about that more.",
                        f"{message} I'm curious about your perspective.",
                        f"{message} It's been on my mind a lot lately.",
                        f"{message} What's your experience with this?"
                    ]
                    varied_pattern.append(random.choice(variations))
                else:
                    varied_pattern.append(message)
            
            result_patterns.append(varied_pattern)
        
        return result_patterns
    
    async def test_concurrent_conversations(self, user_count: int = 100, conversations_per_user: int = 3):
        """Test system under concurrent conversation load"""
        logger.info(f"🧵 Testing concurrent conversations: {user_count} users, {conversations_per_user} conversations each")
        
        start_time = time.time()
        successful_operations = 0
        failed_operations = 0
        response_times = []
        errors = []
        
        async def user_conversation_session(user_id: str):
            """Simulate a complete user conversation session"""
            nonlocal successful_operations, failed_operations
            
            try:
                conversation_patterns = self.generate_conversation_patterns(conversations_per_user)
                
                for pattern_idx, conversation in enumerate(conversation_patterns):
                    for msg_idx, message in enumerate(conversation):
                        operation_start = time.time()
                        
                        try:
                            # Process message through thread manager
                            result = await self.thread_manager.process_user_message(
                                user_id, message, {"pattern": pattern_idx, "message": msg_idx}
                            )
                            
                            operation_time = time.time() - operation_start
                            response_times.append(operation_time)
                            successful_operations += 1
                            
                            # Small delay to simulate user thinking time
                            await asyncio.sleep(random.uniform(0.1, 0.3))
                            
                        except Exception as e:
                            failed_operations += 1
                            errors.append(f"User {user_id} pattern {pattern_idx} msg {msg_idx}: {str(e)[:100]}")
                    
                    # Pause between conversation topics
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                        
            except Exception as e:
                failed_operations += conversations_per_user * 6  # Assume 6 messages per conversation
                errors.append(f"User {user_id} session failed: {str(e)[:100]}")
        
        # Generate users and run concurrent sessions
        user_ids = [f"load_user_{uuid.uuid4().hex[:6]}" for _ in range(user_count)]
        
        tasks = [user_conversation_session(user_id) for user_id in user_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        total_operations = successful_operations + failed_operations
        
        # Calculate performance metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
        
        result = {
            "test_name": "concurrent_conversations",
            "user_count": user_count,
            "conversations_per_user": conversations_per_user,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "duration_seconds": duration,
            "operations_per_second": total_operations / duration if duration > 0 else 0,
            "avg_response_time_ms": avg_response_time * 1000,
            "p95_response_time_ms": p95_response_time * 1000,
            "error_count": len(errors),
            "errors_sample": errors[:3]
        }
        
        logger.info(f"✅ Concurrent conversations: {successful_operations}/{total_operations} ops "
                   f"({result['success_rate']:.1%} success) in {duration:.1f}s, "
                   f"avg {result['avg_response_time_ms']:.1f}ms, p95 {result['p95_response_time_ms']:.1f}ms")
        
        return result
    
    async def test_memory_system_stress(self, user_count: int = 75, memory_ops_per_user: int = 20):
        """Test memory system under stress with concurrent access"""
        logger.info(f"🧠 Testing memory system stress: {user_count} users, {memory_ops_per_user} ops each")
        
        start_time = time.time()
        successful_operations = 0
        failed_operations = 0
        response_times = []
        errors = []
        
        async def memory_stress_worker(user_id: str):
            """Perform intensive memory operations for one user"""
            nonlocal successful_operations, failed_operations
            
            try:
                # Create realistic memory scenarios
                memory_scenarios = [
                    "I remember we talked about my job interview preparation",
                    "This reminds me of when I was learning to cook",
                    "I'm thinking about our conversation about travel plans",
                    "This is similar to when I was dealing with stress",
                    "I recall we discussed my fitness goals",
                    "This brings back our chat about creative projects",
                    "I'm reminded of when we talked about relationships",
                    "This connects to our discussion about learning new skills",
                    "I think about our conversation on personal growth",
                    "This relates to when we discussed career changes"
                ]
                
                for i in range(memory_ops_per_user):
                    operation_start = time.time()
                    
                    try:
                        message = memory_scenarios[i % len(memory_scenarios)]
                        
                        # Test memory analysis with realistic emotional context
                        connections = await self.memory_moments.analyze_conversation_for_memories(
                            user_id, f"memory_context_{i}", message, None
                        )
                        
                        operation_time = time.time() - operation_start
                        response_times.append(operation_time)
                        successful_operations += 1
                        
                        # Small delay to simulate processing
                        await asyncio.sleep(0.01)
                        
                    except Exception as e:
                        failed_operations += 1
                        errors.append(f"User {user_id} memory op {i}: {str(e)[:100]}")
                        
            except Exception as e:
                failed_operations += memory_ops_per_user
                errors.append(f"User {user_id} memory stress failed: {str(e)[:100]}")
        
        # Run concurrent memory stress testing
        user_ids = [f"memory_stress_user_{uuid.uuid4().hex[:6]}" for _ in range(user_count)]
        
        tasks = [memory_stress_worker(user_id) for user_id in user_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        total_operations = successful_operations + failed_operations
        
        # Calculate performance metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
        
        result = {
            "test_name": "memory_system_stress",
            "user_count": user_count,
            "memory_ops_per_user": memory_ops_per_user,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "duration_seconds": duration,
            "operations_per_second": total_operations / duration if duration > 0 else 0,
            "avg_response_time_ms": avg_response_time * 1000,
            "p95_response_time_ms": p95_response_time * 1000,
            "error_count": len(errors),
            "errors_sample": errors[:3]
        }
        
        logger.info(f"✅ Memory system stress: {successful_operations}/{total_operations} ops "
                   f"({result['success_rate']:.1%} success) in {duration:.1f}s, "
                   f"avg {result['avg_response_time_ms']:.1f}ms, p95 {result['p95_response_time_ms']:.1f}ms")
        
        return result
    
    async def test_engagement_analysis_load(self, user_count: int = 60, analyses_per_user: int = 25):
        """Test engagement engine under analysis load"""
        logger.info(f"💡 Testing engagement analysis load: {user_count} users, {analyses_per_user} analyses each")
        
        start_time = time.time()
        successful_operations = 0
        failed_operations = 0
        response_times = []
        errors = []
        
        async def engagement_load_worker(user_id: str):
            """Perform engagement analysis load testing for one user"""
            nonlocal successful_operations, failed_operations
            
            try:
                # Create engagement patterns from highly engaging to stagnant
                engagement_patterns = [
                    # Highly engaging
                    "This is absolutely fascinating! I want to learn everything about this topic!",
                    "I'm so excited about this opportunity! Tell me more about how I can get involved!",
                    "This completely changes my perspective! I never thought about it that way before!",
                    
                    # Moderately engaging
                    "That's really interesting. I'd like to understand more about the details.",
                    "I see what you mean. That makes a lot of sense when you explain it like that.",
                    "That's a good point. I hadn't considered that aspect before.",
                    
                    # Declining engagement
                    "Yeah, I guess that could work.",
                    "I suppose that's one way to look at it.",
                    "Sure, that seems reasonable.",
                    
                    # Low engagement
                    "Mm-hmm.",
                    "I see.",
                    "OK.",
                    
                    # Very low engagement
                    "Yeah...",
                    "Hmm...",
                    "Sure..."
                ]
                
                for i in range(analyses_per_user):
                    operation_start = time.time()
                    
                    try:
                        message = engagement_patterns[i % len(engagement_patterns)]
                        
                        # Test engagement analysis
                        analysis = await self.engagement_engine.analyze_conversation_engagement(
                            user_id, message, []  # Empty recent messages for simplicity
                        )
                        
                        operation_time = time.time() - operation_start
                        response_times.append(operation_time)
                        successful_operations += 1
                        
                        # Small delay to simulate processing
                        await asyncio.sleep(0.005)
                        
                    except Exception as e:
                        failed_operations += 1
                        errors.append(f"User {user_id} engagement analysis {i}: {str(e)[:100]}")
                        
            except Exception as e:
                failed_operations += analyses_per_user
                errors.append(f"User {user_id} engagement load failed: {str(e)[:100]}")
        
        # Run concurrent engagement analysis load testing
        user_ids = [f"engagement_load_user_{uuid.uuid4().hex[:6]}" for _ in range(user_count)]
        
        tasks = [engagement_load_worker(user_id) for user_id in user_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        total_operations = successful_operations + failed_operations
        
        # Calculate performance metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
        
        result = {
            "test_name": "engagement_analysis_load",
            "user_count": user_count,
            "analyses_per_user": analyses_per_user,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "duration_seconds": duration,
            "operations_per_second": total_operations / duration if duration > 0 else 0,
            "avg_response_time_ms": avg_response_time * 1000,
            "p95_response_time_ms": p95_response_time * 1000,
            "error_count": len(errors),
            "errors_sample": errors[:3]
        }
        
        logger.info(f"✅ Engagement analysis load: {successful_operations}/{total_operations} ops "
                   f"({result['success_rate']:.1%} success) in {duration:.1f}s, "
                   f"avg {result['avg_response_time_ms']:.1f}ms, p95 {result['p95_response_time_ms']:.1f}ms")
        
        return result
    
    async def test_integrated_system_scalability(self, user_count: int = 50, session_length: int = 15):
        """Test complete Phase 4 system scalability under realistic load"""
        logger.info(f"🔄 Testing integrated system scalability: {user_count} users, {session_length} interactions each")
        
        start_time = time.time()
        component_stats = {
            "thread_operations": {"success": 0, "failure": 0, "response_times": []},
            "memory_operations": {"success": 0, "failure": 0, "response_times": []},
            "engagement_operations": {"success": 0, "failure": 0, "response_times": []}
        }
        errors = []
        
        async def integrated_user_session(user_id: str):
            """Simulate a realistic integrated user session"""
            try:
                conversation_patterns = self.generate_conversation_patterns(1)[0]  # Get one pattern
                
                # Extend pattern to desired session length
                while len(conversation_patterns) < session_length:
                    follow_ups = [
                        "Can you tell me more about that?",
                        "That's interesting! What else should I consider?",
                        "I'm curious about your thoughts on this.",
                        "How would you approach this situation?",
                        "What has your experience been with this?",
                        "I'd love to hear more details about that."
                    ]
                    conversation_patterns.append(random.choice(follow_ups))
                
                for i, message in enumerate(conversation_patterns[:session_length]):
                    # Thread management operation
                    thread_start = time.time()
                    try:
                        await self.thread_manager.process_user_message(user_id, message, {})
                        component_stats["thread_operations"]["success"] += 1
                        component_stats["thread_operations"]["response_times"].append(time.time() - thread_start)
                    except Exception as e:
                        component_stats["thread_operations"]["failure"] += 1
                        errors.append(f"Thread {user_id}:{i}: {str(e)[:50]}")
                    
                    # Memory analysis operation
                    memory_start = time.time()
                    try:
                        await self.memory_moments.analyze_conversation_for_memories(
                            user_id, f"context_{i}", message, None
                        )
                        component_stats["memory_operations"]["success"] += 1
                        component_stats["memory_operations"]["response_times"].append(time.time() - memory_start)
                    except Exception as e:
                        component_stats["memory_operations"]["failure"] += 1
                        errors.append(f"Memory {user_id}:{i}: {str(e)[:50]}")
                    
                    # Engagement analysis operation
                    engagement_start = time.time()
                    try:
                        await self.engagement_engine.analyze_conversation_engagement(user_id, message, [])
                        component_stats["engagement_operations"]["success"] += 1
                        component_stats["engagement_operations"]["response_times"].append(time.time() - engagement_start)
                    except Exception as e:
                        component_stats["engagement_operations"]["failure"] += 1
                        errors.append(f"Engagement {user_id}:{i}: {str(e)[:50]}")
                    
                    # Realistic interaction delay
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                        
            except Exception as e:
                errors.append(f"Session {user_id}: {str(e)[:50]}")
        
        # Run integrated user sessions
        user_ids = [f"integrated_user_{uuid.uuid4().hex[:6]}" for _ in range(user_count)]
        
        await asyncio.gather(
            *[integrated_user_session(user_id) for user_id in user_ids],
            return_exceptions=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate comprehensive results
        total_operations = sum(
            stats["success"] + stats["failure"] 
            for stats in component_stats.values()
        )
        
        successful_operations = sum(
            stats["success"] 
            for stats in component_stats.values()
        )
        
        # Calculate average response times per component
        component_performance = {}
        for component, stats in component_stats.items():
            if stats["response_times"]:
                avg_time = statistics.mean(stats["response_times"])
                p95_time = sorted(stats["response_times"])[int(len(stats["response_times"]) * 0.95)]
                component_performance[component] = {
                    "avg_response_time_ms": avg_time * 1000,
                    "p95_response_time_ms": p95_time * 1000,
                    "success_rate": stats["success"] / (stats["success"] + stats["failure"]) if (stats["success"] + stats["failure"]) > 0 else 0
                }
        
        result = {
            "test_name": "integrated_system_scalability",
            "user_count": user_count,
            "session_length": session_length,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "duration_seconds": duration,
            "operations_per_second": total_operations / duration if duration > 0 else 0,
            "component_performance": component_performance,
            "error_count": len(errors),
            "errors_sample": errors[:5]
        }
        
        logger.info(f"✅ Integrated system scalability: {successful_operations}/{total_operations} ops "
                   f"({result['success_rate']:.1%} success) in {duration:.1f}s, "
                   f"{result['operations_per_second']:.1f} ops/sec")
        
        for component, perf in component_performance.items():
            logger.info(f"   📊 {component}: {perf['success_rate']:.1%} success, "
                       f"avg {perf['avg_response_time_ms']:.1f}ms, p95 {perf['p95_response_time_ms']:.1f}ms")
        
        return result


async def run_production_load_tests():
    """Run comprehensive production load tests for Phase 4"""
    logger.info("🚀 Starting Phase 4 Production Load Testing Suite")
    logger.info("="*80)
    
    tester = Phase4ProductionLoadTester()
    
    # Test 1: Concurrent Conversations
    logger.info("\n" + "="*80)
    logger.info("TEST 1: CONCURRENT CONVERSATIONS")
    logger.info("="*80)
    conversations_result = await tester.test_concurrent_conversations(100, 3)
    
    # Test 2: Memory System Stress
    logger.info("\n" + "="*80)
    logger.info("TEST 2: MEMORY SYSTEM STRESS")
    logger.info("="*80)
    memory_result = await tester.test_memory_system_stress(75, 20)
    
    # Test 3: Engagement Analysis Load
    logger.info("\n" + "="*80)
    logger.info("TEST 3: ENGAGEMENT ANALYSIS LOAD")
    logger.info("="*80)
    engagement_result = await tester.test_engagement_analysis_load(60, 25)
    
    # Test 4: Integrated System Scalability
    logger.info("\n" + "="*80)
    logger.info("TEST 4: INTEGRATED SYSTEM SCALABILITY")
    logger.info("="*80)
    integrated_result = await tester.test_integrated_system_scalability(50, 15)
    
    # Final Summary
    logger.info("\n" + "="*80)
    logger.info("🎉 PHASE 4 PRODUCTION LOAD TEST SUMMARY")
    logger.info("="*80)
    
    all_results = [conversations_result, memory_result, engagement_result, integrated_result]
    
    for result in all_results:
        test_name = result["test_name"]
        success_rate = result["success_rate"]
        ops_per_sec = result["operations_per_second"]
        avg_response = result.get("avg_response_time_ms", 0)
        
        status = "✅ PASS" if success_rate >= 0.95 else "⚠️ MARGINAL" if success_rate >= 0.90 else "❌ FAIL"
        
        logger.info(f"{status} {test_name:30} - {success_rate:6.1%} success, "
                   f"{ops_per_sec:6.1f} ops/sec, avg {avg_response:5.1f}ms")
    
    # Overall assessment
    overall_success_rate = sum(r["success_rate"] for r in all_results) / len(all_results)
    logger.info("="*80)
    logger.info(f"🎯 OVERALL PHASE 4 SYSTEM PERFORMANCE: {overall_success_rate:.1%}")
    
    if overall_success_rate >= 0.95:
        logger.info("🏆 EXCELLENT - System ready for production deployment!")
    elif overall_success_rate >= 0.90:
        logger.info("👍 GOOD - System stable with minor optimizations needed")
    else:
        logger.info("⚠️ NEEDS IMPROVEMENT - Address performance issues before production")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(run_production_load_tests())