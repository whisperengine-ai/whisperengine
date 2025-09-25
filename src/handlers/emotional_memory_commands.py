"""
🎭 Emotional Memory Commands - Quick Win Feature
Discord commands for users to explore their emotional memory prioritization
"""
import logging
from typing import Optional
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class EmotionalMemoryCommands:
    """Discord commands for emotional memory insights"""
    
    def __init__(self, bot, memory_manager, emotion_analyzer):
        self.bot = bot
        self.memory_manager = memory_manager
        self.emotion_analyzer = emotion_analyzer
    
    async def register_commands(self):
        """Register emotional memory commands"""
        
        @self.bot.tree.command(name="my_emotional_memories", description="🎭 View your most emotionally significant memories")
        async def my_emotional_memories(interaction: discord.Interaction, timeframe: Optional[str] = "week"):
            """Show user's high-priority emotional memories"""
            try:
                user_id = str(interaction.user.id)
                
                # Get high-priority memories
                high_priority_memories = await self.memory_manager.retrieve_context_aware_memories(
                    user_id=user_id,
                    query="emotional significance",
                    limit=5,
                    emotional_context={"priority_filter": "high"}
                )
                
                if not high_priority_memories:
                    await interaction.response.send_message("💭 No high-priority emotional memories found yet. Keep chatting!")
                    return
                
                # Format response
                embed = discord.Embed(
                    title="🎭 Your Most Emotionally Significant Memories",
                    color=discord.Color.purple(),
                    description=f"Last {timeframe} - High priority memories that shaped our conversation"
                )
                
                for i, memory in enumerate(high_priority_memories[:3], 1):
                    priority_marker = memory.get('priority_marker', '')
                    emotional_weight = memory.get('emotional_weight', 0.5)
                    timestamp = memory.get('timestamp', 'Unknown')
                    content_snippet = memory.get('content', '')[:100] + "..."
                    
                    embed.add_field(
                        name=f"{priority_marker} Memory {i} - Weight: {emotional_weight:.2f}",
                        value=f"**When:** {timestamp}\n**Context:** {content_snippet}",
                        inline=False
                    )
                
                embed.set_footer(text="💫 These memories get priority when building our conversation context")
                await interaction.response.send_message(embed=embed)
                
            except Exception as e:
                logger.error(f"Error showing emotional memories: {e}")
                await interaction.response.send_message("❌ Error retrieving emotional memories. Please try again.")
        
        @self.bot.tree.command(name="emotional_journey", description="📈 See your emotional journey and patterns")
        async def emotional_journey(interaction: discord.Interaction):
            """Show user's emotional trajectory"""
            try:
                user_id = str(interaction.user.id)
                
                # Get emotional dashboard data
                dashboard_data = await self.emotion_analyzer.get_user_emotional_dashboard(user_id)
                
                if not dashboard_data.get('recent_emotions'):
                    await interaction.response.send_message("📊 Not enough emotional data yet. Chat more to build your emotional journey!")
                    return
                
                # Format emotional journey
                embed = discord.Embed(
                    title="📈 Your Emotional Journey",
                    color=discord.Color.blue(),
                    description="How your emotions have evolved in our conversations"
                )
                
                recent_emotions = dashboard_data.get('recent_emotions', [])[:10]
                dominant_emotion = dashboard_data.get('dominant_emotion', 'neutral')
                confidence = dashboard_data.get('average_confidence', 0.0)
                
                # Emotion trajectory
                emotion_path = " → ".join(recent_emotions[-5:])  # Last 5 emotions
                embed.add_field(
                    name="🎭 Recent Emotional Path",
                    value=f"```{emotion_path}```",
                    inline=False
                )
                
                # Dominant patterns
                embed.add_field(
                    name="✨ Your Emotional Profile",
                    value=f"**Most Common:** {dominant_emotion}\n**Analysis Confidence:** {confidence:.1%}",
                    inline=True
                )
                
                # Memory prioritization impact
                embed.add_field(
                    name="🧠 Memory Impact",
                    value="High emotional moments get priority in conversation context",
                    inline=True
                )
                
                embed.set_footer(text="💡 This helps me remember what matters most to you")
                await interaction.response.send_message(embed=embed)
                
            except Exception as e:
                logger.error(f"Error showing emotional journey: {e}")
                await interaction.response.send_message("❌ Error retrieving emotional journey. Please try again.")
        
        @self.bot.tree.command(name="memory_priority_stats", description="📊 View your memory prioritization statistics")
        async def memory_priority_stats(interaction: discord.Interaction):
            """Show memory prioritization statistics"""
            try:
                user_id = str(interaction.user.id)
                
                # Get memory statistics with priority breakdown
                all_memories = await self.memory_manager.retrieve_relevant_memories(
                    user_id=user_id,
                    query="statistics",
                    limit=50
                )
                
                if not all_memories:
                    await interaction.response.send_message("📈 No memory data available yet. Start chatting to build your memory profile!")
                    return
                
                # Analyze priority distribution
                high_priority = sum(1 for m in all_memories if m.get('emotional_weight', 0) > 0.7)
                medium_priority = sum(1 for m in all_memories if 0.4 <= m.get('emotional_weight', 0) <= 0.7)
                normal_priority = len(all_memories) - high_priority - medium_priority
                
                # Format statistics
                embed = discord.Embed(
                    title="📊 Your Memory Prioritization Stats",
                    color=discord.Color.green(),
                    description="How your memories are prioritized in our conversations"
                )
                
                # Priority distribution
                total = len(all_memories)
                embed.add_field(
                    name="🎯 Priority Distribution",
                    value=f"**🔴 High Priority:** {high_priority} ({high_priority/total:.1%})\n"
                          f"**🟡 Medium Priority:** {medium_priority} ({medium_priority/total:.1%})\n"
                          f"**⚪ Normal Priority:** {normal_priority} ({normal_priority/total:.1%})",
                    inline=False
                )
                
                # System impact
                embed.add_field(
                    name="💫 System Impact",
                    value=f"**Total Memories:** {total}\n"
                          f"**High Priority memories appear first in conversation context**\n"
                          f"**Crisis emotions get automatic priority boost**",
                    inline=False
                )
                
                embed.set_footer(text="🧠 This prioritization helps me focus on what matters most to you")
                await interaction.response.send_message(embed=embed)
                
            except Exception as e:
                logger.error(f"Error showing memory stats: {e}")
                await interaction.response.send_message("❌ Error retrieving memory statistics. Please try again.")

        logger.info("✅ Emotional Memory Commands registered successfully")