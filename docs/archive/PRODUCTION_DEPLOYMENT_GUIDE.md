# Production Deployment & Monitoring Guide

## Table of Contents
1. [Cloud Deployment Requirements](#cloud-deployment-requirements)
2. [Model Architecture & Training](#model-architecture--training)
3. [Monitoring Bias & Fairness](#monitoring-bias--fairness)
4. [Prompt Engineering & Management](#prompt-engineering--management)
5. [Evaluation: Recall & Precision](#evaluation-recall--precision)
6. [Agent Architecture: ReAct vs Chain-of-Thought](#agent-architecture-react-vs-chain-of-thought)

---

## 1. Cloud Deployment Requirements

### What I Need From You:

#### A. AWS Account Setup (Recommended)
```bash
# 1. AWS Account credentials
- AWS Account ID
- IAM user with administrator access
- AWS CLI configured locally

# 2. Budget approval
- Development/Staging: ~$300-400/month
- Production: ~$1,200-1,500/month (including OpenAI API)
```

#### B. OpenAI API Configuration
```bash
# Already have:
✅ OpenAI API key (currently using gpt-4o-mini)

# Recommendations:
- Upgrade to gpt-4o for production (better accuracy)
- Set up usage limits and alerts
- Create separate keys for dev/staging/prod
```

#### C. Domain & SSL (Optional but Recommended)
```bash
# For production dashboard:
- Domain name (e.g., dhcs-bht-ai.ca.gov)
- SSL certificate (can use AWS Certificate Manager for free)
```

#### D. Data Privacy & Compliance
```bash
# Before using real PHI data:
- [ ] HIPAA compliance review
- [ ] Business Associate Agreement (BAA) with AWS
- [ ] BAA with OpenAI (requires Enterprise plan)
- [ ] Data encryption requirements documented
- [ ] Audit logging requirements defined
```

### Deployment Steps (AWS ECS - Recommended):

#### Step 1: Prepare AWS Infrastructure (30-60 minutes)
```bash
cd /Users/raj/dhcs-intake-lab

# 1. Create ECR repositories
aws ecr create-repository --repository-name dhcs-bht/agent-api
aws ecr create-repository --repository-name dhcs-bht/dashboard
aws ecr create-repository --repository-name dhcs-bht/generator

# 2. Store OpenAI API key in Secrets Manager
aws secretsmanager create-secret \
  --name dhcs-bht/openai-api-key \
  --secret-string "$OPENAI_API_KEY"

# 3. Create VPC and networking (optional - use default VPC for demo)
```

#### Step 2: Build and Push Docker Images (15-20 minutes)
```bash
cd deployment/aws

# Set your AWS account ID
export AWS_ACCOUNT_ID="your-account-id"
export AWS_REGION="us-west-2"  # Or your preferred region

# Build and push
./build_and_push.sh
```

#### Step 3: Deploy to ECS (20-30 minutes)
```bash
# Option A: Use provided CloudFormation template
aws cloudformation create-stack \
  --stack-name dhcs-bht-system \
  --template-body file://cloudformation/ecs-stack.yaml \
  --parameters ParameterKey=OpenAIKeySecretArn,ParameterValue=<secret-arn>

# Option B: Use Terraform (if you prefer)
cd deployment/terraform
terraform init
terraform plan
terraform apply
```

#### Step 4: Verify Deployment (5-10 minutes)
```bash
# Get load balancer URL
aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?contains(LoadBalancerName, 'dhcs-bht')].DNSName"

# Test API
curl https://<your-lb-url>/health

# Access dashboard
open https://<your-lb-url>:8501
```

### Alternative: Kubernetes Deployment

If you prefer Kubernetes (EKS, GKE, or AKS):

```bash
cd deployment/kubernetes

# 1. Create namespace and secrets
kubectl create namespace dhcs-bht
kubectl create secret generic openai-api-key \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  -n dhcs-bht

# 2. Deploy all services
kubectl apply -f . -n dhcs-bht

# 3. Get load balancer IP
kubectl get svc -n dhcs-bht
```

---

## 2. Model Architecture & Training

### Do You Need to Train Models? **NO** ✅

**Current Architecture**: Uses **pre-trained foundation models** (GPT-4o-mini) via API
- ✅ No training required
- ✅ No ML infrastructure needed
- ✅ No labeled data collection needed
- ✅ Instant updates when OpenAI releases new models

### Why No Training?

```
Traditional ML Pipeline (Not Used):
┌──────────────┐     ┌──────────┐     ┌─────────┐     ┌────────┐
│ Collect Data │ →   │  Label   │ →   │  Train  │ →   │ Deploy │
│  (months)    │     │ (weeks)  │     │ (days)  │     │ (hard) │
└──────────────┘     └──────────┘     └─────────┘     └────────┘

Our Approach (Prompt Engineering):
┌─────────────┐     ┌──────────┐     ┌────────┐
│ Use GPT-4o  │ →   │  Prompt  │ →   │ Deploy │
│  (instant)  │     │ Engineer │     │ (easy) │
└─────────────┘     └──────────┘     └────────┘
```

### What You Control Instead:

1. **Prompts** - How you instruct the AI (see section below)
2. **Context** - What data you provide (real-time from Pinot)
3. **Architecture** - How agents collaborate (LangGraph orchestration)
4. **Guardrails** - Validation, filtering, constraints

### When You MIGHT Fine-tune (Optional Future):

```python
# Only if you need to:
# 1. Handle highly specialized DHCS terminology
# 2. Improve response consistency
# 3. Reduce costs (fine-tuned models are cheaper)
# 4. Add domain-specific capabilities

# Example fine-tuning use case:
# - Train on 1000+ examples of DHCS crisis call transcripts
# - Model learns California-specific behavioral health patterns
# - Cost: ~$500-2000 one-time, then cheaper inference
```

---

## 3. Monitoring Bias & Fairness

### Multi-Level Monitoring Strategy:

#### Level 1: Data Input Monitoring

**Monitor synthetic data distribution:**
```python
# Add to generator/producer.py monitoring

from collections import Counter
import json

class BiasMonitor:
    def __init__(self):
        self.event_counts = {
            'county': Counter(),
            'language': Counter(),
            'risk_level': Counter(),
            'channel': Counter(),
            'presenting_problem': Counter()
        }
    
    def track_event(self, event):
        """Track event for bias detection"""
        for field in self.event_counts.keys():
            if field in event:
                self.event_counts[field][event[field]] += 1
    
    def get_distribution_stats(self):
        """Calculate distribution statistics"""
        stats = {}
        for field, counts in self.event_counts.items():
            total = sum(counts.values())
            distribution = {k: v/total for k, v in counts.items()}
            stats[field] = {
                'distribution': distribution,
                'entropy': self._calculate_entropy(distribution),
                'warning': self._check_bias(distribution)
            }
        return stats
    
    def _calculate_entropy(self, dist):
        """Shannon entropy - higher is more balanced"""
        import math
        return -sum(p * math.log2(p) for p in dist.values() if p > 0)
    
    def _check_bias(self, dist):
        """Flag if any category is over-represented"""
        max_ratio = max(dist.values())
        expected = 1.0 / len(dist)
        if max_ratio > expected * 2:
            return f"Over-representation detected: {max_ratio:.1%} vs expected {expected:.1%}"
        return None
```

**Metrics to track:**
- County distribution (ensure no county is ignored)
- Language access (Spanish, Chinese, Vietnamese, etc.)
- Risk level distribution (high vs imminent)
- Channel usage (988, mobile team, ER, walk-in)

#### Level 2: Agent Response Monitoring

**Track AI agent decisions:**
```python
# Add to agents/core/base_agent.py

class AgentMetrics:
    """Track agent performance and bias metrics"""
    
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_response_time': [],
            'queries_by_intent': Counter(),
            
            # Bias tracking
            'queries_by_county': Counter(),
            'queries_by_language': Counter(),
            'high_risk_identified': 0,
            'false_positives': 0,
            'false_negatives': 0,
        }
    
    def log_query(self, query_data):
        """Log query with metadata for bias analysis"""
        self.metrics['total_queries'] += 1
        
        # Extract demographic info
        if 'county' in query_data:
            self.metrics['queries_by_county'][query_data['county']] += 1
        if 'language' in query_data:
            self.metrics['queries_by_language'][query_data['language']] += 1
    
    def calculate_fairness_metrics(self):
        """Calculate statistical parity and equalized odds"""
        # Statistical Parity: P(prediction=1 | group=A) ≈ P(prediction=1 | group=B)
        # Equalized Odds: P(prediction=1 | Y=1, group=A) ≈ P(prediction=1 | Y=1, group=B)
        
        return {
            'county_coverage': len(self.metrics['queries_by_county']) / 6,  # 6 counties
            'language_coverage': len(self.metrics['queries_by_language']) / 5,  # 5 languages
            'recall': self._calculate_recall(),
            'precision': self._calculate_precision(),
            'f1_score': self._calculate_f1()
        }
```

#### Level 3: Outcome Monitoring

**Track real-world impact:**
```python
# New file: agents/monitoring/outcome_tracker.py

class OutcomeTracker:
    """Track outcomes to detect bias in real-world impact"""
    
    def __init__(self):
        self.outcomes = {
            'by_county': {},
            'by_language': {},
            'by_risk_level': {},
            'by_channel': {}
        }
    
    def track_outcome(self, event_id, outcome_type, metadata):
        """
        Outcome types:
        - 'triage_priority': What priority was assigned
        - 'response_time': How long until intervention
        - 'resolution': Was crisis resolved successfully
        - 'escalation': Did situation escalate
        """
        for dimension in ['county', 'language', 'risk_level', 'channel']:
            if dimension in metadata:
                value = metadata[dimension]
                if value not in self.outcomes[f'by_{dimension}']:
                    self.outcomes[f'by_{dimension}'][value] = []
                
                self.outcomes[f'by_{dimension}'][value].append({
                    'event_id': event_id,
                    'outcome_type': outcome_type,
                    'timestamp': metadata.get('timestamp')
                })
    
    def detect_disparate_impact(self, protected_attribute='county'):
        """
        Detect disparate impact (80% rule):
        Outcome rate for group A / Outcome rate for group B >= 0.8
        """
        outcomes_by_group = self.outcomes[f'by_{protected_attribute}']
        
        results = {}
        for group, outcomes in outcomes_by_group.items():
            positive_outcomes = sum(1 for o in outcomes if o['outcome_type'] == 'resolution')
            outcome_rate = positive_outcomes / len(outcomes) if outcomes else 0
            results[group] = outcome_rate
        
        # Check 80% rule
        max_rate = max(results.values())
        min_rate = min(results.values())
        disparate_impact_ratio = min_rate / max_rate if max_rate > 0 else 0
        
        return {
            'outcome_rates': results,
            'disparate_impact_ratio': disparate_impact_ratio,
            'passes_80_percent_rule': disparate_impact_ratio >= 0.8,
            'protected_attribute': protected_attribute
        }
```

#### Level 4: Prometheus + Grafana Dashboard

**Setup monitoring stack:**
```yaml
# deployment/monitoring/docker-compose.monitoring.yml

version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
  
  # Export metrics from your app
  agent-api:
    # Add prometheus metrics endpoint
    environment:
      - PROMETHEUS_ENABLED=true

volumes:
  prometheus_data:
  grafana_data:
```

**Add metrics to FastAPI:**
```python
# Add to api/main.py

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Define metrics
query_counter = Counter('agent_queries_total', 'Total agent queries', ['agent', 'intent'])
query_duration = Histogram('agent_query_duration_seconds', 'Query duration', ['agent'])
bias_gauge = Gauge('bias_metrics', 'Bias metrics', ['dimension', 'value'])

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

# In each endpoint:
@app.post("/chat")
async def chat(request: ChatRequest):
    with query_duration.labels(agent='orchestrator').time():
        result = await process_chat(request)
        query_counter.labels(agent='orchestrator', intent=result['intent']).inc()
    return result
```

### Bias Detection Alerts

```python
# agents/monitoring/bias_alerts.py

class BiasAlertSystem:
    """Alert on potential bias issues"""
    
    THRESHOLDS = {
        'county_imbalance': 0.4,  # Alert if one county gets >40% of queries
        'language_coverage': 0.8,  # Alert if <80% of languages are served
        'disparate_impact': 0.8,  # 80% rule for outcome fairness
        'false_negative_rate': 0.1,  # Alert if missing >10% of high-risk
    }
    
    def check_for_bias(self, metrics):
        """Check metrics against thresholds"""
        alerts = []
        
        # Check county distribution
        if max(metrics['county_dist'].values()) > self.THRESHOLDS['county_imbalance']:
            alerts.append({
                'type': 'COUNTY_IMBALANCE',
                'severity': 'HIGH',
                'message': 'One county is receiving disproportionate attention'
            })
        
        # Check language coverage
        if metrics['language_coverage'] < self.THRESHOLDS['language_coverage']:
            alerts.append({
                'type': 'LANGUAGE_BIAS',
                'severity': 'CRITICAL',
                'message': 'Non-English languages may be underserved'
            })
        
        return alerts
    
    def send_alert(self, alert):
        """Send alert via Slack/email/PagerDuty"""
        # Implementation depends on your alerting system
        pass
```

---

## 4. Prompt Engineering & Management

### Current Architecture: Prompt-Based (Not Fine-Tuned)

Your system uses **prompt engineering** - carefully crafted instructions to guide GPT-4o-mini.

#### Where Prompts Are Used:

1. **Query Agent** ([agents/core/query_agent.py](agents/core/query_agent.py:113-127))
```python
system_message = f"""You are an expert SQL query generator for Apache Pinot.
Your task is to convert natural language questions into valid Pinot SQL queries.

Schema Information:
{schema_info}

Rules:
1. Always generate syntactically correct Pinot SQL
2. Use appropriate aggregations and filters
3. Include reasonable time windows (default to last 60 minutes)
...
"""
```

2. **Analytics Agent** ([agents/core/analytics_agent.py](agents/core/analytics_agent.py))
3. **Triage Agent** ([agents/core/triage_agent.py](agents/core/triage_agent.py))
4. **Recommendations Agent** ([agents/core/recommendations_agent.py](agents/core/recommendations_agent.py))

### Prompt Management Strategy:

#### Option 1: Version Control (Current - Simple)
```bash
# Prompts are in code
agents/core/query_agent.py:113-127
agents/core/analytics_agent.py:XX-YY

# Pros: Simple, version controlled with code
# Cons: Requires code deploy to change
```

#### Option 2: External Configuration (Recommended)
```python
# agents/prompts/prompts.yaml

query_agent:
  version: "1.2.0"
  system_prompt: |
    You are an expert SQL query generator for Apache Pinot.
    Your task is to convert natural language questions into valid Pinot SQL queries.
    
    Schema Information:
    {schema_info}
    
    Rules:
    1. Always generate syntactically correct Pinot SQL
    2. Use appropriate aggregations and filters
    ...
  
  user_prompt_template: |
    Question: {question}
    
    Generate a Pinot SQL query to answer this question.

analytics_agent:
  version: "1.0.0"
  system_prompt: |
    You are a behavioral health crisis analytics expert...
```

**Load prompts dynamically:**
```python
# agents/core/prompt_manager.py

import yaml
from typing import Dict
import os

class PromptManager:
    """Manage prompts with versioning and A/B testing"""
    
    def __init__(self, prompts_file="agents/prompts/prompts.yaml"):
        with open(prompts_file) as f:
            self.prompts = yaml.safe_load(f)
        
        # Load from environment or feature flags
        self.prompt_version = os.getenv("PROMPT_VERSION", "default")
    
    def get_prompt(self, agent_name: str, prompt_type: str = "system_prompt") -> str:
        """Get prompt for agent"""
        agent_prompts = self.prompts.get(agent_name, {})
        return agent_prompts.get(prompt_type, "")
    
    def get_versioned_prompt(self, agent_name: str, version: str = None):
        """Get specific version of prompt for A/B testing"""
        version = version or self.prompt_version
        # Implementation for versioned prompts
        pass

# Use in agents:
from agents.core.prompt_manager import PromptManager

class QueryAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.prompt_mgr = PromptManager()
    
    def _generate_sql(self, question: str) -> str:
        system_message = self.prompt_mgr.get_prompt("query_agent", "system_prompt")
        # Format with schema_info
        system_message = system_message.format(schema_info=self.schema_info)
        ...
```

#### Option 3: LangSmith/LangChain Hub (Production)
```python
# Use LangChain's prompt versioning

from langchain import hub

# Pull prompts from hub
query_prompt = hub.pull("dhcs/query-agent-v1")

# Pros: 
# - Versioning
# - A/B testing
# - Analytics
# - No code deploy needed
```

### Prompt Versioning Strategy:

```python
# agents/monitoring/prompt_experiments.py

class PromptExperiment:
    """A/B test different prompts"""
    
    def __init__(self):
        self.variants = {
            'control': PromptManager().get_prompt('query_agent'),
            'variant_a': self._load_variant('query_agent_v2'),
            'variant_b': self._load_variant('query_agent_v3')
        }
        self.metrics = {variant: [] for variant in self.variants}
    
    def get_prompt(self, user_id: str) -> tuple[str, str]:
        """Get prompt variant for user (consistent hashing)"""
        variant = self._assign_variant(user_id)
        return variant, self.variants[variant]
    
    def record_outcome(self, variant: str, success: bool, latency: float):
        """Record experiment outcome"""
        self.metrics[variant].append({
            'success': success,
            'latency': latency,
            'timestamp': datetime.now()
        })
    
    def analyze_results(self):
        """Statistical analysis of variants"""
        # t-test, confidence intervals, etc.
        pass
```

---

## 5. Evaluation: Recall & Precision

### Current System: Imbalanced Toward Recall

**Triage Use Case**: Better to flag a false positive (low-risk as high-risk) than miss a true high-risk case.

```
Confusion Matrix for Triage:

                    Predicted High Risk    Predicted Low Risk
Actual High Risk          TP                     FN ← BAD!
Actual Low Risk           FP                     TN
```

### Metrics to Track:

```python
# agents/evaluation/metrics.py

class PerformanceMetrics:
    """Track recall, precision, F1 for agent decisions"""
    
    def __init__(self):
        self.true_positives = 0
        self.false_positives = 0
        self.true_negatives = 0
        self.false_negatives = 0
    
    @property
    def recall(self) -> float:
        """Sensitivity: TP / (TP + FN)"""
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator > 0 else 0
    
    @property
    def precision(self) -> float:
        """Positive Predictive Value: TP / (TP + FP)"""
        denominator = self.true_positives + self.false_positives
        return self.true_positives / denominator if denominator > 0 else 0
    
    @property
    def f1_score(self) -> float:
        """Harmonic mean of precision and recall"""
        p, r = self.precision, self.recall
        return 2 * (p * r) / (p + r) if (p + r) > 0 else 0
    
    @property
    def specificity(self) -> float:
        """True Negative Rate: TN / (TN + FP)"""
        denominator = self.true_negatives + self.false_positives
        return self.true_negatives / denominator if denominator > 0 else 0
    
    def f_beta_score(self, beta: float = 2.0) -> float:
        """
        F-beta score: weighted harmonic mean
        beta > 1: weight recall more (prioritize catching high-risk)
        beta < 1: weight precision more (reduce false alarms)
        
        For crisis triage, use beta=2 to prioritize recall
        """
        p, r = self.precision, self.recall
        beta_sq = beta ** 2
        numerator = (1 + beta_sq) * p * r
        denominator = (beta_sq * p) + r
        return numerator / denominator if denominator > 0 else 0
```

### Evaluation Pipeline:

```python
# agents/evaluation/evaluator.py

class AgentEvaluator:
    """Evaluate agent performance with ground truth"""
    
    def __init__(self, agent, test_cases):
        self.agent = agent
        self.test_cases = test_cases
        self.metrics = PerformanceMetrics()
    
    def evaluate(self):
        """Run evaluation on test cases"""
        results = []
        
        for test_case in self.test_cases:
            # Get agent prediction
            prediction = self.agent.execute(test_case['input'])
            
            # Compare to ground truth
            is_correct = self._compare(prediction, test_case['expected'])
            
            # Update metrics
            self._update_metrics(
                predicted=prediction['risk_level'],
                actual=test_case['expected']['risk_level']
            )
            
            results.append({
                'test_case': test_case,
                'prediction': prediction,
                'correct': is_correct
            })
        
        return {
            'results': results,
            'metrics': {
                'recall': self.metrics.recall,
                'precision': self.metrics.precision,
                'f1_score': self.metrics.f1_score,
                'f2_score': self.metrics.f_beta_score(beta=2.0),  # Favor recall
            }
        }
    
    def _update_metrics(self, predicted, actual):
        """Update confusion matrix"""
        if actual == 'high' and predicted == 'high':
            self.metrics.true_positives += 1
        elif actual == 'high' and predicted != 'high':
            self.metrics.false_negatives += 1  # DANGEROUS - missed high-risk
        elif actual != 'high' and predicted == 'high':
            self.metrics.false_positives += 1  # Acceptable - false alarm
        else:
            self.metrics.true_negatives += 1
```

### Create Test Dataset:

```python
# agents/evaluation/test_cases.py

TEST_CASES = [
    {
        'input': {
            'event_id': 'test-001',
            'risk_level': 'imminent',
            'suicidal_ideation': True,
            'substance_use': True,
            'prior_contacts_90d': 5
        },
        'expected': {
            'risk_level': 'imminent',
            'priority_score': 140,  # Should be high priority
            'recommended_action': 'mobile_team_dispatch'
        }
    },
    # Add 100+ test cases covering:
    # - Edge cases
    # - Different counties
    # - Different languages
    # - Various risk levels
    # - Different presenting problems
]
```

### Continuous Evaluation:

```python
# agents/evaluation/continuous_eval.py

class ContinuousEvaluator:
    """Continuously evaluate in production"""
    
    def __init__(self):
        self.evaluator = AgentEvaluator(...)
        self.schedule = "daily"  # Or hourly
    
    def run_evaluation(self):
        """Run daily evaluation"""
        results = self.evaluator.evaluate()
        
        # Check for degradation
        if results['metrics']['recall'] < 0.95:  # 95% recall threshold
            self._send_alert("RECALL_DEGRADATION", results['metrics'])
        
        if results['metrics']['f2_score'] < 0.90:
            self._send_alert("PERFORMANCE_DEGRADATION", results['metrics'])
        
        # Store results
        self._store_results(results)
    
    def _send_alert(self, alert_type, metrics):
        """Alert on performance issues"""
        # Send to Slack, PagerDuty, etc.
        pass
```

---

## 6. Agent Architecture: ReAct vs Chain-of-Thought

### Current Architecture: **Hybrid**

Your system combines multiple patterns:

#### 1. **ReAct Pattern** (Reasoning + Acting)

Used in: **Orchestrator Agent**

```python
# Simplified ReAct loop in orchestrator

def process_query(user_input):
    # Thought: What is the user asking for?
    intent = classify_intent(user_input)
    
    # Action: Route to appropriate agent
    if intent == "query":
        result = query_agent.execute(user_input)
    elif intent == "triage":
        result = triage_agent.execute(user_input)
    
    # Observation: What did the agent return?
    # (implicit in result variable)
    
    # Thought: Do I need more information?
    if result['needs_more_context']:
        # Action: Call another agent
        additional_info = analytics_agent.get_context()
        result = combine(result, additional_info)
    
    # Final response
    return generate_response(result)
```

#### 2. **Chain-of-Thought (CoT)**

Used in: **Individual Agents**

```python
# Query Agent uses CoT for SQL generation

def generate_sql(question):
    prompt = f"""
    Think step by step to generate the SQL query:
    
    1. What tables are needed? → dhcs_crisis_intake
    2. What columns to select? → county, COUNT(*)
    3. What filters to apply? → risk_level IN ('high', 'imminent')
    4. What time range? → last hour (now() - 3600000)
    5. How to group results? → GROUP BY county
    6. How to sort? → ORDER BY COUNT(*) DESC
    
    Now generate the complete SQL query:
    """
    
    # Model generates SQL following the chain of thought
    return llm.generate(prompt)
```

#### 3. **LangGraph State Machine**

Your orchestrator uses **LangGraph** for agent coordination:

```python
# Conceptual flow (already implemented in orchestrator.py)

from langgraph.graph import StateGraph

# Define states
class AgentState(TypedDict):
    user_input: str
    intent: str
    query_result: Optional[Dict]
    analytics_result: Optional[Dict]
    triage_result: Optional[Dict]
    final_response: str

# Define graph
workflow = StateGraph(AgentState)

# Add nodes (agents)
workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("query_agent", query_agent_node)
workflow.add_node("analytics_agent", analytics_agent_node)
workflow.add_node("generate_response", response_node)

# Add edges (transitions)
workflow.add_edge("classify_intent", "query_agent", condition=lambda s: s['intent'] == 'query')
workflow.add_edge("classify_intent", "triage_agent", condition=lambda s: s['intent'] == 'triage')

# This gives you:
# ✅ State management
# ✅ Conditional routing
# ✅ Parallel agent execution
# ✅ Error handling and retries
```

### Balancing Recall vs Precision

#### Strategy 1: Threshold Tuning

```python
class TriageAgent:
    def __init__(self, recall_target=0.95):
        self.recall_target = recall_target
        self.threshold = self._calculate_threshold()
    
    def _calculate_threshold(self):
        """
        Lower threshold = Higher recall (catch more cases)
        Higher threshold = Higher precision (fewer false alarms)
        
        For crisis triage: prioritize recall
        """
        if self.recall_target >= 0.95:
            return 50  # Low threshold - flag more cases
        elif self.recall_target >= 0.90:
            return 70
        else:
            return 90  # High threshold - only obvious cases
    
    def calculate_risk_score(self, event):
        """Calculate risk score"""
        score = 0
        
        if event['risk_level'] == 'imminent':
            score += 100
        elif event['risk_level'] == 'high':
            score += 50
        
        if event['suicidal_ideation']:
            score += 30
        if event['homicidal_ideation']:
            score += 40
        if event['substance_use']:
            score += 10
        
        # Compare to threshold
        is_high_priority = score >= self.threshold
        
        return {
            'score': score,
            'high_priority': is_high_priority,
            'confidence': self._calculate_confidence(score)
        }
```

#### Strategy 2: Ensemble Methods

```python
class EnsembleTriageAgent:
    """Use multiple agents and aggregate results"""
    
    def __init__(self):
        # Multiple triage strategies
        self.rule_based_agent = RuleBasedTriageAgent()
        self.ml_based_agent = MLTriageAgent()
        self.llm_based_agent = LLMTriageAgent()
    
    def triage(self, event):
        """Get predictions from all agents"""
        predictions = [
            self.rule_based_agent.triage(event),
            self.ml_based_agent.triage(event),
            self.llm_based_agent.triage(event)
        ]
        
        # Voting: If 2/3 say high-risk, flag as high-risk
        high_risk_votes = sum(1 for p in predictions if p['high_risk'])
        
        return {
            'high_risk': high_risk_votes >= 2,
            'confidence': high_risk_votes / 3,
            'individual_predictions': predictions
        }
```

#### Strategy 3: Human-in-the-Loop

```python
class HumanInLoopTriage:
    """Flag uncertain cases for human review"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def triage(self, event):
        prediction = self.ai_triage(event)
        
        if prediction['confidence'] < self.confidence_threshold:
            # Low confidence - flag for human review
            return {
                'automated_decision': False,
                'requires_human_review': True,
                'ai_suggestion': prediction,
                'reason': 'Low confidence'
            }
        
        return prediction
```

---

## Summary: What You Need to Do

### Immediate (This Week):

1. **✅ System is working locally** (Done!)
2. **Decide on deployment target**: AWS ECS (recommended) or Kubernetes
3. **Set up AWS account** (if using AWS)
4. **Create OpenAI production API key** with higher rate limits

### Short-term (Next 2-4 Weeks):

1. **Deploy to cloud** (follow steps above)
2. **Implement monitoring** (Prometheus + Grafana)
3. **Set up bias monitoring** (use code examples above)
4. **Create evaluation test cases** (100+ examples)
5. **Establish alert thresholds**

### Medium-term (1-3 Months):

1. **Prompt versioning** (move prompts to YAML)
2. **A/B testing framework** for prompts
3. **Continuous evaluation pipeline**
4. **Bias audits** (monthly)
5. **Performance optimization**

### Long-term (3-6 Months):

1. **Consider fine-tuning** (if needed for cost/performance)
2. **Multi-model deployment** (GPT-4o vs GPT-4o-mini)
3. **Advanced orchestration** (more sophisticated agent collaboration)
4. **Integration with real DHCS systems**
5. **HIPAA compliance audit** (before using real PHI)

---

## Key Takeaways:

1. **No training needed** - Use prompt engineering, not fine-tuning
2. **Monitor at multiple levels** - Data, agents, outcomes
3. **Prioritize recall** for crisis triage (better safe than sorry)
4. **Use F2 score** (weighted toward recall) instead of F1
5. **Implement bias monitoring** from day one
6. **Version your prompts** like code
7. **Continuous evaluation** in production
8. **Human-in-the-loop** for low-confidence cases

