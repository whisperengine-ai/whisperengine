#!/usr/bin/env python3
"""
Test the fact extraction filtering fixes
"""

import re

def test_filtering():
    """Test the message filtering logic"""
    
    # Test the regex patterns
    non_factual_patterns = [
        r'^(testing|test|hmm+|maybe\?*|ok|okay|hello|hi|thanks|thank you|what\?*)\.{0,3}$',
        r'^[!?.,\s]*$',  # Only punctuation and whitespace
        r'^[a-z]{1,5}\.{0,3}$',  # Very short words with optional dots
    ]
    
    test_cases = [
        # Messages that should be filtered out
        ('testing...', True),
        ('hmm', True), 
        ('maybe?', True),
        ('ok', True),
        ('hello', True),
        ('hi', True),
        ('test', True),
        ('thanks', True),
        ('what?', True),
        ('???', True),
        ('...', True),
        
        # Messages that should NOT be filtered out
        ('I like pizza', False),
        ('I play guitar every day', False),
        ('My name is John', False),
        ('I live in California and work as a teacher', False),
        ('testing my guitar skills', False),  # Contains "testing" but has more content
    ]
    
    print("Testing message filtering logic:")
    print("=" * 50)
    
    for message, should_be_filtered in test_cases:
        cleaned = message.strip()
        is_short = len(cleaned) < 10
        matches_pattern = any(re.match(pattern, cleaned, re.IGNORECASE) for pattern in non_factual_patterns)
        would_be_filtered = is_short or matches_pattern
        
        status = "✓" if would_be_filtered == should_be_filtered else "✗"
        print(f'{status} "{message}" -> Filter: {would_be_filtered} (expected: {should_be_filtered})')
        
        if would_be_filtered != should_be_filtered:
            print(f'   Length: {len(cleaned)} < 10 = {is_short}')
            print(f'   Pattern match: {matches_pattern}')

def test_fact_message_validation():
    """Test the fact-to-message validation logic"""
    
    def fact_supported_by_message(fact_text: str, message: str) -> bool:
        """Check if the extracted fact is actually supported by content in the message"""
        if not fact_text or not message:
            return False
        
        fact_lower = fact_text.lower()
        message_lower = message.lower()
        
        # Remove common prefixes from facts for matching
        fact_content = fact_lower
        for prefix in ["user ", "the user ", "they ", "person "]:
            if fact_content.startswith(prefix):
                fact_content = fact_content[len(prefix):]
        
        # Check if key words from the fact appear in the message
        fact_words = fact_content.split()
        message_words = message_lower.split()
        
        # For very short facts (1-2 words), require at least one significant word match
        if len(fact_words) <= 2:
            return any(word in message_lower for word in fact_words if len(word) > 2)
        
        # For longer facts, require at least 1 significant word to match (reduced from 2)
        significant_words = [word for word in fact_words if len(word) > 2 and word not in ['with', 'from', 'that', 'this', 'they', 'have', 'the', 'and', 'for']]
        
        if not significant_words:
            return False
            
        matching_words = [word for word in significant_words if word in message_lower]
        
        # More lenient: require at least 1 significant word match, or 50% for longer facts
        required_matches = max(1, len(significant_words) // 2)
        return len(matching_words) >= required_matches
    
    test_cases = [
        # Cases where facts should be rejected (hallucinated facts)
        ('testing...', 'lives in California', False),
        ('hmm maybe?', 'plays guitar', False),
        ('ok', 'works as teacher', False),
        
        # Cases where facts should be accepted (supported by message)
        ('I play guitar every weekend', 'plays guitar', True),
        ('I live in California', 'lives in California', True),
        ('I work as a teacher', 'works as teacher', True),
        ('My favorite hobby is playing guitar', 'plays guitar', True),
        ('I currently live in Los Angeles, California', 'lives in California', True),
    ]
    
    print("\n\nTesting fact-message validation:")
    print("=" * 50)
    
    for message, fact, should_be_supported in test_cases:
        is_supported = fact_supported_by_message(fact, message)
        status = "✓" if is_supported == should_be_supported else "✗"
        print(f'{status} "{message}" + "{fact}" -> Supported: {is_supported} (expected: {should_be_supported})')

if __name__ == "__main__":
    test_filtering()
    test_fact_message_validation()
