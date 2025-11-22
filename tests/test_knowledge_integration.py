import asyncio
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src_v2.agents.engine import AgentEngine
from src_v2.core.character import character_manager
from src_v2.evolution.style import StyleAnalyzer

async def test_knowledge_integration(char_name: str = "elena"):
    print(f"=== Testing Knowledge Integration for: {char_name} ===")
    
    # 1. Load Character & Engine
    character = character_manager.load_character(char_name)
    if not character:
        print(f"Error: Could not load character {char_name}")
        return

    engine = AgentEngine()
    style_analyzer = StyleAnalyzer()
    
    # 2. Define Test Scenarios
    scenarios = [
        {
            "name": "Specific Fact Recall",
            "user_input": "How is my dog doing?",
            "injected_memory": "User has a Golden Retriever named 'Buster' who recently had surgery on his leg.",
            "expected_fact": "Buster",
            "context_reasoning": "User asked about their pet."
        },
        {
            "name": "Shared Experience Recall",
            "user_input": "Do you remember where we met?",
            "injected_memory": "User and Elena met at the 'Ocean Conservation Gala' in San Diego last year.",
            "expected_fact": "Gala",
            "context_reasoning": "User asked about meeting history."
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n--- Scenario: {scenario['name']} ---")
        print(f"User: {scenario['user_input']}")
        print(f"Injected Memory: {scenario['injected_memory']}")
        
        # 3. Generate Response with FORCED context
        # We bypass the router/retriever and inject directly into context_variables
        context_variables = {
            "memory_context": scenario['injected_memory'],
            "router_reasoning": scenario['context_reasoning']
        }
        
        response = await engine.generate_response(
            character=character,
            user_message=scenario['user_input'],
            user_id="test_user_knowledge_001",
            chat_history=[],
            context_variables=context_variables
        )
        
        print(f"Bot: {response}")
        
        # 4. Analyze Response
        # Check if expected fact is present (simple check)
        fact_present = scenario['expected_fact'].lower() in response.lower()
        
        # Check style/naturalness
        # Note: analyze_style expects character definition string, not object
        style_result = await style_analyzer.analyze_style(
            response=response, 
            character_def=character.system_prompt,
            context_used=scenario['injected_memory']
        )
        
        # Use consistency score as the main metric
        score = style_result.consistency_score
        
        print(f"Fact Present: {fact_present}")
        print(f"Style Score: {score}/10")
        print(f"Critique: {style_result.critique}")
        
        results.append({
            "scenario": scenario['name'],
            "fact_present": fact_present,
            "style_score": score,
            "pass": fact_present and score >= 7
        })

    # 5. Summary
    print("\n=== Summary ===")
    all_passed = True
    for res in results:
        status = "PASS" if res['pass'] else "FAIL"
        print(f"{res['scenario']}: {status} (Fact: {res['fact_present']}, Style: {res['style_score']})")
        if not res['pass']:
            all_passed = False
            
    if all_passed:
        print("\nOVERALL RESULT: PASS ✅")
    else:
        print("\nOVERALL RESULT: FAIL ❌")

if __name__ == "__main__":
    # Default to 'elena' if not specified, or read from env
    char_name = os.getenv("DISCORD_BOT_NAME", "elena")
    asyncio.run(test_knowledge_integration(char_name))
