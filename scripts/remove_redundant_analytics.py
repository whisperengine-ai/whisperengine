#!/usr/bin/env python3
"""
Remove redundant internal analytics systems in favor of InfluxDB-only metrics.

This script:
1. Removes redundant metrics collection files
2. Lists files that import them (for manual cleanup)
3. Documents what was removed for reference
"""

import os
import glob
from pathlib import Path

def find_imports_of_file(target_file: str, search_dir: str = "src/"):
    """Find all files that import a specific file"""
    imports = []
    
    # Convert file path to import name
    import_name = target_file.replace("/", ".").replace(".py", "")
    
    for py_file in glob.glob(f"{search_dir}/**/*.py", recursive=True):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                if import_name in content or target_file in content:
                    imports.append(py_file)
        except Exception:
            pass
    
    return imports

def main():
    print("🗑️ WhisperEngine Analytics Consolidation")
    print("Removing redundant internal analytics in favor of InfluxDB-only")
    print("=" * 80)
    
    # Files to remove (redundant with InfluxDB)
    files_to_remove = [
        "src/metrics/metrics_collector.py",           # Lightweight in-process metrics
        "src/metrics/holistic_ai_metrics.py",        # Comprehensive metrics (overlaps)
        "src/monitoring/engagement_tracker.py",      # User engagement (FidelityMetricsCollector has this)
    ]
    
    # Files to keep (InfluxDB integration)
    files_to_keep = [
        "src/monitoring/fidelity_metrics_collector.py",  # PRIMARY InfluxDB integration
        "src/metrics/metrics_integration.py",            # Integration layer (may need updates)
        "src/metrics/ab_testing_framework.py",           # A/B testing (valuable)
    ]
    
    print("\n📋 Analysis Results:")
    print("\n✅ KEEPING (InfluxDB Integration):")
    for file in files_to_keep:
        if os.path.exists(file):
            print(f"   {file}")
        else:
            print(f"   {file} (NOT FOUND)")
    
    print("\n🗑️ REMOVING (Redundant with InfluxDB):")
    for file in files_to_remove:
        if os.path.exists(file):
            print(f"   {file}")
            
            # Find imports
            imports = find_imports_of_file(file)
            if imports:
                print(f"      ⚠️ IMPORTED BY:")
                for imp in imports[:5]:  # Show first 5
                    print(f"         {imp}")
                if len(imports) > 5:
                    print(f"         ... and {len(imports) - 5} more files")
        else:
            print(f"   {file} (NOT FOUND)")
    
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATION:")
    print("1. Review import warnings above")
    print("2. Update imports to use FidelityMetricsCollector instead")
    print("3. Remove unused files manually")
    print("4. Test that InfluxDB integration still works")
    
    # Check if FidelityMetricsCollector exists
    if os.path.exists("src/monitoring/fidelity_metrics_collector.py"):
        print("\n✅ FidelityMetricsCollector found - this will be your primary metrics system")
    else:
        print("\n🔴 FidelityMetricsCollector NOT FOUND - this is required!")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run this analysis first (this script)")
    print("2. Update imports manually (see warnings above)")
    print("3. Remove redundant files: rm src/metrics/metrics_collector.py ...")
    print("4. Test: ./multi-bot.sh restart elena")
    print("5. Verify InfluxDB still receiving metrics")

if __name__ == "__main__":
    main()