#!/usr/bin/env python3
"""
Create specialized Grafana dashboards for WhisperEngine advanced analytics
Based on the comprehensive metrics available in InfluxDB
"""

import json
import os

def create_advanced_dashboards():
    """Create specialized dashboards for different aspects of WhisperEngine"""
    
    dashboards = {
        "relationship_analytics": create_relationship_analytics_dashboard(),
        "performance_optimization": create_performance_optimization_dashboard(),
        "conversation_quality": create_conversation_quality_dashboard(),
        "real_time_operations": create_real_time_operations_dashboard(),
        "character_development": create_character_development_dashboard()
    }
    
    dashboard_dir = "dashboards"
    os.makedirs(dashboard_dir, exist_ok=True)
    
    for name, dashboard in dashboards.items():
        filepath = os.path.join(dashboard_dir, f"whisperengine_{name}_dashboard.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2)
        print(f"✅ Created {filepath}")
    
    return len(dashboards)

def create_relationship_analytics_dashboard():
    """Dashboard for relationship progression and user engagement metrics"""
    return {
        "id": None,
        "title": "WhisperEngine Relationship Analytics",
        "tags": ["whisperengine", "relationships", "engagement"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "10s",
        "time": {"from": "now-6h", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Trust Levels Over Time",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -6h)
  |> filter(fn: (r) => r._measurement == "relationship_progression")
  |> filter(fn: (r) => r._field == "trust_level")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "custom": {"drawStyle": "line", "lineWidth": 2, "fillOpacity": 20},
                        "color": {"mode": "palette-classic"}
                    }
                }
            },
            {
                "id": 2,
                "title": "Affection Progression",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -6h)
  |> filter(fn: (r) => r._measurement == "relationship_progression")
  |> filter(fn: (r) => r._field == "affection_level")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "custom": {"drawStyle": "line", "lineWidth": 2, "fillOpacity": 20},
                        "color": {"mode": "continuous-RdYlBu"}
                    }
                }
            },
            {
                "id": 3,
                "title": "Current Engagement Score",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "conversation_quality")
  |> filter(fn: (r) => r._field == "engagement_score")
  |> last()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": None},
                                {"color": "yellow", "value": 0.5},
                                {"color": "green", "value": 0.8}
                            ]
                        }
                    }
                }
            },
            {
                "id": 4,
                "title": "Relationship Confidence by Bot",
                "type": "bargauge",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "relationship_progression")
  |> filter(fn: (r) => r._field == "relationship_confidence")
  |> group(columns: ["bot"])
  |> mean()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 12, "x": 0, "y": 8},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "color": {"mode": "continuous-GrYlRd"}
                    }
                }
            },
            {
                "id": 5,
                "title": "Communication Comfort Trends",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -6h)
  |> filter(fn: (r) => r._measurement == "character_consistency")
  |> filter(fn: (r) => r._field == "communication_comfort")
  |> aggregateWindow(every: 10m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 12, "x": 12, "y": 8}
            }
        ]
    }

def create_performance_optimization_dashboard():
    """Dashboard for system performance and optimization metrics"""
    return {
        "id": None,
        "title": "WhisperEngine Performance Optimization",
        "tags": ["whisperengine", "performance", "optimization"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "5s",
        "time": {"from": "now-3h", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Response Time Distribution",
                "type": "histogram",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -3h)
  |> filter(fn: (r) => r._measurement == "response_time_v2")
  |> filter(fn: (r) => r._field == "processing_time_ms")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "ms",
                        "custom": {"bucketSize": 500}
                    }
                }
            },
            {
                "id": 2,
                "title": "Memory Performance",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -3h)
  |> filter(fn: (r) => r._measurement == "vector_memory_performance")
  |> filter(fn: (r) => r._field == "search_time_ms")
  |> aggregateWindow(every: 2m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "ms",
                        "custom": {"drawStyle": "line", "lineWidth": 2}
                    }
                }
            },
            {
                "id": 3,
                "title": "RoBERTa Inference Time",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "emotion_analysis_performance")
  |> filter(fn: (r) => r._field == "roberta_inference_time_ms")
  |> mean()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8},
                "fieldConfig": {
                    "defaults": {
                        "unit": "ms",
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
                "id": 4,
                "title": "Optimization Ratio",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "optimization_ratio_v2")
  |> filter(fn: (r) => r._field == "value")
  |> mean()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 6, "x": 6, "y": 8}
            },
            {
                "id": 5,
                "title": "Messages Per Second",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -3h)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "messages_per_second")
  |> aggregateWindow(every: 1m, fn: sum, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 12, "x": 12, "y": 8}
            }
        ]
    }

def create_conversation_quality_dashboard():
    """Dashboard for conversation quality and character consistency"""
    return {
        "id": None,
        "title": "WhisperEngine Conversation Quality",
        "tags": ["whisperengine", "quality", "conversations"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "15s",
        "time": {"from": "now-4h", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Conversation Quality Score",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -4h)
  |> filter(fn: (r) => r._measurement == "conversation_quality")
  |> filter(fn: (r) => r._field == "conversation_quality_score")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
            },
            {
                "id": 2,
                "title": "Character Consistency",
                "type": "gauge",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "character_consistency")
  |> filter(fn: (r) => r._field == "character_consistency_score")
  |> mean()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
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
                "id": 3,
                "title": "Authenticity Score",
                "type": "gauge",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "character_consistency")
  |> filter(fn: (r) => r._field == "authenticity_score")
  |> mean()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
            },
            {
                "id": 4,
                "title": "Fidelity Score Trends",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -4h)
  |> filter(fn: (r) => r._measurement == "fidelity_score_v2")
  |> filter(fn: (r) => r._field == "value")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 12, "x": 0, "y": 8}
            },
            {
                "id": 5,
                "title": "CDL Integration Performance",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -4h)
  |> filter(fn: (r) => r._measurement == "cdl_integration_performance")
  |> filter(fn: (r) => r._field == "cdl_personality_consistency")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 12, "x": 12, "y": 8}
            }
        ]
    }

def create_real_time_operations_dashboard():
    """Dashboard for real-time operational metrics and system health"""
    return {
        "id": None,
        "title": "WhisperEngine Real-Time Operations",
        "tags": ["whisperengine", "operations", "realtime"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "2s",
        "time": {"from": "now-30m", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Active Sessions",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
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
                                {"color": "yellow", "value": 50},
                                {"color": "red", "value": 100}
                            ]
                        }
                    }
                }
            },
            {
                "id": 2,
                "title": "Concurrent Users",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "concurrent_users")
  |> last()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 4, "x": 4, "y": 0}
            },
            {
                "id": 3,
                "title": "Queue Length",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "queue_length")
  |> last()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 4, "x": 8, "y": 0}
            },
            {
                "id": 4,
                "title": "System Utilization",
                "type": "stat",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "session_utilization")
  |> last()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 4, "w": 4, "x": 12, "y": 0}
            },
            {
                "id": 5,
                "title": "Conversations Per Hour by Bot",
                "type": "timeseries",
                "targets": [
                    {
                        "refId": "A",
                        "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "conversations_elena")
  |> aggregateWindow(every: 1m, fn: sum, createEmpty: false)""",
                        "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                    },
                    {
                        "refId": "B",
                        "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "conversations_gabriel")
  |> aggregateWindow(every: 1m, fn: sum, createEmpty: false)""",
                        "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                    },
                    {
                        "refId": "C",
                        "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "performance_metrics")
  |> filter(fn: (r) => r._field == "conversations_sophia")
  |> aggregateWindow(every: 1m, fn: sum, createEmpty: false)""",
                        "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                    }
                ],
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 4}
            },
            {
                "id": 6,
                "title": "Intelligence Coordination Performance",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "intelligence_coordination")
  |> filter(fn: (r) => r._field == "coordination_time_ms")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 12, "x": 0, "y": 12}
            },
            {
                "id": 7,
                "title": "Memory Cache Performance",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "memory_quality_v2")
  |> filter(fn: (r) => r._field == "cache_hit_value")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 12, "x": 12, "y": 12}
            }
        ]
    }

def create_character_development_dashboard():
    """Dashboard for character learning and development trends"""
    return {
        "id": None,
        "title": "WhisperEngine Character Development",
        "tags": ["whisperengine", "character", "development"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "30s",
        "time": {"from": "now-24h", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Confidence Evolution",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "confidence_evolution")
  |> filter(fn: (r) => r._field == "confidence_score")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
            },
            {
                "id": 2,
                "title": "Knowledge Growth",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "character_graph_performance")
  |> filter(fn: (r) => r._field == "knowledge_stored")
  |> aggregateWindow(every: 1h, fn: sum, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
            },
            {
                "id": 3,
                "title": "Memory Aging Trends",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "memory_aging_metrics")
  |> filter(fn: (r) => r._field == "memory_recall_accuracy")
  |> aggregateWindow(every: 2h, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 8, "x": 0, "y": 8}
            },
            {
                "id": 4,
                "title": "Emotional Range Expansion",
                "type": "timeseries",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "user_emotion")
  |> filter(fn: (r) => r._field == "expanded_emotion_count")
  |> aggregateWindow(every: 2h, fn: mean, createEmpty: false)""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 8, "x": 8, "y": 8}
            },
            {
                "id": 5,
                "title": "Character Preservation Score",
                "type": "gauge",
                "targets": [{
                    "refId": "A",
                    "query": """from(bucket: "performance_metrics")
  |> range(start: -4h)
  |> filter(fn: (r) => r._measurement == "character_consistency")
  |> filter(fn: (r) => r._field == "character_preservation")
  |> mean()""",
                    "datasource": {"type": "influxdb", "uid": "influxdb-whisperengine"}
                }],
                "gridPos": {"h": 6, "w": 8, "x": 16, "y": 8},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "min": 0,
                        "max": 1,
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 0.8},
                                {"color": "green", "value": 0.95}
                            ]
                        }
                    }
                }
            }
        ]
    }

if __name__ == "__main__":
    print("🎯 Creating Advanced WhisperEngine Grafana Dashboards...")
    count = create_advanced_dashboards()
    print(f"\n✅ Created {count} specialized dashboards!")
    print("\nDashboards created:")
    print("1. 📊 Relationship Analytics - Trust, affection, engagement tracking")
    print("2. ⚡ Performance Optimization - Response times, memory performance, optimization ratios")
    print("3. 🎭 Conversation Quality - Quality scores, character consistency, authenticity")
    print("4. 🔴 Real-Time Operations - Live session metrics, concurrent users, system health")
    print("5. 📈 Character Development - Learning trends, knowledge growth, emotional expansion")