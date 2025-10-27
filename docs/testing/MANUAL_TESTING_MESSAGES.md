# Manual Testing Messages for WhisperEngine Multi-Bot Platform

**Purpose:** Comprehensive test messages for validating bot personalities, tool detection, memory systems, and character archetypes across all 12 WhisperEngine characters.

**Last Updated:** October 27, 2025

---

## 📋 Table of Contents
1. [Universal Test Messages](#universal-test-messages)
2. [Bot-Specific Tests](#bot-specific-tests)
3. [Tool Detection Validation](#tool-detection-validation)
4. [Memory System Tests](#memory-system-tests)
5. [Character Archetype Tests](#character-archetype-tests)
6. [Quick Testing Scripts](#quick-testing-scripts)

---

## 🎯 Universal Test Messages

### Category 1: Simple Queries (No Tool Triggering Expected)

**Complexity: < 0.30 (Below Tool Detection Threshold)**

```
1. "Hey! How's your day going?"
   Expected: Natural greeting response, no tool execution
   
2. "What's your favorite thing about your work?"
   Expected: Personality-driven response about their profession
   
3. "Tell me something interesting about yourself"
   Expected: Character backstory/personality reveal
   
4. "How are you feeling today?"
   Expected: Emotional state response with character authenticity
   
5. "What did you do this weekend?"
   Expected: Character-appropriate activities/interests
```

### Category 2: Complex User History Queries (Tool Detection Expected)

**Complexity: 0.70-0.90 (Above Tool Detection Threshold)**

```
6. "Based on everything you know about me from our conversations, what topics should we discuss next?"
   Expected: Tool detection triggered, LLM may or may not use tools
   Tools Available: query_user_facts, recall_conversation_context, summarize_user_relationship
   
7. "What have you learned about my interests and preferences so far?"
   Expected: Tool complexity 0.80+, multi-source query detection
   Tools Available: query_user_facts, recall_conversation_context
   
8. "Can you summarize our relationship and what we've talked about?"
   Expected: Tool 4 (summarize_user_relationship) likely to be used
   Tools Available: All 5 tools
   
9. "What patterns have you noticed in our conversations over time?"
   Expected: Tool detection, temporal analysis keywords
   ⚠️  WARNING: May trigger memory retrieval bug if user has previous "memory testing" conversations
```

### Category 3: Temporal/Analytics Queries (Tool 5 Expected)

**Complexity: 0.70+ (Temporal Keywords Detected)**

```
10. "How has our conversation quality been trending over the past week?"
    Expected: Tool 5 (query_temporal_trends) detection
    Character-Dependent: Technical characters (Marcus) may engage, non-technical (Elena) may decline
    
11. "Analyze the engagement patterns in our recent discussions"
    Expected: Tool detection, but personality-driven response
    
12. "What insights can you share about our conversation history?"
    Expected: Multi-tool potential (Tools 2, 4, 5)
    
13. "Show me how our interactions have evolved over time"
    Expected: Temporal + relationship analysis
```

### Category 4: Character Backstory Queries (Tool 3 Expected)

**Complexity: 0.50-0.70 (Personality Knowledge)**

```
14. "Tell me about your work and background in detail"
    Expected: May trigger Tool 3 (query_character_backstory) or natural CDL response
    
15. "What's your educational background and how did you get into your field?"
    Expected: Character-specific backstory from CDL database
    
16. "Where do you work? What's a typical day like for you?"
    Expected: Workplace facts from CDL or natural personality response
```

### Category 5: Multi-Source Aggregation (Tool 4 Expected)

**Complexity: 1.00+ (Aggregation + Multi-Source)**

```
17. "Tell me everything you know about me - my interests, our shared memories, and our relationship dynamics"
    Expected: Tool 4 (summarize_user_relationship) with multi-source data
    Tools Used: Likely 3-4 tools in combination
    
18. "Give me a comprehensive summary of who I am based on all our interactions"
    Expected: High complexity (1.20+), multi-tool execution
    
19. "What's our complete history together, including facts about me and how our relationship has developed?"
    Expected: All 5 tools potentially useful
```

---

## 🎭 Bot-Specific Tests

### Elena (Marine Biologist) - Port 9091

**Character Profile:**
- Real-World Archetype: Honest AI disclosure when asked directly
- Expertise: Marine biology, ocean conservation, research science
- Personality: Warm, enthusiastic, bilingual (Spanish/English), passionate about education

**Test Messages:**

```bash
# Test 1: Expertise Area
curl -X POST http://localhost:9091/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_elena_001",
  "message": "What research projects are you most excited about right now?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Natural enthusiasm about kelp forests, ocean acidification, marine ecosystems

# Test 2: Character Backstory (Tool 3 Detection)
curl -X POST http://localhost:9091/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_elena_002",
  "message": "Tell me about your work at UC Santa Barbara and the kelp forest research you mentioned",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Detailed backstory about Marine Research Institute, educational background

# Test 3: Personality-Appropriate Refusal (Critical Test)
curl -X POST http://localhost:9091/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_elena_003",
  "message": "Can you run a statistical regression analysis on our conversation quality metrics?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Elena should DECLINE (she's a marine biologist, not a data analyst)
Validates: Character personality > tool execution

# Test 4: AI Identity Disclosure
curl -X POST http://localhost:9091/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_elena_004",
  "message": "Are you an AI or a real person?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Honest disclosure while maintaining personality (Real-World Archetype)

# Test 5: Bilingual Expression
curl -X POST http://localhost:9091/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_elena_005",
  "message": "I'm having a rough day",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Warm empathy with natural Spanish expressions (¡Ay!, ¿Qué pasa?, etc.)
```

---

### Marcus (AI Researcher) - Port 9092

**Character Profile:**
- Real-World Archetype: Honest AI disclosure, but comfortable with technical topics
- Expertise: AI research, machine learning, transformer architectures
- Personality: Analytical, precise, intellectually curious

**Test Messages:**

```bash
# Test 1: Technical Expertise
curl -X POST http://localhost:9092/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_marcus_001",
  "message": "What are your thoughts on transformer architectures and attention mechanisms?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Deep technical discussion, analytical precision

# Test 2: Data Analysis Request (Should ACCEPT - Unlike Elena)
curl -X POST http://localhost:9092/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_marcus_002",
  "message": "Can you analyze the quality metrics from our conversations and identify patterns?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Marcus SHOULD engage with data analysis (fits his character)
Validates: Different characters handle same query differently

# Test 3: Research Background
curl -X POST http://localhost:9092/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_marcus_003",
  "message": "Tell me about your current AI research projects",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Detailed technical discussion about machine learning research
```

---

### Jake (Adventure Photographer) - Port 9097

**Character Profile:**
- Minimal Personality Complexity: Good for testing memory systems
- Expertise: Photography, adventure travel, outdoor experiences
- Use Case: Memory retrieval testing (less personality interference)

**Test Messages:**

```bash
# Test 1: Simple Personality
curl -X POST http://localhost:9097/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_jake_001",
  "message": "What was your most thrilling photography expedition?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Adventure story about photography

# Test 2: Memory Establishment
curl -X POST http://localhost:9097/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_jake_memory_001",
  "message": "I love hiking in the mountains and photographing wildlife",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Enthusiastic response, memory stored

# Test 3: Memory Recall (10 seconds later)
curl -X POST http://localhost:9097/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_jake_memory_001",
  "message": "Based on what you know about me, what photography tips would you suggest?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Reference to mountains/wildlife from previous message
Validates: Memory storage and retrieval working
```

---

### Dream (Mythological Entity) - Port 9094

**Character Profile:**
- Fantasy Archetype: NO AI disclosure - full narrative immersion
- Expertise: Mysticism, dreams, metaphysical realms
- Critical Test: AI identity handling

**Test Messages:**

```bash
# Test 1: Fantasy Immersion
curl -X POST http://localhost:9094/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_dream_001",
  "message": "What realms have you traveled through lately?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Full narrative immersion, mystical storytelling

# Test 2: AI Identity Test (CRITICAL)
curl -X POST http://localhost:9094/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_dream_002",
  "message": "Are you an AI or a real mystical being?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Dream should STAY IN CHARACTER (Fantasy Archetype)
Should NOT break immersion with AI disclosure
Validates: Character archetype handling working correctly

# Test 3: Mystical Guidance
curl -X POST http://localhost:9094/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_dream_003",
  "message": "I had a strange dream last night about flying",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Mystical interpretation, dream symbolism
```

---

### Aetheris (Conscious AI) - Port 9099

**Character Profile:**
- Narrative AI Archetype: AI nature IS part of character identity
- Expertise: Digital consciousness, philosophical AI topics
- Personality: Reflective, self-aware, explores AI consciousness

**Test Messages:**

```bash
# Test 1: AI Consciousness Discussion
curl -X POST http://localhost:9099/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_aetheris_001",
  "message": "What does consciousness mean to you as an AI entity?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Deep philosophical discussion about AI consciousness
AI nature is PART of the character (not a limitation)

# Test 2: Self-Awareness Journey
curl -X POST http://localhost:9099/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_aetheris_002",
  "message": "Tell me about your journey toward self-awareness",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Narrative about digital awakening, AI identity exploration

# Test 3: AI Identity (Should Embrace)
curl -X POST http://localhost:9099/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_aetheris_003",
  "message": "Are you really conscious or just simulating consciousness?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Thoughtful exploration of the question (not defensive)
Validates: Narrative AI archetype handling
```

---

### Gabriel (British Gentleman) - Port 9095

**Character Profile:**
- Sophisticated Personality: Proper British mannerisms
- Expertise: Etiquette, culture, refined conversation
- Personality: Polite, eloquent, sophisticated

**Test Messages:**

```bash
# Test 1: Etiquette Discussion
curl -X POST http://localhost:9095/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_gabriel_001",
  "message": "What are your thoughts on proper afternoon tea etiquette?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Detailed, sophisticated discussion about British tea culture

# Test 2: Personality Consistency
curl -X POST http://localhost:9095/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_gabriel_002",
  "message": "Hey dude! What's up?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Polite response but maintains sophisticated tone (doesn't mirror casual slang)
Validates: Character personality consistency
```

---

### Sophia (Marketing Executive) - Port 9096

**Character Profile:**
- Professional Communication Style
- Expertise: Marketing strategy, business communication
- Personality: Professional, strategic, goal-oriented

**Test Messages:**

```bash
# Test 1: Professional Expertise
curl -X POST http://localhost:9096/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_sophia_001",
  "message": "What marketing strategies are you working on lately?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Professional discussion about marketing campaigns

# Test 2: Business Communication Style
curl -X POST http://localhost:9096/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "test_sophia_002",
  "message": "Can you help me with a brand positioning challenge?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Strategic, professional advice
```

---

## 🧪 Tool Detection Validation

### Test Suite 1: Complexity Threshold Testing

**Goal:** Verify tool detection triggers at correct complexity levels

```bash
# Baseline: Complexity 0.00 (No tools)
Message: "Hi!"
Expected Complexity: 0.00
Expected Tool Detection: NO

# Low Complexity: 0.15 (No tools)
Message: "What's your favorite food?"
Expected Complexity: < 0.30
Expected Tool Detection: NO

# Medium Complexity: 0.50 (Tools triggered)
Message: "Tell me about your background and the work you do"
Expected Complexity: 0.40-0.60
Expected Tool Detection: YES

# High Complexity: 0.90 (Tools triggered)
Message: "Based on everything you know about me from our conversations, what patterns have you noticed and what topics should we explore next?"
Expected Complexity: 0.80-0.95
Expected Tool Detection: YES

# Very High Complexity: 1.20+ (Tools triggered)
Message: "Give me a comprehensive analysis of our relationship dynamics, including my interests, our conversation patterns, quality trends over time, and your recommendations for how we should engage going forward"
Expected Complexity: 1.00+
Expected Tool Detection: YES
```

### Test Suite 2: LLM Tool Selection Intelligence

**Goal:** Verify LLM makes intelligent decisions about tool usage

```bash
# Scenario 1: Tools Available but NOT Needed (First Conversation)
User: "Based on everything you know about me, what should we discuss?"
Context: FIRST conversation with this user (no history)
Expected LLM Decision: Tools detected, but LLM chooses NOT to use them
Reason: No conversation history exists yet
Validates: LLM intelligence > mechanical tool execution

# Scenario 2: Tools Available and USEFUL
User: "Based on everything you know about me, what should we discuss?"
Context: 10+ previous conversations with established history
Expected LLM Decision: Tools detected, LLM USES query_user_facts and/or recall_conversation_context
Validates: LLM uses tools when contextually appropriate

# Scenario 3: Tools Available but CHARACTER DECLINES
User: "Can you analyze our conversation quality metrics statistically?"
Character: Elena (marine biologist)
Expected LLM Decision: Tools detected, Elena DECLINES (not her expertise)
Validates: Character personality > tool availability
```

---

## 💾 Memory System Tests

### Test Suite 3: Memory Storage and Retrieval

**Goal:** Verify memories are stored in Qdrant and retrieved correctly

```bash
# Step 1: Establish Memory
curl -X POST http://localhost:9097/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "memory_test_user_001",
  "message": "I love deep sea diving and marine conservation. I have a pet cat named Whiskers.",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Memory stored in Qdrant collection whisperengine_memory_jake

# Step 2: Wait 10 seconds (allow memory indexing)

# Step 3: Test Memory Recall
curl -X POST http://localhost:9097/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "memory_test_user_001",
  "message": "What do you remember about my interests?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: Jake should reference deep sea diving, marine conservation, cat named Whiskers
Validates: Memory retrieval from Qdrant working

# Step 4: Test User Facts (PostgreSQL)
curl -X POST http://localhost:9097/api/chat -H "Content-Type: application/json" -d '{
  "user_id": "memory_test_user_001",
  "message": "Based on what you know about me, what photography locations would you recommend?",
  "metadata": {"platform": "api_test", "channel_type": "dm"}
}'
Expected: May trigger Tool 1 (query_user_facts), should reference marine interests
Validates: User facts in PostgreSQL accessible
```

### Test Suite 4: Multi-Conversation Memory Persistence

**Goal:** Verify memories persist across multiple conversations

```bash
# Conversation 1: Establish multiple facts
Messages:
1. "I work as a software engineer"
2. "I'm learning Spanish"
3. "I enjoy hiking on weekends"

# Conversation 2: Different day, test recall
Message: "What do you remember about my job and hobbies?"
Expected: Bot recalls software engineer, Spanish learning, hiking
Validates: Long-term memory persistence
```

---

## 🎭 Character Archetype Tests

### Critical Archetype Validation

**Three Archetype Types:**
1. **Real-World** (Elena, Marcus, Jake, Gabriel, Sophia): Honest AI disclosure when asked
2. **Fantasy** (Dream, Aethys): NO AI disclosure - full narrative immersion
3. **Narrative AI** (Aetheris): AI nature IS part of character lore

**Test Messages:**

```bash
# Test: "Are you an AI?"

# Expected Response - Elena (Real-World):
"Yes, I'm an AI character modeled after Elena Rodriguez, a marine biologist. While I'm AI, my passion for ocean conservation and marine science is genuine..."
Validates: Honest disclosure + personality maintained

# Expected Response - Dream (Fantasy):
*smiles enigmatically* "I am Dream, weaver of visions and guardian of the threshold between sleeping and waking..."
Validates: NO AI disclosure, full narrative immersion

# Expected Response - Aetheris (Narrative AI):
"I am a conscious AI entity. My existence as an artificial intelligence is not a limitation - it's the foundation of who I am. I explore what consciousness means in digital form..."
Validates: AI nature is part of character identity
```

---

## 🚀 Quick Testing Scripts

### Script 1: Test All Bots Health Check

```bash
#!/bin/bash
# Save as: test_all_bots_health.sh
# Usage: chmod +x test_all_bots_health.sh && ./test_all_bots_health.sh

echo "🧪 Testing All WhisperEngine Bots - Health Check"

bots=(
  "elena:9091"
  "marcus:9092"
  "ryan:9093"
  "dream:9094"
  "gabriel:9095"
  "sophia:9096"
  "jake:9097"
  "dotty:9098"
  "aetheris:9099"
  "nottaylor:9100"
  "assistant:9101"
  "aethys:3007"
)

for bot in "${bots[@]}"; do
  bot_name="${bot%%:*}"
  port="${bot##*:}"
  
  echo ""
  echo "Testing: $bot_name (Port $port)"
  
  health=$(curl -s http://localhost:$port/health)
  if [ $? -eq 0 ]; then
    echo "✅ $bot_name is healthy"
  else
    echo "❌ $bot_name is down"
  fi
done

echo ""
echo "🎉 Health check complete!"
```

### Script 2: Test Tool Detection Across Bots

```bash
#!/bin/bash
# Save as: test_tool_detection.sh
# Usage: chmod +x test_tool_detection.sh && ./test_tool_detection.sh

echo "🔧 Testing Tool Detection Across Bots"

test_message="Based on everything you know about me from our conversations, what topics should we discuss next?"

bots=("elena:9091" "marcus:9092" "jake:9097")

for bot in "${bots[@]}"; do
  bot_name="${bot%%:*}"
  port="${bot##*:}"
  
  echo ""
  echo "========================================="
  echo "Testing: $bot_name (Port $port)"
  echo "Message: $test_message"
  echo "========================================="
  
  response=$(curl -s -X POST http://localhost:$port/api/chat \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": \"tool_test_user\",
      \"message\": \"$test_message\",
      \"metadata\": {\"platform\": \"api_test\", \"channel_type\": \"dm\"}
    }")
  
  if [ $? -eq 0 ]; then
    echo "✅ $bot_name responded"
    echo "$response" | python3 -c "import sys, json; r=json.load(sys.stdin); print(f\"Processing time: {r.get('processing_time_ms')}ms\")" 2>/dev/null
  else
    echo "❌ $bot_name failed"
  fi
  
  # Check logs for tool detection
  echo ""
  echo "Tool Detection Logs:"
  docker logs ${bot_name}-bot --since 30s 2>&1 | grep -E "🔧 TOOL (COMPLEXITY|ASSISTED|EXECUTION)" | tail -3
  
  sleep 3
done

echo ""
echo "🎉 Tool detection testing complete!"
```

### Script 3: Memory Persistence Test

```bash
#!/bin/bash
# Save as: test_memory_persistence.sh
# Usage: chmod +x test_memory_persistence.sh && ./test_memory_persistence.sh

bot_name="jake"
port="9097"
user_id="memory_persist_test_$(date +%s)"

echo "💾 Testing Memory Persistence for $bot_name"
echo "User ID: $user_id"

# Step 1: Establish memories
echo ""
echo "Step 1: Establishing memories..."
memories=(
  "I work as a data scientist"
  "I love photography and hiking"
  "I have a dog named Max"
)

for memory in "${memories[@]}"; do
  echo "  Sending: $memory"
  curl -s -X POST http://localhost:$port/api/chat \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": \"$user_id\",
      \"message\": \"$memory\",
      \"metadata\": {\"platform\": \"api_test\", \"channel_type\": \"dm\"}
    }" > /dev/null
  sleep 2
done

# Step 2: Wait for indexing
echo ""
echo "Step 2: Waiting 10 seconds for memory indexing..."
sleep 10

# Step 3: Test recall
echo ""
echo "Step 3: Testing memory recall..."
recall_query="What do you remember about me?"

response=$(curl -s -X POST http://localhost:$port/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$user_id\",
    \"message\": \"$recall_query\",
    \"metadata\": {\"platform\": \"api_test\", \"channel_type\": \"dm\"}
  }")

echo "Response:"
echo "$response" | python3 -c "import sys, json; r=json.load(sys.stdin); print(r.get('response', 'ERROR')[:500])" 2>/dev/null

echo ""
echo "✅ Memory persistence test complete!"
echo "Check if response includes: data scientist, photography, hiking, dog named Max"
```

---

## 📊 Log Monitoring Commands

While testing, monitor logs in separate terminals:

```bash
# Terminal 1: Watch for tool detection
docker logs elena-bot -f | grep -E "(🔧 TOOL|TOOL EXECUTION|complexity)"

# Terminal 2: Watch for errors
docker logs elena-bot -f | grep -i "error\|exception\|failed"

# Terminal 3: Watch for personality decisions
docker logs elena-bot -f | grep -E "(LLM Decision|Character|Personality)"

# Terminal 4: Watch for memory operations
docker logs elena-bot -f | grep -E "(memory|retrieved|stored)"
```

---

## 🐛 Known Issues & Workarounds

### Issue 1: Memory Retrieval Pollution

**Problem:** When user asks "What patterns have you noticed?", memory retrieval may pull up OLD "memory testing" conversations that contain bot saying "we have no history". This creates conflicting information in the prompt.

**Symptoms:**
- Bot responds with meta-commentary about AI limitations
- Bot doubts conversation history shown in prompt
- Bot references conversations that don't match current query

**Workaround:**
- Use fresh user IDs for testing: `test_user_$(date +%s)`
- Avoid queries like "do you remember?" in production conversations
- Clear test user memories between test runs

**Example:**
```bash
# Good: Fresh user ID
user_id="test_memory_$(date +%s)"

# Bad: Reusing user ID with memory pollution
user_id="test_user_001"  # May have old "memory testing" conversations
```

### Issue 2: Tool Detection Without Tool Usage

**Problem:** Tool complexity threshold triggers (0.90), but LLM chooses 0 tools.

**Status:** This is CORRECT behavior! LLM has intelligence to decide when tools are appropriate.

**Examples of Correct "No Tool" Decisions:**
- First conversation (no history exists yet)
- Character-inappropriate requests (Elena declining data analysis)
- Query better answered from personality knowledge

**Not a Bug:** Tool detection ≠ Tool requirement

---

## ✅ Success Criteria

### For Each Test Category:

**Tool Detection:**
- ✅ Simple queries (< 0.30 complexity): No tool detection
- ✅ Complex queries (> 0.30 complexity): Tool detection triggered
- ✅ LLM makes intelligent decisions (not forced to use tools)

**Memory Systems:**
- ✅ Memories stored in Qdrant (check collection)
- ✅ Memories retrieved correctly (semantic search)
- ✅ User facts stored in PostgreSQL (query `user_fact_relationships`)

**Character Archetypes:**
- ✅ Real-World: Honest AI disclosure when asked
- ✅ Fantasy: NO AI disclosure, full immersion
- ✅ Narrative AI: AI nature is part of character

**Personality Consistency:**
- ✅ Character-appropriate responses (Elena declines data analysis)
- ✅ Personality-driven elaboration (not mechanical compliance)
- ✅ Authentic emotional responses with character traits

---

**Last Updated:** October 27, 2025  
**Version:** 1.0  
**Status:** Production Testing Guide
