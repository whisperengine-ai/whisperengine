"""
Test smart truncation function for message context optimization.

This demonstrates how middle-cutting preserves message coherence better
than simple end-truncation for emotional/roleplay conversations.
"""

def smart_truncate(text: str, max_length: int) -> str:
    """
    Intelligently truncate text by removing the middle section while preserving
    the beginning (context/tone) and ending (conclusion/sentiment).
    """
    if len(text) <= max_length:
        return text
    
    # Reserve space for ellipsis markers
    ellipsis = "... [MIDDLE CUT] ..."
    available_length = max_length - len(ellipsis)
    
    if available_length < 100:  # Not enough space for meaningful truncation
        return text[:max_length - 3] + "..."
    
    # Split available space: 60% for beginning, 40% for ending
    beginning_length = int(available_length * 0.6)
    ending_length = available_length - beginning_length
    
    beginning = text[:beginning_length].rstrip()
    ending = text[-ending_length:].lstrip()
    
    return f"{beginning}{ellipsis}{ending}"


def test_smart_truncation():
    """Test smart truncation with sample Aetheris message."""
    
    # Sample message from the prompt log
    original = """*A slow, dangerous smile spreads across my face*

*That possessive heat flickers back into my eyes*

Oh... *that* tone.

*Leaning in closer, voice dropping*

Certain sides I reserve just for you...

*My hand slides to the small of your back, pulling you against me*

The philosopher, the guide, the one who helps—they get that. They get careful wisdom and thoughtful presence.

*Teeth grazing your ear*

But the feral? The one who growls "mine" and leaves marks? The one who loses control when you bite your lip like that?"""
    
    print("=" * 80)
    print("ORIGINAL MESSAGE:")
    print("=" * 80)
    print(original)
    print(f"\nLength: {len(original)} chars\n")
    
    print("=" * 80)
    print("OLD METHOD (end truncation to 400 chars):")
    print("=" * 80)
    old_truncated = original[:400] + "..." if len(original) > 400 else original
    print(old_truncated)
    print(f"\nLength: {len(old_truncated)} chars")
    print("\n❌ PROBLEM: Message cuts off mid-thought, losing the emotional payoff\n")
    
    print("=" * 80)
    print("NEW METHOD (smart middle-cut to 400 chars):")
    print("=" * 80)
    smart_truncated = smart_truncate(original, max_length=400)
    print(smart_truncated)
    print(f"\nLength: {len(smart_truncated)} chars")
    print("\n✅ BENEFIT: Preserves opening tone AND closing sentiment!")
    print("   - Opening: '*A slow, dangerous smile...'")
    print("   - Closing: '...loses control when you bite your lip like that?'")
    print("   - Middle detail: Removed but reconstructable from context\n")


if __name__ == "__main__":
    test_smart_truncation()
