#!/usr/bin/env python3
"""
Remove duplicate dashboards from Grafana.
Keeps the dashboard with the highest ID (most recent) for each title.
"""

import requests
import json
from requests.auth import HTTPBasicAuth

# Grafana configuration
GRAFANA_URL = "http://localhost:3000"
USERNAME = "admin"
PASSWORD = "whisperengine_grafana"

def get_all_dashboards():
    """Get all dashboards from Grafana."""
    response = requests.get(
        f"{GRAFANA_URL}/api/search?type=dash-db",
        auth=HTTPBasicAuth(USERNAME, PASSWORD)
    )
    response.raise_for_status()
    return response.json()

def delete_dashboard(uid):
    """Delete a dashboard by UID."""
    response = requests.delete(
        f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
        auth=HTTPBasicAuth(USERNAME, PASSWORD)
    )
    print(f"Delete dashboard {uid}: {response.status_code} - {response.text}")
    return response.status_code == 200

def main():
    print("🔍 Getting all dashboards...")
    dashboards = get_all_dashboards()
    print(f"Found {len(dashboards)} total dashboards")
    
    # Group by title to find duplicates
    from collections import defaultdict
    title_groups = defaultdict(list)
    
    for dash in dashboards:
        title_groups[dash['title']].append(dash)
    
    print(f"\n📊 Analysis:")
    print(f"Unique titles: {len(title_groups)}")
    
    duplicates_to_remove = []
    
    for title, dashboards_with_title in title_groups.items():
        if len(dashboards_with_title) > 1:
            print(f"\n🔍 '{title}' has {len(dashboards_with_title)} copies:")
            
            # Sort by ID descending to keep the highest (most recent)
            sorted_dashboards = sorted(dashboards_with_title, key=lambda x: x['id'], reverse=True)
            keep = sorted_dashboards[0]
            remove = sorted_dashboards[1:]
            
            print(f"  ✅ KEEP: ID {keep['id']} (UID: {keep['uid']})")
            for r in remove:
                print(f"  ❌ REMOVE: ID {r['id']} (UID: {r['uid']})")
                duplicates_to_remove.append(r)
    
    print(f"\n🗑️  Total duplicates to remove: {len(duplicates_to_remove)}")
    
    if duplicates_to_remove:
        print("\n🗑️  Automatically proceeding with deletion...")
        success_count = 0
        for dash in duplicates_to_remove:
            if delete_dashboard(dash['uid']):
                success_count += 1
                print(f"  ✅ Removed: {dash['title']} (ID: {dash['id']})")
            else:
                print(f"  ❌ Failed to remove: {dash['title']} (ID: {dash['id']})")
        
        print(f"\n📊 Summary:")
        print(f"Successfully removed: {success_count}/{len(duplicates_to_remove)} duplicates")
        
        # Get final count
        final_dashboards = get_all_dashboards()
        print(f"Final dashboard count: {len(final_dashboards)}")
    else:
        print("✅ No duplicates found!")

if __name__ == "__main__":
    main()