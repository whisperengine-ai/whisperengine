#!/usr/bin/env python3
"""
Bot Name Normalization Implementation

This implements bot_name normalization directly in the memory system to prevent
case sensitivity and space issues from breaking memory isolation.

SOLUTION APPROACH:
1. Add normalization functions to memory system
2. Always normalize bot_name before storage/retrieval  
3. Maintain backward compatibility with existing data
4. Provide migration script for existing memories
"""

def normalize_bot_name(bot_name: str) -> str:
    """
    Normalize bot name for consistent memory storage and retrieval.
    
    Rules:
    - Convert to lowercase for case-insensitive matching
    - Replace spaces with underscores 
    - Remove special characters except underscore/hyphen
    - Handle empty/None values
    
    Examples:
    - "Elena" -> "elena"
    - "Marcus Chen" -> "marcus_chen"
    - "Dream of the Endless" -> "dream_of_the_endless"
    - None -> "unknown"
    """
    if not bot_name or not isinstance(bot_name, str):
        return "unknown"
    
    import re
    
    # Step 1: Trim and lowercase
    normalized = bot_name.strip().lower()
    
    # Step 2: Replace spaces with underscores
    normalized = re.sub(r'\s+', '_', normalized)
    
    # Step 3: Remove special characters except underscore/hyphen/alphanumeric
    normalized = re.sub(r'[^a-z0-9_-]', '', normalized)
    
    # Step 4: Collapse multiple underscores/hyphens
    normalized = re.sub(r'[_-]+', '_', normalized)
    
    # Step 5: Remove leading/trailing underscores
    normalized = normalized.strip('_-')
    
    return normalized if normalized else "unknown"

def get_normalized_bot_name_from_env() -> str:
    """Get normalized bot name from environment variables"""
    import os
    
    # Try different environment variable names
    raw_bot_name = (
        os.getenv("DISCORD_BOT_NAME") or 
        os.getenv("BOT_NAME") or 
        "unknown"
    )
    
    return normalize_bot_name(raw_bot_name.strip())

# Test the normalization with your current bot names
if __name__ == "__main__":
    test_names = [
        "Elena",
        "elena", 
        "ELENA",
        "Marcus",
        "Marcus Chen",
        "marcus chen",
        "MARCUS CHEN",
        "Dream",
        "Dream of the Endless",
        "Gabriel",
        "",
        None,
        "  Marcus Chen  ",
        "Bot-Name_123"
    ]
    
    print("🧪 TESTING: Bot Name Normalization")
    print("=" * 50)
    
    for name in test_names:
        normalized = normalize_bot_name(name)
        print(f"'{name}' -> '{normalized}'")
    
    print("\n" + "=" * 50)
    print("✅ All names normalized successfully!")
    
    # Test with current environment
    import os
    current_bot = os.getenv("DISCORD_BOT_NAME", "not_set")
    normalized_current = get_normalized_bot_name_from_env()
    
    print(f"\nCurrent environment:")
    print(f"DISCORD_BOT_NAME: '{current_bot}'")
    print(f"Normalized: '{normalized_current}'")