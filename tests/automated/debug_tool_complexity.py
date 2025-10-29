#!/usr/bin/env python3
"""Debug tool complexity assessment for specific query."""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def main():
    from src.memory.unified_query_classification import create_unified_query_classifier
    
    classifier = create_unified_query_classifier()
    
    query = "Tell me everything about my relationship with you"
    print(f"Testing query: '{query}'")
    print(f"Tool complexity threshold: {classifier.tool_complexity_threshold}")
    
    classification = await classifier.classify(
        query=query,
        emotion_data=None,
        user_id="test_user",
        character_name="elena"
    )
    
    print(f"\nResults:")
    print(f"  Intent: {classification.intent_type.value}")
    print(f"  Data Sources: {[ds.value for ds in classification.data_sources]}")
    print(f"  Confidence: {classification.confidence:.3f}")
    
    # Get the raw complexity score (need to expose this or re-calculate)
    query_doc = classifier.nlp(query) if classifier.nlp else None
    matched_patterns = []  # Would need to extract from classification
    question_complexity = 5  # Estimate
    
    complexity_score = classifier._assess_tool_complexity(
        query=query,
        query_doc=query_doc,
        matched_patterns=matched_patterns,
        question_complexity=question_complexity
    )
    
    print(f"\nComplexity Analysis:")
    print(f"  Complexity score: {complexity_score:.3f}")
    print(f"  Threshold: {classifier.tool_complexity_threshold}")
    print(f"  Uses tools: {complexity_score >= classifier.tool_complexity_threshold}")


if __name__ == "__main__":
    asyncio.run(main())
