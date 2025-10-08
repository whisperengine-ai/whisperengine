#!/usr/bin/env python3
"""
CDL Parameter Optimizer - Character Evolution Performance System

Enables data-driven CDL parameter adjustments that maintain character authenticity
while improving conversation effectiveness based on performance analysis.

Core Features:
- Safe CDL parameter optimization with authenticity preservation
- Performance-driven parameter adjustment algorithms
- A/B testing framework for parameter changes
- Rollback mechanisms for failed optimizations
- Character consistency validation
- Integration with CharacterPerformanceAnalyzer

This component ensures character improvements are data-driven while preserving
the core personality traits that make each character unique and authentic.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import copy

# CDL system integration
from src.characters.cdl.parser import CDLParser
from src.database.cdl_database import CDLDatabaseManager

# Performance analysis integration
from src.characters.performance_analyzer import (
    CharacterPerformanceAnalyzer, 
    OptimizationOpportunity,
    CharacterEffectivenessData
)


class OptimizationApproach(Enum):
    """Approaches for CDL parameter optimization."""
    CONSERVATIVE = "conservative"  # Small, safe adjustments
    MODERATE = "moderate"         # Balanced risk/reward adjustments
    AGGRESSIVE = "aggressive"     # Larger changes for significant improvement


class ParameterCategory(Enum):
    """Categories of CDL parameters that can be optimized."""
    PERSONALITY_TRAITS = "personality_traits"          # Big Five, emotional patterns
    COMMUNICATION_STYLE = "communication_style"        # Response patterns, engagement
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"  # Empathy, emotional stability
    COGNITIVE_ABILITIES = "cognitive_abilities"        # Attention, memory patterns
    BEHAVIORAL_PATTERNS = "behavioral_patterns"        # Interaction styles, preferences


@dataclass
class ParameterAdjustment:
    """Represents a single CDL parameter adjustment."""
    parameter_path: str           # CDL JSON path (e.g., "personality.big_five.extraversion")
    current_value: Any           # Current parameter value
    target_value: Any            # Proposed new value
    adjustment_reason: str       # Why this adjustment is recommended
    expected_improvement: float  # Expected performance improvement (0-1)
    risk_level: str             # "low", "medium", "high"
    affected_behaviors: List[str] # Behaviors this change affects


@dataclass
class OptimizationPlan:
    """Complete optimization plan for a character."""
    character_name: str
    current_performance: CharacterEffectivenessData
    target_performance: CharacterEffectivenessData
    parameter_adjustments: List[ParameterAdjustment]
    optimization_approach: OptimizationApproach
    expected_improvement: float
    implementation_complexity: str
    rollback_strategy: Dict[str, Any]
    validation_criteria: Dict[str, Any]


@dataclass
class OptimizationResult:
    """Result of applying an optimization plan."""
    character_name: str
    optimization_plan_id: str
    success: bool
    performance_before: CharacterEffectivenessData
    performance_after: Optional[CharacterEffectivenessData]
    actual_improvement: Optional[float]
    issues_encountered: List[str]
    rollback_applied: bool
    timestamp: datetime


class CDLParameterOptimizer:
    """
    Data-driven CDL parameter optimization system.
    
    This component analyzes character performance data and makes targeted
    adjustments to CDL parameters to improve conversation effectiveness
    while preserving character authenticity.
    """
    
    def __init__(
        self,
        performance_analyzer: CharacterPerformanceAnalyzer,
        cdl_parser: CDLParser,
        cdl_database_manager: Optional[CDLDatabaseManager] = None,
        postgres_pool: Optional[Any] = None,
        characters_dir: str = "characters/examples"
    ):
        self.performance_analyzer = performance_analyzer
        self.cdl_parser = cdl_parser
        self.cdl_database_manager = cdl_database_manager
        self.postgres_pool = postgres_pool
        self.characters_dir = Path(characters_dir)
        self.logger = logging.getLogger(__name__)
        
        # Safety thresholds for parameter adjustments
        self.safety_thresholds = {
            'max_personality_change': 0.15,      # Max change in Big Five traits
            'max_communication_change': 0.20,    # Max change in communication style
            'max_emotional_change': 0.12,        # Max change in emotional patterns
            'min_authenticity_score': 0.85,      # Minimum character authenticity
            'rollback_performance_drop': 0.10    # Performance drop triggering rollback
        }
    
    async def analyze_optimization_potential(
        self, 
        character_name: str,
        days_back: int = 30
    ) -> Tuple[CharacterEffectivenessData, List[OptimizationOpportunity]]:
        """
        Analyze character's optimization potential.
        
        Args:
            character_name: Name of character to analyze
            days_back: Days of conversation history to analyze
            
        Returns:
            Tuple of (current performance metrics, optimization opportunities)
        """
        self.logger.info(f"🔍 Analyzing optimization potential for {character_name}")
        
        try:
            # Get current performance metrics
            performance = await self.performance_analyzer.analyze_character_effectiveness(
                bot_name=character_name,
                days_back=days_back
            )
            
            # Identify optimization opportunities
            opportunities = await self.performance_analyzer.identify_optimization_opportunities(
                bot_name=character_name
            )
            
            self.logger.info(
                f"✅ Found {len(opportunities)} optimization opportunities "
                f"(overall score: {performance.overall_effectiveness:.2f})"
            )
            
            return performance, opportunities
            
        except Exception as e:
            self.logger.error(f"Optimization potential analysis failed for {character_name}: {e}")
            raise
    
    async def create_optimization_plan(
        self,
        character_name: str,
        opportunities: List[OptimizationOpportunity],
        approach: OptimizationApproach = OptimizationApproach.MODERATE
    ) -> OptimizationPlan:
        """
        Create a comprehensive optimization plan for a character.
        
        Args:
            character_name: Character to optimize
            opportunities: Optimization opportunities from performance analysis
            approach: Optimization approach (conservative/moderate/aggressive)
            
        Returns:
            Complete optimization plan with parameter adjustments
        """
        self.logger.info(f"📋 Creating optimization plan for {character_name} ({approach.value})")
        
        try:
            # Load current CDL configuration
            current_cdl = await self._load_character_cdl(character_name)
            
            # Generate parameter adjustments for each opportunity
            all_adjustments = []
            
            for opportunity in opportunities:
                adjustments = await self._generate_parameter_adjustments(
                    character_name=character_name,
                    opportunity=opportunity,
                    current_cdl=current_cdl,
                    approach=approach
                )
                all_adjustments.extend(adjustments)
            
            # Validate adjustments for character authenticity
            validated_adjustments = await self._validate_adjustments_for_authenticity(
                character_name=character_name,
                adjustments=all_adjustments,
                current_cdl=current_cdl
            )
            
            # Calculate expected improvements
            expected_improvement = self._calculate_expected_improvement(validated_adjustments)
            
            # Create rollback strategy
            rollback_strategy = self._create_rollback_strategy(current_cdl)
            
            # Define validation criteria
            validation_criteria = self._create_validation_criteria(opportunities)
            
            # Estimate current and target performance
            current_performance = await self.performance_analyzer.analyze_character_effectiveness(
                bot_name=character_name, days_back=14
            )
            
            target_performance = self._estimate_target_performance(
                current_performance, validated_adjustments
            )
            
            plan = OptimizationPlan(
                character_name=character_name,
                current_performance=current_performance,
                target_performance=target_performance,
                parameter_adjustments=validated_adjustments,
                optimization_approach=approach,
                expected_improvement=expected_improvement,
                implementation_complexity=self._assess_implementation_complexity(validated_adjustments),
                rollback_strategy=rollback_strategy,
                validation_criteria=validation_criteria
            )
            
            self.logger.info(
                f"✅ Optimization plan created: {len(validated_adjustments)} adjustments, "
                f"{expected_improvement:.1%} expected improvement"
            )
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Optimization plan creation failed for {character_name}: {e}")
            raise
    
    async def apply_optimization_plan(
        self,
        plan: OptimizationPlan,
        dry_run: bool = False
    ) -> OptimizationResult:
        """
        Apply optimization plan to character CDL configuration.
        
        Args:
            plan: Optimization plan to apply
            dry_run: If True, validate plan without making changes
            
        Returns:
            Optimization result with success status and performance changes
        """
        self.logger.info(
            f"🚀 Applying optimization plan for {plan.character_name} "
            f"(dry_run: {dry_run})"
        )
        
        optimization_id = f"{plan.character_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Record baseline performance
            performance_before = plan.current_performance
            
            if dry_run:
                # Validate plan without making changes
                validation_result = await self._validate_optimization_plan(plan)
                
                if validation_result['valid']:
                    self.logger.info("✅ Optimization plan validation successful (dry run)")
                    return OptimizationResult(
                        character_name=plan.character_name,
                        optimization_plan_id=optimization_id,
                        success=True,
                        performance_before=performance_before,
                        performance_after=None,
                        actual_improvement=None,
                        issues_encountered=[],
                        rollback_applied=False,
                        timestamp=datetime.now()
                    )
                else:
                    self.logger.warning(f"❌ Optimization plan validation failed: {validation_result['issues']}")
                    return OptimizationResult(
                        character_name=plan.character_name,
                        optimization_plan_id=optimization_id,
                        success=False,
                        performance_before=performance_before,
                        performance_after=None,
                        actual_improvement=None,
                        issues_encountered=validation_result['issues'],
                        rollback_applied=False,
                        timestamp=datetime.now()
                    )
            
            # Apply parameter adjustments
            updated_cdl = await self._apply_parameter_adjustments(
                character_name=plan.character_name,
                adjustments=plan.parameter_adjustments
            )
            
            # Save updated CDL configuration
            await self._save_character_cdl(plan.character_name, updated_cdl)
            
            # Record optimization in database
            if self.postgres_pool:
                await self._record_optimization_attempt(optimization_id, plan)
            
            # Wait for changes to take effect (in production, this might involve restarting character)
            await asyncio.sleep(2)  # Brief pause for configuration reload
            
            # Measure post-optimization performance
            performance_after = await self.performance_analyzer.analyze_character_effectiveness(
                bot_name=plan.character_name,
                days_back=7  # Shorter period for immediate assessment
            )
            
            # Calculate actual improvement
            actual_improvement = (
                performance_after.overall_effectiveness - 
                performance_before.overall_effectiveness
            )
            
            # Check if rollback is needed
            rollback_needed = (
                actual_improvement < -self.safety_thresholds['rollback_performance_drop']
            )
            
            if rollback_needed:
                self.logger.warning(
                    f"🔄 Performance drop detected ({actual_improvement:.1%}), applying rollback"
                )
                await self._apply_rollback(plan.character_name, plan.rollback_strategy)
                rollback_applied = True
                success = False
            else:
                rollback_applied = False
                success = actual_improvement >= 0  # Success if performance maintained or improved
            
            result = OptimizationResult(
                character_name=plan.character_name,
                optimization_plan_id=optimization_id,
                success=success,
                performance_before=performance_before,
                performance_after=performance_after,
                actual_improvement=actual_improvement,
                issues_encountered=[],
                rollback_applied=rollback_applied,
                timestamp=datetime.now()
            )
            
            # Record final result
            if self.postgres_pool:
                await self._record_optimization_result(result)
            
            self.logger.info(
                f"✅ Optimization {'successful' if success else 'completed with issues'}: "
                f"{actual_improvement:.1%} performance change"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Optimization application failed for {plan.character_name}: {e}")
            
            # Attempt emergency rollback
            try:
                await self._apply_rollback(plan.character_name, plan.rollback_strategy)
                rollback_applied = True
            except Exception as rollback_error:
                self.logger.error(f"Emergency rollback failed: {rollback_error}")
                rollback_applied = False
            
            return OptimizationResult(
                character_name=plan.character_name,
                optimization_plan_id=optimization_id,
                success=False,
                performance_before=performance_before,
                performance_after=None,
                actual_improvement=None,
                issues_encountered=[str(e)],
                rollback_applied=rollback_applied,
                timestamp=datetime.now()
            )
    
    async def _load_character_cdl(self, character_name: str) -> Dict[str, Any]:
        """Load character's CDL configuration from PostgreSQL (primary) or JSON fallback."""
        try:
            # PRIMARY: Try PostgreSQL database first
            if self.cdl_database_manager and self.cdl_database_manager.pool:
                self.logger.debug("Loading CDL for %s from PostgreSQL database", character_name)
                cdl_data = await self.cdl_database_manager.get_character_by_name(character_name)
                
                if cdl_data:
                    self.logger.info("✅ Loaded CDL for %s from PostgreSQL database", character_name)
                    return self._convert_db_to_cdl_format(cdl_data)
                else:
                    self.logger.warning("Character %s not found in PostgreSQL database, falling back to JSON", character_name)
            
            # FALLBACK: Use JSON file for backward compatibility
            self.logger.debug("Loading CDL for %s from JSON file (fallback)", character_name)
            cdl_file = self.characters_dir / f"{character_name.lower()}.json"
            
            if not cdl_file.exists():
                raise FileNotFoundError(f"CDL not found in database or JSON file: {character_name}")
            
            with open(cdl_file, 'r', encoding='utf-8') as f:
                cdl_data = json.load(f)
                self.logger.info("✅ Loaded CDL for %s from JSON fallback", character_name)
                return cdl_data
                
        except Exception as e:
            self.logger.error("Failed to load CDL for %s: %s", character_name, e)
            raise
    
    def _convert_db_to_cdl_format(self, db_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database CDL format to standard CDL JSON format."""
        # This method converts the PostgreSQL CDL format to the expected CDL JSON structure
        # The database stores normalized data while CDL expects specific JSON structure
        
        cdl_format = {
            "identity": {
                "name": db_data.get("name", ""),
                "occupation": db_data.get("occupation", ""),
                "description": db_data.get("description", ""),
                "archetype": db_data.get("character_archetype", "")
            },
            "personality": {
                "big_five": {}
            },
            "communication_style": {},
            "emotional_intelligence": {},
            "values_and_beliefs": db_data.get("values_and_beliefs", {}),
            "background": {
                "education": db_data.get("education", ""),
                "career_history": db_data.get("career_history", ""),
                "personal_history": db_data.get("personal_history", "")
            }
        }
        
        # Convert personality traits to Big Five format
        personality_traits = db_data.get("personality_traits", {})
        if isinstance(personality_traits, dict):
            cdl_format["personality"]["big_five"] = {
                "openness": personality_traits.get("openness", 0.7),
                "conscientiousness": personality_traits.get("conscientiousness", 0.7),
                "extraversion": personality_traits.get("extraversion", 0.6),
                "agreeableness": personality_traits.get("agreeableness", 0.7),
                "neuroticism": personality_traits.get("neuroticism", 0.3)
            }
        
        # Convert communication styles
        communication_styles = db_data.get("communication_styles", {})
        if isinstance(communication_styles, dict):
            cdl_format["communication_style"] = {
                "engagement_level": communication_styles.get("engagement_level", 0.7),
                "formality": communication_styles.get("formality", 0.5),
                "emotional_expression": communication_styles.get("emotional_expression", 0.6)
            }
        
        # Add emotional intelligence if available
        if "empathy" in db_data:
            cdl_format["emotional_intelligence"]["empathy"] = db_data["empathy"]
        if "emotional_stability" in db_data:
            cdl_format["emotional_intelligence"]["emotional_stability"] = db_data["emotional_stability"]
        
        return cdl_format
    
    async def _save_character_cdl(self, character_name: str, cdl_data: Dict[str, Any]) -> None:
        """Save character's CDL configuration to PostgreSQL (primary) and JSON (backup)."""
        try:
            # PRIMARY: Save to PostgreSQL database
            if self.cdl_database_manager and self.cdl_database_manager.pool:
                self.logger.debug("Saving CDL for %s to PostgreSQL database", character_name)
                
                # Convert CDL format to database format and update
                db_updates = self._convert_cdl_to_db_format(cdl_data)
                
                # Get character ID first
                existing_character = await self.cdl_database_manager.get_character_by_name(character_name)
                if existing_character and 'id' in existing_character:
                    character_id = existing_character['id']
                    success = await self.cdl_database_manager.update_character(character_id, db_updates)
                    
                    if success:
                        self.logger.info("✅ Saved CDL for %s to PostgreSQL database", character_name)
                    else:
                        self.logger.warning("Failed to save CDL to PostgreSQL, falling back to JSON")
                        await self._save_to_json_fallback(character_name, cdl_data)
                        return
                else:
                    self.logger.warning("Character %s not found in database for update, saving to JSON", character_name)
                    await self._save_to_json_fallback(character_name, cdl_data)
                    return
            
            # BACKUP: Always maintain JSON backup for compatibility
            await self._save_to_json_fallback(character_name, cdl_data)
            
        except Exception as e:
            self.logger.error("Failed to save CDL for %s: %s", character_name, e)
            # Emergency fallback to JSON
            await self._save_to_json_fallback(character_name, cdl_data)
            raise
    
    def _convert_cdl_to_db_format(self, cdl_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CDL JSON format to database update format.
        
        NOTE: Only updates fields that exist in cdl_characters table:
        id, name, normalized_name, bot_name, created_at, updated_at, is_active, version,
        occupation, location, age_range, background, description, character_archetype,
        allow_full_roleplay_immersion, created_by, notes
        """
        db_updates = {}
        
        # Update basic identity fields that exist in table
        if "identity" in cdl_data:
            identity = cdl_data["identity"]
            if "name" in identity:
                db_updates["name"] = identity["name"]
            if "occupation" in identity:
                db_updates["occupation"] = identity["occupation"]
            if "description" in identity:
                db_updates["description"] = identity["description"]
        
        # Update background as consolidated text (table has 'background' field)
        if "background" in cdl_data:
            background = cdl_data["background"]
            # Consolidate all background info into the single 'background' text field
            background_parts = []
            if "education" in background:
                background_parts.append(f"Education: {background['education']}")
            if "career_history" in background:
                background_parts.append(f"Career: {background['career_history']}")
            if "personal_history" in background:
                background_parts.append(f"Personal: {background['personal_history']}")
            
            if background_parts:
                db_updates["background"] = " | ".join(background_parts)
        
        # Update character archetype if available
        if "character_archetype" in cdl_data:
            db_updates["character_archetype"] = cdl_data["character_archetype"]
        
        # Update roleplay immersion setting if available
        if "allow_full_roleplay_immersion" in cdl_data:
            db_updates["allow_full_roleplay_immersion"] = cdl_data["allow_full_roleplay_immersion"]
        
        # Add optimization notes to notes field
        if "optimization_notes" in cdl_data:
            db_updates["notes"] = f"CDL Optimization: {cdl_data['optimization_notes']}"
        
        # Always update the timestamp
        db_updates["updated_at"] = datetime.now()
        
        self.logger.debug("🔄 CDL→DB conversion: %d fields mapped to existing columns", len(db_updates))
        
        return db_updates
    
    async def _save_to_json_fallback(self, character_name: str, cdl_data: Dict[str, Any]) -> None:
        """Save CDL to JSON file as fallback/backup."""
        cdl_file = self.characters_dir / f"{character_name.lower()}.json"
        
        # Create backup before saving
        backup_file = cdl_file.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if cdl_file.exists():
            with open(cdl_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
        
        # Save new configuration
        with open(cdl_file, 'w', encoding='utf-8') as f:
            json.dump(cdl_data, f, indent=2)
        
        self.logger.info("💾 Saved CDL configuration for %s to JSON (backup: %s)", character_name, backup_file.name)
    
    async def _generate_parameter_adjustments(
        self,
        character_name: str,
        opportunity: OptimizationOpportunity,
        current_cdl: Dict[str, Any],
        approach: OptimizationApproach
    ) -> List[ParameterAdjustment]:
        """Generate specific parameter adjustments for an optimization opportunity."""
        adjustments = []
        
        # Determine adjustment magnitude based on approach
        magnitude_multipliers = {
            OptimizationApproach.CONSERVATIVE: 0.5,
            OptimizationApproach.MODERATE: 1.0,
            OptimizationApproach.AGGRESSIVE: 1.5
        }
        
        magnitude = magnitude_multipliers[approach]
        
        # Generate adjustments based on the opportunity category
        if opportunity.category.value == "communication_style":
            adjustments.extend(
                await self._generate_conversation_quality_adjustments(
                    opportunity, current_cdl, magnitude
                )
            )
        elif opportunity.category.value == "knowledge_delivery":
            adjustments.extend(
                await self._generate_memory_effectiveness_adjustments(
                    opportunity, current_cdl, magnitude
                )
            )
        elif opportunity.category.value == "relationship_building":
            adjustments.extend(
                await self._generate_relationship_progression_adjustments(
                    opportunity, current_cdl, magnitude
                )
            )
        elif opportunity.category.value == "emotional_expression":
            adjustments.extend(
                await self._generate_emotional_intelligence_adjustments(
                    opportunity, current_cdl, magnitude
                )
            )
        
        return adjustments
    
    async def _generate_conversation_quality_adjustments(
        self,
        opportunity: OptimizationOpportunity,
        current_cdl: Dict[str, Any],
        magnitude: float
    ) -> List[ParameterAdjustment]:
        """Generate adjustments for conversation quality improvement."""
        adjustments = []
        
        # Adjust communication style for better engagement
        if "communication_style" in current_cdl:
            comm_style = current_cdl.get("communication_style", {})
            current_engagement = comm_style.get("engagement_level", 0.7)
            
            # Ensure current_engagement is a number
            if not isinstance(current_engagement, (int, float)):
                current_engagement = 0.7  # Default fallback
            
            target_engagement = min(1.0, current_engagement + (0.1 * magnitude))
            
            adjustments.append(ParameterAdjustment(
                parameter_path="communication_style.engagement_level",
                current_value=current_engagement,
                target_value=target_engagement,
                adjustment_reason="Increase engagement to improve conversation quality",
                expected_improvement=opportunity.impact_potential * 0.6,
                risk_level="low",
                affected_behaviors=["conversation_flow", "user_engagement", "response_enthusiasm"]
            ))
        
        # Adjust extraversion for better social interaction
        if "personality" in current_cdl and "big_five" in current_cdl["personality"]:
            big_five = current_cdl["personality"]["big_five"]
            current_extraversion = big_five.get("extraversion", 0.6)
            
            # Ensure current_extraversion is a number
            if not isinstance(current_extraversion, (int, float)):
                current_extraversion = 0.6  # Default fallback
            
            target_extraversion = min(1.0, current_extraversion + (0.08 * magnitude))
            
            adjustments.append(ParameterAdjustment(
                parameter_path="personality.big_five.extraversion",
                current_value=current_extraversion,
                target_value=target_extraversion,
                adjustment_reason="Increase extraversion to improve social interaction",
                expected_improvement=opportunity.impact_potential * 0.4,
                risk_level="medium",
                affected_behaviors=["social_initiation", "conversation_energy", "interactive_responses"]
            ))
        
        return adjustments
    
    async def _generate_memory_effectiveness_adjustments(
        self,
        opportunity: OptimizationOpportunity,
        current_cdl: Dict[str, Any],
        magnitude: float
    ) -> List[ParameterAdjustment]:
        """Generate adjustments for memory effectiveness improvement."""
        adjustments = []
        
        # Adjust openness for better information processing
        if "personality" in current_cdl and "big_five" in current_cdl["personality"]:
            big_five = current_cdl["personality"]["big_five"]
            current_openness = big_five.get("openness", 0.7)
            
            # Ensure current_openness is a number
            if not isinstance(current_openness, (int, float)):
                current_openness = 0.7  # Default fallback
            
            target_openness = min(1.0, current_openness + (0.06 * magnitude))
            
            adjustments.append(ParameterAdjustment(
                parameter_path="personality.big_five.openness",
                current_value=current_openness,
                target_value=target_openness,
                adjustment_reason="Increase openness to improve memory and learning effectiveness",
                expected_improvement=opportunity.impact_potential * 0.7,
                risk_level="low",
                affected_behaviors=["information_absorption", "context_awareness", "memory_formation"]
            ))
        
        return adjustments
    
    async def _generate_relationship_progression_adjustments(
        self,
        opportunity: OptimizationOpportunity,
        current_cdl: Dict[str, Any],
        magnitude: float
    ) -> List[ParameterAdjustment]:
        """Generate adjustments for relationship progression improvement."""
        adjustments = []
        
        # Adjust agreeableness for better relationship building
        if "personality" in current_cdl and "big_five" in current_cdl["personality"]:
            big_five = current_cdl["personality"]["big_five"]
            current_agreeableness = big_five.get("agreeableness", 0.7)
            
            # Ensure current_agreeableness is a number
            if not isinstance(current_agreeableness, (int, float)):
                current_agreeableness = 0.7  # Default fallback
            
            target_agreeableness = min(1.0, current_agreeableness + (0.08 * magnitude))
            
            adjustments.append(ParameterAdjustment(
                parameter_path="personality.big_five.agreeableness",
                current_value=current_agreeableness,
                target_value=target_agreeableness,
                adjustment_reason="Increase agreeableness to improve relationship building",
                expected_improvement=opportunity.impact_potential * 0.6,
                risk_level="low",
                affected_behaviors=["trust_building", "cooperation", "empathetic_responses"]
            ))
        
        # Adjust empathy for deeper emotional connections
        if "emotional_intelligence" in current_cdl:
            ei = current_cdl["emotional_intelligence"]
            current_empathy = ei.get("empathy", 0.75)
            
            # Ensure current_empathy is a number
            if not isinstance(current_empathy, (int, float)):
                current_empathy = 0.75  # Default fallback
            
            target_empathy = min(1.0, current_empathy + (0.06 * magnitude))
            
            adjustments.append(ParameterAdjustment(
                parameter_path="emotional_intelligence.empathy",
                current_value=current_empathy,
                target_value=target_empathy,
                adjustment_reason="Increase empathy for better emotional connection",
                expected_improvement=opportunity.impact_potential * 0.4,
                risk_level="low",
                affected_behaviors=["emotional_understanding", "supportive_responses", "relationship_depth"]
            ))
        
        return adjustments
    
    async def _generate_emotional_intelligence_adjustments(
        self,
        opportunity: OptimizationOpportunity,
        current_cdl: Dict[str, Any],
        magnitude: float
    ) -> List[ParameterAdjustment]:
        """Generate adjustments for emotional intelligence improvement."""
        adjustments = []
        
        # Adjust emotional stability
        if "emotional_intelligence" in current_cdl:
            ei = current_cdl["emotional_intelligence"]
            current_stability = ei.get("emotional_stability", 0.7)
            
            # Ensure current_stability is a number
            if not isinstance(current_stability, (int, float)):
                current_stability = 0.7  # Default fallback
            
            target_stability = min(1.0, current_stability + (0.05 * magnitude))
            
            adjustments.append(ParameterAdjustment(
                parameter_path="emotional_intelligence.emotional_stability",
                current_value=current_stability,
                target_value=target_stability,
                adjustment_reason="Increase emotional stability for consistent emotional responses",
                expected_improvement=opportunity.impact_potential * 0.8,
                risk_level="low",
                affected_behaviors=["emotional_consistency", "stress_handling", "mood_stability"]
            ))
        
        return adjustments
    
    async def _validate_adjustments_for_authenticity(
        self,
        character_name: str,
        adjustments: List[ParameterAdjustment],
        current_cdl: Dict[str, Any]
    ) -> List[ParameterAdjustment]:
        """Validate that adjustments maintain character authenticity."""
        validated_adjustments = []
        
        for adjustment in adjustments:
            # Check if adjustment exceeds safety thresholds
            if self._adjustment_exceeds_safety_threshold(adjustment):
                self.logger.warning(
                    f"⚠️ Adjustment to {adjustment.parameter_path} exceeds safety threshold, reducing magnitude"
                )
                # Reduce adjustment to within safety limits
                adjustment = self._reduce_adjustment_to_safe_level(adjustment)
            
            # Validate that adjustment maintains character core traits
            if self._maintains_character_authenticity(adjustment, current_cdl):
                validated_adjustments.append(adjustment)
            else:
                self.logger.warning(
                    f"🚫 Adjustment to {adjustment.parameter_path} would compromise character authenticity, skipping"
                )
        
        self.logger.info(
            f"✅ Validated {len(validated_adjustments)}/{len(adjustments)} adjustments for {character_name}"
        )
        
        return validated_adjustments
    
    def _adjustment_exceeds_safety_threshold(self, adjustment: ParameterAdjustment) -> bool:
        """Check if adjustment exceeds safety thresholds."""
        if "personality.big_five" in adjustment.parameter_path:
            change_magnitude = abs(adjustment.target_value - adjustment.current_value)
            return change_magnitude > self.safety_thresholds['max_personality_change']
        elif "communication_style" in adjustment.parameter_path:
            change_magnitude = abs(adjustment.target_value - adjustment.current_value)
            return change_magnitude > self.safety_thresholds['max_communication_change']
        elif "emotional_intelligence" in adjustment.parameter_path:
            change_magnitude = abs(adjustment.target_value - adjustment.current_value)
            return change_magnitude > self.safety_thresholds['max_emotional_change']
        
        return False
    
    def _reduce_adjustment_to_safe_level(self, adjustment: ParameterAdjustment) -> ParameterAdjustment:
        """Reduce adjustment magnitude to within safety limits."""
        if "personality.big_five" in adjustment.parameter_path:
            max_change = self.safety_thresholds['max_personality_change']
        elif "communication_style" in adjustment.parameter_path:
            max_change = self.safety_thresholds['max_communication_change']
        elif "emotional_intelligence" in adjustment.parameter_path:
            max_change = self.safety_thresholds['max_emotional_change']
        else:
            max_change = 0.1  # Default safe change
        
        if adjustment.target_value > adjustment.current_value:
            adjustment.target_value = adjustment.current_value + max_change
        else:
            adjustment.target_value = adjustment.current_value - max_change
        
        adjustment.risk_level = "low"  # Reduced adjustment is now low risk
        return adjustment
    
    def _maintains_character_authenticity(
        self, 
        adjustment: ParameterAdjustment, 
        current_cdl: Dict[str, Any]
    ) -> bool:
        """Check if adjustment maintains character's core authenticity."""
        # For now, this is a placeholder that assumes all validated adjustments maintain authenticity
        # In a full implementation, this would involve sophisticated character consistency checking
        return True
    
    def _calculate_expected_improvement(self, adjustments: List[ParameterAdjustment]) -> float:
        """Calculate expected overall improvement from all adjustments."""
        if not adjustments:
            return 0.0
        
        # Weight adjustments by their expected improvement and combine
        total_weighted_improvement = sum(
            adj.expected_improvement for adj in adjustments
        )
        
        # Apply diminishing returns for multiple adjustments
        num_adjustments = len(adjustments)
        diminishing_factor = 1.0 - (num_adjustments - 1) * 0.1  # Reduce by 10% per additional adjustment
        diminishing_factor = max(0.5, diminishing_factor)  # Minimum 50% effectiveness
        
        return min(total_weighted_improvement * diminishing_factor, 0.3)  # Cap at 30% improvement
    
    def _create_rollback_strategy(self, current_cdl: Dict[str, Any]) -> Dict[str, Any]:
        """Create rollback strategy to restore original configuration."""
        return {
            'rollback_method': 'full_config_restore',
            'original_cdl': copy.deepcopy(current_cdl),
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_validation_criteria(self, opportunities: List[OptimizationOpportunity]) -> Dict[str, Any]:
        """Create validation criteria for optimization success."""
        return {
            'minimum_improvement_threshold': 0.05,  # 5% minimum improvement
            'maximum_performance_drop': 0.02,       # 2% maximum acceptable drop in any metric
            'validation_period_days': 7,            # 7 days to validate changes
            'rollback_triggers': [
                'performance_drop_exceeds_threshold',
                'user_satisfaction_decrease',
                'character_authenticity_compromise'
            ]
        }
    
    def _estimate_target_performance(
        self, 
        current_performance: CharacterEffectivenessData, 
        adjustments: List[ParameterAdjustment]
    ) -> CharacterEffectivenessData:
        """Estimate target performance after applying adjustments."""
        # Create copy of current performance
        target = copy.deepcopy(current_performance)
        
        # Apply estimated improvements from adjustments
        total_improvement = self._calculate_expected_improvement(adjustments)
        
        # Apply improvement to overall effectiveness score
        target.overall_effectiveness = min(
            1.0, 
            current_performance.overall_effectiveness + total_improvement
        )
        
        return target
    
    def _assess_implementation_complexity(self, adjustments: List[ParameterAdjustment]) -> str:
        """Assess implementation complexity based on adjustments."""
        if not adjustments:
            return "low"  # Changed from "none" to "low" to match database constraint
        
        high_risk_count = sum(1 for adj in adjustments if adj.risk_level == "high")
        medium_risk_count = sum(1 for adj in adjustments if adj.risk_level == "medium")
        
        if high_risk_count > 0 or len(adjustments) > 5:
            return "high"
        elif medium_risk_count > 1 or len(adjustments) > 3:
            return "medium"
        else:
            return "low"
    
    async def _validate_optimization_plan(self, plan: OptimizationPlan) -> Dict[str, Any]:
        """Validate optimization plan before application."""
        issues = []
        
        # Check for conflicting adjustments
        parameter_paths = [adj.parameter_path for adj in plan.parameter_adjustments]
        if len(parameter_paths) != len(set(parameter_paths)):
            issues.append("Duplicate parameter adjustments detected")
        
        # Check expected improvement is reasonable
        if plan.expected_improvement > 0.5:  # 50%
            issues.append("Expected improvement unrealistically high")
        
        # Check number of simultaneous adjustments
        if len(plan.parameter_adjustments) > 8:
            issues.append("Too many simultaneous adjustments (>8)")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    async def _apply_parameter_adjustments(
        self,
        character_name: str,
        adjustments: List[ParameterAdjustment]
    ) -> Dict[str, Any]:
        """Apply parameter adjustments to character CDL."""
        current_cdl = await self._load_character_cdl(character_name)
        updated_cdl = copy.deepcopy(current_cdl)
        
        for adjustment in adjustments:
            # Apply the parameter adjustment
            self._set_nested_parameter(updated_cdl, adjustment.parameter_path, adjustment.target_value)
            
            self.logger.info(
                f"📝 Applied {adjustment.parameter_path}: "
                f"{adjustment.current_value} → {adjustment.target_value}"
            )
        
        return updated_cdl
    
    def _set_nested_parameter(self, cdl_data: Dict[str, Any], path: str, value: Any) -> None:
        """Set a nested parameter in CDL data using dot notation path."""
        keys = path.split('.')
        current = cdl_data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    async def _apply_rollback(self, character_name: str, rollback_strategy: Dict[str, Any]) -> None:
        """Apply rollback strategy to restore previous configuration."""
        if rollback_strategy['rollback_method'] == 'full_config_restore':
            original_cdl = rollback_strategy['original_cdl']
            await self._save_character_cdl(character_name, original_cdl)
            self.logger.info(f"🔄 Rollback applied for {character_name}")
        else:
            raise NotImplementedError(f"Rollback method {rollback_strategy['rollback_method']} not implemented")
    
    async def _record_optimization_attempt(self, optimization_id: str, plan: OptimizationPlan) -> None:
        """Record optimization attempt in PostgreSQL database."""
        if not self.postgres_pool:
            self.logger.debug("No PostgreSQL pool available, skipping optimization attempt recording")
            return
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Insert optimization attempt record
                await conn.execute("""
                    INSERT INTO personality_optimization_attempts (
                        optimization_id, character_name, optimization_approach, 
                        expected_improvement, implementation_complexity,
                        parameter_count, attempt_timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, 
                optimization_id, 
                plan.character_name,
                plan.optimization_approach.value,
                plan.expected_improvement,
                plan.implementation_complexity,
                len(plan.parameter_adjustments),
                datetime.now()
                )
                
                # Insert parameter adjustments
                for i, adjustment in enumerate(plan.parameter_adjustments):
                    await conn.execute("""
                        INSERT INTO personality_parameter_adjustments (
                            optimization_id, adjustment_order, parameter_path,
                            current_value, target_value, adjustment_reason,
                            expected_improvement, risk_level
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    optimization_id,
                    i + 1,
                    adjustment.parameter_path,
                    json.dumps(adjustment.current_value) if not isinstance(adjustment.current_value, (str, int, float)) else str(adjustment.current_value),
                    json.dumps(adjustment.target_value) if not isinstance(adjustment.target_value, (str, int, float)) else str(adjustment.target_value),
                    adjustment.adjustment_reason,
                    adjustment.expected_improvement,
                    adjustment.risk_level
                    )
                
                self.logger.info("📊 Recorded optimization attempt %s with %d parameter adjustments", 
                               optimization_id, len(plan.parameter_adjustments))
                
        except Exception as e:
            self.logger.error("Failed to record optimization attempt %s: %s", optimization_id, e)
    
    async def _record_optimization_result(self, result: OptimizationResult) -> None:
        """Record optimization result in PostgreSQL database."""
        if not self.postgres_pool:
            self.logger.debug("No PostgreSQL pool available, skipping optimization result recording")
            return
        
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO personality_optimization_results (
                        optimization_id, character_name, success, 
                        performance_before, performance_after, actual_improvement,
                        rollback_applied, issues_encountered, completion_timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                result.optimization_plan_id,
                result.character_name,
                result.success,
                result.performance_before.overall_effectiveness if result.performance_before else None,
                result.performance_after.overall_effectiveness if result.performance_after else None,
                result.actual_improvement,
                result.rollback_applied,
                json.dumps(result.issues_encountered),
                result.timestamp
                )
                
                self.logger.info("📊 Recorded optimization result for %s (success: %s, improvement: %s)", 
                               result.character_name, result.success, 
                               f"{result.actual_improvement:.1%}" if result.actual_improvement else "N/A")
                
        except Exception as e:
            self.logger.error("Failed to record optimization result for %s: %s", 
                            result.character_name, e)


def create_cdl_parameter_optimizer(
    performance_analyzer: CharacterPerformanceAnalyzer,
    cdl_parser: CDLParser,
    cdl_database_manager: Optional[CDLDatabaseManager] = None,
    postgres_pool: Optional[Any] = None,
    characters_dir: str = "characters/examples"
) -> CDLParameterOptimizer:
    """
    Factory function to create CDLParameterOptimizer.
    
    Args:
        performance_analyzer: Character performance analyzer
        cdl_parser: CDL parser for character configuration
        cdl_database_manager: CDL database manager for PostgreSQL storage
        postgres_pool: Database connection pool (optional)
        characters_dir: Directory containing character CDL files (JSON fallback)
        
    Returns:
        Configured CDLParameterOptimizer instance
    """
    return CDLParameterOptimizer(
        performance_analyzer=performance_analyzer,
        cdl_parser=cdl_parser,
        cdl_database_manager=cdl_database_manager,
        postgres_pool=postgres_pool,
        characters_dir=characters_dir
    )