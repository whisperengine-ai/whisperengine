import asyncio
import logging
import time
from typing import Optional
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class HeartbeatMonitor:
    """
    Advanced heartbeat monitor that runs in a separate task
    to ensure connection stability and provide detailed diagnostics
    """
    
    def __init__(self, bot: commands.Bot, check_interval: float = 30.0):
        self.bot = bot
        self.check_interval = check_interval
        self.last_heartbeat = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.connection_issues = 0
        self.max_connection_issues = 3
        
    def start(self):
        """Start the heartbeat monitoring task"""
        if self.heartbeat_task is None or self.heartbeat_task.done():
            self.heartbeat_task = asyncio.create_task(self._monitor_loop())
            logger.info(f"Heartbeat monitor started with {self.check_interval}s interval")
    
    def stop(self):
        """Stop the heartbeat monitoring task"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            logger.info("Heartbeat monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop that runs in background"""
        try:
            while not self.bot.is_closed():
                await self._check_connection_health()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("Heartbeat monitor cancelled")
        except Exception as e:
            logger.error(f"Heartbeat monitor error: {e}")
    
    async def _check_connection_health(self):
        """Check the health of the Discord connection with enhanced monitoring"""
        try:
            # Check if bot is connected and ready
            if not self.bot.is_ready():
                logger.debug("Bot not ready, skipping heartbeat check")
                return
            
            # Check WebSocket connection
            if hasattr(self.bot, 'ws') and self.bot.ws:
                # Get latency (this is the heartbeat round-trip time)
                latency = self.bot.latency
                
                if latency > 0:
                    self.last_heartbeat = time.time()
                    
                    # More aggressive latency monitoring to prevent session invalidation
                    if latency > 3.0:  # 3+ seconds is very concerning
                        self.connection_issues += 1
                        logger.warning(f"HIGH heartbeat latency: {latency:.2f}s (issue #{self.connection_issues})")
                        
                        # Immediate recovery attempt for very high latency
                        if latency > 10.0:
                            logger.error(f"CRITICAL heartbeat latency: {latency:.2f}s - attempting immediate recovery")
                            await self._handle_connection_problem()
                    elif latency > 1.5:  # 1.5+ seconds is concerning
                        logger.warning(f"Elevated heartbeat latency: {latency:.2f}s")
                        # Gradual recovery - reset issues counter slower
                        self.connection_issues = max(0, self.connection_issues - 0.5)
                    elif latency > 1.0:  # 1+ seconds is worth noting
                        logger.debug(f"Moderate heartbeat latency: {latency:.2f}s")
                        self.connection_issues = max(0, self.connection_issues - 1)
                    else:
                        # Good latency - reset counter completely
                        self.connection_issues = 0
                        
                    # Proactive recovery for sustained issues
                    if self.connection_issues >= self.max_connection_issues:
                        logger.error("Multiple connection issues detected - attempting proactive recovery")
                        await self._handle_connection_problem()
                else:
                    # Latency of 0 or negative indicates connection issues
                    self.connection_issues += 2  # More severe penalty
                    logger.warning(f"Invalid heartbeat latency: {latency} (issue #{self.connection_issues})")
                    
                    if self.connection_issues >= self.max_connection_issues:
                        logger.error("Invalid latency detected - connection may be failing")
                        await self._handle_connection_problem()
            else:
                logger.warning("No WebSocket connection available")
                self.connection_issues += 1
                
        except Exception as e:
            logger.error(f"Error checking connection health: {e}")
            self.connection_issues += 1
    
    async def _handle_connection_problem(self):
        """Handle detected connection problems with enhanced recovery"""
        logger.warning("Handling connection problem - attempting enhanced recovery")
        
        try:
            # Multiple recovery strategies
            
            # 1. Try presence refresh (lightweight)
            await self.bot.change_presence(status=discord.Status.online)
            await asyncio.sleep(0.5)  # Small delay between attempts
            
            # 2. Try a lightweight API call to test connection
            try:
                if self.bot.user and self.bot.user.id:
                    await self.bot.fetch_user(self.bot.user.id)
                    logger.info("✅ Connection test successful")
            except Exception as api_error:
                logger.warning(f"Connection test failed: {api_error}")
            
            # 3. Final presence update with activity
            try:
                activity = discord.Activity(type=discord.ActivityType.listening, name="for messages")
                await self.bot.change_presence(status=discord.Status.online, activity=activity)
                logger.info("✅ Enhanced recovery completed")
            except Exception as presence_error:
                logger.warning(f"Final presence update failed: {presence_error}")
            
            # Reset connection issue counter after recovery attempts
            self.connection_issues = 0
            
        except Exception as e:
            logger.error(f"Enhanced recovery failed: {e}")
            # Don't reset counter if recovery completely failed
    
    def get_status(self) -> dict:
        """Get current status of the heartbeat monitor"""
        return {
            'running': self.heartbeat_task is not None and not self.heartbeat_task.done(),
            'last_heartbeat': self.last_heartbeat,
            'connection_issues': self.connection_issues,
            'bot_latency': self.bot.latency if hasattr(self.bot, 'latency') else None,
            'bot_ready': self.bot.is_ready() if hasattr(self.bot, 'is_ready') else False
        }
