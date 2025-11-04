"""
Test suite to measure impact of intensity amplifier boost (1.3x multiplier).

This test validates whether the 1.3x emotion boost when intensity amplifiers 
(very, really, extremely, etc.) are present is still necessary with adaptive
emotion thresholding, or if it creates false positives.

Run with:
    source .venv/bin/activate && \
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
    export QDRANT_HOST="localhost" && \
    export QDRANT_PORT="6334" && \
    export POSTGRES_HOST="localhost" && \
    export POSTGRES_PORT="5433" && \
    export DISCORD_BOT_NAME=elena && \
    python tests/automated/test_intensity_amplifier_impact.py
"""

import asyncio
import logging
from typing import Dict, List, Tuple
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class IntensityAmplifierTester:
    """Test intensity amplifier impact with and without the 1.3x boost."""
    
    def __init__(self):
        self.analyzer = EnhancedVectorEmotionAnalyzer()
        self.test_cases = self._create_test_cases()
        
    def _create_test_cases(self) -> List[Dict]:
        """
        Create test cases covering various scenarios with intensity amplifiers.
        
        Categories:
        1. Genuine intensifiers (should boost legitimate emotions)
        2. Neutral with intensifiers (should NOT create false emotions)
        3. Weak emotions with intensifiers (edge cases)
        4. No intensifiers baseline (control group)
        """
        return [
            # === GENUINE INTENSIFIERS (Legitimate boost cases) ===
            {
                "text": "I'm extremely happy about this news!",
                "category": "genuine_positive",
                "expected_emotion": "joy",
                "expected_behavior": "Should detect joy strongly",
                "has_amplifier": True
            },
            {
                "text": "This is really frustrating and I'm very angry",
                "category": "genuine_negative",
                "expected_emotion": "anger",
                "expected_behavior": "Should detect anger strongly",
                "has_amplifier": True
            },
            {
                "text": "I'm so incredibly excited about the trip!",
                "category": "genuine_excitement",
                "expected_emotion": "joy",
                "expected_behavior": "Should detect joy/anticipation strongly",
                "has_amplifier": True
            },
            {
                "text": "I'm absolutely terrified of what might happen",
                "category": "genuine_fear",
                "expected_emotion": "fear",
                "expected_behavior": "Should detect fear strongly",
                "has_amplifier": True
            },
            
            # === NEUTRAL WITH INTENSIFIERS (Should NOT boost to false emotion) ===
            {
                "text": "The meeting is scheduled for 3pm on Tuesday, very important to remember",
                "category": "neutral_factual",
                "expected_emotion": "neutral",
                "expected_behavior": "Should stay neutral despite 'very'",
                "has_amplifier": True
            },
            {
                "text": "It's really quite straightforward - just follow the steps",
                "category": "neutral_instruction",
                "expected_emotion": "neutral",
                "expected_behavior": "Should stay neutral despite 'really'",
                "has_amplifier": True
            },
            {
                "text": "The report is extremely detailed and covers all aspects",
                "category": "neutral_description",
                "expected_emotion": "neutral",
                "expected_behavior": "Should stay neutral despite 'extremely'",
                "has_amplifier": True
            },
            {
                "text": "This is absolutely essential to complete before Friday",
                "category": "neutral_requirement",
                "expected_emotion": "neutral",
                "expected_behavior": "Should stay neutral (maybe anticipation at most)",
                "has_amplifier": True
            },
            
            # === WEAK EMOTIONS WITH INTENSIFIERS (Edge cases) ===
            {
                "text": "I'm somewhat happy, I guess, really just okay with it",
                "category": "weak_ambiguous",
                "expected_emotion": "neutral",
                "expected_behavior": "Amplifier shouldn't create strong emotion from weak signal",
                "has_amplifier": True
            },
            {
                "text": "It's really not that bad, pretty neutral about the whole thing",
                "category": "weak_dismissive",
                "expected_emotion": "neutral",
                "expected_behavior": "Amplifier with explicit neutral statement should stay neutral",
                "has_amplifier": True
            },
            
            # === CONTROL GROUP (No amplifiers - baseline) ===
            {
                "text": "I'm happy about this news!",
                "category": "control_positive",
                "expected_emotion": "joy",
                "expected_behavior": "Should detect joy without amplifier",
                "has_amplifier": False
            },
            {
                "text": "The meeting is scheduled for 3pm on Tuesday",
                "category": "control_neutral",
                "expected_emotion": "neutral",
                "expected_behavior": "Should be neutral without amplifier",
                "has_amplifier": False
            },
            {
                "text": "This is frustrating and I'm angry",
                "category": "control_negative",
                "expected_emotion": "anger",
                "expected_behavior": "Should detect anger without amplifier",
                "has_amplifier": False
            },
        ]
    
    async def test_with_amplifier_boost(self, test_case: Dict) -> Dict:
        """Test emotion detection WITH the 1.3x amplifier boost (current behavior)."""
        result = await self.analyzer.analyze_emotion(
            content=test_case["text"],
            user_id="test_user_amplifier"
        )
        
        return {
            "primary_emotion": result.primary_emotion,
            "confidence": result.confidence,
            "all_emotions": result.all_emotions
        }
    
    async def test_without_amplifier_boost(self, test_case: Dict) -> Dict:
        """
        Test emotion detection WITHOUT the 1.3x amplifier boost.
        
        We'll temporarily disable the boost by modifying the analyzer's behavior.
        This simulates removing lines 905-911 from enhanced_vector_emotion_analyzer.py
        """
        # Temporarily remove intensity amplifiers to simulate no boost
        original_amplifiers = self.analyzer.intensity_amplifiers
        self.analyzer.intensity_amplifiers = []
        
        result = await self.analyzer.analyze_emotion(
            content=test_case["text"],
            user_id="test_user_no_amplifier"
        )
        
        # Restore original amplifiers
        self.analyzer.intensity_amplifiers = original_amplifiers
        
        return {
            "primary_emotion": result.primary_emotion,
            "confidence": result.confidence,
            "all_emotions": result.all_emotions
        }
    
    def _compare_results(self, with_boost: Dict, without_boost: Dict, test_case: Dict) -> Dict:
        """Compare results and determine which is better."""
        expected_emotion = test_case["expected_emotion"]
        
        # Check if results match expectations
        with_boost_correct = with_boost["primary_emotion"] == expected_emotion
        without_boost_correct = without_boost["primary_emotion"] == expected_emotion
        
        # Calculate confidence delta
        confidence_delta = with_boost["confidence"] - without_boost["confidence"]
        
        # Determine verdict
        if with_boost_correct and not without_boost_correct:
            verdict = "✅ BOOST HELPFUL: Amplifier boost corrected the emotion"
        elif not with_boost_correct and without_boost_correct:
            verdict = "❌ BOOST HARMFUL: Amplifier boost created false positive"
        elif with_boost_correct and without_boost_correct:
            verdict = "⚖️ BOTH CORRECT: Boost not necessary but not harmful"
        else:
            verdict = "⚠️ BOTH INCORRECT: Neither approach worked"
        
        return {
            "with_boost_correct": with_boost_correct,
            "without_boost_correct": without_boost_correct,
            "confidence_delta": confidence_delta,
            "verdict": verdict,
            "expected": expected_emotion,
            "with_boost_emotion": with_boost["primary_emotion"],
            "without_boost_emotion": without_boost["primary_emotion"],
            "with_boost_confidence": with_boost["confidence"],
            "without_boost_confidence": without_boost["confidence"]
        }
    
    async def run_tests(self):
        """Run all test cases and generate comprehensive report."""
        logger.info("=" * 80)
        logger.info("INTENSITY AMPLIFIER IMPACT TEST")
        logger.info("Testing whether 1.3x emotion boost is still needed with adaptive thresholding")
        logger.info("=" * 80)
        logger.info("")
        
        results = []
        categories_summary = {}
        
        for i, test_case in enumerate(self.test_cases, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"TEST {i}/{len(self.test_cases)}: {test_case['category']}")
            logger.info(f"{'='*80}")
            logger.info(f"Text: \"{test_case['text']}\"")
            logger.info(f"Expected: {test_case['expected_emotion']}")
            logger.info(f"Has amplifier: {test_case['has_amplifier']}")
            logger.info(f"Behavior: {test_case['expected_behavior']}")
            logger.info("")
            
            # Test with boost
            logger.info("--- WITH 1.3x Amplifier Boost (Current) ---")
            with_boost = await self.test_with_amplifier_boost(test_case)
            logger.info(f"Result: {with_boost['primary_emotion']} (confidence: {with_boost['confidence']:.3f})")
            logger.info(f"All emotions: {with_boost['all_emotions']}")
            logger.info("")
            
            # Test without boost
            logger.info("--- WITHOUT Amplifier Boost (Proposed) ---")
            without_boost = await self.test_without_amplifier_boost(test_case)
            logger.info(f"Result: {without_boost['primary_emotion']} (confidence: {without_boost['confidence']:.3f})")
            logger.info(f"All emotions: {without_boost['all_emotions']}")
            logger.info("")
            
            # Compare
            comparison = self._compare_results(with_boost, without_boost, test_case)
            logger.info(f"--- COMPARISON ---")
            logger.info(f"{comparison['verdict']}")
            logger.info(f"Confidence delta: {comparison['confidence_delta']:+.3f}")
            logger.info("")
            
            # Store results
            result = {
                **test_case,
                **comparison
            }
            results.append(result)
            
            # Track by category
            category = test_case['category'].split('_')[0]  # genuine, neutral, weak, control
            if category not in categories_summary:
                categories_summary[category] = {
                    'boost_correct': 0,
                    'no_boost_correct': 0,
                    'both_correct': 0,
                    'both_wrong': 0,
                    'total': 0
                }
            
            categories_summary[category]['total'] += 1
            if comparison['with_boost_correct'] and comparison['without_boost_correct']:
                categories_summary[category]['both_correct'] += 1
            elif comparison['with_boost_correct']:
                categories_summary[category]['boost_correct'] += 1
            elif comparison['without_boost_correct']:
                categories_summary[category]['no_boost_correct'] += 1
            else:
                categories_summary[category]['both_wrong'] += 1
        
        # Generate summary report
        self._generate_summary_report(results, categories_summary)
    
    def _generate_summary_report(self, results: List[Dict], categories_summary: Dict):
        """Generate comprehensive summary report."""
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY REPORT")
        logger.info("=" * 80)
        
        # Overall statistics
        boost_helpful = sum(1 for r in results if "HELPFUL" in r['verdict'])
        boost_harmful = sum(1 for r in results if "HARMFUL" in r['verdict'])
        both_correct = sum(1 for r in results if "BOTH CORRECT" in r['verdict'])
        both_wrong = sum(1 for r in results if "BOTH INCORRECT" in r['verdict'])
        
        logger.info(f"\nOVERALL STATISTICS:")
        logger.info(f"  Total tests: {len(results)}")
        logger.info(f"  ✅ Boost helpful: {boost_helpful} ({boost_helpful/len(results)*100:.1f}%)")
        logger.info(f"  ❌ Boost harmful: {boost_harmful} ({boost_harmful/len(results)*100:.1f}%)")
        logger.info(f"  ⚖️ Both correct: {both_correct} ({both_correct/len(results)*100:.1f}%)")
        logger.info(f"  ⚠️ Both wrong: {both_wrong} ({both_wrong/len(results)*100:.1f}%)")
        
        # Category breakdown
        logger.info(f"\nCATEGORY BREAKDOWN:")
        for category, stats in categories_summary.items():
            logger.info(f"\n  {category.upper()}:")
            logger.info(f"    Total: {stats['total']}")
            logger.info(f"    Only boost correct: {stats['boost_correct']}")
            logger.info(f"    Only no-boost correct: {stats['no_boost_correct']}")
            logger.info(f"    Both correct: {stats['both_correct']}")
            logger.info(f"    Both wrong: {stats['both_wrong']}")
        
        # Recommendation
        logger.info(f"\n{'='*80}")
        logger.info("RECOMMENDATION:")
        logger.info("="*80)
        
        if boost_harmful > boost_helpful:
            logger.info("🔴 REMOVE THE BOOST: More harm than help")
            logger.info("   The 1.3x amplifier boost is creating false positives.")
            logger.info("   Adaptive thresholding handles emotion detection better without it.")
        elif boost_helpful > boost_harmful + both_correct:
            logger.info("🟢 KEEP THE BOOST: Provides significant value")
            logger.info("   The 1.3x amplifier boost correctly strengthens legitimate emotions.")
        elif both_correct > boost_helpful:
            logger.info("🟡 BOOST IS REDUNDANT: Not harmful but not needed")
            logger.info("   Adaptive thresholding works equally well without the boost.")
            logger.info("   Consider removing for code simplicity.")
        else:
            logger.info("⚪ MIXED RESULTS: Further investigation needed")
            logger.info("   The boost helps in some cases and hurts in others.")
            logger.info("   Consider a reduced multiplier (1.15x instead of 1.3x).")
        
        logger.info("")


async def main():
    """Run the intensity amplifier impact test suite."""
    tester = IntensityAmplifierTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
