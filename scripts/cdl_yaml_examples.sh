#!/bin/bash
# CDL YAML Export/Import Quick Examples
# Demonstrates common usage patterns

echo "🎭 WhisperEngine CDL YAML Export/Import Examples"
echo "================================================"
echo ""

# Activate virtual environment
source .venv/bin/activate

echo "📦 Example 1: Export single character"
echo "--------------------------------------"
echo "Command: python scripts/cdl_yaml_manager.py export elena"
echo ""

echo "📦 Example 2: Export all characters"
echo "------------------------------------"
echo "Command: python scripts/cdl_yaml_manager.py export --all"
echo "Output: backups/characters_yaml/$(date +%Y-%m-%d)/"
echo ""

echo "📥 Example 3: Import single character"
echo "--------------------------------------"
echo "Command: python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/elena_rodriguez.yaml"
echo ""

echo "📥 Example 4: Import with overwrite"
echo "------------------------------------"
echo "Command: python scripts/cdl_yaml_manager.py import elena_updated.yaml --overwrite"
echo ""

echo "📥 Example 5: Import all from directory"
echo "----------------------------------------"
echo "Command: python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/ --all"
echo ""

echo "🧪 Example 6: Test roundtrip"
echo "-----------------------------"
echo "Command: python scripts/test_cdl_yaml_roundtrip.py"
echo ""

echo "💡 Quick Reference:"
echo "  - Export: python scripts/cdl_yaml_manager.py export [character|--all]"
echo "  - Import: python scripts/cdl_yaml_manager.py import [file|dir] [--all] [--overwrite]"
echo "  - Test:   python scripts/test_cdl_yaml_roundtrip.py"
echo ""

echo "📚 Full documentation: docs/guides/CDL_YAML_EXPORT_IMPORT.md"
echo ""

# Optionally run a quick test
read -p "Run quick export test? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Testing export of elena character..."
    python scripts/cdl_yaml_manager.py export elena
    echo ""
    echo "✅ Test complete! Check backups/characters_yaml/ for output"
fi
