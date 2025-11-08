"""
Test episodic recall context builder.
"""

from src.core.message_processor import MessageProcessor


def test_recall_intent_detection():
    """Test that recall keywords trigger episodic context."""
    processor = MessageProcessor(None)  # Mock bot_core for now
    
    # Test messages that SHOULD trigger recall
    recall_messages = [
        "Can you recall when Luna was sick?",
        "Remember when we talked about my cats?",
        "What happened with Luna earlier?",
        "You told me something about Minerva",
        "When did I mention my pets?"
    ]
    
    # Test messages that should NOT trigger
    no_recall_messages = [
        "How are my cats doing?",
        "Tell me about cats",
        "I have two cats"
    ]
    
    # Create mock memories with emotional_intensity
    mock_memories = [
        {
            'content': 'Luna has been sick with an infection',
            'timestamp': '2024-10-18T10:30:00Z',
            'payload': {'emotional_intensity': 0.7},
            'metadata': {'bot_response': 'I hope Luna feels better soon!'},
            'score': 0.85
        },
        {
            'content': 'Luna is recovering and eating again',
            'timestamp': '2024-10-25T14:20:00Z',
            'payload': {'emotional_intensity': 0.6},
            'metadata': {'bot_response': 'That\'s wonderful news about Luna!'},
            'score': 0.82
        }
    ]
    
    # Test recall intent detection
    print("Testing RECALL intent messages:")
    for msg in recall_messages:
        context = processor._build_episodic_recall_context(msg, mock_memories)
        if context:
            print(f"✅ '{msg}' → Triggered episodic recall")
            print(f"   Context length: {len(context)} chars")
        else:
            print(f"❌ '{msg}' → Did NOT trigger (should have)")
    
    print("\nTesting NO RECALL intent messages:")
    for msg in no_recall_messages:
        context = processor._build_episodic_recall_context(msg, mock_memories)
        if context:
            print(f"❌ '{msg}' → Triggered (should NOT have)")
        else:
            print(f"✅ '{msg}' → Did NOT trigger (correct)")
    
    # Test with actual recall message to see formatted output
    print("\n" + "="*60)
    print("SAMPLE EPISODIC RECALL CONTEXT:")
    print("="*60)
    context = processor._build_episodic_recall_context(
        "Can you recall when Luna was sick?",
        mock_memories
    )
    if context:
        print(context)
    else:
        print("(No context generated)")


if __name__ == "__main__":
    test_recall_intent_detection()
