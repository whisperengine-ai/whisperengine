# 🔧 Web UI Personality Restoration - Common Issues

Quick fixes for problems you might encounter.

---

## Issue: Can't Access Web UI

**Problem:** Browser shows "Can't connect" or "Site not found"

**Solutions:**

1. **Check if Web UI is running:**
   - Look for a terminal/command window with "Next.js" or "Ready in" messages
   - If not running, ask technical person to start it

2. **Try different URLs:**
   - `http://localhost:3000`
   - `http://127.0.0.1:3000`
   - `http://[your-server-ip]:3000`

3. **Ask tech person:** "Can you start the CDL Web UI at port 3000?"

---

## Issue: "AI Assistant" Not in Character List

**Problem:** Can't find the assistant character to edit

**Solutions:**

1. **Scroll down** - it might be below visible area
2. **Check character name** - might be listed as "Default Assistant" or "WhisperEngine Assistant"
3. **Look for normalized_name** - should say "assistant" underneath
4. **Search box** - if there's a search, type "assistant"

**Still not there?** You need to run the SQL script instead (see other guide).

---

## Issue: Can't Find Personality Tab

**Problem:** No tab labeled "Personality" at the top

**Solutions:**

1. **Make sure you OPENED the character**
   - You need to CLICK on "AI Assistant" in the list
   - Don't just hover - actually click it
   - Should open a detail page with tabs at the top

2. **Look for these tabs:**
   - Basic
   - Personality ← You want this one
   - Background
   - Interests
   - Communication
   - Speech
   - Responses
   - Preview

3. **Wrong page?**
   - If you see a LIST of characters, click on one
   - If you see "Create Character" form, go back to characters page

---

## Issue: Sliders Won't Move

**Problem:** Can't adjust personality sliders

**Solutions:**

1. **Click and drag** (don't just tap)
2. **Try arrow keys** after clicking slider
3. **Try different browser** (Chrome, Firefox, Safari)
4. **Refresh page** and try again (F5 or Cmd+R)

---

## Issue: Can't Add Communication Patterns

**Problem:** "Add Communication Pattern" button doesn't work

**Solutions:**

1. **Fill all required fields FIRST:**
   - Pattern Type (dropdown)
   - Pattern Name (text)
   - Pattern Value (text)
   - Frequency (dropdown)

2. **Then click "Add"** (not "Save" yet)

3. **Pattern should appear in list below**

4. **THEN click "Save"** at bottom to save all patterns

**Correct order:**
1. Fill form
2. Click "Add" → pattern appears in list
3. Fill form again for next pattern
4. Click "Add" → second pattern appears
5. After adding all patterns → Click "Save"

---

## Issue: Save Button Grayed Out

**Problem:** Can't click the Save button

**Solutions:**

1. **Fill required fields:**
   - Look for red asterisks (*) or red borders
   - All required fields must have values

2. **Wait for form to load:**
   - Sometimes takes 2-3 seconds
   - Wait for spinning icon to stop

3. **Check for error messages:**
   - Red text near fields
   - Fix those errors first

---

## Issue: "Saved Successfully" But Nothing Changed

**Problem:** Save seems to work but data disappears on refresh

**Solutions:**

1. **Check browser console:**
   - Press F12 → look for red errors
   - Take screenshot and share with tech person

2. **Database connection issue:**
   - Web UI might not be connected to database
   - Ask tech person: "Is the Web UI connected to the database?"

3. **Try the SQL script instead:**
   - This means Web UI has a problem
   - Use the SQL migration script (see other guide)

---

## Issue: Added Values/Patterns But Don't See Them

**Problem:** Items disappear after adding them

**Solutions:**

1. **Did you click "Add" button?**
   - Typing in form doesn't add it
   - MUST click "Add" to add to list
   - THEN click "Save" to save to database

2. **Scroll down to see list:**
   - Added items appear below the form
   - Might need to scroll

3. **Check you're on right tab:**
   - Communication patterns → Communication tab
   - Speech patterns → Speech tab
   - Response items → Responses tab

---

## Issue: Bot Still Generic After Restart

**Problem:** Completed all steps but bot hasn't changed

**Solutions:**

1. **Wait 30-60 seconds after restart:**
   - Bot needs time to reload from database
   - Don't test immediately

2. **Verify you clicked Save on EVERY tab:**
   - Go back through each tab
   - Look for "Saved" checkmark or timestamp
   - Re-save if unsure

3. **Check bot name in environment:**
   - Bot's DISCORD_BOT_NAME must be "assistant"
   - Ask tech person: "Is DISCORD_BOT_NAME set to 'assistant'?"

4. **Check startup logs:**
   - Should see: "✅ Character system initialized for bot: assistant"
   - Should NOT see: "⚠️ No character personality found"

5. **Try clearing browser cache:**
   - Might have old cached data
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

---

## Issue: Made Mistake - Want to Start Over

**Problem:** Entered wrong values and want to redo

**Solutions:**

**To fix one item:**
1. Find the item in the list
2. Click "Edit" or trash icon
3. Re-enter correct values
4. Click "Save"

**To start completely over:**
1. Delete all added patterns/items (trash icons)
2. Click "Save" to remove them from database
3. Start again from Step 1 of main guide

**Can't delete?**
- Use SQL script to reset (ask tech person)
- Or just overwrite by editing existing items

---

## Issue: Web UI Looks Different Than Guide

**Problem:** UI doesn't match screenshots/descriptions

**Solutions:**

1. **Check WhisperEngine version:**
   - This guide is for v1.0.24+
   - Earlier versions have different UI

2. **Update to latest version:**
   - Ask tech person to update WhisperEngine
   - Then try guide again

3. **Use SQL script instead:**
   - If UI is very different, use SQL migration
   - See file: `sql/migrations/fix_assistant_personality_v106_to_v124.sql`

---

## Issue: Numbers/Percentages Confusing

**Problem:** Guide says "80%" but slider shows "0.8"

**Solutions:**

- **Same thing!** Just different format:
  - 80% = 0.8
  - 90% = 0.9
  - 70% = 0.7
  - 20% = 0.2

- **Use this conversion:**
  - If slider shows decimals → divide percentage by 100
  - If slider shows percentage → use the percentage directly

---

## 🆘 When to Ask for Help

**Ask technical person if:**
- Web UI won't start at all
- Database connection errors appear
- Save button never works after multiple tries
- Bot still generic after completing ALL steps and waiting 5 minutes
- You see red error messages you can't understand

**What to share with them:**
1. Screenshot of each completed tab
2. Any red error messages
3. Which step you're stuck on
4. Browser you're using (Chrome, Firefox, etc.)
5. Say: "I'm following the Web UI personality restoration guide"

---

## ✅ Success Indicators

**You know it worked when:**

1. Each tab shows "Saved successfully" or green checkmark
2. Lists show your added items after clicking "Add"
3. After bot restart, assistant responds with:
   - Warm, professional tone
   - Clear, helpful explanations
   - Consistent personality (not generic)

**Before/After example:**

❌ **Before:** "I'm an AI assistant. How can I help?"  
✅ **After:** "I'm doing well, thank you! I'm here and ready to help with whatever you need today."

---

**Remember:** This is safe to do! You can't break anything. Worst case, just re-enter the data. 💪
