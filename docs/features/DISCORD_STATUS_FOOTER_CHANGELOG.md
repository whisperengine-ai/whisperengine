# Discord Status Footer - Changelog

## Version 1.1 - October 16, 2025

### 🆕 New Features

#### **Mixed Emotion Support** ✨
- Bot and user emotions now show **secondary emotions** when ≥30% confidence
- Example: `😊 Joy (60%) + 😔 Sadness (40%)`
- Captures emotionally complex moments (bittersweet, nervous excitement, grateful sadness)
- Expanded emotion emoji set: Added Anticipation 💭, Optimism ✨, Disappointment 😞, Nervousness 😬

#### **Real Dynamic Relationship Scores** 📊
- Now uses **actual database values** from `relationship_state` AI component
- Shows real-time Trust/Affection/Attunement evolution (0.0-1.0 scale → 0-100 display)
- Displays **interaction count** when dynamic scores available
- Example: `👋 Acquaintance (Trust: 42, Affection: 38, Attunement: 51) [15 interactions]`
- Graceful fallback to approximate mapping if database unavailable

#### **Conversation Mode & Interaction Type Detection** 🎯
- Detects and displays **non-standard conversation modes**: Deep Conversation 🧠, Emotional Support 💖, Educational 📚, etc.
- Shows **interaction types**: Assistance Request, Question Answering, Creative Collaboration, etc.
- Only displays when interesting modes detected (not "standard" or "general")
- Example: `💬 **Interaction**: Assistance Request`

#### **Workflow Detection** 🔄
- Shows active workflows when triggered (character-specific)
- Displays workflow name, action, and transaction ID
- Example: `🎯 **Workflow**: **Payment** | Action: validate_transaction | ID: abc12345`

### 🐛 Bug Fixes

#### **Learning Moment Deduplication** 🔧
- Fixed duplicate learning moment types (e.g., "💡Connection, 💡Connection, 💡Connection")
- Added `seen_types` set to track and skip duplicate moment types
- Now shows only unique learning types per message

#### **Bot Emotion Field Name Compatibility** 🎭
- Fixed bot emotion always showing "Neutral (0%)"
- Updated to support both current (`primary_emotion`, `confidence`) and legacy (`emotion`, `roberta_confidence`) field names
- Bot emotion now accurately reflects current response analysis

#### **User Emotion Intensity Fallback** 💬
- Added fallback from `intensity` field to `confidence` field
- Ensures user emotion always displays with proper scoring
- Handles variations in emotion data structure

### 🎨 Format Improvements

#### **Multiline Display** 📋
- Changed from inline bullet-separated format to multiline format
- Each intelligence component on its own line for better readability
- Easier to scan and understand footer components

#### **Clearer Trajectory Labeling** 📈
- Updated trajectory types: "Intensifying", "Calming", "Stable" (more accurate than "Improving"/"Declining")
- Clarified that trajectory shows **historical** bot emotional state, not current response

### 📚 Documentation Updates

- Updated `DISCORD_STATUS_FOOTER.md` with all 9 components
- Updated `DISCORD_STATUS_FOOTER_SUMMARY.md` with implementation details
- Updated `DISCORD_STATUS_FOOTER_QUICKREF.md` with new examples
- Added this changelog document

### 🔧 Configuration Changes

#### **Emoji Frequency Updates** 🎭
Per-character emoji frequency adjustments to match personality:
- **Dotty**: `moderate` → `high` (90% - expressive bartender)
- **Sophia**: `moderate` → `low` (30% - professional marketing exec)
- **Jake**: `high` → `low` (30% - less emoji-heavy)
- **Elena**: Remains `high` (90% - enthusiastic marine biologist)

## Version 1.0 - October 15, 2025

### Initial Release

#### **Core Features** 🎯
- 7 intelligence components: Learning, Memory, Relationship, Bot Emotion, User Emotion, Trajectory, Processing Time
- Environment variable control (`DISCORD_STATUS_FOOTER=true/false`)
- **CRITICAL**: Footer stripping before vector memory storage
- Multiline Discord-friendly formatting
- Comprehensive test suite with 9 test scenarios

#### **Safety Guarantees** 🛡️
- Footer NEVER stored in vector memory
- 50-dash separator pattern for reliable detection
- Memory safeguard validation in test suite
- No impact on semantic search or character personality

#### **Documentation** 📚
- Complete feature guide (500+ lines)
- Implementation summary
- Quick reference guide
- Test documentation

---

## Upgrade Notes

### From 1.0 to 1.1

**No breaking changes** - All updates are additive enhancements:
- Mixed emotions will automatically display when detected
- Real relationship scores will be used when available (transparent fallback)
- Conversation modes/interaction types will appear only when non-standard
- Existing configurations remain valid

**Optional**: Update emoji frequencies for better character-appropriate behavior (see Configuration Changes above).

**Recommended**: Run test suite to validate all enhancements:
```bash
source .venv/bin/activate
PYTHONPATH=/Users/markcastillo/git/whisperengine python tests/automated/test_discord_status_footer.py
```

Expected: `✅ ALL TESTS PASSED!`
