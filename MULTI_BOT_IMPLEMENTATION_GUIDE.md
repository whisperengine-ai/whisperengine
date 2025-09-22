# Multi-Bot Memory System: Technical Implementation Guide

## Quick Start

### Basic Multi-Bot Query
```python
from memory.memory_protocol import create_multi_bot_querier

# Initialize querier
querier = create_multi_bot_querier()

# Query all bots
results = await querier.query_all_bots("user preferences", "user123")
print(f"Found memories from {len(results)} bots")

# Query specific bots only
elena_gabriel = await querier.query_specific_bots(
    "emotional support", "user123", ["Elena", "Gabriel"]
)
```

### Cross-Bot Analysis
```python
# Comprehensive analysis across bots
analysis = await querier.cross_bot_analysis("user123", "conversation style")

print(f"Most relevant bot: {analysis['insights']['most_relevant_bot']}")
print(f"Total memories analyzed: {analysis['total_memories']}")
```

## API Reference

### MultiBotMemoryQuerier Class

#### Methods

##### `query_all_bots(query, user_id, top_k=10, min_score=0.0)`
Query across all bot personalities.

**Parameters:**
- `query` (str): Search query text
- `user_id` (str): User to search memories for  
- `top_k` (int): Maximum results per search
- `min_score` (float): Minimum relevance score

**Returns:**
```python
{
    "Elena": [
        {
            "content": "Memory content",
            "score": 0.85,
            "timestamp": "2025-09-22T10:30:00Z",
            "memory_type": "FACT",
            "confidence": 0.9,
            "source": "conversation",
            "significance": 0.7
        }
    ],
    "Gabriel": [...],
    "Marcus": [...]
}
```

##### `query_specific_bots(query, user_id, bot_names, top_k=10, min_score=0.0)`
Query specific subset of bots.

**Parameters:**
- `bot_names` (List[str]): List of specific bot names to query

**Example:**
```python
results = await querier.query_specific_bots(
    "problem solving", 
    "user123", 
    ["Marcus", "Marcus_Chen"]  # Only analytical bots
)
```

##### `cross_bot_analysis(user_id, analysis_topic, include_bots=None)`
Analyze how different bots perceive the same topic.

**Returns:**
```python
{
    "topic": "conversation preferences",
    "user_id": "user123", 
    "bots_analyzed": ["Elena", "Gabriel", "Marcus"],
    "total_memories": 45,
    "bot_perspectives": {
        "Elena": {
            "memory_count": 15,
            "average_relevance_score": 0.82,
            "average_confidence": 0.87,
            "memory_types": {"FACT": 10, "EMOTIONAL": 5}
        }
    },
    "insights": {
        "most_relevant_bot": "Elena",
        "highest_confidence_bot": "Gabriel",
        "most_memories_bot": "Marcus"
    }
}
```

##### `get_bot_memory_stats(user_id=None)`
Get comprehensive memory statistics for all bots.

**Returns:**
```python
{
    "Elena": {
        "total_memories": 150,
        "unique_users": 25,
        "average_confidence": 0.85,
        "average_significance": 0.72,
        "memory_types": {"FACT": 80, "EMOTIONAL": 70},
        "date_range": {
            "earliest": "2025-01-15T09:00:00Z",
            "latest": "2025-09-22T15:30:00Z"
        }
    }
}
```

## Advanced Usage Patterns

### Bot Category Analysis
```python
# Define bot categories
analytical_bots = ["Marcus", "Marcus_Chen"]
emotional_bots = ["Elena", "Gabriel"]
creative_bots = ["Dream"]

# Compare category performance
analytical_results = await querier.query_specific_bots(
    "problem solving", "user123", analytical_bots
)

emotional_results = await querier.query_specific_bots(
    "emotional support", "user123", emotional_bots  
)

# Analyze which category is more effective for user
```

### Temporal Analysis Pattern
```python
# Get memories from different time periods
import datetime

# Recent memories (last 30 days)
recent_analysis = await querier.cross_bot_analysis(
    "user123", "recent preferences"
)

# Historical analysis - implement custom filtering
# Note: Direct temporal filtering will be added in Phase 1
```

### Memory Quality Assessment
```python
# Compare memory consistency across bots
all_user_memories = await querier.query_all_bots(
    "user behavior patterns", "user123", top_k=100
)

# Analyze for contradictions
contradictions = []
for bot1, memories1 in all_user_memories.items():
    for bot2, memories2 in all_user_memories.items():
        if bot1 != bot2:
            # Custom logic to detect contradictory memories
            # This will be automated in Phase 3
            pass
```

## Integration Examples

### Discord Command Integration
```python
# Example Discord command for admin cross-bot analysis
@bot.command(name="analyze_user")
@has_permissions(administrator=True)
async def analyze_user_across_bots(ctx, user_id: str, topic: str):
    querier = create_multi_bot_querier()
    
    analysis = await querier.cross_bot_analysis(user_id, topic)
    
    embed = discord.Embed(title=f"Cross-Bot Analysis: {topic}")
    embed.add_field(
        name="Summary",
        value=f"Analyzed {analysis['total_memories']} memories from {len(analysis['bots_analyzed'])} bots"
    )
    
    for bot_name, perspective in analysis['bot_perspectives'].items():
        embed.add_field(
            name=f"🤖 {bot_name}",
            value=f"Memories: {perspective['memory_count']}\nRelevance: {perspective['average_relevance_score']:.2f}",
            inline=True
        )
    
    await ctx.send(embed=embed)
```

### Health Monitoring Integration  
```python
# System health monitoring
async def check_bot_memory_health():
    querier = create_multi_bot_querier()
    stats = await querier.get_bot_memory_stats()
    
    alerts = []
    for bot_name, bot_stats in stats.items():
        # Check for potential issues
        if bot_stats['average_confidence'] < 0.5:
            alerts.append(f"Low confidence in {bot_name}: {bot_stats['average_confidence']}")
        
        if bot_stats['total_memories'] == 0:
            alerts.append(f"No memories found for {bot_name}")
    
    if alerts:
        # Send alerts to monitoring system
        logger.warning(f"Bot memory health issues: {alerts}")
    
    return stats
```

### User Analytics Dashboard
```python
# Generate user analytics across all bots
async def generate_user_analytics(user_id: str):
    querier = create_multi_bot_querier()
    
    # Get comprehensive stats
    user_stats = await querier.get_bot_memory_stats(user_id)
    
    # Analyze user's interaction patterns
    all_memories = await querier.query_all_bots("", user_id, top_k=1000)
    
    analytics = {
        "user_id": user_id,
        "total_interactions": sum(len(memories) for memories in all_memories.values()),
        "preferred_bots": sorted(
            user_stats.items(), 
            key=lambda x: x[1]['total_memories'], 
            reverse=True
        )[:3],
        "interaction_timeline": {
            # Could be expanded with temporal analysis
        }
    }
    
    return analytics
```

## Performance Considerations

### Query Optimization
```python
# Efficient querying patterns

# ✅ Good: Specific bot queries for performance
specific_results = await querier.query_specific_bots(
    "query", "user123", ["Elena"], top_k=5
)

# ⚠️ Caution: Global queries can be expensive
all_results = await querier.query_all_bots(
    "query", "user123", top_k=100  # Large result sets
)

# ✅ Good: Use min_score to filter irrelevant results
filtered_results = await querier.query_all_bots(
    "query", "user123", top_k=10, min_score=0.7
)
```

### Caching Strategies
```python
import asyncio
from functools import lru_cache

class CachedMultiBotQuerier:
    def __init__(self):
        self.querier = create_multi_bot_querier()
        self._stats_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def get_cached_stats(self, user_id=None):
        cache_key = f"stats_{user_id or 'global'}"
        
        if cache_key in self._stats_cache:
            cached_data, timestamp = self._stats_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return cached_data
        
        # Fetch fresh data
        stats = await self.querier.get_bot_memory_stats(user_id)
        self._stats_cache[cache_key] = (stats, time.time())
        return stats
```

## Error Handling

### Robust Query Patterns
```python
async def safe_cross_bot_query(user_id: str, topic: str):
    try:
        querier = create_multi_bot_querier()
        
        # Try full analysis first
        analysis = await querier.cross_bot_analysis(user_id, topic)
        return analysis
        
    except Exception as e:
        logger.error(f"Cross-bot analysis failed: {e}")
        
        # Fallback to individual bot queries
        try:
            fallback_results = {}
            for bot_name in ["Elena", "Gabriel", "Marcus"]:
                try:
                    results = await querier.query_specific_bots(
                        topic, user_id, [bot_name], top_k=5
                    )
                    fallback_results.update(results)
                except Exception as bot_error:
                    logger.warning(f"Query failed for {bot_name}: {bot_error}")
                    continue
            
            return {
                "fallback": True,
                "partial_results": fallback_results,
                "error": str(e)
            }
            
        except Exception as fallback_error:
            logger.error(f"Complete query failure: {fallback_error}")
            return {"error": "All multi-bot queries failed"}
```

## Testing

### Unit Tests
```python
import pytest

@pytest.mark.asyncio
async def test_multi_bot_querier():
    querier = create_multi_bot_querier()
    
    # Test basic functionality
    results = await querier.query_all_bots("test", "test_user")
    assert isinstance(results, dict)
    
    # Test specific bot querying
    specific = await querier.query_specific_bots(
        "test", "test_user", ["Elena"]
    )
    assert "Elena" in specific or len(specific) == 0  # May be empty
    
    # Test statistics
    stats = await querier.get_bot_memory_stats("test_user")
    assert isinstance(stats, dict)
```

### Integration Tests
```python
@pytest.mark.asyncio 
async def test_multi_bot_integration():
    # Create test memories for different bots
    test_memories = {
        "Elena": "Elena loves emotional support",
        "Gabriel": "Gabriel explores consciousness", 
        "Marcus": "Marcus provides analysis"
    }
    
    # Store test memories (implementation specific)
    for bot_name, content in test_memories.items():
        await store_test_memory(bot_name, "test_user", content)
    
    # Test cross-bot querying
    querier = create_multi_bot_querier()
    results = await querier.query_all_bots("test", "test_user")
    
    # Verify isolation working correctly
    elena_results = await querier.query_specific_bots(
        "emotional", "test_user", ["Elena"]
    )
    
    gabriel_results = await querier.query_specific_bots(
        "consciousness", "test_user", ["Gabriel"] 
    )
    
    # Should find Elena's memory in her results, not Gabriel's
    assert len(elena_results.get("Elena", [])) > 0
    assert len(gabriel_results.get("Gabriel", [])) > 0
```

## Security Considerations

### Access Control
```python
class SecureMultiBotQuerier:
    def __init__(self, user_permissions):
        self.querier = create_multi_bot_querier()
        self.permissions = user_permissions
    
    async def authorized_query_all_bots(self, query, user_id):
        # Only admins can query across all bots
        if not self.permissions.get("admin", False):
            raise PermissionError("Admin access required for global queries")
        
        return await self.querier.query_all_bots(query, user_id)
    
    async def authorized_cross_bot_analysis(self, user_id, topic):
        # Users can only analyze their own data
        if user_id != self.permissions.get("user_id") and not self.permissions.get("admin"):
            raise PermissionError("Can only analyze your own memories")
        
        return await self.querier.cross_bot_analysis(user_id, topic)
```

### Privacy Protection
```python
def anonymize_cross_bot_results(results, user_permissions):
    """Remove sensitive information from cross-bot results"""
    if not user_permissions.get("admin", False):
        # Remove specific content for non-admin users
        for bot_name, memories in results.items():
            for memory in memories:
                if len(memory['content']) > 50:
                    memory['content'] = memory['content'][:50] + "..."
                memory.pop('source', None)  # Remove source information
    
    return results
```

This implementation guide provides practical examples and patterns for using the Multi-Bot Memory System effectively while maintaining security and performance best practices.