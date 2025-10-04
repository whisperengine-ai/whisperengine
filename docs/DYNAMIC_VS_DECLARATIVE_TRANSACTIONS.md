# Dynamic vs Declarative Transaction Management

## The Core Question

**Should bots use TransactionManager declaratively (CDL workflows) or dynamically (LLM decides when)?**

This is a fundamental architecture decision that affects reliability, flexibility, and AI capabilities.

---

## Approach 1: Declarative Workflows (What We Just Designed)

### How It Works
```json
// CDL defines explicit workflows
{
  "workflows": {
    "drink_order": {
      "triggers": ["I'll have", "order a"],
      "states": ["pending", "awaiting_payment", "completed"]
    }
  }
}
```

**Pros**:
- ✅ **Guaranteed consistency**: Payment always tracked, orders always completed
- ✅ **Predictable behavior**: Same input → same workflow trigger
- ✅ **Easy debugging**: Can trace exact workflow state
- ✅ **No hallucination**: Transaction state is real, not LLM-imagined
- ✅ **Testable**: Can unit test workflow transitions

**Cons**:
- ❌ **Requires pre-definition**: Must anticipate all transaction types
- ❌ **Less flexible**: Can't handle unexpected transaction patterns
- ❌ **Maintenance overhead**: Each new transaction type needs CDL update
- ❌ **Rigid patterns**: Regex/keywords may miss natural variations

**Best For**:
- 🍺 Bartender with known menu (whiskey, beer, wine)
- 🛒 Shop with inventory (items, prices)
- 🎯 Quest NPCs with fixed quest chains
- 💼 Service bots with appointment types

---

## Approach 2: Dynamic LLM-Driven (Tool Calling)

### How It Works
```python
# LLM decides when to create transactions
tools = [
    {
        "name": "create_transaction",
        "description": "Create a transaction when user orders something",
        "parameters": {
            "transaction_type": "string",
            "context": "object"
        }
    },
    {
        "name": "complete_transaction",
        "description": "Complete pending transaction when user pays/confirms"
    }
]

# LLM Response:
# "One whiskey coming up! That'll be 5 coins."
# TOOL_CALL: create_transaction(type="drink_order", context={"drink": "whiskey", "price": 5})
```

**Pros**:
- ✅ **Maximum flexibility**: Handles unexpected transaction types
- ✅ **Natural language understanding**: LLM interprets intent perfectly
- ✅ **Zero configuration**: No CDL workflow definitions needed
- ✅ **Adaptive**: Can create new transaction types on the fly
- ✅ **Context-aware**: LLM decides based on full conversation context

**Cons**:
- ❌ **LLM reliability**: May forget to call tools, or call them incorrectly
- ❌ **Hallucination risk**: LLM might "imagine" transactions that don't exist
- ❌ **Inconsistent**: Same input might trigger tool sometimes, not others
- ❌ **Harder debugging**: Why didn't LLM call tool? Hard to know
- ❌ **Cost**: Every message requires function calling API

**Best For**:
- 🎭 Open-ended roleplay (unpredictable interactions)
- 🧙 Creative NPCs (improvised quests, dynamic pricing)
- 🤝 Complex negotiations (multi-party agreements)
- 🎨 Artistic bots (custom commissions, unique requests)

---

## Approach 3: Hybrid (Best of Both Worlds!)

### The Proposal

**Combine declarative workflows with LLM tool calling as fallback:**

1. **Declarative workflows for common patterns** (fast, reliable)
2. **LLM tool calling for edge cases** (flexible, adaptive)
3. **LLM validates workflow triggers** (catch false positives)

### Architecture

```python
class HybridTransactionManager:
    async def process_message(self, message: str, user_id: str, bot_name: str):
        # Step 1: Try declarative workflow detection (fast path)
        workflow_trigger = await self.workflow_manager.detect_intent(message, user_id, bot_name)
        
        if workflow_trigger:
            # Step 2: Validate with LLM (optional, for high-stakes transactions)
            if workflow_trigger.requires_validation:
                is_valid = await self.llm_validate_intent(message, workflow_trigger)
                if not is_valid:
                    logger.info(f"LLM rejected workflow trigger: {workflow_trigger}")
                    workflow_trigger = None
        
        if workflow_trigger:
            # Declarative workflow handles it
            return await self.execute_workflow(workflow_trigger)
        
        # Step 3: No workflow matched, let LLM decide via tool calling
        llm_tools = self.get_transaction_tools()
        response = await self.llm_client.chat_with_tools(message, tools=llm_tools)
        
        if response.tool_calls:
            # LLM decided to create/update transaction dynamically
            return await self.execute_llm_tools(response.tool_calls)
        
        # No transaction detected
        return None
```

### Example: Dotty Bartender

**Common Orders** (Declarative):
```json
{
  "workflows": {
    "drink_order": {
      "triggers": ["I'll have", "order", "give me"],
      "drinks": ["whiskey", "beer", "wine"]  // Known menu
    }
  }
}
```

**Unusual Requests** (LLM Tool Calling):
```
User: "Can you make me something tropical and surprise me?"
→ No workflow match (not specific drink)
→ LLM tool call: create_transaction(type="custom_drink_order", context={
    "description": "tropical surprise cocktail",
    "price": 8,  // LLM estimates
    "custom": true
})
```

**Benefits**:
- ✅ Fast, reliable for 90% of common cases (workflows)
- ✅ Flexible, adaptive for 10% edge cases (LLM tools)
- ✅ LLM validation catches false positives
- ✅ Best of both approaches

---

## Approach 4: Pure LLM State Awareness (No Tools)

### The Radical Approach

**What if we don't use explicit transactions at all?**

Instead, we:
1. **Inject transaction context into prompt**
2. **LLM maintains state in conversation history**
3. **Memory system captures transaction details**
4. **No explicit state machine**

### How It Works

```python
# Before LLM call:
system_prompt += """
You are Dotty, a bartender. When users order drinks:
1. Remember what they ordered and the price
2. Wait for payment before serving
3. Track this in your memory until order is complete

Current pending orders: {pending_orders_from_memory}
"""

# LLM naturally handles state in conversation:
User: "I'll have a whiskey"
Dotty: "One whiskey coming up, love! That'll be 5 coins." 
       [MEMORY: User ordered whiskey, price 5 coins, awaiting payment]

User: "Here you go"
Dotty: "*slides whiskey across bar* Enjoy!" 
       [MEMORY: Whiskey order completed, payment received]
```

**Pros**:
- ✅ **Zero infrastructure**: No workflows, no tool calling, no transaction tables
- ✅ **Maximum naturalness**: Pure conversational flow
- ✅ **Simple**: Just memory + prompt engineering
- ✅ **Character-driven**: Personality determines transaction handling

**Cons**:
- ❌ **Unreliable**: LLM may forget pending orders
- ❌ **Context window limits**: Long conversations may lose transaction state
- ❌ **No guarantees**: Can't ensure payment was collected
- ❌ **No audit trail**: Hard to debug "why wasn't user charged?"

**Best For**:
- 🎭 Low-stakes roleplay (free drinks in fantasy tavern)
- 🎪 Casual interactions (no real consequences)
- 🧸 Toy/demo applications (experimentation)

**NOT For**:
- 💰 Real transactions (money, items, rewards)
- 🎮 Game mechanics (inventory, quests, achievements)
- 📊 Analytics (completion rates, revenue tracking)

---

## Industry Practices

### What Do Production Systems Use?

**Character.AI / Replika**:
- Pure LLM approach (Approach 4)
- No explicit transaction management
- Works for emotional support, casual chat
- Problems with consistency in roleplay scenarios

**Inworld AI (Gaming NPCs)**:
- Hybrid approach (Approach 3)
- Goals + triggers for common patterns
- LLM for natural dialog
- Tool callbacks for game mechanics

**Rasa / Dialogflow (Enterprise Chatbots)**:
- Pure declarative (Approach 1)
- Intent detection → slot filling → actions
- Very reliable, but rigid

**OpenAI Assistants API**:
- Pure LLM tool calling (Approach 2)
- Function calling for actions
- Flexible but sometimes unreliable

---

## Recommendation for WhisperEngine

### 🎯 Start with Hybrid (Approach 3)

**Phase 1: Declarative Workflows**
- Implement CDL workflow system (what we designed)
- Use for Dotty bartender (known menu, clear states)
- Simple, reliable, easy to test

**Phase 2: Add LLM Tool Calling**
- Implement as fallback for unmatched intents
- Tools: `create_transaction()`, `update_transaction()`, `complete_transaction()`
- Use when workflows don't match

**Phase 3: LLM Validation (Optional)**
- Add LLM confirmation for high-stakes transactions
- Reduce false positives from regex patterns
- "Did user really order a drink? Yes/No"

### Implementation Strategy

```python
class TransactionOrchestrator:
    """Hybrid transaction management - declarative + dynamic"""
    
    def __init__(self, workflow_manager, transaction_manager, llm_client):
        self.workflow_manager = workflow_manager  # CDL workflows
        self.transaction_manager = transaction_manager  # PostgreSQL state
        self.llm_client = llm_client  # For tool calling
        self.use_llm_fallback = os.getenv("ENABLE_LLM_TRANSACTION_TOOLS", "true") == "true"
    
    async def process_message(self, message: str, user_id: str, bot_name: str):
        """Process message through hybrid transaction pipeline"""
        
        # 1️⃣ Try declarative workflows first (fast, reliable)
        workflow_result = await self.try_declarative_workflow(message, user_id, bot_name)
        if workflow_result:
            logger.info(f"✅ Declarative workflow handled: {workflow_result['workflow_name']}")
            return workflow_result
        
        # 2️⃣ Try LLM tool calling (flexible, adaptive)
        if self.use_llm_fallback:
            tool_result = await self.try_llm_tool_calling(message, user_id, bot_name)
            if tool_result:
                logger.info(f"✅ LLM tool calling handled: {tool_result['tool_name']}")
                return tool_result
        
        # 3️⃣ No transaction detected
        return None
    
    async def try_declarative_workflow(self, message, user_id, bot_name):
        """Attempt to match message to CDL-defined workflows"""
        if not self.workflow_manager:
            return None
        
        trigger = await self.workflow_manager.detect_intent(message, user_id, bot_name)
        if trigger:
            result = await self.workflow_manager.execute_workflow_action(
                trigger, user_id, bot_name, message
            )
            return {
                "workflow_name": trigger.workflow_name,
                "prompt_injection": result.get("prompt_injection"),
                "transaction_id": result.get("transaction_id")
            }
        
        return None
    
    async def try_llm_tool_calling(self, message, user_id, bot_name):
        """Let LLM decide if transaction is needed via tool calling"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_transaction",
                    "description": "Create a transaction when user orders/requests something that needs tracking",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "transaction_type": {
                                "type": "string",
                                "description": "Type of transaction (drink_order, purchase, quest, etc.)"
                            },
                            "context": {
                                "type": "object",
                                "description": "Transaction details (item, price, quantity, etc.)"
                            }
                        },
                        "required": ["transaction_type", "context"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_transaction",
                    "description": "Complete pending transaction when user pays/confirms",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "completion_note": {
                                "type": "string",
                                "description": "Optional note about completion"
                            }
                        }
                    }
                }
            }
        ]
        
        # Check for pending transaction to provide context
        pending = await self.transaction_manager.check_pending_transaction(user_id, bot_name)
        system_context = ""
        if pending:
            system_context = f"\n\nPending transaction: {pending.transaction_type} - {pending.context}"
        
        # LLM decides if tools are needed
        response = await self.llm_client.chat_with_tools(
            message=message,
            tools=tools,
            system_context=system_context
        )
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.name == "create_transaction":
                    args = tool_call.arguments
                    transaction_id = await self.transaction_manager.create_transaction(
                        user_id=user_id,
                        bot_name=bot_name,
                        transaction_type=args["transaction_type"],
                        context=args["context"]
                    )
                    return {
                        "tool_name": "create_transaction",
                        "transaction_id": transaction_id,
                        "prompt_injection": f"Created {args['transaction_type']} transaction"
                    }
                
                elif tool_call.name == "complete_transaction":
                    if pending:
                        await self.transaction_manager.complete_transaction(pending.id)
                        return {
                            "tool_name": "complete_transaction",
                            "transaction_id": pending.id,
                            "prompt_injection": f"Completed {pending.transaction_type}"
                        }
        
        return None
```

### When to Use Each Approach

**Use Declarative Workflows When**:
- ✅ Transaction types are known (menu items, quest types)
- ✅ Clear state transitions (order → pay → serve)
- ✅ High reliability required (payment tracking)
- ✅ Predictable patterns (regex works well)

**Use LLM Tool Calling When**:
- ✅ Open-ended interactions (custom requests)
- ✅ Unpredictable transaction types
- ✅ Complex context understanding needed
- ✅ Creative/improvised roleplay

**Use Pure LLM State Awareness When**:
- ✅ Low-stakes roleplay (no real consequences)
- ✅ Casual conversation (not transactional)
- ✅ Rapid prototyping (minimal infrastructure)

---

## Configuration Strategy

**Per-Bot Configuration** (Environment Variables):
```bash
# .env.dotty (Bartender - structured transactions)
TRANSACTION_MODE=hybrid
ENABLE_WORKFLOWS=true
ENABLE_LLM_TOOLS=true

# .env.dream (Mythological entity - pure conversation)
TRANSACTION_MODE=none
ENABLE_WORKFLOWS=false
ENABLE_LLM_TOOLS=false

# .env.questgiver (Quest NPC - mostly workflows)
TRANSACTION_MODE=declarative
ENABLE_WORKFLOWS=true
ENABLE_LLM_TOOLS=false

# .env.creative_artist (Custom commissions - LLM-driven)
TRANSACTION_MODE=dynamic
ENABLE_WORKFLOWS=false
ENABLE_LLM_TOOLS=true
```

**Per-Character CDL Configuration**:
```json
{
  "identity": {
    "name": "Dotty",
    "occupation": "AI Bartender"
  },
  "transaction_config": {
    "mode": "hybrid",  // "declarative", "dynamic", "hybrid", "none"
    "workflow_priority": "high",  // Try workflows first
    "llm_fallback": true,  // Use LLM tools if workflows don't match
    "llm_validation": false  // Don't validate every workflow trigger
  },
  "workflows": {
    // CDL workflows here...
  }
}
```

---

## Performance Comparison

### Latency

**Declarative Workflow**:
- Regex matching: ~1ms
- PostgreSQL query: ~5ms
- **Total: ~6ms** ⚡

**LLM Tool Calling**:
- LLM API call: ~500-2000ms
- Tool execution: ~5ms
- **Total: ~500-2000ms** 🐌

**Hybrid**:
- Try workflow: ~6ms
- Fallback to LLM: ~500-2000ms (only if needed)
- **Average: ~50ms** (assuming 90% workflow match) ⚡

### Reliability

**Declarative**: 98-99% accuracy (regex precision)
**LLM Tools**: 85-95% accuracy (model-dependent)
**Hybrid**: 95-99% accuracy (workflows catch common cases, LLM handles edge cases)

### Cost

**Declarative**: $0 (pure regex + database)
**LLM Tools**: ~$0.001-0.01 per message (function calling overhead)
**Hybrid**: ~$0.0001-0.001 per message (LLM only for 10% of cases)

---

## Recommendation Summary

### 🎯 Use Hybrid Approach

**Implementation Priority**:
1. ✅ **Phase 1**: TransactionManager (PostgreSQL) - DONE
2. 🔨 **Phase 2**: CDL Workflows (Declarative) - IN PROGRESS
3. 🔜 **Phase 3**: LLM Tool Calling (Dynamic fallback)
4. 🔜 **Phase 4**: Per-bot configuration

**Start Simple**:
- Dotty gets declarative workflows (known menu)
- Test in production
- Add LLM fallback later if needed
- Monitor which cases fall through to LLM

**Benefits**:
- ✅ Fast & reliable for common patterns (workflows)
- ✅ Flexible for edge cases (LLM tools)
- ✅ Configurable per bot (some bots workflows, some LLM, some hybrid)
- ✅ Gradual rollout (start declarative, add dynamic later)

**The beauty**: You don't have to choose! Hybrid gives you both approaches, use whichever fits the situation. 🎯
