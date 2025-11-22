"""
Trust & Relationship Manager

Tracks the evolving relationship between user and character, including
trust scores, relationship levels, and unlocked personality traits.
"""

from typing import Dict, Optional
from loguru import logger
from src_v2.core.database import db_manager
from src_v2.config.settings import settings


class TrustManager:
    """
    Manages relationship depth and trust scores between users and characters.
    """
    
    # Relationship level thresholds
    RELATIONSHIP_LEVELS = [
        (0, "Stranger"),
        (20, "Acquaintance"),
        (50, "Friend"),
        (80, "Close Friend"),
        (100, "Confidant")
    ]
    
    def __init__(self):
        logger.info("TrustManager initialized")

    async def get_relationship_level(self, user_id: str, character_name: str) -> Dict:
        """
        Retrieves the current relationship level and trust score.
        
        Returns:
            Dict with {trust_score: int, level: str, unlocked_traits: List[str]}
        """
        if not db_manager.postgres_pool:
            return {"trust_score": 0, "level": "Stranger", "unlocked_traits": []}
            
        try:
            async with db_manager.postgres_pool.acquire() as conn:
                # Check if relationship exists
                row = await conn.fetchrow("""
                    SELECT trust_score, unlocked_traits
                    FROM v2_user_relationships
                    WHERE user_id = $1 AND character_name = $2
                """, user_id, character_name)
                
                if not row:
                    # Initialize new relationship
                    await conn.execute("""
                        INSERT INTO v2_user_relationships (user_id, character_name, trust_score, unlocked_traits)
                        VALUES ($1, $2, 0, '[]'::jsonb)
                    """, user_id, character_name)
                    return {"trust_score": 0, "level": "Stranger", "unlocked_traits": []}
                
                trust_score = row['trust_score']
                unlocked_traits = row['unlocked_traits'] or []
                
                # Determine level
                level = "Stranger"
                for threshold, level_name in reversed(self.RELATIONSHIP_LEVELS):
                    if trust_score >= threshold:
                        level = level_name
                        break
                
                return {
                    "trust_score": trust_score,
                    "level": level,
                    "unlocked_traits": unlocked_traits
                }
                
        except Exception as e:
            logger.error(f"Failed to get relationship level: {e}")
            return {"trust_score": 0, "level": "Stranger", "unlocked_traits": []}

    async def update_trust(self, user_id: str, character_name: str, delta: int):
        """
        Adjusts trust score by delta amount.
        
        Args:
            user_id: User ID
            character_name: Character name
            delta: Amount to change trust by (can be negative)
        """
        if not db_manager.postgres_pool:
            return
            
        try:
            async with db_manager.postgres_pool.acquire() as conn:
                # Ensure relationship exists
                await self.get_relationship_level(user_id, character_name)
                
                # Update trust score (clamp between 0 and 150)
                await conn.execute("""
                    UPDATE v2_user_relationships
                    SET trust_score = GREATEST(0, LEAST(150, trust_score + $3)),
                        updated_at = NOW()
                    WHERE user_id = $1 AND character_name = $2
                """, user_id, character_name, delta)
                
                logger.info(f"Updated trust for {user_id} with {character_name}: {delta:+d}")
                
        except Exception as e:
            logger.error(f"Failed to update trust: {e}")

    async def unlock_trait(self, user_id: str, character_name: str, trait: str):
        """
        Unlocks a new personality trait for this relationship.
        
        Args:
            trait: Name of the trait (e.g., "vulnerable", "protective")
        """
        if not db_manager.postgres_pool:
            return
            
        try:
            async with db_manager.postgres_pool.acquire() as conn:
                # Append trait to unlocked_traits array
                await conn.execute("""
                    UPDATE v2_user_relationships
                    SET unlocked_traits = unlocked_traits || $3::jsonb
                    WHERE user_id = $1 AND character_name = $2
                    AND NOT (unlocked_traits @> $3::jsonb)
                """, user_id, character_name, f'["{trait}"]')
                
                logger.info(f"Unlocked trait '{trait}' for {user_id} with {character_name}")
                
        except Exception as e:
            logger.error(f"Failed to unlock trait: {e}")


# Global singleton
trust_manager = TrustManager()
