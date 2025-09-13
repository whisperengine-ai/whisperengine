# Conversation Cache Design Document

## Overview

The `HybridConversationCache` is a sophisticated caching system designed to minimize Discord API calls while maintaining accurate conversation context for the Discord bot. It implements a hybrid approach combining event-driven message caching with intelligent refresh strategies.

## Architecture

### Core Design Principles

1. **API Call Minimization**: Reduce expensive Discord API calls by caching recent messages locally
2. **Thread Safety**: Support concurrent operations from multiple users without data corruption
3. **Smart Refresh Logic**: Balance cache freshness with performance
4. **Event-Driven Updates**: Leverage Discord events to maintain cache accuracy
5. **Configurable Behavior**: Allow tuning for different use cases and environments

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Discord Bot Process                       │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────────┐ │
│  │   Discord       │    │    HybridConversationCache       │ │
│  │   Events        │────▶                                  │ │
│  │                 │    │  ┌─────────────────────────────┐ │ │
│  │ • on_message    │    │  │      Cache Storage          │ │ │
│  │ • message edits │    │  │  ┌─────────────────────────┐│ │ │
│  │ • message deletes│   │  │  │ Channel ID → {         ││ │ │
│  └─────────────────┘    │  │  │   messages: deque,     ││ │ │
│                         │  │  │   last_bootstrap: time ││ │ │
│  ┌─────────────────┐    │  │  │ }                      ││ │ │
│  │   Bot Logic     │◄───┤  │  └─────────────────────────┘│ │ │
│  │                 │    │  └─────────────────────────────┐ │ │
│  │ • Context       │    │                                │ │ │
│  │   requests      │    │  ┌─────────────────────────────┐ │ │
│  │ • Message       │    │  │    Thread Safety Layer      │ │ │
│  │   processing    │    │  │  • RLock for cache ops     │ │ │
│  └─────────────────┘    │  │  • Per-channel bootstrap   │ │ │
│                         │  │    locks                   │ │ │
│                         │  │  • Lock manager            │ │ │
│                         │  └─────────────────────────────┘ │ │
│                         └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Cache Storage Structure

```python
conversations = {
    "channel_id": {
        "messages": deque([message1, message2, ...], maxlen=50),
        "last_bootstrap": timestamp
    }
}
```

- **Channel-based organization**: Each Discord channel has its own cache entry
- **Bounded deque**: Automatically manages memory by limiting message count
- **Timestamp tracking**: Enables cache expiration logic

### 2. Thread Safety Architecture

The cache implements multiple layers of thread safety:

#### Primary Cache Lock (`_cache_lock`)
- **Type**: `threading.RLock` (Re-entrant lock)
- **Purpose**: Protects all cache data structure operations
- **Scope**: Global cache operations (read/write/modify)

#### Bootstrap Lock System
- **Per-channel locks**: Prevents concurrent Discord API calls for the same channel
- **Bootstrap lock manager**: Manages creation/cleanup of per-channel locks
- **Async coordination**: Works with asyncio locks for async/sync boundary

### 3. Smart Refresh Logic

The cache uses a two-tier refresh strategy:

#### Bootstrap Triggers
1. **Cache Miss**: No cached data exists for the channel
2. **Cache Expiration**: Data is older than `cache_timeout_minutes`
3. **Insufficient Data**: Cached messages < requested limit

#### Bootstrap Process
1. **Lock Acquisition**: Prevent concurrent bootstraps for same channel
2. **Discord API Call**: Fetch `bootstrap_limit` recent messages
3. **Cache Update**: Replace existing cache with fresh data
4. **Timestamp Update**: Mark cache as fresh

## Configuration Parameters

### Core Settings

| Parameter | Default | Purpose | Impact |
|-----------|---------|---------|---------|
| `cache_timeout_minutes` | 15 | Cache expiration time | Freshness vs API calls |
| `bootstrap_limit` | 20 | Messages fetched from Discord | API load vs context depth |
| `max_local_messages` | 50 | Maximum cached messages per channel | Memory usage vs history depth |

### Environment Variables

```bash
CONVERSATION_CACHE_TIMEOUT_MINUTES=15    # Cache expiration
CONVERSATION_CACHE_BOOTSTRAP_LIMIT=20    # Bootstrap fetch size
CONVERSATION_CACHE_MAX_LOCAL=50          # Max messages per channel
```

## API Interface

### Primary Methods

#### `get_conversation_context(channel, limit=5, exclude_message_id=None)`
**Purpose**: Retrieve recent conversation context with minimal API calls

```python
messages = await cache.get_conversation_context(
    channel=discord_channel,
    limit=5,                    # Number of recent messages
    exclude_message_id=123456   # Skip specific message (current message)
)
```

**Behavior**:
1. Check if bootstrap is needed
2. Perform bootstrap if required (thread-safe)
3. Return requested number of recent messages
4. Filter excluded messages

#### `add_message(channel_id, message)`
**Purpose**: Add new messages to cache from Discord events

```python
cache.add_message(str(channel.id), discord_message)
```

**Behavior**:
1. Initialize channel cache if first message
2. Append message to existing cache
3. Automatic memory management via bounded deque

#### `clear_channel_cache(channel_id)`
**Purpose**: Remove cache data for specific channel

```python
cache.clear_channel_cache(str(channel.id))
```

**Use Cases**:
- Channel cleanup
- Error recovery
- Memory management

#### `get_cache_stats()`
**Purpose**: Monitoring and debugging cache performance

```python
stats = cache.get_cache_stats()
# Returns: {
#     'cached_channels': 5,
#     'total_cached_messages': 150,
#     'avg_messages_per_channel': 30.0,
#     'cache_timeout_minutes': 15,
#     'bootstrap_limit': 20,
#     'max_local_messages': 50
# }
```

## Integration Patterns

### Discord Bot Integration

#### Event Handler Integration
```python
@bot.event
async def on_message(message):
    # Add to cache for future context requests
    if conversation_cache:
        conversation_cache.add_message(str(message.channel.id), message)
    
    # Process message...
```

#### Context Retrieval
```python
async def process_user_message(message):
    # Get conversation context
    if conversation_cache:
        recent_messages = await conversation_cache.get_conversation_context(
            channel=message.channel,
            limit=5,
            exclude_message_id=message.id
        )
    
    # Use context for AI processing...
```

### Error Handling

The cache implements robust error handling:

1. **Bootstrap Failures**: Initialize empty cache to prevent retry loops
2. **Discord API Errors**: Graceful degradation with logging
3. **Thread Safety**: Prevent deadlocks with timeout mechanisms
4. **Memory Management**: Automatic cleanup via bounded collections

## Performance Characteristics

### Cache Hit Performance
- **Typical Response Time**: < 1ms for cache hits
- **Memory Usage**: ~50KB per active channel (50 messages × ~1KB average)
- **Thread Contention**: Minimal due to RLock and per-channel bootstrap locks

### Cache Miss Performance
- **Bootstrap Time**: 100-500ms (depends on Discord API latency)
- **API Calls**: 1 call per bootstrap (fetches multiple messages)
- **Concurrency**: Multiple channels can bootstrap simultaneously

### Memory Management
- **Automatic Cleanup**: Bounded deques prevent unbounded growth
- **Channel Lifecycle**: Caches persist until explicit cleanup
- **Total Memory**: Scales linearly with active channels

## Testing Strategy

### Unit Tests
- Mock Discord objects for isolated testing
- Thread safety verification with concurrent operations
- Cache expiration timing validation
- Bootstrap logic verification

### Integration Tests
- Full Discord bot integration testing
- Multi-user concurrent access patterns
- Error recovery scenarios
- Performance benchmarking

### Test Coverage Areas
1. **Basic Functionality**: Cache/retrieve operations
2. **Thread Safety**: Concurrent user simulation
3. **Cache Expiration**: Time-based refresh logic
4. **Error Handling**: Discord API failure scenarios
5. **Memory Management**: Bounded growth verification

## Future Enhancements

### Potential Improvements

1. **Persistent Storage**: Redis/SQLite backing for cache survival across restarts
2. **Advanced Eviction**: LRU/LFU policies for memory optimization
3. **Metrics Collection**: Detailed performance monitoring
4. **Compression**: Message content compression for memory efficiency
5. **Selective Caching**: Channel-specific caching policies

### Scalability Considerations

1. **Multi-Instance Deployment**: Shared cache for bot clusters
2. **Memory Monitoring**: Automatic cache size management
3. **Performance Metrics**: Response time and hit rate monitoring
4. **Configuration Management**: Dynamic parameter adjustment

## Monitoring and Debugging

### Key Metrics to Monitor

1. **Cache Hit Rate**: Percentage of requests served from cache
2. **Bootstrap Frequency**: How often Discord API is called
3. **Memory Usage**: Total cache memory consumption
4. **Response Times**: Cache hit vs miss latency
5. **Error Rates**: Bootstrap failure frequency

### Debug Logging

The cache provides detailed logging at DEBUG level:
- Bootstrap operations and timing
- Cache hit/miss information
- Thread safety events
- Error conditions and recovery

### Health Checks

Use `get_cache_stats()` for monitoring:
- Verify reasonable cache sizes
- Monitor bootstrap frequency
- Check for memory leaks
- Validate configuration effectiveness

## Conclusion

The `HybridConversationCache` provides an efficient, thread-safe solution for minimizing Discord API calls while maintaining conversation context accuracy. Its hybrid approach balances performance, memory usage, and data freshness through configurable policies and smart refresh logic.

The design prioritizes:
- **Developer Experience**: Simple API with powerful features
- **Operational Reliability**: Robust error handling and monitoring
- **Performance**: Sub-millisecond cache hits with minimal memory overhead
- **Scalability**: Thread-safe design supporting concurrent users

This architecture enables the Discord bot to provide rich conversational context while maintaining responsive performance and respecting Discord API rate limits.
