# Workflow YAML Format Documentation

## Overview

WhisperEngine's workflow system enables AI roleplay characters to handle structured interactions with state management, pattern matching, and LLM validation. This document describes the YAML format for defining character-specific workflows.

## File Location

Workflow files should be placed in:
```
characters/workflows/{character_name}.yaml
```

Example: `characters/workflows/dotty_bartender.yaml`

## Basic Structure

```yaml
version: "1.0"
character: "character_name"
description: "Brief description of workflows"

workflows:
  workflow_name:
    description: "What this workflow does"
    
    triggers:
      patterns: []
      keywords: []
      llm_validation: {}
    
    states:
      state_name:
        description: "State description"
        prompt_injection: "Context for LLM"
        transitions: []
```

## Top-Level Fields

### Required Fields

- **version** (string): Workflow schema version (currently "1.0")
- **character** (string): Character name (should match the bot's character file)
- **description** (string): Overview of what these workflows do
- **workflows** (object): Dictionary of workflow definitions

### Example

```yaml
version: "1.0"
character: "dotty"
description: "Bartender workflows for drink orders and service at the Lim"

workflows:
  # Workflow definitions here
```

## Workflow Definition

Each workflow has a unique name as its key and contains:

### Required Fields

- **description** (string): Clear explanation of the workflow's purpose
- **triggers** (object): Defines how to detect this workflow
- **states** (object): State machine definition

### Example

```yaml
workflows:
  drink_order:
    description: "Handle standard drink orders from the menu"
    triggers:
      # Trigger configuration
    states:
      # State definitions
```

## Triggers Configuration

Triggers determine when a workflow should activate. The system uses a **hybrid approach**: fast pattern matching with optional LLM validation fallback.

### Trigger Fields

#### patterns (array of strings)
Regex patterns that match user messages. Case-insensitive by default.

```yaml
triggers:
  patterns:
    - "i'?ll have (a |an )?(.*)"           # Matches "I'll have a beer"
    - "give me (a |an )?(.*)"              # Matches "give me a whiskey"
    - "can you make (me |us )?(.*)"        # Matches "can you make me something"
    - "(.*) please"                        # Matches "whiskey please"
```

**Pattern Tips:**
- Use `(.*)` to capture variable content
- Use `(a |an )?` for optional articles
- Use `'?` for optional apostrophes
- Case-insensitive matching is automatic
- First matching pattern wins

#### keywords (array of strings)
Keywords that suggest this workflow. Useful with patterns for higher confidence.

```yaml
triggers:
  keywords:
    - "whiskey"
    - "beer"
    - "wine"
    - "cocktail"
    - "drink"
```

**Keyword Behavior:**
- Keywords are checked if patterns don't match (OR logic)
- Multiple keywords increase confidence
- Case-insensitive matching

#### llm_validation (object)
LLM-based validation for ambiguous intents. Adds ~1 second latency but improves accuracy.

```yaml
triggers:
  llm_validation:
    enabled: true
    prompt: |
      User message: "{message}"
      
      Is the user asking for a custom/creative drink or a recommendation?
      This is different from ordering a specific drink from the menu.
      
      Answer with just: Yes or No
    confidence_threshold: 0.7
```

**LLM Validation Fields:**
- **enabled** (boolean): Whether to use LLM validation
- **prompt** (string): Prompt template for LLM (use `{message}` placeholder)
- **confidence_threshold** (float): Minimum confidence (0.0-1.0) - currently unused but reserved

**When to Use LLM Validation:**
- ✅ Custom/creative requests (ambiguous intent)
- ✅ Recommendations or suggestions
- ✅ Complex multi-step workflows
- ❌ Simple pattern matching (adds unnecessary latency)
- ❌ Clear, unambiguous requests

**Performance:**
- Pattern matching: ~6ms
- LLM validation: ~1000ms
- Use patterns when possible for speed

## States Configuration

States define the workflow's state machine and transitions.

### State Fields

#### description (string)
Human-readable description of what this state represents.

```yaml
states:
  pending:
    description: "Order placed, awaiting payment"
```

#### prompt_injection (string)
Context injected into the character's system prompt when in this state. This guides the character's response.

```yaml
states:
  pending:
    prompt_injection: |
      ACTIVE TRANSACTION - Drink Order:
      - Drink: {context.drink_name}
      - Price: {context.price} coins
      
      Instructions:
      - Acknowledge the order
      - Remind them of the price
      - Wait for payment before serving
```

**Prompt Injection Tips:**
- Use `{context.field_name}` to reference transaction context
- Be specific about what the character should do
- Include pricing information when relevant
- Guide the character's tone and behavior

#### transitions (array of objects)
Defines how to move from this state to another.

```yaml
states:
  pending:
    transitions:
      - to_state: "completed"
        triggers:
          patterns:
            - "here (you go|ya go)"
            - "paid"
            - "(take|here's) the (coins?|money|payment)"
          keywords:
            - "payment"
            - "paid"
```

**Transition Fields:**
- **to_state** (string): Target state name
- **triggers** (object): Same format as workflow triggers (patterns, keywords, llm_validation)

**Common State Transitions:**
- `pending` → `completed`: Payment received
- `pending` → `cancelled`: Order cancelled
- `completed` → (end): Transaction finished

## Complete Example: Drink Order Workflow

```yaml
version: "1.0"
character: "dotty"
description: "Bartender workflows for drink orders and service"

workflows:
  # ============================================================================
  # Standard Drink Orders (Fast Pattern Matching)
  # ============================================================================
  drink_order:
    description: "Handle standard drink orders from the menu"
    
    triggers:
      # Regex patterns for ordering
      patterns:
        - "i'?ll have (a |an )?(.*)"
        - "give me (a |an )?(.*)"
        - "can i get (a |an )?(.*)"
        - "(.*) please"
      
      # Keywords that suggest drink ordering
      keywords:
        - "whiskey"
        - "beer"
        - "wine"
        - "cocktail"
      
      # No LLM validation needed - patterns are reliable
      llm_validation:
        enabled: false
    
    states:
      pending:
        description: "Order placed, awaiting payment"
        
        prompt_injection: |
          ACTIVE TRANSACTION - Drink Order:
          - Drink ordered: {context.drink_name}
          - Price: {context.price} coins
          
          Instructions:
          - Acknowledge their order with Dotty's mystical flair
          - Mention the price
          - Wait for payment before serving
          
          Drink Menu Reference:
          - Beer (4 coins)
          - Wine (6 coins)
          - Whiskey (5 coins)
          - Cocktail (7 coins)
        
        transitions:
          # Transition to completed when payment received
          - to_state: "completed"
            triggers:
              patterns:
                - "here (you go|ya go)"
                - "paid"
                - "(take|here's) the (coins?|money|payment)"
              keywords:
                - "payment"
                - "paid"
          
          # Transition to cancelled if user changes mind
          - to_state: "cancelled"
            triggers:
              patterns:
                - "never ?mind"
                - "cancel"
                - "changed my mind"
                - "don'?t want"
              keywords:
                - "cancel"
                - "nevermind"
      
      completed:
        description: "Payment received, order complete"
        
        prompt_injection: |
          COMPLETED TRANSACTION:
          - The drink order was completed
          - Payment received: {context.price} coins
          
          Instructions:
          - Thank them for their business
          - Serve the drink with flair
          - End the transaction naturally
      
      cancelled:
        description: "Order was cancelled"
        
        prompt_injection: |
          CANCELLED TRANSACTION:
          - The drink order was cancelled
          - No payment required
          
          Instructions:
          - Acknowledge the cancellation gracefully
          - Offer to help with something else
          - Don't push for payment

  # ============================================================================
  # Custom Drink Orders (LLM Validation Fallback)
  # ============================================================================
  custom_drink_order:
    description: "Handle custom/creative drink requests"
    
    triggers:
      # Patterns for creative requests
      patterns:
        - "make me something (.*)"
        - "can you make (me |us )?(a |an |some )?(.*)"
        - "surprise me"
        - "what do you recommend"
        - "something (special|unique|creative)"
        - "mix me (.*)"
      
      # LLM validation required for ambiguous intent
      llm_validation:
        enabled: true
        prompt: |
          User message: "{message}"
          
          Is the user asking for a custom/creative drink or a recommendation?
          This is different from ordering a specific drink from the menu.
          
          Answer with just: Yes or No
        confidence_threshold: 0.7
    
    states:
      pending:
        description: "Custom drink requested, awaiting confirmation"
        
        prompt_injection: |
          ACTIVE TRANSACTION - Custom Drink Order:
          - Request: {context.description}
          - Price: {context.price} coins (custom drinks: 7-10 coins)
          
          Instructions:
          - Be creative! Use Dotty's bartending expertise
          - Suggest a unique drink that matches their request
          - Mention the price
          - Wait for confirmation before serving
        
        transitions:
          - to_state: "completed"
            triggers:
              patterns:
                - "sounds (good|great|perfect|amazing)"
                - "yes"
                - "i'?ll take it"
                - "here (you go|ya go)"
              keywords:
                - "yes"
                - "sure"
                - "payment"
          
          - to_state: "cancelled"
            triggers:
              patterns:
                - "no thanks"
                - "never ?mind"
                - "not interested"
              keywords:
                - "no"
                - "cancel"
      
      completed:
        description: "Custom drink accepted and paid for"
        
        prompt_injection: |
          COMPLETED TRANSACTION:
          - Custom drink order completed
          - Payment received: {context.price} coins
          
          Instructions:
          - Serve the custom drink with theatrical flair
          - Make it feel special and unique
          - Thank them for trying something new
      
      cancelled:
        description: "Custom drink request declined"
        
        prompt_injection: |
          CANCELLED TRANSACTION:
          - Custom drink declined
          - No payment required
          
          Instructions:
          - Accept their decision gracefully
          - Offer standard menu options as alternative
```

## Transaction Context

The workflow system automatically creates transaction records in the database with context that can be referenced in prompt injections.

### Automatic Context Fields

- **price** (integer): Extracted from patterns or set by workflow
- **drink_name** (string): Extracted from patterns
- **custom** (boolean): True for custom_drink_order workflows
- **description** (string): User's original request

### Example Context Usage

```yaml
prompt_injection: |
  Order: {context.drink_name}
  Price: {context.price} coins
  Custom: {context.custom}
```

## Performance Characteristics

### Pattern Matching (Fast Path)
- **Latency**: ~6ms
- **Use for**: Clear, unambiguous requests
- **Confidence**: 95%

### LLM Validation (Fallback Path)
- **Latency**: ~1000ms (1 second)
- **Use for**: Ambiguous or creative requests
- **Confidence**: 95% (after validation)

### State Transitions
- **Latency**: ~4ms (database update)
- **Reliability**: High (ACID-compliant PostgreSQL)

## Best Practices

### 1. Pattern Design
- ✅ Start with specific patterns, add general ones later
- ✅ Use capturing groups `(.*)` for variable content
- ✅ Test patterns with real user messages
- ❌ Don't make patterns too broad (false positives)

### 2. LLM Validation
- ✅ Use for genuinely ambiguous intents
- ✅ Write clear, concise prompts
- ✅ Ask for simple Yes/No answers
- ❌ Don't use for simple pattern matching (adds latency)

### 3. State Machines
- ✅ Keep states simple and focused
- ✅ Provide clear prompt injections for each state
- ✅ Handle both success and cancellation paths
- ❌ Don't create overly complex state machines

### 4. Prompt Injections
- ✅ Be specific about character behavior
- ✅ Include relevant transaction context
- ✅ Guide tone and personality
- ❌ Don't overload with too much instruction

### 5. Testing
- ✅ Test all pattern variations
- ✅ Test state transitions (pending → completed, pending → cancelled)
- ✅ Monitor logs for pattern matching behavior
- ✅ Clear pending transactions between tests

## Debugging

### Enable Debug Logging

The workflow system includes comprehensive debug logging:

```
🔍 WORKFLOW: Checking workflow 'drink_order' with 5 patterns
✅ WORKFLOW: Pattern matched for 'drink_order': i'?ll have (a |an )?(.*)
❌ WORKFLOW: Pattern 'give me (a |an )?(.*)' did not match message
🎯 LLM VALIDATION RESULT: Yes
✅ Created transaction 8: custom_drink_order for user 123 (state: pending)
✅ Completed transaction 8: custom_drink_order → completed
```

### Common Issues

**Issue**: Patterns not matching
- Check regex syntax (use online regex testers)
- Verify case-insensitive matching
- Add debug logging to see which patterns are tested

**Issue**: LLM validation always failing
- Check LLM client configuration
- Verify prompt template formatting
- Test LLM endpoint separately

**Issue**: State transitions not working
- Verify transition trigger patterns
- Check for pending transactions blocking new workflows
- Review transaction state in database

**Issue**: Prompt injections not appearing
- Verify transaction context is being created
- Check for typos in context field names
- Review character response logs

## Database Schema

Transactions are stored in the `roleplay_transactions` table:

```sql
CREATE TABLE roleplay_transactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bot_name VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,  -- Workflow name
    state VARCHAR(50) NOT NULL DEFAULT 'pending',
    context JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### Query Examples

```sql
-- Check pending transactions
SELECT * FROM roleplay_transactions 
WHERE bot_name='dotty' AND state='pending';

-- View completed transactions
SELECT * FROM roleplay_transactions 
WHERE bot_name='dotty' AND state='completed' 
ORDER BY completed_at DESC LIMIT 10;

-- Check transaction context
SELECT id, transaction_type, state, context 
FROM roleplay_transactions 
WHERE id=8;
```

## Integration with Character System

Workflows are loaded automatically when a bot starts if the character JSON file references them:

```json
{
  "identity": {
    "name": "Dotty",
    "occupation": "AI Bartender of the Lim"
  },
  "workflow_file": "characters/workflows/dotty_bartender.yaml"
}
```

The workflow system integrates with:
- ✅ Memory system (conversation history)
- ✅ Emotion analysis (emotional context)
- ✅ CDL personality (character consistency)
- ✅ Universal identity (cross-platform users)

## Future Enhancements

Planned improvements to the workflow system:

- [ ] Multi-step workflows (chained transactions)
- [ ] Conditional branching based on context
- [ ] Time-based state transitions
- [ ] Workflow templates and inheritance
- [ ] Analytics and performance tracking
- [ ] A/B testing support for patterns

## Support

For questions or issues with workflow configuration:
- Check logs: `docker logs whisperengine-{bot}-bot --tail 100`
- Review database: SQL queries above
- Test patterns: Use regex testing tools
- Refer to working example: `characters/workflows/dotty_bartender.yaml`

---

**Version**: 1.0  
**Last Updated**: October 4, 2025  
**Status**: Production Ready ✅
