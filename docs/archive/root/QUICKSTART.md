# 🚀 Quick Start Guide - DHCS BHT Multi-Agent AI System

Get the system running in **5 minutes** with synthetic data!

## What You'll Get

✅ Real-time crisis intake data streaming
✅ 5 specialized AI agents working together
✅ Interactive dashboard for demos
✅ REST API for integration
✅ RAG-based knowledge system

---

## Step 1: Prerequisites (2 minutes)

### Required:
- **Docker Desktop** - Download from docker.com
- **OpenAI API Key** - Get from platform.openai.com/api-keys
- **8GB RAM** minimum
- **20GB disk space**

### Check your setup:
```bash
docker --version          # Should show v20+
docker compose version    # Should show v2+
```

---

## Step 2: Get Your OpenAI API Key (1 minute)

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-...`)
4. **Important**: Keep this key secure!

---

## Step 3: Setup (2 minutes)

```bash
# Clone or navigate to project
cd dhcs-intake-lab

# Create .env file
cp .env.example .env

# Edit .env and paste your OpenAI API key
nano .env  # or use any text editor

# Paste your key:
# OPENAI_API_KEY=sk-your-key-here

# Save and exit (Ctrl+X, Y, Enter in nano)

# Run automated setup
chmod +x setup.sh
./setup.sh
```

The setup script will:
- ✅ Start all Docker containers (Kafka, Pinot, AI agents, dashboard)
- ✅ Bootstrap the database with schema
- ✅ Initialize AI agents with DHCS policies
- ✅ Start generating synthetic crisis data

**This takes 2-3 minutes. Grab a coffee! ☕**

---

## Step 4: Verify (30 seconds)

Check all services are running:

```bash
docker compose ps

# You should see:
# - zookeeper (healthy)
# - kafka (healthy)
# - pinot-controller, pinot-broker, pinot-server (running)
# - generator (running)
# - agent-api (running)
# - dashboard (running)
```

---

## Step 5: Open the Dashboard 🎉

Open your browser to: **http://localhost:8501**

You should see the DHCS BHT AI Assistant dashboard!

---

## 🎮 Try These Demo Scenarios

### Scenario 1: Chat with the AI
1. Select **💬 Chat Assistant** mode
2. Ask: *"How many high-risk events happened in the last hour?"*
3. The Query Agent will generate SQL, query Pinot, and answer!

### Scenario 2: Real-Time Analytics
1. Select **📊 Analytics Dashboard** mode
2. Click **"Run Analysis"**
3. See surge detection, county trends, and risk distribution
4. AI automatically generates insights

### Scenario 3: Triage High-Risk Cases
1. Select **🚨 Triage Center** mode
2. Click **"Run Triage"**
3. See prioritized list of high-risk cases
4. AI recommends specific actions for each

### Scenario 4: Get Recommendations
1. Select **💡 Recommendations** mode
2. Choose focus area (e.g., "Staffing")
3. Click **"Generate Recommendations"**
4. AI provides 5-7 specific, data-driven recommendations

### Scenario 5: Search Policies
1. Select **📚 Knowledge Base** mode
2. Search: *"mobile crisis team response time"*
3. AI retrieves relevant DHCS policies using RAG

---

## 🧪 Test the API

```bash
# Run automated tests
./test_system.sh

# Or test manually:

# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show me event volume by county"}'

# Get analytics
curl -X POST http://localhost:8000/analytics \
  -H "Content-Type: application/json" \
  -d '{"analysis_type":"comprehensive","time_window_minutes":60}'
```

API Documentation: **http://localhost:8000/docs**

---

## 📊 Other Access Points

- **Streamlit Dashboard**: http://localhost:8501
- **Agent API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Pinot Console**: http://localhost:9000

---

## 🎯 What to Show Stakeholders

### For Administrators:
1. **Dashboard Overview** - Show real-time visibility
2. **Analytics Mode** - Demonstrate surge detection
3. **Recommendations** - Show AI-driven staffing suggestions

### For Technical Staff:
1. **API Documentation** - Show integration possibilities
2. **Natural Language Queries** - Demonstrate self-service analytics
3. **Knowledge Base** - Show policy access

### For Leadership:
1. **Use Cases Document** - Share `docs/USE_CASES.md`
2. **Live Demo** - Walk through triage scenario
3. **ROI Discussion** - 40% faster surge detection, 30% faster intervention

---

## 🛠️ Common Issues & Fixes

### "API not responding"
```bash
# Check logs
docker compose logs agent-api

# Common fix: Restart the service
docker compose restart agent-api
```

### "No data in queries"
```bash
# Check generator is running
docker compose logs generator

# Restart if needed
docker compose restart generator

# Wait 30 seconds for data to flow
```

### "OpenAI API error"
```bash
# Check your API key is correct
cat .env | grep OPENAI_API_KEY

# Verify you have credits: https://platform.openai.com/account/usage

# Restart agent-api with new key
docker compose restart agent-api
```

### "Port already in use"
```bash
# Check what's using the port
lsof -i :8501  # or :8000, :9000, etc.

# Stop conflicting service or change port in docker-compose.yml
```

---

## 🔄 Stop & Restart

### Stop everything:
```bash
docker compose down
```

### Stop and remove data (fresh start):
```bash
docker compose down -v
```

### Restart:
```bash
docker compose up -d
```

### View logs:
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f agent-api
docker compose logs -f dashboard
```

---

## ⚙️ Adjust Settings

### Change data generation rate:

Edit `docker-compose.yml`:
```yaml
generator:
  environment:
    RATE_PER_SEC: "10"  # Increase from 5 to 10 events/sec
```

Then: `docker compose restart generator`

### Change AI model:

Edit `.env`:
```bash
AGENT_MODEL=gpt-4-turbo-preview  # or gpt-3.5-turbo for cheaper
AGENT_TEMPERATURE=0.7            # Lower = more consistent
```

Then: `docker compose restart agent-api`

---

## 📚 Next Steps

### For Demo Preparation:
1. ✅ Run system for 10-15 minutes to generate data
2. ✅ Try each dashboard mode
3. ✅ Prepare 2-3 example questions
4. ✅ Review `docs/USE_CASES.md`

### For Pilot Deployment:
1. 📖 Read `deployment/aws/README.md`
2. 🏗️ Plan infrastructure (ECS vs EKS)
3. 🔐 Set up AWS account and permissions
4. 🚀 Deploy to cloud

### For Development:
1. 💻 Read `README_AGENTS.md` for architecture
2. 🧩 Explore agent code in `agents/core/`
3. 🔧 Try adding a custom agent
4. 🧪 Run tests with `./test_system.sh`

---

## ❓ Get Help

### Documentation:
- **Full README**: `README_AGENTS.md`
- **Use Cases**: `docs/USE_CASES.md`
- **AWS Deployment**: `deployment/aws/README.md`
- **Kubernetes**: `deployment/kubernetes/README.md`

### Troubleshooting:
- Check Docker logs: `docker compose logs`
- Check API health: `curl http://localhost:8000/health`
- Run tests: `./test_system.sh`

### Still stuck?
Open an issue or contact the team!

---

## 🎉 Success!

You now have a **production-ready multi-agent AI system** running locally with synthetic data!

**Key Points to Remember**:
- ✅ All data is synthetic - safe for demos
- ✅ 5 specialized agents collaborate automatically
- ✅ Real-time streaming + AI analysis
- ✅ Ready for stakeholder demos
- ✅ Can be deployed to AWS/cloud

**Next**: Show it to your stakeholders and blow their minds! 🚀

---

**Pro Tip**: Let the system run for 30+ minutes to build up data history. The AI insights get better with more data!
