# Memory Import Guide for WhisperEngine

This guide explains how to import memories (like those from ChatGPT) into WhisperEngine's vector memory system.

## Overview

WhisperEngine has a sophisticated vector-based memory system that can store and analyze different types of memories:
- **Facts**: Personal information, biographical details
- **Preferences**: Likes, dislikes, favorites
- **Relationships**: Family, friends, colleagues, pets
- **Habits/Behaviors**: Regular activities and patterns
- **General Information**: Other contextual memories

## Quick Start

### Method 1: Using the Simple Container Script (Recommended)

1. **Prepare your memory file**: Create a text file with one memory per line:
   ```
   My name is John Smith
   I work as a software engineer at Google
   I live in San Francisco
   I have a dog named Max
   I love playing guitar
   My favorite food is pizza
   I prefer morning workouts
   I am married to Sarah
   ```

2. **Copy the file to the container**:
   ```bash
   docker cp your_memories.txt whisperengine-bot:/app/memories.txt
   ```

3. **Run the import** (replace `123456789` with the actual Discord user ID):
   ```bash
   docker exec -it whisperengine-bot python import_memories_simple.py 123456789 memories.txt
   ```

### Method 2: Using the Advanced Script (More Control)

The advanced script (`import_memories.py`) offers more features but requires Python environment setup:

1. **Install dependencies** (if running outside container):
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run with dry-run first** to preview what will be imported:
   ```bash
   python import_memories.py 123456789 memories.txt --dry-run
   ```

3. **Run the actual import**:
   ```bash
   python import_memories.py 123456789 memories.txt --confidence 0.9
   ```

## Memory Format Guidelines

### Good Memory Examples:
- `"I am 28 years old"` → Personal fact with high confidence
- `"I work as a data scientist at Microsoft"` → Career information
- `"My favorite programming language is Python"` → Clear preference
- `"I have two cats named Luna and Shadow"` → Pet relationship with specific details
- `"I usually wake up at 6 AM for morning runs"` → Behavioral pattern

### Tips for Better Memory Quality:
1. **Be specific**: "I love Italian food" is better than "I like food"
2. **Include context**: "I graduated from MIT in 2018 with a CS degree"
3. **Use present tense**: "I work at..." not "I used to work at..."
4. **One fact per line**: Don't combine multiple facts in one line

## Understanding the Import Process

### Automatic Classification
The system automatically classifies memories into categories:
- **Personal Facts**: Name, age, location, education, career
- **Preferences**: Likes, dislikes, favorites, interests
- **Relationships**: Family, friends, colleagues, pets
- **Habits/Behaviors**: Regular activities, routines, patterns

### Confidence Scoring
Each memory gets a confidence score (0.0-1.0):
- **High confidence (0.8-1.0)**: Specific facts with clear indicators
- **Medium confidence (0.6-0.8)**: Preferences and general information
- **Lower confidence (0.4-0.6)**: Vague or uncertain statements

### Metadata Enhancement
Each imported memory includes:
- Import timestamp
- Source identification
- Category classification
- Confidence level
- Original text preservation

## Advanced Usage

### Custom Confidence Levels
```bash
python import_memories.py 123456789 memories.txt --confidence 0.95
```

### Batch Processing
```bash
python import_memories.py 123456789 memories.txt --batch-size 5
```

### Verbose Logging
```bash
python import_memories.py 123456789 memories.txt --verbose
```

## Verification and Testing

### 1. Discord Commands
After importing, test with Discord commands:
- `!my_memory` - Shows what the bot remembers about you
- `!list_facts` - Lists specific facts the bot has stored
- `!sync_check` - Checks memory synchronization

### 2. Validate Import Results
The import script provides detailed statistics:
- Total memories processed
- Success/failure counts
- Classification breakdown
- Error details for failed imports

### 3. Memory Quality Check
Use the bot's conversation to verify imported memories:
- Ask about specific facts: "What do you know about my job?"
- Test preferences: "What kind of food do I like?"
- Check relationships: "Tell me about my pets"

## Troubleshooting

### Common Issues:

1. **Container not running**:
   ```bash
   docker ps  # Check if whisperengine-bot is running
   ./bot.sh start dev  # Start if needed
   ```

2. **File not found**:
   ```bash
   # Make sure to copy file to container first
   docker cp memories.txt whisperengine-bot:/app/
   ```

3. **Permission errors**:
   ```bash
   # Check file permissions
   ls -la memories.txt
   chmod 644 memories.txt
   ```

4. **Memory manager initialization fails**:
   - Check if all containers (postgres, redis, qdrant) are healthy
   - Verify environment variables are set correctly

### Getting User ID
To find a Discord user ID:
1. Enable Developer Mode in Discord settings
2. Right-click on the user
3. Select "Copy User ID"

## Best Practices

### 1. Start Small
- Begin with 10-20 key memories
- Test the import process
- Verify results before importing larger datasets

### 2. Organize by Categories
Structure your memory file with related facts grouped together:
```
# Personal Information
My name is John Smith
I am 28 years old
I live in San Francisco

# Career
I work as a software engineer
I specialize in machine learning
I graduated from Stanford in 2018

# Preferences
I love playing guitar
My favorite food is sushi
I prefer morning workouts
```

### 3. Quality over Quantity
- Focus on important, accurate facts
- Avoid outdated information
- Skip redundant or trivial details

### 4. Regular Updates
- Import new memories periodically
- Use Discord commands to verify and update facts
- Remove outdated information when needed

## Integration with WhisperEngine Features

### Memory-Enhanced Conversations
Imported memories enhance the bot's ability to:
- Provide personalized responses
- Remember context across conversations
- Build long-term relationship understanding
- Offer relevant suggestions and recommendations

### Vector Search Capabilities
The system uses vector embeddings to:
- Find semantically related memories
- Retrieve context-appropriate information
- Enable natural language memory queries
- Support intelligent memory associations

### Personality Integration
Imported memories contribute to:
- Dynamic personality profiling
- Emotional intelligence responses
- Character consistency across interactions
- Relationship depth modeling

## Example Memory Import Session

```bash
# 1. Prepare memory file
echo "I am a software engineer at Google
I live in Mountain View, California
I have a golden retriever named Buddy
I love hiking and photography
My favorite programming language is Python
I am married to Emily
I graduated from UC Berkeley in 2019" > my_memories.txt

# 2. Copy to container
docker cp my_memories.txt whisperengine-bot:/app/memories.txt

# 3. Import memories
docker exec -it whisperengine-bot python import_memories_simple.py 123456789 memories.txt

# 4. Verify in Discord
# Use: !my_memory
```

This should result in the bot remembering and being able to reference all these personal details in future conversations!