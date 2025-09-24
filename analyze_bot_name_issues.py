#!/usr/bin/env python3
"""
Bot Name Normalization Utility

This script addresses critical bot_name case sensitivity and space issues:
1. Case sensitivity: "Elena" vs "elena" 
2. Space handling: "Marcus Chen" vs "marcus-chen"
3. Memory isolation failures due to inconsistent bot names

Provides normalization functions and migration tools.
"""

import os
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class BotNameNormalizer:
    """Handles bot name normalization for consistent memory storage and retrieval"""
    
    @staticmethod
    def normalize_bot_name(bot_name: str) -> str:
        """
        Normalize bot name for consistent storage and filtering.
        
        Rules:
        1. Convert to lowercase for case-insensitive matching
        2. Replace spaces with underscores for URL/file safety
        3. Remove special characters except underscore/hyphen
        4. Trim whitespace
        
        Examples:
        - "Elena" -> "elena"
        - "Marcus Chen" -> "marcus_chen" 
        - "Dream of the Endless" -> "dream_of_the_endless"
        """
        if not bot_name:
            return "unknown"
        
        # Step 1: Trim and lowercase
        normalized = bot_name.strip().lower()
        
        # Step 2: Replace spaces with underscores
        normalized = re.sub(r'\s+', '_', normalized)
        
        # Step 3: Remove special characters except underscore/hyphen
        normalized = re.sub(r'[^a-z0-9_-]', '', normalized)
        
        # Step 4: Collapse multiple underscores/hyphens
        normalized = re.sub(r'[_-]+', '_', normalized)
        
        # Step 5: Remove leading/trailing underscores
        normalized = normalized.strip('_-')
        
        return normalized if normalized else "unknown"
    
    @staticmethod
    def get_display_name(bot_name: str) -> str:
        """
        Get display-friendly version of bot name.
        
        Examples:
        - "elena" -> "Elena"
        - "marcus_chen" -> "Marcus Chen"
        """
        if not bot_name:
            return "Unknown"
        
        # Replace underscores with spaces and title case
        display = bot_name.replace('_', ' ').replace('-', ' ')
        return display.title()
    
    @staticmethod
    def get_container_name(bot_name: str) -> str:
        """
        Get Docker container-safe name.
        
        Examples:
        - "Elena" -> "elena-bot"
        - "Marcus Chen" -> "marcus-chen-bot"
        """
        normalized = BotNameNormalizer.normalize_bot_name(bot_name)
        return f"{normalized.replace('_', '-')}-bot"
    
    @staticmethod
    def validate_bot_name_consistency(env_files: List[str]) -> Dict[str, List[str]]:
        """
        Check for bot name inconsistencies across environment files.
        
        Returns dict of issues found.
        """
        issues = {
            "case_variations": [],
            "space_variations": [], 
            "duplicate_normalized": [],
            "invalid_names": []
        }
        
        bot_names = {}
        normalized_names = {}
        
        for env_file in env_files:
            if not os.path.exists(env_file):
                continue
                
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('DISCORD_BOT_NAME='):
                            raw_name = line.split('=', 1)[1].strip()
                            normalized = BotNameNormalizer.normalize_bot_name(raw_name)
                            
                            # Track raw names
                            if raw_name not in bot_names:
                                bot_names[raw_name] = []
                            bot_names[raw_name].append(env_file)
                            
                            # Track normalized names
                            if normalized not in normalized_names:
                                normalized_names[normalized] = []
                            normalized_names[normalized].append((raw_name, env_file))
                            
                            # Check for issues
                            if not raw_name or raw_name == "YourBotName":
                                issues["invalid_names"].append(f"{env_file}: '{raw_name}'")
                            
                            break
            except Exception as e:
                logger.warning(f"Could not read {env_file}: {e}")
        
        # Find case variations
        lower_names = {}
        for name in bot_names.keys():
            lower = name.lower()
            if lower not in lower_names:
                lower_names[lower] = []
            lower_names[lower].append(name)
        
        for lower_name, variations in lower_names.items():
            if len(variations) > 1:
                issues["case_variations"].append(f"'{lower_name}': {variations}")
        
        # Find space variations
        for name in bot_names.keys():
            if ' ' in name:
                issues["space_variations"].append(f"'{name}' (from {bot_names[name]})")
        
        # Find duplicate normalized names
        for normalized, sources in normalized_names.items():
            if len(sources) > 1:
                raw_names = [src[0] for src in sources]
                if len(set(raw_names)) > 1:  # Different raw names normalize to same
                    issues["duplicate_normalized"].append(f"'{normalized}': {raw_names}")
        
        return issues

def analyze_current_bot_names():
    """Analyze current bot name configuration for issues"""
    print("🔍 ANALYZING: Current Bot Name Configuration")
    
    # Find all .env files
    env_files = []
    for file in os.listdir('.'):
        if file.startswith('.env.') and not file.endswith('.template'):
            env_files.append(file)
    
    print(f"Found {len(env_files)} environment files: {env_files}")
    
    # Check for issues
    normalizer = BotNameNormalizer()
    issues = normalizer.validate_bot_name_consistency(env_files)
    
    print("\n=== CURRENT BOT NAMES ===")
    bot_configs = {}
    
    for env_file in env_files:
        if not os.path.exists(env_file):
            continue
            
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DISCORD_BOT_NAME='):
                        raw_name = line.split('=', 1)[1].strip()
                        normalized = normalizer.normalize_bot_name(raw_name)
                        display = normalizer.get_display_name(normalized)
                        container = normalizer.get_container_name(raw_name)
                        
                        bot_configs[env_file] = {
                            'raw': raw_name,
                            'normalized': normalized,
                            'display': display,
                            'container': container
                        }
                        
                        print(f"{env_file}:")
                        print(f"  Raw: '{raw_name}'")
                        print(f"  Normalized: '{normalized}'")
                        print(f"  Display: '{display}'")
                        print(f"  Container: '{container}'")
                        print()
                        break
        except Exception as e:
            print(f"❌ Could not read {env_file}: {e}")
    
    print("=== ISSUES FOUND ===")
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    
    if total_issues == 0:
        print("✅ No bot name issues found!")
        return bot_configs
    
    print(f"❌ Found {total_issues} issues:")
    
    if issues["case_variations"]:
        print("\n🔸 Case Variations (same name, different case):")
        for variation in issues["case_variations"]:
            print(f"  - {variation}")
    
    if issues["space_variations"]:
        print("\n🔸 Space Variations (spaces in names):")
        for variation in issues["space_variations"]:
            print(f"  - {variation}")
    
    if issues["duplicate_normalized"]:
        print("\n🔸 Duplicate Normalized Names:")
        for duplicate in issues["duplicate_normalized"]:
            print(f"  - {duplicate}")
    
    if issues["invalid_names"]:
        print("\n🔸 Invalid Names:")
        for invalid in issues["invalid_names"]:
            print(f"  - {invalid}")
    
    print("\n=== RECOMMENDATIONS ===")
    print("1. Use normalized names for consistency")
    print("2. Update .env files to use consistent casing")
    print("3. Replace spaces with underscores or hyphens")
    print("4. Consider memory migration if bot names change")
    
    return bot_configs

if __name__ == "__main__":
    analyze_current_bot_names()