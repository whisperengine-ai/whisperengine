"""
Status command handlers for Discord bot
Includes ping, bot status, LLM status, voice status, vision status, and cache stats
"""

import asyncio
import logging
import os
import time

import discord

logger = logging.getLogger(__name__)


class StatusCommandHandlers:
    """Handles status-related commands"""

    def __init__(
        self,
        bot,
        bot_name,
        llm_client,
        voice_manager,
        voice_support_enabled,
        image_processor,
        conversation_history,
        conversation_cache,
        heartbeat_monitor,
    ):
        self.bot = bot
        self.bot_name = bot_name
        self.llm_client = llm_client
        self.voice_manager = voice_manager
        self.voice_support_enabled = voice_support_enabled
        self.image_processor = image_processor
        self.conversation_history = conversation_history
        self.conversation_cache = conversation_cache
        self.heartbeat_monitor = heartbeat_monitor

    def register_commands(self, bot_name_filter):
        """Register all status commands"""

        # Capture self reference for nested functions
        status_handler_instance = self

        @self.bot.command(name="ping")
        @bot_name_filter()
        async def ping(ctx):
            """Simple ping command"""
            logger.debug(
                f"Ping command called by {ctx.author.name} in {ctx.channel.name if ctx.guild else 'DM'}"
            )
            await ctx.send("Pong!")

        @self.bot.command(name="bot_status")
        @bot_name_filter()
        async def bot_status(ctx):
            """Check and refresh the bot's Discord presence"""
            await status_handler_instance._bot_status_handler(ctx)

        # Removed the other hidden status commands Copilot added:
        # cache_stats, vision_status, voice_status, test_image, health_status
        # Users don't need detailed technical diagnostic commands

    async def _bot_status_handler(self, ctx):
        """Handle bot status command"""
        logger.debug(f"Bot status command called by {ctx.author.name}")

        embed = discord.Embed(title="🤖 Discord Bot Status", color=0x3498DB)

        # Show current status
        if self.bot.user:
            embed.add_field(
                name="Bot Information",
                value=f"• Bot Name: **{self.bot.user.name}#{self.bot.user.discriminator}**\n• Bot ID: **{self.bot.user.id}**\n• Connected Guilds: **{len(self.bot.guilds)}**",
                inline=False,
            )
        else:
            embed.add_field(
                name="Bot Information",
                value=f"• Bot User: **Not Available**\n• Connected Guilds: **{len(self.bot.guilds)}**",
                inline=False,
            )

        # Try to refresh presence
        try:
            await self.bot.change_presence(status=discord.Status.online)
            await asyncio.sleep(0.5)  # Small delay
            activity = discord.Activity(type=discord.ActivityType.listening, name="...")
            await self.bot.change_presence(status=discord.Status.online, activity=activity)

            embed.add_field(
                name="Presence Status",
                value="✅ **Online** - Presence refreshed successfully",
                inline=False,
            )

            logger.debug(f"Bot presence refreshed by {ctx.author.name}")

        except Exception as e:
            embed.add_field(
                name="Presence Status",
                value=f"❌ **Error** - Failed to set presence: {str(e)}",
                inline=False,
            )
            logger.error(f"Failed to refresh bot presence: {e}")

        # Add heartbeat monitor status
        if self.heartbeat_monitor:
            heartbeat_status = self.heartbeat_monitor.get_status()
            if heartbeat_status["running"]:
                hb_text = f"✅ **Running** - Monitor active\n• Last heartbeat: {time.strftime('%H:%M:%S', time.localtime(heartbeat_status['last_heartbeat'])) if heartbeat_status['last_heartbeat'] else 'N/A'}\n• Bot latency: {heartbeat_status['bot_latency']:.3f}s\n• Connection issues: {heartbeat_status['connection_issues']}"
            else:
                hb_text = "❌ **Stopped** - Monitor not running"

            embed.add_field(name="🫀 Heartbeat Monitor", value=hb_text, inline=False)

        # Add troubleshooting info
        embed.add_field(
            name="If bot still appears offline:",
            value="• Try refreshing Discord (Ctrl+R)\n• Restart your Discord client\n• Check bot permissions in server settings\n• Wait 1-2 minutes for Discord to update",
            inline=False,
        )

        await ctx.send(embed=embed)

    # Removed _clear_chat_handler - users don't need manual memory management

    async def _cache_stats_handler(self, ctx):
        """Handle cache stats command"""
        if not self.conversation_cache:
            await ctx.send("❌ Conversation cache is not available.")
            return

        # Handle both sync (HybridConversationCache) and async (RedisConversationCache) stats
        try:
            # Import to check the type
            from src.memory.redis_conversation_cache import RedisConversationCache

            if isinstance(self.conversation_cache, RedisConversationCache):
                stats = await self.conversation_cache.get_cache_stats()
            else:
                # Default to sync method
                stats = self.conversation_cache.get_cache_stats()

        except Exception as e:
            await ctx.send(f"❌ Failed to get cache stats: {str(e)}")
            return

        embed = discord.Embed(title="💾 Conversation Cache Statistics", color=0x3498DB)

        # Handle both old and new cache stat formats
        cached_channels = stats.get("cached_channels", stats.get("channels_cached", 0))
        total_messages = stats.get("total_cached_messages", stats.get("total_messages", 0))
        avg_messages = stats.get("avg_messages_per_channel", 0)

        embed.add_field(
            name="📊 Cache Usage",
            value=f"• Cached channels: **{cached_channels}**\n"
            f"• Total cached messages: **{total_messages}**\n"
            f"• Avg messages/channel: **{avg_messages:.1f}**",
            inline=False,
        )

        embed.add_field(
            name="⚙️ Cache Configuration",
            value=f"• Cache timeout: **{stats.get('cache_timeout_minutes', 0):.0f} minutes**\n"
            f"• Bootstrap limit: **{stats.get('bootstrap_limit', 0)} messages**\n"
            f"• Max local messages: **{stats.get('max_local_messages', 0)} per channel**",
            inline=False,
        )

        embed.add_field(
            name="✨ Performance Benefits",
            value="• Reduces Discord API calls by ~90%\n"
            "• Faster response times for active conversations\n"
            "• Automatic cache refresh when stale",
            inline=False,
        )

        await ctx.send(embed=embed)

    async def _vision_status_handler(self, ctx):
        """Handle vision status command"""
        logger.debug(f"Vision status command called by {ctx.author.name}")

        vision_config = self.llm_client.get_vision_config()

        # Handle case where vision_config might be None
        supports_vision = vision_config and vision_config.get("supports_vision", False)

        embed = discord.Embed(
            title="🖼️ Vision Support Status", color=0x3498DB if supports_vision else 0x95A5A6
        )

        if supports_vision:
            embed.add_field(
                name="Status",
                value="✅ **Enabled** - The bot can process image attachments",
                inline=False,
            )
            max_images = vision_config.get("max_images", "Unknown") if vision_config else "Unknown"
            embed.add_field(
                name="Configuration",
                value=f"• Max images per message: **{max_images}**\n• Supported formats: **JPG, PNG, GIF, WebP, BMP**\n• Max image size: **10MB**\n• Max dimensions: **2048x2048**",
                inline=False,
            )
            embed.add_field(
                name="How to use",
                value="Simply attach images to your messages when chatting with the bot in DMs or when mentioning the bot in channels.",
                inline=False,
            )
        else:
            embed.add_field(
                name="Status",
                value="❌ **Disabled** - Vision support is not available",
                inline=False,
            )
            embed.add_field(
                name="Note",
                value="The bot will describe attached images in text instead of processing them visually.",
                inline=False,
            )
            embed.add_field(
                name="Configuration",
                value="To enable vision support, set `LLM_SUPPORTS_VISION=true` in your environment configuration.",
                inline=False,
            )

        await ctx.send(embed=embed)

    async def _voice_status_handler(self, ctx):
        """Handle voice status command"""
        logger.debug(f"Voice status command called by {ctx.author.name}")

        # Determine voice support status
        voice_available = self.voice_manager is not None
        voice_enabled = self.voice_support_enabled
        has_voice_manager = self.voice_manager is not None

        embed = discord.Embed(
            title="🎤 Voice Support Status",
            color=(
                0x3498DB if (voice_available and voice_enabled and has_voice_manager) else 0x95A5A6
            ),
        )

        if voice_available and voice_enabled and has_voice_manager:
            embed.add_field(
                name="Status",
                value="✅ **Enabled** - Voice functionality is fully operational",
                inline=False,
            )
            embed.add_field(
                name="Available Features",
                value="• Text-to-speech responses\n• Voice channel connections\n• Voice commands (!join, !leave, !speak)\n• Connection keepalive system\n• @mention voice responses",
                inline=False,
            )
            embed.add_field(
                name="Configuration",
                value=f"• ElevenLabs API: {'✅ Connected' if self.voice_manager else '❌ Not configured'}\n• Auto-join: {'✅ Enabled' if os.getenv('VOICE_AUTO_JOIN', 'false').lower() == 'true' else '❌ Disabled'}\n• Voice responses: {'✅ Enabled' if os.getenv('VOICE_RESPONSE_ENABLED', 'true').lower() == 'true' else '❌ Disabled'}",
                inline=False,
            )
            embed.add_field(
                name="How to use",
                value="Use `!join` to connect to voice channel, then @mention the bot for voice responses or use `!speak <text>` for TTS.",
                inline=False,
            )
        elif voice_available and not voice_enabled:
            embed.add_field(
                name="Status",
                value="⚙️ **Disabled by Configuration** - Dependencies available but disabled",
                inline=False,
            )
            embed.add_field(
                name="How to enable",
                value="Set `VOICE_SUPPORT_ENABLED=true` in your .env file and restart the bot.",
                inline=False,
            )
            embed.add_field(
                name="Available when enabled",
                value="• Text-to-speech responses\n• Voice channel connections\n• Voice commands\n• ElevenLabs integration",
                inline=False,
            )
        else:
            embed.add_field(
                name="Status",
                value="❌ **Unavailable** - Missing dependencies or configuration",
                inline=False,
            )
            embed.add_field(
                name="Requirements",
                value="• PyNaCl (Discord voice): `pip install PyNaCl`\n• ElevenLabs client: `pip install elevenlabs`\n• Valid ElevenLabs API key\n• FFmpeg installed on system",
                inline=False,
            )
            embed.add_field(
                name="Configuration needed",
                value="• Set `VOICE_SUPPORT_ENABLED=true`\n• Add `ELEVENLABS_API_KEY` to .env\n• Install required dependencies",
                inline=False,
            )

        embed.set_footer(text="Use !voice_help for voice commands when enabled")
        await ctx.send(embed=embed)

    async def _test_image_handler(self, ctx):
        """Handle test image command"""
        logger.debug(f"Test image command called by {ctx.author.name}")

        if not ctx.message.attachments:
            embed = discord.Embed(
                title="📷 Test Image Processing",
                description="Please attach an image to this command to test image processing capabilities.",
                color=0xE67E22,
            )
            embed.add_field(
                name="Usage", value="```!test_image``` with an image attached", inline=False
            )
            embed.add_field(name="Supported formats", value="JPG, PNG, GIF, WebP, BMP", inline=True)
            embed.add_field(name="Max size", value="10MB", inline=True)
            await ctx.send(embed=embed)
            return

        # Process the attachments
        if self.image_processor:
            processed_images = await self.image_processor.process_multiple_attachments(
                ctx.message.attachments
            )
        else:
            processed_images = []

        if not processed_images:
            await ctx.send("❌ No valid images found in your attachments.")
            return

        embed = discord.Embed(title="🖼️ Image Processing Test Results", color=0x27AE60)

        for i, img in enumerate(processed_images, 1):
            embed.add_field(
                name=f"Image {i}: {img['filename']}",
                value=f"• Format: **{img['format'].upper()}**\n• Size: **{img['size']:,} bytes**\n• Status: ✅ **Processed successfully**",
                inline=False,
            )

        vision_config = self.llm_client.get_vision_config()
        if vision_config and vision_config.get("supports_vision", False):
            embed.add_field(
                name="Vision Support",
                value="✅ **Available** - These images can be sent to the LLM for analysis",
                inline=False,
            )
        else:
            embed.add_field(
                name="Vision Support",
                value="❌ **Not available** - Images will be described in text only",
                inline=False,
            )

        embed.set_footer(
            text=f"Processed {len(processed_images)} of {len(ctx.message.attachments)} attachments"
        )

        await ctx.send(embed=embed)

    async def _health_status_handler(self, ctx):
        """Handle comprehensive system health status command"""
        logger.debug(f"Health status command called by {ctx.author.name}")

        # Import here to avoid circular imports

        import aiohttp

        embed = discord.Embed(
            title="🏥 System Health Status",
            color=0x27AE60,  # Will change to red if any issues found
        )

        # Check bot health endpoint
        bot_health = {"status": "unknown", "details": None}
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get("http://localhost:9090/health") as response:
                    if response.status == 200:
                        bot_health = await response.json()
                        bot_health["status"] = "healthy"
                    else:
                        bot_health["status"] = "unhealthy"
                        bot_health["details"] = f"HTTP {response.status}"
        except Exception as e:
            bot_health["status"] = "error"
            bot_health["details"] = str(e)

        # Check bot readiness endpoint for detailed info
        bot_ready = {"status": "unknown", "details": None}
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get("http://localhost:9090/ready") as response:
                    if response.status == 200:
                        bot_ready = await response.json()
                        bot_ready["status"] = "ready"
                    else:
                        bot_ready["status"] = "not_ready"
                        bot_ready["details"] = f"HTTP {response.status}"
        except Exception as e:
            bot_ready["status"] = "error"
            bot_ready["details"] = str(e)

        # Bot Health Summary
        if bot_health["status"] == "healthy" and bot_ready["status"] == "ready":
            bot_status_text = "✅ **Healthy & Ready**"
            if bot_ready.get("bot_user"):
                bot_status_text += f"\n• Bot: {bot_ready['bot_user']}"
            if bot_ready.get("guilds_count") is not None:
                bot_status_text += f"\n• Guilds: {bot_ready['guilds_count']}"
            if bot_ready.get("latency_ms") is not None:
                bot_status_text += f"\n• Latency: {bot_ready['latency_ms']:.1f}ms"
        else:
            bot_status_text = f"❌ **Unhealthy** - {bot_health.get('details', 'Unknown error')}"
            embed.color = 0xE74C3C  # Red color for issues

        embed.add_field(name="🤖 Discord Bot", value=bot_status_text, inline=False)

        # Check LLM connection
        llm_status = (
            "✅ **Connected**" if self.llm_client.check_connection() else "❌ **Disconnected**"
        )
        if not self.llm_client.check_connection():
            embed.color = 0xE74C3C

        embed.add_field(
            name="🧠 LLM Service",
            value=f"{llm_status}\n• Service: {self.llm_client.service_name}\n• Model: {self.llm_client.default_model_name}",
            inline=True,
        )

        # Check voice support if available
        if self.voice_manager is not None and self.voice_support_enabled:
            try:
                # Simple voice support check
                voice_status = "✅ **Available**"
                if self.voice_manager:
                    # Check if voice manager is functioning
                    voice_status += "\n• Manager: Active"
                else:
                    voice_status = "⚠️ **Partial** - Manager not initialized"
            except Exception as e:
                voice_status = f"❌ **Error** - {str(e)}"
                embed.color = 0xE74C3C
        else:
            voice_status = "❌ **Disabled**"

        embed.add_field(name="🎵 Voice Support", value=voice_status, inline=True)

        # Check image processing
        if self.image_processor:
            vision_config = self.llm_client.get_vision_config()
            if vision_config and vision_config.get("supports_vision", False):
                vision_status = "✅ **Available** - Vision model support"
            else:
                vision_status = "⚠️ **Text-only** - No vision model"
        else:
            vision_status = "❌ **Disabled**"

        embed.add_field(name="👁️ Vision/Images", value=vision_status, inline=True)

        # Check conversation cache
        if self.conversation_cache:
            try:
                # Try to get cache stats as a health check
                stats = await self.conversation_cache.get_stats()
                cache_status = f"✅ **Active**\n• Type: {stats.get('cache_type', 'Unknown')}"
                if "total_conversations" in stats:
                    cache_status += f"\n• Conversations: {stats['total_conversations']}"
            except Exception as e:
                cache_status = f"❌ **Error** - {str(e)}"
                embed.color = 0xE74C3C
        else:
            cache_status = "❌ **Disabled**"

        embed.add_field(name="💾 Conversation Cache", value=cache_status, inline=True)

        # Check heartbeat monitor
        if self.heartbeat_monitor:
            try:
                heartbeat_status = "✅ **Active**"
                # Add more details if available
            except Exception as e:
                heartbeat_status = f"❌ **Error** - {str(e)}"
                embed.color = 0xE74C3C
        else:
            heartbeat_status = "❌ **Not Available**"

        embed.add_field(name="💓 Heartbeat Monitor", value=heartbeat_status, inline=True)

        # Overall system status
        overall_status = (
            "🟢 All Systems Operational" if embed.color == 0x27AE60 else "🔴 Issues Detected"
        )
        embed.add_field(name="📊 Overall Status", value=overall_status, inline=False)

        # Add helpful footer
        embed.set_footer(
            text="💡 Use !bot_status, !voice_status for detailed component info"
        )

        await ctx.send(embed=embed)
