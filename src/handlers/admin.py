"""
Admin command handlers for Discord bot
Includes debug, health monitoring, backup management, job scheduling, and system status
"""

import logging
import discord
from discord.ext import commands
from typing import Optional
import asyncio
import time
import os

logger = logging.getLogger(__name__)


class AdminCommandHandlers:
    """Handles admin-only commands"""

    def __init__(
        self,
        bot,
        llm_client,
        memory_manager,
        backup_manager,
        conversation_history,
        health_monitor,
        job_scheduler,
        context_memory_manager,
        phase2_integration,
    ):
        self.bot = bot
        self.llm_client = llm_client
        self.memory_manager = memory_manager
        self.backup_manager = backup_manager
        self.conversation_history = conversation_history
        self.health_monitor = health_monitor
        self.job_scheduler = job_scheduler
        self.context_memory_manager = context_memory_manager
        self.phase2_integration = phase2_integration

    def register_commands(self, is_admin):
        """Register all admin commands"""

        # Capture self reference for nested functions
        admin_handler_instance = self

        @self.bot.command(name="debug")
        async def toggle_debug(ctx, action: str = "status"):
            """Toggle debug logging on/off or check status (admin only)"""
            await admin_handler_instance._debug_handler(ctx, action, is_admin)

        @self.bot.command(name="schedule_followup")
        async def schedule_followup(ctx, user_mention, hours: int = 24):
            """Schedule a follow-up message for a user (admin only)"""
            await admin_handler_instance._schedule_followup_handler(
                ctx, user_mention, hours, is_admin
            )

        @self.bot.command(name="job_status")
        async def job_status(ctx, job_id: Optional[str] = None):
            """Check job scheduler status or specific job status (admin only)"""
            await admin_handler_instance._job_status_handler(ctx, job_id, is_admin)

        @self.bot.command(name="followup_settings")
        async def followup_settings(ctx, setting: str = "status"):
            """Manage your follow-up message preferences (opt-in feature)"""
            await admin_handler_instance._followup_settings_handler(ctx, setting)

        @self.bot.command(name="health")
        async def health_check(ctx):
            """Show system health status (admin only)"""
            await admin_handler_instance._health_check_handler(ctx, is_admin)

        @self.bot.command(name="memory_stats")
        async def memory_stats(ctx):
            """Show memory system statistics (admin only)"""
            await admin_handler_instance._memory_stats_handler(ctx, is_admin)

        @self.bot.command(name="create_backup")
        async def create_backup(ctx):
            """Create a backup of the memory system (admin only)"""
            await admin_handler_instance._create_backup_handler(ctx, is_admin)

        @self.bot.command(name="list_backups")
        async def list_backups(ctx):
            """List available backups (admin only)"""
            await admin_handler_instance._list_backups_handler(ctx, is_admin)

        @self.bot.command(name="system_status")
        async def system_status(ctx):
            """Show comprehensive system status (admin only)"""
            await admin_handler_instance._system_status_handler(ctx, is_admin)

        @self.bot.command(name="emotional_intelligence", aliases=["ei_status", "emotional_status"])
        async def emotional_intelligence_status(ctx):
            """Show the status of the Predictive Emotional Intelligence system"""
            await self._emotional_intelligence_handler(ctx)

    async def _debug_handler(self, ctx, action, is_admin):
        """Handle debug command"""
        if not is_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions.")
            return

        logger.info(f"Debug command called by {ctx.author.name} with action: {action}")

        current_level = logging.getLogger().getEffectiveLevel()
        is_debug = current_level == logging.DEBUG

        if action.lower() == "on":
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("Debug logging enabled via command")
            await ctx.send("✅ Debug logging enabled.")
        elif action.lower() == "off":
            logging.getLogger().setLevel(logging.INFO)
            logger.info("Debug logging disabled via command")
            await ctx.send("✅ Debug logging disabled.")
        elif action.lower() == "status":
            status = "enabled" if is_debug else "disabled"
            await ctx.send(f"🔍 Debug logging is currently **{status}**.")
        else:
            await ctx.send("Usage: `!debug [on|off|status]`")

    async def _schedule_followup_handler(self, ctx, user_mention, hours, is_admin):
        """Handle schedule followup command"""
        if not is_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions.")
            return

        if not self.job_scheduler:
            await ctx.send("❌ Job scheduler is not available.")
            return

        try:
            # Extract user ID from mention
            if user_mention.startswith("<@") and user_mention.endswith(">"):
                user_id = user_mention[2:-1]
                if user_id.startswith("!"):
                    user_id = user_id[1:]
            else:
                await ctx.send("❌ Please mention a valid user (e.g., @username)")
                return

            # Check if the user has opted in to follow-ups
            postgres_pool = getattr(self.context_memory_manager, "postgres_pool", None)
            if postgres_pool:
                async with postgres_pool.acquire() as conn:
                    result = await conn.fetchval(
                        """
                        SELECT follow_ups_enabled FROM user_profiles WHERE user_id = $1
                    """,
                        user_id,
                    )

                    user_opted_in = result if result is not None else False

                    if not user_opted_in:
                        embed = discord.Embed(
                            title="⚠️ User Not Opted In",
                            description=f"<@{user_id}> has not opted in to follow-up messages.",
                            color=0xFFAA00,
                        )
                        embed.add_field(
                            name="Note",
                            value="The follow-up will be scheduled but won't be sent unless they opt in using `!followup_settings on`.",
                            inline=False,
                        )
                        embed.add_field(
                            name="Suggestion",
                            value=f"Consider asking <@{user_id}> to try the experimental follow-up feature first.",
                            inline=False,
                        )
                        await ctx.send(embed=embed)

            # Schedule the follow-up
            job_id = await self.job_scheduler.schedule_follow_up_message(
                user_id=user_id,
                delay_hours=hours,
                message_context={"scheduled_by": ctx.author.id, "channel": ctx.channel.id},
            )

            await ctx.send(
                f"✅ Follow-up message scheduled for <@{user_id}> in {hours} hours.\nJob ID: `{job_id}`"
            )
            logger.info(
                f"Admin {ctx.author.name} scheduled follow-up for user {user_id} in {hours} hours"
            )

        except Exception as e:
            logger.error(f"Failed to schedule follow-up: {e}")
            await ctx.send(f"❌ Failed to schedule follow-up: {e}")

    async def _job_status_handler(self, ctx, job_id, is_admin):
        """Handle job status command"""
        if not is_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions.")
            return

        if not self.job_scheduler:
            await ctx.send("❌ Job scheduler is not available.")
            return

        try:
            if job_id:
                # Check specific job
                job_info = await self.job_scheduler.get_job_status(job_id)
                if job_info:
                    embed = discord.Embed(title=f"Job Status: {job_id}", color=0x00FF00)
                    embed.add_field(name="Type", value=job_info["job_type"], inline=True)
                    embed.add_field(name="Status", value=job_info["status"], inline=True)
                    embed.add_field(name="Scheduled", value=job_info["scheduled_time"], inline=True)

                    if job_info["error_message"]:
                        embed.add_field(name="Error", value=job_info["error_message"], inline=False)

                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"❌ Job `{job_id}` not found.")
            else:
                # Check overall scheduler status
                stats = await self.job_scheduler.get_scheduler_stats()

                embed = discord.Embed(
                    title="Job Scheduler Status", color=0x00FF00 if stats["running"] else 0xFF0000
                )
                embed.add_field(
                    name="Status",
                    value="🟢 Running" if stats["running"] else "🔴 Stopped",
                    inline=True,
                )

                # Status counts
                status_counts = stats.get("status_counts", {})
                for status, count in status_counts.items():
                    embed.add_field(name=f"{status.title()} Jobs", value=str(count), inline=True)

                # Recent stats
                recent = stats.get("recent_24h", {})
                if recent:
                    embed.add_field(
                        name="24h Executions",
                        value=str(recent.get("total_executions", 0)),
                        inline=True,
                    )
                    embed.add_field(
                        name="24h Success Rate",
                        value=f"{(recent.get('successful_executions', 0) / max(recent.get('total_executions', 1), 1) * 100):.1f}%",
                        inline=True,
                    )

                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            await ctx.send(f"❌ Failed to get job status: {e}")

    async def _followup_settings_handler(self, ctx, setting):
        """Handle followup settings command"""
        user_id = str(ctx.author.id)

        if not self.job_scheduler:
            await ctx.send("❌ Follow-up system is not available.")
            return

        try:
            postgres_pool = getattr(self.context_memory_manager, "postgres_pool", None)
            if not postgres_pool:
                await ctx.send("❌ Database not available.")
                return

            if setting.lower() == "off" or setting.lower() == "disable":
                # Disable follow-ups for user
                async with postgres_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO user_profiles (user_id, follow_ups_enabled)
                        VALUES ($1, FALSE)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET follow_ups_enabled = FALSE
                    """,
                        user_id,
                    )

                await ctx.send(
                    "✅ Follow-up messages disabled. You won't receive automatic follow-ups."
                )

            elif setting.lower() == "on" or setting.lower() == "enable":
                # Enable follow-ups for user
                async with postgres_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO user_profiles (user_id, follow_ups_enabled)
                        VALUES ($1, TRUE)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET follow_ups_enabled = TRUE
                    """,
                        user_id,
                    )

                await ctx.send(
                    "✅ Follow-up messages enabled! I'll check in with you if you're away for a while. This is an experimental feature - thanks for testing!"
                )

            else:
                # Show current status
                async with postgres_pool.acquire() as conn:
                    result = await conn.fetchval(
                        """
                        SELECT follow_ups_enabled FROM user_profiles WHERE user_id = $1
                    """,
                        user_id,
                    )

                enabled = result if result is not None else False  # Default to disabled (opt-in)
                status = "enabled" if enabled else "disabled"

                embed = discord.Embed(
                    title="Follow-up Settings", color=0x00FF00 if enabled else 0xFF0000
                )
                embed.add_field(name="Status", value=f"Follow-ups are **{status}**", inline=False)
                if not enabled:
                    embed.add_field(
                        name="🧪 Experimental Feature",
                        value="Follow-up messages are an opt-in experimental feature. Use `!followup_settings on` to enable.",
                        inline=False,
                    )
                embed.add_field(
                    name="Usage", value="`!followup_settings [on|off|status]`", inline=False
                )
                embed.add_field(
                    name="What are follow-ups?",
                    value="If enabled, I'll send you a friendly check-in message if you haven't chatted with me in a while.",
                    inline=False,
                )

                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to manage follow-up settings: {e}")
            await ctx.send(f"❌ Failed to manage settings: {e}")

    async def _health_check_handler(self, ctx, is_admin):
        """Handle health check command"""
        if not is_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions.")
            return

        if not self.health_monitor:
            await ctx.send("❌ Health monitor not available.")
            return

        try:
            await ctx.send("🔍 Performing health check...")
            health_status = await self.health_monitor.perform_health_check()

            # Create embed
            embed = discord.Embed(
                title="🏥 System Health Report",
                color=0x2ECC71 if health_status["overall_status"] == "healthy" else 0xE74C3C,
            )

            embed.add_field(
                name="Overall Status",
                value=f"**{health_status['overall_status'].upper()}**",
                inline=True,
            )
            embed.add_field(name="Uptime", value=self.health_monitor.get_uptime(), inline=True)
            embed.add_field(name="Last Check", value=f"<t:{int(time.time())}:R>", inline=True)

            # Component statuses
            for component, status in health_status["components"].items():
                status_emoji = (
                    "✅"
                    if status["status"] == "healthy"
                    else "❌" if status["status"] == "error" else "⚠️"
                )
                embed.add_field(
                    name=f"{status_emoji} {component.title()}",
                    value=status.get("error", "Operational"),
                    inline=True,
                )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            await ctx.send(f"❌ Health check failed: {str(e)}")

    async def _memory_stats_handler(self, ctx, is_admin):
        """Handle memory stats command"""
        if not is_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions.")
            return

        try:
            stats = self.memory_manager.get_collection_stats()
            conv_stats = self.conversation_history.get_stats()

            embed = discord.Embed(title="📊 Memory System Statistics", color=0x3498DB)
            embed.add_field(
                name="User Memories", value=stats.get("total_memories", "Unknown"), inline=True
            )
            embed.add_field(
                name="Global Facts", value=stats.get("total_global_facts", "Unknown"), inline=True
            )
            embed.add_field(name="Active Conversations", value=conv_stats["channels"], inline=True)
            embed.add_field(name="Cached Messages", value=conv_stats["total_messages"], inline=True)
            embed.add_field(
                name="User Collection",
                value=stats.get("user_collection_name", "Unknown"),
                inline=True,
            )
            embed.add_field(
                name="Global Collection",
                value=stats.get("global_collection_name", "Unknown"),
                inline=True,
            )
            embed.add_field(
                name="Avg Messages/Channel",
                value=f"{conv_stats['avg_messages_per_channel']:.1f}",
                inline=True,
            )

            await ctx.send(embed=embed)
            logger.debug("Sent memory statistics")
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            await ctx.send(f"❌ Error retrieving memory statistics: {str(e)}")

    async def _create_backup_handler(self, ctx, is_admin):
        """Handle create backup command"""
        if not is_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions.")
            return

        try:
            await ctx.send("🔄 Creating backup... This may take a moment.")

            backup_path = self.backup_manager.create_backup(include_metadata=True)

            embed = discord.Embed(
                title="✅ Backup Created Successfully",
                description=f"Backup saved to: `{os.path.basename(backup_path)}`",
                color=0x2ECC71,
            )

            # Get backup info
            backup_info = self.backup_manager.verify_backup(backup_path)
            if backup_info["valid"]:
                size_mb = backup_info["info"].get("size_mb", 0)
                embed.add_field(name="Backup Size", value=f"{size_mb:.2f} MB", inline=True)

                metadata_count = backup_info["info"].get("metadata_count", 0)
                if metadata_count > 0:
                    embed.add_field(name="Documents", value=str(metadata_count), inline=True)

            await ctx.send(embed=embed)
            logger.info(f"Admin {ctx.author.name} created backup: {backup_path}")

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            await ctx.send(f"❌ Error creating backup: {str(e)}")

    async def _list_backups_handler(self, ctx, is_admin):
        """Handle list backups command"""
        if not is_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions.")
            return

        try:
            backups = self.backup_manager.list_backups()

            if not backups:
                await ctx.send("📦 No backups found.")
                return

            embed = discord.Embed(title="📦 Available Backups", color=0x3498DB)

            for i, backup in enumerate(backups[:10], 1):  # Show max 10 backups
                timestamp = backup.get("timestamp", "Unknown")
                size_mb = backup.get("size_mb", 0)

                # Format timestamp for display
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(timestamp.replace("_", " "))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = timestamp

                embed.add_field(
                    name=f"{i}. Backup {timestamp}",
                    value=f"📅 {formatted_time}\n💾 {size_mb:.2f} MB",
                    inline=True,
                )

            if len(backups) > 10:
                embed.set_footer(text=f"Showing 10 of {len(backups)} backups")

            await ctx.send(embed=embed)
            logger.debug(f"Listed {len(backups)} backups for admin {ctx.author.name}")

        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            await ctx.send(f"❌ Error listing backups: {str(e)}")

    async def _system_status_handler(self, ctx, is_admin):
        """Handle system status command"""
        if not is_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions.")
            return

        try:
            # Check LLM connection
            connection_ok = await self.llm_client.check_connection_async()
            service_info = f" ({self.llm_client.service_name})"
            llm_status = (
                f"✅ Connected{service_info}" if connection_ok else f"❌ Disconnected{service_info}"
            )

            # Get memory stats
            try:
                memory_stats = self.memory_manager.get_collection_stats()
                memory_status = f"✅ {memory_stats.get('total_memories', 0)} user memories, {memory_stats.get('total_global_facts', 0)} global facts"
            except Exception as e:
                memory_status = f"❌ Error: {str(e)}"

            # Get conversation stats
            conv_stats = self.conversation_history.get_stats()

            # Get backup count
            try:
                backup_count = len(self.backup_manager.list_backups())
                backup_status = f"✅ {backup_count} backups available"
            except Exception as e:
                backup_status = f"❌ Error: {str(e)}"

            embed = discord.Embed(title="🔧 System Status", color=0x3498DB)

            embed.add_field(name="🤖 LLM Server", value=llm_status, inline=False)
            embed.add_field(name="🧠 Memory System", value=memory_status, inline=False)
            embed.add_field(
                name="💬 Active Conversations",
                value=f"✅ {conv_stats['channels']} channels, {conv_stats['total_messages']} messages",
                inline=False,
            )
            embed.add_field(name="💾 Backup System", value=backup_status, inline=False)

            # Add bot info
            embed.add_field(
                name="📊 Bot Info",
                value=f"✅ Connected to {len(self.bot.guilds)} servers",
                inline=False,
            )

            await ctx.send(embed=embed)
            logger.debug(f"Sent system status to admin {ctx.author.name}")

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            await ctx.send(f"❌ Error retrieving system status: {str(e)}")

    async def _emotional_intelligence_handler(self, ctx):
        """Handle emotional intelligence status command"""
        try:
            # Check if the user is authorized (you can add more restrictions if needed)
            user_id = str(ctx.author.id)

            embed = discord.Embed(
                title="🎯 Predictive Emotional Intelligence Status", color=0x9B59B6
            )

            # Check if Phase 2 is enabled and available
            if self.phase2_integration:
                embed.add_field(
                    name="🟢 System Status",
                    value="**Enabled and Active**\n✅ Emotion Prediction\n✅ Mood Detection\n✅ Proactive Support\n✅ Comprehensive Analysis",
                    inline=False,
                )

                # Get system capabilities
                embed.add_field(
                    name="🧠 AI Capabilities",
                    value=(
                        "• **Emotional Pattern Recognition** - Predicts future emotional states\n"
                        "• **Real-time Mood Detection** - 5-category mood analysis\n"
                        "• **Stress & Alert Detection** - Early warning system\n"
                        "• **Proactive Support** - AI-initiated emotional intervention\n"
                        "• **Personalized Strategies** - Tailored emotional support"
                    ),
                    inline=False,
                )

                # Try to get user's emotional profile if available
                try:
                    test_result = (
                        await self.phase2_integration.process_message_with_emotional_intelligence(
                            user_id=user_id,
                            message="Hello, this is a status check",
                            conversation_context={
                                "source": "status_command",
                                "context": "emotional_intelligence_status",
                            },
                        )
                    )

                    if test_result:
                        embed.add_field(
                            name="📊 Your Emotional Profile",
                            value=(
                                f"**Current Mood:** {test_result.get('mood_assessment', {}).get('current_mood', 'Unknown')}\n"
                                f"**Stress Level:** {test_result.get('mood_assessment', {}).get('stress_level', 'Unknown')}\n"
                                f"**System Active:** ✅ Processing your emotional patterns"
                            ),
                            inline=False,
                        )
                    else:
                        embed.add_field(
                            name="📊 Your Profile",
                            value="No emotional data available yet. Start chatting to build your profile!",
                            inline=False,
                        )
                except Exception as e:
                    logger.debug(f"Could not get emotional profile for status: {e}")
                    embed.add_field(
                        name="📊 Your Profile",
                        value="Emotional analysis ready - continue chatting to build insights!",
                        inline=False,
                    )

                embed.add_field(
                    name="⚙️ Configuration",
                    value="**Unified AI System:** Full Capabilities Always Active\n**Integration:** Complete Emotional Intelligence",
                    inline=False,
                )

            embed.set_footer(text="Phase 2: Predictive Emotional Intelligence System")
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in emotional intelligence status command: {e}")
            await ctx.send("❌ An error occurred while checking emotional intelligence status.")
