# Memory Aging System

## Overview

The Memory Aging System is a comprehensive solution for preventing unbounded memory growth while preserving retrieval quality in WhisperEngine. This system implements intelligent memory consolidation and aging policies with robust safety checks and comprehensive metrics.

## Architecture

### Core Components

1. **MemoryAgingPolicy** (`src/memory/aging/aging_policy.py`)
   - Calculates retention scores based on importance, recency, access patterns, and decay
   - Implements multi-layered safety checks to prevent inappropriate memory deletion
   - Configurable weighting system for different memory attributes

2. **MemoryAgingRunner** (`src/memory/aging/aging_runner.py`)
   - Batch execution engine for aging cycles
   - Comprehensive metrics tracking and instrumentation
   - Dry-run mode for safe testing and validation

3. **MemoryConsolidator** (`src/memory/aging/consolidator.py`)
   - Similarity-based memory clustering and summarization
   - Configurable similarity thresholds
   - Placeholder for advanced semantic consolidation

### Key Features

#### Safety-First Design
- **High Emotional Intensity Protection**: Memories with emotional_intensity ≥ 0.7 are never pruned
- **Intervention Outcome Protection**: Memories marked as intervention outcomes are preserved
- **Recency Protection**: Memories less than 24 hours old are never pruned
- **Graceful Degradation**: Missing metadata fields default to safe (preserve) behavior

#### Comprehensive Metrics
- `memory_aging_run_seconds`: Timing for each aging cycle
- `memories_scanned`: Total memories processed
- `memories_flagged_low_value`: Memories identified for potential action
- `memories_pruned`: Memories actually deleted
- `memories_summarized`: Memories consolidated
- `high_value_memories_preserved`: Important memories retained
- `consolidation_clusters_formed`: Number of consolidation groups created

#### Performance Optimization
- Batch processing for efficiency
- Async operations for non-blocking execution
- Configurable thresholds for hardware constraints
- Memory usage tracking and limits

## Configuration

### Environment Variables

```bash
# Enable memory aging system
MEMORY_AGING_ENABLED=true

# Policy configuration
MEMORY_DECAY_LAMBDA=0.01          # Decay factor influence (0.005-0.02)
MEMORY_PRUNE_THRESHOLD=0.2        # Score threshold for pruning (0.1-0.4)

# Safety thresholds
MEMORY_AGING_SAFETY_EMOTIONAL_THRESHOLD=0.7   # Emotional intensity protection
MEMORY_AGING_SAFETY_RECENCY_HOURS=24          # Recent memory protection

# Consolidation settings
MEMORY_CONSOLIDATION_SIMILARITY=0.92  # Similarity threshold for clustering
```

### Policy Weights

The retention score is calculated as a weighted combination:

```python
score = (
    importance_weight * importance_score +     # Default: 0.6
    recency_weight * recency_factor +          # Default: 0.3
    access_weight * access_factor -            # Default: 0.1
    decay_lambda * decay_score                 # Default: 0.01
)
```

## Usage

### Basic Memory Aging

```python
from src.memory.aging.aging_policy import MemoryAgingPolicy
from src.memory.aging.aging_runner import MemoryAgingRunner

# Initialize components
policy = MemoryAgingPolicy(
    importance_weight=0.6,
    recency_weight=0.3,
    access_weight=0.1,
    decay_lambda=0.01,
    prune_threshold=0.2
)

runner = MemoryAgingRunner(
    memory_manager=memory_manager,
    policy=policy
)

# Run aging cycle (dry run)
results = await runner.run(user_id="user123", dry_run=True)
print(f"Would prune {results['flagged']} memories")

# Execute aging
results = await runner.run(user_id="user123", dry_run=False)
print(f"Pruned {results['pruned']} memories, preserved {results['preserved']}")
```

### Memory Consolidation

```python
from src.memory.aging.consolidator import MemoryConsolidator

consolidator = MemoryConsolidator(
    embedding_manager=embedding_manager,
    similarity_threshold=0.92
)

# Consolidate similar memories
consolidated = await consolidator.consolidate(low_value_memories)
```

### Custom Policy Configuration

```python
# Conservative policy (preserve more)
conservative_policy = MemoryAgingPolicy(
    importance_weight=0.8,  # Higher importance weight
    recency_weight=0.15,
    access_weight=0.05,
    decay_lambda=0.005,     # Lower decay impact
    prune_threshold=0.1     # Lower threshold
)

# Aggressive policy (prune more)
aggressive_policy = MemoryAgingPolicy(
    importance_weight=0.4,
    recency_weight=0.3,
    access_weight=0.2,
    decay_lambda=0.02,      # Higher decay impact
    prune_threshold=0.4     # Higher threshold
)
```

## Memory Metadata Requirements

For optimal aging performance, memories should include:

```python
memory = {
    'id': 'unique_memory_id',
    'content': 'memory content',
    'created_at': timestamp,           # Creation time (required)
    'last_accessed': timestamp,        # Last access time
    'access_count': int,               # Access frequency
    'importance_score': float,         # 0.0-1.0 importance rating
    'decay_score': float,              # 0.0-1.0 decay factor
    'emotional_intensity': float,      # 0.0-1.0 emotional significance
    'category': str,                   # Memory category
    'intervention_outcome': str,       # 'success', 'pending_followup', etc.
    'user_id': str                     # Owner identifier
}
```

## Migration

To add aging support to existing memories:

```bash
# Run metadata migration script
python scripts/memory/migrate_memory_metadata.py

# Verify migration results
python scripts/memory/verify_aging_system.py
```

## Performance Considerations

### Hardware Requirements
- **Memory**: 16-32GB RAM recommended for large memory sets
- **Storage**: Sufficient disk space for consolidated memory storage
- **Processing**: Batch size automatically adjusted based on available resources

### Scaling Guidelines
- Run aging cycles during low-usage periods
- Use dry-run mode to estimate impact before execution
- Monitor metrics to tune policy parameters
- Consider distributed processing for very large memory sets

## Monitoring and Alerts

### Key Metrics to Monitor
1. **Aging Run Duration**: Should complete within reasonable time
2. **Memory Growth Rate**: Should be controlled by aging cycles
3. **Preservation Rate**: Ensure important memories aren't being lost
4. **Consolidation Effectiveness**: Track space savings from consolidation

### Recommended Alerts
- Aging cycle failures or timeouts
- Unusual spike in memory pruning
- Safety check violations
- Performance degradation

## Testing

### Unit Tests
```bash
# Run all aging system tests
pytest tests/memory/test_aging*.py tests/memory/test_consolidator.py -v

# Run specific component tests
pytest tests/memory/test_aging_policy.py -v
pytest tests/memory/test_aging_runner.py -v
```

### Integration Tests
```bash
# Run integration test suite
pytest tests/memory/test_aging_integration.py -v

# Run verification script
python scripts/memory/verify_aging_system.py
```

### Performance Testing
```bash
# Test with large memory sets
python tests/memory/test_aging_performance.py

# Validate memory usage
python tests/memory/test_memory_limits.py
```

## Troubleshooting

### Common Issues

#### High Memory Usage During Aging
- Reduce batch size in aging runner
- Increase available system memory
- Run aging more frequently with smaller sets

#### Too Many Memories Being Pruned
- Lower the prune_threshold value
- Increase importance_weight in policy
- Review safety check thresholds

#### Aging Cycles Taking Too Long
- Optimize memory retrieval queries
- Implement parallel processing
- Consider breaking large users into smaller batches

#### Safety Checks Too Restrictive
- Review emotional_intensity thresholds
- Adjust recency protection timeframe
- Customize intervention outcome categories

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger('memory.aging').setLevel(logging.DEBUG)
```

### Validation Commands

```bash
# Verify system health
python scripts/memory/verify_aging_system.py

# Check memory metadata completeness
python scripts/memory/check_memory_metadata.py

# Analyze aging policy effectiveness
python scripts/memory/analyze_aging_results.py
```

## Future Enhancements

### Planned Features
1. **Advanced Consolidation**: Semantic similarity-based clustering using embeddings
2. **Machine Learning Policy**: Adaptive retention scoring based on user patterns
3. **Distributed Aging**: Multi-node processing for large-scale deployments
4. **Real-time Monitoring**: Dashboard for aging system health and performance

### Integration Points
- **Emotional Intelligence System**: Enhanced emotional_intensity scoring
- **Memory Importance Learning**: Dynamic importance_score updates
- **Usage Analytics**: Access pattern analysis for better retention decisions

## API Reference

### MemoryAgingPolicy

#### Methods
- `compute_retention_score(memory: dict) -> float`: Calculate memory retention score
- `is_prunable(memory: dict) -> bool`: Check if memory can be safely pruned

### MemoryAgingRunner

#### Methods
- `run(user_id: str, dry_run: bool = True) -> dict`: Execute aging cycle

#### Return Format
```python
{
    'user_id': str,
    'scanned': int,         # Total memories processed
    'flagged': int,         # Memories flagged for action
    'pruned': int,          # Memories actually deleted
    'preserved': int,       # Memories kept
    'elapsed_seconds': float,
    'dry_run': bool
}
```

### MemoryConsolidator

#### Methods
- `consolidate(memories: List[dict]) -> List[dict]`: Consolidate similar memories

## Security Considerations

- Memory aging operations are user-scoped (no cross-user access)
- Safety checks prevent accidental deletion of critical memories
- Dry-run mode allows safe testing of aging policies
- All operations are logged for audit purposes
- Backup and restore procedures should be in place

## Best Practices

1. **Start Conservative**: Begin with low prune thresholds and high safety margins
2. **Monitor Closely**: Track metrics and user feedback during initial deployment
3. **Test Thoroughly**: Always use dry-run mode before executing aging cycles
4. **Regular Maintenance**: Schedule aging cycles during low-usage periods
5. **Backup Critical Data**: Maintain backups of important memories before aging
6. **Gradual Tuning**: Adjust policy parameters incrementally based on results