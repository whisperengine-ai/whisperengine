# ChatGPT Import Tools for WhisperEngine

This directory contains tools to import ChatGPT conversation history into WhisperEngine's memory system, allowing users to transfer their conversation context and personality insights.

## Overview

The import system processes ChatGPT's conversation export format and stores messages through WhisperEngine's memory pipeline, preserving timestamps and conversation flow. This enables seamless migration of conversation history and personality continuity.

## Features

- **Format Detection**: Automatically handles different ChatGPT export formats
- **Timestamp Preservation**: Maintains original conversation chronology  
- **Memory Integration**: Uses WhisperEngine's existing memory pipeline
- **Progress Tracking**: Shows import progress for large files
- **Error Recovery**: Continues processing if individual conversations fail
- **Analysis**: Automatically analyzes imported data for insights
- **Flexible Deployment**: Works with both direct Python and Docker setups

## Files

- `importer.py` - Core ChatGPT import functionality
- `import_chatgpt.py` - Main CLI script for importing conversations
- `docker_import.py` - Docker wrapper for containerized imports
- `import_chatgpt.sh` - Simple bash convenience script
- `README.md` - This documentation

## Quick Start

### Method 1: Simple Bash Script (Recommended)

```bash
# Make the script executable (one time setup)
chmod +x scripts/chatgpt_import/import_chatgpt.sh

# Import your conversations
./scripts/chatgpt_import/import_chatgpt.sh conversations.json 123456789
```

### Method 2: Direct Python Script

```bash
python scripts/chatgpt_import/import_chatgpt.py --file conversations.json --user-id 123456789
```

### Method 3: Docker Container

```bash
python scripts/chatgpt_import/docker_import.py --file conversations.json --user-id 123456789
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