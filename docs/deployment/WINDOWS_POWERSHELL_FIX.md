# Windows PowerShell Setup Fix - Implementation Summary

## Problem Reported

User on Windows PowerShell encountered this error:
```
curl: option : blank argument where content is expected
curl: try 'curl --help' for more information
```

When trying to run:
```
curl --help
```

Got:
```
curl : The remote name could not be resolved: '--help'
```

## Root Cause

**Windows PowerShell has `curl` as an alias for `Invoke-WebRequest`**, not the actual curl command-line tool.

When users see documentation showing:
```bash
curl -sSL https://example.com/script.sh | bash
```

And try to run it in PowerShell, it fails because:
1. PowerShell's `Invoke-WebRequest` doesn't understand Unix curl flags (`-s`, `-S`, `-L`)
2. The pipe syntax doesn't work the same way
3. Users get confusing error messages

## Solution Implemented

### 1. Created Native PowerShell Setup Script

**New File:** `setup-containerized.ps1`

Features:
- ✅ Native PowerShell syntax (`Invoke-WebRequest`, `Start-Process`, etc.)
- ✅ Proper error handling with try/catch
- ✅ Colored output with `Write-Host`
- ✅ Windows-friendly file operations
- ✅ Automatic browser opening
- ✅ No curl alias conflicts

### 2. Updated All Documentation

**Files Updated:**
- `README.md` - Changed PowerShell command to use `.ps1` script
- `QUICK_REFERENCE.md` - Updated PowerShell setup command
- `docs/deployment/CLEANUP_SCRIPTS.md` - Updated setup commands
- `docs/deployment/ONE_LINER_COMMANDS.md` - Added note about curl alias

**Pattern Applied:**
```powershell
# OLD (BROKEN in PowerShell):
curl -sSL https://.../setup-containerized.bat -o setup.bat && setup.bat

# NEW (WORKS in PowerShell):
Invoke-WebRequest -Uri "https://.../setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

### 3. Created Comprehensive Troubleshooting Doc

**New File:** `docs/troubleshooting/WINDOWS_POWERSHELL_SETUP.md`

Covers:
- Detailed explanation of curl alias issue
- 4 different solutions (native script, CMD, remove alias, curl.exe)
- Complete setup commands for both PowerShell and CMD
- Verification steps
- Why this happens (educational)
- Additional resources

## Updated Commands

### Setup Commands (All Platforms)

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

**Windows (PowerShell - Recommended):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

**Windows (Command Prompt):**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

### Cleanup Commands (Already Working)

Cleanup scripts were already PowerShell-native, so no changes needed.

## Benefits

### For Windows PowerShell Users
✅ No more curl alias confusion
✅ Native PowerShell experience
✅ Proper error messages
✅ Works out of the box
✅ No need to install curl.exe

### For Command Prompt Users
✅ Existing `.bat` script still works
✅ Can continue using CMD if preferred

### For Support
✅ Clear documentation of the issue
✅ Multiple solution paths
✅ Educational content for users
✅ Reduces GitHub issues about setup failures

## File Structure

```
whisperengine/
├── setup-containerized.sh        # Linux/macOS (existing)
├── setup-containerized.bat       # Windows CMD (existing)
├── setup-containerized.ps1       # Windows PowerShell (NEW)
├── README.md                     # Updated PowerShell command
├── QUICK_REFERENCE.md            # Updated PowerShell command
└── docs/
    ├── deployment/
    │   ├── CLEANUP_SCRIPTS.md           # Updated setup commands
    │   └── ONE_LINER_COMMANDS.md        # Updated with note
    └── troubleshooting/
        ├── README.md                     # General troubleshooting
        └── WINDOWS_POWERSHELL_SETUP.md  # NEW: PowerShell-specific help
```

## Testing Checklist

Before deploying, test on Windows:

- [ ] PowerShell 5.1 (Windows 10 default)
- [ ] PowerShell 7+ (modern)
- [ ] Command Prompt (verify .bat still works)
- [ ] Verify download from GitHub raw URL works
- [ ] Verify script executes without errors
- [ ] Verify Docker containers start successfully
- [ ] Verify browser opens automatically
- [ ] Test on clean Windows system (no repo cloned)

## Deployment Steps

1. **Commit all changes:**
   ```bash
   git add setup-containerized.ps1 README.md QUICK_REFERENCE.md docs/
   git commit -m "Fix: Add native PowerShell setup script for Windows users"
   ```

2. **Push to GitHub:**
   ```bash
   git push origin main
   ```

3. **Verify GitHub raw URL works:**
   - Test: https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1
   - Should download the PowerShell script

4. **Update any external documentation:**
   - Website setup instructions
   - Discord/community announcements
   - Support documentation

## User Communication

Suggested message for users experiencing this issue:

---

**Windows PowerShell Setup Issue - SOLVED**

If you're seeing curl errors in PowerShell, use this updated command:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

This uses a native PowerShell script that avoids the curl alias issue.

Full documentation: [Windows PowerShell Setup Guide](docs/troubleshooting/WINDOWS_POWERSHELL_SETUP.md)

---

## Additional Notes

### Why Not Fix the Batch Script?

The `.bat` script already works fine in Command Prompt. The issue is specifically with PowerShell's curl alias when trying to use Unix-style curl commands.

### Why Three Setup Scripts?

- **`.sh`** - Native Bash for Linux/macOS
- **`.bat`** - Native Batch for Windows CMD
- **`.ps1`** - Native PowerShell for Windows PowerShell

Each uses platform-native syntax for best reliability and user experience.

### Alternative Approaches Considered

1. **Single cross-platform script** - Too complex, hard to maintain
2. **Detect and remove curl alias** - Too invasive, affects user's session
3. **Force curl.exe usage** - Requires curl.exe to be installed
4. **Python-based installer** - Requires Python installation

**Decision:** Platform-native scripts provide the best user experience.

## Related Issues

This fix resolves:
- Windows PowerShell curl alias conflicts
- Setup script download failures on Windows
- Confusing error messages for Windows users
- Need for workarounds or manual setup

## Success Metrics

Implementation is successful if:
✅ Windows PowerShell users can run setup without errors
✅ Reduced GitHub issues about Windows setup failures
✅ Clear documentation prevents confusion
✅ Users understand which command to use on their platform
✅ Setup works on fresh Windows installations without modifications
