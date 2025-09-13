#!/bin/bash
# Public Release Cleanup Script
# Removes development artifacts and temporary files before public release

echo "🧹 Cleaning up repository for public release..."

# Remove development script files
echo "📜 Removing development scripts..."
rm -f fix_chromadb_dimensions.py
rm -f test_global_facts.py
rm -f test_hybrid_global_facts.py
rm -f simple_endpoint_validator.py
rm -f validate_config.py

# Remove duplicate/outdated emotion AI files (moved to src/emotion/)
echo "🧠 Removing outdated emotion AI files..."
rm -f advanced_emotional_intelligence.py
rm -f emotional_intelligence_integration.py
rm -f external_api_emotion_ai.py
rm -f transformer_emotion_ai.py

# Remove backup and temporary files
echo "🗂️ Removing backup and temporary directories..."
rm -rf backups/
rm -rf temp_images/
rm -rf __pycache__/
rm -rf custom_discord_bot.egg-info/

# Remove development documentation
echo "📋 Removing internal development docs..."
rm -f BACKUP_QUICK_START.md
rm -f REFACTORING_SUMMARY.md

# Clean up any Python cache files throughout the project
echo "🗑️ Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Clean up any .DS_Store files (macOS)
echo "🍎 Cleaning macOS artifacts..."
find . -name ".DS_Store" -delete 2>/dev/null || true

# Remove empty log files but keep the directory structure
echo "📝 Cleaning log files..."
if [ -d "logs" ]; then
    find logs/ -name "*.log" -size 0 -delete 2>/dev/null || true
fi

# Clean up any temporary data files
echo "🗄️ Cleaning temporary data..."
if [ -d "data" ]; then
    find data/ -name "*.tmp" -delete 2>/dev/null || true
    find data/ -name "*.temp" -delete 2>/dev/null || true
fi

echo "✅ Repository cleanup complete!"
echo ""
echo "📋 Summary of cleaned files:"
echo "   - Development scripts (fix_chromadb_dimensions.py, test_*.py, etc.)"
echo "   - Outdated emotion AI files (moved to src/emotion/)"
echo "   - Backup directories and temporary files"
echo "   - Python cache files and build artifacts"
echo "   - Internal development documentation"
echo ""
echo "🔍 You may want to review the following files before public release:"
echo "   - README.md (ensure it's comprehensive for new users)"
echo "   - .env.example (ensure it has clear setup instructions)"
echo "   - docs/ directory (consolidate and update documentation)"
echo "   - requirements.txt (ensure all dependencies are listed)"
echo ""
echo "⚠️  Remember to:"
echo "   1. Update version numbers in pyproject.toml"
echo "   2. Review and update LICENSE if needed"
echo "   3. Add CONTRIBUTING.md for open source contributors"
echo "   4. Test the installation process on a clean system"