"""
Meta-Awareness Fix Patch - Adds explicit instructions for context switch acknowledgment

This patch file contains the code that should be added to src/platforms/universal_chat.py
to include meta-awareness instructions when context switches are detected.

The original context switch detection system is working correctly, but it doesn't instruct
the LLM to acknowledge the switches in its response, which is why Elena doesn't show the
meta-awareness described in the validation report.
"""

def patched_code_for_universal_chat():
    """
    This function returns the patched code that should replace the existing code
    in src/platforms/universal_chat.py around line 1257.
    """
    # This is the patched code to add meta-awareness instructions
    patched_code = """
    # ✅ RE-INTEGRATED: Add Phase3 intelligence context to conversation (simplified)
    phase3_context_parts = []
    if phase3_context_switches:
        phase3_context_parts.append(f"**Context Switches Detected:** {len(phase3_context_switches)} transitions")
        
        # Add meta-awareness instructions
        meta_awareness_instructions = []
        
        for switch in phase3_context_switches[:2]:  # Show top 2 switches
            switch_type = getattr(switch, 'switch_type', 'unknown')
            switch_type_value = switch_type.value if hasattr(switch_type, 'value') else str(switch_type)
            strength = getattr(switch, 'strength', 'unknown')
            strength_value = strength.value if hasattr(strength, 'value') else str(strength)
            description = getattr(switch, 'description', 'no description')[:80]
            adaptation_strategy = getattr(switch, 'adaptation_strategy', 'acknowledge_transition')
            
            phase3_context_parts.append(f"- {switch_type_value} ({strength_value}): {description}")
            
            # Extract previous and new topics/contexts for instructions
            previous_context = getattr(switch, 'previous_context', {})
            new_context = getattr(switch, 'new_context', {})
            prev_topic = previous_context.get('primary_topic', 'previous topic') if isinstance(previous_context, dict) else 'previous topic'
            new_topic = new_context.get('primary_topic', 'new topic') if isinstance(new_context, dict) else 'new topic'
            
            # Add strategy-based instructions for meta-awareness
            if adaptation_strategy == "acknowledge_transition" or adaptation_strategy == "acknowledge_topic_change":
                meta_awareness_instructions.append(f"Acknowledge the topic change from {prev_topic} to {new_topic} with a brief meta-comment")
                meta_awareness_instructions.append("Include a bridge between the topics in your response")
            elif adaptation_strategy == "emotional_validation":
                meta_awareness_instructions.append(f"Acknowledge the emotional shift and validate both emotional states")
            elif adaptation_strategy == "mode_adjustment":
                meta_awareness_instructions.append(f"Acknowledge the conversation mode change and create a bridge between modes")
            elif adaptation_strategy == "urgency_adaptation":
                meta_awareness_instructions.append(f"Acknowledge the urgency change and prioritize the urgent matter")
            elif adaptation_strategy == "intent_realignment":
                meta_awareness_instructions.append(f"Acknowledge the change in conversational intent and adapt your role accordingly")
        
        # Add meta-awareness instructions to context
        if meta_awareness_instructions:
            phase3_context_parts.append("**Meta-Awareness Instructions:**")
            for instruction in meta_awareness_instructions:
                phase3_context_parts.append(f"- {instruction}")
            phase3_context_parts.append("- Show your awareness of conversation dynamics in a natural way")
    """
    
    return patched_code

# Display the fix for implementation
print("META-AWARENESS FIX FOR UNIVERSAL CHAT")
print("-" * 80)
print(patched_code_for_universal_chat())
print("-" * 80)
print("To apply this fix:")
print("1. Edit src/platforms/universal_chat.py to replace the existing code around line 1257")
print("2. Restart Elena's bot with './multi-bot.sh restart elena'")
print("3. Test with a conversation that includes a clear context switch")