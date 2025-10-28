"""
Prompt Assembler - Structured Prompt Building System

This module provides the core PromptAssembler class that builds prompts from
discrete, metadata-enriched components. Supports:
- Dynamic component ordering by priority
- Conditional inclusion based on context
- Token budget management
- Content deduplication
- Model-specific formatting (Anthropic, OpenAI, Mistral)

Phase 1: Core Infrastructure
Status: ACTIVE IMPLEMENTATION
"""
import logging
from typing import List, Optional, Set
from collections import defaultdict

from src.prompts.prompt_components import PromptComponent, PromptComponentType


logger = logging.getLogger(__name__)


class PromptAssembler:
    """Assembles structured prompt components into final system prompt.
    
    The assembler manages the lifecycle of prompt assembly:
    1. Component registration with metadata
    2. Filtering by inclusion conditions
    3. Priority-based ordering
    4. Token budget enforcement
    5. Content deduplication
    6. Model-specific formatting
    
    Example:
        ```python
        assembler = PromptAssembler(max_tokens=8000)
        assembler.add_component(core_component)
        assembler.add_component(memory_component)
        assembler.add_component(guidance_component)
        
        final_prompt = assembler.assemble(model_type="anthropic")
        ```
    """
    
    def __init__(self, max_tokens: Optional[int] = None):
        """Initialize the PromptAssembler.
        
        Args:
            max_tokens: Maximum token budget for assembled prompt.
                       If None, no token limit is enforced.
        """
        self.max_tokens = max_tokens
        self.components: List[PromptComponent] = []
        self._assembly_metrics: dict = {}
    
    def add_component(self, component: PromptComponent) -> None:
        """Add a component to the assembly queue.
        
        Args:
            component: PromptComponent to add
        """
        self.components.append(component)
        logger.debug(
            "Added component: type=%s, priority=%d, required=%s, tokens~%d",
            component.type.value,
            component.priority,
            component.required,
            component.estimate_token_cost()
        )
    
    def add_components(self, components: List[PromptComponent]) -> None:
        """Add multiple components to the assembly queue.
        
        Args:
            components: List of PromptComponent objects
        """
        for component in components:
            self.add_component(component)
    
    def assemble(self, model_type: str = "generic") -> str:
        """Assemble components into final prompt.
        
        Args:
            model_type: LLM model type for model-specific formatting
                       ("openai", "anthropic", "mistral", "generic")
        
        Returns:
            Final assembled prompt string
        """
        logger.info(
            "Starting prompt assembly: %d components, model_type=%s, max_tokens=%s",
            len(self.components),
            model_type,
            self.max_tokens if self.max_tokens else "unlimited"
        )
        
        # Filter components
        valid_components = self._filter_components()
        logger.debug("After filtering: %d components remain", len(valid_components))
        
        # Sort by priority (lower number = higher priority)
        valid_components.sort(key=lambda c: c.priority)
        logger.debug("Components sorted by priority")
        
        # Apply token budget if specified
        if self.max_tokens:
            valid_components = self._apply_token_budget(valid_components)
            logger.debug("After token budget: %d components remain", len(valid_components))
        
        # Deduplicate content
        valid_components = self._deduplicate(valid_components)
        logger.debug("After deduplication: %d components remain", len(valid_components))
        
        # Store assembly metrics
        self._store_metrics(valid_components)
        
        # Model-specific formatting
        if model_type == "anthropic":
            result = self._assemble_anthropic(valid_components)
        elif model_type == "openai":
            result = self._assemble_openai(valid_components)
        elif model_type == "mistral":
            result = self._assemble_mistral(valid_components)
        else:
            result = self._assemble_generic(valid_components)
        
        logger.info(
            "Prompt assembly complete: %d chars, ~%d tokens",
            len(result),
            len(result) // 4
        )
        
        return result
    
    def get_assembly_metrics(self) -> dict:
        """Get metrics from last assembly operation.
        
        Returns:
            Dict with assembly metrics (components used, tokens, etc.)
        """
        return self._assembly_metrics.copy()
    
    def _filter_components(self) -> List[PromptComponent]:
        """Filter components based on inclusion conditions.
        
        Returns:
            List of components that should be included
        """
        valid = []
        for component in self.components:
            if component.should_include():
                valid.append(component)
            else:
                logger.debug(
                    "Excluded component: type=%s (failed inclusion check)",
                    component.type.value
                )
        
        return valid
    
    def _apply_token_budget(
        self,
        components: List[PromptComponent]
    ) -> List[PromptComponent]:
        """Drop low-priority optional components if over token budget.
        
        Args:
            components: Sorted list of components (by priority)
            
        Returns:
            List of components within token budget
        """
        total_tokens = sum(c.estimate_token_cost() for c in components)
        
        if self.max_tokens is None or total_tokens <= self.max_tokens:
            logger.debug(
                "Within token budget: %d tokens (limit: %d)",
                total_tokens,
                self.max_tokens
            )
            return components
        
        logger.warning(
            "Over token budget: %d tokens (limit: %d) - dropping optional components",
            total_tokens,
            self.max_tokens
        )
        
        # Keep required components, drop optional ones from lowest priority
        required = [c for c in components if c.required]
        optional = [c for c in components if not c.required]
        
        # Calculate required tokens
        required_tokens = sum(c.estimate_token_cost() for c in required)
        
        if self.max_tokens is not None and required_tokens > self.max_tokens:
            logger.error(
                "Required components exceed token budget: %d > %d - applying intelligent truncation",
                required_tokens,
                self.max_tokens
            )
            # Apply intelligent truncation to required components
            return self._intelligently_truncate_required(required, self.max_tokens)
        
        # Add optional components until budget is reached
        current_tokens = required_tokens
        result = required.copy()
        dropped = []
        
        for component in optional:
            component_tokens = component.estimate_token_cost()
            if self.max_tokens is None or current_tokens + component_tokens <= self.max_tokens:
                result.append(component)
                current_tokens += component_tokens
            else:
                dropped.append(component)
        
        if dropped:
            logger.info(
                "Dropped %d optional components to fit budget: %s",
                len(dropped),
                [c.type.value for c in dropped]
            )
        
        return result
    
    def _intelligently_truncate_required(
        self,
        required_components: List[PromptComponent],
        max_tokens: int
    ) -> List[PromptComponent]:
        """Intelligently truncate required components to fit budget.
        
        Strategy:
        - Preserve highest priority components (core identity)
        - For oversized components, keep beginning (50%) and end (30%)
        - Add graceful truncation notices
        - Ensure critical instructions are preserved
        
        Args:
            required_components: List of required components (already sorted by priority)
            max_tokens: Maximum token budget
            
        Returns:
            List of truncated components within budget
        """
        result = []
        tokens_used = 0
        tokens_available = max_tokens
        
        logger.warning(
            "🎭 Intelligent truncation of %d required components to fit %d token budget",
            len(required_components),
            max_tokens
        )
        
        for component in required_components:
            component_tokens = component.estimate_token_cost()
            
            # If component fits as-is, include it
            if tokens_used + component_tokens <= tokens_available:
                result.append(component)
                tokens_used += component_tokens
                logger.debug(
                    "Preserved component %s: %d tokens (total: %d/%d)",
                    component.type.value,
                    component_tokens,
                    tokens_used,
                    tokens_available
                )
            else:
                # Calculate how much space is left
                remaining_budget = tokens_available - tokens_used
                
                if remaining_budget < 500:  # Not enough space for meaningful content
                    logger.warning(
                        "Dropping component %s: insufficient space (%d tokens left)",
                        component.type.value,
                        remaining_budget
                    )
                    continue
                
                # Truncate this component to fit
                target_chars = remaining_budget * 4  # CHARS_PER_TOKEN = 4
                original_content = component.content
                
                # Keep beginning (50%) and end (30%) of available space
                beginning_chars = int(target_chars * 0.50)
                ending_chars = int(target_chars * 0.30)
                
                beginning = original_content[:beginning_chars]
                ending = original_content[-ending_chars:] if ending_chars > 0 else ""
                
                truncation_notice = (
                    f"\n\n[{component.type.value} truncated to fit token budget. "
                    f"Core content preserved.]\n\n"
                )
                
                truncated_content = beginning + truncation_notice + ending
                
                # Create truncated component
                truncated_component = PromptComponent(
                    type=component.type,
                    content=truncated_content,
                    priority=component.priority,
                    required=component.required,
                    condition=component.condition,
                    token_cost=None,  # Will be recalculated
                    metadata=component.metadata
                )
                
                result.append(truncated_component)
                tokens_used += truncated_component.estimate_token_cost()
                
                logger.warning(
                    "Truncated component %s: %d → %d tokens (preserved %d%%)",
                    component.type.value,
                    component_tokens,
                    truncated_component.estimate_token_cost(),
                    int((truncated_component.estimate_token_cost() / component_tokens) * 100)
                )
                
                # Budget exhausted
                if tokens_used >= tokens_available:
                    logger.warning(
                        "Token budget exhausted after truncating %s. Dropping remaining components.",
                        component.type.value
                    )
                    break
        
        logger.info(
            "Intelligent truncation complete: %d components kept, %d tokens used of %d budget",
            len(result),
            tokens_used,
            tokens_available
        )
        
        return result
    
    def _deduplicate(
        self,
        components: List[PromptComponent]
    ) -> List[PromptComponent]:
        """Remove duplicate content across components.
        
        Args:
            components: List of components to deduplicate
            
        Returns:
            List with duplicates removed
        """
        seen_content: Set[str] = set()
        deduplicated = []
        
        for component in components:
            # Create content hash for deduplication (first 200 chars)
            content_hash = component.content[:200].strip().lower()
            
            if content_hash not in seen_content:
                deduplicated.append(component)
                seen_content.add(content_hash)
            else:
                logger.debug(
                    "Deduplicated component: type=%s (duplicate content)",
                    component.type.value
                )
        
        return deduplicated
    
    def _store_metrics(self, components: List[PromptComponent]) -> None:
        """Store assembly metrics for debugging/monitoring.
        
        Args:
            components: Final list of components used
        """
        total_tokens = sum(c.estimate_token_cost() for c in components)
        
        # Count components by type
        type_counts = defaultdict(int)
        for component in components:
            type_counts[component.type.value] += 1
        
        self._assembly_metrics = {
            'total_components': len(components),
            'total_tokens': total_tokens,
            'total_chars': sum(len(c.content) for c in components),
            'required_components': sum(1 for c in components if c.required),
            'optional_components': sum(1 for c in components if not c.required),
            'components_by_type': dict(type_counts),
            'token_budget': self.max_tokens,
            'within_budget': total_tokens <= self.max_tokens if self.max_tokens else True
        }
    
    def _assemble_generic(self, components: List[PromptComponent]) -> str:
        """Assemble components with generic formatting.
        
        Args:
            components: List of components to assemble
            
        Returns:
            Assembled prompt string
        """
        # Simple concatenation with double newlines
        parts = [component.content for component in components]
        return "\n\n".join(parts)
    
    def _assemble_anthropic(self, components: List[PromptComponent]) -> str:
        """Assemble components with Anthropic Claude XML formatting.
        
        Claude works well with XML-structured prompts for clarity.
        
        Args:
            components: List of components to assemble
            
        Returns:
            Assembled prompt string with XML structure
        """
        # TODO: Implement Anthropic XML formatting
        # For now, use generic formatting
        logger.debug("Anthropic formatting not yet implemented, using generic")
        return self._assemble_generic(components)
    
    def _assemble_openai(self, components: List[PromptComponent]) -> str:
        """Assemble components with OpenAI section formatting.
        
        OpenAI models work well with clear section headers.
        
        Args:
            components: List of components to assemble
            
        Returns:
            Assembled prompt string with section headers
        """
        # TODO: Implement OpenAI section formatting
        # For now, use generic formatting
        logger.debug("OpenAI formatting not yet implemented, using generic")
        return self._assemble_generic(components)
    
    def _assemble_mistral(self, components: List[PromptComponent]) -> str:
        """Assemble components optimized for Mistral models.
        
        Mistral models prefer concise, structured prompts.
        
        Args:
            components: List of components to assemble
            
        Returns:
            Assembled prompt string optimized for Mistral
        """
        # TODO: Implement Mistral optimization
        # For now, use generic formatting
        logger.debug("Mistral formatting not yet implemented, using generic")
        return self._assemble_generic(components)


def create_prompt_assembler(max_tokens: Optional[int] = None) -> PromptAssembler:
    """Factory function to create a PromptAssembler instance.
    
    Args:
        max_tokens: Maximum token budget (None for unlimited)
        
    Returns:
        PromptAssembler instance
    """
    return PromptAssembler(max_tokens=max_tokens)
