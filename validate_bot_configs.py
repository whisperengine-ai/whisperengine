#!/usr/bin/env python3
"""
Bot Name Configuration Validator

Cross-checks DISCORD_BOT_NAME values in .env.* files against:
1. What the normalize_bot_name() function would produce
2. What actually exists in the vector store

Identifies mismatches and provides update recommendations.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.memory.vector_memory_system import normalize_bot_name

def analyze_bot_configurations():
    """Analyze all bot configurations for naming consistency"""
    
    print("🔍 BOT NAME CONFIGURATION ANALYSIS")
    print("=" * 60)
    
    # Vector store data from our previous analysis
    vector_store_bots = {
        'elena': 1903,
        'sophia': 1824, 
        'marcus': 1407,
        'gabriel': 899,
        'dream': 344,
        'jake': 234,
        'unknown': 196,
        'ryan_chen': 136,
        'marcus_chen': 121
    }
    
    # Bot configuration files to check
    env_files = [
        '.env.dream',
        '.env.elena', 
        '.env.gabriel',
        '.env.jake',
        '.env.marcus',
        '.env.ryan-chen',
        '.env.sophia'
    ]
    
    mismatches = []
    matches = []
    
    print("\n📋 CONFIGURATION vs VECTOR STORE ANALYSIS:")
    print("-" * 60)
    
    for env_file in env_files:
        if not os.path.exists(env_file):
            print(f"❌ {env_file}: File not found")
            continue
            
        # Extract DISCORD_BOT_NAME from file
        bot_name_raw = None
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DISCORD_BOT_NAME='):
                        bot_name_raw = line.split('=', 1)[1].strip()
                        break
        except Exception as e:
            print(f"❌ {env_file}: Error reading file - {e}")
            continue
            
        if not bot_name_raw:
            print(f"❌ {env_file}: DISCORD_BOT_NAME not found")
            continue
            
        # Normalize the bot name
        bot_name_normalized = normalize_bot_name(bot_name_raw)
        
        # Check if normalized name exists in vector store
        vector_count = vector_store_bots.get(bot_name_normalized, 0)
        
        # Determine status
        if vector_count > 0:
            status = "✅ MATCH"
            matches.append({
                'file': env_file,
                'raw': bot_name_raw,
                'normalized': bot_name_normalized,
                'count': vector_count
            })
        else:
            # Check if there's a similar name in vector store
            status = "❌ MISMATCH"
            similar_names = []
            for vs_name in vector_store_bots.keys():
                if vs_name.startswith(bot_name_normalized[:3]) or bot_name_normalized.startswith(vs_name[:3]):
                    similar_names.append((vs_name, vector_store_bots[vs_name]))
            
            mismatches.append({
                'file': env_file,
                'raw': bot_name_raw,
                'normalized': bot_name_normalized,
                'similar': similar_names
            })
        
        print(f"{status} {env_file}:")
        print(f"    Raw: '{bot_name_raw}' → Normalized: '{bot_name_normalized}'")
        print(f"    Vector Store: {vector_count} records")
        
        if status == "❌ MISMATCH" and similar_names:
            print(f"    Similar in vector store: {similar_names}")
        print()
    
    # Summary and recommendations
    print("\n" + "=" * 60)
    print("🎯 SUMMARY & RECOMMENDATIONS")
    print("=" * 60)
    
    if matches:
        print(f"\n✅ CORRECTLY CONFIGURED ({len(matches)} bots):")
        for match in matches:
            print(f"  {match['file']}: '{match['raw']}' → '{match['normalized']}' ({match['count']} records)")
    
    if mismatches:
        print(f"\n❌ CONFIGURATION ISSUES ({len(mismatches)} bots):")
        for mismatch in mismatches:
            print(f"\n  {mismatch['file']}:")
            print(f"    Current: '{mismatch['raw']}' → '{mismatch['normalized']}'")
            print(f"    Vector Store: 0 records")
            
            if mismatch['similar']:
                print(f"    🔧 RECOMMENDED FIX:")
                # Find best match
                best_match = max(mismatch['similar'], key=lambda x: x[1])
                suggested_raw = best_match[0].replace('_', ' ').title()
                print(f"    Change DISCORD_BOT_NAME='{mismatch['raw']}' to DISCORD_BOT_NAME='{suggested_raw}'")
                print(f"    This will normalize to '{best_match[0]}' ({best_match[1]} existing records)")
            else:
                print(f"    ⚠️  No similar names found in vector store")
                print(f"    This bot may not have any conversation history yet")
    
    print(f"\n📊 TOTAL: {len(matches)} correct, {len(mismatches)} need updates")
    
    return mismatches

if __name__ == "__main__":
    mismatches = analyze_bot_configurations()
    
    if mismatches:
        print("\n💡 Run with specific fixes to update configurations automatically")
        sys.exit(1)  # Exit with error code if there are mismatches
    else:
        print("\n🎉 All bot configurations are correctly aligned with vector store!")
        sys.exit(0)