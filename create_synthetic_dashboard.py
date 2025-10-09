#!/usr/bin/env python3
"""
Create Synthetic Testing Dashboard for WhisperEngine
"""

import json

def create_synthetic_testing_dashboard():
    """Dashboard for synthetic conversation testing and validation"""
    return {
        "id": None,
        "title": "WhisperEngine Synthetic Testing & Validation",
        "tags": ["whisperengine", "synthetic", "testing", "validation"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "10s",
        "time": {"from": "now-2h", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Synthetic Test Quality Score",
                "type": "gauge",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "synthetic_test_quality")
  |> filter(fn: (r) => r._field == "value")
  |> mean()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "min": 0,
                        "max": 1,
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 0.7},
                                {"color": "green", "value": 0.9}
                            ]
                        }
                    }
                }
            },
            {
                "id": 2,
                "title": "Active Synthetic Users",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "active_synthetic_users")
  |> last()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 10},
                                {"color": "red", "value": 25}
                            ]
                        }
                    }
                }
            },
            {
                "id": 3,
                "title": "Unique Synthetic Users",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "unique_synthetic_users")
  |> last()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 6, "x": 6, "y": 4}
            },
            {
                "id": 4,
                "title": "Test Duration Tracking",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "test_duration_hours")
  |> aggregateWindow(every: 5m, fn: sum, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "h",
                        "custom": {"drawStyle": "line", "lineWidth": 2}
                    }
                }
            },
            {
                "id": 5,
                "title": "Synthetic Conversation Quality",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "synthetic_conversation_quality")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 12, "x": 0, "y": 8},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "custom": {"drawStyle": "line", "lineWidth": 2, "fillOpacity": 20}
                    }
                }
            },
            {
                "id": 6,
                "title": "Synthetic Emotion Testing",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "synthetic_emotion_testing")
  |> filter(fn: (r) => r._field == "emotion_detection_performance")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 12, "x": 12, "y": 8}
            },
            {
                "id": 7,
                "title": "Validation Results Summary",
                "type": "table",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "synthetic_test_quality")
  |> group(columns: ["bot"])
  |> mean()
  |> yield(name: "mean")""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 24, "x": 0, "y": 14},
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "displayMode": "basic",
                            "align": "center"
                        }
                    }
                }
            }
        ]
    }

def main():
    dashboard = create_synthetic_testing_dashboard()
    
    with open("dashboards/whisperengine_synthetic_testing_dashboard.json", 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2)
    
    print("✅ Created Synthetic Testing Dashboard")
    print("📊 Dashboard includes:")
    print("   - Synthetic test quality scoring")
    print("   - Active synthetic users tracking")
    print("   - Test duration monitoring")
    print("   - Conversation quality validation")
    print("   - Emotion detection testing")
    print("   - Per-bot validation results")

if __name__ == "__main__":
    main()