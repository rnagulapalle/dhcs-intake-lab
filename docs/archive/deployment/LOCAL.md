# Local Deployment Guide

**Document Version**: 1.0
**Last Updated**: January 2026
**Target Environment**: Docker Compose (Local Development)

---

## Overview

This guide covers running the DHCS BHT Multi-Agent System locally using Docker Compose for development and testing.

For production deployment, see [AWS Deployment Guide](./AWS.md).

---

## Quick Start

```bash
# 1. Clone repository
git clone <repository-url> dhcs-intake-lab
cd dhcs-intake-lab

# 2. Create .env file
echo "OPENAI_API_KEY=your-key-here" > .env

# 3. Start services
docker-compose up -d

# 4. Generate data
docker-compose exec agent-api python /app/generator/populate_all_data.py

# 5. Access dashboard
open http://localhost:8501
```

---

## Docker Compose Architecture

### Services Overview

| Service | Purpose | Port | Required |
|---------|---------|------|----------|
| `agent-api` | FastAPI backend + agents | 8000 | Yes |
| `dashboard` | Streamlit UI | 8501 | Yes |
| `kafka` | Event streaming | 29092 | Optional |
| `zookeeper` | Kafka coordination | 2181 | Optional |
| `pinot-controller` | Pinot management | 9000 | Optional |
| `pinot-broker` | Pinot SQL queries | 8099 | Optional |
| `pinot-server` | Pinot data storage | 8098 | Optional |
| `generator` | Synthetic data | - | Optional |

### Minimal Setup (API + Dashboard Only)

If you only need the chat interface without real-time streaming:

```yaml
# docker-compose.minimal.yml
version: '3.8'
services:
  agent-api:
    build:
      context: .
      dockerfile: agents/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./agents:/app/agents
      - chroma_data:/data/chroma

  dashboard:
    build:
      context: .
      dockerfile: dashboard/Dockerfile
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://agent-api:8000
    depends_on:
      - agent-api

volumes:
  chroma_data:
```

Start minimal setup:
```bash
docker-compose -f docker-compose.minimal.yml up -d
```

---

## Configuration

### Environment Variables

Create `.env` file:
```bash
# Required
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Optional - Kafka/Pinot
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
PINOT_BROKER_URL=http://pinot-broker:8099

# Optional - Logging
LOG_LEVEL=INFO
```

### Volume Mounts

For development with hot reloading:
```yaml
volumes:
  - ./agents:/app/agents  # Live code changes
  - ./dashboard:/app/dashboard
  - chroma_data:/data/chroma  # Persistent vector DB
```

---

## Common Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d agent-api dashboard

# View logs
docker-compose logs -f agent-api
docker-compose logs --tail=50 dashboard

# Restart service
docker-compose restart agent-api

# Stop all services
docker-compose down

# Stop and remove volumes (full reset)
docker-compose down -v
```

### Data Generation

```bash
# Generate all synthetic data
docker-compose exec agent-api python /app/generator/populate_all_data.py

# Generate specific data types
docker-compose exec agent-api python /app/generator/policy_documents_generator.py
docker-compose exec agent-api python /app/generator/infrastructure_generator.py
docker-compose exec agent-api python /app/generator/licensing_generator.py
docker-compose exec agent-api python /app/generator/outcomes_generator.py
```

### Database Operations

```bash
# Check ChromaDB collections
docker-compose exec agent-api python -c "
from agents.knowledge.knowledge_base import DHCSKnowledgeBase
kb = DHCSKnowledgeBase()
print(f'Documents: {kb.collection.count()}')
"

# Query Pinot
docker-compose exec pinot-broker curl -X POST \
  http://localhost:8099/query/sql \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT COUNT(*) FROM dhcs_crisis_intake"}'

# Check Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Testing

```bash
# Test API health
curl http://localhost:8000/health

# Test knowledge search
curl "http://localhost:8000/knowledge/search?query=crisis%20stabilization&n_results=2"

# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are Prop 1 requirements?"}'
```

---

## Troubleshooting

### Port Conflicts

If ports are already in use:
```bash
# Find process using port
lsof -i :8000
lsof -i :8501

# Kill process or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

### Memory Issues

Docker needs at least 8GB RAM:
1. Open Docker Desktop
2. Go to Settings → Resources
3. Increase Memory to 8GB or more
4. Click "Apply & Restart"

### Build Failures

Clear Docker cache:
```bash
# Remove old images
docker-compose down --rmi all

# Clear build cache
docker builder prune -a

# Rebuild from scratch
docker-compose build --no-cache
```

### Service Won't Start

Check logs for errors:
```bash
# View startup logs
docker-compose logs agent-api | tail -50

# Common issues:
# - Missing OPENAI_API_KEY
# - Port already in use
# - Insufficient memory
# - Network conflicts
```

### ChromaDB Issues

Reset vector database:
```bash
# Stop services
docker-compose down

# Remove ChromaDB volume
docker volume rm dhcs-intake-lab_chroma_data

# Restart and regenerate data
docker-compose up -d
docker-compose exec agent-api python /app/generator/populate_all_data.py
```

---

## Development Workflow

### Hot Reloading

Both API and Dashboard support hot reloading with volume mounts:

```bash
# Edit code in ./agents or ./dashboard
# Changes are automatically reflected

# API: Uses uvicorn --reload
# Dashboard: Uses streamlit with watch mode
```

### Adding New Agents

1. Create agent file: `agents/agents/my_agent.py`
2. Register in orchestrator: `agents/orchestrator/orchestrator.py`
3. Add endpoint in API: `agents/api.py`
4. Restart API: `docker-compose restart agent-api`

### Testing Changes

```bash
# Run Python tests in container
docker-compose exec agent-api pytest tests/

# Run linter
docker-compose exec agent-api flake8 agents/

# Format code
docker-compose exec agent-api black agents/
```

---

## Performance Tuning

### Resource Limits

Add resource limits to services:
```yaml
services:
  agent-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Scaling Services

Run multiple instances:
```bash
# Scale API to 3 instances
docker-compose up -d --scale agent-api=3

# Add load balancer (nginx) in front
```

---

## Next Steps

- [Architecture Documentation](../03-ARCHITECTURE.md)
- [API Reference](../development/API.md)
- [Agent Development Guide](../development/AGENTS.md)
- [Deploy to AWS](./AWS.md)

---

## Quick Reference

### Useful URLs
- Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/health
- Pinot Console: http://localhost:9000
- Kafka Manager: http://localhost:29092

### Common Issues
| Issue | Solution |
|-------|----------|
| Port in use | Change port in docker-compose.yml |
| Out of memory | Increase Docker RAM to 8GB+ |
| API errors | Check OPENAI_API_KEY is set |
| No data | Run populate_all_data.py |
| Build fails | Clear cache: `docker builder prune -a` |
