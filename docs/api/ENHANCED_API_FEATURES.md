# Enhanced WhisperEngine External Chat API

> **📖 For complete API documentation, see [Chat API Reference](./CHAT_API_REFERENCE.md)**  
> This document provides a quick overview of enhanced features. For full integration details, request/response schemas, error handling, and code examples, refer to the comprehensive Chat API Reference.

The WhisperEngine External Chat API has been enhanced to include user facts and relationship metrics in all responses (available in `extended` metadata level).

## New Response Fields

### `user_facts` Object
Contains extracted information about the user:
```json
{
  "name": "Alex Thompson",
  "interaction_count": 5,
  "first_interaction": "2024-10-03T10:30:00Z",
  "last_interaction": "2024-10-03T11:45:00Z"
}
```

### `relationship_metrics` Object
Contains relationship progression metrics:
```json
{
  "affection": 70,
  "trust": 65,
  "attunement": 85
}
```

**Metrics Range**: 0-100 (higher values indicate stronger relationships)
- **Affection**: Based on relationship level (stranger=30, acquaintance=50, friend=70, close_friend=90)
- **Trust**: Calculated from interaction count, positive/negative sentiment, and escalation history
- **Attunement**: Measures emotional understanding based on emotion history and diversity

## API Endpoints

### Single Message: `POST /api/chat`

**Enhanced Response:**
```json
{
  "success": true,
  "response": "Hello Alex! It's wonderful to meet someone passionate about marine biology...",
  "processing_time_ms": 1250,
  "memory_stored": true,
  "timestamp": "2024-10-03T11:45:00Z",
  "user_facts": {
    "name": "Alex Thompson",
    "interaction_count": 3,
    "first_interaction": "2024-10-03T10:30:00Z",
    "last_interaction": "2024-10-03T11:45:00Z"
  },
  "relationship_metrics": {
    "affection": 65,
    "trust": 58,
    "attunement": 78
  }
}
```

### Batch Processing: `POST /api/chat/batch`

**Enhanced Response:**
```json
{
  "results": [
    {
      "index": 0,
      "user_id": "user123",
      "success": true,
      "response": "Hi Sarah! Data science is fascinating...",
      "processing_time_ms": 1100,
      "memory_stored": true,
      "user_facts": {
        "name": "Sarah",
        "interaction_count": 1
      },
      "relationship_metrics": {
        "affection": 50,
        "trust": 42,
        "attunement": 78
      }
    }
  ],
  "total_processed": 1,
  "timestamp": "2024-10-03T11:45:00Z"
}
```

## Implementation Details

### User Facts Extraction
- **Name Detection**: Extracts names from "My name is..." patterns or metadata
- **Interaction Tracking**: Counts total messages and tracks first/last interaction timestamps
- **Extensible**: Additional facts can be added (profession, interests, etc.)

### Relationship Metrics Calculation
- **Affection**: Maps relationship levels to numerical scores
- **Trust**: Factors in interaction frequency, sentiment analysis, and conflict history
- **Attunement**: Evaluates emotional understanding based on conversation patterns

### Memory Integration
- Leverages existing WhisperEngine vector memory system
- Bot-specific memory isolation (Elena's memories ≠ Marcus's memories)
- Preserves conversation context and personality consistency

## Testing

Run the enhanced API test:
```bash
# Ensure Elena bot is running
./multi-bot.sh start elena

# Run the test script
python test_enhanced_api.py
```

## Backwards Compatibility

The enhancement is fully backwards compatible:
- Existing API clients will continue to work
- New fields are added to responses without breaking changes
- Fallback values provided if metrics cannot be calculated

## Character-Specific Behavior

Different WhisperEngine characters may calculate metrics differently based on their personalities:
- **Elena** (Marine Biologist): Emphasizes educational relationship building
- **Marcus** (AI Researcher): Focuses on intellectual trust indicators  
- **Gabriel** (British Gentleman): Values courtesy and proper relationship progression
- **Ryan** (Indie Game Developer): Relaxed, creative relationship building

Each character's unique CDL (Character Definition Language) personality influences how they assess and respond to relationship dynamics.