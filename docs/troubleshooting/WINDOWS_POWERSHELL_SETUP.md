# Windows PowerShell Setup Issues

## Common Problem: curl Command Errors

### Symptoms
When running setup commands in Windows PowerShell, you see errors like:
```
curl: option : blank argument where content is expected
curl: try 'curl --help' for more information
```

Or when trying `curl --help`:
```
curl : The remote name could not be resolved: '--help'
```

### Root Cause
**Windows PowerShell has `curl` as an alias for `Invoke-WebRequest`**, not the actual curl command-line tool. This causes Unix-style curl commands to fail.

When you run:
```powershell
curl -sSL https://example.com/script.sh | bash
```

PowerShell translates this to:
```powershell
Invoke-WebRequest -sSL https://example.com/script.sh | bash
```

Which fails because:
1. `Invoke-WebRequest` doesn't understand `-sSL` flags
2. The pipe to `bash` doesn't work the same way

### Solution 1: Use Native PowerShell Script (Recommended)

Use the **proper PowerShell setup command**:

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

This:
✅ Uses native PowerShell `Invoke-WebRequest`  
✅ Downloads the PowerShell-specific `.ps1` script  
✅ Runs with proper PowerShell syntax  

### Solution 2: Use Command Prompt Instead

If you prefer Command Prompt (CMD), use:

```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

CMD doesn't have the `curl` alias issue and uses the actual curl.exe if available.

### Solution 3: Remove curl Alias (Advanced)

If you really want to use the real curl.exe in PowerShell:

```powershell
# Remove the curl alias temporarily
Remove-Item alias:curl

# Now you can use real curl
curl.exe -sSL https://example.com/script.sh -o script.sh
```

**Note:** This only affects the current PowerShell session.

### Solution 4: Use curl.exe Explicitly

Call curl.exe directly instead of curl:

```powershell
curl.exe -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat
.\setup.bat
```

---

## Complete Setup Commands (Copy/Paste)

### ✅ Recommended: PowerShell Native Script
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

### ✅ Alternative: Command Prompt
Open Command Prompt (not PowerShell) and run:
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

---

## Complete Cleanup Commands (Copy/Paste)

### ✅ PowerShell Cleanup
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.ps1" -OutFile "cleanup.ps1"; .\cleanup.ps1
```

### ✅ Command Prompt Cleanup
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.bat -o cleanup.bat && cleanup.bat
```

---

## Why This Happens

PowerShell's `curl` alias exists for Unix compatibility, but it's actually `Invoke-WebRequest` with different syntax:

| Unix/Linux curl | PowerShell Invoke-WebRequest |
|-----------------|------------------------------|
| `curl -o file URL` | `Invoke-WebRequest -OutFile file -Uri URL` |
| `curl -L URL` | `Invoke-WebRequest -Uri URL` (follows redirects by default) |
| `curl -s URL` | `Invoke-WebRequest -UseBasicParsing -Uri URL` |
| `curl URL \| bash` | **Not supported** - need to save and execute |

---

## Verification

To check which curl you're using:

**In PowerShell:**
```powershell
Get-Command curl
```

Output will show:
```
CommandType     Name                                               
-----------     ----                                               
Alias           curl -> Invoke-WebRequest
```

**To use real curl.exe:**
```powershell
Get-Command curl.exe
```

Output will show actual curl if installed:
```
CommandType     Name                                               
-----------     ----                                               
Application     curl.exe
```

---

## Additional Resources

- **WhisperEngine Setup Guide**: [README.md](../../README.md)
- **General Troubleshooting**: [Troubleshooting Guide](README.md)
- **Cleanup Documentation**: [Cleanup Scripts](../deployment/CLEANUP_SCRIPTS.md)
- **Quick Reference**: [Quick Reference Card](../../QUICK_REFERENCE.md)

---

## Still Having Issues?

If you're still experiencing problems:

1. **Verify PowerShell version:**
   ```powershell
   $PSVersionTable.PSVersion
   ```
   Should be 5.1 or higher.

2. **Try Command Prompt instead:** CMD doesn't have these alias issues

3. **Check Docker is running:**
   ```powershell
   docker ps
   ```

4. **Report the issue:** https://github.com/whisperengine-ai/whisperengine/issues

Include:
- PowerShell version
- Windows version
- Complete error message
- What command you tried
