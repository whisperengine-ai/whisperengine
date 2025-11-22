import asyncio
import os
from src_v2.evolution.style import style_analyzer

async def test_style_analyzer():
    print("Testing Style Analyzer...")
    
    character_def = """
    Name: GrumpyBot
    Personality: Cynical, sarcastic, hates mornings.
    Voice: Uses short sentences. Never uses emojis.
    """
    
    # Test 1: Bad Response (Happy, emojis)
    bad_response = "Good morning! ☀️ I hope you have a wonderful day! 😊"
    print(f"\nAnalyzing Bad Response: '{bad_response}'")
    result_bad = await style_analyzer.analyze_style(bad_response, character_def)
    print(f"Scores: Consistency={result_bad.consistency_score}, Tone={result_bad.tone_score}")
    print(f"Critique: {result_bad.critique}")
    
    # Test 2: Good Response
    good_response = "It's morning. Don't talk to me until I've had coffee."
    print(f"\nAnalyzing Good Response: '{good_response}'")
    result_good = await style_analyzer.analyze_style(good_response, character_def)
    print(f"Scores: Consistency={result_good.consistency_score}, Tone={result_good.tone_score}")
    print(f"Critique: {result_good.critique}")

if __name__ == "__main__":
    asyncio.run(test_style_analyzer())
