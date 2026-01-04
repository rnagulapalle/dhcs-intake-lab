# System Architecture & Design Decisions

## Architecture Pattern: **Prompt-Based Multi-Agent System**

```
┌─────────────────────────────────────────────────────────────────┐
│                       USER INTERFACE                            │
│                   (Streamlit Dashboard)                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                    (REST API Endpoints)                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR AGENT                            │
│              (LangGraph State Machine)                          │
│                                                                 │
│  Pattern: ReAct (Reasoning + Acting)                           │
│  - Classifies user intent                                       │
│  - Routes to specialized agents                                 │
│  - Combines results                                             │
└──────┬──────┬────────┬────────┬──────────┬─────────────────────┘
       │      │        │        │          │
       ▼      ▼        ▼        ▼          ▼
   ┌──────┐ ┌────┐  ┌───────┐ ┌──────┐ ┌──────────┐
   │Query │ │Anal│  │Triage │ │ Recs │ │Knowledge │
   │Agent │ │ytics│  │Agent  │ │Agent │ │  Agent   │
   └──┬───┘ └─┬──┘  └───┬───┘ └──┬───┘ └────┬─────┘
      │       │         │        │          │
      │       │         │        │          │
      └───────┴─────────┴────────┴──────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌─────────┐   ┌─────────────┐   ┌─────────┐
    │  Pinot  │   │   OpenAI    │   │ChromaDB │
    │(Real-time│   │  GPT-4o     │   │ (RAG)   │
    │Analytics)│   │   (LLM)     │   │         │
    └─────────┘   └─────────────┘   └─────────┘
          ▲
          │
          │
    ┌─────┴─────┐
    │   Kafka   │
    │ (Streaming)│
    └─────▲─────┘
          │
          │
    ┌─────┴─────┐
    │ Generator │
    │(Synthetic)│
    └───────────┘
```

## Key Design Decisions

### 1. **No Model Training Required** ✅

```
Traditional ML:                    Our Approach:
┌──────────────┐                  ┌──────────────┐
│ Collect Data │  3-6 months      │ Use GPT-4o   │  Instant
│   (10k+)     │                  │ (Pre-trained)│
└──────┬───────┘                  └──────┬───────┘
       │                                  │
       ▼                                  ▼
┌──────────────┐                  ┌──────────────┐
│ Label Data   │  2-4 weeks       │   Prompt     │  Days
│  (Manual)    │                  │  Engineering │
└──────┬───────┘                  └──────┬───────┘
       │                                  │
       ▼                                  ▼
┌──────────────┐                  ┌──────────────┐
│ Train Model  │  Days-Weeks      │   Deploy     │  Minutes
│  (GPU $$$)   │                  │   (Docker)   │
└──────┬───────┘                  └──────────────┘
       │
       ▼
┌──────────────┐
│ Deploy Model │  Complex
│ (GPU infra)  │
└──────────────┘

Cost: $10k-50k+                   Cost: API usage only
Time: 4-8 months                  Time: Immediate
Maintenance: High                 Maintenance: Low
```

### 2. **Agent Collaboration Pattern**

```python
# REACT PATTERN (Orchestrator)
def process_query(user_input):
    # THOUGHT: What is the user asking?
    intent = llm.classify(user_input)
    
    # ACTION: Route to agent
    if intent == "data_query":
        result = query_agent.execute(user_input)
    
    # OBSERVATION: Check result
    if result.needs_clarification:
        # THOUGHT: Need more info
        # ACTION: Ask follow-up
        clarification = analytics_agent.get_context()
        
    # FINAL ACTION: Generate response
    return generate_response(result)


# CHAIN-OF-THOUGHT (Individual Agents)
def generate_sql(question):
    prompt = """
    Think step-by-step:
    1. What tables? → dhcs_crisis_intake
    2. What columns? → county, COUNT(*)
    3. What filters? → risk_level='high'
    4. Time range? → last hour
    5. Grouping? → GROUP BY county
    
    SQL:
    SELECT county, COUNT(*) FROM dhcs_crisis_intake
    WHERE risk_level='high' AND event_time_ms > now() - 3600000
    GROUP BY county
    """
    return llm.generate(prompt)
```

### 3. **Recall vs Precision Strategy**

For **crisis triage**, we prioritize **RECALL** (catching all high-risk cases):

```
Confusion Matrix:

                  Predicted High    Predicted Low
Actual High           TP                FN ← DANGEROUS!
Actual Low            FP ← OK           TN

Metrics:
- Recall = TP / (TP + FN)  ← TARGET: >95%
- Precision = TP / (TP + FP)  ← TARGET: >70%
- F2 Score = Weighted toward recall ← PRIMARY METRIC

Strategy:
- Use F2 score (β=2) instead of F1
- Lower threshold for flagging high-risk
- Human review for uncertain cases
- Acceptable: 30% false positives
- Unacceptable: 5% false negatives
```

### 4. **Prompt Engineering > Fine-tuning**

**Why prompts, not training?**

| Aspect | Fine-tuning | Prompt Engineering |
|--------|-------------|-------------------|
| Setup Time | Months | Days |
| Data Required | 10k+ examples | None |
| Cost | $5k-50k+ | API usage only |
| Iteration | Slow (retrain) | Fast (change prompt) |
| Expertise | ML engineers | Anyone |
| Infrastructure | GPU clusters | API only |
| Updates | Redeploy model | Update YAML |

**When to fine-tune (Optional):**
- After 6+ months of production
- If you have 10k+ labeled examples
- If you need to reduce API costs
- If you need offline inference

### 5. **Multi-Level Bias Monitoring**

```
Level 1: INPUT DATA
├─ County distribution
├─ Language distribution
├─ Risk level distribution
└─ Channel usage

Level 2: AGENT DECISIONS
├─ Query routing patterns
├─ Triage score distribution
├─ Recommendation types
└─ Response time by group

Level 3: OUTCOMES
├─ Resolution rates by county
├─ Escalation rates by language
├─ Intervention success by channel
└─ Disparate impact analysis (80% rule)

Level 4: ALERTS
├─ Real-time anomaly detection
├─ Daily bias reports
├─ Weekly fairness audits
└─ Monthly compliance review
```

### 6. **Evaluation Framework**

```python
# Test Categories:

1. ACCURACY TESTS (100 cases)
   - SQL generation correctness
   - Triage score accuracy
   - Recommendation relevance

2. BIAS TESTS (50 cases per group)
   - County: 6 groups × 50 = 300 cases
   - Language: 5 groups × 50 = 250 cases
   - Risk level: 4 groups × 50 = 200 cases
   Total: 750 cases

3. EDGE CASES (100 cases)
   - Ambiguous queries
   - Missing data
   - Conflicting indicators
   - Unusual patterns

4. STRESS TESTS (1000 cases)
   - Concurrent requests
   - Large result sets
   - Complex queries
   - Timeout scenarios

Total Test Suite: 2,000+ cases
Run Frequency: Daily (automated)
```

## Production Deployment Checklist

### Phase 1: Pre-Deployment (1-2 weeks)

- [ ] AWS account set up
- [ ] OpenAI API production key obtained
- [ ] Budget approved ($1,500/month)
- [ ] Domain name registered (optional)
- [ ] SSL certificate obtained (AWS ACM)
- [ ] Monitoring tools selected (Prometheus/Grafana)
- [ ] Alert channels configured (Slack/PagerDuty)
- [ ] Team trained on system

### Phase 2: Initial Deployment (1 week)

- [ ] ECR repositories created
- [ ] Docker images built and pushed
- [ ] ECS/EKS cluster provisioned
- [ ] Load balancer configured
- [ ] Environment variables set
- [ ] Health checks configured
- [ ] DNS configured (if using custom domain)
- [ ] SSL enabled

### Phase 3: Monitoring Setup (1 week)

- [ ] Prometheus metrics endpoint added
- [ ] Grafana dashboards created
- [ ] Bias monitoring enabled
- [ ] Alert rules configured
- [ ] Log aggregation set up (CloudWatch)
- [ ] Error tracking enabled (Sentry)
- [ ] Performance monitoring (New Relic/DataDog)

### Phase 4: Testing (1-2 weeks)

- [ ] Smoke tests passing
- [ ] Load tests passing (100 concurrent users)
- [ ] Evaluation suite passing (>95% recall)
- [ ] Bias tests passing (no disparate impact)
- [ ] Security scan passing
- [ ] Penetration test completed (if required)

### Phase 5: Production Launch (Pilot)

- [ ] Launch to 1-2 counties only
- [ ] Monitor for 2-4 weeks
- [ ] Collect user feedback
- [ ] Measure performance metrics
- [ ] Iterate on prompts/thresholds
- [ ] Expand to more counties

### Phase 6: Full Production (if pilot successful)

- [ ] Deploy to all counties
- [ ] 24/7 monitoring enabled
- [ ] On-call rotation established
- [ ] Incident response plan documented
- [ ] Disaster recovery plan tested
- [ ] Backup/restore procedures verified

## Cost Breakdown

### Monthly Operating Costs (Production):

```
Infrastructure:
├─ AWS ECS/Fargate: $200-300/month
├─ AWS MSK (Kafka): $600/month  
├─ AWS RDS (optional): $50/month
├─ Load Balancer: $20/month
├─ CloudWatch Logs: $30/month
├─ Data Transfer: $50/month
└─ Total Infrastructure: $950/month

OpenAI API:
├─ GPT-4o: $0.01-0.02/query
├─ Estimated 50k queries/month
└─ Total API: $500-1,000/month

Monitoring:
├─ New Relic/DataDog: $100/month
├─ Sentry: $50/month
└─ Total Monitoring: $150/month

GRAND TOTAL: $1,600-2,100/month
```

### Cost Optimization Strategies:

1. **Use GPT-4o-mini** for non-critical queries ($10x cheaper)
2. **Cache frequent queries** (30-50% cost reduction)
3. **Batch similar requests** (reduce API calls)
4. **Use spot instances** for non-critical workloads
5. **Right-size containers** (monitor and adjust resources)

## Security Considerations

### Current Status (Demo):
✅ All data synthetic
✅ No PHI
✅ No HIPAA requirements
✅ Safe for demos

### Before Production with Real Data:

1. **Data Encryption**
   - At rest: AWS KMS
   - In transit: TLS 1.3
   - End-to-end encryption

2. **Access Control**
   - IAM roles with least privilege
   - MFA for all admin access
   - VPC isolation
   - Security groups

3. **Audit Logging**
   - CloudTrail enabled
   - All PHI access logged
   - Tamper-proof logs
   - 7-year retention

4. **Compliance**
   - HIPAA compliance audit
   - SOC 2 Type II (if needed)
   - Regular security assessments
   - Penetration testing

5. **Data Handling**
   - PHI de-identification
   - Data minimization
   - Retention policies
   - Secure deletion

## Next Steps

### This Week:
1. Review this document
2. Get AWS account credentials
3. Approve budget
4. Decide: AWS or Kubernetes?

### Next Week:
1. Deploy to AWS dev environment
2. Set up monitoring
3. Create evaluation test cases
4. Test end-to-end

### Next Month:
1. Implement bias monitoring
2. Set up continuous evaluation
3. Conduct user training
4. Plan pilot deployment

---

**Questions?** Review the detailed [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)
