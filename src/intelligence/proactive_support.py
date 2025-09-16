"""
Proactive Emotional Support System
==================================

AI-initiated emotional support system that uses predictive insights to provide
timely interventions and personalized support strategies.

Phase 2: Predictive Emotional Intelligence
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import random
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class SupportType(Enum):
    PREVENTIVE = "preventive"
    REACTIVE = "reactive"
    MAINTENANCE = "maintenance"
    CRISIS = "crisis"


class InterventionStyle(Enum):
    GENTLE_CHECK_IN = "gentle_check_in"
    DIRECT_SUPPORT = "direct_support"
    RESOURCE_OFFERING = "resource_offering"
    SKILL_BUILDING = "skill_building"
    CRISIS_INTERVENTION = "crisis_intervention"


class SupportTiming(Enum):
    IMMEDIATE = "immediate"
    WITHIN_HOUR = "within_hour"
    WITHIN_DAY = "within_day"
    NEXT_INTERACTION = "next_interaction"


@dataclass
class SupportIntervention:
    """Proactive support intervention"""

    intervention_id: str
    support_type: SupportType
    intervention_style: InterventionStyle
    timing: SupportTiming
    message_content: str
    rationale: str
    expected_outcome: str
    success_metrics: List[str]
    fallback_options: List[str]
    priority_level: int  # 1-5
    created_timestamp: datetime


@dataclass
class SupportStrategy:
    """Personalized support strategy"""

    strategy_id: str
    user_preferences: Dict[str, Any]
    effective_approaches: List[str]
    approaches_to_avoid: List[str]
    optimal_timing: Dict[str, str]
    communication_style: str
    support_history: List[Dict]
    last_updated: datetime


@dataclass
class SupportOutcome:
    """Outcome tracking for support interventions"""

    intervention_id: str
    outcome_type: str  # "successful", "partial", "ineffective", "negative"
    user_response: str
    effectiveness_score: float  # 0.0 to 1.0
    follow_up_needed: bool
    lessons_learned: List[str]
    timestamp: datetime


class ProactiveSupport:
    """AI-initiated emotional support system"""

    def __init__(self):
        """Initialize proactive support system"""
        self.intervention_counter = 0
        self.max_daily_interventions = 3  # Prevent overwhelming user
        self.min_intervention_gap = timedelta(hours=2)  # Minimum time between interventions

        # Support message templates
        self._support_templates = {
            SupportType.PREVENTIVE: {
                InterventionStyle.GENTLE_CHECK_IN: [
                    "Hi! I noticed you've been working hard lately. How are you feeling about everything?",
                    "Just wanted to check in - I've been thinking about our last conversation. How are things going?",
                    "I hope your day is going well! Is there anything on your mind that you'd like to talk about?",
                    "Hey there! I've noticed some patterns in our chats and wanted to see how you're doing today.",
                ],
                InterventionStyle.RESOURCE_OFFERING: [
                    "I've been thinking about what you mentioned, and I found some resources that might help. Would you like me to share them?",
                    "Based on our conversations, I think you might benefit from some stress management techniques. Interested?",
                    "I remember you mentioning {topic}. I have some suggestions that others have found helpful - would you like to hear them?",
                ],
            },
            SupportType.REACTIVE: {
                InterventionStyle.DIRECT_SUPPORT: [
                    "I can sense you're going through a challenging time right now. I'm here to help however I can.",
                    "It sounds like you're dealing with a lot. Let's work through this together - what feels most urgent right now?",
                    "I want you to know that what you're experiencing is valid, and you don't have to handle it alone.",
                ],
                InterventionStyle.SKILL_BUILDING: [
                    "This seems like a good moment to try that breathing technique we discussed. Would you like me to guide you through it?",
                    "I remember you found {strategy} helpful before. Would you like to use that approach again?",
                    "Let's break this down into smaller, more manageable pieces. What's the first step we could take?",
                ],
            },
            SupportType.MAINTENANCE: {
                InterventionStyle.GENTLE_CHECK_IN: [
                    "You've been doing great with {positive_pattern}! How are you feeling about your progress?",
                    "I've noticed some really positive changes in how you're handling {situation}. That's wonderful!",
                    "It's been {time_period} since we talked about {topic}. How are things going with that?",
                ]
            },
            SupportType.CRISIS: {
                InterventionStyle.CRISIS_INTERVENTION: [
                    "I'm concerned about you right now. You mentioned some really difficult feelings, and I want to make sure you're safe.",
                    "Thank you for sharing something so personal with me. Your wellbeing is important, and I'm here to support you.",
                    "I can hear how much pain you're in right now. Let's focus on getting through this moment together.",
                ]
            },
        }

        # Personalization factors
        self._personalization_factors = {
            "communication_style": {
                "formal": "professional and structured",
                "casual": "friendly and conversational",
                "direct": "straightforward and clear",
                "gentle": "soft and nurturing",
            },
            "support_preferences": {
                "practical": "concrete solutions and action steps",
                "emotional": "validation and emotional processing",
                "informational": "resources and educational content",
                "social": "connection and shared experiences",
            },
            "intervention_timing": {
                "proactive": "anticipatory support before problems escalate",
                "responsive": "immediate help when requested",
                "scheduled": "regular check-ins at preferred times",
                "crisis_only": "intervention only during high-stress periods",
            },
        }

        # Support effectiveness patterns
        self._effectiveness_indicators = {
            "positive_response": [
                "thank you",
                "helpful",
                "appreciate",
                "better",
                "good idea",
                "makes sense",
                "that works",
                "feeling better",
                "glad you asked",
            ],
            "neutral_response": ["okay", "sure", "maybe", "i guess", "possibly", "alright"],
            "negative_response": [
                "not helpful",
                "doesn't work",
                "not what i need",
                "prefer not to",
                "too much",
                "overwhelming",
                "not now",
                "leave me alone",
            ],
            "crisis_indicators": [
                "give up",
                "no point",
                "can't take it",
                "want to disappear",
                "hopeless",
                "worthless",
                "nobody cares",
                "end it all",
            ],
        }

    async def analyze_support_needs(
        self, user_id: str, emotional_context: Dict[str, Any], user_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze user's current support needs based on emotional context

        Args:
            user_id: User identifier
            emotional_context: Current emotional assessment results
            user_history: Historical interaction data

        Returns:
            Comprehensive support needs analysis
        """
        logger.debug(f"Analyzing support needs for user {user_id}")

        analysis = {
            "immediate_needs": [],
            "preventive_opportunities": [],
            "skill_building_areas": [],
            "crisis_risk_level": "low",
            "support_urgency": 1,
            "recommended_interventions": [],
            "timing_recommendations": {},
            "personalization_insights": {},
        }

        # Extract current emotional state
        mood = emotional_context.get("mood_assessment", {})
        stress = emotional_context.get("stress_assessment", {})
        alerts = emotional_context.get("emotional_alerts", [])
        predictions = emotional_context.get("emotional_predictions", {})

        # Assess immediate needs
        if mood.get("mood_category") in ["negative", "very_negative"]:
            analysis["immediate_needs"].append("emotional_validation")
            analysis["immediate_needs"].append("mood_stabilization")
            analysis["support_urgency"] = max(analysis["support_urgency"], 3)

        if stress.get("stress_level") in ["high", "critical"]:
            analysis["immediate_needs"].append("stress_management")
            analysis["immediate_needs"].append("problem_solving_support")
            analysis["support_urgency"] = max(analysis["support_urgency"], 4)

        # Check for crisis indicators
        crisis_alerts = [alert for alert in alerts if alert.get("severity") == "critical"]
        if crisis_alerts:
            analysis["crisis_risk_level"] = "high"
            analysis["immediate_needs"].append("crisis_intervention")
            analysis["support_urgency"] = 5
        elif any(alert.get("severity") == "high" for alert in alerts):
            analysis["crisis_risk_level"] = "medium"
            analysis["support_urgency"] = max(analysis["support_urgency"], 4)

        # Identify preventive opportunities
        if predictions.get("short_term_prediction") == "potential_support_needed":
            analysis["preventive_opportunities"].append("early_intervention")
            analysis["timing_recommendations"]["preventive_check_in"] = "within_24_hours"

        trajectory = emotional_context.get("emotional_trajectory", {})
        if trajectory.get("trend_direction") == "declining":
            analysis["preventive_opportunities"].append("trend_reversal")
            analysis["timing_recommendations"]["support_boost"] = "within_12_hours"

        # Analyze skill building opportunities
        if stress.get("coping_indicators", []):
            effective_coping = [
                indicator
                for indicator in stress["coping_indicators"]
                if "positive_coping" in indicator or "social_support" in indicator
            ]
            if effective_coping:
                analysis["skill_building_areas"].append("reinforce_effective_coping")
            else:
                analysis["skill_building_areas"].append("develop_coping_strategies")

        # Historical pattern analysis
        if user_history:
            recent_interactions = user_history[-5:] if len(user_history) > 5 else user_history

            # Check for recurring themes
            recurring_stressors = self._identify_recurring_patterns(
                recent_interactions, "stressors"
            )
            if recurring_stressors:
                analysis["skill_building_areas"].append("address_recurring_stressors")
                analysis["personalization_insights"]["recurring_challenges"] = recurring_stressors

            # Identify effective past interventions
            effective_strategies = self._identify_effective_strategies(user_history)
            if effective_strategies:
                analysis["personalization_insights"]["effective_approaches"] = effective_strategies

        # Generate intervention recommendations
        analysis["recommended_interventions"] = await self._generate_intervention_recommendations(
            analysis, emotional_context, user_history
        )

        logger.debug(
            f"Support needs analysis complete: urgency level {analysis['support_urgency']}"
        )
        return analysis

    def _identify_recurring_patterns(
        self, interactions: List[Dict], pattern_type: str
    ) -> List[str]:
        """Identify recurring patterns in user interactions"""
        patterns = []

        if pattern_type == "stressors":
            stressor_mentions = defaultdict(int)
            for interaction in interactions:
                stress_data = interaction.get("stress_assessment", {})
                for stressor in stress_data.get("immediate_stressors", []):
                    # Extract the main stressor category
                    if ":" in stressor:
                        category = stressor.split(":")[0]
                        stressor_mentions[category] += 1

            # Return patterns mentioned in 3+ interactions
            patterns = [category for category, count in stressor_mentions.items() if count >= 3]

        return patterns

    def _identify_effective_strategies(self, user_history: List[Dict]) -> List[str]:
        """Identify strategies that have been effective for this user"""
        effective_strategies = []

        # Look for interventions followed by improved emotional states
        for i in range(len(user_history) - 1):
            current = user_history[i]
            next_interaction = user_history[i + 1]

            if (
                "intervention" in current
                and "mood_assessment" in current
                and "mood_assessment" in next_interaction
            ):

                current_mood = current["mood_assessment"].get("mood_score", 0)
                next_mood = next_interaction["mood_assessment"].get("mood_score", 0)

                if next_mood > current_mood + 0.3:  # Significant improvement
                    intervention_style = current["intervention"].get("intervention_style")
                    if intervention_style:
                        effective_strategies.append(intervention_style)

        # Return unique strategies
        return list(set(effective_strategies))

    async def _generate_intervention_recommendations(
        self, needs_analysis: Dict, emotional_context: Dict, user_history: List[Dict]
    ) -> List[Dict]:
        """Generate specific intervention recommendations"""
        recommendations = []

        urgency = needs_analysis["support_urgency"]
        immediate_needs = needs_analysis["immediate_needs"]

        # Crisis interventions (highest priority)
        if "crisis_intervention" in immediate_needs:
            recommendations.append(
                {
                    "type": "crisis_support",
                    "style": InterventionStyle.CRISIS_INTERVENTION,
                    "timing": SupportTiming.IMMEDIATE,
                    "priority": 5,
                    "rationale": "Crisis indicators detected requiring immediate support",
                }
            )

        # High urgency interventions
        elif urgency >= 4:
            if "stress_management" in immediate_needs:
                recommendations.append(
                    {
                        "type": "stress_support",
                        "style": InterventionStyle.DIRECT_SUPPORT,
                        "timing": SupportTiming.IMMEDIATE,
                        "priority": 4,
                        "rationale": "High stress level requires immediate attention",
                    }
                )

            if "emotional_validation" in immediate_needs:
                recommendations.append(
                    {
                        "type": "emotional_support",
                        "style": InterventionStyle.GENTLE_CHECK_IN,
                        "timing": SupportTiming.WITHIN_HOUR,
                        "priority": 4,
                        "rationale": "Negative emotional state needs validation and support",
                    }
                )

        # Medium urgency interventions
        elif urgency >= 3:
            recommendations.append(
                {
                    "type": "check_in",
                    "style": InterventionStyle.GENTLE_CHECK_IN,
                    "timing": SupportTiming.WITHIN_HOUR,
                    "priority": 3,
                    "rationale": "Emotional state warrants supportive check-in",
                }
            )

        # Preventive interventions
        if "early_intervention" in needs_analysis["preventive_opportunities"]:
            recommendations.append(
                {
                    "type": "preventive_check_in",
                    "style": InterventionStyle.GENTLE_CHECK_IN,
                    "timing": SupportTiming.WITHIN_DAY,
                    "priority": 2,
                    "rationale": "Predictive model suggests support may be needed soon",
                }
            )

        # Skill building opportunities
        if needs_analysis["skill_building_areas"]:
            recommendations.append(
                {
                    "type": "skill_building",
                    "style": InterventionStyle.SKILL_BUILDING,
                    "timing": SupportTiming.NEXT_INTERACTION,
                    "priority": 2,
                    "rationale": f"Opportunity to build skills in: {', '.join(needs_analysis['skill_building_areas'])}",
                }
            )

        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"], reverse=True)

        return recommendations

    async def create_support_intervention(
        self,
        user_id: str,
        support_needs: Dict[str, Any],
        user_strategy: Optional[SupportStrategy] = None,
    ) -> SupportIntervention:
        """
        Create a personalized support intervention

        Args:
            user_id: User identifier
            support_needs: Result from analyze_support_needs
            user_strategy: Personalized support strategy (if available)

        Returns:
            Personalized support intervention
        """
        logger.debug(f"Creating support intervention for user {user_id}")

        recommendations = support_needs.get("recommended_interventions", [])
        if not recommendations:
            # Create a default gentle check-in
            recommendations = [
                {
                    "type": "check_in",
                    "style": InterventionStyle.GENTLE_CHECK_IN,
                    "timing": SupportTiming.NEXT_INTERACTION,
                    "priority": 1,
                    "rationale": "Regular supportive contact",
                }
            ]

        # Select highest priority recommendation
        primary_recommendation = recommendations[0]

        # Determine support type and timing
        support_type = self._map_recommendation_to_support_type(primary_recommendation)
        intervention_style = primary_recommendation["style"]
        timing = primary_recommendation["timing"]

        # Generate personalized message
        message_content = await self._generate_personalized_message(
            support_type, intervention_style, user_strategy, support_needs
        )

        # Create intervention
        self.intervention_counter += 1
        intervention = SupportIntervention(
            intervention_id=f"{user_id}_intervention_{self.intervention_counter}",
            support_type=support_type,
            intervention_style=intervention_style,
            timing=timing,
            message_content=message_content,
            rationale=primary_recommendation["rationale"],
            expected_outcome=self._determine_expected_outcome(support_type, intervention_style),
            success_metrics=self._define_success_metrics(support_type),
            fallback_options=self._generate_fallback_options(intervention_style),
            priority_level=primary_recommendation["priority"],
            created_timestamp=datetime.now(timezone.utc),
        )

        logger.debug(
            f"Created intervention {intervention.intervention_id} with priority {intervention.priority_level}"
        )
        return intervention

    def _map_recommendation_to_support_type(self, recommendation: Dict) -> SupportType:
        """Map recommendation type to support type"""
        rec_type = recommendation["type"]

        if rec_type in ["crisis_support"]:
            return SupportType.CRISIS
        elif rec_type in ["stress_support", "emotional_support"]:
            return SupportType.REACTIVE
        elif rec_type in ["preventive_check_in"]:
            return SupportType.PREVENTIVE
        elif rec_type in ["skill_building"]:
            return SupportType.MAINTENANCE
        else:
            return SupportType.PREVENTIVE

    async def _generate_personalized_message(
        self,
        support_type: SupportType,
        intervention_style: InterventionStyle,
        user_strategy: Optional[SupportStrategy],
        support_needs: Dict,
    ) -> str:
        """Generate personalized intervention message"""

        # Get base templates
        templates = self._support_templates.get(support_type, {}).get(intervention_style, [])
        if not templates:
            templates = ["I wanted to check in with you. How are you doing?"]

        # Select template
        base_message = random.choice(templates)

        # Personalize based on user strategy
        if user_strategy:
            communication_style = user_strategy.communication_style

            # Adjust tone based on communication style
            if communication_style == "formal":
                base_message = self._formalize_message(base_message)
            elif communication_style == "casual":
                base_message = self._casualize_message(base_message)
            elif communication_style == "direct":
                base_message = self._make_message_direct(base_message)
            elif communication_style == "gentle":
                base_message = self._soften_message(base_message)

        # Add context-specific personalization
        personalization_insights = support_needs.get("personalization_insights", {})

        # Replace placeholders with relevant context
        if "{topic}" in base_message:
            recurring_challenges = personalization_insights.get("recurring_challenges", ["stress"])
            topic = recurring_challenges[0] if recurring_challenges else "stress management"
            base_message = base_message.replace("{topic}", topic)

        if "{strategy}" in base_message:
            effective_approaches = personalization_insights.get(
                "effective_approaches", ["breathing exercises"]
            )
            strategy = effective_approaches[0] if effective_approaches else "coping strategies"
            base_message = base_message.replace("{strategy}", strategy)

        if "{positive_pattern}" in base_message:
            base_message = base_message.replace(
                "{positive_pattern}", "managing challenging situations"
            )

        if "{time_period}" in base_message:
            base_message = base_message.replace("{time_period}", "a few days")

        if "{situation}" in base_message:
            base_message = base_message.replace("{situation}", "difficult situations")

        return base_message

    def _formalize_message(self, message: str) -> str:
        """Make message more formal"""
        replacements = {
            "Hi!": "Hello,",
            "Hey there!": "Good day,",
            "How are you feeling": "How would you describe your current state",
            "you've been": "you have been",
            "I've": "I have",
            "you're": "you are",
            "Let's": "Shall we",
            "that's": "that is",
        }

        for informal, formal in replacements.items():
            message = message.replace(informal, formal)
        return message

    def _casualize_message(self, message: str) -> str:
        """Make message more casual"""
        replacements = {
            "Hello,": "Hey!",
            "Good day,": "Hi there!",
            "I hope": "Hope",
            "Would you like": "Want to",
            "I have": "I've got",
            "you have been": "you've been",
        }

        for formal, casual in replacements.items():
            message = message.replace(formal, casual)
        return message

    def _make_message_direct(self, message: str) -> str:
        """Make message more direct"""
        # Remove softening language
        message = message.replace("I was wondering if", "")
        message = message.replace("perhaps", "")
        message = message.replace("maybe", "")
        message = message.replace("if you don't mind", "")

        # Make statements more direct
        message = message.replace("Would you like to", "Let's")
        message = message.replace("You might want to", "You should")

        return message.strip()

    def _soften_message(self, message: str) -> str:
        """Make message gentler"""
        # Add softening language
        if "How are you" in message:
            message = message.replace("How are you", "I hope you're doing well. How are you")

        if message.startswith("Let's"):
            message = message.replace("Let's", "If you're comfortable with it, we could")

        # Add gentle qualifiers
        message = message.replace("You should", "You might consider")
        message = message.replace("You need to", "It might help to")

        return message

    def _determine_expected_outcome(
        self, support_type: SupportType, intervention_style: InterventionStyle
    ) -> str:
        """Determine expected outcome for intervention"""
        outcomes = {
            (
                SupportType.CRISIS,
                InterventionStyle.CRISIS_INTERVENTION,
            ): "immediate emotional stabilization and safety confirmation",
            (
                SupportType.REACTIVE,
                InterventionStyle.DIRECT_SUPPORT,
            ): "stress reduction and problem-solving engagement",
            (
                SupportType.PREVENTIVE,
                InterventionStyle.GENTLE_CHECK_IN,
            ): "early issue identification and rapport maintenance",
            (
                SupportType.MAINTENANCE,
                InterventionStyle.SKILL_BUILDING,
            ): "skill reinforcement and confidence building",
        }

        return outcomes.get(
            (support_type, intervention_style), "positive user engagement and emotional support"
        )

    def _define_success_metrics(self, support_type: SupportType) -> List[str]:
        """Define success metrics for intervention type"""
        metrics = {
            SupportType.CRISIS: [
                "user confirms safety",
                "crisis language decreases",
                "user engages with support resources",
                "immediate stress reduction",
            ],
            SupportType.REACTIVE: [
                "stress level decreases",
                "user reports feeling better",
                "problem-solving engagement",
                "positive emotional shift",
            ],
            SupportType.PREVENTIVE: [
                "user responds positively",
                "early issues identified",
                "relationship maintained",
                "future support openness",
            ],
            SupportType.MAINTENANCE: [
                "skill application attempted",
                "confidence increased",
                "positive pattern reinforcement",
                "continued engagement",
            ],
        }

        return metrics.get(support_type, ["positive user response", "engagement maintained"])

    def _generate_fallback_options(self, intervention_style: InterventionStyle) -> List[str]:
        """Generate fallback options if primary intervention isn't effective"""
        fallbacks = {
            InterventionStyle.GENTLE_CHECK_IN: [
                "Offer more direct support if needed",
                "Provide specific resources",
                "Adjust communication style",
                "Give space if user prefers",
            ],
            InterventionStyle.DIRECT_SUPPORT: [
                "Break down support into smaller steps",
                "Offer alternative coping strategies",
                "Connect with external resources",
                "Schedule follow-up check-in",
            ],
            InterventionStyle.CRISIS_INTERVENTION: [
                "Escalate to emergency resources",
                "Provide crisis hotline information",
                "Maintain continuous monitoring",
                "Involve support network if appropriate",
            ],
            InterventionStyle.SKILL_BUILDING: [
                "Simplify skill into smaller components",
                "Try different learning approach",
                "Focus on motivation building",
                "Postpone to better timing",
            ],
        }

        return fallbacks.get(intervention_style, ["Adjust approach based on user response"])

    async def deliver_intervention(
        self, intervention: SupportIntervention, delivery_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deliver the support intervention to the user

        Args:
            intervention: The intervention to deliver
            delivery_context: Context for delivery (channel, timing, etc.)

        Returns:
            Delivery result and tracking information
        """
        logger.debug(f"Delivering intervention {intervention.intervention_id}")

        # Check delivery constraints
        delivery_checks = await self._validate_delivery_timing(intervention, delivery_context)
        if not delivery_checks["can_deliver"]:
            return {
                "delivered": False,
                "reason": delivery_checks["reason"],
                "suggested_delay": delivery_checks.get("suggested_delay"),
                "intervention_id": intervention.intervention_id,
            }

        # Prepare delivery
        delivery_method = delivery_context.get("method", "chat_message")

        delivery_result = {
            "delivered": True,
            "intervention_id": intervention.intervention_id,
            "message_content": intervention.message_content,
            "delivery_method": delivery_method,
            "delivery_timestamp": datetime.now(timezone.utc),
            "expected_response_timeframe": self._calculate_response_timeframe(intervention.timing),
            "tracking_metrics": intervention.success_metrics,
            "fallback_plan": intervention.fallback_options,
        }

        logger.info(f"Successfully delivered intervention {intervention.intervention_id}")
        return delivery_result

    async def _validate_delivery_timing(
        self, intervention: SupportIntervention, delivery_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate if intervention should be delivered now"""

        # Check for recent interventions to avoid overwhelming
        recent_interventions = delivery_context.get("recent_interventions", [])
        if recent_interventions:
            last_intervention_time = max(
                recent_interventions, key=lambda x: x.get("timestamp", datetime.min)
            )
            time_since_last = datetime.now(timezone.utc) - last_intervention_time.get(
                "timestamp", datetime.min
            )

            if time_since_last < self.min_intervention_gap and intervention.priority_level < 5:
                return {
                    "can_deliver": False,
                    "reason": "too_soon_after_last_intervention",
                    "suggested_delay": self.min_intervention_gap - time_since_last,
                }

        # Check daily intervention limit (except for crisis)
        today_interventions = [
            i
            for i in recent_interventions
            if i.get("timestamp", datetime.min).date() == datetime.now().date()
        ]

        if (
            len(today_interventions) >= self.max_daily_interventions
            and intervention.priority_level < 5
        ):
            return {
                "can_deliver": False,
                "reason": "daily_limit_reached",
                "suggested_delay": "next_day",
            }

        # Check user availability context
        user_status = delivery_context.get("user_status", "available")
        if user_status == "busy" and intervention.priority_level < 4:
            return {"can_deliver": False, "reason": "user_busy", "suggested_delay": "later_today"}

        # Always deliver crisis interventions
        if intervention.support_type == SupportType.CRISIS:
            return {"can_deliver": True}

        # Check timing preferences
        if intervention.timing == SupportTiming.IMMEDIATE:
            return {"can_deliver": True}
        elif intervention.timing == SupportTiming.WITHIN_HOUR:
            return {"can_deliver": True}  # Could add hour-based logic here
        elif intervention.timing == SupportTiming.WITHIN_DAY:
            return {"can_deliver": True}  # Could add day-based logic here
        else:  # NEXT_INTERACTION
            return {
                "can_deliver": False,
                "reason": "wait_for_next_interaction",
                "suggested_delay": "next_user_message",
            }

    def _calculate_response_timeframe(self, timing: SupportTiming) -> str:
        """Calculate expected response timeframe"""
        timeframes = {
            SupportTiming.IMMEDIATE: "within minutes",
            SupportTiming.WITHIN_HOUR: "within 1 hour",
            SupportTiming.WITHIN_DAY: "within 24 hours",
            SupportTiming.NEXT_INTERACTION: "next conversation",
        }
        return timeframes.get(timing, "when appropriate")

    async def track_intervention_outcome(
        self, intervention_id: str, user_response: str, outcome_context: Dict[str, Any]
    ) -> SupportOutcome:
        """
        Track the outcome of a support intervention

        Args:
            intervention_id: ID of the intervention to track
            user_response: User's response to the intervention
            outcome_context: Additional context about the outcome

        Returns:
            Outcome tracking information
        """
        logger.debug(f"Tracking outcome for intervention {intervention_id}")

        # Analyze user response for effectiveness indicators
        response_lower = user_response.lower()
        effectiveness_score = 0.5  # Default neutral
        outcome_type = "partial"

        # Check for positive response indicators
        positive_indicators = self._effectiveness_indicators["positive_response"]
        positive_matches = sum(
            1 for indicator in positive_indicators if indicator in response_lower
        )

        # Check for negative response indicators
        negative_indicators = self._effectiveness_indicators["negative_response"]
        negative_matches = sum(
            1 for indicator in negative_indicators if indicator in response_lower
        )

        # Check for crisis indicators
        crisis_indicators = self._effectiveness_indicators["crisis_indicators"]
        crisis_matches = sum(1 for indicator in crisis_indicators if indicator in response_lower)

        # Calculate effectiveness
        if crisis_matches > 0:
            effectiveness_score = 0.0
            outcome_type = "crisis_escalation"
        elif positive_matches > negative_matches:
            effectiveness_score = min(1.0, 0.7 + (positive_matches * 0.1))
            outcome_type = "successful"
        elif negative_matches > positive_matches:
            effectiveness_score = max(0.0, 0.3 - (negative_matches * 0.1))
            outcome_type = "ineffective"

        # Determine follow-up needs
        follow_up_needed = (
            effectiveness_score < 0.4
            or crisis_matches > 0
            or outcome_type in ["ineffective", "crisis_escalation"]
        )

        # Generate lessons learned
        lessons_learned = []
        if effectiveness_score > 0.7:
            lessons_learned.append("User responded positively to this intervention style")
        elif effectiveness_score < 0.3:
            lessons_learned.append("This intervention approach may not be effective for this user")

        if crisis_matches > 0:
            lessons_learned.append("Crisis indicators detected - escalate support level")

        outcome = SupportOutcome(
            intervention_id=intervention_id,
            outcome_type=outcome_type,
            user_response=user_response,
            effectiveness_score=effectiveness_score,
            follow_up_needed=follow_up_needed,
            lessons_learned=lessons_learned,
            timestamp=datetime.now(timezone.utc),
        )

        logger.debug(
            f"Intervention outcome: {outcome_type} (effectiveness: {effectiveness_score:.2f})"
        )
        return outcome

    def generate_support_summary(
        self, intervention: SupportIntervention, outcome: Optional[SupportOutcome] = None
    ) -> Dict[str, Any]:
        """Generate human-readable support summary"""
        summary = {
            "intervention": {
                "id": intervention.intervention_id,
                "type": intervention.support_type.value,
                "style": intervention.intervention_style.value,
                "priority": intervention.priority_level,
                "timing": intervention.timing.value,
                "rationale": intervention.rationale,
            },
            "delivery": {
                "message": intervention.message_content,
                "expected_outcome": intervention.expected_outcome,
                "success_metrics": intervention.success_metrics,
            },
        }

        if outcome:
            summary["outcome"] = {
                "type": outcome.outcome_type,
                "effectiveness": f"{outcome.effectiveness_score:.1%}",
                "follow_up_needed": outcome.follow_up_needed,
                "lessons_learned": outcome.lessons_learned,
            }

        return summary
