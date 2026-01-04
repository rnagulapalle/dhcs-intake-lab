# AWS Deployment Guide for DHCS BHT Multi-Agent System

## Architecture Overview

### Recommended AWS Services:
- **ECS Fargate**: Containerized services (agent-api, dashboard, generator)
- **MSK (Managed Kafka)**: Kafka cluster
- **Amazon RDS**: Pinot metadata (or self-managed Pinot on ECS)
- **Application Load Balancer**: Traffic distribution
- **CloudWatch**: Logging and monitoring
- **Secrets Manager**: API keys and credentials
- **S3**: Pinot deep storage

## Deployment Options

### Option 1: ECS Fargate (Recommended for Quick Start)
- Fully managed containers
- No server management
- Auto-scaling
- Cost-effective for variable workloads

### Option 2: EKS (Kubernetes)
- More control and flexibility
- Better for complex orchestration
- Portable across cloud providers
- See `../kubernetes/` for manifests

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI installed and configured
3. Docker images pushed to ECR
4. OpenAI API key stored in Secrets Manager

## Quick Deploy with CloudFormation

```bash
# 1. Create ECR repositories
aws ecr create-repository --repository-name dhcs-bht/agent-api
aws ecr create-repository --repository-name dhcs-bht/dashboard
aws ecr create-repository --repository-name dhcs-bht/generator

# 2. Build and push images
./deployment/aws/build_and_push.sh

# 3. Store OpenAI API key in Secrets Manager
aws secretsmanager create-secret \
  --name dhcs-bht/openai-api-key \
  --secret-string "your-openai-api-key"

# 4. Deploy CloudFormation stack
aws cloudformation create-stack \
  --stack-name dhcs-bht-system \
  --template-body file://deployment/aws/cloudformation.yaml \
  --parameters ParameterKey=OpenAISecretArn,ParameterValue=<secret-arn> \
  --capabilities CAPABILITY_IAM
```

## Cost Estimates (us-west-2, monthly)

### Small Demo Environment:
- ECS Fargate (3 services, 0.25 vCPU, 0.5GB each): ~$15
- MSK (2 brokers, kafka.t3.small): ~$200
- Application Load Balancer: ~$20
- CloudWatch Logs: ~$5
- **Total: ~$240/month**

### Production Environment:
- ECS Fargate (auto-scaling, 1-4 vCPU per service): ~$200
- MSK (3+ brokers, kafka.m5.large): ~$600+
- RDS for Pinot metadata: ~$50
- S3 storage: ~$10
- CloudWatch: ~$20
- **Total: ~$880+/month**

## Monitoring

All services log to CloudWatch:
- Log Group: `/aws/ecs/dhcs-bht/`
- Metrics: CPU, Memory, Request Count
- Alarms: High CPU, Failed Health Checks

## Scaling

ECS Service Auto Scaling based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)
- Request count per target

## Security

- VPC with private subnets
- Security groups restrict traffic
- Secrets in AWS Secrets Manager
- IAM roles with least privilege
- TLS/SSL on load balancer

## Backup & DR

- Kafka: MSK automatic backups
- Pinot: Segments backed up to S3
- ChromaDB: EFS volume snapshots
- RTO: < 1 hour
- RPO: < 15 minutes
