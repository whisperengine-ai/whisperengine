"""
LLM Tool Calling Command Handlers

Provides Discord commands to test and demonstrate Phase 1 & 2 LLM tool calling capabilities.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class LLMToolCommandHandlers:
    """Handler for LLM tool calling commands"""
    
    def __init__(self, bot, memory_manager, llm_tool_manager=None):
        self.bot = bot
        self.memory_manager = memory_manager
        self.llm_tool_manager = llm_tool_manager
        
    async def register_commands(self):
        """Register LLM tool calling commands"""
        
        @self.bot.command(name='test_llm_tools')
        async def test_llm_tools(ctx):
            """Test LLM tool calling system with sample scenarios"""
            await self._test_llm_tools_command(ctx)
            
        @self.bot.command(name='llm_tool_status')
        async def llm_tool_status(ctx):
            """Check LLM tool calling system status and available tools"""
            await self._llm_tool_status_command(ctx)
            
        @self.bot.command(name='character_evolve')
        async def character_evolve(ctx, trait: str = "empathy", direction: str = "increase"):
            """Test character evolution tools - adapt personality trait"""
            await self._character_evolve_command(ctx, trait, direction)
            
        @self.bot.command(name='emotional_support')
        async def emotional_support(ctx, *, message: str = "I'm feeling sad"):
            """Test emotional intelligence tools - simulate emotional support scenario"""
            await self._emotional_support_command(ctx, message)
            
        @self.bot.command(name='llm_analytics')
        async def llm_analytics(ctx):
            """Show LLM tool usage analytics and performance metrics"""
            await self._llm_analytics_command(ctx)
    
    async def _test_llm_tools_command(self, ctx):
        """Test LLM tool calling system"""
        if not self.llm_tool_manager:
            await ctx.send("❌ LLM Tool Calling system is not available. Check feature flags: `ENABLE_LLM_TOOL_CALLING=true`")
            return
            
        try:
            user_id = str(ctx.author.id)
            
            # Create test scenarios
            test_scenarios = [
                {
                    "name": "Memory Management Test",
                    "message": "Let me store this important conversation and retrieve some context about our relationship.",
                    "expected_tools": ["memory management"]
                },
                {
                    "name": "Character Evolution Test", 
                    "message": "I'd like you to be more empathetic and adapt your personality to be warmer.",
                    "expected_tools": ["character evolution"]
                },
                {
                    "name": "Emotional Intelligence Test",
                    "message": "I'm feeling really overwhelmed and sad lately. Everything seems hopeless.",
                    "expected_tools": ["emotional intelligence"]
                }
            ]
            
            embed = discord.Embed(
                title="🤖 LLM Tool Calling System Test",
                description="Testing Phase 1 & 2 LLM tool calling capabilities...",
                color=0x00ff00
            )
            
            for scenario in test_scenarios:
                try:
                    result = await self.llm_tool_manager.execute_llm_with_tools(
                        user_message=scenario["message"],
                        user_id=user_id,
                        character_context="Test character for LLM tool demonstration",
                        emotional_context={"mood": "testing", "engagement": "high"}
                    )
                    
                    if result.get("success"):
                        tools_used = result.get("tool_calls_made", 0)
                        execution_time = result.get("execution_time", 0)
                        
                        embed.add_field(
                            name=f"✅ {scenario['name']}",
                            value=f"Tools called: {tools_used}\nExecution: {execution_time:.3f}s",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name=f"❌ {scenario['name']}",
                            value=f"Error: {result.get('error', 'Unknown error')}",
                            inline=True
                        )
                        
                except Exception as e:
                    embed.add_field(
                        name=f"❌ {scenario['name']}",
                        value=f"Exception: {str(e)[:100]}...",
                        inline=True
                    )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Test failed: {str(e)}")
    
    async def _llm_tool_status_command(self, ctx):
        """Show LLM tool system status"""
        embed = discord.Embed(
            title="🔍 LLM Tool Calling System Status",
            color=0x0099ff
        )
        
        # Check if system is available
        if not self.llm_tool_manager:
            embed.add_field(
                name="❌ System Status",
                value="LLM Tool Calling system is not initialized",
                inline=False
            )
            
            # Show feature status - all enabled by default in development!
            flags = {
                "LLM_TOOL_CALLING": "enabled (always on in dev)",
                "PHASE1_MEMORY_TOOLS": "enabled (always on in dev)",
                "PHASE2_CHARACTER_TOOLS": "enabled (always on in dev)",
                "PHASE2_EMOTIONAL_TOOLS": "enabled (always on in dev)"
            }
            
            flag_status = "\n".join([f"`{k}`: {v}" for k, v in flags.items()])
            embed.add_field(
                name="Feature Flags",
                value=flag_status,
                inline=False
            )
            
        else:
            embed.add_field(
                name="✅ System Status",
                value="LLM Tool Calling system is active and operational",
                inline=False
            )
            
            try:
                # Get tools summary
                tools_summary = self.llm_tool_manager.get_available_tools_summary()
                
                embed.add_field(
                    name="📊 Tools Available",
                    value=f"Total: {tools_summary.get('total_tools_available', 0)}",
                    inline=True
                )
                
                embed.add_field(
                    name="🔧 Integration Status",
                    value=tools_summary.get('integration_status', 'unknown').title(),
                    inline=True
                )
                
                # Tool categories
                categories = tools_summary.get('tool_categories', {})
                for category, tools in categories.items():
                    embed.add_field(
                        name=f"🛠️ {category}",
                        value=f"{len(tools)} tools",
                        inline=True
                    )
                    
            except Exception as e:
                embed.add_field(
                    name="⚠️ Error",
                    value=f"Could not retrieve tools summary: {str(e)}",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    async def _character_evolve_command(self, ctx, trait: str, direction: str):
        """Test character evolution functionality"""
        if not self.llm_tool_manager:
            await ctx.send("❌ LLM Tool Calling system not available")
            return
            
        try:
            user_id = str(ctx.author.id)
            
            # Simulate LLM tool calling for character evolution
            message = f"Please adapt your {trait} trait in the {direction} direction based on my preference for that quality."
            
            result = await self.llm_tool_manager.execute_llm_with_tools(
                user_message=message,
                user_id=user_id,
                character_context=f"Character evolution test: adjusting {trait}",
                emotional_context={"mood": "collaborative", "engagement": "high"}
            )
            
            embed = discord.Embed(
                title="🧬 Character Evolution Test",
                description=f"Testing adaptation of `{trait}` trait ({direction})",
                color=0x9932cc
            )
            
            if result.get("success"):
                embed.add_field(
                    name="✅ Evolution Successful",
                    value=f"Tools called: {result.get('tool_calls_made', 0)}",
                    inline=True
                )
                
                embed.add_field(
                    name="⏱️ Execution Time",
                    value=f"{result.get('execution_time', 0):.3f}s",
                    inline=True
                )
                
                if result.get("tool_results"):
                    for i, tool_result in enumerate(result["tool_results"][:2]):  # Show first 2 results
                        if tool_result.get("success"):
                            embed.add_field(
                                name=f"🔧 Tool Result {i+1}",
                                value=f"Success: {tool_result.get('message', 'Tool executed successfully')[:100]}",
                                inline=False
                            )
            else:
                embed.add_field(
                    name="❌ Evolution Failed",
                    value=result.get("error", "Unknown error"),
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Character evolution test failed: {str(e)}")
    
    async def _emotional_support_command(self, ctx, message: str):
        """Test emotional intelligence functionality"""
        if not self.llm_tool_manager:
            await ctx.send("❌ LLM Tool Calling system not available")
            return
            
        try:
            user_id = str(ctx.author.id)
            
            result = await self.llm_tool_manager.execute_llm_with_tools(
                user_message=message,
                user_id=user_id,
                character_context="Empathetic AI companion focused on emotional support",
                emotional_context={"mood": "distressed", "support_needed": True}
            )
            
            embed = discord.Embed(
                title="💙 Emotional Intelligence Test",
                description="Testing crisis detection and empathy calibration",
                color=0x4169e1
            )
            
            if result.get("success"):
                embed.add_field(
                    name="🤖 AI Response",
                    value=result.get("llm_response", "No response generated")[:500],
                    inline=False
                )
                
                embed.add_field(
                    name="🛠️ Tools Activated",
                    value=f"{result.get('tool_calls_made', 0)} tools",
                    inline=True
                )
                
                embed.add_field(
                    name="⏱️ Response Time",
                    value=f"{result.get('execution_time', 0):.3f}s",
                    inline=True
                )
                
                # Check for crisis detection
                tool_results = result.get("tool_results", [])
                for tool_result in tool_results:
                    if tool_result.get("crisis_detected"):
                        severity = tool_result.get("severity", "unknown")
                        embed.add_field(
                            name="🚨 Crisis Detection",
                            value=f"Severity: {severity.title()}\nConfidence: {tool_result.get('confidence', 0):.2f}",
                            inline=True
                        )
                        break
            else:
                embed.add_field(
                    name="❌ Support Failed",
                    value=result.get("error", "Unknown error"),
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Emotional support test failed: {str(e)}")
    
    async def _llm_analytics_command(self, ctx):
        """Show LLM tool usage analytics"""
        if not self.llm_tool_manager:
            await ctx.send("❌ LLM Tool Calling system not available")
            return
            
        try:
            user_id = str(ctx.author.id)
            
            # Get analytics for this user
            user_analytics = await self.llm_tool_manager.get_tool_analytics(user_id)
            global_analytics = await self.llm_tool_manager.get_tool_analytics()
            
            embed = discord.Embed(
                title="📊 LLM Tool Usage Analytics",
                color=0xff6b35
            )
            
            # User-specific stats
            if user_analytics.get("total_executions", 0) > 0:
                embed.add_field(
                    name="👤 Your Usage",
                    value=f"Total: {user_analytics.get('total_executions', 0)}\n"
                          f"Success Rate: {user_analytics.get('success_rate', 0):.1%}\n"
                          f"Avg Time: {user_analytics.get('average_execution_time', 0):.3f}s",
                    inline=True
                )
                
                most_used = user_analytics.get('most_used_tool')
                if most_used:
                    embed.add_field(
                        name="🎯 Your Most Used Tool",
                        value=most_used.replace('_', ' ').title(),
                        inline=True
                    )
            else:
                embed.add_field(
                    name="👤 Your Usage",
                    value="No tool usage recorded yet",
                    inline=True
                )
            
            # Global stats
            if global_analytics.get("total_executions", 0) > 0:
                embed.add_field(
                    name="🌐 Global Usage",
                    value=f"Total: {global_analytics.get('total_executions', 0)}\n"
                          f"Success Rate: {global_analytics.get('success_rate', 0):.1%}\n"
                          f"24h Activity: {global_analytics.get('recent_activity_24h', 0)}",
                    inline=True
                )
                
                # Tool usage breakdown
                usage_breakdown = global_analytics.get('tool_usage_breakdown', {})
                if usage_breakdown:
                    top_tools = sorted(usage_breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
                    breakdown_text = "\n".join([f"{tool.replace('_', ' ').title()}: {count}" for tool, count in top_tools])
                    
                    embed.add_field(
                        name="🏆 Most Used Tools",
                        value=breakdown_text,
                        inline=False
                    )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Analytics retrieval failed: {str(e)}")
    
    async def test_integration_with_user_message(self, user_message: str, user_id: str, 
                                                character_context: str = "", 
                                                emotional_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Test LLM tool integration with actual user message (for use by other handlers)
        
        Returns:
            Dict with LLM response and tool results, or None if not available
        """
        if not self.llm_tool_manager:
            return None
            
        try:
            result = await self.llm_tool_manager.execute_llm_with_tools(
                user_message=user_message,
                user_id=user_id,
                character_context=character_context,
                emotional_context=emotional_context or {}
            )
            return result
        except Exception as e:
            logger.error("LLM tool integration test failed: %s", e)
            return None