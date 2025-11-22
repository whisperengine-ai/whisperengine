from typing import List, Dict, Any, Optional
import json
from loguru import logger
from src_v2.core.database import db_manager
from src_v2.agents.llm_factory import create_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class GoalManager:
    def __init__(self):
        # Default goals that apply to all characters
        # In production, these would be loaded from YAML/DB
        self.default_goals = [
            {
                "slug": "learn_name",
                "description": "Learn the user's name.",
                "success_criteria": "User explicitly states their name.",
                "priority": 10
            }
        ]

    async def ensure_goals_exist(self, character_name: str):
        """
        Ensures default goals exist in the database for the character.
        """
        if not db_manager.postgres_pool:
            return

        # Use the universal default goals
        goals = self.default_goals
        
        async with db_manager.postgres_pool.acquire() as conn:
            for goal in goals:
                # Check if goal exists
                exists = await conn.fetchval("""
                    SELECT id FROM v2_goals 
                    WHERE character_name = $1 AND slug = $2
                """, character_name, goal["slug"])
                
                if not exists:
                    await conn.execute("""
                        INSERT INTO v2_goals (character_name, slug, description, success_criteria, priority)
                        VALUES ($1, $2, $3, $4, $5)
                    """, character_name, goal["slug"], goal["description"], goal["success_criteria"], goal["priority"])
                    logger.info(f"Created goal '{goal['slug']}' for {character_name}")

    async def get_active_goals(self, user_id: str, character_name: str) -> List[Dict[str, Any]]:
        """
        Retrieves active (not completed) goals for the user, ordered by priority.
        """
        if not db_manager.postgres_pool:
            return []

        # First ensure goals exist
        await self.ensure_goals_exist(character_name)

        async with db_manager.postgres_pool.acquire() as conn:
            # Get goals that are NOT completed for this user
            # We join with progress table to check status
            query = """
                SELECT g.id, g.slug, g.description, g.success_criteria, g.priority,
                       COALESCE(p.status, 'not_started') as status,
                       COALESCE(p.progress_score, 0.0) as progress
                FROM v2_goals g
                LEFT JOIN v2_user_goal_progress p ON g.id = p.goal_id AND p.user_id = $1
                WHERE g.character_name = $2
                AND (p.status IS NULL OR p.status != 'completed')
                ORDER BY g.priority DESC
            """
            rows = await conn.fetch(query, user_id, character_name)
            return [dict(row) for row in rows]

    async def update_goal_progress(self, user_id: str, goal_slug: str, character_name: str, status: str, progress: float = 0.0, metadata: Optional[Dict] = None):
        """
        Updates the progress of a specific goal.
        """
        if not db_manager.postgres_pool:
            return

        async with db_manager.postgres_pool.acquire() as conn:
            # Get goal ID
            goal_id = await conn.fetchval("""
                SELECT id FROM v2_goals WHERE character_name = $1 AND slug = $2
            """, character_name, goal_slug)
            
            if not goal_id:
                logger.warning(f"Goal '{goal_slug}' not found for {character_name}")
                return

            # Upsert progress
            await conn.execute("""
                INSERT INTO v2_user_goal_progress (user_id, goal_id, status, progress_score, metadata, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (user_id, goal_id) 
                DO UPDATE SET 
                    status = EXCLUDED.status,
                    progress_score = EXCLUDED.progress_score,
                    metadata = COALESCE(v2_user_goal_progress.metadata, '{}'::jsonb) || EXCLUDED.metadata,
                    updated_at = NOW()
            """, user_id, goal_id, status, progress, json.dumps(metadata or {}))
            
            logger.info(f"Updated goal '{goal_slug}' for user {user_id}: {status} ({progress*100}%)")

class GoalAnalyzer:
    def __init__(self):
        self.llm = create_llm(temperature=0.0) # Deterministic
        self.parser = JsonOutputParser()
        
        self.prompt = ChatPromptTemplate.from_template("""
        You are an AI Goal Analyst. Your job is to evaluate if a conversation has advanced or completed specific goals.

        ACTIVE GOALS:
        {goals_context}

        RECENT CONVERSATION:
        {conversation_text}

        For each goal, determine:
        1. Has the success criteria been met? (status: "completed")
        2. Has significant progress been made? (status: "in_progress")
        3. Or no change? (status: "no_change")

        Return a JSON object with a list of updates:
        {{
            "updates": [
                {{
                    "slug": "goal_slug",
                    "status": "completed" | "in_progress" | "no_change",
                    "progress_score": 0.0 to 1.0,
                    "reasoning": "Why this status?",
                    "extracted_data": {{ "key": "value" }} (optional, e.g. if goal was to learn a name)
                }}
            ]
        }}
        """)
        
        self.chain = self.prompt | self.llm | self.parser

    async def check_goals(self, user_id: str, character_name: str, conversation_text: str):
        """
        Checks active goals against the recent conversation.
        """
        try:
            # 1. Get active goals
            active_goals = await goal_manager.get_active_goals(user_id, character_name)
            if not active_goals:
                return

            # Format goals for prompt
            goals_context = ""
            for g in active_goals:
                goals_context += f"- Slug: {g['slug']}\n  Description: {g['description']}\n  Criteria: {g['success_criteria']}\n\n"

            # 2. Run LLM Analysis
            result = await self.chain.ainvoke({
                "goals_context": goals_context,
                "conversation_text": conversation_text
            })
            
            # 3. Process Updates
            updates = result.get("updates", [])
            for update in updates:
                if update["status"] in ["completed", "in_progress"]:
                    await goal_manager.update_goal_progress(
                        user_id=user_id,
                        goal_slug=update["slug"],
                        character_name=character_name,
                        status=update["status"],
                        progress=update.get("progress_score", 0.0),
                        metadata={"reasoning": update.get("reasoning"), "extracted": update.get("extracted_data")}
                    )
                    
        except Exception as e:
            logger.error(f"Goal analysis failed: {e}")

goal_manager = GoalManager()
goal_analyzer = GoalAnalyzer()
