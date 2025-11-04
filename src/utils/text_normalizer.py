"""
Text normalization utilities for WhisperEngine NLP pipeline.

Provides context-aware text cleaning to improve spaCy accuracy while
preserving semantic information through replacement tokens.

Design Philosophy:
- Use replacement tokens ([URL], [MENTION]) instead of deletion
- Preserve text structure for robust spaCy parsing
- Context-aware: Different modes for different pipeline components
- Signal presence: Tokens show that something was there
"""

import re
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class TextNormalizationMode(Enum):
    """
    Normalization modes for different WhisperEngine pipeline components.
    
    Each mode optimizes for specific NLP tasks while maintaining text quality.
    """
    EMOTION_ANALYSIS = "emotion"      # Keep emojis, replace mentions/URLs (RoBERTa)
    ENTITY_EXTRACTION = "entity"      # Full cleaning for spaCy NER
    SUMMARIZATION = "summary"         # Minimal cleaning, preserve tone
    PATTERN_MATCHING = "pattern"      # Full normalization for regex/lemma matching
    LLM_PROMPT = "llm"               # Clean mentions, keep natural context


class DiscordTextNormalizer:
    """
    Context-aware text normalization for WhisperEngine pipeline.
    
    Handles Discord-specific artifacts (mentions, formatting, emojis) while
    preserving semantic information through intelligent replacement tokens.
    
    Usage:
        normalizer = DiscordTextNormalizer()
        
        # For RoBERTa emotion analysis (keep emojis):
        text = normalizer.normalize(message, TextNormalizationMode.EMOTION_ANALYSIS)
        
        # For spaCy entity extraction (full cleaning):
        text = normalizer.normalize(message, TextNormalizationMode.ENTITY_EXTRACTION)
        
        # For LLM fact extraction (natural context):
        text = normalizer.normalize(message, TextNormalizationMode.LLM_PROMPT)
    """
    
    def __init__(self):
        """Initialize normalizer with compiled regex patterns for performance."""
        # URL patterns
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        
        # Discord mention patterns
        self.user_mention_pattern = re.compile(r'<@!?\d+>')
        self.channel_mention_pattern = re.compile(r'<#\d+>')
        self.role_mention_pattern = re.compile(r'<@&\d+>')
        self.username_mention_pattern = re.compile(r'(?<!\S)@\w+')
        
        # Discord formatting patterns
        self.bold_pattern = re.compile(r'\*\*(.+?)\*\*')
        self.underline_pattern = re.compile(r'__(.+?)__')
        self.strikethrough_pattern = re.compile(r'~~(.+?)~~')
        self.inline_code_pattern = re.compile(r'`(.+?)`')
        self.code_block_pattern = re.compile(r'```.*?```', re.DOTALL)
        
        # Emoji patterns (comprehensive Unicode ranges)
        self.emoji_patterns = [
            re.compile(r'[\U0001F600-\U0001F64F]'),  # Emoticons
            re.compile(r'[\U0001F300-\U0001F5FF]'),  # Symbols & pictographs
            re.compile(r'[\U0001F680-\U0001F6FF]'),  # Transport & map symbols
            re.compile(r'[\U0001F1E0-\U0001F1FF]'),  # Flags
            re.compile(r'[\U00002702-\U000027B0]'),  # Dingbats
            re.compile(r'[\U000024C2-\U0001F251]'),  # Enclosed characters
            re.compile(r'[\U0001F900-\U0001F9FF]'),  # Supplemental Symbols and Pictographs
            re.compile(r'[\U0001FA00-\U0001FA6F]'),  # Chess Symbols
            re.compile(r'[\U0001FA70-\U0001FAFF]'),  # Symbols and Pictographs Extended-A
        ]
        
        # Whitespace normalization
        self.whitespace_pattern = re.compile(r'\s+')
        
        logger.info("DiscordTextNormalizer initialized with compiled regex patterns")
    
    def normalize(self, text: str, mode: TextNormalizationMode) -> str:
        """
        Apply context-aware normalization based on processing mode.
        
        Args:
            text: Raw text to normalize (Discord message, conversation window, etc.)
            mode: Normalization mode for specific pipeline component
            
        Returns:
            Normalized text optimized for the target NLP task
            
        Examples:
            >>> normalizer = DiscordTextNormalizer()
            >>> text = "I love @john's pizza from https://example.com 🍕"
            
            >>> normalizer.normalize(text, TextNormalizationMode.EMOTION_ANALYSIS)
            'I love [MENTION] pizza from [URL] 🍕'
            
            >>> normalizer.normalize(text, TextNormalizationMode.ENTITY_EXTRACTION)
            'I love [MENTION] pizza from [URL]'
        """
        if not text:
            return ""
        
        logger.debug("Normalizing text with mode=%s: '%s...'", mode.value, text[:100])
        
        if mode == TextNormalizationMode.EMOTION_ANALYSIS:
            return self._normalize_for_emotion_analysis(text)
        
        elif mode == TextNormalizationMode.ENTITY_EXTRACTION:
            return self._normalize_for_entity_extraction(text)
        
        elif mode == TextNormalizationMode.SUMMARIZATION:
            return self._normalize_for_summarization(text)
        
        elif mode == TextNormalizationMode.PATTERN_MATCHING:
            return self._normalize_for_pattern_matching(text)
        
        elif mode == TextNormalizationMode.LLM_PROMPT:
            return self._normalize_for_llm_prompt(text)
        
        else:
            logger.warning("Unknown normalization mode: %s, returning original text", mode)
            return text
    
    def _normalize_for_emotion_analysis(self, text: str) -> str:
        """
        Normalize for RoBERTa emotion analysis.
        
        Strategy:
        - KEEP emojis (emotional signals)
        - REPLACE mentions/URLs (structural noise)
        - KEEP formatting emphasis (signals intensity)
        
        Why: RoBERTa models benefit from emotional cues like emojis and emphasis,
        but Discord artifacts pollute the transformer's attention mechanism.
        """
        # Replace structural noise
        text = self._replace_urls(text, '[URL]')
        text = self._replace_mentions(text, '[MENTION]')
        
        # Keep formatting (it signals emotional emphasis)
        # Don't extract content - the ** and __ themselves are signals
        
        # Normalize whitespace
        text = self._normalize_whitespace(text)
        
        logger.debug("Emotion analysis normalization: kept emojis, replaced mentions/URLs")
        return text
    
    def _normalize_for_entity_extraction(self, text: str) -> str:
        """
        Normalize for spaCy entity extraction and dependency parsing.
        
        Strategy:
        - REMOVE emojis (tokenization noise)
        - REPLACE mentions/URLs (preserve structure)
        - EXTRACT content from formatting (preserve emphasized words)
        - PRESERVE case (NER models need proper capitalization)
        
        Why: spaCy NER models were trained on clean text with proper capitalization.
        Discord artifacts break tokenization and confuse POS tagging.
        """
        # Replace structural noise with tokens
        text = self._replace_urls(text, '[URL]')
        text = self._replace_mentions(text, '[MENTION]')
        
        # Extract content from Discord formatting (keep the words, remove markup)
        text = self._extract_formatting_content(text)
        
        # Remove emojis (they break tokenization)
        text = self._remove_emojis(text)
        
        # Normalize whitespace
        text = self._normalize_whitespace(text)
        
        # PRESERVE CASE for proper noun detection
        
        logger.debug("Entity extraction normalization: removed emojis, preserved case")
        return text
    
    def _normalize_for_summarization(self, text: str) -> str:
        """
        Normalize for LLM summarization.
        
        Strategy:
        - MINIMAL cleaning (preserve natural language)
        - REPLACE mentions (privacy + clarity)
        - KEEP URLs (might be discussed topics)
        - KEEP emojis (tone indicators)
        - KEEP formatting (emphasis signals)
        
        Why: Summarization needs natural context. Over-cleaning loses semantic richness.
        """
        # Only replace mentions for privacy/clarity
        text = self._replace_mentions(text, '[USER]')
        
        # Keep everything else for context
        
        # Normalize whitespace
        text = self._normalize_whitespace(text)
        
        logger.debug("Summarization normalization: minimal cleaning, preserved context")
        return text
    
    def _normalize_for_pattern_matching(self, text: str) -> str:
        """
        Normalize for lemmatization and regex pattern matching.
        
        Strategy:
        - LOWERCASE (case-insensitive matching)
        - REMOVE emojis (not useful for patterns)
        - REPLACE mentions/URLs
        - EXTRACT formatting content
        
        Why: Pattern matching needs consistent, clean text. Case and noise interfere
        with lemma-based matching.
        """
        # Full cleaning
        text = self._replace_urls(text, '[URL]')
        text = self._replace_mentions(text, '[MENTION]')
        text = self._extract_formatting_content(text)
        text = self._remove_emojis(text)
        
        # Normalize whitespace
        text = self._normalize_whitespace(text)
        
        # LOWERCASE for case-insensitive matching
        text = text.lower()
        
        logger.debug("Pattern matching normalization: lowercased, full cleaning")
        return text
    
    def _normalize_for_llm_prompt(self, text: str) -> str:
        """
        Normalize for LLM fact extraction prompts.
        
        Strategy:
        - REPLACE mentions with natural placeholder (@User)
        - KEEP URLs (might be named entities: "shared link to...")
        - KEEP emojis (emotional context helps LLM)
        - EXTRACT formatting content (preserve emphasized words)
        - PRESERVE case (natural language)
        
        Why: LLMs need natural, human-readable context. Over-cleaning loses
        information that helps with semantic understanding.
        """
        # Replace mentions with natural placeholder
        text = self._replace_mentions(text, '@User')
        
        # Extract content from formatting (but keep the words)
        text = self._extract_formatting_content(text)
        
        # Keep URLs, emojis for context
        
        # Normalize whitespace
        text = self._normalize_whitespace(text)
        
        logger.debug("LLM prompt normalization: natural language, preserved context")
        return text
    
    # ============================================================================
    # Helper Methods: Replacement Token Operations
    # ============================================================================
    
    def _replace_urls(self, text: str, replacement: str = '[URL]') -> str:
        """Replace URLs with token to preserve structure."""
        return self.url_pattern.sub(replacement, text)
    
    def _replace_mentions(self, text: str, replacement: str = '[MENTION]') -> str:
        """Replace all Discord mention types with token."""
        # User mentions: <@123456789> or <@!123456789>
        text = self.user_mention_pattern.sub(replacement, text)
        
        # Channel mentions: <#123456789>
        text = self.channel_mention_pattern.sub('[CHANNEL]', text)
        
        # Role mentions: <@&123456789>
        text = self.role_mention_pattern.sub('[ROLE]', text)
        
        # @username mentions (but not email addresses)
        text = self.username_mention_pattern.sub(replacement, text)
        
        return text
    
    def _extract_formatting_content(self, text: str) -> str:
        """
        Extract content from Discord formatting markup.
        
        Preserves the emphasized words while removing the markup noise.
        Example: "**bold**" → "bold"
        """
        # Remove code blocks entirely (code is not natural language)
        text = self.code_block_pattern.sub('', text)
        
        # Extract content from formatting
        text = self.bold_pattern.sub(r'\1', text)              # **bold** → bold
        text = self.underline_pattern.sub(r'\1', text)         # __underline__ → underline
        text = self.strikethrough_pattern.sub(r'\1', text)     # ~~strike~~ → strike
        text = self.inline_code_pattern.sub(r'\1', text)       # `code` → code
        
        return text
    
    def _remove_emojis(self, text: str) -> str:
        """Remove emojis from text (for entity extraction)."""
        for emoji_pattern in self.emoji_patterns:
            text = emoji_pattern.sub('', text)
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Collapse multiple spaces, newlines, tabs into single space."""
        text = self.whitespace_pattern.sub(' ', text)
        text = text.strip()
        
        # Remove leading punctuation (cleaner sentence boundaries)
        text = re.sub(r'^\s*[,;:]\s*', '', text)
        
        return text
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def get_replacement_tokens(self) -> list[str]:
        """
        Get list of replacement tokens used by normalizer.
        
        Useful for filtering these out after processing (e.g., in lemmatization).
        """
        return ['[url]', '[mention]', '[channel]', '[role]', '@user']
    
    def should_filter_token(self, token: str) -> bool:
        """
        Check if token is a replacement token that should be filtered.
        
        Useful for post-processing (e.g., removing tokens from lemmatized output).
        """
        return token.lower() in self.get_replacement_tokens()


# ============================================================================
# Convenience Functions
# ============================================================================

# Module-level singleton for performance (compiled regex patterns)
_NORMALIZER_INSTANCE: Optional[DiscordTextNormalizer] = None


def get_text_normalizer() -> DiscordTextNormalizer:
    """Get singleton normalizer instance (avoids recompiling regex patterns)."""
    # pylint: disable=global-statement
    global _NORMALIZER_INSTANCE
    
    if _NORMALIZER_INSTANCE is None:
        _NORMALIZER_INSTANCE = DiscordTextNormalizer()
        logger.info("Created singleton DiscordTextNormalizer instance")
    
    return _NORMALIZER_INSTANCE


def normalize_for_entity_extraction(text: str, preserve_case: bool = True) -> str:
    """
    Convenience function for entity extraction normalization.
    
    Args:
        text: Raw text
        preserve_case: If True, keeps original case (recommended for NER)
    
    Returns:
        Cleaned text ready for spaCy entity extraction
    """
    normalizer = get_text_normalizer()
    normalized = normalizer.normalize(text, TextNormalizationMode.ENTITY_EXTRACTION)
    
    if not preserve_case:
        normalized = normalized.lower()
    
    return normalized


def normalize_for_emotion_analysis(text: str) -> str:
    """
    Convenience function for emotion analysis normalization.
    
    Keeps emojis, replaces mentions/URLs.
    """
    normalizer = get_text_normalizer()
    return normalizer.normalize(text, TextNormalizationMode.EMOTION_ANALYSIS)


def normalize_for_pattern_matching(text: str) -> str:
    """
    Convenience function for pattern matching normalization.
    
    Lowercases and fully cleans text.
    """
    normalizer = get_text_normalizer()
    return normalizer.normalize(text, TextNormalizationMode.PATTERN_MATCHING)


def normalize_for_llm_prompt(text: str) -> str:
    """
    Convenience function for LLM prompt normalization.
    
    Preserves natural language context.
    """
    normalizer = get_text_normalizer()
    return normalizer.normalize(text, TextNormalizationMode.LLM_PROMPT)
