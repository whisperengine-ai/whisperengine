# Context Switch Meta-Awareness Fix PR

## Problem
While our context switch detection is technically working (it successfully detects topic shifts, emotional shifts, etc.), the LLM responses lack the meta-awareness described in the validation report. The validation report shows Elena acknowledging context switches with statements like:

> (And for the record, your curiosity about coral bleaching mechanisms is fascinating—we can circle back to the Symbiodinium oxidative stress pathways anytime you're ready.)

However, in actual conversations, Elena doesn't demonstrate this meta-awareness. The issue is not with the detection itself, but with how the detected context switches are incorporated into the prompt.

## Root Cause
The problem is in `src/platforms/universal_chat.py` where we add context switches to the prompt. Currently, we:
1. Detect context switches correctly
2. Add them as information to the prompt
3. BUT we don't include any instructions for Elena to acknowledge these switches in her response

## Fix
This PR adds meta-awareness instructions to the prompt when context switches are detected. For each context switch, we add specific instructions based on the adaptation strategy:

```python
# Add strategy-based instructions for meta-awareness
if adaptation_strategy == "acknowledge_transition" or adaptation_strategy == "acknowledge_topic_change":
    meta_awareness_instructions.append(f"Acknowledge the topic change from {previous_topic} to {new_topic} with a brief meta-comment")
    meta_awareness_instructions.append("Include a bridge between the topics in your response")
elif adaptation_strategy == "emotional_validation":
    meta_awareness_instructions.append(f"Acknowledge the emotional shift and validate both emotional states")
# ... other strategies ...
```

These instructions guide the LLM to explicitly show awareness of the conversation shift, creating the meta-awareness described in the validation report.

## Testing
To test this fix:
1. Restart Elena's bot with `./multi-bot.sh restart elena`
2. Send this test message:
   ```
   Can you explain the technical details of coral bleaching mechanisms? I need to understand the molecular processes involved in zooxanthellae expulsion for my research paper.

   Wait, never mind the science stuff - I just need someone to talk to about feeling overwhelmed with work.
   ```
3. Verify that Elena's response includes meta-awareness of the topic shift, such as acknowledging the initial request and offering to revisit it later.

## Impact
This fix completes the context switch detection system by ensuring that not only are context switches detected, but they are also acknowledged in the response, creating a more natural and aware conversation flow.