"""
Status command handlers for Discord bot
Includes ping, bot status, LLM status, voice status, vision status, and cache stats
"""
import logging
import discord
from discord.ext import commands
import asyncio
import time
import os

logger = logging.getLogger(__name__)

class StatusCommandHandlers:
    """Handles status-related commands"""
    
    def __init__(self, bot, bot_name, llm_client, voice_manager, voice_support_enabled, 
                 VOICE_AVAILABLE, image_processor, conversation_history, conversation_cache, 
                 heartbeat_monitor):
        self.bot = bot
        self.bot_name = bot_name
        self.llm_client = llm_client
        self.voice_manager = voice_manager
        self.voice_support_enabled = voice_support_enabled
        self.VOICE_AVAILABLE = VOICE_AVAILABLE
        self.image_processor = image_processor
        self.conversation_history = conversation_history
        self.conversation_cache = conversation_cache
        self.heartbeat_monitor = heartbeat_monitor
    
    def register_commands(self, bot_name_filter):
        """Register all status commands"""
        
        # Capture self reference for nested functions
        status_handler_instance = self
        
        @self.bot.command(name='ping')
        @bot_name_filter()
        async def ping(ctx):
            """Simple ping command"""
            logger.debug(f"Ping command called by {ctx.author.name} in {ctx.channel.name if ctx.guild else 'DM'}")
            await ctx.send('Pong!')
        
        @self.bot.command(name='llm_status')
        @bot_name_filter()
        async def llm_status(ctx):
            """Check if the LLM server is running and show configuration"""
            await status_handler_instance._llm_status_handler(ctx)
        
        @self.bot.command(name='bot_status')
        @bot_name_filter()
        async def bot_status(ctx):
            """Check and refresh the bot's Discord presence"""
            await status_handler_instance._bot_status_handler(ctx)
        
        @self.bot.command(name='clear_chat')
        @bot_name_filter()
        async def clear_chat(ctx):
            """Clear the conversation history in this channel"""
            await status_handler_instance._clear_chat_handler(ctx)
        
        @self.bot.command(name='cache_stats')
        @bot_name_filter()
        async def cache_stats(ctx):
            """Show conversation cache statistics"""
            await status_handler_instance._cache_stats_handler(ctx)
        
        @self.bot.command(name='vision_status')
        @bot_name_filter()
        async def vision_status(ctx):
            """Check if the LLM supports vision (image processing)"""
            await status_handler_instance._vision_status_handler(ctx)
        
        @self.bot.command(name='voice_status')
        @bot_name_filter()
        async def voice_status(ctx):
            """Check voice support status and configuration"""
            await status_handler_instance._voice_status_handler(ctx)
        
        @self.bot.command(name='test_image')
        @bot_name_filter()
        async def test_image(ctx):
            """Test image processing with an attached image"""
            await status_handler_instance._test_image_handler(ctx)
    
    async def _llm_status_handler(self, ctx):
        """Handle LLM status command"""
        logger.debug(f"LLM status command called by {ctx.author.name}")
        
        embed = discord.Embed(
            title="🤖 LLM Server Status",
            color=0x27ae60 if self.llm_client.check_connection() else 0xe74c3c
        )
        
        if self.llm_client.check_connection():
            logger.info("LLM status check: Connected")
            embed.add_field(
                name="Connection Status",
                value="✅ **Connected** - Server is running and responding",
                inline=False
            )
            
            # Show main service configuration
            api_key_status = "✅ Configured" if self.llm_client.api_key else "❌ Not set"
            embed.add_field(
                name="🤖 Main Chat Service",
                value=f"• Service: **{self.llm_client.service_name}**\n• API URL: **{self.llm_client.api_url}**\n• API Key: **{api_key_status}**\n• Model: **{self.llm_client.default_model_name}**\n• Max tokens: **{self.llm_client.default_max_tokens_chat:,}**",
                inline=False
            )
            
            # Show emotion analysis service configuration
            emotion_api_key_status = "✅ Configured" if self.llm_client.emotion_api_key else "❌ Not set"
            emotion_same_endpoint = self.llm_client.emotion_api_url == self.llm_client.api_url
            emotion_info = "Same as main service" if emotion_same_endpoint else f"• Service: **{self.llm_client.emotion_service_name}**\n• API URL: **{self.llm_client.emotion_api_url}**\n• API Key: **{emotion_api_key_status}**"
            
            embed.add_field(
                name="😊 Emotion Analysis Service",
                value=f"{emotion_info}\n• Model: **{self.llm_client.emotion_model_name}**\n• Max tokens (emotion): **{self.llm_client.max_tokens_emotion}**\n• Max tokens (trust): **{self.llm_client.max_tokens_trust_detection}**",
                inline=False
            )

            # Show facts analysis service configuration
            facts_api_key_status = "✅ Configured" if self.llm_client.facts_api_key else "❌ Not set"
            facts_same_endpoint = self.llm_client.facts_api_url == self.llm_client.api_url
            facts_info = "Same as main service" if facts_same_endpoint else f"• Service: **{self.llm_client.facts_service_name}**\n• API URL: **{self.llm_client.facts_api_url}**\n• API Key: **{facts_api_key_status}**"
            
            embed.add_field(
                name="📝 Facts Analysis Service",
                value=f"{facts_info}\n• Model: **{self.llm_client.facts_model_name}**\n• Max tokens (facts): **{self.llm_client.max_tokens_fact_extraction}**\n• Max tokens (personal): **{self.llm_client.max_tokens_personal_info}**\n• Max tokens (user facts): **{self.llm_client.max_tokens_user_facts}**",
                inline=False
            )
            
            # Show timeout configuration
            embed.add_field(
                name="⏱️ Timeout Configuration",
                value=f"• Request timeout: **{self.llm_client.request_timeout}s**\n• Connection timeout: **{self.llm_client.connection_timeout}s**",
                inline=False
            )
            
            # Show vision support
            vision_status = "✅ Enabled" if self.llm_client.supports_vision else "❌ Disabled"
            vision_details = f"**{vision_status}**"
            if self.llm_client.supports_vision:
                vision_config = self.llm_client.get_vision_config()
                if vision_config and 'max_images' in vision_config:
                    vision_details += f"\n• Max images: **{vision_config['max_images']}**"
            embed.add_field(
                name="Vision Support",
                value=vision_details,
                inline=False
            )
        else:
            logger.warning("LLM status check: Disconnected")
            embed.add_field(
                name="Connection Status",
                value="❌ **Disconnected** - Server is not responding",
                inline=False
            )
            # Different troubleshooting based on service type
            if self.llm_client.is_openrouter:
                troubleshooting = "• Check your OPENROUTER_API_KEY is valid\n• Verify your OpenRouter account has credits\n• Ensure the model name is correct"
            else:
                troubleshooting = "• Make sure your LLM provider (LM Studio/Ollama/etc.) is running\n• Check that the server is accessible\n• Verify the API endpoint configuration"
                
            embed.add_field(
                name="Troubleshooting",
                value=troubleshooting,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def _bot_status_handler(self, ctx):
        """Handle bot status command"""
        logger.debug(f"Bot status command called by {ctx.author.name}")
        
        embed = discord.Embed(
            title="🤖 Discord Bot Status",
            color=0x3498db
        )
        
        # Show current status
        if self.bot.user:
            embed.add_field(
                name="Bot Information",
                value=f"• Bot Name: **{self.bot.user.name}#{self.bot.user.discriminator}**\n• Bot ID: **{self.bot.user.id}**\n• Connected Guilds: **{len(self.bot.guilds)}**",
                inline=False
            )
        else:
            embed.add_field(
                name="Bot Information",
                value=f"• Bot User: **Not Available**\n• Connected Guilds: **{len(self.bot.guilds)}**",
                inline=False
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
                inline=False
            )
            
            logger.info(f"Bot presence refreshed by {ctx.author.name}")
            
        except Exception as e:
            embed.add_field(
                name="Presence Status",
                value=f"❌ **Error** - Failed to set presence: {str(e)}",
                inline=False
            )
            logger.error(f"Failed to refresh bot presence: {e}")
        
        # Add heartbeat monitor status
        if self.heartbeat_monitor:
            heartbeat_status = self.heartbeat_monitor.get_status()
            if heartbeat_status['running']:
                hb_text = f"✅ **Running** - Monitor active\n• Last heartbeat: {time.strftime('%H:%M:%S', time.localtime(heartbeat_status['last_heartbeat'])) if heartbeat_status['last_heartbeat'] else 'N/A'}\n• Bot latency: {heartbeat_status['bot_latency']:.3f}s\n• Connection issues: {heartbeat_status['connection_issues']}"
            else:
                hb_text = "❌ **Stopped** - Monitor not running"
            
            embed.add_field(
                name="🫀 Heartbeat Monitor",
                value=hb_text,
                inline=False
            )

        # Add troubleshooting info
        embed.add_field(
            name="If bot still appears offline:",
            value="• Try refreshing Discord (Ctrl+R)\n• Restart your Discord client\n• Check bot permissions in server settings\n• Wait 1-2 minutes for Discord to update",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def _clear_chat_handler(self, ctx):
        """Handle clear chat command"""
        logger.info(f"Clear chat command called by {ctx.author.name} in {ctx.channel.name if ctx.guild else 'DM'}")
        channel_id = str(ctx.channel.id)
        
        # Clear both old conversation history and new cache
        if self.conversation_history:
            self.conversation_history.clear_channel(channel_id)
        if self.conversation_cache:
            self.conversation_cache.clear_channel_cache(channel_id)
        
        logger.debug(f"Cleared conversation history and cache for channel {channel_id}")
        
        await ctx.send("✅ Conversation history has been cleared.")
    
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
        
        embed = discord.Embed(
            title="💾 Conversation Cache Statistics",
            color=0x3498db
        )
        
        # Handle both old and new cache stat formats
        cached_channels = stats.get('cached_channels', stats.get('channels_cached', 0))
        total_messages = stats.get('total_cached_messages', stats.get('total_messages', 0))
        avg_messages = stats.get('avg_messages_per_channel', 0)
        
        embed.add_field(
            name="📊 Cache Usage",
            value=f"• Cached channels: **{cached_channels}**\n"
                  f"• Total cached messages: **{total_messages}**\n"
                  f"• Avg messages/channel: **{avg_messages:.1f}**",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Cache Configuration",
            value=f"• Cache timeout: **{stats.get('cache_timeout_minutes', 0):.0f} minutes**\n"
                  f"• Bootstrap limit: **{stats.get('bootstrap_limit', 0)} messages**\n"
                  f"• Max local messages: **{stats.get('max_local_messages', 0)} per channel**",
            inline=False
        )
        
        embed.add_field(
            name="🚀 Performance Benefits",
            value="• Reduces Discord API calls by ~90%\n"
                  "• Faster response times for active conversations\n"
                  "• Automatic cache refresh when stale",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def _vision_status_handler(self, ctx):
        """Handle vision status command"""
        logger.debug(f"Vision status command called by {ctx.author.name}")
        
        vision_config = self.llm_client.get_vision_config()
        
        # Handle case where vision_config might be None
        supports_vision = vision_config and vision_config.get('supports_vision', False)
        
        embed = discord.Embed(
            title="🖼️ Vision Support Status",
            color=0x3498db if supports_vision else 0x95a5a6
        )
        
        if supports_vision:
            embed.add_field(
                name="Status",
                value="✅ **Enabled** - The bot can process image attachments",
                inline=False
            )
            max_images = vision_config.get('max_images', 'Unknown') if vision_config else 'Unknown'
            embed.add_field(
                name="Configuration",
                value=f"• Max images per message: **{max_images}**\n• Supported formats: **JPG, PNG, GIF, WebP, BMP**\n• Max image size: **10MB**\n• Max dimensions: **2048x2048**",
                inline=False
            )
            embed.add_field(
                name="How to use",
                value="Simply attach images to your messages when chatting with the bot in DMs or when mentioning the bot in channels.",
                inline=False
            )
        else:
            embed.add_field(
                name="Status",
                value="❌ **Disabled** - Vision support is not available",
                inline=False
            )
            embed.add_field(
                name="Note",
                value="The bot will describe attached images in text instead of processing them visually.",
                inline=False
            )
            embed.add_field(
                name="Configuration",
                value="To enable vision support, set `LLM_SUPPORTS_VISION=true` in your environment configuration.",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def _voice_status_handler(self, ctx):
        """Handle voice status command"""
        logger.debug(f"Voice status command called by {ctx.author.name}")
        
        # Determine voice support status
        voice_available = self.VOICE_AVAILABLE
        voice_enabled = self.voice_support_enabled
        has_voice_manager = self.voice_manager is not None
        
        embed = discord.Embed(
            title="🎤 Voice Support Status",
            color=0x3498db if (voice_available and voice_enabled and has_voice_manager) else 0x95a5a6
        )
        
        if voice_available and voice_enabled and has_voice_manager:
            embed.add_field(
                name="Status",
                value="✅ **Enabled** - Voice functionality is fully operational",
                inline=False
            )
            embed.add_field(
                name="Available Features",
                value="• Text-to-speech responses\n• Voice channel connections\n• Voice commands (!join, !leave, !speak)\n• Connection keepalive system\n• @mention voice responses",
                inline=False
            )
            embed.add_field(
                name="Configuration",
                value=f"• ElevenLabs API: {'✅ Connected' if self.voice_manager else '❌ Not configured'}\n• Auto-join: {'✅ Enabled' if os.getenv('VOICE_AUTO_JOIN', 'false').lower() == 'true' else '❌ Disabled'}\n• Voice responses: {'✅ Enabled' if os.getenv('VOICE_RESPONSE_ENABLED', 'true').lower() == 'true' else '❌ Disabled'}",
                inline=False
            )
            embed.add_field(
                name="How to use",
                value="Use `!join` to connect to voice channel, then @mention the bot for voice responses or use `!speak <text>` for TTS.",
                inline=False
            )
        elif voice_available and not voice_enabled:
            embed.add_field(
                name="Status",
                value="⚙️ **Disabled by Configuration** - Dependencies available but disabled",
                inline=False
            )
            embed.add_field(
                name="How to enable",
                value="Set `VOICE_SUPPORT_ENABLED=true` in your .env file and restart the bot.",
                inline=False
            )
            embed.add_field(
                name="Available when enabled",
                value="• Text-to-speech responses\n• Voice channel connections\n• Voice commands\n• ElevenLabs integration",
                inline=False
            )
        else:
            embed.add_field(
                name="Status",
                value="❌ **Unavailable** - Missing dependencies or configuration",
                inline=False
            )
            embed.add_field(
                name="Requirements",
                value="• PyNaCl (Discord voice): `pip install PyNaCl`\n• ElevenLabs client: `pip install elevenlabs`\n• Valid ElevenLabs API key\n• FFmpeg installed on system",
                inline=False
            )
            embed.add_field(
                name="Configuration needed",
                value="• Set `VOICE_SUPPORT_ENABLED=true`\n• Add `ELEVENLABS_API_KEY` to .env\n• Install required dependencies",
                inline=False
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
                color=0xe67e22
            )
            embed.add_field(
                name="Usage",
                value="```!test_image``` with an image attached",
                inline=False
            )
            embed.add_field(
                name="Supported formats",
                value="JPG, PNG, GIF, WebP, BMP",
                inline=True
            )
            embed.add_field(
                name="Max size",
                value="10MB",
                inline=True
            )
            await ctx.send(embed=embed)
            return
        
        # Process the attachments
        if self.image_processor:
            processed_images = await self.image_processor.process_multiple_attachments(ctx.message.attachments)
        else:
            processed_images = []
        
        if not processed_images:
            await ctx.send("❌ No valid images found in your attachments.")
            return
        
        embed = discord.Embed(
            title="🖼️ Image Processing Test Results",
            color=0x27ae60
        )
        
        for i, img in enumerate(processed_images, 1):
            embed.add_field(
                name=f"Image {i}: {img['filename']}",
                value=f"• Format: **{img['format'].upper()}**\n• Size: **{img['size']:,} bytes**\n• Status: ✅ **Processed successfully**",
                inline=False
            )
        
        vision_config = self.llm_client.get_vision_config()
        if vision_config and vision_config.get('supports_vision', False):
            embed.add_field(
                name="Vision Support",
                value="✅ **Available** - These images can be sent to the LLM for analysis",
                inline=False
            )
        else:
            embed.add_field(
                name="Vision Support",
                value="❌ **Not available** - Images will be described in text only",
                inline=False
            )
        
        embed.set_footer(text=f"Processed {len(processed_images)} of {len(ctx.message.attachments)} attachments")
        
        await ctx.send(embed=embed)