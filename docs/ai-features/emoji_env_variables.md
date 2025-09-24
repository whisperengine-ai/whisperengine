# WhisperEngine Emoji System Environment Variables

## Core Emoji System Controls

### `EMOJI_ENABLED=true`
**What it does**: Master switch for the entire emoji intelligence system
- `true`: Enables emoji reactions and emoji-enhanced responses  
- `false`: Disables all emoji functionality
- **Default**: `true` (emojis are enabled by default)

### `EMOJI_BASE_THRESHOLD=0.4` 
**What it does**: Confidence threshold for adding emojis to responses for established users
- **Range**: 0.0 to 1.0 (0% to 100% confidence)
- **Higher values** = More selective emoji usage (need higher confidence)
- **Lower values** = More frequent emoji usage (lower confidence needed)
- **Default**: 0.4 (40% confidence required)
- **Example**: If system is 45% confident emojis fit, they'll be added since 0.45 > 0.4

### `EMOJI_NEW_USER_THRESHOLD=0.3`
**What it does**: Special lower threshold for new users to help establish conversation patterns
- **Range**: 0.0 to 1.0 (0% to 100% confidence) 
- **Usually lower** than base threshold to encourage emoji learning
- **Default**: 0.3 (30% confidence required for new users)
- **Purpose**: System uses more emojis initially to learn user preferences

### `VISUAL_REACTION_ENABLED=true`
**What it does**: Enables bots to add emoji reactions to user messages  
- `true`: Bot can react with 👍, ❤️, etc. to user messages
- `false`: Bot only sends text responses, no reactions
- **Default**: `true`
- **Note**: This is separate from emoji-enhanced text responses

## How They Work Together

```bash
# Conservative setup (minimal emojis)
EMOJI_ENABLED=true
EMOJI_BASE_THRESHOLD=0.7      # Need 70% confidence 
EMOJI_NEW_USER_THRESHOLD=0.6  # Even new users need 60% confidence

# Expressive setup (lots of emojis) 
EMOJI_ENABLED=true
EMOJI_BASE_THRESHOLD=0.2      # Only 20% confidence needed
EMOJI_NEW_USER_THRESHOLD=0.1  # New users get emojis at 10% confidence

# Text-only setup
EMOJI_ENABLED=false           # No emojis at all
VISUAL_REACTION_ENABLED=false # No reactions either
```

## Character-Specific Behavior

The CDL `digital_communication` section **overrides** these thresholds:
- Elena (high frequency) might ignore thresholds and emoji frequently regardless
- Marcus (moderate frequency) respects thresholds more closely  
- Dream (minimal symbolic) rarely emojis even with low thresholds

## Debugging Tips

- **Too many emojis**: Increase `EMOJI_BASE_THRESHOLD` to 0.6-0.8
- **Too few emojis**: Decrease `EMOJI_BASE_THRESHOLD` to 0.2-0.3  
- **New user spam**: Increase `EMOJI_NEW_USER_THRESHOLD` closer to base threshold
- **No reactions**: Check `VISUAL_REACTION_ENABLED=true`
- **No emojis at all**: Check `EMOJI_ENABLED=true`