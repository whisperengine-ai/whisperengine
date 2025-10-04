📝 **Discord Test Log - Beer Order**

**Message Sent**: "I'll have a beer"
**Expected**: drink_order workflow, {drink_name: "beer", price: 4}

**Test this in Discord DM to Dotty and record the response here**

Response: [PENDING - Send "I'll have a beer" to Dotty]

**Check logs after:**
```bash
docker logs whisperengine-dotty-bot --tail 50 | grep -E "(🎯|WORKFLOW|workflow|detected.*intent)"
```

**Check database:**
```bash
docker exec -it whisperengine-multi-postgres psql -U whisperengine -d whisperengine -c "SELECT * FROM role_transactions WHERE bot_name = 'dotty' ORDER BY created_at DESC LIMIT 3;"
```