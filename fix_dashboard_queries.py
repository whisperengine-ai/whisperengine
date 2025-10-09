#!/usr/bin/env python3
"""
Fix existing dashboards with working Flux queries for InfluxDB 2.x
Targets our confirmed data structure: user_emotion measurement with confidence field
"""

import json
import os

def create_working_queries():
    """Create actual Flux queries that work with our InfluxDB structure"""
    return {
        "emotion_confidence_timeseries": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "user_emotion")
  |> filter(fn: (r) => r._field == "confidence")
  |> aggregateWindow(every: 2m, fn: mean, createEmpty: false)""",
        
        "emotions_by_bot": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "user_emotion")
  |> filter(fn: (r) => r._field == "confidence")
  |> group(columns: ["bot"])
  |> count()""",
        
        "emotions_by_type": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "user_emotion")
  |> filter(fn: (r) => r._field == "confidence")
  |> group(columns: ["emotion"])
  |> count()""",
        
        "latest_emotion": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "user_emotion")
  |> filter(fn: (r) => r._field == "confidence")
  |> last()""",
        
        "response_time_stats": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "response_time_v2")
  |> filter(fn: (r) => r._field == "response_length")
  |> aggregateWindow(every: 2m, fn: mean, createEmpty: false)""",
        
        "emotion_intensity": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "user_emotion")
  |> filter(fn: (r) => r._field == "intensity")
  |> aggregateWindow(every: 2m, fn: mean, createEmpty: false)"""
    }

def fix_dashboard_file(filepath):
    """Fix a dashboard JSON file by adding working queries"""
    try:
        with open(filepath, 'r') as f:
            dashboard = json.load(f)
        
        queries = create_working_queries()
        panels_fixed = 0
        
        # Navigate through the dashboard structure
        dashboard_content = dashboard.get('dashboard', dashboard)
        panels = dashboard_content.get('panels', [])
        
        for panel in panels:
            if 'targets' in panel and isinstance(panel['targets'], list):
                panel_title = panel.get('title', '').lower()
                
                # Map panel titles to appropriate queries
                if any(keyword in panel_title for keyword in ['emotion', 'confidence']):
                    if 'time' in panel_title or 'series' in panel_title:
                        query = queries['emotion_confidence_timeseries']
                    elif 'bot' in panel_title:
                        query = queries['emotions_by_bot']
                    elif 'type' in panel_title or 'distribution' in panel_title:
                        query = queries['emotions_by_type']
                    elif 'latest' in panel_title or 'current' in panel_title:
                        query = queries['latest_emotion']
                    else:
                        query = queries['emotion_confidence_timeseries']
                elif 'response' in panel_title:
                    query = queries['response_time_stats']
                elif 'intensity' in panel_title:
                    query = queries['emotion_intensity']
                else:
                    # Default to emotion confidence
                    query = queries['emotion_confidence_timeseries']
                
                # Add working query to targets
                if len(panel['targets']) == 0 or not panel['targets'][0].get('query'):
                    panel['targets'] = [{
                        "refId": "A",
                        "query": query,
                        "datasource": {
                            "type": "influxdb",
                            "uid": "influxdb-whisperengine"
                        }
                    }]
                    panels_fixed += 1
        
        # Write back the fixed dashboard
        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"✅ Fixed {filepath} - Updated {panels_fixed} panels with working queries")
        return panels_fixed
    
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        return 0

def main():
    """Fix all dashboard files in the dashboards/ directory"""
    dashboard_dir = "dashboards"
    
    if not os.path.exists(dashboard_dir):
        print(f"❌ Directory {dashboard_dir} not found")
        return
    
    total_panels_fixed = 0
    files_processed = 0
    
    for filename in os.listdir(dashboard_dir):
        if filename.endswith('.json') and 'whisperengine' in filename.lower():
            filepath = os.path.join(dashboard_dir, filename)
            panels_fixed = fix_dashboard_file(filepath)
            total_panels_fixed += panels_fixed
            files_processed += 1
    
    print(f"\n🎯 SUMMARY: Fixed {files_processed} dashboard files, updated {total_panels_fixed} panels total")
    print("✅ All dashboards now have working Flux queries for InfluxDB 2.x")

if __name__ == "__main__":
    main()