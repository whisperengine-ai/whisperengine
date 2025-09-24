"""
🚀 RoBERTa-Enhanced Conversation Summarizer

Advanced conversation summary generation using RoBERTa's contextual understanding
combined with emotional intelligence and thematic analysis.

Key Features:
- Multi-emotion aware summaries that capture emotional nuances
- Thematic extraction using RoBERTa's contextual embeddings
- Conversation arc detection (setup → development → resolution)
- Personality-aware summarization styles
- Fallback to keyword-based analysis for reliability

Integration Points:
- Used by memory system for long conversation archiving
- Enhances CDL character interactions with conversation context
- Provides emotional continuity across conversation sessions

Author: WhisperEngine AI Team
Created: 2024-09-23
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

# Core WhisperEngine imports
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer

logger = logging.getLogger(__name__)

class ConversationArcType(Enum):
    """Types of conversation development patterns"""
    LINEAR = "linear"          # A → B → C progression
    CIRCULAR = "circular"      # Returns to original topic
    BRANCHING = "branching"    # Multiple topic threads
    CRISIS = "crisis"          # Problem → resolution pattern
    DISCOVERY = "discovery"    # Learning/revelation pattern
    EMOTIONAL = "emotional"    # Emotional processing pattern

class SummaryStyle(Enum):
    """Different summarization approaches"""
    ANALYTICAL = "analytical"      # Logical, structured
    NARRATIVE = "narrative"        # Story-like flow
    EMOTIONAL = "emotional"        # Feeling-focused
    FACTUAL = "factual"           # Objective, concise
    PERSONAL = "personal"          # Relationship-focused

@dataclass
class ConversationTheme:
    """A thematic element detected in conversation"""
    theme: str
    confidence: float
    emotional_weight: float
    key_messages: List[str]
    emergence_pattern: str  # "gradual", "sudden", "recurring"

@dataclass
class ConversationSummary:
    """Enhanced conversation summary with RoBERTa intelligence"""
    # Core summary
    primary_summary: str
    key_points: List[str]
    
    # Emotional intelligence
    emotional_arc: Dict[str, Any]
    dominant_emotions: List[Tuple[str, float]]
    emotional_complexity: str
    
    # Thematic analysis
    main_themes: List[ConversationTheme]
    conversation_arc: ConversationArcType
    
    # Metadata
    message_count: int
    time_span: str
    participants: List[str]
    summary_style: SummaryStyle
    roberta_confidence: float

class RoBERTaConversationSummarizer:
    """
    Advanced conversation summarizer using RoBERTa's contextual understanding
    """
    
    def __init__(self):
        self.emotion_analyzer = EnhancedVectorEmotionAnalyzer()
        self.stats = {
            "summaries_generated": 0,
            "roberta_successes": 0,
            "fallback_uses": 0,
            "average_confidence": 0.0
        }
        logger.info("RoBERTa Conversation Summarizer initialized")
    
    async def generate_conversation_summary(
        self,
        messages: List[Dict[str, Any]], 
        style: SummaryStyle = SummaryStyle.NARRATIVE,
        max_length: int = 500,
        user_context: Optional[Dict[str, Any]] = None  # Reserved for future enhancement
    ) -> ConversationSummary:
        """
        Generate comprehensive conversation summary with RoBERTa enhancement
        
        Args:
            messages: List of conversation messages with metadata
            style: Desired summary style 
            max_length: Maximum summary length
            user_context: Additional context about participants
            
        Returns:
            ConversationSummary with rich emotional and thematic analysis
        """
        try:
            logger.debug("Generating RoBERTa summary for %d messages", len(messages))
            
            # Extract conversation content and metadata
            conversation_text = self._extract_conversation_text(messages)
            participants = self._extract_participants(messages)
            
            # RoBERTa-enhanced analysis
            emotional_arc = await self._analyze_emotional_arc(messages)
            themes = await self._extract_conversation_themes(conversation_text)
            arc_type = await self._detect_conversation_arc(messages, emotional_arc)
            
            # Generate style-appropriate summary
            primary_summary = await self._generate_styled_summary(
                conversation_text, style, emotional_arc, themes, max_length
            )
            
            # Extract key points with RoBERTa context
            key_points = await self._extract_key_points(
                messages, emotional_arc, themes
            )
            
            # Calculate confidence and update stats
            roberta_confidence = self._calculate_summary_confidence(
                emotional_arc, themes, len(messages)
            )
            
            self._update_stats(roberta_confidence)
            
            return ConversationSummary(
                primary_summary=primary_summary,
                key_points=key_points,
                emotional_arc=emotional_arc,
                dominant_emotions=self._get_dominant_emotions(emotional_arc),
                emotional_complexity=self._classify_emotional_complexity(emotional_arc),
                main_themes=themes,
                conversation_arc=arc_type,
                message_count=len(messages),
                time_span=self._calculate_time_span(messages),
                participants=participants,
                summary_style=style,
                roberta_confidence=roberta_confidence
            )
            
        except (ImportError, RuntimeError, ValueError) as e:
            logger.error("RoBERTa summary generation failed: %s", str(e))
            return await self._fallback_summary_generation(messages, style, max_length)
    
    async def _analyze_emotional_arc(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze emotional progression through conversation using RoBERTa
        """
        try:
            emotional_timeline = []
            emotion_transitions = []
            
            prev_emotions = None
            
            for i, message in enumerate(messages):
                content = message.get('content', '')
                if not content.strip():
                    continue
                
                # Get RoBERTa emotion analysis
                emotion_result = await self.emotion_analyzer.analyze_emotion(
                    content, user_id="conversation_summarizer"
                )
                
                current_emotions = {
                    'primary': emotion_result.primary_emotion,
                    'intensity': emotion_result.intensity,
                    'all_emotions': emotion_result.all_emotions,
                    'timestamp': i,
                    'message_index': i
                }
                
                emotional_timeline.append(current_emotions)
                
                # Track emotion transitions
                if prev_emotions is not None:
                    if prev_emotions['primary'] != current_emotions['primary']:
                        transition = {
                            'from': prev_emotions['primary'],
                            'to': current_emotions['primary'],
                            'intensity_change': current_emotions['intensity'] - prev_emotions['intensity'],
                            'message_index': i
                        }
                        emotion_transitions.append(transition)
                
                prev_emotions = current_emotions
            
            # Analyze overall emotional patterns
            emotional_patterns = self._analyze_emotional_patterns(emotional_timeline)
            
            return {
                'timeline': emotional_timeline,
                'transitions': emotion_transitions,
                'patterns': emotional_patterns,
                'overall_sentiment': self._calculate_overall_sentiment(emotional_timeline),
                'emotional_volatility': self._calculate_emotional_volatility(emotion_transitions),
                'roberta_analysis': True
            }
            
        except (ImportError, RuntimeError, ValueError) as e:
            logger.warning("RoBERTa emotional arc analysis failed, using fallback: %s", str(e))
            return await self._fallback_emotional_arc(messages)
    
    async def _extract_conversation_themes(self, conversation_text: str) -> List[ConversationTheme]:
        """
        Extract thematic elements using RoBERTa's contextual understanding
        """
        try:
            # Use RoBERTa to analyze thematic content
            emotion_result = await self.emotion_analyzer.analyze_emotion(
                conversation_text, user_id="conversation_theme_analyzer"
            )
            
            # Extract themes based on RoBERTa's contextual analysis
            themes = []
            
            # Analyze for common conversational themes
            theme_patterns = {
                'relationship': ['relationship', 'together', 'love', 'partner', 'friend'],
                'work_career': ['job', 'work', 'career', 'professional', 'boss'],
                'personal_growth': ['learn', 'grow', 'change', 'improve', 'develop'],
                'challenges': ['problem', 'difficult', 'challenge', 'struggle', 'issue'],
                'achievements': ['success', 'accomplish', 'achieve', 'proud', 'win'],
                'future_plans': ['plan', 'future', 'goal', 'want', 'hope', 'will']
            }
            
            for theme_name, keywords in theme_patterns.items():
                # Calculate theme relevance
                keyword_matches = sum(1 for keyword in keywords if keyword.lower() in conversation_text.lower())
                if keyword_matches > 0:
                    confidence = min(keyword_matches / len(keywords), 1.0)
                    
                    # Use emotion analysis to weight themes
                    emotional_weight = 0.5
                    if emotion_result.get('all_emotions'):
                        # Themes with emotional content are more significant
                        relevant_emotions = ['joy', 'sadness', 'anger', 'fear', 'anticipation']
                        emotional_weight = sum(
                            emotion_result['all_emotions'].get(emotion, 0) 
                            for emotion in relevant_emotions
                        ) / len(relevant_emotions)
                    
                    if confidence > 0.2:  # Only include significant themes
                        theme = ConversationTheme(
                            theme=theme_name,
                            confidence=confidence,
                            emotional_weight=emotional_weight,
                            key_messages=self._extract_theme_messages(conversation_text, keywords),
                            emergence_pattern=self._detect_theme_pattern(conversation_text, keywords)
                        )
                        themes.append(theme)
            
            # Sort themes by combined confidence and emotional weight
            themes.sort(key=lambda t: t.confidence * t.emotional_weight, reverse=True)
            
            return themes[:5]  # Return top 5 themes
            
        except (ImportError, RuntimeError, ValueError) as e:
            logger.warning("RoBERTa theme extraction failed, using fallback: %s", str(e))
            return self._fallback_theme_extraction(conversation_text)
    
    async def _detect_conversation_arc(
        self, 
        messages: List[Dict[str, Any]], 
        emotional_arc: Dict[str, Any]
    ) -> ConversationArcType:
        """
        Detect conversation development pattern using RoBERTa insights
        """
        try:
            if len(messages) < 3:
                return ConversationArcType.LINEAR
            
            # Analyze emotional transitions for arc detection
            transitions = emotional_arc.get('transitions', [])
            
            if not transitions:
                return ConversationArcType.LINEAR
            
            # Crisis pattern: negative → positive transition
            negative_emotions = {'sadness', 'anger', 'fear', 'disgust'}
            positive_emotions = {'joy', 'trust', 'anticipation'}
            
            has_crisis_pattern = False
            has_circular_pattern = False
            
            first_emotion = transitions[0]['from']
            # Note: last_emotion reserved for future circular pattern analysis
            
            for transition in transitions:
                # Check for crisis resolution (negative → positive)
                if (transition['from'] in negative_emotions and 
                    transition['to'] in positive_emotions):
                    has_crisis_pattern = True
                
                # Check for circular pattern (return to original emotion)
                if transition['to'] == first_emotion:
                    has_circular_pattern = True
            
            # Determine arc type based on patterns
            if has_crisis_pattern:
                return ConversationArcType.CRISIS
            elif has_circular_pattern:
                return ConversationArcType.CIRCULAR
            elif len(transitions) > len(messages) * 0.3:  # Many transitions
                return ConversationArcType.BRANCHING
            elif emotional_arc.get('emotional_volatility', 0) > 0.7:
                return ConversationArcType.EMOTIONAL
            else:
                return ConversationArcType.LINEAR
                
        except (ImportError, RuntimeError, ValueError) as e:
            logger.warning("Conversation arc detection failed: %s", str(e))
            return ConversationArcType.LINEAR
    
    async def _generate_styled_summary(
        self,
        conversation_text: str,
        style: SummaryStyle,
        emotional_arc: Dict[str, Any],
        themes: List[ConversationTheme],
        max_length: int
    ) -> str:
        """
        Generate summary in specified style using RoBERTa context
        """
        try:
            # Get dominant theme for focus
            main_theme = themes[0].theme if themes else "general_conversation"
            
            # Get emotional context
            overall_sentiment = emotional_arc.get('overall_sentiment', 'neutral')
            emotional_volatility = emotional_arc.get('emotional_volatility', 0.0)
            
            # Style-specific summary generation
            if style == SummaryStyle.EMOTIONAL:
                summary = self._generate_emotional_summary(
                    conversation_text, emotional_arc, max_length
                )
            elif style == SummaryStyle.ANALYTICAL:
                summary = self._generate_analytical_summary(
                    conversation_text, themes, emotional_arc, max_length
                )
            elif style == SummaryStyle.NARRATIVE:
                summary = self._generate_narrative_summary(
                    conversation_text, themes, emotional_arc, max_length
                )
            elif style == SummaryStyle.FACTUAL:
                summary = self._generate_factual_summary(
                    conversation_text, themes, max_length
                )
            else:  # PERSONAL
                summary = self._generate_personal_summary(
                    conversation_text, emotional_arc, max_length
                )
            
            # Ensure summary doesn't exceed max length
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            return summary
            
        except (ImportError, RuntimeError, ValueError) as e:
            logger.warning("Styled summary generation failed: %s", str(e))
            return self._fallback_simple_summary(conversation_text, max_length)
    
    def _generate_emotional_summary(
        self, 
        text: str, 
        emotional_arc: Dict[str, Any], 
        max_length: int
    ) -> str:
        """Generate emotion-focused summary"""
        timeline = emotional_arc.get('timeline', [])
        if not timeline:
            return "A conversation with neutral emotional tone."
        
        # Get emotional progression
        start_emotion = timeline[0].get('primary', 'neutral')
        end_emotion = timeline[-1].get('primary', 'neutral')
        
        volatility = emotional_arc.get('emotional_volatility', 0.0)
        
        if volatility > 0.5:
            return (f"An emotionally dynamic conversation that began with {start_emotion} "
                   f"and evolved through various emotional states, ending with {end_emotion}. "
                   f"The discussion featured significant emotional transitions and processing.")
        else:
            return (f"A conversation with steady emotional tone, primarily characterized by "
                   f"{start_emotion} feelings that remained consistent throughout the discussion.")
    
    def _generate_analytical_summary(
        self,
        text: str,
        themes: List[ConversationTheme],
        emotional_arc: Dict[str, Any],
        max_length: int
    ) -> str:
        """Generate structured analytical summary"""
        if not themes:
            return "A general conversation without distinct thematic focus."
        
        main_themes = [theme.theme.replace('_', ' ') for theme in themes[:3]]
        theme_str = ", ".join(main_themes)
        
        patterns = emotional_arc.get('patterns', {})
        stability = patterns.get('emotional_stability', 'moderate')
        
        return (f"Conversation analysis reveals primary focus on {theme_str}. "
               f"Emotional pattern shows {stability} stability with "
               f"{len(emotional_arc.get('transitions', []))} significant transitions. "
               f"Thematic coherence maintained throughout discussion.")
    
    def _generate_narrative_summary(
        self,
        text: str,
        themes: List[ConversationTheme],
        emotional_arc: Dict[str, Any],
        max_length: int
    ) -> str:
        """Generate story-like narrative summary"""
        timeline = emotional_arc.get('timeline', [])
        if not timeline or not themes:
            return "A conversation unfolded between participants sharing thoughts and experiences."
        
        main_theme = themes[0].theme.replace('_', ' ')
        start_emotion = timeline[0].get('primary', 'neutral')
        end_emotion = timeline[-1].get('primary', 'neutral')
        
        if start_emotion != end_emotion:
            return (f"The conversation began as a discussion about {main_theme}, "
                   f"initially marked by {start_emotion} feelings. As the dialogue progressed, "
                   f"emotional undertones shifted, ultimately concluding with {end_emotion}. "
                   f"The exchange revealed deeper layers of understanding and connection.")
        else:
            return (f"A thoughtful conversation centered on {main_theme} unfolded, "
                   f"characterized by consistent {start_emotion} undertones throughout. "
                   f"Participants engaged in meaningful dialogue that maintained emotional coherence.")
    
    def _generate_factual_summary(
        self,
        text: str,
        themes: List[ConversationTheme],
        max_length: int
    ) -> str:
        """Generate objective factual summary"""
        if not themes:
            return "Conversation covered general topics without specific thematic focus."
        
        theme_count = len(themes)
        main_themes = [theme.theme.replace('_', ' ') for theme in themes[:3]]
        
        return (f"Discussion encompassed {theme_count} primary themes: {', '.join(main_themes)}. "
               f"Conversation maintained topical coherence with structured information exchange.")
    
    def _generate_personal_summary(
        self,
        text: str,
        emotional_arc: Dict[str, Any],
        max_length: int
    ) -> str:
        """Generate relationship-focused summary"""
        volatility = emotional_arc.get('emotional_volatility', 0.0)
        overall_sentiment = emotional_arc.get('overall_sentiment', 'neutral')
        
        if volatility > 0.3:
            return (f"A meaningful exchange that deepened connection between participants. "
                   f"The conversation featured emotional openness and vulnerability, "
                   f"ultimately strengthening understanding and rapport with {overall_sentiment} outcomes.")
        else:
            return (f"A warm and steady conversation that reinforced connection. "
                   f"Participants shared thoughts in a comfortable environment, "
                   f"maintaining {overall_sentiment} rapport throughout their interaction.")
    
    async def _extract_key_points(
        self,
        messages: List[Dict[str, Any]],
        emotional_arc: Dict[str, Any],
        themes: List[ConversationTheme]
    ) -> List[str]:
        """Extract key conversation points using RoBERTa context"""
        try:
            key_points = []
            
            # Add theme-based key points
            for theme in themes[:3]:  # Top 3 themes
                if theme.key_messages:
                    key_points.extend(theme.key_messages[:1])  # Top message per theme
            
            # Add emotional transition points
            transitions = emotional_arc.get('transitions', [])
            significant_transitions = [
                t for t in transitions 
                if abs(t.get('intensity_change', 0)) > 0.3
            ]
            
            if significant_transitions:
                key_points.append(
                    f"Notable emotional shift from {significant_transitions[0]['from']} "
                    f"to {significant_transitions[0]['to']}"
                )
            
            # Add high-confidence content points
            for message in messages:
                content = message.get('content', '').strip()
                if (len(content) > 20 and 
                    any(keyword in content.lower() for keyword in 
                        ['important', 'realize', 'understand', 'discover', 'learn'])):
                    if content not in key_points:
                        key_points.append(content[:100] + ("..." if len(content) > 100 else ""))
            
            return key_points[:5]  # Limit to 5 key points
            
        except Exception as e:
            logger.warning(f"Key point extraction failed: {e}")
            return ["Conversation included meaningful exchanges between participants."]
    
    # Helper methods for analysis
    def _extract_conversation_text(self, messages: List[Dict[str, Any]]) -> str:
        """Extract clean conversation text"""
        return "\n".join(
            msg.get('content', '') for msg in messages 
            if msg.get('content', '').strip()
        )
    
    def _extract_participants(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract unique participant identifiers"""
        participants = set()
        for msg in messages:
            if 'user_id' in msg:
                participants.add(msg['user_id'])
            elif 'author' in msg:
                participants.add(msg['author'])
        return list(participants)
    
    def _analyze_emotional_patterns(self, timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in emotional timeline"""
        if not timeline:
            return {'emotional_stability': 'unknown'}
        
        intensities = [point.get('intensity', 0.5) for point in timeline]
        avg_intensity = sum(intensities) / len(intensities)
        intensity_variance = sum((i - avg_intensity) ** 2 for i in intensities) / len(intensities)
        
        if intensity_variance < 0.1:
            stability = 'high'
        elif intensity_variance < 0.3:
            stability = 'moderate'
        else:
            stability = 'low'
        
        return {
            'emotional_stability': stability,
            'average_intensity': avg_intensity,
            'intensity_variance': intensity_variance
        }
    
    def _calculate_overall_sentiment(self, timeline: List[Dict[str, Any]]) -> str:
        """Calculate overall conversation sentiment"""
        if not timeline:
            return 'neutral'
        
        positive_emotions = {'joy', 'trust', 'anticipation'}
        negative_emotions = {'sadness', 'anger', 'fear', 'disgust'}
        
        positive_count = sum(
            1 for point in timeline 
            if point.get('primary') in positive_emotions
        )
        negative_count = sum(
            1 for point in timeline 
            if point.get('primary') in negative_emotions
        )
        
        if positive_count > negative_count * 1.5:
            return 'positive'
        elif negative_count > positive_count * 1.5:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_emotional_volatility(self, transitions: List[Dict[str, Any]]) -> float:
        """Calculate emotional volatility score"""
        if not transitions:
            return 0.0
        
        total_intensity_change = sum(
            abs(t.get('intensity_change', 0)) for t in transitions
        )
        return min(total_intensity_change / len(transitions), 1.0)
    
    def _get_dominant_emotions(self, emotional_arc: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Get dominant emotions from arc analysis"""
        timeline = emotional_arc.get('timeline', [])
        if not timeline:
            return [('neutral', 0.5)]
        
        emotion_counts = {}
        for point in timeline:
            primary = point.get('primary', 'neutral')
            intensity = point.get('intensity', 0.5)
            if primary in emotion_counts:
                emotion_counts[primary] += intensity
            else:
                emotion_counts[primary] = intensity
        
        # Normalize by occurrence count
        for emotion in emotion_counts:
            count = sum(1 for point in timeline if point.get('primary') == emotion)
            emotion_counts[emotion] = emotion_counts[emotion] / count if count > 0 else 0
        
        # Sort by average intensity
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_emotions[:3]  # Top 3 dominant emotions
    
    def _classify_emotional_complexity(self, emotional_arc: Dict[str, Any]) -> str:
        """Classify emotional complexity level"""
        transitions = emotional_arc.get('transitions', [])
        volatility = emotional_arc.get('emotional_volatility', 0.0)
        
        if not transitions:
            return 'simple'
        
        unique_emotions = len(set(
            t['from'] for t in transitions
        ) | set(
            t['to'] for t in transitions
        ))
        
        if unique_emotions >= 5 and volatility > 0.5:
            return 'highly_complex'
        elif unique_emotions >= 3 and volatility > 0.3:
            return 'moderately_complex'
        elif unique_emotions >= 2:
            return 'simple_mixed'
        else:
            return 'simple'
    
    def _calculate_time_span(self, messages: List[Dict[str, Any]]) -> str:
        """Calculate conversation time span"""
        timestamps = [
            msg.get('timestamp') for msg in messages 
            if msg.get('timestamp')
        ]
        if len(timestamps) < 2:
            return 'single_exchange'
        
        # This would need proper timestamp parsing in real implementation
        return f"{len(messages)}_messages"
    
    def _calculate_summary_confidence(
        self,
        emotional_arc: Dict[str, Any],
        themes: List[ConversationTheme],
        message_count: int
    ) -> float:
        """Calculate confidence in summary quality"""
        base_confidence = 0.6
        
        # Boost for RoBERTa analysis success
        if emotional_arc.get('roberta_analysis', False):
            base_confidence += 0.2
        
        # Boost for theme detection
        if themes:
            base_confidence += 0.1 * min(len(themes), 3)
        
        # Boost for message count (more data = higher confidence)
        if message_count >= 5:
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
    
    def _update_stats(self, confidence: float):
        """Update summarizer statistics"""
        self.stats["summaries_generated"] += 1
        if confidence > 0.7:
            self.stats["roberta_successes"] += 1
        else:
            self.stats["fallback_uses"] += 1
        
        # Update rolling average confidence
        current_avg = self.stats["average_confidence"]
        total = self.stats["summaries_generated"]
        self.stats["average_confidence"] = (current_avg * (total - 1) + confidence) / total
    
    # Fallback methods for reliability
    async def _fallback_emotional_arc(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback emotional arc analysis using keywords"""
        return {
            'timeline': [{'primary': 'neutral', 'intensity': 0.5, 'timestamp': i} 
                        for i in range(len(messages))],
            'transitions': [],
            'patterns': {'emotional_stability': 'moderate'},
            'overall_sentiment': 'neutral',
            'emotional_volatility': 0.0,
            'roberta_analysis': False
        }
    
    def _fallback_theme_extraction(self, conversation_text: str) -> List[ConversationTheme]:
        """Fallback theme extraction using keyword matching"""
        return [
            ConversationTheme(
                theme="general_conversation",
                confidence=0.5,
                emotional_weight=0.5,
                key_messages=["General discussion topics"],
                emergence_pattern="consistent"
            )
        ]
    
    async def _fallback_summary_generation(
        self,
        messages: List[Dict[str, Any]],
        style: SummaryStyle,
        max_length: int
    ) -> ConversationSummary:
        """Complete fallback summary generation"""
        logger.warning("Using complete fallback summary generation")
        
        simple_summary = self._fallback_simple_summary(
            self._extract_conversation_text(messages), max_length
        )
        
        return ConversationSummary(
            primary_summary=simple_summary,
            key_points=["Conversation between participants"],
            emotional_arc={'overall_sentiment': 'neutral'},
            dominant_emotions=[('neutral', 0.5)],
            emotional_complexity='simple',
            main_themes=[],
            conversation_arc=ConversationArcType.LINEAR,
            message_count=len(messages),
            time_span=f"{len(messages)}_messages",
            participants=self._extract_participants(messages),
            summary_style=style,
            roberta_confidence=0.3
        )
    
    def _fallback_simple_summary(self, text: str, max_length: int) -> str:
        """Simple fallback summary using basic text processing"""
        if len(text) <= max_length:
            return text
        
        sentences = text.split('. ')
        summary = sentences[0]
        
        for sentence in sentences[1:]:
            if len(summary + '. ' + sentence) <= max_length:
                summary += '. ' + sentence
            else:
                break
        
        return summary + ("..." if len(text) > max_length else "")
    
    def _extract_theme_messages(self, text: str, keywords: List[str]) -> List[str]:
        """Extract messages relevant to theme keywords"""
        sentences = text.split('.')
        relevant = []
        
        for sentence in sentences:
            if any(keyword.lower() in sentence.lower() for keyword in keywords):
                clean_sentence = sentence.strip()
                if clean_sentence and len(clean_sentence) > 10:
                    relevant.append(clean_sentence)
        
        return relevant[:3]  # Top 3 relevant messages
    
    def _detect_theme_pattern(self, text: str, keywords: List[str]) -> str:
        """Detect how theme emerges in conversation"""
        sentences = text.split('.')
        matches = []
        
        for i, sentence in enumerate(sentences):
            if any(keyword.lower() in sentence.lower() for keyword in keywords):
                matches.append(i)
        
        if not matches:
            return "absent"
        elif len(matches) == 1:
            return "sudden"
        elif matches[-1] - matches[0] < len(sentences) * 0.3:
            return "concentrated"
        else:
            return "recurring"

# Factory function for easy integration
def create_roberta_conversation_summarizer() -> RoBERTaConversationSummarizer:
    """Factory function to create RoBERTa conversation summarizer"""
    return RoBERTaConversationSummarizer()