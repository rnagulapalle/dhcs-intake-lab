# AWS Production Deployment Guide

**Document Version**: 1.0
**Last Updated**: January 2026
**Target Environment**: AWS ECS Fargate

---

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Deployment Steps](#deployment-steps)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This guide walks through deploying the DHCS BHT Multi-Agent System to AWS using:
- **AWS ECS Fargate** for container orchestration
- **Application Load Balancer** for traffic distribution
- **AWS ECR** for container registry
- **CloudWatch** for logging and monitoring

### Deployment Architecture

```
Internet
   ↓
Application Load Balancer (ALB)
   ↓
┌─────────────────────────────────────┐
│         ECS Fargate Cluster         │
│                                     │
│  ┌───────────┐    ┌──────────────┐ │
│  │  API      │    │  Dashboard   │ │
│  │  Task     │    │  Task        │ │
│  │  (8000)   │    │  (8501)      │ │
│  └─────┬─────┘    └──────┬───────┘ │
│        │                  │          │
│        └──────────┬──────┘          │
│                   ↓                  │
│         Managed Services            │
└─────────────────────────────────────┘
          ↓       ↓       ↓
     ┌────────────────────────┐
     │  RDS / ElastiCache     │
     │  CloudWatch            │
     └────────────────────────┘
```

---

## Prerequisites

### AWS Account Requirements
- AWS account with appropriate permissions
- AWS CLI configured
- Docker installed locally
- Sufficient AWS service limits:
  - ECS: At least 2 tasks
  - VPC: At least 2 availability zones
  - ECR: Container registry access

### Required AWS Permissions
- ECS (Full Access)
- ECR (Full Access)
- IAM (Role creation)
- VPC (Network configuration)
- ELB (Load balancer)
- CloudWatch (Logs and metrics)

### Cost Estimate
- **Development**: ~$50-100/month
- **Production**: ~$200-500/month (depending on usage)

---

## Deployment Steps

### Step 1: Setup AWS Infrastructure

#### 1.1 Create ECR Repository
```bash
# Create repository for API
aws ecr create-repository \
  --repository-name dhcs-bht-api \
  --region us-west-2

# Create repository for Dashboard
aws ecr create-repository \
  --repository-name dhcs-bht-dashboard \
  --region us-west-2
```

#### 1.2 Create ECS Cluster
```bash
aws ecs create-cluster \
  --cluster-name dhcs-bht-cluster \
  --region us-west-2
```

#### 1.3 Create VPC and Networking (if needed)
```bash
# Use default VPC or create new one
# Ensure you have:
# - At least 2 public subnets in different AZs
# - Internet Gateway attached
# - Route table configured
```

---

### Step 2: Build and Push Docker Images

#### 2.1 Build for AMD64 (AWS Platform)
```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-west-2.amazonaws.com

# Build API image for AMD64
docker buildx build --platform linux/amd64 \
  -t <account-id>.dkr.ecr.us-west-2.amazonaws.com/dhcs-bht-api:latest \
  -f agents/Dockerfile \
  --push .

# Build Dashboard image for AMD64
docker buildx build --platform linux/amd64 \
  -t <account-id>.dkr.ecr.us-west-2.amazonaws.com/dhcs-bht-dashboard:latest \
  -f dashboard/Dockerfile \
  --push .
```

**Note**: Building for AMD64 from Mac (ARM64) will be slow (10-20 minutes). Consider using GitHub Actions or AWS CodeBuild for faster builds.

---

### Step 3: Create Task Definitions

#### 3.1 API Task Definition
Create `task-definition-api.json`:
```json
{
  "family": "dhcs-bht-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.us-west-2.amazonaws.com/dhcs-bht-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "<your-openai-api-key>"
        },
        {
          "name": "KAFKA_BOOTSTRAP_SERVERS",
          "value": "localhost:29092"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/dhcs-bht-api",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register task definition:
```bash
aws ecs register-task-definition \
  --cli-input-json file://task-definition-api.json
```

#### 3.2 Dashboard Task Definition
Similar structure for dashboard on port 8501.

---

### Step 4: Create Application Load Balancer

#### 4.1 Create ALB
```bash
aws elbv2 create-load-balancer \
  --name dhcs-bht-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4
```

#### 4.2 Create Target Groups
```bash
# API target group
aws elbv2 create-target-group \
  --name dhcs-bht-api-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --target-type ip \
  --health-check-path /health

# Dashboard target group
aws elbv2 create-target-group \
  --name dhcs-bht-dashboard-tg \
  --protocol HTTP \
  --port 8501 \
  --vpc-id vpc-xxxxx \
  --target-type ip \
  --health-check-path /
```

#### 4.3 Create Listeners
```bash
# HTTP listener (port 80)
aws elbv2 create-listener \
  --load-balancer-arn <alb-arn> \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=<dashboard-tg-arn>

# Add rules for /api path
aws elbv2 create-rule \
  --listener-arn <listener-arn> \
  --priority 1 \
  --conditions Field=path-pattern,Values='/api/*' \
  --actions Type=forward,TargetGroupArn=<api-tg-arn>
```

---

### Step 5: Create ECS Services

#### 5.1 API Service
```bash
aws ecs create-service \
  --cluster dhcs-bht-cluster \
  --service-name api-service \
  --task-definition dhcs-bht-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=<api-tg-arn>,containerName=api,containerPort=8000
```

#### 5.2 Dashboard Service
```bash
aws ecs create-service \
  --cluster dhcs-bht-cluster \
  --service-name dashboard-service \
  --task-definition dhcs-bht-dashboard \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=<dashboard-tg-arn>,containerName=dashboard,containerPort=8501
```

---

### Step 6: Configure Auto Scaling (Optional)

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/dhcs-bht-cluster/api-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/dhcs-bht-cluster/api-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

---

## Configuration

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Yes | `sk-proj-...` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka servers | No | `kafka:9092` |
| `PINOT_BROKER_URL` | Pinot broker | No | `http://pinot:8099` |
| `CHROMA_PERSIST_DIR` | ChromaDB path | No | `/data/chroma` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

### Security Groups

**ALB Security Group**:
- Inbound: Port 80 (HTTP) from 0.0.0.0/0
- Inbound: Port 443 (HTTPS) from 0.0.0.0/0 (if using SSL)
- Outbound: All traffic

**ECS Task Security Group**:
- Inbound: Port 8000 from ALB security group
- Inbound: Port 8501 from ALB security group
- Outbound: All traffic (for API calls, database access)

---

## Monitoring

### CloudWatch Logs

Logs are automatically sent to CloudWatch Logs:
- API logs: `/ecs/dhcs-bht-api`
- Dashboard logs: `/ecs/dhcs-bht-dashboard`

View logs:
```bash
aws logs tail /ecs/dhcs-bht-api --follow
```

### CloudWatch Metrics

Key metrics to monitor:
- **CPUUtilization**: Average CPU usage
- **MemoryUtilization**: Average memory usage
- **TargetResponseTime**: ALB target response time
- **RequestCount**: Number of requests
- **HealthyHostCount**: Number of healthy targets

Create alarms:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name high-cpu-api \
  --alarm-description "API CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

---

## Troubleshooting

### Issue: Tasks failing to start

**Check task logs:**
```bash
aws ecs describe-tasks \
  --cluster dhcs-bht-cluster \
  --tasks <task-id>
```

**Common causes:**
- Incorrect IAM permissions
- Image pull failures (check ECR permissions)
- Insufficient CPU/memory
- Missing environment variables

### Issue: Health checks failing

**Verify endpoints:**
```bash
# From within VPC or using VPN
curl http://<task-private-ip>:8000/health
curl http://<task-private-ip>:8501/
```

**Check security groups:**
- ALB can reach tasks on correct ports
- Tasks can reach external services (OpenAI API)

### Issue: High latency

**Possible solutions:**
- Increase task count
- Upgrade task CPU/memory
- Enable auto-scaling
- Add caching layer (ElastiCache)
- Optimize database queries

---

## Cost Optimization

### Development Environment
- Use single task instances (no redundancy)
- Use smaller instance types (0.5 vCPU, 1GB RAM)
- Stop services when not in use

### Production Environment
- Use reserved capacity for predictable workloads
- Enable auto-scaling to handle peaks
- Use spot instances for non-critical services
- Monitor and right-size instances

---

## Next Steps

- [Configure CI/CD Pipeline](./CI-CD.md)
- [Setup Monitoring Dashboard](./MONITORING.md)
- [Configure SSL/TLS](./SSL-SETUP.md)
- [Multi-Region Deployment](./MULTI-REGION.md)

---

## Support

For deployment issues:
1. Check [Troubleshooting Guide](../guides/TROUBLESHOOTING.md)
2. Review CloudWatch logs
3. Contact DevOps team
