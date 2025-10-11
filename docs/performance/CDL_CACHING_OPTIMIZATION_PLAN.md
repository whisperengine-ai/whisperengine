# CDL Caching Optimization Plan

## Current Caching Architecture

### Multi-Level Caching Strategy
1. **Database CDL Manager** (Process-level singleton)
   - Caches Character object + raw data
   - Thread-safe with double-check locking
   - Scope: Per bot process lifetime

2. **Database CDL Parser** (Module-level singleton) 
   - Caches parsed character data by normalized_name
   - Key: "elena", "marcus", etc.
   - Scope: Per bot process, multi-character capable

3. **CDL Manager Singleton** (Global)
   - Single application-wide manager instance

### Fallback Flow
1. **PRIMARY**: Database CDL Manager → Database CDL Parser → PostgreSQL
2. **FALLBACK**: JSON file loading if database fails

## Current Performance Issues

### ❌ Problems
1. **No Cache Invalidation**: Caches never expire/refresh
2. **Memory Growth**: Unlimited cache growth (though data is static)
3. **Cold Start Penalty**: First request hits database
4. **Redundant Instance Creation**: New parser instances in load_character_data()

### ✅ Working Well
- Multiple caching layers prevent repeated DB hits
- Thread-safe singleton patterns
- Automatic fallback to JSON files
- Character data is effectively static (good caching candidate)

## Optimization Recommendations

### Phase 1: Fix Existing Issues
1. **Fix Parser Singleton**: Ensure global parser instance is actually cached
2. **Add Cache TTL**: Optional time-based cache invalidation (default: disabled for static data)
3. **Memory Monitoring**: Log cache sizes and hit rates

### Phase 2: Performance Enhancements
1. **Preload Common Characters**: Warm cache on startup for active bots
2. **Background Refresh**: Optional periodic cache refresh for updated character data
3. **Cache Metrics**: Export caching statistics to monitoring system

### Phase 3: Advanced Optimizations
1. **Redis Caching**: Optional Redis layer for cross-process caching
2. **Selective Loading**: Load only required character data sections
3. **Lazy Loading**: Load communication styles/knowledge on-demand

## Implementation Priority

### HIGH PRIORITY (Immediate)
- [x] Fix global parser singleton caching bug
- [ ] Add cache hit/miss logging for monitoring
- [ ] Document current caching behavior

### MEDIUM PRIORITY (Sprint 2)
- [ ] Add optional cache TTL with environment variable
- [ ] Implement cache preloading for active bots
- [ ] Add cache size monitoring

### LOW PRIORITY (Future)
- [ ] Redis cross-process caching
- [ ] Selective data loading
- [ ] Advanced cache invalidation strategies

## Performance Expectations

### Current Performance
- **First Request**: Database query (~50-100ms)
- **Cached Requests**: Memory access (~1-5ms)
- **Fallback**: JSON file loading (~10-20ms)

### With Optimizations
- **Preloaded Cache**: All requests ~1-5ms
- **Cache Hit Rate**: >99% for active bots
- **Memory Usage**: Predictable, bounded by character count

## Configuration

### Environment Variables
```bash
# Cache behavior
CDL_CACHE_ENABLED=true          # Enable/disable caching
CDL_CACHE_TTL_SECONDS=0         # Cache TTL (0 = no expiration)
CDL_PRELOAD_CHARACTERS=true     # Preload on startup

# Monitoring
CDL_CACHE_METRICS_ENABLED=true  # Export cache metrics
CDL_CACHE_LOG_HITS=false        # Log cache hits/misses
```

### Cache Statistics Monitoring
- Cache hit/miss rates per character
- Memory usage per cache layer
- Database query frequency
- Fallback activation frequency

## Testing Strategy

1. **Performance Testing**: Measure response times with/without cache
2. **Memory Testing**: Monitor cache growth under load
3. **Fallback Testing**: Verify JSON fallback when database unavailable
4. **Concurrency Testing**: Verify thread-safe cache access

## Migration Plan

1. **Phase 1**: Fix existing bugs, add monitoring
2. **Phase 2**: Add configuration options, preloading
3. **Phase 3**: Advanced features based on usage patterns
4. **Validation**: Performance benchmarks at each phase