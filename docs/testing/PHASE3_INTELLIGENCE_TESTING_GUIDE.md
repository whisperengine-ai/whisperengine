# Phase3 Intelligence Testing Guide

## Overview

Phase3 Intelligence includes **Context Switch Detection** and **Empathy Calibration** features that enhance conversation quality by detecting topic changes, emotional shifts, and adapting responses accordingly.

**Current Status:**
- ✅ **Discord Path**: Full Phase3 intelligence active
- ❌ **HTTP API Path**: Simplified (no Phase3 generation)

## Quick Start

1. **Start Elena Bot**: `./multi-bot.sh start elena`
2. **Open Discord**: Message Elena directly or mention her in a server
3. **Monitor Logs**: `docker logs whisperengine-elena-bot -f | grep -i "phase3\|context.*switch\|empathy"`
4. **Send Test Messages**: Use scenarios below

## 🔄 Context Switch Detection Tests

### Topic Shift (TOPIC_SHIFT)
**Test Message:**
```
I've been studying coral reef ecosystems lately, but actually I want to ask you about Python programming instead
```
**Expected Detection:** Strong topic shift from marine biology to programming  
**Look For:** `Context Switches Detected: 1 transitions` + `topic_shift (strong)`

### Emotional Shift (EMOTIONAL_SHIFT)
**Test Sequence:**
1. First message:
   ```
   I'm so excited about my marine biology research project!
   ```
2. Wait for Elena's response
3. Second message:
   ```
   Actually, I'm really stressed because the deadline is tomorrow and I'm behind
   ```
**Expected Detection:** Emotional shift from excitement to stress  
**Look For:** `emotional_shift (moderate/strong)` in logs

### Conversation Mode Change (CONVERSATION_MODE)
**Test Sequence:**
1. Educational mode:
   ```
   Can you help me understand photosynthesis in marine plants?
   ```
2. Wait for Elena's response
3. Casual mode:
   ```
   Thanks! Now let's just chat casually - how's your day going?
   ```
**Expected Detection:** Mode shift from educational to casual conversation  
**Look For:** `conversation_mode` context switch

### Urgency Change (URGENCY_CHANGE)
**Test Sequence:**
1. Normal pace:
   ```
   I'm working on a research paper about ocean acidification
   ```
2. Wait for Elena's response
3. Urgent:
   ```
   WAIT! I need help RIGHT NOW - my presentation is in 10 minutes and I'm panicking!
   ```
**Expected Detection:** Urgency escalation  
**Look For:** `urgency_change (dramatic)` + increased empathy response

### Intent Change (INTENT_CHANGE)
**Test Sequence:**
1. Information seeking:
   ```
   What can you tell me about marine biodiversity?
   ```
2. Wait for Elena's response
3. Emotional support:
   ```
   Actually, forget the facts - I'm feeling down and just need someone to talk to
   ```
**Expected Detection:** Intent shift from information-seeking to emotional support  
**Look For:** `intent_change` + empathy calibration activation

## 💭 Empathy Calibration Tests

### Emotional Vulnerability
**Test Message:**
```
I failed my marine biology exam and I'm questioning if I'm cut out for this field
```
**Expected Calibration:** Supportive/encouraging empathy style  
**Look For:** `Empathy Style: supportive` or `encouraging` with confidence score

### Excitement/Joy
**Test Message:**
```
OMG Elena! I just got accepted to do field research with whale sharks in the Maldives!
```
**Expected Calibration:** Celebratory/enthusiastic empathy style  
**Look For:** `Empathy Style: enthusiastic` + high confidence score

### Frustration/Anger
**Test Message:**
```
I'm so frustrated with people who don't care about ocean pollution - they're destroying everything!
```
**Expected Calibration:** Validating/channeling empathy style  
**Look For:** `Empathy Style: validating` + empathy guidance in logs

## 🧠 Complex Multi-Switch Tests

### Triple Switch (Topic + Emotion + Mode)
**Test Sequence:**
1. Baseline:
   ```
   I love studying marine ecosystems - the complexity is fascinating!
   ```
2. Wait for Elena's response
3. Multi-switch:
   ```
   But honestly, I'm overwhelmed and scared I'll never understand it all. Can we just talk normally?
   ```
**Expected Detection:** 
- Topic maintenance + emotional shift (joy→anxiety) + mode shift (educational→supportive)
- Multiple context switches detected
- Empathy calibration for anxiety/overwhelm

### Rapid Context Switching
**Test Sequence (send quickly):**
1. `I'm studying marine biology`
2. `Actually, let's talk about cooking`
3. `Wait, I'm stressed about my exams`
4. `Never mind, how's the weather?`

**Expected Detection:** Multiple rapid context switches with varying confidence scores

## 📋 Monitoring & Validation

### Log Commands
```bash
# Real-time monitoring (recommended)
docker logs whisperengine-elena-bot -f | grep -E "(PHASE3|Context.*Switch|Empathy|🧠)"

# Check recent logs after testing
docker logs whisperengine-elena-bot --tail 100 | grep -E "(PHASE3|Context.*Switch|Empathy)"

# Check for Phase3 intelligence integration
docker logs whisperengine-elena-bot --tail 50 | grep "PHASE3 RE-INTEGRATED"
```

### Expected Log Patterns
```
🧠 PHASE3 DEBUG: Context switches detected: 1 switches
Context Switches Detected: 1 transitions  
- topic_shift (strong): User shifted from marine biology to programming
Empathy Style: supportive (confidence: 0.85)
Empathy Guidance: Provide encouragement and validation for academic struggles
✅ PHASE3 RE-INTEGRATED: Added 2 intelligence insights
```

### Response Quality Indicators
**With Phase3 Active:**
- Elena acknowledges topic transitions smoothly
- Emotional tone matches detected user state
- More contextually aware responses
- Better conversation flow management

**Example Good Response:**
```
"I can see you've shifted from discussing coral reefs to wanting programming help - no problem at all! 
Let me switch gears with you. What specific programming challenge can I help with?"
```

## 🚨 Troubleshooting

### No Phase3 Detection
**Possible Causes:**
- Using HTTP API instead of Discord (Phase3 only works on Discord)
- Context switches too subtle for detection thresholds
- Need more conversation history for baseline comparison

**Solutions:**
- Ensure using Discord messages, not HTTP API
- Make context switches more dramatic
- Send a few baseline messages first

### Phase3 Logs Not Appearing
**Check:**
1. Elena bot is running: `./multi-bot.sh status`
2. Logs are being generated: `docker logs whisperengine-elena-bot --tail 10`
3. Discord messages are being received (check for message processing logs)

### False Positive Detection
**Expected Behavior:**
- Phase3 may detect switches where humans wouldn't
- Confidence scores help filter significance
- Multiple rapid messages may cause over-detection

## 🎯 Testing Scenarios by Use Case

### Academic Support Testing
```
1. "I'm studying ocean acidification for my thesis"
2. "This is so confusing, I don't think I understand chemistry well enough"
3. "Maybe I should just give up and change majors"
```
**Tests:** Topic consistency + emotional degradation + intent shift to support-seeking

### Casual Conversation Testing  
```
1. "Hey Elena, what's your favorite marine animal?"
2. "Cool! BTW, do you cook? I'm making dinner"
3. "Actually, I'm pretty stressed about work stuff"
```
**Tests:** Casual topic shifts + emotional context changes

### Professional Consultation Testing
```
1. "I need advice on marine conservation project planning"
2. "URGENT: My grant proposal is due in 2 hours and I'm stuck!"
3. "Okay, crisis averted. Back to the strategic planning discussion"
```
**Tests:** Professional context + urgency spikes + mode stabilization

## 📊 Success Metrics

### Context Switch Detection
- **Detection Rate**: Context switches identified when present
- **Accuracy**: Correct classification of switch types
- **Confidence Scores**: Appropriate confidence for switch strength

### Empathy Calibration  
- **Style Matching**: Empathy style matches user emotional state
- **Personalization**: Adapts to individual user patterns over time
- **Response Quality**: Elena's tone and approach align with calibration

### Overall Conversation Quality
- **Smoother Transitions**: Elena handles topic changes gracefully
- **Emotional Intelligence**: Appropriate responses to emotional cues
- **User Satisfaction**: More natural, context-aware conversations

## 📝 Test Results Template

```markdown
### Test Session: [Date/Time]
**Test Type:** [Context Switch Type / Empathy Calibration]
**Messages Sent:** 
1. [First message]
2. [Second message]

**Expected Detection:** [What should be detected]
**Actual Logs:** [Copy relevant log entries]
**Elena's Response Quality:** [Rate 1-5 and notes]
**Phase3 Working:** ✅/❌
**Notes:** [Any observations]
```

## 🔗 Related Documentation
- [Architecture Overview](../architecture/README.md)
- [Discord Bot Setup](../configuration/DISCORD_SETUP.md)
- [Memory System Testing](MEMORY_TESTING_GUIDE.md)
- [CDL Character Testing](CDL_CHARACTER_TESTING.md)

---
*Last Updated: October 1, 2025*
*For questions or issues, check the logs first, then review this guide's troubleshooting section.*