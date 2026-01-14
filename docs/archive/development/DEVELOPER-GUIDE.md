# Developer Guide

**Document Version**: 1.0
**Last Updated**: January 2026
**Audience**: Developers setting up local development environment

---

## Table of Contents
1. [Development Environment Setup](#development-environment-setup)
2. [Python Service Setup](#python-service-setup)
3. [C# Service Setup](#c-service-setup)
4. [Authentication & Access](#authentication--access)
5. [Running Services](#running-services)
6. [Debugging](#debugging)
7. [Common Issues](#common-issues)

---

## Development Environment Setup

### Prerequisites

**Required Software:**
- **Python 3.11+** - For AI service
- **.NET 8.0+** - For C# services (workflow, licensing, IP)
- **Docker Desktop** - For containerized services
- **Visual Studio Code** - Recommended IDE
- **Git** - Version control
- **Homebrew** (Mac) - Package manager

**VS Code Extensions:**
- Python
- C# Dev Kit
- Docker
- GitLens (optional)

### Initial Setup

```bash
# Install Homebrew (Mac only)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install UV (Python package manager)
brew install uv

# Install .NET SDK
brew install dotnet

# Verify installations
uv --version
dotnet --version
docker --version
```

---

## Python Service Setup

### AI Integration Service

The AI service is a Python FastAPI application that provides LLM integration.

#### 1. Navigate to Service Directory

```bash
cd dhcs-intake-lab/DHCS-AI-Integration
```

#### 2. Environment Configuration

Create `.env` file (copy from `.env.example`):

```bash
# Copy example environment file
cp .env.example .env
```

Required environment variables:
```bash
# .env file contents
OPENAI_API_KEY=your-openai-api-key
AWS_REGION=us-west-2
GUARDRAIL_IDENTIFIER=your-guardrail-arn
GUARDRAIL_VERSION=1

# Optional
LOG_LEVEL=INFO
```

**Note**: Guardrail ARNs are available in Slack or Teams chat.

#### 3. Create Virtual Environment & Install Dependencies

```bash
# Sync dependencies (creates .venv automatically)
uv sync

# Activate virtual environment
source .venv/bin/activate

# Verify installation
python --version
```

#### 4. Run the Service

```bash
# Standard run
python main.py

# With hot reloading (for development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 5. Verify Service

```bash
# Check health endpoint
curl http://localhost:8000/health

# Open Swagger UI
open http://localhost:8000/docs
```

**Expected Response**:
```json
{"status": "ok"}
```

---

## C# Service Setup

### Workflow Service

The workflow service is built with C# and Elsa workflows.

#### 1. Navigate to Service Directory

```bash
cd dhcs-intake-lab/BHT-Shared-WorkflowService-API
```

#### 2. NuGet Package Configuration

**Setup GitHub Personal Access Token:**

1. Go to GitHub Settings → Developer Settings
2. Personal Access Tokens → Tokens (classic)
3. Generate new token (classic)
   - Name: `nuget-registry`
   - Expiration: No expiration
   - Scopes: `repo`, `workflow`, `write:packages`
4. Copy the token

**Configure NuGet.config:**

Edit `nuget.config` in the project root:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <add key="GitHub" value="https://nuget.pkg.github.com/ca-department-of-health-care-services/index.json" />
  </packageSources>
  <packageSourceCredentials>
    <GitHub>
      <add key="Username" value="your-github-username" />
      <add key="ClearTextPassword" value="your-github-token" />
    </GitHub>
  </packageSourceCredentials>
</configuration>
```

**Authorize Token:**
1. Go back to GitHub token page
2. Click "Configure SSO"
3. Click "Authorize" next to `ca-department-of-health-care-services`

#### 3. App Settings Configuration

**Get Settings from Vault:**

1. Go to MyApps → Vault App Dev
2. Sign in with Azure
3. Select tenant: `admin/tenant/BHT`
4. Navigate to: Secret → BHT → (find workflow service settings)

**Create Development Settings:**

Create `src/BHT.Shared.WorkflowService.API/appsettings.Development.json`:

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "your-connection-string"
  },
  "Elsa": {
    "Server": {
      "BaseUrl": "http://localhost:5000"
    }
  }
}
```

**Note**: Complete settings are available in Vault or from team members.

#### 4. Restore Dependencies

```bash
# From service directory
dotnet restore

# Verify packages installed
dotnet list package
```

#### 5. Run the Service

```bash
# Run with hot reload
dotnet watch run --project src/BHT.Shared.WorkflowService.API

# Or standard run
dotnet run --project src/BHT.Shared.WorkflowService.API
```

#### 6. Verify Service

```bash
# Check health
curl http://localhost:5000/health

# Open Swagger
open http://localhost:5000/swagger
```

---

## Authentication & Access

### Teleport CLI (AWS Credentials)

**Installation:**

```bash
# Install Teleport CLI
brew install teleport

# Verify installation
tsh version
```

**Usage:**

```bash
# Login to Teleport
tsh login --proxy=teleport.dhcs.ca.gov --user=your-email@dhcs.ca.gov

# Get AWS credentials
tsh aws login --app=aws-app-dev

# Verify credentials
aws sts get-caller-identity
```

**What Teleport Does:**
- Provides temporary AWS credentials
- Enforces authorization via Azure AD
- Eliminates need for long-lived access keys

### Vault (Secrets Management)

**Access Vault:**

1. Go to MyApps: https://myapps.microsoft.com
2. Click "Vault App Dev" (black triangle icon)
3. Sign in with Azure AD
4. Allow pop-ups if prompted

**Safari Pop-up Settings:**
1. Settings → Websites → Pop-up Windows
2. Add `vault-dev.med...` → Allow

**Finding Secrets:**
1. Select tenant: `admin/tenant/BHT`
2. Navigate to: `Secret` tab
3. Search for service name (e.g., "workflow")
4. Copy required secrets

---

## Running Services

### Individual Services

**AI Service (Python):**
```bash
cd DHCS-AI-Integration
source .venv/bin/activate
python main.py
# Runs on http://localhost:8000
```

**Workflow Service (C#):**
```bash
cd BHT-Shared-WorkflowService-API
dotnet run --project src/BHT.Shared.WorkflowService.API
# Runs on http://localhost:5000
```

**Licensing Service (C#):**
```bash
cd BHT-Licensing-Service-API
dotnet run --project src/BHT.Licensing.API
# Runs on http://localhost:5001
```

**IP Service (C#):**
```bash
cd BHT-IP-UI
dotnet run --project src/BHT.IP.API
# Runs on http://localhost:5002
```

### Docker Compose (All Services)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## Debugging

### VS Code Debugging

#### Python Service

**Launch Configuration** (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "cwd": "${workspaceFolder}/DHCS-AI-Integration"
    }
  ]
}
```

**Steps:**
1. Open Python service in VS Code: `code DHCS-AI-Integration`
2. Set breakpoints in Python files
3. Press F5 or click "Run and Debug"
4. Select "Python: FastAPI"

#### C# Service

**Steps:**
1. Open C# service: `code BHT-Shared-WorkflowService-API`
2. Open `src/BHT.Shared.WorkflowService.API/Program.cs`
3. Click "Run and Debug" → Select "C#"
4. Set breakpoints in C# files
5. Press F5

**Note**: C# debugging requires opening the specific project, not the workspace.

### Debugging Across Services

**Challenge**: Setting breakpoints across multiple services in a workspace.

**Solution**:
1. Use separate VS Code windows for each service
2. Or use Docker Compose + remote debugging
3. Or run services separately and debug one at a time

### Tracing Workflows

**Elsa Workflow Debugging:**

1. Workflows have parent/child relationships
2. Workflows are identified by `plant_id`
3. Use Elsa dashboard to visualize workflow execution
4. Check workflow logs for execution history

**Key Concepts:**
- **Kickoff Workflow**: Parent workflow that starts the process
- **Child Workflows**: Sub-workflows triggered by parent
- **Workflow Instance**: Specific execution of a workflow

---

## Common Issues

### Issue: `No module named 'app'`

**Cause**: Virtual environment not activated

**Solution**:
```bash
cd DHCS-AI-Integration
source .venv/bin/activate
python main.py
```

### Issue: NuGet restore fails

**Cause**: GitHub token not configured or not authorized

**Solution**:
1. Verify token in `nuget.config`
2. Check token has correct scopes
3. Authorize token for DHCS organization
4. Run `dotnet restore` again

### Issue: "Unable to find project"

**Cause**: Running from wrong directory or workspace

**Solution**:
- Run from service root directory
- Or use `--project` flag with full path
- Or open service in separate VS Code window

### Issue: Port already in use

**Cause**: Service already running or port conflict

**Solution**:
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in configuration
```

### Issue: AWS credentials not found

**Cause**: Teleport not configured or credentials expired

**Solution**:
```bash
# Install Teleport CLI
brew install teleport

# Login and get credentials
tsh login --proxy=teleport.dhcs.ca.gov
tsh aws login --app=aws-app-dev

# Verify
aws sts get-caller-identity
```

### Issue: Vault access denied

**Cause**: Pop-ups blocked or not logged into Azure AD

**Solution**:
1. Enable pop-ups for vault domain
2. Sign out and sign back in
3. Verify Azure AD credentials

### Issue: C# debugger won't start

**Cause**: Workspace opened instead of project

**Solution**:
```bash
# Open specific project
cd BHT-Shared-WorkflowService-API
code .

# Then debug from that window
```

---

## Development Workflow

### 1. Daily Setup

```bash
# 1. Pull latest changes
git pull origin main

# 2. Update Python dependencies (if changed)
cd DHCS-AI-Integration
uv sync

# 3. Update C# dependencies (if changed)
cd ../BHT-Shared-WorkflowService-API
dotnet restore

# 4. Start services
python main.py  # AI service
dotnet run --project src/BHT.Shared.WorkflowService.API  # Workflow
```

### 2. Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes

# 3. Test locally

# 4. Commit
git add .
git commit -m "feat: your feature description"

# 5. Push
git push origin feature/your-feature-name

# 6. Create pull request
```

### 3. Testing

**Python Tests:**
```bash
cd DHCS-AI-Integration
pytest tests/
```

**C# Tests:**
```bash
cd BHT-Shared-WorkflowService-API
dotnet test
```

**Integration Tests:**
- Use Swagger UI to test endpoints
- Use Postman collections (if available)
- Run end-to-end workflow tests

---

## Architecture Overview

### Service Relationships

```
┌─────────────────────────────────────────────────────┐
│               BHT Platform                          │
│                                                     │
│  ┌─────────────┐      ┌──────────────┐            │
│  │ AI Service  │◄────►│   Workflow   │            │
│  │  (Python)   │      │   Service    │            │
│  │  Port 8000  │      │   (C#/Elsa)  │            │
│  └─────────────┘      │   Port 5000  │            │
│                       └──────────────┘             │
│                              │                      │
│                              ▼                      │
│         ┌────────────────────────────────┐         │
│         │  Child Workflows               │         │
│         │  - Licensing                   │         │
│         │  - IP Compliance               │         │
│         │  - Document Processing         │         │
│         └────────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

### Key Technologies

**Python Stack:**
- FastAPI - REST API framework
- Pydantic - Data validation
- boto3 - AWS SDK
- OpenAI SDK - LLM integration

**C# Stack:**
- ASP.NET Core - Web framework
- Elsa - Workflow engine
- Entity Framework - ORM
- MediatR - CQR pattern

---

## Additional Resources

- [API Documentation](./API.md)
- [Architecture Guide](../03-ARCHITECTURE.md)
- [Troubleshooting Guide](../guides/TROUBLESHOOTING.md)
- [Deployment Guide](../deployment/LOCAL.md)

---

## Getting Help

**Questions?**
- Check [FAQ](../guides/FAQ.md)
- Ask in team Slack channel
- Review meeting recordings
- Contact team lead

**Issues?**
- Check [Troubleshooting Guide](../guides/TROUBLESHOOTING.md)
- Review error logs
- Search existing GitHub issues
- Create new issue if needed

---

**Last Updated**: January 2026
**Document Maintainer**: Development Team
