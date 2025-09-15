# WhisperEngine Optimized Prompts for Phi-3-Mini

This directory contains prompts specifically optimized for the bundled Phi-3-Mini-4K-Instruct model used in pre-built executables.

## Key Optimizations

### Token Efficiency
- **Reduced redundancy**: Eliminated duplicate context tags
- **Streamlined language**: Preserved personality while reducing verbosity  
- **Smart consolidation**: Combined related sections to reduce overhead
- **Essential context**: Maintained core functionality with fewer tokens

### Phi-3-Mini Specific Tuning
- **4096 token limit**: Designed to fit comfortably within model context
- **Instruction following**: Optimized for Phi-3's instruction-following strength
- **Character consistency**: Maintained personality depth with efficient expression
- **Performance focus**: Reduced processing overhead for faster responses

## File Structure

- `system_prompt_optimized.md` - Optimized main Dream character prompt
- `default_optimized.md` - Optimized general companion prompt  
- `quick_templates/` - Ultra-lightweight templates for specific use cases
- `README.md` - This file

## Token Savings

| Original File | Original Tokens | Optimized Tokens | Savings |
|---------------|----------------|------------------|---------|
| system_prompt.md | ~3,851 | ~2,200 | ~43% |
| default.md | ~2,950 | ~1,800 | ~39% |

## Usage

These optimized prompts are automatically used in pre-built executables to ensure:
- Faster response generation
- Better model performance
- Longer conversation context
- Improved reliability

## Fallback Strategy

If memory or performance issues arise, the system automatically falls back to:
1. Optimized prompts (this directory)
2. Quick templates (ultra-lightweight)
3. Minimal prompts (emergency fallback)

This ensures the best possible experience across all hardware configurations.