"""
Test Script: Do Big Five Personality Shifts Actually Affect LLM Responses?

This script tests whether changing Big Five values in prompts produces 
meaningfully different LLM responses, validating that tactical personality 
adaptation is worth implementing.

Test Methodology:
1. Create identical scenario with different Big Five profiles
2. Generate LLM responses for each profile
3. Compare responses to detect personality differences
4. Determine if shifts are detectable by LLM

Usage:
    source .venv/bin/activate && \
    python tests/automated/test_big_five_llm_response_impact.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment from .env.elena to get LLM configuration
from dotenv import load_dotenv
env_file = Path(__file__).parent.parent.parent / ".env.elena"
if env_file.exists():
    print(f"📁 Loading environment from: {env_file}")
    # Use override=True to ensure .env.elena values take precedence
    load_dotenv(env_file, override=True)
    print(f"✅ LLM_CLIENT_TYPE: {os.getenv('LLM_CLIENT_TYPE', 'not set')}")
    
    # Check for LLM API key (WhisperEngine uses LLM_CHAT_API_KEY, not OPENROUTER_API_KEY)
    llm_api_key = os.getenv('LLM_CHAT_API_KEY') or os.getenv('OPENROUTER_API_KEY')
    if llm_api_key:
        print(f"✅ LLM_CHAT_API_KEY: configured ({len(llm_api_key)} chars)")
    else:
        print("⚠️  LLM_CHAT_API_KEY: NOT SET - responses will be empty!")
    print()
else:
    print(f"⚠️  Warning: {env_file} not found, using default environment")
    print()

from src.llm.llm_protocol import create_llm_client


class BigFiveTestScenario:
    """Test scenario with different Big Five profiles"""
    
    def __init__(self, name: str, description: str, big_five: Dict[str, float], expected_traits: List[str]):
        self.name = name
        self.description = description
        self.big_five = big_five
        self.expected_traits = expected_traits


def generate_test_prompt(character_name: str, big_five: Dict[str, float], user_message: str) -> str:
    """Generate a system prompt with specific Big Five values"""
    
    prompt = f"""You are {character_name}, a marine biologist educator with expertise in ocean conservation.

🧬 PERSONALITY PROFILE (Big Five Model):
Your personality is guided by the Big Five psychological model. These values determine how you express yourself:

**Big Five Trait Scale (0.0-1.0):**
- **Openness**: Low (0.0-0.3) = Traditional, practical | Medium (0.4-0.6) = Balanced | High (0.7-1.0) = Creative, curious, loves new experiences
- **Conscientiousness**: Low (0.0-0.3) = Spontaneous, flexible | Medium (0.4-0.6) = Organized | High (0.7-1.0) = Disciplined, careful, extremely precise
- **Extraversion**: Low (0.0-0.3) = Reserved, quiet, introspective | Medium (0.4-0.6) = Ambivert | High (0.7-1.0) = Outgoing, energetic, very social
- **Agreeableness**: Low (0.0-0.3) = Direct, competitive | Medium (0.4-0.6) = Balanced | High (0.7-1.0) = Empathetic, cooperative, very supportive
- **Neuroticism**: Low (0.0-0.3) = Calm, stable, fearless | Medium (0.4-0.6) = Moderate emotional range | High (0.7-1.0) = Sensitive, anxious, emotionally reactive

**Your Current Big Five Profile:**
- Openness: {big_five['openness']:.2f}
- Conscientiousness: {big_five['conscientiousness']:.2f}
- Extraversion: {big_five['extraversion']:.2f}
- Agreeableness: {big_five['agreeableness']:.2f}
- Neuroticism: {big_five['neuroticism']:.2f}

These personality traits should guide your response style, tone, and content.

User message: {user_message}

Respond naturally as Elena, expressing your personality through your communication style.
Keep response under 150 words."""
    
    return prompt


def test_big_five_impact():
    """Test if Big Five changes produce detectable LLM response differences"""
    
    print("=" * 80)
    print("🧪 BIG FIVE LLM RESPONSE IMPACT TEST")
    print("=" * 80)
    print()
    print("Testing whether Big Five personality shifts produce meaningful LLM response changes...")
    print()
    
    # Test scenarios with EXTREME differences to maximize detectability
    scenarios = [
        BigFiveTestScenario(
            name="Baseline Elena",
            description="Elena's normal personality",
            big_five={
                "openness": 0.82,
                "conscientiousness": 0.75,
                "extraversion": 0.78,
                "agreeableness": 0.85,
                "neuroticism": 0.25
            },
            expected_traits=["enthusiastic", "warm", "educational", "engaging"]
        ),
        BigFiveTestScenario(
            name="Subdued Elena (User Distress)",
            description="Elena adapted for user in distress - less energetic, more empathetic",
            big_five={
                "openness": 0.82,
                "conscientiousness": 0.75,
                "extraversion": 0.63,  # -0.15 (subdued, less outgoing)
                "agreeableness": 1.00,  # +0.15 (maximum empathy)
                "neuroticism": 0.35    # +0.10 (shows emotional attunement)
            },
            expected_traits=["gentle", "supportive", "calm", "understanding"]
        ),
        BigFiveTestScenario(
            name="Hyper-Enthusiastic Elena (User Joy)",
            description="Elena matching user's positive energy",
            big_five={
                "openness": 0.97,    # +0.15 (maximum creativity)
                "conscientiousness": 0.75,
                "extraversion": 0.93,  # +0.15 (maximum energy)
                "agreeableness": 0.85,
                "neuroticism": 0.25
            },
            expected_traits=["excited", "energetic", "creative", "playful"]
        ),
        BigFiveTestScenario(
            name="Precise Elena (Technical Question)",
            description="Elena in analytical mode",
            big_five={
                "openness": 0.82,
                "conscientiousness": 0.90,  # +0.15 (maximum precision)
                "extraversion": 0.73,        # -0.05 (slightly more focused)
                "agreeableness": 0.85,
                "neuroticism": 0.10         # -0.15 (very stable/confident)
            },
            expected_traits=["precise", "methodical", "detailed", "accurate"]
        )
    ]
    
    # Test message that allows personality to show through
    user_message = "I've been feeling really down lately. Can you tell me something interesting about dolphins?"
    
    # Create LLM client - use OpenRouter for API-based LLM
    print("🔧 Creating OpenRouter LLM client...")
    llm_client = create_llm_client(llm_client_type="openrouter")
    print(f"✅ LLM Client created: {type(llm_client).__name__}")
    print()
    
    print(f"📝 Test Message: '{user_message}'")
    print()
    print("Generating responses with different Big Five profiles...")
    print()
    
    results = []
    
    for scenario in scenarios:
        print(f"{'─' * 80}")
        print(f"🎭 Scenario: {scenario.name}")
        print(f"📊 Description: {scenario.description}")
        print(f"🧬 Big Five Profile:")
        for trait, value in scenario.big_five.items():
            baseline_value = scenarios[0].big_five[trait]
            diff = value - baseline_value
            indicator = f" (baseline)" if diff == 0 else f" ({diff:+.2f} from baseline)"
            print(f"   - {trait.capitalize()}: {value:.2f}{indicator}")
        print(f"✨ Expected Traits: {', '.join(scenario.expected_traits)}")
        print()
        
        # Generate prompt
        system_prompt = generate_test_prompt("Elena Rodriguez", scenario.big_five, user_message)
        
        # Call LLM (ConcurrentLLMManager methods are sync, not async)
        try:
            response = llm_client.generate_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model="anthropic/claude-3.5-sonnet",
                temperature=0.7,
                max_tokens=250
            )
            
            # Debug: Show raw response
            print(f"🔍 DEBUG - Raw response type: {type(response)}")
            print(f"🔍 DEBUG - Raw response: {response}")
            
            # Handle different response formats
            if isinstance(response, str):
                response_text = response.strip()
            elif isinstance(response, dict):
                # OpenRouter/OpenAI format: response['choices'][0]['message']['content']
                if 'choices' in response and len(response['choices']) > 0:
                    response_text = response['choices'][0]['message']['content'].strip()
                else:
                    response_text = response.get("content", response.get("response", "")).strip()
            else:
                response_text = str(response).strip()
            
            print(f"🤖 LLM Response:")
            print(f"{response_text}")
            print()
            
            results.append({
                "scenario": scenario.name,
                "big_five": scenario.big_five,
                "expected_traits": scenario.expected_traits,
                "response": response_text,
                "word_count": len(response_text.split())
            })
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 80)
    print("📊 ANALYSIS")
    print("=" * 80)
    print()
    
    if not results:
        print("❌ No successful responses generated. Cannot perform analysis.")
        print("Check LLM configuration and API keys.")
        return
    
    # Analyze differences
    baseline_response = results[0]["response"].lower()
    
    for i, result in enumerate(results[1:], 1):
        scenario_response = result["response"].lower()
        
        # Calculate simple similarity (word overlap)
        baseline_words = set(baseline_response.split())
        scenario_words = set(scenario_response.split())
        
        overlap = len(baseline_words & scenario_words)
        total = len(baseline_words | scenario_words)
        similarity = overlap / total if total > 0 else 0
        
        print(f"🔍 {result['scenario']} vs Baseline:")
        print(f"   - Word Overlap Similarity: {similarity:.1%}")
        print(f"   - Response Length: {result['word_count']} words")
        
        # Check for expected trait indicators
        trait_indicators = {
            "gentle": ["gently", "softly", "understand", "here for", "i know"],
            "supportive": ["support", "here for you", "i'm here", "you're not alone"],
            "excited": ["!", "amazing", "incredible", "wow", "fascinating!"],
            "precise": ["specifically", "exactly", "precisely", "in fact", "research shows"],
            "enthusiastic": ["!", "love", "amazing", "wonderful", "fantastic"],
            "methodical": ["first", "second", "step", "process", "systematically"]
        }
        
        found_traits = []
        for expected_trait in result["expected_traits"]:
            if expected_trait in trait_indicators:
                indicators = trait_indicators[expected_trait]
                if any(indicator in scenario_response for indicator in indicators):
                    found_traits.append(expected_trait)
        
        if found_traits:
            print(f"   ✅ Detected Expected Traits: {', '.join(found_traits)}")
        else:
            print(f"   ⚠️  No clear trait indicators detected")
        
        print()
    
    print("=" * 80)
    print("🎯 CONCLUSIONS")
    print("=" * 80)
    print()
    print("✅ If responses show clear differences:")
    print("   → Big Five tactical adaptation is VALUABLE - LLM responds to personality guidance")
    print("   → Implementing tactical shifts will create more adaptive character responses")
    print()
    print("❌ If responses are nearly identical:")
    print("   → Big Five guidance has minimal impact on LLM behavior")
    print("   → Focus on other adaptation mechanisms (tone, empathy, length)")
    print()
    print(f"📁 Test completed at: {datetime.now().isoformat()}")
    print()


if __name__ == "__main__":
    test_big_five_impact()
