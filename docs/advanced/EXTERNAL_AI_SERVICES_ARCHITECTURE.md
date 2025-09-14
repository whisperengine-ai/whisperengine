# External AI Services Architecture

## Overview

For CPU-intensive AI operations like semantic clustering, we can offload processing to dedicated services, keeping the Discord bot responsive and scalable.

## Proposed Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Discord Bot   │    │  AI Gateway     │    │ Semantic        │
│   (Main App)    │───▶│  Service        │───▶│ Clustering      │
│                 │    │                 │    │ Service         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       ▼                       │
        │              ┌─────────────────┐              │
        │              │ Memory Analysis │              │
        │              │ Service         │              │
        │              └─────────────────┘              │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Redis Cache     │    │ Task Queue      │    │ Results Cache   │
│ (Fast Access)   │    │ (Celery/RQ)     │    │ (PostgreSQL)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Service Breakdown

### 1. AI Gateway Service (FastAPI)
- **Purpose**: Route AI requests, manage queues, handle responses
- **Technologies**: FastAPI, Redis, asyncio
- **Deployment**: Lightweight container, scales horizontally

### 2. Semantic Clustering Service
- **Purpose**: Dedicated SentenceTransformers + scikit-learn processing
- **Technologies**: PyTorch, CUDA support, high-memory instances
- **Deployment**: GPU-enabled containers or cloud ML services

### 3. Memory Analysis Service  
- **Purpose**: Graph analysis, pattern detection, importance scoring
- **Technologies**: NetworkX, pandas, specialized ML models
- **Deployment**: CPU-optimized instances

## Implementation Strategies

### Option A: Microservices (Docker Compose)
```yaml
services:
  discord-bot:
    build: ./bot
    depends_on: [ai-gateway, redis]
    
  ai-gateway:
    build: ./ai-gateway
    ports: ["8000:8000"]
    
  semantic-clustering:
    build: ./semantic-clustering  
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '4.0'
          
  memory-analysis:
    build: ./memory-analysis
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
```

### Option B: Cloud AI Services
- **Azure Cognitive Services**: Text Analytics, Custom Models
- **AWS SageMaker**: Custom embeddings, clustering endpoints
- **Google Cloud AI**: AutoML, Vertex AI endpoints
- **OpenAI Embeddings API**: Replace SentenceTransformers

### Option C: Hybrid Approach
- **Local**: Fast operations (< 100ms)
- **External**: Heavy operations (> 1s)
- **Cached**: Previously computed results

## Performance Benefits

1. **Discord Bot Responsiveness**: Never blocked by AI operations
2. **Horizontal Scaling**: Add more AI workers as needed
3. **Resource Optimization**: Right-size each service
4. **Fault Isolation**: AI service failures don't crash Discord bot
5. **Technology Flexibility**: Use best tools for each task

## Implementation Plan

### Phase 1: Async Queue (Immediate)
```python
# In Discord bot
async def trigger_semantic_analysis(user_id, memories):
    task_id = await ai_gateway.submit_clustering_task(user_id, memories)
    return {"status": "queued", "task_id": task_id}

# AI Gateway
@app.post("/cluster/submit")
async def submit_clustering_task(request: ClusteringRequest):
    task_id = redis.enqueue("semantic_clustering", request.dict())
    return {"task_id": task_id}
```

### Phase 2: Real-time Results (Next)
```python
# WebSocket updates when analysis completes
@app.websocket("/results/{task_id}")
async def results_websocket(websocket, task_id):
    while True:
        result = await redis.get_result(task_id)
        if result:
            await websocket.send_json(result)
            break
        await asyncio.sleep(1)
```

### Phase 3: Cloud Integration (Future)
```python
# OpenAI Embeddings API
async def generate_embeddings_cloud(texts):
    response = await openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=texts
    )
    return [item.embedding for item in response.data]
```

## Cost-Benefit Analysis

### Self-Hosted Benefits:
- Complete data control
- No API usage costs
- Customizable models

### Cloud Services Benefits:
- No infrastructure management
- Auto-scaling
- Often faster/better models
- Pay-per-use pricing

### Recommendation:
Start with **Option A (Microservices)** for immediate CPU optimization, then evaluate **Option B (Cloud)** for cost and performance comparison.