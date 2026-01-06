# AWS Minimal Deployment Guide - DHCS BHT Demo

**Goal**: Deploy a cost-optimized, demo-ready system with modern UI for stakeholder presentations

**Cost Target**: $50-150/month (vs $1500-2000 for full production)

## Architecture Overview

### Minimal Demo Stack
```
┌─────────────────────────────────────────────────────────────┐
│                     CloudFront CDN                          │
│                  (Static Assets + API)                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼────────┐  ┌────────▼──────────┐
│   S3 Bucket    │  │  ECS Fargate Spot │
│  (UI Assets)   │  │   (Single Task)   │
└────────────────┘  └────────┬──────────┘
                              │
                    ┌─────────┴─────────┐
                    │  SQLite + ChromaDB │
                    │   (In-Container)   │
                    └───────────────────┘
```

**Key Simplifications for Demo**:
- **No Kafka/Pinot**: Use SQLite with synthetic data pre-loaded
- **No Separate Services**: Single container running API + data generator
- **Fargate Spot**: 70% cheaper than on-demand
- **S3 + CloudFront**: Serve static UI files
- **No RDS**: Embedded SQLite database
- **ChromaDB**: Embedded vector database

## Cost Breakdown (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| **ECS Fargate Spot** | 0.5 vCPU, 1GB RAM, 730hrs | ~$15 |
| **Application Load Balancer** | Minimal traffic | ~$16 |
| **CloudFront** | 10GB data transfer | ~$1 |
| **S3** | 5GB storage + requests | ~$1 |
| **Route53** | 1 hosted zone | ~$0.50 |
| **CloudWatch Logs** | 5GB logs | ~$2.50 |
| **OpenAI API** | 100k tokens/day | ~$30-50 |
| **Total** | | **~$66-86/month** |

## What You Need to Provide

### 1. AWS Account Setup
```bash
# Install AWS CLI
brew install awscli  # macOS
# or
pip install awscli

# Configure credentials
aws configure
# Enter:
# - AWS Access Key ID: [YOUR_KEY]
# - AWS Secret Access Key: [YOUR_SECRET]
# - Default region: us-west-2
# - Default output format: json
```

### 2. Domain Name (Optional)
- **Option A**: Use AWS-provided URL (e.g., `abc123.cloudfront.net`) - **FREE**
- **Option B**: Custom domain (e.g., `dhcs-demo.yourdomain.com`) - requires Route53 setup

### 3. OpenAI API Key
- Already have: `OPENAI_API_KEY` in your `.env`
- Will be stored in AWS Secrets Manager (secure)

### 4. Budget Approval
- **Demo period**: $100/month for 3 months = $300 total
- Set AWS Budget Alert at $120/month

## Step-by-Step Deployment

### Phase 1: Prepare Minimal Container (5 minutes)

I'll create a simplified version that runs everything in one container:

**File**: `deployment/minimal/Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install minimal dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (minimal subset)
COPY deployment/minimal/requirements-minimal.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agents/ /app/agents/
COPY api/ /app/api/
COPY deployment/minimal/synthetic_data.db /app/data/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File**: `deployment/minimal/requirements-minimal.txt`
```txt
# Core API
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# AI/ML (minimal)
openai==1.10.0
langchain==0.1.6
langchain-openai==0.0.5
langchain-community==0.0.20

# Vector DB (embedded)
chromadb==0.4.22
sentence-transformers==2.3.1

# Database
aiosqlite==0.19.0

# Utils
python-dotenv==1.0.0
pandas==2.2.0
```

### Phase 2: Build Modern UI (Next section)

### Phase 3: Deploy to AWS (10 minutes)

**File**: `deployment/deploy-minimal.sh`
```bash
#!/bin/bash
set -e

echo "🚀 DHCS BHT Minimal Deployment to AWS"
echo "======================================"

# Variables
AWS_REGION="us-west-2"
PROJECT_NAME="dhcs-bht-demo"
ECR_REPO="${PROJECT_NAME}-api"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
SERVICE_NAME="${PROJECT_NAME}-service"

# 1. Create ECR repository
echo "📦 Creating ECR repository..."
aws ecr create-repository \
  --repository-name $ECR_REPO \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true \
  || echo "Repository already exists"

ECR_URI=$(aws ecr describe-repositories \
  --repository-names $ECR_REPO \
  --region $AWS_REGION \
  --query 'repositories[0].repositoryUri' \
  --output text)

echo "ECR URI: $ECR_URI"

# 2. Build and push Docker image
echo "🏗️  Building Docker image..."
cd deployment/minimal
docker build -t $ECR_REPO:latest .

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URI

# Tag and push
docker tag $ECR_REPO:latest $ECR_URI:latest
docker push $ECR_URI:latest

echo "✅ Image pushed to ECR"

# 3. Store OpenAI API Key in Secrets Manager
echo "🔐 Storing OpenAI API key..."
aws secretsmanager create-secret \
  --name "${PROJECT_NAME}/openai-key" \
  --secret-string "$(grep OPENAI_API_KEY ../../.env | cut -d '=' -f2)" \
  --region $AWS_REGION \
  || aws secretsmanager update-secret \
       --secret-id "${PROJECT_NAME}/openai-key" \
       --secret-string "$(grep OPENAI_API_KEY ../../.env | cut -d '=' -f2)" \
       --region $AWS_REGION

# 4. Create ECS Cluster
echo "🏗️  Creating ECS cluster..."
aws ecs create-cluster \
  --cluster-name $CLUSTER_NAME \
  --region $AWS_REGION \
  --capacity-providers FARGATE_SPOT FARGATE \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE_SPOT,weight=4 \
    capacityProvider=FARGATE,weight=1 \
  || echo "Cluster already exists"

# 5. Create Task Execution Role
echo "🔑 Creating IAM role..."
ROLE_NAME="${PROJECT_NAME}-task-execution-role"
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}'

aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document "$TRUST_POLICY" \
  || echo "Role already exists"

aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite

ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)

# 6. Register Task Definition
echo "📝 Registering task definition..."
TASK_DEF='{
  "family": "'$PROJECT_NAME'-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "'$ROLE_ARN'",
  "taskRoleArn": "'$ROLE_ARN'",
  "containerDefinitions": [{
    "name": "api",
    "image": "'$ECR_URI':latest",
    "essential": true,
    "portMappings": [{
      "containerPort": 8000,
      "protocol": "tcp"
    }],
    "secrets": [{
      "name": "OPENAI_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:'$AWS_REGION':'$(aws sts get-caller-identity --query Account --output text)':secret:'$PROJECT_NAME'/openai-key"
    }],
    "environment": [
      {"name": "AGENT_MODEL", "value": "gpt-4o-mini"},
      {"name": "LOG_LEVEL", "value": "INFO"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/'$PROJECT_NAME'",
        "awslogs-region": "'$AWS_REGION'",
        "awslogs-stream-prefix": "api",
        "awslogs-create-group": "true"
      }
    }
  }]
}'

echo "$TASK_DEF" > task-definition.json
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 7. Create Security Group
echo "🔒 Creating security group..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)
SG_NAME="${PROJECT_NAME}-sg"

SG_ID=$(aws ec2 create-security-group \
  --group-name $SG_NAME \
  --description "Security group for DHCS BHT Demo" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text) || \
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=$SG_NAME" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0 \
  || echo "Ingress rule already exists"

# 8. Get Subnets
SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[0:2].SubnetId' \
  --output text | tr '\t' ',')

# 9. Create Application Load Balancer
echo "⚖️  Creating load balancer..."
ALB_NAME="${PROJECT_NAME}-alb"

ALB_ARN=$(aws elbv2 create-load-balancer \
  --name $ALB_NAME \
  --subnets $(echo $SUBNETS | tr ',' ' ') \
  --security-groups $SG_ID \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text) || \
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names $ALB_NAME \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

# Get ALB DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

# 10. Create Target Group
echo "🎯 Creating target group..."
TG_NAME="${PROJECT_NAME}-tg"

TG_ARN=$(aws elbv2 create-target-group \
  --name $TG_NAME \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text) || \
TG_ARN=$(aws elbv2 describe-target-groups \
  --names $TG_NAME \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# 11. Create Listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN \
  || echo "Listener already exists"

# 12. Create ECS Service with Fargate Spot
echo "🚀 Creating ECS service..."
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition "${PROJECT_NAME}-task" \
  --desired-count 1 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=api,containerPort=8000" \
  --capacity-provider-strategy \
    capacityProvider=FARGATE_SPOT,weight=4,base=0 \
    capacityProvider=FARGATE,weight=1,base=0 \
  || echo "Service already exists - updating..."
  aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --force-new-deployment

echo ""
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "🌐 Your API is available at:"
echo "   http://$ALB_DNS"
echo ""
echo "🧪 Test it:"
echo "   curl http://$ALB_DNS/health"
echo ""
echo "⏳ Wait 2-3 minutes for the service to start"
echo ""
echo "📊 Monitor deployment:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME"
echo ""
echo "💰 Estimated cost: \$66-86/month"
echo ""
```

### Phase 4: Deploy Modern UI to S3/CloudFront

**File**: `deployment/deploy-ui.sh`
```bash
#!/bin/bash
set -e

PROJECT_NAME="dhcs-bht-demo"
AWS_REGION="us-west-2"
BUCKET_NAME="${PROJECT_NAME}-ui-$(date +%s)"

echo "🎨 Deploying Modern UI to S3/CloudFront"
echo "========================================"

# Get API URL from ALB
API_URL=$(aws elbv2 describe-load-balancers \
  --names "${PROJECT_NAME}-alb" \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "API URL: http://$API_URL"

# 1. Create S3 bucket
echo "📦 Creating S3 bucket..."
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION

# Configure bucket for static website hosting
aws s3 website s3://$BUCKET_NAME --index-document index.html

# 2. Build UI with API endpoint
echo "🏗️  Building UI..."
cd ../../ui-modern
export REACT_APP_API_URL="http://$API_URL"
npm install
npm run build

# 3. Upload to S3
echo "📤 Uploading to S3..."
aws s3 sync build/ s3://$BUCKET_NAME --delete

# 4. Create CloudFront distribution
echo "☁️  Creating CloudFront distribution..."
CF_CONFIG='{
  "CallerReference": "'$(date +%s)'",
  "Comment": "DHCS BHT Demo UI",
  "Enabled": true,
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 2,
    "Items": [
      {
        "Id": "S3-'$BUCKET_NAME'",
        "DomainName": "'$BUCKET_NAME'.s3-website-'$AWS_REGION'.amazonaws.com",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "OriginProtocolPolicy": "http-only"
        }
      },
      {
        "Id": "API-'$PROJECT_NAME'",
        "DomainName": "'$API_URL'",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "OriginProtocolPolicy": "http-only"
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-'$BUCKET_NAME'",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "CacheBehaviors": {
    "Quantity": 1,
    "Items": [{
      "PathPattern": "/api/*",
      "TargetOriginId": "API-'$PROJECT_NAME'",
      "ViewerProtocolPolicy": "redirect-to-https",
      "AllowedMethods": {
        "Quantity": 7,
        "Items": ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"]
      },
      "ForwardedValues": {
        "QueryString": true,
        "Cookies": {"Forward": "all"},
        "Headers": {"Quantity": 1, "Items": ["*"]}
      },
      "MinTTL": 0,
      "DefaultTTL": 0,
      "MaxTTL": 0
    }]
  }
}'

echo "$CF_CONFIG" > cloudfront-config.json
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json \
  --query 'Distribution.Id' \
  --output text)

DOMAIN_NAME=$(aws cloudfront get-distribution \
  --id $DISTRIBUTION_ID \
  --query 'Distribution.DomainName' \
  --output text)

echo ""
echo "✅ UI Deployment Complete!"
echo "======================================"
echo ""
echo "🌐 Your demo is available at:"
echo "   https://$DOMAIN_NAME"
echo ""
echo "⏳ CloudFront takes 10-15 minutes to propagate"
echo ""
echo "📋 Save this information:"
echo "   Bucket: $BUCKET_NAME"
echo "   Distribution: $DISTRIBUTION_ID"
echo "   URL: https://$DOMAIN_NAME"
echo ""
```

## Pre-Flight Checklist

Before running deployment:

- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Docker installed and running
- [ ] `.env` file has valid `OPENAI_API_KEY`
- [ ] AWS account has permissions for:
  - ECR (Elastic Container Registry)
  - ECS (Elastic Container Service)
  - IAM (Identity and Access Management)
  - EC2 (for VPC/Security Groups)
  - ELB (Load Balancer)
  - S3 (Storage)
  - CloudFront (CDN)
  - Secrets Manager
- [ ] Budget alert set at $120/month

## One-Command Deployment

```bash
# Deploy everything
./deployment/deploy-all.sh
```

This will:
1. Build minimal Docker image
2. Push to AWS ECR
3. Deploy ECS Fargate Spot service
4. Create load balancer
5. Build and deploy modern UI
6. Create CloudFront distribution

**Total time**: 15-20 minutes

## Monitoring & Management

### Check Service Status
```bash
aws ecs describe-services \
  --cluster dhcs-bht-demo-cluster \
  --services dhcs-bht-demo-service
```

### View Logs
```bash
aws logs tail /ecs/dhcs-bht-demo --follow
```

### Scale Up/Down
```bash
# Scale to 2 tasks
aws ecs update-service \
  --cluster dhcs-bht-demo-cluster \
  --service dhcs-bht-demo-service \
  --desired-count 2

# Scale to 0 (stop incurring costs)
aws ecs update-service \
  --cluster dhcs-bht-demo-cluster \
  --service dhcs-bht-demo-service \
  --desired-count 0
```

### Check Costs
```bash
# View current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

## Teardown (When Demo Complete)

```bash
./deployment/teardown.sh
```

This will delete:
- ECS Service and Cluster
- Load Balancer and Target Group
- CloudFront Distribution
- S3 Bucket
- ECR Repository
- Security Groups
- IAM Roles

**Note**: Secrets Manager has 7-day recovery window (adds ~$0.40)

## Next Steps

After deployment:
1. Test API: `curl http://[ALB-DNS]/health`
2. Open UI: `https://[CLOUDFRONT-DOMAIN]`
3. Verify agents respond correctly
4. Prepare stakeholder demo script
5. Monitor costs for first 48 hours

## Troubleshooting

**Service won't start**:
```bash
# Check task logs
aws ecs describe-tasks \
  --cluster dhcs-bht-demo-cluster \
  --tasks $(aws ecs list-tasks --cluster dhcs-bht-demo-cluster --query 'taskArns[0]' --output text)
```

**High costs**:
- Check if using Fargate Spot (should be 70% of tasks)
- Verify desired count is 1
- Check CloudWatch logs retention (set to 7 days)

**UI not loading**:
- CloudFront takes 10-15 minutes to propagate
- Check S3 bucket has files: `aws s3 ls s3://[BUCKET]/`
- Verify API URL in UI config

## What's Different from Production?

| Feature | Production | Demo/Minimal |
|---------|-----------|--------------|
| Database | Pinot cluster | SQLite (in-container) |
| Event Streaming | Kafka cluster | Pre-loaded synthetic data |
| Compute | On-demand Fargate | Fargate Spot (70% cheaper) |
| Redundancy | Multi-AZ, 3+ tasks | Single task |
| Storage | RDS + S3 | Embedded DB |
| Cost | $1500-2000/mo | $66-86/mo |
| Scalability | Auto-scaling | Fixed (demo) |

## Upgrade Path to Production

When ready to move to production:
1. Deploy Kafka on MSK (Managed Streaming for Kafka)
2. Deploy Pinot on EKS (Elastic Kubernetes Service)
3. Switch to RDS for persistent storage
4. Enable auto-scaling (2-10 tasks)
5. Add multi-AZ redundancy
6. Set up CloudWatch alarms
7. Enable AWS WAF for security
8. Use Route53 for custom domain

Estimated production cost: $1500-2000/month
