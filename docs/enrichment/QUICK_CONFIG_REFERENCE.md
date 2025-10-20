# Enrichment Worker - Quick Configuration Reference

## ⚡ TL;DR - Just Tell Me What to Use

### Recommended Default (Copy this to `.env`)
```bash
# Best value: GPT-4o-mini for everything
LLM_CHAT_MODEL=openai/gpt-4o-mini
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

**Cost:** ~$25-50/month for 1000 conversations/day  
**Quality:** 85-90% of Claude quality  
**Speed:** Very fast  

---

## 📋 All Configuration Options

### Budget Configuration
```bash
LLM_CHAT_MODEL=openai/gpt-4o-mini
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```
💰 Cost: $25-50/month | ⭐ Quality: Good

### Balanced Configuration
```bash
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```
💰 Cost: $300-400/month | ⭐ Quality: Excellent summaries, good facts

### High Quality Configuration
```bash
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5
LLM_FACT_EXTRACTION_MODEL=anthropic/claude-sonnet-4.5
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```
💰 Cost: $500-600/month | ⭐ Quality: Premium

---

## 🔧 How to Apply

1. **Edit .env file:**
   ```bash
   nano .env
   ```

2. **Add the configuration lines** (see above)

3. **Recreate container:**
   ```bash
   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --force-recreate enrichment-worker
   ```

4. **Verify:**
   ```bash
   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker
   ```

---

## 🌡️ Temperature Cheat Sheet

| Task | Temperature | Why |
|------|-------------|-----|
| Fact Extraction | **0.2** | Consistency, accuracy, no hallucinations |
| Summaries | **0.7** | Natural flow, readable, still accurate |
| Preferences | **0.7** | Uses summary model (LLM_CHAT_MODEL) |

**Never change these unless you know what you're doing!**

---

## 💰 Cost Comparison (1000 conversations/day)

| Configuration | Monthly Cost |
|---------------|-------------|
| Both GPT-4o-mini | **$25-50** ⭐ Recommended |
| Claude + 4o-mini | **$300-400** |
| Both Claude | **$500-600** |
| Both GPT-4 Turbo | **$1,200+** |

---

## ✅ Verification Commands

### Check current configuration
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec enrichment-worker env | grep LLM
```

### Watch enrichment in action
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker
```

### Check for errors
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs enrichment-worker | grep -i error
```

---

## ⚠️ Common Mistakes

### ❌ DON'T DO THIS:
```bash
# Using restart instead of recreate (env vars won't update!)
docker compose restart enrichment-worker

# High temperature for facts (inconsistent results!)
LLM_FACT_EXTRACTION_TEMPERATURE=1.0

# Using GPT-3.5 when 4o-mini exists (worse quality, similar cost!)
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo
```

### ✅ DO THIS:
```bash
# Always recreate after config changes
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --force-recreate enrichment-worker

# Keep fact extraction temperature low
LLM_FACT_EXTRACTION_TEMPERATURE=0.2

# Use GPT-4o-mini for budget option
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
```

---

## 🎯 Model Selection Decision Tree

```
Need to choose a model?
    │
    ├─ Budget is tight? 
    │   └─ Yes → Use GPT-4o-mini for EVERYTHING
    │
    ├─ Quality is critical?
    │   └─ Yes → Use Claude Sonnet for EVERYTHING
    │
    └─ Want balance?
        └─ Claude for summaries, 4o-mini for facts
```

---

## 📊 Model Comparison Matrix

| Model | Cost | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| **GPT-4o-mini** | 💰 | ⭐⭐⭐⭐ | ⚡⚡⚡ | **Everything** |
| Claude Sonnet | 💰💰💰 | ⭐⭐⭐⭐⭐ | ⚡⚡ | Quality-critical |
| GPT-3.5 | 💰💰 | ⭐⭐⭐ | ⚡⚡⚡ | **Avoid** |
| GPT-4 Turbo | 💰💰💰💰 | ⭐⭐⭐⭐⭐ | ⚡ | **Overkill** |

---

## 🚦 Current Defaults

If you don't set these variables, enrichment worker uses:

```bash
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5  # Default (expensive!)
LLM_FACT_EXTRACTION_MODEL=anthropic/claude-sonnet-4.5  # Default (expensive!)
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

**⚠️ Change to GPT-4o-mini to save money!**

---

## 📞 Need Help?

- **Full Guide:** `docs/enrichment/MODEL_SELECTION_GUIDE.md`
- **Configuration File:** `src/enrichment/config.py`
- **Worker Code:** `src/enrichment/worker.py`
- **Issues:** Check `docker compose logs enrichment-worker`

---

**Last Updated:** October 19, 2025
