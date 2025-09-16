"""
Async Discord Commands for Context Boundaries and Privacy Controls

This module provides Discord bot commands for users to manage their privacy
preferences and consent settings for cross-context memory sharing.

Commands:
- !privacy - View current privacy settings
- !privacy_level <level> - Set privacy level
- !privacy_consent <response> - Respond to consent requests
- !privacy_audit - View recent privacy decisions

SECURITY FEATURE: User consent and control for Insufficient Context Boundaries fix
Uses PostgreSQL backend for better data integrity and performance.
"""

import logging

import discord
from discord.ext import commands

from src.security.async_context_boundaries_security import (
    get_async_context_boundaries_manager,
)
from src.security.context_boundaries_security import ConsentStatus, PrivacyLevel

logger = logging.getLogger(__name__)


class AsyncContextBoundariesCommands(commands.Cog):
    """Async Discord commands for privacy and context boundary management"""

    def __init__(self, bot):
        self.bot = bot
        self.boundaries_manager = get_async_context_boundaries_manager()

    async def cog_load(self):
        """Initialize the boundaries manager when cog loads"""
        await self.boundaries_manager.initialize()

    async def cog_unload(self):
        """Clean up when cog unloads"""
        await self.boundaries_manager.close()

    @commands.command(name="privacy")
    async def privacy_settings(self, ctx):
        """Show current privacy settings"""
        user_id = str(ctx.author.id)

        try:
            preferences = await self.boundaries_manager.get_user_preferences(user_id)

            embed = discord.Embed(
                title="🔒 Your Privacy Settings",
                description="Control how your information is shared between different contexts",
                color=0x3498DB,
            )

            # Current privacy level
            level_descriptions = {
                PrivacyLevel.STRICT: "🔒 **Strict** - Maximum privacy, minimal cross-context sharing",
                PrivacyLevel.MODERATE: "⚖️ **Moderate** - Balanced privacy with some cross-context sharing",
                PrivacyLevel.PERMISSIVE: "🔓 **Permissive** - More sharing allowed for convenience",
            }

            embed.add_field(
                name="Privacy Level",
                value=level_descriptions.get(
                    preferences.privacy_level, f"Unknown: {preferences.privacy_level}"
                ),
                inline=False,
            )

            # Cross-context permissions
            permissions = []
            permissions.append(
                f"🌐 Cross-server sharing: {'✅ Allowed' if preferences.allow_cross_server else '❌ Blocked'}"
            )
            permissions.append(
                f"📤 DM to server sharing: {'✅ Allowed' if preferences.allow_dm_to_server else '❌ Blocked'}"
            )
            permissions.append(
                f"📥 Server to DM sharing: {'✅ Allowed' if preferences.allow_server_to_dm else '❌ Blocked'}"
            )
            permissions.append(
                f"🔓 Private to public sharing: {'✅ Allowed' if preferences.allow_private_to_public else '❌ Blocked'}"
            )

            embed.add_field(
                name="Cross-Context Permissions", value="\\n".join(permissions), inline=False
            )

            # Consent status
            consent_info = {
                ConsentStatus.NOT_ASKED: "⏳ Not asked yet",
                ConsentStatus.GRANTED: "✅ Granted",
                ConsentStatus.DENIED: "❌ Denied",
                ConsentStatus.EXPIRED: "⏰ Expired",
            }

            embed.add_field(
                name="Consent Status",
                value=consent_info.get(
                    preferences.consent_status, f"Unknown: {preferences.consent_status}"
                ),
                inline=True,
            )

            # Custom rules
            if preferences.custom_rules:
                custom_rules_text = []
                for rule_type, allowed in preferences.custom_rules.items():
                    status = "✅ Allowed" if allowed else "❌ Blocked"
                    custom_rules_text.append(f"{rule_type}: {status}")

                embed.add_field(
                    name="Custom Rules", value="\\n".join(custom_rules_text), inline=False
                )

            # Usage instructions
            embed.add_field(
                name="Commands",
                value="""
                `!privacy_level <strict|moderate|permissive>` - Change privacy level
                `!privacy_audit` - View recent privacy decisions
                `!privacy_help` - Get detailed help
                """,
                inline=False,
            )

            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text=f"Last updated: {preferences.updated_timestamp}")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error showing privacy settings for user {user_id}: {e}")
            await ctx.send("❌ Error retrieving your privacy settings. Please try again later.")

    @commands.command(name="privacy_level")
    async def set_privacy_level(self, ctx, level: str | None = None):
        """Set privacy level (strict, moderate, permissive)"""
        user_id = str(ctx.author.id)

        if not level:
            await ctx.send(
                "❌ Please specify a privacy level: `strict`, `moderate`, or `permissive`"
            )
            return

        level = level.lower()

        try:
            if level == "strict":
                new_level = PrivacyLevel.STRICT
            elif level == "moderate":
                new_level = PrivacyLevel.MODERATE
            elif level == "permissive":
                new_level = PrivacyLevel.PERMISSIVE
            else:
                await ctx.send(
                    "❌ Invalid privacy level. Choose from: `strict`, `moderate`, `permissive`"
                )
                return

            await self.boundaries_manager.update_user_preferences(
                user_id=user_id, privacy_level=new_level
            )

            level_descriptions = {
                PrivacyLevel.STRICT: "🔒 **Strict** - Maximum privacy protection",
                PrivacyLevel.MODERATE: "⚖️ **Moderate** - Balanced privacy settings",
                PrivacyLevel.PERMISSIVE: "🔓 **Permissive** - More sharing for convenience",
            }

            embed = discord.Embed(
                title="✅ Privacy Level Updated",
                description=f"Your privacy level has been set to: {level_descriptions[new_level]}",
                color=0x2ECC71,
            )

            await ctx.send(embed=embed)
            logger.info(f"User {user_id} updated privacy level to {new_level.value}")

        except Exception as e:
            logger.error(f"Error updating privacy level for user {user_id}: {e}")
            await ctx.send("❌ Error updating your privacy level. Please try again later.")

    @commands.command(name="privacy_audit")
    async def privacy_audit(self, ctx, limit: int = 10):
        """View recent privacy decisions"""
        user_id = str(ctx.author.id)

        if limit > 50:
            limit = 50  # Cap at 50 for performance

        try:
            audit_entries = await self.boundaries_manager.get_audit_history(user_id, limit)

            if not audit_entries:
                embed = discord.Embed(
                    title="📋 Privacy Audit Log",
                    description="No privacy decisions recorded yet.",
                    color=0x95A5A6,
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title=f"📋 Privacy Audit Log (Last {len(audit_entries)} entries)",
                description="Recent privacy boundary decisions",
                color=0x3498DB,
            )

            for _i, entry in enumerate(audit_entries[:10]):  # Show max 10 in embed
                timestamp = entry["request_timestamp"]
                if hasattr(timestamp, "strftime"):
                    time_str = timestamp.strftime("%Y-%m-%d %H:%M")
                else:
                    time_str = str(timestamp)[:16]  # Truncate if string

                decision_emoji = {
                    "allowed": "✅",
                    "blocked": "❌",
                    "consent_requested": "❓",
                    "allowed_once": "✅",
                    "denied_once": "❌",
                    "allowed_always": "✅",
                    "denied_always": "❌",
                }.get(entry["decision"], "❔")

                embed.add_field(
                    name=f"{decision_emoji} {entry['source_context']} → {entry['target_context']}",
                    value=f"{entry['reason']}\\n*{time_str}*",
                    inline=False,
                )

            if len(audit_entries) > 10:
                embed.set_footer(text=f"Showing 10 of {len(audit_entries)} entries")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error showing privacy audit for user {user_id}: {e}")
            await ctx.send("❌ Error retrieving your privacy audit log. Please try again later.")

    @commands.command(name="privacy_help")
    async def privacy_help(self, ctx):
        """Show detailed privacy help"""
        embed = discord.Embed(
            title="🔒 Privacy System Help",
            description="Understanding your privacy controls",
            color=0x3498DB,
        )

        embed.add_field(
            name="Privacy Levels",
            value="""
            **🔒 Strict** - Maximum privacy
            • No cross-server sharing
            • No DM ↔ server sharing
            • No private → public sharing

            **⚖️ Moderate** - Balanced approach
            • Cross-server sharing allowed
            • DM ↔ server sharing blocked
            • Private → public sharing blocked

            **🔓 Permissive** - Convenience focused
            • Most sharing allowed
            • Still protects private → public
            """,
            inline=False,
        )

        embed.add_field(
            name="Context Types",
            value="""
            **DM** - Direct messages with the bot
            **Public Channel** - Public server channels
            **Private Channel** - Private server channels
            **Cross-Server** - Between different servers
            """,
            inline=False,
        )

        embed.add_field(
            name="Commands",
            value="""
            `!privacy` - View current settings
            `!privacy_level <level>` - Change privacy level
            `!privacy_audit [limit]` - View decision history
            `!privacy_cleanup` - Clean old audit entries
            """,
            inline=False,
        )

        embed.add_field(
            name="Data Protection",
            value="""
            • All settings stored securely in PostgreSQL
            • Audit trail for compliance
            • You control your data sharing
            • Settings persist across sessions
            """,
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(name="privacy_cleanup")
    async def privacy_cleanup(self, ctx):
        """Clean up old audit entries (admin command or user consent)"""
        user_id = str(ctx.author.id)

        # For now, allow users to clean their own data
        # In production, you might want admin-only or consent-based cleanup

        try:
            # Clean entries older than 90 days
            cleaned_count = await self.boundaries_manager.cleanup_old_audit_entries(90)

            embed = discord.Embed(
                title="🧹 Privacy Data Cleanup",
                description=f"Cleaned up {cleaned_count} old audit entries (older than 90 days)",
                color=0x2ECC71,
            )

            await ctx.send(embed=embed)
            logger.info(
                f"Privacy cleanup performed by user {user_id}, cleaned {cleaned_count} entries"
            )

        except Exception as e:
            logger.error(f"Error during privacy cleanup for user {user_id}: {e}")
            await ctx.send("❌ Error during privacy cleanup. Please try again later.")


async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(AsyncContextBoundariesCommands(bot))
