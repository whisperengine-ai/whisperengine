"""
Memory command handlers for Discord bot
Includes fact management, conversation sync, memory viewing, and data deletion
"""

import logging
from datetime import UTC, datetime

import discord

from src.utils.helpers import extract_text_for_memory_storage
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MemoryCommandHandlers:
    """Handles memory-related commands"""

    def __init__(
        self,
        bot,
        memory_manager,
        safe_memory_manager,
        context_memory_manager,
        graph_personality_manager,
        personality_profiler,
        dynamic_personality_profiler=None,
    ):
        self.bot = bot
        self.memory_manager = memory_manager
        self.safe_memory_manager = safe_memory_manager
        self.context_memory_manager = context_memory_manager
        self.graph_personality_manager = graph_personality_manager
        self.personality_profiler = personality_profiler
        self.dynamic_personality_profiler = dynamic_personality_profiler

    def register_commands(self, is_admin, bot_name_filter=None):
        """Register all memory commands"""

        # Default to no-op filter if none provided
        if bot_name_filter is None:

            def bot_name_filter():
                return lambda func: func

        @self.bot.command(name="list_facts", aliases=["facts"])
        @bot_name_filter()
        async def list_facts(ctx):
            """List all facts the bot knows about you"""
            await self._list_facts_handler(ctx)

        @self.bot.command(name="list_global_facts")
        async def list_global_facts(ctx):
            """List all global facts (admin only)"""
            await self._list_global_facts_handler(ctx, is_admin)

        @self.bot.command(name="personality", aliases=["profile", "my_personality"])
        @bot_name_filter()
        async def show_personality(ctx, user: discord.Member | None = None):
            """Show personality profile for yourself or another user"""
            await self._personality_handler(ctx, user, is_admin)

        @self.bot.command(
            name="dynamic_personality", aliases=["dynamic_profile", "adaptive_profile"]
        )
        @bot_name_filter()
        async def show_dynamic_personality(ctx, user: discord.Member | None = None):
            """Show dynamic personality profile with adaptive insights"""
            await self._dynamic_personality_handler(ctx, user, is_admin)

        @self.bot.command(name="sync_check")
        async def sync_check(ctx):
            """Check if your DM conversation is in sync with stored memory"""
            await self._sync_check_handler(ctx)

        @self.bot.command(name="my_memory")
        @bot_name_filter()
        async def user_memory_summary(ctx):
            """Show what the bot remembers about you"""
            await self._my_memory_handler(ctx)

        @self.bot.command(name="forget_me")
        @bot_name_filter()
        async def forget_user(ctx):
            """Delete all stored memories about you"""
            await self._forget_me_handler(ctx)

        @self.bot.command(name="import_history")
        async def import_history(ctx, limit: int = 100):
            """Import existing conversation history into ChromaDB"""
            await self._import_history_handler(ctx, limit)

        @self.bot.command(name="auto_facts")
        async def toggle_auto_facts(ctx, setting=None):
            """Toggle automatic fact extraction on/off"""
            await self._auto_facts_handler(ctx, setting)

        @self.bot.command(name="auto_extracted_facts")
        async def show_auto_extracted_facts(ctx):
            """Show facts that were automatically extracted"""
            await self._auto_extracted_facts_handler(ctx)

        @self.bot.command(name="extract_facts")
        async def extract_facts(ctx, *, message):
            """Test fact extraction on a message"""
            await self._extract_facts_handler(ctx, message)

    @handle_errors(
        category=ErrorCategory.MEMORY_SYSTEM,
        severity=ErrorSeverity.MEDIUM,
        operation="list_facts_handler"
    )
    async def _list_facts_handler(self, ctx):
        """Handle list facts command - showcasing personality-driven AI insights"""
        user_id = str(ctx.author.id)

        try:
            # Get modern personality facts (primary data source)
            personality_facts = []
            try:
                personality_facts = self.memory_manager.retrieve_personality_facts(
                    user_id=user_id, limit=30
                )
                logger.debug(
                    f"Retrieved {len(personality_facts)} personality facts for user {user_id}"
                )
            except Exception as e:
                logger.debug(f"Could not retrieve personality facts: {e}")

            # Get legacy facts for comparison/completeness
            legacy_facts = []
            try:
                # Fix ChromaDB method signature - using updated API
                results = self.memory_manager.collection.get(
                    where={"$and": [{"user_id": str(user_id)}, {"type": "user_fact"}]},
                    limit=10
                )

                if results["documents"]:
                    facts_with_meta = list(
                        zip(results["documents"], results["metadatas"], strict=False)
                    )
                    facts_with_meta.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)

                    for doc, metadata in facts_with_meta:
                        legacy_facts.append(
                            {
                                "content": metadata.get("fact", doc),
                                "timestamp": metadata.get("timestamp", "Unknown"),
                                "type": "legacy",
                            }
                        )
            except Exception as e:
                logger.debug(f"Could not retrieve legacy facts: {e}")

            total_facts = len(personality_facts) + len(legacy_facts)

            if total_facts == 0:
                embed = discord.Embed(
                    title=f"🧠 AI Memory: {ctx.author.display_name}",
                    description="No personality insights discovered yet!",
                    color=0x3498DB,
                )
                embed.add_field(
                    name="✨ Get Started",
                    value="� **Chat more** to build your personality profile\n"
                    "🎯 **Share interests** and preferences\n"
                    "🤖 **AI learns** your communication style automatically\n"
                    "📊 **Facts emerge** from natural conversation",
                    inline=False,
                )
                embed.set_footer(
                    text="Personality facts are extracted automatically • No manual entry needed"
                )
                await ctx.send(embed=embed)
                return

            # Create personality-focused embed
            embed = discord.Embed(
                title=f"🧠 AI Personality Profile: {ctx.author.display_name}",
                description=f"Discovered **{len(personality_facts)} personality insights** + {len(legacy_facts)} legacy facts",
                color=0x9B59B6,
                timestamp=datetime.now(UTC),
            )

            # Group personality facts by type with relevance sorting
            if personality_facts:
                from collections import defaultdict

                facts_by_type = defaultdict(list)

                for fact in personality_facts:
                    fact_type = fact.get("fact_type", "general")
                    facts_by_type[fact_type].append(fact)

                # Show top categories by highest relevance
                categories_by_relevance = []
                for fact_type, type_facts in facts_by_type.items():
                    max_relevance = max([f.get("relevance_score", 0) for f in type_facts])
                    categories_by_relevance.append((fact_type, type_facts, max_relevance))

                categories_by_relevance.sort(key=lambda x: x[2], reverse=True)

                # Display top 5 personality fact categories
                for fact_type, type_facts, max_relevance in categories_by_relevance[:5]:
                    type_display = fact_type.replace("_", " ").title()
                    type_emoji = self._get_personality_type_emoji(fact_type)

                    # Show top 3 facts from this category
                    sorted_facts = sorted(
                        type_facts, key=lambda x: x.get("relevance_score", 0), reverse=True
                    )

                    category_text = ""
                    for _i, fact in enumerate(sorted_facts[:3], 1):
                        content = fact.get("content", "Unknown")[:70]
                        relevance = fact.get("relevance_score", 0.0)
                        privacy_tier = fact.get("privacy_tier", "unknown")

                        # Relevance indicators
                        if relevance >= 0.8:
                            relevance_icon = "🔥"
                        elif relevance >= 0.6:
                            relevance_icon = "⭐"
                        elif relevance >= 0.4:
                            relevance_icon = "💡"
                        else:
                            relevance_icon = "📝"

                        # Privacy indicators
                        privacy_icon = (
                            "🔒"
                            if privacy_tier == "high"
                            else "👁️" if privacy_tier == "medium" else "📢"
                        )

                        category_text += (
                            f"{relevance_icon} {content}... ({relevance:.2f}) {privacy_icon}\n"
                        )

                    # Add category summary
                    if len(type_facts) > 3:
                        category_text += f"*...and {len(type_facts) - 3} more insights*\n"

                    embed.add_field(
                        name=f"{type_emoji} {type_display} ({len(type_facts)})",
                        value=category_text[:1024] or "No content",
                        inline=False,
                    )

                # Add personality insights summary
                high_relevance = len(
                    [f for f in personality_facts if f.get("relevance_score", 0) >= 0.7]
                )
                medium_relevance = len(
                    [f for f in personality_facts if 0.4 <= f.get("relevance_score", 0) < 0.7]
                )
                low_relevance = len(personality_facts) - high_relevance - medium_relevance

                insights_summary = f"🔥 **High Impact:** {high_relevance} insights\n"
                insights_summary += f"⭐ **Medium Impact:** {medium_relevance} insights\n"
                insights_summary += f"💡 **Supporting:** {low_relevance} insights"

                embed.add_field(
                    name="📊 Insight Quality Distribution", value=insights_summary, inline=True
                )

                # Privacy distribution
                privacy_counts = defaultdict(int)
                for fact in personality_facts:
                    tier = fact.get("privacy_tier", "unknown")
                    privacy_counts[tier] += 1

                privacy_summary = ""
                if privacy_counts["high"]:
                    privacy_summary += f"🔒 **Private:** {privacy_counts['high']}\n"
                if privacy_counts["medium"]:
                    privacy_summary += f"👁️ **Semi-Private:** {privacy_counts['medium']}\n"
                if privacy_counts["low"]:
                    privacy_summary += f"📢 **Public:** {privacy_counts['low']}\n"

                if privacy_summary:
                    embed.add_field(
                        name="🛡️ Privacy Distribution", value=privacy_summary, inline=True
                    )

                # Show how facts are used in AI
                embed.add_field(
                    name="🤖 AI Integration",
                    value="💬 **Conversation Context:** Active\n"
                    "🎯 **Response Personalization:** Enabled\n"
                    "🧠 **Memory Retrieval:** Semantic search\n"
                    "⚙️ **Behavior Adaptation:** Real-time",
                    inline=True,
                )

            # Show legacy facts if available (smaller section)
            if legacy_facts:
                legacy_text = ""
                for fact in legacy_facts[:3]:
                    content = fact["content"][:50]
                    timestamp = (
                        fact["timestamp"][:10] if fact["timestamp"] != "Unknown" else "Unknown"
                    )
                    legacy_text += f"📝 {content}... *(legacy, {timestamp})*\n"

                if len(legacy_facts) > 3:
                    legacy_text += f"*...and {len(legacy_facts) - 3} more legacy facts*\n"

                embed.add_field(
                    name=f"📚 Legacy Facts ({len(legacy_facts)})",
                    value=legacy_text[:1024] if legacy_text else "None",
                    inline=False,
                )

            # Advanced commands hint
            if len(personality_facts) > 10:
                embed.add_field(
                    name="🔍 Advanced Commands",
                    value="• `!personality` - Full dynamic profile\n"
                    "• `!personality_types` - Filter by fact type\n"
                    "• `!memory_search <query>` - Find specific insights",
                    inline=False,
                )

            # Footer with system info
            if total_facts > 15:
                embed.set_footer(
                    text=f"Showing highlights from {total_facts} total facts • Personality AI system active"
                )
            else:
                embed.set_footer(
                    text=f"Personality AI has discovered {total_facts} facts about you • System learning from conversations"
                )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error displaying personality facts: {e}")
            await ctx.send(f"❌ **Error:** Could not retrieve your personality profile: {str(e)}")

    async def _list_global_facts_handler(self, ctx, is_admin):
        """Handle list global facts command (admin only) - read-only display"""
        if not is_admin(ctx):
            await ctx.send("❌ **Admin only:** This command requires administrator permissions.")
            return

        try:
            global_facts = self.memory_manager.get_all_global_facts(limit=30)

            if not global_facts:
                await ctx.send("📝 **No global facts found** in the system.")
                return

            # Create embed
            embed = discord.Embed(
                title="🌍 Global Facts",
                description="Facts about the world, relationships, and system knowledge",
                color=0xE74C3C,
            )

            fact_list = []
            for i, fact_data in enumerate(global_facts[:20], 1):  # Limit to 20
                metadata = fact_data["metadata"]
                fact = metadata.get("fact", fact_data["content"])
                timestamp = metadata.get("timestamp", "Unknown")[:10]
                source = metadata.get("extraction_method", "system")
                fact_list.append(f"{i}. {fact} *(source: {source}, {timestamp})*")

            embed.description = "\n".join(fact_list) if fact_list else "No global facts found."

            if len(global_facts) > 20:
                embed.set_footer(
                    text=f"Showing first 20 of {len(global_facts)} global facts (read-only)"
                )
            else:
                embed.set_footer(text="Global facts display (read-only)")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error listing global facts: {e}")
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
                color=0x9B59B6,
                timestamp=datetime.now(UTC),
            )

            # Try to get personality profile from graph database first
            personality_data = None
            if self.graph_personality_manager:
                try:
                    personality_data = await self.graph_personality_manager.get_personality_profile(
                        user_id
                    )
                    if personality_data:
                        embed.add_field(
                            name="📊 Data Source", value="Graph Database (Persistent)", inline=True
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
                    inline=True,
                )

                embed.add_field(
                    name="💬 Communication Style",
                    value=f"**Style:** {personality_data.get('communication_style', 'unknown').title()}\n"
                    f"**Directness:** {personality_data.get('directness_style', 'unknown').title()}\n"
                    f"**Confidence:** {personality_data.get('confidence_level', 0):.2f}",
                    inline=True,
                )

                embed.add_field(
                    name="🧭 Decision Making",
                    value=f"**Style:** {personality_data.get('decision_style', 'unknown').title()}\n"
                    f"**Detail Focus:** {personality_data.get('detail_orientation', 0):.2f}\n"
                    f"**Social Engagement:** {personality_data.get('social_engagement', 0):.2f}",
                    inline=True,
                )

                embed.add_field(
                    name="📈 Analysis Meta",
                    value=f"**Messages Analyzed:** {personality_data.get('total_messages_analyzed', 0)}\n"
                    f"**Confidence:** {personality_data.get('confidence_interval', 0):.2f}\n"
                    f"**Last Updated:** {personality_data.get('last_updated', 'Unknown')[:10]}",
                    inline=True,
                )
            else:
                # Try real-time analysis with recent messages
                embed.add_field(name="📊 Data Source", value="Real-time Analysis", inline=True)

                try:
                    # Get recent messages for analysis - CROSS-CONTEXT for personality (user-scoped, not context-scoped)
                    recent_messages = []

                    # For personality analysis, we need ALL user messages across contexts, not just current context
                    try:
                        # Get messages from base memory manager without context filtering for personality analysis
                        base_memory_manager = getattr(
                            self.safe_memory_manager, "base_memory_manager", self.memory_manager
                        )

                        if base_memory_manager and hasattr(
                            base_memory_manager, "retrieve_relevant_memories"
                        ):
                            # Retrieve user's conversation history across ALL contexts for personality profiling
                            # Note: retrieve_relevant_memories is automatically enhanced via memory patch system
                            cross_context_memories = base_memory_manager.retrieve_relevant_memories(
                                user_id, query="conversation messages recent personality patterns", limit=25
                            )

                            # Extract user messages from memory
                            for memory in cross_context_memories:
                                metadata = memory.get("metadata", {})
                                if metadata.get("user_message") and not metadata.get(
                                    "user_message", ""
                                ).startswith("!"):
                                    recent_messages.append(metadata["user_message"])

                            logger.debug(
                                f"Retrieved {len(recent_messages)} cross-context messages for personality analysis"
                            )
                        else:
                            logger.debug(
                                "Base memory manager not available for cross-context retrieval"
                            )

                        # If we don't have enough messages from ChromaDB, supplement with current context
                        if len(recent_messages) < 10:
                            try:
                                message_context = self.memory_manager.classify_discord_context(
                                    ctx.message
                                )
                                recent_context = (
                                    await self.safe_memory_manager.get_recent_conversations(
                                        user_id, limit=15, context=message_context
                                    )
                                )
                                if recent_context and hasattr(recent_context, "conversations"):
                                    for conv in recent_context.conversations:
                                        if (
                                            hasattr(conv, "user_message")
                                            and conv.user_message
                                            and not conv.user_message.startswith("!")
                                        ):
                                            if (
                                                conv.user_message not in recent_messages
                                            ):  # Avoid duplicates
                                                recent_messages.append(conv.user_message)

                                logger.debug(
                                    f"Supplemented with current context: now have {len(recent_messages)} messages"
                                )
                            except Exception as e:
                                logger.debug(f"Could not supplement with current context: {e}")

                    except Exception as e:
                        logger.debug(
                            f"Could not retrieve cross-context memories for personality display: {e}"
                        )

                        # Fallback: Try to get messages from current channel if memory manager completely fails
                        if (
                            ctx.guild is None
                        ):  # Only fallback in DM if memory manager completely fails
                            logger.debug(
                                "Falling back to Discord channel history for DM personality analysis"
                            )
                            async for msg in ctx.channel.history(limit=20):
                                if msg.author == target_user and not msg.content.startswith("!"):
                                    recent_messages.append(msg.content)

                    if len(recent_messages) >= 3:
                        # Perform real-time analysis
                        metrics = self.personality_profiler.analyze_personality(
                            recent_messages, user_id
                        )
                        summary = self.personality_profiler.get_personality_summary(metrics)

                        embed.add_field(
                            name="🎭 Big Five Traits",
                            value=f"**Openness:** {summary['personality_traits']['openness']}\n"
                            f"**Conscientiousness:** {summary['personality_traits']['conscientiousness']}\n"
                            f"**Extraversion:** {summary['personality_traits']['extraversion']}\n"
                            f"**Agreeableness:** {summary['personality_traits']['agreeableness']}\n"
                            f"**Neuroticism:** {summary['personality_traits']['neuroticism']}",
                            inline=True,
                        )

                        embed.add_field(
                            name="💬 Communication Style",
                            value=f"**Style:** {summary['communication_style']['primary'].title()}\n"
                            f"**Directness:** {summary['communication_style']['directness'].title()}\n"
                            f"**Confidence:** {summary['communication_style']['confidence_level']}",
                            inline=True,
                        )

                        embed.add_field(
                            name="🧭 Behavioral Patterns",
                            value=f"**Decision Style:** {summary['behavioral_patterns']['decision_style'].title()}\n"
                            f"**Emotional Expression:** {summary['behavioral_patterns']['emotional_expressiveness']}\n"
                            f"**Social Engagement:** {summary['behavioral_patterns']['social_engagement']}",
                            inline=True,
                        )

                        embed.add_field(
                            name="📈 Analysis Details",
                            value=f"**Messages Analyzed:** {summary['analysis_meta']['messages_analyzed']}\n"
                            f"**Confidence:** {summary['analysis_meta']['confidence']:.2f}\n"
                            f"**Analysis Type:** Real-time",
                            inline=True,
                        )
                    else:
                        embed.add_field(
                            name="⚠️ Insufficient Data",
                            value=f"Need at least 3 messages for personality analysis.\n"
                            f"Currently have: {len(recent_messages)} messages\n"
                            f"Chat with the bot more for better analysis!",
                            inline=False,
                        )
                except Exception as e:
                    logger.error(f"Error performing real-time personality analysis: {e}")
                    embed.add_field(
                        name="❌ Analysis Error",
                        value="Could not perform personality analysis at this time.",
                        inline=False,
                    )

            # Add Dynamic Personality Profile section
            if self.dynamic_personality_profiler:
                try:
                    dynamic_profile = None

                    # Try to get existing dynamic profile
                    if (
                        hasattr(self.dynamic_personality_profiler, "profiles")
                        and user_id in self.dynamic_personality_profiler.profiles
                    ):
                        dynamic_profile = self.dynamic_personality_profiler.profiles[user_id]
                    else:
                        # Try to load from database
                        if hasattr(self.dynamic_personality_profiler, "load_profile_from_db"):
                            dynamic_profile = (
                                await self.dynamic_personality_profiler.load_profile_from_db(
                                    user_id
                                )
                            )

                    if dynamic_profile:
                        embed.add_field(
                            name="🎭 Dynamic Personality Profile",
                            value="Real-time adaptive personality insights",
                            inline=False,
                        )

                        # Relationship metrics
                        embed.add_field(
                            name="🤝 Relationship Depth",
                            value=f"**Trust Level:** {dynamic_profile.trust_level:.2f}/1.0\n"
                            f"**Relationship Depth:** {dynamic_profile.relationship_depth:.2f}/1.0\n"
                            f"**Total Conversations:** {dynamic_profile.total_conversations}",
                            inline=True,
                        )

                        # Dynamic personality traits (top 3)
                        if dynamic_profile.traits:
                            trait_text = ""
                            sorted_traits = sorted(
                                dynamic_profile.traits.items(),
                                key=lambda x: x[1].confidence,
                                reverse=True,
                            )
                            for _i, (trait_name, trait) in enumerate(sorted_traits[:3]):
                                trait_display = trait_name.name.replace("_", " ").title()
                                trait_text += f"**{trait_display}:** {trait.value:.2f} ({trait.confidence:.1f}% confidence)\n"

                            embed.add_field(
                                name="🎯 Top Personality Dimensions",
                                value=trait_text or "No traits analyzed yet",
                                inline=True,
                            )

                        # Adaptation preferences
                        if (
                            hasattr(dynamic_profile, "preferred_response_style")
                            and dynamic_profile.preferred_response_style
                        ):
                            style_text = ""
                            for key, value in dynamic_profile.preferred_response_style.items():
                                if isinstance(value, (int, float)) and value > 0.6:
                                    style_text += (
                                        f"• {key.replace('_', ' ').title()}: {value:.1f}\n"
                                    )

                            if style_text:
                                embed.add_field(
                                    name="⚙️ AI Adaptation Preferences",
                                    value=style_text,
                                    inline=True,
                                )

                        # Recent conversation patterns
                        if (
                            hasattr(dynamic_profile, "conversation_analyses")
                            and dynamic_profile.conversation_analyses
                        ):
                            recent_analyses = list(dynamic_profile.conversation_analyses)[-5:]
                            if recent_analyses:
                                avg_formality = sum(
                                    a.formality_score for a in recent_analyses
                                ) / len(recent_analyses)
                                avg_openness = sum(
                                    a.emotional_openness for a in recent_analyses
                                ) / len(recent_analyses)
                                humor_freq = sum(
                                    1 for a in recent_analyses if a.humor_detected
                                ) / len(recent_analyses)

                                embed.add_field(
                                    name="📊 Recent Communication Patterns",
                                    value=f"**Formality:** {avg_formality:.2f}/1.0\n"
                                    f"**Emotional Openness:** {avg_openness:.2f}/1.0\n"
                                    f"**Humor Frequency:** {humor_freq:.1%}",
                                    inline=True,
                                )
                    else:
                        embed.add_field(
                            name="🎭 Dynamic Personality Profile",
                            value="No dynamic profile data yet. Chat more for adaptive insights!",
                            inline=False,
                        )

                except Exception as e:
                    logger.debug(f"Could not load dynamic personality profile: {e}")
                    embed.add_field(
                        name="🎭 Dynamic Personality Profile",
                        value="Dynamic profiling temporarily unavailable.",
                        inline=False,
                    )

            embed.set_footer(
                text="Personality profiles improve with more interactions • AI-powered analysis"
            )
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error showing personality profile: {e}")
            await ctx.send("❌ **Error:** Could not retrieve personality profile.")

    async def _dynamic_personality_handler(self, ctx, user, is_admin):
        """Handle dynamic personality command - integrated with personality facts"""
        # Determine target user
        target_user = user if user and is_admin(ctx) else ctx.author
        user_id = str(target_user.id)

        # Check if dynamic personality profiling is enabled
        if not self.dynamic_personality_profiler:
            await ctx.send(
                "🎭 **Dynamic personality profiling is not enabled** in this bot configuration."
            )
            return

        try:
            embed = discord.Embed(
                title=f"🎭 Dynamic Personality Profile: {target_user.display_name}",
                description="Real-time adaptive personality insights with AI behavior analysis",
                color=0xE91E63,
                timestamp=datetime.now(UTC),
            )

            dynamic_profile = None
            personality_facts = []

            # Try to get existing dynamic profile
            if (
                hasattr(self.dynamic_personality_profiler, "profiles")
                and user_id in self.dynamic_personality_profiler.profiles
            ):
                dynamic_profile = self.dynamic_personality_profiler.profiles[user_id]
            else:
                # Try to load from database
                if hasattr(self.dynamic_personality_profiler, "load_profile_from_db"):
                    dynamic_profile = await self.dynamic_personality_profiler.load_profile_from_db(
                        user_id
                    )

            # Get personality facts to complement dynamic profile
            try:
                personality_facts = self.memory_manager.retrieve_personality_facts(
                    user_id=user_id, limit=20
                )
            except Exception as e:
                logger.debug(f"Could not retrieve personality facts: {e}")

            if dynamic_profile:
                # Profile summary with integrated personality insights
                personality_insights_count = len(personality_facts)
                embed.add_field(
                    name="📈 Adaptive Profile Summary",
                    value=f"**Conversations Analyzed:** {dynamic_profile.total_conversations}\n"
                    f"**Relationship Depth:** {dynamic_profile.relationship_depth:.2f}/1.0\n"
                    f"**Trust Level:** {dynamic_profile.trust_level:.2f}/1.0\n"
                    f"**Personality Facts:** {personality_insights_count} insights\n"
                    f"**Last Updated:** {dynamic_profile.last_updated.strftime('%Y-%m-%d %H:%M') if hasattr(dynamic_profile, 'last_updated') else 'Unknown'}",
                    inline=False,
                )

                # Dynamic personality dimensions with fact support
                if dynamic_profile.traits:
                    dimensions_text = ""
                    sorted_traits = sorted(
                        dynamic_profile.traits.items(), key=lambda x: x[1].confidence, reverse=True
                    )

                    for trait_name, trait in sorted_traits[:6]:  # Top 6 traits
                        trait_display = trait_name.name.replace("_", " ").title()
                        confidence_stars = "⭐" * min(5, int(trait.confidence * 5))

                        # Create visual bar for trait value
                        bar_length = 10
                        filled = int((trait.value + 1) / 2 * bar_length)  # Convert -1,1 to 0,10
                        value_bar = "█" * filled + "░" * (bar_length - filled)

                        # Get supporting personality facts for this dimension
                        supporting_facts = [
                            f
                            for f in personality_facts
                            if trait_name.value in f.get("fact_type", "")
                        ]
                        fact_support = (
                            f" ({len(supporting_facts)} facts)" if supporting_facts else ""
                        )

                        dimensions_text += f"**{trait_display}**{fact_support}\n`{value_bar}` {trait.value:.2f} {confidence_stars}\n\n"

                    embed.add_field(
                        name="🎯 Personality Dimensions (Top 6)",
                        value=(
                            dimensions_text[:1024]
                            if dimensions_text
                            else "No dimensions analyzed yet"
                        ),
                        inline=False,
                    )

                # Show most relevant personality facts by type
                if personality_facts:
                    from collections import defaultdict

                    facts_by_type = defaultdict(list)

                    for fact in personality_facts:
                        fact_type = fact.get("fact_type", "unknown")
                        facts_by_type[fact_type].append(fact)

                    # Show top 3 fact categories with highest relevance
                    top_categories = sorted(
                        facts_by_type.items(),
                        key=lambda x: max([f.get("relevance_score", 0) for f in x[1]]),
                        reverse=True,
                    )[:3]

                    facts_text = ""
                    for fact_type, type_facts in top_categories:
                        type_display = fact_type.replace("_", " ").title()
                        type_emoji = self._get_personality_type_emoji(fact_type)
                        best_fact = max(type_facts, key=lambda x: x.get("relevance_score", 0))

                        relevance = best_fact.get("relevance_score", 0.0)
                        content = best_fact.get("content", "")[:60]
                        facts_text += f"{type_emoji} **{type_display}** ({len(type_facts)})\n`{content}...` (score: {relevance:.2f})\n\n"

                    if facts_text:
                        embed.add_field(
                            name="🧠 Supporting Personality Facts",
                            value=facts_text[:1024],
                            inline=False,
                        )

                # AI Adaptation insights with personality integration
                adaptation_text = ""
                if (
                    hasattr(dynamic_profile, "preferred_response_style")
                    and dynamic_profile.preferred_response_style
                ):
                    for key, value in dynamic_profile.preferred_response_style.items():
                        if isinstance(value, (int, float)):
                            adaptation_text += f"**{key.replace('_', ' ').title()}:** {value:.2f}\n"

                # Add personality-based adaptations
                if personality_facts:
                    high_relevance_facts = [
                        f for f in personality_facts if f.get("relevance_score", 0) >= 0.7
                    ]
                    adaptation_text += f"**Personality Integration:** {len(high_relevance_facts)} high-relevance insights\n"

                    # Show communication style adaptation
                    comm_facts = [
                        f for f in personality_facts if "communication" in f.get("fact_type", "")
                    ]
                    if comm_facts:
                        adaptation_text += (
                            f"**Communication Adaptation:** {len(comm_facts)} style preferences\n"
                        )

                if adaptation_text:
                    embed.add_field(
                        name="⚙️ AI Adaptation Settings", value=adaptation_text, inline=True
                    )

                # Recent conversation patterns
                if (
                    hasattr(dynamic_profile, "conversation_analyses")
                    and dynamic_profile.conversation_analyses
                ):
                    recent_analyses = list(dynamic_profile.conversation_analyses)[-10:]
                    if recent_analyses:
                        avg_formality = sum(a.formality_score for a in recent_analyses) / len(
                            recent_analyses
                        )
                        avg_openness = sum(a.emotional_openness for a in recent_analyses) / len(
                            recent_analyses
                        )
                        avg_depth = sum(a.conversation_depth for a in recent_analyses) / len(
                            recent_analyses
                        )
                        humor_freq = sum(1 for a in recent_analyses if a.humor_detected) / len(
                            recent_analyses
                        )
                        support_freq = sum(1 for a in recent_analyses if a.support_seeking) / len(
                            recent_analyses
                        )

                        embed.add_field(
                            name="📊 Communication Patterns",
                            value=f"**Formality Level:** {avg_formality:.2f}/1.0\n"
                            f"**Emotional Openness:** {avg_openness:.2f}/1.0\n"
                            f"**Conversation Depth:** {avg_depth:.2f}/1.0\n"
                            f"**Uses Humor:** {humor_freq:.1%}\n"
                            f"**Seeks Support:** {support_freq:.1%}",
                            inline=True,
                        )

                        # Topic analysis integrated with personality facts
                        all_topics = []
                        for analysis in recent_analyses:
                            all_topics.extend(analysis.topics_discussed)

                        if all_topics:
                            from collections import Counter

                            top_topics = Counter(all_topics).most_common(3)

                            # Cross-reference with personality fact topics
                            fact_topics = set()
                            for fact in personality_facts:
                                content = fact.get("content", "").lower()
                                for topic, _ in top_topics:
                                    if topic.lower() in content:
                                        fact_topics.add(topic)

                            topics_text = ""
                            for topic, count in top_topics:
                                emoji = "🎯" if topic in fact_topics else "💬"
                                topics_text += f"{emoji} {topic} ({count}x)\n"

                            embed.add_field(
                                name="🗣️ Frequent Topics", value=topics_text, inline=True
                            )

                # Integration health score
                if personality_facts and dynamic_profile.traits:
                    fact_trait_overlap = 0
                    for fact in personality_facts:
                        fact_type = fact.get("fact_type", "")
                        for trait_name in dynamic_profile.traits.keys():
                            if trait_name.value in fact_type:
                                fact_trait_overlap += 1
                                break

                    integration_score = (
                        fact_trait_overlap / len(personality_facts) if personality_facts else 0
                    )

                    embed.add_field(
                        name="� System Integration",
                        value=f"**Fact-Trait Alignment:** {integration_score:.1%}\n"
                        f"**Profile Completeness:** {len(dynamic_profile.traits)}/10 dimensions\n"
                        f"**Data Sources:** Conversations + Facts",
                        inline=True,
                    )

            else:
                # Show what we do have from personality facts
                if personality_facts:
                    embed.add_field(
                        name="🧠 Personality Facts Available",
                        value=f"Found {len(personality_facts)} personality insights!\n\n"
                        f"💬 **Continue chatting** to build dynamic profile\n"
                        f"📊 **Facts are ready** for integration\n"
                        f"⚙️ **AI adaptation** will improve over time",
                        inline=False,
                    )
                else:
                    embed.add_field(
                        name="🆕 Getting Started",
                        value="No personality data yet!\n\n"
                        "💬 **Chat with me more** to build your profile\n"
                        "🎯 **Share interests** and preferences\n"
                        "⚙️ **AI learns** your communication style\n"
                        "📈 **Check back** after a few conversations!",
                        inline=False,
                    )

            embed.set_footer(
                text="Dynamic profiles + Personality facts = Adaptive AI • Privacy-first analysis"
            )
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error showing dynamic personality profile: {e}")
            await ctx.send("❌ **Error:** Could not retrieve dynamic personality profile.")

    @handle_errors(
        category=ErrorCategory.MEMORY_SYSTEM,
        severity=ErrorSeverity.MEDIUM,
        operation="sync_check_handler"
    )
    async def _sync_check_handler(self, ctx):
        """Handle sync check command - now works globally across all contexts"""
        user_id = str(ctx.author.id)

        try:
            # Get stored conversations from ChromaDB (excluding facts)
            # Fix ChromaDB method signature - using updated API
            conversation_results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": str(user_id)}, {"type": {"$ne": "user_fact"}}]},
                limit=100
            )

            # Get stored facts separately
            # Fix ChromaDB method signature - using updated API
            fact_results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": str(user_id)}, {"type": "user_fact"}]},
                limit=50
            )

            # Analyze conversation contexts from stored memory
            context_breakdown = {}
            total_conversations = (
                len(conversation_results["ids"]) if conversation_results["ids"] else 0
            )

            if conversation_results["metadatas"]:
                for metadata in conversation_results["metadatas"]:
                    context_type = metadata.get("context_type", "unknown")
                    server_id = metadata.get("server_id", "dm")
                    channel_id = metadata.get("channel_id", "unknown")

                    # Create context key
                    if server_id == "dm" or context_type == "private_message":
                        context_key = "🔒 Direct Messages"
                    else:
                        # Try to get server/channel names if available
                        context_key = (
                            f"🌐 Server: {server_id[:8]}... (Channel: {channel_id[:8]}...)"
                        )

                    context_breakdown[context_key] = context_breakdown.get(context_key, 0) + 1

            # Get recent messages from current context for comparison (if DM)
            current_context_messages = 0
            if ctx.guild is None:
                try:
                    discord_messages = [msg async for msg in ctx.channel.history(limit=20)]
                    current_context_messages = len(
                        [msg for msg in discord_messages if msg.author == ctx.author]
                    )
                except Exception as e:
                    logger.debug(f"Could not get current context messages: {e}")
                    current_context_messages = 0

            # Create enhanced global sync report
            embed = discord.Embed(
                title=f"🌐 Global Memory Coverage: {ctx.author.display_name}",
                description="Memory analysis across **all contexts** where you've interacted with the bot",
                color=0x3498DB,
            )

            # Global statistics
            embed.add_field(
                name="📊 Total Stored",
                value=f"**Conversations:** {total_conversations}\n**Facts:** {len(fact_results['documents']) if fact_results['documents'] else 0}",
                inline=True,
            )

            # Context breakdown
            if context_breakdown:
                context_list = []
                for context, count in sorted(
                    context_breakdown.items(), key=lambda x: x[1], reverse=True
                ):
                    context_list.append(f"• {context}: **{count}** messages")

                embed.add_field(
                    name="�️ Context Distribution",
                    value="\n".join(context_list[:5]),  # Show top 5 contexts
                    inline=False,
                )

                if len(context_breakdown) > 5:
                    embed.add_field(
                        name="� Additional Contexts",
                        value=f"+ {len(context_breakdown) - 5} more contexts with stored conversations",
                        inline=False,
                    )

            # Current context comparison (only for DMs)
            if ctx.guild is None and current_context_messages > 0:
                dm_stored = context_breakdown.get("🔒 Direct Messages", 0)
                embed.add_field(
                    name="🔍 Current DM Analysis",
                    value=f"Recent messages here: **{current_context_messages}**\nStored from DMs: **{dm_stored}**",
                    inline=True,
                )

                if dm_stored < current_context_messages:
                    embed.add_field(
                        name="💡 Sync Suggestion",
                        value="Some recent DM messages may not be stored. Use `!import_history` to sync.",
                        inline=True,
                    )

            # Memory health indicator
            if total_conversations > 0:
                health_emoji = (
                    "🟢"
                    if total_conversations >= 10
                    else "🟡" if total_conversations >= 3 else "🔴"
                )
                embed.add_field(
                    name=f"{health_emoji} Memory Health",
                    value=f"{'Excellent' if total_conversations >= 10 else 'Good' if total_conversations >= 3 else 'Building'} conversation history",
                    inline=True,
                )

            embed.set_footer(
                text="💡 Use !import_history to sync older conversations • Memory spans all contexts"
            )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")

    @handle_errors(
        category=ErrorCategory.MEMORY_SYSTEM,
        severity=ErrorSeverity.MEDIUM,
        operation="my_memory_handler"
    )
    async def _my_memory_handler(self, ctx):
        """Handle my memory command"""
        user_id = str(ctx.author.id)

        try:
            # Get facts and conversations separately for accurate counts
            # Fix ChromaDB method signature - using updated API
            fact_results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": str(user_id)}, {"type": "user_fact"}]},
                limit=50
            )

            # Fix ChromaDB method signature - using updated API
            conversation_results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": str(user_id)}, {"type": {"$ne": "user_fact"}}]},
                limit=50
            )

            # Check if any data exists
            if not fact_results["documents"] and not conversation_results["documents"]:
                embed = discord.Embed(
                    title=f"🧠 Memory about {ctx.author.display_name}",
                    description="No memories stored yet. Start chatting to build up our conversation history!",
                    color=0x95A5A6,
                )
                await ctx.send(embed=embed)
                return

            # Process facts
            facts = []
            if fact_results["documents"]:
                for i, doc in enumerate(fact_results["documents"]):
                    metadata = fact_results["metadatas"][i]
                    facts.append(
                        {
                            "fact": metadata.get("fact", doc),
                            "timestamp": metadata.get("timestamp", ""),
                        }
                    )

            # Process conversations
            conversations = []
            if conversation_results["documents"]:
                for i, doc in enumerate(conversation_results["documents"]):
                    metadata = conversation_results["metadatas"][i]
                    conversations.append(
                        {
                            "user_message": metadata.get("user_message", ""),
                            "timestamp": metadata.get("timestamp", ""),
                        }
                    )

            # Sort by timestamp
            facts.sort(key=lambda x: x["timestamp"], reverse=True)
            conversations.sort(key=lambda x: x["timestamp"], reverse=True)

            embed = discord.Embed(
                title=f"🧠 Memory about {ctx.author.display_name}", color=0x3498DB
            )

            # Add facts section
            if facts:
                fact_list = []
                for fact in facts[:5]:  # Show top 5 facts
                    fact_text = (
                        fact["fact"][:80] + "..." if len(fact["fact"]) > 80 else fact["fact"]
                    )
                    fact_list.append(f"• {fact_text}")

                embed.add_field(
                    name="📝 Facts I Remember", value="\n".join(fact_list), inline=False
                )

            # Add recent conversations section
            if conversations:
                conv_list = []
                for conv in conversations[:3]:  # Show top 3 recent topics
                    msg = (
                        conv["user_message"][:60] + "..."
                        if len(conv["user_message"]) > 60
                        else conv["user_message"]
                    )
                    conv_list.append(f"• {msg}")

                embed.add_field(name="💬 Recent Topics", value="\n".join(conv_list), inline=False)

            embed.add_field(
                name="📊 Memory Stats",
                value=f"Total facts: {len(facts)}\nTotal conversations: {len(conversations)}",
                inline=True,
            )

            embed.set_footer(text="Use !add_fact, !list_facts, or !sync_check for more options")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error getting user memory summary: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")

    @handle_errors(
        category=ErrorCategory.MEMORY_SYSTEM,
        severity=ErrorSeverity.HIGH,
        operation="forget_me_handler"
    )
    async def _forget_me_handler(self, ctx):
        """Handle forget me command"""
        user_id = str(ctx.author.id)
        logger.debug(f"User {ctx.author.name} initiated forget_me command")

        # Confirmation step
        embed = discord.Embed(
            title="⚠️ Confirm Data Deletion",
            description="This will delete **ALL** stored information about you including:\n• Conversation history\n• Personal facts\n• All memories\n\n**This cannot be undone!**",
            color=0xE74C3C,
        )
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel (30 seconds)")

        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        logger.debug(f"Added reactions to message {message.id}")

        def check(reaction, user):
            logger.debug(
                f"Reaction check: user={user.name}, emoji={reaction.emoji}, message_id={reaction.message.id}, expected_id={message.id}"
            )
            return (
                user == ctx.author
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == message.id
            )

        try:
            logger.debug("Waiting for reaction...")
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            logger.debug(f"Received reaction: {reaction.emoji} from {user.name}")

            if str(reaction.emoji) == "✅":
                try:
                    logger.debug(
                        f"User confirmed deletion, proceeding to delete memories for {user_id}"
                    )
                    deleted_count = self.memory_manager.delete_user_memories(user_id)
                    await ctx.send(f"🗑️ **Forgotten!** Deleted {deleted_count} memories about you.")
                    logger.info(
                        f"User {ctx.author.name} deleted all their memories ({deleted_count} items)"
                    )
                except Exception as e:
                    logger.error(f"Error deleting user memories: {e}")
                    await ctx.send(f"❌ **Error deleting data:** {str(e)}")
            else:
                logger.debug("User cancelled deletion")
                await ctx.send("🚫 **Cancelled** - Your data has not been deleted.")

        except TimeoutError:
            logger.debug("Reaction timeout occurred")
            await ctx.send("⏰ **Timeout** - Data deletion cancelled.")

    async def _import_history_handler(self, ctx, limit):
        """Handle import history command - enhanced with global context awareness"""
        user_id = str(ctx.author.id)

        try:
            # First, show current memory status across contexts
            # Fix ChromaDB method signature - using updated API
            conversation_results = self.memory_manager.collection.get(
                where={"$and": [{"user_id": str(user_id)}, {"type": {"$ne": "user_fact"}}]},
                limit=200
            )

            # Analyze existing memory contexts
            existing_contexts = {}
            total_stored = len(conversation_results["ids"]) if conversation_results["ids"] else 0

            if conversation_results["metadatas"]:
                for metadata in conversation_results["metadatas"]:
                    context_type = metadata.get("context_type", "unknown")
                    server_id = metadata.get("server_id", "dm")

                    if server_id == "dm" or context_type == "private_message":
                        context_key = "Direct Messages"
                    else:
                        context_key = f"Server {server_id[:8]}..."

                    existing_contexts[context_key] = existing_contexts.get(context_key, 0) + 1

            # Create status embed
            embed = discord.Embed(
                title=f"📥 Import History: {ctx.author.display_name}",
                description="Current memory status and import options",
                color=0xE67E22,
            )

            embed.add_field(
                name="📊 Current Memory",
                value=f"**Total conversations:** {total_stored}\n**Contexts:** {len(existing_contexts)}",
                inline=True,
            )

            if existing_contexts:
                context_list = []
                for context, count in existing_contexts.items():
                    context_list.append(f"• {context}: {count}")
                embed.add_field(
                    name="🗂️ Stored Contexts", value="\n".join(context_list[:4]), inline=True
                )

            # Current context import capability
            if ctx.guild is None:
                # DM context - can import
                embed.add_field(
                    name="🔄 Available Import",
                    value=f"Can import up to **{limit}** messages from this DM conversation",
                    inline=False,
                )

                # Actually perform the import
                await ctx.send(embed=embed)
                await ctx.send(f"🔄 **Starting import** of last {limit} messages from this DM...")

                messages = [msg async for msg in ctx.channel.history(limit=limit)]
                imported = 0
                skipped = 0

                # Process messages in chronological order
                for i in range(len(messages) - 1, 0, -1):
                    current_msg = messages[i]
                    next_msg = messages[i - 1]

                    # Look for user message followed by bot response
                    if current_msg.author != self.bot.user and next_msg.author == self.bot.user:
                        # Skip bot commands - don't import them to memory
                        if current_msg.content.startswith("!"):
                            logger.debug(
                                f"Skipping command from import: {current_msg.content[:50]}..."
                            )
                            skipped += 1
                            continue
                        # Skip empty messages to avoid validation errors
                        if not current_msg.content or not current_msg.content.strip():
                            logger.debug(f"Skipping empty user message from {current_msg.author}")
                            skipped += 1
                            continue
                        if not next_msg.content or not next_msg.content.strip():
                            logger.debug("Skipping empty bot response")
                            skipped += 1
                            continue

                        self.memory_manager.store_conversation(
                            user_id,
                            extract_text_for_memory_storage(
                                current_msg.content, current_msg.attachments
                            ),
                            next_msg.content,
                        )
                        imported += 1
            else:
                # Server context - explain limitations
                embed.add_field(
                    name="⚠️ Server Context Limitation",
                    value="Import currently only works in **DM conversations**.\nSwitch to DMs to import message history.",
                    inline=False,
                )

                embed.add_field(
                    name="💡 Alternative",
                    value="Continue conversations in DMs and use `!sync_check` to monitor global memory coverage.",
                    inline=False,
                )

                await ctx.send(embed=embed)
                return

            # Send success message for DM imports
            result_embed = discord.Embed(
                title="✅ Import Complete",
                description="Successfully processed message history from this DM",
                color=0x27AE60,
            )

            result_embed.add_field(
                name="📊 Import Results",
                value=f"**Imported:** {imported} conversation pairs\n**Skipped:** {skipped} messages (commands/empty)",
                inline=True,
            )

            result_embed.add_field(
                name="🎯 Next Steps",
                value="• Use `!sync_check` to verify global memory\n• Use `!personality` to see updated analysis\n• Continue chatting to build more context",
                inline=False,
            )

            result_embed.set_footer(text="Memory now includes conversations from this DM context")

            await ctx.send(result_embed)
            logger.info(f"Imported {imported} conversation pairs for user {ctx.author.name}")

        except Exception as e:
            logger.error(f"Error importing history: {e}")
            await ctx.send(f"❌ **Import failed:** {str(e)}")

    async def _auto_facts_handler(self, ctx, setting):
        """Handle auto facts command"""
        str(ctx.author.id)

        if setting is None:
            # Show current status
            status = "enabled" if self.memory_manager.enable_auto_facts else "disabled"
            embed = discord.Embed(
                title="🤖 Automatic Fact Extraction",
                description=f"Automatic fact extraction is currently **{status}**",
                color=0x3498DB if self.memory_manager.enable_auto_facts else 0x95A5A6,
            )
            embed.add_field(
                name="ℹ️ What is this?",
                value="When enabled, the bot automatically identifies and remembers personal facts about you from your messages. Global facts can only be managed by admins.",
                inline=False,
            )
            embed.add_field(
                name="🔧 Usage",
                value="`!auto_facts on` - Enable automatic user fact extraction\n`!auto_facts off` - Disable automatic user fact extraction",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        if setting.lower() in ["on", "enable", "true", "1"]:
            await ctx.send(
                "❌ **Legacy feature:** Manual fact extraction has been replaced by automatic personality-driven classification.\n\nThe system now uses advanced AI to automatically classify and store facts based on your personality profile. This provides better accuracy and requires no manual management."
            )
            logger.info(f"User {ctx.author.name} attempted to enable legacy fact extraction")

        elif setting.lower() in ["off", "disable", "false", "0"]:
            await ctx.send(
                "ℹ️ **Info:** Legacy fact extraction is already disabled. The system uses personality-driven classification instead."
            )
            await ctx.send(
                "🔕 **Automatic user fact extraction disabled.**\nThe bot will only remember personal facts you explicitly add with `!add_fact`. Global facts are managed by admins only."
            )
            logger.info(f"User {ctx.author.name} disabled automatic fact extraction")

        else:
            await ctx.send("❌ Invalid setting. Use `on` or `off`.")

    async def _auto_extracted_facts_handler(self, ctx):
        """Handle auto extracted facts command"""
        user_id = str(ctx.author.id)

        try:
            # Get auto-extracted facts
            # Fix ChromaDB method signature - using updated API
            results = self.memory_manager.collection.get(
                where={
                    "$and": [
                        {"user_id": str(user_id)},
                        {"type": "user_fact"},
                        {"extraction_method": "automatic"},
                    ]
                },
                limit=50,
            )

            if not results["documents"]:
                embed = discord.Embed(
                    title="🤖 Auto-Extracted Facts",
                    description="No automatically extracted facts found. Either:\n• Automatic fact extraction is disabled\n• Not enough conversation data for extraction\n• No extractable facts detected yet",
                    color=0x95A5A6,
                )
                embed.add_field(
                    name="💡 Tips",
                    value="• Use `!auto_facts on` to enable automatic extraction\n• Chat more naturally for better fact detection\n• Use `!add_fact` to manually add important facts",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return

            # Sort by confidence score (if available) and timestamp
            facts_with_meta = list(zip(results["documents"], results["metadatas"], strict=False))
            facts_with_meta.sort(
                key=lambda x: (
                    x[1].get("confidence_score", 0.5),  # Sort by confidence
                    x[1].get("timestamp", ""),  # Then by timestamp
                ),
                reverse=True,
            )

            embed = discord.Embed(
                title=f"🤖 Auto-Extracted Facts for {ctx.author.display_name}",
                description=f"Found {len(facts_with_meta)} automatically detected facts:",
                color=0x3498DB,
            )

            # Display facts with confidence scores
            fact_list = []
            for _i, (doc, metadata) in enumerate(facts_with_meta[:15], 1):  # Limit to 15
                fact_text = metadata.get("fact", doc)
                confidence = metadata.get("confidence_score", 0.5)
                timestamp = metadata.get("timestamp", "Unknown")[:10]

                # Format with confidence indicator
                confidence_emoji = (
                    "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🟠"
                )
                fact_list.append(
                    f"{confidence_emoji} {fact_text} *(extracted {timestamp}, confidence: {confidence:.2f})*"
                )

            embed.description = (
                f"Found {len(facts_with_meta)} automatically detected facts:\n\n"
                + "\n\n".join(fact_list)
            )

            if len(facts_with_meta) > 15:
                embed.set_footer(
                    text=f"Showing top 15 of {len(facts_with_meta)} auto-extracted facts"
                )

            embed.add_field(
                name="📊 Confidence Legend",
                value="🟢 High (≥80%) | 🟡 Medium (60-80%) | 🟠 Low (<60%)",
                inline=False,
            )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error showing auto-extracted facts: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")

    async def _extract_facts_handler(self, ctx, message):
        """Handle extract facts command"""
        user_id = str(ctx.author.id)

        if not self.memory_manager.fact_extractor:
            await ctx.send(
                "❌ **Fact extraction is not enabled.** Use `!auto_facts on` to enable it first."
            )
            return

        try:
            # Test fact extraction on the provided message
            extracted_facts = self.memory_manager.fact_extractor.extract_personal_facts(
                message, user_id
            )

            embed = discord.Embed(
                title="🔍 Fact Extraction Test",
                description=f"**Input message:**\n> {message[:200]}{'...' if len(message) > 200 else ''}",
                color=0x3498DB,
            )

            if extracted_facts:
                fact_list = []
                for _i, fact_data in enumerate(extracted_facts, 1):
                    fact = fact_data.get("fact", "Unknown")
                    confidence = fact_data.get("confidence", 0.0)
                    confidence_emoji = (
                        "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🟠"
                    )
                    fact_list.append(f"{confidence_emoji} {fact} *(confidence: {confidence:.2f})*")

                embed.add_field(
                    name=f"📝 Extracted Facts ({len(extracted_facts)})",
                    value="\n\n".join(fact_list),
                    inline=False,
                )

                embed.add_field(
                    name="💡 Note",
                    value="These facts were extracted for testing only and **were not saved** to memory. Use the regular chat to have facts automatically saved.",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="❌ No Facts Extracted",
                    value="No personal facts detected in this message. Try messages that contain personal information like:\n• Hobbies or interests\n• Personal preferences\n• Facts about yourself\n• Life experiences",
                    inline=False,
                )

            embed.add_field(
                name="📊 Confidence Legend",
                value="🟢 High (≥80%) | 🟡 Medium (60-80%) | 🟠 Low (<60%)",
                inline=False,
            )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error testing fact extraction: {e}")
            await ctx.send(f"❌ **Error:** {str(e)}")

    def _get_personality_type_emoji(self, fact_type: str) -> str:
        """Get emoji for personality fact type"""
        emoji_map = {
            "interest_discovery": "🎯",
            "preference_expression": "❤️",
            "value_system": "⚖️",
            "emotional_insight": "🎭",
            "communication_style": "💬",
            "decision_making": "🤔",
            "life_context": "🏠",
            "social_dynamics": "👥",
            "learning_style": "📚",
            "goal_setting": "✨",
            "problem_solving": "🧩",
            "relationship_patterns": "🤝",
            "behavioral_traits": "🎪",
            "cognitive_patterns": "🧠",
            "motivational_drivers": "💪",
            "creative_expression": "🎨",
            "stress_management": "😌",
            "adaptation_style": "🔄",
            "temporal_patterns": "⏰",
            "environmental_preferences": "🌍",
        }
        return emoji_map.get(fact_type, "💡")
