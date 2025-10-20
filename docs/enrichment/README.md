# WhisperEngine Enrichment Worker Documentation

## 📚 Documentation Overview

This directory contains comprehensive guides for configuring and operating the WhisperEngine enrichment worker.

### Quick Navigation

- **[Quick Config Reference](./QUICK_CONFIG_REFERENCE.md)** - Copy/paste configurations, TL;DR guide
- **[Model Selection Guide](./MODEL_SELECTION_GUIDE.md)** - Comprehensive model and temperature guide
- **[Enrichment Architecture](../../docs/architecture/ENRICHMENT_ARCHITECTURE.md)** - System design (if exists)

---

## 🚀 Getting Started

### Step 1: Choose Your Configuration

**New to enrichment?** Start here:
- Open [`QUICK_CONFIG_REFERENCE.md`](./QUICK_CONFIG_REFERENCE.md)
- Copy the **"Budget Configuration"** to your `.env` file
- That's it! You're done.

**Want to understand trade-offs?** Read this:
- Open [`MODEL_SELECTION_GUIDE.md`](./MODEL_SELECTION_GUIDE.md)
- Review the decision tree and cost comparisons
- Choose configuration based on your needs

---

## 🎯 What is the Enrichment Worker?

The enrichment worker is a **background service** that:

1. **Scans conversation history** in Qdrant vector storage
2. **Generates summaries** of time-windowed conversations
3. **Extracts facts** about users (preferences, locations, interests)
4. **Identifies relationships** between entities
5. **Detects preference changes** over time

All of this happens **asynchronously** - zero impact on real-time bot performance!

---

## 📋 Configuration Quick Start

### Recommended Default (GPT-4o-mini)

Add to `.env`:
```bash
LLM_CHAT_MODEL=openai/gpt-4o-mini
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

Apply configuration:
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --force-recreate enrichment-worker
```

**Cost:** ~$25-50/month for 1000 conversations/day  
**Quality:** 85-90% of Claude quality  
**Speed:** Very fast  

---

## 🌡️ Temperature Settings

| Variable | Recommended | Purpose |
|----------|-------------|---------|
| `LLM_TEMPERATURE` | **0.7** | Summaries & preferences (readable, natural) |
| `LLM_FACT_EXTRACTION_TEMPERATURE` | **0.2** | Facts & entities (consistent, accurate) |

**Don't change these unless you have a specific reason!**

---

## 💰 Cost Examples

Based on 1000 conversations/day (30,000/month):

| Configuration | Monthly Cost | Quality | Use Case |
|---------------|--------------|---------|----------|
| Both GPT-4o-mini | **$25-50** | Good | Startups, testing, budget-conscious |
| Claude + 4o-mini | **$300-400** | Excellent | Production, balanced needs |
| Both Claude | **$500-600** | Premium | Enterprise, quality-critical |

---

## 🔧 Common Tasks

### Change Models
1. Edit `.env` file
2. Update `LLM_CHAT_MODEL` and/or `LLM_FACT_EXTRACTION_MODEL`
3. Run: `docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --force-recreate enrichment-worker`

### Check Current Configuration
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec enrichment-worker env | grep LLM
```

### View Logs
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker
```

### Restart Worker
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart enrichment-worker
```

### Stop Worker
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop enrichment-worker
```

---

## 📊 Monitoring

### Check Recent Facts
```sql
-- Connect to database
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec postgres psql -U whisperengine -d whisperengine

-- Query recent facts
SELECT fact_type, fact_value, confidence, created_at 
FROM fact_entities 
ORDER BY created_at DESC 
LIMIT 10;
```

### Check Recent Summaries
```sql
SELECT user_id, bot_name, summary_text, message_count, created_at
FROM conversation_summaries
ORDER BY created_at DESC
LIMIT 5;
```

### Monitor Confidence Scores
```sql
-- Average fact confidence (should be > 0.7)
SELECT AVG(confidence) as avg_confidence
FROM fact_entities
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

## ⚠️ Troubleshooting

### Worker Not Starting
```bash
# Check container status
docker ps -a | grep enrichment

# Check logs for errors
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs enrichment-worker | grep ERROR
```

### No Facts Being Extracted
```bash
# Verify configuration
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec enrichment-worker env | grep LLM

# Check if LLM API key is set
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec enrichment-worker env | grep LLM_CHAT_API_KEY
```

### High Costs
- Switch to GPT-4o-mini if using Claude
- Reduce `ENRICHMENT_INTERVAL_SECONDS` (process less frequently)
- Reduce `LOOKBACK_DAYS` (process fewer old messages)

---

## 📖 Documentation Files

### [QUICK_CONFIG_REFERENCE.md](./QUICK_CONFIG_REFERENCE.md)
**Purpose:** Fast copy/paste configurations  
**Best for:** Quick setup, configuration changes  
**Read time:** 2-3 minutes  

**Contains:**
- TL;DR configurations
- Verification commands
- Common mistakes to avoid
- Quick decision tree

### [MODEL_SELECTION_GUIDE.md](./MODEL_SELECTION_GUIDE.md)
**Purpose:** Comprehensive model and temperature guide  
**Best for:** Understanding trade-offs, cost optimization  
**Read time:** 10-15 minutes  

**Contains:**
- Detailed cost comparisons
- Temperature explanations
- Performance characteristics
- Testing procedures
- Monitoring queries
- Optimization strategies

---

## 🔗 Related Documentation

- **Main Architecture:** `docs/architecture/README.md`
- **Character System:** `docs/architecture/CHARACTER_ARCHETYPES.md`
- **Memory System:** `docs/architecture/MEMORY_INTELLIGENCE_CONVERGENCE.md`
- **Testing Guide:** `docs/testing/DIRECT_PYTHON_TESTING_GUIDE.md`

---

## 💡 Quick Tips

1. **Start with GPT-4o-mini** - best value for money
2. **Never change temperatures** unless you have a specific reason
3. **Always recreate container** after .env changes (don't just restart)
4. **Monitor costs weekly** - enrichment can add up at scale
5. **Check confidence scores** to validate quality
6. **Test in dev first** before changing production config

---

## 🆘 Getting Help

**Something not working?**
1. Check the logs: `docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs enrichment-worker`
2. Review [QUICK_CONFIG_REFERENCE.md](./QUICK_CONFIG_REFERENCE.md) for common mistakes
3. Read [MODEL_SELECTION_GUIDE.md](./MODEL_SELECTION_GUIDE.md) for detailed troubleshooting

**Need to understand costs better?**
- See cost comparison tables in [MODEL_SELECTION_GUIDE.md](./MODEL_SELECTION_GUIDE.md)
- Monitor your actual usage via database queries (examples included)

**Want to optimize quality?**
- Review temperature settings in [MODEL_SELECTION_GUIDE.md](./MODEL_SELECTION_GUIDE.md)
- Check confidence scores using monitoring queries
- Consider upgrading to Claude for quality-critical use cases

---

**Last Updated:** October 19, 2025  
**WhisperEngine Version:** 1.0.0  
**Enrichment Worker Status:** Production Ready ✅
