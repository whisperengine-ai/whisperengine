"""
Template-Based System Prompt Loader

This module provides template-based system prompt loading as an alternative to
database-driven CDL prompt generation. It uses Jinja2 templates with placeholder
injection for dynamic data (user facts, memories, temporal context).

Performance Benefits:
- Zero per-message database queries for static character data
- Templates loaded once at startup and cached
- Only dynamic data (user facts, memories) requires runtime queries

Architecture:
- Static character data (personality, voice, principles) → Template files
- Dynamic runtime data (user facts, relationships) → Placeholder injection
- PostgreSQL still used for adaptive learning, analytics, enrichment

Environment Variable:
- CHARACTER_SYSTEM_PROMPT_PATH: Path to .txt template file (e.g., "characters/system_prompts/elena.txt")
- If set and file exists: Use template system (fast)
- If unset or missing: Fallback to CDL database queries (existing behavior)

Author: WhisperEngine
Date: November 2025
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any, TYPE_CHECKING
from datetime import datetime
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from jinja2 import Template

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("Jinja2 not available - template system will be disabled")

logger = logging.getLogger(__name__)


class TemplateSystemPromptLoader:
    """
    Loads and renders system prompts from template files with dynamic data injection.
    
    This replaces the database-heavy CDL prompt generation with a lightweight
    template-based approach. Character personality definitions are static template
    files, while runtime data (user facts, memories) are injected via placeholders.
    """
    
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize template loader.
        
        Args:
            template_path: Path to template file. If None, reads from CHARACTER_SYSTEM_PROMPT_PATH env var.
        """
        self.template_path = template_path or os.getenv("CHARACTER_SYSTEM_PROMPT_PATH")
        self.template_cache: Optional[Any] = None  # Jinja2 Template object when loaded
        self.template_loaded_at: Optional[datetime] = None
        
        if not JINJA2_AVAILABLE:
            logger.warning("Jinja2 not installed - template system disabled. Install with: pip install jinja2")
            self.template_path = None
    
    def is_template_available(self) -> bool:
        """Check if template file exists and is usable."""
        if not self.template_path:
            return False
        
        template_file = Path(self.template_path)
        return template_file.exists() and template_file.is_file()
    
    def load_template(self, force_reload: bool = False) -> Optional[Any]:
        """
        Load template file and cache it.
        
        Args:
            force_reload: Force reload even if cached
            
        Returns:
            Jinja2 Template object or None if unavailable
        """
        if not JINJA2_AVAILABLE:
            return None
        
        if not self.is_template_available():
            logger.warning(f"Template file not found: {self.template_path}")
            return None
        
        # Return cached template unless force reload
        if self.template_cache and not force_reload:
            logger.debug(f"Using cached template (loaded at {self.template_loaded_at})")
            return self.template_cache
        
        try:
            # Type check: self.template_path guaranteed to be str here (checked by is_template_available)
            assert self.template_path is not None
            template_file = Path(self.template_path)
            template_content = template_file.read_text(encoding="utf-8")
            
            # Create Jinja2 template with autoescape disabled (we control the content)
            if not JINJA2_AVAILABLE:
                return None
            from jinja2 import Environment  # Import here to avoid unbound variable
            env = Environment(autoescape=False)
            self.template_cache = env.from_string(template_content)
            self.template_loaded_at = datetime.now()
            
            logger.info(f"✅ Loaded system prompt template: {self.template_path} ({len(template_content)} chars)")
            return self.template_cache
            
        except Exception as e:
            logger.error(f"Failed to load template {self.template_path}: {e}")
            return None
    
    async def render_system_prompt(
        self,
        user_facts: Optional[str] = None,
        recent_memories: Optional[str] = None,
        relationship_context: Optional[str] = None,
        emotional_state: Optional[str] = None,
        current_datetime: Optional[str] = None,
        timezone: str = "America/Los_Angeles",
        **extra_context: Any
    ) -> Optional[str]:
        """
        Render system prompt template with dynamic data injection.
        
        Args:
            user_facts: Formatted user facts/preferences from PostgreSQL
            recent_memories: Formatted recent conversation memories from Qdrant
            relationship_context: Adaptive relationship state from enrichment
            emotional_state: Current emotional context from RoBERTa analysis
            current_datetime: ISO timestamp (auto-generated if None)
            timezone: Timezone for datetime rendering
            **extra_context: Additional template variables
            
        Returns:
            Rendered system prompt string or None if template unavailable
            
        Example:
            prompt = await loader.render_system_prompt(
                user_facts="Mark prefers casual conversation, lives in La Jolla",
                recent_memories="Last discussed coral reefs and ocean conservation",
                current_datetime="2025-11-01T15:30:00-07:00"
            )
        """
        template = self.load_template()
        if not template:
            return None
        
        # Auto-generate current datetime if not provided
        if not current_datetime:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
            current_datetime = now.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        
        # Build context dict with all placeholders
        context = {
            "user_facts": user_facts or "No user facts available yet.",
            "recent_memories": recent_memories or "No recent conversation history.",
            "relationship_context": relationship_context or "",
            "emotional_state": emotional_state or "",
            "current_datetime": current_datetime,
            **extra_context  # Allow additional custom placeholders
        }
        
        try:
            rendered = template.render(**context)
            logger.debug(f"✅ Rendered system prompt: {len(rendered)} chars")
            return rendered
            
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            return None
    
    def get_template_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about loaded template.
        
        Returns:
            Dict with template path, loaded timestamp, cache status
        """
        return {
            "template_path": self.template_path,
            "template_available": self.is_template_available(),
            "template_cached": self.template_cache is not None,
            "loaded_at": self.template_loaded_at.isoformat() if self.template_loaded_at else None,
            "jinja2_available": JINJA2_AVAILABLE
        }


def create_template_loader(template_path: Optional[str] = None) -> TemplateSystemPromptLoader:
    """
    Factory function to create template loader instance.
    
    Args:
        template_path: Optional path to template file (defaults to env var)
        
    Returns:
        TemplateSystemPromptLoader instance
    """
    return TemplateSystemPromptLoader(template_path=template_path)


# Module-level convenience function for quick checks
def is_template_system_enabled() -> bool:
    """
    Check if template system is enabled via environment variable.
    
    Returns:
        True if CHARACTER_SYSTEM_PROMPT_PATH is set and file exists
    """
    loader = create_template_loader()
    return loader.is_template_available()
