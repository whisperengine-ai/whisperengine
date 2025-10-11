## 🧪 Discord Test Instructions

**Send this message to Dotty in Discord DM:**

```
I'll have a beer
```

**Expected Results:**
1. ✅ **Pattern Detection**: "i'll have (a |an )?(.*)" should match "beer"
2. ✅ **Context Extraction**: {drink_name: "beer", price: 4}
3. ✅ **Transaction Creation**: PostgreSQL transaction with pending state
4. ✅ **Prompt Injection**: LLM gets transaction context
5. ✅ **Character Response**: Dotty acknowledges the beer order with price mention

**Check logs after sending:**
```bash
docker logs whisperengine-dotty-bot --tail 50 | grep -E "(🎯|WORKFLOW|workflow|detected.*intent|pattern.*match)"
```

**Check database:**
```bash
docker exec -it whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "SELECT * FROM role_transactions WHERE bot_name = 'dotty' ORDER BY created_at DESC LIMIT 5;"
```

**Test Payment:**
After the beer order, send:
```
Here you go
```

This should trigger state transition from pending → completed.