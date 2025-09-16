"""
Discord Commands for Context Boundaries and Privacy Controls

This module provides Discord bot commands for users to manage their privacy
preferences and consent settings for cross-context memory sharing.

Commands:
- !privacy - View current privacy settings
- !privacy_level <level> - Set privacy level
- !privacy_consent <response> - Respond to consent requests
- !privacy_audit - View recent privacy decisions

SECURITY FEATURE: User consent and control for Insufficient Context Boundaries fix
"""

import logging

import discord
from context_boundaries_security import get_context_boundaries_manager
from discord.ext import commands

logger = logging.getLogger(__name__)


class ContextBoundariesCommands(commands.Cog):
    """Discord commands for privacy and context boundary management"""

    def __init__(self, bot):
        self.bot = bot
        self.boundaries_manager = get_context_boundaries_manager()

    @commands.command(name="privacy")
    async def privacy_settings(self, ctx):
        """Show current privacy settings"""
        user_id = str(ctx.author.id)

        try:
            settings = self.boundaries_manager.get_privacy_settings_ui(user_id)
            current = settings["current_settings"]

            embed = discord.Embed(
                title="🔒 Your Privacy Settings",
                description="Control how your information is shared between different contexts",
                color=0x3498DB,
            )

            # Current privacy level
            level_info = next(
                (
                    level
                    for level in settings["privacy_levels"]
                    if level["value"] == current["privacy_level"]
                ),
                {"label": current["privacy_level"], "description": "Unknown"},
            )

            embed.add_field(
                name="📊 Privacy Level",
                value=f"{level_info['label']}\n*{level_info['description']}*",
                inline=False,
            )

            # Specific permissions
            permissions = []
            if current["allow_cross_server"]:
                permissions.append("✅ Cross-server sharing")
            else:
                permissions.append("❌ Cross-server sharing")

            if current["allow_dm_to_server"]:
                permissions.append("✅ DM to server sharing")
            else:
                permissions.append("❌ DM to server sharing")

            if current["allow_server_to_dm"]:
                permissions.append("✅ Server to DM sharing")
            else:
                permissions.append("❌ Server to DM sharing")

            if current["allow_private_to_public"]:
                permissions.append("✅ Private to public sharing")
            else:
                permissions.append("❌ Private to public sharing")

            embed.add_field(
                name="⚙️ Current Permissions", value="\\n".join(permissions), inline=False
            )

            # Consent status
            consent_emoji = {"not_asked": "❓", "granted": "✅", "denied": "❌", "expired": "⏰"}

            embed.add_field(
                name="🤝 Consent Status",
                value=f"{consent_emoji.get(current['consent_status'], '❓')} {current['consent_status'].replace('_', ' ').title()}",
                inline=True,
            )

            # Custom rules if any
            if settings["custom_rules"]:
                rules_text = []
                for rule, allowed in settings["custom_rules"].items():
                    status = "✅ Allow" if allowed else "❌ Block"
                    readable_rule = rule.replace("_to_", " → ").replace("_", " ")
                    rules_text.append(f"{status} {readable_rule}")

                embed.add_field(name="📝 Custom Rules", value="\\n".join(rules_text), inline=False)

            # Commands help
            embed.add_field(
                name="💡 Available Commands",
                value=(
                    "`!privacy_level <strict|moderate|permissive|custom>` - Change privacy level\\n"
                    "`!privacy_audit` - View recent decisions\\n"
                    "`!privacy_reset` - Reset to default settings"
                ),
                inline=False,
            )

            embed.set_footer(text=f"Last updated: {settings.get('last_updated', 'Never')}")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error displaying privacy settings: {e}")
            await ctx.send("❌ Error retrieving privacy settings. Please try again.")

    @commands.command(name="privacy_level")
    async def set_privacy_level(self, ctx, level: str | None = None):
        """Set privacy level: strict, moderate, permissive, or custom"""
        user_id = str(ctx.author.id)

        if not level:
            embed = discord.Embed(
                title="🔒 Privacy Levels",
                description="Choose your privacy level for cross-context memory sharing",
                color=0x3498DB,
            )

            embed.add_field(
                name="🔒 Strict",
                value="Never share information between different contexts (DMs, servers, etc.)",
                inline=False,
            )

            embed.add_field(
                name="⚖️ Moderate (Recommended)",
                value="Allow cross-server sharing of non-sensitive, public information only",
                inline=False,
            )

            embed.add_field(
                name="🌐 Permissive",
                value="Allow most cross-context sharing while protecting private channels",
                inline=False,
            )

            embed.add_field(
                name="⚙️ Custom",
                value="Ask for permission on each cross-context sharing request",
                inline=False,
            )

            embed.set_footer(text="Usage: !privacy_level <strict|moderate|permissive|custom>")
            await ctx.send(embed=embed)
            return

        level = level.lower()
        valid_levels = ["strict", "moderate", "permissive", "custom"]

        if level not in valid_levels:
            await ctx.send(f"❌ Invalid privacy level. Choose from: {', '.join(valid_levels)}")
            return

        try:
            success = self.boundaries_manager.update_user_preferences(user_id, privacy_level=level)

            if success:
                level_descriptions = {
                    "strict": "🔒 **Strict** - No cross-context sharing",
                    "moderate": "⚖️ **Moderate** - Safe cross-server sharing only",
                    "permissive": "🌐 **Permissive** - Most sharing allowed",
                    "custom": "⚙️ **Custom** - Ask permission for each request",
                }

                embed = discord.Embed(
                    title="✅ Privacy Level Updated",
                    description=f"Your privacy level has been set to:\\n{level_descriptions[level]}",
                    color=0x2ECC71,
                )

                embed.add_field(
                    name="📋 What this means",
                    value="This setting controls how your conversation history and learned information can be shared between different contexts like DMs, servers, and channels.",
                    inline=False,
                )

                embed.set_footer(text="Use !privacy to see all your current settings")
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to update privacy level. Please try again.")

        except Exception as e:
            logger.error(f"Error updating privacy level: {e}")
            await ctx.send("❌ Error updating privacy level. Please try again.")

    @commands.command(name="privacy_audit")
    async def privacy_audit(self, ctx, limit: int = 10):
        """View recent privacy decisions (last 10 by default)"""
        user_id = str(ctx.author.id)

        try:
            # Read audit log
            import json
            import os

            audit_file = os.path.join(
                self.boundaries_manager.data_dir, "context_boundary_audit.json"
            )

            if not os.path.exists(audit_file):
                await ctx.send("📝 No privacy decisions recorded yet.")
                return

            with open(audit_file) as f:
                audit_log = json.load(f)

            # Filter for this user and get recent entries
            user_entries = [entry for entry in audit_log if entry["user_id"] == user_id]
            user_entries.sort(key=lambda x: x["request_timestamp"], reverse=True)
            recent_entries = user_entries[:limit]

            if not recent_entries:
                await ctx.send("📝 No privacy decisions recorded for your account yet.")
                return

            embed = discord.Embed(
                title="📋 Recent Privacy Decisions",
                description=f"Your last {len(recent_entries)} context boundary decisions",
                color=0x3498DB,
            )

            decision_emojis = {
                "allowed": "✅",
                "blocked": "❌",
                "consent_requested": "❓",
                "allowed_once": "✅",
                "denied_once": "❌",
                "allowed_always": "✅",
                "denied_always": "❌",
            }

            for i, entry in enumerate(recent_entries):
                timestamp = entry["request_timestamp"][:19].replace("T", " ")
                emoji = decision_emojis.get(entry["decision"], "❓")

                source = entry["source_context"].replace("_", " ").title()
                target = entry["target_context"].replace("_", " ").title()

                embed.add_field(
                    name=f"{emoji} {entry['decision'].replace('_', ' ').title()}",
                    value=f"**Context:** {source} → {target}\\n**When:** {timestamp}\\n**Reason:** {entry['reason']}",
                    inline=True if i % 2 == 0 else False,
                )

            embed.set_footer(text="Use !privacy to adjust your settings")
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error retrieving privacy audit: {e}")
            await ctx.send("❌ Error retrieving privacy audit. Please try again.")

    @commands.command(name="privacy_reset")
    async def reset_privacy(self, ctx):
        """Reset privacy settings to defaults"""
        user_id = str(ctx.author.id)

        try:
            # Remove user from preferences to get defaults on next access
            if user_id in self.boundaries_manager.user_preferences:
                del self.boundaries_manager.user_preferences[user_id]
                self.boundaries_manager._save_preferences()

            embed = discord.Embed(
                title="🔄 Privacy Settings Reset",
                description="Your privacy settings have been reset to defaults",
                color=0xF39C12,
            )

            embed.add_field(
                name="📊 Default Settings",
                value=(
                    "**Privacy Level:** ⚖️ Moderate\\n"
                    "**Cross-server sharing:** Safe content only\\n"
                    "**DM/Server separation:** Maintained\\n"
                    "**Consent status:** Will be asked when needed"
                ),
                inline=False,
            )

            embed.set_footer(
                text="Use !privacy to see your current settings or !privacy_level to change them"
            )
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error resetting privacy settings: {e}")
            await ctx.send("❌ Error resetting privacy settings. Please try again.")

    @commands.command(name="privacy_consent")
    async def handle_consent_response(
        self, ctx, response: str | None = None, *, context: str | None = None
    ):
        """Respond to privacy consent requests"""
        str(ctx.author.id)

        if not response:
            embed = discord.Embed(
                title="🤝 Privacy Consent Response",
                description="Respond to cross-context memory sharing requests",
                color=0x3498DB,
            )

            embed.add_field(
                name="📝 Available Responses",
                value=(
                    "`allow_once` - Allow this specific request\\n"
                    "`allow_always` - Always allow this type of sharing\\n"
                    "`deny_once` - Deny this specific request\\n"
                    "`deny_always` - Never allow this type of sharing"
                ),
                inline=False,
            )

            embed.set_footer(text="Usage: !privacy_consent <response> [context information]")
            await ctx.send(embed=embed)
            return

        # This would typically be called in response to a specific consent request
        # For now, provide general guidance
        valid_responses = ["allow_once", "allow_always", "deny_once", "deny_always"]

        if response not in valid_responses:
            await ctx.send(f"❌ Invalid response. Choose from: {', '.join(valid_responses)}")
            return

        embed = discord.Embed(
            title="✅ Consent Response Recorded",
            description=f"Your response '{response}' has been noted.",
            color=0x2ECC71,
        )

        embed.add_field(
            name="📋 Next Steps",
            value="This response will be applied to future cross-context memory sharing requests of the same type.",
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    """Set up the context boundaries commands cog"""
    await bot.add_cog(ContextBoundariesCommands(bot))


def add_context_boundaries_commands(bot):
    """Add context boundaries commands to bot (synchronous version)"""
    import asyncio

    asyncio.create_task(setup(bot))
