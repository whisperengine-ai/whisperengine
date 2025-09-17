# Production Monitoring Guide

WhisperEngine includes comprehensive monitoring capabilities for production deployments, providing real-time insights into system health, performance, and user engagement.

## 🏥 Health Monitoring System

### Overview

The WhisperEngine health monitoring system tracks 8 critical components:

1. **System Resources** - CPU, memory, disk usage, and network
2. **LLM Service Connectivity** - API health and response times
3. **Database Health** - PostgreSQL, ChromaDB, Redis performance
4. **Memory System Operations** - Memory retrieval and storage performance
5. **Cache Performance** - Hit rates and cache efficiency
6. **Discord Bot Status** - Connection health and command latency
7. **Background Tasks** - Async job processing and queue health
8. **Security Events** - Authentication and authorization monitoring

### Discord Admin Commands

Monitor your WhisperEngine deployment directly from Discord:

```bash
# Basic health check
!health

# Detailed component analysis
!health detailed

# View recent errors
!errors

# System performance metrics
!performance

# User engagement statistics
!engagement

# Cache performance analysis
!cache

# Memory system diagnostics
!memory status
```

### Health Check Endpoints

WhisperEngine exposes REST endpoints for external monitoring systems:

```bash
# Basic health check (200 OK = healthy)
curl http://localhost:9091/health

# Detailed health information
curl http://localhost:9091/health/detailed

# Prometheus metrics
curl http://localhost:9091/metrics

# Component-specific health
curl http://localhost:9091/health/component/llm
curl http://localhost:9091/health/component/database
curl http://localhost:9091/health/component/memory
```

## 📊 Analytics Dashboard

### Web Dashboard

Enable the optional web dashboard for real-time monitoring:

```bash
# Enable dashboard in .env
ENABLE_WEB_DASHBOARD=true
DASHBOARD_PORT=8080
DASHBOARD_SECRET_KEY=your-secure-random-key

# Access dashboard
# http://localhost:8080/dashboard
```

#### Dashboard Features

- **Real-time Metrics** - Live system performance graphs
- **Error Tracking** - Categorized error logs with trend analysis
- **User Analytics** - Engagement patterns and usage statistics
- **Performance Trends** - Historical performance data and alerts
- **Component Status** - Visual health indicators for all components
- **Alert Management** - Configure and manage system alerts

#### Dashboard Access

```bash
# Get dashboard URL and access token
!dashboard

# Example response:
# Dashboard URL: http://localhost:8080/dashboard
# Access Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
# Valid for: 24 hours
```

### Metrics Collection

WhisperEngine collects comprehensive metrics for monitoring:

#### System Metrics
- CPU usage percentage and load averages
- Memory utilization and garbage collection
- Disk I/O and free space
- Network connectivity and bandwidth

#### Application Metrics
- Response time percentiles (P50, P95, P99)
- Request rate and throughput
- Error rates by category
- Database query performance
- Cache hit/miss ratios

#### Business Metrics
- Active user count
- Conversation length and quality
- Feature usage patterns
- Memory system efficiency

## 🚨 Intelligent Error Tracking

### Error Categorization

WhisperEngine automatically categorizes errors for easier management:

#### Error Types
- **AI Errors** - LLM API failures, model errors, token limits
- **System Errors** - Database connectivity, file I/O, network issues
- **User Errors** - Invalid input, permission denied, rate limiting
- **Network Errors** - API timeouts, connection failures, DNS issues

#### Severity Levels
- **CRITICAL** - System-wide failures requiring immediate attention
- **HIGH** - Component failures affecting user experience
- **MEDIUM** - Degraded performance or partial functionality
- **LOW** - Minor issues or expected edge cases

### Error Pattern Detection

Automated pattern detection identifies recurring issues:

```bash
# View error patterns
!errors patterns

# Example patterns detected:
# Pattern 1: LLM timeout errors (15 occurrences in 1 hour)
# Pattern 2: Database connection pool exhaustion (5 occurrences)
# Pattern 3: Memory allocation failures (3 occurrences)
```

### Error Resolution Tracking

Track the effectiveness of error fixes:

- **Fix Success Rate** - Percentage of issues resolved after fixes
- **Recurrence Detection** - Identification of recurring issues
- **Resolution Time** - Average time to resolve different error types
- **Impact Assessment** - User experience impact of different errors

## 📈 Performance Monitoring

### Response Time Tracking

Monitor response times across all system components:

```bash
# View current response times
!performance response-times

# Historical performance trends
!performance history --period 24h

# Component-specific performance
!performance component llm
!performance component database
!performance component memory
```

### Resource Utilization

Track resource usage for capacity planning:

```bash
# Current resource usage
!performance resources

# Resource trends
!performance resources --period 7d

# Capacity planning recommendations
!performance capacity-planning
```

### Performance Optimization

Built-in performance optimization recommendations:

- **Bottleneck Detection** - Identify performance bottlenecks automatically
- **Scaling Recommendations** - Suggest when to scale resources
- **Configuration Tuning** - Recommend configuration optimizations
- **Cache Optimization** - Suggest cache configuration improvements

## 🔔 Alerting System

### Alert Configuration

Configure alerts for critical system events:

```yaml
# alerts.yaml
alerts:
  system:
    cpu_threshold: 80  # Alert when CPU usage exceeds 80%
    memory_threshold: 90  # Alert when memory usage exceeds 90%
    disk_threshold: 85  # Alert when disk usage exceeds 85%
  
  application:
    error_rate_threshold: 5  # Alert when error rate exceeds 5%
    response_time_threshold: 2000  # Alert when response time exceeds 2s
    
  business:
    user_drop_threshold: 20  # Alert when active users drop by 20%
```

### Alert Channels

Configure multiple alert delivery channels:

```bash
# Discord alerts (admin channel)
ALERT_DISCORD_ENABLED=true
ALERT_DISCORD_WEBHOOK=https://discord.com/api/webhooks/...

# Email alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.company.com
ALERT_EMAIL_TO=admin@company.com

# Slack alerts
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/...

# PagerDuty integration
ALERT_PAGERDUTY_ENABLED=true
ALERT_PAGERDUTY_INTEGRATION_KEY=your-integration-key
```

### Alert Management

Manage alerts through Discord commands:

```bash
# View active alerts
!alerts

# Acknowledge alert
!alerts ack <alert_id>

# Silence alert temporarily
!alerts silence <alert_id> --duration 1h

# View alert history
!alerts history --period 24h
```

## 📊 Integration with External Systems

### Prometheus Integration

Export metrics to Prometheus for advanced monitoring:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'whisperengine'
    static_configs:
      - targets: ['localhost:9091']
    metrics_path: /metrics
    scrape_interval: 30s
```

### Grafana Dashboards

Import pre-built Grafana dashboards:

```bash
# Download dashboard configuration
curl -L https://github.com/whisperengine-ai/whisperengine/raw/main/monitoring/grafana-dashboard.json

# Import to Grafana
# Dashboard ID: 12345 (available on grafana.com)
```

### ELK Stack Integration

Send logs to Elasticsearch for advanced analysis:

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  paths:
    - /var/log/whisperengine/*.log
  fields:
    service: whisperengine
    environment: production

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

### SIEM Integration

Export security events to SIEM systems:

```bash
# Splunk integration
curl -X POST "https://splunk.company.com:8088/services/collector" \
  -H "Authorization: Splunk $SPLUNK_TOKEN" \
  -d @security-events.json

# ArcSight integration
logger -p local0.info -t whisperengine "$(cat security-events.json)"
```

## 🔧 Configuration

### Environment Variables

Configure monitoring features through environment variables:

```bash
# Health monitoring
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_PORT=9091
HEALTH_CHECK_INTERVAL=30  # seconds

# Performance monitoring
PERFORMANCE_MONITORING_ENABLED=true
PERFORMANCE_METRICS_RETENTION=7d
PERFORMANCE_SAMPLING_RATE=1.0

# Error tracking
ERROR_TRACKING_ENABLED=true
ERROR_PATTERN_DETECTION=true
ERROR_RETENTION_PERIOD=30d

# Web dashboard
ENABLE_WEB_DASHBOARD=true
DASHBOARD_PORT=8080
DASHBOARD_SECRET_KEY=your-secure-key
DASHBOARD_SESSION_TIMEOUT=24h

# Alerting
ALERTING_ENABLED=true
ALERT_EVALUATION_INTERVAL=60s
ALERT_NOTIFICATION_TIMEOUT=30s
```

### Advanced Configuration

Fine-tune monitoring behavior:

```yaml
# monitoring.yaml
monitoring:
  health_checks:
    timeout: 30s
    retry_attempts: 3
    retry_delay: 5s
    
  metrics:
    collection_interval: 15s
    retention_period: 30d
    high_resolution_period: 6h
    
  alerting:
    evaluation_interval: 60s
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 12h
    
  dashboard:
    refresh_interval: 30s
    data_retention: 24h
    max_concurrent_users: 10
```

## 🔍 Troubleshooting

### Common Issues

#### Dashboard Not Loading
```bash
# Check if dashboard is enabled
!config get ENABLE_WEB_DASHBOARD

# Verify port is accessible
curl http://localhost:8080/health

# Check dashboard logs
!logs dashboard --lines 50
```

#### Metrics Not Collecting
```bash
# Verify health check endpoint
curl http://localhost:9091/health

# Check monitoring process status
!health detailed

# Review monitoring configuration
!config monitoring
```

#### Alerts Not Firing
```bash
# Test alert configuration
!alerts test

# Verify alert thresholds
!alerts config

# Check alert channel connectivity
!alerts test-channels
```

### Performance Optimization

#### High Memory Usage
```bash
# Analyze memory usage patterns
!performance memory-analysis

# Optimize memory settings
!config set MEMORY_OPTIMIZATION_ENABLED true
!config set MEMORY_CLEANUP_INTERVAL 300
```

#### Slow Response Times
```bash
# Identify bottlenecks
!performance bottlenecks

# Optimize database connections
!config set DATABASE_POOL_SIZE 20
!config set DATABASE_TIMEOUT 30
```

### Log Analysis

Access detailed logs for troubleshooting:

```bash
# View recent logs
!logs --lines 100

# Filter by component
!logs component llm --level error

# Search logs
!logs search "timeout" --since 1h

# Export logs
!logs export --format json --output /tmp/logs.json
```

## 📚 Additional Resources

- **[Metrics Reference](METRICS_REFERENCE.md)** - Complete list of available metrics
- **[Alert Runbooks](ALERT_RUNBOOKS.md)** - Step-by-step troubleshooting guides
- **[Performance Tuning](PERFORMANCE_TUNING.md)** - Optimization best practices
- **[Dashboard Customization](DASHBOARD_CUSTOMIZATION.md)** - Custom dashboard creation

---

For monitoring support, join our [Operations Discussion](https://github.com/whisperengine-ai/whisperengine/discussions/categories/operations) or contact support@whisperengine.ai.