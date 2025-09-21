# CDL Implementation Guide

## Quick Start

### 1. Character File Format

Create character definitions in JSON format (`.json` files) following the CDL specification.

```bash
characters/
├── examples/
│   ├── elena-rodriguez.json
│   └── marcus-chen.json
└── custom/
    └── your-character.json
```

### 2. Loading Characters

```python
from src.characters.cdl.parser import load_character

# Load character from JSON file
character = load_character("characters/examples/elena-rodriguez.json")

# Access character properties
print(character.identity.name)  # "Elena Rodriguez"
print(character.identity.occupation)  # "Marine Biologist & Research Scientist"
print(character.personality.big_five.openness)  # 0.9
```

### 3. Using Characters in Conversations

Characters are automatically loaded when using the `!roleplay` command:

```
!roleplay elena    # Activate Elena Rodriguez
!roleplay marcus   # Activate Marcus Chen  
!roleplay off      # Return to default bot
```

### 4. Character Integration

The CDL system integrates with WhisperEngine's AI pipeline:

- **Prompt Generation**: Character traits influence conversation prompts
- **Memory System**: Character knowledge stored in vector memory
- **Emotional Intelligence**: Personality affects emotional responses
- **Voice Patterns**: Speech characteristics guide response style

## Converting YAML to JSON

If you have existing YAML character files:

1. Use online YAML-to-JSON converters
2. Validate the JSON structure
3. Update file references to use `.json` extension
4. Test character loading

## Character Development Tips

### Personality Balance
- Use realistic Big Five trait combinations
- Avoid extreme values (0.0 or 1.0) unless justified
- Create believable personality contradictions

### Background Depth
- Include specific formative experiences
- Connect past events to current personality
- Create realistic life progression

### Current Life Details
- Define concrete daily routines
- Include specific current projects
- Set realistic goals and challenges

## Testing Characters

1. **Load Test**: Verify character parses without errors
2. **Identity Test**: Check core identity consistency  
3. **Conversation Test**: Engage in character-appropriate dialogue
4. **Memory Test**: Verify character can reference their background

## Troubleshooting

### Common Issues

**Character won't load:**
- Check JSON syntax with validator
- Verify all required fields present
- Check file path and permissions

**Character responses seem off:**
- Review personality trait values
- Check for contradictory background elements
- Verify prompt generation is working

**Memory issues:**
- Ensure character background is stored in vector memory
- Check memory retrieval during conversations
- Validate character context injection

### Debug Commands

```python
# Test character loading
from src.characters.cdl.parser import load_character
character = load_character("path/to/character.json")

# Validate character
is_valid, errors = character.is_valid()
if not is_valid:
    print("Validation errors:", errors)

# Check character display
print(character.get_display_name())
```