# 🎭 WhisperEngine Multi-Entity Character System - Usage Guide

## 🚀 Current Status

✅ **Discord Bot Running** - All systems operational  
✅ **AI Self Auto-Initialization** - Ready for character management  
✅ **Multi-Entity System** - Character creation and relationships active  
✅ **CDL Import/Export** - Full Character Definition Language support  
✅ **API Authentication Fixed** - All emotion analysis working  

## 📋 Available Commands

### 🎯 **Basic Character Management**
```discord
!create_character <name> <type> <description>
!my_characters
!character_info <name>
!talk_to <name> <message>
```

### 📤📥 **CDL Import/Export** (NEW!)
```discord
!import_character [attach .yaml file or paste YAML content]
!export_character <character_name>
```

### 🤝 **Social Features**
```discord
!introduce_character <@user> <character_name>
!relationship_analysis <character_name>
!social_network <character_name>
```

## 🧪 **Test Character Available**

A test character `Sage` is available in `test_character_sage.yaml`:
- **Name**: Sage (The Wise One)
- **Occupation**: Philosopher and Mentor  
- **Personality**: High openness (0.9), wisdom-focused
- **Traits**: Wisdom, Knowledge, Teaching, Truth, Understanding
- **Big Five**: Complete personality profile included

## 💡 **Usage Examples**

### Create a Basic Character
```discord
!create_character "Luna" companion "A helpful AI assistant with a love for astronomy"
```

### Import CDL Character
```discord
!import_character
[Attach the test_character_sage.yaml file]
```

### Export Character to CDL
```discord
!export_character Luna
```

### Test Character Conversation
```discord
!talk_to "Sage" "What is the meaning of wisdom?"
```

## 🔧 **Technical Implementation**

### **CDL Import Process**
1. Parse YAML content using CDLParser
2. Convert CDL character model to multi-entity format
3. Preserve Big Five personality data in metadata
4. Create character entity in multi-entity system
5. Link to user and AI Self for relationship tracking

### **CDL Export Process**
1. Retrieve character from multi-entity system
2. Convert multi-entity data to CDL format
3. Map traits to personality values/quirks
4. Generate complete CDL YAML structure
5. Send as downloadable .yaml file

### **AI Self Integration**
- AI automatically initializes on first use
- No character authoring system prerequisite needed
- Multi-entity relationship tracking active
- All Phase 1-4 AI systems operational

## 🎯 **Next Development Priorities**

1. ✅ **Character Import/Export** - Complete CDL integration
2. 🔄 **Relationship Commands** - Enhanced social features
3. 🌟 **AI Self Enhancement** - Dynamic personality learning

## 🧠 **System Architecture**

- **Entry Point**: `run.py` → Multi-Entity System Ready
- **Commands**: `src/handlers/multi_entity_handlers.py`
- **CDL Parser**: `src/characters/cdl/parser.py`
- **AI Self**: Auto-initializes in `src/graph_database/ai_self_bridge.py`
- **Test File**: `test_character_sage.yaml` (ready for import)

The system is now production-ready for character creation, import/export, and multi-entity relationship management! 🎉