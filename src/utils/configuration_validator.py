#!/usr/bin/env python3
"""
Configuration Validation and Setup Assistant
Provides user-friendly configuration validation and setup guidance for WhisperEngine
"""

import os
import re
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import asyncio
import aiohttp
import json

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation check severity levels"""
    REQUIRED = "required"      # Must be fixed for system to work
    RECOMMENDED = "recommended"  # Should be set for optimal experience
    OPTIONAL = "optional"      # Nice to have but not necessary


class ConfigCategory(Enum):
    """Configuration categories for organized validation"""
    DISCORD = "discord"
    LLM = "llm"
    DATABASE = "database"
    MEMORY = "memory"
    SECURITY = "security"
    PERFORMANCE = "performance"
    FEATURES = "features"


@dataclass
class ValidationResult:
    """Result of a configuration validation check"""
    category: ConfigCategory
    level: ValidationLevel
    variable: str
    is_valid: bool
    message: str
    suggestion: Optional[str] = None
    current_value: Optional[str] = None
    expected_format: Optional[str] = None


class ConfigurationValidator:
    """
    Comprehensive configuration validation with helpful error messages and suggestions
    """
    
    def __init__(self):
        self.validation_rules = self._setup_validation_rules()
        self.validation_results: List[ValidationResult] = []
    
    def _setup_validation_rules(self) -> Dict[str, Dict]:
        """Setup validation rules for different configuration variables"""
        return {
            # Discord Configuration
            'DISCORD_BOT_TOKEN': {
                'category': ConfigCategory.DISCORD,
                'level': ValidationLevel.REQUIRED,
                'validator': self._validate_discord_token,
                'suggestion': 'Get your bot token from https://discord.com/developers/applications',
                'format': 'Should be a long string starting with your bot ID'
            },
            'ADMIN_USER_IDS': {
                'category': ConfigCategory.DISCORD,
                'level': ValidationLevel.RECOMMENDED,
                'validator': self._validate_user_ids,
                'suggestion': 'Add comma-separated Discord user IDs for admin access',
                'format': 'Example: 123456789012345678,987654321098765432'
            },
            'DISCORD_BOT_NAME': {
                'category': ConfigCategory.DISCORD,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_bot_name,
                'suggestion': 'Set a unique name for your bot to avoid conflicts',
                'format': 'Simple string without spaces, e.g., "mybot"'
            },
            
            # LLM Configuration
            'LLM_CHAT_API_URL': {
                'category': ConfigCategory.LLM,
                'level': ValidationLevel.REQUIRED,
                'validator': self._validate_llm_url,
                'suggestion': 'Set your LLM API endpoint (OpenAI, LM Studio, Ollama, etc.)',
                'format': 'Valid URL like http://localhost:1234/v1 or https://api.openai.com/v1'
            },
            'LLM_CHAT_API_KEY': {
                'category': ConfigCategory.LLM,
                'level': ValidationLevel.RECOMMENDED,
                'validator': self._validate_api_key,
                'suggestion': 'Set API key if using cloud LLM services',
                'format': 'Your API key from the LLM provider'
            },
            'LLM_CHAT_MODEL': {
                'category': ConfigCategory.LLM,
                'level': ValidationLevel.REQUIRED,
                'validator': self._validate_model_name,
                'suggestion': 'Specify the model name to use',
                'format': 'Model name like "gpt-4" or "local-model"'
            },
            
            # Database Configuration
            'POSTGRES_HOST': {
                'category': ConfigCategory.DATABASE,
                'level': ValidationLevel.RECOMMENDED,
                'validator': self._validate_host,
                'suggestion': 'Set PostgreSQL host for production use',
                'format': 'Hostname or IP address, e.g., "localhost" or "192.168.1.100"'
            },
            'REDIS_HOST': {
                'category': ConfigCategory.DATABASE,
                'level': ValidationLevel.RECOMMENDED,
                'validator': self._validate_host,
                'suggestion': 'Set Redis host for conversation caching',
                'format': 'Hostname or IP address, e.g., "localhost" or "redis.example.com"'
            },
            
            # Security Configuration
            'ENABLE_SECURITY_SCANNING': {
                'category': ConfigCategory.SECURITY,
                'level': ValidationLevel.RECOMMENDED,
                'validator': self._validate_boolean,
                'suggestion': 'Enable security scanning for production deployments',
                'format': 'true or false'
            },
            
            # Feature Configuration
            'ENABLE_VISUAL_EMOTION_ANALYSIS': {
                'category': ConfigCategory.FEATURES,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_boolean,
                'suggestion': 'Enable visual emotion analysis for image processing',
                'format': 'true or false'
            },
            
            # Phantom Feature Configuration
            'ENABLE_LOCAL_EMOTION_ENGINE': {
                'category': ConfigCategory.FEATURES,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_boolean,
                'suggestion': 'Enable high-performance emotion analysis (recommended)',
                'format': 'true or false'
            },
            'ENABLE_VECTORIZED_EMOTION_PROCESSOR': {
                'category': ConfigCategory.FEATURES,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_boolean,
                'suggestion': 'Enable batch emotion processing (resource intensive)',
                'format': 'true or false'
            },
            'ENABLE_ADVANCED_EMOTION_DETECTOR': {
                'category': ConfigCategory.FEATURES,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_boolean,
                'suggestion': 'Enable multi-modal emotion detection',
                'format': 'true or false'
            },
            'ENABLE_PROACTIVE_ENGAGEMENT_ENGINE': {
                'category': ConfigCategory.FEATURES,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_boolean,
                'suggestion': 'Enable AI-driven conversation initiation',
                'format': 'true or false'
            },
            'ENABLE_ADVANCED_THREAD_MANAGER': {
                'category': ConfigCategory.FEATURES,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_boolean,
                'suggestion': 'Enable advanced conversation thread management',
                'format': 'true or false'
            },
            'ENABLE_CONCURRENT_CONVERSATION_MANAGER': {
                'category': ConfigCategory.FEATURES,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_boolean,
                'suggestion': 'Enable parallel conversation handling',
                'format': 'true or false'
            },
            'ENABLE_ADVANCED_TOPIC_EXTRACTOR': {
                'category': ConfigCategory.FEATURES,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_boolean,
                'suggestion': 'Enable sophisticated topic analysis',
                'format': 'true or false'
            },
            
            # Phantom Feature Performance Settings
            'VECTORIZED_EMOTION_MAX_WORKERS': {
                'category': ConfigCategory.PERFORMANCE,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_positive_integer,
                'suggestion': 'Set worker count for emotion batch processing (1-16)',
                'format': 'Positive integer, recommended: 2-8'
            },
            'THREAD_MANAGER_MAX_ACTIVE_THREADS': {
                'category': ConfigCategory.PERFORMANCE,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_positive_integer,
                'suggestion': 'Set maximum concurrent conversation threads (5-100)',
                'format': 'Positive integer, recommended: 10-50'
            },
            'MAX_PHANTOM_FEATURE_MEMORY_MB': {
                'category': ConfigCategory.PERFORMANCE,
                'level': ValidationLevel.OPTIONAL,
                'validator': self._validate_positive_integer,
                'suggestion': 'Set memory limit for phantom features (512-4096 MB)',
                'format': 'Positive integer in MB, recommended: 1024-2048'
            }
        }
    
    async def validate_configuration(self, test_connections: bool = True) -> List[ValidationResult]:
        """
        Perform comprehensive configuration validation
        """
        self.validation_results = []
        
        logger.info("🔍 Starting configuration validation...")
        
        # Validate all defined rules
        for var_name, rule in self.validation_rules.items():
            result = await self._validate_variable(var_name, rule, test_connections)
            self.validation_results.append(result)
        
        # Check for common issues
        self._check_common_issues()
        
        # Sort results by priority
        self.validation_results.sort(key=lambda x: (x.level.value, x.category.value))
        
        return self.validation_results
    
    async def _validate_variable(self, var_name: str, rule: Dict, test_connections: bool) -> ValidationResult:
        """Validate a single configuration variable"""
        current_value = os.getenv(var_name)
        category = rule['category']
        level = rule['level']
        validator = rule['validator']
        
        # Check if variable is set
        if not current_value:
            if level == ValidationLevel.REQUIRED:
                message = f"❌ {var_name} is required but not set"
            elif level == ValidationLevel.RECOMMENDED:
                message = f"⚠️ {var_name} is recommended but not set"
            else:
                message = f"ℹ️ {var_name} is optional and not set"
            
            return ValidationResult(
                category=category,
                level=level,
                variable=var_name,
                is_valid=level == ValidationLevel.OPTIONAL,
                message=message,
                suggestion=rule.get('suggestion'),
                current_value=current_value,
                expected_format=rule.get('format')
            )
        
        # Validate the value
        try:
            is_valid, message = await validator(current_value, test_connections)
            
            return ValidationResult(
                category=category,
                level=level,
                variable=var_name,
                is_valid=is_valid,
                message=message,
                suggestion=rule.get('suggestion') if not is_valid else None,
                current_value=current_value,
                expected_format=rule.get('format') if not is_valid else None
            )
            
        except Exception as e:
            logger.warning(f"Validation error for {var_name}: {e}")
            return ValidationResult(
                category=category,
                level=level,
                variable=var_name,
                is_valid=False,
                message=f"❌ {var_name} validation failed: {str(e)}",
                suggestion=rule.get('suggestion'),
                current_value=current_value,
                expected_format=rule.get('format')
            )
    
    # Validation methods for different types of configuration
    async def _validate_discord_token(self, value: str, test_connections: bool) -> Tuple[bool, str]:
        """Validate Discord bot token format and optionally test it"""
        if not value or len(value) < 50:
            return False, "❌ Discord bot token appears to be invalid (too short)"
        
        # Basic format check
        if not re.match(r'^[A-Za-z0-9._-]+$', value):
            return False, "❌ Discord bot token contains invalid characters"
        
        if test_connections:
            # Test token by attempting to get bot user info
            try:
                headers = {'Authorization': f'Bot {value}'}
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://discord.com/api/v10/users/@me',
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            bot_name = data.get('username', 'Unknown')
                            return True, f"✅ Discord bot token valid (Bot: {bot_name})"
                        elif response.status == 401:
                            return False, "❌ Discord bot token is invalid or expired"
                        else:
                            return False, f"❌ Discord API error (status: {response.status})"
            except asyncio.TimeoutError:
                return False, "⚠️ Discord bot token test timed out (but may still be valid)"
            except Exception as e:
                return False, f"⚠️ Could not test Discord token: {str(e)}"
        else:
            return True, "✅ Discord bot token format appears valid"
    
    async def _validate_user_ids(self, value: str, test_connections: bool) -> Tuple[bool, str]:
        """Validate Discord user IDs format"""
        if not value.strip():
            return True, "ℹ️ No admin user IDs set (anyone can use admin commands)"
        
        user_ids = [uid.strip() for uid in value.split(',') if uid.strip()]
        invalid_ids = []
        
        for uid in user_ids:
            if not uid.isdigit() or len(uid) < 17 or len(uid) > 19:
                invalid_ids.append(uid)
        
        if invalid_ids:
            return False, f"❌ Invalid Discord user IDs: {', '.join(invalid_ids)}"
        
        return True, f"✅ {len(user_ids)} admin user ID(s) configured"
    
    async def _validate_bot_name(self, value: str, test_connections: bool) -> Tuple[bool, str]:
        """Validate bot name format"""
        if not value.strip():
            return True, "ℹ️ Bot name not set (will respond to all commands)"
        
        if ' ' in value or not re.match(r'^[a-zA-Z0-9_-]+$', value):
            return False, "❌ Bot name should not contain spaces or special characters"
        
        return True, f"✅ Bot name '{value}' is valid"
    
    async def _validate_llm_url(self, value: str, test_connections: bool) -> Tuple[bool, str]:
        """Validate LLM API URL and optionally test connection"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(value):
            return False, "❌ LLM API URL format is invalid"
        
        if test_connections:
            try:
                async with aiohttp.ClientSession() as session:
                    # Test if endpoint is reachable
                    test_url = f"{value.rstrip('/')}/models" if not value.endswith('/chat/completions') else value.replace('/chat/completions', '/models')
                    async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status in [200, 401, 403]:  # Reachable, even if auth required
                            return True, f"✅ LLM API endpoint is reachable"
                        else:
                            return False, f"❌ LLM API endpoint returned status {response.status}"
            except asyncio.TimeoutError:
                return False, "⚠️ LLM API endpoint test timed out"
            except Exception as e:
                return False, f"⚠️ Could not reach LLM API: {str(e)}"
        else:
            return True, "✅ LLM API URL format is valid"
    
    async def _validate_api_key(self, value: str, test_connections: bool) -> Tuple[bool, str]:
        """Validate API key format"""
        if not value.strip():
            return True, "ℹ️ No API key set (using local LLM or public endpoint)"
        
        if len(value) < 10:
            return False, "❌ API key appears too short to be valid"
        
        return True, "✅ API key is set"
    
    async def _validate_model_name(self, value: str, test_connections: bool) -> Tuple[bool, str]:
        """Validate model name format"""
        if not value.strip():
            return False, "❌ Model name is required"
        
        if len(value) < 2:
            return False, "❌ Model name appears too short"
        
        return True, f"✅ Model name '{value}' is set"
    
    async def _validate_host(self, value: str, test_connections: bool) -> Tuple[bool, str]:
        """Validate host/IP address format"""
        if not value.strip():
            return True, "ℹ️ Host not set (using default/local)"
        
        # Check if it's a valid hostname or IP
        hostname_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        ip_pattern = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
        
        if not (hostname_pattern.match(value) or ip_pattern.match(value) or value == 'localhost'):
            return False, f"❌ '{value}' is not a valid hostname or IP address"
        
        return True, f"✅ Host '{value}' format is valid"
    
    async def _validate_boolean(self, value: str, test_connections: bool) -> Tuple[bool, str]:
        """Validate boolean value format"""
        if value.lower() in ['true', 'false', '1', '0', 'yes', 'no']:
            return True, f"✅ Boolean value '{value}' is valid"
        else:
            return False, f"❌ '{value}' is not a valid boolean (use 'true' or 'false')"
    
    async def _validate_positive_integer(self, value: str, test_connections: bool) -> Tuple[bool, str]:
        """Validate positive integer value"""
        try:
            int_value = int(value)
            if int_value > 0:
                return True, f"✅ Positive integer '{value}' is valid"
            else:
                return False, f"❌ '{value}' must be a positive integer (greater than 0)"
        except ValueError:
            return False, f"❌ '{value}' is not a valid integer"
    
    def _check_common_issues(self):
        """Check for common configuration issues and patterns"""
        
        # Check for missing .env file
        if not os.path.exists('.env'):
            self.validation_results.append(ValidationResult(
                category=ConfigCategory.DISCORD,
                level=ValidationLevel.REQUIRED,
                variable='.env',
                is_valid=False,
                message="❌ No .env file found",
                suggestion="Copy .env.example to .env and configure your settings",
                expected_format="Create .env file in project root"
            ))
        
        # Check for development vs production settings
        env_mode = os.getenv('ENV_MODE', 'development')
        if env_mode == 'production':
            # Production-specific checks
            if not os.getenv('POSTGRES_HOST'):
                self.validation_results.append(ValidationResult(
                    category=ConfigCategory.DATABASE,
                    level=ValidationLevel.REQUIRED,
                    variable='POSTGRES_HOST',
                    is_valid=False,
                    message="❌ Production mode requires PostgreSQL",
                    suggestion="Set POSTGRES_HOST for production deployment"
                ))
    
    def generate_setup_guide(self) -> str:
        """Generate a personalized setup guide based on validation results"""

        required_issues = [r for r in self.validation_results if r.level == ValidationLevel.REQUIRED and not r.is_valid]
        recommended_issues = [r for r in self.validation_results if r.level == ValidationLevel.RECOMMENDED and not r.is_valid]

        guide = "✨ **WhisperEngine Setup Guide**\n\n"

        if not required_issues and not recommended_issues:
            guide += "✅ **Congratulations!** Your configuration looks great!\n"
            guide += "You're ready to start your bot with: `python run.py`\n\n"
        else:
            if required_issues:
                guide += "🔴 **Required Issues (Must Fix):**\n"
                for issue in required_issues:
                    guide += f"• **{issue.variable}**: {issue.message}\n"
                    if issue.suggestion:
                        guide += f"  💡 {issue.suggestion}\n"
                    if issue.expected_format:
                        guide += f"  📝 Format: {issue.expected_format}\n"
                guide += "\n"

            if recommended_issues:
                guide += "🟡 **Recommended Improvements:**\n"
                for issue in recommended_issues:
                    guide += f"• **{issue.variable}**: {issue.message}\n"
                    if issue.suggestion:
                        guide += f"  💡 {issue.suggestion}\n"
                guide += "\n"

            guide += "📋 **Next Steps:**\n"
            guide += "1. Create or update your `.env` file\n"
            guide += "2. Fix the required issues above\n"
            guide += "3. Optionally address recommended items\n"
            guide += "4. Run validation again: `python env_manager.py --validate`\n"
            guide += "5. Start your bot: `python run.py`\n\n"

        return guide
        guide += "• Check the documentation: `docs/configuration/`\\n"
        guide += "• Example configuration: `.env.example`\\n"
        guide += "• Environment variables guide: `docs/configuration/ENVIRONMENT_VARIABLES_REFERENCE.md`\\n"
        
        return guide
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results"""
        total = len(self.validation_results)
        valid = len([r for r in self.validation_results if r.is_valid])
        required_issues = len([r for r in self.validation_results if r.level == ValidationLevel.REQUIRED and not r.is_valid])
        
        return {
            "total_checks": total,
            "valid_checks": valid,
            "required_issues": required_issues,
            "ready_to_deploy": required_issues == 0,
            "validation_percentage": round((valid / total) * 100) if total > 0 else 0
        }


# Global validator instance
config_validator = ConfigurationValidator()


async def quick_validate() -> bool:
    """Quick validation check for essential configuration"""
    essential_vars = ['DISCORD_BOT_TOKEN', 'LLM_CHAT_API_URL']
    
    for var in essential_vars:
        if not os.getenv(var):
            return False
    
    return True


async def interactive_setup():
    """Interactive setup helper"""
    print("🎭 Welcome to WhisperEngine Setup Assistant!\\n")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("No .env file found. Let's create one from the template...")
        try:
            with open('.env.example', 'r') as template:
                with open('.env', 'w') as env_file:
                    env_file.write(template.read())
            print("✅ Created .env file from template\\n")
        except FileNotFoundError:
            print("❌ .env.example not found. Please create a .env file manually.\\n")
            return
    
    # Run validation
    print("🔍 Validating your configuration...\\n")
    results = await config_validator.validate_configuration(test_connections=True)
    
    # Show results
    summary = config_validator.get_validation_summary()
    print(f"📊 Validation Summary:")
    print(f"   ✅ {summary['valid_checks']}/{summary['total_checks']} checks passed ({summary['validation_percentage']}%)")
    print(f"   🔴 {summary['required_issues']} required issues found")
    print(f"   ✨ Ready to deploy: {'Yes' if summary['ready_to_deploy'] else 'No'}\\n")
    
    # Show setup guide
    guide = config_validator.generate_setup_guide()
    print(guide)