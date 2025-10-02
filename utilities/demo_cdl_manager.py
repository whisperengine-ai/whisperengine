#!/usr/bin/env python3
"""
CDL Manager Demo - Test the singleton CDL manager functionality

This script demonstrates the CDL manager's capabilities:
- Lazy loading from CHARACTER_FILE environment variable
- Generic field access with dot notation
- Conversation flow guidelines extraction
- Character metadata access
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.characters.cdl.manager import (
    get_cdl_manager, 
    get_cdl_field, 
    get_character_name,
    get_conversation_flow_guidelines,
    has_cdl_field
)


def demo_cdl_manager():
    """Demonstrate CDL manager functionality"""
    print("🎭 CDL Manager Demo")
    print("=" * 50)
    
    # Get the CDL manager instance
    cdl = get_cdl_manager()
    
    # Show data summary
    print("\n📊 Data Summary:")
    summary = cdl.get_data_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Test character metadata access
    print(f"\n👤 Character Info:")
    print(f"  Name: {get_character_name()}")
    print(f"  Occupation: {cdl.get_character_occupation()}")
    
    # Test conversation flow guidelines access
    print(f"\n💬 Conversation Flow Guidelines:")
    if has_cdl_field("character.communication.conversation_flow_guidelines"):
        flow_guidelines = get_conversation_flow_guidelines()
        print(f"  Found guidelines: {bool(flow_guidelines)}")
        
        # Test specific field access
        max_length = get_cdl_field("character.communication.conversation_flow_guidelines.platform_awareness.discord.max_response_length")
        print(f"  Discord max length: {max_length}")
        
        avoid_patterns = get_cdl_field("character.communication.conversation_flow_guidelines.platform_awareness.discord.avoid")
        print(f"  Avoid patterns: {avoid_patterns}")
        
        prefer_patterns = get_cdl_field("character.communication.conversation_flow_guidelines.platform_awareness.discord.prefer")
        print(f"  Prefer patterns: {prefer_patterns}")
    else:
        print("  No conversation flow guidelines found")
        # Check if it exists in the old location
        if has_cdl_field("character.conversation_flow_guidelines"):
            print("  Found in alternative location: character.conversation_flow_guidelines")
    
    # Test communication style access
    print(f"\n🎤 Communication Style:")
    if has_cdl_field("character.identity.communication_style"):
        comm_style = cdl.get_communication_style()
        print(f"  Found communication style: {bool(comm_style)}")
        
        tone = get_cdl_field("character.identity.communication_style.tone")
        print(f"  Tone: {tone}")
        
        formality = get_cdl_field("character.identity.communication_style.formality")
        print(f"  Formality: {formality}")
    else:
        print("  No communication style found")
    
    # Test AI identity handling
    print(f"\n🤖 AI Identity Handling:")
    ai_handling = cdl.get_ai_identity_handling()
    if ai_handling:
        philosophy = get_cdl_field("character.identity.communication_style.ai_identity_handling.philosophy")
        print(f"  Philosophy: {philosophy}")
        
        responses = get_cdl_field("character.identity.communication_style.ai_identity_handling.responses", [])
        print(f"  Response count: {len(responses) if responses else 0}")
    else:
        print("  No AI identity handling found")
    
    # Test field existence checking
    print(f"\n🔍 Field Existence Tests:")
    test_fields = [
        "character.metadata.name",
        "character.conversation_flow_guidelines",
        "character.personality.big_five",
        "character.nonexistent.field",
        "character.identity.communication_style.ai_identity_handling"
    ]
    
    for field in test_fields:
        exists = has_cdl_field(field)
        value = get_cdl_field(field, "NOT_FOUND")
        print(f"  {field}: {'✅' if exists else '❌'} ({type(value).__name__})")
    
    print(f"\n✅ CDL Manager Demo Complete")
    print(f"💡 The CDL manager provides thread-safe, lazy-loaded access to character data")
    print(f"💡 Use get_cdl_field('path.to.field') for any CDL field access")
    print(f"💡 No more file re-reading - all data cached in memory after first load")


if __name__ == "__main__":
    # Check if CHARACTER_FILE is set
    character_file = os.getenv('CHARACTER_FILE')
    if not character_file:
        print("❌ CHARACTER_FILE environment variable not set")
        print("💡 Set it to test the CDL manager:")
        print("   export CHARACTER_FILE=characters/examples/elena.json")
        print("   python utilities/demo_cdl_manager.py")
        sys.exit(1)
    
    if not Path(character_file).exists():
        print(f"❌ Character file not found: {character_file}")
        sys.exit(1)
    
    demo_cdl_manager()