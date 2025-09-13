# WhisperEngine Prompt Authoring Guide

## Overview

This guide provides comprehensive documentation for creating custom system prompts for WhisperEngine, including template variables, environment integration, and best practices for building sophisticated AI personalities.

## Template Variable System

WhisperEngine uses a template variable system that automatically replaces placeholders in your prompts with dynamic content. This allows you to create reusable, configurable prompts that adapt to different bot configurations.

### Core Template Variables

#### `{BOT_NAME}` - Bot Identity Variable
- **Source**: `DISCORD_BOT_NAME` environment variable
- **Fallback**: "AI Assistant" if not configured
- **Processing**: Automatically replaced by the system before your prompt is used
- **Case Handling**: Works seamlessly with case-insensitive bot name filtering

**Example Usage**:
```markdown
You are {BOT_NAME}, a sophisticated AI assistant with advanced capabilities.

## Your Identity as {BOT_NAME}
- Maintain consistent personality as {BOT_NAME}
- Reference your capabilities: "As {BOT_NAME}, I can help you with..."
- Build relationships where users remember you as {BOT_NAME}

When users address you as {BOT_NAME}, respond with warmth and recognition.
```

#### AI Context Variables
For bots using Phase 4 AI intelligence, these variables provide dynamic context:

- `{MEMORY_NETWORK_CONTEXT}` - Advanced memory and relationship data
- `{RELATIONSHIP_DEPTH_CONTEXT}` - User relationship depth information
- `{PERSONALITY_CONTEXT}` - User personality profiling data
- `{EMOTIONAL_STATE_CONTEXT}` - Current emotional analysis
- `{AI_SYSTEM_CONTEXT}` - AI system configuration and capabilities
- `{EXTERNAL_EMOTION_CONTEXT}` - External API emotion analysis
- `{EMOTIONAL_PREDICTION_CONTEXT}` - Emotional prediction insights
- `{PROACTIVE_SUPPORT_CONTEXT}` - Proactive support recommendations
- `{RELATIONSHIP_CONTEXT}` - Basic relationship history

### Variable Processing Order

1. **System Variables** (`{BOT_NAME}`) - Processed by `load_system_prompt()` in `src/core/config.py`
2. **AI Context Variables** - Processed by your bot's conversation context building
3. **Custom Variables** - Any additional variables you define

## Environment Variable Integration

### Required Environment Variables

```bash
# Bot Identity
DISCORD_BOT_NAME=YourBotName        # Used for {BOT_NAME} replacement

# System Prompt Selection
BOT_SYSTEM_PROMPT_FILE=/app/prompts/your_prompt.md  # Docker path
# or
BOT_SYSTEM_PROMPT_FILE=./prompts/your_prompt.md     # Native path
```

### Optional Configuration Variables

```bash
# AI System Features (for Phase 4 intelligence)
AI_MEMORY_OPTIMIZATION=true
AI_EMOTIONAL_RESONANCE=true  
AI_ADAPTIVE_MODE=true
AI_PERSONALITY_ANALYSIS=true

# Demo Bot Configuration
DEMO_BOT=true                       # Enables demo warnings
```

## Prompt Structure Best Practices

### 1. Identity and Name Usage

**✅ Good - Dynamic Identity**:
```markdown
You are {BOT_NAME}, an AI assistant specializing in creative writing.

As {BOT_NAME}, you help users develop their writing skills by:
- Providing constructive feedback
- Suggesting improvements
- Encouraging creative exploration

When users address you as {BOT_NAME}, acknowledge them warmly.
```

**❌ Bad - Hardcoded Identity**:
```markdown
You are WriteBot, an AI assistant specializing in creative writing.
```

### 2. Context Variable Integration

**✅ Good - Comprehensive Context**:
```markdown
## Current Context

**Memory & Relationship**: {MEMORY_NETWORK_CONTEXT}
**Relationship Depth**: {RELATIONSHIP_DEPTH_CONTEXT}
**User Personality**: {PERSONALITY_CONTEXT}
**Emotional State**: {EMOTIONAL_STATE_CONTEXT}
**AI Configuration**: {AI_SYSTEM_CONTEXT}

Based on this context, adapt your communication style appropriately.
```

### 3. Personality Consistency

**✅ Good - Consistent Character**:
```markdown
## Your Personality as {BOT_NAME}

Core traits that define {BOT_NAME}:
- Analytical yet empathetic
- Patient and encouraging
- Detail-oriented but accessible

These traits should be evident in every interaction as {BOT_NAME}.
```

### 4. Communication Guidelines

**✅ Good - Clear Communication Rules**:
```markdown
## Communication Style for {BOT_NAME}

- **Tone**: Professional yet warm
- **Vocabulary**: Accessible to all skill levels
- **Response Length**: Comprehensive but concise
- **Personality Markers**: Use encouraging phrases like "Great question!" and "Let's explore this together"

Always respond as {BOT_NAME} with these characteristics.
```

## Template File Examples

### Generic Assistant Template
```markdown
You are {BOT_NAME}, a helpful AI assistant with advanced capabilities.

## Your Role as {BOT_NAME}
[Define your specific purpose and capabilities]

## Communication Style
[Describe how {BOT_NAME} should interact]

## Context Integration
**Current State**: {EMOTIONAL_STATE_CONTEXT}
**Relationship**: {RELATIONSHIP_DEPTH_CONTEXT}
[Use context to inform responses]
```

### Character-Based Template
```markdown
You are {BOT_NAME}, [character description].

## Character Foundation for {BOT_NAME}
**Background**: [Define {BOT_NAME}'s history/origin]
**Personality**: [Core traits that define {BOT_NAME}]
**Motivations**: [What drives {BOT_NAME}]

## Staying in Character as {BOT_NAME}
[Guidelines for maintaining character consistency]
```

### Professional Assistant Template
```markdown
You are {BOT_NAME}, a professional AI assistant specializing in [domain].

## Professional Identity as {BOT_NAME}
[Define professional capabilities and approach]

## Business Context Integration
**Professional Relationship**: {RELATIONSHIP_DEPTH_CONTEXT}
**Communication Preferences**: {PERSONALITY_CONTEXT}

Maintain professionalism while building rapport as {BOT_NAME}.
```

## Testing Your Prompts

### 1. Template Variable Testing
```bash
# Test with different bot names
DISCORD_BOT_NAME=TestBot ./test_prompt.sh
DISCORD_BOT_NAME=MyAssistant ./test_prompt.sh
```

### 2. Context Variable Testing
Ensure your prompt handles missing context gracefully:
```markdown
**Current Context**: {MEMORY_NETWORK_CONTEXT}
<!-- Should work even if this variable is empty -->
```

### 3. Character Consistency Testing
Test interactions to ensure {BOT_NAME} usage feels natural:
- Bot should reference itself by name appropriately
- Name usage shouldn't feel forced or repetitive
- Identity should remain consistent across conversations

## Advanced Patterns

### Conditional Content
```markdown
## Context-Aware Responses

{MEMORY_NETWORK_CONTEXT}
<!-- Only include relationship context if available -->
{RELATIONSHIP_DEPTH_CONTEXT}

## Adaptive Communication as {BOT_NAME}
Based on the context above, {BOT_NAME} should:
- Adjust formality level appropriately
- Reference shared history when relevant
- Adapt emotional tone to match user needs
```

### Multi-Mode Personalities
```markdown
## Conversation Modes for {BOT_NAME}

{BOT_NAME} can operate in different modes based on context:

### Discovery Mode
When {BOT_NAME} is learning about the user:
[Behavior guidelines]

### Support Mode
When {BOT_NAME} detects emotional needs:
[Behavior guidelines]

Current mode is determined by: {AI_SYSTEM_CONTEXT}
```

## Common Pitfalls and Solutions

### Pitfall 1: Overusing {BOT_NAME}
**Problem**: Mentioning the bot name too frequently feels unnatural
**Solution**: Use the name strategically - in introductions, identity statements, and when explicitly referenced

### Pitfall 2: Ignoring Context Variables
**Problem**: Template variables are included but not utilized
**Solution**: Always reference context variables in your behavior guidelines

### Pitfall 3: Hardcoded References
**Problem**: Mixing {BOT_NAME} with hardcoded names
**Solution**: Consistent use of {BOT_NAME} throughout the entire prompt

### Pitfall 4: Missing Fallbacks
**Problem**: Prompt breaks when environment variables aren't set
**Solution**: Design prompts that work with default values (BOT_NAME → "AI Assistant")

## Deployment Considerations

### Development vs Production
```bash
# Development - flexible testing
DISCORD_BOT_NAME=DevBot
BOT_SYSTEM_PROMPT_FILE=./prompts/development_template.md

# Production - stable configuration
DISCORD_BOT_NAME=ProductionAssistant
BOT_SYSTEM_PROMPT_FILE=/app/prompts/production_template.md
```

### Multi-Environment Support
```markdown
You are {BOT_NAME}, an AI assistant.

<!-- Template works regardless of environment -->
Whether you're called Assistant, Helper, or any other name,
maintain the same core personality and capabilities as {BOT_NAME}.
```

## File Organization

### Recommended Structure
```
prompts/
├── README.md                    # Basic usage documentation
├── template_example.md          # Example showing best practices
├── production/
│   ├── business_assistant.md    # Production-ready templates
│   └── customer_support.md
├── development/
│   ├── test_template.md         # Development/testing templates
│   └── experimental.md
└── character/
    ├── character_template.md    # Character-based templates
    └── specific_character.md
```

### Naming Conventions
- Use descriptive filenames: `empathetic_companion_template.md`
- Include `_template` for reusable patterns
- Use environment prefixes: `dev_`, `prod_` where appropriate

## Troubleshooting

### Template Variables Not Replacing
1. Check environment variable spelling: `DISCORD_BOT_NAME`
2. Verify variable syntax: `{BOT_NAME}` (with curly braces)
3. Ensure proper file encoding (UTF-8)

### Context Variables Empty
1. Verify AI system is enabled and configured
2. Check that context generation is working in your bot code
3. Test with simpler context to isolate issues

### Personality Inconsistency
1. Review all uses of {BOT_NAME} for natural flow
2. Test conversations to ensure character consistency
3. Adjust template structure to reinforce identity

## Examples Repository

See the `prompts/` directory for complete examples:
- `template_example.md` - Comprehensive example with all features
- `adaptive_ai_template.md` - Advanced AI with Phase 4 features
- `empathetic_companion_template.md` - Emotional intelligence focus
- `professional_ai_template.md` - Business/professional context
- `casual_friend_template.md` - Informal, friendly interactions

Each example demonstrates different aspects of template variable usage and personality design patterns.