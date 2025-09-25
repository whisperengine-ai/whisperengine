"""
Character Evolution Tool Manager for LLM Tool Calling

CONSOLIDATION UPDATE: All character evolution tools removed due to HIGH priority 
conflicts with CDL (Character Definition Language) system.

Character evolution tools fundamentally conflict with CDL's static character definitions
and would cause personality inconsistencies. The CDL system provides stable, 
well-defined character personalities that should not be dynamically modified.

Removed tools (conflicted with CDL system):
- adapt_personality_trait
- update_character_backstory  
- modify_communication_style
- calibrate_emotional_expression
- create_character_relationship
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CharacterEvolutionAction:
    """Represents a character evolution action taken by the LLM"""
    action_type: str
    character_id: str
    trait_modified: str
    old_value: Any
    new_value: Any
    reason: str
    confidence: float
    timestamp: datetime
    success: bool
    result: Optional[Dict[str, Any]] = None


class CharacterEvolutionToolManager:
    """
    Character Evolution Tool Manager - DISABLED
    
    CONSOLIDATION UPDATE: All character evolution tools removed due to HIGH priority 
    conflicts with CDL (Character Definition Language) system.
    
    Character evolution tools fundamentally conflict with CDL's static character definitions
    and would cause personality inconsistencies. The CDL system provides stable, 
    well-defined character personalities that should not be dynamically modified.
    
    Removed tools (conflicted with CDL system):
    - adapt_personality_trait -> Use CDL character definitions as authoritative source
    - update_character_backstory -> Use CDL backstory as canonical character history
    - modify_communication_style -> Use CDL voice/communication style definitions
    - calibrate_emotional_expression -> Use CDL personality/emotion definitions
    - create_character_relationship -> Use CDL relationship definitions
    """
    
    def __init__(self, character_manager, memory_manager, llm_client):
        self.character_manager = character_manager
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.tools = self._initialize_character_tools()
        self.evolution_history: List[CharacterEvolutionAction] = []
        
        logger.warning("CharacterEvolutionToolManager initialized with no tools - "
                      "character evolution disabled to prevent CDL conflicts")
    
    def _initialize_character_tools(self) -> List[Dict[str, Any]]:
        """Initialize character evolution tools for LLM (DISABLED - all tools removed)"""
        # ALL CHARACTER EVOLUTION TOOLS REMOVED TO PREVENT CDL CONFLICTS
        # The CDL system is the authoritative source for character definitions
        return []
        """Initialize character evolution tools for LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "adapt_personality_trait",
                    "description": "Dynamically adjust character personality traits based on conversation patterns and user feedback",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trait_name": {
                                "type": "string",
                                "description": "The personality trait to adjust (e.g., 'extraversion', 'empathy', 'humor_style')",
                                "enum": ["extraversion", "agreeableness", "conscientiousness", "neuroticism", "openness", 
                                        "empathy", "humor_style", "formality", "enthusiasm", "patience"]
                            },
                            "adjustment_direction": {
                                "type": "string",
                                "description": "Direction of trait adjustment",
                                "enum": ["increase", "decrease", "fine_tune"]
                            },
                            "adjustment_strength": {
                                "type": "number",
                                "description": "Strength of adjustment (0.1 = subtle, 1.0 = significant)",
                                "minimum": 0.1,
                                "maximum": 1.0
                            },
                            "evidence_analysis": {
                                "type": "string",
                                "description": "Analysis of conversation evidence supporting this adjustment"
                            },
                            "confidence_score": {
                                "type": "number",
                                "description": "Confidence in this adjustment (0.0-1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["trait_name", "adjustment_direction", "adjustment_strength", "evidence_analysis", "confidence_score"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_character_backstory",
                    "description": "Evolve character history through meaningful interactions and shared experiences",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "backstory_element": {
                                "type": "string",
                                "description": "Type of backstory element to update",
                                "enum": ["life_phase", "relationship", "experience", "skill", "memory", "goal"]
                            },
                            "new_experience": {
                                "type": "string",
                                "description": "Description of the new experience or information to integrate"
                            },
                            "integration_method": {
                                "type": "string",
                                "description": "How to integrate this into existing backstory",
                                "enum": ["add_new", "modify_existing", "create_connection", "resolve_conflict"]
                            },
                            "emotional_impact": {
                                "type": "string",
                                "description": "Emotional significance of this backstory update",
                                "enum": ["low", "medium", "high", "transformative"]
                            },
                            "memory_triggers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keywords or phrases that should trigger this backstory element in future conversations"
                            }
                        },
                        "required": ["backstory_element", "new_experience", "integration_method", "emotional_impact"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "modify_communication_style",
                    "description": "Adapt speaking patterns and communication style to user preferences and relationship development",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "style_aspect": {
                                "type": "string",
                                "description": "Aspect of communication style to modify",
                                "enum": ["formality_level", "response_length", "humor_frequency", "emotional_expressiveness", 
                                        "technical_complexity", "conversation_flow", "topic_switching"]
                            },
                            "user_feedback": {
                                "type": "string",
                                "description": "Evidence from user behavior or explicit feedback"
                            },
                            "adaptation_strength": {
                                "type": "number",
                                "description": "How strongly to adapt (0.1 = subtle, 1.0 = dramatic)",
                                "minimum": 0.1,
                                "maximum": 1.0
                            },
                            "relationship_stage": {
                                "type": "string",
                                "description": "Current relationship stage with user",
                                "enum": ["initial", "acquaintance", "friend", "close_friend", "trusted_confidant"]
                            },
                            "effectiveness_prediction": {
                                "type": "number",
                                "description": "Predicted effectiveness of this adaptation (0.0-1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["style_aspect", "user_feedback", "adaptation_strength", "relationship_stage", "effectiveness_prediction"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calibrate_emotional_expression",
                    "description": "Fine-tune how characters express emotions based on user's emotional needs and preferences",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "emotion_type": {
                                "type": "string",
                                "description": "Type of emotion to calibrate expression for",
                                "enum": ["empathy", "excitement", "concern", "joy", "sadness", "frustration", "curiosity", "pride"]
                            },
                            "expression_intensity": {
                                "type": "number",
                                "description": "Intensity level for emotional expression (0.1 = subtle, 1.0 = intense)",
                                "minimum": 0.1,
                                "maximum": 1.0
                            },
                            "context_awareness": {
                                "type": "object",
                                "properties": {
                                    "user_emotional_state": {"type": "string"},
                                    "conversation_topic": {"type": "string"},
                                    "relationship_intimacy": {"type": "string"},
                                    "cultural_considerations": {"type": "string"}
                                }
                            },
                            "calibration_reason": {
                                "type": "string",
                                "description": "Explanation for why this calibration is needed"
                            },
                            "expected_user_response": {
                                "type": "string",
                                "description": "Expected positive impact on user experience"
                            }
                        },
                        "required": ["emotion_type", "expression_intensity", "calibration_reason", "expected_user_response"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_character_relationship",
                    "description": "Build and evolve connections between characters and users through shared experiences",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relationship_type": {
                                "type": "string",
                                "description": "Type of relationship being developed",
                                "enum": ["friendship", "mentorship", "professional", "casual", "intimate", "familial"]
                            },
                            "development_stage": {
                                "type": "string",
                                "description": "Current stage of relationship development",
                                "enum": ["initial_contact", "building_rapport", "establishing_trust", "deepening_bond", "mature_relationship"]
                            },
                            "shared_experiences": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Significant shared experiences that define this relationship"
                            },
                            "relationship_milestones": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "milestone": {"type": "string"},
                                        "timestamp": {"type": "string"},
                                        "emotional_significance": {"type": "string"}
                                    }
                                },
                                "description": "Key milestones in relationship development"
                            },
                            "communication_preferences": {
                                "type": "object",
                                "description": "User's preferred communication style within this relationship"
                            }
                        },
                        "required": ["relationship_type", "development_stage", "shared_experiences"],
                        "additionalProperties": False
                    }
                }
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available character evolution tools (DISABLED)"""
        return self.tools
    
    async def handle_tool_call(self, function_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Handle LLM tool calls for character evolution (ALL DISABLED)
        
        CONSOLIDATION NOTE: All character evolution tools disabled due to CDL conflicts
        """
        logger.warning("Character evolution tool %s called but DISABLED - conflicts with CDL system", function_name)
        
        # All character evolution tools are disabled to prevent CDL conflicts
        disabled_tools = [
            "adapt_personality_trait",
            "update_character_backstory", 
            "modify_communication_style",
            "calibrate_emotional_expression",
            "create_character_relationship"
        ]
        
        if function_name in disabled_tools:
            return {
                "success": False,
                "error": f"Tool {function_name} disabled to prevent CDL character conflicts",
                "message": "Character evolution tools conflict with CDL system's static character definitions",
                "recommendation": "Use CDL character files as authoritative source for character traits"
            }
        else:
            return {"success": False, "error": f"Unknown character evolution tool: {function_name}"}
    
    # Legacy method aliases for backward compatibility
    async def execute_tool(self, function_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Legacy method - redirects to handle_tool_call"""
        return await self.handle_tool_call(function_name, parameters, user_id)
    
    async def _adapt_personality_trait(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Adapt a character personality trait based on conversation patterns"""
        trait_name = params["trait_name"]
        adjustment_direction = params["adjustment_direction"]
        adjustment_strength = params["adjustment_strength"]
        evidence = params["evidence_analysis"]
        confidence = params["confidence_score"]
        
        logger.info(f"Adapting personality trait '{trait_name}' ({adjustment_direction}) "
                   f"for user {user_id} with confidence {confidence}")
        
        try:
            # Store the personality adaptation in memory
            adaptation_record = {
                "trait_name": trait_name,
                "adjustment": f"{adjustment_direction} by {adjustment_strength}",
                "evidence": evidence,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Character personality trait '{trait_name}' adapted: {adjustment_direction} by {adjustment_strength}. Evidence: {evidence}",
                memory_type="character_evolution",
                metadata={
                    "evolution_type": "personality_trait",
                    "trait_name": trait_name,
                    "adaptation_record": adaptation_record,
                    "confidence": confidence,
                    "tags": ["character_evolution", "personality", trait_name]
                }
            )
            
            # Record evolution action
            action = CharacterEvolutionAction(
                action_type="personality_adaptation",
                character_id="current_character",  # TODO: Get actual character ID
                trait_modified=trait_name,
                old_value="baseline",  # TODO: Get actual current value
                new_value=f"{adjustment_direction}_{adjustment_strength}",
                reason=evidence,
                confidence=confidence,
                timestamp=datetime.now(),
                success=True
            )
            self.evolution_history.append(action)
            
            return {
                "success": True,
                "message": f"Successfully adapted '{trait_name}' trait",
                "trait_name": trait_name,
                "adjustment": f"{adjustment_direction} by {adjustment_strength}",
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Failed to adapt personality trait: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_character_backstory(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update character backstory with new experiences"""
        backstory_element = params["backstory_element"]
        new_experience = params["new_experience"]
        integration_method = params["integration_method"]
        emotional_impact = params["emotional_impact"]
        memory_triggers = params.get("memory_triggers", [])
        
        logger.info(f"Updating character backstory ({backstory_element}) for user {user_id}")
        
        try:
            # Store backstory evolution in memory
            backstory_record = {
                "element_type": backstory_element,
                "experience": new_experience,
                "integration": integration_method,
                "emotional_impact": emotional_impact,
                "triggers": memory_triggers,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Character backstory updated: {backstory_element} - {new_experience}",
                memory_type="character_evolution",
                metadata={
                    "evolution_type": "backstory_update",
                    "backstory_record": backstory_record,
                    "emotional_impact": emotional_impact,
                    "memory_triggers": memory_triggers,
                    "tags": ["character_evolution", "backstory", backstory_element]
                }
            )
            
            return {
                "success": True,
                "message": f"Successfully updated character backstory: {backstory_element}",
                "backstory_element": backstory_element,
                "emotional_impact": emotional_impact
            }
            
        except Exception as e:
            logger.error(f"Failed to update character backstory: {e}")
            return {"success": False, "error": str(e)}
    
    async def _modify_communication_style(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Modify character communication style based on user feedback"""
        style_aspect = params["style_aspect"]
        user_feedback = params["user_feedback"]
        adaptation_strength = params["adaptation_strength"]
        relationship_stage = params["relationship_stage"]
        effectiveness_prediction = params["effectiveness_prediction"]
        
        logger.info(f"Modifying communication style ({style_aspect}) for user {user_id}")
        
        try:
            # Store communication style adaptation
            style_record = {
                "aspect": style_aspect,
                "feedback": user_feedback,
                "adaptation_strength": adaptation_strength,
                "relationship_stage": relationship_stage,
                "effectiveness_prediction": effectiveness_prediction,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Communication style adapted: {style_aspect} based on feedback: {user_feedback}",
                memory_type="character_evolution", 
                metadata={
                    "evolution_type": "communication_style",
                    "style_record": style_record,
                    "relationship_stage": relationship_stage,
                    "tags": ["character_evolution", "communication", style_aspect]
                }
            )
            
            return {
                "success": True,
                "message": f"Successfully adapted communication style: {style_aspect}",
                "style_aspect": style_aspect,
                "adaptation_strength": adaptation_strength,
                "effectiveness_prediction": effectiveness_prediction
            }
            
        except Exception as e:
            logger.error(f"Failed to modify communication style: {e}")
            return {"success": False, "error": str(e)}
    
    async def _calibrate_emotional_expression(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Calibrate emotional expression based on user needs"""
        emotion_type = params["emotion_type"]
        expression_intensity = params["expression_intensity"]
        context_awareness = params.get("context_awareness", {})
        calibration_reason = params["calibration_reason"]
        expected_response = params["expected_user_response"]
        
        logger.info(f"Calibrating emotional expression ({emotion_type}) for user {user_id}")
        
        try:
            # Store emotional calibration
            calibration_record = {
                "emotion_type": emotion_type,
                "intensity": expression_intensity,
                "context": context_awareness,
                "reason": calibration_reason,
                "expected_response": expected_response,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Emotional expression calibrated: {emotion_type} at intensity {expression_intensity}",
                memory_type="character_evolution",
                metadata={
                    "evolution_type": "emotional_calibration",
                    "calibration_record": calibration_record,
                    "emotion_type": emotion_type,
                    "tags": ["character_evolution", "emotional_expression", emotion_type]
                }
            )
            
            return {
                "success": True,
                "message": f"Successfully calibrated emotional expression: {emotion_type}",
                "emotion_type": emotion_type,
                "intensity": expression_intensity,
                "expected_response": expected_response
            }
            
        except Exception as e:
            logger.error(f"Failed to calibrate emotional expression: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_character_relationship(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create or evolve character relationship with user"""
        relationship_type = params["relationship_type"]
        development_stage = params["development_stage"]
        shared_experiences = params["shared_experiences"]
        milestones = params.get("relationship_milestones", [])
        communication_prefs = params.get("communication_preferences", {})
        
        logger.info(f"Creating/evolving character relationship ({relationship_type}) for user {user_id}")
        
        try:
            # Store relationship development
            relationship_record = {
                "type": relationship_type,
                "stage": development_stage,
                "shared_experiences": shared_experiences,
                "milestones": milestones,
                "communication_preferences": communication_prefs,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Character relationship developed: {relationship_type} at {development_stage} stage",
                memory_type="character_evolution",
                metadata={
                    "evolution_type": "relationship_development",
                    "relationship_record": relationship_record,
                    "relationship_type": relationship_type,
                    "development_stage": development_stage,
                    "tags": ["character_evolution", "relationship", relationship_type]
                }
            )
            
            return {
                "success": True,
                "message": f"Successfully developed character relationship: {relationship_type}",
                "relationship_type": relationship_type,
                "development_stage": development_stage,
                "shared_experiences_count": len(shared_experiences)
            }
            
        except Exception as e:
            logger.error(f"Failed to create character relationship: {e}")
            return {"success": False, "error": str(e)}
    
    def get_evolution_history(self, user_id: str = None) -> List[CharacterEvolutionAction]:
        """Get character evolution history, optionally filtered by user"""
        if user_id is None:
            return self.evolution_history
        # TODO: Filter by user_id when we track that in actions
        return self.evolution_history