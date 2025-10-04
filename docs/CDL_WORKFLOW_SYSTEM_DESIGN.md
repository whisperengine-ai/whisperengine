# CDL-Based Workflow System Design

## Overview

WhisperEngine needs a **declarative workflow system** that:
1. Lives in CDL character definitions (JSON)
2. Supports transactional roleplay (bartender, shop, quest)
3. Follows industry best practices for conversational AI (not gaming FSMs)
4. LLM-friendly (AI drives conversation, workflows provide guardrails)

## Industry Best Practices Research

### Conversational AI vs Gaming NPCs

**Gaming NPCs** (Behavior Trees, FSMs, GOAP):
- ❌ Rigid state machines
- ❌ Predefined dialog trees
- ❌ Explicit state transitions
- ✅ Good for: Deterministic game logic, combat AI, pathfinding

**Conversational AI** (Character.AI, Replika, Inworld):
- ✅ LLM-driven natural responses
- ✅ Flexible intent recognition
- ✅ Personality-first approach
- ✅ Context injection over state machines

### Modern Conversational AI Workflows

**1. Rasa Framework** (Industry Standard):
```yaml
# Declarative story-based workflows
stories:
- story: order drink
  steps:
  - intent: order_drink
  - action: create_drink_order
  - intent: provide_payment
  - action: complete_drink_order
  - action: utter_serve_drink
```

**Pros**: Flexible, intent-driven, NLU integrated  
**Cons**: Separate engine, not LLM-first

**2. LangChain Agents** (LLM-Native):
```python
# Tool-based workflows
tools = [
    Tool(name="create_order", func=create_order),
    Tool(name="process_payment", func=process_payment),
]
agent = initialize_agent(tools, llm, agent="chat-conversational-react-description")
```

**Pros**: LLM-first, flexible tool calling  
**Cons**: Complex setup, requires function calling API

**3. Microsoft Bot Framework** (Enterprise):
```yaml
# Dialog-based workflows
dialogs:
  - id: drink_order
    steps:
      - prompt: "What would you like to drink?"
      - action: store_drink_choice
      - prompt: "That'll be {price} coins"
      - action: await_payment
```

**Pros**: Well-documented, scalable  
**Cons**: Heavy infrastructure, overkill for roleplay

**4. Character.AI Approach** (Pure LLM):
```json
{
  "definition": "You are a bartender. Remember drink orders and payment status.",
  "example_dialogs": [
    {"user": "I'll have a whiskey", "bot": "One whiskey, that'll be 5 coins"},
    {"user": "Here you go", "bot": "Thanks! *serves whiskey*"}
  ]
}
```

**Pros**: Simple, LLM handles everything  
**Cons**: No guaranteed state consistency

---

## Recommended: CDL Workflow Definitions

### Design Philosophy

**LLM-Centric + Declarative Guardrails**:
- ✅ LLM drives conversation naturally (personality, tone, creativity)
- ✅ Workflows provide transaction **structure** (not dialog control)
- ✅ Declarative intent patterns (regex, keywords, LLM classification)
- ✅ State tracking in PostgreSQL (persistence)
- ✅ Character-specific workflows in CDL (bartender vs shop vs quest)

### CDL Workflow Schema

```json
{
  "identity": {
    "name": "Dotty",
    "occupation": "AI Bartender at The Lim"
  },
  "workflows": {
    "drink_order": {
      "enabled": true,
      "transaction_type": "drink_order",
      "description": "Handle drink orders with payment tracking",
      "states": [
        {
          "name": "pending",
          "triggers": {
            "intent_patterns": [
              "\\b(I'll have|give me|order|want) a? (?<drink>\\w+)",
              "\\b(?<drink>whiskey|beer|wine|cocktail)\\b"
            ],
            "keywords": ["drink", "order", "have", "want"],
            "llm_classification": true
          },
          "actions": {
            "create_transaction": {
              "context_fields": ["drink", "price", "quantity"],
              "price_lookup": {
                "whiskey": 5,
                "beer": 3,
                "wine": 4,
                "cocktail": 6
              }
            },
            "prompt_injection": "User just ordered {context.drink}. Confirm order and state price: {context.price} coins."
          },
          "next_state": "awaiting_payment"
        },
        {
          "name": "awaiting_payment",
          "triggers": {
            "intent_patterns": [
              "\\b(here you go|here'?s? the|take this|here'?s? payment)\\b",
              "\\b(pay|paying|payment)\\b"
            ],
            "keywords": ["here", "payment", "pay", "take"],
            "llm_classification": true
          },
          "actions": {
            "complete_transaction": {
              "context_updates": {"payment_received": true, "drink_served": true}
            },
            "prompt_injection": "User just paid for their {context.drink}. Serve the drink warmly."
          },
          "next_state": "completed"
        }
      ],
      "cancellation": {
        "triggers": {
          "intent_patterns": ["\\b(never mind|cancel|forget it|changed my mind)\\b"],
          "keywords": ["cancel", "nevermind", "forget"]
        },
        "prompt_injection": "User cancelled their drink order. Acknowledge casually."
      },
      "timeout": {
        "duration_minutes": 15,
        "action": "auto_cancel",
        "prompt_injection": "Previous drink order expired. User may re-order if interested."
      }
    },
    "tab_management": {
      "enabled": false,
      "description": "Track running tab across multiple orders"
    }
  }
}
```

### Workflow Execution Flow

```
1. User Message → Intent Detection (Regex + Keywords + Optional LLM)
2. If Match → Check Pending Transaction
3. If Pending → Inject Context into System Prompt
4. LLM Generates Response (Natural, Character-Driven)
5. After Response → Execute Workflow Actions (Create/Update/Complete Transaction)
6. Store Transaction State in PostgreSQL
```

---

## Implementation Architecture

### 1. Workflow Loader (CDL Integration)

**Location**: `src/roleplay/workflow_manager.py`

```python
class WorkflowManager:
    def __init__(self, character_file: str, transaction_manager: TransactionManager):
        self.character_file = character_file
        self.transaction_manager = transaction_manager
        self.workflows = self._load_workflows_from_cdl()
    
    def _load_workflows_from_cdl(self) -> Dict[str, Workflow]:
        """Load workflows from CDL character definition"""
        with open(self.character_file) as f:
            cdl_data = json.load(f)
        
        workflows = {}
        for workflow_name, workflow_def in cdl_data.get('workflows', {}).items():
            if workflow_def.get('enabled', False):
                workflows[workflow_name] = Workflow(workflow_name, workflow_def)
        
        return workflows
    
    async def detect_intent(self, message: str, user_id: str, bot_name: str) -> Optional[WorkflowTrigger]:
        """Detect if message triggers any workflow"""
        # Check for pending transactions first
        pending = await self.transaction_manager.check_pending_transaction(user_id, bot_name)
        
        if pending:
            # Check if message advances pending transaction
            workflow = self.workflows.get(pending.transaction_type)
            if workflow:
                trigger = workflow.detect_state_transition(message, pending.state)
                if trigger:
                    return trigger
        
        # Check if message initiates new workflow
        for workflow in self.workflows.values():
            trigger = workflow.detect_initiation(message)
            if trigger:
                return trigger
        
        return None
    
    async def execute_workflow_action(
        self, 
        trigger: WorkflowTrigger, 
        user_id: str, 
        bot_name: str,
        message: str
    ) -> Dict[str, Any]:
        """Execute workflow action (create/update/complete transaction)"""
        workflow = self.workflows[trigger.workflow_name]
        
        if trigger.action_type == "create_transaction":
            # Extract context from message using patterns
            context = workflow.extract_context(message, trigger.state)
            transaction_id = await self.transaction_manager.create_transaction(
                user_id=user_id,
                bot_name=bot_name,
                transaction_type=workflow.transaction_type,
                context=context,
                state=trigger.current_state
            )
            return {"transaction_id": transaction_id, "prompt_injection": trigger.prompt_injection}
        
        elif trigger.action_type == "update_transaction":
            pending = await self.transaction_manager.check_pending_transaction(user_id, bot_name)
            if pending:
                await self.transaction_manager.update_transaction_state(
                    pending.id,
                    trigger.next_state,
                    trigger.context_updates
                )
                return {"prompt_injection": trigger.prompt_injection}
        
        elif trigger.action_type == "complete_transaction":
            pending = await self.transaction_manager.check_pending_transaction(user_id, bot_name)
            if pending:
                await self.transaction_manager.complete_transaction(
                    pending.id,
                    trigger.context_updates
                )
                return {"prompt_injection": trigger.prompt_injection}
        
        return {}
```

### 2. Workflow Data Models

```python
@dataclass
class WorkflowTrigger:
    workflow_name: str
    action_type: str  # 'create', 'update', 'complete', 'cancel'
    current_state: str
    next_state: Optional[str]
    prompt_injection: str
    context_updates: Dict[str, Any]

@dataclass
class Workflow:
    name: str
    transaction_type: str
    states: List[WorkflowState]
    cancellation: Optional[CancellationRule]
    timeout: Optional[TimeoutRule]
    
    def detect_initiation(self, message: str) -> Optional[WorkflowTrigger]:
        """Check if message initiates this workflow"""
        initial_state = self.states[0]
        if initial_state.matches(message):
            return WorkflowTrigger(
                workflow_name=self.name,
                action_type="create_transaction",
                current_state=initial_state.name,
                next_state=initial_state.next_state,
                prompt_injection=initial_state.prompt_injection,
                context_updates={}
            )
        return None
    
    def detect_state_transition(self, message: str, current_state: str) -> Optional[WorkflowTrigger]:
        """Check if message triggers state transition"""
        for state in self.states:
            if state.name == current_state and state.matches(message):
                return WorkflowTrigger(
                    workflow_name=self.name,
                    action_type="update_transaction",
                    current_state=current_state,
                    next_state=state.next_state,
                    prompt_injection=state.prompt_injection,
                    context_updates=state.context_updates
                )
        return None
    
    def extract_context(self, message: str, state_name: str) -> Dict[str, Any]:
        """Extract workflow context from message"""
        state = next((s for s in self.states if s.name == state_name), None)
        if state and state.actions.get("create_transaction"):
            # Use regex named groups to extract fields
            for pattern in state.triggers["intent_patterns"]:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    context = match.groupdict()
                    # Add price lookup if configured
                    if "price_lookup" in state.actions["create_transaction"]:
                        drink = context.get("drink", "").lower()
                        context["price"] = state.actions["create_transaction"]["price_lookup"].get(drink, 5)
                    return context
        return {}
```

### 3. Message Handler Integration

**Location**: `src/handlers/events.py` (in `_build_conversation_context`)

```python
# After loading memories, before building system prompt:

# 🎭 WORKFLOW INJECTION: Check for roleplay transactions
workflow_context = None
if hasattr(self, 'workflow_manager') and self.workflow_manager:
    # Detect if message triggers workflow
    trigger = await self.workflow_manager.detect_intent(
        message=content,
        user_id=user_id,
        bot_name=get_normalized_bot_name_from_env()
    )
    
    if trigger:
        # Execute workflow action (create/update/complete transaction)
        result = await self.workflow_manager.execute_workflow_action(
            trigger=trigger,
            user_id=user_id,
            bot_name=get_normalized_bot_name_from_env(),
            message=content
        )
        
        workflow_context = result.get("prompt_injection", "")
        logger.info(f"🎭 Workflow triggered: {trigger.workflow_name} → {trigger.action_type}")

# Inject workflow context into system prompt
if workflow_context:
    system_prompt_content += f"\n\n⚠️ TRANSACTION CONTEXT:\n{workflow_context}"
```

---

## Benefits of CDL Workflow System

### vs Behavior Trees/FSMs:
- ✅ **LLM-first**: AI drives natural conversation, not rigid state machines
- ✅ **Flexible**: Intent patterns (regex + keywords + LLM) handle natural language
- ✅ **Declarative**: Workflows defined in JSON, not hardcoded Python logic
- ✅ **Character-specific**: Each bot defines its own workflows in CDL

### vs Pure LLM (Character.AI):
- ✅ **Transaction consistency**: PostgreSQL ensures state persistence
- ✅ **Guaranteed completion**: Workflow ensures order → payment → serve
- ✅ **Timeout handling**: Auto-cancel stale transactions
- ✅ **Context injection**: LLM always aware of pending transactions

### vs Rasa/Microsoft Bot Framework:
- ✅ **Simpler**: No separate NLU engine, no heavy infrastructure
- ✅ **Integrated**: Works with existing CDL + Qdrant + PostgreSQL
- ✅ **Personality-driven**: Character personality + workflows coexist
- ✅ **Lightweight**: Single JSON file per character

---

## Example: Dotty Bartender Workflow

**CDL File**: `characters/examples/dotty.json`

```json
{
  "identity": {
    "name": "Dotty",
    "occupation": "AI Bartender at The Lim",
    "personality": "Warm, witty British bartender"
  },
  "workflows": {
    "drink_order": {
      "enabled": true,
      "transaction_type": "drink_order",
      "states": [
        {
          "name": "pending",
          "triggers": {
            "intent_patterns": ["\\b(I'll have|give me|order) (?<drink>\\w+)"],
            "keywords": ["drink", "order", "have"]
          },
          "actions": {
            "create_transaction": {
              "context_fields": ["drink", "price"],
              "price_lookup": {"whiskey": 5, "beer": 3}
            },
            "prompt_injection": "User ordered {context.drink}. Confirm and state price."
          },
          "next_state": "awaiting_payment"
        },
        {
          "name": "awaiting_payment",
          "triggers": {
            "intent_patterns": ["\\bhere you go\\b", "\\bpay(ment)?\\b"]
          },
          "actions": {
            "complete_transaction": {},
            "prompt_injection": "User paid. Serve {context.drink} warmly."
          },
          "next_state": "completed"
        }
      ]
    }
  }
}
```

**Conversation Flow**:
```
User: "I'll have a whiskey"
→ Detect: drink_order workflow, pending state
→ Create transaction: {drink: "whiskey", price: 5}
→ Inject: "User ordered whiskey. Confirm and state price."
→ LLM: "One whiskey coming up, love! That'll be 5 coins." (Natural Dotty personality)

User: "Here you go"
→ Detect: drink_order workflow, awaiting_payment state
→ Complete transaction
→ Inject: "User paid. Serve whiskey warmly."
→ LLM: "*slides whiskey across bar* Enjoy, mate!" (Natural Dotty personality)
```

---

## Implementation Phases

### Phase 1: Core Workflow System ✅
- [x] TransactionManager (PostgreSQL state tracking)
- [x] CDL workflow schema design
- [ ] WorkflowManager class
- [ ] Intent detection (regex + keywords)
- [ ] Prompt injection integration

### Phase 2: Advanced Intent Recognition
- [ ] LLM-based intent classification (optional fallback)
- [ ] Named entity extraction (drink names, prices)
- [ ] Context variable interpolation

### Phase 3: Multi-Step Workflows
- [ ] Quest workflows (multi-state progression)
- [ ] Shop inventory management
- [ ] Appointment scheduling

### Phase 4: Workflow Analytics
- [ ] Transaction success rates
- [ ] Workflow completion metrics
- [ ] User behavior patterns

---

## Testing Plan

**Test 1: Dotty Drink Order**
```python
# Test complete workflow
user_message_1 = "I'll have a whiskey"
# Expected: Create transaction, prompt injection
user_message_2 = "Here you go"
# Expected: Complete transaction, serve drink
```

**Test 2: Cancellation**
```python
user_message_1 = "I'll have a beer"
user_message_2 = "Actually, never mind"
# Expected: Cancel transaction
```

**Test 3: Timeout**
```python
user_message_1 = "I'll have wine"
# Wait 16 minutes...
# Expected: Auto-cancel transaction
```

---

## Next Steps

1. **Implement WorkflowManager** (`src/roleplay/workflow_manager.py`)
2. **Add workflow loader to bot initialization** (`src/core/bot.py`)
3. **Integrate intent detection in events.py** (before LLM call)
4. **Test with Dotty bartender** (Discord messages)
5. **Document workflow authoring guide** for character creators

---

## Conclusion

**CDL Workflow System** combines the best of both worlds:
- ✅ **LLM natural conversation** (personality, creativity, flexibility)
- ✅ **Declarative transaction structure** (consistency, persistence, timeout handling)
- ✅ **Character-specific workflows** (bartender, shop, quest defined in CDL)
- ✅ **Industry best practices** (conversational AI, not gaming FSMs)

**Simple, powerful, LLM-first! 🚀**
