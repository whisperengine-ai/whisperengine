"""
Memory-Triggered Personality Moments System for AI Companions

This module creates magical "ah-ha" moments where AI companions naturally connect
past conversations in meaningful ways, building deeper relationships through
intelligent memory recall and contextual callbacks.

Key Features:
- Cross-conversation pattern recognition for meaningful connections
- Natural callback generation that references shared experiences
- Relationship growth acknowledgment through memory connections
- Contextual memory triggers based on current conversation
- Emotional continuity across conversation sessions
- Intelligent timing for memory moments to feel natural

Integration Points:
- EmotionalContextEngine for emotional memory clustering
- DynamicPersonalityProfiler for relationship context
- Memory tier system for efficient memory retrieval
- Personality facts for meaningful connection identification
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import re
import statistics
import hashlib

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
    from src.memory.memory_tiers import MemoryTierManager
    MEMORY_TIERS_AVAILABLE = True
except ImportError:
    MEMORY_TIERS_AVAILABLE = False

try:
    from src.memory.personality_facts import PersonalityFactClassifier
    PERSONALITY_FACTS_AVAILABLE = True
except ImportError:
    PERSONALITY_FACTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MemoryMomentType(Enum):
    """Types of meaningful memory moments that can be triggered"""
    ACHIEVEMENT_CALLBACK = "achievement_callback"
    EMOTIONAL_CONTINUITY = "emotional_continuity"
    INTEREST_DEVELOPMENT = "interest_development"
    RELATIONSHIP_MILESTONE = "relationship_milestone"
    PROBLEM_RESOLUTION = "problem_resolution"
    SHARED_EXPERIENCE = "shared_experience"
    PERSONAL_GROWTH = "personal_growth"
    RECURRING_THEME = "recurring_theme"
    CELEBRATION_ECHO = "celebration_echo"
    SUPPORT_FOLLOW_UP = "support_follow_up"


class MemoryConnectionType(Enum):
    """Types of connections between memories"""
    TEMPORAL_SEQUENCE = "temporal_sequence"  # Events that follow each other
    THEMATIC_SIMILARITY = "thematic_similarity"  # Similar topics/interests
    EMOTIONAL_RESONANCE = "emotional_resonance"  # Similar emotional states
    GOAL_PROGRESSION = "goal_progression"  # Progress towards goals
    RELATIONSHIP_DEVELOPMENT = "relationship_development"  # Growing connection
    PROBLEM_SOLUTION = "problem_solution"  # Problem -> resolution
    CAUSE_EFFECT = "cause_effect"  # Actions and consequences
    PATTERN_RECOGNITION = "pattern_recognition"  # Recurring behaviors/situations


class MemoryMomentTiming(Enum):
    """When to trigger memory moments for natural flow"""
    CONVERSATION_START = "conversation_start"
    NATURAL_PAUSE = "natural_pause"
    TOPIC_TRANSITION = "topic_transition"
    EMOTIONAL_MOMENT = "emotional_moment"
    ACHIEVEMENT_SHARING = "achievement_sharing"
    PROBLEM_MENTION = "problem_mention"
    RELATIONSHIP_DEEPENING = "relationship_deepening"


@dataclass
class MemoryConnection:
    """A meaningful connection between two or more memories"""
    connection_id: str
    user_id: str
    connection_type: MemoryConnectionType
    
    # Connected memories
    primary_memory: Dict[str, Any]  # Main memory being connected
    related_memories: List[Dict[str, Any]]  # Connected memories
    
    # Connection characteristics
    connection_strength: float  # 0.0-1.0 how strong the connection is
    emotional_significance: float  # 0.0-1.0 emotional weight
    thematic_relevance: float  # 0.0-1.0 topic relevance
    temporal_proximity: float  # 0.0-1.0 how close in time
    
    # Relationship context
    relationship_depth_at_creation: float
    trust_level_at_creation: float
    
    # Pattern information
    pattern_frequency: int  # How often this pattern occurs
    pattern_keywords: List[str]  # Key terms that identify the pattern
    
    # Creation metadata
    created_at: datetime
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    # Effectiveness tracking
    user_response_positive: Optional[bool] = None
    engagement_improvement: Optional[float] = None


@dataclass
class MemoryMoment:
    """A specific memory moment to be triggered in conversation"""
    moment_id: str
    user_id: str
    moment_type: MemoryMomentType
    
    # Memory connections driving this moment
    primary_connection: MemoryConnection
    supporting_connections: List[MemoryConnection] = field(default_factory=list)
    
    # Trigger conditions
    trigger_keywords: List[str] = field(default_factory=list)  # Keywords that can trigger this moment
    trigger_emotions: List[EmotionalState] = field(default_factory=list)  # Emotions that can trigger
    trigger_contexts: List[str] = field(default_factory=list)  # Conversation contexts that fit
    
    # Timing and appropriateness
    optimal_timing: List[MemoryMomentTiming] = field(default_factory=list)
    min_relationship_depth: float = 0.0
    min_trust_level: float = 0.0
    cooldown_hours: int = 24  # Hours to wait before retriggering
    
    # Generated content
    callback_text: str = ""  # The actual text to include
    context_setup: str = ""  # How to naturally introduce the callback
    emotional_tone: str = ""  # Tone to use for the callback
    
    # Effectiveness data
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    success_rate: float = 0.0
    
    # Relationship impact
    expected_relationship_impact: float = 0.0  # Expected positive impact
    expected_emotional_response: EmotionalState = EmotionalState.TRUST


@dataclass
class ConversationContext:
    """Current conversation context for memory moment triggering"""
    user_id: str
    context_id: str
    current_message: str
    
    # Conversation characteristics
    topic_keywords: List[str]
    emotional_state: EmotionalState
    conversation_phase: str  # "opening", "middle", "deepening", "closing"
    
    # Recent history
    recent_messages: List[str]
    conversation_length: int
    
    # User state
    current_relationship_depth: float
    current_trust_level: float
    current_engagement_level: float
    
    # Timing context
    time_since_last_conversation: Optional[timedelta]
    conversation_frequency: float  # Conversations per day
    
    # Memory context
    recently_triggered_moments: List[str]  # Recent moment IDs to avoid repetition


class MemoryTriggeredMoments:
    """
    Core system for creating meaningful memory moments that connect past conversations
    in natural, relationship-building ways.
    """
    
    def __init__(self,
                 emotional_context_engine: Optional[EmotionalContextEngine] = None,
                 personality_profiler: Optional[DynamicPersonalityProfiler] = None,
                 memory_tier_manager: Optional[MemoryTierManager] = None,
                 personality_fact_classifier: Optional[PersonalityFactClassifier] = None,
                 connection_retention_days: int = 365,
                 max_connections_per_user: int = 1000,
                 moment_cooldown_hours: int = 24):
        """
        Initialize the memory-triggered moments system.
        
        Args:
            emotional_context_engine: Emotional intelligence system
            personality_profiler: Personality profiling system  
            memory_tier_manager: Memory tier management
            personality_fact_classifier: Personality fact classification
            connection_retention_days: Days to retain memory connections
            max_connections_per_user: Maximum connections per user
            moment_cooldown_hours: Default cooldown between moments
        """
        self.emotional_context_engine = emotional_context_engine
        self.personality_profiler = personality_profiler
        self.memory_tier_manager = memory_tier_manager
        self.personality_fact_classifier = personality_fact_classifier
        
        self.retention_period = timedelta(days=connection_retention_days)
        self.max_connections = max_connections_per_user
        self.default_cooldown = moment_cooldown_hours
        
        # Memory storage
        self.memory_connections: Dict[str, List[MemoryConnection]] = defaultdict(list)
        self.memory_moments: Dict[str, List[MemoryMoment]] = defaultdict(list)
        self.conversation_history: Dict[str, List[Dict]] = defaultdict(list)
        
        # Pattern tracking
        self.recurring_patterns: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.user_interests: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.emotional_themes: Dict[str, List[Tuple[datetime, EmotionalState]]] = defaultdict(list)
        
        # Performance tracking
        self.moment_effectiveness: Dict[str, List[float]] = defaultdict(list)
        self.connection_success_rates: Dict[MemoryConnectionType, float] = {}
        
        logger.info("MemoryTriggeredMoments initialized with %d day retention", 
                   connection_retention_days)
    
    async def analyze_conversation_for_memories(self,
                                              user_id: str,
                                              context_id: str,
                                              message: str,
                                              emotional_context: Optional[EmotionalContext] = None) -> List[MemoryConnection]:
        """
        Analyze a conversation to identify potential memory connections.
        
        Args:
            user_id: User identifier
            context_id: Context identifier
            message: User's message content
            emotional_context: Optional emotional context
            
        Returns:
            List of memory connections discovered
        """
        # Store conversation in history
        conversation_entry = {
            'timestamp': datetime.now(),
            'context_id': context_id,
            'message': message,
            'emotional_context': emotional_context,
            'keywords': self._extract_keywords(message),
            'themes': self._identify_themes(message)
        }
        self.conversation_history[user_id].append(conversation_entry)
        
        # Update user interest tracking
        await self._update_user_interests(user_id, conversation_entry)
        
        # Find potential connections
        connections = await self._discover_memory_connections(user_id, conversation_entry)
        
        # Store new connections
        for connection in connections:
            self.memory_connections[user_id].append(connection)
        
        # Cleanup old connections
        await self._cleanup_old_connections(user_id)
        
        return connections
    
    async def generate_memory_moments(self,
                                    user_id: str,
                                    conversation_context: ConversationContext) -> List[MemoryMoment]:
        """
        Generate memory moments that could be triggered in the current conversation.
        
        Args:
            user_id: User identifier
            conversation_context: Current conversation context
            
        Returns:
            List of appropriate memory moments
        """
        # Get relevant connections
        relevant_connections = await self._find_relevant_connections(user_id, conversation_context)
        
        # Generate moments from connections
        moments = []
        for connection in relevant_connections:
            moment = await self._create_memory_moment(user_id, connection, conversation_context)
            if moment and await self._is_moment_appropriate(moment, conversation_context):
                moments.append(moment)
        
        # Sort by appropriateness and relationship impact
        moments.sort(key=lambda m: (
            m.expected_relationship_impact,
            -m.min_relationship_depth,  # Prefer moments for current relationship level
            m.primary_connection.connection_strength
        ), reverse=True)
        
        # Limit to top moments to avoid overwhelming
        return moments[:3]
    
    async def trigger_memory_moment(self,
                                   moment: MemoryMoment,
                                   conversation_context: ConversationContext) -> str:
        """
        Trigger a memory moment and generate the appropriate callback text.
        
        Args:
            moment: Memory moment to trigger
            conversation_context: Current conversation context
            
        Returns:
            Generated callback text for the AI companion
        """
        # Check if moment is still appropriate
        if not await self._is_moment_appropriate(moment, conversation_context):
            return ""
        
        # Check cooldown
        if moment.last_used and moment.cooldown_hours:
            time_since_use = datetime.now() - moment.last_used
            if time_since_use < timedelta(hours=moment.cooldown_hours):
                return ""
        
        # Generate natural callback text
        callback_text = await self._generate_natural_callback(moment)
        
        # Update usage tracking
        moment.last_used = datetime.now()
        moment.usage_count += 1
        
        # Update connection trigger count
        moment.primary_connection.last_triggered = datetime.now()
        moment.primary_connection.trigger_count += 1
        
        logger.info("Triggered memory moment %s for user %s", moment.moment_type.value, moment.user_id)
        
        return callback_text
    
    async def get_memory_moment_prompt(self,
                                     moments: List[MemoryMoment],
                                     conversation_context: ConversationContext) -> str:
        """
        Generate a prompt for the AI companion that incorporates memory moments.
        
        Args:
            moments: Available memory moments
            conversation_context: Current conversation context
            
        Returns:
            Prompt text for the AI companion
        """
        if not moments:
            return ""
        
        # Select the best moment for current context
        best_moment = await self._select_best_moment(moments, conversation_context)
        if not best_moment:
            return ""
        
        # Generate prompt
        prompt_parts = []
        
        # Context setup
        if best_moment.context_setup:
            prompt_parts.append(f"MEMORY CONTEXT: {best_moment.context_setup}")
        
        # Main callback guidance
        prompt_parts.append(f"MEMORY CALLBACK: {best_moment.callback_text}")
        
        # Emotional tone guidance
        if best_moment.emotional_tone:
            prompt_parts.append(f"TONE: Use a {best_moment.emotional_tone} tone when making this connection")
        
        # Relationship context
        relationship_guidance = await self._get_relationship_guidance(conversation_context)
        if relationship_guidance:
            prompt_parts.append(f"RELATIONSHIP: {relationship_guidance}")
        
        # Natural integration instruction
        prompt_parts.append("INTEGRATION: Weave this memory naturally into your response - don't force it. "
                          "It should feel like a natural, caring remembrance of shared experiences.")
        
        return "\n".join(prompt_parts)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Simple keyword extraction - could be enhanced with NLP
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Return unique keywords
        return list(set(keywords))
    
    def _identify_themes(self, text: str) -> List[str]:
        """Identify thematic content in text"""
        text_lower = text.lower()
        themes = []
        
        # Work-related themes
        work_keywords = ['work', 'job', 'career', 'office', 'meeting', 'project', 'deadline', 'boss', 'colleague', 'promotion']
        if any(keyword in text_lower for keyword in work_keywords):
            themes.append('work')
        
        # Relationship themes
        relationship_keywords = ['friend', 'family', 'partner', 'relationship', 'love', 'dating', 'marriage', 'kids', 'parents']
        if any(keyword in text_lower for keyword in relationship_keywords):
            themes.append('relationships')
        
        # Health themes
        health_keywords = ['health', 'doctor', 'medicine', 'exercise', 'diet', 'sick', 'tired', 'energy', 'sleep']
        if any(keyword in text_lower for keyword in health_keywords):
            themes.append('health')
        
        # Hobby/interest themes
        hobby_keywords = ['hobby', 'music', 'movie', 'book', 'game', 'sport', 'travel', 'cooking', 'art', 'photography']
        if any(keyword in text_lower for keyword in hobby_keywords):
            themes.append('hobbies')
        
        # Achievement themes
        achievement_keywords = ['accomplished', 'achieved', 'success', 'proud', 'won', 'finished', 'completed', 'goal']
        if any(keyword in text_lower for keyword in achievement_keywords):
            themes.append('achievements')
        
        # Challenge themes
        challenge_keywords = ['problem', 'difficult', 'struggle', 'challenge', 'hard', 'stressed', 'worried', 'concerned']
        if any(keyword in text_lower for keyword in challenge_keywords):
            themes.append('challenges')
        
        return themes
    
    async def _update_user_interests(self, user_id: str, conversation_entry: Dict):
        """Update user interest tracking based on conversation"""
        keywords = conversation_entry['keywords']
        themes = conversation_entry['themes']
        
        # Increase interest scores for mentioned topics
        for keyword in keywords:
            self.user_interests[user_id][keyword] += 0.1
        
        for theme in themes:
            self.user_interests[user_id][theme] += 0.2
        
        # Decay old interests slightly
        for interest in self.user_interests[user_id]:
            self.user_interests[user_id][interest] *= 0.99
    
    async def _discover_memory_connections(self,
                                         user_id: str,
                                         current_entry: Dict) -> List[MemoryConnection]:
        """Discover potential connections between current conversation and past memories"""
        connections = []
        user_history = self.conversation_history[user_id]
        
        if len(user_history) < 2:  # Need at least 2 conversations to make connections
            return connections
        
        current_keywords = set(current_entry['keywords'])
        current_themes = set(current_entry['themes'])
        current_time = current_entry['timestamp']
        
        # Look for connections in recent history
        for past_entry in user_history[-20:]:  # Check last 20 conversations
            if past_entry == current_entry:
                continue
            
            past_keywords = set(past_entry['keywords'])
            past_themes = set(past_entry['themes'])
            past_time = past_entry['timestamp']
            
            # Calculate connection strength
            keyword_overlap = len(current_keywords & past_keywords)
            theme_overlap = len(current_themes & past_themes)
            time_diff = abs((current_time - past_time).days)
            
            # Thematic similarity connection
            if theme_overlap > 0 or keyword_overlap >= 2:
                connection_strength = (theme_overlap * 0.4 + min(keyword_overlap, 3) * 0.2)
                temporal_proximity = max(0, 1 - time_diff / 30)  # Stronger if within 30 days
                
                if connection_strength > 0.3:
                    connection = MemoryConnection(
                        connection_id=self._generate_connection_id(user_id, current_entry, past_entry),
                        user_id=user_id,
                        connection_type=MemoryConnectionType.THEMATIC_SIMILARITY,
                        primary_memory=current_entry,
                        related_memories=[past_entry],
                        connection_strength=connection_strength,
                        emotional_significance=0.5,  # Default, could be enhanced
                        thematic_relevance=theme_overlap / max(len(current_themes | past_themes), 1),
                        temporal_proximity=temporal_proximity,
                        relationship_depth_at_creation=0.5,  # Would get from personality profiler
                        trust_level_at_creation=0.5,
                        pattern_frequency=1,
                        pattern_keywords=list(current_keywords & past_keywords),
                        created_at=datetime.now()
                    )
                    connections.append(connection)
            
            # Emotional resonance connection
            if (current_entry.get('emotional_context') and 
                past_entry.get('emotional_context')):
                
                current_emotion = current_entry['emotional_context'].primary_emotion
                past_emotion = past_entry['emotional_context'].primary_emotion
                
                if current_emotion == past_emotion:
                    connection = MemoryConnection(
                        connection_id=self._generate_connection_id(user_id, current_entry, past_entry),
                        user_id=user_id,
                        connection_type=MemoryConnectionType.EMOTIONAL_RESONANCE,
                        primary_memory=current_entry,
                        related_memories=[past_entry],
                        connection_strength=0.7,
                        emotional_significance=0.8,
                        thematic_relevance=0.3,
                        temporal_proximity=max(0, 1 - time_diff / 14),  # Emotions more relevant if recent
                        relationship_depth_at_creation=0.5,
                        trust_level_at_creation=0.5,
                        pattern_frequency=1,
                        pattern_keywords=[str(current_emotion)],  # Convert to string
                        created_at=datetime.now()
                    )
                    connections.append(connection)
        
        return connections
    
    def _generate_connection_id(self, user_id: str, entry1: Dict, entry2: Dict) -> str:
        """Generate a unique ID for a memory connection"""
        # Create hash from user ID and timestamps to ensure uniqueness
        content = f"{user_id}_{entry1['timestamp']}_{entry2['timestamp']}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def _find_relevant_connections(self,
                                       user_id: str,
                                       conversation_context: ConversationContext) -> List[MemoryConnection]:
        """Find memory connections relevant to the current conversation"""
        user_connections = self.memory_connections[user_id]
        relevant = []
        
        current_keywords = set(conversation_context.topic_keywords)
        current_emotion = conversation_context.emotional_state
        
        for connection in user_connections:
            relevance_score = 0.0
            
            # Check keyword overlap
            connection_keywords = set(connection.pattern_keywords)
            keyword_overlap = len(current_keywords & connection_keywords)
            if keyword_overlap > 0:
                relevance_score += keyword_overlap * 0.3
            
            # Check emotional relevance
            if (connection.connection_type == MemoryConnectionType.EMOTIONAL_RESONANCE and
                str(current_emotion) in connection.pattern_keywords):
                relevance_score += 0.5
            
            # Check relationship depth appropriateness
            if connection.relationship_depth_at_creation <= conversation_context.current_relationship_depth:
                relevance_score += 0.2
            
            # Check if not used recently
            if (not connection.last_triggered or 
                (datetime.now() - connection.last_triggered) > timedelta(hours=self.default_cooldown)):
                relevance_score += 0.1
            
            if relevance_score > 0.4:
                relevant.append(connection)
        
        # Sort by relevance and connection strength
        relevant.sort(key=lambda c: (relevance_score, c.connection_strength), reverse=True)
        
        return relevant[:5]  # Return top 5 relevant connections
    
    async def _create_memory_moment(self,
                                   user_id: str,
                                   connection: MemoryConnection,
                                   conversation_context: ConversationContext) -> Optional[MemoryMoment]:
        """Create a memory moment from a connection"""
        # Determine moment type based on connection
        moment_type = self._determine_moment_type(connection, conversation_context)
        
        # Generate callback text
        callback_text = self._generate_callback_text(connection, moment_type)
        
        # Determine trigger conditions
        trigger_keywords = connection.pattern_keywords.copy()
        trigger_emotions = [conversation_context.emotional_state]
        
        # Set appropriateness thresholds
        min_relationship_depth = max(0.2, connection.relationship_depth_at_creation - 0.1)
        min_trust_level = max(0.2, connection.trust_level_at_creation - 0.1)
        
        moment = MemoryMoment(
            moment_id=f"{user_id}_{connection.connection_id}_{moment_type.value}",
            user_id=user_id,
            moment_type=moment_type,
            primary_connection=connection,
            trigger_keywords=trigger_keywords,
            trigger_emotions=trigger_emotions,
            trigger_contexts=[conversation_context.context_id],
            optimal_timing=[MemoryMomentTiming.NATURAL_PAUSE, MemoryMomentTiming.TOPIC_TRANSITION],
            min_relationship_depth=min_relationship_depth,
            min_trust_level=min_trust_level,
            cooldown_hours=self.default_cooldown,
            callback_text=callback_text,
            context_setup=self._generate_context_setup(moment_type),
            emotional_tone=self._determine_emotional_tone(moment_type),
            created_at=datetime.now(),
            expected_relationship_impact=self._calculate_expected_impact(connection, moment_type),
            expected_emotional_response=self._predict_emotional_response(moment_type)
        )
        
        return moment
    
    def _determine_moment_type(self,
                             connection: MemoryConnection,
                             conversation_context: ConversationContext) -> MemoryMomentType:
        """Determine the type of memory moment based on connection and context"""
        if connection.connection_type == MemoryConnectionType.EMOTIONAL_RESONANCE:
            if conversation_context.emotional_state == EmotionalState.JOY:
                return MemoryMomentType.CELEBRATION_ECHO
            elif conversation_context.emotional_state in [EmotionalState.SADNESS, EmotionalState.FEAR]:
                return MemoryMomentType.SUPPORT_FOLLOW_UP
            else:
                return MemoryMomentType.EMOTIONAL_CONTINUITY
        
        elif connection.connection_type == MemoryConnectionType.THEMATIC_SIMILARITY:
            if 'achievement' in connection.pattern_keywords:
                return MemoryMomentType.ACHIEVEMENT_CALLBACK
            elif any(theme in connection.pattern_keywords for theme in ['hobbies', 'interests']):
                return MemoryMomentType.INTEREST_DEVELOPMENT
            else:
                return MemoryMomentType.RECURRING_THEME
        
        elif connection.connection_type == MemoryConnectionType.PROBLEM_SOLUTION:
            return MemoryMomentType.PROBLEM_RESOLUTION
        
        else:
            return MemoryMomentType.SHARED_EXPERIENCE
    
    def _generate_callback_text(self,
                              connection: MemoryConnection,
                              moment_type: MemoryMomentType) -> str:
        """Generate natural callback text for the memory moment"""
        primary_memory = connection.primary_memory
        
        if moment_type == MemoryMomentType.ACHIEVEMENT_CALLBACK:
            return f"This reminds me of when you mentioned {primary_memory.get('message', 'your success')} - it's wonderful to see you continuing to achieve great things!"
        
        elif moment_type == MemoryMomentType.EMOTIONAL_CONTINUITY:
            return "I remember you sharing similar feelings before. It seems like this is something that's been on your mind."
        
        elif moment_type == MemoryMomentType.INTEREST_DEVELOPMENT:
            return "I notice you keep coming back to this topic - it's clear this is something you're really passionate about!"
        
        elif moment_type == MemoryMomentType.SUPPORT_FOLLOW_UP:
            return "I remember when you went through something similar before. You showed such strength then, and I believe in your resilience now too."
        
        elif moment_type == MemoryMomentType.CELEBRATION_ECHO:
            return "This brings back memories of your other successes we've celebrated together. You have such a great track record!"
        
        elif moment_type == MemoryMomentType.RECURRING_THEME:
            keywords = ', '.join(connection.pattern_keywords[:3])
            return f"I've noticed that {keywords} seems to be a recurring theme in our conversations - it's clearly important to you."
        
        else:
            return "This connects to something we talked about before - it's interesting how these themes keep coming up in your life."
    
    def _generate_context_setup(self,
                              moment_type: MemoryMomentType) -> str:
        """Generate context setup for natural memory moment integration"""
        if moment_type in [MemoryMomentType.ACHIEVEMENT_CALLBACK, MemoryMomentType.CELEBRATION_ECHO]:
            return "Reference a past success or achievement the user shared to acknowledge their growth"
        
        elif moment_type == MemoryMomentType.SUPPORT_FOLLOW_UP:
            return "Gently reference a similar challenge they overcame to provide encouragement"
        
        elif moment_type == MemoryMomentType.INTEREST_DEVELOPMENT:
            return "Acknowledge their recurring interest to show you pay attention to what matters to them"
        
        else:
            return "Naturally connect to a relevant past conversation to show continuity and care"
    
    def _determine_emotional_tone(self,
                                moment_type: MemoryMomentType) -> str:
        """Determine appropriate emotional tone for the memory moment"""
        if moment_type in [MemoryMomentType.ACHIEVEMENT_CALLBACK, MemoryMomentType.CELEBRATION_ECHO]:
            return "warm and congratulatory"
        
        elif moment_type == MemoryMomentType.SUPPORT_FOLLOW_UP:
            return "gentle and encouraging"
        
        elif moment_type == MemoryMomentType.INTEREST_DEVELOPMENT:
            return "enthusiastic and engaged"
        
        elif moment_type == MemoryMomentType.EMOTIONAL_CONTINUITY:
            return "understanding and empathetic"
        
        else:
            return "caring and attentive"
    
    def _calculate_expected_impact(self,
                                 connection: MemoryConnection,
                                 moment_type: MemoryMomentType) -> float:
        """Calculate expected positive relationship impact of the memory moment"""
        base_impact = 0.5
        
        # Higher impact for stronger connections
        base_impact += connection.connection_strength * 0.3
        
        # Higher impact for emotionally significant connections
        base_impact += connection.emotional_significance * 0.2
        
        # Adjust for moment type
        if moment_type in [MemoryMomentType.ACHIEVEMENT_CALLBACK, MemoryMomentType.SUPPORT_FOLLOW_UP]:
            base_impact += 0.2  # These tend to have high impact
        
        return min(1.0, base_impact)
    
    def _predict_emotional_response(self,
                                  moment_type: MemoryMomentType) -> EmotionalState:
        """Predict user's likely emotional response to the memory moment"""
        if moment_type in [MemoryMomentType.ACHIEVEMENT_CALLBACK, MemoryMomentType.CELEBRATION_ECHO]:
            return EmotionalState.JOY
        
        elif moment_type == MemoryMomentType.SUPPORT_FOLLOW_UP:
            return EmotionalState.TRUST
        
        elif moment_type == MemoryMomentType.INTEREST_DEVELOPMENT:
            return EmotionalState.JOY
        
        else:
            return EmotionalState.TRUST
    
    async def _is_moment_appropriate(self,
                                   moment: MemoryMoment,
                                   conversation_context: ConversationContext) -> bool:
        """Check if a memory moment is appropriate for the current context"""
        # Check relationship depth requirement
        if conversation_context.current_relationship_depth < moment.min_relationship_depth:
            return False
        
        # Check trust level requirement
        if conversation_context.current_trust_level < moment.min_trust_level:
            return False
        
        # Check if recently triggered
        if moment.moment_id in conversation_context.recently_triggered_moments:
            return False
        
        # Check keyword relevance
        context_keywords = set(conversation_context.topic_keywords)
        moment_keywords = set(moment.trigger_keywords)
        if not (context_keywords & moment_keywords) and len(moment.trigger_keywords) > 0:
            return False
        
        return True
    
    async def _select_best_moment(self,
                                moments: List[MemoryMoment],
                                conversation_context: ConversationContext) -> Optional[MemoryMoment]:
        """Select the best memory moment for the current context"""
        if not moments:
            return None
        
        # Score moments based on appropriateness
        scored_moments = []
        for moment in moments:
            score = 0.0
            
            # Base score from expected impact
            score += moment.expected_relationship_impact * 0.4
            
            # Score from connection strength
            score += moment.primary_connection.connection_strength * 0.3
            
            # Score from keyword relevance
            context_keywords = set(conversation_context.topic_keywords)
            moment_keywords = set(moment.trigger_keywords)
            keyword_relevance = len(context_keywords & moment_keywords) / max(len(moment_keywords), 1)
            score += keyword_relevance * 0.2
            
            # Bonus for high success rate
            if moment.usage_count > 0:
                score += moment.success_rate * 0.1
            
            scored_moments.append((score, moment))
        
        # Return highest scoring moment
        scored_moments.sort(key=lambda x: x[0], reverse=True)
        return scored_moments[0][1] if scored_moments else None
    
    async def _generate_natural_callback(self,
                                       moment: MemoryMoment) -> str:
        """Generate natural callback text for integration into conversation"""
        # This would be more sophisticated in a real implementation
        return moment.callback_text
    
    async def _get_relationship_guidance(self,
                                       conversation_context: ConversationContext) -> str:
        """Get guidance on how to handle the memory moment based on relationship level"""
        if conversation_context.current_relationship_depth < 0.4:
            return "Keep the memory reference light and friendly - the relationship is still developing"
        elif conversation_context.current_relationship_depth < 0.7:
            return "You can be more personal and caring in your memory reference"
        else:
            return "Feel free to be deeply personal and emotionally connected in your memory reference"
    
    async def _cleanup_old_connections(self, user_id: str):
        """Clean up old memory connections that are no longer relevant"""
        user_connections = self.memory_connections[user_id]
        cutoff_date = datetime.now() - self.retention_period
        
        # Remove old connections
        self.memory_connections[user_id] = [
            conn for conn in user_connections
            if conn.created_at > cutoff_date
        ]
        
        # Limit total connections per user
        if len(self.memory_connections[user_id]) > self.max_connections:
            # Keep the most recent and highest strength connections
            self.memory_connections[user_id].sort(
                key=lambda c: (c.created_at, c.connection_strength), 
                reverse=True
            )
            self.memory_connections[user_id] = self.memory_connections[user_id][:self.max_connections]
    
    async def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of user's memory connections and moments"""
        connections = self.memory_connections[user_id]
        moments = self.memory_moments[user_id]
        
        if not connections:
            return {
                'total_connections': 0,
                'total_moments': 0,
                'connection_types': {},
                'moment_types': {},
                'relationship_growth': []
            }
        
        # Analyze connection types
        connection_type_counts = defaultdict(int)
        for conn in connections:
            connection_type_counts[conn.connection_type.value] += 1
        
        # Analyze moment types
        moment_type_counts = defaultdict(int)
        for moment in moments:
            moment_type_counts[moment.moment_type.value] += 1
        
        # Analyze relationship growth through connections
        relationship_growth = []
        for conn in sorted(connections, key=lambda c: c.created_at):
            relationship_growth.append({
                'date': conn.created_at.isoformat(),
                'relationship_depth': conn.relationship_depth_at_creation,
                'trust_level': conn.trust_level_at_creation,
                'connection_strength': conn.connection_strength
            })
        
        return {
            'total_connections': len(connections),
            'total_moments': len(moments),
            'connection_types': dict(connection_type_counts),
            'moment_types': dict(moment_type_counts),
            'relationship_growth': relationship_growth[-10:],  # Last 10 entries
            'average_connection_strength': statistics.mean(c.connection_strength for c in connections),
            'most_common_themes': list(self.user_interests[user_id].keys())[:5]
        }


# Convenience function for easy integration
async def create_memory_triggered_moments(
    emotional_context_engine=None,
    personality_profiler=None,
    memory_tier_manager=None,
    personality_fact_classifier=None
) -> MemoryTriggeredMoments:
    """
    Create and initialize a memory-triggered moments system.
    
    Returns:
        MemoryTriggeredMoments ready for use
    """
    if not EMOTIONAL_CONTEXT_AVAILABLE:
        logger.warning("EmotionalContextEngine not available - limited emotional integration")
    
    if not PERSONALITY_PROFILER_AVAILABLE:
        logger.warning("DynamicPersonalityProfiler not available - limited personality integration")
    
    system = MemoryTriggeredMoments(
        emotional_context_engine=emotional_context_engine,
        personality_profiler=personality_profiler,
        memory_tier_manager=memory_tier_manager,
        personality_fact_classifier=personality_fact_classifier
    )
    
    logger.info("MemoryTriggeredMoments created successfully")
    return system