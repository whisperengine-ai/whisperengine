# 🎯 Adaptive Prompt Engineering Integration Guide

## Overview

WhisperEngine's adaptive prompt engineering system automatically adjusts prompt complexity, length, and structure based on the detected LLM model capabilities. This ensures optimal performance across small, medium, and large models while maximizing token efficiency.

## 🤖 Model Size Categories

### **Small Models (1B-3B parameters)**
- **Examples**: Phi-3-Mini, TinyLlama, Qwen 1.5B, Gemma 2B
- **Context Window**: 1K-4K tokens
- **Strategy**: Minimal prompts, essential instructions only
- **Optimization**: Aggressive compression, remove optional sections

### **Medium Models (3B-8B parameters)**  
- **Examples**: Llama 3.2 3B, Phi-3-Medium, Mistral 7B
- **Context Window**: 4K-8K tokens
- **Strategy**: Balanced approach with moderate context
- **Optimization**: Optimized templates, intelligent truncation

### **Large Models (8B+ parameters)**
- **Examples**: Llama 3.1 8B, CodeLlama 13B, GPT-4, Claude-3
- **Context Window**: 8K+ tokens
- **Strategy**: Full-featured prompts with rich context
- **Optimization**: Maximum capabilities, advanced reasoning

## 🔧 Quick Integration

### **Basic Usage**
```python
from src.utils.adaptive_prompt_engineering import get_model_optimized_prompt

# Get optimized prompt for current model
prompt_content, metadata = get_model_optimized_prompt(
    personality_type="dream",  # or "default", "companion"
    context_items=5           # number of memory items to include
)

print(f"Optimized for: {metadata['model_size']} model")
print(f"Estimated tokens: {metadata['estimated_tokens']}")
```

### **Advanced Usage**
```python
from src.utils.adaptive_prompt_engineering import AdaptivePromptManager

# Create manager instance
manager = AdaptivePromptManager()

# Detect model capabilities
capabilities = manager.detect_model_capabilities()
print(f"Model: {capabilities.size.value} ({capabilities.estimated_params})")
print(f"Context window: {capabilities.context_window:,} tokens")

# Calculate optimal token budget
budget = manager.calculate_prompt_budget(
    conversation_length=8,  # number of conversation turns
    memory_items=3         # number of memory items
)

# Get adaptive system prompt
prompt, metadata = manager.get_adaptive_system_prompt("dream", context_items=3)

# Optimize conversation history
optimized_history = manager.optimize_conversation_history(
    history=conversation_messages,
    token_budget=budget.conversation_history
)
```

## 🎛️ Configuration & Environment

The system automatically detects model capabilities from environment variables:

```bash
# Model detection sources (in priority order)
LLM_CHAT_MODEL=phi-3-mini                   # Model name for classification
LLM_MAX_TOKENS_CHAT=4096                    # Context window size
LOCAL_LLM_MODEL=Phi-3-mini-4k-instruct      # Alternative model name source

# Adaptive behavior is automatic - no additional config needed
```

## 📊 Token Budget Management

### **Automatic Budget Allocation**

The system automatically allocates tokens based on model size:

#### **Small Models (1B-3B)**
```
Total Context: 2K-4K tokens
├── System Prompt: 15% (300-600 tokens)
├── Conversation: 25% (500-1000 tokens)  
├── Memory Context: 15% (300-600 tokens)
├── User Message: 10% (200-400 tokens)
└── Response Reserve: 35% (700-1400 tokens)
```

#### **Medium Models (3B-8B)**
```
Total Context: 4K-8K tokens
├── System Prompt: 20% (800-1600 tokens)
├── Conversation: 30% (1200-2400 tokens)
├── Memory Context: 20% (800-1600 tokens)
├── User Message: 10% (400-800 tokens)
└── Response Reserve: 20% (800-1600 tokens)
```

#### **Large Models (8B+)**
```
Total Context: 8K+ tokens
├── System Prompt: 25% (2000+ tokens)
├── Conversation: 35% (2800+ tokens)
├── Memory Context: 25% (2000+ tokens)
├── User Message: 10% (800+ tokens)
└── Response Reserve: 5% (400+ tokens)
```

## 🎨 Template Selection Strategy

### **Template Hierarchy**

The system selects templates based on model capabilities:

```python
# Small models → Minimal templates
prompts/optimized/quick_templates/dream_minimal.md
prompts/optimized/quick_templates/companion_minimal.md

# Medium models → Optimized templates  
prompts/optimized/system_prompt_optimized.md
prompts/optimized/default_optimized.md

# Large models → Full templates
prompts/dream_ai_enhanced.md
prompts/default.md
```

### **Fallback Chain**
If preferred template doesn't exist:
1. Try model-size-appropriate template
2. Fall back to optimized template
3. Fall back to default template
4. Emergency minimal template

## 🚀 Optimization Strategies

### **Small Model Optimizations**
- **Aggressive compression**: Remove optional sections, verbose phrases
- **Essential instructions only**: Focus on core functionality
- **Minimal examples**: Reduce few-shot examples to bare minimum
- **Conversation truncation**: Keep only 2-6 most recent messages

### **Medium Model Optimizations** 
- **Balanced approach**: Moderate context with key optimizations
- **Selective compression**: Remove only advanced sections
- **Smart truncation**: Keep recent + sample of important older messages
- **Template optimization**: Use templates designed for medium models

### **Large Model Optimizations**
- **Full capabilities**: Rich context and advanced features enabled
- **Maximum context**: Preserve conversation history and memory
- **Enhanced prompts**: Add advanced reasoning instructions
- **Quality focus**: Prioritize output quality over speed

## 🔄 Integration with Existing Systems

### **Memory Manager Integration**
```python
from src.utils.adaptive_prompt_engineering import AdaptivePromptManager

class EnhancedMemoryManager:
    def __init__(self):
        self.prompt_manager = AdaptivePromptManager()
    
    async def get_optimized_context(self, memories, conversation_history):
        # Get token budget for current model
        budget = self.prompt_manager.calculate_prompt_budget(
            conversation_length=len(conversation_history),
            memory_items=len(memories)
        )
        
        # Optimize conversation history
        optimized_history = self.prompt_manager.optimize_conversation_history(
            history=conversation_history,
            token_budget=budget.conversation_history
        )
        
        # Truncate memories if needed
        if len(memories) * 100 > budget.memory_context:  # Rough estimate
            memories = memories[:budget.memory_context // 100]
        
        return optimized_history, memories
```

### **LLM Client Integration**
```python
from src.utils.adaptive_prompt_engineering import get_model_optimized_prompt

class EnhancedLLMClient:
    async def chat_completion(self, messages, personality="default"):
        # Get optimized system prompt
        system_prompt, metadata = get_model_optimized_prompt(
            personality_type=personality,
            context_items=len([m for m in messages if m.get('role') == 'system'])
        )
        
        # Replace or update system message
        if messages and messages[0].get('role') == 'system':
            messages[0]['content'] = system_prompt
        else:
            messages.insert(0, {'role': 'system', 'content': system_prompt})
        
        # Log optimization info
        logger.info("Using %s prompt optimization (%s tokens)", 
                   metadata['model_size'], metadata['estimated_tokens'])
        
        return await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=metadata.get('max_response_tokens', 1024)
        )
```

## 📈 Performance Monitoring

### **Getting Optimization Metrics**
```python
manager = AdaptivePromptManager()
metrics = manager.get_performance_metrics()

print("Model Info:")
print(f"  Size: {metrics['model_info']['size']}")
print(f"  Parameters: {metrics['model_info']['estimated_params']}")
print(f"  Context Window: {metrics['model_info']['context_window']:,}")

print("Current Strategy:")
print(f"  {metrics['template_strategy']}")

print("Recommendations:")
for rec in metrics['recommendations']:
    print(f"  {rec}")
```

### **Sample Output**
```
Model Info:
  Size: small
  Parameters: 2-3B
  Context Window: 4,096

Current Strategy:
  Minimal prompts, aggressive compression, essential instructions only

Recommendations:
  ✨ Using minimal templates optimized for small models
  🚀 Aggressive prompt compression active for better performance  
  💡 Consider upgrading to a larger model for richer conversations
```

## 🔧 Custom Template Creation

### **Creating Size-Specific Templates**

For custom personalities, create templates for each model size:

```
prompts/
├── my_personality.md                    # Large model template (full)
├── optimized/
│   ├── my_personality_optimized.md      # Medium model template  
│   └── quick_templates/
│       └── my_personality_minimal.md    # Small model template
```

### **Template Guidelines**

#### **Small Model Templates (< 500 tokens)**
- Essential instructions only
- No examples or advanced features
- Direct, concise language
- Single paragraph structure

#### **Medium Model Templates (500-1000 tokens)**
- Core instructions + key examples
- Moderate complexity allowed
- Clear section structure
- Balance features vs. size

#### **Large Model Templates (1000+ tokens)**
- Full feature set
- Rich examples and context
- Advanced reasoning instructions
- Detailed behavioral guidelines

## 🚀 Best Practices

### **Development Guidelines**
1. **Test across model sizes**: Verify prompts work on small, medium, and large models
2. **Monitor token usage**: Use budget calculations to stay within limits
3. **Gradual degradation**: Ensure core functionality works even with minimal prompts
4. **Performance feedback**: Monitor response quality across different optimizations

### **Template Design**
1. **Modular structure**: Design templates with optional sections that can be removed
2. **Clear priorities**: Mark essential vs. optional instructions
3. **Token awareness**: Estimate token counts during template creation
4. **Model testing**: Test templates with actual small models, not just large ones

### **Integration Strategy**
1. **Fallback planning**: Always have fallback templates available
2. **Graceful degradation**: Maintain functionality even with aggressive optimization
3. **Monitoring**: Log optimization decisions for debugging
4. **User feedback**: Allow users to see what optimizations are being applied

---

## 🎯 Quick Start Checklist

- [ ] **Import the system**: `from src.utils.adaptive_prompt_engineering import get_model_optimized_prompt`
- [ ] **Replace static prompts**: Use `get_model_optimized_prompt()` instead of hardcoded prompts
- [ ] **Add budget management**: Use `calculate_prompt_budget()` for conversation history
- [ ] **Create size-specific templates**: Add minimal versions of custom prompts
- [ ] **Monitor performance**: Check optimization metrics and adjust as needed
- [ ] **Test across models**: Verify functionality with small, medium, and large models

The adaptive prompt system is designed to be a drop-in enhancement that automatically optimizes performance across all model sizes while maintaining WhisperEngine's rich personality and functionality! 🎉