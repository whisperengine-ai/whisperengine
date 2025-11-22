import asyncio
from datetime import datetime, timedelta, timezone
from loguru import logger
from discord.ext import commands
from src_v2.config.settings import settings
from src_v2.core.database import db_manager
from src_v2.intelligence.activity import activity_modeler
from src_v2.agents.proactive import proactive_agent

class ProactiveScheduler:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_interval_minutes = 60 # Check every hour
        self.min_trust_score = 20 # Only message Acquaintances or higher
        self.silence_threshold_hours = 24 # Don't message if we spoke recently
        self.is_running = False

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.bot.loop.create_task(self._loop())
        logger.info("ProactiveScheduler started.")

    async def _loop(self):
        await self.bot.wait_until_ready()
        while self.is_running:
            try:
                await self.check_all_users()
            except Exception as e:
                logger.error(f"Error in proactive scheduler loop: {e}")
            
            await asyncio.sleep(self.check_interval_minutes * 60)

    async def check_all_users(self):
        if not db_manager.postgres_pool:
            return

        character_name = settings.DISCORD_BOT_NAME
        if not character_name:
            return

        logger.info("Running proactive engagement check...")

        # Get all users who have a relationship with this bot
        # Join with sessions to get last interaction time
        async with db_manager.postgres_pool.acquire() as conn:
            users = await conn.fetch("""
                SELECT 
                    r.user_id, 
                    r.trust_score,
                    MAX(s.updated_at) as last_interaction
                FROM v2_user_relationships r
                LEFT JOIN v2_conversation_sessions s 
                    ON r.user_id = s.user_id 
                    AND r.character_name = s.character_name
                WHERE r.character_name = $1
                GROUP BY r.user_id, r.trust_score
            """, character_name)

        for row in users:
            user_id = row['user_id']
            trust_score = row['trust_score']
            last_interaction = row['last_interaction']

            await self.check_user(user_id, trust_score, last_interaction)

    async def check_user(self, user_id: str, trust_score: int, last_interaction: datetime):
        # 1. Check Trust
        if trust_score < self.min_trust_score:
            return

        # 2. Check Silence Duration
        if last_interaction:
            # Ensure UTC
            if last_interaction.tzinfo is None:
                last_interaction = last_interaction.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            if (now - last_interaction) < timedelta(hours=self.silence_threshold_hours):
                return # Too soon
        else:
            # Never interacted? Or no session found.
            # If trust score > 0 but no session, maybe old data.
            # Let's skip to be safe.
            return

        # 3. Check Activity Model (Is it a good time?)
        is_good_time, confidence = await activity_modeler.is_good_time_to_message(user_id)
        if not is_good_time:
            return

        # 4. Trigger Engagement
        logger.info(f"Triggering proactive message for User {user_id} (Confidence: {confidence:.2f})")
        await self.trigger_proactive_message(user_id)

    async def trigger_proactive_message(self, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            if not user:
                logger.warning(f"Could not fetch user {user_id} for proactive message.")
                return

            # Generate the message
            character_name = settings.DISCORD_BOT_NAME or "default"
            opener = await proactive_agent.generate_opener(user_id, character_name)
            
            if opener:
                logger.info(f"Sending proactive message to {user.name}: {opener}")
                await user.send(opener)
                
                # TODO: Log this message to memory/history so the bot remembers it sent it!
                # Ideally we'd use memory_manager.add_message here.
                
            else:
                logger.warning(f"Failed to generate opener for {user.name}")

        except Exception as e:
            logger.error(f"Failed to send proactive message to {user_id}: {e}")
