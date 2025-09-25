"""
Web Search Commands for Discord Bot

Provides Discord commands to test and use the new web search capabilities.
"""

import logging
from typing import Optional
import discord
from discord.ext import commands

from src.security.command_security import secure_command

logger = logging.getLogger(__name__)


class WebSearchCommands:
    """Discord commands for web search functionality"""
    
    def __init__(self, bot, llm_tool_integration_manager):
        self.bot = bot
        self.tool_integration_manager = llm_tool_integration_manager
    
    async def register_commands(self):
        """Register web search commands with the bot"""
        
        @self.bot.command(name="search_news")
        @secure_command("web_search", max_length=200)
        async def search_news_command(ctx, *, query: str):
            """Search for current news and events
            
            Usage: !search_news AI developments
            """
            # Additional web search validation
            query_lower = query.lower()
            blocked_terms = ['localhost', '127.0.0.1', '192.168.', '10.0.0.', 'internal', 'admin', 'config']
            
            if any(term in query_lower for term in blocked_terms):
                await ctx.send("⚠️ Search query contains restricted terms")
                return
                
            await self._handle_search_news(ctx, query)
        
        @self.bot.command(name="verify_info")
        @secure_command("web_search", max_length=300)
        async def verify_info_command(ctx, *, claim: str):
            """Verify information against current sources
            
            Usage: !verify_info Python is the most popular language in 2025
            """
            # Additional validation for information verification
            claim_lower = claim.lower()
            blocked_terms = ['localhost', '127.0.0.1', '192.168.', 'internal', 'admin']
            
            if any(term in claim_lower for term in blocked_terms):
                await ctx.send("⚠️ Information claim contains restricted terms")
                return
                
            await self._handle_verify_info(ctx, claim)
        
        @self.bot.command(name="test_web_search")
        async def test_web_search_command(ctx):
            """Test web search integration status"""
            await self._handle_test_web_search(ctx)
    
    async def _handle_search_news(self, ctx, query: str):
        """Handle news search command"""
        try:
            user_id = str(ctx.author.id)
            
            await ctx.send(f"🔍 Searching for current news about: **{query}**")
            
            # Execute web search via LLM tool integration
            result = await self.tool_integration_manager.execute_llm_with_tools(
                user_message=f"Search for current news about {query}",
                user_id=user_id,
                character_context="You are helping search for current events and news."
            )
            
            if result.get("success"):
                response = result.get("final_response", "Search completed")
                tool_results = result.get("tool_results", [])
                
                # Send main response
                await ctx.send(f"📰 **News Search Results:**\n{response}")
                
                # Send detailed results if available
                for tool_result in tool_results:
                    if tool_result.get("function_name") == "search_current_events":
                        search_data = tool_result.get("result", {})
                        if search_data.get("success") and search_data.get("results"):
                            embed = discord.Embed(
                                title="🔍 Current Events Search",
                                description=f"Query: {query}",
                                color=0x00ff00
                            )
                            
                            for i, item in enumerate(search_data["results"][:3], 1):
                                title = item.get("title", "No title")[:100]
                                snippet = item.get("snippet", "No snippet")[:200]
                                source = item.get("source", "Unknown")
                                
                                embed.add_field(
                                    name=f"{i}. {title}",
                                    value=f"**Source:** {source}\n{snippet}...",
                                    inline=False
                                )
                            
                            await ctx.send(embed=embed)
            else:
                error_msg = result.get("error", "Unknown error")
                await ctx.send(f"❌ Search failed: {error_msg}")
                
        except Exception as e:
            logger.error("Error in search_news command: %s", e)
            await ctx.send(f"❌ An error occurred while searching: {str(e)}")
    
    async def _handle_verify_info(self, ctx, claim: str):
        """Handle information verification command"""
        try:
            user_id = str(ctx.author.id)
            
            await ctx.send(f"🔍 Verifying claim: **{claim}**")
            
            # Execute verification via LLM tool integration
            result = await self.tool_integration_manager.execute_llm_with_tools(
                user_message=f"Please verify this claim: {claim}",
                user_id=user_id,
                character_context="You are helping verify information against current sources."
            )
            
            if result.get("success"):
                response = result.get("final_response", "Verification completed")
                tool_results = result.get("tool_results", [])
                
                # Send main response
                await ctx.send(f"✅ **Verification Results:**\n{response}")
                
                # Send detailed results if available
                for tool_result in tool_results:
                    if tool_result.get("function_name") == "verify_current_information":
                        verify_data = tool_result.get("result", {})
                        if verify_data.get("success") and verify_data.get("verification_sources"):
                            embed = discord.Embed(
                                title="🔍 Information Verification",
                                description=f"Claim: {claim}",
                                color=0x0099ff
                            )
                            
                            for i, source in enumerate(verify_data["verification_sources"][:2], 1):
                                title = source.get("title", "No title")[:100]
                                snippet = source.get("snippet", "No snippet")[:200]
                                source_name = source.get("source", "Unknown")
                                
                                embed.add_field(
                                    name=f"Source {i}: {title}",
                                    value=f"**From:** {source_name}\n{snippet}...",
                                    inline=False
                                )
                            
                            await ctx.send(embed=embed)
            else:
                error_msg = result.get("error", "Unknown error")
                await ctx.send(f"❌ Verification failed: {error_msg}")
                
        except Exception as e:
            logger.error("Error in verify_info command: %s", e)
            await ctx.send(f"❌ An error occurred while verifying: {str(e)}")
    
    async def _handle_test_web_search(self, ctx):
        """Handle web search test command"""
        try:
            # Get tool summary
            if hasattr(self.tool_integration_manager, 'get_available_tools_summary'):
                summary = self.tool_integration_manager.get_available_tools_summary()
                web_search_available = summary.get("web_search_available", False)
                
                embed = discord.Embed(
                    title="🔍 Web Search Integration Status",
                    color=0x00ff00 if web_search_available else 0xff0000
                )
                
                embed.add_field(
                    name="Status",
                    value="✅ Available" if web_search_available else "❌ Not Available",
                    inline=True
                )
                
                embed.add_field(
                    name="Total Tools",
                    value=summary.get("total_tools_available", "Unknown"),
                    inline=True
                )
                
                if web_search_available:
                    web_tools = summary.get("tool_categories", {}).get("Web Search & Current Events", [])
                    embed.add_field(
                        name="Web Search Tools",
                        value="\n".join([f"• {tool}" for tool in web_tools]) or "None",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
                # Test basic search functionality
                if web_search_available:
                    await ctx.send("🧪 Testing basic search functionality...")
                    
                    # Test with a simple query
                    test_result = await self.tool_integration_manager.execute_llm_with_tools(
                        user_message="What's the latest news about artificial intelligence?",
                        user_id=str(ctx.author.id),
                        character_context="You are testing web search capabilities."
                    )
                    
                    if test_result.get("success"):
                        await ctx.send("✅ Web search test passed!")
                    else:
                        await ctx.send("⚠️ Web search test had issues, but integration is installed.")
            else:
                await ctx.send("❌ Tool integration manager not available")
                
        except Exception as e:
            logger.error("Error in test_web_search command: %s", e)
            await ctx.send(f"❌ Test failed: {str(e)}")