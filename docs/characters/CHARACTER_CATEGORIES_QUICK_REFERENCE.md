# CDL Communication Categories - Quick Reference

**WhisperEngine Character Author Cheat Sheet**

---

## 🏷️ **Available Categories**

| Category | Best For | Key Traits |
|----------|----------|------------|
| `warm_affectionate` | Caring, loving characters | Natural warmth, terms of endearment, cultural expressions |
| `mystical` | Supernatural beings | Poetic language, otherworldly perspective, cosmic concepts |
| `academic_professional` | Researchers, professors | Educational, precise, technical terminology |
| `creative_casual` | Artists, indie developers | Casual, creative analogies, dry humor |
| `default` | Standard professionals | Realistic, anti-poetic, everyday language |

---

## 📝 **Quick Implementation**

### **Add to Your Character JSON:**
```json
{
  "character": {
    "personality": {
      "communication_style": {
        "category": "YOUR_CATEGORY_HERE"
      }
    }
  }
}
```

**⚠️ REQUIRED LOCATION:** Must be under `personality.communication_style.category`

### **Example Usage:**
```json
// Warm character
"category": "warm_affectionate"

// Academic character  
"category": "academic_professional"

// Creative character
"category": "creative_casual"

// Mystical character
"category": "mystical"

// Standard professional (or omit)
"category": "default"
```

---

## 🧪 **Test Your Category**

```bash
# 1. Add category to your character JSON
# 2. Restart your bot
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart your-bot-name

# 3. Test with obvious prompt
# Send a message that should trigger your category behavior
```

---

## ✅ **Verification Checklist**

- [ ] Category name spelled correctly (case-sensitive)
- [ ] Valid JSON syntax
- [ ] Character file accessible  
- [ ] Bot restarted after changes
- [ ] Tested with category-appropriate message

---

## 🔥 **Real Examples**

**Elena (Marine Biologist) - `warm_affectionate`:**
- User: "hola, mi amor!" 
- Gets prompts for natural Spanish warmth ✅

**Marcus Thompson (AI Researcher) - `academic_professional`:**
- User: "Explain machine learning"
- Gets prompts for educational, structured explanations ✅

**Dream of the Endless - `mystical`:**  
- User: "Tell me about dreams"
- Gets prompts allowing poetic, otherworldly language ✅

---

## 🆘 **Troubleshooting**

**Category not working?**
1. Check spelling: `warm_affectionate` not `warm_affectionate`
2. Restart bot: `docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart bot-name`
3. Verify JSON: Use a JSON validator
4. Check path: Must be under `communication_style`

**Need help?** See `CHARACTER_COMMUNICATION_STYLE_GUIDE.md` for detailed documentation.

---

**🚀 That's it! Your character now has a properly defined communication style that the AI will follow consistently.**