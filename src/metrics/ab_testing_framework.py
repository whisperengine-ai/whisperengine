"""
A/B Testing Framework for Human-Like AI System
==============================================

Infrastructure for testing different configurations and measuring
improvements to the overall human-like AI performance.
"""

import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
import hashlib

from .holistic_ai_metrics import HolisticAIMetrics, ConversationMetrics, SystemMetrics

logger = logging.getLogger(__name__)

class TestType(Enum):
    """Types of A/B tests"""
    MEMORY_CONFIGURATION = "memory_config"
    EMOTION_SENSITIVITY = "emotion_sensitivity" 
    PERSONALITY_EXPRESSION = "personality_expression"
    RESPONSE_STYLE = "response_style"
    SYSTEM_INTEGRATION = "system_integration"

class TestStatus(Enum):
    """Status of A/B tests"""
    PLANNING = "planning"
    RUNNING = "running"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    PAUSED = "paused"

@dataclass
class TestConfiguration:
    """Configuration for an A/B test variant"""
    test_id: str
    variant_name: str
    test_type: TestType
    configuration: Dict[str, Any]
    traffic_percentage: float  # 0.0 to 1.0
    description: str

@dataclass
class TestResult:
    """Results from an A/B test"""
    test_id: str
    variant_name: str
    user_count: int
    conversation_count: int
    avg_conversation_naturalness: float
    avg_memory_effectiveness: float
    avg_emotional_intelligence: float
    avg_response_time: float
    user_satisfaction: float
    statistical_significance: float
    confidence_interval: Tuple[float, float]

@dataclass
class ABTest:
    """A/B test definition"""
    test_id: str
    test_name: str
    test_type: TestType
    status: TestStatus
    start_date: datetime
    end_date: Optional[datetime]
    variants: List[TestConfiguration]
    success_metric: str
    minimum_sample_size: int
    target_confidence: float  # e.g., 0.95 for 95%
    description: str

class ABTestingFramework:
    """
    A/B testing framework for human-like AI system optimization
    """
    
    def __init__(self, metrics_collector: HolisticAIMetrics, redis_client=None, database_manager=None):
        self.metrics_collector = metrics_collector
        self.redis_client = redis_client
        self.database_manager = database_manager
        
        # Active tests cache
        self.active_tests: Dict[str, ABTest] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> {test_id: variant}
        
        # Pre-defined test configurations
        self.test_configurations = self._initialize_test_configurations()
    
    def _initialize_test_configurations(self) -> Dict[str, Dict]:
        """Initialize standard test configurations"""
        return {
            'memory_optimization': {
                'control': {
                    'memory_limit': 15,
                    'diversity_weight': 0.3,
                    'recency_weight': 0.4,
                    'relevance_threshold': 0.5
                },
                'enhanced_diversity': {
                    'memory_limit': 20,
                    'diversity_weight': 0.5,
                    'recency_weight': 0.3,
                    'relevance_threshold': 0.45
                },
                'focused_relevance': {
                    'memory_limit': 12,
                    'diversity_weight': 0.2,
                    'recency_weight': 0.6,
                    'relevance_threshold': 0.6
                }
            },
            'emotional_sensitivity': {
                'control': {
                    'intervention_threshold': 0.7,
                    'support_sensitivity': 0.5,
                    'proactive_support': True,
                    'emotion_weight_in_response': 0.6
                },
                'highly_sensitive': {
                    'intervention_threshold': 0.6,
                    'support_sensitivity': 0.4,
                    'proactive_support': True,
                    'emotion_weight_in_response': 0.8
                },
                'conservative': {
                    'intervention_threshold': 0.8,
                    'support_sensitivity': 0.6,
                    'proactive_support': True,
                    'emotion_weight_in_response': 0.4
                }
            },
            'personality_expression': {
                'control': {
                    'dream_formality': 0.7,
                    'archaic_language': 0.6,
                    'philosophical_depth': 0.5,
                    'emotional_expression': 0.6
                },
                'more_formal': {
                    'dream_formality': 0.9,
                    'archaic_language': 0.8,
                    'philosophical_depth': 0.7,
                    'emotional_expression': 0.5
                },
                'more_casual': {
                    'dream_formality': 0.5,
                    'archaic_language': 0.4,
                    'philosophical_depth': 0.3,
                    'emotional_expression': 0.7
                }
            },
            'response_timing': {
                'control': {
                    'max_response_time': 2.0,
                    'memory_timeout': 0.5,
                    'emotion_timeout': 0.3,
                    'parallel_processing': True
                },
                'optimized_speed': {
                    'max_response_time': 1.5,
                    'memory_timeout': 0.3,
                    'emotion_timeout': 0.2,
                    'parallel_processing': True
                },
                'quality_focused': {
                    'max_response_time': 3.0,
                    'memory_timeout': 0.8,
                    'emotion_timeout': 0.5,
                    'parallel_processing': False
                }
            }
        }
    
    async def create_test(self, 
                         test_name: str,
                         test_type: TestType,
                         variants: List[Dict[str, Any]],
                         success_metric: str = "conversation_naturalness",
                         duration_days: int = 7,
                         minimum_sample_size: int = 100,
                         target_confidence: float = 0.95) -> str:
        """Create a new A/B test"""
        
        test_id = f"test_{int(datetime.now().timestamp())}_{test_type.value}"
        
        # Create test variants
        test_variants = []
        for i, variant_config in enumerate(variants):
            variant = TestConfiguration(
                test_id=test_id,
                variant_name=variant_config.get('name', f'variant_{i}'),
                test_type=test_type,
                configuration=variant_config.get('config', {}),
                traffic_percentage=variant_config.get('traffic', 1.0 / len(variants)),
                description=variant_config.get('description', '')
            )
            test_variants.append(variant)
        
        # Create A/B test
        ab_test = ABTest(
            test_id=test_id,
            test_name=test_name,
            test_type=test_type,
            status=TestStatus.PLANNING,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=duration_days),
            variants=test_variants,
            success_metric=success_metric,
            minimum_sample_size=minimum_sample_size,
            target_confidence=target_confidence,
            description=f"A/B test for {test_type.value} optimization"
        )
        
        self.active_tests[test_id] = ab_test
        await self._store_test_definition(ab_test)
        
        logger.info(f"Created A/B test: {test_id} - {test_name}")
        return test_id
    
    async def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        if test_id not in self.active_tests:
            logger.error(f"Test {test_id} not found")
            return False
        
        test = self.active_tests[test_id]
        test.status = TestStatus.RUNNING
        
        await self._update_test_status(test_id, TestStatus.RUNNING)
        logger.info(f"Started A/B test: {test_id}")
        return True
    
    async def get_user_variant(self, user_id: str, test_type: TestType) -> Optional[TestConfiguration]:
        """Get the test variant for a user"""
        
        # Find active test for this type
        active_test = None
        for test in self.active_tests.values():
            if test.test_type == test_type and test.status == TestStatus.RUNNING:
                active_test = test
                break
        
        if not active_test:
            return None
        
        test_id = active_test.test_id
        
        # Check if user already assigned
        if user_id in self.user_assignments and test_id in self.user_assignments[user_id]:
            variant_name = self.user_assignments[user_id][test_id]
            return next((v for v in active_test.variants if v.variant_name == variant_name), None)
        
        # Assign user to variant based on consistent hashing
        variant = self._assign_user_to_variant(user_id, active_test)
        
        # Store assignment
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = {}
        self.user_assignments[user_id][test_id] = variant.variant_name
        
        await self._store_user_assignment(user_id, test_id, variant.variant_name)
        
        return variant
    
    def _assign_user_to_variant(self, user_id: str, test: ABTest) -> TestConfiguration:
        """Consistently assign user to test variant"""
        # Use consistent hashing for stable assignments
        hash_input = f"{test.test_id}_{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        normalized_hash = (hash_value % 1000) / 1000.0
        
        # Assign based on traffic percentages
        cumulative_percentage = 0.0
        for variant in test.variants:
            cumulative_percentage += variant.traffic_percentage
            if normalized_hash <= cumulative_percentage:
                return variant
        
        # Fallback to first variant
        return test.variants[0]
    
    async def record_test_interaction(self, 
                                    user_id: str,
                                    test_type: TestType,
                                    metrics: ConversationMetrics):
        """Record interaction data for A/B testing"""
        
        variant = await self.get_user_variant(user_id, test_type)
        if not variant:
            return
        
        # Store interaction with variant information
        interaction_data = {
            'test_id': variant.test_id,
            'variant_name': variant.variant_name,
            'user_id': user_id,
            'metrics': asdict(metrics),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        await self._store_test_interaction(interaction_data)
    
    async def analyze_test_results(self, test_id: str) -> Dict[str, TestResult]:
        """Analyze A/B test results"""
        if test_id not in self.active_tests:
            logger.error(f"Test {test_id} not found")
            return {}
        
        test = self.active_tests[test_id]
        
        # Get interaction data for each variant
        results = {}
        for variant in test.variants:
            variant_data = await self._get_variant_data(test_id, variant.variant_name)
            
            if not variant_data:
                continue
            
            # Calculate aggregate metrics
            metrics_list = [data['metrics'] for data in variant_data]
            
            if not metrics_list:
                continue
            
            # Calculate conversation naturalness scores
            naturalness_scores = []
            for metrics_dict in metrics_list:
                metrics_obj = ConversationMetrics(**metrics_dict)
                cns = await self.metrics_collector.calculate_conversation_naturalness_score(metrics_obj)
                naturalness_scores.append(cns)
            
            # Calculate other aggregate metrics
            avg_cns = statistics.mean(naturalness_scores) if naturalness_scores else 0
            avg_memory = statistics.mean([m.get('memory_relevance_score', 0) for m in metrics_list])
            avg_emotion = statistics.mean([m.get('emotional_appropriateness', 0) for m in metrics_list])
            avg_response_time = statistics.mean([m.get('total_response_time', 0) for m in metrics_list])
            
            # Calculate statistical significance (simplified)
            significance, confidence_interval = self._calculate_statistical_significance(
                naturalness_scores, test.target_confidence
            )
            
            result = TestResult(
                test_id=test_id,
                variant_name=variant.variant_name,
                user_count=len(set(data['user_id'] for data in variant_data)),
                conversation_count=len(variant_data),
                avg_conversation_naturalness=avg_cns,
                avg_memory_effectiveness=avg_memory,
                avg_emotional_intelligence=avg_emotion,
                avg_response_time=avg_response_time,
                user_satisfaction=0.8,  # Placeholder - would calculate from user feedback
                statistical_significance=significance,
                confidence_interval=confidence_interval
            )
            
            results[variant.variant_name] = result
        
        return results
    
    async def get_test_recommendations(self, test_id: str) -> Dict[str, Any]:
        """Get recommendations based on test results"""
        results = await self.analyze_test_results(test_id)
        
        if not results:
            return {"status": "insufficient_data"}
        
        # Find best performing variant
        best_variant = max(
            results.values(),
            key=lambda r: r.avg_conversation_naturalness
        )
        
        # Calculate improvement over control
        control_result = results.get('control') or results.get('variant_0')
        if control_result and best_variant != control_result:
            improvement = (
                (best_variant.avg_conversation_naturalness - control_result.avg_conversation_naturalness) 
                / control_result.avg_conversation_naturalness * 100
            )
        else:
            improvement = 0
        
        # Generate recommendation
        recommendation = {
            "status": "complete",
            "recommended_variant": best_variant.variant_name,
            "improvement_percentage": improvement,
            "confidence": best_variant.statistical_significance,
            "sample_size": best_variant.conversation_count,
            "ready_for_deployment": (
                best_variant.statistical_significance > 0.95 and
                best_variant.conversation_count >= self.active_tests[test_id].minimum_sample_size and
                improvement > 5  # At least 5% improvement
            )
        }
        
        return recommendation
    
    async def create_predefined_test(self, test_category: str, test_name: str) -> str:
        """Create a test using predefined configurations"""
        if test_category not in self.test_configurations:
            raise ValueError(f"Unknown test category: {test_category}")
        
        configs = self.test_configurations[test_category]
        variants = []
        
        for variant_name, config in configs.items():
            variants.append({
                'name': variant_name,
                'config': config,
                'traffic': 1.0 / len(configs),
                'description': f"{variant_name} configuration for {test_category}"
            })
        
        test_type = TestType.MEMORY_CONFIGURATION  # Map categories to types
        if test_category == 'emotional_sensitivity':
            test_type = TestType.EMOTION_SENSITIVITY
        elif test_category == 'personality_expression':
            test_type = TestType.PERSONALITY_EXPRESSION
        
        return await self.create_test(
            test_name=test_name,
            test_type=test_type,
            variants=variants
        )
    
    def _calculate_statistical_significance(self, 
                                          data: List[float], 
                                          target_confidence: float) -> Tuple[float, Tuple[float, float]]:
        """Calculate statistical significance and confidence interval"""
        if len(data) < 10:
            return 0.0, (0.0, 0.0)
        
        mean_val = statistics.mean(data)
        std_dev = statistics.stdev(data) if len(data) > 1 else 0
        
        # Simplified significance calculation
        n = len(data)
        margin_of_error = 1.96 * (std_dev / (n ** 0.5))  # 95% confidence
        
        confidence_interval = (mean_val - margin_of_error, mean_val + margin_of_error)
        
        # Simplified significance score
        significance = min(0.99, max(0.0, (n - 10) / 100))
        
        return significance, confidence_interval
    
    # Storage methods (would integrate with your database)
    async def _store_test_definition(self, test: ABTest):
        """Store A/B test definition"""
        if self.database_manager:
            await self.database_manager.store_ab_test(asdict(test))
    
    async def _update_test_status(self, test_id: str, status: TestStatus):
        """Update test status"""
        if self.database_manager:
            await self.database_manager.update_test_status(test_id, status.value)
    
    async def _store_user_assignment(self, user_id: str, test_id: str, variant_name: str):
        """Store user assignment to variant"""
        if self.redis_client:
            await self.redis_client.set(f"ab_test:{test_id}:user:{user_id}", variant_name)
    
    async def _store_test_interaction(self, interaction_data: Dict):
        """Store test interaction data"""
        if self.database_manager:
            await self.database_manager.store_test_interaction(interaction_data)
    
    async def _get_variant_data(self, test_id: str, variant_name: str) -> List[Dict]:
        """Get interaction data for a specific variant"""
        if self.database_manager:
            return await self.database_manager.get_variant_interactions(test_id, variant_name)
        return []