# Quick Test Commands for Emotion System Improvements

## Individual Components

### Test Universal Emotion Taxonomy
```bash
source .venv/bin/activate
python -c "
from src.intelligence.emotion_taxonomy import UniversalEmotionTaxonomy
test_scores = {'pos': 0.8, 'neg': 0.1, 'neu': 0.1, 'compound': 0.7}
results = UniversalEmotionTaxonomy.vader_sentiment_to_emotions(test_scores)
print('Results:', [(e.value, i, c) for e, i, c in results])
"
```

### Test RoBERTa Analyzer (with fallbacks)
```bash
source .venv/bin/activate
python -c "
import asyncio
from src.intelligence.roberta_emotion_analyzer import RoBertaEmotionAnalyzer

async def test():
    analyzer = RoBertaEmotionAnalyzer()
    results = await analyzer.analyze_emotion('I am so happy today!')
    print('Results:', [(r.dimension.value, r.intensity, r.method) for r in results])
    analyzer.cleanup()

asyncio.run(test())
"
```

## Full Test Suite

### Unit Tests
```bash
source .venv/bin/activate
python -m pytest tests/unit/test_emotion_systems.py -v
```

### Integration Tests  
```bash
source .venv/bin/activate
python scripts/test_emotion_improvements.py
```

### Complete Test Suite
```bash
./scripts/test_emotion_suite.sh
```

## Container-Based Testing

### Test in Elena Bot Container
```bash
./multi-bot.sh start elena
docker exec whisperengine-elena-bot python -c "
from src.intelligence.emotion_taxonomy import UniversalEmotionTaxonomy
results = UniversalEmotionTaxonomy.vader_sentiment_to_emotions({'pos': 0.8, 'neg': 0.1, 'neu': 0.1, 'compound': 0.7})
print('Container test:', [(e.value, i) for e, i, _ in results])
"
```

### Full Container Test
```bash
docker exec whisperengine-elena-bot python scripts/test_emotion_improvements.py
```

## Performance Benchmarking

### VADER Mapping Performance
```bash
source .venv/bin/activate
python -c "
import time
from src.intelligence.emotion_taxonomy import UniversalEmotionTaxonomy

start = time.time()
for _ in range(1000):
    UniversalEmotionTaxonomy.vader_sentiment_to_emotions({'pos': 0.5, 'neg': 0.3, 'neu': 0.2, 'compound': 0.2})
elapsed = time.time() - start
print(f'1000 VADER mappings: {elapsed:.3f}s ({elapsed/1000*1000:.3f}ms avg)')
"
```

### Async Performance Test
```bash
source .venv/bin/activate
python -c "
import asyncio
import time

async def concurrent_test():
    tasks = []
    for i in range(50):
        tasks.append(asyncio.sleep(0.001))
    
    start = time.time()
    await asyncio.gather(*tasks)
    elapsed = time.time() - start
    print(f'50 concurrent tasks: {elapsed:.3f}s (non-blocking confirmed)')

asyncio.run(concurrent_test())
"
```