#!/usr/bin/env python3
"""
Test RoBERTa emotion analysis on the problematic text
"""

try:
    from transformers import pipeline
    
    # Initialize the same model used in WhisperEngine
    classifier = pipeline(
        "text-classification",
        model="cardiffnlp/twitter-roberta-base-emotion-multilabel-latest",
        return_all_scores=True,
        device=-1
    )
    
    test_text = "We just dropped Logan off for school and now we have the whole afternoon to ourselves!"
    
    print("🧪 Testing RoBERTa emotion analysis")
    print(f"Text: {test_text}")
    print()
    
    results = classifier(test_text)
    
    print("RoBERTa Results:")
    if results and len(results) > 0:
        # Sort by confidence score
        sorted_results = sorted(results[0], key=lambda x: x['score'], reverse=True)
        
        for result in sorted_results:
            label = result['label']
            score = result['score']
            print(f"  {label}: {score:.4f}")
    
    print()
    print("🔍 Analysis:")
    print("This should clearly be 'joy' or 'anticipation', not 'sadness'!")
    
except ImportError:
    print("❌ Transformers not available")
except Exception as e:
    print(f"❌ Error: {e}")