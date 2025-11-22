# Roadmap V2 - Phase 11: Personality & Style Tuning

This phase focuses on the "Soul" of the character. Now that we have the "Brain" (Memory + Knowledge), we need to ensure the bot expresses itself in a way that is consistent, engaging, and true to its persona.

## Goals
- [ ] **Style Enforcement**: Ensure the bot strictly adheres to the voice/tone defined in `character.md`.
- [ ] **Natural Knowledge Integration**: Make the bot use retrieved facts (Graph/Vector) naturally in conversation, avoiding robotic "I see that..." statements.
- [ ] **Automated Evaluation**: Build a "Turing Test" suite where an LLM judge grades the bot's responses against its character definition.
- [ ] **Dynamic Verbosity**: Allow the bot to adjust its response length based on the user's input style (mirroring).

## Tasks

### 1. Style Analyzer (`src_v2/evolution/style.py`)
- [ ] Create `StyleAnalyzer` class.
- [ ] Implement `analyze_style(response, character_definition)`:
    - Uses an LLM to score the response on: `Consistency`, `Tone`, `Emoji Usage`, `Formatting`.
- [ ] Add "Style Guidelines" injection to the System Prompt based on recent failures.

### 2. Knowledge Integration Tuning
- [ ] Update `System Prompt` in `src_v2/agents/prompts.py`:
    - Add specific instructions on *how* to use injected knowledge.
    - Example: "Do not explicitly state you are reading from a database. Weave facts naturally into the conversation."
- [ ] Test with "Fact Recall" scenarios (e.g., "How is my pet doing?").

### 3. Automated Character Evaluation (`tests_v2/evaluation/`)
- [ ] Create `test_character_voice.py`.
- [ ] Define "Golden Scenarios" for each character (e.g., Elena explaining a complex topic, Marcus being sarcastic).
- [ ] Run these scenarios and have `gpt-4o` (or similar) grade the output.

### 4. Dynamic Response Configuration
- [x] Add `response_style` to `v2_user_relationships` (or similar preference store).
- [x] Allow users to set preferences (e.g., "Be more concise", "Use less emojis").
- [x] Inject these preferences into the prompt.

## Success Criteria
- [x] Bot passes 90% of "Character Voice" evaluation tests.
- [x] Knowledge injection feels natural and is not detected as "database reading" by human testers.
