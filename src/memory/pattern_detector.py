"""
Pattern Detector
================

Detects patterns and cross-references in memory networks.
Identifies recurring themes, behavioral patterns, and connections between memories.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be detected"""
    TEMPORAL = "temporal"           # Time-based patterns
    BEHAVIORAL = "behavioral"       # Recurring behaviors
    TOPICAL = "topical"            # Topic clusters  
    EMOTIONAL = "emotional"         # Emotional patterns
    CONVERSATIONAL = "conversational"  # Communication patterns
    PREFERENCE = "preference"       # Preference patterns


@dataclass
class DetectedPattern:
    """A detected pattern in memory data"""
    pattern_type: PatternType
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    supporting_memories: List[str]  # Memory IDs
    frequency: int
    first_occurrence: Optional[datetime]
    last_occurrence: Optional[datetime]
    metadata: Dict[str, Any]


class CrossReferencePatternDetector:
    """Detects patterns and cross-references across memory networks"""
    
    def __init__(self):
        self.min_pattern_frequency = 2  # Minimum occurrences to consider a pattern
        self.confidence_threshold = 0.6  # Minimum confidence for pattern detection
        self.detected_patterns = {}  # Store detected patterns by user_id
    
    async def detect_memory_patterns(self, memories: List[Dict[str, Any]], user_id: str) -> List[DetectedPattern]:
        """Detect memory patterns (alias for detect_patterns)"""
        patterns = await self.detect_patterns(memories, user_id)
        self.detected_patterns[user_id] = patterns
        return patterns
    
    def get_pattern_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get pattern statistics for a user"""
        patterns = self.detected_patterns.get(user_id, [])
        if not patterns:
            return {"total_patterns": 0, "pattern_types": {}, "average_confidence": 0.0}
        
        pattern_types = {}
        total_confidence = 0.0
        
        for pattern in patterns:
            pattern_type = pattern.pattern_type.value
            if pattern_type not in pattern_types:
                pattern_types[pattern_type] = 0
            pattern_types[pattern_type] += 1
            total_confidence += pattern.confidence
        
        return {
            "total_patterns": len(patterns),
            "pattern_types": pattern_types,
            "average_confidence": total_confidence / len(patterns) if patterns else 0.0
        }
    
    async def detect_patterns(
        self, 
        memories: List[Dict[str, Any]], 
        user_id: str
    ) -> List[DetectedPattern]:
        """Detect all types of patterns in memory data"""
        
        try:
            all_patterns = []
            
            # Detect different types of patterns
            temporal_patterns = await self._detect_temporal_patterns(memories)
            behavioral_patterns = await self._detect_behavioral_patterns(memories)
            topical_patterns = await self._detect_topical_patterns(memories)
            emotional_patterns = await self._detect_emotional_patterns(memories)
            conversational_patterns = await self._detect_conversational_patterns(memories)
            preference_patterns = await self._detect_preference_patterns(memories)
            
            all_patterns.extend(temporal_patterns)
            all_patterns.extend(behavioral_patterns)
            all_patterns.extend(topical_patterns)
            all_patterns.extend(emotional_patterns)
            all_patterns.extend(conversational_patterns)
            all_patterns.extend(preference_patterns)
            
            # Filter by confidence threshold
            significant_patterns = [
                pattern for pattern in all_patterns 
                if pattern.confidence >= self.confidence_threshold
            ]
            
            # Sort by confidence (highest first)
            significant_patterns.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"Detected {len(significant_patterns)} significant patterns for user {user_id}")
            
            return significant_patterns
            
        except Exception as e:
            logger.error("Error detecting patterns: %s", str(e))
            return []
    
    async def _detect_temporal_patterns(self, memories: List[Dict[str, Any]]) -> List[DetectedPattern]:
        """Detect time-based patterns"""
        patterns = []
        
        try:
            # Group memories by time periods
            time_groups = self._group_memories_by_time(memories)
            
            # Look for recurring temporal patterns
            for period, period_memories in time_groups.items():
                if len(period_memories) >= self.min_pattern_frequency:
                    pattern = DetectedPattern(
                        pattern_type=PatternType.TEMPORAL,
                        title=f"Active during {period}",
                        description=f"User frequently engages during {period} time period",
                        confidence=min(1.0, len(period_memories) / 10.0),
                        supporting_memories=[m.get('id', '') for m in period_memories],
                        frequency=len(period_memories),
                        first_occurrence=self._get_earliest_timestamp(period_memories),
                        last_occurrence=self._get_latest_timestamp(period_memories),
                        metadata={'time_period': period}
                    )
                    patterns.append(pattern)
            
        except Exception as e:
            logger.warning("Error detecting temporal patterns: %s", str(e))
        
        return patterns
    
    async def _detect_behavioral_patterns(self, memories: List[Dict[str, Any]]) -> List[DetectedPattern]:
        """Detect recurring behavioral patterns"""
        patterns = []
        
        try:
            # Look for recurring phrases/behaviors
            behavior_keywords = [
                'always', 'usually', 'often', 'tend to', 'habit', 'routine',
                'regularly', 'typically', 'every day', 'every week'
            ]
            
            behavioral_memories = []
            for memory in memories:
                content = memory.get('content', '') or memory.get('user_message', '')
                if any(keyword in content.lower() for keyword in behavior_keywords):
                    behavioral_memories.append(memory)
            
            if len(behavioral_memories) >= self.min_pattern_frequency:
                pattern = DetectedPattern(
                    pattern_type=PatternType.BEHAVIORAL,
                    title="Recurring Behaviors",
                    description="User frequently discusses habits and recurring behaviors",
                    confidence=min(1.0, len(behavioral_memories) / 5.0),
                    supporting_memories=[m.get('id', '') for m in behavioral_memories],
                    frequency=len(behavioral_memories),
                    first_occurrence=self._get_earliest_timestamp(behavioral_memories),
                    last_occurrence=self._get_latest_timestamp(behavioral_memories),
                    metadata={'behavior_indicators': behavior_keywords}
                )
                patterns.append(pattern)
                
        except Exception as e:
            logger.warning("Error detecting behavioral patterns: %s", str(e))
        
        return patterns
    
    async def _detect_topical_patterns(self, memories: List[Dict[str, Any]]) -> List[DetectedPattern]:
        """Detect topical/subject patterns"""
        patterns = []
        
        try:
            # Simple topic detection based on keywords
            topic_keywords = {
                'work': ['work', 'job', 'career', 'office', 'boss', 'colleague', 'project'],
                'family': ['family', 'parents', 'siblings', 'kids', 'children', 'spouse'],
                'hobbies': ['hobby', 'fun', 'enjoy', 'passion', 'interest', 'love doing'],
                'health': ['health', 'exercise', 'fitness', 'medical', 'doctor', 'sick'],
                'technology': ['computer', 'software', 'tech', 'app', 'digital', 'online']
            }
            
            for topic, keywords in topic_keywords.items():
                topic_memories = []
                for memory in memories:
                    content = memory.get('content', '') or memory.get('user_message', '')
                    if any(keyword in content.lower() for keyword in keywords):
                        topic_memories.append(memory)
                
                if len(topic_memories) >= self.min_pattern_frequency:
                    pattern = DetectedPattern(
                        pattern_type=PatternType.TOPICAL,
                        title=f"{topic.title()} Topic Pattern",
                        description=f"User frequently discusses {topic}-related topics",
                        confidence=min(1.0, len(topic_memories) / 8.0),
                        supporting_memories=[m.get('id', '') for m in topic_memories],
                        frequency=len(topic_memories),
                        first_occurrence=self._get_earliest_timestamp(topic_memories),
                        last_occurrence=self._get_latest_timestamp(topic_memories),
                        metadata={'topic': topic, 'keywords': keywords}
                    )
                    patterns.append(pattern)
                    
        except Exception as e:
            logger.warning("Error detecting topical patterns: %s", str(e))
        
        return patterns
    
    async def _detect_emotional_patterns(self, memories: List[Dict[str, Any]]) -> List[DetectedPattern]:
        """Detect emotional patterns"""
        patterns = []
        
        try:
            # Group memories by emotional content
            emotional_memories = {}
            
            for memory in memories:
                # Check for emotion data
                emotions = memory.get('emotions', {})
                if not emotions:
                    metadata = memory.get('metadata', {})
                    emotions = metadata.get('emotions', {})
                
                # Simple emotion detection based on content if no emotion data
                if not emotions:
                    content = memory.get('content', '') or memory.get('user_message', '')
                    emotions = self._detect_simple_emotions(content)
                
                for emotion, intensity in emotions.items():
                    if intensity > 0.5:  # Only consider significant emotions
                        if emotion not in emotional_memories:
                            emotional_memories[emotion] = []
                        emotional_memories[emotion].append(memory)
            
            # Create patterns for frequently occurring emotions
            for emotion, emotion_memories in emotional_memories.items():
                if len(emotion_memories) >= self.min_pattern_frequency:
                    pattern = DetectedPattern(
                        pattern_type=PatternType.EMOTIONAL,
                        title=f"{emotion.title()} Emotional Pattern",
                        description=f"User frequently expresses {emotion} in conversations",
                        confidence=min(1.0, len(emotion_memories) / 6.0),
                        supporting_memories=[m.get('id', '') for m in emotion_memories],
                        frequency=len(emotion_memories),
                        first_occurrence=self._get_earliest_timestamp(emotion_memories),
                        last_occurrence=self._get_latest_timestamp(emotion_memories),
                        metadata={'emotion': emotion}
                    )
                    patterns.append(pattern)
                    
        except Exception as e:
            logger.warning("Error detecting emotional patterns: %s", str(e))
        
        return patterns
    
    async def _detect_conversational_patterns(self, memories: List[Dict[str, Any]]) -> List[DetectedPattern]:
        """Detect conversational style patterns"""
        patterns = []
        
        try:
            # Analyze conversational characteristics
            question_memories = []
            detailed_memories = []
            short_memories = []
            
            for memory in memories:
                content = memory.get('content', '') or memory.get('user_message', '')
                
                if '?' in content:
                    question_memories.append(memory)
                
                if len(content) > 100:
                    detailed_memories.append(memory)
                elif len(content) < 30:
                    short_memories.append(memory)
            
            # Create patterns for conversation styles
            if len(question_memories) >= self.min_pattern_frequency:
                pattern = DetectedPattern(
                    pattern_type=PatternType.CONVERSATIONAL,
                    title="Questioning Communication Style",
                    description="User frequently asks questions in conversations",
                    confidence=min(1.0, len(question_memories) / 10.0),
                    supporting_memories=[m.get('id', '') for m in question_memories],
                    frequency=len(question_memories),
                    first_occurrence=self._get_earliest_timestamp(question_memories),
                    last_occurrence=self._get_latest_timestamp(question_memories),
                    metadata={'style': 'questioning'}
                )
                patterns.append(pattern)
            
            if len(detailed_memories) >= self.min_pattern_frequency:
                pattern = DetectedPattern(
                    pattern_type=PatternType.CONVERSATIONAL,
                    title="Detailed Communication Style",
                    description="User tends to provide detailed, comprehensive messages",
                    confidence=min(1.0, len(detailed_memories) / 8.0),
                    supporting_memories=[m.get('id', '') for m in detailed_memories],
                    frequency=len(detailed_memories),
                    first_occurrence=self._get_earliest_timestamp(detailed_memories),
                    last_occurrence=self._get_latest_timestamp(detailed_memories),
                    metadata={'style': 'detailed'}
                )
                patterns.append(pattern)
                
        except Exception as e:
            logger.warning("Error detecting conversational patterns: %s", str(e))
        
        return patterns
    
    async def _detect_preference_patterns(self, memories: List[Dict[str, Any]]) -> List[DetectedPattern]:
        """Detect preference patterns"""
        patterns = []
        
        try:
            # Look for preference indicators
            preference_keywords = [
                'prefer', 'like', 'love', 'enjoy', 'favorite', 'best',
                'dislike', 'hate', 'worst', 'avoid', 'never', 'dont like'
            ]
            
            preference_memories = []
            for memory in memories:
                content = memory.get('content', '') or memory.get('user_message', '')
                if any(keyword in content.lower() for keyword in preference_keywords):
                    preference_memories.append(memory)
            
            if len(preference_memories) >= self.min_pattern_frequency:
                pattern = DetectedPattern(
                    pattern_type=PatternType.PREFERENCE,
                    title="Strong Preferences Pattern",
                    description="User frequently expresses clear preferences and opinions",
                    confidence=min(1.0, len(preference_memories) / 7.0),
                    supporting_memories=[m.get('id', '') for m in preference_memories],
                    frequency=len(preference_memories),
                    first_occurrence=self._get_earliest_timestamp(preference_memories),
                    last_occurrence=self._get_latest_timestamp(preference_memories),
                    metadata={'preference_indicators': preference_keywords}
                )
                patterns.append(pattern)
                
        except Exception as e:
            logger.warning("Error detecting preference patterns: %s", str(e))
        
        return patterns
    
    def _group_memories_by_time(self, memories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group memories by time periods"""
        time_groups = {
            'morning': [],
            'afternoon': [],
            'evening': [],
            'night': []
        }
        
        for memory in memories:
            timestamp = memory.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    
                    hour = dt.hour
                    if 6 <= hour < 12:
                        time_groups['morning'].append(memory)
                    elif 12 <= hour < 18:
                        time_groups['afternoon'].append(memory)
                    elif 18 <= hour < 22:
                        time_groups['evening'].append(memory)
                    else:
                        time_groups['night'].append(memory)
                        
                except Exception:
                    continue
        
        return time_groups
    
    def _detect_simple_emotions(self, content: str) -> Dict[str, float]:
        """Simple emotion detection based on keywords"""
        emotions = {}
        
        emotion_keywords = {
            'joy': ['happy', 'excited', 'great', 'awesome', 'wonderful', 'amazing'],
            'sadness': ['sad', 'depressed', 'down', 'upset', 'disappointed'],
            'anger': ['angry', 'frustrated', 'annoyed', 'mad', 'irritated'],
            'fear': ['scared', 'worried', 'anxious', 'nervous', 'afraid'],
            'surprise': ['surprised', 'shocked', 'unexpected', 'wow']
        }
        
        content_lower = content.lower()
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                emotions[emotion] = min(1.0, score / 3.0)  # Normalize score
        
        return emotions
    
    def _get_earliest_timestamp(self, memories: List[Dict[str, Any]]) -> Optional[datetime]:
        """Get earliest timestamp from memory list"""
        timestamps = []
        for memory in memories:
            timestamp = memory.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    timestamps.append(dt)
                except Exception:
                    continue
        
        return min(timestamps) if timestamps else None
    
    def _get_latest_timestamp(self, memories: List[Dict[str, Any]]) -> Optional[datetime]:
        """Get latest timestamp from memory list"""
        timestamps = []
        for memory in memories:
            timestamp = memory.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    timestamps.append(dt)
                except Exception:
                    continue
        
        return max(timestamps) if timestamps else None