# Pluggable Architecture for BHT Use Cases

**Goal**: Easily add new BHT use cases without modifying core system

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                               │
│                  (Route by Use Case)                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
┌────────▼────────┐ ┌─────▼──────────────┐
│  Core Engine    │ │  Use Case Registry  │
│  (Orchestrator) │ │  (Plugin Manager)   │
└────────┬────────┘ └─────┬──────────────┘
         │                 │
         │        ┌────────┴────────┐
         │        │                 │
         │   ┌────▼────┐       ┌───▼────┐
         │   │ Plugin 1│  ...  │Plugin N│
         │   │(Crisis) │       │(Policy)│
         │   └────┬────┘       └───┬────┘
         │        │                │
         │   ┌────▼────────────────▼────┐
         └───►   Shared Resources        │
             │ • Pinot Client            │
             │ • ChromaDB                │
             │ • LLM Interface           │
             └───────────────────────────┘
```

## Plugin System Design

### 1. Base Plugin Interface

**File**: `agents/plugins/base_plugin.py`

```python
"""
Base plugin interface for BHT use cases
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class PluginMetadata(BaseModel):
    """Metadata describing a plugin"""
    name: str
    version: str
    description: str
    author: str
    use_case: str  # e.g., "crisis_triage", "policy_qa", "licensing"
    capabilities: List[str]  # What can this plugin do?
    required_data_sources: List[str]  # Pinot, ChromaDB, etc.
    keywords: List[str]  # For intent matching


class PluginResponse(BaseModel):
    """Standardized response from a plugin"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    sources: List[Dict[str, Any]]
    confidence: float
    suggestions: Optional[List[str]] = None


class BasePlugin(ABC):
    """
    Base class for all BHT plugins

    Each plugin represents a specific use case (e.g., crisis triage,
    policy Q&A, licensing queries, county portal integration)
    """

    def __init__(self):
        self.metadata = self.get_metadata()
        self._initialized = False

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abstractmethod
    async def initialize(self, resources: Dict[str, Any]) -> bool:
        """
        Initialize plugin with shared resources

        Args:
            resources: Dict containing:
                - pinot_client: PinotClient instance
                - chroma_client: ChromaDB instance
                - llm: OpenAI/LangChain LLM
                - config: Plugin-specific config

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if this plugin can handle the query

        Args:
            query: User's natural language query
            context: Additional context (user role, previous queries, etc.)

        Returns:
            Confidence score 0.0-1.0 (0 = cannot handle, 1.0 = perfect match)
        """
        pass

    @abstractmethod
    async def execute(self, query: str, context: Dict[str, Any]) -> PluginResponse:
        """
        Execute the plugin's core logic

        Args:
            query: User's natural language query
            context: Additional context

        Returns:
            PluginResponse with results
        """
        pass

    @abstractmethod
    async def get_examples(self) -> List[str]:
        """
        Return example queries this plugin can handle
        Used for UI quick actions and help text
        """
        pass

    async def cleanup(self):
        """Cleanup resources (optional)"""
        pass


class PluginRegistry:
    """
    Central registry for managing plugins
    """

    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.initialized = False

    def register(self, plugin: BasePlugin):
        """Register a new plugin"""
        plugin_name = plugin.metadata.name
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin {plugin_name} already registered")

        self.plugins[plugin_name] = plugin
        print(f"✅ Registered plugin: {plugin_name} v{plugin.metadata.version}")

    async def initialize_all(self, shared_resources: Dict[str, Any]):
        """Initialize all registered plugins"""
        for name, plugin in self.plugins.items():
            try:
                success = await plugin.initialize(shared_resources)
                if not success:
                    print(f"⚠️  Plugin {name} failed to initialize")
            except Exception as e:
                print(f"❌ Error initializing plugin {name}: {e}")

        self.initialized = True

    async def route_query(self, query: str, context: Dict[str, Any]) -> PluginResponse:
        """
        Route query to best matching plugin

        Returns response from plugin with highest confidence
        """
        if not self.initialized:
            raise RuntimeError("Plugin registry not initialized")

        # Get confidence scores from all plugins
        scores = {}
        for name, plugin in self.plugins.items():
            try:
                score = await plugin.can_handle(query, context)
                scores[name] = score
            except Exception as e:
                print(f"Error checking plugin {name}: {e}")
                scores[name] = 0.0

        # Select best plugin
        best_plugin_name = max(scores, key=scores.get)
        confidence = scores[best_plugin_name]

        if confidence < 0.3:
            # No plugin confident enough - return generic response
            return PluginResponse(
                success=False,
                data={"error": "No plugin found to handle this query"},
                metadata={"scores": scores},
                sources=[],
                confidence=0.0,
                suggestions=[
                    "Try rephrasing your question",
                    "View example queries for available use cases"
                ]
            )

        # Execute best plugin
        best_plugin = self.plugins[best_plugin_name]
        response = await best_plugin.execute(query, context)

        # Add routing metadata
        response.metadata["selected_plugin"] = best_plugin_name
        response.metadata["confidence"] = confidence
        response.metadata["all_scores"] = scores

        return response

    def get_all_examples(self) -> Dict[str, List[str]]:
        """Get example queries from all plugins"""
        examples = {}
        for name, plugin in self.plugins.items():
            examples[name] = plugin.get_examples()
        return examples

    def get_plugin_info(self) -> List[PluginMetadata]:
        """Get metadata for all plugins"""
        return [plugin.metadata for plugin in self.plugins.values()]


# Global registry instance
registry = PluginRegistry()
```

### 2. Example Plugin: Crisis Triage (Current System)

**File**: `agents/plugins/crisis_triage_plugin.py`

```python
"""
Crisis Triage Plugin - Original use case
"""
from typing import Dict, Any, List
from agents.plugins.base_plugin import BasePlugin, PluginMetadata, PluginResponse
from agents.core.query_agent import QueryAgent
from agents.core.analytics_agent import AnalyticsAgent
from agents.core.triage_agent import TriageAgent


class CrisisTriagePlugin(BasePlugin):
    """
    Handles crisis intake event queries, analytics, and triage
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="crisis_triage",
            version="1.0.0",
            description="Crisis intake event tracking, analytics, and triage",
            author="DHCS BHT Team",
            use_case="crisis_triage",
            capabilities=[
                "query_events",
                "detect_surge",
                "triage_high_risk",
                "analyze_trends",
                "county_statistics"
            ],
            required_data_sources=["pinot", "chromadb"],
            keywords=[
                "crisis", "events", "high-risk", "imminent", "surge",
                "triage", "intake", "county", "trends", "analytics",
                "suicidal", "homicidal", "wait time", "call duration"
            ]
        )

    async def initialize(self, resources: Dict[str, Any]) -> bool:
        """Initialize agents"""
        try:
            self.pinot_client = resources["pinot_client"]
            self.llm = resources["llm"]

            # Initialize sub-agents
            self.query_agent = QueryAgent(self.pinot_client, self.llm)
            self.analytics_agent = AnalyticsAgent(self.pinot_client, self.llm)
            self.triage_agent = TriageAgent(self.pinot_client, self.llm)

            self._initialized = True
            return True
        except Exception as e:
            print(f"Crisis Triage plugin initialization error: {e}")
            return False

    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """
        Determine if query is about crisis triage
        """
        query_lower = query.lower()

        # Keyword matching
        keyword_matches = sum(1 for kw in self.metadata.keywords if kw in query_lower)
        keyword_score = min(keyword_matches / 3, 1.0)  # 3+ keywords = 1.0

        # Pattern matching
        crisis_patterns = [
            "how many events",
            "high-risk",
            "imminent risk",
            "surge",
            "triage",
            "crisis",
            "presenting problem",
            "wait time",
            "county statistics"
        ]

        pattern_matches = sum(1 for pattern in crisis_patterns if pattern in query_lower)
        pattern_score = min(pattern_matches / 2, 1.0)

        # Combine scores
        confidence = (keyword_score * 0.4 + pattern_score * 0.6)

        return confidence

    async def execute(self, query: str, context: Dict[str, Any]) -> PluginResponse:
        """
        Execute crisis triage logic
        """
        try:
            # Determine intent
            if any(word in query.lower() for word in ["surge", "spike", "increase"]):
                # Analytics agent
                result = await self.analytics_agent.analyze(query)
            elif any(word in query.lower() for word in ["triage", "prioritize", "high-risk"]):
                # Triage agent
                result = await self.triage_agent.triage(query)
            else:
                # Query agent
                result = await self.query_agent.query(query)

            return PluginResponse(
                success=True,
                data=result["data"],
                metadata={
                    "agent_used": result.get("agent", "query"),
                    "execution_time_ms": result.get("duration_ms", 0)
                },
                sources=result.get("sources", []),
                confidence=1.0
            )

        except Exception as e:
            return PluginResponse(
                success=False,
                data={"error": str(e)},
                metadata={},
                sources=[],
                confidence=0.0
            )

    async def get_examples(self) -> List[str]:
        return [
            "How many high-risk events in the last hour?",
            "Show me surge patterns for Los Angeles County",
            "Triage the top 20 high-risk cases",
            "What are the most common presenting problems?",
            "Analyze wait times by county",
            "Detect if there's a surge right now"
        ]
```

### 3. New Plugin: Policy Q&A

**File**: `agents/plugins/policy_qa_plugin.py`

```python
"""
Policy Q&A Plugin - Answer questions about DHCS BHT policies
"""
from typing import Dict, Any, List
from agents.plugins.base_plugin import BasePlugin, PluginMetadata, PluginResponse
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


class PolicyQAPlugin(BasePlugin):
    """
    Answers questions about DHCS BHT policies, guidelines, and procedures
    Uses ChromaDB for RAG over policy documents
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="policy_qa",
            version="1.0.0",
            description="Answer questions about DHCS BHT policies and guidelines",
            author="DHCS BHT Team",
            use_case="policy_qa",
            capabilities=[
                "answer_policy_questions",
                "cite_guidelines",
                "explain_procedures",
                "compliance_check"
            ],
            required_data_sources=["chromadb"],
            keywords=[
                "policy", "guideline", "procedure", "requirement",
                "compliance", "regulation", "rule", "standard",
                "AB 531", "SB 326", "Prop 1", "BHT", "DHCS",
                "license", "certification", "eligibility"
            ]
        )

    async def initialize(self, resources: Dict[str, Any]) -> bool:
        try:
            self.chroma_client = resources["chroma_client"]
            self.llm = resources["llm"]

            # Create RAG chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.chroma_client.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": PromptTemplate(
                        template="""You are a DHCS Behavioral Health Transformation policy expert.

Use the following policy documents to answer the question. Always cite specific sections or page numbers.

Context:
{context}

Question: {question}

Provide a clear, accurate answer with citations. If you're not sure, say so.

Answer:""",
                        input_variables=["context", "question"]
                    )
                }
            )

            self._initialized = True
            return True
        except Exception as e:
            print(f"Policy QA plugin initialization error: {e}")
            return False

    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """Determine if query is about policy"""
        query_lower = query.lower()

        # Strong indicators
        strong_patterns = [
            "what is the policy",
            "what are the requirements",
            "what does prop 1",
            "what does AB 531",
            "what does SB 326",
            "compliance",
            "guideline",
            "procedure"
        ]

        if any(pattern in query_lower for pattern in strong_patterns):
            return 0.95

        # Keyword matching
        keyword_matches = sum(1 for kw in self.metadata.keywords if kw in query_lower)
        keyword_score = min(keyword_matches / 2, 1.0)

        # Question patterns
        question_patterns = ["what is", "what are", "how do i", "explain", "define"]
        has_question = any(pattern in query_lower for pattern in question_patterns)

        confidence = keyword_score * (1.2 if has_question else 1.0)
        return min(confidence, 1.0)

    async def execute(self, query: str, context: Dict[str, Any]) -> PluginResponse:
        """Answer policy question using RAG"""
        try:
            result = await self.qa_chain.ainvoke({"query": query})

            # Extract source documents
            sources = []
            for doc in result.get("source_documents", []):
                sources.append({
                    "type": "policy_document",
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })

            return PluginResponse(
                success=True,
                data={
                    "answer": result["result"],
                    "source_count": len(sources)
                },
                metadata={
                    "query_type": "policy_qa"
                },
                sources=sources,
                confidence=0.9
            )

        except Exception as e:
            return PluginResponse(
                success=False,
                data={"error": str(e)},
                metadata={},
                sources=[],
                confidence=0.0
            )

    async def get_examples(self) -> List[str]:
        return [
            "What is Proposition 1?",
            "What are the requirements for AB 531 compliance?",
            "Explain the BHT licensing process",
            "What counties are eligible for Prop 1 funding?",
            "Define behavioral health crisis services",
            "What are the reporting requirements for BHOATR?"
        ]
```

### 4. New Plugin: Infrastructure Tracking

**File**: `agents/plugins/infrastructure_plugin.py`

```python
"""
Infrastructure Tracking Plugin - Track BHT infrastructure projects (AB 531, SB 326)
"""
from typing import Dict, Any, List
from agents.plugins.base_plugin import BasePlugin, PluginMetadata, PluginResponse


class InfrastructurePlugin(BasePlugin):
    """
    Track BHT infrastructure projects, funding, and construction status
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="infrastructure_tracking",
            version="1.0.0",
            description="Track BHT infrastructure projects and funding",
            author="DHCS BHT Team",
            use_case="infrastructure",
            capabilities=[
                "track_projects",
                "funding_status",
                "construction_updates",
                "facility_locations"
            ],
            required_data_sources=["pinot"],  # Would add project tracking table
            keywords=[
                "infrastructure", "construction", "facility", "building",
                "AB 531", "SB 326", "funding", "grant", "project",
                "beds", "treatment center", "residential", "crisis center"
            ]
        )

    async def initialize(self, resources: Dict[str, Any]) -> bool:
        try:
            self.pinot_client = resources["pinot_client"]
            self.llm = resources["llm"]
            self._initialized = True
            return True
        except Exception as e:
            print(f"Infrastructure plugin initialization error: {e}")
            return False

    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """Determine if query is about infrastructure"""
        query_lower = query.lower()

        # Strong patterns
        if any(pattern in query_lower for pattern in ["AB 531", "SB 326", "construction", "facility"]):
            return 0.9

        keyword_matches = sum(1 for kw in self.metadata.keywords if kw in query_lower)
        return min(keyword_matches / 2, 1.0)

    async def execute(self, query: str, context: Dict[str, Any]) -> PluginResponse:
        """Query infrastructure projects"""
        try:
            # Example SQL for infrastructure table (would need to create this)
            sql = """
            SELECT
                project_name,
                county,
                funding_source,
                total_funding,
                status,
                beds_planned,
                completion_date
            FROM bht_infrastructure_projects
            WHERE status IN ('planning', 'construction', 'completed')
            ORDER BY completion_date DESC
            LIMIT 50
            """

            df = self.pinot_client.execute_query(sql)

            return PluginResponse(
                success=True,
                data={
                    "projects": df.to_dict('records'),
                    "total_projects": len(df),
                    "total_funding": df['total_funding'].sum()
                },
                metadata={
                    "query_type": "infrastructure"
                },
                sources=[{
                    "type": "pinot_query",
                    "table": "bht_infrastructure_projects",
                    "rows": len(df)
                }],
                confidence=0.85
            )

        except Exception as e:
            return PluginResponse(
                success=False,
                data={"error": str(e)},
                metadata={},
                sources=[],
                confidence=0.0
            )

    async def get_examples(self) -> List[str]:
        return [
            "Show me all AB 531 projects in progress",
            "What is the total Prop 1 funding allocated?",
            "List new crisis centers under construction",
            "How many treatment beds will be added in Los Angeles?",
            "Show projects by completion date"
        ]
```

### 5. Plugin Configuration File

**File**: `agents/plugins/plugins.yaml`

```yaml
# Plugin Configuration
# Register all available plugins here

plugins:
  # Crisis Triage (Original use case)
  - name: crisis_triage
    enabled: true
    module: agents.plugins.crisis_triage_plugin
    class: CrisisTriagePlugin
    priority: 10  # Higher priority = checked first
    config:
      max_events: 1000
      default_time_window: 60  # minutes

  # Policy Q&A
  - name: policy_qa
    enabled: true
    module: agents.plugins.policy_qa_plugin
    class: PolicyQAPlugin
    priority: 8
    config:
      max_sources: 5
      chroma_collection: "bht_policies"

  # Infrastructure Tracking
  - name: infrastructure_tracking
    enabled: true
    module: agents.plugins.infrastructure_plugin
    class: InfrastructurePlugin
    priority: 7
    config:
      pinot_table: "bht_infrastructure_projects"

  # Licensing & Certification (future)
  - name: licensing
    enabled: false
    module: agents.plugins.licensing_plugin
    class: LicensingPlugin
    priority: 6
    config:
      # To be configured

  # County Portal (future)
  - name: county_portal
    enabled: false
    module: agents.plugins.county_portal_plugin
    class: CountyPortalPlugin
    priority: 5
    config:
      # To be configured
```

### 6. Plugin Loader

**File**: `agents/plugins/loader.py`

```python
"""
Plugin loader - Automatically loads plugins from configuration
"""
import yaml
import importlib
from typing import Dict, Any
from agents.plugins.base_plugin import registry
from agents.utils.pinot_client import PinotClient
from agents.knowledge.knowledge_base import KnowledgeBase
from langchain_openai import ChatOpenAI
from agents.core.config import settings


async def load_plugins(config_path: str = "agents/plugins/plugins.yaml") -> bool:
    """
    Load and initialize all plugins from configuration

    Args:
        config_path: Path to plugins.yaml

    Returns:
        True if all enabled plugins loaded successfully
    """

    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Sort by priority (highest first)
    plugins_config = sorted(
        config['plugins'],
        key=lambda x: x.get('priority', 0),
        reverse=True
    )

    # Prepare shared resources
    shared_resources = {
        "pinot_client": PinotClient(),
        "chroma_client": KnowledgeBase().collection,
        "llm": ChatOpenAI(
            model=settings.agent_model,
            temperature=settings.agent_temperature
        ),
        "config": {}
    }

    # Load each plugin
    success_count = 0
    for plugin_config in plugins_config:
        if not plugin_config.get('enabled', False):
            print(f"⏭️  Skipping disabled plugin: {plugin_config['name']}")
            continue

        try:
            # Import module
            module = importlib.import_module(plugin_config['module'])
            plugin_class = getattr(module, plugin_config['class'])

            # Instantiate plugin
            plugin = plugin_class()

            # Register
            registry.register(plugin)

            # Add plugin-specific config to shared resources
            shared_resources["config"] = plugin_config.get('config', {})

            success_count += 1

        except Exception as e:
            print(f"❌ Failed to load plugin {plugin_config['name']}: {e}")

    # Initialize all plugins
    await registry.initialize_all(shared_resources)

    print(f"\n✅ Loaded {success_count}/{len(plugins_config)} plugins")
    return success_count > 0
```

### 7. Updated API Endpoint

**File**: `api/main.py` (updated)

```python
"""
FastAPI application with plugin support
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.plugins.loader import load_plugins
from agents.plugins.base_plugin import registry

app = FastAPI(
    title="DHCS BHT Multi-Agent API",
    description="Pluggable multi-agent system for behavioral health triage",
    version="2.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Load plugins on startup"""
    success = await load_plugins()
    if not success:
        raise RuntimeError("Failed to load plugins")

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "plugins_loaded": len(registry.plugins),
        "plugins": [p.name for p in registry.get_plugin_info()]
    }

@app.get("/plugins")
async def list_plugins():
    """List all available plugins and their capabilities"""
    plugins = registry.get_plugin_info()
    examples = registry.get_all_examples()

    return {
        "plugins": [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "use_case": p.use_case,
                "capabilities": p.capabilities,
                "examples": examples.get(p.name, [])
            }
            for p in plugins
        ]
    }

class ChatRequest(BaseModel):
    message: str
    context: dict = {}

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint - automatically routes to best plugin
    """
    try:
        response = await registry.route_query(
            query=request.message,
            context=request.context
        )

        return {
            "success": response.success,
            "response": response.data,
            "plugin": response.metadata.get("selected_plugin"),
            "confidence": response.confidence,
            "sources": response.sources,
            "suggestions": response.suggestions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Adding a New Plugin - Step by Step

### Example: Adding BHOATR Reporting Plugin

1. **Create plugin file**: `agents/plugins/bhoatr_plugin.py`

```python
from agents.plugins.base_plugin import BasePlugin, PluginMetadata, PluginResponse
from typing import Dict, Any, List

class BHOATRPlugin(BasePlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="bhoatr_reporting",
            version="1.0.0",
            description="Generate BHOATR reports and analytics",
            author="Your Name",
            use_case="bhoatr",
            capabilities=["generate_report", "analyze_outcomes"],
            required_data_sources=["pinot"],
            keywords=["bhoatr", "report", "outcomes", "accountability", "transparency"]
        )

    async def initialize(self, resources: Dict[str, Any]) -> bool:
        # Initialize resources
        self.pinot_client = resources["pinot_client"]
        return True

    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        # Implement confidence scoring
        if "bhoatr" in query.lower():
            return 0.95
        return 0.0

    async def execute(self, query: str, context: Dict[str, Any]) -> PluginResponse:
        # Implement core logic
        pass

    async def get_examples(self) -> List[str]:
        return [
            "Generate BHOATR report for Q4 2024",
            "Show accountability metrics by county"
        ]
```

2. **Register in `plugins.yaml`**:

```yaml
plugins:
  # ... existing plugins ...

  - name: bhoatr_reporting
    enabled: true
    module: agents.plugins.bhoatr_plugin
    class: BHOATRPlugin
    priority: 7
    config:
      report_template: "quarterly"
```

3. **Test the plugin**:

```bash
# Restart API
docker compose restart agent-api

# Test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate BHOATR report for Q4"}'
```

4. **Done!** No changes to core system needed.

## Benefits of Pluggable Architecture

1. **Isolation**: Bugs in one plugin don't affect others
2. **Easy Testing**: Test plugins independently
3. **Rapid Development**: Add new use cases in hours, not days
4. **Maintainability**: Clear separation of concerns
5. **Reusability**: Share plugins across projects
6. **Versioning**: Each plugin has independent version
7. **Hot Reload**: Enable/disable plugins without restart (future)

## Plugin Development Template

Use this template for new plugins:

```python
# agents/plugins/YOUR_PLUGIN_NAME_plugin.py
from agents.plugins.base_plugin import BasePlugin, PluginMetadata, PluginResponse
from typing import Dict, Any, List

class YourPlugin(BasePlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="your_plugin",
            version="1.0.0",
            description="Brief description",
            author="Your Name",
            use_case="your_use_case",
            capabilities=["capability1", "capability2"],
            required_data_sources=["pinot"],
            keywords=["keyword1", "keyword2"]
        )

    async def initialize(self, resources: Dict[str, Any]) -> bool:
        # Setup resources
        self.pinot_client = resources.get("pinot_client")
        self.llm = resources.get("llm")
        return True

    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        # Return 0.0-1.0 confidence
        query_lower = query.lower()

        # Your logic here
        confidence = 0.0

        return confidence

    async def execute(self, query: str, context: Dict[str, Any]) -> PluginResponse:
        # Your core logic

        return PluginResponse(
            success=True,
            data={"result": "Your data here"},
            metadata={},
            sources=[],
            confidence=1.0
        )

    async def get_examples(self) -> List[str]:
        return [
            "Example query 1",
            "Example query 2"
        ]
```

## Testing Plugins

**File**: `tests/test_plugins.py`

```python
import pytest
from agents.plugins.base_plugin import registry
from agents.plugins.loader import load_plugins

@pytest.mark.asyncio
async def test_plugin_loading():
    """Test all plugins load correctly"""
    success = await load_plugins()
    assert success
    assert len(registry.plugins) > 0

@pytest.mark.asyncio
async def test_plugin_routing():
    """Test query routing"""
    await load_plugins()

    # Test crisis query
    response = await registry.route_query(
        query="How many high-risk events?",
        context={}
    )
    assert response.success
    assert response.metadata["selected_plugin"] == "crisis_triage"

    # Test policy query
    response = await registry.route_query(
        query="What is Proposition 1?",
        context={}
    )
    assert response.success
    assert response.metadata["selected_plugin"] == "policy_qa"
```

## Next Steps

1. Implement base plugin system
2. Refactor existing crisis triage code into plugin
3. Implement policy Q&A plugin based on PDF documents
4. Test plugin routing
5. Add infrastructure tracking plugin
6. Document plugin API for external developers
