"""
spaCy-Based Stance Analysis for Emotion Attribution Detection

Analyzes WHO holds emotions in text (first-person, second-person, third-person)
and filters out misattributed emotions before RoBERTa classification.

Key Problem Solved:
- User says: "You seem frustrated" → Without stance filtering, RoBERTa classifies
  user as frustrated. WITH stance filtering, we recognize this is SECOND-PERSON
  attribution and don't classify user's actual emotion from it.
- Bot says: "I understand you're upset" → Without filtering, bot's empathetic
  statement pollutes bot's emotional state. WITH filtering, we remove the
  "you're upset" clause and analyze only the bot's actual stance.

Architecture:
1. Parse text with spaCy dependency parsing
2. Find emotion words and their subjects using four detection strategies
3. Classify emotions as self/other/attributed
4. Return filtered text appropriate for primary speaker's perspective
5. Return stance metadata for context

Usage:
    from src.intelligence.spacy_stance_analyzer import StanceAnalyzer
    
    analyzer = StanceAnalyzer()
    
    # Analyze user message
    user_stance = analyzer.analyze_user_stance("I'm frustrated with you")
    # Returns: primary_emotions=['frustrated'], self_focus=1.0, emotion_type='direct'
    
    # Filter bot response to find bot's true stance
    filtered_bot = analyzer.filter_second_person_emotions(
        "I understand you're frustrated. I'm here to help."
    )
    # Returns: "I'm here to help." (with "you're frustrated" removed)
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from src.nlp.spacy_manager import get_spacy_nlp

logger = logging.getLogger(__name__)


@dataclass
class StanceAnalysis:
    """Result of stance analysis on text"""
    primary_emotions: List[str]  # User's/bot's actual emotions
    other_emotions: List[str]    # Attributed emotions (to others)
    self_focus: float            # Ratio of self-focused emotions (0.0 to 1.0)
    emotion_type: str            # 'direct', 'attributed', 'mixed', 'none'
    filtered_text: Optional[str] # Text with second-person emotions removed
    stance_subjects: Dict[str, str]  # emotion -> subject (first/second/third)
    has_negation: Dict[str, bool]    # emotion -> has negation modifier
    confidence: float            # Confidence in stance detection (0.0 to 1.0)


class StanceAnalyzer:
    """
    Analyzes emotion attribution and filters text based on speaker perspective.
    
    Uses spaCy dependency parsing to:
    1. Identify emotion words
    2. Trace back to their grammatical subjects
    3. Classify emotions as first/second/third-person
    4. Filter out misattributed emotions
    5. Provide stance metadata for emotional analysis
    """
    
    def __init__(self):
        """Initialize stance analyzer with shared spaCy singleton"""
        self.nlp = get_spacy_nlp()
        
        if not self.nlp:
            logger.warning("⚠️ spaCy not available - stance analysis will be disabled")
        
        # Comprehensive emotion word list (expandable)
        self.emotion_words = {
            # Positive emotions
            'joy', 'happy', 'delighted', 'pleased', 'cheerful', 'elated', 'ecstatic',
            'thrilled', 'wonderful', 'amazing', 'fantastic', 'great',
            'awesome', 'love', 'adore', 'bliss', 'euphoric', 'overjoyed', 'gleeful',
            'jubilant', 'radiant', 'beaming', 'contentment', 'content', 'satisfied',
            'peaceful', 'calm', 'serene', 'relaxed', 'comfortable', 'at ease',
            'hope', 'hopeful', 'optimistic', 'positive', 'encouraging', 'bright',
            'grateful', 'thankful', 'appreciate', 'blessed', 'gratitude',
            'excited', 'excitement', 'enthusiasm', 'enthusiastic',
            
            # Negative emotions
            'sad', 'unhappy', 'depressed', 'melancholy', 'sorrowful', 'grief',
            'disappointed', 'heartbroken', 'down', 'blue', 'gloomy', 'miserable',
            'angry', 'mad', 'furious', 'rage', 'irritated', 'annoyed', 'frustrated',
            'outraged', 'livid', 'incensed', 'hostile', 'aggressive', 'hate', 'disgust',
            'disgusted', 'appalled', 'infuriated', 'upset', 'bothered', 'irate', 'defensive',
            'afraid', 'scared', 'frightened', 'terrified', 'worried', 'anxious',
            'nervous', 'panic', 'dread', 'horror', 'alarmed', 'startled',
            'intimidated', 'threatened', 'uneasy', 'apprehensive', 'petrified',
            'ashamed', 'embarrassed', 'humiliated', 'mortified', 'guilty',
            'regretful', 'remorseful', 'sheepish', 'chagrined',
            
            # Complex emotions
            'interested', 'curious', 'curiosity',
            'puzzled', 'confused', 'bewildered', 'perplexed', 'wondering',
            'surprised', 'shocked', 'amazed', 'astonished', 'stunned',
            'anticipation', 'anticipate', 'expecting', 'expect',
            'trust', 'trustworthy', 'trustful', 'confidence', 'confident',
            'lonely', 'isolated', 'alone', 'solitary', 'abandoned', 'forsaken',
            
            # Intensity words (also emotion indicators)
            'devastated', 'crushed', 'destroyed', 'wrecked', 'exhausted',
            'overwhelmed', 'stressed', 'pressure', 'tension', 'restless',
            'tired', 'exhaustion', 'weary', 'fatigued',
        }
        
        # Pronouns indicating speaker perspective
        self.first_person_pronouns = {'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'}
        self.second_person_pronouns = {'you', 'your', 'yours'}
        self.third_person_pronouns = {'he', 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'they', 'them', 'their', 'theirs'}
        
        # Negation modifiers
        self.negation_markers = {'not', 'no', 'never', 'neither', 'nobody', 'nothing', "n't"}
        
        logger.info("✅ StanceAnalyzer initialized with spaCy singleton")
    
    def analyze_user_stance(self, text: str) -> StanceAnalysis:
        """
        Analyze user's emotional stance in text.
        
        Separates user's actual emotions from emotions attributed to others.
        Example: "I'm frustrated with your suggestions, but you seem defensive"
        - primary_emotions: ['frustrated'] (user's emotion)
        - other_emotions: ['defensive'] (attributed to 'you')
        - self_focus: 0.5 (50% about user's own state)
        
        Args:
            text: User's message text
            
        Returns:
            StanceAnalysis with primary/other emotions and self-focus ratio
        """
        if not self.nlp:
            logger.warning("⚠️ spaCy not available - returning empty stance analysis")
            return StanceAnalysis(
                primary_emotions=[],
                other_emotions=[],
                self_focus=0.0,
                emotion_type='none',
                filtered_text=None,
                stance_subjects={},
                has_negation={},
                confidence=0.0
            )
        
        try:
            doc = self.nlp(text)
            
            # Find all emotion words and their subjects
            emotion_subjects = self._detect_emotion_subjects(doc)
            
            if not emotion_subjects:
                return StanceAnalysis(
                    primary_emotions=[],
                    other_emotions=[],
                    self_focus=0.0,
                    emotion_type='none',
                    filtered_text=text,
                    stance_subjects={},
                    has_negation={},
                    confidence=1.0
                )
            
            # Classify emotions by subject perspective
            primary_emotions = []  # First-person emotions
            other_emotions = []    # Second/third-person emotions
            stance_subjects = {}
            has_negation = {}
            
            for emotion_text, subject_person, has_neg in emotion_subjects:
                # Normalize emotion word
                emotion_normalized = emotion_text.lower().strip()
                
                # Check for negation modifier
                has_negation[emotion_normalized] = has_neg
                
                if subject_person == 'first':
                    primary_emotions.append(emotion_normalized)
                    stance_subjects[emotion_normalized] = 'first'
                else:
                    other_emotions.append(emotion_normalized)
                    stance_subjects[emotion_normalized] = subject_person
            
            # Calculate self-focus ratio
            total_emotions = len(primary_emotions) + len(other_emotions)
            self_focus = len(primary_emotions) / total_emotions if total_emotions > 0 else 0.0
            
            # Determine emotion type
            if len(primary_emotions) > 0 and len(other_emotions) == 0:
                emotion_type = 'direct'
            elif len(primary_emotions) == 0 and len(other_emotions) > 0:
                emotion_type = 'attributed'
            elif len(primary_emotions) > 0 and len(other_emotions) > 0:
                emotion_type = 'mixed'
            else:
                emotion_type = 'none'
            
            # Confidence based on clarity of emotion attribution
            confidence = 0.85 if emotion_subjects else 0.0
            
            logger.debug(
                "USER STANCE: emotions=%s, attributed=%s, self_focus=%.2f, type=%s",
                primary_emotions, other_emotions, self_focus, emotion_type
            )
            
            return StanceAnalysis(
                primary_emotions=primary_emotions,
                other_emotions=other_emotions,
                self_focus=self_focus,
                emotion_type=emotion_type,
                filtered_text=text,
                stance_subjects=stance_subjects,
                has_negation=has_negation,
                confidence=confidence
            )
            
        except ValueError as e:
            logger.error("Error analyzing user stance: %s", e)
            return StanceAnalysis(
                primary_emotions=[],
                other_emotions=[],
                self_focus=0.0,
                emotion_type='none',
                filtered_text=text,
                stance_subjects={},
                has_negation={},
                confidence=0.0
            )
    
    def filter_second_person_emotions(self, text: str) -> str:
        """
        Remove second-person emotion statements from text.
        
        This filters out bot's empathetic echoing to isolate bot's true emotional stance.
        
        Example Input:
            "I understand you're frustrated. I'm here to help you feel better."
        
        After filtering:
            "I'm here to help you feel better."
            (removes "you're frustrated" clause)
        
        Why this works:
        - Removes misattribution of user's emotions to bot
        - Preserves bot's genuine emotional expression
        - Filters out empathetic/contextual statements that aren't bot's own state
        
        Args:
            text: Bot's response text
            
        Returns:
            Filtered text with second-person emotion clauses removed
        """
        if not self.nlp:
            logger.warning("⚠️ spaCy not available - returning unfiltered text")
            return text
        
        try:
            doc = self.nlp(text)
            
            # Find all emotion words and their subjects
            emotion_subjects = self._detect_emotion_subjects(doc)
            
            if not emotion_subjects:
                return text
            
            # Find clauses containing second-person emotions
            clauses_to_remove = []
            
            for emotion_text, subject_person, _ in emotion_subjects:
                if subject_person == 'second':
                    # Find the emotion token in doc
                    for token in doc:
                        if token.text.lower() == emotion_text.lower():
                            # Find clause by looking for sentence boundaries (periods)
                            clause_start = 0
                            for i in range(token.i - 1, -1, -1):
                                if doc[i].text in ('.', '!', '?'):
                                    clause_start = i + 1
                                    break
                            
                            # End: next period or end of text
                            clause_end = len(doc)
                            for i in range(token.i + 1, len(doc)):
                                if doc[i].text in ('.', '!', '?'):
                                    clause_end = i + 1
                                    break
                            
                            clauses_to_remove.append((clause_start, clause_end))
                            break
            
            if not clauses_to_remove:
                return text
            
            # Merge overlapping clauses
            if clauses_to_remove:
                clauses_to_remove.sort()
                merged_clauses = [clauses_to_remove[0]]
                for start, end in clauses_to_remove[1:]:
                    if start <= merged_clauses[-1][1]:
                        merged_clauses[-1] = (merged_clauses[-1][0], max(end, merged_clauses[-1][1]))
                    else:
                        merged_clauses.append((start, end))
                clauses_to_remove = merged_clauses
            
            # Reconstruct by skipping removed clauses
            remaining_text = ""
            
            for i, token in enumerate(doc):
                skip_token = False
                for clause_start, clause_end in clauses_to_remove:
                    if clause_start <= i < clause_end:
                        skip_token = True
                        break
                
                if skip_token:
                    continue
                
                # Add token with proper spacing
                if token.whitespace_:
                    remaining_text += token.text + token.whitespace_
                else:
                    remaining_text += token.text
            
            # Clean up result
            filtered = remaining_text.strip()
            filtered = ' '.join(filtered.split())
            
            logger.debug(
                "FILTER SECOND-PERSON: Removed %d clause(s)\nOriginal: %s\nFiltered: %s",
                len(clauses_to_remove), text, filtered
            )
            
            return filtered if filtered else text
            
        except ValueError as e:
            logger.error("Error filtering second-person emotions: %s", e)
            return text
    
    def _detect_emotion_subjects(self, doc) -> List[Tuple[str, str, bool]]:
        """
        Find emotion words in text and identify their grammatical subjects.
        
        Uses four detection strategies:
        1. Direct subject (nsubj dependency)
        2. Head relationship (emotion modifies verb with subject)
        3. Grand-parent relationships (nested structures)
        4. Possessive detection (my/your emotion)
        
        Args:
            doc: spaCy Doc object
            
        Returns:
            List of tuples: (emotion_word, subject_person, has_negation)
            where subject_person is 'first', 'second', or 'third'
        """
        emotion_subjects = []
        
        for token in doc:
            # Check if this token is an emotion word
            if token.text.lower() not in self.emotion_words:
                continue
            
            # Check for negation modifier (token has "not" parent)
            has_negation = self._has_negation_modifier(token)
            
            # Try four strategies to find subject
            subject_person = self._detect_subject_strategy_1(token)  # Direct subject
            
            if not subject_person:
                subject_person = self._detect_subject_strategy_2(token)  # Head relationship
            
            if not subject_person:
                subject_person = self._detect_subject_strategy_3(token)  # Grand-parent
            
            if not subject_person:
                subject_person = self._detect_subject_strategy_4(token)  # Possessive
            
            # Default to first-person if unclear (conservative)
            if not subject_person:
                subject_person = 'first'
            
            emotion_subjects.append((token.text, subject_person, has_negation))
        
        return emotion_subjects
    
    def _detect_subject_strategy_1(self, token) -> Optional[str]:
        """
        Strategy 1: Check if emotion token's children include a subject (nsubj/nsubjpass).
        
        Example: "I hate vegetables" → "hate" has child "I" with nsubj
        """
        for child in token.children:
            if child.dep_ in ('nsubj', 'nsubjpass'):
                return self._classify_pronoun(child.text)
        
        return None
    
    def _detect_subject_strategy_2(self, token) -> Optional[str]:
        """
        Strategy 2: If emotion modifies a verb/aux (acomp/oprd/xcomp), check verb's subject.
        
        Example: "I am frustrated" → "frustrated" (acomp) head is "am" (AUX)
                → "am" head is "I" (subject indirectly)
        Example: "You seem upset" → "upset" (oprd) head is "seem" (VERB)
                → "seem" has child "You" (subject)
        Example: "you're frustrated" → "frustrated" (acomp) head is "'re" (AUX, ccomp child of verb)
                → Need to find "you" which is nsubj of the verb containing this chain
        """
        # Direct check: is head a VERB?
        if token.head and token.head.pos_ == 'VERB':
            for child in token.head.children:
                if child.dep_ in ('nsubj', 'nsubjpass'):
                    return self._classify_pronoun(child.text)
        
        # Check if head is AUX (can be part of verb chain)
        if token.head and token.head.pos_ == 'AUX':
            # The AUX's children might include the subject
            for child in token.head.children:
                if child.dep_ in ('nsubj', 'nsubjpass'):
                    return self._classify_pronoun(child.text)
            
            # The AUX's head might be a verb with the subject
            if token.head.head:
                for child in token.head.head.children:
                    if child.dep_ in ('nsubj', 'nsubjpass'):
                        return self._classify_pronoun(child.text)
        
        return None
    
    def _detect_subject_strategy_3(self, token) -> Optional[str]:
        """
        Strategy 3: Grand-parent relationship for nested structures.
        
        Example: "I feel completely devastated" → "devastated" head is "feel"
                → "feel" head is eventually a subject or root
        """
        if token.head and token.head.head:
            grandparent = token.head.head
            for child in grandparent.children:
                if child.dep_ in ('nsubj', 'nsubjpass'):
                    return self._classify_pronoun(child.text)
        
        return None
    
    def _detect_subject_strategy_4(self, token) -> Optional[str]:
        """
        Strategy 4: Possessive detection (my/your emotion).
        
        Example: "My frustration is evident" → "frustration" has child "My" (poss)
        Example: "Your concerns are valid" → "concerns" has child "Your" (poss)
        """
        for child in token.children:
            if child.dep_ == 'poss':
                return self._classify_pronoun(child.text)
        
        # Check if token itself is possessive
        if token.dep_ == 'poss':
            return self._classify_pronoun(token.text)
        
        return None
    
    def _has_negation_modifier(self, token) -> bool:
        """
        Check if token has a negation modifier (not, no, never, etc.).
        
        Example: "not frustrated" → True
        Example: "frustrated" → False
        """
        for child in token.children:
            if child.dep_ == 'neg' or child.text.lower() in self.negation_markers:
                return True
        
        # Check if parent is negation
        if token.head and token.head.text.lower() in self.negation_markers:
            return True
        
        return False
    
    def _classify_pronoun(self, pronoun_text: str) -> Optional[str]:
        """
        Classify a pronoun as first, second, or third person.
        
        Args:
            pronoun_text: The pronoun text to classify
            
        Returns:
            'first', 'second', 'third', or None if not a pronoun
        """
        lower_text = pronoun_text.lower()
        
        if lower_text in self.first_person_pronouns:
            return 'first'
        elif lower_text in self.second_person_pronouns:
            return 'second'
        elif lower_text in self.third_person_pronouns:
            return 'third'
        
        return None


def create_stance_analyzer() -> StanceAnalyzer:
    """
    Factory function to create a StanceAnalyzer instance.
    
    Returns:
        StanceAnalyzer instance using shared spaCy singleton
    """
    return StanceAnalyzer()
