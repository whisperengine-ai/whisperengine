# Security Editing Protocol for AI Assistant

## 🔒 CRITICAL: Prevent Secret Leaks in Code Editing

### Before ANY file creation or editing operation:

1. **SCAN for secrets** in source content:
   - API keys (starts with `sk-`, `pk-`, etc.)
   - Tokens (JWT, Discord bot tokens, etc.) 
   - Passwords, credentials, connection strings
   - Private keys, certificates
   - Database URLs with credentials

2. **MASK or REMOVE secrets** before copying:
   - Replace with `[REDACTED]` or `***MASKED***`
   - Use placeholder values like `your-api-key-here`
   - Never copy actual secret values to new files

3. **VALIDATE destination**:
   - Is the target file in `.gitignore`?
   - Will it be committed to version control?
   - Could it be publicly accessible?

### Secret Detection Patterns:
```regex
- sk-[a-zA-Z0-9-_]{20,}     # API keys
- pk_[a-zA-Z0-9-_]{20,}     # Public keys  
- [A-Z0-9]{24}\.[A-Z0-9-_]{6}\.[A-Z0-9-_]{27}  # Discord tokens
- postgres://.*:.*@         # DB connection strings
- redis://.*:.*@            # Redis URLs with auth
- -----BEGIN.*KEY-----      # Private keys
```

### When handling .env files:
- NEVER copy actual secret values
- Use example/template values only
- Reference environment variable names, not values
- Document required variables without exposing values

## Emergency Protocol:
If a secret is accidentally exposed:
1. Immediately revoke/rotate the compromised secret
2. Remove from git history if committed
3. Update all systems using that secret
4. Review and improve detection methods