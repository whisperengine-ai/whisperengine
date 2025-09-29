"""
LLM-Powered Self-Memory Discord Command Handlers

Integrates the revolutionary LLM-powered CDL self-memory system with Discord,
allowing users to interact with bot self-knowledge and see self-reflection in action.
"""

import logging
from typing import Optional
import discord
from discord.ext import commands

from src.memory.llm_powered_bot_memory import create_llm_powered_bot_memory
from src.llm.llm_protocol import create_llm_client
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class LLMSelfMemoryCommandHandlers:
    """Handles LLM-powered self-memory Discord commands"""

    def __init__(self, bot, memory_manager, bot_name: str):
        self.bot = bot
        self.memory_manager = memory_manager
        self.bot_name = bot_name
        self._llm_bot_memory = None
        
        logger.info(f"🧠 Initialized LLM Self-Memory Commands for {bot_name}")

    async def _get_llm_bot_memory(self):
        """Lazy initialization of LLM-powered bot memory"""
        if self._llm_bot_memory is None:
            try:
                llm_client = create_llm_client()
                self._llm_bot_memory = create_llm_powered_bot_memory(
                    self.bot_name, llm_client, self.memory_manager
                )
                logger.info(f"✅ Initialized LLM bot memory for {self.bot_name}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize LLM bot memory: {e}")
                raise
        return self._llm_bot_memory

    @handle_errors(category=ErrorCategory.MEMORY_SYSTEM, severity=ErrorSeverity.MEDIUM)
    async def register_commands(self, bot_name_filter=None):
        """Register LLM self-memory commands"""
        
        # Import bot_name_filter if not provided
        if bot_name_filter is None:
            from src.core.bot_launcher import bot_name_filter
        
        @self.bot.command(name="ask_me", aliases=["personal", "about_me"])
        @bot_name_filter()
        async def ask_personal_question(ctx, *, question: str):
            """Ask me a personal question and I'll answer from my own knowledge!
            
            Examples:
            !ask_me Do you have a boyfriend?
            !ask_me Tell me about your research
            !ask_me What's your daily routine?
            !ask_me What are you passionate about?
            """
            try:
                # Get LLM-powered bot memory
                llm_bot_memory = await self._get_llm_bot_memory()
                
                # Create thinking message
                thinking_msg = await ctx.send(f"🤔 Let me think about that... *{question}*")
                
                # Query personal knowledge using LLM
                knowledge_result = await llm_bot_memory.query_personal_knowledge_with_llm(
                    question, limit=3
                )
                
                if knowledge_result.get("found_relevant_info"):
                    # Found relevant personal knowledge!
                    relevant_items = knowledge_result.get("relevant_items", [])
                    response_guidance = knowledge_result.get("response_guidance", "")
                    authenticity_tips = knowledge_result.get("authenticity_tips", "")
                    
                    # Create embed with personal knowledge
                    embed = discord.Embed(
                        title="💭 Personal Knowledge Response",
                        description=f"**Your question:** {question}",
                        color=0x00ff7f
                    )
                    
                    # Add relevant knowledge items
                    for i, item in enumerate(relevant_items[:2], 1):
                        category = item.get('category', 'personal').title()
                        content = item.get('formatted_content', '')
                        confidence = item.get('confidence', 0.0)
                        
                        confidence_emoji = "🎯" if confidence > 0.9 else "📍" if confidence > 0.8 else "🔍"
                        
                        embed.add_field(
                            name=f"{confidence_emoji} {category} Knowledge #{i}",
                            value=content[:300] + ("..." if len(content) > 300 else ""),
                            inline=False
                        )
                    
                    # Add response guidance if available
                    if response_guidance:
                        embed.add_field(
                            name="💡 How I'll approach this",
                            value=response_guidance[:200] + ("..." if len(response_guidance) > 200 else ""),
                            inline=False
                        )
                    
                    embed.set_footer(text=f"✨ AI-powered self-knowledge from {self.bot_name.title()}'s memory")
                    
                    await thinking_msg.edit(content="", embed=embed)
                    
                    # Generate self-reflection on this interaction
                    try:
                        interaction_data = {
                            "user_message": question,
                            "bot_response": f"Answered using {len(relevant_items)} personal knowledge items",
                            "character_context": f"{self.bot_name} answering personal question",
                            "interaction_outcome": "successful_personal_response"
                        }
                        
                        # Generate self-reflection (async, don't wait)
                        await llm_bot_memory.generate_self_reflection_with_llm(interaction_data)
                        
                    except Exception as e:
                        logger.warning(f"Self-reflection generation failed: {e}")
                    
                else:
                    # No relevant knowledge found
                    embed = discord.Embed(
                        title="🤷 No Personal Knowledge Found",
                        description=f"I don't have specific personal knowledge to answer: *{question}*",
                        color=0xffa500
                    )
                    
                    guidance = knowledge_result.get("response_guidance", "")
                    if guidance:
                        embed.add_field(
                            name="💭 My thoughts",
                            value=guidance[:300] + ("..." if len(guidance) > 300 else ""),
                            inline=False
                        )
                    
                    embed.add_field(
                        name="💡 Suggestion",
                        value="Try asking about my background, research, daily routine, or relationships!",
                        inline=False
                    )
                    
                    embed.set_footer(text=f"🧠 {self.bot_name.title()}'s self-knowledge system")
                    
                    await thinking_msg.edit(content="", embed=embed)
                
            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Self-Memory Error",
                    description=f"Sorry, I had trouble accessing my personal knowledge: {str(e)}",
                    color=0xff0000
                )
                await ctx.send(embed=error_embed)
                logger.error(f"Personal question command failed: {e}")

        @self.bot.command(name="extract_knowledge", aliases=["learn_about_myself"])
        @commands.has_permissions(administrator=True)
        async def extract_personal_knowledge(ctx):
            """Extract personal knowledge from my character file (Admin only)"""
            try:
                # Get LLM-powered bot memory
                llm_bot_memory = await self._get_llm_bot_memory()
                
                # Create progress message
                progress_msg = await ctx.send("🧠 Extracting personal knowledge from my character file...")
                
                # Extract knowledge from character file - use environment variable
                import os
                character_file = os.getenv('CDL_DEFAULT_CHARACTER', f"characters/examples/{self.bot_name}.json")
                
                extraction_result = await llm_bot_memory.extract_cdl_knowledge_with_llm(character_file)
                
                # Create results embed
                embed = discord.Embed(
                    title="✅ Knowledge Extraction Complete!",
                    description=f"Successfully extracted personal knowledge from {character_file}",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="📊 Extraction Results",
                    value=f"**Items Extracted:** {extraction_result.total_items}\n"
                          f"**Confidence Score:** {extraction_result.confidence_score:.2f}\n"
                          f"**Categories:** {len(extraction_result.categories)}",
                    inline=False
                )
                
                # Show categories
                categories_text = ", ".join(extraction_result.categories.keys())
                embed.add_field(
                    name="📂 Knowledge Categories",
                    value=categories_text[:300] + ("..." if len(categories_text) > 300 else ""),
                    inline=False
                )
                
                # Show some examples
                example_count = 0
                for category, items in extraction_result.categories.items():
                    if items and example_count < 2:
                        item = items[0]
                        content = item.get('content', '')[:150]
                        confidence = item.get('confidence', 0.0)
                        
                        embed.add_field(
                            name=f"🔸 {category.title()} Example",
                            value=f"{content}... (confidence: {confidence:.2f})",
                            inline=False
                        )
                        example_count += 1
                
                embed.set_footer(text=f"🤖 {self.bot_name.title()}'s AI-powered knowledge extraction")
                
                await progress_msg.edit(content="", embed=embed)
                
            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Knowledge Extraction Failed",
                    description=f"Error extracting personal knowledge: {str(e)}",
                    color=0xff0000
                )
                await ctx.send(embed=error_embed)
                logger.error(f"Knowledge extraction command failed: {e}")

        @self.bot.command(name="self_reflection", aliases=["reflect", "self_eval"])
        @bot_name_filter()
        async def show_self_reflection(ctx):
            """Show my recent self-reflections and learning insights"""
            try:
                # Get LLM-powered bot memory
                llm_bot_memory = await self._get_llm_bot_memory()
                
                # Get recent insights
                recent_insights = await llm_bot_memory.get_recent_llm_insights(limit=3)
                
                if recent_insights:
                    embed = discord.Embed(
                        title="🤔 My Recent Self-Reflections",
                        description=f"Here are my latest thoughts about my conversations and performance:",
                        color=0x9370db
                    )
                    
                    for i, insight in enumerate(recent_insights, 1):
                        learning = insight.get('learning_insight', 'No insight available')
                        improvement = insight.get('improvement_suggestion', 'No suggestion available')
                        effectiveness = insight.get('effectiveness_score', 0.0)
                        trait = insight.get('dominant_personality_trait', 'unknown')
                        created = insight.get('created_at', '')
                        
                        # Create a nice reflection summary
                        reflection_text = f"**💡 Learning:** {learning[:150]}...\n"
                        reflection_text += f"**🔄 Improvement:** {improvement[:150]}...\n"
                        reflection_text += f"**📊 Effectiveness:** {effectiveness:.2f} | **🎭 Trait:** {trait}"
                        
                        embed.add_field(
                            name=f"🔸 Reflection #{i}",
                            value=reflection_text,
                            inline=False
                        )
                    
                    embed.set_footer(text=f"🧠 {self.bot_name.title()}'s AI-powered self-reflection system")
                    
                else:
                    embed = discord.Embed(
                        title="🤷 No Recent Reflections",
                        description="I haven't generated any self-reflections yet. Try asking me personal questions or having conversations!",
                        color=0xffa500
                    )
                    
                    embed.add_field(
                        name="💭 How Self-Reflection Works",
                        value="After our conversations, I analyze my responses and learn how to improve. "
                              "This helps me become more authentic and effective over time!",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Self-Reflection Error",
                    description=f"Error accessing self-reflections: {str(e)}",
                    color=0xff0000
                )
                await ctx.send(embed=error_embed)
                logger.error(f"Self-reflection command failed: {e}")
        
        @self.bot.command(name="demo_self_memory", aliases=["memory_demo"])
        @commands.has_permissions(administrator=True)
        async def demo_self_memory_system(ctx):
            """Run a live demo of the LLM-powered self-memory system (Admin only)"""
            try:
                embed = discord.Embed(
                    title="🎭 LLM-Powered Self-Memory Demo",
                    description=f"Watch {self.bot_name.title()}'s revolutionary self-awareness system in action!",
                    color=0x00ffff
                )
                
                embed.add_field(
                    name="🧠 What You Can Try",
                    value="• `!ask_me Do you have a boyfriend?`\n"
                          "• `!ask_me Tell me about your research`\n"
                          "• `!ask_me What's your daily routine?`\n"
                          "• `!ask_me What are you passionate about?`",
                    inline=False
                )
                
                embed.add_field(
                    name="🤔 Self-Reflection Commands",
                    value="• `!self_reflection` - See my recent self-evaluations\n"
                          "• `!extract_knowledge` - Extract knowledge from character file (Admin)\n"
                          "• `!demo_self_memory` - Show this demo info",
                    inline=False
                )
                
                embed.add_field(
                    name="✨ Revolutionary Features",
                    value="🎯 **AI-Powered Knowledge Extraction** - I learn about myself from my character file\n"
                          "🔍 **Intelligent Personal Responses** - I answer questions using my own knowledge\n"
                          "🤔 **Self-Reflection & Learning** - I analyze my responses and improve over time\n"
                          "📈 **Personality Evolution** - I track my growth and development",
                    inline=False
                )
                
                embed.set_footer(text=f"🚀 {self.bot_name.title()}'s LLM-Powered CDL Self-Memory System - First of its kind!")
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Demo command failed: {e}")
                await ctx.send(f"❌ Demo failed: {str(e)}")

        logger.info(f"✅ Registered LLM self-memory commands for {self.bot_name}")


# Factory function for easy integration
def create_llm_self_memory_handlers(bot, memory_manager, bot_name: str) -> LLMSelfMemoryCommandHandlers:
    """Create LLM self-memory command handlers"""
    return LLMSelfMemoryCommandHandlers(bot, memory_manager, bot_name)