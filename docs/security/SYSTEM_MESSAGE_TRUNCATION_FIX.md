# System Message Truncation Fix

## Problem
The system message was being truncated to 1,500 characters, causing warnings like:
```
custom-discord-bot  | 2025-09-11 00:19:52,936 - WARNING - System message truncated to 1500 characters
```

This was problematic because:
- Your `system_prompt.md` file is **7,528 characters** long
- Only ~20% of your system prompt was being used
- The truncation was happening in two places as a security measure

## Root Cause
Two hardcoded limits were too restrictive:

1. **`src/security/llm_message_role_security.py`**: Default `max_system_length = 1500`
2. **`src/llm/lmstudio_client.py`**: Hardcoded `MAX_SYSTEM_MESSAGE_LENGTH = 1500`

## Solution Applied
Made the system message length limit configurable and increased the default:

### Changes Made:

1. **Security Module** (`src/security/llm_message_role_security.py`):
   - Added environment variable support: `MAX_SYSTEM_MESSAGE_LENGTH`
   - Increased default from 1,500 to 8,000 characters
   - Made constructor parameter optional with env var fallback

2. **LLM Client** (`src/llm/lmstudio_client.py`):
   - Made `MAX_SYSTEM_MESSAGE_LENGTH` configurable via environment variable
   - Increased default from 1,500 to 8,000 characters

### Configuration Options:

**Option 1: Use defaults (recommended)**
- No configuration needed
- System messages up to 8,000 characters (sufficient for your 7,528 character prompt)

**Option 2: Custom limit via environment variable**
```bash
# Set in your environment or docker-compose.yml
export MAX_SYSTEM_MESSAGE_LENGTH=10000

# Or in docker-compose.yml:
environment:
  - MAX_SYSTEM_MESSAGE_LENGTH=10000
```

## Verification
After the fix:
- ✅ No more truncation warnings in logs  
- ✅ Full system prompt (7,528 chars) is processed without truncation
- ✅ Configurable via `MAX_SYSTEM_MESSAGE_LENGTH` environment variable
- ✅ Maintains security boundaries (still has a limit, just higher)

## Test Results
```bash
Current max_system_length: 8000
System prompt length: 7528 characters
Sanitized length: 7533 characters
Truncated: False
```

Your full Dream persona system prompt is now being used without truncation!
