# 🛡️ WhisperEngine Security Hardening Plan

## 🚨 IMMEDIATE ACTION REQUIRED

### **Critical Vulnerability: Command Handler Input Bypass**
**Risk Level: HIGH** - Command handlers bypass input validation security layer

**Impact:**
- Prompt injection attacks against individual commands
- Potential system information disclosure through specific commands
- TTS abuse with malicious/inappropriate content
- Web search manipulation and potential SSRF
- Admin command exploitation

---

## 🎯 **Phase 1: Critical Command Hardening (URGENT)**

### **1.1 Universal Input Validation Decorator**
Create a security decorator to enforce validation across all commands:

```python
# File: src/security/command_security.py
from functools import wraps
from src.security.input_validator import validate_user_input

def secure_command(command_type: str = "default"):
    """
    Security decorator for Discord commands
    
    Args:
        command_type: Type of command for specialized validation
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            user_id = str(ctx.author.id)
            
            # Validate all string arguments
            for arg_name, arg_value in kwargs.items():
                if isinstance(arg_value, str) and arg_value:
                    validation_result = validate_user_input(
                        arg_value, user_id, f"command_{command_type}"
                    )
                    
                    if not validation_result["is_safe"]:
                        await ctx.send(
                            "⚠️ Your input contains potentially unsafe content. "
                            "Please rephrase and try again."
                        )
                        return
                    
                    # Replace with sanitized content
                    kwargs[arg_name] = validation_result["sanitized_content"]
            
            # Log command usage for monitoring
            logger.info(f"SECURITY: Command {func.__name__} used by {user_id}")
            
            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator
```

### **1.2 Apply Security Decorator to High-Risk Commands**

**Voice Commands** (TTS abuse prevention):
```python
# File: src/handlers/voice.py
from src.security.command_security import secure_command

@secure_command("voice")
async def speak_text(ctx, *, text: str):
    # Additional voice-specific validation
    if len(text) > 500:  # Prevent TTS spam
        await ctx.send("⚠️ Text too long for speech (max 500 characters)")
        return
    await self._speak_text_handler(ctx, text)
```

**Web Search Commands** (SSRF prevention):
```python
# File: src/handlers/web_search_commands.py
from src.security.command_security import secure_command

@secure_command("web_search")
async def search_news_command(ctx, *, query: str):
    # Additional search-specific validation
    if any(suspicious in query.lower() for suspicious in 
           ['localhost', 'internal', 'admin', '127.0.0.1']):
        await ctx.send("⚠️ Search query contains restricted terms")
        return
    await self._handle_search_news(ctx, query)
```

### **1.3 Admin Command Security Enhancement**
```python
# File: src/handlers/admin.py
from src.security.input_validator import is_safe_admin_command

async def _debug_handler(self, ctx, action, is_admin):
    if not is_admin(ctx):
        await ctx.send("❌ Admin privileges required")
        return
    
    # Additional admin command validation
    user_id = str(ctx.author.id)
    if not is_safe_admin_command(f"debug {action}", user_id):
        await ctx.send("⚠️ Admin command contains unsafe content")
        logger.error(f"SECURITY: Unsafe admin command from {user_id}: debug {action}")
        return
    
    # Proceed with admin action
```

---

## 🎯 **Phase 2: Rate Limiting & Abuse Protection**

### **2.1 Command-Level Rate Limiting**
Implement per-user, per-command rate limiting:

```python
# File: src/security/rate_limiter.py
from collections import defaultdict
import time
import asyncio

class CommandRateLimiter:
    def __init__(self):
        self.user_command_history = defaultdict(lambda: defaultdict(list))
        self.rate_limits = {
            "voice": (5, 300),      # 5 TTS commands per 5 minutes
            "web_search": (10, 600), # 10 searches per 10 minutes  
            "memory": (20, 300),     # 20 memory commands per 5 minutes
            "admin": (50, 3600),     # 50 admin commands per hour
            "default": (30, 60),     # 30 commands per minute
        }
        self.warned_users = set()
        
    async def check_rate_limit(self, user_id: str, command_type: str) -> bool:
        """Check if user is within rate limits for command type"""
        now = time.time()
        limit, window = self.rate_limits.get(command_type, self.rate_limits["default"])
        
        # Clean old entries
        user_history = self.user_command_history[user_id][command_type]
        cutoff_time = now - window
        
        # Remove old entries
        self.user_command_history[user_id][command_type] = [
            timestamp for timestamp in user_history if timestamp > cutoff_time
        ]
        
        current_count = len(self.user_command_history[user_id][command_type])
        
        if current_count >= limit:
            # Issue warning for first offense
            if user_id not in self.warned_users:
                self.warned_users.add(user_id)
                logger.warning(f"SECURITY: Rate limit exceeded by user {user_id} for {command_type}")
            return False
        
        # Record this request
        self.user_command_history[user_id][command_type].append(now)
        return True

# Global rate limiter instance
command_rate_limiter = CommandRateLimiter()
```

### **2.2 Suspicious Activity Monitoring**
```python
# File: src/security/activity_monitor.py
from collections import defaultdict
import time

class SuspiciousActivityMonitor:
    def __init__(self):
        self.user_activity = defaultdict(lambda: {
            'failed_commands': 0,
            'rejected_inputs': 0,
            'rapid_requests': 0,
            'admin_attempts': 0,
            'last_reset': time.time()
        })
        
    def log_suspicious_activity(self, user_id: str, activity_type: str, details: str = ""):
        """Log suspicious user activity"""
        now = time.time()
        activity = self.user_activity[user_id]
        
        # Reset daily counters
        if now - activity['last_reset'] > 86400:  # 24 hours
            activity.clear()
            activity['last_reset'] = now
        
        activity[activity_type] += 1
        
        # Trigger warnings for concerning patterns
        if activity['failed_commands'] > 10:
            logger.warning(f"SECURITY: User {user_id} has {activity['failed_commands']} failed commands")
        
        if activity['rejected_inputs'] > 5:
            logger.warning(f"SECURITY: User {user_id} has {activity['rejected_inputs']} rejected inputs - possible attack")
        
        if activity['admin_attempts'] > 3:
            logger.error(f"SECURITY: User {user_id} attempted admin commands {activity['admin_attempts']} times")

# Global activity monitor
activity_monitor = SuspiciousActivityMonitor()
```

---

## 🎯 **Phase 3: Enhanced Input Validation**

### **3.1 Command-Specific Validation Rules**
```python
# File: src/security/command_validators.py

class CommandValidators:
    @staticmethod
    def validate_tts_text(text: str, user_id: str) -> tuple[bool, str]:
        """Validate text-to-speech input"""
        # Length check
        if len(text) > 500:
            return False, "Text too long for speech synthesis"
        
        # Content restrictions
        inappropriate_patterns = [
            r'(phone\s*number|credit\s*card|ssn|social\s*security)',
            r'(password|login|credentials)',
            r'(bomb|threat|kill|die)',
        ]
        
        for pattern in inappropriate_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Text contains inappropriate content for speech"
        
        return True, text
    
    @staticmethod
    def validate_search_query(query: str, user_id: str) -> tuple[bool, str]:
        """Validate web search queries"""
        # Length check
        if len(query) > 200:
            return False, "Search query too long"
        
        # Prevent internal network access attempts
        blocked_terms = [
            'localhost', '127.0.0.1', '192.168.', '10.0.0.', 'internal',
            'admin', 'config', 'database', 'api-key', 'password'
        ]
        
        query_lower = query.lower()
        for term in blocked_terms:
            if term in query_lower:
                return False, f"Search query contains restricted term: {term}"
        
        return True, query
```

---

## 🎯 **Phase 4: Security Monitoring & Alerting**

### **4.1 Security Event Dashboard** 
```python
# File: src/security/security_dashboard.py

class SecurityEventLogger:
    def __init__(self):
        self.security_events = []
        self.alert_thresholds = {
            'blocked_inputs_per_hour': 10,
            'failed_commands_per_hour': 20,
            'admin_attempts_per_hour': 5
        }
    
    async def log_security_event(self, event_type: str, user_id: str, details: dict):
        """Log security events for analysis"""
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'user_id': user_id,
            'details': details
        }
        
        self.security_events.append(event)
        
        # Check for alert conditions
        await self._check_alert_thresholds()
    
    async def _check_alert_thresholds(self):
        """Check if security alerts should be triggered"""
        now = time.time()
        hour_ago = now - 3600
        
        recent_events = [e for e in self.security_events if e['timestamp'] > hour_ago]
        
        # Count events by type
        event_counts = defaultdict(int)
        for event in recent_events:
            event_counts[event['type']] += 1
        
        # Trigger alerts
        for event_type, count in event_counts.items():
            threshold = self.alert_thresholds.get(event_type)
            if threshold and count >= threshold:
                logger.error(f"SECURITY ALERT: {count} {event_type} events in last hour (threshold: {threshold})")
```

---

## 🎯 **Implementation Timeline**

### **Week 1: Critical Command Security** ⚡
- [ ] Create security decorator system
- [ ] Apply to high-risk commands (TTS, web search, memory)
- [ ] Test with penetration testing scenarios

### **Week 2: Rate Limiting & Monitoring** 📊  
- [ ] Implement command rate limiting
- [ ] Add suspicious activity monitoring
- [ ] Create security event logging

### **Week 3: Enhanced Validation** 🔍
- [ ] Add command-specific validation rules
- [ ] Implement security dashboard
- [ ] Create automated security testing

### **Week 4: Testing & Hardening** 🧪
- [ ] Comprehensive security testing
- [ ] Performance impact assessment  
- [ ] Documentation and training

---

## 🛡️ **Additional Considerations**

### **Beyond Basic Input Validation:**

1. **Image Processing Security** - Currently missing validation for image attacks
2. **Memory System Boundaries** - Ensure cross-user memory isolation  
3. **LLM Jailbreaking** - Advanced prompt injection via conversation context
4. **Social Engineering** - Users trying to manipulate bots to reveal system info
5. **Resource Exhaustion** - Large memory operations, expensive LLM calls

### **Advanced Threat Vectors:**
- **Multi-step attacks** - Combining multiple commands for exploitation
- **Context poisoning** - Manipulating conversation history for later exploitation  
- **Timing attacks** - Using response times to infer system information
- **Side-channel attacks** - Using error patterns to map system architecture

---

## 🎯 **Next Steps**

1. **Immediate:** Apply security decorator to top 5 most dangerous commands
2. **This Week:** Implement basic rate limiting for TTS and web search
3. **This Month:** Complete comprehensive security hardening
4. **Ongoing:** Regular security audits and penetration testing

The current security foundation is **strong**, but the **command handler gap** is a critical vulnerability that should be addressed immediately. The hackers you're seeing are likely targeting exactly this type of input validation bypass.