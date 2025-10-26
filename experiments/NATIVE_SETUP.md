# ML Experiments Setup - Native Python

## ✅ What Was Removed
- ❌ `docker-compose.ml-experiments.yml` - Docker orchestration
- ❌ `docker/Dockerfile.ml-experiments` - Container image definition
- ❌ `requirements-ml-experiments.txt` - Separate requirements file

## ✅ What Was Added
- ✅ `requirements-ml.txt` - ML-specific dependencies (extends main requirements)
- ✅ `experiments/install_ml_deps.sh` - One-time ML dependencies installer
- ✅ `experiments/start_jupyter_native.sh` - JupyterLab startup script

## 🚀 Quick Start

### First Time Setup
```bash
# Install ML dependencies (run once)
./experiments/install_ml_deps.sh
```

### Daily Usage
```bash
# Start JupyterLab
./experiments/start_jupyter_native.sh

# Access at http://localhost:8888
```

### Run Experiments as Scripts
```bash
source .venv/bin/activate
export INFLUXDB_HOST="localhost" INFLUXDB_PORT="8087"
export POSTGRES_HOST="localhost" POSTGRES_PORT="5433"
export QDRANT_HOST="localhost" QDRANT_PORT="6334"

python experiments/notebooks/01_response_strategy_optimization.py --algorithm xgboost
```

## 📦 ML Dependencies

**Added via `requirements-ml.txt`:**
- `xgboost` - Gradient boosting (GPU-aware: CUDA/MPS/CPU)
- `lightgbm` - Fast gradient boosting for large datasets
- `jupyterlab` - Interactive notebook environment
- `seaborn` - Statistical visualization
- `plotly` - Interactive plots
- `statsmodels` - Statistical models
- `scikit-optimize` - Hyperparameter tuning

**Already in main `requirements.txt`:**
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `scikit-learn` - ML algorithms (Random Forest, etc.)
- `matplotlib` - Plotting
- `influxdb-client` - Training data source

## 🎯 Why Native?

| Benefit | Description |
|---------|-------------|
| ⚡ **Speed** | No Docker overhead, instant iteration |
| 🔧 **GPU** | Apple Silicon MPS works natively |
| 🐛 **Debugging** | VS Code integration, IntelliSense |
| 📁 **Files** | Direct workspace access |
| 🔄 **Updates** | No container rebuilds |

## 📁 File Structure

```
experiments/
├── install_ml_deps.sh              # One-time setup
├── start_jupyter_native.sh         # Daily startup
├── notebooks/
│   ├── 01_response_strategy_optimization.ipynb  # Jupyter notebook
│   └── 01_response_strategy_optimization.py     # Python script
├── models/                          # Saved trained models
├── data/                            # Training data exports
└── results/                         # Experiment outputs
```

## 🔍 Environment Variables

Auto-configured by `start_jupyter_native.sh`:
- `INFLUXDB_HOST=localhost` + `INFLUXDB_PORT=8087`
- `POSTGRES_HOST=localhost` + `POSTGRES_PORT=5433`
- `QDRANT_HOST=localhost` + `QDRANT_PORT=6334`
- `FASTEMBED_CACHE_PATH=/tmp/fastembed_cache`

Notebooks auto-detect via `os.getenv()` - no manual configuration needed!
