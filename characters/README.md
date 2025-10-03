# Characters Directory

This directory contains all Character Definition Language (CDL) files for WhisperEngine's AI Roleplay Character platform. Each character is a complete personality definition that can be deployed as its own bot instance or used in roleplay scenarios.

## 🎭 Available Character Personalities

### 🤖 **Default Assistant** (`default_assistant.json`)
A helpful, adaptive AI assistant that provides balanced support and information.

### 📁 **Examples Directory** - Complete Character Personalities
- **🧬 Elena Rodriguez** (`examples/elena-rodriguez.json`) - Marine biologist passionate about ocean conservation
- **🤖 Marcus Thompson** (`examples/marcus-thompson.json`) - AI researcher exploring technology's impact on humanity  
- **📸 Jake Sterling** (`examples/jake.json`) - Adventure photographer and survival instructor
- **✨ Gabriel** (`examples/gabriel.json`) - Rugged British gentleman with dry wit and sophistication
- **� Dream of the Endless** (`examples/dream_of_the_endless.json`) - Mythological character from Neil Gaiman's Sandman
- **🎨 Sophia Blake** (`examples/sophia-blake.json`) - Sophisticated marketing executive
- **🌟 Aethys** (`examples/aethys-omnipotent-entity.json`) - Omnipotent entity for philosophical exploration  
- **🎮 Ryan Chen** (`examples/ryan.json`) - Independent game developer with perfectionist approach

## 🚀 Two Ways to Use Characters

### **Method 1: Multi-Bot Deployment (Recommended)**
Deploy each character as its own dedicated bot instance with persistent memory:

```bash
# Each character runs as a separate bot with dedicated environment file
./multi-bot.sh start elena    # Elena Rodriguez bot (marine biologist)
./multi-bot.sh start marcus   # Marcus Thompson bot (AI researcher)
./multi-bot.sh start jake     # Jake Sterling bot (adventure photographer)
./multi-bot.sh start gabriel  # Gabriel bot
./multi-bot.sh start all      # Start all available character bots
```

**Character-specific environment files:**
- `.env.elena` → Elena Rodriguez (uses `characters/examples/elena-rodriguez.json`)
- `.env.marcus` → Marcus Thompson (uses `characters/examples/marcus-thompson.json`)
- `.env.jake` → Jake Sterling (uses `characters/examples/jake-sterling.json`)
- `.env.gabriel` → Gabriel (uses `characters/examples/gabriel.json`)

### **Method 2: Single Bot with Character Switching**
Use one bot instance that can switch between different character personalities:

```bash
# Set default character for single bot deployment
CDL_DEFAULT_CHARACTER=characters/examples/elena-rodriguez.json

# In Discord, switch characters using roleplay commands
!roleplay elena    # Activate Elena Rodriguez personality
!roleplay marcus   # Switch to Marcus Thompson personality  
!roleplay jake     # Switch to Jake Sterling personality
!roleplay off      # Return to default bot behavior
```

## 🛠️ Character Definition Language (CDL)

WhisperEngine uses a comprehensive JSON-based format for character definitions that creates authentic AI personalities:

### **Complete Personality System:**
- **🎭 Identity & Appearance** - Physical characteristics, voice, cultural background
- **🧠 Psychology** - Big Five personality traits, values, fears, dreams, quirks
- **📚 Backstory** - Origin story, formative experiences, life phases, achievements
- **🏠 Current Life** - Living situation, relationships, projects, goals, daily routines
- **💭 Memory Integration** - How characters process and recall information across conversations

### **Advanced Features:**
- **🔄 Persistent Memory** - Characters remember conversations across sessions using vector memory
- **🎯 Emotional Intelligence** - Enhanced emotion analysis adapts character responses
- **🌐 Cross-Platform Identity** - Characters maintain relationships across Discord, web interface, and future platforms
- **🔒 Bot-Specific Isolation** - Each character has completely separate memory preventing personality bleed
- **📈 Relationship Evolution** - Characters develop deeper relationships through extended interaction

### **Integration with AI Pipeline:**
- **🎨 Prompt Generation** - Character traits dynamically influence conversation prompts
- **💾 Vector Memory** - Qdrant database stores character-specific memories and knowledge
- **🧠 Context Awareness** - Characters understand conversation history and relationship development
- **⚡ Adaptive Responses** - Learning user communication preferences over time

## 🎨 Creating Your Own Characters

### **Quick Start: Copy and Customize**
1. **Copy an existing character** from `examples/` folder
2. **Modify the JSON** to create your unique personality
3. **Test locally** using single bot method or create dedicated environment file
4. **Deploy** as either dedicated bot or add to roleplay rotation

### **Character File Structure:**
```json
{
  "cdl_version": "1.0",
  "format": "json", 
  "description": "Your character description",
  "character": {
    "metadata": {
      "character_id": "your-unique-character-id",
      "name": "Character Name",
      "version": "1.0.0",
      "created_by": "Your Name",
      "license": "open"
    },
    "identity": { /* Physical appearance, voice, occupation */ },
    "personality": { /* Psychology, traits, values, quirks */ },
    "backstory": { /* Life history, formative experiences */ },
    "current_life": { /* Present situation, goals, relationships */ }
  }
}
```

### **Advanced Character Creation:**
- **📖 Study the examples** - Each character in `examples/` demonstrates different personality archetypes
- **🧪 Use the CDL Specification** - Complete technical documentation at `docs/characters/cdl-specification.md`
- **🔬 Personality Research** - Base traits on psychological research (Big Five model supported)
- **🎭 Consistent Voice** - Define unique speech patterns, vocabulary, and communication style
- **💡 Clear Motivation** - Give characters compelling goals, fears, and personal projects

## 📖 Documentation & Resources

For complete character creation guidance, see:
- **📋 [CDL Specification](../docs/characters/cdl-specification.md)** - Complete technical format documentation
- **🛠️ [CDL Implementation Guide](../docs/characters/cdl-implementation.md)** - Integration and usage instructions
- **🎨 [Character Communication Guide](../docs/characters/CHARACTER_COMMUNICATION_STYLE_GUIDE.md)** - Voice and personality consistency
- **🚀 [Multi-Bot Setup Guide](../MULTI_BOT_SETUP.md)** - Deploying character bots

## 🔄 File Management

When running in Docker, this entire directory is mounted into containers, allowing you to:
- **✏️ Edit characters** without rebuilding containers
- **➕ Add new characters** by dropping JSON files into `examples/` or custom folders
- **🔄 Hot reload** character changes (some features require bot restart)
- **📂 Organize** characters in subdirectories for better management

**Character files are completely portable** - copy them between installations, share with others, or version control your custom personalities.
- **Relationship Dynamics** - How the character builds and maintains relationships
- **Contextual Adaptability** - Situation-aware response modifications

### Template Variables

CDL characters support automatic template variable replacement:

- `{BOT_NAME}` - Replaced with the Discord bot's display name
- `{USER_NAME}` - Replaced with the user's name (context-dependent)
- `{CURRENT_DATE}` - Replaced with current date
- `{CURRENT_TIME}` - Replaced with current time

## Creating Custom Characters

1. **Start with a Template**: Copy `default_assistant.json` or an example character
2. **Modify Metadata**: Update character_id, name, and description
3. **Customize Personality**: Adjust traits, values, and communication style
4. **Configure Environment**: Set `CDL_DEFAULT_CHARACTER` to point to your new file
5. **Test and Iterate**: Characters reload automatically for real-time testing

### Character Schema

```json
{
  "cdl_version": "1.0",
  "format": "json", 
  "character": {
    "metadata": { ... },
    "core_personality": { ... },
    "communication_style": { ... },
    "behavioral_patterns": { ... },
    "memory_integration": { ... },
    "relationship_dynamics": { ... },
    "contextual_adaptability": { ... }
  }
}
```

## Hot Reload Support

The bot reloads character files dynamically, so you can edit characters while the bot is running and see changes immediately without restarting the container.

## Legacy Prompt System (DEPRECATED)

The old markdown-based prompt system (`prompts/` directory) is deprecated. While still functional, new deployments should use CDL characters for:

- ✅ Structured, validated character definitions
- ✅ Rich personality modeling capabilities  
- ✅ Better maintainability and version control
- ✅ Enhanced relationship dynamics
- ✅ Contextual adaptability features

To migrate from prompts to CDL characters, see the [CDL Migration Guide](../docs/migration/PROMPT_TO_CDL_MIGRATION.md).

## Support Formats

WhisperEngine supports both JSON and YAML formats for CDL characters:

- **JSON**: `character_name.json` (recommended for production)
- **YAML**: `character_name.yaml` (human-friendly for development)

Both formats are automatically detected and parsed correctly.