"""
Multi-Entity Command Handlers

Provides Discord commands for character creation, relationship management,
and multi-entity interactions within WhisperEngine.
"""

import logging
import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

import discord
from discord.ext import commands

from src.graph_database.multi_entity_models import EntityType, RelationshipType

logger = logging.getLogger(__name__)


class MultiEntityCommandHandlers:
    """
    Command handlers for multi-entity relationship features.
    
    Provides commands for:
    - Character creation and management
    - Relationship viewing and analysis  
    - AI-facilitated introductions
    - Social network analysis
    """
    
    def __init__(self, bot, **dependencies):
        self.bot = bot
        self.multi_entity_manager = dependencies.get('multi_entity_manager')
        self.ai_self_bridge = dependencies.get('ai_self_bridge')
        self.memory_manager = dependencies.get('memory_manager')
        self.logger = logging.getLogger(__name__)
        
        # Check if multi-entity features are available
        self.multi_entity_available = (
            self.multi_entity_manager is not None and 
            self.ai_self_bridge is not None
        )
        
        if not self.multi_entity_available:
            self.logger.warning("Multi-entity features not available - commands will be disabled")
    
    def register_commands(self, bot_name_filter: str = "", is_admin: callable = None):
        """Register multi-entity commands with the bot"""
        
        if not self.multi_entity_available:
            self.logger.info("Skipping multi-entity command registration - features not available")
            return
        
        @self.bot.command(name='create_character')
        async def create_character(ctx, name: str, occupation: str = "companion", *, description: str = ""):
            """
            Create a new character.
            
            Usage: !create_character "Character Name" occupation "Description of character"
            Example: !create_character "Sage" philosopher "A wise character who loves deep conversations"
            """
            try:
                # Check if user has reached character limit
                max_characters = int(os.getenv("MAX_CHARACTERS_PER_USER", "10"))
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                if len(user_characters) >= max_characters:
                    await ctx.send(f"❌ You've reached the maximum of {max_characters} characters. Delete a character first using `!delete_character`.")
                    return
                
                # Validate input
                if len(name) > int(os.getenv("MAX_CHARACTER_NAME_LENGTH", "50")):
                    await ctx.send("❌ Character name is too long. Please use a shorter name.")
                    return
                
                if len(description) > int(os.getenv("MAX_CHARACTER_BACKGROUND_LENGTH", "1000")):
                    await ctx.send("❌ Character description is too long. Please shorten it.")
                    return
                
                # Create user entity if not exists
                user_data = {
                    "discord_id": str(ctx.author.id),
                    "username": ctx.author.name,
                    "display_name": ctx.author.display_name,
                    "personality_traits": [],
                    "communication_style": "adaptive"
                }
                
                user_id = await self.multi_entity_manager.create_user_entity(user_data)
                if not user_id:
                    await ctx.send("❌ Failed to create user profile. Please try again.")
                    return
                
                # Create character
                character_data = {
                    "name": name,
                    "occupation": occupation,
                    "age": 25,  # Default age
                    "personality_traits": ["friendly", "helpful"],
                    "communication_style": "adaptive",
                    "background_summary": description or f"A {occupation} named {name}",
                    "preferred_topics": [occupation, "conversation", "helping"],
                    "conversation_style": "engaging"
                }
                
                character_id = await self.multi_entity_manager.create_character_entity(
                    character_data, user_id
                )
                
                if character_id:
                    embed = discord.Embed(
                        title="✨ Character Created!",
                        description=f"**{name}** has been created successfully!",
                        color=0x00ff88
                    )
                    embed.add_field(name="Occupation", value=occupation, inline=True)
                    embed.add_field(name="Creator", value=ctx.author.display_name, inline=True)
                    embed.add_field(name="Character ID", value=character_id[:8], inline=True)
                    
                    if description:
                        embed.add_field(name="Description", value=description[:200] + ("..." if len(description) > 200 else ""), inline=False)
                    
                    embed.add_field(
                        name="Next Steps", 
                        value=f"• Use `!talk_to {name}` to have a conversation\n• Use `!character_info {name}` to view details\n• Use `!my_characters` to see all your characters",
                        inline=False
                    )
                    
                    await ctx.send(embed=embed)
                    
                    # Log character creation
                    self.logger.info(f"Character '{name}' created by user {ctx.author.name} ({ctx.author.id})")
                    
                else:
                    await ctx.send("❌ Failed to create character. Please try again.")
                
            except Exception as e:
                self.logger.error(f"Error creating character: {e}")
                await ctx.send("❌ An error occurred while creating the character. Please try again.")
        
        @self.bot.command(name='my_characters')
        async def my_characters(ctx):
            """List all characters created by the user"""
            try:
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                if not user_characters:
                    embed = discord.Embed(
                        title="Your Characters",
                        description="You haven't created any characters yet.\n\nUse `!create_character` to create your first character!",
                        color=0x3498db
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = discord.Embed(
                    title=f"{ctx.author.display_name}'s Characters",
                    description=f"You have {len(user_characters)} character(s)",
                    color=0x9b59b6
                )
                
                for char_data in user_characters[:10]:  # Limit to 10 characters
                    character = char_data.get("character", {})
                    relationship = char_data.get("relationship", {})
                    
                    name = character.get("name", "Unknown")
                    occupation = character.get("occupation", "Unknown")
                    trust_level = relationship.get("trust_level", 0.0)
                    
                    value = f"**Occupation:** {occupation}\n**Trust Level:** {trust_level:.1f}/1.0"
                    embed.add_field(name=name, value=value, inline=True)
                
                embed.add_field(
                    name="Commands",
                    value="`!character_info <name>` - View character details\n`!talk_to <name>` - Start conversation\n`!delete_character <name>` - Delete character",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                self.logger.error(f"Error listing characters: {e}")
                await ctx.send("❌ An error occurred while fetching your characters.")
        
        @self.bot.command(name='character_info')
        async def character_info(ctx, *, character_name: str):
            """Get detailed information about a character"""
            try:
                # Find character by name (search user's characters first)
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                character_data = None
                for char_data in user_characters:
                    if char_data.get("character", {}).get("name", "").lower() == character_name.lower():
                        character_data = char_data
                        break
                
                if not character_data:
                    await ctx.send(f"❌ Character '{character_name}' not found in your characters.")
                    return
                
                character = character_data.get("character", {})
                relationship = character_data.get("relationship", {})
                character_id = character.get("id", "")
                
                # Get character network
                network = await self.multi_entity_manager.get_character_network(character_id)
                
                embed = discord.Embed(
                    title=f"📋 {character.get('name', 'Unknown')}",
                    color=0xe74c3c
                )
                
                # Basic info
                embed.add_field(name="Occupation", value=character.get("occupation", "Unknown"), inline=True)
                embed.add_field(name="Age", value=str(character.get("age", "Unknown")), inline=True)
                embed.add_field(name="Communication Style", value=character.get("communication_style", "Unknown"), inline=True)
                
                # Personality traits
                traits = character.get("personality_traits", [])
                if traits:
                    embed.add_field(name="Personality Traits", value=", ".join(traits), inline=False)
                
                # Background
                background = character.get("background_summary", "")
                if background:
                    embed.add_field(name="Background", value=background[:300] + ("..." if len(background) > 300 else ""), inline=False)
                
                # Interests
                topics = character.get("preferred_topics", [])
                if topics:
                    embed.add_field(name="Interests", value=", ".join(topics), inline=False)
                
                # Relationship with user
                trust_level = relationship.get("trust_level", 0.0)
                familiarity_level = relationship.get("familiarity_level", 0.0)
                interaction_count = relationship.get("interaction_count", 0)
                
                relationship_value = f"Trust: {trust_level:.1f}/1.0\nFamiliarity: {familiarity_level:.1f}/1.0\nInteractions: {interaction_count}"
                embed.add_field(name="Your Relationship", value=relationship_value, inline=True)
                
                # Network stats
                total_relationships = network.get("total_relationships", 0)
                network_strength = network.get("network_strength", 0.0)
                embed.add_field(name="Social Network", value=f"Connections: {total_relationships}\nNetwork Strength: {network_strength:.1f}", inline=True)
                
                # Character ID (for debugging/admin)
                embed.add_field(name="Character ID", value=character_id[:8], inline=True)
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                self.logger.error(f"Error getting character info: {e}")
                await ctx.send("❌ An error occurred while fetching character information.")
        
        @self.bot.command(name='talk_to')
        async def talk_to(ctx, character_name: str, *, message: str):
            """Have a conversation with one of your characters"""
            try:
                # Find character by name
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                character_data = None
                for char_data in user_characters:
                    if char_data.get("character", {}).get("name", "").lower() == character_name.lower():
                        character_data = char_data
                        break
                
                if not character_data:
                    await ctx.send(f"❌ Character '{character_name}' not found. Use `!my_characters` to see your characters.")
                    return
                
                character = character_data.get("character", {})
                character_id = character.get("id", "")
                
                # Send typing indicator
                async with ctx.typing():
                    # Record the interaction
                    await self.multi_entity_manager.record_interaction(
                        str(ctx.author.id),
                        character_id,
                        "conversation",
                        f"User message: {message[:100]}...",
                        "neutral",
                        0.6,  # Positive sentiment for normal conversation
                        5.0   # Estimated 5 minutes
                    )
                    
                    # For now, create a simple response
                    # In a full implementation, this would integrate with the LLM client
                    # using the multi-entity context injector
                    
                    character_name = character.get("name", "Character")
                    response = f"*{character_name} responds thoughtfully*\n\nThank you for talking with me! I appreciate our conversation. Your message was: '{message}'\n\n*This is a basic response. Full LLM integration with character context coming soon!*"
                    
                    # Create response embed
                    embed = discord.Embed(
                        title=f"💬 Conversation with {character_name}",
                        description=response,
                        color=0xf39c12
                    )
                    
                    # Add character context
                    traits = character.get("personality_traits", [])
                    if traits:
                        embed.add_field(name="Character Traits", value=", ".join(traits[:3]), inline=True)
                    
                    style = character.get("communication_style", "")
                    if style:
                        embed.add_field(name="Communication Style", value=style, inline=True)
                    
                    await ctx.send(embed=embed)
                
            except Exception as e:
                self.logger.error(f"Error in character conversation: {e}")
                await ctx.send("❌ An error occurred during the conversation.")
        
        @self.bot.command(name='introduce_character')
        async def introduce_character(ctx, target_user: discord.Member, character_name: str):
            """Have the AI introduce one of your characters to another user"""
            try:
                if not self.ai_self_bridge:
                    await ctx.send("❌ AI introductions are not available.")
                    return
                
                # Find character
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                character_data = None
                for char_data in user_characters:
                    if char_data.get("character", {}).get("name", "").lower() == character_name.lower():
                        character_data = char_data
                        break
                
                if not character_data:
                    await ctx.send(f"❌ Character '{character_name}' not found in your characters.")
                    return
                
                character = character_data.get("character", {})
                character_id = character.get("id", "")
                
                # Create target user entity if needed
                target_user_data = {
                    "discord_id": str(target_user.id),
                    "username": target_user.name,
                    "display_name": target_user.display_name,
                    "personality_traits": [],
                    "communication_style": "adaptive"
                }
                
                target_user_id = await self.multi_entity_manager.create_user_entity(target_user_data)
                
                # Perform AI-facilitated introduction
                async with ctx.typing():
                    introduction_result = await self.ai_self_bridge.introduce_character_to_user(
                        character_id,
                        target_user_id,
                        f"Discord introduction from {ctx.author.display_name}"
                    )
                
                if introduction_result.get("introduction_successful"):
                    compatibility = introduction_result.get("compatibility_analysis", {})
                    compatibility_score = compatibility.get("compatibility_score", 0.0)
                    
                    embed = discord.Embed(
                        title="🤝 Character Introduction",
                        description=f"The AI system has introduced **{character.get('name')}** to {target_user.mention}!",
                        color=0x2ecc71
                    )
                    
                    embed.add_field(name="Character", value=character.get("name", "Unknown"), inline=True)
                    embed.add_field(name="Occupation", value=character.get("occupation", "Unknown"), inline=True)
                    embed.add_field(name="Compatibility Score", value=f"{compatibility_score:.1f}/1.0", inline=True)
                    
                    # Add conversation starters
                    starters = introduction_result.get("recommended_conversation_starters", [])
                    if starters:
                        embed.add_field(name="Conversation Starters", value=f"• {starters[0]}", inline=False)
                    
                    # Add AI insights
                    ai_insights = introduction_result.get("ai_insights", {})
                    potential = ai_insights.get("relationship_potential", "")
                    if potential:
                        embed.add_field(name="Relationship Potential", value=potential, inline=False)
                    
                    await ctx.send(embed=embed)
                    
                    # Send notification to target user
                    try:
                        dm_embed = discord.Embed(
                            title="Character Introduction",
                            description=f"{ctx.author.display_name} has introduced you to their character **{character.get('name')}**!",
                            color=0x3498db
                        )
                        dm_embed.add_field(name="How to interact", value=f"You can now use `!talk_to {character.get('name')}` to have a conversation!", inline=False)
                        await target_user.send(embed=dm_embed)
                    except:
                        # If DM fails, mention in channel
                        await ctx.send(f"{target_user.mention}, you've been introduced to {character.get('name')}! Check the message above for details.")
                
                else:
                    await ctx.send("❌ The AI system determined this introduction wouldn't be beneficial at this time.")
                
            except Exception as e:
                self.logger.error(f"Error in character introduction: {e}")
                await ctx.send("❌ An error occurred during the introduction.")
        
        @self.bot.command(name='relationship_analysis')
        async def relationship_analysis(ctx, character_name: str):
            """Analyze your relationship with a character"""
            try:
                if not self.ai_self_bridge:
                    await ctx.send("❌ Relationship analysis is not available.")
                    return
                
                # Find character
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                character_data = None
                for char_data in user_characters:
                    if char_data.get("character", {}).get("name", "").lower() == character_name.lower():
                        character_data = char_data
                        break
                
                if not character_data:
                    await ctx.send(f"❌ Character '{character_name}' not found in your characters.")
                    return
                
                character = character_data.get("character", {})
                character_id = character.get("id", "")
                
                # Analyze relationship evolution
                async with ctx.typing():
                    analysis = await self.ai_self_bridge.analyze_relationship_evolution(
                        str(ctx.author.id), character_id
                    )
                
                if "error" in analysis:
                    await ctx.send("❌ Unable to analyze relationship at this time.")
                    return
                
                embed = discord.Embed(
                    title=f"📊 Relationship Analysis: {character.get('name')}",
                    color=0x9b59b6
                )
                
                # Current metrics
                stage = analysis.get("current_stage", "unknown")
                trust = analysis.get("trust_level", 0.0)
                familiarity = analysis.get("familiarity_level", 0.0)
                interactions = analysis.get("interaction_count", 0)
                strength = analysis.get("relationship_strength", 0.0)
                
                embed.add_field(name="Relationship Stage", value=stage.replace("_", " ").title(), inline=True)
                embed.add_field(name="Trust Level", value=f"{trust:.1f}/1.0", inline=True)
                embed.add_field(name="Familiarity", value=f"{familiarity:.1f}/1.0", inline=True)
                embed.add_field(name="Interactions", value=str(interactions), inline=True)
                embed.add_field(name="Overall Strength", value=f"{strength:.1f}/1.0", inline=True)
                embed.add_field(name="Development Trend", value=analysis.get("development_trend", "unknown").replace("_", " ").title(), inline=True)
                
                # Next stage requirements
                requirements = analysis.get("next_stage_requirements", [])
                if requirements:
                    req_text = "\n".join([f"• {req}" for req in requirements[:3]])
                    embed.add_field(name="To Improve Relationship", value=req_text, inline=False)
                
                # AI recommendations
                recommendations = analysis.get("ai_recommendations", [])
                if recommendations:
                    rec_text = "\n".join([f"• {rec}" for rec in recommendations[:3]])
                    embed.add_field(name="AI Recommendations", value=rec_text, inline=False)
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                self.logger.error(f"Error in relationship analysis: {e}")
                await ctx.send("❌ An error occurred during relationship analysis.")
        
        @self.bot.command(name='social_network')
        async def social_network(ctx):
            """View your social network summary"""
            try:
                if not self.ai_self_bridge:
                    await ctx.send("❌ Social network analysis is not available.")
                    return
                
                # Get user's social network summary
                async with ctx.typing():
                    summary = await self.ai_self_bridge.get_entity_social_network_summary(str(ctx.author.id))
                
                if "error" in summary:
                    await ctx.send("❌ Unable to analyze your social network at this time.")
                    return
                
                embed = discord.Embed(
                    title=f"🌐 {ctx.author.display_name}'s Social Network",
                    color=0x1abc9c
                )
                
                # Network stats
                network_size = summary.get("network_size", 0)
                strong_relationships = summary.get("strong_relationships", 0)
                developing = summary.get("developing_relationships", 0)
                weak = summary.get("weak_relationships", 0)
                
                embed.add_field(name="Total Connections", value=str(network_size), inline=True)
                embed.add_field(name="Strong Relationships", value=str(strong_relationships), inline=True)
                embed.add_field(name="Developing", value=str(developing), inline=True)
                
                # Network health
                avg_trust = summary.get("average_trust_level", 0.0)
                avg_familiarity = summary.get("average_familiarity_level", 0.0)
                diversity = summary.get("network_diversity", 0)
                
                embed.add_field(name="Average Trust", value=f"{avg_trust:.1f}/1.0", inline=True)
                embed.add_field(name="Average Familiarity", value=f"{avg_familiarity:.1f}/1.0", inline=True)
                embed.add_field(name="Relationship Diversity", value=str(diversity), inline=True)
                
                # AI assessment
                assessment = summary.get("ai_network_assessment", {})
                health_score = assessment.get("health_score", 0.0)
                health_assessment = assessment.get("assessment", "unknown")
                
                embed.add_field(name="Network Health", value=f"{health_assessment.title()} ({health_score:.1f}/1.0)", inline=False)
                
                # Recommendations
                recommendations = assessment.get("recommendations", [])
                if recommendations:
                    rec_text = "\n".join([f"• {rec}" for rec in recommendations[:3]])
                    embed.add_field(name="Recommendations", value=rec_text, inline=False)
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                self.logger.error(f"Error in social network analysis: {e}")
                await ctx.send("❌ An error occurred during social network analysis.")

        self.logger.info("✅ Multi-entity commands registered successfully")