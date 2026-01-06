# DHCS BHT Multi-Agent AI System - Overview

**Version**: 1.0
**Last Updated**: January 2026
**Status**: Production Ready

---

## Table of Contents
1. [What is this system?](#what-is-this-system)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [Quick Links](#quick-links)

---

## What is this system?

The **DHCS Behavioral Health Transformation (BHT) Multi-Agent AI System** is an intelligent platform designed to support California's behavioral health transformation initiatives under Proposition 1 and related legislation (AB 531, SB 326).

### Purpose
This system provides AI-powered assistance for:
- **Crisis Triage**: Real-time analysis and recommendations for behavioral health crises
- **Policy Q&A**: Instant access to policy documents and guidelines
- **BHOATR Reporting**: Automated outcomes, accountability, and transparency reporting
- **Licensing Assistance**: Streamlined facility licensing application support
- **IP Compliance**: Integrated Plan compliance verification
- **Infrastructure Tracking**: Prop 1/SB 326 project monitoring
- **Population Analytics**: Demographics and service utilization analysis
- **Resource Allocation**: Optimized resource distribution recommendations

### Background: Proposition 1 & BHT

**Proposition 1 (2024)**
- **$6.38 billion** bond measure for behavioral health infrastructure
- Focus on treatment facilities, housing, and crisis services
- Target populations: individuals experiencing homelessness and justice involvement

**Key Goals**:
- Increase county compliance with BHT requirements
- Improve access to behavioral health care
- Expand treatment facilities statewide
- Enhance crisis response capabilities

---

## Key Features

### 🤖 Multi-Agent Architecture
- **Orchestrator Agent**: Routes queries to specialized agents
- **Crisis Triage Agent**: Analyzes crisis situations and recommends interventions
- **Knowledge Agent**: RAG-based policy document retrieval
- **Analytics Agent**: Real-time data analysis and reporting
- **Recommendations Agent**: Generates actionable insights

### 📊 Real-Time Data Processing
- **Kafka Streaming**: Live crisis event ingestion
- **Apache Pinot**: Real-time OLAP analytics
- **ChromaDB**: Vector database for semantic search

### 💬 Modern UI
- **Streamlit Dashboard**: Clean, Grok-inspired interface
- **8 Use Cases**: Specialized interfaces for each workflow
- **Real-time Chat**: Interactive AI assistant
- **Context-Aware**: Filters and suggestions based on use case

### 🔒 Production Ready
- **Dockerized**: Fully containerized stack
- **AWS Deployment**: ECS/Fargate compatible
- **Scalable**: Horizontal scaling support
- **Monitored**: Health checks and logging

---

## Technology Stack

### Backend
- **FastAPI**: REST API framework
- **LangGraph**: Multi-agent orchestration
- **OpenAI GPT-4**: Large language model
- **Python 3.11+**: Core runtime

### Data Layer
- **Apache Kafka**: Event streaming
- **Apache Pinot**: Real-time analytics
- **ChromaDB**: Vector database
- **PostgreSQL**: Optional structured data storage

### Frontend
- **Streamlit**: Web dashboard
- **Modern CSS**: Clean, minimal design

### Infrastructure
- **Docker Compose**: Local development
- **AWS ECS**: Production deployment
- **AWS ECR**: Container registry
- **Application Load Balancer**: Traffic distribution

---

## Quick Links

### Getting Started
- [Quick Start Guide](./02-QUICKSTART.md) - Get running in 5 minutes
- [Architecture Details](./03-ARCHITECTURE.md) - System design and patterns
- [Use Cases](./04-USE-CASES.md) - Detailed use case documentation

### Deployment
- [Local Deployment](./deployment/LOCAL.md) - Docker Compose setup
- [AWS Deployment](./deployment/AWS.md) - Production deployment guide
- [Configuration](./deployment/CONFIGURATION.md) - Environment variables and settings

### Development
- [Developer Guide](./development/DEVELOPER-GUIDE.md) - Contributing and development
- [API Documentation](./development/API.md) - REST API reference
- [Agent Development](./development/AGENTS.md) - Creating custom agents

---

## Project Status

### ✅ Completed
- Multi-agent AI system with 8 use cases
- Real-time crisis event streaming (Kafka → Pinot)
- Policy Q&A with RAG (ChromaDB)
- Modern Streamlit dashboard UI
- Docker Compose local deployment
- Synthetic data generators
- Comprehensive testing

### 🚧 In Progress
- AWS production deployment optimization
- Additional use case implementations
- Performance monitoring dashboard

### 📋 Planned
- Multi-county deployment
- Advanced analytics features
- Mobile application
- Integration with existing DHCS systems

---

## License

This project is developed for the California Department of Health Care Services (DHCS).

---

## Support

For questions or issues, please contact the development team or refer to:
- [Troubleshooting Guide](./guides/TROUBLESHOOTING.md)
- [FAQ](./guides/FAQ.md)

---

**Next Steps**: Start with the [Quick Start Guide](./02-QUICKSTART.md) to get the system running locally.
