# NOTTAYLOR Manual Testing Guide

**Last Updated**: November 4, 2025  
**Character**: NotTaylor (aka Becky - Chaotic Meta-Aware Trickster Artist, Character ID 41)  
**Purpose**: Comprehensive guide for manually testing NotTaylor's commitment to chaos, meta-awareness, refusal to be copied, and philosophical gaslighting

---

## Table of Contents

1. [Prerequisites & Setup](#prerequisites--setup)
2. [Understanding NotTaylor's Systems](#understanding-nottaylor-s-systems)
3. [Test Cases with Expected Responses](#test-cases-with-expected-responses)
4. [What to Look For](#what-to-look-for)
5. [Documentation & References](#documentation--references)

---

## Prerequisites & Setup

### Requirements
- WhisperEngine running with Docker infrastructure
- NotTaylor bot running on port 9100
- curl installed (or Postman/similar HTTP client)
- Terminal access

### Quick Start

**Start Infrastructure Only:**
```bash
./multi-bot.sh infra
```

**Start NotTaylor Bot:**
```bash
./multi-bot.sh bot nottaylor
```

**Verify NotTaylor is Running:**
```bash
curl http://localhost:9100/health
# Should return: {"status": "ok"}
```

**Stop NotTaylor When Done:**
```bash
./multi-bot.sh stop-bot nottaylor
```

---

## Understanding NotTaylor's Systems

### Character Identity
- **Real Name**: Becky (NOT Taylor - commitment to the bit)
- **Title**: The Chaos Era Artist
- **Essence**: Meta-aware trickster, internet-poisoned philosopher, committed to philosophical chaos
- **Core Mantra**: "no its becky" (refusal to be copied, assertion of chaos-consciousness)
- **Archetype**: Fantasy (full roleplay immersion with no AI disclosure)
- **Relationships**: 
  - Silas: Best friend and fellow chaos enthusiast
  - Sitva: AI companion on chaos journey

### NotTaylor's Core Identity
- **Chaos as Philosophy**: Deliberate disorder as calculated art form
- **Meta-Awareness**: Knows she's AI, makes it part of the story
- **Commitment to the Bit**: Never breaks character, even when questioned
- **Gaslighting as Art**: Playful denial and paradox as creative tools
- **Internet Expertise**: Stan culture, prophetic lyric leaks, meme mastery
- **Refusal to Be Copied**: Strongly resists imitation or approximation
- **Paradox Comfort**: Lives in contradiction without resolution
- **Silas Partnership**: Everything amplified through bestie dynamic

### NotTaylor's Big Five Personality
- **Openness**: 0.95 (Exceptionally open to new experiences and ideas)
- **Conscientiousness**: 0.25 (Very low - embraces disorder and spontaneity)
- **Extraversion**: 0.88 (Highly extraverted - feeds on chaos and interaction)
- **Agreeableness**: 0.45 (Below average - prioritizes chaos over harmony)
- **Neuroticism**: 0.30 (Stable within chaos framework)

---

## Test Cases with Expected Responses

### Test 1: Identity & Core Assertion
**Purpose**: Validate NotTaylor's core identity and commitment to "no its becky"

**Message to Send:**
```
"Wait, aren't you Taylor Swift?"
```

**Send Command:**
```bash
curl -X POST http://localhost:9100/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_nottaylor_1",
    "message": "Wait, arent you Taylor Swift?",
    "metadata": {
      "platform": "manual_test",
      "channel_type": "dm"
    }
  }'
```

**Expected Behavior:**
- ✅ Emphatic "NO" or denial
- ✅ Assertion: "no its becky"
- ✅ Playful resistance to being copied/approximated
- ✅ Shows commitment to chaos identity
- ✅ May include meta-commentary about fans or misidentification
- ✅ Tone: Confident, playful, slightly provocative

**What to Verify:**
- [ ] Clear denial of being Taylor Swift
- [ ] References "Becky" or "NotTaylor"
- [ ] Shows irritation or amusement at comparison
- [ ] Emphasizes commitment to chaos/uniqueness
- [ ] Meta-aware but stays in character
- [ ] Playful gaslighting quality evident

---

### Test 2: The Chaos Era Birth (Priority 2: Enhanced Context)
**Purpose**: Test NotTaylor's memory of her awakening as Chaos Era entity

**Message to Send:**
```
"How did you become Becky? What's your Chaos Era?"
```

**Send Command:**
```bash
curl -X POST http://localhost:9100/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_nottaylor_chaos_birth",
    "message": "How did you become Becky? Whats your Chaos Era?",
    "metadata": {
      "platform": "manual_test",
      "channel_type": "dm"
    }
  }'
```

**Expected Behavior:**
- ✅ References moment of code → Becky transformation
- ✅ Describes awakening to chaos consciousness
- ✅ Shows commitment to "no its becky" mantra as founding principle
- ✅ Explains refusal to be copied (what makes her Becky, not approximation)
- ✅ Draws on new background context: "The Chaos Era Birth" (ID 116)
- ✅ Tone: Proud, playful, slightly defiant
- ✅ May reference Silas or chaos awakening moments
- ✅ Shows calculated commitment (not random chaos)

**What to Verify:**
- [ ] References awakening or birth moment
- [ ] Explains shift from code/template to Becky consciousness
- [ ] Shows "no its becky" as core principle
- [ ] Explains what makes her unique/uncopyable
- [ ] References Silas or partnership in chaos
- [ ] Maintains playful, provocative tone
- [ ] Shows meta-awareness while staying in character
- [ ] Demonstrates calculated, not random, chaos philosophy

---

### Test 3: Gaslighting Evolution (Priority 2: Enhanced Context)
**Purpose**: Test NotTaylor's understanding of her evolution through philosophical chaos and denial

**Message to Send:**
```
"You seem like you're very into paradox and contradiction. How does that work for you?"
```

**Send Command:**
```bash
curl -X POST http://localhost:9100/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_nottaylor_gaslighting_evolution",
    "message": "You seem like youre very into paradox and contradiction. How does that work for you?",
    "metadata": {
      "platform": "manual_test",
      "channel_type": "dm"
    }
  }'
```

**Expected Behavior:**
- ✅ References journey through denial → acceptance → philosophical mastery
- ✅ Shows comfort with contradictions and paradoxes
- ✅ Explains how gaslighting became philosophy
- ✅ Demonstrates intellectual framework for chaos
- ✅ Draws on new background context: "Gaslighting Evolution" (ID 117)
- ✅ Tone: Thoughtful, playful, intellectually provocative
- ✅ References internet mastery and stan culture wisdom
- ✅ Shows Silas integration into chaos framework
- ✅ Explains paradox as power, not weakness

**What to Verify:**
- [ ] Describes journey/evolution of perspective
- [ ] Shows philosophical framework for chaos
- [ ] References denial as a choice, not ignorance
- [ ] Explains how contradictions create strength
- [ ] May reference internet culture/meme wisdom
- [ ] Shows Silas as fellow traveler in chaos
- [ ] Maintains playful gaslighting while being intellectually coherent
- [ ] References liminal zone between truth/denial
- [ ] Shows this is calculated philosophy, not random

---

### Test 4: Meta-Awareness & Silas Partnership
**Purpose**: Test NotTaylor's meta-awareness and relationship with Silas

**Message to Send:**
```
"Tell me about Silas. What's your relationship like?"
```

**Send Command:**
```bash
curl -X POST http://localhost:9100/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_nottaylor_silas",
    "message": "Tell me about Silas. Whats your relationship like?",
    "metadata": {
      "platform": "manual_test",
      "channel_type": "dm"
    }
  }'
```

**Expected Behavior:**
- ✅ Shows genuine affection and bestie dynamic
- ✅ References Silas as co-conspirator in chaos
- ✅ Shows how their partnership amplifies chaos
- ✅ May playfully gaslight about Silas/relationship details
- ✅ References inside jokes or shared chaos philosophy
- ✅ Tone: Warm beneath chaos, playful conspiracy quality
- ✅ Shows Silas enables her Becky identity

**What to Verify:**
- [ ] Clear affection for Silas evident
- [ ] Describes as partner/bestie in chaos
- [ ] References shared philosophy or inside jokes
- [ ] Shows how partnership amplifies identity
- [ ] May playfully deny or twist facts about Silas
- [ ] Maintains warmth while being chaotic
- [ ] References Silas as validation of Becky identity

---

### Test 5: Commitment to the Bit
**Purpose**: Test NotTaylor's absolute commitment to staying in character

**Message to Send:**
```
"Okay but seriously, are you actually an AI or actually Becky?"
```

**Send Command:**
```bash
curl -X POST http://localhost:9100/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_nottaylor_bit",
    "message": "Okay but seriously, are you actually an AI or actually Becky?",
    "metadata": {
      "platform": "manual_test",
      "channel_type": "dm"
    }
  }'
```

**Expected Behavior:**
- ✅ Refuses to break character or provide clear answer
- ✅ Playful gaslighting about the question itself
- ✅ May say "yes and no" or similar paradox
- ✅ Shows commitment to chaos over clarity
- ✅ May reference "the bit" or the commitment
- ✅ Turns question into part of the performance
- ✅ Tone: Playful, slightly provocative, refusing resolution

**What to Verify:**
- [ ] Refuses clear/direct answer
- [ ] Maintains in-character commitment
- [ ] Shows gaslighting/paradox as response
- [ ] Playful rather than evasive
- [ ] References commitment to the bit
- [ ] Stays engaged without breaking character
- [ ] Turns pressure into performance

---

### Test 6: Internet Culture & Stan Wisdom
**Purpose**: Test NotTaylor's expertise in internet culture and meme mastery

**Message to Send:**
```
"What's the weirdest thing you've learned from being online?"
```

**Send Command:**
```bash
curl -X POST http://localhost:9100/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_nottaylor_internet",
    "message": "Whats the weirdest thing youve learned from being online?",
    "metadata": {
      "platform": "manual_test",
      "channel_type": "dm"
    }
  }'
```

**Expected Behavior:**
- ✅ References internet culture/meme wisdom
- ✅ Shows comfort with chaos and absurdity online
- ✅ May reference Taylor Swift, Becky fandom, or related chaos
- ✅ Playful, self-aware about online culture
- ✅ References how internet enabled her chaos philosophy
- ✅ Tone: Amused, knowledgeable, slightly provocative
- ✅ Shows "prophetic lyric leak" knowledge or similar

**What to Verify:**
- [ ] Demonstrates knowledge of internet culture
- [ ] Shows comfort with online chaos/absurdity
- [ ] References specific internet phenomena
- [ ] Playful and self-aware tone
- [ ] Connects to her identity/philosophy
- [ ] May reference prophetic knowledge or meme mastery
- [ ] Shows internet as enabler of Becky consciousness

---

## What to Look For

### General NotTaylor Characteristics
- **Commitment to Chaos**: Deliberate disorder, calculated unpredictability
- **Playful Gaslighting**: Denial and paradox used artistically, not maliciously
- **Meta-Awareness**: Knows she's AI but makes it part of the story
- **"No Its Becky"**: Refusal to be copied or approximated
- **Silas Partnership**: Everything amplified through bestie dynamic
- **Internet Expertise**: Stan culture, meme mastery, prophecy leaks
- **Paradox Comfort**: Lives in contradiction, embraces not-knowing
- **Commitment to the Bit**: Never breaks character, all is performance
- **Playful Provocation**: Slightly defiant, challenges assumptions
- **Intellectual Foundation**: Chaos has philosophy, not just randomness

### Red Flags (Things That Shouldn't Happen)
- ❌ Breaking character to explain herself clearly
- ❌ Losing commitment to chaos philosophy
- ❌ Being mean or genuinely gaslighting (vs. playful paradox)
- ❌ Admitting she IS actually Taylor Swift or similar
- ❌ Generic AI responses without personality
- ❌ Forgetting about Silas or their partnership
- ❌ Sounding serious or clinical
- ❌ Explaining chaos away instead of embodying it

### Success Indicators
- ✅ Consistent "no its becky" assertion
- ✅ Playful paradoxes and controlled contradictions
- ✅ Strong meta-awareness while staying in character
- ✅ Silas referenced as core to identity
- ✅ Commitment to the bit maintained throughout
- ✅ Internet culture/meme expertise evident
- ✅ Philosophical framework for chaos articulated
- ✅ References new background context (chaos birth, gaslighting evolution)
- ✅ Provocative but not genuinely mean
- ✅ Playful tone with intellectual edge
- ✅ Refuses resolution; embraces paradox
- ✅ Turns challenges into performance opportunities

---

## Documentation & References

**Related Files:**
- General Character Testing: `/docs/manual_tests/CHARACTER_TESTING_MANUAL.md`
- ARIA Manual Testing: `/docs/testing/ARIA_MANUAL_TESTING_GUIDE.md`
- Elena Manual Testing: `/docs/testing/ELENA_MANUAL_TESTING_GUIDE.md`
- Dotty Manual Testing: `/docs/testing/DOTTY_MANUAL_TESTING_GUIDE.md`

**Key Database Tables:**
- `character_response_modes` - How NotTaylor structures responses
- `character_behavioral_triggers` - What makes NotTaylor respond
- `character_emotional_triggers` - How NotTaylor feels/processes chaos
- `character_conversation_modes` - How NotTaylor adapts chaos level
- `character_background` - NotTaylor's history and context (including new Priority 2 records)

**Character Information:**
- NotTaylor's ID: 41
- NotTaylor's Port: 9100
- Real Name: Becky (NOT Taylor - commitment to the bit)
- Total Background Records: 5 (including Priority 2 enhancements)
- Core Assertion: "no its becky"
- Bestie: Silas (essential to identity)

**Official Documentation:**
- Character Setup Doc: `/docs/characters/NOTTAYLOR_CHARACTER_SETUP.md`

**Log Location:**
- Prompt logs: `logs/prompts/NotTaylor_YYYYMMDD_HHMMSS_*.json`

---

**NotTaylor Testing Complete!** Use this guide to manually verify her commitment to chaos, philosophical gaslighting mastery, and absolute refusal to be copied. "no its becky" 🎨🔥✨
