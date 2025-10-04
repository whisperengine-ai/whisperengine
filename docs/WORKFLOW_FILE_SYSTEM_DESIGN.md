# Workflow File System Design

## Architecture: Separate YAML Workflow Files

### Why Separate Files?

**Problems with Inline Workflows in CDL**:
- ❌ CDL JSON files getting huge (elena.json is already 1000+ lines)
- ❌ Workflow definitions are verbose (states, triggers, actions, prompts)
- ❌ Hard to maintain when mixed with personality data
- ❌ JSON is not human-friendly for long configuration

**Benefits of Separate YAML Files**:
- ✅ Clean separation: CDL = personality, Workflows = transactional logic
- ✅ YAML is more readable than JSON (no quotes, better comments)
- ✅ Easy to version/diff workflow changes
- ✅ Can have multiple workflow files per character
- ✅ Prepares for future CDL → YAML migration

---

## File Structure

### Directory Layout
```
characters/
├── examples/
│   ├── dotty.json                    # CDL personality (clean!)
│   ├── elena.json                    # CDL personality
│   └── marcus.json                   # CDL personality
│
└── workflows/
    ├── dotty_bartender.yaml          # Dotty's bartender workflows
    ├── dotty_conversation.yaml       # Dotty's social workflows (optional)
    ├── questgiver_quests.yaml        # Quest NPC workflows
    └── shopkeeper_inventory.yaml     # Shop NPC workflows
```

### CDL Reference to Workflows

**dotty.json** (CDL personality file):
```json
{
  "identity": {
    "name": "Dotty",
    "occupation": "AI Bartender of the Lim"
  },
  "transaction_config": {
    "mode": "hybrid",
    "workflow_files": [
      "characters/workflows/dotty_bartender.yaml"
    ],
    "llm_fallback": true,
    "llm_validation": false
  },
  "personality": {
    // ... personality data stays clean ...
  }
}
```

**Benefits**:
- CDL file stays focused on personality
- Can reference multiple workflow files
- Easy to enable/disable workflows
- Workflow files can be shared across characters

---

## YAML Workflow Schema

### Basic Structure

```yaml
# characters/workflows/dotty_bartender.yaml
version: "1.0"
character: "dotty"
description: "Bartender workflows for drink orders and service"

workflows:
  # Workflow 1: Drink Orders
  drink_order:
    description: "Handle drink orders from menu"
    
    # Intent detection - when to trigger this workflow
    triggers:
      patterns:
        - "i'?ll have (a |an )?(.*)"
        - "give me (a |an )?(.*)"
        - "order (a |an )?(.*)"
        - "can i get (a |an )?(.*)"
      
      keywords:
        - "whiskey"
        - "beer"
        - "wine"
        - "cocktail"
        - "drink"
      
      context_required:
        - type: "message_type"
          value: "user_request"
      
      # Optional: LLM validation for ambiguous cases
      llm_validation:
        enabled: false
        prompt: "Is the user ordering a drink? Yes/No"
        confidence_threshold: 0.8
    
    # State machine definition
    states:
      pending:
        description: "Drink ordered, awaiting payment"
        
        # What to inject into system prompt when in this state
        prompt_injection: |
          The user just ordered: {context.drink_name}
          Price: {context.price} coins
          Wait for payment before serving the drink.
          Confirm the order warmly and mention the price.
        
        # How to detect transition to next state
        transitions:
          - to_state: "completed"
            triggers:
              patterns:
                - "here (you go|ya go)"
                - "here'?s (the |your )?.*"
                - "take it"
                - "paid"
              keywords:
                - "payment"
                - "coins"
                - "money"
            action: "complete_transaction"
          
          - to_state: "cancelled"
            triggers:
              patterns:
                - "never mind"
                - "cancel"
                - "forget it"
              keywords:
                - "cancel"
                - "nevermind"
            action: "cancel_transaction"
        
        # Automatic timeout if user doesn't respond
        timeout:
          duration_seconds: 300  # 5 minutes
          action: "cancel_transaction"
          message: "Order timed out - cancelled"
      
      completed:
        description: "Payment received, drink served"
        
        prompt_injection: |
          The user paid for their {context.drink_name}.
          Serve the drink warmly and thank them.
        
        # No transitions - this is final state
        final: true
      
      cancelled:
        description: "Order cancelled by user or timeout"
        
        prompt_injection: |
          The drink order was cancelled.
          Acknowledge politely and offer to help with something else.
        
        final: true
    
    # Initial state and action when workflow triggers
    initial_state: "pending"
    
    # Action to execute when workflow first triggers
    on_trigger:
      action: "create_transaction"
      
      # Context extraction from trigger message
      extract_context:
        drink_name:
          from: "pattern_group"  # Extract from regex group
          group: 2  # Second capture group from pattern
          default: "drink"
        
        price:
          from: "lookup"
          table: "drink_prices"  # Look up in predefined table
          key: "{drink_name}"
          default: 5
      
      # Validation rules
      validation:
        - field: "drink_name"
          rule: "in_list"
          values: ["whiskey", "beer", "wine", "rum", "vodka", "gin", "cocktail"]
          on_fail: "reject"  # or "use_default"
    
    # What to inject into system prompt for this workflow
    system_prompt_addition: |
      You are serving drinks at the Lim. When users order drinks:
      1. Confirm the order warmly
      2. Mention the price (check context for pricing)
      3. Wait for payment
      4. Serve the drink with Dotty's signature warmth

  # Workflow 2: Custom Drink Orders (LLM-driven fallback)
  custom_drink_order:
    description: "Handle custom/creative drink requests"
    
    triggers:
      patterns:
        - "make me something (.*)"
        - "surprise me"
        - "what do you recommend"
      
      # This workflow only triggers if LLM confirms intent
      llm_validation:
        enabled: true
        prompt: |
          User message: "{message}"
          Is the user asking for a custom/creative drink or recommendation?
          Answer: Yes/No
        confidence_threshold: 0.7
    
    states:
      pending:
        description: "Custom drink requested, Dotty is creating it"
        
        prompt_injection: |
          The user wants a custom drink: {context.description}
          Create something special that matches their request.
          Use your creativity as Dotty the bartender!
          Mention the price you decide (usually 7-10 coins for custom drinks).
        
        transitions:
          - to_state: "completed"
            triggers:
              patterns:
                - "here (you go|ya go)"
                - "sounds (good|great|perfect)"
                - "i'?ll take it"
            action: "complete_transaction"
      
      completed:
        prompt_injection: |
          Serve the custom drink with flair!
          Make it a memorable moment.
        final: true
    
    initial_state: "pending"
    
    on_trigger:
      action: "create_transaction"
      extract_context:
        description:
          from: "message"  # Use full message as description
        custom:
          from: "literal"
          value: true

# Drink prices lookup table
lookup_tables:
  drink_prices:
    whiskey: 5
    beer: 4
    wine: 6
    rum: 5
    vodka: 5
    gin: 5
    cocktail: 7
    custom: 8

# Configuration
config:
  workflow_priority: "first_match"  # or "best_match", "all_matches"
  concurrent_workflows: false  # Can user have multiple active workflows?
  max_pending_per_user: 1  # Max pending transactions per user
```

---

## WorkflowManager Implementation

### Loading YAML Workflows

```python
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class WorkflowFile:
    """Represents a loaded workflow file"""
    version: str
    character: str
    description: str
    workflows: Dict[str, Any]
    lookup_tables: Dict[str, Any]
    config: Dict[str, Any]

class WorkflowManager:
    """Manages YAML-based workflows for characters"""
    
    def __init__(self, transaction_manager, llm_client):
        self.transaction_manager = transaction_manager
        self.llm_client = llm_client
        self.loaded_workflows: Dict[str, WorkflowFile] = {}
        self.logger = logging.getLogger(__name__)
    
    async def load_workflows_for_character(self, character_file: str) -> bool:
        """Load workflows from CDL character file reference"""
        try:
            # 1. Load CDL file to get workflow file references
            cdl_data = await self._load_cdl_file(character_file)
            
            transaction_config = cdl_data.get("transaction_config", {})
            workflow_files = transaction_config.get("workflow_files", [])
            
            if not workflow_files:
                self.logger.info(f"No workflow files configured for {character_file}")
                return False
            
            # 2. Load each workflow file
            character_name = cdl_data.get("identity", {}).get("name", "unknown")
            
            for workflow_file_path in workflow_files:
                await self._load_workflow_file(workflow_file_path, character_name)
            
            self.logger.info(f"✅ Loaded {len(workflow_files)} workflow files for {character_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load workflows for {character_file}: {e}")
            return False
    
    async def _load_cdl_file(self, character_file: str) -> Dict[str, Any]:
        """Load CDL JSON file"""
        file_path = Path(character_file)
        if not file_path.exists():
            raise FileNotFoundError(f"CDL file not found: {character_file}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def _load_workflow_file(self, workflow_file: str, character_name: str):
        """Load YAML workflow file"""
        file_path = Path(workflow_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_file}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow_data = yaml.safe_load(f)
        
        # Validate schema
        required_fields = ["version", "workflows"]
        for field in required_fields:
            if field not in workflow_data:
                raise ValueError(f"Workflow file missing required field: {field}")
        
        # Store loaded workflow
        workflow_file_obj = WorkflowFile(
            version=workflow_data.get("version"),
            character=workflow_data.get("character", character_name),
            description=workflow_data.get("description", ""),
            workflows=workflow_data.get("workflows", {}),
            lookup_tables=workflow_data.get("lookup_tables", {}),
            config=workflow_data.get("config", {})
        )
        
        # Index by character name for quick lookup
        self.loaded_workflows[character_name.lower()] = workflow_file_obj
        
        self.logger.info(f"✅ Loaded workflow file: {workflow_file} ({len(workflow_file_obj.workflows)} workflows)")
    
    async def detect_intent(self, message: str, user_id: str, bot_name: str) -> Optional[Dict[str, Any]]:
        """Detect if message triggers any workflow"""
        
        # Get workflows for this bot
        workflow_file = self.loaded_workflows.get(bot_name.lower())
        if not workflow_file:
            return None
        
        # Check each workflow
        for workflow_name, workflow_def in workflow_file.workflows.items():
            trigger_result = await self._check_workflow_trigger(
                workflow_name, workflow_def, message, user_id, bot_name
            )
            
            if trigger_result:
                return {
                    "workflow_name": workflow_name,
                    "workflow_def": workflow_def,
                    "extracted_context": trigger_result["context"],
                    "match_confidence": trigger_result["confidence"]
                }
        
        return None
    
    async def _check_workflow_trigger(
        self, 
        workflow_name: str, 
        workflow_def: Dict[str, Any], 
        message: str, 
        user_id: str, 
        bot_name: str
    ) -> Optional[Dict[str, Any]]:
        """Check if message triggers a specific workflow"""
        
        triggers = workflow_def.get("triggers", {})
        
        # 1. Pattern matching (regex)
        patterns = triggers.get("patterns", [])
        pattern_match = None
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                pattern_match = match
                break
        
        # 2. Keyword matching
        keywords = triggers.get("keywords", [])
        keyword_found = any(kw.lower() in message.lower() for kw in keywords)
        
        # 3. Must match pattern OR keyword (unless both required)
        if not pattern_match and not keyword_found:
            return None
        
        # 4. Extract context from match
        extracted_context = await self._extract_context(
            workflow_def, message, pattern_match
        )
        
        # 5. Validate extracted context
        if not await self._validate_context(workflow_def, extracted_context):
            return None
        
        # 6. LLM validation (if required)
        llm_validation = triggers.get("llm_validation", {})
        if llm_validation.get("enabled", False):
            llm_confirms = await self._llm_validate_intent(
                llm_validation, message, workflow_name
            )
            if not llm_confirms:
                return None
        
        # Trigger confirmed!
        return {
            "context": extracted_context,
            "confidence": 0.9 if pattern_match else 0.7
        }
    
    async def _extract_context(
        self, 
        workflow_def: Dict[str, Any], 
        message: str, 
        pattern_match: Optional[re.Match]
    ) -> Dict[str, Any]:
        """Extract context from message based on workflow definition"""
        
        on_trigger = workflow_def.get("on_trigger", {})
        extract_config = on_trigger.get("extract_context", {})
        
        context = {}
        workflow_file = self.loaded_workflows.get(workflow_def.get("character", "").lower())
        
        for field_name, extract_def in extract_config.items():
            from_type = extract_def.get("from")
            
            if from_type == "pattern_group" and pattern_match:
                # Extract from regex capture group
                group_num = extract_def.get("group", 1)
                try:
                    value = pattern_match.group(group_num).strip()
                    context[field_name] = value or extract_def.get("default", "")
                except (IndexError, AttributeError):
                    context[field_name] = extract_def.get("default", "")
            
            elif from_type == "lookup":
                # Look up value in table
                table_name = extract_def.get("table")
                key = extract_def.get("key", "").format(**context)
                
                if workflow_file and table_name in workflow_file.lookup_tables:
                    lookup_table = workflow_file.lookup_tables[table_name]
                    context[field_name] = lookup_table.get(key, extract_def.get("default", 0))
                else:
                    context[field_name] = extract_def.get("default", 0)
            
            elif from_type == "message":
                # Use full message
                context[field_name] = message
            
            elif from_type == "literal":
                # Use literal value
                context[field_name] = extract_def.get("value")
        
        return context
    
    async def _validate_context(self, workflow_def: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Validate extracted context against workflow rules"""
        
        on_trigger = workflow_def.get("on_trigger", {})
        validation_rules = on_trigger.get("validation", [])
        
        for rule in validation_rules:
            field = rule.get("field")
            rule_type = rule.get("rule")
            on_fail = rule.get("on_fail", "reject")
            
            if field not in context:
                continue
            
            value = context[field]
            
            if rule_type == "in_list":
                allowed_values = rule.get("values", [])
                if value.lower() not in [v.lower() for v in allowed_values]:
                    if on_fail == "reject":
                        return False
                    elif on_fail == "use_default":
                        context[field] = rule.get("default", value)
        
        return True
    
    async def _llm_validate_intent(
        self, 
        llm_validation: Dict[str, Any], 
        message: str, 
        workflow_name: str
    ) -> bool:
        """Use LLM to validate if intent matches workflow"""
        
        prompt = llm_validation.get("prompt", "").format(message=message)
        threshold = llm_validation.get("confidence_threshold", 0.7)
        
        try:
            response = await self.llm_client.simple_completion(
                prompt=prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            answer = response.strip().lower()
            is_yes = "yes" in answer or "true" in answer
            
            self.logger.debug(f"LLM validation for {workflow_name}: {answer} (threshold: {threshold})")
            return is_yes
            
        except Exception as e:
            self.logger.error(f"LLM validation failed: {e}")
            return False  # Fail closed
    
    async def execute_workflow_action(
        self, 
        trigger_result: Dict[str, Any], 
        user_id: str, 
        bot_name: str, 
        message: str
    ) -> Dict[str, Any]:
        """Execute workflow action (create transaction, update state, etc.)"""
        
        workflow_name = trigger_result["workflow_name"]
        workflow_def = trigger_result["workflow_def"]
        extracted_context = trigger_result["extracted_context"]
        
        # Check for pending transaction first
        pending = await self.transaction_manager.check_pending_transaction(user_id, bot_name)
        
        if pending:
            # Existing transaction - check for state transition
            return await self._handle_state_transition(
                pending, workflow_def, message, extracted_context
            )
        else:
            # New transaction - execute on_trigger action
            return await self._handle_new_workflow(
                workflow_name, workflow_def, user_id, bot_name, extracted_context
            )
    
    async def _handle_new_workflow(
        self,
        workflow_name: str,
        workflow_def: Dict[str, Any],
        user_id: str,
        bot_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle new workflow trigger - create transaction"""
        
        on_trigger = workflow_def.get("on_trigger", {})
        action = on_trigger.get("action")
        
        if action == "create_transaction":
            initial_state = workflow_def.get("initial_state", "pending")
            
            # Create transaction
            transaction_id = await self.transaction_manager.create_transaction(
                user_id=user_id,
                bot_name=bot_name,
                transaction_type=workflow_name,
                context=context,
                state=initial_state
            )
            
            # Get prompt injection for initial state
            states = workflow_def.get("states", {})
            state_def = states.get(initial_state, {})
            prompt_injection = state_def.get("prompt_injection", "").format(context=context)
            
            return {
                "transaction_id": transaction_id,
                "workflow_name": workflow_name,
                "state": initial_state,
                "prompt_injection": prompt_injection,
                "context": context
            }
        
        return {}
    
    async def _handle_state_transition(
        self,
        pending_transaction,
        workflow_def: Dict[str, Any],
        message: str,
        new_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle state transition for existing transaction"""
        
        current_state = pending_transaction.state
        states = workflow_def.get("states", {})
        current_state_def = states.get(current_state, {})
        
        # Check transitions
        transitions = current_state_def.get("transitions", [])
        for transition in transitions:
            if await self._check_transition_trigger(transition, message):
                next_state = transition["to_state"]
                action = transition.get("action")
                
                # Execute action
                if action == "complete_transaction":
                    await self.transaction_manager.complete_transaction(
                        pending_transaction.id,
                        final_context={**pending_transaction.context, **new_context}
                    )
                elif action == "cancel_transaction":
                    await self.transaction_manager.cancel_transaction(
                        pending_transaction.id,
                        reason="User cancelled"
                    )
                else:
                    # Update to next state
                    await self.transaction_manager.update_transaction_state(
                        pending_transaction.id,
                        new_state=next_state,
                        context_updates=new_context
                    )
                
                # Get prompt injection for next state
                next_state_def = states.get(next_state, {})
                prompt_injection = next_state_def.get("prompt_injection", "").format(
                    context={**pending_transaction.context, **new_context}
                )
                
                return {
                    "transaction_id": pending_transaction.id,
                    "state": next_state,
                    "prompt_injection": prompt_injection,
                    "action": action
                }
        
        # No transition matched - return current state
        return {
            "transaction_id": pending_transaction.id,
            "state": current_state,
            "prompt_injection": "",
            "no_transition": True
        }
    
    async def _check_transition_trigger(self, transition: Dict[str, Any], message: str) -> bool:
        """Check if message triggers a state transition"""
        triggers = transition.get("triggers", {})
        
        # Pattern matching
        patterns = triggers.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        # Keyword matching
        keywords = triggers.get("keywords", [])
        if any(kw.lower() in message.lower() for kw in keywords):
            return True
        
        return False
    
    def get_workflow_prompt_injection(self, bot_name: str, pending_transaction) -> str:
        """Get prompt injection for current transaction state"""
        
        workflow_file = self.loaded_workflows.get(bot_name.lower())
        if not workflow_file:
            return ""
        
        workflow_name = pending_transaction.transaction_type
        workflow_def = workflow_file.workflows.get(workflow_name)
        if not workflow_def:
            return ""
        
        states = workflow_def.get("states", {})
        state_def = states.get(pending_transaction.state, {})
        
        prompt_injection = state_def.get("prompt_injection", "")
        
        # Format with context
        try:
            return prompt_injection.format(context=pending_transaction.context)
        except KeyError as e:
            self.logger.warning(f"Context formatting error: {e}")
            return prompt_injection
```

---

## Integration with Bot Initialization

### bot.py Updates

```python
# src/core/bot.py

async def initialize_workflow_manager(self):
    """Initialize workflow manager with YAML workflow loading"""
    try:
        # Wait for dependencies
        max_wait = 30
        start_time = time.time()
        
        while (not self.initialized.get("postgres_pool") or 
               not self.initialized.get("transaction_manager") or
               not self.initialized.get("llm_client")):
            if time.time() - start_time > max_wait:
                self.logger.error("❌ Timeout waiting for dependencies for workflow_manager")
                return
            await asyncio.sleep(1)
        
        # Create workflow manager
        from src.roleplay.workflow_manager import WorkflowManager
        self.workflow_manager = WorkflowManager(
            transaction_manager=self.transaction_manager,
            llm_client=self.llm_client
        )
        
        # Load workflows for this character
        character_file = os.getenv("CHARACTER_FILE")
        if character_file:
            loaded = await self.workflow_manager.load_workflows_for_character(character_file)
            if loaded:
                self.logger.info(f"✅ WorkflowManager initialized with workflows")
            else:
                self.logger.info(f"ℹ️ WorkflowManager initialized (no workflows configured)")
        else:
            self.logger.warning("⚠️ No CHARACTER_FILE set, workflows not loaded")
        
        self.initialized["workflow_manager"] = True
        
    except Exception as e:
        self.logger.error(f"❌ Failed to initialize workflow_manager: {e}")
        self.workflow_manager = None
```

---

## Benefits of YAML Approach

### Readability Comparison

**JSON (Old)**:
```json
{
  "workflows": {
    "drink_order": {
      "triggers": {
        "patterns": ["i'll have (a |an )?(.*)"],
        "keywords": ["whiskey", "beer"]
      }
    }
  }
}
```

**YAML (New)**:
```yaml
workflows:
  drink_order:
    triggers:
      patterns:
        - "i'll have (a |an )?(.*)"
      keywords:
        - whiskey
        - beer
```

### Maintainability

- ✅ **Comments**: YAML supports inline comments
- ✅ **Multiline strings**: Easy prompt injection templates
- ✅ **Less noise**: No quotes, commas, braces
- ✅ **Git-friendly**: Better diffs for version control

### Future Migration Path

```yaml
# Future: CDL in YAML format
identity:
  name: Dotty
  occupation: AI Bartender of the Lim
  description: >
    A warm, motherly bartender who serves drinks and wisdom
    in equal measure at the Lim, a mystical tavern.

personality:
  core_traits:
    - warm
    - nurturing
    - wise

# Reference workflows
transaction_config:
  mode: hybrid
  workflow_files:
    - characters/workflows/dotty_bartender.yaml
```

---

## Migration Plan

### Phase 1: Create Workflow Files (Current)
1. ✅ Design YAML schema
2. 🔨 Create `characters/workflows/` directory
3. 🔨 Create `dotty_bartender.yaml` example
4. 🔨 Update `dotty.json` to reference workflow file

### Phase 2: Implement WorkflowManager (Next)
1. 🔨 Create `src/roleplay/workflow_manager.py`
2. 🔨 Implement YAML loading
3. 🔨 Implement intent detection
4. 🔨 Integrate with TransactionManager

### Phase 3: Test & Deploy
1. 🔨 Test Dotty bartender end-to-end
2. 🔨 Create workflows for other characters
3. 🔨 Monitor performance and accuracy

### Phase 4: Future CDL Migration (Optional)
1. 🔜 Convert CDL JSON → YAML
2. 🔜 Unified YAML format for personality + workflows
3. 🔜 Schema validation for both

---

## Summary

**Architecture Decision**: ✅ Separate YAML workflow files

**Key Benefits**:
- Clean separation of personality (CDL) and transactions (workflows)
- Human-readable YAML format
- Scalable for complex characters (multiple workflow files)
- Future-proof for CDL → YAML migration

**Implementation**: Hybrid approach with YAML-based declarative workflows + LLM tool calling fallback

**Next Steps**: Create `characters/workflows/dotty_bartender.yaml` and implement `WorkflowManager` class.
