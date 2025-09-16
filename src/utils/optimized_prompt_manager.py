#!/usr/bin/env python3
"""
Optimized Prompt Manager for WhisperEngine

Automatically selects the most appropriate prompt template based on:
- Available system resources
- Model capabilities (Phi-3-Mini vs full models)
- Performance requirements
- User preferences

This ensures the best possible experience across all deployment scenarios.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import psutil
import logging

class OptimizedPromptManager:
    """Manages prompt selection based on system capabilities and performance needs"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.prompts_dir = self.project_root / "prompts"
        self.optimized_dir = self.prompts_dir / "optimized"
        self.quick_templates_dir = self.optimized_dir / "quick_templates"
        
        # System capability detection
        memory = psutil.virtual_memory()
        self.available_memory_gb = memory.total / (1024**3) if memory else 4.0
        self.cpu_count = psutil.cpu_count() or 2
        
        # Model detection
        self.is_bundled_executable = self._detect_bundled_executable()
        self.model_type = self._detect_model_type()
        
        self.logger = logging.getLogger(__name__)
    
    def _detect_bundled_executable(self) -> bool:
        """Detect if running as a bundled executable"""
        # PyInstaller detection
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return True
        
        # Check for bundled models directory
        bundled_models = self.project_root / "models"
        if bundled_models.exists():
            phi3_model = list(bundled_models.glob("**/Phi-3-mini*"))
            if phi3_model:
                return True
        
        return False
    
    def _detect_model_type(self) -> str:
        """Detect which model is being used"""
        # Check environment variables
        local_model = os.getenv('LOCAL_LLM_MODEL', '')
        if 'phi-3' in local_model.lower() or 'phi3' in local_model.lower():
            return 'phi3-mini'
        
        # Check if bundled executable with Phi-3
        if self.is_bundled_executable:
            return 'phi3-mini'
        
        # Check actual model files
        models_dir = self.project_root / "models"
        if models_dir.exists():
            if list(models_dir.glob("**/Phi-3-mini*")):
                return 'phi3-mini'
            elif list(models_dir.glob("**/DialoGPT*")):
                return 'dialogpt'
        
        return 'unknown'
    
    def _assess_system_performance(self) -> str:
        """Assess system performance capability"""
        if self.available_memory_gb >= 16 and self.cpu_count >= 8:
            return 'high'
        elif self.available_memory_gb >= 8 and self.cpu_count >= 4:
            return 'medium'
        else:
            return 'low'
    
    def _get_token_estimate(self, file_path: Path) -> int:
        """Estimate token count for a prompt file"""
        if not file_path.exists():
            return 0
        
        try:
            content = file_path.read_text(encoding='utf-8')
            # Rough token estimation: 1 token ≈ 4 characters
            return len(content) // 4
        except Exception:
            return 0
    
    def select_optimal_prompt(self, prompt_type: str = 'system') -> Tuple[Path, Dict[str, Any]]:
        """
        Select the optimal prompt based on system capabilities and requirements
        
        Args:
            prompt_type: 'system', 'default', or specific character type
            
        Returns:
            Tuple of (selected_prompt_path, selection_metadata)
        """
        
        system_performance = self._assess_system_performance()
        selection_metadata = {
            'model_type': self.model_type,
            'is_bundled': self.is_bundled_executable,
            'system_performance': system_performance,
            'available_memory_gb': self.available_memory_gb,
            'selection_strategy': 'auto'
        }
        
        # Priority order for prompt selection
        prompt_candidates = []
        
        if prompt_type == 'system':
            # System prompt (Dream character) selection
            if self.model_type == 'phi3-mini' or self.is_bundled_executable:
                prompt_candidates = [
                    self.optimized_dir / "system_prompt_optimized.md",
                    self.quick_templates_dir / "dream_minimal.md",
                    self.prompts_dir / "default.md"  # Updated fallback
                ]
            else:
                prompt_candidates = [
                    self.prompts_dir / "default.md",  # Updated default
                    self.optimized_dir / "system_prompt_optimized.md"
                ]
        
        elif prompt_type == 'default':
            # Default companion selection
            if self.model_type == 'phi3-mini' or self.is_bundled_executable:
                prompt_candidates = [
                    self.optimized_dir / "default_optimized.md",
                    self.quick_templates_dir / "companion_minimal.md",
                    self.prompts_dir / "default.md"  # Fallback
                ]
            else:
                prompt_candidates = [
                    self.prompts_dir / "default.md",
                    self.optimized_dir / "default_optimized.md"
                ]
        
        else:
            # Character-specific prompts
            character_file = f"{prompt_type}.md"
            prompt_candidates = [
                self.prompts_dir / character_file,
                self.optimized_dir / "default_optimized.md",  # Fallback to optimized default
                self.prompts_dir / "default.md"  # Final fallback
            ]
        
        # Select first existing candidate with appropriate token count
        max_tokens = 2000 if self.model_type == 'phi3-mini' else 4000
        
        for candidate in prompt_candidates:
            if candidate.exists():
                token_count = self._get_token_estimate(candidate)
                if token_count <= max_tokens:
                    selection_metadata.update({
                        'selected_file': str(candidate),
                        'estimated_tokens': token_count,
                        'max_tokens': max_tokens,
                        'reason': f'Optimal for {self.model_type} within {max_tokens} token limit'
                    })
                    return candidate, selection_metadata
        
        # Emergency fallback - use minimal template
        if prompt_type == 'system':
            fallback = self.quick_templates_dir / "dream_minimal.md"
        else:
            fallback = self.quick_templates_dir / "companion_minimal.md"
        
        if fallback.exists():
            selection_metadata.update({
                'selected_file': str(fallback),
                'estimated_tokens': self._get_token_estimate(fallback),
                'reason': 'Emergency fallback - minimal template'
            })
            return fallback, selection_metadata
        
        # Absolute fallback - default system prompt
        absolute_fallback = self.prompts_dir / "default.md"
        selection_metadata.update({
            'selected_file': str(absolute_fallback),
            'estimated_tokens': self._get_token_estimate(absolute_fallback),
            'reason': 'Absolute fallback - default system prompt'
        })
        return absolute_fallback, selection_metadata
    
    def load_optimized_prompt(self, prompt_type: str = 'system') -> Tuple[str, Dict[str, Any]]:
        """
        Load the optimal prompt content with metadata
        
        Returns:
            Tuple of (prompt_content, selection_metadata)
        """
        
        selected_path, metadata = self.select_optimal_prompt(prompt_type)
        
        try:
            content = selected_path.read_text(encoding='utf-8')
            metadata['load_success'] = True
            self.logger.info(f"Loaded optimized prompt: {selected_path} ({metadata['estimated_tokens']} tokens)")
            return content, metadata
        
        except Exception as e:
            self.logger.error(f"Failed to load prompt {selected_path}: {e}")
            metadata.update({
                'load_success': False,
                'error': str(e)
            })
            
            # Return minimal fallback content
            fallback_content = f"You are a helpful AI assistant. Respond naturally and helpfully."
            return fallback_content, metadata
    
    def get_prompt_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for prompt optimization"""
        
        system_perf = self._assess_system_performance()
        
        recommendations = {
            'current_model': self.model_type,
            'system_performance': system_perf,
            'memory_gb': self.available_memory_gb,
            'is_bundled': self.is_bundled_executable,
            'recommendations': []
        }
        
        if self.model_type == 'phi3-mini':
            recommendations['recommendations'].append(
                "✅ Using Phi-3-Mini optimized prompts for best performance"
            )
        
        if system_perf == 'low':
            recommendations['recommendations'].extend([
                "⚡ Recommend using quick templates for faster responses",
                "💡 Consider closing other applications to free memory"
            ])
        
        if self.is_bundled_executable:
            recommendations['recommendations'].append(
                "📦 Bundled executable detected - using optimized prompts automatically"
            )
        
        return recommendations

def get_optimized_prompt(prompt_type: str = 'system', project_root: Optional[Path] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Convenience function to get optimized prompt content
    
    Args:
        prompt_type: Type of prompt to load ('system', 'default', etc.)
        project_root: Optional project root path
        
    Returns:
        Tuple of (prompt_content, selection_metadata)
    """
    manager = OptimizedPromptManager(project_root)
    return manager.load_optimized_prompt(prompt_type)

if __name__ == "__main__":
    # Demo the optimization system
    manager = OptimizedPromptManager()
    
    print("🎯 WhisperEngine Prompt Optimization Analysis")
    print("=" * 50)
    
    # System analysis
    recommendations = manager.get_prompt_recommendations()
    print(f"Model Type: {recommendations['current_model']}")
    print(f"System Performance: {recommendations['system_performance']}")
    print(f"Available Memory: {recommendations['memory_gb']:.1f}GB")
    print(f"Bundled Executable: {recommendations['is_bundled']}")
    print()
    
    print("Recommendations:")
    for rec in recommendations['recommendations']:
        print(f"  {rec}")
    print()
    
    # Test prompt selection
    for prompt_type in ['system', 'default']:
        selected_path, metadata = manager.select_optimal_prompt(prompt_type)
        print(f"{prompt_type.capitalize()} Prompt:")
        print(f"  Selected: {selected_path.name}")
        print(f"  Tokens: {metadata['estimated_tokens']}")
        print(f"  Reason: {metadata['reason']}")
        print()