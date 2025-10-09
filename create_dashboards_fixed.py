#!/usr/bin/env python3
"""
WhisperEngine Character Intelligence Dashboards - FIXED VERSION
===============================================

Comprehensive InfluxDB/Grafana dashboard configurations for monitoring
character intelligence performance metrics in real-time.
"""

import json
import os
from typing import Dict, Any

def create_character_performance_dashboard() -> Dict[str, Any]:
    """Generate Character Performance Overview dashboard"""
    return {
        "id": None,
        "title": "WhisperEngine Character Performance Overview",
        "tags": ["whisperengine", "character-intelligence", "performance"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "panels": [
            {
                "id": 1,
                "title": "Character Response Times",
                "type": "timeseries",
                "targets": [],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "ms",
                        "custom": {"drawStyle": "line"}
                    }
                }
            },
            {
                "id": 2,
                "title": "Knowledge Query Success Rate",
                "type": "stat",
                "targets": [],
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 70},
                                {"color": "green", "value": 90}
                            ]
                        }
                    }
                }
            }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "5s"
    }

def create_emotion_analysis_dashboard() -> Dict[str, Any]:
    """Generate Emotion Analysis Intelligence dashboard"""
    return {
        "id": None,
        "title": "WhisperEngine Emotion Analysis Intelligence",
        "tags": ["whisperengine", "emotion-analysis", "roberta"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "panels": [
            {
                "id": 1,
                "title": "RoBERTa Analysis Performance",
                "type": "timeseries",
                "targets": [],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "ms",
                        "custom": {"drawStyle": "line"}
                    }
                }
            },
            {
                "id": 2,
                "title": "Emotion Detection Confidence",
                "type": "stat",
                "targets": [],
                "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 0.6},
                                {"color": "green", "value": 0.8}
                            ]
                        }
                    }
                }
            }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "10s"
    }

def create_vector_memory_dashboard() -> Dict[str, Any]:
    """Generate Vector Memory Performance dashboard"""
    return {
        "id": None,
        "title": "WhisperEngine Vector Memory Performance",
        "tags": ["whisperengine", "vector-memory", "qdrant"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "panels": [
            {
                "id": 1,
                "title": "Qdrant Query Performance",
                "type": "timeseries",
                "targets": [],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "ms",
                        "custom": {"drawStyle": "line"}
                    }
                }
            },
            {
                "id": 2,
                "title": "Memory Retrieval Success Rate",
                "type": "stat",
                "targets": [],
                "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 0.7},
                                {"color": "green", "value": 0.9}
                            ]
                        }
                    }
                }
            }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "10s"
    }

def create_system_health_dashboard() -> Dict[str, Any]:
    """Generate System Health & Optimization dashboard"""
    return {
        "id": None,
        "title": "WhisperEngine System Health & Optimization",
        "tags": ["whisperengine", "system-health", "optimization"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "panels": [
            {
                "id": 1,
                "title": "Overall Processing Time Trends",
                "type": "timeseries",
                "targets": [],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "ms",
                        "custom": {"drawStyle": "line"}
                    }
                }
            },
            {
                "id": 2,
                "title": "Character Intelligence Health Score",
                "type": "stat",
                "targets": [],
                "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percentunit",
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 0.6},
                                {"color": "green", "value": 0.8}
                            ]
                        }
                    }
                }
            }
        ],
        "time": {"from": "now-4h", "to": "now"},
        "refresh": "30s"
    }

def export_all_dashboards():
    """Export all WhisperEngine dashboards to JSON files"""
    os.makedirs("dashboards", exist_ok=True)
    
    dashboards = [
        ("character_performance", create_character_performance_dashboard()),
        ("emotion_analysis", create_emotion_analysis_dashboard()),
        ("vector_memory", create_vector_memory_dashboard()),
        ("system_health", create_system_health_dashboard())
    ]
    
    for name, dashboard in dashboards:
        filename = f"dashboards/whisperengine_{name}_dashboard.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2)
        print(f"✅ Exported: {filename}")
    
    print("🎯 All WhisperEngine Character Intelligence dashboards exported!")

if __name__ == "__main__":
    export_all_dashboards()