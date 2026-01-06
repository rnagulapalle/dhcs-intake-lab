# DHCS BHT Multi-Agent AI System

**California Department of Health Care Services**
**Behavioral Health Transformation Initiative**

[![Status](https://img.shields.io/badge/status-production%20ready-green)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![Docker](https://img.shields.io/badge/docker-required-blue)]()
[![License](https://img.shields.io/badge/license-DHCS-blue)]()

---

## 🎯 What is this?

An **AI-powered multi-agent system** to support California's $6.38 billion Behavioral Health Transformation initiative (Proposition 1, AB 531, SB 326). The system provides intelligent assistance for:

- **Crisis Triage** - Real-time crisis assessment and recommendations
- **Policy Q&A** - Instant access to policy documents via RAG
- **BHOATR Reporting** - Automated outcomes and accountability reporting
- **Licensing** - Facility licensing application support
- **Infrastructure** - Prop 1/SB 326 project tracking
- **Compliance** - Integrated Plan verification
- **Analytics** - Population and resource insights

---

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (Mac/Linux/Windows)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **8GB+ RAM** recommended

### Get Running in 5 Minutes

```bash
# 1. Clone repository
git clone <repository-url> dhcs-intake-lab
cd dhcs-intake-lab

# 2. Configure OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 3. Start all services
docker-compose up -d

# 4. Wait 30-60 seconds, then generate synthetic data
docker-compose exec agent-api python /app/generator/populate_all_data.py

# 5. Open dashboard
open http://localhost:8501
```

✅ **Dashboard**: http://localhost:8501
✅ **API Docs**: http://localhost:8000/docs
✅ **Health Check**: http://localhost:8000/health

---

## 📖 Documentation

### 📘 Core Documentation
- **[System Overview](./docs/01-OVERVIEW.md)** - Features, architecture, and background
- **[Quick Start Guide](./docs/02-QUICKSTART.md)** - Detailed setup instructions
- **[Architecture](./docs/03-ARCHITECTURE.md)** - Technical design and patterns
- **[Use Cases](./docs/04-USE-CASES.md)** - 8 specialized use cases explained

### 🚀 Deployment
- **[Local Deployment](./docs/deployment/LOCAL.md)** - Docker Compose for development
- **[AWS Deployment](./docs/deployment/AWS.md)** - Production on AWS ECS/Fargate

### 👨‍💻 Development
- **[Developer Guide](./docs/development/DEVELOPER-GUIDE.md)** - Contributing and dev workflow
- **[API Reference](./docs/development/API.md)** - REST API endpoints
- **[Agent Development](./docs/development/AGENTS.md)** - Create custom agents

### 📚 Complete Documentation
👉 **[Full Documentation Index](./docs/README.md)**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│            Streamlit Dashboard (Port 8501)              │
│         8 Use Cases | Chat Interface | Filters          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           FastAPI Backend (Port 8000)                   │
│           REST API + Agent Orchestration                │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │    ORCHESTRATOR AGENT     │
        │    (LangGraph ReAct)      │
        └─────────────┬─────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌────────┐      ┌──────────┐     ┌─────────┐
│ Triage │      │Knowledge │     │ Query   │
│ Agent  │      │  Agent   │     │ Agent   │
└────┬───┘      └────┬─────┘     └────┬────┘
     │               │                │
     └───────────────┴────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
┌─────────┐   ┌───────────┐   ┌──────────┐
│  Pinot  │   │  OpenAI   │   │ChromaDB  │
│(Analytics)  │  GPT-4o   │   │  (RAG)   │
└─────────┘   └───────────┘   └──────────┘
     ▲
     │
┌────┴─────┐
│  Kafka   │
│(Streaming)
└──────────┘
```

**Key Components**:
- **Multi-Agent System**: LangGraph orchestrator + specialized agents
- **Real-Time Data**: Kafka → Apache Pinot for live analytics
- **RAG**: ChromaDB for semantic policy document search
- **LLM**: OpenAI GPT-4o for natural language understanding

---

## 💡 Use Cases

### 1. Crisis Triage 🚨
Analyze real-time crisis events, assess risk, and recommend interventions.

```
Query: "Show me high-risk cases from the last hour"
AI: Returns prioritized list with risk scores and recommendations
```

### 2. Policy Q&A 📚
Instant answers from 20+ policy documents using RAG.

```
Query: "What are crisis stabilization unit requirements?"
AI: Returns policy text with sources and citations
```

### 3. BHOATR Reporting 📊
Generate quarterly outcome and accountability reports.

```
Query: "Generate Q4 2024 report for Los Angeles County"
AI: Returns comprehensive metrics, trends, and recommendations
```

### 4. Licensing Assistant 📋
Support facility licensing applications.

```
Query: "What documents are needed for CSU license?"
AI: Returns checklist and guidance
```

### 5-8. Additional Use Cases
- **IP Compliance**: Integrated Plan verification
- **Infrastructure**: Project tracking and monitoring
- **Population Analytics**: Demographics and service utilization
- **Resource Allocation**: Optimized resource distribution

👉 **[Full Use Case Documentation](./docs/04-USE-CASES.md)**

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - REST API framework
- **LangGraph** - Multi-agent orchestration
- **OpenAI GPT-4o** - Large language model
- **Python 3.11+** - Core runtime

### Data & Analytics
- **Apache Kafka** - Event streaming
- **Apache Pinot** - Real-time OLAP
- **ChromaDB** - Vector database (RAG)
- **PostgreSQL** - Structured data (optional)

### Frontend
- **Streamlit** - Web dashboard
- **Modern CSS** - Clean, Grok-inspired UI

### Infrastructure
- **Docker / Docker Compose** - Containerization
- **AWS ECS / Fargate** - Production deployment
- **AWS ECR** - Container registry
- **CloudWatch** - Logging and monitoring

---

## 📊 Project Status

### ✅ Completed (v1.0)
- Multi-agent AI system with 8 use cases
- Real-time crisis event streaming (Kafka → Pinot)
- Policy Q&A with RAG (ChromaDB + OpenAI embeddings)
- Modern Streamlit dashboard with Grok-style UI
- Docker Compose local deployment
- AWS ECS deployment support
- Comprehensive synthetic data generators
- API documentation and health checks

### 🚧 In Progress
- Advanced analytics dashboard
- Performance optimization
- Multi-county deployment testing

### 📋 Planned
- Mobile application
- Multi-region deployment
- Integration with existing DHCS systems
- Advanced monitoring and alerting

---

## 🔧 Common Commands

```bash
# Start system
docker-compose up -d

# View logs
docker-compose logs -f agent-api
docker-compose logs -f dashboard

# Generate synthetic data
docker-compose exec agent-api python /app/generator/populate_all_data.py

# Test API
curl http://localhost:8000/health
curl "http://localhost:8000/knowledge/search?query=Prop%201"

# Restart services
docker-compose restart agent-api dashboard

# Stop system
docker-compose down

# Full reset (remove data)
docker-compose down -v
```

---

## 📁 Repository Structure

```
dhcs-intake-lab/
├── agents/                    # AI agents and backend
│   ├── agents/               # Specialized agents (triage, query, etc.)
│   ├── orchestrator/         # LangGraph orchestrator
│   ├── knowledge/            # ChromaDB RAG system
│   ├── api.py                # FastAPI application
│   └── Dockerfile
├── dashboard/                 # Streamlit frontend
│   ├── streamlit_app.py      # Main dashboard
│   └── Dockerfile
├── generator/                 # Synthetic data generators
│   ├── policy_documents_generator.py
│   ├── infrastructure_generator.py
│   ├── licensing_generator.py
│   ├── outcomes_generator.py
│   └── populate_all_data.py
├── pinot/                     # Apache Pinot configuration
│   ├── schema.json
│   └── table-realtime.json
├── deployment/                # Deployment scripts
│   ├── build-and-deploy.sh
│   └── deploy-minimal.sh
├── docs/                      # Documentation
│   ├── 01-OVERVIEW.md
│   ├── 02-QUICKSTART.md
│   ├── 03-ARCHITECTURE.md
│   ├── 04-USE-CASES.md
│   ├── deployment/
│   ├── development/
│   └── guides/
├── docker-compose.yml         # Local development
├── .env.example               # Environment variables template
└── README.md                  # This file
```

---

## 🆘 Troubleshooting

### Services won't start
```bash
# Check Docker resources (need 8GB+ RAM)
# Increase in Docker Desktop → Settings → Resources

# Clear and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Port conflicts
```bash
# Find what's using the port
lsof -i :8000
lsof -i :8501

# Kill the process or change port in docker-compose.yml
```

### API errors
```bash
# Check OpenAI API key is set
docker-compose exec agent-api env | grep OPENAI

# View API logs
docker-compose logs agent-api | tail -50
```

### No data in responses
```bash
# Regenerate synthetic data
docker-compose exec agent-api python /app/generator/populate_all_data.py

# Verify ChromaDB
curl http://localhost:8000/knowledge/search?query=test
```

👉 **[Full Troubleshooting Guide](./docs/guides/TROUBLESHOOTING.md)**

---

## 🤝 Contributing

See [Developer Guide](./docs/development/DEVELOPER-GUIDE.md) for:
- Development environment setup
- Code style and testing guidelines
- Pull request process
- Agent development

---

## 📄 License

This project is developed for the California Department of Health Care Services (DHCS).

---

## 📞 Support

- **Documentation**: [docs/README.md](./docs/README.md)
- **Troubleshooting**: [docs/guides/TROUBLESHOOTING.md](./docs/guides/TROUBLESHOOTING.md)
- **FAQ**: [docs/guides/FAQ.md](./docs/guides/FAQ.md)

---

## 🔗 Related Links

- [Proposition 1 Information](https://www.dhcs.ca.gov/prop1)
- [DHCS Behavioral Health](https://www.dhcs.ca.gov/services/MH/Pages/default.aspx)
- [OpenAI API](https://platform.openai.com/docs)
- [LangGraph](https://python.langchain.com/docs/langgraph)
- [Apache Pinot](https://pinot.apache.org/)
- [Streamlit](https://streamlit.io/)

---

## 🎯 Next Steps

**For New Users**:
1. Read the [Overview](./docs/01-OVERVIEW.md) (5 min)
2. Follow [Quick Start Guide](./docs/02-QUICKSTART.md) (10 min)
3. Try the dashboard at http://localhost:8501

**For Developers**:
1. Review [Architecture](./docs/03-ARCHITECTURE.md)
2. Setup dev environment: [Developer Guide](./docs/development/DEVELOPER-GUIDE.md)
3. Explore [API Reference](./docs/development/API.md)

**For Deployment**:
1. Local: [Docker Compose Guide](./docs/deployment/LOCAL.md)
2. Production: [AWS Deployment Guide](./docs/deployment/AWS.md)

---

**Built for California's Behavioral Health Transformation Initiative**
**Proposition 1 | AB 531 | SB 326**
