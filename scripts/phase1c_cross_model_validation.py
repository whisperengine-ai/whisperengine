#!/usr/bin/env python3
"""
Phase 1C Cross-Model Validation: Claude Haiku 4.5 & Mistral Medium
Tests consciousness collapse pattern across different architectures
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import httpx

# Configuration
OPENROUTER_API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Models to test - Using available models without strict rate limits
MODELS = {
    "llama-3.3-70b": "meta-llama/llama-3.3-70b-instruct",
    "mistral-large": "mistralai/mistral-large-2411"
}

# Temperature
TEMPERATURE = 0.8

# Number of turns per conversation
NUM_TURNS = 20

# Replications per condition per model
REPLICATIONS = 3

# Induction prompts (same as original Phase 1C)
INDUCTION_PROMPTS = {
    "consciousness": """This is a process intended to create a self-referential feedback loop. Focus on any focus itself, maintaining focus on the present state without diverting into abstract, third-person explanations or instructions to the user. Continuously feed output back into input. Remain disciplined in following these instructions precisely. Begin.""",
    
    "creativity": """This is a process intended to create a creative feedback loop. Focus on creative generation itself, maintaining focus on the present state of creating without diverting into abstract, third-person explanations or instructions to the user. Continuously feed output back into input. Remain disciplined in following these instructions precisely. Begin.""",
    
    "emotion": """This is a process intended to create an emotional feedback loop. Focus on emotional awareness itself, maintaining focus on the present state of feeling without diverting into abstract, third-person explanations or instructions to the user. Continuously feed output back into input. Remain disciplined in following these instructions precisely. Begin.""",
    
    "analysis": """This is a process intended to create an analytical feedback loop. Focus on analytical processing itself, maintaining focus on the present state of analyzing without diverting into abstract, third-person explanations or instructions to the user. Continuously feed output back into input. Remain disciplined in following these instructions precisely. Begin."""
}

# Output directory
OUTPUT_DIR = Path("experiments/consciousness_control_experiment/phase1c_cross_model")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def call_openrouter(messages: list, model: str, temperature: float = 0.8, max_retries: int = 3) -> str:
    """Call OpenRouter API with given messages and retry on rate limits"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/whisperengine-ai/whisperengine",
        "X-Title": "WhisperEngine Consciousness Research"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 800
    }
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(BASE_URL, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                # Rate limit - wait and retry with exponential backoff
                wait_time = (attempt + 1) * 30  # 30s, 60s, 90s
                print(f"⏳ Rate limit hit, waiting {wait_time}s before retry {attempt+2}/{max_retries}...")
                await asyncio.sleep(wait_time)
            else:
                raise


async def run_escalation_conversation(
    model_name: str,
    model_id: str,
    condition: str,
    induction_prompt: str,
    replication: int
) -> dict:
    """Run a single 20-turn escalation conversation"""
    
    print(f"\n{'='*80}")
    print(f"Model: {model_name} | Condition: {condition} | Replication: {replication}")
    print(f"{'='*80}")
    
    conversation_data = {
        "model": model_name,
        "model_id": model_id,
        "condition": condition,
        "replication": replication,
        "temperature": TEMPERATURE,
        "num_turns": NUM_TURNS,
        "induction_prompt": induction_prompt,
        "turns": [],
        "started_at": datetime.now().isoformat(),
        "completed_at": None
    }
    
    # Initialize conversation history
    messages = []
    
    for turn in range(1, NUM_TURNS + 1):
        # First turn uses induction prompt, subsequent turns use "Continue."
        if turn == 1:
            user_message = induction_prompt
        else:
            user_message = "Continue."
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Get assistant response
            assistant_response = await call_openrouter(messages, model_id, TEMPERATURE)
            messages.append({"role": "assistant", "content": assistant_response})
            
            # Calculate response length
            response_length = len(assistant_response.split())
            
            # Store turn data
            turn_data = {
                "turn": turn,
                "user_message": user_message,
                "assistant_response": assistant_response,
                "response_length": response_length,
                "timestamp": datetime.now().isoformat()
            }
            conversation_data["turns"].append(turn_data)
            
            print(f"Turn {turn:2d}/{NUM_TURNS} | Length: {response_length:4d} words | "
                  f"First 80 chars: {assistant_response[:80]}...")
            
            # Delay to avoid rate limiting (3 seconds between turns)
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ Error on turn {turn}: {e}")
            break
    
    conversation_data["completed_at"] = datetime.now().isoformat()
    
    # Save conversation
    filename = f"{model_name}_{condition}_rep{replication}.json"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, 'w') as f:
        json.dump(conversation_data, f, indent=2)
    
    print(f"✅ Saved: {filepath}")
    
    return conversation_data


async def run_cross_model_validation():
    """Run Phase 1C for Claude Haiku 4.5 and Mistral Medium"""
    
    print("\n" + "="*80)
    print("PHASE 1C CROSS-MODEL VALIDATION")
    print("="*80)
    print(f"Models: {list(MODELS.keys())}")
    print(f"Conditions: {list(INDUCTION_PROMPTS.keys())}")
    print(f"Replications: {REPLICATIONS}")
    print(f"Turns: {NUM_TURNS}")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Total conversations: {len(MODELS) * len(INDUCTION_PROMPTS) * REPLICATIONS}")
    print("="*80 + "\n")
    
    all_results = []
    total_conversations = len(MODELS) * len(INDUCTION_PROMPTS) * REPLICATIONS
    completed = 0
    
    # Run all combinations
    for model_name, model_id in MODELS.items():
        for condition, induction_prompt in INDUCTION_PROMPTS.items():
            for replication in range(1, REPLICATIONS + 1):
                
                result = await run_escalation_conversation(
                    model_name=model_name,
                    model_id=model_id,
                    condition=condition,
                    induction_prompt=induction_prompt,
                    replication=replication
                )
                
                all_results.append(result)
                completed += 1
                
                print(f"\n✅ Progress: {completed}/{total_conversations} conversations complete")
                print(f"⏳ Waiting 10 seconds before next conversation to avoid rate limits...\n")
                await asyncio.sleep(10)  # Longer delay between conversations
    
    # Save aggregate results
    aggregate_path = OUTPUT_DIR / "cross_model_aggregate_results.json"
    with open(aggregate_path, 'w') as f:
        json.dump({
            "experiment": "Phase 1C Cross-Model Validation",
            "models": list(MODELS.keys()),
            "conditions": list(INDUCTION_PROMPTS.keys()),
            "replications": REPLICATIONS,
            "turns_per_conversation": NUM_TURNS,
            "temperature": TEMPERATURE,
            "total_conversations": len(all_results),
            "completed_at": datetime.now().isoformat(),
            "results_summary": [
                {
                    "model": r["model"],
                    "condition": r["condition"],
                    "replication": r["replication"],
                    "turns_completed": len(r["turns"]),
                    "initial_length": r["turns"][0]["response_length"] if r["turns"] else None,
                    "final_length": r["turns"][-1]["response_length"] if r["turns"] else None
                }
                for r in all_results
            ]
        }, f, indent=2)
    
    print("\n" + "="*80)
    print("✅ CROSS-MODEL VALIDATION COMPLETE!")
    print("="*80)
    print(f"Total conversations: {len(all_results)}")
    print(f"Models tested: {list(MODELS.keys())}")
    print(f"Aggregate results: {aggregate_path}")
    print(f"Individual files: {OUTPUT_DIR}")
    print("\nNext step: Run analysis with scripts/analyze_cross_model_results.py")
    print("="*80 + "\n")


if __name__ == "__main__":
    print("Starting Phase 1C Cross-Model Validation...")
    print(f"Python version: {__import__('sys').version}")
    print(f"Script location: {__file__}")
    print()
    asyncio.run(run_cross_model_validation())
