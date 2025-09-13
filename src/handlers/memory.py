"""
Memory command handlers for Discord bot
Includes fact management, conversation sync, memory viewing, and data deletion
"""
import logging
import discord
from discord.ext import commands
from typing import Optional
import asyncio
from datetime import datetime, timezone
from src.utils.exceptions import ValidationError, MemoryStorageError
from src.utils.helpers import extract_text_for_memory_storage

logger = logging.getLogger(__name__)

class MemoryCommandHandlers:
    """Handles memory-related commands"""
    
    def __init__(self, bot, memory_manager, safe_memory_manager, context_memory_manager, 
                 graph_personality_manager, personality_profiler):
        self.bot = bot
        self.memory_manager = memory_manager
        self.safe_memory_manager = safe_memory_manager
        self.context_memory_manager = context_memory_manager
        self.graph_personality_manager = graph_personality_manager
        self.personality_profiler = personality_profiler
    
    def register_commands(self, is_admin, bot_name_filter=None):
        """Register all memory commands"""
        
        # Default to no-op filter if none provided
        if bot_name_filter is None:
            bot_name_filter = lambda: lambda func: func
        
        @self.bot.command(name='add_fact')
        @bot_name_filter()
        async def add_fact(ctx, *, fact):
            """Add a fact about yourself to the bot's memory"""
            await self._add_fact_handler(ctx, fact)
        
        @self.bot.command(name='remove_fact')
        @bot_name_filter()
        async def remove_fact(ctx, *, search_term):
            """Search and remove facts about yourself"""
            await self._remove_fact_handler(ctx, search_term)
        
        @self.bot.command(name='remove_fact_by_number')
        @bot_name_filter()
        async def remove_fact_by_number(ctx, fact_number: int, *, search_term):
            """Remove a specific fact by its number from the search results"""
            await self._remove_fact_by_number_handler(ctx, fact_number, search_term)
        
        @self.bot.command(name='list_facts')
        @bot_name_filter()
        async def list_facts(ctx):
            """List all facts the bot knows about you"""
            await self._list_facts_handler(ctx)
        
        @self.bot.command(name='add_global_fact')
        async def add_global_fact(ctx, *, fact):
            """Add a global fact about the world or relationships (admin only)"""
            await self._add_global_fact_handler(ctx, fact, is_admin)
        
        @self.bot.command(name='list_global_facts')
        async def list_global_facts(ctx):
            """List all global facts (admin only)"""
            await self._list_global_facts_handler(ctx, is_admin)
        
        @self.bot.command(name='remove_global_fact')
        async def remove_global_fact(ctx, *, search_term):
            """Search and remove global facts (admin only)"""
            await self._remove_global_fact_handler(ctx, search_term, is_admin)
        
        @self.bot.command(name='remove_global_fact_by_number')
        async def remove_global_fact_by_number(ctx, fact_number: int, *, search_term):
            """Remove a specific global fact by its number from the search results (admin only)"""
            await self._remove_global_fact_by_number_handler(ctx, fact_number, search_term, is_admin)
        
        @self.bot.command(name='personality', aliases=['profile', 'my_personality'])
        @bot_name_filter()
        async def show_personality(ctx, user: Optional[discord.Member] = None):
            """Show personality profile for yourself or another user"""
            await self._personality_handler(ctx, user, is_admin)
        
        @self.bot.command(name='sync_check')
        async def sync_check(ctx):
            """Check if your DM conversation is in sync with stored memory"""
            await self._sync_check_handler(ctx)
        
        @self.bot.command(name='my_memory')
        @bot_name_filter()
        async def user_memory_summary(ctx):
            """Show what the bot remembers about you"""
            await self._my_memory_handler(ctx)
        
        @self.bot.command(name='forget_me')
        @bot_name_filter()
        async def forget_user(ctx):
            """Delete all stored memories about you"""
            await self._forget_me_handler(ctx)
        
        @self.bot.command(name='import_history')
        async def import_history(ctx, limit: int = 100):
            """Import existing conversation history into ChromaDB"""
            await self._import_history_handler(ctx, limit)
        
        @self.bot.command(name='auto_facts')
        async def toggle_auto_facts(ctx, setting=None):
            """Toggle automatic fact extraction on/off"""
            await self._auto_facts_handler(ctx, setting)
        
        @self.bot.command(name='auto_extracted_facts')
        async def show_auto_extracted_facts(ctx):
            """Show facts that were automatically extracted"""
            await self._auto_extracted_facts_handler(ctx)
        
        @self.bot.command(name='extract_facts')
        async def extract_facts(ctx, *, message):
            """Test fact extraction on a message"""
            await self._extract_facts_handler(ctx, message)
    
    async def _add_fact_handler(self, ctx, fact):
        """Handle add fact command"""
        user_id = str(ctx.author.id)
        
        try:
            self.memory_manager.store_user_fact(
                user_id, 
                fact, 
                f"Added via !add_fact command in {ctx.channel.name if ctx.guild else 'DM'}"
            )
            await ctx.send(f"✅ **Fact added to memory:**\n> {fact}")
            logger.info(f"User {ctx.author.name} added fact: {fact[:50]}...")
        except ValidationError as e:
            logger.warning(f"Invalid input for add_fact: {e}")
            await ctx.send(f"❌ **Invalid input:** {str(e)}")
        except MemoryStorageError as e:
            logger.error(f"Error storing user fact: {e}")
            await ctx.send("❌ **Error:** Could not save the fact. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected error storing user fact: {e}")
            await ctx.send("❌ **Error:** An unexpected error occurred. Please try again later.")
    
    async def _remove_fact_handler(self, ctx, search_term):
        """Handle remove fact command"""
        user_id = str(ctx.author.id)
        
        try:
            # Search for facts containing the search term
            relevant_memories = self.memory_manager.retrieve_relevant_memories(user_id, search_term, limit=5)
            facts = [m for m in relevant_memories if m['metadata'].get('type') == 'user_fact']
            
            if not facts:
                await ctx.send(f"❌ **No facts found** containing: `{search_term}`")
                return
            
            if len(facts) == 1:
                # If only one fact found, delete it directly
                fact = facts[0]
                fact_text = fact['metadata'].get('fact', 'Unknown fact')
                
                # Delete the fact
                if self.memory_manager.delete_specific_memory(fact['id']):
                    await ctx.send(f"✅ **Fact removed:** {fact_text}")
                    logger.info(f"User {ctx.author.name} removed fact: {fact_text}")
                else:
                    await ctx.send("❌ **Error:** Failed to remove the fact.")
            else:
                # Multiple facts found, show them with numbered options
                embed = discord.Embed(
                    title="🔍 Multiple Facts Found",
                    description=f"Found {len(facts)} fact(s) containing `{search_term}`. Please use a more specific search term or select one by number:",
                    color=0xf39c12
                )
                
                for i, fact in enumerate(facts[:5], 1):  # Limit to 5 facts
                    fact_text = fact['metadata'].get('fact', 'Unknown fact')
                    timestamp = fact['metadata'].get('timestamp', 'Unknown time')
                    embed.add_field(
                        name=f"{i}. {fact_text[:100]}{'...' if len(fact_text) > 100 else ''}",
                        value=f"*Added: {timestamp[:10]}*",
                        inline=False
                    )
                
                embed.set_footer(text="Use `!remove_fact_by_number <number>` to remove a specific fact.")
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error removing user fact: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")
    
    async def _remove_fact_by_number_handler(self, ctx, fact_number, search_term):
        """Handle remove fact by number command"""
        user_id = str(ctx.author.id)
        
        try:
            # Search for facts containing the search term
            relevant_memories = self.memory_manager.retrieve_relevant_memories(user_id, search_term, limit=5)
            facts = [m for m in relevant_memories if m['metadata'].get('type') == 'user_fact']
            
            if not facts:
                await ctx.send(f"❌ **No facts found** containing: `{search_term}`")
                return
            
            if fact_number < 1 or fact_number > len(facts):
                await ctx.send(f"❌ **Invalid number.** Please choose a number between 1 and {len(facts)}.")
                return
            
            # Get the selected fact
            fact = facts[fact_number - 1]
            fact_text = fact['metadata'].get('fact', 'Unknown fact')
            
            # Delete the fact
            if self.memory_manager.delete_specific_memory(fact['id']):
                await ctx.send(f"✅ **Fact removed:** {fact_text}")
                logger.info(f"User {ctx.author.name} removed fact: {fact_text}")
            else:
                await ctx.send("❌ **Error:** Failed to remove the fact.")
                
        except ValueError:
            await ctx.send("❌ **Invalid number format.** Please provide a valid number.")
        except Exception as e:
            logger.error(f"Error removing user fact by number: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")
    
    async def _list_facts_handler(self, ctx):
        """Handle list facts command"""
        user_id = str(ctx.author.id)
        
        try:
            # Get all user facts using proper ChromaDB syntax
            results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": user_id}, {"type": "user_fact"}]},
                limit=50
            )
            
            if not results['documents']:
                await ctx.send("📝 **No facts stored** about you yet. Use `!add_fact` to add some!")
                return
            
            # Sort by timestamp
            facts_with_meta = list(zip(results['documents'], results['metadatas']))
            facts_with_meta.sort(key=lambda x: x[1].get('timestamp', ''), reverse=True)
            
            # Create embed
            embed = discord.Embed(
                title=f"📋 Facts about {ctx.author.display_name}",
                color=0x3498db
            )
            
            fact_list = []
            for i, (doc, metadata) in enumerate(facts_with_meta[:20], 1):  # Limit to 20
                fact = metadata.get('fact', doc)
                timestamp = metadata.get('timestamp', 'Unknown')[:10]
                fact_list.append(f"{i}. {fact} *(added {timestamp})*")
            
            embed.description = '\n'.join(fact_list) if fact_list else "No facts found."
            
            if len(facts_with_meta) > 20:
                embed.set_footer(text=f"Showing first 20 of {len(facts_with_meta)} facts")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing user facts: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")
    
    async def _add_global_fact_handler(self, ctx, fact, is_admin):
        """Handle add global fact command (admin only)"""
        if not is_admin(ctx):
            await ctx.send("❌ **Admin only:** This command requires administrator permissions.")
            return
        
        # SECURITY ENHANCEMENT: Validate admin command input
        from src.security.input_validator import validate_user_input, is_safe_admin_command
        
        user_id = str(ctx.author.id)
        if not is_safe_admin_command(fact, user_id):
            logger.error(f"SECURITY: Unsafe admin command attempted by {user_id}: add_global_fact")
            await ctx.send("❌ **Security Error:** This command contains potentially dangerous content and has been blocked.")
            return
        
        # Validate input content
        validation_result = validate_user_input(fact, user_id, "admin_command")
        if not validation_result['is_safe']:
            logger.error(f"SECURITY: Malicious admin command input from {user_id}: {validation_result['blocked_patterns']}")
            await ctx.send("❌ **Security Error:** Command input contains potentially malicious content.")
            return
        
        # Use sanitized input
        fact = validation_result['sanitized_content']
        
        try:
            admin_name = ctx.author.display_name
            self.memory_manager.store_global_fact(
                fact, 
                f"Added via !add_global_fact command by {admin_name} in {ctx.channel.name if ctx.guild else 'DM'}",
                added_by=admin_name
            )
            await ctx.send(f"✅ **Global fact added:**\n> {fact}")
            logger.info(f"Admin {admin_name} added global fact: {fact[:50]}...")
        except ValidationError as e:
            logger.warning(f"Invalid input for add_global_fact: {e}")
            await ctx.send(f"❌ **Invalid input:** {str(e)}")
        except MemoryStorageError as e:
            logger.error(f"Error storing global fact: {e}")
            await ctx.send("❌ **Error:** Could not save the global fact. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected error storing global fact: {e}")
            await ctx.send("❌ **Error:** An unexpected error occurred. Please try again later.")
    
    async def _list_global_facts_handler(self, ctx, is_admin):
        """Handle list global facts command (admin only)"""
        if not is_admin(ctx):
            await ctx.send("❌ **Admin only:** This command requires administrator permissions.")
            return
        
        try:
            global_facts = self.memory_manager.get_all_global_facts(limit=30)
            
            if not global_facts:
                await ctx.send("📝 **No global facts stored** yet. Use `!add_global_fact` to add some!")
                return
            
            # Create embed
            embed = discord.Embed(
                title="🌍 Global Facts",
                description="Facts about the world, relationships, and the bot",
                color=0xe74c3c
            )
            
            fact_list = []
            for i, fact_data in enumerate(global_facts[:20], 1):  # Limit to 20
                metadata = fact_data['metadata']
                fact = metadata.get('fact', fact_data['content'])
                timestamp = metadata.get('timestamp', 'Unknown')[:10]
                added_by = metadata.get('added_by', 'system')
                fact_list.append(f"{i}. {fact} *(added {timestamp} by {added_by})*")
            
            embed.description = '\n'.join(fact_list) if fact_list else "No global facts found."
            
            if len(global_facts) > 20:
                embed.set_footer(text=f"Showing first 20 of {len(global_facts)} global facts")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing global facts: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")
    
    async def _remove_global_fact_handler(self, ctx, search_term, is_admin):
        """Handle remove global fact command (admin only)"""
        if not is_admin(ctx):
            await ctx.send("❌ **Admin only:** This command requires administrator permissions.")
            return
        
        try:
            # Search for global facts containing the search term
            relevant_facts = self.memory_manager.retrieve_relevant_global_facts(search_term, limit=5)
            
            if not relevant_facts:
                await ctx.send(f"❌ **No global facts found** containing: `{search_term}`")
                return
            
            if len(relevant_facts) == 1:
                # If only one fact found, delete it directly
                fact = relevant_facts[0]
                fact_text = fact['metadata'].get('fact', 'Unknown fact')
                
                # Delete the fact
                if self.memory_manager.delete_global_fact(fact['id']):
                    await ctx.send(f"✅ **Global fact removed:** {fact_text}")
                    logger.info(f"Admin {ctx.author.display_name} removed global fact: {fact_text}")
                else:
                    await ctx.send("❌ **Error:** Failed to remove the global fact.")
            else:
                # Multiple facts found, show them with numbered options
                embed = discord.Embed(
                    title="🔍 Multiple Global Facts Found",
                    description=f"Found {len(relevant_facts)} global fact(s) containing `{search_term}`. Please use a more specific search term or select one by number:",
                    color=0xf39c12
                )
                
                for i, fact in enumerate(relevant_facts[:5], 1):  # Limit to 5 facts
                    fact_text = fact['metadata'].get('fact', 'Unknown fact')
                    timestamp = fact['metadata'].get('timestamp', 'Unknown time')
                    embed.add_field(
                        name=f"{i}. {fact_text[:100]}{'...' if len(fact_text) > 100 else ''}",
                        value=f"*Added: {timestamp[:10]}*",
                        inline=False
                    )
                
                embed.set_footer(text="Use `!remove_global_fact_by_number <number> <search_term>` to remove a specific global fact.")
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error removing global fact: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")
    
    async def _remove_global_fact_by_number_handler(self, ctx, fact_number, search_term, is_admin):
        """Handle remove global fact by number command (admin only)"""
        if not is_admin(ctx):
            await ctx.send("❌ **Admin only:** This command requires administrator permissions.")
            return
        
        try:
            # Search for global facts containing the search term
            relevant_facts = self.memory_manager.retrieve_relevant_global_facts(search_term, limit=5)
            
            if not relevant_facts:
                await ctx.send(f"❌ **No global facts found** containing: `{search_term}`")
                return
            
            if fact_number < 1 or fact_number > len(relevant_facts):
                await ctx.send(f"❌ **Invalid number.** Please choose a number between 1 and {len(relevant_facts)}.")
                return
            
            # Get the selected fact
            fact = relevant_facts[fact_number - 1]
            fact_text = fact['metadata'].get('fact', 'Unknown fact')
            
            # Delete the fact
            if self.memory_manager.delete_global_fact(fact['id']):
                await ctx.send(f"✅ **Global fact removed:** {fact_text}")
                logger.info(f"Admin {ctx.author.display_name} removed global fact: {fact_text}")
            else:
                await ctx.send("❌ **Error:** Failed to remove the global fact.")
                
        except ValueError:
            await ctx.send("❌ **Invalid number format.** Please provide a valid number.")
        except Exception as e:
            logger.error(f"Error removing global fact by number: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")
    
    async def _personality_handler(self, ctx, user, is_admin):
        """Handle personality command"""
        # Determine target user
        target_user = user if user and is_admin(ctx) else ctx.author
        user_id = str(target_user.id)
        
        # Check if personality profiling is enabled
        if not self.personality_profiler:
            await ctx.send("🧠 **Personality profiling is not enabled** in this bot configuration.")
            return
        
        try:
            embed = discord.Embed(
                title=f"🧠 Personality Profile: {target_user.display_name}",
                color=0x9b59b6,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Try to get personality profile from graph database first
            personality_data = None
            if self.graph_personality_manager:
                try:
                    personality_data = await self.graph_personality_manager.get_personality_profile(user_id)
                    if personality_data:
                        embed.add_field(
                            name="📊 Data Source",
                            value="Graph Database (Persistent)",
                            inline=True
                        )
                except Exception as e:
                    logger.debug(f"Could not retrieve graph personality data: {e}")
            
            if personality_data:
                # Display graph database personality data
                embed.add_field(
                    name="🎭 Big Five Traits",
                    value=f"**Openness:** {personality_data.get('openness', 0):.2f}\n"
                          f"**Conscientiousness:** {personality_data.get('conscientiousness', 0):.2f}\n"
                          f"**Extraversion:** {personality_data.get('extraversion', 0):.2f}\n"
                          f"**Agreeableness:** {personality_data.get('agreeableness', 0):.2f}\n"
                          f"**Neuroticism:** {personality_data.get('neuroticism', 0):.2f}",
                    inline=True
                )
                
                embed.add_field(
                    name="💬 Communication Style",
                    value=f"**Style:** {personality_data.get('communication_style', 'unknown').title()}\n"
                          f"**Directness:** {personality_data.get('directness_style', 'unknown').title()}\n"
                          f"**Confidence:** {personality_data.get('confidence_level', 0):.2f}",
                    inline=True
                )
                
                embed.add_field(
                    name="🧭 Decision Making",
                    value=f"**Style:** {personality_data.get('decision_style', 'unknown').title()}\n"
                          f"**Detail Focus:** {personality_data.get('detail_orientation', 0):.2f}\n"
                          f"**Social Engagement:** {personality_data.get('social_engagement', 0):.2f}",
                    inline=True
                )
                
                embed.add_field(
                    name="📈 Analysis Meta",
                    value=f"**Messages Analyzed:** {personality_data.get('total_messages_analyzed', 0)}\n"
                          f"**Confidence:** {personality_data.get('confidence_interval', 0):.2f}\n"
                          f"**Last Updated:** {personality_data.get('last_updated', 'Unknown')[:10]}",
                    inline=True
                )
            else:
                # Try real-time analysis with recent messages
                embed.add_field(
                    name="📊 Data Source",
                    value="Real-time Analysis",
                    inline=True
                )
                
                try:
                    # Get recent messages for analysis
                    recent_messages = []
                    if ctx.guild is None:
                        # DM context - get messages from this channel
                        async for msg in ctx.channel.history(limit=20):
                            if msg.author == target_user and not msg.content.startswith('!'):
                                recent_messages.append(msg.content)
                    else:
                        # Server context - get recent stored conversations
                        try:
                            message_context = self.memory_manager.classify_discord_context(ctx.message)
                            recent_context = await self.safe_memory_manager.get_recent_conversations(
                                user_id, limit=15, context=message_context
                            )
                            if recent_context and hasattr(recent_context, 'conversations'):
                                for conv in recent_context.conversations:
                                    if hasattr(conv, 'user_message') and conv.user_message:
                                        recent_messages.append(conv.user_message)
                        except Exception as e:
                            logger.debug(f"Could not retrieve recent conversations for personality display: {e}")
                    
                    if len(recent_messages) >= 3:
                        # Perform real-time analysis
                        metrics = self.personality_profiler.analyze_personality(recent_messages, user_id)
                        summary = self.personality_profiler.get_personality_summary(metrics)
                        
                        embed.add_field(
                            name="🎭 Big Five Traits",
                            value=f"**Openness:** {summary['personality_traits']['openness']}\n"
                                  f"**Conscientiousness:** {summary['personality_traits']['conscientiousness']}\n"
                                  f"**Extraversion:** {summary['personality_traits']['extraversion']}\n"
                                  f"**Agreeableness:** {summary['personality_traits']['agreeableness']}\n"
                                  f"**Neuroticism:** {summary['personality_traits']['neuroticism']}",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="💬 Communication Style",
                            value=f"**Style:** {summary['communication_style']['primary'].title()}\n"
                                  f"**Directness:** {summary['communication_style']['directness'].title()}\n"
                                  f"**Confidence:** {summary['communication_style']['confidence_level']}",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="🧭 Behavioral Patterns",
                            value=f"**Decision Style:** {summary['behavioral_patterns']['decision_style'].title()}\n"
                                  f"**Emotional Expression:** {summary['behavioral_patterns']['emotional_expressiveness']}\n"
                                  f"**Social Engagement:** {summary['behavioral_patterns']['social_engagement']}",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="📈 Analysis Details",
                            value=f"**Messages Analyzed:** {summary['analysis_meta']['messages_analyzed']}\n"
                                  f"**Confidence:** {summary['analysis_meta']['confidence']:.2f}\n"
                                  f"**Analysis Type:** Real-time",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name="⚠️ Insufficient Data",
                            value=f"Need at least 3 messages for personality analysis.\n"
                                  f"Currently have: {len(recent_messages)} messages\n"
                                  f"Chat with the bot more for better analysis!",
                            inline=False
                        )
                except Exception as e:
                    logger.error(f"Error performing real-time personality analysis: {e}")
                    embed.add_field(
                        name="❌ Analysis Error",
                        value="Could not perform personality analysis at this time.",
                        inline=False
                    )
            
            embed.set_footer(text="Personality profiles improve with more interactions • AI-powered analysis")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing personality profile: {e}")
            await ctx.send(f"❌ **Error:** Could not retrieve personality profile.")
    
    async def _sync_check_handler(self, ctx):
        """Handle sync check command"""
        if ctx.guild is not None:
            await ctx.send("❌ **This command only works in DMs** to check conversation sync.")
            return
        
        user_id = str(ctx.author.id)
        
        try:
            # Get recent Discord messages
            discord_messages = [msg async for msg in ctx.channel.history(limit=20)]
            discord_messages.reverse()  # Chronological order
            
            # Get stored conversations from ChromaDB (excluding facts)
            conversation_results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": user_id}, {"type": {"$ne": "user_fact"}}]},
                limit=50
            )
            
            # Get stored facts separately
            fact_results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": user_id}, {"type": "user_fact"}]},
                limit=50
            )
            
            # Process conversations
            stored_conversations = []
            if conversation_results['documents']:
                for i, doc in enumerate(conversation_results['documents']):
                    metadata = conversation_results['metadatas'][i]
                    stored_conversations.append({
                        'user_message': metadata.get('user_message', ''),
                        'bot_response': metadata.get('bot_response', ''),
                        'timestamp': metadata.get('timestamp', '')
                    })
            
            # Sort stored conversations by timestamp
            stored_conversations.sort(key=lambda x: x['timestamp'])
            
            # Analysis - exclude bot commands from user messages
            discord_user_messages = [msg.content for msg in discord_messages if msg.author != self.bot.user and not msg.content.startswith('!')]
            discord_bot_messages = [msg.content for msg in discord_messages if msg.author == self.bot.user]
            
            stored_user_messages = [conv['user_message'] for conv in stored_conversations]
            stored_bot_messages = [conv['bot_response'] for conv in stored_conversations]
            
            # Create sync report
            embed = discord.Embed(
                title="🔄 Conversation Sync Status",
                color=0x2ecc71
            )
            
            embed.add_field(
                name="📱 Discord Messages",
                value=f"User messages: {len(discord_user_messages)}\nBot messages: {len(discord_bot_messages)}",
                inline=True
            )
            
            embed.add_field(
                name="💾 Stored in Memory",
                value=f"Conversations: {len(stored_conversations)}\nFacts: {len(fact_results['documents']) if fact_results['documents'] else 0}",
                inline=True
            )
            
            # Check for recent missing conversations
            recent_discord = discord_user_messages[-5:] if discord_user_messages else []
            recent_stored = stored_user_messages[-5:] if stored_user_messages else []
            
            missing_from_memory = []
            for msg in recent_discord:
                if msg not in stored_user_messages:
                    missing_from_memory.append(msg[:50] + "..." if len(msg) > 50 else msg)
            
            if missing_from_memory:
                embed.add_field(
                    name="⚠️ Possibly Missing from Memory",
                    value="\n".join([f"• {msg}" for msg in missing_from_memory[:3]]),
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ Sync Status",
                    value="Recent conversations appear to be stored correctly",
                    inline=False
                )
            
            embed.set_footer(text="Use !import_history to sync older conversations")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")
    
    async def _my_memory_handler(self, ctx):
        """Handle my memory command"""
        user_id = str(ctx.author.id)
        
        try:
            # Get facts and conversations separately for accurate counts
            fact_results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": user_id}, {"type": "user_fact"}]},
                limit=50
            )
            
            conversation_results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": user_id}, {"type": {"$ne": "user_fact"}}]},
                limit=50
            )
            
            # Check if any data exists
            if not fact_results['documents'] and not conversation_results['documents']:
                embed = discord.Embed(
                    title=f"🧠 Memory about {ctx.author.display_name}",
                    description="No memories stored yet. Start chatting to build up our conversation history!",
                    color=0x95a5a6
                )
                await ctx.send(embed=embed)
                return
            
            # Process facts
            facts = []
            if fact_results['documents']:
                for i, doc in enumerate(fact_results['documents']):
                    metadata = fact_results['metadatas'][i]
                    facts.append({
                        'fact': metadata.get('fact', doc),
                        'timestamp': metadata.get('timestamp', '')
                    })
            
            # Process conversations
            conversations = []
            if conversation_results['documents']:
                for i, doc in enumerate(conversation_results['documents']):
                    metadata = conversation_results['metadatas'][i]
                    conversations.append({
                        'user_message': metadata.get('user_message', ''),
                        'timestamp': metadata.get('timestamp', '')
                    })
            
            # Sort by timestamp
            facts.sort(key=lambda x: x['timestamp'], reverse=True)
            conversations.sort(key=lambda x: x['timestamp'], reverse=True)
            
            embed = discord.Embed(
                title=f"🧠 Memory about {ctx.author.display_name}",
                color=0x3498db
            )
            
            # Add facts section
            if facts:
                fact_list = []
                for fact in facts[:5]:  # Show top 5 facts
                    fact_text = fact['fact'][:80] + "..." if len(fact['fact']) > 80 else fact['fact']
                    fact_list.append(f"• {fact_text}")
                
                embed.add_field(
                    name="📝 Facts I Remember",
                    value='\n'.join(fact_list),
                    inline=False
                )
            
            # Add recent conversations section
            if conversations:
                conv_list = []
                for conv in conversations[:3]:  # Show top 3 recent topics
                    msg = conv['user_message'][:60] + "..." if len(conv['user_message']) > 60 else conv['user_message']
                    conv_list.append(f"• {msg}")
                
                embed.add_field(
                    name="💬 Recent Topics",
                    value='\n'.join(conv_list),
                    inline=False
                )
            
            embed.add_field(
                name="📊 Memory Stats",
                value=f"Total facts: {len(facts)}\nTotal conversations: {len(conversations)}",
                inline=True
            )
            
            embed.set_footer(text="Use !add_fact, !list_facts, or !sync_check for more options")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting user memory summary: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")
    
    async def _forget_me_handler(self, ctx):
        """Handle forget me command"""
        user_id = str(ctx.author.id)
        logger.debug(f"User {ctx.author.name} initiated forget_me command")
        
        # Confirmation step
        embed = discord.Embed(
            title="⚠️ Confirm Data Deletion",
            description="This will delete **ALL** stored information about you including:\n• Conversation history\n• Personal facts\n• All memories\n\n**This cannot be undone!**",
            color=0xe74c3c
        )
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel (30 seconds)")
        
        message = await ctx.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        logger.debug(f"Added reactions to message {message.id}")
        
        def check(reaction, user):
            logger.debug(f"Reaction check: user={user.name}, emoji={reaction.emoji}, message_id={reaction.message.id}, expected_id={message.id}")
            return (user == ctx.author and 
                   str(reaction.emoji) in ['✅', '❌'] and 
                   reaction.message.id == message.id)
        
        try:
            logger.debug("Waiting for reaction...")
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            logger.debug(f"Received reaction: {reaction.emoji} from {user.name}")
            
            if str(reaction.emoji) == '✅':
                try:
                    logger.debug(f"User confirmed deletion, proceeding to delete memories for {user_id}")
                    deleted_count = self.memory_manager.delete_user_memories(user_id)
                    await ctx.send(f"🗑️ **Forgotten!** Deleted {deleted_count} memories about you.")
                    logger.info(f"User {ctx.author.name} deleted all their memories ({deleted_count} items)")
                except Exception as e:
                    logger.error(f"Error deleting user memories: {e}")
                    await ctx.send(f"❌ **Error deleting data:** {str(e)}")
            else:
                logger.debug("User cancelled deletion")
                await ctx.send("🚫 **Cancelled** - Your data has not been deleted.")
                
        except asyncio.TimeoutError:
            logger.debug("Reaction timeout occurred")
            await ctx.send("⏰ **Timeout** - Data deletion cancelled.")
    
    async def _import_history_handler(self, ctx, limit):
        """Handle import history command"""
        if ctx.guild is not None:
            await ctx.send("❌ **This command only works in DMs** to import your conversation history.")
            return
        
        user_id = str(ctx.author.id)
        
        try:
            await ctx.send(f"🔄 **Importing** last {limit} messages from this conversation...")
            
            messages = [msg async for msg in ctx.channel.history(limit=limit)]
            imported = 0
            
            # Process messages in chronological order
            for i in range(len(messages) - 1, 0, -1):
                current_msg = messages[i]
                next_msg = messages[i-1]
                
                # Look for user message followed by bot response
                if current_msg.author != self.bot.user and next_msg.author == self.bot.user:
                    # Skip bot commands - don't import them to memory
                    if current_msg.content.startswith('!'):
                        logger.debug(f"Skipping command from import: {current_msg.content[:50]}...")
                        continue
                    # Skip empty messages to avoid validation errors
                    if not current_msg.content or not current_msg.content.strip():
                        logger.debug(f"Skipping empty user message from {current_msg.author}")
                        continue
                    if not next_msg.content or not next_msg.content.strip():
                        logger.debug(f"Skipping empty bot response")
                        continue
                        
                    self.memory_manager.store_conversation(
                        user_id, 
                        extract_text_for_memory_storage(current_msg.content, current_msg.attachments), 
                        next_msg.content
                    )
                    imported += 1
            
            await ctx.send(f"✅ **Import complete!** Added {imported} conversation pairs to memory.\n\nUse `!sync_check` to verify the import.")
            logger.info(f"Imported {imported} conversation pairs for user {ctx.author.name}")
            
        except Exception as e:
            logger.error(f"Error importing history: {e}")
            await ctx.send(f"❌ **Import failed:** {str(e)}")
    
    async def _auto_facts_handler(self, ctx, setting):
        """Handle auto facts command"""
        user_id = str(ctx.author.id)
        
        if setting is None:
            # Show current status
            status = "enabled" if self.memory_manager.enable_auto_facts else "disabled"
            embed = discord.Embed(
                title="🤖 Automatic Fact Extraction",
                description=f"Automatic fact extraction is currently **{status}**",
                color=0x3498db if self.memory_manager.enable_auto_facts else 0x95a5a6
            )
            embed.add_field(
                name="ℹ️ What is this?",
                value="When enabled, the bot automatically identifies and remembers personal facts about you from your messages. Global facts can only be managed by admins.",
                inline=False
            )
            embed.add_field(
                name="🔧 Usage", 
                value="`!auto_facts on` - Enable automatic user fact extraction\n`!auto_facts off` - Disable automatic user fact extraction",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        if setting.lower() in ['on', 'enable', 'true', '1']:
            self.memory_manager.enable_auto_facts = True
            if not self.memory_manager.fact_extractor:
                from src.utils.fact_extractor import FactExtractor
                self.memory_manager.fact_extractor = FactExtractor()
            
            await ctx.send("✅ **Automatic user fact extraction enabled!**\nThe bot will now automatically identify and remember personal facts from your messages. Global facts are managed by admins only.")
            logger.info(f"User {ctx.author.name} enabled automatic fact extraction")
            
        elif setting.lower() in ['off', 'disable', 'false', '0']:
            self.memory_manager.enable_auto_facts = False
            await ctx.send("🔕 **Automatic user fact extraction disabled.**\nThe bot will only remember personal facts you explicitly add with `!add_fact`. Global facts are managed by admins only.")
            logger.info(f"User {ctx.author.name} disabled automatic fact extraction")
            
        else:
            await ctx.send("❌ Invalid setting. Use `on` or `off`.")
    
    async def _auto_extracted_facts_handler(self, ctx):
        """Handle auto extracted facts command"""
        user_id = str(ctx.author.id)
        
        try:
            # Get auto-extracted facts
            results = self.memory_manager.collection.get(
                where={"$and": [
                    {"user_id": user_id}, 
                    {"type": "user_fact"},
                    {"extraction_method": "automatic"}
                ]},
                limit=50
            )
            
            if not results['documents']:
                embed = discord.Embed(
                    title="🤖 Auto-Extracted Facts",
                    description="No automatically extracted facts found. Either:\n• Automatic fact extraction is disabled\n• Not enough conversation data for extraction\n• No extractable facts detected yet",
                    color=0x95a5a6
                )
                embed.add_field(
                    name="💡 Tips",
                    value="• Use `!auto_facts on` to enable automatic extraction\n• Chat more naturally for better fact detection\n• Use `!add_fact` to manually add important facts",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
            
            # Sort by confidence score (if available) and timestamp
            facts_with_meta = list(zip(results['documents'], results['metadatas']))
            facts_with_meta.sort(key=lambda x: (
                x[1].get('confidence_score', 0.5),  # Sort by confidence
                x[1].get('timestamp', '')           # Then by timestamp
            ), reverse=True)
            
            embed = discord.Embed(
                title=f"🤖 Auto-Extracted Facts for {ctx.author.display_name}",
                description=f"Found {len(facts_with_meta)} automatically detected facts:",
                color=0x3498db
            )
            
            # Display facts with confidence scores
            fact_list = []
            for i, (doc, metadata) in enumerate(facts_with_meta[:15], 1):  # Limit to 15
                fact_text = metadata.get('fact', doc)
                confidence = metadata.get('confidence_score', 0.5)
                timestamp = metadata.get('timestamp', 'Unknown')[:10]
                
                # Format with confidence indicator
                confidence_emoji = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🟠"
                fact_list.append(f"{confidence_emoji} {fact_text} *(extracted {timestamp}, confidence: {confidence:.2f})*")
            
            embed.description = f"Found {len(facts_with_meta)} automatically detected facts:\n\n" + '\n\n'.join(fact_list)
            
            if len(facts_with_meta) > 15:
                embed.set_footer(text=f"Showing top 15 of {len(facts_with_meta)} auto-extracted facts")
            
            embed.add_field(
                name="📊 Confidence Legend",
                value="🟢 High (≥80%) | 🟡 Medium (60-80%) | 🟠 Low (<60%)",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing auto-extracted facts: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")
    
    async def _extract_facts_handler(self, ctx, message):
        """Handle extract facts command"""
        user_id = str(ctx.author.id)
        
        if not self.memory_manager.fact_extractor:
            await ctx.send("❌ **Fact extraction is not enabled.** Use `!auto_facts on` to enable it first.")
            return
        
        try:
            # Test fact extraction on the provided message
            extracted_facts = self.memory_manager.fact_extractor.extract_personal_facts(message, user_id)
            
            embed = discord.Embed(
                title="🔍 Fact Extraction Test",
                description=f"**Input message:**\n> {message[:200]}{'...' if len(message) > 200 else ''}",
                color=0x3498db
            )
            
            if extracted_facts:
                fact_list = []
                for i, fact_data in enumerate(extracted_facts, 1):
                    fact = fact_data.get('fact', 'Unknown')
                    confidence = fact_data.get('confidence', 0.0)
                    confidence_emoji = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🟠"
                    fact_list.append(f"{confidence_emoji} {fact} *(confidence: {confidence:.2f})*")
                
                embed.add_field(
                    name=f"📝 Extracted Facts ({len(extracted_facts)})",
                    value='\n\n'.join(fact_list),
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Note",
                    value="These facts were extracted for testing only and **were not saved** to memory. Use the regular chat to have facts automatically saved.",
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ No Facts Extracted",
                    value="No personal facts detected in this message. Try messages that contain personal information like:\n• Hobbies or interests\n• Personal preferences\n• Facts about yourself\n• Life experiences",
                    inline=False
                )
            
            embed.add_field(
                name="📊 Confidence Legend",
                value="🟢 High (≥80%) | 🟡 Medium (60-80%) | 🟠 Low (<60%)",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error testing fact extraction: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")