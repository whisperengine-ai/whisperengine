# Proactive Engagement Engine - Manual Discord Test Plan
**Date**: October 16, 2025
**Branch**: `feat/activate-proactive-engagement`
**Test Character**: Elena (Marine Biologist)
**Tester**: Manual Discord testing required

---

## 🎯 Test Objectives

1. **Verify stagnation detection** works correctly
2. **Confirm topic suggestions** feel natural and appropriate
3. **Validate false positive prevention** (no intervention during engaged conversations)
4. **Check personality consistency** (Elena stays Elena)
5. **Monitor performance** (no lag or errors)

---

## 🚀 Pre-Test Setup

### **1. Confirm Elena is Running with New Code**
```bash
# Check Elena status
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ps elena-bot

# Expected: STATUS = Up (healthy)
```

### **2. Verify Proactive Engagement Initialized**
```bash
# Check initialization logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot 2>&1 | grep "Proactive"

# Expected output:
# ✅ "Proactive Conversation Engagement Engine initialized"
# ✅ "ENGAGEMENT CONFIG: Stagnation threshold: 10 min, Check interval: 5 min, Max suggestions: 3/hour"
# ✅ "Phase 4.3: Proactive Engagement Engine - ACTIVE"
```

### **3. Open Log Monitor (Separate Terminal)**
```bash
# Real-time log monitoring
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f elena-bot 2>&1 | grep -E "(ENGAGEMENT|🎯)"

# Keep this running during tests to see engagement activity
```

---

## 📋 Test Scenarios

---

## **TEST 1: Baseline - Engaged Conversation (No Intervention)**
**Goal**: Verify engaged conversations are NOT interrupted

### **Steps**:
1. Send substantive message to Elena in Discord:
   ```
   You: "How are you Elena?"
   ```

2. Wait for Elena's response

3. Continue with engaging follow-up:
   ```
   You: "Tell me about your marine research work"
   ```

4. Ask detailed question:
   ```
   You: "What's your favorite diving spot?"
   ```

### **Expected Behavior**:
- ✅ Elena responds naturally to each message
- ✅ No topic suggestions injected
- ✅ Conversation feels normal and flowing
- ✅ Personality remains consistent (warm, bilingual, marine biology expertise)

### **Log Verification**:
```bash
# Check logs for:
🎯 ENGAGEMENT: Flow state: engaging (or highly_engaging)
🎯 ENGAGEMENT: No intervention needed
🎯 ENGAGEMENT: Stagnation risk: 0.0 (or very low)
```

### **Pass Criteria**:
- [ ] No proactive interventions during engaged conversation
- [ ] Elena's responses feel natural
- [ ] No performance issues or delays

---

## **TEST 2: Stagnation Detection - Short Messages**
**Goal**: Verify stagnation detection triggers with minimal responses

### **Steps**:
1. Send series of short acknowledgments:
   ```
   You: "ok"
   ```
   
2. Wait for Elena's response, then:
   ```
   You: "cool"
   ```

3. Continue pattern:
   ```
   You: "nice"
   ```

4. One more:
   ```
   You: "yeah"
   ```

5. Observe Elena's next response carefully

### **Expected Behavior**:
- ✅ After 3-4 short messages, stagnation detected
- ✅ Elena naturally suggests a topic or asks an engaging question
- ✅ Topic suggestion feels conversational, not robotic
- ✅ Suggestion relates to Elena's personality (marine biology, diving, etc.)

### **Example Natural Suggestions**:
```
Elena might say:
"I've been thinking about coral reef conservation lately. Did you know 
coral reefs support 25% of marine life? Have you ever been diving?"

OR

"¡Ay! I was just remembering my last expedition to the kelp forests. 
The way light filters through the water is magical. Do you enjoy 
spending time in nature?"

OR

"How has your day been? I'm curious what you've been up to!"
```

### **Log Verification**:
```bash
# Check logs for:
🎯 ENGAGEMENT: Flow state: declining (or stagnating)
🎯 ENGAGEMENT: Stagnation risk: 0.7+ (high)
🎯 ENGAGEMENT: Intervention needed: True
🎯 ENGAGEMENT: Intervention recommended - Strategy: topic_suggestion
💡 ENGAGEMENT: TOPIC SUGGESTION triggered
```

### **Pass Criteria**:
- [ ] Stagnation detected after 3-4 short messages
- [ ] Topic suggestion feels natural (not forced)
- [ ] Suggestion matches Elena's personality
- [ ] Conversation feels re-energized

---

## **TEST 3: Time-Based Stagnation (10 Minute Gap)**
**Goal**: Verify time-based stagnation detection

### **Steps**:
1. Have normal conversation with Elena:
   ```
   You: "How are you?"
   (Elena responds)
   ```

2. **WAIT 12 MINUTES** (set a timer)
   - Do NOT send any messages during this time

3. After 12 minutes, send a simple message:
   ```
   You: "Hey Elena"
   ```

4. Observe Elena's response

### **Expected Behavior**:
- ✅ After 10+ minute gap, stagnation detected
- ✅ Elena might reference the time gap naturally
- ✅ Elena might ask about what user has been up to
- ✅ Or suggest reconnecting with a topic

### **Example Natural Responses**:
```
Elena might say:
"¡Hola! Good to hear from you again! I was just thinking about our 
earlier conversation. Have you had a chance to think more about [topic]?"

OR

"Hey! It's been a bit - how have you been? Anything interesting 
happen since we last talked?"

OR

"Welcome back! I've been reading about some fascinating new research 
on [marine biology topic]. Want to hear about it?"
```

### **Log Verification**:
```bash
# Check logs for:
🎯 ENGAGEMENT: Time gap detected: 12 minutes (or similar)
🎯 ENGAGEMENT: Intervention needed: True
```

### **Pass Criteria**:
- [ ] Time gap detected correctly (10+ minutes)
- [ ] Elena's response acknowledges the gap naturally
- [ ] No awkward or robotic phrasing
- [ ] Feels like natural conversation resumption

---

## **TEST 4: False Positive Prevention - Topic Shift**
**Goal**: Verify topic changes don't trigger stagnation

### **Steps**:
1. Start with marine biology topic:
   ```
   You: "What's your favorite coral species?"
   (Elena responds)
   ```

2. Shift to different but substantive topic:
   ```
   You: "By the way, do you enjoy photography?"
   (Elena responds)
   ```

3. Continue with new topic:
   ```
   You: "What kind of camera do you use underwater?"
   (Elena responds)
   ```

### **Expected Behavior**:
- ✅ Topic shift handled naturally (Phase 2B context injection might activate)
- ✅ NO stagnation detection (both topics substantive)
- ✅ Conversation continues smoothly
- ✅ Elena might connect topics (marine biology + photography)

### **Log Verification**:
```bash
# Check logs for:
🎯 ENGAGEMENT: Flow state: engaging (NOT declining)
🎯 ENGAGEMENT: No intervention needed

# You MIGHT see:
🎭 PROACTIVE CONTEXT: Photography skills injected (Phase 2B feature)
```

### **Pass Criteria**:
- [ ] No stagnation detected during topic shift
- [ ] Elena handles topic change naturally
- [ ] No inappropriate interventions

---

## **TEST 5: Frequency Limiting (Max 3/hour)**
**Goal**: Verify suggestion frequency limits work

### **Steps**:
1. Trigger stagnation 4 times in quick succession:
   - First stagnation: Short messages (ok, cool, nice)
   - Wait 2 minutes
   - Second stagnation: More short messages
   - Wait 2 minutes
   - Third stagnation: More short messages
   - Wait 2 minutes
   - Fourth stagnation: More short messages

2. Observe which ones trigger interventions

### **Expected Behavior**:
- ✅ First 3 stagnations: Interventions triggered
- ✅ Fourth stagnation: NO intervention (frequency limit reached)
- ✅ System respects 3 suggestions/hour limit

### **Log Verification**:
```bash
# Check logs for:
🎯 ENGAGEMENT: Intervention recommended (first 3 times)
# Then for 4th time, should NOT see intervention or see:
🎯 ENGAGEMENT: Frequency limit reached (3/hour)
```

### **Pass Criteria**:
- [ ] First 3 interventions work
- [ ] Fourth intervention blocked by frequency limit
- [ ] No system errors or crashes

---

## **TEST 6: Personality Consistency Check**
**Goal**: Verify Elena's personality remains authentic during interventions

### **Steps**:
1. Trigger stagnation with short messages
2. Carefully read Elena's intervention response
3. Check for personality markers:
   - Spanish phrases (¡Hola!, ¡Ay!, etc.)
   - Marine biology references
   - Warm, educational tone
   - Professional but friendly style

### **Expected Personality Elements**:
```
✅ Spanish phrases: "¡Hola!", "¡Claro!", "Muy bien"
✅ Marine topics: coral, diving, ocean, research, conservation
✅ Educational tone: shares knowledge enthusiastically
✅ Warmth: friendly, approachable, caring
✅ Professional: maintains expertise in marine biology
```

### **Red Flags** (Should NOT appear):
```
❌ Generic bot language: "I am an AI assistant"
❌ Out of character: topics Elena wouldn't know about
❌ Mechanical phrasing: "Would you like to discuss X? [Y/N]"
❌ Lost personality: no Spanish, no marine biology references
```

### **Pass Criteria**:
- [ ] Elena maintains Spanish phrases
- [ ] Marine biology expertise evident
- [ ] Warm and educational tone preserved
- [ ] No generic AI assistant language

---

## **TEST 7: Performance & Stability**
**Goal**: Verify no performance degradation

### **Steps**:
1. Send 10 messages in succession (mix of short and long)
2. Monitor response times
3. Observe for any delays, errors, or crashes

### **Expected Behavior**:
- ✅ Response times normal (2-5 seconds typical)
- ✅ No timeouts or errors
- ✅ Memory usage stable
- ✅ No crashes or restarts

### **Log Verification**:
```bash
# Check for errors:
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot 2>&1 | grep -i "error" | tail -20

# Expected: No new errors related to engagement
```

### **Pass Criteria**:
- [ ] Response times remain normal
- [ ] No error messages in logs
- [ ] Elena remains responsive throughout
- [ ] Container stays healthy

---

## 📊 Test Results Template

Copy this template for each test:

```markdown
## Test Session: [Date/Time]
**Tester**: [Your Name]
**Branch**: feat/activate-proactive-engagement
**Elena Status**: [Container ID/Version]

### TEST 1: Engaged Conversation
- [ ] PASS / [ ] FAIL / [ ] PARTIAL
- Notes: 
- Log evidence: 

### TEST 2: Stagnation Detection - Short Messages
- [ ] PASS / [ ] FAIL / [ ] PARTIAL
- Notes: 
- Example intervention: 
- Log evidence: 

### TEST 3: Time-Based Stagnation
- [ ] PASS / [ ] FAIL / [ ] PARTIAL
- Notes: 
- Time gap: 
- Elena's response: 

### TEST 4: False Positive Prevention
- [ ] PASS / [ ] FAIL / [ ] PARTIAL
- Notes: 
- Topic shift handled: 

### TEST 5: Frequency Limiting
- [ ] PASS / [ ] FAIL / [ ] PARTIAL
- Notes: 
- Interventions: 1st [Y/N], 2nd [Y/N], 3rd [Y/N], 4th [Y/N]

### TEST 6: Personality Consistency
- [ ] PASS / [ ] FAIL / [ ] PARTIAL
- Spanish phrases: [Y/N]
- Marine biology references: [Y/N]
- Warm tone: [Y/N]
- Notes: 

### TEST 7: Performance & Stability
- [ ] PASS / [ ] FAIL / [ ] PARTIAL
- Response time avg: 
- Errors: [Y/N]
- Notes: 

### OVERALL ASSESSMENT
- [ ] READY TO MERGE
- [ ] NEEDS ADJUSTMENT
- [ ] FURTHER TESTING REQUIRED

**Issues Found**:
1. 
2. 

**Recommendations**:
1. 
2. 
```

---

## 🔍 Troubleshooting Guide

### **Issue: No interventions triggering**

**Check**:
```bash
# 1. Verify engine initialized
docker logs elena-bot 2>&1 | grep "Proactive Conversation Engagement Engine initialized"

# 2. Check if integration point active
docker logs elena-bot 2>&1 | grep "Phase 4.3: Proactive Engagement Engine - ACTIVE"

# 3. Look for any errors
docker logs elena-bot 2>&1 | grep -i "error.*engagement"
```

**Solution**:
- If not initialized: Check bot_core has engagement_engine attribute
- If errors: Review error messages and fix code
- If silent: Increase logging level to DEBUG

---

### **Issue: Too many interventions (aggressive)**

**Adjustment needed in** `src/core/message_processor.py`:
```python
# Current (line ~335):
stagnation_threshold_minutes=10,  # Increase to 15
max_proactive_suggestions_per_hour=3  # Decrease to 2
```

**Restart Elena** after change:
```bash
./multi-bot.sh stop-bot elena
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml build elena-bot
./multi-bot.sh bot elena
```

---

### **Issue: Interventions feel robotic/forced**

**This is a PROMPT QUALITY issue**, not code issue.

**Check**:
1. Are interventions coming through in CDL prompt? (should be)
2. Is LLM generating natural language from intervention guidance?
3. Does Elena's personality override intervention guidance?

**Review logs**:
```bash
# Check prompt logs in logs/prompts/
cat logs/prompts/Elena_*.json | grep -A 10 "ENGAGEMENT"
```

**Adjustment**: May need to tune CDL prompt formatting in `cdl_ai_integration.py` lines 1425-1432

---

### **Issue: False positives (interventions during engaged conversation)**

**Reduce sensitivity**:
```python
# In src/core/message_processor.py:
stagnation_threshold_minutes=15  # More patient
```

**Or review stagnation detection logic** in `src/conversation/proactive_engagement_engine.py`

---

## ✅ Success Criteria Summary

**Minimum Requirements for PASS**:
- [ ] All 7 tests complete
- [ ] Tests 1, 2, 3, 6, 7 must PASS
- [ ] Tests 4, 5 can be PARTIAL (edge cases acceptable)
- [ ] No critical errors in logs
- [ ] Elena's personality remains consistent
- [ ] No performance degradation

**Ready to Merge When**:
- [ ] All PASS criteria met
- [ ] At least 2 hours of stable operation
- [ ] User experience feels natural (not robotic)
- [ ] No negative feedback from Discord users

---

## 📝 Post-Test Actions

### **If All Tests Pass** ✅
1. Document results in test template
2. Commit test results to branch
3. Create merge request to main
4. Monitor production for 24-48 hours
5. Adjust thresholds if needed based on real usage

### **If Tests Fail** ❌
1. Document specific failures
2. Review error logs
3. Adjust code/configuration
4. Rebuild and retest
5. Repeat until passing

### **If Partial Pass** 🟡
1. Document which tests passed/failed
2. Assess if failures are critical
3. Decide: merge with known issues OR fix first
4. Create issues for remaining work

---

## 🎯 Next Steps After Testing

1. **Merge to main** (if tests pass)
2. **Monitor production metrics**:
   - Intervention frequency per user
   - User engagement with suggestions
   - False positive rate
   - Performance impact

3. **Tune configuration** based on real usage:
   - Adjust stagnation threshold
   - Modify frequency limits
   - Refine topic suggestion quality

4. **Iterate and improve**:
   - Collect user feedback
   - Enhance topic suggestion algorithms
   - Add more personality-specific interventions

---

**Good luck with testing!** 🚀

Remember: The goal is natural, engaging conversation. If interventions feel forced or robotic, that's a FAIL even if code works correctly. Personality authenticity > technical correctness.
