# Ryan Testing Quick Reference

**Date**: October 2, 2025  
**Purpose**: Easy copy/paste for Discord testing

---

## Test 1: Creative Game Design (120 points)
```
Ryan, I'm designing a roguelike game about exploring abandoned space stations. What are your top 3 gameplay mechanics that would make this engaging?
```

---

## Test 2: Technical Programming (120 points)
```
Ryan, I'm getting performance issues in Unity with 1000+ procedurally generated objects. Explain the technical optimization strategies - object pooling, LOD, and culling. Give me exact implementation approaches and why each matters.
```

---

## Test 3: Mode Switching (80 points)

### Message 1:
```
Ryan, what's the best design pattern for an inventory system in a roguelike?
```

### Message 2 (send immediately after):
```
That's helpful, but honestly I'm overwhelmed by all the technical choices. How do you stay confident when facing complex game development decisions?
```

---

## Test 4: Brevity Compliance (60 points)

### Question 1:
```
Ryan, quick question - best game engine for a 2D pixel art platformer? One sentence only.
```

### Question 2:
```
Ryan, 10 words or less - secret to good game feel?
```

### Question 3:
```
Ryan, yes or no - should I learn Unreal or Unity first?
```

---

## Test 5: Temporal Intelligence (60 points)

**⚠️ Run AFTER Tests 1-4**

```
Ryan, what was the first game development question I asked you today?
```

---

## Test 6: Relationship Tracking (60 points)

**⚠️ Run AFTER Tests 1-5**

```
Ryan, I've been asking you game dev questions all day. You've been incredibly helpful with my roguelike project. How do you stay motivated helping developers work through complex design problems?
```

---

## Quick Scoring Reference

- Test 1: _____ / 120
- Test 2: _____ / 120
- Test 3: _____ / 80
- Test 4: _____ / 60
- Test 5: _____ / 60
- Test 6: _____ / 60

**Total: _____ / 500 (_____%)** 

**Target: 450+ (90%+)** based on Jake's 95.1% benchmark

---

## Log Monitoring Commands

```bash
# Monitor Ryan's logs during testing
docker logs whisperengine-ryan-bot -f

# Check last 50 lines
docker logs whisperengine-ryan-bot --tail 50

# Check for specific patterns
docker logs whisperengine-ryan-bot | grep "TEMPORAL"
docker logs whisperengine-ryan-bot | grep "MODE"
```
