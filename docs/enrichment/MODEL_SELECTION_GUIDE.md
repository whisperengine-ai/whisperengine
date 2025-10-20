# WhisperEngine Enrichment Worker - Model Selection & Temperature Guide

## 📋 Quick Reference

### Recommended Configurations

**Budget Option (Best Value)** ⭐ RECOMMENDED
```bash
LLM_CHAT_MODEL=openai/gpt-4o-mini
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

**Balanced Option (Quality + Cost)**
```bash
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

**High Quality Option (Best Results)**
```bash
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5
LLM_FACT_EXTRACTION_MODEL=anthropic/claude-sonnet-4.5
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

---

## 🎯 Understanding the Two Models

WhisperEngine's enrichment worker uses **TWO separate models** for different tasks:

### 1. **Conversation Summary Model** (`LLM_CHAT_MODEL`)

**What it does:**
- Generates conversation summaries (narrative text)
- Extracts user preferences from conversations
- Analyzes communication patterns
- Creates readable, human-friendly summaries

**Requirements:**
- Good at narrative/creative writing
- Understands context and nuance
- Produces natural-sounding text

**Temperature:** `0.7` (medium - balances accuracy and readability)

### 2. **Fact Extraction Model** (`LLM_FACT_EXTRACTION_MODEL`)

**What it does:**
- Extracts structured facts about users
- Identifies entities and relationships
- Detects preference changes and conflicts
- Produces JSON-formatted data

**Requirements:**
- Excellent at structured output
- Consistent, deterministic results
- Strong instruction-following
- Low hallucination rate

**Temperature:** `0.2` (low - maximizes consistency and accuracy)

---

## 💰 Model Cost Comparison

### Input Costs (per 1M tokens)

| Model | Input Cost | Output Cost | Speed | Quality |
|-------|-----------|-------------|-------|---------|
| **GPT-4o-mini** | $0.15 | $0.60 | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| GPT-3.5-turbo | $0.50 | $1.50 | ⚡⚡⚡ | ⭐⭐⭐ |
| Mistral Small | $0.20 | $0.60 | ⚡⚡⚡ | ⭐⭐⭐ |
| Claude Sonnet 3.5 | $3.00 | $15.00 | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| Claude Sonnet 4.5 | $3.00 | $15.00 | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| GPT-4 Turbo | $10.00 | $30.00 | ⚡ | ⭐⭐⭐⭐⭐ |

### Monthly Cost Estimates

Assumptions: 1,000 conversations/day, average 50 messages each, 20-message windows

| Configuration | Monthly Input | Monthly Output | Total/Month |
|---------------|---------------|----------------|-------------|
| **Both GPT-4o-mini** | $4.50 | $18.00 | **$22.50** |
| Claude/4o-mini mix | $90.00 | $225.00 | **$315.00** |
| Both Claude | $90.00 | $450.00 | **$540.00** |
| Both GPT-4 Turbo | $300.00 | $900.00 | **$1,200.00** |

**Note:** Enrichment processes LARGE volumes of text (conversation windows), so costs add up quickly!

---

## 🌡️ Temperature Settings Explained

### What is Temperature?

Temperature controls the **randomness/creativity** of LLM outputs:
- **0.0** = Deterministic, always picks the most likely token
- **1.0** = Balanced between likely and creative tokens
- **2.0** = Highly random, unpredictable outputs

### Recommended Temperatures

#### For Fact Extraction: **0.2** (Low)

**Why?**
- ✅ **Consistency**: Same conversation → same facts extracted
- ✅ **Accuracy**: Sticks closely to what's actually stated
- ✅ **Structured output**: Better JSON formatting compliance
- ✅ **Less hallucination**: Doesn't invent facts
- ✅ **Reproducibility**: Critical for data quality

**Example Output (temp=0.2):**
```json
{
  "facts": [
    {"type": "preference", "value": "likes pizza", "confidence": 0.95},
    {"type": "location", "value": "lives in Seattle", "confidence": 0.90}
  ]
}
```

**What happens at higher temps (0.8+)?**
- ❌ Different facts from same conversation each run
- ❌ Invented relationships not in the text
- ❌ JSON parsing failures (creative formatting)
- ❌ Inconsistent confidence scores

#### For Summaries: **0.7** (Medium)

**Why?**
- ✅ **Natural flow**: Summaries read like human-written text
- ✅ **Engaging**: Not robotic or repetitive
- ✅ **Accurate**: Still grounded in conversation content
- ✅ **Varied phrasing**: Avoids monotonous patterns

**Example Output (temp=0.7):**
```
User shared their excitement about their upcoming trip to Seattle, 
mentioning their love of coffee and Pacific Northwest hiking. They 
expressed particular interest in visiting local pizza spots and 
discussed their preference for thin-crust styles.
```

**What happens at lower temps (0.2)?**
- ❌ "User mentioned Seattle. User mentioned pizza. User mentioned hiking."
- ❌ Repetitive sentence structures
- ❌ Robotic, unnatural phrasing

**What happens at higher temps (1.2+)?**
- ❌ May add details not in conversation
- ❌ Overly creative interpretations
- ❌ Less reliable accuracy

---

## 🎯 Model Selection Decision Tree

### Step 1: What's Your Priority?

```
┌─────────────────────────────────────────┐
│ What matters most to you?              │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
    ┌───▼────┐         ┌────▼───┐
    │  COST  │         │QUALITY │
    └───┬────┘         └────┬───┘
        │                   │
        ▼                   ▼
   Use 4o-mini         Use Claude
   for both            for both
```

### Step 2: Task-Specific Recommendations

#### Fact Extraction Model Selection

**Use GPT-4o-mini when:**
- ✅ Budget is a concern
- ✅ Processing high volumes (1000+ conversations/day)
- ✅ Acceptable to have 90-95% accuracy vs 98% with Claude
- ✅ Facts are relatively straightforward (preferences, locations, etc.)

**Use Claude Sonnet when:**
- ✅ Need highest accuracy (medical, legal, sensitive data)
- ✅ Complex relationship detection required
- ✅ Processing multilingual conversations
- ✅ Budget allows for 20x higher cost

**Avoid GPT-3.5-turbo when:**
- ❌ Weaker at structured output than 4o-mini
- ❌ More prone to hallucination
- ❌ Not significantly cheaper than 4o-mini

#### Summary Model Selection

**Use GPT-4o-mini when:**
- ✅ Need good-quality summaries at low cost
- ✅ Summaries are for internal use/logging
- ✅ Processing high volumes
- ✅ 80% quality of Claude is acceptable

**Use Claude Sonnet when:**
- ✅ Summaries shown to users
- ✅ Need best narrative quality
- ✅ Complex emotional/contextual understanding needed
- ✅ Budget allows premium pricing

---

## 🔧 Configuration Examples

### Example 1: Startup/Budget Mode
**Best for:** New deployments, testing, cost-conscious operations

```bash
# .env configuration
LLM_CHAT_MODEL=openai/gpt-4o-mini
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2

# Monthly cost: ~$25-50 for 1000 conversations/day
```

### Example 2: Production Balanced
**Best for:** Production deployments with quality expectations

```bash
# .env configuration
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5  # High-quality summaries
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini  # Budget facts
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2

# Monthly cost: ~$300-400 for 1000 conversations/day
```

### Example 3: Enterprise/High Quality
**Best for:** Premium deployments, user-facing features

```bash
# .env configuration
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5
LLM_FACT_EXTRACTION_MODEL=anthropic/claude-sonnet-4.5
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2

# Monthly cost: ~$500-600 for 1000 conversations/day
```

### Example 4: Experimental Mix
**Best for:** Testing different providers

```bash
# .env configuration
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5
LLM_FACT_EXTRACTION_MODEL=mistralai/mistral-small-latest
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2

# Monthly cost: ~$350-450 for 1000 conversations/day
```

---

## 🚀 How to Apply Configuration

### 1. Edit your `.env` file
```bash
nano .env
```

Add/update these lines:
```bash
LLM_CHAT_MODEL=openai/gpt-4o-mini
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

### 2. Recreate the enrichment worker container
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --force-recreate enrichment-worker
```

**Why recreate?** Environment variables are set at container creation time, not runtime.

### 3. Verify configuration
```bash
# Check environment variables
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec enrichment-worker env | grep LLM

# Check logs for model usage
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs enrichment-worker | grep -i "initialized"
```

---

## 📊 Performance Characteristics

### GPT-4o-mini
- **Latency:** 1-3 seconds per request
- **Token throughput:** Very high
- **Rate limits:** 30,000 tokens/min (tier 1)
- **Best for:** High-volume, cost-sensitive workloads
- **Quality:** 85-90% of Claude quality
- **Structured output:** Excellent

### Claude Sonnet 4.5
- **Latency:** 2-5 seconds per request
- **Token throughput:** Medium-high
- **Rate limits:** Varies by tier
- **Best for:** Quality-critical workloads
- **Quality:** Industry-leading
- **Structured output:** Excellent

### GPT-3.5-turbo
- **Latency:** 1-2 seconds per request
- **Token throughput:** Very high
- **Rate limits:** 40,000 tokens/min (tier 1)
- **Best for:** Legacy compatibility (NOT recommended)
- **Quality:** 70-75% of Claude quality
- **Structured output:** Moderate

---

## ⚠️ Common Pitfalls

### Pitfall 1: Using High Temperature for Facts
**Problem:**
```bash
LLM_FACT_EXTRACTION_TEMPERATURE=1.0  # ❌ TOO HIGH
```

**Result:** Different facts extracted from same conversation each run, hallucinated data

**Solution:**
```bash
LLM_FACT_EXTRACTION_TEMPERATURE=0.2  # ✅ Consistent, accurate
```

### Pitfall 2: Using Low Temperature for Summaries
**Problem:**
```bash
LLM_TEMPERATURE=0.1  # ❌ TOO LOW
```

**Result:** "User said X. User mentioned Y. User discussed Z." (robotic)

**Solution:**
```bash
LLM_TEMPERATURE=0.7  # ✅ Natural, readable
```

### Pitfall 3: Using GPT-3.5 When 4o-mini Exists
**Problem:**
```bash
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo  # ❌ Outdated choice
```

**Result:** Worse quality, similar cost to 4o-mini

**Solution:**
```bash
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini  # ✅ Better quality, similar cost
```

### Pitfall 4: Not Recreating Container After Config Changes
**Problem:**
```bash
# Edit .env
nano .env

# Just restart (environment variables not updated!)
docker compose restart enrichment-worker  # ❌ Won't pick up new env vars
```

**Solution:**
```bash
# Edit .env
nano .env

# Force recreate container
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --force-recreate enrichment-worker  # ✅
```

---

## 🧪 Testing Your Configuration

### Test 1: Verify Model Configuration
```bash
# Check what models are configured
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec enrichment-worker env | grep LLM_

# Should see:
# LLM_CHAT_MODEL=openai/gpt-4o-mini
# LLM_FACT_EXTRACTION_MODEL=openai/gpt-4o-mini
# LLM_TEMPERATURE=0.7
# LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

### Test 2: Monitor First Enrichment Cycle
```bash
# Follow logs in real-time
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f enrichment-worker

# Look for:
# ✅ "EnrichmentWorker initialized - ... Summary Model: openai/gpt-4o-mini, Fact Model: openai/gpt-4o-mini"
# ✅ "Extracted X facts from conversation"
# ✅ "Created Y summaries"
# ❌ "ERROR" or "Failed to" messages
```

### Test 3: Check Data Quality
```bash
# Connect to PostgreSQL
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml exec postgres psql -U whisperengine -d whisperengine

# Check recent facts
SELECT fact_type, fact_value, confidence, created_at 
FROM fact_entities 
ORDER BY created_at DESC 
LIMIT 10;

# Check recent summaries
SELECT user_id, bot_name, summary_text, message_count, created_at
FROM conversation_summaries
ORDER BY created_at DESC
LIMIT 5;
```

---

## 📈 Monitoring & Optimization

### Cost Tracking

Track your token usage over time:
```sql
-- Total facts extracted per day
SELECT DATE(created_at) as date, COUNT(*) as facts_extracted
FROM fact_entities
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Summaries created per day
SELECT DATE(created_at) as date, COUNT(*) as summaries_created, 
       AVG(message_count) as avg_messages_per_summary
FROM conversation_summaries
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Quality Monitoring

Monitor fact extraction quality:
```sql
-- Average confidence scores (should be > 0.7 for good quality)
SELECT AVG(confidence) as avg_confidence, 
       MIN(confidence) as min_confidence,
       MAX(confidence) as max_confidence
FROM fact_entities
WHERE created_at > NOW() - INTERVAL '7 days';

-- Summary compression ratios (lower = more efficient)
SELECT AVG(compression_ratio) as avg_compression,
       AVG(confidence_score) as avg_confidence
FROM conversation_summaries
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

## 🔄 When to Change Models

### Upgrade to Higher Quality Model When:
- ✅ You notice low-quality summaries or missed facts
- ✅ Users complain about inaccurate bot memory
- ✅ Confidence scores are consistently < 0.7
- ✅ Budget allows for improved quality

### Downgrade to Budget Model When:
- ✅ Current quality exceeds requirements
- ✅ Cost optimization is priority
- ✅ Processing volumes are very high
- ✅ Facts/summaries are for internal use only

### Keep Current Configuration When:
- ✅ Quality meets expectations
- ✅ No cost concerns
- ✅ No user complaints
- ✅ Confidence scores > 0.8

---

## 📚 Additional Resources

- **OpenRouter Models:** https://openrouter.ai/models
- **Anthropic Pricing:** https://www.anthropic.com/pricing
- **OpenAI Pricing:** https://openai.com/pricing
- **Enrichment Worker Code:** `src/enrichment/worker.py`
- **Configuration:** `src/enrichment/config.py`

---

## 💡 Quick Tips

1. **Start with GPT-4o-mini** for everything - best value proposition
2. **Keep fact extraction temperature at 0.2** - never go above 0.3
3. **Keep summary temperature at 0.7** - sweet spot for quality
4. **Monitor costs weekly** - enrichment can be expensive at scale
5. **Test config changes in dev** before applying to production
6. **Always recreate container** after changing .env
7. **Check logs for errors** after configuration changes
8. **Track confidence scores** to measure quality over time

---

**Last Updated:** October 19, 2025
**WhisperEngine Version:** 1.0.0
**Enrichment Worker Status:** Production Ready
