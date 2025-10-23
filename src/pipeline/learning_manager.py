"""
🔄 Sprint 6: Learning Pipeline Manager

This module implements the Learning Pipeline Manager that automates the execution
of adaptive learning tasks across all sprints. It orchestrates the execution
of learning cycles, prioritizes tasks based on impact and urgency, and ensures
all learning systems work together as a unified whole.

Key Features:
- Automated learning cycle execution
- Priority-based task scheduling
- Cross-component coordination
- Pipeline health monitoring
- Execution tracking and metrics

Architecture:
- Integrates with Learning Orchestrator for task prioritization
- Manages execution of all adaptive learning components
- Ensures synchronization between concurrent learning processes
- Provides pipeline status monitoring and reporting
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a learning pipeline task."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskPriority(Enum):
    """Priority levels for learning pipeline tasks."""
    CRITICAL = 0    # Must execute immediately
    HIGH = 1        # Should execute in current cycle
    MEDIUM = 2      # Execute when resources available
    LOW = 3         # Can be deferred to future cycles
    BACKGROUND = 4  # Run only when system is idle


class TaskCategory(Enum):
    """Categories of tasks in the learning pipeline."""
    TRENDWISE = "trendwise"                # Sprint 1: TrendWise
    MEMORYBOOST = "memoryboost"            # Sprint 2: MemoryBoost
    RELATIONSHIP = "relationship"          # Sprint 3: RelationshipTuner
    CHARACTER_EVOLUTION = "character"      # Sprint 4: CharacterEvolution
    KNOWLEDGE_FUSION = "knowledge"         # Sprint 5: KnowledgeFusion
    ORCHESTRATION = "orchestration"        # Sprint 6: Intelligence Orchestration
    PREDICTION = "prediction"              # Sprint 6: Predictive Adaptation
    SYSTEM = "system"                      # System management tasks


class PipelineStage(Enum):
    """Stages in the learning pipeline."""
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    LEARNING = "learning"
    ADAPTATION = "adaptation"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"
    REPORTING = "reporting"


@dataclass
class PipelineTask:
    """Represents a task in the learning pipeline."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: TaskCategory = TaskCategory.SYSTEM
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    name: str = "Unnamed Task"
    description: str = ""
    stage: PipelineStage = PipelineStage.ANALYSIS
    bot_name: Optional[str] = None
    user_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    estimated_duration_seconds: int = 60
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineCycle:
    """Represents an execution cycle of the learning pipeline."""
    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Learning Cycle"
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "running"
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_pending: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""


class LearningPipelineManager:
    """
    🔄 Learning Pipeline Manager - Sprint 6 Component
    
    Manages the execution of all adaptive learning tasks across all sprints.
    Provides automated scheduling, priority-based execution, and pipeline
    monitoring capabilities.
    """
    
    def __init__(self, 
                 learning_orchestrator=None, 
                 predictive_engine=None,
                 temporal_client=None,
                 max_concurrent_tasks=5,
                 default_cycle_interval_hours=6):
        """Initialize the Learning Pipeline Manager."""
        self.learning_orchestrator = learning_orchestrator
        self.predictive_engine = predictive_engine
        self.temporal_client = temporal_client
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_cycle_interval_hours = default_cycle_interval_hours
        
        # Task management
        self._task_queue: List[PipelineTask] = []
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._completed_tasks: Dict[str, PipelineTask] = {}
        self._task_results: Dict[str, Any] = {}
        
        # Cycle management
        self._current_cycle: Optional[PipelineCycle] = None
        self._cycle_history: List[PipelineCycle] = []
        self._cycle_lock = asyncio.Lock()
        self._next_cycle_time = datetime.utcnow()
        
        # Execution state
        self._running = False
        self._paused = False
        self._shutdown_event = asyncio.Event()
        
        # Sprint 6 Telemetry: Usage tracking for evaluation
        self._telemetry = {
            'start_pipeline_count': 0,
            'schedule_learning_cycle_count': 0,
            'execute_task_count': 0,
            'total_tasks_completed': 0,
            'total_tasks_failed': 0,
            'total_execution_time_seconds': 0.0,
            'initialization_time': datetime.utcnow()
        }
        
        logger.info("Learning Pipeline Manager initialized")
    
    # =============================================================================
    # Core Pipeline Management Methods
    # =============================================================================
    
    async def start_pipeline(self):
        """Start the learning pipeline manager."""
        if self._running:
            logger.warning("Pipeline is already running")
            return
        
        self._running = True
        self._shutdown_event.clear()
        
        # Sprint 6 Telemetry: Track invocation
        self._telemetry['start_pipeline_count'] += 1
        
        logger.info("Starting Learning Pipeline Manager")
        
        # Start the main pipeline loop
        asyncio.create_task(self._pipeline_loop())
        
        # Schedule initial learning cycle
        await self.schedule_learning_cycle("Initial Learning Cycle")
        
        logger.info("Pipeline started successfully")
    
    async def stop_pipeline(self, wait_for_completion=False):
        """Stop the learning pipeline manager."""
        if not self._running:
            logger.warning("Pipeline is not running")
            return
        
        logger.info("Stopping Learning Pipeline Manager")
        self._running = False
        self._shutdown_event.set()
        
        if wait_for_completion:
            # Wait for running tasks to complete
            if self._running_tasks:
                logger.info("Waiting for %d tasks to complete...", len(self._running_tasks))
                pending_tasks = list(self._running_tasks.values())
                _, pending = await asyncio.wait(pending_tasks, timeout=30)
                
                # Cancel any remaining tasks
                for task in pending:
                    task.cancel()
        
        # Complete current cycle if one is running
        if self._current_cycle and self._current_cycle.status == "running":
            self._current_cycle.status = "interrupted"
            self._current_cycle.completed_at = datetime.utcnow()
            self._current_cycle.summary = "Cycle interrupted due to pipeline shutdown"
            self._cycle_history.append(self._current_cycle)
            self._current_cycle = None
        
        logger.info("Pipeline stopped successfully")
    
    async def pause_pipeline(self):
        """Pause the learning pipeline."""
        if self._paused:
            logger.warning("Pipeline is already paused")
            return
        
        logger.info("Pausing Learning Pipeline")
        self._paused = True
    
    async def resume_pipeline(self):
        """Resume the learning pipeline."""
        if not self._paused:
            logger.warning("Pipeline is not paused")
            return
        
        logger.info("Resuming Learning Pipeline")
        self._paused = False
    
    async def schedule_learning_cycle(self, name="Scheduled Learning Cycle", 
                                     delay_seconds=0) -> str:
        """
        Schedule a learning cycle to run after the specified delay.
        
        Args:
            name: Name for the learning cycle
            delay_seconds: Seconds to wait before starting the cycle
            
        Returns:
            str: Cycle ID
        """
        # Sprint 6 Telemetry: Track invocation
        self._telemetry['schedule_learning_cycle_count'] += 1
        
        async with self._cycle_lock:
            cycle = PipelineCycle(
                name=name,
                started_at=datetime.utcnow() + timedelta(seconds=delay_seconds)
            )
            
            if delay_seconds > 0:
                logger.info("Scheduling learning cycle '%s' to start in %d seconds", 
                           name, delay_seconds)
                # Use a task to schedule the cycle
                asyncio.create_task(self._schedule_cycle(cycle, delay_seconds))
            else:
                logger.info("Scheduling immediate learning cycle '%s'", name)
                self._current_cycle = cycle
                asyncio.create_task(self._execute_learning_cycle(cycle))
            
            return cycle.cycle_id
    
    # =============================================================================
    # Task Management Methods
    # =============================================================================
    
    async def add_task(self, task: PipelineTask) -> str:
        """
        Add a task to the pipeline queue.
        
        Args:
            task: The task to add
            
        Returns:
            str: Task ID
        """
        logger.info("Adding task: %s (priority: %s)", task.name, task.priority.name)
        
        # Add task to queue
        self._task_queue.append(task)
        
        # Sort queue by priority
        self._task_queue.sort(key=lambda t: t.priority.value)
        
        # Update cycle metrics if within a cycle
        if self._current_cycle:
            self._current_cycle.tasks_total += 1
            self._current_cycle.tasks_pending += 1
        
        # Record task addition
        await self._record_task_event(task, "added")
        
        return task.task_id
    
    async def add_tasks(self, tasks: List[PipelineTask]) -> List[str]:
        """
        Add multiple tasks to the pipeline queue.
        
        Args:
            tasks: List of tasks to add
            
        Returns:
            List[str]: List of task IDs
        """
        task_ids = []
        for task in tasks:
            task_id = await self.add_task(task)
            task_ids.append(task_id)
        
        return task_ids
    
    async def get_task(self, task_id: str) -> Optional[PipelineTask]:
        """
        Get a task by ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Optional[PipelineTask]: The task if found, None otherwise
        """
        # Check active queue
        for task in self._task_queue:
            if task.task_id == task_id:
                return task
        
        # Check completed tasks
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task by ID.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            bool: True if task was canceled, False otherwise
        """
        # Check if task is in queue
        for i, task in enumerate(self._task_queue):
            if task.task_id == task_id:
                task.status = TaskStatus.CANCELED
                self._task_queue.pop(i)
                self._completed_tasks[task_id] = task
                
                # Update cycle metrics
                if self._current_cycle:
                    self._current_cycle.tasks_pending -= 1
                
                await self._record_task_event(task, "canceled")
                return True
        
        # Check if task is running
        if task_id in self._running_tasks:
            # Cancel the running task
            self._running_tasks[task_id].cancel()
            
            # Update task status
            for i, task in enumerate(self._task_queue):
                if task.task_id == task_id:
                    task.status = TaskStatus.CANCELED
                    self._task_queue.pop(i)
                    self._completed_tasks[task_id] = task
                    
                    # Update cycle metrics
                    if self._current_cycle:
                        self._current_cycle.tasks_pending -= 1
                    
                    await self._record_task_event(task, "canceled")
                    return True
        
        return False
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current status of the learning pipeline.
        
        Returns:
            Dict[str, Any]: Pipeline status information
        """
        pending_by_priority = {}
        for priority in TaskPriority:
            pending_by_priority[priority.name] = len([
                t for t in self._task_queue if t.priority == priority
            ])
        
        pending_by_category = {}
        for category in TaskCategory:
            pending_by_category[category.name] = len([
                t for t in self._task_queue if t.category == category
            ])
        
        return {
            "running": self._running,
            "paused": self._paused,
            "current_cycle": self._current_cycle.cycle_id if self._current_cycle else None,
            "current_cycle_name": self._current_cycle.name if self._current_cycle else None,
            "current_cycle_status": self._current_cycle.status if self._current_cycle else None,
            "tasks_pending": len(self._task_queue),
            "tasks_running": len(self._running_tasks),
            "tasks_completed": len(self._completed_tasks),
            "next_cycle_time": self._next_cycle_time,
            "pending_by_priority": pending_by_priority,
            "pending_by_category": pending_by_category,
            "completed_cycles": len(self._cycle_history)
        }
    
    # =============================================================================
    # Pipeline Loop and Cycle Execution
    # =============================================================================
    
    async def _pipeline_loop(self):
        """Main pipeline loop that manages task execution."""
        logger.info("Pipeline loop started")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                # Check if pipeline is paused
                if self._paused:
                    await asyncio.sleep(1)
                    continue
                
                # Check if we need to start a new cycle
                now = datetime.utcnow()
                if not self._current_cycle and now >= self._next_cycle_time:
                    cycle_name = f"Automated Learning Cycle {len(self._cycle_history) + 1}"
                    await self.schedule_learning_cycle(cycle_name)
                    
                    # Set next cycle time
                    self._next_cycle_time = now + timedelta(hours=self.default_cycle_interval_hours)
                
                # Process tasks if we have room for execution
                available_slots = self.max_concurrent_tasks - len(self._running_tasks)
                
                if available_slots > 0 and self._task_queue:
                    # Get highest priority tasks that are ready to run
                    ready_tasks = self._get_ready_tasks(available_slots)
                    
                    # Start each ready task
                    for task in ready_tasks:
                        if task.task_id not in self._running_tasks:
                            asyncio.create_task(self._execute_task(task))
                
                # Check for completed tasks
                completed_task_ids = []
                for task_id, task_future in self._running_tasks.items():
                    if task_future.done():
                        completed_task_ids.append(task_id)
                
                # Remove completed tasks from running list
                for task_id in completed_task_ids:
                    self._running_tasks.pop(task_id, None)
                
                # Small sleep to prevent tight loop
                await asyncio.sleep(0.1)
                
            except (ValueError, TypeError, AttributeError) as e:
                logger.error("Error in pipeline loop: %s", str(e))
                await asyncio.sleep(1)
            
            except asyncio.CancelledError:
                logger.info("Pipeline loop canceled")
                break
        
        logger.info("Pipeline loop exited")
    
    async def _schedule_cycle(self, cycle: PipelineCycle, delay_seconds: int):
        """Schedule a cycle to run after a delay."""
        await asyncio.sleep(delay_seconds)
        
        async with self._cycle_lock:
            # Only schedule if no current cycle is running
            if not self._running:
                return
            
            if not self._current_cycle:
                self._current_cycle = cycle
                asyncio.create_task(self._execute_learning_cycle(cycle))
            else:
                logger.warning("Cannot schedule cycle, another cycle is already running")
    
    async def _execute_learning_cycle(self, cycle: PipelineCycle):
        """Execute a complete learning cycle."""
        logger.info("Starting learning cycle: %s", cycle.name)
        
        try:
            # PHASE 1: Generate tasks for this cycle
            tasks = await self._generate_cycle_tasks()
            task_ids = await self.add_tasks(tasks)
            
            cycle.tasks_total = len(task_ids)
            cycle.tasks_pending = len(task_ids)
            
            # Record cycle start
            await self._record_cycle_event(cycle, "started")
            
            # PHASE 2: Wait for all tasks to complete
            start_time = time.time()
            timeout = 60 * 60  # 1 hour max for a cycle
            
            while (self._task_queue or self._running_tasks) and time.time() - start_time < timeout:
                # Update cycle metrics
                cycle.tasks_completed = len([t for t in self._completed_tasks.values() 
                                          if t.metadata.get('cycle_id') == cycle.cycle_id])
                cycle.tasks_failed = len([t for t in self._completed_tasks.values() 
                                       if t.metadata.get('cycle_id') == cycle.cycle_id
                                       and t.status == TaskStatus.FAILED])
                cycle.tasks_pending = cycle.tasks_total - cycle.tasks_completed - cycle.tasks_failed
                
                # Check if all tasks are done
                if cycle.tasks_pending == 0:
                    break
                
                # Wait a bit
                await asyncio.sleep(1)
            
            # PHASE 3: Analyze cycle results
            result_summary = await self._analyze_cycle_results(cycle)
            
            # PHASE 4: Complete cycle
            cycle.completed_at = datetime.utcnow()
            cycle.status = "completed"
            cycle.summary = result_summary
            
            # Record cycle completion
            await self._record_cycle_event(cycle, "completed")
            
            # Store in history and clear current
            self._cycle_history.append(cycle)
            self._current_cycle = None
            
            logger.info("Completed learning cycle: %s - %s", cycle.name, result_summary)
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Error in learning cycle execution: %s", str(e))
            
            # Mark cycle as failed
            cycle.status = "failed"
            cycle.completed_at = datetime.utcnow()
            cycle.summary = f"Failed due to error: {str(e)}"
            
            # Record cycle failure
            await self._record_cycle_event(cycle, "failed")
            
            # Store in history and clear current
            self._cycle_history.append(cycle)
            self._current_cycle = None
    
    async def _execute_task(self, task: PipelineTask):
        """Execute a single task."""
        task_start = datetime.utcnow()
        logger.info("Executing task: %s", task.name)
        
        # Sprint 6 Telemetry: Track invocation
        self._telemetry['execute_task_count'] += 1
        
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        # Record task start
        await self._record_task_event(task, "started")
        
        # Create task future
        task_future = asyncio.create_task(self._run_task_function(task))
        self._running_tasks[task.task_id] = task_future
        
        try:
            # Run the task
            result = await task_future
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            
            # Sprint 6 Telemetry: Record successful task execution
            task_duration = (datetime.utcnow() - task_start).total_seconds()
            self._telemetry['total_tasks_completed'] += 1
            self._telemetry['total_execution_time_seconds'] += task_duration
            
            # Sprint 6 Telemetry: Write to InfluxDB for evaluation
            if self.temporal_client:
                try:
                    telemetry_point = {
                        'measurement': 'component_usage',
                        'tags': {
                            'component': 'learning_pipeline_manager',
                            'method': 'execute_task',
                            'task_category': task.category.value,
                            'task_stage': task.stage.value,
                            'bot_name': task.bot_name or 'unknown'
                        },
                        'fields': {
                            'execution_time_seconds': task_duration,
                            'task_priority': task.priority.value,
                            'invocation_count': self._telemetry['execute_task_count'],
                            'total_tasks_completed': self._telemetry['total_tasks_completed']
                        },
                        'time': task_start
                    }
                    await self.temporal_client.write_point(telemetry_point)
                    logger.info("📊 PIPELINE TELEMETRY: Recorded task execution metrics to InfluxDB")
                except Exception as telemetry_error:
                    logger.warning("Failed to record pipeline telemetry: %s", telemetry_error)
            
            # Record task completion
            await self._record_task_event(task, "completed")
            
            # Update cycle metrics
            if self._current_cycle:
                self._current_cycle.tasks_completed += 1
                self._current_cycle.tasks_pending -= 1
            
            # Store result
            self._task_results[task.task_id] = result
            
            logger.info("Task completed: %s", task.name)
            
        except (ValueError, TypeError, AttributeError) as e:
            # Update task status
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error = str(e)
            
            # Sprint 6 Telemetry: Record failed task
            self._telemetry['total_tasks_failed'] += 1
            
            # Record task failure
            await self._record_task_event(task, "failed", {"error": str(e)})
            
            # Update cycle metrics
            if self._current_cycle:
                self._current_cycle.tasks_failed += 1
                self._current_cycle.tasks_pending -= 1
            
            logger.error("Task failed: %s - %s", task.name, str(e))
        
        finally:
            # Move task from queue to completed
            if task in self._task_queue:
                self._task_queue.remove(task)
            self._completed_tasks[task.task_id] = task
            
            # Remove from running tasks
            self._running_tasks.pop(task.task_id, None)
    
    async def _run_task_function(self, task: PipelineTask):
        """
        Run the appropriate function based on task category and stage.
        
        This is where tasks are actually executed by calling the appropriate
        component based on task category and stage.
        """
        # Simulate execution time for demo purposes
        await asyncio.sleep(task.estimated_duration_seconds / 10)  # 10x faster for demo
        
        # Default result
        result = {"status": "executed", "task_name": task.name}
        
        # TrendWise tasks (Sprint 1)
        if task.category == TaskCategory.TRENDWISE:
            if task.stage == PipelineStage.ANALYSIS:
                # Would call: trend_analyzer.get_confidence_trends()
                result["confidence_trend"] = "analyzed"
                
            elif task.stage == PipelineStage.ADAPTATION:
                # Would call: confidence_adapter.adjust_response_style()
                result["adaptation"] = "applied"
        
        # MemoryBoost tasks (Sprint 2)
        elif task.category == TaskCategory.MEMORYBOOST:
            if task.stage == PipelineStage.ANALYSIS:
                # Would call: memory_effectiveness_analyzer.analyze_memory_performance()
                result["memory_analysis"] = "completed"
                
            elif task.stage == PipelineStage.OPTIMIZATION:
                # Would call: vector_relevance_optimizer.boost_effective_memories()
                result["memory_optimization"] = "applied"
        
        # RelationshipTuner tasks (Sprint 3)
        elif task.category == TaskCategory.RELATIONSHIP:
            if task.stage == PipelineStage.ANALYSIS:
                # Would call: relationship_evolution_engine.calculate_dynamic_relationship_score()
                result["relationship_scores"] = str({"trust": 0.8, "affection": 0.7})
                
            elif task.stage == PipelineStage.ADAPTATION:
                # Would call: trust_recovery_system.detect_trust_decline()
                result["trust_analysis"] = "stable"
        
        # CharacterEvolution tasks (Sprint 4)
        elif task.category == TaskCategory.CHARACTER_EVOLUTION:
            if task.stage == PipelineStage.ANALYSIS:
                # Would call: character_performance_analyzer.analyze_character_effectiveness()
                result["character_analysis"] = "completed"
                
            elif task.stage == PipelineStage.OPTIMIZATION:
                # Would call: cdl_parameter_optimizer.generate_parameter_adjustments()
                result["character_optimization"] = "parameters generated"
        
        # KnowledgeFusion tasks (Sprint 5)
        elif task.category == TaskCategory.KNOWLEDGE_FUSION:
            if task.stage == PipelineStage.ANALYSIS:
                # Would call: knowledge_integration_engine.fuse_cross_store_insights()
                result["knowledge_fusion"] = "insights generated"
                
            elif task.stage == PipelineStage.LEARNING:
                # Would call: fact_confidence_learner.update_fact_confidence_dynamically()
                result["fact_learning"] = "confidence updated"
        
        # Orchestration tasks (Sprint 6)
        elif task.category == TaskCategory.ORCHESTRATION:
            if self.learning_orchestrator:
                if task.stage == PipelineStage.ANALYSIS:
                    # Call learning orchestrator health check
                    bot_name = task.bot_name or "elena"  # Default if not specified
                    result["health_report"] = await self.learning_orchestrator.monitor_learning_health(bot_name)
                
                elif task.stage == PipelineStage.OPTIMIZATION:
                    # Call learning orchestrator to coordinate optimizations
                    result["optimization_tasks"] = await self.learning_orchestrator.prioritize_learning_tasks()
        
        # Prediction tasks (Sprint 6)
        elif task.category == TaskCategory.PREDICTION:
            if self.predictive_engine:
                if task.stage == PipelineStage.ANALYSIS:
                    # Call predictive engine to generate predictions
                    user_id = task.user_id or "test_user"  # Default if not specified
                    bot_name = task.bot_name or "elena"  # Default if not specified
                    result["predictions"] = await self.predictive_engine.predict_user_needs(user_id, bot_name)
                
                elif task.stage == PipelineStage.ADAPTATION:
                    # Call predictive engine to create adaptations
                    result["adaptations"] = "generated"  # Would contain actual adaptations
        
        # System tasks
        elif task.category == TaskCategory.SYSTEM:
            # System tasks like metrics collection, cleanup, etc.
            result["system_task"] = "executed"
        
        return result
    
    # =============================================================================
    # Task Generation and Analysis
    # =============================================================================
    
    async def _generate_cycle_tasks(self) -> List[PipelineTask]:
        """Generate tasks for the current learning cycle."""
        tasks = []
        cycle_id = self._current_cycle.cycle_id if self._current_cycle else str(uuid.uuid4())
        
        # Add orchestration tasks for all bots
        bot_names = ["elena", "marcus", "gabriel", "jake", "ryan"]
        for bot_name in bot_names:
            # Health monitoring task
            tasks.append(PipelineTask(
                name=f"Health monitoring for {bot_name}",
                description=f"Monitor learning system health for {bot_name}",
                category=TaskCategory.ORCHESTRATION,
                stage=PipelineStage.ANALYSIS,
                priority=TaskPriority.HIGH,
                bot_name=bot_name,
                estimated_duration_seconds=30,
                metadata={"cycle_id": cycle_id}
            ))
            
            # TrendWise analysis (Sprint 1)
            tasks.append(PipelineTask(
                name=f"TrendWise analysis for {bot_name}",
                description=f"Analyze confidence and quality trends for {bot_name}",
                category=TaskCategory.TRENDWISE,
                stage=PipelineStage.ANALYSIS,
                priority=TaskPriority.HIGH,
                bot_name=bot_name,
                estimated_duration_seconds=45,
                metadata={"cycle_id": cycle_id}
            ))
            
            # MemoryBoost optimization (Sprint 2)
            tasks.append(PipelineTask(
                name=f"MemoryBoost optimization for {bot_name}",
                description=f"Optimize memory retrieval for {bot_name}",
                category=TaskCategory.MEMORYBOOST,
                stage=PipelineStage.OPTIMIZATION,
                priority=TaskPriority.MEDIUM,
                bot_name=bot_name,
                estimated_duration_seconds=60,
                metadata={"cycle_id": cycle_id}
            ))
            
            # RelationshipTuner analysis (Sprint 3)
            tasks.append(PipelineTask(
                name=f"RelationshipTuner analysis for {bot_name}",
                description=f"Analyze relationship dynamics for {bot_name}",
                category=TaskCategory.RELATIONSHIP,
                stage=PipelineStage.ANALYSIS,
                priority=TaskPriority.MEDIUM,
                bot_name=bot_name,
                estimated_duration_seconds=40,
                metadata={"cycle_id": cycle_id}
            ))
            
            # CharacterEvolution optimization (Sprint 4)
            tasks.append(PipelineTask(
                name=f"CharacterEvolution for {bot_name}",
                description=f"Optimize character parameters for {bot_name}",
                category=TaskCategory.CHARACTER_EVOLUTION,
                stage=PipelineStage.OPTIMIZATION,
                priority=TaskPriority.MEDIUM,
                bot_name=bot_name,
                estimated_duration_seconds=90,
                metadata={"cycle_id": cycle_id}
            ))
            
            # KnowledgeFusion learning (Sprint 5)
            tasks.append(PipelineTask(
                name=f"KnowledgeFusion for {bot_name}",
                description=f"Integrate cross-store knowledge for {bot_name}",
                category=TaskCategory.KNOWLEDGE_FUSION,
                stage=PipelineStage.LEARNING,
                priority=TaskPriority.LOW,
                bot_name=bot_name,
                estimated_duration_seconds=75,
                metadata={"cycle_id": cycle_id}
            ))
            
            # Predictive analysis (Sprint 6)
            tasks.append(PipelineTask(
                name=f"Predictive analysis for {bot_name}",
                description=f"Generate user need predictions for {bot_name}",
                category=TaskCategory.PREDICTION,
                stage=PipelineStage.ANALYSIS,
                priority=TaskPriority.HIGH,
                bot_name=bot_name,
                estimated_duration_seconds=50,
                metadata={"cycle_id": cycle_id}
            ))
        
        # Add general system tasks
        tasks.append(PipelineTask(
            name="System metrics collection",
            description="Collect system performance metrics",
            category=TaskCategory.SYSTEM,
            stage=PipelineStage.REPORTING,
            priority=TaskPriority.LOW,
            estimated_duration_seconds=20,
            metadata={"cycle_id": cycle_id}
        ))
        
        # Add final coordination task
        tasks.append(PipelineTask(
            name="Cycle coordination",
            description="Final coordination and optimization task",
            category=TaskCategory.ORCHESTRATION,
            stage=PipelineStage.OPTIMIZATION,
            priority=TaskPriority.HIGH,
            estimated_duration_seconds=30,
            metadata={"cycle_id": cycle_id, "is_final_task": True}
        ))
        
        return tasks
    
    async def _analyze_cycle_results(self, cycle: PipelineCycle) -> str:
        """Analyze results of a learning cycle."""
        if not cycle:
            return "No cycle to analyze"
        
        # Collect metrics
        success_rate = 0
        if cycle.tasks_total > 0:
            success_rate = cycle.tasks_completed / cycle.tasks_total * 100
        
        execution_time = 0
        if cycle.completed_at and cycle.started_at:
            execution_time = (cycle.completed_at - cycle.started_at).total_seconds()
        
        # Calculate improvements
        improvements = []
        if self._task_results:
            # Look for specific task results that indicate improvements
            for _, result in self._task_results.items():
                if isinstance(result, dict):
                    if "confidence_trend" in result:
                        improvements.append("Confidence trend analysis")
                    if "memory_optimization" in result:
                        improvements.append("Memory retrieval optimization")
                    if "character_optimization" in result:
                        improvements.append("Character parameter optimization")
                    if "knowledge_fusion" in result:
                        improvements.append("Cross-store knowledge integration")
                    if "predictions" in result:
                        improvements.append("User need predictions")
        
        # Generate summary
        if success_rate >= 90:
            quality = "excellent"
        elif success_rate >= 75:
            quality = "good"
        elif success_rate >= 50:
            quality = "average"
        else:
            quality = "poor"
        
        summary = (f"Cycle completed with {quality} results. Success rate: {success_rate:.1f}%. "
                   f"Execution time: {execution_time:.1f}s. "
                   f"Completed tasks: {cycle.tasks_completed}/{cycle.tasks_total}. "
                   f"Improvements: {', '.join(improvements) if improvements else 'None'}")
        
        # Update cycle metrics
        cycle.metrics = {
            "success_rate": success_rate,
            "execution_time": execution_time,
            "improvements": len(improvements)
        }
        
        return summary
    
    def _get_ready_tasks(self, max_tasks: int) -> List[PipelineTask]:
        """
        Get tasks that are ready to run, based on priority and dependencies.
        
        Args:
            max_tasks: Maximum number of tasks to return
            
        Returns:
            List[PipelineTask]: List of tasks ready to run
        """
        if not self._task_queue:
            return []
        
        # Start with tasks that have no dependencies
        ready_tasks = []
        completed_task_ids = set(self._completed_tasks.keys())
        
        for task in self._task_queue[:max_tasks * 2]:  # Look at twice as many tasks
            # Check if all dependencies are completed
            dependencies_met = all(dep in completed_task_ids for dep in task.dependencies)
            
            if dependencies_met and len(ready_tasks) < max_tasks:
                ready_tasks.append(task)
                
                # Check if we have enough tasks
                if len(ready_tasks) >= max_tasks:
                    break
        
        return ready_tasks
    
    # =============================================================================
    # Metrics and Monitoring
    # =============================================================================
    
    async def _record_task_event(self, task: PipelineTask, event_type: str, 
                               extra_fields: Optional[Dict[str, Any]] = None):
        """Record task event to InfluxDB."""
        if not self.temporal_client:
            return
        
        try:
            fields = {
                "event": 1,
                "event_type": event_type,
                "priority": task.priority.value,
                "estimated_duration": task.estimated_duration_seconds
            }
            
            # Add any extra fields
            if extra_fields:
                fields.update(extra_fields)
            
            # Add execution time if completed
            if event_type == "completed" and task.started_at and task.completed_at:
                execution_time = (task.completed_at - task.started_at).total_seconds()
                fields["execution_time"] = execution_time
            
            # Record to InfluxDB
            await self.temporal_client.record_point(
                measurement="pipeline_tasks",
                tags={
                    "task_id": task.task_id,
                    "name": task.name,
                    "category": task.category.value,
                    "stage": task.stage.value,
                    "status": task.status.value,
                    "bot_name": task.bot_name or "system",
                    "event_type": event_type
                },
                fields=fields
            )
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Failed to record task event: %s", str(e))
    
    async def _record_cycle_event(self, cycle: PipelineCycle, event_type: str):
        """Record cycle event to InfluxDB."""
        if not self.temporal_client:
            return
        
        try:
            fields = {
                "event": 1,
                "event_type": event_type,
                "tasks_total": cycle.tasks_total,
                "tasks_completed": cycle.tasks_completed,
                "tasks_failed": cycle.tasks_failed,
                "tasks_pending": cycle.tasks_pending
            }
            
            # Add execution time if completed
            if event_type == "completed" and cycle.started_at and cycle.completed_at:
                execution_time = (cycle.completed_at - cycle.started_at).total_seconds()
                fields["execution_time"] = execution_time
            
            # Record to InfluxDB
            await self.temporal_client.record_point(
                measurement="pipeline_cycles",
                tags={
                    "cycle_id": cycle.cycle_id,
                    "name": cycle.name,
                    "status": cycle.status,
                    "event_type": event_type
                },
                fields=fields
            )
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Failed to record cycle event: %s", str(e))


def create_learning_pipeline_manager(learning_orchestrator=None, predictive_engine=None,
                                   temporal_client=None, max_concurrent_tasks=5):
    """
    🏭 Factory function to create Learning Pipeline Manager.
    
    Args:
        learning_orchestrator: Learning Orchestrator component
        predictive_engine: Predictive Adaptation Engine
        temporal_client: InfluxDB client for metrics
        max_concurrent_tasks: Maximum concurrent tasks
        
    Returns:
        LearningPipelineManager: Configured pipeline manager
    """
    return LearningPipelineManager(
        learning_orchestrator=learning_orchestrator,
        predictive_engine=predictive_engine,
        temporal_client=temporal_client,
        max_concurrent_tasks=max_concurrent_tasks
    )