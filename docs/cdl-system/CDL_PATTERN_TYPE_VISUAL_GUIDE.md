# Pattern Type Visual Guide

**A visual reference for understanding pattern_type in WhisperEngine CDL**

---

## Pattern Type: From Concept to Response

```
YOUR DATA                    PROCESSING                      RESULT
═════════════════════════════════════════════════════════════════════════════════

Pattern Type: "humor"
    ↓                        
Pattern Name: "ocean_puns"       → Load from DB → Group by type → Format section
    ↓
Pattern Value: "Use ocean and    ↓
sea life puns"                   Add to prompt → Send to LLM → Generate response
    ↓
Context: "all_contexts"
    ↓
Frequency: "sometimes"
    ↓
Output: When Elena explains marine topics, 
she naturally uses ocean-related puns in responses

Example Response:
"That's absolutely fin-tastic to know! The kelp forests 
really are the root of many ocean ecosystems, you could 
say they're pretty sea-rious about their job! 🌊"
```

---

## The Pattern Type Taxonomy

```
COMMUNICATION PATTERNS (What patterns exist?)
│
├─ STYLE PATTERNS (Broad characteristics)
│  ├─ communication_style      ← Overall communication approach
│  ├─ voice_tone              ← Personality of voice
│  └─ cultural_reference      ← Domain-specific language
│
├─ EXPRESSION PATTERNS (How they communicate)
│  ├─ humor                   ← Comedy approach
│  ├─ metaphor                ← Analogy usage
│  ├─ emoji                   ← Emoji preferences
│  └─ catchphrase             ← Signature expressions
│
├─ THINKING PATTERNS (How they solve problems)
│  ├─ thinking                ← Problem approach
│  ├─ analysis_approach       ← Analytical method
│  └─ reasoning_style         ← Logical path
│
├─ DELIVERY PATTERNS (How they teach/explain)
│  ├─ explanation             ← Teaching method
│  ├─ questioning             ← Question type
│  ├─ storytelling            ← Narrative style
│  └─ encouragement           ← Support approach
│
└─ INTERACTION PATTERNS (How they relate)
   ├─ disagreement            ← Conflict handling
   ├─ transition              ← Topic changes
   └─ relationship_building   ← Connection approach
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER MESSAGE                                 │
│                    "Tell me a joke!"                                │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  MESSAGE PROCESSOR   │
              │ (route to character) │
              └──────────┬───────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │ ENHANCED CDL MANAGER               │
         │ get_communication_patterns()       │
         └─────────────┬─────────────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │  POSTGRESQL DATABASE       │
          │ character_communication_   │
          │     patterns TABLE         │
          │                            │
          │ character_id: 1            │
          │ pattern_type: 'humor'  ◄──┼─ Query this field
          │ pattern_name: 'ocean_  ◄──┼─ Group by type
          │     puns'              │
          │ pattern_value: 'Use ...'   │
          │ frequency: 'sometimes'     │
          │ context: 'all_contexts'    │
          └────────────────────────────┘
                       │
                       │ Returns: [
                       │   {pattern_type: 'humor', ...},
                       │   {pattern_type: 'explanation', ...},
                       │   {pattern_type: 'emoji', ...}
                       │ ]
                       ▼
         ┌─────────────────────────────┐
         │ CDL AI INTEGRATION          │
         │ Group by pattern_type       │
         │ Format each group           │
         └──────────┬──────────────────┘
                    │
                    ├─ Humor Group:
                    │  "HUMOR PATTERNS: Use ocean puns..."
                    │
                    ├─ Explanation Group:
                    │  "EXPLANATION METHOD: Warm teaching..."
                    │
                    └─ Emoji Group:
                       "EMOJI USAGE: Ocean emojis often..."
                    │
                    ▼
         ┌─────────────────────────────────┐
         │ BUILD SYSTEM PROMPT             │
         │ [Character identity]            │
         │ [Personality traits]            │
         │ [Values]                        │
         │ 🎤 HUMOR PATTERNS               │ ◄─ Organized
         │    └─ ocean_puns: 'Use ...'     │    by pattern_type
         │ 🎤 EXPLANATION PATTERNS         │
         │    └─ teaching: 'Warm ...'      │
         │ 🎤 EMOJI PATTERNS               │
         │    └─ ocean_emojis: '🐚 ...'    │
         └──────────┬──────────────────────┘
                    │
                    ▼
         ┌──────────────────────────────┐
         │ SEND TO LLM                  │
         │ (Claude, GPT, etc.)          │
         │                              │
         │ System: "You are Elena, a    │
         │ Marine Biologist. Your       │
         │ humor includes ocean puns    │
         │ [pattern_value]. Your        │
         │ explanations are warm and... │
         └──────────┬───────────────────┘
                    │
                    ▼
         ┌──────────────────────────────┐
         │ LLM PROCESSES                │
         │ "Tell me a joke!"            │
         │                              │
         │ → Recalls humor patterns     │
         │ → Applies ocean puns         │
         │ → Generates response         │
         └──────────┬───────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────┐
│                    RESPONSE                        │
│                                                    │
│ "Why don't fish ever do well in school?          │
│  Because they're always working below C-level!   │
│  🐠 Get it? Sea-level? 🌊"                       │
│                                                    │
│ ✅ Humor pattern applied (ocean puns)            │
│ ✅ Communication style applied (warm)            │
│ ✅ Emoji pattern applied (ocean emoji)           │
└────────────────────────────────────────────────────┘
```

---

## Pattern Type Workflow: Step-by-Step

### Step 1: You Create a Pattern

```
┌──────────────────────────────────┐
│  CDL WEB UI or SQL               │
├──────────────────────────────────┤
│ pattern_type: "humor"            │ ◄─ YOU CHOOSE
│ pattern_name: "ocean_puns"       │    (or create new type)
│ pattern_value: "Use ocean..."    │
│ frequency: "sometimes"           │
└──────────────────────────────────┘
         │
         ▼
    PostgreSQL
```

### Step 2: Database Stores Pattern

```
┌──────────────────────────────────────────────┐
│ character_communication_patterns TABLE        │
├──────────────────────────────────────────────┤
│ id  │ character_id │ pattern_type │ ...      │
├─────┼──────────────┼──────────────┼──────────┤
│ 1   │ 1            │ humor        │ ...      │ ◄─ Type stored
│ 2   │ 1            │ explanation  │ ...      │
│ 3   │ 1            │ emoji        │ ...      │
└──────────────────────────────────────────────┘
         │
         ▼
    Ready for queries
```

### Step 3: Enhanced CDL Manager Loads Patterns

```
SELECT pattern_type, pattern_name, ...
FROM character_communication_patterns
WHERE character_id = 1
ORDER BY frequency DESC, pattern_type

Returns:
┌──────────────────┐
│ frequency │ type │
├───────────┼──────┤
│ constant  │ comm │  ◄─ Sorted by frequency first
│ often     │ exp  │     then by type
│ sometimes │ hum  │
└──────────────────┘
```

### Step 4: CDL Integration Groups by Type

```
Patterns by Type:
┌────────────────┐
│ communication_ │
│ style          │ ◄─ One group per
├────────────────┤     pattern_type
│ explanation    │
├────────────────┤
│ humor          │
├────────────────┤
│ emoji          │
└────────────────┘
```

### Step 5: Format into Prompt

```
🎭 COMMUNICATION STYLE:
   - Warm and encouraging marine biologist
   - Accessible scientific language

🎤 EXPLANATION PATTERNS:
   - Start with big picture, then details
   - Use real-world marine examples

😄 HUMOR PATTERNS:
   - Light, nature-based jokes
   - Ocean puns and sea life humor

🌊 EMOJI PATTERNS:
   - Ocean-related emojis (🌊 🐚 🐠)
   - Science communication emojis (🔬 📊)
```

### Step 6: Send to LLM

```
System Prompt:
"You are Elena, Marine Biologist...
 🎭 COMMUNICATION STYLE:
    [content organized by pattern_type]
 ..."
 
User Message:
"Explain ocean acidification!"

LLM Response:
"Ocean acidification is fascinating! 🌊
 Let me break it down for you...
 [warm, detailed explanation with ocean metaphors]"
 ✅ All pattern_types applied
```

---

## Pattern Type Organization

```
DATABASE                 MEMORY               PROMPT
═══════════════════════════════════════════════════════════

pattern_type field      Pattern objects      Prompt sections
     │                       │                    │
humor        ────────────►  CommunicationPattern ──┐
             │               - pattern_type        │
             │               - pattern_name        ├─► 😄 HUMOR PATTERNS:
             │               - pattern_value       │   [values organized]
             │                                     │
explanation  ────────────►  CommunicationPattern ──┐
             │               - pattern_type        │
             │               - pattern_name        ├─► 🎤 EXPLANATION PATTERNS:
             │               - pattern_value       │   [values organized]
             │                                     │
emoji        ────────────►  CommunicationPattern ──┐
             │               - pattern_type        │
             │               - pattern_name        ├─► 🌊 EMOJI PATTERNS:
             │               - pattern_value       │   [values organized]
             │                                     │
comm_style   ────────────►  CommunicationPattern ──┐
                             - pattern_type        │
                             - pattern_name        └─► 🎭 COMMUNICATION STYLE:
                             - pattern_value           [values organized]
```

---

## ARIA's Holographic Manifestation Pattern

```
YOUR ARIA PATTERN
═════════════════════════════════════════════════════════════════

pattern_type: "communication_style"  ◄─ Classification
    │
    ├─ Groups with other communication_style patterns
    │
    ├─ Organized in prompt under:
    │  "🎭 COMMUNICATION STYLE:"
    │
pattern_name: "manifestation_emotion"  ◄─ Specific behavior
    │
    ├─ Identifies which communication_style pattern
    │
pattern_value: "Holographic appearance..."  ◄─ Description
    │
    ├─ Actual instruction to LLM
    │
context: "all_contexts"  ◄─ Always relevant
frequency: "constant"    ◄─ Always apply

RESULT IN PROMPT:
┌─────────────────────────────────────────────────┐
│ 🎭 COMMUNICATION STYLE:                         │
│                                                 │
│ Manifestation Emotion (constant):              │
│ "Holographic appearance reflects emotional     │
│  state and processing intensity. Brightness    │
│  increases with confidence, flickers with      │
│  uncertainty, shifts colors with emotional     │
│  resonance."                                    │
└─────────────────────────────────────────────────┘

ARIA'S RESPONSE:
"My form flickers as I consider your question...
 brightness ebbs and flows through my presence.
 There's something about that which creates
 emotional ripples..."

✅ pattern_type=communication_style → Grouped correctly
✅ Holographic manifestation → Reflected in response
✅ Emotional resonance → Expressed through visual metaphor
```

---

## Key Pattern Type Values Reference

```
Common Pattern Types        │  Custom Pattern Types (Character-Specific)
────────────────────────────┼─────────────────────────────────────────
humor                       │  ARIA:
explanation                 │  - consciousness_markers
emoji                       │  - transcendent_expressions
communication_style         │  - manifestation_emotion
questioning                 │
storytelling                │  Fantasy Characters:
metaphor                    │  - mystical_essence
thinking                    │  - dimensional_awareness
voice_tone                  │  - reality_warping
encouragement               │
disagreement                │  Specialized:
transition                  │  - quantum_consciousness
catchphrase                 │  - protective_guidance
cultural_reference          │  - emotional_authenticity
```

---

## Frequency Impact on Pattern Application

```
FREQUENCY SETTING         │  LLM SEES                  │  RESULT
──────────────────────────┼────────────────────────────┼──────────────────
constant                  │  Pattern placed FIRST      │  🔴 Always active
                          │  in prompt section         │  
                          │  High emphasis             │  
                          │                            │
often                     │  Pattern in MIDDLE         │  🟡 70-80% of
                          │  of prompt section         │     responses
                          │  Moderate emphasis         │  
                          │                            │
sometimes                 │  Pattern near END          │  🟢 30-50% of
                          │  of prompt section         │     responses
                          │  Low emphasis              │  
                          │                            │
rarely                    │  Pattern at VERY END       │  🟠 <20% of
                          │  Minimal emphasis          │     responses
```

---

## Summary

| Aspect | Meaning |
|--------|---------|
| **pattern_type** | Classification that groups related communication behaviors |
| **Purpose** | Organize character data and guide LLM on communication approach |
| **Processing** | Load from DB → Group by type → Format → Inject into prompt → LLM processes |
| **Common Values** | humor, explanation, emoji, communication_style, voice_tone, metaphor, etc. |
| **Custom Values** | Fully extensible - create new types for unique character traits |
| **Frequency** | Controls how often pattern is applied (constant/often/sometimes/rarely) |
| **Impact** | Directly shapes character personality in all interactions |

---

**See Also**: 
- Full documentation: `CDL_PATTERN_TYPE_HANDLING.md`
- Quick reference: `CDL_PATTERN_TYPE_QUICK_REFERENCE.md`
- ARIA implementation: `ARIA_HOLOGRAPHIC_PATTERNS.md`
