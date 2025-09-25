"""
Emotional Intelligence Tool Manager for LLM Tool Calling

CONSOLIDATION UPDATE: High-overlap tools removed and replaced with 
direct ProactiveSupport integration for better functionality.

Removed tools (replaced with ProactiveSupport integration):
- detect_emotional_crisis
- provide_proactive_support  
- emotional_crisis_intervention
- calibrate_empathy_response

Remaining: analyze_emotional_patterns (unique pattern analysis)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
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
    """
    Manages emotional intelligence tools for LLM tool calling
    
    CONSOLIDATION UPDATE: High-overlap tools removed and replaced with 
    direct ProactiveSupport integration for better functionality.
    
    Removed tools (replaced with ProactiveSupport integration):
    - detect_emotional_crisis -> Use emotional_intelligence_integration.analyze_emotional_needs()
    - provide_proactive_support -> Use emotional_intelligence_integration.analyze_emotional_needs()
    - emotional_crisis_intervention -> Use emotional_intelligence_integration.provide_crisis_intervention()
    - calibrate_empathy_response -> Use emotional_intelligence_integration.calibrate_empathy_response()
    
    Remaining: analyze_emotional_patterns (unique pattern analysis functionality)
    """
    
    def __init__(self, memory_manager, llm_client, emotion_analyzer=None, emotional_intelligence_integration=None):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.emotion_analyzer = emotion_analyzer
        self.emotional_intelligence_integration = emotional_intelligence_integration
        self.tools = self._initialize_emotional_tools()
        self.emotional_history: List[EmotionalIntelligenceAction] = []
        self.crisis_patterns = self._load_crisis_patterns()
    
    def _initialize_emotional_tools(self) -> List[Dict[str, Any]]:
        """Initialize emotional intelligence tools for LLM (consolidated - removed overlapping tools)"""
        return [
            # ONLY keep analyze_emotional_patterns - unique functionality not covered by ProactiveSupport
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
            }
            # NOTE: detect_emotional_crisis, provide_proactive_support, emotional_crisis_intervention, 
            # and calibrate_empathy_response have been REMOVED and replaced with ProactiveSupport integration
        ]
    
    def _load_crisis_patterns(self) -> Dict[str, Any]:
        """Load crisis detection patterns"""
        return {
            "crisis_keywords": [
                "suicide", "kill myself", "end it all", "give up", "hopeless",
                "worthless", "nobody cares", "can't go on", "want to die"
            ],
            "high_stress_keywords": [
                "overwhelming", "can't handle", "breaking down", "falling apart",
                "can't cope", "too much", "exhausted", "burned out"
            ],
            "support_keywords": [
                "need help", "struggling", "difficult time", "support",
                "don't know what to do", "feeling lost"
            ]
        }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available emotional intelligence tools"""
        return self.tools
    
    async def handle_tool_call(self, function_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Handle LLM tool calls for emotional intelligence
        
        CONSOLIDATION NOTE: Most tools now redirect to ProactiveSupport integration
        """
        try:
            if function_name == "analyze_emotional_patterns":
                return await self._analyze_emotional_patterns(parameters, user_id)
            
            # CONSOLIDATION: Redirect removed tools to ProactiveSupport integration
            elif function_name in ["detect_emotional_crisis", "provide_proactive_support", 
                                 "emotional_crisis_intervention", "calibrate_empathy_response"]:
                
                if self.emotional_intelligence_integration:
                    logger.info("Redirecting %s to ProactiveSupport integration", function_name)
                    
                    if function_name == "detect_emotional_crisis":
                        # Convert to emotional needs analysis
                        emotional_context = {
                            "crisis_indicators": parameters.get("crisis_indicators", []),
                            "mood_assessment": {"mood_category": parameters.get("crisis_severity", "normal")},
                            "stress_assessment": {"stress_level": parameters.get("crisis_severity", "normal")}
                        }
                        return await self.emotional_intelligence_integration.analyze_emotional_needs(
                            user_id=user_id,
                            message=" ".join(parameters.get("crisis_indicators", [])),
                            emotional_context=emotional_context
                        )
                    
                    elif function_name == "emotional_crisis_intervention":
                        return await self.emotional_intelligence_integration.provide_crisis_intervention(
                            user_id=user_id,
                            crisis_assessment=parameters
                        )
                    
                    elif function_name == "calibrate_empathy_response":
                        return await self.emotional_intelligence_integration.calibrate_empathy_response(
                            user_id=user_id,
                            detected_emotions=parameters.get("detected_emotions", []),
                            empathy_level=parameters.get("empathy_level", "moderate"),
                            emotional_context=parameters.get("emotional_context", {})
                        )
                    
                    elif function_name == "provide_proactive_support":
                        # Convert to emotional needs analysis
                        emotional_context = {
                            "support_triggers": parameters.get("support_triggers", []),
                            "emotional_predictions": {"short_term_prediction": "potential_support_needed"}
                        }
                        return await self.emotional_intelligence_integration.analyze_emotional_needs(
                            user_id=user_id,
                            message=" ".join(parameters.get("support_triggers", [])),
                            emotional_context=emotional_context
                        )
                
                else:
                    logger.warning("ProactiveSupport integration not available, tool %s disabled", function_name)
                    return {
                        "success": False, 
                        "error": f"Tool {function_name} requires ProactiveSupport integration",
                        "fallback_message": "Emotional intelligence features currently unavailable"
                    }
            
            else:
                logger.error("Unknown emotional intelligence tool: %s", function_name)
                return {"success": False, "error": f"Unknown tool: {function_name}"}
        
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Error handling emotional intelligence tool %s: %s", function_name, e)
            return {"success": False, "error": str(e)}
    
    async def _analyze_emotional_patterns(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Analyze emotional patterns for insights - UNIQUE FUNCTIONALITY RETAINED"""
        pattern_timeframe = params["pattern_timeframe"]
        pattern_focus = params["pattern_focus"]
        insights_discovered = params["insights_discovered"]
        predictive_indicators = params["predictive_indicators"]
        support_adaptations = params["support_adaptations"]
        confidence_level = params["confidence_level"]
        
        logger.info("Analyzing emotional patterns (%s) for user %s", pattern_focus, user_id)
        
        try:
            # Get relevant memories for pattern analysis
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=f"emotion mood {pattern_focus} pattern",
                limit=50,
                memory_types=["emotional_intelligence", "conversation"]
            )
            
            # Store pattern analysis
            pattern_record = {
                "timeframe": pattern_timeframe,
                "focus": pattern_focus,
                "insights": insights_discovered,
                "predictive_indicators": predictive_indicators,
                "adaptations": support_adaptations,
                "confidence": confidence_level,
                "memory_count": len(memories),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Emotional pattern analysis: {pattern_focus} over {pattern_timeframe}",
                memory_type="emotional_intelligence",
                metadata={
                    "tool_type": "pattern_analysis",
                    "pattern_record": pattern_record,
                    "focus": pattern_focus,
                    "confidence": confidence_level,
                    "tags": ["emotional_intelligence", "pattern_analysis", pattern_focus]
                }
            )
            
            return {
                "success": True,
                "pattern_analysis": pattern_record,
                "insights_count": len(insights_discovered),
                "predictive_indicators_count": len(predictive_indicators),
                "confidence_level": confidence_level,
                "memories_analyzed": len(memories)
            }
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to analyze emotional patterns: %s", e)
            return {"success": False, "error": str(e)}
    
    async def get_emotional_risk_level(self, user_id: str) -> Tuple[EmotionalCrisisLevel, float]:
        """Get current emotional risk level for user"""
        # Delegate to ProactiveSupport integration if available
        if self.emotional_intelligence_integration:
            crisis_level, confidence = await self.emotional_intelligence_integration.get_emotional_risk_level(user_id)
            
            # Convert to enum
            level_map = {
                "low": EmotionalCrisisLevel.NORMAL,
                "medium": EmotionalCrisisLevel.MODERATE_CONCERN,
                "high": EmotionalCrisisLevel.HIGH_CONCERN,
                "critical": EmotionalCrisisLevel.CRISIS
            }
            
            return level_map.get(crisis_level.level, EmotionalCrisisLevel.NORMAL), confidence
        
        # Fallback implementation
        try:
            recent_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="emotional state mood crisis stress",
                limit=20,
                memory_types=["emotional_intelligence", "conversation"]
            )
            
            crisis_level = EmotionalCrisisLevel.NORMAL
            confidence = 0.5
            
            for memory in recent_memories:
                content = memory.get("content", "").lower()
                if any(keyword in content for keyword in self.crisis_patterns["crisis_keywords"]):
                    crisis_level = EmotionalCrisisLevel.CRISIS
                    confidence = 0.9
                    break
                elif any(keyword in content for keyword in self.crisis_patterns["high_stress_keywords"]):
                    crisis_level = EmotionalCrisisLevel.HIGH_CONCERN
                    confidence = max(confidence, 0.7)
            
            return crisis_level, confidence
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to assess emotional risk: %s", e)
            return EmotionalCrisisLevel.NORMAL, 0.0
    
    def get_emotional_history(self, user_id: Optional[str] = None) -> List[EmotionalIntelligenceAction]:
        """Get emotional intelligence action history"""
        if user_id:
            return [action for action in self.emotional_history if action.user_id == user_id]
        return self.emotional_history