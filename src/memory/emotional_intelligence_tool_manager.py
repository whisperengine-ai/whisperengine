"""
Emotional Intelligence Tool Manager for LLM Tool Calling

Provides sophisticated emotional awareness tools that enable LLMs to 
detect emotional crises, calibrate empathy, and provide proactive support.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionalCrisisLevel(Enum):
    """Emotional crisis severity levels"""
    NORMAL = "normal"
    MILD_CONCERN = "mild_concern"
    MODERATE_CONCERN = "moderate_concern"
    HIGH_CONCERN = "high_concern"
    CRISIS = "crisis"


class EmpathyCalibrationLevel(Enum):
    """Empathy expression calibration levels"""
    MINIMAL = "minimal"
    SUBTLE = "subtle"
    MODERATE = "moderate"
    HIGH = "high"
    INTENSE = "intense"


@dataclass
class EmotionalIntelligenceAction:
    """Represents an emotional intelligence action taken by the LLM"""
    action_type: str
    user_id: str
    emotion_detected: str
    confidence: float
    intervention_type: str
    crisis_level: EmotionalCrisisLevel
    empathy_calibration: EmpathyCalibrationLevel
    response_strategy: str
    timestamp: datetime
    success: bool
    result: Optional[Dict[str, Any]] = None


class EmotionalIntelligenceToolManager:
    """Manages emotional intelligence tools for LLM tool calling"""
    
    def __init__(self, memory_manager, llm_client, emotion_analyzer=None):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.emotion_analyzer = emotion_analyzer
        self.tools = self._initialize_emotional_tools()
        self.emotional_history: List[EmotionalIntelligenceAction] = []
        self.crisis_patterns = self._load_crisis_patterns()
    
    def _initialize_emotional_tools(self) -> List[Dict[str, Any]]:
        """Initialize emotional intelligence tools for LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "detect_emotional_crisis",
                    "description": "Detect potential emotional crisis situations requiring immediate attention and support",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "crisis_indicators": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Observable indicators suggesting emotional distress or crisis"
                            },
                            "crisis_severity": {
                                "type": "string",
                                "description": "Assessed severity level of the potential crisis",
                                "enum": ["normal", "mild_concern", "moderate_concern", "high_concern", "crisis"]
                            },
                            "emotional_pattern_analysis": {
                                "type": "string",
                                "description": "Analysis of emotional patterns leading to this assessment"
                            },
                            "immediate_needs": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Immediate emotional or support needs identified"
                            },
                            "intervention_urgency": {
                                "type": "string",
                                "description": "How urgently intervention is needed",
                                "enum": ["none", "low", "medium", "high", "immediate"]
                            },
                            "confidence_score": {
                                "type": "number",
                                "description": "Confidence in crisis assessment (0.0-1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["crisis_indicators", "crisis_severity", "emotional_pattern_analysis", "immediate_needs", "intervention_urgency", "confidence_score"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calibrate_empathy_response",
                    "description": "Calibrate empathetic responses based on user's emotional state and needs",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "detected_emotions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Primary emotions detected in user's communication"
                            },
                            "empathy_level": {
                                "type": "string",
                                "description": "Appropriate level of empathetic response",
                                "enum": ["minimal", "subtle", "moderate", "high", "intense"]
                            },
                            "emotional_context": {
                                "type": "object",
                                "properties": {
                                    "current_situation": {"type": "string"},
                                    "user_personality": {"type": "string"},
                                    "relationship_stage": {"type": "string"},
                                    "cultural_factors": {"type": "string"}
                                },
                                "description": "Contextual factors influencing appropriate empathy calibration"
                            },
                            "response_strategy": {
                                "type": "string",
                                "description": "Recommended strategy for empathetic response",
                                "enum": ["active_listening", "emotional_validation", "gentle_support", "practical_help", "professional_referral"]
                            },
                            "avoid_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Communication patterns to avoid based on user's emotional state"
                            }
                        },
                        "required": ["detected_emotions", "empathy_level", "emotional_context", "response_strategy"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "provide_proactive_support",
                    "description": "Proactively offer emotional support based on detected patterns and user history",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "support_triggers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Patterns or events that triggered proactive support consideration"
                            },
                            "support_type": {
                                "type": "string",
                                "description": "Type of proactive support to offer",
                                "enum": ["emotional_check_in", "resource_sharing", "distraction_activity", "memory_recall", "future_planning", "celebration"]
                            },
                            "timing_strategy": {
                                "type": "string",
                                "description": "When and how to offer this support",
                                "enum": ["immediate", "next_interaction", "scheduled_followup", "conditional"]
                            },
                            "support_approach": {
                                "type": "string",
                                "description": "How to approach offering support",
                                "enum": ["direct_offer", "gentle_suggestion", "embedded_naturally", "user_initiated"]
                            },
                            "expected_impact": {
                                "type": "string",
                                "description": "Expected positive impact of this proactive support"
                            },
                            "fallback_options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Alternative support approaches if primary approach doesn't work"
                            }
                        },
                        "required": ["support_triggers", "support_type", "timing_strategy", "support_approach", "expected_impact"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_emotional_patterns",
                    "description": "Analyze long-term emotional patterns to improve understanding and support",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern_timeframe": {
                                "type": "string",
                                "description": "Timeframe for pattern analysis",
                                "enum": ["recent_session", "past_week", "past_month", "long_term"]
                            },
                            "pattern_focus": {
                                "type": "string",
                                "description": "Focus area for pattern analysis",
                                "enum": ["emotional_cycles", "trigger_events", "coping_strategies", "relationship_dynamics", "stress_patterns"]
                            },
                            "insights_discovered": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Key insights discovered through pattern analysis"
                            },
                            "predictive_indicators": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Patterns that might predict future emotional states"
                            },
                            "support_adaptations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Recommended adaptations to support strategy based on patterns"
                            },
                            "confidence_level": {
                                "type": "number",
                                "description": "Confidence in pattern analysis (0.0-1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["pattern_timeframe", "pattern_focus", "insights_discovered", "predictive_indicators", "support_adaptations", "confidence_level"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "emotional_crisis_intervention",
                    "description": "Implement immediate intervention strategies for emotional crisis situations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "crisis_assessment": {
                                "type": "object",
                                "properties": {
                                    "severity": {"type": "string"},
                                    "immediate_risk": {"type": "boolean"},
                                    "support_network_available": {"type": "boolean"},
                                    "professional_help_needed": {"type": "boolean"}
                                },
                                "description": "Comprehensive crisis situation assessment"
                            },
                            "intervention_strategy": {
                                "type": "string",
                                "description": "Primary intervention strategy to implement",
                                "enum": ["stabilization", "grounding_techniques", "resource_connection", "safety_planning", "professional_referral"]
                            },
                            "immediate_actions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Immediate actions to take for crisis intervention"
                            },
                            "safety_protocols": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Safety protocols to implement or recommend"
                            },
                            "followup_requirements": {
                                "type": "object",
                                "properties": {
                                    "timing": {"type": "string"},
                                    "method": {"type": "string"},
                                    "escalation_triggers": {"type": "array", "items": {"type": "string"}}
                                },
                                "description": "Required follow-up actions and monitoring"
                            }
                        },
                        "required": ["crisis_assessment", "intervention_strategy", "immediate_actions", "safety_protocols", "followup_requirements"],
                        "additionalProperties": False
                    }
                }
            }
        ]
    
    def _load_crisis_patterns(self) -> Dict[str, Any]:
        """Load crisis detection patterns and indicators"""
        return {
            "verbal_indicators": [
                "hopelessness", "overwhelming", "can't take it", "giving up",
                "nothing matters", "end it all", "too much", "worthless"
            ],
            "behavioral_patterns": [
                "sudden_withdrawal", "dramatic_mood_changes", "sleep_disruption",
                "appetite_changes", "isolation", "reckless_behavior"
            ],
            "crisis_escalation": {
                "mild": ["stress", "overwhelmed", "tired", "frustrated"],
                "moderate": ["hopeless", "desperate", "trapped", "burden"],
                "severe": ["worthless", "ending", "giving up", "no point"]
            }
        }
    
    async def execute_tool(self, function_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute an emotional intelligence tool with the given parameters"""
        try:
            if function_name == "detect_emotional_crisis":
                return await self._detect_emotional_crisis(parameters, user_id)
            elif function_name == "calibrate_empathy_response":
                return await self._calibrate_empathy_response(parameters, user_id)
            elif function_name == "provide_proactive_support":
                return await self._provide_proactive_support(parameters, user_id)
            elif function_name == "analyze_emotional_patterns":
                return await self._analyze_emotional_patterns(parameters, user_id)
            elif function_name == "emotional_crisis_intervention":
                return await self._emotional_crisis_intervention(parameters, user_id)
            else:
                return {"success": False, "error": f"Unknown tool: {function_name}"}
                
        except Exception as e:
            logger.error("Error executing emotional intelligence tool %s: %s", function_name, e)
            return {"success": False, "error": str(e)}
    
    async def _detect_emotional_crisis(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Detect potential emotional crisis situations"""
        crisis_indicators = params["crisis_indicators"]
        crisis_severity = params["crisis_severity"]
        pattern_analysis = params["emotional_pattern_analysis"]
        immediate_needs = params["immediate_needs"]
        intervention_urgency = params["intervention_urgency"]
        confidence = params["confidence_score"]
        
        logger.warning("Emotional crisis detection triggered for user %s with severity: %s", 
                      user_id, crisis_severity)
        
        try:
            # Store crisis detection in memory with high priority
            crisis_record = {
                "indicators": crisis_indicators,
                "severity": crisis_severity,
                "pattern_analysis": pattern_analysis,
                "immediate_needs": immediate_needs,
                "intervention_urgency": intervention_urgency,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
                "followup_required": intervention_urgency in ["high", "immediate"]
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Emotional crisis detected: {crisis_severity} - Indicators: {', '.join(crisis_indicators)}",
                memory_type="emotional_intelligence",
                metadata={
                    "tool_type": "crisis_detection",
                    "crisis_record": crisis_record,
                    "severity": crisis_severity,
                    "confidence": confidence,
                    "urgent": intervention_urgency in ["high", "immediate"],
                    "tags": ["emotional_intelligence", "crisis_detection", crisis_severity]
                }
            )
            
            # Record emotional intelligence action
            action = EmotionalIntelligenceAction(
                action_type="crisis_detection",
                user_id=user_id,
                emotion_detected=crisis_severity,
                confidence=confidence,
                intervention_type=intervention_urgency,
                crisis_level=EmotionalCrisisLevel(crisis_severity),
                empathy_calibration=EmpathyCalibrationLevel.HIGH,  # Default for crisis
                response_strategy="crisis_support",
                timestamp=datetime.now(),
                success=True,
                result=crisis_record
            )
            self.emotional_history.append(action)
            
            return {
                "success": True,
                "crisis_detected": True,
                "severity": crisis_severity,
                "confidence": confidence,
                "intervention_urgency": intervention_urgency,
                "immediate_needs": immediate_needs,
                "followup_required": crisis_record["followup_required"]
            }
            
        except Exception as e:
            logger.error("Failed to detect emotional crisis: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _calibrate_empathy_response(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Calibrate empathetic responses based on emotional state"""
        detected_emotions = params["detected_emotions"]
        empathy_level = params["empathy_level"]
        emotional_context = params["emotional_context"]
        response_strategy = params["response_strategy"]
        avoid_patterns = params.get("avoid_patterns", [])
        
        logger.info("Calibrating empathy response (%s) for user %s", empathy_level, user_id)
        
        try:
            # Store empathy calibration
            empathy_record = {
                "detected_emotions": detected_emotions,
                "empathy_level": empathy_level,
                "context": emotional_context,
                "strategy": response_strategy,
                "avoid_patterns": avoid_patterns,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Empathy calibrated: {empathy_level} level for emotions: {', '.join(detected_emotions)}",
                memory_type="emotional_intelligence",
                metadata={
                    "tool_type": "empathy_calibration",
                    "empathy_record": empathy_record,
                    "empathy_level": empathy_level,
                    "strategy": response_strategy,
                    "tags": ["emotional_intelligence", "empathy_calibration", empathy_level]
                }
            )
            
            return {
                "success": True,
                "empathy_level": empathy_level,
                "response_strategy": response_strategy,
                "detected_emotions": detected_emotions,
                "avoid_patterns": avoid_patterns
            }
            
        except Exception as e:
            logger.error("Failed to calibrate empathy response: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _provide_proactive_support(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Provide proactive emotional support"""
        support_triggers = params["support_triggers"]
        support_type = params["support_type"]
        timing_strategy = params["timing_strategy"]
        support_approach = params["support_approach"]
        expected_impact = params["expected_impact"]
        fallback_options = params.get("fallback_options", [])
        
        logger.info("Providing proactive support (%s) for user %s", support_type, user_id)
        
        try:
            # Store proactive support action
            support_record = {
                "triggers": support_triggers,
                "type": support_type,
                "timing": timing_strategy,
                "approach": support_approach,
                "expected_impact": expected_impact,
                "fallback_options": fallback_options,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Proactive support provided: {support_type} via {support_approach}",
                memory_type="emotional_intelligence",
                metadata={
                    "tool_type": "proactive_support",
                    "support_record": support_record,
                    "support_type": support_type,
                    "timing": timing_strategy,
                    "tags": ["emotional_intelligence", "proactive_support", support_type]
                }
            )
            
            return {
                "success": True,
                "support_type": support_type,
                "timing_strategy": timing_strategy,
                "support_approach": support_approach,
                "expected_impact": expected_impact
            }
            
        except Exception as e:
            logger.error("Failed to provide proactive support: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _analyze_emotional_patterns(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Analyze emotional patterns for insights"""
        timeframe = params["pattern_timeframe"]
        focus = params["pattern_focus"]
        insights = params["insights_discovered"]
        predictive_indicators = params["predictive_indicators"]
        adaptations = params["support_adaptations"]
        confidence = params["confidence_level"]
        
        logger.info("Analyzing emotional patterns (%s) for user %s", focus, user_id)
        
        try:
            # Store pattern analysis
            pattern_record = {
                "timeframe": timeframe,
                "focus": focus,
                "insights": insights,
                "predictive_indicators": predictive_indicators,
                "adaptations": adaptations,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Emotional pattern analysis: {focus} over {timeframe} - {len(insights)} insights discovered",
                memory_type="emotional_intelligence",
                metadata={
                    "tool_type": "pattern_analysis",
                    "pattern_record": pattern_record,
                    "focus": focus,
                    "timeframe": timeframe,
                    "confidence": confidence,
                    "tags": ["emotional_intelligence", "pattern_analysis", focus]
                }
            )
            
            return {
                "success": True,
                "timeframe": timeframe,
                "focus": focus,
                "insights_count": len(insights),
                "predictive_indicators": predictive_indicators,
                "adaptations": adaptations,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error("Failed to analyze emotional patterns: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _emotional_crisis_intervention(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Implement immediate crisis intervention"""
        crisis_assessment = params["crisis_assessment"]
        intervention_strategy = params["intervention_strategy"]
        immediate_actions = params["immediate_actions"]
        safety_protocols = params["safety_protocols"]
        followup_requirements = params["followup_requirements"]
        
        logger.critical("Crisis intervention activated for user %s with strategy: %s", 
                       user_id, intervention_strategy)
        
        try:
            # Store crisis intervention with highest priority
            intervention_record = {
                "assessment": crisis_assessment,
                "strategy": intervention_strategy,
                "immediate_actions": immediate_actions,
                "safety_protocols": safety_protocols,
                "followup": followup_requirements,
                "timestamp": datetime.now().isoformat(),
                "critical": True
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"CRISIS INTERVENTION: {intervention_strategy} - Immediate actions: {len(immediate_actions)}",
                memory_type="emotional_intelligence",
                metadata={
                    "tool_type": "crisis_intervention",
                    "intervention_record": intervention_record,
                    "strategy": intervention_strategy,
                    "critical": True,
                    "immediate_risk": crisis_assessment.get("immediate_risk", False),
                    "tags": ["emotional_intelligence", "crisis_intervention", "critical"]
                }
            )
            
            return {
                "success": True,
                "intervention_strategy": intervention_strategy,
                "immediate_actions": immediate_actions,
                "safety_protocols": safety_protocols,
                "followup_required": True,
                "followup_timing": followup_requirements.get("timing", "immediate"),
                "professional_help_needed": crisis_assessment.get("professional_help_needed", False)
            }
            
        except Exception as e:
            logger.error("Failed to execute crisis intervention: %s", e)
            return {"success": False, "error": str(e)}
    
    async def get_emotional_risk_level(self, user_id: str) -> Tuple[EmotionalCrisisLevel, float]:
        """Get current emotional risk level for user"""
        try:
            # Query recent emotional intelligence memories
            recent_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="emotional crisis detection intervention",
                limit=10
            )
            
            # Analyze recent emotional state
            crisis_level = EmotionalCrisisLevel.NORMAL
            confidence = 0.0
            
            for memory in recent_memories:
                if memory.get("metadata", {}).get("tool_type") == "crisis_detection":
                    severity = memory.get("metadata", {}).get("severity", "normal")
                    mem_confidence = memory.get("metadata", {}).get("confidence", 0.0)
                    
                    # Use most severe recent detection
                    if EmotionalCrisisLevel(severity).value > crisis_level.value:
                        crisis_level = EmotionalCrisisLevel(severity)
                        confidence = mem_confidence
            
            return crisis_level, confidence
            
        except Exception as e:
            logger.error("Failed to get emotional risk level: %s", e)
            return EmotionalCrisisLevel.NORMAL, 0.0
    
    def get_emotional_history(self, user_id: str = None) -> List[EmotionalIntelligenceAction]:
        """Get emotional intelligence action history"""
        if user_id is None:
            return self.emotional_history
        return [action for action in self.emotional_history if action.user_id == user_id]