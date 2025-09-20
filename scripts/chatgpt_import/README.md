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

## 🚀 Step-by-Step Import Process

### Method 1: Simple One-Command Import (Easiest)

**Step 1**: Open your terminal/command prompt and navigate to WhisperEngine folder:
```bash
cd /path/to/whisperengine
```

**Step 2**: Run the import using our bot management script:
```bash
./bot.sh import-chatgpt /path/to/conversations.json 672814231002939413
```

**Replace these parts:**
- `/path/to/conversations.json` → actual path to your ChatGPT file
- `672814231002939413` → your actual Discord User ID

**Example with real paths:**
```bash
# If your file is on Desktop (Mac/Linux)
./bot.sh import-chatgpt ~/Desktop/conversations.json 672814231002939413

# If your file is in Downloads (Mac/Linux)  
./bot.sh import-chatgpt ~/Downloads/conversations.json 672814231002939413

# Windows example
./bot.sh import-chatgpt "C:\Users\YourName\Desktop\conversations.json" 672814231002939413
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