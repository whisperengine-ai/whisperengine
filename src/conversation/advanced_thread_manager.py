"""
Advanced Multi-Thread Conversation Management System for AI Companions

This module provides sophisticated conversation thread management that allows AI companions
to handle multiple topics gracefully, maintain context across thread switches, and
prioritize conversations based on emotional urgency and user engagement.

This is Phase 4.2 of the personality-driven AI companion system, building on:
- Phase 3.1: Emotional Context Engine
- Phase 4.1: Memory-Triggered Personality Moments

Key Features:
- Multi-thread conversation tracking and identification
- Intelligent thread transition detection
- Context preservation across thread switches
- Priority-based thread management
- Natural conversation flow maintenance
- Integration with memory and personality systems

Thread Management Capabilities:
- Thread creation, pause, resume, and merging
- Topic similarity analysis for thread identification
- Emotional context continuity across threads
- User intent classification and thread routing
- Proactive thread switching opportunity detection
- Conversation stagnation detection and response

Integration Points:
- Memory-triggered moments for thread connections
- Emotional context engine for thread prioritization
- Dynamic personality profiler for conversation adaptation
- Universal chat platform for multi-platform support
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
import re
import statistics
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import existing systems for integration
try:
    from src.intelligence.emotional_context_engine import EmotionalContextEngine, EmotionalContext, EmotionalState
    EMOTIONAL_CONTEXT_AVAILABLE = True
except ImportError:
    EMOTIONAL_CONTEXT_AVAILABLE = False

try:
    from src.intelligence.dynamic_personality_profiler import DynamicPersonalityProfiler
    PERSONALITY_PROFILER_AVAILABLE = True
except ImportError:
    PERSONALITY_PROFILER_AVAILABLE = False

try:
    from src.personality.memory_moments import MemoryTriggeredMoments, ConversationContext
    MEMORY_MOMENTS_AVAILABLE = True
except ImportError:
    MEMORY_MOMENTS_AVAILABLE = False

# Memory tier system removed for performance optimization

logger = logging.getLogger(__name__)


class ConversationThreadState(Enum):
    """States that a conversation thread can be in"""
    ACTIVE = "active"              # Currently being discussed
    PAUSED = "paused"              # Temporarily paused
    SUSPENDED = "suspended"        # Waiting for user attention
    BACKGROUND = "background"      # Low priority, monitoring only
    RESOLVED = "resolved"          # Discussion completed
    MERGED = "merged"              # Merged with another thread
    ARCHIVED = "archived"          # Archived for historical reference


class ThreadTransitionType(Enum):
    """Types of transitions between conversation threads"""
    NATURAL_FLOW = "natural_flow"           # Topic evolved naturally
    EXPLICIT_SWITCH = "explicit_switch"     # User explicitly changed topics
    REMINDER_DRIVEN = "reminder_driven"     # User remembered something
    INTERRUPTION = "interruption"           # External interruption occurred
    EMOTIONAL_DRIVEN = "emotional_driven"   # Emotional state change drove switch
    TIME_DRIVEN = "time_driven"             # Time/schedule related switch
    PRIORITY_DRIVEN = "priority_driven"     # High priority thread demanded attention
    COMPLETION_DRIVEN = "completion_driven" # Previous thread naturally completed


class ThreadPriorityLevel(Enum):
    """Priority levels for conversation threads"""
    CRITICAL = "critical"       # Immediate attention required
    HIGH = "high"              # Important, should address soon
    MEDIUM = "medium"          # Normal conversation priority
    LOW = "low"                # Background, address when convenient
    MINIMAL = "minimal"        # Monitor only, very low priority


@dataclass
class ConversationThreadAdvanced:
    """An advanced conversation thread with topic continuity and context management"""
    thread_id: str
    user_id: str
    
    # Thread identification
    topic_seeds: List[str] = field(default_factory=list)      # Initial topic keywords
    topic_keywords: List[str] = field(default_factory=list)   # All related keywords
    theme_tags: List[str] = field(default_factory=list)       # Semantic themes
    
    # Thread state
    state: ConversationThreadState = ConversationThreadState.ACTIVE
    priority_level: ThreadPriorityLevel = ThreadPriorityLevel.MEDIUM
    
    # Content tracking
    messages: List[Dict[str, Any]] = field(default_factory=list)
    last_message_time: datetime = field(default_factory=datetime.now)
    total_messages: int = 0
    
    # Context preservation
    emotional_context: Optional[Any] = None   # Current emotional state
    conversation_phase: str = "opening"       # opening, developing, deepening, resolving
    unresolved_questions: List[str] = field(default_factory=list)
    pending_actions: List[str] = field(default_factory=list)
    
    # Relationship tracking
    relationship_depth_at_start: float = 0.0
    trust_level_at_start: float = 0.0
    engagement_level: float = 0.0
    
    # Thread management
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    pause_reason: Optional[str] = None
    resumption_cues: List[str] = field(default_factory=list)
    
    # Connection tracking
    related_threads: List[str] = field(default_factory=list)
    parent_thread: Optional[str] = None
    child_threads: List[str] = field(default_factory=list)
    
    # Priority factors
    emotional_urgency: float = 0.0
    time_sensitivity: float = 0.0
    completion_status: float = 0.0  # 0.0 = just started, 1.0 = completed
    user_investment: float = 0.0    # How much user cares about this topic


@dataclass 
class ThreadTransition:
    """Information about a transition between conversation threads"""
    transition_id: str
    user_id: str
    
    # Transition details
    from_thread: Optional[str]
    to_thread: str
    transition_type: ThreadTransitionType
    trigger_message: str
    
    # Transition context
    bridge_message: str = ""                  # AI's transition message
    context_preserved: Dict[str, Any] = field(default_factory=dict)
    transition_quality: float = 0.0          # 0.0-1.0 smoothness rating
    
    # Timing
    transition_time: datetime = field(default_factory=datetime.now)
    preparation_time: float = 0.0            # Seconds to prepare transition
    
    # User response
    user_accepted_transition: Optional[bool] = None
    user_feedback: Optional[str] = None


class AdvancedConversationThreadManager:
    """
    Advanced system for managing multiple conversation threads with intelligent
    context switching, priority management, and natural conversation flow.
    
    This is the Phase 4.2 implementation focused on sophisticated thread management
    rather than basic persistence (which is handled by the existing thread_manager.py).
    """
    
    def __init__(self,
                 emotional_context_engine: Optional[EmotionalContextEngine] = None,
                 personality_profiler: Optional[DynamicPersonalityProfiler] = None,
                 memory_moments: Optional[MemoryTriggeredMoments] = None,
                 memory_manager: Optional[Any] = None,
                 max_active_threads: int = 5,
                 max_background_threads: int = 20,
                 thread_timeout_hours: int = 48):
        """
        Initialize the advanced conversation thread manager.
        
        Args:
            emotional_context_engine: Emotional intelligence system
            personality_profiler: Personality profiling system
            memory_moments: Memory-triggered moments system
            memory_tier_manager: Memory tier management
            max_active_threads: Maximum active threads per user
            max_background_threads: Maximum background threads per user
            thread_timeout_hours: Hours before threads are archived
        """
        self.emotional_context_engine = emotional_context_engine
        self.personality_profiler = personality_profiler
        self.memory_moments = memory_moments
        self.memory_manager = memory_manager
        
        self.max_active_threads = max_active_threads
        self.max_background_threads = max_background_threads
        self.thread_timeout = timedelta(hours=thread_timeout_hours)
        
        # Thread storage
        self.user_threads: Dict[str, List[ConversationThreadAdvanced]] = defaultdict(list)
        self.thread_transitions: Dict[str, List[ThreadTransition]] = defaultdict(list)
        self.active_threads: Dict[str, str] = {}  # user_id -> current thread_id
        
        # Analysis engines
        self.topic_analyzer = TopicSimilarityAnalyzer()
        self.transition_detector = TransitionDetector()
        self.priority_calculator = ThreadPriorityCalculator()
        
        # Performance tracking
        self.thread_success_rates: Dict[str, float] = {}
        self.transition_quality_scores: List[float] = []
        self.user_satisfaction_scores: Dict[str, List[float]] = defaultdict(list)
        
        logger.info("AdvancedConversationThreadManager initialized with max %d active threads", 
                   max_active_threads)
    
    async def process_user_message(self,
                                 user_id: str,
                                 message: str,
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message and manage conversation threads intelligently.
        
        Args:
            user_id: User identifier
            message: User's message content
            context: Optional conversation context
            
        Returns:
            Thread management information and response guidance
        """
        # Analyze message for thread identification
        thread_analysis = await self._analyze_message_for_thread(user_id, message, context)
        
        # Determine if this continues existing thread or starts new one
        target_thread = await self._determine_target_thread(user_id, message, thread_analysis)
        
        # Handle thread transitions if necessary
        transition_info = await self._handle_thread_transition(user_id, target_thread, message)
        
        # Update thread state
        await self._update_thread_state(user_id, target_thread, message, context)
        
        # Calculate thread priorities
        priorities = await self._calculate_thread_priorities(user_id)
        
        # Generate response guidance
        response_guidance = await self._generate_response_guidance(
            user_id, target_thread, transition_info, priorities
        )
        
        return {
            'current_thread': target_thread,
            'thread_analysis': thread_analysis,
            'transition_info': transition_info,
            'thread_priorities': priorities,
            'response_guidance': response_guidance,
            'active_threads': await self._get_active_threads(user_id),
            'context_switches': await self._get_recent_context_switches(user_id)
        }
    
    async def _analyze_message_for_thread(self,
                                        user_id: str,
                                        message: str,
                                        context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze message to understand thread context and intent"""
        
        # Extract topics and keywords
        keywords = self._extract_keywords(message)
        themes = self._identify_themes(message)
        
        # Detect transition indicators
        transition_indicators = self._detect_transition_indicators(message)
        
        # Analyze emotional context
        emotional_analysis = await self._analyze_emotional_context(message, context)
        
        # Check for explicit thread references
        thread_references = await self._detect_thread_references(user_id, message)
        
        # Determine conversation intent
        intent_analysis = await self._analyze_conversation_intent(message, context)
        
        return {
            'keywords': keywords,
            'themes': themes,
            'transition_indicators': transition_indicators,
            'emotional_analysis': emotional_analysis,
            'thread_references': thread_references,
            'intent_analysis': intent_analysis,
            'message_complexity': self._assess_message_complexity(message),
            'engagement_level': self._assess_engagement_level(message)
        }
    
    async def _determine_target_thread(self,
                                     user_id: str,
                                     message: str,
                                     analysis: Dict[str, Any]) -> str:
        """Determine which thread this message belongs to"""
        
        user_threads = self.user_threads[user_id]
        current_thread_id = self.active_threads.get(user_id)
        
        # If explicit thread reference, use that
        if analysis['thread_references']:
            return analysis['thread_references'][0]
        
        # If strong transition indicator, consider new thread
        if analysis['transition_indicators']['strength'] > 0.7:
            return await self._create_new_thread(user_id, message, analysis)
        
        # Check similarity with existing threads
        thread_similarities = []
        for thread in user_threads:
            if thread.state in [ConversationThreadState.ACTIVE, ConversationThreadState.PAUSED]:
                similarity = await self._calculate_thread_similarity(thread, analysis)
                thread_similarities.append((thread.thread_id, similarity))
        
        # Find best matching thread
        if thread_similarities:
            thread_similarities.sort(key=lambda x: x[1], reverse=True)
            best_thread_id, best_similarity = thread_similarities[0]
            
            # If good similarity and recent activity, continue thread
            if best_similarity > 0.6:
                best_thread = next(t for t in user_threads if t.thread_id == best_thread_id)
                time_since_last = datetime.now() - best_thread.last_active
                
                if time_since_last < timedelta(hours=2):  # Recent activity
                    return best_thread_id
        
        # If no good match or current thread is very different, create new thread
        if current_thread_id:
            current_thread = next((t for t in user_threads if t.thread_id == current_thread_id), None)
            if current_thread:
                current_similarity = await self._calculate_thread_similarity(current_thread, analysis)
                if current_similarity < 0.3:  # Very different from current thread
                    return await self._create_new_thread(user_id, message, analysis)
        
        # Continue current thread or create new one if none exists
        return current_thread_id or await self._create_new_thread(user_id, message, analysis)
    
    async def _create_new_thread(self,
                               user_id: str,
                               initial_message: str,
                               analysis: Dict[str, Any]) -> str:
        """Create a new conversation thread"""
        
        thread_id = self._generate_thread_id(user_id)
        
        # Determine initial priority
        priority_level = await self._assess_initial_priority(analysis)
        
        # Extract emotional context
        emotional_context = analysis.get('emotional_analysis', {}).get('primary_emotion')
        
        # Create thread
        thread = ConversationThreadAdvanced(
            thread_id=thread_id,
            user_id=user_id,
            topic_seeds=analysis['keywords'][:5],  # Top 5 keywords as seeds
            topic_keywords=analysis['keywords'],
            theme_tags=analysis['themes'],
            priority_level=priority_level,
            emotional_context=emotional_context,
            engagement_level=analysis.get('engagement_level', 0.5),
            emotional_urgency=analysis.get('emotional_analysis', {}).get('urgency', 0.0),
            time_sensitivity=analysis.get('intent_analysis', {}).get('time_sensitivity', 0.0)
        )
        
        # Add initial message
        thread.messages.append({
            'timestamp': datetime.now(),
            'content': initial_message,
            'message_type': 'user',
            'analysis': analysis
        })
        thread.total_messages = 1
        
        # Store thread
        self.user_threads[user_id].append(thread)
        
        # Set as active thread
        self.active_threads[user_id] = thread_id
        
        # Cleanup old threads if necessary
        await self._cleanup_old_threads(user_id)
        
        logger.info("Created new conversation thread %s for user %s with priority %s",
                   thread_id, user_id, priority_level.value)
        
        return thread_id
    
    async def _handle_thread_transition(self,
                                      user_id: str,
                                      target_thread_id: str,
                                      message: str) -> Optional[ThreadTransition]:
        """Handle transition between conversation threads"""
        
        current_thread_id = self.active_threads.get(user_id)
        
        # No transition if same thread or no current thread
        if not current_thread_id or current_thread_id == target_thread_id:
            self.active_threads[user_id] = target_thread_id
            return None
        
        # Determine transition type
        transition_type = await self._classify_transition_type(
            user_id, current_thread_id, target_thread_id, message
        )
        
        # Generate context bridge
        bridge_message = await self._generate_context_bridge(
            user_id, current_thread_id, target_thread_id, transition_type
        )
        
        # Preserve important context from current thread
        preserved_context = await self._preserve_thread_context(user_id, current_thread_id)
        
        # Create transition record
        transition = ThreadTransition(
            transition_id=self._generate_transition_id(user_id),
            user_id=user_id,
            from_thread=current_thread_id,
            to_thread=target_thread_id,
            transition_type=transition_type,
            trigger_message=message,
            bridge_message=bridge_message,
            context_preserved=preserved_context
        )
        
        # Update thread states
        await self._update_thread_after_transition(user_id, current_thread_id, target_thread_id)
        
        # Store transition
        self.thread_transitions[user_id].append(transition)
        
        # Update active thread
        self.active_threads[user_id] = target_thread_id
        
        logger.info("Thread transition for user %s: %s -> %s (%s)",
                   user_id, current_thread_id, target_thread_id, transition_type.value)
        
        return transition
    
    async def _update_thread_state(self,
                                 user_id: str,
                                 thread_id: str,
                                 message: str,
                                 context: Optional[Dict[str, Any]]):
        """Update the state of a conversation thread"""
        
        thread = await self._get_thread(user_id, thread_id)
        if not thread:
            return
        
        # Add message to thread
        thread.messages.append({
            'timestamp': datetime.now(),
            'content': message,
            'message_type': 'user',
            'context': context
        })
        
        # Update thread metadata
        thread.last_message_time = datetime.now()
        thread.last_active = datetime.now()
        thread.total_messages += 1
        thread.state = ConversationThreadState.ACTIVE
        
        # Update topic keywords
        new_keywords = self._extract_keywords(message)
        thread.topic_keywords = list(set(thread.topic_keywords + new_keywords))
        
        # Update themes
        new_themes = self._identify_themes(message)
        thread.theme_tags = list(set(thread.theme_tags + new_themes))
        
        # Update emotional context if available
        if context and 'emotional_state' in context:
            thread.emotional_context = context['emotional_state']
        
        # Update engagement level
        engagement = self._assess_engagement_level(message)
        thread.engagement_level = (thread.engagement_level * 0.7) + (engagement * 0.3)
        
        # Update conversation phase
        thread.conversation_phase = await self._determine_conversation_phase(thread)
        
        # Update priority factors
        await self._update_thread_priority_factors(thread, message, context)
    
    # Utility methods for thread analysis and management
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Enhanced stop words list for conversation
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 
            'can', 'may', 'might', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 
            'these', 'those', 'just', 'now', 'then', 'here', 'there', 'when', 
            'where', 'why', 'how', 'what', 'who', 'which', 'some', 'any', 'all',
            'very', 'really', 'quite', 'so', 'too', 'much', 'many', 'more', 'most'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:20]  # Limit to top 20 keywords
    
    def _identify_themes(self, text: str) -> List[str]:
        """Identify thematic content in text"""
        text_lower = text.lower()
        themes = []
        
        # Enhanced theme detection with more categories
        theme_patterns = {
            'work': ['work', 'job', 'career', 'office', 'meeting', 'project', 'deadline', 'boss', 'colleague', 'promotion', 'salary', 'interview'],
            'relationships': ['friend', 'family', 'partner', 'relationship', 'love', 'dating', 'marriage', 'kids', 'parents', 'sibling', 'social'],
            'health': ['health', 'doctor', 'medicine', 'exercise', 'diet', 'sick', 'tired', 'energy', 'sleep', 'fitness', 'wellness'],
            'hobbies': ['hobby', 'music', 'movie', 'book', 'game', 'sport', 'travel', 'cooking', 'art', 'photography', 'reading'],
            'achievements': ['accomplished', 'achieved', 'success', 'proud', 'won', 'finished', 'completed', 'goal', 'milestone'],
            'challenges': ['problem', 'difficult', 'struggle', 'challenge', 'hard', 'stressed', 'worried', 'concerned', 'issue'],
            'learning': ['learn', 'study', 'course', 'class', 'education', 'school', 'university', 'skill', 'knowledge', 'practice'],
            'technology': ['computer', 'software', 'app', 'internet', 'digital', 'online', 'tech', 'programming', 'ai', 'robot'],
            'finance': ['money', 'budget', 'save', 'spend', 'invest', 'bank', 'loan', 'debt', 'income', 'financial'],
            'home': ['house', 'apartment', 'room', 'furniture', 'decoration', 'cleaning', 'maintenance', 'neighbor'],
            'food': ['food', 'eat', 'cook', 'recipe', 'restaurant', 'meal', 'lunch', 'dinner', 'breakfast', 'hungry'],
            'emotions': ['feel', 'emotion', 'happy', 'sad', 'angry', 'excited', 'nervous', 'calm', 'frustrated', 'grateful']
        }
        
        for theme, keywords in theme_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                themes.append(theme)
        
        return themes
    
    def _detect_transition_indicators(self, message: str) -> Dict[str, Any]:
        """Detect linguistic indicators of topic transitions"""
        text_lower = message.lower()
        
        # Explicit transition phrases
        explicit_indicators = [
            'anyway', 'by the way', 'speaking of', 'on another note', 'changing topics',
            'oh', 'actually', 'wait', 'also', 'meanwhile', 'however', 'but first',
            'before i forget', 'that reminds me', 'while we\'re talking about'
        ]
        
        # Question-based transitions
        question_indicators = [
            'what about', 'how about', 'can we talk about', 'i wanted to ask',
            'do you know', 'have you', 'what do you think about'
        ]
        
        # Time-based transitions
        time_indicators = [
            'now', 'today', 'yesterday', 'tomorrow', 'next week', 'last time',
            'recently', 'lately', 'earlier', 'later', 'meanwhile'
        ]
        
        explicit_found = [ind for ind in explicit_indicators if ind in text_lower]
        question_found = [ind for ind in question_indicators if ind in text_lower]
        time_found = [ind for ind in time_indicators if ind in text_lower]
        
        # Calculate transition strength
        strength = 0.0
        if explicit_found:
            strength += 0.8
        if question_found:
            strength += 0.6
        if time_found:
            strength += 0.4
        
        # Check for sentence structure indicators
        if message.startswith(('But ', 'However ', 'Actually ', 'Oh ', 'Wait ')):
            strength += 0.5
        
        return {
            'strength': min(1.0, strength),
            'explicit_indicators': explicit_found,
            'question_indicators': question_found,
            'time_indicators': time_found,
            'has_strong_transition': strength > 0.6
        }
    
    # Additional analysis and management methods
    
    async def _analyze_emotional_context(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze emotional context of a message"""
        if self.emotional_context_engine and context:
            try:
                # Use the actual method signature from EmotionalContextEngine
                user_id = context.get('user_id', '')
                context_id = context.get('context_id', 'unknown')
                emotional_context = await self.emotional_context_engine.analyze_emotional_context(
                    user_id, context_id, message
                )
                return {
                    'primary_emotion': emotional_context.primary_emotion.value if hasattr(emotional_context.primary_emotion, 'value') else 'neutral',
                    'urgency': emotional_context.emotion_intensity * 0.8 if emotional_context.primary_emotion.value in ['anger', 'fear', 'sadness'] else 0.2,
                    'emotional_intensity': emotional_context.emotion_intensity
                }
            except Exception as e:
                logger.warning("Failed to analyze emotional context: %s", e)
        
        # Simple fallback analysis
        urgency_indicators = ['urgent', 'emergency', 'help', 'problem', 'worried', 'scared']
        urgency = 0.8 if any(ind in message.lower() for ind in urgency_indicators) else 0.2
        
        return {
            'primary_emotion': 'neutral',
            'urgency': urgency,
            'emotional_intensity': 0.5
        }
    
    async def _detect_thread_references(self, user_id: str, message: str) -> List[str]:
        """Detect references to existing threads"""
        thread_references = []
        user_threads = self.user_threads[user_id]
        
        for thread in user_threads:
            # Check if any topic keywords from thread appear in message
            for keyword in thread.topic_keywords[:5]:  # Check top keywords
                if keyword in message.lower():
                    thread_references.append(thread.thread_id)
                    break
        
        return thread_references
    
    async def _analyze_conversation_intent(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the intent behind a conversation message"""
        text_lower = message.lower()
        
        intent_categories = {
            'question': ['?', 'what', 'how', 'why', 'when', 'where', 'who'],
            'request': ['can you', 'could you', 'would you', 'please help', 'i need'],
            'sharing': ['i feel', 'i think', 'today i', 'yesterday', 'i did', 'i went'],
            'seeking_advice': ['should i', 'what do you think', 'advice', 'recommend'],
            'expressing_emotion': ['happy', 'sad', 'angry', 'excited', 'frustrated', 'grateful']
        }
        
        detected_intents = []
        for intent, indicators in intent_categories.items():
            if any(indicator in text_lower for indicator in indicators):
                detected_intents.append(intent)
        
        # Assess time sensitivity
        time_sensitive_words = ['today', 'tomorrow', 'now', 'urgent', 'deadline', 'soon']
        time_sensitivity = 0.8 if any(word in text_lower for word in time_sensitive_words) else 0.2
        
        return {
            'primary_intent': detected_intents[0] if detected_intents else 'general',
            'all_intents': detected_intents,
            'time_sensitivity': time_sensitivity,
            'complexity_score': len(message.split())  # Simple complexity measure
        }
    
    def _assess_message_complexity(self, message: str) -> float:
        """Assess the complexity of a message"""
        word_count = len(message.split())
        sentence_count = len([s for s in message.split('.') if s.strip()])
        question_count = message.count('?')
        
        # Normalize to 0-1 scale
        complexity = min(1.0, (word_count / 50) + (sentence_count / 5) + (question_count / 3))
        return complexity
    
    def _assess_engagement_level(self, message: str) -> float:
        """Assess user engagement level from message"""
        text_lower = message.lower()
        
        # High engagement indicators
        high_engagement = ['!', 'excited', 'love', 'amazing', 'great', 'wonderful', 'fantastic']
        medium_engagement = ['good', 'nice', 'cool', 'interesting', 'thanks', 'appreciate']
        low_engagement = ['ok', 'fine', 'sure', 'maybe', 'whatever', 'i guess']
        
        score = 0.5  # baseline
        
        for indicator in high_engagement:
            if indicator in text_lower:
                score += 0.2
        
        for indicator in medium_engagement:
            if indicator in text_lower:
                score += 0.1
        
        for indicator in low_engagement:
            if indicator in text_lower:
                score -= 0.1
        
        # Length factor (longer messages often indicate higher engagement)
        word_count = len(message.split())
        if word_count > 20:
            score += 0.1
        elif word_count < 5:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _calculate_thread_similarity(self, thread: ConversationThreadAdvanced, analysis: Dict[str, Any]) -> float:
        """Calculate similarity between thread and message analysis"""
        message_keywords = set(analysis.get('keywords', []))
        thread_keywords = set(thread.topic_keywords)
        
        # Keyword similarity
        if message_keywords and thread_keywords:
            intersection = message_keywords & thread_keywords
            union = message_keywords | thread_keywords
            keyword_similarity = len(intersection) / len(union)
        else:
            keyword_similarity = 0.0
        
        # Theme similarity
        message_themes = set(analysis.get('themes', []))
        thread_themes = set(thread.theme_tags)
        
        if message_themes and thread_themes:
            theme_intersection = message_themes & thread_themes
            theme_union = message_themes | thread_themes
            theme_similarity = len(theme_intersection) / len(theme_union)
        else:
            theme_similarity = 0.0
        
        # Weighted combination
        return (keyword_similarity * 0.7) + (theme_similarity * 0.3)
    
    async def _assess_initial_priority(self, analysis: Dict[str, Any]) -> ThreadPriorityLevel:
        """Assess initial priority level for a new thread"""
        emotional_urgency = analysis.get('emotional_analysis', {}).get('urgency', 0.0)
        time_sensitivity = analysis.get('intent_analysis', {}).get('time_sensitivity', 0.0)
        engagement_level = analysis.get('engagement_level', 0.5)
        
        # Calculate priority score
        priority_score = (emotional_urgency * 0.4) + (time_sensitivity * 0.3) + (engagement_level * 0.3)
        
        if priority_score > 0.8:
            return ThreadPriorityLevel.CRITICAL
        elif priority_score > 0.6:
            return ThreadPriorityLevel.HIGH
        elif priority_score > 0.4:
            return ThreadPriorityLevel.MEDIUM
        elif priority_score > 0.2:
            return ThreadPriorityLevel.LOW
        else:
            return ThreadPriorityLevel.MINIMAL
    
    async def _classify_transition_type(self, user_id: str, from_thread_id: str, 
                                      to_thread_id: str, message: str) -> ThreadTransitionType:
        """Classify the type of thread transition"""
        transition_indicators = self._detect_transition_indicators(message)
        
        if transition_indicators['explicit_indicators']:
            return ThreadTransitionType.EXPLICIT_SWITCH
        
        if any('remind' in ind for ind in transition_indicators['explicit_indicators']):
            return ThreadTransitionType.REMINDER_DRIVEN
        
        if transition_indicators['time_indicators']:
            return ThreadTransitionType.TIME_DRIVEN
        
        # Check emotional context
        emotional_analysis = await self._analyze_emotional_context(message, None)
        if emotional_analysis['urgency'] > 0.7:
            return ThreadTransitionType.EMOTIONAL_DRIVEN
        
        # Default to natural flow
        return ThreadTransitionType.NATURAL_FLOW
    
    async def _generate_context_bridge(self, user_id: str, from_thread_id: str, 
                                     to_thread_id: str, transition_type: ThreadTransitionType) -> str:
        """Generate a context bridge message for thread transitions"""
        from_thread = await self._get_thread(user_id, from_thread_id)
        to_thread = await self._get_thread(user_id, to_thread_id)
        
        if not from_thread or not to_thread:
            return ""
        
        # Generate appropriate bridge based on transition type
        if transition_type == ThreadTransitionType.EXPLICIT_SWITCH:
            return f"I see you'd like to shift our focus from {', '.join(from_thread.topic_keywords[:2])} to {', '.join(to_thread.topic_keywords[:2])}."
        
        elif transition_type == ThreadTransitionType.REMINDER_DRIVEN:
            return f"That's a good connection! This reminds me of what we were discussing about {', '.join(to_thread.topic_keywords[:2])}."
        
        elif transition_type == ThreadTransitionType.EMOTIONAL_DRIVEN:
            return f"I can sense this is important to you right now. Let's focus on {', '.join(to_thread.topic_keywords[:2])}."
        
        else:
            return f"This naturally connects to {', '.join(to_thread.topic_keywords[:2])}."
    
    async def _preserve_thread_context(self, user_id: str, thread_id: str) -> Dict[str, Any]:
        """Preserve important context from a thread being paused"""
        thread = await self._get_thread(user_id, thread_id)
        if not thread:
            return {}
        
        return {
            'unresolved_questions': thread.unresolved_questions.copy(),
            'pending_actions': thread.pending_actions.copy(),
            'emotional_context': thread.emotional_context,
            'conversation_phase': thread.conversation_phase,
            'last_topics': thread.topic_keywords[-5:] if thread.topic_keywords else []
        }
    
    async def _update_thread_after_transition(self, user_id: str, from_thread_id: str, to_thread_id: str):
        """Update thread states after a transition"""
        from_thread = await self._get_thread(user_id, from_thread_id)
        to_thread = await self._get_thread(user_id, to_thread_id)
        
        if from_thread:
            from_thread.state = ConversationThreadState.PAUSED
            from_thread.pause_reason = f"Transitioned to {to_thread_id}"
        
        if to_thread:
            to_thread.state = ConversationThreadState.ACTIVE
            to_thread.last_active = datetime.now()
    
    async def _determine_conversation_phase(self, thread: ConversationThreadAdvanced) -> str:
        """Determine the current phase of conversation in a thread"""
        message_count = thread.total_messages
        
        if message_count <= 3:
            return "opening"
        elif message_count <= 10:
            return "developing"
        elif message_count <= 20:
            return "deepening"
        else:
            return "established"
    
    async def _update_thread_priority_factors(self, thread: ConversationThreadAdvanced, 
                                            message: str, context: Optional[Dict[str, Any]]):
        """Update thread priority factors based on new message"""
        # Update emotional urgency
        emotional_analysis = await self._analyze_emotional_context(message, context)
        thread.emotional_urgency = (thread.emotional_urgency * 0.7) + (emotional_analysis['urgency'] * 0.3)
        
        # Update time sensitivity
        intent_analysis = await self._analyze_conversation_intent(message, context)
        thread.time_sensitivity = (thread.time_sensitivity * 0.7) + (intent_analysis['time_sensitivity'] * 0.3)
        
        # Update completion status based on conversation phase
        phase_completion = {
            'opening': 0.1,
            'developing': 0.3,
            'deepening': 0.6,
            'established': 0.8
        }
        thread.completion_status = phase_completion.get(thread.conversation_phase, 0.5)
    
    async def _calculate_thread_priorities(self, user_id: str) -> Dict[str, Any]:
        """Calculate priorities for all user threads"""
        user_threads = self.user_threads[user_id]
        priorities = {}
        
        for thread in user_threads:
            if thread.state in [ConversationThreadState.ACTIVE, ConversationThreadState.PAUSED]:
                priority_score = await self.priority_calculator.calculate_priority(thread)
                priorities[thread.thread_id] = {
                    'score': priority_score,
                    'level': thread.priority_level.value,
                    'factors': {
                        'emotional_urgency': thread.emotional_urgency,
                        'time_sensitivity': thread.time_sensitivity,
                        'engagement_level': thread.engagement_level,
                        'completion_status': thread.completion_status
                    }
                }
        
        return priorities
    
    async def _generate_response_guidance(self, user_id: str, current_thread_id: str,
                                        transition_info: Optional[ThreadTransition],
                                        priorities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate guidance for response generation"""
        current_thread = await self._get_thread(user_id, current_thread_id)
        if not current_thread:
            return {}
        
        guidance = {
            'thread_context': {
                'topic_keywords': current_thread.topic_keywords[:5],
                'theme_tags': current_thread.theme_tags,
                'conversation_phase': current_thread.conversation_phase,
                'engagement_level': current_thread.engagement_level
            },
            'priority_level': current_thread.priority_level.value,
            'unresolved_items': {
                'questions': current_thread.unresolved_questions,
                'actions': current_thread.pending_actions
            }
        }
        
        if transition_info:
            guidance['transition'] = {
                'type': transition_info.transition_type.value,
                'bridge_message': transition_info.bridge_message,
                'context_preserved': transition_info.context_preserved
            }
        
        # Add personality guidance if available
        if self.personality_profiler:
            try:
                personality_profile = await self.personality_profiler.get_personality_profile(user_id)
                if personality_profile:
                    guidance['personality_context'] = {
                        'relationship_depth': personality_profile.relationship_depth,
                        'trust_level': personality_profile.trust_level,
                        'preferred_response_style': personality_profile.preferred_response_style,
                        'topics_of_high_engagement': personality_profile.topics_of_high_engagement[:5]  # Top 5
                    }
            except (AttributeError, TypeError, KeyError) as e:
                logger.warning("Failed to get personality context: %s", e)
        
        return guidance
    
    async def _get_recent_context_switches(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent context switches for a user"""
        recent_transitions = []
        transitions = self.thread_transitions[user_id]
        
        # Get transitions from last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for transition in transitions:
            if transition.transition_time >= cutoff_time:
                recent_transitions.append({
                    'transition_id': transition.transition_id,
                    'from_thread': transition.from_thread,
                    'to_thread': transition.to_thread,
                    'transition_type': transition.transition_type.value,
                    'transition_time': transition.transition_time.isoformat(),
                    'quality': transition.transition_quality
                })
        
        # Sort by recency
        recent_transitions.sort(key=lambda t: t['transition_time'], reverse=True)
        
        return recent_transitions[:10]  # Return last 10 transitions
    
    def _generate_thread_id(self, user_id: str) -> str:
        """Generate a unique thread ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content = f"{user_id}_{timestamp}_{len(self.user_threads[user_id])}"
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"thread_{timestamp}_{hash_suffix}"
    
    def _generate_transition_id(self, user_id: str) -> str:
        """Generate a unique transition ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content = f"{user_id}_transition_{timestamp}"
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"trans_{timestamp}_{hash_suffix}"
    
    async def _get_thread(self, user_id: str, thread_id: str) -> Optional[ConversationThreadAdvanced]:
        """Get a specific thread for a user"""
        user_threads = self.user_threads[user_id]
        return next((thread for thread in user_threads if thread.thread_id == thread_id), None)
    
    async def _get_active_threads(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active threads for a user"""
        user_threads = self.user_threads[user_id]
        active_threads = []
        
        for thread in user_threads:
            if thread.state in [ConversationThreadState.ACTIVE, ConversationThreadState.PAUSED]:
                active_threads.append({
                    'thread_id': thread.thread_id,
                    'topic_keywords': thread.topic_keywords[:5],
                    'theme_tags': thread.theme_tags,
                    'priority_level': thread.priority_level.value,
                    'last_active': thread.last_active.isoformat(),
                    'message_count': thread.total_messages,
                    'engagement_level': thread.engagement_level
                })
        
        # Sort by priority and recency
        active_threads.sort(key=lambda t: (t['engagement_level'], t['last_active']), reverse=True)
        
        return active_threads
    
    async def _cleanup_old_threads(self, user_id: str):
        """Clean up old and inactive threads"""
        user_threads = self.user_threads[user_id]
        now = datetime.now()
        
        # Archive old threads
        for thread in user_threads:
            if thread.state not in [ConversationThreadState.ARCHIVED, ConversationThreadState.RESOLVED]:
                time_since_active = now - thread.last_active
                
                if time_since_active > self.thread_timeout:
                    thread.state = ConversationThreadState.ARCHIVED
                    logger.info("Archived inactive thread %s for user %s", thread.thread_id, user_id)
        
        # Limit active threads
        active_threads = [t for t in user_threads if t.state == ConversationThreadState.ACTIVE]
        if len(active_threads) > self.max_active_threads:
            # Sort by priority and keep top threads
            active_threads.sort(key=lambda t: (t.engagement_level, t.last_active), reverse=True)
            
            for thread in active_threads[self.max_active_threads:]:
                thread.state = ConversationThreadState.BACKGROUND
                logger.info("Moved thread %s to background for user %s", thread.thread_id, user_id)
        
        # Limit background threads
        background_threads = [t for t in user_threads if t.state == ConversationThreadState.BACKGROUND]
        if len(background_threads) > self.max_background_threads:
            background_threads.sort(key=lambda t: t.last_active)
            
            for thread in background_threads[:-self.max_background_threads]:
                thread.state = ConversationThreadState.ARCHIVED
                logger.info("Archived background thread %s for user %s", thread.thread_id, user_id)


# Supporting classes for thread analysis

class TopicSimilarityAnalyzer:
    """Analyzes topic similarity between messages and threads"""
    
    def __init__(self):
        self.similarity_cache = {}
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple implementation - could be enhanced with NLP
        cache_key = hash((text1, text2))
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # Extract and compare keywords
        keywords1 = set(self._extract_keywords(text1))
        keywords2 = set(self._extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            similarity = 0.0
        else:
            intersection = keywords1 & keywords2
            union = keywords1 | keywords2
            similarity = len(intersection) / len(union)
        
        self.similarity_cache[cache_key] = similarity
        return similarity
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        return [word for word in words if len(word) > 2 and word not in stop_words]


class TransitionDetector:
    """Detects conversation transitions and classifies them"""
    
    def __init__(self):
        self.transition_patterns = self._load_transition_patterns()
    
    def _load_transition_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for different transition types"""
        return {
            'explicit': ['anyway', 'by the way', 'speaking of', 'changing topics'],
            'temporal': ['now', 'then', 'next', 'meanwhile', 'earlier', 'later'],
            'causal': ['because', 'since', 'therefore', 'as a result'],
            'additive': ['also', 'furthermore', 'additionally', 'moreover'],
            'contrastive': ['however', 'but', 'although', 'on the other hand']
        }
    
    async def detect_transition(self, message: str) -> Dict[str, Any]:
        """Detect if message contains transition indicators"""
        text_lower = message.lower()
        
        detected_patterns = {}
        for category, patterns in self.transition_patterns.items():
            found_patterns = [p for p in patterns if p in text_lower]
            if found_patterns:
                detected_patterns[category] = found_patterns
        
        return {
            'has_transition': bool(detected_patterns),
            'patterns': detected_patterns,
            'strength': len(detected_patterns) / len(self.transition_patterns)
        }


class ThreadPriorityCalculator:
    """Calculates thread priorities based on multiple factors"""
    
    def __init__(self):
        self.priority_weights = {
            'emotional_urgency': 0.3,
            'time_sensitivity': 0.25,
            'user_engagement': 0.2,
            'relationship_importance': 0.15,
            'completion_status': 0.1
        }
    
    async def calculate_priority(self, thread: ConversationThreadAdvanced) -> float:
        """Calculate priority score for a thread"""
        factors = {
            'emotional_urgency': thread.emotional_urgency,
            'time_sensitivity': thread.time_sensitivity,
            'user_engagement': thread.engagement_level,
            'relationship_importance': self._assess_relationship_importance(thread),
            'completion_status': 1.0 - thread.completion_status
        }
        
        weighted_score = sum(
            factors[factor] * weight 
            for factor, weight in self.priority_weights.items()
        )
        
        return min(1.0, weighted_score)
    
    def _assess_relationship_importance(self, thread: ConversationThreadAdvanced) -> float:
        """Assess the relationship importance of a thread"""
        # Simple implementation - could be enhanced
        important_themes = ['relationships', 'health', 'work', 'family']
        theme_importance = sum(0.2 for theme in thread.theme_tags if theme in important_themes)
        
        return min(1.0, theme_importance + thread.trust_level_at_start)


# Convenience function for easy integration
async def create_advanced_conversation_thread_manager(
    emotional_context_engine=None,
    personality_profiler=None,
    memory_moments=None,
    memory_manager=None
) -> AdvancedConversationThreadManager:
    """
    Create and initialize an advanced conversation thread manager.
    
    Returns:
        AdvancedConversationThreadManager ready for use
    """
    if not EMOTIONAL_CONTEXT_AVAILABLE:
        logger.warning("EmotionalContextEngine not available - limited emotional integration")
    
    if not PERSONALITY_PROFILER_AVAILABLE:
        logger.warning("DynamicPersonalityProfiler not available - limited personality integration")
    
    if not MEMORY_MOMENTS_AVAILABLE:
        logger.warning("MemoryTriggeredMoments not available - limited memory integration")
    
    manager = AdvancedConversationThreadManager(
        emotional_context_engine=emotional_context_engine,
        personality_profiler=personality_profiler,
        memory_moments=memory_moments,
        memory_manager=memory_manager
    )
    
    logger.info("AdvancedConversationThreadManager created successfully")
    return manager