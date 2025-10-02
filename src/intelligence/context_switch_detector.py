"""
Emotional Context Switching Detection System
==========================================

Advanced system that detects when users change topics or emotional states
during conversations, enabling more natural and contextually aware responses.

Phase 3: Advanced Intelligence
"""

import logging
import os
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
        logger.info("🔍🔍🔍 ULTRA EXPLICIT DEBUG: Starting context switch detection for user %s", user_id)
        logger.info("🔍🔍🔍 ULTRA EXPLICIT DEBUG: New message: '%s'", new_message[:100])
        
        try:
            # Get current context
            current_context = await self._get_current_context(user_id)
            logger.info("🔍🔍🔍 ULTRA EXPLICIT DEBUG: Current context primary_topic: %s", 
                        current_context.primary_topic if current_context else "None")
            
            # Analyze different types of context switches
            detected_switches = []
            
            # 1. Topic shift detection
            logger.info("🔍🔍🔍 ULTRA EXPLICIT DEBUG: Starting topic shift detection...")
            topic_switch = await self._detect_topic_shift(user_id, new_message, current_context)
            if topic_switch:
                logger.info("🔍🔍🔍 CONTEXT SWITCH DETECTED: Topic shift - %s", topic_switch.description)
                detected_switches.append(topic_switch)
            else:
                logger.info("🔍🔍🔍 ULTRA EXPLICIT DEBUG: No topic shift detected")
            
            # 2. Emotional shift detection
            logger.debug("🔍 CONTEXT SWITCH DEBUG: Starting emotional shift detection...")
            emotional_switch = await self._detect_emotional_shift(user_id, current_context)
            if emotional_switch:
                logger.info("🔍 CONTEXT SWITCH DETECTED: Emotional shift - %s", emotional_switch.description)
                detected_switches.append(emotional_switch)
            
            # 3. Conversation mode change
            logger.debug("🔍 CONTEXT SWITCH DEBUG: Starting conversation mode detection...")
            mode_switch = await self._detect_conversation_mode_change(user_id, new_message, current_context)
            if mode_switch:
                logger.info("🔍 CONTEXT SWITCH DETECTED: Mode change - %s", mode_switch.description)
                detected_switches.append(mode_switch)
            
            # 4. Urgency level change
            logger.debug("🔍 CONTEXT SWITCH DEBUG: Starting urgency detection...")
            urgency_switch = await self._detect_urgency_change(user_id, new_message, current_context)
            if urgency_switch:
                logger.info("🔍 CONTEXT SWITCH DETECTED: Urgency change - %s", urgency_switch.description)
                detected_switches.append(urgency_switch)
            
            # 5. Intent category change
            logger.debug("🔍 CONTEXT SWITCH DEBUG: Starting intent detection...")
            intent_switch = await self._detect_intent_change(user_id, new_message, current_context)
            if intent_switch:
                logger.info("🔍 CONTEXT SWITCH DETECTED: Intent change - %s", intent_switch.description)
                detected_switches.append(intent_switch)
            
            # Update context based on detected switches
            if detected_switches:
                logger.info("🔍 CONTEXT SWITCH SUMMARY: %d switches detected, updating context", len(detected_switches))
                await self._update_context_after_switches(user_id, detected_switches)
            else:
                logger.debug("🔍 CONTEXT SWITCH DEBUG: No context switches detected")
            
            logger.info("🔍 CONTEXT SWITCH FINAL: Detected %d context switches for user %s", 
                       len(detected_switches), user_id)
            return detected_switches
            
        except (AttributeError, ValueError, KeyError) as e:
            logger.error("🔍 CONTEXT SWITCH ERROR: Error detecting context switches: %s", e)
            return []
    
    async def _detect_topic_shift(
        self, 
        user_id: str, 
        new_message: str, 
        current_context: ConversationContext
    ) -> Optional[ContextSwitch]:
        """Detect topic shifts using vector contradictions and semantic analysis"""
        
        logger.debug("🔍 TOPIC SHIFT DEBUG: Starting topic shift detection for user %s", user_id)
        logger.debug("🔍 TOPIC SHIFT DEBUG: Vector store check - has detect_contradictions? %s", 
                    hasattr(self.vector_store, 'detect_contradictions'))
        
        logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Entered _detect_topic_shift method")
        
        if not self.vector_store:
            logger.warning("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: No vector store available")
            return None
        else:
            logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Vector store is available")
        
        # Extract the topic from the new message
        new_topic = await self._extract_primary_topic(new_message)
        logger.info(f"🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: New topic detected: '{new_topic}', current topic: '{current_context.primary_topic}'")
        
        # Log threshold values
        logger.info(f"🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Using threshold value: {self.topic_shift_threshold}")
        
        # 1. First attempt: Direct topic extraction for clear topic comparison
        if (current_context.primary_topic != "general" and 
            new_topic != current_context.primary_topic and
            new_topic != "general"):
            
            logger.info("🔍 TOPIC SHIFT FOUND: Direct topic change from %s to %s", 
                       current_context.primary_topic, new_topic)
            
            # Create topic shift result with correct parameter format
            now = datetime.now(UTC)
            return ContextSwitch(
                switch_id=f"topic_{user_id}_{int(now.timestamp())}",
                switch_type=ContextSwitchType.TOPIC_SHIFT,
                strength=ContextSwitchStrength.STRONG,
                confidence_score=0.85,
                description=f"Topic shift from {current_context.primary_topic} to {new_topic}",
                evidence=[new_message[:100]],
                previous_context={"primary_topic": current_context.primary_topic},
                new_context={"primary_topic": new_topic},
                adaptation_strategy="acknowledge_topic_change",
                detected_at=now,
                metadata={"user_id": user_id}
            )
        
        # 2. Use contradiction detection if direct comparison didn't work
        contradictions = None
        try:
            logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Starting contradiction detection")
            if hasattr(self.vector_store, 'detect_contradictions'):
                logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Vector store has detect_contradictions method")
                
                # Call detect_contradictions with explicit logging
                logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Calling detect_contradictions with threshold %s", 
                           self.topic_shift_threshold)
                
                contradictions = await self.vector_store.detect_contradictions(
                    new_content=new_message,
                    user_id=user_id,
                    similarity_threshold=self.topic_shift_threshold
                )
                
                logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Retrieved contradictions for '%s': %d contradictions found", 
                            new_message[:100], len(contradictions) if contradictions else 0)
                
                # Log the first contradiction for debugging
                if contradictions and len(contradictions) > 0:
                    logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Contradiction found: %s", str(contradictions[0]))
                else:
                    logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: No contradictions found")
            else:
                logger.info("🔍🔍🔍 TOPIC SHIFT ULTRA DEBUG: Vector store does NOT have detect_contradictions method")
            
            # Process contradictions if found
            if contradictions and len(contradictions) > 0:
                # Get the most significant contradiction
                top_contradiction = contradictions[0]
                
                # Extract topics from contradiction
                previous_topic = await self._extract_primary_topic(top_contradiction.get('content', ''))
                
                # Calculate a dissimilarity score (1.0 - similarity)
                similarity = float(top_contradiction.get('similarity_score', 0.5))
                dissimilarity = 1.0 - similarity
                
                logger.debug("🔍 TOPIC SHIFT DEBUG: Detected topic shift from '%s' to '%s'. Average dissimilarity: %.2f, strength: %s",
                            previous_topic, new_topic, dissimilarity, 
                            "strong" if dissimilarity > 0.4 else "moderate")
                
                # Create topic shift result with correct parameter format
                now = datetime.now(UTC)
                return ContextSwitch(
                    switch_id=f"topic_{user_id}_{int(now.timestamp())}",
                    switch_type=ContextSwitchType.TOPIC_SHIFT,
                    strength=ContextSwitchStrength.MODERATE if dissimilarity < 0.4 else ContextSwitchStrength.STRONG,
                    confidence_score=dissimilarity * 0.8 + 0.2,  # Scale to 0.2-1.0 range
                    description=f"Topic shift detected with {dissimilarity:.2f} dissimilarity",
                    evidence=[top_contradiction.get('content', 'No content')[:100]],
                    previous_context={"primary_topic": previous_topic},
                    new_context={"primary_topic": new_topic},
                    adaptation_strategy="acknowledge_topic_change",
                    detected_at=now,
                    metadata={"user_id": user_id}
                )
        except (AttributeError, ValueError, KeyError, IndexError) as e:
            logger.error("Error in contradiction detection: %s", str(e), exc_info=True)
        
        # 3. Fallback: use conversation history for basic topic shift detection
        try:
            # Get recent conversation history
            recent_memories = await self.vector_store.get_conversation_history(
                user_id=user_id,
                limit=5
            )
            
            if recent_memories and len(recent_memories) > 0:
                # Compute semantic similarity
                last_topics = []
                for memory in recent_memories:
                    if isinstance(memory, dict) and 'content' in memory:
                        last_topic = await self._extract_primary_topic(memory['content'])
                        if last_topic != "general":
                            last_topics.append(last_topic)
                
                # If we have previous topics, compare with current
                if last_topics and new_topic not in last_topics and new_topic != "general":
                    last_primary_topic = last_topics[0] if last_topics else "general"
                    
                    logger.debug("🔍 TOPIC SHIFT DEBUG: Detected topic shift from '%s' to '%s' using fallback method", 
                                last_primary_topic, new_topic)
                    
                    # Create topic shift result
                    now = datetime.now(UTC)
                    return ContextSwitch(
                        switch_id=f"topic_{user_id}_{int(now.timestamp())}",
                        switch_type=ContextSwitchType.TOPIC_SHIFT,
                        strength=ContextSwitchStrength.MODERATE,
                        confidence_score=0.6,  # Medium confidence
                        description=f"Topic shift from {last_primary_topic} to {new_topic} (fallback detection)",
                        evidence=[],
                        previous_context={"primary_topic": last_primary_topic},
                        new_context={"primary_topic": new_topic},
                        adaptation_strategy="acknowledge_topic_change",
                        detected_at=now,
                        metadata={"user_id": user_id, "detection_method": "fallback"}
                    )
        except (AttributeError, ValueError, KeyError, IndexError) as e:
            logger.error("Error in fallback topic detection: %s", str(e), exc_info=True)
        
        # No topic shift detected
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
        
        logger.debug("🔍 CONTEXT INIT DEBUG: Initializing context for user %s", user_id)
        
        try:
            if self.vector_store:
                logger.debug("🔍 CONTEXT INIT DEBUG: Vector store available, fetching recent conversation")
                # Get recent conversation to infer context
                recent_memories = await self.vector_store.get_conversation_history(
                    user_id=user_id,
                    limit=3
                )
                
                logger.debug("🔍 CONTEXT INIT DEBUG: Retrieved %d recent memories", 
                           len(recent_memories) if recent_memories else 0)
                
                if recent_memories:
                    # Extract context from most recent user message
                    user_memory = None
                    for memory in recent_memories:
                        # Handle different possible memory formats
                        metadata = memory.get('metadata', {})
                        role = metadata.get('role') or metadata.get('message_type') or metadata.get('speaker_type')
                        
                        if role == 'user' or role == 'human':
                            user_memory = memory
                            break
                    
                    logger.debug("🔍 CONTEXT INIT DEBUG: Found user memory: %s", bool(user_memory))
                    
                    if user_memory:
                        metadata = user_memory.get('metadata', {})
                        content = user_memory.get('content', '')
                        
                        logger.debug("🔍 CONTEXT INIT DEBUG: User memory content preview: %s", content[:100])
                        
                        # Extract topic with fallback
                        primary_topic = await self._extract_primary_topic(content)
                        logger.debug("🔍 CONTEXT INIT DEBUG: Extracted primary topic: %s", primary_topic)
                        
                        return ConversationContext(
                            primary_topic=primary_topic,
                            emotional_state=metadata.get('emotional_context', 'neutral'),
                            conversation_mode=await self._determine_conversation_mode(content),
                            urgency_level=await self._calculate_message_urgency(content),
                            intent_category=await self._determine_intent_category(content),
                            engagement_level=0.5,
                            context_confidence=0.6,
                            established_at=datetime.now(UTC),
                            last_updated=datetime.now(UTC)
                        )
                    else:
                        logger.debug("🔍 CONTEXT INIT DEBUG: No user memory found in recent history")
                else:
                    logger.debug("🔍 CONTEXT INIT DEBUG: No recent memories available")
            else:
                logger.warning("🔍 CONTEXT INIT DEBUG: No vector store available")
            
            # Default context for new users
            logger.debug("🔍 CONTEXT INIT DEBUG: Using default context")
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
            logger.error("🔍 CONTEXT INIT ERROR: Error initializing context: %s", e)
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
        """
        Extract primary topic from message using intelligent analysis.
        
        This method provides basic topic categorization while maintaining
        compatibility with existing code. For production use, consider 
        upgrading to vector-based semantic topic analysis.
        """
        if not message or not message.strip():
            return "general"
        
        message_lower = message.lower()
        logger.info("🔍🔍🔍 TOPIC EXTRACTION: Analyzing message for topic: '%s'", message_lower[:50])
        
        # Enhanced topic categorization with broader categories for better detection
        
        # Topic categories with keyword lists
        topic_categories = {
            "inquiry": ["?", "who", "what", "when", "where", "why", "how", "which", "can you", "could you"],
            "emotional": ["feel", "emotion", "mood", "sad", "happy", "angry", "excited", "nervous", "anxious", 
                         "love", "hate", "like", "dislike", "afraid", "scared", "worried", "glad"],
            "professional": ["work", "job", "career", "office", "business", "company", "interview", "resume", 
                           "salary", "boss", "colleague", "project", "meeting"],
            "educational": ["learn", "study", "school", "college", "university", "class", "course", "teacher", 
                          "student", "homework", "assignment", "degree", "education", "knowledge"],
            "health": ["health", "doctor", "medical", "hospital", "sick", "pain", "medicine", "disease", 
                      "injury", "fitness", "diet", "exercise", "weight", "symptom"],
            "technology": ["computer", "software", "hardware", "internet", "website", "app", "program", 
                         "code", "digital", "technology", "online", "mobile", "device", "smartphone"],
            "entertainment": ["movie", "tv", "show", "music", "game", "play", "book", "read", "watch", 
                            "listen", "hobby", "fun", "entertainment", "sport", "actor", "artist"],
            "food": ["food", "eat", "drink", "restaurant", "recipe", "cooking", "meal", "breakfast", 
                   "lunch", "dinner", "snack", "taste", "flavor", "kitchen"],
            "travel": ["travel", "trip", "vacation", "visit", "country", "city", "flight", "hotel", 
                     "tourism", "destination", "journey", "abroad", "explore"],
            "personal": ["family", "friend", "relationship", "marriage", "partner", "child", "parent", 
                       "home", "house", "life", "personal", "private", "birthday", "celebration"]
        }
        
        # Check for each category
        for topic, keywords in topic_categories.items():
            if any(keyword in message_lower for keyword in keywords):
                logger.info("🔍🔍🔍 TOPIC EXTRACTION: Detected topic '%s' from keywords", topic)
                return topic
                
        # Check for question mark (common case)
        if "?" in message:
            logger.info("🔍🔍🔍 TOPIC EXTRACTION: Detected 'inquiry' from question mark")
            return "inquiry"
            
        # Length-based categorization as fallback
        if len(message.split()) > 30:
            logger.info("🔍🔍🔍 TOPIC EXTRACTION: Detected 'detailed_discussion' based on length")
            return "detailed_discussion"
            
        # Final fallback
        logger.info("🔍🔍🔍 TOPIC EXTRACTION: No specific topic detected, returning 'general'")
        return "general"
    
    async def _determine_conversation_mode(self, message: str) -> str:
        """
        Determine conversation mode from message using structural analysis.
        
        This method provides basic mode detection while reducing dependency 
        on hardcoded keyword lists. For production use, consider upgrading 
        to LLM-based mode detection for better accuracy.
        """
        if not message or not message.strip():
            return "casual"
        
        message_lower = message.lower()
        
        # Use structural and contextual indicators
        if "?" in message:
            return "educational"  # Questions indicate learning/inquiry
        elif "!" in message or message.isupper():
            return "support"  # Exclamation or caps may indicate urgency/emotion
        elif any(word in message_lower for word in ["help", "problem", "stuck"]):
            return "problem_solving"
        elif any(word in message_lower for word in ["sad", "worried", "upset"]):
            return "support"
        elif any(word in message_lower for word in ["thanks", "thank", "appreciate"]):
            return "casual"  # Gratitude indicates casual conversation
        else:
            return "casual"
    
    async def _calculate_message_urgency(self, message: str) -> float:
        """
        Calculate urgency level of message (0.0 to 1.0) using structural indicators.
        
        This method reduces dependency on hardcoded keyword lists while maintaining
        urgency detection capabilities. For production use, consider upgrading 
        to LLM-based urgency analysis for better accuracy.
        """
        if not message or not message.strip():
            return 0.3  # baseline
        
        urgency_score = 0.3  # baseline
        
        # Structural urgency indicators
        exclamation_count = message.count('!')
        question_count = message.count('?')
        caps_words = sum(1 for word in message.split() if word.isupper() and len(word) > 1)
        
        # Punctuation-based urgency
        if exclamation_count >= 3:
            urgency_score += 0.5  # Multiple exclamations indicate high urgency
        elif exclamation_count >= 1:
            urgency_score += 0.2
        
        if question_count >= 2:
            urgency_score += 0.3  # Multiple questions may indicate confusion/urgency
        
        # Caps lock usage indicates urgency or strong emotion
        if caps_words > 0:
            urgency_score += min(0.4, caps_words * 0.1)
        
        # Message length and timing can indicate urgency
        if len(message) < 20 and exclamation_count > 0:
            urgency_score += 0.2  # Short urgent messages
        
        # Explicit urgency words (minimal set)
        if any(word in message.lower() for word in ["urgent", "emergency", "asap", "help!"]):
            urgency_score += 0.6
        elif any(word in message.lower() for word in ["need", "problem", "issue"]):
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