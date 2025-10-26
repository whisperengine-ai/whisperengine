#!/usr/bin/env .venv/bin/python3
"""
Response Strategy Optimization - WhisperEngine ML Experiment 01

This experiment trains a model to predict optimal response strategies based on:
- Time of day
- User engagement patterns
- Conversation history
- Recent emotional states

Goal: Learn when to use different CDL conversation modes for better engagement.

Expected Performance:
- 75-85% accuracy with synthetic training data
- 80-85% accuracy with synthetic + augmented real user data

GPU Support:
- Auto-detects Apple Silicon (MPS), NVIDIA (CUDA), or CPU
- XGBoost/LightGBM can leverage GPU acceleration
- Random Forest remains CPU-only (scikit-learn doesn't support GPU)
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ============================================================================
# GPU AUTO-DETECTION
# ============================================================================

def detect_gpu():
    """Auto-detect available GPU and return device configuration"""
    
    # Check for Apple Silicon (MPS)
    try:
        import torch
        if torch.backends.mps.is_available():
            print("✅ Detected: Apple Silicon GPU (MPS)")
            return "mps", "cpu_hist"  # XGBoost uses 'cpu_hist' for Apple Silicon
    except ImportError:
        pass
    
    # Check for NVIDIA GPU (CUDA)
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ Detected: NVIDIA GPU - {gpu_name}")
            return "cuda", "gpu_hist"  # XGBoost uses 'gpu_hist' for CUDA
    except ImportError:
        pass
    
    # Fallback to CPU
    print("ℹ️  No GPU detected - using CPU")
    return "cpu", "hist"  # XGBoost uses 'hist' for CPU

# Auto-detect GPU at startup
GPU_DEVICE, XGBOOST_TREE_METHOD = detect_gpu()

# ============================================================================
# STEP 1: CONNECT TO INFLUXDB (READ TRAINING DATA)
# ============================================================================

def connect_to_influxdb():
    """Connect to WhisperEngine InfluxDB to query conversation metrics"""
    
    # Use localhost when running outside Docker, influxdb hostname when inside Docker
    influxdb_host = os.getenv("INFLUXDB_HOST", "localhost")
    influxdb_port = os.getenv("INFLUXDB_PORT", "8087")  # External port
    
    client = InfluxDBClient(
        url=f"http://{influxdb_host}:{influxdb_port}",
        token="whisperengine-fidelity-first-metrics-token",
        org="whisperengine"
    )
    
    return client, client.query_api()

# ============================================================================
# STEP 2: QUERY TRAINING DATA FROM INFLUXDB
# ============================================================================

def query_conversation_quality_data(query_api, days_back=30):
    """
    Query conversation quality metrics from InfluxDB
    
    Returns DataFrame with:
    - user_id
    - bot_name
    - timestamp
    - engagement_score (target variable)
    - satisfaction_score
    - natural_flow_score
    - emotional_resonance
    - topic_relevance
    """
    
    query = f'''
    from(bucket: "performance_metrics")
      |> range(start: -{days_back}d)
      |> filter(fn: (r) => r._measurement == "conversation_quality")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    
    result = query_api.query(query)
    
    # Parse results into DataFrame
    records = []
    for table in result:
        for record in table.records:
            records.append({
                'timestamp': record.get_time(),
                'user_id': record.values.get('user_id'),
                'bot_name': record.values.get('bot'),
                'engagement_score': record.values.get('engagement_score', 0.5),
                'satisfaction_score': record.values.get('satisfaction_score', 0.5),
                'natural_flow_score': record.values.get('natural_flow_score', 0.5),
                'emotional_resonance': record.values.get('emotional_resonance', 0.5),
                'topic_relevance': record.values.get('topic_relevance', 0.5)
            })
    
    df = pd.DataFrame(records)
    print(f"✅ Loaded {len(df)} conversation quality records from InfluxDB")
    return df

# ============================================================================
# STEP 3: FEATURE ENGINEERING
# ============================================================================

def engineer_features(df):
    """
    Create ML features from conversation data
    
    Features:
    - User conversation history patterns
    - Time of day
    - Conversation length trends
    - Emotional patterns
    - Bot personality (one-hot encoded)
    """
    
    # Time-based features
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # User-specific aggregates (rolling windows)
    df = df.sort_values(['user_id', 'timestamp'])
    
    for metric in ['engagement_score', 'satisfaction_score', 'emotional_resonance']:
        # 7-day moving average per user
        df[f'{metric}_ma7'] = df.groupby('user_id')[metric].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )
        
        # Recent trend (last 3 conversations)
        df[f'{metric}_trend3'] = df.groupby('user_id')[metric].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean()
        )
    
    # Bot personality (one-hot encode)
    df = pd.get_dummies(df, columns=['bot_name'], prefix='bot')
    
    print(f"✅ Engineered {len(df.columns)} features")
    return df

# ============================================================================
# STEP 4: DEFINE TARGET VARIABLE (RESPONSE STRATEGY EFFECTIVENESS)
# ============================================================================

def create_target_labels(df):
    """
    Create binary target: Was this conversation effective?
    
    Effective = engagement_score > 0.7 AND satisfaction_score > 0.7
    
    In production, this would be 3-class:
    - 0: Ineffective (need to change strategy)
    - 1: Neutral (maintain current strategy)
    - 2: Highly effective (reinforce this strategy)
    """
    
    df['is_effective'] = (
        (df['engagement_score'] > 0.7) & 
        (df['satisfaction_score'] > 0.7)
    ).astype(int)
    
    print(f"✅ Target distribution:")
    print(df['is_effective'].value_counts(normalize=True))
    
    return df

# ============================================================================
# STEP 5: TRAIN ML MODEL (WITH GPU SUPPORT)
# ============================================================================

def train_response_strategy_model(df, use_gpu=True, algorithm="auto"):
    """
    Train ML model to predict conversation effectiveness
    
    Args:
        df: Training data
        use_gpu: Whether to use GPU if available (default: True)
        algorithm: "auto" (picks best), "random_forest", "xgboost", "lightgbm"
    
    Returns:
        model, feature_cols, feature_importance
    """
    
    # Select features
    feature_cols = [col for col in df.columns if any([
        col.startswith('bot_'),
        col.endswith('_ma7'),
        col.endswith('_trend3'),
        col in ['hour_of_day', 'day_of_week', 'is_weekend']
    ])]
    
    X = df[feature_cols].fillna(0)  # Handle any NaN values
    y = df['is_effective']
    
    print(f"Training with {len(feature_cols)} features on {len(X)} samples")
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Choose algorithm
    if algorithm == "auto":
        # XGBoost with GPU if available, otherwise Random Forest
        algorithm = "xgboost" if use_gpu and GPU_DEVICE != "cpu" else "random_forest"
        print(f"🤖 Auto-selected: {algorithm}")
    
    # Train model based on algorithm choice
    if algorithm == "xgboost":
        try:
            import xgboost as xgb
            
            # Configure device for XGBoost 3.x+
            if use_gpu:
                if GPU_DEVICE == "cuda":
                    device = "cuda"
                    tree_method = "hist"
                elif GPU_DEVICE == "mps":
                    # Apple Silicon - XGBoost doesn't support MPS yet
                    device = "cpu"
                    tree_method = "hist"
                    print("ℹ️  Note: XGBoost doesn't support Apple Silicon GPU yet, using CPU")
                else:
                    device = "cpu"
                    tree_method = "hist"
            else:
                device = "cpu"
                tree_method = "hist"
            
            print(f"🚀 Training XGBoost model (device={device}, tree_method={tree_method})...")
            
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=10,
                learning_rate=0.1,
                tree_method=tree_method,
                device=device,
                random_state=42,
                eval_metric='logloss'
            )
            
            model.fit(X_train, y_train)
            feature_importance_values = model.feature_importances_
            
        except ImportError:
            print("⚠️  XGBoost not installed, falling back to Random Forest")
            algorithm = "random_forest"
    
    if algorithm == "lightgbm":
        try:
            import lightgbm as lgb
            
            device = "gpu" if use_gpu and GPU_DEVICE != "cpu" else "cpu"
            print(f"🚀 Training LightGBM model (device={device})...")
            
            model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=10,
                learning_rate=0.1,
                device=device,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            feature_importance_values = model.feature_importances_
            
        except ImportError:
            print("⚠️  LightGBM not installed, falling back to Random Forest")
            algorithm = "random_forest"
    
    if algorithm == "random_forest":
        print("🚀 Training Random Forest model (CPU-only)...")
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            random_state=42,
            n_jobs=-1  # Use all CPU cores
        )
        
        model.fit(X_train, y_train)
        feature_importance_values = model.feature_importances_
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = (y_pred == y_test).mean()
    
    print(f"\n✅ Model Accuracy: {accuracy:.3f} ({algorithm})")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, 
                                target_names=['Ineffective', 'Effective']))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': feature_importance_values
    }).sort_values('importance', ascending=False).head(10)
    
    print("\n📊 Top 10 Most Important Features:")
    print(feature_importance)
    
    return model, feature_cols, feature_importance

# ============================================================================
# STEP 6: VISUALIZE RESULTS
# ============================================================================

def visualize_results(feature_importance):
    """Create visualizations of model performance"""
    
    # Use current directory when running outside Docker
    results_dir = Path('experiments/results')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=feature_importance, x='importance', y='feature')
    plt.title('Top 10 Features Predicting Conversation Effectiveness')
    plt.xlabel('Feature Importance')
    plt.tight_layout()
    plt.savefig(results_dir / 'feature_importance.png', dpi=150)
    print(f"✅ Saved feature importance plot to {results_dir / 'feature_importance.png'}")

# ============================================================================
# MAIN EXPERIMENT RUNNER
# ============================================================================

def main(use_gpu=True, algorithm="auto"):
    """
    Run the full ML experiment
    
    Args:
        use_gpu: Whether to use GPU if available (default: True)
        algorithm: "auto", "random_forest", "xgboost", or "lightgbm"
    """
    
    print("=" * 70)
    print("WhisperEngine ML Experiment 1: Response Strategy Optimization")
    if use_gpu and GPU_DEVICE != "cpu":
        print(f"🚀 GPU-Accelerated ML - Using {GPU_DEVICE.upper()}")
    else:
        print("💻 CPU-only ML - No GPU required")
    print("=" * 70)
    
    # Step 1: Connect to InfluxDB
    print("\n[1/6] Connecting to InfluxDB...")
    client, query_api = connect_to_influxdb()
    
    # Step 2: Query training data
    print("\n[2/6] Querying conversation quality data...")
    df = query_conversation_quality_data(query_api, days_back=30)
    
    if len(df) == 0:
        print("❌ No data found! Make sure you have conversation_quality data in InfluxDB")
        print("   Run some bot conversations first to generate training data.")
        return
    
    # Step 3: Engineer features
    print("\n[3/6] Engineering features...")
    df = engineer_features(df)
    
    # Step 4: Create target labels
    print("\n[4/6] Creating target labels...")
    df = create_target_labels(df)
    
    # Step 5: Train model
    print("\n[5/6] Training ML model...")
    model, feature_cols, feature_importance = train_response_strategy_model(
        df, use_gpu=use_gpu, algorithm=algorithm
    )
    
    # Step 6: Visualize
    print("\n[6/6] Creating visualizations...")
    visualize_results(feature_importance)
    
    # Save model
    import joblib
    models_dir = Path('experiments/models')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_name = f'response_strategy_{algorithm}_v1.pkl' if algorithm != "auto" else 'response_strategy_model_v1.pkl'
    model_path = models_dir / model_name
    features_path = models_dir / 'response_strategy_features_v1.pkl'
    
    joblib.dump(model, model_path)
    joblib.dump(feature_cols, features_path)
    print(f"\n✅ Saved model to {model_path}")
    print(f"✅ Saved features to {features_path}")
    
    print("\n" + "=" * 70)
    print("✅ Experiment Complete!")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. Review feature importance to understand what drives effectiveness")
    print("2. Integrate model into MessageProcessor for real-time strategy selection")
    print("3. Run A/B test: ML-predicted strategy vs. current rule-based")
    print("4. Track improvement in engagement_score over 1 week")

# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Train ML model for WhisperEngine response strategy optimization"
    )
    parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Disable GPU acceleration (default: auto-detect and use if available)"
    )
    parser.add_argument(
        "--algorithm",
        choices=["auto", "random_forest", "xgboost", "lightgbm"],
        default="auto",
        help="ML algorithm to use (default: auto - picks best for available hardware)"
    )
    
    args = parser.parse_args()
    
    main(use_gpu=not args.no_gpu, algorithm=args.algorithm)
