"""
Phase 2 Integration Module
=========================

Integrates Phase 2 Predictive Emotional Intelligence with the main bot system.
Provides seamless integration with existing personality profiling and memory systems.
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json

from .emotional_intelligence import PredictiveEmotionalIntelligence, EmotionalIntelligenceAssessment

logger = logging.getLogger(__name__)

class Phase2Integration:
    """Integration layer for Phase 2 Predictive Emotional Intelligence"""
    
    def __init__(self, bot_instance=None, graph_personality_manager=None, conversation_cache=None):
        """Initialize Phase 2 integration"""
        logger.info("Initializing Phase 2 Emotional Intelligence Integration")
        
        self.bot = bot_instance
        self.emotional_intelligence = PredictiveEmotionalIntelligence(
            graph_personality_manager=graph_personality_manager,
            conversation_cache=conversation_cache
        )
        
        # Integration settings
        self.auto_intervention_enabled = True
        self.intervention_cooldown = timedelta(hours=2)
        self.last_interventions = {}  # Track last intervention time per user
        
        logger.info("Phase 2 Integration initialized successfully")

    async def process_message_with_emotional_intelligence(self, user_id: str, 
                                                        message: str,
                                                        conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process message with full emotional intelligence capabilities
        
        Args:
            user_id: User identifier
            message: User's message
            conversation_context: Full conversation context
            
        Returns:
            Enhanced context with emotional intelligence insights
        """
        logger.debug(f"Processing message with emotional intelligence for user {user_id}")
        
        try:
            # Perform comprehensive emotional assessment
            assessment = await self.emotional_intelligence.comprehensive_emotional_assessment(
                user_id, message, conversation_context
            )
            
            # Add emotional intelligence data to context
            enhanced_context = conversation_context.copy()
            enhanced_context.update({
                'emotional_intelligence': {
                    'assessment': assessment,
                    'mood': assessment.mood_assessment.mood_category.value,
                    'stress_level': assessment.stress_assessment.stress_level.value,
                    'predicted_emotion': assessment.emotional_prediction.predicted_emotion,
                    'risk_level': assessment.emotional_prediction.risk_level,
                    'phase_status': assessment.phase_status.value,
                    'confidence': assessment.confidence_score,
                    'alerts': len(assessment.emotional_alerts),
                    'support_needed': assessment.recommended_intervention is not None
                }
            })
            
            # Execute intervention if needed and appropriate
            if (assessment.recommended_intervention and 
                self.auto_intervention_enabled and
                self._should_execute_intervention(user_id)):
                
                intervention_result = await self._execute_automatic_intervention(
                    user_id, assessment.recommended_intervention, enhanced_context
                )
                enhanced_context['emotional_intelligence']['intervention_executed'] = intervention_result
            
            # Generate bot response recommendations
            response_guidance = self._generate_response_guidance(assessment)
            enhanced_context['emotional_intelligence']['response_guidance'] = response_guidance
            
            logger.debug(f"Emotional intelligence processing complete: {assessment.phase_status.value} status")
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Error in emotional intelligence processing for {user_id}: {str(e)}")
            # Return original context with error indication
            enhanced_context = conversation_context.copy()
            enhanced_context['emotional_intelligence'] = {
                'error': str(e),
                'status': 'error',
                'fallback_mode': True
            }
            return enhanced_context

    def _should_execute_intervention(self, user_id: str) -> bool:
        """Check if intervention should be executed based on cooldown and settings"""
        if not self.auto_intervention_enabled:
            return False
        
        if user_id in self.last_interventions:
            time_since_last = datetime.now(timezone.utc) - self.last_interventions[user_id]
            if time_since_last < self.intervention_cooldown:
                logger.debug(f"Intervention cooldown active for {user_id}: {time_since_last} < {self.intervention_cooldown}")
                return False
        
        return True

    async def _execute_automatic_intervention(self, user_id: str, 
                                            intervention: Any,
                                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute automatic intervention"""
        logger.info(f"Executing automatic intervention for {user_id}: {intervention.intervention_id}")
        
        try:
            # Prepare delivery context
            delivery_context = {
                'method': 'chat_message',
                'user_status': 'available',  # Could be enhanced with actual status
                'recent_interventions': context.get('recent_interventions', [])
            }
            
            # Execute intervention
            result = await self.emotional_intelligence.execute_intervention(
                intervention, delivery_context
            )
            
            if result['delivered']:
                self.last_interventions[user_id] = datetime.now(timezone.utc)
                logger.info(f"Intervention {intervention.intervention_id} executed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing automatic intervention for {user_id}: {str(e)}")
            return {
                'delivered': False,
                'error': str(e),
                'intervention_id': intervention.intervention_id
            }

    def _generate_response_guidance(self, assessment: EmotionalIntelligenceAssessment) -> Dict[str, Any]:
        """Generate guidance for bot response based on emotional assessment"""
        
        guidance = {
            'tone_adjustments': [],
            'content_suggestions': [],
            'avoid_topics': [],
            'priority_focus': [],
            'intervention_needed': assessment.recommended_intervention is not None
        }
        
        mood = assessment.mood_assessment
        stress = assessment.stress_assessment
        alerts = assessment.emotional_alerts
        
        # Tone adjustments based on mood
        if mood.mood_category.value in ['negative', 'very_negative']:
            guidance['tone_adjustments'].extend([
                'use_empathetic_tone',
                'acknowledge_feelings',
                'be_patient_and_understanding',
                'avoid_overly_cheerful_responses'
            ])
        elif mood.mood_category.value in ['positive', 'very_positive']:
            guidance['tone_adjustments'].extend([
                'match_positive_energy',
                'celebrate_achievements',
                'encourage_momentum',
                'be_enthusiastic'
            ])
        
        # Content suggestions based on stress level
        if stress.stress_level.value in ['high', 'critical']:
            guidance['content_suggestions'].extend([
                'offer_immediate_stress_relief',
                'break_down_complex_problems',
                'provide_step_by_step_guidance',
                'suggest_coping_strategies'
            ])
            guidance['avoid_topics'].extend([
                'additional_complexity',
                'overwhelming_information',
                'non_urgent_topics'
            ])
        
        # Priority focus based on alerts
        high_priority_alerts = [alert for alert in alerts if alert.urgency_level >= 4]
        if high_priority_alerts:
            guidance['priority_focus'].extend([
                'address_immediate_concerns',
                'provide_emotional_support',
                'monitor_for_crisis_indicators',
                'offer_concrete_assistance'
            ])
        
        # Prediction-based guidance
        predicted_emotion = assessment.emotional_prediction.predicted_emotion
        if predicted_emotion in ['stress', 'anxiety']:
            guidance['content_suggestions'].append('proactive_stress_management')
        elif predicted_emotion in ['frustration', 'anger']:
            guidance['tone_adjustments'].append('remain_calm_and_patient')
            guidance['content_suggestions'].append('validate_concerns')
        
        return guidance

    async def handle_intervention_response(self, user_id: str, 
                                         intervention_id: str,
                                         user_response: str,
                                         response_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle user response to an intervention
        
        Args:
            user_id: User identifier
            intervention_id: ID of the intervention
            user_response: User's response
            response_context: Additional context
            
        Returns:
            Outcome tracking information
        """
        logger.debug(f"Handling intervention response from {user_id} for {intervention_id}")
        
        try:
            outcome = await self.emotional_intelligence.track_intervention_response(
                intervention_id, user_response, response_context
            )
            
            # Additional integration-specific processing
            if outcome.follow_up_needed:
                logger.info(f"Follow-up needed for intervention {intervention_id}")
                # Could trigger additional follow-up logic here
            
            if outcome.effectiveness_score >= 0.8:
                logger.info(f"Highly effective intervention {intervention_id} - learning from success")
                # Could enhance learning algorithms here
            
            return {
                'outcome': outcome,
                'follow_up_needed': outcome.follow_up_needed,
                'effectiveness': outcome.effectiveness_score,
                'lessons_learned': outcome.lessons_learned
            }
            
        except Exception as e:
            logger.error(f"Error handling intervention response for {user_id}: {str(e)}")
            return {
                'error': str(e),
                'intervention_id': intervention_id,
                'follow_up_needed': True
            }

    async def get_user_emotional_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get current emotional status for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Current emotional status summary
        """
        try:
            dashboard = await self.emotional_intelligence.get_user_emotional_dashboard(user_id)
            
            # Add integration-specific information
            dashboard['integration_status'] = {
                'auto_intervention_enabled': self.auto_intervention_enabled,
                'last_intervention': self.last_interventions.get(user_id, {}).isoformat() if user_id in self.last_interventions else None,
                'cooldown_active': not self._should_execute_intervention(user_id)
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error getting emotional status for {user_id}: {str(e)}")
            return {
                'user_id': user_id,
                'status': 'error',
                'error': str(e)
            }

    async def generate_proactive_check_in(self, user_id: str) -> Optional[str]:
        """
        Generate proactive check-in message if appropriate
        
        Args:
            user_id: User identifier
            
        Returns:
            Check-in message if appropriate, None otherwise
        """
        try:
            # Get user's emotional dashboard
            dashboard = await self.emotional_intelligence.get_user_emotional_dashboard(user_id)
            
            if dashboard.get('status') == 'no_data':
                return None
            
            current_status = dashboard.get('current_status', {})
            trends = dashboard.get('trends', {})
            
            # Check if proactive check-in is warranted
            should_check_in = False
            check_in_reason = []
            
            # Check for declining trends
            if trends.get('mood_trend') == 'declining':
                should_check_in = True
                check_in_reason.append('declining mood trend')
            
            if trends.get('stress_trend') == 'increasing':
                should_check_in = True
                check_in_reason.append('increasing stress')
            
            # Check for high-risk status
            if current_status.get('phase') in ['intervention', 'crisis']:
                should_check_in = True
                check_in_reason.append('high-risk emotional state')
            
            # Check time since last interaction (would need to be implemented)
            # if time_since_last_interaction > threshold:
            #     should_check_in = True
            #     check_in_reason.append('extended absence')
            
            if should_check_in and self._should_execute_intervention(user_id):
                # Generate personalized check-in message
                check_in_messages = [
                    f"Hi! I've been thinking about our recent conversations and wanted to check in. How are you doing today?",
                    f"Just wanted to reach out and see how things are going. I'm here if you need to talk about anything.",
                    f"I hope you're having a good day! I noticed some patterns in our chats and wanted to make sure you're doing well.",
                    f"Hi there! How are you feeling today? I'm here to listen if you want to share what's on your mind."
                ]
                
                # Could be enhanced with personalization based on user preferences
                import random
                message = random.choice(check_in_messages)
                
                logger.info(f"Generated proactive check-in for {user_id}: {', '.join(check_in_reason)}")
                return message
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating proactive check-in for {user_id}: {str(e)}")
            return None

    async def get_system_status(self) -> Dict[str, Any]:
        """Get Phase 2 system status"""
        try:
            health_report = await self.emotional_intelligence.get_system_health_report()
            
            # Add integration-specific status
            health_report['integration_status'] = {
                'phase_2_active': True,
                'auto_intervention_enabled': self.auto_intervention_enabled,
                'total_users_with_interventions': len(self.last_interventions),
                'integration_version': '2.0'
            }
            
            return health_report
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'integration_status': {
                    'phase_2_active': False,
                    'error': True
                }
            }

    def configure_auto_intervention(self, enabled: bool, cooldown_hours: Optional[float] = None):
        """Configure automatic intervention settings"""
        self.auto_intervention_enabled = enabled
        
        if cooldown_hours is not None:
            self.intervention_cooldown = timedelta(hours=cooldown_hours)
        
        logger.info(f"Auto-intervention configured: enabled={enabled}, cooldown={self.intervention_cooldown}")

    async def force_assessment(self, user_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Force an immediate emotional assessment (for testing/debugging)"""
        logger.info(f"Forcing emotional assessment for user {user_id}")
        
        try:
            assessment = await self.emotional_intelligence.comprehensive_emotional_assessment(
                user_id, message, context
            )
            
            summary = self.emotional_intelligence.get_assessment_summary(assessment)
            
            return {
                'forced_assessment': True,
                'user_id': user_id,
                'assessment_summary': summary,
                'full_assessment': assessment,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in forced assessment for {user_id}: {str(e)}")
            return {
                'forced_assessment': False,
                'error': str(e),
                'user_id': user_id
            }

# Global instance for integration
phase2_integration = None

def initialize_phase2_integration(bot_instance=None, graph_personality_manager=None, conversation_cache=None):
    """Initialize global Phase 2 integration instance"""
    global phase2_integration
    phase2_integration = Phase2Integration(bot_instance, graph_personality_manager, conversation_cache)
    return phase2_integration

def get_phase2_integration():
    """Get global Phase 2 integration instance"""
    return phase2_integration