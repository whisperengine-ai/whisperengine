# Character Learning Persistence - Quick Reference

**Status**: ✅ Layer 1 (PostgreSQL) Complete  
**Date**: October 17, 2025

---

## 🚀 Quick Start

```python
from src.characters.learning.character_insight_storage import (
    create_character_insight_storage,
    CharacterInsight,
    InsightRelationship,
    LearningTimelineEvent
)

# 1. Create storage
storage = await create_character_insight_storage()

# 2. Store an insight
insight = CharacterInsight(
    character_id=1,
    insight_type="emotional_pattern",
    insight_content="Shows enthusiasm for marine topics",
    confidence_score=0.85,
    importance_level=7,
    triggers=["marine", "ocean"]
)
insight_id = await storage.store_insight(insight)

# 3. Retrieve insights
insights = await storage.get_insights_by_triggers(
    character_id=1,
    triggers=["marine"],
    limit=5
)
```

---

## 📊 Database Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `character_insights` | Core insights | `insight_content`, `confidence_score`, `triggers` |
| `character_insight_relationships` | Graph connections | `from_insight_id`, `to_insight_id`, `relationship_type` |
| `character_learning_timeline` | Evolution history | `learning_event`, `before_state`, `after_state` |

---

## 🔧 Common Operations

### Store Insight
```python
insight_id = await storage.store_insight(CharacterInsight(...))
```

### Search by Keywords
```python
insights = await storage.get_insights_by_triggers(
    character_id=1,
    triggers=["keyword1", "keyword2"],
    limit=10
)
```

### Get Recent Insights
```python
recent = await storage.get_recent_insights(
    character_id=1,
    days_back=30
)
```

### Create Relationship (Graph)
```python
rel_id = await storage.create_relationship(InsightRelationship(
    from_insight_id=1,
    to_insight_id=3,
    relationship_type="supports",
    strength=0.8
))
```

### Record Timeline Event
```python
event_id = await storage.record_learning_event(LearningTimelineEvent(
    character_id=1,
    learning_event="Discovered passion for marine conservation",
    learning_type="self_discovery",
    significance_score=0.9
))
```

---

## 🧪 Testing

```bash
# Run test suite
source .venv/bin/activate
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5433"
python tests/automated/test_character_insight_storage.py
```

**Expected**: All 10 tests pass ✅

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `src/characters/learning/character_insight_storage.py` | Storage implementation (611 lines) |
| `alembic/versions/20251017_1919_336ce8830dfe_*.py` | Database migration |
| `tests/automated/test_character_insight_storage.py` | Test suite (317 lines) |
| `CHARACTER_LEARNING_LAYER_1_COMPLETE.md` | Full documentation |

---

## 🎯 Integration Points (Future)

1. **Message Processor** (`src/core/message_processor.py`)
   - After detecting learning moments → `storage.store_insight()`

2. **CDL Prompt** (`src/prompts/cdl_ai_integration.py`)
   - Include relevant insights in system prompt

3. **Bot Initialization** (`src/core/bot.py`)
   - Create storage instance and inject dependencies

---

## 🚀 Next Phases

- **Phase 2**: Qdrant semantic index (semantic similarity search)
- **Phase 3**: InfluxDB metrics (learning velocity, trends)

---

## ✅ What's Complete

- [x] PostgreSQL tables with indexes
- [x] Python storage class with CRUD operations
- [x] Graph relationship support
- [x] Timeline event tracking
- [x] Analytics queries
- [x] Comprehensive test suite
- [x] All tests passing

**Ready for integration!** 🎉
