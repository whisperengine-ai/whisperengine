# Embedding Model Guidelines for Users

## 🎯 Quick Decision Guide

### Stick with Current Setup (Recommended)
Your current Nomic embed model is excellent. Only change if you have specific needs.

### Current Configuration Analysis
- ✅ Model: `text-embedding-nomic-embed-text-v1.5`
- ✅ Dimensions: 768 (good balance)
- ✅ Quality: Very high
- ✅ Privacy: Open source, can run locally
- ✅ Cost: Free when run locally

## 🔄 When to Change Models

### Reasons to Stay:
- Current quality is good
- Privacy-focused setup
- No vendor lock-in
- Stable 768 dimensions

### Reasons to Change:
- Need OpenAI ecosystem integration
- Want larger models (3072 dimensions)
- Specific performance requirements
- Moving to cloud-only setup

## ⚠️ Important: Dimension Changes

**Critical Rule:** Changing to a model with different dimensions requires resetting ChromaDB!

### Same Dimensions (Safe):
- `text-embedding-nomic-embed-text-v1.5` (768) ↔ `all-mpnet-base-v2` (768)
- `text-embedding-ada-002` (1536) ↔ `text-embedding-3-small` (1536)

### Different Dimensions (Requires Reset):
- `text-embedding-nomic-embed-text-v1.5` (768) → `text-embedding-3-small` (1536)
- `all-MiniLM-L6-v2` (384) → anything else

## 🚀 Migration Process

### For Same Dimensions:
1. Stop bot
2. Update `LLM_EMBEDDING_MODEL_NAME` in .env
3. Restart bot

### For Different Dimensions:
1. Stop bot
2. Run: `python reset_chromadb.py`
3. Update `LLM_EMBEDDING_MODEL_NAME` in .env
4. Restart bot
5. Allow time for memory regeneration

## � Automatic Fallback Feature

**NEW**: The embedding system now automatically falls back to `LLM_CHAT_API_URL` when `LLM_EMBEDDING_API_URL` is not configured!

### How it works:
1. **Primary**: Uses `LLM_EMBEDDING_API_URL` if set
2. **Fallback**: Uses `LLM_CHAT_API_URL` if embedding URL not set
3. **Default**: Falls back to `http://localhost:1234/v1` if neither is set

### Benefits:
- ✅ Simpler configuration - one API URL for both chat and embeddings
- ✅ Automatic detection of embedding-capable providers (OpenAI, OpenRouter, localhost)
- ✅ No breaking changes - existing configurations still work

### Example configurations:
```bash
# Minimal - uses same endpoint for both
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_EMBEDDING_MODEL_NAME=text-embedding-nomic-embed-text-v1.5
# Embedding API URL will automatically use LLM_CHAT_API_URL

# Separate endpoints (advanced)
LLM_CHAT_API_URL=https://api.openai.com/v1
LLM_EMBEDDING_API_URL=https://api.openai.com/v1  # Explicit (optional)
LLM_EMBEDDING_MODEL_NAME=text-embedding-3-small
```

## �📊 Model Recommendations

### Development/Testing:
```bash
# Local, fast, good enough
LLM_EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
# No API URL = uses local ChromaDB
```

### Production (Privacy-focused):
```bash
# Your current setup - excellent choice!
LLM_EMBEDDING_API_URL=http://localhost:1234/v1
LLM_EMBEDDING_MODEL_NAME=text-embedding-nomic-embed-text-v1.5
```

### Production (Cloud):
```bash
# Best cost/performance
LLM_EMBEDDING_API_URL=https://api.openai.com/v1
LLM_EMBEDDING_MODEL_NAME=text-embedding-3-small
LLM_EMBEDDING_API_KEY=your_key_here
```

### Production (Highest Quality):
```bash
# Best quality, higher cost
LLM_EMBEDDING_API_URL=https://api.openai.com/v1
LLM_EMBEDDING_MODEL_NAME=text-embedding-3-large
LLM_EMBEDDING_API_KEY=your_key_here
```

## 🛠️ Tools Available

- `python debug_embedding_issue.py` - Test current setup
- `python migrate_embedding_model.py` - Interactive migration helper
- `python reset_chromadb.py` - Reset database for dimension changes

## 💡 Pro Tips

1. **Test first**: Always test new models before production
2. **Backup**: Consider backing up ChromaDB before major changes
3. **Monitor**: Check embedding quality after changes
4. **Document**: Keep track of which model you're using
5. **Plan migrations**: Do dimension changes during low-usage periods

## ❓ Quick FAQ

**Q: Is Nomic embed good enough?**
A: Yes! It's competitive with OpenAI models and open source.

**Q: Should I upgrade to OpenAI models?**
A: Only if you need specific features or ecosystem integration.

**Q: How often should I change models?**
A: Rarely. Stability is more important than chasing new models.

**Q: What if I mess up the migration?**
A: Run `python reset_chromadb.py` and restart. Memories will regenerate.
