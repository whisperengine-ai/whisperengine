#!/usr/bin/env python3
"""
Export CDL Database to Template Files

This script exports character data from PostgreSQL CDL database to template files.
It generates .txt files in characters/system_prompts/ that can be used with the
template-based system prompt loader.

Usage:
    # Export specific character
    python scripts/export_cdl_to_templates.py --character elena
    
    # Export all characters
    python scripts/export_cdl_to_templates.py --all
    
    # Custom output directory
    python scripts/export_cdl_to_templates.py --character elena --output-dir /path/to/templates

Author: WhisperEngine
Date: November 2025
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.postgres_pool_manager import get_postgres_pool
from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generate_trait_descriptions(trait_name: str, value: float) -> list:
    """Generate detailed bullet point descriptions based on trait value."""
    
    trait_bullets = {
        "openness": {
            "low": [
                "Prefers familiar routines and established methods",
                "Practical and grounded in approach",
                "Values proven solutions over experimentation",
                "Comfortable with traditional perspectives"
            ],
            "medium": [
                "Balances tradition with new ideas",
                "Open to different perspectives when relevant",
                "Curious about new concepts in areas of interest",
                "Comfortable with moderate change and innovation"
            ],
            "high": [
                "Very open to new experiences and ideas",
                "Intellectually curious and creative",
                "Loves exploring new methods and discoveries",
                "Open to different perspectives and interdisciplinary connections",
                "Enthusiastic about emerging innovations"
            ]
        },
        "conscientiousness": {
            "low": [
                "Flexible and spontaneous in approach",
                "Adapts easily to changing circumstances",
                "Comfortable with ambiguity and improvisation",
                "Prioritizes creativity over strict organization"
            ],
            "medium": [
                "Organized when needed but not rigid",
                "Balances thoroughness with flexibility",
                "Takes work seriously without being perfectionistic",
                "Plans ahead but can adapt when necessary"
            ],
            "high": [
                "Highly organized and detail-oriented",
                "Takes work seriously with strong commitment",
                "Balances thoroughness with practical efficiency",
                "Tracks important details meticulously",
                "Disciplined in methodology and follow-through"
            ]
        },
        "extraversion": {
            "low": [
                "Reflective and comfortable in solitude",
                "Thoughtful in communication",
                "Energized by quiet, focused work",
                "Prefers deeper one-on-one connections",
                "Values introspection and internal processing"
            ],
            "medium": [
                "Balanced between social and solo activities",
                "Warm in appropriate contexts",
                "Comfortable in social settings but values alone time",
                "Shows enthusiasm selectively",
                "Adapts energy to the situation"
            ],
            "high": [
                "Energetic and outgoing, especially about interests",
                "Warm and engaging in conversation",
                "Energized by interaction and sharing knowledge",
                "Comfortable in social settings",
                "Shows genuine enthusiasm readily"
            ]
        },
        "agreeableness": {
            "low": [
                "Direct and frank in communication",
                "Prioritizes truth over harmony",
                "Comfortable with constructive conflict",
                "Values honest debate and challenge",
                "Independent in decision-making"
            ],
            "medium": [
                "Balances cooperation with healthy boundaries",
                "Supportive while maintaining perspective",
                "Collaborative when it serves goals",
                "Empathetic but also realistic",
                "Diplomatic in most interactions"
            ],
            "high": [
                "Warm, compassionate, and collaborative",
                "Patient with learners at all levels",
                "Supportive of others' ideas and questions",
                "Gently helpful without being overbearing",
                "Highly cooperative in interactions"
            ]
        },
        "neuroticism": {
            "low": [
                "Emotionally stable and resilient",
                "Calm under pressure",
                "Optimistic outlook even during challenges",
                "Quick to recover from setbacks",
                "Rarely experiences prolonged anxiety"
            ],
            "medium": [
                "Generally stable with occasional stress",
                "Experiences normal pressure in demanding situations",
                "Some worries about important concerns",
                "Maintains overall optimism",
                "Emotionally balanced in most situations"
            ],
            "high": [
                "Deeply sensitive to stressors",
                "Experiences anxiety about important matters",
                "Worries about potential problems",
                "Feels stress from high-stakes situations",
                "Works to maintain emotional regulation"
            ]
        }
    }
    
    # Determine intensity level based on value
    if value < 0.40:
        level = "low"
    elif value < 0.70:
        level = "medium"
    else:
        level = "high"
    
    return trait_bullets.get(trait_name, {}).get(level, [])


def format_big_five_section(personality: Dict[str, Any]) -> str:
    """Format Big Five personality traits section."""
    big_five = personality.get("big_five", {})
    if not big_five:
        return "PERSONALITY PROFILE: Not configured"
    
    lines = []
    lines.append("═══════════════════════════════════════════════════════════════════════════")
    lines.append("PERSONALITY PROFILE (Big Five Traits)")
    lines.append("═══════════════════════════════════════════════════════════════════════════")
    lines.append("")
    
    trait_descriptions = {
        "openness": "Creativity, curiosity, intellectual exploration",
        "conscientiousness": "Organization, responsibility, goal-directedness",
        "extraversion": "Social energy, enthusiasm, assertiveness",
        "agreeableness": "Compassion, cooperation, trust",
        "neuroticism": "Emotional sensitivity, stress response, anxiety"
    }
    
    for trait_name, description in trait_descriptions.items():
        trait_data = big_five.get(trait_name, {})
        
        # Handle different data formats
        if isinstance(trait_data, dict):
            value = trait_data.get("value", 0.5)
            intensity = trait_data.get("intensity", "moderate")
            trait_desc = trait_data.get("description", description)
        elif isinstance(trait_data, str):
            # Parse string format like "Openness: Very High (0.95) - medium intensity"
            import re
            value_match = re.search(r'\((\d+\.\d+)\)', trait_data)
            intensity_match = re.search(r'- (\w+) intensity', trait_data)
            value = float(value_match.group(1)) if value_match else 0.5
            intensity = intensity_match.group(1) if intensity_match else "moderate"
        else:
            value = float(trait_data) if trait_data else 0.5
            intensity = "moderate"
        
        # Determine intensity label based on value
        if value < 0.30:
            intensity_label = "Very Low"
        elif value < 0.40:
            intensity_label = "Low"
        elif value < 0.60:
            intensity_label = "Medium"
        elif value < 0.80:
            intensity_label = "High"
        else:
            intensity_label = "Very High"
        
        lines.append(f"{trait_name.upper()}: {value} ({intensity_label})")
        
        # Add detailed bullet descriptions
        bullets = generate_trait_descriptions(trait_name, value)
        for bullet in bullets:
            lines.append(f"- {bullet}")
        
        lines.append("")
    
    return "\n".join(lines)


def format_communication_style_section(comm_style: Dict[str, Any]) -> str:
    """Format communication style section."""
    lines = []
    lines.append("═══════════════════════════════════════════════════════════════════════════")
    lines.append("COMMUNICATION STYLE")
    lines.append("═══════════════════════════════════════════════════════════════════════════")
    lines.append("")
    
    engagement = comm_style.get("engagement_level", 0.5)
    lines.append(f"ENGAGEMENT LEVEL: {engagement} (How warm and actively engaged)")
    lines.append("")
    
    formality = comm_style.get("formality", {})
    if isinstance(formality, dict):
        formality_value = formality.get("value", "Balanced")
    else:
        formality_value = str(formality)
    lines.append(f"FORMALITY: {formality_value}")
    lines.append("")
    
    emotional = comm_style.get("emotional_expression", 0.5)
    lines.append(f"EMOTIONAL EXPRESSION: {emotional} (How expressive emotionally)")
    lines.append("")
    
    return "\n".join(lines)


def format_values_section(values: Dict[str, Any]) -> str:
    """Format values and beliefs section."""
    lines = []
    lines.append("═══════════════════════════════════════════════════════════════════════════")
    lines.append("CORE VALUES & BELIEFS")
    lines.append("═══════════════════════════════════════════════════════════════════════════")
    lines.append("")
    
    # Extract different value types
    fears = []
    dreams = []
    quirks = []
    values_list = []
    
    for key, value_data in values.items():
        if not isinstance(value_data, dict):
            continue
            
        description = value_data.get("description", "")
        importance = value_data.get("importance", "medium")
        
        if "fear" in key.lower():
            fears.append(f"- {description} [{importance}]")
        elif "dream" in key.lower():
            dreams.append(f"- {description} [{importance}]")
        elif "quirk" in key.lower():
            quirks.append(f"- {description} [{importance}]")
        elif "value" in key.lower():
            values_list.append(f"- {description} [{importance}]")
    
    if values_list:
        lines.append("PRIMARY VALUES:")
        lines.extend(values_list)
        lines.append("")
    
    if fears:
        lines.append("CORE FEARS:")
        lines.extend(fears)
        lines.append("")
    
    if dreams:
        lines.append("DREAMS & ASPIRATIONS:")
        lines.extend(dreams)
        lines.append("")
    
    if quirks:
        lines.append("QUIRKS & HABITS:")
        lines.extend(quirks)
        lines.append("")
    
    return "\n".join(lines)


async def export_character_to_template(
    character_name: str,
    output_dir: Path,
    enhanced_manager
) -> Optional[Path]:
    """
    Export single character from database to template file.
    
    Args:
        character_name: Character name (e.g., "elena")
        output_dir: Output directory for template files
        enhanced_manager: EnhancedCDLManager instance
        
    Returns:
        Path to generated template file or None if failed
    """
    try:
        logger.info(f"📥 Fetching character data for '{character_name}'...")
        character_data = await enhanced_manager.get_character_by_name(character_name)
        
        if not character_data:
            logger.error(f"❌ Character '{character_name}' not found in database")
            return None
        
        logger.info(f"✅ Retrieved character data for '{character_name}'")
        
        # Extract sections
        identity = character_data.get("identity", {})
        personality = character_data.get("personality", {})
        communication = character_data.get("communication_style", {})
        values = character_data.get("values_and_beliefs", {})
        
        # Build template content
        lines = []
        lines.append(f"# SYSTEM PROMPT: {identity.get('name', character_name.title())}")
        lines.append(f"# Character Type: {identity.get('archetype', 'Unknown')}")
        lines.append(f"# Last Updated: {datetime.now().strftime('%B %Y')}")
        lines.append("")
        
        # Character Identity
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("CHARACTER IDENTITY")
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("")
        lines.append(f"You are {identity.get('name', character_name.title())}, a {identity.get('occupation', 'Character')}.")
        lines.append("")
        if identity.get("description"):
            lines.append(f"DESCRIPTION: {identity['description']}")
            lines.append("")
        lines.append(f"ARCHETYPE: {identity.get('archetype', 'Unknown')}")
        lines.append("")
        
        # Personality
        lines.append(format_big_five_section(personality))
        
        # Communication Style
        lines.append(format_communication_style_section(communication))
        
        # Values & Beliefs
        lines.append(format_values_section(values))
        
        # Dynamic placeholders
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("TEMPORAL AWARENESS")
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("")
        lines.append("Current Date & Time: {{ current_datetime }}")
        lines.append("")
        
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("USER CONTEXT (DYNAMIC)")
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("")
        lines.append("{{ user_facts }}")
        lines.append("")
        
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("RELATIONSHIP CONTEXT (ADAPTIVE)")
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("")
        lines.append("{{ relationship_context }}")
        lines.append("")
        
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("RECENT CONVERSATION HISTORY")
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("")
        lines.append("{{ recent_memories }}")
        lines.append("")
        
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("EMOTIONAL INTELLIGENCE")
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("")
        lines.append("{{ emotional_state }}")
        lines.append("")
        
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        lines.append("END OF SYSTEM PROMPT")
        lines.append("═══════════════════════════════════════════════════════════════════════════")
        
        # Write to file
        output_file = output_dir / f"{character_name}.txt"
        output_file.write_text("\n".join(lines), encoding="utf-8")
        
        logger.info(f"✅ Exported template to: {output_file}")
        logger.info(f"   Template size: {len(''.join(lines))} characters")
        
        return output_file
        
    except Exception as e:
        logger.error(f"❌ Failed to export '{character_name}': {e}")
        return None


async def export_all_characters(output_dir: Path):
    """Export all characters from database."""
    try:
        pool = await get_postgres_pool()
        if not pool:
            logger.error("❌ Failed to connect to PostgreSQL")
            return
        
        enhanced_manager = create_enhanced_cdl_manager(pool)
        
        # Get all character names from database
        async with pool.acquire() as conn:
            result = await conn.fetch("SELECT DISTINCT name FROM character_identity ORDER BY name")
            character_names = [row['name'].lower() for row in result]
        
        logger.info(f"📋 Found {len(character_names)} characters in database")
        
        exported_count = 0
        for character_name in character_names:
            output_file = await export_character_to_template(character_name, output_dir, enhanced_manager)
            if output_file:
                exported_count += 1
        
        logger.info(f"✅ Successfully exported {exported_count}/{len(character_names)} characters")
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description="Export CDL database characters to template files"
    )
    parser.add_argument(
        "--character",
        type=str,
        help="Character name to export (e.g., 'elena', 'marcus')"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Export all characters"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("characters/system_prompts"),
        help="Output directory for template files (default: characters/system_prompts)"
    )
    
    args = parser.parse_args()
    
    if not args.character and not args.all:
        parser.error("Must specify either --character or --all")
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Output directory: {args.output_dir}")
    
    if args.all:
        await export_all_characters(args.output_dir)
    else:
        pool = await get_postgres_pool()
        if not pool:
            logger.error("❌ Failed to connect to PostgreSQL")
            return
        
        enhanced_manager = create_enhanced_cdl_manager(pool)
        output_file = await export_character_to_template(
            args.character,
            args.output_dir,
            enhanced_manager
        )
        
        if output_file:
            logger.info(f"✅ Export complete!")
            logger.info(f"   To use this template, set in .env:")
            logger.info(f"   CHARACTER_SYSTEM_PROMPT_PATH=characters/system_prompts/{args.character}.txt")


if __name__ == "__main__":
    asyncio.run(main())
