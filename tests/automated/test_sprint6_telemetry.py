"""
Test Sprint 6 Learning Component Telemetry

Validates that telemetry tracking works correctly for:
- LearningOrchestrator
- PredictiveAdaptationEngine
- LearningPipelineManager

This test helps evaluate Sprint 6 component usage for the completion decision.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from influxdb_client import Point

# Sprint 6 components
from src.orchestration.learning_orchestrator import LearningOrchestrator, LearningHealthReport, SystemLearningHealth
from src.adaptation.predictive_engine import PredictiveAdaptationEngine, PredictedNeed, PredictionType, PredictionConfidence
from src.pipeline.learning_manager import LearningPipelineManager, PipelineTask, TaskCategory, TaskPriority, TaskStatus, PipelineStage


class TestLearningOrchestratorTelemetry:
    """Test telemetry tracking for LearningOrchestrator."""
    
    @pytest.mark.asyncio
    async def test_coordinate_learning_cycle_telemetry(self):
        """Test that coordinate_learning_cycle tracks usage properly."""
        # Create mock dependencies
        temporal_client = Mock()
        temporal_client.write_point = AsyncMock()
        
        # Create orchestrator with telemetry
        orchestrator = LearningOrchestrator(
            temporal_client=temporal_client,
            postgres_pool=Mock()
        )
        
        # Verify telemetry initialized
        assert orchestrator._telemetry is not None
        assert orchestrator._telemetry['coordinate_learning_cycle_count'] == 0
        
        # Mock internal methods to avoid complex setup
        orchestrator.monitor_learning_health = AsyncMock(return_value=Mock(
            overall_health=SystemLearningHealth.GOOD,
            component_statuses=[],
            active_tasks=[],
            completed_tasks_24h=0,
            quality_trend="stable",
            system_performance_score=0.8,
            recommendations=[],
            generated_at=datetime.utcnow()
        ))
        orchestrator.prioritize_learning_tasks = AsyncMock(return_value=[])
        orchestrator._execute_priority_tasks = AsyncMock(return_value={'completed_tasks': [], 'failed_tasks': []})
        orchestrator._analyze_cross_sprint_correlations = AsyncMock(return_value=[])
        orchestrator._update_system_performance = AsyncMock(return_value={'improvement_score': 0.1})
        orchestrator._record_orchestration_metrics = AsyncMock()
        orchestrator._generate_cycle_recommendations = Mock(return_value=[])
        
        # Execute learning cycle
        result = await orchestrator.coordinate_learning_cycle("elena")
        
        # Verify telemetry updated
        assert orchestrator._telemetry['coordinate_learning_cycle_count'] == 1
        assert orchestrator._telemetry['total_execution_time_seconds'] > 0
        
        # Verify InfluxDB telemetry recorded
        assert temporal_client.write_point.called
        call_args = temporal_client.write_point.call_args[0][0]
        assert call_args['measurement'] == 'component_usage'
        assert call_args['tags']['component'] == 'learning_orchestrator'
        assert call_args['tags']['method'] == 'coordinate_learning_cycle'
        assert call_args['tags']['bot_name'] == 'elena'
        assert 'execution_time_seconds' in call_args['fields']
        assert call_args['fields']['invocation_count'] == 1
        
        print(f"✅ LearningOrchestrator telemetry validated: {orchestrator._telemetry['coordinate_learning_cycle_count']} cycles, "
              f"{orchestrator._telemetry['total_execution_time_seconds']:.3f}s total")
    
    @pytest.mark.asyncio
    async def test_monitor_learning_health_telemetry(self):
        """Test that monitor_learning_health tracks usage properly."""
        # Create orchestrator with telemetry
        orchestrator = LearningOrchestrator(
            temporal_client=Mock(),
            postgres_pool=Mock()
        )
        
        # Mock internal health check methods
        orchestrator._check_trendwise_health = AsyncMock(return_value=Mock())
        orchestrator._check_memoryboost_health = AsyncMock(return_value=Mock())
        orchestrator._check_relationship_health = AsyncMock(return_value=Mock())
        orchestrator._check_character_evolution_health = AsyncMock(return_value=Mock())
        orchestrator._check_knowledge_fusion_health = AsyncMock(return_value=Mock())
        orchestrator._calculate_overall_health = Mock(return_value=SystemLearningHealth.GOOD)
        orchestrator._generate_system_recommendations = Mock(return_value=[])
        orchestrator._calculate_quality_trend = Mock(return_value="stable")
        orchestrator._calculate_system_performance = Mock(return_value=0.8)
        orchestrator._record_health_metrics = AsyncMock()
        
        # Execute health monitoring
        result = await orchestrator.monitor_learning_health("elena")
        
        # Verify telemetry updated
        assert orchestrator._telemetry['monitor_learning_health_count'] == 1
        
        print(f"✅ LearningOrchestrator health monitoring telemetry validated: "
              f"{orchestrator._telemetry['monitor_learning_health_count']} checks")


class TestPredictiveEngineTelemetry:
    """Test telemetry tracking for PredictiveAdaptationEngine."""
    
    @pytest.mark.asyncio
    async def test_predict_user_needs_telemetry(self):
        """Test that predict_user_needs tracks usage properly."""
        # Create mock dependencies
        temporal_client = Mock()
        temporal_client.write_point = AsyncMock()
        
        # Create predictive engine with telemetry
        engine = PredictiveAdaptationEngine(
            trend_analyzer=Mock(),
            confidence_adapter=Mock(),
            temporal_client=temporal_client,
            memory_manager=Mock()
        )
        
        # Verify telemetry initialized
        assert engine._telemetry is not None
        assert engine._telemetry['predict_user_needs_count'] == 0
        assert engine._telemetry['total_predictions_generated'] == 0
        
        # Mock internal prediction methods
        engine._get_trend_analysis = AsyncMock(return_value={})
        engine._predict_confidence_issues = AsyncMock(return_value=[])
        engine._predict_quality_issues = AsyncMock(return_value=[])
        engine._predict_relationship_issues = AsyncMock(return_value=[])
        engine._predict_engagement_issues = AsyncMock(return_value=[
            Mock(
                prediction_type=PredictionType.ENGAGEMENT_DECREASE,
                confidence=PredictionConfidence.HIGH
            )
        ])
        engine._record_prediction_metrics = AsyncMock()
        
        # Execute prediction
        predictions = await engine.predict_user_needs("test_user_123", "elena", prediction_horizon_hours=24)
        
        # Verify telemetry updated
        assert engine._telemetry['predict_user_needs_count'] == 1
        assert engine._telemetry['total_predictions_generated'] == 1
        assert engine._telemetry['total_execution_time_seconds'] > 0
        
        # Verify InfluxDB telemetry recorded
        assert temporal_client.write_point.called
        call_args = temporal_client.write_point.call_args[0][0]
        assert call_args['measurement'] == 'component_usage'
        assert call_args['tags']['component'] == 'predictive_engine'
        assert call_args['tags']['method'] == 'predict_user_needs'
        assert call_args['tags']['bot_name'] == 'elena'
        assert call_args['tags']['user_id'] == 'test_user_123'
        assert call_args['fields']['predictions_generated'] == 1
        assert call_args['fields']['prediction_horizon_hours'] == 24
        assert call_args['fields']['invocation_count'] == 1
        
        print(f"✅ PredictiveEngine telemetry validated: {engine._telemetry['predict_user_needs_count']} predictions, "
              f"{engine._telemetry['total_predictions_generated']} needs identified, "
              f"{engine._telemetry['total_execution_time_seconds']:.3f}s total")
    
    @pytest.mark.asyncio
    async def test_preemptively_adapt_responses_telemetry(self):
        """Test that preemptively_adapt_responses tracks usage properly."""
        # Create predictive engine with telemetry
        engine = PredictiveAdaptationEngine(
            trend_analyzer=Mock(),
            confidence_adapter=Mock(),
            temporal_client=Mock(),
            memory_manager=Mock()
        )
        
        # Mock internal adaptation methods
        engine._create_adaptation_actions = AsyncMock(return_value=[Mock()])
        engine._record_adaptation_metrics = AsyncMock()
        
        # Create mock predicted needs
        predicted_needs = [
            Mock(
                user_id="test_user_123",
                bot_name="elena",
                confidence=PredictionConfidence.HIGH,
                prediction_type=PredictionType.CONFIDENCE_DECLINE
            )
        ]
        
        # Execute adaptation
        adaptations = await engine.preemptively_adapt_responses(predicted_needs)
        
        # Verify telemetry updated
        assert engine._telemetry['preemptively_adapt_responses_count'] == 1
        assert engine._telemetry['total_adaptations_created'] == 1
        assert engine._telemetry['total_execution_time_seconds'] > 0
        
        print(f"✅ PredictiveEngine adaptation telemetry validated: "
              f"{engine._telemetry['preemptively_adapt_responses_count']} adaptations, "
              f"{engine._telemetry['total_adaptations_created']} actions created")


class TestLearningPipelineManagerTelemetry:
    """Test telemetry tracking for LearningPipelineManager."""
    
    @pytest.mark.asyncio
    async def test_start_pipeline_telemetry(self):
        """Test that start_pipeline tracks usage properly."""
        # Create pipeline manager with telemetry
        manager = LearningPipelineManager(
            learning_orchestrator=Mock(),
            predictive_engine=Mock(),
            temporal_client=Mock()
        )
        
        # Verify telemetry initialized
        assert manager._telemetry is not None
        assert manager._telemetry['start_pipeline_count'] == 0
        
        # Mock internal methods to avoid actual pipeline execution
        manager._pipeline_loop = AsyncMock()
        manager.schedule_learning_cycle = AsyncMock(return_value="cycle_123")
        
        # Start pipeline
        await manager.start_pipeline()
        
        # Verify telemetry updated
        assert manager._telemetry['start_pipeline_count'] == 1
        assert manager._running is True
        
        print(f"✅ LearningPipelineManager telemetry validated: "
              f"{manager._telemetry['start_pipeline_count']} starts")
    
    @pytest.mark.asyncio
    async def test_schedule_learning_cycle_telemetry(self):
        """Test that schedule_learning_cycle tracks usage properly."""
        # Create pipeline manager with telemetry
        manager = LearningPipelineManager(
            learning_orchestrator=Mock(),
            predictive_engine=Mock(),
            temporal_client=Mock()
        )
        
        # Mock internal methods
        manager._execute_learning_cycle = AsyncMock()
        
        # Schedule cycle
        cycle_id = await manager.schedule_learning_cycle("Test Cycle", delay_seconds=0)
        
        # Verify telemetry updated
        assert manager._telemetry['schedule_learning_cycle_count'] == 1
        assert cycle_id is not None
        
        print(f"✅ LearningPipelineManager scheduling telemetry validated: "
              f"{manager._telemetry['schedule_learning_cycle_count']} cycles scheduled")
    
    @pytest.mark.asyncio
    async def test_execute_task_telemetry(self):
        """Test that task execution tracks usage properly."""
        # Create mock dependencies
        temporal_client = Mock()
        temporal_client.write_point = AsyncMock()
        
        # Create pipeline manager with telemetry
        manager = LearningPipelineManager(
            learning_orchestrator=Mock(),
            predictive_engine=Mock(),
            temporal_client=temporal_client
        )
        
        # Create test task
        task = PipelineTask(
            name="Test Learning Task",
            category=TaskCategory.TRENDWISE,
            priority=TaskPriority.HIGH,
            stage=PipelineStage.ANALYSIS,
            bot_name="elena",
            estimated_duration_seconds=5
        )
        
        # Mock internal methods
        manager._record_task_event = AsyncMock()
        manager._run_task_function = AsyncMock(return_value={"status": "success"})
        
        # Execute task
        await manager._execute_task(task)
        
        # Verify telemetry updated
        assert manager._telemetry['execute_task_count'] == 1
        assert manager._telemetry['total_tasks_completed'] == 1
        assert manager._telemetry['total_execution_time_seconds'] > 0
        
        # Verify InfluxDB telemetry recorded
        assert temporal_client.write_point.called
        call_args = temporal_client.write_point.call_args[0][0]
        assert call_args['measurement'] == 'component_usage'
        assert call_args['tags']['component'] == 'learning_pipeline_manager'
        assert call_args['tags']['method'] == 'execute_task'
        assert call_args['tags']['task_category'] == 'trendwise'
        assert call_args['tags']['task_stage'] == 'analysis'
        assert call_args['tags']['bot_name'] == 'elena'
        assert call_args['fields']['invocation_count'] == 1
        assert call_args['fields']['total_tasks_completed'] == 1
        
        print(f"✅ LearningPipelineManager task execution telemetry validated: "
              f"{manager._telemetry['execute_task_count']} tasks, "
              f"{manager._telemetry['total_tasks_completed']} completed, "
              f"{manager._telemetry['total_execution_time_seconds']:.3f}s total")


def test_telemetry_summary():
    """Print summary of telemetry implementation."""
    print("\n" + "="*80)
    print("Sprint 6 Learning Component Telemetry Summary")
    print("="*80)
    print("\n✅ TELEMETRY IMPLEMENTED FOR:")
    print("\n1. LearningOrchestrator:")
    print("   - coordinate_learning_cycle_count")
    print("   - monitor_learning_health_count")
    print("   - total_execution_time_seconds")
    print("   - InfluxDB recording to 'component_usage' measurement")
    
    print("\n2. PredictiveAdaptationEngine:")
    print("   - predict_user_needs_count")
    print("   - preemptively_adapt_responses_count")
    print("   - total_predictions_generated")
    print("   - total_adaptations_created")
    print("   - total_execution_time_seconds")
    print("   - InfluxDB recording to 'component_usage' measurement")
    
    print("\n3. LearningPipelineManager:")
    print("   - start_pipeline_count")
    print("   - schedule_learning_cycle_count")
    print("   - execute_task_count")
    print("   - total_tasks_completed")
    print("   - total_tasks_failed")
    print("   - total_execution_time_seconds")
    print("   - InfluxDB recording to 'component_usage' measurement")
    
    print("\n📊 DATA COLLECTION STRATEGY:")
    print("   - All telemetry writes to InfluxDB 'component_usage' measurement")
    print("   - Tags: component, method, bot_name, user_id (where applicable)")
    print("   - Fields: execution_time_seconds, invocation_count, task metrics")
    print("   - Non-intrusive: No behavior changes, monitoring only")
    
    print("\n🎯 EVALUATION PLAN:")
    print("   1. Deploy to production with telemetry enabled")
    print("   2. Collect 1-2 weeks of real usage data")
    print("   3. Query InfluxDB for Sprint 6 component usage patterns")
    print("   4. Analyze: invocation frequency, execution time, feature utilization")
    print("   5. Decision: Keep, optimize, or defer based on actual usage")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
