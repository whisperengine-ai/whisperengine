#!/bin/bash
# Pre-load RoBERTa emotion models for instant startup
# Run this script during Docker build to cache models

echo "🚀 Pre-loading RoBERTa emotion models for instant startup..."

python3 -c "
import sys
sys.path.append('/app/src')
from transformers import pipeline
import time

print('Initializing j-hartmann/emotion-english-distilroberta-base...')
start_time = time.time()

# Initialize the pipeline (downloads and caches model)
classifier = pipeline(
    'text-classification',
    model='j-hartmann/emotion-english-distilroberta-base',
    return_all_scores=True
)

# Test inference to ensure complete initialization
test_text = 'I am happy and excited about this amazing opportunity!'
results = classifier(test_text)

end_time = time.time()
print(f'✅ RoBERTa model loaded and cached in {end_time - start_time:.2f} seconds')
print(f'   Model size: ~329MB cached in /root/.cache/huggingface/')
print(f'   Emotions detected: {len(results[0])} categories')
print(f'   Test result: {results[0][0][\"label\"]} ({results[0][0][\"score\"]:.3f})')
print('🎯 Instant startup ready - no model download needed!')
"

echo "✅ RoBERTa pre-loading completed successfully!"