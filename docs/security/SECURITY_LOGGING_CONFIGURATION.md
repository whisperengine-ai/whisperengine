# 🛡️ Security Logging Configuration Guide

## Overview

The LLM Message Role Security system now supports configurable logging levels to reduce noise in production while maintaining security monitoring capabilities.

## Environment Variable Configuration

Set the `SECURITY_LOG_LEVEL` environment variable to control security logging verbosity:

```bash
# .env file
SECURITY_LOG_LEVEL=quiet    # Recommended for production
# SECURITY_LOG_LEVEL=normal  # Default development
# SECURITY_LOG_LEVEL=verbose # Debug/audit mode
```

## Logging Levels

### 🔇 **QUIET** (Production Recommended)
- **Purpose**: Minimal noise, only genuine security alerts
- **System Message Processing**: Silent for normal 3-5 system messages
- **Alerts Only When**: 
  - 6+ system messages (possible injection attack)
  - 8+ security events (high security activity)
- **Best For**: Production environments, stable deployments

### 📊 **NORMAL** (Development Default)
- **Purpose**: Balanced monitoring with optimization warnings  
- **System Message Processing**: Debug logging for normal operation
- **Alerts When**:
  - 5+ system messages (optimization suggestion)
  - 5+ security events (review recommended)
- **Best For**: Development, testing, initial deployments

### 🔍 **VERBOSE** (Debug/Audit Mode)
- **Purpose**: Complete security event visibility
- **System Message Processing**: Info level for all operations
- **Logs Everything**: All security events and processing steps
- **Best For**: Security audits, debugging, compliance monitoring

## Expected Behavior by Bot Architecture

### 🤖 **Normal Discord Bot Operation**
Your bot architecture typically creates **4-5 system messages** per conversation:

1. **Core System Prompt** - Character/personality definition
2. **Time Context** - "Current time: ..."  
3. **Emotional Context** - User relationship state
4. **Memory Context** - Previous conversation history
5. **AI Context** - Personality analysis, emotional intelligence

### 📊 **Logging Expectations by Level**

| Level | 3-4 System Messages | 5 System Messages | 6+ System Messages |
|-------|-------------------|-------------------|-------------------|
| **Quiet** | Silent | Silent | ⚠️ WARNING |
| **Normal** | 🐛 DEBUG | ⚠️ WARNING | ⚠️ WARNING |
| **Verbose** | ℹ️ INFO | ℹ️ INFO | ℹ️ INFO + ⚠️ WARNING |

## Security Events Count Reference

| Event Count | Meaning | Quiet | Normal | Verbose |
|-------------|---------|-------|--------|---------|
| 1-3 events | Normal security processing | Silent | 🐛 DEBUG | ℹ️ INFO |
| 4-5 events | Typical complex conversation | Silent | 🐛 DEBUG | ℹ️ INFO |
| 6-8 events | Higher complexity/optimization needed | Silent | ⚠️ WARNING | ℹ️ INFO |
| 9+ events | Potential security concern | ⚠️ WARNING | ⚠️ WARNING | ⚠️ WARNING |

## Configuration Examples

### Production Environment (.env)
```bash
# Minimal security logging
SECURITY_LOG_LEVEL=quiet
LOG_LEVEL=INFO
```

### Development Environment (.env)
```bash
# Balanced monitoring  
SECURITY_LOG_LEVEL=normal
LOG_LEVEL=DEBUG
```

### Security Audit/Debug (.env)
```bash
# Maximum visibility
SECURITY_LOG_LEVEL=verbose
LOG_LEVEL=DEBUG
```

## Implementation Benefits

### ✅ **Reduced Log Noise**
- **Before**: WARNING for every 4-5 system message conversation (normal)
- **After**: Silent operation for typical bot conversations

### 🛡️ **Maintained Security**
- All security protections remain active
- Genuine threats still trigger alerts
- Attack patterns still detected and logged

### 📈 **Scalable Monitoring**
- Production environments: clean logs, critical alerts only
- Development environments: helpful optimization feedback
- Audit environments: complete security event visibility

## Migration Notes

### **Existing Deployments**
- **Default**: Automatically uses "quiet" mode (reduces noise)
- **No Action Required**: Security protections remain fully active
- **Optional**: Set `SECURITY_LOG_LEVEL=normal` to restore previous behavior

### **Log Monitoring**
- **Update Alerts**: Adjust monitoring systems for new log levels
- **Security Dashboards**: May show fewer "warning" events (this is expected)
- **Compliance**: Verbose mode provides complete audit trail when needed

## Troubleshooting

### **If You Stop Seeing Security Logs**
```bash
# Temporarily increase verbosity
export SECURITY_LOG_LEVEL=verbose
```

### **If Logs Are Too Noisy**
```bash
# Reduce to production level
export SECURITY_LOG_LEVEL=quiet
```

### **To Verify Security Is Active**
```bash
# Check for genuine security alerts
grep "SECURITY ALERT" /path/to/logs/bot.log
```

---

**✅ Security remains fully active at all logging levels - only the verbosity changes, not the protection.**