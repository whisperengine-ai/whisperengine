"""
Mystical Symbol Detector for WhisperEngine.

Detects and filters out messages containing mystical/esoteric unicode symbols
and ritualistic math formulas that may be used for spam or unwanted content injection.
"""

import re
import unicodedata
from typing import Set, Tuple


class MysticalSymbolDetector:
    """Detects mystical and esoteric unicode symbols in text."""
    
    def __init__(self):
        """Initialize detector with mystical symbol unicode ranges."""
        # Unicode ranges for mystical/esoteric symbols
        self.mystical_ranges = [
            (0x2600, 0x26FF),  # Miscellaneous Symbols (includes astrological, religious symbols)
            (0x2700, 0x27BF),  # Dingbats (includes religious and mystical symbols)
            (0x2B00, 0x2BFF),  # Miscellaneous Symbols and Arrows
            (0x1F780, 0x1F7FF),  # Geometric Shapes Extended
            (0x1FA00, 0x1FA6F),  # Chess Symbols
            (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
        ]
        
        # Specific mystical/esoteric symbols to detect
        self.mystical_symbols = {
            # Zodiac signs
            '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓',
            # Alchemical symbols
            '🜁', '🜂', '🜃', '🜄', '🜅', '🜆', '🜇', '🜈', '🜉', '🜊', '🜋', '🜌',
            # Religious/mystical symbols
            '☪', '☯', '☸', '✡', '🕉', '☦', '🔯',
            # Runes and ancient scripts
            'ᚠ', 'ᚢ', 'ᚦ', 'ᚨ', 'ᚱ', 'ᚲ', 'ᚷ', 'ᚹ', 'ᚺ', 'ᚾ', 'ᛁ', 'ᛃ', 'ᛇ', 'ᛈ', 'ᛉ', 'ᛊ', 'ᛏ', 'ᛒ', 'ᛖ', 'ᛗ', 'ᛚ', 'ᛜ', 'ᛞ', 'ᛟ',
            # Mystical geometric shapes
            '⬟', '⬠', '⬡', '⬢', '⬣', '⯁', '⯂', '⯃', '⯄', '⯅', '⯆', '⯇', '⯈',
            # Esoteric punctuation and marks
            '⁂', '⁜', '※', '⁕', '⁖', '⁘', '⁙', '⁚', '⁛', '⁝', '⁞',
            # Mystical arrows and pointers
            '⤊', '⤋', '⤌', '⤍', '⤎', '⤏', '⤐', '⤑', '⤒', '⤓',
            # Sacred geometry and mandalas
            '🕉️', '☸️', '🔱', '⚛️', '🛐',
            # Occult/esoteric specific
            '⛤', '⛥', '⛦', '⛧',
            # Crystal ball and mystical items
            '🔮',
        }
        
        # Exclude common decorative emojis that aren't mystical
        self.non_mystical_emojis = {
            '✨', '🌟', '💫', '⭐', '🌙', '☀', '☁', '☂', '⛱',  # Weather/decorative
            '✀', '✁', '✂',  # Scissors and tools
            '♠', '♣', '♥', '♦',  # Playing card suits
        }
        
        # Threshold for detection (percentage of mystical characters)
        self.symbol_threshold = 0.20  # 20% or more mystical symbols
        self.min_symbols_for_detection = 3  # Minimum number of mystical symbols
        
        # Ritualistic math patterns - formulas with mystical/esoteric appearance
        self.ritualistic_math_patterns = [
            # Excessive mathematical symbols in non-mathematical context
            r'[∀∃∄∅∆∇∈∉∊∋∌∍∎∏∐∑−∓∔∕∖∗∘∙√∛∜∝∞∟∠∡∢∣∤∥∦∧∨∩∪∫∬∭∮∯∰∱∲∳∴∵∶∷∸∹∺∻∼∽∾∿≀≁≂≃≄≅]{5,}',
            # Repeating mathematical sequences
            r'(?:[∫∑∏∐∇∆√]{3,})',
            # Complex nested brackets with symbols
            r'(?:\[\[\[|\]\]\]|\{\{\{|\}\}\}|\(\(\(|\)\)\))',
            # Unicode mathematical alphanumeric (often used in spam) - check for sequences
            r'[𝐀�𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘�𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝟎𝟏𝟐𝟑������]{10,}',
            # Excessive use of superscript/subscript
            r'[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎]{5,}',
            # Mathematical symbols with mystical arrangement
            r'(?:[∴∵∷⊕⊖⊗⊘⊙⊚⊛⊜⊝⊞⊟⊠⊡]{3,})',
        ]
    
    def _is_in_mystical_range(self, char: str) -> bool:
        """Check if character is in a mystical unicode range."""
        if len(char) != 1:
            return False
        
        # Exclude non-mystical emojis first
        if char in self.non_mystical_emojis:
            return False
        
        codepoint = ord(char)
        return any(start <= codepoint <= end for start, end in self.mystical_ranges)
    
    def _contains_mystical_symbol(self, char: str) -> bool:
        """Check if character is a known mystical symbol."""
        # Exclude non-mystical emojis first
        if char in self.non_mystical_emojis:
            return False
        return char in self.mystical_symbols
    
    def _detect_ritualistic_math(self, text: str) -> Tuple[bool, str]:
        """Detect ritualistic or spam-like mathematical formulas."""
        for pattern in self.ritualistic_math_patterns:
            match = re.search(pattern, text)
            if match:
                matched_text = match.group(0)[:30]  # First 30 chars
                return True, f"Ritualistic math pattern detected: '{matched_text}...'"
        return False, ""
    
    def detect_mystical_content(self, text: str) -> Tuple[bool, str]:
        """
        Detect if text contains significant mystical/esoteric content
        or ritualistic math patterns.
        
        Args:
            text: The message text to analyze
            
        Returns:
            Tuple of (is_suspicious, reason) where:
            - is_suspicious: True if suspicious content detected
            - reason: Description of why it was detected
        """
        if not text or not text.strip():
            return False, ""
        
        # Check for ritualistic math patterns
        is_ritual_math, math_reason = self._detect_ritualistic_math(text)
        if is_ritual_math:
            return True, math_reason
        
        # Count mystical symbols
        mystical_count = 0
        total_chars = 0
        detected_symbols = set()
        
        for char in text:
            # Skip whitespace
            if char.isspace():
                continue
            
            total_chars += 1
            
            # Check if character is mystical
            if self._contains_mystical_symbol(char):
                mystical_count += 1
                detected_symbols.add(char)
            elif self._is_in_mystical_range(char):
                # Check if it's actually a mystical symbol (not just emoji)
                cat = unicodedata.category(char)
                if cat in ['So', 'Sm', 'Sk']:  # Symbol categories
                    mystical_count += 1
                    detected_symbols.add(char)
        
        # Check threshold
        if total_chars > 0:
            symbol_ratio = mystical_count / total_chars
            
            # Detect if above threshold AND minimum count
            if symbol_ratio >= self.symbol_threshold and mystical_count >= self.min_symbols_for_detection:
                symbols_str = ', '.join(sorted(detected_symbols)[:10])  # Show first 10
                if len(detected_symbols) > 10:
                    symbols_str += f' (+{len(detected_symbols) - 10} more)'
                return True, f"High density of mystical symbols: {symbols_str} ({mystical_count}/{total_chars} = {symbol_ratio:.1%})"
        
        return False, ""
    
    def should_ignore_message(self, text: str) -> Tuple[bool, str]:
        """
        Determine if a message should be silently ignored.
        
        Args:
            text: The message text to analyze
            
        Returns:
            Tuple of (should_ignore, reason)
        """
        return self.detect_mystical_content(text)


# Global instance for reuse
_detector_instance = None


def get_mystical_symbol_detector() -> MysticalSymbolDetector:
    """Get or create global mystical symbol detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = MysticalSymbolDetector()
    return _detector_instance
