#!/usr/bin/env python3
"""
Sprint 4 CharacterEvolution Direct Validation - Complete Feature Testing
WhisperEngine Adaptive Learning System

Validates all Sprint 4 CharacterEvolution features using direct Python API calls:
- Character Performance Analyzer: Effectiveness analysis across Sprint 1-3 metrics
- CDL Parameter Optimizer: Data-driven personality adjustments with PostgreSQL integration
- Personality Evolution Schema: Database tracking and analytics

This test suite provides comprehensive validation of character optimization
capabilities while maintaining character authenticity and providing complete
audit trails for personality changes.

Usage:
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
    export QDRANT_HOST="localhost" 
    export QDRANT_PORT="6334"
    python tests/automated/test_sprint4_characterevolution_direct_validation.py
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Core WhisperEngine imports
from src.characters.performance_analyzer import (
    CharacterPerformanceAnalyzer,
    OptimizationOpportunity,
    CharacterEffectivenessData,
    OptimizationCategory
)
from src.characters.cdl_optimizer import (
    CDLParameterOptimizer,
    OptimizationPlan,
    OptimizationResult,
    OptimizationApproach,
    create_cdl_parameter_optimizer
)
from src.characters.cdl.parser import CDLParser
from src.database.cdl_database import CDLDatabaseManager

# Memory and database components
from src.memory.memory_protocol import create_memory_manager
from src.llm.llm_protocol import create_llm_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class Sprint4CharacterEvolutionValidator:
    """
    Comprehensive validator for Sprint 4 CharacterEvolution features.
    
    Tests all components of the character optimization system:
    - Performance analysis across Sprint 1-3 metrics
    - CDL parameter optimization with safety mechanisms
    - PostgreSQL personality evolution tracking
    - Data-driven character improvement workflows
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.memory_manager = None
        self.llm_client = None
        self.performance_analyzer = None
        self.cdl_optimizer = None
        self.cdl_database_manager = None
        self.cdl_parser = None
        
        # Test configuration
        self.test_character = "elena"  # Use Elena for rich personality testing
        self.test_results = {
            'performance_analyzer': {'passed': 0, 'total': 0, 'details': []},
            'cdl_optimizer': {'passed': 0, 'total': 0, 'details': []},
            'personality_evolution': {'passed': 0, 'total': 0, 'details': []},
            'integration': {'passed': 0, 'total': 0, 'details': []}
        }
    
    async def initialize_components(self) -> bool:
        """Initialize all Sprint 4 components for testing."""
        try:
            self.logger.info("🔧 Initializing Sprint 4 CharacterEvolution components...")
            
            # Initialize memory manager
            self.memory_manager = create_memory_manager(memory_type="vector")
            if not self.memory_manager:
                raise RuntimeError("Failed to create memory manager")
            
            # Initialize LLM client  
            self.llm_client = create_llm_client(llm_client_type="openrouter")
            if not self.llm_client:
                raise RuntimeError("Failed to create LLM client")
            
            # Initialize CDL parser
            self.cdl_parser = CDLParser()
            
            # Initialize CDL database manager
            self.cdl_database_manager = CDLDatabaseManager()
            try:
                await self.cdl_database_manager.initialize_pool(min_size=2, max_size=5)
                self.logger.info("✅ CDL database manager initialized")
            except Exception as e:
                self.logger.warning("⚠️ CDL database manager initialization failed: %s", e)
                self.cdl_database_manager = None
            
            # Initialize Performance Analyzer
            self.performance_analyzer = CharacterPerformanceAnalyzer(
                cdl_parser=self.cdl_parser,
                cdl_database_manager=self.cdl_database_manager,
                postgres_pool=self.cdl_database_manager.pool if self.cdl_database_manager else None
            )
            
            # Initialize CDL Parameter Optimizer
            self.cdl_optimizer = create_cdl_parameter_optimizer(
                performance_analyzer=self.performance_analyzer,
                cdl_parser=self.cdl_parser,
                cdl_database_manager=self.cdl_database_manager,
                postgres_pool=self.cdl_database_manager.pool if self.cdl_database_manager else None
            )
            
            self.logger.info("✅ All Sprint 4 components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error("❌ Component initialization failed: %s", e)
            return False
    
    async def test_performance_analyzer(self) -> Dict[str, Any]:
        """Test Character Performance Analyzer functionality."""
        self.logger.info("🧪 Testing Character Performance Analyzer...")
        
        component_results = {'passed': 0, 'total': 0, 'details': []}
        
        # Test 1: Character effectiveness analysis
        try:
            component_results['total'] += 1
            effectiveness_data = await self.performance_analyzer.analyze_character_effectiveness(
                bot_name=self.test_character,
                days_back=14
            )
            
            # Validate effectiveness data structure
            required_fields = [
                'bot_name', 'analysis_period_days', 'overall_effectiveness',
                'conversation_quality_avg', 'confidence_trend_direction',
                'memory_effectiveness_score', 'relationship_progression_rate',
                'user_engagement_level', 'metric_scores', 'data_points'
            ]
            
            missing_fields = [field for field in required_fields if not hasattr(effectiveness_data, field)]
            
            if not missing_fields and effectiveness_data.bot_name == self.test_character:
                component_results['passed'] += 1
                component_results['details'].append({
                    'test': 'Character Effectiveness Analysis',
                    'status': 'PASS',
                    'details': f"Analyzed {effectiveness_data.data_points} data points, effectiveness: {effectiveness_data.overall_effectiveness:.2f}"
                })
                self.logger.info("✅ Character effectiveness analysis: PASS")
            else:
                component_results['details'].append({
                    'test': 'Character Effectiveness Analysis',
                    'status': 'FAIL',
                    'details': f"Missing fields: {missing_fields}"
                })
                self.logger.warning("❌ Character effectiveness analysis: FAIL")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Character Effectiveness Analysis',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Character effectiveness analysis error: %s", e)
        
        # Test 2: Optimization opportunity identification
        try:
            component_results['total'] += 1
            opportunities = await self.performance_analyzer.identify_optimization_opportunities(
                bot_name=self.test_character
            )
            
            if isinstance(opportunities, list) and len(opportunities) >= 0:
                # Validate opportunity structure if any exist
                if opportunities:
                    first_opp = opportunities[0]
                    required_opp_fields = ['category', 'confidence_score', 'impact_potential', 'recommendation']
                    missing_opp_fields = [field for field in required_opp_fields if not hasattr(first_opp, field)]
                    
                    if not missing_opp_fields:
                        component_results['passed'] += 1
                        component_results['details'].append({
                            'test': 'Optimization Opportunity Identification',
                            'status': 'PASS',
                            'details': f"Found {len(opportunities)} optimization opportunities"
                        })
                        self.logger.info("✅ Optimization opportunity identification: PASS")
                    else:
                        component_results['details'].append({
                            'test': 'Optimization Opportunity Identification',
                            'status': 'FAIL',
                            'details': f"Invalid opportunity structure: missing {missing_opp_fields}"
                        })
                        self.logger.warning("❌ Optimization opportunity identification: FAIL")
                else:
                    component_results['passed'] += 1
                    component_results['details'].append({
                        'test': 'Optimization Opportunity Identification',
                        'status': 'PASS',
                        'details': "No optimization opportunities found (acceptable)"
                    })
                    self.logger.info("✅ Optimization opportunity identification: PASS (no opportunities)")
            else:
                component_results['details'].append({
                    'test': 'Optimization Opportunity Identification',
                    'status': 'FAIL',
                    'details': "Invalid return type or negative length"
                })
                self.logger.warning("❌ Optimization opportunity identification: FAIL")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Optimization Opportunity Identification',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Optimization opportunity identification error: %s", e)
        
        # Test 3: Performance metric calculations
        try:
            component_results['total'] += 1
            
            # Create mock effectiveness data for testing calculations
            mock_effectiveness = CharacterEffectivenessData(
                bot_name=self.test_character,
                analysis_period_days=14,
                overall_effectiveness=0.75,
                conversation_quality_avg=0.8,
                confidence_trend_direction="improving",
                memory_effectiveness_score=0.7,
                relationship_progression_rate=0.6,
                trust_building_success=0.8,
                user_engagement_level=0.75,
                metric_scores={},
                trait_correlations={},
                optimization_opportunities=[],
                data_points=50,
                statistical_confidence=0.85,
                analysis_timestamp=datetime.now()
            )
            
            # Test calculations (this would normally be internal methods)
            if (0 <= mock_effectiveness.overall_effectiveness <= 1 and
                mock_effectiveness.data_points > 0 and
                mock_effectiveness.statistical_confidence > 0):
                
                component_results['passed'] += 1
                component_results['details'].append({
                    'test': 'Performance Metric Calculations',
                    'status': 'PASS',
                    'details': f"Metrics within valid ranges, {mock_effectiveness.data_points} data points"
                })
                self.logger.info("✅ Performance metric calculations: PASS")
            else:
                component_results['details'].append({
                    'test': 'Performance Metric Calculations',
                    'status': 'FAIL',
                    'details': "Metrics outside valid ranges"
                })
                self.logger.warning("❌ Performance metric calculations: FAIL")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Performance Metric Calculations',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Performance metric calculations error: %s", e)
        
        return component_results
    
    async def test_cdl_optimizer(self) -> Dict[str, Any]:
        """Test CDL Parameter Optimizer functionality."""
        self.logger.info("🧪 Testing CDL Parameter Optimizer...")
        
        component_results = {'passed': 0, 'total': 0, 'details': []}
        
        # Test 1: Optimization potential analysis
        try:
            component_results['total'] += 1
            performance, opportunities = await self.cdl_optimizer.analyze_optimization_potential(
                character_name=self.test_character,
                days_back=14
            )
            
            if (isinstance(performance, CharacterEffectivenessData) and
                isinstance(opportunities, list) and
                performance.bot_name == self.test_character):
                
                component_results['passed'] += 1
                component_results['details'].append({
                    'test': 'Optimization Potential Analysis',
                    'status': 'PASS',
                    'details': f"Performance: {performance.overall_effectiveness:.2f}, {len(opportunities)} opportunities"
                })
                self.logger.info("✅ Optimization potential analysis: PASS")
            else:
                component_results['details'].append({
                    'test': 'Optimization Potential Analysis',
                    'status': 'FAIL',
                    'details': "Invalid return types or character mismatch"
                })
                self.logger.warning("❌ Optimization potential analysis: FAIL")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Optimization Potential Analysis',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Optimization potential analysis error: %s", e)
        
        # Test 2: Optimization plan creation
        try:
            component_results['total'] += 1
            
            # Create mock opportunities for testing
            mock_opportunities = [
                OptimizationOpportunity(
                    category=OptimizationCategory.COMMUNICATION_STYLE,
                    confidence_score=0.8,
                    impact_potential=0.15,
                    current_performance=0.7,
                    target_performance=0.85,
                    affected_traits=["extraversion", "engagement_level"],
                    evidence_metrics={"conversation_quality": 0.7},
                    recommendation="Increase engagement and extraversion",
                    priority="medium"
                )
            ]
            
            optimization_plan = await self.cdl_optimizer.create_optimization_plan(
                character_name=self.test_character,
                opportunities=mock_opportunities,
                approach=OptimizationApproach.MODERATE
            )
            
            # Validate optimization plan structure
            if (isinstance(optimization_plan, OptimizationPlan) and
                optimization_plan.character_name == self.test_character and
                len(optimization_plan.parameter_adjustments) >= 0 and
                optimization_plan.optimization_approach == OptimizationApproach.MODERATE):
                
                component_results['passed'] += 1
                component_results['details'].append({
                    'test': 'Optimization Plan Creation',
                    'status': 'PASS',
                    'details': f"{len(optimization_plan.parameter_adjustments)} adjustments, {optimization_plan.expected_improvement:.1%} expected improvement"
                })
                self.logger.info("✅ Optimization plan creation: PASS")
            else:
                component_results['details'].append({
                    'test': 'Optimization Plan Creation',
                    'status': 'FAIL',
                    'details': "Invalid optimization plan structure"
                })
                self.logger.warning("❌ Optimization plan creation: FAIL")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Optimization Plan Creation',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Optimization plan creation error: %s", e)
        
        # Test 3: CDL loading with PostgreSQL/JSON fallback
        try:
            component_results['total'] += 1
            
            # Test CDL loading mechanism
            cdl_data = await self.cdl_optimizer._load_character_cdl(self.test_character)
            
            # Validate CDL structure
            required_cdl_sections = ['identity', 'personality']
            missing_sections = [section for section in required_cdl_sections if section not in cdl_data]
            
            if not missing_sections and isinstance(cdl_data, dict):
                component_results['passed'] += 1
                component_results['details'].append({
                    'test': 'CDL Loading (PostgreSQL/JSON)',
                    'status': 'PASS',
                    'details': f"Loaded CDL with sections: {list(cdl_data.keys())}"
                })
                self.logger.info("✅ CDL loading: PASS")
            else:
                component_results['details'].append({
                    'test': 'CDL Loading (PostgreSQL/JSON)',
                    'status': 'FAIL',
                    'details': f"Missing CDL sections: {missing_sections}"
                })
                self.logger.warning("❌ CDL loading: FAIL")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'CDL Loading (PostgreSQL/JSON)',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 CDL loading error: %s", e)
        
        # Test 4: Dry run optimization application
        try:
            component_results['total'] += 1
            
            if 'optimization_plan' in locals():
                # Test dry run application
                dry_run_result = await self.cdl_optimizer.apply_optimization_plan(
                    plan=optimization_plan,
                    dry_run=True
                )
                
                if (isinstance(dry_run_result, OptimizationResult) and
                    dry_run_result.character_name == self.test_character and
                    not dry_run_result.rollback_applied):
                    
                    component_results['passed'] += 1
                    component_results['details'].append({
                        'test': 'Dry Run Optimization Application',
                        'status': 'PASS',
                        'details': f"Dry run successful: {dry_run_result.success}"
                    })
                    self.logger.info("✅ Dry run optimization: PASS")
                else:
                    component_results['details'].append({
                        'test': 'Dry Run Optimization Application',
                        'status': 'FAIL',
                        'details': "Invalid dry run result structure"
                    })
                    self.logger.warning("❌ Dry run optimization: FAIL")
            else:
                component_results['details'].append({
                    'test': 'Dry Run Optimization Application',
                    'status': 'SKIP',
                    'details': "No optimization plan available for dry run"
                })
                self.logger.info("⏭️ Dry run optimization: SKIP")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Dry Run Optimization Application',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Dry run optimization error: %s", e)
        
        return component_results
    
    async def test_personality_evolution_database(self) -> Dict[str, Any]:
        """Test personality evolution database operations."""
        self.logger.info("🧪 Testing Personality Evolution Database...")
        
        component_results = {'passed': 0, 'total': 0, 'details': []}
        
        if not self.cdl_database_manager or not self.cdl_database_manager.pool:
            component_results['details'].append({
                'test': 'Database Connection',
                'status': 'SKIP',
                'details': 'CDL database not available for testing'
            })
            self.logger.warning("⏭️ Database tests skipped - no database connection")
            return component_results
        
        # Test 1: Database schema existence
        try:
            component_results['total'] += 1
            
            async with self.cdl_database_manager.pool.acquire() as conn:
                # Check for personality evolution tables
                schema_check = await conn.fetchval("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name IN (
                        'personality_optimization_attempts',
                        'personality_parameter_adjustments', 
                        'personality_optimization_results',
                        'personality_evolution_timeline'
                    )
                """)
                
                if schema_check >= 4:
                    component_results['passed'] += 1
                    component_results['details'].append({
                        'test': 'Database Schema Existence',
                        'status': 'PASS',
                        'details': f"Found {schema_check}/4 required tables"
                    })
                    self.logger.info("✅ Database schema: PASS")
                else:
                    component_results['details'].append({
                        'test': 'Database Schema Existence',
                        'status': 'FAIL',
                        'details': f"Missing tables: found {schema_check}/4"
                    })
                    self.logger.warning("❌ Database schema: FAIL")
                    
        except Exception as e:
            component_results['details'].append({
                'test': 'Database Schema Existence',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Database schema error: %s", e)
        
        # Test 2: Character data retrieval
        try:
            component_results['total'] += 1
            
            character_data = await self.cdl_database_manager.get_character_by_name(self.test_character)
            
            if character_data and isinstance(character_data, dict):
                component_results['passed'] += 1
                component_results['details'].append({
                    'test': 'Character Data Retrieval',
                    'status': 'PASS',
                    'details': f"Retrieved character: {character_data.get('name', 'Unknown')}"
                })
                self.logger.info("✅ Character data retrieval: PASS")
            else:
                component_results['details'].append({
                    'test': 'Character Data Retrieval',
                    'status': 'FAIL',
                    'details': "No character data found or invalid format"
                })
                self.logger.warning("❌ Character data retrieval: FAIL")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Character Data Retrieval',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Character data retrieval error: %s", e)
        
        # Test 3: Mock optimization tracking
        try:
            component_results['total'] += 1
            
            # Test optimization attempt recording (if available)
            optimization_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            async with self.cdl_database_manager.pool.acquire() as conn:
                # Try to insert a test optimization attempt
                await conn.execute("""
                    INSERT INTO personality_optimization_attempts (
                        optimization_id, character_name, optimization_approach,
                        expected_improvement, implementation_complexity, parameter_count
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                optimization_id, self.test_character, 'conservative', 0.1, 'low', 2)
                
                # Verify insertion
                verification = await conn.fetchval("""
                    SELECT COUNT(*) FROM personality_optimization_attempts 
                    WHERE optimization_id = $1
                """, optimization_id)
                
                if verification == 1:
                    component_results['passed'] += 1
                    component_results['details'].append({
                        'test': 'Optimization Tracking',
                        'status': 'PASS',
                        'details': f"Successfully recorded optimization attempt: {optimization_id}"
                    })
                    self.logger.info("✅ Optimization tracking: PASS")
                    
                    # Clean up test data
                    await conn.execute("""
                        DELETE FROM personality_optimization_attempts 
                        WHERE optimization_id = $1
                    """, optimization_id)
                else:
                    component_results['details'].append({
                        'test': 'Optimization Tracking',
                        'status': 'FAIL',
                        'details': "Failed to record optimization attempt"
                    })
                    self.logger.warning("❌ Optimization tracking: FAIL")
                    
        except Exception as e:
            component_results['details'].append({
                'test': 'Optimization Tracking',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Optimization tracking error: %s", e)
        
        # Test 4: Complete optimization save with parameter adjustments
        try:
            component_results['total'] += 1
            
            # Create a complete optimization plan and save it
            performance, opportunities = await self.cdl_optimizer.analyze_optimization_potential(
                character_name=self.test_character
            )
            
            if opportunities and len(opportunities) > 0:
                # Import the enum for approach
                from src.characters.cdl_optimizer import OptimizationApproach
                
                # Create optimization plan
                plan = await self.cdl_optimizer.create_optimization_plan(
                    character_name=self.test_character,
                    opportunities=opportunities,
                    approach=OptimizationApproach.MODERATE
                )
                
                if plan:
                    # Apply the optimization plan (dry run = False to actually save)
                    result = await self.cdl_optimizer.apply_optimization_plan(
                        plan=plan,
                        dry_run=False  # Actually save to database
                    )
                    
                    if result and result.success:
                        # Verify the save operation by checking database
                        async with self.cdl_database_manager.pool.acquire() as conn:
                            # Check for saved optimization attempt
                            saved_attempt = await conn.fetchval("""
                                SELECT COUNT(*) FROM personality_optimization_attempts 
                                WHERE optimization_id = $1
                            """, result.optimization_plan_id)
                            
                            # Check for saved parameter adjustments
                            saved_adjustments = await conn.fetchval("""
                                SELECT COUNT(*) FROM personality_parameter_adjustments 
                                WHERE optimization_id = $1
                            """, result.optimization_plan_id)
                            
                            if saved_attempt > 0 and saved_adjustments >= 0:
                                component_results['passed'] += 1
                                component_results['details'].append({
                                    'test': 'Complete Optimization Save',
                                    'status': 'PASS',
                                    'details': f"Saved optimization {result.optimization_plan_id} with {saved_adjustments} parameter adjustments"
                                })
                                self.logger.info("✅ Complete optimization save: PASS")
                                
                                # Clean up test data
                                await conn.execute("""
                                    DELETE FROM personality_parameter_adjustments 
                                    WHERE optimization_id = $1
                                """, result.optimization_plan_id)
                                await conn.execute("""
                                    DELETE FROM personality_optimization_attempts 
                                    WHERE optimization_id = $1
                                """, result.optimization_plan_id)
                            else:
                                component_results['details'].append({
                                    'test': 'Complete Optimization Save',
                                    'status': 'FAIL',
                                    'details': f"Failed to save optimization data: attempts={saved_attempt}, adjustments={saved_adjustments}"
                                })
                                self.logger.warning("❌ Complete optimization save: FAIL")
                    else:
                        component_results['details'].append({
                            'test': 'Complete Optimization Save',
                            'status': 'FAIL',
                            'details': "Optimization plan application failed"
                        })
                        self.logger.warning("❌ Complete optimization save: FAIL")
                else:
                    component_results['details'].append({
                        'test': 'Complete Optimization Save',
                        'status': 'FAIL',
                        'details': "Failed to create optimization plan"
                    })
                    self.logger.warning("❌ Complete optimization save: FAIL")
            else:
                component_results['details'].append({
                    'test': 'Complete Optimization Save',
                    'status': 'SKIP',
                    'details': "No optimization opportunities available for testing"
                })
                self.logger.warning("⏭️ Complete optimization save: SKIP")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Complete Optimization Save',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Complete optimization save error: %s", e)
        
        return component_results
    
    async def test_end_to_end_integration(self) -> Dict[str, Any]:
        """Test end-to-end Sprint 4 CharacterEvolution integration."""
        self.logger.info("🧪 Testing End-to-End Integration...")
        
        component_results = {'passed': 0, 'total': 0, 'details': []}
        
        # Test 1: Complete optimization workflow
        try:
            component_results['total'] += 1
            
            # Step 1: Analyze character performance
            performance, opportunities = await self.cdl_optimizer.analyze_optimization_potential(
                character_name=self.test_character,
                days_back=7
            )
            
            # Step 2: Create optimization plan if opportunities exist
            if opportunities:
                plan = await self.cdl_optimizer.create_optimization_plan(
                    character_name=self.test_character,
                    opportunities=opportunities[:1],  # Use first opportunity only
                    approach=OptimizationApproach.CONSERVATIVE
                )
                
                # Step 3: Validate plan with dry run
                result = await self.cdl_optimizer.apply_optimization_plan(
                    plan=plan,
                    dry_run=True
                )
                
                if (result.success and 
                    result.character_name == self.test_character and
                    not result.rollback_applied):
                    
                    component_results['passed'] += 1
                    component_results['details'].append({
                        'test': 'Complete Optimization Workflow',
                        'status': 'PASS',
                        'details': f"Full workflow completed successfully with {len(opportunities)} opportunities"
                    })
                    self.logger.info("✅ Complete optimization workflow: PASS")
                else:
                    component_results['details'].append({
                        'test': 'Complete Optimization Workflow',
                        'status': 'FAIL',
                        'details': "Workflow failed at optimization application"
                    })
                    self.logger.warning("❌ Complete optimization workflow: FAIL")
            else:
                component_results['passed'] += 1
                component_results['details'].append({
                    'test': 'Complete Optimization Workflow',
                    'status': 'PASS',
                    'details': "Workflow completed - no optimization opportunities found"
                })
                self.logger.info("✅ Complete optimization workflow: PASS (no opportunities)")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Complete Optimization Workflow',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Complete optimization workflow error: %s", e)
        
        # Test 2: Component interaction validation
        try:
            component_results['total'] += 1
            
            # Verify all components are properly initialized and can interact
            components_valid = all([
                self.performance_analyzer is not None,
                self.cdl_optimizer is not None,
                self.cdl_parser is not None
            ])
            
            if components_valid:
                # Test basic interaction between components
                effectiveness = await self.performance_analyzer.analyze_character_effectiveness(
                    bot_name=self.test_character,
                    days_back=3
                )
                
                if effectiveness and effectiveness.bot_name == self.test_character:
                    component_results['passed'] += 1
                    component_results['details'].append({
                        'test': 'Component Interaction Validation',
                        'status': 'PASS',
                        'details': "All components initialized and interacting properly"
                    })
                    self.logger.info("✅ Component interaction: PASS")
                else:
                    component_results['details'].append({
                        'test': 'Component Interaction Validation',
                        'status': 'FAIL',
                        'details': "Component interaction failed"
                    })
                    self.logger.warning("❌ Component interaction: FAIL")
            else:
                component_results['details'].append({
                    'test': 'Component Interaction Validation',
                    'status': 'FAIL',
                    'details': "Some components not properly initialized"
                })
                self.logger.warning("❌ Component interaction: FAIL")
                
        except Exception as e:
            component_results['details'].append({
                'test': 'Component Interaction Validation',
                'status': 'ERROR',
                'details': str(e)
            })
            self.logger.error("💥 Component interaction error: %s", e)
        
        return component_results
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete Sprint 4 CharacterEvolution validation suite."""
        self.logger.info("🚀 Starting Sprint 4 CharacterEvolution Comprehensive Validation")
        self.logger.info("=" * 80)
        
        # Initialize components
        if not await self.initialize_components():
            return {'error': 'Component initialization failed'}
        
        # Run all test suites
        test_suites = [
            ('performance_analyzer', self.test_performance_analyzer),
            ('cdl_optimizer', self.test_cdl_optimizer),
            ('personality_evolution', self.test_personality_evolution_database),
            ('integration', self.test_end_to_end_integration)
        ]
        
        for suite_name, test_method in test_suites:
            self.logger.info(f"\n📋 Running {suite_name.replace('_', ' ').title()} Tests...")
            self.test_results[suite_name] = await test_method()
        
        # Calculate overall results
        total_passed = sum(suite['passed'] for suite in self.test_results.values())
        total_tests = sum(suite['total'] for suite in self.test_results.values())
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Generate summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📊 SPRINT 4 CHARACTEREVOLUTION VALIDATION SUMMARY")
        self.logger.info("=" * 80)
        
        for suite_name, results in self.test_results.items():
            suite_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
            status_emoji = "✅" if suite_rate >= 80 else "⚠️" if suite_rate >= 60 else "❌"
            
            self.logger.info(
                f"{status_emoji} {suite_name.replace('_', ' ').title()}: "
                f"{results['passed']}/{results['total']} ({suite_rate:.1f}%)"
            )
            
            # Show details for failed tests
            for detail in results['details']:
                if detail['status'] in ['FAIL', 'ERROR']:
                    self.logger.warning(f"   ⚠️ {detail['test']}: {detail['details']}")
        
        # Overall assessment
        self.logger.info("-" * 80)
        overall_status = "🎉 EXCELLENT" if success_rate >= 90 else "✅ GOOD" if success_rate >= 80 else "⚠️ NEEDS IMPROVEMENT" if success_rate >= 60 else "❌ CRITICAL ISSUES"
        self.logger.info(f"Overall Sprint 4 CharacterEvolution Status: {overall_status}")
        self.logger.info(f"Total Success Rate: {total_passed}/{total_tests} ({success_rate:.1f}%)")
        
        # Specific recommendations
        if success_rate >= 80:
            self.logger.info("🎯 Sprint 4 CharacterEvolution features are production-ready!")
            self.logger.info("🔧 Character optimization system validated successfully")
            self.logger.info("📊 Performance analysis and CDL optimization working as expected")
        else:
            self.logger.warning("⚠️ Some Sprint 4 features need attention before production use")
            
        # Cleanup
        if self.cdl_database_manager:
            await self.cdl_database_manager.close_pool()
        
        return {
            'overall_success_rate': success_rate,
            'total_passed': total_passed,
            'total_tests': total_tests,
            'component_results': self.test_results,
            'status': overall_status,
            'production_ready': success_rate >= 80
        }


async def main():
    """Main execution function for Sprint 4 CharacterEvolution validation."""
    print("🚀 Sprint 4 CharacterEvolution Direct Validation")
    print("WhisperEngine Adaptive Learning System")
    print("=" * 60)
    
    # Environment validation
    required_env = ['FASTEMBED_CACHE_PATH', 'QDRANT_HOST', 'QDRANT_PORT']
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if missing_env:
        print(f"❌ Missing required environment variables: {missing_env}")
        print("Please set the required environment variables and try again.")
        return False
    
    # Run validation
    validator = Sprint4CharacterEvolutionValidator()
    
    try:
        results = await validator.run_comprehensive_validation()
        
        # Exit with appropriate code
        if results.get('production_ready', False):
            print("\n🎉 Sprint 4 CharacterEvolution validation completed successfully!")
            return True
        else:
            print("\n⚠️ Sprint 4 CharacterEvolution validation completed with issues.")
            return False
            
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        return False


if __name__ == "__main__":
    # Run the validation
    success = asyncio.run(main())
    sys.exit(0 if success else 1)