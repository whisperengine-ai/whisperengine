# 🎯 Hybrid Transaction System - Quick Reference

## System Architecture

```
User Message → Workflow Detection → Transaction Action → Prompt Injection → LLM Response
     │                 │                    │                    │              │
     │                 │                    │                    │              │
  "I'll have     Pattern Match:        Create tx in      Add context to    "Well sugar,
   a whiskey"    "i'll have (.*)"      PostgreSQL        character prompt   one whiskey..."
                 Confidence: 0.95       State: pending    (150 chars)
```

## Component Map

| Component | File | Purpose |
|-----------|------|---------|
| **Workflow Definitions** | `characters/workflows/dotty_bartender.yaml` | YAML patterns, state machines, lookup tables |
| **Workflow Manager** | `src/roleplay/workflow_manager.py` | Intent detection, context extraction, state transitions |
| **Platform-Agnostic Detection** | `src/core/message_processor.py` | Workflow detection in Phase 2.5 (works for Discord, web API, etc.) |
| **CDL Character Enhancement** | `src/core/message_processor.py` | Workflow prompt injection into CDL character prompt |
| **Bot Initialization** | `src/core/bot.py` | Async WorkflowManager initialization |
| **Character Config** | `characters/examples/dotty.json` | transaction_config: mode, workflow_files, llm_fallback |

## Integration Flow

### 1. Bot Startup
```python
# src/core/bot.py (line 1088)
asyncio.create_task(self.initialize_workflow_manager())
  ↓
# Wait for dependencies: transaction_manager, llm_client
  ↓
# Load workflows from CDL character file
workflows = await workflow_manager.load_workflows_for_character(character_file)
  ↓
# Result: 3 workflows loaded (drink_order, custom_drink_order, open_tab)
```

### 2. Message Processing
```python
# src/core/message_processor.py (Phase 2.5 - PLATFORM AGNOSTIC)
await self._process_workflow_detection(message_context)
  ↓
trigger_result = await workflow_manager.detect_intent(message, user_id, bot_name)
  ↓
# Pattern match: "i'll have (a |an )?(.*)" → drink_name = "whiskey"
# Lookup: drink_prices["whiskey"] → price = 5
  ↓
workflow_result = await workflow_manager.execute_workflow_action(trigger_result, ...)
  ↓
# Action: "new_workflow" → Create transaction in PostgreSQL
# Result: {"transaction_id": "tx_abc123", "prompt_injection": "User ordered: whiskey..."}
  ↓
# Store in MessageContext metadata for CDL enhancement
message_context.metadata['workflow_prompt_injection'] = prompt_injection
```

### 3. LLM Integration
```python
# src/core/message_processor.py (line 1413)
character_prompt = await cdl_integration.create_unified_character_prompt(...)
  ↓
# Inject workflow context
workflow_prompt = message_context.metadata.get('workflow_prompt_injection')
if workflow_prompt:
    character_prompt += f"\n\n🎯 ACTIVE TRANSACTION CONTEXT:\n{workflow_prompt}"
  ↓
# LLM receives enhanced prompt with transaction awareness
response = await llm_client.get_chat_response(enhanced_context)
```

## YAML Workflow Schema

### Workflow Definition
```yaml
workflows:
  drink_order:
    name: "Standard Drink Order"
    description: "Handle standard menu drink orders"
    
    # Intent Detection
    triggers:
      patterns:
        - pattern: "i'll have (a |an )?(.*)"
          confidence: 0.95
      keywords:
        - "whiskey"
        - "beer"
        - "wine"
    
    # Context Extraction
    context_extraction:
      drink_name:
        type: "pattern_group"
        pattern_index: 2  # Regex group
      price:
        type: "lookup"
        table: "drink_prices"
        key_field: "drink_name"
    
    # State Machine
    states:
      pending:
        transitions:
          completed:
            patterns: ["here you go", "payment received"]
          cancelled:
            patterns: ["never mind", "cancel"]
    
    # Actions
    actions:
      on_trigger:
        type: "new_workflow"
        prompt: "User ordered: {drink_name}, price {price} coins, wait for payment"
      on_completed:
        type: "complete_transaction"
        prompt: "Payment received, serve drink"

# Lookup Tables
lookup_tables:
  drink_prices:
    whiskey: 5
    beer: 4
    wine: 6
```

## Performance Targets

| Path | Frequency | Latency | Description |
|------|-----------|---------|-------------|
| **Declarative** | 90% | ~6ms | Pattern match + context extract + DB insert |
| **LLM Fallback** | 10% | ~500-2000ms | LLM validation + context extract + DB insert |
| **Average** | 100% | ~50ms | Weighted average (6ms × 0.9 + 500ms × 0.1) |

## Database Schema

```sql
CREATE TABLE role_transactions (
  transaction_id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  bot_name VARCHAR(100) NOT NULL,
  workflow_name VARCHAR(255) NOT NULL,
  state VARCHAR(50) NOT NULL,  -- pending, completed, cancelled
  context_data JSONB,           -- {drink_name: "whiskey", price: 5}
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## Testing Commands

### Start Bot
```bash
./multi-bot.sh start dotty
```

### Test Order
**Discord DM**: `I'll have a whiskey`
**Expected**: "Well sugar, one whiskey comin' right up! That'll be 5 coins, darlin'. 🥃✨"

### Check Transaction
```bash
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
  "SELECT * FROM role_transactions WHERE bot_name = 'dotty' ORDER BY created_at DESC LIMIT 1;"
```

### Monitor Logs
```bash
docker logs whisperengine-dotty-bot -f | grep "WORKFLOW"
```

## Key Log Messages

### Success Path
```
✅ Loaded 3 workflows for character
🎯 WORKFLOW: Detected intent - workflow: drink_order, confidence: 0.95
🎯 WORKFLOW: Extracted context: {'drink_name': 'whiskey', 'price': 5}
🎯 WORKFLOW: Created new transaction tx_abc123
🎯 WORKFLOW: Injected transaction context into character prompt (150 chars)
```

### LLM Fallback
```
🎯 WORKFLOW: Pattern matching confidence below threshold
🎯 WORKFLOW: Using LLM validation for custom request
🎯 WORKFLOW: LLM validated: custom drink with chocolate and strawberries
```

## Character Configuration

### CDL Structure
```json
{
  "character": {
    "metadata": { ... },
    "identity": { ... },
    "personality": { ... },
    "background": { ... },
    "transaction_config": {
      "mode": "hybrid",
      "workflow_files": ["characters/workflows/dotty_bartender.yaml"],
      "llm_fallback": true,
      "description": "Hybrid transaction management..."
    }
  }
}
```

## Common Issues

### Workflow Not Detected
**Symptom**: Bot responds but no transaction created
**Check**: `docker logs whisperengine-dotty-bot | grep "Loaded.*workflows"`
**Fix**: Verify `transaction_config` in `dotty.json`

### Prompt Not Injected
**Symptom**: Transaction created but LLM doesn't mention price
**Check**: `docker logs whisperengine-dotty-bot | grep "Injected transaction context"`
**Fix**: Verify `workflow_prompt_injection` in metadata pass-through

### State Transition Fails
**Symptom**: Transaction stays pending after payment
**Check**: `docker logs whisperengine-dotty-bot | grep "state_transition"`
**Fix**: Verify payment patterns in YAML workflow

## File Locations

```
whisperengine/
├── characters/
│   ├── examples/
│   │   └── dotty.json                     # CDL config with transaction_config
│   └── workflows/
│       └── dotty_bartender.yaml           # Workflow definitions
├── src/
│   ├── core/
│   │   ├── bot.py                         # WorkflowManager initialization
│   │   └── message_processor.py           # Prompt injection
│   ├── handlers/
│   │   └── events.py                      # Workflow detection
│   └── roleplay/
│       └── workflow_manager.py            # WorkflowManager class
└── docs/
    ├── WORKFLOW_INTEGRATION_COMPLETE.md   # Integration summary
    ├── WORKFLOW_TESTING_GUIDE.md          # Testing guide
    └── HYBRID_TRANSACTION_QUICK_REF.md    # This file
```

## Next Steps

### Immediate Testing
1. Start Dotty bot
2. Test drink order → payment flow
3. Verify transaction creation
4. Check LLM awareness

### Short-term Expansion
1. Add guild message handler
2. Implement open_tab workflow
3. Add more drink types
4. Create analytics dashboard

### Long-term Scale
1. Add workflows for other characters
2. Build workflow creation UI
3. Implement A/B testing
4. Add workflow versioning

---

**Status**: ✅ **INTEGRATION COMPLETE**

**Last Updated**: 2025-01-20

**Quick Start**: `./multi-bot.sh start dotty` → DM "I'll have a whiskey"
