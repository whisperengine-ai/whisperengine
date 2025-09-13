# ChatGPT History Import Guide

This guide explains how to import ChatGPT conversation history into your bot's ChromaDB memory system.

## Overview

The `import_chatgpt_history.py` script allows you to import conversation history from ChatGPT exports into your bot's memory system. This enables the bot to have context about previous conversations a user had with ChatGPT.

## Getting ChatGPT Export Data

### From ChatGPT Web Interface:
1. Go to ChatGPT settings (click your profile in bottom left)
2. Navigate to "Data controls" 
3. Click "Export data"
4. Wait for the export email (usually takes a few minutes to hours)
5. Download and extract the ZIP file
6. Look for `conversations.json` in the extracted files

### Expected Format

The script supports multiple ChatGPT export formats:

#### Standard Format (with mapping):
```json
[
  {
    "id": "conversation-id-123",
    "title": "Conversation Title",
    "create_time": 1609459200,
    "update_time": 1609459800,
    "mapping": {
      "node-id-1": {
        "message": {
          "id": "message-id-1",
          "role": "user",
          "content": {
            "parts": ["User message content here"]
          },
          "create_time": 1609459200
        }
      },
      "node-id-2": {
        "message": {
          "id": "message-id-2",
          "role": "assistant",
          "content": {
            "parts": ["Assistant response here"]
          },
          "create_time": 1609459300
        }
      }
    }
  }
]
```

#### Simple Format (direct messages):
```json
{
  "conversations": [
    {
      "id": "conv-456",
      "title": "Simple Conversation",
      "messages": [
        {
          "role": "user", 
          "content": "User message"
        },
        {
          "role": "assistant", 
          "content": "Assistant response"
        }
      ]
    }
  ]
}
```

## Usage

### Basic Import
```bash
python import_chatgpt_history.py <user_id> <json_file>
```

### Examples

```bash
# Basic import for a Discord user
python import_chatgpt_history.py 123456789012345678 conversations.json

# Dry run to preview what would be imported
python import_chatgpt_history.py 123456789012345678 conversations.json --dry-run

# Import with custom channel ID
python import_chatgpt_history.py 123456789012345678 conversations.json --channel-id 987654321

# Import without automatic fact extraction
python import_chatgpt_history.py 123456789012345678 conversations.json --no-auto-facts

# Verbose output for debugging
python import_chatgpt_history.py 123456789012345678 conversations.json --verbose
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `user_id` | Discord user ID (required) - must be numeric |
| `json_file` | Path to ChatGPT export JSON file (required) |
| `--channel-id` | Channel ID to associate with imported conversations |
| `--chromadb-path` | Path to ChromaDB directory (default: `./chromadb_data`) |
| `--dry-run` | Preview import without storing data |
| `--no-auto-facts` | Disable automatic fact extraction |
| `--verbose` | Enable detailed logging |

## What Gets Imported

### Conversations
- User messages and ChatGPT responses are paired into conversation turns
- Each turn gets stored in ChromaDB with metadata including timestamps
- Channel ID is set to `chatgpt_import_{conversation_id}` unless specified

### Automatic Fact Extraction
By default, the script will extract facts from user messages:
- Personal information (age, location, occupation)
- Preferences (likes/dislikes)
- Relationships (family, pets)
- Hobbies and interests
- And more...

### What Gets Skipped
The script automatically filters out:
- Very short messages (less than 3 characters)
- System messages from ChatGPT
- Empty or whitespace-only content
- Error messages and disclaimers

## Testing

### Run Unit Tests
```bash
python test_chatgpt_import.py
```

### Create Sample Files for Testing
```bash
python test_chatgpt_import.py create-samples
```

This creates:
- `sample_chatgpt_standard.json` - Standard ChatGPT export format
- `sample_chatgpt_simple.json` - Simplified format

### Test with Sample Data
```bash
# Test dry run with sample data
python import_chatgpt_history.py 123456789012345678 sample_chatgpt_standard.json --dry-run --verbose
```

## Integration with Existing System

The imported conversations integrate seamlessly with your bot's existing memory system:

1. **Memory Retrieval**: The bot can retrieve imported ChatGPT conversations when building context
2. **Fact Extraction**: Facts extracted from ChatGPT conversations are stored alongside facts from Discord conversations
3. **Unified Storage**: All data uses the same ChromaDB format as native bot conversations

## Troubleshooting

### Common Issues

#### "Invalid JSON format"
- Ensure the file is valid JSON
- Check for truncated downloads
- Verify file encoding (should be UTF-8)

#### "No valid conversations found"
- Check if the JSON structure matches expected formats
- Use `--verbose` flag to see parsing details
- Verify the export file contains conversation data

#### "Invalid user ID format"
- User ID must be numeric (Discord user ID format)
- Remove any spaces or special characters

#### ChromaDB Connection Issues
- Ensure ChromaDB path exists and is writable
- Check if another process is using the database
- Verify Python dependencies are installed

### Getting Help

1. Use `--dry-run` first to preview imports
2. Enable `--verbose` for detailed logging
3. Check the console output for specific error messages
4. Verify your ChatGPT export format matches expected structure

## Data Privacy and Security

### Important Considerations
- ChatGPT conversations may contain sensitive personal information
- User IDs can identify specific Discord users
- Ensure compliance with privacy policies
- Secure any exported files appropriately
- Consider data retention policies

### Best Practices
- Review conversations before importing sensitive data
- Use dry-run mode to preview imports
- Regularly backup ChromaDB data
- Limit access to imported conversation data
- Document what data has been imported for each user

## Examples of What Gets Extracted

### Personal Information
From: "I'm 28 years old and work as a software engineer in Seattle"
- Fact: "is 28 years old"
- Fact: "works as software engineer"
- Fact: "lives in Seattle"

### Preferences
From: "I love playing guitar and hate doing laundry"
- Fact: "likes playing guitar"
- Fact: "dislikes doing laundry"

### Relationships
From: "My dog Max is a golden retriever"
- Fact: "has a dog named Max"

## File Structure

```
custom_bot/
├── import_chatgpt_history.py    # Main import script
├── test_chatgpt_import.py       # Test suite
├── CHATGPT_IMPORT_GUIDE.md      # This documentation
├── memory_manager.py            # Existing memory system
├── fact_extractor.py            # Automatic fact extraction
└── chromadb_data/               # ChromaDB storage directory
```

## Advanced Usage

### Custom Channel Mapping
You can map different ChatGPT conversations to different Discord channels:

```bash
# Process each conversation file separately with different channel IDs
python import_chatgpt_history.py 123456 work_conversations.json --channel-id 111111
python import_chatgpt_history.py 123456 personal_conversations.json --channel-id 222222
```

### Selective Import
For large exports, you might want to process conversations selectively:

1. Use dry-run to see what would be imported
2. Edit the JSON file to include only desired conversations
3. Run the actual import

### Batch Processing
For multiple users:

```bash
#!/bin/bash
# batch_import.sh
for user_file in exports/*.json; do
    user_id=$(basename "$user_file" .json)
    python import_chatgpt_history.py "$user_id" "$user_file"
done
```
