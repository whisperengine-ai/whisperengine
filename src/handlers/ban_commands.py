"""
Ban System Command Handlers for WhisperEngine
Provides Discord commands for banning and unbanning abusive users.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands

from src.database.database_integration import DatabaseIntegrationManager
from src.utils.production_error_handler import (
    ErrorCategory,
    ErrorSeverity,
    handle_errors,
)

logger = logging.getLogger(__name__)


class BanCommandHandlers:
    """
    Handler class for Discord ban/unban commands.
    
    Provides moderation capabilities to ban abusive users from interacting
    with WhisperEngine bots across all servers.
    """

    def __init__(self, bot: commands.Bot, postgres_pool=None, db_integration: Optional[DatabaseIntegrationManager] = None):
        """
        Initialize ban command handlers.
        
        Args:
            bot: Discord bot instance
            postgres_pool: Shared PostgreSQL connection pool (preferred)
            db_integration: Database integration manager for persistence (fallback)
        """
        self.bot = bot
        self.postgres_pool = postgres_pool
        self.db_integration = db_integration or DatabaseIntegrationManager()
        self._ban_cache = {}  # Cache for frequently checked banned users
        self._cache_ttl = 300  # 5 minutes cache TTL
        
    async def _execute_query(self, query: str, params: Optional[dict] = None):
        """
        Execute a database query using the preferred connection method.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Query result
        """
        if self.postgres_pool:
            # Use shared PostgreSQL pool (preferred)
            async with self.postgres_pool.acquire() as connection:
                if params:
                    # Convert named parameters to positional for asyncpg
                    query_positional = query
                    values = []
                    for key, value in params.items():
                        query_positional = query_positional.replace(f":{key}", f"${len(values) + 1}")
                        values.append(value)
                    result = await connection.fetch(query_positional, *values)
                else:
                    result = await connection.fetch(query)
                # Convert to list of dicts to match DatabaseManager interface
                return [dict(row) for row in result]
        else:
            # Fall back to DatabaseIntegrationManager
            if not self.db_integration.initialized:
                await self.db_integration.initialize()
            
            db_manager = self.db_integration.get_database_manager()
            result = await db_manager.query(query, params)
            
            # Handle QueryResult type
            if hasattr(result, 'rows'):
                return result.rows
            elif isinstance(result, list):
                return result
            else:
                return []
        
    def register_commands(self, bot_name_filter=None, is_admin=None):
        """
        Register ban/unban commands with the Discord bot.
        
        Args:
            bot_name_filter: Optional filter function for bot names
            is_admin: Optional function to check admin privileges
        """
        @self.bot.command(name="ban", help="Ban a user from interacting with the bot")
        @handle_errors(
            category=ErrorCategory.DISCORD_API,
            severity=ErrorSeverity.HIGH,
            operation="ban_user_command"
        )
        async def ban_user(ctx, user_id: str, *, reason: str = "No reason provided"):
            await self._handle_ban_command(ctx, user_id, reason, is_admin)
            
        @self.bot.command(name="unban", help="Unban a user")
        @handle_errors(
            category=ErrorCategory.DISCORD_API,
            severity=ErrorSeverity.HIGH,
            operation="unban_user_command"
        )
        async def unban_user(ctx, user_id: str, *, reason: str = "No reason provided"):
            await self._handle_unban_command(ctx, user_id, reason, is_admin)
            
        @self.bot.command(name="banlist", help="List banned users")
        @handle_errors(
            category=ErrorCategory.DISCORD_API,
            severity=ErrorSeverity.MEDIUM,
            operation="list_banned_users"
        )
        async def list_banned_users(ctx, limit: int = 10):
            await self._handle_banlist_command(ctx, limit, is_admin)
            
        @self.bot.command(name="bancheck", help="Check if a user is banned")
        @handle_errors(
            category=ErrorCategory.DISCORD_API,
            severity=ErrorSeverity.MEDIUM,
            operation="check_banned_user"
        )
        async def check_banned_user(ctx, user_id: str):
            await self._handle_bancheck_command(ctx, user_id, is_admin)
            
        logger.info("✅ Ban command handlers registered")

    async def _handle_ban_command(self, ctx, user_id: str, reason: str, is_admin=None):
        """Handle the ban command."""
        # Check admin permissions
        if is_admin and not is_admin(ctx.author.id):
            await ctx.send("❌ You don't have permission to use this command.")
            return
            
        # Validate user ID format
        if not self._is_valid_discord_id(user_id):
            await ctx.send("❌ Invalid Discord user ID format. Please provide a valid Discord user ID (numbers only).")
            return
            
        # Prevent self-ban
        if user_id == str(ctx.author.id):
            await ctx.send("❌ You cannot ban yourself!")
            return
            
        # Prevent banning the bot
        if self.bot.user and user_id == str(self.bot.user.id):
            await ctx.send("❌ I cannot ban myself!")
            return
            
        try:
            # Check if user is already banned
            if await self.is_user_banned(user_id):
                await ctx.send(f"⚠️ User `{user_id}` is already banned.")
                return
                
            # Add ban to database
            success = await self._add_ban_to_database(
                discord_user_id=user_id,
                banned_by=str(ctx.author.id),
                reason=reason
            )
            
            if success:
                # Clear cache for this user
                cache_key = f"ban_{user_id}"
                self._ban_cache.pop(cache_key, None)
                
                # Try to get user info for better display
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_display = f"{user.name}#{user.discriminator} (`{user_id}`)"
                except:
                    user_display = f"`{user_id}`"
                
                await ctx.send(f"✅ Successfully banned user {user_display}\n"
                              f"**Reason:** {reason}\n"
                              f"**Banned by:** {ctx.author.mention}")
                              
                logger.info(f"User {user_id} banned by {ctx.author.id} - Reason: {reason}")
            else:
                await ctx.send("❌ Failed to ban user. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await ctx.send("❌ An error occurred while processing the ban command.")

    async def _handle_unban_command(self, ctx, user_id: str, reason: str, is_admin=None):
        """Handle the unban command."""
        # Check admin permissions
        if is_admin and not is_admin(ctx.author.id):
            await ctx.send("❌ You don't have permission to use this command.")
            return
            
        # Validate user ID format
        if not self._is_valid_discord_id(user_id):
            await ctx.send("❌ Invalid Discord user ID format.")
            return
            
        try:
            # Check if user is actually banned
            if not await self.is_user_banned(user_id):
                await ctx.send(f"⚠️ User `{user_id}` is not currently banned.")
                return
                
            # Remove ban from database
            success = await self._remove_ban_from_database(
                discord_user_id=user_id,
                unbanned_by=str(ctx.author.id),
                reason=reason
            )
            
            if success:
                # Clear cache for this user
                cache_key = f"ban_{user_id}"
                self._ban_cache.pop(cache_key, None)
                
                # Try to get user info for better display
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_display = f"{user.name}#{user.discriminator} (`{user_id}`)"
                except:
                    user_display = f"`{user_id}`"
                
                await ctx.send(f"✅ Successfully unbanned user {user_display}\n"
                              f"**Reason:** {reason}\n"
                              f"**Unbanned by:** {ctx.author.mention}")
                              
                logger.info(f"User {user_id} unbanned by {ctx.author.id} - Reason: {reason}")
            else:
                await ctx.send("❌ Failed to unban user. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in unban command: {e}")
            await ctx.send("❌ An error occurred while processing the unban command.")

    async def _handle_banlist_command(self, ctx, limit: int, is_admin=None):
        """Handle the banlist command."""
        # Check admin permissions
        if is_admin and not is_admin(ctx.author.id):
            await ctx.send("❌ You don't have permission to use this command.")
            return
            
        # Validate limit
        if limit < 1 or limit > 50:
            await ctx.send("❌ Limit must be between 1 and 50.")
            return
            
        try:
            banned_users_result = await self._get_banned_users_list(limit)
            
            # Extract rows from QueryResult or handle list directly
            banned_users = []
            if banned_users_result:
                # Check if it's a QueryResult with rows attribute
                if hasattr(banned_users_result, 'rows') and hasattr(banned_users_result, 'success'):
                    # Type narrowing for QueryResult
                    banned_users = getattr(banned_users_result, 'rows', [])
                elif isinstance(banned_users_result, list):
                    banned_users = banned_users_result
            
            if not banned_users:
                await ctx.send("✅ No users are currently banned.")
                return
                
            # Format the ban list
            embed = discord.Embed(
                title="📋 Banned Users List",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            for idx, ban_record in enumerate(banned_users, 1):
                # Handle dictionary result (most common from QueryResult.rows)
                if isinstance(ban_record, dict):
                    user_id = ban_record.get('discord_user_id', 'Unknown')
                    reason = ban_record.get('ban_reason') or "No reason provided"
                    banned_at = ban_record.get('banned_at', 'Unknown')
                    banned_by = ban_record.get('banned_by', 'Unknown')
                else:
                    # Handle tuple/list result (fallback)
                    user_id = str(ban_record[0]) if len(ban_record) > 0 else 'Unknown'
                    reason = str(ban_record[2]) if len(ban_record) > 2 else "No reason provided"
                    banned_at = str(ban_record[3]) if len(ban_record) > 3 else 'Unknown'
                    banned_by = str(ban_record[1]) if len(ban_record) > 1 else 'Unknown'
                
                # Try to get user info
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_display = f"{user.name}#{user.discriminator}"
                except:
                    user_display = f"User ID: {user_id}"
                
                embed.add_field(
                    name=f"{idx}. {user_display}",
                    value=f"**ID:** `{user_id}`\n"
                          f"**Reason:** {reason[:100]}{'...' if len(reason) > 100 else ''}\n"
                          f"**Banned:** {banned_at}\n"
                          f"**By:** <@{banned_by}>",
                    inline=False
                )
                
            embed.set_footer(text=f"Showing {len(banned_users)} of {limit} requested")
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in banlist command: {e}")
            await ctx.send("❌ An error occurred while retrieving the ban list.")

    async def _handle_bancheck_command(self, ctx, user_id: str, is_admin=None):
        """Handle the bancheck command."""
        # Check admin permissions
        if is_admin and not is_admin(ctx.author.id):
            await ctx.send("❌ You don't have permission to use this command.")
            return
            
        # Validate user ID format
        if not self._is_valid_discord_id(user_id):
            await ctx.send("❌ Invalid Discord user ID format.")
            return
            
        try:
            is_banned = await self.is_user_banned(user_id)
            
            if is_banned:
                # Get ban details
                ban_details = await self._get_ban_details(user_id)
                
                # Try to get user info
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_display = f"{user.name}#{user.discriminator} (`{user_id}`)"
                except:
                    user_display = f"`{user_id}`"
                
                embed = discord.Embed(
                    title="🚫 User is Banned",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(name="User", value=user_display, inline=False)
                if ban_details:
                    embed.add_field(name="Reason", value=ban_details.get('ban_reason', 'No reason provided'), inline=False)
                    embed.add_field(name="Banned At", value=ban_details.get('banned_at', 'Unknown'), inline=True)
                    embed.add_field(name="Banned By", value=f"<@{ban_details.get('banned_by', 'Unknown')}>", inline=True)
                
                await ctx.send(embed=embed)
            else:
                # Try to get user info
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_display = f"{user.name}#{user.discriminator} (`{user_id}`)"
                except:
                    user_display = f"`{user_id}`"
                
                await ctx.send(f"✅ User {user_display} is not banned.")
                
        except Exception as e:
            logger.error(f"Error in bancheck command: {e}")
            await ctx.send("❌ An error occurred while checking ban status.")

    async def is_user_banned(self, discord_user_id: str) -> bool:
        """
        Check if a Discord user is currently banned.
        
        Args:
            discord_user_id: Discord user ID to check
            
        Returns:
            True if user is banned, False otherwise
        """
        # Check cache first
        cache_key = f"ban_{discord_user_id}"
        cached_result = self._ban_cache.get(cache_key)
        
        if cached_result is not None:
            cache_time, is_banned = cached_result
            if (datetime.now() - cache_time).total_seconds() < self._cache_ttl:
                return is_banned
        
        try:
            # Query database for active ban using preferred connection method
            result = await self._execute_query(
                """
                SELECT id FROM banned_users 
                WHERE discord_user_id = :user_id 
                AND is_active = TRUE 
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                LIMIT 1
                """,
                {"user_id": discord_user_id}
            )
            
            # Check if we actually have results
            is_banned = bool(result)
            
            # Cache the result
            self._ban_cache[cache_key] = (datetime.now(), is_banned)
            
            return is_banned
            
        except Exception as e:
            logger.error(f"Error checking ban status for user {discord_user_id}: {e}")
            # On error, assume not banned to avoid false positives
            return False

    async def _add_ban_to_database(self, discord_user_id: str, banned_by: str, reason: str) -> bool:
        """Add a ban record to the database."""
        try:
            # Insert ban record - use CURRENT_TIMESTAMP for cross-database compatibility
            await self._execute_query(
                """
                INSERT INTO banned_users 
                (discord_user_id, banned_by, ban_reason, banned_at, is_active, notes)
                VALUES (:user_id, :banned_by, :reason, CURRENT_TIMESTAMP, TRUE, 
                        'Banned via Discord command')
                """,
                {
                    "user_id": discord_user_id,
                    "banned_by": banned_by,
                    "reason": reason
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding ban to database: {e}")
            return False

    async def _remove_ban_from_database(self, discord_user_id: str, unbanned_by: str, reason: str) -> bool:
        """Remove a ban record from the database (mark as inactive)."""
        try:
            # Update ban record to inactive with proper audit columns
            await self._execute_query(
                """
                UPDATE banned_users 
                SET is_active = FALSE,
                    unbanned_at = CURRENT_TIMESTAMP,
                    unbanned_by = :unbanned_by,
                    unban_reason = :reason
                WHERE discord_user_id = :user_id AND is_active = TRUE
                """,
                {
                    "user_id": discord_user_id,
                    "unbanned_by": unbanned_by,
                    "reason": reason
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing ban from database: {e}")
            return False

    async def _get_banned_users_list(self, limit: int = 10):
        """Get a list of currently banned users."""
        try:
            # Query for active bans
            result = await self._execute_query(
                """
                SELECT discord_user_id, banned_by, ban_reason, banned_at
                FROM banned_users 
                WHERE is_active = TRUE 
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ORDER BY banned_at DESC
                LIMIT :limit
                """,
                {"limit": limit}
            )
            
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error retrieving banned users list: {e}")
            return []

    async def _get_ban_details(self, discord_user_id: str):
        """Get detailed information about a user's ban."""
        try:
            # Query for ban details
            result = await self._execute_query(
                """
                SELECT discord_user_id, banned_by, ban_reason, banned_at, expires_at, notes
                FROM banned_users 
                WHERE discord_user_id = :user_id 
                AND is_active = TRUE
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                LIMIT 1
                """,
                {"user_id": discord_user_id}
            )
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error retrieving ban details for user {discord_user_id}: {e}")
            return None

    def _is_valid_discord_id(self, user_id: str) -> bool:
        """
        Validate that a string is a valid Discord user ID.
        
        Args:
            user_id: String to validate
            
        Returns:
            True if valid Discord ID format, False otherwise
        """
        # Discord IDs are 17-19 digit snowflakes
        return bool(re.match(r'^\d{17,19}$', user_id))

    def clear_cache(self):
        """Clear the ban cache (useful for testing or manual refresh)."""
        self._ban_cache.clear()
        logger.info("Ban cache cleared")