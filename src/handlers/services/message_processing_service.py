"""
Message Processing Service

Handles the core message processing logic including DM, guild, and mention message handling.
Extracted from events.py for better code organization and maintainability.
"""

import asyncio
import logging
import os
from datetime import UTC, datetime

import discord

from src.security.input_validator import validate_user_input
from src.utils.helpers import get_message_content
from src.utils.production_error_handler import ErrorCategory, ErrorSeverity, handle_errors

logger = logging.getLogger(__name__)


class MessageProcessingService:
    """
    Service for processing different types of messages (DM, guild, mentions).
    
    This service handles the initial processing and routing of messages,
    including security validation and basic message classification.
    """
    
    def __init__(self, bot, bot_core):
        self.bot = bot
        self.bot_core = bot_core
        
        # Core dependencies
        self.emoji_response_intelligence = getattr(bot_core, "emoji_response_intelligence", None)
        
        logger.info("📨 Message Processing Service initialized")
    
    async def handle_dm_message(self, message):
        """Handle direct message to the bot."""
        # Check if this is a command first
        if message.content.startswith("!"):
            await self.bot.process_commands(message)
            return None  # Message was processed as command

        reply_channel = message.channel
        user_id = str(message.author.id)
        logger.debug(f"Processing DM from {message.author.name}")

        # Security validation
        validation_result = validate_user_input(message.content, user_id, "dm")
        
        if not validation_result["is_safe"]:
            logger.error(f"SECURITY: Unsafe input detected from user {user_id} in DM")
            logger.error(f"SECURITY: Blocked patterns: {validation_result['blocked_patterns']}")
            
            # 🎭 EMOJI INTELLIGENCE: Use emoji response for inappropriate content
            try:
                # Determine bot character
                bot_character = "general"
                if 'elena' in str(self.bot.user.name).lower() or 'dream' in str(self.bot.user.name).lower():
                    bot_character = "mystical"
                elif 'marcus' in str(self.bot.user.name).lower():
                    bot_character = "technical"
                
                # Evaluate emoji response for inappropriate content
                emoji_decision = await self.emoji_response_intelligence.evaluate_emoji_response(
                    user_id=user_id,
                    user_message=message.content,
                    bot_character=bot_character,
                    security_validation_result=validation_result,
                    emotional_context=None,
                    conversation_context={'channel_type': 'dm'}
                )
                
                if emoji_decision.should_use_emoji:
                    logger.info(f"🎭 SECURITY + EMOJI: Using emoji '{emoji_decision.emoji_choice}' for inappropriate content")
                    await self.emoji_response_intelligence.apply_emoji_response(message, emoji_decision)
                    return None
                    
            except Exception as e:
                logger.error(f"Error in security emoji response: {e}")
            
            # Fallback to text warning if emoji response fails
            await reply_channel.send(
                "⚠️ Your message contains content that could not be processed for security reasons. Please rephrase your message."
            )
            return None

        # Use sanitized content
        sanitized_content = validation_result["sanitized_content"]
        if validation_result["warnings"]:
            logger.warning(
                f"SECURITY: Input warnings for user {user_id} in DM: {validation_result['warnings']}"
            )

        # Replace original message content with sanitized version
        message.content = sanitized_content

        return {
            'message': message,
            'reply_channel': reply_channel,
            'user_id': user_id,
            'validation_result': validation_result
        }
        validation_result = validate_user_input(message.content, user_id, "dm")
        
        if not validation_result["is_safe"]:
            await self._handle_unsafe_content(message, validation_result)
            return

        # Use sanitized content
        sanitized_content = validation_result["sanitized_content"]
        if validation_result["warnings"]:
            logger.warning(
                f"SECURITY: Input warnings for user {user_id} in DM: {validation_result['warnings']}"
            )

        # Replace original message content with sanitized version
        message.content = sanitized_content
        
        # Return processed message info for further handling
        return {
            'message': message,
            'reply_channel': reply_channel,
            'user_id': user_id,
            'validation_result': validation_result
        }
    
    async def handle_guild_message(self, message):
        """Handle guild (server) message."""
        # Configurable response behavior:
        # DISCORD_RESPOND_MODE options:
        #   mention (default)  -> only reply when explicitly mentioned
        #   name               -> reply when bot name OR fallback name appears as a whole word OR mentioned
        #   all                -> reply to any non-command message in guild channel (acts like a chat bot)
        # Backward compatibility: if REQUIRE_DISCORD_MENTION=true force mention mode.

        try:
            respond_mode = os.getenv("DISCORD_RESPOND_MODE", "mention").lower().strip()
            if os.getenv("REQUIRE_DISCORD_MENTION", "false").lower() == "true":
                respond_mode = "mention"
        except Exception:
            respond_mode = "mention"

        # Fast‑path for commands (always allow the command system to process first)
        # Commands are handled by discord.py after this method returns from process_commands
        # We avoid double-processing: if command prefix matches, let process_commands handle and exit early
        command_prefix = os.getenv("DISCORD_COMMAND_PREFIX", "!")
        if message.content.startswith(command_prefix):
            await self.bot.process_commands(message)
            return False

        bot_name = os.getenv("DISCORD_BOT_NAME", "").lower()
        fallback_name = "whisperengine"
        content_lower = message.content.lower()
        content_words = content_lower.split()

        should_active_reply = False

        # Mention always triggers active reply
        if self.bot.user in message.mentions:
            should_active_reply = True
        else:
            if respond_mode == "name":
                # Check if bot name appears anywhere in message (improved detection)
                name_found = False
                if bot_name:
                    # Check both as separate word and as substring
                    if bot_name in content_words or bot_name in content_lower:
                        name_found = True
                # Also check fallback name
                if fallback_name in content_words or fallback_name in content_lower:
                    name_found = True
                
                if name_found:
                    should_active_reply = True
                    logger.debug(f"Bot name detected in message: '{message.content[:50]}...'")
            elif respond_mode == "all":
                should_active_reply = True
            # mention mode (default) leaves should_active_reply False unless mentioned

        # Optional verbose logging when debugging interaction issues
        if logger.isEnabledFor(logging.INFO) and should_active_reply:
            logger.info(
                "💬 Guild message triggering reply (mode=%s, author=%s, channel=%s): %.80s",
                respond_mode,
                getattr(message.author, 'name', 'unknown'),
                getattr(message.channel, 'name', 'dm'),
                message.content.replace("\n", " "),
            )
        elif logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Guild message received (mode=%s, reply=%s, author=%s, channel=%s)",
                respond_mode,
                should_active_reply,
                getattr(message.author, 'name', 'unknown'),
                getattr(message.channel, 'name', 'dm'),
            )

        return should_active_reply
    
    async def handle_mention_message(self, message):
        """Handle message where bot is mentioned."""
        reply_channel = message.channel
        user_id = str(message.author.id)
        logger.info(f"[CONV-CTX] Handling mention message_id={message.id} user_id={user_id} channel_id={getattr(message.channel, 'id', None)} guild_id={getattr(message.guild, 'id', None)} content='{message.content[:60]}'")

        # Remove mentions from content
        content = message.content
        logger.info(f"[CONV-CTX] Original message content: '{message.content}'")
        for mention in message.mentions:
            if mention == self.bot.user:
                content = (
                    content.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "").strip()
                )
        logger.info(f"[CONV-CTX] Content after mention removal: '{content}'")

        if not content:
            logger.info(f"[CONV-CTX] No content after mention removal, processing as command")
            await self.bot.process_commands(message)
            return None

        # Security validation for guild messages
        validation_result = validate_user_input(content, user_id, "server_channel")
        if not validation_result["is_safe"]:
            logger.error(
                f"SECURITY: Unsafe input detected from user {user_id} in server {message.guild.name}"
            )
            logger.error(f"SECURITY: Blocked patterns: {validation_result['blocked_patterns']}")
            security_msg = f"⚠️ {message.author.mention} Your message contains content that could not be processed for security reasons. Please rephrase your message."
            await message.reply(security_msg, mention_author=False)  # mention_author=False since we already include the mention
            return None

        content = validation_result["sanitized_content"]
        if validation_result["warnings"]:
            logger.warning(
                f"SECURITY: Input warnings for user {user_id} in server {message.guild.name}: {validation_result['warnings']}"
            )

        return {
            'content': content,  # Content after mention removal and sanitization
            'user_id': user_id,
            'reply_channel': reply_channel
        }
    
    async def _handle_unsafe_content(self, message, validation_result):
        """Handle unsafe content with appropriate response."""
        user_id = str(message.author.id)
        
        logger.error(f"SECURITY: Unsafe input detected from user {user_id}")
        logger.error(f"SECURITY: Blocked patterns: {validation_result['blocked_patterns']}")
        
        # Fallback to text warning
        reply_channel = message.channel
        await reply_channel.send(
            "⚠️ Your message contains content that could not be processed for security reasons. Please rephrase your message."
        )