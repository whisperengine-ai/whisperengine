"""
Unit Tests for Structured Prompt Assembly System

Tests the core infrastructure:
- PromptComponent creation and metadata
- PromptAssembler filtering and ordering
- Token budget management
- Content deduplication
- Component factory functions

Phase 1: Core Infrastructure
Status: ACTIVE IMPLEMENTATION
"""
import pytest
from src.prompts.prompt_components import (
    PromptComponent,
    PromptComponentType,
    create_core_system_component,
    create_memory_component,
    create_anti_hallucination_component,
    create_guidance_component,
    create_ai_intelligence_component
)
from src.prompts.prompt_assembler import PromptAssembler, create_prompt_assembler


class TestPromptComponent:
    """Tests for PromptComponent dataclass."""
    
    def test_component_creation(self):
        """Test basic component creation."""
        component = PromptComponent(
            type=PromptComponentType.CORE_SYSTEM,
            content="Test content",
            priority=1,
            required=True
        )
        
        assert component.type == PromptComponentType.CORE_SYSTEM
        assert component.content == "Test content"
        assert component.priority == 1
        assert component.required is True
    
    def test_should_include_empty_content(self):
        """Test that empty content is excluded."""
        component = PromptComponent(
            type=PromptComponentType.MEMORY,
            content="",
            priority=4
        )
        
        assert component.should_include() is False
    
    def test_should_include_with_condition(self):
        """Test conditional inclusion."""
        # Condition returns True
        component1 = PromptComponent(
            type=PromptComponentType.MEMORY,
            content="Test",
            priority=4,
            condition=lambda: True
        )
        assert component1.should_include() is True
        
        # Condition returns False
        component2 = PromptComponent(
            type=PromptComponentType.MEMORY,
            content="Test",
            priority=4,
            condition=lambda: False
        )
        assert component2.should_include() is False
    
    def test_token_cost_estimation(self):
        """Test token cost estimation."""
        # Explicit token cost
        component1 = PromptComponent(
            type=PromptComponentType.MEMORY,
            content="Test content",
            priority=4,
            token_cost=100
        )
        assert component1.estimate_token_cost() == 100
        
        # Estimated token cost (4 chars per token)
        component2 = PromptComponent(
            type=PromptComponentType.MEMORY,
            content="A" * 400,  # 400 chars = ~100 tokens
            priority=4
        )
        assert component2.estimate_token_cost() == 100


class TestPromptAssembler:
    """Tests for PromptAssembler class."""
    
    def test_assembler_creation(self):
        """Test basic assembler creation."""
        assembler = PromptAssembler(max_tokens=1000)
        
        assert assembler.max_tokens == 1000
        assert len(assembler.components) == 0
    
    def test_add_component(self):
        """Test adding components."""
        assembler = PromptAssembler()
        component = PromptComponent(
            type=PromptComponentType.CORE_SYSTEM,
            content="Test",
            priority=1
        )
        
        assembler.add_component(component)
        
        assert len(assembler.components) == 1
        assert assembler.components[0] == component
    
    def test_add_multiple_components(self):
        """Test adding multiple components."""
        assembler = PromptAssembler()
        components = [
            PromptComponent(type=PromptComponentType.CORE_SYSTEM, content="A", priority=1),
            PromptComponent(type=PromptComponentType.MEMORY, content="B", priority=2),
            PromptComponent(type=PromptComponentType.GUIDANCE, content="C", priority=3)
        ]
        
        assembler.add_components(components)
        
        assert len(assembler.components) == 3
    
    def test_priority_ordering(self):
        """Test that components are ordered by priority."""
        assembler = PromptAssembler()
        
        # Add components in reverse priority order
        assembler.add_component(PromptComponent(
            type=PromptComponentType.GUIDANCE, content="Low priority", priority=10
        ))
        assembler.add_component(PromptComponent(
            type=PromptComponentType.CORE_SYSTEM, content="High priority", priority=1
        ))
        assembler.add_component(PromptComponent(
            type=PromptComponentType.MEMORY, content="Medium priority", priority=5
        ))
        
        result = assembler.assemble()
        
        # Should be ordered: High (1), Medium (5), Low (10)
        assert result.index("High priority") < result.index("Medium priority")
        assert result.index("Medium priority") < result.index("Low priority")
    
    def test_token_budget_enforcement(self):
        """Test that token budget is enforced."""
        assembler = PromptAssembler(max_tokens=50)  # Very small budget
        
        # Add required component (will always be included)
        assembler.add_component(PromptComponent(
            type=PromptComponentType.CORE_SYSTEM,
            content="A" * 100,  # ~25 tokens
            priority=1,
            required=True
        ))
        
        # Add optional components (may be dropped)
        assembler.add_component(PromptComponent(
            type=PromptComponentType.MEMORY,
            content="B" * 100,  # ~25 tokens
            priority=2,
            required=False
        ))
        
        assembler.add_component(PromptComponent(
            type=PromptComponentType.GUIDANCE,
            content="C" * 100,  # ~25 tokens
            priority=3,
            required=False
        ))
        
        result = assembler.assemble()
        metrics = assembler.get_assembly_metrics()
        
        # Should have dropped at least one optional component
        assert metrics['total_tokens'] <= 50
        assert "A" in result  # Required component always present
    
    def test_deduplication(self):
        """Test content deduplication."""
        assembler = PromptAssembler()
        
        # Add duplicate content
        assembler.add_component(PromptComponent(
            type=PromptComponentType.MEMORY,
            content="Duplicate content here",
            priority=1
        ))
        assembler.add_component(PromptComponent(
            type=PromptComponentType.MEMORY,
            content="Duplicate content here",  # Exact duplicate
            priority=2
        ))
        
        result = assembler.assemble()
        
        # Should only appear once
        assert result.count("Duplicate content here") == 1
    
    def test_assembly_metrics(self):
        """Test that assembly metrics are collected."""
        assembler = PromptAssembler()
        
        assembler.add_component(PromptComponent(
            type=PromptComponentType.CORE_SYSTEM,
            content="Test",
            priority=1,
            required=True
        ))
        
        assembler.assemble()
        metrics = assembler.get_assembly_metrics()
        
        assert 'total_components' in metrics
        assert 'total_tokens' in metrics
        assert 'total_chars' in metrics
        assert metrics['total_components'] == 1


class TestComponentFactories:
    """Tests for component factory functions."""
    
    def test_create_core_system_component(self):
        """Test core system component factory."""
        component = create_core_system_component("System prompt", priority=1)
        
        assert component.type == PromptComponentType.CORE_SYSTEM
        assert component.content == "System prompt"
        assert component.priority == 1
        assert component.required is True
    
    def test_create_memory_component(self):
        """Test memory component factory."""
        component = create_memory_component("Memory narrative", priority=4)
        
        assert component.type == PromptComponentType.MEMORY
        assert component.content == "Memory narrative"
        assert component.priority == 4
        assert component.required is False
    
    def test_create_anti_hallucination_component(self):
        """Test anti-hallucination component factory."""
        component = create_anti_hallucination_component(priority=4)
        
        assert component.type == PromptComponentType.ANTI_HALLUCINATION
        assert "MEMORY STATUS" in component.content
        assert component.priority == 4
        assert component.required is True
    
    def test_create_guidance_component(self):
        """Test guidance component factory."""
        component = create_guidance_component("TestBot", priority=6)
        
        assert component.type == PromptComponentType.GUIDANCE
        assert "TestBot" in component.content
        assert component.priority == 6
        assert component.required is True
    
    def test_create_ai_intelligence_component(self):
        """Test AI intelligence component factory."""
        component = create_ai_intelligence_component(
            "Intelligence guidance",
            priority=7
        )
        
        assert component.type == PromptComponentType.AI_INTELLIGENCE
        assert component.content == "Intelligence guidance"
        assert component.priority == 7
        assert component.required is False


class TestIntegrationScenarios:
    """Integration tests for complete scenarios."""
    
    def test_full_assembly_pipeline(self):
        """Test complete assembly pipeline."""
        assembler = create_prompt_assembler(max_tokens=1000)
        
        # Add all component types
        assembler.add_component(create_core_system_component(
            "You are a helpful assistant", priority=1
        ))
        assembler.add_component(create_memory_component(
            "USER FACTS: Name is Mark; PAST SUMMARIES: Discussed marine biology",
            priority=4
        ))
        assembler.add_component(create_guidance_component(
            "Assistant", priority=6
        ))
        
        result = assembler.assemble(model_type="generic")
        metrics = assembler.get_assembly_metrics()
        
        # Verify result structure
        assert "You are a helpful assistant" in result
        assert "USER FACTS" in result
        assert "Assistant" in result
        
        # Verify ordering (core system first, then memory, then guidance)
        assert result.index("You are a helpful assistant") < result.index("USER FACTS")
        assert result.index("USER FACTS") < result.index("Assistant")
        
        # Verify metrics
        assert metrics['total_components'] == 3
        assert metrics['within_budget'] is True
    
    def test_no_memory_scenario(self):
        """Test assembly when no memory is available."""
        assembler = create_prompt_assembler()
        
        # Add core components without memory
        assembler.add_component(create_core_system_component(
            "You are a helpful assistant", priority=1
        ))
        assembler.add_component(create_anti_hallucination_component(priority=4))
        assembler.add_component(create_guidance_component("Assistant", priority=6))
        
        result = assembler.assemble()
        
        # Should have anti-hallucination warning instead of memory
        assert "MEMORY STATUS" in result
        assert "No previous conversation history" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
