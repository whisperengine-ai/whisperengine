# Multi-Entity Template Variables Guide

This guide covers the template variables available for multi-entity character-aware prompts in WhisperEngine.

## Core Character Variables

### `{CHARACTER_NAME}`
The character's display name.
```
Example: "Sage the Philosopher"
```

### `{CHARACTER_OCCUPATION}`
The character's occupation or role.
```
Example: "philosopher", "digital artist", "inventor"
```

### `{CHARACTER_TRAITS}`
Comma-separated list of personality traits.
```
Example: "wise, thoughtful, patient, introspective"
```

### `{CHARACTER_BACKGROUND}`
The character's background story or summary.
```
Example: "A wise philosopher who enjoys deep conversations about life and meaning"
```

### `{CHARACTER_COMMUNICATION_STYLE}`
How the character communicates.
```
Example: "philosophical", "enthusiastic", "empathetic"
```

### `{CHARACTER_INTERESTS}`
The character's preferred topics or interests.
```
Example: "philosophy, ethics, wisdom, life_lessons"
```

## Relationship Variables

### `{RELATIONSHIP_STAGE}`
Current relationship stage between character and user.
```
Possible values:
- "unestablished" - No previous interaction
- "initial_contact" - First few interactions
- "getting_acquainted" - Building familiarity
- "developing_friendship" - Growing connection
- "established_relationship" - Solid bond
- "deep_bond" - Very close relationship
```

### `{TRUST_LEVEL}`
Trust level between character and user (0.0-1.0).
```
Example: "0.7" (high trust)
Usage: "Trust: {TRUST_LEVEL}/1.0"
```

### `{FAMILIARITY_LEVEL}`
Familiarity level between character and user (0.0-1.0).
```
Example: "0.5" (moderately familiar)
Usage: "Familiarity: {FAMILIARITY_LEVEL}/1.0"
```

### `{INTERACTION_COUNT}`
Number of previous interactions between character and user.
```
Example: "12"
Usage: "Previous interactions: {INTERACTION_COUNT}"
```

### `{RELATIONSHIP_STRENGTH}`
Overall relationship strength (calculated from trust + familiarity).
```
Example: "0.6"
Usage: "Relationship strength: {RELATIONSHIP_STRENGTH}/1.0"
```

## Network Variables

### `{KNOWN_CHARACTERS}`
Other characters this character is aware of.
```
Example: "Echo the Storyteller (knows_about), Luna the Artist (inspired_by)"
```

### `{CONNECTED_USERS}`
Users connected to this character.
```
Example: "Created by Alice (Creative Writer), Favorite of Bob (Engineer)"
```

### `{CHARACTER_CREATOR}`
The user who created this character.
```
Example: "Alice (Creative Writer)"
```

## User Variables

### `{USER_NAME}`
The user's display name or username.
```
Example: "Alice" or "Bob the Engineer"
```

### `{USER_DISCORD_ID}`
The user's Discord ID (for system use).
```
Example: "user_12345"
```

## AI System Variables

### `{AI_GUIDANCE}`
AI system recommendations for the current interaction.
```
Example: "Focus on building trust through consistent, honest interactions"
```

### `{COMPATIBILITY_SCORE}`
Compatibility score between character and user (0.0-1.0).
```
Example: "0.8" (high compatibility)
```

### `{CONVERSATION_STARTERS}`
AI-suggested conversation starters.
```
Example: "I'd love to hear your thoughts about philosophy"
```

### `{RELATIONSHIP_POTENTIAL}`
AI assessment of relationship potential.
```
Example: "high - strong natural compatibility"
```

## Context Variables

### `{CONVERSATION_TOPIC}`
Current or suggested conversation topic.
```
Example: "creative writing techniques"
```

### `{CONVERSATION_MOOD}`
Current conversation mood or tone.
```
Example: "thoughtful", "celebratory", "supportive"
```

### `{SPECIAL_INSTRUCTIONS}`
Special context or instructions for this interaction.
```
Example: "This is an AI-facilitated introduction"
```

## Contextual Usage Examples

### Character Introduction
```markdown
You are {CHARACTER_NAME}, a {CHARACTER_OCCUPATION}.
Personality: {CHARACTER_TRAITS}
This is your first interaction with {USER_NAME}.
Compatibility: {COMPATIBILITY_SCORE}/1.0
Suggested starter: {CONVERSATION_STARTERS}
```

### Established Relationship
```markdown
You are {CHARACTER_NAME} speaking with {USER_NAME}.
Relationship stage: {RELATIONSHIP_STAGE}
Trust: {TRUST_LEVEL}/1.0, Familiarity: {FAMILIARITY_LEVEL}/1.0
Previous interactions: {INTERACTION_COUNT}
AI guidance: {AI_GUIDANCE}
```

### Cross-Character Awareness
```markdown
You are {CHARACTER_NAME}.
You know about: {KNOWN_CHARACTERS}
Current conversation with: {USER_NAME}
Creator: {CHARACTER_CREATOR}
```

## Advanced Template Usage

### Conditional Content
Use template variables in conditional statements:
```markdown
{% if TRUST_LEVEL > 0.7 %}
You feel comfortable sharing deeper insights with {USER_NAME}.
{% elif TRUST_LEVEL > 0.3 %}
You're building trust with {USER_NAME} and can be moderately open.
{% else %}
You're still getting to know {USER_NAME} and should be cautious but friendly.
{% endif %}
```

### Dynamic Personality Adaptation
```markdown
{% if RELATIONSHIP_STAGE == "initial_contact" %}
Be welcoming but respectful, building trust gradually.
{% elif RELATIONSHIP_STAGE == "deep_bond" %}
Communicate with the intimacy of a close friend.
{% endif %}
```

### Relationship-Aware Responses
```markdown
{% if INTERACTION_COUNT > 10 %}
Reference shared experiences and inside jokes naturally.
{% else %}
Focus on learning about {USER_NAME} and sharing about yourself.
{% endif %}
```

## Integration with LLM Context

These variables are automatically injected into prompts by the `MultiEntityContextInjector` class:

```python
enhanced_prompt = await context_injector.inject_character_context(
    prompt=base_prompt,
    character_id=character_id,
    user_id=user_id,
    conversation_context={
        "conversation_topic": "philosophy",
        "conversation_mood": "thoughtful"
    }
)
```

## Template Variable Precedence

Variables are resolved in this order:
1. Real-time relationship data (trust, familiarity, interaction count)
2. Character profile data (name, traits, background)
3. Network relationship data (known characters, creators)
4. AI system recommendations (guidance, compatibility)
5. Conversation context (topic, mood, special instructions)
6. Default values (if data unavailable)

This ensures that prompts always have meaningful content even when some relationship data is incomplete.