# Enrichment Worker LLM Model Configuration

**Date**: October 19, 2025  
**Status**: Implemented  
**Branch**: `feature/async-enrichment-worker`

## Overview

The enrichment worker now supports **separate LLM models** for different tasks, matching the main bot's configuration pattern. This allows flexible cost/quality trade-offs.

## Configuration Variables

### From `.env` file:

```bash
# API Configuration (shared)
LLM_CHAT_API_KEY=sk-or-v1-...
LLM_CHAT_API_URL=https://openrouter.ai/api/v1

# Conversation Summaries (high-quality conversational understanding)
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5
LLM_TEMPERATURE=0.7

# Fact Extraction (structured data extraction)
LLM_FACT_EXTRACTION_MODEL=anthropic/claude-sonnet-4.5  # Default: same as chat
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

## Model Usage Breakdown

### 1. Conversation Summaries (2 LLM calls per window)

**Uses**: `LLM_CHAT_MODEL` (default: Claude Sonnet 4.5)

**Tasks**:
- Summary text generation (3-5 sentence comprehensive summary)
- Key topics extraction (3-5 main topics as JSON)

**Why high-quality model**:
- Conversational understanding requires nuance
- Must preserve emotional tone and context
- Summary quality directly impacts bot context quality

**Cost impact**: ~500-600 tokens per window

---

### 2. Fact Extraction (1 LLM call per window)

**Uses**: `LLM_FACT_EXTRACTION_MODEL` (default: Claude Sonnet 4.5)

**Tasks**:
- Extract structured facts from conversation window
- Analyze confirmation patterns across messages
- Build knowledge graph relationships
- Detect temporal fact evolution

**Why this is DIFFERENT from runtime fact extraction**:

| Aspect | Runtime Extraction (Disabled) | Enrichment Extraction |
|--------|------------------------------|----------------------|
| **Context** | Single message | 5-10 message window |
| **Quality** | Basic extraction | Conversation-level analysis |
| **Latency** | 200-500ms (blocking!) | Async background (no impact) |
| **Model** | GPT-3.5-turbo (cheap) | Claude Sonnet 4.5 (superior) |
| **Purpose** | Quick facts | High-confidence knowledge |

**Default: Claude Sonnet 4.5** because:
1. ✅ **No latency cost** - runs async in background
2. ✅ **Complex reasoning** - conversation-level context analysis
3. ✅ **Better conflict detection** - temporal fact evolution
4. ✅ **Knowledge graph building** - semantic relationships

**Can override to GPT-3.5** if cost is priority:
```bash
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo
```

**Cost impact**: ~1000 tokens per window

---

## Total LLM Calls Per User Per Window

**3 LLM calls total** (2 summaries + 1 fact extraction):

1. **Summary text generation** → `LLM_CHAT_MODEL`
2. **Key topics extraction** → `LLM_CHAT_MODEL`
3. **Fact extraction** → `LLM_FACT_EXTRACTION_MODEL`

**Total tokens**: ~1500-2000 per conversation window

---

## Cost Analysis

### Scenario 1: All Claude Sonnet 4.5 (DEFAULT)

```
Summary text:     500 tokens × $3/1M input  = $0.0015
Topics:           100 tokens × $3/1M input  = $0.0003
Fact extraction: 1000 tokens × $3/1M input  = $0.0030
---------------------------------------------------
Total per window:                            $0.0048
```

**Pros**:
- Highest quality summaries and facts
- Best conversation understanding
- Superior conflict detection
- Better knowledge graph relationships

**Cons**:
- ~3x more expensive than mixed approach

---

### Scenario 2: Mixed Models (COST OPTIMIZED)

```bash
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5  # Summaries
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo  # Facts
```

```
Summary text:     500 tokens × $3/1M input    = $0.0015
Topics:           100 tokens × $3/1M input    = $0.0003
Fact extraction: 1000 tokens × $0.5/1M input  = $0.0005
-----------------------------------------------------
Total per window:                              $0.0023
```

**Pros**:
- ~50% cost savings vs all-Claude
- Still high-quality summaries
- Good-enough fact extraction

**Cons**:
- Lower quality fact extraction
- Weaker conversation-level reasoning
- May miss subtle confirmation patterns

---

## Recommendation

### ✅ **DEFAULT: All Claude Sonnet 4.5**

**Reasoning**:
1. Enrichment runs **async in background** - no latency penalty
2. Sophisticated conversation-level analysis **benefits from Claude's reasoning**
3. Cost difference is **minimal** for background processing (~$0.005 per window)
4. Higher quality facts → better bot personality and memory

### 🔄 **Override to Mixed** if:
- Processing **thousands of windows per day** (cost adds up)
- Basic fact extraction is sufficient
- Budget constraints outweigh quality benefits

---

## How to Override

### Option 1: Use GPT-3.5 for fact extraction only

```bash
# .env
LLM_CHAT_MODEL=anthropic/claude-sonnet-4.5
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo
```

### Option 2: Use all GPT-4 Turbo (balance)

```bash
# .env
LLM_CHAT_MODEL=openai/gpt-4-turbo
LLM_FACT_EXTRACTION_MODEL=openai/gpt-4-turbo
```

### Option 3: Use all Mistral (cheapest)

```bash
# .env
LLM_CHAT_MODEL=mistralai/mistral-large-latest
LLM_FACT_EXTRACTION_MODEL=mistralai/mistral-large-latest
```

---

## Implementation Details

### Configuration Loading

**File**: `src/enrichment/config.py`

```python
# Summaries use LLM_CHAT_MODEL
LLM_CHAT_MODEL: str = os.getenv("LLM_CHAT_MODEL", "anthropic/claude-sonnet-4.5")

# Fact extraction uses separate model (defaults to same as chat)
LLM_FACT_EXTRACTION_MODEL: str = os.getenv(
    "LLM_FACT_EXTRACTION_MODEL", 
    "anthropic/claude-sonnet-4.5"  # Can override to cheaper model
)
```

### Worker Initialization

**File**: `src/enrichment/worker.py`

```python
# Single LLM client with API key/URL
self.llm_client = create_llm_client(
    llm_client_type="openrouter",
    api_url=config.LLM_API_URL,
    api_key=config.LLM_API_KEY
)

# Summarization engine uses LLM_CHAT_MODEL
self.summarizer = SummarizationEngine(
    llm_client=self.llm_client,
    llm_model=config.LLM_CHAT_MODEL
)

# Fact extraction engine uses LLM_FACT_EXTRACTION_MODEL
self.fact_extractor = FactExtractionEngine(
    llm_client=self.llm_client,
    model=config.LLM_FACT_EXTRACTION_MODEL
)
```

---

## Migration Notes

### Breaking Changes

**None** - defaults maintain current behavior (all Claude Sonnet 4.5)

### For Existing Deployments

If you were using `LLM_MODEL` environment variable:
- **Old**: `LLM_MODEL=anthropic/claude-sonnet-4.5`
- **New**: Auto-detects from `LLM_CHAT_MODEL` and `LLM_FACT_EXTRACTION_MODEL`

### Backwards Compatibility

The config supports legacy `OPENROUTER_API_KEY` but prefers `LLM_CHAT_API_KEY` (standardized with main bot).

---

## Testing Recommendations

### 1. Verify Model Loading

```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
  logs enrichment-worker | grep "initialized"
```

Should see:
```
EnrichmentWorker initialized - Summary Model: anthropic/claude-sonnet-4.5, 
Fact Model: anthropic/claude-sonnet-4.5
```

### 2. Test Cost Optimization

Change `.env`:
```bash
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo
```

Restart worker:
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
  restart enrichment-worker
```

Verify:
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml \
  logs enrichment-worker | grep "Fact Model"
```

Should see:
```
Fact Model: openai/gpt-3.5-turbo
```

---

## Related Documentation

- [Enrichment Worker Architecture](ENRICHMENT_WORKER_ARCHITECTURE.md)
- [Runtime Fact Extraction Deprecation](RUNTIME_FACT_EXTRACTION_DEPRECATION.md)
- [Memory Intelligence Convergence Roadmap](../roadmaps/MEMORY_INTELLIGENCE_CONVERGENCE_ROADMAP.md)
