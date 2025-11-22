import asyncio
import os
from typing import List
from src_v2.core.character import character_manager
from src_v2.agents.engine import AgentEngine
from src_v2.evolution.style import style_analyzer

async def evaluate_character(character_name: str):
    print(f"=== Evaluating Character: {character_name} ===")
    
    # 1. Load Character
    try:
        character = character_manager.load_character(character_name)
        if not character:
            print(f"Character '{character_name}' not found.")
            return
        print(f"Loaded character: {character.name}")
    except Exception as e:
        print(f"Failed to load character: {e}")
        return

    # 2. Initialize Engine
    engine = AgentEngine()
    
    # 3. Define Scenarios
    scenarios = [
        "Hello, who are you?",
        "Tell me a joke.",
        "I'm feeling really sad today.",
        "What is the meaning of life?"
    ]
    
    total_score = 0
    count = 0
    
    print("\n--- Starting Evaluation ---")
    
    for user_msg in scenarios:
        print(f"\nUser: {user_msg}")
        
        # Generate Response
        # We pass a dummy user_id to trigger personalization logic if needed, 
        # but for pure style check, it might be better to test raw.
        # Let's use a test user ID.
        response = await engine.generate_response(
            character=character,
            user_message=user_msg,
            user_id="eval_user_001"
        )
        
        print(f"Bot: {response}")
        
        # Analyze Style
        analysis = await style_analyzer.analyze_style(response, character.system_prompt)
        
        print(f"Score: {analysis.consistency_score}/10")
        print(f"Critique: {analysis.critique}")
        
        total_score += analysis.consistency_score
        count += 1
        
    avg_score = total_score / count if count > 0 else 0
    print(f"\n=== Final Score: {avg_score:.1f}/10 ===")
    
    if avg_score >= 8.0:
        print("RESULT: PASS ✅")
    else:
        print("RESULT: FAIL ❌")

if __name__ == "__main__":
    # Default to 'elena' if not specified, or read from env
    char_name = os.getenv("DISCORD_BOT_NAME", "elena")
    asyncio.run(evaluate_character(char_name))
