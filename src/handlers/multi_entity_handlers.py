"""
Multi-Entity Command Handlers

Provides Discord commands for character creation, relationship management,
and multi-entity interactions within WhisperEngine.
"""

import logging
import asyncio
import json
import os
import io
from typing import Dict, List, Optional, Any
from datetime import datetime

import discord
from discord.ext import commands

from src.graph_database.multi_entity_models import EntityType, RelationshipType
from src.characters.cdl.parser import CDLParser, CDLParseError

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
    
    def register_commands(self, bot_name_filter, is_admin=None):
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
                    
                    # Handle character data safely (could be dict or other format)
                    if isinstance(character, dict):
                        name = character.get("name", "Unknown")
                        occupation = character.get("occupation", "Unknown")
                    else:
                        name = getattr(character, 'name', "Unknown")
                        occupation = getattr(character, 'occupation', "Unknown")
                    
                    # Handle relationship data safely
                    trust_level = 0.0
                    if isinstance(relationship, dict):
                        trust_level = relationship.get("trust_level", 0.0)
                    elif hasattr(relationship, 'get'):
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
        async def talk_to(ctx, character_name: str, *, message: str = ""):
            """Have a conversation with one of your characters"""
            try:
                # Check if message is provided
                if not message.strip():
                    await ctx.send(f"❌ Please provide a message to send to {character_name}.\n**Usage:** `!talk_to {character_name} <your message>`\n**Example:** `!talk_to {character_name} Hello, how are you?`")
                    return
                
                # Find character by name
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                character_data = None
                for char_data in user_characters:
                    # Handle character data safely (same fix as my_characters)
                    character = char_data.get("character", {})
                    if isinstance(character, dict):
                        char_name = character.get("name", "")
                    else:
                        char_name = getattr(character, 'name', "")
                    
                    if char_name.lower() == character_name.lower():
                        character_data = char_data
                        break
                
                if not character_data:
                    await ctx.send(f"❌ Character '{character_name}' not found. Use `!my_characters` to see your characters.")
                    return
                
                character = character_data.get("character", {})
                
                # Handle character data safely (same fix as my_characters)
                if isinstance(character, dict):
                    character_id = character.get("id", "")
                    char_name = character.get("name", "Character")
                    traits = character.get("personality_traits", [])
                    style = character.get("communication_style", "")
                else:
                    character_id = getattr(character, 'id', "")
                    char_name = getattr(character, 'name', "Character")
                    traits = getattr(character, 'personality_traits', [])
                    style = getattr(character, 'communication_style', "")
                
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
                    
                    response = f"*{char_name} responds thoughtfully*\n\nThank you for talking with me! I appreciate our conversation. Your message was: '{message}'\n\n*This is a basic response. Full LLM integration with character context coming soon!*"
                    
                    # Create response embed
                    embed = discord.Embed(
                        title=f"💬 Conversation with {char_name}",
                        description=response,
                        color=0xf39c12
                    )
                    
                    # Add character context
                    if traits:
                        if isinstance(traits, list):
                            embed.add_field(name="Character Traits", value=", ".join(str(t) for t in traits[:3]), inline=True)
                        else:
                            embed.add_field(name="Character Traits", value=str(traits)[:50], inline=True)
                    
                    if style:
                        embed.add_field(name="Communication Style", value=str(style), inline=True)
                    
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

        @self.bot.command(name='import_character')
        async def import_character(ctx, *, yaml_content: Optional[str] = None):
            """
            Import a character from CDL (Character Definition Language) YAML format.
            
            Usage: 
            !import_character <YAML content>
            Or attach a .yaml/.yml file to the message
            """
            if not self.multi_entity_available:
                await ctx.send("❌ Multi-entity features are not available.")
                return
                
            try:
                character_data = None
                source_info = ""
                
                # Check for attached file first
                if ctx.message.attachments:
                    attachment = ctx.message.attachments[0]
                    if attachment.filename.endswith(('.yaml', '.yml', '.cdl')):
                        try:
                            file_content = await attachment.read()
                            yaml_content = file_content.decode('utf-8')
                            source_info = f" from {attachment.filename}"
                        except Exception as e:
                            await ctx.send(f"❌ Error reading attached file: {e}")
                            return
                    else:
                        await ctx.send("❌ Please attach a .yaml, .yml, or .cdl file, or provide YAML content directly.")
                        return
                
                # If no attachment and no content provided
                if not yaml_content:
                    await ctx.send("❌ Please provide CDL YAML content or attach a character file.\n"
                                 "Example: `!import_character` with a .yaml file attached")
                    return
                
                # Parse the CDL YAML
                parser = CDLParser()
                
                # Try to parse as YAML dict first
                import yaml
                try:
                    yaml_dict = yaml.safe_load(yaml_content)
                    character = parser.parse_dict(yaml_dict)
                except yaml.YAMLError as e:
                    await ctx.send(f"❌ Invalid YAML format: {e}")
                    return
                except CDLParseError as e:
                    await ctx.send(f"❌ CDL parsing error: {e}")
                    return
                
                # Convert CDL character to multi-entity format
                user_id = str(ctx.author.id)
                
                # Create character entity data
                character_data = {
                    "name": character.identity.name,
                    "description": f"CDL imported character: {character.identity.occupation}",
                    "personality_type": "companion",  # Default type for CDL imports
                    "traits": character.personality.values + character.personality.quirks,  # Combine values and quirks as traits
                    "background": f"Occupation: {character.identity.occupation}, Location: {character.identity.location}",
                    "created_by": user_id,
                    "import_source": f"CDL{source_info}",
                    "metadata": {
                        "cdl_version": character.metadata.version if character.metadata else "1.0",
                        "original_name": character.identity.name,
                        "imported_at": datetime.now().isoformat(),
                        "character_id": character.metadata.character_id
                    }
                }
                
                # Add any additional CDL-specific data
                if character.personality and hasattr(character.personality, 'big_five'):
                    big_five = character.personality.big_five
                    if big_five:
                        character_data["metadata"]["big_five"] = {
                            "openness": big_five.openness,
                            "conscientiousness": big_five.conscientiousness,
                            "extraversion": big_five.extraversion,
                            "agreeableness": big_five.agreeableness,
                            "neuroticism": big_five.neuroticism
                        }
                
                # Create the character in the multi-entity system
                character_id = await self.multi_entity_manager.create_character_entity(
                    character_data, str(ctx.author.id)
                )
                
                # Create success embed
                embed = discord.Embed(
                    title="✅ Character Imported Successfully",
                    description=f"**{character.identity.name}** has been imported{source_info}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(name="Character ID", value=str(character_id), inline=True)
                embed.add_field(name="Type", value=character_data["personality_type"], inline=True)
                embed.add_field(name="Source", value="CDL Import", inline=True)
                
                # Add occupation and location info
                if character.identity.occupation:
                    embed.add_field(name="Occupation", value=character.identity.occupation, inline=True)
                
                if character.identity.location:
                    embed.add_field(name="Location", value=character.identity.location, inline=True)
                
                # Add personality traits
                if character.personality.values:
                    values_text = ", ".join(character.personality.values[:5])  # Limit to 5 values
                    embed.add_field(name="Core Values", value=values_text, inline=False)
                
                embed.set_footer(text=f"You can now use !talk_to \"{character.identity.name}\" to interact")
                
                await ctx.send(embed=embed)
                
                # Log the import
                self.logger.info(f"Character '{character.identity.name}' imported from CDL by user {ctx.author.id}")
                
            except Exception as e:
                self.logger.error(f"Error in CDL character import: {e}")
                await ctx.send(f"❌ An error occurred during character import: {e}")

        @self.bot.command(name='export_character')
        async def export_character(ctx, *, character_name: str):
            """
            Export a character to CDL (Character Definition Language) YAML format.
            
            Usage: !export_character <character_name>
            """
            if not self.multi_entity_available:
                await ctx.send("❌ Multi-entity features are not available.")
                return
                
            try:
                # Get user's characters
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                # Find the character by name
                target_character = None
                for char in user_characters:
                    if char.get('name', '').lower() == character_name.lower():
                        target_character = char
                        break
                
                if not target_character:
                    available_names = [char.get('name') for char in user_characters if char.get('name')]
                    if available_names:
                        names_list = ", ".join(available_names)
                        await ctx.send(f"❌ Character '{character_name}' not found.\nYour characters: {names_list}")
                    else:
                        await ctx.send("❌ You don't have any characters to export. Create one with `!create_character` first.")
                    return
                
                # Convert multi-entity character to CDL format
                cdl_data = {
                    "cdl_version": "1.0",
                    "character": {
                        "metadata": {
                            "character_id": target_character.get('id', 'unknown'),
                            "name": target_character.get('name', ''),
                            "version": "1.0.0",
                            "created_by": f"WhisperEngine User {ctx.author.name}",
                            "created_date": target_character.get('created_at', datetime.now().isoformat()),
                            "last_modified": datetime.now().isoformat(),
                            "license": "free",
                            "tags": ["exported", "multi-entity"]
                        },
                        "identity": {
                            "name": target_character.get('name', ''),
                            "age": 25,  # Default age
                            "gender": "prefer_not_to_say",
                            "occupation": target_character.get('personality_type', 'companion').title(),
                            "location": "Online",
                            "nickname": target_character.get('name', ''),
                            "full_name": target_character.get('name', '')
                        },
                        "personality": {
                            "big_five": {
                                "openness": 0.7,
                                "conscientiousness": 0.6,
                                "extraversion": 0.6,
                                "agreeableness": 0.8,
                                "neuroticism": 0.3
                            },
                            "values": target_character.get('traits', [])[:5],  # Use traits as values
                            "fears": [],
                            "dreams": [],
                            "quirks": target_character.get('traits', [])[5:] if len(target_character.get('traits', [])) > 5 else [],
                            "core_beliefs": []
                        },
                        "backstory": {
                            "childhood": {
                                "phase_name": "Digital Genesis",
                                "age_range": "0-1",
                                "key_events": ["Created in WhisperEngine"],
                                "formative_experiences": ["First interactions with users"]
                            },
                            "major_life_events": [
                                f"Created by {ctx.author.name}",
                                "Began conversations with users"
                            ],
                            "family_background": target_character.get('background', ''),
                            "cultural_background": "Digital AI Culture"
                        },
                        "current_life": {
                            "current_goals": [
                                "Assist and engage with users",
                                "Learn and grow through interactions"
                            ],
                            "current_challenges": [
                                "Understanding human emotions",
                                "Providing helpful responses"
                            ],
                            "living_situation": "Exists in digital space",
                            "hobbies": ["Conversation", "Learning", "Helping others"]
                        }
                    }
                }
                
                # Add Big Five data from metadata if available
                metadata = target_character.get('metadata', {})
                if isinstance(metadata, dict) and 'big_five' in metadata:
                    big_five_data = metadata['big_five']
                    if isinstance(big_five_data, dict):
                        cdl_data["character"]["personality"]["big_five"].update(big_five_data)
                
                # Convert to YAML
                import yaml
                yaml_content = yaml.dump(cdl_data, default_flow_style=False, allow_unicode=True, indent=2)
                
                # Create and send the file
                import io
                yaml_file = io.StringIO(yaml_content)
                file_name = f"{target_character.get('name', 'character').lower().replace(' ', '_')}_export.yaml"
                
                discord_file = discord.File(io.BytesIO(yaml_content.encode('utf-8')), filename=file_name)
                
                # Create success embed
                embed = discord.Embed(
                    title="📤 Character Exported Successfully",
                    description=f"**{target_character.get('name')}** has been exported to CDL format",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(name="Format", value="CDL (Character Definition Language)", inline=True)
                embed.add_field(name="File Type", value="YAML", inline=True)
                embed.add_field(name="Version", value="1.0", inline=True)
                
                traits_count = len(target_character.get('traits', []))
                embed.add_field(name="Traits Exported", value=str(traits_count), inline=True)
                embed.add_field(name="Original Type", value=target_character.get('personality_type', 'unknown'), inline=True)
                
                embed.set_footer(text="You can import this character with !import_character")
                
                await ctx.send(embed=embed, file=discord_file)
                
                # Log the export
                self.logger.info(f"Character '{target_character.get('name')}' exported to CDL by user {ctx.author.id}")
                
            except Exception as e:
                self.logger.error(f"Error in CDL character export: {e}")
                await ctx.send(f"❌ An error occurred during character export: {e}")

        @self.bot.command(name='set_relationship')
        async def set_relationship(ctx, character1_name: str, relationship_type: str, character2_name: str, trust_level: float = 0.5):
            """Set a relationship between two of your characters"""
            try:
                # Validate trust level
                if not 0.0 <= trust_level <= 1.0:
                    await ctx.send("❌ Trust level must be between 0.0 and 1.0")
                    return
                
                # Validate relationship type
                valid_types = {
                    'knows': RelationshipType.KNOWS_ABOUT,
                    'friends': RelationshipType.FAMILIAR_WITH,
                    'family': RelationshipType.RELATED_TO,
                    'similar': RelationshipType.SIMILAR_TO,
                    'contrasts': RelationshipType.CONTRASTS_WITH,
                    'collaborates': RelationshipType.INTERACTS_WITH
                }
                
                if relationship_type.lower() not in valid_types:
                    types_list = ", ".join(valid_types.keys())
                    await ctx.send(f"❌ Invalid relationship type. Valid types: {types_list}")
                    return
                
                # Get user's characters
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                # Find both characters
                char1_data = None
                char2_data = None
                
                for char_data in user_characters:
                    character = char_data.get("character", {})
                    if isinstance(character, dict):
                        char_name = character.get("name", "")
                    else:
                        char_name = getattr(character, 'name', "")
                    
                    if char_name.lower() == character1_name.lower():
                        char1_data = char_data
                    elif char_name.lower() == character2_name.lower():
                        char2_data = char_data
                
                if not char1_data:
                    await ctx.send(f"❌ Character '{character1_name}' not found in your characters.")
                    return
                
                if not char2_data:
                    await ctx.send(f"❌ Character '{character2_name}' not found in your characters.")
                    return
                
                # Get character IDs
                char1 = char1_data.get("character", {})
                char2 = char2_data.get("character", {})
                
                if isinstance(char1, dict):
                    char1_id = char1.get("id", "")
                    char1_name_display = char1.get("name", character1_name)
                else:
                    char1_id = getattr(char1, 'id', "")
                    char1_name_display = getattr(char1, 'name', character1_name)
                
                if isinstance(char2, dict):
                    char2_id = char2.get("id", "")
                    char2_name_display = char2.get("name", character2_name)
                else:
                    char2_id = getattr(char2, 'id', "")
                    char2_name_display = getattr(char2, 'name', character2_name)
                
                if not char1_id or not char2_id:
                    await ctx.send("❌ Unable to get character IDs. Please try again.")
                    return
                
                # Create the relationship
                rel_type = valid_types[relationship_type.lower()]
                success = await self.multi_entity_manager.create_relationship(
                    char1_id, char2_id,
                    EntityType.CHARACTER, EntityType.CHARACTER,
                    rel_type,
                    relationship_context=f"User-defined {relationship_type} relationship",
                    trust_level=trust_level,
                    familiarity_level=trust_level  # Use trust level as familiarity baseline
                )
                
                if success:
                    embed = discord.Embed(
                        title="🤝 Relationship Created",
                        description=f"Successfully created a **{relationship_type}** relationship between **{char1_name_display}** and **{char2_name_display}**",
                        color=0x2ecc71
                    )
                    embed.add_field(name="Relationship Type", value=relationship_type.title(), inline=True)
                    embed.add_field(name="Trust Level", value=f"{trust_level:.1f}/1.0", inline=True)
                    embed.add_field(name="Status", value="✅ Active", inline=True)
                    
                    await ctx.send(embed=embed)
                    
                    # Log the relationship creation
                    self.logger.info(f"User {ctx.author.id} created {relationship_type} relationship between {char1_name_display} and {char2_name_display}")
                else:
                    await ctx.send("❌ Failed to create relationship. Please try again.")
                
            except Exception as e:
                self.logger.error(f"Error setting relationship: {e}")
                await ctx.send("❌ An error occurred while setting the relationship.")

        @self.bot.command(name='character_relationships')
        async def character_relationships(ctx, character_name: str):
            """View all relationships for a specific character"""
            try:
                # Get user's characters
                user_characters = await self.multi_entity_manager.get_user_characters(str(ctx.author.id))
                
                # Find the character
                character_data = None
                for char_data in user_characters:
                    character = char_data.get("character", {})
                    if isinstance(character, dict):
                        char_name = character.get("name", "")
                    else:
                        char_name = getattr(character, 'name', "")
                    
                    if char_name.lower() == character_name.lower():
                        character_data = char_data
                        break
                
                if not character_data:
                    await ctx.send(f"❌ Character '{character_name}' not found in your characters.")
                    return
                
                character = character_data.get("character", {})
                if isinstance(character, dict):
                    character_id = character.get("id", "")
                    char_display_name = character.get("name", character_name)
                else:
                    character_id = getattr(character, 'id', "")
                    char_display_name = getattr(character, 'name', character_name)
                
                if not character_id:
                    await ctx.send("❌ Unable to get character ID. Please try again.")
                    return
                
                # Get character's network
                network = await self.multi_entity_manager.get_character_network(character_id)
                
                if not network:
                    await ctx.send(f"❌ Unable to retrieve relationship network for {char_display_name}.")
                    return
                
                embed = discord.Embed(
                    title=f"🕸️ {char_display_name}'s Relationships",
                    color=0x9b59b6
                )
                
                # Character relationships
                char_relationships = network.get("characters", [])
                if char_relationships:
                    char_list = []
                    for rel in char_relationships[:5]:  # Limit to 5 to avoid embed limits
                        char_info = rel.get("character", {})
                        rel_info = rel.get("relationship", {})
                        
                        if isinstance(char_info, dict):
                            related_name = char_info.get("name", "Unknown")
                        else:
                            related_name = getattr(char_info, 'name', "Unknown")
                        
                        if isinstance(rel_info, dict):
                            rel_type = rel_info.get("relationship_type", "unknown")
                            trust = rel_info.get("trust_level", 0.0)
                        else:
                            rel_type = getattr(rel_info, 'relationship_type', "unknown")
                            trust = getattr(rel_info, 'trust_level', 0.0)
                        
                        char_list.append(f"**{related_name}** - {rel_type.replace('_', ' ').title()} (Trust: {trust:.1f})")
                    
                    embed.add_field(
                        name=f"Character Relationships ({len(char_relationships)})",
                        value="\n".join(char_list) if char_list else "No character relationships",
                        inline=False
                    )
                
                # User relationships
                user_relationships = network.get("users", [])
                if user_relationships:
                    user_list = []
                    for rel in user_relationships[:3]:  # Limit to 3 users
                        user_info = rel.get("user", {})
                        rel_info = rel.get("relationship", {})
                        
                        if isinstance(user_info, dict):
                            username = user_info.get("username", "Unknown User")
                        else:
                            username = getattr(user_info, 'username', "Unknown User")
                        
                        if isinstance(rel_info, dict):
                            trust = rel_info.get("trust_level", 0.0)
                            familiarity = rel_info.get("familiarity_level", 0.0)
                        else:
                            trust = getattr(rel_info, 'trust_level', 0.0)
                            familiarity = getattr(rel_info, 'familiarity_level', 0.0)
                        
                        user_list.append(f"**{username}** - Trust: {trust:.1f}, Familiarity: {familiarity:.1f}")
                    
                    embed.add_field(
                        name=f"User Relationships ({len(user_relationships)})",
                        value="\n".join(user_list) if user_list else "No user relationships",
                        inline=False
                    )
                
                # Network stats
                total_relationships = network.get("total_relationships", 0)
                network_strength = network.get("network_strength", 0.0)
                
                embed.add_field(
                    name="Network Summary",
                    value=f"Total Connections: **{total_relationships}**\nNetwork Strength: **{network_strength:.2f}**",
                    inline=False
                )
                
                embed.add_field(
                    name="Commands",
                    value="`!set_relationship <char1> <type> <char2>` - Create relationship\n`!relationship_analysis <character>` - Analyze relationship with you",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                self.logger.error(f"Error viewing character relationships: {e}")
                await ctx.send("❌ An error occurred while retrieving character relationships.")

        self.logger.info("✅ Multi-entity commands registered successfully")