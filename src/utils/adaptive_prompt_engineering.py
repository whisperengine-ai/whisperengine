#!/usr/bin/env python3
"""
Adaptive Prompt Engineering for WhisperEngine

This module implements model-size-aware prompt engineering that automatically
adjusts prompt complexity, length, and structure based on the detected LLM
model capabilities and context window size.

Key Features:
- Automatic model capability detection (small/medium/large)
- Context window optimization based on model type
- Dynamic prompt compression for resource-constrained models
- Model-specific prompt templates and strategies
- Token budget management across different prompt types
- Performance monitoring and optimization feedback

Model Categories:
- Small Models (1B-3B params): Minimal prompts, essential instructions only
- Medium Models (3B-8B params): Balanced prompts with moderate context
- Large Models (8B+ params): Full-featured prompts with rich context
"""

import os
import re
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelSize(Enum):
    """Model size categories based on parameter count and capabilities"""
    SMALL = "small"    # 1B-3B params, limited context (1K-4K tokens)
    MEDIUM = "medium"  # 3B-8B params, moderate context (4K-8K tokens)
    LARGE = "large"    # 8B+ params, large context (8K+ tokens)


@dataclass
class ModelCapabilities:
    """Detected model capabilities and constraints"""
    size: ModelSize
    context_window: int
    max_tokens_response: int
    supports_complex_reasoning: bool
    supports_long_conversations: bool
    model_name: str
    estimated_params: str
    performance_tier: str  # "fast", "balanced", "quality"


@dataclass
class PromptBudget:
    """Token budget allocation for different prompt components"""
    total_budget: int
    system_prompt: int
    conversation_history: int
    memory_context: int
    user_message: int
    response_reserve: int
    
    def validate(self) -> bool:
        """Validate that budget allocations don't exceed total"""
        allocated = (self.system_prompt + self.conversation_history + 
                    self.memory_context + self.user_message + self.response_reserve)
        return allocated <= self.total_budget


class AdaptivePromptManager:
    """
    Manages adaptive prompt engineering based on model capabilities
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.prompts_dir = self.project_root / "prompts"
        self.optimized_dir = self.prompts_dir / "optimized"
        self.quick_templates_dir = self.optimized_dir / "quick_templates"
        
        # Model capability cache
        self._model_capabilities: Optional[ModelCapabilities] = None
        self._prompt_templates_cache: Dict[str, str] = {}
        
        # Performance metrics
        self._performance_history: Dict[str, List[float]] = {}
        
        logger.info("🎯 Adaptive Prompt Manager initialized")
    
    def detect_model_capabilities(self) -> ModelCapabilities:
        """
        Detect current model capabilities and constraints
        """
        if self._model_capabilities:
            return self._model_capabilities
        
        # Get model info from environment
        model_name = os.getenv("LLM_CHAT_MODEL", "unknown").lower()
        max_tokens = int(os.getenv("LLM_MAX_TOKENS_CHAT", "4096"))
        
        # Detect model size based on name patterns
        size = self._classify_model_size(model_name)
        
        # Determine context window based on model and configuration
        context_window = self._estimate_context_window(model_name, max_tokens)
        
        # Estimate capabilities based on size and known model characteristics
        model_capabilities = ModelCapabilities(
            size=size,
            context_window=context_window,
            max_tokens_response=min(max_tokens, context_window // 3),  # Reserve 2/3 for input
            supports_complex_reasoning=size != ModelSize.SMALL,
            supports_long_conversations=context_window >= 4096,
            model_name=model_name,
            estimated_params=self._estimate_param_count(model_name),
            performance_tier=self._determine_performance_tier(size, model_name)
        )
        
        self._model_capabilities = model_capabilities
        logger.info("🤖 Detected model: %s (%s) - Context: %s, Performance: %s",
                   size.value, model_capabilities.estimated_params,
                   context_window, model_capabilities.performance_tier)
        
        return model_capabilities
    
    def _classify_model_size(self, model_name: str) -> ModelSize:
        """Classify model size based on name patterns"""
        model_name_lower = model_name.lower()
        
        # Small models (1B-3B)
        small_patterns = [
            r'1\.?1?b', r'1\.?5b', r'2\.?7?b', r'3\.?2?b', r'3b',
            r'tiny', r'mini', r'small', r'phi-?3?-?mini', r'gemma-?2b'
        ]
        
        # Large models (8B+)
        large_patterns = [
            r'8b', r'13b', r'20b', r'30b', r'70b', r'large', r'xl',
            r'gpt-4', r'claude-3', r'llama-?3\.?1?-?8b'
        ]
        
        # Check for small models first
        for pattern in small_patterns:
            if re.search(pattern, model_name_lower):
                return ModelSize.SMALL
        
        # Check for large models
        for pattern in large_patterns:
            if re.search(pattern, model_name_lower):
                return ModelSize.LARGE
        
        # Default to medium (3B-8B)
        return ModelSize.MEDIUM
    
    def _estimate_context_window(self, model_name: str, configured_max: int) -> int:
        """Estimate actual context window size"""
        model_lower = model_name.lower()
        
        # Known context windows for specific models
        context_mappings = {
            'phi-3': 4096,
            'llama-3.2': 8192,
            'llama-3.1': 8192,
            'gemma': 2048,
            'tinyllama': 2048,
            'gpt-4': 8192,
            'claude-3': 200000,
        }
        
        # Check for known models
        for model_key, context_size in context_mappings.items():
            if model_key in model_lower:
                return min(configured_max, context_size)
        
        # Fallback based on configured max
        return configured_max
    
    def _estimate_param_count(self, model_name: str) -> str:
        """Estimate parameter count from model name"""
        model_lower = model_name.lower()
        
        if any(x in model_lower for x in ['1.1b', '1b', 'tiny']):
            return "1B"
        elif any(x in model_lower for x in ['2.7b', '2b', 'mini']):
            return "2-3B"  
        elif any(x in model_lower for x in ['3.2b', '3b']):
            return "3B"
        elif any(x in model_lower for x in ['7b', '8b']):
            return "7-8B"
        elif any(x in model_lower for x in ['13b']):
            return "13B"
        elif any(x in model_lower for x in ['20b', '30b', '70b']):
            return "20B+"
        else:
            return "Unknown"
    
    def _determine_performance_tier(self, size: ModelSize, model_name: str) -> str:
        """Determine performance tier for optimization strategy"""
        # Use model_name for future enhancements
        _ = model_name  # Acknowledge parameter for future use
        
        if size == ModelSize.SMALL:
            return "fast"  # Prioritize speed and minimal resource usage
        elif size == ModelSize.LARGE:
            return "quality"  # Prioritize output quality and complexity
        else:
            return "balanced"  # Balance between speed and quality
    
    def calculate_prompt_budget(self, conversation_length: int = 0, 
                               memory_items: int = 0) -> PromptBudget:
        """
        Calculate optimal token budget allocation based on model capabilities
        """
        capabilities = self.detect_model_capabilities()
        total_budget = capabilities.context_window
        response_reserve = capabilities.max_tokens_response
        
        # Base allocations based on model size
        if capabilities.size == ModelSize.SMALL:
            # Minimal allocations for small models
            base_allocations = {
                'system_prompt': min(500, total_budget * 0.15),
                'conversation_history': min(800, total_budget * 0.25),
                'memory_context': min(400, total_budget * 0.15),
                'user_message': min(300, total_budget * 0.10)
            }
        elif capabilities.size == ModelSize.MEDIUM:
            # Balanced allocations for medium models
            base_allocations = {
                'system_prompt': min(1000, total_budget * 0.20),
                'conversation_history': min(1500, total_budget * 0.30),
                'memory_context': min(800, total_budget * 0.20),
                'user_message': min(500, total_budget * 0.10)
            }
        else:  # LARGE
            # Rich allocations for large models
            base_allocations = {
                'system_prompt': min(2000, total_budget * 0.25),
                'conversation_history': min(3000, total_budget * 0.35),
                'memory_context': min(1500, total_budget * 0.25),
                'user_message': min(800, total_budget * 0.10)
            }
        
        # Adjust based on actual usage
        if conversation_length == 0:
            # No conversation history - reallocate to memory and system
            extra_tokens = base_allocations['conversation_history']
            base_allocations['conversation_history'] = 0
            base_allocations['memory_context'] += extra_tokens * 0.6
            base_allocations['system_prompt'] += extra_tokens * 0.4
        
        if memory_items == 0:
            # No memory context - reallocate to conversation and system
            extra_tokens = base_allocations['memory_context']
            base_allocations['memory_context'] = 0
            base_allocations['conversation_history'] += extra_tokens * 0.7
            base_allocations['system_prompt'] += extra_tokens * 0.3
        
        budget = PromptBudget(
            total_budget=total_budget,
            system_prompt=int(base_allocations['system_prompt']),
            conversation_history=int(base_allocations['conversation_history']),
            memory_context=int(base_allocations['memory_context']),
            user_message=int(base_allocations['user_message']),
            response_reserve=response_reserve
        )
        
        # Validate and adjust if needed
        if not budget.validate():
            # Scale down proportionally
            scale_factor = 0.9
            budget.system_prompt = int(budget.system_prompt * scale_factor)
            budget.conversation_history = int(budget.conversation_history * scale_factor)
            budget.memory_context = int(budget.memory_context * scale_factor)
            budget.user_message = int(budget.user_message * scale_factor)
        
        return budget
    
    def get_adaptive_system_prompt(self, personality_type: str = "default", 
                                  context_items: int = 0) -> Tuple[str, Dict[str, Any]]:
        """
        Get system prompt optimized for current model capabilities
        """
        capabilities = self.detect_model_capabilities()
        budget = self.calculate_prompt_budget(memory_items=context_items)
        
        # Select appropriate template based on model size
        template_path = self._select_optimal_template(capabilities, personality_type)
        
        # Load and process template
        prompt_content = self._load_and_process_template(
            template_path, capabilities, budget.system_prompt
        )
        
        metadata = {
            'model_size': capabilities.size.value,
            'template_used': str(template_path),
            'estimated_tokens': self._estimate_token_count(prompt_content),
            'budget_allocated': budget.system_prompt,
            'optimization_strategy': capabilities.performance_tier
        }
        
        return prompt_content, metadata
    
    def _select_optimal_template(self, capabilities: ModelCapabilities, 
                                personality_type: str) -> Path:
        """Select the most appropriate template for model capabilities"""
        
        # Template selection based on model size
        if capabilities.size == ModelSize.SMALL:
            # Use minimal templates for small models
            if personality_type == "dream":
                template_path = self.quick_templates_dir / "dream_minimal.md"
            else:
                template_path = self.quick_templates_dir / "companion_minimal.md"
        
        elif capabilities.size == ModelSize.MEDIUM:
            # Use optimized templates for medium models
            if personality_type == "dream":
                template_path = self.optimized_dir / "system_prompt_optimized.md"
            else:
                template_path = self.optimized_dir / "default_optimized.md"
        
        else:  # LARGE
            # Use full templates for large models
            if personality_type == "dream":
                template_path = self.prompts_dir / "dream_ai_enhanced.md"
            else:
                template_path = self.prompts_dir / "default.md"
        
        # Fallback chain if preferred template doesn't exist
        fallback_chain = [
            template_path,
            self.optimized_dir / "system_prompt_optimized.md",
            self.prompts_dir / "default.md"
        ]
        
        for path in fallback_chain:
            if path.exists():
                return path
        
        # Emergency fallback
        return self.prompts_dir / "default.md"
    
    def _load_and_process_template(self, template_path: Path, 
                                  capabilities: ModelCapabilities, 
                                  token_budget: int) -> str:
        """Load template and apply model-specific optimizations"""
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            logger.warning("Template not found: %s", template_path)
            content = "You are a helpful AI assistant."
        
        # Apply model-specific optimizations
        if capabilities.size == ModelSize.SMALL:
            content = self._compress_prompt_for_small_model(content, token_budget)
        elif capabilities.size == ModelSize.MEDIUM:
            content = self._optimize_prompt_for_medium_model(content, token_budget)
        else:  # LARGE
            content = self._enhance_prompt_for_large_model(content, token_budget)
        
        return content
    
    def _compress_prompt_for_small_model(self, content: str, token_budget: int) -> str:
        """Compress prompt for small models - focus on essentials"""
        
        # Remove optional sections for small models
        sections_to_remove = [
            r'## Advanced Features.*?(?=##|\Z)',
            r'## Complex Instructions.*?(?=##|\Z)',
            r'## Extended Context.*?(?=##|\Z)',
            r'### Optional:.*?(?=###|\Z)',
        ]
        
        for section_pattern in sections_to_remove:
            content = re.sub(section_pattern, '', content, flags=re.DOTALL)
        
        # Simplify language and remove redundancy
        optimizations = [
            (r'\n\n\n+', '\n\n'),  # Remove excessive newlines
            (r'(?i)please\s+', ''),  # Remove "please"
            (r'(?i)remember\s+to\s+', ''),  # Remove "remember to"
            (r'(?i)make\s+sure\s+to\s+', ''),  # Remove "make sure to"
            (r'(?i)it\s+is\s+important\s+to\s+', ''),  # Remove verbose phrasing
        ]
        
        for pattern, replacement in optimizations:
            content = re.sub(pattern, replacement, content)
        
        # Truncate if still too long
        estimated_tokens = self._estimate_token_count(content)
        if estimated_tokens > token_budget:
            # Keep only the first 80% of content
            target_chars = int(len(content) * 0.8 * (token_budget / estimated_tokens))
            content = content[:target_chars]
            # Ensure we end at a sentence boundary
            last_period = content.rfind('.')
            if last_period > len(content) * 0.5:
                content = content[:last_period + 1]
        
        return content.strip()
    
    def _optimize_prompt_for_medium_model(self, content: str, token_budget: int) -> str:
        """Optimize prompt for medium models - balanced approach"""
        
        # Remove only the most advanced sections
        sections_to_remove = [
            r'## Advanced Reasoning.*?(?=##|\Z)',
            r'## Complex Analysis.*?(?=##|\Z)',
        ]
        
        for section_pattern in sections_to_remove:
            content = re.sub(section_pattern, '', content, flags=re.DOTALL)
        
        # Light optimization
        content = re.sub(r'\n\n\n+', '\n\n', content)  # Remove excessive newlines
        
        # Check token budget and truncate if needed
        estimated_tokens = self._estimate_token_count(content)
        if estimated_tokens > token_budget:
            target_chars = int(len(content) * (token_budget / estimated_tokens))
            content = content[:target_chars]
            # Ensure we end at a section boundary
            last_section = content.rfind('\n##')
            if last_section > len(content) * 0.7:
                content = content[:last_section]
        
        return content.strip()
    
    def _enhance_prompt_for_large_model(self, content: str, token_budget: int) -> str:
        """Enhance prompt for large models - full capabilities"""
        
        # Add model-specific enhancements for large models
        if "AI_SYSTEM_CONTEXT" in content:
            # Add advanced context for large models
            advanced_context = """
**Advanced Capabilities Available**: Complex reasoning, extended memory integration, 
nuanced emotional understanding, sophisticated conversation patterns, creative expression."""
            
            content = content.replace(
                "{AI_SYSTEM_CONTEXT}", 
                f"{{AI_SYSTEM_CONTEXT}}\n{advanced_context}"
            )
        
        # No need to compress for large models unless budget is exceeded
        estimated_tokens = self._estimate_token_count(content)
        if estimated_tokens > token_budget * 1.1:  # Allow 10% buffer
            # Gentle truncation only if significantly over budget
            target_chars = int(len(content) * (token_budget / estimated_tokens))
            content = content[:target_chars]
        
        return content.strip()
    
    def _estimate_token_count(self, text: str) -> int:
        """Rough token count estimation (1 token ≈ 4 characters for English)"""
        return len(text) // 4
    
    def optimize_conversation_history(self, history: List[Dict[str, Any]], 
                                    token_budget: int) -> List[Dict[str, Any]]:
        """
        Optimize conversation history based on model capabilities and token budget
        """
        capabilities = self.detect_model_capabilities()
        
        if not history or token_budget <= 0:
            return []
        
        # Strategy based on model size
        if capabilities.size == ModelSize.SMALL:
            # Keep only the most recent and important messages
            return self._compress_history_for_small_model(history, token_budget)
        elif capabilities.size == ModelSize.MEDIUM:
            # Balanced approach - keep recent + summarize older
            return self._optimize_history_for_medium_model(history, token_budget)
        else:  # LARGE
            # Keep full context with intelligent truncation
            return self._preserve_history_for_large_model(history, token_budget)
    
    def _compress_history_for_small_model(self, history: List[Dict[str, Any]], 
                                        token_budget: int) -> List[Dict[str, Any]]:
        """Aggressive compression for small models"""
        # Keep only last few messages and summarize older ones
        max_messages = 6
        recent_history = history[-max_messages:]
        
        # Estimate tokens and truncate if needed
        total_tokens = sum(self._estimate_token_count(str(msg)) for msg in recent_history)
        
        while total_tokens > token_budget and len(recent_history) > 2:
            # Remove oldest message
            recent_history.pop(0)
            total_tokens = sum(self._estimate_token_count(str(msg)) for msg in recent_history)
        
        return recent_history
    
    def _optimize_history_for_medium_model(self, history: List[Dict[str, Any]], 
                                         token_budget: int) -> List[Dict[str, Any]]:
        """Balanced optimization for medium models"""
        if len(history) <= 10:
            return history  # Keep all if reasonable length
        
        # Keep recent messages + sample of older important ones
        recent_count = min(8, len(history))
        recent_history = history[-recent_count:]
        older_history = history[:-recent_count]
        
        # Sample important older messages (every 3rd message)
        sampled_older = older_history[::3] if older_history else []
        
        combined = sampled_older + recent_history
        
        # Check token budget
        total_tokens = sum(self._estimate_token_count(str(msg)) for msg in combined)
        
        while total_tokens > token_budget and len(combined) > recent_count:
            # Remove from sampled older messages first
            if len(sampled_older) > 0:
                sampled_older.pop(0)
                combined = sampled_older + recent_history
            else:
                recent_history.pop(0)
                combined = recent_history
            
            total_tokens = sum(self._estimate_token_count(str(msg)) for msg in combined)
        
        return combined
    
    def _preserve_history_for_large_model(self, history: List[Dict[str, Any]], 
                                        token_budget: int) -> List[Dict[str, Any]]:
        """Preserve maximum context for large models"""
        # Try to keep full history if within budget
        total_tokens = sum(self._estimate_token_count(str(msg)) for msg in history)
        
        if total_tokens <= token_budget:
            return history
        
        # Intelligent truncation - keep recent + important older messages
        # This could be enhanced with actual importance scoring
        target_messages = int(len(history) * (token_budget / total_tokens))
        target_messages = max(target_messages, 10)  # Keep at least 10 messages
        
        if target_messages >= len(history):
            return history
        
        # Keep most recent messages
        return history[-target_messages:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and optimization suggestions"""
        capabilities = self.detect_model_capabilities()
        
        metrics = {
            'model_info': {
                'size': capabilities.size.value,
                'estimated_params': capabilities.estimated_params,
                'context_window': capabilities.context_window,
                'performance_tier': capabilities.performance_tier
            },
            'optimization_active': True,
            'template_strategy': self._get_current_strategy(),
            'recommendations': self._get_optimization_recommendations(capabilities)
        }
        
        return metrics
    
    def _get_current_strategy(self) -> str:
        """Get current optimization strategy description"""
        if not self._model_capabilities:
            return "Not initialized"
        
        size = self._model_capabilities.size
        if size == ModelSize.SMALL:
            return "Minimal prompts, aggressive compression, essential instructions only"
        elif size == ModelSize.MEDIUM:
            return "Balanced approach, moderate context, optimized templates"
        else:
            return "Full-featured prompts, rich context, advanced capabilities"
    
    def _get_optimization_recommendations(self, capabilities: ModelCapabilities) -> List[str]:
        """Get optimization recommendations based on model capabilities"""
        recommendations = []
        
        if capabilities.size == ModelSize.SMALL:
            recommendations.extend([
                "✨ Using minimal templates optimized for small models",
                "✨ Aggressive prompt compression active for better performance",
                "💡 Consider upgrading to a larger model for richer conversations"
            ])
        elif capabilities.size == ModelSize.MEDIUM:
            recommendations.extend([
                "⚖️ Balanced optimization for medium models",
                "🎯 Using optimized templates with moderate context",
                "✅ Good balance between performance and capability"
            ])
        else:
            recommendations.extend([
                "🎉 Full-featured prompts for large models",
                "🧠 Rich context and advanced reasoning capabilities enabled",
                "⭐ Maximum conversation quality available"
            ])
        
        if capabilities.context_window < 4096:
            recommendations.append("⚠️ Limited context window - conversation history will be truncated")
        
        return recommendations


# Factory function for easy integration
def create_adaptive_prompt_manager(project_root: Optional[Path] = None) -> AdaptivePromptManager:
    """Create and return an adaptive prompt manager instance"""
    return AdaptivePromptManager(project_root)


# Integration helper for existing codebase
def get_model_optimized_prompt(personality_type: str = "default", 
                              context_items: int = 0,
                              project_root: Optional[Path] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Get a model-optimized prompt - convenience function for existing code
    
    Returns:
        Tuple of (prompt_content, optimization_metadata)
    """
    adaptive_manager = create_adaptive_prompt_manager(project_root)
    return adaptive_manager.get_adaptive_system_prompt(personality_type, context_items)


if __name__ == "__main__":
    # Demo the adaptive prompt system
    print("🎯 WhisperEngine Adaptive Prompt Engineering")
    print("=" * 50)
    
    prompt_manager = AdaptivePromptManager()
    
    # Show model detection
    detected_capabilities = prompt_manager.detect_model_capabilities()
    print(f"🤖 Detected Model: {detected_capabilities.size.value} ({detected_capabilities.estimated_params})")
    print(f"📊 Context Window: {detected_capabilities.context_window:,} tokens")
    print(f"⚡ Performance Tier: {detected_capabilities.performance_tier}")
    print()
    
    # Show budget calculation
    calculated_budget = prompt_manager.calculate_prompt_budget(conversation_length=5, memory_items=3)
    print("💰 Token Budget Allocation:")
    print(f"  System Prompt: {calculated_budget.system_prompt:,} tokens")
    print(f"  Conversation History: {calculated_budget.conversation_history:,} tokens")
    print(f"  Memory Context: {calculated_budget.memory_context:,} tokens")
    print(f"  Response Reserve: {calculated_budget.response_reserve:,} tokens")
    print()
    
    # Show optimization metrics
    performance_metrics = prompt_manager.get_performance_metrics()
    print("📈 Current Optimization Strategy:")
    print(f"  {performance_metrics['template_strategy']}")
    print()
    print("💡 Recommendations:")
    for rec in performance_metrics['recommendations']:
        print(f"  {rec}")