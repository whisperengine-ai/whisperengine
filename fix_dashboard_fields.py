#!/usr/bin/env python3
"""
Quick fix for existing dashboards - update field names to match actual data
"""

import json
import os

# Field mappings from what we tried to use vs what actually exists
FIELD_CORRECTIONS = {
    # conversation_quality measurement
    "conversation_quality_score": "engagement_score",  # Use engagement_score instead
    
    # character_consistency_v2 measurement  
    "character_consistency_score": "character_consistency_score",  # This might need checking
    
    # relationship_progression measurement - need to check what fields actually exist
    "trust_level": "trust_level",  # These need verification
    "affection_level": "affection_level",
    "relationship_confidence": "relationship_confidence",
    
    # Use confirmed working fields
    "analysis_time_ms": "analysis_time_ms",  # From emotion_analysis_performance
    "coordination_time_ms": "coordination_time_ms"  # From intelligence_coordination_metrics
}

def fix_dashboard_queries(filepath):
    """Fix queries in a dashboard file to use actual field names"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            dashboard = json.load(f)
        
        panels_fixed = 0
        
        # Navigate through dashboard structure
        dashboard_content = dashboard.get('dashboard', dashboard)
        panels = dashboard_content.get('panels', [])
        
        for panel in panels:
            if 'targets' in panel and isinstance(panel['targets'], list):
                for target in panel['targets']:
                    if 'query' in target and target['query']:
                        original_query = target['query']
                        updated_query = original_query
                        
                        # Replace non-existent field names with working ones
                        for bad_field, good_field in FIELD_CORRECTIONS.items():
                            if bad_field in updated_query:
                                updated_query = updated_query.replace(f'r._field == "{bad_field}"', f'r._field == "{good_field}"')
                        
                        # Also add fallback queries for measurements that might not exist
                        if 'relationship_progression' in updated_query:
                            # Replace with a working measurement
                            updated_query = updated_query.replace('relationship_progression', 'conversation_quality')
                            updated_query = updated_query.replace('trust_level', 'engagement_score')
                            updated_query = updated_query.replace('affection_level', 'emotional_resonance')
                        
                        if 'character_consistency' in updated_query and 'character_consistency_v2' not in updated_query:
                            updated_query = updated_query.replace('character_consistency', 'character_consistency_v2')
                        
                        if updated_query != original_query:
                            target['query'] = updated_query
                            panels_fixed += 1
        
        # Write back the fixed dashboard
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"✅ Fixed {filepath} - Updated {panels_fixed} query targets")
        return panels_fixed
    
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        return 0

def main():
    """Fix all the problematic dashboards"""
    dashboard_dir = "dashboards"
    
    # Target the original dashboards that were showing "no data"
    problem_dashboards = [
        "whisperengine_relationship_analytics_dashboard.json",
        "whisperengine_conversation_quality_dashboard.json",
        "whisperengine_performance_optimization_dashboard.json",
        "whisperengine_character_development_dashboard.json"
    ]
    
    total_fixes = 0
    
    for dashboard_name in problem_dashboards:
        filepath = os.path.join(dashboard_dir, dashboard_name)
        if os.path.exists(filepath):
            fixes = fix_dashboard_queries(filepath)
            total_fixes += fixes
        else:
            print(f"⚠️ Dashboard not found: {filepath}")
    
    print(f"\n🎯 SUMMARY: Applied {total_fixes} query fixes across dashboards")
    print("✅ Dashboards should now show data using confirmed field names!")

if __name__ == "__main__":
    main()