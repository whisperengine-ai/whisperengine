from typing import Dict, Tuple
from datetime import datetime, timezone
from loguru import logger
from src_v2.core.database import db_manager

class ActivityModeler:
    """
    Analyzes user activity patterns to determine the best time to engage.
    """
    
    def __init__(self):
        pass

    async def get_user_activity_heatmap(self, user_id: str) -> Dict[str, float]:
        """
        Generates a heatmap of user activity probability for each hour of the week.
        Returns a dictionary where keys are "{weekday}_{hour}" (e.g., "0_14" for Monday 2 PM)
        and values are probabilities (0.0 to 1.0).
        
        Weekday: 0=Monday, 6=Sunday
        Hour: 0-23
        """
        if not db_manager.postgres_pool:
            logger.warning("Database not available for activity modeling.")
            return {}

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                # Fetch all session start times for the user
                # We look back up to 30 days to keep it relevant
                rows = await conn.fetch("""
                    SELECT start_time 
                    FROM v2_conversation_sessions 
                    WHERE user_id = $1 
                    AND start_time > NOW() - INTERVAL '30 days'
                """, user_id)

                if not rows:
                    return {}

                # Initialize grid (7 days * 24 hours)
                activity_counts = {}
                total_sessions = len(rows)

                for row in rows:
                    start_time: datetime = row['start_time']
                    # Ensure UTC
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                    
                    # Convert to user's local time? 
                    # Ideally yes, but we don't store user timezone yet.
                    # We will assume the bot operates in UTC or server time for now.
                    
                    weekday = start_time.weekday() # 0-6
                    hour = start_time.hour # 0-23
                    key = f"{weekday}_{hour}"
                    
                    activity_counts[key] = activity_counts.get(key, 0) + 1

                # Normalize to probabilities
                heatmap = {k: v / total_sessions for k, v in activity_counts.items()}
                return heatmap

        except Exception as e:
            logger.error(f"Failed to generate activity heatmap: {e}")
            return {}

    async def is_good_time_to_message(self, user_id: str, threshold: float = 0.1) -> Tuple[bool, float]:
        """
        Determines if now is a good time to message the user.
        Returns (is_good_time, confidence_score).
        """
        heatmap = await self.get_user_activity_heatmap(user_id)
        if not heatmap:
            # No data, assume it's NOT a good time to avoid spamming new users
            return False, 0.0

        now = datetime.now(timezone.utc)
        weekday = now.weekday()
        hour = now.hour
        key = f"{weekday}_{hour}"
        
        probability = heatmap.get(key, 0.0)
        
        # Also check adjacent hours (smoothing)
        # If user is usually active at 5 PM, 4 PM might also be okay.
        prev_hour = (hour - 1) % 24
        next_hour = (hour + 1) % 24
        
        prob_prev = heatmap.get(f"{weekday}_{prev_hour}", 0.0)
        prob_next = heatmap.get(f"{weekday}_{next_hour}", 0.0)
        
        # Weighted score
        score = (probability * 0.6) + (prob_prev * 0.2) + (prob_next * 0.2)
        
        is_good = score >= threshold
        return is_good, score

activity_modeler = ActivityModeler()
