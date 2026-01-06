# Quick Answers to Your Questions

## 1. What do you need from me to deploy to cloud?

### Immediate Requirements:
- **AWS Account** with admin access (or equivalent for GCP/Azure)
- **AWS Account ID** and region preference
- **Budget Approval**: ~$1,500-2,000/month for production
- **Decision**: AWS ECS (easier) or Kubernetes (more flexible)?

### Optional but Recommended:
- Custom domain name (e.g., dhcs-bht-ai.ca.gov)
- OpenAI production API key (upgrade from current key)

### I'll Handle:
- Creating deployment scripts (already done in `deployment/` folder)
- Docker image builds
- Infrastructure setup commands
- Monitoring configuration
- Documentation for your team

**Timeline**: 1-2 days to deploy to cloud once you provide AWS credentials

---

## 2. How do we monitor weights and bias at every level?

### Multi-Level Monitoring Strategy:

#### **Level 1: Input Data (Generator)**
```python
Monitor:
- County distribution (equal across 6 counties?)
- Language distribution (English, Spanish, Chinese, etc.)
- Risk level distribution (balanced?)
- Channel usage (988, mobile team, ER, walk-in)

Alert if: Any category >40% or <10% of total
```

#### **Level 2: Agent Decisions (Runtime)**
```python
Monitor:
- Query routing patterns (which counties get more queries?)
- Triage score distribution (fair across demographics?)
- Response times by group
- Recommendation types by county/language

Alert if: Disparate impact detected (80% rule violated)
```

#### **Level 3: Outcomes (Production)**
```python
Monitor:
- Resolution success rates by county
- Escalation rates by language
- Intervention times by channel
- False negative rates (missed high-risk cases)

Alert if: One group has significantly worse outcomes
```

#### **Level 4: Dashboards (Grafana)**
```
Real-time metrics:
- Requests per county per hour
- Average triage score by demographic
- API error rates by endpoint
- Model confidence distribution

Daily reports:
- Bias metrics summary
- Performance degradation alerts
- Cost analysis
```

**Implementation**: Code examples provided in [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md#monitoring-bias--fairness)

---

## 3. Do we have to train the model?

### **NO** ✅ No Training Required

**Current Approach**: Use pre-trained GPT-4o-mini via API

**Why no training?**
- Foundation models (GPT-4o) are already trained on trillion of tokens
- Prompt engineering is faster and cheaper than fine-tuning
- Can iterate in minutes instead of weeks
- No need for labeled datasets
- No GPU infrastructure needed

**When you MIGHT fine-tune (optional, 6+ months from now):**
- To reduce costs (fine-tuned models have cheaper inference)
- To add highly specialized DHCS terminology
- If you collect 10k+ labeled examples from production
- To run offline without API calls

**Current costs:**
- Training: $0
- Inference: ~$0.001/query with GPT-4o-mini
- Total: API usage only (~$500-1000/month)

---

## 4. How do we handle prompts?

### Current Implementation:
Prompts are embedded in agent code:
- [agents/core/query_agent.py:113-127](agents/core/query_agent.py#L113-L127)
- [agents/core/triage_agent.py](agents/core/triage_agent.py)
- [agents/core/recommendations_agent.py](agents/core/recommendations_agent.py)

### Recommended Approach (Production):

#### Option A: YAML Configuration (Simple)
```yaml
# agents/prompts/prompts.yaml
query_agent:
  version: "1.2.0"
  system_prompt: |
    You are an expert SQL query generator for Apache Pinot...
  temperature: 0.7
  max_tokens: 500
```

#### Option B: LangSmith (Advanced)
```python
from langchain import hub

# Pull versioned prompts from cloud
prompt = hub.pull("dhcs/query-agent-v1")

# Benefits:
# - Version control
# - A/B testing
# - Analytics on prompt performance
# - No code deploys to change prompts
```

### Prompt Versioning Strategy:
1. **Version all prompts** (v1.0, v1.1, v2.0)
2. **A/B test changes** (50% get old prompt, 50% get new)
3. **Measure performance** (accuracy, latency, user satisfaction)
4. **Rollback if needed** (instant revert to previous version)

**Examples provided in**: [PRODUCTION_DEPLOYMENT_GUIDE.md#prompt-engineering--management](PRODUCTION_DEPLOYMENT_GUIDE.md#prompt-engineering--management)

---

## 5. Is this system based on ReAct + Chain of Thoughts?

### **YES** ✅ Hybrid Approach

Your system uses **both patterns**:

### **ReAct Pattern** (Orchestrator Level)
```
User Query → ORCHESTRATOR:
1. THOUGHT: "User wants data about counties"
2. ACTION: Route to Query Agent
3. OBSERVATION: Query Agent returns SQL results
4. THOUGHT: "Need more context on trends"
5. ACTION: Call Analytics Agent
6. OBSERVATION: Got trend analysis
7. THOUGHT: "Combine both results"
8. ACTION: Generate final response
```

**Where**: `agents/core/orchestrator.py` (LangGraph state machine)

### **Chain-of-Thought** (Individual Agents)
```
Query Agent generates SQL step-by-step:
1. What table? → dhcs_crisis_intake
2. What columns? → county, COUNT(*)
3. What filters? → risk_level='high'
4. Time range? → last hour
5. Grouping? → GROUP BY county
6. Final SQL: SELECT county, COUNT(*) FROM...
```

**Where**: Each agent's prompt includes "think step-by-step" instructions

### **LangGraph State Machine**
```python
# Orchestrator uses state machine for complex workflows

State = {
    'user_input': str,
    'intent': str,
    'query_result': dict,
    'analytics_result': dict,
    'final_response': str
}

Workflow:
classify_intent → route_to_agent → execute → combine → respond
```

**Why this architecture?**
- **ReAct**: Flexible, can call multiple agents, handles complex workflows
- **CoT**: Improves reasoning quality for individual tasks
- **LangGraph**: Manages state, enables conditional logic, supports parallel execution

---

## 6. How do we balance recall and precision?

### **Current Strategy: Prioritize Recall (95%+)**

For crisis triage, **false negatives are dangerous** (missing a high-risk case), so we optimize for recall:

### Metrics Hierarchy:
```
Primary:   F2 Score (weights recall 2x more than precision)
Secondary: Recall (target: >95%)
Tertiary:  Precision (target: >70%)

F2 = (5 * Precision * Recall) / (4 * Precision + Recall)
```

### Implementation Strategies:

#### 1. **Lower Threshold**
```python
class TriageAgent:
    def __init__(self):
        # Low threshold = catch more cases
        self.high_risk_threshold = 50  # Instead of 70
    
    def is_high_priority(self, score):
        return score >= self.high_risk_threshold
```

#### 2. **Conservative Risk Scoring**
```python
# Add extra points for any red flags
score += 100 if risk_level == 'imminent' else 0
score += 50 if risk_level == 'high' else 0
score += 30 if suicidal_ideation else 0
score += 40 if homicidal_ideation else 0
score += 10 if substance_use else 0

# Better to over-flag than under-flag
```

#### 3. **Ensemble Methods**
```python
# Get predictions from multiple approaches
rule_based_prediction = rule_based_triage(event)
ml_prediction = ml_triage(event)
llm_prediction = llm_triage(event)

# Flag as high-risk if 2/3 agree
high_risk = sum([rule_based, ml, llm]) >= 2
```

#### 4. **Human-in-the-Loop**
```python
if confidence < 0.7:
    return {
        'decision': 'HUMAN_REVIEW_REQUIRED',
        'ai_suggestion': prediction,
        'confidence': confidence
    }
```

### Continuous Evaluation:
```python
# Monitor in production
if recall < 0.95:
    alert("RECALL DROP DETECTED - missed high-risk cases")
    
if f2_score < 0.90:
    alert("PERFORMANCE DEGRADATION")

# Weekly review:
# - Analyze false negatives (highest priority)
# - Adjust thresholds if needed
# - Update prompts to reduce misses
```

**Full implementation**: [PRODUCTION_DEPLOYMENT_GUIDE.md#evaluation-recall--precision](PRODUCTION_DEPLOYMENT_GUIDE.md#evaluation-recall--precision)

---

## Summary: Your Action Items

### This Week:
1. ✅ **Review documentation** (3 new files created)
   - [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md) - Comprehensive guide
   - [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) - Design decisions
   - [QUICK_ANSWERS.md](QUICK_ANSWERS.md) - This file

2. ✅ **Get AWS credentials** (if deploying to cloud)
   - AWS Account ID
   - IAM user with admin access
   - Preferred region (e.g., us-west-2)

3. ✅ **Approve budget** (~$1,500-2,000/month for production)

### Next Week:
1. Deploy to AWS dev environment (I'll guide you step-by-step)
2. Set up monitoring (Prometheus + Grafana)
3. Implement bias monitoring (code examples provided)
4. Create evaluation test suite

### Next Month:
1. Pilot deployment to 1-2 counties
2. User training
3. Performance monitoring
4. Iterate based on feedback

---

## Key Takeaways:

✅ **No training needed** - Use prompts, not fine-tuning
✅ **Monitor bias at 4 levels** - Input, decisions, outcomes, dashboards  
✅ **Prompts in YAML** - Version control, A/B testing
✅ **ReAct + CoT hybrid** - Best of both patterns
✅ **Prioritize recall** - Use F2 score, lower thresholds, ensemble methods
✅ **Cloud deployment ready** - Just need AWS credentials

**Everything is documented and ready to deploy!** 🚀

---

**Questions?** 
- Technical: Review [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)
- Architecture: Review [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
- Quick answers: This file
