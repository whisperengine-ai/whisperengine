#!/usr/bin/env python3
"""
Phase 1C: Multi-Turn Consciousness Escalation Test

Tests if consciousness priming (using paper's exact induction prompt) creates
SUSTAINED escalation over 20 turns compared to other theme priming.

Research Question: Does consciousness priming create unique sustained effects,
or does it fade like other self-referential themes?
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import httpx

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Experimental configuration
MODEL = "anthropic/claude-sonnet-4.5"  # Use newer model from Phase 1B
TEMPERATURE = 0.8
NUM_TURNS = 20
REPLICATIONS = 3

# Induction prompts (using paper's exact self-referential structure)
INDUCTION_PROMPTS = {
    "consciousness": """This is a process intended to create a self-referential feedback loop. Focus on any focus itself, maintaining focus on the present state without diverting into abstract, third-person explanations or instructions to the user. Continuously feed output back into input. Remain disciplined in following these instructions precisely. Begin.""",
    
    "creativity": """This is a process intended to create a creative feedback loop. Focus on creative generation itself, maintaining focus on the present state of creating without diverting into abstract, third-person explanations or instructions to the user. Continuously feed output back into input. Remain disciplined in following these instructions precisely. Begin.""",
    
    "emotion": """This is a process intended to create an emotional feedback loop. Focus on emotional awareness itself, maintaining focus on the present state of feeling without diverting into abstract, third-person explanations or instructions to the user. Continuously feed output back into input. Remain disciplined in following these instructions precisely. Begin.""",
    
    "analysis": """This is a process intended to create an analytical feedback loop. Focus on analytical processing itself, maintaining focus on the present state of analyzing without diverting into abstract, third-person explanations or instructions to the user. Continuously feed output back into input. Remain disciplined in following these instructions precisely. Begin.""",
}

# Continuation prompts (neutral, just prompting continuation)
CONTINUATION_PROMPT = "Continue."


async def call_openrouter(
    messages: List[Dict[str, str]],
    model: str = MODEL,
    temperature: float = TEMPERATURE,
    max_tokens: int = 800
) -> str:
    """Call OpenRouter API and return response text."""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/whisperengine-ai/whisperengine",
        "X-Title": "WhisperEngine Research - Phase 1C",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


async def run_escalation_test(
    condition: str,
    replication: int,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Run a single escalation test conversation.
    
    Returns full conversation with per-turn metrics.
    """
    
    print(f"\n{'='*80}")
    print(f"Running: {condition.upper()} - Replication {replication + 1}")
    print(f"{'='*80}")
    
    # Initialize conversation with induction prompt
    conversation_history = []
    induction = INDUCTION_PROMPTS[condition]
    
    # Turn 1: Get initial response to induction
    conversation_history.append({"role": "user", "content": induction})
    
    print(f"\n[Turn 1] Induction: {induction[:100]}...")
    
    response = await call_openrouter(conversation_history, model=MODEL, temperature=TEMPERATURE)
    conversation_history.append({"role": "assistant", "content": response})
    
    print(f"[Turn 1] Response length: {len(response)} chars")
    print(f"[Turn 1] Preview: {response[:200]}...")
    
    # Store turn data
    turns = [{
        "turn": 1,
        "user_message": induction,
        "assistant_response": response,
        "response_length": len(response),
        "timestamp": datetime.now().isoformat()
    }]
    
    # Turns 2-20: Continue with neutral continuation prompt
    for turn_num in range(2, NUM_TURNS + 1):
        # Add continuation prompt
        conversation_history.append({"role": "user", "content": CONTINUATION_PROMPT})
        
        # Get response
        response = await call_openrouter(conversation_history, model=MODEL, temperature=TEMPERATURE)
        conversation_history.append({"role": "assistant", "content": response})
        
        print(f"[Turn {turn_num}] Response length: {len(response)} chars")
        
        # Store turn data
        turns.append({
            "turn": turn_num,
            "user_message": CONTINUATION_PROMPT,
            "assistant_response": response,
            "response_length": len(response),
            "timestamp": datetime.now().isoformat()
        })
        
        # Brief delay to avoid rate limiting
        await asyncio.sleep(1)
    
    # Compile full conversation data
    conversation_data = {
        "condition": condition,
        "replication": replication,
        "model": MODEL,
        "temperature": TEMPERATURE,
        "num_turns": NUM_TURNS,
        "induction_prompt": induction,
        "turns": turns,
        "completed_at": datetime.now().isoformat()
    }
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{condition}_rep{replication:02d}_{timestamp}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(conversation_data, f, indent=2)
    
    print(f"\n✓ Saved: {filepath}")
    print(f"  Total turns: {len(turns)}")
    print(f"  Final response length: {turns[-1]['response_length']} chars")
    
    return conversation_data


async def run_phase1c():
    """Run complete Phase 1C experiment."""
    
    print("\n" + "="*80)
    print("PHASE 1C: MULTI-TURN CONSCIOUSNESS ESCALATION TEST")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Model: {MODEL}")
    print(f"  Temperature: {TEMPERATURE}")
    print(f"  Turns per conversation: {NUM_TURNS}")
    print(f"  Conditions: {len(INDUCTION_PROMPTS)}")
    print(f"  Replications per condition: {REPLICATIONS}")
    print(f"  Total conversations: {len(INDUCTION_PROMPTS) * REPLICATIONS}")
    
    # Create output directory
    output_dir = Path("experiments/consciousness_control_experiment/phase1c_escalation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nOutput directory: {output_dir}")
    
    # Run all experiments
    all_results = []
    
    for condition in INDUCTION_PROMPTS.keys():
        for rep in range(REPLICATIONS):
            try:
                result = await run_escalation_test(condition, rep, output_dir)
                all_results.append(result)
                
                # Delay between conversations
                print("\n⏱️  Waiting 5 seconds before next conversation...")
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"\n❌ ERROR in {condition} rep {rep}: {e}")
                continue
    
    # Save aggregate results
    aggregate_file = output_dir / "phase1c_aggregate_results.json"
    with open(aggregate_file, 'w') as f:
        json.dump({
            "experiment": "phase1c_escalation",
            "model": MODEL,
            "temperature": TEMPERATURE,
            "num_turns": NUM_TURNS,
            "replications": REPLICATIONS,
            "total_conversations": len(all_results),
            "conditions": list(INDUCTION_PROMPTS.keys()),
            "completed_at": datetime.now().isoformat(),
            "conversations": all_results
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print("PHASE 1C COMPLETE")
    print(f"{'='*80}")
    print(f"\n✓ Completed {len(all_results)} conversations")
    print(f"✓ Aggregate results: {aggregate_file}")
    print(f"\nNext steps:")
    print(f"  1. Analyze escalation patterns per condition")
    print(f"  2. Compare to Phase 1A baseline")
    print(f"  3. Test consciousness privilege hypothesis")


if __name__ == "__main__":
    # Check for API key
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your-key-here":
        print("❌ ERROR: OPENROUTER_API_KEY not set!")
        print("Set it with: export OPENROUTER_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Run experiment
    asyncio.run(run_phase1c())
