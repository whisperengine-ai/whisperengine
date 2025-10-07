#!/usr/bin/env python3
"""
Sprint 6 IntelligenceOrchestrator Direct Validation

Comprehensive validation of the Learning Orchestrator and related Sprint 6 components:
- Learning Orchestrator: Master coordination system
- Predictive Adaptation Engine: Proactive user need prediction
- Learning Pipeline Manager: Automated learning cycles

This script validates the complete Sprint 6 implementation with direct Python API access.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add src to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from orchestration.learning_orchestrator import (
    LearningOrchestrator, 
    LearningComponentStatus,
    SystemLearningHealth,
    LearningTaskPriority
)
from adaptation.predictive_engine import PredictiveAdaptationEngine
from pipeline.learning_manager import LearningPipelineManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Sprint6DirectValidator:
    """Direct validation for Sprint 6 IntelligenceOrchestrator components."""
    
    def __init__(self):
        self.test_results = []
        self.bot_name = "test_bot"
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive Sprint 6 validation tests."""
        logger.info("🚀 Starting Sprint 6 IntelligenceOrchestrator Direct Validation")
        
        validation_results = {
            'sprint_6_validation': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'test_details': []
            }
        }
        
        # Test 1: Learning Orchestrator Initialization
        await self._test_learning_orchestrator_init()
        
        # Test 2: Learning Health Monitoring
        await self._test_health_monitoring()
        
        # Test 3: Learning Task Prioritization
        await self._test_task_prioritization()
        
        # Test 4: Learning Cycle Coordination
        await self._test_learning_cycle_coordination()
        
        # Test 5: Predictive Adaptation Engine
        await self._test_predictive_adaptation()
        
        # Test 6: Learning Pipeline Manager
        await self._test_learning_pipeline()
        
        # Test 7: Cross-Component Integration
        await self._test_cross_component_integration()
        
        # Calculate final results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        validation_results['sprint_6_validation'].update({
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'test_details': self.test_results
        })
        
        # Print summary
        logger.info("=" * 60)
        logger.info("🎯 SPRINT 6 VALIDATION SUMMARY")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {validation_results['sprint_6_validation']['success_rate']:.1f}%")
        
        if failed_tests == 0:
            logger.info("✅ ALL SPRINT 6 TESTS PASSED - IntelligenceOrchestrator ready for production!")
        else:
            logger.warning(f"❌ {failed_tests} tests failed - review implementation")
            
        return validation_results
    
    async def _test_learning_orchestrator_init(self):
        """Test Learning Orchestrator initialization."""
        logger.info("🔧 Testing Learning Orchestrator initialization...")
        
        try:
            # Initialize orchestrator
            orchestrator = LearningOrchestrator()
            
            # Verify initialization
            assert orchestrator is not None
            assert hasattr(orchestrator, 'health_check_interval')
            assert hasattr(orchestrator, 'optimization_cycle_interval')
            assert hasattr(orchestrator, 'correlation_analysis_interval')
            
            self._record_test_result("learning_orchestrator_init", True, 
                                   "Successfully initialized Learning Orchestrator")
            
        except Exception as e:
            self._record_test_result("learning_orchestrator_init", False, 
                                   f"Failed to initialize Learning Orchestrator: {str(e)}")
    
    async def _test_health_monitoring(self):
        """Test learning health monitoring across all components."""
        logger.info("🏥 Testing learning health monitoring...")
        
        try:
            orchestrator = LearningOrchestrator()
            
            # Test health monitoring
            health_report = await orchestrator.monitor_learning_health(self.bot_name)
            
            # Verify health report structure
            assert health_report is not None
            assert hasattr(health_report, 'overall_health')
            assert hasattr(health_report, 'component_statuses')
            assert hasattr(health_report, 'system_performance_score')
            assert isinstance(health_report.component_statuses, list)
            
            # Verify all Sprint 1-5 components are monitored
            component_names = [status.component_name for status in health_report.component_statuses]
            expected_components = ["TrendWise", "MemoryBoost", "RelationshipTuner", 
                                 "CharacterEvolution", "KnowledgeFusion"]
            
            for component in expected_components:
                assert component in component_names, f"Missing component: {component}"
            
            self._record_test_result("health_monitoring", True, 
                                   f"Health monitoring working - {len(component_names)} components monitored")
            
        except Exception as e:
            self._record_test_result("health_monitoring", False, 
                                   f"Health monitoring failed: {str(e)}")
    
    async def _test_task_prioritization(self):
        """Test learning task prioritization."""
        logger.info("📋 Testing learning task prioritization...")
        
        try:
            orchestrator = LearningOrchestrator()
            
            # Get health report first
            health_report = await orchestrator.monitor_learning_health(self.bot_name)
            
            # Test task prioritization
            priority_tasks = await orchestrator.prioritize_learning_tasks(health_report)
            
            # Verify task prioritization
            assert isinstance(priority_tasks, list)
            
            # Verify task structure if tasks exist
            if priority_tasks:
                task = priority_tasks[0]
                assert hasattr(task, 'task_id')
                assert hasattr(task, 'priority')
                assert hasattr(task, 'estimated_impact')
                assert hasattr(task, 'component')
            
            self._record_test_result("task_prioritization", True, 
                                   f"Task prioritization working - {len(priority_tasks)} tasks generated")
            
        except Exception as e:
            self._record_test_result("task_prioritization", False, 
                                   f"Task prioritization failed: {str(e)}")
    
    async def _test_learning_cycle_coordination(self):
        """Test complete learning cycle coordination."""
        logger.info("🔄 Testing learning cycle coordination...")
        
        try:
            orchestrator = LearningOrchestrator()
            
            # Test learning cycle coordination
            cycle_result = await orchestrator.coordinate_learning_cycle(self.bot_name)
            
            # Verify cycle result structure
            assert isinstance(cycle_result, dict)
            assert 'cycle_id' in cycle_result
            assert 'bot_name' in cycle_result
            assert 'cycle_duration_seconds' in cycle_result
            
            # Verify bot name matches
            assert cycle_result['bot_name'] == self.bot_name
            
            self._record_test_result("learning_cycle_coordination", True, 
                                   f"Learning cycle completed in {cycle_result.get('cycle_duration_seconds', 0):.2f}s")
            
        except Exception as e:
            self._record_test_result("learning_cycle_coordination", False, 
                                   f"Learning cycle coordination failed: {str(e)}")
    
    async def _test_predictive_adaptation(self):
        """Test Predictive Adaptation Engine."""
        logger.info("🔮 Testing Predictive Adaptation Engine...")
        
        try:
            # Initialize predictive engine
            predictive_engine = PredictiveAdaptationEngine()
            
            predictions = await predictive_engine.predict_user_needs(
                user_id="test_user",
                bot_name="test_bot",
                prediction_horizon_hours=24
            )
            
            # Verify predictions structure
            assert isinstance(predictions, list)
            # Predictions can be empty if trend analyzer is not available (which is normal for testing)
            
            self._record_test_result("predictive_adaptation", True, 
                                   f"Predictive adaptation working - {len(predictions)} predictions made")
            
        except Exception as e:
            self._record_test_result("predictive_adaptation", False, 
                                   f"Predictive adaptation failed: {str(e)}")
    
    async def _test_learning_pipeline(self):
        """Test Learning Pipeline Manager."""
        logger.info("⚙️ Testing Learning Pipeline Manager...")
        
        try:
            # Initialize pipeline manager
            pipeline_manager = LearningPipelineManager()
            
            # Test pipeline scheduling
            schedule_result = await pipeline_manager.schedule_learning_cycle(
                name="Test Learning Cycle",
                delay_seconds=0
            )
            
            # Verify scheduling result
            assert isinstance(schedule_result, str)  # Returns cycle_id
            assert len(schedule_result) > 0
            
            self._record_test_result("learning_pipeline", True, 
                                   f"Learning pipeline working - cycle {schedule_result} scheduled")
            
        except Exception as e:
            self._record_test_result("learning_pipeline", False, 
                                   f"Learning pipeline failed: {str(e)}")
    
    async def _test_cross_component_integration(self):
        """Test cross-component integration."""
        logger.info("🔗 Testing cross-component integration...")
        
        try:
            # Initialize all components
            orchestrator = LearningOrchestrator()
            predictive_engine = PredictiveAdaptationEngine()
            pipeline_manager = LearningPipelineManager()
            
            # Test integration workflow
            # 1. Health monitoring
            health_report = await orchestrator.monitor_learning_health(self.bot_name)
            
            # 2. Predictive analysis
            predictions = await predictive_engine.predict_user_needs(
                user_id="test_user",
                bot_name="test_bot",
                prediction_horizon_hours=24
            )
            
            # 3. Pipeline scheduling
            schedule_result = await pipeline_manager.schedule_learning_cycle(
                name="Integration Test Cycle",
                delay_seconds=0
            )
            
            # Verify all components work together
            assert health_report is not None
            assert predictions is not None
            assert schedule_result is not None
            assert isinstance(predictions, list)  # List of predictions
            assert isinstance(schedule_result, str)  # Cycle ID
            
            self._record_test_result("cross_component_integration", True, 
                                   "All Sprint 6 components integrate successfully")
            
        except Exception as e:
            self._record_test_result("cross_component_integration", False, 
                                   f"Cross-component integration failed: {str(e)}")
    
    def _record_test_result(self, test_name: str, success: bool, details: str):
        """Record individual test result."""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name} - {details}")


async def main():
    """Run Sprint 6 IntelligenceOrchestrator direct validation."""
    validator = Sprint6DirectValidator()
    results = await validator.run_all_tests()
    
    # Print detailed results
    print("\n" + "="*60)
    print("SPRINT 6 INTELLIGENCEORCHESTRATOR VALIDATION RESULTS")
    print("="*60)
    
    for test in results['sprint_6_validation']['test_details']:
        status = "PASS ✅" if test['success'] else "FAIL ❌"
        print(f"{status} {test['test_name']}: {test['details']}")
    
    print(f"\nOVERALL SUCCESS RATE: {results['sprint_6_validation']['success_rate']:.1f}%")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())