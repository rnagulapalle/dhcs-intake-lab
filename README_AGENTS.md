# DHCS BHT Multi-Agent AI System

**Behavioral Health Treatment Crisis Intake Intelligence System**

## 🎯 Project Overview

This project demonstrates how **multi-agent AI systems** can transform behavioral health crisis intake operations for California DHCS (Department of Health Care Services). Built with synthetic data, it provides a safe, demo-ready environment to show stakeholders how AI can improve crisis response, save lives, and support staff.

### Key Innovation
A **multi-agent system** where specialized AI agents collaborate to:
- Answer complex questions about crisis data (Query Agent)
- Detect trends and anomalies (Analytics Agent)
- Prioritize high-risk cases (Triage Agent)
- Provide operational recommendations (Recommendations Agent)
- Access policy knowledge (Knowledge Agent via RAG)
- Orchestrate between agents intelligently (Orchestrator)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                       │
│                     (User Interface)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│                  (REST API Endpoints)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  LangGraph Orchestrator                      │
│              (Multi-Agent Coordination)                      │
└─────┬──────┬─────────┬─────────┬──────────┬────────────────┘
      │      │         │         │          │
      ▼      ▼         ▼         ▼          ▼
  ┌─────┐ ┌────┐  ┌─────┐   ┌─────┐   ┌─────────┐
  │Query│ │Anal│  │Triage│  │Recs │   │Knowledge│
  │Agent│ │ytics│  │Agent│   │Agent│   │  Agent  │
  └──┬──┘ └─┬──┘  └──┬──┘   └──┬──┘   └────┬────┘
     │      │        │          │           │
     └──────┴────────┴──────────┴───────────┘
                     │
                     ▼
     ┌──────────────────────────────────────┐
     │  Apache Pinot (Real-time Analytics)   │
     │  ChromaDB (Vector Knowledge Base)     │
     └──────────────────┬───────────────────┘
                        │
                        ▼
     ┌──────────────────────────────────────┐
     │    Kafka (Event Streaming)            │
     │    Synthetic Data Generator           │
     └───────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- OpenAI API key
- 8GB RAM minimum
- 20GB disk space

### Installation (5 minutes)

```bash
# 1. Clone repository
git clone <repo-url>
cd dhcs-intake-lab

# 2. Create .env file with your OpenAI API key
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY

# 3. Run automated setup
./setup.sh
```

That's it! The script will:
- Start all Docker services (Kafka, Pinot, agents, dashboard)
- Bootstrap Pinot schema and table
- Initialize the AI agents
- Load DHCS policies into knowledge base

### Access the System

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Pinot Console**: http://localhost:9000

### Test the System

```bash
./test_system.sh
```

## 💬 Try It Out

### Via Dashboard (Recommended)
1. Open http://localhost:8501
2. Select "💬 Chat Assistant"
3. Ask: "How many high-risk events happened in the last hour?"
4. Explore other modes: Analytics, Triage, Recommendations

### Via API
```bash
# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Show me the top 3 counties by volume"}'

# Run analytics
curl -X POST http://localhost:8000/analytics \
  -H "Content-Type: application/json" \
  -d '{"analysis_type":"comprehensive","time_window_minutes":60}'

# Get triage recommendations
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"time_window_minutes":30,"limit":20}'
```

## 🤖 The Agents

### 1. Query Agent
**Role**: Data Query Specialist

Translates natural language questions into Pinot SQL queries and interprets results.

**Example Questions**:
- "How many events in the last 24 hours?"
- "Which county has the most high-risk cases?"
- "Show me Spanish-language call volume"

**Tech Stack**: LangChain, OpenAI GPT-4, Pinot SQL

### 2. Analytics Agent
**Role**: Trend & Anomaly Detection

Monitors data for surges, patterns, and anomalies. Provides operational insights.

**Capabilities**:
- Surge detection (compares current rate vs baseline)
- County-level trend analysis
- Risk distribution analysis
- Channel performance monitoring
- Anomaly detection (unusual patterns)

**Tech Stack**: Pandas, Statistical analysis, GPT-4 for insights

### 3. Triage Agent
**Role**: Risk Assessment & Prioritization

Scores crisis events by risk factors and creates prioritized action lists.

**Scoring Algorithm**:
- Risk level: Imminent (100), High (50)
- Suicidal ideation: +30
- Homicidal ideation: +40
- Substance use: +10
- Recency factor

**Output**: Prioritized list of cases requiring immediate attention

### 4. Recommendations Agent
**Role**: Operational Strategy Advisor

Analyzes operational data and provides actionable recommendations for improvement.

**Focus Areas**:
- **Staffing**: Where to add staff, language interpreters, schedule changes
- **Equity**: Language access disparities, geographic equity
- **Efficiency**: Wait time reduction, process improvements

**Output**: 5-7 specific, data-driven recommendations

### 5. Knowledge Agent (RAG)
**Role**: Policy & Procedure Expert

Uses Retrieval Augmented Generation to answer questions about DHCS policies and best practices.

**Knowledge Base Includes**:
- 988 Crisis Hotline protocols
- Mobile crisis team guidelines
- Language access requirements
- Data privacy & HIPAA compliance
- Quality metrics & KPIs
- Staffing guidelines

**Tech Stack**: ChromaDB, OpenAI Embeddings, RAG architecture

### 6. Orchestrator Agent
**Role**: Multi-Agent Coordinator

Uses LangGraph to:
1. Classify user intent
2. Route to appropriate specialized agent(s)
3. Coordinate multi-agent workflows
4. Generate final integrated response

**Tech Stack**: LangGraph (state machine for agent workflows)

## 📊 Data Flow

```
Synthetic Generator → Kafka → Pinot → AI Agents → Insights
     (JSON events)   (stream) (query)  (analyze)  (actions)
```

1. **Generator**: Creates realistic synthetic crisis intake events
2. **Kafka**: Streams events in real-time
3. **Pinot**: Stores and indexes for millisecond SQL queries
4. **Agents**: Query, analyze, and generate insights
5. **Dashboard**: Presents insights to users

## 🔐 Privacy & Security

### Synthetic Data Only
- **All data is synthetic** - No real PHI (Protected Health Information)
- Safe for demos, training, and development
- Realistic but completely fabricated

### Production Considerations
When deploying with real data:
- HIPAA-compliant infrastructure required
- Encryption in transit and at rest
- Role-based access control (RBAC)
- Audit logging for all PHI access
- De-identification for analytics where possible

## 📈 Use Cases

See [docs/USE_CASES.md](docs/USE_CASES.md) for detailed use cases including:

1. Real-time surge detection & response
2. Intelligent triage & case prioritization
3. Natural language query for non-technical staff
4. Operational recommendations & staffing
5. Policy & procedure knowledge access
6. Quality improvement & performance monitoring
7. Equity & language access monitoring
8. Cross-county mutual aid coordination

## 🌩️ Cloud Deployment

### AWS (Recommended for Production)
```bash
# See deployment/aws/README.md for detailed guide

# Quick deploy:
cd deployment/aws
./build_and_push.sh  # Push images to ECR
# Deploy CloudFormation stack
```

**Services Used**:
- ECS Fargate (containers)
- MSK (Managed Kafka)
- Application Load Balancer
- CloudWatch (monitoring)
- Secrets Manager (API keys)

**Est. Cost**: ~$240/month (small demo) to $880+/month (production)

### Kubernetes (AWS EKS, GKE, AKS)
```bash
# See deployment/kubernetes/README.md

kubectl apply -f deployment/kubernetes/
```

## 📦 Project Structure

```
dhcs-intake-lab/
├── agents/                    # Multi-agent system
│   ├── core/                 # Agent implementations
│   │   ├── orchestrator.py   # LangGraph orchestrator
│   │   ├── query_agent.py    # Natural language queries
│   │   ├── analytics_agent.py # Trend detection
│   │   ├── triage_agent.py   # Risk prioritization
│   │   ├── recommendations_agent.py # Operational advice
│   │   └── base_agent.py     # Base class
│   ├── knowledge/            # RAG knowledge base
│   │   └── knowledge_base.py # ChromaDB + DHCS policies
│   ├── utils/                # Utilities
│   │   └── pinot_client.py   # Pinot database client
│   └── requirements.txt
│
├── api/                      # FastAPI backend
│   ├── main.py              # API endpoints
│   └── Dockerfile
│
├── dashboard/               # Streamlit UI
│   ├── streamlit_app.py    # Dashboard app
│   ├── requirements.txt
│   └── Dockerfile
│
├── generator/              # Synthetic data generator
│   ├── producer.py         # Kafka producer
│   └── Dockerfile
│
├── pinot/                  # Pinot configuration
│   ├── schema.json         # Table schema
│   └── table-realtime.json # Table config
│
├── deployment/             # Cloud deployment
│   ├── aws/               # AWS (ECS, MSK)
│   └── kubernetes/        # Kubernetes manifests
│
├── docs/                  # Documentation
│   └── USE_CASES.md       # Detailed use cases
│
├── docker-compose.yml     # Local development
├── setup.sh              # Automated setup
├── test_system.sh        # System tests
├── README.md             # Original Pinot lab README
└── README_AGENTS.md      # This file
```

## 🛠️ Technology Stack

### AI & ML
- **LangChain**: Agent framework
- **LangGraph**: Multi-agent orchestration (state machine)
- **OpenAI GPT-4**: Large language model for reasoning
- **ChromaDB**: Vector database for RAG
- **OpenAI Embeddings**: Semantic search

### Data Infrastructure
- **Apache Kafka**: Event streaming (real-time ingestion)
- **Apache Pinot**: OLAP database (millisecond query latency)
- **Python**: Agent implementation language

### API & UI
- **FastAPI**: REST API backend
- **Streamlit**: Interactive dashboard
- **Uvicorn**: ASGI server

### DevOps
- **Docker & Docker Compose**: Containerization
- **AWS ECS/EKS**: Cloud deployment
- **CloudFormation**: Infrastructure as Code

## 🧪 Development

### Local Development Setup

```bash
# Install agent dependencies
cd agents
pip install -r requirements.txt

# Run API locally (without Docker)
cd ..
python -m uvicorn api.main:app --reload

# Run dashboard locally
cd dashboard
streamlit run streamlit_app.py
```

### Adding a New Agent

1. Create new agent in `agents/core/`:
```python
from agents.core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="My Agent",
            role="My Role",
            goal="My Goal"
        )

    def execute(self, input_data):
        # Your logic here
        return {"result": "..."}
```

2. Add to orchestrator in `agents/core/orchestrator.py`
3. Add API endpoint in `api/main.py`
4. Add UI in `dashboard/streamlit_app.py`

### Testing

```bash
# Test individual agents
python -m agents.core.query_agent

# Test API endpoints
./test_system.sh

# Load test
# Use locust or similar tools
```

## 📝 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (with defaults)
AGENT_MODEL=gpt-4-turbo-preview
AGENT_TEMPERATURE=0.7
PINOT_BROKER_URL=http://localhost:8099
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
CHROMA_PERSIST_DIR=./chroma_data
LOG_LEVEL=INFO
```

### Adjusting Synthetic Data Rate

Edit `docker-compose.yml`:
```yaml
generator:
  environment:
    RATE_PER_SEC: "10"  # Events per second
```

## 🐛 Troubleshooting

### Agents not responding
```bash
# Check API logs
docker compose logs agent-api

# Common issue: OpenAI API key not set
# Fix: Check .env file has correct OPENAI_API_KEY
```

### Pinot queries failing
```bash
# Check Pinot has data
curl "http://localhost:8099/query/sql" \
  -H "Content-Type: application/json" \
  -d '{"sql":"select count(*) from dhcs_crisis_intake"}'

# If count is 0, check:
docker compose logs generator  # Is generator running?
docker compose logs kafka      # Is Kafka healthy?
```

### Dashboard connection errors
```bash
# Ensure API is running
curl http://localhost:8000/health

# Check dashboard logs
docker compose logs dashboard
```

## 🎓 Learning Resources

### Understanding Multi-Agent Systems
- LangGraph documentation: https://langchain-ai.github.io/langgraph/
- Multi-agent patterns: https://python.langchain.com/docs/use_cases/agent_workflows

### RAG (Retrieval Augmented Generation)
- LangChain RAG tutorial: https://python.langchain.com/docs/use_cases/question_answering/
- ChromaDB docs: https://docs.trychroma.com/

### Real-time Analytics
- Apache Pinot: https://docs.pinot.apache.org/
- Stream processing patterns: https://kafka.apache.org/documentation/streams/

## 🤝 Contributing

This is a demo/prototype system. For production use:

1. **Security review** required before using real PHI
2. **HIPAA compliance** assessment needed
3. **Load testing** for expected traffic
4. **Incident response** plan
5. **Model evaluation** (accuracy, bias, fairness)

## 📄 License

[Your License Here]

## 👥 Team & Support

**Project Lead**: [Your Name]
**Organization**: DHCS Innovation Lab

**For Questions**:
- Technical: [email]
- Use Cases: [email]
- Deployment: [email]

---

## 🎯 Next Steps

### For Demo/Stakeholder Presentation:
1. Run `./setup.sh`
2. Open dashboard at http://localhost:8501
3. Show each mode (Chat, Analytics, Triage, Recommendations)
4. Emphasize: "All data is synthetic - this is a safe demo environment"

### For Pilot Deployment:
1. Review [docs/USE_CASES.md](docs/USE_CASES.md)
2. Select 1-2 pilot counties
3. Follow [deployment/aws/README.md](deployment/aws/README.md)
4. Train staff on system use
5. Gather feedback for iteration

### For Production:
1. Security & compliance review
2. Integration with real crisis line systems
3. Staff training program
4. Gradual rollout with monitoring
5. Continuous improvement based on outcomes

---

**Remember**: The goal is to build confidence that AI can help save lives and improve behavioral health crisis response. Start with synthetic data, demonstrate value, then scale.

**Questions?** Open an issue or contact the team!
