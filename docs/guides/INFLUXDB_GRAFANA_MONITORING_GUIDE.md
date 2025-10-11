# WhisperEngine Character Intelligence Monitoring Stack

## 🎯 Complete InfluxDB + Grafana Integration

This document provides comprehensive setup and usage instructions for WhisperEngine's advanced character intelligence monitoring infrastructure.

## 📊 Monitoring Stack Components

### Infrastructure
- **InfluxDB 2.7**: Time-series database for character intelligence metrics
- **Grafana 11.3**: Real-time dashboard visualization and alerting  
- **PostgreSQL 16.4**: Core character and conversation data
- **Qdrant 1.15.4**: Vector memory storage with performance tracking

### Character Intelligence Metrics
- **Enhanced Vector Emotion Analyzer**: RoBERTa-powered emotion analysis performance
- **Vector Memory System**: Qdrant 3D vector search and retrieval metrics
- **Character Graph Manager**: CDL-driven character knowledge performance
- **Intelligence Coordination**: Multi-system orchestration and authenticity scoring

## 🚀 Quick Start

### Complete Setup (Recommended)
```bash
# Complete monitoring stack deployment
./setup_monitoring.sh setup

# Access dashboards
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:8086  # InfluxDB Web UI
```

### Individual Components
```bash
# Generate dashboards only
./setup_monitoring.sh dashboards-only

# Setup monitoring infrastructure only  
./setup_monitoring.sh monitoring-only

# Start character bots with monitoring
./setup_monitoring.sh start
```

## 📈 Available Dashboards

### 1. Character Performance Overview
**URL**: `http://localhost:3000/d/character-performance`

**Key Metrics**:
- Character response times by bot
- Knowledge query success rates  
- Cache hit ratios and optimization
- Authenticity scores and trends
- Intelligence system coordination efficiency

**Use Cases**:
- Monitor overall character bot performance
- Identify slow response patterns
- Track character authenticity consistency
- Optimize caching strategies

### 2. Emotion Analysis Intelligence  
**URL**: `http://localhost:3000/d/emotion-analysis`

**Key Metrics**:
- RoBERTa transformer analysis performance
- Emotion detection confidence scores
- Multi-emotion detection rates
- Primary emotion distribution patterns
- User vs Bot emotional trends
- Inference time vs accuracy correlation

**Use Cases**:
- Monitor RoBERTa emotion analysis accuracy
- Track emotional conversation patterns
- Optimize emotion detection performance
- Analyze user-bot emotional dynamics

### 3. Vector Memory Performance
**URL**: `http://localhost:3000/d/vector-memory`

**Key Metrics**:
- Qdrant query performance by vector type
- Memory retrieval success rates
- Average relevance scores
- 3D named vector system performance (content/emotion/semantic)
- Memory collection efficiency
- Vector type performance comparison

**Use Cases**:
- Optimize vector search performance
- Monitor memory retrieval quality
- Track 3D vector system efficiency
- Identify memory collection bottlenecks

### 4. System Health & Optimization
**URL**: `http://localhost:3000/d/system-health`

**Key Metrics**:
- Overall processing time trends
- Character intelligence health scores
- System utilization rates
- Performance optimization opportunities
- Memory aging health status
- Error rates and recovery patterns

**Use Cases**:
- Monitor overall system health
- Identify optimization opportunities
- Track error patterns and recovery
- Plan capacity and scaling

## 🔧 Management Commands

### Monitoring Stack Control
```bash
# Check status
./setup_monitoring.sh status

# View logs
./setup_monitoring.sh logs grafana
./setup_monitoring.sh logs influxdb

# Stop monitoring stack
./setup_monitoring.sh stop

# Show monitoring information
./setup_monitoring.sh info
```

### Container Management
```bash
# Monitor specific components
docker logs whisperengine-grafana -f
docker logs whisperengine-influxdb -f

# Check container health
docker-compose -f docker-compose.monitoring.yml ps

# Restart individual services
docker-compose -f docker-compose.monitoring.yml restart grafana
```

## 📊 Metrics Collection Details

### InfluxDB Schema

#### Character Graph Performance (`character_graph_performance`)
```
measurement: character_graph_performance
tags: bot, operation, cache_hit
fields: query_time_ms, knowledge_matches
```

#### Intelligence Coordination (`intelligence_coordination_metrics`)  
```
measurement: intelligence_coordination_metrics
tags: bot, context_type, coordination_strategy
fields: systems_used, coordination_time_ms, authenticity_score, confidence_score
```

#### Emotion Analysis Performance (`emotion_analysis_performance`)
```
measurement: emotion_analysis_performance  
tags: bot, user_id, primary_emotion
fields: analysis_time_ms, confidence_score, emotion_count
```

#### Vector Memory Performance (`vector_memory_performance`)
```
measurement: vector_memory_performance
tags: bot, collection_name, vector_type, operation
fields: search_time_ms, memories_found, avg_relevance_score
```

### Grafana Query Examples

#### Average Character Response Time
```flux
from(bucket: "temporal_intelligence")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "character_graph_performance")
  |> filter(fn: (r) => r._field == "query_time_ms")
  |> group(columns: ["bot"])
  |> mean()
```

#### Emotion Analysis Success Rate
```flux
from(bucket: "temporal_intelligence")
  |> range(start: -1h)  
  |> filter(fn: (r) => r._measurement == "emotion_analysis_performance")
  |> filter(fn: (r) => r._field == "confidence_score")
  |> filter(fn: (r) => r._value > 0.7)
  |> group(columns: ["bot"])
  |> count()
```

## 🛠️ Configuration

### Environment Variables (.env.monitoring)
```bash
# InfluxDB Configuration
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=whisperengine_metrics_*
INFLUXDB_ORG=whisperengine
INFLUXDB_BUCKET=temporal_intelligence
INFLUXDB_TOKEN=whisperengine_admin_token_*

# Grafana Configuration  
GRAFANA_USER=admin
GRAFANA_PASSWORD=whisperengine_grafana_*

# Database Configuration
POSTGRES_DB=whisperengine
POSTGRES_USER=whisperengine_user
POSTGRES_PASSWORD=your_secure_password_*
```

### Character Bot Integration
Each character bot automatically records metrics when:
- `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET` environment variables are set
- TemporalIntelligenceClient is initialized
- Character intelligence systems process messages

## 🔍 Validation & Testing

### Automated Validation
```bash
# Complete monitoring stack validation
python3 validate_monitoring_stack.py

# Expected output: 80%+ success rate with detailed metrics validation
```

### Manual Testing
```bash
# Test character bot metrics collection
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello Elena!",
    "context": {"platform": "test"}
  }'

# Check InfluxDB data
curl -H "Authorization: Token $INFLUXDB_TOKEN" \
  "http://localhost:8086/api/v2/query?org=whisperengine" \
  -d 'from(bucket:"temporal_intelligence")|>range(start:-1h)|>limit(n:10)'
```

## 📈 Performance Optimization

### Dashboard Performance
- **Refresh Rates**: 5-30 seconds based on dashboard complexity
- **Time Ranges**: Default 1-4 hours for real-time monitoring
- **Query Optimization**: Use appropriate time windows and sampling

### InfluxDB Optimization
- **Retention Policies**: Configure based on storage requirements
- **Downsampling**: Aggregate older data for long-term storage
- **Index Optimization**: Optimize tag queries for frequently used dimensions

### Grafana Optimization
- **Panel Limits**: Limit data points for complex visualizations
- **Caching**: Enable query result caching for repeated dashboard views
- **Alerting**: Configure alerts for critical character intelligence metrics

## 🚨 Troubleshooting

### Common Issues

#### Grafana Can't Connect to InfluxDB
```bash
# Check InfluxDB health
curl http://localhost:8086/ping

# Verify network connectivity
docker network ls | grep whisperengine

# Check InfluxDB logs
docker logs whisperengine-influxdb
```

#### No Metrics Data in Dashboards
```bash
# Verify character bots are recording metrics
docker logs whisperengine-elena-bot | grep "InfluxDB"

# Check InfluxDB bucket data
curl -H "Authorization: Token $INFLUXDB_TOKEN" \
  "http://localhost:8086/api/v2/buckets?org=whisperengine"
```

#### Dashboard Import Failures
```bash
# Re-import dashboards
./setup_monitoring.sh dashboards-only

# Check Grafana logs
docker logs whisperengine-grafana
```

### Health Check Endpoints
- **Grafana**: `http://localhost:3000/api/health`
- **InfluxDB**: `http://localhost:8086/ping`  
- **Elena Bot**: `http://localhost:9091/health`
- **Gabriel Bot**: `http://localhost:9095/health`
- **Sophia Bot**: `http://localhost:9096/health`

## 🎯 Next Steps

### Advanced Features
1. **Real-time Alerting**: Configure Grafana alerts for critical metrics
2. **Capacity Planning**: Set up long-term trend analysis  
3. **Multi-Bot Comparison**: Cross-character performance analysis
4. **Custom Metrics**: Add domain-specific character intelligence metrics

### Integration Opportunities
1. **Prometheus Integration**: Add Prometheus for infrastructure metrics
2. **Log Aggregation**: ELK stack for comprehensive log analysis
3. **Distributed Tracing**: Jaeger for request flow analysis
4. **Performance Profiling**: Custom profiling for optimization insights

## 📚 References

- **InfluxDB Documentation**: https://docs.influxdata.com/
- **Grafana Documentation**: https://grafana.com/docs/
- **WhisperEngine Architecture**: See `.github/copilot-instructions.md`
- **Character Intelligence Design**: See `MEMORY_INTELLIGENCE_CONVERGENCE_ROADMAP.md`