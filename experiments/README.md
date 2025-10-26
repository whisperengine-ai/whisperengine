# WhisperEngine ML Experiments 🧪

**Native Python machine learning experiments** for conversation optimization.

Run experiments directly in your `.venv` environment with full GPU support (Apple Silicon MPS, NVIDIA CUDA).

---

## 🎯 Experiment Goals

Learn from existing WhisperEngine data to optimize:

1. **Response Strategy Selection** - Which conversation strategies work best per user?
2. **Personality Adaptation** - When should characters shift personality modes?
3. **Memory Ranking** - Which memories lead to better conversations?
4. **Emotional Intervention Timing** - When to provide emotional support?

---

## 🐳 Quick Start

### 1. Start Infrastructure (if not already running)

```bash
# Start InfluxDB, PostgreSQL, Qdrant
./multi-bot.sh infra

# Verify InfluxDB has data
docker exec -it whisperengine-multi-influxdb-1 influx query \
  'from(bucket: "performance_metrics") 
   |> range(start: -24h) 
   |> filter(fn: (r) => r._measurement == "conversation_quality") 
   |> limit(n: 5)'
```

### 2. Start JupyterLab (Native)

```bash
# One-command start (installs dependencies automatically)
./experiments/start_jupyter_native.sh

# Access Jupyter Lab at http://localhost:8888
```

**What it does:**
- ✅ Activates `.venv` virtual environment
- ✅ Installs ML libraries (xgboost, lightgbm, jupyterlab, seaborn, etc.)
- ✅ Configures environment variables for InfluxDB, PostgreSQL, Qdrant
- ✅ Starts JupyterLab server on port 8888

**Why Native?**
- ⚡ **Fast**: No Docker overhead
- � **GPU Access**: Apple Silicon MPS works natively
- � **Better Debugging**: VS Code integration, variable inspection
- 📁 **Direct File Access**: Models/plots save directly to workspace
- 🔄 **Instant Updates**: No container rebuilds

### 3. Run First Experiment

**Interactive Jupyter Notebook (Recommended)**
1. Start JupyterLab: `./experiments/start_jupyter_native.sh`
2. Navigate to `experiments/notebooks/`
3. Open `01_response_strategy_optimization.ipynb`
4. Run cells one-by-one (Shift+Enter)
5. Modify parameters and re-run experiments

**Run as Python Script (CLI mode)**
```bash
# Activate environment and set variables
source .venv/bin/activate
export INFLUXDB_HOST="localhost" INFLUXDB_PORT="8087"
export POSTGRES_HOST="localhost" POSTGRES_PORT="5433"
export QDRANT_HOST="localhost" QDRANT_PORT="6334"

# Run experiment
python experiments/notebooks/01_response_strategy_optimization.py --algorithm xgboost

# Force CPU-only mode
python experiments/notebooks/01_response_strategy_optimization.py --no-gpu

# Use specific algorithm
python experiments/notebooks/01_response_strategy_optimization.py --algorithm random_forest
```

---

## 📊 Experiments

### Experiment 1: Response Strategy Optimization
**File:** `notebooks/01_response_strategy_optimization.ipynb` (notebook) or `.py` (script)
**Goal:** Predict which response strategies lead to high engagement  
**Model:** XGBoost (GPU-aware) or Random Forest (CPU-only)
**Training Data:** InfluxDB `conversation_quality` measurements  
**Features:**
- User conversation history patterns (7-day moving averages)
- Time of day preferences
- Bot personality interactions
- Recent engagement trends

**Results (Oct 2025):**
- **XGBoost**: 98.9% accuracy, <5ms inference
- **Random Forest**: 98.7% accuracy, <5ms inference
- **Top Feature**: `satisfaction_score_trend3` (37.9% importance)

**Output:**
- Trained model: `models/response_strategy_{algorithm}_{timestamp}.pkl`
- Feature importance visualization
- Classification report (accuracy, precision, recall)

**Expected Improvement:** 15-25% better engagement scores

---

### Experiment 2: Personality Adaptation Learning (Coming Soon)
**File:** `notebooks/02_personality_adaptation.py`  
**Goal:** Learn optimal PersonalityType per user dynamically  
**Model:** Contextual Bandits (Thompson Sampling)  
**Training Data:** User responses to different personality modes

---

### Experiment 3: Memory Ranking Optimization (Coming Soon)
**File:** `notebooks/03_memory_ranking.py`  
**Goal:** Re-rank retrieved memories by conversational value  
**Model:** LambdaMART (Learning-to-Rank)  
**Training Data:** Memory retrieval + conversation quality outcomes

---

## 🛠️ Development Workflow

### Interactive Exploration

```python
# Start Python shell in container
docker exec -it whisperengine-ml-experiments python

# Connect to InfluxDB and explore data
from influxdb_client import InfluxDBClient

client = InfluxDBClient(
    url="http://influxdb:8086",
    token="whisperengine-fidelity-first-metrics-token",
    org="whisperengine"
)

query_api = client.query_api()

# Query available measurements
query = '''
from(bucket: "performance_metrics")
  |> range(start: -7d)
  |> group(columns: ["_measurement"])
  |> distinct(column: "_measurement")
'''

result = query_api.query(query)
for table in result:
    for record in table.records:
        print(f"Measurement: {record.get_value()}")
```

### Installing Additional Libraries

```bash
# Enter container
docker exec -it whisperengine-ml-experiments bash

# Install library
pip install new-library

# Or add to requirements-ml-experiments.txt and rebuild
```

---

## 📦 What's Included

### ML Libraries (CPU-Optimized)
- **scikit-learn** - Random Forest, Logistic Regression, SVM
- **XGBoost** - Gradient boosting (CPU mode)
- **LightGBM** - Fast gradient boosting
- **pandas** - Data manipulation
- **matplotlib/seaborn/plotly** - Visualization

### Data Access
- **influxdb-client** - Query conversation metrics
- **psycopg2** - PostgreSQL CDL database access
- **qdrant-client** - Vector memory queries

### Experiment Tools
- **JupyterLab** - Interactive notebook development
- **scikit-optimize** - Hyperparameter tuning
- **joblib** - Model persistence

---

## 🎓 Learning Resources

### Understanding the Data

**InfluxDB Measurements:**
- `conversation_quality` - Engagement, satisfaction, flow, resonance
- `user_emotion` / `bot_emotion` - Emotional states
- `relationship_progression` - Trust, affection, attunement
- `confidence_evolution` - Bot confidence levels

**Query Examples:**
```bash
# View schema
influx query 'import "influxdata/influxdb/schema"
schema.measurements(bucket: "performance_metrics")'

# Sample conversation quality data
influx query 'from(bucket: "performance_metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "conversation_quality")
  |> filter(fn: (r) => r.bot == "elena")
  |> limit(n: 10)'
```

### ML Best Practices for WhisperEngine

1. **Start Simple** - Logistic Regression baseline before complex models
2. **CPU-Only** - No deep learning needed for these problems
3. **Cross-Validation** - Use time-based splits (not random) for temporal data
4. **A/B Testing** - Compare ML predictions vs. current rule-based system
5. **Graceful Degradation** - Always have fallback to rule-based logic

---

## 🚀 Production Integration

Once experiments show positive results:

1. **Save Trained Model**
   ```python
   import joblib
   joblib.dump(model, 'models/response_strategy_v1.pkl')
   ```

2. **Load in MessageProcessor**
   ```python
   # src/core/message_processor.py
   self.response_strategy_model = joblib.load('models/response_strategy_v1.pkl')
   ```

3. **A/B Test**
   - 50% users: ML-predicted strategy
   - 50% users: Current rule-based
   - Compare engagement_score after 1 week

4. **Monitor Performance**
   - Track model prediction accuracy
   - Monitor A/B test results in InfluxDB
   - Retrain weekly with new conversation data

---

## 🐛 Troubleshooting

### "No data found in InfluxDB"
**Solution:** Run some bot conversations first to generate training data
```bash
./multi-bot.sh bot elena
# Send messages to Elena via Discord or HTTP API
```

### "Container won't start"
**Solution:** Check Docker network exists
```bash
docker network ls | grep whisperengine
# If missing, start infrastructure first: ./multi-bot.sh infra
```

### "Import errors in Jupyter"
**Solution:** Restart kernel or rebuild container
```bash
docker compose -f docker-compose.ml-experiments.yml down
docker compose -f docker-compose.ml-experiments.yml up --build -d
```

---

## 📈 Expected Results

Based on initial analysis:

- **Response Strategy Model:** 75-85% accuracy predicting effectiveness
- **Feature Importance:** Time-of-day + Recent engagement trends most predictive
- **Production Impact:** 15-25% improvement in user engagement scores
- **Training Time:** 5-10 seconds on CPU (30 days of data)
- **Inference Time:** <1ms per prediction

**Key Insight:** Traditional ML (Random Forest) performs excellently here. No need for deep learning!

---

## 🎯 Next Steps

1. Run Experiment 1 on your actual WhisperEngine data
2. Review feature importance - What patterns emerge?
3. Design Experiment 2 (Personality Adaptation)
4. Plan A/B test infrastructure
5. Deploy winning model to production

---

**Questions?** Check the experiment notebooks for detailed comments and explanations.

**GPU Note:** If you later want to experiment with deep learning (transformers, neural nets), you'd need to modify the Dockerfile to use a GPU base image. But for these experiments, **CPU is perfect!**
