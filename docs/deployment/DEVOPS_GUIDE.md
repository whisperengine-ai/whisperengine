# WhisperEngine DevOps Guide

## 🚀 Overview

This guide covers deployment, monitoring, scaling, and operational procedures for WhisperEngine in production environments. Whether you're running a single instance or managing a distributed deployment, this guide provides the operational knowledge you need.

## 📋 Table of Contents

1. [Docker Build & Registry](#-docker-build--registry)
2. [Deployment Strategies](#-deployment-strategies)
3. [Environment Management](#-environment-management)
4. [Monitoring & Observability](#-monitoring--observability)
5. [Backup & Recovery](#-backup--recovery)
6. [Scaling & Performance](#-scaling--performance)
7. [Security Operations](#-security-operations)
8. [Troubleshooting](#-troubleshooting)
9. [CI/CD Pipeline](#-cicd-pipeline)
10. [Infrastructure as Code](#-infrastructure-as-code)

---

## 🐳 Docker Build & Registry

### Multi-Platform Docker Builds

**Quick Reference:**
```bash
# Single platform (development/testing)
docker buildx build --platform linux/amd64 \
  -f docker/Dockerfile.multi-stage \
  --target production \
  -t whisperengine/whisperengine:dev \
  --push .

# Multi-platform (production)
docker buildx build --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile.multi-stage \
  --target production \
  -t whisperengine/whisperengine:v1.0.0 \
  -t whisperengine/whisperengine:latest \
  --push .

# Local testing (no push)
docker buildx build --platform linux/amd64 \
  -f docker/Dockerfile.multi-stage \
  --target production \
  -t whisperengine/whisperengine:test \
  --load .
```

### Build System Setup

**1. Configure Docker Buildx:**
```bash
# Create builder (one-time setup)
docker buildx create --name whisperengine-builder \
  --driver docker-container \
  --use --bootstrap

# Verify builder
docker buildx inspect whisperengine-builder
```

**2. Registry Authentication:**
```bash
# Docker Hub
docker login

# GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

**3. Build Troubleshooting:**

Common issues and solutions:

```bash
# Clear buildx cache
docker buildx prune -f

# Reset builder
docker buildx rm whisperengine-builder
docker buildx create --name whisperengine-builder --use --bootstrap

# Check build context size
du -sh . | head -1

# Exclude unnecessary files (.dockerignore)
echo "*.pyc" >> .dockerignore
echo "__pycache__" >> .dockerignore
echo ".git" >> .dockerignore
echo "tests/" >> .dockerignore
```

### Build Automation Script

```bash
#!/bin/bash
# build-and-deploy.sh - Production build script

set -euo pipefail

VERSION=${1:-$(git describe --tags --always)}
REGISTRY=${2:-"whisperengine"}
PUSH=${3:-"true"}

echo "🐳 Building WhisperEngine $VERSION"

# Build arguments
BUILD_ARGS=(
  --platform linux/amd64,linux/arm64
  --file docker/Dockerfile.multi-stage
  --target production
  --tag "$REGISTRY/whisperengine:$VERSION"
  --tag "$REGISTRY/whisperengine:latest"
)

if [[ "$PUSH" == "true" ]]; then
  BUILD_ARGS+=(--push)
else
  BUILD_ARGS+=(--load)
fi

# Execute build
docker buildx build "${BUILD_ARGS[@]}" .

echo "✅ Build completed: $REGISTRY/whisperengine:$VERSION"
```

---

## 🚀 Deployment Strategies

### 1. Single Instance Deployment

**Docker Compose Production:**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  whisperengine-bot:
    image: whisperengine/whisperengine:latest
    environment:
      - ENV_MODE=production
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9090/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Deployment Commands:**
```bash
# Deploy production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Rolling update
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps whisperengine-bot

# Health check
curl -f http://localhost:9090/health
```

### 2. Multi-Instance Deployment

**Load Balancer Configuration (nginx):**
```nginx
upstream whisperengine_backend {
    least_conn;
    server whisperengine-1:9090 max_fails=3 fail_timeout=30s;
    server whisperengine-2:9090 max_fails=3 fail_timeout=30s;
    server whisperengine-3:9090 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name whisperengine.yourdomain.com;
    
    location /health {
        proxy_pass http://whisperengine_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}
```

**Docker Swarm Deployment:**
```yaml
# docker-stack.yml
version: '3.8'
services:
  whisperengine-bot:
    image: whisperengine/whisperengine:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    networks:
      - whisperengine-network
```

```bash
# Deploy to swarm
docker stack deploy -c docker-stack.yml whisperengine

# Scale services
docker service scale whisperengine_whisperengine-bot=5

# Update service
docker service update --image whisperengine/whisperengine:v1.1.0 whisperengine_whisperengine-bot
```

### 3. Kubernetes Deployment

**Deployment Manifest:**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whisperengine-bot
  namespace: whisperengine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: whisperengine-bot
  template:
    metadata:
      labels:
        app: whisperengine-bot
    spec:
      containers:
      - name: whisperengine
        image: whisperengine/whisperengine:latest
        ports:
        - containerPort: 9090
        env:
        - name: ENV_MODE
          value: "production"
        - name: POSTGRES_HOST
          value: "postgres-service"
        - name: REDIS_HOST
          value: "redis-service"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 9090
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 9090
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Service & Ingress:**
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: whisperengine-service
spec:
  selector:
    app: whisperengine-bot
  ports:
  - port: 80
    targetPort: 9090
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: whisperengine-ingress
spec:
  rules:
  - host: whisperengine.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: whisperengine-service
            port:
              number: 80
```

**Deployment Commands:**
```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Rolling update
kubectl set image deployment/whisperengine-bot whisperengine=whisperengine/whisperengine:v1.1.0

# Scale deployment
kubectl scale deployment whisperengine-bot --replicas=5

# Check status
kubectl get pods -l app=whisperengine-bot
kubectl logs -l app=whisperengine-bot --tail=100
```

---

## 🌍 Environment Management

### Environment Configuration Matrix

| Environment | Purpose | Database | Scaling | Monitoring |
|-------------|---------|----------|---------|------------|
| Development | Local dev | SQLite | Single | Basic |
| Staging | Testing | PostgreSQL | Single | Enhanced |
| Production | Live | PostgreSQL | Multi | Full |
| DR | Disaster Recovery | PostgreSQL | Single | Full |

### Configuration Management

**Environment-Specific Configs:**
```bash
# development.env
ENV_MODE=development
DEBUG_MODE=true
LOG_LEVEL=DEBUG
USE_SQLITE=true
ENABLE_MEMORY_OPTIMIZATION=false

# staging.env
ENV_MODE=staging
DEBUG_MODE=false
LOG_LEVEL=INFO
USE_POSTGRESQL=true
POSTGRES_HOST=staging-postgres
ENABLE_MEMORY_OPTIMIZATION=true

# production.env
ENV_MODE=production
DEBUG_MODE=false
LOG_LEVEL=INFO
USE_POSTGRESQL=true
POSTGRES_HOST=prod-postgres
ENABLE_MEMORY_OPTIMIZATION=true
```

**Secrets Management:**
```bash
# Using Docker Secrets
echo "your_discord_token" | docker secret create discord_token -
echo "your_postgres_password" | docker secret create postgres_password -

# Using Kubernetes Secrets
kubectl create secret generic whisperengine-secrets \
  --from-literal=discord-token=your_discord_token \
  --from-literal=postgres-password=your_postgres_password

# Using environment variables with external secret management
export DISCORD_BOT_TOKEN=$(vault kv get -field=token secret/discord)
export POSTGRES_PASSWORD=$(vault kv get -field=password secret/postgres)
```

---

## 📊 Monitoring & Observability

### Health Checks

**Application Health Endpoints:**
```python
# Health check implementation
@app.route('/health')
def health_check():
    checks = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {
            'database': check_database_connection(),
            'redis': check_redis_connection(),
            'chromadb': check_chromadb_connection(),
            'discord': check_discord_connection(),
            'memory_usage': get_memory_usage(),
            'response_time': measure_response_time()
        }
    }
    
    status_code = 200 if all(checks['checks'].values()) else 503
    return jsonify(checks), status_code

@app.route('/metrics')
def metrics():
    # Prometheus metrics endpoint
    return generate_prometheus_metrics()
```

**Docker Health Checks:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:9090/health || exit 1
```

### Prometheus Monitoring

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'whisperengine'
    static_configs:
      - targets: ['whisperengine:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

**Key Metrics to Monitor:**
- Response time (95th percentile)
- Error rate (4xx/5xx responses)
- Database connection pool usage
- Memory consumption
- Discord API rate limit usage
- ChromaDB query performance
- Redis cache hit rate

### Grafana Dashboards

**Essential Dashboards:**
1. **Application Overview** - Response times, error rates, throughput
2. **Infrastructure** - CPU, memory, disk, network
3. **Database Performance** - Query times, connection pools, locks
4. **Discord Metrics** - Command usage, guild counts, latency
5. **AI/ML Metrics** - LLM response times, memory operations, embeddings

### Logging Strategy

**Centralized Logging (ELK Stack):**
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    
  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    
  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
```

**Structured Logging:**
```python
import structlog

logger = structlog.get_logger()

# Application logging
logger.info(
    "user_command_processed",
    user_id=user.id,
    guild_id=guild.id,
    command=command_name,
    response_time_ms=response_time,
    success=True
)

# Error logging
logger.error(
    "llm_request_failed",
    user_id=user.id,
    error_type="timeout",
    retry_count=retry_count,
    llm_provider=provider_name
)
```

---

## 💾 Backup & Recovery

### Automated Backup Strategy

**Database Backups:**
```bash
#!/bin/bash
# backup-databases.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL backup
pg_dump -h postgres -U bot_user whisper_engine > "$BACKUP_DIR/postgres_$DATE.sql"

# Redis backup
redis-cli -h redis --rdb > "$BACKUP_DIR/redis_$DATE.rdb"

# ChromaDB backup
tar -czf "$BACKUP_DIR/chromadb_$DATE.tar.gz" /app/chromadb_data

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/" s3://whisperengine-backups/ --recursive --exclude "*" --include "*$DATE*"

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

**Scheduled Backups (cron):**
```bash
# Daily backups at 2 AM
0 2 * * * /opt/whisperengine/scripts/backup-databases.sh >> /var/log/whisperengine-backup.log 2>&1

# Weekly full system backup
0 3 * * 0 /opt/whisperengine/scripts/full-backup.sh >> /var/log/whisperengine-backup.log 2>&1
```

### Disaster Recovery

**Recovery Procedures:**

1. **Database Recovery:**
```bash
# PostgreSQL restore
psql -h postgres -U bot_user whisper_engine < backup_20240916_120000.sql

# Redis restore
redis-cli -h redis --rdb < backup_20240916_120000.rdb

# ChromaDB restore
tar -xzf backup_20240916_120000.tar.gz -C /app/
```

2. **Application Recovery:**
```bash
# Stop services
docker-compose down

# Restore data volumes
docker volume create whisperengine-postgres
docker run --rm -v whisperengine-postgres:/data -v $(pwd)/backups:/backup alpine sh -c "cd /data && tar xzf /backup/postgres_backup.tar.gz"

# Start services
docker-compose up -d
```

3. **Cross-Region Recovery:**
```bash
# Sync from backup region
aws s3 sync s3://whisperengine-backups-us-east-1/ s3://whisperengine-backups-us-west-2/

# Deploy in new region
terraform apply -var region=us-west-2
```

---

## ⚡ Scaling & Performance

### Horizontal Scaling

**Load Balancing Strategies:**
1. **Round Robin** - Simple distribution
2. **Least Connections** - Route to least busy instance
3. **IP Hash** - Sticky sessions based on client IP
4. **Weighted** - Different capacities per instance

**Auto-Scaling (Kubernetes HPA):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: whisperengine-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: whisperengine-bot
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

**Resource Optimization:**
```yaml
# Resource limits and requests
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

**JVM Tuning (if using Java components):**
```bash
JAVA_OPTS="-Xms1g -Xmx2g -XX:+UseG1GC -XX:G1HeapRegionSize=16m"
```

### Database Scaling

**PostgreSQL Optimization:**
```sql
-- Connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';

-- Query optimization
CREATE INDEX CONCURRENTLY idx_user_memories_user_id ON user_memories(user_id);
CREATE INDEX CONCURRENTLY idx_conversations_timestamp ON conversations(created_at);
```

**Redis Optimization:**
```redis
# Memory optimization
CONFIG SET maxmemory 1gb
CONFIG SET maxmemory-policy allkeys-lru

# Persistence tuning
CONFIG SET save "900 1 300 10 60 10000"
```

### Performance Monitoring

**Key Performance Indicators:**
- Response time < 500ms (95th percentile)
- Error rate < 1%
- Memory usage < 80%
- CPU usage < 70%
- Database query time < 100ms
- Cache hit rate > 90%

**Performance Testing:**
```bash
# Load testing with Artillery
npm install -g artillery
artillery run load-test.yml

# Stress testing
ab -n 1000 -c 10 http://localhost:9090/health

# Database performance testing
pgbench -c 10 -j 2 -t 1000 whisper_engine
```

---

## 🔒 Security Operations

### Security Hardening

**Container Security:**
```dockerfile
# Use non-root user
RUN addgroup -g 1001 -S whisperengine && \
    adduser -S whisperengine -G whisperengine -u 1001

USER whisperengine

# Security scanning
RUN apk add --no-cache \
    && rm -rf /var/cache/apk/*
```

**Network Security:**
```yaml
# Docker Compose network isolation
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  whisperengine-bot:
    networks:
      - frontend
      - backend
  
  postgres:
    networks:
      - backend
```

**Secrets Management:**
```bash
# Kubernetes secrets
kubectl create secret generic whisperengine-secrets \
  --from-file=discord-token=discord-token.txt \
  --from-file=postgres-password=postgres-password.txt

# Vault integration
vault kv put secret/whisperengine \
  discord_token=xxx \
  postgres_password=xxx
```

### Security Monitoring

**Log Analysis:**
```bash
# Failed authentication attempts
grep "authentication failed" /var/log/whisperengine/*.log

# Suspicious activity patterns
grep -E "(sql injection|xss|command injection)" /var/log/nginx/access.log

# Rate limiting violations
grep "rate limit exceeded" /var/log/whisperengine/*.log
```

**Security Alerts:**
```python
# Security event monitoring
def monitor_security_events():
    events = [
        'multiple_failed_logins',
        'privilege_escalation_attempt',
        'suspicious_database_queries',
        'unusual_api_usage_patterns'
    ]
    
    for event in events:
        if detect_security_event(event):
            alert_security_team(event)
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

**1. Container Won't Start:**
```bash
# Check logs
docker-compose logs whisperengine-bot

# Common fixes
docker-compose down && docker-compose up -d  # Restart
docker system prune -f  # Clean up resources
docker volume prune  # Clean up volumes
```

**2. Database Connection Issues:**
```bash
# Test database connectivity
docker exec whisperengine-postgres pg_isready

# Check connection string
docker exec whisperengine-bot python -c "import psycopg2; print('Connection OK')"

# Reset database
./bot.sh reset-data prod  # WARNING: Destroys all data
```

**3. Memory Issues:**
```bash
# Check memory usage
docker stats

# Optimize memory settings
export MEMORY_OPTIMIZATION_LEVEL=high
docker-compose restart whisperengine-bot

# Clear caches
./bot.sh clear-cache prod
```

**4. Discord API Issues:**
```bash
# Check Discord connection
curl -H "Authorization: Bot $DISCORD_BOT_TOKEN" https://discord.com/api/v10/users/@me

# Rate limit monitoring
grep "rate limit" /var/log/whisperengine/*.log

# Restart Discord connection
docker-compose restart whisperengine-bot
```

### Debugging Tools

**Application Debugging:**
```bash
# Enable debug mode
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up -d

# Interactive debugging session
docker exec -it whisperengine-bot python -m pdb /app/src/main.py

# Memory profiling
docker exec whisperengine-bot python -m memory_profiler /app/src/main.py
```

**Network Debugging:**
```bash
# Network connectivity
docker exec whisperengine-bot ping postgres
docker exec whisperengine-bot nc -zv redis 6379

# DNS resolution
docker exec whisperengine-bot nslookup postgres
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy WhisperEngine

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        file: docker/Dockerfile.multi-stage
        target: production
        platforms: linux/amd64,linux/arm64
        push: true
        tags: |
          whisperengine/whisperengine:latest
          whisperengine/whisperengine:${{ github.ref_name }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging
    steps:
    - name: Deploy to staging
      run: |
        ssh ${{ secrets.STAGING_HOST }} "
          cd /opt/whisperengine &&
          docker-compose pull &&
          docker-compose up -d
        "

  deploy-production:
    needs: [build-and-push, deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    if: startsWith(github.ref, 'refs/tags/')
    steps:
    - name: Deploy to production
      run: |
        ssh ${{ secrets.PROD_HOST }} "
          cd /opt/whisperengine &&
          docker-compose pull &&
          docker-compose up -d --no-deps whisperengine-bot
        "
```

### Deployment Automation

**Zero-Downtime Deployment:**
```bash
#!/bin/bash
# zero-downtime-deploy.sh

VERSION=$1
OLD_CONTAINER=$(docker ps --format "table {{.Names}}" | grep whisperengine-bot)

# Start new container
docker run -d --name whisperengine-bot-new \
  --network whisperengine-network \
  whisperengine/whisperengine:$VERSION

# Health check new container
for i in {1..30}; do
  if curl -f http://whisperengine-bot-new:9090/health; then
    break
  fi
  sleep 2
done

# Switch traffic
docker exec nginx nginx -s reload

# Stop old container
docker stop $OLD_CONTAINER
docker rm $OLD_CONTAINER

# Rename new container
docker rename whisperengine-bot-new whisperengine-bot
```

---

## 🏗️ Infrastructure as Code

### Terraform Configuration

**main.tf:**
```hcl
provider "aws" {
  region = var.aws_region
}

# VPC and networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "whisperengine-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
}

# ECS Cluster
resource "aws_ecs_cluster" "whisperengine" {
  name = "whisperengine-cluster"
  
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  allocated_storage    = 20
  storage_type         = "gp2"
  engine              = "postgres"
  engine_version      = "15.3"
  instance_class      = "db.t3.micro"
  db_name             = "whisper_engine"
  username            = "bot_user"
  password            = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "redis" {
  name       = "whisperengine-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "whisperengine-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]
}
```

### Ansible Playbooks

**site.yml:**
```yaml
---
- hosts: whisperengine_servers
  become: yes
  vars:
    whisperengine_version: "{{ version | default('latest') }}"
    
  tasks:
    - name: Update system packages
      apt:
        update_cache: yes
        upgrade: dist
        
    - name: Install Docker
      apt:
        name: docker.io
        state: present
        
    - name: Install Docker Compose
      pip:
        name: docker-compose
        state: present
        
    - name: Create whisperengine directory
      file:
        path: /opt/whisperengine
        state: directory
        
    - name: Copy compose files
      template:
        src: "{{ item }}"
        dest: "/opt/whisperengine/{{ item }}"
      loop:
        - docker-compose.yml
        - docker-compose.prod.yml
        - .env
        
    - name: Start WhisperEngine services
      docker_compose:
        project_src: /opt/whisperengine
        files:
          - docker-compose.yml
          - docker-compose.prod.yml
        state: present
        
    - name: Verify services are running
      uri:
        url: http://localhost:9090/health
        method: GET
      retries: 5
      delay: 10
```

### Monitoring Stack (Prometheus + Grafana)

**docker-compose.monitoring.yml:**
```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
      
volumes:
  prometheus_data:
  grafana_data:
```

---

## 📈 Performance Benchmarks

### Target Performance Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Response Time (95th) | < 500ms | > 1s | > 2s |
| Error Rate | < 1% | > 2% | > 5% |
| Memory Usage | < 80% | > 90% | > 95% |
| CPU Usage | < 70% | > 85% | > 95% |
| Database Connections | < 80% | > 90% | > 95% |
| Cache Hit Rate | > 90% | < 85% | < 70% |

### Load Testing

**Artillery Configuration:**
```yaml
# load-test.yml
config:
  target: 'http://localhost:9090'
  phases:
    - duration: 60
      arrivalRate: 10
    - duration: 120
      arrivalRate: 50
    - duration: 60
      arrivalRate: 100

scenarios:
  - name: "Health Check"
    weight: 50
    requests:
      - get:
          url: "/health"
  
  - name: "Status Check"
    weight: 30
    requests:
      - get:
          url: "/status"
          
  - name: "Metrics"
    weight: 20
    requests:
      - get:
          url: "/metrics"
```

---

## 🎯 Best Practices Summary

### Development
- Use infrastructure mode for local development
- Always test builds locally before pushing
- Implement proper health checks
- Use structured logging
- Follow the 12-factor app methodology

### Production
- Use multi-platform Docker builds
- Implement proper monitoring and alerting
- Automate backups and test recovery procedures
- Use secrets management for sensitive data
- Implement proper resource limits

### Security
- Regular security updates
- Use non-root containers
- Implement network segmentation
- Monitor for security events
- Regular vulnerability scanning

### Operations
- Document all procedures
- Automate repetitive tasks
- Monitor key metrics
- Have runbooks for common issues
- Regular disaster recovery testing

---

This DevOps guide provides comprehensive operational knowledge for running WhisperEngine in production. Keep it updated as your infrastructure evolves and new operational procedures are developed.