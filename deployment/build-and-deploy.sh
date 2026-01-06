#!/bin/bash
set -e

echo "🚀 DHCS BHT Build & Deploy (Industry-Standard Approach)"
echo "========================================================="
echo ""

# Variables
AWS_REGION="us-west-2"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
PROJECT_NAME="dhcs-bht-demo"
ECR_REPO="${PROJECT_NAME}-api"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
SERVICE_NAME="${PROJECT_NAME}-service"

echo "📋 Configuration:"
echo "   AWS Account: $AWS_ACCOUNT"
echo "   Region: $AWS_REGION"
echo "   Project: $PROJECT_NAME"
echo ""

# Pre-flight Safeguards
echo "✅ Pre-flight Checks:"
echo ""

# 1. Check AWS credentials
echo -n "   [1/5] AWS credentials... "
aws sts get-caller-identity > /dev/null 2>&1 && echo "✓" || (echo "✗ Failed" && exit 1)

# 2. Check Docker is running
echo -n "   [2/5] Docker daemon... "
docker ps > /dev/null 2>&1 && echo "✓" || (echo "✗ Not running" && exit 1)

# 3. Check Docker buildx available
echo -n "   [3/5] Docker buildx... "
docker buildx version > /dev/null 2>&1 && echo "✓" || (echo "✗ Not available" && exit 1)

# 4. Check existing AWS resources
echo -n "   [4/5] ECS Cluster... "
aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION > /dev/null 2>&1 && echo "✓" || (echo "✗ Not found" && exit 1)

echo -n "   [5/5] ECR Repository... "
ECR_URI=$(aws ecr describe-repositories \
  --repository-names $ECR_REPO \
  --region $AWS_REGION \
  --query 'repositories[0].repositoryUri' \
  --output text 2>/dev/null)

if [ -z "$ECR_URI" ]; then
  echo "✗ Not found"
  exit 1
else
  echo "✓"
fi

echo ""

# Disk space check
FREE_SPACE=$(df -k . | tail -1 | awk '{print $4}')
FREE_SPACE_GB=$((FREE_SPACE / 1024 / 1024))
echo "💾 Disk space available: ${FREE_SPACE_GB}GB"
if [ $FREE_SPACE_GB -lt 10 ]; then
  echo "   ⚠️  Warning: Low disk space (recommended 10GB+)"
  read -p "   Continue anyway? (yes/no): " CONTINUE
  if [ "$CONTINUE" != "yes" ]; then
    exit 1
  fi
fi
echo ""

# Backup current task definition
echo "💾 Creating backup of current task definition..."
TASK_FAMILY="${PROJECT_NAME}-task"
CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
  --task-definition $TASK_FAMILY \
  --region $AWS_REGION 2>/dev/null)

if [ ! -z "$CURRENT_TASK_DEF" ]; then
  echo "$CURRENT_TASK_DEF" > /tmp/task-definition-backup-$(date +%Y%m%d_%H%M%S).json
  echo "   Backup saved to: /tmp/task-definition-backup-*.json"
else
  echo "   No existing task definition to backup"
fi
echo ""

# Build Docker image for AMD64 using buildx
echo "🏗️  Building Docker image for AMD64 (linux/amd64)..."
echo "   Note: Using Docker buildx with proper platform targeting"
echo ""

# Create a new builder instance if it doesn't exist
docker buildx create --name dhcs-builder --use 2>/dev/null || docker buildx use dhcs-builder 2>/dev/null || true

# Build for AMD64 platform and load into local Docker
# This avoids cross-compilation by using QEMU emulation efficiently
docker buildx build \
  --platform linux/amd64 \
  --file deployment/minimal/Dockerfile \
  --tag $ECR_REPO:latest \
  --load \
  .

echo ""
echo "✅ Image built successfully"
echo ""

# Login to ECR
echo "🔐 Logging into Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URI > /dev/null 2>&1
echo "   Logged in successfully"
echo ""

# Tag and push image
echo "📤 Pushing image to ECR..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker tag $ECR_REPO:latest $ECR_URI:latest
docker tag $ECR_REPO:latest $ECR_URI:$TIMESTAMP

echo "   Pushing $ECR_URI:latest"
docker push $ECR_URI:latest

echo "   Pushing $ECR_URI:$TIMESTAMP"
docker push $ECR_URI:$TIMESTAMP

echo "✅ Image pushed to ECR"
echo ""

# Update ECS service
echo "🚀 Deploying to ECS..."
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service $SERVICE_NAME \
  --force-new-deployment \
  --region $AWS_REGION \
  > /dev/null

echo "   Service update initiated"
echo ""

# Monitor deployment
echo "⏳ Monitoring deployment progress..."
echo "   (This typically takes 2-3 minutes)"
echo ""

# Wait for service to stabilize (with timeout)
echo "   Waiting for service to stabilize..."
aws ecs wait services-stable \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $AWS_REGION \
  2>/dev/null || echo "   Timed out, but deployment may still succeed"

echo ""

# Get deployment status
echo "📊 Deployment Status:"
SERVICE_INFO=$(aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $AWS_REGION \
  --query 'services[0]' \
  --output json)

RUNNING_COUNT=$(echo $SERVICE_INFO | jq -r '.runningCount')
DESIRED_COUNT=$(echo $SERVICE_INFO | jq -r '.desiredCount')
DEPLOYMENT_STATUS=$(echo $SERVICE_INFO | jq -r '.deployments[0].rolloutState // "IN_PROGRESS"')

echo "   Running tasks: $RUNNING_COUNT / $DESIRED_COUNT"
echo "   Rollout state: $DEPLOYMENT_STATUS"
echo ""

# Check for any issues in events
EVENTS=$(echo $SERVICE_INFO | jq -r '.events[:3][] | "   - \(.createdAt) \(.message)"')
echo "📋 Recent service events:"
echo "$EVENTS"
echo ""

# Get load balancer URL
echo "🌐 API Endpoint:"
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names "${PROJECT_NAME}-alb" \
  --region $AWS_REGION \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "   http://$ALB_DNS"
echo ""

# Test health endpoint
echo "🧪 Testing health endpoint (waiting 30 seconds for task to start)..."
sleep 30

for i in {1..5}; do
  echo -n "   Attempt $i/5... "
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$ALB_DNS/health --max-time 5)
  if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Success (HTTP $HTTP_CODE)"
    HEALTH_CHECK_PASSED=true
    break
  else
    echo "❌ Failed (HTTP $HTTP_CODE)"
    sleep 10
  fi
done

echo ""

if [ "$HEALTH_CHECK_PASSED" = "true" ]; then
  echo "✅ Deployment Successful!"
  echo "========================="
  echo ""
  echo "🎉 Your DHCS BHT Multi-Agent System is now live on AWS!"
  echo ""
  echo "📍 API URL: http://$ALB_DNS"
  echo ""
  echo "🧪 Test commands:"
  echo "   curl http://$ALB_DNS/health"
  echo "   curl http://$ALB_DNS/docs"
  echo ""
else
  echo "⚠️  Deployment completed but health check failed"
  echo "================================================"
  echo ""
  echo "This may be normal - the service might still be starting up."
  echo ""
  echo "🔍 Troubleshooting steps:"
  echo ""
  echo "1. Check service status:"
  echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION"
  echo ""
  echo "2. Check task status:"
  echo "   aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --region $AWS_REGION"
  echo ""
  echo "3. View logs:"
  echo "   aws logs tail /ecs/$PROJECT_NAME --follow --region $AWS_REGION"
  echo ""
  echo "4. Try health check manually:"
  echo "   curl -v http://$ALB_DNS/health"
  echo ""
fi

echo "💰 Cost estimate: ~\$66-86/month"
echo ""
echo "📊 AWS Console:"
echo "   ECS: https://console.aws.amazon.com/ecs/v2/clusters/$CLUSTER_NAME?region=$AWS_REGION"
echo "   Logs: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups/log-group/\$252Fecs\$252F$PROJECT_NAME"
echo ""

# Rollback instructions
echo "🔄 Rollback (if needed):"
echo "   aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --task-definition $TASK_FAMILY:PREVIOUS_VERSION --region $AWS_REGION"
echo ""
