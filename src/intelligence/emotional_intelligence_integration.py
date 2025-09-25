"""
Emotional Intelligence Integration Service

Replaces LLM emotional intelligence tools with direct integration to ProactiveSupport system.
This consolidates crisis intervention and proactive support functionality.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from src.intelligence.proactive_support import (
    ProactiveSupport, 
    SupportIntervention, 
    SupportStrategy,
    SupportOutcome
)

logger = logging.getLogger(__name__)


@dataclass
class EmotionalCrisisLevel:
    """Emotional crisis risk level assessment"""
    level: str  # "low", "medium", "high", "critical"
    confidence: float  # 0.0-1.0
    indicators: List[str]
    immediate_risk: bool


class EmotionalIntelligenceIntegration:
    """
    Unified emotional intelligence service that integrates ProactiveSupport 
    with the existing memory and LLM systems.
    """
    
    def __init__(self, proactive_support: ProactiveSupport, memory_manager):
        self.proactive_support = proactive_support
        self.memory_manager = memory_manager
        self.intervention_history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def analyze_emotional_needs(
        self, 
        user_id: str, 
        message: str, 
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze user's emotional needs and generate support recommendations.
        
        Replaces LLM tools: detect_emotional_crisis, provide_proactive_support
        """
        logger.debug("Analyzing emotional needs for user %s", user_id)
        
        # Get user history from memory
        user_history = await self._get_user_emotional_history(user_id)
        
        # Use ProactiveSupport for comprehensive analysis
        support_needs = await self.proactive_support.analyze_support_needs(
            user_id=user_id,
            emotional_context=emotional_context,
            user_history=user_history
        )
        
        # Assess crisis level
        crisis_level = await self._assess_crisis_level(user_id, emotional_context, message)
        
        # Generate intervention if needed
        intervention = None
        if support_needs["support_urgency"] >= 3:
            intervention = await self.proactive_support.create_support_intervention(
                user_id=user_id,
                support_needs=support_needs,
                user_strategy=await self._get_user_strategy(user_id)
            )
        
        # Store analysis in memory
        await self._store_emotional_analysis(user_id, support_needs, crisis_level, intervention)
        
        return {
            "support_needs": support_needs,
            "crisis_level": {
                "level": crisis_level.level,
                "confidence": crisis_level.confidence,
                "immediate_risk": crisis_level.immediate_risk
            },
            "intervention": intervention.intervention_id if intervention else None,
            "intervention_message": intervention.message_content if intervention else None,
            "recommended_actions": support_needs.get("recommended_interventions", [])
        }
    
    async def provide_crisis_intervention(
        self, 
        user_id: str, 
        crisis_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Immediate crisis intervention using ProactiveSupport system.
        
        Replaces LLM tool: emotional_crisis_intervention
        """
        logger.critical("Crisis intervention activated for user %s", user_id)
        
        # Create high-priority crisis intervention
        crisis_context = {
            "mood_assessment": {"mood_category": "crisis"},
            "stress_assessment": {"stress_level": "critical"},
            "emotional_alerts": [{"severity": "critical", "type": "crisis_detected"}],
            "emotional_predictions": {"short_term_prediction": "immediate_support_needed"}
        }
        
        # Get comprehensive support needs
        support_needs = await self.proactive_support.analyze_support_needs(
            user_id=user_id,
            emotional_context=crisis_context,
            user_history=await self._get_user_emotional_history(user_id)
        )
        
        # Create immediate intervention
        intervention = await self.proactive_support.create_support_intervention(
            user_id=user_id,
            support_needs=support_needs
        )
        
        # Deliver intervention immediately
        delivery_context = {
            "method": "chat_message",
            "user_status": "crisis",
            "recent_interventions": self.intervention_history.get(user_id, [])
        }
        
        delivery_result = await self.proactive_support.deliver_intervention(
            intervention, delivery_context
        )
        
        # Track intervention
        if user_id not in self.intervention_history:
            self.intervention_history[user_id] = []
        
        self.intervention_history[user_id].append({
            "intervention_id": intervention.intervention_id,
            "type": "crisis_intervention",
            "timestamp": datetime.now(),
            "delivered": delivery_result["delivered"]
        })
        
        # Store crisis intervention in memory
        await self.memory_manager.store_memory(
            user_id=user_id,
            content=f"CRISIS INTERVENTION: {intervention.intervention_style.value}",
            memory_type="emotional_intelligence",
            metadata={
                "intervention_id": intervention.intervention_id,
                "crisis_level": "critical",
                "immediate_actions": support_needs.get("immediate_needs", []),
                "tags": ["crisis_intervention", "proactive_support", "critical"]
            }
        )
        
        return {
            "success": True,
            "intervention_id": intervention.intervention_id,
            "message": intervention.message_content,
            "delivery_status": delivery_result,
            "followup_required": True,
            "safety_protocols_activated": True
        }
    
    async def calibrate_empathy_response(
        self, 
        user_id: str, 
        detected_emotions: List[str], 
        empathy_level: str,
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calibrate empathy response using ProactiveSupport personalization.
        
        Replaces LLM tool: calibrate_empathy_response
        """
        # Analyze user's emotional state and history
        user_history = await self._get_user_emotional_history(user_id)
        
        # Use ProactiveSupport's personalization system
        emotional_ctx = {
            "mood_assessment": {"primary_emotions": detected_emotions},
            "emotional_context": emotional_context
        }
        
        support_needs = await self.proactive_support.analyze_support_needs(
            user_id=user_id,
            emotional_context=emotional_ctx,
            user_history=user_history
        )
        
        # Get personalization insights
        personalization = support_needs.get("personalization_insights", {})
        
        # Calibrate empathy based on user preferences and emotional state
        empathy_calibration = {
            "empathy_level": empathy_level,
            "detected_emotions": detected_emotions,
            "response_strategy": self._determine_empathy_strategy(detected_emotions, empathy_level),
            "personalization": personalization,
            "communication_adjustments": self._get_communication_adjustments(
                detected_emotions, personalization
            )
        }
        
        # Store empathy calibration
        await self.memory_manager.store_memory(
            user_id=user_id,
            content=f"Empathy calibrated: {empathy_level} for emotions: {', '.join(detected_emotions)}",
            memory_type="emotional_intelligence",
            metadata={
                "empathy_calibration": empathy_calibration,
                "tags": ["empathy", "emotional_intelligence", "calibration"]
            }
        )
        
        return empathy_calibration
    
    async def get_emotional_risk_level(self, user_id: str) -> Tuple[EmotionalCrisisLevel, float]:
        """Get current emotional risk level for user"""
        # Get recent emotional memories
        recent_memories = await self.memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="emotional state mood crisis stress",
            limit=20,
            memory_types=["emotional_intelligence", "conversation"]
        )
        
        # Analyze risk indicators
        risk_indicators = []
        confidence = 0.5
        immediate_risk = False
        level = "low"
        
        for memory in recent_memories:
            content = memory.get("content", "").lower()
            metadata = memory.get("metadata", {})
            
            # Check for crisis indicators
            if "crisis" in content or metadata.get("crisis_level") == "critical":
                risk_indicators.append("crisis_language_detected")
                level = "critical"
                confidence = 0.9
                immediate_risk = True
                break
            elif any(indicator in content for indicator in [
                "hopeless", "give up", "can't take it", "worthless", "end it all"
            ]):
                risk_indicators.append("concerning_language")
                level = "high"
                confidence = max(confidence, 0.8)
            elif any(indicator in content for indicator in [
                "stressed", "overwhelmed", "anxious", "depressed"
            ]):
                risk_indicators.append("emotional_distress")
                level = "medium" if level == "low" else level
                confidence = max(confidence, 0.6)
        
        crisis_level = EmotionalCrisisLevel(
            level=level,
            confidence=confidence,
            indicators=risk_indicators,
            immediate_risk=immediate_risk
        )
        
        return crisis_level, confidence
    
    async def _assess_crisis_level(
        self, 
        user_id: str, 
        emotional_context: Dict[str, Any], 
        message: str
    ) -> EmotionalCrisisLevel:
        """Assess crisis level from emotional context and message content"""
        crisis_indicators = []
        confidence = 0.5
        immediate_risk = False
        level = "low"
        
        # Check message content for crisis language
        message_lower = message.lower()
        crisis_keywords = [
            "suicide", "kill myself", "end it all", "give up", "hopeless",
            "worthless", "nobody cares", "can't go on", "want to die"
        ]
        
        high_stress_keywords = [
            "overwhelming", "can't handle", "breaking down", "falling apart",
            "can't cope", "too much", "exhausted", "burned out"
        ]
        
        for keyword in crisis_keywords:
            if keyword in message_lower:
                crisis_indicators.append(f"crisis_language: {keyword}")
                level = "critical"
                confidence = 0.9
                immediate_risk = True
        
        if not immediate_risk:
            for keyword in high_stress_keywords:
                if keyword in message_lower:
                    crisis_indicators.append(f"high_stress: {keyword}")
                    level = "high"
                    confidence = max(confidence, 0.7)
        
        # Check emotional context
        mood = emotional_context.get("mood_assessment", {})
        if mood.get("mood_category") in ["very_negative", "crisis"]:
            crisis_indicators.append("negative_mood_detected")
            level = "high" if level == "low" else level
            confidence = max(confidence, 0.7)
        
        stress = emotional_context.get("stress_assessment", {})
        if stress.get("stress_level") == "critical":
            crisis_indicators.append("critical_stress_detected")
            level = "critical"
            confidence = 0.9
            immediate_risk = True
        
        return EmotionalCrisisLevel(
            level=level,
            confidence=confidence,
            indicators=crisis_indicators,
            immediate_risk=immediate_risk
        )
    
    async def _get_user_emotional_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's emotional history for analysis"""
        memories = await self.memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="emotion mood stress support intervention",
            limit=50,
            memory_types=["emotional_intelligence", "conversation"]
        )
        
        # Convert to format expected by ProactiveSupport
        history = []
        for memory in memories:
            history.append({
                "timestamp": memory.get("created_at", datetime.now()),
                "content": memory.get("content", ""),
                "metadata": memory.get("metadata", {}),
                "mood_assessment": memory.get("metadata", {}).get("mood_assessment", {}),
                "stress_assessment": memory.get("metadata", {}).get("stress_assessment", {}),
                "intervention": memory.get("metadata", {}).get("intervention_record", {})
            })
        
        return history
    
    async def _get_user_strategy(self, user_id: str) -> Optional[SupportStrategy]:
        """Get personalized support strategy for user"""
        # Get user preferences from memory
        preference_memories = await self.memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="communication style preferences support effective",
            limit=20
        )
        
        # Analyze preferences
        communication_style = "gentle"  # default
        effective_approaches = []
        
        for memory in preference_memories:
            metadata = memory.get("metadata", {})
            if "effective_approaches" in metadata:
                effective_approaches.extend(metadata["effective_approaches"])
        
        # Create strategy if we have enough data
        if effective_approaches or len(preference_memories) > 5:
            return SupportStrategy(
                strategy_id=f"{user_id}_strategy",
                user_preferences={"communication_style": communication_style},
                effective_approaches=list(set(effective_approaches)),
                approaches_to_avoid=[],
                optimal_timing={"preventive_check_in": "within_24_hours"},
                communication_style=communication_style,
                support_history=[],
                last_updated=datetime.now()
            )
        
        return None
    
    def _determine_empathy_strategy(self, emotions: List[str], empathy_level: str) -> str:
        """Determine appropriate empathy response strategy"""
        if any(emotion in ["sadness", "grief", "loss"] for emotion in emotions):
            return "supportive_presence"
        elif any(emotion in ["anger", "frustration", "irritation"] for emotion in emotions):
            return "de_escalation"
        elif any(emotion in ["anxiety", "fear", "worry"] for emotion in emotions):
            return "reassurance"
        elif empathy_level == "high":
            return "deep_empathy"
        else:
            return "active_listening"
    
    def _get_communication_adjustments(
        self, 
        emotions: List[str], 
        personalization: Dict[str, Any]
    ) -> Dict[str, str]:
        """Get communication style adjustments based on emotions and personalization"""
        adjustments = {}
        
        # Adjust tone based on emotions
        if any(emotion in ["sadness", "grief"] for emotion in emotions):
            adjustments["tone"] = "gentle_supportive"
        elif any(emotion in ["anger", "frustration"] for emotion in emotions):
            adjustments["tone"] = "calm_understanding"
        elif any(emotion in ["anxiety", "fear"] for emotion in emotions):
            adjustments["tone"] = "reassuring_stable"
        
        # Adjust based on personalization insights
        if personalization.get("effective_approaches"):
            effective = personalization["effective_approaches"]
            if "direct_support" in effective:
                adjustments["directness"] = "direct"
            elif "gentle_check_in" in effective:
                adjustments["directness"] = "gentle"
        
        return adjustments
    
    async def _store_emotional_analysis(
        self, 
        user_id: str, 
        support_needs: Dict[str, Any],
        crisis_level: EmotionalCrisisLevel,
        intervention: Optional[SupportIntervention]
    ):
        """Store emotional analysis results in memory"""
        await self.memory_manager.store_memory(
            user_id=user_id,
            content=f"Emotional analysis: {crisis_level.level} risk, urgency {support_needs['support_urgency']}",
            memory_type="emotional_intelligence",
            metadata={
                "support_needs": support_needs,
                "crisis_level": crisis_level.level,
                "crisis_confidence": crisis_level.confidence,
                "intervention_id": intervention.intervention_id if intervention else None,
                "analysis_timestamp": datetime.now().isoformat(),
                "tags": ["emotional_analysis", "proactive_support", crisis_level.level]
            }
        )


def create_emotional_intelligence_integration(
    proactive_support: ProactiveSupport, 
    memory_manager
) -> EmotionalIntelligenceIntegration:
    """Factory function to create emotional intelligence integration"""
    return EmotionalIntelligenceIntegration(proactive_support, memory_manager)