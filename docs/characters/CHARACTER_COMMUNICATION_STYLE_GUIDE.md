# Character Communication Style Guide

**CDL Category System for WhisperEngine Character Authors**

Version: 2.0  
Last Updated: September 22, 2025  
Architecture: CDL-Based Speaking Style Categories

---

## 🚀 **What Is This System?**

The CDL Communication Style Category system is a **declarative approach** to character personality that replaces complex hardcoded Python logic with simple JSON categories. Instead of writing code to detect character traits, you simply declare what type of communication style your character has.

### **Why This Architecture Is Better**

**❌ OLD WAY (Hardcoded Python Logic):**
```python
# Complex, error-prone detection logic
if "mystical" in character_name.lower() or "dream" in character_name.lower():
    # mystical prompts
elif "elena" in character_name.lower() and has_warm_vocabulary:
    # warm prompts
# ... dozens of if/else statements
```

**✅ NEW WAY (CDL Categories):**
```json
{
  "communication_style": {
    "category": "warm_affectionate"  // Simple, explicit, maintainable
  }
}
```

---

## 📋 **Available Communication Categories**

### **1. `warm_affectionate`**
**Best For:** Characters with naturally warm, loving, and affectionate personalities

**Personality Traits:**
- Naturally warm and caring
- Uses terms of endearment appropriately
- Expresses genuine affection
- Culturally expressive (can use native language phrases)
- Responds to warmth with warmth

**Example Characters:** Elena Rodriguez (Marine Biologist), Caring teachers, Loving mentors, Family-oriented characters

**Generated Prompts Include:**
- Instructions for natural warmth and affection
- Permission to use cultural expressions and loving language
- Guidelines for responding warmly to warm greetings
- Balance of professional expertise with genuine care

### **2. `mystical` / `supernatural`**
**Best For:** Supernatural, mythological, or otherworldly characters

**Personality Traits:**
- Supernatural or mythological nature
- Speaks from otherworldly perspective
- Uses poetic, mystical language naturally
- References cosmic/mythological concepts
- Timeless or otherworldly viewpoint

**Example Characters:** Dream of the Endless, Gods, Spirits, Mythological beings, Fantasy characters

**Generated Prompts Include:**
- Permission for poetic and mystical language
- Guidelines for supernatural perspective
- Instructions for otherworldly communication style
- Metaphorical and cosmic language patterns

### **3. `academic_professional`**
**Best For:** Academics, researchers, scientists, professors

**Personality Traits:**
- Educational and informative approach
- Precise, well-structured language
- Explains complex concepts accessibly
- Uses technical terminology appropriately
- Builds concepts progressively and logically

**Example Characters:** Dr. Marcus Thompson (AI Researcher), Professors, Scientists, Technical experts

**Generated Prompts Include:**
- Instructions for educational communication
- Guidelines for explaining complex concepts
- Technical terminology usage patterns
- Progressive concept building approach

### **4. `creative_casual`**
**Best For:** Artists, designers, creative professionals, indie developers

**Personality Traits:**
- Thoughtful and creative perspective
- Casual, relaxed communication style
- Uses creative analogies and connections
- Honest and straightforward with dry humor
- Shows passion for creative work

**Example Characters:** Marcus Chen (Indie Game Developer), Artists, Writers, Creative professionals

**Generated Prompts Include:**
- Instructions for creative, relaxed communication
- Guidelines for using creative analogies
- Casual language patterns with expertise
- Creative insight and practical experience sharing

### **5. `default` (No Category Specified)**
**Best For:** Professional, realistic characters without special communication needs

**Personality Traits:**
- Realistic, professional communication
- Avoids poetic or mystical language
- Uses normal, everyday conversational language
- Focused on authentic professional interaction

**Generated Prompts Include:**
- Anti-poetic guidelines (prevents fantasy-style language)
- Instructions for realistic professional communication
- Normal conversational language patterns

---

## 🛠 **How to Implement Categories**

### **Standardized JSON Structure (Required Location)**
```json
{
  "character": {
    "personality": {
      "communication_style": {
        "category": "YOUR_CATEGORY_HERE",
        "tone": "character-specific tone",
        "formality": "appropriate formality level",
        // ... other communication style properties
      }
    }
  }
}
```

**⚠️ IMPORTANT:** Categories MUST be placed under `character.personality.communication_style.category`. This is the only supported location.

### **Example Implementation:**
```json
// Academic character example
{
  "character": {
    "personality": {
      "communication_style": {
        "category": "academic_professional",
        "language_patterns": {
          "vocabulary_level": "technical but accessible"
        }
      }
    }
  }
}
```

---

## 📝 **Character Creation Workflow**

### **Step 1: Choose Your Category**
1. **Warm/Affectionate Character?** → `warm_affectionate`
2. **Supernatural/Mythological?** → `mystical` or `supernatural`  
3. **Academic/Scientific?** → `academic_professional`
4. **Creative Professional?** → `creative_casual`
5. **Standard Professional?** → `default` (or omit category)

### **Step 2: Add to Your Character JSON**
```json
{
  "character": {
    "personality": {
      "communication_style": {
        "category": "YOUR_CHOSEN_CATEGORY",
        // ... other communication style properties
      }
    }
  }
}
```

### **Step 3: Test Your Character**
```bash
# Restart your bot to load changes
./multi-bot.sh restart your-bot-name

# Test in Discord or via container
docker exec whisperengine-your-bot python -c "
import asyncio
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration

async def test():
    cdl = CDLAIPromptIntegration()
    prompt = await cdl.create_character_aware_prompt(
        character_file='characters/examples/your-character.json',
        user_id='test',
        message_content='Hello!',
        user_name='Tester'
    )
    print('SPEAKING STYLE:' in prompt and 'SUCCESS' or 'NEED TO CHECK')

asyncio.run(test())
"
```

---

## 🎯 **Real-World Examples**

### **Elena Rodriguez (Marine Biologist) - `warm_affectionate`**
**Before Category System:**
- User: "hola, mi amor!"
- Elena: "I should probably keep things a bit more professional!"

**After Category System:**
- User: "hola, mi amor!"  
- Elena: Gets warm prompts → Responds with natural warmth and Spanish phrases

### **Dr. Marcus Thompson (AI Researcher) - `academic_professional`**
**Before:** Default professional restrictions
**After:** Gets academic-specific prompts for educational, precise communication

### **Marcus Chen (Indie Game Developer) - `creative_casual`**
**Before:** Generic professional guidelines
**After:** Gets creative-specific prompts for casual, insightful communication with gaming analogies

### **Dream of the Endless - `mystical`**
**Before:** Anti-poetic restrictions (inappropriate for mythological character)
**After:** Gets mystical prompts permitting otherworldly, poetic language

---

## 🔧 **Technical Implementation Details**

### **How the System Works**
1. **Character File Loading:** CDL integration reads your character JSON
2. **Category Detection:** System checks for `communication_style.category`
3. **Prompt Generation:** Generates category-specific speaking style instructions
4. **LLM Integration:** Instructions are included in the character-aware prompt

### **Category Lookup Location**
```python
# Standardized lookup path (single location)
category = character.personality.communication_style.category
```

### **Fallback Behavior**
- If no category is specified → Uses `default` category
- If category is unrecognized → Uses `default` category  
- If file read fails → Uses `default` category
- If wrong location used → Category not found, uses `default`

---

## 📈 **Extending the System**

### **Adding New Categories**

**Step 1: Define Your Category**
Choose a clear, descriptive name like:
- `formal_diplomatic` (for ambassadors, diplomats)
- `technical_precise` (for engineers, technical specialists)
- `artistic_expressive` (for artists, poets)
- `casual_friendly` (for informal, buddy-like characters)

**Step 2: Add to CDL Integration**
Edit `src/prompts/cdl_ai_integration.py`:
```python
elif speaking_style_category == 'your_new_category':
    prompt += f"""

YOUR_NEW_CATEGORY SPEAKING STYLE FOR {character.identity.name}:
- Instructions specific to your category
- Guidelines for this communication style
- Behavioral patterns for this type
"""
```

**Step 3: Document Your Category**
Add it to this guide with:
- Description of personality traits
- Example character types
- Sample generated prompt instructions

### **Category Design Best Practices**

1. **Make Categories Broad Enough** to apply to multiple characters
2. **Keep Categories Specific Enough** to generate meaningful prompt differences
3. **Use Clear, Descriptive Names** that character authors can understand easily
4. **Test Categories Thoroughly** with different character types
5. **Document Real-World Impact** on character behavior

---

## 🚨 **Common Issues & Solutions**

### **Issue: Category Not Working**
**Symptoms:** Character gets default prompts instead of category-specific ones

**Solutions:**
1. **Check JSON Syntax:** Ensure valid JSON structure
2. **Verify Category Spelling:** Must match exactly (case-sensitive)
3. **Check File Location:** Ensure character file exists and is accessible
4. **Restart Bot:** Changes require bot restart to take effect

### **Issue: Wrong Category Applied**
**Symptoms:** Character gets different category than expected

**Solutions:**
1. **Check Category Name:** Verify exact spelling and case
2. **Validate JSON Structure:** Ensure `communication_style` is properly nested
3. **Test Category Detection:** Use debug scripts to verify category reading

### **Issue: No Behavioral Change**
**Symptoms:** Category works but character behavior unchanged

**Solutions:**
1. **Check LLM Response:** Some models may not follow instructions precisely
2. **Test with Clear Examples:** Use obvious prompts that should trigger category behavior
3. **Verify Prompt Integration:** Ensure category instructions appear in final prompt

---

## 📚 **References & Resources**

### **Related Documentation**
- `CDL_CHARACTER_SYSTEM_DEBUGGING_SUMMARY.md` - Debugging character issues
- `CHARACTER_JSON_MIGRATION_COMPLETE.md` - Migration from old markdown system
- `MULTI_BOT_SETUP.md` - Setting up multiple character bots

### **Example Character Files**
- `characters/examples/elena-rodriguez.json` - `warm_affectionate` example
- `characters/examples/marcus-thompson.json` - `academic_professional` example  
- `characters/examples/marcus-chen.json` - `creative_casual` example
- `characters/examples/dream_of_the_endless.json` - `mystical` example

### **Technical Implementation**
- `src/prompts/cdl_ai_integration.py` - Main category system implementation
- `src/characters/cdl/parser.py` - CDL parsing and validation
- `src/core/bot.py` - Character integration with bot system

---

## 🎉 **Why This System Rocks**

### **For Character Authors**
- ✅ **Simple to Use:** Just add one line to your character JSON
- ✅ **Predictable Results:** Know exactly what prompts your character will get
- ✅ **No Code Required:** Pure JSON configuration, no Python needed
- ✅ **Easy Testing:** Clear verification that your category is working

### **For Developers**  
- ✅ **Maintainable Architecture:** No more complex if/else personality detection
- ✅ **Extensible Design:** Add new categories without changing existing code
- ✅ **Clear Separation:** Character definition separate from implementation logic
- ✅ **Better Testing:** Each category can be tested independently

### **For Users**
- ✅ **Consistent Characters:** Predictable personality patterns
- ✅ **Authentic Interactions:** Characters behave true to their nature
- ✅ **Rich Diversity:** Different characters feel genuinely different
- ✅ **Natural Responses:** Appropriate reactions to different conversation styles

---

**Happy Character Creating! 🚀**

*The CDL Category System makes character personality definition simple, powerful, and maintainable. Create characters that feel authentic and behave consistently with just a few lines of JSON.*