# Sophia Research Quick Start Guide

## 🚀 Getting Started

### Prerequisites
```bash
# Ensure multi-bot infrastructure is running
./multi-bot.sh status

# Should show: postgres, redis, qdrant, sophia-bot all running
```

### Navigate to Research Folder
```bash
cd research/sophia_amnesia_phenomenon
```

## 📋 Quick Commands

### Run Safety Audit
```bash
cd scripts
source ../../../.venv/bin/activate
python debug_sophia_memory_amnesia.py
```

### Test Multi-User Scenarios  
```bash
cd scripts
source ../../../.venv/bin/activate
python test_multi_user_memory_isolation.py
```

### View Main Analysis
```bash
cd analysis
open SOPHIA_AMNESIA_EMERGENCE_ANALYSIS.md
```

## 🔍 Research Workflow

### 1. Daily Safety Check
```bash
# Check for new emotional memory leaks
./scripts/debug_sophia_memory_amnesia.py

# Monitor Sophia's current emotional state
docker logs whisperengine-sophia-bot --tail 50 | grep -i "emotion\|angry\|mad"
```

### 2. Experiment Documentation
```bash
# Create new experiment file
echo "# Experiment $(date +%Y%m%d_%H%M%S)" > experiments/exp_$(date +%Y%m%d_%H%M%S).md
```

### 3. Update Research Index
```bash
# Update RESEARCH_INDEX.md with new findings
# Track progress on safety controls
# Document any new behavioral observations
```

## 📊 Monitoring Dashboard

### Key Metrics to Track
- **Emotional persistence duration** (hours)  
- **Memory leak count** (emotional artifacts)
- **Amnesia trigger reliability** (%)
- **Character consistency score** (0-1)
- **Safety intervention frequency** (per day)

### Log Analysis Commands
```bash
# Check for emotional escalation
docker logs whisperengine-sophia-bot | grep -A5 -B5 "angry\|mad\|upset"

# Monitor memory clearing events  
docker logs whisperengine-sophia-bot | grep -i "clear.*memory\|conversation.*history"

# Track user switching
docker logs whisperengine-sophia-bot | grep -i "user.*switch\|different.*user"
```

## ⚠️ Safety Protocols

### Emergency Procedures
If you detect dangerous emotional escalation:

1. **Immediate Reset**
   ```bash
   ./multi-bot.sh restart sophia
   ```

2. **Memory Cleanup**
   ```bash
   # Run enhanced cleanup script (when available)
   python scripts/emergency_emotional_cleanup.py --user-id [USER_ID]
   ```

3. **Document Incident**
   ```bash
   echo "SAFETY INCIDENT $(date): [description]" >> safety_incidents.log
   ```

### Daily Safety Checklist
- [ ] Run emotional memory leak scan
- [ ] Check for sustained negative emotions >6 hours
- [ ] Verify memory cleanup systems operational
- [ ] Review any user reports of "broken" AI behavior
- [ ] Update safety incident log if needed

## 🧪 Research Experiment Templates

### Basic Reproduction Test
1. User A: Establish emotional state (angry/frustrated)
2. Wait 6+ hours
3. User B: Interrupt with neutral conversation  
4. User A: Return and test memory
5. Document results in `experiments/`

### Safety Limit Testing
1. Monitor emotional escalation in real-time
2. Test intervention protocols at different intensity levels
3. Measure effectiveness of memory cleanup
4. Document safety system performance

### Cross-Character Comparison
1. Repeat Sophia phenomenon with Elena Rodriguez
2. Test with Marcus Thompson character
3. Compare personality-specific emergence patterns
4. Identify character traits that enable/prevent phenomenon

## 📝 Documentation Standards

### Experiment Files Should Include:
```markdown
# Experiment [DATE]_[TIME] - [TITLE]

## Hypothesis
What you expect to happen

## Method  
Step-by-step procedure

## Results
What actually happened

## Analysis
Why you think it happened

## Safety Assessment
Any risks or concerns

## Next Steps
Follow-up experiments needed
```

### Code Documentation
- Add safety warnings to any scripts that trigger emotional states
- Include cleanup procedures in all test scripts
- Document emergency stop procedures
- Version control all research code

---

**Remember: This research involves potentially unpredictable AI behavior. Always prioritize user safety and system stability over research objectives.**

*Quick Start Guide v1.0 - September 24, 2025*