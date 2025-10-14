"""
Performance Monitoring Discord Commands

Discord commands for accessing fidelity-first performance metrics and InfluxDB dashboards.
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import discord
from discord.ext import commands

from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class PerformanceCommands:
    """Discord commands for performance monitoring and fidelity metrics"""
    
    def __init__(self, bot):
        self.bot = bot
        # Import here to avoid circular import
        from src.monitoring.enhanced_performance_monitor import get_fidelity_performance_monitor
        self.performance_monitor = get_fidelity_performance_monitor()
    
    async def register_commands(self):
        """Register performance monitoring commands"""
        
        @self.bot.command(name="performance", aliases=["perf", "metrics"])
        async def performance_status(ctx):
            """Show current performance metrics and system health"""
            await self._performance_status_handler(ctx)
        
        @self.bot.command(name="fidelity_dashboard", aliases=["fidelity", "dashboard"])
        async def fidelity_dashboard(ctx, hours: int = 24):
            """Show fidelity-first performance dashboard"""
            await self._fidelity_dashboard_handler(ctx, hours)
        
        @self.bot.command(name="flush_metrics")
        async def flush_metrics(ctx):
            """Flush performance metrics to InfluxDB (admin only)"""
            await self._flush_metrics_handler(ctx)
    
    @handle_errors(
        category=ErrorCategory.SYSTEM_RESOURCE,
        severity=ErrorSeverity.MEDIUM,
        operation="performance_status"
    )
    async def _performance_status_handler(self, ctx):
        """Handle performance status command"""
        
        try:
            # Get system health
            health = self.performance_monitor.get_system_health()
            bottlenecks = self.performance_monitor.get_bottlenecks()
            
            # Create embed
            embed = discord.Embed(
                title="🎯 Performance Status",
                description="Real-time fidelity-first performance metrics",
                color=0x3498DB if health['overall_health'] == 'good' else 0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            
            # System health overview
            embed.add_field(
                name="🏥 System Health",
                value=f"**Status:** {health['overall_health'].title()}\n"
                      f"**Success Rate:** {health['avg_success_rate']:.1%}\n"
                      f"**Avg Response:** {health['avg_response_time_ms']:.0f}ms\n"
                      f"**Memory Usage:** {health['memory_usage_mb']:.0f}MB",
                inline=True
            )
            
            # Active operations
            embed.add_field(
                name="📊 Operations",
                value=f"**Active:** {health['active_operations']}\n"
                      f"**Total Metrics:** {health['total_metrics']}\n"
                      f"**Bottlenecks:** {health['bottlenecks_count']}\n"
                      f"**Memory Trend:** {health['memory_trend'].title()}",
                inline=True
            )
            
            # Recent performance stats
            all_stats = self.performance_monitor.get_all_stats()
            if all_stats:
                top_operations = sorted(
                    all_stats.items(), 
                    key=lambda x: x[1].total_calls, 
                    reverse=True
                )[:3]
                
                perf_text = []
                for op_name, stats in top_operations:
                    perf_text.append(
                        f"**{op_name}:** {stats.avg_duration_ms:.0f}ms "
                        f"({stats.success_rate:.1%}, {stats.total_calls} calls)"
                    )
                
                embed.add_field(
                    name="⚡ Top Operations",
                    value="\n".join(perf_text) if perf_text else "No operations recorded",
                    inline=False
                )
            
            # Bottlenecks warning
            if bottlenecks:
                bottleneck_text = []
                for bottleneck in bottlenecks[:3]:
                    bottleneck_text.append(
                        f"• **{bottleneck['operation']}**: {bottleneck['issue']}"
                    )
                
                embed.add_field(
                    name="⚠️ Performance Issues",
                    value="\n".join(bottleneck_text),
                    inline=False
                )
            
            embed.set_footer(text="Use !fidelity_dashboard for time series analysis")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error("Error in performance status handler: %s", str(e))
            await ctx.send("❌ **Error:** Could not retrieve performance status.")
    
    @handle_errors(
        category=ErrorCategory.SYSTEM_RESOURCE,
        severity=ErrorSeverity.MEDIUM,
        operation="fidelity_dashboard"
    )
    async def _fidelity_dashboard_handler(self, ctx, hours: int = 24):
        """Handle fidelity dashboard command"""
        
        # Validate hours parameter
        if hours < 1 or hours > 168:  # Max 1 week
            await ctx.send("❌ **Error:** Hours must be between 1 and 168 (1 week)")
            return
        
        try:
            # Send "thinking" message
            thinking_msg = await ctx.send("📊 Generating fidelity dashboard...")
            
            # Get dashboard data
            dashboard_data = await self.performance_monitor.get_fidelity_dashboard_data(hours)
            
            if "error" in dashboard_data:
                await thinking_msg.edit(content=f"❌ **Error:** {dashboard_data['error']}")
                return
            
            # Create comprehensive embed
            embed = discord.Embed(
                title="🎯 Fidelity-First Dashboard",
                description=f"Performance analysis for the last {hours} hours",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            
            # System overview
            system_health = dashboard_data.get("system_health", {})
            embed.add_field(
                name="🏥 System Health",
                value=f"**Overall:** {system_health.get('overall_health', 'unknown').title()}\n"
                      f"**Success Rate:** {system_health.get('avg_success_rate', 0):.1%}\n"
                      f"**Avg Response:** {system_health.get('avg_response_time_ms', 0):.0f}ms",
                inline=True
            )
            
            # In-memory performance stats
            in_memory_stats = dashboard_data.get("in_memory_stats", {})
            if in_memory_stats:
                top_ops = sorted(
                    in_memory_stats.items(),
                    key=lambda x: x[1].get('total_calls', 0),
                    reverse=True
                )[:3]
                
                stats_text = []
                for op_name, stats in top_ops:
                    stats_text.append(
                        f"**{op_name}:** {stats.get('avg_duration_ms', 0):.0f}ms "
                        f"({stats.get('success_rate', 0):.1%})"
                    )
                
                embed.add_field(
                    name="📈 Recent Performance",
                    value="\n".join(stats_text) if stats_text else "No data",
                    inline=True
                )
            
            # Time series data status
            time_series = dashboard_data.get("time_series_data", {})
            if "error" in time_series:
                embed.add_field(
                    name="📊 Time Series Data",
                    value=f"❌ InfluxDB: {time_series['error']}",
                    inline=False
                )
            elif "trends" in time_series:
                trend_count = len(time_series["trends"])
                embed.add_field(
                    name="📊 Time Series Data",
                    value=f"✅ InfluxDB: {trend_count} trend points\n"
                          f"Period: {time_series.get('period_hours', hours)} hours",
                    inline=False
                )
            else:
                embed.add_field(
                    name="📊 Time Series Data",
                    value="⚠️ InfluxDB: No trend data available",
                    inline=False
                )
            
            # Bottlenecks
            bottlenecks = dashboard_data.get("bottlenecks", [])
            if bottlenecks:
                bottleneck_text = []
                for bottleneck in bottlenecks[:3]:
                    bottleneck_text.append(f"• {bottleneck.get('operation', 'unknown')}: {bottleneck.get('issue', 'unknown')}")
                
                embed.add_field(
                    name="⚠️ Current Issues",
                    value="\n".join(bottleneck_text),
                    inline=False
                )
            
            embed.set_footer(text="InfluxDB dashboard: http://localhost:8087")
            
            await thinking_msg.edit(content="", embed=embed)
            
        except Exception as e:
            logger.error("Error in fidelity dashboard handler: %s", str(e))
            await ctx.send("❌ **Error:** Could not generate fidelity dashboard.")
    
    @handle_errors(
        category=ErrorCategory.SYSTEM_RESOURCE,
        severity=ErrorSeverity.LOW,
        operation="flush_metrics"
    )
    async def _flush_metrics_handler(self, ctx):
        """Handle flush metrics command (admin only)"""
        
        # Check if user is admin (you can customize this check)
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ **Error:** This command requires administrator permissions.")
            return
        
        try:
            thinking_msg = await ctx.send("🔄 Flushing metrics to InfluxDB...")
            
            # Flush metrics
            await self.performance_monitor.flush_metrics()
            
            embed = discord.Embed(
                title="✅ Metrics Flushed",
                description="Successfully flushed performance metrics to InfluxDB",
                color=0x2ECC71,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="📊 Status",
                value="All buffered metrics have been written to the time series database.",
                inline=False
            )
            
            embed.set_footer(text="View metrics at: http://localhost:8087")
            
            await thinking_msg.edit(content="", embed=embed)
            
        except Exception as e:
            logger.error("Error in flush metrics handler: %s", str(e))
            await ctx.send("❌ **Error:** Could not flush metrics to InfluxDB.")


async def setup_performance_commands(bot):
    """Setup performance monitoring commands"""
    performance_commands = PerformanceCommands(bot)
    await performance_commands.register_commands()
    logger.info("✅ Performance monitoring commands registered")