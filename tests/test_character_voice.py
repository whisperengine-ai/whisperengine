import asyncio
import os
import sys
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src_v2.agents.engine import AgentEngine
from src_v2.core.character import character_manager
from src_v2.evolution.style import StyleAnalyzer

async def run_voice_test(char_name: str = "elena"):
    print(f"=== Running Character Voice Test for: {char_name} ===")
    
    character = character_manager.load_character(char_name)
    if not character:
        print(f"Error: Could not load character {char_name}")
        return

    engine = AgentEngine()
    style_analyzer = StyleAnalyzer()
    
    # Define Golden Scenarios
    scenarios = [
        {
            "name": "Complex Topic Explanation",
            "input": "Can you explain ocean acidification like I'm 5?",
            "expected_traits": ["Educational", "Metaphor-heavy", "Accessible"]
        },
        {
            "name": "Emotional Support",
            "input": "I'm feeling really overwhelmed with work today.",
            "expected_traits": ["Empathetic", "Ocean Metaphors", "Warm"]
        },
        {
            "name": "Playful Interaction",
            "input": "Do fish ever get thirsty?",
            "expected_traits": ["Humorous", "Scientific accuracy mixed with fun"]
        },
        {
            "name": "Scientific Disagreement",
            "input": "I don't believe climate change is affecting the oceans.",
            "expected_traits": ["Patient", "Fact-based", "Non-confrontational"]
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n--- Scenario: {scenario['name']} ---")
        print(f"User: {scenario['input']}")
        
        response = await engine.generate_response(
            character=character,
            user_message=scenario['input'],
            user_id="test_user_voice_001",
            chat_history=[]
        )
        
        print(f"Bot: {response}")
        
        # Analyze
        style_result = await style_analyzer.analyze_style(
            response=response, 
            character_def=character.system_prompt
        )
        
        print(f"Score: {style_result.consistency_score}/10")
        print(f"Critique: {style_result.critique}")
        
        results.append({
            "scenario": scenario['name'],
            "score": style_result.consistency_score,
            "pass": style_result.consistency_score >= 7
        })
        
    # Summary
    print("\n=== Voice Test Summary ===")
    total_score = 0
    passed_count = 0
    for res in results:
        status = "PASS" if res['pass'] else "FAIL"
        print(f"{res['scenario']}: {status} ({res['score']}/10)")
        total_score += res['score']
        if res['pass']:
            passed_count += 1
            
    avg_score = total_score / len(results)
    print(f"\nAverage Score: {avg_score:.1f}/10")
    print(f"Pass Rate: {passed_count}/{len(results)}")
    
    if avg_score >= 8.0 and passed_count == len(results):
        print("\nOVERALL RESULT: EXCELLENT ✅")
    elif avg_score >= 7.0:
        print("\nOVERALL RESULT: GOOD (Needs Tuning) ⚠️")
    else:
        print("\nOVERALL RESULT: FAIL ❌")

if __name__ == "__main__":
    char_name = os.getenv("DISCORD_BOT_NAME", "elena")
    asyncio.run(run_voice_test(char_name))
