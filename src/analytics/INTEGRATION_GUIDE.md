"""
Sprint 1: TrendWise Integration Guide

This file documents how to integrate TrendWise components into the existing
WhisperEngine message processing pipeline.

## Integration Points

### 1. Message Processor Integration

Add trend analysis to `src/core/message_processor.py`:

```python
# In __init__ method:
from src.analytics.trend_analyzer import create_trend_analyzer
from src.adaptation.confidence_adapter import create_confidence_adapter

self.trend_analyzer = create_trend_analyzer(self.temporal_client)
self.confidence_adapter = create_confidence_adapter(self.trend_analyzer)

# In _build_conversation_context_with_ai_intelligence method:
async def _build_conversation_context_with_ai_intelligence(
    self, message_context, relevant_memories, ai_components
):
    # Existing context building...
    conversation_context = await self._build_conversation_context(message_context, relevant_memories)
    
    # NEW: Add confidence adaptation guidance
    adaptation_params = await self.confidence_adapter.adjust_response_style(
        user_id=message_context.user_id,
        bot_name=os.getenv('DISCORD_BOT_NAME', 'unknown')
    )
    
    if adaptation_params:
        adaptation_guidance = self.confidence_adapter.generate_adaptation_guidance(adaptation_params)
        
        # Apply system prompt additions
        for i, msg in enumerate(conversation_context):
            if msg.get("role") == "system":
                additional_guidance = " ".join(adaptation_guidance.system_prompt_additions)
                conversation_context[i]["content"] += f" {additional_guidance}"
                break
        
        # Store adaptation context for monitoring
        ai_components['adaptation_applied'] = {
            'style': adaptation_params.response_style.value,
            'reason': adaptation_params.adaptation_reason,
            'parameters': adaptation_params
        }
    
    return conversation_context
```

### 2. Temporal Intelligence Integration

The trend analyzer requires the temporal client. Ensure it's passed during initialization:

```python
# In message processor initialization:
if self.temporal_intelligence_enabled and self.temporal_client:
    self.trend_analyzer = create_trend_analyzer(self.temporal_client)
else:
    self.trend_analyzer = None
```

### 3. Performance Monitoring

Add effectiveness tracking to measure adaptation success:

```python
# After response generation:
if hasattr(self, 'confidence_adapter') and 'adaptation_applied' in ai_components:
    # Calculate conversation quality score (use existing metrics)
    quality_score = self._calculate_conversation_quality(response, ai_components)
    
    # Record adaptation effectiveness
    await self.confidence_adapter.record_adaptation_effectiveness(
        user_id=message_context.user_id,
        bot_name=bot_name,
        adaptation_params=ai_components['adaptation_applied']['parameters'],
        conversation_quality_score=quality_score
    )
```

## Testing

### Unit Tests
- `tests/unit/test_trend_analyzer.py`
- `tests/unit/test_confidence_adapter.py`

### Integration Tests
- Test with live InfluxDB data
- A/B testing framework for adaptation effectiveness

### Performance Tests
- Measure latency impact (<50ms target)
- Memory usage monitoring

## Rollout Strategy

1. **Phase 1**: Deploy trend analyzer (read-only)
2. **Phase 2**: Enable confidence adaptation for single bot
3. **Phase 3**: Rollout to all bots with monitoring
4. **Phase 4**: Optimize based on effectiveness metrics

## Success Metrics

- 5% improvement in conversation quality scores
- <50ms additional latency per message
- Adaptation effectiveness >70% (subjective evaluation)
- System stability maintained

## Next Steps

After Sprint 1 TrendWise is complete and showing results:
1. Sprint 2: MemoryBoost - leverage trend data for memory optimization
2. Sprint 3: RelationshipTuner - use relationship trends for progression
3. Continuous monitoring and optimization
"""