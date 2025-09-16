"""
Phase Integration Optimizer

This module optimizes the integration between AI phases to improve performance,
data consistency, and reduce processing overhead while maintaining quality.

Key Optimizations:
1. Parallel phase execution where possible
2. Intelligent caching of phase results
3. Standardized inter-phase data structures
4. Performance monitoring and adaptive optimization
5. Graceful degradation when phases fail
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Levels of optimization to apply"""

    MINIMAL = "minimal"  # Basic optimizations only
    BALANCED = "balanced"  # Balance performance vs quality
    AGGRESSIVE = "aggressive"  # Maximum performance optimization


class PhaseExecutionStrategy(Enum):
    """Strategies for executing phases"""

    SEQUENTIAL = "sequential"  # Execute phases one after another
    PARALLEL = "parallel"  # Execute phases in parallel where possible
    ADAPTIVE = "adaptive"  # Adapt based on system load and context


@dataclass
class PhaseResult:
    """Standardized result structure for all phases"""

    phase_name: str
    success: bool
    data: dict[str, Any]
    processing_time: float
    error_message: str | None = None
    cache_hit: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegratedPhaseContext:
    """Unified context structure for integrated phase processing"""

    user_id: str
    message: str
    conversation_context: list[dict[str, Any]] = field(default_factory=list)
    phase_results: dict[str, PhaseResult] = field(default_factory=dict)
    processing_metadata: dict[str, Any] = field(default_factory=dict)
    optimization_stats: dict[str, Any] = field(default_factory=dict)


class PhaseIntegrationOptimizer:
    """
    Optimizes the integration between Phase 2 (Emotional Intelligence),
    Phase 3 (Memory Networks), and Phase 4 (Human-Like Integration)
    """

    def __init__(
        self,
        phase2_integration=None,
        phase3_memory_networks=None,
        memory_manager=None,
        llm_client=None,
        optimization_level: OptimizationLevel = OptimizationLevel.BALANCED,
        execution_strategy: PhaseExecutionStrategy = PhaseExecutionStrategy.ADAPTIVE,
        enable_caching: bool = True,
        cache_ttl_seconds: int = 300,
    ):
        """
        Initialize the phase integration optimizer

        Args:
            phase2_integration: Phase 2 emotional intelligence integration
            phase3_memory_networks: Phase 3 memory networks
            memory_manager: Memory manager for storage operations
            llm_client: LLM client for AI operations
            optimization_level: Level of optimization to apply
            execution_strategy: Strategy for executing phases
            enable_caching: Whether to enable result caching
            cache_ttl_seconds: Time-to-live for cached results
        """
        self.phase2_integration = phase2_integration
        self.phase3_memory_networks = phase3_memory_networks
        self.memory_manager = memory_manager
        self.llm_client = llm_client

        self.optimization_level = optimization_level
        self.execution_strategy = execution_strategy
        self.enable_caching = enable_caching
        self.cache_ttl_seconds = cache_ttl_seconds

        # Performance tracking
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "parallel_executions": 0,
            "phase_timings": {},
            "optimization_savings": 0.0,
        }

        # Result cache: message_hash -> {timestamp, results}
        self.result_cache = {}

        # Phase dependency mapping
        self.phase_dependencies = {
            "phase2": [],  # Phase 2 has no dependencies
            "phase3": ["phase2"],  # Phase 3 can benefit from Phase 2 results
            "memory_optimization": ["phase2"],  # Memory optimization uses emotional context
        }

        logger.info(
            f"🔧 PhaseIntegrationOptimizer initialized with {optimization_level.value} optimization "
            f"and {execution_strategy.value} execution strategy"
        )

    async def process_integrated_phases(
        self, user_id: str, message: str, conversation_context: list[dict] | None = None
    ) -> IntegratedPhaseContext:
        """
        Process all phases with optimization strategies applied

        Args:
            user_id: User identifier
            message: User message content
            conversation_context: Conversation context for processing

        Returns:
            IntegratedPhaseContext with optimized results from all phases
        """
        start_time = time.time()
        self.performance_stats["total_requests"] += 1

        # Initialize context
        context = IntegratedPhaseContext(
            user_id=user_id,
            message=message,
            conversation_context=conversation_context or [],
            processing_metadata={
                "start_time": datetime.now(UTC),
                "optimization_level": self.optimization_level.value,
                "execution_strategy": self.execution_strategy.value,
            },
        )

        try:
            # Step 1: Check cache for recent similar results
            if self.enable_caching:
                cached_result = await self._check_result_cache(user_id, message)
                if cached_result:
                    logger.debug(f"✅ Cache hit for user {user_id}, returning cached results")
                    context.phase_results = cached_result
                    context.optimization_stats["cache_hit"] = True
                    self.performance_stats["cache_hits"] += 1
                    return context

            # Step 2: Determine execution strategy based on optimization level
            phases_to_execute = await self._determine_phases_to_execute(message, context)

            # Step 3: Execute phases using selected strategy
            if self.execution_strategy == PhaseExecutionStrategy.PARALLEL:
                await self._execute_phases_parallel(phases_to_execute, context)
            elif self.execution_strategy == PhaseExecutionStrategy.SEQUENTIAL:
                await self._execute_phases_sequential(phases_to_execute, context)
            else:  # ADAPTIVE
                await self._execute_phases_adaptive(phases_to_execute, context)

            # Step 4: Optimize and standardize results
            await self._optimize_phase_results(context)

            # Step 5: Cache results if enabled
            if self.enable_caching:
                await self._cache_results(user_id, message, context.phase_results)

            # Step 6: Update performance statistics
            total_time = time.time() - start_time
            context.processing_metadata["total_processing_time"] = total_time
            context.optimization_stats["processing_time"] = total_time

            self._update_performance_stats(context)

            logger.info(
                f"✅ Integrated phase processing completed for user {user_id} "
                f"in {total_time:.3f}s (phases: {list(context.phase_results.keys())})"
            )

            return context

        except Exception as e:
            logger.error(f"❌ Integrated phase processing failed for user {user_id}: {e}")
            context.processing_metadata["error"] = str(e)
            return context

    async def _determine_phases_to_execute(
        self, message: str, context: IntegratedPhaseContext
    ) -> list[str]:
        """Determine which phases to execute based on optimization level"""

        base_phases = []

        # Always include Phase 2 if available (emotional intelligence is core)
        if self.phase2_integration:
            base_phases.append("phase2")

        # Include Phase 3 based on optimization level
        if self.phase3_memory_networks:
            if self.optimization_level == OptimizationLevel.MINIMAL:
                # Only run Phase 3 for complex queries
                if len(message.split()) > 10 or any(
                    word in message.lower() for word in ["remember", "recall", "before", "history"]
                ):
                    base_phases.append("phase3")
            else:
                base_phases.append("phase3")

        # Include memory optimization if memory manager available
        if self.memory_manager:
            base_phases.append("memory_optimization")

        logger.debug(f"Selected phases for execution: {base_phases}")
        return base_phases

    async def _execute_phases_parallel(self, phases: list[str], context: IntegratedPhaseContext):
        """Execute phases in parallel where dependencies allow"""

        # Group phases by dependency level
        phase_groups = self._group_phases_by_dependencies(phases)

        for group_level, phase_group in enumerate(phase_groups):
            if not phase_group:
                continue

            logger.debug(f"Executing phase group {group_level}: {phase_group}")

            # Create tasks for parallel execution within the group
            tasks = []
            for phase in phase_group:
                task = self._execute_single_phase(phase, context)
                tasks.append(task)

            # Execute all phases in this group in parallel
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for i, result in enumerate(results):
                    phase_name = phase_group[i]
                    if isinstance(result, Exception):
                        logger.error(f"Phase {phase_name} failed: {result}")
                        context.phase_results[phase_name] = PhaseResult(
                            phase_name=phase_name,
                            success=False,
                            data={},
                            processing_time=0.0,
                            error_message=str(result),
                        )
                    elif isinstance(result, PhaseResult):
                        context.phase_results[phase_name] = result
                    else:
                        logger.warning(
                            f"Unexpected result type for phase {phase_name}: {type(result)}"
                        )

        self.performance_stats["parallel_executions"] += 1

    async def _execute_phases_sequential(self, phases: list[str], context: IntegratedPhaseContext):
        """Execute phases sequentially in dependency order"""

        # Sort phases by dependencies
        sorted_phases = self._sort_phases_by_dependencies(phases)

        for phase in sorted_phases:
            logger.debug(f"Executing phase: {phase}")
            result = await self._execute_single_phase(phase, context)
            context.phase_results[phase] = result

            # Allow subsequent phases to use results from previous phases
            context.processing_metadata[f"{phase}_completed"] = True

    async def _execute_phases_adaptive(self, phases: list[str], context: IntegratedPhaseContext):
        """Adaptively choose execution strategy based on system load and context"""

        # Simple heuristic: use parallel for short messages, sequential for complex ones
        message_complexity = len(context.message.split()) + len(context.conversation_context)

        if message_complexity < 20 and len(phases) > 1:
            # Use parallel execution for simple messages
            logger.debug("Using parallel execution for simple message")
            await self._execute_phases_parallel(phases, context)
        else:
            # Use sequential execution for complex messages
            logger.debug("Using sequential execution for complex message")
            await self._execute_phases_sequential(phases, context)

    async def _execute_single_phase(
        self, phase_name: str, context: IntegratedPhaseContext
    ) -> PhaseResult:
        """Execute a single phase and return standardized result"""

        start_time = time.time()

        try:
            if phase_name == "phase2":
                return await self._execute_phase2(context, start_time)
            elif phase_name == "phase3":
                return await self._execute_phase3(context, start_time)
            elif phase_name == "memory_optimization":
                return await self._execute_memory_optimization(context, start_time)
            else:
                raise ValueError(f"Unknown phase: {phase_name}")

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Phase {phase_name} execution failed: {e}")
            return PhaseResult(
                phase_name=phase_name,
                success=False,
                data={},
                processing_time=processing_time,
                error_message=str(e),
            )

    async def _execute_phase2(
        self, context: IntegratedPhaseContext, start_time: float
    ) -> PhaseResult:
        """Execute Phase 2 (Emotional Intelligence)"""

        if not self.phase2_integration:
            raise ValueError("Phase 2 integration not available")

        # Prepare Phase 2 context with optimizations
        phase2_context = {
            "user_id": context.user_id,
            "message_length": len(context.message),
            "conversation_depth": len(context.conversation_context),
            "optimization_mode": self.optimization_level.value,
        }

        # Execute Phase 2
        results = await self.phase2_integration.process_message_with_emotional_intelligence(
            user_id=context.user_id, message=context.message, conversation_context=phase2_context
        )

        processing_time = time.time() - start_time

        return PhaseResult(
            phase_name="phase2",
            success=True,
            data=results,
            processing_time=processing_time,
            metadata={"optimization_applied": True},
        )

    async def _execute_phase3(
        self, context: IntegratedPhaseContext, start_time: float
    ) -> PhaseResult:
        """Execute Phase 3 (Memory Networks)"""

        if not self.phase3_memory_networks or not self.memory_manager:
            raise ValueError("Phase 3 components not available")

        # Use Phase 2 results for enhanced context if available
        enhanced_context = {}
        if "phase2" in context.phase_results:
            phase2_data = context.phase_results["phase2"].data
            enhanced_context["emotional_context"] = phase2_data.get("emotional_intelligence", {})

        # Execute Phase 3 with optimization
        if self.optimization_level == OptimizationLevel.AGGRESSIVE:
            # Use background processing for aggressive optimization
            results = await self._execute_phase3_optimized(context, enhanced_context)
        else:
            # Standard Phase 3 execution
            results = await self.phase3_memory_networks.analyze_complete_memory_network(
                user_id=context.user_id, memory_manager=self.memory_manager
            )

        processing_time = time.time() - start_time

        return PhaseResult(
            phase_name="phase3",
            success=True,
            data=results,
            processing_time=processing_time,
            metadata={"enhanced_context_used": bool(enhanced_context)},
        )

    async def _execute_memory_optimization(
        self, context: IntegratedPhaseContext, start_time: float
    ) -> PhaseResult:
        """Execute memory optimization with phase integration"""

        if not self.memory_manager:
            raise ValueError("Memory manager not available")

        # Optimize memory queries based on available phase results
        optimized_queries = []

        # Use Phase 2 emotional context for query optimization
        if "phase2" in context.phase_results:
            emotional_data = context.phase_results["phase2"].data.get("emotional_intelligence", {})
            emotional_state = emotional_data.get("detected_emotion", "neutral")

            # Generate emotion-aware queries
            optimized_queries.extend(
                [f"{context.message} {emotional_state}", f"{emotional_state} conversation context"]
            )

        # Use Phase 3 patterns for query optimization
        if "phase3" in context.phase_results:
            phase3_data = context.phase_results["phase3"].data
            if "core_memories" in phase3_data:
                core_topics = [mem.get("topic", "") for mem in phase3_data["core_memories"][:3]]
                optimized_queries.extend(core_topics)

        # Fallback to basic query optimization
        if not optimized_queries:
            optimized_queries = [context.message]

        processing_time = time.time() - start_time

        return PhaseResult(
            phase_name="memory_optimization",
            success=True,
            data={
                "optimized_queries": optimized_queries,
                "query_count": len(optimized_queries),
                "optimization_method": "phase_integrated",
            },
            processing_time=processing_time,
            metadata={"phase_integration_used": True},
        )

    async def _execute_phase3_optimized(
        self, context: IntegratedPhaseContext, enhanced_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute Phase 3 with optimization strategies"""

        if not self.memory_manager:
            raise ValueError("Memory manager not available for optimized Phase 3")

        # For aggressive optimization, run a lightweight version of Phase 3
        try:
            # Get core memories only (faster than full network analysis)
            core_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=context.user_id, query=context.message, limit=10
            )

            return {
                "core_memories": core_memories,
                "optimization_note": "Lightweight Phase 3 execution for performance",
                "enhanced_context": enhanced_context,
            }

        except Exception as e:
            logger.warning(f"Optimized Phase 3 execution failed, falling back to standard: {e}")
            if self.phase3_memory_networks:
                return await self.phase3_memory_networks.analyze_complete_memory_network(
                    user_id=context.user_id, memory_manager=self.memory_manager
                )
            else:
                raise ValueError("Phase 3 memory networks not available for fallback")

    def _group_phases_by_dependencies(self, phases: list[str]) -> list[list[str]]:
        """Group phases by dependency levels for parallel execution"""

        # Level 0: No dependencies
        level_0 = [phase for phase in phases if not self.phase_dependencies.get(phase, [])]

        # Level 1: Depends on level 0
        level_1 = [
            phase
            for phase in phases
            if phase not in level_0
            and all(dep in level_0 for dep in self.phase_dependencies.get(phase, []))
        ]

        return [level_0, level_1]

    def _sort_phases_by_dependencies(self, phases: list[str]) -> list[str]:
        """Sort phases by their dependencies for sequential execution"""

        sorted_phases = []
        remaining_phases = phases.copy()

        while remaining_phases:
            # Find phases with no unmet dependencies
            ready_phases = [
                phase
                for phase in remaining_phases
                if all(dep in sorted_phases for dep in self.phase_dependencies.get(phase, []))
            ]

            if not ready_phases:
                # If no phases are ready, just take the first one (break circular dependencies)
                ready_phases = [remaining_phases[0]]

            # Add ready phases to sorted list
            for phase in ready_phases:
                sorted_phases.append(phase)
                remaining_phases.remove(phase)

        return sorted_phases

    async def _optimize_phase_results(self, context: IntegratedPhaseContext):
        """Optimize and standardize phase results for consistency"""

        # Standardize result format
        for phase_name, result in context.phase_results.items():
            if result.success:
                # Add cross-phase references
                if phase_name == "phase3" and "phase2" in context.phase_results:
                    # Enhance Phase 3 results with emotional context
                    emotional_data = context.phase_results["phase2"].data.get(
                        "emotional_intelligence", {}
                    )
                    result.data["emotional_enhancement"] = emotional_data

                # Add performance metadata
                result.metadata["optimization_level"] = self.optimization_level.value
                result.metadata["execution_strategy"] = self.execution_strategy.value

        # Calculate optimization statistics
        total_time = sum(r.processing_time for r in context.phase_results.values())
        context.optimization_stats.update(
            {
                "total_phase_time": total_time,
                "phase_count": len(context.phase_results),
                "successful_phases": sum(1 for r in context.phase_results.values() if r.success),
                "cache_enabled": self.enable_caching,
            }
        )

    async def _check_result_cache(
        self, user_id: str, message: str
    ) -> dict[str, PhaseResult] | None:
        """Check if we have cached results for this user/message combination"""

        if not self.enable_caching:
            return None

        # Create cache key from user_id and message
        cache_key = hashlib.md5(f"{user_id}:{message}".encode()).hexdigest()

        if cache_key in self.result_cache:
            cached_data = self.result_cache[cache_key]

            # Check if cache is still valid
            cache_age = time.time() - cached_data["timestamp"]
            if cache_age < self.cache_ttl_seconds:
                return cached_data["results"]
            else:
                # Remove expired cache entry
                del self.result_cache[cache_key]

        return None

    async def _cache_results(self, user_id: str, message: str, results: dict[str, PhaseResult]):
        """Cache successful phase results"""

        if not self.enable_caching:
            return

        # Only cache successful results
        successful_results = {name: result for name, result in results.items() if result.success}

        if successful_results:
            cache_key = hashlib.md5(f"{user_id}:{message}".encode()).hexdigest()
            self.result_cache[cache_key] = {"timestamp": time.time(), "results": successful_results}

            # Clean up old cache entries (simple LRU)
            if len(self.result_cache) > 100:
                # Remove oldest entries
                sorted_entries = sorted(self.result_cache.items(), key=lambda x: x[1]["timestamp"])
                for old_key, _ in sorted_entries[:20]:
                    del self.result_cache[old_key]

    def _update_performance_stats(self, context: IntegratedPhaseContext):
        """Update performance statistics for monitoring"""

        # Update phase timing statistics
        for phase_name, result in context.phase_results.items():
            if phase_name not in self.performance_stats["phase_timings"]:
                self.performance_stats["phase_timings"][phase_name] = []

            self.performance_stats["phase_timings"][phase_name].append(result.processing_time)

            # Keep only recent timings (last 100)
            if len(self.performance_stats["phase_timings"][phase_name]) > 100:
                self.performance_stats["phase_timings"][phase_name] = self.performance_stats[
                    "phase_timings"
                ][phase_name][-100:]

    def get_performance_report(self) -> dict[str, Any]:
        """Get comprehensive performance report"""

        report = {
            "total_requests": self.performance_stats["total_requests"],
            "cache_hit_rate": (
                self.performance_stats["cache_hits"]
                / max(1, self.performance_stats["total_requests"])
            )
            * 100,
            "parallel_execution_rate": (
                self.performance_stats["parallel_executions"]
                / max(1, self.performance_stats["total_requests"])
            )
            * 100,
            "average_phase_timings": {},
            "optimization_settings": {
                "level": self.optimization_level.value,
                "strategy": self.execution_strategy.value,
                "caching_enabled": self.enable_caching,
            },
        }

        # Calculate average timings for each phase
        for phase_name, timings in self.performance_stats["phase_timings"].items():
            if timings:
                report["average_phase_timings"][phase_name] = {
                    "average": sum(timings) / len(timings),
                    "min": min(timings),
                    "max": max(timings),
                    "samples": len(timings),
                }

        return report
