# Security & Authorization Design

## Overview

This document defines the security architecture for the Discord bot, including authentication, authorization, data protection, and abuse prevention mechanisms. The bot handles sensitive user data including conversation history, personal facts, and emotional profiles, requiring robust security controls.

## Security Architecture

### Core Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Principle of Least Privilege**: Minimum necessary permissions
3. **Data Minimization**: Collect and retain only necessary data
4. **User Control**: Users can manage their own data
5. **Secure by Default**: Safe configurations out of the box
6. **Audit Trail**: Comprehensive logging for security events

### Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    Discord Bot Security Stack                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Application Layer                         │ │
│  │  • Admin Role Verification    • Command Authorization       │ │
│  │  • Rate Limiting             • Input Validation            │ │
│  │  • Data Access Controls      • Audit Logging               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                     Data Layer                              │ │
│  │  • Per-User Data Isolation   • Encryption at Rest          │ │
│  │  • User Data Ownership       • Secure Deletion             │ │
│  │  • Access Logging            • Data Retention Policies     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Network Layer                             │ │
│  │  • HTTPS/WSS Encryption      • API Key Management          │ │
│  │  • Certificate Validation    • Connection Security         │ │
│  │  • Rate Limiting             • IP-based Controls           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                Infrastructure Layer                         │ │
│  │  • Environment Variables     • File System Permissions     │ │
│  │  • Process Isolation         • System-level Security       │ │
│  │  • Backup Encryption         • Log File Security           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication & Authorization

### Admin Role Management

#### Admin User Identification
```python
# Environment-based admin configuration
ADMIN_USER_IDS=123456789012345678,987654321098765432
```

**Design Decisions:**
- **Discord User IDs**: Immutable, unique identifiers
- **Environment Variable**: Secure, deployment-specific configuration
- **Multiple Admins**: Comma-separated list for operational redundancy
- **No Runtime Changes**: Requires bot restart for security

#### Admin Authorization Pattern
```python
def is_admin(ctx) -> bool:
    """Check if user has admin permissions"""
    # 1. Check guild admin permissions (Discord server owners/admins)
    if hasattr(ctx, 'author') and hasattr(ctx.author, 'guild_permissions'):
        if ctx.author.guild_permissions.administrator:
            return True
    
    # 2. Check explicit admin user IDs from environment
    user_id = getattr(ctx.author, 'id', None) or getattr(ctx, 'user_id', None)
    return user_id in admin_user_ids
```

**Security Features:**
- **Dual Check**: Discord permissions OR explicit admin list
- **Guild Context**: Respects Discord server admin roles
- **Fallback Protection**: Works even if Discord permissions fail
- **Type Safety**: Handles different context types safely

#### Admin Command Protection
```python
@bot.command(name="admin_command")
async def admin_only_command(ctx):
    if not is_admin(ctx):
        await ctx.send("❌ This command requires administrator privileges.")
        logger.warning(f"Unauthorized admin command attempt by {ctx.author.id}")
        return
    
    # Admin functionality here
```

**Protection Mechanisms:**
- **Early Return**: Fail fast on authorization check
- **User Feedback**: Clear error message for unauthorized attempts
- **Audit Logging**: Security events logged for monitoring
- **No Data Exposure**: No sensitive information in error messages

### User Authorization Model

#### Data Ownership Principles
1. **User Data Ownership**: Each user owns their personal data
2. **Admin Override**: Admins can access any data for moderation
3. **No Cross-User Access**: Users cannot access other users' data
4. **Consent Required**: Explicit consent for data processing

#### Access Control Matrix

| Resource Type | User (Self) | User (Other) | Admin | Bot |
|---------------|-------------|--------------|-------|-----|
| Personal Facts | ✅ Full | ❌ None | ✅ Full | ✅ Read |
| Conversation History | ✅ Full | ❌ None | ✅ Full | ✅ Read/Write |
| Emotion Profiles | ✅ Read | ❌ None | ✅ Full | ✅ Read/Write |
| Global Facts | ✅ Read | ✅ Read | ✅ Full | ✅ Read/Write |
| System Commands | ❌ None | ❌ None | ✅ Full | ✅ Execute |

## API Security

### API Key Management

#### Secure Storage Pattern
```python
# ✅ SECURE: Environment variables
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# ❌ INSECURE: Hard-coded keys (never do this)
# API_KEY = "sk-1234567890abcdef"
```

#### API Key Validation
```python
def validate_api_configuration():
    """Validate API keys are properly configured"""
    required_keys = {
        'DISCORD_BOT_TOKEN': 'Discord bot token',
        'OPENROUTER_API_KEY': 'OpenRouter API key (if using cloud LLM)',
    }
    
    missing_keys = []
    for key, description in required_keys.items():
        if not os.getenv(key):
            missing_keys.append(f"{key} ({description})")
    
    if missing_keys:
        logger.error(f"Missing required API keys: {', '.join(missing_keys)}")
        return False
    
    return True
```

#### HTTP Security Configuration
```python
# LLM Client Security Settings
class LMStudioClient:
    def __init__(self):
        self.session = requests.Session()
        
        # Security configurations
        self.session.verify = True  # Always verify SSL certificates
        self.session.timeout = (5, 30)  # Connection and read timeouts
        
        # Security headers
        self.session.headers.update({
            'User-Agent': 'DiscordBot/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Connection pool limits
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=Retry(total=3, backoff_factor=1)
        )
        self.session.mount('https://', adapter)
```

## Rate Limiting & Abuse Prevention

### Multi-Layer Rate Limiting

#### 1. Discord Rate Limiting Compliance
```python
# Built into discord.py - automatic rate limit handling
# No additional implementation needed
```

#### 2. LLM API Rate Limiting
```python
class AsyncLLMManager:
    def __init__(self, max_concurrent_requests: int = 3):
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._request_times = {}  # Per-user tracking
        self._min_request_interval = 1.0  # 1 second between requests
    
    async def _apply_rate_limit(self, user_id: str):
        """Apply per-user rate limiting"""
        current_time = time.time()
        
        if user_id in self._request_times:
            time_since_last = current_time - self._request_times[user_id]
            if time_since_last < self._min_request_interval:
                wait_time = self._min_request_interval - time_since_last
                await asyncio.sleep(wait_time)
        
        self._request_times[user_id] = time.time()
```

#### 3. Command-Level Rate Limiting
```python
from collections import defaultdict
import time

class CommandRateLimiter:
    def __init__(self):
        self.user_command_times = defaultdict(dict)
        self.rate_limits = {
            'default': (5, 60),    # 5 commands per 60 seconds
            'memory': (10, 300),   # 10 memory commands per 5 minutes
            'admin': (50, 60),     # 50 admin commands per minute
        }
    
    def check_rate_limit(self, user_id: str, command_type: str = 'default') -> bool:
        """Check if user is within rate limits"""
        now = time.time()
        limit, window = self.rate_limits.get(command_type, self.rate_limits['default'])
        
        # Clean old entries
        user_times = self.user_command_times[user_id]
        cutoff = now - window
        user_times[command_type] = [t for t in user_times.get(command_type, []) if t > cutoff]
        
        # Check current usage
        if len(user_times[command_type]) >= limit:
            return False
        
        # Record this request
        user_times[command_type].append(now)
        return True
```

### Abuse Detection Patterns

#### Suspicious Activity Detection
```python
class SecurityMonitor:
    def __init__(self):
        self.user_activity = defaultdict(lambda: {
            'failed_commands': 0,
            'rapid_requests': 0,
            'large_responses': 0,
            'last_warning': 0
        })
    
    def check_suspicious_activity(self, user_id: str, event_type: str):
        """Monitor for suspicious user activity"""
        activity = self.user_activity[user_id]
        now = time.time()
        
        # Reset counters daily
        if now - activity.get('last_reset', 0) > 86400:  # 24 hours
            activity.clear()
            activity['last_reset'] = now
        
        # Track different types of suspicious activity
        if event_type == 'failed_command':
            activity['failed_commands'] += 1
            if activity['failed_commands'] > 10:  # 10 failed commands
                self._issue_warning(user_id, "excessive_failed_commands")
        
        elif event_type == 'rapid_requests':
            activity['rapid_requests'] += 1
            if activity['rapid_requests'] > 30:  # 30 rapid requests
                self._issue_warning(user_id, "rapid_fire_requests")
    
    def _issue_warning(self, user_id: str, reason: str):
        """Issue security warning for suspicious activity"""
        activity = self.user_activity[user_id]
        now = time.time()
        
        # Rate limit warnings (max 1 per hour)
        if now - activity['last_warning'] < 3600:
            return
        
        activity['last_warning'] = now
        logger.warning(f"Security warning for user {user_id}: {reason}")
        
        # Could implement additional actions:
        # - Temporary rate limit increase
        # - Admin notification
        # - Automatic temporary suspension
```

## Data Protection

### Data Encryption

#### Data at Rest
```python
# SQLite database encryption (using PRAGMA key)
class UserProfileDatabase:
    def __init__(self, db_path: str = "user_profiles.db"):
        self.db_path = db_path
        
        # Enable encryption if key provided
        encryption_key = os.getenv('DATABASE_ENCRYPTION_KEY')
        if encryption_key:
            # Apply encryption pragma on connection
            self._apply_encryption(encryption_key)
```

#### Sensitive Data Handling
```python
import hashlib
import hmac

class DataProtection:
    @staticmethod
    def hash_user_id(user_id: str) -> str:
        """Create reproducible hash of user ID for logging"""
        salt = os.getenv('USER_ID_SALT', 'default_salt_change_in_production')
        return hmac.new(
            salt.encode(),
            str(user_id).encode(),
            hashlib.sha256
        ).hexdigest()[:12]  # First 12 chars for brevity
    
    @staticmethod
    def sanitize_for_logging(data: str) -> str:
        """Remove sensitive information from log data"""
        # Remove potential API keys, tokens, personal info
        import re
        
        # Remove API key patterns
        data = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[API_KEY_REDACTED]', data)
        data = re.sub(r'Bearer [a-zA-Z0-9+/=]{20,}', '[TOKEN_REDACTED]', data)
        
        # Remove Discord tokens
        data = re.sub(r'[A-Za-z0-9]{24}\.[A-Za-z0-9]{6}\.[A-Za-z0-9_\-]{27}', '[DISCORD_TOKEN_REDACTED]', data)
        
        return data
```

### Data Retention & Deletion

#### User Data Deletion
```python
async def handle_forget_me_command(user_id: str):
    """Complete user data deletion"""
    try:
        # 1. User profile database
        user_db = UserProfileDatabase()
        user_db.delete_user_profile(user_id)
        
        # 2. ChromaDB memory data
        memory_manager = UserMemoryManager()
        memory_manager.delete_user_data(user_id)
        
        # 3. Conversation cache
        if conversation_cache:
            # Clear from all channels where user participated
            conversation_cache.clear_user_data(user_id)
        
        # 4. Temporary files and images
        temp_dir = Path("temp_images")
        for file in temp_dir.glob(f"*{user_id}*"):
            file.unlink(missing_ok=True)
        
        # 5. Audit log the deletion
        logger.info(f"Complete data deletion for user {DataProtection.hash_user_id(user_id)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete user data: {e}")
        return False
```

#### Data Retention Policies
```python
class DataRetentionManager:
    def __init__(self):
        self.retention_policies = {
            'conversation_history': 365,    # 1 year
            'emotion_history': 180,         # 6 months  
            'fact_data': 730,              # 2 years
            'audit_logs': 2555,            # 7 years (compliance)
            'temp_files': 7,               # 1 week
        }
    
    async def apply_retention_policies(self):
        """Apply data retention policies"""
        for data_type, days in self.retention_policies.items():
            try:
                await self._cleanup_old_data(data_type, days)
            except Exception as e:
                logger.error(f"Failed to cleanup {data_type}: {e}")
    
    async def _cleanup_old_data(self, data_type: str, days: int):
        """Clean up data older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if data_type == 'conversation_history':
            # Clean old conversation data from ChromaDB
            pass  # Implementation depends on ChromaDB query capabilities
        
        elif data_type == 'emotion_history':
            # Clean old emotion data from SQLite
            with sqlite3.connect("user_profiles.db") as conn:
                conn.execute(
                    "DELETE FROM emotion_history WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
```

## Input Validation & Sanitization

### Message Content Validation
```python
class InputValidator:
    def __init__(self):
        self.max_message_length = 2000  # Discord limit
        self.blocked_patterns = [
            r'<script.*?>.*?</script>',     # Script injection
            r'javascript:.*',               # JavaScript URLs
            r'data:.*base64.*',            # Data URLs (potential XSS)
        ]
    
    def validate_user_input(self, content: str) -> tuple[bool, str]:
        """Validate and sanitize user input"""
        # Length check
        if len(content) > self.max_message_length:
            return False, "Message too long"
        
        # Pattern check
        import re
        for pattern in self.blocked_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, "Potentially malicious content detected"
        
        # Basic sanitization
        sanitized = self._sanitize_content(content)
        return True, sanitized
    
    def _sanitize_content(self, content: str) -> str:
        """Basic content sanitization"""
        # Remove null bytes
        content = content.replace('\x00', '')
        
        # Normalize whitespace
        content = ' '.join(content.split())
        
        # Remove potentially dangerous Unicode characters
        content = ''.join(char for char in content if ord(char) < 0x10000)
        
        return content
```

### Command Parameter Validation
```python
def validate_user_id(user_id_str: str) -> tuple[bool, int]:
    """Validate Discord user ID format"""
    try:
        user_id = int(user_id_str)
        
        # Discord user IDs are 64-bit integers
        if user_id < 1 or user_id > 2**63 - 1:
            return False, 0
            
        # Basic sanity check (Discord IDs are typically 17-19 digits)
        if len(str(user_id)) < 15 or len(str(user_id)) > 20:
            return False, 0
            
        return True, user_id
        
    except (ValueError, OverflowError):
        return False, 0

def validate_command_parameters(command: str, params: dict) -> bool:
    """Validate command parameters"""
    validators = {
        'user_lookup': lambda p: validate_user_id(p.get('user_id', ''))[0],
        'memory_query': lambda p: len(p.get('query', '')) <= 500,
        'fact_extraction': lambda p: len(p.get('text', '')) <= 2000,
    }
    
    validator = validators.get(command)
    if validator:
        return validator(params)
    
    return True  # Allow unknown commands (handled elsewhere)
```

## Audit Logging & Monitoring

### Security Event Logging
```python
import logging
from datetime import datetime
from enum import Enum

class SecurityEventType(Enum):
    ADMIN_COMMAND = "admin_command"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_ACCESS = "data_access"
    DATA_DELETION = "data_deletion"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_KEY_USAGE = "api_key_usage"

class SecurityLogger:
    def __init__(self):
        # Separate logger for security events
        self.security_logger = logging.getLogger('security')
        handler = logging.FileHandler('security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.security_logger.addHandler(handler)
        self.security_logger.setLevel(logging.INFO)
    
    def log_security_event(self, event_type: SecurityEventType, user_id: str, 
                          details: dict = None, success: bool = True):
        """Log security-related events"""
        hashed_user_id = DataProtection.hash_user_id(user_id)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type.value,
            'user_id_hash': hashed_user_id,
            'success': success,
            'details': details or {}
        }
        
        # Sanitize details for logging
        sanitized_details = {
            k: DataProtection.sanitize_for_logging(str(v))
            for k, v in log_entry['details'].items()
        }
        log_entry['details'] = sanitized_details
        
        level = logging.WARNING if not success else logging.INFO
        self.security_logger.log(level, f"SECURITY_EVENT: {log_entry}")

# Global security logger instance
security_logger = SecurityLogger()
```

### Usage Examples
```python
# Admin command execution
@bot.command(name="admin_stats")
async def admin_stats(ctx):
    if not is_admin(ctx):
        security_logger.log_security_event(
            SecurityEventType.UNAUTHORIZED_ACCESS,
            str(ctx.author.id),
            {'command': 'admin_stats', 'channel': str(ctx.channel.id)},
            success=False
        )
        return
    
    security_logger.log_security_event(
        SecurityEventType.ADMIN_COMMAND,
        str(ctx.author.id),
        {'command': 'admin_stats'}
    )
    
    # Command implementation...

# Data deletion
async def delete_user_data(user_id: str):
    security_logger.log_security_event(
        SecurityEventType.DATA_DELETION,
        user_id,
        {'deletion_type': 'complete_user_data'}
    )
    
    # Deletion implementation...
```

## Security Configuration

### Environment Variables
```bash
# === SECURITY CONFIGURATION ===
# Admin user management
ADMIN_USER_IDS=123456789012345678,987654321098765432

# Data protection
DATABASE_ENCRYPTION_KEY=your_encryption_key_here
USER_ID_SALT=your_unique_salt_here

# Rate limiting
MAX_REQUESTS_PER_USER_PER_MINUTE=30
MAX_ADMIN_REQUESTS_PER_MINUTE=100

# API security
REQUIRE_SSL_VERIFICATION=true
API_TIMEOUT_SECONDS=30
MAX_RETRY_ATTEMPTS=3

# Logging
ENABLE_SECURITY_LOGGING=true
LOG_LEVEL=INFO
SECURITY_LOG_RETENTION_DAYS=2555
```

### Security Checklist

#### Pre-Deployment Security Review
- [ ] All API keys stored in environment variables
- [ ] Admin user IDs configured correctly
- [ ] SSL certificate verification enabled
- [ ] Rate limiting configured appropriately
- [ ] Input validation implemented for all user inputs
- [ ] Audit logging enabled and configured
- [ ] Data retention policies defined and implemented
- [ ] User data deletion functionality tested
- [ ] Error messages don't leak sensitive information
- [ ] Security event monitoring configured

#### Ongoing Security Monitoring
- [ ] Regular review of security logs
- [ ] Monitor for unusual rate limit violations
- [ ] Review admin command usage patterns
- [ ] Check for failed authentication attempts
- [ ] Monitor data access patterns
- [ ] Regular security dependency updates
- [ ] Periodic security configuration review

## Incident Response

### Security Incident Types
1. **Unauthorized Admin Access**: Non-admin user accessing admin commands
2. **Data Breach**: Unauthorized access to user data
3. **API Key Compromise**: Suspected API key theft or misuse
4. **Abuse Detection**: Automated detection of suspicious activity
5. **System Compromise**: Evidence of system-level security breach

### Response Procedures
```python
class IncidentResponse:
    @staticmethod
    async def handle_security_incident(incident_type: str, details: dict):
        """Handle security incidents"""
        
        # 1. Log the incident
        security_logger.log_security_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            details.get('user_id', 'unknown'),
            {'incident_type': incident_type, 'details': details},
            success=False
        )
        
        # 2. Take immediate protective action
        if incident_type == 'unauthorized_admin_access':
            await _temporarily_restrict_user(details['user_id'])
        
        elif incident_type == 'api_abuse':
            await _increase_rate_limits(details['user_id'])
        
        elif incident_type == 'data_breach_suspected':
            await _emergency_data_protection_mode()
        
        # 3. Notify administrators
        await _notify_admins(incident_type, details)
    
    @staticmethod
    async def _notify_admins(incident_type: str, details: dict):
        """Notify administrators of security incidents"""
        # Implementation would send notifications to admin users
        pass
```

## Conclusion

This security architecture provides comprehensive protection through:

1. **Multi-layer Security**: Defense in depth across application, data, network, and infrastructure layers
2. **Strong Authentication**: Discord-based authentication with admin role management
3. **Robust Authorization**: Clear access control matrix with user data ownership
4. **Comprehensive Monitoring**: Security event logging and suspicious activity detection
5. **Data Protection**: Encryption, retention policies, and user deletion capabilities
6. **Input Validation**: Protection against injection and malicious content
7. **Incident Response**: Automated detection and response procedures

The design balances security requirements with usability, ensuring the bot can operate safely while providing rich functionality to users and administrators.
