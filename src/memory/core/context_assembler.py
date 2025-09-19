# src/memory/core/context_assembler.py

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class ContextPriority(Enum):
    """Priority levels for different context sources"""
    CRITICAL = 1.0      # Recent conversations, direct references
    HIGH = 0.8          # Semantic matches, strong topic relationships
    MEDIUM = 0.6        # Related topics, session context
    LOW = 0.4           # Historical patterns, weak associations
    BACKGROUND = 0.2    # General user interests, distant topics

@dataclass
class ContextSource:
    """Represents a source of context information"""
    source_type: str  # 'redis', 'postgresql', 'chromadb', 'neo4j'
    content: str
    metadata: Dict[str, Any]
    priority: ContextPriority
    relevance_score: float
    timestamp: Optional[datetime] = None
    conversation_id: Optional[str] = None
    
    def get_weighted_score(self) -> float:
        """Calculate final weighted score for prioritization"""
        return self.relevance_score * self.priority.value

@dataclass
class AssembledContext:
    """Final assembled context ready for LLM consumption"""
    context_string: str
    context_sources: List[ContextSource]
    assembly_metadata: Dict[str, Any]
    total_length: int
    assembly_time_ms: float
    
    def get_source_breakdown(self) -> Dict[str, int]:
        """Get breakdown of context sources"""
        breakdown = {}
        for source in self.context_sources:
            breakdown[source.source_type] = breakdown.get(source.source_type, 0) + 1
        return breakdown

class IntelligentContextAssembler:
    """
    Intelligent context assembly engine that optimizes context from all tiers
    Target: <100ms assembly time with optimal relevance
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration parameters
        self.max_context_length = self.config.get('max_context_length', 4000)
        self.min_relevance_threshold = self.config.get('min_relevance_threshold', 0.3)
        self.recent_context_weight = self.config.get('recent_context_weight', 0.4)
        self.semantic_context_weight = self.config.get('semantic_context_weight', 0.3)
        self.topical_context_weight = self.config.get('topical_context_weight', 0.2)
        self.historical_context_weight = self.config.get('historical_context_weight', 0.1)
        
        # Performance tracking
        self.assembly_stats = {
            'total_assemblies': 0,
            'avg_assembly_time_ms': 0,
            'avg_context_length': 0,
            'source_usage_frequency': {}
        }
    
    async def assemble_context(
        self,
        user_id: str,
        current_query: str,
        recent_context: List[Dict[str, Any]],
        semantic_context: List[Dict[str, Any]],
        topical_context: List[Dict[str, Any]],
        historical_context: Optional[List[Dict[str, Any]]] = None
    ) -> AssembledContext:
        """
        Intelligently assemble context from all sources with optimal prioritization
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Convert raw context to ContextSource objects
            context_sources = await self._prepare_context_sources(
                recent_context, semantic_context, topical_context, historical_context, current_query
            )
            
            # Step 2: Apply relevance scoring and filtering
            filtered_sources = self._filter_and_score_sources(context_sources, current_query)
            
            # Step 3: Prioritize and select optimal context mix
            selected_sources = self._select_optimal_context_mix(filtered_sources)
            
            # Step 4: Assemble final context string
            context_string = self._build_context_string(selected_sources, current_query)
            
            # Step 5: Create assembly metadata
            assembly_time = (datetime.now() - start_time).total_seconds() * 1000
            
            metadata = {
                'user_id': user_id,
                'current_query': current_query,
                'assembly_time_ms': assembly_time,
                'sources_processed': len(context_sources),
                'sources_selected': len(selected_sources),
                'filtering_threshold': self.min_relevance_threshold,
                'context_weights': {
                    'recent': self.recent_context_weight,
                    'semantic': self.semantic_context_weight,
                    'topical': self.topical_context_weight,
                    'historical': self.historical_context_weight
                }
            }
            
            assembled = AssembledContext(
                context_string=context_string,
                context_sources=selected_sources,
                assembly_metadata=metadata,
                total_length=len(context_string),
                assembly_time_ms=assembly_time
            )
            
            # Update performance statistics
            self._update_stats(assembled)
            
            self.logger.debug("Assembled context for user %s in %.2fms (%d chars from %d sources)",
                           user_id, assembly_time, len(context_string), len(selected_sources))
            
            return assembled
            
        except Exception as e:
            self.logger.error("Failed to assemble context for user %s: %s", user_id, e)
            # Return minimal fallback context
            return self._create_fallback_context(user_id, current_query)
    
    async def _prepare_context_sources(
        self,
        recent_context: List[Dict[str, Any]],
        semantic_context: List[Dict[str, Any]],
        topical_context: List[Dict[str, Any]],
        historical_context: Optional[List[Dict[str, Any]]],
        current_query: str
    ) -> List[ContextSource]:
        """Convert raw context data to structured ContextSource objects"""
        
        sources = []
        
        # Process recent context (Redis)
        for item in recent_context:
            content = self._format_conversation_content(item)
            relevance = self._calculate_recency_relevance(item)
            
            source = ContextSource(
                source_type='redis',
                content=content,
                metadata=item,
                priority=ContextPriority.CRITICAL,
                relevance_score=relevance,
                timestamp=self._parse_timestamp(item.get('timestamp')),
                conversation_id=item.get('conversation_id')
            )
            sources.append(source)
        
        # Process semantic context (ChromaDB)
        for item in semantic_context:
            content = item.get('summary', '')
            relevance = item.get('relevance_score', 0.5)
            
            source = ContextSource(
                source_type='chromadb',
                content=content,
                metadata=item,
                priority=ContextPriority.HIGH,
                relevance_score=relevance,
                conversation_id=item.get('conversation_id')
            )
            sources.append(source)
        
        # Process topical context (Neo4j)
        for item in topical_context:
            content = f"Related topic: {item.get('topic', '')}"
            relevance = item.get('relevance_score', 0.5)
            
            source = ContextSource(
                source_type='neo4j',
                content=content,
                metadata=item,
                priority=ContextPriority.MEDIUM,
                relevance_score=relevance
            )
            sources.append(source)
        
        # Process historical context (PostgreSQL)
        if historical_context:
            for item in historical_context:
                content = self._format_conversation_content(item)
                relevance = self._calculate_historical_relevance(item, current_query)
                
                source = ContextSource(
                    source_type='postgresql',
                    content=content,
                    metadata=item,
                    priority=ContextPriority.LOW,
                    relevance_score=relevance,
                    conversation_id=item.get('conversation_id')
                )
                sources.append(source)
        
        return sources
    
    def _filter_and_score_sources(
        self, 
        sources: List[ContextSource], 
        current_query: str
    ) -> List[ContextSource]:
        """Filter sources by relevance and apply query-specific scoring"""
        
        filtered_sources = []
        query_terms = set(current_query.lower().split())
        
        for source in sources:
            # Apply minimum relevance threshold
            if source.relevance_score < self.min_relevance_threshold:
                continue
            
            # Apply query-specific relevance boost
            content_terms = set(source.content.lower().split())
            term_overlap = len(query_terms.intersection(content_terms))
            
            if term_overlap > 0:
                query_boost = min(0.3, term_overlap * 0.1)  # Up to 30% boost
                source.relevance_score = min(1.0, source.relevance_score + query_boost)
            
            # Apply time decay for older content
            if source.timestamp:
                time_decay = self._calculate_time_decay(source.timestamp)
                source.relevance_score *= time_decay
            
            filtered_sources.append(source)
        
        # Sort by weighted score
        filtered_sources.sort(key=lambda s: s.get_weighted_score(), reverse=True)
        
        return filtered_sources
    
    def _select_optimal_context_mix(self, sources: List[ContextSource]) -> List[ContextSource]:
        """Select optimal mix of context sources within length constraints"""
        
        selected_sources = []
        current_length = 0
        
        # Ensure we have representation from different source types
        source_type_counts = {}
        
        for source in sources:
            # Check length constraint
            estimated_addition = len(source.content) + 50  # Buffer for formatting
            if current_length + estimated_addition > self.max_context_length:
                break
            
            # Ensure balanced representation
            source_type = source.source_type
            current_count = source_type_counts.get(source_type, 0)
            
            # Limits per source type to ensure diversity
            max_per_type = {
                'redis': 5,       # Recent conversations
                'chromadb': 4,    # Semantic summaries
                'neo4j': 3,       # Topic relationships
                'postgresql': 2   # Historical context
            }
            
            if current_count >= max_per_type.get(source_type, 3):
                continue
            
            selected_sources.append(source)
            current_length += estimated_addition
            source_type_counts[source_type] = current_count + 1
        
        return selected_sources
    
    def _build_context_string(
        self, 
        sources: List[ContextSource], 
        current_query: str
    ) -> str:
        """Build the final context string optimized for LLM consumption"""
        
        if not sources:
            return f"Current question: {current_query}\n\nNo relevant conversation history found."
        
        context_sections = []
        
        # Group sources by type for organized presentation
        sources_by_type = {}
        for source in sources:
            if source.source_type not in sources_by_type:
                sources_by_type[source.source_type] = []
            sources_by_type[source.source_type].append(source)
        
        # Add current query at the top
        context_sections.append(f"Current question: {current_query}\n")
        
        # Add recent conversations first (highest priority)
        if 'redis' in sources_by_type:
            context_sections.append("Recent conversation:")
            for source in sources_by_type['redis'][:3]:  # Limit recent context
                context_sections.append(f"- {source.content}")
            context_sections.append("")
        
        # Add semantic context
        if 'chromadb' in sources_by_type:
            context_sections.append("Related past discussions:")
            for source in sources_by_type['chromadb'][:3]:
                relevance = f"({source.relevance_score:.2f})"
                context_sections.append(f"- {source.content} {relevance}")
            context_sections.append("")
        
        # Add topical context
        if 'neo4j' in sources_by_type:
            context_sections.append("Related topics:")
            for source in sources_by_type['neo4j'][:2]:
                context_sections.append(f"- {source.content}")
            context_sections.append("")
        
        # Add historical context if space permits
        if 'postgresql' in sources_by_type and len(context_sections) < 15:
            context_sections.append("Additional context:")
            for source in sources_by_type['postgresql'][:2]:
                context_sections.append(f"- {source.content}")
        
        final_context = "\n".join(context_sections)
        
        # Ensure we don't exceed length limit
        if len(final_context) > self.max_context_length:
            final_context = final_context[:self.max_context_length - 100] + "\n\n[Context truncated for length]"
        
        return final_context
    
    def _format_conversation_content(self, conversation: Dict[str, Any]) -> str:
        """Format conversation data for context inclusion"""
        user_msg = conversation.get('user_message', '')
        bot_msg = conversation.get('bot_response', '')
        
        # Truncate long messages
        if len(user_msg) > 150:
            user_msg = user_msg[:147] + "..."
        if len(bot_msg) > 150:
            bot_msg = bot_msg[:147] + "..."
        
        return f"User: {user_msg} | Bot: {bot_msg}"
    
    def _calculate_recency_relevance(self, item: Dict[str, Any]) -> float:
        """Calculate relevance based on recency"""
        timestamp = self._parse_timestamp(item.get('timestamp'))
        if not timestamp:
            return 0.5
        
        hours_ago = (datetime.now() - timestamp).total_seconds() / 3600
        
        # Relevance decays over time
        if hours_ago < 1:
            return 1.0
        elif hours_ago < 24:
            return 0.9
        elif hours_ago < 168:  # 1 week
            return 0.7
        else:
            return 0.5
    
    def _calculate_historical_relevance(self, item: Dict[str, Any], query: str) -> float:
        """Calculate relevance for historical content"""
        # Simple keyword matching for now
        content = f"{item.get('user_message', '')} {item.get('bot_response', '')}"
        query_terms = set(query.lower().split())
        content_terms = set(content.lower().split())
        
        overlap = len(query_terms.intersection(content_terms))
        max_possible = len(query_terms)
        
        if max_possible == 0:
            return 0.3
        
        return min(0.8, 0.3 + (overlap / max_possible) * 0.5)
    
    def _calculate_time_decay(self, timestamp: datetime) -> float:
        """Calculate time decay factor"""
        days_ago = (datetime.now() - timestamp).days
        
        # Exponential decay
        if days_ago == 0:
            return 1.0
        elif days_ago <= 7:
            return 0.9
        elif days_ago <= 30:
            return 0.8
        elif days_ago <= 90:
            return 0.6
        else:
            return 0.4
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None
        
        try:
            # Handle various timestamp formats
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            return None
    
    def _create_fallback_context(self, user_id: str, current_query: str) -> AssembledContext:
        """Create minimal fallback context when assembly fails"""
        fallback_content = f"Current question: {current_query}\n\nNo conversation history available."
        
        return AssembledContext(
            context_string=fallback_content,
            context_sources=[],
            assembly_metadata={
                'user_id': user_id,
                'current_query': current_query,
                'fallback': True,
                'error': 'Context assembly failed'
            },
            total_length=len(fallback_content),
            assembly_time_ms=0
        )
    
    def _update_stats(self, assembled: AssembledContext):
        """Update performance statistics"""
        self.assembly_stats['total_assemblies'] += 1
        
        # Update average assembly time
        current_avg = self.assembly_stats['avg_assembly_time_ms']
        new_time = assembled.assembly_time_ms
        count = self.assembly_stats['total_assemblies']
        
        self.assembly_stats['avg_assembly_time_ms'] = (current_avg * (count - 1) + new_time) / count
        
        # Update average context length
        current_avg_length = self.assembly_stats['avg_context_length']
        new_length = assembled.total_length
        
        self.assembly_stats['avg_context_length'] = (current_avg_length * (count - 1) + new_length) / count
        
        # Update source usage frequency
        for source in assembled.context_sources:
            source_type = source.source_type
            self.assembly_stats['source_usage_frequency'][source_type] = (
                self.assembly_stats['source_usage_frequency'].get(source_type, 0) + 1
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get assembler performance statistics"""
        return {
            'total_assemblies': self.assembly_stats['total_assemblies'],
            'avg_assembly_time_ms': round(self.assembly_stats['avg_assembly_time_ms'], 2),
            'avg_context_length': round(self.assembly_stats['avg_context_length'], 0),
            'source_usage_frequency': self.assembly_stats['source_usage_frequency'].copy(),
            'configuration': {
                'max_context_length': self.max_context_length,
                'min_relevance_threshold': self.min_relevance_threshold,
                'context_weights': {
                    'recent': self.recent_context_weight,
                    'semantic': self.semantic_context_weight,
                    'topical': self.topical_context_weight,
                    'historical': self.historical_context_weight
                }
            }
        }
    
    def optimize_configuration(self, target_assembly_time_ms: float = 50):
        """Automatically optimize configuration based on performance data"""
        current_avg_time = self.assembly_stats['avg_assembly_time_ms']
        
        if current_avg_time > target_assembly_time_ms:
            # Reduce context length to improve speed
            reduction_factor = target_assembly_time_ms / current_avg_time
            self.max_context_length = int(self.max_context_length * reduction_factor)
            
            # Increase relevance threshold to filter more aggressively
            self.min_relevance_threshold = min(0.6, self.min_relevance_threshold + 0.1)
            
            self.logger.info("Optimized configuration: max_length=%d, min_relevance=%.2f",
                           self.max_context_length, self.min_relevance_threshold)


# Utility functions for testing

async def test_context_assembler():
    """Test the context assembler with sample data"""
    assembler = IntelligentContextAssembler()
    
    # Sample data
    recent_context = [
        {
            'conversation_id': 'conv1',
            'user_message': 'How do I optimize Python code?',
            'bot_response': 'Here are some Python optimization techniques...',
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    semantic_context = [
        {
            'conversation_id': 'conv2',
            'summary': 'Discussion about Python performance optimization',
            'relevance_score': 0.8
        }
    ]
    
    topical_context = [
        {
            'topic': 'python_optimization',
            'relevance_score': 0.7
        }
    ]
    
    # Assemble context
    result = await assembler.assemble_context(
        user_id='test_user',
        current_query='What are the best Python optimization libraries?',
        recent_context=recent_context,
        semantic_context=semantic_context,
        topical_context=topical_context
    )
    
    print(f"Assembled context ({result.total_length} chars in {result.assembly_time_ms:.2f}ms):")
    print(result.context_string)
    print(f"\nSource breakdown: {result.get_source_breakdown()}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_context_assembler())