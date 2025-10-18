# 🧪 Workflow System Testing Guide

## Quick Start

### 1. Start Dotty Bot
```bash
./multi-bot.sh start dotty
```

### 2. Wait for Initialization
Look for these log messages:
```
✅ Loaded 3 workflows for character
🎯 WORKFLOW MANAGER: Initialized with 3 workflows
```

### 3. Test Basic Drink Order
**Discord DM to Dotty**: `I'll have a whiskey`

**Expected Response**:
- Dotty acknowledges order naturally (with price)
- Example: "Well sugar, one whiskey comin' right up! That'll be 5 coins, darlin'. 🥃✨"

**Backend Verification**:
```bash
# Check transaction created in PostgreSQL
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
  "SELECT * FROM role_transactions WHERE user_id = '<your_discord_id>' ORDER BY created_at DESC LIMIT 1;"
```

Expected output:
```
transaction_id | user_id | bot_name | workflow_name | state   | context_data
tx_abc123      | 123456  | dotty    | drink_order   | pending | {"drink_name":"whiskey","price":5}
```

## Test Scenarios

### Scenario 1: Standard Drink Order + Payment
**Purpose**: Test declarative path (~6ms) with state transition

**Steps**:
1. **Order**: `I'll have a whiskey`
   - Expected: Dotty acknowledges, mentions 5 coins
   - Transaction state: `pending`

2. **Payment**: `Here you go`
   - Expected: Dotty thanks you, serves drink
   - Transaction state: `completed`

**Validation**:
```bash
# Check transaction state updated
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
  "SELECT transaction_id, state, context_data FROM role_transactions WHERE user_id = '<your_discord_id>' ORDER BY created_at DESC LIMIT 1;"
```

### Scenario 2: Order Cancellation
**Purpose**: Test state transition to cancelled

**Steps**:
1. **Order**: `I'll have a beer`
   - Expected: Dotty acknowledges, mentions 4 coins
   - Transaction state: `pending`

2. **Cancel**: `Never mind`
   - Expected: Dotty acknowledges cancellation naturally
   - Transaction state: `cancelled`

**Validation**:
```bash
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
  "SELECT state FROM role_transactions WHERE user_id = '<your_discord_id>' ORDER BY created_at DESC LIMIT 1;"
```

Expected: `cancelled`

### Scenario 3: Multiple Drink Options
**Purpose**: Test pattern matching variants

**Test Messages**:
- `I'll have a whiskey` (pattern: "i'll have")
- `Give me a beer` (pattern: "give me")
- `Can I get some wine?` (keyword: "wine")
- `Whiskey please` (keyword: "whiskey")

**Expected**: All should trigger drink_order workflow

**Validation**: Check logs for workflow detection
```bash
docker logs whisperengine-dotty-bot --tail 50 | grep "WORKFLOW"
```

Look for:
```
🎯 WORKFLOW: Detected intent - workflow: drink_order, confidence: 0.95
🎯 WORKFLOW: Created new transaction tx_abc123
🎯 WORKFLOW: Injected transaction context into character prompt
```

### Scenario 4: Custom Drink (LLM Fallback)
**Purpose**: Test LLM fallback path (~500-2000ms)

**Steps**:
1. **Custom Request**: `Can you make me something with chocolate and strawberries?`
   - Expected: Dotty responds creatively (LLM validation)
   - Transaction state: `pending`
   - Workflow: `custom_drink_order`

2. **Payment**: `Here's 8 coins`
   - Expected: Dotty thanks you, serves custom drink
   - Transaction state: `completed`

**Validation**: Check workflow_name in database
```bash
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
  "SELECT workflow_name, context_data FROM role_transactions WHERE user_id = '<your_discord_id>' ORDER BY created_at DESC LIMIT 1;"
```

Expected: `custom_drink_order` with LLM-validated drink details

### Scenario 5: Lookup Table Validation
**Purpose**: Test price extraction from YAML configuration

**Test Messages**:
- `I'll have a whiskey` → Expected price: 5 coins
- `Give me a beer` → Expected price: 4 coins
- `Can I get some wine?` → Expected price: 6 coins
- `Rum please` → Expected price: 5 coins
- `Vodka` → Expected price: 5 coins

**Validation**: Check context_data.price in database
```bash
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
  "SELECT context_data->>'drink_name', context_data->>'price' FROM role_transactions WHERE user_id = '<your_discord_id>' ORDER BY created_at DESC LIMIT 5;"
```

## Log Monitoring

### Real-time Workflow Logs
```bash
docker logs whisperengine-dotty-bot -f | grep -E "(WORKFLOW|TRANSACTION|🎯)"
```

### Key Log Patterns

**Successful Workflow Detection**:
```
🎯 WORKFLOW: Detected intent - workflow: drink_order, confidence: 0.95
🎯 WORKFLOW: Extracted context: {'drink_name': 'whiskey', 'price': 5}
🎯 WORKFLOW: Created new transaction tx_abc123
```

**Prompt Injection**:
```
🎯 WORKFLOW: Injected transaction context into character prompt (150 chars)
```

**State Transition**:
```
🎯 WORKFLOW: Updated transaction tx_abc123 from pending → completed
```

**LLM Fallback**:
```
🎯 WORKFLOW: Pattern matching failed, using LLM validation
🎯 WORKFLOW: LLM validated custom drink request
```

## Database Queries

### View All Transactions for User
```bash
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
  "SELECT transaction_id, workflow_name, state, context_data, created_at 
   FROM role_transactions 
   WHERE user_id = '<your_discord_id>' 
   ORDER BY created_at DESC 
   LIMIT 10;"
```

### View Pending Transactions
```bash
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
  "SELECT transaction_id, workflow_name, context_data 
   FROM role_transactions 
   WHERE state = 'pending' AND bot_name = 'dotty';"
```

### View Completed Transactions (Last 24h)
```bash
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
  "SELECT workflow_name, COUNT(*), AVG((context_data->>'price')::int) as avg_price
   FROM role_transactions 
   WHERE state = 'completed' 
     AND bot_name = 'dotty' 
     AND created_at > NOW() - INTERVAL '24 hours'
   GROUP BY workflow_name;"
```

## Performance Validation

### Expected Response Times

**Declarative Path** (standard drinks):
- Pattern matching: ~1ms
- Context extraction: ~2ms
- Transaction creation: ~3ms
- **Total**: ~6ms

**LLM Fallback** (custom drinks):
- Pattern matching: ~1ms (fails)
- LLM validation: ~500-2000ms
- Context extraction: ~5ms
- Transaction creation: ~3ms
- **Total**: ~500-2000ms

### Measure Actual Performance
```bash
# Enable debug logging
docker exec -it whisperengine-dotty-bot bash
export LOG_LEVEL=DEBUG
# Restart bot to apply

# Monitor timing logs
docker logs whisperengine-dotty-bot -f | grep -E "(WORKFLOW.*ms|TIMING)"
```

## Troubleshooting

### Issue: Workflow Not Detected
**Symptoms**: Bot responds but no transaction created

**Check**:
1. Workflow manager initialized?
   ```bash
   docker logs whisperengine-dotty-bot | grep "Loaded.*workflows"
   ```

2. Pattern matching working?
   ```bash
   docker logs whisperengine-dotty-bot --tail 100 | grep "detect_intent"
   ```

3. CDL configuration correct?
   ```bash
   # Check dotty.json has transaction_config
   cat characters/examples/dotty.json | jq '.character.transaction_config'
   ```

### Issue: Transaction Created but LLM Unaware
**Symptoms**: Transaction in DB but Dotty doesn't mention price/order

**Check**:
1. Prompt injection working?
   ```bash
   docker logs whisperengine-dotty-bot --tail 100 | grep "Injected transaction context"
   ```

2. Metadata pass-through?
   ```bash
   docker logs whisperengine-dotty-bot --tail 100 | grep "workflow_prompt_injection"
   ```

3. MessageProcessor receiving metadata?
   ```bash
   docker logs whisperengine-dotty-bot --tail 100 | grep "ACTIVE TRANSACTION CONTEXT"
   ```

### Issue: State Transitions Not Working
**Symptoms**: Transaction stays in pending state after payment

**Check**:
1. Payment patterns matching?
   ```bash
   docker logs whisperengine-dotty-bot --tail 100 | grep "state_transition"
   ```

2. Transaction ID resolution?
   ```bash
   # Check last pending transaction exists
   docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c \
     "SELECT transaction_id, state FROM role_transactions WHERE state = 'pending' ORDER BY created_at DESC LIMIT 5;"
   ```

### Issue: LLM Fallback Not Triggering
**Symptoms**: Custom drink requests not creating transactions

**Check**:
1. LLM client available?
   ```bash
   docker logs whisperengine-dotty-bot | grep "LLM.*initialized"
   ```

2. Workflow file has requires_llm_validation?
   ```bash
   cat characters/workflows/dotty_bartender.yaml | grep "requires_llm_validation"
   ```

## Success Criteria

### ✅ Basic Integration
- [ ] Dotty bot starts without errors
- [ ] Workflow manager loads 3 workflows
- [ ] Pattern matching detects drink orders
- [ ] Transactions created in PostgreSQL

### ✅ End-to-End Flow
- [ ] Order message creates pending transaction
- [ ] LLM response mentions price
- [ ] Payment message completes transaction
- [ ] Cancellation message marks transaction cancelled

### ✅ Performance
- [ ] Standard orders respond in <100ms total
- [ ] Custom requests use LLM validation
- [ ] 90%+ requests use declarative path
- [ ] Average response time <50ms

### ✅ Character Consistency
- [ ] Dotty maintains personality in responses
- [ ] Transaction acknowledgments feel natural
- [ ] Price mentions integrated into dialogue
- [ ] No "robotic" transaction confirmations

## Next Steps After Validation

### Immediate
1. Fix any issues discovered in testing
2. Add guild message handler integration
3. Implement open_tab workflow

### Short-term
1. Add more drink types to menu
2. Create workflow analytics dashboard
3. Add error recovery patterns

### Long-term
1. Expand to other characters (Elena, Marcus)
2. Build workflow creation UI
3. Implement A/B testing framework

---

**Last Updated**: 2025-01-20

**Status**: Ready for testing

**Contact**: Run tests and report any issues
