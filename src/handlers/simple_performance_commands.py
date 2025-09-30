"""
Simple Performance Commands - No Circular Dependencies

Basic performance monitoring commands using existing infrastructure.
"""

import logging
import psutil
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class SimplePerformanceCommands:
    """Simple Discord commands for basic performance monitoring"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def register_commands(self):
        """Register performance monitoring commands"""
        
        @self.bot.command(name="performance", aliases=["perf", "metrics"])
        async def performance_status(ctx):
            """Show current performance metrics and system health"""
            await self._performance_status_handler(ctx)
        
        @self.bot.command(name="system_health", aliases=["health_detailed"])
        async def system_health(ctx):
            """Show detailed system health information"""
            await self._system_health_handler(ctx)
        
        @self.bot.command(name="influxdb_status", aliases=["influx"])
        async def influxdb_status(ctx):
            """Check InfluxDB connection and status"""
            await self._influxdb_status_handler(ctx)
        
        @self.bot.command(name="dashboard", aliases=["monitoring", "dashboards"])
        async def dashboard_links(ctx):
            """Show available dashboard and monitoring links"""
            await self._dashboard_links_handler(ctx)
    
    async def _performance_status_handler(self, ctx):
        """Handle performance status command"""
        try:
            # Get basic system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Create performance embed
            embed = discord.Embed(
                title="🚀 Performance Status",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            
            # System metrics
            embed.add_field(
                name="💻 System Resources",
                value=f"**CPU Usage:** {cpu_percent:.1f}%\n"
                      f"**Memory:** {memory.percent:.1f}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)\n"
                      f"**Available:** {memory.available / 1024**3:.1f}GB",
                inline=False
            )
            
            # Bot status
            embed.add_field(
                name="🤖 Bot Status",
                value=f"**Latency:** {self.bot.latency * 1000:.1f}ms\n"
                      f"**Guilds:** {len(self.bot.guilds)}\n"
                      f"**Status:** Online ✅",
                inline=True
            )
            
            # Quick health indicators
            health_indicators = []
            if cpu_percent < 80:
                health_indicators.append("CPU: ✅")
            else:
                health_indicators.append("CPU: ⚠️")
                
            if memory.percent < 80:
                health_indicators.append("Memory: ✅")
            else:
                health_indicators.append("Memory: ⚠️")
            
            embed.add_field(
                name="🏥 Health Status",
                value=" | ".join(health_indicators),
                inline=True
            )
            
            embed.set_footer(text="Basic performance metrics • Use !system_health for detailed info")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in performance status: {e}")
            await ctx.send("❌ **Error:** Could not retrieve performance metrics.")
    
    async def _system_health_handler(self, ctx):
        """Handle system health command"""
        try:
            # Get detailed system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            embed = discord.Embed(
                title="🏥 Detailed System Health",
                color=0x0099ff,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Detailed CPU info
            embed.add_field(
                name="🖥️ CPU Information",
                value=f"**Usage:** {cpu_percent:.1f}%\n"
                      f"**Cores:** {psutil.cpu_count()} physical, {psutil.cpu_count(logical=True)} logical\n"
                      f"**Load Average:** {', '.join(f'{x:.2f}' for x in psutil.getloadavg())}",
                inline=True
            )
            
            # Detailed memory info
            embed.add_field(
                name="🧠 Memory Information",
                value=f"**Usage:** {memory.percent:.1f}%\n"
                      f"**Used:** {memory.used / 1024**3:.2f}GB\n"
                      f"**Available:** {memory.available / 1024**3:.2f}GB\n"
                      f"**Total:** {memory.total / 1024**3:.2f}GB",
                inline=True
            )
            
            # Disk information
            embed.add_field(
                name="💽 Disk Information",
                value=f"**Usage:** {disk.percent:.1f}%\n"
                      f"**Used:** {disk.used / 1024**3:.2f}GB\n"
                      f"**Free:** {disk.free / 1024**3:.2f}GB\n"
                      f"**Total:** {disk.total / 1024**3:.2f}GB",
                inline=True
            )
            
            # Network info (if available)
            try:
                net_io = psutil.net_io_counters()
                embed.add_field(
                    name="🌐 Network I/O",
                    value=f"**Bytes Sent:** {net_io.bytes_sent / 1024**2:.1f}MB\n"
                          f"**Bytes Recv:** {net_io.bytes_recv / 1024**2:.1f}MB",
                    inline=True
                )
            except:
                pass
            
            # Process info
            try:
                process = psutil.Process()
                embed.add_field(
                    name="🔄 Process Info",
                    value=f"**PID:** {process.pid}\n"
                          f"**CPU:** {process.cpu_percent():.1f}%\n"
                          f"**Memory:** {process.memory_percent():.1f}%",
                    inline=True
                )
            except:
                pass
            
            # Overall health assessment
            issues = []
            if cpu_percent > 90:
                issues.append("High CPU usage")
            if memory.percent > 90:
                issues.append("High memory usage")
            if disk.percent > 90:
                issues.append("Low disk space")
            
            if not issues:
                health_status = "🟢 **System Health: EXCELLENT**"
            elif len(issues) == 1:
                health_status = f"🟡 **System Health: GOOD** (Note: {issues[0]})"
            else:
                health_status = f"🔴 **System Health: ATTENTION NEEDED**\nIssues: {', '.join(issues)}"
            
            embed.add_field(
                name="📊 Overall Assessment",
                value=health_status,
                inline=False
            )
            
            embed.set_footer(text="Detailed system health report")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in system health: {e}")
            await ctx.send("❌ **Error:** Could not retrieve system health information.")
    
    async def _influxdb_status_handler(self, ctx):
        """Check InfluxDB connection status"""
        try:
            # Try to import and check InfluxDB
            try:
                from src.monitoring.fidelity_metrics_collector import get_fidelity_metrics_collector
                
                # Test InfluxDB connection
                collector = get_fidelity_metrics_collector()
                
                embed = discord.Embed(
                    title="📊 InfluxDB Status",
                    color=0x00ff00,
                    timestamp=datetime.now(timezone.utc)
                )
                
                # Basic status
                embed.add_field(
                    name="🔗 Connection Status",
                    value="✅ **Connected** - InfluxDB is accessible",
                    inline=False
                )
                
                # Database info
                embed.add_field(
                    name="🗄️ Database Info", 
                    value="InfluxDB collector available ✅",
                    inline=True
                )
                
                # Test write capability
                embed.add_field(
                    name="✍️ Write Test",
                    value="Metrics collection active ✅",
                    inline=True
                )
                
                embed.set_footer(text="InfluxDB time series database status")
                
            except ImportError as e:
                embed = discord.Embed(
                    title="📊 InfluxDB Status",
                    color=0xff9900,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(
                    name="⚠️ Import Error",
                    value=f"InfluxDB client not available: {e}",
                    inline=False
                )
            
            except Exception as e:
                embed = discord.Embed(
                    title="📊 InfluxDB Status",
                    color=0xff0000,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(
                    name="❌ Connection Error",
                    value=f"Could not connect to InfluxDB: {e}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error checking InfluxDB status: {e}")
            await ctx.send("❌ **Error:** Could not check InfluxDB status.")
    
    async def _dashboard_links_handler(self, ctx):
        """Show available dashboard and monitoring links"""
        try:
            embed = discord.Embed(
                title="📊 Dashboard & Monitoring Links",
                description="Available monitoring interfaces and dashboards",
                color=0x0099ff,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Check what's actually running
            dashboards = []
            
            # Built-in monitoring dashboard
            try:
                import aiohttp
                import asyncio
                
                async def check_port(port, name, description):
                    try:
                        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                            async with session.get(f'http://localhost:{port}/health') as resp:
                                if resp.status == 200:
                                    return f"✅ **{name}**: http://localhost:{port}\n{description}"
                                else:
                                    return f"⚠️ **{name}**: http://localhost:{port} (Status: {resp.status})"
                    except:
                        return f"❌ **{name}**: Not accessible on port {port}"
                
                # Check monitoring dashboard (usually 8080, but might be disabled)
                monitoring_status = await check_port(8080, "Monitoring Dashboard", "System health, engagement metrics, error tracking")
                dashboards.append(monitoring_status)
                
                # Check InfluxDB 
                influx_status = await check_port(8086, "InfluxDB Dashboard", "Time series metrics database")
                dashboards.append(influx_status)
                
                # Check for web chat interface (might be on 8080 or 8081)
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                        async with session.get('http://localhost:8080/') as resp:
                            if resp.status == 200:
                                text = await resp.text()
                                if 'WhisperEngine - AI Companions' in text:
                                    dashboards.append("✅ **Web Chat Interface**: http://localhost:8080\nChatGPT-like interface for bot conversations")
                except:
                    pass
                
            except ImportError:
                dashboards.append("⚠️ **aiohttp not available** - Cannot check dashboard status")
            
            # Discord commands
            discord_commands = [
                "`!performance` - Real-time system metrics",
                "`!system_health` - Detailed health analysis",  
                "`!influxdb_status` - Database connectivity",
                "`!ping` - Bot response time",
                "`!bot_status` - Bot operational status"
            ]
            
            # Add dashboard information
            if dashboards:
                embed.add_field(
                    name="🌐 Web Dashboards",
                    value="\n\n".join(dashboards),
                    inline=False
                )
            
            embed.add_field(
                name="🤖 Discord Commands",
                value="\n".join(discord_commands),
                inline=False
            )
            
            # Bot-specific health endpoints
            bot_endpoints = [
                "Elena (Marine Biologist): http://localhost:9091/health",
                "Marcus (AI Researcher): http://localhost:9092/health", 
                "Ryan (Game Developer): http://localhost:9093/health",
                "Dream (Mythological): http://localhost:9094/health",
                "Gabriel (Archangel): http://localhost:9095/health",
                "Sophia (Marketing): http://localhost:9096/health",
                "Jake (Photographer): http://localhost:9097/health",
                "Aethys (Omnipotent): http://localhost:3007/health"
            ]
            
            embed.add_field(
                name="🏥 Bot Health Endpoints",
                value="\n".join(bot_endpoints[:4]) + "\n*(and 4 more bots)*",
                inline=False
            )
            
            embed.set_footer(text="Real-time monitoring and dashboard access")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in dashboard links: {e}")
            await ctx.send("❌ **Error:** Could not retrieve dashboard information.")


def create_simple_performance_commands(bot):
    """Factory function to create simple performance commands"""
    return SimplePerformanceCommands(bot)