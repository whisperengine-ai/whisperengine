#!/bin/bash

# Re-import 6 characters with fixed voice_traits extraction
# Fixes JSON dumps issue in vocabulary fields

echo "🔄 Re-importing 6 characters with fixed voice_traits extraction..."
echo "This will add properly extracted vocabulary records (lists → individual records)"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Re-import all 6 characters in order
echo "1/6 Re-importing Dream..."
python3 scripts/import_dream_extended.py
echo ""

echo "2/6 Re-importing Dotty..."
python3 scripts/import_dotty_extended.py
echo ""

echo "3/6 Re-importing Gabriel..."
python3 scripts/import_gabriel_extended.py
echo ""

echo "4/6 Re-importing Aetheris..."
python3 scripts/import_aetheris_extended.py
echo ""

echo "5/6 Re-importing Jake..."
python3 scripts/import_jake_extended.py
echo ""

echo "6/6 Re-importing Ryan..."
python3 scripts/import_ryan_extended.py
echo ""

echo "✅ All 6 characters re-imported with fixed voice_traits extraction!"
echo ""
echo "Next: Verify NO JSON dumps remain in voice_traits table"
