"""
Enhanced 7-Dimensional Vector Analysis Components

This module provides the intelligence analysis components for the enhanced 7D vector system:
- RelationshipAnalyzer: Intimacy and trust level analysis
- PersonalityAnalyzer: Character trait prominence detection
- InteractionAnalyzer: Communication style and mode classification
- TemporalAnalyzer: Conversation flow and timing patterns
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class IntimacyLevel(Enum):
    """Intimacy levels for relationship analysis"""
    CASUAL = "casual"
    PERSONAL = "personal"
    DEEP = "deep"
    INTIMATE = "intimate"


class TrustLevel(Enum):
    """Trust levels for relationship analysis"""
    SKEPTICAL = "skeptical"
    NEUTRAL = "neutral"
    TRUSTING = "trusting"
    CONFIDENTIAL = "confidential"


class CommunicationStyle(Enum):
    """Communication style patterns"""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    SUPPORTIVE = "supportive"
    CASUAL = "casual"
    FORMAL = "formal"
    PLAYFUL = "playful"
    SERIOUS = "serious"


class ConversationMode(Enum):
    """Conversation mode types"""
    CRISIS_SUPPORT = "crisis_support"
    EDUCATIONAL = "educational"
    EMOTIONAL_SUPPORT = "emotional_support"
    CREATIVE_COLLABORATION = "creative_collaboration"
    PROBLEM_SOLVING = "problem_solving"
    CASUAL_CHAT = "casual_chat"
    PLAYFUL = "playful"
    SERIOUS = "serious"


class ConversationPhase(Enum):
    """Conversation flow phases"""
    OPENING = "opening"
    BUILDING = "building"
    MIDDLE = "middle"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    FOLLOWUP = "followup"


class ConversationRhythm(Enum):
    """Conversation rhythm patterns"""
    QUICK_EXCHANGE = "quick_exchange"
    THOUGHTFUL_PACED = "thoughtful_paced"
    DEEP_EXPLORATION = "deep_exploration"
    CASUAL_FLOW = "casual_flow"


@dataclass
class RelationshipContext:
    """Relationship analysis result"""
    intimacy_level: IntimacyLevel
    trust_level: TrustLevel
    confidence_score: float
    indicators: List[str]


@dataclass
class PersonalityContext:
    """Personality analysis result"""
    primary_traits: List[str]
    trait_confidence: Dict[str, float]
    character_alignment: float
    prominence_indicators: List[str]


@dataclass
class InteractionContext:
    """Interaction analysis result"""
    communication_style: CommunicationStyle
    conversation_mode: ConversationMode
    style_confidence: float
    mode_confidence: float
    interaction_indicators: List[str]


@dataclass
@dataclass
class TemporalContext:
    """Temporal analysis result"""
    conversation_phase: ConversationPhase
    conversation_rhythm: ConversationRhythm
    phase_confidence: float
    rhythm_confidence: float
    flow_indicators: List[str]
    flow_optimization_hints: List[str] = field(default_factory=list)


class RelationshipAnalyzer:
    """Analyzes relationship intimacy and trust levels"""
    
    def __init__(self):
        self.intimacy_keywords = {
            IntimacyLevel.INTIMATE: [
                'love', 'relationship', 'feelings', 'heart', 'soul', 'deep connection',
                'romantic', 'partner', 'significant other', 'intimate', 'vulnerable',
                'personal space', 'private moments', 'emotional bond'
            ],
            IntimacyLevel.DEEP: [
                'worry', 'fear', 'dream', 'hope', 'struggle', 'personal',
                'anxiety', 'depression', 'mental health', 'therapy', 'counseling',
                'family problems', 'relationship issues', 'career stress',
                'life goals', 'deep thoughts', 'philosophical', 'existential'
            ],
            IntimacyLevel.PERSONAL: [
                'family', 'grandmother', 'friend', 'life', 'experience',
                'childhood', 'memories', 'background', 'history', 'hobby',
                'interests', 'preferences', 'opinions', 'beliefs', 'values',
                'work', 'job', 'school', 'education', 'past'
            ],
            IntimacyLevel.CASUAL: [
                'weather', 'news', 'general', 'how are you', 'hello',
                'good morning', 'good evening', 'thanks', 'please',
                'simple question', 'basic information', 'surface level'
            ]
        }
        
        self.trust_keywords = {
            TrustLevel.CONFIDENTIAL: [
                'secret', "don't tell", 'between us', 'private', 'confidential',
                'keep this to yourself', 'just between you and me', 'classified',
                'sensitive information', 'personal matter', 'discretion'
            ],
            TrustLevel.TRUSTING: [
                'trust you', 'count on', 'believe you', 'rely on', 'depend on',
                'confident in you', 'faith in', 'comfortable with', 'open with',
                'honest', 'transparent', 'share with you'
            ],
            TrustLevel.SKEPTICAL: [
                'doubt', 'unsure', 'suspicious', 'questionable', 'uncertain',
                'not convinced', 'hesitant', 'wary', 'cautious', 'reserved'
            ]
        }
    
    async def analyze_relationship_context(self, content: str, _user_id: str, _conversation_history: Optional[List[Dict]] = None) -> RelationshipContext:
        """Analyze relationship intimacy and trust levels"""
        content_lower = content.lower()
        
        # Analyze intimacy level
        intimacy_scores = {}
        intimacy_indicators = []
        
        for level, keywords in self.intimacy_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                intimacy_scores[level] = score
                intimacy_indicators.extend([kw for kw in keywords if kw in content_lower])
        
        # Determine intimacy level
        if intimacy_scores:
            intimacy_level = max(intimacy_scores.keys(), key=lambda x: intimacy_scores[x])
        else:
            intimacy_level = IntimacyLevel.CASUAL
        
        # Analyze trust level
        trust_scores = {}
        trust_indicators = []
        
        for level, keywords in self.trust_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                trust_scores[level] = score
                trust_indicators.extend([kw for kw in keywords if kw in content_lower])
        
        # Determine trust level
        if trust_scores:
            trust_level = max(trust_scores.keys(), key=lambda x: trust_scores[x])
        else:
            trust_level = TrustLevel.NEUTRAL
        
        # Calculate confidence score
        total_indicators = len(intimacy_indicators) + len(trust_indicators)
        confidence_score = min(1.0, total_indicators * 0.2)  # Cap at 1.0
        
        all_indicators = intimacy_indicators + trust_indicators
        
        return RelationshipContext(
            intimacy_level=intimacy_level,
            trust_level=trust_level,
            confidence_score=confidence_score,
            indicators=all_indicators[:5]  # Top 5 indicators
        )
    
    def get_relationship_embedding_key(self, relationship_context: RelationshipContext) -> str:
        """Generate embedding key for relationship context"""
        return f"relationship intimacy_{relationship_context.intimacy_level.value}_trust_{relationship_context.trust_level.value}"


class PersonalityAnalyzer:
    """Analyzes character trait prominence"""
    
    def __init__(self):
        self.trait_keywords = {
            'empathy': [
                'understand', 'feel', 'emotion', 'support', 'care', 'comfort',
                'compassion', 'sympathy', 'listen', 'here for you', 'emotional',
                'feelings', 'heart', 'empathetic', 'understanding', 'caring'
            ],
            'analytical': [
                'analyze', 'think', 'logic', 'reason', 'calculate', 'research',
                'study', 'examine', 'investigate', 'data', 'evidence', 'facts',
                'systematic', 'methodical', 'rational', 'logical'
            ],
            'creative': [
                'create', 'imagine', 'art', 'design', 'innovative', 'original',
                'artistic', 'creative', 'inspiration', 'brainstorm', 'invent',
                'craft', 'build', 'make', 'compose', 'draw'
            ],
            'adventurous': [
                'adventure', 'explore', 'travel', 'risk', 'exciting', 'journey',
                'expedition', 'discovery', 'bold', 'daring', 'brave', 'courage',
                'thrill', 'new experiences', 'unknown'
            ],
            'scientific': [
                'research', 'study', 'experiment', 'theory', 'hypothesis',
                'scientific', 'analysis', 'methodology', 'observation',
                'lab', 'laboratory', 'academic', 'scholarly', 'peer review'
            ],
            'humorous': [
                'funny', 'joke', 'laugh', 'humor', 'wit', 'comedy', 'amusing',
                'hilarious', 'entertaining', 'playful', 'lighthearted', 'fun',
                'sarcasm', 'irony', 'pun'
            ],
            'protective': [
                'protect', 'safe', 'security', 'guard', 'defend', 'shield',
                'safety', 'secure', 'watch out', 'look after', 'care for',
                'guardian', 'protector', 'shelter'
            ],
            'curious': [
                'wonder', 'question', 'curious', 'investigate', 'learn',
                'why', 'how', 'what', 'interested', 'fascinated', 'intrigued',
                'explore', 'discover', 'find out'
            ]
        }
    
    async def analyze_personality_prominence(self, content: str, _character_name: Optional[str] = None) -> PersonalityContext:
        """Analyze personality trait prominence in content"""
        content_lower = content.lower()
        
        # Analyze trait prominence
        trait_scores = {}
        trait_indicators = {}
        
        for trait, keywords in self.trait_keywords.items():
            matches = [keyword for keyword in keywords if keyword in content_lower]
            score = len(matches)
            if score > 0:
                trait_scores[trait] = score
                trait_indicators[trait] = matches
        
        # Get top traits
        if trait_scores:
            sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)
            primary_traits = [trait for trait, score in sorted_traits[:2]]  # Top 2 traits
        else:
            primary_traits = ['balanced']  # Default if no specific traits detected
        
        # Calculate trait confidence scores
        trait_confidence = {}
        for trait, score in trait_scores.items():
            trait_confidence[trait] = min(1.0, score * 0.3)  # Cap at 1.0
        
        # Character alignment score (placeholder - could be enhanced with CDL integration)
        character_alignment = 0.8  # Default high alignment
        
        # Prominence indicators
        prominence_indicators = []
        for trait in primary_traits:
            if trait in trait_indicators:
                prominence_indicators.extend(trait_indicators[trait][:2])  # Top 2 per trait
        
        return PersonalityContext(
            primary_traits=primary_traits,
            trait_confidence=trait_confidence,
            character_alignment=character_alignment,
            prominence_indicators=prominence_indicators[:5]  # Top 5 indicators
        )
    
    def get_personality_embedding_key(self, personality_context: PersonalityContext) -> str:
        """Generate embedding key for personality context"""
        traits_str = "_".join(personality_context.primary_traits)
        return f"personality traits_{traits_str}"


class InteractionAnalyzer:
    """Analyzes communication style and conversation mode"""
    
    def __init__(self):
        self.style_keywords = {
            CommunicationStyle.ANALYTICAL: [
                'analyze', 'research', 'data', 'study', 'examine', 'investigate',
                'methodology', 'systematic', 'logical', 'evidence', 'facts',
                'technical', 'detailed', 'comprehensive', 'thorough'
            ],
            CommunicationStyle.CREATIVE: [
                'creative', 'brainstorm', 'imagine', 'innovative', 'design',
                'artistic', 'original', 'inspiration', 'ideas', 'concept',
                'vision', 'craft', 'build', 'make'
            ],
            CommunicationStyle.SUPPORTIVE: [
                'support', 'help', 'care', 'comfort', 'encourage', 'listen',
                'understand', 'empathy', 'there for you', 'guidance',
                'advice', 'assistance', 'emotional support'
            ],
            CommunicationStyle.CASUAL: [
                'hey', 'hi', 'what\'s up', 'how\'s it going', 'cool', 'awesome',
                'nice', 'chill', 'relaxed', 'informal', 'friendly'
            ],
            CommunicationStyle.FORMAL: [
                'please', 'thank you', 'certainly', 'indeed', 'furthermore',
                'moreover', 'therefore', 'consequently', 'respectfully',
                'formally', 'professionally'
            ]
        }
        
        self.mode_keywords = {
            ConversationMode.CRISIS_SUPPORT: [
                'help', 'emergency', 'urgent', 'panic', 'desperate', 'crisis',
                'immediate', 'serious', 'critical', 'urgent', 'emergency'
            ],
            ConversationMode.EDUCATIONAL: [
                'learn', 'explain', 'teach', 'understand', 'how does',
                'education', 'knowledge', 'information', 'instruction',
                'lesson', 'tutorial', 'guide'
            ],
            ConversationMode.EMOTIONAL_SUPPORT: [
                'sad', 'upset', 'worried', 'anxious', 'hurt', 'depressed',
                'emotional', 'feelings', 'mental health', 'support',
                'comfort', 'care'
            ],
            ConversationMode.CREATIVE_COLLABORATION: [
                'brainstorm', 'collaborate', 'create', 'design', 'build',
                'project', 'ideas', 'innovative', 'creative', 'teamwork'
            ],
            ConversationMode.PROBLEM_SOLVING: [
                'problem', 'solution', 'fix', 'resolve', 'troubleshoot',
                'issue', 'challenge', 'solve', 'optimize', 'improve'
            ],
            ConversationMode.CASUAL_CHAT: [
                'chat', 'talk', 'casual', 'conversation', 'friendly',
                'social', 'informal', 'relaxed'
            ]
        }
    
    async def analyze_interaction_context(self, content: str, _conversation_history: Optional[List[Dict]] = None) -> InteractionContext:
        """Analyze communication style and conversation mode"""
        content_lower = content.lower()
        
        # Analyze communication style
        style_scores = {}
        style_indicators = {}
        
        for style, keywords in self.style_keywords.items():
            matches = [keyword for keyword in keywords if keyword in content_lower]
            score = len(matches)
            if score > 0:
                style_scores[style] = score
                style_indicators[style] = matches
        
        # Determine communication style
        if style_scores:
            communication_style = max(style_scores.keys(), key=lambda x: style_scores[x])
            style_confidence = min(1.0, style_scores[communication_style] * 0.3)
        else:
            communication_style = CommunicationStyle.CASUAL
            style_confidence = 0.5
        
        # Analyze conversation mode
        mode_scores = {}
        mode_indicators = {}
        
        for mode, keywords in self.mode_keywords.items():
            matches = [keyword for keyword in keywords if keyword in content_lower]
            score = len(matches)
            if score > 0:
                mode_scores[mode] = score
                mode_indicators[mode] = matches
        
        # Determine conversation mode
        if mode_scores:
            conversation_mode = max(mode_scores.keys(), key=lambda x: mode_scores[x])
            mode_confidence = min(1.0, mode_scores[conversation_mode] * 0.3)
        else:
            conversation_mode = ConversationMode.CASUAL_CHAT
            mode_confidence = 0.5
        
        # Collect interaction indicators
        interaction_indicators = []
        if communication_style in style_indicators:
            interaction_indicators.extend(style_indicators[communication_style][:2])
        if conversation_mode in mode_indicators:
            interaction_indicators.extend(mode_indicators[conversation_mode][:2])
        
        return InteractionContext(
            communication_style=communication_style,
            conversation_mode=conversation_mode,
            style_confidence=style_confidence,
            mode_confidence=mode_confidence,
            interaction_indicators=interaction_indicators[:5]
        )
    
    def get_interaction_embedding_key(self, interaction_context: InteractionContext) -> str:
        """Generate embedding key for interaction context"""
        return f"interaction style_{interaction_context.communication_style.value}_mode_{interaction_context.conversation_mode.value}"


class TemporalAnalyzer:
    """Analyzes conversation flow and timing patterns"""
    
    def __init__(self):
        self.phase_keywords = {
            ConversationPhase.OPENING: [
                'hello', 'hi', 'good morning', 'good evening', 'greetings',
                'introduction', 'nice to meet', 'how are you', 'start',
                'begin', 'first time', 'initial'
            ],
            ConversationPhase.BUILDING: [
                'tell me more', 'continue', 'go on', 'elaborate', 'expand',
                'building', 'developing', 'growing', 'establishing'
            ],
            ConversationPhase.MIDDLE: [
                'furthermore', 'additionally', 'also', 'moreover', 'meanwhile',
                'ongoing', 'discussion', 'conversation', 'talking about'
            ],
            ConversationPhase.CLIMAX: [
                'most important', 'crucial', 'critical', 'key point',
                'main issue', 'heart of', 'core', 'essential'
            ],
            ConversationPhase.RESOLUTION: [
                'conclusion', 'summary', 'wrap up', 'final', 'end',
                'resolution', 'solution', 'answer', 'decision'
            ],
            ConversationPhase.FOLLOWUP: [
                'follow up', 'next time', 'later', 'future', 'continue',
                'keep in touch', 'talk again', 'see you'
            ]
        }
        
        self.rhythm_keywords = {
            ConversationRhythm.QUICK_EXCHANGE: [
                'quick', 'fast', 'rapid', 'brief', 'short', 'immediate',
                'instant', 'prompt', 'swift'
            ],
            ConversationRhythm.THOUGHTFUL_PACED: [
                'thoughtful', 'careful', 'considered', 'deliberate',
                'measured', 'reflective', 'contemplative'
            ],
            ConversationRhythm.DEEP_EXPLORATION: [
                'deep', 'thorough', 'comprehensive', 'detailed', 'extensive',
                'in-depth', 'profound', 'exploring', 'diving deep'
            ],
            ConversationRhythm.CASUAL_FLOW: [
                'casual', 'relaxed', 'easy', 'natural', 'flowing',
                'comfortable', 'informal', 'laid back'
            ]
        }
    
    async def analyze_temporal_context(self, content: str, _conversation_history: Optional[List[Dict]] = None, _message_timing: Optional[datetime] = None) -> TemporalContext:
        """Analyze conversation flow and timing patterns"""
        content_lower = content.lower()
        
        # Analyze conversation phase
        phase_scores = {}
        phase_indicators = {}
        
        for phase, keywords in self.phase_keywords.items():
            matches = [keyword for keyword in keywords if keyword in content_lower]
            score = len(matches)
            if score > 0:
                phase_scores[phase] = score
                phase_indicators[phase] = matches
        
        # Determine conversation phase (default to middle if unclear)
        if phase_scores:
            conversation_phase = max(phase_scores.keys(), key=lambda x: phase_scores[x])
            phase_confidence = min(1.0, phase_scores[conversation_phase] * 0.3)
        else:
            conversation_phase = ConversationPhase.MIDDLE
            phase_confidence = 0.5
        
        # Analyze conversation rhythm
        rhythm_scores = {}
        rhythm_indicators = {}
        
        for rhythm, keywords in self.rhythm_keywords.items():
            matches = [keyword for keyword in keywords if keyword in content_lower]
            score = len(matches)
            if score > 0:
                rhythm_scores[rhythm] = score
                rhythm_indicators[rhythm] = matches
        
        # Determine conversation rhythm (default to casual flow)
        if rhythm_scores:
            conversation_rhythm = max(rhythm_scores.keys(), key=lambda x: rhythm_scores[x])
            rhythm_confidence = min(1.0, rhythm_scores[conversation_rhythm] * 0.3)
        else:
            conversation_rhythm = ConversationRhythm.CASUAL_FLOW
            rhythm_confidence = 0.5
        
        # Collect flow indicators
        flow_indicators = []
        if conversation_phase in phase_indicators:
            flow_indicators.extend(phase_indicators[conversation_phase][:2])
        if conversation_rhythm in rhythm_indicators:
            flow_indicators.extend(rhythm_indicators[conversation_rhythm][:2])
        
        # 🚨 CONVERSATION FLOW INTELLIGENCE: Add flow optimization hints
        flow_optimization_hints = []
        
        # Detect verbose patterns that need conversational compression
        verbose_patterns = [
            "let me explain", "i should mention", "it's important to note",
            "first", "second", "third", "in conclusion", "to elaborate"
        ]
        has_verbose_indicators = any(pattern in content_lower for pattern in verbose_patterns)
        
        # Detect question opportunities for engagement
        question_indicators = ["?", "what do you think", "how about you", "your thoughts"]
        has_question_opportunities = any(indicator in content_lower for indicator in question_indicators)
        
        # Generate conversation flow hints
        if has_verbose_indicators:
            flow_optimization_hints.append("compress_to_conversational")
            flow_optimization_hints.append("use_engaging_questions")
        
        if conversation_phase == ConversationPhase.OPENING:
            flow_optimization_hints.append("keep_opening_concise")
            flow_optimization_hints.append("invite_user_sharing")
        elif conversation_phase == ConversationPhase.MIDDLE:
            flow_optimization_hints.append("maintain_back_and_forth")
            if not has_question_opportunities:
                flow_optimization_hints.append("add_engaging_question")
        elif conversation_phase == ConversationPhase.CLIMAX:
            flow_optimization_hints.append("balance_depth_with_engagement")
        elif conversation_phase == ConversationPhase.RESOLUTION:
            flow_optimization_hints.append("natural_conversation_pause")
        
        # Discord-specific optimization
        if len(content) > 1500:  # Approaching Discord 2000 char limit
            flow_optimization_hints.append("discord_length_optimization")
        
        return TemporalContext(
            conversation_phase=conversation_phase,
            conversation_rhythm=conversation_rhythm,
            phase_confidence=phase_confidence,
            rhythm_confidence=rhythm_confidence,
            flow_indicators=flow_indicators[:5],
            flow_optimization_hints=flow_optimization_hints[:4]  # Keep top 4 hints
        )
    
    def get_temporal_embedding_key(self, temporal_context: TemporalContext) -> str:
        """Generate embedding key for temporal context"""
        return f"temporal phase_{temporal_context.conversation_phase.value}_rhythm_{temporal_context.conversation_rhythm.value}"


class Enhanced7DVectorAnalyzer:
    """Coordinator for all 7-dimensional vector analysis"""
    
    def __init__(self):
        self.relationship_analyzer = RelationshipAnalyzer()
        self.personality_analyzer = PersonalityAnalyzer()
        self.interaction_analyzer = InteractionAnalyzer()
        self.temporal_analyzer = TemporalAnalyzer()
    
    async def analyze_all_dimensions(
        self,
        content: str,
        user_id: str,
        character_name: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        message_timing: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Analyze content across all 7 dimensions"""
        
        # Run all analyzers in parallel for efficiency
        relationship_task = self.relationship_analyzer.analyze_relationship_context(content, user_id, conversation_history)
        personality_task = self.personality_analyzer.analyze_personality_prominence(content, character_name)
        interaction_task = self.interaction_analyzer.analyze_interaction_context(content, conversation_history)
        temporal_task = self.temporal_analyzer.analyze_temporal_context(content, conversation_history, message_timing)
        
        # Await all results
        relationship_context, personality_context, interaction_context, temporal_context = await asyncio.gather(
            relationship_task, personality_task, interaction_task, temporal_task
        )
        
        return {
            'relationship_context': relationship_context,
            'personality_context': personality_context,
            'interaction_context': interaction_context,
            'temporal_context': temporal_context,
            'relationship_key': self.relationship_analyzer.get_relationship_embedding_key(relationship_context),
            'personality_key': self.personality_analyzer.get_personality_embedding_key(personality_context),
            'interaction_key': self.interaction_analyzer.get_interaction_embedding_key(interaction_context),
            'temporal_key': self.temporal_analyzer.get_temporal_embedding_key(temporal_context)
        }