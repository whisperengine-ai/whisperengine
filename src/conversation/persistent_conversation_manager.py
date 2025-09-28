"""
Persistent Conversation State Manager for WhisperEngine

Unifies conversation flow management by tracking:
1. Unanswered follow-up questions (persistent until resolved)
2. Topic transitions and coherence 
3. Conversation stagnation and steering
4. User engagement patterns

This bridges the gap between WhisperEngine's sophisticated conversation engines
and persistent question tracking for improved conversation continuity.
"""

import logging
import random
import statistics
import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any

# Import PersonalityDimension for personality profiler integration
try:
    from src.intelligence.dynamic_personality_profiler import PersonalityDimension
except ImportError:
    # Fallback if personality profiler not available
    PersonalityDimension = None

# Vector-native integrations with existing WhisperEngine systems
try:
    from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
    VECTOR_EMOTION_AVAILABLE = True
except ImportError:
    VECTOR_EMOTION_AVAILABLE = False

try:
    from src.intelligence.dynamic_personality_profiler import DynamicPersonalityProfiler
    PERSONALITY_PROFILER_AVAILABLE = True
except ImportError:
    PERSONALITY_PROFILER_AVAILABLE = False

logger = logging.getLogger(__name__)


class QuestionPriority(Enum):
    """Priority levels for pending questions"""
    LOW = "low"           # Casual follow-up, can be dropped if topic changes significantly
    MEDIUM = "medium"     # Important clarification, gentle persistence 
    HIGH = "high"         # Critical question, strong persistence needed
    URGENT = "urgent"     # Must be answered, blocks conversation flow


class QuestionType(Enum):
    """Categories of questions for different handling strategies"""
    CLARIFICATION = "clarification"     # "What did you mean by...?"
    FOLLOWUP = "followup"              # "Tell me more about..."
    PERSONAL = "personal"              # "How did that make you feel?"
    FACTUAL = "factual"               # "When did that happen?"
    OPINION = "opinion"               # "What's your favorite...?"
    CHOICE = "choice"                 # "Would you prefer A or B?"


class ConversationIntimacy(Enum):
    """Relationship intimacy levels for appropriate question depth"""
    STRANGER = "stranger"              # First few interactions
    GETTING_ACQUAINTED = "getting_acquainted"  # First few days
    BUILDING_RAPPORT = "building_rapport"      # 1-2 weeks
    CLOSE_FRIEND = "close_friend"             # 2+ weeks, many interactions
    INTIMATE = "intimate"                     # Long-term relationship


class ConversationRhythm(Enum):
    """Conversation flow states for timing decisions"""
    INTENSE_DISCUSSION = "intense_discussion"  # Don't interrupt
    NATURAL_FLOW = "natural_flow"             # Standard engagement
    CASUAL_CHAT = "casual_chat"               # Light conversation
    WINDING_DOWN = "winding_down"             # Conversation ending
    TOPIC_TRANSITION = "topic_transition"     # Perfect for new questions


@dataclass
class PendingQuestion:
    """A bot question waiting for user response"""
    
    question_id: str
    question_text: str
    question_type: QuestionType
    priority: QuestionPriority
    
    # Context
    original_topic: str
    related_topics: List[str] = field(default_factory=list)
    user_context: str = ""  # What user said that prompted this question
    
    # Timing and persistence
    asked_at: datetime = field(default_factory=datetime.now)
    last_reminded_at: Optional[datetime] = None
    reminder_count: int = 0
    max_reminders: int = 2
    
    # Follow-up strategies
    gentle_reminders: List[str] = field(default_factory=list)
    natural_callbacks: List[str] = field(default_factory=list)
    
    # Resolution tracking  
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_quality: Optional[float] = None  # How well was it answered (0.0-1.0)


@dataclass
class ConversationState:
    """Current state of conversation with user"""
    
    user_id: str
    
    # Active conversation tracking
    current_topic: Optional[str] = None
    topic_depth: int = 0  # How deep into current topic (0=surface, 5=very deep)
    topic_started_at: Optional[datetime] = None
    topic_engagement_score: float = 0.5  # User engagement with current topic
    
    # Pending questions management
    pending_questions: List[PendingQuestion] = field(default_factory=list)
    total_questions_asked: int = 0
    total_questions_answered: int = 0
    
    # Topic transition tracking
    recent_topics: List[str] = field(default_factory=list)  # Last 5 topics
    topic_transition_abruptness: float = 0.0  # 0.0=smooth, 1.0=jarring
    
    # Stagnation detection
    messages_since_topic_change: int = 0
    repetitive_patterns: List[str] = field(default_factory=list)
    stagnation_risk_score: float = 0.0
    
    # User conversation patterns
    typical_topic_duration: float = 10.0  # minutes
    question_answer_ratio: float = 0.5  # User questions vs answers
    topic_jumping_tendency: float = 0.3  # How often user changes topics abruptly
    
    # Human-like conversation enhancements
    intimacy_level: ConversationIntimacy = ConversationIntimacy.GETTING_ACQUAINTED
    current_rhythm: ConversationRhythm = ConversationRhythm.NATURAL_FLOW
    emotional_state: str = "neutral"  # Current detected user emotion
    conversation_intensity: float = 0.5  # 0.0=casual, 1.0=intense
    days_known: int = 0  # Days since first interaction
    total_interactions: int = 0  # Total message exchanges
    personality_type: str = "default"  # Bot personality for personalized responses


class PersistentConversationManager:
    """
    Vector-Native Persistent Conversation Manager
    
    Integrates with WhisperEngine's existing vector-based systems:
    - EnhancedVectorEmotionAnalyzer for sophisticated emotion detection
    - DynamicPersonalityProfiler for real-time personality adaptation
    - Vector memory system for conversation state storage
    - ProactiveEngagementEngine for conversation flow
    """
    
    def __init__(self, memory_manager: Any, bot_core=None):
        self.memory_manager = memory_manager
        self.bot_core = bot_core
        self.user_states: Dict[str, ConversationState] = {}
        # Add concurrency protection for user states
        self._state_locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        
        # Integration with existing WhisperEngine vector systems
        self.emotion_analyzer = None
        self.personality_profiler = None
        
        # Initialize vector intelligence components from bot_core if available
        if bot_core:
            # Access EnhancedVectorEmotionAnalyzer (stored as hybrid_emotion_analyzer)
            self.emotion_analyzer = getattr(bot_core, 'hybrid_emotion_analyzer', None)
            # Access DynamicPersonalityProfiler  
            self.personality_profiler = getattr(bot_core, 'dynamic_personality_profiler', None)
            
            logger.info("🤖 Vector Intelligence Integration: emotion_analyzer=%s, personality_profiler=%s", 
                       self.emotion_analyzer is not None, self.personality_profiler is not None)
        
        if bot_core:
            # Use existing vector-based emotion analysis
            self.emotion_analyzer = getattr(bot_core, 'enhanced_vector_emotion_analyzer', None)
            # Use existing personality profiler
            self.personality_profiler = getattr(bot_core, 'dynamic_personality_profiler', None)
        
        # Configuration
        self.max_pending_questions = 3  # Don't overwhelm users
        self.question_timeout_hours = 24  # Auto-resolve after 24h
        self.gentle_reminder_delay_minutes = 15  # Wait before first reminder
        
        logger.info("🗣️ Vector-Native Persistent Conversation Manager initialized")
    
    async def track_bot_question(
        self, 
        user_id: str, 
        question_text: str, 
        question_type: QuestionType,
        priority: QuestionPriority = QuestionPriority.MEDIUM,
        current_topic: Optional[str] = None,
        user_context: str = ""
    ) -> str:
        """
        Track a question asked by the bot for future follow-up.
        
        Returns:
            question_id for tracking
        """
        # Get or create conversation state
        state = await self._get_conversation_state(user_id)
        
        # Generate unique question ID
        question_id = f"q_{user_id}_{datetime.now().timestamp()}"
        
        # Create pending question
        pending_question = PendingQuestion(
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            priority=priority,
            original_topic=current_topic or state.current_topic or "general",
            user_context=user_context,
            gentle_reminders=await self._generate_gentle_reminders_vector_native(question_text, question_type, user_id),
            natural_callbacks=self._generate_natural_callbacks(question_text, current_topic)
        )
        
        # Add to pending questions (limit to max)
        if len(state.pending_questions) >= self.max_pending_questions:
            # Remove oldest low-priority question
            state.pending_questions = [q for q in state.pending_questions 
                                      if q.priority != QuestionPriority.LOW][:self.max_pending_questions-1]
        
        state.pending_questions.append(pending_question)
        state.total_questions_asked += 1
        
        # Persist state
        await self._save_conversation_state(user_id, state)
        
        logger.info(f"📝 Tracked question for {user_id}: {question_text[:50]}...")
        return question_id
    
    async def process_user_response(
        self, 
        user_id: str, 
        user_message: str,
        current_topic: Optional[str] = None,
        emotional_state: str = "neutral",
        response_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Vector-native user response processing using existing WhisperEngine intelligence.
        
        Returns:
            Dict with answered questions, conversation guidance, and vector-based insights
        """
        state = await self._get_conversation_state(user_id)
        
        # Use existing vector systems for intelligence instead of duplicating
        vector_insights = await self._get_vector_intelligence_insights(user_id, user_message, emotional_state)
        
        # Update state with vector-based intelligence
        state.total_interactions += 1
        state.emotional_state = emotional_state
        
        if not state.pending_questions:
            return {
                "answered_questions": [], 
                "guidance": None, 
                "vector_insights": vector_insights,
                "integration_status": "using_existing_vector_systems"
            }
        
        # Check if user response answers any pending questions using vector similarity
        answered_questions = []
        remaining_questions = []
        
        for question in state.pending_questions:
            if await self._is_question_answered_vector(question, user_message, current_topic):
                # Mark as resolved
                question.is_resolved = True
                question.resolved_at = datetime.now()
                question.resolution_quality = await self._evaluate_answer_quality(
                    question, user_message
                )
                answered_questions.append(question)
                state.total_questions_answered += 1
                
                logger.info("✅ Question resolved for %s: %s...", user_id, question.question_text[:30])
            else:
                remaining_questions.append(question)
        
        # Update pending questions
        state.pending_questions = remaining_questions
        
        # Generate conversation guidance using vector intelligence
        guidance = await self._generate_vector_guidance(state, user_message, current_topic, vector_insights)
        
        await self._save_conversation_state(user_id, state)
        
        return {
            "answered_questions": answered_questions,
            "remaining_questions": remaining_questions,
            "guidance": guidance,
            "vector_insights": vector_insights,
            "question_answer_ratio": self._calculate_answer_ratio(state),
            "integration_status": "vector_native"
        }
    
    async def get_reminder_suggestions(self, user_id: str) -> List[str]:
        """
        Get natural reminder suggestions for unanswered questions.
        
        Returns:
            List of natural ways to bring up pending questions
        """
        state = await self._get_conversation_state(user_id)
        reminders = []
        
        for question in state.pending_questions:
            # Check if it's time for a gentle reminder using simple timing
            if self._should_remind(question):
                reminder = await self._create_natural_reminder(question, state)
                if reminder:
                    reminders.append(reminder)
                    question.last_reminded_at = datetime.now()
                    question.reminder_count += 1
        
        await self._save_conversation_state(user_id, state)
        return reminders
    
    async def detect_conversation_issues(self, user_id: str) -> Dict[str, Any]:
        """
        Detect conversation flow issues and suggest improvements.
        
        Returns:
            Analysis of conversation health and suggestions
        """
        state = await self._get_conversation_state(user_id)
        
        issues = []
        suggestions = []
        
        # Too many unanswered questions
        if len(state.pending_questions) > 2:
            issues.append("too_many_pending_questions")
            suggestions.append("Focus on one key question and let others naturally fade")
        
        # Low answer ratio (user not engaging with bot questions)
        answer_ratio = self._calculate_answer_ratio(state)
        if answer_ratio < 0.3 and state.total_questions_asked > 5:
            issues.append("low_question_engagement")
            suggestions.append("Ask fewer questions, focus on statements and observations")
        
        # Topic jumping (user avoiding deeper conversation)
        if state.topic_transition_abruptness > 0.7:
            issues.append("topic_avoidance")
            suggestions.append("Follow user's lead more, ask fewer probing questions")
        
        # Stagnation risk
        if state.stagnation_risk_score > 0.8:
            issues.append("conversation_stagnation")
            suggestions.append("Introduce fresh topic or ask about user's current interests")
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "health_score": self._calculate_conversation_health(state),
            "answer_ratio": answer_ratio,
            "pending_count": len(state.pending_questions)
        }
    
    # Helper methods for natural conversation flow
    
    async def _generate_gentle_reminders_vector_native(self, question_text: str, question_type: QuestionType, user_id: str) -> List[str]:
        """Generate natural reminders using WhisperEngine's vector-based intelligence"""
        
        try:
            # Vector-native approach: Use existing sophisticated systems
            emotional_context = None
            personality_profile = None
            conversation_patterns = None
            
            # 1. Use existing EnhancedVectorEmotionAnalyzer for sophisticated emotion detection
            if self.emotion_analyzer:
                emotional_context = await self.emotion_analyzer.analyze_emotion_with_context(
                    text=question_text,
                    user_id=user_id,
                    context="reminder_generation"
                )
            
            # 2. Use existing DynamicPersonalityProfiler for real-time personality adaptation
            if self.personality_profiler:
                personality_profile = await self.personality_profiler.get_personality_profile(user_id)
            
            # 3. Use vector memory to understand user's conversation preferences
            if hasattr(self.memory_manager, 'retrieve_relevant_memories'):
                conversation_patterns = await self.memory_manager.retrieve_relevant_memories(
                    user_id=user_id,
                    query=f"reminder style question response {question_type.value}",
                    limit=5
                )
            
            # 4. Generate vector-informed reminders
            return await self._create_vector_informed_reminders(
                question_text, question_type, emotional_context, personality_profile, conversation_patterns
            )
            
        except Exception as e:
            logger.debug("Vector reminder generation fallback: %s", e)
            # Fallback to simple reminders
            return self._generate_simple_reminders(question_text, question_type)
    
    async def _create_vector_informed_reminders(
        self, 
        question_text: str, 
        question_type: QuestionType,
        emotional_context: Optional[Dict] = None,
        personality_profile: Optional[Dict] = None,
        conversation_patterns: Optional[List] = None
    ) -> List[str]:
        """Create reminders using vector intelligence instead of duplicate emotion/personality systems"""
        
        # Use vector-based emotional intelligence for tone
        tone_modifier = "curious"
        if emotional_context:
            primary_emotion = emotional_context.get('primary_emotion', 'neutral')
            if primary_emotion in ['sad', 'stressed', 'overwhelmed']:
                tone_modifier = "gently interested"
            elif primary_emotion in ['excited', 'happy']:
                tone_modifier = "enthusiastically curious"
        
        # Use personality profiler results for style
        approach_style = "about"
        if personality_profile and PersonalityDimension:
            # personality_profile is a PersonalityProfile object, not a dict
            try:
                # Check if it has traits attribute (PersonalityProfile object)
                if hasattr(personality_profile, 'traits') and personality_profile.traits:
                    communication_trait = personality_profile.traits.get(PersonalityDimension.COMMUNICATION_STYLE)
                    if communication_trait:
                        # Formality: negative values = casual, positive values = formal
                        if communication_trait.value > 0.4:  # More formal
                            approach_style = "regarding"
                        elif communication_trait.value < -0.4:  # More casual  
                            approach_style = "about"
            except (AttributeError, KeyError, TypeError):
                # Fallback to default if personality data unavailable
                pass
        
        topic = self._extract_topic(question_text)
        
        # Generate contextually appropriate reminders
        reminders = {
            QuestionType.OPINION: [
                f"I'm still {tone_modifier} {approach_style} your thoughts on {topic}...",
                f"Your perspective on {topic} would really help me understand better"
            ],
            QuestionType.PERSONAL: [
                f"I keep thinking about what you mentioned {approach_style} {topic}...",
                f"I'm {tone_modifier} {approach_style} your experience with {topic}"
            ],
            QuestionType.FOLLOWUP: [
                f"I'd love to know more {approach_style} {topic}",
                f"That conversation about {topic} really interested me..."
            ]
        }
        
        return reminders.get(question_type, [f"I'm still {tone_modifier} {approach_style} what you mentioned earlier"])
    
    def _generate_simple_reminders(self, question_text: str, question_type: QuestionType) -> List[str]:
        """Simple fallback reminders when vector systems unavailable"""
        topic = self._extract_topic(question_text)
        base_reminders = {
            QuestionType.OPINION: [f"I'm still curious about your thoughts on {topic}"],
            QuestionType.PERSONAL: [f"I'm interested in your experience with {topic}"],
            QuestionType.FOLLOWUP: [f"I'd love to know more about {topic}"]
        }
        return base_reminders.get(question_type, ["I'm still curious about what you mentioned earlier"])
    
    def _generate_natural_callbacks(self, question_text: str, topic: Optional[str]) -> List[str]:
        """Generate natural ways to return to the topic later"""
        topic_focus = topic or self._extract_topic(question_text)
        return [
            f"Speaking of {topic_focus}...",
            f"That reminds me of what we were discussing about {topic_focus}",
            f"Oh, that's interesting! It relates to {topic_focus} too"
        ]
    
    def _extract_topic(self, question_text: str) -> str:
        """Extract the main topic from a question"""
        # Simple keyword extraction - could be enhanced with NLP
        words = question_text.lower().split()
        # Remove question words and focus on content
        content_words = [w for w in words if w not in ['what', 'how', 'when', 'where', 'why', 'who', 'do', 'did', 'can', 'could', 'would', 'should']]
        return ' '.join(content_words[:3]) if content_words else "that"
    
    async def _is_question_answered(
        self, 
        question: PendingQuestion, 
        user_message: str, 
        current_topic: Optional[str]
    ) -> bool:
        """
        Determine if user's message answers the pending question.
        
        This could be enhanced with:
        - Semantic similarity checking
        - Topic coherence analysis  
        - Intent recognition
        """
        message_lower = user_message.lower()
        question_lower = question.question_text.lower()
        
        # Simple heuristics (could be enhanced with ML)
        
        # If user directly addresses the question topic
        question_keywords = set(self._extract_topic(question_lower).split())
        message_words = set(message_lower.split())
        
        keyword_overlap = len(question_keywords.intersection(message_words))
        if keyword_overlap >= 2:
            return True
        
        # If current topic matches question topic
        if (current_topic and question.original_topic and 
            current_topic.lower() == question.original_topic.lower()):
            return True
        
        # Question type specific checking
        if question.question_type == QuestionType.CHOICE:
            # Look for decision words
            choice_words = ['prefer', 'choose', 'like', 'better', 'favorite']
            if any(word in message_lower for word in choice_words):
                return True
        
        elif question.question_type == QuestionType.OPINION:
            # Look for opinion expressions
            opinion_words = ['think', 'believe', 'feel', 'opinion', 'view', 'perspective']
            if any(word in message_lower for word in opinion_words):
                return True
        
        return False
    
    async def _evaluate_answer_quality(self, question: PendingQuestion, answer: str) -> float:
        """
        Evaluate how well the user answered the question (0.0-1.0).
        
        Could be enhanced with:
        - Semantic analysis
        - Completeness checking
        - Relevance scoring
        """
        # Simple length-based heuristic (fuller answers score higher)
        if len(answer) < 10:
            return 0.3  # Very brief
        elif len(answer) < 50:
            return 0.6  # Moderate
        else:
            return 0.9  # Detailed
    
    def _should_remind(self, question: PendingQuestion) -> bool:
        """Check if it's time to gently remind about this question"""
        
        # Don't remind too often
        if question.reminder_count >= question.max_reminders:
            return False
        
        # Wait appropriate time since asking or last reminder
        time_threshold = datetime.now() - timedelta(minutes=self.gentle_reminder_delay_minutes)
        
        last_action = question.last_reminded_at or question.asked_at
        if last_action > time_threshold:
            return False
        
        # Higher priority questions get more reminders
        if question.priority == QuestionPriority.HIGH and question.reminder_count < 3:
            return True
        elif question.priority == QuestionPriority.MEDIUM and question.reminder_count < 2:
            return True
        elif question.priority == QuestionPriority.LOW and question.reminder_count < 1:
            return True
        
        return False
    
    async def _create_natural_reminder(self, question: PendingQuestion, state: ConversationState) -> Optional[str]:
        """Create natural reminders using vector-based emotional and personality intelligence"""
        
        try:
            # Use vector-based systems instead of duplicating functionality
            emotional_context = None
            personality_insights = None
            
            # Get sophisticated emotional analysis from existing system
            if self.emotion_analyzer:
                emotional_context = await self.emotion_analyzer.analyze_emotion_with_context(
                    text=question.question_text,
                    user_id=state.user_id,
                    context="reminder_timing"
                )
            
            # Get personality-aware communication style from existing system  
            if self.personality_profiler:
                personality_insights = await self.personality_profiler.get_personality_profile(state.user_id)
            
            # Use vector memory to understand current conversation context
            if hasattr(self.memory_manager, 'retrieve_relevant_memories') and state.current_topic:
                topic_memories = await self.memory_manager.retrieve_relevant_memories(
                    user_id=state.user_id,
                    query=f"conversation flow {state.current_topic} {question.original_topic}",
                    limit=3
                )
                
                # Create memory bridge using vector similarity
                if topic_memories:
                    bridge = await self._create_vector_memory_bridge(
                        state.current_topic, question.question_text, topic_memories
                    )
                    if bridge:
                        return bridge
            
            # Generate context-aware reminder based on vector intelligence
            return await self._generate_vector_contextual_reminder(
                question, emotional_context, personality_insights
            )
            
        except Exception as e:
            logger.debug("Vector reminder creation fallback: %s", e)
            # Simple fallback
            topic = self._extract_topic(question.question_text)
            if question.reminder_count == 0:
                return f"I'm still curious about {topic}..."
            elif question.reminder_count == 1:
                return f"I'm still wondering about {topic} - would love to know!"
            else:
                return f"Feel free to skip my earlier question about {topic} if you'd rather talk about something else"
    
    def _calculate_answer_ratio(self, state: ConversationState) -> float:
        """Calculate ratio of answered questions to total questions asked"""
        if state.total_questions_asked == 0:
            return 1.0
        return state.total_questions_answered / state.total_questions_asked
    
    def _calculate_conversation_health(self, state: ConversationState) -> float:
        """
        Calculate overall conversation health score (0.0-1.0).
        
        Factors:
        - Question answer ratio
        - Pending question count
        - Topic engagement
        - Stagnation risk
        """
        answer_ratio = self._calculate_answer_ratio(state)
        pending_penalty = len(state.pending_questions) * 0.1
        engagement_score = state.topic_engagement_score
        stagnation_penalty = state.stagnation_risk_score * 0.3
        
        health = (answer_ratio + engagement_score - pending_penalty - stagnation_penalty) / 2
        return max(0.0, min(1.0, health))
    
    async def _get_conversation_state(self, user_id: str) -> ConversationState:
        """Get or create conversation state for user - thread-safe"""
        # Use per-user locking to prevent race conditions
        async with self._global_lock:
            if user_id not in self._state_locks:
                self._state_locks[user_id] = asyncio.Lock()
            user_lock = self._state_locks[user_id]
        
        async with user_lock:
            if user_id not in self.user_states:
                # Try to load from memory storage
                try:
                    stored_state = await self.memory_manager.retrieve_relevant_memories(
                        user_id=f"conversation_state_{user_id}",
                        query="conversation_state",
                        limit=1
                    )
                    if stored_state and len(stored_state) > 0:
                        # Handle different memory return formats
                        memory_item = stored_state[0]
                        state_data = None
                        
                        # Try different ways to access metadata
                        if hasattr(memory_item, 'metadata') and memory_item.metadata:
                            state_data = memory_item.metadata.get("state_data")
                        elif isinstance(memory_item, dict) and "metadata" in memory_item:
                            state_data = memory_item["metadata"].get("state_data")
                        elif isinstance(memory_item, dict) and "state_data" in memory_item:
                            state_data = memory_item.get("state_data")
                        
                        if state_data:
                            parsed_data = json.loads(state_data) if isinstance(state_data, str) else state_data
                            self.user_states[user_id] = ConversationState(**parsed_data)
                        else:
                            self.user_states[user_id] = ConversationState(user_id=user_id)
                    else:
                        self.user_states[user_id] = ConversationState(user_id=user_id)
                except Exception as e:
                    logger.warning("Could not load conversation state for %s: %s", user_id, e)
                    self.user_states[user_id] = ConversationState(user_id=user_id)
            
            return self.user_states[user_id]
    
    async def _save_conversation_state(self, user_id: str, state: ConversationState):
        """Persist conversation state to memory"""
        try:
            # Convert to JSON for storage
            state_data = {
                "user_id": state.user_id,
                "current_topic": state.current_topic,
                "topic_depth": state.topic_depth,
                "total_questions_asked": state.total_questions_asked,
                "total_questions_answered": state.total_questions_answered,
                # Serialize pending questions
                "pending_questions": [
                    {
                        "question_id": q.question_id,
                        "question_text": q.question_text,
                        "question_type": q.question_type.value,
                        "priority": q.priority.value,
                        "original_topic": q.original_topic,
                        "asked_at": q.asked_at.isoformat(),
                        "reminder_count": q.reminder_count,
                        "is_resolved": q.is_resolved
                    }
                    for q in state.pending_questions
                ]
            }
            
            await self.memory_manager.store_conversation(
                user_id=f"conversation_state_{user_id}",
                user_message="conversation_state",
                bot_response="conversation_state_data",
                metadata={
                    "memory_type": "conversation_state",
                    "state_data": json.dumps(state_data),
                    "updated_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to save conversation state for {user_id}: {e}")
    
    async def _generate_conversation_guidance(
        self, 
        state: ConversationState, 
        user_message: str, 
        current_topic: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Generate guidance for the bot on how to handle the conversation"""
        
        guidance = {
            "should_ask_questions": True,
            "topic_transition_advice": "smooth",
            "engagement_strategy": "balanced"
        }
        
        # Adjust based on user's question-answering pattern
        answer_ratio = self._calculate_answer_ratio(state)
        if answer_ratio < 0.4:
            guidance.update({
                "should_ask_questions": False,
                "engagement_strategy": "statements_only",
                "advice": "User seems to prefer statements over questions - focus on sharing and observations"
            })
        
        # Check for too many pending questions
        if len(state.pending_questions) > 2:
            guidance.update({
                "should_ask_questions": False,
                "advice": "Too many pending questions - focus on responding without asking new ones"
            })
        
        return guidance
    
    # REMOVED: Duplicate human-like conversation methods
    # These features now integrate with existing WhisperEngine vector systems:
    # - EnhancedVectorEmotionAnalyzer for sophisticated emotion detection
    # - DynamicPersonalityProfiler for real-time personality adaptation
    # - Vector memory system for conversation pattern analysis
    # 
    # The vector-native approach provides more sophisticated intelligence
    # while maintaining architectural consistency with WhisperEngine's design.
    
    # Vector-native helper methods that integrate with existing WhisperEngine systems
    
    async def _create_vector_memory_bridge(self, current_topic: str, question_text: str, topic_memories: List[Any]) -> Optional[str]:
        """Create natural topic bridges using vector memory intelligence"""
        if not topic_memories:
            return None
        
        # Use vector similarity to find natural connection points
        topic = self._extract_topic(question_text)
        
        # Simple bridge generation (could be enhanced with more sophisticated vector analysis)
        bridges = [
            f"That's fascinating about {current_topic}! It reminds me of when you mentioned {topic}...",
            f"Speaking of {current_topic}, I'm still curious about {topic}...",
            f"Your point about {current_topic} connects to something I wanted to ask about {topic}..."
        ]
        return random.choice(bridges)
    
    async def _get_vector_intelligence_insights(
        self, 
        user_id: str, 
        user_message: str, 
        emotional_state: str
    ) -> Dict[str, Any]:
        """
        Get insights from existing vector-based intelligence systems.
        """
        insights = {
            "emotional_analysis": {"primary_emotion": emotional_state},
            "personality_adaptation": {"current_style": "adaptive"},
            "conversation_intelligence": {"pattern": "engaged"}
        }
        
        try:
            # Use existing emotion analyzer if available
            if self.emotion_analyzer is not None:
                emotion_result = await self.emotion_analyzer.analyze_emotion(
                    user_id=user_id,
                    content=user_message,
                    context=None
                )
                insights["emotional_analysis"] = emotion_result.to_dict() if hasattr(emotion_result, 'to_dict') else {}
            
            # Use existing personality profiler if available  
            if self.personality_profiler is not None:
                personality_result = await self.personality_profiler.get_adaptation_recommendations(
                    user_id=user_id
                )
                insights["personality_adaptation"] = personality_result
                
        except Exception as e:
            logger.warning("Vector intelligence insights failed: %s", e)
            
        return insights
    
    async def _generate_vector_guidance(
        self, 
        state: ConversationState, 
        user_message: str, 
        current_topic: Optional[str], 
        vector_insights: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate conversation guidance using vector intelligence.
        """
        if not state.pending_questions:
            return None
            
        try:
            # Use vector insights to determine appropriate guidance style
            emotional_tone = vector_insights.get("emotional_analysis", {}).get("primary_emotion", "neutral")
            
            oldest_question = min(state.pending_questions, key=lambda q: q.asked_at)
            time_since = datetime.now() - oldest_question.asked_at
            
            if time_since.total_seconds() > 300:  # 5 minutes
                return await self._generate_vector_contextual_reminder(
                    oldest_question,
                    vector_insights.get("emotional_analysis"),
                    vector_insights.get("personality_adaptation")
                )
            
            return None
            
        except Exception as e:
            logger.warning("Vector guidance generation failed: %s", e)
            return None
    
    async def _generate_vector_contextual_reminder(
        self, 
        question: PendingQuestion, 
        emotional_context: Optional[Dict] = None,
        personality_insights: Optional[Dict] = None
    ) -> str:
        """Generate contextual reminders using vector-based intelligence"""
        
        topic = self._extract_topic(question.question_text)
        
        # Use emotional context from vector analyzer
        tone = "curious"
        if emotional_context:
            primary_emotion = emotional_context.get('primary_emotion', 'neutral')
            if primary_emotion in ['sad', 'stressed', 'overwhelmed']:
                tone = "gently interested"
            elif primary_emotion in ['excited', 'happy', 'enthusiastic']:
                tone = "enthusiastically curious"
        
        # Use personality insights for communication style
        style = "about"
        if personality_insights:
            communication_traits = personality_insights.get('communication_style', {})
            formality = communication_traits.get('formality', 0.5)
            if formality > 0.7:
                style = "regarding"
        
        # Generate reminder based on count and context
        if question.reminder_count == 0:
            return f"I'm still {tone} {style} {topic}..."
        elif question.reminder_count == 1:
            if tone == "gently interested":
                return f"When you're ready, I'd love to hear {style} {topic} - no rush at all"
            else:
                return f"I'm still wondering {style} {topic} - would love to know!"
        else:
            return f"Feel free to skip my earlier question {style} {topic} if you'd rather talk about something else"
    
    async def _is_question_answered_vector(self, question: PendingQuestion, user_message: str, current_topic: Optional[str]) -> bool:
        """Use vector similarity to detect if question was answered (replaces keyword matching)"""
        
        try:
            # Use vector embeddings for semantic similarity detection
            if hasattr(self.memory_manager, 'vector_store'):
                vector_store = self.memory_manager.vector_store
                
                # Generate embeddings
                question_embedding = await vector_store.generate_embedding(question.question_text)
                answer_embedding = await vector_store.generate_embedding(user_message)
                
                if question_embedding and answer_embedding:
                    # Calculate semantic similarity
                    similarity = self._calculate_cosine_similarity(question_embedding, answer_embedding)
                    
                    # Higher threshold for semantic answering vs keyword matching
                    return similarity > 0.3  # Adjust threshold based on testing
            
        except Exception as e:
            logger.debug("Vector similarity detection fallback: %s", e)
        
        # Fallback to enhanced keyword matching
        return await self._is_question_answered_fallback(question, user_message, current_topic)
    
    def _calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        import math
        
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(b * b for b in embedding2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def _is_question_answered_fallback(self, question: PendingQuestion, user_message: str, current_topic: Optional[str]) -> bool:
        """Enhanced fallback question answering detection"""
        message_lower = user_message.lower()
        question_lower = question.question_text.lower()
        
        # Enhanced keyword matching with context
        question_keywords = self._extract_keywords(question_lower)
        message_keywords = self._extract_keywords(message_lower)
        
        # Check for keyword overlap
        overlap = len(set(question_keywords) & set(message_keywords))
        keyword_threshold = max(1, len(question_keywords) // 3)
        
        # Topic coherence check
        topic_match = current_topic and question.original_topic == current_topic
        
        # Answer pattern detection
        answer_patterns = ['because', 'since', 'i think', 'i feel', 'my opinion', 'i believe']
        has_answer_pattern = any(pattern in message_lower for pattern in answer_patterns)
        
        return overlap >= keyword_threshold or topic_match or has_answer_pattern
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove question words and common words
        stop_words = {'what', 'how', 'when', 'where', 'why', 'who', 'do', 'did', 'can', 'could', 'would', 'should', 'the', 'a', 'an', 'and', 'or', 'but'}
        words = [word.strip('.,!?') for word in text.split() if len(word) > 2]
        return [word for word in words if word.lower() not in stop_words]


# Factory function for integration with WhisperEngine
async def create_persistent_conversation_manager(memory_manager: Any) -> PersistentConversationManager:
    """Factory to create persistent conversation manager"""
    return PersistentConversationManager(memory_manager)