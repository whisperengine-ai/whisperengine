"""
WhisperEngine Character Intelligence Dashboards
===============================================

Comprehensive InfluxDB/Grafana dashboard configurations for monitoring
character intelligence performance metrics in real-time.

Dashboard Categories:
1. Character Performance Overview
2. Emotion Analysis Intelligence  
3. Vector Memory Performance
4. Intelligence Coordination Metrics
5. System Health & Optimization
"""

import json
from typing import Dict, List, Any

class WhisperEngineDashboardGenerator:
    """Generate Grafana dashboard configurations for WhisperEngine metrics"""
    
    def __init__(self):
        self.datasource_uid = "influxdb-whisperengine"
        
    def generate_character_performance_dashboard(self) -> Dict[str, Any]:
        """Generate Character Performance Overview dashboard"""
        return {
            "id": None,
            "title": "WhisperEngine - Character Performance Overview",
            "tags": ["whisperengine", "character-intelligence", "performance"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Character Response Times",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "SELECT mean(\"processing_time_ms\") FROM \"character_graph_performance\" WHERE $timeFilter GROUP BY time($__interval), \"bot\" fill(null)",
                            "datasource": {"uid": self.datasource_uid}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "ms",
                            "color": {"mode": "palette-classic"}
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Knowledge Query Success Rate",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "SELECT mean(\"knowledge_matches\") FROM \"character_graph_performance\" WHERE $timeFilter GROUP BY \"bot\"",
                            "datasource": {"uid": self.datasource_uid}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "mappings": [],
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "yellow", "value": 0.7},
                                    {"color": "green", "value": 0.9}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Cache Hit Ratio",
                    "type": "gauge",
                    "targets": [
                        {
                            "expr": "SELECT mean(case when \"cache_hit\"=true then 1 else 0 end) FROM \"character_graph_performance\" WHERE $timeFilter GROUP BY \"bot\"",
                            "datasource": {"uid": self.datasource_uid}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percentunit",
                            "min": 0,
                            "max": 1,
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "yellow", "value": 0.5},
                                    {"color": "green", "value": 0.8}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
                },
                {
                    "id": 4,
                    "title": "Character Authenticity Scores",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "SELECT mean(\"authenticity_score\") FROM \"intelligence_coordination_metrics\" WHERE $timeFilter GROUP BY time($__interval), \"bot\" fill(null)",
                            "datasource": {"uid": self.datasource_uid}
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percentunit",
                            "min": 0,
                            "max": 1,
                            "color": {"mode": "palette-classic"}
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                },
                {
                    "id": 5,
                    "title": "Intelligence System Coordination",
                    "type": "heatmap",
                    "targets": [
                        {
                            "expr": "SELECT mean(\"coordination_time_ms\") FROM \"intelligence_coordination_metrics\" WHERE $timeFilter GROUP BY time($__interval), \"context_type\", \"coordination_strategy\"",
                            "datasource": {"uid": self.datasource_uid}
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                }
            ],
            "time": {"from": "now-1h", "to": "now"},
            "refresh": "5s"
        }
    
    def generate_emotion_analysis_dashboard(self) -> Dict[str, Any]:
        """Generate Emotion Analysis Intelligence dashboard"""
        return {
            "id": None,
            "title": "WhisperEngine - Emotion Analysis Intelligence",
            "tags": ["whisperengine", "emotion-analysis", "roberta"],
            "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "RoBERTa Analysis Performance",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"analysis_time_ms\") FROM \"emotion_analysis_performance\" WHERE $timeFilter GROUP BY time($__interval), \"bot\" fill(null)",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "ms",
                                "color": {"mode": "palette-classic"}
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Emotion Detection Confidence",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"confidence_score\") FROM \"emotion_analysis_performance\" WHERE $timeFilter GROUP BY \"bot\"",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
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
                        },
                        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Multi-Emotion Detection Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"emotion_count\") FROM \"emotion_analysis_performance\" WHERE $timeFilter GROUP BY \"bot\"",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "short",
                                "decimals": 1
                            }
                        },
                        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0}
                    },
                    {
                        "id": 4,
                        "title": "Primary Emotions Distribution",
                        "type": "piechart",
                        "targets": [
                            {
                                "expr": "SELECT count(*) FROM \"emotion_analysis_performance\" WHERE $timeFilter GROUP BY \"primary_emotion\"",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 4}
                    },
                    {
                        "id": 5,
                        "title": "User vs Bot Emotion Trends",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"intensity\") FROM \"user_emotions\" WHERE $timeFilter GROUP BY time($__interval), \"primary_emotion\" fill(null)",
                                "datasource": {"uid": self.datasource_uid},
                                "alias": "User Emotions"
                            },
                            {
                                "expr": "SELECT mean(\"intensity\") FROM \"bot_emotions\" WHERE $timeFilter GROUP BY time($__interval), \"primary_emotion\" fill(null)",
                                "datasource": {"uid": self.datasource_uid},
                                "alias": "Bot Emotions"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percentunit",
                                "color": {"mode": "palette-classic"}
                            }
                        },
                        "gridPos": {"h": 8, "w": 18, "x": 0, "y": 8}
                    },
                    {
                        "id": 6,
                        "title": "RoBERTa Inference Time vs Accuracy",
                        "type": "scatterplot",
                        "targets": [
                            {
                                "expr": "SELECT \"roberta_inference_time_ms\", \"confidence_score\" FROM \"emotion_analysis_performance\" WHERE $timeFilter",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 8}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "10s"
            }

    def generate_vector_memory_dashboard(self) -> Dict[str, Any]:
        """Generate Vector Memory Performance dashboard"""
        return {
            "id": None,
            "title": "WhisperEngine - Vector Memory Performance",
            "tags": ["whisperengine", "vector-memory", "qdrant"],
            "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Qdrant Query Performance",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"search_time_ms\") FROM \"vector_memory_performance\" WHERE $timeFilter GROUP BY time($__interval), \"bot\", \"vector_type\" fill(null)",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "ms",
                                "color": {"mode": "palette-classic"}
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Memory Retrieval Success Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "SELECT mean(case when \"memories_found\">0 then 1 else 0 end) FROM \"vector_memory_performance\" WHERE $timeFilter GROUP BY \"bot\"",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
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
                        },
                        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Average Relevance Score",
                        "type": "gauge",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"avg_relevance_score\") FROM \"vector_memory_performance\" WHERE $timeFilter GROUP BY \"bot\"",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percentunit",
                                "min": 0,
                                "max": 1,
                                "thresholds": {
                                    "steps": [
                                        {"color": "red", "value": 0},
                                        {"color": "yellow", "value": 0.5},
                                        {"color": "green", "value": 0.8}
                                    ]
                                }
                            }
                        },
                        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0}
                    },
                    {
                        "id": 4,
                        "title": "Vector Type Performance Comparison",
                        "type": "barchart",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"search_time_ms\") FROM \"vector_memory_performance\" WHERE $timeFilter GROUP BY \"vector_type\"",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 4}
                    },
                    {
                        "id": 5,
                        "title": "Memory Collection Performance",
                        "type": "table",
                        "targets": [
                            {
                                "expr": "SELECT \"collection_name\", mean(\"search_time_ms\") as \"avg_search_time\", mean(\"memories_found\") as \"avg_memories\", mean(\"avg_relevance_score\") as \"avg_relevance\" FROM \"vector_memory_performance\" WHERE $timeFilter GROUP BY \"collection_name\"",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 4}
                    },
                    {
                        "id": 6,
                        "title": "3D Named Vector System Performance",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"search_time_ms\") FROM \"vector_memory_performance\" WHERE $timeFilter AND \"vector_type\" IN ('content', 'emotion', 'semantic') GROUP BY time($__interval), \"vector_type\" fill(null)",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "ms",
                                "color": {"mode": "palette-classic"}
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "10s"
            }
        }

    def generate_system_health_dashboard(self) -> Dict[str, Any]:
        """Generate System Health & Optimization dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "WhisperEngine - System Health & Optimization",
                "tags": ["whisperengine", "system-health", "optimization"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Overall Processing Time Trends",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"coordination_time_ms\") FROM \"intelligence_coordination_metrics\" WHERE $timeFilter GROUP BY time($__interval), \"bot\" fill(null)",
                                "datasource": {"uid": self.datasource_uid},
                                "alias": "Intelligence Coordination"
                            },
                            {
                                "expr": "SELECT mean(\"analysis_time_ms\") FROM \"emotion_analysis_performance\" WHERE $timeFilter GROUP BY time($__interval), \"bot\" fill(null)",
                                "datasource": {"uid": self.datasource_uid},
                                "alias": "Emotion Analysis"
                            },
                            {
                                "expr": "SELECT mean(\"search_time_ms\") FROM \"vector_memory_performance\" WHERE $timeFilter GROUP BY time($__interval), \"bot\" fill(null)",
                                "datasource": {"uid": self.datasource_uid},
                                "alias": "Vector Memory"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "ms",
                                "color": {"mode": "palette-classic"}
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Character Intelligence Health Score",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"authenticity_score\" * \"confidence_score\") FROM \"intelligence_coordination_metrics\" WHERE $timeFilter GROUP BY \"bot\"",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
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
                        },
                        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "System Utilization Rate",
                        "type": "gauge",
                        "targets": [
                            {
                                "expr": "SELECT count(*) FROM \"intelligence_coordination_metrics\" WHERE $timeFilter AND time >= now() - 5m",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "reqps",
                                "min": 0,
                                "max": 100
                            }
                        },
                        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0}
                    },
                    {
                        "id": 4,
                        "title": "Performance Optimization Opportunities",
                        "type": "table",
                        "targets": [
                            {
                                "expr": "SELECT \"bot\", mean(\"coordination_time_ms\") as \"avg_coord_time\", mean(\"authenticity_score\") as \"avg_authenticity\", count(*) as \"requests\" FROM \"intelligence_coordination_metrics\" WHERE $timeFilter GROUP BY \"bot\" ORDER BY \"avg_coord_time\" DESC",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 4}
                    },
                    {
                        "id": 5,
                        "title": "Memory Aging Health Status",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "SELECT mean(\"flagged_ratio\") FROM \"memory_aging_metrics\" WHERE $timeFilter GROUP BY time($__interval), \"bot\" fill(null)",
                                "datasource": {"uid": self.datasource_uid}
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percentunit",
                                "color": {"mode": "palette-classic"}
                            }
                        },
                        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 4}
                    },
                    {
                        "id": 6,
                        "title": "Error Rate & Recovery",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "SELECT count(*) FROM \"conversation_quality\" WHERE $timeFilter AND \"quality_score\" < 0.5 GROUP BY time($__interval) fill(0)",
                                "datasource": {"uid": self.datasource_uid},
                                "alias": "Poor Quality Conversations"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "short",
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "steps": [
                                        {"color": "green", "value": 0},
                                        {"color": "yellow", "value": 5},
                                        {"color": "red", "value": 10}
                                    ]
                                }
                            }
                        },
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    }
                ],
                "time": {"from": "now-4h", "to": "now"},
                "refresh": "30s"
            }
        }

    def generate_all_dashboards(self) -> List[Dict[str, Any]]:
        """Generate all WhisperEngine dashboards"""
        return [
            self.generate_character_performance_dashboard(),
            self.generate_emotion_analysis_dashboard(),
            self.generate_vector_memory_dashboard(),
            self.generate_system_health_dashboard()
        ]

    def export_dashboards_to_files(self, output_dir: str = "dashboards"):
        """Export all dashboards to JSON files"""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        dashboards = [
            ("character_performance", self.generate_character_performance_dashboard()),
            ("emotion_analysis", self.generate_emotion_analysis_dashboard()),
            ("vector_memory", self.generate_vector_memory_dashboard()),
            ("system_health", self.generate_system_health_dashboard())
        ]
        
        for name, dashboard in dashboards:
            filename = f"{output_dir}/whisperengine_{name}_dashboard.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dashboard, f, indent=2)
            print(f"✅ Exported: {filename}")

if __name__ == "__main__":
    generator = WhisperEngineDashboardGenerator()
    generator.export_dashboards_to_files()
    print("🎯 All WhisperEngine Character Intelligence dashboards exported!")