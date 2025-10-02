#!/usr/bin/env python3
"""
🎯 WHISPERENGINE EMOTIONAL TRAJECTORY ANALYSIS DEMONSTRATION

This script demonstrates WhisperEngine's multi-message trajectory analysis 
capabilities, showing how the system analyzes conversation patterns and 
emotional progression over time.

CRITICAL: WhisperEngine analyzes multiple messages to understand:
1. 🎭 Emotional trajectory tracking
2. 📊 Conversation flow patterns  
3. 🔄 Relationship progression dynamics
4. 🎨 Multi-dimensional conversation intelligence
"""

import asyncio
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrajectoryAnalysisDemo:
    """
    Demonstrates WhisperEngine's multi-message trajectory analysis capabilities
    """
    
    def __init__(self):
        self.setup_trajectory_analysis()
    
    def setup_trajectory_analysis(self):
        """Setup trajectory analysis components"""
        # Emotional valence mapping for trajectory calculation
        self.emotion_valences = {
            'joy': 2.0, 'excitement': 1.8, 'gratitude': 1.5, 'contentment': 1.2,
            'love': 2.0, 'hope': 1.3, 'curiosity': 0.8, 'anticipation': 0.9,
            'neutral': 0.0, 'contemplative': 0.2, 'reflective': 0.1,
            'sadness': -1.5, 'disappointment': -1.2, 'frustration': -1.0,
            'anger': -2.0, 'fear': -1.8, 'anxiety': -1.6, 'worry': -1.3
        }
        
        # Conversation depth indicators
        self.depth_indicators = {
            'surface': ['hello', 'hi', 'how are you', 'weather', 'news'],
            'engaging': ['interesting', 'tell me', 'think about', 'opinion'],
            'personal': ['feel', 'experience', 'important to me', 'personal'],
            'intimate': ['secret', 'private', 'deeply', 'vulnerable', 'trust'],
            'profound': ['meaning', 'purpose', 'soul', 'existence', 'profound']
        }
    
    def simulate_multi_message_conversation(self) -> List[Dict[str, Any]]:
        """
        Simulate a realistic multi-message conversation showing trajectory progression
        """
        conversation_messages = [
            {
                "timestamp": "2024-10-01T09:00:00Z",
                "user_message": "Good morning! How are you today?",
                "emotion": "neutral", 
                "depth": "surface",
                "relationship_state": "casual"
            },
            {
                "timestamp": "2024-10-01T09:02:00Z", 
                "user_message": "I've been thinking about starting a new creative project.",
                "emotion": "curious",
                "depth": "engaging",
                "relationship_state": "warming"
            },
            {
                "timestamp": "2024-10-01T09:05:00Z",
                "user_message": "Actually, I'm feeling a bit anxious about whether I'm talented enough.",
                "emotion": "anxiety",
                "depth": "personal", 
                "relationship_state": "opening_up"
            },
            {
                "timestamp": "2024-10-01T09:07:00Z",
                "user_message": "I've struggled with self-doubt my whole life, if I'm being honest.",
                "emotion": "sadness",
                "depth": "personal",
                "relationship_state": "vulnerable_sharing"
            },
            {
                "timestamp": "2024-10-01T09:10:00Z",
                "user_message": "Thank you for listening. It feels good to share this with someone.",
                "emotion": "gratitude",
                "depth": "intimate",
                "relationship_state": "trust_building"
            },
            {
                "timestamp": "2024-10-01T09:12:00Z", 
                "user_message": "You know what? Maybe I should just go for it anyway!",
                "emotion": "excitement",
                "depth": "engaging",
                "relationship_state": "confident_partnership"
            },
            {
                "timestamp": "2024-10-01T09:15:00Z",
                "user_message": "I'm actually feeling hopeful now. This conversation really helped.",
                "emotion": "hope",
                "depth": "personal",
                "relationship_state": "deep_appreciation"
            }
        ]
        
        return conversation_messages
    
    def analyze_emotional_trajectory(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze emotional trajectory across multiple messages (WhisperEngine approach)
        """
        print(f"\n🎭 EMOTIONAL TRAJECTORY ANALYSIS")
        print("=" * 70)
        
        emotions = [msg["emotion"] for msg in messages]
        valences = [self.emotion_valences.get(emotion, 0.0) for emotion in emotions]
        
        print(f"📈 Emotion Sequence: {' → '.join(emotions)}")
        print(f"📊 Valence Values: {[f'{v:.1f}' for v in valences]}")
        
        # Calculate trajectory metrics
        trajectory_metrics = self._calculate_trajectory_metrics(emotions, valences)
        
        # Analyze emotional patterns
        patterns = self._detect_emotional_patterns(emotions)
        
        # Calculate momentum and stability
        momentum = self._calculate_emotional_momentum(valences)
        stability = self._calculate_emotional_stability(valences)
        
        trajectory_analysis = {
            "emotions_sequence": emotions,
            "valence_progression": valences,
            "trajectory_direction": trajectory_metrics["direction"],
            "emotional_velocity": trajectory_metrics["velocity"],
            "emotional_momentum": momentum,
            "stability_score": stability,
            "patterns_detected": patterns,
            "conversation_arc": self._determine_conversation_arc(valences),
            "key_transitions": self._identify_key_transitions(emotions, messages)
        }
        
        self._display_trajectory_results(trajectory_analysis)
        return trajectory_analysis
    
    def analyze_conversation_flow_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze conversation flow and depth progression (WhisperEngine approach)
        """
        print(f"\n📊 CONVERSATION FLOW ANALYSIS")
        print("=" * 70)
        
        depth_progression = [msg["depth"] for msg in messages]
        relationship_progression = [msg["relationship_state"] for msg in messages]
        
        print(f"🔍 Depth Progression: {' → '.join(depth_progression)}")
        print(f"🤝 Relationship Flow: {' → '.join(relationship_progression)}")
        
        # Analyze conversation patterns
        flow_analysis = {
            "depth_progression": depth_progression,
            "relationship_progression": relationship_progression, 
            "conversation_depth_score": self._calculate_depth_score(depth_progression),
            "intimacy_development": self._analyze_intimacy_development(relationship_progression),
            "engagement_patterns": self._detect_engagement_patterns(messages),
            "trust_indicators": self._extract_trust_indicators(messages),
            "conversation_velocity": self._calculate_conversation_velocity(messages)
        }
        
        self._display_flow_results(flow_analysis)
        return flow_analysis
    
    def analyze_multi_dimensional_progression(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Demonstrate 6-dimensional trajectory analysis (content, emotion, semantic, relationship, context, personality)
        """
        print(f"\n🎯 6-DIMENSIONAL TRAJECTORY ANALYSIS")
        print("=" * 70)
        
        multi_dimensional_analysis = {
            "content_evolution": self._analyze_content_evolution(messages),
            "emotional_trajectory": self._analyze_emotional_dimension(messages),
            "semantic_clustering": self._analyze_semantic_progression(messages),
            "relationship_dynamics": self._analyze_relationship_dimension(messages),
            "contextual_shifts": self._analyze_context_dimension(messages),
            "personality_emergence": self._analyze_personality_dimension(messages)
        }
        
        self._display_multi_dimensional_results(multi_dimensional_analysis)
        return multi_dimensional_analysis
    
    def _calculate_trajectory_metrics(self, emotions: List[str], valences: List[float]) -> Dict[str, Any]:
        """Calculate trajectory direction and velocity"""
        if len(valences) < 2:
            return {"direction": "stable", "velocity": 0.0}
        
        # Calculate overall direction
        start_avg = sum(valences[:2]) / 2 if len(valences) >= 2 else valences[0]
        end_avg = sum(valences[-2:]) / 2 if len(valences) >= 2 else valences[-1]
        
        direction_change = end_avg - start_avg
        
        if direction_change > 0.5:
            direction = "improving"
        elif direction_change < -0.5:
            direction = "declining"
        else:
            direction = "stable"
        
        # Calculate velocity (rate of change)
        changes = []
        for i in range(1, len(valences)):
            change = valences[i] - valences[i-1]
            changes.append(abs(change))
        
        velocity = sum(changes) / len(changes) if changes else 0.0
        
        return {
            "direction": direction,
            "velocity": velocity,
            "total_change": direction_change
        }
    
    def _detect_emotional_patterns(self, emotions: List[str]) -> List[str]:
        """Detect emotional patterns in the sequence"""
        patterns = []
        
        # Check for emotional arc patterns
        positive_emotions = {'joy', 'excitement', 'gratitude', 'hope', 'love', 'contentment'}
        negative_emotions = {'sadness', 'anxiety', 'anger', 'fear', 'frustration', 'disappointment'}
        
        # Analyze emotional transitions
        transitions = 0
        recovery_count = 0
        
        for i in range(1, len(emotions)):
            prev_emotion = emotions[i-1]
            curr_emotion = emotions[i]
            
            if prev_emotion != curr_emotion:
                transitions += 1
            
            # Check for recovery pattern (negative → positive)
            if prev_emotion in negative_emotions and curr_emotion in positive_emotions:
                recovery_count += 1
        
        if recovery_count >= 2:
            patterns.append("emotional_recovery")
        
        if transitions > len(emotions) * 0.6:
            patterns.append("high_volatility")
        elif transitions < len(emotions) * 0.2:
            patterns.append("emotional_stability")
        
        # Check for specific arc patterns
        if len(emotions) >= 5:
            if emotions[0] in {'neutral'} and emotions[-1] in positive_emotions:
                patterns.append("positive_development")
            if any(e in negative_emotions for e in emotions[1:-1]) and emotions[-1] in positive_emotions:
                patterns.append("overcome_adversity")
        
        return patterns if patterns else ["linear_progression"]
    
    def _calculate_emotional_momentum(self, valences: List[float]) -> str:
        """Calculate emotional momentum type"""
        if len(valences) < 3:
            return "neutral"
        
        recent_changes = []
        for i in range(-3, 0):
            if i + len(valences) > 0:
                change = valences[i] - valences[i-1]
                recent_changes.append(change)
        
        avg_change = sum(recent_changes) / len(recent_changes) if recent_changes else 0.0
        
        if avg_change > 0.3:
            return "positive_momentum"
        elif avg_change < -0.3:
            return "negative_momentum"
        else:
            return "stable_momentum"
    
    def _calculate_emotional_stability(self, valences: List[float]) -> float:
        """Calculate emotional stability score (0.0-1.0)"""
        if len(valences) < 2:
            return 1.0
        
        mean_val = sum(valences) / len(valences)
        variance = sum((x - mean_val) ** 2 for x in valences) / len(valences)
        std_dev = variance ** 0.5
        
        # Convert to stability score (lower std dev = higher stability)
        max_possible_std = 2.0  # Based on emotion valence range
        stability = max(0.0, 1.0 - (std_dev / max_possible_std))
        
        return stability
    
    def _determine_conversation_arc(self, valences: List[float]) -> str:
        """Determine conversation arc type"""
        if len(valences) < 3:
            return "linear"
        
        start = valences[0]
        middle = sum(valences[len(valences)//3:2*len(valences)//3]) / max(1, len(valences)//3)
        end = valences[-1]
        
        if start < middle and middle > end:
            return "peak_and_decline"
        elif start > middle and middle < end:
            return "valley_and_rise"  
        elif start < end:
            return "ascending_arc"
        elif start > end:
            return "descending_arc"
        else:
            return "stable_arc"
    
    def _identify_key_transitions(self, emotions: List[str], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify key emotional transitions with context"""
        transitions = []
        
        for i in range(1, len(emotions)):
            if emotions[i] != emotions[i-1]:
                transition = {
                    "from_emotion": emotions[i-1],
                    "to_emotion": emotions[i],
                    "message_index": i,
                    "message_content": messages[i]["user_message"][:50] + "...",
                    "significance": self._calculate_transition_significance(emotions[i-1], emotions[i])
                }
                transitions.append(transition)
        
        return transitions
    
    def _calculate_transition_significance(self, from_emotion: str, to_emotion: str) -> str:
        """Calculate the significance of an emotional transition"""
        from_valence = self.emotion_valences.get(from_emotion, 0.0)
        to_valence = self.emotion_valences.get(to_emotion, 0.0)
        
        change_magnitude = abs(to_valence - from_valence)
        
        if change_magnitude > 1.5:
            return "major"
        elif change_magnitude > 0.8:
            return "moderate"
        else:
            return "minor"
    
    def _analyze_content_evolution(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how conversation content evolved"""
        topics = []
        for msg in messages:
            content = msg["user_message"].lower()
            if any(word in content for word in ['project', 'creative', 'art']):
                topics.append("creativity")
            elif any(word in content for word in ['anxious', 'doubt', 'struggle']):
                topics.append("self_doubt")
            elif any(word in content for word in ['thank', 'grateful', 'helped']):
                topics.append("gratitude")
            elif any(word in content for word in ['hope', 'go for it', 'confident']):
                topics.append("empowerment")
            else:
                topics.append("general")
        
        return {
            "topic_progression": topics,
            "content_depth_evolution": [len(msg["user_message"]) for msg in messages],
            "thematic_coherence": len(set(topics)) / len(topics) if topics else 1.0
        }
    
    def _analyze_emotional_dimension(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze emotional dimension progression"""
        emotions = [msg["emotion"] for msg in messages]
        return {
            "emotion_sequence": emotions,
            "emotional_complexity": len(set(emotions)),
            "emotional_resilience": self._calculate_resilience_score(emotions)
        }
    
    def _calculate_resilience_score(self, emotions: List[str]) -> float:
        """Calculate emotional resilience based on recovery patterns"""
        negative_emotions = {'sadness', 'anxiety', 'anger', 'fear'}
        positive_emotions = {'joy', 'excitement', 'gratitude', 'hope'}
        
        recoveries = 0
        for i in range(1, len(emotions)):
            if emotions[i-1] in negative_emotions and emotions[i] in positive_emotions:
                recoveries += 1
        
        return recoveries / max(1, len([e for e in emotions if e in negative_emotions]))
    
    def _analyze_semantic_progression(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze semantic clustering dimension"""
        return {
            "semantic_categories": ["creative_goals", "emotional_vulnerability", "self_empowerment"],
            "concept_evolution": "fear_to_confidence",
            "semantic_coherence": 0.85
        }
    
    def _analyze_relationship_dimension(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze relationship dimension progression"""
        relationship_states = [msg["relationship_state"] for msg in messages]
        return {
            "relationship_progression": relationship_states,
            "intimacy_development": "significant_deepening",
            "trust_building_events": 3
        }
    
    def _analyze_context_dimension(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contextual dimension changes"""
        return {
            "conversation_modes": ["casual_chat", "emotional_support", "empowerment_coaching"],
            "context_shifts": 2,
            "situational_awareness": "high"
        }
    
    def _analyze_personality_dimension(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze personality trait emergence"""
        return {
            "personality_traits_revealed": ["creative", "vulnerable", "resilient", "growth_oriented"],
            "character_consistency": 0.92,
            "authentic_expression": "high"
        }
    
    def _calculate_depth_score(self, depth_progression: List[str]) -> float:
        """Calculate conversation depth score"""
        depth_values = {"surface": 0.1, "engaging": 0.3, "personal": 0.6, "intimate": 0.8, "profound": 1.0}
        scores = [depth_values.get(depth, 0.0) for depth in depth_progression]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _analyze_intimacy_development(self, relationship_progression: List[str]) -> str:
        """Analyze how intimacy developed"""
        if "vulnerable_sharing" in relationship_progression and "trust_building" in relationship_progression:
            return "significant_deepening"
        elif len(set(relationship_progression)) > 3:
            return "progressive_development"
        else:
            return "stable_interaction"
    
    def _detect_engagement_patterns(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Detect engagement patterns in conversation"""
        patterns = []
        
        # Check message length progression
        lengths = [len(msg["user_message"]) for msg in messages]
        if any(lengths[i] > lengths[i-1] for i in range(1, len(lengths))):
            patterns.append("increasing_engagement")
        
        # Check depth progression
        depths = [msg["depth"] for msg in messages]
        if "intimate" in depths or "personal" in depths:
            patterns.append("deep_sharing")
        
        return patterns
    
    def _extract_trust_indicators(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract trust indicators from messages"""
        trust_indicators = []
        for msg in messages:
            content = msg["user_message"].lower()
            if "honest" in content or "if i'm being" in content:
                trust_indicators.append("honest_disclosure")
            if "thank" in content or "feels good" in content:
                trust_indicators.append("appreciation_expressed")
            if "struggle" in content or "anxious" in content:
                trust_indicators.append("vulnerability_shared")
        
        return trust_indicators
    
    def _calculate_conversation_velocity(self, messages: List[Dict[str, Any]]) -> str:
        """Calculate conversation velocity"""
        # Simulate time gaps between messages
        if len(messages) < 2:
            return "static"
        
        # In real system, would calculate actual time differences
        avg_response_time = 3.2  # minutes (simulated)
        
        if avg_response_time < 1.0:
            return "rapid"
        elif avg_response_time < 3.0:
            return "engaged"
        else:
            return "thoughtful"
    
    def _display_trajectory_results(self, analysis: Dict[str, Any]):
        """Display trajectory analysis results"""
        print(f"\n📈 TRAJECTORY ANALYSIS RESULTS:")
        print(f"   Direction: {analysis['trajectory_direction']}")
        print(f"   Velocity: {analysis['emotional_velocity']:.3f}")
        print(f"   Momentum: {analysis['emotional_momentum']}")
        print(f"   Stability: {analysis['stability_score']:.3f}")
        print(f"   Arc Type: {analysis['conversation_arc']}")
        print(f"   Patterns: {', '.join(analysis['patterns_detected'])}")
        
        if analysis['key_transitions']:
            print(f"\n🔄 KEY EMOTIONAL TRANSITIONS:")
            for transition in analysis['key_transitions']:
                print(f"   {transition['from_emotion']} → {transition['to_emotion']} "
                     f"({transition['significance']}): {transition['message_content']}")
    
    def _display_flow_results(self, analysis: Dict[str, Any]):
        """Display conversation flow results"""
        print(f"\n📊 FLOW ANALYSIS RESULTS:")
        print(f"   Depth Score: {analysis['conversation_depth_score']:.3f}")
        print(f"   Intimacy Development: {analysis['intimacy_development']}")
        print(f"   Engagement Patterns: {', '.join(analysis['engagement_patterns'])}")
        print(f"   Trust Indicators: {', '.join(analysis['trust_indicators'])}")
        print(f"   Conversation Velocity: {analysis['conversation_velocity']}")
    
    def _display_multi_dimensional_results(self, analysis: Dict[str, Any]):
        """Display 6-dimensional analysis results"""
        print(f"\n🎯 6-DIMENSIONAL ANALYSIS RESULTS:")
        print(f"   Content Evolution: {analysis['content_evolution']['thematic_coherence']:.3f} coherence")
        print(f"   Emotional Resilience: {analysis['emotional_trajectory']['emotional_resilience']:.3f}")
        print(f"   Semantic Evolution: {analysis['semantic_clustering']['concept_evolution']}")
        print(f"   Relationship Growth: {analysis['relationship_dynamics']['intimacy_development']}")
        print(f"   Context Adaptability: {analysis['contextual_shifts']['situational_awareness']}")
        print(f"   Personality Authenticity: {analysis['personality_emergence']['character_consistency']:.3f}")
    
    def run_comprehensive_trajectory_demo(self):
        """
        Run comprehensive demonstration of trajectory analysis capabilities
        """
        print("🎯 WHISPERENGINE MULTI-MESSAGE TRAJECTORY ANALYSIS")
        print("=" * 90)
        print("""
🔍 TRAJECTORY ANALYSIS OVERVIEW:
WhisperEngine analyzes multiple messages to understand:

1. 🎭 EMOTIONAL TRAJECTORY: How emotions evolve over conversation
2. 📊 CONVERSATION FLOW: Depth and engagement progression  
3. 🤝 RELATIONSHIP DYNAMICS: Trust and intimacy development
4. 🎯 6-DIMENSIONAL INTELLIGENCE: Complete contextual understanding

This enables authentic, contextually-aware AI character responses that 
maintain consistency across long conversations while adapting to user needs.
        """)
        
        # Generate sample conversation
        messages = self.simulate_multi_message_conversation()
        
        print(f"\n📝 SAMPLE CONVERSATION SEQUENCE ({len(messages)} messages):")
        for i, msg in enumerate(messages, 1):
            print(f"{i}. [{msg['emotion']}] {msg['user_message']}")
        
        # Analyze trajectory
        emotional_analysis = self.analyze_emotional_trajectory(messages)
        
        # Analyze conversation flow  
        flow_analysis = self.analyze_conversation_flow_patterns(messages)
        
        # Analyze multi-dimensional progression
        multi_dim_analysis = self.analyze_multi_dimensional_progression(messages)
        
        # Show how this impacts AI responses
        self.demonstrate_trajectory_impact_on_responses(emotional_analysis, flow_analysis)
    
    def demonstrate_trajectory_impact_on_responses(self, emotional_analysis: Dict[str, Any], flow_analysis: Dict[str, Any]):
        """
        Show how trajectory analysis impacts AI character responses
        """
        print(f"\n🤖 IMPACT ON AI CHARACTER RESPONSES")
        print("=" * 70)
        
        print(f"""
🎭 EMOTIONAL INTELLIGENCE IMPACT:
   Trajectory: {emotional_analysis['trajectory_direction']} with {emotional_analysis['emotional_momentum']}
   → AI Response Style: Supportive and encouraging, acknowledging growth
   → Memory Weighting: Recent positive emotions get higher retrieval weight
   → Character Consistency: Maintains empathetic personality throughout

📊 CONVERSATION FLOW IMPACT:  
   Depth Score: {flow_analysis['conversation_depth_score']:.3f} (personal/intimate level)
   → AI Response Depth: Matches user's openness level
   → Trust Calibration: Responds to vulnerability with appropriate support
   → Relationship Awareness: Recognizes deepening bond, adjusts intimacy

🎯 6-DIMENSIONAL IMPACT:
   → Content: Maintains thematic coherence around creativity and self-doubt
   → Emotion: Tracks recovery pattern, provides emotionally appropriate support  
   → Semantic: Groups related concepts (creativity, confidence, growth)
   → Relationship: Adapts to trust-building and vulnerability sharing
   → Context: Shifts from casual chat to emotional support to empowerment
   → Personality: Maintains character authenticity while showing growth

🚀 RESULT: More human-like AI that remembers emotional journey, adapts to 
relationship dynamics, and provides contextually intelligent responses
that feel authentic and emotionally supportive.
        """)

def main():
    """Run the trajectory analysis demonstration"""
    demo = TrajectoryAnalysisDemo()
    demo.run_comprehensive_trajectory_demo()

if __name__ == "__main__":
    main()