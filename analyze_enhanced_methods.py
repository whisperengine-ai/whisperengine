#!/usr/bin/env python3
"""
Simple verification script to check enhanced memory method integration.

This script analyzes the source code to verify enhanced methods are being used.
"""

import os
import re
import sys

def analyze_source_file(filepath, relative_path):
    """Analyze a source file for memory method usage."""
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patterns to look for
        legacy_patterns = [
            r'\.retrieve_relevant_memories\(',
            r'\.store_conversation\(',
        ]
        
        enhanced_patterns = [
            r'retrieve_relevant_memories_enhanced',
            r'store_conversation_with_full_context',
            r'process_with_phase4_intelligence',
            r'search_like_human_friend',
            r'get_phase4_response_context',
        ]
        
        legacy_matches = []
        enhanced_matches = []
        
        for pattern in legacy_patterns:
            matches = re.findall(pattern, content)
            if matches:
                legacy_matches.extend([(pattern, len(matches))])
        
        for pattern in enhanced_patterns:
            matches = re.findall(pattern, content)
            if matches:
                enhanced_matches.extend([(pattern, len(matches))])
        
        return {
            'file': relative_path,
            'legacy': legacy_matches,
            'enhanced': enhanced_matches,
            'content_length': len(content)
        }
        
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def main():
    """Main verification function."""
    
    print("🔍 WhisperEngine Enhanced Memory Method Source Analysis")
    print("=" * 60)
    
    # Files to analyze
    files_to_check = [
        'src/handlers/events.py',
        'src/handlers/memory.py', 
        'src/memory/integrated_memory_manager.py',
        'src/memory/thread_safe_memory.py',
        'src/utils/enhanced_memory_manager.py',
        'src/core/bot.py',
    ]
    
    total_legacy = 0
    total_enhanced = 0
    analysis_results = []
    
    for file_path in files_to_check:
        full_path = os.path.join('/Users/markcastillo/git/whisperengine', file_path)
        result = analyze_source_file(full_path, file_path)
        
        if result:
            analysis_results.append(result)
            
            legacy_count = sum(count for _, count in result['legacy'])
            enhanced_count = sum(count for _, count in result['enhanced'])
            
            total_legacy += legacy_count
            total_enhanced += enhanced_count
            
            print(f"\n📁 {file_path}")
            print(f"   Size: {result['content_length']:,} chars")
            
            if result['enhanced']:
                print("   ✅ Enhanced methods found:")
                for pattern, count in result['enhanced']:
                    print(f"      🚀 {pattern}: {count} usage(s)")
            
            if result['legacy']:
                print("   ⚠️  Legacy methods found:")
                for pattern, count in result['legacy']:
                    print(f"      📝 {pattern}: {count} usage(s)")
            
            if not result['enhanced'] and not result['legacy']:
                print("   📋 No memory method usage detected")
    
    # Special check for enhanced memory manager implementation
    print(f"\n🔧 Enhanced Memory Manager Implementation Check")
    enhanced_manager_path = '/Users/markcastillo/git/whisperengine/src/utils/enhanced_memory_manager.py'
    
    if os.path.exists(enhanced_manager_path):
        with open(enhanced_manager_path, 'r') as f:
            content = f.read()
        
        # Check if it overrides basic methods
        override_patterns = [
            r'def retrieve_relevant_memories\(',
            r'def retrieve_context_aware_memories\(',
        ]
        
        overrides_found = []
        for pattern in override_patterns:
            if re.search(pattern, content):
                overrides_found.append(pattern.replace('def ', '').replace('(', ''))
        
        if overrides_found:
            print("   ✅ Enhanced manager overrides basic methods:")
            for override in overrides_found:
                print(f"      🔄 {override}")
        else:
            print("   ⚠️  Enhanced manager doesn't override basic methods")
    
    # Check memory integration patch
    print(f"\n🔗 Memory Integration Patch Check")
    patch_path = '/Users/markcastillo/git/whisperengine/src/utils/memory_integration_patch.py'
    
    if os.path.exists(patch_path):
        print("   ✅ Memory integration patch exists")
        
        # Check if it's being used in bot.py
        bot_path = '/Users/markcastillo/git/whisperengine/src/core/bot.py'
        if os.path.exists(bot_path):
            with open(bot_path, 'r') as f:
                bot_content = f.read()
            
            if 'apply_memory_enhancement_patch' in bot_content:
                print("   ✅ Bot.py applies memory enhancement patch")
            else:
                print("   ⚠️  Bot.py doesn't apply memory enhancement patch")
    else:
        print("   ❌ Memory integration patch not found")
    
    # Summary
    print(f"\n📊 Summary")
    print("=" * 30)
    print(f"Total legacy method usages: {total_legacy}")
    print(f"Total enhanced method usages: {total_enhanced}")
    
    if total_enhanced > 0:
        ratio = total_enhanced / (total_legacy + total_enhanced)
        print(f"Enhanced method adoption rate: {ratio:.1%}")
        
        if ratio > 0.7:
            print("🎉 EXCELLENT: High adoption of enhanced methods")
        elif ratio > 0.4:
            print("👍 GOOD: Moderate adoption of enhanced methods")
        else:
            print("⚠️  IMPROVEMENT NEEDED: Low adoption of enhanced methods")
    else:
        print("❌ NO enhanced methods detected in source code")
    
    # Key findings
    print(f"\n🎯 Key Findings:")
    
    if total_enhanced > 0:
        print("✅ Enhanced memory methods are being used")
    else:
        print("❌ Enhanced memory methods not detected")
    
    # Check specific files for enhanced usage
    events_analysis = next((r for r in analysis_results if 'events.py' in r['file']), None)
    if events_analysis and events_analysis['enhanced']:
        print("✅ Events handler uses enhanced methods")
    else:
        print("⚠️  Events handler may not use enhanced methods")
    
    # Check if basic methods are overridden
    enhanced_manager_analysis = next((r for r in analysis_results if 'enhanced_memory_manager.py' in r['file']), None)
    if enhanced_manager_analysis:
        has_overrides = any('retrieve_relevant_memories' in pattern for pattern, _ in enhanced_manager_analysis['enhanced'])
        if has_overrides:
            print("✅ Basic methods are overridden with enhanced versions")
        else:
            print("📋 Enhanced manager provides additional methods")
    
    return 0 if total_enhanced > 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)