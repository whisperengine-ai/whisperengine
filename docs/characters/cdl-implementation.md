# CDL Implementation Guide

## 🚀 Quick Start Guide

### 1. Character Deployment Options

**Multi-Bot Deployment (Recommended):**
```bash
# Deploy dedicated character bots with persistent memory
./multi-bot.sh start elena    # Elena Rodriguez bot (marine biologist)
./multi-bot.sh start marcus   # Marcus Thompson bot (AI researcher)
./multi-bot.sh start jake     # Jake Sterling bot (game developer)
./multi-bot.sh start all      # Start all configured character bots
```

**Single-Bot Character Switching:**
```bash
# Set default character
CDL_DEFAULT_CHARACTER=characters/examples/elena-rodriguez.json python run.py

# Or use Discord roleplay commands
!roleplay elena    # Activate Elena Rodriguez
!roleplay marcus   # Switch to Marcus Thompson  
!roleplay off      # Return to default bot
```

### 2. Character File Structure

Characters are stored as JSON files following CDL v1.0 specification:

```bash
characters/
├── examples/                    # Included character personalities
│   ├── elena-rodriguez.json     # Marine biologist (passionate scientist)
│   ├── marcus-thompson.json     # AI researcher (philosophical tech expert)
│   ├── jake-sterling.json       # Game developer (creative collaborator)  
│   ├── gabriel.json             # Archangel (spiritual wisdom)
│   ├── sophia-blake.json        # Neuroscientist (consciousness explorer)
│   ├── dream_of_the_endless.json # Mythological figure (Sandman series)
│   ├── aethys-omnipotent-entity.json # Omnipotent entity (philosophical)
│   └── ryan-chen.json           # Software engineer (elegant solutions)
├── custom/                      # Your custom characters
│   └── your-character.json
└── default_assistant.json       # Fallback assistant personality
```

### 3. Multi-Bot Environment Configuration

Each character bot requires its own environment file:

```bash
# Elena Rodriguez bot configuration (.env.elena)
DISCORD_BOT_TOKEN=your_elena_token_here
DISCORD_BOT_NAME=elena
CDL_DEFAULT_CHARACTER=characters/examples/elena-rodriguez.json
CONTAINER_NAME=elena-bot

# Marcus Thompson bot configuration (.env.marcus)  
DISCORD_BOT_TOKEN=your_marcus_token_here
DISCORD_BOT_NAME=marcus
CDL_DEFAULT_CHARACTER=characters/examples/marcus-thompson.json
CONTAINER_NAME=marcus-bot
```

## 🧠 CDL Integration with AI Pipeline

The CDL system integrates deeply with WhisperEngine's AI infrastructure:

### **Core Integration Points:**

**🎭 Character-Aware Prompts** (`src/prompts/cdl_ai_integration.py`):
```python
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

# Create character-aware conversation prompts
cdl_integration = CDLAIPromptIntegration(memory_manager)
system_prompt = await cdl_integration.create_character_aware_prompt(
    character_file='characters/examples/elena-rodriguez.json',
    user_id=user_id,
    message_content=message,
    pipeline_result=emotion_analysis  # Optional emotional context
)
```

**💾 Vector Memory Integration** (Qdrant + FastEmbed):
- **Character-specific memory isolation** - Each character maintains separate memory space
- **Semantic relationship tracking** - Characters remember conversation context and user preferences
- **Cross-platform continuity** - Memories persist across Discord, web interface, and future platforms
- **Emotional context storage** - Enhanced emotion analysis stored with memories for personality-consistent responses

**🧠 Personality-Driven Responses:**
- **Big Five traits influence** conversation patterns and response styles
- **Values and beliefs** guide character decision-making in conversations
- **Speech patterns** from CDL voice definition shape response language
- **Cultural background** influences character perspectives and knowledge

### **Advanced Features:**

**🔄 Dynamic Character Loading:**
```python
from src.characters.cdl.parser import load_character

# Characters are cached for performance
character = await cdl_integration.load_character(character_file)

# Access personality traits for response generation
openness = character.personality.big_five.openness  # 0.0 - 1.0
values = character.personality.values  # List of core values
speech_patterns = character.identity.voice.speech_patterns
```

**🎯 Context-Aware Behavior:**
- **Project tracking** - Characters remember and discuss their current projects
- **Goal-oriented conversations** - Characters work toward their defined goals
- **Relationship awareness** - Characters build relationships through memory system
- **Emotional intelligence** - Enhanced vector emotion analysis adapts responses

**🌐 Universal Identity Integration:**
```python
# Characters work with Universal Identity for cross-platform relationships
from src.identity.universal_identity import create_identity_manager

# Characters remember users across Discord, web, and future platforms
universal_user = await identity_manager.get_or_create_discord_user(
    discord_user_id=discord_id,
    username=username  
)
```

## 🔧 Character Development Workflow

### **Creating Custom Characters:**

**1. Start with Template:**
```bash
# Copy existing character as starting point
cp characters/examples/elena-rodriguez.json characters/custom/my-character.json
```

**2. Customize Core Identity:**
```json
{
  "character": {
    "metadata": {
      "character_id": "my-unique-character-id",
      "name": "My Character Name",
      "version": "1.0.0"
    },
    "identity": {
      "name": "Character Name",
      "occupation": "Character Profession", 
      "location": "Character Location",
      "description": "Character overview"
    }
  }
}
```

**3. Define Personality:**
```json
{
  "personality": {
    "big_five": {
      "openness": 0.8,        # Creativity and openness to experience
      "conscientiousness": 0.7, # Organization and reliability
      "extraversion": 0.6,     # Social energy and assertiveness  
      "agreeableness": 0.8,    # Cooperation and empathy
      "neuroticism": 0.3       # Emotional stability (low = stable)
    },
    "values": ["authenticity", "growth", "connection"],
    "fears": ["isolation", "meaninglessness"],
    "dreams": ["making a difference", "deep relationships"]
  }
}
```

**4. Create Backstory & Current Life:**
- **Formative experiences** that shaped the character
- **Current projects** and goals they're working toward
- **Relationships** and social connections
- **Daily routines** and lifestyle patterns

**5. Test Character:**
```bash
# Test with single bot method
CDL_DEFAULT_CHARACTER=characters/custom/my-character.json python run.py

# Or create dedicated bot environment
# Create .env.mycharacter with character-specific configuration
./multi-bot.sh start mycharacter
```

### **Character Iteration:**
- **Monitor conversations** - How does the character respond in different contexts?
- **Adjust personality traits** - Fine-tune Big Five values based on desired behavior
- **Expand backstory** - Add details that emerge through conversations
- **Update current projects** - Keep character goals and activities fresh
- **Refine speech patterns** - Develop unique voice and communication style

### **Performance Optimization:**
- **Characters are cached** after first load for better performance
- **Memory queries are optimized** with character-specific vector search
- **Conversation context** is efficiently managed through semantic memory
- **Hot reloading** - Some character changes don't require bot restarts

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