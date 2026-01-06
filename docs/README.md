# DHCS BHT Multi-Agent AI System - Documentation

Welcome to the documentation for the California Department of Health Care Services (DHCS) Behavioral Health Transformation (BHT) Multi-Agent AI System.

---

## 📚 Documentation Structure

### Getting Started
1. **[Overview](./01-OVERVIEW.md)** - What is this system? Key features and background
2. **[Quick Start Guide](./02-QUICKSTART.md)** - Get running in 5 minutes
3. **[Architecture](./03-ARCHITECTURE.md)** - System design and technical details
4. **[Use Cases](./04-USE-CASES.md)** - Detailed use case documentation

### Deployment
- **[Local Deployment](./deployment/LOCAL.md)** - Docker Compose for development
- **[AWS Deployment](./deployment/AWS.md)** - Production deployment on AWS ECS
- **[Configuration](./deployment/CONFIGURATION.md)** - Environment variables and settings

### Development
- **[Developer Guide](./development/DEVELOPER-GUIDE.md)** - Contributing and development workflow
- **[API Reference](./development/API.md)** - REST API endpoints and usage
- **[Agent Development](./development/AGENTS.md)** - Creating custom agents
- **[Data Generators](./development/DATA-GENERATORS.md)** - Synthetic data generation

### Guides
- **[Troubleshooting](./guides/TROUBLESHOOTING.md)** - Common issues and solutions
- **[FAQ](./guides/FAQ.md)** - Frequently asked questions
- **[Best Practices](./guides/BEST-PRACTICES.md)** - Development and operational guidelines

---

## 🚀 Quick Links

### For New Users
Start here to understand what the system does:
1. [Overview](./01-OVERVIEW.md) - 5 minute read
2. [Quick Start](./02-QUICKSTART.md) - 10 minute setup
3. Try the dashboard: http://localhost:8501

### For Developers
Start building with the system:
1. [Architecture](./03-ARCHITECTURE.md) - Understand the design
2. [Developer Guide](./development/DEVELOPER-GUIDE.md) - Setup dev environment
3. [API Reference](./development/API.md) - Integrate with APIs

### For Operators
Deploy and maintain the system:
1. [Local Deployment](./deployment/LOCAL.md) - Development setup
2. [AWS Deployment](./deployment/AWS.md) - Production deployment
3. [Monitoring](./deployment/MONITORING.md) - System monitoring

---

## 🎯 Use Cases Covered

The system supports 8 specialized use cases:

1. **Crisis Triage** - Real-time crisis assessment and prioritization
2. **Policy Q&A** - AI-powered policy document search
3. **BHOATR Reporting** - Automated outcomes and accountability reporting
4. **Licensing Assistant** - Facility licensing application support
5. **IP Compliance** - Integrated Plan compliance verification
6. **Infrastructure Tracking** - Prop 1/SB 326 project monitoring
7. **Population Analytics** - Demographics and service utilization
8. **Resource Allocation** - Optimized resource distribution

See [Use Cases Documentation](./04-USE-CASES.md) for details.

---

## 🏗️ Technology Stack

### Core Technologies
- **Backend**: FastAPI, LangGraph, Python 3.11+
- **Frontend**: Streamlit, Modern CSS
- **AI/ML**: OpenAI GPT-4o, ChromaDB (RAG)
- **Data**: Apache Kafka, Apache Pinot, PostgreSQL
- **Infrastructure**: Docker, AWS ECS, CloudWatch

### Key Features
- 🤖 Multi-agent AI architecture
- 📊 Real-time streaming analytics
- 💬 Natural language interface
- 🔒 Production-ready deployment
- 📈 Comprehensive monitoring

---

## 📖 Documentation Map

```
docs/
├── README.md (this file)
│
├── Core Documentation
│   ├── 01-OVERVIEW.md          # System overview and background
│   ├── 02-QUICKSTART.md        # 5-minute getting started guide
│   ├── 03-ARCHITECTURE.md      # Technical architecture
│   └── 04-USE-CASES.md         # Detailed use cases
│
├── deployment/
│   ├── LOCAL.md                # Docker Compose setup
│   ├── AWS.md                  # AWS ECS deployment
│   ├── KUBERNETES.md           # Kubernetes (optional)
│   ├── CONFIGURATION.md        # Environment variables
│   └── MONITORING.md           # Observability setup
│
├── development/
│   ├── DEVELOPER-GUIDE.md      # Dev environment setup
│   ├── API.md                  # REST API reference
│   ├── AGENTS.md               # Agent development
│   ├── DATA-GENERATORS.md      # Synthetic data
│   └── TESTING.md              # Testing guidelines
│
├── guides/
│   ├── TROUBLESHOOTING.md      # Common issues
│   ├── FAQ.md                  # Frequently asked questions
│   ├── BEST-PRACTICES.md       # Guidelines
│   └── SECURITY.md             # Security considerations
│
└── archive/
    └── (old documentation files)
```

---

## 🔧 Common Tasks

### Setup Development Environment
```bash
# Clone and start
git clone <repo> dhcs-intake-lab
cd dhcs-intake-lab
echo "OPENAI_API_KEY=sk-..." > .env
docker-compose up -d

# Generate data
docker-compose exec agent-api python /app/generator/populate_all_data.py

# Access dashboard
open http://localhost:8501
```

See [Quick Start Guide](./02-QUICKSTART.md) for details.

### Deploy to AWS
```bash
# Build and push images
./deployment/build-and-deploy.sh

# Or use automated setup
./deployment/deploy-minimal.sh
```

See [AWS Deployment Guide](./deployment/AWS.md) for details.

### Create Custom Agent
```python
# Create agent file
# agents/agents/my_custom_agent.py

from agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def execute(self, input_data):
        # Your logic here
        return result
```

See [Agent Development Guide](./development/AGENTS.md) for details.

---

## 📊 System Status

### Current Version: 1.0
- ✅ Multi-agent system (8 use cases)
- ✅ Real-time streaming (Kafka → Pinot)
- ✅ Policy Q&A with RAG (ChromaDB)
- ✅ Modern Streamlit dashboard
- ✅ Docker Compose deployment
- ✅ AWS ECS deployment support
- ✅ Comprehensive synthetic data generators

### In Progress
- 🚧 Advanced analytics features
- 🚧 Performance monitoring dashboard
- 🚧 Additional use case implementations

---

## 🆘 Getting Help

### Documentation Issues
If you find errors or gaps in documentation:
1. Check [FAQ](./guides/FAQ.md) first
2. Review [Troubleshooting Guide](./guides/TROUBLESHOOTING.md)
3. Contact development team

### Technical Support
For system issues:
1. Check logs: `docker-compose logs agent-api`
2. Verify health: `curl http://localhost:8000/health`
3. Review [Troubleshooting Guide](./guides/TROUBLESHOOTING.md)

### Feature Requests
To propose new features or improvements:
1. Review [Roadmap](./archive/ROADMAP.md)
2. Submit request to development team

---

## 📝 Contributing

See [Developer Guide](./development/DEVELOPER-GUIDE.md) for:
- Code style guidelines
- Testing requirements
- Pull request process
- Development workflow

---

## 📄 License

This project is developed for the California Department of Health Care Services (DHCS).

---

## 🔗 External Resources

### Background Documents
- [BHT Project Background (PDF)](../BHT%20Project%20Background%20for%20Candidates%20(1)%20(1).pdf)
- [DHCS Prop 1 Fact Sheet (PDF)](../DHCS%20Prop%201%20Fact%20Sheet%20(1)%20(1).pdf)

### Related Links
- [Proposition 1 Information](https://www.dhcs.ca.gov/prop1)
- [DHCS Behavioral Health](https://www.dhcs.ca.gov/services/MH/Pages/default.aspx)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)

---

**Last Updated**: January 2026
**Version**: 1.0

---

## Next Steps

👉 **New to the system?** Start with the [Overview](./01-OVERVIEW.md)

👉 **Want to try it?** Follow the [Quick Start Guide](./02-QUICKSTART.md)

👉 **Ready to deploy?** Check [Local](./deployment/LOCAL.md) or [AWS Deployment](./deployment/AWS.md)

👉 **Want to develop?** Read the [Developer Guide](./development/DEVELOPER-GUIDE.md)
