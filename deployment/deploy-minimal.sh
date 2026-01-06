#!/bin/bash
set -e

echo "🚀 DHCS BHT Minimal Deployment to AWS"
echo "======================================"
echo ""

# Variables
AWS_REGION="us-west-2"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
PROJECT_NAME="dhcs-bht-demo"
ECR_REPO="${PROJECT_NAME}-api"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
SERVICE_NAME="${PROJECT_NAME}-service"
TASK_FAMILY="${PROJECT_NAME}-task"

echo "📋 Deployment Configuration:"
echo "   AWS Account: $AWS_ACCOUNT"
echo "   Region: $AWS_REGION"
echo "   Project: $PROJECT_NAME"
echo ""

# Check if OpenAI API key exists in .env
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create .env file with your OPENAI_API_KEY"
    exit 1
fi

OPENAI_KEY=$(grep OPENAI_API_KEY .env | cut -d '=' -f2)
if [ -z "$OPENAI_KEY" ] || [ "$OPENAI_KEY" = "sk-your-openai-api-key-here" ]; then
    echo "❌ Error: Valid OPENAI_API_KEY not found in .env"
    echo "   Please update .env with your actual OpenAI API key"
    exit 1
fi

echo "✅ OpenAI API key found"
echo ""

# 1. Create ECR repository
echo "📦 Step 1/12: Creating ECR repository..."
aws ecr create-repository \
  --repository-name $ECR_REPO \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true \
  2>/dev/null || echo "   Repository already exists"

ECR_URI=$(aws ecr describe-repositories \
  --repository-names $ECR_REPO \
  --region $AWS_REGION \
  --query 'repositories[0].repositoryUri' \
  --output text)

echo "   ECR URI: $ECR_URI"
echo ""

# 2. Build Docker image
echo "🏗️  Step 2/12: Building Docker image..."
docker build -f deployment/minimal/Dockerfile -t $ECR_REPO:latest .

echo ""

# 3. Login to ECR
echo "🔐 Step 3/12: Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URI

echo ""

# 4. Tag and push image
echo "📤 Step 4/12: Pushing image to ECR..."
docker tag $ECR_REPO:latest $ECR_URI:latest
docker push $ECR_URI:latest

echo ""

# 5. Store OpenAI API Key in Secrets Manager
echo "🔐 Step 5/12: Storing OpenAI API key in Secrets Manager..."
aws secretsmanager create-secret \
  --name "${PROJECT_NAME}/openai-key" \
  --secret-string "$OPENAI_KEY" \
  --region $AWS_REGION \
  2>/dev/null || \
aws secretsmanager update-secret \
  --secret-id "${PROJECT_NAME}/openai-key" \
  --secret-string "$OPENAI_KEY" \
  --region $AWS_REGION

echo "   Secret stored: ${PROJECT_NAME}/openai-key"
echo ""

# 6. Create ECS Cluster
echo "🏗️  Step 6/12: Creating ECS cluster..."
aws ecs create-cluster \
  --cluster-name $CLUSTER_NAME \
  --region $AWS_REGION \
  --capacity-providers FARGATE_SPOT FARGATE \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE_SPOT,weight=4,base=0 \
    capacityProvider=FARGATE,weight=1,base=0 \
  2>/dev/null || echo "   Cluster already exists"

echo ""

# 7. Create Task Execution Role
echo "🔑 Step 7/12: Creating IAM role..."
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
  2>/dev/null || echo "   Role already exists"

aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  2>/dev/null || true

aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  2>/dev/null || true

ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
echo "   Role ARN: $ROLE_ARN"
echo ""

# Wait a bit for IAM role to propagate
echo "⏳ Waiting for IAM role to propagate..."
sleep 10
echo ""

# 8. Register Task Definition
echo "📝 Step 8/12: Registering task definition..."
cat > /tmp/task-definition.json << EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "$ROLE_ARN",
  "taskRoleArn": "$ROLE_ARN",
  "containerDefinitions": [{
    "name": "api",
    "image": "$ECR_URI:latest",
    "essential": true,
    "portMappings": [{
      "containerPort": 8000,
      "protocol": "tcp"
    }],
    "secrets": [{
      "name": "OPENAI_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT:secret:${PROJECT_NAME}/openai-key"
    }],
    "environment": [
      {"name": "AGENT_MODEL", "value": "gpt-4o-mini"},
      {"name": "LOG_LEVEL", "value": "INFO"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/$PROJECT_NAME",
        "awslogs-region": "$AWS_REGION",
        "awslogs-stream-prefix": "api",
        "awslogs-create-group": "true"
      }
    },
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 60
    }
  }]
}
EOF

aws ecs register-task-definition --cli-input-json file:///tmp/task-definition.json > /dev/null
echo "   Task definition registered: $TASK_FAMILY"
echo ""

# 9. Create Security Group
echo "🔒 Step 9/12: Creating security group..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)
SG_NAME="${PROJECT_NAME}-sg"

SG_ID=$(aws ec2 create-security-group \
  --group-name $SG_NAME \
  --description "Security group for DHCS BHT Demo" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text 2>/dev/null) || \
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=$SG_NAME" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0 \
  2>/dev/null || echo "   Ingress rule already exists"

echo "   Security Group: $SG_ID"
echo ""

# 10. Get Subnets
echo "🌐 Step 10/12: Getting subnet information..."
SUBNETS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[0:2].SubnetId' \
  --output text | tr '\t' ',')

echo "   Using subnets: $SUBNETS"
echo ""

# 11. Create Application Load Balancer
echo "⚖️  Step 11/12: Creating load balancer..."
ALB_NAME="${PROJECT_NAME}-alb"

ALB_ARN=$(aws elbv2 create-load-balancer \
  --name $ALB_NAME \
  --subnets $(echo $SUBNETS | tr ',' ' ') \
  --security-groups $SG_ID \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text 2>/dev/null) || \
ALB_ARN=$(aws elbv2 describe-load-balancers \
  --names $ALB_NAME \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

# Get ALB DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "   Load Balancer: $ALB_DNS"
echo ""

# 12. Create Target Group
echo "🎯 Step 12/12: Creating target group..."
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
  --output text 2>/dev/null) || \
TG_ARN=$(aws elbv2 describe-target-groups \
  --names $TG_NAME \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

echo "   Target Group: $TG_ARN"
echo ""

# Create Listener
echo "🔊 Creating listener..."
LISTENER_ARN=$(aws elbv2 describe-listeners \
  --load-balancer-arn $ALB_ARN \
  --query 'Listeners[0].ListenerArn' \
  --output text 2>/dev/null)

if [ "$LISTENER_ARN" = "None" ] || [ -z "$LISTENER_ARN" ]; then
  aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN \
    > /dev/null
  echo "   Listener created"
else
  echo "   Listener already exists"
fi
echo ""

# 13. Create ECS Service
echo "🚀 Step 13/12: Creating ECS service..."
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition $TASK_FAMILY \
  --desired-count 1 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=api,containerPort=8000" \
  --health-check-grace-period-seconds 60 \
  2>/dev/null && echo "   Service created" || \
  (echo "   Service exists, forcing new deployment..." && \
   aws ecs update-service \
     --cluster $CLUSTER_NAME \
     --service $SERVICE_NAME \
     --force-new-deployment > /dev/null)

echo ""
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "🌐 Your API will be available at:"
echo "   http://$ALB_DNS"
echo ""
echo "⏳ Wait 2-3 minutes for the service to start, then test:"
echo "   curl http://$ALB_DNS/health"
echo ""
echo "📊 Monitor deployment:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --query 'services[0].deployments'"
echo ""
echo "💰 Estimated cost: \$66-86/month"
echo ""
echo "📝 Save this info:"
cat > DEPLOYMENT_INFO.txt << INFO
DHCS BHT Demo - Deployment Information
======================================

Deployed: $(date)

API URL: http://$ALB_DNS
AWS Account: $AWS_ACCOUNT
Region: $AWS_REGION

Resources:
- ECS Cluster: $CLUSTER_NAME
- ECS Service: $SERVICE_NAME
- Load Balancer: $ALB_DNS
- Security Group: $SG_ID
- ECR Repository: $ECR_URI

Management Commands:
-------------------

# Check service status
aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME

# View logs
aws logs tail /ecs/$PROJECT_NAME --follow

# Scale down (stop, saves ~\$15/mo)
aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --desired-count 0

# Scale up (restart)
aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --desired-count 1

# Force new deployment
aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment

# Teardown (delete everything)
./deployment/teardown.sh
INFO

echo "   Deployment info saved to: DEPLOYMENT_INFO.txt"
echo ""
