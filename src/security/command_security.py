"""
Command Security Decorator
Provides universal input validation for Discord commands
"""

import logging
from functools import wraps
from typing import Optional

from src.security.input_validator import validate_user_input
from src.security.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)


def secure_command(command_type: str = "default", max_length: Optional[int] = None):
    """
    Security decorator for Discord commands with input validation
    
    Args:
        command_type: Type of command for logging context
        max_length: Optional maximum length for string inputs
    
    Usage:
        @secure_command("voice", max_length=500)
        async def speak_command(ctx, *, text: str):
            # text is now validated and sanitized
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract ctx from args (first argument after self)
            ctx = None
            if args:
                if hasattr(args[0], 'bot'):  # Handler class instance
                    ctx = args[1] if len(args) > 1 else None
                else:
                    ctx = args[0]  # Direct command function
            
            if not ctx or not hasattr(ctx, 'author'):
                # Fallback - proceed without validation if ctx not found
                return await func(*args, **kwargs)
            
            user_id = str(ctx.author.id)
            
            # Check rate limits first
            if not check_rate_limit(user_id, command_type):
                await ctx.send(
                    f"⚠️ Rate limit exceeded for {command_type} commands. "
                    "Please wait before trying again."
                )
                logger.warning("SECURITY: Rate limit blocked command %s for user %s", func.__name__, user_id)
                return
            
            # Validate all string arguments and keyword arguments
            validated_kwargs = {}
            
            for arg_name, arg_value in kwargs.items():
                if isinstance(arg_value, str) and arg_value.strip():
                    # Apply length check if specified
                    if max_length and len(arg_value) > max_length:
                        await ctx.send(f"⚠️ Input too long (max {max_length} characters)")
                        logger.warning(
                            "SECURITY: Input length exceeded by %s in %s: %d chars", 
                            user_id, command_type, len(arg_value)
                        )
                        return
                    
                    # Validate input security
                    validation_result = validate_user_input(
                        arg_value, user_id, f"command_{command_type}"
                    )
                    
                    if not validation_result["is_safe"]:
                        await ctx.send(
                            "⚠️ Your input contains potentially unsafe content. "
                            "Please rephrase and try again."
                        )
                        logger.error(
                            "SECURITY: Unsafe input blocked from %s in %s: %s",
                            user_id, command_type, validation_result['blocked_patterns']
                        )
                        return
                    
                    # Use sanitized content
                    validated_kwargs[arg_name] = validation_result["sanitized_content"]
                    
                    # Log warnings if any
                    if validation_result["warnings"]:
                        logger.warning(
                            "SECURITY: Input warnings for %s in %s: %s",
                            user_id, command_type, validation_result['warnings']
                        )
                else:
                    validated_kwargs[arg_name] = arg_value
            
            # Log successful command usage
            logger.info("SECURITY: Command %s validated for user %s", func.__name__, user_id)
            
            # Call original function with validated inputs
            return await func(*args, **validated_kwargs)
        
        return wrapper
    return decorator


def admin_secure_command(command_type: str = "admin"):
    """
    Enhanced security decorator for admin commands
    
    Args:
        command_type: Type of admin command for logging
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get context
            ctx = None
            if args:
                if hasattr(args[0], 'bot'):  # Handler class instance
                    ctx = args[1] if len(args) > 1 else None
                else:
                    ctx = args[0]  # Direct command function
            
            if not ctx:
                return await func(*args, **kwargs)
            
            user_id = str(ctx.author.id)
            
            # Additional admin command validation
            from src.security.input_validator import is_safe_admin_command
            
            # Check all string inputs for admin-specific threats
            for arg_value in kwargs.values():
                if isinstance(arg_value, str) and arg_value.strip():
                    if not is_safe_admin_command(f"{command_type} {arg_value}", user_id):
                        await ctx.send("⚠️ Admin command contains unsafe content")
                        logger.error(
                            "SECURITY: Unsafe admin command blocked from %s: %s %s",
                            user_id, command_type, arg_value
                        )
                        return
            
            logger.info("SECURITY: Admin command %s validated for user %s", func.__name__, user_id)
            
            # Apply standard security validation as well
            return await secure_command(command_type)(func)(*args, **kwargs)
        
        return wrapper
    return decorator