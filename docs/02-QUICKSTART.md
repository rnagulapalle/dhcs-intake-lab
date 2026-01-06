# Quick Start Guide

Get the DHCS BHT Multi-Agent System running locally in 5 minutes.

---

## Prerequisites

### Required Software
- **Docker Desktop** (Mac/Linux/Windows)
- **Docker Compose** v2+
- **curl** (for testing)
- **git** (to clone repository)

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **CPU**: 4 cores recommended

### Verify Installation
```bash
docker --version        # Should be 20.10+
docker compose version  # Should be v2.0+
curl --version
```

---

## Step 1: Clone and Setup

```bash
# Clone the repository
cd ~/
git clone <repository-url> dhcs-intake-lab
cd dhcs-intake-lab

# Verify files
ls -la
# Should see: docker-compose.yml, agents/, dashboard/, generator/, etc.
```

---

## Step 2: Configure Environment

### Option A: Use OpenAI API (Recommended)
```bash
# Create .env file
cat > .env << 'EOF'
OPENAI_API_KEY=your-openai-api-key-here
EOF
```

Get your OpenAI API key from: https://platform.openai.com/api-keys

### Option B: Use Local LLM (Optional)
```bash
# For local deployment without OpenAI
# See docs/guides/LOCAL-LLM.md for details
```

---

## Step 3: Start the System

```bash
# Start all services
docker-compose up -d

# Wait 30-60 seconds for services to start
docker-compose ps
```

### Expected Output
```
NAME                    STATUS              PORTS
agent-api               Up                  8000:8000
dashboard               Up                  8501:8501
generator               Up
kafka                   Up (healthy)        29092:29092
pinot-broker            Up                  8099:8099
pinot-controller        Up                  9000:9000
pinot-server            Up                  8098:8098
zookeeper               Up (healthy)        2181:2181
```

---

## Step 4: Generate Synthetic Data

```bash
# Run the data generation script
docker-compose exec agent-api python /app/generator/populate_all_data.py
```

This generates:
- 20+ policy documents (ChromaDB)
- 100 infrastructure projects
- 50 licensing applications
- 40 BHOATR quarterly reports
- Real-time crisis events (streaming to Kafka/Pinot)

**Expected Output:**
```
✓ Generated 20 policy documents
✓ Generated 100 infrastructure projects
✓ Generated 50 licensing applications
✓ Generated 40 BHOATR reports
✓ Vector database populated successfully
```

---

## Step 5: Access the Dashboard

Open your browser and navigate to:

**Dashboard URL**: http://localhost:8501

You should see the DHCS BHT Platform interface with:
- Left panel: 8 use cases
- Center panel: Chat interface
- Right panel: Filters and sample queries

---

## Step 6: Test the System

### Test 1: Policy Q&A
1. Select **"Policy Q&A"** from the left panel
2. Click sample query: **"What are crisis stabilization unit requirements?"**
3. Wait 5-10 seconds for AI response
4. Should see policy documents with sources

### Test 2: Crisis Triage
1. Select **"Crisis Triage"** from the left panel
2. Type: **"Show me high-risk cases from the last hour"**
3. Should see real-time crisis event analysis

### Test 3: BHOATR Reporting
1. Select **"BHOATR Reporting"**
2. Click: **"Generate summary report for Los Angeles"**
3. Should see metrics and analytics

---

## Verification Checklist

### ✅ Services Running
```bash
# Check all services are up
docker-compose ps

# Check logs for errors
docker-compose logs agent-api | tail -20
docker-compose logs dashboard | tail -20
```

### ✅ API Health
```bash
# Test API endpoint
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test knowledge base
curl "http://localhost:8000/knowledge/search?query=Prop%201&n_results=2"
# Should return policy documents
```

### ✅ Pinot Data
```bash
# Check Pinot has data
curl -X POST http://localhost:8099/query/sql \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT COUNT(*) FROM dhcs_crisis_intake"}'
# Should show event count > 0
```

### ✅ Dashboard Access
- Open http://localhost:8501
- Should load without errors
- Can switch between use cases
- Sample queries work

---

## Common Issues

### Issue: Services not starting
```bash
# Check Docker resources
docker system df

# Increase Docker memory to 8GB+ in Docker Desktop settings
# Restart Docker and try again
docker-compose down
docker-compose up -d
```

### Issue: Port already in use
```bash
# Check what's using port 8000 or 8501
lsof -i :8000
lsof -i :8501

# Kill process or change port in docker-compose.yml
```

### Issue: OpenAI API errors
```bash
# Verify API key is set
docker-compose exec agent-api env | grep OPENAI

# Check API key is valid at platform.openai.com
```

### Issue: No data in responses
```bash
# Re-run data generation
docker-compose exec agent-api python /app/generator/populate_all_data.py

# Check vector database
curl http://localhost:8000/knowledge/search?query=test
```

---

## Next Steps

### Learn More
- [Architecture Documentation](./03-ARCHITECTURE.md) - Understand system design
- [Use Cases Guide](./04-USE-CASES.md) - Detailed use case documentation
- [API Reference](./development/API.md) - REST API endpoints

### Customize
- [Configuration Guide](./deployment/CONFIGURATION.md) - Environment variables
- [Agent Development](./development/AGENTS.md) - Create custom agents
- [Data Generators](./development/DATA-GENERATORS.md) - Customize synthetic data

### Deploy
- [AWS Deployment](./deployment/AWS.md) - Production deployment guide
- [Kubernetes](./deployment/KUBERNETES.md) - K8s deployment (optional)

---

## Shutdown

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (reset everything)
docker-compose down -v
```

---

## Getting Help

- Check [Troubleshooting Guide](./guides/TROUBLESHOOTING.md)
- Review [FAQ](./guides/FAQ.md)
- Contact development team

---

**Congratulations!** Your DHCS BHT Multi-Agent System is now running locally.
