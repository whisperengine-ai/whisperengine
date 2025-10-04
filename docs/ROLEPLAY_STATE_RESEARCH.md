# Roleplay State Management Research

## The Problem

**Dotty the AI Bartender** needs to handle stateful interactions:
- User: "I'll have a whiskey"
- Dotty: "One whiskey coming up! That'll be 5 coins"
- User: "Here you go" 
- Dotty: *Should remember the pending order and complete the transaction*

**Current System**: Qdrant conversation memory alone may not preserve transactional state reliably across message boundaries.

## What Game NPCs Use

### 1. **Behavior Trees** (Most Common)
Used by: Unreal Engine, Unity, Halo, The Sims

```
Root
├── Selector (Try in order until one succeeds)
│   ├── Sequence: Handle Active Order
│   │   ├── Check: Has pending order?
│   │   ├── Check: User provided payment?
│   │   └── Action: Complete transaction
│   ├── Sequence: Take New Order
│   │   ├── Check: User requested item?
│   │   ├── Action: Create pending order
│   │   └── Action: Request payment
│   └── Fallback: General conversation
```

**Pros**: 
- ✅ Simple tree structure
- ✅ Composable and reusable
- ✅ Easy to visualize

**Cons**:
- ❌ Rigid - not great for open-ended AI conversations
- ❌ Requires predefined decision paths
- ❌ Doesn't leverage LLM intelligence

### 2. **Finite State Machines (FSM)**
Used by: Elder Scrolls, Fallout, classic RPGs

```
States:
- IDLE → (order detected) → TAKING_ORDER
- TAKING_ORDER → (order confirmed) → AWAITING_PAYMENT  
- AWAITING_PAYMENT → (payment received) → SERVING_DRINK
- SERVING_DRINK → (drink served) → IDLE
```

**Pros**:
- ✅ Clear state transitions
- ✅ Easy to debug
- ✅ Predictable behavior

**Cons**:
- ❌ State explosion problem (N states × M triggers = N×M transitions)
- ❌ Doesn't handle natural language ambiguity
- ❌ Too rigid for AI personality-driven responses

### 3. **Goal-Oriented Action Planning (GOAP)**
Used by: F.E.A.R., Fallout 3, Shadow of Mordor

```
Goal: "Serve user a drink"
Available Actions:
- Take order (precondition: user wants drink, effect: order_placed=true)
- Request payment (precondition: order_placed=true, effect: payment_requested=true)
- Accept payment (precondition: payment_requested=true, effect: payment_received=true)
- Serve drink (precondition: payment_received=true, effect: goal_complete)

AI plans action sequence dynamically to reach goal
```

**Pros**:
- ✅ Flexible - AI plans actions dynamically
- ✅ Handles complex dependencies
- ✅ Emergent behavior

**Cons**:
- ❌ Complex to implement
- ❌ Overkill for simple interactions
- ❌ Requires careful action design

### 4. **Dialog Trees** (Classic)
Used by: Mass Effect, Witcher, old-school RPGs

```
Node 1: "What can I get you?"
├── Option A: "Whiskey" → Node 2
├── Option B: "Beer" → Node 3
└── Option C: "Nothing" → Exit

Node 2: "That'll be 5 coins"
├── Option A: "Here you go" → Serve drink
└── Option B: "Never mind" → Node 1
```

**Pros**:
- ✅ Total control over conversation flow
- ✅ Predictable outcomes
- ✅ Easy to write and test

**Cons**:
- ❌ **TERRIBLE for AI roleplay** - kills natural conversation
- ❌ Rigid branching doesn't leverage LLM capabilities
- ❌ User can't express things naturally

## Modern AI Character Systems

### Character.AI / Replika Approach
**No explicit state machines** - rely entirely on:
1. **LLM context window** (conversation history)
2. **Prompt engineering** ("You are a bartender who remembers orders")
3. **Implicit memory** (LLM infers state from conversation)

**Works for**: Casual conversation, emotional support, open-ended roleplay  
**Fails for**: Precise transactions, game mechanics, inventory tracking

### Inworld AI (Game NPCs)
Uses **Hybrid Approach**:
1. **LLM for natural conversation** (personality, emotions, dialogue)
2. **Goals & Triggers** (lightweight state tracking)
3. **Action callbacks** (trigger game code for mechanics)

```javascript
// Example: Inworld NPC bartender
character: {
  goals: [
    { id: "serve_drinks", priority: 8 },
    { id: "collect_payment", priority: 10 }
  ],
  triggers: [
    { pattern: /order|drink|whiskey/i, action: "take_order" },
    { pattern: /pay|coins|money/i, action: "process_payment" }
  ],
  state: {
    pending_order: null,
    awaiting_payment: false
  }
}
```

### AI Dungeon / NovelAI
**Pure LLM approach** with:
- **World Info** (persistent facts injected into context)
- **Memory pins** (important events kept in context)
- **No formal state machines**

**Problem**: Inconsistent with transactions (AI might forget you paid, or give you free items)

## Recommendation for WhisperEngine

### Option A: **Lightweight Transaction State (PostgreSQL)**
**Best for**: Transactional roleplay (bartender, shopkeeper, quest giver)

```sql
-- Simple transaction state table
CREATE TABLE roleplay_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    bot_name VARCHAR(50),
    transaction_type VARCHAR(50),  -- 'drink_order', 'quest', 'purchase'
    state VARCHAR(50),              -- 'pending', 'awaiting_payment', 'completed', 'cancelled'
    context JSONB,                  -- Flexible state data
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Example for Dotty:
{
  "transaction_type": "drink_order",
  "state": "awaiting_payment",
  "context": {
    "drink": "whiskey",
    "price": 5,
    "order_time": "2025-10-04T10:30:00Z"
  }
}
```

**Integration Pattern**:
```python
# src/roleplay/transaction_manager.py
class TransactionManager:
    async def check_pending_transaction(self, user_id: str, bot_name: str):
        """Check if user has any pending transactions"""
        # Query PostgreSQL for active transactions
        
    async def create_transaction(self, user_id: str, bot_name: str, 
                                  transaction_type: str, context: dict):
        """Create new transaction state"""
        
    async def update_transaction_state(self, transaction_id: int, 
                                        new_state: str, context: dict):
        """Update transaction state"""
        
    async def complete_transaction(self, transaction_id: int):
        """Mark transaction as completed"""
```

**Used in message processing**:
```python
# In events.py message handler:

# 1. Check for pending transactions BEFORE building prompt
pending_transaction = await transaction_manager.check_pending_transaction(user_id, bot_name)

# 2. Inject transaction context into system prompt
if pending_transaction:
    system_prompt += f"\n\nIMPORTANT CONTEXT: User has pending {pending_transaction['type']}. "
    system_prompt += f"Current state: {pending_transaction['state']}. "
    system_prompt += f"Details: {pending_transaction['context']}"

# 3. After LLM response, detect state changes via semantic analysis
if "here you go" in user_message.lower() and pending_transaction['state'] == 'awaiting_payment':
    await transaction_manager.update_transaction_state(
        pending_transaction['id'], 
        'completed',
        {'payment_received': True}
    )
```

**Pros**:
- ✅ Simple table structure (5 columns)
- ✅ Works with existing PostgreSQL
- ✅ Character-agnostic (any bot can use it)
- ✅ LLM still drives conversation naturally
- ✅ Persistent across container restarts
- ✅ Query with bot_name + user_id for isolation

**Cons**:
- Need to detect state transitions (can use LLM or semantic patterns)
- Adds DB queries per message (but only when transactions exist)

---

### Option B: **Graph-Based Interaction State**
**Best for**: Complex multi-step interactions, relationship-driven roleplay

```cypher
// PostgreSQL with graph queries (using recursive CTEs)
// Or use actual graph extensions like Apache AGE

// Example: Dotty bartender interactions
(User)-[:HAS_PENDING_ORDER {
  drink: "whiskey",
  price: 5,
  state: "awaiting_payment",
  created_at: timestamp
}]->(Dotty)

(User)-[:PAID_FOR]->(Order {drink: "whiskey", price: 5})
(Dotty)-[:SERVED]->(Order)
```

**Pros**:
- ✅ Natural relationship modeling
- ✅ Can track complex interaction chains
- ✅ Query relationship history easily

**Cons**:
- ❌ More complex queries
- ❌ Need graph query expertise
- ❌ PostgreSQL graph support is limited (need extensions)

---

### Option C: **Pure LLM Context (No State Tracking)**
**Best for**: Casual roleplay, non-transactional interactions

**Rely on**:
1. Qdrant conversation history (last 1 hour)
2. Strong CDL prompt engineering
3. LLM's ability to infer state from context

```python
# Just strengthen CDL prompts:
# characters/examples/dotty.json
{
  "personality": {
    "occupation": "AI Bartender at The Lim",
    "traits": {
      "transaction_memory": "CRITICAL: Always remember pending drink orders and whether payment was received. Track each order until completion."
    }
  }
}
```

**Pros**:
- ✅ Zero infrastructure changes
- ✅ Simplest approach
- ✅ Works "good enough" for casual roleplay

**Cons**:
- ❌ Not reliable for precise transactions
- ❌ Context window limits may cause forgetting
- ❌ Can't guarantee consistency

---

## Recommendation: **Option A (Lightweight Transaction State)**

**Why**:
1. ✅ **Simple**: Just 1 table, 5 columns
2. ✅ **Flexible**: JSONB context supports any transaction type
3. ✅ **Character-agnostic**: Works for Dotty (drinks), future quest NPCs, shops, etc.
4. ✅ **LLM-friendly**: Inject state into prompts, let AI respond naturally
5. ✅ **PostgreSQL**: You already have it running
6. ✅ **Persistent**: Survives container restarts
7. ✅ **Opt-in**: Only bots that need it (bartenders, shops) use it

**Implementation Phases**:

### Phase 1: Core Transaction Table
```sql
CREATE TABLE roleplay_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL DEFAULT 'pending',
    context JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    INDEX idx_user_bot_state (user_id, bot_name, state)
);
```

### Phase 2: TransactionManager Class
```python
# src/roleplay/transaction_manager.py
async def check_pending(user_id, bot_name) -> Optional[Dict]
async def create(user_id, bot_name, type, context) -> int
async def update_state(transaction_id, new_state, context) -> bool
async def complete(transaction_id) -> bool
```

### Phase 3: Integration in Message Handler
```python
# Before LLM call: Check pending transactions
# Inject into system prompt if found
# After LLM response: Detect state changes
```

### Phase 4: CDL Integration
```json
// characters/examples/dotty.json
{
  "roleplay_capabilities": {
    "transaction_support": true,
    "transaction_types": ["drink_order", "tab_management"],
    "state_awareness": "high"
  }
}
```

---

## State Transition Detection

**How to detect when to update transaction state?**

### Approach 1: **Semantic Pattern Matching** (Simple)
```python
# After user message received
if pending_transaction and pending_transaction['state'] == 'awaiting_payment':
    payment_patterns = [
        r'\bhere you go\b',
        r'\bhere\'?s? the (money|coins|payment)\b',
        r'\bpay(ing)?\b',
        r'\btake (this|it)\b'
    ]
    if any(re.search(p, user_message.lower()) for p in payment_patterns):
        await transaction_manager.complete(pending_transaction['id'])
```

### Approach 2: **LLM Classification** (Smarter)
```python
# Ask LLM to classify user intent
classification_prompt = f"""User said: "{user_message}"
Pending transaction: {pending_transaction}

Did the user:
A) Provide payment
B) Cancel the order
C) Ask a question
D) Something else

Answer with just the letter."""

intent = await llm_client.classify(classification_prompt)
if intent == 'A':
    await transaction_manager.complete(pending_transaction['id'])
```

### Approach 3: **Function Calling** (Most Reliable)
```python
# Use OpenAI function calling / tool use
tools = [
    {
        "type": "function",
        "function": {
            "name": "complete_drink_order",
            "description": "Call when user has paid for their drink",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

# LLM decides when to call function
# Guarantees state updates happen at right time
```

---

## Alternative: CDL-Driven State Templates

**What if transaction types are defined in CDL?**

```json
// characters/examples/dotty.json
{
  "roleplay_transactions": {
    "drink_order": {
      "states": ["pending", "awaiting_payment", "completed", "cancelled"],
      "transitions": {
        "pending → awaiting_payment": "User confirmed drink choice",
        "awaiting_payment → completed": "User provided payment",
        "* → cancelled": "User cancelled or changed mind"
      },
      "context_schema": {
        "drink": "string",
        "price": "number",
        "special_requests": "string?"
      }
    }
  }
}
```

This makes transactions **character-aware** and **CDL-driven**.

---

## Conclusion

**For Dotty and future roleplay bots, use Option A: Lightweight PostgreSQL transaction state**

**Benefits**:
- 🎯 Precise transaction tracking
- 🤖 LLM still drives natural conversation
- 🏗️ Simple infrastructure (1 table)
- 🔄 Character-agnostic design
- 📊 Query transaction history easily
- ⚡ Only active when needed

**Next Steps**:
1. Create `roleplay_transactions` table in PostgreSQL
2. Implement `TransactionManager` class
3. Integrate in message handler (check pending, inject context, detect completion)
4. Test with Dotty bartender scenario
5. Extend to other transactional roleplay (shops, quests, etc.)

**Don't use**: Heavy FSMs, dialog trees, or behavior trees - they kill natural AI conversation. Keep LLM in control of personality, just give it transaction state as context.
