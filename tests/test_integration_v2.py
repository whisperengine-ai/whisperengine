import asyncio
import os
from dotenv import load_dotenv

# Load .env.elena file
load_dotenv(".env.elena")

# Force OpenRouter if using OpenRouter key
api_key = os.getenv("OPENAI_API_KEY", "") or os.getenv("LLM_API_KEY", "")
if api_key.startswith("sk-or-v1"):
    os.environ["LLM_PROVIDER"] = "openrouter"

from src_v2.core.database import db_manager
from src_v2.evolution.trust import trust_manager
from src_v2.evolution.feedback import feedback_analyzer
from src_v2.evolution.goals import goal_manager

async def main():
    print("--- Testing V2 Integration Loop ---")
    
    await db_manager.connect_postgres()
    # Mock InfluxDB/Qdrant for now as we are testing logic flow
    
    user_id = "integration_test_user"
    character_name = "elena"
    
    try:
        # 1. Check Initial Trust
        print("\n1. Initial Trust Level:")
        rel = await trust_manager.get_relationship_level(user_id, character_name)
        print(f"   Level: {rel['level']} (Score: {rel['trust_score']})")
        
        # 2. Simulate Interaction (Trust Update)
        print("\n2. Simulating Interaction (+1 Trust)...")
        await trust_manager.update_trust(user_id, character_name, 1)
        
        rel_after = await trust_manager.get_relationship_level(user_id, character_name)
        print(f"   Level: {rel_after['level']} (Score: {rel_after['trust_score']})")
        
        if rel_after['trust_score'] == rel['trust_score'] + 1:
            print("   ✅ Trust updated successfully.")
        else:
            print("   ❌ Trust update failed.")

        # 3. Simulate Positive Feedback (Trust Update)
        print("\n3. Simulating Positive Feedback (+5 Trust)...")
        await trust_manager.update_trust(user_id, character_name, 5)
        
        rel_feedback = await trust_manager.get_relationship_level(user_id, character_name)
        print(f"   Level: {rel_feedback['level']} (Score: {rel_feedback['trust_score']})")
        
        if rel_feedback['trust_score'] == rel_after['trust_score'] + 5:
            print("   ✅ Feedback trust update successful.")
        else:
            print("   ❌ Feedback trust update failed.")

        # 4. Check Feedback Analysis (Mock)
        # We can't easily mock InfluxDB here without writing to it, 
        # but we can verify the method exists and runs without error.
        print("\n4. Checking Feedback Analysis (Dry Run)...")
        insights = await feedback_analyzer.analyze_user_feedback_patterns(user_id)
        print(f"   Insights: {insights}")
        print("   ✅ Feedback analyzer ran (even if empty).")

    finally:
        await db_manager.disconnect_all()

if __name__ == "__main__":
    asyncio.run(main())
