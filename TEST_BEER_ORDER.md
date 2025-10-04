# Beer Order Test - Hybrid Workflow System

## Test Scenario: Beer Order (Declarative Path)

**Expected Flow:**
1. User sends: "I'll have a beer"
2. WorkflowManager detects intent: drink_order
3. Pattern matches: "i'll have (a |an )?(.*)" → captures "beer"
4. Context extracted: {drink_name: "beer", price: 4}
5. Transaction stored in database with state: "pending"
6. Prompt injected with transaction context
7. Dotty responds with transaction-aware message

**Test Instructions:**
1. Send DM to Dotty: "I'll have a beer"
2. Monitor logs for workflow detection
3. Check database for transaction creation
4. Validate response includes transaction awareness

**Expected Log Output:**
```
🎯 Workflow detection: drink_order (confidence: 0.95)
💾 Created transaction: tx_[uuid] for beer order
📋 Injected transaction context into prompt
```

**Expected Response:**
- Dotty should mention the beer
- Should include mystical bartender personality
- May reference the transaction/order state

**Database Validation:**
Check for new record in role_transactions with:
- transaction_type: "drink_order"
- context: {"drink_name": "beer", "price": 4}
- state: "pending"

## Ready to Test!

Send the message and we'll validate the ~6ms declarative path is working.