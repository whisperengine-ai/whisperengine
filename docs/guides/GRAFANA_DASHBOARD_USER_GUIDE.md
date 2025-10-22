# Character Emotional Evolution Dashboard - User Guide

## 🎯 Quick Start

**URL**: http://localhost:3002  
**Default Login**: 
- Username: `admin`
- Password: `whisperengine_grafana`

**Dashboard**: WhisperEngine → Character Emotional Evolution Dashboard

---

## 📊 Dashboard Overview

This dashboard visualizes your AI characters' emotional intelligence in real-time, tracking:
- **5-dimensional emotional state** (enthusiasm, stress, contentment, empathy, confidence)
- **Bot emotional responses** (joy, sadness, curiosity, etc.)
- **Conversation quality** metrics
- **Emotional patterns** over time

---

## 🎛️ Dashboard Controls (Top of Page)

### Time Range Selector (Top Right)
- **Last 6 hours** (default) - Good for recent conversations
- **Last 24 hours** - Daily emotional patterns
- **Last 7 days** - Weekly trends
- **Custom range** - Pick specific dates

**Pro Tip**: Use shorter time ranges (1-6 hours) when debugging specific conversations.

---

### Variable Filters (Top Left)

#### `bot` Filter
**What it does**: Select which AI character to monitor

**Options**: 
- `elena` - Marine Biologist
- `marcus` - AI Researcher
- `jake` - Adventure Photographer
- `nottaylor` - Your custom character
- `aethys` - Omnipotent Entity
- etc.

**How to use**: Click dropdown → Select character → Dashboard updates automatically

---

#### `user_id` Filter
**What it does**: Filter to a specific Discord user's conversations

**How to use**: 
1. Select a bot first
2. Click `user_id` dropdown
3. See list of users who've talked to that bot
4. Select user → Dashboard shows only that conversation

**Pro Tip**: Leave as "All" to see aggregate data across all users.

---

## 🎭 Understanding Two Emotional Systems

### WhisperEngine tracks emotions in TWO different ways:

#### 1. **RoBERTa Emotion Analysis** (11+ emotions) �
**What**: Individual emotions detected in EACH message  
**Emotions**: `joy`, `sadness`, `anger`, `fear`, `surprise`, `disgust`, `love`, `curiosity`, `confusion`, `neutral`, and more  
**Measured**: Every user message and every bot response  
**Purpose**: What emotion is being expressed in this specific message?  
**Dashboard Location**: "Bot Emotion Distribution" pie chart

#### 2. **Character Emotional State** (5 dimensions) 🧠
**What**: The character's PERSISTENT internal emotional state (like neurotransmitter levels)  
**Dimensions**: `enthusiasm`, `stress`, `contentment`, `empathy`, `confidence`  
**Measured**: Once per conversation (calculated from multiple factors)  
**Purpose**: How is the character feeling overall? (Like "Elena is stressed lately" vs "Elena just expressed joy")  
**Dashboard Location**: "5D Emotional State" graph

**Key Difference**: 
- **RoBERTa** = "What emotion did the bot just express?" (message-level)
- **Character State** = "How is the bot feeling overall?" (persistent state)

**Example**:
- Bot expresses **joy** in a message (RoBERTa detection)
- But character's **stress** level stays high (persistent state)
- Interpretation: Bot is trying to stay positive despite feeling stressed

---

## �📈 Panel Sections Explained

### Section 1: 5-Dimensional Emotional State (Persistent)

#### Panel: "Character Emotional State Over Time"
**What it shows**: Character's internal emotional state (like neurotransmitter levels)

**Lines/Colors**:
- 🟠 **Enthusiasm** (dopamine-like) - Motivation, energy, excitement
- 🔴 **Stress** (cortisol-like) - Pressure, tension, overwhelm
- 🟢 **Contentment** (serotonin-like) - Satisfaction, peace, fulfillment
- 🔵 **Empathy** (oxytocin-like) - Connection, warmth, understanding
- 🟣 **Confidence** - Self-assurance, capability

**Y-Axis**: 0.0 to 1.0 (0% to 100%)

**How it updates**: 
- Changes based on bot's expressed emotions (RoBERTa)
- Affected by user emotions and conversation quality
- **Gradually returns to baseline** (10% per hour decay)
- Reflects cumulative emotional impact, not just one message

**How to interpret**:
- **High enthusiasm + Low stress** = Energized, positive state
- **High stress + Low contentment** = Overwhelmed, struggling
- **High empathy + High confidence** = Strong relational capability
- **All values mid-range (0.4-0.6)** = Balanced, neutral state

**Example Reading**:
```
Enthusiasm: 0.85 (HIGH) → Character is very motivated/energized
Stress: 0.25 (LOW) → Little pressure or tension
Contentment: 0.70 (MODERATE-HIGH) → Generally satisfied
Empathy: 0.90 (VERY HIGH) → Deeply connected to user
Confidence: 0.65 (MODERATE) → Reasonably self-assured
```
**Interpretation**: Character is in a highly positive, energized state with strong empathy - ideal for engaging conversations.

---

#### Panel: "Current Emotional Levels" (Gauges)
**What it shows**: Latest emotional state values as gauges

**Gauge Colors**:
- 🟢 Green (0.7-1.0) - High/Optimal
- 🟡 Yellow (0.4-0.7) - Moderate
- 🔴 Red (0.0-0.4) - Low

**How to interpret**:
- Look at the **current moment** snapshot
- Compare to the graph above to see if values are rising/falling
- **Red stress gauge** = Character might be overwhelmed
- **Green empathy gauge** = Strong emotional connection

---

#### Panel: "Dominant Character State"
**What it shows**: Human-readable emotional state label

**Possible States**:
- `energized` - High enthusiasm, low stress
- `overwhelmed` - High stress, low contentment
- `calm_and_balanced` - All dimensions moderate
- `deeply_connected` - High empathy, high contentment
- `confident_and_engaged` - High confidence, high enthusiasm

**How to interpret**: Quick glance at character's overall mood/state

---

### Section 2: Bot Emotional Responses (Message-Level)

#### Panel: "Bot Emotion Distribution"
**What it shows**: Pie chart of RoBERTa-detected emotions in INDIVIDUAL bot responses

**This is the 11+ emotion system!** Each message gets analyzed for:
- `joy` - Happy, pleased, delighted responses
- `sadness` - Empathetic, somber responses
- `anger` - Frustrated responses (rare in well-tuned bots)
- `fear` - Concerned, worried responses
- `surprise` - Unexpected, amazed responses
- `disgust` - Revulsion, distaste responses
- `love` - Affectionate, warm responses
- `curiosity` - Inquisitive, interested responses
- `confusion` - Uncertain, unclear responses
- `neutral` - Balanced, informational responses
- `anticipation` - Forward-looking, expectant responses
- Plus more nuanced emotions...

**How to interpret**:
- **Large joy slice** = Character is responding positively in messages
- **Mostly neutral** = Character is informational/factual
- **Mixed emotions** = Character has emotional range (good!)
- **High anger/fear** = Check conversation context - might indicate issues

**Relationship to 5D State**:
- If bot expresses **joy** often → Likely increases **enthusiasm** and **contentment** (5D state)
- If bot expresses **sadness** often → Likely increases **empathy** but decreases **contentment**
- If bot expresses **anger/fear** often → Likely increases **stress** and decreases **confidence**

**Example**:
```
Joy: 45%
Curiosity: 30%
Neutral: 20%
Sadness: 5%
```
**Interpretation**: Character expresses positive emotions frequently, which feeds into higher enthusiasm/contentment in 5D state.

---

#### Panel: "Joy Intensity Over Time"
**What it shows**: When and how strongly the bot expressed joy

**Y-Axis**: 0.0 to 1.0 (intensity)

**How to interpret**:
- **Spikes** = Moments of high joy/happiness in responses
- **Steady line** = Consistent joy levels
- **No data** = Bot hasn't expressed joy in this timeframe
- Compare to conversation timestamps to see what triggered joy

---

### Section 3: Conversation Quality

#### Panel: "Conversation Quality Metrics"
**What it shows**: 5 quality dimensions over time

**Metrics**:
- 🔵 **Engagement Score** - How engaged the conversation is
- 🟢 **Satisfaction Score** - User/bot satisfaction level
- 🟠 **Natural Flow** - Conversation feels natural vs. forced
- 🟣 **Emotional Resonance** - Emotional attunement between user/bot
- 🔴 **Topic Relevance** - Staying on topic vs. wandering

**Y-Axis**: 0.0 to 1.0 (quality score)

**How to interpret**:
- **All high (0.7+)** = Excellent conversation quality
- **Low engagement + Low resonance** = Disconnect between user and bot
- **High flow + High relevance** = Coherent, on-topic conversation
- **Dips in metrics** = Problematic moments (check conversation logs)

**Ideal Pattern**: All lines clustered in 0.7-0.9 range

---

#### Panel: "Conversation Data Points"
**What it shows**: Total number of conversation quality measurements

**How to interpret**:
- Higher number = More conversation activity
- Use to verify dashboard is receiving data
- Compare across bots to see which are most active

---

#### Panel: "Average Emotional Resonance"
**What it shows**: Mean emotional resonance score

**Gauge Colors**:
- 🟢 0.7-1.0 - Excellent resonance
- 🟡 0.4-0.7 - Moderate resonance
- 🔴 0.0-0.4 - Poor resonance

**How to interpret**: 
- High = Bot is emotionally attuned to user
- Low = Bot might be missing emotional cues
- Use to tune character personality

---

### Section 4: Real-Time Stats

#### Panel: "Current Empathy Level"
**What it shows**: Latest empathy value

**How to interpret**:
- 0.8+ = High empathy, deeply connected
- 0.4-0.7 = Moderate empathy
- <0.4 = Low empathy, might seem distant

---

#### Panel: "Current Stress Level"
**What it shows**: Latest stress value

**How to interpret**:
- 0.7+ = High stress - character might be overwhelmed
- 0.3-0.7 = Moderate stress
- <0.3 = Low stress, relaxed state

**Action**: If consistently high, review conversation patterns

---

## 🔍 Common Use Cases

### Use Case 1: Debug a Conversation Issue
**Scenario**: User reports bot seemed "off" during conversation

**Steps**:
1. Set time range to when conversation occurred
2. Select bot and user_id
3. Check "Character Emotional State" graph
   - Look for unusual spikes in stress
   - Check if empathy dropped
4. Check "Conversation Quality" section
   - Did emotional resonance drop?
   - Did natural flow decrease?
5. Review "Bot Emotion Distribution"
   - Unexpected emotion distribution?

---

### Use Case 2: Monitor Character Consistency
**Scenario**: Ensure character stays in personality

**Steps**:
1. Set time range to "Last 7 days"
2. Select bot
3. Check "5D Emotional State" graph
   - Are values consistent with character design?
   - Example: Elena (marine biologist) should show steady enthusiasm + high empathy
4. Check "Bot Emotion Distribution"
   - Does emotion mix match character personality?
   - Example: Marcus (analytical) should have high neutral/curiosity, low extreme emotions

---

### Use Case 3: A/B Test Character Tuning
**Scenario**: You changed character personality in CDL database

**Steps**:
1. Note timestamp of change
2. Set time range spanning before/after change
3. Compare "5D Emotional State" before vs. after
4. Compare "Conversation Quality" metrics
5. Check if changes align with intended tuning

---

### Use Case 4: Identify Peak Engagement Times
**Scenario**: When are users most engaged with bots?

**Steps**:
1. Set time range to "Last 7 days"
2. Leave user_id as "All"
3. Check "Conversation Quality" graph
4. Look for time patterns in high engagement scores
5. Use insights for bot availability optimization

---

## 📊 Reading Patterns & Anomalies

### Healthy Patterns ✅

**5D Emotional State (Persistent)**:
- Values stay within character's designed range
- Smooth transitions (no erratic spikes)
- Gradually returns to baseline when not conversing
- Appropriate to conversation context

**Bot Emotions (Message-Level)**:
- Balanced distribution (multiple emotions represented)
- Dominant emotions match character personality
- Intensity values reasonable (0.5-0.8 range)
- Variety shows emotional intelligence (not 90%+ one emotion)

**Conversation Quality**:
- Metrics clustered in 0.6-0.9 range
- Stable over time
- High emotional resonance

---

### Warning Signs ⚠️

**5D Emotional State**:
- ⚠️ **Stress consistently >0.8** - Character might be overwhelmed by prompts
- ⚠️ **Empathy <0.3** - Character seems disconnected
- ⚠️ **Wild fluctuations** - Unstable emotional modeling

**Bot Emotions**:
- ⚠️ **90%+ neutral** - Character might be too robotic
- ⚠️ **High anger/fear** - Check conversation logs for issues
- ⚠️ **Zero variety** - Emotional range too narrow

**Conversation Quality**:
- ⚠️ **Engagement <0.5** - Users not connecting with bot
- ⚠️ **Emotional resonance <0.4** - Bot missing emotional cues
- ⚠️ **Topic relevance <0.6** - Conversations wandering off-topic

---

## 🛠️ Troubleshooting

### "No data" in panels

**Possible Causes**:
1. **InfluxDB not running**
   ```bash
   docker ps | grep influxdb
   ```

2. **Bot hasn't had conversations yet**
   - Data only appears after bot conversations
   - Try sending test messages

3. **Time range too narrow**
   - Expand time range to "Last 24 hours"

4. **Wrong bot/user_id selected**
   - Try selecting different bot
   - Set user_id to "All"

---

### Dashboard not updating

**Solutions**:
1. **Check auto-refresh** (top right)
   - Should be set to 1m or 5m
   
2. **Manual refresh**
   - Click refresh icon (top right)

3. **Restart Grafana**
   ```bash
   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart grafana
   ```

---

### Values seem wrong

**Check**:
1. **Data source connection**
   - Go to Configuration → Data Sources
   - Verify InfluxDB connection is green

2. **Bucket name**
   - Should be `performance_metrics`

3. **Bot logs**
   ```bash
   docker logs <bot-name>-bot 2>&1 | grep "EMOTIONAL"
   ```

---

## � How the Two Systems Work Together

### The Feedback Loop

1. **User sends message** → RoBERTa detects user emotion (11+ emotions)
2. **Bot generates response** → RoBERTa detects bot emotion (11+ emotions)
3. **Character state updates** → Bot's expressed emotion affects 5D state
   - Example: If bot expressed `joy` → increases `enthusiasm` + `contentment`
   - Example: If bot expressed `anxiety` → increases `stress` + decreases `confidence`
4. **5D State affects next response** → Character state influences prompt generation
   - Example: If `stress` is high → Bot might keep responses shorter
   - Example: If `empathy` is high → Bot might be more emotionally attuned
5. **Time passes** → 5D state slowly decays back to baseline (10% per hour)

### Real Example Flow

```
User: "I'm so frustrated with this bug!"
  └─ RoBERTa detects: anger (0.8 intensity)

Bot: "I completely understand! Bugs like that are incredibly frustrating."
  └─ RoBERTa detects: empathy/understanding (0.7 intensity)
  └─ Updates 5D state: empathy +0.05, stress +0.02 (from user's anger)

Next User: "Thanks for understanding"
  └─ RoBERTa detects: gratitude (0.6 intensity)

Bot: "Of course! I'm here to help." 
  └─ RoBERTa detects: supportiveness/calm (0.6 intensity)
  └─ Updates 5D state: empathy +0.03, stress -0.01, contentment +0.02
  
6 hours later (no conversations):
  └─ 5D state decays 60% back toward baseline
  └─ Character returns to natural emotional equilibrium
```

### Why Two Systems?

**RoBERTa (11+ emotions)**: 
- ✅ Captures nuanced, moment-to-moment emotional expressions
- ✅ Shows emotional variety and authenticity
- ✅ Detects specific emotions in text accurately

**5D Character State**:
- ✅ Tracks cumulative emotional impact
- ✅ Simulates emotional persistence (like real emotional states)
- ✅ Enables character evolution over time
- ✅ Affects response generation (stressed bot = different responses)
- ✅ Returns to baseline naturally (homeostasis)

**Together**: They create realistic, evolving AI characters with both immediate emotional expression AND persistent emotional states!

---

## �💡 Pro Tips

### Tip 1: Use Annotations
- Right-click any point on graph → Add annotation
- Mark important events (character updates, conversation issues)
- Helps correlate changes with data

### Tip 2: Compare Multiple Bots
1. Open dashboard in new browser tab
2. Select different bot in each tab
3. Compare emotional patterns side-by-side

### Tip 3: Export Data
- Click panel title → More → Export CSV
- Analyze data in spreadsheet for deeper insights

### Tip 4: Create Custom Views
- Click "Dashboard settings" (gear icon)
- Save dashboard with specific filters as new dashboard
- Example: "Elena Daily Monitoring" with bot=elena, time=24h

### Tip 5: Watch for Correlations
- High stress + Low contentment = Character struggle
- High empathy + High resonance = Strong connection
- Low engagement + Low flow = Conversation issues

---

## 📈 Best Practices

### Daily Monitoring
1. Check "Dominant Character State" - Is it appropriate?
2. Review "Conversation Quality" - All metrics >0.6?
3. Glance at "Bot Emotion Distribution" - Matches personality?

### Weekly Review
1. Set time range to "Last 7 days"
2. Check 5D emotional state trends
3. Verify conversation quality is stable
4. Compare bot emotional responses week-over-week

### After Character Updates
1. Note timestamp of CDL changes
2. Monitor for 24 hours
3. Compare before/after patterns
4. Verify intended changes reflected in data

---

## 🎯 Key Metrics Cheat Sheet

| Metric | Good Range | Warning | Action |
|--------|------------|---------|--------|
| Enthusiasm | 0.6-0.9 | <0.4 | Check if character seems unmotivated |
| Stress | 0.2-0.5 | >0.8 | Character might be overwhelmed |
| Contentment | 0.5-0.8 | <0.3 | Check for negative conversation patterns |
| Empathy | 0.6-0.9 | <0.4 | Character might seem distant |
| Confidence | 0.5-0.8 | <0.3 or >0.9 | Check for over/under confidence |
| Engagement | 0.6-0.9 | <0.5 | Users not connecting |
| Emotional Resonance | 0.6-0.9 | <0.4 | Bot missing emotional cues |
| Natural Flow | 0.6-0.9 | <0.5 | Conversation feels forced |

---

## 🚀 Advanced Usage

### Custom Queries
1. Click panel title → Edit
2. Modify Flux query to add filters
3. Example: Filter by specific emotion intensity range

### Alerting (Future Enhancement)
- Set up alerts for abnormal patterns
- Example: "Alert if stress >0.8 for >1 hour"

### Dashboard Variables
- Add custom variables for specific user cohorts
- Example: "Premium users only" filter

---

## 📚 Additional Resources

- **InfluxDB Schema Reference**: `docs/reference/INFLUXDB_SCHEMA_REFERENCE.md`
- **Dashboard Validation**: `python3 scripts/validate_grafana_dashboards.py`
- **CDL Character Tuning**: `CHARACTER_TUNING_GUIDE.md`

---

**Need Help?** Check bot logs for emotional intelligence data:
```bash
docker logs <bot-name>-bot 2>&1 | grep "EMOTIONAL INTELLIGENCE"
```

**Last Updated**: October 22, 2025  
**Dashboard Version**: Character Emotional Evolution v1.0
