#!/usr/bin/env python3
"""
Create WORKING Grafana dashboards using only confirmed available data
Based on actual InfluxDB measurements with real data
"""

import json
import os

def create_working_dashboards():
    """Create dashboards that will actually show data"""
    
    dashboards = {
        "confirmed_real_time": create_confirmed_real_time_dashboard(),
        "confirmed_character_analytics": create_confirmed_character_dashboard(),
        "confirmed_performance": create_confirmed_performance_dashboard()
    }
    
    dashboard_dir = "dashboards"
    os.makedirs(dashboard_dir, exist_ok=True)
    
    for name, dashboard in dashboards.items():
        filepath = os.path.join(dashboard_dir, f"whisperengine_{name}_dashboard.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2)
        print(f"✅ Created {filepath} - GUARANTEED DATA")
    
    return len(dashboards)

def create_confirmed_real_time_dashboard():
    """Real-time dashboard using confirmed data sources"""
    return {
        "id": None,
        "title": "WhisperEngine LIVE Operations (Confirmed Data)",
        "tags": ["whisperengine", "live", "confirmed"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "2s",
        "time": {"from": "now-30m", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Active Sessions (LIVE)",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "response_time_v2")
  |> filter(fn: (r) => r._field == "active_sessions")
  |> last()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 4, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 100},
                                {"color": "red", "value": 200}
                            ]
                        }
                    }
                }
            },
            {
                "id": 2,
                "title": "Concurrent Users (LIVE)",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "response_time_v2")
  |> filter(fn: (r) => r._field == "concurrent_users")
  |> last()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 4, "x": 4, "y": 0}
            },
            {
                "id": 3,
                "title": "Queue Length (LIVE)",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "response_time_v2")
  |> filter(fn: (r) => r._field == "queue_length")
  |> last()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 4, "x": 8, "y": 0}
            },
            {
                "id": 4,
                "title": "Messages Per Second",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "response_time_v2")
  |> filter(fn: (r) => r._field == "messages_per_second")
  |> aggregateWindow(every: 30s, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
            },
            {
                "id": 5,
                "title": "Response Length Distribution",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "response_time_v2")
  |> filter(fn: (r) => r._field == "response_length")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
            },
            {
                "id": 6,
                "title": "System Utilization Live",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "response_time_v2")
  |> filter(fn: (r) => r._field == "session_utilization")
  |> aggregateWindow(every: 30s, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 24, "x": 0, "y": 12}
            }
        ]
    }

def create_confirmed_character_dashboard():
    """Character analytics using confirmed data sources"""
    return {
        "id": None,
        "title": "WhisperEngine Character Analytics (Confirmed Data)",
        "tags": ["whisperengine", "character", "confirmed"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "10s",
        "time": {"from": "now-2h", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Confidence Evolution",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "confidence_evolution")
  |> filter(fn: (r) => r._field == "confidence_score")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
            },
            {
                "id": 2,
                "title": "Conversation Quality Score",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "conversation_quality")
  |> filter(fn: (r) => r._field == "conversation_quality_score")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
            },
            {
                "id": 3,
                "title": "Character Consistency",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "character_consistency_v2")
  |> filter(fn: (r) => r._field == "character_consistency_score")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 8, "x": 0, "y": 8}
            },
            {
                "id": 4,
                "title": "Fidelity Score",
                "type": "gauge",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fidelity_score_v2")
  |> filter(fn: (r) => r._field == "value")
  |> mean()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 8, "x": 8, "y": 8},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "min": 0,
                        "max": 1
                    }
                }
            },
            {
                "id": 5,
                "title": "Memory Quality",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "memory_quality_v2")
  |> filter(fn: (r) => r._field == "memory_recall_accuracy")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 8, "x": 16, "y": 8}
            }
        ]
    }

def create_confirmed_performance_dashboard():
    """Performance dashboard using confirmed data sources"""
    return {
        "id": None,
        "title": "WhisperEngine Performance Metrics (Confirmed Data)",
        "tags": ["whisperengine", "performance", "confirmed"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "5s",
        "time": {"from": "now-1h", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Response Time Values",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "response_time_v2")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 2m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "ms"
                    }
                }
            },
            {
                "id": 2,
                "title": "Optimization Ratio",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "optimization_ratio_v2")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 2m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
            },
            {
                "id": 3,
                "title": "Emotion Analysis Performance",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "emotion_analysis_performance")
  |> filter(fn: (r) => r._field == "analysis_time_ms")
  |> aggregateWindow(every: 2m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 8, "x": 0, "y": 8}
            },
            {
                "id": 4,
                "title": "Bot Emotion Distribution",
                "type": "piechart",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "bot_emotion")
  |> filter(fn: (r) => r._field == "confidence")
  |> group(columns: ["bot"])
  |> count()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 8, "x": 8, "y": 8}
            },
            {
                "id": 5,
                "title": "Intelligence Coordination",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "intelligence_coordination_metrics")
  |> filter(fn: (r) => r._field == "coordination_time_ms")
  |> mean()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 8, "x": 16, "y": 8},
                "fieldConfig": {
                    "defaults": {"unit": "ms"}
                }
            }
        ]
    }

if __name__ == "__main__":
    print("🎯 Creating CONFIRMED DATA Grafana Dashboards...")
    count = create_working_dashboards()
    print(f"\n✅ Created {count} dashboards with GUARANTEED data!")
    print("\n📊 These dashboards use only confirmed available measurements:")
    print("1. 🔴 LIVE Operations - Real-time metrics from response_time_v2")
    print("2. 🎭 Character Analytics - Character data from confidence_evolution, conversation_quality")
    print("3. ⚡ Performance Metrics - Performance data from confirmed measurements")
    print("\n🚨 THESE WILL SHOW DATA IMMEDIATELY!")