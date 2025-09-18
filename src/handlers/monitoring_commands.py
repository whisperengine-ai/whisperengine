"""
Monitoring Command Handlers

Discord command handlers for monitoring system control and visibility.
Provides admin commands for health checks, metrics, and dashboard access.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands

from ..monitoring import get_monitoring_manager
from ..monitoring.health_monitor import HealthStatus
from ..monitoring.error_tracker import ErrorSeverity

logger = logging.getLogger(__name__)


class MonitoringCommands:
    """Discord commands for monitoring system."""
    
    def __init__(self, bot, **dependencies):
        self.bot = bot
        self.monitoring_manager = get_monitoring_manager()
        
        # Check if user is admin (placeholder - integrate with actual admin check)
        self.is_admin = dependencies.get('is_admin', lambda ctx: False)
        
        # Monitoring commands initialized quietly
    
    def register_commands(self, bot_name_filter, is_admin):
        """Register monitoring commands."""
        self.is_admin = is_admin
        
        @self.bot.command(name='monitor_health', aliases=['monitor_status'])
        async def health_command(ctx):
            """Get detailed system monitoring and health status."""
            if not self.is_admin(ctx):
                await ctx.send("❌ This command requires administrator privileges.")
                return
            
            try:
                await ctx.send("🔍 Checking system monitoring health...")
                
                # Perform health check
                health = await self.monitoring_manager.check_health(full_check=True)
                
                if not health:
                    await ctx.send("❌ Health monitoring unavailable")
                    return
                
                # Create health status embed
                embed = discord.Embed(
                    title="🏥 System Health Status",
                    color=self._get_status_color(health.overall_status),
                    timestamp=datetime.now()
                )
                
                # Overall status
                status_emoji = self._get_status_emoji(health.overall_status)
                embed.add_field(
                    name="Overall Status",
                    value=f"{status_emoji} {health.overall_status.value.upper()}",
                    inline=True
                )
                
                # System uptime
                embed.add_field(
                    name="System Uptime",
                    value=str(health.uptime),
                    inline=True
                )
                
                # Performance score
                if health.performance_score:
                    embed.add_field(
                        name="Performance Score",
                        value=f"{health.performance_score:.1f}/100",
                        inline=True
                    )
                
                # Component status summary
                component_summary = self._format_component_summary(health.to_dict()['components'])
                if component_summary:
                    embed.add_field(
                        name="Components",
                        value=component_summary,
                        inline=False
                    )
                
                # Dashboard link
                dashboard_url = self.monitoring_manager.get_dashboard_url()
                if dashboard_url:
                    embed.add_field(
                        name="Dashboard",
                        value=f"[View Dashboard]({dashboard_url})",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error("Error in health command: %s", e)
                await ctx.send(f"❌ Error checking health: {str(e)}")
        
        @self.bot.command(name='errors')
        async def errors_command(ctx, hours: int = 24):
            """Get error summary for the specified hours."""
            if not self.is_admin(ctx):
                await ctx.send("❌ This command requires administrator privileges.")
                return
            
            try:
                # Validate hours parameter
                if hours < 1 or hours > 168:  # Max 1 week
                    await ctx.send("❌ Hours must be between 1 and 168 (1 week)")
                    return
                
                await ctx.send(f"📊 Getting error summary for last {hours} hours...")
                
                error_summary = self.monitoring_manager.get_error_summary(hours)
                
                if not error_summary:
                    await ctx.send("❌ Error tracking unavailable")
                    return
                
                # Create error summary embed
                embed = discord.Embed(
                    title=f"🐛 Error Summary ({hours}h)",
                    color=0xff6b6b if error_summary.get('unresolved_critical_errors', 0) > 0 else 0x4ecdc4,
                    timestamp=datetime.now()
                )
                
                # Total errors
                total_errors = error_summary.get('total_errors', 0)
                embed.add_field(
                    name="Total Errors",
                    value=str(total_errors),
                    inline=True
                )
                
                # Error rate
                error_rate = error_summary.get('error_rate_per_hour', 0)
                embed.add_field(
                    name="Error Rate",
                    value=f"{error_rate:.2f}/hour",
                    inline=True
                )
                
                # Critical errors
                critical_errors = error_summary.get('unresolved_critical_errors', 0)
                embed.add_field(
                    name="Critical Errors",
                    value=f"🚨 {critical_errors}" if critical_errors > 0 else "✅ 0",
                    inline=True
                )
                
                # Errors by category
                errors_by_category = error_summary.get('errors_by_category', {})
                if errors_by_category:
                    category_text = "\\n".join([
                        f"• {cat}: {count}" 
                        for cat, count in sorted(errors_by_category.items())
                    ])
                    embed.add_field(
                        name="By Category",
                        value=category_text or "None",
                        inline=True
                    )
                
                # Errors by severity
                errors_by_severity = error_summary.get('errors_by_severity', {})
                if errors_by_severity:
                    severity_text = "\\n".join([
                        f"• {sev}: {count}" 
                        for sev, count in sorted(errors_by_severity.items())
                    ])
                    embed.add_field(
                        name="By Severity",
                        value=severity_text or "None",
                        inline=True
                    )
                
                # Most common error types
                common_errors = error_summary.get('most_common_error_types', [])
                if common_errors:
                    common_text = "\\n".join([
                        f"• {error_type}: {count}" 
                        for error_type, count in common_errors[:5]
                    ])
                    embed.add_field(
                        name="Most Common",
                        value=common_text,
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error("Error in errors command: %s", e)
                await ctx.send(f"❌ Error getting error summary: {str(e)}")
        
        @self.bot.command(name='engagement', aliases=['metrics'])
        async def engagement_command(ctx):
            """Get user engagement metrics."""
            if not self.is_admin(ctx):
                await ctx.send("❌ This command requires administrator privileges.")
                return
            
            try:
                await ctx.send("📈 Getting engagement metrics...")
                
                engagement_summary = self.monitoring_manager.get_engagement_summary()
                
                if not engagement_summary:
                    await ctx.send("❌ Engagement tracking unavailable")
                    return
                
                # Create engagement embed
                embed = discord.Embed(
                    title="📊 User Engagement Metrics",
                    color=0x3498db,
                    timestamp=datetime.now()
                )
                
                # Active users
                embed.add_field(
                    name="Active Users (24h)",
                    value=str(engagement_summary.total_active_users),
                    inline=True
                )
                
                # New vs returning users
                embed.add_field(
                    name="New Users",
                    value=str(engagement_summary.new_users),
                    inline=True
                )
                
                embed.add_field(
                    name="Returning Users",
                    value=str(engagement_summary.returning_users),
                    inline=True
                )
                
                # Session metrics
                avg_duration = engagement_summary.avg_session_duration / 60  # Convert to minutes
                embed.add_field(
                    name="Avg Session Duration",
                    value=f"{avg_duration:.1f} minutes",
                    inline=True
                )
                
                # Conversation metrics
                embed.add_field(
                    name="Total Conversations",
                    value=str(engagement_summary.total_conversations),
                    inline=True
                )
                
                if engagement_summary.avg_conversation_length > 0:
                    embed.add_field(
                        name="Avg Conversation Length",
                        value=f"{engagement_summary.avg_conversation_length:.1f} messages",
                        inline=True
                    )
                
                # Platform breakdown
                platform_info = []
                for platform, metrics in engagement_summary.platform_breakdown.items():
                    platform_info.append(f"• {platform.title()}: {metrics.active_users_today} users")
                
                if platform_info:
                    embed.add_field(
                        name="Platform Usage",
                        value="\\n".join(platform_info),
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error("Error in engagement command: %s", e)
                await ctx.send(f"❌ Error getting engagement metrics: {str(e)}")
        
        @self.bot.command(name='dashboard')
        async def dashboard_command(ctx):
            """Get monitoring dashboard information."""
            if not self.is_admin(ctx):
                await ctx.send("❌ This command requires administrator privileges.")
                return
            
            try:
                dashboard_url = self.monitoring_manager.get_dashboard_url()
                is_running = self.monitoring_manager.is_dashboard_running()
                
                embed = discord.Embed(
                    title="📊 Monitoring Dashboard",
                    color=0x2ecc71 if is_running else 0x95a5a6,
                    timestamp=datetime.now()
                )
                
                if is_running and dashboard_url:
                    embed.add_field(
                        name="Status",
                        value="🟢 Running",
                        inline=True
                    )
                    embed.add_field(
                        name="Dashboard URL",
                        value=f"[Open Dashboard]({dashboard_url})",
                        inline=True
                    )
                    embed.description = f"Dashboard is running at {dashboard_url}"
                else:
                    embed.add_field(
                        name="Status",
                        value="🔴 Not Running",
                        inline=True
                    )
                    embed.description = "Dashboard is not currently available. It may be disabled or web dependencies may be missing."
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error("Error in dashboard command: %s", e)
                await ctx.send(f"❌ Error getting dashboard info: {str(e)}")
        
        @self.bot.command(name='monitoring_overview', aliases=['mon_overview', 'overview'])
        async def overview_command(ctx):
            """Get comprehensive monitoring overview."""
            if not self.is_admin(ctx):
                await ctx.send("❌ This command requires administrator privileges.")
                return
            
            try:
                await ctx.send("📋 Generating monitoring overview...")
                
                overview = self.monitoring_manager.get_system_overview()
                
                # Create overview embed
                embed = discord.Embed(
                    title="🔍 System Monitoring Overview",
                    color=0x3498db,
                    timestamp=datetime.fromisoformat(overview['timestamp'])
                )
                
                # Monitoring components status
                enabled = overview.get('monitoring_enabled', {})
                status_text = "\\n".join([
                    f"• Health: {'✅' if enabled.get('health') else '❌'}",
                    f"• Engagement: {'✅' if enabled.get('engagement') else '❌'}",
                    f"• Errors: {'✅' if enabled.get('errors') else '❌'}",
                    f"• Dashboard: {'✅' if enabled.get('dashboard') else '❌'}"
                ])
                embed.add_field(
                    name="Monitoring Components",
                    value=status_text,
                    inline=True
                )
                
                # Health summary
                health = overview.get('health')
                if health:
                    health_status = health.get('overall_status', 'unknown')
                    health_emoji = self._get_status_emoji_from_string(health_status)
                    embed.add_field(
                        name="System Health",
                        value=f"{health_emoji} {health_status.upper()}",
                        inline=True
                    )
                
                # Engagement summary
                engagement = overview.get('engagement')
                if engagement:
                    embed.add_field(
                        name="Active Users",
                        value=str(engagement.get('total_active_users', 0)),
                        inline=True
                    )
                
                # Error summary
                errors = overview.get('errors')
                if errors:
                    critical_errors = errors.get('unresolved_critical_errors', 0)
                    error_rate = errors.get('error_rate_per_hour', 0)
                    embed.add_field(
                        name="Errors (24h)",
                        value=f"🚨 {critical_errors} critical\\n📊 {error_rate:.1f}/hour",
                        inline=True
                    )
                
                # Dashboard info
                dashboard = overview.get('dashboard', {})
                dashboard_status = "✅ Available" if dashboard.get('available') else "❌ Unavailable"
                dashboard_url = dashboard.get('url')
                if dashboard_url:
                    dashboard_status += f"\\n[Open Dashboard]({dashboard_url})"
                
                embed.add_field(
                    name="Dashboard",
                    value=dashboard_status,
                    inline=True
                )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error("Error in overview command: %s", e)
                await ctx.send(f"❌ Error getting overview: {str(e)}")
    
    def _get_status_color(self, status: HealthStatus) -> int:
        """Get Discord embed color for health status."""
        color_map = {
            HealthStatus.HEALTHY: 0x2ecc71,    # Green
            HealthStatus.WARNING: 0xf39c12,    # Orange  
            HealthStatus.CRITICAL: 0xe74c3c,   # Red
            HealthStatus.UNKNOWN: 0x95a5a6     # Gray
        }
        return color_map.get(status, 0x95a5a6)
    
    def _get_status_emoji(self, status: HealthStatus) -> str:
        """Get emoji for health status."""
        emoji_map = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.CRITICAL: "🚨",
            HealthStatus.UNKNOWN: "❓"
        }
        return emoji_map.get(status, "❓")
    
    def _get_status_emoji_from_string(self, status: str) -> str:
        """Get emoji for health status from string."""
        emoji_map = {
            'healthy': "✅",
            'warning': "⚠️", 
            'critical': "🚨",
            'unknown': "❓"
        }
        return emoji_map.get(status.lower(), "❓")
    
    def _format_component_summary(self, components: Dict[str, Any]) -> str:
        """Format component status summary."""
        if not components:
            return "No components monitored"
        
        summary_lines = []
        for comp_type, comp_health in components.items():
            status = comp_health.get('status', 'unknown')
            emoji = self._get_status_emoji_from_string(status)
            comp_name = comp_type.replace('_', ' ').title()
            summary_lines.append(f"{emoji} {comp_name}")
        
        return "\\n".join(summary_lines)