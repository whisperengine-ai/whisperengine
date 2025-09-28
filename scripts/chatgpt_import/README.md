# ChatGPT Import Guide - Docker Method (Recommended)

This guide walks you through importing your ChatGPT conversation history into WhisperEngine using Docker. The Docker method is recommended because it handles all dependencies automatically and runs in an isolated environment.

## 🎯 What This Does

This tool imports your ChatGPT conversations into WhisperEngine, allowing the AI to:
- **Remember your conversation history** from ChatGPT
- **Understand your communication style** and preferences  
- **Reference past topics** you've discussed
- **Provide more personalized responses** based on your history

## 📋 Prerequisites (What You Need)

### 1. Get Your ChatGPT Export File
**This is the most important step!**

1. **Login to ChatGPT**: Go to [ChatGPT](https://chat.openai.com)
2. **Access Settings**: Click your profile picture → Settings
3. **Request Export**: 
   - Go to "Data Controls" → "Export Data"
   - Click "Export" button
   - **Wait for email** (can take up to 30 days!)
4. **Download**: When you get the email, download the ZIP file
5. **Extract**: Unzip the file and find `conversations.json`
6. **Save Location**: Put the file somewhere easy to find (like Desktop or Downloads)

### 2. Get Your Discord User ID
**This tells WhisperEngine which user the conversations belong to.**

1. **Enable Developer Mode**: 
   - Open Discord → Settings (gear icon)
   - Go to "Advanced" → Turn ON "Developer Mode"
2. **Copy Your ID**:
   - Right-click your username anywhere in Discord
   - Click "Copy User ID" 
   - You'll get a long number like `672814231002939413`

### 3. WhisperEngine Setup
- WhisperEngine must be **already installed and working**
- Docker must be **running on your computer**
- The WhisperEngine database should be **set up and accessible**

## �️ Troubleshooting Common Issues

### Problem: "File not found" Error
**Solution:**
1. **Check file path**: Make sure the path to `conversations.json` is correct
2. **Use full path**: Try using the complete file path instead of relative paths
3. **Check file name**: Ensure the file is named exactly `conversations.json`

```bash
# Check if file exists
ls -la /path/to/conversations.json

# If file exists, try full path
./multi-bot.sh import-chatgpt /full/path/to/conversations.json 672814231002939413
```

### Problem: "Permission denied" Error
**Solution:**
```bash
# Make sure bot.sh is executable
chmod +x bot.sh

# Try with sudo if needed (be careful!)
sudo ./multi-bot.sh import-chatgpt /path/to/conversations.json 672814231002939413
```

### Problem: "Docker not running" Error
**Solution:**
1. **Start Docker**: Make sure Docker Desktop is running
2. **Check services**: Verify WhisperEngine containers are up
```bash
# Check if Docker is running
docker ps

# Start WhisperEngine if needed
docker compose up -d

# Check service status
docker compose ps
```

### Problem: "Invalid User ID" Error
**Solution:**
- **Double-check ID**: Discord User IDs are 17-19 digit numbers
- **No quotes needed**: Use the number directly, without quotes
- **Copy carefully**: Make sure you copied the complete ID

### Problem: Import Seems Stuck
**Solution:**
1. **Be patient**: Large files can take time (1,000+ conversations = 10+ minutes)
2. **Check progress**: Look for progress messages in the output
3. **Interrupt safely**: Use `Ctrl+C` to stop if needed

```bash
# Check if import is still running
docker compose logs whisperengine-bot --tail=50

# If stuck, restart and try smaller batch
docker compose restart whisperengine-bot
```

### Problem: "Database connection failed"
**Solution:**
1. **Check environment**: Make sure `.env` file is properly configured
2. **Restart services**: Sometimes database connections timeout
```bash
# Restart all services
docker compose down
docker compose up -d

# Wait for services to fully start (30-60 seconds)
sleep 60

# Try import again
./multi-bot.sh import-chatgpt /path/to/conversations.json 672814231002939413
```

### Problem: File Format Issues
**Error messages like**: `Invalid JSON format`, `Unexpected file structure`

**Solution:**
1. **Check file size**: Make sure the file isn't corrupted (should be several MB for active users)
2. **Verify format**: Open the file and check it starts with `[` and contains conversation objects
3. **Re-download**: If file seems wrong, request a new export from ChatGPT

## 💡 Tips for Success

### Before Starting:
- ✅ **Backup first**: WhisperEngine will create a backup, but be safe
- ✅ **Free space**: Ensure you have enough disk space (exports can be large)
- ✅ **Stable internet**: For Docker image downloads if needed
- ✅ **Close ChatGPT**: Make sure you're not actively using ChatGPT during import

### During Import:
- ⏰ **Be patient**: Large files take time (plan for 30+ minutes for heavy users)
- 👀 **Watch output**: Look for error messages or progress updates
- 🔋 **Keep computer awake**: Don't let your computer sleep during import

### After Import:
- 🧪 **Test memory**: Ask WhisperEngine about something from your ChatGPT history
- 📊 **Check counts**: Use Discord commands to verify conversation count
- 🔍 **Search test**: Try searching for specific topics you discussed

## 🔧 Advanced Options

### Import Specific Date Range
```bash
# Only import conversations from 2024
docker compose exec whisperengine-bot python scripts/chatgpt_import/import_chatgpt.py \
  --file /path/to/conversations.json \
  --user-id 672814231002939413 \
  --start-date 2024-01-01 \
  --end-date 2024-12-31
```

### Skip Certain Conversation Types
```bash
# Skip short conversations (less than 5 messages)
docker compose exec whisperengine-bot python scripts/chatgpt_import/import_chatgpt.py \
  --file /path/to/conversations.json \
  --user-id 672814231002939413 \
  --min-messages 5
```

### Batch Processing for Large Files
```bash
# Process in smaller chunks to avoid timeouts
docker compose exec whisperengine-bot python scripts/chatgpt_import/import_chatgpt.py \
  --file /path/to/conversations.json \
  --user-id 672814231002939413 \
  --batch-size 50 \
  --verbose
```

## 📞 Getting Help

If you're still having trouble:

1. **Check logs**: Look at WhisperEngine logs for detailed error messages
```bash
docker compose logs whisperengine-bot --tail=100
```

2. **Join Discord**: Ask for help in the WhisperEngine support channels

3. **Create issue**: Report bugs on the GitHub repository with:
   - Your operating system
   - Docker version (`docker --version`)
   - Complete error message
   - Size of your ChatGPT export file

## Export Process

### Method 1: Simple One-Command Import (Easiest)

**Step 1**: Open your terminal/command prompt and navigate to WhisperEngine folder:
```bash
cd /path/to/whisperengine
```

**Step 2**: Run the import using our bot management script:
```bash
./multi-bot.sh import-chatgpt /path/to/conversations.json 672814231002939413
```

**Replace these parts:**
- `/path/to/conversations.json` → actual path to your ChatGPT file
- `672814231002939413` → your actual Discord User ID

**Example with real paths:**
```bash
# If your file is on Desktop (Mac/Linux)
./multi-bot.sh import-chatgpt ~/Desktop/conversations.json 672814231002939413

# If your file is in Downloads (Mac/Linux)  
./multi-bot.sh import-chatgpt ~/Downloads/conversations.json 672814231002939413

# Windows example
./multi-bot.sh import-chatgpt "C:\Users\YourName\Desktop\conversations.json" 672814231002939413
```

### Method 2: Direct Docker Command (More Control)

**Step 1**: Start WhisperEngine services:
```bash
docker compose up -d
```

**Step 2**: Run the import command:
```bash
docker compose exec whisperengine-bot python scripts/chatgpt_import/import_chatgpt.py \
  --file /path/to/conversations.json \
  --user-id 672814231002939413 \
  --verbose
```

### Method 3: Test First (Recommended for Large Files)

**Step 1**: Test the import without actually saving (dry run):
```bash
docker compose exec whisperengine-bot python scripts/chatgpt_import/import_chatgpt.py \
  --file /path/to/conversations.json \
  --user-id 672814231002939413 \
  --dry-run --verbose
```

**Step 2**: If test looks good, run the real import:
```bash
docker compose exec whisperengine-bot python scripts/chatgpt_import/import_chatgpt.py \
  --file /path/to/conversations.json \
  --user-id 672814231002939413 \
  --verbose
```

## 📊 What You'll See During Import

### Successful Import Output:
```
🔍 Analyzing ChatGPT export file...
✅ Found 45 conversations with 1,247 messages
🚀 Starting import process...
📝 Processing conversation 1/45...
📝 Processing conversation 10/45...
📝 Processing conversation 20/45...
...
✅ Import completed successfully!

📊 IMPORT SUMMARY:
   💬 Conversations imported: 45
   📨 Messages processed: 1,247  
   👤 User ID: 672814231002939413
   ⏱️  Total time: 2m 34s
   
🧠 Memory integration complete!
🔍 Your ChatGPT history is now searchable in WhisperEngine
```

### Test Run (Dry Run) Output:
```
🧪 DRY RUN MODE - No data will be saved
🔍 Analyzing ChatGPT export file...
✅ Found 45 conversations with 1,247 messages
📋 Would import:
   📅 Date range: 2023-01-15 to 2024-09-19
   💬 Conversation topics: AI development, cooking, travel planning...
   🗣️  Your common questions: "How do I...", "Can you help with...", "Explain..."
   
✅ File format is valid and ready for import!
💡 Run without --dry-run to perform actual import
```

## Prerequisites

1. **WhisperEngine Setup**: Ensure WhisperEngine is properly configured
2. **Environment**: Valid `.env` file with database credentials
3. **ChatGPT Export**: Download your `conversations.json` from ChatGPT
4. **User ID**: Discord user ID for associating conversations

## Getting Your ChatGPT Export

1. Go to ChatGPT Settings → Data Controls → Export Data
2. Wait for the export email (can take up to 30 days)
3. Download and extract the ZIP file
4. Locate `conversations.json` in the extracted folder

## Getting Your Discord User ID

1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click your username and select "Copy User ID"
3. Use this ID in the import command

## Usage Examples

### Basic Import
```bash
./scripts/chatgpt_import/import_chatgpt.sh ~/Downloads/conversations.json 123456789012345678
```

### Import with Verbose Logging
```bash
python scripts/chatgpt_import/import_chatgpt.py \
  --file conversations.json \
  --user-id 123456789012345678 \
  --verbose
```

### Docker Import (for isolated environments)
```bash
python scripts/chatgpt_import/docker_import.py \
  --file ~/Downloads/conversations.json \
  --user-id 123456789012345678 \
  --verbose
```

## What Gets Imported

- **User Messages**: Your prompts and questions to ChatGPT
- **Assistant Responses**: ChatGPT's replies and responses
- **Timestamps**: Original conversation timestamps are preserved
- **Conversation Context**: Messages are grouped by conversation threads
- **Metadata**: Source tracking and import information

## How It Works

1. **Parse Export**: Reads and validates the ChatGPT export format
2. **Extract Conversations**: Identifies conversation threads and messages
3. **Convert Format**: Transforms ChatGPT messages to WhisperEngine format
4. **Store Messages**: Saves through WhisperEngine's memory pipeline
5. **Generate Analysis**: Creates insights about imported conversation patterns

## Supported ChatGPT Export Formats

The importer handles various ChatGPT export formats:

- **Tree Structure**: ChatGPT's native message tree format
- **Linear Messages**: Simple message arrays
- **Nested Conversations**: Various conversation object structures
- **Legacy Formats**: Older ChatGPT export versions

## Output and Results

After successful import, you'll see:

```
✅ Import completed successfully!
📊 Conversations imported: 45
💬 Messages processed: 1,247
👤 User ID: 123456789012345678
```

## Integration with WhisperEngine

Imported conversations integrate seamlessly with WhisperEngine:

- **Memory System**: Messages stored in ChromaDB with proper indexing
- **Personality Analysis**: Conversation patterns analyzed for insights
- **Emotional Context**: Imported messages contribute to emotion tracking
- **Search & Retrieval**: Imported content becomes searchable
- **Conversation Flow**: Maintains chronological conversation history

## Troubleshooting

### Common Issues

**File Not Found**
```bash
❌ Error: File conversations.json not found
```
- Verify the file path is correct
- Use absolute paths if relative paths fail

**Invalid User ID**
```bash
❌ Error: Invalid user ID format
```
- Ensure you're using a Discord user ID (18-digit number)
- Check that Developer Mode is enabled in Discord

**ChromaDB Connection Error**
```bash
❌ ChromaDB server is not available
```
- Start the database: `docker compose up chromadb`
- Check `.env` file has correct database settings

**Docker Image Not Found**
```bash
❌ Docker image whisperengine:latest not found
```
- Build the image: `docker compose build`
- Or use direct Python method instead

### Performance Notes

- Large exports (>1000 conversations) may take several minutes
- Progress is logged every 10 conversations
- Memory analysis runs automatically after import
- Failed conversations are logged but don't stop the import

## 📚 Technical Reference (For Advanced Users)

### Available Command Line Options

#### Required Parameters:
- `--file` / `-f`: Path to your `conversations.json` file
- `--user-id` / `-u`: Your Discord User ID (long number)

#### Optional Parameters:
- `--verbose` / `-v`: Show detailed progress messages
- `--dry-run`: Test the import without saving anything
- `--batch-size`: Process conversations in chunks (default: 100)

#### Filtering Options:
- `--start-date`: Only import after this date (format: YYYY-MM-DD)
- `--end-date`: Only import before this date (format: YYYY-MM-DD)
- `--min-messages`: Skip conversations shorter than X messages
- `--max-messages`: Skip conversations longer than X messages

### Full Command Examples:

```bash
# Import only 2024 conversations
./multi-bot.sh import-chatgpt conversations.json 672814231002939413 \
  --start-date 2024-01-01 --end-date 2024-12-31

# Skip very short conversations (less than 3 messages)
./multi-bot.sh import-chatgpt conversations.json 672814231002939413 \
  --min-messages 3

# Process in smaller batches (good for slow computers)
./multi-bot.sh import-chatgpt conversations.json 672814231002939413 \
  --batch-size 25 --verbose
```

### Understanding the Process

When you run the import, here's what happens:

1. **File Validation**: Checks if your `conversations.json` file is valid
2. **Conversation Parsing**: Reads through all your ChatGPT conversations
3. **Filtering**: Applies any date/size filters you specified
4. **Memory Integration**: Stores conversations in WhisperEngine's memory system
5. **Embedding Generation**: Creates searchable representations of your conversations
6. **Completion**: Provides summary of what was imported

### Legacy Methods (Alternative Approaches)

#### Method A: Direct Python Script
```bash
# Navigate to WhisperEngine folder
cd /path/to/whisperengine

# Run the Python script directly
python scripts/chatgpt_import/import_chatgpt.py \
  --file /path/to/conversations.json \
  --user-id 672814231002939413 \
  --verbose
```

#### Method B: Simple Bash Script
```bash
# Make script executable (one time only)
chmod +x scripts/chatgpt_import/import_chatgpt.sh

# Run the import
./scripts/chatgpt_import/import_chatgpt.sh conversations.json 672814231002939413
```

#### Method C: Docker Wrapper Script
```bash
python scripts/chatgpt_import/docker_import.py \
  --file /path/to/conversations.json \
  --user-id 672814231002939413 \
  --verbose
```

### Environment Variables (For Developers)

These environment variables can customize the import behavior:

- `OPENAI_API_KEY`: For enhanced conversation analysis
- `DATABASE_URL`: Custom database connection
- `CHROMA_PATH`: Vector database storage location
- `LOG_LEVEL`: Control logging detail (DEBUG, INFO, WARNING, ERROR)

## 🎉 After Import: What Next?

### Test Your Import
Once import is complete, test that it worked:

1. **Start WhisperEngine**: Make sure the bot is running
2. **Join Discord**: Go to your Discord server where WhisperEngine is active
3. **Test Memory**: Ask about something you discussed in ChatGPT:
   ```
   @WhisperEngine do you remember when I asked about Python programming?
   ```
4. **Check Statistics**: Use admin commands to see conversation counts:
   ```
   !memory stats
   ```

### What You Can Do Now
With your ChatGPT history imported, WhisperEngine can:

- 🧠 **Remember your preferences**: Coding style, communication preferences, interests
- 🔍 **Reference past topics**: "Like we discussed before about X..."
- 🎯 **Provide personalized responses**: Based on your conversation patterns
- 📈 **Learn your style**: How you ask questions and prefer answers

### Managing Your Imported Data
```bash
# View memory statistics
!memory user stats

# Search your imported conversations
!memory search "topic you discussed"

# Clear specific conversations if needed (be careful!)
!memory clear --confirm
```

---

## 📝 Summary

**The easiest way to import your ChatGPT history:**

1. **Get your file**: Export from ChatGPT → download → unzip → find `conversations.json`
2. **Get your Discord ID**: Discord Settings → Advanced → Developer Mode → Right-click username → Copy User ID
3. **Run one command**: `./multi-bot.sh import-chatgpt /path/to/conversations.json YOUR_DISCORD_ID`
4. **Wait patiently**: Large files take time, but you'll see progress messages
5. **Test it works**: Ask WhisperEngine about something from your ChatGPT history

Need help? Check the troubleshooting section above or ask for support in Discord!

## Security Considerations

- Conversations are stored locally in your WhisperEngine instance
- No data is sent to external services during import
- Original ChatGPT export file is not modified
- Import metadata includes source tracking for transparency

## Development Notes

The import system follows WhisperEngine's architecture:

- **Error Handling**: Uses WhisperEngine's error management patterns
- **Logging**: Integrates with WhisperEngine's logging system
- **Memory Integration**: Uses existing memory manager interfaces
- **Configuration**: Respects WhisperEngine environment settings

## Support

For issues or questions:

1. Check WhisperEngine logs for detailed error information
2. Verify your ChatGPT export file format
3. Ensure WhisperEngine is properly configured
4. Test with a smaller export file first

## License

This import tool is part of WhisperEngine and follows the same licensing terms.