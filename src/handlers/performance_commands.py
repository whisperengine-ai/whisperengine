#!/usr/bin/env python3
"""
Performance Monitoring Command Handlers
Command handlers for monitoring and optimizing system performance in real-time
"""

import logging
from datetime import datetime
import discord
from discord.ext import commands
from src.utils.performance_monitor import performance_monitor, performance_optimizer

logger = logging.getLogger(__name__)


class PerformanceCommands:
    """Command handlers for performance monitoring and optimization"""
    
    def __init__(self, bot, **dependencies):
        self.bot = bot
        
        # Store dependencies passed from DiscordBotCore
        self.memory_manager = dependencies.get('memory_manager')
        self.llm_client = dependencies.get('llm_client')
        self.emotion_manager = dependencies.get('emotion_manager')
        
        # Start performance monitoring
        performance_monitor.start_monitoring()
        logger.info("📊 Performance monitoring commands initialized")
    
    def register_commands(self, bot_name_filter, is_admin):
        """Register performance monitoring commands"""
        
        @self.bot.command(name='perf', aliases=['performance', 'stats'])
        async def performance_status(ctx):
            """Show current system performance metrics"""
            try:
                health = performance_monitor.get_system_health()
                all_stats = performance_monitor.get_all_stats()
                
                # Create embed
                embed = discord.Embed(
                    title="📊 System Performance Dashboard",
                    color=0x00ff00 if health['overall_health'] == 'good' else 0xff6600,
                    timestamp=datetime.now()
                )
                
                # System health overview
                embed.add_field(
                    name="🏥 System Health",
                    value=f"**Status**: {health['overall_health'].title()}\n"
                          f"**Success Rate**: {health['avg_success_rate']:.1%}\n"
                          f"**Avg Response**: {health['avg_response_time_ms']:.0f}ms\n"
                          f"**Memory Usage**: {health['memory_usage_mb']:.0f}MB",
                    inline=True
                )
                
                # Resource usage
                embed.add_field(
                    name="⚡ Resources",
                    value=f"**CPU**: {health['cpu_percent']:.1f}%\n"
                          f"**Memory Trend**: {health['memory_trend'].title()}\n"
                          f"**Active Operations**: {health['active_operations']}\n"
                          f"**Total Metrics**: {health['total_metrics']}",
                    inline=True
                )
                
                # Top operations by response time
                if all_stats:
                    top_operations = sorted(
                        all_stats.items(), 
                        key=lambda x: x[1].avg_duration_ms, 
                        reverse=True
                    )[:3]
                    
                    operations_text = "\n".join([
                        f"**{op}**: {stats.avg_duration_ms:.0f}ms ({stats.total_calls} calls)"
                        for op, stats in top_operations
                    ])
                    
                    embed.add_field(
                        name="🔥 Slowest Operations",
                        value=operations_text or "No data available",
                        inline=False
                    )
                
                # Bottlenecks
                bottlenecks = performance_monitor.get_bottlenecks()
                if bottlenecks:
                    bottleneck_text = "\n".join([
                        f"⚠️ **{b['operation']}**: {b['issues'][0][:60]}..."
                        for b in bottlenecks[:3]
                    ])
                    embed.add_field(
                        name="🚨 Performance Issues",
                        value=bottleneck_text,
                        inline=False
                    )
                
                embed.set_footer(text="Use !optimize for optimization suggestions")
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error in performance status command: {e}")
                await ctx.send("❌ Error retrieving performance data. Check logs for details.")
        
        @self.bot.command(name='optimize', aliases=['perf-optimize', 'bottlenecks'])
        async def performance_optimize(ctx):
            """Get performance optimization recommendations"""
            try:
                report = performance_optimizer.get_optimization_report()
                
                # Split report into chunks for Discord's character limit
                chunks = self._split_message(report, 2000)
                
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        embed = discord.Embed(
                            title="🔧 Performance Optimization Report",
                            description=chunk,
                            color=0x0099ff,
                            timestamp=datetime.now()
                        )
                    else:
                        embed = discord.Embed(
                            title=f"🔧 Performance Report (Part {i+1})",
                            description=chunk,
                            color=0x0099ff
                        )
                    
                    if i == len(chunks) - 1:
                        embed.set_footer(text="Run !perf-reset to clear metrics and start fresh")
                    
                    await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error in optimization command: {e}")
                await ctx.send("❌ Error generating optimization report. Check logs for details.")
        
        @self.bot.command(name='perf-details', aliases=['perf-full'])
        async def performance_details(ctx, operation: str | None = None):
            """Show detailed performance metrics for specific operations"""
            try:
                all_stats = performance_monitor.get_all_stats()
                
                if operation:
                    # Show details for specific operation
                    if operation in all_stats:
                        stats = all_stats[operation]
                        embed = discord.Embed(
                            title=f"📈 Performance Details: {operation}",
                            color=0x0099ff,
                            timestamp=datetime.now()
                        )
                        
                        embed.add_field(
                            name="📊 Response Times",
                            value=f"**Average**: {stats.avg_duration_ms:.0f}ms\n"
                                  f"**Median**: {stats.median_duration_ms:.0f}ms\n"
                                  f"**95th Percentile**: {stats.p95_duration_ms:.0f}ms\n"
                                  f"**Min/Max**: {stats.min_duration_ms:.0f}ms / {stats.max_duration_ms:.0f}ms",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="🎯 Reliability",
                            value=f"**Total Calls**: {stats.total_calls:,}\n"
                                  f"**Success Rate**: {stats.success_rate:.1%}\n"
                                  f"**Failed Calls**: {stats.total_calls - int(stats.total_calls * stats.success_rate):,}\n"
                                  f"**Last Updated**: {stats.last_updated.strftime('%H:%M:%S')}",
                            inline=True
                        )
                        
                        # Performance status
                        baseline = performance_monitor.baselines.get(operation, 1000)
                        is_degraded = stats.is_degraded(baseline)
                        status = "⚠️ Degraded" if is_degraded else "✅ Good"
                        
                        embed.add_field(
                            name="🏥 Health Status",
                            value=f"**Status**: {status}\n"
                                  f"**Baseline**: {baseline:.0f}ms\n"
                                  f"**Performance**: {stats.p95_duration_ms/baseline:.1f}x baseline\n"
                                  f"**Trend**: {'↗️ Slower' if is_degraded else '✅ Normal'}",
                            inline=False
                        )
                        
                        await ctx.send(embed=embed)
                    else:
                        available_ops = ", ".join(list(all_stats.keys())[:10])
                        await ctx.send(f"❌ Operation '{operation}' not found.\n"
                                     f"Available operations: {available_ops}")
                else:
                    # Show list of all operations
                    if all_stats:
                        operations_list = []
                        for op, stats in sorted(all_stats.items(), key=lambda x: x[1].avg_duration_ms, reverse=True):
                            status = "⚠️" if stats.is_degraded() else "✅"
                            operations_list.append(f"{status} **{op}**: {stats.avg_duration_ms:.0f}ms ({stats.total_calls} calls)")
                        
                        embed = discord.Embed(
                            title="📊 All Performance Operations",
                            description="\n".join(operations_list[:15]),
                            color=0x0099ff,
                            timestamp=datetime.now()
                        )
                        
                        if len(operations_list) > 15:
                            embed.set_footer(text=f"Showing 15 of {len(operations_list)} operations. Use !perf-details <operation> for details.")
                        else:
                            embed.set_footer(text="Use !perf-details <operation> for detailed metrics.")
                        
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("📊 No performance data available yet. Start using the bot to generate metrics!")
                
            except Exception as e:
                logger.error(f"Error in performance details command: {e}")
                await ctx.send("❌ Error retrieving performance details. Check logs for details.")
        
        @self.bot.command(name='perf-reset', aliases=['clear-metrics'])
        async def reset_performance_metrics(ctx):
            """Reset all performance metrics (admin only)"""
            if not is_admin(ctx.author.id):
                await ctx.send("❌ This command is admin-only.")
                return
                
            try:
                # Clear all metrics
                performance_monitor.metrics.clear()
                performance_monitor.stats_cache.clear()
                performance_monitor.cache_expiry.clear()
                
                embed = discord.Embed(
                    title="🔄 Performance Metrics Reset",
                    description="All performance metrics have been cleared.\n"
                               "New metrics will be collected as the bot operates.",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                await ctx.send(embed=embed)
                logger.info(f"Performance metrics reset by admin user {ctx.author.id}")
                
            except Exception as e:
                logger.error(f"Error resetting performance metrics: {e}")
                await ctx.send("❌ Error resetting performance metrics. Check logs for details.")
        
        @self.bot.command(name='perf-test', aliases=['benchmark'])
        async def performance_test(ctx):
            """Run a quick performance test"""
            try:
                embed = discord.Embed(
                    title="🔍 Running Performance Test...",
                    description="Testing system components, please wait...",
                    color=0xffaa00,
                    timestamp=datetime.now()
                )
                
                message = await ctx.send(embed=embed)
                
                # Test LLM performance
                if self.llm_client:
                    test_messages = [{"role": "user", "content": "Hello, this is a performance test."}]
                    try:
                        response = self.llm_client.generate_chat_completion(
                            messages=test_messages,
                            max_tokens=50
                        )
                        llm_status = "✅ Working"
                    except Exception as e:
                        llm_status = f"❌ Error: {str(e)[:50]}"
                else:
                    llm_status = "⚪ Not configured"
                
                # Test memory performance
                if self.memory_manager:
                    try:
                        memories = await self.memory_manager.retrieve_contextual_memories(
                            str(ctx.author.id), 
                            "test query", 
                            limit=3
                        )
                        memory_status = f"✅ Working ({len(memories)} memories)"
                    except Exception as e:
                        memory_status = f"❌ Error: {str(e)[:50]}"
                else:
                    memory_status = "⚪ Not configured"
                
                # Update embed with results
                embed = discord.Embed(
                    title="🔍 Performance Test Results",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🤖 LLM Client",
                    value=llm_status,
                    inline=True
                )
                
                embed.add_field(
                    name="🧠 Memory System",
                    value=memory_status,
                    inline=True
                )
                
                # Get current performance stats
                health = performance_monitor.get_system_health()
                embed.add_field(
                    name="📊 Current Health",
                    value=f"**Status**: {health['overall_health'].title()}\n"
                          f"**Memory**: {health['memory_usage_mb']:.0f}MB\n"
                          f"**CPU**: {health['cpu_percent']:.1f}%",
                    inline=True
                )
                
                embed.set_footer(text="Use !perf for detailed metrics")
                await message.edit(embed=embed)
                
            except Exception as e:
                logger.error(f"Error in performance test command: {e}")
                await ctx.send("❌ Error running performance test. Check logs for details.")
    
    def _split_message(self, text: str, max_length: int = 2000) -> list[str]:
        """Split a long message into Discord-compatible chunks"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        for line in text.split('\n'):
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.rstrip())
        
        return chunks


def create_performance_commands(bot, **dependencies):
    """Factory function to create performance commands"""
    return PerformanceCommands(bot, **dependencies)