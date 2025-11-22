import asyncio
import os
from dotenv import load_dotenv

# Load .env.elena file
load_dotenv(".env.elena")

# Force OpenRouter if using OpenRouter key (common in this dev env)
# We check if the key looks like an OpenRouter key
api_key = os.getenv("OPENAI_API_KEY", "") or os.getenv("LLM_API_KEY", "")
if api_key.startswith("sk-or-v1"):
    os.environ["LLM_PROVIDER"] = "openrouter"
    print("   ℹ️ Detected OpenRouter key, forcing LLM_PROVIDER='openrouter'")

from src_v2.evolution.goals import goal_manager, goal_analyzer
from src_v2.core.database import db_manager

# Set env vars for V2 (override if needed, but .env should have them)
# We force these just in case .env has V1 values
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_DB"] = "whisperengine_v2"
os.environ["POSTGRES_USER"] = "whisper"
os.environ["POSTGRES_PASSWORD"] = "password"
os.environ["DISCORD_BOT_NAME"] = "elena"

async def main():
    print("--- Testing Goal System ---")
    
    # 1. Connect DB
    await db_manager.connect_postgres()
    
    try:
        user_id = "test_user_123"
        character_name = "elena"
        
        # 2. Ensure Goals Exist
        print("\n1. Ensuring goals exist...")
        await goal_manager.ensure_goals_exist(character_name)
        
        # 3. Get Active Goals (Should be all default ones)
        print("\n2. Fetching active goals...")
        goals = await goal_manager.get_active_goals(user_id, character_name)
        for g in goals:
            print(f"   - {g['slug']}: {g['status']} (Priority: {g['priority']})")
            
        if not goals:
            print("   ❌ No goals found!")
            return

        # 4. Simulate Conversation (Goal: learn_name)
        print("\n3. Simulating conversation (User states name)...")
        conversation = """
        AI: Hi there! I'm Elena. What's your name?
        User: My name is Mark.
        """
        
        # 5. Run Analyzer
        print("   Running GoalAnalyzer...")
        await goal_analyzer.check_goals(user_id, character_name, conversation)
        
        # 6. Check Progress Again
        print("\n4. Checking progress after analysis...")
        goals_after = await goal_manager.get_active_goals(user_id, character_name)
        
        # Note: If status is 'completed', it won't show up in get_active_goals
        # So we check the DB directly or check if the list is smaller
        
        found_learn_name = False
        for g in goals_after:
            print(f"   - {g['slug']}: {g['status']}")
            if g['slug'] == 'learn_name':
                found_learn_name = True
        
        if not found_learn_name:
            print("   ✅ 'learn_name' goal is no longer active (Completed!)")
        else:
            print("   ⚠️ 'learn_name' goal is still active (Analysis might have failed or LLM didn't see it)")

    finally:
        await db_manager.disconnect_all()

if __name__ == "__main__":
    asyncio.run(main())
