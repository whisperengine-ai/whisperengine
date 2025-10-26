#!/bin/bash
# Install ML experiment dependencies
# Run this once to set up your environment for ML experiments

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Installing ML Experiment Dependencies${NC}"

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install main requirements first (if not already installed)
if ! python -c "import pandas" &> /dev/null; then
    echo -e "${BLUE}📦 Installing main requirements...${NC}"
    pip install -r requirements.txt
fi

# Install ML-specific requirements
echo -e "${BLUE}📦 Installing ML experiment libraries...${NC}"
pip install -r requirements-ml.txt

echo ""
echo -e "${GREEN}✅ ML experiment environment ready!${NC}"
echo ""
echo "Installed:"
echo "  • XGBoost (gradient boosting with GPU support)"
echo "  • LightGBM (fast gradient boosting)"
echo "  • JupyterLab (interactive notebooks)"
echo "  • Seaborn, Plotly (advanced visualization)"
echo "  • statsmodels, scikit-optimize (advanced ML)"
echo ""
echo "Next steps:"
echo "  1. Start JupyterLab: ./experiments/start_jupyter_native.sh"
echo "  2. Or run experiment: source .venv/bin/activate && python experiments/notebooks/01_response_strategy_optimization.py"
