"""
Emotional Context Switching Detection System
==========================================

Advanced system that detects when users change topics or emotional states
during conversations, enabling more natural and contextually aware responses.

Phase 3: Advanced Intelligence
"""

import logging
import os
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContextSwitchType(Enum):
    """Types of context switches that can be detected"""
    TOPIC_SHIFT = "topic_shift"
    EMOTIONAL_SHIFT = "emotional_shift"
    CONVERSATION_MODE = "conversation_mode"
    URGENCY_CHANGE = "urgency_change"
    INTENT_CHANGE = "intent_change"


class ContextSwitchStrength(Enum):
    """Strength of detected context switch"""
    SUBTLE = "subtle"
    MODERATE = "moderate"
    STRONG = "strong"
    DRAMATIC = "dramatic"


@dataclass
class ContextSwitch:
    """Represents a detected context switch in conversation"""
    
    switch_id: str
    switch_type: ContextSwitchType
    strength: ContextSwitchStrength
    confidence_score: float
    description: str
    evidence: List[str]
    previous_context: Dict[str, Any]
    new_context: Dict[str, Any]
    adaptation_strategy: str
    detected_at: datetime
    metadata: Dict[str, Any]


@dataclass
class ConversationContext:
    """Current conversation context state"""
    
    primary_topic: str
    emotional_state: str
    conversation_mode: str  # casual, support, educational, problem_solving
    urgency_level: float  # 0.0 to 1.0
    intent_category: str  # question, sharing, venting, seeking_help
    engagement_level: float  # 0.0 to 1.0
    context_confidence: float  # 0.0 to 1.0
    established_at: datetime
    last_updated: datetime


class ContextSwitchDetector:
    """
    Advanced context switching detection system using vector analysis
    and emotional trajectory monitoring.
    """
    
    def __init__(self, vector_memory_store=None):
        """Initialize the context switch detector"""
        self.vector_store = vector_memory_store
        
        # Detection thresholds (configurable via environment)
        self.topic_shift_threshold = float(os.getenv("PHASE3_TOPIC_SHIFT_THRESHOLD", "0.4"))
        self.emotional_shift_threshold = float(os.getenv("PHASE3_EMOTIONAL_SHIFT_THRESHOLD", "0.3"))
        self.conversation_mode_threshold = float(os.getenv("PHASE3_CONVERSATION_MODE_THRESHOLD", "0.5"))
        self.urgency_change_threshold = float(os.getenv("PHASE3_URGENCY_CHANGE_THRESHOLD", "0.4"))
        
        # Analysis parameters
        self.max_memories_for_analysis = int(os.getenv("PHASE3_MAX_MEMORIES", "50"))
        self.analysis_timeout = int(os.getenv("PHASE3_ANALYSIS_TIMEOUT", "60"))
        
        # Context state tracking
        self.user_contexts = {}  # user_id -> ConversationContext
        
        # Adaptation strategies
        self.adaptation_strategies = {
            ContextSwitchType.TOPIC_SHIFT: "acknowledge_transition",
            ContextSwitchType.EMOTIONAL_SHIFT: "emotional_validation",
            ContextSwitchType.CONVERSATION_MODE: "mode_adjustment",
            ContextSwitchType.URGENCY_CHANGE: "urgency_adaptation",
            ContextSwitchType.INTENT_CHANGE: "intent_realignment"
        }
        
        logger.info(
            "Context Switch Detector initialized with thresholds: "
            "topic=%s, emotional=%s, mode=%s, urgency=%s",
            self.topic_shift_threshold, self.emotional_shift_threshold,
            self.conversation_mode_threshold, self.urgency_change_threshold
        )
    
    async def detect_context_switches(
        self, 
        user_id: str, 
        new_message: str
    ) -> List[ContextSwitch]:
        """
        Detect all types of context switches in the new message.
        
        Args:
            user_id: User identifier
            new_message: New user message
            message_metadata: Additional message context
            
        Returns:
            List of detected context switches
        """
        logger.debug("Detecting context switches for user %s", user_id)
        
        try:
            # Get current context
            current_context = await self._get_current_context(user_id)
            
            # Analyze different types of context switches
            detected_switches = []
            
            # 1. Topic shift detection
            topic_switch = await self._detect_topic_shift(user_id, new_message, current_context)
            if topic_switch:
                detected_switches.append(topic_switch)
            
            # 2. Emotional shift detection
            emotional_switch = await self._detect_emotional_shift(user_id, current_context)
            if emotional_switch:
                detected_switches.append(emotional_switch)
            
            # 3. Conversation mode change
            mode_switch = await self._detect_conversation_mode_change(user_id, new_message, current_context)
            if mode_switch:
                detected_switches.append(mode_switch)
            
            # 4. Urgency level change
            urgency_switch = await self._detect_urgency_change(user_id, new_message, current_context)
            if urgency_switch:
                detected_switches.append(urgency_switch)
            
            # 5. Intent category change
            intent_switch = await self._detect_intent_change(user_id, new_message, current_context)
            if intent_switch:
                detected_switches.append(intent_switch)
            
            # Update context based on detected switches
            if detected_switches:
                await self._update_context_after_switches(user_id, detected_switches)
            
            logger.debug("Detected %d context switches", len(detected_switches))
            return detected_switches
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error detecting context switches: %s", e)
            return []
    
    async def _detect_topic_shift(
        self, 
        user_id: str, 
        new_message: str, 
        current_context: ConversationContext
    ) -> Optional[ContextSwitch]:
        """Detect topic shifts using vector contradictions and semantic analysis"""
        
        if not self.vector_store:
            return None
        
        try:
            # Use vector store's contradiction detection for topic shifts
            if hasattr(self.vector_store, 'detect_contradictions'):
                contradictions = await self.vector_store.detect_contradictions(
                    new_content=new_message,
                    user_id=user_id,
                    similarity_threshold=self.topic_shift_threshold
                )
            elif hasattr(self.vector_store, 'vector_store') and hasattr(self.vector_store.vector_store, 'detect_contradictions'):
                # Try accessing underlying vector store
                contradictions = await self.vector_store.vector_store.detect_contradictions(
                    new_content=new_message,
                    user_id=user_id,
                    similarity_threshold=self.topic_shift_threshold
                )
            else:
                # Fallback: use semantic similarity for basic topic shift detection
                recent_memories = await self.vector_store.get_conversation_history(
                    user_id=user_id,
                    limit=3
                )
                
                if recent_memories and len(recent_memories) > 0:
                    # Simple topic shift detection based on current vs previous topic
                    previous_topic = current_context.primary_topic
                    new_topic = await self._extract_primary_topic(new_message)
                    
                    if previous_topic != new_topic and previous_topic != "general":
                        # Create mock contradiction for topic shift
                        contradictions = [{
                            'similarity_score': 0.3,  # Assume moderate dissimilarity
                            'content': new_message,
                            'reason': f'Topic change from {previous_topic} to {new_topic}'
                        }]
                    else:
                        contradictions = []
                else:
                    contradictions = []
            
            # Get recent conversation for topic context analysis
            await self.vector_store.search_memories(
                query=current_context.primary_topic,
                user_id=user_id,
                limit=5,
                memory_types=["conversation"]
            )
            
            # Calculate topic shift strength
            if contradictions:
                # Analyze contradiction strength
                avg_dissimilarity = statistics.mean([
                    1.0 - c.get('similarity_score', 0.5) for c in contradictions
                ])
                
                # Determine shift strength
                if avg_dissimilarity > 0.7:
                    strength = ContextSwitchStrength.DRAMATIC
                elif avg_dissimilarity > 0.5:
                    strength = ContextSwitchStrength.STRONG
                elif avg_dissimilarity > 0.3:
                    strength = ContextSwitchStrength.MODERATE
                else:
                    strength = ContextSwitchStrength.SUBTLE
                
                # Extract new topic from message
                new_topic = await self._extract_primary_topic(new_message)
                
                return ContextSwitch(
                    switch_id=f"topic_{user_id}_{int(datetime.now(UTC).timestamp())}",
                    switch_type=ContextSwitchType.TOPIC_SHIFT,
                    strength=strength,
                    confidence_score=avg_dissimilarity,
                    description=f"Topic shift from '{current_context.primary_topic}' to '{new_topic}'",
                    evidence=[f"Vector contradictions found: {len(contradictions)}"],
                    previous_context={"topic": current_context.primary_topic},
                    new_context={"topic": new_topic},
                    adaptation_strategy=self.adaptation_strategies[ContextSwitchType.TOPIC_SHIFT],
                    detected_at=datetime.now(UTC),
                    metadata={
                        "contradictions": contradictions,
                        "dissimilarity_score": avg_dissimilarity
                    }
                )
            
            return None
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error detecting topic shift: %s", e)
            return None
    
    async def _detect_emotional_shift(
        self, 
        user_id: str, 
        current_context: ConversationContext
    ) -> Optional[ContextSwitch]:
        """Detect emotional state changes using trajectory analysis"""
        
        if not self.vector_store:
            return None
        
        try:
            # Get recent emotional trajectory
            recent_memories = await self.vector_store.get_conversation_history(
                user_id=user_id,
                limit=5
            )
            
            # Extract emotional progression
            emotions = []
            for memory in recent_memories:
                metadata = memory.get('metadata', {})
                if metadata.get('role') == 'user':
                    emotional_context = metadata.get('emotional_context', '')
                    if emotional_context:
                        emotions.append(emotional_context)
            
            if len(emotions) < 2:
                return None
            
            # Analyze emotional shift
            current_emotion = emotions[0] if emotions else 'neutral'
            previous_emotion = current_context.emotional_state
            
            # Calculate emotional distance (simplified)
            emotional_distance = self._calculate_emotional_distance(previous_emotion, current_emotion)
            
            if emotional_distance > self.emotional_shift_threshold:
                # Determine shift strength
                if emotional_distance > 0.8:
                    strength = ContextSwitchStrength.DRAMATIC
                elif emotional_distance > 0.6:
                    strength = ContextSwitchStrength.STRONG
                elif emotional_distance > 0.4:
                    strength = ContextSwitchStrength.MODERATE
                else:
                    strength = ContextSwitchStrength.SUBTLE
                
                return ContextSwitch(
                    switch_id=f"emotion_{user_id}_{int(datetime.now(UTC).timestamp())}",
                    switch_type=ContextSwitchType.EMOTIONAL_SHIFT,
                    strength=strength,
                    confidence_score=emotional_distance,
                    description=f"Emotional shift from '{previous_emotion}' to '{current_emotion}'",
                    evidence=[f"Emotional distance: {emotional_distance:.3f}"],
                    previous_context={"emotion": previous_emotion},
                    new_context={"emotion": current_emotion},
                    adaptation_strategy=self.adaptation_strategies[ContextSwitchType.EMOTIONAL_SHIFT],
                    detected_at=datetime.now(UTC),
                    metadata={
                        "emotional_trajectory": emotions,
                        "emotional_distance": emotional_distance
                    }
                )
            
            return None
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error detecting emotional shift: %s", e)
            return None
    
    async def _detect_conversation_mode_change(
        self, 
        user_id: str, 
        new_message: str, 
        current_context: ConversationContext
    ) -> Optional[ContextSwitch]:
        """Detect changes in conversation mode (casual, support, educational, etc.)"""
        
        try:
            # Analyze message for mode indicators
            new_mode = await self._determine_conversation_mode(new_message)
            
            if new_mode != current_context.conversation_mode:
                # Calculate mode change significance
                mode_distance = self._calculate_mode_distance(
                    current_context.conversation_mode, 
                    new_mode
                )
                
                if mode_distance > self.conversation_mode_threshold:
                    return ContextSwitch(
                        switch_id=f"mode_{user_id}_{int(datetime.now(UTC).timestamp())}",
                        switch_type=ContextSwitchType.CONVERSATION_MODE,
                        strength=ContextSwitchStrength.MODERATE,
                        confidence_score=mode_distance,
                        description=f"Mode change from '{current_context.conversation_mode}' to '{new_mode}'",
                        evidence=["Mode indicators detected in message"],
                        previous_context={"mode": current_context.conversation_mode},
                        new_context={"mode": new_mode},
                        adaptation_strategy=self.adaptation_strategies[ContextSwitchType.CONVERSATION_MODE],
                        detected_at=datetime.now(UTC),
                        metadata={"mode_distance": mode_distance}
                    )
            
            return None
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error detecting conversation mode change: %s", e)
            return None
    
    async def _detect_urgency_change(
        self, 
        user_id: str, 
        new_message: str, 
        current_context: ConversationContext
    ) -> Optional[ContextSwitch]:
        """Detect changes in message urgency level"""
        
        try:
            # Analyze message for urgency indicators
            new_urgency = await self._calculate_message_urgency(new_message)
            urgency_change = abs(new_urgency - current_context.urgency_level)
            
            if urgency_change > self.urgency_change_threshold:
                if urgency_change > 0.6:
                    strength = ContextSwitchStrength.STRONG
                elif urgency_change > 0.4:
                    strength = ContextSwitchStrength.MODERATE
                else:
                    strength = ContextSwitchStrength.SUBTLE
                
                return ContextSwitch(
                    switch_id=f"urgency_{user_id}_{int(datetime.now(UTC).timestamp())}",
                    switch_type=ContextSwitchType.URGENCY_CHANGE,
                    strength=strength,
                    confidence_score=urgency_change,
                    description=f"Urgency change from {current_context.urgency_level:.2f} to {new_urgency:.2f}",
                    evidence=[f"Urgency shift detected: {urgency_change:.3f}"],
                    previous_context={"urgency": current_context.urgency_level},
                    new_context={"urgency": new_urgency},
                    adaptation_strategy=self.adaptation_strategies[ContextSwitchType.URGENCY_CHANGE],
                    detected_at=datetime.now(UTC),
                    metadata={"urgency_change": urgency_change}
                )
            
            return None
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error detecting urgency change: %s", e)
            return None
    
    async def _detect_intent_change(
        self, 
        user_id: str, 
        new_message: str, 
        current_context: ConversationContext
    ) -> Optional[ContextSwitch]:
        """Detect changes in user intent category"""
        
        try:
            # Analyze message for intent indicators
            new_intent = await self._determine_intent_category(new_message)
            
            if new_intent != current_context.intent_category:
                return ContextSwitch(
                    switch_id=f"intent_{user_id}_{int(datetime.now(UTC).timestamp())}",
                    switch_type=ContextSwitchType.INTENT_CHANGE,
                    strength=ContextSwitchStrength.MODERATE,
                    confidence_score=0.7,  # Intent changes are typically clear
                    description=f"Intent change from '{current_context.intent_category}' to '{new_intent}'",
                    evidence=["Intent indicators detected"],
                    previous_context={"intent": current_context.intent_category},
                    new_context={"intent": new_intent},
                    adaptation_strategy=self.adaptation_strategies[ContextSwitchType.INTENT_CHANGE],
                    detected_at=datetime.now(UTC),
                    metadata={"intent_change": True}
                )
            
            return None
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error detecting intent change: %s", e)
            return None
    
    async def _get_current_context(self, user_id: str) -> ConversationContext:
        """Get or create current conversation context for user"""
        
        if user_id not in self.user_contexts:
            # Initialize context from recent conversation history
            self.user_contexts[user_id] = await self._initialize_context(user_id)
        
        return self.user_contexts[user_id]
    
    async def _initialize_context(self, user_id: str) -> ConversationContext:
        """Initialize conversation context from recent history"""
        
        try:
            if self.vector_store:
                # Get recent conversation to infer context
                recent_memories = await self.vector_store.get_conversation_history(
                    user_id=user_id,
                    limit=3
                )
                
                if recent_memories:
                    # Extract context from most recent user message
                    user_memory = next(
                        (m for m in recent_memories if m.get('metadata', {}).get('role') == 'user'), 
                        None
                    )
                    
                    if user_memory:
                        metadata = user_memory.get('metadata', {})
                        content = user_memory.get('content', '')
                        
                        return ConversationContext(
                            primary_topic=await self._extract_primary_topic(content),
                            emotional_state=metadata.get('emotional_context', 'neutral'),
                            conversation_mode=await self._determine_conversation_mode(content),
                            urgency_level=await self._calculate_message_urgency(content),
                            intent_category=await self._determine_intent_category(content),
                            engagement_level=0.5,
                            context_confidence=0.6,
                            established_at=datetime.now(UTC),
                            last_updated=datetime.now(UTC)
                        )
            
            # Default context for new users
            return ConversationContext(
                primary_topic="general",
                emotional_state="neutral",
                conversation_mode="casual",
                urgency_level=0.3,
                intent_category="greeting",
                engagement_level=0.5,
                context_confidence=0.3,
                established_at=datetime.now(UTC),
                last_updated=datetime.now(UTC)
            )
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("Error initializing context: %s", e)
            return ConversationContext(
                primary_topic="general",
                emotional_state="neutral", 
                conversation_mode="casual",
                urgency_level=0.3,
                intent_category="general",
                engagement_level=0.5,
                context_confidence=0.1,
                established_at=datetime.now(UTC),
                last_updated=datetime.now(UTC)
            )
    
    # Helper methods for analysis
    async def _extract_primary_topic(self, message: str) -> str:
        """Extract primary topic from message"""
        # Simplified topic extraction - could be enhanced with NLP
        message_lower = message.lower()
        
        # Topic keywords mapping
        topic_keywords = {
            "technology": ["ai", "computer", "software", "programming", "tech"],
            "health": ["health", "medicine", "doctor", "symptoms", "medical"],
            "work": ["job", "work", "career", "office", "colleague", "boss"],
            "family": ["family", "parent", "child", "sibling", "relative"],
            "relationships": ["relationship", "friend", "partner", "dating"],
            "education": ["school", "college", "study", "exam", "learn"],
            "hobbies": ["hobby", "game", "music", "art", "sport", "fun"],
            "travel": ["travel", "trip", "vacation", "country", "visit"],
            "food": ["food", "eat", "cook", "restaurant", "recipe"],
            "personal": ["feel", "think", "personal", "myself", "me"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic
        
        return "general"
    
    async def _determine_conversation_mode(self, message: str) -> str:
        """Determine conversation mode from message"""
        message_lower = message.lower()
        
        # Mode indicators
        if any(word in message_lower for word in ["help", "problem", "issue", "trouble", "stuck"]):
            return "problem_solving"
        elif any(word in message_lower for word in ["sad", "upset", "worried", "anxious", "depressed"]):
            return "support"
        elif any(word in message_lower for word in ["learn", "explain", "how", "what", "why", "teach"]):
            return "educational"
        elif any(word in message_lower for word in ["hi", "hello", "hey", "good", "thanks"]):
            return "casual"
        else:
            return "casual"
    
    async def _calculate_message_urgency(self, message: str) -> float:
        """Calculate urgency level of message (0.0 to 1.0)"""
        message_lower = message.lower()
        urgency_score = 0.3  # baseline
        
        # Urgency indicators
        high_urgency = ["urgent", "emergency", "asap", "immediately", "crisis", "help!", "now"]
        medium_urgency = ["soon", "important", "quickly", "need", "problem"]
        low_urgency = ["whenever", "maybe", "sometime", "eventually"]
        
        if any(word in message_lower for word in high_urgency):
            urgency_score += 0.6
        elif any(word in message_lower for word in medium_urgency):
            urgency_score += 0.3
        elif any(word in message_lower for word in low_urgency):
            urgency_score -= 0.2
        
        # Punctuation indicators
        if "!" in message:
            urgency_score += 0.2
        if "??" in message or "!!!" in message:
            urgency_score += 0.3
        
        return min(1.0, max(0.0, urgency_score))
    
    async def _determine_intent_category(self, message: str) -> str:
        """Determine user intent category"""
        message_lower = message.lower()
        
        if message_lower.endswith("?") or any(word in message_lower for word in ["what", "how", "why", "when", "where"]):
            return "question"
        elif any(word in message_lower for word in ["help", "assist", "support", "advice"]):
            return "seeking_help"
        elif any(word in message_lower for word in ["feel", "think", "believe", "experience"]):
            return "sharing"
        elif any(word in message_lower for word in ["frustrated", "angry", "upset", "annoyed"]):
            return "venting"
        else:
            return "general"
    
    def _calculate_emotional_distance(self, emotion1: str, emotion2: str) -> float:
        """Calculate distance between two emotional states"""
        # Simplified emotional distance calculation
        emotion_map = {
            "very_positive": 1.0,
            "positive": 0.7,
            "neutral": 0.0,
            "negative": -0.7,
            "very_negative": -1.0,
            "anxious": -0.5,
            "contemplative": 0.2
        }
        
        val1 = emotion_map.get(emotion1, 0.0)
        val2 = emotion_map.get(emotion2, 0.0)
        
        return abs(val1 - val2) / 2.0  # Normalize to 0-1
    
    def _calculate_mode_distance(self, mode1: str, mode2: str) -> float:
        """Calculate distance between conversation modes"""
        # Mode compatibility matrix (lower = more similar)
        mode_distances = {
            ("casual", "educational"): 0.3,
            ("casual", "support"): 0.5,
            ("casual", "problem_solving"): 0.6,
            ("educational", "support"): 0.4,
            ("educational", "problem_solving"): 0.2,
            ("support", "problem_solving"): 0.3
        }
        
        pair = (mode1, mode2) if mode1 <= mode2 else (mode2, mode1)
        return mode_distances.get(pair, 0.8)  # Default high distance for unknown pairs
    
    async def _update_context_after_switches(
        self, 
        user_id: str, 
        switches: List[ContextSwitch]
    ):
        """Update conversation context based on detected switches"""
        
        context = self.user_contexts[user_id]
        
        for switch in switches:
            new_context = switch.new_context
            
            if switch.switch_type == ContextSwitchType.TOPIC_SHIFT:
                context.primary_topic = new_context.get("topic", context.primary_topic)
            elif switch.switch_type == ContextSwitchType.EMOTIONAL_SHIFT:
                context.emotional_state = new_context.get("emotion", context.emotional_state)
            elif switch.switch_type == ContextSwitchType.CONVERSATION_MODE:
                context.conversation_mode = new_context.get("mode", context.conversation_mode)
            elif switch.switch_type == ContextSwitchType.URGENCY_CHANGE:
                context.urgency_level = new_context.get("urgency", context.urgency_level)
            elif switch.switch_type == ContextSwitchType.INTENT_CHANGE:
                context.intent_category = new_context.get("intent", context.intent_category)
        
        context.last_updated = datetime.now(UTC)
        context.context_confidence = min(1.0, context.context_confidence + 0.1)  # Increase confidence
    
    def get_adaptation_strategy(self, switch: ContextSwitch) -> str:
        """Get recommended adaptation strategy for a context switch"""
        return switch.adaptation_strategy
    
    async def get_context_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of current conversation context"""
        context = await self._get_current_context(user_id)
        
        return {
            "user_id": user_id,
            "primary_topic": context.primary_topic,
            "emotional_state": context.emotional_state,
            "conversation_mode": context.conversation_mode,
            "urgency_level": context.urgency_level,
            "intent_category": context.intent_category,
            "engagement_level": context.engagement_level,
            "context_confidence": context.context_confidence,
            "last_updated": context.last_updated.isoformat()
        }