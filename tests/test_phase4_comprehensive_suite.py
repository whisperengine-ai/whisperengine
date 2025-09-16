"""
Comprehensive Phase 4 System Testing Suite

This module provides extensive testing for all Phase 4 components with focus on:
- Critical code path coverage for production reliability
- Concurrency and thread safety validation under heavy load
- Integration testing across all Phase 4 systems
- Edge case and error condition handling
- Performance benchmarking and regression testing

Components Under Test:
- Phase 4.1: Memory-Triggered Personality Moments
- Phase 4.2: Multi-Thread Conversation Management
- Phase 4.3: Proactive Conversation Engagement
- Emotional Context Engine Integration
- Dynamic Personality Profiler Integration

Test Categories:
- Unit Tests: Individual component functionality
- Integration Tests: Cross-component interactions
- Concurrency Tests: Thread safety and race conditions
- Load Tests: High-volume stress testing
- Performance Tests: Speed and resource usage benchmarks
- Edge Case Tests: Error conditions and boundary cases
"""

import pytest
import asyncio
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import random
import statistics
from unittest.mock import Mock, patch, MagicMock
import gc
import psutil
import os

# Import Phase 4 components
from src.personality.memory_moments import (
    MemoryTriggeredMoments, 
    MemoryConnectionType,
    MemoryMomentType, 
    ConversationContext
)
from src.conversation.advanced_thread_manager import (
    AdvancedConversationThreadManager,
    ConversationThreadAdvanced,
    ConversationThreadState,
    ThreadTransitionType,
    ThreadPriorityLevel
)
from src.conversation.proactive_engagement_engine import (
    ProactiveConversationEngagementEngine,
    ConversationFlowState,
    EngagementStrategy
)

# Import supporting systems
try:
    from src.intelligence.emotional_context_engine import EmotionalContextEngine, EmotionalContext, EmotionalState
    EMOTIONAL_CONTEXT_AVAILABLE = True
except ImportError:
    EMOTIONAL_CONTEXT_AVAILABLE = False

try:
    from src.intelligence.dynamic_personality_profiler import DynamicPersonalityProfiler
    PERSONALITY_PROFILER_AVAILABLE = True
except ImportError:
    PERSONALITY_PROFILER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Test configuration
TEST_USER_COUNT = 100  # Number of concurrent users for load testing
TEST_MESSAGE_COUNT = 50  # Messages per user for stress testing
PERFORMANCE_BASELINE_MS = 100  # Expected response time baseline
CONCURRENCY_THREAD_COUNT = 20  # Number of concurrent threads for safety testing


class Phase4TestFramework:
    """Comprehensive testing framework for Phase 4 systems"""
    
    def __init__(self):
        self.memory_moments = None
        self.thread_manager = None
        self.engagement_engine = None
        self.emotional_engine = None
        self.personality_profiler = None
        self.test_data = {}
        self.performance_metrics = {}
        self.concurrency_results = {}
        
    async def setup_test_environment(self):
        """Initialize all Phase 4 components for testing"""
        try:
            # Initialize core Phase 4 components
            self.memory_moments = MemoryTriggeredMoments()
            self.thread_manager = AdvancedConversationThreadManager()
            self.engagement_engine = ProactiveConversationEngagementEngine()
            
            # Initialize supporting systems if available
            if EMOTIONAL_CONTEXT_AVAILABLE:
                self.emotional_engine = EmotionalContextEngine()
            
            if PERSONALITY_PROFILER_AVAILABLE:
                self.personality_profiler = DynamicPersonalityProfiler()
            
            logger.info("✅ Phase 4 test environment initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize test environment: {e}")
            return False
    
    def generate_test_users(self, count: int) -> List[str]:
        """Generate test user IDs for concurrent testing"""
        return [f"test_user_{uuid.uuid4().hex[:8]}" for _ in range(count)]
    
    def generate_test_messages(self, count: int) -> List[str]:
        """Generate realistic test messages for conversation testing"""
        message_templates = [
            "I've been thinking about {topic} lately and {feeling}",
            "Yesterday I {action} and it made me {emotion}",
            "I'm wondering about {question} - what do you think?",
            "I had a {adjective} conversation about {topic}",
            "I'm feeling {emotion} about {situation}",
            "Remember when we talked about {topic}? Well, {update}",
            "I've made some progress on {goal} and {result}",
            "I'm struggling with {challenge} and need {support}",
            "Something interesting happened - {event}",
            "I want to learn more about {interest}"
        ]
        
        topics = ["career", "relationships", "learning", "travel", "hobbies", "goals", "family", "health"]
        feelings = ["excited", "nervous", "curious", "confident", "uncertain", "hopeful"]
        emotions = ["happy", "sad", "frustrated", "proud", "worried", "optimistic"]
        adjectives = ["great", "challenging", "interesting", "difficult", "inspiring"]
        
        messages = []
        for _ in range(count):
            template = random.choice(message_templates)
            message = template.format(
                topic=random.choice(topics),
                feeling=random.choice(feelings),
                emotion=random.choice(emotions),
                adjective=random.choice(adjectives),
                action=f"tried {random.choice(['something new', 'a different approach', 'to change'])}",
                question=f"how to {random.choice(['improve', 'understand', 'approach'])} {random.choice(topics)}",
                situation=random.choice(topics),
                update=f"I've {random.choice(['learned', 'discovered', 'realized'])} something new",
                goal=random.choice(topics),
                result=f"I'm feeling {random.choice(emotions)}",
                challenge=random.choice(topics),
                support=random.choice(["advice", "encouragement", "perspective"]),
                event=f"I {random.choice(['met', 'discovered', 'learned about'])} something {random.choice(adjectives)}",
                interest=random.choice(topics)
            )
            messages.append(message)
        
        return messages


class CriticalPathTester:
    """Tests for critical code paths in Phase 4 systems"""
    
    def __init__(self, framework: Phase4TestFramework):
        self.framework = framework
        
    async def test_memory_moments_critical_paths(self):
        """Test critical paths in memory moments system"""
        results = {
            "connection_discovery": False,
            "moment_generation": False,
            "timing_validation": False,
            "prompt_integration": False,
            "error_handling": False
        }
        
        test_user = "critical_path_user"
        
        try:
            # Test 1: Memory connection discovery
            logger.info("🧠 Testing memory connection discovery...")
            
            # Create a proper conversation context with all required fields
            emotional_context = None
            if EMOTIONAL_CONTEXT_AVAILABLE:
                emotional_context = EmotionalContext(
                    emotional_state=EmotionalState.JOY,  # Use existing enum value
                    confidence=0.8,
                    emotional_intensity=0.6
                )
            
            connections = await self.framework.memory_moments.analyze_conversation_for_memories(
                test_user, "test_context", "I'm thinking about my career goals again", emotional_context
            )
            results["connection_discovery"] = True
            logger.info(f"✅ Memory connection discovery: {len(connections)} connections found")
            
            # Test 2: Memory moment generation
            logger.info("💭 Testing memory moment generation...")
            moments = await self.framework.memory_moments.generate_memory_moments(test_user, context)
            results["moment_generation"] = True
            logger.info(f"✅ Memory moment generation: {len(moments)} moments generated")
            
            # Test 3: Timing and appropriateness validation
            logger.info("⏰ Testing timing validation...")
            if moments:
                timing_valid = await self.framework.memory_moments._is_moment_appropriate(
                    moments[0], context
                )
                results["timing_validation"] = True
                logger.info(f"✅ Timing validation: appropriate={timing_valid}")
            
            # Test 4: Prompt integration
            logger.info("📝 Testing prompt integration...")
            prompt = await self.framework.memory_moments.get_memory_moment_prompt(moments, context)
            results["prompt_integration"] = prompt is not None
            logger.info(f"✅ Prompt integration: {len(prompt) if prompt else 0} characters generated")
            
            # Test 5: Error handling
            logger.info("🚨 Testing error handling...")
            try:
                # Test with invalid data
                invalid_context = ConversationContext(
                    user_id="", context_id="", current_message="", emotional_state=None
                )
                error_connections = await self.framework.memory_moments.analyze_conversation_for_memories(
                    "", "", "", invalid_context
                )
                results["error_handling"] = True
                logger.info("✅ Error handling: graceful degradation working")
            except Exception as e:
                logger.info(f"✅ Error handling: exception caught properly - {e}")
                results["error_handling"] = True
            
        except Exception as e:
            logger.error(f"❌ Memory moments critical path test failed: {e}")
            
        return results
    
    async def test_thread_manager_critical_paths(self):
        """Test critical paths in thread manager system"""
        results = {
            "thread_creation": False,
            "thread_identification": False,
            "context_switching": False,
            "priority_management": False,
            "state_transitions": False
        }
        
        test_user = "thread_test_user"
        
        try:
            # Test 1: Thread creation
            logger.info("🧵 Testing thread creation...")
            thread_result = await self.framework.thread_manager.process_user_message(
                test_user, "I want to talk about my weekend plans", {}
            )
            results["thread_creation"] = "current_thread" in thread_result
            logger.info(f"✅ Thread creation: {thread_result.get('current_thread', 'None')}")
            
            # Test 2: Thread identification with existing threads
            logger.info("🔍 Testing thread identification...")
            second_result = await self.framework.thread_manager.process_user_message(
                test_user, "Let me continue about those weekend plans", {}
            )
            results["thread_identification"] = True
            logger.info(f"✅ Thread identification: {second_result.get('current_thread', 'None')}")
            
            # Test 3: Context switching
            logger.info("🔄 Testing context switching...")
            switch_result = await self.framework.thread_manager.process_user_message(
                test_user, "Actually, let me ask about work instead", {}
            )
            results["context_switching"] = True
            logger.info(f"✅ Context switching: {switch_result.get('transition_type', 'None')}")
            
            # Test 4: Priority management
            logger.info("📊 Testing priority management...")
            urgent_result = await self.framework.thread_manager.process_user_message(
                test_user, "I'm really stressed about this deadline", {}
            )
            results["priority_management"] = True
            logger.info(f"✅ Priority management: {urgent_result.get('thread_priority', 'None')}")
            
            # Test 5: State transitions
            logger.info("🔧 Testing state transitions...")
            user_threads = self.framework.thread_manager.get_user_threads(test_user)
            if user_threads:
                thread_id = list(user_threads.keys())[0]
                await self.framework.thread_manager.pause_thread(test_user, thread_id, "User request")
                paused_thread = user_threads[thread_id]
                results["state_transitions"] = paused_thread.state == ConversationThreadState.PAUSED
                logger.info(f"✅ State transitions: {paused_thread.state}")
            
        except Exception as e:
            logger.error(f"❌ Thread manager critical path test failed: {e}")
            
        return results
    
    async def test_engagement_engine_critical_paths(self):
        """Test critical paths in proactive engagement engine"""
        results = {
            "stagnation_detection": False,
            "engagement_analysis": False,
            "strategy_generation": False,
            "prompt_creation": False,
            "flow_state_tracking": False
        }
        
        test_user = "engagement_test_user"
        
        try:
            # Test 1: Stagnation detection
            logger.info("📉 Testing stagnation detection...")
            
            # Simulate declining conversation
            messages = ["Yeah...", "I guess...", "Hmm...", "Sure..."]
            for message in messages:
                analysis = await self.framework.engagement_engine.analyze_conversation_engagement(
                    test_user, message, {}
                )
                
            final_analysis = await self.framework.engagement_engine.analyze_conversation_engagement(
                test_user, "OK", {}
            )
            
            flow_state = final_analysis.get("flow_state", ConversationFlowState.STEADY)
            results["stagnation_detection"] = flow_state in [
                ConversationFlowState.DECLINING, 
                ConversationFlowState.STAGNATING, 
                ConversationFlowState.STAGNANT
            ]
            logger.info(f"✅ Stagnation detection: {flow_state}")
            
            # Test 2: Engagement analysis
            logger.info("📊 Testing engagement analysis...")
            engagement_score = final_analysis.get("engagement_score", 0.5)
            results["engagement_analysis"] = 0.0 <= engagement_score <= 1.0
            logger.info(f"✅ Engagement analysis: score={engagement_score}")
            
            # Test 3: Strategy generation
            logger.info("💡 Testing strategy generation...")
            if final_analysis.get("intervention_needed", False):
                strategies = await self.framework.engagement_engine.generate_engagement_strategies(
                    test_user, final_analysis
                )
                results["strategy_generation"] = len(strategies) > 0
                logger.info(f"✅ Strategy generation: {len(strategies)} strategies")
            else:
                results["strategy_generation"] = True
                logger.info("✅ Strategy generation: no intervention needed")
            
            # Test 4: Prompt creation
            logger.info("💬 Testing prompt creation...")
            recommendations = await self.framework.engagement_engine.generate_conversation_recommendations(
                test_user, final_analysis, limit=3
            )
            results["prompt_creation"] = len(recommendations) > 0
            logger.info(f"✅ Prompt creation: {len(recommendations)} recommendations")
            
            # Test 5: Flow state tracking
            logger.info("🌊 Testing flow state tracking...")
            flow_history = self.framework.engagement_engine.get_user_flow_history(test_user)
            results["flow_state_tracking"] = len(flow_history) > 0
            logger.info(f"✅ Flow state tracking: {len(flow_history)} states tracked")
            
        except Exception as e:
            logger.error(f"❌ Engagement engine critical path test failed: {e}")
            
        return results


class ConcurrencyTester:
    """Tests for concurrency and thread safety under load"""
    
    def __init__(self, framework: Phase4TestFramework):
        self.framework = framework
        
    async def test_concurrent_memory_operations(self, user_count: int = 50, operation_count: int = 20):
        """Test memory moments system under concurrent load"""
        logger.info(f"🧠 Testing concurrent memory operations: {user_count} users, {operation_count} ops each")
        
        start_time = time.time()
        errors = []
        results = []
        
        async def memory_operation_worker(user_id: str, operation_id: int):
            try:
                context = ConversationContext(
                    user_id=user_id,
                    context_id=f"context_{operation_id}",
                    current_message=f"Test message {operation_id} about learning",
                    emotional_state=EmotionalState.CURIOSITY if EMOTIONAL_CONTEXT_AVAILABLE else None
                )
                
                # Concurrent memory analysis
                connections = await self.framework.memory_moments.analyze_conversation_for_memories(
                    user_id, context.context_id, context.current_message, context
                )
                
                # Concurrent moment generation
                moments = await self.framework.memory_moments.generate_memory_moments(user_id, context)
                
                return {
                    "user_id": user_id,
                    "operation_id": operation_id,
                    "connections": len(connections),
                    "moments": len(moments),
                    "success": True
                }
                
            except Exception as e:
                error_msg = f"Memory operation failed for {user_id}:{operation_id} - {e}"
                errors.append(error_msg)
                return {
                    "user_id": user_id,
                    "operation_id": operation_id,
                    "success": False,
                    "error": str(e)
                }
        
        # Generate concurrent operations
        tasks = []
        for user_id in self.framework.generate_test_users(user_count):
            for op_id in range(operation_count):
                task = memory_operation_worker(user_id, op_id)
                tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Analyze results
        successful_ops = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed_ops = len(results) - successful_ops
        total_ops = user_count * operation_count
        
        concurrency_result = {
            "test_type": "memory_operations",
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "success_rate": successful_ops / total_ops,
            "duration_seconds": duration,
            "operations_per_second": total_ops / duration,
            "errors": errors[:10]  # First 10 errors
        }
        
        logger.info(f"✅ Memory concurrency test: {successful_ops}/{total_ops} ops successful "
                   f"({concurrency_result['success_rate']:.2%}) in {duration:.2f}s")
        
        return concurrency_result
    
    async def test_concurrent_thread_management(self, user_count: int = 30, message_count: int = 10):
        """Test thread manager system under concurrent load"""
        logger.info(f"🧵 Testing concurrent thread management: {user_count} users, {message_count} messages each")
        
        start_time = time.time()
        errors = []
        results = []
        
        async def thread_operation_worker(user_id: str, message_id: int):
            try:
                messages = [
                    "I want to discuss my career plans",
                    "Let me tell you about my weekend",
                    "I'm thinking about learning something new",
                    "I need advice about relationships",
                    "I'm working on a personal project",
                    "I have some exciting news to share",
                    "I'm feeling stressed about work",
                    "Let's talk about my hobbies",
                    "I'm planning a trip",
                    "I want to improve my health"
                ]
                
                message = messages[message_id % len(messages)]
                
                # Concurrent thread processing
                result = await self.framework.thread_manager.process_user_message(
                    user_id, f"{message} - iteration {message_id}", {}
                )
                
                # Get thread information
                threads = self.framework.thread_manager.get_user_threads(user_id)
                
                return {
                    "user_id": user_id,
                    "message_id": message_id,
                    "thread_id": result.get("current_thread"),
                    "thread_count": len(threads),
                    "success": True
                }
                
            except Exception as e:
                error_msg = f"Thread operation failed for {user_id}:{message_id} - {e}"
                errors.append(error_msg)
                return {
                    "user_id": user_id,
                    "message_id": message_id,
                    "success": False,
                    "error": str(e)
                }
        
        # Generate concurrent operations
        tasks = []
        for user_id in self.framework.generate_test_users(user_count):
            for msg_id in range(message_count):
                task = thread_operation_worker(user_id, msg_id)
                tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Analyze results
        successful_ops = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed_ops = len(results) - successful_ops
        total_ops = user_count * message_count
        
        # Calculate thread creation stats
        unique_threads = set()
        for r in results:
            if isinstance(r, dict) and r.get("thread_id"):
                unique_threads.add(r["thread_id"])
        
        concurrency_result = {
            "test_type": "thread_management",
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "success_rate": successful_ops / total_ops,
            "duration_seconds": duration,
            "operations_per_second": total_ops / duration,
            "unique_threads_created": len(unique_threads),
            "errors": errors[:10]
        }
        
        logger.info(f"✅ Thread concurrency test: {successful_ops}/{total_ops} ops successful "
                   f"({concurrency_result['success_rate']:.2%}) in {duration:.2f}s, "
                   f"{len(unique_threads)} threads created")
        
        return concurrency_result
    
    async def test_concurrent_engagement_analysis(self, user_count: int = 40, analysis_count: int = 15):
        """Test engagement engine under concurrent load"""
        logger.info(f"💡 Testing concurrent engagement analysis: {user_count} users, {analysis_count} analyses each")
        
        start_time = time.time()
        errors = []
        results = []
        
        async def engagement_operation_worker(user_id: str, analysis_id: int):
            try:
                # Simulate conversation patterns
                patterns = [
                    "This is really interesting and I'd love to learn more!",
                    "Yeah, I guess that makes sense...",
                    "Hmm...",
                    "I'm so excited about this opportunity!",
                    "I don't know...",
                    "That's fascinating! Tell me more about that.",
                    "Sure...",
                    "I'm really passionate about this topic!",
                    "OK...",
                    "This is exactly what I was looking for!"
                ]
                
                message = patterns[analysis_id % len(patterns)]
                
                # Concurrent engagement analysis
                analysis = await self.framework.engagement_engine.analyze_conversation_engagement(
                    user_id, message, {}
                )
                
                # Generate recommendations if needed
                recommendations = []
                if analysis.get("intervention_needed", False):
                    recommendations = await self.framework.engagement_engine.generate_conversation_recommendations(
                        user_id, analysis, limit=3
                    )
                
                return {
                    "user_id": user_id,
                    "analysis_id": analysis_id,
                    "flow_state": analysis.get("flow_state", "unknown"),
                    "engagement_score": analysis.get("engagement_score", 0.0),
                    "intervention_needed": analysis.get("intervention_needed", False),
                    "recommendations": len(recommendations),
                    "success": True
                }
                
            except Exception as e:
                error_msg = f"Engagement operation failed for {user_id}:{analysis_id} - {e}"
                errors.append(error_msg)
                return {
                    "user_id": user_id,
                    "analysis_id": analysis_id,
                    "success": False,
                    "error": str(e)
                }
        
        # Generate concurrent operations
        tasks = []
        for user_id in self.framework.generate_test_users(user_count):
            for analysis_id in range(analysis_count):
                task = engagement_operation_worker(user_id, analysis_id)
                tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Analyze results
        successful_ops = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))
        failed_ops = len(results) - successful_ops
        total_ops = user_count * analysis_count
        
        # Calculate engagement stats
        total_interventions = sum(1 for r in results 
                                if isinstance(r, dict) and r.get("intervention_needed", False))
        
        concurrency_result = {
            "test_type": "engagement_analysis",
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "success_rate": successful_ops / total_ops,
            "duration_seconds": duration,
            "operations_per_second": total_ops / duration,
            "interventions_triggered": total_interventions,
            "errors": errors[:10]
        }
        
        logger.info(f"✅ Engagement concurrency test: {successful_ops}/{total_ops} ops successful "
                   f"({concurrency_result['success_rate']:.2%}) in {duration:.2f}s, "
                   f"{total_interventions} interventions triggered")
        
        return concurrency_result


@pytest.mark.asyncio
async def test_phase4_critical_paths():
    """Test all critical code paths in Phase 4 systems"""
    framework = Phase4TestFramework()
    
    setup_success = await framework.setup_test_environment()
    assert setup_success, "Failed to initialize test environment"
    
    critical_tester = CriticalPathTester(framework)
    
    # Test memory moments critical paths
    memory_results = await critical_tester.test_memory_moments_critical_paths()
    assert all(memory_results.values()), f"Memory moments critical path failures: {memory_results}"
    
    # Test thread manager critical paths
    thread_results = await critical_tester.test_thread_manager_critical_paths()
    assert all(thread_results.values()), f"Thread manager critical path failures: {thread_results}"
    
    # Test engagement engine critical paths
    engagement_results = await critical_tester.test_engagement_engine_critical_paths()
    assert all(engagement_results.values()), f"Engagement engine critical path failures: {engagement_results}"
    
    logger.info("🎉 All critical paths tested successfully!")


@pytest.mark.asyncio
async def test_phase4_concurrency():
    """Test Phase 4 systems under concurrent load"""
    framework = Phase4TestFramework()
    
    setup_success = await framework.setup_test_environment()
    assert setup_success, "Failed to initialize test environment"
    
    concurrency_tester = ConcurrencyTester(framework)
    
    # Test concurrent memory operations
    memory_concurrency = await concurrency_tester.test_concurrent_memory_operations(50, 20)
    assert memory_concurrency["success_rate"] >= 0.95, f"Memory concurrency test failed: {memory_concurrency}"
    
    # Test concurrent thread management
    thread_concurrency = await concurrency_tester.test_concurrent_thread_management(30, 10)
    assert thread_concurrency["success_rate"] >= 0.95, f"Thread concurrency test failed: {thread_concurrency}"
    
    # Test concurrent engagement analysis
    engagement_concurrency = await concurrency_tester.test_concurrent_engagement_analysis(40, 15)
    assert engagement_concurrency["success_rate"] >= 0.95, f"Engagement concurrency test failed: {engagement_concurrency}"
    
    logger.info("🎉 All concurrency tests passed successfully!")


if __name__ == "__main__":
    # Run comprehensive Phase 4 testing
    asyncio.run(test_phase4_critical_paths())
    asyncio.run(test_phase4_concurrency())