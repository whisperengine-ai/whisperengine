# Monitoring Guide: PostgreSQL Fact Storage (Phase 2)

**Status**: Phase 2 DEPLOYED - Monitoring in Development  
**Date**: October 5, 2025  
**Decision**: Skip Phase 1 migration - monitor dual storage in dev/test environment

## 🎯 Monitoring Strategy

**Approach**: Run Phase 2 PostgreSQL retrieval alongside existing vector storage
- **No migration needed** - This is dev/test environment
- **Dual storage acceptable** - Vector facts remain for fallback/comparison
- **Monitor performance** - Validate 12-25x improvement in real usage
- **Collect metrics** - Gather data for future optimization decisions

## 📊 What to Monitor

### 1. PostgreSQL Query Performance

**Check logs for PostgreSQL retrieval:**
```bash
# Monitor PostgreSQL fact retrieval
docker logs whisperengine-elena-bot 2>&1 | grep "POSTGRES FACTS: Retrieved" | tail -20

# Sample output:
# ✅ POSTGRES FACTS: Retrieved 5 facts/preferences from PostgreSQL (facts: 4, preferences: 1)
```

**Success indicators:**
- ✅ Log entries show "POSTGRES FACTS: Retrieved X facts"
- ✅ Retrieval happens in 2-5ms (check processing time)
- ✅ No errors about missing knowledge_router

### 2. Fact Storage Accuracy

**Verify entities stored separately:**
```bash
# Check recent facts
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT fe.entity_name, fe.entity_type, ufr.relationship_type, ufr.confidence, ufr.updated_at
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
ORDER BY ufr.updated_at DESC
LIMIT 20;
"
```

**Expected behavior:**
- ✅ "pizza and sushi" stored as TWO entities (pizza, sushi)
- ✅ Each entity has separate relationship entry
- ✅ Confidence scores present (typically 0.8)
- ✅ Timestamps updated correctly

### 3. Preference Storage

**Check preference storage:**
```bash
# View recent preferences
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT universal_id, preferences::jsonb
FROM universal_users
WHERE preferences IS NOT NULL
ORDER BY last_active DESC
LIMIT 10;
"
```

**Expected format:**
```json
{
  "preferred_name": {
    "value": "Mark",
    "confidence": 0.95,
    "updated_at": "2025-10-05T..."
  }
}
```

### 4. Conversation Quality

**Monitor bot responses:**
```bash
# Check if bots mention stored facts
docker logs whisperengine-elena-bot 2>&1 | grep -A 5 "What do you remember"
```

**Quality indicators:**
- ✅ Bots recall pizza/sushi preferences correctly
- ✅ Bots use preferred names in responses
- ✅ Facts integrated naturally into conversation
- ✅ No "I don't remember" when facts exist

## 🔍 Quick Health Checks

### Daily Quick Check (30 seconds)
```bash
# 1. Check PostgreSQL retrieval is working
docker logs whisperengine-elena-bot --tail 100 2>&1 | grep "POSTGRES FACTS" | tail -5

# 2. Count stored facts (should grow over time)
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT COUNT(*) as total_facts FROM user_fact_relationships;
"

# 3. Check for errors
docker logs whisperengine-elena-bot --tail 100 2>&1 | grep -i "error.*postgres\|knowledge_router"
```

### Weekly Deep Check (5 minutes)
```bash
# Run E2E test suite
source .venv/bin/activate
python tests/e2e_postgres_fact_http_test.py

# Expected: 85-95% pass rate
# Elena: 100% (7/7 tests)
# Dotty: 85-100% (6-7/7 tests)
```

## 📈 Performance Baseline

### Current Metrics (Validated)
- **PostgreSQL retrieval**: 2-5ms per query
- **Legacy vector retrieval**: 62-125ms per query
- **Improvement**: 12-25x faster
- **Storage**: PostgreSQL = 1KB, Dual = 2.5KB (60% overhead acceptable in dev)

### Performance Trends to Watch
```bash
# Monitor query performance over time
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT 
  DATE(updated_at) as date,
  COUNT(*) as facts_stored,
  AVG(confidence) as avg_confidence
FROM user_fact_relationships
GROUP BY DATE(updated_at)
ORDER BY date DESC
LIMIT 7;
"
```

## ⚠️ Warning Signs

### Problems to Watch For

**1. PostgreSQL Not Being Used:**
```bash
# If you see NO "POSTGRES FACTS: Retrieved" logs:
docker logs whisperengine-elena-bot --tail 500 2>&1 | grep "POSTGRES FACTS"

# Troubleshooting:
# - Check knowledge_router initialization
# - Verify PostgreSQL pool is connected
# - Check bot logs for initialization errors
```

**2. Duplicate Entity Storage:**
```bash
# Check if entities are STILL being combined
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT entity_name, COUNT(*) as count
FROM fact_entities
WHERE entity_name LIKE '%and%'
GROUP BY entity_name
HAVING COUNT(*) > 1;
"

# Should return ZERO results (entities should be split)
```

**3. Missing Preferences:**
```bash
# Verify preferences are storing
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "
SELECT COUNT(*) FROM universal_users WHERE preferences IS NOT NULL;
"

# Should grow over time as users introduce themselves
```

## 🎯 Success Criteria (Phase 2 Monitoring)

### Week 1 Validation (Oct 5-12, 2025)
- [ ] PostgreSQL retrieval logs appear consistently
- [ ] Entities stored separately (no "X and Y" combined entities)
- [ ] Preferences captured correctly (preferred_name, etc.)
- [ ] No PostgreSQL connection errors
- [ ] E2E test maintains 85%+ pass rate

### Month 1 Validation (Oct 5 - Nov 5, 2025)
- [ ] Performance stays in 2-5ms range
- [ ] Fact count grows with user interactions
- [ ] Conversation quality remains high
- [ ] No memory leaks or connection pool exhaustion
- [ ] PostgreSQL queries scale linearly with fact count

## 🔧 Troubleshooting Commands

### If PostgreSQL Retrieval Stops Working:
```bash
# 1. Check knowledge_router initialization
docker logs whisperengine-elena-bot 2>&1 | grep "SemanticKnowledgeRouter initialized"

# 2. Verify PostgreSQL connection
docker logs whisperengine-elena-bot 2>&1 | grep "PostgreSQL pool initialized"

# 3. Test direct PostgreSQL connection
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "SELECT version();"

# 4. Restart bot if needed
./multi-bot.sh restart elena
```

### If Facts Not Storing:
```bash
# 1. Check for extraction errors
docker logs whisperengine-elena-bot 2>&1 | grep "KNOWLEDGE: Stored fact"

# 2. Verify semantic_router is working
docker logs whisperengine-elena-bot 2>&1 | grep "semantic_router"

# 3. Check for PostgreSQL errors
docker logs whisperengine-multi-postgres 2>&1 | grep -i error | tail -20
```

## 📝 Monitoring Checklist

### Daily (Automated - Add to Cron)
```bash
#!/bin/bash
# scripts/monitor_postgres_facts.sh

echo "=== PostgreSQL Fact Storage Health Check ==="
echo "Date: $(date)"
echo ""

# Check retrieval is working
echo "Recent PostgreSQL retrievals:"
docker logs whisperengine-elena-bot --tail 100 2>&1 | grep "POSTGRES FACTS" | tail -3

# Count facts
echo ""
echo "Total facts stored:"
docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine -t -c "SELECT COUNT(*) FROM user_fact_relationships;"

# Check for errors
echo ""
echo "Recent errors (should be empty):"
docker logs whisperengine-elena-bot --tail 100 2>&1 | grep -i "error.*postgres" | tail -3

echo ""
echo "=== Health Check Complete ==="
```

### Weekly (Manual)
- [ ] Run E2E test suite
- [ ] Review PostgreSQL query performance
- [ ] Check fact storage accuracy
- [ ] Verify preference storage
- [ ] Review bot conversation quality

### Monthly (Manual)
- [ ] Analyze performance trends
- [ ] Review storage growth
- [ ] Check for optimization opportunities
- [ ] Validate fallback behavior
- [ ] Update monitoring thresholds

## 📊 Data Points to Collect

### For Future Optimization Decisions
1. **Query Performance Distribution**: How often are queries <5ms vs >5ms?
2. **Fact Growth Rate**: How many facts per day per user?
3. **Retrieval Success Rate**: What % of queries find facts?
4. **Conversation Impact**: Do retrieved facts improve response quality?
5. **Storage Overhead**: Is dual storage causing issues?

### SQL Queries for Data Collection
```sql
-- Query performance analysis (manual timing)
EXPLAIN ANALYZE
SELECT fe.entity_name, ufr.relationship_type
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'test_user'
  AND ufr.confidence >= 0.5;

-- Fact growth over time
SELECT 
  DATE(created_at) as date,
  COUNT(*) as new_facts
FROM user_fact_relationships
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Entity type distribution
SELECT 
  entity_type,
  COUNT(*) as count,
  AVG(confidence) as avg_confidence
FROM fact_entities fe
JOIN user_fact_relationships ufr ON fe.id = ufr.entity_id
GROUP BY entity_type
ORDER BY count DESC;
```

## 🚀 Future Decisions

### When to Execute Phase 1 Migration
**Consider migrating IF:**
- ✅ Phase 2 runs successfully for 30+ days
- ✅ No PostgreSQL performance issues
- ✅ Storage overhead becomes problematic
- ✅ Moving to production environment
- ✅ Need to simplify architecture

**Skip migration IF:**
- ✅ Dev/test environment only (current state)
- ✅ Dual storage not causing issues
- ✅ Want to keep fallback option
- ✅ Prioritizing other features

### Current Recommendation
**SKIP Phase 1 migration** - Reasons:
- Development/test environment
- Dual storage overhead acceptable
- PostgreSQL working correctly
- No production users
- Focus on feature development

---

## 🎯 Summary

**Current State**: Phase 2 deployed and working (92.9% test pass rate)  
**Monitoring Approach**: Passive observation, no active migration  
**Success Metrics**: PostgreSQL retrieval working, facts stored correctly, performance excellent  
**Next Steps**: Continue development, monitor passively, revisit migration decision if moving to production

**Phase 1 Migration**: DEFERRED - Not needed in dev/test environment
