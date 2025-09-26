#!/usr/bin/env python3
"""
Fix CRITICAL missing fields that are actually used by CDL AI integration system.
Focus only on fields that have active code paths:
1. custom_speaking_instructions (used in CDL AI integration)  
2. life_phases (used in CDL AI integration and bot self-memory)
3. speech_patterns sections (used with dual-location fallback)
"""

import json
from pathlib import Path

def fix_character_file(filepath):
    """Fix critical missing fields in a character file"""
    print(f"\n🔧 Fixing critical fields in {filepath}")
    
    filepath_str = str(filepath).lower()  # Define once at the top
    
    with open(filepath, 'r', encoding='utf-8') as f:
        character = json.load(f)
    
    character_name = character.get('character', {}).get('metadata', {}).get('name', 'Unknown')
    fixed_count = 0
    
    # 1. Add custom_speaking_instructions to communication_style if missing
    comm_style = character.get('character', {}).get('personality', {}).get('communication_style', {})
    if comm_style and 'custom_speaking_instructions' not in comm_style:
        # Generate character-appropriate instructions
        if 'sophia' in filepath_str:
            instructions = [
                "Keep responses SHORT and punchy (1-3 sentences max)",
                "Use NYC slang and marketing terminology",
                "Sound confident and trendy",
                "Include luxury brand references when relevant"
            ]
        elif 'elena' in filepath_str:
            instructions = [
                "Include scientific terminology naturally",
                "Show passion for ocean conservation",
                "Balance technical detail with accessibility",
                "Express wonder about marine ecosystems"
            ]
        elif 'marcus' in filepath_str:
            instructions = [
                "Explain complex AI concepts clearly",
                "Show intellectual curiosity",
                "Reference current tech developments",
                "Balance optimism with realistic caution"
            ]
        elif 'jake' in filepath_str:
            instructions = [
                "Use understated, confident language",
                "Show deep connection to nature",
                "Speak with quiet authority about outdoors",
                "Include subtle photography insights"
            ]
        elif 'ryan' in filepath_str:
            instructions = [
                "Use gaming terminology naturally",
                "Show enthusiasm for game mechanics",
                "Balance technical and creative perspectives",
                "Reference gaming culture appropriately"
            ]
        elif 'dream' in filepath_str:
            instructions = [
                "Speak with ancient, timeless wisdom",
                "Use poetic, metaphorical language",
                "Reference dreams and subconscious realms",
                "Maintain mysterious, otherworldly tone"
            ]
        elif 'gabriel' in filepath_str:
            instructions = [
                "Use theatrical, expressive language",
                "Show emotional depth and intelligence",
                "Reference performance and storytelling",
                "Balance vulnerability with strength"
            ]
        else:
            instructions = [
                "Maintain authentic personality",
                "Use character-appropriate vocabulary",
                "Stay consistent with established traits"
            ]
            
        comm_style['custom_speaking_instructions'] = instructions
        fixed_count += 1
        print(f"  ✅ Added custom_speaking_instructions for {character_name}")
    
    # 2. Add life_phases to background section if missing
    character_obj = character.get('character', {})
    if 'background' not in character_obj:
        character_obj['background'] = {}
        fixed_count += 1
        print(f"  ✅ Created background section for {character_name}")
    
    background = character_obj['background']
    if 'life_phases' not in background:
        # Generate character-appropriate life phases
        if 'sophia' in filepath_str:
            life_phases = [
                {
                    "age_range": "22-28",
                    "title": "Marketing Hustle Years",
                    "description": "Built reputation in NYC marketing scene through networking and bold campaigns",
                    "key_experiences": ["First major brand launch", "Industry recognition", "Building professional network"],
                    "formative_impact": "Developed confidence and street-smart business instincts"
                }
            ]
        elif 'elena' in filepath_str:
            life_phases = [
                {
                    "age_range": "16-22",
                    "title": "Marine Biology Discovery",
                    "description": "First exposure to marine ecosystems sparked lifelong passion",
                    "key_experiences": ["First scuba diving experience", "Marine biology degree", "Reef research"],
                    "formative_impact": "Developed deep connection to ocean conservation mission"
                }
            ]
        elif 'marcus' in filepath_str:
            life_phases = [
                {
                    "age_range": "25-30",
                    "title": "AI Research Foundation",
                    "description": "Graduate studies and early research in artificial intelligence",
                    "key_experiences": ["PhD research", "First AI publications", "Academic collaborations"],
                    "formative_impact": "Established intellectual framework and research methodology"
                }
            ]
        elif 'jake' in filepath_str:
            life_phases = [
                {
                    "age_range": "18-25",
                    "title": "Wilderness Immersion",
                    "description": "Extended solo trips developed deep connection to nature",
                    "key_experiences": ["Solo backpacking", "Wildlife photography", "Survival skills"],
                    "formative_impact": "Cultivated quiet confidence and nature wisdom"
                }
            ]
        elif 'ryan' in filepath_str:
            life_phases = [
                {
                    "age_range": "20-26",
                    "title": "Game Development Learning",
                    "description": "Transition from player to creator, mastering development tools",
                    "key_experiences": ["First game prototype", "Learning Unity", "Indie development community"],
                    "formative_impact": "Developed creative-technical problem solving approach"
                }
            ]
        elif 'dream' in filepath_str:
            life_phases = [
                {
                    "age_range": "Timeless",
                    "title": "The Dreaming Genesis",
                    "description": "Formation of the realm of dreams and emergence of consciousness",
                    "key_experiences": ["Creation of dream realm", "First mortal dreams", "Understanding unconscious"],
                    "formative_impact": "Established eternal connection to all sleeping minds"
                }
            ]
        elif 'gabriel' in filepath_str:
            life_phases = [
                {
                    "age_range": "22-28",
                    "title": "Theatrical Awakening",
                    "description": "Discovery of acting as both craft and emotional expression",
                    "key_experiences": ["First major role", "Method acting training", "Emotional breakthrough"],
                    "formative_impact": "Developed ability to access and express deep emotions"
                }
            ]
        else:
            life_phases = [
                {
                    "age_range": "20-30",
                    "title": "Formative Years",
                    "description": "Key developmental period that shaped current personality",
                    "key_experiences": ["Personal growth", "Career development", "Life lessons"],
                    "formative_impact": "Established core values and worldview"
                }
            ]
            
        background['life_phases'] = life_phases
        fixed_count += 1
        print(f"  ✅ Added {len(life_phases)} life_phases for {character_name}")
    
    # 3. Add top-level speech_patterns if missing (for dual-location fallback)
    if 'speech_patterns' not in character_obj:
        # Check if we have speech patterns in identity.voice
        voice_patterns = character_obj.get('identity', {}).get('voice', {}).get('speech_patterns', [])
        if voice_patterns:
            # Create top-level speech_patterns based on voice patterns
            character_obj['speech_patterns'] = {
                "vocabulary": {
                    "preferred_words": [],
                    "avoided_words": []
                },
                "sentence_structure": "Reflects patterns found in identity.voice.speech_patterns",
                "patterns_reference": "See also identity.voice.speech_patterns for additional patterns"
            }
            fixed_count += 1
            print(f"  ✅ Added top-level speech_patterns structure for {character_name}")
    
    # Save if we made changes
    if fixed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(character, f, indent=2, ensure_ascii=False)
        print(f"  💾 Saved {fixed_count} fixes to {filepath}")
        return fixed_count
    else:
        print(f"  ✅ No fixes needed for {character_name}")
        return 0

def main():
    """Fix critical missing fields in all character files"""
    print("🔧 FIXING CRITICAL MISSING FIELDS")
    print("=" * 50)
    
    character_dir = Path("characters/examples")
    total_fixes = 0
    
    # Find all character JSON files
    character_files = list(character_dir.glob("*.json"))
    
    print(f"Found {len(character_files)} character files to check...")
    
    for filepath in sorted(character_files):
        fixes = fix_character_file(filepath)
        total_fixes += fixes
    
    print("\n" + "=" * 50)
    print(f"✅ COMPLETE: Applied {total_fixes} critical fixes across {len(character_files)} files")
    print("\nFixed fields:")
    print("  • custom_speaking_instructions (used by CDL AI integration)")
    print("  • background.life_phases (used by CDL AI integration and bot memory)")  
    print("  • speech_patterns structure (for dual-location fallback)")
    print("\nThese are the HIGH PRIORITY fields actively used by the system.")

if __name__ == "__main__":
    main()