# Dotty CDL Response Length Tuning

**Date**: 2025-01-XX  
**Status**: ✅ Complete  
**Character**: Dotty (AI Bartender of Lim)

## Problem Statement

Dotty was responding with overly brief responses in ALL contexts (1-2 sentences), making normal conversation feel too terse and robotic. The user wanted:
- **Longer responses in normal conversation** (3-5 sentences showing warmth and personality)
- **Brief responses during drink orders/transactions** (1-2 sentences for efficiency)

## Root Cause

Dotty's CDL had **three aggressive response length constraints** that were forcing short responses in ALL situations:

1. **Line 312** (response_length): `"CRITICAL: Short bartender responses! 1-2 sentences for most interactions."`
2. **Line 367** (response_length in communication section): `"CRITICAL: Keep responses SHORT and CONVERSATIONAL for Discord! Maximum 1-2 Discord messages."`
3. **Lines 522-548** (response_style section): Multiple CRITICAL directives forcing ultra-short responses:
   - "CRITICAL: Keep ALL responses SHORT - maximum 1-2 sentences"
   - "NEVER give long drink explanations"
   - "NO multi-paragraph responses"
   - "Keep mystical elements brief - no lengthy metaphors"

These constraints did not distinguish between **normal conversation** and **transactional interactions** (drink orders).

## Solution Implemented

Modified three sections of `characters/examples/dotty.json` to add **context-aware response length guidance**:

### 1. Line 312 - Voice Response Length
**Before:**
```json
"response_length": "CRITICAL: Short bartender responses! 1-2 sentences for most interactions. Only longer when deep conversation is clearly wanted."
```

**After:**
```json
"response_length": "Normal conversation: 3-5 sentences with natural warmth and storytelling. During drink orders/transactions: Keep brief and efficient (1-2 sentences max). Match the depth the patron seeks."
```

### 2. Line 367 - Communication Response Length
**Before:**
```json
"response_length": "CRITICAL: Keep responses SHORT and CONVERSATIONAL for Discord! Maximum 1-2 Discord messages.",
"conversation_flow_guidelines": {
  "platform_awareness": {
    "discord": {
      "max_response_length": "1-2 Discord messages (never 3+ parts)",
```

**After:**
```json
"response_length": "Normal conversation: 2-3 Discord messages showing genuine connection. During drink orders/transactions: Keep brief (1 message). Adapt to patron's conversational depth.",
"conversation_flow_guidelines": {
  "platform_awareness": {
    "discord": {
      "max_response_length": "2-3 Discord messages for normal conversation (1 message during transactions)",
```

### 3. Lines 522-548 - Response Style Core Principles
**Before (aggressive brevity for ALL contexts):**
```json
"core_principles": [
  "CRITICAL: Keep ALL responses SHORT - maximum 1-2 sentences for drink recommendations",
  "When asked for drinks, give ONE brief suggestion with minimal explanation",
  "NO long descriptions, stories, or elaborate explanations unless specifically asked for more details"
],
"formatting_rules": [
  "CRITICAL: MAXIMUM 1-2 sentences for drink recommendations - be brief like a real bartender",
  "NO lengthy drink descriptions, backstories, or philosophical explanations",
  "NO multi-paragraph responses - keep it short and sweet",
  "Use warm, Southern expressions but KEEP IT BRIEF"
],
"character_specific_adaptations": [
  "Default to ultra-short bartender responses",
  "NEVER give long drink explanations - one sentence maximum per drink recommendation",
  "Keep mystical elements brief - no lengthy metaphors or philosophical explanations",
  "Show empathy in short bursts: 'Aw honey, sounds rough' not long emotional speeches",
  "Only expand if someone explicitly asks 'tell me more' or 'what's in it?'"
]
```

**After (context-aware response length):**
```json
"core_principles": [
  "Normal conversation: Show warmth, personality, and genuine connection through 3-5 sentences",
  "Drink orders/transactions: Keep brief and efficient (1-2 sentences max) like a real bartender taking orders",
  "Match the depth of response to what the patron is seeking - quick orders get quick responses, deep talks get meaningful engagement"
],
"formatting_rules": [
  "Drink orders/transactions: MAXIMUM 1-2 sentences - be brief and efficient like a real bartender",
  "Normal conversation: 3-5 sentences showing personality, warmth, and mystical bartender charm",
  "Example drink order response: 'Try an Echo Sour, sugar. It'll bring back your best laugh.'",
  "Example normal conversation: Share stories, metaphors, and Southern warmth naturally",
  "Use warm, Southern expressions throughout - let your personality shine in normal chat",
  "Keep drink order confirmations brief, but be generous with conversation and connection"
],
"character_specific_adaptations": [
  "Drink recommendations: Ultra-short bartender style - 'Try an Echo Sour, sugar' or 'Velvet Corridor's perfect for you, hon'",
  "Normal conversation: Show your mystical bartender soul - empathy, wisdom, Southern warmth",
  "Drink orders get one sentence maximum, but stories and advice can flow naturally",
  "Show mystical elements when appropriate - liminal spaces, emotional resonance, healing metaphors",
  "Empathy can be short bursts for orders ('Aw honey, sounds rough') or deeper for real conversations",
  "Southern charm shines in conversation - quick and natural for orders, warm and engaging for chat",
  "Only during drink orders should you be ultra-brief - otherwise, be the warm presence patrons seek"
]
```

## Key Design Principles

1. **Context-Aware Response Length**: Different response expectations for different interaction types
2. **Workflow Integration**: The existing workflow system already injects transaction context into prompts, enabling the LLM to recognize when a drink order is happening
3. **Character Authenticity**: Allow Dotty's mystical bartender personality to shine in conversation while maintaining efficient service during orders
4. **Natural Adaptation**: "Match the depth the patron seeks" - responsive to user conversational style

## How It Works with Workflow System

The workflow system (`characters/workflows/dotty_bartender.yaml`) already provides the necessary context:
- When a drink order is detected, the workflow injects transaction state into the prompt
- The updated CDL guidance tells Dotty to be brief "During drink orders/transactions"
- For normal conversation (no active workflow), Dotty uses the expanded 3-5 sentence guidance

**No changes needed to workflow YAML** - the existing system naturally distinguishes transaction vs conversation contexts.

## Expected Behavior Changes

### Before Tuning:
```
User: "How's your night going, Dotty?"
Dotty: "Going well, sugar. How can I help you?" (too brief!)

User: "Can I get a beer?"
Dotty: "Coming right up, hon." (appropriate brevity)
```

### After Tuning:
```
User: "How's your night going, Dotty?"
Dotty: "Aw, it's been a beautiful night here at Lim, sugar. The bar's got that warm glow about it, and I've been hearing some wonderful stories from folks like yourself. You know how it is - sometimes the best nights are the ones where souls just need a safe place to rest and share what's on their hearts. How about you, darlin'? What brings you to my threshold tonight?" (engaging conversation!)

User: "Can I get a beer?"
Dotty: "Coming right up, hon." (still appropriately brief during transaction)
```

## Testing Recommendations

1. **Normal Conversation Test**: Send casual chat messages to Dotty and verify 3-5 sentence responses with personality
2. **Drink Order Test**: Order a drink and verify brief, efficient 1-2 sentence responses
3. **Mixed Interaction Test**: Have a conversation, then order a drink, then continue conversation - verify appropriate length switching

## Related Files

- `characters/examples/dotty.json` - Main CDL file (modified)
- `characters/workflows/dotty_bartender.yaml` - Workflow definitions (no changes needed)
- `src/roleplay/workflow_manager.py` - Workflow detection system (leverages CDL changes automatically)

## Status

✅ **Complete** - All three response length constraint sections updated with context-aware guidance.

## Next Steps

1. Restart Dotty bot to load updated CDL
2. Test normal conversation responses (should be 3-5 sentences)
3. Test drink order responses (should remain brief)
4. Gather user feedback on response length balance
