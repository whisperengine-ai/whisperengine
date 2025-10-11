# LM Studio Docker Integration Gui### Environment Variables (Set in docker-compose.synthetic.yml)
- `LLM_CLIENT_TYPE=lmstudio` - Use LM Studio client
- `LLM_CHAT_API_URL=http://host.docker.internal:1234/v1` - Docker access to host LM Studio
- `LLM_CHAT_MODEL=local-model` - Generic name (actual model set in LM Studio)
- `SYNTHETIC_USE_LLM=true` - Enable LLM-enhanced generation
- `LLM_MAX_TOKENS_CHAT=1024` - Token limit for generation

**Model Flexibility**: The configuration uses `local-model` as a generic name. You can switch between any models in LM Studio (Mistral Nemo, Qwen 4B, etc.) without rebuilding containers! Overview
WhisperEngine synthetic conversation generation now supports local LM Studio integration with full Docker containerization. This setup allows you to generate high-quality synthetic conversations using any local model you load in LM Studio while running the entire system in containers.

## Quick Start

### 1. Start LM Studio
```bash
# Make sure LM Studio is running on localhost:1234
# Load any compatible model (mistral-nemo, qwen-4b, etc.)
# Verify server is accessible at http://127.0.0.1:1234/v1
```

### 2. Test Docker Integration
```bash
# Run the complete Docker integration test
./run_synthetic_docker_test.sh
```

### 3. Generate Synthetic Conversations
```bash
# Start the synthetic generation system
docker-compose -f docker-compose.synthetic.yml up --build -d

# View generation logs
docker-compose -f docker-compose.synthetic.yml logs -f synthetic-generator

# View validation logs  
docker-compose -f docker-compose.synthetic.yml logs -f synthetic-validator
```

## Configuration Details

### Environment Variables (Set in docker-compose.synthetic.yml)
- `LLM_CLIENT_TYPE=lmstudio` - Use LM Studio client
- `LLM_CHAT_API_URL=http://host.docker.internal:1234/v1` - Docker access to host LM Studio
- `LLM_CHAT_MODEL=liquid/lfm2-1.2b` - Your loaded model
- `SYNTHETIC_USE_LLM=true` - Enable LLM-enhanced generation
- `LLM_MAX_TOKENS_CHAT=1024` - Token limit for generation

### Bot Endpoints
The system is configured to test against WhisperEngine bots running on standard ports:
- Elena: :9091, Marcus: :9092, Ryan: :9093, Dream: :9094
- Gabriel: :9095, Sophia: :9096, Jake: :9097
- Dotty: :9098, Aetheris: :9099, Aethys: :3007

### File Structure
```
synthetic_conversation_generator.py  # Enhanced LLM-driven generator
synthetic_validation_metrics.py     # Quality metrics validator
test_docker_lmstudio.py             # Connection test script
Dockerfile.synthetic                # Container configuration
docker-compose.synthetic.yml        # Full service orchestration
requirements-synthetic.txt          # Dependencies including LLM client
```

## Key Features

### LLM-Enhanced Generation
- **Contextual Conversation Flow**: LLM generates realistic conversation progression
- **Character-Aware Openers**: First messages that match bot personalities  
- **Dynamic Follow-ups**: Responses that build on conversation history
- **Quality Improvement**: Significantly more natural than template-based generation

### Docker Integration Benefits
- **Isolated Environment**: Clean testing environment separate from main WhisperEngine
- **Host LM Studio Access**: Containers can access your local LM Studio server
- **Volume Persistence**: Generated conversations saved to host filesystem
- **Health Monitoring**: Built-in container health checks
- **InfluxDB Integration**: Metrics collection for performance analysis

### Sync LLM Calls
The system uses synchronous LLM calls to avoid async compatibility issues:
```python
def _llm_generate_sync(self, prompt):
    """Use sync LLM calls to avoid async issues"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        response = loop.run_until_complete(self.llm_client.generate_response(prompt))
        return response
    finally:
        loop.close()
```

## Troubleshooting

### Connection Issues
```bash
# Test LM Studio connectivity
curl http://127.0.0.1:1234/v1/models

# Test Docker container connectivity  
docker run --rm whisperengine-synthetic:latest python test_docker_lmstudio.py
```

### View Container Logs
```bash
# Generator logs
docker-compose -f docker-compose.synthetic.yml logs synthetic-generator

# Validator logs  
docker-compose -f docker-compose.synthetic.yml logs synthetic-validator

# All logs
docker-compose -f docker-compose.synthetic.yml logs
```

### Stop Services
```bash
# Stop all synthetic services
docker-compose -f docker-compose.synthetic.yml down

# Force rebuild
docker-compose -f docker-compose.synthetic.yml up --build --force-recreate
```

## Quality Validation

The system includes automatic quality validation:
- **Conversation Coherence**: LLM-generated flow analysis
- **Character Consistency**: Personality adherence metrics
- **Response Quality**: Content quality scoring
- **InfluxDB Storage**: Metrics stored for trend analysis

Generated conversations are stored in `./synthetic_conversations/` with comprehensive metadata including LLM-enhanced quality scores.

## Next Steps

1. **Monitor Quality**: Check InfluxDB dashboards for quality trends
2. **Adjust Models**: Try different LM Studio models for comparison
3. **Scale Testing**: Generate larger conversation datasets
4. **Integration**: Use synthetic data for WhisperEngine testing and validation