# Emotion States and Relationship Management System

## Overview

This system implements dynamic emotional awareness and relationship progression for your Discord bot, following the design specification you provided. The bot now:

1. **Detects emotions** from user messages
2. **Tracks relationship levels** (Stranger → Acquaintance → Friend → Close Friend)
3. **Adapts responses** based on emotional state and relationship
4. **Handles escalation** of negative emotions
5. **Maintains context** across conversations

## Key Features

### Emotional States
- **Neutral** (default)
- **Happy/Excited** 
- **Frustrated/Angry**
- **Sad/Disappointed**
- **Curious/Inquisitive**
- **Worried/Anxious**
- **Grateful**

### Relationship Levels
- **Stranger** (first-time user)
- **Acquaintance** (returning user, 3+ interactions)
- **Friend** (personal info shared, 10+ interactions)
- **Close Friend** (deep trust, 25+ interactions)

### Escalation Management
- Tracks repeated negative emotions
- Provides warnings to the bot at 3+ negative episodes
- Suggests offering additional help or escalation to human

## Files Added/Modified

### New Files
1. **`emotion_manager.py`** - Core emotion and relationship management
2. **`test_emotion_system.py`** - Comprehensive test suite
3. **`system_prompt_emotion_aware.txt`** - Enhanced system prompt with emotion guidance

### Modified Files
1. **`memory_manager.py`** - Integrated emotion processing
2. **`basic_discord_bot.py`** - Added emotion context to system prompts
3. **`requirements.txt`** - Added textblob dependency

## How It Works

### 1. Emotion Detection
The system analyzes user messages using:
- **Keyword matching** for emotional words
- **Pattern recognition** for emotional expressions
- **Intensity calculation** based on context and intensifiers
- **Confidence scoring** for detected emotions

Example:
```python
# Input: "I'm so excited about this project!"
# Output: EmotionalState.HAPPY, confidence: 0.90, intensity: 1.0
```

### 2. Relationship Progression
Relationships progress based on:
- **Interaction count** 
- **Personal information sharing** (name, work, hobbies, etc.)
- **Trust indicators** ("I trust you", "can I tell you something private")
- **Time spent interacting**

### 3. Response Adaptation
The bot receives context like:
```
User: Friend (Alice) | Current Emotion: Happy | Interactions: 15 | 
Be warm and personal. Use their name (Alice) when appropriate. | 
Known info: name: alice, work: google | 
Respond with enthusiasm and share in their joy
```

### 4. Memory Integration
- Emotions are stored with each conversation
- Relationship levels are tracked over time
- Context includes both factual and emotional information

## Usage Examples

### Testing the System
```bash
# Run the comprehensive test suite
python test_emotion_system.py
```

### Enabling in Your Bot
The emotion system is automatically enabled when you initialize the memory manager:

```python
# In basic_discord_bot.py (already implemented)
memory_manager = UserMemoryManager(
    persist_directory="./chromadb_data",
    enable_emotions=True  # This enables the emotion system
)
```

### Getting Emotion Context
```python
# Get emotion context for a user
emotion_context = memory_manager.get_emotion_context(user_id)
# Returns: "User: Friend (Alice) | Current Emotion: Happy | ..."

# Get full emotion profile
profile = memory_manager.get_user_emotion_profile(user_id)
print(f"Relationship: {profile.relationship_level.value}")
print(f"Emotion: {profile.current_emotion.value}")
```

### Monitoring Escalation
```python
# Check if user needs escalation (handled automatically)
if profile.escalation_count >= 3:
    # System will add warning to context:
    # "WARNING: User has shown repeated negative emotions. 
    #  Be extra empathetic and consider offering additional help."
```

## Configuration Options

### Debug Mode
When running the bot with the `--debug` flag, emotional state and relationship information will be appended to all responses:

```bash
python basic_discord_bot.py --debug
```

In debug mode, responses will include information like:
```
`[DEBUG] Emotion: Happy | Relationship: Friend | Interactions: 15 | Name: Alice`
```

This helps with:
- **Monitoring emotion detection accuracy**
- **Tracking relationship progression**
- **Identifying users who need escalation**
- **Debugging the emotion system**

The debug information includes:
- Current detected emotion
- Relationship level
- Number of interactions
- User's name (if known)
- Escalation warnings (⚠️ when 3+ negative emotions detected)

### Emotion Manager Settings
```python
emotion_manager = EmotionManager(
    use_database=True,  # Use SQLite database (recommended)
    persist_file="./user_profiles.json"  # JSON fallback file
)
```

### Memory Manager Settings
```python
memory_manager = UserMemoryManager(
    persist_directory="./chromadb_data",
    enable_auto_facts=True,      # Extract facts automatically
    enable_emotions=True         # Enable emotion/relationship tracking
)
```

### Relationship Progression Rules
You can modify the progression rules in `emotion_manager.py`:

```python
self.relationship_rules = {
    RelationshipLevel.STRANGER: {
        "interaction_threshold": 0,
        "requirements": [],
        "progression_to": RelationshipLevel.ACQUAINTANCE
    },
    # ... modify thresholds and requirements as needed
}
```

## System Prompt Integration

The emotion system enhances your system prompt with contextual information. Your bot (Dream) will receive additional context like:

```
Emotional Context: User: Friend (Alice) | Current Emotion: Worried | 
Interactions: 12 | Be warm and personal. Use their name (Alice) when appropriate. | 
Known info: name: alice, work: google | Be reassuring, practical, and offer concrete help
```

This allows Dream to:
- **Adjust formality** based on relationship level
- **Respond appropriately** to emotional states
- **Use personal information** when appropriate
- **Show progression** in the relationship over time

## Monitoring and Maintenance

### View Statistics
```python
stats = memory_manager.get_collection_stats()
print(f"Emotion profiles: {stats['emotion_profiles_count']}")
print(f"Total memories: {stats['total_memories']}")
```

### Clean Up Old Data
```python
# Clean up emotion data older than 30 days
memory_manager.cleanup_emotion_data(days_to_keep=30)

# Save emotion profiles manually
memory_manager.save_emotion_profiles()
```

### Debug Emotion Detection
The test file includes comprehensive examples showing how emotions are detected and relationships progress.

## Best Practices

### 1. Regular Monitoring
- Check the bot's responses to ensure appropriate emotional awareness
- Monitor escalation warnings for users who may need additional help
- Review relationship progressions to ensure they feel natural

### 2. Privacy Considerations
- Emotion profiles are stored locally in JSON files
- Personal information is extracted but stored securely
- Users can have their data deleted through Discord commands

### 3. Customization
- Adjust emotion detection patterns for your use case
- Modify relationship progression thresholds
- Customize response guidance for different emotional states

### 4. Testing
- Use the test suite regularly to ensure the system works correctly
- Test with real users to refine emotion detection accuracy
- Monitor for false positives/negatives in emotion detection

## Troubleshooting

### Common Issues

1. **Emotion not detected correctly**
   - Check the emotion patterns in `emotion_manager.py`
   - Add more keywords or patterns for specific emotions
   - Adjust confidence thresholds

2. **Relationship progression too fast/slow**
   - Modify interaction thresholds in `relationship_rules`
   - Adjust requirements for each level
   - Add more sophisticated personal info detection

3. **Memory integration errors**
   - Ensure ChromaDB is properly initialized
   - Check that emotion_manager is properly imported
   - Verify textblob is installed

### Performance Considerations
- Emotion detection is fast (< 1ms per message)
- Profiles are saved every 5 interactions automatically
- Clean up old data periodically to maintain performance

## Future Enhancements

Potential improvements you could make:

1. **Advanced Sentiment Analysis**
   - Integrate with more sophisticated NLP models
   - Add sentiment intensity scoring
   - Detect sarcasm and complex emotions

2. **Multi-Modal Emotion Detection**
   - Analyze emoji usage patterns
   - Consider message timing and frequency
   - Detect emotion from image attachments

3. **Relationship Quality Metrics**
   - Track conversation satisfaction
   - Measure relationship health over time
   - Detect relationship deterioration

4. **Predictive Features**
   - Predict user needs based on emotion history
   - Suggest proactive support for struggling users
   - Anticipate escalation before it occurs

## Support

If you encounter issues or need help customizing the emotion system:

1. Run the test suite: `python test_emotion_system.py`
2. Check the logs for emotion processing messages
3. Review the emotion detection patterns and relationship rules
4. Test with known emotional messages to verify detection

The system is designed to be robust and fail gracefully - if emotion detection fails, the bot will continue to function normally without the emotional context.
